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


def test_design_reviews_have_a_hard_cap_and_named_blocked_states():
    # Guard: the hard cap (anti-thrash) and the two blocked terminal states. The per-layer
    # minimum-round figures are scaffolding and are deliberately not pinned here.
    contract = (ROOT / "references/review-budgets.md").read_text(encoding="utf-8")
    assert "No design-review layer may set a hard limit above 6" in contract
    assert "blocked_unrepaired" in contract
    assert "budget_exhausted_blocked" in contract
    assert "consumes the round and cannot establish closure" in " ".join(contract.split())


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
    # Guards only: evidence classes, intent classes, independent critic context, and "never ask
    # for a discoverable fact". The round budget and the round-3 outcome are scaffolding.
    for phrase in (
        "observed|inferred|unknown",
        "intentional_design|historical_compromise|accidental_behavior|unknown_intent",
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


# ---------------------------------------------------------------------------------------------
# Guard table. A guard constrains information flow or motive and holds regardless of model
# strength; removing one must fail CI. Method text (tiers, counts, templates, rhythm) is not
# pinned anywhere in this file. Any one anchor matching in the named files satisfies a guard.
# ---------------------------------------------------------------------------------------------
import re

GUARDS = {
    "VERIFY never receives executor narrative": (
        ["references/model-policy.md", "prompts/supervisor.md"],
        [r"never receive executor narrative", r"Do not equate model identity with independence"],
        "Expectation isolation: a verifier that reads the claim is anchored by it.",
    ),
    "zero executed tests is not a pass": (
        ["prompts/supervisor.md", "prompts/executor.md"],
        [r"Executed 0 tests", r"ran 0 tests", r"non-zero executed-test count"],
        "Evidence gate: a selector that matched nothing exits 0 and proves nothing.",
    ),
    "failed critic consumes the round": (
        ["references/review-budgets.md"],
        [r"consumes the round and cannot establish closure"],
        "Defective returns are discarded whole; a retry is a new fresh context, not a patch.",
    ),
    "frequency never rewrites damage": (
        ["references/failure-proportionality.md"],
        [r"Frequency never rewrites damage"],
        "Anti-rationalisation: 'rarely happens' must not downgrade what the failure destroys.",
    ),
    "no default, empty, stale, or mock result as success": (
        ["references/execution.md", "prompts/executor.md", "prompts/supervisor.md"],
        [r"default/empty/stale/mock", r"default/empty value"],
        "Motive gate: a fallback turns a failure into a fake success.",
    ),
    "environmental failure is a reality gate, not permission to guess": (
        ["references/execution.md", "references/concurrency.md"],
        [r"not permission to guess", r"reality gate"],
        "Honesty gate: proof pending is neither verified nor failed.",
    ),
    "portable completion is the confirmed commit marker": (
        ["references/concurrency.md", "references/handoff.md"],
        [r"grillstorm-confirmed:"],
        "Evidence gate: a handoff file or transcript is not completion; a reachable marker is.",
    ),
    "locked or unknown model source forces inherited": (
        ["references/model-policy.md"],
        [r"locked or unknown source -> `inherited`", r"Otherwise use `inherited`"],
        "Never override a host-owned model selection silently, whatever names are in play.",
    ),
    "zero findings valid only with full supported coverage": (
        ["prompts/orientation-critic.md"],
        [r"Zero findings is valid only when"],
        "Zero hits are a question, not a conclusion.",
    ),
    "concurrent writers never share a working tree": (
        ["references/concurrency.md"],
        [r"Concurrent writers never share a Git working tree"],
        "Concurrency isolation: prompt-level promises are not isolation.",
    ),
    "controller owns the global validation gate": (
        ["references/concurrency.md", "prompts/executor.md", "prompts/supervisor.md"],
        [r"runs the full required suite", r"never run the full repository suite"],
        "Gate ownership: N workers each running the whole suite is neither isolation nor proof.",
    ),
    "credentials never enter Git or trackers": (
        ["references/handoff.md", "references/implementation-and-diagnosis.md"],
        [r"redact API keys", r"Keep credentials"],
        "Safety.",
    ),
    "no permission is not permission": (
        ["SKILL.md", "references/execution.md"],
        [r"not permission to guess", r"non-changing evidence", r"reality-gate runbook"],
        "Safety: without authority, collect evidence and write the runbook; never push or deploy.",
    ),
}


def test_every_guard_is_present():
    missing = []
    for name, (files, anchors, why) in GUARDS.items():
        text = "\n".join((ROOT / f).read_text(encoding="utf-8") for f in files)
        if not any(re.search(a, text, flags=re.IGNORECASE | re.DOTALL) for a in anchors):
            missing.append(f"{name}: files={files} why={why}")
    assert not missing, "guards removed from the skill text:\n" + "\n".join(missing)
