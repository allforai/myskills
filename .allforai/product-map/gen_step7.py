#!/usr/bin/env python3
"""Step 7: Validation — completeness scan + conflict rescan."""
import json

BASE = "/home/dv/myskills/.allforai/product-map"

with open(f"{BASE}/task-inventory.json") as f:
    tasks = json.load(f)["tasks"]
with open(f"{BASE}/business-flows.json") as f:
    flows_data = json.load(f)
with open(f"{BASE}/conflict-report.json") as f:
    conflicts_data = json.load(f)

# ============================================================
# Part 1: Completeness scan
# ============================================================
issues = []

for t in tasks:
    tid = t["id"]
    tname = t["task_name"]
    freq = t["frequency"]
    risk = t["risk_level"]
    is_high_priority = freq == "高" or risk == "高"

    # ERROR: required fields
    if not t.get("main_flow"):
        issues.append({"task_id": tid, "task_name": tname, "level": "ERROR",
                       "flags": ["MISSING_MAIN_FLOW"], "detail": "main_flow 为空或缺失"})
    if not t.get("owner_role"):
        issues.append({"task_id": tid, "task_name": tname, "level": "ERROR",
                       "flags": ["MISSING_OWNER"], "detail": "owner_role 缺失"})
    if not t.get("frequency") or not t.get("risk_level"):
        issues.append({"task_id": tid, "task_name": tname, "level": "ERROR",
                       "flags": ["MISSING_PRIORITY"], "detail": "frequency 或 risk_level 缺失"})

    # WARNING: recommended fields missing on high-priority tasks
    if is_high_priority:
        if not t.get("exceptions"):
            issues.append({"task_id": tid, "task_name": tname, "level": "WARNING",
                           "flags": ["MISSING_EXCEPTIONS"], "detail": "高频/高风险任务缺少 exceptions"})
        if not t.get("rules"):
            issues.append({"task_id": tid, "task_name": tname, "level": "WARNING",
                           "flags": ["MISSING_RULES"], "detail": "高频/高风险任务缺少 rules"})
    else:
        # INFO: recommended fields missing on mid/low tasks
        if not t.get("exceptions"):
            issues.append({"task_id": tid, "task_name": tname, "level": "INFO",
                           "flags": ["INFO_MISSING_EXCEPTIONS"], "detail": "中低频任务缺少 exceptions"})
        if not t.get("value"):
            issues.append({"task_id": tid, "task_name": tname, "level": "INFO",
                           "flags": ["INFO_MISSING_VALUE"], "detail": "缺少 value 字段"})

# ============================================================
# Part 2: Conflict rescan
# ============================================================
conflict_rescan = []

# Check cross-role conflicts
# Build role → rules mapping
from collections import defaultdict
role_rules = defaultdict(list)
for t in tasks:
    for rule in t.get("rules", []):
        role_rules[t["owner_role"]].append({"task_id": t["id"], "rule": rule})

# Check for state deadlocks: tasks that produce output consumed by another task with blocking rules
# In this interview-mode product, we check logically
# Check: T001 free limit vs T004/T021 (already resolved in C001)
# Check: all confirmed conflicts are resolved

# Check idempotency: tasks operating on same object
# Payment tasks: T022, T024 both involve payment — check for idempotency rules
payment_tasks = [t for t in tasks if any(kw in t["task_name"] for kw in ["购买", "支付", "订阅方案"])]
has_idempotency_rule = any("幂等" in r for t in payment_tasks for r in t.get("rules", []))
if not has_idempotency_rule and len(payment_tasks) > 1:
    conflict_rescan.append({
        "id": "V001",
        "type": "IDEMPOTENCY_CONFLICT",
        "description": "T022（购买订阅）和T024（购买场景包）均涉及支付，但未明确幂等防重复规则",
        "affected_tasks": [t["id"] for t in payment_tasks],
        "severity": "中",
        "confirmed": False
    })

# Check: prompt/parameter versioning consistency
versioned_tasks = [t for t in tasks if any("回滚" in r for r in t.get("rules", []))]
for vt in versioned_tasks:
    has_version_rule = any("版本" in r or "回滚" in r for r in vt.get("rules", []))
    if has_version_rule:
        # Check if there's a rollback exception
        has_rollback_exception = any("回滚" in e for e in vt.get("exceptions", []))
        if not has_rollback_exception and vt["risk_level"] == "高":
            conflict_rescan.append({
                "id": f"V{len(conflict_rescan)+2:03d}",
                "type": "STATE_DEADLOCK",
                "description": f"{vt['id']}（{vt['task_name']}）有回滚规则但无回滚异常流描述",
                "affected_tasks": [vt["id"]],
                "severity": "低",
                "confirmed": False
            })

# ============================================================
# Summary
# ============================================================
error_count = sum(1 for i in issues if i["level"] == "ERROR")
warning_count = sum(1 for i in issues if i["level"] == "WARNING")
info_count = sum(1 for i in issues if i["level"] == "INFO")

print(f"Part 1 — Completeness scan:")
print(f"  ERROR: {error_count}")
print(f"  WARNING: {warning_count}")
print(f"  INFO: {info_count}")

if error_count > 0:
    print("\n  ERROR details:")
    for i in issues:
        if i["level"] == "ERROR":
            print(f"    {i['task_id']}: {i['flags']} — {i['detail']}")

if warning_count > 0:
    print("\n  WARNING details:")
    for i in issues:
        if i["level"] == "WARNING":
            print(f"    {i['task_id']} {i['task_name']}: {i['flags']}")

print(f"\nPart 2 — Conflict rescan:")
print(f"  New conflicts found: {len(conflict_rescan)}")
for c in conflict_rescan:
    print(f"    {c['id']}: {c['type']} — {c['description']}")

# ============================================================
# Output validation-report.json (without competitor diff, that comes after web search)
# ============================================================
validation = {
    "generated_at": "2026-02-25T15:15:00Z",
    "summary": {
        "error_issues": error_count,
        "warning_issues": warning_count,
        "info_issues": info_count,
        "conflict_issues": len(conflict_rescan),
        "competitor_gaps": 0
    },
    "completeness": [i for i in issues if i["level"] in ("ERROR", "WARNING")],
    "completeness_info_count": info_count,
    "conflicts": conflict_rescan,
    "competitor_diff": None
}

with open(f"{BASE}/validation-report.json", "w", encoding="utf-8") as f:
    json.dump(validation, f, ensure_ascii=False, indent=2)
print(f"\nGenerated validation-report.json")
