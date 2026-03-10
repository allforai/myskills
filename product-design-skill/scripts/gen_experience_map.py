#!/usr/bin/env python3
# Skeleton generator — LLM enrichment required after running
"""Generate experience-map skeleton from business-flows + task-inventory.

Creates the three-layer structure (operation_lines > nodes > screens) with
deterministic fields populated and LLM-creative fields left as placeholders.

Output: .allforai/experience-map/experience-map-skeleton.json

Usage:
    python3 gen_experience_map.py <BASE_PATH> [--mode auto] [--shard experience-map]
"""

import os
import sys
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C

# Sentinel for "not yet set" flow_context fields (distinguishes from explicit None)
_UNSET = object()

# ── Setup ────────────────────────────────────────────────────────────────────
BASE, args = C.parse_args()
OUT = os.path.join(BASE, "experience-map")
C.ensure_dir(OUT)
NOW = C.now_iso()

# ── Load required inputs ─────────────────────────────────────────────────────
tasks = C.load_task_inventory(BASE)
flows = C.load_business_flows(BASE)

if not tasks:
    print("ERROR: task-inventory is empty or missing", file=sys.stderr)
    sys.exit(1)

# ── Load optional inputs ─────────────────────────────────────────────────────
roles_full = C.load_role_profiles_full(BASE)
role_map = {r["id"]: r.get("name", r["id"]) for r in roles_full}
audience_map = {}  # role_id → audience_type
platform_map = {}  # role_id → platform
for r in roles_full:
    atype = r.get("audience_type", "")
    if not atype:
        atype = "professional" if r.get("role_type") == "producer" else "consumer"
    audience_map[r["id"]] = atype
    platform_map[r["id"]] = "mobile-ios" if atype == "consumer" else "desktop-web"

entities_list, _ = C.load_entity_model(BASE)
entity_by_name = {e["name"]: e for e in entities_list}
entity_by_id = {e["id"]: e for e in entities_list}

view_objects = C.load_view_objects(BASE)

journey_lines = C.load_journey_emotion(BASE)
if not journey_lines:
    print("WARNING: journey-emotion-map.json not found, emotion data will be empty",
          file=sys.stderr)

# Build emotion lookup: (source_flow, step_seq) → emotion_node
emotion_lookup = {}
for jl in journey_lines:
    sf = jl.get("source_flow", "")
    for en in jl.get("emotion_nodes", []):
        step = en.get("step", en.get("seq", 0))
        emotion_lookup[(sf, step)] = en

# ── Load business-flows summary ──────────────────────────────────────────────
flows_data = C.load_json(os.path.join(BASE, "product-map/business-flows.json"))
summary = flows_data.get("summary", {}) if flows_data else {}
independent_ops = summary.get("independent_operations", [])
orphan_tasks_ids = summary.get("orphan_tasks", [])


# ── Helpers ──────────────────────────────────────────────────────────────────

def _infer_entity_for_task(task):
    """Return the entity dict most relevant to a task, or None."""
    module = task.get("module", "")
    if module and module in entity_by_name:
        return entity_by_name[module]
    return None


def _find_vo_for_task(task_id, task, interaction_type):
    """Find the best-matching VO for a task + interaction_type."""
    # Map interaction_type to view_type for matching
    itype_to_vtype = {
        "CT1": "list_item", "CT7": "list_item",
        "CT2": "detail", "CT5": "detail",
        "MG1": "detail", "MG2-D": "detail", "MG5": "detail",
        "MG2-L": "list_item", "MG3": "list_item",
        "MG2-C": "create_form", "SY2": "create_form", "SB1": "create_form",
        "MG2-E": "edit_form", "MG8": "edit_form",
        "MG4": "detail", "MG7": "detail",
        "EC1": "detail", "EC2": "create_form",
    }
    target_vtype = itype_to_vtype.get(interaction_type, "detail")

    # First pass: match by task_refs + view_type
    for vo in view_objects:
        if task_id in vo.get("task_refs", []) and vo.get("view_type") == target_vtype:
            return vo

    # Second pass: match by task_refs only
    for vo in view_objects:
        if task_id in vo.get("task_refs", []):
            return vo

    # Third pass: match by entity + view_type
    entity = _infer_entity_for_task(task)
    if entity:
        for vo in view_objects:
            if vo.get("entity_ref") == entity["id"] and vo.get("view_type") == target_vtype:
                return vo
        # Fourth pass: match by entity only
        for vo in view_objects:
            if vo.get("entity_ref") == entity["id"]:
                return vo

    return None


