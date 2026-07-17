# Codex Megastorm and Cross-exam Parity Design

## Goal

Bring the Codex implementation to behavioral parity with the Claude Megastorm
v0.14.0 protocol, add Cross-exam as an independent Codex skill, and harden the
Codex execution runner for safe unattended operation.

Parity means equivalent contracts, evidence standards, failure semantics, and
reporting outcomes. It does not mean copying Claude Code's Workflow APIs,
plugin manifests, slash commands, or directory layout. The implementation must
use Codex-native skills, fresh `codex exec` processes where appropriate, and
Codex multi-agent support for independent Cross-exam probing.

## Scope

This change covers three related deliverables:

1. Extend `codex/megastorm-skill/` from its current v0.3.0 protocol to the
   capabilities present in Claude Megastorm v0.14.0.
2. Add an independent `codex/cross-exam-skill/` that can audit any delivery and
   can optionally consume Megastorm artifacts.
3. Replace unsafe runner behavior with isolated execution, protected user Git
   state, controlled processes, durable state, and auditable events.

The change does not introduce a shared Claude/Codex runtime, automatically run
Cross-exam after Megastorm, perform fixes during Cross-exam, or silently choose
or downgrade models.

## Chosen Approach

Incrementally extend the existing Codex implementation. Preserve its tested
deterministic gates, prompt contracts, and execution runner interfaces while
adding the missing protocol and reliability behavior.

This is preferred over a full orchestrator rewrite because the existing runner
already implements dependency-ready scheduling, mutexes, retries, supervision,
and resume behavior. It is preferred over a literal file port because Codex and
Claude expose different orchestration primitives.

## Package Architecture

```text
codex/
├── megastorm-skill/
│   ├── SKILL.md
│   ├── AGENTS.md
│   ├── execution-playbook.md
│   ├── models.example.json
│   ├── schemas.md
│   ├── prompts/
│   └── scripts/
│       ├── run_layers.py
│       ├── deterministic gates
│       └── focused runner support modules as needed
└── cross-exam-skill/
    ├── SKILL.md
    ├── AGENTS.md
    ├── lenses.md
    ├── schemas.md
    ├── prompts/prober.md
    └── scripts/render_report.py
```

The skills communicate through files, not imports or hidden session state.
Cross-exam may read a Megastorm registry and report but remains fully usable
with a spec, README, user-provided baseline, or no baseline.

## Megastorm Protocol Parity

### Environment capability probe

Phase -1 must probe the environment before planning acceptance work. The
overview records these capabilities as `available`, `flaky`, or `absent`:

- real or stable headless display for UI and E2E;
- device simulator or emulator availability and boot stability;
- reachable real hardware or physical I/O;
- reachable shared/external systems and required credentials.

The plan agent uses this matrix to mark work that cannot be autonomously proven
in the current environment. A plan must not claim an unavailable proof method.

### Census requirement for class-elimination goals

Phase 0 must distinguish ordinary feature goals from goals that claim to remove
or enforce an entire class of behavior. Examples include eliminating every fake
success, connecting every operation to a real effect, or finding every unused
contract endpoint.

For a class-elimination goal, planning begins from an exhaustive census artifact
rather than a smell-based search. Every population member must be dispositioned
as either:

- mapped to one or more implementation tasks; or
- `verified-clean` with concrete evidence.

The overview records census method, population size, and disposition counts. If
the task set was derived from an audit or its derivation is unknown, the final
report must state `Completeness unverified` and must not say that the class was
eliminated.

### Reality-gated work

Plan tasks may add:

```json
{
  "reality_gate": true,
  "runbook_ptr": "docs/path.md#human-verification"
}
```

A reality-gated task receives at most one autonomous acceptance attempt. If the
supervisor determines that implementation exists but proof requires unavailable
hardware, external systems, or human observation, it returns a structured
`reality_gated` outcome with a reason. This outcome:

