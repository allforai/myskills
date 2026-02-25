#!/usr/bin/env python3
"""Generate Step 6 outputs: product-map.json, report.md, task-index.json, flow-index.json"""
import json
from datetime import datetime

BASE = "/home/dv/myskills/.allforai/product-map"
NOW = "2026-02-25T15:00:00Z"

# Load all sources
with open(f"{BASE}/role-profiles.json") as f:
    roles = json.load(f)
with open(f"{BASE}/task-inventory.json") as f:
    tasks_data = json.load(f)
with open(f"{BASE}/business-flows.json") as f:
    flows_data = json.load(f)
with open(f"{BASE}/conflict-report.json") as f:
    conflicts_data = json.load(f)
with open(f"{BASE}/constraints.json") as f:
    constraints_data = json.load(f)
with open(f"{BASE}/competitor-profile.json") as f:
    competitor_data = json.load(f)

tasks = tasks_data["tasks"]
flows = flows_data["flows"]
conflicts = conflicts_data["conflicts"]
crud_gaps = conflicts_data["crud_gaps"]
constraints = constraints_data["constraints"]

# ============================================================
# 1. product-map.json
# ============================================================
# Identify high-freq tasks (top 20% pareto)
high_freq = [t for t in tasks if t["frequency"] == "高"]

product_map = {
    "generated_at": NOW,
    "version": "2.5.0",
    "scope": "full",
    "scale": "medium",
    "analysis_mode": "interview",
    "concept_guided": True,
    "summary": {
        "role_count": len(roles["roles"]),
        "task_count": len(tasks),
        "flow_count": len(flows),
        "flow_gaps": flows_data["summary"]["flow_gaps"],
        "orphan_task_count": len(flows_data["summary"]["orphan_tasks"]),
        "independent_operation_count": len(flows_data["summary"]["independent_operations"]),
        "high_freq_task_count": len(high_freq),
        "conflict_count": len(conflicts),
        "crud_gap_count": len(crud_gaps),
        "constraint_count": len(constraints),
        "config_level_summary": tasks_data["config_level_summary"],
        "validation_issues": 0,
        "competitor_gaps": 0
    },
    "roles": roles["roles"],
    "tasks": tasks,
    "conflicts": conflicts,
    "crud_gaps": crud_gaps,
    "constraints": constraints
}

with open(f"{BASE}/product-map.json", "w", encoding="utf-8") as f:
    json.dump(product_map, f, ensure_ascii=False, indent=2)
print("Generated product-map.json")

# ============================================================
# 2. product-map-report.md
# ============================================================
role_lookup = {r["id"]: r for r in roles["roles"]}

report_lines = []
report_lines.append("# 产品地图摘要")
report_lines.append("")
report_lines.append(f"角色 {len(roles['roles'])} 个 · 任务 {len(tasks)} 个 · 高频任务 {len(high_freq)} 个 · 冲突 {len(conflicts)} 个 · 约束 {len(constraints)} 条")
report_lines.append("")

# Role overview
report_lines.append("## 角色总览")
report_lines.append("")
report_lines.append("| 角色 | 职责 | KPI |")
report_lines.append("|------|------|-----|")
for r in roles["roles"]:
    kpi = ", ".join(r.get("kpi", [])[:2]) if r.get("kpi") else "-"
    report_lines.append(f"| {r['name']} | {r['description'][:30]} | {kpi} |")
report_lines.append("")

# High freq tasks
report_lines.append("## 高频任务（帕累托 Top 20%）")
report_lines.append("")
for t in high_freq:
    role_name = role_lookup.get(t["owner_role"], {}).get("name", t["owner_role"])
    risk = f"风险{t['risk_level']}"
    report_lines.append(f"- {t['id']} {t['task_name']}（{role_name} / 高频 / {risk}）")
report_lines.append("")

# Conflicts
report_lines.append("## 冲突摘要")
report_lines.append("")
for c in conflicts:
    status = "已解决" if c["confirmed"] else "待确认"
    report_lines.append(f"- {c['id']} {c['description']}（{c['severity']}，{status}）")
for cg in crud_gaps:
    status = "已解决" if cg["confirmed"] else "待确认"
    report_lines.append(f"- {cg['id']} {cg['description']}（{cg['severity']}，{status}）")
report_lines.append("")

# Constraints
report_lines.append("## 业务约束摘要")
report_lines.append("")
for cn in constraints:
    cn_type = "合规" if cn["type"] == "compliance" else "业务"
    report_lines.append(f"- {cn['id']} {cn['description']}（{cn_type}，{cn['enforcement']}）")
report_lines.append("")

