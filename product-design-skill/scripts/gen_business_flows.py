#!/usr/bin/env python3
"""Generate business flows from task-inventory by analyzing state handoffs.

Pre-built script for product-map Step 3 (business flow generation + validation).
Analyzes task outputs.states / prerequisites relationships to build flow chains,
validates handoff continuity, detects orphan/ghost states, generates SVG swimlane.

Usage:
    python3 gen_business_flows.py <BASE_PATH> [--mode auto] [--shard product-map]
"""

import os
import sys
import re
from collections import defaultdict

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

# ── Helpers ───────────────────────────────────────────────────────────────────

def get_output_states(task):
    """Extract output states from a task, defensively."""
    outputs = task.get("outputs")
    if not outputs or not isinstance(outputs, dict):
        return []
    states = outputs.get("states", [])
    if isinstance(states, list):
        return [s for s in states if isinstance(s, str) and s.strip()]
    return []


def get_prerequisites(task):
    """Extract prerequisites from a task, defensively."""
    prereqs = task.get("prerequisites", [])
    if isinstance(prereqs, list):
        return [p for p in prereqs if isinstance(p, str) and p.strip()]
    return []


def normalize_state(s):
    """Normalize a state string for fuzzy matching."""
    # Remove common prefixes/suffixes, lowercase, strip whitespace
    s = s.strip()
    # Remove quotes
    s = s.replace("「", "").replace("」", "").replace(""", "").replace(""", "")
    s = s.replace("'", "").replace("'", "").replace("\"", "")
    return s


def states_match(output_state, prereq):
    """Check if an output state matches a prerequisite (fuzzy)."""
    os_norm = normalize_state(output_state)
    pr_norm = normalize_state(prereq)
    if not os_norm or not pr_norm:
        return False
    # Exact match
    if os_norm == pr_norm:
        return True
    # Containment match (state appears in prerequisite or vice versa)
    if os_norm in pr_norm or pr_norm in os_norm:
        return True
    # Keyword overlap: split on common delimiters, check overlap
    os_words = set(re.split(r'[，,、/\s]+', os_norm)) - {""}
    pr_words = set(re.split(r'[，,、/\s]+', pr_norm)) - {""}
    if os_words and pr_words:
        overlap = os_words & pr_words
        # At least 2 words overlap, or overlap is >50% of the smaller set
        min_len = min(len(os_words), len(pr_words))
        if len(overlap) >= 2 or (min_len > 0 and len(overlap) / min_len >= 0.5):
            return True
    return False


# ── Step 1: Build state-based edges ──────────────────────────────────────────
# edge = (task_A_id, task_B_id, matched_state, matched_prereq)

edges = []  # (from_id, to_id, output_state, prereq_text)
task_ids = list(tasks.keys())

for tid_a in task_ids:
    out_states = get_output_states(tasks[tid_a])
    if not out_states:
        continue
    for tid_b in task_ids:
        if tid_a == tid_b:
            continue
        prereqs = get_prerequisites(tasks[tid_b])
        if not prereqs:
            continue
        for state in out_states:
            for prereq in prereqs:
                if states_match(state, prereq):
                    edges.append((tid_a, tid_b, state, prereq))

# Deduplicate edges (keep first match per pair)
seen_pairs = set()
unique_edges = []
for e in edges:
    pair = (e[0], e[1])
    if pair not in seen_pairs:
        seen_pairs.add(pair)
        unique_edges.append(e)
edges = unique_edges

# ── Step 2: Build connected components (flow chains) ─────────────────────────

# Adjacency list (undirected for component detection)
adj = defaultdict(set)
# Directed adjacency for ordering
directed = defaultdict(set)
directed_reverse = defaultdict(set)

for (a, b, _, _) in edges:
    adj[a].add(b)
    adj[b].add(a)
    directed[a].add(b)
    directed_reverse[b].add(a)

