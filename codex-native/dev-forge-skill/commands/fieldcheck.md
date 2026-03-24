# Fieldcheck For Codex Native

This document turns fieldcheck into a standalone Codex-native field-consistency
workflow.

## When to use

Use this workflow when the user wants to:

- compare UI, API, entity, and database field names
- find stale, ghost, mismatched, or semantically drifting fields
- limit analysis to frontend, backend, end-to-end, or a chosen module

## Scopes

| Scope | Meaning |
|---|---|
| `full` or unspecified | L1 UI <-> L2 API <-> L3 Entity <-> L4 DB |
| `frontend` | L1 UI <-> L2 API |
| `backend` | L2 API <-> L3 Entity <-> L4 DB |
| `endtoend` | L1 UI <-> L4 DB |

Optional narrowing:

- `--module <name>`

## Native execution rules

- prefer upstream manifest and prior deadhunt decisions when available
- otherwise infer stack and module layout conservatively
- keep all analysis outputs under `.allforai/deadhunt/output/field-analysis/`
- do not mutate implementation code during analysis

## Core outputs

- `.allforai/deadhunt/fieldcheck-decisions.json`
- `.allforai/deadhunt/output/field-analysis/field-profile.json`
- `.allforai/deadhunt/output/field-analysis/field-mapping.json`
- `.allforai/deadhunt/output/field-analysis/field-issues.json`
- `.allforai/deadhunt/output/field-analysis/field-report.md`

## Output contract

The final response must include:

- selected scope and module filter if any
- coverage summary across the compared layers
- concrete critical issues
- concrete warning issues
- ambiguous cases requiring human review
- suggested fix order

Do not stop at percentages alone.
