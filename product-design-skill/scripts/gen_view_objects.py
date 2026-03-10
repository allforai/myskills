#!/usr/bin/env python3
# Skeleton generator — LLM enrichment required after running
"""Step 8: Generate one View Object per entity with all entity fields.

Reads entity-model.json. Generates a single VO per entity containing
all fields as-is. No CRUD inference or smart action generation.
Writes view-objects.json to <BASE>/product-map/.

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
    "decimal": "currency",
    "datetime": "relative_time",
    "integer": "number",
    "file": "thumbnail",
    "file[]": "thumbnail_group",
}

# ── Setup ────────────────────────────────────────────────────────────────────
BASE, args = C.parse_args()
OUT = os.path.join(BASE, "product-map")
C.ensure_dir(OUT)
NOW = C.now_iso()

# ── Load inputs ──────────────────────────────────────────────────────────────
entities, relationships = C.load_entity_model(BASE)

# ── Generate one VO per entity ───────────────────────────────────────────────
all_vos = []
vo_counter = 0

for entity in entities:
    vo_counter += 1
    eid = entity["id"]
    ename = entity["name"]
    vo_id = f"VO{vo_counter:03d}"

    # Include all entity fields as-is
    fields = []
    for f in entity.get("fields", []):
        field_entry = {
            "name": f["name"],
            "type": f["type"],
            "read_only": True,
        }
        display_format = DISPLAY_FORMATS.get(f["type"])
        if display_format:
            field_entry["display_format"] = display_format
        if f.get("label"):
            field_entry["label"] = f["label"]
        fields.append(field_entry)

    vo = {
        "id": vo_id,
        "entity_ref": eid,
        "entity_name": ename,
        "view_type": "detail",
        "interaction_type": "MG1",
        "fields": fields,
        "actions": [],
    }
    all_vos.append(vo)

# ── Build type distribution ──────────────────────────────────────────────────
type_dist = {}
for vo in all_vos:
    vtype = vo["view_type"]
    type_dist[vtype] = type_dist.get(vtype, 0) + 1

# ── Write output ─────────────────────────────────────────────────────────────
output = {
    "generated_at": NOW,
    "vo_count": len(all_vos),
    "type_distribution": type_dist,
    "view_objects": all_vos,
}
out_path = C.write_json(os.path.join(OUT, "view-objects.json"), output)

# ── Pipeline decision ────────────────────────────────────────────────────────
dist_str = ", ".join(f"{k}:{v}" for k, v in type_dist.items())
C.append_pipeline_decision(
    BASE,
    "Step 8 — view-objects",
    f"vo_count={len(all_vos)}, types=[{dist_str}]",
    shard=args.get("shard"),
)

# ── Summary ──────────────────────────────────────────────────────────────────
print(f"OK: {out_path} ({len(all_vos)} VOs: {dist_str})")
