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
${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/visual-acceptance-review/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/00-env/2d-animation-toolchain-env/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/00-env/image-model-capability-registry/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/00-env/production-tool-capability-registry/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/10-design/2d-animation-production-plan/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/10-design/asset-source-strategy-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/20-spec/asset-acceptance-criteria/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/20-spec/asset-pack-search-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/20-spec/character-layer-sheet/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/30-generate/image-generation-contract/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/30-generate/batch-image-generation/SKILL.md
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
.allforai/game-design/art/qa/visual-acceptance-task-list.json
visual-qa/40-qa/batch-visual-acceptance/SKILL.md
visual-qa/batch-visual-acceptance
visual-qa/00-env/visual-model-capability-registry/SKILL.md
codex-cli-delegation/30-execute/codex-cli-task/SKILL.md
codex-cli-delegation/30-execute/codex-cli-task/SKILL.md
visual_model_routing
blocked_by_missing_visual_model_capability
.allforai/game-design/art/qa/visual-acceptance-batches/
.allforai/game-design/art/qa/codex-visual-review.json
.allforai/game-design/art/qa/codex-visual-review.md
.allforai/game-design/art/qa/visual-review-closure-audit.json
.allforai/game-design/art/qa/visual-review-closure-audit.md
.allforai/game-design/art/qa/visual-repair-loop-report.json
.allforai/game-design/art/qa/visual-repair-loop-report.md
.allforai/game-design/art/art-concept-validation.html
.allforai/game-design/art/art-concept-validation.json
.allforai/game-design/art/export/engine-ready-art-output-contract.json
.allforai/game-runtime/art/engine-ready-art-manifest.json
.allforai/game-design/art/qa/runtime-import-check-report.json
.allforai/game-design/art/image-generation/accepted-image-manifest.json
raw PNG/JPG/WebP paths
image-model-capability-registry
game-art/20-spec/asset-acceptance-criteria/SKILL.md
""",
    )
    _write(
        tmp_path,
        "claude/meta-skill/skills/game-art/10-design/art-concept-validation/SKILL.md",
        "---\nname: art-concept-validation\ndescription: x\n---\n",
    )
    for rel in [
        "art-preview-qa",
        "visual-acceptance-review",
        "2d-style-consistency-qa",
        "atlas-packaging",
        "runtime-import-check",
        "asset-license-provenance-qa",
    ]:
        _write(tmp_path, f"claude/meta-skill/skills/game-art/40-qa/{rel}/SKILL.md", "---\nname: x\ndescription: x\n---\n")
    _write(
        tmp_path,
        "claude/meta-skill/skills/game-art/40-qa/art-preview-qa/SKILL.md",
        """Manifest-only review is not allowed
blocked_by_missing_visual_evidence
visual_evidence_inspected: true
actual visual evidence was inspected
""",
    )
    _write(
        tmp_path,
        "claude/meta-skill/skills/game-art/40-qa/visual-acceptance-review/SKILL.md",
        """.allforai/game-design/art/qa/visual-acceptance-task-list.json
.allforai/game-design/art/qa/visual-acceptance-batches/
.allforai/game-design/art/qa/codex-visual-review.json
.allforai/game-design/art/qa/codex-visual-review.md
.allforai/game-design/art/qa/visual-review-closure-audit.json
.allforai/game-design/art/qa/visual-review-closure-audit.md
.allforai/game-design/art/qa/visual-repair-loop-report.json
.allforai/game-design/art/qa/visual-repair-loop-report.md
.allforai/game-design/art/asset-acceptance-criteria.json
.allforai/game-design/art/asset-acceptance-criteria.md
codex-cli-delegation/30-execute/codex-cli-task/SKILL.md
visual-qa/40-qa/batch-visual-acceptance/SKILL.md
visual-qa/batch-visual-acceptance
visual-qa/00-env/visual-model-capability-registry/SKILL.md
visual_model_routing
blocked_by_missing_visual_model_capability
Codex CLI
Claude Code closure audit
Claude Code does not re-judge visual quality
without re-scoring visual quality
audit_verdict
Repair And Revalidation Loop
image-feedback-report.json
process_downstream_feedback
rerun Codex CLI review
batch Markdown documents
.allforai/bootstrap/specialized-skills/<specialization_id>-art-generation/SKILL.md
Project-Specific Acceptance
blocked_by_missing_codex_cli
blocked_by_missing_visual_evidence
Do not accept manifest-only review
visual evidence paths
""",
    )
    _write(
        tmp_path,
        "claude/meta-skill/skills/visual-qa/40-qa/batch-visual-acceptance/SKILL.md",
        """codex-cli-delegation/30-execute/codex-cli-task/SKILL.md
short, path-based prompt
Do not paste batch contents
--return-all-messages
final report files
""",
    )
    _write(
        tmp_path,
        "claude/meta-skill/skills/codex-cli-delegation/30-execute/codex-cli-task/SKILL.md",
        """Pull Mode Delegation
pull mode
short prompt is not a vague prompt
target cwd
input paths
evidence directories
output paths
success/failure conditions
pulls the
needed context from the workspace
Do not push file contents
blocked_by_missing_input_paths
return_all_messages: false
""",
    )
    _write(
        tmp_path,
        "claude/meta-skill/skills/game-frontend/40-qa/visual-runtime-regression-qa/SKILL.md",
        """visual-qa/40-qa/batch-visual-acceptance/SKILL.md
codex-cli-delegation/30-execute/codex-cli-task/SKILL.md
.allforai/game-frontend/qa/codex-runtime-visual-review.json
.allforai/game-frontend/qa/codex-runtime-visual-review.md
.allforai/game-frontend/qa/runtime-visual-closure-audit.json
.allforai/game-frontend/qa/runtime-visual-closure-audit.md
Codex CLI must inspect screenshots
do not pass from probes or metadata alone
Claude Code performs only closure audit
blocked_by_missing_codex_cli
""",
    )
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
.allforai/game-design/art/asset-acceptance-criteria.json
asset-acceptance-criteria
consumer_ready` remains false
game-art/30-generate/batch-image-generation/SKILL.md
mcp-image-batch
long-task
.allforai/game-design/art/image-generation/mcp-image-batch-input.json
.allforai/game-design/art/image-generation/mcp-image-batch-task.json
.allforai/game-design/art/image-generation/mcp-image-batch-output.json
.allforai/game-design/art/image-generation/generated-image-files-manifest.json
blocked_by_missing_mcp_image_batch
Do not mark MCP outputs `consumer_ready: true` directly
""",
    )
    _write(
        tmp_path,
        "claude/meta-skill/skills/game-art/30-generate/batch-image-generation/SKILL.md",
        """mcp-image-batch
long-task image generation
file handoff
.allforai/game-design/art/image-generation/mcp-image-batch-input.json
.allforai/game-design/art/image-generation/mcp-image-batch-task.json
.allforai/game-design/art/image-generation/mcp-image-batch-output.json
.allforai/game-design/art/image-generation/generated-image-files-manifest.json
input file path
output file path
poll
task_id
blocked_by_missing_mcp_image_batch
Do not paste large
`image-generation-contract` may write accepted entries
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
mcp_image_batch
project_local_mcp
GOOGLE_API_KEY
FAL_KEY
OPENROUTER_API_KEY
output_modalities=image
generation_profile
missing_capabilities
blocked_by_missing_model
mcp-image-batch
mcp_long_task
batch_execution_skill=game-art/30-generate/batch-image-generation/SKILL.md
blocked_by_missing_mcp_image_batch
selected_model
""",
    )
    _write(
        tmp_path,
        "claude/meta-skill/skills/game-art/00-env/2d-animation-toolchain-env/SKILL.md",
        """.allforai/game-design/art/env/2d-animation-toolchain-report.json
.allforai/game-design/art/env/2d-animation-toolchain-registry.json
DragonBones
Spine
DragonBones-compatible JSON/atlas generation
DragonBones Pro GUI
required=false
project-local generator/adapter
GUI app presence without an automated export/import adapter
blocked_by_missing_toolchain
blocked_by_missing_runtime_profile
validation_evidence
install_policy
Do not silently switch DragonBones
""",
    )
    _write(
        tmp_path,
        "claude/meta-skill/skills/game-art/00-env/production-tool-capability-registry/SKILL.md",
        """Tool Capability Rule
Required capability must be an automatable execution path
GUI application
Do not mutate global PATH
Blender GUI presence alone is not executable evidence
Texture packing requires an atlas generator
Audio production requires provider APIs
""",
    )
    _write(
        tmp_path,
        "claude/meta-skill/skills/game-art/10-design/2d-animation-production-plan/SKILL.md",
        "game-art/00-env/2d-animation-toolchain-env .allforai/game-design/art/env/2d-animation-toolchain-report.json",
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
    _write(
        tmp_path,
        "claude/meta-skill/skills/game-art/20-spec/asset-acceptance-criteria/SKILL.md",
        """.allforai/game-design/art/asset-acceptance-criteria.json
.allforai/game-design/art/asset-acceptance-criteria.md
Project And Technology Variation
visual_acceptance
technical_acceptance
evidence_required
blocking_failure_codes
repair_routes
project/runtime-specific
Return `UPSTREAM_DEFECT`
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
            "game-art/30-generate/image-generation-contract game-art/00-env/2d-animation-toolchain-env",
        )
    _write(
        tmp_path,
        "claude/meta-skill/skills/game-art/30-generate/tileset-generation/SKILL.md",
        """game-art/30-generate/image-generation-contract
spec_only
planning only
cannot complete a production art-gen node
accepted image entries
preview maps
blocked_by_missing_visual_evidence
""",
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
.allforai/game-design/art/asset-acceptance-criteria.json
.allforai/game-design/art/asset-acceptance-criteria.md
asset-acceptance-criteria/SKILL.md
project-specific standards
technology-specific standards
.allforai/game-design/art/image-generation/accepted-image-manifest.json
consumer_ready: true
referenced image files exist
Spec-only, manifest-only, or path-existence-only output is not a completed art-gen node
blocked_by_missing_visual_evidence
**Art-QA Node Injection
${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/art-preview-qa/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/visual-acceptance-review/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/2d-style-consistency-qa/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/atlas-packaging/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/runtime-import-check/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/asset-license-provenance-qa/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/engine-ready-art-output-contract/SKILL.md
.allforai/game-design/art-qa-report.html
.allforai/game-design/art/qa/visual-acceptance-task-list.json
.allforai/game-design/art/qa/visual-acceptance-batches/
.allforai/game-design/art/qa/codex-visual-review.json
.allforai/game-design/art/qa/codex-visual-review.md
.allforai/game-design/art/qa/visual-review-closure-audit.json
.allforai/game-design/art/qa/visual-review-closure-audit.md
.allforai/game-design/art/qa/visual-repair-loop-report.json
.allforai/game-design/art/qa/visual-repair-loop-report.md
.allforai/game-design/art/export/engine-ready-art-output-contract.json
.allforai/game-runtime/art/engine-ready-art-manifest.json
Do not advance to `art-qa`
FAILED_VALIDATION
blocked_by_missing_visual_evidence
blocked_by_missing_codex_cli
regenerate/repair plus rerun Codex CLI review and Claude Code closure audit
image-feedback-report.json
UI screenshot + Codex CLI visual review hard gate
visual-qa/40-qa/batch-visual-acceptance/SKILL.md
codex-cli-delegation/30-execute/codex-cli-task/SKILL.md
.allforai/verify/codex-ui-visual-review.json
.allforai/verify/codex-ui-visual-review.md
.allforai/verify/ui-visual-closure-audit.json
.allforai/verify/ui-visual-closure-audit.md
Claude Code only performs closure audit
not re-score screenshot quality
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
