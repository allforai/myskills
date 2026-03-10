# Skeleton generator — LLM enrichment required after running
#!/usr/bin/env python3
"""Generate design pattern catalog skeleton: list screens and interaction types.

Skeleton for Phase 3.5 (design-pattern). Outputs raw screen and task data
without keyword-based pattern detection. LLM enrichment is required to
classify screens into pattern types (PT-CRUD, PT-LIST-DETAIL, etc.).

Usage:
    python3 gen_design_pattern.py <BASE_PATH> [--mode auto] [--shard design-pattern]
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C

# ── Setup ─────────────────────────────────────────────────────────────────────
BASE, args = C.parse_args()
OUT = os.path.join(BASE, "design-pattern")
C.ensure_dir(OUT)
NOW = C.now_iso()

# ── Load data ─────────────────────────────────────────────────────────────────
tasks = C.load_task_inventory(BASE)
op_lines, screen_index, em_loaded = C.load_experience_map(BASE)
flows = C.load_business_flows(BASE)

screen_by_id = C.build_screen_by_id_from_lines(op_lines)
task_screen_map = C.build_task_screen_map_from_lines(op_lines)
screens = list(screen_by_id.values())

# ── Pattern type definitions (for reference in output) ────────────────────────

ALL_PATTERN_TYPES = [
    {"pattern_id": "PT-CRUD", "name": "CRUD 管理台", "description": "实体的增删改查管理"},
    {"pattern_id": "PT-LIST-DETAIL", "name": "列表+详情对", "description": "列表界面与详情界面成对出现"},
    {"pattern_id": "PT-APPROVAL", "name": "审批流", "description": "提交→审核→批准/驳回流程"},
    {"pattern_id": "PT-SEARCH", "name": "搜索+筛选+分页", "description": "搜索、筛选、分页组合"},
    {"pattern_id": "PT-EXPORT", "name": "导出/报表", "description": "数据导出和报表生成"},
    {"pattern_id": "PT-NOTIFY", "name": "通知触发", "description": "系统通知和消息推送"},
    {"pattern_id": "PT-PERMISSION", "name": "权限矩阵", "description": "角色权限差异化控制"},
    {"pattern_id": "PT-STATE", "name": "状态机", "description": "实体状态流转管理"},
]

# ── Collect raw screen data ───────────────────────────────────────────────────

screen_inventory = []
for s in screens:
    actions = s.get("actions", [])
    screen_inventory.append({
        "id": s["id"],
        "name": s.get("name", ""),
        "module": s.get("module", ""),
        "interaction_type": s.get("interaction_type", ""),
        "task_refs": s.get("tasks", []),
        "actions": [
            {"label": a.get("label", ""), "crud": a.get("crud", ""), "frequency": a.get("frequency", "")}
            for a in actions
        ],
        "data_fields_count": len(s.get("data_fields", [])),
        "states": list(s.get("states", {}).keys()) if isinstance(s.get("states"), dict) else [],
    })

# ── Collect raw task data ─────────────────────────────────────────────────────

task_inventory = []
for tid, task in tasks.items():
    task_inventory.append({
        "id": tid,
        "task_name": task.get("task_name", ""),
        "category": task.get("category", ""),
        "owner_role": task.get("owner_role", ""),
        "screen_ids": task_screen_map.get(tid, []),
    })

# ── Collect raw flow data ─────────────────────────────────────────────────────

flow_inventory = []
for flow in flows:
    nodes = C.get_flow_nodes(flow)
    node_summaries = []
    for n in nodes:
        if isinstance(n, str):
            node_summaries.append({"task_ref": n, "label": tasks.get(n, {}).get("task_name", n)})
        elif isinstance(n, dict):
            node_summaries.append({
                "task_ref": n.get("task_ref", ""),
                "label": n.get("label", ""),
                "type": n.get("type", ""),
            })
    flow_inventory.append({
        "id": flow.get("id", ""),
        "name": flow.get("name", ""),
        "node_count": len(nodes),
        "nodes": node_summaries,
    })

# ═════════════════════════════════════════════════════════════════════════════
# Output
# ═════════════════════════════════════════════════════════════════════════════

catalog = {
    "created_at": NOW,
    "pattern_types": ALL_PATTERN_TYPES,
    "screen_inventory": screen_inventory,
    "task_inventory": task_inventory,
    "flow_inventory": flow_inventory,
    "total_screens": len(screen_inventory),
    "total_tasks": len(task_inventory),
    "total_flows": len(flow_inventory),
    "llm_enrichment_required": True,
}
C.write_json(os.path.join(OUT, "pattern-catalog.json"), catalog)

# ── pattern-report.md ─────────────────────────────────────────────────────────
lines = []
lines.append("# Phase 3.5 — 设计模式分析报告（骨架）\n")
lines.append("> LLM enrichment required: pattern detection pending\n")
lines.append("## 概览\n")
lines.append("| 指标 | 值 |")
lines.append("|------|-----|")
lines.append(f"| Screens | {len(screen_inventory)} 个 |")
lines.append(f"| Tasks | {len(task_inventory)} 个 |")
lines.append(f"| Flows | {len(flow_inventory)} 个 |")
lines.append(f"| 模式类型（待检测） | {len(ALL_PATTERN_TYPES)} 种 |\n")

lines.append("## 可检测模式类型\n")
for pt in ALL_PATTERN_TYPES:
    lines.append(f"- **{pt['pattern_id']}**: {pt['name']} — {pt['description']}")

lines.append("\n## Screen 概览\n")
lines.append("| Screen | Module | Interaction Type | Actions | Tasks |")
lines.append("|--------|--------|-----------------|---------|-------|")
for s in screen_inventory[:30]:
    action_labels = ", ".join(a["label"] for a in s["actions"][:3])
    if len(s["actions"]) > 3:
        action_labels += "..."
    task_refs = ", ".join(s["task_refs"][:3])
    if len(s["task_refs"]) > 3:
        task_refs += "..."
    lines.append(f"| {s['name']} | {s['module']} | {s['interaction_type']} | {action_labels} | {task_refs} |")
if len(screen_inventory) > 30:
    lines.append(f"\n*... and {len(screen_inventory) - 30} more screens*")

with open(os.path.join(OUT, "pattern-report.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

# ── Pipeline decisions ────────────────────────────────────────────────────────
C.append_pipeline_decision(
    BASE,
    "Phase 3.5 — design-pattern",
    f"{len(screen_inventory)} screens, {len(task_inventory)} tasks, "
    f"{len(flow_inventory)} flows inventoried, "
    f"pending LLM enrichment for pattern detection",
    shard=args.get("shard"),
)

# ── Summary ───────────────────────────────────────────────────────────────────
print(f"Screens: {len(screen_inventory)}")
print(f"Tasks: {len(task_inventory)}")
print(f"Flows: {len(flow_inventory)}")
print(f"Pattern types available: {len(ALL_PATTERN_TYPES)}")
print(f"Status: skeleton generated, LLM enrichment required")
print(f"\nAll files written to {OUT}/")