# All tasks that participate in at least one edge
edge_tasks = set()
for (a, b, _, _) in edges:
    edge_tasks.add(a)
    edge_tasks.add(b)

# BFS to find connected components
visited = set()
components = []

for start in sorted(edge_tasks):
    if start in visited:
        continue
    component = []
    queue = [start]
    visited.add(start)
    while queue:
        node = queue.pop(0)
        component.append(node)
        for neighbor in sorted(adj[node]):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    if component:
        components.append(component)

# ── Step 3: Topological sort within each component ───────────────────────────

def topo_sort(task_ids_in_component):
    """Topological sort of tasks within a component using directed edges."""
    in_scope = set(task_ids_in_component)
    in_degree = {t: 0 for t in in_scope}
    local_adj = defaultdict(list)
    for t in in_scope:
        for nxt in directed[t]:
            if nxt in in_scope:
                local_adj[t].append(nxt)
                in_degree[nxt] = in_degree.get(nxt, 0) + 1

    # Kahn's algorithm
    queue = sorted([t for t in in_scope if in_degree[t] == 0])
    result = []
    while queue:
        node = queue.pop(0)
        result.append(node)
        for nxt in sorted(local_adj[node]):
            in_degree[nxt] -= 1
            if in_degree[nxt] == 0:
                queue.append(nxt)

    # If cycle detected, append remaining tasks
    remaining = [t for t in task_ids_in_component if t not in set(result)]
    result.extend(sorted(remaining))
    return result


# ── Step 4: Build flow objects ───────────────────────────────────────────────

def infer_flow_name(task_list):
    """Infer a flow name from the task names in the chain."""
    names = [tasks[t].get("task_name", tasks[t].get("name", "")) for t in task_list]
    if not names:
        return "未命名流程"
    # Use the first and last task to describe the flow
    first = names[0]
    last = names[-1]
    if len(names) == 1:
        return f"{first}流程"
    return f"{first} → {last}"


def infer_trigger(task_list):
    """Infer a trigger description from the first task's prerequisites."""
    if not task_list:
        return ""
    first_task = tasks[task_list[0]]
    prereqs = get_prerequisites(first_task)
    if prereqs:
        return "；".join(prereqs[:3])
    return first_task.get("task_name", first_task.get("name", ""))


def get_handoff_text(from_tid, to_tid):
    """Get handoff description between two tasks."""
    out_states = get_output_states(tasks[from_tid])
    prereqs = get_prerequisites(tasks[to_tid])
    for state in out_states:
        for prereq in prereqs:
            if states_match(state, prereq):
                return state
    # Fallback: use first output state
    if out_states:
        return out_states[0]
    return ""


flows = []
flow_counter = 0

for comp in components:
    if len(comp) < 2:
        # Single-task components don't form meaningful flows
        continue
    sorted_tasks = topo_sort(comp)
    flow_counter += 1
    fid = f"F{flow_counter:03d}"

    nodes = []
    for seq_idx, tid in enumerate(sorted_tasks):
        task = tasks[tid]
        # Determine handoff to next node
        handoff = ""
        if seq_idx < len(sorted_tasks) - 1:
            handoff = get_handoff_text(tid, sorted_tasks[seq_idx + 1])

        nodes.append({
            "seq": seq_idx + 1,
            "task_ref": tid,
            "task_name": task.get("task_name", task.get("name", "")),
            "role": task.get("owner_role", ""),
            "handoff": handoff,
            "gap_flags": []
        })

    flows.append({
        "id": fid,
        "name": infer_flow_name(sorted_tasks),
        "description": f"{len(sorted_tasks)} 个任务组成的业务链路",
        "trigger": infer_trigger(sorted_tasks),
        "nodes": nodes,
        "gap_flags": [],
        "audit": {
            "handoff_breaks": 0,
            "orphan_states": [],
            "ghost_states": [],
            "missing_terminals": False
        }
    })

