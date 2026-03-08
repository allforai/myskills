# Wireframe Quality Upgrade Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace generic wireframes with data-model-driven, interaction-type-specific wireframes with 4D/6V/XV enrichment.

**Architecture:** Insert data modeling (Step 7/8) into product-map, add data-model-review gate, upgrade experience-map to consume VOs, rewrite wireframe renderer with per-type templates + 4D panel + 6V tabs + XV validation.

**Tech Stack:** Python 3 (scripts), HTML/CSS/JS (review servers), OpenRouter API (XV)

---

## Task 1: _common.py — New Loaders + Port

**Files:**
- Modify: `product-design-skill/scripts/_common.py:52-59` (REVIEW_PORTS)
- Modify: `product-design-skill/scripts/_common.py:206+` (add new loader functions)

**Step 1: Add data-model port to REVIEW_PORTS**

In `_common.py:54-59`, change:
```python
REVIEW_PORTS = {
    "concept": 18900,
    "product-map": 18901,
    "wireframe": 18902,
    "ui": 18903,
}
```
to:
```python
REVIEW_PORTS = {
    "concept": 18900,
    "product-map": 18901,
    "wireframe": 18902,
    "ui": 18903,
    "data-model": 18904,
}
```

**Step 2: Add entity/API/VO loaders**

Append after the existing `load_interaction_gate` function (around line 263):

```python
def load_entity_model(base):
    """Load entity-model.json, return entities list and relationships list."""
    data = load_json(os.path.join(base, "product-map/entity-model.json"))
    if data is None:
        return [], []
    entities = data.get("entities", [])
    relationships = data.get("relationships", [])
    return entities, relationships


def load_api_contracts(base):
    """Load api-contracts.json, return endpoints list."""
    data = load_json(os.path.join(base, "product-map/api-contracts.json"))
    if data is None:
        return []
    return data.get("endpoints", [])


def load_view_objects(base):
    """Load view-objects.json, return view_objects list."""
    data = load_json(os.path.join(base, "product-map/view-objects.json"))
    if data is None:
        return []
    return data.get("view_objects", [])
```

**Step 3: Verify syntax**

Run: `python3 -c "import product_design_skill_scripts._common" 2>/dev/null || python3 product-design-skill/scripts/_common.py`
Expected: "All imports OK"

**Step 4: Commit**

```bash
git add product-design-skill/scripts/_common.py
git commit -m "feat(product-design): add data-model loaders and review port to _common.py"
```

---

## Task 2: gen_data_model.py — Step 7 Entity + API Inference

**Files:**
- Create: `product-design-skill/scripts/gen_data_model.py`
- Test: manual run with synthetic data

**Step 1: Create test fixture**

Create a minimal `.allforai/` test directory with task-inventory.json, business-flows.json, role-profiles.json, constraints.json that exercises the entity inference logic. Put this in a temp location for testing:

```bash
mkdir -p /tmp/test-dm/.allforai/product-map
```

Write `/tmp/test-dm/.allforai/product-map/task-inventory.json`:
```json
{
  "tasks": [
    {"id": "T001", "name": "查看订单列表", "module": "order", "owner_role": "R001", "category": "basic"},
    {"id": "T002", "name": "创建订单", "module": "order", "owner_role": "R001", "category": "basic"},
    {"id": "T003", "name": "查看订单详情", "module": "order", "owner_role": "R001", "category": "core"},
    {"id": "T004", "name": "修改订单备注", "module": "order", "owner_role": "R001", "category": "core"},
    {"id": "T005", "name": "确认支付", "module": "order", "owner_role": "R001", "category": "basic"},
    {"id": "T006", "name": "发货", "module": "order", "owner_role": "R002", "category": "basic"},
    {"id": "T007", "name": "取消订单", "module": "order", "owner_role": "R001", "category": "core"},
    {"id": "T008", "name": "删除订单", "module": "order", "owner_role": "R002", "category": "core"},
    {"id": "T010", "name": "查看商品列表", "module": "product", "owner_role": "R002", "category": "basic"},
    {"id": "T011", "name": "创建商品", "module": "product", "owner_role": "R002", "category": "basic"},
    {"id": "T012", "name": "编辑商品信息", "module": "product", "owner_role": "R002", "category": "core"},
    {"id": "T013", "name": "上传商品图片", "module": "product", "owner_role": "R002", "category": "core"},
    {"id": "T014", "name": "商品上下架", "module": "product", "owner_role": "R002", "category": "basic"}
  ]
}
```

Write `/tmp/test-dm/.allforai/product-map/business-flows.json`:
```json
{
  "flows": [
    {
      "id": "F001",
      "name": "订单履约流程",
      "nodes": [
        {"task_ref": "T002", "label": "创建订单"},
        {"task_ref": "T005", "label": "确认支付"},
        {"task_ref": "T006", "label": "发货"},
        {"task_ref": "T003", "label": "确认收货"}
      ]
    }
  ]
}
```

Write `/tmp/test-dm/.allforai/product-map/role-profiles.json`:
```json
{
  "roles": [
    {"id": "R001", "name": "买家", "audience_type": "consumer"},
    {"id": "R002", "name": "商户", "audience_type": "business"}
  ]
}
```

Write `/tmp/test-dm/.allforai/product-map/constraints.json`:
```json
{
  "constraints": [
    {"id": "CON001", "rule": "订单金额不能为负", "scope": "order"},
    {"id": "CON002", "rule": "商品名称必填", "scope": "product"}
  ]
}
```

**Step 2: Write gen_data_model.py**

Create `product-design-skill/scripts/gen_data_model.py`:

```python
#!/usr/bin/env python3
"""Step 7: Generate entity-model.json + api-contracts.json from product-map data.

Infers backend entities, fields, state machines, and API endpoints from
task-inventory, business-flows, constraints, and role-profiles.

Usage:
    python3 gen_data_model.py <BASE_PATH> [--mode auto]
"""
import sys, os, json, datetime, re

sys.path.insert(0, os.path.dirname(__file__))
import _common as C

# ── CRUD keywords (shared with gen_experience_map.py) ────────────────────────
CRUD_KEYWORDS = {
    "C": ["新增", "创建", "添加", "注册", "上传", "发布", "录入",
          "create", "add", "new", "register", "upload", "publish"],
    "U": ["修改", "编辑", "更新", "调整", "设置", "配置",
          "update", "edit", "modify", "configure", "set"],
    "D": ["删除", "移除", "撤销", "取消",
          "remove", "delete", "cancel", "revoke"],
    "R": ["查看", "浏览", "搜索", "筛选", "导出", "统计", "列表", "详情",
          "view", "list", "search", "filter", "export", "detail", "report"],
}

# State-transition keywords — tasks that drive entity state changes, not field edits
STATE_KEYWORDS = ["审核", "审批", "确认", "发货", "签收", "上架", "下架",
                  "冻结", "解冻", "激活", "禁用", "关闭", "打回", "驳回",
                  "approve", "reject", "ship", "deliver", "freeze", "activate",
                  "disable", "close", "publish", "unpublish"]

# Field-hint nouns — extracted from task names to infer entity fields
FIELD_HINT_PATTERNS = {
    "名称": ("name", "string", True),
    "标题": ("title", "string", True),
    "描述": ("description", "text", False),
    "备注": ("note", "text", False),
    "价格": ("price", "decimal", True),
    "金额": ("amount", "decimal", True),
    "数量": ("quantity", "integer", True),
    "图片": ("images", "file[]", False),
    "头像": ("avatar", "file", False),
    "地址": ("address", "string", True),
    "手机": ("phone", "string", True),
    "邮箱": ("email", "string", False),
    "密码": ("password", "string", True),
    "状态": ("status", "enum", True),
    "时间": ("datetime_field", "datetime", False),
    "日期": ("date_field", "date", False),
    "分类": ("category", "string", False),
    "标签": ("tags", "string[]", False),
    "评分": ("rating", "decimal", False),
    "内容": ("content", "text", True),
    "链接": ("url", "string", False),
    "排序": ("sort_order", "integer", False),
}


def infer_crud(task_name):
    for crud, keywords in CRUD_KEYWORDS.items():
        for kw in keywords:
            if kw in task_name.lower():
                return crud
    return "R"


def is_state_transition(task_name):
    name_lower = task_name.lower()
    return any(kw in name_lower for kw in STATE_KEYWORDS)


def extract_field_hints(task_name):
    """Extract field hints from task name using FIELD_HINT_PATTERNS."""
    hints = []
    for zh_kw, (field_name, field_type, required) in FIELD_HINT_PATTERNS.items():
        if zh_kw in task_name:
            hints.append({"name": field_name, "type": field_type, "required": required,
                          "source_hint": zh_kw})
    return hints


def extract_noun_from_task(task_name, module):
    """Extract the object noun from task name (remove verb prefix)."""
    # Strip common verb prefixes
    for keywords in CRUD_KEYWORDS.values():
        for kw in keywords:
            if task_name.startswith(kw):
                remainder = task_name[len(kw):]
                if remainder:
                    return remainder
    for kw in STATE_KEYWORDS:
        if task_name.startswith(kw):
            remainder = task_name[len(kw):]
            if remainder:
                return remainder
    return module


# ── Entity inference ─────────────────────────────────────────────────────────

def infer_entities(tasks_by_module, flows, constraints):
    """Infer entities from task modules, enrich with flows and constraints."""
    entities = []
    entity_counter = 0

    for module, task_list in tasks_by_module.items():
        entity_counter += 1
        eid = f"E{entity_counter:03d}"

        # Determine entity name from most common noun in tasks
        nouns = []
        for t in task_list:
            noun = extract_noun_from_task(t["name"], module)
            nouns.append(noun)
        # Use module name as entity name (most reliable)
        entity_name_zh = module

        # Collect CRUD types
        crud_set = set()
        field_hints = []
        state_tasks = []
        source_task_ids = []

        for t in task_list:
            crud = infer_crud(t["name"])
            crud_set.add(crud)
            field_hints.extend(extract_field_hints(t["name"]))
            if is_state_transition(t["name"]):
                state_tasks.append(t)
            source_task_ids.append(t["id"])

        # Build fields — always start with id + standard fields
        fields = [
            {"name": "id", "type": "uuid", "pk": True, "required": True,
             "label": f"{entity_name_zh}ID"},
        ]

        # Add inferred fields (deduplicate by name)
        seen_fields = {"id"}
        for hint in field_hints:
            if hint["name"] not in seen_fields:
                seen_fields.add(hint["name"])
                fields.append({
                    "name": hint["name"],
                    "type": hint["type"],
                    "required": hint["required"],
                    "label": hint["source_hint"],
                })

        # If entity has state transitions, add status enum field
        state_machine = None
        if state_tasks:
            states = set()
            transitions = []
            for st in state_tasks:
                action_name = st["name"]
                # Infer from/to states from action name
                # This is a heuristic — will be refined by user in review
                action_verb = action_name
                for kw in STATE_KEYWORDS:
                    if kw in action_name:
                        action_verb = kw
                        break
                transitions.append({
                    "action": action_verb,
                    "task_ref": st["id"],
                    "label": action_name,
                })
                states.add(action_verb)

            if "status" not in seen_fields:
                fields.append({
                    "name": "status", "type": "enum",
                    "required": True, "label": "状态",
                    "values": sorted(states),
                })
                seen_fields.add("status")

            state_machine = {
                "field": "status",
                "transitions": transitions,
            }

        # Add timestamps if CRUD includes C
        if "C" in crud_set and "created_at" not in seen_fields:
            fields.append({"name": "created_at", "type": "datetime",
                           "required": True, "auto": True, "label": "创建时间"})
            seen_fields.add("created_at")
        if "U" in crud_set and "updated_at" not in seen_fields:
            fields.append({"name": "updated_at", "type": "datetime",
                           "required": True, "auto": True, "label": "更新时间"})
            seen_fields.add("updated_at")

        # Apply constraints
        for con in constraints:
            scope = con.get("scope", "")
            if scope == module or scope in entity_name_zh:
                rule = con.get("rule", "")
                # Try to extract field + constraint from rule text
                for zh_kw, (fname, _, _) in FIELD_HINT_PATTERNS.items():
                    if zh_kw in rule and fname in seen_fields:
                        # Find the field and add constraint
                        for f in fields:
                            if f["name"] == fname:
                                f.setdefault("constraints", []).append(rule)

        entity = {
            "id": eid,
            "name": module,
            "name_zh": entity_name_zh,
            "source_module": module,
            "source_tasks": source_task_ids,
            "crud_operations": sorted(crud_set),
            "fields": fields,
        }
        if state_machine:
            entity["state_machine"] = state_machine

        entities.append(entity)

    return entities


def infer_relationships(entities, flows):
    """Infer entity relationships from business flows and task references."""
    relationships = []
    entity_by_module = {e["source_module"]: e for e in entities}

    # From flows: if two entities appear in the same flow, they're related
    for flow in flows:
        modules_in_flow = []
        for node in C.get_flow_nodes(flow):
            task_ref = node.get("task_ref", "") if isinstance(node, dict) else ""
            # Find which entity this task belongs to
            for e in entities:
                if task_ref in e["source_tasks"]:
                    if e["source_module"] not in modules_in_flow:
                        modules_in_flow.append(e["source_module"])
                    break

        # Create relationships between consecutive entities in flow
        for i in range(len(modules_in_flow) - 1):
            m1, m2 = modules_in_flow[i], modules_in_flow[i + 1]
            if m1 != m2:
                e1 = entity_by_module.get(m1)
                e2 = entity_by_module.get(m2)
                if e1 and e2:
                    rel_id = f"{e1['id']}_{e2['id']}"
                    # Avoid duplicates
                    if not any(r.get("id") == rel_id for r in relationships):
                        relationships.append({
                            "id": rel_id,
                            "from": e1["id"],
                            "from_name": e1["name_zh"],
                            "to": e2["id"],
                            "to_name": e2["name_zh"],
                            "type": "1:N",
                            "fk": f"{m2}_id",
                            "source_flow": flow.get("id", ""),
                        })

    return relationships


# ── API contract inference ───────────────────────────────────────────────────

def infer_api_contracts(entities, tasks_inv):
    """Generate API endpoints from entities and their CRUD operations."""
    endpoints = []
    api_counter = 0

    for entity in entities:
        module = entity["source_module"]
        path_base = f"/{module}s"  # simple pluralization
        eid = entity["id"]

        # Group source tasks by CRUD
        task_cruds = {}
        for tid in entity["source_tasks"]:
            task = tasks_inv.get(tid, {})
            crud = infer_crud(task.get("name", ""))
            task_cruds.setdefault(crud, []).append(task)

        # R tasks → GET list + GET detail
        if "R" in task_cruds:
            r_tasks = task_cruds["R"]
            list_tasks = [t for t in r_tasks
                          if any(kw in t.get("name", "") for kw in ["列表", "查看", "搜索", "浏览", "list"])]
            detail_tasks = [t for t in r_tasks
                            if any(kw in t.get("name", "") for kw in ["详情", "detail"])]

            if list_tasks or not detail_tasks:
                api_counter += 1
                # Build filterable fields
                filters = []
                for f in entity["fields"]:
                    if f["type"] == "enum" or f.get("name") == "status":
                        filters.append({"name": f["name"], "type": f["type"], "label": f.get("label", f["name"])})
                endpoints.append({
                    "id": f"API{api_counter:03d}",
                    "method": "GET",
                    "path": path_base,
                    "name_zh": f"获取{entity['name_zh']}列表",
                    "type": "list",
                    "entity_ref": eid,
                    "source_tasks": [t["id"] for t in (list_tasks or r_tasks[:1])],
                    "request": {
                        "query": [
                            {"name": "page", "type": "int", "default": 1},
                            {"name": "limit", "type": "int", "default": 20},
                        ] + [{"name": f["name"], "type": f["type"], "required": False,
                              "filterable": True, "label": f["label"]}
                             for f in filters]
                    },
                    "response": {"type": "paginated_list", "item_entity": eid},
                })

            if detail_tasks:
                api_counter += 1
                endpoints.append({
                    "id": f"API{api_counter:03d}",
                    "method": "GET",
                    "path": f"{path_base}/:id",
                    "name_zh": f"获取{entity['name_zh']}详情",
                    "type": "detail",
                    "entity_ref": eid,
                    "source_tasks": [t["id"] for t in detail_tasks],
                    "request": {"params": [{"name": "id", "type": "uuid", "required": True}]},
                    "response": {"type": "object", "entity_ref": eid},
                })

        # C tasks → POST create
        if "C" in task_cruds:
            api_counter += 1
            writable_fields = [f for f in entity["fields"]
                                if not f.get("pk") and not f.get("auto") and f["name"] != "status"]
            endpoints.append({
                "id": f"API{api_counter:03d}",
                "method": "POST",
                "path": path_base,
                "name_zh": f"创建{entity['name_zh']}",
                "type": "create",
                "entity_ref": eid,
                "source_tasks": [t["id"] for t in task_cruds["C"]],
                "request": {
                    "body": [{"name": f["name"], "type": f["type"],
                              "required": f.get("required", False), "label": f.get("label", f["name"])}
                             for f in writable_fields]
                },
                "response": {"type": "object", "entity_ref": eid},
            })

        # U tasks → PUT/PATCH update (split: field edit vs state transition)
        if "U" in task_cruds:
            field_edit_tasks = [t for t in task_cruds["U"] if not is_state_transition(t.get("name", ""))]
            if field_edit_tasks:
                api_counter += 1
                writable_fields = [f for f in entity["fields"]
                                    if not f.get("pk") and not f.get("auto") and f["name"] != "status"]
                endpoints.append({
                    "id": f"API{api_counter:03d}",
                    "method": "PUT",
                    "path": f"{path_base}/:id",
                    "name_zh": f"更新{entity['name_zh']}",
                    "type": "update",
                    "entity_ref": eid,
                    "source_tasks": [t["id"] for t in field_edit_tasks],
                    "request": {
                        "params": [{"name": "id", "type": "uuid", "required": True}],
                        "body": [{"name": f["name"], "type": f["type"],
                                  "required": False, "label": f.get("label", f["name"])}
                                 for f in writable_fields]
                    },
                    "response": {"type": "object", "entity_ref": eid},
                })

        # D tasks → DELETE
        if "D" in task_cruds:
            api_counter += 1
            endpoints.append({
                "id": f"API{api_counter:03d}",
                "method": "DELETE",
                "path": f"{path_base}/:id",
                "name_zh": f"删除{entity['name_zh']}",
                "type": "delete",
                "entity_ref": eid,
                "source_tasks": [t["id"] for t in task_cruds["D"]],
                "request": {"params": [{"name": "id", "type": "uuid", "required": True}]},
                "response": {"type": "empty"},
            })

        # State transition tasks → PATCH /entity/:id/action
        if entity.get("state_machine"):
            for trans in entity["state_machine"]["transitions"]:
                api_counter += 1
                action = trans["action"]
                # Check if this transition needs input
                task = tasks_inv.get(trans.get("task_ref", ""), {})
                input_fields = extract_field_hints(task.get("name", ""))
                req = {"params": [{"name": "id", "type": "uuid", "required": True}]}
                if input_fields:
                    req["body"] = [{"name": f["name"], "type": f["type"],
                                    "required": f["required"], "label": f["source_hint"]}
                                   for f in input_fields]
                endpoints.append({
                    "id": f"API{api_counter:03d}",
                    "method": "PATCH",
                    "path": f"{path_base}/:id/{action}",
                    "name_zh": trans.get("label", action),
                    "type": "state_transition",
                    "entity_ref": eid,
                    "source_tasks": [trans.get("task_ref", "")],
                    "action": action,
                    "request": req,
                    "response": {"type": "object", "entity_ref": eid},
                })

    return endpoints


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: gen_data_model.py <BASE_PATH> [--mode auto]")
        sys.exit(1)

    BASE = sys.argv[1]

    # Load inputs
    tasks_inv = C.load_task_inventory(BASE)
    flows = C.load_business_flows(BASE)
    roles = C.load_role_profiles(BASE)
    constraints_data = C.load_json(os.path.join(BASE, "product-map/constraints.json"))
    constraints = constraints_data.get("constraints", []) if constraints_data else []

    if not tasks_inv:
        print("ERROR: task-inventory.json not found or empty.", file=sys.stderr)
        sys.exit(1)

    # Group tasks by module
    tasks_by_module = {}
    for tid, task in tasks_inv.items():
        module = task.get("module", task.get("owner_role", "unknown"))
        tasks_by_module.setdefault(module, []).append({**task, "id": tid})

    # Infer entities
    entities = infer_entities(tasks_by_module, flows, constraints)
    relationships = infer_relationships(entities, flows)

    # Infer API contracts
    endpoints = infer_api_contracts(entities, tasks_inv)

    # Write entity-model.json
    out_dir = os.path.join(BASE, "product-map")
    entity_model = {
        "entities": entities,
        "relationships": relationships,
        "generated_at": datetime.datetime.now().isoformat(),
    }
    em_path = C.write_json(os.path.join(out_dir, "entity-model.json"), entity_model)

    # Write api-contracts.json
    api_contracts = {
        "endpoints": endpoints,
        "generated_at": datetime.datetime.now().isoformat(),
    }
    api_path = C.write_json(os.path.join(out_dir, "api-contracts.json"), api_contracts)

    # Write report
    report = [
        "# Data Model Report\n",
        f"> Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n",
        f"## Summary\n",
        f"- Entities: {len(entities)}",
        f"- Relationships: {len(relationships)}",
        f"- API Endpoints: {len(endpoints)}\n",
    ]
    for e in entities:
        sm = " (has state machine)" if e.get("state_machine") else ""
        report.append(f"### {e['id']} {e['name_zh']}{sm}")
        report.append(f"- Fields: {len(e['fields'])}")
        report.append(f"- CRUD: {', '.join(e['crud_operations'])}")
        report.append(f"- Tasks: {', '.join(e['source_tasks'])}")
        for f in e["fields"]:
            req = " *" if f.get("required") else ""
            pk = " (PK)" if f.get("pk") else ""
            auto = " (auto)" if f.get("auto") else ""
            report.append(f"  - {f['name']}: {f['type']}{req}{pk}{auto}")
        report.append("")

    report.append("## API Endpoints\n")
    for ep in endpoints:
        report.append(f"- `{ep['method']} {ep['path']}` — {ep['name_zh']} ({ep['id']})")
    report.append("")

    report.append("## Relationships\n")
    for r in relationships:
        report.append(f"- {r['from_name']} → {r['to_name']} ({r['type']}, FK: {r['fk']})")

    rpt_path = os.path.join(out_dir, "data-model-report.md")
    with open(rpt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report))

    total_fields = sum(len(e["fields"]) for e in entities)
    print(f"OK: {em_path} ({len(entities)} entities, {total_fields} fields)")
    print(f"OK: {api_path} ({len(endpoints)} endpoints)")
    print(f"OK: {rpt_path}")

    C.append_pipeline_decision(BASE, "data-model", {
        "entity_count": len(entities),
        "relationship_count": len(relationships),
        "endpoint_count": len(endpoints),
        "total_fields": total_fields,
    })


if __name__ == "__main__":
    main()
```

