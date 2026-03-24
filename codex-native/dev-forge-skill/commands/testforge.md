# Testforge For Codex Native

This document replaces the thin compatibility wrapper with a Codex-native test
auditing and test-forging contract.

## When to use

Use this workflow when the user wants to:

- audit existing tests against product and implementation intent
- discover missing tests across the test pyramid
- generate or refine tests
- identify implementation bugs discovered through test work
- run a forge-fix loop until quality converges

## Modes

| Mode | Meaning |
|---|---|
| `full` or unspecified | analyze, forge tests, fix findings, and report |
| `analyze` | audit only, without writing tests or fixing code |
| `fix` | use existing analysis artifacts to drive forging and repair |

Optional narrowing:

- `--sub-project <name>`
- `--module <name>`

## Native execution rules

- preserve `.allforai/testforge/` outputs
- if `fix` mode is selected, require an existing analysis artifact or fail fast
- separate "tests missing" from "implementation broken"
- do not claim all-green status unless verification actually passed

## Core outputs

- `.allforai/testforge/testforge-decisions.json`
- `.allforai/testforge/test-profile.json`
- `.allforai/testforge/testforge-analysis.json`
- `.allforai/testforge/testforge-fixes.json`
- `.allforai/testforge/testforge-report.md`

## Audit dimensions

- vertical alignment against upstream artifacts
- horizontal alignment across sibling projects and mocks
- negative-space scenario discovery
- forge-fix convergence
- outer-loop intent verification when upstream artifacts exist

## Final response contract

The final response must include:

- selected mode
- audited scope
- highest-value missing tests
- implementation bugs discovered via testing
- whether new tests were actually written or only recommended
- where the analysis and final report artifacts live
