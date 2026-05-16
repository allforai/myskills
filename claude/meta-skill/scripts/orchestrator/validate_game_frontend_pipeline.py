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
    ".allforai/game-frontend/qa/codex-gameplay-visual-review.json",
    ".allforai/game-frontend/qa/codex-gameplay-visual-review.md",
    ".allforai/game-frontend/qa/runtime-gameplay-visual-repair-loop-report.json",
    ".allforai/game-frontend/qa/runtime-gameplay-visual-acceptance-report.json",
    "Screenshot review is mandatory for visible gameplay acceptance",
    "must not pass from logs, DOM, canvas probes, or state deltas alone",
    "Gameplay Screenshot Plan",
    "before/after pairs",
    "Codex CLI",
    "pull mode",
    "Claude Code must not re-score visual quality",
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
    "blocked_by_missing_codex_cli",
    "blocked_by_missing_visual_model_capability",
}


def _read(path: Path) -> str:
    return path.read_text()


def _has_term(text: str, term: str) -> bool:
    return term in text or term in " ".join(text.split())


def _canonical_refs(text: str) -> set[str]:
    pattern = re.compile(
        r"\$\{CLAUDE_PLUGIN_ROOT\}/skills/(game-frontend/[^\s`]+/SKILL\.md)"
    )
    return set(pattern.findall(text))


def validate_game_frontend_pipeline(repo_root: str) -> list[str]:
    root = Path(repo_root)
    skills_root = root / "claude/meta-skill/skills"
    frontend_root = skills_root / "game-frontend"
    frontend_pack = frontend_root / "SKILL.md"
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
            errors.append(f"game-frontend/SKILL.md: missing canonical child path skills/{ref}")

    for term in sorted(REQUIRED_PARENT_TERMS):
        if not _has_term(parent_text, term):
            errors.append(f"game-frontend/SKILL.md: missing frontend architecture term {term}")
    for term in sorted(REQUIRED_ASSEMBLY_TERMS):
        if not _has_term(assembly_text, term):
            errors.append(f"playable-client-assembly: missing required input term {term}")
    for term in sorted(REQUIRED_ARCH_QA_TERMS):
        if not _has_term(arch_qa_text, term):
            errors.append(f"runtime-architecture-qa: missing graph closure term {term}")
    for term in sorted(REQUIRED_RUNTIME_ARCH_TERMS):
        if not _has_term(runtime_arch_text, term):
            errors.append(f"runtime-architecture-design: missing specialization term {term}")
    for term in sorted(REQUIRED_GAMEPLAY_VISUAL_ACCEPTANCE_TERMS):
        if not _has_term(gameplay_visual_acceptance_text, term):
            errors.append(f"runtime-gameplay-visual-acceptance: missing gameplay visual term {term}")
    for term in sorted(REQUIRED_AUDIO_BINDING_TERMS):
        if not _has_term(audio_binding_text, term):
            errors.append(f"audio-binding-spec: missing Canvas2D audio runtime term {term}")
    for term in sorted(REQUIRED_GAMEPLAY_BINDING_TERMS):
        if not _has_term(gameplay_binding_text, term):
            errors.append(f"gameplay-system-binding-spec: missing game rule constraint term {term}")
    for term in sorted(REQUIRED_SMOKE_TERMS):
        if not _has_term(smoke_test_text, term):
            errors.append(f"playable-smoke-test: missing Canvas2D smoke term {term}")
    for term in sorted(REQUIRED_PERFORMANCE_TERMS):
        if not _has_term(performance_spec_text, term) and not _has_term(performance_qa_text, term):
            errors.append(f"performance Canvas2D DPR term missing {term}")

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
