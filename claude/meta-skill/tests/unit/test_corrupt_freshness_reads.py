"""Corrupt `observed-input-dependencies.json` at the copied freshness CLI (#12 recheck C2).

The dynamic-read register is freshness state written by the `read` operation.
When it is malformed, `observe`, `read`, `check` and `publish` must answer with
a structured ``invalid`` result naming the file, never a traceback, and never
treat the corrupt register as empty: a silently dropped read would let evidence
claim provenance it no longer tracks. The corrupt file and every prior
observation, publication and report stay on disk for repair; the public gates
keep blocking; restoring a well-formed register restores the dependency.
These exercise copied CLIs in temporary projects on both host adapters, not
actual Claude/Codex host dialogue.
"""
import json

import pytest

from .test_bootstrap_scope import gate, write
from .test_evidence_freshness import WORKFLOW
from .test_evidence_freshness import invoke, setup
from .test_freshness_admission_corrections import _artifacts, _blockers, _no_crash, _readiness, _reconcile

READS = ".allforai/bootstrap/observed-input-dependencies.json"
STATE = ".allforai/bootstrap/evidence-freshness.json"
NODE = "deliver-export"
HOSTS = ["claude", "codex"]

CORRUPT = [
    ("top-level list", []),
    ("top-level list of paths", ["policy.txt"]),
    ("top-level string", "policy.txt"),
    ("top-level number", 42),
    ("top-level null", None),
    ("node value string", {NODE: "policy.txt"}),
    ("node value object", {NODE: {"path": "policy.txt"}}),
    ("node value null", {NODE: None}),
    ("node entry number", {NODE: [42]}),
    ("node entry empty", {NODE: [""]}),
    ("node entry absolute", {NODE: ["/etc/passwd"]}),
    ("node entry parent", {NODE: ["../policy.txt"]}),
    ("empty node id", {"": ["policy.txt"]}),
]


def _invalid(result, payload):
    _no_crash(result)
    assert result.returncode == 1, (result.stdout, result.stderr)
    assert payload["status"] == "invalid", payload
    assert "observed-input-dependencies.json" in payload["reason"], payload
    return payload


def _tree(root):
    bootstrap = root / ".allforai/bootstrap"
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in bootstrap.rglob("*") if p.is_file()}


def _provenance(tmp_path):
    """Valid observe → read → publish, returning the observation token of the published record."""
    (tmp_path / "policy.txt").write_text("region = JP")
    _, original = invoke(tmp_path, "observe", node_id=NODE)
    result, observed = invoke(tmp_path, "read", observation=original["observation"], path="policy.txt")
    assert result.returncode == 0, (result.stdout, result.stderr)
    result, published = invoke(tmp_path, "publish", observation=observed["observation"])
    assert result.returncode == 0 and published["status"] == "valid"
    assert json.loads((tmp_path / READS).read_text()) == {NODE: ["policy.txt"]}
    return observed["observation"]


@pytest.mark.parametrize("host", HOSTS)
@pytest.mark.parametrize("label,value", CORRUPT, ids=[c[0] for c in CORRUPT])
def test_corrupt_read_register_is_a_structured_invalid_result_at_every_cli_seam(tmp_path, host, label, value):
    setup(tmp_path, host)
    token = _provenance(tmp_path)
    _, checked = invoke(tmp_path, "check")
    assert checked["nodes"][NODE]["status"] == "valid"
    write(tmp_path, READS, value)
    before = _tree(tmp_path)

    # observe: never records a snapshot built on a register it cannot read.
    result, payload = invoke(tmp_path, "observe", node_id=NODE)
    _invalid(result, payload)
    assert "observation" not in payload
    # read: never rewrites the register or the observation.
    result, payload = invoke(tmp_path, "read", observation=token, path="policy.txt")
    _invalid(result, payload)
    assert "content" not in payload
    # check: the evidence is not reported valid on an unreadable dependency set.
    result, payload = invoke(tmp_path, "check")
    _invalid(result, payload)
    assert "nodes" not in payload
    # publish: no evidence is published while the register is unreadable.
    result, payload = invoke(tmp_path, "publish", observation=token)
    _invalid(result, payload)

    assert _tree(tmp_path) == before, "corrupt register and existing provenance must be preserved for repair"


