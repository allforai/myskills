# Grillstorm Failure Proportionality Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bound how far each failure mode expands into Grillstorm specs, tasks, code, and proof, using a damage × frequency table with three anti-rationalization locks enforced by a deterministic validator.

**Architecture:** A new reference document defines the rule. The two reverse-Grill prompts classify each failure mode before expanding it and redefine lens closure as *classified* rather than *designed*. The two closure critics accept the same table, so suppressed modes are not re-raised. The two closure gates accept `none` and `guard-only` as closed states. A Python validator applies the fallbacks and the table lookup deterministically, so the locks cannot be talked around in prose.

**Tech Stack:** Python 3 standard library (`argparse`, `json`, `pathlib`), pytest, Markdown skill documents.

## Global Constraints

- Repository root for all paths below: `/Users/aa/Documents/myskills`.
- Claude source of truth: `claude/grillstorm/skills/grillstorm/`. All edits land there first.
- `codex/grillstorm/` is byte-identical to the Claude skill directory apart from its `agents/` directory. Task 6 mirrors every change.
- Test command, run from `claude/grillstorm/skills/grillstorm/`: `python3 -m pytest scripts/ -q`. Baseline before this plan: **182 passed**.
- Validator style follows `scripts/validate_probe_artifacts.py`: module docstring, uppercase constant sets, a `ValueError` subclass for domain errors, and a `main(argv=None)` that calls `parser.error(str(exc))` and returns `0`.
- Document style is terse and imperative, matching the existing `references/*.md`: no hedging, no "you should", lines wrapped near 96 columns.
- Version bump `0.19.5` -> `0.20.0` in exactly two files: `claude/grillstorm/.claude-plugin/plugin.json` and `claude/grillstorm/.claude-plugin/marketplace.json`. `SKILL.md` has no version field in this plugin — do not add one.
- Spec: `docs/superpowers/specs/2026-08-15-grillstorm-failure-proportionality-design.md`.

---

### Task 1: Deterministic classification validator

**Files:**
- Create: `claude/grillstorm/skills/grillstorm/scripts/validate_failure_classification.py`
- Test: `claude/grillstorm/skills/grillstorm/scripts/test_validate_failure_classification.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: `FailureClassificationError(ValueError)`; `resolve_record(record: dict) -> dict` returning keys `mode`, `outcome`, `damage`, `frequency`, `expansion`, `fallbacks`; `validate_records(records: list) -> list[dict]`; `load_classification(path: str) -> list`; `main(argv=None) -> int`. Task 2 references the script path from the reference document.

- [ ] **Step 1: Write the failing tests**

Create `claude/grillstorm/skills/grillstorm/scripts/test_validate_failure_classification.py`:

```python
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run from `claude/grillstorm/skills/grillstorm/`:

```bash
python3 -m pytest scripts/test_validate_failure_classification.py -q
```

Expected: collection error — `ModuleNotFoundError: No module named 'validate_failure_classification'`.

- [ ] **Step 3: Write the validator**

Create `claude/grillstorm/skills/grillstorm/scripts/validate_failure_classification.py`:

```python
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
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
python3 -m pytest scripts/test_validate_failure_classification.py -q
```

Expected: `19 passed`.

- [ ] **Step 5: Run the whole suite**

```bash
python3 -m pytest scripts/ -q
```

Expected: `201 passed` (182 baseline + 19 new).

- [ ] **Step 6: Commit**

```bash
git add claude/grillstorm/skills/grillstorm/scripts/validate_failure_classification.py \
        claude/grillstorm/skills/grillstorm/scripts/test_validate_failure_classification.py
git commit -m "add deterministic failure classification validator"
```

---

### Task 2: Failure proportionality reference document

**Files:**
- Create: `claude/grillstorm/skills/grillstorm/references/failure-proportionality.md`
- Modify: `claude/grillstorm/skills/grillstorm/SKILL.md` (Phase 2.5 and Phase 3 reference wiring)
- Test: `claude/grillstorm/skills/grillstorm/scripts/test_failure_proportionality_contract.py`

