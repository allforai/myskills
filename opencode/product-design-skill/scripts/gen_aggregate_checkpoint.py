#!/usr/bin/env python3
"""Aggregation checkpoint: merge shards + detect cross-skill conflicts.

Detection only — conflict resolution is handled by the orchestrating skill.

Steps:
1. Merge pipeline-decisions-*.json shards → pipeline-decisions.json (dedup, delete shards)
2. Cross-skill conflict detection:
   - use-case coverage gaps
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

# ── Check 1: Use-case coverage ───────────────────────────────────────────────
uc_covered = set()
if uc:
    # v2.5.0+ flat format
    flat_ucs = uc.get("use_cases")
    if flat_ucs and isinstance(flat_ucs, list):
        for ucase in flat_ucs:
            tid = ucase.get("task_id", "")
            if tid:
                uc_covered.add(tid)
    else:
        # Legacy nested format
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
