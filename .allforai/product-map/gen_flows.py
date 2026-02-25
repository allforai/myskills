#!/usr/bin/env python3
"""Generate business-flows.json from task-inventory.json."""
import json

flows = []
fid = 0

def F(name, desc, nodes, **kw):
    global fid
    fid += 1
    gap_count = sum(1 for n in nodes if n.get("gap", False))
    flow = {
        "id": f"F{fid:03d}",
        "name": name,
        "description": desc,
        "systems_involved": ["english-app"],
        "nodes": [],
        "gap_count": gap_count,
        "confirmed": False
    }
    for i, n in enumerate(nodes, 1):
        node = {
            "seq": i,
            "name": n["name"],
            "task_ref": n.get("task_ref", ""),
            "role": n["role"],
            "handoff": n.get("handoff"),
            "gap": n.get("gap", False),
            "gap_type": n.get("gap_type")
        }
        flow["nodes"].append(node)
    for k, v in kw.items():
        flow[k] = v
    flows.append(flow)

# ============================================================
# F001: 新用户上手流
# ============================================================
F("新用户上手流",
  "从注册到完成首次场景对话的完整新用户体验链路",
  [
    {"name": "注册账户", "task_ref": "T038", "role": "新用户",
     "handoff": None},
    {"name": "完成新手引导（选目的、选水平、体验示范对话）", "task_ref": "T043", "role": "新用户",
     "handoff": {"mechanism": "自动跳转", "data": ["注册完成状态"]}},
    {"name": "设置个人角色偏好（职场/旅行/移民）", "task_ref": "T019", "role": "新用户",
     "handoff": {"mechanism": "引导流程", "data": ["水平评估结果"]}},
    {"name": "接受个性化场景推荐", "task_ref": "T020", "role": "新用户",
     "handoff": {"mechanism": "推荐引擎", "data": ["角色偏好", "水平"]}},
    {"name": "选择场景并开始首次对话", "task_ref": "T001", "role": "新用户",
     "handoff": {"mechanism": "用户选择", "data": ["推荐场景列表"]}},
    {"name": "进行AI场景对话", "task_ref": "T002", "role": "新用户",
     "handoff": {"mechanism": "进入对话", "data": ["场景ID", "用户水平"]}},
    {"name": "查看首次对话报告", "task_ref": "T003", "role": "新用户",
     "handoff": {"mechanism": "对话结束自动生成", "data": ["对话记录", "生词列表", "发音评估"]}}
  ])

# ============================================================
# F002: 日常学习主流程
# ============================================================
F("日常学习主流程",
  "用户每日打开APP到完成学习任务的核心循环（场景对话 + 发音纠正 + 记忆复习）",
  [
    {"name": "登录账户", "task_ref": "T039", "role": "学习者",
     "handoff": None},
    {"name": "接收学习提醒推送", "task_ref": "T044", "role": "学习者",
     "handoff": {"mechanism": "推送通知", "data": ["今日推荐场景"]}},
    {"name": "接受个性化场景推荐", "task_ref": "T020", "role": "学习者",
     "handoff": {"mechanism": "首页推荐", "data": ["角色偏好", "学习历史"]}},
    {"name": "选择场景并开始对话", "task_ref": "T001", "role": "学习者",
     "handoff": {"mechanism": "用户选择", "data": ["推荐场景列表"]}},
    {"name": "进行AI场景对话 + 实时发音纠正", "task_ref": "T002", "role": "学习者",
     "handoff": {"mechanism": "并行执行", "data": ["场景脚本", "发音评估实时流"]}},
    {"name": "查看对话报告 + 发音报告", "task_ref": "T003", "role": "学习者",
     "handoff": {"mechanism": "对话结束", "data": ["流利度评分", "生词", "发音问题"]}},
    {"name": "进行记忆曲线复习", "task_ref": "T007", "role": "学习者",
     "handoff": {"mechanism": "系统推送待复习词汇", "data": ["遗忘曲线到期词汇"]}},
    {"name": "学习连胜+1", "task_ref": "T013", "role": "学习者",
     "handoff": {"mechanism": "每日目标达成", "data": ["完成状态"]}}
  ])

