"""Ledger-shaped evidence entries written by /run's runtime gates (ADR-0008, #59).

product-verify, runtime-smoke-verify and test-verify write, beside their human reports, entries in
cross-exam's ledger-entry shape. The engine validates the shape; capture_evidence writes what the
agent cannot author (build identity from the whole tree, probed_at with an offset, image digests, the
author marker); check_evidence refuses by name and a gate whose entry is refused is not passed.
"""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from .. import module_isolation

SCRIPTS = str(Path(module_isolation.ORCHESTRATOR).parent)
_capture, _check = module_isolation._isolation.load(SCRIPTS, "capture_evidence", "check_evidence")
_cc = module_isolation._isolation.load(SCRIPTS, "compute_completeness")
write_entry, entry_reason, entries_reason = _capture.write_entry, _check.entry_reason, _check.entries_reason
ENGINE = Path(SCRIPTS) / "engine"

RUN = ".allforai/product-verify"
NODE = "product-verify-web"
SERVED = {"host": "localhost:3000", "process": "node next dev (pid 4242)", "mock_layers": []}


def _git(repo, *args):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_AUTHOR_NAME="a", GIT_AUTHOR_EMAIL="a@b", GIT_COMMITTER_NAME="a", GIT_COMMITTER_EMAIL="a@b")
    return subprocess.run(["git", "-C", str(repo), "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null",
                           *args], check=True, capture_output=True, text=True, env=env).stdout.strip()


@pytest.fixture
def project(tmp_path, monkeypatch):
    """A committed target project with one runtime evidence directory under the product-verify run."""
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
        monkeypatch.delenv(key, raising=False)
    (tmp_path / "app.py").write_text("print(1)\n")
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-q", "-m", "one")
    evidence = tmp_path / RUN / "evidence" / NODE / "q01"
    evidence.mkdir(parents=True)
    (evidence / "q01-01-home.png").write_bytes(b"\x89PNG-home")
    (evidence / "q01-health.json").write_text(json.dumps({
        "schema": "capture_evidence/v1", "command": ["curl", "localhost:3000/health"], "exit_code": 0,
        "stdout": '{"status": "ok", "orders": 3}', "stdout_sha256": "abc"}))
    return tmp_path


def _draft(**extra):
    return {"q": "首页在真实后端下能渲染吗？", "facet": "F1", "medium": "runtime", "verdict": "done",
            "served_by": dict(SERVED), "readback": {"theme": "light", "locale": "zh-CN", "width": "1280"},
            "evidence": {"dir": "evidence/%s/q01/" % NODE, "key_observation": "首页渲染，/health 返回 200"},
            "images": ["q01-01-home.png"], **extra}


def _entries_file(root):
    return root / RUN / "evidence-entries" / (NODE + ".json")


def _identity(root):
    spec = __import__("importlib.util").util.spec_from_file_location("engine_identity_for_test", ENGINE / "identity.py")
    module = __import__("importlib.util").util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build_identity(root, exclude=_check.BUILD_EXCLUDES)


# --- writing ---

def test_write_entry_records_what_the_agent_cannot_author(project):
    entry, reason = write_entry(project / RUN, _draft(), project, NODE, "product-verify")

    assert reason == ""
    assert entry["build"] == _identity(project)["build"] and entry["build"].startswith(_git(project, "rev-parse", "HEAD"))
    # the host directories are outside the build: the gate's own writes under .allforai do not move it
    assert entry["build_excludes"] == [".allforai", ".claude", ".codex"]
    assert _check.BUILD_EXCLUDES == (".allforai", ".claude", ".codex")
    assert entry["probed_at"][-6] in "+-" and entry["probed_at"][-3] == ":"      # an offset, never a naive stamp
    assert entry["author"] == {"pipeline": "meta-skill/run", "node_id": NODE, "capability": "product-verify"}
    assert entry["image_digests"] == {"q01-01-home.png": hashlib.sha256(b"\x89PNG-home").hexdigest()}
    stored = json.loads(_entries_file(project).read_text())
    assert stored["schema"] == "evidence-entries/v1" and stored["entries"] == [entry]
    assert stored["run_dir"] == RUN                                      # project-relative, never a machine path
    assert entries_reason(project / RUN, project, NODE) == ""


def test_a_second_entry_appends_and_the_probe_time_given_by_the_gate_is_kept(project):
    assert write_entry(project / RUN, _draft(), project, NODE, "product-verify")[1] == ""
    second = _draft(q="订单页", probed_at="2026-09-10T09:00:00+08:00")
    entry, reason = write_entry(project / RUN, second, project, NODE, "product-verify")
    assert reason == "" and entry["probed_at"] == "2026-09-10T09:00:00+08:00"
    assert [e["q"] for e in json.loads(_entries_file(project).read_text())["entries"]] == [_draft()["q"], "订单页"]


