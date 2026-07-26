# Grillstorm Orientation Grill And Intent Archaeology

## Goal

Prevent Grillstorm from entering product decisions, specifications, ticket generation, or
implementation with a mistaken model of the repository's current state.

The startup phase must investigate first, explicitly distinguish observation from inference, and
survive independent adversarial cross-examination. This is an internal evidence gate, not another
user approval or a broad interview.

Grillstorm must also reconstruct why important existing behavior and user requirements exist.
Understanding only the literal code or requested solution is insufficient: downstream work must
trace to the underlying purpose, protected constraint, and observable outcome.

## Global Intent-Archaeology Invariant

Intent archaeology is a reasoning protocol applied across orientation, human decisions, specs,
tasks, reviews, and acceptance. It is not another sequential phase.

For every material existing behavior or request, distinguish:

```text
implementation or requested solution
<- behavior, pain, or constraint it addresses
<- underlying purpose
<- observable user outcome
```

Do not infer purpose from code shape alone. Reconstruct it from the strongest available combination
of runtime behavior, tests, commit history, blame, ADRs, documentation, issues, configuration, and
surrounding invariants. Classify the result:

- `intentional_design`: purpose is supported by direct historical or behavioral evidence;
- `historical_compromise`: evidence shows a constraint or workaround that may no longer apply;
- `accidental_behavior`: no protected purpose is found and evidence indicates incidental behavior;
- `unknown_intent`: plausible purpose exists but evidence cannot distinguish it.

`unknown_intent` cannot silently become a requirement. If it could affect route selection or the
meaning of existing scope, resolve it at a narrowly bounded pre-route decision boundary: present
one purpose question with evidence, recommendation, and tradeoff, then rerun orientation
confirmation. This asks for product intent, never a discoverable repository fact. Unknown intent
that affects only future behavior proceeds to the normal Phase 1 decision Grill.

## Purpose-Complete Minimalism

Grillstorm's “use as little code as necessary” philosophy means the minimum implementation that
fully preserves the confirmed purpose, protected constraints, failure semantics, and proof. It
does not optimize source-line count.

Choose the design with the fewest concepts, states, branches, abstractions, and long-term
maintenance obligations that still delivers and proves the observable outcome. A small explicit
error path may be more minimal than a shorter generic abstraction because it hides less behavior.

Remove or avoid:

- abstractions with no current consumer or protected invariant;
- speculative extension points and compatibility layers for hypothetical futures;
- duplicated ownership or repeated expression of one business rule;
- historical compromises whose original constraint is evidenced to be gone;
- tests that lock incidental implementation details without proving an outcome;
- modules, interfaces, configuration, or fallback behavior added only for architectural symmetry.

Never minimize away:

- observable success, empty, failure, degraded, recovery, or rollback behavior;
- compatibility, security, privacy, authority, and data-integrity constraints;
- explicit cross-module contracts and ownership;
- evidence required to prove the underlying purpose;
- material behavior whose removal risk remains unresolved.

For every material simplification, record the counterfactual and classify it:

- `remove`: no current purpose or protected constraint remains;
- `simplify`: the purpose remains but the mechanism is heavier than necessary;
- `retain`: both purpose and mechanism remain justified;
- `replace`: the purpose remains and a smaller mechanism preserves it;
- `unknown`: intent or removal impact is unresolved.

`unknown` is not permanent immunity for dead code. Investigate it within the same goal-relative,
bounded evidence budget. If it remains material and unknown, block or defer only the affected
simplification; do not expand scope or preserve a speculative abstraction as a new requirement.

Every proposed abstraction or extra mechanism bears the burden of proof: name its current
consumer, protected invariant, hidden complexity, and independent test seam. Every removal bears
the symmetric burden of proving that the underlying purpose and constraint are absent or preserved
elsewhere.

## Position In The Workflow

Add an orientation-closure gate inside Phase 0 after initial repository/environment discovery but
before route selection or Phase 1 product questions. Route selection is a downstream conclusion
and must be derived from the verified current-state model.

```text
inspect repository and runtime
-> build current-state evidence map
-> independent fresh-context orientation Grill
-> repair misunderstandings and missing evidence
-> independent confirmation when a material repair occurred
-> select route from the verified baseline
-> begin user decision Grill
```

The gate applies before and independently of every route. A later compact route may mirror the
canonical orientation record but may not replace it or skip the reasoning and evidence
requirements.

## Current-State Evidence Map