**Step 3: Run with test fixture**

Run: `python3 product-design-skill/scripts/gen_data_model.py /tmp/test-dm/.allforai`
Expected: `OK: ... (2 entities, N fields)` + `OK: ... (N endpoints)`

**Step 4: Verify output files**

Run: `cat /tmp/test-dm/.allforai/product-map/entity-model.json | python3 -m json.tool | head -30`
Expected: Valid JSON with `entities` array containing order + product entities

Run: `cat /tmp/test-dm/.allforai/product-map/api-contracts.json | python3 -m json.tool | head -30`
Expected: Valid JSON with `endpoints` array

**Step 5: Commit**

```bash
git add product-design-skill/scripts/gen_data_model.py
git commit -m "feat(product-design): add gen_data_model.py for Step 7 entity+API inference"
```

---

## Task 3: gen_view_objects.py — Step 8 VO Generation + Action Bindings

**Files:**
- Create: `product-design-skill/scripts/gen_view_objects.py`

**Step 1: Write gen_view_objects.py**

Create `product-design-skill/scripts/gen_view_objects.py`:

```python
#!/usr/bin/env python3
"""Step 8: Generate view-objects.json from entity-model + api-contracts + tasks.

Each task CRUD operation on an entity produces a View Object (VO) with:
- Fields (what the UI shows/edits)
- Action Bindings (buttons/links with full behavior chains)
- interaction_type inference

Usage:
    python3 gen_view_objects.py <BASE_PATH> [--mode auto]
"""
import sys, os, json, datetime

sys.path.insert(0, os.path.dirname(__file__))
import _common as C

# ── CRUD → VO type mapping ──────────────────────────────────────────────────

CRUD_KEYWORDS = {
    "C": ["新增", "创建", "添加", "注册", "上传", "发布", "录入",
          "create", "add", "new", "register", "upload"],
    "U": ["修改", "编辑", "更新", "调整", "设置", "配置",
          "update", "edit", "modify", "configure", "set"],
    "D": ["删除", "移除", "撤销", "取消",
          "remove", "delete", "cancel", "revoke"],
    "R": ["查看", "浏览", "搜索", "筛选", "导出", "统计", "列表", "详情",
          "view", "list", "search", "filter", "export", "detail"],
}

STATE_KEYWORDS = ["审核", "审批", "确认", "发货", "签收", "上架", "下架",
                  "冻结", "解冻", "激活", "禁用", "关闭", "打回", "驳回",
                  "approve", "reject", "ship", "deliver", "freeze", "activate"]

# Field type → input widget mapping
INPUT_WIDGET_MAP = {
    "string": "text",
    "text": "textarea",
    "integer": "number",
    "decimal": "number",
    "enum": "select",
    "boolean": "checkbox",
    "date": "date_picker",
    "datetime": "datetime_picker",
    "file": "file_upload",
    "file[]": "multi_file_upload",
    "string[]": "tag_input",
    "uuid": "text",
}

# Field type → display format mapping
DISPLAY_FORMAT_MAP = {
    "string": "text",
    "text": "text",
    "integer": "number",
    "decimal": "number",
    "enum": "status_badge",
    "boolean": "boolean_badge",
    "date": "date",
    "datetime": "relative_time",
    "file": "thumbnail",
    "file[]": "thumbnail_grid",
    "string[]": "tag_list",
    "uuid": "text",
}

# Name suffix → VO type
NAME_SUFFIX_MAP = {
    "list_item": "列表",
    "detail": "详情",
    "create_form": "创建表单",
    "edit_form": "编辑表单",
    "delete_confirm": "删除确认",
    "state_action": "状态操作",
}


def infer_crud(task_name):
    for crud, keywords in CRUD_KEYWORDS.items():
        for kw in keywords:
            if kw in task_name.lower():
                return crud
    return "R"


def is_state_transition(task_name):
    return any(kw in task_name.lower() for kw in STATE_KEYWORDS)


def is_list_task(task_name):
    return any(kw in task_name for kw in ["列表", "查看", "浏览", "搜索", "筛选", "list", "browse"])


def is_detail_task(task_name):
    return any(kw in task_name for kw in ["详情", "detail"])


def find_api_for_task(task_id, endpoints):
    """Find API endpoint that references this task."""
    for ep in endpoints:
        if task_id in ep.get("source_tasks", []):
            return ep
    return None


def find_apis_for_entity(entity_id, endpoints):
    """Find all API endpoints for an entity."""
    return [ep for ep in endpoints if ep.get("entity_ref") == entity_id]


# ── VO generation ────────────────────────────────────────────────────────────

def generate_view_objects(entities, endpoints, tasks_inv):
    """Generate view objects from entities, APIs, and tasks."""
    view_objects = []
    vo_counter = 0
    entity_by_id = {e["id"]: e for e in entities}

    for entity in entities:
        eid = entity["id"]
        module = entity["source_module"]
        name_zh = entity["name_zh"]
        fields = entity["fields"]
        entity_apis = find_apis_for_entity(eid, endpoints)

        # Track which tasks have been assigned to VOs
        assigned_tasks = set()

        # R-list tasks → ListItemVO
        list_tasks = []
        detail_tasks = []
        create_tasks = []
        edit_tasks = []
        delete_tasks = []
        state_tasks = []

        for tid in entity["source_tasks"]:
            task = tasks_inv.get(tid, {})
            tname = task.get("name", "")
            crud = infer_crud(tname)

            if is_state_transition(tname):
                state_tasks.append(tid)
            elif crud == "R" and is_detail_task(tname):
                detail_tasks.append(tid)
            elif crud == "R":
                list_tasks.append(tid)
            elif crud == "C":
                create_tasks.append(tid)
            elif crud == "U":
                edit_tasks.append(tid)
            elif crud == "D":
                delete_tasks.append(tid)

        # ── ListItemVO ──
        if list_tasks or "R" in entity.get("crud_operations", []):
            vo_counter += 1
            vo_id = f"VO{vo_counter:03d}"
            # List shows subset of fields: no text, no file[], no auto
            list_fields = []
            for f in fields:
                if f.get("auto") and f["name"] not in ("status",):
                    continue
                if f["type"] in ("text", "file[]", "file"):
                    continue
                if f.get("pk"):
                    list_fields.append({
                        "name": f["name"], "label": f.get("label", f["name"]),
                        "type": f["type"], "display": "text",
                        "sortable": True, "width": "120px",
                    })
                elif f["type"] == "enum":
                    list_fields.append({
                        "name": f["name"], "label": f.get("label", f["name"]),
                        "type": f["type"], "display": "status_badge",
                        "sortable": True,
                        "values": f.get("values", []),
                    })
                elif f["type"] == "decimal":
                    list_fields.append({
                        "name": f["name"], "label": f.get("label", f["name"]),
                        "type": f["type"], "display": "currency",
                        "sortable": True, "align": "right",
                    })
                else:
                    list_fields.append({
                        "name": f["name"], "label": f.get("label", f["name"]),
                        "type": f["type"],
                        "display": DISPLAY_FORMAT_MAP.get(f["type"], "text"),
                    })

            # Filters from enum fields
            filters = [{"field": f["name"], "input": "select",
                         "label": f.get("label", f["name"]),
                         "options_from": f"E.{f['name']}.values"}
                        for f in fields if f["type"] == "enum"]

            # Row actions
            row_actions = []
            if detail_tasks:
                row_actions.append("view_detail")
            if edit_tasks:
                row_actions.append("edit")
            if delete_tasks:
                row_actions.append("delete")

            # Find matching API
            list_api = next((ep for ep in entity_apis if ep["type"] == "list"), None)

            # Action bindings for toolbar
            actions = []
            if create_tasks:
                create_api = next((ep for ep in entity_apis if ep["type"] == "create"), None)
                actions.append({
                    "id": f"ACT_{vo_id}_create",
                    "label": f"新建{name_zh}",
                    "type": "navigate",
                    "trigger": "toolbar_button",
                    "target_vo": None,  # will be linked to CreateFormVO
                    "nav_mode": "push",
                    "style": "primary",
                    "frequency": "high",
                })

            # Row-level action bindings
            if detail_tasks:
                detail_api = next((ep for ep in entity_apis if ep["type"] == "detail"), None)
                actions.append({
                    "id": f"ACT_{vo_id}_detail",
                    "label": "查看详情",
                    "type": "navigate",
                    "trigger": "row_click",
                    "target_vo": None,  # linked to DetailVO
                    "nav_mode": "push",
                    "params": {"id": "$row.id"},
                    "data_load": {"api_ref": detail_api["id"]} if detail_api else None,
                    "style": "ghost",
                    "frequency": "high",
                })

            if delete_tasks:
                delete_api = next((ep for ep in entity_apis if ep["type"] == "delete"), None)
                actions.append({
                    "id": f"ACT_{vo_id}_delete",
                    "label": "删除",
                    "type": "api_call",
                    "trigger": "row_action",
                    "api_ref": delete_api["id"] if delete_api else None,
                    "api_params": {"id": "$row.id"},
                    "confirm": {"title": f"确认删除", "message": f"删除后不可恢复，确认删除该{name_zh}？"},
                    "on_success": {"action": "refresh_list", "toast": "删除成功"},
                    "on_error": {"action": "show_error"},
                    "style": "danger",
                    "frequency": "low",
                })

            has_row_actions = bool(row_actions)
            interaction_type = "MG2-L" if has_row_actions else "MG1"

            vo = {
                "id": vo_id,
                "name": f"{module.title()}ListItem",
                "name_zh": f"{name_zh}列表",
                "entity_ref": eid,
                "view_type": "list_item",
                "interaction_type": interaction_type,
                "source_tasks": list_tasks or [entity["source_tasks"][0]],
                "api_ref": list_api["id"] if list_api else None,
                "fields": list_fields,
                "filters": filters,
                "row_actions": row_actions,
                "actions": actions,
            }
            view_objects.append(vo)
            # Link create action target
            # (will be patched after CreateFormVO is generated)

        # ── DetailVO ──
        if detail_tasks:
            vo_counter += 1
            vo_id = f"VO{vo_counter:03d}"
            detail_fields = []
            for f in fields:
                detail_fields.append({
                    "name": f["name"], "label": f.get("label", f["name"]),
                    "type": f["type"],
                    "display": DISPLAY_FORMAT_MAP.get(f["type"], "text"),
                    "read_only": True,
                })

            detail_api = next((ep for ep in entity_apis if ep["type"] == "detail"), None)

            # Actions from detail page
            detail_actions = []
            if edit_tasks:
                detail_actions.append({
                    "id": f"ACT_{vo_id}_edit",
                    "label": f"编辑{name_zh}",
                    "type": "navigate",
                    "trigger": "button",
                    "target_vo": None,
                    "nav_mode": "push",
                    "params": {"id": "$current.id"},
                    "style": "secondary",
                    "frequency": "medium",
                })
            if state_tasks:
                for stid in state_tasks:
                    st = tasks_inv.get(stid, {})
                    st_api = find_api_for_task(stid, endpoints)
                    detail_actions.append({
                        "id": f"ACT_{vo_id}_{stid}",
                        "label": st.get("name", stid),
                        "type": "api_call",
                        "trigger": "button",
                        "api_ref": st_api["id"] if st_api else None,
                        "api_params": {"id": "$current.id"},
                        "on_success": {"action": "refresh_detail", "toast": f"{st.get('name', '')}成功"},
                        "on_error": {"action": "show_error"},
                        "style": "primary",
                        "frequency": "medium",
                    })

            vo = {
                "id": vo_id,
                "name": f"{module.title()}Detail",
                "name_zh": f"{name_zh}详情",
                "entity_ref": eid,
                "view_type": "detail",
                "interaction_type": "MG2-D",
                "source_tasks": detail_tasks,
                "api_ref": detail_api["id"] if detail_api else None,
                "fields": detail_fields,
                "actions": detail_actions,
            }
            view_objects.append(vo)

        # ── CreateFormVO ──
        if create_tasks:
            vo_counter += 1
            vo_id = f"VO{vo_counter:03d}"
            form_fields = []
            for f in fields:
                if f.get("pk") or f.get("auto"):
                    continue
                if f["name"] == "status":
                    continue  # status set by backend
                form_fields.append({
                    "name": f["name"], "label": f.get("label", f["name"]),
                    "type": f["type"],
                    "input": INPUT_WIDGET_MAP.get(f["type"], "text"),
                    "required": f.get("required", False),
                    "placeholder": f"请输入{f.get('label', f['name'])}",
                })

            create_api = next((ep for ep in entity_apis if ep["type"] == "create"), None)

            vo = {
                "id": vo_id,
                "name": f"{module.title()}CreateForm",
                "name_zh": f"{name_zh}创建表单",
                "entity_ref": eid,
                "view_type": "create_form",
                "interaction_type": "MG2-C",
                "source_tasks": create_tasks,
                "api_ref": create_api["id"] if create_api else None,
                "fields": form_fields,
                "actions": [
                    {
                        "id": f"ACT_{vo_id}_submit",
                        "label": f"创建{name_zh}",
                        "type": "api_call",
                        "trigger": "button",
                        "api_ref": create_api["id"] if create_api else None,
                        "api_params": {f["name"]: f"$form.{f['name']}" for f in form_fields},
                        "on_success": {"action": "navigate_back", "toast": f"创建成功"},
                        "on_error": {"action": "show_field_errors"},
                        "style": "primary",
                        "frequency": "high",
                    },
                    {
                        "id": f"ACT_{vo_id}_cancel",
                        "label": "取消",
                        "type": "navigate",
                        "trigger": "button",
                        "nav_mode": "back",
                        "style": "ghost",
                        "frequency": "high",
                    },
                ],
                "submit_label": f"创建{name_zh}",
                "cancel_label": "取消",
            }
            view_objects.append(vo)

        # ── EditFormVO ──
        if edit_tasks:
            vo_counter += 1
            vo_id = f"VO{vo_counter:03d}"
            form_fields = []
            for f in fields:
                if f.get("pk") or f.get("auto"):
                    continue
                if f["name"] == "status":
                    continue
                form_fields.append({
                    "name": f["name"], "label": f.get("label", f["name"]),
                    "type": f["type"],
                    "input": INPUT_WIDGET_MAP.get(f["type"], "text"),
                    "required": f.get("required", False),
                    "prefill": True,  # key difference from create
                    "placeholder": f"请输入{f.get('label', f['name'])}",
                })

            update_api = next((ep for ep in entity_apis if ep["type"] == "update"), None)
            detail_api = next((ep for ep in entity_apis if ep["type"] == "detail"), None)

            vo = {
                "id": vo_id,
                "name": f"{module.title()}EditForm",
                "name_zh": f"{name_zh}编辑表单",
                "entity_ref": eid,
                "view_type": "edit_form",
                "interaction_type": "MG2-E",
                "source_tasks": edit_tasks,
                "api_ref": update_api["id"] if update_api else None,
                "data_load": {"api_ref": detail_api["id"]} if detail_api else None,
                "fields": form_fields,
                "actions": [
                    {
                        "id": f"ACT_{vo_id}_submit",
                        "label": f"保存",
                        "type": "api_call",
                        "trigger": "button",
                        "api_ref": update_api["id"] if update_api else None,
                        "api_params": {"id": "$current.id",
                                       **{f["name"]: f"$form.{f['name']}" for f in form_fields}},
                        "on_success": {"action": "navigate_back", "toast": "保存成功"},
                        "on_error": {"action": "show_field_errors"},
                        "style": "primary",
                        "frequency": "high",
                    },
                    {
                        "id": f"ACT_{vo_id}_cancel",
                        "label": "取消",
                        "type": "navigate",
                        "trigger": "button",
                        "nav_mode": "back",
                        "style": "ghost",
                        "frequency": "high",
                    },
                ],
                "submit_label": "保存",
                "cancel_label": "取消",
            }
            view_objects.append(vo)

        # ── StateActionVO ──
        if state_tasks and entity.get("state_machine"):
            vo_counter += 1
            vo_id = f"VO{vo_counter:03d}"

            # Build actions by state
            state_actions = []
            for stid in state_tasks:
                st = tasks_inv.get(stid, {})
                st_api = find_api_for_task(stid, endpoints)
                # Check if needs input
                input_fields = []
                if st_api and st_api.get("request", {}).get("body"):
                    for bf in st_api["request"]["body"]:
                        input_fields.append({
                            "name": bf["name"], "label": bf.get("label", bf["name"]),
                            "input": INPUT_WIDGET_MAP.get(bf["type"], "text"),
                            "required": bf.get("required", False),
                        })

                action = {
                    "id": f"ACT_{vo_id}_{stid}",
                    "label": st.get("name", stid),
                    "type": "api_call",
                    "trigger": "row_action",
                    "api_ref": st_api["id"] if st_api else None,
                    "api_params": {"id": "$row.id"},
                    "on_success": {"action": "refresh_row", "toast": f"{st.get('name', '')}成功"},
                    "on_error": {"action": "show_error"},
                    "style": "primary",
                    "frequency": "medium",
                }
                if input_fields:
                    action["input_form"] = {"fields": input_fields}
                state_actions.append(action)

            # Display fields (subset for state management view)
            display_fields = [
                {"name": f["name"], "label": f.get("label", f["name"]),
                 "type": f["type"], "display": DISPLAY_FORMAT_MAP.get(f["type"], "text")}
                for f in fields
                if f.get("pk") or f["name"] == "status" or f["type"] == "decimal"
            ]

            vo = {
                "id": vo_id,
                "name": f"{module.title()}StateAction",
                "name_zh": f"{name_zh}状态操作",
                "entity_ref": eid,
                "view_type": "state_action",
                "interaction_type": "MG3",
                "source_tasks": state_tasks,
                "fields": display_fields,
                "state_machine_ref": f"{eid}.state_machine",
                "actions": state_actions,
            }
            view_objects.append(vo)

    # Cross-link VO references (create button → create form VO, etc.)
    vo_by_entity_type = {}
    for vo in view_objects:
        key = (vo["entity_ref"], vo["view_type"])
        vo_by_entity_type[key] = vo["id"]

    for vo in view_objects:
        for act in vo.get("actions", []):
            if act.get("type") == "navigate" and act.get("target_vo") is None:
                # Infer target VO from action label
                label = act.get("label", "")
                eid = vo["entity_ref"]
                if "新建" in label or "创建" in label:
                    act["target_vo"] = vo_by_entity_type.get((eid, "create_form"))
                elif "编辑" in label:
                    act["target_vo"] = vo_by_entity_type.get((eid, "edit_form"))
                elif "详情" in label:
                    act["target_vo"] = vo_by_entity_type.get((eid, "detail"))

    return view_objects


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: gen_view_objects.py <BASE_PATH> [--mode auto]")
        sys.exit(1)

    BASE = sys.argv[1]

    entities, relationships = C.load_entity_model(BASE)
    endpoints = C.load_api_contracts(BASE)
    tasks_inv = C.load_task_inventory(BASE)

    if not entities:
        print("ERROR: entity-model.json not found or empty. Run gen_data_model.py first.", file=sys.stderr)
        sys.exit(1)

    view_objects = generate_view_objects(entities, endpoints, tasks_inv)

    out_dir = os.path.join(BASE, "product-map")
    result = {
        "view_objects": view_objects,
        "generated_at": datetime.datetime.now().isoformat(),
    }
    out_path = C.write_json(os.path.join(out_dir, "view-objects.json"), result)

    # Count by type
    type_counts = {}
    for vo in view_objects:
        vt = vo["view_type"]
        type_counts[vt] = type_counts.get(vt, 0) + 1

    type_summary = ", ".join(f"{k}:{v}" for k, v in sorted(type_counts.items()))
    print(f"OK: {out_path} ({len(view_objects)} VOs: {type_summary})")

    C.append_pipeline_decision(BASE, "view-objects", {
        "vo_count": len(view_objects),
        "type_distribution": type_counts,
    })


if __name__ == "__main__":
    main()
```

