#!/usr/bin/env python3
"""Generate validation report for product-map Step 7.

Validates the complete product map with completeness scanning,
conflict recheck, and generates validation-report.json + validation-report.md.

Usage:
    python3 gen_validation_report.py <BASE_PATH> [--mode auto] [--shard product-map]
"""

import os
import sys
import re

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
conflict_report = C.load_json(os.path.join(BASE, "product-map/conflict-report.json"))
constraints = C.load_json(os.path.join(BASE, "product-map/constraints.json"))
concept = C.load_product_concept(BASE)

# ── Innovation task helpers ───────────────────────────────────────────────────

def _get_innovation_severity(task):
    """For innovation tasks, map protection_level to severity override.

    Returns None for non-innovation tasks (use normal rules).
    """
    if not task.get("innovation_task"):
        return None
    protection = task.get("protection_level", "experimental")
    return {
        "core": "ERROR",
        "defensible": "WARNING",
        "experimental": "INFO",
    }.get(protection, "INFO")


def _effective_severity(base_severity, task):
    """Apply innovation override if applicable."""
    override = _get_innovation_severity(task)
    if override is not None:
        return override
    return base_severity


# ── Part 1: Completeness Scanning ─────────────────────────────────────────────

issues = []

for tid, task in tasks.items():
    tname = task.get("task_name", task.get("name", ""))
    freq = task.get("frequency", "")
    risk = task.get("risk_level", "")
    is_high_priority = freq == "高" and risk == "高"

    # ── ERROR level: required fields missing ──────────────────────────────

    # MISSING_MAIN_FLOW
    main_flow = task.get("main_flow", [])
    if not main_flow:
        sev = _effective_severity("ERROR", task)
        issues.append({
            "task_id": tid,
            "task_name": tname,
            "severity": sev,
            "flag": "MISSING_MAIN_FLOW",
            "detail": f"任务 {tid} ({tname}) 的 main_flow 为空或缺失"
        })

    # MISSING_OWNER
    if not task.get("owner_role"):
        sev = _effective_severity("ERROR", task)
        issues.append({
            "task_id": tid,
            "task_name": tname,
            "severity": sev,
            "flag": "MISSING_OWNER",
            "detail": f"任务 {tid} ({tname}) 缺少 owner_role"
        })

    # MISSING_PRIORITY
    if not freq or not risk:
        missing_fields = []
        if not freq:
            missing_fields.append("frequency")
        if not risk:
            missing_fields.append("risk_level")
        sev = _effective_severity("ERROR", task)
        issues.append({
            "task_id": tid,
            "task_name": tname,
            "severity": sev,
            "flag": "MISSING_PRIORITY",
            "detail": f"任务 {tid} ({tname}) 缺少 {', '.join(missing_fields)}"
        })

    # ── WARNING level: recommended fields missing (high-freq + high-risk) ─

    if is_high_priority:
        # MISSING_EXCEPTIONS
        if not task.get("exceptions"):
            sev = _effective_severity("WARNING", task)
            issues.append({
                "task_id": tid,
                "task_name": tname,
                "severity": sev,
                "flag": "MISSING_EXCEPTIONS",
                "detail": f"高频高风险任务 {tid} ({tname}) 的 exceptions 为空"
            })

        # THIN_AC
        ac = task.get("acceptance_criteria", [])
        if len(ac) < 3:
            sev = _effective_severity("WARNING", task)
            issues.append({
                "task_id": tid,
                "task_name": tname,
                "severity": sev,
                "flag": "THIN_AC",
                "detail": f"高频高风险任务 {tid} ({tname}) 的 acceptance_criteria 仅 {len(ac)} 条，建议补充到 3 条以上"
            })

        # MISSING_RULES
        if not task.get("rules"):
            sev = _effective_severity("WARNING", task)
            issues.append({
                "task_id": tid,
                "task_name": tname,
                "severity": sev,
                "flag": "MISSING_RULES",
                "detail": f"高频高风险任务 {tid} ({tname}) 的 rules 为空"
            })

    # ── INFO level: recommended fields missing (medium/low-freq tasks) ────

    if not is_high_priority:
        # INFO_MISSING_EXCEPTIONS
        if not task.get("exceptions"):
            sev = _effective_severity("INFO", task)
            issues.append({
                "task_id": tid,
                "task_name": tname,
                "severity": sev,
                "flag": "INFO_MISSING_EXCEPTIONS",
                "detail": f"任务 {tid} ({tname}) 的 exceptions 为空"
            })

        # INFO_THIN_AC
        ac = task.get("acceptance_criteria", [])
        if len(ac) < 3:
            sev = _effective_severity("INFO", task)
            issues.append({
                "task_id": tid,
                "task_name": tname,
                "severity": sev,
                "flag": "INFO_THIN_AC",
                "detail": f"任务 {tid} ({tname}) 的 acceptance_criteria 仅 {len(ac)} 条"
            })

        # INFO_MISSING_VALUE
        if not task.get("value"):
            sev = _effective_severity("INFO", task)
            issues.append({
                "task_id": tid,
                "task_name": tname,
                "severity": sev,
                "flag": "INFO_MISSING_VALUE",
                "detail": f"任务 {tid} ({tname}) 缺少 value 字段"
            })

