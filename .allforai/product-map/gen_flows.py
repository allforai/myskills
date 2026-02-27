#!/usr/bin/env python3
"""Generate business-flows.json, task-index.json, conflict-report, constraints, product-map.json, reports."""
import json
from datetime import datetime, timezone

now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
BASE = "/home/hello/Documents/myskills/.allforai"

with open(f"{BASE}/product-map/task-inventory.json") as f:
    inv = json.load(f)
with open(f"{BASE}/product-map/role-profiles.json") as f:
    roles_data = json.load(f)

tasks = inv["tasks"]
task_by_id = {t["id"]: t for t in tasks}
roles = roles_data["roles"]

# ── Step 3: Business Flows ──
flows = [
    {
        "id": "F001", "name": "场景学习全链路",
        "description": "用户从浏览场景到完成对话获得报告的完整学习体验",
        "systems_involved": ["app"],
        "nodes": [
            {"seq": 1, "name": "浏览并选择场景", "task_ref": "T001", "role": "职场人士", "handoff": None, "gap": False},
            {"seq": 2, "name": "进行场景对话", "task_ref": "T002", "role": "职场人士", "handoff": {"mechanism": "场景选择→对话启动", "data": ["场景ID", "难度"]}, "gap": False},
            {"seq": 3, "name": "查看实时发音纠正", "task_ref": "T005", "role": "职场人士", "handoff": {"mechanism": "对话中实时触发", "data": ["语音数据", "音素评分"]}, "gap": False},
            {"seq": 4, "name": "查看对话报告", "task_ref": "T003", "role": "职场人士", "handoff": {"mechanism": "对话完成→报告生成", "data": ["对话记录", "评分"]}, "gap": False},
            {"seq": 5, "name": "完成记忆曲线复习", "task_ref": "T007", "role": "职场人士", "handoff": {"mechanism": "生词收集→复习队列", "data": ["新词列表", "来源场景"]}, "gap": False}
        ],
        "gap_count": 0, "confirmed": True
    },
    {
        "id": "F002", "name": "记忆闭环链路",
        "description": "对话中收集生词 → 记忆曲线复习 → 在新场景中使用",
        "systems_involved": ["app"],
        "nodes": [
            {"seq": 1, "name": "对话中收集生词", "task_ref": "T002", "role": "职场人士", "handoff": None, "gap": False},
            {"seq": 2, "name": "管理词汇本", "task_ref": "T008", "role": "职场人士", "handoff": {"mechanism": "自动收集", "data": ["词汇", "语境"]}, "gap": False},
            {"seq": 3, "name": "完成记忆曲线复习", "task_ref": "T007", "role": "职场人士", "handoff": {"mechanism": "复习调度", "data": ["待复习词汇"]}, "gap": False},
            {"seq": 4, "name": "在新场景中使用", "task_ref": "T001", "role": "职场人士", "handoff": {"mechanism": "推荐含已学词汇的场景", "data": ["已掌握词汇"]}, "gap": False}
        ],
        "gap_count": 0, "confirmed": True
    },
    {
        "id": "F003", "name": "场景内容生产链路",
        "description": "内容运营创建场景到场景上线的完整内容管线",
        "systems_involved": ["admin"],
        "nodes": [
            {"seq": 1, "name": "创建场景对话脚本", "task_ref": "T009", "role": "内容运营", "handoff": None, "gap": False},
            {"seq": 2, "name": "审核场景内容", "task_ref": "T010", "role": "内容运营", "handoff": {"mechanism": "提交审核", "data": ["场景ID"]}, "gap": False},
            {"seq": 3, "name": "管理场景包", "task_ref": "T011", "role": "内容运营", "handoff": {"mechanism": "审核通过→上架", "data": ["场景ID", "场景包ID"]}, "gap": False}
        ],
        "gap_count": 0, "confirmed": True
    },
    {
        "id": "F004", "name": "用户注册到首次学习",
        "description": "新用户从注册到完成首次场景对话的引导流",
        "systems_involved": ["app"],
        "nodes": [
            {"seq": 1, "name": "注册账户", "task_ref": "T038", "role": "职场人士", "handoff": None, "gap": False},
            {"seq": 2, "name": "完成新手引导", "task_ref": "T043", "role": "职场人士", "handoff": {"mechanism": "注册完成→引导", "data": ["用户ID"]}, "gap": False},
            {"seq": 3, "name": "查看个性化推荐", "task_ref": "T020", "role": "职场人士", "handoff": {"mechanism": "引导完成→首页推荐", "data": ["偏好设置"]}, "gap": False},
            {"seq": 4, "name": "浏览并选择场景", "task_ref": "T001", "role": "职场人士", "handoff": {"mechanism": "推荐→场景", "data": ["场景ID"]}, "gap": False},
            {"seq": 5, "name": "进行场景对话", "task_ref": "T002", "role": "职场人士", "handoff": {"mechanism": "选择→对话", "data": ["场景ID"]}, "gap": False}
        ],
        "gap_count": 0, "confirmed": True
    },
    {
        "id": "F005", "name": "付费转化链路",
        "description": "免费用户触达付费墙到完成订阅",
        "systems_involved": ["app"],
        "nodes": [
            {"seq": 1, "name": "触达免费上限", "task_ref": "T002", "role": "职场人士", "handoff": None, "gap": False},
            {"seq": 2, "name": "订阅付费方案", "task_ref": "T022", "role": "职场人士", "handoff": {"mechanism": "免费上限→付费引导", "data": ["用户ID", "使用量"]}, "gap": False},
            {"seq": 3, "name": "管理订阅", "task_ref": "T023", "role": "职场人士", "handoff": {"mechanism": "订阅完成→管理", "data": ["订阅ID"]}, "gap": False}
        ],
        "gap_count": 0, "confirmed": True
    },
    {
        "id": "F006", "name": "AI质量监控链路",
        "description": "AI训练师监控质量到优化Prompt的完整闭环",
        "systems_involved": ["admin"],
        "nodes": [
            {"seq": 1, "name": "查看AI对话质量评分", "task_ref": "T029", "role": "AI 训练师", "handoff": None, "gap": False},
            {"seq": 2, "name": "标注异常对话", "task_ref": "T030", "role": "AI 训练师", "handoff": {"mechanism": "低分→标注", "data": ["对话ID"]}, "gap": False},
            {"seq": 3, "name": "管理Prompt模板", "task_ref": "T031", "role": "AI 训练师", "handoff": {"mechanism": "标注反馈→优化", "data": ["异常类型"]}, "gap": False},
            {"seq": 4, "name": "调整发音评估参数", "task_ref": "T032", "role": "AI 训练师", "handoff": {"mechanism": "质量数据→参数调优", "data": ["评分分布"]}, "gap": False}
        ],
        "gap_count": 0, "confirmed": True
    },
    {
        "id": "F007", "name": "运营分析链路",
        "description": "数据运营从监控到输出报告的分析流程",
        "systems_involved": ["admin"],
        "nodes": [
            {"seq": 1, "name": "查看关键指标看板", "task_ref": "T025", "role": "数据运营", "handoff": None, "gap": False},
            {"seq": 2, "name": "分析用户行为", "task_ref": "T026", "role": "数据运营", "handoff": {"mechanism": "指标异常→行为分析", "data": ["指标数据"]}, "gap": False},
            {"seq": 3, "name": "管理A/B测试", "task_ref": "T027", "role": "数据运营", "handoff": {"mechanism": "分析结论→实验验证", "data": ["假设"]}, "gap": False},
            {"seq": 4, "name": "生成运营报告", "task_ref": "T028", "role": "数据运营", "handoff": {"mechanism": "实验结果→报告", "data": ["测试数据"]}, "gap": False}
        ],
        "gap_count": 0, "confirmed": True
    },
    {
        "id": "F008", "name": "投诉处理链路",
        "description": "用户投诉到处理完成的闭环",
        "systems_involved": ["app", "admin"],
        "nodes": [
            {"seq": 1, "name": "提交意见反馈", "task_ref": "T045", "role": "职场人士", "handoff": None, "gap": False},
            {"seq": 2, "name": "处理用户投诉", "task_ref": "T037", "role": "系统管理员", "handoff": {"mechanism": "反馈提交→投诉队列", "data": ["反馈ID", "内容"]}, "gap": False}
        ],
        "gap_count": 0, "confirmed": True
    },
    {
        "id": "F009", "name": "紧急场景速学链路",
        "description": "新移民出发前的紧急学习流程",
        "systems_involved": ["app"],
        "nodes": [
            {"seq": 1, "name": "使用紧急场景速学", "task_ref": "T021", "role": "新移民", "handoff": None, "gap": False},
            {"seq": 2, "name": "完成记忆曲线复习", "task_ref": "T007", "role": "新移民", "handoff": {"mechanism": "速学词汇→复习", "data": ["关键句词汇"]}, "gap": False}
        ],
        "gap_count": 0, "confirmed": True
    }
]

