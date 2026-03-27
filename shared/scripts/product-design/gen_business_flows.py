#!/usr/bin/env python3
# Skeleton generator — LLM enrichment required after running
"""Generate business flows by grouping tasks per module.

Pre-built script for product-map Step 3 (business flow generation).
Groups tasks by module field, creates one flow per module with tasks
ordered by ID. Generates JSON, Markdown report, and SVG swimlane.

Usage:
    python3 gen_business_flows.py <BASE_PATH> [--mode auto] [--shard product-map]
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C

# ── Setup ─────────────────────────────────────────────────────────────────────
BASE, args = C.parse_args()
OUT = os.path.join(BASE, "product-map")
C.ensure_dir(OUT)
NOW = C.now_iso()

# ── Load data ─────────────────────────────────────────────────────────────────
tasks = C.load_task_inventory(BASE)
role_map = C.load_role_profiles(BASE)

# ── Step 1: Group tasks by module ─────────────────────────────────────────────
module_tasks = {}  # module_name → [task_id, ...]
for tid, task in tasks.items():
    module = task.get("module", "unknown")
    module_tasks.setdefault(module, []).append(tid)

# Sort task IDs within each module for deterministic ordering
for mod in module_tasks:
    module_tasks[mod].sort()

# ── Step 2: Build one flow per module ─────────────────────────────────────────
flows = []
flow_counter = 0

for module, tids in sorted(module_tasks.items()):
    if len(tids) < 1:
        continue
    flow_counter += 1
    fid = f"F{flow_counter:03d}"

    nodes = []
    for seq_idx, tid in enumerate(tids):
        task = tasks[tid]
        nodes.append({
            "seq": seq_idx + 1,
            "task_ref": tid,
            "task_name": task.get("task_name", task.get("name", "")),
            "role": task.get("owner_role", ""),
            "handoff": "",
            "gap_flags": []
        })

    flows.append({
        "id": fid,
        "name": f"{module}流程",
        "description": f"{module} 模块的 {len(tids)} 个任务",
        "trigger": module,
        "nodes": nodes,
        "gap_flags": [],
        "audit": {
            "handoff_breaks": 0,
            "orphan_states": [],
            "ghost_states": [],
            "missing_terminals": False
        }
    })

# ── Step 3: Identify orphan tasks (not in any flow — none here, but keep structure)
flow_tasks_set = set()
for flow in flows:
    for node in flow["nodes"]:
        flow_tasks_set.add(node["task_ref"])

orphan_tasks_list = []
for tid in sorted(tasks.keys()):
    if tid not in flow_tasks_set:
        task = tasks[tid]
        orphan_tasks_list.append({
            "task_ref": tid,
            "task_name": task.get("task_name", task.get("name", "")),
            "classification": "ORPHAN_TASK",
            "reason": "未归入任何模块流程"
        })

# ── Step 4: Build output JSON ─────────────────────────────────────────────────
output = {
    "flows": flows,
    "orphan_tasks": orphan_tasks_list,
    "audit_summary": {
        "total_flows": len(flows),
        "total_gaps": 0,
        "orphan_states": [],
        "ghost_states": [],
        "high_freq_uncovered": []
    },
    "generated_at": NOW
}

C.write_json(os.path.join(OUT, "business-flows.json"), output)

# ── Step 5: Markdown report ───────────────────────────────────────────────────
lines = []
lines.append("# 业务流报告\n")
lines.append(f"{len(flows)} 条业务流 · {len(orphan_tasks_list)} 个孤立任务\n")

lines.append("## 业务流列表\n")
for flow in flows:
    lines.append(f"- **{flow['id']}** {flow['name']} ({len(flow['nodes'])} 步)")

lines.append("\n## 业务流详情\n")
for flow in flows:
    lines.append(f"### {flow['id']} {flow['name']}\n")
    lines.append(f"触发条件: {flow['trigger']}\n")
    lines.append("| 序号 | 任务 | 角色 |")
    lines.append("|------|------|------|")
    for node in flow["nodes"]:
        role_name = role_map.get(node["role"], node["role"])
        lines.append(f"| {node['seq']} | {node['task_name']} ({node['task_ref']}) | {role_name} |")
    lines.append("")

if orphan_tasks_list:
    lines.append("## 孤立任务\n")
    for o in orphan_tasks_list:
        lines.append(f"- {o['task_ref']} {o['task_name']}")
    lines.append("")

lines.append("> 完整数据见 .allforai/product-map/business-flows.json\n")

with open(os.path.join(OUT, "business-flows-report.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

# ── Step 6: SVG Swimlane Diagram ──────────────────────────────────────────────

SVG_FLOW_TITLE_BG = "#1E293B"
SVG_FLOW_TITLE_TEXT = "#FFFFFF"
SVG_LANE_BG = "#F1F5F9"
SVG_LANE_TEXT = "#475569"
SVG_NODE_BORDER = "#3B82F6"
SVG_NODE_FILL = "#EFF6FF"
SVG_NODE_TEXT = "#1E3A8A"
SVG_SEQ_FILL = "#3B82F6"
SVG_SEQ_TEXT = "#FFFFFF"
SVG_ARROW_COLOR = "#94A3B8"

NODE_W = 200
NODE_H = 50
NODE_PAD_X = 60
NODE_PAD_Y = 30
LANE_PAD = 20
FLOW_TITLE_H = 40
LANE_LABEL_W = 100
SEQ_R = 12
FLOW_GAP_Y = 40


def escape_xml(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace("\"", "&quot;"))


def truncate(s, max_len=22):
    return s[:max_len - 1] + "…" if len(s) > max_len else s


def generate_svg(flows_data):
    if not flows_data:
        return '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="100">' \
               '<text x="20" y="50" fill="#666" font-size="14">无业务流数据</text></svg>'

    svg_parts = []
    total_y = 20

    for flow in flows_data:
        nodes = flow["nodes"]
        if not nodes:
            continue

        role_ids_ordered = []
        seen_roles = set()
        for node in nodes:
            rid = node["role"]
            if rid not in seen_roles:
                seen_roles.add(rid)
                role_ids_ordered.append(rid)

        num_lanes = len(role_ids_ordered)
        if num_lanes == 0:
            continue

        role_to_lane = {rid: idx for idx, rid in enumerate(role_ids_ordered)}
        lane_h = NODE_H + NODE_PAD_Y * 2
        num_nodes = len(nodes)
        content_w = LANE_LABEL_W + num_nodes * (NODE_W + NODE_PAD_X) + NODE_PAD_X
        flow_h = FLOW_TITLE_H + num_lanes * lane_h
        flow_y = total_y

        svg_parts.append(
            f'<rect x="20" y="{flow_y}" width="{content_w}" height="{FLOW_TITLE_H}" '
            f'rx="6" fill="{SVG_FLOW_TITLE_BG}"/>'
        )
        svg_parts.append(
            f'<text x="30" y="{flow_y + 26}" fill="{SVG_FLOW_TITLE_TEXT}" '
            f'font-size="14" font-weight="bold">'
            f'{escape_xml(flow["id"])} {escape_xml(truncate(flow["name"], 50))}</text>'
        )

        lanes_y = flow_y + FLOW_TITLE_H
        for lane_idx, rid in enumerate(role_ids_ordered):
            ly = lanes_y + lane_idx * lane_h
            rname = role_map.get(rid, rid)
            bg_color = SVG_LANE_BG if lane_idx % 2 == 0 else "#E8EEF4"
            svg_parts.append(
                f'<rect x="20" y="{ly}" width="{content_w}" height="{lane_h}" fill="{bg_color}"/>'
            )
            svg_parts.append(
                f'<line x1="20" y1="{ly}" x2="{20 + content_w}" y2="{ly}" '
                f'stroke="#CBD5E1" stroke-width="1"/>'
            )
            svg_parts.append(
                f'<text x="30" y="{ly + lane_h // 2 + 5}" fill="{SVG_LANE_TEXT}" '
                f'font-size="12" font-weight="bold">{escape_xml(truncate(rname, 10))}</text>'
            )

        bottom_y = lanes_y + num_lanes * lane_h
        svg_parts.append(
            f'<line x1="20" y1="{bottom_y}" x2="{20 + content_w}" y2="{bottom_y}" '
            f'stroke="#CBD5E1" stroke-width="1"/>'
        )

        node_positions = {}
        for node in nodes:
            seq = node["seq"]
            lane_idx = role_to_lane.get(node["role"], 0)
            nx = 20 + LANE_LABEL_W + (seq - 1) * (NODE_W + NODE_PAD_X) + NODE_PAD_X // 2
            ny = lanes_y + lane_idx * lane_h + NODE_PAD_Y
            cx = nx + NODE_W // 2
            cy = ny + NODE_H // 2
            node_positions[seq] = (cx, cy, nx, ny)

            svg_parts.append(
                f'<rect x="{nx}" y="{ny}" width="{NODE_W}" height="{NODE_H}" '
                f'rx="8" fill="{SVG_NODE_FILL}" stroke="{SVG_NODE_BORDER}" stroke-width="2"/>'
            )
            svg_parts.append(
                f'<circle cx="{nx + 16}" cy="{ny + 16}" r="{SEQ_R}" fill="{SVG_SEQ_FILL}"/>'
            )
            svg_parts.append(
                f'<text x="{nx + 16}" y="{ny + 20}" fill="{SVG_SEQ_TEXT}" '
                f'font-size="10" text-anchor="middle">{seq}</text>'
            )
            svg_parts.append(
                f'<text x="{nx + 36}" y="{ny + 20}" fill="{SVG_NODE_TEXT}" '
                f'font-size="11">{escape_xml(truncate(node["task_name"], 16))}</text>'
            )
            svg_parts.append(
                f'<text x="{nx + 36}" y="{ny + 38}" fill="#64748B" '
                f'font-size="9">{escape_xml(node["task_ref"])}</text>'
            )

        for i in range(len(nodes) - 1):
            seq_a = nodes[i]["seq"]
            seq_b = nodes[i + 1]["seq"]
            if seq_a not in node_positions or seq_b not in node_positions:
                continue
            cx_a, cy_a, nx_a, ny_a = node_positions[seq_a]
            cx_b, cy_b, nx_b, ny_b = node_positions[seq_b]
            x1 = nx_a + NODE_W
            y1 = cy_a
            x2 = nx_b
            y2 = cy_b
            if abs(y1 - y2) < 5:
                svg_parts.append(
                    f'<line x1="{x1}" y1="{y1}" x2="{x2 - 6}" y2="{y2}" '
                    f'stroke="{SVG_ARROW_COLOR}" stroke-width="2" marker-end="url(#arrowhead)"/>'
                )
            else:
                mid_x = (x1 + x2) // 2
                svg_parts.append(
                    f'<path d="M {x1} {y1} C {mid_x} {y1}, {mid_x} {y2}, {x2 - 6} {y2}" '
                    f'stroke="{SVG_ARROW_COLOR}" stroke-width="2" fill="none" '
                    f'marker-end="url(#arrowhead)"/>'
                )

        total_y = bottom_y + FLOW_GAP_Y

    canvas_w = max(600, max(
        (LANE_LABEL_W + len(f["nodes"]) * (NODE_W + NODE_PAD_X) + NODE_PAD_X + 40)
        for f in flows_data if f["nodes"]
    ) if flows_data else 600)
    canvas_h = total_y + 20

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w}" height="{canvas_h}"
     viewBox="0 0 {canvas_w} {canvas_h}" style="background:#FFFFFF">
  <defs>
    <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
      <polygon points="0 0, 10 3.5, 0 7" fill="{SVG_ARROW_COLOR}"/>
    </marker>
    <style>
      text {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
    </style>
  </defs>
'''
    svg += "\n".join(f"  {p}" for p in svg_parts)
    svg += "\n</svg>"
    return svg


svg_content = generate_svg(flows)
with open(os.path.join(OUT, "business-flows-visual.svg"), "w", encoding="utf-8") as f:
    f.write(svg_content)

# ── Pipeline decisions ────────────────────────────────────────────────────────
C.append_pipeline_decision(
    BASE,
    "Phase 3 — business-flows",
    f"flows={len(flows)}, orphan_tasks={len(orphan_tasks_list)}",
    shard=args.get("shard")
)

# ── Summary ───────────────────────────────────────────────────────────────────
print(f"Flows generated: {len(flows)}")
print(f"Total flow nodes: {sum(len(f['nodes']) for f in flows)}")
print(f"Orphan tasks: {len(orphan_tasks_list)}")
print(f"\nAll files written to {OUT}/")
