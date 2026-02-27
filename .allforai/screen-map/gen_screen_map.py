#!/usr/bin/env python3
"""Generate screen-map, screen-index, screen-conflict, report, SVG, and decisions (auto-mode)."""
import json, os
from datetime import datetime, timezone

BASE = "/home/hello/Documents/myskills/.allforai"

with open(f"{BASE}/product-map/task-inventory.json") as f:
    inv = json.load(f)
with open(f"{BASE}/product-map/task-index.json") as f:
    idx = json.load(f)
with open(f"{BASE}/product-map/role-profiles.json") as f:
    roles = json.load(f)
with open(f"{BASE}/product-map/business-flows.json") as f:
    flows = json.load(f)

tasks = inv["tasks"]
task_by_id = {t["id"]: t for t in tasks}
role_by_id = {r["id"]: r for r in roles["roles"]}
modules = idx["modules"]
now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# ── helpers ──
sid = [0]
def next_sid():
    sid[0] += 1
    return f"S{sid[0]:03d}"

def a(label, crud, task_ref, click_depth=1, frequency="中",
       validation_rules=None, exception_flows=None):
    act = {"label": label, "crud": crud, "task_ref": task_ref,
           "click_depth": click_depth, "frequency": frequency}
    if validation_rules:
        act["validation_rules"] = validation_rules
    if exception_flows:
        act["exception_flows"] = exception_flows
    return act

def make_screen(name, module, task_ids, actions, notes=""):
    return {"id": next_sid(), "name": name, "module": module,
            "tasks": task_ids, "actions": actions, "notes": notes}

screens = []

# ── Module: 场景对话 ──
screens.append(make_screen("场景列表页", "场景对话", ["T001", "T020"], [
    a("浏览场景列表", "R", "T001", 1, "高"),
    a("按角色/难度/主题筛选", "R", "T001", 2, "高"),
    a("选择场景", "R", "T001", 2, "高"),
    a("查看个性化推荐", "R", "T020", 1, "高"),
], "入口页，合并推荐"))

screens.append(make_screen("场景详情页", "场景对话", ["T001"], [
    a("查看场景简介", "R", "T001", 2, "高"),
    a("开始对话", "R", "T001", 2, "高",
      exception_flows=["已达免费上限→提示升级", "场景暂不可用→推荐相似"]),
]))

screens.append(make_screen("AI对话页", "场景对话", ["T002", "T005"], [
    a("语音输入", "C", "T002", 1, "高",
      exception_flows=["语音识别失败→提示重说或切换文字"]),
    a("文字输入", "C", "T002", 1, "高"),
    a("查看AI回复", "R", "T002", 1, "高",
      exception_flows=["AI响应超时→等待动画并重试"]),
    a("实时发音纠正提示", "R", "T005", 1, "高"),
    a("查看生词收集", "R", "T002", 2, "中"),
], "核心交互页"))

screens.append(make_screen("对话报告页", "场景对话", ["T003"], [
    a("查看综合评分", "R", "T003", 1, "高"),
    a("查看语法错误清单", "R", "T003", 2, "中"),
    a("查看表达建议", "R", "T003", 2, "中"),
    a("重新开始同场景", "R", "T003", 2, "中"),
]))

screens.append(make_screen("自由对话页", "场景对话", ["T004"], [
    a("选择话题", "R", "T004", 2, "中"),
    a("自由语音/文字输入", "C", "T004", 1, "中"),
    a("AI自由回复", "R", "T004", 1, "中"),
]))

# ── Module: 发音纠正 ──
screens.append(make_screen("发音详细报告页", "发音纠正", ["T006"], [
    a("查看音素级评分", "R", "T006", 2, "中"),
    a("播放标准发音对比", "R", "T006", 2, "中"),
    a("查看发音趋势", "R", "T006", 3, "中"),
]))

