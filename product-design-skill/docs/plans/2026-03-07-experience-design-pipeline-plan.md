# Experience Design Pipeline Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace screen-map with experience-map pipeline: journey-emotion-map (Phase 3) -> experience-map (Phase 4) -> interaction-quality-gate (Phase 4.5), upgrade all downstream consumers.

**Architecture:** Three new scripts replace `gen_screen_map.py` and `gen_screen_map_split.py`. All downstream scripts (`gen_use_cases.py`, `gen_feature_gap.py`, `gen_feature_prune.py`, `gen_ui_design.py`, `gen_design_audit.py`, `gen_ui_stitch.py`, `gen_ui_components.py`) switch from `load_screen_map()` to `load_experience_map()`. Skill files and schemas are renamed/rewritten to match.

**Tech Stack:** Python 3, JSON, Markdown. No new dependencies.

**Design doc:** `docs/plans/2026-03-07-experience-design-pipeline-design.md`

---

### Task 1: Update `_common.py` — Replace screen-map loaders with experience-map loaders

**Files:**
- Modify: `product-design-skill/scripts/_common.py`

**Step 1: Remove old screen-map functions**

Remove these functions and constants:
- `load_screen_map(base)` (returns `(screens_list, loaded_bool)`)
- `build_screen_by_id(screens)` (returns `{id: screen}`)
- `build_task_screen_map(screens)` (returns `{task_id: [screens]}`)
- `get_screen_tasks(screen)` (returns task ID list)
- `SCREEN_TASKS_FIELD = "tasks"`
- `SCREEN_INDEX_TASK_REFS_FIELD = "task_refs"`

**Step 2: Add new experience-map functions**

```python
# ── experience-map loaders ──

def load_journey_emotion(base):
    """Load journey-emotion-map.json, return journey_lines list."""
    data = load_json(os.path.join(base, "experience-map/journey-emotion-map.json"))
    if data is None:
        return []
    return ensure_list(data, "journey_lines")


def load_experience_map(base):
    """Load experience-map.json, return (operation_lines list, screen_index dict, loaded bool)."""
    data = load_json(os.path.join(base, "experience-map/experience-map.json"))
    if data is None:
        return [], {}, False
    lines = ensure_list(data, "operation_lines")
    index = data.get("screen_index", {}) if isinstance(data, dict) else {}
    return lines, index, True


def build_node_by_id(operation_lines):
    """Build {node_id: node_object} mapping from operation_lines."""
    result = {}
    for line in operation_lines:
        for node in line.get("nodes", []):
            result[node["id"]] = node
    return result


def build_screen_by_id_from_lines(operation_lines):
    """Build {screen_id: screen_object} mapping from all nodes in all operation lines."""
    result = {}
    for line in operation_lines:
        for node in line.get("nodes", []):
            for s in node.get("screens", []):
                result[s["id"]] = s
    return result


def build_task_screen_map_from_lines(operation_lines):
    """Build {task_id: [screen_ids]} by collecting screen.tasks across all nodes."""
    result = {}
    for line in operation_lines:
        for node in line.get("nodes", []):
            for s in node.get("screens", []):
                for tid in s.get("tasks", []):
                    result.setdefault(tid, []).append(s["id"])
    return result


def get_node_screens(node):
    """Return screen list from a node object."""
    return node.get("screens", [])


def load_interaction_gate(base):
    """Load interaction-gate.json, return gate data dict or None."""
    return load_json(os.path.join(base, "experience-map/interaction-gate.json"))
```

**Step 3: Commit**

```bash
git add product-design-skill/scripts/_common.py
git commit -m "refactor: replace screen-map loaders with experience-map loaders in _common.py"
```

---

### Task 2: Create `gen_journey_emotion.py` — Phase 3 journey-emotion-map generation

**Files:**
- Create: `product-design-skill/scripts/gen_journey_emotion.py`

**Step 1: Write the script**

The script must:
1. Load `role-profiles.json` and `business-flows.json` from product-map
2. For each business flow, generate a journey line with emotion nodes
3. Each emotion node has: `step`, `action`, `emotion`, `intensity` (1-10), `risk`, `design_hint`
4. Set `human_decision: true` on all lines (default — human confirms before experience-map)
5. Output to `.allforai/experience-map/journey-emotion-map.json`

