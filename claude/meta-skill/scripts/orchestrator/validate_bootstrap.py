#!/usr/bin/env python3
"""Validate bootstrap products: workflow.json + node-specs/*.md.

Checks:
  - workflow.json: schema valid, nodes non-empty, each node has node_id, goal/capability/exit_artifacts
  - workflow.json: consumers[]/hard_blocked_by[]/unlocks[]/alignment_refs[] references point to existing node IDs
  - workflow.json: exit_artifacts paths are not bare filenames
  - workflow.json nodes have matching node-specs, and node-specs are not orphaned
  - node-spec frontmatter matches workflow node_id, exit_artifacts, and graph fields
  - human_gate workflow nodes have matching approval records
  - app-design workflow closure emits handoff/QA artifacts and routes execution through concept-freeze
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


def _artifact_path(item) -> str:
    if isinstance(item, dict):
        return item.get("path", "")
    return item


def _artifact_paths(items) -> list:
    if not isinstance(items, list):
        return []
    return [_artifact_path(item) for item in items]


def _read_node_spec(path: str) -> tuple:
    try:
        with open(path) as f:
            text = f.read()
    except Exception as e:
        return None, "", [f"cannot read: {e}"]

    if not text.startswith("---"):
        return None, text, ["no YAML frontmatter (missing opening ---)"]

    second = text.find("---", 3)
    if second == -1:
        return None, text, ["no closing --- for YAML frontmatter"]

    yaml_text = text[3:second].strip()
    if _HAS_YAML:
        try:
            data = yaml.safe_load(yaml_text)
        except Exception as e:
            return None, text, [f"YAML parse error: {e}"]
        if not isinstance(data, dict):
            return None, text, ["frontmatter is not a dict"]
        return data, text, []

    data = {}
    for line in yaml_text.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip()
    return data, text, []


REFERENCE_FIELDS = ("consumers", "hard_blocked_by", "unlocks", "alignment_refs")


APP_DESIGN_REQUIRED_NODES = {
    "ia-design",
    "user-flow-design",
    "interaction-design",
    "app-design-finalize",
}


APP_DESIGN_FINALIZE_REQUIRED_ARTIFACTS = {
    ".allforai/app-design/app-design-doc.json",
    ".allforai/app-design/app-design-doc.html",
    ".allforai/app-design/handoff/ui-design-input-handoff.json",
    ".allforai/app-design/handoff/program-development-node-handoff.json",
    ".allforai/app-design/qa/app-design-closure-qa-report.json",
}


GAME_2D_PRODUCTION_REQUIRED_NODES = [
    "game-2d-runtime-profile",
    "game-2d-view-mode-runtime-contract",
    "game-2d-core-loop-playable-contract",
    "game-2d-asset-runtime-binding-contract",
    "game-2d-input-feedback-contract",
    "game-2d-session-flow-contract",
    "game-2d-playable-slice-assembly",
    "game-2d-core-loop-playability-qa",
    "game-2d-asset-binding-visual-qa",
    "game-2d-session-completion-qa",
    "game-2d-code-repair-loop",
    "game-2d-production-closure-qa",
]


GAME_2D_PRODUCTION_REQUIRED_ARTIFACTS = {
    ".allforai/game-2d/assembly/playable-slice-assembly-report.json",
    ".allforai/game-2d/qa/core-loop-playability-qa-report.json",
    ".allforai/game-2d/qa/asset-binding-visual-qa-report.json",
    ".allforai/game-2d/qa/session-completion-qa-report.json",
    ".allforai/game-2d/repair/code-repair-loop-report.json",
    ".allforai/game-2d/qa/revalidation-report.json",
    ".allforai/game-2d/qa/2d-production-closure-report.json",
    ".allforai/game-2d/qa/2d-production-closure.html",
}


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
                artifact_path = _artifact_path(raw)
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


def validate_node_spec_contracts(bdir: str) -> list:
    """Ensure node-spec frontmatter mirrors workflow node contracts."""
    errors = []
    workflow_path = os.path.join(bdir, "workflow.json")
    specs_dir = os.path.join(bdir, "node-specs")
    if not os.path.exists(workflow_path) or not os.path.isdir(specs_dir):
        return errors

    try:
        workflow = _load_json(workflow_path)
    except Exception:
        return errors

    nodes = {node.get("node_id"): node for node in workflow.get("nodes", []) if node.get("node_id")}
    for node_id, node in sorted(nodes.items()):
        spec_path = os.path.join(specs_dir, f"{node_id}.md")
        if not os.path.exists(spec_path):
            continue
        data, _text, spec_errors = _read_node_spec(spec_path)
        if spec_errors:
            continue

        if data.get("node") != node_id:
            errors.append(
                f"node-specs/{node_id}.md: frontmatter node '{data.get('node')}' "
                f"does not match workflow node_id '{node_id}'"
            )

        if "exit_artifacts" in data:
            spec_paths = _artifact_paths(data.get("exit_artifacts"))
            workflow_paths = _artifact_paths(node.get("exit_artifacts"))
            if spec_paths != workflow_paths:
                errors.append(
                    f"node-specs/{node_id}.md: frontmatter exit_artifacts {spec_paths} "
                    f"do not match workflow exit_artifacts {workflow_paths}"
                )

        for field in ("hard_blocked_by", "alignment_refs", "unlocks"):
            if field in data:
                spec_value = data.get(field) or []
                workflow_value = node.get(field) or []
                if spec_value != workflow_value:
                    errors.append(
                        f"node-specs/{node_id}.md: frontmatter {field} {spec_value} "
                        f"does not match workflow {field} {workflow_value}"
                    )

    return errors


def validate_approval_records(bdir: str) -> list:
    """Ensure human_gate nodes and approval-records.json stay in sync."""
    errors = []
    workflow_path = os.path.join(bdir, "workflow.json")
    if not os.path.exists(workflow_path):
        return errors

    try:
        workflow = _load_json(workflow_path)
    except Exception:
        return errors

    nodes = [node for node in workflow.get("nodes", []) if node.get("human_gate") is True]
    if not nodes:
        return errors

    by_path = {}
    for node in nodes:
        node_id = node.get("node_id", "?")
        record_path = node.get("approval_record_path")
        if not record_path:
            errors.append(f"workflow.json: {node_id} human_gate missing approval_record_path")
            continue
        by_path.setdefault(record_path, []).append(node)

    for record_path, gated_nodes in sorted(by_path.items()):
        abs_path = os.path.join(os.path.dirname(bdir), "..", record_path)
        abs_path = os.path.normpath(abs_path)
        if not os.path.exists(abs_path):
            errors.append(f"{record_path}: approval records file missing")
            continue
        try:
            data = _load_json(abs_path)
        except Exception as e:
            errors.append(f"{record_path}: cannot parse: {e}")
            continue

        records = data.get("records")
        if not isinstance(records, list):
            errors.append(f"{record_path}: 'records' array missing or not a list")
            continue

        record_by_node = {}
        for index, record in enumerate(records):
            if "node" in record:
                errors.append(f"{record_path}: records[{index}] uses forbidden legacy field 'node'")
            record_node_id = record.get("node_id")
            if not record_node_id:
                errors.append(f"{record_path}: records[{index}] missing node_id")
                continue
            if record_node_id in record_by_node:
                errors.append(f"{record_path}: duplicate record for node_id '{record_node_id}'")
            record_by_node[record_node_id] = record

        expected_ids = {node["node_id"] for node in gated_nodes}
        actual_ids = set(record_by_node)
        for missing in sorted(expected_ids - actual_ids):
            errors.append(f"{record_path}: missing approval record for node_id '{missing}'")
        for extra in sorted(actual_ids - expected_ids):
            errors.append(f"{record_path}: approval record for non-human_gate node_id '{extra}'")

        for node in gated_nodes:
            node_id = node["node_id"]
            record = record_by_node.get(node_id)
            if not record:
                continue
            if (record.get("unlocks") or []) != (node.get("unlocks") or []):
                errors.append(
                    f"{record_path}: record '{node_id}' unlocks {record.get('unlocks') or []} "
                    f"do not match workflow unlocks {node.get('unlocks') or []}"
                )

            checklist = record.get("review_checklist")
            if checklist is not None and not isinstance(checklist, list):
                errors.append(f"{record_path}: record '{node_id}' review_checklist must be a list")

    return errors


def validate_app_design_flow(bdir: str) -> list:
    """Validate app-design planning closes into downstream implementation contracts."""
    errors = []
    workflow_path = os.path.join(bdir, "workflow.json")
    if not os.path.exists(workflow_path):
        return errors

    try:
        workflow = _load_json(workflow_path)
    except Exception:
        return errors

    nodes = {node.get("node_id"): node for node in workflow.get("nodes", []) if node.get("node_id")}
    app_nodes = {
        node_id: node
        for node_id, node in nodes.items()
        if node.get("capability") == "app-design" or node_id in APP_DESIGN_REQUIRED_NODES
    }
    if not app_nodes:
        return errors

    missing_required = sorted(APP_DESIGN_REQUIRED_NODES - set(nodes))
    for node_id in missing_required:
        errors.append(f"workflow.json: app-design workflow missing required node '{node_id}'")

    finalize = nodes.get("app-design-finalize")
    if not finalize:
        return errors

    expected_blockers = sorted(node_id for node_id in app_nodes if node_id != "app-design-finalize")
    actual_blockers = sorted(finalize.get("hard_blocked_by") or [])
    missing_blockers = sorted(set(expected_blockers) - set(actual_blockers))
    if missing_blockers:
        errors.append(
            "workflow.json: app-design-finalize hard_blocked_by missing "
            f"selected app-design nodes {missing_blockers}"
        )

    finalize_artifacts = set(_artifact_paths(finalize.get("exit_artifacts")))
    missing_artifacts = sorted(APP_DESIGN_FINALIZE_REQUIRED_ARTIFACTS - finalize_artifacts)
    if missing_artifacts:
        errors.append(
            "workflow.json: app-design-finalize missing required handoff/closure "
            f"exit_artifacts {missing_artifacts}"
        )

    concept_freeze = nodes.get("concept-freeze")
    if not concept_freeze:
        errors.append("workflow.json: app-design workflow missing concept-freeze node")
    elif "app-design-finalize" not in (concept_freeze.get("hard_blocked_by") or []):
        errors.append("workflow.json: concept-freeze must be hard_blocked_by app-design-finalize")

    for node_id, node in sorted(nodes.items()):
        if node_id == "concept-freeze":
            continue
        if node_id in app_nodes:
            continue
        if "app-design-finalize" in (node.get("hard_blocked_by") or []):
            errors.append(
                f"workflow.json: {node_id} depends directly on app-design-finalize; "
                "depend on concept-freeze instead"
            )

    return errors


def _project_root_from_bootstrap_dir(bdir: str) -> str:
    return os.path.abspath(os.path.join(bdir, "..", ".."))


def _game_2d_handoff_required(project_root: str) -> bool:
    handoff_path = os.path.join(
        project_root,
        ".allforai/game-design/design/program-development-node-handoff.json",
    )
    if not os.path.exists(handoff_path):
        return False

    try:
        handoff = _load_json(handoff_path)
    except Exception:
        return False

    blob = _lower_blob(handoff)
    if "game_2d_production" in blob:
        return True

    # Older handoff files may predate the explicit game_2d_production block.
    # Treat clear 2D client/runtime evidence as requiring the same expansion so
    # stale bootstraps are forced to regenerate instead of silently skipping
    # final 2D production closure.
    two_d_terms = (
        "2d",
        "web-canvas",
        "cocos",
        "phaser",
        "godot_2d",
        "unity_2d",
        "canvas",
    )
    implementation_nodes = handoff.get("implementation_nodes")
    has_program_nodes = isinstance(implementation_nodes, list) and bool(implementation_nodes)
    return has_program_nodes and any(term in blob for term in two_d_terms)


def validate_game_2d_production_flow(bdir: str) -> list:
    """Validate that 2D game handoff expands into concrete production nodes."""
    errors = []
    workflow_path = os.path.join(bdir, "workflow.json")
    specs_dir = os.path.join(bdir, "node-specs")
    if not os.path.exists(workflow_path):
        return errors

    project_root = _project_root_from_bootstrap_dir(bdir)
    if not _game_2d_handoff_required(project_root):
        return errors

    try:
        workflow = _load_json(workflow_path)
    except Exception:
        return errors

    nodes = {node.get("node_id"): node for node in workflow.get("nodes", []) if node.get("node_id")}
    missing_nodes = [node_id for node_id in GAME_2D_PRODUCTION_REQUIRED_NODES if node_id not in nodes]
    if missing_nodes:
        errors.append(
            "workflow.json: game 2D production handoff detected, but workflow is missing "
            f"required game-2d-production nodes {missing_nodes}"
        )
        return errors

    for previous, current in zip(
        GAME_2D_PRODUCTION_REQUIRED_NODES,
        GAME_2D_PRODUCTION_REQUIRED_NODES[1:],
    ):
        blockers = nodes[current].get("hard_blocked_by") or []
        if previous not in blockers:
            errors.append(
                f"workflow.json: {current} must be hard_blocked_by {previous} "
                "for ordered 2D production closure"
            )

    closure = nodes["game-2d-production-closure-qa"]
    closure_artifacts = set(_artifact_paths(closure.get("exit_artifacts")))
    missing_artifacts = sorted(GAME_2D_PRODUCTION_REQUIRED_ARTIFACTS - closure_artifacts)
    if missing_artifacts:
        errors.append(
            "workflow.json: game-2d-production-closure-qa missing required exit_artifacts "
            f"{missing_artifacts}"
        )

    for node_id in GAME_2D_PRODUCTION_REQUIRED_NODES:
        spec_path = os.path.join(specs_dir, f"{node_id}.md")
        if not os.path.exists(spec_path):
            continue
        try:
            with open(spec_path) as f:
                spec_text = f.read()
        except Exception:
            continue
        if "game-2d-production/" not in spec_text:
            errors.append(
                f"node-specs/{node_id}.md: game 2D production node-spec must delegate "
                "to a game-2d-production child skill"
            )

    return errors


def validate_node_spec(path: str) -> list:
    """Validate a single node-spec markdown file."""
    data, _text, errors = _read_node_spec(path)
    if errors:
        return errors
    if "node" not in data:
        errors.append("frontmatter missing 'node' field")

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
        errors.extend(validate_node_spec_contracts(bdir))
        errors.extend(validate_approval_records(bdir))
        errors.extend(validate_app_design_flow(bdir))
        errors.extend(validate_game_2d_production_flow(bdir))
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
    "validate_node_spec_contracts",
    "validate_approval_records",
    "validate_app_design_flow",
    "validate_game_2d_production_flow",
    "validate_mobile_ui_coverage",
]


if __name__ == "__main__":
    main()
