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
  Missing dimensions produce pending gap questions. Draft always stays pending.
- `resume`: `{operation: "resume"}` returns only pending topics/items/questions.
  Use it on re-entry; never replace existing intent history with a new draft.
- `decide`: `{operation, batch_id, topic, user_reference, actions}` records one
  explicit topic batch. Each action needs the user's `reason`: `confirm`/`remove`
  select `id`; `add` supplies `item`; `adjust` selects `id` and supplies `changes`
  to product meaning; `answer` selects a question `id` and supplies `answer`.
  Include precisely the actions the user chose. Empty actions are a no-op.
  New needs require user provenance, never code evidence. Adjustments retain
  revision lineage; removals retain the old item and journal history. Reuse valid
  existing journal decisions and do not resubmit confirmed items.
- `freeze`: `{operation, batch_id, user_reference, reason, include, exclude}`.
  `include` names confirmed intent IDs. `exclude` maps every other intent and
  pending question ID to an explicit exclusion reason. Excluding a question
  cannot authorize work that depends on its unanswered choice. The scope and
  increasing version are journal-backed; no inferred scope or silent approval.
- `plan`: `{operation, nodes, not_applicable, ...workflow_fields}` consumes the
  frozen baseline. Freely design the smallest applicable full process, using
  capability guidance, suppress rules and project detections. Each node has its
  normal workflow fields plus `intent_ids`, `responsibilities`, and a substantive
  `body` following the normal Node-spec contract. Responsibilities cover product,
  experience, technical, implementation, documentation and verification for each
  included intent; combine nodes freely. `not_applicable` may explain experience
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
