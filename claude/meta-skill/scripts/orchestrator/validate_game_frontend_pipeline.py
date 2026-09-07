#!/usr/bin/env python3
"""Validate static game-frontend pipeline wiring."""

import argparse
import re
import sys
from pathlib import Path


REQUIRED_PARENT_TERMS = {
    "runtime-architecture-design",
    "game-state-model-spec",
    "scene-flow-spec",
    "asset-loading-strategy-spec",
    "gameplay-system-binding-spec",
    "performance-budget-spec",
    "runtime-architecture-qa",
    "runtime-gameplay-visual-acceptance",
    "runtime-debug-bridge-contract",
    ".allforai/bootstrap/specialized-skills/<specialization_id>-frontend-runtime/SKILL.md",
    "knowledge/engines/",
    "generic frontend contract for all game runtimes",
    "corresponding runtime knowledge file",
}

REQUIRED_ASSEMBLY_TERMS = {
    ".allforai/game-frontend/design/runtime-architecture-design.json",
    ".allforai/game-frontend/bindings/game-state-model-spec.json",
    ".allforai/game-frontend/bindings/scene-flow-spec.json",
    ".allforai/game-frontend/bindings/asset-loading-strategy-spec.json",
    ".allforai/game-frontend/bindings/gameplay-system-binding-spec.json",
    ".allforai/game-frontend/bindings/runtime-debug-bridge-contract.json",
    "module_wiring_proofs",
    "preserved_exports",
    "zero production consumers",
    "rewriting an existing module",
    "Canvas2D",
}

REQUIRED_AUDIO_BINDING_TERMS = {
    "runtime_effect_assertions",
    "AudioBuffer",
    "AudioContext.state",
    "loadBGM",
    "loadSFX",
    "mock",
}

REQUIRED_GAMEPLAY_BINDING_TERMS = {
    "gameplay_rule_constraints",
    "pathfinding traversability",
    "null/shape-hole",
    "initial state contains a legal action",
}

REQUIRED_SMOKE_TERMS = {
    "deviceScaleFactor: 3",
    "central gameplay region is nonblank/nonblack",
    "I/O features",
    "runtime effects",
}

REQUIRED_PERFORMANCE_TERMS = {
    "Canvas2D",
    "DPR",
    "deviceScaleFactor: 3",
    "central gameplay region",
}

REQUIRED_ARCH_QA_TERMS = {
    "runtime-architecture-design.json",
    "game-state-model-spec.json",
    "scene-flow-spec.json",
    "gameplay-system-binding-spec.json",
    "asset-loading-strategy-spec.json",
    "performance-budget-spec.json",
    "do not substitute static review for runtime evidence",
    "specialization_required=true",
}

REQUIRED_RUNTIME_ARCH_TERMS = {
    ".allforai/bootstrap/specialized-skills/<specialization_id>-frontend-runtime/SKILL.md",
    "Specialization gate",
    "Do not encode Cocos/Phaser/Unity/Godot or genre-specific",
}

REQUIRED_GAMEPLAY_VISUAL_ACCEPTANCE_TERMS = {
    ".allforai/game-frontend/qa/runtime-gameplay-visual-acceptance-plan.json",
    ".allforai/game-frontend/qa/runtime-gameplay-screenshot-manifest.json",
    ".allforai/game-frontend/qa/runtime-gameplay-visual-batches/",
    (".allforai/game-frontend/qa/codex-gameplay-visual-review.json", ".allforai/game-frontend/qa/runtime-gameplay-visual-review-2.json"),
    (".allforai/game-frontend/qa/codex-gameplay-visual-review.md", ".allforai/game-frontend/qa/runtime-gameplay-visual-review-2.md"),
    ".allforai/game-frontend/qa/runtime-gameplay-visual-repair-loop-report.json",
    ".allforai/game-frontend/qa/runtime-gameplay-visual-acceptance-report.json",
    "Screenshot review is mandatory for visible gameplay acceptance",
    "must not pass from logs, DOM, canvas probes, or state deltas alone",
    "Gameplay Screenshot Plan",
    "before/after pairs",
    ("Codex CLI", "reviewer two"),
    "pull mode",
    ("Claude Code independently inspects the same runtime screenshots", "reviewer one independently inspects the same runtime screenshots"),
    "union of both reviews",
    "Repair And Revalidation Loop",
    "rerun the same affected gameplay screenshot tasks",
    "production_visual_binding",
    "prototype/placeholder rejection",
    "pure-color blocks",
    "black debug",
    "generic geometric",
    "engine-ready asset manifest",
    "wrong entrypoint",
    "prototype component",
    "missing asset loader mapping",
    "blocked_by_missing_screenshot",
    ("blocked_by_missing_codex_cli", "missing_cross_platform_cli"),
    "blocked_by_missing_visual_model_capability",
}



