#!/usr/bin/env python3
# Skeleton generator — LLM enrichment required after running
"""Generate use-case-tree.json, use-case-report.md, and use-case-decisions.json.

Skeleton generator: reads task-inventory and builds one use case per task
using raw main_flow steps. No keyword-based boundary/perception detection.

Usage:
    python3 gen_use_cases.py <BASE_PATH> [--mode auto] [--shard <name>]
"""

import os
import sys

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

op_lines, screen_index, em_loaded = C.load_experience_map(BASE)
task_screen_ids = C.build_task_screen_map_from_lines(op_lines) if em_loaded else {}

flows = C.load_business_flows(BASE)

# ── Feature area grouping from task-index modules ────────────────────────────
feature_areas = []
for i, mod in enumerate(idx.get("modules", []), 1):
    feature_areas.append({
        "id": f"FA{i:03d}",
        "name": mod["name"],
        "task_ids": [t["id"] for t in mod["tasks"]]
    })

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
    cat = task.get("category", "")
    if f == "高" or r == "高":
        return "高"
    if f == "中" or r == "中" or cat == "core":
        return "中"
    return "低"

# ── Screen ref helper ─────────────────────────────────────────────────────────
def get_screen_ref(tid):
    sids = task_screen_ids.get(tid, [])
    return sids[0] if sids else None

# ── Use case generation ──────────────────────────────────────────────────────
uc_counter = [0]

def next_uc():
    uc_counter[0] += 1
    return f"UC{uc_counter[0]:03d}"

def gen_use_case(task):
    """Generate one use case per task using raw main_flow steps."""
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
        then_steps = [f"{task['task_name']}操作成功"]

    exceptions = task.get("exceptions", [])
    rules = task.get("rules", [])

    return {
        "id": next_uc(),
        "title": f"{task['task_name']}",
        "type": "happy_path",
        "priority": prio,
        "given": given,
        "when": when_steps,
        "then": then_steps,
        "screen_ref": get_screen_ref(tid),
        "action_ref": task["task_name"],
        "raw_exceptions": exceptions,
        "raw_rules": rules,
        "flags": ["SKELETON_NEEDS_LLM_ENRICHMENT"]
    }

# ── Build the tree ────────────────────────────────────────────────────────────
role_fas = {}
for fa in feature_areas:
    for tid in fa["task_ids"]:
        task = tasks_by_id.get(tid)
        if not task:
            continue
        rid = task.get("owner_role") or task.get("role_id", "")
        if rid not in role_fas:
            role_fas[rid] = {}
        if fa["id"] not in role_fas[rid]:
            role_fas[rid][fa["id"]] = {"id": fa["id"], "name": fa["name"], "tasks": []}

        uc = gen_use_case(task)
        role_fas[rid][fa["id"]]["tasks"].append({
            "id": tid,
            "name": task["task_name"],
            "category": task.get("category", ""),
            "use_cases": [uc]
        })

# ── E2E use cases ────────────────────────────────────────────────────────────
e2e_cases = []
for flow in flows:
    fid = flow.get("id") or flow.get("flow_id", "")
    fname = flow.get("name") or flow.get("flow_name", "")
    gap_count = flow.get("gap_count", 0)
    if gap_count > 0:
        e2e_cases.append({
            "id": f"E2E-{fid}-NOTE",
            "type": "e2e_gap",
            "flow_ref": fid,
            "title": f"{fname}_含{gap_count}个缺口，待修复后生成E2E用例",
            "steps": [],
            "then": []
        })
        continue
    steps_list = []
    for node in C.get_flow_nodes(flow):
        if isinstance(node, dict):
            task_ref = node.get("task_ref", "")
            t = tasks_by_id.get(task_ref, {})
            task_name = t.get("name", node.get("name", str(task_ref)))
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
        "title": f"{fname}_正常流",
        "given": ["用户已登录", f"具备{fname}相关操作权限"],
        "steps": steps_list,
        "then": [f"{fname}全链路执行成功"],
        "flags": ["SKELETON_NEEDS_LLM_ENRICHMENT"]
    })

