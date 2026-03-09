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

# ── Interaction type inference (cross-project keyword matching) ────────────────
# Priority: keyword match > CRUD-based fallback.
# Each entry: (keywords_list, interaction_type, audience_filter)
# audience_filter: None = any, "consumer" = mobile only, "professional" = desktop only
_INTERACTION_TYPE_RULES = [
    # ── Disambiguation rules (highest priority — prevent false matches) ──
    (["复习调度", "调度", "队列", "schedule", "queue"],                          "MG1", None),
    (["llm生成", "ai生成", "生成内容", "prompt模板"],                             "WK3", "professional"),

    # ── SY 引导系统（high priority — onboarding/wizard) ──
    (["新手引导", "引导流程", "onboarding", "入门", "教程", "welcome"],        "SY1", None),
    (["注册", "register", "signup", "多步表单", "向导", "登录", "login",
     "signin"],                                                                "SY2", None),

    # ── CT 内容消费（consumer-facing content patterns）──
    (["feed", "动态流", "推荐流", "时间线", "信息流",
     "场景列表", "浏览列表", "内容列表", "课程列表"],                              "CT1", "consumer"),
    (["阅读", "详情阅读", "文章", "帖子", "对话阅读", "长文"],                   "CT2", None),
    (["场景详情", "查看详情", "内容详情"],                                       "CT2", "consumer"),
    (["个人资料", "个人主页", "profile", "我的", "个人设置", "个人信息",
     "编辑个人"],                                                              "CT3", None),
    (["闪卡", "swipe", "翻卡", "flashcard", "轮播",
     "闪卡复习", "填空练习", "听音选词", "拼写测试",
     "练习关键", "学习核心", "标记生词",
     "单词卡", "生词本"],                                                        "CT4", None),
    (["播放", "播放器", "音频", "视频播放", "player", "发音"],                   "CT5", None),
    (["相册", "图库", "gallery", "图片浏览", "配图"],                            "CT6", None),
    (["搜索结果", "search result"],                                            "CT7", None),
    (["短视频", "story", "stories", "短视频流"],                                "CT8", None),

    # ── EC 电商交易 ──
    (["商品详情", "product detail", "订阅方案", "价格方案", "升级"],              "EC1", None),
    (["购物车", "结算", "checkout", "cart", "付费", "购买"],                     "EC2", None),
    (["物流", "订单追踪", "tracking", "时间线追踪", "进度追踪"],                  "EC3", None),

    # ── WK 协作办公 ──
    (["聊天", "对话", "IM", "消息", "chat"],                                   "WK1", None),
    (["频道", "群组", "channel", "group"],                                     "WK2", None),
    (["文档编辑", "编辑器", "editor", "rich text", "markdown编辑"],              "WK3", None),
    (["画布", "白板", "canvas", "whiteboard"],                                 "WK4", None),
    (["看板", "kanban", "board"],                                              "WK5", None),
    (["甘特图", "gantt", "项目排期"],                                           "WK6", None),
    (["文件管理", "file manager", "文件列表"],                                   "WK7", None),

    # ── RT 通讯实时 ──
    (["通话", "视频通话", "语音通话", "call"],                                   "RT1", None),
    (["直播", "live", "直播间"],                                                "RT2", None),
    (["邮件", "email", "收件箱"],                                               "RT3", None),
    (["通知", "通知中心", "notification", "消息中心", "提醒"],                    "RT4", None),

    # ── SB 审核提交 ──
    (["反馈", "意见反馈", "feedback", "举报", "投诉", "提交审核"],               "SB1", None),

    # ── Progress/download patterns ──
    (["下载", "download", "同步", "sync", "进度"],                              "MG3", "consumer"),

    # ── MG 管理类（lower priority — CRUD-based fallback handles most）──
    (["审核", "审批", "approve", "review", "驳回"],                             "MG4", None),
    (["状态流转", "上架", "下架", "冻结", "发布", "归档"],                       "MG3", None),
    (["仪表盘", "dashboard", "数据面板", "统计", "数据概览", "数据分析",
     "学习统计"],                                                               "MG7", None),
    (["配置", "系统设置", "系统配置", "偏好设置", "setting",
     "学习目标", "目标设置"],                                                    "MG8", None),
    (["分类管理", "标签管理", "树形", "层级", "目录管理"],                        "MG6", None),
    (["主从", "订单详情+明细", "用户详情+关联"],                                  "MG5", None),
    (["管理用户", "用户管理", "用户列表", "管理成员"],                             "MG2-L", None),
]


def _infer_interaction_type(task, crud_type, audience_type=""):
    """Infer interaction_type from task name + module using the 37-type system.

    Priority:
    1. Keyword match from _INTERACTION_TYPE_RULES (most specific wins)
    2. CRUD-based MG fallback (MG1/MG2-*/MG3/MG4)

    Returns interaction_type string (e.g. "CT4", "MG2-L", "SY1").
    """
    tname = task.get("task_name", task.get("name", "")).lower()
    module = task.get("module", "").lower()
    text = tname + " " + module

    # 1. Keyword match
    for keywords, itype, audience_filter in _INTERACTION_TYPE_RULES:
        if audience_filter and audience_filter != audience_type:
            continue
        for kw in keywords:
            if kw.lower() in text:
                return itype

    # 2. CRUD-based MG fallback
    if crud_type == "C":
        return "MG2-C"
    elif crud_type == "U":
        return "MG2-E"
    elif crud_type == "D":
        return "MG3"
    elif crud_type == "R":
        # Use _refine_view_type to pick detail vs list
        preferred = _refine_view_type(task, "R")
        if preferred and preferred[0] == "detail":
            return "MG2-D"
        return "MG1"
    return "MG1"

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


