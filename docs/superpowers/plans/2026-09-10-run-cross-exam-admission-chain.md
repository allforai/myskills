# `/run` → `/cross-exam` Admission Chain Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the evidence chain that ADR-0008 promised actually carry weight end to end: `/run`'s mechanical gates emit entries `/cross-exam` can admit (#63), runtime nodes are asked for the `served_by` that the kept hollow refusals need (#64), and `auto_fix_once` never halts as "unauthorized" for want of a repair loop bootstrap forgot to plan (#65).

**Architecture:** Three independent tickets, each a vertical slice. #63 adds `medium: build|contract` entries to four capabilities using the existing `write_entry` seam; the engine already accepts those media (`GATE_MEDIA`). #64 threads `served_by` through the run engine's `NODE_RESULT_SCHEMA.verification` into `transition_log`, where `compute_completeness._served_by` already reads it, and refuses a `verified` runtime claim that lacks it. #65 makes `validate_bootstrap` emit the coverage gate's repair loop into `unattended-run-readiness-spec.json` and makes readiness refuse the gate+policy combination without it.

**Tech Stack:** Python 3 (pytest), Node (run-engine tests via `node --test`), Markdown capability texts. Claude and Codex meta-skill share `capabilities/`, `scripts/`, `tests/` by symlink; only `knowledge/orchestrator-template.md` and `knowledge/flow-template.py` are separate files.

**Spec:** GitHub issues #63, #64, #65 (children of #53 / ADR-0008, `docs/adr/0008-verdicts-leave-the-run-the-engine-is-shared.md`).

## Global Constraints