# ── Module: 记忆曲线 ──
screens.append(make_screen("记忆曲线复习页", "记忆曲线", ["T007"], [
    a("查看今日复习任务", "R", "T007", 1, "高"),
    a("开始闪卡复习", "R", "T007", 1, "高"),
    a("标记已记住/未记住", "U", "T007", 1, "高"),
    a("查看复习统计", "R", "T007", 2, "中"),
]))

screens.append(make_screen("词汇本页", "记忆曲线", ["T008"], [
    a("浏览词汇列表", "R", "T008", 2, "中"),
    a("按来源/状态筛选", "R", "T008", 2, "中"),
    a("查看词汇详情", "R", "T008", 3, "低"),
]))

# ── Module: 场景库管理 (R004) ──
screens.append(make_screen("场景脚本编辑器", "场景库管理", ["T009"], [
    a("创建新场景", "C", "T009", 2, "高"),
    a("编辑对话节点", "U", "T009", 2, "高"),
    a("预览场景对话", "R", "T009", 3, "中"),
    a("保存草稿", "U", "T009", 2, "高",
      validation_rules=["场景名不能为空", "至少3轮对话节点"]),
]))

screens.append(make_screen("审核队列页", "场景库管理", ["T010"], [
    a("查看待审核列表", "R", "T010", 1, "高"),
    a("审核通过", "U", "T010", 2, "高"),
    a("驳回并备注", "U", "T010", 2, "高",
      validation_rules=["驳回必须填写原因"]),
]))

screens.append(make_screen("场景包管理页", "场景库管理", ["T011", "T012"], [
    a("查看场景包列表", "R", "T011", 2, "中"),
    a("上架场景包", "U", "T011", 2, "中"),
    a("下架场景包", "U", "T011", 2, "中"),
    a("编辑标签和关键词", "U", "T012", 2, "中"),
]))

# ── Module: 游戏化与轻社交 ──
screens.append(make_screen("学习连胜与成就页", "游戏化与轻社交", ["T013"], [
    a("查看连胜天数", "R", "T013", 1, "高"),
    a("领取连胜奖励", "U", "T013", 1, "高"),
    a("查看成就徽章", "R", "T013", 2, "中"),
]))

screens.append(make_screen("排行榜页", "游戏化与轻社交", ["T014"], [
    a("查看好友排名", "R", "T014", 2, "中"),
    a("查看全站排名", "R", "T014", 2, "中"),
]))

screens.append(make_screen("积分商城页", "游戏化与轻社交", ["T015"], [
    a("查看积分余额", "R", "T015", 2, "中"),
    a("兑换奖品", "U", "T015", 2, "中"),
    a("查看兑换记录", "R", "T015", 3, "低"),
]))

screens.append(make_screen("分享成果页", "游戏化与轻社交", ["T016"], [
    a("选择分享模板", "R", "T016", 3, "低"),
    a("分享到社交媒体", "C", "T016", 3, "低"),
]))

# ── Module: 学习档案与进度 ──
screens.append(make_screen("个人学习档案页", "学习档案与进度", ["T017"], [
    a("查看口语能力雷达图", "R", "T017", 2, "中"),
    a("查看学习目标进度", "R", "T017", 2, "中"),
    a("查看历史对话列表", "R", "T017", 2, "中"),
]))

screens.append(make_screen("学习统计报告页", "学习档案与进度", ["T018"], [
    a("查看周/月学习数据", "R", "T018", 2, "中"),
    a("查看开口时长趋势", "R", "T018", 2, "中"),
    a("查看场景通关率", "R", "T018", 2, "中"),
]))

# ── Module: 角色场景推荐 ──
screens.append(make_screen("角色偏好设置页", "角色场景推荐", ["T019"], [
    a("选择角色类型", "U", "T019", 3, "低"),
    a("设置学习目标", "U", "T019", 3, "低"),
    a("选择感兴趣场景", "U", "T019", 3, "低"),
]))

# ── Module: 紧急场景速学 ──
screens.append(make_screen("紧急场景速学页", "紧急场景速学", ["T021"], [
    a("选择紧急场景", "R", "T021", 1, "中"),
    a("查看关键句模板", "R", "T021", 1, "中"),
    a("跟读练习", "C", "T021", 1, "中",
      exception_flows=["语音识别失败→文字替代"]),
    a("收藏到词汇本", "C", "T021", 2, "低"),
]))