# Also create single-task flows if they have strong connections (both in and out edges)
for comp in components:
    if len(comp) == 1:
        tid = comp[0]
        # Only if the task has both incoming and outgoing edges outside component
        # (already included via edge-based component — skip singles)
        pass

# ── Step 5: Flow Validation (self-audit) ─────────────────────────────────────

# Collect all produced and consumed states globally
all_produced_states = set()
all_consumed_states = set()
produced_state_tasks = defaultdict(list)  # state → [task_ids that produce it]
consumed_state_tasks = defaultdict(list)  # state → [task_ids that consume it]

for tid, task in tasks.items():
    for state in get_output_states(task):
        ns = normalize_state(state)
        all_produced_states.add(ns)
        produced_state_tasks[ns].append(tid)
    for prereq in get_prerequisites(task):
        ns = normalize_state(prereq)
        all_consumed_states.add(ns)
        consumed_state_tasks[ns].append(tid)

# Global orphan states: produced but never consumed by any task
global_orphan_states = []
for state in sorted(all_produced_states):
    consumed = False
    for consumed_state in all_consumed_states:
        if states_match(state, consumed_state):
            consumed = True
            break
    if not consumed:
        global_orphan_states.append(state)

# Global ghost states: consumed but never produced by any task
global_ghost_states = []
for state in sorted(all_consumed_states):
    produced = False
    for produced_state in all_produced_states:
        if states_match(produced_state, state):
            produced = True
            break
    if not produced:
        global_ghost_states.append(state)

# Per-flow validation
total_gaps = 0
flow_tasks_set = set()  # all tasks in any flow

for flow in flows:
    nodes = flow["nodes"]
    flow_gap_flags = []
    handoff_breaks = 0
    flow_orphan = []
    flow_ghost = []

    for tid_node in nodes:
        flow_tasks_set.add(tid_node["task_ref"])

    # 5a. Handoff continuity: node[i] outputs match node[i+1] prerequisites
    for i in range(len(nodes) - 1):
        curr_tid = nodes[i]["task_ref"]
        next_tid = nodes[i + 1]["task_ref"]
        curr_outputs = get_output_states(tasks.get(curr_tid, {}))
        next_prereqs = get_prerequisites(tasks.get(next_tid, {}))

        if not curr_outputs and not next_prereqs:
            # Both empty — may be fine for simple tasks
            continue

        if curr_outputs and next_prereqs:
            found_match = False
            for state in curr_outputs:
                for prereq in next_prereqs:
                    if states_match(state, prereq):
                        found_match = True
                        break
                if found_match:
                    break
            if not found_match:
                handoff_breaks += 1
                nodes[i]["gap_flags"].append("HANDOFF_BREAK")
                nodes[i + 1]["gap_flags"].append("HANDOFF_BREAK")
        elif curr_outputs and not next_prereqs:
            # Next task has no prereqs — might be fine, but flag as info
            pass
        elif not curr_outputs and next_prereqs:
            # Current task produces no states but next expects prereqs
            handoff_breaks += 1
            nodes[i]["gap_flags"].append("NO_OUTPUT_STATES")

    # 5b. Terminal check: last node should have no outgoing handoffs within the flow
    last_tid = nodes[-1]["task_ref"] if nodes else None
    missing_terminal = False
    if last_tid:
        last_outputs = get_output_states(tasks.get(last_tid, {}))
        # Check if any output feeds into another flow task
        for state in last_outputs:
            for other_node in nodes[:-1]:
                other_prereqs = get_prerequisites(tasks.get(other_node["task_ref"], {}))
                for prereq in other_prereqs:
                    if states_match(state, prereq):
                        missing_terminal = True
                        break
                if missing_terminal:
                    break
            if missing_terminal:
                break

    # 5c. State contract check: tasks with outputs.states should have exceptions
    for node in nodes:
        tid = node["task_ref"]
        task = tasks.get(tid, {})
        out_states = get_output_states(task)
        if out_states and not task.get("exceptions"):
            node["gap_flags"].append("NO_EXCEPTION_FOR_STATES")

    # Collect gap flags
    for node in nodes:
        if node["gap_flags"]:
            flow_gap_flags.extend(node["gap_flags"])

    if handoff_breaks > 0:
        flow_gap_flags.append("HANDOFF_BREAK")
    if missing_terminal:
        flow_gap_flags.append("MISSING_TERMINAL")

    # Deduplicate flow-level flags
    seen = set()
    unique_flags = []
    for f in flow_gap_flags:
        if f not in seen:
            seen.add(f)
            unique_flags.append(f)

    flow["gap_flags"] = unique_flags
    flow["audit"] = {
        "handoff_breaks": handoff_breaks,
        "orphan_states": flow_orphan,
        "ghost_states": flow_ghost,
        "missing_terminals": missing_terminal
    }
    total_gaps += len(unique_flags)