def _build_data_fields(task, entity, vo):
    """Build data_fields list in server-compatible format.

    Merges fields from entity-model and view-objects, each element is a dict
    with {name, label, type, input_widget, required}.
    """
    fields = []
    seen = set()

    # Primary source: VO fields
    if vo:
        for vf in vo.get("fields", []):
            fname = vf.get("name", "")
            if fname in seen:
                continue
            seen.add(fname)
            fields.append({
                "name": fname,
                "label": vf.get("label", fname),
                "type": _map_field_type(vf.get("type", "string")),
                "input_widget": _infer_widget(vf),
                "required": vf.get("required", False),
            })

    # Fallback: entity fields (if VO had no fields or doesn't exist)
    if not fields and entity:
        for ef in entity.get("fields", [])[:10]:  # cap at 10 for skeleton
            fname = ef.get("name", "")
            if fname in seen:
                continue
            seen.add(fname)
            fields.append({
                "name": fname,
                "label": ef.get("label", fname),
                "type": _map_field_type(ef.get("type", "string")),
                "input_widget": _infer_widget(ef),
                "required": "not_null" in ef.get("constraints", []),
            })

    return fields


def _map_field_type(raw_type):
    """Map entity-model types to data_fields types."""
    mapping = {
        "uuid": "string",
        "text": "rich_text",
        "decimal": "number",
        "integer": "number",
        "file": "image",
        "file[]": "array",
        "string[]": "array",
        "json": "string",
        "datetime": "date",
    }
    return mapping.get(raw_type, raw_type)


def _infer_widget(field):
    """Infer input_widget from field metadata."""
    ftype = field.get("type", "string")
    read_only = field.get("read_only", False)
    if read_only:
        return "readonly"
    widget_map = {
        "enum": "select",
        "boolean": "toggle",
        "text": "textarea",
        "rich_text": "rich_editor",
        "file": "file_upload",
        "file[]": "file_upload",
        "datetime": "date_picker",
        "date": "date_picker",
        "integer": "number_input",
        "decimal": "number_input",
        "number": "number_input",
        "string[]": "multi_select",
        "array": "multi_select",
        "image": "file_upload",
    }
    return widget_map.get(ftype, "text_input")


def _infer_actions(task, crud_type):
    """Infer basic actions from task name and CRUD type."""
    actions = []
    task_name = task.get("name", "")
    actions.append({
        "label": task_name,
        "type": {"C": "create", "U": "update", "D": "delete"}.get(crud_type, "navigate"),
        "frequency": "高" if task.get("category") == "core" else "中",
    })
    # Add common secondary actions based on CRUD
    if crud_type == "C":
        actions.append({"label": "取消", "type": "navigate", "frequency": "中"})
    elif crud_type == "U":
        actions.append({"label": "保存", "type": "update", "frequency": "高"})
    elif crud_type == "R":
        actions.append({"label": "返回", "type": "navigate", "frequency": "中"})
    return actions


# ── Screen counter & dedup tracking ──────────────────────────────────────────
screen_counter = 0
# (task_id, role_id) → screen object (for dedup)
task_role_screen = {}
# screen_id → screen object (global registry)
all_screens = {}