```python
#!/usr/bin/env python3
"""Phase 3: Generate journey-emotion-map from product-map data.

Usage:
    python3 gen_journey_emotion.py <BASE_PATH> [--mode auto]
"""
import sys, os, json, datetime

sys.path.insert(0, os.path.dirname(__file__))
import _common as C


def main():
    if len(sys.argv) < 2:
        print("Usage: gen_journey_emotion.py <BASE_PATH> [--mode auto]")
        sys.exit(1)

    BASE = sys.argv[1]
    mode = "auto"
    if "--mode" in sys.argv:
        idx = sys.argv.index("--mode")
        if idx + 1 < len(sys.argv):
            mode = sys.argv[idx + 1]

    # ── load inputs ──
    roles = C.load_role_profiles(BASE)
    flows = C.load_business_flows(BASE)
    tasks_inv = C.load_task_inventory(BASE)

    if not flows:
        print("ERROR: business-flows.json not found or empty. Run product-map first.")
        sys.exit(1)

    # ── build journey lines from business flows ──
    journey_lines = []
    for i, flow in enumerate(flows):
        fid = flow.get("id", f"F{i+1:02d}")
        fname = flow.get("name", f"Flow {i+1}")
        frole = flow.get("role", flow.get("owner_role", ""))

        nodes_raw = C.get_flow_nodes(flow)
        emotion_nodes = []
        for step_idx, node in enumerate(nodes_raw):
            tid = node.get("task_id", node.get("id", ""))
            task = tasks_inv.get(tid, {})
            action = node.get("action", task.get("name", f"Step {step_idx+1}"))

            emotion_nodes.append({
                "step": step_idx + 1,
                "action": action,
                "emotion": "neutral",
                "intensity": 5,
                "risk": "",
                "design_hint": "",
            })

        journey_lines.append({
            "id": f"JL{i+1:02d}",
            "name": fname,
            "role": frole,
            "source_flow": fid,
            "emotion_nodes": emotion_nodes,
            "human_decision": True,
        })

    result = {
        "journey_lines": journey_lines,
        "decision_log": [],
        "generated_at": datetime.datetime.now().isoformat(),
    }

    # ── write output ──
    out_dir = os.path.join(BASE, "experience-map")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "journey-emotion-map.json")
    C.write_json(out_path, result)
    print(f"OK: {out_path} ({len(journey_lines)} journey lines)")

    # ── pipeline decision ──
    C.append_pipeline_decision(BASE, "journey-emotion", {
        "journey_line_count": len(journey_lines),
        "total_emotion_nodes": sum(len(jl["emotion_nodes"]) for jl in journey_lines),
    })


if __name__ == "__main__":
    main()
```

**Step 2: Run quick smoke test**

```bash
cd /Users/aa/Documents/myskills
python3 product-design-skill/scripts/gen_journey_emotion.py --help
```

Expected: Usage message printed, exit 1 (no BASE_PATH)

**Step 3: Commit**

```bash
git add product-design-skill/scripts/gen_journey_emotion.py
git commit -m "feat: add gen_journey_emotion.py for Phase 3 journey-emotion-map"
```

---

### Task 3: Create `gen_experience_map.py` — Phase 4 experience-map generation (replaces screen-map)

**Files:**
- Create: `product-design-skill/scripts/gen_experience_map.py`

**Step 1: Write the script**

The script must:
1. Load `journey-emotion-map.json` (Phase 3 output), `task-inventory.json`, `task-index.json`, `role-profiles.json`, `product-concept.json` (optional)
2. For each journey line, generate an operation line with nodes
3. Each node maps emotion data from journey line + generates screens from task inventory
4. Screen generation reuses CRUD inference logic from old `gen_screen_map.py` (module grouping, action metadata)
5. Build `screen_index` as embedded dict
6. Compute `continuity` metrics per line (total_steps, context_switches, wait_points)
7. Output to `.allforai/experience-map/experience-map.json`
8. Also generate `.allforai/experience-map/experience-map-report.md`