# ── Counts ───────────────────────────────────────────────────────────────────
total_uc = uc_counter[0]
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

for i, r in enumerate(roles_tree):
    if i > 0:
        r["e2e_cases"] = []

tree = {
    "version": "3.0.0-skeleton",
    "generated_at": NOW,
    "summary": {
        "role_count": len(role_fas),
        "feature_area_count": len(feature_areas),
        "task_count": len(tasks_by_id),
        "use_case_count": total_uc + e2e_count,
        "e2e_count": e2e_count,
        "experience_map_loaded": em_loaded,
        "note": "Skeleton output — LLM enrichment required for boundary/exception/validation cases"
    },
    "feature_areas": feature_areas,
    "roles": roles_tree
}

C.write_json(os.path.join(OUT, "use-case-tree.json"), tree)

# ── Markdown report ──────────────────────────────────────────────────────────
lines = []
lines.append("# 用例集摘要（骨架）\n")
lines.append(f"角色 {len(role_fas)} 个 · 功能区 {len(feature_areas)} 个 · "
             f"任务 {len(tasks_by_id)} 个 · 用例 {total_uc + e2e_count} 条 · "
             f"E2E {e2e_count} 条\n")
lines.append("> **骨架输出** — 每个任务生成一条基础用例，需 LLM 补充边界/异常/校验用例\n")

for role_entry in roles_tree:
    lines.append(f"\n## {role_entry['id']} {role_entry['name']}\n")
    for fa_data in role_entry["feature_areas"]:
        lines.append(f"\n### {fa_data['name']}\n")
        for t_data in fa_data["tasks"]:
            lines.append(f"\n**{t_data['id']} {t_data['name']}**\n")
            lines.append("| ID | 标题 | 优先级 |")
            lines.append("|----|------|--------|")
            for uc in t_data["use_cases"]:
                lines.append(f"| {uc['id']} | {uc['title']} | {uc.get('priority', '-')} |")

if e2e_cases:
    lines.append("\n## 端到端用例\n")
    lines.append("| ID | 标题 | 类型 | 关联流 | 步骤数 |")
    lines.append("|----|------|------|--------|--------|")
    for e in e2e_cases:
        steps_n = len(e.get("steps", []))
        lines.append(f"| {e['id']} | {e['title']} | {e['type']} | {e['flow_ref']} | {steps_n} |")

lines.append(f"\n> 完整字段见 .allforai/use-case/use-case-tree.json")

with open(os.path.join(OUT, "use-case-report.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

# ── Decisions ─────────────────────────────────────────────────────────────────
decisions = [
    {"step": "Step 0", "item_id": "feature_areas",
     "item_name": f"{len(feature_areas)} 个功能区",
     "decision": "auto_confirmed", "reason": "全自动模式 — 骨架生成", "decided_at": NOW},
    {"step": "Step 1", "item_id": "use_cases",
     "item_name": f"{total_uc} 条基础用例 + {e2e_count} 条 E2E",
     "decision": "auto_confirmed", "reason": "全自动模式 — 骨架生成", "decided_at": NOW},
]
C.write_json(os.path.join(OUT, "use-case-decisions.json"), decisions)

# ── Pipeline decisions ────────────────────────────────────────────────────────
C.append_pipeline_decision(
    BASE,
    "Phase 4 — use-case",
    f"use_cases={total_uc + e2e_count}, e2e={e2e_count} (skeleton)",
    shard=args.get("shard")
)

# ── Summary ───────────────────────────────────────────────────────────────────
print(f"Use cases: {total_uc + e2e_count} total (skeleton)")
print(f"  per-task: {total_uc}")
print(f"  e2e:      {e2e_count}")
print(f"Feature areas: {len(feature_areas)}")
print(f"Roles: {len(role_fas)}")
print(f"Experience-map loaded: {em_loaded}")
print(f"\nAll files written to {OUT}/")
