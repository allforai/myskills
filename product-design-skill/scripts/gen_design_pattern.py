#!/usr/bin/env python3
"""Generate design pattern catalog: detect 8 pattern types, build catalog + report.

Pre-built script for Phase 3.5 (design-pattern). Detects:
- PT-CRUD, PT-LIST-DETAIL, PT-APPROVAL, PT-SEARCH,
- PT-EXPORT, PT-NOTIFY, PT-PERMISSION, PT-STATE

Usage:
    python3 gen_design_pattern.py <BASE_PATH> [--mode auto] [--shard design-pattern]
"""

import os
import sys
import re
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C

# ── Setup ─────────────────────────────────────────────────────────────────────
BASE, args = C.parse_args()
OUT = os.path.join(BASE, "design-pattern")
C.ensure_dir(OUT)
NOW = C.now_iso()

# ── Load data ─────────────────────────────────────────────────────────────────
tasks = C.load_task_inventory(BASE)
screens, has_screens = C.load_screen_map(BASE)
flows = C.load_business_flows(BASE)

screen_by_id = C.build_screen_by_id(screens)
task_screen_map = C.build_task_screen_map(screens)

# ── Helpers ───────────────────────────────────────────────────────────────────

# Chinese verbs to strip from task names (order: longer first for greedy match)
CRUD_VERBS_ZH = re.compile(
    r"^(创建|新建|新增|添加|编辑|修改|更新|删除|移除|"
    r"查看|查询|获取|列出|浏览|搜索|管理|配置|设置|"
    r"提交|审核|发布|撤回|发起|处理|生成)"
)
CRUD_VERBS_EN = re.compile(
    r"^(create|add|new|edit|modify|update|delete|remove|view|query|list|browse|"
    r"search|manage|get|fetch|configure|set up|submit|review|publish)\s+",
    re.IGNORECASE,
)

# Suffixes to strip from entity names after verb removal
ENTITY_SUFFIXES_ZH = re.compile(r"(列表|详情|页|信息|概览|草稿|报告|统计|摘要|记录|结果)$")


def extract_entity(task_name):
    """Extract entity name from task name by stripping verbs and suffixes."""
    name = task_name.strip()
    # Strip verb prefix
    stripped = CRUD_VERBS_ZH.sub("", name)
    if stripped == name:
        stripped = CRUD_VERBS_EN.sub("", name)
    stripped = stripped.strip()
    # Strip view-type suffixes
    stripped = ENTITY_SUFFIXES_ZH.sub("", stripped).strip()
    return stripped if stripped else name


def classify_crud_action(task_name):
    """Classify a task as create/read/update/delete or 'manage' (all-in-one)."""
    name = task_name.lower()
    # "管理 X" implies full CRUD
    if any(v in name for v in ["管理", "manage"]):
        return "manage"
    if any(v in name for v in ["创建", "新建", "新增", "添加", "create", "add", "new"]):
        return "create"
    if any(v in name for v in ["查看", "查询", "获取", "列出", "列表", "浏览", "搜索",
                                "view", "query", "list", "browse", "search", "get"]):
        return "read"
    if any(v in name for v in ["编辑", "修改", "更新", "配置", "设置",
                                "edit", "modify", "update", "configure"]):
        return "update"
    if any(v in name for v in ["删除", "移除", "delete", "remove"]):
        return "delete"
    return None


def _slugify(text):
    """Create a URL-friendly slug from text."""
    return re.sub(r"\W+", "-", text.lower()).strip("-") or "unnamed"


def _merge_entity_groups(groups):
    """Merge entity groups where one entity name is a substring of another.

    For example, "X" and "YX" should be merged under "YX" (longer = more specific).
    Returns merged dict: {canonical_entity: [items]}.
    """
    entities = sorted(groups.keys(), key=len, reverse=True)  # longest first
    merged = {}
    alias_map = {}  # entity → canonical

    for entity in entities:
        if entity in alias_map:
            continue
        canonical = entity
        # Check if this entity is a substring of an already-established canonical
        for existing in list(merged.keys()):
            if len(entity) >= 2 and entity in existing:
                alias_map[entity] = existing
                canonical = existing
                break
            elif len(existing) >= 2 and existing in entity:
                # existing is a substring of entity → entity is more specific, adopt it
                alias_map[existing] = entity
                merged[entity] = merged.pop(existing) + groups[entity]
                canonical = entity
                break
        if canonical == entity and entity not in merged:
            merged[entity] = list(groups[entity])
        elif canonical != entity:
            merged[canonical].extend(groups[entity])

    return merged