def test_a_refused_draft_writes_nothing_and_names_the_rule(project):
    naive = _draft(probed_at="2026-09-10T09:00:00")
    entry, reason = write_entry(project / RUN, naive, project, NODE, "product-verify")
    assert reason == "probed_at 缺时区偏移（如 +08:00）"
    assert not _entries_file(project).exists()

    mocked = _draft(served_by={**SERVED, "mock_layers": ["msw"]})
    assert write_entry(project / RUN, mocked, project, NODE, "product-verify")[1] == "经 mock 层（msw）的 runtime 不能判 done"
    gap = _draft(served_by={**SERVED, "mock_layers": ["msw"]}, verdict="gap")
    assert write_entry(project / RUN, gap, project, NODE, "product-verify")[1] == ""     # a gap through a mock is still a gap

    assert write_entry(project / RUN, _draft(evidence={"dir": "."}), project, NODE, "product-verify")[1] == "无证据目录"
    assert write_entry(project / RUN, "not an entry", project, NODE, "product-verify")[1] == "条目须是对象"


def test_a_launched_artifact_enters_the_build_and_the_entry_says_which(project):
    """runtime-smoke launches a built artifact (gitignored dist/): its digest is part of the build, the entry
    records the path so the gate recomputes the same value, and a rebuilt artifact is a stale build."""
    (project / ".gitignore").write_text("dist/\n")
    _git(project, "add", ".gitignore")
    _git(project, "commit", "-q", "-m", "ignore dist")
    dist = project / "dist"
    dist.mkdir()
    (dist / "app.bin").write_bytes(b"v1")
    entry, reason = write_entry(project / RUN, _draft(), project, NODE, "runtime-smoke-verify", artifacts=["dist"])
    assert reason == "" and entry["build_artifacts"] == ["dist"]
    plain, reason = write_entry(project / RUN, _draft(q="no artifact"), project, NODE, "runtime-smoke-verify")
    assert reason == "" and plain["build"] != entry["build"] and "build_artifacts" not in plain
    assert entries_reason(project / RUN, project, NODE) == ""             # each entry is checked with its own artifacts
    (dist / "app.bin").write_bytes(b"v2")
    assert entries_reason(project / RUN, project, NODE).startswith("#1: 构建标识不匹配")


def test_a_tree_that_cannot_be_identified_is_a_reason_not_a_traceback(tmp_path):
    (tmp_path / RUN / "evidence/q01").mkdir(parents=True)
    (tmp_path / RUN / "evidence/q01/a.png").write_bytes(b"x")
    entry, reason = write_entry(tmp_path / RUN, _draft(evidence={"dir": "evidence/q01/"}, images=[]),
                                tmp_path, NODE, "product-verify")
    assert "不是 git 仓库" in reason and entry is None


# --- checking ---

def test_stale_build_is_refused_by_name_and_the_gate_is_not_passed(project):
    assert write_entry(project / RUN, _draft(), project, NODE, "product-verify")[1] == ""
    (project / "app.py").write_text("print(2)\n")             # the tree moved after the entry was written

    reason = entries_reason(project / RUN, project, NODE)
    assert "构建标识不匹配" in reason

    gate = subprocess.run([sys.executable, str(Path(SCRIPTS) / "check_evidence.py"), "--entries", RUN,
                           "--node", NODE, "--root", str(project)], capture_output=True, text=True, cwd=project)
    assert gate.returncode == 1 and "构建标识不匹配" in gate.stdout and gate.stderr == ""


def test_fixture_match_uses_the_refusal_compute_completeness_uses(project):
    """served_by.fixtures names the canned files that could have answered; an output identical to one is
    refused with the literal #55 put in compute_completeness, so the two gates cannot drift apart."""
    fixture = project / "mocks/health.json"
    fixture.parent.mkdir()
    fixture.write_text('{\n  "status": "ok",\n  "orders": 3\n}\n')
    draft = _draft(served_by={**SERVED, "fixtures": ["mocks/health.json"]})

    entry, reason = write_entry(project / RUN, draft, project, NODE, "product-verify")

    assert reason == "响应与 fixture 一致（mocks/health.json）的 runtime 不能判 done"
    log_entry = {"node": NODE, "status": "completed", "generated_by": "g",
                 "verification": {"method": "real-api", "verifier": "v", "served_by": draft["served_by"],
                                  "evidence_path": RUN + "/evidence/%s/q01/q01-health.json" % NODE}}
    assert _cc.hollow_reason(log_entry, str(project)) == reason
    fixture.write_text('{"status": "ok", "orders": 4}')
    assert write_entry(project / RUN, draft, project, NODE, "product-verify")[1] == ""
    assert "mocks/gone.json" in write_entry(project / RUN, _draft(q="x", served_by={**SERVED, "fixtures": ["mocks/gone.json"]}),
                                            project, NODE, "product-verify")[1]


