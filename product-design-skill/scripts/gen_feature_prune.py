#!/usr/bin/env python3
"""Generate feature-prune analysis: frequency-tier, scenario-alignment,
competitive-ref, prune-decisions, prune-tasks, and prune-report.

Pre-built script for Phase 6 (feature-prune). Fixes:
- Uses s.get("tasks", []) instead of hardcoded field names
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

# Load experience-map for scenario alignment
op_lines, screen_index, em_loaded = C.load_experience_map(BASE)
screens_by_id = C.build_screen_by_id_from_lines(op_lines)
task_screen_map = C.build_task_screen_map_from_lines(op_lines)

# Count operation lines per task (frequency signal)
task_line_count = {}
for ol in op_lines:
    for node in ol.get("nodes", []):
        for s in node.get("screens", []):
            for tid in s.get("tasks", []):
                task_line_count.setdefault(tid, set()).add(ol["id"])

# Load business flows for CUT safety check
flows = C.load_business_flows(BASE)
flow_task_refs = C.collect_flow_task_refs(flows)

# ── Step 1: Frequency tier ───────────────────────────────────────────────────
freq_tier = []
for tid, task in tasks.items():
    freq = task.get("frequency", "低")
    line_count = len(task_line_count.get(tid, set()))
    if freq == "高":
        tier = "protected"
    elif freq == "低" and line_count == 0:
        tier = "candidate"
    elif freq == "低":
        tier = "candidate" if line_count <= 1 else "review"
    else:
        tier = "review"
    freq_tier.append({
        "task_id": tid,
        "name": task["name"],
        "frequency": freq,
        "tier": tier,
        "line_count": line_count,
        "data_points": f"frequency={freq}, risk={task.get('risk_level', '低')}, lines={line_count}"
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
    screen_ids_for_task = task_screen_map.get(tid, [])
    line_count = len(task_line_count.get(tid, set()))
    if screen_ids_for_task:
        is_high_freq_action = False
        for sid in screen_ids_for_task:
            scr = screens_by_id.get(sid, {})
            for a in scr.get("actions", []):
                if a.get("task_ref") == tid and a.get("frequency") == "高":
                    is_high_freq_action = True
                    break
        # Also consider high line count as a core signal
        question_a = "core" if (is_high_freq_action or line_count >= 3) else "secondary"
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
    category = task.get("category", "")
    revenue_keywords = {"付费", "购买", "订阅", "支付", "充值", "续费"}
    is_revenue = any(kw in task["name"] for kw in revenue_keywords)
    has_business_rules = len(rules) >= 2 or len(exceptions) >= 1
    is_basic = category == "basic"

    # CRUD completeness: if sibling create/edit exists, delete/cancel must not be CUT
    crud_create = {"创建", "添加", "新增", "注册", "申请", "发起", "提交", "撰写"}
    crud_reverse = {"删除", "移除", "取消", "撤回", "撤销"}
    task_name = task["name"]
    is_crud_reverse = any(kw in task_name for kw in crud_reverse)
    has_crud_sibling = False
    if is_crud_reverse:
        # Extract entity from reverse task by stripping the reverse keyword
        reverse_entity = task_name
        for kw in crud_reverse:
            reverse_entity = reverse_entity.replace(kw, "")

        # Check if any task in same role has a create/forward operation on same entity
        role = task.get("owner_role", "")
        for other_tid, other_task in tasks.items():
            if other_tid == tid:
                continue
            if other_task.get("owner_role") == role:
                other_name = other_task["name"]
                if any(kw in other_name for kw in crud_create):
                    # Method 1: share >=2 common chars at end (e.g. 宠物档案)
                    for elen in range(4, 1, -1):
                        if len(task_name) >= elen and len(other_name) >= elen:
                            if task_name[-elen:] == other_name[-elen:]:
                                has_crud_sibling = True
                                break
                    # Method 2: entity overlap — strip CRUD keywords, check >=2 char overlap
                    if not has_crud_sibling and len(reverse_entity) >= 2:
                        other_entity = other_name
                        for kw in crud_create:
                            other_entity = other_entity.replace(kw, "")
                        if len(other_entity) >= 2:
                            for elen in range(min(len(reverse_entity), len(other_entity)), 1, -1):
                                if reverse_entity in other_entity or other_entity in reverse_entity:
                                    has_crud_sibling = True
                                    break
                    if has_crud_sibling:
                        break

    is_crud_protected = is_crud_reverse and has_crud_sibling

    is_risk_protected = is_basic or (risk_level in ("高", "中")) or is_revenue or has_business_rules or is_crud_protected

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
                    f"复杂度匹配={question_b}", f"风险={risk_level}",
                    f"类别={category or '未分类'}"]
    if tid in flow_task_refs:
        reason_parts.append("被业务流引用")
    if is_risk_protected and freq == "低":
        guardrail_reasons = []
        if is_basic:
            guardrail_reasons.append("basic基本功能")
        if risk_level in ("高", "中"):
            guardrail_reasons.append(f"risk={risk_level}")
        if is_revenue:
            guardrail_reasons.append("营收相关")
        if has_business_rules:
            guardrail_reasons.append(f"rules={len(rules)},exceptions={len(exceptions)}")
        if is_crud_protected:
            guardrail_reasons.append("CRUD完整性(反向操作)")
        reason_parts.append(f"护栏保护({'+'.join(guardrail_reasons)})")
    reason_parts.append(f"策略={scope_strategy}")

    scenario_align.append({
        "task_id": tid,
        "name": task["name"],
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
    tname = task["name"]
    if tname in core_features_competitors_have:
        coverage = "all_have"
    elif tname in some_features:
        coverage = "some_have"
    else:
        coverage = "none_have"
    comp_ref["features"].append({
        "task_id": tid,
        "name": tname,
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
            "task_id": ft["task_id"],
            "item_name": ft["name"],
            "decision": "CORE",
            "reason": f"高频受保护（frequency=高）— 策略={scope_strategy}",
            "decided_at": NOW
        })

# Candidate/review tasks = from scenario alignment
for sa in scenario_align:
    decisions.append({
        "step": "Step 4",
        "item_id": sa["task_id"],
        "task_id": sa["task_id"],
        "item_name": sa["name"],
        "decision": sa["preliminary_decision"],
        "reason": sa["reason"],
        "decided_at": NOW
    })

C.write_json(os.path.join(OUT, "prune-decisions.json"), decisions)


# ── XV auto-apply helpers ────────────────────────────────────────────────────

def _apply_pruning_findings(data, decisions, tasks):
    """Apply pruning second-opinion findings: promote risky CUTs, demote over-kept.

    Returns (promoted_count, demoted_count).
    """
    dec_by_id = {d["item_id"]: d for d in decisions}
    promoted = 0
    demoted = 0

    for item in data.get("risky_cuts", []):
        tid = item.get("task_id", "")
        rec = item.get("recommended", "")
        if tid in dec_by_id and dec_by_id[tid]["decision"] == "CUT" and rec in ("CORE", "DEFER"):
            dec_by_id[tid]["decision"] = rec
            dec_by_id[tid].setdefault("xv_notes", []).append(
                f"XV: CUT→{rec} — {item.get('reason', '')}"
            )
            promoted += 1

    for item in data.get("over_kept", []):
        tid = item.get("task_id", "")
        rec = item.get("recommended", "")
        if tid in dec_by_id and dec_by_id[tid]["decision"] == "CORE" and rec in ("DEFER", "CUT"):
            # Only demote if not high-frequency and not basic category
            task = tasks.get(tid, {})
            if task.get("frequency") != "高" and task.get("category") != "basic":
                dec_by_id[tid]["decision"] = rec
                dec_by_id[tid].setdefault("xv_notes", []).append(
                    f"XV: CORE→{rec} — {item.get('reason', '')}"
                )
                demoted += 1

    return promoted, demoted


def _apply_competitive_findings(data, decisions):
    """Apply competitive benchmark: flag competitive risks on CUT/DEFER items.

    Returns flagged_count.
    """
    dec_by_id = {d["item_id"]: d for d in decisions}
    flagged = 0

    for risk in data.get("competitive_risks", []):
        tid = risk.get("task_id", "")
        if tid not in dec_by_id:
            continue
        current = dec_by_id[tid]["decision"]
        if current not in ("CUT", "DEFER"):
            continue
        note = f"XV competitive risk: {risk.get('risk', '')} (coverage={risk.get('coverage', '')})"
        # Promote CUT→DEFER if competitors all have it (only if still CUT)
        if current == "CUT" and risk.get("coverage") == "all_have":
            dec_by_id[tid]["decision"] = "DEFER"
            note += " → CUT promoted to DEFER"
        dec_by_id[tid].setdefault("xv_notes", []).append(note)
        flagged += 1

    return flagged


# ── XV Cross-model validation ────────────────────────────────────────────────
xv_reviews = []

if C.xv_available():
    from xv_prompts import pruning_second_opinion_prompt, competitive_benchmark_prompt

    # XV-1: pruning_second_opinion → gemini
    try:
        ps_prompt = pruning_second_opinion_prompt(decisions, tasks, flow_task_refs)
        ps_result = C.xv_call("pruning_second_opinion", ps_prompt["user"], ps_prompt["system"])
        print(f"  XV pruning_second_opinion: model={ps_result['model_used']}")
        ps_data = C.xv_parse_json(ps_result["response"])
        promoted, demoted = _apply_pruning_findings(ps_data, decisions, tasks)
        xv_reviews.append({
            "task_type": "pruning_second_opinion",
            "model_used": ps_result["model_used"],
            "family": ps_result["family"],
            "auto_applied": {"promoted": promoted, "demoted": demoted},
            "raw_findings": ps_data,
        })
        print(f"  XV pruning_second_opinion: {promoted} promoted, {demoted} demoted")
    except Exception as e:
        print(f"  XV pruning_second_opinion failed: {e} (continuing without XV)", file=sys.stderr)

    # XV-2: competitive_benchmark → deepseek
    # NOTE: runs after XV-1; `decisions` list is mutated in-place by XV-1,
    # so XV-2 sees XV-1's promoted/demoted changes via Python reference semantics.
    try:
        cb_prompt = competitive_benchmark_prompt(comp_ref, decisions)
        cb_result = C.xv_call("competitive_benchmark", cb_prompt["user"], cb_prompt["system"])
        print(f"  XV competitive_benchmark: model={cb_result['model_used']}")
        cb_data = C.xv_parse_json(cb_result["response"])
        flagged = _apply_competitive_findings(cb_data, decisions)
        xv_reviews.append({
            "task_type": "competitive_benchmark",
            "model_used": cb_result["model_used"],
            "family": cb_result["family"],
            "auto_applied": {"competitive_flags": flagged},
            "raw_findings": cb_data,
        })
        print(f"  XV competitive_benchmark: {flagged} competitive flags")
    except Exception as e:
        print(f"  XV competitive_benchmark failed: {e} (continuing without XV)", file=sys.stderr)

    if xv_reviews:
        # Rewrite prune-decisions.json with XV corrections
        C.write_json(os.path.join(OUT, "prune-decisions.json"), decisions)
        # Write XV review to separate file
        C.write_json(os.path.join(OUT, "prune-xv-review.json"), C.xv_review(xv_reviews))
        print(f"  XV: prune-decisions.json rewritten, prune-xv-review.json created")
    else:
        print(f"  XV: all calls failed, primary output unchanged")


# ── Step 5: Generate prune tasks ─────────────────────────────────────────────
prune_tasks = []
prune_counter = 0

for d in decisions:
    if d["decision"] in ("DEFER", "CUT"):
        prune_counter += 1
        tid = d["item_id"]
        task = tasks.get(tid, {})
        sids = task_screen_map.get(tid, [])

        if d["decision"] == "DEFER":
            action = "从当前迭代移除，迁移到 backlog，3个月后重新评估"
            risk = "低"
        else:
            action = "标记移除，通知开发团队清理相关代码和界面"
            risk = "中" if tid in flow_task_refs else "低"

        prune_tasks.append({
            "id": f"PRUNE-{prune_counter:03d}",
            "title": f"{task.get('name', tid)} → {d['decision']}",
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
    f"strategy={scope_strategy}, CORE={core_count}, DEFER={defer_count}, CUT={cut_count}",
    shard=args.get("shard")
)

# ── Summary ───────────────────────────────────────────────────────────────────
print(f"Strategy: {scope_strategy}")
print(f"CORE: {core_count}")
print(f"DEFER: {defer_count}")
print(f"CUT: {cut_count}")
print(f"Prune tasks: {len(prune_tasks)}")
print(f"Competitors: {competitors}")
print(f"\nAll files written to {OUT}/")
