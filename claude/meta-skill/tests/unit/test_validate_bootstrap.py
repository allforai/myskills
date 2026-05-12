import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../scripts/orchestrator"))
from validate_bootstrap import (
    validate_mobile_ui_coverage,
    validate_node_spec_coverage,
    validate_workflow,
)


def _write_workflow(tmp_path, nodes):
    wf = {"nodes": nodes, "transition_log": []}
    p = tmp_path / "workflow.json"
    p.write_text(json.dumps(wf))
    return str(p)


def _base_node(**overrides):
    node = {
        "node_id": "test-node",
        "goal": "do stuff",
        "capability": "discovery",
        "exit_artifacts": [".allforai/out.json"],
        "consumers": [],
        "hard_blocked_by": [],
        "alignment_refs": [],
        "human_gate": False,
        "discipline_owner": None,
    }
    node.update(overrides)
    return node


def test_string_artifact_passes(tmp_path):
    path = _write_workflow(tmp_path, [_base_node(exit_artifacts=[".allforai/out.json"])])
    errors = validate_workflow(path)
    assert errors == []


def test_dict_artifact_valid_path_passes(tmp_path):
    """Object-form artifact must not TypeError."""
    artifact = {"path": ".allforai/out.json", "validation_commands": []}
    path = _write_workflow(tmp_path, [_base_node(exit_artifacts=[artifact])])
    errors = validate_workflow(path)
    assert errors == []


def test_dict_artifact_suspicious_bare_path_fails(tmp_path):
    """Object-form artifact with suspicious bare path should still error."""
    artifact = {"path": "config.json", "validation_commands": []}
    path = _write_workflow(tmp_path, [_base_node(exit_artifacts=[artifact])])
    errors = validate_workflow(path)
    assert any("bare filename" in e for e in errors)


def test_mixed_artifacts_passes(tmp_path):
    """Mix of string and dict artifacts."""
    artifacts = [
        ".allforai/good.json",
        {"path": ".allforai/also-good.json", "validation_commands": ["true"]},
    ]
    path = _write_workflow(tmp_path, [_base_node(exit_artifacts=artifacts)])
    errors = validate_workflow(path)
    assert errors == []


def test_dependency_reference_to_missing_node_fails(tmp_path):
    path = _write_workflow(
        tmp_path,
        [
            _base_node(
                node_id="consumer",
                hard_blocked_by=["missing-build"],
                unlocks=["missing-next"],
                alignment_refs=["missing-design"],
            )
        ],
    )
    errors = validate_workflow(path)

    assert any("hard_blocked_by references non-existent node 'missing-build'" in e for e in errors)
    assert any("unlocks references non-existent node 'missing-next'" in e for e in errors)
    assert any("alignment_refs references non-existent node 'missing-design'" in e for e in errors)


def test_legacy_id_schema_fails(tmp_path):
    node = _base_node()
    node["id"] = "legacy-id"
    path = _write_workflow(tmp_path, [node])
    errors = validate_workflow(path)

    assert any("forbidden legacy field 'id'" in e for e in errors)


def test_legacy_blocked_by_schema_fails(tmp_path):
    node = _base_node(blocked_by=["upstream"])
    path = _write_workflow(tmp_path, [node, _base_node(node_id="upstream")])
    errors = validate_workflow(path)

    assert any("forbidden legacy field 'blocked_by'" in e for e in errors)


def test_node_id_schema_passes(tmp_path):
    path = _write_workflow(tmp_path, [_base_node(node_id="node-id-style")])
    errors = validate_workflow(path)

    assert errors == []


def test_node_spec_coverage_detects_missing_and_orphan_specs(tmp_path):
    _write_workflow(
        tmp_path,
        [
            _base_node(node_id="has-spec"),
            _base_node(node_id="missing-spec"),
        ],
    )
    (tmp_path / "node-specs").mkdir()
    (tmp_path / "node-specs" / "has-spec.md").write_text("---\nnode: has-spec\n---\n")
    (tmp_path / "node-specs" / "orphan.md").write_text("---\nnode: orphan\n---\n")

    errors = validate_node_spec_coverage(str(tmp_path))

    assert "node-specs: workflow node 'missing-spec' has no matching node-spec file" in errors
    assert "node-specs/orphan.md: no matching workflow node" in errors


def _write_mobile_profile(tmp_path, framework, language="Kotlin", test_commands=None):
    profile = {
        "tech_stacks": [
            {
                "role": "mobile",
                "language": language,
                "framework": framework,
            }
        ],
        "modules": [
            {
                "id": "M001",
                "path": "app/",
                "role": "mobile",
                "description": "UI layer",
            }
        ],
        "test_commands": test_commands or {},
    }
    (tmp_path / "bootstrap-profile.json").write_text(json.dumps(profile))
    (tmp_path / "node-specs").mkdir()


