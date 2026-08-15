import pytest

from validate_failure_classification import (
    FailureClassificationError,
    resolve_record,
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
