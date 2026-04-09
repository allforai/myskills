# Design Audit Dimensions & Interaction Gate

> Consolidated knowledge extracted from the product-design-skill's design-audit and interaction-gate systems.
> Reference for any capability that needs to perform design verification, quality gating, or cross-layer consistency checks.

---

## Part 1: The 8-Dimension Design Audit System

The design audit verifies the full product design pipeline using `product-map` as the anchor. It operates across 8 dimensions, organized into deterministic checks (Phase A) and semantic checks (Phase B).

### Dimension 1: Reverse Trace (逆向追溯)

**Purpose**: Every downstream artifact must trace back to a legitimate upstream source.

**Direction**: Bottom-up -- from downstream products back to upstream sources.

**Check items**:

| ID | Check | Condition | Logic |
|----|-------|-----------|-------|
| T1 | screen -> task | experience-map exists | Every screen's `task_refs` task_id must exist in task-inventory |
| T2 | use-case -> task | use-case exists | Every use-case's `task_id` must exist in task-inventory |
| T3 | use-case -> screen | use-case + experience-map exist | Every use-case's `screen_ref` must exist in experience-map |
| T4 | gap-finding -> task | feature-gap exists | Every gap's `task_id` must exist in task-inventory |

**Result markers**:
- `PASS` -- reference is valid, upstream source exists
- `ORPHAN` -- no source, downstream artifact references a non-existent upstream ID

Each orphan item records: check_id, source layer, item_id, item_name, missing upstream ID.

---

### Dimension 2: Coverage Flood (覆盖洪泛)

**Purpose**: Every upstream node must be fully consumed by downstream layers.

**Direction**: Top-down -- from task-inventory flooding down to all downstream layers.

**Check items**:

| ID | Check | Condition | Logic |
|----|-------|-----------|-------|
| C1 | task -> screen | experience-map exists | Every task has at least one screen referencing it (via screen's `task_refs`) |
| C2 | task -> use-case | use-case exists | Every task has at least one normal-flow use case |
| C3 | task -> gap-checked | feature-gap exists | Every task has been checked in the gap report |
| C4 | task -> ui-design | ui-design exists | Every task is reflected in UI design (task name or associated screen mentioned in ui-design-spec) |
| C5 | role -> full journey | experience-map + use-case exist | Per-role trace: tasks -> screens -> use-cases, detecting broken chains |

**Coverage formula**: `covered / total x 100%`

**Result markers**:
- `COVERED` -- task is fully consumed by downstream layer
- `GAP` -- task is not consumed by a downstream layer

Each gap item records: check_id, task_id, name, missing_in (which downstream layer).

---

### Dimension 3: Horizontal Consistency (横向一致性)

**Purpose**: Adjacent layers have no contradictions.

**Check items**:

| ID | Check | Condition | Logic |
|----|-------|-----------|-------|
| X1 | frequency x click_depth | product-map + experience-map exist | High-frequency task (frequency=high) with click_depth >= 3 in experience-map -> WARNING (high-frequency operation buried deep) |
| X2 | use-case screen_ref validity | use-case + experience-map exist | Use-case references a `screen_ref` that does not exist in experience-map -> BROKEN_REF |

**Result markers**:

| Marker | Meaning | Severity |
|--------|---------|----------|
| `OK` | No contradiction | -- |
| `CONFLICT` | Cross-layer contradiction, must fix | Highest |
| `WARNING` | Design rationality risk | Medium |
| `BROKEN_REF` | Reference broken | Medium |

**Severity ordering** (for all reported issues): CONFLICT > ORPHAN > GAP > WARNING > BROKEN_REF. Within same severity, sort by task_id.

---

### Dimension 4: Information Fidelity (信息保真)

**Purpose**: Intent is preserved across transformations. Key objects must be traceable and have multi-viewpoint coverage.

**Gate metrics**:

| ID | Gate | Logic | Recommended Threshold |
|----|------|-------|-----------------------|
| F1 | Traceability completeness rate | Proportion of key downstream objects traceable to upstream evidence/references | >= 95% |
| F2 | Viewpoint coverage rate | Proportion of key objects covering at least 4/6 viewpoints (user/business/tech/ux/data/risk) | >= 90% |

**Result markers**:
- `PASS` -- meets threshold
- `BELOW_THRESHOLD` -- below threshold, recommend going upstream to add context

**Quantified output**: `fidelity_score` as a numeric indicator, plus Traceability completeness rate and Viewpoint coverage rate as quality gates.

---

### Dimension 5: Pattern Consistency (模式一致性)

**Purpose**: Similar entities/screens follow the same design patterns.

**Activation condition**: experience-map.json has at least one screen with `_pattern` or `_pattern_group` fields. Otherwise skipped.

**Check items**:

| ID | Check | Logic |
|----|-------|-------|
| 5a | Layout template consistency | Group screens by `_pattern_group`, check if main layout template is consistent (action bar position, list style, form entry method). Inconsistency -> `PATTERN_DRIFT` |
| 5b | Cross-entity CRUD consistency | For all PT-CRUD instances: check "Create" button position consistency (unified top-right vs inline), "Delete" confirmation method consistency (modal vs inline). Inconsistency -> `CRUD_INCONSISTENCY` |
| 5c | Approval flow status label system | For all PT-APPROVAL instances: check status label color semantics (pending/approved/rejected) are unified. Inconsistency -> `APPROVAL_COLOR_DRIFT` |
| 5d | State machine action buttons | For all PT-STATE instances: check state transition button placement consistency (top action bar / detail bottom / inline). Inconsistency -> `STATE_ACTION_DRIFT` |

**Severity levels**:
- `HIGH` -- Core path (CRUD/approval flow) drift, high user cognitive cost
- `MEDIUM` -- Secondary path (export/state machine) drift
- `LOW` -- Detail-level differences (button label text)

**Issue types**: `PATTERN_DRIFT`, `CRUD_INCONSISTENCY`, `APPROVAL_COLOR_DRIFT`, `STATE_ACTION_DRIFT`

---

### Dimension 6: Behavioral Consistency (行为一致性)

**Purpose**: The same action behaves the same way everywhere across all screens.

**Activation condition**: experience-map.json has at least one screen with `_behavioral` or `_behavioral_standards` fields. Otherwise skipped.

**Check items**:

| ID | Check | Logic |
|----|-------|-------|
| 5.6a | Behavioral standard compliance | Group screens by `_behavioral_standards` category. Check if each screen's design in ui-design-spec matches the standard scheme. Mismatch -> `BEHAVIORAL_DRIFT` |
| 5.6b | Destructive operation confirmation compliance | For each screen's `crud=D` action with `requires_confirm=false`: if BC-DELETE-CONFIRM standard is `modal_confirm` -> `BEHAVIORAL_VIOLATION` |

**Severity levels**:
- `HIGH` -- Destructive operation without confirmation (`BEHAVIORAL_VIOLATION`), user data safety risk
- `MEDIUM` -- Behavioral drift (`BEHAVIORAL_DRIFT`), consistency experience degraded
- `LOW` -- Minor deviation (slight loading method difference)

**Issue types**: `BEHAVIORAL_DRIFT`, `BEHAVIORAL_VIOLATION`

---

### Dimension 7: Interaction Type Consistency (交互类型一致性)

**Purpose**: Screens sharing the same interaction type follow unified layout constraints.

**Activation condition**: experience-map screens contain `interaction_type` field.

**Check items**:

| ID | Check | Logic |
|----|-------|-------|
| 5.7a | Same-type layout consistency | Extract layout constraints per interaction type. Check each screen against allowed/forbidden layouts. Forbidden layout -> `LAYOUT_FORBIDDEN`. Non-allowed layout -> `LAYOUT_DRIFT` |
| 5.7b | Same-type layout drift detection | For screens sharing an interaction_type, detect if layouts diverge (e.g., 4 use table but 1 uses card). Divergence -> `INCONSISTENT_LAYOUT` |
| 5.7c | Type-context match validation | Verify interaction_type matches expected frequency for product_type x audience x platform. Excluded type appearing -> `TYPE_CONTEXT_MISMATCH`. Low-frequency types exceeding 30% -> `LOW_TYPE_OVERREPRESENTED` |

**Layout constraints reference** (selected types):

| Type | Allowed Layout | Forbidden |
|------|---------------|-----------|
| MG1 Read-only list | list/table/grid | form, wizard |
| MG2-L List | list/table | inline form (create should be separate page/modal) |
| MG2-C Create | form page/modal | -- |
| MG2-E Edit | form page/modal (must prefill old values) | -- |
| MG3 State machine | status label (dedicated column) + action dropdown/swipe | -- |
| MG5 Master-detail | master entity area + child entity tabs | single-layer detail without child entities |
| MG6 Tree management | tree component + linked edit area | -- |
| EC1 Content detail | image carousel + spec selection + bottom action bar | no spec selection |
| WK1 Chat/IM | message stream + bottom input box | -- |
| WK5 Kanban | horizontal multi-column + cards | single-column list |

**Severity levels**:
- `HIGH` -- `LAYOUT_FORBIDDEN` / `TYPE_CONTEXT_MISMATCH`
- `MEDIUM` -- `INCONSISTENT_LAYOUT` / `LAYOUT_DRIFT`
- `LOW` -- `LOW_TYPE_OVERREPRESENTED`

---

### Dimension 8: Consumer Maturity Consistency (用户端成熟度一致性)

**Purpose**: When `experience_priority.mode = consumer` or `mixed`, all downstream artifacts must continuously maintain mature consumer product standards rather than regressing into admin-panel-style or concept-demo-style expression.

**Activation condition**: `product-map.json` contains `experience_priority` with mode `consumer` or `mixed`.

**Audit checks** (Phase A, Step 3.8):
- Does product-map define a main-line closed loop and sustained relationship?
- Does experience-map preserve home-page main-line, next-step guidance, and status system?
- Does ui-design implement these requirements as visual and interaction specs?
- Can feature-gap / use-case still identify consumer maturity gaps?

**Regression detection**: If any layer in the chain degrades the consumer experience into:
- "Feature entrance puzzle" (功能入口拼盘)
- "Compressed admin page" (后台页面压缩版)
- "Concept demo page collection" (概念 demo 页面集合)

...it is recorded as a consistency issue.

**Additional checks when consumer/mixed**:
- Main-line clarity: can the user identify the core goal within 2 seconds?
- Next-step guidance: after completing an action, does the user know what to do next?
- Sustained relationship: does the flow stop at one-time completion without revisit/continuous-use cues?
- Low-attention adaptation: does the mobile scenario require excessive memory and back-and-forth jumping?

---

## Part 2: Interaction Gate Scoring Model

The Interaction Gate is a quality gate positioned between experience-map and ui-design. It scores every operation line for usability before allowing it to proceed to UI design.

### 4 Scoring Dimensions

| Dimension | Weight (pts) | Description |
|-----------|-------------|-------------|
| `step_count` | 30 | Operation step count: fewer steps = better. Deducted when exceeding reasonable range |
| `context_switches` | 25 | Context switches: role/page/modal switch count. Fewer = better |
| `wait_feedback` | 25 | Wait feedback: whether async operations have clear wait states and feedback mechanisms |
| `thumb_zone` | 20 | Thumb zone: whether high-frequency mobile operations fall within thumb-reachable area |

### Scoring Formula

```
total_score = step_count + context_switches + wait_feedback + thumb_zone
```

Maximum score: 100 points.

### Default Threshold

**70 points**. Lines scoring below threshold are marked `fail`.

### Result Values

- `pass` -- total_score >= threshold
- `fail` -- total_score < threshold

### Fail Protocol

**Fail blocks downstream until user decides.** For each failing operation line, the user must choose:
- **(a) Adjust experience-map**: modify the operation line definition based on issue suggestions, then re-run interaction-gate
- **(b) Accept current score**: mark as `accepted`, continue to downstream UI design

All failing lines must be resolved before proceeding. No silent skipping of failing lines.

**Auto mode exception**: When `__orchestrator_auto: true`, failing lines are auto-accepted (`disposition: "auto_accepted"`), EXCEPT lines scoring below 50 (severe UX defect) which still require explicit user confirmation.

### Score Writeback to experience-map

After scoring, each operation line's `total_score` is written back to the corresponding node's `quality_score` field in `experience-map.json` (Step 5 of the workflow).

### Self-Review Loop for Score Validation (Step 2.5)

After LLM scoring, the LLM switches to a reviewer perspective and validates scores against upstream baselines. All validation is performed by the LLM.

**Upstream baseline checks** (using experience-map.json):

1. **Score vs design complexity**: A line with only 2 screens and 1-2 actions each -- step_count should not be below 25/30. Conversely, an 8-step line spanning 4 screens -- step_count should not exceed 20/30.
2. **context_switches vs flow_context**: Platform switches, role switches, and modal popup counts in the operation line should correspond to context_switches score.
3. **wait_feedback vs states**: Lines where screens define loading/error state handling should score higher than those without.
4. **thumb_zone vs platform**: Desktop-web operation lines should have thumb_zone weight reasonably adjusted (desktop has no thumb zone constraint).

**Consumer/mixed additional review**:

5. **Main-line clarity**: Does the home/entry page bury the main action in a feature entrance puzzle?
6. **Next-step clarity**: After completing an action, is there clear follow-up guidance or result feedback?
7. **Sustained relationship**: Is there a complete absence of progress, history, reminders, notifications, recent activity, or other revisit cues?

**Self-consistency checks**:
- Score distribution should not cluster in the "safety zone" (e.g., all lines at 85-90)
- Similar operation lines (e.g., two CRUD management lines) should have explainable score differences
- Issues list must correspond to low-scoring dimensions (no dimension should lose points without a matching issue)

**Loop mechanism**:
```
LLM scores -> self-review validation
  Pass -> proceed to Step 3
  Fail ->
    List specific problems (which scores mismatch design, which distributions are abnormal)
    LLM corrects affected line scores and issues
    -> re-review (max 2 rounds)
  After 2 rounds still failing -> record remaining issues as WARNING, continue
```

### Output Schema (interaction-gate.json)

```json
{
  "version": "1.1.0",
  "generated_at": "ISO8601",
  "threshold": 70,
  "summary": {
    "total_lines": 8,
    "passed": 6,
    "failed": 2,
    "accepted": 1,
    "adjusted": 1,
    "avg_score": 78.5
  },
  "lines": [
    {
      "line_id": "OL001",
      "line_name": "...",
      "scores": {
        "step_count": 28,
        "context_switches": 20,
        "wait_feedback": 22,
        "thumb_zone": 18
      },
      "total_score": 88,
      "result": "pass",
      "issues": []
    },
    {
      "line_id": "OL002",
      "line_name": "...",
      "scores": { "step_count": 18, "context_switches": 15, "wait_feedback": 10, "thumb_zone": 12 },
      "total_score": 55,
      "result": "fail",
      "disposition": "accepted",
      "issues": [
        {
          "dimension": "wait_feedback",
          "detail": "No progress feedback during wait",
          "suggestion": "Add progress bar and estimated time"
        }
      ]
    }
  ]
}
```

---

## Part 3: Three-Phase Parallel Audit Architecture

### Phase A: Script-Driven Checks (Serial)

Deterministic, script-based verification. Executes sequentially.

**Pre-requisites**:
1. Load concept baseline: `concept-baseline.json` (auto-load, WARNING if missing)
2. Two-stage loading: load indexes first (task-index, screen-index, flow-index), then probe available layers

**Available layers probed**:

| Layer | Required/Optional | Detection File |
|-------|-------------------|----------------|
| product-map | Required (abort if missing) | `.allforai/product-map/product-map.json` |
| experience-map | Required (auto-run if missing) | `.allforai/experience-map/experience-map.json` |
| use-case | Optional | `.allforai/use-case/use-case-tree.json` |
| feature-gap | Optional | `.allforai/feature-gap/gap-tasks.json` |
| ui-design | Optional | `.allforai/ui-design/ui-design-spec.md` |

Missing optional layers -> skip related checks, annotate "layer missing, skipped" in report.

**Steps executed in Phase A**:

| Step | Dimension | Description |
|------|-----------|-------------|
| Step 1 | Reverse Trace | Bottom-up reference validation |
| Step 2 | Coverage Flood | Top-down consumption verification |
| Step 3 | Horizontal Consistency | Adjacent-layer contradiction detection |
| Step 3.5 | Information Fidelity | Traceability and viewpoint coverage gates |
| Step 3.7 | Continuity Audit | Reads interaction-gate.json, checks step count <= 7, context switches <= 2, wait feedback coverage = 1.0, thumb zone compliance >= 0.8 |
| Step 3.8 | Consumer Maturity | When experience_priority = consumer/mixed |
| XV | Cross-Validation | Cross-model review if available |

**Output**: `audit-report.json` (baseline report) + `audit-report.md`

### Phase B: 3 Parallel LLM Agents (Semantic Audit)

After Phase A completes, three agents run in parallel via a single message with 3 Agent tool calls. Each reads Phase A's `audit-report.json` as read-only context.

| Agent | Audit Dimensions | Shard Output |
|-------|-----------------|--------------|
| Agent 1 | Step 5: Pattern Consistency + Step 5.5: Innovation Fidelity | `audit-shard-pattern.json` |
| Agent 2 | Step 5.6: Behavioral Consistency | `audit-shard-behavioral.json` |
| Agent 3 | Step 5.7: Interaction Type Consistency | `audit-shard-interaction.json` |

**Barrier synchronization**: All 3 agents must complete before Phase C begins.

**Shard JSON schema**:
```json
{
  "shard": "{shard_name}",
  "generated_at": "ISO8601",
  "sections": {
    "{section_key}": {
      "status": "pass | issues_found | skipped",
      "issues": [...]
    }
  }
}
```

**Agent rules**:
- Must not modify `audit-report.json` (Phase A output)
- Must not read/write other agents' shard files
- If preconditions not met, write shard with `status: "skipped"` (never skip writing the file entirely)

**Quick mode**: Phase B is skipped entirely. Phase C uses Phase A's report as final.

### Phase C: Merge and Reconcile

After all 3 agents complete, the orchestrator merges results.

**Merge steps**:
1. Read Phase A baseline: `audit-report.json`
2. Read 3 shard files (missing shards treated as skipped):
   - `audit-shard-pattern.json` -> merge into `pattern_consistency` + `innovation_fidelity`
   - `audit-shard-behavioral.json` -> merge into `behavioral_consistency`
   - `audit-shard-interaction.json` -> merge into `interaction_type_consistency`
3. Merge shard `sections` content into `audit-report.json` summary and top-level fields
4. Regenerate `audit-report.md` (including all dimensions)
5. Delete shard files (already merged into main report)

**Merge pseudocode**:
```python
report = load_json("audit-report.json")  # Phase A baseline

for shard_name in ["pattern", "behavioral", "interaction"]:
    shard_path = f"audit-shard-{shard_name}.json"
    if not exists(shard_path):
        continue
    shard = load_json(shard_path)
    for section_key, section_data in shard["sections"].items():
        report["summary"][section_key] = {
            k: v for k, v in section_data.items() if k != "issues"
        }
        report[f"{section_key}_issues"] = section_data.get("issues", [])

write_json("audit-report.json", report)
regenerate_markdown("audit-report.md", report)
delete_shards()
```

---

## Part 4: Scale Adaptation & Defensive Patterns

### Scale-Adaptive Reporting

Threshold based on task count:

| Scale | Task Count | Report Detail |
|-------|-----------|---------------|
| small | <= 30 | Full detailed report -- every check result listed individually |
| medium | 31-80 | Layered by severity -- HIGH/CONFLICT detailed, MEDIUM/WARNING summarized, LOW/INFO statistics only |
| large | > 80 | Statistical overview + only HIGH/CONFLICT expanded, rest collapsed to statistics |

### Iron Laws

1. **Read-only**: Audit only reports issues, never modifies upstream artifacts
2. **Available artifacts determine scope**: Missing layers are auto-skipped, no error, annotate "layer missing, skipped"
3. **product-map is the anchor**: All trace and flood operations root at product-map's task-inventory
4. **Sort by severity**: CONFLICT > ORPHAN > GAP > WARNING > BROKEN_REF
5. **Category consistency**: All tasks in task-inventory must have `category` (basic/core). Missing category -> WARNING
6. **Idempotent**: Multiple runs produce same results. No side effects, no cached decisions, no dependency on previous run

### XV Cross-Validation (after Step 3)

| Validation Point | Task Type | Content Sent | Written To |
|-----------------|-----------|--------------|------------|
| Cross-layer contradiction verification | `cross_layer_validation` -> gpt | Audit summary: CONFLICT/ORPHAN/GAP issue list + typical contradiction cases | `cross_model_review.additional_contradictions` |
| Coverage blind spot analysis | `coverage_analysis` -> deepseek | Audit summary: coverage stats + uncovered task list + available layer info | `cross_model_review.coverage_blindspots` |

---

## Part 5: Final Report Schema

### JSON Schema (audit-report.json)

```json
{
  "generated_at": "ISO8601",
  "mode": "full|trace|coverage|cross|role",
  "role_filter": "role name (role mode only)",
  "available_layers": ["product-map", "experience-map", "..."],
  "summary": {
    "trace": { "total": 0, "pass": 0, "orphan": 0 },
    "coverage": { "total": 0, "covered": 0, "gap": 0, "rate": "0%" },
    "cross": { "total": 0, "ok": 0, "conflict": 0, "warning": 0, "broken_ref": 0 },
    "fidelity": {
      "traceability_rate": "0%",
      "traceability_status": "PASS|BELOW_THRESHOLD",
      "viewpoint_coverage_rate": "0%",
      "viewpoint_status": "PASS|BELOW_THRESHOLD"
    },
    "pattern_consistency": {
      "status": "pass|issues_found|skipped",
      "total_patterns_checked": 0,
      "clean_patterns": 0,
      "drift_patterns": 0
    },
    "innovation_fidelity": {
      "status": "pass|issues_found|skipped",
      "core_concepts_total": 0,
      "survived": 0,
      "diluted": 0,
      "incomplete": 0
    },
    "behavioral_consistency": {
      "status": "pass|issues_found|skipped",
      "total_categories_checked": 0,
      "compliant_screens": 0,
      "violating_screens": 0
    },
    "interaction_type_consistency": {
      "status": "pass|issues_found|skipped",
      "total_types_checked": 0,
      "consistent_types": 0,
      "drift_types": 0
    }
  },
  "trace_issues": [],
  "coverage_issues": [],
  "cross_issues": [],
  "pattern_consistency_issues": [],
  "behavioral_consistency_issues": [],
  "interaction_type_consistency_issues": []
}
```

### Markdown Report Structure (audit-report.md)

Sections in order:
1. Summary (mode, available layers, per-dimension statistics)
2. CONFLICT (cross-layer contradictions)
3. ORPHAN (no upstream source)
4. GAP (uncovered tasks)
5. WARNING (risks)
6. BROKEN_REF (reference breakage)
7. Pattern Consistency (PATTERN_DRIFT, CRUD_INCONSISTENCY, etc.)
8. Behavioral Consistency (BEHAVIORAL_DRIFT, BEHAVIORAL_VIOLATION)
9. Interaction Type Consistency (LAYOUT_FORBIDDEN, LAYOUT_DRIFT, TYPE_CONTEXT_MISMATCH)
10. Innovation Fidelity (INNOVATION_DILUTED, INNOVATION_INCOMPLETE)
11. Consumer Maturity (when applicable)
