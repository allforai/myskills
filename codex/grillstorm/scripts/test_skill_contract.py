from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_skill_requires_explicit_command_invocation():
    # Codex only recognises the Agent Skills frontmatter keys; the Claude-only
    # disable-model-invocation key makes its validator warn and does nothing here.
    # Explicit-only invocation on Codex is agents/openai.yaml policy.allow_implicit_invocation.
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    frontmatter = skill.split("---", 2)[1]
    assert "disable-model-invocation" not in frontmatter
    assert "Use only when the user explicitly invokes $grillstorm" in frontmatter
    manifest = (ROOT / "agents/openai.yaml").read_text(encoding="utf-8")
    assert "allow_implicit_invocation: false" in manifest


def test_upstream_grilling_frontier_rounds_and_diagnostic_redaction_are_preserved():
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    grilling = (ROOT / "references/grilling.md").read_text(encoding="utf-8")
    official = (ROOT / "references/official-skills.md").read_text(encoding="utf-8")
    diagnosis = (ROOT / "references/implementation-and-diagnosis.md").read_text(
        encoding="utf-8"
    )
    notices = (ROOT / "references/third-party-notices.md").read_text(encoding="utf-8")
    assert "every currently independent decision in one numbered frontier round" in skill
    assert "This is not a second grilling protocol" in grilling
    assert "load official `grill-with-docs`" in grilling
    assert "Never invoke official `implement`" in official
    assert "do not load `grilling`, `grill-me`, `grill-with-docs`" in official
    assert "Install them now? Recommended: **yes**" in official
    assert "scripts/install_official_skills.py" in official
    assert "redact API keys, tokens, passwords, cookies, session IDs" in diagnosis
    assert "Keep credentials\nin environment variables" in diagnosis
    assert "0ab1b63a410a03d3627979a109c8695de27af954" in notices


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
        "references/official-skills.md",
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
    official = (ROOT / "references/official-skills.md").read_text(encoding="utf-8")
    tasks = (ROOT / "references/task-documents.md").read_text(encoding="utf-8")
    review = (ROOT / "references/review-and-validation.md").read_text(encoding="utf-8")
    assert "evidence_verified`, `user_confirmed`, or `autonomous_post_freeze`" in contract
    assert "remove|simplify|retain|replace|unknown" in contract
    assert "Additions and deletions bear symmetric evidence burdens" in normalized_contract
    assert "intent before mechanism" in official
    assert "Purpose chain:" in tasks
    assert "symmetric evidence" in review


def test_unattended_is_highest_workflow_invariant_and_summary_gates_are_forbidden():
    skill = " ".join((ROOT / "SKILL.md").read_text(encoding="utf-8").split())
    official = " ".join(
        (ROOT / "references/official-skills.md").read_text(encoding="utf-8").split()
    )
    assert "Official design skills may ask" in skill
    assert "run unattended to a terminal state" in skill
    assert "Execution may not reopen grilling" in skill
    assert "Never invoke official `implement`" in skill
    assert "Do not ask for a redundant start approval" in skill
    assert "Official design skills may ask" in official
    assert "Never invoke official `implement`" in official


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


def test_method_files_are_official_adapters_not_second_protocols():
    grilling = (ROOT / "references/grilling.md").read_text(encoding="utf-8")
    domain = (ROOT / "references/domain-modeling.md").read_text(encoding="utf-8")
    setup = (ROOT / "references/project-setup.md").read_text(encoding="utf-8")
    supporting = (ROOT / "references/supporting-disciplines.md").read_text(encoding="utf-8")
    tdd = (ROOT / "references/implementation-and-diagnosis.md").read_text(encoding="utf-8")
    review = (ROOT / "references/review-and-validation.md").read_text(encoding="utf-8")
    assert "This is not a second grilling protocol" in grilling
    assert "❓ **Q1**" not in grilling
    assert "Load official `domain-modeling`" in domain
    assert "_Avoid_: Purchase, transaction" not in domain
    assert "Load official `setup-matt-pocock-skills`" in setup
    assert "Ask one section at a time with a recommended answer." not in setup
    assert "Load the matching official skill" in supporting
    assert "Prefer fewer methods and parameters" not in supporting
    assert "Load official `tdd`" in tdd
    assert "Write one focused test at the approved seam." not in tdd
    assert "Load official `code-review`" in review
    assert "mysterious names and duplicated logic" not in review


def test_execution_workers_load_official_tdd_and_code_review():
    executor = (ROOT / "prompts/executor.md").read_text(encoding="utf-8")
    supervisor = (ROOT / "prompts/supervisor.md").read_text(encoding="utf-8")
    concurrency = (ROOT / "references/concurrency.md").read_text(encoding="utf-8")
    execution = (ROOT / "references/execution.md").read_text(encoding="utf-8")
    assert "Load official `tdd`" in executor
    assert "Never load official `implement`" in executor
    assert "official `code-review`" in supervisor
    assert "Never load official `implement`" in supervisor
    assert "official `tdd`" in concurrency
    assert "official `code-review`" in concurrency
    assert "official `implement`" in execution
