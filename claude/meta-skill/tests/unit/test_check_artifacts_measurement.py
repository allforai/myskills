"""Read-only measurement surface of check_artifacts --json (both-host repair acceptance).

An independent gate agent runs the shipped command and compares its structured output
across an attempt. Existence alone cannot tell a fresh delivery from a pre-existing or
touched leftover, and a digest of the delivered bytes cannot say what the node is bound
to, so the two questions are answered by two fields: ``artifacts[].digest`` and
``freshness.binding_identity`` beside the existing ``readiness_status``.

These drive the copied helper in temporary projects; they are seam tests, not host proof.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from .test_bootstrap_scope import project, publish_contract, write

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts/orchestrator"))
import check_artifacts  # noqa: E402
from check_artifacts import artifact_digest, check_node_artifacts, recorded_binding  # noqa: E402

NODE = "deliver-export"
REPORT = ".allforai/bootstrap/export-report.json"
WORKFLOW = ".allforai/bootstrap/workflow.json"
STATE = ".allforai/bootstrap/evidence-freshness.json"


def node_of(root):
    workflow = json.loads((root / WORKFLOW).read_text())
    return next(n for n in workflow["nodes"] if n["node_id"] == NODE)


def measure(root):
    return check_node_artifacts(node_of(root), root)


def artifact(root, path=REPORT):
    return next(a for a in measure(root)["artifacts"] if a["path"] == path)


def tree(root):
    return {p: p.read_bytes() for p in sorted(root.rglob("*"))
            if p.is_file() and "__pycache__" not in p.parts}


# --- artifacts[].digest: content, not existence and not mtime ------------------------


def test_the_digest_is_the_sha256_of_the_delivered_bytes(tmp_path):
    project(tmp_path, confirmed=True)
    write(tmp_path, REPORT, {"status": "passed"})
    body = (tmp_path / REPORT).read_bytes()
    assert artifact(tmp_path)["digest"] == hashlib.sha256(body).hexdigest()


def test_a_content_edit_changes_the_digest(tmp_path):
    project(tmp_path, confirmed=True)
    write(tmp_path, REPORT, {"status": "passed"})
    before = artifact(tmp_path)["digest"]
    write(tmp_path, REPORT, {"status": "passed", "attempt": 2})
    after = artifact(tmp_path)["digest"]
    assert before and after and before != after


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_touching_an_artifact_does_not_change_its_digest(tmp_path, host):
    """The touched-leftover case: a moved write time is not a delivery."""
    project(tmp_path, confirmed=True, host=host)
    write(tmp_path, REPORT, {"status": "passed"})
    before = artifact(tmp_path)["digest"]
    stat = os.stat(tmp_path / REPORT)
    os.utime(tmp_path / REPORT, (stat.st_atime + 120, stat.st_mtime + 120))
    entry = artifact(tmp_path)
    assert entry["digest"] == before
    assert os.stat(tmp_path / REPORT).st_mtime != stat.st_mtime


def test_a_missing_artifact_measures_null_with_its_reason(tmp_path):
    project(tmp_path, confirmed=True)
    entry = artifact(tmp_path)
    assert entry["exists"] is False
    assert entry["digest"] is None
    assert entry["digest_error"] == "missing"


def test_a_directory_in_place_of_an_artifact_measures_null(tmp_path):
    project(tmp_path, confirmed=True)
    (tmp_path / REPORT).mkdir(parents=True)
    entry = artifact(tmp_path)
    assert entry["digest"] is None and entry["digest_error"] == "missing"


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="requires POSIX named pipes")
def test_a_fifo_artifact_is_refused_without_waiting_for_a_writer(tmp_path):
    target = tmp_path / "artifact.pipe"
    os.mkfifo(target)
    script = ("import json, sys; from check_artifacts import artifact_digest; "
              "print(json.dumps(artifact_digest(sys.argv[1])))")
    result = subprocess.run(
        [sys.executable, "-B", "-c", script, str(target)],
        cwd=Path(check_artifacts.__file__).parent,
        capture_output=True, text=True, timeout=3, check=True,
    )
    assert json.loads(result.stdout) == [None, "missing"]


def test_invalid_utf8_state_has_no_binding(tmp_path):
    state = tmp_path / STATE
    state.parent.mkdir(parents=True)
    state.write_bytes(b"\xff")
    assert check_artifacts.read_state_text(tmp_path) is None
    assert recorded_binding(tmp_path, NODE) == (None, None)


def test_an_unreadable_artifact_measures_null(tmp_path):
    project(tmp_path, confirmed=True)
    write(tmp_path, REPORT, {"status": "passed"})
    target = tmp_path / REPORT
    os.chmod(target, 0o000)
    try:
        if os.access(target, os.R_OK):
            pytest.skip("cannot make a file unreadable for this user")
        entry = artifact(tmp_path)
        assert entry["digest"] is None
        assert entry["digest_error"].startswith("unreadable: ")
    finally:
        os.chmod(target, 0o600)


def test_an_artifact_that_escapes_the_project_is_refused_even_though_it_exists(tmp_path):
    """A symlink out of the project is not this project's evidence."""
    outside = tmp_path.parent / ("outside-" + tmp_path.name + ".json")
    outside.write_text(json.dumps({"status": "passed"}), encoding="utf-8")
    project(tmp_path, confirmed=True)
    (tmp_path / REPORT).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / REPORT).symlink_to(outside)
    entry = artifact(tmp_path)
    assert entry["exists"] is True, "exists is unchanged for backward compatibility"
    assert entry["digest"] is None
    assert entry["digest_error"] == "outside project root"