# ADR-0003 transition table: legacy reviewer-named vocabulary -> reviewer-neutral vocabulary.
# Every REQUIRED_* term whose neutral form differs is accepted in either form until the emitters
# migrate (#40); the contract step (#41) drops the legacy form. Longest keys first.
ADR3_NEUTRAL = {
    ".allforai/game-design/art/qa/codex-visual-review.json": ".allforai/game-design/art/qa/visual-review-2.json",
    ".allforai/game-design/art/qa/codex-visual-review.md": ".allforai/game-design/art/qa/visual-review-2.md",
    ".allforai/game-design/art/qa/claude-code-visual-review.json": ".allforai/game-design/art/qa/visual-review-1.json",
    ".allforai/game-design/art/qa/claude-code-visual-review.md": ".allforai/game-design/art/qa/visual-review-1.md",
    ".allforai/verify/codex-ui-visual-review.json": ".allforai/verify/visual-review-2.json",
    ".allforai/verify/codex-ui-visual-review.md": ".allforai/verify/visual-review-2.md",
    ".allforai/verify/claude-code-visual-review.json": ".allforai/verify/visual-review-1.json",
    ".allforai/verify/claude-code-visual-review.md": ".allforai/verify/visual-review-1.md",
    ".allforai/game-frontend/qa/codex-runtime-visual-review.json": ".allforai/game-frontend/qa/runtime-visual-review-2.json",
    ".allforai/game-frontend/qa/codex-runtime-visual-review.md": ".allforai/game-frontend/qa/runtime-visual-review-2.md",
    ".allforai/game-frontend/qa/codex-gameplay-visual-review.json": ".allforai/game-frontend/qa/runtime-gameplay-visual-review-2.json",
    ".allforai/game-frontend/qa/codex-gameplay-visual-review.md": ".allforai/game-frontend/qa/runtime-gameplay-visual-review-2.md",
    "blocked_by_missing_codex_cli": "missing_cross_platform_cli",
    "Codex CLI must inspect screenshots": "reviewer two must inspect screenshots",
    "Claude Code performs its own independent screenshot review": "reviewer one performs its own independent screenshot review",
    "Claude Code independently inspects the same runtime screenshots": "reviewer one independently inspects the same runtime screenshots",
    "must not read the Codex report first": "must not read the other reviewer's report first",
    "Claude Code Visual Review": "Reviewer One",
    "Claude Code closure audit": "closure audit",
    "Codex CLI": "reviewer two",
    "Claude Code": "reviewer one",
}


def neutral_form(term: str) -> str:
    for old, new in ADR3_NEUTRAL.items():
        term = term.replace(old, new)
    return term


def _has(text: str, term) -> bool:
    """`term` is a string or a tuple of accepted alternatives; matches raw or whitespace-flattened text."""
    alts = term if isinstance(term, tuple) else (term,)
    flat = " ".join(text.split())
    return any(alt in text or alt in flat for alt in alts)


def _key(term) -> str:
    return term[0] if isinstance(term, tuple) else term


def _with_neutral(terms):
    out = set()
    for t in terms:
        if isinstance(t, tuple):
            out.add(t)
        elif neutral_form(t) != t:
            out.add((t, neutral_form(t)))
        else:
            out.add(t)
    return out


REQUIRED_ARCH_QA_TERMS = _with_neutral(REQUIRED_ARCH_QA_TERMS)
REQUIRED_ASSEMBLY_TERMS = _with_neutral(REQUIRED_ASSEMBLY_TERMS)
REQUIRED_AUDIO_BINDING_TERMS = _with_neutral(REQUIRED_AUDIO_BINDING_TERMS)
REQUIRED_GAMEPLAY_BINDING_TERMS = _with_neutral(REQUIRED_GAMEPLAY_BINDING_TERMS)
REQUIRED_GAMEPLAY_VISUAL_ACCEPTANCE_TERMS = _with_neutral(REQUIRED_GAMEPLAY_VISUAL_ACCEPTANCE_TERMS)
REQUIRED_PARENT_TERMS = _with_neutral(REQUIRED_PARENT_TERMS)
REQUIRED_PERFORMANCE_TERMS = _with_neutral(REQUIRED_PERFORMANCE_TERMS)
REQUIRED_RUNTIME_ARCH_TERMS = _with_neutral(REQUIRED_RUNTIME_ARCH_TERMS)
REQUIRED_SMOKE_TERMS = _with_neutral(REQUIRED_SMOKE_TERMS)


def _read(path: Path) -> str:
    return path.read_text()


def _has_term(text: str, term) -> bool:
    """`term` is a string or a tuple of accepted alternatives (ADR-0003 transition: legacy
    reviewer-named form and reviewer-neutral form both accepted until #40 migrates emitters)."""
    alts = term if isinstance(term, tuple) else (term,)
    flat = " ".join(text.split())
    return any(alt in text or alt in flat for alt in alts)



def _canonical_refs(text: str) -> set[str]:
    pattern = re.compile(
        r"\$\{CLAUDE_PLUGIN_ROOT\}/skills/(game-frontend/[^\s`]+/SKILL\.md)"
    )
    return set(pattern.findall(text))