**Step 2: Run with test fixture (requires Task 2 output)**

Run: `python3 product-design-skill/scripts/gen_view_objects.py /tmp/test-dm/.allforai`
Expected: `OK: ... (N VOs: list_item:2, create_form:2, ...)`

**Step 3: Verify output**

Run: `python3 -c "import json; d=json.load(open('/tmp/test-dm/.allforai/product-map/view-objects.json')); print(len(d['view_objects']), 'VOs'); [print(f'  {v[\"id\"]} {v[\"name_zh\"]} ({v[\"interaction_type\"]})') for v in d['view_objects']]"`
Expected: List of VOs with meaningful Chinese names and correct interaction_types

**Step 4: Commit**

```bash
git add product-design-skill/scripts/gen_view_objects.py
git commit -m "feat(product-design): add gen_view_objects.py for Step 8 VO+Action Binding generation"
```

---

## Task 4: datamodel_review_server.py — Mind Map Review Gate

**Files:**
- Create: `product-design-skill/scripts/datamodel_review_server.py`
- Reference: `product-design-skill/scripts/mindmap_review_server.py` (copy pattern)

**Step 1: Write datamodel_review_server.py**

This server follows the exact same pattern as `mindmap_review_server.py` but loads entity-model + api-contracts + view-objects and builds a custom tree. The server is ~600 lines because it includes the full HTML/CSS/JS mind map UI (copied from the existing mindmap server with different node types and colors).