error_count = sum(1 for i in issues if i["severity"] == "ERROR")
warning_count = sum(1 for i in issues if i["severity"] == "WARNING")
info_count = sum(1 for i in issues if i["severity"] == "INFO")

print(f"Part 1 — Completeness: {error_count} ERROR, {warning_count} WARNING, {info_count} INFO")

# ── Part 2: Conflict Recheck ──────────────────────────────────────────────────

# Contradiction keyword pairs (Chinese business rule patterns)
CONTRADICTION_PAIRS = [
    ("可修改", "不可修改"), ("允许", "禁止"), ("可以", "不可以"),
    ("可编辑", "不可编辑"), ("可删除", "不可删除"), ("可撤销", "不可撤销"),
    ("允许修改", "禁止修改"), ("允许删除", "禁止删除"),
    ("自动", "手动"), ("公开", "私密"), ("必填", "选填"),
    ("实时", "延迟"), ("可重复", "不可重复"),
]

conflicts = []
conflict_counter = [0]


def next_conflict_id():
    conflict_counter[0] += 1
    return f"CR{conflict_counter[0]:03d}"


def _extract_keywords(task):
    """Extract rule/flow keywords for overlap matching."""
    keywords = set()
    for rule in task.get("rules", []):
        # Extract nouns/entities (Chinese 2-4 char words as heuristic)
        words = re.findall(r'[\u4e00-\u9fff]{2,4}', rule)
        keywords.update(words)
    for step in task.get("main_flow", []):
        words = re.findall(r'[\u4e00-\u9fff]{2,4}', step)
        keywords.update(words)
    # Also include entity from name
    tname = task.get("task_name", task.get("name", ""))
    words = re.findall(r'[\u4e00-\u9fff]{2,4}', tname)
    keywords.update(words)
    return keywords


def _rules_text(task):
    """Concatenate all rules into a single string for matching."""
    return " ".join(task.get("rules", []))


def _check_contradictions(rules_a, rules_b):
    """Check if two rule texts contain contradictory keywords."""
    found = []
    for pos, neg in CONTRADICTION_PAIRS:
        if (pos in rules_a and neg in rules_b) or (neg in rules_a and pos in rules_b):
            found.append((pos, neg))
    return found


# Build keyword sets per task for overlap detection
task_keywords = {}
for tid, task in tasks.items():
    task_keywords[tid] = _extract_keywords(task)

task_ids = sorted(tasks.keys())

# 2a: CROSS_ROLE_CONFLICT — different owners, shared objects, contradictory rules
for i, tid_a in enumerate(task_ids):
    task_a = tasks[tid_a]
    role_a = task_a.get("owner_role", "")
    rules_a = _rules_text(task_a)
    if not rules_a:
        continue
    kw_a = task_keywords[tid_a]

    for tid_b in task_ids[i + 1:]:
        task_b = tasks[tid_b]
        role_b = task_b.get("owner_role", "")

        # Must be different roles
        if role_a == role_b:
            continue

        rules_b = _rules_text(task_b)
        if not rules_b:
            continue

        # Must share at least 2 keywords (entity overlap)
        kw_b = task_keywords[tid_b]
        overlap = kw_a & kw_b
        if len(overlap) < 2:
            continue

        # Check for contradictions
        contradictions = _check_contradictions(rules_a, rules_b)
        if contradictions:
            pairs_desc = ", ".join(f"「{p}」vs「{n}」" for p, n in contradictions[:3])
            name_a = task_a.get("task_name", task_a.get("name", tid_a))
            name_b = task_b.get("task_name", task_b.get("name", tid_b))
            conflicts.append({
                "id": next_conflict_id(),
                "type": "CROSS_ROLE_CONFLICT",
                "description": (
                    f"{tid_a} ({name_a}, {role_map.get(role_a, role_a)}) 与 "
                    f"{tid_b} ({name_b}, {role_map.get(role_b, role_b)}) "
                    f"规则矛盾: {pairs_desc}"
                ),
                "affected_tasks": [tid_a, tid_b],
                "severity": "高"
            })