# ── Module: 订阅与付费 ──
screens.append(make_screen("订阅方案页", "订阅与付费", ["T022"], [
    a("查看订阅方案", "R", "T022", 2, "低"),
    a("选择方案并支付", "C", "T022", 2, "低",
      validation_rules=["支付前确认方案详情"],
      exception_flows=["支付失败→提示重试", "网络错误→保存订单稍后续费"]),
]))

screens.append(make_screen("订阅管理页", "订阅与付费", ["T023"], [
    a("查看当前订阅", "R", "T023", 2, "低"),
    a("续费/升级", "U", "T023", 2, "低"),
    a("取消订阅", "D", "T023", 3, "低",
      exception_flows=["取消确认二次弹窗"]),
]))

screens.append(make_screen("场景包购买页", "订阅与付费", ["T024"], [
    a("浏览可购场景包", "R", "T024", 2, "低"),
    a("购买场景包", "C", "T024", 2, "低",
      exception_flows=["支付失败→重试"]),
]))

# ── Module: 运营数据看板 (R006) ──
screens.append(make_screen("关键指标看板", "运营数据看板", ["T025"], [
    a("查看DAU/MAU/留存", "R", "T025", 1, "高"),
    a("查看开口时长指标", "R", "T025", 1, "高"),
    a("设置指标告警", "U", "T025", 2, "中"),
]))

screens.append(make_screen("用户行为分析页", "运营数据看板", ["T026"], [
    a("查看行为漏斗", "R", "T026", 2, "中"),
    a("创建自定义分析", "C", "T026", 2, "中"),
    a("导出分析数据", "R", "T026", 3, "低"),
]))

screens.append(make_screen("A/B测试管理页", "运营数据看板", ["T027"], [
    a("创建A/B测试", "C", "T027", 2, "中",
      validation_rules=["测试名称必填", "至少2个变体"]),
    a("查看测试结果", "R", "T027", 2, "中"),
    a("停止/启动测试", "U", "T027", 2, "中"),
]))

screens.append(make_screen("运营报告生成页", "运营数据看板", ["T028"], [
    a("选择报告模板", "R", "T028", 2, "中"),
    a("生成运营报告", "C", "T028", 2, "中"),
    a("导出报告", "R", "T028", 3, "低"),
]))

# ── Module: AI质量监控 (R005) ──
screens.append(make_screen("AI对话质量评分页", "AI质量监控", ["T029"], [
    a("查看质量评分概览", "R", "T029", 1, "高"),
    a("查看低分对话列表", "R", "T029", 2, "中"),
    a("查看评分趋势", "R", "T029", 2, "中"),
]))

screens.append(make_screen("异常对话标注页", "AI质量监控", ["T030"], [
    a("查看待标注对话", "R", "T030", 2, "中"),
    a("标注异常类型", "U", "T030", 2, "中",
      validation_rules=["必须选择异常分类"]),
    a("提交标注", "C", "T030", 2, "中"),
]))

screens.append(make_screen("Prompt模板管理页", "AI质量监控", ["T031"], [
    a("查看Prompt模板列表", "R", "T031", 2, "中"),
    a("创建新Prompt模板", "C", "T031", 2, "中"),
    a("编辑Prompt模板", "U", "T031", 2, "中"),
    a("发布Prompt到生产环境", "U", "T031", 3, "低",
      exception_flows=["发布前强制预览验证"]),
]))

screens.append(make_screen("发音评估参数页", "AI质量监控", ["T032"], [
    a("查看当前评估参数", "R", "T032", 3, "低"),
    a("调整音素阈值", "U", "T032", 3, "低",
      validation_rules=["阈值范围0.0-1.0"]),
    a("测试参数效果", "R", "T032", 3, "低"),
]))