# ── Task name → view_type refinement keywords (cross-project) ────────────────
# When CRUD is "R", disambiguate list vs detail vs other view types.
_VIEW_TYPE_KEYWORDS = {
    "detail": ["详情", "detail", "查看详情", "详细"],
    "list_item": ["列表", "浏览", "搜索", "筛选", "list", "browse"],
    "state_action": ["审核", "通过", "驳回", "approve", "reject", "发布", "publish"],
    "create_form": ["生成", "generate", "新建"],
}


def _refine_view_type(task, crud_type):
    """Refine CRUD_TO_VIEW_TYPE preference based on task name keywords.

    For "R" tasks, checks if the task name suggests detail vs list.
    For other CRUDs, checks for state_action or generation patterns.
    Returns refined preferred_types list.
    """
    tname = task.get("task_name", task.get("name", "")).lower()
    base_types = CRUD_TO_VIEW_TYPE.get(crud_type, ["list_item"])

    # For "R" tasks: detail keywords should prioritize detail over list
    if crud_type == "R":
        for kw in _VIEW_TYPE_KEYWORDS["detail"]:
            if kw in tname:
                return ["detail", "list_item"]
        for kw in _VIEW_TYPE_KEYWORDS["list_item"]:
            if kw in tname:
                return ["list_item", "detail"]
        # Default: if task name doesn't have list keywords either,
        # check if it's a standalone action (download, read, practice)
        # — these are more like detail/full-screen than list
        if not any(kw in tname for kw in ["列表", "浏览", "搜索", "筛选"]):
            return ["detail", "list_item"]

    # For state-like tasks mapped to U/D
    if crud_type in ("U", "D"):
        for kw in _VIEW_TYPE_KEYWORDS["state_action"]:
            if kw in tname:
                return ["state_action"] + base_types

    # For C tasks that are actually "generate" actions
    if crud_type == "C":
        for kw in _VIEW_TYPE_KEYWORDS["create_form"]:
            if kw in tname:
                return base_types  # keep create_form first

    return base_types


def _find_vo_for_task(task, crud_type, vo_lookup):
    """Find the best matching VO for a task based on module and CRUD type.

    Uses task name keywords to refine view_type preference.
    Returns the VO dict or None if no match.
    """
    module = task.get("module", task.get("owner_role", ""))
    preferred_types = _refine_view_type(task, crud_type)

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
        inferred_itype = _infer_interaction_type(first_task, dominant_crud, audience_type)

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
                CRUD_TO_VIEW_TYPE.get(dominant_crud, ["list_item"])[0], ""
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