# 2b: STATE_DEADLOCK — flow node[i] outputs state rejected by node[i+1] rules
for flow in flows:
    nodes = C.get_flow_nodes(flow)
    for idx in range(len(nodes) - 1):
        node_cur = nodes[idx] if isinstance(nodes[idx], dict) else {}
        node_nxt = nodes[idx + 1] if isinstance(nodes[idx + 1], dict) else {}

        task_ref_cur = node_cur.get("task_ref", "")
        task_ref_nxt = node_nxt.get("task_ref", "")

        # Strip system prefix if present (e.g. "user-app:T001" → "T001")
        tid_cur = task_ref_cur.split(":")[-1] if ":" in task_ref_cur else task_ref_cur
        tid_nxt = task_ref_nxt.split(":")[-1] if ":" in task_ref_nxt else task_ref_nxt

        task_cur = tasks.get(tid_cur)
        task_nxt = tasks.get(tid_nxt)
        if not task_cur or not task_nxt:
            continue

        # Get output states from current task
        outputs = task_cur.get("outputs", {})
        output_states = outputs.get("states", []) if isinstance(outputs, dict) else []

        # Get rules from next task
        rules_nxt = _rules_text(task_nxt)
        if not rules_nxt or not output_states:
            continue

        # Check if any output state is rejected by next task's rules
        reject_keywords = ["禁止", "不可", "不允许", "拒绝", "不接受"]
        for state in output_states:
            for kw in reject_keywords:
                if state in rules_nxt and kw in rules_nxt:
                    name_cur = task_cur.get("task_name", task_cur.get("name", tid_cur))
                    name_nxt = task_nxt.get("task_name", task_nxt.get("name", tid_nxt))
                    conflicts.append({
                        "id": next_conflict_id(),
                        "type": "STATE_DEADLOCK",
                        "description": (
                            f"业务流 {flow.get('id', '?')} 中，"
                            f"{tid_cur} ({name_cur}) 输出状态「{state}」"
                            f"被 {tid_nxt} ({name_nxt}) 的规则拒绝"
                        ),
                        "affected_tasks": [tid_cur, tid_nxt],
                        "severity": "高"
                    })
                    break  # one match per state is enough

# 2c: IDEMPOTENCY_CONFLICT — tasks on same entity with different retry/repeat rules
idempotency_keywords = ["幂等", "重复", "去重", "重试", "retry", "idempotent", "重入"]


def _has_idempotency_rule(task):
    """Check if task has any idempotency-related rules."""
    rules_text = _rules_text(task)
    return any(kw in rules_text for kw in idempotency_keywords)


def _get_entity_name(task):
    """Extract primary entity from task name (heuristic: object noun)."""
    tname = task.get("task_name", task.get("name", ""))
    # Common pattern: verb + object, extract 2-4 char nouns
    nouns = re.findall(r'[\u4e00-\u9fff]{2,4}', tname)
    # Filter out common verbs
    verbs = {"创建", "提交", "修改", "删除", "审核", "查看", "编辑", "发布",
             "管理", "处理", "配置", "设置", "添加", "新建", "导入", "导出",
             "发起", "取消", "撤销", "确认", "分配"}
    entities = [n for n in nouns if n not in verbs]
    return entities


# Group tasks by entity overlap
entity_task_groups = {}
for tid, task in tasks.items():
    entities = _get_entity_name(task)
    for ent in entities:
        entity_task_groups.setdefault(ent, []).append(tid)

# Check idempotency conflicts within each entity group
checked_pairs = set()
for entity, tids in entity_task_groups.items():
    if len(tids) < 2:
        continue
    for i, tid_a in enumerate(tids):
        task_a = tasks[tid_a]
        has_idemp_a = _has_idempotency_rule(task_a)

        for tid_b in tids[i + 1:]:
            pair = (min(tid_a, tid_b), max(tid_a, tid_b))
            if pair in checked_pairs:
                continue
            checked_pairs.add(pair)

            task_b = tasks[tid_b]
            has_idemp_b = _has_idempotency_rule(task_b)

            # Conflict: one has idempotency rule, the other doesn't,
            # and both operate on same entity with CUD-like operations
            if has_idemp_a != has_idemp_b:
                name_a = task_a.get("task_name", task_a.get("name", tid_a))
                name_b = task_b.get("task_name", task_b.get("name", tid_b))
                has_task = tid_a if has_idemp_a else tid_b
                missing_task = tid_b if has_idemp_a else tid_a
                conflicts.append({
                    "id": next_conflict_id(),
                    "type": "IDEMPOTENCY_CONFLICT",
                    "description": (
                        f"实体「{entity}」上，{has_task} 有幂等/去重规则，"
                        f"但 {missing_task} 缺少相应规则，可能导致重复操作"
                    ),
                    "affected_tasks": [tid_a, tid_b],
                    "severity": "中"
                })

