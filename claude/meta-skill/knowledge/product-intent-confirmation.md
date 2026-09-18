# Interactive product-intent confirmation

For `product-reconstruction` and `new-product`, bootstrap and interactive resume
use this protocol before emitting executable product work. Local requests retain
the local requirement protocol. This is the same protocol on Claude and Codex.

## Discussion responsibility

For reconstruction, read actual code and relevant artifacts and synthesize a
provisional product draft across target users, scenarios, core problem, value
proposition, business loop, experience direction and tradeoffs. Separate `facts`
from inferred intent and unknowns; each inference has source quotes and a
concrete uncertainty.
High confidence never supplies approval. Product-summary and legacy concept
fields without confirmation provenance remain evidence. New products begin
from the user's request with `origin: user-request`, without reverse-concept.

Present one relevant topic at a time, show contradictory evidence and missing
product decisions proactively, and adapt the next question to the answers.
Topics are coverage dimensions, not a fixed questionnaire: combine related items
in one topic turn, omit already answered discussions, and expose only pending
exceptions on resume. Explicit batch approval may cover several named items;
recommendations, displayed defaults, omitted answers and silence are not
actions; `select` and `delegate` are actions.
Capture contradictions/gaps as questions with the intent IDs that depend on them.
A quote validator checks supplied evidence, not whether the agent discovered all
relevant facts: the host still owns semantic analysis and dialogue quality.

## Experience direction proposals

On a product route whose `bootstrap-profile.json` `experience_priority.mode` is
anything but `none`, `propose` is mandatory before the `experience-direction`
topic is discussed: the user chooses between written directions, never from an
empty prompt.

Each direction answers who it is for, in what circumstance (including scale and
frequency), what its core loop should feel like and why anyone comes back, before
it names a single feature. Each names one mature product doing the same job for
the same people, and what that product actually does about it. Two or three
directions differ in direction, not in size; three budgets for one idea are one
direction. `acceptance` states observable experience criteria, not a feature list.

The user's words are the circumstance to design for, never vocabulary to
transcribe. "fragmented learning / 碎片化学习" names minutes taken standing in a
queue between other things; a direction that answers it with a "fragments"
module has translated the phrase instead of designing for what it describes.

