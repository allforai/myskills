#!/usr/bin/env python3
"""Validate static game-creative pipeline wiring."""

import argparse
import re
import sys
from pathlib import Path


REQUIRED_PARENT_TERMS = {
    "creative-quality-critique",
    "${CLAUDE_PLUGIN_ROOT}/skills/game-creative/40-qa/creative-quality-critique/SKILL.md",
    "contract_defect",
    "evidence_based_critique",
    "llm_judgment",
    "insufficient_evidence",
    ".allforai/game-creative/",
}

REQUIRED_CRITIQUE_TERMS = {
    ".allforai/game-creative/creative-quality-critique.json",
    ".allforai/game-creative/creative-quality-critique.html",
    "hook_score",
    "coherence_score",
    "novelty_score",
    "readability_score",
    "emotional_curve_score",
    "production_fit_score",
    "market_fit_score",
    "audiovisual_sync_score",
    "frontend_experience_score",
    "contract_defect",
    "evidence_based_critique",
    "llm_judgment",
    "insufficient_evidence",
    "must_fix_before_art_gen",
    "must_fix_before_frontend",
    "must_fix_before_release",
    "recommended_iterations",
    "review_language",
    "zh-CN",
    "repair_route",
    "counterexample_or_comparison",
}


def _read(path: Path) -> str:
    return path.read_text()


def _has_term(text: str, term: str) -> bool:
    return term in text or term in " ".join(text.split())


def _canonical_refs(text: str) -> set[str]:
    pattern = re.compile(
        r"\$\{CLAUDE_PLUGIN_ROOT\}/skills/(game-creative/[^\s`]+/SKILL\.md)"
    )
    return set(pattern.findall(text))


def validate_game_creative_pipeline(repo_root: str) -> list[str]:
    root = Path(repo_root)
    skills_root = root / "claude/meta-skill/skills"
    creative_root = skills_root / "game-creative"
    creative_pack = creative_root / "SKILL.md"
    critique = creative_root / "40-qa/creative-quality-critique/SKILL.md"

    errors: list[str] = []
    for path in [creative_pack, critique]:
        if not path.exists():
            errors.append(f"{path}: required game-creative pipeline file missing")
    if errors:
        return errors

    parent_text = _read(creative_pack)
    critique_text = _read(critique)
    listed_refs = _canonical_refs(parent_text)

    for skill_file in sorted(creative_root.rglob("SKILL.md")):
        if skill_file == creative_pack:
            continue
        ref = skill_file.relative_to(skills_root).as_posix()
        if ref not in listed_refs:
            errors.append(f"game-creative/SKILL.md: missing canonical child path skills/{ref}")

    for term in sorted(REQUIRED_PARENT_TERMS):
        if not _has_term(parent_text, term):
            errors.append(f"game-creative/SKILL.md: missing creative pack term {term}")
    for term in sorted(REQUIRED_CRITIQUE_TERMS):
        if not _has_term(critique_text, term):
            errors.append(f"creative-quality-critique: missing required term {term}")

    return errors


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo_root", nargs="?", default=".")
    args = parser.parse_args(argv)
    errors = validate_game_creative_pipeline(args.repo_root)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
