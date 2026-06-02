# Workflow Run-Engine — Plan 3: Planning Audits (G0 / A0 / Phase A) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the three planning-time audits that run inside `/bootstrap` before any execution: G0 node-granularity audit (right-size nodes), A0 decision-coverage audit (catch every decision), and Phase A brainstorming-lite (gather all decisions up front) — so `/run` can be fully autonomous.

**Architecture:** Each audit is an LLM-judgment procedure authored into `skills/bootstrap.md`, but each emits a **machine-validatable JSON artifact** whose shape is guarded by a Python validator (mirroring the existing `check_structured_node_spec.py` pattern). G0 measures nodes against their Attention Contract and acts (split/merge, ≤2 passes) → `granularity-audit.json`. A0 runs dual-angle agents (concept-completeness ⨁ node-reverse-inference) → `decision-coverage.json`, folding `missing` into the Phase A queue. Phase A iterates the decision queue via a reusable `brainstorming-lite.md` protocol → one `decision-<id>.json` per decision. Ordering is strict: G0 → A0 → Phase A.

**Tech Stack:** Python 3 (`unittest`) for the three output validators; markdown authoring for the bootstrap procedures + the `brainstorming-lite.md` knowledge doc.

**Depends on:** Plan 2 (bootstrap emits `decision_mode`/`decision_inputs`; the invariant check consumes the `decision-<id>.json` artifacts this plan produces).

---

## File Structure

| File | Change | Responsibility |
|------|--------|----------------|
| `shared/scripts/orchestrator/validate_audit_outputs.py` | Create | Validate shapes of `granularity-audit.json`, `decision-coverage.json`, `decision-<id>.json`. |
| `shared/scripts/orchestrator/test_validate_audit_outputs.py` | Create | Tests for the three validators. |
| `claude/meta-skill/knowledge/brainstorming-lite.md` | Create | Reusable distilled decision protocol (one-question-at-a-time → decision artifact). |
| `claude/meta-skill/skills/bootstrap.md` | Modify | Insert G0, A0, Phase A procedures in order (after node generation, before the Plan 2 invariant gate). |
| `claude/meta-skill/scripts/validate_audit_outputs.py` | Create (copy) | Plugin-local copy for `${CLAUDE_PLUGIN_ROOT}` reach. |

---

## Task 1: Output validators for the three audit artifacts

**Files:**
- Create: `shared/scripts/orchestrator/validate_audit_outputs.py`
- Create: `shared/scripts/orchestrator/test_validate_audit_outputs.py`

- [ ] **Step 1: Write the failing test**

Create `shared/scripts/orchestrator/test_validate_audit_outputs.py`:

```python
import unittest
from validate_audit_outputs import (
    validate_granularity_audit, validate_decision_coverage, validate_decision_artifact
)

class TestGranularity(unittest.TestCase):
    def test_valid(self):
        ok, errs = validate_granularity_audit({
            "split": [{"from": "big", "into": ["a", "b"], "rationale": "two outcomes"}],
            "merged": [{"from": ["t1", "t2"], "into": "u", "rationale": "fragment"}],
            "kept": ["c"]
        })
        self.assertTrue(ok, errs)

    def test_missing_top_key(self):
        ok, errs = validate_granularity_audit({"split": [], "merged": []})  # no 'kept'
        self.assertFalse(ok)
        self.assertIn("kept", " ".join(errs))

    def test_split_requires_rationale(self):
        ok, errs = validate_granularity_audit({"split": [{"from": "x", "into": ["a"]}], "merged": [], "kept": []})
        self.assertFalse(ok)
        self.assertIn("rationale", " ".join(errs))

class TestDecisionCoverage(unittest.TestCase):
    def test_valid(self):
        ok, errs = validate_decision_coverage({
            "captured": [{"id": "art-style", "node_id": "ui"}],
            "missing": [{"id": "tone", "rationale": "implied by concept, no node"}]
        })
        self.assertTrue(ok, errs)

    def test_missing_entry_requires_rationale(self):
        ok, errs = validate_decision_coverage({"captured": [], "missing": [{"id": "tone"}]})
        self.assertFalse(ok)
        self.assertIn("rationale", " ".join(errs))

class TestDecisionArtifact(unittest.TestCase):
    def test_valid(self):
        ok, errs = validate_decision_artifact({
            "id": "art-style", "decision": "flat-2d", "rationale": "fits brand", "options_considered": ["flat-2d", "painterly"]
        })
        self.assertTrue(ok, errs)

    def test_requires_decision_field(self):
        ok, errs = validate_decision_artifact({"id": "art-style", "rationale": "x"})
        self.assertFalse(ok)
        self.assertIn("decision", " ".join(errs))

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd shared/scripts/orchestrator && python3 -m unittest test_validate_audit_outputs -v`
Expected: FAIL — `No module named 'validate_audit_outputs'`.