- does not consume a business soft retry;
- does not transitively skip dependents;
- is not counted as an autonomous verification or as a failure;
- is recorded in a dedicated reality-gate ledger;
- appears with its concrete runbook in the final report.

An implementation defect remains an ordinary rejection or escalation even when
the task carries `reality_gate: true`.

### Failure taxonomy

The runner separates three categories:

- Business failure: executor or acceptance behavior is incorrect. It consumes
  the existing soft-retry budget.
- Infrastructure failure: CLI crash, provider/network failure, timeout, quota
  exhaustion, missing output, or malformed transport result. It uses a separate
  retry counter and configurable backoff and does not consume the business
  retry budget.
- Reality-gated proof: implementation is available but this environment cannot
  prove its real-world behavior. It is recorded without retry or dependency
  blocking.

After the configured infrastructure attempts are exhausted, the task escalates
with `failure_kind: infrastructure`. Infrastructure retry defaults and timeout
values must be configurable and visible; they must never silently change model
tiers.

### Execution and final reporting

Execution retains dependency-ready scheduling, resource mutexes, independent
executor/supervisor contexts, transitive skipping after genuine escalation, and
continued execution of unrelated work.

Phase 2 must render:

- supervisor-confirmed work separately from executor claims;
- every escalation with reason, evidence, retry history, and complete skipped
  chain;
- counts in the form `N verified / M reality-gated / K escalated / S skipped`;
- a Reality Gate section with reason and `runbook_ptr` for every pending proof;
- a Completeness Confidence section stating whether coverage was census-backed,
  audit-based, or unknown;
- DAG warnings, derived edges, assumptions, and approved model deviations;
- an invitation to run the independent Cross-exam skill.

For class-elimination goals, census reconciliation or Cross-exam sweep is a
completion gate. A green task count alone cannot prove full class coverage.

## Safe Runner Design

### Git isolation

The runner must not execute concurrent writers in the user's main worktree and
must not use `git add -A && git commit` to capture arbitrary pre-existing user
changes.

At startup it records the user's current branch, HEAD, worktree status, and a
content fingerprint for existing modifications. It creates a Megastorm-owned
integration branch/worktree from a controlled baseline. Every writing task runs
in its own task worktree derived from the latest eligible integration state.

Task flow is:

1. create an isolated task worktree;
2. run executor in that worktree;
3. capture the actual diff and compare it with declared `touched_paths`;
4. run the fresh supervisor against the task worktree;
5. commit only the task worktree's changes;
6. merge confirmed work into the integration branch under a merge lock;
7. publish the final integration branch and commit without checking it out over
   the user's current branch.

Existing dirty state remains in the user's worktree and is never staged or
committed by Megastorm. If Git cannot create a safe baseline without modifying
that state, preflight stops with an actionable explanation rather than stashing
or committing it implicitly.

All writers use worktrees by default. The old shared-main-tree `run_free` path is
removed from normal execution. Merge conflicts and unexpected repository state
become structured escalations; the runner does not resolve conflicts by guessing.

### Touched-path enforcement

After execution, actual changed paths are compared with task declarations:

- declared changes proceed;
- reasonable generated or mechanically related changes are recorded and checked
  for newly introduced conflicts before supervision/merge;
- sensitive or clearly unrelated changes escalate;
- a task with no substantive change is explicitly presented to the supervisor,
  which may accept it only when the task demonstrably required no repository
  mutation.

Path comparison must handle renames, deletions, untracked files, and normalized
repository-relative paths. Paths escaping the repository are invalid.

### Process lifecycle

Each executor and supervisor invocation has a configurable timeout. Child
processes run in a process group so cancellation can terminate descendants.
Timeout or user interruption sends a graceful termination first, then forcefully
terminates after a bounded grace period.

On Ctrl-C, the scheduler stops dispatching new work, terminates active agent
processes, persists state atomically, records a cancellation event, and leaves
enough metadata to resume or explicitly clean up worktrees. It must not report
the run as completed.

### Durable state and events

