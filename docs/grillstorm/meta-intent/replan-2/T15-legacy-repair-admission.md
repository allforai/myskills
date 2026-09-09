# T15 — legacy repair admission

Closes the last opening the previous dispatch (ctx_fbb91465b558) left behind and recorded as
residual: a project with no freshness state returned `freshness: null`, `qa_inputs_current`
read that as "the pre-freshness gate applies", and a touched leftover report could still open
an automatic repair. That was not accepted. Scope here is
`codex/meta-skill/knowledge/flow-template.py`, `codex/meta-skill/test_flow.py` and the
repair-loop section of `codex/meta-skill/knowledge/orchestrator-template.md`. The shared gates,
readiness, `product_intent.py` and `evidence_freshness.py` belong to the planning worker
(ctx_a377a4a12a25) and are read, never written. No commit.

> `msg_41234c8c8e94` was not in this dispatch's inbox (`check --all` returns zero messages), so
> the work follows the TASK block's statement of it; that was reported as `msg_4d64889a8c13`
> before anything changed.

## Two defects, not one

The dispatch opened on the `freshness: null` bypass. Reviewing the first fix, the
coordinator found a second one in it (`msg_0d59755f36a2`): the positive migration test bound
inputs *after* the report and the failed transition already existed, so a contract
observation laundered a historical report into an admissible one with no new QA execution.
That is the same bypass wearing a different hat, and it was accepted rather than argued.
Four further requirements followed. A fresh re-run reaching the same verdict must not be
denied (`msg_6295fe138aab`); the attempt must be tied to one identified input snapshot rather
than two independent currentness answers (`msg_cc97b459c5d6`); the digest-or-write-time rule I
proposed for the first of those was reproduced as still admitting a touched leftover and was
withdrawn (`msg_ce0a4299cb8a`, `msg_7cc9c3e5e00c`); a node that once published passing evidence
must not be denied forever by that stale snapshot (`msg_fb2d6278463c`); and the routing
regressions must exercise the real selector rather than a forced one (`msg_7b76fd060073`). All
of it is closed below.

## Defect 1 — absence of proof read as permission

Two different questions were being answered by one predicate:

- **May this node complete?** Legacy semantics, unchanged. `check_artifacts.freshness_admits`
  still admits a legacy node's `undeclared`, and a project with no freshness state still
  completes on the pre-freshness gate exactly as before. Nothing in this change touches it.
- **May this run automatically start a repair on the strength of a report?** That is work the
  driver begins unattended, for which a report is the entire justification. Here the absence
  of proof is not permission. `freshness: null`, a `legacy` node's `undeclared`, a `missing`
  or `invalid` declaration, an `uncertain` status and an undecided `external` change all
  refuse the route now; only `admission: declared` with no input drift admits it.

A refused QA node is not stranded: it is re-run, exactly as an unreadable or non-QA report
already was, and consecutive failures reach the driver's diagnosis threshold and stop under
the recorded Run Policy. That is the same route every other unrepairable QA failure takes.

## Defect 2 — a binding published after the fact

`qa_inputs_current` answers "do the node's inputs still stand", and that is all it can
answer. It says nothing about *which attempt wrote the report* — so when the inputs never
moved, or were observed after the fact, it is satisfied by a report from any era. The
comment claiming a touched file necessarily fails freshness was simply wrong, and is gone.

The missing half is proof that the attempt produced its own verdict, and the driver is the
only thing that can witness it. `flow.py` now brackets every declared QA node's attempt,
measuring each exit artifact's digest and write time plus the node's input-snapshot identity
before it runs and again after, and writes `qa_evidence` on the failed transition it appends:

```json
"qa_evidence": {"binding": "<sha256 of the observed input snapshot>",
                "produced": {"verify.json": "<sha256>"},
                "ambiguous": ["some-other-report.json"]}
```

Admission requires a non-empty `produced` whose digests still match disk, a `binding` that is
still the node's current snapshot identity, and the verdict itself to come from an artifact in
`produced`. The consequences:

- **A leftover cannot be touched into a verdict.** An artifact counts as produced only when
  its *content* changed between the driver's two measurements. An intermediate version of
  this fix admitted a write-time change as well, to keep byte-identical re-runs working; the
  coordinator's read-only probe (`msg_7cc9c3e5e00c`) showed that `os.utime` inside the
  executor window then reopens the exact bypass being closed, so that rule was withdrawn
  rather than defended. `test_an_executor_that_only_touches_the_report_does_not_dispatch_repair`
  drives `flow.main()` with an executor whose entire body is `os.utime` and pins it.
