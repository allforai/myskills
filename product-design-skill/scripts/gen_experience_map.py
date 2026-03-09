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
    "MG2-E":  {"empty": "表单回填旧值", "loading": "提交中，按钮禁用", "error": "保存失败，字段标红", "success": "保存成功，返回"},
    "MG2-D":  {"empty": "数据不存在，显示404提示", "loading": "骨架屏占位", "error": "加载失败，显示重试", "success": "详情正常展示"},
    "MG2-ST": {"empty": "无可操作项", "loading": "状态变更中", "error": "状态流转失败", "success": "状态已更新"},
    "MG3":    {"empty": "无待处理项", "loading": "操作执行中", "error": "操作失败，显示原因", "success": "状态变更成功，刷新列表"},
    "MG4":    {"empty": "无待审核项", "loading": "提交审批中", "error": "审批失败", "success": "审批完成"},
    "MG5":    {"empty": "主实体不存在", "loading": "加载主从数据", "error": "主从数据加载失败", "success": "主从详情正常展示"},
    "MG6":    {"empty": "空树，显示创建根节点引导", "loading": "加载树结构", "error": "加载失败", "success": "树结构正常展示"},
    "MG7":    {"empty": "暂无数据", "loading": "加载统计数据", "error": "数据加载失败", "success": "仪表盘正常展示"},
    "MG8":    {"empty": "加载默认配置", "loading": "保存配置中", "error": "保存失败", "success": "配置已保存"},
    # CT 内容消费类
    "CT1":    {"empty": "暂无内容，刷新或探索", "loading": "加载内容流", "error": "加载失败，下拉重试", "success": "内容流正常展示"},
    "CT2":    {"empty": "内容不存在", "loading": "加载内容", "error": "加载失败", "success": "内容正常展示"},
    "CT3":    {"empty": "用户不存在", "loading": "加载个人主页", "error": "加载失败", "success": "个人主页正常展示"},
    "CT4":    {"empty": "队列已空，稍后再来", "loading": "加载卡片", "error": "加载失败", "success": "卡片展示中"},
    "CT5":    {"empty": "无可播放媒体", "loading": "缓冲中", "error": "播放失败", "success": "播放中"},
    "CT6":    {"empty": "暂无图片", "loading": "加载图片", "error": "加载失败", "success": "相册正常展示"},
    "CT7":    {"empty": "未找到结果", "loading": "搜索中", "error": "搜索失败", "success": "搜索结果展示"},
    "CT8":    {"empty": "无更多内容", "loading": "加载视频", "error": "播放失败", "success": "自动播放中"},
    # EC 电商交易类
    "EC1":    {"empty": "商品不存在", "loading": "加载商品详情", "error": "加载失败", "success": "商品详情正常展示"},
    "EC2":    {"empty": "购物车为空", "loading": "结算中", "error": "结算失败", "success": "订单创建成功"},
    "EC3":    {"empty": "无物流信息", "loading": "加载物流", "error": "查询失败", "success": "物流时间线展示"},
    # WK 协作办公类
    "WK1":    {"empty": "暂无消息", "loading": "加载消息", "error": "发送失败", "success": "消息已发送"},
    "WK2":    {"empty": "暂无频道", "loading": "加载频道列表", "error": "加载失败", "success": "频道列表展示"},
    "WK3":    {"empty": "空白文档", "loading": "加载文档", "error": "保存失败", "success": "文档已保存"},
    "WK4":    {"empty": "空白画布", "loading": "加载画布", "error": "保存失败", "success": "画布已保存"},
    "WK5":    {"empty": "无任务卡片", "loading": "加载看板", "error": "加载失败", "success": "看板正常展示"},
    "WK6":    {"empty": "无任务", "loading": "加载甘特图", "error": "加载失败", "success": "甘特图正常展示"},
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

# ── Interaction type inference — delegated to _common.py ──────────────────────
# Use C.INTERACTION_TYPE_RULES, C.infer_interaction_type, C.refine_view_type

