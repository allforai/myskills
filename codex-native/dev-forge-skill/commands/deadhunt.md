# Deadhunt For Codex Native

This document replaces the thin compatibility wrapper with a Codex-native
workflow contract for dead-link and completeness validation.

## When to use

Use this workflow when the user wants to:

- find dead links or ghost features
- validate CRUD completeness
- run static-only completeness checks
- run deep browser-driven validation when tooling is available
- generate regression follow-up tests after issues are found

## Modes

| Mode | Meaning |
|---|---|
| `full` or unspecified | static + planning + deep validation + reporting + follow-up tests |
| `static` | static analysis and reporting only |
| `deep` | deep validation path only, with report and follow-up actions |
| `incremental` | narrow the scan to changed modules when reliable scope detection exists |

## Prerequisites

- repository code must exist locally
- deep or full mode requires browser automation for web verification
- upstream `project-manifest.json` is helpful but not mandatory

## Native execution rules

- reuse upstream project profile decisions when possible
- ask the user only for missing facts that cannot be inferred safely
- if deep verification tooling is missing, do not pretend it ran
- for `deep` or `full`, either block on missing tooling or explicitly fall back
  to `static` only if the user accepts that downgrade

## Core outputs

- `.allforai/deadhunt/deadhunt-decisions.json`
- `.allforai/deadhunt/output/validation-report-summary.md`
- `.allforai/deadhunt/output/fix-tasks.json`
- any client-specific validation report files under `.allforai/deadhunt/output/`

## Report contract

The final response must include:

- selected mode
- validated scope
- concrete critical findings
- concrete warning findings
- items requiring manual confirmation
- next-step repair advice

Do not report only counts. The summary must name the failing area and the
recommended fix direction.

## Regression follow-up

When deadhunt produces fix-worthy issues, the workflow should also identify
which regression or coverage tests should be added next. If tests are not
actually added, state that clearly.