Persist `reviews/orientation.md` before route selection for every run. A later compact route may
mirror its terminal status and artifact pointer into compact state, but the evidence map remains
the canonical source. Scope investigation to facts material to the user's goal and its reachable
dependency, interface, runtime, and acceptance surfaces. Expand outward only when repository
evidence or a critic finding shows that another surface could change a material conclusion; this
is not a default whole-repository audit. Within that boundary, record:

- actual user-visible capabilities and known non-capabilities;
- real entry points, important call chains, data flows, state stores, and external dependencies;
- existing modules, public/cross-module interfaces, policies, and reusable capabilities;
- what tests and acceptance commands actually prove, plus important unproved behavior;
- contradictions among documentation, code, tests, configuration, and observed runtime behavior;
- relevant recent commits, active branches/worktrees, and pre-existing dirty paths;
- goal statements that describe genuinely new work versus behavior already present;
- constraints and historical decisions that limit the solution space.

Every material claim has:

```json
{
  "claim_id": "OS-001",
  "claim": "specific current-state statement",
  "classification": "observed|inferred|unknown",
  "evidence": ["path:line", "command and result", "commit", "runtime artifact"],
  "confidence": "high|medium|low",
  "impact_if_wrong": "scope|architecture|interface|acceptance|execution|low",
  "status": "open|verified|corrected_pending_confirmation|unknown"
}
```

Material behavior claims also record:

```json
{
  "observed_behavior": "what actually happens",
  "intent_class": "intentional_design|historical_compromise|accidental_behavior|unknown_intent",
  "likely_intent": "purpose supported or hypothesized",
  "protected_constraint": "what must not be lost",
  "alternative_explanation": "strongest competing interpretation",
  "counterfactual": "what would break or improve if removed"
}
```

`observed` requires direct repository, command, history, or runtime evidence. `inferred` names the
reasoning and competing interpretation. `unknown` remains unknown and cannot silently become a
fact, requirement, route premise, or task premise.

A claim is **material** when being wrong could change scope, route, architecture, a public or
cross-module interface, acceptance, execution ordering, destructive/external authority, or the
reuse-versus-rebuild decision. Materiality is sticky. Downgrading a material claim requires new
direct evidence and independent confirmation. A corrected claim remains
`corrected_pending_confirmation` until a later complete valid critic round verifies it.

Claim transitions are:

- investigation creates `open` with classification `observed`, `inferred`, or `unknown`;
- an `observed` claim becomes `verified` only when its direct evidence is inspectable and the
  critic returns `supported`;
- an `inferred` claim becomes `verified` only when its premises are directly evidenced, its
  competing interpretation is recorded, and the critic independently returns `supported`;
- a repaired material claim becomes `corrected_pending_confirmation`, then `verified` only after
  a later complete valid round returns `supported`;
- an `unknown` claim remains `unknown` and can never be `verified`; if material, it blocks.

No other classification/status combination is terminal.

## Independent Orientation Grill

Dispatch a fresh-context `THINK` critic. It receives:

- the user's goal verbatim;
- repository access and the starting Git state;
- the evidence-map artifact;
- a neutral orientation-critic prompt.

It does not receive the investigator's conversational rationale or intended design. The critic
must inspect raw evidence independently and attempt to falsify the current-state model:

1. Which claims are conclusions without adequate evidence?
2. What evidence supports a materially different interpretation?
3. Has desired future behavior been mistaken for existing behavior?
4. Has existing capability been missed and scheduled for needless reconstruction?
5. Are documented entry points, call chains, states, or side effects stale?
6. Do tests merely exist, or do they execute and prove the claimed behavior?
7. Do recent commits, dirty files, worktrees, generated artifacts, or configuration change the
   apparent baseline?
8. What failure, degraded, migration, operational, or external-system behavior is absent from the
   model?
9. Which unknowns could change scope, architecture, interfaces, acceptance, or execution?
10. Which alleged business rule is only a workaround or historical compromise?
11. Which test protects an observable purpose versus an accidental implementation detail?
12. Which existing capability is being scheduled for reconstruction because its intent was missed?

The critic returns:

- one coverage row for every material claim ID with
  `verdict: supported|refuted|insufficient|unreviewed`, raw evidence checked, and rationale;
- stable finding-family IDs, `material|residual` severity, affected claim IDs, direct evidence,
  alternative interpretation, and required investigation;
- explicit checks for missing material claims in each orientation category.

A result is complete and valid only when every existing material claim has exactly one coverage
row, every required category has been checked for omissions, evidence paths or command results are
inspectable, and the schema is well formed. Zero findings may close only with complete supported
claim coverage. An empty findings list without that coverage, prose-only approval, an
`unreviewed` row, or missing coverage cannot establish closure. The critic cannot accept a claim
merely because the artifact is well written.

