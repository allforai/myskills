# Codex Bug Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 6 bugs identified by Codex in the meta-skill plugin — 2 blocking Python script bugs and 4 documentation/schema gaps — in execution order: scripts first, then bootstrap injection, then orchestrator, then concept-contract, then parallelism.

**Architecture:** Tasks 1–2 touch real Python code with testable behaviour (pytest). Tasks 3–6 are markdown/documentation edits verified by grep assertions. All changes are in `/Users/aa/workspace/myskills/claude/meta-skill/`. Git root is `/Users/aa/workspace/myskills`.

**Tech Stack:** Python 3, pytest, markdown, meta-skill plugin schema

---

## File Structure

| Action | Path | Fix |
|--------|------|-----|
| Modify | `scripts/orchestrator/check_artifacts.py:44` | `all_exist` must also check no `validation_error` |
| Modify | `scripts/orchestrator/validate_bootstrap.py:60–66` | Extract `.path` before `os.path.basename` for dict artifacts |
| Create | `tests/unit/test_check_artifacts.py` | pytest for both Python script fixes |
| Create | `tests/unit/test_validate_bootstrap.py` | pytest for validate_bootstrap fix |
| Modify | `skills/bootstrap.md` (App Design Injection block) | Add non-game app-design node injection rule |
| Modify | `skills/bootstrap.md` (game-design injection lines 906–907) | `blocked_by` → `hard_blocked_by`; identify parallel nodes |
| Modify | `knowledge/orchestrator-template.md:44` | Generalize human gate to use node's `approval_record_path` |
| Modify | `knowledge/capabilities/concept-contract.md` | Conditionally include `app-design-doc.json` |

---

## Task 1: Fix check_artifacts.py — validation_error not counted as incomplete

**Bug:** Line 44 computes `all_exist = all(r["exists"] for r in results)`. A node whose file exists but whose `validation_commands` returned non-zero gets `all_exist: true`, so `/run` marks it done.

**Fix:** `all_exist` must be false if any result has a `validation_error`.

**Files:**
- Modify: `scripts/orchestrator/check_artifacts.py:44`
- Create: `tests/unit/test_check_artifacts.py`

- [ ] **Step 1: Create the test file**

Create `/Users/aa/workspace/myskills/claude/meta-skill/tests/unit/test_check_artifacts.py`:

```python
import json
import os
import sys
import tempfile
import textwrap

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../scripts/orchestrator"))
from check_artifacts import check_node_artifacts


def _make_node(artifacts):
    return {"id": "test-node", "goal": "test", "exit_artifacts": artifacts}


def test_string_artifact_exists(tmp_path):
    f = tmp_path / "out.json"
    f.write_text("{}")
    result = check_node_artifacts(_make_node([str(f)]))
    assert result["all_exist"] is True
    assert len(result["artifacts"]) == 1


def test_string_artifact_missing(tmp_path):
    result = check_node_artifacts(_make_node([str(tmp_path / "missing.json")]))
    assert result["all_exist"] is False


def test_dict_artifact_exists_no_commands(tmp_path):
    f = tmp_path / "out.json"
    f.write_text("{}")
    result = check_node_artifacts(_make_node([{"path": str(f), "validation_commands": []}]))
    assert result["all_exist"] is True


def test_dict_artifact_validation_command_passes(tmp_path):
    f = tmp_path / "out.json"
    f.write_text('{"status": "final"}')
    result = check_node_artifacts(_make_node([{
        "path": str(f),
        "validation_commands": [f'python3 -c "import json; json.load(open(\\"{f}\\"))"']
    }]))
    assert result["all_exist"] is True
    assert "validation_error" not in result["artifacts"][0]


def test_dict_artifact_validation_command_fails(tmp_path):
    """File exists but validation command exits non-zero → all_exist must be False."""
    f = tmp_path / "bad.json"
    f.write_text("not json")
    result = check_node_artifacts(_make_node([{
        "path": str(f),
        "validation_commands": [f'python3 -c "import json,sys; json.load(open(sys.argv[1]))" {f}']
    }]))
    # THE BUG: currently all_exist is True despite validation_error
    assert result["all_exist"] is False  # must be False after fix
    assert "validation_error" in result["artifacts"][0]


def test_false_command_fails(tmp_path):
    """Using `false` as command (always exits 1) → all_exist must be False."""
    f = tmp_path / "file.txt"
    f.write_text("content")
    result = check_node_artifacts(_make_node([{
        "path": str(f),
        "validation_commands": ["false"]
    }]))
    assert result["all_exist"] is False
    assert "validation_error" in result["artifacts"][0]
```

