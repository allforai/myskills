# Interactive product-intent confirmation

For `product-reconstruction` and `new-product`, bootstrap and interactive resume
use this protocol before emitting executable product work. Local requests retain
the local requirement protocol. This is the same protocol on Claude and Codex.

## Discussion responsibility

For reconstruction, read actual code and relevant artifacts and synthesize a
provisional product draft across target users, scenarios, core problem, value
proposition, business loop and tradeoffs. Separate `facts` from inferred intent
and unknowns; each inference has source quotes and a concrete uncertainty.
High confidence never supplies approval. Product-summary and legacy concept
fields without confirmation provenance remain evidence. New products begin
from the user's request with `origin: user-request`, without reverse-concept.

Present one relevant topic at a time, show contradictory evidence and missing
product decisions proactively, and adapt the next question to the answers.
Topics are coverage dimensions, not a fixed questionnaire: combine related items
in one topic turn, omit already answered discussions, and expose only pending
exceptions on resume. Explicit batch approval may cover several named items;
recommendations, displayed defaults, omitted answers and silence are not actions.
Capture contradictions/gaps as questions with the intent IDs that depend on them.
A quote validator checks supplied evidence, not whether the agent discovered all
relevant facts: the host still owns semantic analysis and dialogue quality.

## Executable persistence boundary

Copy `scripts/orchestrator/product_intent.py` into the project's
`.allforai/bootstrap/scripts/` before discussion (not only at final generation).
Run `python3 .allforai/bootstrap/scripts/product_intent.py . < request.json`.
JSON stdout reports `discussion`, `frozen`, `planned`, or `blocked`; a blocked
request exits 1. The host supplies requests from actual conversation and project
analysis; the CLI never interprets arbitrary prose as approval and never asks a
question during unattended execution. Request files are ordinary temporary input,
not additional product authorities.

- `draft`: `{operation, route, goal, items, facts, questions}`. Each item has a
  stable `id`, `topic`, `goal`, non-empty `scope`, `business_rules`, `acceptance`,
  `origin` (`inference`, `unknown`, `user-request`), `evidence` as `{path, quote}`
  objects, and `uncertainty` for inference. Topic names: `target-users`,
  `scenarios`, `core-problem`, `value-proposition`, `business-loop`, `tradeoffs`.
  Questions have `id`, `topic`, `question`, `kind`, and `depends_on` intent IDs.
  Question IDs are unique and distinct from all intent IDs, including generated
  gap questions; an ambiguous identity is rejected, never counted as an answer.
  Missing dimensions produce pending gap questions. New inferences stay pending.
  A legacy confirmed item stays confirmed only when its canonical journal decision
  records the complete `intent` payload; otherwise it is pending with a reason.
  A goal-only journal choice (recorded `chosen`/`rationale`, no `intent`) evidences
  the goal alone: the item is returned pending with `legacy_reuse` naming the
  evidenced field (`goal`) and the unconfirmed ones (`scope`, `business_rules`,
  `acceptance`), keeps its goal and prior reference for context, and needs an
  explicit `confirm` decision before freeze; `confirm` retains that reference as
  `prior_confirmation`. Reusing a recorded goal never approves inferred details.
- `resume`: `{operation: "resume"}` returns pending `topics` plus the complete
  requirement `history`, current `questions`, and journal-verified `excluded`
  scope with its reasons. Present only `topics` as questions; use history to
  restore context, not to repeat confirmed interviews. Explicitly excluded
  questions remain pending in storage and are distinct from answered questions.
  Use it on re-entry; never replace existing intent history with a new draft.
- `decide`: `{operation, batch_id, topic, user_reference, actions}` records one
  explicit topic batch. Each action needs the user's `reason`: `confirm`/`remove`
  select `id`; `add` supplies `item`; `adjust` selects `id` and supplies `changes`
  to product meaning; `answer` selects a question `id` and supplies `answer`.
  Include precisely the actions the user chose. Empty actions are a no-op.
  New needs require user provenance, never code evidence. Adjustments retain
  revision lineage; removals retain the old item and journal history. Reuse valid
  existing journal decisions and do not resubmit confirmed items.
  `reopen` selects an intent or question and records the user's reconsideration
  without an answer; dependent work blocks. `restore` explicitly restores a
  removed intention as a new confirmed revision with its reason. Never restore
  by relabeling old code or interpreting continue/accept as a product choice.
