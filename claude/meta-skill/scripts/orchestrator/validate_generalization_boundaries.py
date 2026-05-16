#!/usr/bin/env python3
"""Validate that generic meta-skill layers do not absorb project-specific rules."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path("claude/meta-skill")


RULES = {
    "skills/bootstrap.md": (
        "Canvas2D",
        "canvas2d",
        "deviceScaleFactor",
        "DPR screenshot",
        "progression map",
        "progression_map",
        "level-select",
        "world-map",
        "mission-map",
        "chapter-map",
        "map metaphor",
        "prototype map geometry",
    ),
    "skills/game-ui/20-spec/screen-layout-spec/SKILL.md": (
        "progression_map_contract",
        "progression map acceptance",
        "map metaphor",
        "prototype map geometry",
        "level-select",
        "world-map",
        "mission-map",
        "chapter-map",
    ),
    "skills/game-ui/40-qa/ui-readability-qa/SKILL.md": (
        "progression_map_contract",
        "progression map acceptance",
        "map metaphor",
        "prototype map geometry",
        "level-select",
        "world-map",
        "mission-map",
        "chapter-map",
    ),
    "skills/visual-qa/20-spec/visual-acceptance-criteria/SKILL.md": (
        "progression map acceptance",
        "progression_map_contract",
        "map metaphor",
        "prototype map geometry",
        "level-select",
        "world-map",
        "mission-map",
        "chapter-map",
    ),
    "skills/game-frontend/40-qa/runtime-gameplay-visual-acceptance/SKILL.md": (
        "progression map acceptance",
        "progression_map_contract",
        "map metaphor",
        "prototype map geometry",
        "level-select",
        "world-map",
        "mission-map",
        "chapter-map",
    ),
}


REQUIRED_GENERIC_TERMS = {
    "skills/bootstrap.md": (
        "screen archetype",
        "project-local criteria artifact",
        "project's concept, UI registry, art direction, scene flow, and runtime handoff",
        "## Quality Acceptance",
        "## Attention Contract",
        "Primary outcome",
        "Non-goals",
        "Stop conditions",
        "Bootstrap should spend context once",
        "execute in pull mode",
        "quality-driven acceptance",
        "not_good_enough",
        "quality_gaps",
    ),
    "skills/game-ui/20-spec/screen-layout-spec/SKILL.md": (
        "screen_archetype_contract",
        "project concept",
        "not hard-code one project's screen type as universal",
    ),
    "skills/visual-qa/20-spec/visual-acceptance-criteria/SKILL.md": (
        "screen-specific archetype",
        "project-local screen archetype contract",
    ),
    "skills/meta-orchestration/40-qa/bootstrap-node-expansion-qa/SKILL.md": (
        "Quality-driven acceptance",
        "existence-only completion",
        "missing_quality_acceptance",
        "quality_gaps",
        "Attention management",
        "missing_attention_contract",
        "unbounded_context_pull",
        "Bootstrap context compression",
    ),
}


def main() -> int:
    errors: list[str] = []
    for rel, forbidden_terms in RULES.items():
        path = ROOT / rel
        if not path.exists():
            errors.append(f"{path}: missing file for generalization boundary check")
            continue
        text = path.read_text(encoding="utf-8")
        for term in forbidden_terms:
            if term in text:
                errors.append(
                    f"{path}: generic layer contains project/screen-specific term "
                    f"{term!r}; move concrete rules to runtime knowledge or "
                    "project-local specialized skills"
                )

    for rel, required_terms in REQUIRED_GENERIC_TERMS.items():
        path = ROOT / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for term in required_terms:
            if term not in text:
                errors.append(f"{path}: missing generic specialization boundary term {term!r}")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