- [ ] **Step 2: Run tests to verify they fail (before fix)**

```bash
cd /Users/aa/workspace/myskills
python3 -m pytest claude/meta-skill/tests/unit/test_check_artifacts.py -v 2>&1 | tail -20
```

Expected: `test_dict_artifact_validation_command_fails` and `test_false_command_fails` FAIL with `AssertionError: assert True is False`.

- [ ] **Step 3: Apply the fix**

In `/Users/aa/workspace/myskills/claude/meta-skill/scripts/orchestrator/check_artifacts.py`, find line 44:

```python
        "all_exist": all(r["exists"] for r in results),
```

Replace with:

```python
        "all_exist": all(r["exists"] and "validation_error" not in r for r in results),
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /Users/aa/workspace/myskills
python3 -m pytest claude/meta-skill/tests/unit/test_check_artifacts.py -v 2>&1 | tail -20
```

Expected: all 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
cd /Users/aa/workspace/myskills
git add claude/meta-skill/scripts/orchestrator/check_artifacts.py claude/meta-skill/tests/unit/test_check_artifacts.py
git commit -m "$(cat <<'EOF'
fix: all_exist now false when validation_command fails

Previously a node with validation_error was still marked complete.
Now all_exist is false if any artifact has a validation_error.
Adds pytest coverage for both string and object artifact forms.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Fix validate_bootstrap.py — TypeError on dict exit_artifacts

**Bug:** Lines 60–66 do `for artifact_path in node["exit_artifacts"]:` then call `os.path.basename(artifact_path)`. If an artifact entry is a dict `{"path": "...", "validation_commands": [...]}`, `os.path.basename(dict)` raises `TypeError`.

**Fix:** Extract the path string from both forms before calling `os.path.basename`.

**Files:**
- Modify: `scripts/orchestrator/validate_bootstrap.py:60–66`
- Create: `tests/unit/test_validate_bootstrap.py`

- [ ] **Step 1: Create the test file**

Create `/Users/aa/workspace/myskills/claude/meta-skill/tests/unit/test_validate_bootstrap.py`:

```python
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../scripts/orchestrator"))
from validate_bootstrap import validate_workflow


def _write_workflow(tmp_path, nodes):
    wf = {"nodes": nodes, "transition_log": []}
    p = tmp_path / "workflow.json"
    p.write_text(json.dumps(wf))
    return str(p)


def _base_node(**overrides):
    node = {
        "id": "test-node",
        "goal": "do stuff",
        "capability": "discovery",
        "exit_artifacts": [".allforai/out.json"],
        "consumers": [],
        "hard_blocked_by": [],
        "alignment_refs": [],
        "human_gate": False,
        "discipline_owner": None,
    }
    node.update(overrides)
    return node


def test_string_artifact_passes(tmp_path):
    path = _write_workflow(tmp_path, [_base_node(exit_artifacts=[".allforai/out.json"])])
    errors = validate_workflow(path)
    assert errors == []


def test_dict_artifact_valid_path_passes(tmp_path):
    """Object-form artifact must not TypeError."""
    artifact = {"path": ".allforai/out.json", "validation_commands": []}
    path = _write_workflow(tmp_path, [_base_node(exit_artifacts=[artifact])])
    errors = validate_workflow(path)
    assert errors == []


def test_dict_artifact_suspicious_bare_path_fails(tmp_path):
    """Object-form artifact with suspicious bare path should still error."""
    artifact = {"path": "config.json", "validation_commands": []}
    path = _write_workflow(tmp_path, [_base_node(exit_artifacts=[artifact])])
    errors = validate_workflow(path)
    assert any("bare filename" in e for e in errors)


def test_mixed_artifacts_passes(tmp_path):
    """Mix of string and dict artifacts."""
    artifacts = [
        ".allforai/good.json",
        {"path": ".allforai/also-good.json", "validation_commands": ["true"]},
    ]
    path = _write_workflow(tmp_path, [_base_node(exit_artifacts=artifacts)])
    errors = validate_workflow(path)
    assert errors == []
```