def _extract_screen_entity(screen_name):
    """Extract entity from screen name by stripping UI suffixes (iteratively)."""
    name = screen_name.strip()
    # Strip parenthetical qualifiers like （管理端）
    name = re.sub(r"[（(].*?[）)]", "", name).strip()
    # Iteratively strip suffixes until stable
    suffix_re = re.compile(r"(页|界面|面板|弹窗|对话框|列表|详情|管理|编辑|创建|审核|监控|配置|队列)$")
    for _ in range(5):
        stripped = suffix_re.sub("", name).strip()
        if stripped == name:
            break
        name = stripped
    return name


# ── Tag accumulators ──────────────────────────────────────────────────────────
patterns = []
all_task_tags = {}    # task_id → {_pattern: [...], _pattern_template: "..."}
all_screen_tags = {}  # screen_id → {_pattern: [...], _pattern_template: "...", _pattern_group: "..."}


def tag_task(tid, pattern_id, template):
    if tid not in all_task_tags:
        all_task_tags[tid] = {"_pattern": [], "_pattern_template": ""}
    if pattern_id not in all_task_tags[tid]["_pattern"]:
        all_task_tags[tid]["_pattern"].append(pattern_id)
    cur = all_task_tags[tid]["_pattern_template"]
    all_task_tags[tid]["_pattern_template"] = (cur + "+" + template) if cur else template


def tag_screen(sid, pattern_id, template, group_id=""):
    if sid not in all_screen_tags:
        all_screen_tags[sid] = {"_pattern": [], "_pattern_template": "", "_pattern_group": ""}
    if pattern_id not in all_screen_tags[sid]["_pattern"]:
        all_screen_tags[sid]["_pattern"].append(pattern_id)
    cur = all_screen_tags[sid]["_pattern_template"]
    all_screen_tags[sid]["_pattern_template"] = (cur + "+" + template) if cur else template
    if group_id:
        all_screen_tags[sid]["_pattern_group"] = group_id


# ═════════════════════════════════════════════════════════════════════════════
# Pattern Detection
# ═════════════════════════════════════════════════════════════════════════════

# ── PT-CRUD: CRUD management (threshold: ≥3 actions per entity, or "管理" verb) ─
entity_crud_raw = defaultdict(list)
for tid, task in tasks.items():
    entity = extract_entity(task["name"])
    action = classify_crud_action(task["name"])
    if action:
        entity_crud_raw[entity].append({"task_id": tid, "action": action})

# Merge entities with substring overlap
entity_crud_groups = _merge_entity_groups(entity_crud_raw)

crud_instances = []
for entity, items in entity_crud_groups.items():
    actions = set()
    for item in items:
        if item["action"] == "manage":
            actions.update({"create", "read", "update", "delete"})
        else:
            actions.add(item["action"])
    if len(actions) >= 3:
        tids = [item["task_id"] for item in items]
        sids = []
        for tid in tids:
            for s in task_screen_map.get(tid, []):
                if s["id"] not in sids:
                    sids.append(s["id"])
        group_id = _slugify(entity) + "-crud"
        crud_instances.append({
            "group_id": group_id,
            "entity": entity,
            "task_ids": tids,
            "screen_ids": sids,
            "actions_found": sorted(actions),
            "template": "顶部操作栏+数据表格+弹窗表单",
            "user_decision": "auto",
        })
        for tid in tids:
            tag_task(tid, "PT-CRUD", "顶部操作栏+数据表格")
        for sid in sids:
            tag_screen(sid, "PT-CRUD", "顶部操作栏+数据表格", group_id)

if crud_instances:
    patterns.append({
        "pattern_id": "PT-CRUD",
        "name": "CRUD 管理台",
        "instances": crud_instances,
        "total_instances": len(crud_instances),
    })

# ── PT-LIST-DETAIL: list + detail pairs (threshold: 2+ pairs) ────────────────
# Pair screens by name similarity: list-like screen paired with detail-like screen
# sharing a common entity substring
LIST_KW = {"列表", "list", "概览", "overview"}
DETAIL_KW = {"详情", "detail", "info"}

list_screens_for_ld = [s for s in screens
                       if any(kw in s.get("name", "").lower() for kw in LIST_KW)]
detail_screens_for_ld = [s for s in screens
                         if any(kw in s.get("name", "").lower() for kw in DETAIL_KW)]