- [ ] **Step 3: Write implementation**

Create `shared/scripts/orchestrator/validate_audit_outputs.py`:

```python
"""Shape validators for the three /bootstrap planning-audit artifacts.
These guard the machine-readable contracts; the audits themselves are LLM judgment."""


def _require_keys(obj, keys):
    return [f"missing top-level key: {k}" for k in keys if k not in obj]


def validate_granularity_audit(obj):
    errs = _require_keys(obj, ["split", "merged", "kept"])
    for s in obj.get("split", []):
        if "from" not in s or "into" not in s:
            errs.append("split entry needs 'from' and 'into'")
        if "rationale" not in s:
            errs.append("split entry needs 'rationale'")
    for m in obj.get("merged", []):
        if "from" not in m or "into" not in m:
            errs.append("merged entry needs 'from' and 'into'")
        if "rationale" not in m:
            errs.append("merged entry needs 'rationale'")
    return (len(errs) == 0, errs)


def validate_decision_coverage(obj):
    errs = _require_keys(obj, ["captured", "missing"])
    for m in obj.get("missing", []):
        if "id" not in m:
            errs.append("missing-entry needs 'id'")
        if "rationale" not in m:
            errs.append("missing-entry needs 'rationale'")
    return (len(errs) == 0, errs)


def validate_decision_artifact(obj):
    errs = _require_keys(obj, ["id", "decision", "rationale"])
    return (len(errs) == 0, errs)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd shared/scripts/orchestrator && python3 -m unittest test_validate_audit_outputs -v`
Expected: PASS (7 tests).

- [ ] **Step 5: Commit**

```bash
git add shared/scripts/orchestrator/validate_audit_outputs.py shared/scripts/orchestrator/test_validate_audit_outputs.py
git commit -m "feat(orchestrator): validators for G0/A0/Phase A audit outputs"
```

---

## Task 2: `brainstorming-lite.md` protocol knowledge doc

**Files:**
- Create: `claude/meta-skill/knowledge/brainstorming-lite.md`

- [ ] **Step 1: Write the protocol doc**

Create `claude/meta-skill/knowledge/brainstorming-lite.md`:

```markdown
# brainstorming-lite

A distilled decision protocol for Phase A of `/bootstrap`. Use it to resolve ONE
decision into ONE artifact. It borrows the brainstorming method (intent first,
options with tradeoffs, incremental confirmation) but omits the heavy ceremony:
**no spec doc, no reviewer loop, no writing-plans handoff.**

## When to use
For each item in the Phase A decision queue (nodes with `decision_mode: "brainstorm"`
plus A0 `missing` entries). High-frequency, lightweight, converges fast.

## Protocol (per decision)
1. State the decision and why it matters (one sentence).
2. Surface intent with ONE question at a time (prefer multiple-choice). Never batch.
3. Offer 2–3 options with concrete tradeoffs; lead with a recommendation + reason.
4. Confirm incrementally; iterate only if the answer reveals a new fork.
5. Write the decision artifact and stop — do NOT generate the downstream work.

## Output contract
Write `.allforai/<domain>/decision-<id>.json`:
```json
{
  "id": "<decision id>",
  "decision": "<the chosen direction>",
  "rationale": "<why, in the user's framing>",
  "options_considered": ["<a>", "<b>"]
}
```
Validate with `validate_decision_artifact` before moving to the next decision.

## Hard rules
- One question per message.
- Generation-before: this runs BEFORE the node that consumes the decision.
- Stay in `/bootstrap`; `/run` must never reach a brainstorming step.
```

