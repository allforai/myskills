#!/usr/bin/env python3
"""Generate product-map Step 6 outputs: product-map.json, product-map-report.md,
task-index.json, flow-index.json, and product-map-visual.svg.

Aggregates confirmed data from Steps 1-5 into a consolidated product map,
generates lightweight indexes for downstream two-phase loading, and creates
a role-task tree SVG visualization.

Usage:
    python3 gen_product_map.py <BASE_PATH> [--mode auto] [--shard product-map]
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C

# ── Setup ─────────────────────────────────────────────────────────────────────
BASE, args = C.parse_args()
PM = os.path.join(BASE, "product-map")
C.ensure_dir(PM)
NOW = C.now_iso()

# ── Load inputs ───────────────────────────────────────────────────────────────
print("Loading inputs...")

roles_data = C.require_json(
    os.path.join(PM, "role-profiles.json"),
    "role-profiles.json"
)
roles = roles_data.get("roles", [])
print(f"  Roles: {len(roles)}")

inv_data = C.require_json(
    os.path.join(PM, "task-inventory.json"),
    "task-inventory.json"
)
tasks = inv_data.get("tasks", [])
tasks_by_id = {t["id"]: C._normalize_task(t) for t in tasks}
print(f"  Tasks: {len(tasks)}")

flows_data = C.load_json(os.path.join(PM, "business-flows.json"))
flows = flows_data.get("flows", []) if flows_data else []
print(f"  Flows: {len(flows)}")

conflict_data = C.load_json(os.path.join(PM, "conflict-report.json"))
conflicts = []
if conflict_data:
    conflicts = conflict_data.get("conflicts", []) + conflict_data.get("crud_gaps", [])
    print(f"  Conflicts: {len(conflicts)}")
else:
    print("  Conflicts: skipped (file not found)")

constraints_data = C.load_json(os.path.join(PM, "constraints.json"))
constraints = []
if constraints_data:
    constraints = constraints_data.get("constraints", [])
    print(f"  Constraints: {len(constraints)}")
else:
    print("  Constraints: skipped (file not found)")

# ── Compute summary statistics ────────────────────────────────────────────────
print("Computing summary...")

basic_count = sum(1 for t in tasks if t.get("category") == "basic")
core_count = sum(1 for t in tasks if t.get("category") == "core")
high_freq_count = sum(1 for t in tasks if t.get("frequency") == "高")
high_risk_count = sum(1 for t in tasks if t.get("risk_level") == "高")

# Flow gap count
flow_gap_total = sum(f.get("gap_count", 0) for f in flows)

# Orphan tasks (not referenced by any flow)
flow_task_refs = C.collect_flow_task_refs(flows)
orphan_tasks = [t["id"] for t in tasks if t["id"] not in flow_task_refs]

# Independent operations count
independent_count = 0
for f in flows:
    for node in C.get_flow_nodes(f):
        if isinstance(node, dict) and node.get("gap_type") == "INDEPENDENT_OPERATION":
            independent_count += 1

summary = {
    "role_count": len(roles),
    "task_count": len(tasks),
    "flow_count": len(flows),
    "flow_gaps": flow_gap_total,
    "orphan_task_count": len(orphan_tasks),
    "independent_operation_count": independent_count,
    "basic_count": basic_count,
    "core_count": core_count,
    "high_freq_count": high_freq_count,
    "high_risk_count": high_risk_count,
    "conflict_count": len(conflicts),
    "constraint_count": len(constraints),
    "validation_issues": 0,
    "competitor_gaps": 0,
}

# ── Write product-map.json ────────────────────────────────────────────────────
print("Writing product-map.json...")

product_map = {
    "generated_at": NOW,
    "version": "2.6.0",
    "scope": "full",
    "scale": "large" if len(tasks) > 80 else ("medium" if len(tasks) > 30 else "small"),
    "summary": summary,
    "roles": roles,
    "tasks": tasks,
    "conflicts": conflicts,
    "constraints": constraints,
}

C.write_json(os.path.join(PM, "product-map.json"), product_map)

# ── Write task-index.json ─────────────────────────────────────────────────────
print("Writing task-index.json...")


# ── Group tasks by module (LLM-assigned, no keyword heuristics) ──
module_map = {}  # module_name -> [task]
for t in tasks:
    mod = t.get("module", t.get("name", t.get("task_name", "unknown")))
    module_map.setdefault(mod, []).append(t)

# Build category summary
category_map = {}  # category -> [task_id]
for t in tasks:
    cat = t.get("category", "core")
    category_map.setdefault(cat, []).append(t["id"])

category_labels = {"basic": "基本功能", "core": "核心功能"}
categories = [
    {
        "name": cat,
        "label": category_labels.get(cat, cat),
        "task_ids": ids,
        "count": len(ids),
    }
    for cat, ids in sorted(category_map.items())
]

modules = []
for mod_name, mod_tasks in sorted(module_map.items()):
    modules.append({
        "name": mod_name,
        "task_ids": [t["id"] for t in mod_tasks],
        "tasks": [
            {
                "id": t["id"],
                "name": t.get("name", t.get("task_name", "")),
                "frequency": t.get("frequency", "低"),
                "owner_role": t.get("owner_role", ""),
                "risk_level": t.get("risk_level", "低"),
                "category": t.get("category", "core"),
            }
            for t in mod_tasks
        ],
    })

task_index = {
    "generated_at": NOW,
    "source": "task-inventory.json",
    "task_count": len(tasks),
    "categories": categories,
    "modules": modules,
}

C.write_json(os.path.join(PM, "task-index.json"), task_index)

# ── Write flow-index.json ─────────────────────────────────────────────────────
print("Writing flow-index.json...")

flow_index_items = []
for f in flows:
    nodes = C.get_flow_nodes(f)
    # Collect unique roles from nodes
    flow_roles = set()
    for node in nodes:
        if isinstance(node, dict):
            role_ref = node.get("role", node.get("owner_role", ""))
            if role_ref:
                flow_roles.add(role_ref)
            # Also check task_ref to resolve role
            tref = node.get("task_ref", "")
            if tref in tasks_by_id:
                owner = tasks_by_id[tref].get("owner_role", "")
                if owner:
                    flow_roles.add(owner)
    # Resolve role IDs to names
    role_name_map = {r["id"]: r["name"] for r in roles}
    resolved_roles = []
    for rid in sorted(flow_roles):
        resolved_roles.append(role_name_map.get(rid, rid))

    flow_index_items.append({
        "id": f.get("id", ""),
        "name": f.get("name", ""),
        "node_count": len(nodes),
        "gap_count": f.get("gap_count", 0),
        "roles": resolved_roles,
    })

flow_index = {
    "generated_at": NOW,
    "source": "business-flows.json",
    "flow_count": len(flows),
    "flows": flow_index_items,
}

C.write_json(os.path.join(PM, "flow-index.json"), flow_index)

# ── Write product-map-report.md ──────────────────────────────────────────────
print("Writing product-map-report.md...")

role_name_map = {r["id"]: r["name"] for r in roles}
lines = []
lines.append("# 产品地图摘要\n")
lines.append(
    f"角色 {len(roles)} 个 · 任务 {len(tasks)} 个 · "
    f"高频任务 {high_freq_count} 个 · "
    f"冲突 {len(conflicts)} 个 · 约束 {len(constraints)} 条\n"
)

# Role overview table
lines.append("## 角色总览\n")
lines.append("| 角色 | 职责 | KPI |")
lines.append("|------|------|-----|")
for r in roles:
    desc = r.get("description", "")[:60]
    kpi = ", ".join(r.get("kpi", [])[:3]) if r.get("kpi") else ""
    lines.append(f"| {r['name']} | {desc} | {kpi} |")

# Role -> task table
lines.append("\n## 角色-任务分布\n")
lines.append("| 角色 | 任务数 | 高频 | 高风险 |")
lines.append("|------|--------|------|--------|")
for r in roles:
    rid = r["id"]
    role_tasks = [t for t in tasks if t.get("owner_role") == rid]
    hf = sum(1 for t in role_tasks if t.get("frequency") == "高")
    hr = sum(1 for t in role_tasks if t.get("risk_level") == "高")
    lines.append(f"| {r['name']} | {len(role_tasks)} | {hf} | {hr} |")

# High-frequency tasks
high_freq_tasks = [t for t in tasks if t.get("frequency") == "高"]
if high_freq_tasks:
    lines.append("\n## 高频任务（Top 20%）\n")
    for t in high_freq_tasks:
        tid = t["id"]
        tname = t.get("name", t.get("task_name", ""))
        risk = t.get("risk_level", "低")
        cross = t.get("cross_dept", False)
        tags = [f"高频"]
        if risk == "高":
            tags.append("高风险")
        if cross:
            tags.append("跨部门")
        lines.append(f"- {tid} {tname}（{'/ '.join(tags)}）")

# Flow summary
if flows:
    lines.append("\n## 业务流摘要\n")
    lines.append("| 流 ID | 名称 | 节点数 | 缺口数 | 涉及角色 |")
    lines.append("|-------|------|--------|--------|----------|")
    for fi in flow_index_items:
        roles_str = ", ".join(fi["roles"]) if fi["roles"] else "-"
        lines.append(
            f"| {fi['id']} | {fi['name']} | {fi['node_count']} | "
            f"{fi['gap_count']} | {roles_str} |"
        )

# Conflict highlights
if conflicts:
    lines.append("\n## 冲突摘要\n")
    for c in conflicts:
        sev = c.get("severity", "中")
        lines.append(f"- {c.get('id', '')} {c.get('description', '')}（{sev}）")

# Constraint summary
if constraints:
    lines.append("\n## 业务约束摘要\n")
    for cn in constraints:
        enforcement = cn.get("enforcement", "")
        label = "硬约束" if enforcement == "hard" else "软约束"
        lines.append(f"- {cn.get('id', '')} {cn.get('description', '')}（{label}）")

# Next steps
lines.append("\n## 下一步建议\n")
lines.append("- 运行 /experience-map 梳理界面、按钮和异常状态（必须，下游技能缺失时会自动运行）")
lines.append("- 运行 /use-case 生成用例集（可选）")
lines.append("- 运行 /feature-gap 检测功能缺口")
lines.append("")
lines.append("> 完整数据见 .allforai/product-map/product-map.json")

with open(os.path.join(PM, "product-map-report.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

# ── Write product-map-visual.svg ──────────────────────────────────────────────
print("Writing product-map-visual.svg...")

# Color definitions per schema
COLOR_ROLE_BG = "#3B82F6"
COLOR_HIGH_FREQ = "#22C55E"
COLOR_MED_FREQ = "#F59E0B"
COLOR_LOW_FREQ = "#9CA3AF"
COLOR_RISK_BADGE = "#EF4444"
COLOR_CROSS_DEPT = "#8B5CF6"
COLOR_CONFLICT = "#F97316"
COLOR_LINE = "#CBD5E1"
COLOR_WHITE = "#FFFFFF"

# Layout constants
ROLE_BOX_W = 140
ROLE_BOX_H = 40
TASK_BOX_W = 220
TASK_BOX_H = 32
TASK_GAP_Y = 8
ROLE_GAP_Y = 30
LEFT_MARGIN = 40
ROLE_X = LEFT_MARGIN
TASK_X = ROLE_X + ROLE_BOX_W + 80
LEGEND_H = 60
TOP_MARGIN = LEGEND_H + 20

# Build tasks grouped by owner_role for layout
role_tasks_map = {}
for t in tasks:
    rid = t.get("owner_role", "unknown")
    role_tasks_map.setdefault(rid, []).append(t)

# Collect conflict task IDs for marking
conflict_task_ids = set()
for c in conflicts:
    for tid in c.get("affected_tasks", []):
        conflict_task_ids.add(tid)


def _escape_xml(s):
    """Escape special characters for SVG/XML."""
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;")
             .replace("'", "&apos;"))


def _truncate(s, max_len=18):
    """Truncate string for display in SVG boxes."""
    if len(s) > max_len:
        return s[:max_len - 1] + "…"
    return s


def _freq_color(freq):
    if freq == "高":
        return COLOR_HIGH_FREQ
    elif freq == "中":
        return COLOR_MED_FREQ
    return COLOR_LOW_FREQ


def _freq_label(freq):
    return {"高": "高频", "中": "中频"}.get(freq, "低频")


# Calculate canvas dimensions
y_cursor = TOP_MARGIN
role_positions = []  # (role, y_start, y_end, tasks_list)
for r in roles:
    rid = r["id"]
    rtasks = role_tasks_map.get(rid, [])
    if not rtasks:
        # Role with no tasks still gets a row
        role_positions.append((r, y_cursor, y_cursor + ROLE_BOX_H, []))
        y_cursor += ROLE_BOX_H + ROLE_GAP_Y
    else:
        block_h = len(rtasks) * (TASK_BOX_H + TASK_GAP_Y) - TASK_GAP_Y
        block_h = max(block_h, ROLE_BOX_H)
        role_positions.append((r, y_cursor, y_cursor + block_h, rtasks))
        y_cursor += block_h + ROLE_GAP_Y

canvas_w = TASK_X + TASK_BOX_W + 100  # extra space for badges
canvas_h = y_cursor + 20

svg_parts = []

# SVG header
svg_parts.append(
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w}" height="{canvas_h}" '
    f'viewBox="0 0 {canvas_w} {canvas_h}" font-family="system-ui, sans-serif">'
)

# Background
svg_parts.append(f'<rect width="{canvas_w}" height="{canvas_h}" fill="#FAFBFC"/>')

# Legend
legend_items = [
    ("高频", COLOR_HIGH_FREQ),
    ("中频", COLOR_MED_FREQ),
    ("低频", COLOR_LOW_FREQ),
    ("高风险", COLOR_RISK_BADGE),
    ("跨部门", COLOR_CROSS_DEPT),
    ("冲突", COLOR_CONFLICT),
]
lx = LEFT_MARGIN
ly = 20
for label, color in legend_items:
    svg_parts.append(
        f'<rect x="{lx}" y="{ly}" width="14" height="14" rx="3" fill="{color}"/>'
    )
    svg_parts.append(
        f'<text x="{lx + 18}" y="{ly + 11}" font-size="11" fill="#475569">'
        f'{_escape_xml(label)}</text>'
    )
    lx += 70

# Title
svg_parts.append(
    f'<text x="{canvas_w / 2}" y="{ly + 11}" font-size="13" font-weight="bold" '
    f'fill="#1E293B" text-anchor="middle">产品地图 · 角色-任务树</text>'
)

# Draw roles and tasks
for role, y_start, y_end, rtasks in role_positions:
    role_cy = (y_start + y_end) / 2
    role_y = role_cy - ROLE_BOX_H / 2

    # Role box
    svg_parts.append(
        f'<rect x="{ROLE_X}" y="{role_y}" width="{ROLE_BOX_W}" height="{ROLE_BOX_H}" '
        f'rx="6" fill="{COLOR_ROLE_BG}"/>'
    )
    svg_parts.append(
        f'<text x="{ROLE_X + ROLE_BOX_W / 2}" y="{role_y + ROLE_BOX_H / 2 + 5}" '
        f'font-size="13" font-weight="bold" fill="{COLOR_WHITE}" text-anchor="middle">'
        f'{_escape_xml(_truncate(role["name"], 10))}</text>'
    )

    # Tasks
    ty = y_start
    for t in rtasks:
        tid = t["id"]
        tname = t.get("name", t.get("task_name", ""))
        freq = t.get("frequency", "低")
        risk = t.get("risk_level", "低")
        cross_dept = t.get("cross_dept", False)
        has_conflict = tid in conflict_task_ids

        fill = _freq_color(freq)

        # Connector line (role box right edge → task box left edge)
        line_y = ty + TASK_BOX_H / 2
        svg_parts.append(
            f'<line x1="{ROLE_X + ROLE_BOX_W}" y1="{role_cy}" '
            f'x2="{TASK_X}" y2="{line_y}" '
            f'stroke="{COLOR_LINE}" stroke-width="1.5"/>'
        )

        # Task box
        svg_parts.append(
            f'<rect x="{TASK_X}" y="{ty}" width="{TASK_BOX_W}" height="{TASK_BOX_H}" '
            f'rx="4" fill="{fill}"/>'
        )

        # Task label
        display_name = _truncate(f"{tid} {tname}", 22)
        svg_parts.append(
            f'<text x="{TASK_X + 8}" y="{ty + TASK_BOX_H / 2 + 4}" '
            f'font-size="11" fill="{COLOR_WHITE}">'
            f'{_escape_xml(display_name)}</text>'
        )

        # Frequency badge
        badge_x = TASK_X + TASK_BOX_W + 6
        svg_parts.append(
            f'<text x="{badge_x}" y="{ty + TASK_BOX_H / 2 + 4}" '
            f'font-size="9" fill="{fill}">{_escape_xml(_freq_label(freq))}</text>'
        )

        # Risk badge
        if risk == "高":
            rx_badge = badge_x + 30
            svg_parts.append(
                f'<circle cx="{rx_badge}" cy="{ty + TASK_BOX_H / 2}" r="5" '
                f'fill="{COLOR_RISK_BADGE}"/>'
            )
            svg_parts.append(
                f'<text x="{rx_badge}" y="{ty + TASK_BOX_H / 2 + 3}" '
                f'font-size="7" fill="{COLOR_WHITE}" text-anchor="middle">!</text>'
            )

        # Cross-dept badge
        if cross_dept:
            cx_badge = badge_x + (50 if risk == "高" else 30)
            svg_parts.append(
                f'<circle cx="{cx_badge}" cy="{ty + TASK_BOX_H / 2}" r="5" '
                f'fill="{COLOR_CROSS_DEPT}"/>'
            )
            svg_parts.append(
                f'<text x="{cx_badge}" y="{ty + TASK_BOX_H / 2 + 3}" '
                f'font-size="7" fill="{COLOR_WHITE}" text-anchor="middle">⇄</text>'
            )

        # Conflict marker (orange triangle)
        if has_conflict:
            tx = TASK_X - 12
            t_cy = ty + TASK_BOX_H / 2
            svg_parts.append(
                f'<polygon points="{tx},{t_cy - 6} {tx + 6},{t_cy + 4} {tx - 6},{t_cy + 4}" '
                f'fill="{COLOR_CONFLICT}"/>'
            )

        ty += TASK_BOX_H + TASK_GAP_Y

svg_parts.append("</svg>")

with open(os.path.join(PM, "product-map-visual.svg"), "w", encoding="utf-8") as f:
    f.write("\n".join(svg_parts))

# ── Decisions ─────────────────────────────────────────────────────────────────
decisions = [
    {
        "step": "Step 6",
        "item_id": "product_map",
        "item_name": f"产品地图汇总：{len(roles)} 角色, {len(tasks)} 任务, {len(flows)} 流",
        "decision": "auto_confirmed",
        "reason": "全自动模式",
        "decided_at": NOW,
    },
    {
        "step": "Step 6",
        "item_id": "task_index",
        "item_name": f"任务索引：{len(modules)} 模块, {len(categories)} 分类",
        "decision": "auto_confirmed",
        "reason": "全自动模式",
        "decided_at": NOW,
    },
    {
        "step": "Step 6",
        "item_id": "flow_index",
        "item_name": f"业务流索引：{len(flows)} 流",
        "decision": "auto_confirmed",
        "reason": "全自动模式",
        "decided_at": NOW,
    },
]

C.write_json(os.path.join(PM, "product-map-decisions-step6.json"), decisions)

# ── Pipeline decisions ────────────────────────────────────────────────────────
C.append_pipeline_decision(
    BASE,
    "Phase 2 — product-map (Step 6)",
    f"roles={len(roles)}, tasks={len(tasks)}, flows={len(flows)}, "
    f"basic={basic_count}, core={core_count}, "
    f"high_freq={high_freq_count}, high_risk={high_risk_count}, "
    f"conflicts={len(conflicts)}, constraints={len(constraints)}",
    shard=args.get("shard"),
)

# ── Step 7-8: Chain data-model + view-objects generation ─────────────────────
import subprocess

script_dir = os.path.dirname(os.path.abspath(__file__))
shard_args = ["--shard", args["shard"]] if args.get("shard") else []

dm_script = os.path.join(script_dir, "gen_data_model.py")
if os.path.exists(dm_script):
    print("\n--- Step 7: Data Model ---")
    subprocess.run([sys.executable, dm_script, BASE] + shard_args, check=True)

vo_script = os.path.join(script_dir, "gen_view_objects.py")
if os.path.exists(vo_script):
    print("\n--- Step 8: View Objects ---")
    subprocess.run([sys.executable, vo_script, BASE] + shard_args, check=True)

# ── Summary ───────────────────────────────────────────────────────────────────
print(f"\n=== Product Map Steps 6-8 Complete ===")
print(f"Roles: {len(roles)}")
print(f"Tasks: {len(tasks)} (basic={basic_count}, core={core_count})")
print(f"  High frequency: {high_freq_count}")
print(f"  High risk: {high_risk_count}")
print(f"Flows: {len(flows)} (gaps={flow_gap_total})")
print(f"Conflicts: {len(conflicts)}")
print(f"Constraints: {len(constraints)}")
print(f"Modules (task-index): {len(modules)}")
print(f"Scale: {product_map['scale']}")
print(f"\nFiles written to {PM}/")
print(f"  product-map.json")
print(f"  product-map-report.md")
print(f"  product-map-visual.svg")
print(f"  task-index.json")
print(f"  flow-index.json")
print(f"  entity-model.json (Step 7)")
print(f"  view-objects.json (Step 8)")
