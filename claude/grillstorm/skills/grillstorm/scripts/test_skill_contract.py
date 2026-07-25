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


def test_design_reviews_are_bounded_and_never_exceed_six():
    contract = (ROOT / "references/review-budgets.md").read_text(encoding="utf-8")
    assert "| Specification design | 3 | 5 | 6 |" in contract
    assert "| Task design | 2 | 3 | 5 |" in contract
    assert "| Workflow/DAG design | 2 | 3 | 4 |" in contract
    assert "No design-review layer may set a hard limit above 6" in contract
    assert "blocked_unrepaired" in contract
    assert "budget_exhausted_blocked" in contract


def test_no_redundant_start_or_task_breakdown_approval():
    skill = " ".join((ROOT / "SKILL.md").read_text(encoding="utf-8").split())
    tasks = " ".join(
        (ROOT / "references/task-documents.md").read_text(encoding="utf-8").split()
    )
    assert "Do not ask for a redundant start approval" in skill
    assert "launched without another question" in skill
    assert "Do not request a separate task-list, start, or publication approval" in tasks
    assert "After the user approves the breakdown" not in tasks


def test_post_design_decisions_are_autonomous():
    skill = " ".join((ROOT / "SKILL.md").read_text(encoding="utf-8").split())
    spec = " ".join(
        (ROOT / "references/spec-closure-and-abstraction.md").read_text(encoding="utf-8").split()
    )
    tasks = " ".join(
        (ROOT / "references/task-documents.md").read_text(encoding="utf-8").split()
    )
    assert "This is the end of ordinary interaction" in skill
    assert "without asking the user" in skill
    assert "Do not interrupt the user" in spec
    assert "continue without a question" in tasks


def test_interactive_audit_is_opt_in_only():
    skill = " ".join((ROOT / "SKILL.md").read_text(encoding="utf-8").split())
    assert "Phase 6 is the default unattended endpoint" in skill
    assert "only when the user explicitly requests `$grillstorm audit`" in skill
    assert "never continue into an interactive audit implicitly" in skill
