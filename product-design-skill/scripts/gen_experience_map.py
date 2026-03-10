#!/usr/bin/env python3
"""Phase 4: Generate experience-map from journey-emotion-map + task-inventory.

Produces screen skeletons with heuristic interaction type assignment.
Uses task characteristics (name, category, audience, CRUD indicators)
to infer appropriate interaction types without LLM.

Usage:
    python3 gen_experience_map.py <BASE_PATH> [--mode auto] [--shard NAME]
"""
import sys, os, json, datetime, re

sys.path.insert(0, os.path.dirname(__file__))
import _common as C

# ── View type → Chinese name suffix ──────────────────────────────────────────
VIEW_TYPE_NAMES = {
    "list_item": "列表",
    "detail": "详情",
    "create_form": "创建",
    "edit_form": "编辑",
    "state_action": "操作",
}

# ── Default states per interaction type (all 37 types from interaction-types.md) ──
DEFAULT_STATES = {
    # MG 管理/CRUD 类
    "MG1":    {"empty": "暂无数据，显示空态插图", "loading": "骨架屏占位", "error": "加载失败，显示重试按钮", "success": "数据列表正常展示"},
    "MG2-L":  {"empty": "暂无数据，引导创建", "loading": "骨架屏占位", "error": "加载失败，显示重试按钮", "success": "数据列表正常展示"},
    "MG2-C":  {"empty": "空表单，所有字段待填写", "loading": "提交中，按钮禁用+加载指示器", "error": "提交失败，字段标红+错误提示", "success": "创建成功，跳转或提示"},
    "MG2-D":  {"empty": "数据不存在", "loading": "骨架屏占位", "error": "加载失败", "success": "详情正常展示"},
    "MG2-E":  {"empty": "空表单", "loading": "保存中", "error": "保存失败", "success": "保存成功"},
    "MG3":    {"empty": "无待操作项", "loading": "操作执行中", "error": "操作失败", "success": "操作成功，状态已变更"},
    "MG4":    {"empty": "无待审核项", "loading": "提交中", "error": "审核操作失败", "success": "审核通过/驳回成功"},
    "MG5":    {"empty": "暂无关联数据", "loading": "骨架屏占位", "error": "加载失败", "success": "主从数据正常展示"},
    "MG6":    {"empty": "空分类树", "loading": "加载分类", "error": "加载失败", "success": "分类树正常展示"},
    "MG7":    {"empty": "暂无数据", "loading": "加载图表", "error": "数据加载失败", "success": "仪表盘正常展示"},
    "MG8":    {"empty": "默认配置", "loading": "保存中", "error": "保存失败", "success": "配置已保存"},
    # CT 内容消费类
    "CT1":    {"empty": "暂无内容，引导关注", "loading": "骨架屏占位", "error": "加载失败", "success": "Feed流正常展示"},
    "CT2":    {"empty": "内容不存在", "loading": "骨架屏占位", "error": "加载失败", "success": "内容正常展示"},
    "CT3":    {"empty": "空个人资料", "loading": "加载中", "error": "加载失败", "success": "个人资料展示"},
    "CT4":    {"empty": "无可翻阅内容", "loading": "加载卡片", "error": "加载失败", "success": "卡片正常展示"},
    "CT5":    {"empty": "无可播放内容", "loading": "缓冲中", "error": "播放失败", "success": "播放中"},
    "CT6":    {"empty": "无图片", "loading": "加载图库", "error": "加载失败", "success": "图库正常展示"},
    "CT7":    {"empty": "无搜索结果", "loading": "搜索中", "error": "搜索失败", "success": "搜索结果展示"},
    "CT8":    {"empty": "无短视频", "loading": "加载中", "error": "加载失败", "success": "短视频播放中"},
    # EC 电商交易类
    "EC1":    {"empty": "商品不存在", "loading": "加载商品", "error": "加载失败", "success": "商品详情展示"},
    "EC2":    {"empty": "购物车为空", "loading": "处理中", "error": "支付失败", "success": "支付成功"},
    "EC3":    {"empty": "无物流信息", "loading": "查询物流", "error": "查询失败", "success": "物流信息展示"},
    # WK 协作办公类
    "WK1":    {"empty": "暂无消息", "loading": "加载消息", "error": "加载失败", "success": "消息列表展示"},
    "WK2":    {"empty": "暂无频道", "loading": "加载频道", "error": "加载失败", "success": "频道列表展示"},
    "WK3":    {"empty": "空白文档", "loading": "加载文档", "error": "加载失败", "success": "编辑器就绪"},
    "WK4":    {"empty": "空白画布", "loading": "加载画布", "error": "加载失败", "success": "画布就绪"},
    "WK5":    {"empty": "空看板", "loading": "加载看板", "error": "加载失败", "success": "看板正常展示"},
    "WK6":    {"empty": "无排期数据", "loading": "加载甘特图", "error": "加载失败", "success": "甘特图正常展示"},
    "WK7":    {"empty": "空目录", "loading": "加载文件列表", "error": "加载失败", "success": "文件列表展示"},
    # RT 通讯实时类
    "RT1":    {"empty": "无通话记录", "loading": "连接中", "error": "连接失败", "success": "通话中"},
    "RT2":    {"empty": "直播未开始", "loading": "加载直播", "error": "连接失败", "success": "直播中"},
    "RT3":    {"empty": "收件箱为空", "loading": "加载邮件", "error": "加载失败", "success": "邮件列表展示"},
    "RT4":    {"empty": "暂无通知", "loading": "加载通知", "error": "加载失败", "success": "通知列表展示"},
    # SB 审核提交类
    "SB1":    {"empty": "空表单", "loading": "提交审核中", "error": "提交失败", "success": "已提交，等待审核"},
    # SY 引导系统类
    "SY1":    {"empty": "引导未开始", "loading": "加载引导", "error": "加载失败", "success": "引导进行中"},
    "SY2":    {"empty": "表单待填写", "loading": "提交中", "error": "验证失败", "success": "完成提交"},
    # TU TUI/CLI 类
    "TU1":    {"empty": "等待输入", "loading": "执行中", "error": "命令执行失败", "success": "执行完成"},
    "TU2":    {"empty": "无选项", "loading": "加载菜单", "error": "加载失败", "success": "菜单展示"},
    "TU3":    {"empty": "无日志", "loading": "加载日志流", "error": "连接断开", "success": "日志流输出中"},
    "TU4":    {"empty": "无任务", "loading": "执行中", "error": "任务失败", "success": "任务完成"},
}

