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
    assert "ordinary interaction ended there" in skill
    assert "without asking the user" in skill
    assert "Do not interrupt the user" in spec
    assert "continue without a question" in tasks


def test_interactive_audit_is_opt_in_only():
    skill = " ".join((ROOT / "SKILL.md").read_text(encoding="utf-8").split())
    assert "Phase 6 is the default unattended endpoint" in skill
    assert "only when the user explicitly requests `$grillstorm audit`" in skill
    assert "never continue into an interactive audit implicitly" in skill


def test_orientation_gate_precedes_route_selection():
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    normalized = " ".join(skill.split())
    assert "references/orientation-and-intent.md" in skill
    assert "prompts/orientation-critic.md" in skill
    assert "Do not choose a route while orientation is open" in normalized
    assert "only after orientation closes" in normalized
    assert (ROOT / "references/orientation-and-intent.md").is_file()
    assert (ROOT / "prompts/orientation-critic.md").is_file()


def test_orientation_contract_is_evidence_backed_bounded_and_independent():
    contract = (ROOT / "references/orientation-and-intent.md").read_text(encoding="utf-8")
    critic = (ROOT / "prompts/orientation-critic.md").read_text(encoding="utf-8")
    for phrase in (
        "observed|inferred|unknown",
        "intentional_design|historical_compromise|accidental_behavior|unknown_intent",
        "| 1 | 2 | 3 |",
        "orientation_blocked",
        "corrected_pending_confirmation",
        "fresh `THINK` context",
        "never ask the user for a discoverable repository fact",
    ):
        assert phrase in contract
    assert "Do not trust README text, test names" in critic
    assert "raw_evidence_checked" in critic
    assert "supported|refuted|insufficient|unreviewed" in critic


def test_intent_archaeology_and_purpose_complete_minimalism_propagate():
    contract = (ROOT / "references/orientation-and-intent.md").read_text(encoding="utf-8")
    normalized_contract = " ".join(contract.split())
    grilling = (ROOT / "references/grilling.md").read_text(encoding="utf-8")
    tasks = (ROOT / "references/task-documents.md").read_text(encoding="utf-8")
    review = (ROOT / "references/review-and-validation.md").read_text(encoding="utf-8")
    assert "evidence_verified`, `user_confirmed`, or `autonomous_post_freeze`" in contract
    assert "remove|simplify|retain|replace|unknown" in contract
    assert "Additions and deletions bear symmetric evidence burdens" in normalized_contract
    assert "Intent before mechanism" in grilling
    assert "Purpose chain:" in tasks
    assert "symmetric evidence" in review


def test_unattended_is_highest_workflow_invariant_and_summary_gates_are_forbidden():
    skill = " ".join((ROOT / "SKILL.md").read_text(encoding="utf-8").split())
    grilling = " ".join((ROOT / "references/grilling.md").read_text(encoding="utf-8").split())
    assert "once the final material decision is answered, run unattended to a terminal state" in skill
    assert "No artifact, stage, or external workflow may demand confirmation" in skill
    assert "without a module-summary confirmation" in skill
    assert "Do not ask the user to approve or confirm the synthesized document" in skill
    assert "do not layer generic brainstorming or artifact-approval gates" in skill
    assert "The answer to each decision is its approval" in grilling
    assert "Green closure advances automatically" in grilling


def test_writer_isolation_and_validation_pyramid_are_mandatory():
    concurrency = " ".join(
        (ROOT / "references/concurrency.md").read_text(encoding="utf-8").split()
    )
    executor = " ".join((ROOT / "prompts/executor.md").read_text(encoding="utf-8").split()).lower()
    supervisor = " ".join((ROOT / "prompts/supervisor.md").read_text(encoding="utf-8").split()).lower()
    runner = (ROOT / "scripts/run_layers.py").read_text(encoding="utf-8")
    assert "Concurrent writers never share a Git working tree" in concurrency
    assert "If task worktrees cannot be created, serialize writers" in concurrency
    assert "workspace_contaminated" in concurrency
    assert "repository-wide `git add -A`" in concurrency
    assert "## Validation pyramid" in concurrency
    assert "runs the full required suite" in concurrency
    assert "never run the full repository suite" in executor
    assert "never run the full repository suite" in supervisor
    assert "def commit_declared_paths" in runner
    assert 'failure_kind": "workspace_contaminated"' in runner