list_detail_pairs = []
seen_pairs = set()
for ls in list_screens_for_ld:
    ls_entity = _extract_screen_entity(ls.get("name", ""))
    ls_tasks = set(C.get_screen_tasks(ls))
    for ds in detail_screens_for_ld:
        if ls["id"] == ds["id"]:
            continue
        pair_key = (ls["id"], ds["id"])
        if pair_key in seen_pairs:
            continue
        ds_entity = _extract_screen_entity(ds.get("name", ""))
        # Match by entity name overlap (either is substring of the other, min 2 chars)
        entity_match = (
            (len(ls_entity) >= 2 and ls_entity in ds_entity) or
            (len(ds_entity) >= 2 and ds_entity in ls_entity)
        )
        # Also match by shared task refs
        ds_tasks = set(C.get_screen_tasks(ds))
        task_overlap = ls_tasks & ds_tasks
        if entity_match or task_overlap:
            seen_pairs.add(pair_key)
            merged_tasks = ls_tasks | ds_tasks
            list_detail_pairs.append((ls["id"], ds["id"], merged_tasks))

list_detail_instances = []
if len(list_detail_pairs) >= 2:
    for ls_id, ds_id, pair_tasks in list_detail_pairs:
        entity = _extract_screen_entity(screen_by_id[ls_id].get("name", ""))
        group_id = (_slugify(entity) + "-list-detail") if entity else f"{ls_id}-list-detail"
        tids = sorted(pair_tasks)
        list_detail_instances.append({
            "group_id": group_id,
            "entity": entity or ls_id,
            "task_ids": tids,
            "screen_ids": [ls_id, ds_id],
            "template": "主列表+右侧详情面板",
            "user_decision": "auto",
        })
        for tid in tids:
            tag_task(tid, "PT-LIST-DETAIL", "主列表+右侧详情面板")
        tag_screen(ls_id, "PT-LIST-DETAIL", "主列表+右侧详情面板", group_id)
        tag_screen(ds_id, "PT-LIST-DETAIL", "主列表+右侧详情面板", group_id)

    patterns.append({
        "pattern_id": "PT-LIST-DETAIL",
        "name": "列表+详情对",
        "instances": list_detail_instances,
        "total_instances": len(list_detail_instances),
    })

# ── PT-APPROVAL: approval flow (threshold: 1+ flow) ─────────────────────────
approval_instances = []
for flow in flows:
    nodes = C.get_flow_nodes(flow)
    node_labels = []
    for n in nodes:
        if isinstance(n, str):
            # Bare task_id string — resolve to task name
            label = n.lower()
            if n in tasks:
                label += " " + tasks[n]["name"].lower()
            node_labels.append(label)
        elif isinstance(n, dict):
            label = (n.get("label", "") + " " + n.get("task_ref", "")).lower()
            # Also resolve task_ref to task name for keyword matching
            tref = n.get("task_ref", "")
            if tref in tasks:
                label += " " + tasks[tref]["name"].lower()
            node_labels.append(label)
    flow_text = " ".join(node_labels)
    flow_name = flow.get("name", "").lower()
    combined = flow_text + " " + flow_name

    has_submit = any(kw in combined for kw in ["submit", "提交", "发起"])
    has_review = any(kw in combined for kw in ["review", "审核", "审批", "审查"])
    has_verdict = any(kw in combined for kw in [
        "approve", "reject", "通过", "驳回", "拒绝", "批准", "退回",
    ])

    if (has_submit and has_review) or (has_review and has_verdict):
        tids = []
        for n in nodes:
            if isinstance(n, dict) and n.get("task_ref"):
                tids.append(n["task_ref"])
            elif isinstance(n, str) and n in tasks:
                tids.append(n)
        approval_instances.append({
            "group_id": f"{flow.get('id', 'flow')}-approval",
            "entity": flow.get("name", ""),
            "task_ids": tids,
            "screen_ids": [],
            "template": "流程时间轴+审批意见区",
            "user_decision": "auto",
        })
        for tid in tids:
            tag_task(tid, "PT-APPROVAL", "流程时间轴+审批意见区")

if len(approval_instances) >= 1:
    patterns.append({
        "pattern_id": "PT-APPROVAL",
        "name": "审批流",
        "instances": approval_instances,
        "total_instances": len(approval_instances),
    })

# ── PT-SEARCH: search + filter + pagination (threshold: 2+ screens) ─────────
SEARCH_KW = {"search", "filter", "query", "搜索", "筛选", "查询", "过滤"}
PAGE_KW = {"paginate", "page", "分页", "翻页", "pagination"}