def _get_or_create_screen(task_id, role_id):
    """Return existing screen for (task_id, role_id) or create a new one.

    Returns (screen_dict, is_new).
    """
    global screen_counter
    key = (task_id, role_id)
    if key in task_role_screen:
        return task_role_screen[key], False

    task = tasks.get(task_id)
    if not task:
        return None, False

    screen_counter += 1
    sid = f"S{screen_counter:03d}"

    audience = audience_map.get(role_id, "consumer")
    platform = platform_map.get(role_id, "mobile-ios")

    itype, crud = C.infer_interaction_type(task, audience_type=audience)
    entity = _infer_entity_for_task(task)
    vo = _find_vo_for_task(task_id, task, itype)

    screen = {
        "id": sid,
        # LLM placeholder fields
        "name": "",
        "description": "",
        "platform": platform,
        "layout_type": "",
        "tasks": [task_id],
        "interaction_type": itype,
        "data_fields": _build_data_fields(task, entity, vo),
        "vo_ref": vo["id"] if vo else "",
        "actions": _infer_actions(task, crud),
        # LLM placeholder: components, interaction_pattern, emotion_design, states
        "components": [],
        "interaction_pattern": "",
        "emotion_design": "",
        "states": [],
        "flow_context": {
            "prev_screen": _UNSET,
            "next_screen": _UNSET,
            "entry_points": [],
            "exit_points": [],
        },
    }

    task_role_screen[key] = screen
    all_screens[sid] = screen
    return screen, True


# ── Step 1: Build operation_lines from business flows ────────────────────────
operation_lines = []

for flow in flows:
    flow_id = flow.get("id", "")
    flow_name = flow.get("name", "")
    flow_roles = flow.get("roles", [])

    nodes_out = []
    line_screen_ids = set()  # for intra-line dedup

    for fnode in C.get_flow_nodes(flow):
        task_ref = fnode.get("task_ref", "") if isinstance(fnode, dict) else fnode
        node_seq = fnode.get("seq", 0) if isinstance(fnode, dict) else 0
        node_name = fnode.get("name", "") if isinstance(fnode, dict) else ""
        node_role = fnode.get("role", "") if isinstance(fnode, dict) else ""

        if not task_ref or task_ref not in tasks:
            continue

        screen, _ = _get_or_create_screen(task_ref, node_role)
        if screen is None:
            continue

        # Intra-line dedup: skip if this screen already in this operation line
        if screen["id"] in line_screen_ids:
            # Still create the node but with empty screens (node exists in flow)
            nodes_out.append({
                "seq": node_seq,
                "id": f"{flow_id}-N{node_seq:02d}",
                "action": node_name,
                "task_ref": task_ref,
                "role": node_role,
                "screens": [],
            })
            continue

        line_screen_ids.add(screen["id"])

        # Attach emotion data if available
        emotion = emotion_lookup.get((flow_id, node_seq))
        emotion_ref = None
        if emotion:
            emotion_ref = {
                "emotion": emotion.get("emotion", ""),
                "intensity": emotion.get("intensity", ""),
                "design_hint": emotion.get("design_hint", ""),
            }

        node_out = {
            "seq": node_seq,
            "id": f"{flow_id}-N{node_seq:02d}",
            "action": node_name,
            "task_ref": task_ref,
            "role": node_role,
            "screens": [screen],
        }
        if emotion_ref:
            node_out["_emotion_ref"] = emotion_ref

        nodes_out.append(node_out)

    if not nodes_out:
        continue

    # Determine source journey (match by flow_id)
    source_journey = ""
    for jl in journey_lines:
        if jl.get("source_flow", "") == flow_id:
            source_journey = jl.get("id", jl.get("name", ""))
            break

    op_line = {
        "id": f"OL-{flow_id}",
        "name": flow_name,
        "source_flow": flow_id,
        "source_journey": source_journey,
        "role": flow_roles[0] if flow_roles else "",
        "nodes": nodes_out,
    }
    operation_lines.append(op_line)


# ── Step 2: Build extra operation lines for independent/orphan tasks ─────────
# Group independent_operations + orphan_tasks by role
extra_by_role = {}  # role_id → [task_id, ...]

for tid in independent_ops + orphan_tasks_ids:
    task = tasks.get(tid)
    if not task:
        continue
    role_id = task.get("owner_role", task.get("role_id", ""))
    if not role_id:
        # Try to infer from module → entity → owner_roles
        entity = _infer_entity_for_task(task)
        if entity and entity.get("owner_roles"):
            role_id = entity["owner_roles"][0] if isinstance(entity["owner_roles"][0], str) else ""
    extra_by_role.setdefault(role_id, []).append(tid)

