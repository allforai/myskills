#!/usr/bin/env python3
"""Generate screen-map.json, screen-index.json, and screen-map-report.md.

Pre-built script for Phase 3 (screen-map). Reads task-inventory, task-index,
role-profiles, product-concept (optional), and adversarial-concepts (optional).

Groups tasks into logical screens by module, generates actions from task
metadata, calculates flags and pareto analysis.

Usage:
    python3 gen_screen_map.py <BASE_PATH> [--mode auto] [--shard screen-map]
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C

# ── Setup ─────────────────────────────────────────────────────────────────────
BASE, args = C.parse_args()  # args is dict: {"mode": "auto", "shard": "screen-map", ...}
OUT = os.path.join(BASE, "screen-map")
C.ensure_dir(OUT)
NOW = C.now_iso()

# ── Load data ─────────────────────────────────────────────────────────────────
tasks_by_id = C.load_task_inventory(BASE)
idx = C.load_task_index(BASE)
if idx is None:
    print("WARNING: task-index.json not found, grouping by owner_role")
    idx = {"modules": []}
role_map = C.load_role_profiles(BASE)
roles_full = C.load_role_profiles_full(BASE)

# Role audience type mapping
role_audience = {}
for r in roles_full:
    role_audience[r["id"]] = r.get("audience_type", "default")

# Product concept (optional)
concept = C.load_product_concept(BASE)
errc_eliminate = []
concept_mode = "none"
if concept and "competitive_position" in concept:
    errc = concept["competitive_position"].get("errc", {})
    errc_eliminate = errc.get("eliminate", [])
    concept_mode = "active"

# Adversarial concepts (optional)
adv_concepts = C.load_json(os.path.join(BASE, "product-concept/adversarial-concepts.json"))
innovation_map = {}  # task_id -> concept
if adv_concepts:
    for c in adv_concepts.get("concepts", []):
        for tid in c.get("task_ids", []):
            innovation_map[tid] = c

# Filter out user_removed tasks
active_tasks = {tid: t for tid, t in tasks_by_id.items()
                if t.get("status") != "user_removed"}

print(f"Loaded {len(active_tasks)} active tasks ({len(tasks_by_id) - len(active_tasks)} removed)")

# ── Module grouping ──────────────────────────────────────────────────────────
modules = []
if idx.get("modules"):
    modules = idx["modules"]
else:
    # Fallback: group by owner_role
    by_role = {}
    for tid, t in active_tasks.items():
        role = t.get("owner_role", "unknown")
        by_role.setdefault(role, []).append(t)
    for role_id, tasks in by_role.items():
        role_name = role_map.get(role_id, role_id)
        modules.append({
            "name": f"{role_name}管理",
            "tasks": [{"id": t["id"], "name": t["name"]} for t in tasks]
        })

# ── Audience type helpers ────────────────────────────────────────────────────

AUDIENCE_PROFILES = {
    "default":      {"overloaded": 5, "hfb_depth": 3, "primary_depth": 1, "confirm_risk": "高"},
    "consumer":     {"overloaded": 3, "hfb_depth": 3, "primary_depth": 1, "confirm_risk": "中"},
    "professional": {"overloaded": 8, "hfb_depth": 5, "primary_depth": 2, "confirm_risk": "高"},
}

def resolve_audience(role_ids):
    """Resolve audience type from role IDs."""
    types = set()
    for rid in role_ids:
        types.add(role_audience.get(rid, "default"))
    if not types or types == {"default"}:
        return "default"
    if "consumer" in types:
        return "consumer"  # mixed → consumer (strict side)
    return "professional"


def get_profile(audience):
    return AUDIENCE_PROFILES.get(audience, AUDIENCE_PROFILES["default"])


# ── CRUD inference ───────────────────────────────────────────────────────────

CRUD_KEYWORDS = {
    "C": ["新增", "创建", "新建", "添加", "注册", "发布", "提交", "申请", "录入", "上传"],
    "U": ["修改", "编辑", "更新", "调整", "变更", "设置", "配置", "审批", "审核", "处理"],
    "D": ["删除", "移除", "取消", "撤回", "作废", "停用", "注销", "禁用"],
    "R": ["查看", "查询", "搜索", "浏览", "导出", "下载", "统计", "报表", "列表"],
}


def infer_crud(task_name):
    """Infer CRUD type from task name."""
    for crud, keywords in CRUD_KEYWORDS.items():
        for kw in keywords:
            if kw in task_name:
                return crud
    return "R"  # default to Read


# ── Interaction type inference ───────────────────────────────────────────────

def infer_interaction_type(actions, task_count):
    """Infer interaction type from action CRUD distribution."""
    cruds = set(a["crud"] for a in actions)
    has_c = "C" in cruds
    has_u = "U" in cruds
    has_d = "D" in cruds
    has_r = "R" in cruds

    if has_c and has_u and has_d:
        return "MG2"  # Full CRUD cluster
    if has_c and has_u:
        return "MG3"  # State machine (create + update, no delete)
    if has_c and not has_u and not has_d:
        return "MG5"  # Create-only (submission)
    if has_u and not has_c:
        return "MG3"  # State/status update
    if has_d and not has_c:
        return "MG3"
    if has_r and not has_c and not has_u and not has_d:
        if task_count > 1:
            return "MG1"  # Read-only list
        return "MG5"  # Single detail view
    return "MG1"


# ── Screen generation ────────────────────────────────────────────────────────

FREQ_ORDER = {"高": 3, "中": 2, "低": 1}
screens = []
screen_counter = 0


def next_screen_id():
    global screen_counter
    screen_counter += 1
    return f"S{screen_counter:03d}"


for mod in modules:
    mod_task_ids = [t["id"] if isinstance(t, dict) else t for t in mod.get("tasks", [])]
    mod_tasks = [active_tasks[tid] for tid in mod_task_ids if tid in active_tasks]

    if not mod_tasks:
        continue

    # Group tasks within module by semantic similarity (simple: by CRUD pattern)
    # Tasks with C/U/D go to a management screen, R-only tasks to a list screen
    mgmt_tasks = []
    read_tasks = []
    for t in mod_tasks:
        crud = infer_crud(t["name"])
        if crud in ("C", "U", "D"):
            mgmt_tasks.append((t, crud))
        else:
            read_tasks.append((t, crud))

    # If all tasks are read-only, make one list screen
    # If mixed, make management screen(s) + optional list screen
    screen_groups = []
    if mgmt_tasks:
        screen_groups.append(("mgmt", mgmt_tasks))
    if read_tasks:
        screen_groups.append(("list", read_tasks))
    if not screen_groups:
        continue

    for group_type, task_tuples in screen_groups:
        sid = next_screen_id()
        task_ids = [t["id"] for t, _ in task_tuples]
        all_roles = set()
        actions = []

        for task, crud in task_tuples:
            tid = task["id"]
            freq = task.get("frequency", "低")
            risk = task.get("risk_level", "低")
            owner = task.get("owner_role", "")
            if owner:
                all_roles.add(owner)

            # Determine click depth based on CRUD and frequency
            if crud == "R":
                depth = 1
            elif crud == "C":
                depth = 1 if freq == "高" else 2
            elif crud == "U":
                depth = 2
            else:  # D
                depth = 2

            # Determine requires_confirm
            needs_confirm = crud == "D" or risk in ("高", "中")

            # Build validation rules from task.rules
            val_rules = []
            for rule in task.get("rules", []):
                if any(kw in rule for kw in ["必填", "必须", "≥", "≤", ">", "<", "限",
                                              "格式", "长度", "范围", "不可"]):
                    val_rules.append(rule)

            # Build exception flows from task.exceptions
            exc_flows = []
            for exc in task.get("exceptions", []):
                parts = exc.split("→")
                if len(parts) >= 2:
                    exc_flows.append(f"{parts[0].strip()} → {parts[1].strip()}")
                else:
                    exc_flows.append(f"{exc} → 系统提示异常信息")

            # On failure text
            if crud == "C":
                on_fail = "高亮必填字段，顶部显示错误汇总"
            elif crud == "U":
                on_fail = "提示修改失败原因，保留已填内容"
            elif crud == "D":
                on_fail = f"提示{task['name']}失败原因"
            else:
                on_fail = "提示加载失败，显示重试按钮"

            action = {
                "label": task["name"],
                "crud": crud,
                "frequency": freq,
                "click_depth": depth,
                "is_primary": False,  # calculated below
                "roles": [owner] if owner else [],
                "requires_confirm": needs_confirm,
                "on_failure": on_fail,
                "on_success": "",
                "validation_rules": val_rules,
                "exception_flows": exc_flows,
            }
            actions.append(action)

        # Resolve audience type
        audience = resolve_audience(all_roles)
        profile = get_profile(audience)

        # Calculate is_primary
        for a in actions:
            f_val = FREQ_ORDER.get(a["frequency"], 0)
            a["is_primary"] = (f_val >= 3 and a["click_depth"] <= profile["primary_depth"])

        # Pareto analysis
        sorted_actions = sorted(actions, key=lambda a: FREQ_ORDER.get(a["frequency"], 0), reverse=True)
        high_freq = [a["label"] for a in sorted_actions if a["frequency"] == "高"]
        hf_buried = [a["label"] for a in sorted_actions
                     if a["frequency"] == "高" and a["click_depth"] >= profile["hfb_depth"]]
        lf_shallow = [a["label"] for a in sorted_actions
                      if a["frequency"] == "低" and a["click_depth"] <= 1]

        # Screen-level flags
        flags = []
        if len(task_ids) > profile["overloaded"]:
            flags.append("OVERLOADED")
        if hf_buried:
            flags.append("HIGH_FREQ_BURIED")
        # Check primary mismatch
        if actions:
            highest_freq_label = sorted_actions[0]["label"]
            primaries = [a for a in actions if a["is_primary"]]
            if primaries and primaries[0]["label"] != highest_freq_label:
                flags.append("PRIMARY_MISMATCH")

        # Screen name
        mod_name = mod["name"]
        if group_type == "list":
            screen_name = f"{mod_name}列表"
            desc = f"查看和筛选{mod_name}相关数据"
            purpose = f"浏览{mod_name}信息"
            itype = "MG1"
        else:
            screen_name = f"{mod_name}管理"
            desc = f"管理{mod_name}的增删改查操作"
            purpose = f"完成{mod_name}的日常管理操作"
            itype = infer_interaction_type(actions, len(task_ids))

        # Entry point
        entry = "侧边栏菜单"
        if audience == "consumer":
            entry = "底部导航 Tab"

        # Innovation check
        innovation_screen = False
        adv_ref = None
        adv_dir = None
        for tid in task_ids:
            if tid in innovation_map:
                innovation_screen = True
                ic = innovation_map[tid]
                adv_ref = ic.get("id")
                adv_dir = ic.get("direction", "")
                break

        # States
        states = {
            "empty": f"暂无{mod_name}数据，提示用户新建" if group_type == "mgmt"
                     else f"暂无{mod_name}数据",
            "loading": "加载中，显示骨架屏",
            "error": "网络错误，显示重试按钮",
        }

        screen = {
            "id": sid,
            "name": screen_name,
            "description": desc,
            "interaction_type": itype,
            "primary_purpose": purpose,
            "primary_action": sorted_actions[0]["label"] if sorted_actions else "",
            "entry_point": entry,
            "audience_type": audience,
            "tasks": task_ids,
            "states": states,
            "actions": actions,
            "pareto": {
                "high_freq_actions": high_freq,
                "low_freq_buried": lf_shallow,
                "high_freq_buried": hf_buried,
            },
            "flags": flags,
        }

        if innovation_screen:
            screen["innovation_screen"] = True
            screen["adversarial_concept_ref"] = adv_ref
            screen["innovation_direction"] = adv_dir

        screens.append(screen)

# ── Write screen-map.json ────────────────────────────────────────────────────
sm_data = {"screens": screens}
sm_path = C.write_json(os.path.join(OUT, "screen-map.json"), sm_data)
print(f"Wrote {sm_path} ({len(screens)} screens)")

# ── Write screen-index.json ──────────────────────────────────────────────────
# Group screens by module
mod_screens = {}
for mod in modules:
    mod_task_ids = set(t["id"] if isinstance(t, dict) else t for t in mod.get("tasks", []))
    mod_name = mod["name"]
    for s in screens:
        if set(s["tasks"]) & mod_task_ids:
            mod_screens.setdefault(mod_name, []).append({
                "id": s["id"],
                "name": s["name"],
                "task_refs": s["tasks"],
                "action_count": len(s["actions"]),
                "audience_type": s.get("audience_type", "default"),
                "interaction_type": s.get("interaction_type", "MG1"),
                "has_gaps": bool(s["flags"] or any(
                    not a.get("on_failure") for a in s.get("actions", [])
                )),
            })

concept_eliminated = sum(1 for s in screens if "CONCEPT_ELIMINATED" in s.get("flags", []))
innovation_count = sum(1 for s in screens if s.get("innovation_screen"))

index_data = {
    "generated_at": NOW,
    "source": "screen-map.json",
    "screen_count": len(screens),
    "concept_eliminated_count": concept_eliminated,
    "innovation_count": innovation_count,
    "modules": [
        {"name": name, "screens": slist}
        for name, slist in mod_screens.items()
    ]
}
idx_path = C.write_json(os.path.join(OUT, "screen-index.json"), index_data)
print(f"Wrote {idx_path}")

# ── Write screen-map-report.md ───────────────────────────────────────────────
total_actions = sum(len(s["actions"]) for s in screens)
flagged = [s for s in screens if s["flags"]]

lines = [
    f"# 界面地图报告",
    f"",
    f"> 生成时间：{NOW}",
    f"",
    f"## 总览",
    f"",
    f"| 指标 | 值 |",
    f"|------|-----|",
    f"| 界面总数 | {len(screens)} |",
    f"| 操作按钮总数 | {total_actions} |",
    f"| 有问题界面 | {len(flagged)} |",
    f"| 创新界面 | {innovation_count} |",
    f"| 概念排除界面 | {concept_eliminated} |",
    f"",
    f"## 界面清单",
    f"",
    f"| ID | 界面名 | 交互类型 | 任务数 | 操作数 | 受众 | 标记 |",
    f"|-----|--------|----------|--------|--------|------|------|",
]

for s in screens:
    flags_str = ", ".join(s["flags"]) if s["flags"] else "—"
    lines.append(
        f"| {s['id']} | {s['name']} | {s['interaction_type']} "
        f"| {len(s['tasks'])} | {len(s['actions'])} "
        f"| {s.get('audience_type', 'default')} | {flags_str} |"
    )

if flagged:
    lines.extend(["", "## 问题界面详情", ""])
    for s in flagged:
        lines.append(f"### {s['id']} {s['name']}")
        lines.append("")
        for f in s["flags"]:
            lines.append(f"- **{f}**")
        lines.append("")

lines.append("")
rpt_path = os.path.join(OUT, "screen-map-report.md")
with open(rpt_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"Wrote {rpt_path}")

# ── Pipeline decisions ───────────────────────────────────────────────────────
shard = args.get("shard")
C.append_pipeline_decision(
    BASE,
    phase="Phase 3 — screen-map",
    detail=f"screens={len(screens)}, actions={total_actions}, flagged={len(flagged)}",
    shard=shard,
)

# ── XV cross-model review ───────────────────────────────────────────────────
if C.xv_available():
    try:
        xv_content = "\n".join([
            f"Screen Map ({len(screens)} screens, {total_actions} actions):",
            *[f"- {s['id']} {s['name']} ({s.get('interaction_type','?')}, "
              f"{len(s['actions'])} actions, audience={s.get('audience_type','default')}, "
              f"flags={s['flags']}, actions=[{', '.join(a['label'] for a in s['actions'])}])"
              for s in screens]
        ])
        xv_raw = C.xv_call(
            task_type="ux_review",
            prompt=f"Review this screen map for UX consistency issues. Check: "
                   f"1) screens with too many actions (overloaded), "
                   f"2) high-frequency actions buried deep, "
                   f"3) audience type mismatches. "
                   f"Return JSON: {{\"issues\": [{{\"screen_id\": \"S001\", \"severity\": \"high\", \"description\": \"...\"}}]}}\n\n"
                   f"{xv_content}",
        )
        xv_parsed = C.xv_parse_json(xv_raw)
        if xv_parsed:
            sm_data["cross_model_review"] = xv_parsed
            C.write_json(os.path.join(OUT, "screen-map.json"), sm_data)
            print(f"XV review appended ({len(xv_parsed.get('issues', []))} issues)")
    except Exception as e:
        print(f"XV review failed: {e}")

print(f"\nDone. {len(screens)} screens, {total_actions} actions, {len(flagged)} flagged.")
