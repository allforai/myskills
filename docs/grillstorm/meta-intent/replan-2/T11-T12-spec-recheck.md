# T11/T12 spec recheck (candidate 90257b15)

HEAD verified = `90257b1504d1c009d6e0f8a920fe0cf389f18463`, tree clean. Fixed diff `5cab4f8f...HEAD`. Independent rerun of the 13 #9–#12 suites in `validation-commands.md` plus `test_bootstrap_scope` / `test_product_intent_session`: 362 passed. Probes (`scratchpad/probe.py`, `probe2.py`) ran the copied CLIs in temp projects on both host copies (Codex script dir is a symlink). No host-dialogue proof; #13–#18 stay pending.

## Six prior findings

| # | Status | Evidence |
|---|---|---|
| 1 freshness opt-in | Fixed | undeclared scoped node → `missing_source_inputs` at all four gates; templates name the rule |
| 2 legacy reuse, product route | Fixed, see C1 | valid schema-1.0 choice kept; `source: code` → pending |
| 3 local baseline version | Fixed | observation records local scope version |
| 4 reopen blocks unrelated nodes | Fixed, local + product | reopen `archive`/`value-proposition`: all blockers `node_id: node-b`, no `invalid_scope`; freeze-level tamper stays global |
| 5 malformed declaration crash | Fixed | 8 malformed shapes → `invalid_source_inputs`, report written, no traceback |
| 6 run-policy repair | Fixed | invalid file → `needs_run_policy`; `--policy-event` and run-event answers refused; repair audited; valid file never replaced |

Root fixes verified: consumer publish with unpublished producer, requirement edit after observe, verifier mutating source, token replay after change → all `stale`; unmapped new file → `uncertain`, readiness blocks; every gate from another cwd, relative path and symlink gives identical results.

## (a) Missing / partial

**A1. Identical re-freeze is not idempotent.** Spec #12: "相同输入再次 bootstrap／续跑时，不生成重复产品决定、不重复规划". Probe A (product route, unchanged scope): a second `freeze` appends a journal decision, bumps version 2, and every gate turns global `invalid_scope` until `plan` reruns. Evidence survives the replan; convergence relies on host prose, not the CLI.

## (b) Scope creep

None. `run-policy-repairs.json` and typed admission blockers serve the #11/#12 increments.

## (c) Implemented-looking wrong behavior

**C1. Goal-only legacy choice authorizes unrecorded acceptance/scope.** Spec #11: "没有确认来源的旧代码推断不能伪装为已批准需求"; reuse "按相关范围". Probe B: a product draft item citing a schema-1.0 journal decision (goal + rationale only) with model-invented `acceptance` and an added `scope` area is stored `confirmed`, never appears in `discussion` topics, freezes with no `decide`, plans, and all gates report ready; the node's `acceptance` is the invention. `product-intent-confirmation.md` says the user "explicitly confirms the complete selected projection at scope freeze", but `freeze` presents nothing and `_confirmed` compares only goal and rationale. The same helper serves local `admit`. Medium.

**C2. Freshness CLI tracebacks on corrupt `observed-input-dependencies.json`.** #9 malformed-input rule. Gates fail closed, but `observe` exits with an uncaught `AttributeError` instead of `{"status":"invalid"}`. Minor.

**C3.** A reopen emits both `pending_requirement` and `stale_requirement` for one node. Cosmetic.

Blocker for acceptance: C1. A1 and C2 minor.