search_screens = []
for s in screens:
    actions = s.get("actions", [])
    action_text = " ".join(
        (a.get("label", "") + " " + a.get("type", "")).lower() for a in actions
    )
    screen_text = (s.get("name", "") + " " + action_text).lower()
    has_search = any(kw in screen_text for kw in SEARCH_KW)
    has_page = any(kw in screen_text for kw in PAGE_KW)
    if has_search and has_page:
        search_screens.append(s)
    elif has_search and len(actions) >= 2:
        # Relaxed: search/filter with 2+ actions suggests a search-capable screen
        search_screens.append(s)

search_instances = []
if len(search_screens) >= 2:
    for s in search_screens:
        tids = C.get_screen_tasks(s)
        search_instances.append({
            "group_id": f"{s['id']}-search",
            "entity": s.get("name", ""),
            "task_ids": tids,
            "screen_ids": [s["id"]],
            "template": "顶部筛选栏+分页器",
            "user_decision": "auto",
        })
        tag_screen(s["id"], "PT-SEARCH", "顶部筛选栏+分页器", f"{s['id']}-search")
        for tid in tids:
            tag_task(tid, "PT-SEARCH", "顶部筛选栏+分页器")

    patterns.append({
        "pattern_id": "PT-SEARCH",
        "name": "搜索+筛选+分页",
        "instances": search_instances,
        "total_instances": len(search_instances),
    })

# ── PT-EXPORT: export / report (threshold: 2+ tasks) ────────────────────────
EXPORT_KW = {"export", "report", "download", "导出", "报表", "下载"}

export_tasks = []
for tid, task in tasks.items():
    name = task["name"].lower()
    actions_text = " ".join(
        a.get("label", "").lower()
        for s in task_screen_map.get(tid, [])
        for a in s.get("actions", [])
    )
    if any(kw in name or kw in actions_text for kw in EXPORT_KW):
        export_tasks.append(tid)

if len(export_tasks) >= 2:
    sids = []
    for tid in export_tasks:
        for s in task_screen_map.get(tid, []):
            if s["id"] not in sids:
                sids.append(s["id"])
    patterns.append({
        "pattern_id": "PT-EXPORT",
        "name": "导出/报表",
        "instances": [{
            "group_id": "export-group",
            "entity": "导出功能",
            "task_ids": export_tasks,
            "screen_ids": sids,
            "template": "导出按钮+导出配置弹窗",
            "user_decision": "auto",
        }],
        "total_instances": 1,
    })
    for tid in export_tasks:
        tag_task(tid, "PT-EXPORT", "导出按钮+导出配置弹窗")
    for sid in sids:
        tag_screen(sid, "PT-EXPORT", "导出按钮+导出配置弹窗", "export-group")
else:
    print(f"  PT-EXPORT: {len(export_tasks)} tasks < threshold 2, skipped")

# ── PT-NOTIFY: notification triggers (threshold: 2+ flow nodes) ──────────────
NOTIFY_KW = {"notify", "send", "push", "通知", "发送", "推送"}

notify_nodes = []
for flow in flows:
    for i, node in enumerate(C.get_flow_nodes(flow)):
        label = ""
        if isinstance(node, str):
            label = node.lower()
        elif isinstance(node, dict):
            label = (node.get("label", "") + " " + node.get("type", "")).lower()
        if any(kw in label for kw in NOTIFY_KW):
            notify_nodes.append({
                "flow_id": flow.get("id", ""),
                "node_index": i,
                "label": label,
            })

if len(notify_nodes) >= 2:
    tids = sorted(set(
        n.get("task_ref", "")
        for flow in flows
        for n in C.get_flow_nodes(flow)
        if isinstance(n, dict)
        and any(kw in (n.get("label", "") + " " + n.get("type", "")).lower()
                for kw in NOTIFY_KW)
        and n.get("task_ref")
    ))
    patterns.append({
        "pattern_id": "PT-NOTIFY",
        "name": "通知触发",
        "instances": [{
            "group_id": "notify-group",
            "entity": "通知",
            "task_ids": tids,
            "screen_ids": [],
            "template": "系统级通知中心",
            "user_decision": "auto",
        }],
        "total_instances": 1,
    })
    for tid in tids:
        tag_task(tid, "PT-NOTIFY", "系统级通知中心")
else:
    print(f"  PT-NOTIFY: {len(notify_nodes)} flow nodes < threshold 2, skipped")

