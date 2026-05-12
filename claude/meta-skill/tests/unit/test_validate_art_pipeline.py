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
${CLAUDE_PLUGIN_ROOT}/skills/game-art/00-env/image-model-capability-registry/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/10-design/asset-source-strategy-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/20-spec/asset-pack-search-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/20-spec/character-layer-sheet/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/30-generate/image-generation-contract/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/30-generate/background-generation/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/30-generate/decal-generation/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/30-generate/expression-set-generation/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/30-generate/frame-animation-generation/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/30-generate/icon-generation/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/30-generate/item-art-generation/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/30-generate/particle-system/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/30-generate/portrait-generation/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/30-generate/prop-generation/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/30-generate/skeletal-animation/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/30-generate/sprite-vfx-generation/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/30-generate/tileset-generation/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/30-generate/trail-generation/SKILL.md
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
.allforai/game-design/art/image-generation/accepted-image-manifest.json
raw PNG/JPG/WebP paths
image-model-capability-registry
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
        "claude/meta-skill/skills/game-art/30-generate/image-generation-contract/SKILL.md",
        """.allforai/game-design/art/image-generation/accepted-image-manifest.json
.allforai/game-design/art/image-generation/image-model-capability-registry.json
.allforai/game-design/art/image-generation/image-model-routing-report.json
consumer_ready
image-model-capability-registry
route_model
selected provider/model
missing_capabilities
register_searched_or_existing
web_or_marketplace_search
local_asset_library
Downstream skills must not consume raw PNG paths directly
re-run the downstream consumer validation
""",
    )
    _write(
        tmp_path,
        "claude/meta-skill/skills/game-art/00-env/image-model-capability-registry/SKILL.md",
        """.allforai/game-design/art/image-generation/image-model-capability-registry.json
.allforai/game-design/art/image-generation/image-model-routing-report.json
google_gemini_image
fal_ai
openrouter_image
project_local_mcp
GOOGLE_API_KEY
FAL_KEY
OPENROUTER_API_KEY
output_modalities=image
generation_profile
missing_capabilities
blocked_by_missing_model
selected_model
""",
    )
    _write(
        tmp_path,
        "claude/meta-skill/skills/game-art/10-design/asset-source-strategy-spec/SKILL.md",
        """source_priority_chain
local_asset_library
user_provided_asset
web_or_marketplace_search
llm_image_generation
.allforai/game-design/art/image-generation/accepted-image-manifest.json
consumer_ready: true
""",
    )
    _write(
        tmp_path,
        "claude/meta-skill/skills/game-art/20-spec/asset-pack-search-spec/SKILL.md",
        """source_order
project-local asset folders
user-provided bundles
wider web search
register_searched_or_existing
.allforai/game-design/art/image-generation/accepted-image-manifest.json
consumer_ready: true
""",
    )
    for rel in [
        "20-spec/character-layer-sheet",
        "30-generate/background-generation",
        "30-generate/decal-generation",
        "30-generate/expression-set-generation",
        "30-generate/frame-animation-generation",
        "30-generate/icon-generation",
        "30-generate/item-art-generation",
        "30-generate/particle-system",
        "30-generate/portrait-generation",
        "30-generate/prop-generation",
        "30-generate/skeletal-animation",
        "30-generate/sprite-vfx-generation",
        "30-generate/tileset-generation",
        "30-generate/trail-generation",
    ]:
        _write(
            tmp_path,
            f"claude/meta-skill/skills/game-art/{rel}/SKILL.md",
            "game-art/30-generate/image-generation-contract",
        )
    _write(
        tmp_path,
        "claude/meta-skill/skills/game-ui/30-generate/ui-mockup-generation/SKILL.md",
        "game-art/30-generate/image-generation-contract",
    )
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
