from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative_path):
    return " ".join((ROOT / relative_path).read_text(encoding="utf-8").split())


def test_reference_states_the_expansion_table():
    doc = read("references/failure-proportionality.md")
    for phrase in (
        "| `routine` | `guard-only` | `full` |",
        "| `rare` | `none` | `guard-only` |",
        "`expansion` is looked up, never chosen",
    ):
        assert phrase in doc


def test_reference_states_the_three_locks():
    doc = read("references/failure-proportionality.md")
    for phrase in (
        "Frequency never rewrites damage",
        "does not convert `durable` into `reenterable`",
        "A missing, unlisted, or unevidenced basis falls back to `routine`",
        "Missing or placeholder `reentry_proof` falls back to `durable`",
        "`damage: unknown` counts as `durable`",
    ):
        assert phrase in doc


def test_reference_redefines_lens_closure_as_classified():
    doc = read("references/failure-proportionality.md")
    assert (
        "A lens counts as applied to an outcome when every mode is classified, "
        "not when every mode is designed" in doc
    )


def test_reference_gives_ordering_without_a_skip_permission():
    doc = read("references/failure-proportionality.md")
    assert "No lens outside exceptional behavior gains a skip permission" in doc
    assert "Ordering defers expansion, never examination" in doc


def test_reference_names_the_validator():
    doc = read("references/failure-proportionality.md")
    assert "scripts/validate_failure_classification.py" in doc
    assert "A failing run blocks the closure gate" in doc


def test_skill_routes_the_new_reference():
    skill = read("SKILL.md")
    assert "references/failure-proportionality.md" in skill


REVERSE_GRILLS = ("prompts/spec-reverse-grill.md", "prompts/task-reverse-grill.md")


def test_reverse_grills_classify_before_expanding():
    for path in REVERSE_GRILLS:
        prompt = read(path)
        assert "references/failure-proportionality.md" in prompt
        assert "Classify each mode" in prompt
        assert "before expanding it" in prompt


def test_reverse_grills_suppress_modes_that_resolve_to_none():
    for path in REVERSE_GRILLS:
        prompt = read(path)
        assert (
            "Emit an issue only for modes whose table result is `full` or `guard-only`"
            in prompt
        )
        assert "Modes resolving to `none` are recorded as classification records, not issues" in prompt


def test_reverse_grills_emit_classification_records():
    for path in REVERSE_GRILLS:
        prompt = read(path)
        assert '"failure_classification": [' in prompt
        assert '"damage": "reenterable|durable|unknown"' in prompt
        assert '"frequency": "routine|rare"' in prompt
        assert '"expansion": "full|guard-only|none"' in prompt


def test_reverse_grill_issues_carry_blast_radius():
    for path in REVERSE_GRILLS:
        assert '"blast_radius": "contract|module|local"' in read(path)


def test_reverse_grills_close_on_classified_not_designed():
    for path in REVERSE_GRILLS:
        assert (
            "A lens is applied when every mode is classified, not when every mode is designed"
            in read(path)
        )


CLOSURE_CRITICS = ("prompts/spec-closure-critic.md", "prompts/task-closure-critic.md")


def test_closure_critics_accept_the_expansion_table():
    for path in CLOSURE_CRITICS:
        prompt = read(path)
        assert "references/failure-proportionality.md" in prompt
        assert (
            "Accept `expansion: none` and a proved `guard-only` as closed" in prompt
        )
        assert "Do not demand per-mode treatment of a mode the table exempts" in prompt


def test_closure_critics_may_still_challenge_the_classification():
    for path in CLOSURE_CRITICS:
        prompt = read(path)
        for phrase in (
            "`durable` damage recorded as `reenterable`",
            "`rare` without an admissible evidenced basis",
            "placeholder `reentry_proof`",
            "a `guard-only` defense with no proof it holds",
        ):
            assert phrase in prompt


def test_spec_closure_gate_scopes_the_failure_block_to_expanded_modes():
    doc = read("references/spec-closure-and-abstraction.md")
    assert (
        "failure/degraded/rollback behavior that cannot return to a safe state, for every mode "
        "whose `references/failure-proportionality.md` result is `full` or `guard-only`" in doc
    )


def test_spec_exit_gate_requires_the_validator():
    doc = read("references/spec-closure-and-abstraction.md")
    assert (
        "every failure mode is classified and "
        "`scripts/validate_failure_classification.py` passes" in doc
    )


def test_task_closure_applies_the_expansion_table():
    doc = read("references/task-documents.md")
    assert "references/failure-proportionality.md" in doc
    assert "classify each mode, expand only per the table" in doc
    assert (
        "validate `reviews/failure-classification.json` before ticket publication" in doc
    )