- [ ] **Step 2: Structural check**

Run: `grep -n 'decision-<id>.json\|One question\|options_considered\|no spec doc' claude/meta-skill/knowledge/brainstorming-lite.md`
Expected: all four anchors present.

- [ ] **Step 3: Commit**

```bash
git add claude/meta-skill/knowledge/brainstorming-lite.md
git commit -m "feat(meta-skill): brainstorming-lite decision protocol for Phase A"
```

---

## Task 3: G0 — Node-Granularity Audit procedure in bootstrap

**Files:**
- Modify: `claude/meta-skill/skills/bootstrap.md`

- [ ] **Step 1: Find the insertion point**

Run: `grep -n 'node-specs\|Attention Contract\|Primary outcome\|Context budget\|workflow.json' claude/meta-skill/skills/bootstrap.md | head`
Identify the point immediately AFTER initial node + node-spec generation and BEFORE the Plan 2 invariant gate. G0 goes first among the audits.

- [ ] **Step 2: Insert the G0 procedure (verbatim)**

```markdown
## G0 — Node-Granularity Audit (right-size for single-task attention)

Runs immediately after node generation, BEFORE A0. Granularity quality is U-shaped:
too coarse → attention dilution / context overflow; too fine → coordination cost +
coherence collapse. Target: each node = one coherent, independently-deliverable,
independently-testable responsibility that fits its attention budget. NOT minimal.

**Acts non-interactively** (split/merge), then batches confirmations into Phase A.

For up to 2 passes:
1. For each node, measure against its Attention Contract (Primary outcome / Context
   budget / Non-goals):
   - **Too coarse → split** when: multiple primary outcomes, exceeds context budget,
     or bundles independent concerns. Split into right-sized nodes; regenerate their
     specs, exit_artifacts, and `hard_blocked_by`/`alignment_refs` using the same
     node-generation machinery.
   - **Too fine → merge** when: no standalone deliverable, exists only to feed one
     sibling, or its exit artifact is a fragment. Merge into the coherent parent.
   - Otherwise → keep.
2. Write `.allforai/bootstrap/granularity-audit.json`:
   `{ "split": [{from,into[],rationale}], "merged": [{from[],into,rationale}], "kept": [ids] }`
   then re-run the pass on the restructured graph.
3. Stop after 2 passes (convergence cap); log any residual outliers.

Validate the output:
`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate_audit_outputs.py granularity .allforai/bootstrap/granularity-audit.json`

Queue non-trivial restructures for Phase A confirmation (do not ask now).
```

- [ ] **Step 3: Verify insertion + ordering**

Run: `grep -n 'G0 — Node-Granularity\|A0 —\|Phase A' claude/meta-skill/skills/bootstrap.md`
Expected: G0 appears, and (after Tasks 4–5) precedes A0 which precedes Phase A.

- [ ] **Step 4: Commit**

```bash
git add claude/meta-skill/skills/bootstrap.md
git commit -m "feat(bootstrap): G0 node-granularity audit (bidirectional, U-curve, <=2 passes)"
```

---

## Task 4: A0 — Decision-Coverage Audit procedure in bootstrap

**Files:**
- Modify: `claude/meta-skill/skills/bootstrap.md`

- [ ] **Step 1: Insert the A0 procedure (verbatim), immediately after G0**

```markdown
## A0 — Decision-Coverage Audit (catch every decision before the run)

Runs after G0 (over the right-sized graph), before Phase A. Dual-angle; union results.

- **Agent 1 (concept completeness):** enumerate every direction/intent fork implied by
  the source concept artifacts (art style, monetization model, tech selection, tone,
  scope tradeoffs, …).
- **Agent 2 (node reverse-inference):** scan nodes/node-specs for implicit choices NOT
  marked `decision_mode: "brainstorm"`.

Union the two; write `.allforai/bootstrap/decision-coverage.json`:
`{ "captured": [{id, node_id}], "missing": [{id, rationale}] }`.

Validate:
`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate_audit_outputs.py decision-coverage .allforai/bootstrap/decision-coverage.json`

Fold every `missing` entry into the Phase A decision queue (and set `decision_mode:
"brainstorm"` + the future `decision_inputs` path on the node that will consume it).
```