# ── PT-PERMISSION: permission matrix (threshold: 1+ entity with 3+ roles) ───
entity_role_actions = defaultdict(lambda: defaultdict(set))
for tid, task in tasks.items():
    entity = extract_entity(task["name"])
    action = classify_crud_action(task["name"])
    role = task.get("role", "")
    if action and role:
        if action == "manage":
            entity_role_actions[entity][role].update({"create", "read", "update", "delete"})
        else:
            entity_role_actions[entity][role].add(action)

# Merge entities with substring overlap for permission check
merged_perm = _merge_entity_groups(entity_role_actions)

permission_entities = []
for entity, role_actions in merged_perm.items():
    # role_actions here might be a list from merge; rebuild as dict
    if isinstance(role_actions, list):
        # Merge came from defaultdict items flattened — skip
        continue
    if len(role_actions) >= 3:
        action_sets = [frozenset(v) for v in role_actions.values()]
        if len(set(action_sets)) > 1:
            tids = [item["task_id"]
                    for item in entity_crud_groups.get(entity, entity_crud_raw.get(entity, []))]
            group_id = _slugify(entity) + "-permission"
            permission_entities.append({
                "group_id": group_id,
                "entity": entity,
                "task_ids": tids,
                "screen_ids": [],
                "roles": {r: sorted(a) for r, a in role_actions.items()},
                "template": "权限开关矩阵",
                "user_decision": "auto",
            })
            for tid in tids:
                tag_task(tid, "PT-PERMISSION", "权限开关矩阵")

if len(permission_entities) >= 1:
    patterns.append({
        "pattern_id": "PT-PERMISSION",
        "name": "权限矩阵",
        "instances": permission_entities,
        "total_instances": len(permission_entities),
    })

# ── PT-STATE: state machine (threshold: 2+ tasks) ───────────────────────────
STATE_KW = {"status", "state", "状态"}
TRANSITION_KW = {
    "approve", "reject", "cancel", "archive", "activate",
    "publish", "suspend", "complete", "close", "open",
    "审批", "驳回", "取消", "归档", "激活", "发布", "暂停", "完成", "关闭", "开启",
    "启用", "禁用", "上架", "下架", "封禁", "解封", "恢复",
}

state_tasks = []
for tid, task in tasks.items():
    name = task["name"].lower()
    desc = (task.get("description") or "").lower()
    combined = name + " " + desc

    has_state = any(kw in combined for kw in STATE_KW)
    has_transition = any(kw in combined for kw in TRANSITION_KW)

    if not has_transition and tid in task_screen_map:
        for s in task_screen_map[tid]:
            for a in s.get("actions", []):
                if any(kw in a.get("label", "").lower() for kw in TRANSITION_KW):
                    has_transition = True
                    break
            if has_transition:
                break

    if has_state or has_transition:
        state_tasks.append(tid)

if len(state_tasks) >= 2:
    sids = []
    for tid in state_tasks:
        for s in task_screen_map.get(tid, []):
            if s["id"] not in sids:
                sids.append(s["id"])
    patterns.append({
        "pattern_id": "PT-STATE",
        "name": "状态机",
        "instances": [{
            "group_id": "state-machine",
            "entity": "状态管理",
            "task_ids": state_tasks,
            "screen_ids": sids,
            "template": "状态标签+动态操作按钮",
            "user_decision": "auto",
        }],
        "total_instances": 1,
    })
    for tid in state_tasks:
        tag_task(tid, "PT-STATE", "状态标签+动态操作按钮")
    for sid in sids:
        tag_screen(sid, "PT-STATE", "状态标签+动态操作按钮", "state-machine")
else:
    print(f"  PT-STATE: {len(state_tasks)} tasks < threshold 2, skipped")


# ═════════════════════════════════════════════════════════════════════════════
# Output
# ═════════════════════════════════════════════════════════════════════════════

total_instances = sum(p["total_instances"] for p in patterns)

# No patterns above threshold → skip
if not patterns:
    print("Phase 3.5: no patterns detected above threshold, skipping")
    C.append_pipeline_decision(
        BASE,
        "Phase 3.5 — design-pattern",
        "0 patterns detected (all below threshold), skipped",
        shard=args.get("shard"),
    )
    sys.exit(0)

# ── pattern-catalog.json ─────────────────────────────────────────────────────
catalog = {
    "created_at": NOW,
    "total_patterns_detected": len(patterns),
    "patterns": patterns,
    "task_tags": all_task_tags,
    "screen_tags": all_screen_tags,
    "tasks_tagged": len(all_task_tags),
    "screens_tagged": len(all_screen_tags),
}
C.write_json(os.path.join(OUT, "pattern-catalog.json"), catalog)

