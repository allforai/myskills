import json

import pytest

from validate_failure_classification import (
    FAILURE_MODES,
    FailureClassificationError,
    load_classification,
    main,
    resolve_record,
    validate_coverage,
    validate_records,
)


def record(**overrides):
    base = {
        "mode": "timeout",
        "outcome": "R1",
        "damage": "reenterable",
        "reentry_proof": "the job queue redelivers; the row is upserted by request id",
        "frequency": "routine",
        "expansion": "guard-only",
    }
    base.update(overrides)
    return base


def rare(**overrides):
    base = {
        "frequency": "rare",
        "frequency_basis": "structural",
        "frequency_basis_evidence": "the unique index makes a duplicate insert unreachable",
    }
    base.update(overrides)
    return record(**base)


def test_routine_reenterable_is_guard_only():
    assert resolve_record(record())["expansion"] == "guard-only"


def test_routine_durable_is_full():
    resolved = resolve_record(
        record(damage="durable", reentry_proof="", expansion="full")
    )
    assert resolved["expansion"] == "full"


def test_rare_reenterable_is_none():
    assert resolve_record(rare(expansion="none"))["expansion"] == "none"


def test_rare_durable_is_guard_only():
    resolved = resolve_record(
        rare(damage="durable", reentry_proof="", expansion="guard-only")
    )
    assert resolved["expansion"] == "guard-only"


def test_frequency_never_rewrites_damage():
    resolved = resolve_record(
        rare(
            damage="durable",
            reentry_proof="",
            frequency_basis="external-sla",
            frequency_basis_evidence="the gateway publishes a 99.99% availability target",
            expansion="guard-only",
        )
    )
    assert resolved["damage"] == "durable"
    assert resolved["expansion"] == "guard-only"


def test_rare_without_basis_falls_back_to_routine():
    entry = record(frequency="rare", expansion="none")
    entry.pop("frequency_basis", None)
    resolved = resolve_record(entry)
    assert resolved["frequency"] == "routine"
    assert resolved["expansion"] == "guard-only"


def test_rare_with_unlisted_basis_falls_back_to_routine():
    resolved = resolve_record(
        rare(frequency_basis="seems-unlikely", expansion="none")
    )
    assert resolved["frequency"] == "routine"
    assert resolved["expansion"] == "guard-only"


def test_rare_without_basis_evidence_falls_back_to_routine():
    resolved = resolve_record(rare(frequency_basis_evidence="TBD", expansion="none"))
    assert resolved["frequency"] == "routine"
    assert resolved["expansion"] == "guard-only"


def test_missing_reentry_proof_falls_back_to_durable():
    entry = record(expansion="guard-only")
    entry.pop("reentry_proof")
    resolved = resolve_record(entry)
    assert resolved["damage"] == "durable"
    assert resolved["expansion"] == "full"


def test_placeholder_reentry_proof_falls_back_to_durable():
    resolved = resolve_record(record(reentry_proof="  TODO  ", expansion="guard-only"))
    assert resolved["damage"] == "durable"
    assert resolved["expansion"] == "full"


def test_unknown_damage_counts_as_durable():
    resolved = resolve_record(
        record(damage="unknown", reentry_proof="", expansion="full")
    )
    assert resolved["damage"] == "durable"
    assert resolved["expansion"] == "full"


def test_self_reported_expansion_contradicting_the_table_is_rejected():
    with pytest.raises(FailureClassificationError) as excinfo:
        validate_records([record(expansion="none")])
    assert "contradicts the table result" in str(excinfo.value)


def test_fallback_is_disclosed_in_the_error():
    with pytest.raises(FailureClassificationError) as excinfo:
        validate_records([rare(frequency_basis="hunch", expansion="none")])
    assert "admissible frequency_basis" in str(excinfo.value)


def test_record_without_outcome_is_rejected():
    entry = record()
    entry["outcome"] = ""
    with pytest.raises(FailureClassificationError) as excinfo:
        resolve_record(entry)
    assert "names no outcome" in str(excinfo.value)


def test_invalid_damage_value_is_rejected():
    with pytest.raises(FailureClassificationError):
        resolve_record(record(damage="probably-fine"))


def test_errors_name_the_mode_and_outcome():
    with pytest.raises(FailureClassificationError) as excinfo:
        validate_records([record(mode="race", outcome="R7", expansion="full")])
    assert "race@R7" in str(excinfo.value)


def test_validate_records_reports_every_bad_record():
    with pytest.raises(FailureClassificationError) as excinfo:
        validate_records(
            [
                record(mode="race", outcome="R7", expansion="full"),
                record(mode="timeout", outcome="R8", expansion="none"),
            ]
        )
    message = str(excinfo.value)
    assert "race@R7" in message
    assert "timeout@R8" in message


def test_valid_records_return_resolved_entries():
    resolved = validate_records([record(), rare(expansion="none")])
    assert [entry["expansion"] for entry in resolved] == ["guard-only", "none"]


def test_empty_record_list_is_rejected():
    with pytest.raises(FailureClassificationError):
        validate_records([])


# --- coverage: the record SET, not just each record's inside (Finding 1) ---


