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
                    "task_name": t["task_name"],
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
