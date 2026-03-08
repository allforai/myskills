#!/usr/bin/env python3
"""Step 7: Infer backend entities, fields, state machines, relationships,
and API endpoints from product-map data.

Reads task-inventory.json (required), business-flows.json, constraints.json,
role-profiles.json (all optional). Writes entity-model.json, api-contracts.json,
and data-model-report.md to <BASE>/product-map/.

Usage:
    python3 gen_data_model.py <BASE_PATH> [--mode auto]
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C

# ── CRUD keywords (same as gen_experience_map.py) ────────────────────────────
CRUD_KEYWORDS = {
    "C": ["新增", "创建", "添加", "注册", "上传", "发布", "录入", "create", "add", "new", "register", "upload"],
    "U": ["修改", "编辑", "更新", "调整", "设置", "配置", "update", "edit", "modify", "configure", "set"],
    "D": ["删除", "移除", "撤销", "取消", "remove", "delete", "cancel", "revoke"],
    "R": ["查看", "浏览", "搜索", "筛选", "导出", "统计", "列表", "详情", "view", "list", "search", "filter", "export", "detail"],
}


def infer_crud(task_name):
    """Infer CRUD type from task name keywords."""
    for crud, keywords in CRUD_KEYWORDS.items():
        for kw in keywords:
            if kw in task_name.lower():
                return crud
    return "R"


# ── Field hint patterns ──────────────────────────────────────────────────────
FIELD_HINTS = {
    "价格": ("price", "decimal"),
    "金额": ("amount", "decimal"),
    "图片": ("images", "file[]"),
    "地址": ("address", "string"),
    "状态": ("status", "enum"),
    "名称": ("name", "string"),
    "描述": ("description", "text"),
    "数量": ("quantity", "integer"),
    "备注": ("note", "text"),
    "邮箱": ("email", "string"),
    "标签": ("tags", "string[]"),
    "评分": ("rating", "decimal"),
    "内容": ("content", "text"),
    "分类": ("category", "string"),
    "电话": ("phone", "string"),
    "日期": ("date", "datetime"),
    "时间": ("time", "datetime"),
    "密码": ("password", "string"),
    "头像": ("avatar", "file"),
    "封面": ("cover_image", "file"),
    "链接": ("url", "string"),
    "排序": ("sort_order", "integer"),
    "权重": ("weight", "decimal"),
    "库存": ("stock", "integer"),
}

# ── State transition keywords ────────────────────────────────────────────────
STATE_KEYWORDS = [
    "审核", "确认", "发货", "上架", "下架", "冻结", "解冻",
    "approve", "reject", "ship", "publish", "unpublish", "freeze", "unfreeze",
    "激活", "禁用", "启用", "停用", "关闭", "开启",
    "支付", "退款", "完成", "取消", "驳回", "通过",
    "签收", "退货", "归档",
]


def _matches_state_keyword(task_name):
    """Check if task name contains a state-transition keyword."""
    name_lower = task_name.lower()
    for kw in STATE_KEYWORDS:
        if kw in name_lower:
            return kw
    return None


def _pluralize(name):
    """Simple pluralization for API paths."""
    if name.endswith("s") or name.endswith("x") or name.endswith("sh") or name.endswith("ch"):
        return name + "es"
    return name + "s"


def _infer_transition(keyword):
    """Map a state keyword to (from_state, to_state) pair."""
    transition_map = {
        "创建": ("created", "created"),
        "审核": ("pending", "approved"),
        "确认": ("pending", "confirmed"),
        "支付": ("confirmed", "paid"),
        "发货": ("paid", "shipped"),
        "签收": ("shipped", "received"),
        "完成": ("active", "completed"),
        "取消": ("pending", "cancelled"),
        "退款": ("paid", "refunded"),
        "退货": ("received", "returned"),
        "驳回": ("pending", "rejected"),
        "通过": ("pending", "approved"),
        "上架": ("draft", "active"),
        "下架": ("active", "inactive"),
        "上下架": ("draft", "active"),
        "冻结": ("active", "frozen"),
        "解冻": ("frozen", "active"),
        "激活": ("inactive", "active"),
        "禁用": ("active", "disabled"),
        "启用": ("disabled", "active"),
        "停用": ("active", "suspended"),
        "关闭": ("active", "closed"),
        "开启": ("closed", "active"),
        "归档": ("completed", "archived"),
        "approve": ("pending", "approved"),
        "reject": ("pending", "rejected"),
        "ship": ("paid", "shipped"),
        "publish": ("draft", "active"),
        "unpublish": ("active", "inactive"),
        "freeze": ("active", "frozen"),
        "unfreeze": ("frozen", "active"),
    }
    return transition_map.get(keyword, ("active", keyword))


# ── Setup ────────────────────────────────────────────────────────────────────
BASE, args = C.parse_args()
OUT = os.path.join(BASE, "product-map")
C.ensure_dir(OUT)
NOW = C.now_iso()

# ── Load data ────────────────────────────────────────────────────────────────
tasks = C.load_task_inventory(BASE)  # dict keyed by task ID

# Optional inputs
flows = C.load_business_flows(BASE)

constraints_data = C.load_json(os.path.join(BASE, "product-map/constraints.json"))
constraints_list = []
if constraints_data:
    constraints_list = C.ensure_list(constraints_data, "constraints")

roles_data = C.load_json(os.path.join(BASE, "product-map/role-profiles.json"))
role_map = {}
if roles_data and "roles" in roles_data:
    role_map = {r["id"]: r.get("name", r["id"]) for r in roles_data["roles"]}

# ── Step 1: Group tasks by module → entities ─────────────────────────────────
module_tasks = {}  # module_name → [task_dict]
for tid, task in tasks.items():
    module = task.get("module", "unknown")
    module_tasks.setdefault(module, []).append({**task, "_id": tid})

entities = []
entity_id_map = {}  # module_name → entity_id

for idx, (module, mod_tasks) in enumerate(sorted(module_tasks.items()), start=1):
    eid = f"E{idx:03d}"
    entity_id_map[module] = eid

    # Classify tasks by CRUD
    crud_tasks = {"C": [], "R": [], "U": [], "D": []}
    state_tasks = []
    for t in mod_tasks:
        crud = infer_crud(t.get("name", ""))
        crud_tasks[crud].append(t)
        kw = _matches_state_keyword(t.get("name", ""))
        if kw:
            state_tasks.append((t, kw))

    # ── Infer fields ─────────────────────────────────────────────────────
    fields = [{"name": "id", "type": "uuid", "constraints": ["PK"]}]

    # Timestamp fields based on CRUD presence
    if crud_tasks["C"]:
        fields.append({"name": "created_at", "type": "datetime", "constraints": ["auto"]})
    if crud_tasks["U"]:
        fields.append({"name": "updated_at", "type": "datetime", "constraints": ["auto"]})

    # Scan task names for field hints
    seen_fields = {"id", "created_at", "updated_at"}
    for t in mod_tasks:
        tname = t.get("name", "")
        for keyword, (fname, ftype) in FIELD_HINTS.items():
            if keyword in tname and fname not in seen_fields:
                seen_fields.add(fname)
                field_entry = {"name": fname, "type": ftype, "constraints": []}
                fields.append(field_entry)

    # Apply constraints from constraints.json
    module_constraints = [c for c in constraints_list
                          if c.get("scope", "") == module]
    for con in module_constraints:
        rule = con.get("rule", "")
        # Parse constraint patterns
        if "不能为负" in rule or ">=0" in rule or "> 0" in rule:
            # Find which field this applies to
            matched_field = False
            for keyword, (fname, ftype) in FIELD_HINTS.items():
                if keyword in rule:
                    # Check if field already exists
                    found_in_fields = False
                    for f in fields:
                        if f["name"] == fname:
                            if "min:0" not in f["constraints"]:
                                f["constraints"].append("min:0")
                            found_in_fields = True
                            break
                    if not found_in_fields:
                        # Add the field with constraint
                        seen_fields.add(fname)
                        fields.append({"name": fname, "type": ftype,
                                       "constraints": ["min:0"]})
                    matched_field = True
                    break
            # If no keyword matched, try generic amount
            if not matched_field and "金额" in rule:
                found = False
                for f in fields:
                    if f["name"] == "amount":
                        if "min:0" not in f["constraints"]:
                            f["constraints"].append("min:0")
                        found = True
                        break
                if not found:
                    seen_fields.add("amount")
                    fields.append({"name": "amount", "type": "decimal",
                                   "constraints": ["min:0"]})

    # ── State machine ────────────────────────────────────────────────────
    state_machine = None
    if state_tasks:
        # Add status enum field if not already present
        if "status" not in seen_fields:
            seen_fields.add("status")
            fields.append({"name": "status", "type": "enum", "constraints": []})

        # Build transitions from state keywords
        transitions = []
        states_set = {"created"}  # initial state
        for t, kw in state_tasks:
            # Map keyword to from→to states
            from_state, to_state = _infer_transition(kw)
            states_set.add(from_state)
            states_set.add(to_state)
            transitions.append({
                "from": from_state,
                "to": to_state,
                "trigger": kw,
                "task_ref": t["_id"],
            })

        state_machine = {
            "initial_state": "created",
            "states": sorted(states_set),
            "transitions": transitions,
        }

    # ── Collect owner roles ──────────────────────────────────────────────
    owner_roles = sorted(set(
        role_map.get(t.get("owner_role", ""), t.get("owner_role", ""))
        for t in mod_tasks
    ))

    entity = {
        "id": eid,
        "name": module,
        "name_zh": module,
        "fields": fields,
        "owner_roles": owner_roles,
        "task_count": len(mod_tasks),
        "crud_coverage": {k: len(v) for k, v in crud_tasks.items()},
    }
    if state_machine:
        entity["state_machine"] = state_machine

    entities.append(entity)


# ── Step 2: Infer relationships from business flows ──────────────────────────
relationships = []
rel_seen = set()

for flow in flows:
    nodes = C.get_flow_nodes(flow)
    # Collect entities referenced in this flow
    flow_entities = []
    for node in nodes:
        task_ref = node.get("task_ref", "") if isinstance(node, dict) else node
        if task_ref in tasks:
            module = tasks[task_ref].get("module", "")
            eid = entity_id_map.get(module)
            if eid and eid not in [fe[0] for fe in flow_entities]:
                flow_entities.append((eid, module))

    # Create relationships between consecutive entity pairs in flow
    for i in range(len(flow_entities) - 1):
        e1_id, e1_name = flow_entities[i]
        e2_id, e2_name = flow_entities[i + 1]
        if e1_id == e2_id:
            continue
        pair = tuple(sorted([e1_id, e2_id]))
        if pair not in rel_seen:
            rel_seen.add(pair)
            relationships.append({
                "from_entity": e1_id,
                "from_name": e1_name,
                "to_entity": e2_id,
                "to_name": e2_name,
                "type": "1:N",
                "inferred_from": f"flow:{flow.get('id', '')}",
            })

# ── Write entity-model.json ──────────────────────────────────────────────────
entity_model = {
    "generated_at": NOW,
    "entity_count": len(entities),
    "relationship_count": len(relationships),
    "entities": entities,
    "relationships": relationships,
}
em_path = C.write_json(os.path.join(OUT, "entity-model.json"), entity_model)

# ── Step 3: Infer API contracts ──────────────────────────────────────────────
endpoints = []
ep_counter = 0

for entity in entities:
    eid = entity["id"]
    ename = entity["name"]
    path_base = f"/{_pluralize(ename)}"
    crud = entity["crud_coverage"]

    # Collect enum fields for query params
    enum_fields = [f["name"] for f in entity["fields"]
                   if f["type"] == "enum"]
    # Also add string fields that look filterable
    filterable = enum_fields + [f["name"] for f in entity["fields"]
                                if f["type"] == "string" and f["name"] in ("category", "status")]
    filterable = sorted(set(filterable))

    # R tasks → GET list
    if crud.get("R", 0) > 0:
        ep_counter += 1
        query_params = [{"name": "page", "type": "integer", "required": False},
                        {"name": "page_size", "type": "integer", "required": False}]
        for fp in filterable:
            query_params.append({"name": fp, "type": "string", "required": False})

        endpoints.append({
            "id": f"API-{ep_counter:03d}",
            "method": "GET",
            "path": path_base,
            "summary": f"List {ename}",
            "entity_ref": eid,
            "query_params": query_params,
            "response_type": "array",
        })

        # Check for detail tasks (详情/detail keyword)
        has_detail = any(
            "详情" in t.get("name", "") or "detail" in t.get("name", "").lower()
            for t in module_tasks.get(ename, [])
        )
        if has_detail:
            ep_counter += 1
            endpoints.append({
                "id": f"API-{ep_counter:03d}",
                "method": "GET",
                "path": f"{path_base}/:id",
                "summary": f"Get {ename} detail",
                "entity_ref": eid,
                "query_params": [],
                "response_type": "object",
            })

    # C tasks → POST
    if crud.get("C", 0) > 0:
        ep_counter += 1
        writable_fields = [f["name"] for f in entity["fields"]
                           if f["name"] not in ("id", "created_at", "updated_at")
                           and "auto" not in f.get("constraints", [])
                           and "PK" not in f.get("constraints", [])]
        endpoints.append({
            "id": f"API-{ep_counter:03d}",
            "method": "POST",
            "path": path_base,
            "summary": f"Create {ename}",
            "entity_ref": eid,
            "request_body": writable_fields,
            "response_type": "object",
        })

    # U tasks (non-state) → PUT
    non_state_u = [t for t in module_tasks.get(ename, [])
                   if infer_crud(t.get("name", "")) == "U"
                   and not _matches_state_keyword(t.get("name", ""))]
    if non_state_u:
        ep_counter += 1
        writable_fields = [f["name"] for f in entity["fields"]
                           if f["name"] not in ("id", "created_at", "updated_at")
                           and "auto" not in f.get("constraints", [])
                           and "PK" not in f.get("constraints", [])]
        endpoints.append({
            "id": f"API-{ep_counter:03d}",
            "method": "PUT",
            "path": f"{path_base}/:id",
            "summary": f"Update {ename}",
            "entity_ref": eid,
            "request_body": writable_fields,
            "response_type": "object",
        })

    # D tasks → DELETE
    if crud.get("D", 0) > 0:
        ep_counter += 1
        endpoints.append({
            "id": f"API-{ep_counter:03d}",
            "method": "DELETE",
            "path": f"{path_base}/:id",
            "summary": f"Delete {ename}",
            "entity_ref": eid,
            "response_type": "empty",
        })

    # State transition tasks → PATCH
    if entity.get("state_machine"):
        for trans in entity["state_machine"]["transitions"]:
            trigger = trans["trigger"]
            ep_counter += 1
            endpoints.append({
                "id": f"API-{ep_counter:03d}",
                "method": "PATCH",
                "path": f"{path_base}/:id/{trigger}",
                "summary": f"{ename}: {trigger} ({trans['from']} → {trans['to']})",
                "entity_ref": eid,
                "request_body": [],
                "response_type": "object",
            })

# ── Write api-contracts.json ─────────────────────────────────────────────────
api_contracts = {
    "generated_at": NOW,
    "endpoint_count": len(endpoints),
    "endpoints": endpoints,
}
api_path = C.write_json(os.path.join(OUT, "api-contracts.json"), api_contracts)

# ── Step 4: Generate Markdown report ─────────────────────────────────────────
lines = []
lines.append("# 数据模型报告\n")
lines.append(f"生成时间: {NOW}\n")

lines.append("## 摘要\n")
lines.append(f"- 实体数量: {len(entities)}")
lines.append(f"- 关系数量: {len(relationships)}")
lines.append(f"- API 端点数量: {len(endpoints)}\n")

lines.append("## 实体列表\n")
lines.append("| ID | 名称 | 字段数 | 任务数 | CRUD | 状态机 |")
lines.append("|----|------|--------|--------|------|--------|")
for e in entities:
    crud_str = "/".join(f"{k}:{v}" for k, v in e["crud_coverage"].items())
    has_sm = "Yes" if e.get("state_machine") else "No"
    lines.append(f"| {e['id']} | {e['name']} | {len(e['fields'])} | {e['task_count']} | {crud_str} | {has_sm} |")

lines.append("\n## 实体详情\n")
for e in entities:
    lines.append(f"### {e['id']}: {e['name']}\n")
    lines.append(f"负责角色: {', '.join(e['owner_roles'])}\n")

    lines.append("**字段:**\n")
    lines.append("| 字段名 | 类型 | 约束 |")
    lines.append("|--------|------|------|")
    for f in e["fields"]:
        cons = ", ".join(f["constraints"]) if f.get("constraints") else "-"
        lines.append(f"| {f['name']} | {f['type']} | {cons} |")

    if e.get("state_machine"):
        sm = e["state_machine"]
        lines.append(f"\n**状态机:** (初始状态: {sm['initial_state']})\n")
        lines.append("| 触发 | 从 | 到 | 任务 |")
        lines.append("|------|----|----|------|")
        for t in sm["transitions"]:
            lines.append(f"| {t['trigger']} | {t['from']} | {t['to']} | {t['task_ref']} |")
    lines.append("")

if relationships:
    lines.append("## 实体关系\n")
    lines.append("| 来源 | 目标 | 类型 | 推断依据 |")
    lines.append("|------|------|------|----------|")
    for r in relationships:
        lines.append(f"| {r['from_name']} | {r['to_name']} | {r['type']} | {r['inferred_from']} |")
    lines.append("")

lines.append("## API 端点\n")
lines.append("| ID | 方法 | 路径 | 说明 |")
lines.append("|----|------|------|------|")
for ep in endpoints:
    lines.append(f"| {ep['id']} | {ep['method']} | {ep['path']} | {ep['summary']} |")

report_path = os.path.join(OUT, "data-model-report.md")
with open(report_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

# ── Pipeline decisions ───────────────────────────────────────────────────────
C.append_pipeline_decision(
    BASE,
    "Step 7 — data-model",
    f"entities={len(entities)}, relationships={len(relationships)}, "
    f"endpoints={len(endpoints)}",
    shard=args.get("shard"),
)

# ── Summary ──────────────────────────────────────────────────────────────────
print(f"OK: {em_path} ({len(entities)} entities, {len(relationships)} relationships)")
print(f"OK: {api_path} ({len(endpoints)} endpoints)")
print(f"OK: {report_path}")