# ── pattern-report.md ────────────────────────────────────────────────────────
lines = []
lines.append("# Phase 3.5 — 设计模式分析报告\n")
lines.append("## 概览\n")
lines.append("| 指标 | 值 |")
lines.append("|------|-----|")
lines.append(f"| 检测模式数 | {len(patterns)} 类 |")
lines.append(f"| 模式实例总数 | {total_instances} 个 |")
lines.append(f"| 标注 Tasks | {len(all_task_tags)} 个 |")
lines.append(f"| 标注 Screens | {len(all_screen_tags)} 个 |\n")

lines.append("## 检测到的模式\n")
lines.append("| 模式 | 实例数 | 涉及 Tasks | 涉及 Screens | 推荐模板 |")
lines.append("|------|--------|-----------|------------|--------|")
for p in patterns:
    all_tids = sorted(set(t for inst in p["instances"] for t in inst["task_ids"]))
    all_sids = sorted(set(s for inst in p["instances"] for s in inst["screen_ids"]))
    tids_str = ",".join(all_tids[:8])
    if len(all_tids) > 8:
        tids_str += "..."
    sids_str = ",".join(all_sids[:8]) or "—"
    if len(all_sids) > 8:
        sids_str += "..."
    template = p["instances"][0]["template"] if p["instances"] else "—"
    lines.append(f"| {p['name']} | {p['total_instances']} | {tids_str} | {sids_str} | {template} |")

# Skipped patterns
ALL_PATTERN_IDS = {"PT-CRUD", "PT-LIST-DETAIL", "PT-APPROVAL", "PT-SEARCH",
                   "PT-EXPORT", "PT-NOTIFY", "PT-PERMISSION", "PT-STATE"}
detected_ids = {p["pattern_id"] for p in patterns}
skipped_ids = sorted(ALL_PATTERN_IDS - detected_ids)

if skipped_ids:
    skip_counts = {
        "PT-CRUD": len(crud_instances),
        "PT-LIST-DETAIL": len(list_detail_pairs),
        "PT-APPROVAL": len(approval_instances),
        "PT-SEARCH": len(search_screens),
        "PT-EXPORT": len(export_tasks),
        "PT-NOTIFY": len(notify_nodes),
        "PT-PERMISSION": len(permission_entities),
        "PT-STATE": len(state_tasks),
    }
    skip_thresholds = {
        "PT-CRUD": "≥1 entity with ≥3 CRUD actions",
        "PT-LIST-DETAIL": "≥2 pairs",
        "PT-APPROVAL": "≥1 flow",
        "PT-SEARCH": "≥2 screens",
        "PT-EXPORT": "≥2 tasks",
        "PT-NOTIFY": "≥2 flow nodes",
        "PT-PERMISSION": "≥1 entity with 3+ roles",
        "PT-STATE": "≥2 tasks",
    }
    lines.append("\n## 未检测到的模式\n")
    for pid in skipped_ids:
        count = skip_counts.get(pid, 0)
        threshold = skip_thresholds.get(pid, "")
        lines.append(f"- {pid} — found {count}, need {threshold}")

with open(os.path.join(OUT, "pattern-report.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

# ── Pipeline decisions ────────────────────────────────────────────────────────
pattern_summary = ", ".join(
    f"{p['pattern_id']}({p['total_instances']})" for p in patterns
)
skipped_summary = ", ".join(skipped_ids) if skipped_ids else "none"

C.append_pipeline_decision(
    BASE,
    "Phase 3.5 — design-pattern",
    f"{len(patterns)} patterns detected ({total_instances} instances), "
    f"{len(all_task_tags)} tasks tagged, {len(all_screen_tags)} screens tagged. "
    f"Detected: {pattern_summary}. "
    f"Skipped: {skipped_summary}",
    shard=args.get("shard"),
)

# ── Summary ───────────────────────────────────────────────────────────────────
print(f"Patterns detected: {len(patterns)} ({total_instances} instances)")
print(f"Tasks tagged: {len(all_task_tags)}")
print(f"Screens tagged: {len(all_screen_tags)}")
for p in patterns:
    print(f"  {p['pattern_id']}: {p['total_instances']} instances")
for pid in skipped_ids:
    print(f"  {pid}: skipped (below threshold)")
print(f"\nAll files written to {OUT}/")
