#!/usr/bin/env python3
"""Validate static game-art pipeline wiring.

This validator checks the art pipeline contracts that should be true before any
project-specific bootstrap run:

- every game-art child skill is listed by the parent pack canonical paths,
- every game-art/game-ui/game-frontend skill path referenced by bootstrap exists,
- art-qa includes the required QA gates before engine-ready handoff,
- engine-ready art manifest is produced by game-art and consumed by frontend
  asset binding.
"""

import argparse
import re
import sys
from pathlib import Path


REQUIRED_ART_QA_SKILLS = {
    "game-art/40-qa/art-preview-qa",
    "game-art/40-qa/visual-acceptance-review",
    "game-art/40-qa/2d-style-consistency-qa",
    "game-art/40-qa/atlas-packaging",
    "game-art/40-qa/runtime-import-check",
    "game-art/40-qa/asset-license-provenance-qa",
    "game-art/40-qa/engine-ready-art-output-contract",
}

REQUIRED_ART_QA_EXIT_ARTIFACTS = {
    ".allforai/game-design/art-qa-report.html",
    ".allforai/game-design/art/qa/visual-acceptance-task-list.json",
    ".allforai/game-design/art/qa/visual-acceptance-batches/",
    ".allforai/game-design/art/qa/codex-visual-review.json",
    ".allforai/game-design/art/qa/codex-visual-review.md",
    ".allforai/game-design/art/qa/visual-review-closure-audit.json",
    ".allforai/game-design/art/qa/visual-review-closure-audit.md",
    ".allforai/game-design/art/qa/visual-repair-loop-report.json",
    ".allforai/game-design/art/qa/visual-repair-loop-report.md",
    ".allforai/game-design/art/export/engine-ready-art-output-contract.json",
    ".allforai/game-runtime/art/engine-ready-art-manifest.json",
}

REQUIRED_ART_CONCEPT_ARTIFACTS = {
    ".allforai/game-design/art-pipeline-config.json",
    ".allforai/game-design/art/art-concept-validation.html",
    ".allforai/game-design/art/art-concept-validation.json",
}

ENGINE_READY_MANIFEST = ".allforai/game-runtime/art/engine-ready-art-manifest.json"
ACCEPTED_IMAGE_MANIFEST = ".allforai/game-design/art/image-generation/accepted-image-manifest.json"
IMAGE_MODEL_REGISTRY = ".allforai/game-design/art/image-generation/image-model-capability-registry.json"
IMAGE_MODEL_ROUTING_REPORT = ".allforai/game-design/art/image-generation/image-model-routing-report.json"
MCP_IMAGE_BATCH_INPUT = ".allforai/game-design/art/image-generation/mcp-image-batch-input.json"
MCP_IMAGE_BATCH_TASK = ".allforai/game-design/art/image-generation/mcp-image-batch-task.json"
MCP_IMAGE_BATCH_OUTPUT = ".allforai/game-design/art/image-generation/mcp-image-batch-output.json"
GENERATED_IMAGE_FILES_MANIFEST = ".allforai/game-design/art/image-generation/generated-image-files-manifest.json"
ASSET_ACCEPTANCE_CRITERIA_JSON = ".allforai/game-design/art/asset-acceptance-criteria.json"
ASSET_ACCEPTANCE_CRITERIA_MD = ".allforai/game-design/art/asset-acceptance-criteria.md"
ANIMATION_TOOLCHAIN_REPORT = ".allforai/game-design/art/env/2d-animation-toolchain-report.json"
ANIMATION_TOOLCHAIN_REGISTRY = ".allforai/game-design/art/env/2d-animation-toolchain-registry.json"

REQUIRED_IMAGE_CONTRACT_TERMS = {
    ACCEPTED_IMAGE_MANIFEST,
    IMAGE_MODEL_REGISTRY,
    IMAGE_MODEL_ROUTING_REPORT,
    "consumer_ready",
    "image-model-capability-registry",
    "route_model",
    "selected provider/model",
    "missing_capabilities",
    "register_searched_or_existing",
    "web_or_marketplace_search",
    "local_asset_library",
    "Downstream skills must not consume raw PNG paths directly",
    "re-run the downstream consumer validation",
    ASSET_ACCEPTANCE_CRITERIA_JSON,
    "asset-acceptance-criteria",
    "consumer_ready` remains false",
    "game-art/30-generate/batch-image-generation/SKILL.md",
    "mcp-image-batch",
    "long-task",
    MCP_IMAGE_BATCH_INPUT,
    MCP_IMAGE_BATCH_TASK,
    MCP_IMAGE_BATCH_OUTPUT,
    GENERATED_IMAGE_FILES_MANIFEST,
    "blocked_by_missing_mcp_image_batch",
    "Do not mark MCP outputs `consumer_ready: true` directly",
    "repair_coverage_shortage",
    "coverage shortage",
    "insufficient accepted images",
    "mcp-image-batch` file handoff",
    "operation",
    "context/base image",
    "maskRegion",
    "preservation acceptance",
}

