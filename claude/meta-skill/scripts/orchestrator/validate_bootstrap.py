#!/usr/bin/env python3
"""Validate bootstrap products: workflow.json + node-specs/*.md.

Checks:
  - workflow.json: schema valid, nodes non-empty, each node has node_id, goal/capability/exit_artifacts
  - workflow.json: consumers[]/hard_blocked_by[]/unlocks[]/alignment_refs[] references point to existing node IDs
  - workflow.json: exit_artifacts paths are not bare filenames
  - workflow.json nodes have matching node-specs, and node-specs are not orphaned
  - bootstrap-profile.json + workflow.json: mobile UI modules have platform UI automation
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
    return node.get("node_id") or fallback


def _lower_blob(value) -> str:
    """Serialize nested workflow/profile snippets for simple capability matching."""
    try:
        return json.dumps(value, ensure_ascii=False).lower()
    except TypeError:
        return str(value).lower()


def _load_json(path: str):
    with open(path) as f:
        return json.load(f)


REFERENCE_FIELDS = ("consumers", "hard_blocked_by", "unlocks", "alignment_refs")


UI_TEST_PLATFORMS = {
    "android": {
        "display": "Android mobile UI",
        "runner_terms": (
            "connectedandroidtest",
            "espresso",
            "compose ui",
            "android-ui",
            "android ui",
            "maestro",
        ),
        "evidence_terms": (
            "android-ui-test-report",
            "android-logcat",
            "android-ui-screenshots",
            "connectedandroidtest",
        ),
    },
    "ios": {
        "display": "iOS mobile UI",
        "runner_terms": (
            "xcodebuild test",
            "xcuitest",
            "xctest",
            "ios-ui",
            "ios ui",
        ),
        "evidence_terms": (
            "ios-ui-test-report",
            "xcresult",
            "ios-ui-screenshots",
            "xcodebuild test",
        ),
    },
    "flutter": {
        "display": "Flutter mobile UI",
        "runner_terms": (
            "flutter test integration_test",
            "integration_test/",
            "patrol",
            "flutter-ui",
            "flutter ui",
        ),
        "evidence_terms": (
            "flutter-ui-test-report",
            "integration_test",
            "flutter-ui-screenshots",
            "patrol",
        ),
    },
    "react-native": {
        "display": "React Native mobile UI",
        "runner_terms": (
            "detox",
            "maestro",
            "react-native-ui",
            "react native ui",
        ),
        "evidence_terms": (
            "react-native-ui-test-report",
            "detox",
            "maestro",
            "rn-ui-screenshots",
        ),
    },
    "harmonyos": {
        "display": "HarmonyOS mobile UI",
        "runner_terms": (
            "hypium",
            "ohostest",
            "hdc",
            "harmony-ui",
            "harmonyos ui",
        ),
        "evidence_terms": (
            "harmony-ui-test-report",
            "hypium",
            "ohostest",
            "hdc",
        ),
    },
}


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
        if "id" in node:
            errors.append(f"workflow.json: {nid} uses forbidden legacy field 'id'; use 'node_id'")
        if "blocked_by" in node:
            errors.append(f"workflow.json: {nid} uses forbidden legacy field 'blocked_by'; use 'hard_blocked_by'")
        if not node.get("node_id"):
            errors.append(f"workflow.json: node[{i}] missing 'node_id'")
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

        for field in REFERENCE_FIELDS:
            if field not in node:
                continue
            if not isinstance(node[field], list):
                errors.append(f"workflow.json: {nid} '{field}' must be a list")
                continue
            for cid in node[field]:
                if cid not in node_ids:
                    errors.append(
                        f"workflow.json: {nid} {field} references "
                        f"non-existent node '{cid}'"
                    )

    return errors


def _profile_has_mobile_ui_module(profile: dict) -> bool:
    """Detect mobile app modules with user-facing screens."""
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


def _required_mobile_ui_platforms(profile: dict) -> list:
    """Infer platform-specific UI automation requirements from bootstrap profile."""
    if not _profile_has_mobile_ui_module(profile):
        return []

    blob = _lower_blob(profile)
    required = []

    if "flutter" in blob:
        required.append("flutter")
    if "react native" in blob or "react-native" in blob or "expo" in blob:
        required.append("react-native")
    if "harmonyos" in blob or "arkts" in blob or "deveco" in blob or "hypium" in blob:
        required.append("harmonyos")

    native_mobile_frameworks = {"flutter", "react-native", "harmonyos"}
    if not any(platform in required for platform in native_mobile_frameworks):
        if (
            "ios" in blob
            or "swiftui" in blob
            or "swift" in blob
            or "xcodebuild" in blob
            or "xcuitest" in blob
        ):
            required.append("ios")
        if (
            "android" in blob
            or "kotlin" in blob
            or "jetpack compose" in blob
            or "connectedandroidtest" in blob
        ):
            required.append("android")

    return required


def _node_blob(node: dict, specs_dir: str) -> str:
    nid = _node_id(node)
    blob = _lower_blob(node)
    spec_path = os.path.join(specs_dir, f"{nid}.md")
    if os.path.exists(spec_path):
        try:
            with open(spec_path) as f:
                blob += "\n" + f.read().lower()
        except Exception:
            pass
    return blob


def _ui_node_present(workflow: dict, specs_dir: str, platform: str) -> bool:
    """Return true when workflow contains a real platform UI automation node."""
    spec = UI_TEST_PLATFORMS[platform]
    runner_terms = spec["runner_terms"]
    evidence_terms = spec["evidence_terms"]

    for node in workflow.get("nodes", []):
        node_blob = _node_blob(node, specs_dir)

        if not any(term in node_blob for term in runner_terms):
            continue

        manual_only = (
            "manual — requires device" in node_blob
            or "manual - requires device" in node_blob
            or "document manual test scenarios" in node_blob
        )
        has_runner = any(term in node_blob for term in runner_terms)
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

    for platform in _required_mobile_ui_platforms(profile):
        if not _ui_node_present(workflow, specs_dir, platform):
            spec = UI_TEST_PLATFORMS[platform]
            errors.append(
                f"workflow.json: {spec['display']} module detected, but no platform UI "
                f"automation node with runner evidence was found. Generate a dedicated "
                f"UI automation/e2e-test node for {platform} and report BLOCKED_ENV if "
                f"the required device, simulator, emulator, or service is unavailable; "
                f"do not replace it with manual scenarios."
            )

    return errors


def validate_node_spec_coverage(bdir: str) -> list:
    """Ensure workflow nodes and node-spec files stay in sync."""
    errors = []
    workflow_path = os.path.join(bdir, "workflow.json")
    specs_dir = os.path.join(bdir, "node-specs")
    if not os.path.exists(workflow_path) or not os.path.isdir(specs_dir):
        return errors

    try:
        workflow = _load_json(workflow_path)
    except Exception:
        return errors

    node_ids = {_node_id(node) for node in workflow.get("nodes", []) if _node_id(node)}
    spec_ids = {
        os.path.splitext(fname)[0]
        for fname in os.listdir(specs_dir)
        if fname.endswith(".md")
    }

    for node_id in sorted(node_ids - spec_ids):
        errors.append(f"node-specs: workflow node '{node_id}' has no matching node-spec file")
    for spec_id in sorted(spec_ids - node_ids):
        errors.append(f"node-specs/{spec_id}.md: no matching workflow node")

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
        errors.extend(validate_node_spec_coverage(bdir))
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
__all__ = [
    "validate_workflow",
    "validate_node_spec",
    "validate_node_spec_coverage",
    "validate_mobile_ui_coverage",
]


if __name__ == "__main__":
    main()
