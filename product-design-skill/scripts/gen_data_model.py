#!/usr/bin/env python3
# Skeleton generator — LLM enrichment required after running
"""Step 7: Generate skeleton entity model from task-inventory modules.

Creates one entity per unique module with default fields (id, name,
created_at, updated_at). Infers relationships from business flows.
Writes entity-model.json, api-contracts.json, and data-model-report.md.

Usage:
    python3 gen_data_model.py <BASE_PATH> [--mode auto] [--shard product-map]
"""

import os
import sys
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C

# ── Setup ────────────────────────────────────────────────────────────────────
BASE, args = C.parse_args()
OUT = os.path.join(BASE, "product-map")
C.ensure_dir(OUT)
NOW = C.now_iso()

# ── Load data ────────────────────────────────────────────────────────────────
tasks = C.load_task_inventory(BASE)
flows = C.load_business_flows(BASE)

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

# ── Field inference from task characteristics ────────────────────────────────

# Keyword → (field_name, field_type, label) patterns
# Scanned against task name, main_flow, rules, acceptance_criteria, config_items
FIELD_PATTERNS = [
    # Status/state fields
    (r"状态|status|state|上下架|发布", ("status", "enum", "状态")),
    (r"进度|progress|完成率|completion", ("progress", "decimal", "进度")),
    (r"优先级|priority", ("priority", "enum", "优先级")),
    (r"难度|difficulty|level|级别", ("difficulty_level", "enum", "难度等级")),
    # Content fields
    (r"标题|title|名称|name", ("title", "string", "标题")),
    (r"描述|description|简介|摘要|说明", ("description", "text", "描述")),
    (r"内容|content|正文|body", ("content", "text", "内容")),
    (r"封面|cover|缩略图|thumbnail|图片|image|配图", ("cover_image", "file", "封面图")),
    (r"音频|audio|发音|tts|语音", ("audio_url", "file", "音频")),
    (r"视频|video", ("video_url", "file", "视频")),
    # Classification/tagging
    (r"分类|category|类别|类型|type", ("category", "enum", "分类")),
    (r"标签|tag|label", ("tags", "string[]", "标签")),
    (r"语言|language|语种", ("language", "enum", "语言")),
    # Metrics/counts
    (r"数量|count|总数|词汇量", ("item_count", "integer", "数量")),
    (r"评分|score|rating|星级|得分", ("score", "decimal", "评分")),
    (r"次数|times|频次", ("attempt_count", "integer", "次数")),
    # Size/capacity
    (r"大小|size|容量|MB|包大小", ("size_bytes", "integer", "大小")),
    # Time-related
    (r"截止|deadline|到期|过期", ("expires_at", "datetime", "到期时间")),
    (r"排序|sort|order|序号", ("sort_order", "integer", "排序序号")),
    # User/role references
    (r"创建者|creator|作者|author|负责人|owner", ("creator_id", "uuid", "创建者")),
    # Config-like
    (r"参数|parameter|config|配置项", ("config_json", "json", "配置参数")),
    # Payment/subscription
    (r"价格|price|金额|费用|amount", ("price", "decimal", "价格")),
    (r"订阅|subscription|plan|方案", ("plan_type", "enum", "订阅方案")),
    # Versioning
    (r"版本|version", ("version", "string", "版本")),
]


def _infer_fields_for_module(module_name, mod_tasks):
    """Infer entity fields from task names, main_flow, rules, config_items, and acceptance_criteria."""
    # Always start with PK + timestamps
    fields = [
        {"name": "id", "type": "uuid", "constraints": ["PK"], "label": "ID"},
    ]
    seen_names = {"id"}

    # Collect all text from tasks in this module
    all_texts = []
    for t in mod_tasks:
        all_texts.append(t.get("name", ""))
        all_texts.extend(str(s) for s in t.get("main_flow", []))
        all_texts.extend(str(s) for s in t.get("rules", []))
        all_texts.extend(str(s) for s in t.get("acceptance_criteria", []))
        for ci in t.get("config_items", []):
            all_texts.append(ci.get("param", ""))
        for state in t.get("outputs", {}).get("states", []):
            all_texts.append(str(state))
        all_texts.extend(str(s) for s in t.get("exceptions", []))
    corpus = " ".join(all_texts).lower()

    # Scan patterns
    for pattern, (fname, ftype, flabel) in FIELD_PATTERNS:
        if fname in seen_names:
            continue
        if re.search(pattern, corpus):
            constraints = ["not_null"] if ftype in ("string", "enum") else []
            fields.append({
                "name": fname,
                "type": ftype,
                "constraints": constraints,
                "label": flabel,
            })
            seen_names.add(fname)

    # Extract config_items as dedicated fields
    for t in mod_tasks:
        for ci in t.get("config_items", []):
            param = ci.get("param", "")
            if param and param not in seen_names:
                fields.append({
                    "name": param,
                    "type": _guess_config_type(ci.get("current", "")),
                    "constraints": ["config"],
                    "label": _humanize_param(param),
                })
                seen_names.add(param)

    # Always end with timestamps
    fields.append({"name": "created_at", "type": "datetime", "constraints": ["auto"], "label": "创建时间"})
    fields.append({"name": "updated_at", "type": "datetime", "constraints": ["auto"], "label": "更新时间"})

    return fields