def test_shared_mode_enumeration_is_the_union_of_both_reverse_grill_prompts():
    # spec-reverse-grill.md lens 4 + task-reverse-grill.md lens 4, union, stable slugs.
    assert set(FAILURE_MODES) == {
        "invalid-input",
        "partial-failure",
        "timeout",
        "cancellation",
        "retry",
        "idempotency",
        "concurrency-race",
        "stale-data",
        "external-outage",
        "permission-denial",
        "cleanup",
        "degraded-operation",
        "observability",
        "recovery",
    }


def test_validate_coverage_reports_the_single_missing_pair():
    modes = ("timeout", "race")
    records = [
        {"outcome": "R1", "mode": "timeout"},
        {"outcome": "R1", "mode": "race"},
        {"outcome": "R2", "mode": "timeout"},
        # R2/race is omitted entirely.
    ]
    with pytest.raises(FailureClassificationError) as excinfo:
        validate_coverage(records, ["R1", "R2"], modes=modes)
    message = str(excinfo.value)
    assert "R2" in message
    assert "race" in message


def test_validate_coverage_truncates_many_missing_pairs():
    modes = tuple(f"mode-{i:02d}" for i in range(15))
    with pytest.raises(FailureClassificationError) as excinfo:
        validate_coverage([], ["R1"], modes=modes)
    message = str(excinfo.value)
    for mode in modes[:10]:
        assert mode in message
    for mode in modes[10:]:
        assert mode not in message
    assert "5 more" in message


def test_validate_coverage_passes_with_full_coverage():
    modes = ("timeout", "race")
    records = [
        {"outcome": "R1", "mode": "timeout"},
        {"outcome": "R1", "mode": "race"},
    ]
    assert validate_coverage(records, ["R1"], modes=modes) is None


def test_validate_coverage_extra_unlisted_mode_neither_breaks_nor_substitutes():
    modes = ("timeout", "race")
    records = [
        {"outcome": "R1", "mode": "timeout"},
        {"outcome": "R1", "mode": "an-extra-mode-outside-the-enumeration"},
    ]
    with pytest.raises(FailureClassificationError) as excinfo:
        validate_coverage(records, ["R1"], modes=modes)
    assert "race" in str(excinfo.value)


def test_validate_coverage_defaults_to_the_shared_mode_enumeration():
    with pytest.raises(FailureClassificationError) as excinfo:
        validate_coverage([], ["R1"])
    message = str(excinfo.value)
    for mode in FAILURE_MODES[:10]:
        assert mode in message


# --- load_classification: two accepted array keys, required outcomes (Findings 1 & 2a) ---


def test_load_classification_accepts_records_key(tmp_path):
    path = tmp_path / "classification.json"
    path.write_text(
        json.dumps({"records": [{"mode": "timeout", "outcome": "R1"}], "outcomes": ["R1"]})
    )
    records, outcomes = load_classification(path)
    assert records == [{"mode": "timeout", "outcome": "R1"}]
    assert outcomes == ["R1"]


def test_load_classification_accepts_failure_classification_key(tmp_path):
    path = tmp_path / "classification.json"
    path.write_text(
        json.dumps(
            {
                "failure_classification": [{"mode": "timeout", "outcome": "R1"}],
                "outcomes": ["R1"],
            }
        )
    )
    records, outcomes = load_classification(path)
    assert records == [{"mode": "timeout", "outcome": "R1"}]
    assert outcomes == ["R1"]


def test_load_classification_rejects_a_document_with_neither_key(tmp_path):
    path = tmp_path / "classification.json"
    path.write_text(json.dumps({"outcomes": ["R1"]}))
    with pytest.raises(FailureClassificationError):
        load_classification(path)


def test_load_classification_requires_outcomes(tmp_path):
    path = tmp_path / "classification.json"
    path.write_text(json.dumps({"records": [{"mode": "timeout", "outcome": "R1"}]}))
    with pytest.raises(FailureClassificationError):
        load_classification(path)


# --- main: wires validate_records then validate_coverage ---


def _full_record(mode, outcome):
    return {
        "mode": mode,
        "outcome": outcome,
        "damage": "reenterable",
        "reentry_proof": "the queue redelivers; the row is upserted by request id",
        "frequency": "rare",
        "frequency_basis": "structural",
        "frequency_basis_evidence": "the unique index makes this unreachable",
        "expansion": "none",
    }


def test_main_rejects_incomplete_coverage(tmp_path):
    path = tmp_path / "classification.json"
    path.write_text(
        json.dumps(
            {"records": [_full_record("timeout", "R1")], "outcomes": ["R1"]}
        )
    )
    with pytest.raises(SystemExit):
        main([str(path)])


def test_main_passes_with_full_coverage(tmp_path, capsys):
    records = [_full_record(mode, "R1") for mode in FAILURE_MODES]
    path = tmp_path / "classification.json"
    path.write_text(json.dumps({"records": records, "outcomes": ["R1"]}))
    exit_code = main([str(path)])
    assert exit_code == 0
    assert f"{len(FAILURE_MODES)} records" in capsys.readouterr().out