- [ ] **Step 2: Verify**

Run: `grep -n 'A0 — Decision-Coverage\|decision-coverage.json\|reverse-inference' claude/meta-skill/skills/bootstrap.md`
Expected: all present.

- [ ] **Step 3: Commit**

```bash
git add claude/meta-skill/skills/bootstrap.md
git commit -m "feat(bootstrap): A0 dual-angle decision-coverage audit"
```

---

## Task 5: Phase A — brainstorming-lite gathering in bootstrap

**Files:**
- Modify: `claude/meta-skill/skills/bootstrap.md`

- [ ] **Step 1: Insert the Phase A procedure (verbatim), after A0 and before the Plan 2 invariant gate**

```markdown
## Phase A — Decision Gathering (the ONLY place humans are asked)

Runs after A0, as the final interactive step of `/bootstrap`. Iterate the decision
queue = (nodes with `decision_mode: "brainstorm"`) ∪ (A0 `missing`) ∪ (G0 restructure
confirmations).

For EACH decision, follow `${CLAUDE_PLUGIN_ROOT}/knowledge/brainstorming-lite.md`:
one question at a time, intent → 2–3 options with tradeoffs → incremental confirm →
write `.allforai/<domain>/decision-<id>.json` and validate it:
`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate_audit_outputs.py decision .allforai/<domain>/decision-<id>.json`

Generation-before: each decision is gathered BEFORE the node that consumes it (the node
references it via `decision_inputs`). When the queue is empty, every decision artifact is
on disk — proceed to the final invariant gate. `/run` will be fully autonomous.
```

- [ ] **Step 2: Confirm the four-step order now reads G0 → A0 → Phase A → invariant gate**

Run: `grep -n 'G0 — Node-Granularity\|A0 — Decision-Coverage\|Phase A — Decision Gathering\|Final gate: decision_inputs' claude/meta-skill/skills/bootstrap.md`
Expected: the four headings appear in that order (line numbers ascending).

- [ ] **Step 3: Confirm no human-interaction language leaked into `/run`/orchestrator**

Run: `grep -niE 'brainstorm|AskUserQuestion|one question' claude/meta-skill/knowledge/orchestrator-template.md`
Expected: zero matches (all interaction is in bootstrap).

- [ ] **Step 4: Commit**

```bash
git add claude/meta-skill/skills/bootstrap.md
git commit -m "feat(bootstrap): Phase A brainstorming-lite decision gathering"
```

---

## Task 6: Plugin-local validator copy + end-to-end bootstrap dry check

**Files:**
- Create: `claude/meta-skill/scripts/validate_audit_outputs.py` (copy)

- [ ] **Step 1: Add a CLI dispatcher to the validator (so the bootstrap commands above work)**

Append to `shared/scripts/orchestrator/validate_audit_outputs.py`:

```python
if __name__ == "__main__":
    import json, sys
    kind, path = sys.argv[1], sys.argv[2]
    obj = json.load(open(path))
    fn = {
        "granularity": validate_granularity_audit,
        "decision-coverage": validate_decision_coverage,
        "decision": validate_decision_artifact,
    }[kind]
    ok, errs = fn(obj)
    print("OK" if ok else "INVALID: " + "; ".join(errs))
    sys.exit(0 if ok else 1)
```

- [ ] **Step 2: Add a test for the CLI dispatcher** (append to `test_validate_audit_outputs.py`)

```python
import subprocess, sys, os, json, tempfile

class TestCli(unittest.TestCase):
    def test_cli_valid_granularity(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump({"split": [], "merged": [], "kept": ["a"]}, f)
            p = f.name
        r = subprocess.run([sys.executable, "validate_audit_outputs.py", "granularity", p],
                           cwd=os.path.dirname(os.path.abspath(__file__)), capture_output=True, text=True)
        os.unlink(p)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("OK", r.stdout)
```

- [ ] **Step 3: Run tests**

Run: `cd shared/scripts/orchestrator && python3 -m unittest test_validate_audit_outputs -v`
Expected: PASS (8 tests).

- [ ] **Step 4: Copy to plugin-local scripts dir**