@pytest.mark.parametrize("host", HOSTS)
def test_unparseable_read_register_is_invalid_not_empty(tmp_path, host):
    setup(tmp_path, host)
    token = _provenance(tmp_path)
    (tmp_path / READS).write_text("{not json")
    before = _tree(tmp_path)
    for operation, request in (("observe", {"node_id": NODE}), ("read", {"observation": token, "path": "policy.txt"}),
                               ("check", {}), ("publish", {"observation": token})):
        result, payload = invoke(tmp_path, operation, **request)
        _invalid(result, payload)
    assert _tree(tmp_path) == before


@pytest.mark.parametrize("host", HOSTS)
@pytest.mark.parametrize("label,value", [CORRUPT[1], CORRUPT[5], CORRUPT[8]], ids=lambda c: c if isinstance(c, str) else "")
def test_public_gates_stay_blocked_on_corrupt_read_register(tmp_path, host, label, value):
    setup(tmp_path, host)
    _provenance(tmp_path)
    assert _artifacts(tmp_path)["all_exist"] is True
    write(tmp_path, READS, value)

    checked = _artifacts(tmp_path)
    assert checked["all_exist"] is False
    assert checked["freshness"]["status"] == "invalid"
    assert "observed-input-dependencies.json" in checked["freshness"]["reason"]
    code, report = _readiness(tmp_path)
    assert code == 1 and report["status"] == "not_ready"
    # A corrupt register also leaves the external-change comparison undeterminable,
    # which is a project-wide blocker rather than one node's.
    blocked = [b for b in report["blockers"] if b.get("node_id") == NODE]
    assert blocked, report["blockers"]
    assert all("observed-input-dependencies.json" in b["message"] for b in report["blockers"]), report["blockers"]
    node, plan = _reconcile(tmp_path)
    assert node["artifact_readiness"] == "blocked" and plan["action"] == "invalidate"
    result = gate(tmp_path, "validate_bootstrap.py")
    _no_crash(result)
    assert json.loads((tmp_path / READS).read_text()) == value, "gates never repair or drop the register"


@pytest.mark.parametrize("host", HOSTS)
def test_repaired_register_restores_the_dynamic_dependency(tmp_path, host):
    setup(tmp_path, host)
    token = _provenance(tmp_path)
    write(tmp_path, READS, [NODE])
    _invalid(*invoke(tmp_path, "check"))

    write(tmp_path, READS, {NODE: ["policy.txt"]})
    result, checked = invoke(tmp_path, "check")
    assert result.returncode == 0 and checked["nodes"][NODE]["status"] == "valid", checked
    result, again = invoke(tmp_path, "read", observation=token, path="policy.txt")
    assert result.returncode == 0 and again["content"] == "region = JP"
    # The repaired register still binds the read: editing it invalidates the evidence.
    (tmp_path / "policy.txt").write_text("region = US")
    _, checked = invoke(tmp_path, "check")
    assert checked["nodes"][NODE]["status"] == "stale"
    assert _artifacts(tmp_path)["all_exist"] is False


@pytest.mark.parametrize("host", HOSTS)
def test_register_for_an_unknown_node_is_kept_and_reported_not_dropped(tmp_path, host):
    """A well-formed entry for a node the workflow no longer lists is not corruption;
    it is retained provenance and stays in the owned-input set."""
    setup(tmp_path, host)
    _provenance(tmp_path)
    write(tmp_path, READS, {NODE: ["policy.txt"], "retired-node": ["archive.txt"]})
    (tmp_path / "archive.txt").write_text("old")
    result, checked = invoke(tmp_path, "check")
    _no_crash(result)
    assert checked["nodes"][NODE]["status"] == "valid", checked
    assert checked["uncertain_inputs"] == []
    workflow = json.loads((tmp_path / WORKFLOW).read_text())
    assert [n["node_id"] for n in workflow["nodes"]] == [NODE]
