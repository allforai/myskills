---
description: "Merge decision-journal entries into product-concept.json and emit concept-drift.json."
---

# Journal Merge — Decision Reconciliation

Merge `decision-journal.json` into `product-concept.json`, resolve conflicts, and emit `concept-drift.json`.

## Inputs

Read:

- `.allforai/product-concept/decision-journal.json`
- `.allforai/product-concept/product-concept.json`
- `.allforai/product-concept/concept-drift.json` if it exists

If the journal file is missing, stop and tell the user to run `journal` first.
If the concept file is missing, stop and tell the user to complete the concept phase first.

## Step 1: Identify Unmerged Decisions

Use `concept-drift.json.last_merged_batch` when present to determine which batches are still unmerged.

Classify each unmerged decision as:

- conflict
- addition
- no-op

## Step 2: Resolve Conflicts

For each conflict:

- show the journal decision
- show the current concept value
- ask the user whether to:
  - accept the journal decision
  - keep the concept value
  - provide a custom merged value

For additions:

- auto-accept unless a new contradiction is found

For no-ops:

- skip silently

## Step 3: Update the Concept

Apply accepted changes to `.allforai/product-concept/product-concept.json`.

Typical update classes:

- feature removed
- feature added
- feature modified
- role removed
- role added
- tech changed

## Step 4: Write Audit Trail

Append the merge result to:

- `.allforai/product-concept/merge-audit.json`

Include:

- merged batches
- resolution mode
- before / after values

## Step 5: Emit Drift Manifest

Write or update:

- `.allforai/product-concept/concept-drift.json`

Include:

- drift timestamp
- merged source batches
- change list
- affected downstream areas such as `product-map`, `experience-map`, `workflow`, and `code`
- `resolved: false`

## Step 6: Report Impact

Present:

- change summary
- impacted downstream artifacts
- output file list

Then instruct the user to rerun `bootstrap` so the Codex-generated workflow can be re-planned.