# ── Platform profiles by audience_type (cross-project) ────────────────────────
# consumer → mobile app patterns; professional → desktop admin patterns.
_PLATFORM_PROFILES = {
    "consumer": {
        "platform": "mobile",
        "navigation": "bottom_tab",
        "layout": "single_column",
        "list_pattern": "card_list",
        "detail_pattern": "full_screen",
        "form_pattern": "bottom_sheet",
        "action_pattern": "swipe_action",
        "extra_states": {
            "pull_refresh": "下拉刷新",
            "skeleton": "骨架屏",
        },
        "contract_defaults": {
            "C": "bottom-sheet",
            "R": "full-page",
            "U": "bottom-sheet",
            "D": "bottom-sheet",
        },
    },
    "professional": {
        "platform": "desktop",
        "navigation": "sidebar",
        "layout": "master_detail",
        "list_pattern": "data_table",
        "detail_pattern": "side_panel",
        "form_pattern": "modal",
        "action_pattern": "toolbar",
        "extra_states": {
            "bulk_select": "批量选择",
            "breadcrumb": "面包屑导航",
        },
        "contract_defaults": {
            "C": "multi-step-form",
            "R": "standard-page",
            "U": "standard-page",
            "D": "modal-picker",
        },
    },
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


def infer_contract(ux_intent, crud_type, emotion_intensity, audience_type=""):
    """Infer implementation contract from UX intent, CRUD type, emotion intensity, and audience_type."""
    intent_lower = (ux_intent or "").lower()

    # Platform-aware default pattern
    profile = _PLATFORM_PROFILES.get(audience_type, {})
    platform_default = profile.get("contract_defaults", {}).get(crud_type, "standard-page")

    if any(kw in intent_lower for kw in ["quick", "overlay", "confirm", "dismiss"]):
        pattern = "bottom-sheet"
    elif any(kw in intent_lower for kw in ["detail", "full", "comprehensive"]):
        pattern = "full-page"
    elif any(kw in intent_lower for kw in ["select", "pick", "choose"]):
        pattern = "modal-picker"
    elif crud_type == "C" and emotion_intensity >= 7:
        pattern = "multi-step-form"
    elif audience_type:
        pattern = platform_default
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


# ── View type refinement — delegated to _common.py ───────────────────────────
# Use C.refine_view_type, C.CRUD_TO_VIEW_TYPE


def _find_vo_for_task(task, crud_type, vo_lookup):
    """Find the best matching VO for a task based on module and CRUD type.

    Uses task name keywords to refine view_type preference.
    Returns the VO dict or None if no match.
    """
    module = task.get("module", task.get("owner_role", ""))
    preferred_types = C.refine_view_type(task, crud_type)

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
                           ux_intent="", emotion_intensity=5, vo_lookup=None,
                           audience_type=""):
    """Build screen objects from a list of task IDs. Returns (screens, updated_counter).

    When vo_lookup is provided, screens are enriched with VO data (name, fields,
    interaction_type, actions, states). Falls back to generic names when no VO matches.
    audience_type: 'consumer' (mobile app) or 'professional' (desktop admin).
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

        # Derive implementation contract (platform-aware)
        contract = infer_contract(ux_intent, dominant_crud, emotion_intensity, audience_type)

        # ── Platform metadata ──
        profile = _PLATFORM_PROFILES.get(audience_type, {})
        platform_meta = {
            "platform": profile.get("platform", "unknown"),
            "navigation": profile.get("navigation", ""),
            "layout": profile.get("layout", ""),
        } if profile else {}

        # ── Infer interaction_type from 37-type system ──
        first_task = task_pairs[0][1] if task_pairs else {}
        inferred_itype = C.infer_interaction_type(first_task, dominant_crud, audience_type)

        # ── Try VO enrichment ──
        matched_vo = None
        if vo_lookup:
            matched_vo = _find_vo_for_task(first_task, dominant_crud, vo_lookup)

        if matched_vo:
            # Enriched screen from VO
            # Prefer inferred type (37-type) over VO's type (often just MG)
            vo_itype = matched_vo.get("interaction_type", "")
            interaction_type = inferred_itype if inferred_itype else vo_itype
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
                **platform_meta,
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
            interaction_type = inferred_itype
            suffix = VIEW_TYPE_NAMES.get(
                C.CRUD_TO_VIEW_TYPE.get(dominant_crud, ["list_item"])[0], ""
            )
            fallback_name = _derive_screen_name_from_tasks(task_pairs, suffix) or primary
            fallback_desc = f"{fallback_name} — {', '.join(a['label'] for a in actions[:3])}"
            contract["interaction_type"] = interaction_type
            screen = {
                "id": sid,
                "name": fallback_name,
                "description": fallback_desc,
                "route_type": "push",
                **platform_meta,
                "tasks": task_ids,
                "actions": actions,
                "primary_action": primary,
                "interaction_type": interaction_type,
                "states": DEFAULT_STATES.get(interaction_type, {}),
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


# ── Screen enrichment (fills sparse VO/entity data) ─────────────────────────

def _f(name, label, typ="string", widget="text", req=False, ro=False):
    d = {"name": name, "type": typ, "input_widget": widget, "required": req, "label": label}
    if ro:
        d["read_only"] = True
    return d


# ── Cross-project enrichment patterns ─────────────────────────────────────────
# Only universal patterns that apply to any product. Project-specific enrichments
# come from view-objects.json at runtime, not hardcoded here.
_ENRICHMENTS = [
    # ── Auth (universal) ──
    (("注册", "register", "signup"), {
        "fields": [_f("email", "邮箱", widget="email", req=True), _f("password", "密码", widget="password", req=True),
                   _f("confirm_password", "确认密码", widget="password", req=True)],
        "actions": [{"label": "注册", "crud": "C", "frequency": "高"}, {"label": "已有账号？去登录", "crud": "R", "frequency": "中"}],
        "states": {"default": "空表单", "loading": "提交中", "error": "注册失败", "success": "注册成功"},
    }),
    (("登录", "login", "signin"), {
        "fields": [_f("email", "邮箱/手机号", widget="email", req=True), _f("password", "密码", widget="password", req=True)],
        "actions": [{"label": "登录", "crud": "R", "frequency": "高"}, {"label": "忘记密码", "crud": "R", "frequency": "低"}],
        "states": {"default": "空表单", "loading": "验证中", "error": "凭证错误", "success": "登录成功"},
    }),
    (("重置密码", "reset password"), {
        "fields": [_f("email", "注册邮箱", widget="email", req=True), _f("code", "验证码", req=True),
                   _f("new_password", "新密码", widget="password", req=True)],
        "actions": [{"label": "发送验证码", "crud": "C", "frequency": "高"}, {"label": "确认重置", "crud": "U", "frequency": "高"}],
        "states": {"default": "输入邮箱", "code_sent": "验证码已发送", "error": "验证码错误", "success": "密码已重置"},
    }),
    # ── Onboarding (universal) ──
    (("新手引导", "onboarding", "引导"), {
        "fields": [_f("step", "引导步骤", typ="int", ro=True), _f("illustration", "插图", typ="image", ro=True),
                   _f("title", "标题", ro=True), _f("description", "描述", ro=True)],
        "actions": [{"label": "下一步", "crud": "R", "frequency": "高"}, {"label": "跳过引导", "crud": "R", "frequency": "低"}],
        "states": {"step_1": "欢迎页", "step_2": "核心功能", "step_3": "偏好设置", "complete": "引导完成"},
    }),
    # ── Profile (universal) ──
    (("个人资料", "profile", "个人信息"), {
        "fields": [_f("avatar", "头像", typ="image", widget="image_picker"), _f("nickname", "昵称", req=True),
                   _f("email", "邮箱", widget="email", ro=True)],
        "actions": [{"label": "保存修改", "crud": "U", "frequency": "高"}],
        "states": {"default": "表单回填", "editing": "修改中", "saved": "保存成功"},
    }),
    # ── Feedback (universal) ──
    (("意见反馈", "feedback", "反馈"), {
        "fields": [_f("type", "反馈类型", typ="enum", widget="select", req=True),
                   _f("content", "详细描述", widget="textarea", req=True),
                   _f("screenshot", "截图", typ="image", widget="image_picker")],
        "actions": [{"label": "提交反馈", "crud": "C", "frequency": "高"}],
        "states": {"default": "空表单", "submitting": "提交中", "success": "反馈已提交"},
    }),
    # ── Subscription (universal) ──
    (("订阅", "subscription", "套餐"), {
        "fields": [_f("plan_name", "当前套餐", ro=True), _f("price", "价格", ro=True),
                   _f("status", "状态", typ="enum", ro=True), _f("expiry_date", "到期日", typ="date", ro=True)],
        "actions": [{"label": "升级套餐", "crud": "U", "frequency": "高"}, {"label": "查看所有套餐", "crud": "R", "frequency": "中"}],
        "states": {"default": "套餐信息", "expiring": "即将到期", "expired": "已过期"},
    }),
    # ── Notification settings (universal) ──
    (("通知设置", "notification settings"), {
        "fields": [_f("push_enabled", "推送通知", typ="bool", widget="toggle"),
                   _f("email_enabled", "邮件通知", typ="bool", widget="toggle")],
        "actions": [{"label": "保存设置", "crud": "U", "frequency": "高"}],
        "states": {"default": "当前设置", "saved": "设置已保存"},
    }),
]


def _match_enrichment(task_name):
    """Match task name against enrichment patterns. Returns enrichment dict or None."""
    for keywords, enrichment in _ENRICHMENTS:
        if any(kw in task_name for kw in keywords):
            return enrichment
    return None


def _generic_crud_enrichment(crud_type, task_name):
    """Fallback enrichment based on CRUD type when no keyword match."""
    if crud_type == "C":
        return {
            "fields": [_f("title", "名称", req=True), _f("description", "描述", widget="textarea"),
                       _f("category", "分类", typ="enum", widget="select")],
            "actions": [{"label": "提交", "crud": "C", "frequency": "高"}, {"label": "取消", "crud": "R", "frequency": "中"}],
            "states": {"default": "空表单", "loading": "提交中", "error": "提交失败", "success": "创建成功"},
        }
    elif crud_type == "U":
        return {
            "fields": [_f("title", "名称", req=True), _f("description", "描述", widget="textarea"),
                       _f("status", "状态", typ="enum", ro=True)],
            "actions": [{"label": "保存", "crud": "U", "frequency": "高"}, {"label": "取消", "crud": "R", "frequency": "中"}],
            "states": {"default": "表单回填", "modified": "有修改", "saving": "保存中", "saved": "已保存"},
        }
    elif crud_type == "D":
        return {
            "fields": [_f("name", "名称", ro=True), _f("status", "状态", ro=True)],
            "actions": [{"label": "确认删除", "crud": "D", "frequency": "高"}, {"label": "取消", "crud": "R", "frequency": "高"}],
            "states": {"default": "删除确认", "deleting": "删除中", "deleted": "已删除"},
        }
    else:  # R
        return {
            "fields": [_f("title", "标题", ro=True), _f("description", "描述", ro=True),
                       _f("status", "状态", typ="enum", ro=True), _f("updated_at", "更新时间", typ="date", ro=True)],
            "actions": [{"label": "查看详情", "crud": "R", "frequency": "高"}, {"label": "搜索", "crud": "R", "frequency": "中"}],
            "states": {"default": "数据列表", "empty": "暂无数据", "loading": "加载中", "error": "加载失败"},
        }


def _post_enrich_screens(operation_lines, tasks_inv):
    """Post-process all screens: fill sparse data_fields, actions, states."""
    for ol in operation_lines:
        for node in ol.get("nodes", []):
            for screen in node.get("screens", []):
                _enrich_screen(screen, tasks_inv)


def _enrich_screen(screen, tasks_inv):
    """Enrich a single screen with realistic data if sparse."""
    existing = screen.get("data_fields", [])
    real = [f for f in existing if f.get("name") not in ("id", "updated_at", "created_at")]
    fields_rich = len(real) >= 3
    actions_rich = len(screen.get("actions", [])) >= 2

    if fields_rich and actions_rich:
        return

    # Gather task names for matching
    task_names = []
    for tid in screen.get("tasks", []):
        t = tasks_inv.get(tid, {})
        task_names.append(t.get("task_name", t.get("name", "")))
    combined = " ".join(task_names)
    if not combined.strip():
        return

    # Try domain-specific match first, then generic CRUD
    enrichment = _match_enrichment(combined)
    if not enrichment:
        crud = "R"
        for a in screen.get("actions", []):
            if a.get("crud", "R") != "R":
                crud = a["crud"]
                break
        enrichment = _generic_crud_enrichment(crud, combined)

    if not enrichment:
        return

    # Apply fields only if sparse
    if not fields_rich and enrichment.get("fields"):
        screen["data_fields"] = enrichment["fields"]

    # Merge actions (keep existing task-based, add enrichment extras)
    if enrichment.get("actions"):
        existing_labels = {a.get("label") for a in screen.get("actions", [])}
        merged = list(screen.get("actions", []))
        for a in enrichment["actions"]:
            if isinstance(a, str):
                a = {"label": a, "crud": "R", "frequency": "中"}
            if a["label"] not in existing_labels:
                merged.append(a)
        screen["actions"] = merged

    # Apply states
    if enrichment.get("states"):
        screen["states"] = enrichment["states"]


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

    # ── build role→audience_type mapping ──
    # roles from C.load_role_profiles() is {role_id: role_name} dict
    # Need full role objects for audience_type
    roles_full = C.load_role_profiles_full(BASE) if hasattr(C, 'load_role_profiles_full') else []
    role_audience = {}
    for r in roles_full:
        rid = r.get("id", r.get("role_id", ""))
        role_audience[rid] = r.get("audience_type", "professional")
    if role_audience:
        print(f"  Roles: {', '.join(f'{k}={v}' for k, v in role_audience.items())}")

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
                # Also register zero-padded variants: F1→F01, F1→F001
                import re as _re
                m = _re.match(r'^(F)(\d+)$', fid)
                if m:
                    num = int(m.group(2))
                    flow_by_id[f"{m.group(1)}{num:02d}"] = f
                    flow_by_id[f"{m.group(1)}{num:03d}"] = f

    # ── generate operation lines ──
    operation_lines = []
    screen_index = {}
    screen_counter = 0
    # Dedup: map (task_id_tuple, audience_type) → existing screen list
    # so the same task in different operation lines reuses the same screen
    _screen_dedup = {}  # (frozenset(task_ids), audience_type) → [screen, ...]

    for jl in journey_lines:
        jl_id = jl["id"]
        source_flow_id = jl.get("source_flow", "")
        flow = flow_by_id.get(source_flow_id, {})
        flow_nodes = C.get_flow_nodes(flow) if flow else []

        # Determine audience_type for this journey line's role
        jl_role = jl.get("role", "")
        jl_audience = role_audience.get(jl_role, "professional")

        nodes = []
        for en in jl.get("emotion_nodes", []):
            step = en["step"]

            # Match to flow node for task references
            flow_node = flow_nodes[step - 1] if step - 1 < len(flow_nodes) else {}
            # Support both task_ref (canonical) and task_id (legacy)
            node_task_id = flow_node.get("task_ref", flow_node.get("task_id", ""))
            node_tasks = [node_task_id] if node_task_id and node_task_id in tasks_inv else []

            # Dedup: check if this exact task set already generated screens
            dedup_key = (frozenset(node_tasks), jl_audience) if node_tasks else None
            if dedup_key and dedup_key in _screen_dedup:
                node_screens = _screen_dedup[dedup_key]
            else:
                # Build screens for this node
                node_screens, screen_counter = build_screens_for_node(
                    node_tasks, tasks_inv, screen_counter,
                    ux_intent=en.get("design_hint", ""),
                    emotion_intensity=en.get("intensity", 5),
                    vo_lookup=vo_lookup,
                    audience_type=jl_audience,
                )
                if dedup_key:
                    _screen_dedup[dedup_key] = node_screens

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

    # ── enrich screens with domain-specific data_fields/actions/states ──
    _post_enrich_screens(operation_lines, tasks_inv)

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