REQUIRED_BATCH_IMAGE_GENERATION_TERMS = {
    "mcp-image-batch",
    "long-task image generation",
    "file handoff",
    MCP_IMAGE_BATCH_INPUT,
    MCP_IMAGE_BATCH_TASK,
    MCP_IMAGE_BATCH_OUTPUT,
    GENERATED_IMAGE_FILES_MANIFEST,
    "input file path",
    "output file path",
    "poll",
    "task_id",
    "blocked_by_missing_mcp_image_batch",
    "not paste large",
    "`image-generation-contract` may write accepted entries",
    "coverage shortage",
    "enough visually accepted images",
    "accepted output count is below",
    "triggers another",
    "mcp_image_batch_edit_file_handoff",
    "prepare_edit_session",
    "run_edit_prompt",
    "operation=edit",
    "contextImage",
    "basePrompt",
    "maskRegion",
    "imageIndex",
    "identity/style preservation outside the mask",
}

REQUIRED_ART_GEN_COMPLETION_TERMS = {
    ACCEPTED_IMAGE_MANIFEST,
    "consumer_ready: true",
    "referenced image files exist",
    "Spec-only, manifest-only, or path-existence-only output is not a completed art-gen node",
    "blocked_by_missing_visual_evidence",
}

REQUIRED_ART_PREVIEW_QA_TERMS = {
    "Manifest-only review is not allowed",
    "blocked_by_missing_visual_evidence",
    "visual_evidence_inspected: true",
    "actual visual evidence was inspected",
}

REQUIRED_VISUAL_ACCEPTANCE_TERMS = {
    "visual-qa/40-qa/batch-visual-acceptance/SKILL.md",
    "visual-qa/batch-visual-acceptance",
    "visual-qa/00-env/visual-model-capability-registry/SKILL.md",
    "codex-cli-delegation/30-execute/codex-cli-task/SKILL.md",
    "visual_model_routing",
    "blocked_by_missing_visual_model_capability",
    ".allforai/game-design/art/qa/visual-acceptance-task-list.json",
    ".allforai/game-design/art/qa/visual-acceptance-batches/",
    ".allforai/game-design/art/qa/codex-visual-review.json",
    ".allforai/game-design/art/qa/codex-visual-review.md",
    ".allforai/game-design/art/qa/visual-review-closure-audit.json",
    ".allforai/game-design/art/qa/visual-review-closure-audit.md",
    ".allforai/game-design/art/qa/visual-repair-loop-report.json",
    ".allforai/game-design/art/qa/visual-repair-loop-report.md",
    "Codex CLI",
    "Claude Code closure audit",
    "Claude Code does not re-judge visual quality",
    "without re-scoring visual quality",
    "audit_verdict",
    "Repair And Revalidation Loop",
    "image-feedback-report.json",
    "process_downstream_feedback",
    "repair_coverage_shortage",
    "coverage_shortage",
    "rerun Codex CLI review",
    "too few visually accepted candidates",
    "batch Markdown documents",
    ".allforai/bootstrap/specialized-skills/<specialization_id>-art-generation/SKILL.md",
    "Project-Specific Acceptance",
    ASSET_ACCEPTANCE_CRITERIA_JSON,
    ASSET_ACCEPTANCE_CRITERIA_MD,
    "blocked_by_missing_codex_cli",
    "blocked_by_missing_visual_evidence",
    "Do not accept manifest-only review",
    "visual evidence paths",
}

REQUIRED_CODEX_DELEGATION_TERMS = {
    "codex-cli-delegation/30-execute/codex-cli-task/SKILL.md",
    "short, path-based prompt",
    "Do not paste batch contents",
    "--return-all-messages",
    "final report files",
}

