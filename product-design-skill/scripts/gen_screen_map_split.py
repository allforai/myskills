#!/usr/bin/env python3
"""Generate per-role split files from screen-map.json.

Reads screen-map.json + task-inventory.json, maps each screen to owner roles
via screen.tasks[], and writes screen-map-{RID}.json per role.

Usage:
    python3 gen_screen_map_split.py <BASE_PATH>
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C

# ── Setup ─────────────────────────────────────────────────────────────────────
BASE = C.resolve_base_path()

# ── Load data ─────────────────────────────────────────────────────────────────
tasks_by_id = C.load_task_inventory(BASE)
role_map = C.load_role_profiles(BASE)
screens, loaded = C.load_screen_map(BASE)

if not loaded:
    print("ERROR: screen-map.json not found", file=sys.stderr)
    sys.exit(1)

# ── Build task_id → owner_role mapping ────────────────────────────────────────
task_role = {tid: t["owner_role"] for tid, t in tasks_by_id.items()}

# ── Assign screens to role buckets ────────────────────────────────────────────
role_screens = {}  # role_id -> list of screens

for screen in screens:
    assigned_roles = set()
    for tid in C.get_screen_tasks(screen):
        rid = task_role.get(tid)
        if rid:
            assigned_roles.add(rid)
    if not assigned_roles:
        # Orphan screen — skip (no role assignment possible)
        continue
    for rid in assigned_roles:
        role_screens.setdefault(rid, []).append(screen)

# ── Write split files ─────────────────────────────────────────────────────────
splits = {}
for rid in sorted(role_screens.keys()):
    rname = role_map.get(rid, rid)
    splits[rid] = {
        "label": rname,
        "description": f"角色 {rid}（{rname}）关联的界面子集",
        "items": role_screens[rid],
    }

written = C.write_split_files(BASE, "screen-map", "screen-map", "role", splits)

# ── Summary ───────────────────────────────────────────────────────────────────
total_assigned = sum(len(s) for s in role_screens.values())
print(f"Screen-map split by role: {len(splits)} files")
for rid in sorted(role_screens.keys()):
    rname = role_map.get(rid, rid)
    print(f"  {rid} ({rname}): {len(role_screens[rid])} screens")
print(f"Total screen assignments: {total_assigned} (screens may appear in multiple roles)")
print(f"Original screen count: {len(screens)}")
for p in written:
    print(f"  Written: {p}")
