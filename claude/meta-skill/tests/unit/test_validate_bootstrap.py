import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from ..module_isolation import load

_validate_bootstrap = load("validate_bootstrap")
APP_DESIGN_FINALIZE_REQUIRED_ARTIFACTS = _validate_bootstrap.APP_DESIGN_FINALIZE_REQUIRED_ARTIFACTS
GAME_2D_PRODUCTION_REQUIRED_NODES = _validate_bootstrap.GAME_2D_PRODUCTION_REQUIRED_NODES
RETURN_TO_BOOTSTRAP = _validate_bootstrap.RETURN_TO_BOOTSTRAP
validate_approval_records = _validate_bootstrap.validate_approval_records
validate_app_design_flow = _validate_bootstrap.validate_app_design_flow
validate_canvas2d_game_client_profile_flow = _validate_bootstrap.validate_canvas2d_game_client_profile_flow
validate_game_2d_production_flow = _validate_bootstrap.validate_game_2d_production_flow
validate_mobile_ui_coverage = _validate_bootstrap.validate_mobile_ui_coverage
validate_node_spec_contracts = _validate_bootstrap.validate_node_spec_contracts
validate_node_spec = _validate_bootstrap.validate_node_spec
validate_node_spec_coverage = _validate_bootstrap.validate_node_spec_coverage
validate_workflow = _validate_bootstrap.validate_workflow
validate_experience_design_coverage = _validate_bootstrap.validate_experience_design_coverage
validate_experience_gate_flow = _validate_bootstrap.validate_experience_gate_flow
experience_gate_flow_findings = _validate_bootstrap.experience_gate_flow_findings
APP_EXPERIENCE_CRITIQUE = _validate_bootstrap.APP_EXPERIENCE_CRITIQUE
GAME_CREATIVE_CRITIQUE = _validate_bootstrap.GAME_CREATIVE_CRITIQUE
effect_stage_ownership_findings = _validate_bootstrap.effect_stage_ownership_findings
repair_loop_declaration_findings = _validate_bootstrap.repair_loop_declaration_findings
structural_gate_blockers = _validate_bootstrap.structural_gate_blockers
workflow_shape_findings = _validate_bootstrap.workflow_shape_findings
coverage_gate_loop = _validate_bootstrap.coverage_gate_loop


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
            body += " concept-acceptance acceptance-report coverage gate missing_mappings"
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
            "concept-acceptance acceptance-report coverage gate missing_mappings",
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
            "concept-acceptance acceptance-report coverage gate missing_mappings",
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


# Experience-design coverage is decided on the graph a run is about to execute, and each
# host reaches it through its own script path, so every behaviour below is proven on both.
# `module_isolation.load` caches by realpath and `codex/meta-skill/scripts` resolves into
# the claude tree, so an in-process load would hand both parameters the same module object
# and the host parameter would prove nothing. A subprocess per host imports the file that
# host actually ships, which is the thing a user runs.
HOSTS = ["claude", "codex"]

_COVERAGE_DRIVER = """
import json, sys
sys.path.insert(0, sys.argv[1])
import validate_bootstrap
print(json.dumps(validate_bootstrap.experience_design_coverage_findings(sys.argv[2])))
"""


