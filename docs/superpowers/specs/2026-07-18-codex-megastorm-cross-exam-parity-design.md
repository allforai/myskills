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

Every judgment is atomically persisted to `ledger.json` immediately. Evidence
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

## Normative Operational Contracts

### Git baseline, refs, publication, and cleanup

The controlled baseline is the target repository's current `HEAD` commit at
preflight. Dirty tracked and untracked content is excluded because capturing it
would require staging, stashing, or copying user-owned state. If the goal depends
on dirty content absent from `HEAD`, preflight stops and asks the user to commit
it; the runner never chooses how to preserve it.

Each run has an immutable UUID. Internal refs use
`refs/megastorm/runs/<uuid>/{baseline,integration}` and worktrees live below a
run-owned temporary root. Ref creation and movement use compare-and-swap rules:
refs must be absent on first creation; resume must find the persisted object IDs;
and an update succeeds only if the old value equals the persisted expected value.
Missing, externally moved, or mismatched refs escalate and are never force-reset.

Successful close retains the integration ref and final commit, removes task
worktrees, and optionally creates a human-facing branch using a user-approved
name. An existing human-facing ref causes a closed failure rather than overwrite.
Cancelled or escalated runs retain internal refs, state, logs, and unmerged
worktrees required for diagnosis/resume. Explicit cleanup may delete only paths
under the recorded run root and refs under `refs/megastorm/runs/<uuid>/`; deletion
of the final handoff ref requires separate confirmation.

### Execution security envelope

Worktrees are not a complete security boundary. Unattended `codex exec` and
acceptance commands therefore run with workspace-write sandboxing, non-interactive
approval, closed stdin, bounded timeouts, captured output, and the task worktree
as cwd. They receive an allowlist of ordinary build variables plus only the
credentials or task variables explicitly approved in Phase 0. Ambient secrets
are not forwarded by default.

Network is disabled by default when the available sandbox can enforce it. A task
requiring network, credentials, destructive behavior, an external system, or a
write outside the worktree must declare the exact capability and target in Phase
0 and receive explicit authorization. Production targets, elevation, undeclared
external mutation, path/symlink escape, and capabilities the current sandbox
cannot safely constrain are refused or escalated. The preflight discloses when
the host cannot enforce the requested boundary instead of claiming safety.

Symlinks are resolved before repository-path policy checks. Submodules are
read-only by default; a writable submodule is a separate controlled repository
with its own baseline/ref lifecycle and an explicit touched resource.

### Event and summary durability

The JSONL event stream is the audit trail; the atomic JSON summary is the
authoritative resume snapshot. A single coordinator owns both files. Workers
return results through an in-process queue and never write persistent state.
Every event carries `run_id`, monotonic `seq`, stable `event_id`, task and attempt
IDs, timestamp, type, and payload.

The coordinator writes and `fsync`s a complete JSON line, then atomically
publishes a summary containing `last_applied_seq`. On recovery, an invalid or
unterminated final line is quarantined and ignored. Later valid events are
replayed only when their stable ID, payload hash, and expected pre-state make the
transition idempotent. Duplicate IDs with the same hash are ignored; conflicting
duplicates stop recovery as corruption. Merge-intent and merge-complete events
record expected parent and resulting Git object IDs, preventing duplicate merges.

### Reality-gate lifecycle

A reality-gated result is permitted only after the supervisor confirms the
code-side implementation and every autonomously executable check passed, with
only the declared environmental proof remaining. Its changes are committed and
merged exactly like a confirmed task. Only the merge-complete transition makes
dependents ready. The autonomous terminal state is
`implementation_merged_proof_pending`.

A later explicit import records a human runbook outcome as `human_verified` or
`human_rejected`, both with evidence. Verification closes the pending gate
without rerunning dependents. Rejection reopens the task as a business failure,
invalidates downstream confirmations, and requires a new planned execution; it
is never silently rewritten as done. A rejection marks every earlier final report
for that run as superseded. The follow-up run records the rejected integration
commit as its provenance and derives a new controlled baseline from an explicit
human choice, never by silently moving the old run ref.