**Interfaces:**
- Consumes: `scripts/validate_failure_classification.py` from Task 1 (referenced by path in the document).
- Produces: `references/failure-proportionality.md`, cited by name in Tasks 3, 4, and 5. The contract test file created here is extended by Tasks 3, 4, and 5.

- [ ] **Step 1: Write the failing contract test**

Create `claude/grillstorm/skills/grillstorm/scripts/test_failure_proportionality_contract.py`:

```python
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
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
python3 -m pytest scripts/test_failure_proportionality_contract.py -q
```

Expected: 6 failures — `FileNotFoundError` for `references/failure-proportionality.md`.

- [ ] **Step 3: Write the reference document**

Create `claude/grillstorm/skills/grillstorm/references/failure-proportionality.md`:

````markdown
# Failure Proportionality

Bound how far each failure mode expands into specs, tasks, code, and proof. Every mode is still
examined. This is an expansion budget, not permission to skip analysis.

## Classify before expanding

Record one entry per failure mode per outcome in `reviews/failure-classification.json`:

```json
{
  "schema_version": 1,
  "records": [
    {
      "mode": "timeout",
      "outcome": "requirement or global outcome ID",
      "damage": "reenterable|durable|unknown",
      "reentry_proof": "re-entry point and how state converges on re-run",
      "frequency": "routine|rare",
      "frequency_basis": "structural|external-sla|no-recorded-occurrence",
      "frequency_basis_evidence": "the constraint, declared SLA, or inspected history source",
      "expansion": "full|guard-only|none",
      "note": "one line; the whole record when expansion is none"
    }
  ]
}
```

`reenterable` means the failure leaves no durable trace and re-running restores a correct state.
`durable` means the failure can leave persistent wrong state: committed partial writes, an emitted
external side effect, moved money, a granted permission, a published message, or corrupt stored
rows.

`routine` means the mode is expected in normal operation. `rare` means it is credibly infrequent
for an evidenced reason.

## Expansion table

`expansion` is looked up, never chosen.

| | `reenterable` | `durable` |
|---|---|---|
| `routine` | `guard-only` | `full` |
| `rare` | `none` | `guard-only` |

- `full`: state transitions, rollback, recovery ordering, test seam, runtime observation, and
  completion evidence.
- `guard-only`: exactly one defense plus proof it holds. For `durable`, a transaction boundary,
  idempotency key, uniqueness constraint, or precondition check. For `reenterable routine`, proof
  that the re-entry path exists and is exercised. No branch tree, no recovery orchestration, no
  per-mode spec section.
- `none`: one ledger line. No requirement, spec section, task, test, or code branch.

`rare` with `reenterable` is the only exempt cell.

## Locks

1. Frequency never rewrites damage. `rare` does not convert `durable` into `reenterable`. Low
   probability does not undo an irreversible effect; it only shrinks the defense to one guard.
2. `rare` requires an admissible basis and its evidence: `structural` when a constraint, type, or
   invariant makes the mode unreachable; `external-sla` when an external dependency declares the
   guarantee; `no-recorded-occurrence` when named inspectable history shows none. A missing,
   unlisted, or unevidenced basis falls back to `routine`. "It basically never happens" is not a
   basis.
3. Re-entrancy is proved, not asserted. Missing or placeholder `reentry_proof` falls back to
   `durable`.

`damage: unknown` counts as `durable`. Investigate inside the same bounded gate; if it stays
unknown, defer that one mode without blocking the rest of the graph.

Run `scripts/validate_failure_classification.py reviews/failure-classification.json`. It applies
the fallbacks and the table deterministically, and rejects a self-reported `expansion` that
disagrees with the lookup. A failing run blocks the closure gate. The validator makes no
probability judgment of its own.

## Lens closure

