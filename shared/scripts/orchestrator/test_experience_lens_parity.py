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


# The post-hoc review prose below has no executable behaviour; these literals are its only guard.
# Every twin pair carries the same literals, so a one-sided edit fails as loudly as a deletion.
CROSS_EXAMS = [ROOT / "claude/superstorm/skills/cross-exam/SKILL.md",
               ROOT / "codex/cross-exam-skill/SKILL.md"]
CROSS_EXAM_LENSES = [ROOT / "claude/superstorm/knowledge/cross-exam/lenses.md",
                     ROOT / "codex/cross-exam-skill/lenses.md"]


def line_with(path, marker):
    matches = [line for line in read(path).splitlines() if marker in line]
    assert len(matches) == 1, f"{path.relative_to(ROOT)} has {len(matches)} lines with {marker}"
    return matches[0]


def section(path, heading):
    text = read(path)
    assert heading in text, f"{path.relative_to(ROOT)} lost the heading {heading}"
    body = text.split(heading, 1)[1]
    return body.split("\n## ", 1)[0]


@pytest.mark.parametrize("path", REVIEWS, ids=lambda p: str(p.relative_to(ROOT)))
def test_review_prior_evidence_rule_names_the_runtime_review(path):
    rule = line_with(path, "**Prior evidence — runtime experience review.**")
    for term in ("`docs/experience-review/runtime.md`", "Do not read `design.md`",
                 "by the id it carries in that file"):
        assert term in rule, f"{path.relative_to(ROOT)} prior-evidence rule lost {term}"


@pytest.mark.parametrize("path", REVIEWS, ids=lambda p: str(p.relative_to(ROOT)))
def test_review_lens_table_carries_the_audience_leak_row(path):
    row = line_with(path, "| 4 商业级够不够 · 受众泄漏 |")
    for term in ("部署方/开发者才该碰的配置", "服务地址", "访问凭证",
                 "`end-user` / `operator` / `developer`", "Pattern J"):
        assert term in row, f"{path.relative_to(ROOT)} audience-leak row lost {term}"


@pytest.mark.parametrize("path", CROSS_EXAMS, ids=lambda p: str(p.relative_to(ROOT)))
def test_cross_exam_journey_intake_reads_the_experience_direction(path):
    intake = section(path, "## 1b. 旅程采集")
    for term in ("`.allforai/product-concept/product-concept.json`",
                 '`topic == "experience-direction"`', '`status == "confirmed"`',
                 "`auto_decided: true`", "（此方向由模型受托选定）"):
        assert term in intake, f"{path.relative_to(ROOT)} section 1b lost {term}"


@pytest.mark.parametrize("path", CROSS_EXAM_LENSES, ids=lambda p: str(p.relative_to(ROOT)))
def test_cross_exam_lenses_carry_the_audience_leak_point(path):
    row = line_with(path, "最终用户界面里出现部署方/开发者才该碰的配置")
    for term in ("服务地址", "访问凭证", "这一项是给谁填的"):
        assert term in row, f"{path.relative_to(ROOT)} audience-leak point lost {term}"