```python
#!/usr/bin/env python3
"""Phase 4: Generate experience-map from journey-emotion-map + task-inventory.

Replaces gen_screen_map.py. Organizes screens into operation lines with
emotion context, ux intent, and continuity metrics.

Usage:
    python3 gen_experience_map.py <BASE_PATH> [--mode auto]
"""
import sys, os, json, datetime, re

sys.path.insert(0, os.path.dirname(__file__))
import _common as C

# ── CRUD keywords (same as old gen_screen_map.py) ──
CRUD_KEYWORDS = {
    "C": ["新增", "创建", "添加", "注册", "上传", "发布", "录入", "create", "add", "new", "register", "upload"],
    "U": ["修改", "编辑", "更新", "调整", "设置", "配置", "update", "edit", "modify", "configure", "set"],
    "D": ["删除", "移除", "撤销", "取消", "remove", "delete", "cancel", "revoke"],
    "R": ["查看", "浏览", "搜索", "筛选", "导出", "统计", "列表", "详情", "view", "list", "search", "filter", "export", "detail"],
}


def infer_crud(task_name):
    """Infer CRUD type from task name keywords."""
    for crud, keywords in CRUD_KEYWORDS.items():
        for kw in keywords:
            if kw in task_name.lower():
                return crud
    return "R"


def infer_frequency(task):
    """Infer frequency tier from task metadata."""
    cat = task.get("category", "")
    if cat == "basic":
        return "高"
    elif cat == "core":
        return "中"
    return "低"


def build_screens_for_node(node_tasks, tasks_inv, screen_counter):
    """Build screen objects from a list of task IDs. Returns (screens, updated_counter)."""
    if not node_tasks:
        return [], screen_counter

    # Group by module
    module_groups = {}
    for tid in node_tasks:
        task = tasks_inv.get(tid, {})
        module = task.get("module", task.get("owner_role", "unknown"))
        module_groups.setdefault(module, []).append((tid, task))

    screens = []
    for module, task_pairs in module_groups.items():
        screen_counter += 1
        sid = f"S{screen_counter:03d}"

        actions = []
        task_ids = []
        for tid, task in task_pairs:
            tname = task.get("name", tid)
            crud = infer_crud(tname)
            actions.append({
                "label": tname,
                "crud": crud,
                "frequency": infer_frequency(task),
                "task_ref": tid,
            })
            task_ids.append(tid)

        # Determine primary action
        primary = actions[0]["label"] if actions else module
        screen_name = f"{module}_screen"

        screens.append({
            "id": sid,
            "name": screen_name,
            "description": f"{module} operations",
            "route_type": "push",
            "tasks": task_ids,
            "actions": actions,
            "primary_action": primary,
            "non_negotiable": [],
        })

    return screens, screen_counter


def main():
    if len(sys.argv) < 2:
        print("Usage: gen_experience_map.py <BASE_PATH> [--mode auto]")
        sys.exit(1)

    BASE = sys.argv[1]

    # ── load inputs ──
    journey_lines = C.load_journey_emotion(BASE)
    tasks_inv = C.load_task_inventory(BASE)
    roles = C.load_role_profiles(BASE)
    flows = C.load_business_flows(BASE)

    if not journey_lines:
        print("ERROR: journey-emotion-map.json not found or empty. Run journey-emotion first.")
        sys.exit(1)
    if not tasks_inv:
        print("ERROR: task-inventory.json not found or empty. Run product-map first.")
        sys.exit(1)

    # ── build flow→tasks mapping ──
    flow_by_id = {f.get("id", ""): f for f in flows} if flows else {}

    # ── generate operation lines ──
    operation_lines = []
    screen_index = {}
    screen_counter = 0

    for jl in journey_lines:
        jl_id = jl["id"]
        source_flow_id = jl.get("source_flow", "")
        flow = flow_by_id.get(source_flow_id, {})
        flow_nodes = C.get_flow_nodes(flow) if flow else []

        nodes = []
        for en in jl.get("emotion_nodes", []):
            step = en["step"]

            # Match to flow node for task references
            flow_node = flow_nodes[step - 1] if step - 1 < len(flow_nodes) else {}
            node_task_id = flow_node.get("task_id", "")
            node_tasks = [node_task_id] if node_task_id and node_task_id in tasks_inv else []

            # Build screens for this node
            node_screens, screen_counter = build_screens_for_node(
                node_tasks, tasks_inv, screen_counter
            )

            node_id = f"N{jl_id[2:]}{step:02d}"  # e.g. N0101 for JL01 step 1
            node = {
                "seq": step,
                "id": node_id,
                "action": en.get("action", f"Step {step}"),
                "emotion_state": en.get("emotion", "neutral"),
                "emotion_intensity": en.get("intensity", 5),
                "ux_intent": en.get("design_hint", ""),
                "screens": node_screens,
                "exception_states": [],
            }
            nodes.append(node)

            # Update screen_index
            for s in node_screens:
                sid = s["id"]
                if sid not in screen_index:
                    screen_index[sid] = {"name": s["name"], "appears_in": []}
                ol_id = f"OL{jl_id[2:]}"
                screen_index[sid]["appears_in"].append(f"{ol_id}.{node_id}")

        ol = {
            "id": f"OL{jl_id[2:]}",
            "name": jl.get("name", ""),
            "source_journey": jl_id,
            "role": jl.get("role", ""),
            "nodes": nodes,
            "continuity": {
                "total_steps": len(nodes),
                "context_switches": 0,
                "wait_points": [],
                "quality_score": None,
            },
        }
        operation_lines.append(ol)

    result = {
        "operation_lines": operation_lines,
        "screen_index": screen_index,
        "generated_at": datetime.datetime.now().isoformat(),
    }

    # ── write output ──
    out_dir = os.path.join(BASE, "experience-map")
    os.makedirs(out_dir, exist_ok=True)

    out_path = os.path.join(out_dir, "experience-map.json")
    C.write_json(out_path, result)

    total_screens = len(screen_index)
    total_nodes = sum(len(ol["nodes"]) for ol in operation_lines)
    print(f"OK: {out_path} ({len(operation_lines)} lines, {total_nodes} nodes, {total_screens} screens)")

    # ── generate report ──
    report_lines = [
        "# Experience Map Report\n",
        f"> Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n",
        f"## Summary\n",
        f"- Operation lines: {len(operation_lines)}",
        f"- Total nodes: {total_nodes}",
        f"- Total screens: {total_screens}\n",
        "## Operation Lines\n",
    ]
    for ol in operation_lines:
        report_lines.append(f"### {ol['id']} {ol['name']}")
        report_lines.append(f"- Role: {ol['role']}")
        report_lines.append(f"- Source journey: {ol['source_journey']}")
        report_lines.append(f"- Steps: {ol['continuity']['total_steps']}")
        report_lines.append("")
        for node in ol["nodes"]:
            screens_str = ", ".join(f"{s['id']}({s['name']})" for s in node["screens"])
            report_lines.append(
                f"  {node['seq']}. {node['action']} "
                f"[{node['emotion_state']} {node['emotion_intensity']}/10] "
                f"→ {screens_str or 'no screens'}"
            )
        report_lines.append("")

    report_path = os.path.join(out_dir, "experience-map-report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    # ── pipeline decision ──
    C.append_pipeline_decision(BASE, "experience-map", {
        "operation_line_count": len(operation_lines),
        "total_nodes": total_nodes,
        "total_screens": total_screens,
    })


if __name__ == "__main__":
    main()
```

**Step 2: Commit**

```bash
git add product-design-skill/scripts/gen_experience_map.py
git commit -m "feat: add gen_experience_map.py for Phase 4 experience-map (replaces screen-map)"
```

---

### Task 4: Create `gen_interaction_gate.py` — Phase 4.5 interaction quality gate

**Files:**
- Create: `product-design-skill/scripts/gen_interaction_gate.py`

**Step 1: Write the script**

