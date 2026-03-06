#!/usr/bin/env python3
"""Standardized XV prompt templates for cross-model validation.

Each function returns {"system": str, "user": str} ready for xv_call().
"""

import json


# ── journey_validation (gemini) ──────────────────────────────────────────────

def journey_validation_prompt(journey_gaps):
    """Build prompts for journey breakpoint validation.

    Args:
        journey_gaps: list of journey gap dicts from gen_feature_gap.py
    """
    # Take first 20 breakpoint entries
    sample = journey_gaps[:20]
    summary = json.dumps(sample, ensure_ascii=False, indent=2)

    system = (
        "You are a product completeness auditor. "
        "Analyze the user journey breakpoints and identify:\n"
        "1. Overlooked gaps not captured by the automated checks\n"
        "2. False positives that are not real gaps\n\n"
        "Respond with ONLY valid JSON, no markdown fences, no explanation.\n"
        "Schema:\n"
        '{"overlooked": [{"role": str, "task": str, "gap": str, "severity": "high"|"medium"|"low"}], '
        '"false_positives": ["gap_description_string"]}'
    )

    user = (
        "Here are user journey breakpoints from automated analysis. "
        "Each entry has a role, task, score, and breakpoints.\n\n"
        f"{summary}\n\n"
        "Identify overlooked journey gaps (cross-role handoff failures, "
        "async flow breaks, dead-end states not caught) and any false positives."
    )

    return {"system": system, "user": user}


# ── gap_prioritization (gpt) ─────────────────────────────────────────────────

def gap_prioritization_prompt(gap_tasks_list):
    """Build prompts for gap task priority review.

    Args:
        gap_tasks_list: list of gap task dicts from gen_feature_gap.py
    """
    # Summarize: id, title, priority, type only
    summary = json.dumps(
        [{"id": g["id"], "title": g["title"], "priority": g["priority"], "type": g["type"]}
         for g in gap_tasks_list],
        ensure_ascii=False, indent=2
    )

    system = (
        "You are a product prioritization expert. "
        "Review the gap task list and suggest:\n"
        "1. Priority adjustments (low-frequency high-risk gaps may need elevation)\n"
        "2. Duplicate entries that should be merged\n\n"
        "Respond with ONLY valid JSON, no markdown fences, no explanation.\n"
        "Schema:\n"
        '{"adjustments": [{"id": "GAP-NNN", "current": "高|中|低", "recommended": "高|中|低", "reason": "..."}], '
        '"dedup": ["GAP-NNN"]}\n'
        'Priority values MUST be Chinese: "高" (high), "中" (medium), "低" (low).'
    )

    user = (
        "Here is a prioritized gap task list from feature-gap analysis.\n\n"
        f"{summary}\n\n"
        "Suggest priority adjustments and identify duplicates to merge."
    )

    return {"system": system, "user": user}


# ── edge_case_generation (deepseek) ──────────────────────────────────────────

def edge_case_prompt(roles_tree):
    """Build prompts for missing edge case detection.

    Args:
        roles_tree: list of role entries from use-case-tree
    """
    # Summarize: each role's first 3 feature areas + use case titles
    summary_parts = []
    for role in roles_tree:
        role_info = {"role_id": role["id"], "role_name": role["name"], "areas": []}
        for fa in role.get("feature_areas", [])[:3]:
            area = {"name": fa["name"], "tasks": []}
            for t in fa.get("tasks", [])[:5]:
                area["tasks"].append({
                    "task_id": t["id"],
                    "name": t["name"],
                    "use_case_titles": [uc.get("title", "") for uc in t.get("use_cases", [])[:5]]
                })
            role_info["areas"].append(area)
        summary_parts.append(role_info)

    summary = json.dumps(summary_parts, ensure_ascii=False, indent=2)

    system = (
        "You are a QA edge-case specialist. "
        "Analyze the use case tree and identify missing edge cases:\n"
        "- Concurrency issues\n"
        "- Timing dependencies\n"
        "- Data boundary extremes\n"
        "- Cross-role interaction edge cases\n\n"
        "Respond with ONLY valid JSON, no markdown fences, no explanation.\n"
        "Schema:\n"
        '{"missing_cases": [{"role_id": str, "task_id": str, "title": str, '
        '"type": "boundary"|"exception"|"concurrency", "severity": "high"|"medium"|"low"}]}'
    )

    user = (
        "Here is a summary of the use case tree (roles, feature areas, tasks, existing use cases).\n\n"
        f"{summary}\n\n"
        "Identify missing edge cases not covered by existing use cases."
    )

    return {"system": system, "user": user}