def test_a_symlink_inside_the_project_is_measured(tmp_path):
    project(tmp_path, confirmed=True)
    real = tmp_path / ".allforai/bootstrap/real-report.json"
    real.write_text(json.dumps({"status": "passed"}), encoding="utf-8")
    (tmp_path / REPORT).symlink_to(real)
    assert artifact(tmp_path)["digest"] == hashlib.sha256(real.read_bytes()).hexdigest()


def test_the_digest_helper_refuses_an_absolute_path_outside_the_root(tmp_path):
    outside = tmp_path.parent / ("bare-" + tmp_path.name + ".json")
    outside.write_text("{}", encoding="utf-8")
    assert artifact_digest(str(outside), tmp_path) == (None, "outside project root")
    assert artifact_digest(str(outside), None)[0] is not None  # no root claimed, no claim made


# --- freshness.binding_identity: what the node is bound to ---------------------------


def test_a_published_contract_reports_a_stable_current_binding(tmp_path):
    project(tmp_path, confirmed=True)
    freshness = measure(tmp_path)["freshness"]
    assert freshness["readiness_status"] == "valid"
    assert freshness["binding_kind"] == "contract"
    assert len(freshness["binding_identity"]) == 64
    assert int(freshness["binding_identity"], 16) >= 0
    assert measure(tmp_path)["freshness"]["binding_identity"] == freshness["binding_identity"]


def test_the_binding_identity_is_the_recorded_observation_not_the_delivered_bytes(tmp_path):
    project(tmp_path, confirmed=True)
    before = measure(tmp_path)["freshness"]["binding_identity"]
    write(tmp_path, REPORT, {"status": "passed"})
    assert measure(tmp_path)["freshness"]["binding_identity"] == before
    assert artifact(tmp_path)["digest"] is not None


def test_moving_an_input_leaves_the_old_binding_and_turns_readiness_stale(tmp_path):
    """Identity unchanged plus readiness stale is the unbound-delivery signal."""
    project(tmp_path, confirmed=True)
    bound = measure(tmp_path)["freshness"]["binding_identity"]
    (tmp_path / "orders.py").write_text("def list_orders(account): return [account]\n")
    freshness = measure(tmp_path)["freshness"]
    assert freshness["binding_identity"] == bound
    assert freshness["readiness_status"] == "stale"


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_re_observing_the_changed_inputs_rebinds_the_node(tmp_path, host):
    """The source-changing repair: the binding that matters is to the final inputs."""
    project(tmp_path, confirmed=True, host=host)
    bound = measure(tmp_path)["freshness"]["binding_identity"]
    (tmp_path / "orders.py").write_text("def list_orders(account): return [account]\n")
    publish_contract(tmp_path, NODE)
    freshness = measure(tmp_path)["freshness"]
    assert freshness["binding_identity"] != bound
    assert freshness["readiness_status"] == "valid"


@pytest.mark.parametrize("state", ["{not json", '"a string"', '{"nodes": []}', '{}'],
                         ids=["unparseable", "not-an-object", "nodes-not-a-map", "empty"])
def test_an_unusable_freshness_state_fails_closed_to_a_null_binding(tmp_path, state):
    project(tmp_path, confirmed=True)
    (tmp_path / STATE).write_text(state, encoding="utf-8")
    assert recorded_binding(tmp_path, NODE) == (None, None)
    assert measure(tmp_path)["freshness"]["binding_identity"] is None


