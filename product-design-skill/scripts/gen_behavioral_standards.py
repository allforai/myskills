#!/usr/bin/env python3
"""Generate behavioral standards: detect cross-screen behavioral inconsistencies.

Pre-built script for Phase 3.6 (behavioral-standards). Detects 9 categories:
- BC-DELETE-CONFIRM, BC-EMPTY-STATE, BC-LOADING, BC-ERROR-DISPLAY,
- BC-FORM-VALIDATION, BC-SUCCESS-FEEDBACK, BC-PERMISSION-DENIED,
- BC-PAGINATION, BC-UNSAVED-GUARD

Usage:
    python3 gen_behavioral_standards.py <BASE_PATH> [--mode auto] [--shard behavioral-standards]
"""

import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C

# ── Setup ─────────────────────────────────────────────────────────────────────
BASE, args = C.parse_args()
OUT = os.path.join(BASE, "behavioral-standards")
C.ensure_dir(OUT)
NOW = C.now_iso()

# ── Load data ─────────────────────────────────────────────────────────────────
screens, has_screens = C.load_screen_map(BASE)
if not has_screens or not screens:
    print("ERROR: screen-map.json not found or empty", file=sys.stderr)
    sys.exit(1)

screen_by_id = C.build_screen_by_id(screens)

# Optionally load pattern-catalog for enrichment
pattern_catalog = C.load_json(os.path.join(BASE, "design-pattern/pattern-catalog.json"))

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

# ── Approach Classification Keywords ─────────────────────────────────────────

# Delete confirmation approaches
DELETE_CONFIRM_KW = {
    "modal_confirm": ["modal", "弹窗", "弹框", "对话框", "dialog", "确认弹窗", "二次确认"],
    "inline_confirm": ["inline", "行内确认", "内联", "inline confirm", "行内"],
    "no_confirm": ["直接", "无确认", "no confirm", "skip"],
}

# Empty state approaches
EMPTY_STATE_KW = {
    "illustration_text": ["插图", "illustration", "图文", "引导图", "空状态图", "图片"],
    "text_only": ["文字", "text", "提示文字", "文案", "引导文案"],
    "nothing": ["无", "空白", "nothing", "blank", "隐藏"],
}

# Loading approaches
LOADING_KW = {
    "skeleton": ["骨架屏", "skeleton", "占位", "placeholder"],
    "spinner": ["spinner", "loading", "加载中", "转圈", "菊花", "旋转"],
    "progressive": ["渐进", "progressive", "lazy", "懒加载", "分步"],
}

# Error display approaches
ERROR_DISPLAY_KW = {
    "toast": ["toast", "弹出提示", "轻提示", "消息提示", "notification", "message"],
    "inline_error": ["inline", "行内", "字段下方", "内联", "红色提示"],
    "page_level": ["页面", "page", "整页", "全屏错误", "错误页", "error page"],
}

# Form validation approaches
FORM_VALIDATION_KW = {
    "realtime": ["实时", "real-time", "realtime", "即时", "逐字段", "blur", "onChange"],
    "on_submit": ["提交时", "on-submit", "submit", "点击提交", "整体校验"],
    "hybrid": ["混合", "hybrid", "关键字段实时", "提交时全量"],
}

# Success feedback approaches
SUCCESS_FEEDBACK_KW = {
    "toast_success": ["toast", "提示", "消息", "notification", "message", "轻提示"],
    "redirect": ["跳转", "redirect", "返回列表", "页面跳转"],
    "inline_success": ["inline", "行内", "内联", "原地更新"],
}

# Permission denied approaches
PERMISSION_DENIED_KW = {
    "redirect_login": ["跳转", "redirect", "重定向", "登录页", "403"],
    "inline_disable": ["禁用", "disable", "灰化", "不可点击", "置灰"],
    "hide_element": ["隐藏", "hide", "不显示", "不展示", "移除"],
}

# Pagination approaches
PAGINATION_KW = {
    "infinite_scroll": ["无限滚动", "infinite", "load more", "加载更多", "瀑布流"],
    "numbered_pages": ["分页", "page", "页码", "翻页", "pagination", "分页器"],
}

# Unsaved guard approaches
UNSAVED_GUARD_KW = {
    "browser_prompt": ["browser", "浏览器", "beforeunload", "系统提示", "原生"],
    "custom_modal": ["自定义", "custom", "弹窗", "modal", "对话框"],
    "no_guard": ["无", "none", "不拦截", "无守卫"],
}