# ── acceptance_criteria_review (gpt) ─────────────────────────────────────────

def acceptance_criteria_prompt(roles_tree):
    """Build prompts for acceptance criteria quality review.

    Args:
        roles_tree: list of role entries from use-case-tree
    """
    import random

    # Collect all use cases, sample up to 20
    all_ucs = []
    for role in roles_tree:
        for fa in role.get("feature_areas", []):
            for t in fa.get("tasks", []):
                for uc in t.get("use_cases", []):
                    if uc.get("given") and uc.get("when") and uc.get("then"):
                        all_ucs.append({
                            "use_case_id": uc["id"],
                            "title": uc.get("title", ""),
                            "given": uc["given"],
                            "when": uc["when"],
                            "then": uc["then"],
                        })

    sample = random.sample(all_ucs, min(20, len(all_ucs))) if all_ucs else []
    summary = json.dumps(sample, ensure_ascii=False, indent=2)

    system = (
        "You are a test quality reviewer. "
        "Review Given/When/Then acceptance criteria and identify:\n"
        "1. Weak criteria (untestable, missing negative assertions, missing data integrity checks)\n"
        "2. Good criteria worth highlighting\n\n"
        "Respond with ONLY valid JSON, no markdown fences, no explanation.\n"
        "Schema:\n"
        '{"weak": [{"use_case_id": str, "issue": str, "suggestion": str}], '
        '"good": ["use_case_id_string"]}'
    )

    user = (
        "Here are sampled use cases with Given/When/Then criteria.\n\n"
        f"{summary}\n\n"
        "Identify weak acceptance criteria and good examples."
    )

    return {"system": system, "user": user}


# ── pruning_second_opinion (gemini) — Phase 6 ───────────────────────────────

def pruning_second_opinion_prompt(decisions, tasks_dict, flow_task_refs):
    """Build prompts for pruning decision second-opinion review.

    Args:
        decisions: list of prune decision dicts (item_id, item_name, decision, reason)
        tasks_dict: {task_id: task} mapping
        flow_task_refs: set of task IDs referenced by business flows
    """
    # Prioritize CUT/DEFER decisions, cap at 50 entries
    sorted_decs = sorted(decisions, key=lambda d: {"CUT": 0, "DEFER": 1}.get(d["decision"], 2))
    summary = []
    for d in sorted_decs[:50]:
        tid = d["item_id"]
        task = tasks_dict.get(tid, {})
        summary.append({
            "task_id": tid,
            "name": d["item_name"],
            "decision": d["decision"],
            "frequency": task.get("frequency", "?"),
            "category": task.get("category", "?"),
            "risk_level": task.get("risk_level", "?"),
            "in_business_flow": tid in flow_task_refs,
            "reason_snippet": d["reason"][:80],
        })

    system = (
        "You are a product scope reviewer. "
        "Review CORE/DEFER/CUT pruning decisions for a product feature set.\n"
        "Identify:\n"
        "1. Risky CUTs — features that should NOT be cut (revenue-critical, "
        "security-essential, or referenced in business flows)\n"
        "2. Over-kept features — low-value CORE items that could be DEFER\n"
        "3. Missing rationale — decisions that lack clear justification\n\n"
        "Respond with ONLY valid JSON, no markdown fences, no explanation.\n"
        "Schema:\n"
        '{"risky_cuts": [{"task_id": str, "reason": str, "recommended": "CORE"|"DEFER"}], '
        '"over_kept": [{"task_id": str, "reason": str, "recommended": "DEFER"|"CUT"}], '
        '"weak_rationale": [{"task_id": str, "issue": str}]}'
    )

    user = (
        "Here are feature pruning decisions. Each entry shows the task, decision "
        "(CORE/DEFER/CUT), frequency, category, risk level, and whether it's in a business flow.\n\n"
        f"{json.dumps(summary, ensure_ascii=False, indent=2)}\n\n"
        "Identify risky CUTs, over-kept COREs, and decisions with weak rationale."
    )

    return {"system": system, "user": user}