def validate_game_frontend_pipeline(repo_root: str) -> list[str]:
    root = Path(repo_root)
    skills_root = root / "claude/meta-skill/skills"
    frontend_root = skills_root / "game-frontend"
    frontend_pack = frontend_root / "PACK.md"
    runtime_arch = frontend_root / "10-design/runtime-architecture-design/SKILL.md"
    assembly = frontend_root / "30-generate/playable-client-assembly/SKILL.md"
    arch_qa = frontend_root / "40-qa/runtime-architecture-qa/SKILL.md"
    gameplay_visual_acceptance = frontend_root / "40-qa/runtime-gameplay-visual-acceptance/SKILL.md"
    runtime_debug_bridge = frontend_root / "20-spec/runtime-debug-bridge-contract/SKILL.md"
    audio_binding = frontend_root / "20-spec/audio-binding-spec/SKILL.md"
    gameplay_binding = frontend_root / "20-spec/gameplay-system-binding-spec/SKILL.md"
    smoke_test = frontend_root / "40-qa/playable-smoke-test/SKILL.md"
    performance_spec = frontend_root / "20-spec/performance-budget-spec/SKILL.md"
    performance_qa = frontend_root / "40-qa/frontend-performance-budget-qa/SKILL.md"

    errors: list[str] = []
    for path in [
        frontend_pack,
        runtime_arch,
        assembly,
        arch_qa,
        gameplay_visual_acceptance,
        runtime_debug_bridge,
        audio_binding,
        gameplay_binding,
        smoke_test,
        performance_spec,
        performance_qa,
    ]:
        if not path.exists():
            errors.append(f"{path}: required game-frontend pipeline file missing")
    if errors:
        return errors

    parent_text = _read(frontend_pack)
    runtime_arch_text = _read(runtime_arch)
    assembly_text = _read(assembly)
    arch_qa_text = _read(arch_qa)
    gameplay_visual_acceptance_text = _read(gameplay_visual_acceptance)
    audio_binding_text = _read(audio_binding)
    gameplay_binding_text = _read(gameplay_binding)
    smoke_test_text = _read(smoke_test)
    performance_spec_text = _read(performance_spec)
    performance_qa_text = _read(performance_qa)
    listed_refs = _canonical_refs(parent_text)

    for skill_file in sorted(frontend_root.rglob("SKILL.md")):
        if skill_file == frontend_pack:
            continue
        ref = skill_file.relative_to(skills_root).as_posix()
        if ref not in listed_refs:
            errors.append(f"game-frontend/PACK.md: missing canonical child path skills/{ref}")

    for term in sorted(REQUIRED_PARENT_TERMS, key=_key):
        if not _has(parent_text, term):
            errors.append(f"game-frontend/PACK.md: missing frontend architecture term {_key(term)}")
    for term in sorted(REQUIRED_ASSEMBLY_TERMS, key=_key):
        if not _has(assembly_text, term):
            errors.append(f"playable-client-assembly: missing required input term {_key(term)}")
    for term in sorted(REQUIRED_ARCH_QA_TERMS, key=_key):
        if not _has(arch_qa_text, term):
            errors.append(f"runtime-architecture-qa: missing graph closure term {_key(term)}")
    for term in sorted(REQUIRED_RUNTIME_ARCH_TERMS, key=_key):
        if not _has(runtime_arch_text, term):
            errors.append(f"runtime-architecture-design: missing specialization term {_key(term)}")
    for term in sorted(REQUIRED_GAMEPLAY_VISUAL_ACCEPTANCE_TERMS, key=_key):
        if not _has(gameplay_visual_acceptance_text, term):
            errors.append(f"runtime-gameplay-visual-acceptance: missing gameplay visual term {_key(term)}")
    for term in sorted(REQUIRED_AUDIO_BINDING_TERMS, key=_key):
        if not _has(audio_binding_text, term):
            errors.append(f"audio-binding-spec: missing Canvas2D audio runtime term {_key(term)}")
    for term in sorted(REQUIRED_GAMEPLAY_BINDING_TERMS, key=_key):
        if not _has(gameplay_binding_text, term):
            errors.append(f"gameplay-system-binding-spec: missing game rule constraint term {_key(term)}")
    for term in sorted(REQUIRED_SMOKE_TERMS, key=_key):
        if not _has(smoke_test_text, term):
            errors.append(f"playable-smoke-test: missing Canvas2D smoke term {_key(term)}")
    for term in sorted(REQUIRED_PERFORMANCE_TERMS, key=_key):
        if not _has_term(performance_spec_text, term) and not _has_term(performance_qa_text, term):
            errors.append(f"performance Canvas2D DPR term missing {_key(term)}")

    return errors


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo_root", nargs="?", default=".")
    args = parser.parse_args(argv)
    errors = validate_game_frontend_pipeline(args.repo_root)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