def _classify_approach(text, keyword_map):
    """Classify text into an approach using keyword matching.

    Returns (approach_key, confidence) or (None, 0).
    """
    text_lower = text.lower()
    scores = {}
    for approach, keywords in keyword_map.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[approach] = score
    if scores:
        best = max(scores, key=scores.get)
        return best, scores[best]
    return None, 0


def _extract_screen_text(screen):
    """Extract all relevant text from a screen for keyword matching."""
    parts = [screen.get("name", "")]
    # States
    states = screen.get("states", {})
    if isinstance(states, dict):
        for state_key, state_val in states.items():
            if isinstance(state_val, str):
                parts.append(f"{state_key}: {state_val}")
            elif isinstance(state_val, dict):
                parts.append(f"{state_key}: {state_val.get('description', '')}")
    elif isinstance(states, list):
        for s in states:
            if isinstance(s, str):
                parts.append(s)
            elif isinstance(s, dict):
                parts.append(s.get("name", "") + " " + s.get("description", ""))
    # Actions
    for action in screen.get("actions", []):
        label = action.get("label", "")
        crud = action.get("crud", "")
        on_failure = action.get("on_failure", "")
        requires_confirm = action.get("requires_confirm", "")
        parts.append(f"{label} crud={crud} on_failure={on_failure} confirm={requires_confirm}")
        # Validation rules
        for rule in action.get("validation_rules", []):
            if isinstance(rule, str):
                parts.append(rule)
            elif isinstance(rule, dict):
                parts.append(rule.get("rule", "") + " " + rule.get("message", ""))
    # On failure at screen level
    on_failure = screen.get("on_failure", "")
    if isinstance(on_failure, str):
        parts.append(on_failure)
    elif isinstance(on_failure, dict):
        parts.append(str(on_failure))
    return " ".join(parts)


# ── Detect Categories ─────────────────────────────────────────────────────────

category_results = []
all_screen_tags = {}  # screen_id → {_behavioral: [], _behavioral_standards: {}}

SKIP_THRESHOLD_MIN_SCREENS = 3
SKIP_THRESHOLD_DIVERGENCE = 0.30  # 30%


def _detect_category(cat_id, cat_name, cat_desc, screen_filter_fn, keyword_map):
    """Generic category detection.

    Args:
        cat_id: Category ID (e.g. "BC-DELETE-CONFIRM")
        cat_name: Human readable name
        cat_desc: Description
        screen_filter_fn: function(screen) → bool, whether this screen is relevant
        keyword_map: {approach: [keywords]} for classification

    Returns category result dict or None if not enough screens.
    """
    affected_screens = []
    approach_distribution = defaultdict(lambda: {"count": 0, "screen_ids": []})

    for screen in screens:
        if not screen_filter_fn(screen):
            continue
        sid = screen["id"]
        affected_screens.append(sid)
        text = _extract_screen_text(screen)
        approach, confidence = _classify_approach(text, keyword_map)
        if approach is None:
            approach = "unspecified"
        approach_distribution[approach]["count"] += 1
        approach_distribution[approach]["screen_ids"].append(sid)

    if len(affected_screens) < SKIP_THRESHOLD_MIN_SCREENS:
        return None

    # Convert defaultdict to regular dict
    dist = {k: dict(v) for k, v in approach_distribution.items()}

    # Determine recommended standard: majority approach if >= 60%
    total = len(affected_screens)
    majority_approach = None
    majority_count = 0
    for approach, info in dist.items():
        if info["count"] > majority_count:
            majority_count = info["count"]
            majority_approach = approach

    has_majority = (majority_count / total) >= 0.60 if total > 0 else False

    # Check divergence
    non_majority_count = total - majority_count
    divergence_ratio = non_majority_count / total if total > 0 else 0

    if divergence_ratio <= SKIP_THRESHOLD_DIVERGENCE and len(dist) <= 1:
        # Single approach with low divergence — no behavioral inconsistency
        return None

    recommended = {
        "approach": majority_approach if has_majority else "needs_review",
        "description": f"{'多数界面采用' if has_majority else '无明显多数，建议统一为'} {majority_approach or '待定'}",
        "exceptions": "",
    }

    return {
        "category_id": cat_id,
        "name": cat_name,
        "detection_summary": {
            "total_screens_affected": total,
            "approach_distribution": dist,
        },
        "recommended_standard": recommended,
        "user_decision": "auto_confirmed" if args.get("mode") == "auto" else "pending",
    }


# ── Filter Functions ──────────────────────────────────────────────────────────

def _has_delete_action(screen):
    """Screen has delete/destructive action."""
    for action in screen.get("actions", []):
        crud = (action.get("crud", "") or "").upper()
        label = (action.get("label", "") or "").lower()
        if crud == "D" or any(kw in label for kw in ["删除", "移除", "delete", "remove", "清空", "撤销"]):
            return True
    return False


