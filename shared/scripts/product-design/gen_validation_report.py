#!/usr/bin/env python3
# Skeleton generator — LLM enrichment required after running
"""Generate validation report for product-map.

Skeleton generator: structural validation only (file exists, required fields
present, ID references valid). No keyword-based contradiction detection or
semantic overlap analysis.

Usage:
    python3 gen_validation_report.py <BASE_PATH> [--mode auto] [--shard <name>]
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C

# ── Setup ─────────────────────────────────────────────────────────────────────
BASE, args = C.parse_args()
OUT = os.path.join(BASE, "product-map")
C.ensure_dir(OUT)
NOW = C.now_iso()

# ── Load data ─────────────────────────────────────────────────────────────────
tasks = C.load_task_inventory(BASE)
role_map = C.load_role_profiles(BASE)
flows = C.load_business_flows(BASE)

# ── Part 1: Structural Completeness ─────────────────────────────────────────

issues = []

for tid, task in tasks.items():
    tname = task.get("task_name", task.get("name", ""))
    freq = task.get("frequency", "")
    risk = task.get("risk_level", "")
    is_high_priority = freq == "高" and risk == "高"

    # ERROR: required fields missing
    if not task.get("main_flow"):
        issues.append({
            "task_id": tid, "task_name": tname, "severity": "ERROR",
            "flag": "MISSING_MAIN_FLOW",
            "detail": f"任务 {tid} ({tname}) 的 main_flow 为空或缺失"
        })

    if not task.get("owner_role"):
        issues.append({
            "task_id": tid, "task_name": tname, "severity": "ERROR",
            "flag": "MISSING_OWNER",
            "detail": f"任务 {tid} ({tname}) 缺少 owner_role"
        })

    if not freq or not risk:
        missing_fields = []
        if not freq:
            missing_fields.append("frequency")
        if not risk:
            missing_fields.append("risk_level")
        issues.append({
            "task_id": tid, "task_name": tname, "severity": "ERROR",
            "flag": "MISSING_PRIORITY",
            "detail": f"任务 {tid} ({tname}) 缺少 {', '.join(missing_fields)}"
        })

    # WARNING: high-priority tasks missing recommended fields
    if is_high_priority:
        if not task.get("exceptions"):
            issues.append({
                "task_id": tid, "task_name": tname, "severity": "WARNING",
                "flag": "MISSING_EXCEPTIONS",
                "detail": f"高频高风险任务 {tid} ({tname}) 的 exceptions 为空"
            })
        ac = task.get("acceptance_criteria", [])
        if len(ac) < 3:
            issues.append({
                "task_id": tid, "task_name": tname, "severity": "WARNING",
                "flag": "THIN_AC",
                "detail": f"高频高风险任务 {tid} ({tname}) 的 acceptance_criteria 仅 {len(ac)} 条"
            })
        if not task.get("rules"):
            issues.append({
                "task_id": tid, "task_name": tname, "severity": "WARNING",
                "flag": "MISSING_RULES",
                "detail": f"高频高风险任务 {tid} ({tname}) 的 rules 为空"
            })

    # INFO: non-high-priority missing recommended fields
    if not is_high_priority:
        if not task.get("exceptions"):
            issues.append({
                "task_id": tid, "task_name": tname, "severity": "INFO",
                "flag": "INFO_MISSING_EXCEPTIONS",
                "detail": f"任务 {tid} ({tname}) 的 exceptions 为空"
            })
        ac = task.get("acceptance_criteria", [])
        if len(ac) < 3:
            issues.append({
                "task_id": tid, "task_name": tname, "severity": "INFO",
                "flag": "INFO_THIN_AC",
                "detail": f"任务 {tid} ({tname}) 的 acceptance_criteria 仅 {len(ac)} 条"
            })

# ── Part 2: ID Reference Validation ─────────────────────────────────────────

ref_issues = []

# Validate role references in tasks
valid_roles = set(role_map.keys())
for tid, task in tasks.items():
    role_id = task.get("owner_role", "")
    if role_id and role_id not in valid_roles:
        ref_issues.append({
            "task_id": tid, "task_name": task.get("task_name", ""),
            "severity": "ERROR", "flag": "INVALID_ROLE_REF",
            "detail": f"任务 {tid} 引用不存在的角色 {role_id}"
        })

# Validate task references in flows
valid_tasks = set(tasks.keys())
for flow in flows:
    fid = flow.get("id") or flow.get("flow_id", "")
    for node in C.get_flow_nodes(flow):
        if isinstance(node, dict):
            task_ref = node.get("task_ref", "")
        elif isinstance(node, str):
            task_ref = node
        else:
            continue
        # Strip system prefix
        clean_ref = task_ref.split(":")[-1] if ":" in task_ref else task_ref
        if clean_ref and clean_ref not in valid_tasks:
            ref_issues.append({
                "task_id": clean_ref, "task_name": "",
                "severity": "ERROR", "flag": "INVALID_TASK_REF_IN_FLOW",
                "detail": f"业务流 {fid} 引用不存在的任务 {clean_ref}"
            })

issues.extend(ref_issues)

error_count = sum(1 for i in issues if i["severity"] == "ERROR")
warning_count = sum(1 for i in issues if i["severity"] == "WARNING")
info_count = sum(1 for i in issues if i["severity"] == "INFO")

print(f"Part 1 — Completeness: {error_count} ERROR, {warning_count} WARNING, {info_count} INFO")

# ── Part 3: Stats summary ───────────────────────────────────────────────────

total_tasks = len(tasks)
tasks_with_errors = {i["task_id"] for i in issues if i["severity"] == "ERROR"}
tasks_complete = total_tasks - len(tasks_with_errors)
completeness_score = round((tasks_complete / total_tasks * 100) if total_tasks > 0 else 100, 1)

# ── Build output JSON ─────────────────────────────────────────────────────────
report = {
    "generated_at": NOW,
    "completeness": {
        "error_count": error_count,
        "warning_count": warning_count,
        "info_count": info_count,
        "issues": issues
    },
    "conflict_recheck": {
        "conflicts": [],
        "note": "骨架输出 — 语义冲突检测需 LLM 分析"
    },
    "summary": {
        "total_tasks": total_tasks,
        "error_issues": error_count,
        "warning_issues": warning_count,
        "info_issues": info_count,
        "conflicts_found": 0,
        "completeness_score": f"{completeness_score}%",
        "note": "Skeleton — structural validation only, LLM enrichment needed for semantic checks"
    }
}

C.write_json(os.path.join(OUT, "validation-report.json"), report)

# ── Build Markdown report ─────────────────────────────────────────────────────
md = []
md.append("# 产品地图校验报告（骨架）\n")
md.append("> **骨架输出** — 仅结构性校验，语义冲突检测需 LLM 补充\n")
md.append(f"ERROR {error_count} 个 · WARNING {warning_count} 个 · INFO {info_count} 个")
md.append(f"完整度: {completeness_score}%（{tasks_complete}/{total_tasks} 任务无 ERROR）\n")

md.append("## ERROR 级问题（必须修复）\n")
error_issues = [i for i in issues if i["severity"] == "ERROR"]
if error_issues:
    for i in error_issues:
        md.append(f"- **{i['task_id']}** {i['flag']}: {i['detail']}")
else:
    md.append("无 ERROR 级问题\n")

md.append("\n## WARNING 级问题（建议修复）\n")
warning_issues = [i for i in issues if i["severity"] == "WARNING"]
if warning_issues:
    for i in warning_issues:
        md.append(f"- {i['task_id']} {i['flag']}: {i['detail']}")
else:
    md.append("无 WARNING 级问题\n")

md.append("\n## INFO 统计\n")
if info_count > 0:
    info_by_flag = {}
    for i in issues:
        if i["severity"] == "INFO":
            info_by_flag.setdefault(i["flag"], 0)
            info_by_flag[i["flag"]] += 1
    for flag, count in sorted(info_by_flag.items(), key=lambda x: -x[1]):
        md.append(f"- {flag}: {count} 个任务")
else:
    md.append("无 INFO 级问题\n")

md.append("\n## 冲突复检\n")
md.append("骨架输出 — 语义冲突检测需 LLM 分析\n")

md.append(f"\n> 完整数据见 .allforai/product-map/validation-report.json")

with open(os.path.join(OUT, "validation-report.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(md) + "\n")

# ── Pipeline decisions ────────────────────────────────────────────────────────
C.append_pipeline_decision(
    BASE,
    "Phase 2 Step 7 — validation",
    f"errors={error_count}, warnings={warning_count}, infos={info_count}, "
    f"completeness={completeness_score}% (skeleton — structural only)",
    shard=args.get("shard")
)

# ── Summary ───────────────────────────────────────────────────────────────────
print(f"Completeness score: {completeness_score}%")
print(f"  ERROR: {error_count}, WARNING: {warning_count}, INFO: {info_count}")
print(f"  Reference issues: {len(ref_issues)}")
print(f"\nFiles written to {OUT}/")
print(f"  validation-report.json")
print(f"  validation-report.md")
