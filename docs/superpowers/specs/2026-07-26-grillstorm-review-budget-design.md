# Grillstorm Review Budget Design

## Goal

Bound Grillstorm's adversarial design-review loops at the point of diminishing returns
without stopping before repair-induced or cross-artifact defects have received one independent
confirmation pass.

The budget applies independently to:

1. specification design: reverse Spec Grill, closure critic, and abstraction critic;
2. task design: reverse Task Grill and task-closure critic;
3. workflow design: workflow Reverse Grill, DAG validation, and simulation review.

Implementation execution, test retry, diagnosis, and post-delivery audit sampling retain their
own existing budgets and are not charged to these design-review budgets.

## Budgets

| Review layer | Mandatory rounds | Soft limit | Hard limit |
|---|---:|---:|---:|
| Specification design | 3 | 5 | 8 |
| Task design | 2 | 3 | 5 |
| Workflow/DAG design | 2 | 3 | 4 |

A round starts when the first required fresh-context critic for that layer is dispatched. The
counter increments exactly once at that point. All required critics belong to that numbered
round. A critic failure, timeout, cancellation, malformed result, or incomplete critic set still
consumes the round and cannot close the layer; infrastructure retry may finish the same numbered
round once, but cannot restart its completed critics or create free extra review. Adding an
unplanned critic does not increase the budget or replace a required critic.

Repair work occurs between rounds. The transition is:

`round N verdicts → recorded repairs → mandatory confirmation round N+1`.

Any material repair after round N forces round N+1 when budget remains.

Budgets are independent. Unused rounds never transfer between layers.

## Finding classes

A **material blocking finding** is any issue that can cause:

- incorrect behavior, data loss/corruption, security failure, fake success, or runtime deadlock;
- contradiction in requirements, state machines, public interfaces, ownership, or failure policy;
- missing or stale cross-module/cross-artifact propagation;
- an unverifiable acceptance contract or absent real-effect proof;
- a repair-induced defect with a distinct failure mechanism or affected surface.

A **residual finding** is naming, wording, duplication, presentation, optional refactoring, or a
preference that does not change approved behavior, safety, interfaces, proof, or runtime outcome.

Rephrasing, splitting, or rediscovering an already recorded failure mechanism is not a new finding
family. Each finding carries a stable `family_id`, severity, affected artifacts, evidence, and
status so later rounds cannot inflate novelty by changing prose.

Material classification is sticky. A material family may become residual only when evidence proves
its original failure mechanism cannot affect behavior, safety, interfaces, proof, or runtime
outcome, and a fresh independent critic accepts that evidence. Renaming, narrowing, splitting, or
rewriting the finding cannot downgrade it. Otherwise it remains material until
`verified_resolved`.

## Continuation and stopping

1. Run every mandatory round unless the layer is proven genuinely inapplicable to the selected
   route. A missing, stale, invalid, or failed-to-generate artifact blocks the layer; it never
   waives review.
2. Before the soft limit, stop early after a clean confirmation round: the round after the last
   material repair explicitly rechecks every repair since the prior completed round, marks every
   affected family `verified_resolved`, finds zero open material blockers, and finds no new
   material blocking family.
3. At or beyond the soft limit, continue only when the immediately preceding round:
   - found a new material blocking family; or
   - was followed by a material repair to a public interface, state machine, ownership boundary,
     cross-artifact reference, acceptance/proof contract, or other open material family.
   If a known material family remains open, no new family appears, and no concrete repair is
   available or performed, stop immediately as `blocked_unrepaired`; do not spend later rounds
   rediscovering it.
4. Stop only when a complete confirmation round has marked all known material families
   `verified_resolved`, zero material blockers remain open, and any new findings are residual.
   Persist residual risks; they do not block the next layer.
5. Never exceed the layer's hard limit. At the hard limit:
   - a complete valid critic set, zero open material blockers, and all known material families
     `verified_resolved` -> close the layer and record residual risks;
   - any material blocker -> set the layer to `budget_exhausted_blocked`, emit the unresolved
     inventory and evidence, and prohibit progression to implementation.
   - an incomplete, failed, malformed, or inconclusive critic set ->
     `budget_exhausted_blocked`, even when no blocker was successfully reported.

The last material repair must receive one independent confirmation round. No material repair may
be performed after the hard-limit review and then declared closed: without a remaining review
round, the layer ends `budget_exhausted_blocked`. Deterministic checks may support evidence but
never substitute for the required fresh critic confirmation.

## Budget reset

Internal discoveries, repairs, critic edits, task regeneration, and projection rebuilding do not
reset or increase a budget.

Only a new explicit user instruction received after the epoch baseline that changes the goal,
user-visible scope, public interface, or acceptance policy creates a new review epoch for the
affected layer. The run records the old epoch, exact user instruction, trigger, invalidated
artifacts, and new budget. Autonomous reinterpretation of existing answers, implementation
decisions, critic suggestions, and requests made merely to obtain more budget never reset a
design-review budget. During unattended execution, do not solicit or infer a reset; finish within
budget or return `budget_exhausted_blocked`.

## State and reporting

Persist per layer and epoch:

```json
{
  "layer": "spec|task|workflow",
  "epoch": 1,
  "round": 4,
  "mandatory": 3,
  "soft_limit": 5,
  "hard_limit": 8,
  "new_material_family_ids": ["SPEC-STATE-003"],
  "rechecked_family_ids": ["SPEC-STATE-001"],
  "verified_resolved_family_ids": ["SPEC-STATE-001"],
  "open_material_family_ids": ["SPEC-STATE-003"],
  "residual_family_ids": [],
  "material_repairs_since_prior_round": true,
  "confirmation_required": true,
  "status": "continue|closed|blocked_unrepaired|budget_exhausted_blocked"
}
```

Review reports include a round ledger showing new families, repeated families, repairs,
confirmation result, stop reason, and remaining blockers. “No new wording” is not closure.
Closure requires a complete valid confirmation round that explicitly rechecks every material
repair since the prior completed round, marks all known material families `verified_resolved`,
and leaves zero open material blockers.

## Skill changes

- Add the shared budget policy to Grillstorm's review references.
- Route specification, task, and workflow review loops through it.
- Keep Claude and Codex `SKILL.md` behavior identical.
- Add deterministic contract tests for the numeric budgets, non-reset rule, clean-confirmation
  rule, and hard-limit blocking behavior.
- Add pressure tests covering a seven-round useful sequence, cosmetic-only late findings,
  repeated rephrasing, hard-limit repair without confirmation, and user-triggered epoch reset.

## Versioning

This is a bounded behavior change to Grillstorm. Bump the patch version after implementation and
keep root marketplace, plugin manifest, local marketplace, and Codex metadata consistent.