- **Unchanged content is diagnosed, not guessed.** A node that re-ran and reached the same
  verdict is indistinguishable from a file nobody wrote. The attempt records `ambiguous` and
  the error line says so, the route stays shut, and repeated failure reaches diagnosis. The
  supported way to repeat a verdict is for the QA node to name the attempt that reached it —
  a run identifier in the report makes the same finding twice two distinct verdicts, which
  `test_a_repeated_verdict_carrying_its_attempt_identity_opens_the_repair` exercises.
- **One snapshot, not two answers.** `binding` names the observation itself. Two independent
  "inputs are current" answers can describe *different* inputs if a source changed and was
  re-observed between them; comparing identities cannot. The driver keeps the identity only
  when it was the same at both ends of the attempt, and admission compares it again, so a
  republish during *or* after the attempt closes the route rather than reopening it.
- **A report edited or replaced after the attempt that wrote it** no longer matches its digest.
- **Old passing evidence is not a permanent veto.** Currency is read from `readiness_status`,
  not `status`: `status` tracks published evidence, which a failing QA node has none of, so
  requiring it would refuse every repair the loop exists for. `readiness_status` is the
  contract-level answer, and `binding_identity` prefers a freshly observed contract over an
  older evidence record for the same reason. A node whose inputs moved after it once passed
  recovers by observing its contract against the inputs as they are now.
- **The worker cannot file its own evidence.** The driver overwrites `qa_evidence` on the
  entry it finalizes and keeps that entry as the node's latest transition, dropping any the
  worker appended behind it. A transition with no `qa_evidence` — an older log, or one written
  by something else — carries no proof and does not qualify.

## Recovering a legitimate legacy repair

Refusing the route is only defensible with a way back, so the orchestrator template now
carries one ("Recovering a legacy node's repair route"), and the tests execute it:

1. Declare the node's inputs in `workflow.json` — `source_inputs` (explicit `[]` when no
   product source applies) and `input_dependencies` for the files it reads.
2. Observe and publish the node once through the generated helper:
   `evidence_freshness.py` `{"operation":"observe", "node_id":…, "kind":"contract"}` then
   `{"operation":"publish", "observation":…, "verification_command":[…]}`.
3. Let the QA node **run again**. The binding applies to attempts that start after it, so
   the route opens on that attempt's own report — never on the one already sitting on disk
   when you observed. If an input moves afterwards, the route closes until the node is
   reobserved.

`kind: "contract"` matters: a failed QA node can never publish *evidence*, so a contract
observation is what binds it. The template also says plainly that step 1 belongs at planning
time and is a migration for retained history, not a way to open a route for work that never
declared what it judges.

## Verification

Written test-first, against the real helpers rather than a stub. `legacy_project` copies the
shipped `check_artifacts.py` and `evidence_freshness.py` into a scratch project with no
declarations and no freshness state; `flow.node_freshness` returns `None` there, which the
first test pins as the real legacy shape rather than assuming it.

New public-driver regressions:

- `test_a_legacy_project_reports_no_freshness_at_all` — pins `freshness: null` at the seam.
- `test_a_touched_legacy_report_does_not_dispatch_automatic_repair` — the required negative.
  It first asserts the report *does* state a verdict and this run *did* record a failed
  attempt, so the refusal is attributable to the missing proof and nothing else.
- `test_observing_a_legacy_node_does_not_launder_its_old_report` — the case the coordinator
  rejected, now a rejection test. It asserts `qa_inputs_current` is `True` after the real
  observe/publish, and that the route stays shut anyway, so it pins the distinction rather
  than an accident.
- `test_a_rerun_after_observing_restores_the_legacy_repair_route` — the real positive: the QA
  node runs again after the binding, and the repair answers *that* attempt's verdict. It
  asserts the recorded `qa_evidence` too.
- `test_a_bound_node_does_not_pass_on_mtime_alone` — declared inputs that never moved, an old
  report merely touched, a later failed dispatch. Every timestamp lines up and the freshness
  predicate is satisfied; the route stays shut because the attempt produced nothing.
- `test_a_report_edited_after_the_attempt_that_produced_it_is_refused`.
- `test_an_observed_legacy_node_still_loses_the_route_when_its_inputs_move` — the recovery is
  a binding, not a permanent waiver.
- `test_the_driver_records_what_a_qa_attempt_produced` — drives `flow.main()` with the real
  helpers through a controlled executor seam: one attempt writes a failing report, the next
  writes nothing, and the recorded transitions carry the snapshot `binding` with the report's
  digest, then `produced: {}`.
