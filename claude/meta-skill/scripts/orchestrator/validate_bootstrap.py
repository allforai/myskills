#!/usr/bin/env python3
"""Validate bootstrap products: workflow.json + node-specs/*.md.

Checks:
  - workflow.json: schema valid, nodes non-empty, each node has id/node_id, goal/capability/exit_artifacts
  - workflow.json: consumers[] references point to existing node IDs
  - workflow.json: exit_artifacts paths are not bare filenames
  - bootstrap-profile.json + workflow.json: Android UI modules have platform UI automation
  - node-specs/*.md: YAML frontmatter parseable, 'node' field present
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


def _node_id(node: dict, fallback: str = "") -> str:
    """Return the canonical workflow node identifier."""
    return node.get("id") or node.get("node_id") or fallback


def _lower_blob(value) -> str:
    """Serialize nested workflow/profile snippets for simple capability matching."""
    try:
        return json.dumps(value, ensure_ascii=False).lower()
    except TypeError:
        return str(value).lower()


def _load_json(path: str):
    with open(path) as f:
        return json.load(f)


def validate_workflow(wf_path: str) -> list:
    """Validate workflow.json schema."""
    errors = []
    try:
        wf = _load_json(wf_path)
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

    node_ids = {_node_id(n) for n in wf["nodes"] if _node_id(n)}

    for i, node in enumerate(wf["nodes"]):
        nid = _node_id(node, f"node[{i}]")
        if not _node_id(node):
            errors.append(f"workflow.json: node[{i}] missing 'id' or 'node_id'")
        if "goal" not in node:
            errors.append(f"workflow.json: {nid} missing 'goal'")
        if "capability" not in node:
            errors.append(f"workflow.json: {nid} missing 'capability'")
        elif not isinstance(node["capability"], str) or not node["capability"]:
            errors.append(f"workflow.json: {nid} 'capability' must be a non-empty string")
        if "exit_artifacts" not in node:
            errors.append(f"workflow.json: {nid} missing 'exit_artifacts'")
        elif not isinstance(node["exit_artifacts"], list):
            errors.append(f"workflow.json: {nid} exit_artifacts must be a list")
        else:
            for raw in node["exit_artifacts"]:
                if isinstance(raw, dict):
                    artifact_path = raw.get("path", "")
                else:
                    artifact_path = raw
                basename = os.path.basename(artifact_path)
                if artifact_path == basename and basename in SUSPICIOUS_BARE:
                    errors.append(
                        f"workflow.json: {nid} exit_artifact '{artifact_path}' "
                        f"looks like a bare filename — use full project-relative "
                        f"path (e.g., 'subdir/{artifact_path}' not '{artifact_path}')"
                    )

        if "consumers" in node:
            if not isinstance(node["consumers"], list):
                errors.append(f"workflow.json: {nid} 'consumers' must be a list")
            else:
                for cid in node["consumers"]:
                    if cid not in node_ids:
                        errors.append(
                            f"workflow.json: {nid} consumers references "
                            f"non-existent node '{cid}'"
                        )

    return errors


def _profile_has_android_ui_module(profile: dict) -> bool:
    """Detect Android app modules that need runtime UI automation."""
    stack_blob = _lower_blob(profile.get("tech_stacks", []))
    test_blob = _lower_blob(profile.get("test_commands", {}))
    android_stack = (
        "android" in stack_blob
        or "kotlin" in stack_blob
        or "jetpack compose" in stack_blob
        or "connectedandroidtest" in test_blob
    )
    if not android_stack:
        return False

    for module in profile.get("modules", []):
        module_blob = _lower_blob(module)
        if module.get("role") == "mobile" and (
            "ui" in module_blob
            or "screen" in module_blob
            or "compose" in module_blob
            or "app/" in module_blob
            or "android" in module_blob
        ):
            return True

    return False


def _android_ui_node_present(workflow: dict, specs_dir: str) -> bool:
    """Return true when workflow contains a real Android UI automation node."""
    android_terms = (
        "connectedandroidtest",
        "espresso",
        "compose ui",
        "android-ui",
        "android ui",
        "maestro",
    )
    evidence_terms = (
        "android-ui-test-report",
        "android-logcat",
        "android-ui-screenshots",
        "connectedandroidtest",
    )

    for node in workflow.get("nodes", []):
        nid = _node_id(node)
        node_blob = _lower_blob(node)
        spec_path = os.path.join(specs_dir, f"{nid}.md")
        if os.path.exists(spec_path):
            try:
                with open(spec_path) as f:
                    node_blob += "\n" + f.read().lower()
            except Exception:
                pass

        if not any(term in node_blob for term in android_terms):
            continue

        manual_only = (
            "manual — requires device" in node_blob
            or "manual - requires device" in node_blob
            or "document manual test scenarios" in node_blob
        )
        has_runner = "connectedandroidtest" in node_blob or "maestro" in node_blob
        has_evidence = any(term in node_blob for term in evidence_terms)
        has_blocked_env = "blocked_env" in node_blob or "failed_env" in node_blob

        if has_runner and (has_evidence or has_blocked_env) and not manual_only:
            return True

    return False


def validate_mobile_ui_coverage(bdir: str) -> list:
    """Ensure mobile UI projects do not lose platform UI automation at bootstrap."""
    errors = []
    profile_path = os.path.join(bdir, "bootstrap-profile.json")
    workflow_path = os.path.join(bdir, "workflow.json")
    specs_dir = os.path.join(bdir, "node-specs")

    if not os.path.exists(profile_path) or not os.path.exists(workflow_path):
        return errors

    try:
        profile = _load_json(profile_path)
        workflow = _load_json(workflow_path)
    except Exception:
        return errors

    if not _profile_has_android_ui_module(profile):
        return errors

    if not _android_ui_node_present(workflow, specs_dir):
        errors.append(
            "workflow.json: Android mobile UI module detected, but no Android UI "
            "automation node with connectedAndroidTest/Espresso/Compose UI/Maestro "
            "evidence was found. Generate android-ui-verify/e2e-test-* and report "
            "BLOCKED_ENV if no device or emulator is available; do not replace it "
            "with manual scenarios."
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
        errors.extend(validate_mobile_ui_coverage(bdir))
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
__all__ = ["validate_workflow", "validate_node_spec", "validate_mobile_ui_coverage"]


if __name__ == "__main__":
    main()