# Config summary
report_lines.append("## 配置项分布")
report_lines.append("")
cls = tasks_data["config_level_summary"]
report_lines.append(f"| 级别 | 数量 |")
report_lines.append(f"|------|------|")
report_lines.append(f"| 界面写死 (frontend_hardcode) | {cls['frontend_hardcode']} |")
report_lines.append(f"| 代码写死 (code_constant) | {cls['code_constant']} |")
report_lines.append(f"| 配置文件 (config_file) | {cls['config_file']} |")
report_lines.append(f"| 通用配置 (general_config) | {cls['general_config']} |")
report_lines.append(f"| 专用配置 (dedicated_config) | {cls['dedicated_config']} |")
report_lines.append(f"| **总计** | **{cls['total']}** |")
report_lines.append("")

# Next steps
report_lines.append("## 下一步建议")
report_lines.append("")
report_lines.append("1. 运行 /screen-map 梳理界面、按钮和异常状态（可选，推荐）")
report_lines.append("2. 运行 /use-case 生成用例集（可选）")
report_lines.append("3. 运行 /feature-gap 检测功能缺口")
report_lines.append("4. 运行 /feature-prune 评估功能去留")
report_lines.append("5. 运行 /seed-forge 生成种子数据")
report_lines.append("")
report_lines.append("> 完整数据见 .allforai/product-map/product-map.json")

with open(f"{BASE}/product-map-report.md", "w", encoding="utf-8") as f:
    f.write("\n".join(report_lines))
print("Generated product-map-report.md")

# ============================================================
# 3. task-index.json
# ============================================================
# Group tasks by module (derived from concept modules)
module_map = {
    "场景对话": ["T001", "T002", "T003", "T004"],
    "发音纠正": ["T005", "T006"],
    "记忆曲线": ["T007", "T008"],
    "场景库管理": ["T009", "T010", "T011", "T012"],
    "游戏化与轻社交": ["T013", "T014", "T015", "T016"],
    "学习档案与进度": ["T017", "T018"],
    "角色场景推荐": ["T019", "T020"],
    "紧急场景速学": ["T021"],
    "订阅与付费": ["T022", "T023", "T024"],
    "运营数据看板": ["T025", "T026", "T027", "T028"],
    "AI质量监控": ["T029", "T030", "T031", "T032"],
    "用户管理与系统配置": ["T033", "T034", "T035", "T036", "T037"],
    "注册登录与个人设置": ["T038", "T039", "T040", "T041", "T042"],
    "首次体验": ["T043"],
    "推送与通知": ["T044"],
    "用户反馈": ["T045"],
}

task_lookup = {t["id"]: t for t in tasks}
modules = []
for mod_name, task_ids in module_map.items():
    mod_tasks = []
    for tid in task_ids:
        if tid in task_lookup:
            t = task_lookup[tid]
            mod_tasks.append({
                "id": t["id"],
                "task_name": t["task_name"],
                "frequency": t["frequency"],
                "owner_role": t["owner_role"],
                "risk_level": t["risk_level"]
            })
    if mod_tasks:
        modules.append({"name": mod_name, "tasks": mod_tasks})

task_index = {
    "generated_at": NOW,
    "source": "task-inventory.json",
    "task_count": len(tasks),
    "modules": modules
}

with open(f"{BASE}/task-index.json", "w", encoding="utf-8") as f:
    json.dump(task_index, f, ensure_ascii=False, indent=2)
print("Generated task-index.json")

# ============================================================
# 4. flow-index.json
# ============================================================
flow_entries = []
for fl in flows:
    roles_in_flow = list(set(n["role"] for n in fl["nodes"]))
    flow_entries.append({
        "id": fl["id"],
        "name": fl["name"],
        "node_count": len(fl["nodes"]),
        "gap_count": fl["gap_count"],
        "roles": roles_in_flow
    })

flow_index = {
    "generated_at": NOW,
    "source": "business-flows.json",
    "flow_count": len(flows),
    "flows": flow_entries
}

with open(f"{BASE}/flow-index.json", "w", encoding="utf-8") as f:
    json.dump(flow_index, f, ensure_ascii=False, indent=2)
print("Generated flow-index.json")

# Summary
print(f"\nStep 6 complete:")
print(f"  Roles: {len(roles['roles'])}")
print(f"  Tasks: {len(tasks)}")
print(f"  High-freq: {len(high_freq)}")
print(f"  Flows: {len(flows)}")
print(f"  Conflicts: {len(conflicts)}")
print(f"  CRUD gaps: {len(crud_gaps)}")
print(f"  Constraints: {len(constraints)}")
print(f"  Config items: {cls['total']}")
