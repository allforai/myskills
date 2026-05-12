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
    "game-art/40-qa/2d-style-consistency-qa",
    "game-art/40-qa/atlas-packaging",
    "game-art/40-qa/runtime-import-check",
    "game-art/40-qa/asset-license-provenance-qa",
    "game-art/40-qa/engine-ready-art-output-contract",
}

REQUIRED_ART_QA_EXIT_ARTIFACTS = {
    ".allforai/game-design/art-qa-report.html",
    ".allforai/game-design/art/export/engine-ready-art-output-contract.json",
    ".allforai/game-runtime/art/engine-ready-art-manifest.json",
}

REQUIRED_ART_CONCEPT_ARTIFACTS = {
    ".allforai/game-design/art-pipeline-config.json",
    ".allforai/game-design/art/art-concept-validation.html",
    ".allforai/game-design/art/art-concept-validation.json",
}

ENGINE_READY_MANIFEST = ".allforai/game-runtime/art/engine-ready-art-manifest.json"

SKILL_REF_RE = re.compile(
    r"(?:\$\{CLAUDE_PLUGIN_ROOT\}/)?skills/((?:game-art|game-ui|game-frontend)/[^\s`)]+/SKILL\.md)"
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

    required_files = [game_art_pack, bootstrap, game_design, engine_ready, asset_binding]
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