A lens counts as applied to an outcome when every mode is classified, not when every mode is
designed. `expansion: none` and a proved `guard-only` are closed states.

## Issue ordering

Every issue from any lens carries `blast_radius`: `contract` when being wrong changes a
cross-module contract or acceptance, `module` when it changes one module's internals, `local` when
it changes a single call site. Consume issues in that order. Record `local` issues in
`reviews/spec-grill.md` or `reviews/task-grill.md` without expanding them.

No lens outside exceptional behavior gains a skip permission. Ordering defers expansion, never
examination.
````

- [ ] **Step 4: Wire the reference into SKILL.md**

In `claude/grillstorm/skills/grillstorm/SKILL.md`, Phase 2.5, replace this line:

```markdown
Read `references/spec-closure-and-abstraction.md` and `references/review-budgets.md`. Run
```

with:

```markdown
Read `references/spec-closure-and-abstraction.md`, `references/failure-proportionality.md`, and
`references/review-budgets.md`. Run
```

In the same file, Phase 3, replace this line:

```markdown
Write task/workflow Grill, closure, and dry-run reviews.
```

with:

```markdown
Write task/workflow Grill, closure, and dry-run reviews. Bound exceptional-behavior expansion with
`references/failure-proportionality.md` and validate `reviews/failure-classification.json` before
closure.
```

- [ ] **Step 5: Run the tests to verify they pass**

```bash
python3 -m pytest scripts/test_failure_proportionality_contract.py -q
```

Expected: `6 passed`.

- [ ] **Step 6: Run the whole suite**

```bash
python3 -m pytest scripts/ -q
```

Expected: `207 passed`.

- [ ] **Step 7: Commit**

```bash
git add claude/grillstorm/skills/grillstorm/references/failure-proportionality.md \
        claude/grillstorm/skills/grillstorm/SKILL.md \
        claude/grillstorm/skills/grillstorm/scripts/test_failure_proportionality_contract.py
git commit -m "define failure proportionality reference"
```

---

### Task 3: Reverse-Grill prompts classify before expanding

**Files:**
- Modify: `claude/grillstorm/skills/grillstorm/prompts/spec-reverse-grill.md:16-18` (lens 4), `:36-53` (return schema), `:56-57` (closing rule)
- Modify: `claude/grillstorm/skills/grillstorm/prompts/task-reverse-grill.md:15-17` (lens 4), `:31-48` (return schema), `:51-52` (closing rule)
- Test: `claude/grillstorm/skills/grillstorm/scripts/test_failure_proportionality_contract.py` (extend)

**Interfaces:**
- Consumes: `references/failure-proportionality.md` from Task 2.
- Produces: both prompts emit a top-level `failure_classification` array whose records match the schema in `references/failure-proportionality.md`, and every issue carries `blast_radius`. Task 4's critics read these.

- [ ] **Step 1: Write the failing contract tests**

Append to `claude/grillstorm/skills/grillstorm/scripts/test_failure_proportionality_contract.py`:

```python
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
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
python3 -m pytest scripts/test_failure_proportionality_contract.py -q
```

Expected: 5 failures, all `AssertionError`.

- [ ] **Step 3: Edit `prompts/spec-reverse-grill.md`**

Replace lens 4 (lines 16-18):

```markdown
4. **Exceptional behavior:** invalid input, partial failure, timeout, cancellation, retry,
   idempotency, concurrency/race, stale data, external outage, permission denial, cleanup,
   degraded operation, and recovery.
```

with:

```markdown
4. **Exceptional behavior:** invalid input, partial failure, timeout, cancellation, retry,
   idempotency, concurrency/race, stale data, external outage, permission denial, cleanup,
   degraded operation, and recovery. Classify each mode against
   `references/failure-proportionality.md` before expanding it. Emit an issue only for modes
   whose table result is `full` or `guard-only`. Modes resolving to `none` are recorded as
   classification records, not issues.
```

In the return schema, add `blast_radius` to the issue object by replacing:

```json
      "main_tradeoff": "short tradeoff",
      "affected_artifacts": ["paths or IDs"],
      "blocks": ["issue IDs"]
    }
  ]
}
```

with:

```json
      "main_tradeoff": "short tradeoff",
      "blast_radius": "contract|module|local",
      "affected_artifacts": ["paths or IDs"],
      "blocks": ["issue IDs"]
    }
  ],
  "failure_classification": [
    {
      "mode": "timeout|partial-failure|race|stale-data|invalid-input|...",
      "outcome": "outcome or requirement ID",
      "damage": "reenterable|durable|unknown",
      "reentry_proof": "re-entry point and how state converges on re-run",
      "frequency": "routine|rare",
      "frequency_basis": "structural|external-sla|no-recorded-occurrence",
      "frequency_basis_evidence": "the constraint, declared SLA, or inspected history source",
      "expansion": "full|guard-only|none",
      "note": "one line; the whole record when expansion is none"
    }
  ]
}
```

Replace the closing rule:

```markdown
Return `closed` only after every lens was applied to every global outcome and no unresolved
issue remains.
```

with:

```markdown
Return `closed` only after every lens was applied to every global outcome and no unresolved
issue remains. A lens is applied when every mode is classified, not when every mode is designed.
Order issues by `blast_radius` — `contract`, then `module`, then `local`.
```

- [ ] **Step 4: Edit `prompts/task-reverse-grill.md`**

Replace lens 4 (lines 15-17):

```markdown
4. **Exceptional behavior:** invalid input, partial failure, timeout, cancellation, retry,
   idempotency, concurrency/race, stale data, external dependency outage, permission denial,
   cleanup, observability, and recovery.
```

with:

```markdown
4. **Exceptional behavior:** invalid input, partial failure, timeout, cancellation, retry,
   idempotency, concurrency/race, stale data, external dependency outage, permission denial,
   cleanup, observability, and recovery. Classify each mode against
   `references/failure-proportionality.md` before expanding it. Emit an issue only for modes
   whose table result is `full` or `guard-only`. Modes resolving to `none` are recorded as
   classification records, not issues.
```

In the return schema, replace:

```json
      "main_tradeoff": "short tradeoff",
      "affected_artifacts": ["paths or IDs"],
      "blocks": ["issue IDs"]
    }
  ]
}
```

with:

```json
      "main_tradeoff": "short tradeoff",
      "blast_radius": "contract|module|local",
      "affected_artifacts": ["paths or IDs"],
      "blocks": ["issue IDs"]
    }
  ],
  "failure_classification": [
    {
      "mode": "timeout|partial-failure|race|stale-data|invalid-input|...",
      "outcome": "outcome or acceptance ID",
      "damage": "reenterable|durable|unknown",
      "reentry_proof": "re-entry point and how state converges on re-run",
      "frequency": "routine|rare",
      "frequency_basis": "structural|external-sla|no-recorded-occurrence",
      "frequency_basis_evidence": "the constraint, declared SLA, or inspected history source",
      "expansion": "full|guard-only|none",
      "note": "one line; the whole record when expansion is none"
    }
  ]
}
```

Replace the closing rule:

```markdown
Return `closed` only when every lens was applied to every global outcome and no unresolved
issue remains.
```

with:

```markdown
Return `closed` only when every lens was applied to every global outcome and no unresolved
issue remains. A lens is applied when every mode is classified, not when every mode is designed.
Order issues by `blast_radius` — `contract`, then `module`, then `local`.
```

- [ ] **Step 5: Run the tests to verify they pass**

```bash
python3 -m pytest scripts/test_failure_proportionality_contract.py -q
```

Expected: `11 passed`.

- [ ] **Step 6: Run the whole suite**

```bash
python3 -m pytest scripts/ -q
```

Expected: `212 passed`.

- [ ] **Step 7: Commit**