- `admit`: `{operation, route: "local-change", goal, areas, items, questions?}`
  admits only the relevant legacy projections to the existing local-requirements
  contract. Each item uses the draft item fields and any actual prior journal
  confirmation reference. Valid recorded choices are reused; unsupported ones
  are presented as pending. Missing whole-product dimensions do not generate a
  questionnaire. Old concept/baseline files stay unchanged; existing local
  requirement history must be resumed instead of overwritten. `decide`, `freeze`
  and `plan` then operate on this local session and require implementation,
  documentation and verification coverage, without whole-product stages.
  A legacy recorded goal alone cannot approve newly inferred scope, rules or
  acceptance: such an item is presented pending with `legacy_reuse` and needs one
  explicit `confirm` decision, not a whole-product interview, before freeze.
- `freeze`: `{operation, batch_id, user_reference, reason, include, exclude}`.
  `include` names confirmed intent IDs. `exclude` maps every other intent and
  pending question ID to an explicit exclusion reason. Excluding a question
  cannot authorize work that depends on its unanswered choice. The scope and
  increasing version are journal-backed; no inferred scope or silent approval.
  Re-freezing the identical confirmed selection (same intents, revisions and
  exclusions under a still-verified scope) returns the existing version with
  `unchanged: true` and writes nothing; a changed selection, exclusion or intent
  revision freezes the next version and the affected plan must be regenerated.
- `plan`: `{operation, nodes, not_applicable, ...workflow_fields}` consumes the
  frozen baseline. Freely design the smallest applicable full process, using
  capability guidance, suppress rules and project detections. Each node has its
  normal workflow fields plus `intent_ids`, `responsibilities`, `source_inputs`, and a substantive
  `body` following the normal Node-spec contract. Responsibilities cover product,
  experience, technical, implementation, documentation and verification for each
  included intent; combine nodes freely. Source inputs are relevant project-relative
  paths or globs, with explicit `[]` only when no product source is relevant;
  declaration alone is not verified contract or completion evidence.
  `not_applicable` may explain experience
  or technical omissions (for example a headless API has no UI experience work).
  This does not mandate every Capability. Emit a complete graph, including
  dependency edges, repair ownership and domain-specific acceptance; the helper
  binds confirmed goals/acceptance and generates matching Node-specs. Run all
  normal bootstrap audits after this projection. Scope labels alone do not prove
  semantic process completeness. Normal reconciliation owns existing execution
  history; pass its reconciled workflow fields instead of resetting a live run.

The CLI writes only product-concept artifacts and generated bootstrap artifacts.
Discussion never changes product source, including when the user removes intent.
It reuses `product-concept.json.requirements` as the projection and canonical
schema-1.0 `decision-journal.json.batches` as authority, with full confirmed
payloads and rationale. `concept-baseline.json.intent_baseline` holds the frozen
scope/version and journal reference. Earlier journal batches retain older scope
versions. Other concept fields remain available for compatibility, but may not
override this confirmed scope. Product-concept synthesis must derive its normal
mission/roles/mechanisms from these confirmed requirements, not the old feature
inventory. Do not create a second independent product baseline.

Generated workflow `product_baseline` and node `requirement_refs`,
`product_goals`, `acceptance`, and `decision_inputs` must agree with that version.
All three copied public gates validate journal payloads, scope and plan coverage;
bootstrap also checks Node-spec parity. The helper validates structure and binding,
not whether a natural-language goal is commercially good or a chosen graph is
semantically sufficient. Independent host tests must establish those properties;
scripted JSON tests are not real-host dialogue evidence.

Input declarations are a reading minimum; additional relevant reads are allowed,
but reading facts never expands authorization. Preserve main's one-time Run Policy
questions before execution, autonomous execution thereafter, ADR3 independent
visual-review semantics, and the 2D/2.5D limit disclosure: no revived 3D route choice.

At the interactive run entry, check `python3 .allforai/bootstrap/scripts/product_intent.py . --run-policy`.
`needs_run_policy` exits 1 and returns the three recorded-policy questions and
options; collect actual responses together before the first node. Persist via
`{operation: "run-policy", answers: {on_repeated_failure, on_needs_iteration,
on_safety_warning}, user_reference}`. Existing valid policy returns no questions;
invalid policy returns the questions with its invalidity reason for interactive
repair, never defaults. Explicit answers and the actual user response reference
repair it while retaining the prior content in `run-policy-repairs.json`.
Unattended policy events cannot collect or repair these choices. These operations
never write the product journal or requirement confirmations. Runtime consumers
use `--policy-event <key>`; `auto_fix_once` consumption is persisted before repair
in run-policy-state.json, so interruption cannot grant a second repair. Accepted
gaps are an explicitly qualified run outcome, not verified/completed work.
