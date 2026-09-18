"""Contract tests for the landed `experience-quality-critique` skill.

These read the real files in the checkout, not a fixture: the point is that the
vocabulary M6 greps for and the report shape downstream nodes parse are present
in the shipped SKILL.md, not merely expressible.
"""

import json
import re
from pathlib import Path

from ..module_isolation import load

validate_app_experience_pipeline = load(
    "validate_app_experience_pipeline"
).validate_app_experience_pipeline

REPO = Path(__file__).resolve().parents[4]
CRITIQUE = (
    REPO
    / "claude/meta-skill/skills/app-design/40-qa/experience-quality-critique/SKILL.md"
)

LENS_ORDER = (
    "onboarding",
    "process_feedback",
    "next_step",
    "state_consistency",
    "return_reason",
    "mainline",
    "direction_fidelity",
    "audience_leak",
)
GATE_KEYS = {
    "must_fix_before_implementation",
    "must_fix_before_release",
    "recommended_iterations",
}
REVIEW_DOC_HEADINGS = ("## 结论", "## Must-fix", "## 各镜头观察", "## 证据限制")
VERDICT_ENTRIES = ("cross-exam", "product-review")
JSON_BLOCK_RE = re.compile(r"```json\n(.*?)\n```", re.DOTALL)


def _text() -> str:
    return CRITIQUE.read_text(encoding="utf-8")


def _section(text: str, heading: str) -> str:
    start = text.index(heading) + len(heading)
    rest = text[start:]
    end = rest.find("\n## ")
    return rest if end == -1 else rest[:end]


def _json_blocks(text: str) -> list:
    return [json.loads(block) for block in JSON_BLOCK_RE.findall(text)]


def _string_fields(payload, key=""):
    if isinstance(payload, dict):
        for name, value in payload.items():
            yield from _string_fields(value, name)
    elif isinstance(payload, list):
        for item in payload:
            yield from _string_fields(item, key)
    elif isinstance(payload, str):
        yield key, payload


def test_app_experience_pipeline_wiring_is_complete_apart_from_the_bootstrap_corpus():
    """PACK lists the child and both files carry every pinned term.

    The bootstrap corpus is wired by a later task, so its one error is filtered.
    """
    errors = [
        error
        for error in validate_app_experience_pipeline(str(REPO))
        if not error.startswith("bootstrap corpus:")
    ]

    assert errors == []


def test_lenses_section_declares_the_eight_identifiers_in_registry_order():
    section = _section(_text(), "\n## Lenses\n")

    positions = []
    for lens in LENS_ORDER:
        token = f"`{lens}`"
        assert token in section, f"{lens} is not inline code in the Lenses section"
        positions.append(section.index(token))

    assert positions == sorted(positions), dict(zip(LENS_ORDER, positions))


def test_report_and_invocation_contracts_are_machine_readable():
    blocks = _json_blocks(_text())
    assert blocks, "SKILL.md has no json fenced block"

    reports = [block for block in blocks if isinstance(block, dict) and "gates" in block]
    assert len(reports) == 1
    report = reports[0]
    assert set(report["gates"]) == GATE_KEYS
    assert set(report["findings"][0]["observation"]) == {
        "who",
        "circumstance",
        "task",
        "observed",
    }
    assert report["experience_gaps"] == []

    invocations = [
        block
        for block in blocks
        if isinstance(block, dict)
        and block.get("skill") == "app-design/experience-quality-critique"
    ]
    assert invocations, "no Invocation Contract block names this skill"
    invocation = invocations[0]
    assert invocation["mode"] in {"design", "runtime"}
    assert invocation["output_root"] == ".allforai/app-design/qa"
    assert all(
        path.startswith(".allforai/") for path in invocation["input_paths"].values()
    )


def test_review_doc_contract_names_its_root_and_fixed_headings_in_order():
    text = _text()

    assert "docs/experience-review/" in text
    positions = []
    for heading in REVIEW_DOC_HEADINGS:
        assert heading in text, heading
        positions.append(text.index(heading))

    assert positions == sorted(positions), dict(zip(REVIEW_DOC_HEADINGS, positions))


def test_no_post_run_verdict_entry_is_named_as_a_skill_or_node_id():
    for block in _json_blocks(_text()):
        for key, value in _string_fields(block):
            if key.endswith("skill") or key.endswith("node_id") or key == "capability":
                for entry in VERDICT_ENTRIES:
                    assert entry not in value, f"{key} names the post-run {entry}"