def _write_android_profile(tmp_path):
    _write_mobile_profile(
        tmp_path,
        "Android native + Jetpack Compose",
        test_commands={"instrumentation": "./gradlew connectedAndroidTest"},
    )


def test_android_ui_module_requires_automation_node(tmp_path):
    _write_android_profile(tmp_path)
    _write_workflow(
        tmp_path,
        [
            _base_node(node_id="compile-verify", capability="compile-verify"),
            _base_node(
                node_id="test-verify",
                goal="Run unit tests and document manual test scenarios.",
                capability="test-verify",
            ),
        ],
    )
    (tmp_path / "node-specs" / "test-verify.md").write_text(
        "---\nnode: test-verify\n---\nManual test scenarios require device.\n"
    )

    errors = validate_mobile_ui_coverage(str(tmp_path))

    assert any("Android mobile UI module detected" in e for e in errors)


def test_android_ui_automation_node_passes(tmp_path):
    _write_android_profile(tmp_path)
    _write_workflow(
        tmp_path,
        [
            _base_node(node_id="compile-verify", capability="compile-verify"),
            _base_node(
                node_id="android-ui-verify",
                goal=(
                    "Run ./gradlew connectedAndroidTest and collect "
                    "android-ui-test-report plus android-logcat."
                ),
                capability="test-verify",
                exit_artifacts=[
                    ".allforai/verify/android-ui-test-report.json",
                    ".allforai/verify/android-logcat.txt",
                ],
            ),
        ],
    )
    (tmp_path / "node-specs" / "android-ui-verify.md").write_text(
        "---\nnode: android-ui-verify\n---\n"
        "Run ./gradlew connectedAndroidTest. If adb devices has no target, "
        "return BLOCKED_ENV.\n"
    )

    errors = validate_mobile_ui_coverage(str(tmp_path))

    assert errors == []


def test_ios_ui_module_requires_automation_node(tmp_path):
    _write_mobile_profile(
        tmp_path,
        "iOS native + SwiftUI",
        language="Swift",
        test_commands={"ui": "xcodebuild test -destination 'platform=iOS Simulator'"},
    )
    _write_workflow(tmp_path, [_base_node(node_id="test-verify", goal="Unit tests only")])
    (tmp_path / "node-specs" / "test-verify.md").write_text(
        "---\nnode: test-verify\n---\nManual test scenarios require device.\n"
    )

    errors = validate_mobile_ui_coverage(str(tmp_path))

    assert any("iOS mobile UI module detected" in e for e in errors)


def test_ios_ui_automation_node_passes(tmp_path):
    _write_mobile_profile(tmp_path, "iOS native + SwiftUI", language="Swift")
    _write_workflow(
        tmp_path,
        [
            _base_node(
                node_id="ios-ui-verify",
                goal="Run xcodebuild test and collect ios-ui-test-report plus xcresult.",
                exit_artifacts=[
                    ".allforai/verify/ios-ui-test-report.json",
                    ".allforai/verify/result.xcresult",
                ],
            )
        ],
    )
    (tmp_path / "node-specs" / "ios-ui-verify.md").write_text(
        "---\nnode: ios-ui-verify\n---\nRun xcodebuild test. Return BLOCKED_ENV if no simulator is available.\n"
    )

    errors = validate_mobile_ui_coverage(str(tmp_path))

    assert errors == []


def test_flutter_ui_automation_node_passes(tmp_path):
    _write_mobile_profile(tmp_path, "Flutter mobile", language="Dart")
    _write_workflow(
        tmp_path,
        [
            _base_node(
                node_id="flutter-ui-verify",
                goal="Run flutter test integration_test/ and collect flutter-ui-test-report.",
                exit_artifacts=[".allforai/verify/flutter-ui-test-report.json"],
            )
        ],
    )
    (tmp_path / "node-specs" / "flutter-ui-verify.md").write_text(
        "---\nnode: flutter-ui-verify\n---\nflutter test integration_test/ or BLOCKED_ENV.\n"
    )

    errors = validate_mobile_ui_coverage(str(tmp_path))

    assert errors == []


def test_react_native_ui_automation_node_passes(tmp_path):
    _write_mobile_profile(tmp_path, "React Native bare workflow", language="TypeScript")
    _write_workflow(
        tmp_path,
        [
            _base_node(
                node_id="react-native-ui-verify",
                goal="Run Detox E2E and collect react-native-ui-test-report.",
                exit_artifacts=[".allforai/verify/react-native-ui-test-report.json"],
            )
        ],
    )
    (tmp_path / "node-specs" / "react-native-ui-verify.md").write_text(
        "---\nnode: react-native-ui-verify\n---\nRun detox test. Return BLOCKED_ENV when simulator is unavailable.\n"
    )

    errors = validate_mobile_ui_coverage(str(tmp_path))

    assert errors == []
