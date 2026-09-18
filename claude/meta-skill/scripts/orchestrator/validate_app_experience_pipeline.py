#!/usr/bin/env python3
"""Validate static app-design experience-gate pipeline wiring."""

import argparse
import re
import sys
from pathlib import Path


REQUIRED_PARENT_TERMS = {
    "experience-quality-critique",
    "${CLAUDE_PLUGIN_ROOT}/skills/app-design/40-qa/experience-quality-critique/SKILL.md",
    "contract_defect",
    "evidence_based_critique",
    "llm_judgment",
    "insufficient_evidence",
    ".allforai/app-design/qa/",
    "docs/experience-review/",
}

REQUIRED_CRITIQUE_TERMS = {
    ".allforai/app-design/qa/experience-quality-critique-design.json",
    ".allforai/app-design/qa/experience-quality-critique-design.html",
    ".allforai/app-design/qa/experience-quality-critique-runtime.json",
    ".allforai/app-design/qa/experience-quality-critique-runtime.html",
    "docs/experience-review/",
    "onboarding",
    "process_feedback",
    "next_step",
    "state_consistency",
    "return_reason",
    "mainline",
    "direction_fidelity",
    "audience_leak",
    "contract_defect",
    "evidence_based_critique",
    "llm_judgment",
    "insufficient_evidence",
    "must_fix_before_implementation",
    "must_fix_before_release",
    "recommended_iterations",
    "experience_gaps",
    "review_language",
    "zh-CN",
    "repair_route",
    "counterexample_or_comparison",
    "rerun_from_node_id",
    "fresh-context",
}


# bootstrap.md plus the protocol files it delegates to; missing files are skipped.
BOOTSTRAP_CORPUS = (
    "claude/meta-skill/skills/bootstrap/SKILL.md",
    "claude/meta-skill/knowledge/bootstrap-planning.md",
    "claude/meta-skill/knowledge/capabilities/app-design.md",
)
CRITIQUE_PATH = "skills/app-design/40-qa/experience-quality-critique/SKILL.md"


def _read(path: Path) -> str:
    return path.read_text()


def _bootstrap_corpus(root: Path) -> str:
    return "\n".join(_read(root / rel) for rel in BOOTSTRAP_CORPUS if (root / rel).exists())


def _has_term(text: str, term: str) -> bool:
    return term in text or term in " ".join(text.split())


def _canonical_refs(text: str) -> set[str]:
    pattern = re.compile(
        r"\$\{CLAUDE_PLUGIN_ROOT\}/skills/(app-design/[^\s`]+/SKILL\.md)"
    )
    return set(pattern.findall(text))


def validate_app_experience_pipeline(repo_root: str) -> list[str]:
    root = Path(repo_root)
    skills_root = root / "claude/meta-skill/skills"
    app_root = skills_root / "app-design"
    app_pack = app_root / "PACK.md"
    critique = app_root / "40-qa/experience-quality-critique/SKILL.md"

    errors: list[str] = []
    for path in [app_pack, critique]:
        if not path.exists():
            errors.append(f"{path}: required app-design pipeline file missing")
    if errors:
        return errors

    parent_text = _read(app_pack)
    critique_text = _read(critique)
    listed_refs = _canonical_refs(parent_text)

    for skill_file in sorted(app_root.rglob("SKILL.md")):
        if skill_file == app_pack:
            continue
        ref = skill_file.relative_to(skills_root).as_posix()
        if ref not in listed_refs:
            errors.append(f"app-design/PACK.md: missing canonical child path skills/{ref}")

    for term in sorted(REQUIRED_PARENT_TERMS):
        if not _has_term(parent_text, term):
            errors.append(f"app-design/PACK.md: missing app pack term {term}")
    for term in sorted(REQUIRED_CRITIQUE_TERMS):
        if not _has_term(critique_text, term):
            errors.append(f"experience-quality-critique: missing required term {term}")

    if CRITIQUE_PATH not in _bootstrap_corpus(root):
        errors.append(
            "bootstrap corpus: experience-quality-critique is not wired; "
            "bootstrap-planning.md or app-design.md must reference " + CRITIQUE_PATH
        )

    return errors


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo_root", nargs="?", default=".")
    args = parser.parse_args(argv)
    errors = validate_app_experience_pipeline(args.repo_root)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