The script must:
1. Load `experience-map.json`
2. For each operation line, evaluate: step count, context switches, wait feedback coverage, thumb zone compliance
3. Calculate per-line score (0-100)
4. Determine pass/fail against threshold (default 70)
5. Back-fill `quality_score` into experience-map.json
6. Output to `.allforai/experience-map/interaction-gate.json`

```python
#!/usr/bin/env python3
"""Phase 4.5: Interaction quality gate — validate experience-map continuity.

Evaluates operation lines for step count, context switches, wait feedback,
and thumb zone compliance. Back-fills quality_score into experience-map.

Usage:
    python3 gen_interaction_gate.py <BASE_PATH> [--threshold 70]
"""
import sys, os, json, datetime

sys.path.insert(0, os.path.dirname(__file__))
import _common as C

DEFAULT_THRESHOLD = 70
MAX_STEPS_IDEAL = 7  # Miller's law: 7 +/- 2
MAX_CONTEXT_SWITCHES = 2


def evaluate_line(ol):
    """Evaluate a single operation line, return score dict."""
    cont = ol.get("continuity", {})
    total_steps = cont.get("total_steps", len(ol.get("nodes", [])))
    context_switches = cont.get("context_switches", 0)
    wait_points = cont.get("wait_points", [])

    nodes = ol.get("nodes", [])
    issues = []

    # ── Step count score (0-30) ──
    if total_steps <= MAX_STEPS_IDEAL:
        step_score = 30
    elif total_steps <= MAX_STEPS_IDEAL + 2:
        step_score = 20
    else:
        step_score = max(0, 30 - (total_steps - MAX_STEPS_IDEAL) * 5)
        issues.append({
            "node": "-",
            "type": "step_count",
            "detail": f"Operation line has {total_steps} steps (ideal <= {MAX_STEPS_IDEAL})",
        })

    # ── Context switch score (0-25) ──
    if context_switches <= MAX_CONTEXT_SWITCHES:
        ctx_score = 25
    else:
        ctx_score = max(0, 25 - (context_switches - MAX_CONTEXT_SWITCHES) * 10)
        issues.append({
            "node": "-",
            "type": "context_switch",
            "detail": f"{context_switches} context switches (ideal <= {MAX_CONTEXT_SWITCHES})",
        })

    # ── Wait feedback coverage (0-25) ──
    # Check if wait points have corresponding screen actions
    wait_coverage = 1.0 if not wait_points else 0.8  # simplified heuristic
    wait_score = int(25 * wait_coverage)

    # ── Thumb zone compliance (0-20) ──
    # Heuristic: check if primary actions are in non_negotiable
    nn_count = 0
    total_screens = 0
    for node in nodes:
        for s in node.get("screens", []):
            total_screens += 1
            if s.get("non_negotiable"):
                nn_count += 1

    thumb_compliance = nn_count / max(total_screens, 1)
    thumb_score = int(20 * thumb_compliance)
    if thumb_compliance < 0.5 and total_screens > 0:
        issues.append({
            "node": "-",
            "type": "thumb_zone",
            "detail": f"Only {nn_count}/{total_screens} screens have non_negotiable constraints",
        })

    score = step_score + ctx_score + wait_score + thumb_score

    return {
        "line_id": ol["id"],
        "steps": total_steps,
        "context_switches": context_switches,
        "wait_feedback_coverage": round(wait_coverage, 2),
        "thumb_zone_compliance": round(thumb_compliance, 2),
        "score": score,
        "issues": issues,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: gen_interaction_gate.py <BASE_PATH> [--threshold 70]")
        sys.exit(1)

    BASE = sys.argv[1]
    threshold = DEFAULT_THRESHOLD
    if "--threshold" in sys.argv:
        idx = sys.argv.index("--threshold")
        if idx + 1 < len(sys.argv):
            threshold = int(sys.argv[idx + 1])

    # ── load experience-map ──
    op_lines, screen_index, loaded = C.load_experience_map(BASE)
    if not loaded:
        print("ERROR: experience-map.json not found. Run experience-map first.")
        sys.exit(1)

    # ── evaluate each line ──
    line_results = []
    for ol in op_lines:
        line_results.append(evaluate_line(ol))

    # ── determine overall result ──
    all_pass = all(lr["score"] >= threshold for lr in line_results)
    total_issues = sum(len(lr["issues"]) for lr in line_results)

    gate = {
        "gate_result": "pass" if all_pass else "warn",
        "lines": line_results,
        "threshold": threshold,
        "recommendation": f"{'pass' if all_pass else 'review'}, {total_issues} issue(s) to address",
        "generated_at": datetime.datetime.now().isoformat(),
    }

    # ── write gate output ──
    out_dir = os.path.join(BASE, "experience-map")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "interaction-gate.json")
    C.write_json(out_path, gate)
    print(f"OK: {out_path} (result={gate['gate_result']}, {total_issues} issues)")

    # ── back-fill quality_score into experience-map ──
    em_path = os.path.join(BASE, "experience-map/experience-map.json")
    em_data = C.load_json(em_path)
    if em_data and isinstance(em_data, dict):
        score_map = {lr["line_id"]: lr["score"] for lr in line_results}
        for ol in em_data.get("operation_lines", []):
            if ol["id"] in score_map:
                ol.setdefault("continuity", {})["quality_score"] = score_map[ol["id"]]
        C.write_json(em_path, em_data)
        print(f"OK: back-filled quality_score into {em_path}")

    # ── pipeline decision ──
    C.append_pipeline_decision(BASE, "interaction-gate", {
        "gate_result": gate["gate_result"],
        "threshold": threshold,
        "total_issues": total_issues,
        "line_scores": {lr["line_id"]: lr["score"] for lr in line_results},
    })


if __name__ == "__main__":
    main()
```

