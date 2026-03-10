# Skeleton generator — LLM enrichment required after running
#!/usr/bin/env python3
"""Generate behavioral standards skeleton: list screens per behavioral category.

Skeleton for Phase 3.6 (behavioral-standards). Outputs 9 categories with
relevant screens referenced — no keyword-based approach classification.
LLM enrichment is required to classify approaches and detect inconsistencies.

Usage:
    python3 gen_behavioral_standards.py <BASE_PATH> [--mode auto] [--shard behavioral-standards]
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C

# ── Setup ─────────────────────────────────────────────────────────────────────
BASE, args = C.parse_args()
OUT = os.path.join(BASE, "behavioral-standards")
C.ensure_dir(OUT)
NOW = C.now_iso()

# ── Load data ─────────────────────────────────────────────────────────────────
op_lines, screen_index, em_loaded = C.load_experience_map(BASE)
if not em_loaded or not op_lines:
    print("ERROR: experience-map.json not found or empty", file=sys.stderr)
    sys.exit(1)

screen_by_id = C.build_screen_by_id_from_lines(op_lines)
screens = list(screen_by_id.values())

# ── Category Definitions ─────────────────────────────────────────────────────

CATEGORIES = [
    {
        "id": "BC-DELETE-CONFIRM",
        "name": "破坏性操作确认",
        "description": "crud=D 或高风险操作的确认方式",
    },
    {
        "id": "BC-EMPTY-STATE",
        "name": "空状态展示",
        "description": "界面无数据时的空状态展示方式",
    },
    {
        "id": "BC-LOADING",
        "name": "加载模式",
        "description": "界面加载中的展示方式",
    },
    {
        "id": "BC-ERROR-DISPLAY",
        "name": "错误展示",
        "description": "操作失败或异常时的错误展示方式",
    },
    {
        "id": "BC-FORM-VALIDATION",
        "name": "表单校验反馈",
        "description": "表单输入校验的反馈方式",
    },
    {
        "id": "BC-SUCCESS-FEEDBACK",
        "name": "成功反馈",
        "description": "操作成功后的反馈方式",
    },
    {
        "id": "BC-PERMISSION-DENIED",
        "name": "权限不足",
        "description": "用户无权限时的展示方式",
    },
    {
        "id": "BC-PAGINATION",
        "name": "分页行为",
        "description": "列表/表格的分页方式",
    },
    {
        "id": "BC-UNSAVED-GUARD",
        "name": "未保存变更守卫",
        "description": "用户离开含未保存变更的界面时的守卫方式",
    },
]

# ── Collect screen references per category ────────────────────────────────────

def _collect_screen_ids(screens):
    """Return all screen IDs with their basic metadata for category assignment."""
    entries = []
    for s in screens:
        actions = s.get("actions", [])
        crud_set = {(a.get("crud", "") or "").upper() for a in actions}
        states = s.get("states", {})
        state_keys = list(states.keys()) if isinstance(states, dict) else []
        entries.append({
            "id": s["id"],
            "name": s.get("name", ""),
            "interaction_type": s.get("interaction_type", ""),
            "crud_types": sorted(crud_set - {""}),
            "action_count": len(actions),
            "state_keys": state_keys,
            "has_data_fields": bool(s.get("data_fields")),
        })
    return entries

screen_entries = _collect_screen_ids(screens)

# Build category results — list all screens, let LLM classify later
category_results = []
for cat in CATEGORIES:
    category_results.append({
        "category_id": cat["id"],
        "name": cat["name"],
        "description": cat["description"],
        "screen_refs": [e["id"] for e in screen_entries],
        "approach": "pending_llm_classification",
        "user_decision": "auto_confirmed" if args.get("mode") == "auto" else "pending",
    })

# ═════════════════════════════════════════════════════════════════════════════
# Output
# ═════════════════════════════════════════════════════════════════════════════

standards = {
    "created_at": NOW,
    "total_categories": len(CATEGORIES),
    "categories": category_results,
    "screen_inventory": screen_entries,
    "total_screens": len(screen_entries),
    "llm_enrichment_required": True,
}
C.write_json(os.path.join(OUT, "behavioral-standards.json"), standards)

# ── behavioral-standards-report.md ────────────────────────────────────────────
lines = []
lines.append("# Phase 3.6 — 产品行为规范报告（骨架）\n")
lines.append("> LLM enrichment required: approach classification pending\n")
lines.append("## 概览\n")
lines.append("| 指标 | 值 |")
lines.append("|------|-----|")
lines.append(f"| 行为类别数 | {len(CATEGORIES)} 个 |")
lines.append(f"| 总 Screens | {len(screen_entries)} 个 |")
lines.append(f"| 分类状态 | 待 LLM 分类 |\n")

lines.append("## 行为类别\n")
for cat in category_results:
    lines.append(f"### {cat['category_id']}: {cat['name']}\n")
    lines.append(f"{cat['description']}\n")
    lines.append(f"关联界面数: {len(cat['screen_refs'])}\n")

with open(os.path.join(OUT, "behavioral-standards-report.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

# ── Pipeline decisions ────────────────────────────────────────────────────────
C.append_pipeline_decision(
    BASE,
    "Phase 3.6 — behavioral-standards",
    f"{len(CATEGORIES)} categories, {len(screen_entries)} screens inventoried, "
    f"pending LLM enrichment for approach classification",
    shard=args.get("shard"),
)

# ── Summary ───────────────────────────────────────────────────────────────────
print(f"Categories: {len(CATEGORIES)}")
print(f"Screens inventoried: {len(screen_entries)}")
print(f"Status: skeleton generated, LLM enrichment required")
print(f"\nAll files written to {OUT}/")
