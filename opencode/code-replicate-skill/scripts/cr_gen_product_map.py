#!/usr/bin/env python3
"""Generate the summary product-map.json from merged artifacts.

CLI: python3 cr_gen_product_map.py <base_path>

Reads task-inventory.json, role-profiles.json, business-flows.json,
optionally constraints.json → produces product-map.json.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _common import (
    require_json,
    load_json,
    ensure_list,
    get_flow_nodes,
    now_iso,
    write_json,
)


def _infer_experience_priority(roles, tasks):
    """Infer experience_priority from role audience_type and task distribution.

    Returns a dict matching the product-design experience_priority schema.
    """
    consumer_roles = [r for r in roles if r.get("audience_type") == "consumer"]
    professional_roles = [r for r in roles if r.get("audience_type") == "professional"]

    has_consumer = len(consumer_roles) > 0
    has_professional = len(professional_roles) > 0

    # Count tasks owned by consumer vs professional roles
    consumer_role_ids = {r.get("id") for r in consumer_roles}
    consumer_task_count = sum(1 for t in tasks if t.get("owner_role") in consumer_role_ids)
    total_tasks = len(tasks)

    consumer_ratio = consumer_task_count / total_tasks if total_tasks > 0 else 0

    reasoning = []
    if not has_consumer and not has_professional:
        # No roles with audience_type — cannot determine, default to mixed
        mode = "mixed"
        primary = "mixed"
        reasoning = [
            "No roles with audience_type detected — defaulting to mixed mode",
            "LLM fragments should include audience_type for accurate inference",
        ]
    elif has_consumer and not has_professional:
        mode = "consumer"
        primary = "web-customer"
        reasoning = [
            "All roles are consumer-facing — no professional/admin roles detected",
            "Source code analysis shows only end-user interfaces",
        ]
    elif not has_consumer and has_professional:
        mode = "admin"
        primary = "admin"
        reasoning = [
            "All roles are professional/admin — no consumer-facing roles detected",
            "Source code analysis shows only back-office/management interfaces",
        ]
    elif consumer_ratio > 0.6:
        mode = "consumer"
        primary = "web-customer"
        reasoning = [
            f"Consumer roles own {consumer_task_count}/{total_tasks} tasks ({consumer_ratio:.0%})",
            "Consumer-facing functionality dominates the product surface",
        ]
    elif consumer_ratio < 0.3:
        mode = "admin"
        primary = "admin"
        reasoning = [
            f"Professional roles own majority of tasks ({1-consumer_ratio:.0%})",
            "Administrative/management functionality dominates the product surface",
        ]
    else:
        mode = "mixed"
        primary = "mixed"
        reasoning = [
            f"Both consumer ({consumer_ratio:.0%}) and professional ({1-consumer_ratio:.0%}) roles are significant",
            "Product serves both end-users and operators with substantial task coverage",
        ]

    return {
        "mode": mode,
        "consumer_surface": has_consumer,
        "consumer_core": has_consumer and consumer_ratio > 0.4,
        "primary_experience": primary,
        "reasoning": reasoning,
    }


def generate_product_map(base_path):
    """Generate product-map.json summary."""
    pm_dir = os.path.join(base_path, ".allforai", "product-map")

    tasks_data = require_json(os.path.join(pm_dir, "task-inventory.json"), "task-inventory")
    roles_data = require_json(os.path.join(pm_dir, "role-profiles.json"), "role-profiles")
    flows_data = require_json(os.path.join(pm_dir, "business-flows.json"), "business-flows")

    tasks = ensure_list(tasks_data, "tasks")
    roles = ensure_list(roles_data, "roles")
    flows = ensure_list(flows_data, "flows")

    # Constraints (optional)
    constraints_data = load_json(os.path.join(pm_dir, "constraints.json"))
    constraints = ensure_list(constraints_data, "constraints") if constraints_data else []

    # Scale
    task_count = len(tasks)
    if task_count <= 30:
        scale = "small"
    elif task_count <= 80:
        scale = "medium"
    else:
        scale = "large"

    # Category counts
    basic_count = sum(1 for t in tasks if str(t.get("category", "")).lower() == "basic")
    core_count = sum(1 for t in tasks if str(t.get("category", "")).lower() == "core")

    # Frequency / risk
    high_freq_count = sum(1 for t in tasks if "high" in str(t.get("frequency", "")).lower())
    high_risk_count = sum(1 for t in tasks if "high" in str(t.get("risk_level", "")).lower())

    # Flow gaps
    flow_gaps = 0
    referenced_task_ids = set()
    for flow in flows:
        nodes = get_flow_nodes(flow)
        flow_gaps += sum(1 for n in nodes if n.get("gap"))
        for n in nodes:
            tid = n.get("task_id") or n.get("task_ref")
            if tid:
                referenced_task_ids.add(tid)

    # Orphan tasks (not referenced in any flow)
    all_task_ids = {t.get("id", "") for t in tasks}
    orphan_task_count = len(all_task_ids - referenced_task_ids)

    # Experience priority (P0 — dev-forge reads this to control consumer maturity checks)
    experience_priority = _infer_experience_priority(roles, tasks)

    output = {
        "generated_at": now_iso(),
        "version": "2.6.0",
        "source": "code-replicate",
        "scope": "full",
        "scale": scale,
        "experience_priority": experience_priority,
        "summary": {
            "role_count": len(roles),
            "task_count": task_count,
            "flow_count": len(flows),
            "flow_gaps": flow_gaps,
            "orphan_task_count": orphan_task_count,
            "basic_count": basic_count,
            "core_count": core_count,
            "high_freq_count": high_freq_count,
            "high_risk_count": high_risk_count,
            "conflict_count": 0,
            "constraint_count": len(constraints),
            "validation_issues": 0,
            "competitor_gaps": 0,
        },
        "roles": roles,
        "tasks": tasks,
        "conflicts": [],
        "constraints": constraints,
    }

    output_path = os.path.join(pm_dir, "product-map.json")
    write_json(output_path, output)

    print(f"Generated product-map ({task_count} tasks, {scale}) → {output_path}", file=sys.stderr)
    return output_path


def main():
    if len(sys.argv) < 2:
        print("Usage: cr_gen_product_map.py <base_path>", file=sys.stderr)
        sys.exit(1)
    generate_product_map(sys.argv[1])


if __name__ == "__main__":
    main()