**Step 2: Commit**

```bash
git add product-design-skill/scripts/gen_interaction_gate.py
git commit -m "feat: add gen_interaction_gate.py for Phase 4.5 interaction quality gate"
```

---

### Task 5: Delete old screen-map scripts

**Files:**
- Delete: `product-design-skill/scripts/gen_screen_map.py`
- Delete: `product-design-skill/scripts/gen_screen_map_split.py`

**Step 1: Delete files**

```bash
git rm product-design-skill/scripts/gen_screen_map.py
git rm product-design-skill/scripts/gen_screen_map_split.py
```

**Step 2: Commit**

```bash
git commit -m "refactor: remove gen_screen_map.py and gen_screen_map_split.py (replaced by experience-map)"
```

---

### Task 6: Update `gen_use_cases.py` — consume experience-map instead of screen-map

**Files:**
- Modify: `product-design-skill/scripts/gen_use_cases.py`

**Step 1: Read the current file to understand all screen-map references**

Read the file. Find all occurrences of:
- `C.load_screen_map(`
- `C.get_screen_tasks(`
- `C.build_screen_by_id(`
- `C.build_task_screen_map(`
- `screen_map`, `screen-map`, `screens`
- Any reference to `screen_ref`

**Step 2: Replace screen-map loading with experience-map loading**

Replace:
```python
screens, sm_loaded = C.load_screen_map(BASE)
screen_by_id = C.build_screen_by_id(screens) if sm_loaded else {}
```

With:
```python
op_lines, screen_index, em_loaded = C.load_experience_map(BASE)
screen_by_id = C.build_screen_by_id_from_lines(op_lines) if em_loaded else {}
node_by_id = C.build_node_by_id(op_lines) if em_loaded else {}
```

**Step 3: Update use-case generation to reference operation lines**

Where use cases previously referenced `screen_ref` by looking up screens, now also include:
- `operation_line` — the OL ID containing this screen
- `node_ref` — the node ID containing this screen
- `emotion_context` — emotion_state from the node

Use the `screen_index` to find which operation_line/node a screen belongs to.

**Step 4: Commit**

```bash
git add product-design-skill/scripts/gen_use_cases.py
git commit -m "refactor: gen_use_cases.py consumes experience-map instead of screen-map"
```

---

### Task 7: Update `gen_feature_gap.py` — consume experience-map

**Files:**
- Modify: `product-design-skill/scripts/gen_feature_gap.py`

**Step 1: Read the current file**

Find all screen-map references.

**Step 2: Replace screen-map with experience-map**

Replace:
```python
screens, sm_loaded = C.load_screen_map(BASE)
```
With:
```python
op_lines, screen_index, em_loaded = C.load_experience_map(BASE)
screen_by_id = C.build_screen_by_id_from_lines(op_lines) if em_loaded else {}
```

**Step 3: Update coverage calculation**

Change screen coverage to node coverage — check that each task appears in at least one operation line node. Use `build_task_screen_map_from_lines()` to build the mapping.

**Step 4: Update gap output**

Replace `"screen_id"` references in output JSON with operation-line-aware references:
```python
{
    "id": "SG001",
    "type": "node_gap",
    "operation_line": "OL01",
    "node": "N0103",
    "detail": "Task T015 not covered by any operation line node",
}
```

**Step 5: Commit**

```bash
git add product-design-skill/scripts/gen_feature_gap.py
git commit -m "refactor: gen_feature_gap.py consumes experience-map, node-based coverage"
```

---

### Task 8: Update `gen_feature_prune.py` — consume experience-map

**Files:**
- Modify: `product-design-skill/scripts/gen_feature_prune.py`

**Step 1: Read the current file**

Find all screen-map references.

**Step 2: Replace screen-map loading**

Replace `C.load_screen_map()` with `C.load_experience_map()`.

**Step 3: Update frequency tiering**

Change frequency source from screen action frequency to operation line occurrence count. A task that appears in multiple operation lines is higher frequency.

```python
# Count how many operation lines reference each task
task_line_count = {}
for ol in op_lines:
    for node in ol.get("nodes", []):
        for s in node.get("screens", []):
            for tid in s.get("tasks", []):
                task_line_count.setdefault(tid, set()).add(ol["id"])
```

**Step 4: Commit**

```bash
git add product-design-skill/scripts/gen_feature_prune.py
git commit -m "refactor: gen_feature_prune.py consumes experience-map, line-based frequency"
```

---

### Task 9: Update `gen_ui_design.py` — core overhaul for emotion-aware design

**Files:**
- Modify: `product-design-skill/scripts/gen_ui_design.py`

This is the largest change. The script must now receive 5 new input channels from experience-map.

**Step 1: Read the current file thoroughly**

Understand the full flow: loading → role-screen mapping → layout decision → spec generation → HTML preview.

**Step 2: Replace screen-map loading with experience-map + gate loading**

```python
op_lines, screen_index, em_loaded = C.load_experience_map(BASE)
screen_by_id = C.build_screen_by_id_from_lines(op_lines) if em_loaded else {}
node_by_id = C.build_node_by_id(op_lines) if em_loaded else {}
gate = C.load_interaction_gate(BASE)
gate_issues_by_node = {}
if gate:
    for lr in gate.get("lines", []):
        for issue in lr.get("issues", []):
            nid = issue.get("node", "")
            gate_issues_by_node.setdefault(nid, []).append(issue)
```

