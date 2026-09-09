# T10 Spec P2 retained completed nodes repair

Base: `b5c66303ce62618bd587ffa0ec705b8af61a6336`. Scope is only the retained-node handling in shared `product_intent.py` and the new public regression file `claude/meta-skill/tests/unit/test_product_retained_scope.py`; no staging or commits. Root concurrently owns question identity changes in the same production file and its separate test file.

## Changes

- Share the existing retained-node classification between scope validation and planning: fold `node_id` (Claude) and `node` (Codex) transitions in log order, require the node's latest status to be completed, and require no overlap with current scoped requirement references.
- Pass that set into the product contract so unrelated completed work is exempt from current intent projection checks. Current scoped nodes still supply all applicable full-process responsibilities and exact confirmed goals/acceptance.
- Planning preserves retained workflow metadata, historical decision inputs, goals, acceptance, existing Node-spec bytes, evidence files and transition provenance. A retained node can supply an existing Node-spec without new planning-only `body`/`intent_ids`; if no historical Node-spec exists, an explicit supplied brief is required and persisted without projecting current product intent onto it.
- Keep validation before file writes. Rejected plans leave prior files untouched. Both adapter script paths consume the shared implementation through the existing symlink.

## TDD and validation

The pre-agreed seam was copied public session input/output and the three generated-project gates. Read TDD instructions, examples and mocking guidance, `CONTEXT.md`, ADR-0001, the revised ticket, review and parent source before implementing; existing tests were not edited.

1. Added the retained historical workflow preservation regression first, then ran `python3 -m pytest claude/meta-skill/tests/unit/test_product_retained_scope.py -q`: **2 failed** on both adapters because planning required a fresh `body` for retained work.
2. Implemented minimal retained preservation, then reran that file: **2 passed**, including all three public gates.
3. Added coverage for absent/empty/historical references, a supplied historical brief, inserted unscoped work, a reopened historical node using a later event from the other adapter, and completed current-scope work with invalid acceptance or unconfirmed intent. An initial extended run found a test-fixture alias of the shared `TOPICS` list; copying the list fixed fixture isolation without changing production behavior.
4. `python3 -m pytest claude/meta-skill/tests/unit/test_product_retained_scope.py claude/meta-skill/tests/unit/test_product_intent_session.py claude/meta-skill/tests/unit/test_bootstrap_scope.py -q`: **178 passed in 30.75s** against the working candidate, including concurrent root changes present during execution.
5. Independently reproduced the precise review failure using `PYTHONPATH=claude/meta-skill python3` with temporary projects from `prepared_plan`, supplying historical `body` and empty `intent_ids`, and replacing only each temporary copied script with `git show b5c66303ce62618bd587ffa0ec705b8af61a6336:claude/meta-skill/scripts/orchestrator/product_intent.py`: both native histories returned exit 1 with **Product node consumes excluded or unconfirmed intent**. The checkout source was never reverted.
6. Final dedicated run, `python3 -m pytest claude/meta-skill/tests/unit/test_product_retained_scope.py -q`: **14 passed in 3.10s**. `git diff --check`: **exit 0**, no whitespace errors.

## Helper contract and limits

The shared classifier consumes already-reconciled history, retaining the established scope contract rather than implementing a new reconciliation/provenance authority. Completion history for one identity does not exempt a newly inserted identity; a later failed transition removes exemption even across adapter formats; current scoped references remove exemption even when the node is completed. The three gates retain structural validation of historical input paths and transition events.

This does not authenticate forged completion history or determine whether historical evidence remains reusable after external product changes; that remains reconciliation's responsibility under the parent contract and later tickets. No P1 work, #11–18 implementation, host execution claim, source/baseline policy change, main modification, install, stage or commit was performed by this worker. Coordinator owns combined review and commit.