# Task-name keyword → enrichment.  First match wins.
_ENRICHMENTS = [
    # ── Auth ──
    (("注册",), {
        "fields": [_f("email", "邮箱", widget="email", req=True), _f("password", "密码", widget="password", req=True),
                   _f("confirm_password", "确认密码", widget="password", req=True), _f("nickname", "昵称")],
        "actions": [{"label": "注册", "crud": "C", "frequency": "高"}, {"label": "已有账号？去登录", "crud": "R", "frequency": "中"},
                    {"label": "第三方注册", "crud": "C", "frequency": "低"}],
        "states": {"default": "空表单，所有字段待填写", "loading": "注册中，按钮禁用", "error": "注册失败（邮箱已存在/密码不符）", "success": "注册成功，进入引导"},
    }),
    (("登录",), {
        "fields": [_f("email", "邮箱/手机号", widget="email", req=True), _f("password", "密码", widget="password", req=True)],
        "actions": [{"label": "登录", "crud": "R", "frequency": "高"}, {"label": "忘记密码", "crud": "R", "frequency": "低"},
                    {"label": "第三方登录", "crud": "R", "frequency": "中"}],
        "states": {"default": "空表单，待输入凭证", "loading": "验证中", "error": "账号或密码错误", "success": "登录成功，跳转首页"},
    }),
    (("重置密码",), {
        "fields": [_f("email", "注册邮箱", widget="email", req=True), _f("code", "验证码", req=True), _f("new_password", "新密码", widget="password", req=True)],
        "actions": [{"label": "发送验证码", "crud": "C", "frequency": "高"}, {"label": "确认重置", "crud": "U", "frequency": "高"}],
        "states": {"default": "输入邮箱", "code_sent": "验证码已发送，倒计时60s", "error": "验证码错误/过期", "success": "密码已重置"},
    }),
    # ── Onboarding ──
    (("新手引导", "引导"), {
        "fields": [_f("step", "引导步骤", typ="int", ro=True), _f("illustration", "插图", typ="image", ro=True),
                   _f("title", "标题", ro=True), _f("description", "描述", ro=True)],
        "actions": [{"label": "下一步", "crud": "R", "frequency": "高"}, {"label": "跳过引导", "crud": "R", "frequency": "低"}],
        "states": {"step_1": "欢迎页+产品介绍", "step_2": "核心功能演示", "step_3": "选择学习偏好", "complete": "引导完成，进入首页"},
    }),
    # ── Scene browsing ──
    (("场景列表", "浏览场景"), {
        "fields": [_f("title", "场景名称", ro=True), _f("category", "分类", typ="enum", ro=True),
                   _f("thumbnail", "封面图", typ="image", ro=True), _f("difficulty", "难度", typ="enum", ro=True),
                   _f("word_count", "单词数", typ="int", ro=True), _f("download_count", "下载量", typ="int", ro=True)],
        "actions": [{"label": "搜索场景", "crud": "R", "frequency": "高"}, {"label": "按分类筛选", "crud": "R", "frequency": "高"},
                    {"label": "按难度筛选", "crud": "R", "frequency": "中"}, {"label": "查看场景详情", "crud": "R", "frequency": "高"}],
        "states": {"default": "场景卡片列表+分类标签", "empty": "暂无场景，引导探索", "loading": "骨架屏占位", "filtered": "筛选结果展示"},
    }),
    (("场景详情", "查看场景"), {
        "fields": [_f("title", "场景名称", ro=True), _f("description", "场景描述", ro=True),
                   _f("cover_image", "封面图", typ="image", ro=True), _f("difficulty", "难度", typ="enum", ro=True),
                   _f("dialogue_count", "对话数", typ="int", ro=True), _f("word_count", "核心词汇数", typ="int", ro=True),
                   _f("tags", "标签", typ="array", ro=True), _f("sample_dialogue", "对话预览", ro=True)],
        "actions": [{"label": "下载场景包", "crud": "C", "frequency": "高"}, {"label": "预览对话", "crud": "R", "frequency": "中"},
                    {"label": "分享场景", "crud": "R", "frequency": "低"}],
        "states": {"default": "场景详情完整展示", "not_downloaded": "显示下载按钮+预览", "downloaded": "显示开始学习按钮", "loading": "骨架屏"},
    }),
    # ── Download ──
    (("下载场景",), {
        "fields": [_f("package_name", "场景包名称", ro=True), _f("file_size", "文件大小", typ="int", ro=True),
                   _f("progress", "下载进度", typ="float", ro=True), _f("speed", "下载速度", ro=True),
                   _f("status", "状态", typ="enum", ro=True)],
        "actions": [{"label": "开始下载", "crud": "C", "frequency": "高"}, {"label": "暂停下载", "crud": "U", "frequency": "中"},
                    {"label": "取消下载", "crud": "D", "frequency": "低"}],
        "states": {"queued": "排队中", "downloading": "下载中+进度条+速度", "paused": "已暂停，可恢复", "complete": "下载完成，可开始学习", "error": "下载失败，可重试"},
    }),
    (("管理已下载",), {
        "fields": [_f("package_name", "场景包名称", ro=True), _f("size", "占用空间", typ="int", ro=True),
                   _f("downloaded_at", "下载日期", typ="date", ro=True), _f("last_studied", "上次学习", typ="date", ro=True),
                   _f("progress_pct", "学习进度", typ="float", ro=True)],
        "actions": [{"label": "继续学习", "crud": "R", "frequency": "高"}, {"label": "删除场景包", "crud": "D", "frequency": "低"},
                    {"label": "检查更新", "crud": "R", "frequency": "低"}],
        "states": {"default": "已下载场景列表+空间占用统计", "empty": "暂无下载，引导去场景市场", "storage_full": "存储空间不足警告"},
    }),
    # ── Dialogue / Reading ──
    (("阅读场景对话", "场景对话"), {
        "fields": [_f("speaker", "说话人", ro=True), _f("text", "原文", ro=True),
                   _f("translation", "翻译", ro=True), _f("audio_url", "音频", typ="audio", ro=True),
                   _f("scene_image", "场景连环画", typ="image", ro=True)],
        "actions": [{"label": "播放音频", "crud": "R", "frequency": "高"}, {"label": "显示/隐藏翻译", "crud": "R", "frequency": "高"},
                    {"label": "点击句子查看解析", "crud": "R", "frequency": "高"}, {"label": "下一段对话", "crud": "R", "frequency": "高"},
                    {"label": "标记难句", "crud": "C", "frequency": "中"}],
        "states": {"default": "气泡对话+连环画配图", "translation_hidden": "仅显示原文", "sentence_detail": "展开句子解析面板", "audio_playing": "音频播放中+高亮当前句"},
    }),
    # ── Sentence practice ──
    (("练习关键句子", "练句子"), {
        "fields": [_f("sentence", "句子原文", ro=True), _f("translation", "中文翻译", ro=True),
                   _f("audio_url", "句子音频", typ="audio", ro=True), _f("key_phrase", "关键短语", ro=True),
                   _f("context", "场景上下文", ro=True), _f("progress", "练习进度", typ="float", ro=True)],
        "actions": [{"label": "播放音频", "crud": "R", "frequency": "高"}, {"label": "跟读录音", "crud": "C", "frequency": "高"},
                    {"label": "下一句", "crud": "R", "frequency": "高"}, {"label": "上一句", "crud": "R", "frequency": "中"}],
        "states": {"default": "句子卡片+音频+翻译", "recording": "录音中+波形显示", "playback": "回放录音vs原音对比", "complete": "本组句子练习完成"},
    }),
    # ── Word learning ──
    (("学习核心单词",), {
        "fields": [_f("word", "单词", ro=True), _f("phonetic", "音标", ro=True),
                   _f("meaning", "释义", ro=True), _f("example", "例句", ro=True),
                   _f("audio_url", "发音", typ="audio", ro=True), _f("image", "配图", typ="image", ro=True),
                   _f("scene_context", "场景出处", ro=True)],
        "actions": [{"label": "播放发音", "crud": "R", "frequency": "高"}, {"label": "标记为生词", "crud": "C", "frequency": "高"},
                    {"label": "已掌握", "crud": "U", "frequency": "高"}, {"label": "下一个单词", "crud": "R", "frequency": "高"},
                    {"label": "查看例句", "crud": "R", "frequency": "中"}],
        "states": {"default": "单词卡片正面（词+音标+释义）", "expanded": "展开例句+配图+场景出处", "marked": "已标记为生词，加入复习队列"},
    }),
    (("标记生词",), {
        "fields": [_f("word", "单词", ro=True), _f("phonetic", "音标", ro=True),
                   _f("meaning", "释义", ro=True), _f("source_scene", "出处场景", ro=True),
                   _f("note", "个人笔记", widget="textarea")],
        "actions": [{"label": "确认标记", "crud": "C", "frequency": "高"}, {"label": "添加笔记", "crud": "U", "frequency": "中"},
                    {"label": "取消标记", "crud": "D", "frequency": "低"}],
        "states": {"default": "单词信息+标记确认", "with_note": "已添加笔记", "success": "已加入生词本"},
    }),
    # ── Vocabulary ──
    (("生词本", "查看生词", "生词"), {
        "fields": [_f("word", "单词", ro=True), _f("phonetic", "音标", ro=True),
                   _f("meaning", "释义", ro=True), _f("mastery", "掌握度", typ="float", ro=True),
                   _f("next_review", "下次复习", typ="date", ro=True), _f("added_at", "添加日期", typ="date", ro=True)],
        "actions": [{"label": "搜索单词", "crud": "R", "frequency": "高"}, {"label": "按掌握度排序", "crud": "R", "frequency": "中"},
                    {"label": "移除生词", "crud": "D", "frequency": "低"}, {"label": "开始复习", "crud": "R", "frequency": "高"}],
        "states": {"default": "生词列表+掌握度指示", "empty": "暂无生词，引导去学习场景", "filtered": "按掌握度/日期筛选结果"},
    }),
    # ── Flashcard ──
    (("闪卡复习", "闪卡"), {
        "fields": [_f("word", "单词", ro=True), _f("phonetic", "音标", ro=True),
                   _f("meaning", "释义", ro=True), _f("example", "例句", ro=True),
                   _f("mastery", "掌握度", typ="float", ro=True), _f("progress", "本轮进度", typ="float", ro=True)],
        "actions": [{"label": "认识", "crud": "U", "frequency": "高"}, {"label": "模糊", "crud": "U", "frequency": "高"},
                    {"label": "不认识", "crud": "U", "frequency": "高"}, {"label": "播放发音", "crud": "R", "frequency": "高"}],
        "states": {"front": "卡片正面：单词+音标", "back": "卡片背面：释义+例句+评分按钮", "result": "本轮结束统计", "empty": "无待复习卡片"},
    }),
    # ── Fill-in ──
    (("填空练习", "填空"), {
        "fields": [_f("sentence", "完整句子", ro=True), _f("blank_word", "空缺单词", ro=True),
                   _f("options", "选项列表", typ="array", ro=True), _f("correct_answer", "正确答案", ro=True),
                   _f("context_hint", "上下文提示", ro=True), _f("progress", "进度", typ="float", ro=True)],
        "actions": [{"label": "选择答案", "crud": "U", "frequency": "高"}, {"label": "查看提示", "crud": "R", "frequency": "中"},
                    {"label": "下一题", "crud": "R", "frequency": "高"}],
        "states": {"default": "题目+选项", "selected": "已选答案待确认", "correct": "回答正确+绿色反馈", "wrong": "回答错误+红色+显示正确答案"},
    }),
    # ── Listening ──
    (("听音选词", "听音"), {
        "fields": [_f("audio_url", "音频", typ="audio", ro=True), _f("options", "候选单词", typ="array", ro=True),
                   _f("correct_word", "正确单词", ro=True), _f("play_count", "播放次数", typ="int", ro=True),
                   _f("progress", "进度", typ="float", ro=True)],
        "actions": [{"label": "播放音频", "crud": "R", "frequency": "高"}, {"label": "再听一次", "crud": "R", "frequency": "高"},
                    {"label": "选择单词", "crud": "U", "frequency": "高"}, {"label": "下一题", "crud": "R", "frequency": "高"}],
        "states": {"default": "播放按钮+候选词列表", "playing": "音频播放中", "correct": "选对+发音+释义展示", "wrong": "选错+正确答案+再听"},
    }),
    # ── Spelling ──
    (("拼写测试", "拼写"), {
        "fields": [_f("meaning", "中文释义", ro=True), _f("phonetic", "音标提示", ro=True),
                   _f("audio_url", "发音", typ="audio", ro=True), _f("input_letters", "已输入字母", ro=True),
                   _f("hint_count", "提示次数", typ="int", ro=True), _f("progress", "进度", typ="float", ro=True)],
        "actions": [{"label": "输入字母", "crud": "U", "frequency": "高"}, {"label": "播放发音", "crud": "R", "frequency": "高"},
                    {"label": "获取提示", "crud": "R", "frequency": "中"}, {"label": "删除字母", "crud": "U", "frequency": "高"}],
        "states": {"default": "释义+音标+字母键盘", "partial": "部分字母已输入", "correct": "拼写正确+完整单词展示", "wrong": "拼写错误+正确拼写+重试"},
    }),
    # ── SRS / Review schedule ──
    (("SRS复习调度", "复习调度", "复习计划"), {
        "fields": [_f("due_today", "今日待复习", typ="int", ro=True), _f("due_tomorrow", "明日待复习", typ="int", ro=True),
                   _f("total_in_queue", "总队列数", typ="int", ro=True), _f("mastery_distribution", "掌握度分布", typ="object", ro=True),
                   _f("streak_days", "连续天数", typ="int", ro=True), _f("next_review_time", "下次复习", typ="datetime", ro=True)],
        "actions": [{"label": "开始今日复习", "crud": "R", "frequency": "高"}, {"label": "查看复习日历", "crud": "R", "frequency": "中"},
                    {"label": "调整复习设置", "crud": "U", "frequency": "低"}],
        "states": {"default": "今日待复习统计+日历预览", "all_done": "今日复习已完成+鼓励文案", "overdue": "有逾期未复习+提醒"},
    }),
    # ── Stats ──
    (("学习统计", "统计"), {
        "fields": [_f("words_learned", "已学单词", typ="int", ro=True), _f("words_mastered", "已掌握", typ="int", ro=True),
                   _f("accuracy_rate", "正确率", typ="float", ro=True), _f("streak_days", "连续学习天数", typ="int", ro=True),
                   _f("total_study_time", "总学习时长", typ="int", ro=True), _f("weekly_chart", "本周趋势", typ="object", ro=True),
                   _f("scenes_completed", "已完成场景", typ="int", ro=True)],
        "actions": [{"label": "切换周/月/年", "crud": "R", "frequency": "高"}, {"label": "分享成就", "crud": "R", "frequency": "低"}],
        "states": {"default": "统计卡片+趋势图表", "empty": "暂无数据，引导开始学习", "milestone": "达成里程碑弹窗"},
    }),
    # ── Goal ──
    (("学习目标", "目标"), {
        "fields": [_f("daily_minutes", "每日目标(分钟)", typ="int", widget="slider"),
                   _f("daily_words", "每日新词数", typ="int", widget="slider"),
                   _f("reminder_time", "提醒时间", typ="time", widget="time_picker"),
                   _f("rest_days", "休息日", typ="array", widget="multi_select")],
        "actions": [{"label": "保存目标", "crud": "U", "frequency": "高"}, {"label": "重置为默认", "crud": "U", "frequency": "低"}],
        "states": {"default": "当前目标设置+完成率环形图", "editing": "调整目标参数", "saved": "保存成功提示"},
    }),
    # ── Role play ──
    (("角色扮演",), {
        "fields": [_f("scene_title", "场景名称", ro=True), _f("role", "扮演角色", ro=True),
                   _f("ai_message", "AI对话", ro=True), _f("user_input", "用户输入", widget="textarea"),
                   _f("hint", "提示词", ro=True), _f("score", "表现评分", typ="float", ro=True)],
        "actions": [{"label": "发送对话", "crud": "C", "frequency": "高"}, {"label": "获取提示", "crud": "R", "frequency": "中"},
                    {"label": "重新开始", "crud": "U", "frequency": "低"}, {"label": "结束对话", "crud": "U", "frequency": "中"}],
        "states": {"default": "AI对话气泡+输入框", "thinking": "AI思考中", "feedback": "AI纠错+建议", "complete": "对话结束+评分"},
    }),
    # ── Recommendation ──
    (("预测式学习", "预测", "推荐"), {
        "fields": [_f("recommended_scenes", "推荐场景", typ="array", ro=True),
                   _f("reason", "推荐理由", ro=True), _f("difficulty_match", "难度匹配度", typ="float", ro=True),
                   _f("estimated_time", "预估时长", typ="int", ro=True)],
        "actions": [{"label": "开始学习", "crud": "R", "frequency": "高"}, {"label": "换一批", "crud": "R", "frequency": "中"},
                    {"label": "不感兴趣", "crud": "U", "frequency": "低"}],
        "states": {"default": "推荐卡片列表+理由标签", "loading": "AI分析中", "empty": "暂无推荐，继续学习解锁更多"},
    }),
    # ── Semantic graph ──
    (("语义关联", "关联网络"), {
        "fields": [_f("center_word", "中心词", ro=True), _f("related_words", "关联词汇", typ="array", ro=True),
                   _f("relation_type", "关系类型", typ="enum", ro=True), _f("strength", "关联强度", typ="float", ro=True)],
        "actions": [{"label": "点击词汇展开", "crud": "R", "frequency": "高"}, {"label": "缩放图谱", "crud": "R", "frequency": "中"},
                    {"label": "切换关系类型", "crud": "R", "frequency": "中"}],
        "states": {"default": "力导向图+词汇节点", "expanded": "展开词汇详情面板", "filtered": "按关系类型筛选"},
    }),
    # ── Offline ──
    (("离线学习",), {
        "fields": [_f("available_scenes", "可用场景包", typ="array", ro=True),
                   _f("cached_audio", "已缓存音频", typ="bool", ro=True),
                   _f("pending_sync", "待同步条数", typ="int", ro=True)],
        "actions": [{"label": "继续学习", "crud": "R", "frequency": "高"}, {"label": "查看已缓存内容", "crud": "R", "frequency": "中"}],
        "states": {"default": "离线模式标识+可用内容列表", "no_content": "无已下载内容，提示在线下载"},
    }),
    (("同步学习进度", "同步"), {
        "fields": [_f("pending_items", "待同步条数", typ="int", ro=True), _f("last_sync", "上次同步", typ="datetime", ro=True),
                   _f("sync_status", "同步状态", typ="enum", ro=True), _f("conflict_count", "冲突数", typ="int", ro=True)],
        "actions": [{"label": "立即同步", "crud": "U", "frequency": "高"}, {"label": "查看冲突", "crud": "R", "frequency": "低"}],
        "states": {"default": "同步状态+待同步数量", "syncing": "同步中+进度", "complete": "同步完成", "conflict": "存在冲突需处理", "offline": "无网络连接"},
    }),
    # ── Profile & Settings ──
    (("编辑个人资料", "个人资料"), {
        "fields": [_f("avatar", "头像", typ="image", widget="image_picker"), _f("nickname", "昵称", req=True),
                   _f("email", "邮箱", widget="email", ro=True), _f("learning_language", "学习语言", typ="enum", widget="select"),
                   _f("native_language", "母语", typ="enum", widget="select")],
        "actions": [{"label": "保存修改", "crud": "U", "frequency": "高"}, {"label": "更换头像", "crud": "U", "frequency": "低"}],
        "states": {"default": "表单回填当前信息", "editing": "字段修改中", "saved": "保存成功", "error": "保存失败"},
    }),
    (("管理通知设置", "通知设置"), {
        "fields": [_f("daily_reminder", "每日学习提醒", typ="bool", widget="toggle"),
                   _f("reminder_time", "提醒时间", typ="time", widget="time_picker"),
                   _f("review_reminder", "复习到期提醒", typ="bool", widget="toggle"),
                   _f("new_scene_alert", "新场景上线通知", typ="bool", widget="toggle"),
                   _f("sound_enabled", "提示音", typ="bool", widget="toggle")],
        "actions": [{"label": "保存设置", "crud": "U", "frequency": "高"}],
        "states": {"default": "当前通知设置+开关", "saved": "设置已保存"},
    }),
    (("提交意见反馈", "意见反馈"), {
        "fields": [_f("type", "反馈类型", typ="enum", widget="select", req=True),
                   _f("content", "详细描述", widget="textarea", req=True),
                   _f("screenshot", "截图", typ="image", widget="image_picker"),
                   _f("contact", "联系方式")],
        "actions": [{"label": "提交反馈", "crud": "C", "frequency": "高"}, {"label": "添加截图", "crud": "C", "frequency": "中"}],
        "states": {"default": "空表单", "submitting": "提交中", "success": "反馈已提交，感谢！", "error": "提交失败，请重试"},
    }),
    # ── Subscription ──
    (("查看订阅", "订阅状态"), {
        "fields": [_f("plan_name", "当前套餐", ro=True), _f("price", "价格", ro=True),
                   _f("status", "订阅状态", typ="enum", ro=True), _f("expiry_date", "到期日", typ="date", ro=True),
                   _f("download_quota", "剩余下载额度", typ="int", ro=True), _f("features", "套餐权益", typ="array", ro=True)],
        "actions": [{"label": "升级套餐", "crud": "U", "frequency": "高"}, {"label": "查看所有套餐", "crud": "R", "frequency": "中"}],
        "states": {"default": "当前套餐信息+权益列表", "expiring_soon": "即将到期提醒", "expired": "已过期，功能受限提示"},
    }),
    (("升级", "变更订阅"), {
        "fields": [_f("plans", "可选套餐", typ="array", ro=True), _f("current_plan", "当前套餐", ro=True),
                   _f("price_diff", "差价", typ="float", ro=True), _f("payment_method", "支付方式", typ="enum", widget="select")],
        "actions": [{"label": "确认升级", "crud": "U", "frequency": "高"}, {"label": "对比套餐", "crud": "R", "frequency": "中"}],
        "states": {"default": "套餐对比卡片", "selected": "已选套餐+支付确认", "processing": "支付处理中", "success": "升级成功", "failed": "支付失败"},
    }),
    (("取消订阅",), {
        "fields": [_f("current_plan", "当前套餐", ro=True), _f("expiry_date", "失效日期", typ="date", ro=True),
                   _f("cancel_reason", "取消原因", typ="enum", widget="select"), _f("feedback", "改进建议", widget="textarea")],
        "actions": [{"label": "确认取消", "crud": "D", "frequency": "高"}, {"label": "保留订阅", "crud": "R", "frequency": "高"}],
        "states": {"default": "取消确认+挽留提示", "reason_selection": "选择取消原因", "confirmed": "已取消，月底失效", "retained": "用户选择保留"},
    }),
    # ── Admin: content creation ──
    (("创建场景",), {
        "fields": [_f("title", "场景标题", req=True), _f("category", "分类", typ="enum", widget="select", req=True),
                   _f("difficulty", "难度", typ="enum", widget="select", req=True), _f("description", "场景描述", widget="textarea"),
                   _f("target_words", "目标词汇量", typ="int"), _f("tags", "标签", typ="array", widget="tag_input")],
        "actions": [{"label": "创建并生成内容", "crud": "C", "frequency": "高"}, {"label": "保存草稿", "crud": "C", "frequency": "中"}],
        "states": {"default": "空表单", "draft": "草稿已保存", "submitting": "创建中", "success": "创建成功，进入内容生成"},
    }),
    (("LLM生成场景内容", "LLM生成", "生成场景内容"), {
        "fields": [_f("scene_title", "场景标题", ro=True), _f("generation_status", "生成状态", typ="enum", ro=True),
                   _f("dialogue_preview", "对话预览", ro=True), _f("word_list_preview", "词汇预览", typ="array", ro=True),
                   _f("model_used", "使用模型", ro=True), _f("generation_time", "生成耗时", typ="int", ro=True)],
        "actions": [{"label": "开始生成", "crud": "C", "frequency": "高"}, {"label": "重新生成", "crud": "U", "frequency": "中"},
                    {"label": "调整参数", "crud": "U", "frequency": "低"}],
        "states": {"generating": "AI生成中+进度(对话→句子→词汇→练习)", "preview": "生成完成，预览内容", "error": "生成失败，可重试", "accepted": "内容已确认"},
    }),
    (("审核场景内容", "审核场景"), {
        "fields": [_f("scene_title", "场景标题", ro=True), _f("content_preview", "内容预览", ro=True),
                   _f("quality_score", "质量评分", typ="float", ro=True), _f("issues", "问题列表", typ="array", ro=True),
                   _f("reviewer_comment", "审核意见", widget="textarea")],
        "actions": [{"label": "通过", "crud": "U", "frequency": "高"}, {"label": "驳回", "crud": "U", "frequency": "中"},
                    {"label": "标记问题", "crud": "C", "frequency": "高"}],
        "states": {"default": "内容详情+审核面板", "approved": "已通过", "rejected": "已驳回+原因", "needs_revision": "标记待修改"},
    }),
    (("编辑场景内容",), {
        "fields": [_f("dialogue_text", "对话内容", widget="textarea", req=True), _f("vocabulary_list", "词汇列表", widget="textarea"),
                   _f("exercise_config", "练习配置", widget="textarea"), _f("notes", "修改备注", widget="textarea")],
        "actions": [{"label": "保存修改", "crud": "U", "frequency": "高"}, {"label": "预览效果", "crud": "R", "frequency": "中"},
                    {"label": "重置为AI版本", "crud": "U", "frequency": "低"}],
        "states": {"default": "富文本编辑器+内容回填", "modified": "有未保存修改", "saved": "保存成功", "preview": "预览模式"},
    }),
    (("AI生成连环画", "连环画"), {
        "fields": [_f("scene_title", "场景标题", ro=True), _f("dialogue_panels", "分镜面板", typ="array", ro=True),
                   _f("style", "画风", typ="enum", widget="select"), _f("generation_status", "生成状态", typ="enum", ro=True)],
        "actions": [{"label": "开始生成配图", "crud": "C", "frequency": "高"}, {"label": "重新生成某帧", "crud": "U", "frequency": "中"},
                    {"label": "调整画风", "crud": "U", "frequency": "低"}],
        "states": {"generating": "逐帧生成中+进度", "preview": "配图预览网格", "editing": "选中某帧重新生成", "complete": "全部配图生成完成"},
    }),
    (("发布场景包",), {
        "fields": [_f("scene_title", "场景标题", ro=True), _f("status", "当前状态", typ="enum", ro=True),
                   _f("content_check", "内容检查", typ="bool", ro=True), _f("image_check", "配图检查", typ="bool", ro=True),
                   _f("target_audience", "目标受众", typ="enum", widget="select")],
        "actions": [{"label": "发布", "crud": "U", "frequency": "高"}, {"label": "预览", "crud": "R", "frequency": "中"},
                    {"label": "返回编辑", "crud": "R", "frequency": "低"}],
        "states": {"ready": "所有检查通过，可发布", "incomplete": "有未完成项，不可发布", "publishing": "发布中", "published": "已发布"},
    }),
    # ── Admin: management ──
    (("管理员登录",), {
        "fields": [_f("username", "管理员账号", req=True), _f("password", "密码", widget="password", req=True),
                   _f("otp", "二次验证码")],
        "actions": [{"label": "登录后台", "crud": "R", "frequency": "高"}],
        "states": {"default": "登录表单", "otp_required": "需要二次验证", "error": "凭证错误", "success": "登录成功"},
    }),
    (("用户管理",), {
        "fields": [_f("user_id", "用户ID", ro=True), _f("nickname", "昵称", ro=True),
                   _f("email", "邮箱", ro=True), _f("subscription", "订阅状态", typ="enum", ro=True),
                   _f("registered_at", "注册时间", typ="date", ro=True), _f("last_active", "最后活跃", typ="date", ro=True)],
        "actions": [{"label": "搜索用户", "crud": "R", "frequency": "高"}, {"label": "查看详情", "crud": "R", "frequency": "高"},
                    {"label": "禁用账号", "crud": "U", "frequency": "低"}, {"label": "导出用户列表", "crud": "R", "frequency": "低"}],
        "states": {"default": "用户数据表格+搜索框", "detail": "用户详情侧边栏", "empty": "无搜索结果"},
    }),
    (("系统配置",), {
        "fields": [_f("free_download_limit", "免费下载限制", typ="int"), _f("pro_price", "Pro套餐价格", typ="float"),
                   _f("ai_model", "AI生成模型", typ="enum", widget="select"), _f("cache_ttl", "缓存有效期", typ="int"),
                   _f("maintenance_mode", "维护模式", typ="bool", widget="toggle")],
        "actions": [{"label": "保存配置", "crud": "U", "frequency": "高"}, {"label": "重置默认值", "crud": "U", "frequency": "低"}],
        "states": {"default": "配置项列表+当前值", "modified": "有未保存更改", "saved": "配置已保存"},
    }),
    (("下架", "更新场景包"), {
        "fields": [_f("scene_title", "场景名称", ro=True), _f("status", "当前状态", typ="enum", ro=True),
                   _f("download_count", "下载量", typ="int", ro=True), _f("reason", "下架原因", widget="textarea")],
        "actions": [{"label": "下架", "crud": "U", "frequency": "中"}, {"label": "重新上架", "crud": "U", "frequency": "中"},
                    {"label": "推送更新", "crud": "U", "frequency": "中"}],
        "states": {"default": "场景包状态+操作面板", "confirming": "下架确认弹窗", "archived": "已下架"},
    }),
    (("管理场景分类", "分类标签"), {
        "fields": [_f("tag_name", "标签名称", req=True), _f("tag_icon", "图标", typ="image"),
                   _f("scene_count", "关联场景数", typ="int", ro=True), _f("sort_order", "排序权重", typ="int")],
        "actions": [{"label": "新建标签", "crud": "C", "frequency": "中"}, {"label": "编辑标签", "crud": "U", "frequency": "中"},
                    {"label": "删除标签", "crud": "D", "frequency": "低"}, {"label": "拖拽排序", "crud": "U", "frequency": "中"}],
        "states": {"default": "标签列表+关联数量", "editing": "编辑标签弹窗", "empty": "暂无标签，点击创建"},
    }),
    (("管理prompt", "prompt模板"), {
        "fields": [_f("template_name", "模板名称", req=True), _f("prompt_text", "Prompt内容", widget="textarea", req=True),
                   _f("model", "适用模型", typ="enum", widget="select"), _f("version", "版本号", typ="int", ro=True),
                   _f("last_used", "最后使用", typ="date", ro=True)],
        "actions": [{"label": "新建模板", "crud": "C", "frequency": "中"}, {"label": "编辑模板", "crud": "U", "frequency": "高"},
                    {"label": "测试运行", "crud": "R", "frequency": "中"}, {"label": "查看历史版本", "crud": "R", "frequency": "低"}],
        "states": {"default": "模板列表+搜索", "editing": "模板编辑器", "testing": "测试运行中+结果预览"},
    }),
    # ── Admin: analytics ──
    (("学习数据仪表盘", "数据仪表盘"), {
        "fields": [_f("dau", "日活用户", typ="int", ro=True), _f("mau", "月活用户", typ="int", ro=True),
                   _f("avg_study_time", "平均学习时长", typ="float", ro=True), _f("retention_rate", "次日留存", typ="float", ro=True),
                   _f("conversion_rate", "付费转化率", typ="float", ro=True), _f("revenue", "收入", typ="float", ro=True)],
        "actions": [{"label": "切换时间范围", "crud": "R", "frequency": "高"}, {"label": "导出报告", "crud": "R", "frequency": "中"}],
        "states": {"default": "关键指标卡片+趋势图", "loading": "数据加载中", "date_range": "自定义时间范围"},
    }),
    (("场景包使用热度", "场景包热度"), {
        "fields": [_f("scene_title", "场景名称", ro=True), _f("download_count", "下载量", typ="int", ro=True),
                   _f("completion_rate", "完成率", typ="float", ro=True), _f("avg_rating", "平均评分", typ="float", ro=True),
                   _f("trend", "趋势", typ="enum", ro=True)],
        "actions": [{"label": "按热度排序", "crud": "R", "frequency": "高"}, {"label": "按完成率排序", "crud": "R", "frequency": "中"},
                    {"label": "导出数据", "crud": "R", "frequency": "低"}],
        "states": {"default": "热度排行榜+趋势图", "detail": "单个场景详细数据"},
    }),
    (("查看用户反馈", "用户反馈"), {
        "fields": [_f("user_name", "用户", ro=True), _f("feedback_type", "类型", typ="enum", ro=True),
                   _f("content", "反馈内容", ro=True), _f("submitted_at", "提交时间", typ="date", ro=True),
                   _f("status", "处理状态", typ="enum", ro=True), _f("reply", "回复", widget="textarea")],
        "actions": [{"label": "回复反馈", "crud": "U", "frequency": "高"}, {"label": "标记已处理", "crud": "U", "frequency": "高"},
                    {"label": "按类型筛选", "crud": "R", "frequency": "中"}],
        "states": {"default": "反馈列表+状态标签", "detail": "反馈详情+回复框", "empty": "暂无待处理反馈"},
    }),
    (("导出数据报告",), {
        "fields": [_f("report_type", "报告类型", typ="enum", widget="select", req=True),
                   _f("date_range", "时间范围", typ="daterange", widget="date_range_picker", req=True),
                   _f("format", "导出格式", typ="enum", widget="select"),
                   _f("include_charts", "包含图表", typ="bool", widget="toggle")],
        "actions": [{"label": "生成报告", "crud": "C", "frequency": "高"}, {"label": "下载报告", "crud": "R", "frequency": "高"}],
        "states": {"default": "报告参数配置", "generating": "报告生成中", "ready": "报告已生成，可下载", "error": "生成失败"},
    }),
    (("批量生成场景包", "批量生成"), {
        "fields": [_f("batch_count", "批量数量", typ="int", req=True), _f("category", "场景分类", typ="enum", widget="select"),
                   _f("difficulty_range", "难度范围", typ="enum", widget="select"),
                   _f("progress", "生成进度", typ="float", ro=True), _f("completed", "已完成数", typ="int", ro=True)],
        "actions": [{"label": "开始批量生成", "crud": "C", "frequency": "高"}, {"label": "暂停", "crud": "U", "frequency": "中"},
                    {"label": "查看已生成", "crud": "R", "frequency": "中"}],
        "states": {"config": "参数配置+预估时间", "running": "批量生成中+进度条+实时日志", "paused": "已暂停", "complete": "全部完成+结果摘要"},
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

            # Build screens for this node
            node_screens, screen_counter = build_screens_for_node(
                node_tasks, tasks_inv, screen_counter,
                ux_intent=en.get("design_hint", ""),
                emotion_intensity=en.get("intensity", 5),
                vo_lookup=vo_lookup,
                audience_type=jl_audience,
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