print(f"Part 2 — Conflict recheck: {len(conflicts)} conflicts found")

# ── Part 3: Stats summary ─────────────────────────────────────────────────────
# Competitor diff is skipped in script — requires WebSearch, LLM handles it

total_tasks = len(tasks)

# Completeness score: % of tasks with zero ERROR-level issues
tasks_with_errors = set()
for issue in issues:
    if issue["severity"] == "ERROR":
        tasks_with_errors.add(issue["task_id"])

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
        "conflicts": conflicts
    },
    "competitor_diff": {
        "analysis_status": "script_skipped",
        "note": "Competitor analysis requires WebSearch — run via skill for this part"
    },
    "summary": {
        "total_tasks": total_tasks,
        "error_issues": error_count,
        "warning_issues": warning_count,
        "info_issues": info_count,
        "conflicts_found": len(conflicts),
        "completeness_score": f"{completeness_score}%"
    }
}

C.write_json(os.path.join(OUT, "validation-report.json"), report)

# ── Build Markdown report ─────────────────────────────────────────────────────
md = []
md.append("# 产品地图校验报告\n")
md.append(f"ERROR {error_count} 个 · WARNING {warning_count} 个 · "
          f"INFO {info_count} 个 · 冲突 {len(conflicts)} 个")
md.append(f"完整度: {completeness_score}%（{tasks_complete}/{total_tasks} 任务无 ERROR）\n")

# ERROR issues
md.append("## ERROR 级问题（必须修复）\n")
error_issues = [i for i in issues if i["severity"] == "ERROR"]
if error_issues:
    for i in error_issues:
        md.append(f"- **{i['task_id']}** {i['flag']}: {i['detail']}")
else:
    md.append("无 ERROR 级问题\n")

# WARNING issues
md.append("\n## WARNING 级问题（建议修复）\n")
warning_issues = [i for i in issues if i["severity"] == "WARNING"]
if warning_issues:
    for i in warning_issues:
        md.append(f"- {i['task_id']} {i['flag']}: {i['detail']}")
else:
    md.append("无 WARNING 级问题\n")

# INFO issues (count only)
md.append("\n## INFO 统计\n")
if info_count > 0:
    # Group by flag
    info_by_flag = {}
    for i in issues:
        if i["severity"] == "INFO":
            info_by_flag.setdefault(i["flag"], 0)
            info_by_flag[i["flag"]] += 1
    for flag, count in sorted(info_by_flag.items(), key=lambda x: -x[1]):
        md.append(f"- {flag}: {count} 个任务")
else:
    md.append("无 INFO 级问题\n")

# Conflict recheck
md.append("\n## 冲突复检\n")
if conflicts:
    for c in conflicts:
        md.append(f"- **{c['id']}** {c['type']}（{c['severity']}）: {c['description']}")
else:
    md.append("未发现冲突\n")

# Competitor diff placeholder
md.append("\n## 竞品差异\n")
md.append("竞品分析需要 WebSearch，请通过 skill 运行此部分。\n")

md.append(f"\n> 完整数据见 .allforai/product-map/validation-report.json")

with open(os.path.join(OUT, "validation-report.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(md) + "\n")

# ── Pipeline decisions ────────────────────────────────────────────────────────
C.append_pipeline_decision(
    BASE,
    "Phase 2 Step 7 — validation",
    f"errors={error_count}, warnings={warning_count}, infos={info_count}, "
    f"conflicts={len(conflicts)}, completeness={completeness_score}%",
    shard=args.get("shard")
)

# ── Summary ───────────────────────────────────────────────────────────────────
print(f"Completeness score: {completeness_score}%")
print(f"  ERROR: {error_count}, WARNING: {warning_count}, INFO: {info_count}")
print(f"Conflicts: {len(conflicts)}")
for c in conflicts:
    print(f"  {c['id']} {c['type']}: {c['description'][:80]}")
print(f"\nFiles written to {OUT}/")
print(f"  validation-report.json")
print(f"  validation-report.md")
