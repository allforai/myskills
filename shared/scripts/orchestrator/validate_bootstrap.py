#!/usr/bin/env python3
"""Validate bootstrap products: workflow.json + node-specs/*.md.

Checks:
  - workflow.json: schema valid, nodes non-empty, each node has id/goal/exit_artifacts
  - node-specs/*.md: YAML frontmatter parseable, 'node' field present

No graph connectivity check (nodes have no entry_requires).
"""

import json
import os
import re
import sys

try:
    import yaml
    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False


def validate_workflow(wf_path: str) -> list:
    """Validate workflow.json schema."""
    errors = []
    try:
        with open(wf_path) as f:
            wf = json.load(f)
    except Exception as e:
        return [f"workflow.json: cannot parse: {e}"]

    if "nodes" not in wf or not isinstance(wf["nodes"], list):
        errors.append("workflow.json: 'nodes' array missing or not a list")
        return errors

    if len(wf["nodes"]) == 0:
        errors.append("workflow.json: nodes array is empty")

    # Suspicious bare filenames that likely need a directory prefix
    SUSPICIOUS_BARE = {'.env', 'config.json', 'config.yaml', 'package.json',
                       'go.mod', 'Makefile', 'Dockerfile', 'README.md'}

    for i, node in enumerate(wf["nodes"]):
        nid = node.get("id", f"node[{i}]")
        if "id" not in node:
            errors.append(f"workflow.json: node[{i}] missing 'id'")
        if "goal" not in node:
            errors.append(f"workflow.json: {nid} missing 'goal'")
        if "exit_artifacts" not in node:
            errors.append(f"workflow.json: {nid} missing 'exit_artifacts'")
        elif not isinstance(node["exit_artifacts"], list):
            errors.append(f"workflow.json: {nid} exit_artifacts must be a list")
        else:
            for artifact_path in node["exit_artifacts"]:
                basename = os.path.basename(artifact_path)
                if artifact_path == basename and basename in SUSPICIOUS_BARE:
                    errors.append(
                        f"workflow.json: {nid} exit_artifact '{artifact_path}' "
                        f"looks like a bare filename — use full project-relative "
                        f"path (e.g., 'subdir/{artifact_path}' not '{artifact_path}')"
                    )

    return errors


def validate_node_spec(path: str) -> list:
    """Validate a single node-spec markdown file."""
    errors = []
    try:
        with open(path) as f:
            text = f.read()
    except Exception as e:
        return [f"cannot read: {e}"]

    if not text.startswith("---"):
        errors.append("no YAML frontmatter (missing opening ---)")
        return errors

    second = text.find("---", 3)
    if second == -1:
        errors.append("no closing --- for YAML frontmatter")
        return errors

    yaml_text = text[3:second].strip()
    if _HAS_YAML:
        try:
            data = yaml.safe_load(yaml_text)
            if not isinstance(data, dict):
                errors.append("frontmatter is not a dict")
                return errors
            if "node" not in data:
                errors.append("frontmatter missing 'node' field")
        except Exception as e:
            errors.append(f"YAML parse error: {e}")
    else:
        if "node:" not in yaml_text:
            errors.append("frontmatter missing 'node' field (no YAML lib, regex check)")

    return errors


def main():
    if len(sys.argv) < 2:
        print("Usage: validate_bootstrap.py <bootstrap-dir>")
        sys.exit(1)

    bdir = sys.argv[1]
    errors = []

    wf_path = os.path.join(bdir, "workflow.json")
    if os.path.exists(wf_path):
        errors.extend(validate_workflow(wf_path))
    else:
        sm_path = os.path.join(bdir, "state-machine.json")
        if os.path.exists(sm_path):
            pass  # backward compat: old format, skip validation
        else:
            errors.append("workflow.json not found")

    specs_dir = os.path.join(bdir, "node-specs")
    if os.path.isdir(specs_dir):
        for fname in sorted(os.listdir(specs_dir)):
            if fname.endswith(".md"):
                fpath = os.path.join(specs_dir, fname)
                spec_errors = validate_node_spec(fpath)
                errors.extend([f"node-specs/{fname}: {e}" for e in spec_errors])

    result = {"errors": errors, "passed": len(errors) == 0}
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["passed"] else 1)


# Also export for testing
__all__ = ["validate_workflow", "validate_node_spec"]


if __name__ == "__main__":
    main()