Run: `cp shared/scripts/orchestrator/validate_audit_outputs.py claude/meta-skill/scripts/validate_audit_outputs.py && python3 claude/meta-skill/scripts/validate_audit_outputs.py decision-coverage <(printf '{"captured":[],"missing":[]}'); echo "exit=$?"`
Expected: `OK` + `exit=0`.

- [ ] **Step 5: Commit**

```bash
git add shared/scripts/orchestrator/validate_audit_outputs.py shared/scripts/orchestrator/test_validate_audit_outputs.py claude/meta-skill/scripts/validate_audit_outputs.py
git commit -m "feat(orchestrator): audit-output CLI dispatcher + plugin-local copy"
```

---

## Task 7: Version bump + full regression

**Files:**
- Modify: `claude/meta-skill/.claude-plugin/plugin.json`, `marketplace.json`, bootstrap version marker

- [ ] **Step 1: Read current versions**

Run: `grep -n '"version"' claude/meta-skill/.claude-plugin/plugin.json claude/meta-skill/.claude-plugin/marketplace.json; grep -niE 'Protocol v[0-9]' claude/meta-skill/skills/bootstrap.md | head -1`

- [ ] **Step 2: Bump all three (minor — Plan 3 completes the feature)**

Increment the minor digit consistently (e.g. `0.9.1` → `0.10.0`). Same string in all three.

- [ ] **Step 3: Verify match**

Run: `grep -rn '0.10.0' claude/meta-skill/.claude-plugin/ claude/meta-skill/skills/bootstrap.md` (substitute your version)
Expected: three identical matches.

- [ ] **Step 4: Full regression across all three plans**

Run:
```bash
node --test claude/meta-skill/knowledge/run-engine/tests/
cd shared/scripts/orchestrator && python3 -m unittest discover -p 'test_*.py' && cd -
```
Expected: all green — JS engine suites (Plans 1–2) + Python orchestrator suites (Plans 2–3).

- [ ] **Step 5: Commit**

```bash
git add claude/meta-skill/.claude-plugin/plugin.json claude/meta-skill/.claude-plugin/marketplace.json claude/meta-skill/skills/bootstrap.md
git commit -m "chore(meta-skill): bump version for run-engine Plan 3 (feature complete)"
```

---

## Self-Review

**1. Spec coverage (Plan 3 portion):**

| Spec § | Covered by |
|--------|------------|
| §4.6 G0 granularity audit (U-curve, bidirectional, ≤2 passes, granularity-audit.json) | Tasks 1, 3 |
| §4.7 A0 dual-angle decision-coverage (decision-coverage.json, missing→Phase A) | Tasks 1, 4 |
| §4.8 Phase A brainstorming-lite (decision-<id>.json, generation-before, no ceremony) | Tasks 1, 2, 5 |
| §3.1 ordering G0 → A0 → Phase A → invariant gate | Task 5 Step 2 |
| §6 audit artifact contracts | Task 1 |
| §1.2 all interaction in bootstrap; none in /run | Task 5 Step 3 |
| §7 DoD version bump + full regression | Task 7 |

**Cross-plan closure:** Plan 2 Task 2's invariant (`check_decision_inputs`) consumes exactly the `decision-<id>.json` artifacts Plan 3 Task 5 produces — the loop is closed. Plan 2 Task 4 sets `decision_mode`/`decision_inputs`; Plan 3 A0/Phase A populate the decisions those fields point to.

**2. Placeholder scan:** All bootstrap insertions (Tasks 3–5) provide verbatim content + a concrete validation command. No "add appropriate X". Task 6's CLI dispatcher is fully shown.

**3. Type consistency:** Validator names (`validate_granularity_audit`, `validate_decision_coverage`, `validate_decision_artifact`) match across Task 1 test/impl, the CLI dispatcher (Task 6), and the bootstrap invocations (Tasks 3–5). Artifact key sets match the validators exactly: granularity `{split, merged, kept}` with per-entry `rationale`; coverage `{captured, missing}` with `missing[].rationale`; decision `{id, decision, rationale, options_considered?}`. The `decision-<id>.json` shape matches `brainstorming-lite.md`'s output contract (Task 2) and Plan 2's `decision_inputs` references.
```
