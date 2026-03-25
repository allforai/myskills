#!/usr/bin/env python3
"""Step 8: Generate CRUD-aware View Objects from entity-model + task-inventory.

Creates multiple VOs per entity based on task operations:
- list VO (CT1/MG2-L) for browsing tasks
- detail VO (CT2/MG1) for viewing tasks
- create_form VO (MG2-C) for creation tasks
- edit_form VO (MG2-E) for editing tasks
- state_action VO (MG3) for state management tasks

Each VO gets fields filtered by view_type (list shows summary fields,
create_form shows writable fields, etc.) and actions derived from tasks.

Usage:
    python3 gen_view_objects.py <BASE_PATH> [--mode auto] [--shard product-map]
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C

# ── Display format mapping ───────────────────────────────────────────────────
DISPLAY_FORMATS = {
    "enum": "status_badge",
    "datetime": "relative_time",
    "integer": "number",
    "file": "thumbnail",
    "file[]": "thumbnail_group",
    "boolean": "toggle",
    "json": "code_block",
    "text": "multiline",
    "string[]": "tag_list",
}

# Decimal fields need context-aware format — not all decimals are currency
DECIMAL_FORMAT_PATTERNS = {
    "price": "currency",
    "amount": "currency",
    "cost": "currency",
    "fee": "currency",
    "progress": "percentage",
    "rate": "percentage",
    "ratio": "percentage",
    "completion": "percentage",
    "score": "rating",
    "rating": "rating",
}

# ── View type → interaction type mapping ─────────────────────────────────────
VIEW_TYPE_ITYPE = {
    "list_item": {"consumer": "CT1", "professional": "MG2-L"},
    "detail": {"consumer": "CT2", "professional": "MG1"},
    "create_form": {"consumer": "MG2-C", "professional": "MG2-C"},
    "edit_form": {"consumer": "MG8", "professional": "MG2-E"},
    "state_action": {"consumer": "MG3", "professional": "MG3"},
}

# Fields to exclude from list views (too verbose)
LIST_EXCLUDE = {"content", "config_json", "audio_url", "video_url"}
# Additional fields to exclude from consumer list views
CONSUMER_LIST_EXCLUDE = {"id", "version", "creator_id"}
# Fields to exclude from create/edit forms (auto-managed)
FORM_EXCLUDE = {"id", "created_at", "updated_at", "creator_id"}
# Fields always shown in list (summary)
LIST_PRIORITY = {"title", "name", "status", "category", "difficulty_level", "language", "score", "cover_image"}

# ── Setup ────────────────────────────────────────────────────────────────────
BASE, args = C.parse_args()
OUT = os.path.join(BASE, "product-map")
C.ensure_dir(OUT)
NOW = C.now_iso()

# ── Load inputs ──────────────────────────────────────────────────────────────
entities, relationships = C.load_entity_model(BASE)
tasks = C.load_task_inventory(BASE)

roles_data = C.load_json(os.path.join(BASE, "product-map/role-profiles.json"))
role_map = {}
audience_map = {}  # role_id → audience_type
if roles_data and "roles" in roles_data:
    for r in roles_data["roles"]:
        role_map[r["id"]] = r.get("name", r["id"])
        atype = r.get("audience_type", "")
        if not atype:
            atype = "professional" if r.get("role_type") == "producer" else "consumer"
        audience_map[r["id"]] = atype

# Build module → tasks mapping
module_tasks = {}
for tid, task in tasks.items():
    module = task.get("module", "unknown")
    module_tasks.setdefault(module, []).append({**task, "_id": tid})

# Build entity_name → entity lookup
entity_by_name = {e["name"]: e for e in entities}


def _build_field_entry(f, read_only=True):
    """Create a VO field entry from an entity field."""
    entry = {
        "name": f["name"],
        "type": f["type"],
        "read_only": read_only,
    }
    # Context-aware display format for decimal fields
    if f["type"] == "decimal":
        fname = f["name"].lower()
        fmt = "number"  # default for decimal
        for pattern, dfmt in DECIMAL_FORMAT_PATTERNS.items():
            if pattern in fname:
                fmt = dfmt
                break
        entry["display_format"] = fmt
    else:
        fmt = DISPLAY_FORMATS.get(f["type"])
        if fmt:
            entry["display_format"] = fmt
    if f.get("label"):
        entry["label"] = f["label"]
    if f.get("constraints"):
        if "not_null" in f["constraints"]:
            entry["required"] = True
    return entry


def _task_actions(task_list, entity_name):
    """Derive VO actions from a list of tasks."""
    actions = []
    seen = set()
    for t in task_list:
        itype, crud = C.infer_interaction_type(t, audience_type=audience_map.get(t.get("owner_role", ""), ""))
        action_name = t.get("name", "")
        if action_name in seen:
            continue
        seen.add(action_name)
        action = {
            "label": action_name,
            "task_ref": t.get("_id", t.get("id", "")),
            "crud": crud,
        }
        # Infer action type from CRUD
        if crud == "C":
            action["type"] = "create"
        elif crud == "U":
            action["type"] = "update"
        elif crud == "D":
            action["type"] = "delete"
        else:
            action["type"] = "navigate"
        actions.append(action)
    return actions


# ── Generate VOs per entity ──────────────────────────────────────────────────
all_vos = []
vo_counter = 0

for entity in entities:
    eid = entity["id"]
    ename = entity["name"]
    e_fields = entity.get("fields", [])
    mod_tasks_list = module_tasks.get(ename, [])

    if not mod_tasks_list:
        # No tasks for this entity → single detail VO
        vo_counter += 1
        all_vos.append({
            "id": f"VO{vo_counter:03d}",
            "entity_ref": eid,
            "entity_name": ename,
            "view_type": "detail",
            "interaction_type": "MG1",
            "fields": [_build_field_entry(f) for f in e_fields],
            "actions": [],
        })
        continue

    # Determine primary audience type for this module's tasks
    audience_counts = {}
    for t in mod_tasks_list:
        at = audience_map.get(t.get("owner_role", ""), "consumer")
        audience_counts[at] = audience_counts.get(at, 0) + 1
    primary_audience = max(audience_counts, key=audience_counts.get)

    # Classify tasks by their inferred CRUD operation
    crud_groups = {"R": [], "C": [], "U": [], "D": []}
    for t in mod_tasks_list:
        _, crud = C.infer_interaction_type(t, audience_type=audience_map.get(t.get("owner_role", ""), ""))
        crud_groups[crud].append(t)

    # Determine which VOs to create based on CRUD presence
    vo_specs = []

    # Always create a list VO if there are Read tasks
    if crud_groups["R"]:
        vo_specs.append(("list_item", crud_groups["R"]))

    # Always create a detail VO (needed for navigation from list)
    vo_specs.append(("detail", crud_groups["R"] or mod_tasks_list))

    # Create form VO if there are Create tasks
    if crud_groups["C"]:
        vo_specs.append(("create_form", crud_groups["C"]))

    # Edit form VO if there are Update tasks
    if crud_groups["U"]:
        vo_specs.append(("edit_form", crud_groups["U"]))

    # State action VO if there are state management tasks
    state_tasks = [t for t in mod_tasks_list
                   if C.infer_interaction_type(t, audience_type=audience_map.get(t.get("owner_role", ""), ""))[0] == "MG3"]
    if state_tasks:
        vo_specs.append(("state_action", state_tasks))

    # Deduplicate view_types
    seen_types = set()
    for view_type, related_tasks in vo_specs:
        if view_type in seen_types:
            continue
        seen_types.add(view_type)
        vo_counter += 1

        # Select interaction_type based on view_type + audience
        itype_map = VIEW_TYPE_ITYPE.get(view_type, {})
        interaction_type = itype_map.get(primary_audience, "MG1")

        # Filter fields by view_type
        if view_type == "list_item":
            # Show summary fields only
            fields = []
            for f in e_fields:
                if f["name"] in LIST_EXCLUDE:
                    continue
                if f["name"] in FORM_EXCLUDE and f["name"] != "id":
                    continue
                # Exclude ID and config fields from consumer list views
                if primary_audience == "consumer" and f["name"] in CONSUMER_LIST_EXCLUDE:
                    continue
                if "config" in f.get("constraints", []):
                    continue
                fields.append(_build_field_entry(f, read_only=True))
        elif view_type in ("create_form", "edit_form"):
            # Show writable fields only — exclude config_items (system-level params)
            fields = []
            for f in e_fields:
                if f["name"] in FORM_EXCLUDE:
                    continue
                if "config" in f.get("constraints", []):
                    continue
                # Exclude status from create forms (auto-set on creation)
                if view_type == "create_form" and f["name"] == "status":
                    continue
                read_only = f["name"] in ("id",) or "auto" in f.get("constraints", [])
                fields.append(_build_field_entry(f, read_only=read_only))
        elif view_type == "state_action":
            # Show status + key identifier fields
            fields = []
            for f in e_fields:
                if f["name"] in ("status", "title", "name", "id", "progress"):
                    fields.append(_build_field_entry(f, read_only=f["name"] != "status"))
                elif f["type"] == "enum":
                    fields.append(_build_field_entry(f, read_only=False))
            if not fields:
                fields = [_build_field_entry(f) for f in e_fields[:4]]
        else:
            # detail: all fields
            fields = [_build_field_entry(f) for f in e_fields]

        vo = {
            "id": f"VO{vo_counter:03d}",
            "entity_ref": eid,
            "entity_name": ename,
            "view_type": view_type,
            "interaction_type": interaction_type,
            "fields": fields,
            "actions": _task_actions(related_tasks, ename),
            "task_refs": [t.get("_id", t.get("id", "")) for t in related_tasks],
        }
        all_vos.append(vo)

# ── Build type distribution ──────────────────────────────────────────────────
type_dist = {}
itype_dist = {}
for vo in all_vos:
    vtype = vo["view_type"]
    type_dist[vtype] = type_dist.get(vtype, 0) + 1
    itype = vo["interaction_type"]
    itype_dist[itype] = itype_dist.get(itype, 0) + 1

# ── Write output ─────────────────────────────────────────────────────────────
output = {
    "generated_at": NOW,
    "vo_count": len(all_vos),
    "type_distribution": type_dist,
    "interaction_type_distribution": itype_dist,
    "view_objects": all_vos,
}
out_path = C.write_json(os.path.join(OUT, "view-objects.json"), output)

# ── Pipeline decision ────────────────────────────────────────────────────────
dist_str = ", ".join(f"{k}:{v}" for k, v in sorted(type_dist.items()))
itype_str = ", ".join(f"{k}:{v}" for k, v in sorted(itype_dist.items()))
C.append_pipeline_decision(
    BASE,
    "Step 8 — view-objects",
    f"vo_count={len(all_vos)}, types=[{dist_str}], itypes=[{itype_str}]",
    shard=args.get("shard"),
)

# ── Summary ──────────────────────────────────────────────────────────────────
print(f"OK: {out_path} ({len(all_vos)} VOs)")
print(f"  view_types: {dist_str}")
print(f"  interaction_types: {itype_str}")
