# Grillstorm Evidence-Backed Orientation Grill

## Goal

Prevent Grillstorm from entering product decisions, specifications, ticket generation, or
implementation with a mistaken model of the repository's current state.

The startup phase must investigate first, explicitly distinguish observation from inference, and
survive independent adversarial cross-examination. This is an internal evidence gate, not another
user approval or a broad interview.

## Position In The Workflow

Add an orientation-closure gate inside Phase 0 after repository/environment discovery and route
selection, but before Phase 1 asks product questions.

```text
inspect repository and runtime
-> build current-state evidence map
-> independent fresh-context orientation Grill
-> repair misunderstandings and missing evidence
-> independent confirmation
-> begin user decision Grill
```

The gate applies to every route. Compact routes may use a compact artifact, but they may not skip
the reasoning or evidence requirements.

## Current-State Evidence Map

Persist `reviews/orientation.md` for a program run, or the equivalent structured state entry for a
compact route. It records:

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
  "status": "open|verified|corrected|unknown"
}
```

`observed` requires direct repository, command, history, or runtime evidence. `inferred` names the
reasoning and competing interpretation. `unknown` remains unknown and cannot silently become a
fact, requirement, or task premise.

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

The critic returns stable finding-family IDs, severity, affected claim IDs, direct evidence,
alternative interpretation, and required investigation. It cannot accept a claim merely because
the artifact is well written.

## Repair And Review Budget

Orientation review has:

| Mandatory rounds | Soft limit | Hard limit |
|---:|---:|---:|
| 1 | 2 | 3 |

A round starts with critic dispatch and consumes the round even if the critic fails or returns an
invalid result. One infrastructure retry may complete the same round.

The investigator resolves findings by inspecting more raw evidence, running safe diagnostics, and
correcting or downgrading claims. Rewording the same root cause is the same finding family.
Material repairs require a fresh independent confirmation round when budget remains.

Close only when a complete valid critic round confirms:

- every scope-, architecture-, interface-, acceptance-, or execution-affecting claim is verified
  or explicitly unknown;
- no material contradiction or misunderstood baseline remains;
- unknowns are visible inputs to the later decision Grill rather than hidden assumptions.

If round 3 ends with an unresolved material conflict, invalid review, or unconfirmed material
repair, record `orientation_blocked`. Do not begin product questioning, specification, ticket
generation, launch, or implementation.

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
changes before task execution, invalidate affected orientation claims and rerun only the necessary
orientation review before continuing. Do not replay a valid orientation gate merely to reconstruct
conversation context.

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
- Claude and Codex artifacts remain in parity.

Run pressure tests against:

1. a plausible but wrong architecture summary contradicted by code;
2. tests that exist but execute zero relevant assertions;
3. stale docs that disagree with runtime behavior;
4. dirty worktree changes that alter the apparent baseline;
5. a round-3 material repair without confirmation;
6. unavailable external/runtime evidence that must remain `unknown`.