# ── Module: 用户管理与系统配置 (R007) ──
screens.append(make_screen("用户管理页", "用户管理与系统配置", ["T033"], [
    a("搜索用户", "R", "T033", 1, "高"),
    a("查看用户详情", "R", "T033", 2, "中"),
    a("封禁/解禁用户", "U", "T033", 2, "中",
      exception_flows=["封禁需二次确认"]),
]))

screens.append(make_screen("订阅与退款管理页", "用户管理与系统配置", ["T034"], [
    a("查看订阅列表", "R", "T034", 2, "中"),
    a("处理退款申请", "U", "T034", 2, "中",
      validation_rules=["退款需填写审批理由"],
      exception_flows=["退款金额超限→需上级审批"]),
]))

screens.append(make_screen("系统配置页", "用户管理与系统配置", ["T035"], [
    a("查看系统参数", "R", "T035", 3, "低"),
    a("修改参数值", "U", "T035", 3, "低",
      validation_rules=["参数修改需确认"],
      exception_flows=["关键参数修改需二次确认"]),
]))

screens.append(make_screen("权限角色管理页", "用户管理与系统配置", ["T036"], [
    a("查看角色列表", "R", "T036", 3, "低"),
    a("创建/编辑角色权限", "U", "T036", 3, "低"),
    a("分配用户角色", "U", "T036", 3, "低"),
]))

screens.append(make_screen("投诉处理页", "用户管理与系统配置", ["T037"], [
    a("查看投诉列表", "R", "T037", 2, "中"),
    a("处理投诉", "U", "T037", 2, "中",
      validation_rules=["处理结果必填"]),
    a("回复用户", "C", "T037", 2, "中"),
]))

# ── Module: 注册登录与个人设置 ──
screens.append(make_screen("注册页", "注册登录与个人设置", ["T038"], [
    a("手机号/邮箱注册", "C", "T038", 1, "低",
      validation_rules=["手机号格式校验", "密码强度要求"],
      exception_flows=["手机号已注册→提示登录"]),
    a("第三方登录注册", "C", "T038", 1, "低"),
]))

screens.append(make_screen("登录页", "注册登录与个人设置", ["T039"], [
    a("账号密码登录", "R", "T039", 1, "高",
      exception_flows=["密码错误→提示重试+忘记密码"]),
    a("第三方快捷登录", "R", "T039", 1, "高"),
    a("验证码登录", "R", "T039", 1, "高"),
]))

screens.append(make_screen("个人设置页", "注册登录与个人设置", ["T040", "T042"], [
    a("修改头像/昵称", "U", "T040", 3, "低"),
    a("修改通知偏好", "U", "T040", 3, "低"),
    a("修改语言设置", "U", "T040", 3, "低"),
    a("注销账户", "D", "T042", 3, "低",
      exception_flows=["注销需二次确认+等待期"]),
]))

screens.append(make_screen("重置密码页", "注册登录与个人设置", ["T041"], [
    a("输入注册邮箱/手机", "R", "T041", 2, "低",
      validation_rules=["邮箱/手机格式校验"]),
    a("输入验证码", "R", "T041", 2, "低"),
    a("设置新密码", "U", "T041", 2, "低",
      validation_rules=["密码强度要求"]),
]))

# ── Module: 首次体验 ──
screens.append(make_screen("新手引导页", "首次体验", ["T043"], [
    a("选择学习目的", "C", "T043", 1, "低"),
    a("选择当前水平", "C", "T043", 1, "低"),
    a("体验示范对话", "R", "T043", 1, "低"),
]))

# ── Module: 推送与通知 ──
screens.append(make_screen("通知中心页", "推送与通知", ["T044"], [
    a("查看学习提醒", "R", "T044", 2, "高"),
    a("查看系统通知", "R", "T044", 2, "中"),
    a("管理通知设置", "U", "T044", 3, "低"),
]))

# ── Module: 用户反馈 ──
screens.append(make_screen("意见反馈页", "用户反馈", ["T045"], [
    a("选择反馈类型", "R", "T045", 3, "低"),
    a("填写反馈内容", "C", "T045", 3, "低",
      validation_rules=["反馈内容不能为空"]),
    a("上传截图", "C", "T045", 3, "低"),
    a("提交反馈", "C", "T045", 3, "低"),
]))