def test_an_edited_entries_file_is_refused_by_the_first_rule_it_breaks(project):
    assert write_entry(project / RUN, _draft(), project, NODE, "product-verify")[1] == ""
    stored = json.loads(_entries_file(project).read_text())

    del stored["entries"][0]["author"]
    _entries_file(project).write_text(json.dumps(stored))
    assert entries_reason(project / RUN, project, NODE) == "#1: 缺作者标记 author（pipeline / node_id / capability）"

    stored["entries"][0]["author"] = {"pipeline": "meta-skill/run", "node_id": "someone-else", "capability": "product-verify"}
    _entries_file(project).write_text(json.dumps(stored))
    assert "someone-else" in entries_reason(project / RUN, project, NODE)

    stored["entries"][0]["author"]["node_id"] = NODE
    stored["entries"][0]["build_excludes"] = ["."]                # an entry may not choose its own build scope
    _entries_file(project).write_text(json.dumps(stored))
    assert entries_reason(project / RUN, project, NODE) == "#1: 构建标识排除范围须为 .allforai, .claude, .codex"

    stored["entries"][0]["build_excludes"] = [".allforai", ".claude", ".codex"]
    (project / RUN / "evidence" / NODE / "q01/q01-01-home.png").write_bytes(b"\x89PNG-swapped")
    _entries_file(project).write_text(json.dumps(stored))
    assert entries_reason(project / RUN, project, NODE) == "#1: 截图内容摘要不匹配: q01-01-home.png"


def test_a_gate_without_entries_or_with_an_unreadable_file_is_not_passed(project):
    assert entries_reason(project / RUN, project, NODE) == "无证据条目文件: %s/evidence-entries/%s.json" % (RUN, NODE)
    _entries_file(project).parent.mkdir(parents=True)
    _entries_file(project).write_text("{not json")
    assert entries_reason(project / RUN, project, NODE).startswith("证据条目文件不可读")
    _entries_file(project).write_text(json.dumps({"schema": "evidence-entries/v1", "entries": []}))
    assert entries_reason(project / RUN, project, NODE) == "证据条目为空"
    _entries_file(project).write_text(json.dumps({"schema": "evidence-entries/v1", "entries": [7]}))
    assert entries_reason(project / RUN, project, NODE) == "#1: 条目须是对象"


def test_entry_reason_reads_the_engine_from_the_scripts_directory(project):
    entry, _ = write_entry(project / RUN, _draft(), project, NODE, "product-verify")
    assert entry_reason(entry, project / RUN, project) == ""
    assert entry_reason({**entry, "medium": "oral"}, project / RUN, project) == "非法介质: oral"
    assert entry_reason({**entry, "readback": {"theme": ""}}, project / RUN, project) == "theme 轴缺应用内读回值"


def test_test_layer_entries_are_mechanical_gates(project):
    """A suite run is a mechanical gate (medium test): admitted on its captured output alone, no served_by,
    so a later /cross-exam admits it as a gate instead of rerunning the suite. A UI path stays runtime."""
    run = project / RUN
    (run / "evidence" / NODE / "q05").mkdir(parents=True)
    (run / "evidence" / NODE / "q05" / "pytest.log").write_text("42 passed in 1.2s\n")
    gate = {"q": "R2 单元层在真实目标上达标吗？", "facet": "F1", "medium": "test", "verdict": "done",
            "evidence": {"dir": "evidence/%s/q05/" % NODE, "key_observation": "42 passed"}}
    entry, reason = write_entry(run, gate, project, NODE, "test-verify")
    assert reason == "", reason
    assert entry["medium"] == "test" and "served_by" not in entry
    (run / "evidence" / NODE / "q06").mkdir(parents=True)
    (run / "evidence" / NODE / "q06" / "coverage.png").write_bytes(b"\x89PNG")   # a picture is not a captured output
    bare = {**gate, "evidence": {"dir": "evidence/%s/q06/" % NODE, "key_observation": "x"}}
    _, reason = write_entry(run, bare, project, NODE, "test-verify")
    assert "机械门证据无输出文件" in reason
