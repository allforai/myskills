#!/usr/bin/env python3
"""Validate genre/art specialization governance contracts.

This validator is intentionally structural. It checks that the meta-skill can
generate project-local specialized skills without polluting bundled global
skills or Sub-Skill Mapping.
"""

import argparse
import re
import sys
from pathlib import Path


SPECIALIZED_SKILL_ROOT = ".allforai/bootstrap/specialized-skills/"
SPECIALIZATION_KNOWLEDGE = "knowledge/domains/game-genre-specialization.md"
REQUIRED_SECTIONS = {
    "Input Contract",
    "Output Contract",
    "Invocation Contract",
    "Automatic Validation",
    "Repair Routing",
    "Completion Conditions",
}
GENRE_TIGHT_GLOBAL_NAME_TERMS = {
    "lianliankan",
    "onet",
    "mahjong-connect",
    "match3",
    "match-3",
    "tower-defense",
    "rhythm-chart",
    "beatmap",
    "deck-builder",
    "deckbuilding",
    "roguelike-seed",
    "merge-chain",
    "word-puzzle",
}


def _read(path: Path) -> str:
    return path.read_text()


def _contains_genre_tight_name_term(path_text: str, term: str) -> bool:
    escaped = re.escape(term)
    return re.search(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", path_text) is not None


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


def validate_specialization_contracts(repo_root: str) -> list[str]:
    root = Path(repo_root)
    errors: list[str] = []

    bootstrap = root / "claude/meta-skill/skills/bootstrap.md"
    game_design = root / "claude/meta-skill/knowledge/capabilities/game-design.md"
    specialization = root / "claude/meta-skill/knowledge/domains/game-genre-specialization.md"
    skills_root = root / "claude/meta-skill/skills"

    for path in [bootstrap, game_design, specialization, skills_root]:
        if not path.exists():
            errors.append(f"{path}: required specialization governance path missing")
    if errors:
        return errors

    bootstrap_text = _read(bootstrap)
    game_design_text = _read(game_design)
    specialization_text = _read(specialization)

    if SPECIALIZATION_KNOWLEDGE not in bootstrap_text:
        errors.append("bootstrap.md: does not read game-genre-specialization knowledge")
    if "game-genre-specialization.md" not in game_design_text:
        errors.append("game-design.md: does not reference game-genre-specialization knowledge")
    if SPECIALIZED_SKILL_ROOT not in bootstrap_text:
        errors.append("bootstrap.md: missing project-local specialized skill output root")
    if SPECIALIZED_SKILL_ROOT not in game_design_text:
        errors.append("game-design.md: missing project-local specialized skill output root")
    if SPECIALIZED_SKILL_ROOT not in specialization_text:
        errors.append("game-genre-specialization.md: missing specialized skill output root")

    for section in sorted(REQUIRED_SECTIONS):
        if f"`{section}`" not in bootstrap_text:
            errors.append(f"bootstrap.md: missing required specialized skill section `{section}`")
        if f"`{section}`" not in specialization_text and f"## {section}" not in specialization_text:
            errors.append(
                f"game-genre-specialization.md: missing required specialized skill section `{section}`"
            )

    sub_skill_mapping = _section(
        game_design_text,
        "## Sub-Skill Mapping",
        "**Path validation:**",
    )
    if SPECIALIZED_SKILL_ROOT in sub_skill_mapping:
        errors.append("game-design.md: Sub-Skill Mapping must not reference project-local specialized skills")
    if re.search(r"`[^`]*\.allforai/bootstrap/specialized-skills/[^`]*`", game_design_text):
        mapping_mentions = [
            line for line in game_design_text.splitlines()
            if SPECIALIZED_SKILL_ROOT in line and "| `" in line
        ]
        if mapping_mentions:
            errors.append("game-design.md: table-like specialized-skill reference may pollute bundled mapping")

    for skill_file in sorted(skills_root.rglob("SKILL.md")):
        rel = skill_file.relative_to(skills_root).as_posix()
        rel_lower = rel.lower()
        for term in sorted(GENRE_TIGHT_GLOBAL_NAME_TERMS):
            if _contains_genre_tight_name_term(rel_lower, term):
                errors.append(
                    f"skills/{rel}: genre-tight skill name belongs in project-local specialized-skills"
                )

    for project_skill in sorted(root.glob(".allforai/bootstrap/specialized-skills/*/SKILL.md")):
        text = _read(project_skill)
        rel = project_skill.relative_to(root).as_posix()
        for section in sorted(REQUIRED_SECTIONS):
            if f"## {section}" not in text:
                errors.append(f"{rel}: missing required section ## {section}")
        lower = text.lower()
        if any(term in lower for term in ["runtime", "executable", "solver", "screenshot"]):
            if not any(term in lower for term in ["blocked", "failed_validation", "failed validation"]):
                errors.append(f"{rel}: executable validation mentioned without blocked/failed state")

    return errors


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo_root", nargs="?", default=".")
    args = parser.parse_args(argv)
    errors = validate_specialization_contracts(args.repo_root)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