Create `product-design-skill/scripts/datamodel_review_server.py`:

The structure should be:
1. Load data: `C.load_entity_model(BASE)`, `C.load_api_contracts(BASE)`, `C.load_view_objects(BASE)`
2. Build tree with `_node()` helper (same pattern as mindmap_review_server.py):
   - Root: "数据模型"
   - Per entity: entity node with children:
     - "字段" group → field nodes (with type/required/PK tags)
     - "状态机" group → transition nodes (if entity has state_machine)
     - "接口" group → API endpoint nodes (with method badge)
     - "视图" group → VO nodes with children:
       - VO field nodes
       - Action binding nodes
   - "关系" group → relationship nodes
3. HTTP handler: same as mindmap_review_server.py (GET /, POST /api/feedback, POST /api/submit)
4. HTML: reuse the radial mind map SVG layout from mindmap_review_server.py with additional node type styles:
   - `entity`: blue border
   - `field`: white with type tag
   - `field-pk`: gold border
   - `field-required`: red asterisk
   - `api`: green badge with HTTP method
   - `vo`: purple badge with interaction_type
   - `action`: orange badge with api_ref
   - `transition`: teal arrow style
   - `relation`: orange dashed line

5. Feedback: `{round, submitted_at, source: "data-model", nodes: {node_id: {status, comments: [{id, text, category}]}}}`
6. Categories: entity, api, vo, action, state-machine, product-map
7. Output: `.allforai/data-model-review/review-feedback.json`