- `test_a_byte_identical_rerun_is_recorded_as_ambiguous_not_produced` and
  `test_a_repeated_verdict_carrying_its_attempt_identity_opens_the_repair` — the legitimate
  case `msg_6295fe138aab` asked for, resolved the way `msg_ce0a4299cb8a` required: the
  ambiguity is recorded and diagnosed, and an attempt identifier is the supported way through.
- `test_an_executor_that_only_touches_the_report_does_not_dispatch_repair` — the `flow.main()`
  negative from `msg_ce0a4299cb8a`.
- `test_an_input_changed_and_reobserved_during_the_attempt_is_refused` — the source moves and
  is republished mid-attempt; both currentness answers say yes and the route still closes.
- `test_reobserving_after_the_attempt_does_not_revalidate_its_report` — the same on the
  admission side: re-observing afterwards binds a different snapshot, not the old verdict.
- `test_a_worker_cannot_supply_its_own_attempt_evidence` — drives `flow.main()` with a worker
  that appends two forged transitions carrying its own `qa_evidence`; the driver's own entry
  is what survives, and no repair opens.
- `test_a_node_that_once_passed_is_not_denied_forever_by_its_stale_evidence` and
  `test_a_declared_node_whose_contract_is_current_admits_despite_unpublished_evidence` — the
  `msg_fb2d6278463c` case: publish passing evidence, move the inputs, reobserve the contract,
  and the binding is current again. What still holds the route there is the separate
  external-change gate, which the test names rather than works around.
- `test_real_routing_never_executes_repair_for_a_touched_leftover` and
  `test_real_routing_repairs_then_reruns_qa_before_closure` — the `msg_7b76fd060073` case:
  `flow.main()` with the **real** `first_pending_node`, wrapped by a spy rather than replaced,
  recording the node ids the driver actually selected and executed. The touch-only run never
  reaches `repair`; the genuine one executes `verify`, `repair`, `verify` in that order and
  only then `accept`.
- `test_automatic_repair_needs_positive_input_proof` — seven states that claim no provenance,
  including `legacy`/`undeclared`, all refuse.

`gate_by_ready_artifacts` now stubs `node_freshness` to a bound declared state
(`{'admission': 'declared', 'status': 'stale', 'diff': {'evidence': 'unpublished'}}`) instead
of `None`, because those fixtures test routing, budgets and closure, not provenance; its
docstring says so.

Exact commands and observed results, working tree:

```
python3 -m pytest codex/meta-skill/test_flow.py -q --tb=short             89 passed (was 63)
node --test 'claude/meta-skill/knowledge/run-engine/tests/**/*.test.js'   82/82 pass
```

**Red before each fix**, in scratch copies — scratch only, no shared file swapped. Two
baselines, one per defect:

```
# defect 1: qa_inputs_current reverted to admitting null and legacy/undeclared
cd <scratch>; python3 -m pytest codex/meta-skill/test_flow.py -q --tb=no   6 failed, 68 passed

# defect 2: the attempt-evidence checks removed, every artifact counted as produced
cd <scratch>; python3 -m pytest codex/meta-skill/test_flow.py -q --tb=no   5 failed, 73 passed

# the follow-ups: content-only produced, a boolean instead of a snapshot identity,
# and no latest-transition guard
cd <scratch>; python3 -m pytest codex/meta-skill/test_flow.py -q --tb=no   5 failed, 77 passed

# the withdrawn rule (digest-OR-write-time, no ambiguity) plus diff-parsed currency
cd <scratch>; python3 -m pytest codex/meta-skill/test_flow.py -q --tb=no   6 failed, 83 passed
```

The first baseline fails `test_a_touched_legacy_report_does_not_dispatch_automatic_repair`,
the migration test, and `test_automatic_repair_needs_positive_input_proof[None]` and
`[freshness2]`. The second fails `test_observing_a_legacy_node_does_not_launder_its_old_report`,
`test_a_bound_node_does_not_pass_on_mtime_alone` and
`test_a_report_edited_after_the_attempt_that_produced_it_is_refused`. The third fails
`test_reobserving_after_the_attempt_does_not_revalidate_its_report` and
`test_a_worker_cannot_supply_its_own_attempt_evidence`. The fourth, against the withdrawn
digest-or-write-time rule and the diff-parsed currency it replaced, fails
`test_a_byte_identical_rerun_is_recorded_as_ambiguous_not_produced`,
`test_an_executor_that_only_touches_the_report_does_not_dispatch_repair`,
`test_real_routing_never_executes_repair_for_a_touched_leftover` and
`test_a_node_that_once_passed_is_not_denied_forever_by_its_stale_evidence`. In all four runs the other two,
`test_canonical_entry_is_resolvable` and `test_standalone_installer_keeps_canonical_entry`,
fail only because that scratch holds a partial tree; both pass in the working tree and in the
git-context run below.

