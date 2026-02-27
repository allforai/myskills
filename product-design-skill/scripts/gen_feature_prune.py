#!/usr/bin/env python3
"""Generate feature-prune analysis: frequency-tier, scenario-alignment,
competitive-ref, prune-decisions, prune-tasks, and prune-report.

Pre-built script for Phase 6 (feature-prune). Fixes:
- Uses _common.get_screen_tasks() instead of hardcoded field names
- Uses _common.collect_flow_task_refs() with 'nodes' field
- Accepts --strategy parameter to override scope_strategy
- Pipeline-decisions dedup via _common.append_pipeline_decision()

Usage:
    python3 gen_feature_prune.py <BASE_PATH> [--mode auto] [--strategy aggressive|balanced|conservative]
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C

# ── Setup ─────────────────────────────────────────────────────────────────────
BASE, args = C.parse_args()
OUT = os.path.join(BASE, "feature-prune")
C.ensure_dir(OUT)
NOW = C.now_iso()

# ── Load data ─────────────────────────────────────────────────────────────────
tasks = C.load_task_inventory(BASE)
tidx = C.load_task_index(BASE)
role_map = C.load_role_profiles(BASE)

# Load pipeline preferences for scope_strategy and competitors
concept = C.load_product_concept(BASE)
prefs = concept.get("pipeline_preferences", {}) if concept else {}
scope_strategy = args.get("strategy", prefs.get("scope_strategy", "balanced"))
competitors = prefs.get("competitors", [])

# Load screen-map for scenario alignment
screens, _ = C.load_screen_map(BASE)
task_screen_map = C.build_task_screen_map(screens)

# Load business flows for CUT safety check
flows = C.load_business_flows(BASE)
flow_task_refs = C.collect_flow_task_refs(flows)

# ── Step 1: Frequency tier ───────────────────────────────────────────────────
freq_tier = []
for tid, task in tasks.items():
    freq = task.get("frequency", "低")
    if freq == "高":
        tier = "protected"
    elif freq == "低":
        tier = "candidate"
    else:
        tier = "review"
    freq_tier.append({
        "task_id": tid,
        "task_name": task["task_name"],
        "frequency": freq,
        "tier": tier,
        "data_points": f"frequency={freq}, risk={task.get('risk_level', '低')}"
    })

C.write_json(os.path.join(OUT, "frequency-tier.json"), freq_tier)

# ── Step 2: Scenario alignment ──────────────────────────────────────────────
scenario_align = []
for ft in freq_tier:
    if ft["tier"] == "protected":
        continue

    tid = ft["task_id"]
    task = tasks[tid]

    # Question A: Core scenario?
    screens_for_task = task_screen_map.get(tid, [])
    if screens_for_task:
        is_high_freq_action = False
        for s in screens_for_task:
            for a in s.get("actions", []):
                if a.get("task_ref") == tid and a.get("frequency") == "高":
                    is_high_freq_action = True
                    break
        question_a = "core" if is_high_freq_action else "secondary"
    else:
        question_a = "none"

    # Question B: Complexity vs frequency match
    main_flow = task.get("main_flow", [])
    rules = task.get("rules", [])
    exceptions = task.get("exceptions", [])
    complexity = "high" if (len(main_flow) >= 5 or len(rules) >= 3 or len(exceptions) >= 3) else (
        "low" if (len(main_flow) <= 2 and len(rules) <= 1) else "medium"
    )
    freq = ft["frequency"]
    if freq == "低" and complexity in ("high", "medium"):
        question_b = "over_engineered"
    elif freq == "低" and complexity == "low":
        question_b = "match"
    elif freq == "中" and complexity == "high":
        question_b = "over_engineered"
    else:
        question_b = "match"

    # Question C: Cross-department dependency
    question_c = "standalone"

    # ── Risk guardrail: low-frequency tasks that must NOT be CUT ──────────
    risk_level = task.get("risk_level", "低")
    revenue_keywords = {"付费", "购买", "订阅", "支付", "充值", "续费"}
    is_revenue = any(kw in task["task_name"] for kw in revenue_keywords)
    has_business_rules = len(rules) >= 2 or len(exceptions) >= 1
    is_risk_protected = (risk_level in ("高", "中")) or is_revenue or has_business_rules

    # Preliminary decision based on scope_strategy
    if scope_strategy == "aggressive":
        if freq == "高":
            prelim = "CORE"
        elif freq == "中" and question_a == "core":
            prelim = "CORE"
        elif freq == "中" and question_a != "core":
            prelim = "DEFER"
        elif freq == "低" and (tid in flow_task_refs or is_risk_protected):
            prelim = "DEFER"
        elif freq == "低":
            prelim = "CUT"
        else:
            prelim = "DEFER"
    elif scope_strategy == "balanced":
        if freq == "高":
            prelim = "CORE"
        elif freq == "中":
            prelim = "CORE"
        elif freq == "低" and (question_a == "core" or is_risk_protected):
            prelim = "DEFER"
        else:
            prelim = "CUT"
    else:  # conservative
        if freq == "高":
            prelim = "CORE"
        elif freq == "中":
            prelim = "CORE"
        elif freq == "低" and question_a == "core":
            prelim = "CORE"
        elif freq == "低" and is_risk_protected:
            prelim = "CORE"
        else:
            prelim = "DEFER"

    reason_parts = [f"频次={freq}", f"场景={question_a}",
                    f"复杂度匹配={question_b}", f"风险={risk_level}"]
    if tid in flow_task_refs:
        reason_parts.append("被业务流引用")
    if is_risk_protected and freq == "低":
        guardrail_reasons = []
        if risk_level in ("高", "中"):
            guardrail_reasons.append(f"risk={risk_level}")
        if is_revenue:
            guardrail_reasons.append("营收相关")
        if has_business_rules:
            guardrail_reasons.append(f"rules={len(rules)},exceptions={len(exceptions)}")
        reason_parts.append(f"护栏保护({'+'.join(guardrail_reasons)})")
    reason_parts.append(f"策略={scope_strategy}")

    scenario_align.append({
        "task_id": tid,
        "task_name": task["task_name"],
        "tier": ft["tier"],
        "question_a": question_a,
        "question_b": question_b,
        "question_c": question_c,
        "preliminary_decision": prelim,
        "reason": "；".join(reason_parts)
    })

C.write_json(os.path.join(OUT, "scenario-alignment.json"), scenario_align)

# ── Step 3: Competitive reference ────────────────────────────────────────────
comp_ref = {
    "competitors": competitors,
    "analysis_date": NOW[:10],
    "note": "全自动模式 — 竞品覆盖为估算值，基于产品类型",
    "features": []
}

core_features_competitors_have = {
    "浏览并选择场景", "进行场景对话", "查看对话报告", "查看实时发音纠正",
    "完成记忆曲线复习", "登录账户", "注册账户", "查看个性化推荐",
    "订阅付费方案"
}
some_features = {
    "进行自由对话", "查看发音详细报告", "管理词汇本", "查看学习连胜与成就",
    "查看排行榜", "管理个人设置", "查看学习统计报告", "管理通知中心"
}

for tid, task in tasks.items():
    tname = task["task_name"]
    if tname in core_features_competitors_have:
        coverage = "all_have"
    elif tname in some_features:
        coverage = "some_have"
    else:
        coverage = "none_have"
    comp_ref["features"].append({
        "task_id": tid,
        "task_name": tname,
        "competitor_coverage": coverage,
        "notes": ""
    })

C.write_json(os.path.join(OUT, "competitive-ref.json"), comp_ref)

# ── Step 4: Classification decisions ─────────────────────────────────────────
decisions = []

# Protected tasks = CORE
for ft in freq_tier:
    if ft["tier"] == "protected":
        decisions.append({
            "step": "Step 4",
            "item_id": ft["task_id"],
            "item_name": ft["task_name"],
            "decision": "CORE",
            "reason": f"高频受保护（frequency=高）— 策略={scope_strategy}",
            "decided_at": NOW
        })

# Candidate/review tasks = from scenario alignment
for sa in scenario_align:
    decisions.append({
        "step": "Step 4",
        "item_id": sa["task_id"],
        "item_name": sa["task_name"],
        "decision": sa["preliminary_decision"],
        "reason": sa["reason"],
        "decided_at": NOW
    })

C.write_json(os.path.join(OUT, "prune-decisions.json"), decisions)

# ── Step 5: Generate prune tasks ─────────────────────────────────────────────
prune_tasks = []
prune_counter = 0

for d in decisions:
    if d["decision"] in ("DEFER", "CUT"):
        prune_counter += 1
        tid = d["item_id"]
        task = tasks.get(tid, {})
        sids = [s["id"] for s in task_screen_map.get(tid, [])]

        if d["decision"] == "DEFER":
            action = "从当前迭代移除，迁移到 backlog，3个月后重新评估"
            risk = "低"
        else:
            action = "标记移除，通知开发团队清理相关代码和界面"
            risk = "中" if tid in flow_task_refs else "低"

        prune_tasks.append({
            "id": f"PRUNE-{prune_counter:03d}",
            "title": f"{task.get('task_name', tid)} → {d['decision']}",
            "decision": d["decision"],
            "affected_tasks": [tid],
            "affected_screens": sids,
            "reason": d["reason"],
            "action": action,
            "risk": risk
        })

C.write_json(os.path.join(OUT, "prune-tasks.json"), prune_tasks)

# ── Statistics ────────────────────────────────────────────────────────────────
core_count = sum(1 for d in decisions if d["decision"] == "CORE")
defer_count = sum(1 for d in decisions if d["decision"] == "DEFER")
cut_count = sum(1 for d in decisions if d["decision"] == "CUT")

# ── Markdown report ──────────────────────────────────────────────────────────
lines = []
lines.append("# 功能剪枝报告\n")
lines.append(f"策略: {scope_strategy}\n")
lines.append("## 总览\n")
lines.append("| 分类 | 数量 |")
lines.append("|------|------|")
lines.append(f"| CORE（必须保留）| {core_count} |")
lines.append(f"| DEFER（推迟）| {defer_count} |")
lines.append(f"| CUT（移除）| {cut_count} |")

if cut_count > 0:
    lines.append("\n## CUT 清单\n")
    lines.append("| 任务 | 频次 | 场景 | 理由 |")
    lines.append("|------|------|------|------|")
    for d in decisions:
        if d["decision"] == "CUT":
            tid = d["item_id"]
            task = tasks.get(tid, {})
            lines.append(f"| {d['item_name']} | {task.get('frequency', '-')} | {d['reason'][:40]} | {d['reason']} |")

if defer_count > 0:
    lines.append("\n## DEFER 清单\n")
    lines.append("| 任务 | 频次 | 理由 | 建议重评时间 |")
    lines.append("|------|------|------|-------------|")
    for d in decisions:
        if d["decision"] == "DEFER":
            tid = d["item_id"]
            task = tasks.get(tid, {})
            lines.append(f"| {d['item_name']} | {task.get('frequency', '-')} | {d['reason']} | 3个月后 |")

lines.append("\n## CORE 清单\n")
lines.append("| 任务 | 频次 | 理由 |")
lines.append("|------|------|------|")
for d in decisions:
    if d["decision"] == "CORE":
        tid = d["item_id"]
        task = tasks.get(tid, {})
        lines.append(f"| {d['item_name']} | {task.get('frequency', '-')} | {d['reason'][:60]} |")

with open(os.path.join(OUT, "prune-report.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

# ── Pipeline decisions ────────────────────────────────────────────────────────
C.append_pipeline_decision(
    BASE,
    "Phase 6 — feature-prune",
    f"strategy={scope_strategy}, CORE={core_count}, DEFER={defer_count}, CUT={cut_count}"
)

# ── Summary ───────────────────────────────────────────────────────────────────
print(f"Strategy: {scope_strategy}")
print(f"CORE: {core_count}")
print(f"DEFER: {defer_count}")
print(f"CUT: {cut_count}")
print(f"Prune tasks: {len(prune_tasks)}")
print(f"Competitors: {competitors}")
print(f"\nAll files written to {OUT}/")