# ============================================================
# F003: 记忆曲线闭环流
# ============================================================
F("记忆曲线闭环流",
  "核心差异化：对话中学的词 → 记忆曲线复习 → 在新场景中用出来的闭环",
  [
    {"name": "场景对话中自动收集生词", "task_ref": "T002", "role": "学习者",
     "handoff": None},
    {"name": "生词进入词汇本", "task_ref": "T008", "role": "学习者",
     "handoff": {"mechanism": "自动收集", "data": ["生词", "来源场景", "上下文"]}},
    {"name": "遗忘曲线到期触发复习", "task_ref": "T007", "role": "学习者",
     "handoff": {"mechanism": "SM-2算法定时触发", "data": ["待复习词汇列表"]}},
    {"name": "词汇嵌入新场景句子中复习", "task_ref": "T007", "role": "学习者",
     "handoff": {"mechanism": "语境嵌入引擎", "data": ["词汇", "新场景模板"]}},
    {"name": "根据表现调整复习间隔", "task_ref": "T007", "role": "系统",
     "handoff": {"mechanism": "算法自动", "data": ["用户答题表现"]}}
  ])

# ============================================================
# F004: 紧急场景速学流
# ============================================================
F("紧急场景速学流",
  "新移民出发前10分钟预演即将面对的场景",
  [
    {"name": "选择紧急场景类型", "task_ref": "T021", "role": "新移民",
     "handoff": None},
    {"name": "输入具体情境", "task_ref": "T021", "role": "新移民",
     "handoff": {"mechanism": "用户输入", "data": ["场景类型"]}},
    {"name": "AI生成定制化速学对话", "task_ref": "T021", "role": "系统",
     "handoff": {"mechanism": "AI实时生成", "data": ["情境描述", "用户水平"]}},
    {"name": "快速预演2-3轮", "task_ref": "T021", "role": "新移民",
     "handoff": {"mechanism": "进入对话", "data": ["生成的速学脚本"]}},
    {"name": "生成关键句清单（可离线查看）", "task_ref": "T021", "role": "系统",
     "handoff": {"mechanism": "对话结束", "data": ["对话中的关键句"]}}
  ])

# ============================================================
# F005: 场景内容生产流
# ============================================================
F("场景内容生产流",
  "从AI生成脚本草稿到场景上架可供用户学习的完整内容生产链路",
  [
    {"name": "使用AI生成场景脚本草稿", "task_ref": "T009", "role": "内容运营",
     "handoff": None},
    {"name": "编辑对话内容和分支逻辑", "task_ref": "T009", "role": "内容运营",
     "handoff": {"mechanism": "AI生成完成", "data": ["脚本草稿"]}},
    {"name": "标定难度和角色适用范围", "task_ref": "T009", "role": "内容运营",
     "handoff": {"mechanism": "编辑完成", "data": ["场景内容"]}},
    {"name": "提交审核", "task_ref": "T009", "role": "内容运营",
     "handoff": {"mechanism": "提交操作", "data": ["场景ID", "内容", "难度", "角色"]}},
    {"name": "审核场景内容（准确性+文化适当性+难度）", "task_ref": "T010", "role": "内容运营(审核员)",
     "handoff": {"mechanism": "审核队列通知", "data": ["待审场景ID"]}},
    {"name": "标定搜索关键词和标签", "task_ref": "T012", "role": "内容运营",
     "handoff": {"mechanism": "审核通过", "data": ["场景ID"]}},
    {"name": "组织到场景包并上架", "task_ref": "T011", "role": "内容运营",
     "handoff": {"mechanism": "标签完成", "data": ["场景ID", "标签"]}},
    {"name": "用户可浏览和选择该场景", "task_ref": "T001", "role": "学习者",
     "handoff": {"mechanism": "上架后可见", "data": ["场景包更新"]}}
  ])