def _has_states(screen):
    """Screen has states definition."""
    states = screen.get("states", {})
    return bool(states)


def _has_empty_state(screen):
    """Screen could have empty state (list/table screens or screens with states.empty)."""
    states = screen.get("states", {})
    if isinstance(states, dict) and "empty" in states:
        return True
    # List/table screens typically need empty state
    name = screen.get("name", "").lower()
    return any(kw in name for kw in ["列表", "list", "管理", "概览", "overview", "表格", "table"])


def _has_loading(screen):
    """Most screens have loading state — include all screens for consistency analysis."""
    return True


def _has_error_state(screen):
    """Screen could have error state."""
    states = screen.get("states", {})
    if isinstance(states, dict) and "error" in states:
        return True
    # Screens with actions can have errors
    return bool(screen.get("actions", []))


def _has_form(screen):
    """Screen has form/input actions."""
    for action in screen.get("actions", []):
        crud = (action.get("crud", "") or "").upper()
        label = (action.get("label", "") or "").lower()
        has_validation = bool(action.get("validation_rules"))
        if crud in ("C", "U") or has_validation:
            return True
        if any(kw in label for kw in ["提交", "保存", "submit", "save", "创建", "新建", "编辑"]):
            return True
    return False


def _has_success_action(screen):
    """Screen has actions that produce success feedback."""
    return bool(screen.get("actions", []))


def _has_permission_state(screen):
    """Screen has permission denied state."""
    states = screen.get("states", {})
    if isinstance(states, dict) and "permission_denied" in states:
        return True
    return False


def _is_list_screen(screen):
    """Screen is a list/table screen that might need pagination."""
    name = screen.get("name", "").lower()
    return any(kw in name for kw in ["列表", "list", "管理", "概览", "overview", "表格", "table", "搜索", "search"])


def _has_edit_action(screen):
    """Screen has edit/update action (unsaved guard candidate)."""
    for action in screen.get("actions", []):
        crud = (action.get("crud", "") or "").upper()
        label = (action.get("label", "") or "").lower()
        if crud == "U":
            return True
        if any(kw in label for kw in ["编辑", "修改", "更新", "edit", "update", "保存", "save"]):
            return True
    return False


# ── Run Detection ─────────────────────────────────────────────────────────────

DETECTION_CONFIG = [
    ("BC-DELETE-CONFIRM", "破坏性操作确认", "crud=D 或高风险操作的确认方式", _has_delete_action, DELETE_CONFIRM_KW),
    ("BC-EMPTY-STATE", "空状态展示", "界面无数据时的空状态展示方式", _has_empty_state, EMPTY_STATE_KW),
    ("BC-LOADING", "加载模式", "界面加载中的展示方式", _has_loading, LOADING_KW),
    ("BC-ERROR-DISPLAY", "错误展示", "操作失败或异常时的错误展示方式", _has_error_state, ERROR_DISPLAY_KW),
    ("BC-FORM-VALIDATION", "表单校验反馈", "表单输入校验的反馈方式", _has_form, FORM_VALIDATION_KW),
    ("BC-SUCCESS-FEEDBACK", "成功反馈", "操作成功后的反馈方式", _has_success_action, SUCCESS_FEEDBACK_KW),
    ("BC-PERMISSION-DENIED", "权限不足", "用户无权限时的展示方式", _has_permission_state, PERMISSION_DENIED_KW),
    ("BC-PAGINATION", "分页行为", "列表/表格的分页方式", _is_list_screen, PAGINATION_KW),
    ("BC-UNSAVED-GUARD", "未保存变更守卫", "用户离开含未保存变更的界面时的守卫方式", _has_edit_action, UNSAVED_GUARD_KW),
]

detected_categories = []
inconsistencies_found = 0

for cat_id, cat_name, cat_desc, filter_fn, kw_map in DETECTION_CONFIG:
    result = _detect_category(cat_id, cat_name, cat_desc, filter_fn, kw_map)
    if result is not None:
        detected_categories.append(result)
        # Count inconsistencies: categories with >1 distinct approach
        dist = result["detection_summary"]["approach_distribution"]
        real_approaches = {k for k in dist if k != "unspecified"}
        if len(real_approaches) > 1 or (len(real_approaches) == 1 and "unspecified" in dist):
            inconsistencies_found += 1

# ── Skip Check ────────────────────────────────────────────────────────────────

if not detected_categories:
    print("Phase 3.6: 所有行为模式一致，跳过")
    C.append_pipeline_decision(
        BASE,
        "Phase 3.6 — behavioral-standards",
        "All behavioral patterns consistent across screens, skipped",
        shard=args.get("shard"),
    )
    sys.exit(0)

