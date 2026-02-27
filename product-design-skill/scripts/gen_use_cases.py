#!/usr/bin/env python3
"""Generate use-case-tree.json, use-case-report.md, and use-case-decisions.json.

Pre-built script for Phase 4 (use-case). Reads task-inventory, task-index,
role-profiles, screen-map (recommended, missing triggers WARNING), and business-flows (optional).

Usage:
    python3 gen_use_cases.py <BASE_PATH> [--mode auto]
"""

import os
import sys

# Add scripts dir to path for _common import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C

# ── Setup ─────────────────────────────────────────────────────────────────────
BASE, args = C.parse_args()
OUT = os.path.join(BASE, "use-case")
C.ensure_dir(OUT)
NOW = C.now_iso()

# ── Load data ─────────────────────────────────────────────────────────────────
tasks_by_id = C.load_task_inventory(BASE)
idx = C.load_task_index(BASE)
if idx is None:
    print("WARNING: task-index.json not found, using task-inventory grouping")
    idx = {"modules": []}
role_map = C.load_role_profiles(BASE)

screens, screen_injected = C.load_screen_map(BASE)
screens_by_task = C.build_task_screen_map(screens)

flows = C.load_business_flows(BASE)

# ── Step 0: Feature area grouping from task-index modules ─────────────────────
feature_areas = []
for i, mod in enumerate(idx.get("modules", []), 1):
    feature_areas.append({
        "id": f"FA{i:03d}",
        "name": mod["name"],
        "task_ids": [t["id"] for t in mod["tasks"]]
    })

# If no modules in index, group all tasks into one area
if not feature_areas:
    feature_areas.append({
        "id": "FA001",
        "name": "全部任务",
        "task_ids": list(tasks_by_id.keys())
    })

# ── Priority calculation ─────────────────────────────────────────────────────
def calc_priority(task):
    f = task.get("frequency", "低")
    r = task.get("risk_level", "低")
    if f == "高" or r == "高":
        return "高"
    if f == "中" or r == "中":
        return "中"
    return "低"

# ── Screen ref helper ─────────────────────────────────────────────────────────
def get_screen_ref(tid):
    ss = screens_by_task.get(tid, [])
    return ss[0].get("id") if ss else None

# ── Use case generation ──────────────────────────────────────────────────────
uc_counter = [0]

def next_uc():
    uc_counter[0] += 1
    return f"UC{uc_counter[0]:03d}"

def gen_happy(task):
    tid = task["id"]
    prio = calc_priority(task)
    given = task.get("prerequisites", [])
    if not given:
        given = ["用户已登录", f"具备{task['task_name']}的操作权限"]
    when_steps = task.get("main_flow", [])
    if not when_steps:
        when_steps = [task["task_name"]]
    then_steps = []
    outputs = task.get("outputs", {})
    if isinstance(outputs, dict):
        then_steps.extend(outputs.get("states", []))
        then_steps.extend(outputs.get("messages", []))
    if not then_steps:
        then_steps = [f"{task['task_name']}操作成功", "页面展示操作成功提示"]
    return {
        "id": next_uc(),
        "title": f"{task['task_name']}_正常流",
        "type": "happy_path",
        "priority": prio,
        "given": given,
        "when": when_steps,
        "then": then_steps,
        "screen_ref": get_screen_ref(tid),
        "action_ref": task["task_name"],
        "exception_source": None,
        "flags": []
    }

def gen_exceptions(task):
    cases = []
    tid = task["id"]
    prio = calc_priority(task)
    excs = task.get("exceptions", [])
    for i, exc in enumerate(excs):
        parts = exc.split("→")
        trigger = parts[0].strip() if len(parts) > 0 else exc
        response = parts[1].strip() if len(parts) > 1 else "系统提示异常"
        cases.append({
            "id": next_uc(),
            "title": f"{task['task_name']}_{trigger}",
            "type": "exception",
            "priority": prio,
            "given": ["用户已登录", f"正在执行{task['task_name']}"],
            "when": [trigger],
            "then": [response],
            "screen_ref": get_screen_ref(tid),
            "action_ref": task["task_name"],
            "exception_source": f"task.exceptions[{i}]",
            "flags": []
        })
    if not excs:
        cases.append({
            "id": next_uc(),
            "title": f"{task['task_name']}_无异常定义",
            "type": "exception",
            "priority": "低",
            "given": [],
            "when": [],
            "then": [],
            "screen_ref": get_screen_ref(tid),
            "action_ref": task["task_name"],
            "exception_source": None,
            "flags": ["NO_EXCEPTION_CASES"]
        })
    return cases

