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
