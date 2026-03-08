#!/usr/bin/env python3
"""Step 8: Generate View Objects with fields, Action Bindings, and interaction_type.

Reads entity-model.json, api-contracts.json, task-inventory.json from product-map.
Writes view-objects.json to <BASE>/product-map/.

Usage:
    python3 gen_view_objects.py <BASE_PATH> [--mode auto]
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C

# ── Display format mapping ───────────────────────────────────────────────────
DISPLAY_FORMATS = {
    "enum": "status_badge",
    "decimal": "currency",
    "datetime": "relative_time",
    "integer": "number",
    "file": "thumbnail",
    "file[]": "thumbnail_group",
}

# ── Input widget mapping ─────────────────────────────────────────────────────
INPUT_WIDGETS = {
    "string": "text",
    "text": "textarea",
    "integer": "number",
    "decimal": "number",
    "enum": "select",
    "file": "file_upload",
    "file[]": "file_upload",
    "date": "date_picker",
    "datetime": "date_picker",
    "string[]": "tag_input",
    "uuid": "text",
}

# ── CRUD keywords (mirror from gen_data_model.py) ────────────────────────────
CRUD_KEYWORDS = {
    "C": ["新增", "创建", "添加", "注册", "上传", "发布", "录入", "create", "add", "new", "register", "upload"],
    "U": ["修改", "编辑", "更新", "调整", "设置", "配置", "update", "edit", "modify", "configure", "set"],
    "D": ["删除", "移除", "撤销", "取消", "remove", "delete", "cancel", "revoke"],
    "R": ["查看", "浏览", "搜索", "筛选", "导出", "统计", "列表", "详情", "view", "list", "search", "filter", "export", "detail"],
}

# Fields to exclude from list items
LIST_EXCLUDE_TYPES = {"text", "file[]"}
LIST_EXCLUDE_CONSTRAINTS = {"auto"}


def infer_crud(task_name):
    """Infer CRUD type from task name keywords."""
    for crud, keywords in CRUD_KEYWORDS.items():
        for kw in keywords:
            if kw in task_name.lower():
                return crud
    return "R"


def _has_crud_tasks(entity_tasks, crud_type):
    """Check if entity has tasks of given CRUD type."""
    for t in entity_tasks:
        if infer_crud(t.get("name", "")) == crud_type:
            return True
    return False


def _has_detail_tasks(entity_tasks):
    """Check if entity has detail-viewing tasks."""
    for t in entity_tasks:
        name = t.get("name", "").lower()
        if "详情" in name or "detail" in name:
            return True
    return False


def _find_api(endpoints, entity_id, method, path_suffix=None):
    """Find an API endpoint matching entity, method, and optional path suffix."""
    for ep in endpoints:
        if ep.get("entity_ref") != entity_id:
            continue
        if ep["method"] != method:
            continue
        if path_suffix and not ep["path"].endswith(path_suffix):
            continue
        if path_suffix is None:
            # For POST/GET list, match the base path (no :id)
            if method in ("POST", "GET") and ":id" not in ep["path"]:
                return ep
            elif method in ("PUT", "DELETE") and ":id" in ep["path"]:
                return ep
        else:
            return ep
    return None


def _find_api_by_method_entity(endpoints, entity_id, method, require_id=None):
    """Find API by entity and method. require_id: True=must have :id, False=must not, None=any."""
    for ep in endpoints:
        if ep.get("entity_ref") != entity_id or ep["method"] != method:
            continue
        has_id = ":id" in ep["path"]
        if require_id is True and not has_id:
            continue
        if require_id is False and has_id:
            continue
        # Skip state transition PATCHes (path has extra segment after :id)
        if method == "PATCH":
            continue
        return ep
    return None


def _make_action_id(vo_id, suffix):
    return f"ACT_{vo_id}_{suffix}"


# ── VO Generators ────────────────────────────────────────────────────────────

def gen_list_item_vo(vo_counter, entity, entity_tasks, endpoints):
    """Generate ListItemVO for an entity."""
    eid = entity["id"]
    ename = entity["name"]
    vo_id = f"VO{vo_counter:03d}"

    # Fields: exclude text, file[], auto fields
    fields = []
    filters = []
    for f in entity["fields"]:
        ftype = f["type"]
        cons = f.get("constraints", [])
        if ftype in LIST_EXCLUDE_TYPES:
            continue
        if any(c in LIST_EXCLUDE_CONSTRAINTS for c in cons):
            continue
        display_format = DISPLAY_FORMATS.get(ftype)
        field_entry = {
            "name": f["name"],
            "type": ftype,
            "read_only": True,
        }
        if display_format:
            field_entry["display_format"] = display_format
        fields.append(field_entry)
        # Enum fields become filters
        if ftype == "enum":
            filters.append(f["name"])

    # Row actions
    has_detail = _has_detail_tasks(entity_tasks)
    has_edit = _has_crud_tasks(entity_tasks, "U")
    has_delete = _has_crud_tasks(entity_tasks, "D")

    row_actions = []
    if has_detail:
        row_actions.append("view_detail")
    if has_edit:
        row_actions.append("edit")
    if has_delete:
        row_actions.append("delete")

    interaction_type = "MG2-L" if row_actions else "MG1"

    # Actions
    actions = []

    # Toolbar "新建" button
    has_create = _has_crud_tasks(entity_tasks, "C")
    if has_create:
        actions.append({
            "id": _make_action_id(vo_id, "create"),
            "label": f"新建{ename}",
            "type": "navigate",
            "trigger": "toolbar_button",
            "target_vo": None,  # cross-linked later
            "nav_mode": "push",
            "style": "primary",
            "frequency": "high",
        })

    # Row "查看详情"
    if has_detail:
        actions.append({
            "id": _make_action_id(vo_id, "view_detail"),
            "label": "查看详情",
            "type": "navigate",
            "trigger": "row_click",
            "target_vo": None,  # cross-linked later
            "nav_mode": "push",
            "style": "ghost",
            "frequency": "high",
        })

    # Row "删除"
    if has_delete:
        delete_api = _find_api_by_method_entity(endpoints, eid, "DELETE", require_id=True)
        act = {
            "id": _make_action_id(vo_id, "delete"),
            "label": "删除",
            "type": "api_call",
            "trigger": "row_action",
            "confirm": {
                "title": f"确认删除{ename}",
                "message": f"删除后无法恢复，是否确认删除该{ename}？",
            },
            "api_params": {"id": "$row.id"},
            "on_success": {"action": "refresh_list", "toast": "删除成功"},
            "on_error": {"action": "show_error"},
            "style": "danger",
            "frequency": "low",
        }
        if delete_api:
            act["api_ref"] = delete_api["id"]
        actions.append(act)

    # List API ref
    list_api = _find_api_by_method_entity(endpoints, eid, "GET", require_id=False)

    vo = {
        "id": vo_id,
        "entity_ref": eid,
        "entity_name": ename,
        "view_type": "list_item",
        "interaction_type": interaction_type,
        "fields": fields,
        "filters": filters,
        "row_actions": row_actions,
        "actions": actions,
    }
    if list_api:
        vo["api_ref"] = list_api["id"]

    return vo


def gen_detail_vo(vo_counter, entity, entity_tasks, endpoints):
    """Generate DetailVO for an entity."""
    eid = entity["id"]
    ename = entity["name"]
    vo_id = f"VO{vo_counter:03d}"

    # All fields, read-only
    fields = []
    for f in entity["fields"]:
        display_format = DISPLAY_FORMATS.get(f["type"])
        field_entry = {
            "name": f["name"],
            "type": f["type"],
            "read_only": True,
        }
        if display_format:
            field_entry["display_format"] = display_format
        fields.append(field_entry)

    actions = []

    # "编辑" button
    has_edit = _has_crud_tasks(entity_tasks, "U")
    if has_edit:
        actions.append({
            "id": _make_action_id(vo_id, "edit"),
            "label": "编辑",
            "type": "navigate",
            "trigger": "button",
            "target_vo": None,  # cross-linked later
            "nav_mode": "push",
            "style": "primary",
            "frequency": "medium",
        })

    # State transition buttons
    if entity.get("state_machine"):
        for trans in entity["state_machine"]["transitions"]:
            trigger = trans["trigger"]
            # Find PATCH endpoint for this transition
            patch_api = None
            for ep in endpoints:
                if (ep.get("entity_ref") == eid
                        and ep["method"] == "PATCH"
                        and trigger in ep["path"]):
                    patch_api = ep
                    break

            act = {
                "id": _make_action_id(vo_id, f"state_{trigger}"),
                "label": trigger,
                "type": "api_call",
                "trigger": "button",
                "precondition": {"field": "status", "op": "eq", "value": trans["from"]},
                "api_params": {"id": "$row.id"},
                "on_success": {"action": "refresh_row", "toast": f"{trigger}成功"},
                "on_error": {"action": "show_error"},
                "style": "secondary",
                "frequency": "medium",
            }
            if patch_api:
                act["api_ref"] = patch_api["id"]
            actions.append(act)

    detail_api = _find_api_by_method_entity(endpoints, eid, "GET", require_id=True)

    vo = {
        "id": vo_id,
        "entity_ref": eid,
        "entity_name": ename,
        "view_type": "detail",
        "interaction_type": "MG2-D",
        "fields": fields,
        "actions": actions,
    }
    if detail_api:
        vo["api_ref"] = detail_api["id"]

    return vo


def gen_create_form_vo(vo_counter, entity, endpoints):
    """Generate CreateFormVO for an entity."""
    eid = entity["id"]
    ename = entity["name"]
    vo_id = f"VO{vo_counter:03d}"

    # Writable fields: no PK, no auto, no status
    fields = []
    for f in entity["fields"]:
        cons = f.get("constraints", [])
        if "PK" in cons or "auto" in cons:
            continue
        if f["name"] == "status":
            continue
        widget = INPUT_WIDGETS.get(f["type"], "text")
        required = "required" in cons or f["name"] in ("name", "title")
        field_entry = {
            "name": f["name"],
            "type": f["type"],
            "input_widget": widget,
            "required": required,
            "prefill": False,
        }
        fields.append(field_entry)

    post_api = _find_api_by_method_entity(endpoints, eid, "POST")

    actions = [
        {
            "id": _make_action_id(vo_id, "submit"),
            "label": f"创建{ename}",
            "type": "api_call",
            "trigger": "button",
            "api_ref": post_api["id"] if post_api else None,
            "on_success": {"action": "navigate_back", "toast": "创建成功"},
            "on_error": {"action": "show_field_errors"},
            "style": "primary",
            "frequency": "high",
        },
        {
            "id": _make_action_id(vo_id, "cancel"),
            "label": "取消",
            "type": "navigate",
            "trigger": "button",
            "nav_mode": "back",
            "style": "secondary",
            "frequency": "medium",
        },
    ]

    vo = {
        "id": vo_id,
        "entity_ref": eid,
        "entity_name": ename,
        "view_type": "create_form",
        "interaction_type": "MG2-C",
        "fields": fields,
        "actions": actions,
    }
    if post_api:
        vo["api_ref"] = post_api["id"]

    return vo


def gen_edit_form_vo(vo_counter, entity, endpoints):
    """Generate EditFormVO for an entity."""
    eid = entity["id"]
    ename = entity["name"]
    vo_id = f"VO{vo_counter:03d}"

    # Same as create but prefill=true
    fields = []
    for f in entity["fields"]:
        cons = f.get("constraints", [])
        if "PK" in cons or "auto" in cons:
            continue
        if f["name"] == "status":
            continue
        widget = INPUT_WIDGETS.get(f["type"], "text")
        required = "required" in cons or f["name"] in ("name", "title")
        field_entry = {
            "name": f["name"],
            "type": f["type"],
            "input_widget": widget,
            "required": required,
            "prefill": True,
        }
        fields.append(field_entry)

    put_api = _find_api_by_method_entity(endpoints, eid, "PUT", require_id=True)

    actions = [
        {
            "id": _make_action_id(vo_id, "submit"),
            "label": f"保存{ename}",
            "type": "api_call",
            "trigger": "button",
            "api_ref": put_api["id"] if put_api else None,
            "api_params": {"id": "$row.id"},
            "on_success": {"action": "navigate_back", "toast": "保存成功"},
            "on_error": {"action": "show_field_errors"},
            "style": "primary",
            "frequency": "high",
        },
        {
            "id": _make_action_id(vo_id, "cancel"),
            "label": "取消",
            "type": "navigate",
            "trigger": "button",
            "nav_mode": "back",
            "style": "secondary",
            "frequency": "medium",
        },
    ]

    vo = {
        "id": vo_id,
        "entity_ref": eid,
        "entity_name": ename,
        "view_type": "edit_form",
        "interaction_type": "MG2-E",
        "fields": fields,
        "actions": actions,
    }
    if put_api:
        vo["api_ref"] = put_api["id"]

    return vo


def gen_state_action_vo(vo_counter, entity, endpoints):
    """Generate StateActionVO for an entity with state_machine."""
    eid = entity["id"]
    ename = entity["name"]
    vo_id = f"VO{vo_counter:03d}"

    # Display fields: PK + status + key numeric fields
    fields = []
    for f in entity["fields"]:
        if f["name"] == "id" or f["type"] == "enum":
            display_format = DISPLAY_FORMATS.get(f["type"])
            field_entry = {
                "name": f["name"],
                "type": f["type"],
                "read_only": True,
            }
            if display_format:
                field_entry["display_format"] = display_format
            fields.append(field_entry)
        elif f["type"] in ("integer", "decimal"):
            field_entry = {
                "name": f["name"],
                "type": f["type"],
                "read_only": True,
                "display_format": DISPLAY_FORMATS.get(f["type"], "number"),
            }
            fields.append(field_entry)

    # One action per state transition
    actions = []
    for trans in entity["state_machine"]["transitions"]:
        trigger = trans["trigger"]
        # Find PATCH endpoint
        patch_api = None
        for ep in endpoints:
            if (ep.get("entity_ref") == eid
                    and ep["method"] == "PATCH"
                    and trigger in ep["path"]):
                patch_api = ep
                break

        act = {
            "id": _make_action_id(vo_id, f"transition_{trigger}"),
            "label": f"{trigger} ({trans['from']} → {trans['to']})",
            "type": "api_call",
            "trigger": "button",
            "precondition": {"field": "status", "op": "eq", "value": trans["from"]},
            "api_params": {"id": "$row.id"},
            "on_success": {"action": "refresh_row", "toast": f"{trigger}成功"},
            "on_error": {"action": "show_error"},
            "style": "secondary",
            "frequency": "medium",
        }
        if patch_api:
            act["api_ref"] = patch_api["id"]
            # Add input_form if API has non-empty request body
            if patch_api.get("request_body"):
                act["input_form"] = {
                    "fields": [
                        {"name": fb, "input_widget": "text"}
                        for fb in patch_api["request_body"]
                    ]
                }
        actions.append(act)

    vo = {
        "id": vo_id,
        "entity_ref": eid,
        "entity_name": ename,
        "view_type": "state_action",
        "interaction_type": "MG3",
        "fields": fields,
        "actions": actions,
    }

    return vo


# ── Cross-linking ────────────────────────────────────────────────────────────

def cross_link_vos(vos):
    """Cross-link navigate actions to their target VOs."""
    # Build lookup: (entity_ref, view_type) → vo_id
    type_map = {}
    for vo in vos:
        key = (vo["entity_ref"], vo["view_type"])
        type_map[key] = vo["id"]

    for vo in vos:
        entity_ref = vo["entity_ref"]
        for act in vo.get("actions", []):
            if act.get("type") != "navigate":
                continue
            if act.get("target_vo") is not None:
                continue  # already set (e.g., "back")

            aid = act["id"]
            # Determine target by action suffix
            if "create" in aid:
                target = type_map.get((entity_ref, "create_form"))
            elif "view_detail" in aid:
                target = type_map.get((entity_ref, "detail"))
            elif "edit" in aid:
                target = type_map.get((entity_ref, "edit_form"))
            else:
                target = None

            if target:
                act["target_vo"] = target


# ── Main ─────────────────────────────────────────────────────────────────────

BASE, args = C.parse_args()
OUT = os.path.join(BASE, "product-map")
C.ensure_dir(OUT)
NOW = C.now_iso()

# Load inputs
entities, relationships = C.load_entity_model(BASE)
endpoints = C.load_api_contracts(BASE)
tasks_dict = C.load_task_inventory(BASE)

# Group tasks by module
module_tasks = {}
for tid, task in tasks_dict.items():
    module = task.get("module", "unknown")
    module_tasks.setdefault(module, []).append({**task, "_id": tid})

# Generate VOs
all_vos = []
vo_counter = 0

for entity in entities:
    ename = entity["name"]
    etasks = module_tasks.get(ename, [])
    crud = entity.get("crud_coverage", {})

    # 1. ListItemVO — always generate if has R tasks
    if crud.get("R", 0) > 0:
        vo_counter += 1
        all_vos.append(gen_list_item_vo(vo_counter, entity, etasks, endpoints))

    # 2. DetailVO — only if has detail tasks
    if _has_detail_tasks(etasks):
        vo_counter += 1
        all_vos.append(gen_detail_vo(vo_counter, entity, etasks, endpoints))

    # 3. CreateFormVO — if has C tasks
    if crud.get("C", 0) > 0:
        vo_counter += 1
        all_vos.append(gen_create_form_vo(vo_counter, entity, endpoints))

    # 4. EditFormVO — if has U tasks
    if crud.get("U", 0) > 0:
        vo_counter += 1
        all_vos.append(gen_edit_form_vo(vo_counter, entity, endpoints))

    # 5. StateActionVO — if has state_machine
    if entity.get("state_machine"):
        vo_counter += 1
        all_vos.append(gen_state_action_vo(vo_counter, entity, endpoints))

# Cross-link navigate actions
cross_link_vos(all_vos)

# Build type distribution
type_dist = {}
for vo in all_vos:
    vtype = vo["view_type"]
    type_dist[vtype] = type_dist.get(vtype, 0) + 1

# Write output
output = {
    "generated_at": NOW,
    "vo_count": len(all_vos),
    "type_distribution": type_dist,
    "view_objects": all_vos,
}
out_path = C.write_json(os.path.join(OUT, "view-objects.json"), output)

# Pipeline decision
dist_str = ", ".join(f"{k}:{v}" for k, v in type_dist.items())
C.append_pipeline_decision(
    BASE,
    "Step 8 — view-objects",
    f"vo_count={len(all_vos)}, types=[{dist_str}]",
    shard=args.get("shard"),
)

print(f"OK: {out_path} ({len(all_vos)} VOs: {dist_str})")