```bash
git add claude/grillstorm/skills/grillstorm/prompts/spec-reverse-grill.md \
        claude/grillstorm/skills/grillstorm/prompts/task-reverse-grill.md \
        claude/grillstorm/skills/grillstorm/scripts/test_failure_proportionality_contract.py
git commit -m "classify failure modes before expanding them in reverse grills"
```

---

### Task 4: Closure critics accept the table

**Files:**
- Modify: `claude/grillstorm/skills/grillstorm/prompts/spec-closure-critic.md:7-9`
- Modify: `claude/grillstorm/skills/grillstorm/prompts/task-closure-critic.md:7-11`
- Test: `claude/grillstorm/skills/grillstorm/scripts/test_failure_proportionality_contract.py` (extend)

**Interfaces:**
- Consumes: `references/failure-proportionality.md` from Task 2; the `failure_classification` records produced by Task 3.
- Produces: nothing new. This task closes the loop — without it a critic re-raises every suppressed mode and the rest of the change is inert.

- [ ] **Step 1: Write the failing contract tests**

Append to `claude/grillstorm/skills/grillstorm/scripts/test_failure_proportionality_contract.py`:

```python
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
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
python3 -m pytest scripts/test_failure_proportionality_contract.py -q
```

Expected: 2 failures, both `AssertionError`.

- [ ] **Step 3: Edit `prompts/spec-closure-critic.md`**

After this existing paragraph:

```markdown
Trace every requirement forward to an owned behavior, interface or state transition, test
seam, runtime observation, and completion proof. Trace every module/interface/seam backward
to the requirement that justifies it. Check failure, degraded, rollback, compatibility, and
real-side-effect closure.
```

insert this new paragraph:

```markdown
Failure closure follows `references/failure-proportionality.md`. Accept `expansion: none` and a
proved `guard-only` as closed. Do not demand per-mode treatment of a mode the table exempts.
Challenge only misclassification, a bypassed lock, or an unproved defense: `durable` damage
recorded as `reenterable`, `rare` without an admissible evidenced basis, placeholder
`reentry_proof`, or a `guard-only` defense with no proof it holds.
```

- [ ] **Step 4: Edit `prompts/task-closure-critic.md`**

After this existing paragraph:

```markdown
Verify that every final behavior has an integration/runtime proof task, every consumer task
is preceded by its interface producer, every extracted shared module precedes migrations,
and every prerequisite, migration, failure path, and reality gate is represented. Check that
tasks remain vertical, independently verifiable, and suitable for isolated execution.
```

insert this new paragraph:

```markdown
Failure paths follow `references/failure-proportionality.md`. Accept `expansion: none` and a
proved `guard-only` as closed. Do not demand per-mode treatment of a mode the table exempts.
Challenge only misclassification, a bypassed lock, or an unproved defense: `durable` damage
recorded as `reenterable`, `rare` without an admissible evidenced basis, placeholder
`reentry_proof`, or a `guard-only` defense with no proof it holds.
```

- [ ] **Step 5: Run the tests to verify they pass**

```bash
python3 -m pytest scripts/test_failure_proportionality_contract.py -q
```

Expected: `13 passed`.

- [ ] **Step 6: Run the whole suite**

```bash
python3 -m pytest scripts/ -q
```

Expected: `214 passed`.

- [ ] **Step 7: Commit**

```bash
git add claude/grillstorm/skills/grillstorm/prompts/spec-closure-critic.md \
        claude/grillstorm/skills/grillstorm/prompts/task-closure-critic.md \
        claude/grillstorm/skills/grillstorm/scripts/test_failure_proportionality_contract.py
git commit -m "teach closure critics the failure expansion table"
```

---

### Task 5: Closure gates accept classified-not-expanded

**Files:**
- Modify: `claude/grillstorm/skills/grillstorm/references/spec-closure-and-abstraction.md:52` (block list) and `:113-124` (exit gate)
- Modify: `claude/grillstorm/skills/grillstorm/references/task-documents.md:154-158` (global reverse closure)
- Test: `claude/grillstorm/skills/grillstorm/scripts/test_failure_proportionality_contract.py` (extend)