def _humanize_param(param):
    """Convert snake_case config param name to readable label.

    Uses generic abbreviation expansion (no product-specific mappings).
    """
    # Common technical abbreviation expansions
    ABBREVS = {
        "mb": "MB", "gb": "GB", "kb": "KB",
        "api": "API", "url": "URL", "id": "ID",
        "llm": "LLM", "ai": "AI", "tts": "TTS",
        "cdn": "CDN", "srs": "SRS", "fsrs": "FSRS",
    }
    parts = param.lower().split("_")
    result = []
    for p in parts:
        if p in ABBREVS:
            result.append(ABBREVS[p])
        else:
            result.append(p.capitalize())
    return " ".join(result)


def _guess_config_type(current_value):
    """Guess field type from config_item current value."""
    v = str(current_value).lower().strip()
    if v in ("true", "false"):
        return "boolean"
    try:
        int(v)
        return "integer"
    except (ValueError, TypeError):
        pass
    try:
        float(v)
        return "decimal"
    except (ValueError, TypeError):
        pass
    return "string"


for idx, (module, mod_tasks) in enumerate(sorted(module_tasks.items()), start=1):
    eid = f"E{idx:03d}"
    entity_id_map[module] = eid

    # Collect owner roles
    owner_roles = sorted(set(
        role_map.get(t.get("owner_role", ""), t.get("owner_role", ""))
        for t in mod_tasks
    ))

    inferred_fields = _infer_fields_for_module(module, mod_tasks)

    entity = {
        "id": eid,
        "name": module,
        "name_zh": module,
        "fields": inferred_fields,
        "owner_roles": owner_roles,
        "task_count": len(mod_tasks),
    }
    entities.append(entity)

# ── Step 2: Infer relationships from business flows ──────────────────────────
relationships = []
rel_seen = set()

for flow in flows:
    nodes = C.get_flow_nodes(flow)
    flow_entities = []
    for node in nodes:
        task_ref = node.get("task_ref", "") if isinstance(node, dict) else node
        if task_ref in tasks:
            module = tasks[task_ref].get("module", "")
            eid = entity_id_map.get(module)
            if eid and eid not in [fe[0] for fe in flow_entities]:
                flow_entities.append((eid, module))

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

# ── Step 3: Skeleton API contracts (one CRUD set per entity) ─────────────────
endpoints = []
ep_counter = 0


def _pluralize(name):
    if name.endswith("s") or name.endswith("x") or name.endswith("sh") or name.endswith("ch"):
        return name + "es"
    return name + "s"


for entity in entities:
    eid = entity["id"]
    ename = entity["name"]
    path_base = f"/{_pluralize(ename)}"

    # GET list
    ep_counter += 1
    endpoints.append({
        "id": f"API-{ep_counter:03d}",
        "method": "GET",
        "path": path_base,
        "summary": f"List {ename}",
        "entity_ref": eid,
        "query_params": [
            {"name": "page", "type": "integer", "required": False},
            {"name": "page_size", "type": "integer", "required": False},
        ],
        "response_type": "array",
    })

    # GET detail
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

    # Collect writable field names for request bodies
    writable_fields = [
        f["name"] for f in entity.get("fields", [])
        if f["name"] not in ("id", "created_at", "updated_at", "creator_id")
        and "auto" not in f.get("constraints", [])
        and "PK" not in f.get("constraints", [])
    ]
    if not writable_fields:
        writable_fields = ["name"]

    # POST create
    ep_counter += 1
    endpoints.append({
        "id": f"API-{ep_counter:03d}",
        "method": "POST",
        "path": path_base,
        "summary": f"Create {ename}",
        "entity_ref": eid,
        "request_body": writable_fields,
        "response_type": "object",
    })

    # PUT update
    ep_counter += 1
    endpoints.append({
        "id": f"API-{ep_counter:03d}",
        "method": "PUT",
        "path": f"{path_base}/:id",
        "summary": f"Update {ename}",
        "entity_ref": eid,
        "request_body": writable_fields,
        "response_type": "object",
    })

    # DELETE
    ep_counter += 1
    endpoints.append({
        "id": f"API-{ep_counter:03d}",
        "method": "DELETE",
        "path": f"{path_base}/:id",
        "summary": f"Delete {ename}",
        "entity_ref": eid,
        "response_type": "empty",
    })

# ── Write api-contracts.json ─────────────────────────────────────────────────
api_contracts = {
    "generated_at": NOW,
    "endpoint_count": len(endpoints),
    "endpoints": endpoints,
}
api_path = C.write_json(os.path.join(OUT, "api-contracts.json"), api_contracts)

# ── Step 4: Markdown report ──────────────────────────────────────────────────
lines = []
lines.append("# 数据模型报告\n")
lines.append(f"生成时间: {NOW}\n")

lines.append("## 摘要\n")
lines.append(f"- 实体数量: {len(entities)}")
lines.append(f"- 关系数量: {len(relationships)}")
lines.append(f"- API 端点数量: {len(endpoints)}\n")

lines.append("## 实体列表\n")
lines.append("| ID | 名称 | 字段数 | 任务数 |")
lines.append("|----|------|--------|--------|")
for e in entities:
    lines.append(f"| {e['id']} | {e['name']} | {len(e['fields'])} | {e['task_count']} |")

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