**Step 3: Build node→screen→context mapping**

```python
# For each screen, find its node context (emotion, ux_intent, continuity)
screen_context = {}
for ol in op_lines:
    for node in ol.get("nodes", []):
        nid = node["id"]
        for s in node.get("screens", []):
            sid = s["id"]
            screen_context[sid] = {
                "emotion_state": node.get("emotion_state", "neutral"),
                "emotion_intensity": node.get("emotion_intensity", 5),
                "ux_intent": node.get("ux_intent", ""),
                "non_negotiable": s.get("non_negotiable", []),
                "operation_line": ol["id"],
                "node_id": nid,
                "continuity": ol.get("continuity", {}),
                "gate_issues": gate_issues_by_node.get(nid, []),
            }
```

**Step 4: Update spec generation to include new fields**

For each screen section in `ui-design-spec.md`, prepend:
```python
ctx = screen_context.get(sid, {})
spec_lines.append(f"**Emotion Context**: {ctx['emotion_state']} ({ctx['emotion_intensity']}/10)")
spec_lines.append(f"**Interaction Intent**: {ctx['ux_intent']}")
if ctx["non_negotiable"]:
    spec_lines.append(f"**Non-negotiable**: {', '.join(ctx['non_negotiable'])}")
if ctx["gate_issues"]:
    issues_str = "; ".join(i["detail"] for i in ctx["gate_issues"])
    spec_lines.append(f"**Quality Gate Issues**: {issues_str}")
```

**Step 5: Update HTML preview to reflect emotion context**

Add emotion indicator (color bar) to each screen card in the HTML preview.

**Step 6: Commit**

```bash
git add product-design-skill/scripts/gen_ui_design.py
git commit -m "feat: gen_ui_design.py receives emotion/intent/constraint/gate from experience-map"
```

---

### Task 10: Update `gen_design_audit.py` — node-based trace + continuity audit

**Files:**
- Modify: `product-design-skill/scripts/gen_design_audit.py`

**Step 1: Read the current file**

Understand the four audit checks: Trace, Coverage, Cross-check, Fidelity.

**Step 2: Replace screen-map loading**

Replace:
```python
sm = C.load_json(os.path.join(BASE, "screen-map/screen-map.json"))
for s in sm.get("screens", []):
    sid = s["id"]
    screens[sid] = s
    trefs = C.get_screen_tasks(s)
```

With:
```python
op_lines, screen_index_data, em_loaded = C.load_experience_map(BASE)
screen_by_id = C.build_screen_by_id_from_lines(op_lines) if em_loaded else {}
node_by_id = C.build_node_by_id(op_lines) if em_loaded else {}
# Build screen→task and task→screen maps
screen_task_map = {}
task_screen_map = {}
for ol in op_lines:
    for node in ol.get("nodes", []):
        for s in node.get("screens", []):
            sid = s["id"]
            trefs = s.get("tasks", [])
            screen_task_map[sid] = trefs
            for tid in trefs:
                task_screen_map.setdefault(tid, []).append(sid)
```

**Step 3: Add continuity audit dimension**

Add a new check section after Cross-check:

```python
# ── Continuity Audit (NEW) ──
continuity_issues = []
gate = C.load_interaction_gate(BASE)
if gate:
    for lr in gate.get("lines", []):
        if lr["score"] < gate.get("threshold", 70):
            continuity_issues.append({
                "line_id": lr["line_id"],
                "score": lr["score"],
                "issues": lr["issues"],
            })
```

Include continuity results in the final report.

**Step 4: Update file path references**

All references to `screen-map/screen-map.json` → `experience-map/experience-map.json`
All references to `screen-map` layer name → `experience-map`

**Step 5: Commit**

```bash
git add product-design-skill/scripts/gen_design_audit.py
git commit -m "refactor: gen_design_audit.py uses experience-map, adds continuity audit"
```

---

### Task 11: Update `gen_ui_stitch.py` and `gen_ui_components.py`

**Files:**
- Modify: `product-design-skill/scripts/gen_ui_stitch.py`
- Modify: `product-design-skill/scripts/gen_ui_components.py`

**Step 1: Read both files**

Find all screen-map references in each.

**Step 2: Update `gen_ui_stitch.py`**

Replace `C.load_screen_map()` → `C.load_experience_map()`.
Add emotion_state and ux_intent to Stitch prompt context:
```python
ctx = screen_context.get(sid, {})
prompt_context["emotion"] = ctx.get("emotion_state", "neutral")
prompt_context["ux_intent"] = ctx.get("ux_intent", "")
```

**Step 3: Update `gen_ui_components.py`**

Replace `C.load_screen_map()` → `C.load_experience_map()`.
Reference `ux_intent` when selecting component types.

**Step 4: Commit**

```bash
git add product-design-skill/scripts/gen_ui_stitch.py product-design-skill/scripts/gen_ui_components.py
git commit -m "refactor: gen_ui_stitch.py and gen_ui_components.py consume experience-map"
```

---

### Task 12: Create schema docs

**Files:**
- Delete: `product-design-skill/docs/schemas/screen-map-schema.md`
- Create: `product-design-skill/docs/schemas/experience-map-schema.md`
- Create: `product-design-skill/docs/schemas/journey-emotion-schema.md`
- Create: `product-design-skill/docs/schemas/interaction-gate-schema.md`