# Identify orphan/independent tasks
flow_task_refs = set()
for fl in flows:
    for n in fl["nodes"]:
        if n.get("task_ref"):
            flow_task_refs.add(n["task_ref"])

orphan_tasks = []
independent_ops = []
INDEPENDENT_KW = ["导出", "设置", "配置", "查看列表", "管理档案", "管理个人", "管理通知", "重置密码", "注销", "查看学习", "查看排行", "兑换", "分享", "管理权限", "管理词汇"]

for t in tasks:
    if t["id"] not in flow_task_refs:
        is_independent = any(kw in t["task_name"] for kw in INDEPENDENT_KW) or (not t.get("cross_dept") and not t.get("approver_role"))
        if is_independent:
            independent_ops.append(t["id"])
        else:
            orphan_tasks.append(t["id"])

# Write business-flows.json
bf = {
    "generated_at": now,
    "systems": {"current": "app", "linked": []},
    "flows": flows,
    "summary": {
        "flow_count": len(flows),
        "flow_gaps": sum(fl["gap_count"] for fl in flows),
        "orphan_tasks": orphan_tasks,
        "independent_operations": independent_ops
    }
}
with open(f"{BASE}/product-map/business-flows.json", "w", encoding="utf-8") as f:
    json.dump(bf, f, ensure_ascii=False, indent=2)