# ── Platform profiles by audience_type ────────────────────────────────────────
_PLATFORM_PROFILES = {
    "consumer": {
        "platform": "mobile",
        "navigation": "bottom_tab",
        "layout": "single_column",
    },
    "professional": {
        "platform": "desktop",
        "navigation": "sidebar",
        "layout": "master_detail",
    },
}

# ── Simplified contract patterns ──────────────────────────────────────────────
# LLM will assign correct patterns; this is a minimal fallback.
CONTRACT_PATTERNS = {
    "standard-page": {
        "forbidden": [],
        "required_behaviors": ["back-navigation"],
    },
    "full-page": {
        "forbidden": ["bottom-sheet", "inline-expand"],
        "required_behaviors": ["back-navigation", "scroll-to-top"],
    },
    "bottom-sheet": {
        "forbidden": ["page-route", "full-screen-modal"],
        "required_behaviors": ["swipe-to-dismiss", "backdrop-tap-close"],
    },
    "modal-picker": {
        "forbidden": ["page-route", "inline-expand"],
        "required_behaviors": ["backdrop-tap-close", "keyboard-dismiss"],
    },
}


# ── Interaction type inference ────────────────────────────────────────────────
# Heuristic rules based on task characteristics — no business-specific keywords.
# Priority: first matching rule wins.

def _infer_interaction_type(task, audience_type=""):
    """Delegate to _common.infer_interaction_type (single source of truth)."""
    return C.infer_interaction_type(task, audience_type=audience_type)


# ── VO matching helpers ──────────────────────────────────────────────────────

def _build_vo_lookup(view_objects):
    """Build {(entity_name, view_type): vo} lookup from view_objects list."""
    lookup = {}
    for vo in view_objects:
        key = (vo.get("entity_name", ""), vo.get("view_type", ""))
        if key not in lookup:
            lookup[key] = vo
    return lookup


def _find_vo_for_task(task, vo_lookup, audience_type=""):
    """Find matching VO for a task by module + CRUD-aligned view_type.

    Uses infer_interaction_type to determine CRUD, then picks the VO
    whose view_type matches the task's operation.
    """
    module = task.get("module", task.get("owner_role", ""))
    _, crud = C.infer_interaction_type(task, audience_type=audience_type)

    # CRUD → preferred view_type order
    crud_vt_order = {
        "C": ("create_form", "detail", "list_item"),
        "R": ("detail", "list_item"),
        "U": ("edit_form", "state_action", "detail"),
        "D": ("state_action", "detail", "list_item"),
    }
    preferred = crud_vt_order.get(crud, ("detail", "list_item"))

    for vt in preferred:
        vo = vo_lookup.get((module, vt))
        if vo:
            return vo
    # Fallback: any VO for this module
    for vt in ("list_item", "detail", "create_form", "edit_form", "state_action"):
        vo = vo_lookup.get((module, vt))
        if vo:
            return vo
    return None


