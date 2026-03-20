#!/usr/bin/env python3
"""Generate the final replicate-report.md summarising all generated artifacts.

CLI: python3 cr_gen_report.py <base_path>

Reads replicate-config.json + all generated artifacts → produces replicate-report.md.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _common import (
    require_json,
    load_json,
    ensure_list,
    now_iso,
    write_markdown,
)


def _count_use_cases(uc_data):
    """Count total use cases.

    Supports formats:
    - v2.5.0+ flat: use_cases[] (top-level array)
    - 4-layer tree: tree[].feature_areas[].tasks[].use_cases[]
    - flat roles:   roles[].features[].use_cases[]
    """
    if not uc_data:
        return 0
    # v2.5.0+ flat format
    flat = uc_data.get("use_cases")
    if flat and isinstance(flat, list):
        return len(flat)
    # Legacy tree formats
    roles = ensure_list(uc_data, "tree", "roles")
    total = 0
    for role in roles:
        features = ensure_list(role, "feature_areas", "features")
        for feature in features:
            tasks = ensure_list(feature, "tasks")
            if tasks:
                for task in tasks:
                    total += len(ensure_list(task, "use_cases"))
            else:
                total += len(ensure_list(feature, "use_cases"))
    return total


def _coverage_warnings(module_count, file_count, task_count, role_count, flow_count):
    """Detect suspiciously sparse extraction for large codebases.

    Returns list of warning strings when extraction density is too low.
    """
    warnings = []

    if file_count <= 0:
        return warnings

    # Heuristic: expect roughly 1 task per 10-30 code files
    expected_tasks_low = file_count // 30
    if expected_tasks_low > 20 and task_count < expected_tasks_low:
        warnings.append(
            f"⚠️ Low task density: {task_count} tasks extracted from {file_count} code files "
            f"(expected ≥{expected_tasks_low}). Module discovery may have missed inner modules — "
            f"consider re-running with `--from-phase 2` after verifying source-summary.json"
        )

    # Heuristic: expect roughly 1 role per 100-200 code files
    expected_roles_low = max(2, file_count // 200)
    if expected_roles_low > 5 and role_count < expected_roles_low:
        warnings.append(
            f"⚠️ Low role density: {role_count} roles extracted from {file_count} code files "
            f"(expected ≥{expected_roles_low}). Auth/RBAC modules may not have been scanned"
        )

    # Heuristic: modules too few relative to files → likely mega-modules not split
    if module_count > 0 and file_count / module_count > 200:
        avg = file_count // module_count
        warnings.append(
            f"⚠️ Large average module size: {avg} files/module ({module_count} modules, {file_count} files). "
            f"Inner sub-modules may have been merged — check source-summary.json for accuracy"
        )

    return warnings


def generate_report(base_path):
    """Generate replicate-report.md."""
    allforai = os.path.join(base_path, ".allforai")
    cr_dir = os.path.join(allforai, "code-replicate")

    config = require_json(os.path.join(cr_dir, "replicate-config.json"), "replicate-config")

    source_path = config.get("source_path", "unknown")
    fidelity = config.get("fidelity", "unknown")
    target_stack = config.get("target_stack", "unknown")
    overview = config.get("source_overview", {})
    warnings = config.get("warnings", [])

    module_count = overview.get("module_count", 0)
    file_count = overview.get("file_count", 0)
    line_count = overview.get("line_count", 0)
    stacks = overview.get("detected_stacks", [])
    stacks_str = ", ".join(stacks) if stacks else "none"

    # Load artifact counts
    roles_data = load_json(os.path.join(allforai, "product-map", "role-profiles.json"))
    tasks_data = load_json(os.path.join(allforai, "product-map", "task-inventory.json"))
    flows_data = load_json(os.path.join(allforai, "product-map", "business-flows.json"))
    uc_data = load_json(os.path.join(allforai, "use-case", "use-case-tree.json"))

    role_count = len(ensure_list(roles_data, "roles")) if roles_data else 0
    task_count = len(ensure_list(tasks_data, "tasks")) if tasks_data else 0
    flow_count = len(ensure_list(flows_data, "flows")) if flows_data else 0
    uc_count = _count_use_cases(uc_data)

    lines = []
    lines.append("# Code Replicate Report")
    lines.append("")
    lines.append(f"> Generated: {now_iso()}")
    lines.append(f"> Source: {source_path}")
    lines.append(f"> Fidelity: {fidelity}")
    lines.append(f"> Target Stack: {target_stack}")
    lines.append("")

    # Source Overview
    lines.append("## Source Overview")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Modules | {module_count} |")
    lines.append(f"| Files | {file_count} |")
    lines.append(f"| Lines | {line_count} |")
    lines.append(f"| Detected Stacks | {stacks_str} |")
    lines.append("")

    # Generated Artifacts
    lines.append("## Generated Artifacts")
    lines.append("")
    lines.append("| Artifact | Path | Items |")
    lines.append("|----------|------|-------|")
    lines.append(f"| Roles | product-map/role-profiles.json | {role_count} |")
    lines.append(f"| Tasks | product-map/task-inventory.json | {task_count} |")
    lines.append(f"| Flows | product-map/business-flows.json | {flow_count} |")
    lines.append(f"| Use Cases | use-case/use-case-tree.json | {uc_count} |")
    lines.append("")

    # Coverage analysis
    cov_warnings = _coverage_warnings(module_count, file_count, task_count, role_count, flow_count)

    # Warnings
    lines.append("## Warnings")
    lines.append("")
    all_warnings = list(warnings) + cov_warnings
    if all_warnings:
        for w in all_warnings:
            lines.append(f"- {w}")
    else:
        lines.append("No warnings.")
    lines.append("")

    # Next Steps
    lines.append("## Next Steps")
    lines.append("")
    lines.append("Run: `/project-setup` → `/design-to-spec` → `/task-execute`")
    lines.append("")

    content = "\n".join(lines)
    output_path = os.path.join(cr_dir, "replicate-report.md")
    write_markdown(output_path, content)

    print(f"Generated replicate report → {output_path}", file=sys.stderr)
    return output_path


def main():
    if len(sys.argv) < 2:
        print("Usage: cr_gen_report.py <base_path>", file=sys.stderr)
        sys.exit(1)
    generate_report(sys.argv[1])


if __name__ == "__main__":
    main()
