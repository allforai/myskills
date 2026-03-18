#!/usr/bin/env python3
"""Validate all generated .allforai/ artifacts for schema compliance and cross-reference integrity.

CLI: python3 cr_validate.py <base_path> [--fullstack]

Exit codes: 0 = valid, 1 = invalid

Outputs JSON to stdout with validation results.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _common import FLOW_NODES_FIELD, load_json, ensure_list


# ── Required fields ──────────────────────────────────────────────────────────

TASK_REQUIRED_FIELDS = ("id", "name", "owner_role", "frequency", "risk_level", "main_flow", "status", "category")
ROLE_REQUIRED_FIELDS = ("id", "name")
NODE_REQUIRED_FIELDS = ("task_ref", "role", "seq")
USE_CASE_REQUIRED_FIELDS = ("id", "title", "type", "given", "when", "then")
CONSTRAINT_REQUIRED_FIELDS = ("id", "description", "enforcement")


def validate(base_path, fullstack=False):
    """Run all validation checks and return result dict.

    Returns:
        dict with keys: valid (bool), errors (list), warnings (list), stats (dict)
    """
    errors = []
    warnings = []
    stats = {"tasks": 0, "roles": 0, "flows": 0, "use_cases": 0, "task_ref_coverage": 0.0}

    pm_dir = os.path.join(base_path, ".allforai", "product-map")
    uc_dir = os.path.join(base_path, ".allforai", "use-case")
    em_dir = os.path.join(base_path, ".allforai", "experience-map")
    cr_dir = os.path.join(base_path, ".allforai", "code-replicate")

    # ── 1. task-inventory.json (required) ────────────────────────────────────

    task_ids = set()
    task_inv_path = os.path.join(pm_dir, "task-inventory.json")
    task_data = load_json(task_inv_path)

    if task_data is None:
        errors.append({"file": "task-inventory.json", "path": "", "issue": "file not found or invalid JSON"})
    else:
        raw_tasks = task_data.get("tasks") if isinstance(task_data, dict) else task_data
        if not isinstance(raw_tasks, list):
            errors.append({"file": "task-inventory.json", "path": "tasks", "issue": "tasks field is not an array"})
            raw_tasks = []

        # Check required fields
        seen_ids = set()
        for i, task in enumerate(raw_tasks):
            for field in TASK_REQUIRED_FIELDS:
                if field not in task:
                    errors.append({
                        "file": "task-inventory.json",
                        "path": f"tasks[{i}]",
                        "issue": f"missing required field: {field}"
                    })
            tid = task.get("id")
            if tid:
                if tid in seen_ids:
                    errors.append({
                        "file": "task-inventory.json",
                        "path": f"tasks[{i}]",
                        "issue": f"duplicate task ID: {tid}"
                    })
                seen_ids.add(tid)
                task_ids.add(tid)

        stats["tasks"] = len(raw_tasks)

    # ── 2. role-profiles.json (required) ─────────────────────────────────────

    role_ids = set()
    role_path = os.path.join(pm_dir, "role-profiles.json")
    role_data = load_json(role_path)

    if role_data is None:
        errors.append({"file": "role-profiles.json", "path": "", "issue": "file not found or invalid JSON"})
    else:
        roles = ensure_list(role_data, "roles")
        seen_ids = set()
        for i, role in enumerate(roles):
            for field in ROLE_REQUIRED_FIELDS:
                if field not in role:
                    errors.append({
                        "file": "role-profiles.json",
                        "path": f"roles[{i}]",
                        "issue": f"missing required field: {field}"
                    })
            rid = role.get("id")
            if rid:
                if rid in seen_ids:
                    errors.append({
                        "file": "role-profiles.json",
                        "path": f"roles[{i}]",
                        "issue": f"duplicate role ID: {rid}"
                    })
                seen_ids.add(rid)
                role_ids.add(rid)

        stats["roles"] = len(roles)

    # ── 3. business-flows.json (optional) ────────────────────────────────────

    referenced_task_ids = set()
    flows_path = os.path.join(pm_dir, "business-flows.json")
    flows_data = load_json(flows_path)

    if flows_data is not None:
        flows = ensure_list(flows_data, "flows")
        stats["flows"] = len(flows)

        for fi, flow in enumerate(flows):
            # Check nodes field exists and is array
            nodes = flow.get(FLOW_NODES_FIELD)
            if nodes is None or not isinstance(nodes, list):
                errors.append({
                    "file": "business-flows.json",
                    "path": f"flows[{fi}]",
                    "issue": f"missing or invalid {FLOW_NODES_FIELD} field (must be array)"
                })
                continue

            for ni, node in enumerate(nodes):
                # Check required node fields
                for field in NODE_REQUIRED_FIELDS:
                    if field not in node:
                        errors.append({
                            "file": "business-flows.json",
                            "path": f"flows[{fi}].{FLOW_NODES_FIELD}[{ni}]",
                            "issue": f"missing required field: {field}"
                        })

                # Cross-ref: task_ref
                task_ref = node.get("task_ref")
                if task_ref and task_ref != "[INFERRED]":
                    referenced_task_ids.add(task_ref)
                    if task_ids and task_ref not in task_ids:
                        errors.append({
                            "file": "business-flows.json",
                            "path": f"flows[{fi}].{FLOW_NODES_FIELD}[{ni}]",
                            "issue": f"task_ref {task_ref} not found in task-inventory"
                        })

                # Cross-ref: role
                role_ref = node.get("role")
                if role_ref and role_ref != "[INFERRED]":
                    if role_ids and role_ref not in role_ids:
                        errors.append({
                            "file": "business-flows.json",
                            "path": f"flows[{fi}].{FLOW_NODES_FIELD}[{ni}]",
                            "issue": f"role {role_ref} not found in role-profiles"
                        })

    # ── 4. use-case-tree.json (optional) ─────────────────────────────────────

    uc_path = os.path.join(uc_dir, "use-case-tree.json")
    uc_data = load_json(uc_path)
    use_case_count = 0

    if uc_data is not None:
        tree = ensure_list(uc_data, "tree")
        for ti, entry in enumerate(tree):
            feature_areas = entry.get("feature_areas")
            if not isinstance(feature_areas, list):
                errors.append({
                    "file": "use-case-tree.json",
                    "path": f"tree[{ti}]",
                    "issue": "missing or invalid feature_areas (must be array)"
                })
                continue
            for fi, fa in enumerate(feature_areas):
                tasks = fa.get("tasks")
                if not isinstance(tasks, list):
                    errors.append({
                        "file": "use-case-tree.json",
                        "path": f"tree[{ti}].feature_areas[{fi}]",
                        "issue": "missing or invalid tasks (must be array)"
                    })
                    continue
                for tki, task in enumerate(tasks):
                    use_cases = task.get("use_cases")
                    if not isinstance(use_cases, list):
                        errors.append({
                            "file": "use-case-tree.json",
                            "path": f"tree[{ti}].feature_areas[{fi}].tasks[{tki}]",
                            "issue": "missing or invalid use_cases (must be array)"
                        })
                        continue
                    for ui, uc in enumerate(use_cases):
                        use_case_count += 1
                        for field in USE_CASE_REQUIRED_FIELDS:
                            if field not in uc:
                                errors.append({
                                    "file": "use-case-tree.json",
                                    "path": f"tree[{ti}].feature_areas[{fi}].tasks[{tki}].use_cases[{ui}]",
                                    "issue": f"missing required field: {field}"
                                })

    stats["use_cases"] = use_case_count

    # ── 5. constraints.json (optional — exact mode only) ─────────────────────

    constraints_path = os.path.join(pm_dir, "constraints.json")
    constraints_data = load_json(constraints_path)

    if constraints_data is None:
        warnings.append({"file": "constraints.json", "issue": "not found (expected for exact mode only)"})
    else:
        constraints = ensure_list(constraints_data, "constraints")
        for ci, con in enumerate(constraints):
            for field in CONSTRAINT_REQUIRED_FIELDS:
                if field not in con:
                    errors.append({
                        "file": "constraints.json",
                        "path": f"constraints[{ci}]",
                        "issue": f"missing required field: {field}"
                    })

    # ── 6. experience-map.json (optional — frontend/fullstack) ───────────────

    em_path = os.path.join(em_dir, "experience-map.json")
    em_data = load_json(em_path)

    if em_data is None:
        warnings.append({"file": "experience-map.json", "issue": "not found (expected for frontend/fullstack only)"})
    else:
        op_lines = em_data.get("operation_lines") if isinstance(em_data, dict) else None
        if not isinstance(op_lines, list):
            errors.append({
                "file": "experience-map.json",
                "path": "",
                "issue": "missing or invalid operation_lines (must be array)"
            })

    # ── 7. Cross-reference coverage ──────────────────────────────────────────

    if stats["tasks"] > 0:
        stats["task_ref_coverage"] = round(len(referenced_task_ids & task_ids) / stats["tasks"], 2)
    else:
        stats["task_ref_coverage"] = 0.0

    # ── 8. Fullstack mode ────────────────────────────────────────────────────

    if fullstack:
        ss_path = os.path.join(cr_dir, "source-summary.json")
        ss_data = load_json(ss_path)

        if ss_data is None:
            warnings.append({"file": "source-summary.json", "issue": "not found (expected for fullstack mode)"})
        else:
            api_map = ss_data.get("api_call_map")
            if isinstance(api_map, list):
                for ai, entry in enumerate(api_map):
                    backend_ref = entry.get("backend_task_ref")
                    if backend_ref and task_ids and backend_ref not in task_ids:
                        warnings.append({
                            "file": "source-summary.json",
                            "path": f"api_call_map[{ai}]",
                            "issue": f"backend_task_ref {backend_ref} not found in task-inventory"
                        })

    # ── Result ───────────────────────────────────────────────────────────────

    valid = len(errors) == 0
    return {
        "valid": valid,
        "errors": errors,
        "warnings": warnings,
        "stats": stats,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: cr_validate.py <base_path> [--fullstack]", file=sys.stderr)
        sys.exit(1)

    base_path = sys.argv[1]
    fullstack = "--fullstack" in sys.argv

    result = validate(base_path, fullstack=fullstack)

    # Output JSON to stdout
    print(json.dumps(result, indent=2, ensure_ascii=False))

    # Exit code
    sys.exit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