# ============================================================
# F006: 订阅转化流
# ============================================================
F("免费转付费订阅流",
  "免费用户达到使用限制后转化为付费用户的完整链路",
  [
    {"name": "免费用户达到每日对话上限", "task_ref": "T001", "role": "免费用户",
     "handoff": None},
    {"name": "展示升级提示", "task_ref": "T001", "role": "系统",
     "handoff": {"mechanism": "触发限制", "data": ["当日已用次数", "限制值"]}},
    {"name": "查看订阅方案对比", "task_ref": "T022", "role": "免费用户",
     "handoff": {"mechanism": "点击升级", "data": []}},
    {"name": "选择方案并完成支付", "task_ref": "T022", "role": "用户",
     "handoff": {"mechanism": "选择方案", "data": ["方案ID", "价格"]}},
    {"name": "立即解锁付费功能", "task_ref": "T022", "role": "系统",
     "handoff": {"mechanism": "支付成功回调", "data": ["订阅状态", "到期日"]}}
  ])

# ============================================================
# F007: AI质量监控与调优流
# ============================================================
F("AI质量监控与调优流",
  "从发现AI对话质量问题到调优修复的完整运营循环",
  [
    {"name": "查看AI对话质量评分趋势", "task_ref": "T029", "role": "AI训练师",
     "handoff": None},
    {"name": "筛选低分对话并查看日志", "task_ref": "T029", "role": "AI训练师",
     "handoff": {"mechanism": "筛选操作", "data": ["低分对话列表"]}},
    {"name": "标注异常对话（类型+严重度+建议）", "task_ref": "T030", "role": "AI训练师",
     "handoff": {"mechanism": "选择异常对话", "data": ["对话ID", "对话日志"]}},
    {"name": "编辑并测试新Prompt模板", "task_ref": "T031", "role": "AI训练师",
     "handoff": {"mechanism": "积累足够标注", "data": ["标注结果", "问题模式"]}},
    {"name": "沙盒验证通过后发布新Prompt", "task_ref": "T031", "role": "AI训练师",
     "handoff": {"mechanism": "沙盒测试通过", "data": ["新Prompt版本"]}},
    {"name": "观察新版本质量评分变化", "task_ref": "T029", "role": "AI训练师",
     "handoff": {"mechanism": "发布后监控", "data": ["版本标记"]}}
  ])

# ============================================================
# F008: 用户投诉处理流
# ============================================================
F("用户投诉与退款处理流",
  "从用户投诉到处理完成（含退款场景）的服务闭环",
  [
    {"name": "用户提交意见或投诉", "task_ref": "T045", "role": "用户",
     "handoff": None},
    {"name": "接收并查看投诉工单", "task_ref": "T037", "role": "系统管理员",
     "handoff": {"mechanism": "工单系统通知", "data": ["投诉ID", "用户信息"]}},
    {"name": "查看用户详情和历史记录", "task_ref": "T033", "role": "系统管理员",
     "handoff": {"mechanism": "关联查看", "data": ["用户ID"]}},
    {"name": "回复用户并处理", "task_ref": "T037", "role": "系统管理员",
     "handoff": {"mechanism": "处理操作", "data": ["投诉内容", "用户记录"]}},
    {"name": "处理退款（如需要）", "task_ref": "T034", "role": "系统管理员",
     "handoff": {"mechanism": "需退款时", "data": ["订阅记录", "退款原因"]}},
    {"name": "关闭工单", "task_ref": "T037", "role": "系统管理员",
     "handoff": {"mechanism": "处理完成", "data": ["处理结果"]}}
  ])

