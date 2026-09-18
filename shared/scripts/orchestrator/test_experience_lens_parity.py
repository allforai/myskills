"""Hold the five experience lenses to one vocabulary across the runtime gate and both reviews."""
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]
LENSES = {"onboarding": "引导", "process_feedback": "过程反馈", "next_step": "下一步",
          "state_consistency": "状态一致", "return_reason": "回来理由"}
GATE = ROOT / "claude/meta-skill/skills/app-design/40-qa/experience-quality-critique/SKILL.md"
REVIEWS = [ROOT / "claude/superstorm/skills/product-review/SKILL.md",
           ROOT / "codex/cross-exam-skill/product-review.md"]


def read(path):
    assert path.exists(), f"{path.relative_to(ROOT)} is missing"
    return path.read_text(encoding="utf-8")


@pytest.mark.parametrize("path", [GATE, *REVIEWS], ids=lambda p: str(p.relative_to(ROOT)))
def test_gate_and_both_reviews_name_every_lens(path):
    text = read(path)
    for identifier in LENSES:
        assert f"`{identifier}`" in text, f"{path.relative_to(ROOT)} does not name `{identifier}`"


@pytest.mark.parametrize("path", REVIEWS, ids=lambda p: str(p.relative_to(ROOT)))
def test_reviews_pair_each_identifier_with_its_lens(path):
    text = read(path)
    for identifier, lens in LENSES.items():
        assert f"{lens} = `{identifier}`" in text, (
            f"{path.relative_to(ROOT)} does not pair {lens} with `{identifier}`"
        )


def test_review_twins_carry_the_same_mapping_line():
    lines = []
    for path in REVIEWS:
        matches = [line for line in read(path).splitlines() if "`onboarding`" in line]
        assert len(matches) == 1, f"{path.relative_to(ROOT)} has {len(matches)} `onboarding` lines"
        lines.append(matches[0])
    assert lines[0] == lines[1], "the product-review twins carry different mapping lines"