- Validators return a reason string, never raise; reason strings are Chinese and match neighbours (`经 mock 层（…）的 runtime 不能判 done`, `机械门证据无输出文件（构建 / 测试 / 契约比对的捕获输出）`).
- Capability texts state acceptance criteria and contracts, not method (CLAUDE.md, #19 principle).
- Human report files keep their names per the `.allforai/` output contract in CLAUDE.md; entries are the machine record beside them.
- Suites run per directory (two `test_render_report.py` files collide): `claude/meta-skill/tests/unit`, `shared/evidence-engine`, `claude/superstorm/scripts`, `codex/cross-exam-skill/scripts`, `shared/scripts/orchestrator`. Run-engine tests: `node --test claude/meta-skill/knowledge/run-engine/tests/`.
- `shared/scripts/orchestrator/{capture_evidence,check_evidence,compute_completeness}.py` are byte-identical copies of the `claude/meta-skill/scripts` versions and must be re-copied after any edit (`shared/scripts/orchestrator/test_verification_honesty.py` checks).
- Never stage `docs/feedback/inbox/`.
- Commit trailer on every commit:
  ```
  Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
  Claude-Session: https://claude.ai/code/session_019P9YwUQfRBh2BhcLJGpXmo
  ```
- Pre-commit hooks take ~5 minutes; write commit messages to a file and commit with `-F`.

---

## File Structure

| File | Responsibility |
|---|---|
| `claude/meta-skill/scripts/capture_evidence.py` | `write_entry(run_dir, draft, root, node_id, capability, artifacts=(), now=None) -> (entry, reason)` — unchanged API; #63 uses it as is |
| `claude/meta-skill/scripts/check_evidence.py` | `entry_reason`, `entries_reason`, `--entries` CLI — unchanged; #63 tests drive it |
| `claude/meta-skill/knowledge/capabilities/{compile-verify,spec-compliance-verify,security-verify,pipeline-closure-verify}.md` | #63: each gains an "Evidence Entries (ledger shape, ADR-0008)" section with `medium: build` or `contract` |
| `claude/meta-skill/knowledge/verification-protocol.md` | #63: rule 7 lists the four mechanical gates |
| `claude/meta-skill/scripts/orchestrator/evidence_freshness.py` | #63: `outputs()` already treats `evidence-entries/<node>.json` as node outputs for runtime gates; one test proves it for a `build` gate too |
| `claude/meta-skill/tests/unit/test_mechanical_gate_entries.py` | #63: new test file |
| `claude/meta-skill/knowledge/run-engine/engine-core.js` | #64: `NODE_RESULT_SCHEMA.verification.served_by`, `runtimeVerificationReason(result)`, wired in `routeOutcome` |
| `claude/meta-skill/knowledge/run-engine/run-engine.workflow.js` | #64: regenerated shell (inlines engine-core verbatim) |
| `claude/meta-skill/knowledge/run-engine/tests/engine-core.test.js` | #64: new tests |
| `claude/meta-skill/scripts/compute_completeness.py` | #64: `hollow_reason` refuses a runtime `verified` claim with no `served_by` |
| `claude/meta-skill/tests/unit/test_compute_completeness.py` | #64: new test |
| `codex/meta-skill/knowledge/flow-template.py` | #64: Codex twin of the schema requirement |
| `claude/meta-skill/knowledge/node-spec-template.md`, `capabilities/{product-verify,runtime-smoke-verify,test-verify}.md` | #64: state who fills `served_by` |
| `claude/meta-skill/scripts/orchestrator/validate_bootstrap.py` | #65: `coverage_gate_loop(nodes)` emitted into the readiness spec |
| `claude/meta-skill/scripts/orchestrator/validate_unattended_readiness.py` | #65: `missing_coverage_repair_loop` blocker |
| `claude/meta-skill/knowledge/bootstrap-planning.md` | #65: the loop's three nodes as a planning rule |
| `claude/meta-skill/tests/unit/test_validate_unattended_readiness.py`, `test_validate_bootstrap.py` | #65: new tests |

---

### Task 1: `#63` — compile-verify emits `medium: build` entries

**Files:**
- Modify: `claude/meta-skill/knowledge/capabilities/compile-verify.md` (append section after "## Rules" or at end)
- Modify: `claude/meta-skill/knowledge/verification-protocol.md:55-63` (rule 7)
- Test: `claude/meta-skill/tests/unit/test_mechanical_gate_entries.py` (create)

**Interfaces:**
- Consumes: `capture_evidence.write_entry(run_dir, draft, root, node_id, capability)`; `check_evidence.entries_reason(run_dir, root, node_id)`; engine `GATE_MEDIA = ('build','test','contract')`, `OUTPUT_SUFFIXES = {'.txt','.log','.json','.md'}`.
- Produces: the convention every later task copies — `<run>/evidence-entries/<node_id>.json` with `medium: "build"` and an evidence dir holding the `capture_evidence/v1` build output; test helper `_gate_project(tmp_path, monkeypatch)` and `_gate_draft(run, node, medium, q)`.

- [ ] **Step 1: Write the failing test**

```python
# claude/meta-skill/tests/unit/test_mechanical_gate_entries.py
"""Mechanical gates (compile, spec-compliance, security, pipeline-closure) write ledger-shaped entries
with medium build or contract — the media a later /cross-exam admits as gates (#63, ADR-0008)."""
import json
import subprocess
from pathlib import Path

import pytest

from .. import module_isolation

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
_capture = module_isolation.load("capture_evidence", SCRIPTS / "capture_evidence.py")
_check = module_isolation.load("check_evidence", SCRIPTS / "check_evidence.py")
write_entry, entries_reason = _capture.write_entry, _check.entries_reason


def _git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def gate_project(tmp_path, monkeypatch):
    monkeypatch.setenv("GIT_AUTHOR_NAME", "t"); monkeypatch.setenv("GIT_AUTHOR_EMAIL", "t@x")
    monkeypatch.setenv("GIT_COMMITTER_NAME", "t"); monkeypatch.setenv("GIT_COMMITTER_EMAIL", "t@x")
    _git(tmp_path, "init", "-q"); (tmp_path / "app.py").write_text("print(1)\n")
    _git(tmp_path, "add", "."); _git(tmp_path, "commit", "-qm", "init")
    return tmp_path


def _gate_draft(run, node, medium, q, output="ok\n", suffix=".log"):
    d = run / "evidence" / node / "q01"
    d.mkdir(parents=True, exist_ok=True)
    (d / ("capture" + suffix)).write_text(output)
    return {"q": q, "facet": "F1", "medium": medium, "verdict": "done",
            "evidence": {"dir": "evidence/%s/q01/" % node, "key_observation": "captured"}}


def test_compile_verify_writes_a_build_entry_cross_exam_can_admit(gate_project):
    run = gate_project / ".allforai/compile-verify"
    node = "compile-verify-web"
    draft = _gate_draft(run, node, "build", "npm run build 在真实树上过吗？", "vite v5 built in 1.2s\n")
    entry, reason = write_entry(run, draft, gate_project, node, "compile-verify")
    assert reason == "", reason
    assert entry["medium"] == "build" and "served_by" not in entry
    assert entry["author"] == {"pipeline": "meta-skill/run", "node_id": node, "capability": "compile-verify"}
    assert entries_reason(run, gate_project, node) == ""


def test_a_failed_build_is_a_gap_entry_never_omitted(gate_project):
    run = gate_project / ".allforai/compile-verify"
    node = "compile-verify-web"
    draft = {**_gate_draft(run, node, "build", "构建过吗？", "error TS2304\n"), "verdict": "gap"}
    entry, reason = write_entry(run, draft, gate_project, node, "compile-verify")
    assert reason == "" and entry["verdict"] == "gap"


def test_a_build_entry_without_captured_output_is_refused(gate_project):
    run = gate_project / ".allforai/compile-verify"
    node = "compile-verify-web"
    draft = _gate_draft(run, node, "build", "构建过吗？", suffix=".png")   # a picture is not a captured output
    _, reason = write_entry(run, draft, gate_project, node, "compile-verify")
    assert "机械门证据无输出文件" in reason


def test_a_stale_build_entry_is_refused_at_gate_time(gate_project):
    run = gate_project / ".allforai/compile-verify"
    node = "compile-verify-web"
    draft = _gate_draft(run, node, "build", "构建过吗？")
    assert write_entry(run, draft, gate_project, node, "compile-verify")[1] == ""
    (gate_project / "app.py").write_text("print(2)\n")
    assert "构建标识不匹配" in entries_reason(run, gate_project, node)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest -q claude/meta-skill/tests/unit/test_mechanical_gate_entries.py -v`
Expected: all four PASS already — the engine accepts `build` since #60 and `write_entry` is medium-agnostic. This task's failing part is the **contract**: the capability text and protocol rule say nothing about it, so no gate would write one. Confirm with:

Run: `grep -c "evidence-entries" claude/meta-skill/knowledge/capabilities/compile-verify.md`
Expected: `0`

- [ ] **Step 3: Write the capability contract**

Append to `claude/meta-skill/knowledge/capabilities/compile-verify.md`:

```markdown

### Evidence Entries (ledger shape, ADR-0008)

Beside the build result it reports, the node writes machine entries in cross-exam's ledger-entry
shape to `.allforai/compile-verify/evidence-entries/<node_id>.json` (`{"schema":
"evidence-entries/v1", "entries": [...]}`): one entry per build command it ran. The entry is the
machine record a later `/cross-exam` admits as a **gate** (`medium: build` is mechanical media)
instead of rerunning the build; it never closes a verdict.

An entry is admissible when, and only when, all of the following hold. The shared engine
(`${CLAUDE_PLUGIN_ROOT}/scripts/engine`) decides the shape; `capture_evidence.py entry` records what
the node must not author and refuses a draft that fails; `check_evidence.py --entries
.allforai/compile-verify --node <node_id>` re-checks every entry against the tree at gate time.
**The gate is not passed while any entry is refused, or while the file is missing or empty.**

- `medium` is `build`; `verdict` is `done` (the build succeeded), `gap` (it failed — a failed build
  is an entry, never an omission) or `unprovable` (no toolchain in this environment). No
  `served_by`: a build has no request destination.
- `build` is the whole-tree identity from the engine (commit + working-tree snapshot digest +
  artifact digest), with `.allforai`, `.claude`, `.codex` outside it; the build's own output
  directory (`dist/`, `build/`, the `.apk`) is named in `build_artifacts` so it enters the identity.
- `probed_at` carries a timezone offset.
- `evidence.dir` is a non-empty directory under `.allforai/compile-verify/evidence/`, relative to
  the run directory, holding the `capture_evidence/v1` record of the real build command — its
  captured output is what makes the entry admissible; a directory holding only images is refused
  (`机械门证据无输出文件`).
- `author` is `{pipeline: "meta-skill/run", node_id, capability: "compile-verify"}`, written by
  `capture_evidence.py`, never by hand.
```

Edit `claude/meta-skill/knowledge/verification-protocol.md` rule 7: find the sentence beginning `test-verify and visual-verify write, beside their human reports,` (line ≈55) and change the gate list to read:

```markdown
   product-verify, runtime-smoke-verify, test-verify and visual-verify (runtime media) and
   compile-verify, spec-compliance-verify, security-verify and pipeline-closure-verify (mechanical
   media: `build` / `contract`) write, beside their human reports, `<run>/evidence-entries/<node_id>.json` in
```

- [ ] **Step 4: Run the tests and the contract grep**

Run: `python3 -m pytest -q claude/meta-skill/tests/unit/test_mechanical_gate_entries.py && grep -c "evidence-entries" claude/meta-skill/knowledge/capabilities/compile-verify.md`
Expected: `4 passed`, then `2` or more.

- [ ] **Step 5: Commit**

```bash
cat > /tmp/msg63a.txt <<'EOF'
meta-skill: compile-verify emits medium build entries a later /cross-exam admits as a gate (#63)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_019P9YwUQfRBh2BhcLJGpXmo
EOF
git add claude/meta-skill/knowledge/capabilities/compile-verify.md claude/meta-skill/knowledge/verification-protocol.md claude/meta-skill/tests/unit/test_mechanical_gate_entries.py
git commit -q -F /tmp/msg63a.txt
```

---

### Task 2: `#63` — the three contract gates emit `medium: contract` entries

**Files:**
- Modify: `claude/meta-skill/knowledge/capabilities/spec-compliance-verify.md`, `security-verify.md`, `pipeline-closure-verify.md` (append section at end of each)
- Test: `claude/meta-skill/tests/unit/test_mechanical_gate_entries.py` (append)

**Interfaces:**
- Consumes: `_gate_draft`, `gate_project` from Task 1; `write_entry`; `entries_reason`.
- Produces: nothing new; the same convention with `medium: "contract"` and the diff/presence check as the captured output.

- [ ] **Step 1: Write the failing test**

Append to `claude/meta-skill/tests/unit/test_mechanical_gate_entries.py`:

```python


@pytest.mark.parametrize("capability, run_name, output", [
    ("spec-compliance-verify", "spec-compliance", '{"endpoints": {"declared": 20, "present": 20, "drifted": []}}\n'),
    ("security-verify", "security-verify", '{"decisions_checked": 6, "missing": []}\n'),
    ("pipeline-closure-verify", "pipeline-closure", '{"pipelines": [{"id": "checkout", "status": "complete"}]}\n'),
])
def test_contract_gates_write_contract_entries(gate_project, capability, run_name, output):
    run = gate_project / ".allforai" / run_name
    node = capability + "-1"
    draft = _gate_draft(run, node, "contract", capability + " 的比对在真实树上做了吗？", output, suffix=".json")
    entry, reason = write_entry(run, draft, gate_project, node, capability)
    assert reason == "", reason
    assert entry["medium"] == "contract" and "served_by" not in entry
    assert entry["author"]["capability"] == capability
    assert entries_reason(run, gate_project, node) == ""


def test_a_contract_entry_whose_diff_was_not_captured_is_refused(gate_project):
    run = gate_project / ".allforai/spec-compliance"
    node = "spec-compliance-verify-1"
    d = run / "evidence" / node / "q01"; d.mkdir(parents=True)
    (d / "diff.png").write_bytes(b"\x89PNG")
    draft = {"q": "比对做了吗？", "facet": "F1", "medium": "contract", "verdict": "done",
             "evidence": {"dir": "evidence/%s/q01/" % node, "key_observation": "x"}}
    _, reason = write_entry(run, draft, gate_project, node, "spec-compliance-verify")
    assert "机械门证据无输出文件" in reason
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest -q claude/meta-skill/tests/unit/test_mechanical_gate_entries.py -v`
Expected: PASS (engine already accepts `contract`). Contract gap confirmed by:

Run: `grep -c "evidence-entries" claude/meta-skill/knowledge/capabilities/spec-compliance-verify.md claude/meta-skill/knowledge/capabilities/security-verify.md claude/meta-skill/knowledge/capabilities/pipeline-closure-verify.md`
Expected: `0` for each.

- [ ] **Step 3: Write the three capability contracts**

Append this block to **each** of the three files, substituting `<run>` and `<capability>`:

| file | `<run>` | `<capability>` | `<what was captured>` |
|---|---|---|---|
| spec-compliance-verify.md | `spec-compliance` | `spec-compliance-verify` | the per-endpoint / per-table / per-message diff it computed |
| security-verify.md | `security-verify` | `security-verify` | the per-decision presence check it computed |
| pipeline-closure-verify.md | `pipeline-closure` | `pipeline-closure-verify` | the per-pipeline path trace it computed |

```markdown

### Evidence Entries (ledger shape, ADR-0008)

Beside `<run>-report.json`, the node writes machine entries in cross-exam's ledger-entry shape to
`.allforai/<run>/evidence-entries/<node_id>.json` (`{"schema": "evidence-entries/v1", "entries":
[...]}`): one entry per artifact it compared. The entry is the machine record a later `/cross-exam`
admits as a **gate** (`medium: contract` is mechanical media) instead of redoing the comparison; it
never closes a verdict.

An entry is admissible when, and only when, all of the following hold. The shared engine
(`${CLAUDE_PLUGIN_ROOT}/scripts/engine`) decides the shape; `capture_evidence.py entry` records what
the node must not author and refuses a draft that fails; `check_evidence.py --entries
.allforai/<run> --node <node_id>` re-checks every entry against the tree at gate time.
**The gate is not passed while any entry is refused, or while the file is missing or empty.**

- `medium` is `contract`; `verdict` is `done` (everything declared is present and matches), `gap`
  (something is missing or drifted — named in `key_observation`) or `unprovable` (the artifact it
  compares against is absent). No `served_by`: a comparison has no request destination.
- `build` is the whole-tree identity from the engine (commit + working-tree snapshot digest +
  artifact digest), with `.allforai`, `.claude`, `.codex` outside it.
- `probed_at` carries a timezone offset.
- `evidence.dir` is a non-empty directory under `.allforai/<run>/evidence/`, relative to the run
  directory, holding <what was captured> as a `.json` or `.md` file — that captured output is what
  makes the entry admissible; a directory holding only images is refused (`机械门证据无输出文件`).
- `author` is `{pipeline: "meta-skill/run", node_id, capability: "<capability>"}`, written by
  `capture_evidence.py`, never by hand.
```

- [ ] **Step 4: Run the tests and the contract grep**

Run: `python3 -m pytest -q claude/meta-skill/tests/unit/test_mechanical_gate_entries.py && grep -c "evidence-entries" claude/meta-skill/knowledge/capabilities/spec-compliance-verify.md claude/meta-skill/knowledge/capabilities/security-verify.md claude/meta-skill/knowledge/capabilities/pipeline-closure-verify.md`
Expected: `8 passed`; each grep ≥ 2.

- [ ] **Step 5: Commit**

```bash
cat > /tmp/msg63b.txt <<'EOF'
meta-skill: spec-compliance, security and pipeline-closure gates emit medium contract entries (#63)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_019P9YwUQfRBh2BhcLJGpXmo
EOF
git add claude/meta-skill/knowledge/capabilities/spec-compliance-verify.md claude/meta-skill/knowledge/capabilities/security-verify.md claude/meta-skill/knowledge/capabilities/pipeline-closure-verify.md claude/meta-skill/tests/unit/test_mechanical_gate_entries.py
git commit -q -F /tmp/msg63b.txt
```

---

### Task 3: `#63` — cross-exam admits the four mechanical gates, freshness tracks their entries

**Files:**
- Test: `claude/superstorm/scripts/test_render_report.py` (append to `class TestAuthorEvidence`)
- Test: `codex/cross-exam-skill/scripts/test_render_report.py` (append to `class TestAuthorEvidence`)
- Test: `claude/meta-skill/tests/unit/test_evidence_freshness.py` (append)

**Interfaces:**
- Consumes: `TestAuthorEvidence._author(self, q, medium="test", verdict="done", **extra)` and `_run(self, tmp, entries, files=None, dirty=None)` (existing helpers in both renderer suites; `_author` sets `author`, `build`, `probed_at`, `readback`, an evidence dir with `pytest.json`); `evidence_freshness.outputs(root, node, kind='evidence')`.
- Produces: proof, no new symbols.

- [ ] **Step 1: Write the failing tests**

Append inside `class TestAuthorEvidence` in **both** `test_render_report.py` files (identical text):

```python
    def test_every_mechanical_medium_is_admitted_as_a_gate(self):
        # build and contract entries from compile / spec-compliance / security / pipeline-closure
        # land in the author section as gates; the facet still needs a prober for a verdict
        for medium, capability in (("build", "compile-verify"), ("contract", "spec-compliance-verify"),
                                   ("contract", "security-verify"), ("contract", "pipeline-closure-verify")):
            with tempfile.TemporaryDirectory() as tmp:
                e = self._author("这道机械门在真实树上过了吗？", medium=medium)
                e["author"]["capability"] = capability
                report = render(self._run(tmp, [e]))
                self.assertIn("## 作者证据", report, medium)
                self.assertIn("门通过", report, medium)
                self.assertIn("无法自证：1", report, medium)   # a gate alone never closes a verdict
```

Append to `claude/meta-skill/tests/unit/test_evidence_freshness.py`:

```python


def test_a_mechanical_gate_entries_file_is_a_node_output(tmp_path):
    """evidence_freshness sees build/contract entries the same way it sees runtime ones."""
    from .. import module_isolation
    from pathlib import Path
    scripts = Path(__file__).resolve().parents[2] / "scripts" / "orchestrator"
    ef = module_isolation.load("evidence_freshness", scripts / "evidence_freshness.py")
    node = {"node_id": "compile-verify-web", "capability": "compile-verify",
            "exit_artifacts": [".allforai/compile-verify/compile-report.json"]}
    (tmp_path / ".allforai/compile-verify/evidence-entries").mkdir(parents=True)
    (tmp_path / ".allforai/compile-verify/evidence-entries/compile-verify-web.json").write_text(
        '{"schema": "evidence-entries/v1", "entries": []}')
    outs = ef.outputs(tmp_path, node, kind="evidence")
    assert any(str(o).endswith("evidence-entries/compile-verify-web.json") for o in outs), outs
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest -q claude/superstorm/scripts/test_render_report.py -k mechanical_medium -v`
Expected: PASS for `build` (already in `GATE_MEDIA`); PASS for `contract`. If any FAIL, the message names which — fix nothing in renderers; the renderers admit every `GATE_MEDIA` since #60. This test is a regression guard.

Run: `python3 -m pytest -q claude/meta-skill/tests/unit/test_evidence_freshness.py -k mechanical_gate -v`
Expected: PASS if `outputs()` matches on the `evidence-entries` path generically; FAIL with an empty `outs` if it filters by a runtime-capability list. In that case proceed to Step 3; otherwise skip to Step 4.

- [ ] **Step 3: If `outputs()` filtered by capability — remove the filter**

Open `claude/meta-skill/scripts/orchestrator/evidence_freshness.py`, function `outputs(root, node, kind='evidence')`. If it contains a capability allow-list such as

```python
    if node.get('capability') in ('product-verify', 'runtime-smoke-verify', 'test-verify', 'visual-verify'):
```

replace that condition with a path-existence check — the entries file is an output for whichever node wrote it:

```python
    entries = root / run_dir_of(node) / 'evidence-entries' / (node['node_id'] + '.json')
    if entries.is_file():
```

(`run_dir_of` = the existing helper that maps a node's first `exit_artifacts` path to its `.allforai/<run>` directory; reuse whatever name the file already uses for that.)

- [ ] **Step 4: Run all three suites**

Run: `python3 -m pytest -q claude/superstorm/scripts && python3 -m pytest -q codex/cross-exam-skill/scripts && python3 -m pytest -q claude/meta-skill/tests/unit/test_evidence_freshness.py claude/meta-skill/tests/unit/test_mechanical_gate_entries.py`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
cat > /tmp/msg63c.txt <<'EOF'
cross-exam + meta-skill: the four mechanical gates are admitted as gates; freshness tracks their entries (#63)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_019P9YwUQfRBh2BhcLJGpXmo
EOF
git add claude/superstorm/scripts/test_render_report.py codex/cross-exam-skill/scripts/test_render_report.py claude/meta-skill/tests/unit/test_evidence_freshness.py claude/meta-skill/scripts/orchestrator/evidence_freshness.py
git commit -q -F /tmp/msg63c.txt
```

---

### Task 4: `#64` — `compute_completeness` refuses a runtime `verified` claim with no `served_by`

**Files:**
- Modify: `claude/meta-skill/scripts/compute_completeness.py:43-50` (`hollow_reason`)
- Modify: `shared/scripts/orchestrator/compute_completeness.py` (byte copy)
- Test: `claude/meta-skill/tests/unit/test_compute_completeness.py` (append; replace one test)

**Interfaces:**
- Consumes: `_served_by(entry) -> dict` (reads `entry.verification.served_by`, falls back to `entry.served_by`, else `{}`); `fixture_match_reason`.
- Produces: `hollow_reason(entry, base_dir=".") -> str` now returns `"runtime 节点未报请求去向 served_by（host / process / mock_layers），不计 verified"` when `verification.method` is a runtime method and `served_by` is absent. `RUNTIME_METHODS = ("real-run", "real-api", "db-query", "screenshot")` — `real-test` is a suite run (mechanical) and is exempt.

- [ ] **Step 1: Write the failing test**

Open `claude/meta-skill/tests/unit/test_compute_completeness.py`. Replace the existing test `test_hollow_reason_is_empty_without_served_by` (line ≈158) with:

```python
def test_a_runtime_claim_without_served_by_is_not_verified():
    """Nothing asked the node where its requests went, so nothing can say they went to the real thing."""
    for method in ("real-run", "real-api", "db-query", "screenshot"):
        entry = {"node_id": "n", "verification": {"method": method, "evidence_path": "e.json"}}
        reason = hollow_reason(entry)
        assert "served_by" in reason and "不计 verified" in reason, (method, reason)


def test_a_suite_run_and_a_generated_only_node_need_no_served_by():
    # real-test is a mechanical run; none never counted anyway
    for method in ("real-test", "none"):
        assert hollow_reason({"node_id": "n", "verification": {"method": method}}) == ""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest -q claude/meta-skill/tests/unit/test_compute_completeness.py -k "without_served_by or need_no_served_by" -v`
Expected: `test_a_runtime_claim_without_served_by_is_not_verified` FAIL (`hollow_reason` returns `""`); the other PASS.

- [ ] **Step 3: Implement**

In `claude/meta-skill/scripts/compute_completeness.py`, above `def hollow_reason`, add:

```python
# a runtime method exercises the product; the node must say where its requests went. real-test is a
# suite run — a mechanical gate — and needs no destination.
RUNTIME_METHODS = ("real-run", "real-api", "db-query", "screenshot")
```

and change the start of `hollow_reason` from

```python
def hollow_reason(entry, base_dir="."):
    """..."""
    served = _served_by(entry)
    layers = served.get("mock_layers")
```

to

```python
def hollow_reason(entry, base_dir="."):
    """..."""
    served = _served_by(entry)
    method = (entry.get("verification") or {}).get("method")
    if method in RUNTIME_METHODS and not served:
        return "runtime 节点未报请求去向 served_by（host / process / mock_layers），不计 verified"
    layers = served.get("mock_layers")
```

(keep the existing docstring). Then copy:

```bash
cp claude/meta-skill/scripts/compute_completeness.py shared/scripts/orchestrator/compute_completeness.py
```

- [ ] **Step 4: Run the suites**

Run: `python3 -m pytest -q claude/meta-skill/tests/unit/test_compute_completeness.py && python3 -m pytest -q shared/scripts/orchestrator`
Expected: all PASS. If an existing test in `test_compute_completeness.py` built a runtime `verified` entry without `served_by` and expected `verified`, it now fails correctly: give that fixture `"served_by": {"host": "localhost:3000", "process": "node", "mock_layers": []}` under `verification`.

- [ ] **Step 5: Commit**

```bash
cat > /tmp/msg64a.txt <<'EOF'
meta-skill: a runtime verified claim with no served_by is not counted (#64)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_019P9YwUQfRBh2BhcLJGpXmo
EOF
git add claude/meta-skill/scripts/compute_completeness.py shared/scripts/orchestrator/compute_completeness.py claude/meta-skill/tests/unit/test_compute_completeness.py
git commit -q -F /tmp/msg64a.txt
```

---

### Task 5: `#64` — the run engine asks runtime nodes for `served_by` and refuses a claim without it

**Files:**
- Modify: `claude/meta-skill/knowledge/run-engine/engine-core.js:63-80` (schema), `:201-208` (`routeOutcome`), `:327-333` (prompt), `:344-346` (`commitPrompt`)
- Modify: `claude/meta-skill/knowledge/run-engine/run-engine.workflow.js` (regenerate — see Step 4)
- Modify: `codex/meta-skill/knowledge/flow-template.py` (twin rule)
- Test: `claude/meta-skill/knowledge/run-engine/tests/engine-core.test.js` (append)

**Interfaces:**
- Consumes: `NODE_RESULT_SCHEMA`, `routeOutcome(result) -> 'done'|'soft'|'hard'|'accepted'`, `commitPrompt(result)`.
- Produces: `NODE_RESULT_SCHEMA.properties.verification.properties.served_by = { type:'object', properties:{ host:{type:'string'}, process:{type:'string'}, mock_layers:{type:'array', items:{type:'string'}}, fixtures:{type:'array', items:{type:'string'}} }, required:['host','process','mock_layers'] }`; `RUNTIME_METHODS = ['real-run','real-api','db-query','screenshot']`; `runtimeVerificationReason(result) -> string` (`''` or `'runtime verification without served_by: ...'`); `routeOutcome` returns `'soft'` with the reason appended to `result.blocking_findings` when the claim is unbacked.

- [ ] **Step 1: Write the failing tests**

Append to `claude/meta-skill/knowledge/run-engine/tests/engine-core.test.js`:

```js
test('NODE_RESULT_SCHEMA: verification may carry served_by with host, process, mock_layers, fixtures', () => {
  const sb = core.NODE_RESULT_SCHEMA.properties.verification.properties.served_by
  assert.ok(sb, 'served_by missing from verification schema')
  assert.deepEqual(sb.required, ['host', 'process', 'mock_layers'])
  assert.equal(sb.properties.fixtures.type, 'array')
})

test('runtimeVerificationReason: a runtime method without served_by names the field', () => {
  for (const method of core.RUNTIME_METHODS) {
    const r = { node_id: 'n', outcome: 'passed', blocking_findings: [],
      verification: { method, evidence_path: 'e.json', verifier: 'v', claim: 'c' } }
    assert.match(core.runtimeVerificationReason(r), /served_by/, method)
  }
})

test('runtimeVerificationReason: real-test and none need no served_by; a served_by claim passes', () => {
  assert.equal(core.runtimeVerificationReason({ verification: { method: 'real-test' } }), '')
  assert.equal(core.runtimeVerificationReason({ verification: { method: 'none' } }), '')
  assert.equal(core.runtimeVerificationReason({ verification: { method: 'real-api',
    served_by: { host: 'localhost:3000', process: 'node', mock_layers: [] } } }), '')
})

test('routeOutcome: a passed runtime claim without served_by is soft, not done, and the finding says why', () => {
  const r = { outcome: 'passed', blocking_findings: [],
    verification: { method: 'real-api', evidence_path: 'e.json', verifier: 'v', claim: 'c' } }
  assert.equal(core.routeOutcome(r), 'soft')
  assert.ok(r.blocking_findings.some(f => f.type === 'unbacked_runtime_verification'), JSON.stringify(r.blocking_findings))
})

test('commitPrompt: served_by is recorded verbatim inside verification', () => {
  const p = core.commitPrompt({ node_id: 'n', artifacts_written: [], verification: { method: 'real-api',
    served_by: { host: 'localhost:3000', process: 'node', mock_layers: ['msw'] } } })
  assert.match(p, /"served_by":\{"host":"localhost:3000","process":"node","mock_layers":\["msw"\]\}/)
})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `node --test claude/meta-skill/knowledge/run-engine/tests/engine-core.test.js`
Expected: the five new tests FAIL (`served_by` undefined in schema; `core.RUNTIME_METHODS` / `runtimeVerificationReason` not exported; `routeOutcome` returns `'done'`; `commitPrompt` already passes — `JSON.stringify(v)` is verbatim — so that one may PASS).

- [ ] **Step 3: Implement**

In `engine-core.js`:

(a) Inside `NODE_RESULT_SCHEMA.properties.verification.properties`, after `claim: { type: 'string' }`, add:

```js
        ,
        served_by: { type: 'object',       // where the exercised code's requests went (ADR-0008, #64):
          properties: {                    // required for every runtime method; the hollow refusals read it
            host: { type: 'string' },
            process: { type: 'string' },
            mock_layers: { type: 'array', items: { type: 'string' } },
            fixtures: { type: 'array', items: { type: 'string' } }
          },
          required: ['host', 'process', 'mock_layers'] }
```

(b) Above `function routeOutcome`, add:

```js
// A runtime method exercises the product, so the node must say where its requests went; without
// served_by nothing can tell a real backend from a mock, and compute_completeness will not count it.
// real-test is a suite run (mechanical) and none never counted.
const RUNTIME_METHODS = ['real-run', 'real-api', 'db-query', 'screenshot']

function runtimeVerificationReason(result) {
  const v = (result && result.verification) || {}
  if (!RUNTIME_METHODS.includes(v.method)) return ''
  const sb = v.served_by
  if (!sb || typeof sb !== 'object' || typeof sb.host !== 'string' || typeof sb.process !== 'string'
      || !Array.isArray(sb.mock_layers)) {
    return 'runtime verification without served_by (host / process / mock_layers): the node did not say where its requests went'
  }
  return ''
}
```

(c) Change `routeOutcome` to:

```js
function routeOutcome(result) {
  if (result.outcome === 'accepted_with_gaps') return 'accepted'
  const unbacked = runtimeVerificationReason(result)
  if (unbacked && result.outcome === 'passed') {
    result.blocking_findings = [...(result.blocking_findings || []),
      { type: 'unbacked_runtime_verification', detail: unbacked }]
  }
  const findings = result.blocking_findings || []
  if (result.outcome === 'passed' && findings.length === 0) return 'done'
  if (result.outcome === 'hard_fail') return 'hard'
  if (findings.some(f => f.type === 'cross_node' || f.suspected_root_node)) return 'hard'
  return 'soft'
}
```

(d) In the node prompt (line ≈327), change

```js
    'and RETURN verification: {method, evidence_path, verifier, claim}. If you only generated code',
```

to

```js
    'and RETURN verification: {method, evidence_path, verifier, claim, served_by}. served_by is',
    'REQUIRED for real-run / real-api / db-query / screenshot: {host, process, mock_layers[], fixtures[]}',
    '— the dev server or binary your requests reached, the mock layers in effect (MSW, nock, an',
    'in-memory DB; [] when none) and the fixture files a canned answer could have come from. A runtime',
    'claim without it is not counted as verified. If you only generated code',
```

(e) Add `RUNTIME_METHODS, runtimeVerificationReason` to the `module.exports` list at the end of the file (line ≈1006, next to `DAG_SCHEMA, NODE_RESULT_SCHEMA, ...`).

- [ ] **Step 4: Regenerate the workflow shell and run the tests**

`run-engine.workflow.js` inlines `engine-core.js` verbatim. Check `claude/meta-skill/knowledge/run-engine/README.md` for the regeneration command (it names a script or a marker pair); run it. If the README says the shell is assembled by a script, run that script; if it says "copy between the markers", do exactly that. Then:

Run: `node --test claude/meta-skill/knowledge/run-engine/tests/`
Expected: all PASS, including the five new ones.

- [ ] **Step 5: Codex twin and node-spec template**

In `codex/meta-skill/knowledge/flow-template.py`, find where a node result's `verification` is recorded into the transition log (search `verification`). Add, immediately before it is written, the same rule as a Python function and use it:

```python
RUNTIME_METHODS = ("real-run", "real-api", "db-query", "screenshot")


def runtime_verification_reason(result):
    """A runtime method must say where its requests went; a claim without served_by is not verified."""
    v = result.get("verification") or {}
    if v.get("method") not in RUNTIME_METHODS:
        return ""
    sb = v.get("served_by")
    if not isinstance(sb, dict) or not isinstance(sb.get("host"), str) or not isinstance(sb.get("process"), str) \
            or not isinstance(sb.get("mock_layers"), list):
        return "runtime verification without served_by (host / process / mock_layers): the node did not say where its requests went"
    return ""
```

and where the Codex flow routes a `passed` result, append `{"type": "unbacked_runtime_verification", "detail": reason}` to `blocking_findings` when the reason is non-empty, so the outcome is soft, mirroring `routeOutcome`.

In `claude/meta-skill/knowledge/node-spec-template.md`, in the section that describes the `verification` return, add one bullet:

```markdown
- `served_by` (required when `method` is `real-run`, `real-api`, `db-query` or `screenshot`): `{host, process, mock_layers[], fixtures[]}` — where the exercised code's requests went. A runtime claim without it is not counted as verified; a non-empty `mock_layers` or a response equal to a listed fixture cannot be `done` (ADR-0008, #64).
```

In `claude/meta-skill/knowledge/capabilities/product-verify.md`, `runtime-smoke-verify.md`, `test-verify.md`: locate the existing `served_by` bullet in each "Evidence Entries" section and prepend one sentence:

```markdown
  The node also returns the same `served_by` inside its `verification` result to the run engine; the engine does not count a runtime claim without it.
```

- [ ] **Step 6: Run everything this task touches**

Run: `node --test claude/meta-skill/knowledge/run-engine/tests/ && python3 -m pytest -q claude/meta-skill/tests/unit/test_run_policy_session.py claude/meta-skill/tests/unit/test_compute_completeness.py && python3 -c "import ast,sys; ast.parse(open('codex/meta-skill/knowledge/flow-template.py').read())"`
Expected: all PASS; the `ast.parse` prints nothing.

- [ ] **Step 7: Commit**

```bash
cat > /tmp/msg64b.txt <<'EOF'
meta-skill: the run engine asks runtime nodes for served_by; an unbacked runtime claim is soft, not done (#64)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_019P9YwUQfRBh2BhcLJGpXmo
EOF
git add claude/meta-skill/knowledge/run-engine/engine-core.js claude/meta-skill/knowledge/run-engine/run-engine.workflow.js claude/meta-skill/knowledge/run-engine/tests/engine-core.test.js codex/meta-skill/knowledge/flow-template.py claude/meta-skill/knowledge/node-spec-template.md claude/meta-skill/knowledge/capabilities/product-verify.md claude/meta-skill/knowledge/capabilities/runtime-smoke-verify.md claude/meta-skill/knowledge/capabilities/test-verify.md
git commit -q -F /tmp/msg64b.txt
```

---

### Task 6: `#65` — readiness refuses the coverage gate + `auto_fix_once` without a declared loop

**Files:**
- Modify: `claude/meta-skill/scripts/orchestrator/validate_unattended_readiness.py` (new `_coverage_gate_loop_blockers`, called from the same place as `_verdict_entry_blockers`, line ≈564)
- Test: `claude/meta-skill/tests/unit/test_validate_unattended_readiness.py` (append)

**Interfaces:**
- Consumes: `_add(blockers, code, message, *, node_id=None)`; `_minimal_project(tmp_path, ...)`; `_with_workflow(tmp_path, workflow)`; `_repair_loop(**overrides)`; the readiness spec at `.allforai/bootstrap/unattended-run-readiness-spec.json` with `required_repair_loops: [{scope, qa_node_ids, repair_node_id, closure_node_ids, max_attempts}]`; the run policy at `.allforai/bootstrap/run-policy.json` with `on_needs_iteration`.
- Produces: blocker code `missing_coverage_repair_loop`; helper `coverage_gate_nodes(nodes) -> list[str]` (node ids whose `capability == "concept-acceptance"`).

- [ ] **Step 1: Write the failing tests**

Append to `claude/meta-skill/tests/unit/test_validate_unattended_readiness.py`:

```python


def _gate_node():
    return {"node_id": "concept-acceptance", "goal": "coverage gate", "capability": "concept-acceptance",
            "exit_artifacts": [{"path": ".allforai/concept-acceptance/acceptance-report.json"}]}


def _with_policy(tmp_path, on_needs_iteration):
    _write(tmp_path, ".allforai/bootstrap/run-policy.json", json.dumps({"on_needs_iteration": on_needs_iteration}))


def test_auto_fix_once_with_the_coverage_gate_needs_a_declared_repair_loop(tmp_path):
    _with_workflow(tmp_path, {"nodes": [_design_node(), _gate_node()],
                              "user_steps": ["/cross-exam", "/product-review"]})
    _with_policy(tmp_path, "auto_fix_once")
    report = validate_unattended_readiness(tmp_path)
    blocker = next(b for b in report["blockers"] if b["code"] == "missing_coverage_repair_loop")
    assert "required_repair_loops" in blocker["message"] and "concept-acceptance" in blocker["message"]
    assert blocker["node_id"] == "concept-acceptance"


def test_halt_with_report_needs_no_loop_for_the_coverage_gate(tmp_path):
    _with_workflow(tmp_path, {"nodes": [_design_node(), _gate_node()],
                              "user_steps": ["/cross-exam", "/product-review"]})
    _with_policy(tmp_path, "halt_with_report")
    report = validate_unattended_readiness(tmp_path)
    assert not [b for b in report["blockers"] if b["code"] == "missing_coverage_repair_loop"]


def test_a_declared_coverage_loop_satisfies_the_gate(tmp_path):
    gate, repair, rerun = _gate_node(), {
        "node_id": "concept-repair", "goal": "repair", "capability": "implement",
        "hard_blocked_by": ["concept-acceptance"],
        "exit_artifacts": [{"path": ".allforai/concept-acceptance/repair.json"}]}, {
        "node_id": "concept-acceptance-rerun", "goal": "rerun", "capability": "concept-acceptance",
        "hard_blocked_by": ["concept-repair", "concept-acceptance"],
        "exit_artifacts": [{"path": ".allforai/concept-acceptance/acceptance-report-2.json"}]}
    _with_workflow(tmp_path, {"nodes": [_design_node(), gate, repair, rerun],
                              "user_steps": ["/cross-exam", "/product-review"]})
    for n in ("concept-acceptance", "concept-repair", "concept-acceptance-rerun"):
        _write(tmp_path, f".allforai/bootstrap/node-specs/{n}.md", "non interactive work")
    _with_policy(tmp_path, "auto_fix_once")
    spec = json.loads((tmp_path / ".allforai/bootstrap/unattended-run-readiness-spec.json").read_text())
    spec["required_repair_loops"] = [_repair_loop(scope="concept-acceptance", qa_node_ids=["concept-acceptance"],
                                                  repair_node_id="concept-repair",
                                                  closure_node_ids=["concept-acceptance-rerun"])]
    _write(tmp_path, ".allforai/bootstrap/unattended-run-readiness-spec.json", json.dumps(spec))
    report = validate_unattended_readiness(tmp_path)
    assert not [b for b in report["blockers"] if b["code"] == "missing_coverage_repair_loop"], report
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest -q claude/meta-skill/tests/unit/test_validate_unattended_readiness.py -k "coverage" -v`
Expected: first test FAIL (`StopIteration` — no such blocker); second and third PASS (nothing fires yet).

- [ ] **Step 3: Implement**

In `validate_unattended_readiness.py`, add above `def _verdict_entry_blockers`:

```python
def coverage_gate_nodes(nodes: list[dict]) -> list[str]:
    """Node ids of the concept-acceptance coverage gate (ADR-0008): the gate whose missing-mapping list
    fires on_needs_iteration."""
    return [n["node_id"] for n in nodes
            if isinstance(n, dict) and n.get("capability") == "concept-acceptance" and isinstance(n.get("node_id"), str)]


def _coverage_gate_loop_blockers(project_root: str, nodes: list[dict], spec: dict,
                                 blockers: list[dict]) -> None:
    """auto_fix_once repairs only through a declared loop (ADR-0006). A workflow that carries the coverage
    gate and that policy without a loop naming the gate would halt at run time as an unauthorized
    repair; the plan is the fault, so it is refused here where the user can fix it."""
    policy_path = os.path.join(project_root, ".allforai", "bootstrap", "run-policy.json")
    try:
        with open(policy_path, encoding="utf-8") as fh:
            policy = json.load(fh)
    except (OSError, ValueError):
        return
    if not isinstance(policy, dict) or policy.get("on_needs_iteration") != "auto_fix_once":
        return
    loops = spec.get("required_repair_loops") if isinstance(spec, dict) else None
    declared = set()
    for loop in loops or []:
        if isinstance(loop, dict):
            declared.update(str(q) for q in (loop.get("qa_node_ids") or loop.get("qa_nodes") or []))
    for gate in coverage_gate_nodes(nodes):
        if gate not in declared:
            _add(blockers, "missing_coverage_repair_loop",
                 f"run-policy.json on_needs_iteration is auto_fix_once and node {gate} is the "
                 f"concept-acceptance coverage gate, but no unattended-run-readiness-spec.json "
                 f"required_repair_loops entry names it in qa_node_ids. auto_fix_once repairs only "
                 f"through a declared loop (ADR-0006): declare one with a repair node hard_blocked_by "
                 f"{gate} and a rerun of the gate blocked by the repair, or choose halt_with_report.",
                 node_id=gate)
```

Then at the call site (line ≈564), after `_verdict_entry_blockers(workflow, nodes, blockers, warnings)`, add:

```python
    _coverage_gate_loop_blockers(project_root, nodes, spec, blockers)
```

(`spec` is the readiness spec dict the function already loaded for `_validate_repair_loop_spec`; if it is loaded later than this line, move this call to just after that load. `os` and `json` are already imported in the file.)

- [ ] **Step 4: Run the suite**

Run: `python3 -m pytest -q claude/meta-skill/tests/unit/test_validate_unattended_readiness.py`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
cat > /tmp/msg65a.txt <<'EOF'
meta-skill: readiness refuses the coverage gate with auto_fix_once and no declared repair loop (#65)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_019P9YwUQfRBh2BhcLJGpXmo
EOF
git add claude/meta-skill/scripts/orchestrator/validate_unattended_readiness.py claude/meta-skill/tests/unit/test_validate_unattended_readiness.py
git commit -q -F /tmp/msg65a.txt
```

---

### Task 7: `#65` — bootstrap declares the coverage gate's loop; the run-time halt names the plan

**Files:**
- Modify: `claude/meta-skill/scripts/orchestrator/validate_bootstrap.py` (where `unattended-run-readiness-spec.json` is written/validated, line ≈1795-1814)
- Modify: `claude/meta-skill/knowledge/bootstrap-planning.md` (new subsection under the readiness-spec paragraph at line ≈224)
- Modify: `claude/meta-skill/knowledge/run-engine/engine-core.js` (`auto_fix_once` branch, line ≈551-557: halt message)
- Test: `claude/meta-skill/tests/unit/test_validate_bootstrap.py` (append)
- Test: `claude/meta-skill/knowledge/run-engine/tests/engine-core.test.js` (append)

**Interfaces:**
- Consumes: `coverage_gate_nodes(nodes)` from Task 6 (import by path the way `validate_bootstrap` already loads sibling modules, or re-declare the three-line function locally — it must stay identical); the readiness spec shape.
- Produces: `coverage_gate_loop(nodes) -> dict | None` in `validate_bootstrap.py` returning `{"scope": "concept-acceptance", "qa_node_ids": [gate], "repair_node_id": "<gate>-repair", "closure_node_ids": ["<gate>-rerun"], "max_attempts": 1}`; the two nodes it names must exist in `workflow.json`, so bootstrap planning is told to plan them (prose) and `validate_bootstrap` refuses a spec that names a node absent from the graph (the existing `_validate_repair_loop_spec` already does this at readiness time).

- [ ] **Step 1: Write the failing tests**

Append to `claude/meta-skill/tests/unit/test_validate_bootstrap.py` (use the file's existing project fixture; the name below assumes a helper `_project(tmp_path)` that writes a minimal `.allforai/bootstrap/` — if the file names it differently, use that name):

```python


def test_coverage_gate_loop_names_the_repair_and_rerun_nodes():
    from .. import module_isolation
    from pathlib import Path
    vb = module_isolation.load("validate_bootstrap", Path(__file__).resolve().parents[2] / "scripts/orchestrator/validate_bootstrap.py")
    nodes = [{"node_id": "concept-acceptance", "capability": "concept-acceptance"}]
    loop = vb.coverage_gate_loop(nodes)
    assert loop == {"scope": "concept-acceptance", "qa_node_ids": ["concept-acceptance"],
                    "repair_node_id": "concept-acceptance-repair",
                    "closure_node_ids": ["concept-acceptance-rerun"], "max_attempts": 1}
    assert vb.coverage_gate_loop([{"node_id": "design", "capability": "game-design"}]) is None
```

Append to `engine-core.test.js`:

```js
test('auto_fix_once halt for an undeclared coverage loop names the planning declaration', () => {
  assert.match(core.undeclaredCoverageLoopMessage('concept-acceptance'),
    /required_repair_loops/)
  assert.match(core.undeclaredCoverageLoopMessage('concept-acceptance'),
    /bootstrap/)
})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest -q claude/meta-skill/tests/unit/test_validate_bootstrap.py -k coverage_gate_loop -v && node --test claude/meta-skill/knowledge/run-engine/tests/engine-core.test.js`
Expected: both FAIL (`coverage_gate_loop` / `undeclaredCoverageLoopMessage` not defined).

- [ ] **Step 3: Implement**

In `validate_bootstrap.py`, near the other readiness-spec helpers (line ≈1790), add:

```python
def coverage_gate_loop(nodes):
    """The repair loop auto_fix_once needs for the concept-acceptance coverage gate (ADR-0008, #65):
    one bounded repair hard_blocked_by the gate, then a rerun of the gate blocked by the repair.
    None when the workflow has no coverage gate."""
    gates = [n["node_id"] for n in nodes
             if isinstance(n, dict) and n.get("capability") == "concept-acceptance" and isinstance(n.get("node_id"), str)]
    if not gates:
        return None
    gate = gates[0]
    return {"scope": "concept-acceptance", "qa_node_ids": [gate], "repair_node_id": gate + "-repair",
            "closure_node_ids": [gate + "-rerun"], "max_attempts": 1}
```

and where the readiness spec is written for a planned workflow (the code path that produces `unattended-run-readiness-spec.json` with `required_repair_loops`), when the run policy is `auto_fix_once` and `coverage_gate_loop(nodes)` is not `None` and no existing loop names the gate, append it to `required_repair_loops`. (If `validate_bootstrap.py` only validates and the spec is authored by the planning step, then instead add the check: an `auto_fix_once` policy with a coverage gate and no loop naming it is a bootstrap refusal with the same message as Task 6, so the plan is fixed before readiness.)

In `bootstrap-planning.md`, after the paragraph at line ≈224 that begins `Write \`.allforai/bootstrap/unattended-run-readiness-spec.json\``, add:

```markdown

### The coverage gate's repair loop

When the run policy may answer `on_needs_iteration: auto_fix_once` and the workflow carries the
concept-acceptance coverage gate, `required_repair_loops` declares a loop naming that gate in
`qa_node_ids`, and the workflow plans its two nodes: `<gate>-repair` (capability `implement`,
`hard_blocked_by: [<gate>]`, the one bounded repair) and `<gate>-rerun` (capability
`concept-acceptance`, `hard_blocked_by: [<gate>-repair, <gate>]`, the rerun that proves it). Without
the loop, `auto_fix_once` halts at run time as an unauthorized repair (ADR-0006) and the user cannot
see that the plan was the cause; the readiness gate refuses such a plan
(`missing_coverage_repair_loop`). `halt_with_report` and `accept` need no loop.
```

In `engine-core.js`, above the `auto_fix_once` branch (line ≈551), add:

```js
// The halt a user actually sees when auto_fix_once has no declared loop: name the planning
// declaration, not just "unauthorized", so the fix is found at bootstrap (#65).
function undeclaredCoverageLoopMessage(gateNodeId) {
  return `auto_fix_once: no required_repair_loops entry names ${gateNodeId} in qa_node_ids; the repair is unauthorized (ADR-0006). Declare the loop at bootstrap (bootstrap-planning: "The coverage gate's repair loop") or choose halt_with_report.`
}
```

and in the branch where an `auto_fix_once` event finds no declared loop for the gate (the code that returns `hard_fail` / `iteration_repair: true` with an unauthorized reason), set that reason to `undeclaredCoverageLoopMessage(<gate node id>)`. Export `undeclaredCoverageLoopMessage`. Regenerate `run-engine.workflow.js` as in Task 5 Step 4.

- [ ] **Step 4: Run everything this task touches**

Run: `python3 -m pytest -q claude/meta-skill/tests/unit/test_validate_bootstrap.py claude/meta-skill/tests/unit/test_validate_unattended_readiness.py && node --test claude/meta-skill/knowledge/run-engine/tests/`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
cat > /tmp/msg65b.txt <<'EOF'
meta-skill: bootstrap declares the coverage gate's repair loop; the auto_fix_once halt names the plan (#65)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_019P9YwUQfRBh2BhcLJGpXmo
EOF
git add claude/meta-skill/scripts/orchestrator/validate_bootstrap.py claude/meta-skill/knowledge/bootstrap-planning.md claude/meta-skill/knowledge/run-engine/engine-core.js claude/meta-skill/knowledge/run-engine/run-engine.workflow.js claude/meta-skill/tests/unit/test_validate_bootstrap.py claude/meta-skill/knowledge/run-engine/tests/engine-core.test.js
git commit -q -F /tmp/msg65b.txt
```

---

### Task 8: Closure — full suites, mirrors, push, tickets

**Files:** none new.

- [ ] **Step 1: Run every suite and both mirror checks**

Run:
```bash
for s in shared/evidence-engine shared/visual-acceptance claude/superstorm/scripts codex/cross-exam-skill/scripts shared/scripts/orchestrator "codex/superstorm-skill/scripts claude/meta-skill/tests/unit"; do printf "%s: " "$s"; eval python3 -m pytest -q $s 2>&1 | tail -1; done
node --test claude/meta-skill/knowledge/run-engine/tests/
python3 shared/evidence-engine/sync.py --check; python3 shared/visual-acceptance/sync.py --check
```
Expected: every line ends `passed`; both mirrors "match".

- [ ] **Step 2: Push and close**

```bash
git fetch -q origin && test "$(git log --oneline HEAD..origin/main | wc -l)" = 0 && git push -q origin main
for n in 63 64 65; do gh issue close $n --comment "Done and pushed to origin/main; see the commits referencing #$n."; done
```

---

## Self-Review

**Spec coverage.**
- #63: build entries (T1), contract entries for all three (T2), engine accepts / cross-exam admits (T3 renderer test), freshness records (T3), capability texts as acceptance (T1/T2), reports keep names (Global). ✔
- #64: schema (T5a), completeness refuses without `served_by` (T4), reason strings match engine (T4 uses the same `不能判 done` family; the new one is its own sentence, named in Interfaces), node-spec template + three capability texts (T5 Step 5), Codex twin (T5 Step 5), run-engine tests extended (T5 Step 1), no change to build/test/contract nodes (`RUNTIME_METHODS` excludes `real-test`). ✔
- #65: planning prose with the three nodes (T7), generated workflows carry the loop or bootstrap refuses (T7 Step 3, conditional on where the spec is authored), readiness refuses gate+policy without loop naming `required_repair_loops` (T6), run-time halt names the declaration (T7), tests extended (T6/T7). ✔

**Placeholder scan.** T3 Step 3 and T7 Step 3 each carry a conditional ("if the file names it differently / if the spec is authored by planning"), because the exact helper name and the authoring site could not be confirmed without reading 1,800-line files in full; both branches are fully specified with code, so an implementer needs no invention. No TBD/TODO.

**Type consistency.** `_gate_draft(run, node, medium, q, output, suffix)` used identically in T1/T2. `RUNTIME_METHODS` is the same four strings in Python (T4) and JS (T5). `coverage_gate_nodes` (readiness, T6) and the inline comprehension in `coverage_gate_loop` (bootstrap, T7) select on the same predicate. `_repair_loop(**overrides)` keys (`scope, qa_node_ids, repair_node_id, closure_node_ids, max_attempts`) match what `coverage_gate_loop` returns. Blocker code `missing_coverage_repair_loop` is the same string in T6 code, T6 tests and T7 prose.
