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
        if claimed != entry["expansion"]:
            detail = (
                f" after {'; '.join(entry['fallbacks'])}" if entry["fallbacks"] else ""
            )
            errors.append(
                f"{entry['mode']}@{entry['outcome']}: expansion {claimed!r} "
                f"contradicts the table result {entry['expansion']!r}{detail}"
            )
        resolved.append(entry)
    if errors:
        raise FailureClassificationError("; ".join(errors))
    return resolved


def load_classification(path):
    document = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(document, dict) or "records" not in document:
        raise FailureClassificationError("classification file needs a records list")
    return document["records"]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("classification")
    args = parser.parse_args(argv)
    try:
        resolved = validate_records(load_classification(args.classification))
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(f"failure classification: valid ({len(resolved)} records)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