# ── Step 6: High-freq coverage check ─────────────────────────────────────────
high_freq_uncovered = []
for tid, task in tasks.items():
    if task.get("frequency") == "高" and tid not in flow_tasks_set:
        high_freq_uncovered.append(tid)

# ── Step 7: Orphan Task Classification ───────────────────────────────────────

INDEPENDENT_KEYWORDS = ["导出", "设置", "配置", "查看列表", "管理档案",
                        "导入", "下载", "打印", "统计", "报表"]

orphan_tasks_list = []
for tid in sorted(tasks.keys()):
    if tid in flow_tasks_set:
        continue
    task = tasks[tid]
    tname = task.get("task_name", task.get("name", ""))
    cross_dept = task.get("cross_dept", False)
    approver = task.get("approver_role", "")

    # Determine classification
    is_independent = False
    reason = ""

    # Check keyword match
    for kw in INDEPENDENT_KEYWORDS:
        if kw in tname:
            is_independent = True
            reason = f"任务名称包含关键词「{kw}」"
            break

    # Additional heuristic: no cross_dept and no approver
    if not is_independent and not cross_dept and not approver:
        # Check if task has no output states (truly standalone)
        out_states = get_output_states(task)
        prereqs = get_prerequisites(task)
        if not out_states and not prereqs:
            is_independent = True
            reason = "无跨部门、无审批角色、无状态输入输出"

    if not is_independent:
        reason = "未匹配独立操作条件，可能遗漏业务流建模"

    orphan_tasks_list.append({
        "task_ref": tid,
        "task_name": tname,
        "classification": "INDEPENDENT_OPERATION" if is_independent else "ORPHAN_TASK",
        "reason": reason
    })

# ── Step 8: Build output JSON ────────────────────────────────────────────────

output = {
    "flows": flows,
    "orphan_tasks": orphan_tasks_list,
    "audit_summary": {
        "total_flows": len(flows),
        "total_gaps": total_gaps,
        "orphan_states": global_orphan_states,
        "ghost_states": global_ghost_states,
        "high_freq_uncovered": high_freq_uncovered
    },
    "generated_at": NOW
}

C.write_json(os.path.join(OUT, "business-flows.json"), output)

# ── Step 9: Markdown report ──────────────────────────────────────────────────

lines = []
lines.append("# 业务流报告\n")

orphan_count = sum(1 for o in orphan_tasks_list if o["classification"] == "ORPHAN_TASK")
indep_count = sum(1 for o in orphan_tasks_list if o["classification"] == "INDEPENDENT_OPERATION")
lines.append(
    f"{len(flows)} 条业务流 · {total_gaps} 个流缺口 · "
    f"{orphan_count} 个孤立任务 · {indep_count} 个独立操作\n"
)

# Flow list
lines.append("## 业务流列表\n")
for flow in flows:
    gap_info = f"— {len(flow['gap_flags'])} 个缺口" if flow["gap_flags"] else "— 无缺口"
    lines.append(f"- **{flow['id']}** {flow['name']} {gap_info}")