# ── competitive_benchmark (deepseek) — Phase 6 ─────────────────────────────

def competitive_benchmark_prompt(comp_ref, decisions):
    """Build prompts for competitive coverage validation.

    Args:
        comp_ref: competitive-ref dict with features and competitor coverage
        decisions: prune decisions list
    """
    decision_map = {d["item_id"]: d["decision"] for d in decisions}
    summary = []
    for feat in comp_ref.get("features", []):
        tid = feat.get("task_id", "")
        summary.append({
            "task_id": tid,
            "name": feat.get("name", ""),
            "competitor_coverage": feat.get("competitor_coverage", "unknown"),
            "prune_decision": decision_map.get(tid, "?"),
        })

    system = (
        "You are a competitive analysis expert. "
        "Review feature pruning decisions against competitor coverage.\n"
        "Identify:\n"
        "1. Competitive risks — features all competitors have but are being CUT/DEFERRED\n"
        "2. Differentiation opportunities — features no competitor has that are CORE "
        "(potential differentiators worth highlighting)\n\n"
        "Respond with ONLY valid JSON, no markdown fences, no explanation.\n"
        "Schema:\n"
        '{"competitive_risks": [{"task_id": str, "name": str, "coverage": str, "risk": str}], '
        '"differentiators": [{"task_id": str, "name": str, "opportunity": str}]}'
    )

    user = (
        "Here are features with competitor coverage (all_have/some_have/none_have) "
        "and pruning decisions (CORE/DEFER/CUT).\n\n"
        f"{json.dumps(summary, ensure_ascii=False, indent=2)}\n\n"
        "Identify competitive risks and differentiation opportunities."
    )

    return {"system": system, "user": user}


# ── design_review (gemini) — Phase 7 ────────────────────────────────────────

def design_review_prompt(spec_text, screen_count, role_count):
    """Build prompts for UI design spec review.

    Args:
        spec_text: the full ui-design-spec.md content (truncated to ~4000 chars)
        screen_count: total screens
        role_count: total roles
    """
    truncated = spec_text[:4000]

    system = (
        "You are a UX design reviewer. "
        "Review a UI design specification and identify:\n"
        "1. Usability issues — inconsistent patterns, missing states, accessibility gaps\n"
        "2. Missing patterns — common UX patterns expected but not specified\n"
        "3. Strengths — well-designed aspects worth preserving\n\n"
        "Respond with ONLY valid JSON, no markdown fences, no explanation.\n"
        "Schema:\n"
        '{"usability_issues": [{"screen_or_section": str, "issue": str, "severity": "high"|"medium"|"low", "suggestion": str}], '
        '"missing_patterns": [{"pattern": str, "context": str}], '
        '"strengths": [str]}'
    )

    user = (
        f"Here is a UI design spec for a product with {role_count} roles and {screen_count} screens.\n\n"
        f"{truncated}\n\n"
        "Review for usability issues, missing patterns, and strengths."
    )

    return {"system": system, "user": user}


# ── visual_consistency (gpt) — Phase 7 ──────────────────────────────────────

def visual_consistency_prompt(screens, style_config):
    """Build prompts for design system consistency check.

    Args:
        screens: list of screen objects
        style_config: style dict (primary, secondary, radius, etc.)
    """
    summary = []
    for s in screens[:30]:
        summary.append({
            "name": s.get("name", ""),
            "module": s.get("module", ""),
            "action_count": len(s.get("actions", [])),
            "has_notes": bool(s.get("notes")),
        })

    system = (
        "You are a design system consistency checker. "
        "Given a screen inventory and design tokens, identify:\n"
        "1. Inconsistencies — screens that likely need different treatment "
        "but share the same template\n"
        "2. Token gaps — missing design tokens for common states\n"
        "3. Module grouping issues — screens that seem misplaced\n\n"
        "Respond with ONLY valid JSON, no markdown fences, no explanation.\n"
        "Schema:\n"
        '{"inconsistencies": [{"screens": [str], "issue": str}], '
        '"token_gaps": [{"token": str, "context": str}], '
        '"grouping_issues": [{"screen": str, "current_module": str, "suggested_module": str}]}'
    )

    user = (
        f"Design tokens: {json.dumps(style_config, ensure_ascii=False)}\n\n"
        f"Screen inventory ({len(screens)} total, showing first 30):\n"
        f"{json.dumps(summary, ensure_ascii=False, indent=2)}\n\n"
        "Check for design system inconsistencies, missing tokens, and grouping issues."
    )

    return {"system": system, "user": user}