- [ ] **Step 2: Run tests to verify they fail (before fix)**

```bash
cd /Users/aa/workspace/myskills
python3 -m pytest claude/meta-skill/tests/unit/test_validate_bootstrap.py -v 2>&1 | tail -20
```

Expected: `test_dict_artifact_valid_path_passes`, `test_dict_artifact_suspicious_bare_path_fails`, `test_mixed_artifacts_passes` FAIL with `TypeError: expected str, bytes or os.PathLike object, not dict`.

- [ ] **Step 3: Apply the fix**

In `/Users/aa/workspace/myskills/claude/meta-skill/scripts/orchestrator/validate_bootstrap.py`, find lines 59–66:

```python
        else:
            for artifact_path in node["exit_artifacts"]:
                basename = os.path.basename(artifact_path)
                if artifact_path == basename and basename in SUSPICIOUS_BARE:
                    errors.append(
                        f"workflow.json: {nid} exit_artifact '{artifact_path}' "
                        f"looks like a bare filename — use full project-relative "
                        f"path (e.g., 'subdir/{artifact_path}' not '{artifact_path}')"
                    )
```

Replace with:

```python
        else:
            for raw in node["exit_artifacts"]:
                if isinstance(raw, dict):
                    artifact_path = raw.get("path", "")
                else:
                    artifact_path = raw
                basename = os.path.basename(artifact_path)
                if artifact_path == basename and basename in SUSPICIOUS_BARE:
                    errors.append(
                        f"workflow.json: {nid} exit_artifact '{artifact_path}' "
                        f"looks like a bare filename — use full project-relative "
                        f"path (e.g., 'subdir/{artifact_path}' not '{artifact_path}')"
                    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /Users/aa/workspace/myskills
python3 -m pytest claude/meta-skill/tests/unit/test_validate_bootstrap.py -v 2>&1 | tail -20
```

Expected: all 4 tests PASS.

- [ ] **Step 5: Run all unit tests together**

```bash
cd /Users/aa/workspace/myskills
python3 -m pytest claude/meta-skill/tests/unit/ -v 2>&1 | tail -10
```

Expected: all tests PASS (Tasks 1 + 2 combined).

- [ ] **Step 6: Commit**

```bash
cd /Users/aa/workspace/myskills
git add claude/meta-skill/scripts/orchestrator/validate_bootstrap.py claude/meta-skill/tests/unit/test_validate_bootstrap.py
git commit -m "$(cat <<'EOF'
fix: validate_bootstrap handles dict-form exit_artifacts

os.path.basename(dict) raised TypeError. Now extracts .path from
both string and object artifact forms before validation.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Add app-design bootstrap injection rule

**Bug:** `app-design.md` says "Bootstrap uses this registry" but `bootstrap.md` has no injection rule for non-game projects. The capability is dead code.

**Fix:** Add a parallel injection block to `bootstrap.md` — mirror of the game project injection at line 891, but triggered by `is_game_project = false` AND a design-phase goal.

**Files:**
- Modify: `skills/bootstrap.md` (after the game project injection block, around line 943)

- [ ] **Step 1: Read the current injection block location**

```bash
grep -n "Game project node injection\|Art Concept Node\|Concept Freeze Node\|app.design injection\|App design" /Users/aa/workspace/myskills/claude/meta-skill/skills/bootstrap.md | head -10
```

Identify the line number of the **end** of the game project injection block (the line just before `5. Initialise .allforai/game-design/approval-records.json`).

- [ ] **Step 2: Insert the app-design injection block**

In `skills/bootstrap.md`, find the line (after the concept-freeze injection block):

```
5. Initialise `.allforai/game-design/approval-records.json` with one `pending` record per game-design node
```

BEFORE that line, insert this new block:

```markdown
**App Design Node Injection (when `is_game_project = false` AND goal includes design phase):**

When `is_game_project = false` AND the selected goal implies product design phases (e.g., user chose "从零构建新产品" or the goal includes UI/UX design work), inject app-design nodes using `knowledge/capabilities/app-design.md` Canonical Node Registry:

- Required nodes always injected: `ia-design`, `user-flow-design`, `interaction-design`, `app-design-finalize`
- Optional nodes injected when relevant: `content-design` (content-heavy apps), `data-model-design` (data-intensive apps — inject when `has_database_model` is detected or user confirms)
- Each node gets: `capability: "app-design"`, `human_gate: true`, `approval_record_path: ".allforai/app-design/approval-records.json"`, `gate_status: "pending"`, `discipline_owner` from app-design.md Canonical Node Registry
- Ordering: `ia-design` first (no hard_blocked_by); `user-flow-design` and `content-design` and `data-model-design` each `hard_blocked_by: ["ia-design"]`; `interaction-design` `hard_blocked_by: ["user-flow-design"]`; `app-design-finalize` `hard_blocked_by:` ALL other selected app-design nodes
- `app-design-finalize` `unlocks:` subsequent execution nodes (same role as `game-design-finalize`)
- **No approval-records entry** for nodes with `human_gate: false` — only human_gate nodes get records
- After injecting, initialise `.allforai/app-design/approval-records.json` with one `pending` record per selected app-design node (same structure as game-design approval-records.json)

**Concept Freeze for app projects:** When `app-design-finalize` is in the workflow, also inject a `concept-freeze` node immediately after it:
- `node_id: "concept-freeze"`, `capability: "concept-contract"`, `human_gate: false`
- `hard_blocked_by: ["app-design-finalize"]`
- `exit_artifacts: [".allforai/concept-contract.json"]`
- **No approval-records entry**
```

- [ ] **Step 3: Verify the insertion**

```bash
grep -n "App Design Node Injection\|app-design injection\|app-design-finalize\|ia-design" /Users/aa/workspace/myskills/claude/meta-skill/skills/bootstrap.md | head -15
```

Expected: "App Design Node Injection" appears; `ia-design`, `user-flow-design`, `app-design-finalize` appear in the injection rule.

- [ ] **Step 4: Commit**

```bash
cd /Users/aa/workspace/myskills
git add claude/meta-skill/skills/bootstrap.md
git commit -m "$(cat <<'EOF'
feat: add app-design node injection for non-game projects

bootstrap.md was missing injection logic for app-design nodes despite
app-design.md declaring 'Bootstrap uses this registry'. Now non-game
projects with a design phase get ia-design/user-flow/interaction nodes
injected, and concept-freeze is wired after app-design-finalize.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Generalize orchestrator human gate to handle any approval_record_path

**Bug:** `orchestrator-template.md` Core Loop step 4 hardcodes `.allforai/game-design/approval-records.json`. When app-design nodes are injected (with `approval_record_path: ".allforai/app-design/approval-records.json"`), their gates are silently ignored.

**Fix:** Replace the hardcoded path with a rule that reads `approval_record_path` from the node's own workflow.json definition.

**Files:**
- Modify: `knowledge/orchestrator-template.md` (Core Loop step 4, around line 44)

- [ ] **Step 1: Read the current gate rule**

```bash
sed -n '42,52p' /Users/aa/workspace/myskills/claude/meta-skill/knowledge/orchestrator-template.md
```

- [ ] **Step 2: Replace the hardcoded gate rule**

In `knowledge/orchestrator-template.md`, find the entire `**Game-design nodes with `human_gate: true`:**` block (lines ~44–48):

```
     - **Game-design nodes with `human_gate: true`:** do NOT advance to the next node based on exit_artifact existence alone. Also check `.allforai/game-design/approval-records.json`:
       - `gate_status == "pending"` AND all exit_artifacts exist → auto-set `gate_status` to `"in-review"` and notify the `discipline_owner` that the output is ready for review. Do NOT advance yet.
       - `gate_status == "in-review"` → wait for `discipline_owner` to approve or request revision. Do NOT advance.
       - `gate_status == "approved"` → this node is done; advance to unlocked nodes.
       - `gate_status == "revision-requested"` → re-run the node passing `revision_notes` as instruction; after re-execution completes, reset `gate_status` to `"in-review"`.
```

Replace with:

```
     - **Nodes with `human_gate: true`:** do NOT advance based on exit_artifact existence alone. Read the node's `approval_record_path` field from workflow.json (e.g., `.allforai/game-design/approval-records.json` for game-design nodes, `.allforai/app-design/approval-records.json` for app-design nodes). Look up this node's record by `node_id`:
       - `gate_status == "pending"` AND all exit_artifacts exist → auto-set `gate_status` to `"in-review"` and notify `discipline_owner`. Do NOT advance yet.
       - `gate_status == "in-review"` → wait for `discipline_owner` to approve or request revision. Do NOT advance.
       - `gate_status == "approved"` → this node is done; advance to unlocked nodes.
       - `gate_status == "revision-requested"` → re-run the node passing `revision_notes` as instruction; after re-execution completes, reset `gate_status` to `"in-review"`.
       - If `approval_record_path` is missing on the node → treat as `gate_status == "pending"` and warn.
```

- [ ] **Step 3: Verify**

```bash
grep -n "approval_record_path\|game-design/approval\|app-design/approval\|human_gate" /Users/aa/workspace/myskills/claude/meta-skill/knowledge/orchestrator-template.md | head -10
```

Expected: `approval_record_path` appears; the hardcoded `game-design/approval-records.json` path no longer appears as the sole gate path.

- [ ] **Step 4: Commit**

```bash
cd /Users/aa/workspace/myskills
git add claude/meta-skill/knowledge/orchestrator-template.md
git commit -m "$(cat <<'EOF'
fix: orchestrator reads approval_record_path from node, not hardcoded

Previously only .allforai/game-design/approval-records.json was checked,
so app-design human gates were silently ignored. Now uses the node's own
approval_record_path field to support any capability's gate records.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Generalize concept-contract.md — support app-design projects

**Bug:** `concept-contract.md` Inputs table only lists game/art files. But `app-design.md` line 166 says concept-freeze includes `app-design-doc.json`. The two files are inconsistent.

**Fix:** Make game/art inputs conditional; add app-design input as an alternative branch.

**Files:**
- Modify: `knowledge/capabilities/concept-contract.md`

- [ ] **Step 1: Read the current Inputs table**

```bash
sed -n '18,35p' /Users/aa/workspace/myskills/claude/meta-skill/knowledge/capabilities/concept-contract.md
```

- [ ] **Step 2: Replace the Inputs section with a conditional structure**

In `concept-contract.md`, find the Inputs section (the table starting with `| File | Required fields |`). Replace the entire Inputs section (table + the two "If missing" lines below it) with:

```markdown
## Inputs

The concept-freeze node serves both game/art projects and non-game app projects. Inputs are conditional on project type — read `bootstrap-profile.json.is_game_project` to determine which branch applies.

### Branch A: Game / Art project (`is_game_project = true`)

| File | Required fields |
|------|----------------|
| `.allforai/product-concept/product-concept.json` | `genre`, `target_platform`, `core_loop` |
| `.allforai/game-design/art-style-guide.json` | `art_overview` (incl. `animation_system`) |
| `.allforai/game-design/art-pipeline-config.json` | `dimension`, `style`, `active_nodes` |
| `.allforai/game-design/art-asset-inventory.json` | `assets[].asset_id`, `assets[].type`, `assets[].name` |
| `.allforai/game-design/approval-records.json` | all records with `gate_status` |

If `art-asset-inventory.json` is missing → report UPSTREAM_DEFECT and halt.
If any game-design human_gate node has `gate_status != "approved"` → halt listing unapproved gates.

### Branch B: Non-game app project (`is_game_project = false`)

| File | Required fields |
|------|----------------|
| `.allforai/product-concept/product-concept.json` | `name`, `target_users`, `core_features` |
| `.allforai/app-design/app-design-doc.json` | `ia-design`, `user-flow-design`, `interaction-design` top-level keys |
| `.allforai/app-design/approval-records.json` | all records with `gate_status` |

If `app-design-doc.json` is missing → report UPSTREAM_DEFECT and halt.
If any app-design human_gate node has `gate_status != "approved"` → halt listing unapproved gates.

