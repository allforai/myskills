# Megastorm Unattended Decisions Design

## Goal

Megastorm front-loads human decisions in Phase 0. After Phase 0 it never pauses for a
new design choice, stage transition, model failure, oversized module, or non-convergent
agent. It chooses the recommended safe path, records the choice, continues all viable
work, and discloses every autonomous decision in the final report.

## Decision policy

Phase 0 freezes a decision envelope: goal, scope, permissions, destructive-action
limits, external-service authority, cost preference, model policy, and acceptance
criteria.

After Phase 0, every previously unseen decision is handled as follows:

1. Generate viable options.
2. Rank them by goal alignment, safety, reversibility, evidence, maintenance cost,
   and consistency with the existing repository.
3. Select the highest-ranked option that stays inside the Phase 0 authority envelope.
4. Persist the choice before acting.
5. Continue without asking the user.

Every fallback must also remain inside the Phase 0 authority envelope; reversibility
does not confer permission. If no option is authorized, Megastorm may collect
non-mutating evidence, records the item as `deferred`, skips only its dependent
subgraph, and continues all independent work. Lack of authority never grants authority
implicitly.

Ranking uses this stable order: authorized over unauthorized; non-destructive over
destructive; reversible over irreversible; existing repository convention over a new
pattern; fewer affected interfaces/files over more; stronger available evidence over
weaker; lower maintenance cost over higher; finally lexicographic option name as a
deterministic tie-break.

Phase 0 persists `decision-envelope.json` in the run directory. It contains the run ID
and frozen fields for scope, allowed write roots, destructive operations, external
systems, network, secrets/environment variables, spending, model substitutions, and
acceptance authority. An `inside-envelope` decision must cite the controlling field and
value.

## Decision ledger

The run owns `<run-dir>/decision-ledger.json`, updated by atomic replacement. It is
initialized before Phase 1 and reused on resume. The main orchestrator is the only
writer and allocates monotonically increasing IDs under a run-scoped single-writer
lock. Workers return schema-bound decision proposals through their normal result
channel. The orchestrator persists the accepted entry before acting; persistence
failure retries atomic replacement three times, then writes and fsyncs a minimal entry
to `<run-dir>/decision-emergency.ndjson`. An emergency-journaled decision may only be
deferred; its proposed action is not performed, while independent work continues. If
both ledger and emergency journal are unwritable, the run performs no further
mutations and transitions directly to a degraded Phase 2 terminal report from memory;
it does not ask for a decision or wait for approval. Each entry contains:

```json
{
  "decision_id": "D-001",
  "run_id": "stable-run-id",
  "phase": "1.3",
  "branch_id": "module-or-task-branch",
  "task_id": "task-id-or-null",
  "question": "decision that arose",
  "options_considered": ["option A", "option B"],
  "chosen": "option A",
  "reason": "why it ranked highest",
  "assumptions": ["assumption"],
  "risk": "low|medium|high",
  "reversible": true,
  "authority": "inside-envelope|deferred",
  "authority_basis": {
    "field": "external_systems",
    "value": ["staging-api"]
  },
  "fallback": "fallback used or null",
  "outcome": null,
  "result_ref": null,
  "affected_artifacts": ["path-or-interface"],
  "skipped_dependents": ["task-id"]
}
```

`outcome` is nullable before execution; its terminal enum is
`action-taken|fallback-taken|deferred`. `result_ref` is nullable before execution and
becomes a string referencing the event, artifact, or skip record that proves the
terminal outcome.

The unified **decision record** abstraction includes normal ledger entries, emergency
journal entries, and degraded in-memory terminal records. Every unseen decision must
map one-to-one to a decision record and then to
exactly one observable outcome: action taken, authorized fallback taken, or branch
deferred with its complete skipped-dependent list. The entry is first persisted with
`outcome:null` and `result_ref:null`; after execution the single writer atomically
updates both fields with the final outcome and proof reference. Recovery treats a null
outcome as not executed and safely reconciles it from run events before any retry.
Phase 2 merges all three record sources, labels their durability, and reports each
exactly once.

## Pipeline behavior

- Stages 1.1–1.5 convert `status:"escalate"` into an autonomous decision cycle rather
  than a human halt.
- Missing registry interfaces may be added only when existing specs/code provide
  evidence for the exact contract and the change stays inside the frozen scope.
  Otherwise defer that branch.
- Oversized modules are split at the first stable boundary in this order: existing
  package/component boundary, independent acceptance boundary, non-cyclic interface
  cut, then lowest cross-boundary touched-path count. If every split changes
  user-visible scope, defer the excess branch. Equal candidates use canonical
  boundary/path name as the final stable tie-break.
- Repeated model/infrastructure failure uses the Phase 0 model policy; if unavailable,
  the affected branch is recorded and skipped without stopping the run.
- Execution failures retain existing retry, evidence, and transitive-skip semantics.
- Phase completion is a checkpoint, never a user-interaction boundary.
- Reality gates do not stop dependent implementation that is authorized, reversible,
  and has no irreversible/external effect. Such outputs remain explicitly unverified.
  Dependents requiring external, destructive, financial, or irreversible action are
  deferred until proof exists.

**No-pause invariant:** after Phase 0 no code path may ask a question, request input,
wait for approval, invite a follow-up workflow, or return control merely because a
stage completed or a choice is unresolved. Every Phase 1 exit path must instead produce
a unified decision record and either continue the pipeline or skip only the
affected branch. Phase 2 is the next normal user interaction.

## Final report

Phase 2 must include:

- **Autonomous decisions**: every unified decision record, its durability source,
  chosen option, rationale, risk, and affected artifacts.
- **Assumptions made**: deduplicated assumptions introduced after Phase 0.
- **Deferred by authority boundary**: unauthorized work, safe fallback used, and every
  skipped dependent.
- Existing verification, escalation, reality-gate, and completeness accounting.

The report ends the run. It does not invoke or suggest another interactive workflow.

## Scope

Implement this behavior in the Claude and Codex Megastorm variants. Remove the Grok
Megastorm variant in full at the user's request; Git history remains the recovery path.

## Validation

- Static checks cover every human-input mechanism and Phase 1 exit path: no question,
  request-for-input, approval wait, interactive invitation, or stage-boundary return.
- Prompt checks require decision proposals instead of instructions to ask the human.
- Existing deterministic runner tests continue to pass.
- New checks assert the decision-ledger contract and mandatory Phase 2 sections.
- Tests assert one-to-one accounting from decision proposal to unified decision record to
  action/fallback/defer outcome and final-report row, including authority denial,
  model failure, oversized modules, persistence failure, registry gaps, and reality
  gates. They cover null pre-execution fields, recovery to terminal fields, emergency
  records, and degraded in-memory records.
- No tracked file remains under `grok/megastorm/`.