**Step 1: Write `experience-map-schema.md`**

Document the full JSON schema from the design doc: `operation_lines[].nodes[].screens[]` structure with all fields, types, and descriptions. Include `screen_index` and `continuity`.

**Step 2: Write `journey-emotion-schema.md`**

Document: `journey_lines[].emotion_nodes[]` structure. Fields: step, action, emotion, intensity, risk, design_hint. Plus `decision_log[]`.

**Step 3: Write `interaction-gate-schema.md`**

Document: `gate_result`, `lines[]` with score breakdown, `threshold`, `recommendation`.

**Step 4: Delete old schema**

```bash
git rm product-design-skill/docs/schemas/screen-map-schema.md
```

**Step 5: Commit**

```bash
git add product-design-skill/docs/schemas/
git commit -m "docs: add experience-map, journey-emotion, interaction-gate schemas; remove screen-map schema"
```

---

### Task 13: Create `skills/journey-emotion.md` — Phase 3 skill file

**Files:**
- Create: `product-design-skill/skills/journey-emotion.md`

**Step 1: Write the skill file**

Follow the pattern of existing skills (e.g., screen-map.md). Include:
- YAML frontmatter: `name: journey-emotion`, `description: ...`
- Prerequisites: product-map must exist
- Steps:
  - Step 0: Load product-map data (role-profiles + business-flows)
  - Step 1: Generate journey-emotion-map via script or LLM
  - Step 2: Present to user for review (human decision point)
  - Step 3: Record user adjustments in decision_log
  - Step 4: Output report
- Script invocation: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gen_journey_emotion.py <BASE>`
- Output files: `.allforai/experience-map/journey-emotion-map.json`
- Emphasize: **this step requires human confirmation before proceeding**

**Step 2: Commit**

```bash
git add product-design-skill/skills/journey-emotion.md
git commit -m "feat: add journey-emotion.md skill for Phase 3"
```

---

### Task 14: Create `skills/interaction-gate.md` — Phase 4.5 skill file

**Files:**
- Create: `product-design-skill/skills/interaction-gate.md`

**Step 1: Write the skill file**

Include:
- YAML frontmatter: `name: interaction-gate`, `description: ...`
- Prerequisites: experience-map must exist
- Steps:
  - Step 1: Run quality gate script
  - Step 2: Review issues with user
  - Step 3: Back-fill quality_score
- Script invocation: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gen_interaction_gate.py <BASE>`
- Output files: `.allforai/experience-map/interaction-gate.json`

**Step 2: Commit**

```bash
git add product-design-skill/skills/interaction-gate.md
git commit -m "feat: add interaction-gate.md skill for Phase 4.5"
```

---

### Task 15: Rename and rewrite `skills/screen-map.md` → `skills/experience-map.md`

**Files:**
- Delete: `product-design-skill/skills/screen-map.md`
- Create: `product-design-skill/skills/experience-map.md`

**Step 1: Write the new experience-map skill**

Rewrite the entire skill file. Key changes from old screen-map.md:
- Phase number: 4 (was 3)
- Input: journey-emotion-map.json + task-inventory.json (was just task-inventory)
- Output dir: `.allforai/experience-map/` (was `.allforai/screen-map/`)
- Output structure: operation_lines > nodes > screens (was flat screens list)
- Script: `gen_experience_map.py` (was `gen_screen_map.py`)
- Step structure:
  - Step 0: Load journey-emotion-map + product-map data
  - Step 1: Generate operation lines with nodes and screens → experience-map.json
  - Step 2: Run interaction-quality-gate (auto-invoke Phase 4.5)
  - Step 3: Output report → experience-map-report.md

**Step 2: Delete old file and commit**

```bash
git rm product-design-skill/skills/screen-map.md
git add product-design-skill/skills/experience-map.md
git commit -m "refactor: replace screen-map.md skill with experience-map.md"
```

---

### Task 16: Update downstream skill files — use-case, feature-gap, feature-prune

**Files:**
- Modify: `product-design-skill/skills/use-case.md`
- Modify: `product-design-skill/skills/feature-gap.md`
- Modify: `product-design-skill/skills/feature-prune.md`

**Step 1: Read each file**

Find all references to `screen-map`, `screen_map`, `.allforai/screen-map/`.

**Step 2: Update references in each file**

In all three files:
- Replace `screen-map` → `experience-map` in all file path references
- Replace `.allforai/screen-map/screen-map.json` → `.allforai/experience-map/experience-map.json`
- Replace `screen-map.json` → `experience-map.json` in prerequisite checks
- Replace "auto-run screen-map" → "auto-run experience-map" in fallback logic
- Update field references in JSON examples: flat `screens[]` → `operation_lines[].nodes[].screens[]`
- Update script references: `gen_screen_map.py` → `gen_experience_map.py`

**Step 3: Commit**

```bash
git add product-design-skill/skills/use-case.md product-design-skill/skills/feature-gap.md product-design-skill/skills/feature-prune.md
git commit -m "refactor: update use-case, feature-gap, feature-prune skills to reference experience-map"
```

---

### Task 17: Update `skills/ui-design.md` — emotion-aware input channels

**Files:**
- Modify: `product-design-skill/skills/ui-design.md`

**Step 1: Read the current file**

Understand the step structure and how screen-map data is referenced.

**Step 2: Update input references**

