# Grillstorm Evidence-Backed Orientation Grill

## Goal

Prevent Grillstorm from entering product decisions, specifications, ticket generation, or
implementation with a mistaken model of the repository's current state.

The startup phase must investigate first, explicitly distinguish observation from inference, and
survive independent adversarial cross-examination. This is an internal evidence gate, not another
user approval or a broad interview.

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

The gate applies to every route. Compact routes may use a compact artifact, but they may not skip
the reasoning or evidence requirements.

## Current-State Evidence Map

Persist `reviews/orientation.md` for a program run, or the equivalent structured state entry for a
compact route. Scope investigation to facts material to the user's goal and its reachable
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

`observed` requires direct repository, command, history, or runtime evidence. `inferred` names the
reasoning and competing interpretation. `unknown` remains unknown and cannot silently become a
fact, requirement, route premise, or task premise.

A claim is **material** when being wrong could change scope, route, architecture, a public or
cross-module interface, acceptance, execution ordering, destructive/external authority, or the
reuse-versus-rebuild decision. Materiality is sticky. Downgrading a material claim requires new
direct evidence and independent confirmation. A corrected claim remains
`corrected_pending_confirmation` until a later complete valid critic round verifies it.

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

The critic returns:

- one coverage row for every material claim ID with
  `verdict: supported|refuted|insufficient|unreviewed`, raw evidence checked, and rationale;
- stable finding-family IDs, `material|residual` severity, affected claim IDs, direct evidence,
  alternative interpretation, and required investigation;
- explicit checks for missing material claims in each orientation category.

A result is complete and valid only when every existing material claim has exactly one coverage
row, every required category has been checked for omissions, evidence paths or command results are
inspectable, and the schema is well formed. An empty findings list, prose-only approval,
`unreviewed` row, or missing coverage cannot establish closure. The critic cannot accept a claim
merely because the artifact is well written.

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

Run round 1 always. Close after round 1 only if it is complete and valid, all material claims are
supported, no material claim is missing or unknown, and no material repair followed the verdict.
Run round 2 for any new/open material family or material repair needing confirmation. At the soft
limit, run round 3 only for an open/new material family or the single confirmation required by the
latest material repair. Never run round 4.

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

## Reporting And Resume

Persist the evidence map, critic verdicts, repairs, round ledger, final orientation status, and
source Git state. `state.json` must point to them so a resumed or cross-host run can verify whether
the baseline is still current.

If the source revision, relevant dirty paths, environment capability, or runtime configuration
changes before any downstream design or execution action, invalidate affected orientation claims
and every derived route, decision, spec, task, workflow, and launch artifact. Rerun the necessary
orientation investigation and independent review, then regenerate only the affected downstream
subgraph. Direct and diagnostic routes follow the same rule. Do not replay a valid orientation
gate merely to reconstruct conversation context.

The final execution report includes a compact list of corrected misunderstandings and unresolved
unknowns. Routine confirmed facts are referenced through `reviews/orientation.md`, not duplicated.

## Validation

Add contract tests for both Claude and Codex copies proving:

- Phase 0 routes through the orientation gate before Phase 1;
- the evidence map requires `observed|inferred|unknown`;
- the review budget is exactly mandatory 1, soft 2, hard 3;
- material repairs require independent confirmation;
- `orientation_blocked` prevents specs, tickets, and implementation;
- the gate does not ask for current-state facts or a new start approval;
- critic input proves fresh-context independence and requires inspection of raw repository
  evidence;
- goal-relative scoping prevents a compact route from becoming an unconditional repository audit;
- Claude and Codex artifacts remain in parity.

Run pressure tests against:

1. a plausible but wrong architecture summary contradicted by code;
2. tests that exist but execute zero relevant assertions;
3. stale docs that disagree with runtime behavior;
4. dirty worktree changes that alter the apparent baseline;
5. a round-3 material repair without confirmation;
6. unavailable external/runtime evidence that must remain `unknown`.
