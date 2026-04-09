---
description: "Record product-level decisions from the current conversation into decision-journal.json."
---

# Journal — Product Decision Journal

Record product-level decisions made in the current conversation.

## Step 1: Scan Conversation Context

Look for:

- user choices among options you presented
- design changes or redirections
- feature additions, removals, or deferments
- architecture or stack changes
- product behavior clarifications

Do not record:

- low-level implementation details
- temporary debugging choices
- bug-fix mechanics
- facts already fully represented in stable product artifacts unless the user changed them

## Step 2: Summarize Decisions

For each decision, record:

- `question`
- `chosen`
- `rationale`
- `supersedes` if this decision overrides an earlier one

## Step 3: Write Journal File

Target file:

- `.allforai/product-concept/decision-journal.json`

If the file exists, append a new batch.
If it does not exist, create it with the canonical schema.

## Step 4: Confirm Summary

Present a plain-text summary:

- how many decisions were recorded
- batch topic
- one line per recorded decision
- the target file path

## Step 5: Detect Concept Conflicts

If `.allforai/product-concept/product-concept.json` exists:

1. compare new journal decisions against the current concept
2. identify contradictions such as:
   - removed features that still exist in concept
   - new features that concept explicitly excludes
   - role changes that disagree with current role definitions
   - tech-direction changes that disagree with concept assumptions

If conflicts exist:

- list them
- instruct the user to run `journal-merge`

If no conflicts exist:

- report that the journal is currently consistent with `product-concept.json`
