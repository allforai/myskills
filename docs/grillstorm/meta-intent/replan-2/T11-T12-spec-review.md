# T11/T12 independent spec review (candidate 5cab4f8f)

Base a37ca40a, HEAD verified = 5cab4f8f. Suites: 387 Python passed, 55 engine passed. Probes ran copied CLIs in temp projects (`scratchpad/probe.py`, `probe2.py`); none are host-dialogue proof, which stays pending for #16/#17.

## (a) Missing / partial

1. **#12 freshness is opt-in.** Spec: "文档、执行合同和验收证据能追溯到所使用的产品源码状态". Nothing requires `source_inputs`: `validate_bootstrap.py:1063` only checks consistency when present; `plan` (`product_intent.py:520-540`) adds none; `node-spec-template.md`, `bootstrap-planning.md`, codex `orchestrator-template.md` never mention it. Probe P4: two-node product plan without declarations → all three gates rc 0, `check_artifacts` `freshness: None`, then `orders.py` edited → still `all_exist: True`, readiness rc 0. A host that skips SKILL.md §3.0 prose silently gets zero traceability.
2. **#11 legacy reuse only for local-change.** Spec: "旧 concept／baseline 有可信确认记录时按相关范围复用". `admit` rejects non-local routes (`product_intent.py:477`); `draft` strips `confirmation` (`:717-718`). Probe P5: product-route draft item with a valid schema-1.0 journal choice → returned as pending, re-asked.
3. **#12 baseline version provenance** only read from `concept-baseline.json` (`evidence_freshness.py:211`); local-change route (profile `intent_scope`) records `null`. Minor.

## (b) Scope creep

None found. `safety_warnings`/`acceptance_verdict`/`accepted_with_gaps` in `engine-core.js` and `run-warnings.json` in `flow-template.py` map to the #11 Run Policy increment. ADR-0003 reviewer-neutral rules and main's input-floor semantics are untouched by these commits.

## (c) Wrong behavior

4. **#11: reopening one intent blocks unrelated nodes.** Spec: "相关未决依赖保持不可执行，无关工作不会仅因这个问题被失效". `_product_contract` raises globally (`product_intent.py:345-346, :320-322`), surfaced as `invalid_scope` without `node_id`. Probe P1: two nodes on disjoint intents, evidence published for both, `reopen value-proposition` (node-b) → `validate_bootstrap`, `check_decision_inputs`, readiness all rc 1 with global `invalid_scope`; freshness correctly reports node-a `valid`, node-b `stale`. Inherited from #10's frozen-baseline check, but #11 owns this criterion.
5. **#12: malformed declaration crashes gates** (regression vs #9's malformed-input rule, c93fc941). `source_inputs: "orders.py"` (string): `validate_bootstrap` rc 0; readiness and reconcile die with `TypeError` at `evidence_freshness.py:161` (`evaluate` unguarded in `validate_unattended_readiness.py:318`, `reconcile_bootstrap_workflow.py:220`); no readiness report written. Probe P3.
6. **#11: invalid `run-policy.json` cannot be repaired via CLI.** Templates say "Invalid policy blocks for interactive repair", but `run_policy` only writes when the file is absent (`product_intent.py:228`). Probe P6: valid answers + user_reference → `blocked`, file unchanged. Minor.

## Verified OK

SG01 observe-A/change-B rejection and pre/post-verification recheck (`:224-226, :250-252`); adjust + refreeze + replan keeps node-a evidence valid, node-b stale, readiness blocker only `node-b`, re-plan converges (P2); `check_artifacts.all_exist` consumes `status`, readiness consumes `readiness_status`, reconcile invalidates; both engines require `run_policy_ready` before the first node, consume repeated-failure/iteration/safety choices, and `accept` never commits the node.

Blockers for implementation: 4, 5, 1. Items 2, 3, 6 are partial/minor.