**Implementation approach:** Copy `mindmap_review_server.py`, replace `load_concept_tree()` and `load_product_map_tree()` with `load_data_model_tree()`. Change SOURCE to "data-model", PORT to 18904. Update node type CSS colors. Keep all other HTML/JS/CSS identical.

**Step 2: Test server startup**

Run: `python3 product-design-skill/scripts/datamodel_review_server.py /tmp/test-dm/.allforai --no-open true &`
Then: `curl -s http://localhost:18904/ | head -5`
Expected: HTML page starts with `<!DOCTYPE html>`
Cleanup: `kill %1`

**Step 3: Commit**

```bash
git add product-design-skill/scripts/datamodel_review_server.py
git commit -m "feat(product-design): add datamodel_review_server.py for data-model mind map review"
```

---

## Task 5: data-model-review Command

**Files:**
- Create: `product-design-skill/commands/data-model-review.md`

**Step 1: Write command file**

Create `product-design-skill/commands/data-model-review.md`:

```markdown
---
name: data-model-review
description: >
  Use when the user says "data-model-review", "review data model", "数据模型审核",
  "审核数据模型", "审核实体", "审核接口", "review entities", "review APIs",
  "review view objects", "data model mind map".
  Interactive mind map review of data model — validate entities, fields,
  API contracts, and view objects before proceeding to experience-map.
arguments:
  - name: mode
    description: "start (launch review server) | process (read feedback and route)"
    required: false
    default: "start"
---

# Data Model Review — 数据模型脑图审核

## 模式

| 模式 | 触发 | 行为 |
|------|------|------|
| `start` | `/data-model-review` 或 `/data-model-review start` | 启动脑图审核服务器 |
| `process` | `/data-model-review process` | 读取反馈，汇总修改建议 |

---

## Mode: start

启动数据模型脑图审核服务器，展示实体-字段-接口-视图对象的树形结构。

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/datamodel_review_server.py <BASE> --port 18904
```

