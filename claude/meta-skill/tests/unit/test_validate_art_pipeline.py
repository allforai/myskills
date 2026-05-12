import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../scripts/orchestrator"))
from validate_art_pipeline import validate_art_pipeline


def _write(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def _minimal_repo(tmp_path):
    _write(
        tmp_path,
        "claude/meta-skill/skills/game-art/SKILL.md",
        """${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/art-preview-qa/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/2d-style-consistency-qa/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/atlas-packaging/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/runtime-import-check/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/asset-license-provenance-qa/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/engine-ready-art-output-contract/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/10-design/art-concept-validation/SKILL.md
.allforai/game-design/art-qa-report.html
.allforai/game-design/art/art-concept-validation.html
.allforai/game-design/art/art-concept-validation.json
.allforai/game-design/art/export/engine-ready-art-output-contract.json
.allforai/game-runtime/art/engine-ready-art-manifest.json
.allforai/game-design/art/qa/runtime-import-check-report.json
""",
    )
    _write(
        tmp_path,
        "claude/meta-skill/skills/game-art/10-design/art-concept-validation/SKILL.md",
        "---\nname: art-concept-validation\ndescription: x\n---\n",
    )
    for rel in [
        "art-preview-qa",
        "2d-style-consistency-qa",
        "atlas-packaging",
        "runtime-import-check",
        "asset-license-provenance-qa",
    ]:
        _write(tmp_path, f"claude/meta-skill/skills/game-art/40-qa/{rel}/SKILL.md", "---\nname: x\ndescription: x\n---\n")
    _write(
        tmp_path,
        "claude/meta-skill/skills/game-art/40-qa/engine-ready-art-output-contract/SKILL.md",
        ".allforai/game-runtime/art/engine-ready-art-manifest.json runtime_id asset_id blocked_by_runtime_import",
    )
    _write(
        tmp_path,
        "claude/meta-skill/skills/game-frontend/20-spec/asset-import-binding-spec/SKILL.md",
        ".allforai/game-runtime/art/engine-ready-art-manifest.json blocked_by_import_validation",
    )
    _write(
        tmp_path,
        "claude/meta-skill/knowledge/capabilities/game-design.md",
        """.allforai/game-runtime/art/engine-ready-art-manifest.json
.allforai/game-design/art/art-concept-validation.html
.allforai/game-design/art/art-concept-validation.json
""",
    )
    _write(
        tmp_path,
        "claude/meta-skill/skills/bootstrap.md",
        """**Art Concept Node Injection
${CLAUDE_PLUGIN_ROOT}/skills/game-art/10-design/art-concept-validation/SKILL.md
.allforai/game-design/art-pipeline-config.json
.allforai/game-design/art/art-concept-validation.html
.allforai/game-design/art/art-concept-validation.json
state in ["passed", "passed_with_warnings"]
**Concept Freeze Node Injection
.allforai/game-design/art/art-concept-validation.json
UPSTREAM_DEFECT
**Art-Gen Node Injection
**Art-QA Node Injection
${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/art-preview-qa/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/2d-style-consistency-qa/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/atlas-packaging/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/runtime-import-check/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/asset-license-provenance-qa/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/engine-ready-art-output-contract/SKILL.md
.allforai/game-design/art-qa-report.html
.allforai/game-design/art/export/engine-ready-art-output-contract.json
.allforai/game-runtime/art/engine-ready-art-manifest.json
Do not advance to `art-qa`
**App Design Node Injection
""",
    )


def test_validate_art_pipeline_accepts_minimal_closed_graph(tmp_path):
    _minimal_repo(tmp_path)
    assert validate_art_pipeline(str(tmp_path)) == []


def test_validate_art_pipeline_rejects_unlisted_child(tmp_path):
    _minimal_repo(tmp_path)
    _write(
        tmp_path,
        "claude/meta-skill/skills/game-art/40-qa/new-required-qa/SKILL.md",
        "---\nname: y\ndescription: y\n---\n",
    )
    errors = validate_art_pipeline(str(tmp_path))
    assert any("missing canonical child path" in error for error in errors)


def test_validate_art_pipeline_rejects_missing_engine_ready_consumer(tmp_path):
    _minimal_repo(tmp_path)
    _write(
        tmp_path,
        "claude/meta-skill/skills/game-frontend/20-spec/asset-import-binding-spec/SKILL.md",
        "blocked_by_import_validation",
    )
    errors = validate_art_pipeline(str(tmp_path))
    assert any("does not consume engine-ready manifest" in error for error in errors)
