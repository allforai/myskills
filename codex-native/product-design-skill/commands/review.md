# Product Design Review For Codex Native

This document turns the source review hub into a Codex-native review workflow.

## When to use

Use this workflow when the user wants to:

- launch or inspect the review hub for existing `.allforai/` artifacts
- process submitted review feedback
- convert review comments into constraint files

Review remains optional unless the user explicitly asks for it.

## Modes

| Mode | Meaning |
|---|---|
| `start` or unspecified | describe or launch the review hub workflow |
| `process` | process all submitted review tabs |
| `process <tab>` | process one tab only |

Supported tabs:

- `concept`
- `map`
- `data-model`
- `wireframe`
- `ui`
- `spec`

## Start behavior

When the user wants to start review:

- identify the `.allforai/` base directory
- verify which tabs have backing artifacts
- describe the expected local server command and resulting URL
- if actual launch is requested and feasible, start the review hub server
- otherwise report the exact command the user would run locally

Expected review server source:

- `../../product-design-skill/commands/review.md`
- `../../product-design-skill/scripts/review_hub_server.py`

## Process behavior

When processing feedback:

1. read the relevant `review-feedback.json` files
2. reject tabs that were never submitted
3. count approved vs revision-needed items
4. if all items are approved, clear the corresponding constraints file when it
   exists
5. if revision items exist, convert them into `.allforai/constraints/<tab>.json`
6. output a concise repair-action summary

## Constraint generation rules

- each review comment that still requires revision becomes one constraint item
- IDs must be stable and idempotent across repeated processing
- target routing must map back to the correct upstream workflow
- processing must not directly rewrite upstream product artifacts

## Native output contract

The final response should include:

- which tabs were processed
- how many items were approved vs flagged
- which constraint files were written, updated, cleared, or skipped
- what upstream workflow should be rerun next

## Safety rules

- never claim a tab was reviewed if `submitted_at` is missing or null
- never mutate upstream design artifacts during review processing
- if server launch is not performed, state that clearly rather than implying it
  happened