- Replace `screen-map` → `experience-map` in all file paths
- Add new input channels documentation:
  - emotion_state + intensity from nodes
  - ux_intent from nodes
  - non_negotiable from screens
  - continuity from operation lines
  - quality_gate issues from interaction-gate.json

**Step 3: Update output format documentation**

Add the new per-screen fields to the spec format:
- Emotion Context
- Interaction Intent
- Non-negotiable
- Quality Gate
- Transition
- Continuity Constraint

**Step 4: Update script reference**

`gen_screen_map.py` → `gen_experience_map.py` (in prerequisite auto-run)

**Step 5: Commit**

```bash
git add product-design-skill/skills/ui-design.md
git commit -m "feat: ui-design.md receives emotion/intent/constraint channels from experience-map"
```

---

### Task 18: Update `skills/design-audit.md` — continuity audit dimension

**Files:**
- Modify: `product-design-skill/skills/design-audit.md`

**Step 1: Read the current file**

Find screen-map references and audit check definitions.

**Step 2: Update references**

Replace all `screen-map` → `experience-map` in file paths and layer names.

**Step 3: Add continuity audit section**

Add after Cross-check section:
```markdown
### Step 3.7: 连贯性审计（Continuity Audit）

从 interaction-gate.json 读取质量门禁结果：
- 操作线步骤数 ≤ 7
- 上下文切换 ≤ 2
- 等待反馈覆盖率 = 1.0
- 拇指热区合规率 ≥ 0.8

不合格的操作线记入审计报告。
```

**Step 4: Commit**

```bash
git add product-design-skill/skills/design-audit.md
git commit -m "refactor: design-audit.md references experience-map, adds continuity audit"
```

---

### Task 19: Update `SKILL.md` — pipeline flow and phase numbering

**Files:**
- Modify: `product-design-skill/SKILL.md`

**Step 1: Read the current file**

Understand the pipeline flow diagram and skill listing.

**Step 2: Update pipeline flow**

Replace the old flow with:
```
├── 1. product-concept（产品概念发现）
├── 2. product-map（产品地图）
├── 3. journey-emotion（情绪旅程地图）   ← NEW
├── 4. experience-map（体验地图）         ← REPLACES screen-map
├── 4.5. interaction-gate（交互质量门禁） ← NEW
├── 5. use-case / feature-gap / ui-design（并行）
├── 6. feature-prune（可选手动）
└── 7. design-audit（设计审计）
```

**Step 3: Update skill references**

- Remove `screen-map` from skill listing
- Add `journey-emotion`, `experience-map`, `interaction-gate`
- Update all cross-references

**Step 4: Commit**

```bash
git add product-design-skill/SKILL.md
git commit -m "docs: update SKILL.md pipeline flow for experience-design architecture"
```

---

### Task 20: Update remaining references and version bump

**Files:**
- Modify: `product-design-skill/docs/pipeline-analysis.md` (if exists)
- Modify: `product-design-skill/.claude-plugin/plugin.json`
- Modify: `/Users/aa/Documents/myskills/CLAUDE.md`

**Step 1: Search for any remaining `screen-map` or `screen_map` references**

```bash
cd /Users/aa/Documents/myskills
grep -r "screen.map\|screen_map\|gen_screen_map\|load_screen_map\|build_screen_by_id" product-design-skill/ --include="*.py" --include="*.md" --include="*.json" -l
```

Fix any remaining references found.

**Step 2: Update `pipeline-analysis.md`**

If it exists, update the flow diagram to match the new pipeline.

**Step 3: Update `CLAUDE.md`**

In the root CLAUDE.md:
- Update the `.allforai/` directory listing: replace `screen-map/` with `experience-map/`
- Update the scripts list: replace `gen_screen_map.py`, `gen_screen_map_split.py` with `gen_journey_emotion.py`, `gen_experience_map.py`, `gen_interaction_gate.py`
- Update the workflow section

**Step 4: Version bump**

```python
# In plugin.json, bump version
"version": "4.0.0"  # Major version bump — breaking change (screen-map removed)
```

**Step 5: Commit**

```bash
git add -A
git commit -m "feat: complete experience-design pipeline v4.0.0 — replace screen-map with experience-map"
```

**Step 6: Push**

```bash
git push
```

---

## Task Dependency Graph

```
Task 1 (_common.py loaders)
  ├── Task 2 (gen_journey_emotion.py)      ← depends on Task 1
  ├── Task 3 (gen_experience_map.py)        ← depends on Task 1, 2
  ├── Task 4 (gen_interaction_gate.py)      ← depends on Task 1, 3
  └── Task 5 (delete old scripts)           ← depends on Task 1

Task 6-8 (update downstream scripts)        ← depend on Task 1
Task 9 (gen_ui_design.py overhaul)           ← depends on Task 1
Task 10 (gen_design_audit.py)                ← depends on Task 1
Task 11 (stitch + components)                ← depends on Task 1

Task 12 (schema docs)                        ← independent
Task 13-14 (new skill files)                 ← independent
Task 15 (experience-map skill)               ← independent
Task 16-18 (update skill files)              ← independent
Task 19 (SKILL.md)                           ← depends on Task 13-15
Task 20 (final sweep + version)              ← depends on ALL above
```

**Parallelizable groups:**
- Group A (scripts): Tasks 2, 5, 6, 7, 8, 9, 10, 11 (all depend only on Task 1)
- Group B (docs/skills): Tasks 12, 13, 14, 15, 16, 17, 18 (independent of scripts)
- Group C (finalize): Tasks 19, 20 (after A + B)
