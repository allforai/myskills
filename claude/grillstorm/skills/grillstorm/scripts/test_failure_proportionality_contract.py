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
