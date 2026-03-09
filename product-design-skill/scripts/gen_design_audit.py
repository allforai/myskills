#!/usr/bin/env python3
"""Generate design audit: trace, coverage, cross-check, continuity, fidelity, and report.

Pre-built script for Phase 8 (design-audit). Fixes:
- Fixed gaps[:30) syntax error → gaps[:30]
- Uses experience-map (operation_lines) instead of screen-map
- Adds continuity audit via interaction-gate
- Pipeline-decisions dedup via _common.append_pipeline_decision()

Usage:
    python3 gen_design_audit.py <BASE_PATH> [--mode auto]
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C

# ── Setup ─────────────────────────────────────────────────────────────────────
BASE, args = C.parse_args()
OUT = os.path.join(BASE, "design-audit")
C.ensure_dir(OUT)
NOW = C.now_iso()

# ── Layer detection ───────────────────────────────────────────────────────────
available_layers = []

# product-map (required)
pm = C.load_json(os.path.join(BASE, "product-map/product-map.json"))
if not pm:
    print("ERROR: product-map.json not found", file=sys.stderr)
    sys.exit(1)
available_layers.append("product-map")

inv = C.load_json(os.path.join(BASE, "product-map/task-inventory.json"))
tasks = {t["id"]: C._normalize_task(t) for t in inv["tasks"]} if inv else {}
task_ids = set(tasks.keys())

# experience-map (recommended — missing triggers WARNING)
op_lines, screen_index_data, em_loaded = C.load_experience_map(BASE)
screens = C.build_screen_by_id_from_lines(op_lines) if em_loaded else {}
screen_task_map = {}  # screen_id -> [task_ids]
task_screen_map = {}  # task_id -> [screen_ids]
if em_loaded:
    available_layers.append("experience-map")
    for ol in op_lines:
        for node in ol.get("nodes", []):
            for s in node.get("screens", []):
                sid = s["id"]
                trefs = s.get("tasks", [])
                screen_task_map[sid] = trefs
                for tid in trefs:
                    task_screen_map.setdefault(tid, []).append(sid)

# use-case (optional)
uc = C.load_json(os.path.join(BASE, "use-case/use-case-tree.json"))
uc_task_map = {}  # task_id -> [use_case_ids]
uc_screen_refs = {}  # uc_id -> screen_ref
if uc:
    available_layers.append("use-case")
    for role in uc.get("roles", []):
        for fa in role.get("feature_areas", []):
            for t_data in fa.get("tasks", []):
                raw_tid = t_data["id"]
                # Handle composite task IDs like "T014_T015"
                parts = raw_tid.split("_") if "_" in raw_tid else [raw_tid]
                tids = parts if all(p.upper().startswith("T") for p in parts) else [raw_tid]
                for ucase in t_data.get("use_cases", []):
                    for tid in tids:
                        uc_task_map.setdefault(tid, []).append(ucase["id"])
                    if ucase.get("screen_ref"):
                        uc_screen_refs[ucase["id"]] = ucase["screen_ref"]

# feature-gap (optional)
_gap_raw = C.load_json(os.path.join(BASE, "feature-gap/gap-tasks.json"))
gap = C.ensure_list(_gap_raw, "gap_tasks", "gaps") if _gap_raw else []
gap_task_ids = set()
if gap:
    available_layers.append("feature-gap")
    for g in gap:
        if not isinstance(g, dict):
            continue
        affected = g.get("affected_tasks", [])
        if isinstance(affected, str):
            affected = [affected]
        if affected:
            for tid in affected:
                gap_task_ids.add(tid)
        elif "task_id" in g:
            gap_task_ids.add(g["task_id"])

# Also load task-gaps for per-task check
_tg_raw = C.load_json(os.path.join(BASE, "feature-gap/task-gaps.json"))
task_gaps_data = C.ensure_list(_tg_raw, "task_gaps", "tasks") if _tg_raw else []
gap_checked_tasks = set()
for tg in task_gaps_data:
    if not isinstance(tg, dict):
        continue
    tid = tg.get("task_id", tg.get("id", ""))
    if tid:
        gap_checked_tasks.add(tid)

# feature-prune (optional)
_prune_raw = C.load_json(os.path.join(BASE, "feature-prune/prune-decisions.json"))
prune = C.ensure_list(_prune_raw, "prune_decisions", "decisions") if _prune_raw else []
prune_map = {}  # task_id -> decision
if prune:
    available_layers.append("feature-prune")
    for d in prune:
        if not isinstance(d, dict):
            continue
        tid = d.get("task_id", d.get("item_id"))
        if tid:
            prune_map[tid] = d.get("decision", "")

# ui-design (optional)
ui_spec_path = os.path.join(BASE, "ui-design/ui-design-spec.md")
ui_spec_text = ""
if os.path.exists(ui_spec_path):
    available_layers.append("ui-design")
    with open(ui_spec_path) as f:
        ui_spec_text = f.read()

ctx = C.load_full_context(BASE)

print(f"Available layers: {available_layers}")

# ── Step 1: Trace (reverse) ──────────────────────────────────────────────────
trace_issues = []
trace_total = 0
trace_pass = 0

# T1: screen -> task
if "experience-map" in available_layers:
    for sid, trefs in screen_task_map.items():
        for tid in trefs:
            trace_total += 1
            if tid not in task_ids:
                trace_issues.append({
                    "check_id": "T1",
                    "type": "ORPHAN",
                    "source": "experience-map",
                    "item_id": sid,
                    "item_name": screens[sid].get("name", ""),
                    "missing_ref": tid,
                    "detail": f"screen {sid} 引用了不存在的 task {tid}"
                })
            else:
                trace_pass += 1

# T2: use-case -> task
if "use-case" in available_layers:
    for tid, uids in uc_task_map.items():
        trace_total += 1
        if tid not in task_ids:
            trace_issues.append({
                "check_id": "T2",
                "type": "ORPHAN",
                "source": "use-case",
                "item_id": uids[0] if uids else "?",
                "item_name": f"use-case for {tid}",
                "missing_ref": tid,
                "detail": f"use-case 引用了不存在的 task {tid}"
            })
        else:
            trace_pass += 1

# T3: use-case screen_ref -> experience-map
# screen_ref may be comma-separated (e.g. "S005,S006") or single ID
if "use-case" in available_layers and "experience-map" in available_layers:
    for ucid, sref in uc_screen_refs.items():
        if not sref:
            continue
        refs = [r.strip() for r in sref.split(",")] if "," in sref else [sref]
        for ref in refs:
            trace_total += 1
            if ref not in screens:
                trace_issues.append({
                    "check_id": "T3",
                    "type": "ORPHAN",
                    "source": "use-case",
                    "item_id": ucid,
                    "item_name": f"use-case {ucid}",
                    "missing_ref": ref,
                    "detail": f"use-case {ucid} 的 screen_ref {ref} 在 experience-map 中不存在"
                })
            else:
                trace_pass += 1

# T5: prune-decision -> task
if "feature-prune" in available_layers:
    for tid in prune_map:
        trace_total += 1
        if tid not in task_ids:
            trace_issues.append({
                "check_id": "T5",
                "type": "ORPHAN",
                "source": "feature-prune",
                "item_id": tid,
                "item_name": f"prune decision for {tid}",
                "missing_ref": tid,
                "detail": f"prune 决策引用了不存在的 task {tid}"
            })
        else:
            trace_pass += 1

# ── Step 2: Coverage (flood) ─────────────────────────────────────────────────
coverage_issues = []
coverage_total = 0
coverage_covered = 0

for tid in task_ids:
    if "experience-map" in available_layers:
        coverage_total += 1
        if tid in task_screen_map:
            coverage_covered += 1
        else:
            coverage_issues.append({
                "check_id": "C1",
                "type": "GAP",
                "task_id": tid,
                "name": tasks[tid]["task_name"],
                "missing_in": "experience-map",
                "detail": f"任务 {tid} ({tasks[tid]['task_name']}) 在 experience-map 中无对应界面"
            })

    if "use-case" in available_layers:
        coverage_total += 1
        if tid in uc_task_map:
            coverage_covered += 1
        else:
            coverage_issues.append({
                "check_id": "C2",
                "type": "GAP",
                "task_id": tid,
                "name": tasks[tid]["task_name"],
                "missing_in": "use-case",
                "detail": f"任务 {tid} ({tasks[tid]['task_name']}) 无对应用例"
            })

    if "feature-gap" in available_layers:
        coverage_total += 1
        if tid in gap_checked_tasks:
            coverage_covered += 1
        else:
            coverage_issues.append({
                "check_id": "C3",
                "type": "GAP",
                "task_id": tid,
                "name": tasks[tid]["task_name"],
                "missing_in": "feature-gap",
                "detail": f"任务 {tid} ({tasks[tid]['task_name']}) 未被 feature-gap 检查"
            })

    if "feature-prune" in available_layers:
        coverage_total += 1
        if tid in prune_map:
            coverage_covered += 1
        else:
            coverage_issues.append({
                "check_id": "C4",
                "type": "GAP",
                "task_id": tid,
                "name": tasks[tid]["task_name"],
                "missing_in": "feature-prune",
                "detail": f"任务 {tid} ({tasks[tid]['task_name']}) 无 prune 决策"
            })

coverage_rate = f"{coverage_covered / coverage_total * 100:.0f}%" if coverage_total > 0 else "N/A"

# ── Step 3: Cross-check ──────────────────────────────────────────────────────
cross_issues = []
cross_total = 0
cross_ok = 0

# X1: gap x prune conflict
if "feature-gap" in available_layers and "feature-prune" in available_layers:
    for tid in gap_task_ids:
        if tid in prune_map:
            cross_total += 1
            if prune_map[tid] == "CUT":
                cross_issues.append({
                    "check_id": "X1",
                    "type": "CONFLICT",
                    "task_id": tid,
                    "name": tasks.get(tid, {}).get("name", "?"),
                    "detail": f"feature-gap 报 {tid} 有缺口，但 feature-prune 标为 CUT — 矛盾"
                })
            else:
                cross_ok += 1

# X2: ui-design x prune CUT
if "ui-design" in available_layers and "feature-prune" in available_layers:
    for tid, decision in prune_map.items():
        if decision == "CUT":
            cross_total += 1
            tname = tasks.get(tid, {}).get("name", "")
            if tname and tname in ui_spec_text:
                cross_issues.append({
                    "check_id": "X2",
                    "type": "CONFLICT",
                    "task_id": tid,
                    "name": tname,
                    "detail": f"CUT 任务 {tid} ({tname}) 仍出现在 ui-design-spec.md 中"
                })
            else:
                cross_ok += 1

# X3: frequency x click_depth
if "experience-map" in available_layers:
    for tid, task in tasks.items():
        if task.get("frequency") == "高":
            sids = task_screen_map.get(tid, [])
            for sid in sids:
                s = screens.get(sid, {})
                for a in s.get("actions", []):
                    if a.get("task_ref") == tid and a.get("click_depth", 1) >= 3:
                        cross_total += 1
                        cross_issues.append({
                            "check_id": "X3",
                            "type": "WARNING",
                            "task_id": tid,
                            "name": task["task_name"],
                            "detail": f"高频任务 {tid} 的操作 '{a.get('label', '')}' click_depth={a['click_depth']} ≥ 3（被埋深）"
                        })

# X4: category field completeness
tasks_without_category = [tid for tid, t in tasks.items() if not t.get("category")]
if tasks_without_category:
    cross_total += 1
    cross_issues.append({
        "check_id": "X4",
        "type": "WARNING",
        "task_id": ",".join(tasks_without_category[:5]),
        "name": f"{len(tasks_without_category)} tasks missing category",
        "detail": f"{len(tasks_without_category)} 个任务缺少 category 字段（basic/core），影响下游剪枝和优先级判定"
    })
else:
    cross_total += 1
    cross_ok += 1

# X5: basic category task should not be CUT
if "feature-prune" in available_layers:
    for tid, decision in prune_map.items():
        t = tasks.get(tid, {})
        if t.get("category") == "basic" and decision == "CUT":
            cross_total += 1
            cross_issues.append({
                "check_id": "X5",
                "type": "CONFLICT",
                "task_id": tid,
                "name": t.get("name", "?"),
                "detail": f"基本功能 {tid} ({t.get('name','?')}) 被标为 CUT — basic 类任务不应被剪除"
            })

# ── Continuity Audit ─────────────────────────────────────────────────────────
continuity_issues = []
gate = C.load_interaction_gate(BASE)
if gate:
    available_layers.append("interaction-gate")
    for lr in gate.get("lines", []):
        if lr.get("score", 100) < gate.get("threshold", 70):
            continuity_issues.append({
                "line_id": lr["line_id"],
                "score": lr["score"],
                "issues": lr.get("issues", []),
            })

# ── Fidelity ──────────────────────────────────────────────────────────────────
total_downstream = trace_total
traceable = trace_pass
traceability_rate = f"{traceable / total_downstream * 100:.0f}%" if total_downstream > 0 else "N/A"
traceability_status = "PASS" if total_downstream == 0 or (traceable / total_downstream >= 0.95) else "BELOW_THRESHOLD"

vp_total = len(task_ids)
vp_covered = 0
for tid in task_ids:
    viewpoints = 0
    if tid in task_screen_map:
        viewpoints += 1
    if tid in uc_task_map:
        viewpoints += 1
    if tid in gap_checked_tasks:
        viewpoints += 1
    if tid in prune_map:
        viewpoints += 1
    if viewpoints >= 4:
        vp_covered += 1
vp_rate = f"{vp_covered / vp_total * 100:.0f}%" if vp_total > 0 else "N/A"
vp_status = "PASS" if vp_total == 0 or (vp_covered / vp_total >= 0.90) else "BELOW_THRESHOLD"

# ── Build report ──────────────────────────────────────────────────────────────
report = {
    "generated_at": NOW,
    "mode": "full",
    "role_filter": None,
    "available_layers": available_layers,
    "summary": {
        "trace": {"total": trace_total, "pass": trace_pass, "orphan": len(trace_issues)},
        "coverage": {"total": coverage_total, "covered": coverage_covered,
                     "gap": len(coverage_issues), "rate": coverage_rate},
        "cross": {"total": cross_total, "ok": cross_ok,
                  "conflict": sum(1 for i in cross_issues if i["type"] == "CONFLICT"),
                  "warning": sum(1 for i in cross_issues if i["type"] == "WARNING"),
                  "broken_ref": sum(1 for i in cross_issues if i["type"] == "BROKEN_REF")},
        "continuity": {"total_lines": len(gate.get("lines", [])) if gate else 0,
                       "failing": len(continuity_issues)},
        "fidelity": {
            "traceability_rate": traceability_rate,
            "traceability_status": traceability_status,
            "viewpoint_coverage_rate": vp_rate,
            "viewpoint_status": vp_status
        }
    },
    "trace_issues": trace_issues,
    "coverage_issues": coverage_issues,
    "cross_issues": cross_issues,
    "continuity_issues": continuity_issues
}

# ── Active constraint tracking ──
if ctx.constraints:
    report["active_constraints"] = {
        "count": len(ctx.constraints),
        "by_target": {},
    }
    for c in ctx.constraints:
        target = c.get("target", "unknown")
        report["active_constraints"]["by_target"].setdefault(target, []).append({
            "id": c.get("id", ""),
            "constraint": c.get("constraint", ""),
            "severity": c.get("severity", "must"),
        })
    print(f"  Active constraints: {len(ctx.constraints)}")

C.write_json(os.path.join(OUT, "audit-report.json"), report)


# ── XV auto-apply helpers ────────────────────────────────────────────────────

def _apply_cross_layer_findings(data, trace_issues, cross_issues):
    """Apply cross-layer validation: annotate root causes, remove false alarms.

    Returns (root_cause_count, false_alarm_count).
    """
    root_count = 0
    alarm_count = 0

    # Annotate root causes on affected issues
    for rc in data.get("root_causes", []):
        if rc.get("severity") == "high":
            root_count += 1

    # Mark false alarms using _xv_id composite keys
    false_ids = {fa.get("issue_id", "") for fa in data.get("false_alarms", [])}
    for ti in trace_issues:
        xv_id = f"TRACE-{ti.get('check_id', '')}-{ti.get('item_id', '')}"
        if xv_id in false_ids:
            ti["xv_false_alarm"] = True
            alarm_count += 1
    for ci in cross_issues:
        xv_id = f"CROSS-{ci.get('check_id', '')}-{ci.get('task_id', '')}"
        if xv_id in false_ids:
            ci["xv_false_alarm"] = True
            alarm_count += 1

    return root_count, alarm_count


def _apply_coverage_findings(data, coverage_issues):
    """Apply coverage analysis: annotate critical gaps and acceptable gaps.

    Returns (critical_count, acceptable_count).
    """
    critical_count = 0
    acceptable_count = 0

    acceptable_ids = {ag.get("task_id", "") for ag in data.get("acceptable_gaps", [])}
    critical_ids = {cg.get("task_id", "") for cg in data.get("critical_gaps", [])}

    for ci in coverage_issues:
        tid = ci.get("task_id", "")
        if tid in critical_ids:
            ci["xv_critical"] = True
            critical_count += 1
        elif tid in acceptable_ids:
            ci["xv_acceptable"] = True
            acceptable_count += 1

    return critical_count, acceptable_count


# ── XV Cross-model validation ────────────────────────────────────────────────
xv_reviews = []

if C.xv_available():
    from xv_prompts import cross_layer_validation_prompt, coverage_analysis_prompt

    # XV-1: cross_layer_validation → deepseek
    try:
        cl_prompt = cross_layer_validation_prompt(trace_issues, cross_issues, available_layers)
        cl_result = C.xv_call("cross_layer_validation", cl_prompt["user"], cl_prompt["system"])
        print(f"  XV cross_layer_validation: model={cl_result['model_used']}")
        cl_data = C.xv_parse_json(cl_result["response"])
        root_count, alarm_count = _apply_cross_layer_findings(cl_data, trace_issues, cross_issues)
        xv_reviews.append({
            "task_type": "cross_layer_validation",
            "model_used": cl_result["model_used"],
            "family": cl_result["family"],
            "auto_applied": {"root_causes": root_count, "false_alarms": alarm_count},
            "raw_findings": cl_data,
        })
        print(f"  XV cross_layer_validation: {root_count} root causes, {alarm_count} false alarms")
    except Exception as e:
        print(f"  XV cross_layer_validation failed: {e} (continuing without XV)", file=sys.stderr)

    # XV-2: coverage_analysis → gpt
    try:
        ca_prompt = coverage_analysis_prompt(coverage_issues, len(task_ids), len(available_layers))
        ca_result = C.xv_call("coverage_analysis", ca_prompt["user"], ca_prompt["system"])
        print(f"  XV coverage_analysis: model={ca_result['model_used']}")
        ca_data = C.xv_parse_json(ca_result["response"])
        critical_count, acceptable_count = _apply_coverage_findings(ca_data, coverage_issues)
        xv_reviews.append({
            "task_type": "coverage_analysis",
            "model_used": ca_result["model_used"],
            "family": ca_result["family"],
            "auto_applied": {"critical_gaps": critical_count, "acceptable_gaps": acceptable_count},
            "raw_findings": ca_data,
        })
        print(f"  XV coverage_analysis: {critical_count} critical, {acceptable_count} acceptable")
    except Exception as e:
        print(f"  XV coverage_analysis failed: {e} (continuing without XV)", file=sys.stderr)

    if xv_reviews:
        # Rewrite audit-report.json with XV annotations
        report["cross_model_review"] = C.xv_review(xv_reviews)
        C.write_json(os.path.join(OUT, "audit-report.json"), report)
        # Write XV review to separate file
        C.write_json(os.path.join(OUT, "audit-xv-review.json"), C.xv_review(xv_reviews))
        print(f"  XV: audit-report.json rewritten, audit-xv-review.json created")
    else:
        print(f"  XV: all calls failed, primary output unchanged")


# ── Markdown report ──────────────────────────────────────────────────────────
lines = []
lines.append("# 设计审计报告\n")
lines.append("## 摘要\n")
lines.append(f"- 执行模式: full")
lines.append(f"- 可用层: {', '.join(available_layers)}")
lines.append(f"- 逆向追溯: {trace_total} 项检查, {trace_pass} PASS, {len(trace_issues)} ORPHAN")
lines.append(f"- 覆盖洪泛: {coverage_total} 项检查, {coverage_covered} COVERED, {len(coverage_issues)} GAP, 覆盖率 {coverage_rate}")
lines.append(f"- 横向一致性: {cross_total} 项检查, {cross_ok} OK, {report['summary']['cross']['conflict']} CONFLICT, {report['summary']['cross']['warning']} WARNING")
cont_total = len(gate.get("lines", [])) if gate else 0
lines.append(f"- 连续性: {cont_total} 条操作线, {len(continuity_issues)} 条未达标")
lines.append(f"- 信息保真: 追溯完整率 {traceability_rate} ({traceability_status}) · 视角覆盖率 {vp_rate} ({vp_status})\n")

conflicts = [i for i in cross_issues if i["type"] == "CONFLICT"]
orphans = trace_issues
# FIX: gaps[:30] not gaps[:30) — Python uses square brackets for slicing
gaps = coverage_issues
warnings = [i for i in cross_issues if i["type"] == "WARNING"]

if conflicts:
    lines.append("## CONFLICT（跨层矛盾）\n")
    lines.append("| # | 检查项 | 任务 | 说明 |")
    lines.append("|---|--------|------|------|")
    for i, c in enumerate(conflicts, 1):
        lines.append(f"| {i} | {c['check_id']} | {c.get('name', '')} | {c['detail']} |")

if orphans:
    lines.append("\n## ORPHAN（无源头）\n")
    lines.append("| # | 检查项 | 来源层 | 项目 | 说明 |")
    lines.append("|---|--------|--------|------|------|")
    for i, o in enumerate(orphans, 1):
        lines.append(f"| {i} | {o['check_id']} | {o['source']} | {o['item_id']} | {o['detail']} |")

if gaps:
    lines.append("\n## GAP（未覆盖）\n")
    lines.append("| # | 检查项 | 任务 | 缺失层 | 说明 |")
    lines.append("|---|--------|------|--------|------|")
    for i, g in enumerate(gaps[:30], 1):
        lines.append(f"| {i} | {g['check_id']} | {g['name']} | {g['missing_in']} | {g['detail'][:80]} |")
    if len(gaps) > 30:
        lines.append(f"\n... 及另外 {len(gaps) - 30} 个 GAP\n")

if warnings:
    lines.append("\n## WARNING（风险）\n")
    lines.append("| # | 检查项 | 任务 | 说明 |")
    lines.append("|---|--------|------|------|")
    for i, w in enumerate(warnings, 1):
        lines.append(f"| {i} | {w['check_id']} | {w.get('name', '')} | {w['detail']} |")

if continuity_issues:
    lines.append("\n## CONTINUITY（连续性未达标）\n")
    lines.append("| # | 操作线 | 得分 | 问题数 |")
    lines.append("|---|--------|------|--------|")
    for i, ci in enumerate(continuity_issues, 1):
        lines.append(f"| {i} | {ci['line_id']} | {ci['score']} | {len(ci['issues'])} |")

with open(os.path.join(OUT, "audit-report.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

# ── Pipeline decisions ────────────────────────────────────────────────────────
C.append_pipeline_decision(
    BASE,
    "Phase 8 — design-audit",
    f"layers={len(available_layers)}, trace={trace_total}({len(trace_issues)} orphan), "
    f"coverage={coverage_rate}({len(coverage_issues)} gap), "
    f"cross={cross_total}({report['summary']['cross']['conflict']} conflict, "
    f"{report['summary']['cross']['warning']} warning), "
    f"continuity={cont_total}({len(continuity_issues)} failing), "
    f"fidelity={traceability_rate}/{vp_rate}",
    shard=args.get("shard")
)

# ── Summary ───────────────────────────────────────────────────────────────────
print(f"Layers: {available_layers}")
print(f"Trace: {trace_total} checks, {trace_pass} PASS, {len(trace_issues)} ORPHAN")
print(f"Coverage: {coverage_total} checks, {coverage_covered} COVERED, {len(coverage_issues)} GAP, rate={coverage_rate}")
print(f"Cross: {cross_total} checks, {cross_ok} OK, {report['summary']['cross']['conflict']} CONFLICT, {report['summary']['cross']['warning']} WARNING")
print(f"Continuity: {cont_total} lines, {len(continuity_issues)} failing")
print(f"Fidelity: traceability={traceability_rate} ({traceability_status}), viewpoint={vp_rate} ({vp_status})")
print(f"\nAll files written to {OUT}/")
