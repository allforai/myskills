# Revised #11 implementation evidence

Scope: revised issue #11 only, based on accepted producer `3f66d7acc367cdb39ee12ae10827c8d81298ae0a` and documentation HEAD `88e7becaf30522ef29dd2fa168b62045affcb782`, in the assigned `j08069099777/grillstorm-meta-intent` checkout. Independent two-axis review and integration belong to the coordinator.

## Delivered behavior

- The copied interactive `product_intent.py` resume operation returns decision history/reasons, current questions, and journal-verified exclusions. Exclusions suppress repeated interviews without marking unanswered questions answered. Revoked scope cannot hide pending topics. An explicit reconsideration reopens only the selected excluded topic and its dependent questions.
- Explicit `reopen` and `restore` operations preserve journal history and revision lineage. Answered questions are validated against their actual journal payload and supersession history. Reopening a relevant question blocks all three generated public gates; answering and refreezing/replanning restores readiness. Unsupported legacy removal labels remain pending and can be explicitly corrected.
- Local `admit` consumes relevant legacy projections using the existing local-requirements contract. Canonical schema-1.0 choices can be reused, while unsupported choices need focused confirmation. Scope freeze binds the complete local projection to a recorded user decision. The scenario uses the pre-intent §A.1 mission/roles/errc_highlights baseline and preserves old concept, baseline, and product source byte-for-byte. It never inserts a whole-product questionnaire or whole-product planning stages. Existing local histories are protected against overwrite.
- Run Policy capture/reuse uses the same copied CLI on both platforms, independently of product decisions. Runtime policy consumption never writes product confirmations. The generated Claude Workflow shell and Codex flow driver require a valid policy before nodes, route repeated failures and non-blocking safety warnings, and consume the persisted iteration choice. One automatic repair is consumed durably before repair, including across resume. Accepted gaps remain a qualified outcome, without marking the acceptance node completed/verified or clearing its failing artifact.
- Both bootstrap entries and run templates invoke these public operations. Free planning, scope responsibilities, existing journal authority, retained unrelated-work checks, and ADR3 visual-review semantics are preserved.

## Test evidence

Tests were added and executed one failing behavioral slice at a time before implementation. Observed red failures included repeated excluded questions, unsupported reversal operations, unavailable local admission, accepted local projection tampering, missing policy collection, runtime starts without policy, unconditional retry halts, ignored iteration/safety choices, revoked exclusion authority, and a declared acceptance artifact bypassing the iteration-policy branch.

The new Python suites execute copied bootstrap/resume and three gate CLIs. Runtime tests execute the actual Workflow shell in its public injected-agent environment and the generated Codex driver; the external agent/host boundary is scripted while policy CLIs and project artifacts are real. Tests distinguish outcome, emitted questions, immutable historical files, readiness, actual execution/repair counts, and completed-transition behavior. Existing engine fixtures now supply the mandatory recorded policy, and existing timeout tests copy the actual policy CLI instead of bypassing it.

Final validation:

- `python3 -m pytest claude/meta-skill/tests/unit codex/meta-skill/test_flow.py -q`: **352 passed**, 43.41 seconds.
- `node --test 'claude/meta-skill/knowledge/run-engine/tests/**/*.test.js'`: **55 passed**, including shell/core synchronization.
- The final policy-only run passed all **20** copied CLI/runtime scenarios before the full suite.
- `python3 -m py_compile` for the changed product-intent CLI and native flow template, `node --check` for the engine core, and `git diff --check`: passed.

## Limits and remaining ownership

These are deterministic CLI and scripted runtime proofs, not real Claude/Codex host dialogue transcripts or a semantic evaluation of an agent's inferred product draft. The coordinator retains real-host evaluation, independent standards/spec review, and integration. Legacy admission requires the interactive host to supply relevant projections and actual journal references; the helper does not infer the commercial meaning of arbitrary old documents. Source/evidence fingerprint synchronization remains #12 scope.

Static type checking is not configured for these Python/Workflow files in this repository, and `python3 -m mypy --version` reports `No module named mypy`; no typecheck pass is claimed. Python compilation, Node syntax checking, and whitespace validation are reported separately. No push, main merge, installed-skill mutation, issue closure, or subworker dispatch was performed.
