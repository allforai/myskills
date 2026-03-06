#!/usr/bin/env python3
"""Aggregation checkpoint: merge shards + detect cross-skill conflicts.

Detection only — conflict resolution is handled by the orchestrating skill.

Steps:
1. Merge pipeline-decisions-*.json shards → pipeline-decisions.json (dedup, delete shards)
2. Cross-skill conflict detection:
   - use-case coverage gaps
   - gap×prune contradictions (task has gaps but marked CUT)
   - UI CORE coverage (CORE task name missing from ui-design-spec.md)
   - Safety violations (high-freq CUT + business-flow ref)
3. Output aggregate-checkpoint.json with all findings

Usage:
    python3 gen_aggregate_checkpoint.py <BASE_PATH> [--mode auto]
"""

import os
import sys
import glob as globmod

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C

# ── Setup ─────────────────────────────────────────────────────────────────────
BASE, args = C.parse_args()
NOW = C.now_iso()

findings = []  # list of {check, severity, detail, task_ids}

# ── Step 1: Merge pipeline-decisions shards ──────────────────────────────────
shard_pattern = os.path.join(BASE, "pipeline-decisions-*.json")
shard_files = sorted(globmod.glob(shard_pattern))

main_path = os.path.join(BASE, "pipeline-decisions.json")
main_decisions = C.load_json(main_path) or []

merged_count = 0
for sf in shard_files:
    shard_data = C.load_json(sf)
    if not shard_data or not isinstance(shard_data, list):
        continue
    for entry in shard_data:
        phase = entry.get("phase", "")
        main_decisions = [d for d in main_decisions if d.get("phase") != phase]
        main_decisions.append(entry)
        merged_count += 1

if shard_files:
    C.write_json(main_path, main_decisions)
    for sf in shard_files:
        try:
            os.remove(sf)
        except OSError:
            pass
    print(f"  Merged {merged_count} entries from {len(shard_files)} shards")
else:
    print(f"  No shard files found")

# ── Load data ────────────────────────────────────────────────────────────────
tasks = C.load_task_inventory(BASE)
flows = C.load_business_flows(BASE)
flow_task_refs = C.collect_flow_task_refs(flows)

uc = C.load_json(os.path.join(BASE, "use-case/use-case-tree.json"))
gap_tasks = C.load_json(os.path.join(BASE, "feature-gap/gap-tasks.json"))
prune_decisions = C.load_json(os.path.join(BASE, "feature-prune/prune-decisions.json"))

ui_spec_path = os.path.join(BASE, "ui-design/ui-design-spec.md")
ui_spec_text = ""
if os.path.exists(ui_spec_path):
    with open(ui_spec_path, encoding="utf-8") as f:
        ui_spec_text = f.read()

# Build prune index
prune_by_tid = {}
if prune_decisions:
    for d in prune_decisions:
        tid = d.get("task_id", d.get("item_id"))
        prune_by_tid[tid] = d

# ── Check 1: Use-case coverage ───────────────────────────────────────────────
uc_covered = set()
if uc:
    for role in uc.get("roles", []):
        for fa in role.get("feature_areas", []):
            for t_data in fa.get("tasks", []):
                uc_covered.add(t_data["id"])

uc_missing = [tid for tid in tasks if tid not in uc_covered]
if uc_missing:
    findings.append({
        "check": "use-case-coverage",
        "severity": "WARNING",
        "detail": f"{len(uc_missing)} tasks without use cases",
        "task_ids": uc_missing,
    })
    print(f"  WARNING: {len(uc_missing)} tasks without use cases")
else:
    print(f"  PASS: use-case coverage ({len(tasks)} tasks)")

# ── Check 2: Gap×prune contradictions ────────────────────────────────────────
if gap_tasks and prune_decisions:
    gap_affected = set()
    for g in gap_tasks:
        for tid in g.get("affected_tasks", []):
            gap_affected.add(tid)

    contradictions = []
    for tid in sorted(gap_affected):
        d = prune_by_tid.get(tid)
        if d and d["decision"] == "CUT":
            task = tasks.get(tid, {})
            contradictions.append({
                "task_id": tid,
                "name": task.get("name", ""),
                "frequency": task.get("frequency", ""),
                "category": task.get("category", ""),
                "risk_level": task.get("risk_level", ""),
                "in_flow": tid in flow_task_refs,
            })

    if contradictions:
        findings.append({
            "check": "gap-prune-contradiction",
            "severity": "CONFLICT",
            "detail": f"{len(contradictions)} tasks have gaps but marked CUT",
            "tasks": contradictions,
        })
        print(f"  CONFLICT: {len(contradictions)} gap×prune contradictions")
    else:
        print(f"  PASS: gap×prune consistency")

# ── Check 3: Safety — high-freq CUT + flow ref ──────────────────────────────
if prune_decisions:
    safety_violations = []
    for tid, task in tasks.items():
        d = prune_by_tid.get(tid)
        if not d or d["decision"] != "CUT":
            continue
        if task.get("frequency") == "高" and tid in flow_task_refs:
            safety_violations.append({
                "task_id": tid,
                "name": task.get("name", ""),
                "category": task.get("category", ""),
            })

    if safety_violations:
        findings.append({
            "check": "safety-highfreq-cut-flow",
            "severity": "ERROR",
            "detail": f"{len(safety_violations)} high-freq tasks CUT but referenced by business flow",
            "tasks": safety_violations,
        })
        print(f"  ERROR: {len(safety_violations)} safety violations (high-freq CUT + flow ref)")

# ── Check 4: UI CORE coverage ───────────────────────────────────────────────
if prune_decisions and ui_spec_text:
    core_tasks = []
    for d in prune_decisions:
        if d["decision"] == "CORE":
            tid = d.get("task_id", d.get("item_id"))
            core_tasks.append((tid, d.get("item_name", "")))

    ui_missing = [(tid, tname) for tid, tname in core_tasks
                  if tname and tname not in ui_spec_text]
    if ui_missing:
        rate = (len(core_tasks) - len(ui_missing)) / len(core_tasks) * 100 if core_tasks else 0
        findings.append({
            "check": "ui-core-coverage",
            "severity": "WARNING",
            "detail": f"{len(ui_missing)}/{len(core_tasks)} CORE tasks not in ui-design-spec.md ({rate:.0f}% coverage)",
            "task_ids": [tid for tid, _ in ui_missing],
        })
        print(f"  WARNING: UI CORE coverage {rate:.0f}%")
    else:
        print(f"  PASS: UI CORE coverage ({len(core_tasks)} tasks)")

# ── Output ───────────────────────────────────────────────────────────────────
has_error = any(f["severity"] == "ERROR" for f in findings)
has_conflict = any(f["severity"] == "CONFLICT" for f in findings)
status = "ERROR" if has_error else ("CONFLICT" if has_conflict else
         ("WARNING" if findings else "PASS"))

checkpoint = {
    "generated_at": NOW,
    "shards_merged": len(shard_files),
    "entries_merged": merged_count,
    "findings": findings,
    "status": status,
}

C.write_json(os.path.join(BASE, "aggregate-checkpoint.json"), checkpoint)

print(f"\nAggregate checkpoint: {status}")
print(f"  Output: {os.path.join(BASE, 'aggregate-checkpoint.json')}")

# Exit code: 0=PASS/WARNING, 1=CONFLICT/ERROR (needs skill-level resolution)
if has_error or has_conflict:
    sys.exit(1)
