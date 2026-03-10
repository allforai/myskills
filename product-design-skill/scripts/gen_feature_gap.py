#!/usr/bin/env python3
# Skeleton generator — LLM enrichment required after running
"""Generate feature-gap analysis: task-gaps, screen-gaps, journey-gaps,
flow-gaps, gap-tasks, gap-report, and decisions.

Skeleton generator: structural checks only (missing fields, empty states,
orphan references). No keyword-based error state detection or gap classification.

Usage:
    python3 gen_feature_gap.py <BASE_PATH> [--mode auto] [--shard <name>]
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C

# ── Setup ─────────────────────────────────────────────────────────────────────
BASE, args = C.parse_args()
OUT = os.path.join(BASE, "feature-gap")
C.ensure_dir(OUT)
NOW = C.now_iso()

# ── Load data ─────────────────────────────────────────────────────────────────
tasks = C.load_task_inventory(BASE)
ctx = C.load_full_context(BASE)
role_map = C.load_role_profiles(BASE)

op_lines, screen_index, em_loaded = C.load_experience_map(BASE)
screens_by_id = C.build_screen_by_id_from_lines(op_lines)
screens = list(screens_by_id.values())

flows = C.load_business_flows(BASE)

# ── Step 1: Task completeness check ──────────────────────────────────────────
task_gaps = []
for tid, task in tasks.items():
    gaps = []
    details = {
        "exceptions_count": len(task.get("exceptions", [])),
        "acceptance_criteria_count": len(task.get("acceptance_criteria", [])),
        "rules_count": len(task.get("rules", [])),
    }

    if not task.get("exceptions"):
        gaps.append("NO_EXCEPTIONS")
    if not task.get("rules"):
        gaps.append("NO_RULES")
    if not task.get("acceptance_criteria"):
        gaps.append("NO_ACCEPTANCE_CRITERIA")
    if not task.get("main_flow"):
        gaps.append("NO_MAIN_FLOW")

    task_gaps.append({
        "task_id": tid,
        "name": task["task_name"],
        "frequency": task.get("frequency", "低"),
        "category": task.get("category", ""),
        "gaps": gaps if gaps else ["COMPLETE"],
        "details": details
    })

# ── Prevalence filter: flags on >80% of tasks → SCHEMA_INCOMPLETE ────────────
_schema_flags = {"NO_EXCEPTIONS", "NO_RULES", "NO_ACCEPTANCE_CRITERIA"}
_total = len(task_gaps)
if _total > 0:
    _counts = {}
    for tg in task_gaps:
        for g in tg["gaps"]:
            if g in _schema_flags:
                _counts[g] = _counts.get(g, 0) + 1
    _demoted = {f for f, c in _counts.items() if c / _total > 0.80}
    for flag in _demoted:
        print(f"  INFO: {flag} on {_counts[flag]}/{_total} tasks — reclassified as SCHEMA_INCOMPLETE")
    if _demoted:
        for tg in task_gaps:
            kept = [g for g in tg["gaps"] if g not in _demoted]
            removed = [g for g in tg["gaps"] if g in _demoted]
            if removed:
                tg["schema_incomplete"] = removed
            tg["gaps"] = kept if kept else ["COMPLETE"]
        C.write_json(os.path.join(OUT, "schema-summary.json"), {
            "generated_at": NOW, "total_tasks": _total,
            "demoted_flags": {f: _counts[f] for f in _demoted},
            "threshold": 0.80
        })

C.write_json(os.path.join(OUT, "task-gaps.json"), task_gaps)

# ── Step 2: Screen structural check ─────────────────────────────────────────
screen_gaps = []
task_screen_map = C.build_task_screen_map_from_lines(op_lines)

# Tasks without screens
for tid in tasks:
    if tid not in task_screen_map:
        screen_gaps.append({
            "id": "N/A",
            "screen_name": f"(任务 {tid} 无对应界面)",
            "gaps": ["NO_SCREEN"],
            "details": [{
                "flag": "NO_SCREEN",
                "description": f"任务 {tid} ({tasks[tid]['task_name']}) 在 experience-map 中无对应界面",
                "affected_tasks": [tid],
                "severity": "高" if tasks[tid].get("frequency") == "高" else "中"
            }]
        })

for s in screens:
    gaps = []
    details_list = []
    actions = s.get("actions", [])
    trefs = s.get("tasks", [])

    # Check if states are defined
    states = s.get("states", [])
    if not states:
        gaps.append("NO_STATES_DEFINED")
        details_list.append({
            "flag": "NO_STATES_DEFINED",
            "description": f"界面 {s['id']} ({s.get('name', '')}) 无 states 定义",
            "affected_tasks": trefs,
            "severity": "中"
        })

    # Orphan screens
    if not trefs:
        gaps.append("ORPHAN_SCREEN")
        details_list.append({
            "flag": "ORPHAN_SCREEN",
            "description": f"界面 {s['id']} ({s.get('name', '')}) 无关联任务",
            "affected_tasks": [],
            "severity": "低"
        })

    # No actions defined
    if not actions:
        gaps.append("NO_ACTIONS")
        details_list.append({
            "flag": "NO_ACTIONS",
            "description": f"界面 {s['id']} ({s.get('name', '')}) 无 actions 定义",
            "affected_tasks": trefs,
            "severity": "中"
        })

    if gaps:
        seen = set()
        unique_gaps = [g for g in gaps if g not in seen and not seen.add(g)]
        entry = {
            "id": s["id"],
            "screen_name": s.get("name", ""),
            "gaps": unique_gaps,
            "details": details_list
        }
        si_entry = screen_index.get(s["id"])
        if si_entry:
            entry["operation_line"] = si_entry.get("line", "")
            entry["node_id"] = si_entry.get("node", "")
        screen_gaps.append(entry)

C.write_json(os.path.join(OUT, "screen-gaps.json"), screen_gaps)

# ── Step 3: User journey validation ──────────────────────────────────────────
journey_gaps = []
for tid, task in tasks.items():
    rid = task.get("owner_role", "")
    rname = role_map.get(rid, rid)
    score = 4
    breakpoints = []

    has_screen = tid in task_screen_map
    if not has_screen:
        score -= 1
        breakpoints.append({"node": "入口存在", "issue": f"任务 {tid} 无对应界面", "affected_screen": "N/A"})

    if has_screen:
        sids = task_screen_map[tid]
        has_actions = any(screens_by_id.get(sid, {}).get("actions") for sid in sids)
        if not has_actions:
            score -= 1
            breakpoints.append({"node": "操作可触达", "issue": "界面无 actions 定义",
                                "affected_screen": sids[0] if sids else "N/A"})

    if not task.get("outputs") and not task.get("main_flow"):
        score -= 1
        breakpoints.append({"node": "结果可见", "issue": "任务无 outputs 定义", "affected_screen": "N/A"})

    if not task.get("main_flow"):
        score -= 1
        breakpoints.append({"node": "流程完整", "issue": "任务无 main_flow 定义", "affected_screen": "N/A"})

    if breakpoints:
        journey_gaps.append({
            "role": rname, "task_id": tid, "name": task["task_name"],
            "score": f"{score}/4", "breakpoints": breakpoints
        })

C.write_json(os.path.join(OUT, "journey-gaps.json"), journey_gaps)

# ── Step 5: Business flow link completeness ──────────────────────────────────
flow_gaps = []
flow_task_refs = C.collect_flow_task_refs(flows)

orphan_tasks = [tid for tid in tasks if tid not in flow_task_refs]
if orphan_tasks:
    flow_gaps.append({
        "flow_id": "GLOBAL", "flow_name": "全局孤立任务检查",
        "gap_type": "ORPHAN_TASK",
        "description": f"{len(orphan_tasks)} 个任务未被任何业务流引用",
        "affected_tasks": orphan_tasks, "severity": "低"
    })

for flow in flows:
    if flow.get("gap_count", 0) > 0:
        flow_gaps.append({
            "flow_id": flow.get("id") or flow.get("flow_id", ""),
            "flow_name": flow.get("name") or flow.get("flow_name", ""),
            "gap_type": "FLOW_GAP",
            "description": f"业务流含 {flow['gap_count']} 个缺口",
            "affected_tasks": [
                n.get("task_ref", "") if isinstance(n, dict) else n
                for n in C.get_flow_nodes(flow)
            ],
            "severity": "高"
        })

C.write_json(os.path.join(OUT, "flow-gaps.json"), flow_gaps)

# ── Step 4: Generate gap task list (prioritized) ─────────────────────────────
gap_counter = [0]
def next_gap():
    gap_counter[0] += 1
    return f"GAP-{gap_counter[0]:03d}"

gap_tasks_list = []

# From task gaps
for tg in task_gaps:
    if "COMPLETE" in tg["gaps"]:
        continue
    for gap in tg["gaps"]:
        tid = tg["task_id"]
        task = tasks[tid]
        freq = tg["frequency"]
        gap_tasks_list.append({
            "id": next_gap(),
            "title": f"{task['task_name']} — {gap}",
            "type": gap,
            "category": task.get("category", ""),
            "priority": "高" if freq == "高" else ("中" if freq == "中" else "低"),
            "affected_tasks": [tid],
            "affected_screens": task_screen_map.get(tid, []),
            "description": f"任务 {tid} ({task['task_name']}) 检测到 {gap}",
            "flags": ["SKELETON_NEEDS_LLM_ENRICHMENT"]
        })

# From screen gaps
for sg in screen_gaps:
    for detail in sg.get("details", []):
        gap_tasks_list.append({
            "id": next_gap(),
            "title": f"{sg['screen_name']} — {detail['flag']}",
            "type": detail["flag"],
            "priority": detail.get("severity", "中"),
            "affected_tasks": detail.get("affected_tasks", []),
            "affected_screens": [sg["id"]],
            "description": detail["description"],
            "flags": ["SKELETON_NEEDS_LLM_ENRICHMENT"]
        })

C.write_json(os.path.join(OUT, "gap-tasks.json"), gap_tasks_list)

# ── Statistics ────────────────────────────────────────────────────────────────
task_gap_count = sum(1 for tg in task_gaps if "COMPLETE" not in tg["gaps"])
screen_gap_count = len(screen_gaps)
journey_gap_count = len(journey_gaps)
flow_gap_count = len(flow_gaps)

flag_stats = {}
for tg in task_gaps:
    for g in tg["gaps"]:
        if g != "COMPLETE":
            flag_stats[g] = flag_stats.get(g, 0) + 1
for sg in screen_gaps:
    for g in sg["gaps"]:
        flag_stats[g] = flag_stats.get(g, 0) + 1

# ── Markdown report ──────────────────────────────────────────────────────────
lines = []
lines.append("# 功能缺口报告（骨架）\n")
lines.append("> **骨架输出** — 仅包含结构性检查，需 LLM 补充语义分析\n")
lines.append("## 摘要\n")
lines.append(f"- 任务缺口: {task_gap_count} 个")
lines.append(f"- 界面缺口: {screen_gap_count} 个")
lines.append(f"- 旅程缺口: {journey_gap_count} 个")
lines.append(f"- 业务流缺口: {flow_gap_count} 个\n")

lines.append("## Flag 统计\n")
lines.append("| Flag | 数量 |")
lines.append("|------|------|")
for flag, count in sorted(flag_stats.items(), key=lambda x: -x[1]):
    lines.append(f"| {flag} | {count} |")

lines.append("\n## 缺口任务清单\n")
lines.append("| 优先级 | ID | 任务 | 缺口类型 | 描述 |")
lines.append("|--------|----|------|---------|------|")
for g in gap_tasks_list[:50]:
    lines.append(f"| {g['priority']} | {g['id']} | {g['title']} | {g['type']} | {g['description'][:60]} |")

with open(os.path.join(OUT, "gap-report.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

# ── Decisions ─────────────────────────────────────────────────────────────────
decisions = [
    {"step": "Step 1", "item_id": "task_check", "item_name": f"{task_gap_count} 任务缺口",
     "decision": "auto_confirmed", "reason": "全自动模式 — 骨架生成", "decided_at": NOW},
    {"step": "Step 2", "item_id": "screen_check", "item_name": f"{screen_gap_count} 界面缺口",
     "decision": "auto_confirmed", "reason": "全自动模式 — 骨架生成", "decided_at": NOW},
    {"step": "Step 3", "item_id": "journey_check", "item_name": f"{journey_gap_count} 旅程缺口",
     "decision": "auto_confirmed", "reason": "全自动模式 — 骨架生成", "decided_at": NOW},
    {"step": "Step 4", "item_id": "gap_tasks", "item_name": f"{len(gap_tasks_list)} 缺口任务",
     "decision": "auto_confirmed", "reason": "全自动模式 — 骨架生成", "decided_at": NOW},
    {"step": "Step 5", "item_id": "flow_check", "item_name": f"{flow_gap_count} 业务流缺口",
     "decision": "auto_confirmed", "reason": "全自动模式 — 骨架生成", "decided_at": NOW},
]
C.write_json(os.path.join(OUT, "gap-decisions.json"), decisions)

# ── Pipeline decisions ────────────────────────────────────────────────────────
C.append_pipeline_decision(
    BASE,
    "Phase 5 — feature-gap",
    f"task_gaps={task_gap_count}, screen_gaps={screen_gap_count}, "
    f"journey_gaps={journey_gap_count}, flow_gaps={flow_gap_count}, "
    f"total_gap_tasks={len(gap_tasks_list)} (skeleton)",
    shard=args.get("shard")
)

# ── Summary ───────────────────────────────────────────────────────────────────
print(f"Task gaps: {task_gap_count} (of {len(tasks)} tasks)")
print(f"Screen gaps: {screen_gap_count}")
print(f"Journey gaps: {journey_gap_count}")
print(f"Flow gaps: {flow_gap_count}")
print(f"Gap tasks generated: {len(gap_tasks_list)}")
print(f"Flags: {dict(sorted(flag_stats.items(), key=lambda x: -x[1]))}")
print(f"\nAll files written to {OUT}/")