# Flow details
lines.append("\n## 业务流详情\n")
for flow in flows:
    lines.append(f"### {flow['id']} {flow['name']}\n")
    lines.append(f"触发条件: {flow['trigger']}\n")
    lines.append("| 序号 | 任务 | 角色 | 交接 | 缺口 |")
    lines.append("|------|------|------|------|------|")
    for node in flow["nodes"]:
        role_name = role_map.get(node["role"], node["role"])
        gaps_str = ", ".join(node["gap_flags"]) if node["gap_flags"] else "—"
        handoff_str = node["handoff"] if node["handoff"] else "—"
        lines.append(
            f"| {node['seq']} | {node['task_name']} ({node['task_ref']}) "
            f"| {role_name} | {handoff_str} | {gaps_str} |"
        )
    if flow["audit"]["handoff_breaks"] > 0:
        lines.append(f"\n> 交接断裂: {flow['audit']['handoff_breaks']} 处")
    if flow["audit"]["missing_terminals"]:
        lines.append("> 缺少终止节点")
    lines.append("")

# Gap summary
if global_ghost_states:
    lines.append("## 幽灵状态（CRITICAL）\n")
    lines.append("以下状态被任务前置条件引用，但没有任何任务产出：\n")
    for gs in global_ghost_states:
        consumers = consumed_state_tasks.get(gs, [])
        lines.append(f"- **{gs}** ← 被 {', '.join(consumers[:5])} 依赖")
    lines.append("")

if global_orphan_states:
    lines.append("## 孤立状态\n")
    lines.append("以下状态被任务产出，但没有任何任务消费：\n")
    for os_state in global_orphan_states:
        producers = produced_state_tasks.get(os_state, [])
        lines.append(f"- **{os_state}** ← 由 {', '.join(producers[:5])} 产出")
    lines.append("")

if high_freq_uncovered:
    lines.append("## 高频任务未覆盖\n")
    for tid in high_freq_uncovered:
        task = tasks[tid]
        tname = task.get("task_name", task.get("name", ""))
        lines.append(f"- {tid} {tname}")
    lines.append("")

# Orphan tasks
if orphan_tasks_list:
    orphan_only = [o for o in orphan_tasks_list if o["classification"] == "ORPHAN_TASK"]
    indep_only = [o for o in orphan_tasks_list if o["classification"] == "INDEPENDENT_OPERATION"]

    if orphan_only:
        lines.append("## 孤立任务（可能遗漏建模，需确认）\n")
        for o in orphan_only:
            lines.append(f"- {o['task_ref']} {o['task_name']} — {o['reason']}")
        lines.append("")

    if indep_only:
        lines.append("## 独立操作（无需纳入流）\n")
        for o in indep_only:
            lines.append(f"- {o['task_ref']} {o['task_name']}")
        lines.append("")

lines.append("> 完整数据见 .allforai/product-map/business-flows.json\n")