### Cross-exam persistence and probe authorization

`ledger.json` is a versioned JSON snapshot written by whole-file temporary write,
`fsync`, and atomic replace; it is not append-in-place. Only the interactive
examiner writes it, under a run lock containing examiner PID and run UUID. Every
entry and open thread has a stable UUID. Resume deduplicates by UUID and content
hash, rejects conflicting duplicates, and quarantines unreadable snapshots.
Evidence files are durable before the snapshot references them. A concurrent
examiner refuses the active run instead of merging ledgers.

A lock is stale only when its recorded process start identity (PID plus platform
start-time token) is no longer live or its run UUID disagrees with the ledger.
Stale-lock takeover requires explicit user confirmation, archives the old lock,
and records a recovery event. PID reuse alone can never authorize takeover.

Audit-only forbids source fixes but does not imply that every runtime probe is
read-only. Intake records allowed hosts, accounts/tenants, operations, test-data
namespace, credential sources, and cleanup obligations. A mutating card displays
its exact side effect and rollback/cleanup plan and requires authorization before
dispatch. Shared valuable data, irreversible calls, production credentials or
hosts, and mutations outside the envelope are refused. Credentials go only to
the authorized prober, are redacted from logs, and are never copied into evidence.

### State machines

A task moves through `pending -> dispatched -> implementation_ready -> verifying`.
Verification transitions to `confirmed`,
`implementation_confirmed_proof_pending`, `business_retry`, or
`infrastructure_retry`. Retries return to `dispatched`; exhausted budgets become
`escalated`. Merge completion changes the proof-pending state to
`implementation_merged_proof_pending`. Only confirmed or proof-pending tasks
with a merge-complete event satisfy dependencies. Escalation makes nonterminal transitive dependents
`skipped`. Cancellation preserves nonterminal state and never creates success.

Each executor and supervisor attempt has a stable attempt ID. Business and
infrastructure counters are independent. Commit and merge transitions are
idempotent and keyed by expected parent/resulting object ID.

Cross-exam entries move through
`question_selected -> probing -> evidence_ready -> judged`. Infrastructure
redispatch retains the entry UUID and creates a new probe-attempt ID. Exhaustion
can become `judged:unprovable` only after a `could_not` evidence file exists.
Open threads are stable non-judgment records and become entries when selected.
Renderer admission is derived and never mutates the ledger.

### Exact compatibility and invalidation rules

- Missing `reality_gate` means `false`. A `runbook_ptr` is forbidden unless it
  is true; true without a non-empty pointer fails validation.
- Old DAGs without reality maps derive them from the task array.
- Old state without schema version or fingerprints is report-readable but not
  resumable; the user starts a new run from its recorded baseline.
- Task content changes invalidate that task and its transitive dependents.
- Effective dependency or ancestor-closure changes invalidate affected tasks.
- Executor prompt or BULK model changes invalidate unverified/executor-run work;
  supervisor prompt or VERIFY model changes invalidate all confirmations.
- Planning, registry, or THINK changes regenerate the plan and invalidate the
  entire execution plan.
- Integration baseline movement invalidates the complete execution run.
- Timeout, backoff, and report-format-only changes do not invalidate confirmed
  work.

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
external movement of run refs, ref-name collisions, symlink escapes, writable
submodule declarations, commands attempting writes outside task worktrees, and
resume. Before and after assertions must prove the user's checked-out branch,
HEAD, index, and pre-existing file content are unchanged. Durability tests inject
partial JSONL tails, duplicate/conflicting event IDs, concurrent Cross-exam lock
attempts, and crashes between event `fsync` and summary replacement.

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

Existing `orchestration.json`, plan-task arrays, and model files remain accepted
under the exact compatibility rules above.
State files gain an explicit schema version; unsupported or unsafe legacy state
is rejected with recovery instructions rather than guessed into the new format.

The previous default that permitted shared main-tree writers is not preserved as
normal behavior. If a temporary compatibility flag is necessary, it must be
explicit, prominently warn that isolation guarantees are disabled, and be
excluded from recommended documentation.