# ── Build Screen Tags ─────────────────────────────────────────────────────────

for cat in detected_categories:
    cat_id = cat["category_id"]
    recommended = cat["recommended_standard"]["approach"]
    dist = cat["detection_summary"]["approach_distribution"]
    for approach, info in dist.items():
        for sid in info["screen_ids"]:
            if sid not in all_screen_tags:
                all_screen_tags[sid] = {
                    "_behavioral": [],
                    "_behavioral_standards": {},
                }
            if cat_id not in all_screen_tags[sid]["_behavioral"]:
                all_screen_tags[sid]["_behavioral"].append(cat_id)
            # Tag with the recommended standard (not the current approach)
            all_screen_tags[sid]["_behavioral_standards"][cat_id] = recommended

# ═════════════════════════════════════════════════════════════════════════════
# Output
# ═════════════════════════════════════════════════════════════════════════════

# ── behavioral-standards.json ─────────────────────────────────────────────────
standards = {
    "created_at": NOW,
    "total_categories_detected": len(detected_categories),
    "categories": detected_categories,
    "screen_behavioral_tags": all_screen_tags,
    "screens_tagged": len(all_screen_tags),
    "inconsistencies_found": inconsistencies_found,
    "inconsistencies_resolved": inconsistencies_found if args.get("mode") == "auto" else 0,
}
C.write_json(os.path.join(OUT, "behavioral-standards.json"), standards)

# ── behavioral-standards-report.md ────────────────────────────────────────────
lines = []
lines.append("# Phase 3.6 — 产品行为规范报告\n")
lines.append("## 概览\n")
lines.append("| 指标 | 值 |")
lines.append("|------|-----|")
lines.append(f"| 检测行为类别数 | {len(detected_categories)} 个 |")
lines.append(f"| 标注 Screens | {len(all_screen_tags)} 个 |")
lines.append(f"| 发现不一致 | {inconsistencies_found} 处 |")
lines.append(f"| 已解决不一致 | {standards['inconsistencies_resolved']} 处 |\n")

lines.append("## 行为类别分析\n")
for cat in detected_categories:
    lines.append(f"### {cat['category_id']}: {cat['name']}\n")
    lines.append(f"影响界面数: {cat['detection_summary']['total_screens_affected']}\n")
    lines.append("| 方案 | 数量 | 界面 |")
    lines.append("|------|------|------|")
    for approach, info in cat["detection_summary"]["approach_distribution"].items():
        sids = ", ".join(info["screen_ids"][:5])
        if len(info["screen_ids"]) > 5:
            sids += "..."
        lines.append(f"| {approach} | {info['count']} | {sids} |")
    rec = cat["recommended_standard"]
    lines.append(f"\n**推荐标准**: {rec['approach']} — {rec['description']}")
    if rec.get("exceptions"):
        lines.append(f"\n**例外**: {rec['exceptions']}")
    lines.append("")

# Skipped categories
all_cat_ids = {c[0] for c in DETECTION_CONFIG}
detected_ids = {c["category_id"] for c in detected_categories}
skipped_ids = sorted(all_cat_ids - detected_ids)
if skipped_ids:
    lines.append("## 一致或不适用的类别（跳过）\n")
    for cid in skipped_ids:
        lines.append(f"- {cid} — 所有界面一致或影响界面不足 3 个")

with open(os.path.join(OUT, "behavioral-standards-report.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

# ── Pipeline decisions ────────────────────────────────────────────────────────
cat_summary = ", ".join(
    f"{c['category_id']}({c['detection_summary']['total_screens_affected']})"
    for c in detected_categories
)
C.append_pipeline_decision(
    BASE,
    "Phase 3.6 — behavioral-standards",
    f"{len(detected_categories)} categories detected, "
    f"{len(all_screen_tags)} screens tagged, "
    f"{inconsistencies_found} inconsistencies. "
    f"Detected: {cat_summary}. "
    f"Skipped: {', '.join(skipped_ids) if skipped_ids else 'none'}",
    shard=args.get("shard"),
)

# ── Summary ───────────────────────────────────────────────────────────────────
print(f"Categories detected: {len(detected_categories)}")
print(f"Screens tagged: {len(all_screen_tags)}")
print(f"Inconsistencies found: {inconsistencies_found}")
for cat in detected_categories:
    print(f"  {cat['category_id']}: {cat['detection_summary']['total_screens_affected']} screens")
for cid in skipped_ids:
    print(f"  {cid}: skipped (consistent or < 3 screens)")
print(f"\nAll files written to {OUT}/")