REQUIRED_CODEX_DELEGATION_SKILL_TERMS = {
    "Pull Mode Delegation",
    "pull mode",
    "short prompt is not a vague prompt",
    "target cwd",
    "input paths",
    "evidence directories",
    "output paths",
    "success/failure conditions",
    "pulls the",
    "needed context from the workspace",
    "Do not push file contents",
    "blocked_by_missing_input_paths",
    "return_all_messages: false",
}

REQUIRED_FRONTEND_VISUAL_RUNTIME_TERMS = {
    "visual-qa/40-qa/batch-visual-acceptance/SKILL.md",
    "codex-cli-delegation/30-execute/codex-cli-task/SKILL.md",
    ".allforai/game-frontend/qa/codex-runtime-visual-review.json",
    ".allforai/game-frontend/qa/codex-runtime-visual-review.md",
    ".allforai/game-frontend/qa/runtime-visual-closure-audit.json",
    ".allforai/game-frontend/qa/runtime-visual-closure-audit.md",
    "Codex CLI must inspect screenshots",
    "do not pass from probes or metadata alone",
    "Claude Code performs only closure audit",
    "blocked_by_missing_codex_cli",
}

REQUIRED_BOOTSTRAP_UI_VISUAL_TERMS = {
    "UI screenshot + Codex CLI visual review hard gate",
    "visual-qa/40-qa/batch-visual-acceptance/SKILL.md",
    "codex-cli-delegation/30-execute/codex-cli-task/SKILL.md",
    ".allforai/verify/codex-ui-visual-review.json",
    ".allforai/verify/codex-ui-visual-review.md",
    ".allforai/verify/ui-visual-closure-audit.json",
    ".allforai/verify/ui-visual-closure-audit.md",
    "Claude Code only performs closure audit",
    "not re-score screenshot quality",
    "blocked_by_missing_codex_cli",
}

REQUIRED_TILESET_GENERATION_TERMS = {
    "spec_only",
    "planning only",
    "cannot complete a production art-gen node",
    "accepted image entries",
    "preview maps",
    "blocked_by_missing_visual_evidence",
}

REQUIRED_ACCEPTANCE_CRITERIA_TERMS = {
    ASSET_ACCEPTANCE_CRITERIA_JSON,
    ASSET_ACCEPTANCE_CRITERIA_MD,
    "Project And Technology Variation",
    "visual_acceptance",
    "technical_acceptance",
    "evidence_required",
    "blocking_failure_codes",
    "repair_routes",
    "project/runtime-specific",
    "Return `UPSTREAM_DEFECT`",
}

REQUIRED_SOURCE_STRATEGY_TERMS = {
    "source_priority_chain",
    "local_asset_library",
    "user_provided_asset",
    "web_or_marketplace_search",
    "llm_image_generation",
    ACCEPTED_IMAGE_MANIFEST,
    "consumer_ready: true",
}

REQUIRED_ASSET_SEARCH_TERMS = {
    "source_order",
    "project-local asset folders",
    "user-provided bundles",
    "wider web search",
    "register_searched_or_existing",
    ACCEPTED_IMAGE_MANIFEST,
    "consumer_ready: true",
}

REQUIRED_IMAGE_MODEL_REGISTRY_TERMS = {
    IMAGE_MODEL_REGISTRY,
    IMAGE_MODEL_ROUTING_REPORT,
    "google_gemini_image",
    "fal_ai",
    "openrouter_image",
    "mcp_image_batch",
    "project_local_mcp",
    "GOOGLE_API_KEY",
    "FAL_KEY",
    "OPENROUTER_API_KEY",
    "output_modalities=image",
    "generation_profile",
    "missing_capabilities",
    "blocked_by_missing_model",
    "mcp-image-batch",
    "mcp_long_task",
    "batch_execution_skill=game-art/30-generate/batch-image-generation/SKILL.md",
    "blocked_by_missing_mcp_image_batch",
    "supports_edit_mode=true",
    "missing edit capability",
    "selected_model",
}

REQUIRED_2D_ANIMATION_TOOLCHAIN_TERMS = {
    ANIMATION_TOOLCHAIN_REPORT,
    ANIMATION_TOOLCHAIN_REGISTRY,
    "DragonBones",
    "Spine",
    "DragonBones-compatible JSON/atlas generation",
    "DragonBones Pro GUI",
    "required=false",
    "project-local generator/adapter",
    "GUI app presence without an automated export/import adapter",
    "blocked_by_missing_toolchain",
    "blocked_by_missing_runtime_profile",
    "validation_evidence",
    "install_policy",
    "Do not silently switch DragonBones",
}