# ============================================================
# F009: 运营数据分析流
# ============================================================
F("运营数据分析与优化流",
  "从指标监控到发现问题到A/B测试验证的数据驱动优化循环",
  [
    {"name": "查看关键指标看板", "task_ref": "T025", "role": "数据运营",
     "handoff": None},
    {"name": "发现异常指标（如留存率下降）", "task_ref": "T025", "role": "数据运营",
     "handoff": {"mechanism": "告警触发", "data": ["异常指标", "变化幅度"]}},
    {"name": "分析用户学习行为（定位问题）", "task_ref": "T026", "role": "数据运营",
     "handoff": {"mechanism": "深入分析", "data": ["异常指标维度"]}},
    {"name": "创建A/B测试方案", "task_ref": "T027", "role": "数据运营",
     "handoff": {"mechanism": "假设验证", "data": ["分析结论", "优化假设"]}},
    {"name": "执行测试并监控数据", "task_ref": "T027", "role": "数据运营",
     "handoff": {"mechanism": "测试启动", "data": ["实验配置"]}},
    {"name": "输出结论并生成报告", "task_ref": "T028", "role": "数据运营",
     "handoff": {"mechanism": "测试结束", "data": ["实验数据", "显著性"]}}
  ])

# ============================================================
# Identify orphan and independent tasks
# ============================================================
with open("/home/dv/myskills/.allforai/product-map/task-inventory.json") as f:
    inv = json.load(f)

all_task_ids = {t["id"] for t in inv["tasks"]}
referenced_ids = set()
for fl in flows:
    for node in fl["nodes"]:
        ref = node["task_ref"]
        if ref:
            referenced_ids.add(ref)

unreferenced = all_task_ids - referenced_ids

# Classify unreferenced tasks
# Tasks that are standalone user/admin actions (not part of a multi-step flow)
independent_keywords = ["查看", "修改", "设置", "词汇本", "统计", "档案", "排行榜", "成就", "分享",
                        "管理", "配置", "重置", "购买", "调整"]
# Tasks that are sub-features or confirmed independent learning modes (not truly orphan)
embedded_or_standalone = {
    "T004",  # 自由对话 — 独立学习路径，用户确认为独立操作
    "T005",  # 发音纠正 — 嵌入 T002 对话过程中，F002 已涵盖
    "T042",  # 注销账户 — 独立自助操作
}
task_lookup = {t["id"]: t for t in inv["tasks"]}

orphan_tasks = []
independent_operations = []

for tid in sorted(unreferenced):
    if tid in embedded_or_standalone:
        independent_operations.append(tid)  # Sub-feature, classify as independent
        continue
    t = task_lookup[tid]
    name = t["task_name"]
    is_independent = any(kw in name for kw in independent_keywords) or (t["frequency"] == "低" and t["risk_level"] == "低")
    if is_independent:
        independent_operations.append(tid)
    else:
        orphan_tasks.append(tid)

# ============================================================
# Output
# ============================================================
output = {
    "generated_at": "2026-02-25T14:00:00Z",
    "systems": {
        "current": "english-app",
        "linked": []
    },
    "flows": flows,
    "summary": {
        "flow_count": len(flows),
        "flow_gaps": sum(f["gap_count"] for f in flows),
        "orphan_tasks": orphan_tasks,
        "independent_operations": independent_operations
    }
}

with open("/home/dv/myskills/.allforai/product-map/business-flows.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"Generated {len(flows)} flows.")
print(f"  Flow gaps: {sum(f['gap_count'] for f in flows)}")
print(f"  Referenced tasks: {sorted(referenced_ids)}")
print(f"  Orphan tasks: {orphan_tasks}")
print(f"  Independent operations ({len(independent_operations)}): {independent_operations}")

# Print per-task name for verification
print("\n--- Referenced task verification ---")
for ref in sorted(referenced_ids):
    if ref in task_lookup:
        print(f"  {ref}: {task_lookup[ref]['task_name']}")
    else:
        print(f"  {ref}: *** NOT FOUND ***")
