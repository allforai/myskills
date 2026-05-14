import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../scripts/orchestrator"))
from validate_game_frontend_pipeline import validate_game_frontend_pipeline


def _write(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def _minimal_repo(tmp_path):
    refs = [
        "10-design/runtime-architecture-design",
        "20-spec/game-state-model-spec",
        "20-spec/scene-flow-spec",
        "20-spec/asset-import-binding-spec",
        "20-spec/asset-loading-strategy-spec",
        "20-spec/game-data-binding-spec",
        "20-spec/gameplay-system-binding-spec",
        "20-spec/scene-composition-spec",
        "20-spec/input-camera-binding-spec",
        "20-spec/hud-ui-binding-spec",
        "20-spec/animation-vfx-binding-spec",
        "20-spec/audio-binding-spec",
        "20-spec/save-state-binding-spec",
        "20-spec/performance-budget-spec",
        "20-spec/runtime-debug-bridge-contract",
        "30-generate/playable-client-assembly",
        "40-qa/runtime-architecture-qa",
        "40-qa/runtime-gameplay-visual-acceptance",
    ]
    parent = "\n".join(
        f"${{CLAUDE_PLUGIN_ROOT}}/skills/game-frontend/{ref}/SKILL.md"
        for ref in refs
    )
    _write(
        tmp_path,
        "claude/meta-skill/skills/game-frontend/SKILL.md",
        parent + "\n.allforai/bootstrap/specialized-skills/<specialization_id>-frontend-runtime/SKILL.md",
    )
    for ref in refs:
        if ref == "10-design/runtime-architecture-design":
            continue
        _write(
            tmp_path,
            f"claude/meta-skill/skills/game-frontend/{ref}/SKILL.md",
            "---\nname: x\ndescription: x\n---\n",
        )
    _write(
        tmp_path,
        "claude/meta-skill/skills/game-frontend/10-design/runtime-architecture-design/SKILL.md",
        """.allforai/bootstrap/specialized-skills/<specialization_id>-frontend-runtime/SKILL.md
Specialization gate
Do not encode Cocos/Phaser/Unity/Godot or genre-specific
""",
    )
    _write(
        tmp_path,
        "claude/meta-skill/skills/game-frontend/30-generate/playable-client-assembly/SKILL.md",
        """.allforai/game-frontend/design/runtime-architecture-design.json
.allforai/game-frontend/bindings/game-state-model-spec.json
.allforai/game-frontend/bindings/scene-flow-spec.json
.allforai/game-frontend/bindings/asset-loading-strategy-spec.json
.allforai/game-frontend/bindings/gameplay-system-binding-spec.json
.allforai/game-frontend/bindings/runtime-debug-bridge-contract.json
""",
    )
    _write(
        tmp_path,
        "claude/meta-skill/skills/game-frontend/40-qa/runtime-architecture-qa/SKILL.md",
        """runtime-architecture-design.json
game-state-model-spec.json
scene-flow-spec.json
gameplay-system-binding-spec.json
asset-loading-strategy-spec.json
performance-budget-spec.json
do not substitute static review for runtime evidence
specialization_required=true
""",
    )
    _write(
        tmp_path,
        "claude/meta-skill/skills/game-frontend/40-qa/runtime-gameplay-visual-acceptance/SKILL.md",
        """.allforai/game-frontend/qa/runtime-gameplay-visual-acceptance-plan.json
.allforai/game-frontend/qa/runtime-gameplay-screenshot-manifest.json
.allforai/game-frontend/qa/runtime-gameplay-visual-batches/
.allforai/game-frontend/qa/codex-gameplay-visual-review.json
.allforai/game-frontend/qa/codex-gameplay-visual-review.md
.allforai/game-frontend/qa/runtime-gameplay-visual-repair-loop-report.json
.allforai/game-frontend/qa/runtime-gameplay-visual-acceptance-report.json
Screenshot review is mandatory for visible gameplay acceptance
must not pass from logs, DOM, canvas probes, or state deltas alone
Gameplay Screenshot Plan
before/after pairs
Codex CLI
pull mode
Claude Code must not re-score visual quality
Repair And Revalidation Loop
rerun the same affected gameplay screenshot tasks
production_visual_binding
prototype/placeholder rejection
pure-color blocks
black debug
generic geometric
engine-ready asset manifest
wrong entrypoint
prototype component
missing asset loader mapping
blocked_by_missing_screenshot
blocked_by_missing_codex_cli
blocked_by_missing_visual_model_capability
""",
    )


def test_validate_game_frontend_pipeline_accepts_minimal_graph(tmp_path):
    _minimal_repo(tmp_path)

    assert validate_game_frontend_pipeline(str(tmp_path)) == []


def test_validate_game_frontend_pipeline_rejects_unlisted_child(tmp_path):
    _minimal_repo(tmp_path)
    _write(
        tmp_path,
        "claude/meta-skill/skills/game-frontend/20-spec/new-binding/SKILL.md",
        "---\nname: y\ndescription: y\n---\n",
    )

    errors = validate_game_frontend_pipeline(str(tmp_path))

    assert any("missing canonical child path" in error for error in errors)