def test_a_record_without_inputs_or_kind_has_no_binding(tmp_path):
    project(tmp_path, confirmed=True)
    state = json.loads((tmp_path / STATE).read_text())
    state["contracts"][NODE] = {"kind": "contract"}
    write(tmp_path, STATE, state)
    assert recorded_binding(tmp_path, NODE) == (None, None)
    state["contracts"][NODE] = {"kind": 7, "inputs": {"files": {}}}
    write(tmp_path, STATE, state)
    assert recorded_binding(tmp_path, NODE) == (None, None)


def test_a_node_with_no_record_has_no_binding(tmp_path):
    project(tmp_path, confirmed=True)
    assert recorded_binding(tmp_path, "never-observed") == (None, None)


def test_evidence_and_contract_records_are_distinguished(tmp_path):
    """binding_kind names which observation readiness_status is judged against."""
    project(tmp_path, confirmed=True)
    contract_identity, kind = recorded_binding(tmp_path, NODE)
    assert kind == "contract"
    state = json.loads((tmp_path / STATE).read_text())
    state.pop("contracts")
    write(tmp_path, STATE, state)
    evidence_identity, kind = recorded_binding(tmp_path, NODE)
    assert kind == "evidence" or evidence_identity is None


# --- read-only ----------------------------------------------------------------------


def test_measuring_writes_nothing(tmp_path):
    project(tmp_path, confirmed=True)
    write(tmp_path, REPORT, {"status": "passed"})
    measure(tmp_path)  # any first-call caching settles here
    before = tree(tmp_path)
    result = measure(tmp_path)
    assert result["artifacts"][0]["digest"] is not None
    assert tree(tmp_path) == before


def test_measuring_registers_no_observed_read(tmp_path):
    project(tmp_path, confirmed=True)
    write(tmp_path, REPORT, {"status": "passed"})
    register = tmp_path / ".allforai/bootstrap/observed-input-dependencies.json"
    before = register.read_bytes() if register.exists() else None
    measure(tmp_path)
    after = register.read_bytes() if register.exists() else None
    assert after == before


