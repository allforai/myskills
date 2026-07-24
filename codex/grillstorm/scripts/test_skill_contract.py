from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_post_launch_unforeseen_choices_do_not_pause():
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    normalized = " ".join(skill.split())
    required = (
        "Never pause merely because",
        "inside the launch authority",
        "record its outcome",
        "transitively skip only its dependents",
        "continue every independent authorized branch",
    )
    for phrase in required:
        assert phrase in normalized


def test_handoff_cannot_replace_branch_local_deferral():
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    normalized = " ".join(skill.split())
    assert "Do not use handoff merely because one branch is blocked" in normalized
    assert "explicit user request" in normalized
    assert "all further safe progress impossible" in normalized


def test_progressive_disclosure_references_are_routed():
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    required = (
        "references/upstream-flow.md",
        "references/project-setup.md",
        "references/routing.md",
        "references/spec-closure-and-abstraction.md",
        "references/task-documents.md",
        "references/execution.md",
        "references/post-delivery-probing.md",
    )
    for phrase in required:
        assert phrase in skill
        assert (ROOT / phrase).is_file()