# ── Verify coverage ──
covered = set()
for s in screens:
    covered.update(s["tasks"])
all_task_ids = {t["id"] for t in tasks}
missing = all_task_ids - covered
assert not missing, f"Missing tasks: {missing}"

total_actions = sum(len(s["actions"]) for s in screens)
print(f"Screens: {len(screens)}, Actions: {total_actions}, Tasks covered: {len(covered)}/{len(all_task_ids)}")

# ── Write screen-map.json ──
sm = {"generated_at": now, "mode": "full", "auto_mode": True,
      "audience_mode": "typed", "concept_mode": "none",
      "screens": screens}
with open(f"{BASE}/screen-map/screen-map.json", "w", encoding="utf-8") as f:
    json.dump(sm, f, ensure_ascii=False, indent=2)

# ── Write screen-index.json ──
mod_map = {}
for s in screens:
    mod_map.setdefault(s["module"], []).append({"id": s["id"], "name": s["name"]})
si = {"generated_at": now, "screen_count": len(screens),
      "modules": [{"name": k, "screens": v} for k, v in mod_map.items()]}
with open(f"{BASE}/screen-map/screen-index.json", "w", encoding="utf-8") as f:
    json.dump(si, f, ensure_ascii=False, indent=2)

# ── Conflict & gap detection ──
NON_FORM = {"浏览", "查看", "播放", "语音", "AI", "接收", "领取", "开始", "体验", "跟读"}
conflicts = []
gaps = []

# REDUNDANT_ENTRY: same action on different screens
action_screen_map = {}
for s in screens:
    for act in s["actions"]:
        key = (act["crud"], act["label"])
        action_screen_map.setdefault(key, []).append(s["id"])
for (crud, label), sids in action_screen_map.items():
    if len(set(sids)) > 1:
        conflicts.append({"type": "REDUNDANT_ENTRY", "severity": "medium",
            "screens": list(set(sids)), "detail": f"操作「{label}」({crud}) 出现在多个界面: {', '.join(set(sids))}"})

# MISSING_VALIDATION on form-like CUD actions
for s in screens:
    for act in s["actions"]:
        if act["crud"] in ("C", "U", "D") and not act.get("validation_rules"):
            if not any(kw in act["label"] for kw in NON_FORM):
                gaps.append({"type": "MISSING_VALIDATION", "severity": "medium",
                    "screen": s["id"], "screen_name": s["name"], "action": act["label"],
                    "detail": f"CUD 操作「{act['label']}」缺少 validation_rules"})

# SILENT_FAILURE on high-risk tasks
for s in screens:
    for act in s["actions"]:
        tid = act["task_ref"]
        task = task_by_id.get(tid, {})
        if task.get("risk_level") in ("中", "高") and not act.get("exception_flows"):
            if act["crud"] in ("C", "U", "D"):
                gaps.append({"type": "SILENT_FAILURE", "severity": "medium",
                    "screen": s["id"], "screen_name": s["name"], "action": act["label"],
                    "detail": f"中高风险任务 {tid} 的操作「{act['label']}」缺少异常处理"})

# NO_EMPTY_STATE on list/browse screens
for s in screens:
    has_list = any("列表" in act["label"] or "浏览" in act["label"] for act in s["actions"])
    has_empty = any("空" in act.get("label", "") for act in s["actions"])
    if has_list and not has_empty:
        gaps.append({"type": "NO_EMPTY_STATE", "severity": "low",
            "screen": s["id"], "screen_name": s["name"],
            "detail": f"列表界面「{s['name']}」缺少空状态设计"})

sc = {"generated_at": now, "conflicts": conflicts, "exception_gaps": gaps}
with open(f"{BASE}/screen-map/screen-conflict.json", "w", encoding="utf-8") as f:
    json.dump(sc, f, ensure_ascii=False, indent=2)