**Git-context isolation.** `git archive HEAD` → `git init` → commit, then only this
dispatch's files plus the run-engine files the engine suite needs, so the git-dependent
helpers have real context and the shared helpers stay at their committed state:

```
cd <gitctx-scratch>
node --test 'claude/meta-skill/knowledge/run-engine/tests/**/*.test.js'   82/82 pass
python3 -m pytest codex/meta-skill/test_flow.py -q --tb=short             89 passed
```

The `claude/meta-skill/tests` suite was run in that tree earlier in the dispatch (647 passed
in 258.04s, before the attempt-evidence work); the coordinator asked in `msg_f9bd3b4cda2d`
not to repeat it, and nothing in this change touches those files.

`validate_unattended_readiness.py` is deliberately left at `HEAD` in that tree. It is no
longer separable: the planning worker has added
`from validate_bootstrap import plan_confirmation_blockers` to it (line 14, called at line
327) together with +490 lines in `validate_bootstrap.py`, so my copy of the first file and
`HEAD`'s copy of the second fail collection on 22 modules, and the reverse pairing — my
`validate_unattended_readiness.py` with the working tree's `validate_bootstrap.py` on an
otherwise `HEAD` tree — fails most of the suite, because it takes half of a coupled change
set. Neither file is this dispatch's to move; the coupling was reported to the coordinator as
`msg_f4a524adfd62`, and verifying that pair belongs to the combined run. The 647 above is
lower than the 655 the previous dispatch recorded only because that overlay carried my
`test_validate_unattended_readiness.py` additions and this one does not; no test regressed.

## What is preserved

The earlier fixes are intact and still covered: positive QA verdict, an actual failed attempt
on record, current-input binding, per-QA durable repair budgets, the mixed-wave
`accepted_with_gaps` / `iteration_repair_stopped` terminal verdicts, fail-closed invalid
budgets, and the execution-policy sandbox check (untouched).

## Residual risk

- **No host proof.** Unit and scratch-project level only; no real Codex run drove `flow.py`.
- **Migration is manual and costs one QA run.** Nothing automatically observes a legacy node;
  an operator or a bootstrap pass must run steps 1–2, and the route only opens on the *next*
  attempt, by design. A project with many legacy QA nodes loses every repair route until each
  is declared and re-run — deliberate, but a real cost that lands on the first `/run` after
  this change rather than at planning time.
- **An in-flight run loses one repair attempt.** Transitions written before this change carry
  no `qa_evidence`, so the first attempt after the upgrade is refused and re-runs. Fail-closed
  and self-correcting, but visible.
- **A QA node that repeats a verdict byte-for-byte loses its repair route** until its report
  names the attempt that produced it. That is a real requirement on node-specs, recorded in
  the template and surfaced at runtime on the transition's error line, not a silent denial —
  but existing QA nodes that emit stable reports will hit it, and the run reaches diagnosis
  rather than repairing.
- **`binding_identity` reads the planner's state file layout** (`evidence-freshness.json`,
  `contracts`/`nodes` → `inputs`), and admission now reads `readiness_status` from
  `check_artifacts`. Both read-only, but a change to either shape silently closes every route
  — fail-closed, and it needs coordinating with ctx_a377a4a12a25.
- **The external-change gate can still hold a recovered node.** After reobserving, a node
  whose source changed outside its own delivery reports `external: unverified` and stays shut
  until that change is decided. That is a different gate with a different owner; this task
  neither weakens nor resolves it, and the test says so explicitly rather than routing around
  it.
- **Each declared QA attempt now costs two extra helper runs** (`check_artifacts.py` at
  dispatch, plus the existing gate) and two state reads.
- **`qa_inputs_current` reads a diff shape owned by `evidence_freshness.py`.** A new non-input
  diff key added there would read as input drift and refuse a legitimate repair; fail-closed,
  but it needs coordinating with ctx_a377a4a12a25.
- **`NON_QA_FAILURE_TYPES`, `NON_QA_REPORT_STATUSES` and `qa_verdict`** remain hand-kept in two
  languages; nothing fails if one drifts.
- **The freshness call costs a helper process** per candidate QA node, and `_pending_state` is
  still computed twice per iteration.