# --- the shipped command, which is what the gate agent actually runs ------------------


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_the_shipped_json_command_carries_the_measurement_and_stays_additive(tmp_path, host):
    """Both hosts copy the same helper, so both gates read the same measurement."""
    project(tmp_path, confirmed=True, host=host)
    write(tmp_path, REPORT, {"status": "passed"})
    result = subprocess.run(
        [sys.executable, str(tmp_path / ".allforai/bootstrap/scripts/check_artifacts.py"),
         str(tmp_path / WORKFLOW), "--node", NODE, "--json"],
        capture_output=True, text=True, cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    entry = payload["artifacts"][0]
    assert set(("path", "exists", "digest")) <= set(entry)
    assert entry["digest"] == hashlib.sha256((tmp_path / REPORT).read_bytes()).hexdigest()
    assert payload["freshness"]["binding_kind"] == "contract"
    assert len(payload["freshness"]["binding_identity"]) == 64
    # Every pre-existing key still carries its old meaning. Here the node holds a
    # published contract and no evidence yet, so readiness_status is valid while
    # status is stale and all_exist stays false — unchanged by the measurement, and
    # the reason the binding pairs with readiness_status rather than with status.
    assert payload["node_id"] == NODE and "goal" in payload
    assert payload["freshness"]["readiness_status"] == "valid"
    assert payload["freshness"]["status"] == "stale"
    assert payload["freshness"]["diff"] == {"evidence": "unpublished"}
    assert payload["all_exist"] is False
    assert entry["exists"] is True and "status_error" not in entry


# --- the record must be the observation evidence_freshness actually writes ----------


def _record(root, **overrides):
    state = json.loads((root / STATE).read_text())
    state["contracts"][NODE] = {**state["contracts"][NODE], **overrides}
    write(root, STATE, state)
    return state


@pytest.mark.parametrize("inputs", [
    None, "a snapshot", ["files"], 7, {},
    {"files": {}, "requirements": {}, "baseline_scope": {}, "upstream": {}},
    {"files": [], "requirements": {}, "contract": "d", "baseline_scope": {}, "upstream": {}},
    {"files": {}, "requirements": {}, "contract": "", "baseline_scope": {}, "upstream": {}},
    {"files": {}, "requirements": {}, "contract": 7, "baseline_scope": {}, "upstream": {}},
    {"files": {}, "requirements": {}, "contract": "d", "baseline_scope": {}},
], ids=["null", "string", "list", "number", "empty", "no-contract", "files-not-a-map",
        "blank-contract", "contract-not-a-string", "no-upstream"])
def test_a_record_that_is_not_the_canonical_snapshot_has_no_binding(tmp_path, inputs):
    """Only the shape evidence_freshness.snapshot writes can be an identity: a record
    that could never equal a current snapshot must not be digested into authority."""
    project(tmp_path, confirmed=True)
    _record(tmp_path, inputs=inputs)
    assert recorded_binding(tmp_path, NODE) == (None, None)
    assert measure(tmp_path)["freshness"]["binding_identity"] is None


@pytest.mark.parametrize("kind", ["draft", "", "Contract", 7, None, ["contract"]],
                         ids=["unknown", "blank", "wrong-case", "number", "null", "list"])
def test_a_kind_outside_the_shared_set_has_no_binding(tmp_path, kind):
    """evidence_freshness.session refuses any kind but contract or evidence."""
    project(tmp_path, confirmed=True)
    _record(tmp_path, kind=kind)
    assert recorded_binding(tmp_path, NODE) == (None, None)


def test_an_absent_kind_reads_as_evidence_exactly_as_evaluate_does(tmp_path):
    """Not a malformed record: evaluate reads a record with no kind as evidence, so the
    binding reports the same observation its readiness_status was judged against."""
    project(tmp_path, confirmed=True)
    state = json.loads((tmp_path / STATE).read_text())
    record = dict(state["contracts"][NODE])
    record.pop("kind")
    state["contracts"][NODE] = record
    write(tmp_path, STATE, state)
    identity, kind = recorded_binding(tmp_path, NODE)
    assert kind == "evidence" and len(identity) == 64


def test_the_binding_reads_the_exact_state_bytes_it_is_given(tmp_path):
    project(tmp_path, confirmed=True)
    text = (tmp_path / STATE).read_text()
    assert recorded_binding(tmp_path, NODE, text) == recorded_binding(tmp_path, NODE)
    assert recorded_binding(tmp_path, NODE, "{not json") == (None, None)


# --- readiness and binding must describe one observation ----------------------------


def test_a_rebind_between_the_two_reads_fails_closed(tmp_path, monkeypatch):
    """A concurrent rebind must not report a new identity beside the old readiness."""
    project(tmp_path, confirmed=True)
    bound = measure(tmp_path)["freshness"]["binding_identity"]
    real_states = check_artifacts.freshness_states
    rebound = []

    def rebinding_states(root, workflow):
        result = real_states(root, workflow)
        if not rebound:
            rebound.append(True)
            state = json.loads((root / STATE).read_text())
            record = state["contracts"][NODE]
            record["inputs"] = {**record["inputs"], "contract": "0" * 64}
            write(root, STATE, state)
        return result

    monkeypatch.setattr(check_artifacts, "freshness_states", rebinding_states)
    freshness = check_node_artifacts(node_of(tmp_path), tmp_path)["freshness"]
    monkeypatch.undo()
    assert rebound, "the rebind must have landed inside the measurement window"
    assert freshness["binding_identity"] is None and freshness["binding_kind"] is None
    assert freshness["readiness_status"] in ("valid", "stale"), "readiness is not weakened"
    # Once the window is closed the next measurement reports the new binding coherently.
    settled = measure(tmp_path)["freshness"]
    assert settled["binding_identity"] not in (None, bound)


def test_an_absent_state_leaves_the_binding_null_without_failing_the_read(tmp_path):
    project(tmp_path, confirmed=True)
    (tmp_path / STATE).unlink()
    freshness = measure(tmp_path)["freshness"]
    assert freshness["binding_identity"] is None and freshness["binding_kind"] is None


def test_a_target_swapped_after_it_was_opened_is_refused(tmp_path, monkeypatch):
    """The containment check accepted a descriptor; the bytes must come from that file."""
    project(tmp_path, confirmed=True)
    write(tmp_path, REPORT, {"status": "passed"})
    target = tmp_path / REPORT
    real_open = os.open
    swapped = []

    def swapping_open(path, *args, **kwargs):
        handle = real_open(path, *args, **kwargs)
        if not swapped and str(path) == str(target.resolve()):
            swapped.append(True)
            target.unlink()
            target.write_text(json.dumps({"status": "passed", "other": True}), encoding="utf-8")
        return handle

    monkeypatch.setattr(os, "open", swapping_open)
    entry = artifact(tmp_path)
    monkeypatch.undo()
    assert swapped, "the swap must have landed inside the measurement window"
    assert entry["digest"] is None
    assert entry["digest_error"].startswith("unreadable: target changed")


def test_a_blocked_artifact_still_blocks_and_is_still_measured(tmp_path):
    project(tmp_path, confirmed=True)
    write(tmp_path, REPORT, {"status": "blocked"})
    result = measure(tmp_path)
    assert result["all_exist"] is False
    assert result["artifacts"][0]["status_error"]["value"] == "blocked"
    assert result["artifacts"][0]["digest"] is not None, "a blocked report is still measurable"