Self-check each round against `consumer-maturity-patterns.md` §B: The Compressed
Admin Panel (an operator's console handed to the person who lives with it), The
Concept Demo (a demonstration of the idea rather than a product), and Feature
Checklist Design (coverage standing in for an experience). Generating directions
may use `innovation-protocols.md` §A; this protocol does not require it.

A recommendation is not an action. Only the user's own `select`, or a `delegate`
they asked for in that turn, creates a confirmed experience direction; a
displayed default nobody answered stays a proposal. A delegated direction is
marked `auto_decided` (the naming of `defensive-patterns.md` Pattern H) and is
disclosed back to the user at run completion through
`product_intent.py . --delegations`. Deciding for the user is allowed only
because it is later visible as having been decided for them.

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
  objects, and `uncertainty` for inference. A drafted item never carries
  `model-proposal`: that origin belongs to proposals and to the items `select`
  and `delegate` derive from them. Topic names: `target-users`, `scenarios`,
  `core-problem`, `value-proposition`, `business-loop`, `experience-direction`,
  `tradeoffs`. The topic `experience-direction` is the experience the product
  gives a person; the `plan` stage and `not_applicable` key `experience` is the
  experience responsibility a node carries. They are not interchangeable.
  A product nobody looks at excludes `gap-experience-direction` at `freeze` with
  its reason, like any other inapplicable dimension.
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
  Without a session marker, `resume` reads an existing hand-projected
  `local-requirements.json` on a non-product route and verifies each item exactly
  as the public gates do: an actual user-turn reference or a journal decision with
  the full `intent` payload stays confirmed; a goal-only journal choice matching
  the goal and reason is pending with `legacy_reuse`; a mismatched or invalid one
  is pending with its reason. A removed item with that provenance stays removed
  history, never pending or new work, and needs explicit `restore` to revive it.
  An invalid tombstone is pending verification, not authoritative removal or approval.
  If the user confirms the removal, record `remove` directly: retain the old
  tombstone and append a confirmed removed revision without activating it first.
  `confirm` then recovers the gates without a
  session marker, freeze or plan. A later local `freeze` records the marker and is
  journal-backed: a user-turn item it includes must first be recorded with one
  `confirm` whose batch `user_reference` is the original user turn and whose
  `reason` is the recorded one. That records the already evidenced payload
  unchanged, with the old reference kept as `prior_confirmation`; it is not a
  fresh approval and asks no question. The freeze names the item until then.
  A removal excluded at that freeze stays removed history; ordinary `confirm`
  cannot revive it after the session marker changes.
- `propose`: `{operation, proposals, recommended_id, rationale}` offers the user
  two or three written experience directions on a product route. Each proposal
  carries exactly `id`, `title`, `who`, `circumstance`, `core_loop_feel`,
  `first_minute`, `return_reason` and `goal` as non-empty text, `anti_goals`,
  `tradeoffs`, `scope`, `business_rules` and `acceptance` as non-empty lists, and
  `comparable` as `{product, approach}`. Authority fields (`origin`, `status`,
  `confirmation`, `round`, `recommended`) are rejected: the CLI stamps
  `origin: model-proposal`, the round and the recommendation itself.
  `recommended_id` names exactly one of the offered proposals and `rationale`
  says why in the user's own terms. Proposal identities are unique across all
  rounds, intent IDs and question IDs. The store is append-only: a further
  `propose` opens the next round and keeps the earlier one as history. It records
  no journal decision and needs no `user_reference`, because offering a direction
  approves nothing. `resume` then returns the current round as `proposals` with
  `recommended_id` and `rationale` under the `experience-direction` topic.
- `decide`: `{operation, batch_id, topic, user_reference, actions}` records one
  explicit topic batch. Each action names itself with its own `operation` key.
  Each action needs the user's `reason`: `confirm`/`remove`
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
  `select` supplies the `proposal_id` the user picked from the current round.
  `delegate` supplies no `proposal_id` and takes that round's recommended
  proposal; it is legal only where the user said in that very turn to decide for
  them, and the batch `user_reference` must be that real user turn, never the
  recommendation or the turn it was displayed in. Both record one confirmed item
  `experience-direction-<proposal_id>` with `origin: model-proposal`, carrying the
  proposal's `who` and `circumstance`; `delegate` additionally marks it
  `auto_decided: true` and its `confirmation` `delegated: true`. The same batch
  may `adjust` the new item, and must `answer` `gap-experience-direction` with the
  chosen direction's title. Without a current proposal round both are refused, and
  a round opened in that same turn is not yet a current round: the user must have
  read those written directions and answered them, so the turn that opens a round
  ends with the proposals presented and the topic pending. `propose` and then
  `delegate` in one turn confirms a direction the user never saw, which is the
  refusal above wearing a round the model built for itself. A direction already
  selected is `remove`d before another one is chosen.
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
  `not_applicable.experience` is legal only when `bootstrap-profile.json` `experience_priority.mode` is `none`; any other mode is refused as `experience_not_applicable_on_ui_product`.
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
use `--policy-event <key>` as a read of the recorded choice.
`python3 .allforai/bootstrap/scripts/product_intent.py . --delegations` is the
other read-only entry: it lists every confirmed direction the user delegated, with
the proposal, the user turn and the reason. It writes nothing, asks nothing, and
the run's completion text reports what it returns. The one repair
`auto_fix_once` grants is an attempt charged in the repair-authorization ledger
against the concept-acceptance gate's declared loop, so interruption cannot grant
a second repair and no second accounting exists. Accepted gaps are an explicitly
qualified run outcome, not verified/completed work.