- 服务器启动后会自动打开浏览器，**禁止**再用 Playwright `browser_navigate` 或其他方式重复打开同一 URL
- 脑图包含：
  - 实体列表（字段、类型、约束）
  - 状态机（状态流转规则）
  - API 接口（method + path + 请求/响应）
  - 视图对象（VO 字段 + Action Binding）
  - 实体关系（1:N / N:N）
- 点击任意节点展开/折叠子树
- 点击节点添加评论，选择评论类别：
  - `entity`: 实体定义问题
  - `api`: 接口设计问题
  - `vo`: 视图对象问题
  - `action`: Action Binding 问题
  - `state-machine`: 状态机问题
  - `product-map`: 根源性问题（需回到产品地图）
- 审核完毕点击 "Submit Feedback" → 生成反馈文件 → 服务器自动关闭
- **服务器退出后**：Bash 输出包含反馈摘要，**自动进入 process 模式**

---

## Mode: process

读取 `.allforai/data-model-review/review-feedback.json`，汇总反馈。

### 流程

```
1. 读取 .allforai/data-model-review/review-feedback.json
   - 不存在 → 提示先运行 /data-model-review start
   - submitted_at = null → 提示先提交反馈

2. 统计：N 个节点已审核，M 个通过，K 个需修改

3. K = 0 → 数据模型确认，进入 journey-emotion → experience-map

4. K > 0 → 按类别汇总修改建议：
   - entity/api/state-machine 类 → 修改 entity-model.json，重跑 Step 7
   - vo/action 类 → 修改 view-objects.json，重跑 Step 8
   - product-map 类 → 回到 /product-map 修改，重跑全链
   - 提示用户修改后重跑对应步骤

5. 更新 review-feedback.json: round += 1
```

### 安全护栏

- 不直接修改 data-model 产物
- 只输出修复建议，由用户决定
```

**Step 2: Commit**

```bash
git add product-design-skill/commands/data-model-review.md
git commit -m "feat(product-design): add /data-model-review command"
```

---

## Task 6: gen_experience_map.py — Consume VOs

**Files:**
- Modify: `product-design-skill/scripts/gen_experience_map.py`

**Step 1: Add VO loading and matching**

In `gen_experience_map.py`, after the existing imports (line 13), add VO loading capability. Then modify `build_screens_for_node` to use VOs when available.

Key changes to `main()` (around line 151):
- After loading tasks_inv, also load view_objects (optional, fallback to current behavior)
- Pass view_objects into `build_screens_for_node`

Key changes to `build_screens_for_node` (line 91-141):
- Accept new `view_objects` parameter
- For each screen's task_ids, find matching VO via `source_tasks`
- If VO found: use VO's `name_zh`, `interaction_type`, `fields`, `actions`
- If no VO found: fall back to current behavior (backward compatible)

Add new fields to each screen dict:
- `vo_ref`: VO ID
- `api_ref`: API endpoint ID
- `interaction_type`: from VO
- `data_fields`: from VO fields
- `states`: default state descriptions per interaction_type

Add `flow_context` computation after all screens are generated (prev/next from operation line sequence).

**Step 2: Run with test fixture**

First need journey-emotion-map.json for test. Create `/tmp/test-dm/.allforai/experience-map/journey-emotion-map.json`:
```json
{
  "journey_lines": [
    {
      "id": "JL01",
      "name": "订单购买旅程",
      "role": "买家",
      "source_flow": "F001",
      "emotion_nodes": [
        {"step": 1, "action": "创建订单", "emotion": "exploring", "intensity": 5, "design_hint": "简化下单流程"},
        {"step": 2, "action": "确认支付", "emotion": "anxious", "intensity": 7, "design_hint": "明确支付安全"},
        {"step": 3, "action": "发货", "emotion": "curious", "intensity": 4, "design_hint": "物流追踪"},
        {"step": 4, "action": "确认收货", "emotion": "satisfied", "intensity": 8, "design_hint": "确认流程简化"}
      ]
    }
  ]
}
```

Run: `python3 product-design-skill/scripts/gen_experience_map.py /tmp/test-dm/.allforai`
Expected: `OK: ...` with screens that have `vo_ref`, `interaction_type`, `data_fields` when VOs are available

**Step 3: Verify VO binding**

Run: `python3 -c "import json; d=json.load(open('/tmp/test-dm/.allforai/experience-map/experience-map.json')); screens=[s for ol in d['operation_lines'] for n in ol['nodes'] for s in n['screens']]; [print(f'{s[\"id\"]} {s[\"name\"]} type={s.get(\"interaction_type\",\"NONE\")} vo={s.get(\"vo_ref\",\"NONE\")}') for s in screens]"`
Expected: Screens with real names and VO references (not `{module}_screen`)

**Step 4: Commit**

```bash
git add product-design-skill/scripts/gen_experience_map.py
git commit -m "feat(product-design): gen_experience_map consumes VOs for real field binding"
```

---

## Task 7: wireframe_review_server.py — Interaction-Type Templates + 4D Panel

**Files:**
- Modify: `product-design-skill/scripts/wireframe_review_server.py:122-207`

**Step 1: Replace generate_wireframe with type-dispatch**

Replace the single `generate_wireframe()` function (lines 122-207) with a dispatcher + per-type template functions. The key concept: instead of one gray "Content Area" box for all screens, render actual wireframe elements based on `interaction_type`:

```python
def generate_wireframe(screen):
    """Generate interaction-type-specific wireframe HTML."""
    itype = screen.get("interaction_type", "")

    # Dispatch to type-specific renderer
    if itype.startswith("MG1"):
        return _wf_readonly_list(screen)
    elif itype == "MG2-L":
        return _wf_crud_list(screen)
    elif itype == "MG2-C":
        return _wf_create_form(screen)
    elif itype == "MG2-E":
        return _wf_edit_form(screen)
    elif itype == "MG2-D":
        return _wf_detail(screen)
    elif itype == "MG3":
        return _wf_state_machine(screen)
    elif itype == "MG4":
        return _wf_approval(screen)
    else:
        return _wf_default(screen)
```

Each template function renders real VO fields from `screen["data_fields"]` and action bindings from `screen["actions"]`. All templates share the same wireframe CSS (gray/white style) and include the 4D panel at the bottom.

For the 4D panel, append to every wireframe:
```html
<div class="wf-4d">
  <div class="wf-4d-row"><span class="wf-4d-label">Data</span> {field_summary}</div>
  <div class="wf-4d-row"><span class="wf-4d-label">Action</span> {action_summary}</div>
  <div class="wf-4d-row"><span class="wf-4d-label">State</span> {state_summary}</div>
  <div class="wf-4d-row"><span class="wf-4d-label">Flow</span> {flow_summary}</div>