State files use write-to-temporary plus `os.replace()` for atomic publication.
State includes schema and runner versions plus fingerprints of:

- task definitions;
- effective DAG;
- relevant prompts;
- model configuration;
- controlled integration baseline.

On resume, unchanged confirmed tasks remain valid. A changed task invalidates
itself and its downstream dependents. A changed prompt/model policy or baseline
invalidates tasks according to a documented conservative rule. Already merged
tasks must never be merged twice.

An append-only JSONL event log records dispatch, executor completion,
supervisor verdict, retry classification, reality gating, confirmation,
escalation, skip propagation, commit, merge, cancellation, and resume. Summary
state and final reports are derived from structured records rather than terminal
narrative alone.

The existing CLI and old task/DAG inputs remain readable. Safer isolation and
durability behavior become the default; deprecated unsafe options, if retained
for migration, must require explicit opt-in and warning.

## Cross-exam Skill

### Invariants

Cross-exam is interactive, audit-only, generic, and evidence-backed.

- It records findings but never fixes them.
- It runs only while the user is present.
- Every observation is gathered by a fresh-context independent prober.
- The main examiner may judge evidence but may not impersonate the prober.
- The completion report is generated only by the deterministic renderer.

### Independent-agent hard gate

Before intake, the skill verifies that the current Codex harness can dispatch a
fresh-context independent sub-agent. If it cannot, Cross-exam stops and explains
that independent evidence collection is unavailable. It must not fall back to
self-review or use `codex exec` merely to simulate the required harness-level
independence.

Each prober receives only:

- the concrete question;
- target and access information;
- states to capture;
- an evidence directory;
- optional context paths without the examiner's interpretation.

The examiner's suspicion, desired verdict, conversation history, and severity
expectation are excluded from the prober input.

### Intake and safety

Intake determines the target, how to run it, the evidence baseline, environment
capabilities, and whether runtime/screenshots are possible. Baseline discovery
order is Megastorm registry, related specs, README, user-provided requirements,
then no-baseline mode.

No-baseline mode disables requirement-coverage and requirement-drift judgments
while retaining integration-seam, detail-quality, and contract-census lenses.

The user must confirm the target is local or a development/test environment
before probes may cause real calls. Production systems and destructive real-world
operations are refused. Missing runtime or screenshot capability is disclosed
before examination and may produce `unprovable` outcomes rather than invented
evidence.

Each run uses `docs/cross-exam/<date>-<target-slug>/`. If an unfinished run exists,
the user chooses whether to resume it or start a new run. Resume loads entries,
facets, and `open_threads`.

### Facet discovery and modes

A fresh-context census prober first enumerates the delivery's operation and
contract surface using a coverage method. Its result is merged with examiner-
identified facets and deduplicated. Facets found only by the census are marked
so hidden examiner blind spots remain visible.

The user chooses facets and priority. Unselected facets are recorded as
`not_examined`, risk-ranked, and excluded from completion counts.

Cross-exam supports:

- Deep-dive mode: the examiner presents three independently testable question
  cards for one facet; the user chooses one for a fresh prober.
- Census-sweep mode: for completeness and class-elimination goals, independent
  probers cover the enumerated population, followed by deep dives on high-risk
  findings.

Each question card names the question, triggering leak point, illuminated facet,
and, for UI flows, required states such as loading, empty, error, and success.
Unselected cards are immediately stored in `open_threads`. When later examined,
they move into ledger entries.

### Evidence and judgments

Probers write raw runtime, code, ledger, screenshot, or `could_not` evidence into
the assigned directory and report observations without verdicts. Prober death or
timeout receives one infrastructure re-dispatch; a second failure produces a
reason file and an `unprovable` judgment rather than fabricated evidence.

The examiner assigns one of:

- `done`: evidence demonstrates the requirement or behavior;
- `gap`: observed behavior contradicts completion;
- `drift`: implementation exists but differs from the intended requirement;
- `unprovable`: the available environment cannot establish the result.

