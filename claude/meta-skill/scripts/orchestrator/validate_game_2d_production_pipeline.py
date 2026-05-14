#!/usr/bin/env python3
"""Validate static game-2d-production pipeline wiring."""

import argparse
import re
import sys
from pathlib import Path


CHILD_REFS = [
    "00-env/runtime-profile",
    "20-spec/view-mode-runtime-contract",
    "20-spec/core-loop-playable-contract",
    "20-spec/asset-runtime-binding-contract",
    "20-spec/input-feedback-contract",
    "20-spec/session-flow-contract",
    "30-generate/playable-slice-assembly",
    "40-qa/core-loop-playability-qa",
    "40-qa/asset-binding-visual-qa",
    "40-qa/session-completion-qa",
    "40-qa/code-repair-loop",
    "40-qa/2d-production-closure-qa",
]

REQUIRED_PARENT_TERMS = {
    "playable vertical slice",
    "not genre-specific",
    "project-local specialized skill",
    "game-frontend",
    "game-art",
    "game-ui",
    "game-audio",
    "runtime screenshot evidence",
    "2d-production-closure-qa",
    "code-repair-loop",
    "do not accept static review",
}

REQUIRED_CLOSURE_TERMS = {
    ".allforai/game-2d/qa/2d-production-closure-report.json",
    ".allforai/game-2d/qa/2d-production-closure.html",
    "engine-ready art manifest",
    "runtime_id",
    "asset_id",
    "playable vertical slice",
    "core-loop playability QA",
    "asset-binding visual QA",
    "session-completion QA",
    "code-repair-loop report",
    "revalidation report",
    "runtime-gameplay-visual-acceptance",
    "functional assertions and Codex CLI screenshot review",
    "blocked_by_unrunnable_client",
    "blocked_by_missing_screenshot",
    "blocked_by_missing_runtime_command",
    "failed_validation",
    "no blocker or major findings",
    "Do not accept static review",
}

REQUIRED_GAME_DESIGN_TERMS = {
    "game_2d_production",
    "game-2d-production",
    "after_game_frontend_bindings_and_runtime_art_audio_ui_manifests",
    "game-2d-production/40-qa/2d-production-closure-qa",
    "game-2d-production/40-qa/code-repair-loop",
    ".allforai/game-2d/qa/2d-production-closure-report.json",
    "do not accept static review",
}

REQUIRED_BOOTSTRAP_TERMS = {
    "2D game production handoff",
    "Game implementation handoff expansion",
    "game_2d_production",
    "required_closure_skills",
    "game-2d-production-closure-qa",
    "game-2d-production/40-qa/2d-production-closure-qa",
    "<specialization_id>-2d-production",
    "do not leave the",
}

REQUIRED_GAME_PRODUCTION_TERMS = {
    "game-2d-production",
    ".allforai/game-2d/qa/2d-production-closure-report.json",
    "visible runtime screenshot evidence",
}


def _read(path: Path) -> str:
    return path.read_text()


def _has_term(text: str, term: str) -> bool:
    return term in text or term in " ".join(text.split())


def _canonical_refs(text: str) -> set[str]:
    pattern = re.compile(
        r"\$\{CLAUDE_PLUGIN_ROOT\}/skills/(game-2d-production/[^\s`]+/SKILL\.md)"
    )
    return set(pattern.findall(text))


def _check_terms(errors: list[str], text: str, label: str, terms: set[str]) -> None:
    for term in sorted(terms):
        if not _has_term(text, term):
            errors.append(f"{label}: missing required 2D production term {term}")


def validate_game_2d_production_pipeline(repo_root: str) -> list[str]:
    root = Path(repo_root)
    skills_root = root / "claude/meta-skill/skills"
    production_root = skills_root / "game-2d-production"
    parent = production_root / "SKILL.md"
    closure = production_root / "40-qa/2d-production-closure-qa/SKILL.md"
    game_design = root / "claude/meta-skill/knowledge/capabilities/game-design.md"
    bootstrap = root / "claude/meta-skill/skills/bootstrap.md"
    game_production = skills_root / "game-production/SKILL.md"

    required_files = [parent, closure, game_design, bootstrap, game_production]
    required_files.extend(production_root / ref / "SKILL.md" for ref in CHILD_REFS)

    errors: list[str] = []
    for path in required_files:
        if not path.exists():
            errors.append(f"{path}: required game-2d-production pipeline file missing")
    if errors:
        return errors

    parent_text = _read(parent)
    closure_text = _read(closure)
    game_design_text = _read(game_design)
    bootstrap_text = _read(bootstrap)
    game_production_text = _read(game_production)

    listed_refs = _canonical_refs(parent_text)
    for ref in CHILD_REFS:
        canonical = f"game-2d-production/{ref}/SKILL.md"
        if canonical not in listed_refs:
            errors.append(f"game-2d-production/SKILL.md: missing canonical child path skills/{canonical}")

    for skill_file in sorted(production_root.rglob("SKILL.md")):
        if skill_file == parent:
            continue
        ref = skill_file.relative_to(skills_root).as_posix()
        if ref not in listed_refs:
            errors.append(f"game-2d-production/SKILL.md: missing canonical child path skills/{ref}")

    _check_terms(errors, parent_text, "game-2d-production/SKILL.md", REQUIRED_PARENT_TERMS)
    _check_terms(errors, closure_text, "2d-production-closure-qa", REQUIRED_CLOSURE_TERMS)
    _check_terms(errors, game_design_text, "game-design.md", REQUIRED_GAME_DESIGN_TERMS)
    _check_terms(errors, bootstrap_text, "bootstrap.md", REQUIRED_BOOTSTRAP_TERMS)
    _check_terms(errors, game_production_text, "game-production/SKILL.md", REQUIRED_GAME_PRODUCTION_TERMS)

    return errors


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo_root", nargs="?", default=".")
    args = parser.parse_args(argv)
    errors = validate_game_2d_production_pipeline(args.repo_root)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