# ── cross_layer_validation (deepseek) — Phase 8 ─────────────────────────────

def cross_layer_validation_prompt(trace_issues, cross_issues, available_layers):
    """Build prompts for semantic cross-layer validation.

    Args:
        trace_issues: list of trace (orphan) issues from audit
        cross_issues: list of cross-check issues from audit
        available_layers: list of available layer names
    """
    # Add stable composite IDs for round-trip matching
    tagged_trace = []
    for i, ti in enumerate(trace_issues[:15]):
        entry = dict(ti)
        entry["_xv_id"] = f"TRACE-{ti.get('check_id', '')}-{ti.get('item_id', '')}"
        tagged_trace.append(entry)

    tagged_cross = []
    for i, ci in enumerate(cross_issues[:15]):
        entry = dict(ci)
        entry["_xv_id"] = f"CROSS-{ci.get('check_id', '')}-{ci.get('task_id', '')}"
        tagged_cross.append(entry)

    summary = {
        "layers": available_layers,
        "trace_issues": tagged_trace,
        "cross_issues": tagged_cross,
    }

    system = (
        "You are a design system integrity validator. "
        "Given automated audit findings (orphans + cross-layer conflicts), identify:\n"
        "1. Deeper root causes — issues that share a common root cause\n"
        "2. Missed connections — cross-layer inconsistencies the automated checks missed\n"
        "3. False alarms — automated findings that are likely false positives\n\n"
        "Respond with ONLY valid JSON, no markdown fences, no explanation.\n"
        "Each issue has a `_xv_id` field — use it exactly as-is when referencing issues.\n"
        "Schema:\n"
        '{"root_causes": [{"description": str, "affected_issues": ["_xv_id_string"], "severity": "high"|"medium"|"low"}], '
        '"missed_connections": [{"layer_a": str, "layer_b": str, "issue": str, "severity": "high"|"medium"|"low"}], '
        '"false_alarms": [{"issue_id": "_xv_id_string", "reason": str}]}'
    )

    user = (
        f"Available design layers: {', '.join(available_layers)}\n\n"
        f"Trace issues (orphan references):\n{json.dumps(summary['trace_issues'], ensure_ascii=False, indent=2)}\n\n"
        f"Cross-check issues (conflicts/warnings):\n{json.dumps(summary['cross_issues'], ensure_ascii=False, indent=2)}\n\n"
        "Analyze root causes, find missed cross-layer connections, and flag false alarms."
    )

    return {"system": system, "user": user}


# ── coverage_analysis (gpt) — Phase 8 ───────────────────────────────────────

def coverage_analysis_prompt(coverage_issues, task_count, layer_count):
    """Build prompts for coverage gap analysis.

    Args:
        coverage_issues: list of coverage gap issues from audit
        task_count: total task count
        layer_count: number of available layers
    """
    by_layer = {}
    for ci in coverage_issues:
        layer = ci.get("missing_in", "unknown")
        by_layer.setdefault(layer, []).append({
            "task_id": ci["task_id"],
            "name": ci["name"],
        })

    system = (
        "You are a product coverage analyst. "
        "Given coverage gaps (tasks missing from certain design layers), identify:\n"
        "1. Critical gaps — missing coverage that poses high risk\n"
        "2. Acceptable gaps — gaps that are OK to leave uncovered (e.g., admin-only features)\n"
        "3. Patterns — systematic coverage failures that suggest a process issue\n\n"
        "Respond with ONLY valid JSON, no markdown fences, no explanation.\n"
        "Schema:\n"
        '{"critical_gaps": [{"task_id": str, "name": str, "missing_in": str, "risk": str}], '
        '"acceptable_gaps": [{"task_id": str, "reason": str}], '
        '"patterns": [{"pattern": str, "affected_count": int, "suggestion": str}]}'
    )

    user = (
        f"Product has {task_count} tasks across {layer_count} design layers.\n\n"
        f"Coverage gaps grouped by missing layer:\n{json.dumps(by_layer, ensure_ascii=False, indent=2)}\n\n"
        "Identify critical gaps, acceptable gaps, and systematic patterns."
    )

    return {"system": system, "user": user}