REQUIRED_PRODUCTION_TOOL_RULE_TERMS = {
    "Tool Capability Rule",
    "Required capability must be an automatable execution path",
    "GUI application",
    "Do not mutate global PATH",
    "Blender GUI presence alone is not executable evidence",
    "Texture packing requires an atlas generator",
    "Audio production requires provider APIs",
}

IMAGE_UPSTREAM_CONSUMER_SKILLS = {
    "game-art/20-spec/character-layer-sheet/SKILL.md",
    "game-art/30-generate/background-generation/SKILL.md",
    "game-art/30-generate/decal-generation/SKILL.md",
    "game-art/30-generate/expression-set-generation/SKILL.md",
    "game-art/30-generate/frame-animation-generation/SKILL.md",
    "game-art/30-generate/icon-generation/SKILL.md",
    "game-art/30-generate/item-art-generation/SKILL.md",
    "game-art/30-generate/particle-system/SKILL.md",
    "game-art/30-generate/portrait-generation/SKILL.md",
    "game-art/30-generate/prop-generation/SKILL.md",
    "game-art/30-generate/skeletal-animation/SKILL.md",
    "game-art/30-generate/sprite-vfx-generation/SKILL.md",
    "game-art/30-generate/tileset-generation/SKILL.md",
    "game-art/30-generate/trail-generation/SKILL.md",
    "game-ui/30-generate/ui-mockup-generation/SKILL.md",
}

ANIMATION_TOOLCHAIN_CONSUMER_SKILLS = {
    "game-art/10-design/2d-animation-production-plan/SKILL.md",
    "game-art/30-generate/skeletal-animation/SKILL.md",
}

SKILL_REF_RE = re.compile(
    r"(?:\$\{CLAUDE_PLUGIN_ROOT\}/)?skills/((?:game-art|game-ui|game-frontend|visual-qa|codex-cli-delegation)/[^\s`)]+/SKILL\.md)"
)


def _read(path: Path) -> str:
    return path.read_text()


def _skill_ref_to_path(root: Path, ref: str) -> Path:
    return root / "claude/meta-skill/skills" / ref


def _skill_ref_to_slug(ref: str) -> str:
    return ref.removesuffix("/SKILL.md")


def _canonical_refs(text: str, pack_name: str) -> set:
    pattern = re.compile(
        rf"\$\{{CLAUDE_PLUGIN_ROOT\}}/skills/({re.escape(pack_name)}/[^\s`]+/SKILL\.md)"
    )
    return set(pattern.findall(text))


def _section(text: str, start_marker: str, end_marker: str | None = None) -> str:
    start = text.find(start_marker)
    if start == -1:
        return ""
    if not end_marker:
        return text[start:]
    end = text.find(end_marker, start + len(start_marker))
    if end == -1:
        return text[start:]
    return text[start:end]