`gap` and `drift` require `high`, `medium`, or `low` severity. When the examiner
also authored the delivery, downgrading a gap to low or judging it done requires
additional independent evidence.

Every judgment is atomically appended to `ledger.json` immediately. Evidence
must be non-empty, reside under the run's `evidence/` directory, and be referenced
by the entry. The renderer rejects invalid verdicts, missing evidence, empty
evidence, and path escape. Rejected entries are disclosed but excluded from all
counts.

### Deterministic report

`render_report.py` is the only supported report generator. Its report contains:

- baseline and disabled-lens disclosure;
- verdict counts and per-facet `X examined / Y evidenced done` summaries;
- evidence-linked gap and drift lists ordered by severity;
- unprovable items;
- risk-ranked unexamined facets;
- unresolved `open_threads`;
- rejected/invalid judgment disclosure.

It does not invent a global completion percentage. Reports remain audit outputs,
not implementation plans or authorization to fix findings.

## Error Handling

All externally visible failures use structured categories and preserve evidence:

- preflight/configuration errors stop before mutation;
- infrastructure errors retry under their own budget and then escalate;
- business failures use the soft-retry ledger;
- reality-gated proof becomes pending human verification;
- Git isolation or merge failure escalates without modifying the user's branch;
- malformed agent output is re-requested once, then classified and recorded;
- invalid Cross-exam evidence is rejected by the renderer and surfaced;
- cancellation persists a resumable non-complete state.

No error path may silently downgrade a model, convert unprovable work into done,
discard a skipped chain, or delete evidence needed for audit.

## Testing Strategy

### Unit tests

Cover schema validation, verdict parsing, path normalization, changed-path
classification, input fingerprints, atomic state writes, infrastructure failure
classification, reality-gate ledger behavior, resume invalidation, and report
rejection rules.

### Runner integration tests

Use a fake Codex command to simulate success, business rejection, timeout, empty
output, malformed output, process crash, infrastructure recovery, cancellation,
and resume. Verify independent retry budgets and exact terminal accounting.

### Git isolation tests

Exercise dirty user worktrees, untracked files, concurrent tasks editing the same
file, undeclared changes, renames/deletions, merge conflicts, interrupted merges,
and resume. Before and after assertions must prove the user's checked-out branch,
HEAD, index, and pre-existing file content are unchanged.

### Protocol parity tests

Maintain a parity matrix and fixtures for Claude v0.14 and Codex semantics:

- environment capability classification;
- census-backed versus audit-based completeness;
- reality-gated task handling;
- business versus infrastructure failure;
- escalation and complete transitive skip accounting;
- Cross-exam evidence acceptance/rejection;
- unexamined facets and open threads;
- deterministic final reporting.

Parity fixtures compare contract-level outcomes, not host-specific invocation
syntax.

## Completion Criteria

- All existing Codex Megastorm tests continue to pass.
- New parity and reliability tests pass.
- A documented parity matrix has no unexplained Claude v0.14 capability gaps.
- Cross-exam refuses to run without an independent fresh-context agent.
- Invalid or evidence-free judgments never enter report counts.
- Running from a dirty worktree leaves the user's branch, HEAD, index, and prior
  modifications unchanged.
- Interrupted runs resume from a consistent state without duplicate merges.
- Class-elimination reports without a census explicitly state
  `Completeness unverified` and never claim full elimination.
- Documentation explains installation, invocation, model selection, recovery,
  cleanup, migration, and the boundary between autonomous verification and human
  reality-gate verification.

## Migration and Compatibility

Existing `orchestration.json`, plan-task arrays, and model files remain accepted.
New fields are optional when reading old data and receive conservative defaults.
State files gain an explicit schema version; unsupported or unsafe legacy state
is rejected with recovery instructions rather than guessed into the new format.

The previous default that permitted shared main-tree writers is not preserved as
normal behavior. If a temporary compatibility flag is necessary, it must be
explicit, prominently warn that isolation guarantees are disabled, and be
excluded from recommended documentation.