For every material behavior whose intent affects downstream work, coverage also states whether the
intent classification is evidenced, contradicted, or still unknown. A critic must challenge the
investigator's preferred explanation and name the strongest counterfactual interpretation.

Treat each material intent assessment as a governed subclaim. `contradicted` or `still_unknown`
cannot close orientation: it creates an open material family, requires investigation or the
bounded pre-route purpose decision, and follows the same round-continuation rules as any other
material claim. A repaired intent classification becomes `corrected_pending_confirmation` and
requires a later independent `evidenced` verdict. At closure, every route-affecting material intent
subclaim must be independently evidenced or user-resolved and confirmed.

## Human Decision Intent Grill

When the user proposes a feature, constraint, or solution, internally separate:

1. the literal requested mechanism;
2. the behavior or pain being changed;
3. the underlying purpose and non-negotiable constraint;
4. the observable success condition.

Ask only when different plausible purposes would materially change scope, architecture, public
interfaces, acceptance, or external authority. Keep the one-question format, but summarize the
inferred purpose and recommend the solution that best serves it. Do not interrogate internal,
reversible implementation details.

Persist each material decision as a purpose chain:

```text
decision
-> why requested
-> underlying purpose
-> evidence
-> protected constraint
-> rejected alternative and tradeoff
-> observable acceptance
```

User confirmation accepts the purpose, protected constraint, and tradeoff—not merely the proposed
mechanism. If the literal mechanism conflicts with the confirmed purpose, explain the mismatch and
recommend the purpose-preserving option.

Stop asking “why” when the chain reaches an observable user outcome, a non-negotiable
safety/compatibility/legal/operational constraint, or a depth at which another answer would not
change a material design or acceptance decision. If further depth would be speculation, record the
uncertainty instead of inventing purpose.

## Downstream Purpose Trace

Every material spec requirement and task must trace backward to an authoritative purpose chain and
forward to observable acceptance. Its source is one of:

- `evidence_verified`: repository intent independently confirmed by the orientation critic;
- `user_confirmed`: purpose and tradeoff accepted during the front-loaded decision Grill;
- `autonomous_post_freeze`: a purpose-preserving interpretation chosen later inside frozen
  authority and disclosed at completion.

Evidence-verified repository intent does not require user approval. A change to either repository
evidence or a user decision invalidates every downstream purpose chain that depends on it.

```text
code change
-> task
-> requirement
-> decision
-> underlying purpose
-> observable outcome
```

Spec, task, workflow, and implementation critics must test purpose fidelity, not only literal
coverage. A review blocks when the system faithfully implements the requested mechanism but fails
the underlying purpose, drops its protected constraint, or proves only implementation details.

They must also test minimality symmetrically:

- reject unnecessary concepts, speculative abstractions, and duplicated mechanisms;
- reject simplifications that erase purpose, failure semantics, compatibility, authority, or
  proof;
- demand evidence both for adding complexity and for deleting material behavior.

After the ordinary interaction boundary, intent archaeology never reopens a user interview.
Choose and record the best purpose-preserving interpretation inside frozen authority, then
revalidate affected artifacts. If no interpretation is authorized, defer only that scope and its
transitive dependents while independent work continues.

## Repair And Review Budget

Orientation review has:

| Mandatory rounds | Soft limit | Hard limit |
|---:|---:|---:|
| 1 | 2 | 3 |

A round starts with critic dispatch and consumes the round even if the critic fails or returns an
invalid result. One infrastructure retry may complete the same round. If it still fails, the round
cannot close; continue to the next available round to obtain a valid review. An invalid review at
the hard limit yields `orientation_blocked`.

The investigator resolves findings by inspecting more raw evidence, running safe diagnostics, and
correcting claims or their classifications. Rewording the same root cause is the same finding
family. A finding remains material until direct counter-evidence plus an independent critic
supports downgrade. Material repairs require a fresh independent confirmation round when budget
remains.

Run round 1 always. After any invalid round, run the next round when budget remains regardless of
the soft-limit continuation criteria. Close after round 1 only if it is complete and valid, all material claims are
supported, no material claim is missing or unknown, and no material repair followed the verdict.
Run the next available round for any non-closing condition: invalid review; `refuted`,
`insufficient`, `unreviewed`, missing, or material-unknown coverage; a new/open material family; or
a material repair needing confirmation. At the soft limit, round 3 uses exactly these same
continuation triggers. Never run round 4.

If a known material conflict has no safe diagnostic, obtainable evidence, or concrete
investigation step, stop early as `orientation_blocked`; do not spend the remaining rounds
rephrasing it. Record the exact missing evidence and why downstream work would be unsafe.

Close only when a complete valid critic round confirms:

- every material claim is `verified` and independently supported;
- no material contradiction or misunderstood baseline remains;
- every remaining `unknown` is demonstrably non-material and is visible rather than a hidden
  assumption.

If any material claim is `unknown`, insufficient, refuted, unreviewed, missing, or awaiting
confirmation, the gate remains open. If round 3 ends with such a condition, an invalid review, or
an unconfirmed material repair, record `orientation_blocked`. Do not select a route or begin
product questioning, specification, ticket generation, launch, or implementation.

## Interaction And Authority

The orientation Grill is internal and must not ask the user to approve the repository summary or
authorize ordinary investigation. Discoverable facts are obtained from code, tools, history,
tests, documentation, and safe runtime diagnostics.

After the gate closes, the normal front-loaded user decision Grill may ask only genuine product,
scope, boundary, interface, acceptance, or external-authority decisions. Unknown repository facts
remain investigation work, not user questions.

Destructive, paid, production, secret-bearing, or externally mutating diagnostics require existing
authority. Lack of that authority leaves the claim `unknown`; it does not justify fabricated
evidence.

Repository intent archaeology stops when all concrete goal-relevant evidence sources have been
checked and no named remaining source could change a material interpretation. Do not search
history, issues, or adjacent modules without a specific competing explanation to test. When
evidence is exhausted, classify `unknown_intent` and route it through the material rules above
rather than continuing an open-ended historical audit.

## Reporting And Resume

Persist the evidence map, critic verdicts, repairs, round ledger, final orientation status, and
source Git state. `state.json` must point to them so a resumed or cross-host run can verify whether
the baseline is still current.

If the source revision, relevant dirty paths, environment capability, or runtime configuration
changes before any downstream design or execution action, identify the affected orientation
claims and invalidate the transitive route, decisions, specs, tasks, workflow, and launch
artifacts that cite or depend on those claims. Rerun the necessary orientation investigation and
independent review, then regenerate that affected downstream subgraph. Direct and diagnostic
routes follow the same rule. Do not replay a valid orientation gate merely to reconstruct
conversation context.

The final execution report includes a compact list of corrected misunderstandings and unresolved
unknowns. It also discloses important reconstructed intentions, user mechanisms reinterpreted in
light of their purpose, autonomous purpose-preserving choices, and intent classifications that
remain uncertain. Routine confirmed facts are referenced through `reviews/orientation.md`, not
duplicated.

## Validation

Add contract tests for both Claude and Codex copies proving:

- Phase 0 routes through the orientation gate before Phase 1;
- the evidence map requires `observed|inferred|unknown`;
- material behavior claims require intent class, protected constraint, alternative explanation,
  and counterfactual;
- material simplifications use `remove|simplify|retain|replace|unknown` with symmetric evidence
  burdens for addition and deletion;
- material intent verdicts participate in validity, continuation, confirmation, and closure;
- the review budget is exactly mandatory 1, soft 2, hard 3;
- material repairs require independent confirmation;
- `orientation_blocked` prevents specs, tickets, and implementation;
- the gate does not ask for current-state facts or a new start approval;
- critic input proves fresh-context independence and requires inspection of raw repository
  evidence;
- goal-relative scoping prevents a compact route from becoming an unconditional repository audit;
- material decisions persist a complete purpose chain;
- purpose chains distinguish evidence-verified, user-confirmed, and autonomous sources without
  adding a repository-summary approval;
- spec/task/review closure rejects literal compliance that misses the underlying purpose;
- “why” questioning stops at observable outcomes, non-negotiable constraints, or immaterial depth;
- repository archaeology stops when no named remaining evidence source could change a material
  interpretation;
- late intent ambiguity never reopens user interaction and blocks only unauthorized affected scope;
- minimalism removes unsupported complexity without deleting purpose, failure semantics,
  compatibility, authority, or proof;
- Claude and Codex artifacts remain in parity.

Run pressure tests against:

1. a plausible but wrong architecture summary contradicted by code;
2. tests that exist but execute zero relevant assertions;
3. stale docs that disagree with runtime behavior;
4. dirty worktree changes that alter the apparent baseline;
5. a round-3 material repair without confirmation;
6. unavailable external/runtime evidence that must remain `unknown`.
7. a workaround incorrectly treated as an enduring business requirement;
8. a user-requested mechanism that conflicts with the user's stated underlying purpose;
9. a test that locks an implementation detail while failing to prove the protected outcome.
10. a shorter implementation that silently drops recovery or compatibility behavior;
11. dead-looking code with unknown intent that must be investigated but not preserved forever;
12. a speculative abstraction whose only defense is possible future reuse.