print(f"Conflicts: {len(conflicts)}, Gaps: {len(gaps)}")

# ── Report ──
high_freq = []
for s in screens:
    for act in s["actions"]:
        if act["frequency"] == "高":
            high_freq.append((s["name"], act["label"], act["click_depth"]))

report = [f"# 界面地图报告摘要\n",
    f"> 执行时间: {now}", f"> 执行模式: full（全自动）",
    f"> 产品规模: 中型（45 个任务）", f"> 受众模式: typed（consumer 3 + professional 4）",
    f"> 概念感知: none\n",
    "## 总览\n", "| 维度 | 数量 |", "|------|------|",
    f"| 界面总数 | {len(screens)} 个 |",
    f"| 按钮/操作总数 | {total_actions} 个 |",
    f"| 已覆盖任务 | {len(covered)} / {len(all_task_ids)} |",
    f"| 异常覆盖缺口 | {len(gaps)} 个 |",
    f"| 界面级冲突 | {len(conflicts)} 个 |\n",
    "## 高频操作（Top 20%）\n", "| 界面 | 操作 | click_depth |",
    "|------|------|-------------|"]
for sn, al, cd in sorted(high_freq, key=lambda x: x[2]):
    report.append(f"| {sn} | {al} | {cd} |")

if conflicts:
    report.append("\n## 冲突清单\n")
    for c in conflicts:
        report.append(f"- [{c['severity']}] {c['type']}: {c['detail']}")
if gaps:
    report.append("\n## 缺口清单\n")
    for g in gaps:
        report.append(f"- [{g['severity']}] {g['type']}: {g['screen_name']} → {g['detail']}")

with open(f"{BASE}/screen-map/screen-map-report.md", "w", encoding="utf-8") as f:
    f.write("\n".join(report))

# ── SVG ──
svg_lines = ['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="TOTAL_H">']
y = 20
for mod_name, mod_screens in mod_map.items():
    svg_lines.append(f'<text x="20" y="{y}" font-size="14" font-weight="bold" fill="#333">{mod_name}</text>')
    y += 25
    for ms in mod_screens:
        svg_lines.append(f'<rect x="40" y="{y-12}" width="200" height="20" rx="4" fill="#e3f2fd"/>')
        svg_lines.append(f'<text x="50" y="{y}" font-size="11" fill="#1565c0">{ms["name"]}</text>')
        y += 25
    y += 10
svg_lines[0] = svg_lines[0].replace("TOTAL_H", str(y + 20))
svg_lines.append('</svg>')
with open(f"{BASE}/screen-map/screen-map-visual.svg", "w", encoding="utf-8") as f:
    f.write("\n".join(svg_lines))

# ── Decisions (auto-mode) ──
decisions = []
for s in screens:
    decisions.append({"step": "Step1", "item_id": s["id"], "item_name": s["name"],
                      "decision": "auto_confirmed", "decided_at": now})
for c in conflicts:
    decisions.append({"step": "Step2", "item_id": c["screens"][0], "type": c["type"],
                      "decision": "auto_confirmed", "decided_at": now})
for g in gaps:
    decisions.append({"step": "Step2", "item_id": g["screen"], "type": g["type"],
                      "decision": "auto_confirmed", "decided_at": now})
with open(f"{BASE}/screen-map/screen-map-decisions.json", "w", encoding="utf-8") as f:
    json.dump(decisions, f, ensure_ascii=False, indent=2)

# ── Pipeline decisions ──
pd = [{"phase": "Phase 3 screen-map", "checkpoint": "PASS",
       "severity": "INFO", "detail": f"{len(screens)} screens, {total_actions} actions, {len(conflicts)} conflicts, {len(gaps)} gaps",
       "decided_at": now, "decision": "auto_confirmed"}]
with open(f"{BASE}/pipeline-decisions.json", "w", encoding="utf-8") as f:
    json.dump(pd, f, ensure_ascii=False, indent=2)

print(f"\nAll files written to {BASE}/screen-map/")
print(f"High-freq actions: {len(high_freq)}")
