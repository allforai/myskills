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


# ── Implementation contract presets ──────────────────────────────────────────
CONTRACT_PATTERNS = {
    "bottom-sheet": {
        "forbidden": ["page-route", "full-screen-modal"],
        "required_behaviors": ["swipe-to-dismiss", "backdrop-tap-close"],
    },
    "full-page": {
        "forbidden": ["bottom-sheet", "inline-expand"],
        "required_behaviors": ["back-navigation", "scroll-to-top"],
    },
    "modal-picker": {
        "forbidden": ["page-route", "inline-expand"],
        "required_behaviors": ["backdrop-tap-close", "keyboard-dismiss"],
    },
    "multi-step-form": {
        "forbidden": ["single-submit", "inline-edit"],
        "required_behaviors": ["step-indicator", "back-to-previous-step", "draft-save"],
    },
    "standard-page": {
        "forbidden": [],
        "required_behaviors": ["back-navigation"],
    },
}


def infer_contract(ux_intent, crud_type, emotion_intensity):
    """Infer implementation contract from UX intent, CRUD type, and emotion intensity."""
    intent_lower = (ux_intent or "").lower()

    if any(kw in intent_lower for kw in ["quick", "overlay", "confirm", "dismiss"]):
        pattern = "bottom-sheet"
    elif any(kw in intent_lower for kw in ["detail", "full", "comprehensive"]):
        pattern = "full-page"
    elif any(kw in intent_lower for kw in ["select", "pick", "choose"]):
        pattern = "modal-picker"
    elif crud_type == "C" and emotion_intensity >= 7:
        pattern = "multi-step-form"
    else:
        pattern = "standard-page"

    preset = CONTRACT_PATTERNS[pattern]
    return {
        "pattern": pattern,
        "forbidden": preset["forbidden"],
        "required_behaviors": preset["required_behaviors"],
    }


def build_screens_for_node(node_tasks, tasks_inv, screen_counter, ux_intent="", emotion_intensity=5):
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

        # Determine primary action and dominant CRUD
        primary = actions[0]["label"] if actions else module
        dominant_crud = actions[0]["crud"] if actions else "R"
        screen_name = f"{module}_screen"

        # Derive implementation contract
        contract = infer_contract(ux_intent, dominant_crud, emotion_intensity)

        screens.append({
            "id": sid,
            "name": screen_name,
            "description": f"{module} operations",
            "route_type": "push",
            "tasks": task_ids,
            "actions": actions,
            "primary_action": primary,
            "non_negotiable": contract["required_behaviors"][:2] if contract["required_behaviors"] else [],
            "implementation_contract": contract,
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
            # Support both task_ref (canonical) and task_id (legacy)
            node_task_id = flow_node.get("task_ref", flow_node.get("task_id", ""))
            node_tasks = [node_task_id] if node_task_id and node_task_id in tasks_inv else []

            # Build screens for this node
            node_screens, screen_counter = build_screens_for_node(
                node_tasks, tasks_inv, screen_counter,
                ux_intent=en.get("design_hint", ""),
                emotion_intensity=en.get("intensity", 5),
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
            ol_id = f"OL{jl_id[2:]}"
            for s in node_screens:
                sid = s["id"]
                if sid not in screen_index:
                    screen_index[sid] = {"name": s["name"], "appears_in": []}
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

    if total_screens == 0:
        print("ERROR: 0 screens generated — check that business-flows nodes have task_ref matching task-inventory IDs", file=sys.stderr)
        sys.exit(1)

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