def _vo_screen_name(vo, task_pairs=None):
    """Generate screen name from VO or task context."""
    if vo.get("display_name"):
        return vo["display_name"]

    entity = vo.get("entity_name", "unknown")
    vtype = vo.get("view_type", "")
    suffix = VIEW_TYPE_NAMES.get(vtype, vtype)

    # Use first task name if available
    if task_pairs:
        first_task = task_pairs[0][1] if task_pairs else {}
        name = first_task.get("task_name", first_task.get("name", ""))
        if name:
            return name

    return f"{entity}_{suffix}"


# ── Screen builder ───────────────────────────────────────────────────────────

def build_screens_for_node(node_tasks, tasks_inv, screen_counter,
                           ux_intent="", emotion_intensity=5, vo_lookup=None,
                           audience_type=""):
    """Build minimal screen skeletons from task IDs.

    Returns (screens, updated_counter).
    # LLM will enrich fields, actions, states
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

        task_ids = [tid for tid, _ in task_pairs]

        # Primary action = first task name
        first_task = task_pairs[0][1] if task_pairs else {}
        primary = first_task.get("task_name", first_task.get("name", module))

        # Infer interaction type from task characteristics
        interaction_type, crud_type = _infer_interaction_type(first_task, audience_type)

        # Platform metadata
        profile = _PLATFORM_PROFILES.get(audience_type, {})
        platform_meta = {
            "platform": profile.get("platform", "unknown"),
            "navigation": profile.get("navigation", ""),
            "layout": profile.get("layout", ""),
        } if profile else {}

        # Simple contract
        contract = {
            "pattern": "standard-page",
            "forbidden": [],
            "required_behaviors": ["back-navigation"],
            "interaction_type": interaction_type,
        }

        # Try VO matching by entity reference (ID-based, not keyword-based)
        matched_vo = None
        if vo_lookup:
            matched_vo = _find_vo_for_task(first_task, vo_lookup, audience_type)

        if matched_vo:
            screen_name = _vo_screen_name(matched_vo, task_pairs)
            # Include ALL VO fields without filtering
            data_fields = matched_vo.get("fields", [])
            vo_actions = matched_vo.get("actions", [])
            vo_ref = matched_vo.get("id", "")
            # Task-inferred interaction_type takes priority (it's task-specific);
            # VO interaction_type is entity-level fallback only
            # interaction_type already set by _infer_interaction_type above
        else:
            screen_name = primary
            data_fields = []
            vo_actions = []
            vo_ref = ""

        # Minimal actions: just the task name as primary action
        actions = [{"label": primary, "task_ref": task_ids[0] if task_ids else ""}]

        screen = {
            "id": sid,
            "name": screen_name,
            "description": primary,  # LLM will generate smart descriptions
            "route_type": "push",
            **platform_meta,
            "tasks": task_ids,
            "actions": actions,
            "vo_actions": vo_actions,
            "primary_action": primary,
            "vo_ref": vo_ref,
            "interaction_type": interaction_type,
            "data_fields": data_fields,
            "states": DEFAULT_STATES.get(interaction_type, {}),
            "implementation_contract": contract,
        }

        screens.append(screen)

    return screens, screen_counter


def _compute_flow_context(operation_lines):
    """Compute flow_context (prev/next/entry_points/exit_points) for each screen.

    Iterates through operation_lines -> nodes -> screens in order and records
    sequential prev/next relationships within each operation line.
    """
    all_screens = {}
    vo_to_screen = {}

    for ol in operation_lines:
        for node in ol.get("nodes", []):
            for s in node.get("screens", []):
                all_screens[s["id"]] = s
                vo_ref = s.get("vo_ref", "")
                if vo_ref:
                    vo_to_screen.setdefault(vo_ref, []).append(s["id"])

    for ol in operation_lines:
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

            # Entry/exit points from VO navigate actions
            entry_points = []
            my_vo = screen.get("vo_ref", "")
            if my_vo:
                for other_sid, other_screen in all_screens.items():
                    if other_sid == sid:
                        continue
                    for act in other_screen.get("vo_actions", []):
                        if act.get("type") == "navigate" and act.get("target_vo") == my_vo:
                            entry_points.append(other_sid)

            exit_points = []
            for act in screen.get("vo_actions", []):
                if act.get("type") == "navigate" and act.get("target_vo"):
                    target_sids = vo_to_screen.get(act["target_vo"], [])
                    exit_points.extend(target_sids)
                elif act.get("type") == "navigate" and act.get("nav_mode") == "back":
                    exit_points.extend(prev_ids)

            screen["flow_context"] = {
                "prev": prev_ids,
                "next": next_ids,
                "entry_points": list(set(entry_points)),
                "exit_points": list(set(exit_points)),
            }


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: gen_experience_map.py <BASE_PATH> [--mode auto] [--shard NAME]")
        sys.exit(1)

    BASE = sys.argv[1]

    # Parse optional args
    args = {}
    i = 2
    while i < len(sys.argv):
        if sys.argv[i].startswith("--") and i + 1 < len(sys.argv):
            args[sys.argv[i][2:]] = sys.argv[i + 1]
            i += 2
        else:
            i += 1

    shard = args.get("shard")

    # ── Load inputs ──
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

    # ── Build role -> audience_type mapping ──
    roles_full = C.load_role_profiles_full(BASE) if hasattr(C, 'load_role_profiles_full') else []
    role_audience = {}
    for r in roles_full:
        rid = r.get("id", r.get("role_id", ""))
        role_audience[rid] = r.get("audience_type", "professional")
    if role_audience:
        print(f"  Roles: {', '.join(f'{k}={v}' for k, v in role_audience.items())}")

    # ── Load view objects (optional) ──
    view_objects = C.load_view_objects(BASE)
    vo_lookup = _build_vo_lookup(view_objects) if view_objects else {}
    if vo_lookup:
        print(f"  VO: loaded {len(view_objects)} view objects, {len(vo_lookup)} unique (entity, type) keys")

    # ── Build flow -> tasks mapping ──
    import re as _re
    flow_by_id = {}
    if flows:
        for f in flows:
            fid = f.get("id") or f.get("flow_id", "")
            if fid:
                flow_by_id[fid] = f
                m = _re.match(r'^(F)(\d+)$', fid)
                if m:
                    num = int(m.group(2))
                    flow_by_id[f"{m.group(1)}{num:02d}"] = f
                    flow_by_id[f"{m.group(1)}{num:03d}"] = f

    # ── Generate operation lines ──
    operation_lines = []
    screen_index = {}
    screen_counter = 0
    _screen_dedup = {}

    for jl in journey_lines:
        jl_id = jl["id"]
        source_flow_id = jl.get("source_flow", "")
        flow = flow_by_id.get(source_flow_id, {})
        flow_nodes = C.get_flow_nodes(flow) if flow else []

        jl_role = jl.get("role", "")
        jl_audience = role_audience.get(jl_role, "professional")

        nodes = []
        for en in jl.get("emotion_nodes", []):
            step = en["step"]

            flow_node = flow_nodes[step - 1] if step - 1 < len(flow_nodes) else {}
            node_task_id = flow_node.get("task_ref", flow_node.get("task_id", ""))
            node_tasks = [node_task_id] if node_task_id and node_task_id in tasks_inv else []

            dedup_key = (frozenset(node_tasks), jl_audience) if node_tasks else None
            if dedup_key and dedup_key in _screen_dedup:
                node_screens = _screen_dedup[dedup_key]
            else:
                node_screens, screen_counter = build_screens_for_node(
                    node_tasks, tasks_inv, screen_counter,
                    ux_intent=en.get("design_hint", ""),
                    emotion_intensity=en.get("intensity", 5),
                    vo_lookup=vo_lookup,
                    audience_type=jl_audience,
                )
                if dedup_key:
                    _screen_dedup[dedup_key] = node_screens

            node_id = f"N{jl_id[2:]}{step:02d}"
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

    # ── Compute flow_context for all screens ──
    if vo_lookup:
        _compute_flow_context(operation_lines)

    result = {
        "operation_lines": operation_lines,
        "screen_index": screen_index,
        "generated_at": datetime.datetime.now().isoformat(),
    }

    # ── Write output ──
    out_dir = os.path.join(BASE, "experience-map")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "experience-map.json")
    C.write_json(out_path, result)

    # ── Summary ──
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
    # Count interaction type distribution
    itype_dist = {}
    for ol in operation_lines:
        for n in ol.get("nodes", []):
            for s in n.get("screens", []):
                it = s.get("interaction_type", "MG1")
                itype_dist[it] = itype_dist.get(it, 0) + 1

    print(f"OK: {out_path} ({len(operation_lines)} lines, {total_nodes} nodes, {total_screens} screens{vo_msg})")
    print(f"  Interaction types: {dict(sorted(itype_dist.items()))}")

    # ── Report ──
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
                f"-> {screens_str or 'no screens'}{vo_tags}"
            )
        report_lines.append("")

    report_path = os.path.join(out_dir, "experience-map-report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    # ── Pipeline decision ──
    C.append_pipeline_decision(BASE, "experience-map", {
        "operation_line_count": len(operation_lines),
        "total_nodes": total_nodes,
        "total_screens": total_screens,
        "vo_enriched_screens": vo_enriched,
    }, shard=shard)


if __name__ == "__main__":
    main()