def gen_boundary(task):
    cases = []
    tid = task["id"]
    prio = calc_priority(task)
    rules = task.get("rules", [])
    boundary_keywords = ["≥", "≤", ">", "<", "限", "最", "不可", "必须",
                         "超时", "幂等", "范围", "阈值", "上限", "下限", "限制"]
    for i, rule in enumerate(rules):
        if any(kw in rule for kw in boundary_keywords):
            cases.append({
                "id": next_uc(),
                "title": f"{task['task_name']}_边界_{rule[:20]}",
                "type": "boundary",
                "priority": prio,
                "given": ["用户已登录", f"正在执行{task['task_name']}"],
                "when": [f"触发边界条件: {rule}"],
                "then": [f"系统按规则处理: {rule}"],
                "screen_ref": get_screen_ref(tid),
                "action_ref": task["task_name"],
                "rule_source": f"task.rules[{i}]",
                "flags": []
            })
    return cases

def gen_validation(task):
    """Generate validation use cases from screen-map validation_rules."""
    cases = []
    tid = task["id"]
    prio = calc_priority(task)
    slist = screens_by_task.get(tid, [])
    for s in slist:
        for act in s.get("actions", []):
            for vr in act.get("validation_rules", []):
                cases.append({
                    "id": next_uc(),
                    "title": f"{task['task_name']}_校验_{vr[:20]}",
                    "type": "validation",
                    "priority": prio,
                    "given": ["用户已登录", f"正在执行{task['task_name']}"],
                    "when": [f"违反校验规则: {vr}"],
                    "then": [f"系统提示校验失败: {vr}"],
                    "screen_ref": s.get("id"),
                    "action_ref": act.get("label", task["task_name"]),
                    "validation_rule": vr,
                    "flags": []
                })
    return cases

# ── Build the tree ────────────────────────────────────────────────────────────
role_fas = {}  # role_id -> {fa_id: fa_data}
for fa in feature_areas:
    for tid in fa["task_ids"]:
        task = tasks_by_id.get(tid)
        if not task:
            continue
        rid = task["owner_role"]
        if rid not in role_fas:
            role_fas[rid] = {}
        if fa["id"] not in role_fas[rid]:
            role_fas[rid][fa["id"]] = {"id": fa["id"], "name": fa["name"], "tasks": []}

        ucs = []
        ucs.append(gen_happy(task))
        ucs.extend(gen_exceptions(task))
        ucs.extend(gen_boundary(task))
        ucs.extend(gen_validation(task))

        role_fas[rid][fa["id"]]["tasks"].append({
            "id": tid,
            "task_name": task["task_name"],
            "use_cases": ucs
        })

# ── E2E use cases (uses 'nodes' not 'steps') ─────────────────────────────────
e2e_cases = []
for flow in flows:
    fid = flow["id"]
    gap_count = flow.get("gap_count", 0)
    if gap_count > 0:
        e2e_cases.append({
            "id": f"E2E-{fid}-NOTE",
            "type": "e2e_gap",
            "flow_ref": fid,
            "title": f"{flow['name']}_含{gap_count}个缺口，待修复后生成E2E用例",
            "steps": [],
            "then": []
        })
        continue
    steps_list = []
    for node in C.get_flow_nodes(flow):
        if isinstance(node, dict):
            task_ref = node.get("task_ref", "")
            t = tasks_by_id.get(task_ref, {})
            task_name = t.get("task_name", node.get("name", str(task_ref)))
            steps_list.append({
                "seq": node.get("seq", len(steps_list) + 1),
                "task_ref": task_ref,
                "action": task_name
            })
        elif isinstance(node, str) and node in tasks_by_id:
            steps_list.append({
                "seq": len(steps_list) + 1,
                "task_ref": node,
                "action": tasks_by_id[node]["task_name"]
            })
    e2e_cases.append({
        "id": f"E2E-{fid}-01",
        "type": "e2e",
        "flow_ref": fid,
        "title": f"{flow['name']}_正常流",
        "given": ["用户已登录", f"具备{flow['name']}相关操作权限"],
        "steps": steps_list,
        "then": [f"{flow['name']}全链路执行成功"]
    })

# ── Count by type ─────────────────────────────────────────────────────────────
total_uc = uc_counter[0]
happy_count = sum(1 for fa in feature_areas for tid in fa["task_ids"] if tid in tasks_by_id)
exc_count = bnd_count = val_count = 0

for rid, fas in role_fas.items():
    for faid, fa_data in fas.items():
        for t_data in fa_data["tasks"]:
            for uc in t_data["use_cases"]:
                if uc["type"] == "exception":
                    exc_count += 1
                elif uc["type"] == "boundary":
                    bnd_count += 1
                elif uc["type"] == "validation":
                    val_count += 1

e2e_count = sum(1 for e in e2e_cases if e["type"] == "e2e")

# ── Assemble roles tree ──────────────────────────────────────────────────────
roles_tree = []
for rid in sorted(role_fas.keys()):
    fas = role_fas[rid]
    role_entry = {
        "id": rid,
        "name": role_map.get(rid, rid),
        "feature_areas": list(fas.values()),
        "e2e_cases": list(e2e_cases)
    }
    roles_tree.append(role_entry)

# Only attach E2E to first role to avoid duplication
for i, r in enumerate(roles_tree):
    if i > 0:
        r["e2e_cases"] = []