with open(os.path.join(OUT, "business-flows-report.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

# ── Step 10: SVG Swimlane Diagram ────────────────────────────────────────────

# SVG constants
SVG_FLOW_TITLE_BG = "#1E293B"
SVG_FLOW_TITLE_TEXT = "#FFFFFF"
SVG_LANE_BG = "#F1F5F9"
SVG_LANE_TEXT = "#475569"
SVG_NODE_BORDER = "#3B82F6"
SVG_NODE_FILL = "#EFF6FF"
SVG_NODE_TEXT = "#1E3A8A"
SVG_GAP_BORDER = "#EF4444"
SVG_GAP_FILL = "#FEF2F2"
SVG_GAP_TEXT = "#991B1B"
SVG_SEQ_FILL = "#3B82F6"
SVG_SEQ_TEXT = "#FFFFFF"
SVG_ARROW_TEXT = "#64748B"
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
    """Escape text for SVG/XML."""
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace("\"", "&quot;"))


def truncate(s, max_len=22):
    """Truncate string for SVG display."""
    if len(s) > max_len:
        return s[:max_len - 1] + "…"
    return s


def generate_svg(flows_data):
    """Generate SVG swimlane diagram for all flows."""
    if not flows_data:
        return '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="100">' \
               '<text x="20" y="50" fill="#666" font-size="14">无业务流数据</text></svg>'

    svg_parts = []
    total_y = 20

    for flow in flows_data:
        nodes = flow["nodes"]
        if not nodes:
            continue

        # Determine roles (swimlanes) in this flow
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

        # Calculate flow section dimensions
        num_nodes = len(nodes)
        content_w = LANE_LABEL_W + num_nodes * (NODE_W + NODE_PAD_X) + NODE_PAD_X
        flow_h = FLOW_TITLE_H + num_lanes * lane_h

        flow_y = total_y

        # Flow title bar
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

        # Draw swimlanes
        for lane_idx, rid in enumerate(role_ids_ordered):
            ly = lanes_y + lane_idx * lane_h
            rname = role_map.get(rid, rid)

            # Lane background
            bg_color = SVG_LANE_BG if lane_idx % 2 == 0 else "#E8EEF4"
            svg_parts.append(
                f'<rect x="20" y="{ly}" width="{content_w}" height="{lane_h}" '
                f'fill="{bg_color}"/>'
            )
            # Lane divider
            svg_parts.append(
                f'<line x1="20" y1="{ly}" x2="{20 + content_w}" y2="{ly}" '
                f'stroke="#CBD5E1" stroke-width="1"/>'
            )
            # Lane label
            svg_parts.append(
                f'<text x="30" y="{ly + lane_h // 2 + 5}" fill="{SVG_LANE_TEXT}" '
                f'font-size="12" font-weight="bold">{escape_xml(truncate(rname, 10))}</text>'
            )

        # Bottom border of lanes
        bottom_y = lanes_y + num_lanes * lane_h
        svg_parts.append(
            f'<line x1="20" y1="{bottom_y}" x2="{20 + content_w}" y2="{bottom_y}" '
            f'stroke="#CBD5E1" stroke-width="1"/>'
        )

        # Draw nodes
        node_positions = {}  # node_seq → (cx, cy)
        for node in nodes:
            seq = node["seq"]
            lane_idx = role_to_lane.get(node["role"], 0)
            nx = 20 + LANE_LABEL_W + (seq - 1) * (NODE_W + NODE_PAD_X) + NODE_PAD_X // 2
            ny = lanes_y + lane_idx * lane_h + NODE_PAD_Y
            cx = nx + NODE_W // 2
            cy = ny + NODE_H // 2
            node_positions[seq] = (cx, cy, nx, ny)

            has_gap = bool(node["gap_flags"])
            border = SVG_GAP_BORDER if has_gap else SVG_NODE_BORDER
            fill = SVG_GAP_FILL if has_gap else SVG_NODE_FILL
            text_color = SVG_GAP_TEXT if has_gap else SVG_NODE_TEXT
            dash = ' stroke-dasharray="6,3"' if has_gap else ""

            # Node rectangle
            svg_parts.append(
                f'<rect x="{nx}" y="{ny}" width="{NODE_W}" height="{NODE_H}" '
                f'rx="8" fill="{fill}" stroke="{border}" stroke-width="2"{dash}/>'
            )

            # Seq number circle
            svg_parts.append(
                f'<circle cx="{nx + 16}" cy="{ny + 16}" r="{SEQ_R}" '
                f'fill="{SVG_SEQ_FILL}"/>'
            )
            svg_parts.append(
                f'<text x="{nx + 16}" y="{ny + 20}" fill="{SVG_SEQ_TEXT}" '
                f'font-size="10" text-anchor="middle">{seq}</text>'
            )

            # Task name
            display_name = truncate(node["task_name"], 16)
            svg_parts.append(
                f'<text x="{nx + 36}" y="{ny + 20}" fill="{text_color}" '
                f'font-size="11">{escape_xml(display_name)}</text>'
            )
            # Task ref
            svg_parts.append(
                f'<text x="{nx + 36}" y="{ny + 38}" fill="{SVG_ARROW_TEXT}" '
                f'font-size="9">{escape_xml(node["task_ref"])}</text>'
            )

        # Draw arrows between consecutive nodes
        # Arrow marker definition is added once at the top
        for i in range(len(nodes) - 1):
            seq_a = nodes[i]["seq"]
            seq_b = nodes[i + 1]["seq"]
            if seq_a not in node_positions or seq_b not in node_positions:
                continue
            cx_a, cy_a, nx_a, ny_a = node_positions[seq_a]
            cx_b, cy_b, nx_b, ny_b = node_positions[seq_b]

            # Arrow from right edge of A to left edge of B
            x1 = nx_a + NODE_W
            y1 = cy_a
            x2 = nx_b
            y2 = cy_b

            # If same lane, straight arrow; if different lane, curved
            if abs(y1 - y2) < 5:
                svg_parts.append(
                    f'<line x1="{x1}" y1="{y1}" x2="{x2 - 6}" y2="{y2}" '
                    f'stroke="{SVG_ARROW_COLOR}" stroke-width="2" '
                    f'marker-end="url(#arrowhead)"/>'
                )
            else:
                mid_x = (x1 + x2) // 2
                svg_parts.append(
                    f'<path d="M {x1} {y1} C {mid_x} {y1}, {mid_x} {y2}, {x2 - 6} {y2}" '
                    f'stroke="{SVG_ARROW_COLOR}" stroke-width="2" fill="none" '
                    f'marker-end="url(#arrowhead)"/>'
                )

            # Handoff text
            handoff = nodes[i].get("handoff", "")
            if handoff:
                tx = (x1 + x2) // 2
                ty = min(y1, y2) - 8
                svg_parts.append(
                    f'<text x="{tx}" y="{ty}" fill="{SVG_ARROW_TEXT}" '
                    f'font-size="9" text-anchor="middle">'
                    f'{escape_xml(truncate(handoff, 18))}</text>'
                )

        total_y = bottom_y + FLOW_GAP_Y

    # Canvas dimensions
    canvas_w = max(600, max(
        (LANE_LABEL_W + len(f["nodes"]) * (NODE_W + NODE_PAD_X) + NODE_PAD_X + 40)
        for f in flows_data if f["nodes"]
    ) if flows_data else 600)
    canvas_h = total_y + 20

    # Assemble SVG
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


# Generate SVG
svg_content = generate_svg(flows)

with open(os.path.join(OUT, "business-flows-visual.svg"), "w", encoding="utf-8") as f:
    f.write(svg_content)

# ── Pipeline decisions ────────────────────────────────────────────────────────
C.append_pipeline_decision(
    BASE,
    "Phase 3 — business-flows",
    f"flows={len(flows)}, orphan_tasks={len(orphan_tasks_list)}, "
    f"ghost_states={len(global_ghost_states)}, "
    f"orphan_states={len(global_orphan_states)}, "
    f"high_freq_uncovered={len(high_freq_uncovered)}, "
    f"total_gaps={total_gaps}",
    shard=args.get("shard")
)

# ── Summary ───────────────────────────────────────────────────────────────────
print(f"Flows generated: {len(flows)}")
print(f"Total flow nodes: {sum(len(f['nodes']) for f in flows)}")
print(f"Gap flags: {total_gaps}")
print(f"Ghost states (CRITICAL): {len(global_ghost_states)}")
print(f"Orphan states: {len(global_orphan_states)}")
print(f"High-freq uncovered: {len(high_freq_uncovered)}")
print(f"Orphan tasks: {orphan_count} ORPHAN + {indep_count} INDEPENDENT")
print(f"\nAll files written to {OUT}/")
