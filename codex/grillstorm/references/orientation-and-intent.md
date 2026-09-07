# Orientation Grill And Intent Archaeology

Run this goal-relative gate before route selection or product questioning. It proves the current
state and reconstructs material intent without adding a repository-summary or start approval.

## Evidence map

Write `reviews/orientation.md` for every route. Inspect only the goal and its reachable dependency,
interface, runtime, and acceptance surfaces; expand when a concrete competing explanation requires
it. Record actual capabilities, entry points/call chains, data/state/external dependencies,
existing reusable seams, effective configuration, relevant tests and their executed assertions,
doc/code/runtime contradictions, recent commits/worktrees/dirty paths, and new-versus-existing
goal behavior.

Every material claim has a stable ID and:

```json
{
  "classification": "observed|inferred|unknown",
  "evidence": ["inspectable path, command result, commit, or runtime artifact"],
  "confidence": "high|medium|low",
  "impact_if_wrong": "route|scope|architecture|interface|acceptance|execution|authority",
  "status": "open|verified|corrected_pending_confirmation|unknown"
}
```

Material behavior also records `observed_behavior`,
`intent_class: intentional_design|historical_compromise|accidental_behavior|unknown_intent`,
`likely_intent`, `protected_constraint`, `alternative_explanation`, and `counterfactual`.

Material means being wrong could change route, scope, architecture, public/cross-module
interfaces, acceptance, execution, authority, or reuse-versus-rebuild. Materiality is sticky;
downgrade requires direct evidence and independent confirmation.

## Independent falsification

Dispatch `prompts/orientation-critic.md` in a fresh `THINK` context with the goal verbatim, starting
Git state, repository access, and evidence map. Exclude the investigator's conversation and
preferred design.

The critic returns exactly one coverage row per material claim:
`supported|refuted|insufficient|unreviewed`, plus checked raw evidence, rationale, missing-claim
checks, stable finding families, and material intent verdicts
`evidenced|contradicted|still_unknown`.

A valid round covers every material claim/category with inspectable evidence. Zero findings may
close with complete supported coverage. Prose approval, missing/duplicate coverage, `unreviewed`,
or uninspectable evidence is invalid.

## Budget and closure

| Mandatory | Soft | Hard |
|---:|---:|---:|
| 1 | 2 | 3 |

A dispatch consumes one round; one infrastructure retry may complete that round. Run the next
available round for any invalid review, non-supported material coverage, missing/material-unknown
claim or intent, open/new material family, or material repair needing confirmation. Never run
round 4. Rewording one root cause is not a new family.

Repairs become `corrected_pending_confirmation`. Close only after a later complete valid round
supports them and every material claim/intent is verified. At round 3, whatever is still not
supported is recorded as `unknown` in the orientation report, claim by claim, and orientation
closes with those unknowns attached: choose the most conservative route consistent with them and
say which unknowns drove the choice. `orientation_blocked` is reserved for a known material
conflict with no obtainable evidence and no safe investigation — not for running out of rounds
on a large or messy repository.

Route-affecting `unknown_intent` may trigger one narrowly bounded pre-route purpose decision with
evidence, recommendation, and tradeoff; never ask the user for a discoverable repository fact.
Future-only purpose belongs to the normal decision Grill.

Stop repository archaeology when every named goal-relevant evidence source is checked and no
concrete remaining source could change a material interpretation. History and adjacent modules
are evidence sources like any other: read them when they could change a material interpretation
and record what you read and what it settled.

## Intent archaeology

For material behavior or requests, trace:

```text
implementation or requested mechanism
<- behavior, pain, or constraint
<- underlying purpose
<- observable outcome
```

Purpose chains have source `evidence_verified`, `user_confirmed`, or `autonomous_post_freeze` and
record why requested, evidence, protected constraint, rejected alternative/tradeoff, and
observable acceptance. Repository evidence does not require user approval.

After ordinary interaction ends, never reopen a “why” interview. Adopt and record the best
purpose-preserving option inside frozen authority; otherwise defer only the affected scope and
dependents while independent work continues.

## Purpose-complete minimalism

Minimize concepts, states, branches, abstractions, and maintenance—not source lines. Remove
unsupported complexity, but preserve confirmed purpose, applicable success/empty/failure/degraded/
recovery behavior, compatibility, security, authority, data integrity, contracts, and proof.

Classify each material simplification `remove|simplify|retain|replace|unknown`. Additions and
deletions bear symmetric evidence burdens. An abstraction names a current consumer, protected
invariant, hidden complexity, and test seam. A removal proves the purpose/constraint is absent or
preserved elsewhere. Investigate `unknown` within this bounded gate; if still material, defer only
that simplification. Unknown intent is neither deletion permission nor permanent immunity.

Every downstream artifact traces:

```text
code -> task -> requirement -> purpose chain -> observable outcome
```

Reviews reject both speculative complexity and literal/minimal implementations that lose the
underlying purpose, protected constraints, failure semantics, compatibility, authority, or proof.

## Invalidation and reporting

When source revision, relevant dirty paths, environment, or runtime configuration changes,
invalidate affected orientation claims and all transitive route/decision/spec/task/workflow/launch
artifacts that depend on them. Re-investigate and regenerate only that subgraph.

The final report discloses corrected misunderstandings, unresolved non-material unknowns, important
intent classifications, mechanism-to-purpose reinterpretations, autonomous purpose-preserving
choices, and material simplifications.