For Branch B, `canonical_registry` is derived from `app-design-doc.json` screen and component IDs rather than art asset IDs:
- `screens[]` from `ia-design` → registry group `screens`, `file_prefix: "scr_{screen_id}"`
- `components[]` from `interaction-design` → registry group `components`, `file_prefix: "cmp_{component_id}"`
- `flows[]` from `user-flow-design` → registry group `flows`, `file_prefix: "flw_{flow_id}"`
```

- [ ] **Step 3: Verify**

```bash
grep -n "Branch A\|Branch B\|is_game_project\|app-design-doc" /Users/aa/workspace/myskills/claude/meta-skill/knowledge/capabilities/concept-contract.md | head -10
```

Expected: both branches present; `is_game_project` mentioned; `app-design-doc.json` mentioned.

- [ ] **Step 4: Commit**

```bash
cd /Users/aa/workspace/myskills
git add claude/meta-skill/knowledge/capabilities/concept-contract.md
git commit -m "$(cat <<'EOF'
fix: generalize concept-contract to support app-design projects

Previously only game/art files were listed as inputs. Now has
Branch A (game: art-asset-inventory → canonical_registry) and
Branch B (app: ia-design screens/components → canonical_registry).
Consistent with app-design.md's claim that concept-freeze includes
app-design-doc.json.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: Fix game-design injection — hard_blocked_by + identify parallel nodes

**Bug:** `bootstrap.md` lines 906–907 set `blocked_by` (legacy name) in a strict serial chain for all game-design nodes. This makes every node wait for the previous one, even when the dependency is only a read (not a data write). Nodes like `economy-design`, `progression-design`, and `narrative-design` can run in parallel once `core-loop-design` is approved — they only read from it, not from each other.

**Fix:** 
1. Change `blocked_by` → `hard_blocked_by` in the injection rule text.
2. Add an explicit parallelism rule identifying which sibling game-design nodes can use `alignment_refs` instead of `hard_blocked_by`.

**Files:**
- Modify: `skills/bootstrap.md` (lines 906–907, game-design node injection)

- [ ] **Step 1: Read the current injection rules**

```bash
sed -n '900,915p' /Users/aa/workspace/myskills/claude/meta-skill/skills/bootstrap.md
```

- [ ] **Step 2: Update the canonical node injection rule (line 906)**

In `bootstrap.md`, find this exact text (the canonical node injection rule):

```
     - **Canonical node** (in registry AND node_order): look up `discipline_owner`, `html_output`, `json_output`, `presentation` from the registry. Set `blocked_by` = **previous SELECTED node in `node_order`** (skip unselected optional nodes — a node that is not included in the workflow cannot appear in any `blocked_by` list); `unlocks` = **next SELECTED node in `node_order`** (same skipping rule). Exception: `game-design-finalize` is `blocked_by` ALL other game-design nodes in the scenario that are actually selected (it aggregates every system JSON from selected nodes only).
```

Replace with:

```
     - **Canonical node** (in registry AND node_order): look up `discipline_owner`, `html_output`, `json_output`, `presentation` from the registry. Set `hard_blocked_by` = **previous SELECTED node in `node_order`** (skip unselected optional nodes); `unlocks` = **next SELECTED node in `node_order`** (same skipping rule). Exception: `game-design-finalize` has `hard_blocked_by` = ALL other game-design nodes that are actually selected.
     
     **Parallelism rule:** After assigning the default serial `hard_blocked_by`, apply this override for sibling nodes that only READ a shared predecessor's output (not data-produce it): if two or more nodes both `hard_blocked_by` the same single predecessor and neither is in the other's consumers[], reclassify the later node's dependency on its sibling as `alignment_refs` instead of `hard_blocked_by`. Common parallel groups by scenario:
       - `casual-mobile`: once `core-loop-design` is approved → `economy-design`, `progression-design`, `retention-design` may all run concurrently (each `hard_blocked_by: ["core-loop-design"]`, `alignment_refs: []` to each other)
       - `action-rpg`: once `core-loop-design` approved → `combat-system-design`, `character-design`, `progression-design` may run concurrently
       - `narrative-adventure`: once `core-loop-design` approved → `narrative-design`, `character-design`, `world-design` may run concurrently
       - Always serial (never parallelise): `art-direction → art-concept → art-spec-design` (each writes data the next needs)
       - Always serial: `game-design-finalize` (reads ALL — stays `hard_blocked_by` all selected nodes)
```