def validate_art_pipeline(repo_root: str) -> list:
    root = Path(repo_root)
    errors = []

    skills_root = root / "claude/meta-skill/skills"
    game_art_root = skills_root / "game-art"
    game_art_pack = game_art_root / "SKILL.md"
    bootstrap = root / "claude/meta-skill/skills/bootstrap.md"
    game_design = root / "claude/meta-skill/knowledge/capabilities/game-design.md"
    engine_ready = game_art_root / "40-qa/engine-ready-art-output-contract/SKILL.md"
    asset_binding = skills_root / "game-frontend/20-spec/asset-import-binding-spec/SKILL.md"
    image_contract = game_art_root / "30-generate/image-generation-contract/SKILL.md"
    batch_image_generation = game_art_root / "30-generate/batch-image-generation/SKILL.md"
    tileset_generation = game_art_root / "30-generate/tileset-generation/SKILL.md"
    art_preview_qa = game_art_root / "40-qa/art-preview-qa/SKILL.md"
    visual_acceptance = game_art_root / "40-qa/visual-acceptance-review/SKILL.md"
    acceptance_criteria = game_art_root / "20-spec/asset-acceptance-criteria/SKILL.md"
    codex_delegation = skills_root / "codex-cli-delegation/30-execute/codex-cli-task/SKILL.md"
    frontend_visual_runtime = skills_root / "game-frontend/40-qa/visual-runtime-regression-qa/SKILL.md"
    image_model_registry = game_art_root / "00-env/image-model-capability-registry/SKILL.md"
    animation_toolchain_env = game_art_root / "00-env/2d-animation-toolchain-env/SKILL.md"
    production_tool_registry = game_art_root / "00-env/production-tool-capability-registry/SKILL.md"
    source_strategy = game_art_root / "10-design/asset-source-strategy-spec/SKILL.md"
    asset_search = game_art_root / "20-spec/asset-pack-search-spec/SKILL.md"

    required_files = [
        game_art_pack,
        bootstrap,
        game_design,
        engine_ready,
        asset_binding,
        image_contract,
        batch_image_generation,
        tileset_generation,
        art_preview_qa,
        visual_acceptance,
        acceptance_criteria,
        codex_delegation,
        frontend_visual_runtime,
        image_model_registry,
        animation_toolchain_env,
        production_tool_registry,
        source_strategy,
        asset_search,
    ]
    for path in required_files:
        if not path.exists():
            errors.append(f"{path}: required art pipeline file missing")
    if errors:
        return errors

    game_art_text = _read(game_art_pack)
    bootstrap_text = _read(bootstrap)
    game_design_text = _read(game_design)
    engine_ready_text = _read(engine_ready)
    asset_binding_text = _read(asset_binding)
    image_contract_text = _read(image_contract)
    batch_image_generation_text = _read(batch_image_generation)
    tileset_generation_text = _read(tileset_generation)
    art_preview_qa_text = _read(art_preview_qa)
    visual_acceptance_text = _read(visual_acceptance)
    acceptance_criteria_text = _read(acceptance_criteria)
    codex_delegation_text = _read(codex_delegation)
    frontend_visual_runtime_text = _read(frontend_visual_runtime)
    image_model_registry_text = _read(image_model_registry)
    animation_toolchain_env_text = _read(animation_toolchain_env)
    production_tool_registry_text = _read(production_tool_registry)
    source_strategy_text = _read(source_strategy)
    asset_search_text = _read(asset_search)

    listed_game_art_refs = _canonical_refs(game_art_text, "game-art")
    for skill_file in sorted(game_art_root.rglob("SKILL.md")):
        if skill_file == game_art_pack:
            continue
        ref = skill_file.relative_to(skills_root).as_posix()
        if ref not in listed_game_art_refs:
            errors.append(f"game-art/SKILL.md: missing canonical child path skills/{ref}")

    for ref in sorted(set(SKILL_REF_RE.findall(bootstrap_text))):
        target = _skill_ref_to_path(root, ref)
        if not target.exists():
            errors.append(f"bootstrap.md: referenced art pipeline skill missing: skills/{ref}")

    art_concept_section = _section(
        bootstrap_text,
        "**Art Concept Node Injection",
        "**Concept Freeze Node Injection",
    )
    if not art_concept_section:
        errors.append("bootstrap.md: Art Concept Node Injection section missing")
    else:
        if "game-art/10-design/art-concept-validation/SKILL.md" not in art_concept_section:
            errors.append("bootstrap.md: art-concept does not invoke art-concept-validation")
        for artifact in sorted(REQUIRED_ART_CONCEPT_ARTIFACTS):
            if artifact not in art_concept_section:
                errors.append(f"bootstrap.md: art-concept missing exit artifact {artifact}")
        if 'state in ["passed", "passed_with_warnings"]' not in art_concept_section:
            errors.append("bootstrap.md: art-concept completion does not gate validation state")

    concept_freeze_section = _section(
        bootstrap_text,
        "**Concept Freeze Node Injection",
        "**Art-Gen Node Injection",
    )
    if not concept_freeze_section:
        errors.append("bootstrap.md: Concept Freeze Node Injection section missing")
    else:
        if ".allforai/game-design/art/art-concept-validation.json" not in concept_freeze_section:
            errors.append("bootstrap.md: concept-freeze does not require art concept validation")
        if "UPSTREAM_DEFECT" not in concept_freeze_section:
            errors.append("bootstrap.md: concept-freeze missing art concept validation failure gate")

    art_qa_section = _section(
        bootstrap_text,
        "**Art-QA Node Injection",
        "**App Design Node Injection",
    )
    if not art_qa_section:
        errors.append("bootstrap.md: Art-QA Node Injection section missing")
    else:
        art_qa_refs = {_skill_ref_to_slug(ref) for ref in SKILL_REF_RE.findall(art_qa_section)}
        for required in sorted(REQUIRED_ART_QA_SKILLS):
            if required not in art_qa_refs:
                errors.append(f"bootstrap.md: art-qa missing required QA skill {required}")
        for artifact in sorted(REQUIRED_ART_QA_EXIT_ARTIFACTS):
            if artifact not in art_qa_section:
                errors.append(f"bootstrap.md: art-qa missing exit artifact {artifact}")
        if "Do not advance to `art-qa`" not in bootstrap_text:
            errors.append("bootstrap.md: art-gen UPSTREAM_DEFECT halt rule missing")
        for term in sorted(REQUIRED_ART_GEN_COMPLETION_TERMS):
            if term not in bootstrap_text:
                errors.append(f"bootstrap.md: art-gen completion missing visual closure term {term}")
        for term in ["FAILED_VALIDATION", "blocked_by_missing_visual_evidence", "blocked_by_missing_codex_cli"]:
            if term not in art_qa_section:
                errors.append(f"bootstrap.md: art-qa completion missing blocking status {term}")
        for term in [
            "asset-acceptance-criteria/SKILL.md",
            ASSET_ACCEPTANCE_CRITERIA_JSON,
            ASSET_ACCEPTANCE_CRITERIA_MD,
            "project-specific standards",
            "technology-specific standards",
        ]:
            if term not in bootstrap_text:
                errors.append(f"bootstrap.md: art-gen missing acceptance criteria term {term}")
        for term in [
            ".allforai/game-design/art/qa/visual-repair-loop-report.json",
            ".allforai/game-design/art/qa/visual-repair-loop-report.md",
            "regenerate/repair plus rerun Codex CLI review and Claude Code closure audit",
            "image-feedback-report.json",
        ]:
            if term not in art_qa_section:
                errors.append(f"bootstrap.md: art-qa missing visual repair loop term {term}")

    for term in sorted(REQUIRED_BOOTSTRAP_UI_VISUAL_TERMS):
        if term not in bootstrap_text:
            errors.append(f"bootstrap.md: UI screenshot visual gate missing term {term}")

    for artifact in REQUIRED_ART_QA_EXIT_ARTIFACTS:
        if artifact not in game_art_text and artifact not in engine_ready_text:
            errors.append(f"game-art: required program-facing artifact not documented: {artifact}")

    if ENGINE_READY_MANIFEST not in engine_ready_text:
        errors.append("engine-ready-art-output-contract: does not write engine-ready manifest")
    if ENGINE_READY_MANIFEST not in asset_binding_text:
        errors.append("asset-import-binding-spec: does not consume engine-ready manifest")
    if ENGINE_READY_MANIFEST not in game_design_text:
        errors.append("game-design.md: does not route program implementation through engine-ready manifest")
    for artifact in sorted(REQUIRED_ART_CONCEPT_ARTIFACTS - {".allforai/game-design/art-pipeline-config.json"}):
        if artifact not in game_design_text and artifact not in game_art_text:
            errors.append(f"game-design/game-art: art concept gate artifact not documented: {artifact}")

    if "runtime_id" not in engine_ready_text or "asset_id" not in engine_ready_text:
        errors.append("engine-ready-art-output-contract: missing runtime_id/asset_id contract")
    if "blocked_by_import_validation" not in asset_binding_text:
        errors.append("asset-import-binding-spec: missing blocked_by_import_validation state")
    if "blocked_by_runtime_import" not in engine_ready_text:
        errors.append("engine-ready-art-output-contract: missing blocked_by_runtime_import state")

    for term in sorted(REQUIRED_IMAGE_CONTRACT_TERMS):
        if term not in image_contract_text:
            errors.append(f"image-generation-contract: missing closure term {term}")
    for term in sorted(REQUIRED_BATCH_IMAGE_GENERATION_TERMS):
        if term not in batch_image_generation_text:
            errors.append(f"batch-image-generation: missing MCP batch term {term}")
    for term in sorted(REQUIRED_ART_PREVIEW_QA_TERMS):
        if term not in art_preview_qa_text:
            errors.append(f"art-preview-qa: missing visual evidence term {term}")
    for term in sorted(REQUIRED_VISUAL_ACCEPTANCE_TERMS):
        if term not in visual_acceptance_text:
            errors.append(f"visual-acceptance-review: missing review closure term {term}")
    batch_visual_acceptance = skills_root / "visual-qa/40-qa/batch-visual-acceptance/SKILL.md"
    if not batch_visual_acceptance.exists():
        errors.append(f"{batch_visual_acceptance}: required visual-qa batch skill missing")
    else:
        batch_visual_acceptance_text = _read(batch_visual_acceptance)
        for term in sorted(REQUIRED_CODEX_DELEGATION_TERMS):
            if term not in batch_visual_acceptance_text:
                errors.append(f"batch-visual-acceptance: missing codex delegation term {term}")
    for term in sorted(REQUIRED_CODEX_DELEGATION_SKILL_TERMS):
        if term not in codex_delegation_text:
            errors.append(f"codex-cli-task: missing pull-mode delegation term {term}")
    for term in sorted(REQUIRED_FRONTEND_VISUAL_RUNTIME_TERMS):
        if term not in frontend_visual_runtime_text:
            errors.append(f"visual-runtime-regression-qa: missing Codex screenshot review term {term}")
    for term in sorted(REQUIRED_TILESET_GENERATION_TERMS):
        if term not in tileset_generation_text:
            errors.append(f"tileset-generation: missing spec-only closure term {term}")
    for term in sorted(REQUIRED_ACCEPTANCE_CRITERIA_TERMS):
        if term not in acceptance_criteria_text:
            errors.append(f"asset-acceptance-criteria: missing standards term {term}")
    for term in sorted(REQUIRED_IMAGE_MODEL_REGISTRY_TERMS):
        if term not in image_model_registry_text:
            errors.append(f"image-model-capability-registry: missing model routing term {term}")
    for term in sorted(REQUIRED_2D_ANIMATION_TOOLCHAIN_TERMS):
        if term not in animation_toolchain_env_text:
            errors.append(f"2d-animation-toolchain-env: missing toolchain closure term {term}")
    for term in sorted(REQUIRED_PRODUCTION_TOOL_RULE_TERMS):
        if term not in production_tool_registry_text:
            errors.append(f"production-tool-capability-registry: missing tool capability rule term {term}")
    for term in sorted(REQUIRED_SOURCE_STRATEGY_TERMS):
        if term not in source_strategy_text:
            errors.append(f"asset-source-strategy-spec: missing source priority term {term}")
    for term in sorted(REQUIRED_ASSET_SEARCH_TERMS):
        if term not in asset_search_text:
            errors.append(f"asset-pack-search-spec: missing search cascade term {term}")
    if ACCEPTED_IMAGE_MANIFEST not in game_art_text:
        errors.append("game-art/SKILL.md: missing accepted image manifest closure rule")
    if "game-art/20-spec/asset-acceptance-criteria/SKILL.md" not in game_art_text:
        errors.append("game-art/SKILL.md: missing asset acceptance criteria child path")
    if "raw PNG/JPG/WebP paths" not in game_art_text:
        errors.append("game-art/SKILL.md: missing raw bitmap path consumption ban")
    if "game-art/00-env/image-model-capability-registry/SKILL.md" not in game_art_text:
        errors.append("game-art/SKILL.md: missing image model capability registry child path")
    if "game-art/00-env/2d-animation-toolchain-env/SKILL.md" not in game_art_text:
        errors.append("game-art/SKILL.md: missing 2D animation toolchain env child path")
    if IMAGE_MODEL_REGISTRY not in game_art_text and "image-model-capability-registry" not in game_art_text:
        errors.append("game-art/SKILL.md: missing image model routing closure rule")

    for ref in sorted(IMAGE_UPSTREAM_CONSUMER_SKILLS):
        skill_path = _skill_ref_to_path(root, ref)
        if not skill_path.exists():
            errors.append(f"image upstream consumer missing: skills/{ref}")
            continue
        skill_text = _read(skill_path)
        if "image-generation-contract" not in skill_text:
            errors.append(f"skills/{ref}: missing image-generation-contract reference")

    for ref in sorted(ANIMATION_TOOLCHAIN_CONSUMER_SKILLS):
        skill_path = _skill_ref_to_path(root, ref)
        if not skill_path.exists():
            errors.append(f"2d animation toolchain consumer missing: skills/{ref}")
            continue
        skill_text = _read(skill_path)
        if "2d-animation-toolchain" not in skill_text:
            errors.append(f"skills/{ref}: missing 2d-animation-toolchain-env/report reference")

    return errors


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo_root", nargs="?", default=".")
    args = parser.parse_args(argv)
    errors = validate_art_pipeline(args.repo_root)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
