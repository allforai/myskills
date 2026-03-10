#!/usr/bin/env python3
# Skeleton generator — LLM enrichment required after running
"""Generate feature-prune analysis: frequency-tier, task listing with
category/frequency data, and prune-report.

Skeleton generator: lists all tasks with their category and frequency.
No keyword-based revenue detection, entity overlap checking, or prune decisions.

Usage:
    python3 gen_feature_prune.py <BASE_PATH> [--mode auto] [--strategy aggressive|balanced|conservative] [--shard <name>]
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
role_map = C.load_role_profiles(BASE)

concept = C.load_product_concept(BASE)
prefs = concept.get("pipeline_preferences", {}) if concept else {}
scope_strategy = args.get("strategy", prefs.get("scope_strategy", "balanced"))
competitors = prefs.get("competitors", [])

op_lines, screen_index, em_loaded = C.load_experience_map(BASE)
task_screen_map = C.build_task_screen_map_from_lines(op_lines)

# Count operation lines per task
task_line_count = {}
for ol in op_lines:
    for node in ol.get("nodes", []):
        for s in node.get("screens", []):
            for tid in s.get("tasks", []):
                task_line_count.setdefault(tid, set()).add(ol["id"])

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
        "name": task["task_name"],
        "frequency": freq,
        "tier": tier,
        "line_count": line_count,
        "data_points": f"frequency={freq}, risk={task.get('risk_level', '低')}, lines={line_count}"
    })

C.write_json(os.path.join(OUT, "frequency-tier.json"), freq_tier)

# ── Step 2: Task data listing for LLM decision ──────────────────────────────
task_listing = []
for tid, task in tasks.items():
    role_id = task.get("owner_role") or task.get("role_id", "")
    sids = task_screen_map.get(tid, [])
    task_listing.append({
        "task_id": tid,
        "name": task["task_name"],
        "category": task.get("category", ""),
        "frequency": task.get("frequency", "低"),
        "risk_level": task.get("risk_level", "低"),
        "role": role_map.get(role_id, role_id),
        "in_business_flow": tid in flow_task_refs,
        "screen_count": len(sids),
        "line_count": len(task_line_count.get(tid, set())),
        "main_flow_steps": len(task.get("main_flow", [])),
        "rules_count": len(task.get("rules", [])),
        "exceptions_count": len(task.get("exceptions", [])),
        "flags": ["SKELETON_NEEDS_LLM_DECISION"]
    })

C.write_json(os.path.join(OUT, "task-listing.json"), task_listing)

# ── Step 3: Competitive reference (placeholder) ─────────────────────────────
comp_ref = {
    "competitors": competitors,
    "analysis_date": NOW[:10],
    "note": "骨架输出 — 竞品覆盖需 LLM 分析",
    "features": [{
        "task_id": tid,
        "name": task["task_name"],
        "competitor_coverage": "unknown",
        "notes": ""
    } for tid, task in tasks.items()]
}

C.write_json(os.path.join(OUT, "competitive-ref.json"), comp_ref)

# ── Placeholder decisions (all pending LLM) ──────────────────────────────────
decisions = []
for ft in freq_tier:
    tid = ft["task_id"]
    task = tasks[tid]
    freq = ft["frequency"]

    # Only structural classification: high-freq = CORE, rest = PENDING
    if freq == "高":
        decision = "CORE"
        reason = f"高频受保护 — 策略={scope_strategy}"
    else:
        decision = "PENDING_LLM"
        reason = (f"频次={freq}, 类别={task.get('category', '未分类')}, "
                  f"风险={task.get('risk_level', '低')}, 策略={scope_strategy} — 需 LLM 决策")

    decisions.append({
        "step": "Step 4",
        "item_id": tid,
        "task_id": tid,
        "item_name": ft["name"],
        "decision": decision,
        "reason": reason,
        "decided_at": NOW
    })

C.write_json(os.path.join(OUT, "prune-decisions.json"), decisions)

# ── Statistics ────────────────────────────────────────────────────────────────
core_count = sum(1 for d in decisions if d["decision"] == "CORE")
pending_count = sum(1 for d in decisions if d["decision"] == "PENDING_LLM")

# ── Markdown report ──────────────────────────────────────────────────────────
lines = []
lines.append("# 功能剪枝报告（骨架）\n")
lines.append(f"策略: {scope_strategy}\n")
lines.append("> **骨架输出** — 仅高频任务自动标记 CORE，其余需 LLM 决策\n")
lines.append("## 总览\n")
lines.append("| 分类 | 数量 |")
lines.append("|------|------|")
lines.append(f"| CORE（高频保护）| {core_count} |")
lines.append(f"| PENDING_LLM（待决策）| {pending_count} |")

lines.append("\n## 任务数据清单\n")
lines.append("| 任务 | 频次 | 风险 | 类别 | 业务流 | 界面数 |")
lines.append("|------|------|------|------|--------|--------|")
for tl in task_listing:
    lines.append(f"| {tl['name']} | {tl['frequency']} | {tl['risk_level']} | "
                 f"{tl['category'] or '-'} | {'是' if tl['in_business_flow'] else '否'} | {tl['screen_count']} |")

with open(os.path.join(OUT, "prune-report.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

# ── Pipeline decisions ────────────────────────────────────────────────────────
C.append_pipeline_decision(
    BASE,
    "Phase 6 — feature-prune",
    f"strategy={scope_strategy}, CORE={core_count}, PENDING_LLM={pending_count} (skeleton)",
    shard=args.get("shard")
)

# ── Summary ───────────────────────────────────────────────────────────────────
print(f"Strategy: {scope_strategy}")
print(f"CORE: {core_count}")
print(f"PENDING_LLM: {pending_count}")
print(f"Tasks listed: {len(task_listing)}")
print(f"Competitors: {competitors}")
print(f"\nAll files written to {OUT}/")