- [ ] **Step 3: Update the ad-hoc node injection rule (line 907)**

Find this text immediately after the canonical node rule:

```
     - **Ad-hoc optional node** (in `optional_nodes` but absent from node_order or canonical registry): use Step 2.7 research to generate node-spec content; position it immediately before `game-design-finalize` in the generated workflow sequence; `blocked_by` = last SELECTED canonical optional node in node_order sequence order (i.e., highest-index selected canonical optional); if no canonical optionals are selected, `blocked_by` = last required node in node_order; `unlocks` = game-design-finalize.
```

Replace with:

```
     - **Ad-hoc optional node** (in `optional_nodes` but absent from node_order or canonical registry): use Step 2.7 research to generate node-spec content; position it immediately before `game-design-finalize` in the generated workflow sequence; `hard_blocked_by` = last SELECTED canonical optional node in node_order sequence order (if no canonical optionals selected, `hard_blocked_by` = last required node in node_order); `unlocks` = game-design-finalize.
```

- [ ] **Step 4: Update the art-concept injection line (line 914)**

Find:

```
- `blocked_by: ["art-direction"]`; update `art-spec-design` to `blocked_by: ["art-concept"]` (remove `art-direction` from its blocked_by list)
```

Replace with:

```
- `hard_blocked_by: ["art-direction"]`; update `art-spec-design` to `hard_blocked_by: ["art-concept"]` (remove `art-direction` from its hard_blocked_by list)
```

- [ ] **Step 5: Verify no remaining legacy `blocked_by:` in YAML frontmatter**

```bash
grep -n "^blocked_by:\|  blocked_by:" /Users/aa/workspace/myskills/claude/meta-skill/skills/bootstrap.md | head -10
```

Expected: zero results (all frontmatter should now use `hard_blocked_by:`).

Also verify the new parallelism rule is present:

```bash
grep -n "Parallelism rule\|alignment_refs.*each other\|casual-mobile.*economy" /Users/aa/workspace/myskills/claude/meta-skill/skills/bootstrap.md | head -5
```

Expected: "Parallelism rule" appears; `casual-mobile` parallel group is listed.

- [ ] **Step 6: Commit**

```bash
cd /Users/aa/workspace/myskills
git add claude/meta-skill/skills/bootstrap.md
git commit -m "$(cat <<'EOF'
fix: game-design injection uses hard_blocked_by + parallelism rule

Replaces legacy blocked_by with hard_blocked_by throughout game-design
injection rules. Adds explicit parallelism rule identifying which sibling
nodes (economy, progression, narrative etc.) can run concurrently after
their shared predecessor is approved, using alignment_refs semantics.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Self-Review

**Spec coverage:**

| Bug | Task | Covered? |
|-----|------|---------|
| #1 check_artifacts all_exist ignores validation_error | Task 1 | ✅ |
| #2 validate_bootstrap TypeError on dict artifact | Task 2 | ✅ |
| #3 app-design.md no bootstrap injection | Task 3 | ✅ |
| #4 orchestrator hardcodes game-design gate path | Task 4 | ✅ |
| #5 concept-contract game/art-only, app-design inconsistency | Task 5 | ✅ |
| #6 game-design injection uses legacy blocked_by, no parallelism | Task 6 | ✅ |

**Placeholder scan:** None. All Python code blocks are complete and runnable. All markdown replacement blocks are complete and exact.

**Type consistency:**
- `check_node_artifacts` function name used in test matches the actual import from `check_artifacts.py` ✅
- `validate_workflow` function name used in test matches `__all__` export in `validate_bootstrap.py` ✅
- `hard_blocked_by` used consistently in Tasks 3, 4, 6 ✅
- `approval_record_path` field name used consistently in Tasks 3 and 4 ✅

**Dependencies between tasks:**
- Tasks 1 and 2 are independent — run in either order
- Task 3 (app-design injection) must come before Task 4 (orchestrator fix uses `approval_record_path` that Task 3 establishes)
- Task 5 (concept-contract generalize) is independent
- Task 6 (parallelism) is independent
- Recommended order: **1 → 2 → 3 → 4 → 5 → 6**