# Write business-flows-report.md
lines = [
    "# 业务流报告\n",
    f"{len(flows)} 条业务流 · {sum(fl['gap_count'] for fl in flows)} 个流缺口 · {len(orphan_tasks)} 个孤立任务 · {len(independent_ops)} 个独立操作\n",
    "## 业务流列表\n"
]
for fl in flows:
    lines.append(f"- {fl['id']} {fl['name']}（{', '.join(fl['systems_involved'])}）— {fl['gap_count']} 个缺口")
if orphan_tasks:
    lines.append("\n## 孤立任务（可能遗漏建模，需确认）\n")
    for tid in orphan_tasks:
        lines.append(f"- {tid} {task_by_id[tid]['task_name']}")
lines.append("\n## 独立操作（无需纳入流）\n")
for tid in independent_ops:
    lines.append(f"- {tid} {task_by_id[tid]['task_name']}")
with open(f"{BASE}/product-map/business-flows-report.md", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

# ── Step 4: Conflict & CRUD gap detection ──
conflicts = []
crud_gaps = []
# CRUD check: tasks with write actions should have cancel/edit options
for t in tasks:
    flow_str = " ".join(t.get("main_flow", []))
    has_create = any(kw in flow_str for kw in ["创建", "提交", "注册", "购买", "订阅"])
    has_cancel = any(kw in flow_str for kw in ["撤回", "取消", "撤销"])
    if has_create and not has_cancel and t["risk_level"] in ("高", "中"):
        crud_gaps.append({
            "id": f"CG{len(crud_gaps)+1:03d}",
            "type": "CRUD_INCOMPLETE",
            "description": f"{t['task_name']} 有创建/提交但缺少撤回/取消流程",
            "affected_tasks": [t["id"]],
            "severity": "中",
            "confirmed": True
        })

cr = {"generated_at": now, "conflicts": conflicts, "crud_gaps": crud_gaps}
with open(f"{BASE}/product-map/conflict-report.json", "w", encoding="utf-8") as f:
    json.dump(cr, f, ensure_ascii=False, indent=2)

# ── Step 5: Constraints ──
constraints = [
    {"id": "CN001", "type": "business", "description": "免费版每天3轮对话限制", "affected_tasks": ["T002"], "enforcement": "hard", "code_status": "missing"},
    {"id": "CN002", "type": "business", "description": "退款金额不可超过原订单金额", "affected_tasks": ["T034"], "enforcement": "hard", "code_status": "missing"},
    {"id": "CN003", "type": "compliance", "description": "用户注销后数据保留30天", "affected_tasks": ["T042"], "enforcement": "hard", "code_status": "missing"},
    {"id": "CN004", "type": "business", "description": "连胜中断恢复限每月1次", "affected_tasks": ["T013"], "enforcement": "soft", "code_status": "missing"},
    {"id": "CN005", "type": "compliance", "description": "支付操作必须留存审计日志", "affected_tasks": ["T022", "T024", "T034"], "enforcement": "hard", "code_status": "missing"},
    {"id": "CN006", "type": "business", "description": "场景审核通过后方可上架", "affected_tasks": ["T010", "T011"], "enforcement": "hard", "code_status": "missing"},
    {"id": "CN007", "type": "business", "description": "发音评估阈值范围0.0-1.0", "affected_tasks": ["T032"], "enforcement": "hard", "code_status": "missing"},
    {"id": "CN008", "type": "compliance", "description": "用户封禁操作需二次确认+日志", "affected_tasks": ["T033"], "enforcement": "hard", "code_status": "missing"}
]
with open(f"{BASE}/product-map/constraints.json", "w", encoding="utf-8") as f:
    json.dump({"generated_at": now, "constraints": constraints}, f, ensure_ascii=False, indent=2)

# ── Step 6: Product map + indexes ──
# task-index.json
modules_map = {}
for t in tasks:
    name = t["task_name"]
    # Group by semantic module
    if any(kw in name for kw in ["场景", "对话", "自由"]):
        mod = "场景对话"
    elif any(kw in name for kw in ["发音"]):
        mod = "发音纠正"
    elif any(kw in name for kw in ["记忆", "复习", "词汇"]):
        mod = "记忆曲线"
    elif any(kw in name for kw in ["脚本", "审核场景", "场景包", "标签"]):
        mod = "场景库管理"
    elif any(kw in name for kw in ["连胜", "成就", "排行", "积分", "分享"]):
        mod = "游戏化与轻社交"
    elif any(kw in name for kw in ["档案", "统计"]):
        mod = "学习档案与进度"
    elif any(kw in name for kw in ["偏好", "推荐"]):
        mod = "角色场景推荐"
    elif any(kw in name for kw in ["紧急"]):
        mod = "紧急场景速学"
    elif any(kw in name for kw in ["订阅", "购买"]):
        mod = "订阅与付费"
    elif any(kw in name for kw in ["看板", "行为", "A/B", "运营报告"]):
        mod = "运营数据看板"
    elif any(kw in name for kw in ["AI", "异常对话", "Prompt", "发音评估"]):
        mod = "AI质量监控"
    elif any(kw in name for kw in ["用户账户", "退款", "系统参数", "权限", "投诉"]):
        mod = "用户管理与系统配置"
    elif any(kw in name for kw in ["注册", "登录", "个人设置", "密码", "注销"]):
        mod = "注册登录与个人设置"
    elif any(kw in name for kw in ["新手"]):
        mod = "首次体验"
    elif any(kw in name for kw in ["通知"]):
        mod = "推送与通知"
    elif any(kw in name for kw in ["反馈"]):
        mod = "用户反馈"
    else:
        mod = "其他"
    modules_map.setdefault(mod, []).append({
        "id": t["id"], "task_name": t["task_name"],
        "frequency": t["frequency"], "owner_role": t["owner_role"],
        "risk_level": t["risk_level"]
    })

task_idx = {
    "generated_at": now,
    "source": "task-inventory.json",
    "task_count": len(tasks),
    "modules": [{"name": k, "tasks": v} for k, v in modules_map.items()]
}
with open(f"{BASE}/product-map/task-index.json", "w", encoding="utf-8") as f:
    json.dump(task_idx, f, ensure_ascii=False, indent=2)

# flow-index.json
flow_idx = {
    "generated_at": now,
    "source": "business-flows.json",
    "flow_count": len(flows),
    "flows": [{"id": fl["id"], "name": fl["name"], "node_count": len(fl["nodes"]),
               "gap_count": fl["gap_count"],
               "roles": list(set(n["role"] for n in fl["nodes"]))} for fl in flows]
}
with open(f"{BASE}/product-map/flow-index.json", "w", encoding="utf-8") as f:
    json.dump(flow_idx, f, ensure_ascii=False, indent=2)

# product-map.json
pm = {
    "generated_at": now,
    "version": "2.5.0",
    "scope": "full",
    "scale": "medium",
    "summary": {
        "role_count": len(roles),
        "task_count": len(tasks),
        "flow_count": len(flows),
        "flow_gaps": sum(fl["gap_count"] for fl in flows),
        "orphan_task_count": len(orphan_tasks),
        "independent_operation_count": len(independent_ops),
        "conflict_count": len(conflicts),
        "crud_gap_count": len(crud_gaps),
        "constraint_count": len(constraints)
    },
    "roles": roles,
    "tasks": tasks,
    "conflicts": conflicts,
    "crud_gaps": crud_gaps,
    "constraints": constraints
}
with open(f"{BASE}/product-map/product-map.json", "w", encoding="utf-8") as f:
    json.dump(pm, f, ensure_ascii=False, indent=2)

# product-map-report.md
high_freq = [t for t in tasks if t["frequency"] == "高"]
rpt = [
    "# 产品地图摘要\n",
    f"角色 {len(roles)} 个 · 任务 {len(tasks)} 个 · 高频任务 {len(high_freq)} 个 · 冲突 {len(conflicts)} 个 · 约束 {len(constraints)} 条\n",
    "## 角色总览\n",
    "| 角色 | 职责 | KPI |",
    "|------|------|-----|"
]
for r in roles:
    rpt.append(f"| {r['name']} | {r['description'][:30]} | {', '.join(r.get('kpi', [])[:2])} |")
rpt.append("\n## 高频任务（Top 20%）\n")
for t in high_freq:
    rpt.append(f"- {t['id']} {t['task_name']}（{t['frequency']}频 / {t['risk_level']}风险）")
if crud_gaps:
    rpt.append("\n## CRUD 缺口\n")
    for cg in crud_gaps:
        rpt.append(f"- {cg['id']}: {cg['description']}（{cg['severity']}）")
rpt.append("\n## 业务约束摘要\n")
for cn in constraints:
    rpt.append(f"- {cn['id']} {cn['description']}（{cn['enforcement']}）")
with open(f"{BASE}/product-map/product-map-report.md", "w", encoding="utf-8") as f:
    f.write("\n".join(rpt))

# Competitor profile
comp = {
    "competitors": ["Speak", "ELSA Speak", "Duolingo Max", "Praktika AI"],
    "comparison_scope": "comprehensive",
    "analysis_status": "pending",
    "analyzed_at": None
}
with open(f"{BASE}/product-map/competitor-profile.json", "w", encoding="utf-8") as f:
    json.dump(comp, f, ensure_ascii=False, indent=2)

# Decisions
decisions = [
    {"step": "Step 0", "decision": "concept_guided", "detail": "产品画像从concept加载", "decided_at": now},
    {"step": "Step 1", "decision": "concept_guided", "detail": f"{len(roles)} roles mapped", "decided_at": now},
    {"step": "Step 2", "decision": "concept_guided", "detail": f"{len(tasks)} tasks generated", "decided_at": now},
    {"step": "Step 3", "decision": "concept_guided", "detail": f"{len(flows)} flows, {len(orphan_tasks)} orphan, {len(independent_ops)} independent", "decided_at": now},
    {"step": "Step 4", "decision": "concept_guided", "detail": f"{len(conflicts)} conflicts, {len(crud_gaps)} CRUD gaps", "decided_at": now},
    {"step": "Step 5", "decision": "concept_guided", "detail": f"{len(constraints)} constraints", "decided_at": now},
    {"step": "Step 6", "decision": "concept_guided", "detail": "product-map + indexes generated", "decided_at": now}
]
with open(f"{BASE}/product-map/product-map-decisions.json", "w", encoding="utf-8") as f:
    json.dump(decisions, f, ensure_ascii=False, indent=2)

print(f"\n=== PRODUCT MAP COMPLETE ===")
print(f"Roles: {len(roles)}, Tasks: {len(tasks)}, Flows: {len(flows)}")
print(f"High-freq tasks: {len(high_freq)}, CRUD gaps: {len(crud_gaps)}, Constraints: {len(constraints)}")
print(f"Orphan tasks: {len(orphan_tasks)}, Independent ops: {len(independent_ops)}")
print(f"Modules: {len(modules_map)}")
print(f"\nFiles written:")
for fn in ["role-profiles.json", "task-inventory.json", "business-flows.json",
           "business-flows-report.md", "conflict-report.json", "constraints.json",
           "task-index.json", "flow-index.json", "product-map.json",
           "product-map-report.md", "competitor-profile.json", "product-map-decisions.json"]:
    print(f"  .allforai/product-map/{fn}")