**Interfaces:**
- Consumes: `references/failure-proportionality.md` from Task 2.
- Produces: nothing new. This is the last gate that could still reject a `none` record.

- [ ] **Step 1: Write the failing contract tests**

Append to `claude/grillstorm/skills/grillstorm/scripts/test_failure_proportionality_contract.py`:

```python
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
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
python3 -m pytest scripts/test_failure_proportionality_contract.py -q
```

Expected: 3 failures, all `AssertionError`.

- [ ] **Step 3: Edit the spec closure gate**

In `claude/grillstorm/skills/grillstorm/references/spec-closure-and-abstraction.md`, replace this block-list bullet:

```markdown
- failure/degraded/rollback behavior that cannot return to a safe state;
```

with:

```markdown
- failure/degraded/rollback behavior that cannot return to a safe state, for every mode whose
  `references/failure-proportionality.md` result is `full` or `guard-only`;
```

In the same file, in the `## Exit gate` list, replace this bullet:

```markdown
- every matrix row is closed or explicitly reality-gated;
```

with:

```markdown
- every matrix row is closed or explicitly reality-gated;
- every failure mode is classified and `scripts/validate_failure_classification.py` passes over
  `reviews/failure-classification.json`; `expansion: none` and a proved `guard-only` are closed;
```

- [ ] **Step 4: Edit the task closure gate**

In `claude/grillstorm/skills/grillstorm/references/task-documents.md`, in `## Global reverse closure`, replace:

```markdown
   prefactoring. Apply problem, design, consistency, exception, and execution-reality
   lenses.
```

with:

```markdown
   prefactoring. Apply problem, design, consistency, exception, and execution-reality
   lenses. For the exception lens, follow `references/failure-proportionality.md`: classify
   each mode, expand only per the table, and validate
   `reviews/failure-classification.json` before ticket publication.
```

- [ ] **Step 5: Run the tests to verify they pass**

```bash
python3 -m pytest scripts/test_failure_proportionality_contract.py -q
```

Expected: `16 passed`.

- [ ] **Step 6: Run the whole suite**

```bash
python3 -m pytest scripts/ -q
```

Expected: `217 passed`.

- [ ] **Step 7: Commit**

```bash
git add claude/grillstorm/skills/grillstorm/references/spec-closure-and-abstraction.md \
        claude/grillstorm/skills/grillstorm/references/task-documents.md \
        claude/grillstorm/skills/grillstorm/scripts/test_failure_proportionality_contract.py
git commit -m "accept classified-not-expanded failure modes at closure gates"
```

---

### Task 6: Mirror to Codex and bump the version

**Files:**
- Modify: `claude/grillstorm/.claude-plugin/plugin.json:4`
- Modify: `claude/grillstorm/.claude-plugin/marketplace.json:9`
- Sync: `codex/grillstorm/` (references, prompts, scripts, SKILL.md)

**Interfaces:**
- Consumes: every file changed in Tasks 1-5.
- Produces: a Codex tree byte-identical to the Claude skill tree apart from `agents/`, and version `0.20.0` in both manifests.

- [ ] **Step 1: Verify the Claude tree is green**

From `claude/grillstorm/skills/grillstorm/`:

```bash
python3 -m pytest scripts/ -q
```

Expected: `217 passed`.

- [ ] **Step 2: Bump both manifests**

In `claude/grillstorm/.claude-plugin/plugin.json`, change `"version": "0.19.5",` to `"version": "0.20.0",`.

In `claude/grillstorm/.claude-plugin/marketplace.json`, change `"version": "0.19.5",` to `"version": "0.20.0",`.

- [ ] **Step 3: Mirror the changed files into Codex**

From the repository root:

```bash
cp claude/grillstorm/skills/grillstorm/SKILL.md codex/grillstorm/SKILL.md
cp claude/grillstorm/skills/grillstorm/references/failure-proportionality.md \
   claude/grillstorm/skills/grillstorm/references/spec-closure-and-abstraction.md \
   claude/grillstorm/skills/grillstorm/references/task-documents.md \
   codex/grillstorm/references/
cp claude/grillstorm/skills/grillstorm/prompts/spec-reverse-grill.md \
   claude/grillstorm/skills/grillstorm/prompts/task-reverse-grill.md \
   claude/grillstorm/skills/grillstorm/prompts/spec-closure-critic.md \
   claude/grillstorm/skills/grillstorm/prompts/task-closure-critic.md \
   codex/grillstorm/prompts/
cp claude/grillstorm/skills/grillstorm/scripts/validate_failure_classification.py \
   claude/grillstorm/skills/grillstorm/scripts/test_validate_failure_classification.py \
   claude/grillstorm/skills/grillstorm/scripts/test_failure_proportionality_contract.py \
   codex/grillstorm/scripts/
```

- [ ] **Step 4: Verify the mirror is exact**

From the repository root:

```bash
diff -rq claude/grillstorm/skills/grillstorm codex/grillstorm \
  --exclude=.pytest_cache --exclude=__pycache__
```

Expected: exactly one line — `Only in codex/grillstorm: agents`.

- [ ] **Step 5: Run the Codex suite**

From `codex/grillstorm/`:

```bash
python3 -m pytest scripts/ -q
```

Expected: `217 passed`. The contract tests resolve `ROOT` as `parents[1]`, which is `codex/grillstorm/` here, so they check the mirrored copies.

- [ ] **Step 6: Commit**

```bash
git add claude/grillstorm/.claude-plugin/plugin.json \
        claude/grillstorm/.claude-plugin/marketplace.json \
        codex/grillstorm/
git commit -m "mirror failure proportionality to codex and bump to 0.20.0"
```

---

## Self-Review

**Spec coverage:**

| Spec section | Task |
|---|---|
| The Rule — record schema | Task 2 (reference), Task 3 (prompt schema) |
| Expansion table | Task 2 (document), Task 1 (`EXPANSION_TABLE`) |
| Lock 1 — frequency cannot rewrite damage | Task 1 (`resolve_record` never reads frequency while resolving damage; `test_frequency_never_rewrites_damage`), Task 2 (prose) |
| Lock 2 — `rare` needs an evidenced basis | Task 1 (fallback + 3 tests), Task 2 (prose) |
| Lock 3 — re-entrancy is proved | Task 1 (fallback + 2 tests), Task 2 (prose) |
| `unknown` counts as `durable` | Task 1 (`test_unknown_damage_counts_as_durable`), Task 2 (prose) |
| Closure semantics — classified, not designed | Task 3 (both prompts), Task 5 (both gates) |
| Issue ordering by `blast_radius` | Task 2 (prose), Task 3 (schema + ordering rule) |
| Enforcement — validator points 1-5 | Task 1 (all five, each with a test) |
| Files Changed table | Tasks 1-5, one row each |
| Critics must change in the same revision | Task 4 |
| Version and mirror | Task 6 |
| Non-Goals | No task adds a finding cap, a probability estimate, or a skip permission |

**Placeholder scan:** No "TBD", "TODO", or "handle edge cases" outside the validator's `PLACEHOLDERS` constant and test fixtures, where those strings are the data under test.

**Type consistency:** `resolve_record` returns `mode`, `outcome`, `damage`, `frequency`, `expansion`, `fallbacks` — the keys every test reads. `validate_records` returns the same entries. `FailureClassificationError` subclasses `ValueError`, so `main`'s `except (OSError, ValueError)` catches it. The field names in the reference document (Task 2), both reverse-Grill schemas (Task 3), and the validator constants (Task 1) are identical: `mode`, `outcome`, `damage`, `reentry_proof`, `frequency`, `frequency_basis`, `frequency_basis_evidence`, `expansion`, `note`.