for role_id, task_ids in extra_by_role.items():
    role_name = role_map.get(role_id, role_id)
    nodes_out = []
    line_screen_ids = set()

    for seq, tid in enumerate(task_ids, start=1):
        task = tasks.get(tid)
        if not task:
            continue

        screen, _ = _get_or_create_screen(tid, role_id)
        if screen is None:
            continue

        if screen["id"] in line_screen_ids:
            continue
        line_screen_ids.add(screen["id"])

        node_out = {
            "seq": seq,
            "id": f"OL-IND-{role_id}-N{seq:02d}",
            "action": task.get("name", ""),
            "task_ref": tid,
            "role": role_id,
            "screens": [screen],
        }
        nodes_out.append(node_out)

    if not nodes_out:
        continue

    op_line = {
        "id": f"OL-IND-{role_id}",
        "name": f"{role_name}独立操作",
        "source_flow": "",
        "source_journey": "",
        "role": role_id,
        "nodes": nodes_out,
    }
    operation_lines.append(op_line)


# ── Step 3: Populate flow_context (prev/next within each operation line) ─────

for line in operation_lines:
    # Collect screens in order across nodes
    screen_sequence = []
    for node in line.get("nodes", []):
        for s in node.get("screens", []):
            screen_sequence.append(s)

    for i, scr in enumerate(screen_sequence):
        prev_id = screen_sequence[i - 1]["id"] if i > 0 else None
        next_id = screen_sequence[i + 1]["id"] if i < len(screen_sequence) - 1 else None
        fc = scr.get("flow_context", {})
        # Only set if not already set by another line (first writer wins)
        if fc.get("prev_screen") is _UNSET:
            fc["prev_screen"] = prev_id
        if fc.get("next_screen") is _UNSET:
            fc["next_screen"] = next_id
        # entry/exit from operation line
        if i == 0:
            fc.setdefault("entry_points", []).append(line["id"])
        if i == len(screen_sequence) - 1:
            fc.setdefault("exit_points", []).append(line["id"])


# ── Step 3b: Finalize flow_context (convert sentinels to None) ───────────────
for screen in all_screens.values():
    fc = screen.get("flow_context", {})
    if fc.get("prev_screen") is _UNSET:
        fc["prev_screen"] = None
    if fc.get("next_screen") is _UNSET:
        fc["next_screen"] = None

# ── Step 4: Build screen_index ───────────────────────────────────────────────
screen_index = {sid: screen for sid, screen in all_screens.items()}


# ── Step 5: Verify task coverage ─────────────────────────────────────────────
covered_tasks = set()
for line in operation_lines:
    for node in line.get("nodes", []):
        for s in node.get("screens", []):
            for tid in s.get("tasks", []):
                covered_tasks.add(tid)

uncovered = set(tasks.keys()) - covered_tasks
if uncovered:
    print(f"WARNING: {len(uncovered)} tasks not covered: {sorted(uncovered)}",
          file=sys.stderr)


# ── Step 6: Write output ─────────────────────────────────────────────────────
output = {
    "generated_at": NOW,
    "generator": "gen_experience_map.py",
    "status": "skeleton",
    "stats": {
        "operation_line_count": len(operation_lines),
        "screen_count": len(all_screens),
        "task_coverage": f"{len(covered_tasks)}/{len(tasks)}",
        "uncovered_tasks": sorted(uncovered),
    },
    "operation_lines": operation_lines,
    "screen_index": screen_index,
}

out_path = C.write_json(os.path.join(OUT, "experience-map-skeleton.json"), output)

# ── Pipeline decision ────────────────────────────────────────────────────────
C.append_pipeline_decision(
    BASE,
    "experience-map-skeleton",
    f"op_lines={len(operation_lines)}, screens={len(all_screens)}, "
    f"coverage={len(covered_tasks)}/{len(tasks)}",
    shard=args.get("shard"),
)

# ── Summary ──────────────────────────────────────────────────────────────────
print(f"OK: {out_path}")
print(f"  operation_lines: {len(operation_lines)}")
print(f"  screens: {len(all_screens)}")
print(f"  task_coverage: {len(covered_tasks)}/{len(tasks)}")
if uncovered:
    print(f"  uncovered_tasks: {sorted(uncovered)}")
print(f"  LLM placeholder fields: name, description, components, interaction_pattern, "
      f"emotion_design, states, layout_type")
