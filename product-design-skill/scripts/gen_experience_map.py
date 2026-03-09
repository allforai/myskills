#!/usr/bin/env python3
"""Phase 4: Generate experience-map from journey-emotion-map + task-inventory.

Replaces gen_screen_map.py. Organizes screens into operation lines with
emotion context, ux intent, and continuity metrics.

When view-objects.json is available, screens are enriched with real VO fields,
interaction types, data_fields, actions, flow_context, and states.

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

# ── CRUD → preferred VO view_type mapping ─────────────────────────────────────
CRUD_TO_VIEW_TYPE = {
    "C": ["create_form"],
    "R": ["list_item", "detail"],
    "U": ["edit_form"],
    "D": ["state_action", "list_item"],  # delete often on list or state_action
}

# ── View type → Chinese name suffix ──────────────────────────────────────────
VIEW_TYPE_NAMES = {
    "list_item": "列表",
    "detail": "详情",
    "create_form": "创建",
    "edit_form": "编辑",
    "state_action": "操作",
}

# ── Default states per interaction type ──────────────────────────────────────
DEFAULT_STATES = {
    "MG1": {"empty": "暂无数据，显示空态插图", "loading": "骨架屏占位", "error": "加载失败，显示重试按钮", "success": "数据列表正常展示"},
    "MG2-L": {"empty": "暂无数据，引导创建", "loading": "骨架屏占位", "error": "加载失败，显示重试按钮", "success": "数据列表正常展示"},
    "MG2-C": {"empty": "空表单，所有字段待填写", "loading": "提交中，按钮禁用+加载指示器", "error": "提交失败，字段标红+错误提示", "success": "创建成功，跳转或提示"},
    "MG2-E": {"empty": "表单回填旧值", "loading": "提交中，按钮禁用", "error": "保存失败，字段标红", "success": "保存成功，返回"},
    "MG2-D": {"empty": "数据不存在，显示404提示", "loading": "骨架屏占位", "error": "加载失败，显示重试", "success": "详情正常展示"},
    "MG3": {"empty": "无待处理项", "loading": "操作执行中", "error": "操作失败，显示原因", "success": "状态变更成功，刷新列表"},
    "MG4": {"empty": "无待审核项", "loading": "提交审批中", "error": "审批失败", "success": "审批完成"},
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


# ── VO matching helpers ──────────────────────────────────────────────────────

def _build_vo_lookup(view_objects):
    """Build {(entity_name, view_type): vo} lookup from view_objects list.

    When multiple VOs share (entity_name, view_type), the first one wins.
    """
    lookup = {}
    for vo in view_objects:
        key = (vo.get("entity_name", ""), vo.get("view_type", ""))
        if key not in lookup:
            lookup[key] = vo
    return lookup


def _find_vo_for_task(task, crud_type, vo_lookup):
    """Find the best matching VO for a task based on module and CRUD type.

    Returns the VO dict or None if no match.
    """
    module = task.get("module", task.get("owner_role", ""))
    preferred_types = CRUD_TO_VIEW_TYPE.get(crud_type, ["list_item"])

    for vt in preferred_types:
        vo = vo_lookup.get((module, vt))
        if vo:
            return vo
    return None


def _vo_screen_name(vo, task_pairs=None):
    """Generate a human-readable screen name from a VO + task context.

    Priority: VO display_name > task-derived Chinese name > entity_suffix fallback.
    """
    # 1. VO itself may carry a display_name (best source)
    if vo.get("display_name"):
        return vo["display_name"]

    entity = vo.get("entity_name", "unknown")
    vtype = vo.get("view_type", "")
    suffix = VIEW_TYPE_NAMES.get(vtype, vtype)

    # 2. Derive Chinese name from first task name (e.g. "查看订单列表" → "订单列表")
    if task_pairs:
        name = _derive_screen_name_from_tasks(task_pairs, suffix)
        if name:
            return name

    # 3. Fallback: entity + suffix
    return f"{entity}_{suffix}"


def _derive_screen_name_from_tasks(task_pairs, suffix_hint=""):
    """Derive a meaningful Chinese screen name from task names.

    Strips CRUD verb prefixes to get the core noun phrase.
    e.g. "查看订单列表" → "订单列表"
         "创建配送单"   → "创建配送单"   (C → keep verb as it's the screen purpose)
         "修改用户信息" → "编辑用户信息"
         "注册账户"     → "注册账户"     (short name, keep as-is)
    """
    if not task_pairs:
        return ""

    # Use first task name as primary source (task_name is canonical, name is legacy)
    first_task = task_pairs[0][1] if task_pairs else {}
    first_name = first_task.get("task_name", first_task.get("name", ""))
    if not first_name:
        return ""

    # For short names (≤4 chars), keep as-is — they're already concise
    if len(first_name) <= 4:
        return first_name

    # Strip READ verb prefixes to extract the core noun (read verbs are redundant for screen names)
    read_prefixes = ["查看", "浏览", "搜索", "筛选", "导出", "统计"]
    core = first_name
    stripped = False
    for prefix in read_prefixes:
        if core.startswith(prefix):
            core = core[len(prefix):]
            stripped = True
            break

    # If no READ prefix stripped, return original name as-is
    # (C/U/D verbs are meaningful for screen purpose: "创建订单", "编辑资料", "删除记录")
    if not stripped:
        return first_name

    # For READ screens: if core already contains a view type word, don't append suffix
    view_type_words = ["列表", "详情", "概览", "面板", "报表", "统计", "记录"]
    if any(w in core for w in view_type_words):
        return core

    # Append suffix only if core is a bare noun (e.g. "订单" → "订单列表")
    if suffix_hint and core:
        return f"{core}{suffix_hint}"

    return core or first_name


def _vo_description(vo):
    """Generate a description from VO fields and type."""
    vtype = vo.get("view_type", "")
    entity = vo.get("entity_name", "unknown")
    fields = vo.get("fields", [])
    field_names = [f.get("name", "") for f in fields[:5]]
    field_str = ", ".join(field_names) if field_names else "no fields"

    type_desc = {
        "list_item": "列表视图",
        "detail": "详情视图",
        "create_form": "创建表单",
        "edit_form": "编辑表单",
        "state_action": "状态操作",
    }
    desc = type_desc.get(vtype, vtype)
    return f"{entity} {desc} — fields: {field_str}"


def build_screens_for_node(node_tasks, tasks_inv, screen_counter,
                           ux_intent="", emotion_intensity=5, vo_lookup=None):
    """Build screen objects from a list of task IDs. Returns (screens, updated_counter).

    When vo_lookup is provided, screens are enriched with VO data (name, fields,
    interaction_type, actions, states). Falls back to generic names when no VO matches.
    """
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
            tname = task.get("task_name", task.get("name", tid))
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

        # Derive implementation contract
        contract = infer_contract(ux_intent, dominant_crud, emotion_intensity)

        # ── Try VO enrichment ──
        matched_vo = None
        if vo_lookup:
            # Use the first task to find a matching VO
            first_task = task_pairs[0][1] if task_pairs else {}
            matched_vo = _find_vo_for_task(first_task, dominant_crud, vo_lookup)

        if matched_vo:
            # Enriched screen from VO
            interaction_type = matched_vo.get("interaction_type", "")
            screen_name = _vo_screen_name(matched_vo, task_pairs)
            description = _vo_description(matched_vo)

            # Override contract pattern from interaction_type when available
            if interaction_type:
                contract["interaction_type"] = interaction_type

            # Build enriched actions from VO actions
            vo_actions = matched_vo.get("actions", [])

            screen = {
                "id": sid,
                "name": screen_name,
                "description": description,
                "route_type": "push",
                "tasks": task_ids,
                "actions": actions,
                "vo_actions": vo_actions,
                "primary_action": primary,
                "vo_ref": matched_vo.get("id", ""),
                "api_ref": matched_vo.get("api_ref", ""),
                "interaction_type": interaction_type,
                "data_fields": matched_vo.get("fields", []),
                "states": DEFAULT_STATES.get(interaction_type, {}),
                "non_negotiable": contract["required_behaviors"][:2] if contract["required_behaviors"] else [],
                "implementation_contract": contract,
            }
        else:
            # Fallback: derive name from tasks, then module
            suffix = VIEW_TYPE_NAMES.get(
                CRUD_TO_VIEW_TYPE.get(dominant_crud, ["list_item"])[0], ""
            )
            fallback_name = _derive_screen_name_from_tasks(task_pairs, suffix) or primary
            fallback_desc = f"{fallback_name} — {', '.join(a['label'] for a in actions[:3])}"
            screen = {
                "id": sid,
                "name": fallback_name,
                "description": fallback_desc,
                "route_type": "push",
                "tasks": task_ids,
                "actions": actions,
                "primary_action": primary,
                "non_negotiable": contract["required_behaviors"][:2] if contract["required_behaviors"] else [],
                "implementation_contract": contract,
            }

        screens.append(screen)

    return screens, screen_counter


def _compute_flow_context(operation_lines):
    """Compute flow_context (prev/next/entry_points/exit_points) for each screen.

    Iterates through operation_lines → nodes → screens in order and records
    sequential prev/next relationships within each operation line.
    Also infers entry_points and exit_points from VO navigate actions.
    """
    # Build screen_id → screen object mapping (for VO action cross-referencing)
    all_screens = {}  # sid → screen
    vo_to_screen = {}  # vo_ref → [screen_ids]

    for ol in operation_lines:
        for node in ol.get("nodes", []):
            for s in node.get("screens", []):
                all_screens[s["id"]] = s
                vo_ref = s.get("vo_ref", "")
                if vo_ref:
                    vo_to_screen.setdefault(vo_ref, []).append(s["id"])

    # For each operation line, compute sequential flow
    for ol in operation_lines:
        # Collect all screens in node order
        ordered_screens = []
        for node in ol.get("nodes", []):
            for s in node.get("screens", []):
                ordered_screens.append(s["id"])

        for i, sid in enumerate(ordered_screens):
            screen = all_screens.get(sid)
            if not screen:
                continue

            prev_ids = [ordered_screens[i - 1]] if i > 0 else []
            next_ids = [ordered_screens[i + 1]] if i < len(ordered_screens) - 1 else []

            # Infer entry_points: find VO actions from OTHER screens that navigate to this screen's VO
            entry_points = []
            my_vo = screen.get("vo_ref", "")
            if my_vo:
                for other_sid, other_screen in all_screens.items():
                    if other_sid == sid:
                        continue
                    for act in other_screen.get("vo_actions", []):
                        if act.get("type") == "navigate" and act.get("target_vo") == my_vo:
                            entry_points.append(other_sid)

            # Infer exit_points: VO navigate actions from this screen
            exit_points = []
            for act in screen.get("vo_actions", []):
                if act.get("type") == "navigate" and act.get("target_vo"):
                    target_vo = act["target_vo"]
                    target_sids = vo_to_screen.get(target_vo, [])
                    exit_points.extend(target_sids)
                elif act.get("type") == "navigate" and act.get("nav_mode") == "back":
                    exit_points.extend(prev_ids)

            screen["flow_context"] = {
                "prev": prev_ids,
                "next": next_ids,
                "entry_points": list(set(entry_points)),
                "exit_points": list(set(exit_points)),
            }


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

    # ── load view objects (optional enhancement) ──
    view_objects = C.load_view_objects(BASE)
    vo_lookup = _build_vo_lookup(view_objects) if view_objects else {}
    if vo_lookup:
        print(f"  VO: loaded {len(view_objects)} view objects, {len(vo_lookup)} unique (entity, type) keys")

    # ── build flow→tasks mapping ──
    # Support both "id" and "flow_id" fields, and normalize F1→F001 format
    flow_by_id = {}
    if flows:
        for f in flows:
            fid = f.get("id") or f.get("flow_id", "")
            if fid:
                flow_by_id[fid] = f
                # Also register zero-padded variant: F1→F001, F2→F002
                import re as _re
                m = _re.match(r'^(F)(\d+)$', fid)
                if m:
                    padded = f"{m.group(1)}{int(m.group(2)):03d}"
                    flow_by_id[padded] = f

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
                vo_lookup=vo_lookup,
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

    # ── compute flow_context for all screens ──
    if vo_lookup:
        _compute_flow_context(operation_lines)

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
    vo_enriched = sum(1 for sid in screen_index if any(
        s.get("vo_ref")
        for ol in operation_lines
        for n in ol.get("nodes", [])
        for s in n.get("screens", [])
        if s["id"] == sid
    ))

    if total_screens == 0:
        print("ERROR: 0 screens generated — check that business-flows nodes have task_ref matching task-inventory IDs", file=sys.stderr)
        sys.exit(1)

    vo_msg = f", {vo_enriched} VO-enriched" if vo_enriched else ""
    print(f"OK: {out_path} ({len(operation_lines)} lines, {total_nodes} nodes, {total_screens} screens{vo_msg})")

    # ── generate report ──
    report_lines = [
        "# Experience Map Report\n",
        f"> Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n",
        f"## Summary\n",
        f"- Operation lines: {len(operation_lines)}",
        f"- Total nodes: {total_nodes}",
        f"- Total screens: {total_screens}",
    ]
    if vo_enriched:
        report_lines.append(f"- VO-enriched screens: {vo_enriched}")
    report_lines.append("")
    report_lines.append("## Operation Lines\n")

    for ol in operation_lines:
        report_lines.append(f"### {ol['id']} {ol['name']}")
        report_lines.append(f"- Role: {ol['role']}")
        report_lines.append(f"- Source journey: {ol['source_journey']}")
        report_lines.append(f"- Steps: {ol['continuity']['total_steps']}")
        report_lines.append("")
        for node in ol["nodes"]:
            screens_str = ", ".join(f"{s['id']}({s['name']})" for s in node["screens"])
            vo_tags = ""
            for s in node["screens"]:
                if s.get("vo_ref"):
                    vo_tags += f" [{s['vo_ref']}:{s.get('interaction_type', '')}]"
            report_lines.append(
                f"  {node['seq']}. {node['action']} "
                f"[{node['emotion_state']} {node['emotion_intensity']}/10] "
                f"→ {screens_str or 'no screens'}{vo_tags}"
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
        "vo_enriched_screens": vo_enriched,
    })


if __name__ == "__main__":
    main()