tree = {
    "version": "2.3.0",
    "generated_at": NOW,
    "summary": {
        "role_count": len(role_fas),
        "feature_area_count": len(feature_areas),
        "task_count": len(tasks_by_id),
        "use_case_count": total_uc + e2e_count,
        "happy_path_count": happy_count,
        "exception_count": exc_count,
        "boundary_count": bnd_count,
        "validation_count": val_count,
        "e2e_count": e2e_count,
        "screen_map_injected": screen_injected
    },
    "feature_areas": feature_areas,
    "roles": roles_tree
}

C.write_json(os.path.join(OUT, "use-case-tree.json"), tree)

# ── Markdown report ──────────────────────────────────────────────────────────
lines = []
lines.append("# 用例集摘要\n")
lines.append(f"角色 {len(role_fas)} 个 · 功能区 {len(feature_areas)} 个 · 任务 {len(tasks_by_id)} 个 · "
             f"用例 {total_uc + e2e_count} 条（正常流 {happy_count} / 异常流 {exc_count} / 边界 {bnd_count} / 校验 {val_count} / E2E {e2e_count}）\n")

for role_entry in roles_tree:
    lines.append(f"\n## {role_entry['id']} {role_entry['name']}\n")
    for fa_data in role_entry["feature_areas"]:
        lines.append(f"\n### {fa_data['name']}\n")
        for t_data in fa_data["tasks"]:
            uc_count = len(t_data["use_cases"])
            lines.append(f"\n**{t_data['id']} {t_data['task_name']}**（{uc_count} 条用例）\n")
            lines.append("| ID | 标题 | 类型 | 优先级 |")
            lines.append("|----|------|------|--------|")
            for uc in t_data["use_cases"]:
                lines.append(f"| {uc['id']} | {uc['title']} | {uc['type']} | {uc.get('priority', '-')} |")

if e2e_cases:
    lines.append("\n## 端到端用例\n")
    lines.append("| ID | 标题 | 类型 | 关联流 | 步骤数 |")
    lines.append("|----|------|------|--------|--------|")
    for e in e2e_cases:
        steps_n = len(e.get("steps", []))
        lines.append(f"| {e['id']} | {e['title']} | {e['type']} | {e['flow_ref']} | {steps_n} |")

lines.append(f"\n> 完整字段见 .allforai/use-case/use-case-tree.json")
lines.append(f"> 决策日志见 .allforai/use-case/use-case-decisions.json")

with open(os.path.join(OUT, "use-case-report.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

# ── Decisions ─────────────────────────────────────────────────────────────────
decisions = []
for fa in feature_areas:
    decisions.append({
        "step": "Step 0",
        "item_id": fa["id"],
        "item_name": fa["name"],
        "decision": "auto_confirmed",
        "reason": "全自动模式 — 功能区分组自动确认",
        "decided_at": NOW
    })
decisions.append({
    "step": "Step 1",
    "item_id": "all_happy_path",
    "item_name": f"{happy_count} 条正常流用例",
    "decision": "auto_confirmed",
    "reason": "全自动模式 — 正常流用例自动确认",
    "decided_at": NOW
})
decisions.append({
    "step": "Step 2",
    "item_id": "all_exception_boundary",
    "item_name": f"{exc_count} 异常 + {bnd_count} 边界 + {val_count} 校验用例",
    "decision": "auto_confirmed",
    "reason": "全自动模式 — 异常/边界/校验用例自动确认",
    "decided_at": NOW
})
decisions.append({
    "step": "Step 3",
    "item_id": "dual_format",
    "item_name": "JSON + Markdown 双格式输出",
    "decision": "auto_confirmed",
    "reason": "全自动模式",
    "decided_at": NOW
})
decisions.append({
    "step": "Step 4",
    "item_id": "e2e_cases",
    "item_name": f"{e2e_count} 条 E2E 用例",
    "decision": "auto_confirmed",
    "reason": "全自动模式 — E2E用例自动确认",
    "decided_at": NOW
})

C.write_json(os.path.join(OUT, "use-case-decisions.json"), decisions)

# ── Pipeline decisions ────────────────────────────────────────────────────────
C.append_pipeline_decision(
    BASE,
    "Phase 4 — use-case",
    f"use_cases={total_uc + e2e_count}, happy={happy_count}, exception={exc_count}, "
    f"boundary={bnd_count}, validation={val_count}, e2e={e2e_count}"
)

# ── Summary ───────────────────────────────────────────────────────────────────
print(f"Use cases: {total_uc + e2e_count} total")
print(f"  happy_path: {happy_count}")
print(f"  exception:  {exc_count}")
print(f"  boundary:   {bnd_count}")
print(f"  validation: {val_count}")
print(f"  e2e:        {e2e_count}")
print(f"Feature areas: {len(feature_areas)}")
print(f"Roles: {len(role_fas)}")
print(f"Screen-map injected: {screen_injected}")
print(f"\nAll files written to {OUT}/")