</div>
```

**Step 2: Update load_data to include VO/API data**

In `load_data()` and `build_screens_with_context()`, also load view-objects.json and api-contracts.json so the wireframe renderer has access to full field and action data.

**Step 3: Test with fixture**

Run wireframe server against the test fixture:
```bash
python3 product-design-skill/scripts/wireframe_review_server.py /tmp/test-dm/.allforai --no-open true &
curl -s http://localhost:18902/wireframe/S001 | grep -o 'wf-table\|wf-form\|wf-4d' | sort -u
kill %1
```
Expected: `wf-4d` + type-specific class (e.g., `wf-table` for list, `wf-form` for form)

**Step 4: Commit**

```bash
git add product-design-skill/scripts/wireframe_review_server.py
git commit -m "feat(product-design): interaction-type wireframe templates + 4D panel"
```

---

## Task 8: wireframe_review_server.py — 6V Tabs in Detail Page

**Files:**
- Modify: `product-design-skill/scripts/wireframe_review_server.py` (render_screen_detail function)

**Step 1: Replace single "Screen Info" panel with 6V tabs**

In `render_screen_detail()` (line 443+), replace the single `<dl>{rationale}</dl>` section with 6 tabbed views:

```html
<div class="tab-bar">
  <button class="tab-btn active" data-tab="structure">Structure</button>
  <button class="tab-btn" data-tab="behavior">Behavior</button>
  <button class="tab-btn" data-tab="data">Data</button>
  <button class="tab-btn" data-tab="state">State</button>
  <button class="tab-btn" data-tab="flow">Flow</button>
  <button class="tab-btn" data-tab="emotion">Emotion</button>
</div>
```

Each tab renders:
- **Structure**: Screen sections inferred from interaction_type (header/filter/content/pagination/action-bar)
- **Behavior**: Interaction type name + description + platform behavior notes
- **Data**: VO field table (name, label, type, input/display, required)
- **State**: 4 state descriptions (empty/loading/error/success)
- **Flow**: Prev/next screen links + entry/exit points
- **Emotion**: Current emotion display (unchanged from existing)

**Step 2: Verify tabs render**

Run: `curl -s http://localhost:18902/screen/S001 | grep -c 'tab-btn'`
Expected: `6`

**Step 3: Commit**

```bash
git add product-design-skill/scripts/wireframe_review_server.py
git commit -m "feat(product-design): 6V tabs in wireframe detail page"
```

---

## Task 9: wireframe_review_server.py — XV Cross-Validation

**Files:**
- Modify: `product-design-skill/scripts/wireframe_review_server.py`

**Step 1: Add XV review on startup**

After loading all screens, if `C.xv_available()`:
1. Build a batch prompt summarizing all screens (name, interaction_type, field count, action count)
2. Call `C.xv_call("wireframe_usability_review", prompt)` — gemini reviews usability
3. Call `C.xv_call("wireframe_completeness_check", prompt)` — deepseek checks coverage
4. Call `C.xv_call("wireframe_consistency_check", prompt)` — gpt checks naming/type consistency
5. Parse results, store in `xv_review.json` under wireframe-review dir
6. Attach per-screen issues to `_all_screens` data

**Step 2: Add XV task types to _common.py XV_ROUTING**

In `_common.py`, add to `XV_ROUTING` dict:
```python
"wireframe_usability_review": "gemini",
"wireframe_completeness_check": "deepseek",
"wireframe_consistency_check": "gpt",
```

**Step 3: Render XV badges on dashboard + XV tab in detail**

- Dashboard: each screen card shows XV issue count badge (red for errors, orange for warnings)
- Detail: add 7th tab "XV Review" showing issues for this screen

**Step 4: Test (only if OPENROUTER_API_KEY is set)**

Run: `OPENROUTER_API_KEY=test python3 -c "import product_design_skill... " ` — verify no crash when key unavailable (graceful skip)

**Step 5: Commit**

```bash
git add product-design-skill/scripts/wireframe_review_server.py product-design-skill/scripts/_common.py
git commit -m "feat(product-design): XV cross-validation for wireframes"
```

---

## Task 10: product-map.md — Add Step 7/8, Renumber Step 9

**Files:**
- Modify: `product-design-skill/skills/product-map.md`

**Step 1: Add Step 7 and Step 8 descriptions**

After the existing Step 7 (validation), renumber it to Step 9. Insert:

**Step 7: 数据建模**
- Description of entity inference, API contract generation
- Script: `gen_data_model.py`
- Output: entity-model.json, api-contracts.json, data-model-report.md
- User confirmation point

**Step 8: 视图对象**
- Description of VO generation from entities + APIs
- Script: `gen_view_objects.py`
- Output: view-objects.json
- User confirmation point
- Note: "完成后运行 /data-model-review 审核数据模型"

**Step 9: 校验** (was Step 7)
- Add data-model validation checks: entity-VO coverage, API completeness, field consistency

**Step 2: Update 快速开始 section**

Change `Step 0-7` references to `Step 0-9`.

**Step 3: Commit**

```bash
git add product-design-skill/skills/product-map.md
git commit -m "feat(product-design): add Step 7 data-model + Step 8 view-objects to product-map"
```

---

## Task 11: experience-map.md + SKILL.md — Update Pipeline Docs

**Files:**
- Modify: `product-design-skill/skills/experience-map.md`
- Modify: `product-design-skill/SKILL.md`

**Step 1: Update experience-map.md**

- Add VO dependency note: "可选加载 view-objects.json（优先使用 VO 绑定真实字段，无 VO 时回退到任务名推导）"
- Document new screen fields: vo_ref, interaction_type, data_fields, flow_context, states

**Step 2: Update SKILL.md**

- Add /data-model-review to pipeline
- Update product-map step count (Step 0–9)
- Add data-model output files to .allforai/ structure

**Step 3: Commit**

```bash
git add product-design-skill/skills/experience-map.md product-design-skill/SKILL.md
git commit -m "docs(product-design): update pipeline docs for data-model + VO flow"
```

---

## Task 12: End-to-End Integration Test

**Files:**
- Test with the `/tmp/test-dm/` fixture from Task 2

**Step 1: Run full pipeline**

```bash
# Step 7: Data model
python3 product-design-skill/scripts/gen_data_model.py /tmp/test-dm/.allforai

# Step 8: View objects
python3 product-design-skill/scripts/gen_view_objects.py /tmp/test-dm/.allforai

# Experience map (consumes VOs)
python3 product-design-skill/scripts/gen_experience_map.py /tmp/test-dm/.allforai
```

Expected: All 3 scripts succeed, screens have real names + VO refs + interaction_types

**Step 2: Verify wireframe rendering**

```bash
python3 product-design-skill/scripts/wireframe_review_server.py /tmp/test-dm/.allforai --no-open true &
sleep 1
# Check a list screen has table wireframe
curl -s http://localhost:18902/wireframe/S001 | grep -c 'wf-table\|wf-field-row\|wf-4d'
# Check dashboard loads
curl -s http://localhost:18902/ | grep -c 'card'
kill %1
```

Expected: Non-zero counts (wireframes have real content, not just "Content Area")

**Step 3: Verify data-model review server**

```bash
python3 product-design-skill/scripts/datamodel_review_server.py /tmp/test-dm/.allforai --no-open true &
sleep 1
curl -s http://localhost:18904/ | grep -c 'mm-node\|entity\|api'
kill %1
```

Expected: Non-zero counts (mind map renders entity/api nodes)

**Step 4: Cleanup test fixture**

```bash
rm -rf /tmp/test-dm
```

**Step 5: Final commit**

```bash
git add -A
git commit -m "test(product-design): verify end-to-end data-model → wireframe pipeline"
```
