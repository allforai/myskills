#!/usr/bin/env python3
"""Validate Grillstorm exceptional-behavior classification and expansion budget."""
import argparse
import json
from pathlib import Path


DAMAGE_VALUES = {"reenterable", "durable", "unknown"}
FREQUENCY_VALUES = {"routine", "rare"}
FREQUENCY_BASES = {"structural", "external-sla", "no-recorded-occurrence"}
EXPANSION_TABLE = {
    ("reenterable", "routine"): "guard-only",
    ("reenterable", "rare"): "none",
    ("durable", "routine"): "full",
    ("durable", "rare"): "guard-only",
}
PLACEHOLDERS = {"", "-", "?", "n/a", "na", "tba", "tbd", "todo", "unknown"}

# Shared exceptional-behavior lens enumeration (lens 4 of both reverse-Grill prompts),
# expressed as stable slugs. The two prompts word two entries differently:
#   prompts/spec-reverse-grill.md: "external outage" -> external-outage;
#     "degraded operation" -> degraded-operation (no "observability" entry).
#   prompts/task-reverse-grill.md: "external dependency outage" -> external-outage;
#     "observability" -> observability (no "degraded operation" entry).
# FAILURE_MODES is the union of both enumerations, so coverage is checked against every
# mode either prompt can produce, regardless of which prompt wrote the record.
FAILURE_MODES = (
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
)


class FailureClassificationError(ValueError):
    pass


def _blank(value):
    return not isinstance(value, str) or value.strip().lower() in PLACEHOLDERS


def resolve_record(record):
    """Apply the three locks, then look up the expansion budget."""
    mode = record.get("mode")
    if _blank(mode):
        raise FailureClassificationError("record has no mode")
    outcome = record.get("outcome")
    if _blank(outcome):
        raise FailureClassificationError(f"{mode}: record names no outcome")
    label = f"{mode}@{outcome}"

    damage = record.get("damage")
    if damage not in DAMAGE_VALUES:
        raise FailureClassificationError(
            f"{label}: damage must be one of {sorted(DAMAGE_VALUES)}"
        )
    frequency = record.get("frequency")
    if frequency not in FREQUENCY_VALUES:
        raise FailureClassificationError(
            f"{label}: frequency must be one of {sorted(FREQUENCY_VALUES)}"
        )

    fallbacks = []
    # Lock 3: re-entrancy is proved, not asserted.
    if damage == "reenterable" and _blank(record.get("reentry_proof")):
        damage = "durable"
        fallbacks.append("reenterable without reentry_proof -> durable")
    # Unresolved unknown damage counts as durable.
    if damage == "unknown":
        damage = "durable"
        fallbacks.append("unresolved unknown damage -> durable")
    # Lock 2: rare needs an admissible, evidenced basis.
    # Lock 1 is structural: damage is resolved without reading frequency.
    if frequency == "rare":
        if record.get("frequency_basis") not in FREQUENCY_BASES:
            frequency = "routine"
            fallbacks.append("rare without an admissible frequency_basis -> routine")
        elif _blank(record.get("frequency_basis_evidence")):
            frequency = "routine"
            fallbacks.append("rare without frequency_basis_evidence -> routine")

    return {
        "mode": mode,
        "outcome": outcome,
        "damage": damage,
        "frequency": frequency,
        "expansion": EXPANSION_TABLE[(damage, frequency)],
        "fallbacks": fallbacks,
    }


def validate_records(records):
    """Resolve every record and reject any self-reported expansion that disagrees."""
    if not isinstance(records, list) or not records:
        raise FailureClassificationError("records must be a non-empty list")
    resolved = []
    errors = []
    for record in records:
        if not isinstance(record, dict):
            errors.append("record is not an object")
            continue
        try:
            entry = resolve_record(record)
        except FailureClassificationError as exc:
            errors.append(str(exc))
            continue
        claimed = record.get("expansion")
        override = record.get("expansion_override")
        if claimed != entry["expansion"]:
            if isinstance(override, dict) and not _blank(override.get("evidence")) \
                    and override.get("expansion") == claimed \
                    and claimed in {"none", "guard-only", "full"}:
                # The three locks resolved damage and frequency; the table gave the default
                # expansion. A judgment that differs may stand only with evidence, and it is
                # recorded, never silent: the report shows table result, override and evidence.
                entry["expansion_table"] = entry["expansion"]
                entry["expansion"] = claimed
                entry["expansion_override"] = {"evidence": override["evidence"].strip()}
            else:
                detail = (
                    f" after {'; '.join(entry['fallbacks'])}" if entry["fallbacks"] else ""
                )
                errors.append(
                    f"{entry['mode']}@{entry['outcome']}: expansion {claimed!r} "
                    f"contradicts the table result {entry['expansion']!r}{detail}"
                    " (an expansion_override with evidence would be recorded instead)"
                )
        resolved.append(entry)
    if errors:
        raise FailureClassificationError("; ".join(errors))
    return resolved


def validate_coverage(records, outcomes, modes=None):
    """Reject any `(outcome, mode)` pair in `outcomes` x `modes` with no matching record.

    A record covers a pair only when both its `outcome` and `mode` match exactly. A record
    whose `mode` falls outside `modes` is allowed to exist but covers nothing — it neither
    breaks coverage nor substitutes for a listed mode.
    """
    modes = tuple(modes) if modes is not None else FAILURE_MODES
    covered = {
        (record.get("outcome"), record.get("mode"))
        for record in records
        if isinstance(record, dict)
    }
    missing = [
        (outcome, mode)
        for outcome in outcomes
        for mode in modes
        if (outcome, mode) not in covered
    ]
    if not missing:
        return None

    shown = missing[:10]
    grouped = {}
    for outcome, mode in shown:
        grouped.setdefault(outcome, []).append(mode)
    parts = [
        f"{outcome}: {', '.join(grouped[outcome])}"
        for outcome in outcomes
        if outcome in grouped
    ]
    remaining = len(missing) - len(shown)
    suffix = f"; and {remaining} more missing pair{'s' if remaining != 1 else ''}" if remaining else ""
    raise FailureClassificationError(
        "failure classification is missing coverage for: " + "; ".join(parts) + suffix
    )


def load_classification(path):
    document = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise FailureClassificationError("classification file needs a records list")
    records = document.get("records")
    if records is None:
        records = document.get("failure_classification")
    if records is None:
        raise FailureClassificationError(
            "classification file needs a records or failure_classification list"
        )
    outcomes = document.get("outcomes")
    if not isinstance(outcomes, list):
        raise FailureClassificationError(
            "classification file needs an outcomes list naming what it covers"
        )
    return records, outcomes


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("classification")
    args = parser.parse_args(argv)
    try:
        records, outcomes = load_classification(args.classification)
        resolved = validate_records(records)
        validate_coverage(resolved, outcomes)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(f"failure classification: valid ({len(resolved)} records)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