def _coverage_findings(host, bdir):
    """Typed findings from `host`'s own copy of the validator."""
    scripts = Path(__file__).resolve().parents[4] / host / "meta-skill/scripts/orchestrator"
    result = subprocess.run([sys.executable, "-c", _COVERAGE_DRIVER, str(scripts), str(bdir)],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    findings = json.loads(result.stdout)
    assert all(RETURN_TO_BOOTSTRAP in f["message"] for f in findings), findings
    return findings


def _codes(findings):
    return sorted({finding["code"] for finding in findings})


EXPERIENCE_DESIGN_ARTIFACTS = [
    ".allforai/app-design/concept/job-story-spec.json",
    ".allforai/app-design/spec/user-flow-spec.json",
    ".allforai/app-design/spec/screen-requirements-spec.json",
    ".allforai/app-design/spec/permissions-notifications-settings-spec.json",
]
GAME_DESIGN_DOC_PATHS = [
    ".allforai/game-design/game-design-doc.json",
    ".allforai/game-design/design/game-design-doc.json",
]
CONSUMER_PRIORITY = {"mode": "consumer", "reason": "Shoppers use the app voluntarily"}


def _design_node(artifacts):
    return _base_node(node_id="experience-design", capability="app-design",
                      goal="Design the user flows and the screen requirements",
                      exit_artifacts=list(artifacts))


def _ui_implementation_node(node_id="implement-mobile", **overrides):
    node = _base_node(node_id=node_id, capability="implement",
                      goal="Implement the mobile screen stack",
                      exit_artifacts=[f".allforai/bootstrap/{node_id}-report.json"],
                      hard_blocked_by=["experience-design"])
    node.update(overrides)
    return node


def _experience_project(tmp_path, *, route="new-product", priority=CONSUMER_PRIORITY,
                        nodes=None, not_applicable=None, game=False):
    """The shape this gate reads: a routed profile with a UI module, and one graph."""
    bdir = _bootstrap_dir(tmp_path)
    profile = {"task_goal": "Ship the shopping app", "task_route": route,
               "modules": [{"id": "app", "path": "mobile", "role": "mobile"}]}
    if priority is not None:
        profile["experience_priority"] = priority
    if game:
        profile["is_game_project"] = True
    (bdir / "bootstrap-profile.json").write_text(json.dumps(profile))
    workflow = {
        "nodes": nodes if nodes is not None else [
            _design_node(EXPERIENCE_DESIGN_ARTIFACTS), _ui_implementation_node()],
        "transition_log": [],
    }
    if not_applicable is not None:
        workflow["not_applicable"] = not_applicable
    (bdir / "workflow.json").write_text(json.dumps(workflow))
    return bdir


@pytest.mark.parametrize("host", HOSTS)
def test_experience_coverage_passes_with_design_node_blocking_ui_implementation(tmp_path, host):
    """The intended shape must stay silent, or the gate is a blanket refusal."""
    assert _coverage_findings(host, _experience_project(tmp_path)) == []


@pytest.mark.parametrize("host", HOSTS)
@pytest.mark.parametrize("priority", [None, {"mode": "premium", "reason": "Sounds better"},
                                      {"mode": "consumer", "reason": "  "}],
                         ids=["absent", "illegal-mode", "empty-reason"])
def test_experience_coverage_rejects_missing_experience_priority(tmp_path, host, priority):
    """An unknown mode decides nothing else: the classification is demanded first, alone."""
    bdir = _experience_project(tmp_path, priority=priority,
                               nodes=[_ui_implementation_node(hard_blocked_by=[])],
                               not_applicable={"experience": "Skipped"})

    findings = _coverage_findings(host, bdir)

    assert _codes(findings) == ["missing_experience_priority"], findings


@pytest.mark.parametrize("host", HOSTS)
def test_experience_coverage_rejects_workflow_without_design_node(tmp_path, host):
    """The ink-scent incident: a product route plans screens and designs none of them."""
    bdir = _experience_project(tmp_path, nodes=[_ui_implementation_node(hard_blocked_by=[])])

    findings = _coverage_findings(host, bdir)

    assert _codes(findings) == ["missing_experience_design_node"], findings
    messages = " ".join(finding["message"] for finding in findings)
    assert ".allforai/app-design/spec/user-flow-spec.json" in messages, messages
    assert ".allforai/app-design/spec/screen-requirements-spec.json" in messages, messages


@pytest.mark.parametrize("host", HOSTS)
def test_experience_coverage_rejects_ui_implementation_not_blocked_by_design(tmp_path, host):
    """Reaching the design node through an intermediate node is reaching it."""
    bdir = _experience_project(tmp_path, nodes=[
        _design_node(EXPERIENCE_DESIGN_ARTIFACTS),
        _ui_implementation_node(hard_blocked_by=[]),
        _base_node(node_id="concept-freeze", capability="concept-contract",
                   hard_blocked_by=["experience-design"]),
        _ui_implementation_node("implement-web", goal="Implement the web frontend screens",
                                hard_blocked_by=["concept-freeze"]),
    ])

    findings = _coverage_findings(host, bdir)

    assert _codes(findings) == ["implementation_not_blocked_by_experience_design"], findings
    assert {finding["node_id"] for finding in findings} == {"implement-mobile"}, findings


@pytest.mark.parametrize("host", HOSTS)
def test_experience_coverage_rejects_experience_not_applicable_on_ui_product(tmp_path, host):
    """Every mode but `none` has end users, so none of them may opt out of designing for them."""
    bdir = _experience_project(tmp_path,
                               priority={"mode": "admin", "reason": "Operators run the console"},
                               not_applicable={"experience": "Internal tool, skipping"})

    findings = _coverage_findings(host, bdir)

    assert _codes(findings) == ["experience_not_applicable_on_ui_product"], findings


@pytest.mark.parametrize("host", HOSTS)
def test_experience_coverage_ignores_local_change(tmp_path, host):
    """A local change is not a product route; it never had to classify its users."""
    bdir = _experience_project(tmp_path, route="local-change", priority=None,
                               nodes=[_ui_implementation_node(hard_blocked_by=[])])

    assert _coverage_findings(host, bdir) == []


@pytest.mark.parametrize("host", HOSTS)
def test_experience_coverage_ignores_mode_none(tmp_path, host):
    """`none` is an honest answer: no end-user interface, so nothing here applies."""
    bdir = _experience_project(tmp_path,
                               priority={"mode": "none", "reason": "Headless ingest service"},
                               nodes=[_ui_implementation_node(hard_blocked_by=[])],
                               not_applicable={"experience": "No end-user interface"})

    assert _coverage_findings(host, bdir) == []


@pytest.mark.parametrize("host", HOSTS)
@pytest.mark.parametrize("doc_path", GAME_DESIGN_DOC_PATHS,
                         ids=["canonical", "design-variant"])
def test_experience_coverage_game_accepts_either_design_doc_path(tmp_path, host, doc_path):
    """Both game-design-doc paths are in use in this repo; either one is the design."""
    gameplay = _ui_implementation_node(goal="Implement the gameplay scene and HUD")
    present = _experience_project(tmp_path, game=True,
                                  nodes=[_design_node([doc_path]), gameplay])

    assert _coverage_findings(host, present) == []

    absent = _experience_project(tmp_path / "without", game=True, nodes=[
        _design_node([".allforai/game-design/story-bible.json"]), gameplay])

    assert _codes(_coverage_findings(host, absent)) == ["missing_experience_design_node"]


def test_experience_coverage_is_a_structural_gate_blocker(tmp_path):
    """`/run` re-decides this gate, so the refused graph cannot execute unattended either."""
    _experience_project(tmp_path, nodes=[_ui_implementation_node(hard_blocked_by=[])])

    blockers = structural_gate_blockers(tmp_path)

    assert "missing_experience_design_node" in {b["code"] for b in blockers}, blockers


def _ui_node_ids(tmp_path, nodes, *, specs=None, game=False):
    """Which of `nodes` the one shared heuristic recognises as building a user-facing surface."""
    bdir = _experience_project(tmp_path, nodes=nodes, game=game)
    for node_id, body in (specs or {}).items():
        _write(bdir / "node-specs", f"{node_id}.md", body)
    profile = json.loads((bdir / "bootstrap-profile.json").read_text())
    workflow = json.loads((bdir / "workflow.json").read_text())
    found = _validate_bootstrap._ui_implementation_nodes(
        workflow, str(bdir / "node-specs"), profile)
    return sorted(node["node_id"] for node in found)


@pytest.mark.parametrize("mention", ["screenshot QA", "Screenshots of the report",
                                     "attach the ScreenshotManifest"],
                         ids=["screenshot", "screenshots", "camel-case-screenshot"])
def test_ui_detection_does_not_read_screen_inside_a_longer_word(tmp_path, mention):
    """A headless node that checks pictures builds no interface: "screenshot" is not "screen"."""
    headless = _base_node(node_id="verify-api-headless", capability="verify",
                          responsibilities=["implementation", "verification"],
                          goal="Build the headless API smoke harness",
                          exit_artifacts=[".allforai/bootstrap/verify-api-headless-report.json"])

    assert _ui_node_ids(tmp_path, [headless], specs={
        "verify-api-headless": f"Run the API smoke suite, then {mention}.\n"}) == []


@pytest.mark.parametrize("host", HOSTS)
def test_experience_coverage_ignores_headless_node_that_only_mentions_screenshots(tmp_path, host):
    """The same word through the gate: no interface is planned, so no design is demanded."""
    headless = _base_node(node_id="implement-api", capability="implement",
                          goal="Implement the orders API and attach screenshot QA evidence",
                          exit_artifacts=[".allforai/bootstrap/implement-api-report.json"])

    assert _coverage_findings(host, _experience_project(tmp_path, nodes=[headless])) == []


@pytest.mark.parametrize("goal", [
    "implement the settings screen", "Implement the Settings Screen.", "Build both screens",
    "Build src/screens/SettingsScreen.tsx", "Build the home_screen widget",
    "Build the web frontend", "Build the front-end shell", "Build the user interface",
    "Build the React Native shell", "Build the react-native shell", "Build the SwiftUI views",
    "Build the homescreen", "Build the touchscreen kiosk flow", "Build the lockscreen",
    "Build the fullscreen player", "实现设置界面", "实现设置页面"])
def test_ui_detection_keeps_every_genuine_surface(tmp_path, goal):
    """The safe direction: whole words, plurals, identifiers and CJK terms all still count."""
    node = _base_node(node_id="implement-client", capability="implement", goal=goal,
                      exit_artifacts=[".allforai/bootstrap/implement-client-report.json"])

    assert _ui_node_ids(tmp_path, [node]) == ["implement-client"]


def test_ui_detection_reads_the_node_spec_body(tmp_path):
    """The spec body names the surface as often as the goal does."""
    node = _base_node(node_id="implement-client", capability="implement", goal="Build the client",
                      exit_artifacts=[".allforai/bootstrap/implement-client-report.json"])

    assert _ui_node_ids(tmp_path, [node], specs={
        "implement-client": "Implement the settings screen.\n"}) == ["implement-client"]


def test_ui_detection_keeps_game_terms_and_profile_module_paths(tmp_path):
    """A game's own words for a screen, and the project's own UI directory, still count."""
    hud = _base_node(node_id="implement-hud", capability="implement", goal="Build the HUDs",
                     exit_artifacts=[".allforai/bootstrap/implement-hud-report.json"])
    path = _base_node(node_id="implement-app", capability="implement",
                      goal="Write mobile/App.tsx",
                      exit_artifacts=[".allforai/bootstrap/implement-app-report.json"])

    assert _ui_node_ids(tmp_path, [hud, path], game=True) == ["implement-app", "implement-hud"]


# `main()` runs the cross-node rules only behind a clean scope contract, and both experience
# gates fire only on a product route, whose scope contract wants a frozen baseline, a journal
# and a confirmed plan. The driver answers the scope question and nothing else, so what is
# left is `main()` itself: its argv, its registrations, its printed report, its exit status.
# The unstubbed path is test_consumer_product_regression.py, which replays a whole session.
_MAIN_DRIVER = """
import sys
sys.path.insert(0, sys.argv[1])
import validate_bootstrap
validate_bootstrap.validate_scope = lambda *args, **kwargs: []
sys.argv = ["validate_bootstrap.py", sys.argv[2]]
validate_bootstrap.main()
"""


def _main_report(host, bdir):
    """Exit status and printed report of `host`'s validator run as a process."""
    scripts = Path(__file__).resolve().parents[4] / host / "meta-skill/scripts/orchestrator"
    result = subprocess.run([sys.executable, "-c", _MAIN_DRIVER, str(scripts), str(bdir)],
                            capture_output=True, text=True)
    assert not result.stderr, result.stderr
    return result.returncode, json.loads(result.stdout)


@pytest.mark.parametrize("host", HOSTS)
@pytest.mark.parametrize("code", ["missing_experience_design_node", "missing_experience_gate"])
def test_main_registers_both_experience_gates(tmp_path, host, code):
    """The functions deciding is not the script deciding: `main()` must call each one."""
    bdir = _experience_project(tmp_path, nodes=[_ui_implementation_node(hard_blocked_by=[])])
    _write(bdir / "node-specs", "implement-mobile.md", "Implement the mobile screen stack\n")

    returncode, report = _main_report(host, bdir)

    assert returncode == 1, report
    assert report["passed"] is False, report
    assert [error for error in report["errors"] if error.startswith(f"{code}: ")], report


@pytest.mark.parametrize("host", HOSTS)
def test_main_reports_no_experience_code_without_end_users(tmp_path, host):
    """The control: the same graph on a product nobody looks at reaches the same rules, silent."""
    bdir = _experience_project(tmp_path, priority={"mode": "none", "reason": "A batch job"},
                               nodes=[_ui_implementation_node(hard_blocked_by=[])])
    _write(bdir / "node-specs", "implement-mobile.md", "Implement the mobile screen stack\n")

    _, report = _main_report(host, bdir)

    reported = {error.split(":")[0] for error in report["errors"]}
    # `unconfirmed_plan` is a cross-node rule too: seeing it proves `main()` got that far.
    assert "unconfirmed_plan" in reported, report
    assert reported.isdisjoint({"missing_experience_design_node", "missing_experience_gate"}), report


def test_app_design_flow_fixtures_raise_no_experience_findings(tmp_path):
    """The app-design fixtures above write no profile at all; the gate stays out of their way."""
    for index, finalize_artifacts in enumerate((
            [".allforai/app-design/app-design-doc.json"],
            sorted(APP_DESIGN_FINALIZE_REQUIRED_ARTIFACTS))):
        bdir = _bootstrap_dir(tmp_path / f"fixture-{index}")
        (bdir / "workflow.json").write_text(json.dumps({"nodes": [
            _base_node(node_id="ia-design", capability="app-design", human_gate=True),
            _base_node(node_id="user-flow-design", capability="app-design", human_gate=True),
            _base_node(node_id="interaction-design", capability="app-design", human_gate=True),
            _base_node(node_id="app-design-finalize", capability="app-design", human_gate=True,
                       hard_blocked_by=["ia-design"], exit_artifacts=finalize_artifacts),
            _base_node(node_id="implement-web", hard_blocked_by=["app-design-finalize"]),
        ], "transition_log": []}))

        assert validate_experience_design_coverage(str(bdir)) == []


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


# Shape before semantics. A node identifier keys every map these gates build, orders the
# report they emit and names the blocker they raise. The gates below are reached by a
# run-time entry on whatever `workflow.json` currently holds, so an identifier that cannot
# do those three things has to be refused as a verdict, never raised as a traceback: a
# caller handed an exception publishes nothing, and its previous verdict stays on disk.
MALFORMED_IDS = [1, 0, 3.5, True, None, ["a"], {"a": 1}, "", "   "]


@pytest.mark.parametrize("node_id", MALFORMED_IDS)
def test_a_node_identifier_that_cannot_key_the_graph_is_rejected_by_shape(tmp_path, node_id):
    path = _write_workflow(tmp_path, [_base_node(node_id=node_id)])

    errors = validate_workflow(path)

    assert any("node_id" in error for error in errors), errors


@pytest.mark.parametrize("node_id", MALFORMED_IDS)
def test_the_structural_gates_report_a_malformed_identifier_instead_of_raising(tmp_path, node_id):
    """`/run` reaches these on the user's current graph; a traceback is not a verdict."""
    _write(tmp_path, ".allforai/bootstrap/workflow.json",
           json.dumps({"nodes": [_base_node(node_id=node_id),
                                 _base_node(node_id="paired", downstream_effect_owner="absent")]}))

    blockers = structural_gate_blockers(tmp_path)

    assert [b["code"] for b in blockers] == ["malformed_workflow_node"], blockers
    # The ownership rule is not answered from the addressable remainder: the graph the
    # user has is not the graph that subset describes.
    assert not any(b["code"] == "unowned_effect_stage" for b in blockers), blockers


def test_two_nodes_sharing_one_identifier_are_a_shape_fault(tmp_path):
    """One entry replaces the other in every map, so the validated graph is not the graph."""
    _write(tmp_path, ".allforai/bootstrap/workflow.json",
           json.dumps({"nodes": [_base_node(node_id="twin"), _base_node(node_id="twin")]}))

    blockers = structural_gate_blockers(tmp_path)

    assert [b["code"] for b in blockers] == ["malformed_workflow_node"], blockers
    assert blockers[0]["node_id"] == "twin", blockers


@pytest.mark.parametrize("nodes", [
    None, "bad", 42, {}, {"a": 1}, [None], ["bad"], [[]], [False], [{}],
    [{"node_id": 1}, {"node_id": "b"}], [{"node_id": ["a"]}], [{"node_id": {"a": 1}}],
    [{"node_id": "a", "hard_blocked_by": ["b"]}, {"node_id": 2}],
], ids=["null", "string", "number", "empty-object", "object", "null-entry", "string-entry",
        "array-entry", "boolean-entry", "no-id", "mixed-int-string", "array-id", "object-id",
        "one-valid-one-malformed"])
def test_no_graph_rule_raises_on_a_malformed_node_collection(tmp_path, nodes):
    """Each gate is called directly, so a caller cannot be shielded by an earlier one."""
    _write(tmp_path, ".allforai/bootstrap/workflow.json", json.dumps({"nodes": nodes}))
    _write(tmp_path, ".allforai/bootstrap/unattended-run-readiness-spec.json", json.dumps(
        {"required_repair_loops": [{"repair_node_id": "repair", "qa_node_ids": ["qa"],
                                    "closure_node_ids": ["closure"], "max_attempts": 2}]}))
    bdir = str(tmp_path / ".allforai/bootstrap")

    for findings in (workflow_shape_findings(bdir), repair_loop_declaration_findings(bdir),
                     effect_stage_ownership_findings(bdir), structural_gate_blockers(tmp_path)):
        assert isinstance(findings, list)
        assert all(isinstance(f, dict) and "code" in f and "message" in f for f in findings), findings


@pytest.mark.parametrize("workflow", [b"{not json", b'{"nodes": [{"node_id": "\xff\xfe"}]}'],
                         ids=["unparseable", "undecodable"])
def test_a_workflow_that_cannot_be_read_yields_no_structural_verdict(tmp_path, workflow):
    """Unreadable bytes are the file gates' finding; a graph rule invents nothing from them."""
    path = tmp_path / ".allforai/bootstrap/workflow.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(workflow)

    assert structural_gate_blockers(tmp_path) == []
    assert validate_workflow(str(path))


def test_a_reference_to_a_malformed_identifier_is_reported_not_hashed(tmp_path):
    path = _write_workflow(tmp_path, [_base_node(hard_blocked_by=[["upstream"]], unlocks=[7])])

    errors = validate_workflow(path)

    assert any("hard_blocked_by entry must be a non-empty node id" in e for e in errors), errors
    assert any("unlocks entry must be a non-empty node id" in e for e in errors), errors


def test_a_well_formed_graph_still_reaches_the_structural_rules(tmp_path):
    """The shape gate must not become a blanket refusal: the routing rule still decides."""
    _write(tmp_path, ".allforai/bootstrap/workflow.json", json.dumps({"nodes": [
        _base_node(node_id="qa"),
        _base_node(node_id="repair", hard_blocked_by=["qa"]),
        _base_node(node_id="closure", hard_blocked_by=["repair"]),
    ]}))
    _write(tmp_path, ".allforai/bootstrap/unattended-run-readiness-spec.json", json.dumps(
        {"required_repair_loops": [{"repair_node_id": "repair", "qa_node_ids": ["qa"],
                                    "closure_node_ids": ["closure"], "max_attempts": 2}]}))

    blockers = structural_gate_blockers(tmp_path)

    assert [b["code"] for b in blockers] == ["undeclared_repair_loop_routing"], blockers
    assert blockers[0]["node_id"] == "closure", blockers


def test_workflow_naming_a_retired_capability_is_refused_by_name(tmp_path):
    """hollowness-detector left /run (ADR-0008). A workflow generated before retirement must
    fail with a reason naming the capability, not run a node that no longer exists."""
    path = _write_workflow(tmp_path, [_base_node(node_id="hollow-audit", capability="hollowness-detector")])

    errors = validate_workflow(path)

    assert any("hollow-audit" in e and "retired capability 'hollowness-detector'" in e for e in errors), errors
    assert any("cross-exam" in e for e in errors), errors


def test_node_spec_naming_a_retired_capability_is_refused_by_name(tmp_path):
    spec = _write(tmp_path, "hollow-audit.md", "---\nnode_id: hollow-audit\ncapability: hollowness-detector\n---\n"
                  + ATTENTION_CONTRACT_BODY)

    errors = validate_node_spec(str(spec))

    assert any("retired capability 'hollowness-detector'" in e for e in errors), errors


def test_coverage_gate_loop_names_the_repair_and_rerun_nodes():
    nodes = [{"node_id": "concept-acceptance", "capability": "concept-acceptance"}]
    loop = coverage_gate_loop(nodes)
    assert loop == {"scope": "concept-acceptance", "qa_node_ids": ["concept-acceptance"],
                    "repair_node_id": "concept-acceptance-repair",
                    "closure_node_ids": ["concept-acceptance-rerun"], "max_attempts": 1}
    assert coverage_gate_loop([{"node_id": "design", "capability": "game-design"}]) is None


@pytest.mark.parametrize('spec_scopes', ['', 'parallel_write_scopes: [other/**]\n'])
def test_parallel_write_scopes_require_matching_node_spec(tmp_path, spec_scopes):
    _write_workflow(tmp_path, [_base_node(node_id='build', parallel_write_scopes=['src/**'])])
    (tmp_path / 'node-specs').mkdir()
    spec = tmp_path / 'node-specs/build.md'
    spec.write_text('---\nnode_id: build\nexit_artifacts: [.allforai/out.json]\n'
                    + spec_scopes + '---\n' + ATTENTION_CONTRACT_BODY)
    assert any('frontmatter parallel_write_scopes' in e for e in validate_node_spec_contracts(str(tmp_path)))
    spec.write_text(spec.read_text().replace(spec_scopes, '', 1) if spec_scopes else spec.read_text())
    spec.write_text(spec.read_text().replace('node_id: build\n', 'node_id: build\nparallel_write_scopes: [src/**]\n'))
    assert not any('frontmatter parallel_write_scopes' in e for e in validate_node_spec_contracts(str(tmp_path)))


# The experience quality gate reads the graph a run is about to execute: two critique
# nodes on an app, at least one on a game, each held in a declared repair loop, the
# interface built after the design critique and closure held behind the runtime one.
# Every fixture below starts from a graph that passes and removes exactly one edge, node
# or loop, so the code asserted is attributable to that one defect. The interface
# implementation node is M1's `_ui_implementation_node`, so both gates agree on what
# building a user-facing surface is.
APP_DESIGN_CRITIQUE_ARTIFACT = ".allforai/app-design/qa/experience-quality-critique-design.json"
APP_RUNTIME_CRITIQUE_ARTIFACT = ".allforai/app-design/qa/experience-quality-critique-runtime.json"
GAME_CRITIQUE_ARTIFACT = ".allforai/game-design/qa/creative-quality-critique.json"


def _critique_node(node_id, artifact, blocked_by, goal="Review the delivered experience"):
    return _base_node(node_id=node_id, capability="quality-checks", goal=goal,
                      exit_artifacts=[artifact], hard_blocked_by=list(blocked_by))


def _repair_node(node_id, blocked_by):
    return _base_node(node_id=node_id, capability="quality-checks",
                      goal="Repair what the review refused",
                      exit_artifacts=[f".allforai/bootstrap/{node_id}-report.json"],
                      hard_blocked_by=list(blocked_by))


def _closure_node(blocked_by, node_id="concept-acceptance"):
    return _base_node(node_id=node_id, capability="concept-acceptance",
                      goal="Accept the concept against its evidence",
                      exit_artifacts=[f".allforai/bootstrap/{node_id}.json"],
                      hard_blocked_by=list(blocked_by))


def _loop(repair_node_id, qa_node_ids, closure_node_ids):
    return {"scope": repair_node_id, "qa_node_ids": list(qa_node_ids),
            "repair_node_id": repair_node_id, "closure_node_ids": list(closure_node_ids),
            "max_attempts": 2}


def _app_gate_nodes():
    """The Must #9 shape on an app: design critique before the build, runtime after it."""
    return [
        _design_node(EXPERIENCE_DESIGN_ARTIFACTS),
        _critique_node("experience-design-critique", APP_DESIGN_CRITIQUE_ARTIFACT,
                       ["experience-design"]),
        _repair_node("experience-design-repair", ["experience-design-critique"]),
        _ui_implementation_node(hard_blocked_by=["experience-design-critique",
                                                 "experience-design-repair"]),
        _critique_node("experience-runtime-critique", APP_RUNTIME_CRITIQUE_ARTIFACT,
                       ["implement-mobile"]),
        _repair_node("experience-runtime-repair", ["experience-runtime-critique"]),
        _closure_node(["experience-runtime-critique", "experience-runtime-repair"]),
    ]


def _app_gate_loops():
    return [_loop("experience-design-repair", ["experience-design-critique"],
                  ["implement-mobile"]),
            _loop("experience-runtime-repair", ["experience-runtime-critique"],
                  ["concept-acceptance"])]


def _game_gate_nodes():
    """A game's creative critique runs twice against one artifact path; position tells them apart."""
    return [
        _design_node([GAME_DESIGN_DOC_PATHS[0]]),
        _critique_node("creative-critique-design", GAME_CRITIQUE_ARTIFACT, ["experience-design"]),
        _repair_node("creative-design-repair", ["creative-critique-design"]),
        _ui_implementation_node("implement-gameplay", goal="Implement the gameplay scene and HUD",
                                hard_blocked_by=["creative-critique-design",
                                                 "creative-design-repair"]),
        _critique_node("creative-critique-runtime", GAME_CRITIQUE_ARTIFACT,
                       ["implement-gameplay"]),
        _repair_node("creative-runtime-repair", ["creative-critique-runtime"]),
        _closure_node(["creative-critique-runtime", "creative-runtime-repair"]),
    ]


def _game_gate_loops():
    return [_loop("creative-design-repair", ["creative-critique-design"], ["implement-gameplay"]),
            _loop("creative-runtime-repair", ["creative-critique-runtime"], ["concept-acceptance"])]


def _experience_gate_project(tmp_path, *, game=False, mode="consumer", route="new-product",
                             nodes=None, loops=None, specs=None, spec_missing=False):
    """A routed product whose graph carries the Must #9 gate, passing unless one part is removed."""
    bdir = _bootstrap_dir(tmp_path)
    profile = {"task_goal": "Ship the shopping app", "task_route": route,
               "modules": [{"id": "app", "path": "mobile", "role": "mobile"}]}
    if mode is not None:
        profile["experience_priority"] = {"mode": mode, "reason": "fixture"}
    if game:
        profile["is_game_project"] = True
    (bdir / "bootstrap-profile.json").write_text(json.dumps(profile))

    if nodes is None:
        nodes = _game_gate_nodes() if game else _app_gate_nodes()
    (bdir / "workflow.json").write_text(json.dumps({"nodes": nodes, "transition_log": []}))

    for node in nodes:
        if isinstance(node, dict) and isinstance(node.get("node_id"), str):
            body = (specs or {}).get(node["node_id"], node.get("goal", ""))
            _write(bdir / "node-specs", f"{node['node_id']}.md",
                   f"---\nnode_id: {node['node_id']}\n---\n{body}\n")

    if not spec_missing:
        if loops is None:
            loops = _game_gate_loops() if game else _app_gate_loops()
        (bdir / "unattended-run-readiness-spec.json").write_text(
            json.dumps({"required_repair_loops": loops}))
    return bdir


def _gate_codes(bdir):
    findings = experience_gate_flow_findings(str(bdir))
    assert all(isinstance(f, dict) and f["message"] for f in findings), findings
    return sorted(f["code"] for f in findings)


def test_experience_gate_app_passes(tmp_path):
    """The intended shape must stay silent, or the gate refuses every product alike."""
    assert experience_gate_flow_findings(str(_experience_gate_project(tmp_path))) == []


def test_experience_gate_game_passes(tmp_path):
    """A game's two creative reviews are one path twice; the graph position tells them apart."""
    assert experience_gate_flow_findings(str(_experience_gate_project(tmp_path, game=True))) == []


def test_experience_gate_rejects_app_without_critique_node(tmp_path):
    """An app that builds an interface and reviews it at neither stage is missing both gates."""
    nodes = [n for n in _app_gate_nodes() if "critique" not in n["node_id"]]
    bdir = _experience_gate_project(tmp_path, nodes=nodes, loops=[])

    findings = experience_gate_flow_findings(str(bdir))

    assert [f["code"] for f in findings].count("missing_experience_gate") == 2, findings
    messages = " ".join(f["message"] for f in findings)
    assert APP_DESIGN_CRITIQUE_ARTIFACT.rsplit("/", 1)[-1] in messages, messages
    assert APP_RUNTIME_CRITIQUE_ARTIFACT.rsplit("/", 1)[-1] in messages, messages


def test_experience_gate_names_the_missing_stage(tmp_path):
    """One stage missing is one blocker, and it says which stage and which artifact."""
    nodes = [n for n in _app_gate_nodes() if n["node_id"] != "experience-runtime-critique"]
    nodes = [n for n in nodes if n["node_id"] != "experience-runtime-repair"]
    bdir = _experience_gate_project(
        tmp_path, nodes=nodes,
        loops=[_loop("experience-design-repair", ["experience-design-critique"],
                     ["implement-mobile"])])

    missing = [f for f in experience_gate_flow_findings(str(bdir))
               if f["code"] == "missing_experience_gate"]

    assert len(missing) == 1, missing
    assert "runtime" in missing[0]["message"], missing
    assert APP_RUNTIME_CRITIQUE_ARTIFACT.rsplit("/", 1)[-1] in missing[0]["message"], missing


def test_experience_gate_rejects_game_without_creative_critique(tmp_path):
    """A game with no creative review at all is one blocker, not one per stage."""
    nodes = [n for n in _game_gate_nodes() if "critique" not in n["node_id"]]
    bdir = _experience_gate_project(tmp_path, game=True, nodes=nodes, loops=[])

    findings = experience_gate_flow_findings(str(bdir))

    missing = [f for f in findings if f["code"] == "missing_experience_gate"]
    assert len(missing) == 1, findings
    assert GAME_CREATIVE_CRITIQUE in missing[0]["message"], missing


def test_experience_gate_rejects_implementation_not_blocked_by_design_critique(tmp_path):
    """An interface built before its review was reviewed after it was already decided."""
    nodes = []
    for node in _app_gate_nodes():
        if node["node_id"] == "implement-mobile":
            node = _ui_implementation_node(hard_blocked_by=["experience-design"])
        nodes.append(node)
    bdir = _experience_gate_project(tmp_path, nodes=nodes)

    findings = experience_gate_flow_findings(str(bdir))

    assert _gate_codes(bdir) == ["implementation_not_blocked_by_design_critique"], findings
    assert {f["node_id"] for f in findings} == {"implement-mobile"}, findings


def test_experience_gate_rejects_closure_not_blocked_by_runtime_critique(tmp_path):
    """Closure that does not wait for the runtime review can accept an unreviewed product."""
    nodes = []
    for node in _app_gate_nodes():
        if node["node_id"] == "concept-acceptance":
            node = _closure_node(["experience-design-critique"])
        nodes.append(node)
    bdir = _experience_gate_project(tmp_path, nodes=nodes)

    findings = experience_gate_flow_findings(str(bdir))

    assert _gate_codes(bdir) == ["closure_not_blocked_by_experience_gate"], findings
    assert {f["node_id"] for f in findings} == {"concept-acceptance"}, findings


def test_experience_gate_rejects_game_closure_not_blocked_by_post_implementation_critique(tmp_path):
    """A game reviewed only before it was built has no review of the thing it shipped."""
    nodes = [n for n in _game_gate_nodes()
             if n["node_id"] not in ("creative-critique-runtime", "creative-runtime-repair")]
    nodes = [_closure_node(["creative-critique-design"]) if n["node_id"] == "concept-acceptance"
             else n for n in nodes]
    bdir = _experience_gate_project(
        tmp_path, game=True, nodes=nodes,
        loops=[_loop("creative-design-repair", ["creative-critique-design"],
                     ["implement-gameplay"])])

    findings = experience_gate_flow_findings(str(bdir))

    assert _gate_codes(bdir) == ["closure_not_blocked_by_experience_gate"], findings
    assert {f["node_id"] for f in findings} == {"concept-acceptance"}, findings


def test_experience_gate_rejects_critique_outside_repair_loop(tmp_path):
    """A review nobody declared a loop for stops the run instead of routing its findings."""
    bdir = _experience_gate_project(
        tmp_path, loops=[_loop("experience-design-repair", ["experience-design-critique"],
                               ["implement-mobile"])])

    findings = experience_gate_flow_findings(str(bdir))

    assert _gate_codes(bdir) == ["experience_gate_without_repair_loop"], findings
    assert {f["node_id"] for f in findings} == {"experience-runtime-critique"}, findings


def test_experience_gate_without_readiness_spec_is_an_undeclared_loop(tmp_path):
    """No readiness spec declares no loop, so both reviews route nothing."""
    bdir = _experience_gate_project(tmp_path, spec_missing=True)

    findings = experience_gate_flow_findings(str(bdir))

    assert _gate_codes(bdir) == ["experience_gate_without_repair_loop"] * 2, findings
    assert {f["node_id"] for f in findings} == {"experience-design-critique",
                                                "experience-runtime-critique"}, findings


def test_experience_gate_not_triggered_when_mode_none(tmp_path):
    """`none` means no end users; there is no experience to review."""
    nodes = [n for n in _app_gate_nodes() if "critique" not in n["node_id"]]
    assert experience_gate_flow_findings(
        str(_experience_gate_project(tmp_path, mode="none", nodes=nodes, loops=[]))) == []


def test_experience_gate_not_triggered_on_local_change(tmp_path):
    """A local change is not a product route; it never planned an experience."""
    nodes = [n for n in _app_gate_nodes() if "critique" not in n["node_id"]]
    assert experience_gate_flow_findings(
        str(_experience_gate_project(tmp_path, route="local-change", nodes=nodes,
                                     loops=[]))) == []


def test_experience_gate_not_triggered_without_experience_priority(tmp_path):
    """A project planned before the classification existed is not retro-blocked here."""
    nodes = [n for n in _app_gate_nodes() if "critique" not in n["node_id"]]
    assert experience_gate_flow_findings(
        str(_experience_gate_project(tmp_path, mode=None, nodes=nodes, loops=[]))) == []


def test_experience_gate_reader_node_is_not_a_gate(tmp_path):
    """Reading the review is not performing it: only the node that writes the report is the gate."""
    reader = _base_node(node_id="release-notes", capability="quality-checks",
                        goal="Summarise what the review found",
                        exit_artifacts=[".allforai/bootstrap/release-notes.json"],
                        hard_blocked_by=["implement-mobile"])
    nodes = [n for n in _app_gate_nodes()
             if n["node_id"] not in ("experience-runtime-critique", "experience-runtime-repair")]
    nodes.append(reader)
    bdir = _experience_gate_project(
        tmp_path, nodes=nodes,
        specs={"release-notes": f"Read {APP_RUNTIME_CRITIQUE_ARTIFACT} and "
                                f"the {APP_EXPERIENCE_CRITIQUE} report."},
        loops=[_loop("experience-design-repair", ["experience-design-critique"],
                     ["implement-mobile"])])

    assert "missing_experience_gate" in _gate_codes(bdir), _gate_codes(bdir)


def test_structural_gate_blockers_include_experience_gate(tmp_path):
    """`/run` re-decides this gate, so a graph broken after bootstrap cannot execute either."""
    nodes = [n for n in _app_gate_nodes() if "critique" not in n["node_id"]]
    _experience_gate_project(tmp_path, nodes=nodes, loops=[])

    blockers = structural_gate_blockers(tmp_path)

    assert "missing_experience_gate" in {b["code"] for b in blockers}, blockers


@pytest.mark.parametrize("workflow", ["{not json", '{"nodes": "everything"}', '"a string"'],
                         ids=["unparseable", "nodes-not-a-list", "root-not-an-object"])
def test_experience_gate_malformed_inputs_return_empty(tmp_path, workflow):
    """Shape faults belong to the shape gate; this rule never raises and never guesses."""
    bdir = _experience_gate_project(tmp_path)
    (bdir / "workflow.json").write_text(workflow)

    assert experience_gate_flow_findings(str(bdir)) == []

    (bdir / "bootstrap-profile.json").write_text("{not json")
    assert experience_gate_flow_findings(str(bdir)) == []
    assert validate_experience_gate_flow(str(bdir)) == []
