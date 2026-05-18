import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../scripts/orchestrator"))
from validate_bootstrap import (
    GAME_2D_PRODUCTION_REQUIRED_NODES,
    validate_approval_records,
    validate_app_design_flow,
    validate_canvas2d_game_client_profile_flow,
    validate_game_2d_production_flow,
    validate_mobile_ui_coverage,
    validate_node_spec_contracts,
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


def _write(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


ATTENTION_CONTRACT_BODY = """
## Attention Contract
- Primary outcome: produce the tested node outcome.
- Non-goals / out-of-scope: do not perform unrelated work.
- Must-read inputs: workflow fields required by the node.
- Optional inputs: none.
- Context budget: read only the relevant fixtures.
- Quality questions: does the node meet the fixture contract?
- Stop conditions: stop when required inputs are missing.
- Repair targets: code_gaps, quality_gaps.
"""


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


def _write_node_spec(root, node_id, body="Canvas2D gameplay effect verification runtime evidence"):
    _write(
        root,
        f"node-specs/{node_id}.md",
        f"---\nnode_id: {node_id}\n---\n{ATTENTION_CONTRACT_BODY}\n{body}\n",
    )


def test_canvas2d_game_client_underexpanded_workflow_fails(tmp_path):
    nodes = [
        _base_node(node_id="canvas2d-client-scaffold", capability="game-frontend", exit_artifacts=[".allforai/canvas/scaffold.json"]),
        _base_node(node_id="canvas2d-browser-qa", capability="game-frontend", exit_artifacts=[".allforai/canvas/browser-qa.json"]),
        _base_node(node_id="canvas2d-mobile-build", capability="game-frontend", exit_artifacts=[".allforai/canvas/mobile-build.json"]),
        _base_node(node_id="canvas2d-android-sim-test", capability="game-frontend", exit_artifacts=[".allforai/canvas/android.json"]),
    ]
    _write(tmp_path, "workflow.json", json.dumps({"nodes": nodes}))
    _write(tmp_path, "bootstrap-profile.json", json.dumps({"project_type": "game", "runtime": "Canvas2D"}))
    _write(tmp_path, "canvas2d-game-client-profile.json", "{}")
    for node in nodes:
        _write_node_spec(tmp_path, node["node_id"])

    errors = validate_canvas2d_game_client_profile_flow(str(tmp_path))

    assert any("under-expanded" in e for e in errors)
    assert any("missing required profile families" in e for e in errors)
    assert any("QA matrix" in e for e in errors)


def test_canvas2d_game_client_mature_profile_passes(tmp_path):
    node_ids = [
        "canvas2d-runtime-core",
        "canvas2d-interface-cards",
        "canvas2d-asset-bundle",
        "canvas2d-gameplay-scene",
        "canvas2d-gameplay-system-matcher",
        "canvas2d-browser-qa",
        "canvas2d-visual-qa",
        "canvas2d-gameplay-quality-qa",
        "canvas2d-performance-qa",
        "canvas2d-art-quality-qa",
        "canvas2d-audio-registry",
        "canvas2d-audio-style",
        "canvas2d-sfx-spec",
        "canvas2d-audio-generation",
        "canvas2d-audio-system",
        "canvas2d-audio-qa",
        "canvas2d-runtime-audio-import",
        "canvas2d-qa-repair-loop",
        "canvas2d-concept-acceptance",
    ]
    nodes = []
    for node_id in node_ids:
        blockers = []
        if node_id == "canvas2d-concept-acceptance":
            blockers = ["canvas2d-qa-repair-loop"]
        nodes.append(
            _base_node(
                node_id=node_id,
                capability="game-frontend",
                hard_blocked_by=blockers,
                exit_artifacts=[f".allforai/canvas/{node_id}.json"],
            )
        )
        body = (
            "Canvas2D gameplay scene effect verification runtime evidence screenshot "
            "module_wiring_proofs production consumer visual acceptance runtime probe "
            "asset manifest preload fps memory performance budget legal action"
        )
        if "interface-cards" in node_id:
            body = "interface cards public module signatures preserved_exports"
        if "asset-bundle" in node_id:
            body += " decoded resource"
        if "browser-qa" in node_id:
            body += " Playwright browser smoke"
        if "visual-qa" in node_id:
            body += " Codex visual screenshot"
        if "gameplay-quality" in node_id:
            body += " playability solvability legal action rule invariant"
        if "performance" in node_id:
            body += " performance-qa render pressure"
        if "audio-registry" in node_id:
            body += " game-audio audio-registry audio ids audio manifest sfx-manifest bgm-loop-manifest"
        if "audio-style" in node_id:
            body += " game-audio audio-style sonic palette mix direction audio mood"
        if "sfx-spec" in node_id:
            body += " game-audio sfx-spec event sfx sfx source strategy sfx-source-strategy"
        if "audio-generation" in node_id:
            body += " game-audio sfx-procedural-generation sfx-source-adaptation bgm-loop-generation google lyria real audio files"
        if "audio-system" in node_id:
            body += " game-audio audio-system AudioManager Web Audio loadBGM loadSFX decoded buffer production consumer"
        if "audio-qa" in node_id:
            body += " game-audio audio-qa audio-loudness-qa AudioBuffer AudioContext.state decoded buffer"
        if "runtime-audio-import" in node_id:
            body += " game-audio runtime-audio-import engine-ready-audio-manifest runtime audio import actual playback playback validation"
        if "repair-loop" in node_id:
            body += " qa-repair-loop repair and revalidation revalidation-report"
        if "concept-acceptance" in node_id:
            body += " concept-acceptance acceptance-report final weighted product acceptance"
        _write_node_spec(tmp_path, node_id, body)

    _write(tmp_path, "workflow.json", json.dumps({"nodes": nodes}))
    _write(tmp_path, "bootstrap-profile.json", json.dumps({"project_type": "game", "runtime": "Canvas2D"}))
    _write(tmp_path, "canvas2d-game-client-profile.json", json.dumps({"runtime": "Canvas2D game-client profile"}))

    assert validate_canvas2d_game_client_profile_flow(str(tmp_path)) == []


def test_canvas2d_game_client_requires_audio_closure_by_default(tmp_path):
    node_ids = [
        "canvas2d-runtime-core",
        "canvas2d-interface-cards",
        "canvas2d-asset-bundle",
        "canvas2d-gameplay-scene",
        "canvas2d-gameplay-system-matcher",
        "canvas2d-browser-qa",
        "canvas2d-visual-qa",
        "canvas2d-gameplay-quality-qa",
        "canvas2d-performance-qa",
        "canvas2d-art-quality-qa",
        "canvas2d-qa-repair-loop",
        "canvas2d-concept-acceptance",
    ]
    nodes = []
    for node_id in node_ids:
        blockers = ["canvas2d-qa-repair-loop"] if node_id == "canvas2d-concept-acceptance" else []
        nodes.append(
            _base_node(
                node_id=node_id,
                capability="game-frontend",
                hard_blocked_by=blockers,
                exit_artifacts=[f".allforai/canvas/{node_id}.json"],
            )
        )
        _write_node_spec(
            tmp_path,
            node_id,
            "Canvas2D gameplay scene effect verification runtime evidence screenshot "
            "module_wiring_proofs production consumer visual acceptance runtime probe "
            "asset manifest preload fps memory performance budget legal action "
            "interface cards public module signatures preserved_exports qa-repair-loop "
            "concept-acceptance acceptance-report final weighted product acceptance",
        )

    _write(tmp_path, "workflow.json", json.dumps({"nodes": nodes}))
    _write(tmp_path, "bootstrap-profile.json", json.dumps({"project_type": "game", "runtime": "Canvas2D"}))
    _write(tmp_path, "canvas2d-game-client-profile.json", json.dumps({"runtime": "Canvas2D game-client profile"}))

    errors = validate_canvas2d_game_client_profile_flow(str(tmp_path))

    assert any("audio closure" in e or "audio-" in e for e in errors)


def test_canvas2d_game_client_audio_can_be_scope_locked_out(tmp_path):
    node_ids = [
        "canvas2d-runtime-core",
        "canvas2d-interface-cards",
        "canvas2d-asset-bundle",
        "canvas2d-gameplay-scene",
        "canvas2d-gameplay-system-matcher",
        "canvas2d-browser-qa",
        "canvas2d-visual-qa",
        "canvas2d-gameplay-quality-qa",
        "canvas2d-performance-qa",
        "canvas2d-art-quality-qa",
        "canvas2d-qa-repair-loop",
        "canvas2d-concept-acceptance",
    ]
    nodes = []
    for node_id in node_ids:
        blockers = ["canvas2d-qa-repair-loop"] if node_id == "canvas2d-concept-acceptance" else []
        nodes.append(
            _base_node(
                node_id=node_id,
                capability="game-frontend",
                hard_blocked_by=blockers,
                exit_artifacts=[f".allforai/canvas/{node_id}.json"],
            )
        )
        _write_node_spec(
            tmp_path,
            node_id,
            "Canvas2D gameplay scene effect verification runtime evidence screenshot "
            "module_wiring_proofs production consumer visual acceptance runtime probe "
            "asset manifest preload fps memory performance budget legal action "
            "interface cards public module signatures preserved_exports qa-repair-loop "
            "concept-acceptance acceptance-report final weighted product acceptance",
        )

    _write(tmp_path, "workflow.json", json.dumps({"nodes": nodes}))
    _write(tmp_path, "bootstrap-profile.json", json.dumps({"project_type": "game", "runtime": "Canvas2D"}))
    _write(tmp_path, "canvas2d-game-client-profile.json", json.dumps({"runtime": "Canvas2D game-client profile"}))
    _write(
        tmp_path,
        "scope-lock.json",
        json.dumps(
            {
                "scope_decision_id": "scope-audio-cut",
                "excluded_feature_or_asset": "audio / SFX / BGM",
                "approved_before_run": True,
                "product_reason": "silent prototype",
            }
        ),
    )

    assert validate_canvas2d_game_client_profile_flow(str(tmp_path)) == []


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


def test_game_2d_handoff_requires_production_nodes(tmp_path):
    bdir = tmp_path / ".allforai/bootstrap"
    bdir.mkdir(parents=True)
    _write_workflow(
        bdir,
        [
            _base_node(
                node_id="setup-runtime-env",
                capability="game-runtime",
                exit_artifacts=[".allforai/bootstrap/runtime.json"],
            )
        ],
    )
    _write(
        tmp_path,
        ".allforai/game-design/design/program-development-node-handoff.json",
        json.dumps(
            {
                "target_engine": "cocos-creator-3.x",
                "runtime_assumptions": {"platform": "web-canvas-2d"},
                "implementation_nodes": [{"node_id": "implement-puzzle-core"}],
            }
        ),
    )

    errors = validate_game_2d_production_flow(str(bdir))

    assert any("missing required game-2d-production nodes" in error for error in errors)


def test_game_2d_handoff_accepts_ordered_production_nodes(tmp_path):
    bdir = tmp_path / ".allforai/bootstrap"
    specs_dir = bdir / "node-specs"
    specs_dir.mkdir(parents=True)
    nodes = []
    previous = None
    for node_id in GAME_2D_PRODUCTION_REQUIRED_NODES:
        artifacts = [f".allforai/game-2d/{node_id}.json"]
        if node_id == "game-2d-production-closure-qa":
            artifacts = [
                ".allforai/game-2d/assembly/playable-slice-assembly-report.json",
                ".allforai/game-2d/qa/core-loop-playability-qa-report.json",
                ".allforai/game-2d/qa/asset-binding-visual-qa-report.json",
                ".allforai/game-2d/qa/session-completion-qa-report.json",
                ".allforai/game-2d/repair/code-repair-loop-report.json",
                ".allforai/game-2d/qa/revalidation-report.json",
                ".allforai/game-2d/qa/2d-production-closure-report.json",
                ".allforai/game-2d/qa/2d-production-closure.html",
            ]
        nodes.append(
            _base_node(
                node_id=node_id,
                capability="game-2d-production",
                hard_blocked_by=[previous] if previous else [],
                exit_artifacts=artifacts,
            )
        )
        _write(
            bdir,
            f"node-specs/{node_id}.md",
            f"---\nnode_id: {node_id}\n---\n{ATTENTION_CONTRACT_BODY}\nRead game-2d-production/{node_id}/SKILL.md\n",
        )
        previous = node_id
    _write_workflow(bdir, nodes)
    _write(
        tmp_path,
        ".allforai/game-design/design/program-development-node-handoff.json",
        json.dumps({"game_2d_production": {"required": True}, "implementation_nodes": []}),
    )

    errors = validate_game_2d_production_flow(str(bdir))

    assert errors == []


def test_node_spec_contract_detects_frontmatter_mismatch(tmp_path):
    _write_workflow(
        tmp_path,
        [
            _base_node(
                node_id="build",
                exit_artifacts=[".allforai/build.json"],
                hard_blocked_by=["setup"],
                unlocks=["verify"],
            ),
            _base_node(node_id="setup"),
            _base_node(node_id="verify"),
        ],
    )
    (tmp_path / "node-specs").mkdir()
    (tmp_path / "node-specs" / "build.md").write_text(
        "---\n"
        "node_id: wrong-build\n"
        "exit_artifacts:\n"
        "  - .allforai/other.json\n"
        "hard_blocked_by: []\n"
        "unlocks: []\n"
        "---\n"
        f"{ATTENTION_CONTRACT_BODY}\n"
    )

    errors = validate_node_spec_contracts(str(tmp_path))

    assert any("frontmatter node_id 'wrong-build'" in e for e in errors)
    assert any("frontmatter exit_artifacts" in e for e in errors)
    assert any("frontmatter hard_blocked_by" in e for e in errors)
    assert any("frontmatter unlocks" in e for e in errors)


def test_node_spec_contract_passes_when_frontmatter_matches(tmp_path):
    _write_workflow(
        tmp_path,
        [
            _base_node(
                node_id="build",
                exit_artifacts=[".allforai/build.json"],
                hard_blocked_by=["setup"],
                unlocks=["verify"],
            ),
            _base_node(node_id="setup"),
            _base_node(node_id="verify"),
        ],
    )
    (tmp_path / "node-specs").mkdir()
    (tmp_path / "node-specs" / "build.md").write_text(
        "---\n"
        "node_id: build\n"
        "exit_artifacts:\n"
        "  - .allforai/build.json\n"
        "hard_blocked_by:\n"
        "  - setup\n"
        "unlocks:\n"
        "  - verify\n"
        "---\n"
        f"{ATTENTION_CONTRACT_BODY}\n"
    )

    errors = validate_node_spec_contracts(str(tmp_path))

    assert errors == []


def test_node_spec_contract_requires_attention_contract(tmp_path):
    _write_workflow(
        tmp_path,
        [
            _base_node(
                node_id="build",
                exit_artifacts=[".allforai/build.json"],
            ),
        ],
    )
    (tmp_path / "node-specs").mkdir()
    (tmp_path / "node-specs" / "build.md").write_text(
        "---\n"
        "node_id: build\n"
        "exit_artifacts:\n"
        "  - .allforai/build.json\n"
        "---\n"
        "## Effect Verification\n"
    )

    errors = validate_node_spec_contracts(str(tmp_path))

    assert any("missing attention contract term '## Attention Contract'" in e for e in errors)
    assert any("missing attention contract term 'Primary outcome'" in e for e in errors)


def _bootstrap_dir(tmp_path):
    bdir = tmp_path / ".allforai" / "bootstrap"
    (bdir / "node-specs").mkdir(parents=True)
    return bdir


def test_approval_records_detect_missing_and_mismatched_records(tmp_path):
    bdir = _bootstrap_dir(tmp_path)
    workflow = {
        "nodes": [
            _base_node(
                node_id="design",
                human_gate=True,
                approval_record_path=".allforai/game-design/approval-records.json",
                unlocks=["next"],
            ),
            _base_node(node_id="next"),
        ],
        "transition_log": [],
    }
    (bdir / "workflow.json").write_text(json.dumps(workflow))
    approval_dir = tmp_path / ".allforai" / "game-design"
    approval_dir.mkdir()
    (approval_dir / "approval-records.json").write_text(json.dumps({
        "records": [
            {"node_id": "other", "gate_status": "pending", "unlocks": []},
            {"node": "legacy", "gate_status": "pending", "unlocks": []},
        ]
    }))

    errors = validate_approval_records(str(bdir))

    assert any("missing approval record for node_id 'design'" in e for e in errors)
    assert any("approval record for non-human_gate node_id 'other'" in e for e in errors)
    assert any("uses forbidden legacy field 'node'" in e for e in errors)


def test_approval_records_pass_when_matching(tmp_path):
    bdir = _bootstrap_dir(tmp_path)
    workflow = {
        "nodes": [
            _base_node(
                node_id="design",
                human_gate=True,
                approval_record_path=".allforai/app-design/approval-records.json",
                unlocks=["next"],
            ),
            _base_node(node_id="next"),
        ],
        "transition_log": [],
    }
    (bdir / "workflow.json").write_text(json.dumps(workflow))
    approval_dir = tmp_path / ".allforai" / "app-design"
    approval_dir.mkdir()
    (approval_dir / "approval-records.json").write_text(json.dumps({
        "records": [
            {
                "node_id": "design",
                "gate_status": "pending",
                "unlocks": ["next"],
                "review_checklist": [],
            }
        ]
    }))

    errors = validate_approval_records(str(bdir))

    assert errors == []


def test_app_design_flow_requires_finalize_handoff_and_concept_freeze(tmp_path):
    bdir = _bootstrap_dir(tmp_path)
    workflow = {
        "nodes": [
            _base_node(node_id="ia-design", capability="app-design", human_gate=True),
            _base_node(node_id="user-flow-design", capability="app-design", human_gate=True),
            _base_node(node_id="interaction-design", capability="app-design", human_gate=True),
            _base_node(
                node_id="app-design-finalize",
                capability="app-design",
                human_gate=True,
                hard_blocked_by=["ia-design"],
                exit_artifacts=[".allforai/app-design/app-design-doc.json"],
            ),
            _base_node(node_id="implement-web", hard_blocked_by=["app-design-finalize"]),
        ],
        "transition_log": [],
    }
    (bdir / "workflow.json").write_text(json.dumps(workflow))

    errors = validate_app_design_flow(str(bdir))

    assert any("app-design-finalize hard_blocked_by missing" in e for e in errors)
    assert any("app-design-finalize missing required handoff/closure" in e for e in errors)
    assert any("missing concept-freeze node" in e for e in errors)
    assert any("depends directly on app-design-finalize" in e for e in errors)


def test_app_design_flow_passes_with_handoff_and_concept_freeze(tmp_path):
    bdir = _bootstrap_dir(tmp_path)
    app_nodes = [
        _base_node(node_id="ia-design", capability="app-design", human_gate=True),
        _base_node(node_id="user-flow-design", capability="app-design", human_gate=True),
        _base_node(node_id="interaction-design", capability="app-design", human_gate=True),
    ]
    workflow = {
        "nodes": [
            *app_nodes,
            _base_node(
                node_id="app-design-finalize",
                capability="app-design",
                human_gate=True,
                hard_blocked_by=["ia-design", "user-flow-design", "interaction-design"],
                exit_artifacts=[
                    ".allforai/app-design/app-design-doc.json",
                    ".allforai/app-design/app-design-doc.html",
                    ".allforai/app-design/handoff/ui-design-input-handoff.json",
                    ".allforai/app-design/handoff/program-development-node-handoff.json",
                    ".allforai/app-design/qa/app-design-closure-qa-report.json",
                ],
            ),
            _base_node(
                node_id="concept-freeze",
                capability="concept-contract",
                hard_blocked_by=["app-design-finalize"],
            ),
            _base_node(node_id="implement-web", hard_blocked_by=["concept-freeze"]),
        ],
        "transition_log": [],
    }
    (bdir / "workflow.json").write_text(json.dumps(workflow))

    errors = validate_app_design_flow(str(bdir))

    assert errors == []


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
