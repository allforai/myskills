# T15 coordinator boundary checks — in-flight corrections

Observed 2026-09-09, integration checkout based on `2cc347af` with three concurrent
editors. This is neither fixed-candidate acceptance nor real-host campaign proof.

## Decision-family discrimination

A read-only `python3 -B` probe imported the current `product_intent` module and
mocked `Path.read_text` for `decision-probe.json`. No candidate or fixture was edited.

| Supplied object | `decision_record` | `_decision_artifact` |
| --- | --- | --- |
| `{"id":"choice","status":"pending","operation":"choose"}` | `None` | `None` |
| `{"id":"choice","status":"pending","decision":null,"rationale":"","schema_version":1,"batches":[]}` | Original pending object | `None` |

Both results discard an explicitly pending choice from resolution checking. The
first exploits a sibling-family signature consisting of the `operation` key alone;
the second exploits the unconditional journal-key exclusion after a Phase A record
has already been recognized. Positive audit/envelope discrimination is necessary,
but must not make malformed or mixed pending choices invisible.

The decision editor was asked to add copied-public-driver negative cases and repair
these boundaries in messages `msg_a7a3b603791b` and `msg_72a9d9d8548b`. This finding
remains open until those tests and fixes are independently verified.

### Follow-up on the decision discriminator

At approximately 09:38 Singapore time, the coordinator reran both exact read-only
probes against the updated implementation. Both objects now remain decision
artifacts and `_unresolved` returns `true`; neither is discarded. The expanded
copied-public-driver test file also passed independently:

```text
python3 -B -m pytest claude/meta-skill/tests/unit/test_decision_gate.py -q --tb=short
42 passed in 14.43s
```

This verifies the two reported discriminator bypasses no longer reproduce in that
tree. Stable combined regression, independent review, and real-host campaign
acceptance remain outstanding; this does not accept the whole correction batch.

## Planning journal placement decision

The planning editor asked `msg_49f123f555b2` whether all plan confirmations must
write to the product journal, because doing so violates the existing non-product
Run Policy invariant and changes product history/freeze inputs. Coordinator read
`test_run_policy_session.py` and `_journal_decision`: the latter already resolves
any project-local schema-1.0 journal reference; forcing the product path was a new
restriction in the in-flight validator, not a limitation of the shared resolver.

Reply `msg_1981b0041a79` directs a bootstrap-local
`.allforai/bootstrap/plan-confirmation-journal.json`, resolved through the same
existing journal validator. A real product-journal reference can still be used
when applicable; local planning must not create product-concept decisions.
Exact graph/delta binding, explicit recorded user choice, supersession checks and
history retention remain required. Planner owns the minimal readiness gate hook
and typed repair routing; runtime follow-up was notified of the file ownership.

Fixture confirmation must represent an explicit scripted user event. Never
automatically approve the current graph inside `gate`, `publish_contract`, or
generic file writes: doing so masks the very unconfirmed-delta defect being tested.
This is implementation direction, not evidence that the gate is finished.

## Existing focused tests do not cover these boundaries

Coordinator command on the in-flight tree:

```text
python3 -B -m pytest claude/meta-skill/tests/unit/test_decision_gate.py -q --tb=short
28 passed in 10.45s
```

The green result coexists with the two reproduced bypasses above. It proves the
existing cases passed at observation time, not that C1/C2 or the combined candidate
is accepted. Run a stable combined regression after all editors settle.

## Coordination and report corrections

- `2cc347af` was committed, not accepted: both independent reviews required fixes.
- Distinguish tests of fixed HEAD from tests of a concurrently edited checkout.
  A transient test failure during overlapping edits does not establish load or
  ordering sensitivity.
- Runtime report drafts must not omit assigned stale-report/non-QA admission fixes.
- Wait for a worker's exact test job, not a global `pgrep` pattern that can match
  the polling shell itself or another worker's test.

These points were returned to the responsible active dispatches. No main merge,
remote write, terminal cancellation, or worktree cleanup was performed.

## In-flight plan confirmation provenance

At 09:34 Singapore time, the new `_plan_confirmation_entry_errors` helper accepted
the following record with zero errors in a direct read-only `python3 -B` call:

```json
{"revision":1,"stage":"3.4","plan":{"implement":[]},"confirmation":{"source":"user","reference":"nonexistent-user-turn","reason":"invented approval"}}
```

Returned value: `[[], {"implement": []}]`. The helper checks nonempty provenance
strings, not whether a resolved user record actually confirms this graph. This is
an intermediate helper-level finding, not an end-to-end runtime reproduction.
The planner was asked in `msg_1d9d2e3f0bb2` to resolve actual confirmation provenance,
bind it to the graph/delta, test stale and fabricated references, and ensure the
real readiness/runtime gate consumes the check. No acceptance is inferred from
the presence of this new validator.

## T15 helper-suite regression

Coordinator reran the complete T15 helper suite after the three extra-file admission
cases were added:

```text
python3 -B -m pytest docs/grillstorm/meta-intent/replan-2/T15 -q --tb=short
23 passed in 51.88s
```

This covers the preparation/admission tooling, including unexpected regular,
hidden, and symlink entries. It is not a real-host semantic pass, and does not
change the campaign's admitted-pass count.

## Pre-existing Codex parity checker drift

Coordinator reproduced `python3 -B shared/scripts/orchestrator/check_codex_meta_skill_parity.py`
exiting 1 with seven errors. Inspection located stale assertions rather than a
reason to restore old installation or execution behavior:

- Version lookup uses removed `claude/meta-skill/skills/bootstrap.md`; the real
  entry is `skills/bootstrap/SKILL.md`, version `0.14.2`, matching Codex
  `0.14.2-codex.1`.
- `install.sh` delegates to `install_bundle.py`. The checker still searches the
  Shell wrapper for copying, metadata, and installation-path implementation.
  The Python implementation copies canonical skills/knowledge and writes
  `.install-source`; the documented layout puts the payload in `skill-bundles`
  and only a routing entry in `skills`.
- The checker requires the automatic approval/sandbox-bypass flag, while the
  current driver uses `--sandbox` with an explicit read-only/workspace-write
  policy and rejects automatic escalation. Do not restore bypass to satisfy an
  obsolete assertion.
- `smoke_codex_generated_run.py` contains the same obsolete permission assertion
  and needs inspection alongside the parity checker.

No checker change has been applied at this checkpoint. Correct the verifier
against the actual installation/permission contracts with negative tests rather
than removing the checks or claiming the current failures are acceptable proof.

### Checker correction follow-up

The coordinator subsequently updated both checkers, without changing installation
or runtime behavior. Parity now reads `skills/bootstrap/SKILL.md`, checks the Shell
delegation and Python bundle installer, and verifies discovery entry/payload
separation. Both checkers reject automatic permission bypass and require the
driver's explicit limited sandbox policy. The smoke description now accurately
calls this materialization/static verification, not engine behavior proof.

Observed existing checks after the patch:

- `python3 -B shared/scripts/orchestrator/check_codex_meta_skill_parity.py`: exit 0,
  no errors (previously seven errors).
- `python3 -B shared/scripts/orchestrator/smoke_codex_generated_run.py`: exit 0,
  no errors (previously the obsolete permission assertion).
- `python3 -B -m pytest codex/meta-skill/test_install.py -q --tb=short`:
  7 passed in 0.08s. These exercise temporary installation fixtures, not a local
  user installation.

The checkers remain static source checks; combined-candidate review is still
outstanding. A subsequent coordinator regression added
`shared/scripts/orchestrator/test_codex_contract_checks.py`: both public checker
commands run on disposable source snapshots, with unchanged positives and
mutations for permission bypass, omitted sandbox argument, expanded permissions,
missing bootstrap, missing canonical knowledge copy, payload under discovery,
lost source metadata, and broken installer delegation. No live installation is
performed, and only disposable fixture copies are modified.

Observed: the focused checker suite passed 13 tests in 2.28s; the complete
`python3 -B -m pytest shared/scripts/orchestrator -q --tb=short` suite passed
122 tests in 3.63s. These tests were added after the checker correction, not
claimed as test-first evidence.

### In-flight plan provenance boundary review (2026-09-09 02:08 UTC)

Current source inspection found two further cases for the planning worker to
resolve before acceptance (`msg_413d158481d1`):

- `_plan_provenance_findings` compares a journal plan through `_normalized_plan`,
  which maps non-list edge values to `[]` and drops non-text edges. Unlike the
  confirmation entry, the journal plan has no preceding shape validation. A
  malformed recorded choice can therefore normalize to a valid empty-edge plan.
  Reject malformed provenance rather than repairing it into authority.
- Every retained revision resolves through `_journal_decision`, which rejects
  superseded decisions. The fixture helper always writes `supersedes: null`.
  Test and document whether normal successive confirmations are append-only
  historical snapshots; verify that supported updates retain history without
  accepting a superseded decision as current authority.

These are in-flight code-review findings, not completed reproducer tests or
accepted fixes. The worker's latest observed broad run reported 208 failed and
489 passed; it remains active. No combined-candidate acceptance is claimed.

A subsequent read-only `python3 -B` helper probe confirmed that journal edge
values `null`, `"qa"`, and `[17, null]` each normalize to `[]` and compare equal
to the valid empty-edge graph. This confirms the normalization behavior only;
the public-gate regression and correction remain assigned to the worker.

The QA admission worker was immediately reused as `ctx_57a9adb41210` for
`task_e622ad3f9496` after `msg_a6c4f29a9812`: previous completion was withheld
because legacy `freshness: null` still permitted stale reports to trigger
automatic repair. Its new task preserves legacy completion while requiring
current-attempt/current-input evidence for automatic repair, with public-driver
rejection and recovery regressions. Delivery `delivery_954f9e67216a` was
acknowledged only after the terminal's new dispatch accepted input.

### Legacy migration does not retroactively prove a QA report (02:11 UTC)

The in-flight `test_observing_a_legacy_node_restores_its_repair_route` creates a
legacy failed report and transition, then publishes only a contract observation
using `python -c pass`. It asserts that the same historical report now dispatches
repair, without a new QA attempt. The coordinator ran that exact test through
pytest: **1 passed, 73 deselected in 0.31s**. This is evidence of an incorrectly
accepted recovery path, not evidence that recovery is safe.

Contract observation proves current inputs, not that an earlier report evaluated
them. Message `msg_0d59755f36a2` requires the worker to turn this case into a
rejection regression and separately prove a new QA attempt/report after input
binding. A declared node with unchanged inputs plus a touched historical report
also needs attempt binding: mtime and current input state alone do not establish
that this attempt produced that report. The worker remains active; acceptance
is withheld.

### Campaign ledger acceptance withdrawal

The coordinator found T15–T18 still reporting `candidate_accepted: true` and
`candidate_refresh_required: false` for e30ccc7c, contrary to the subsequent
host findings and rejected repair reviews. All four ledgers now withdraw
acceptance and require refresh, preserving the old commit, tree hash, packet
paths and attempts under explicit historical withdrawal records. Their launch
requests now begin with a suspension notice; no frozen packet was changed.

Added `test_campaign_acceptance.py`: four cases first failed on the stale
acceptance flags. T18's pin test now distinguishes an unlaunched reference from
a historically launched candidate whose acceptance was subsequently withdrawn,
while retaining commit re-export, manifest and hash verification. No historical
launch identity is erased to satisfy the old no-candidate branch.

Observed combined ledger checks: 29 passed in 45.08s with pytest
`--import-mode=importlib`. The initial default-mode invocation failed collection
because T17 and T18 both name a module `test_results_pin.py`; no test passed in
that invocation, and no cache deletion was needed. These are ledger checks,
not host-scenario admission. Production worker edits remain in flight.

Follow-up checks after the launch suspension text was added: the four campaign
consistency cases passed in 0.01s; the complete T15 helper suite passed 23 tests
in 63.02s and T16 passed 22 in 34.25s. Main remains clean at 4e34c684; no merge,
push, installation, frozen-export mutation or worktree deletion was performed.

### Runtime worker accepted the migration counterexample (02:19 UTC)

`msg_b34a5cd88065` acknowledges that the positive migration test admitted old
bytes without new QA execution. The worker is now implementing driver-recorded
attempt evidence instead of settling the earlier 74-test result as accepted.
Coordinator follow-up `msg_6295fe138aab` requires pre/post input binding,
driver-owned evidence even when the executor appends its own transition, actual
`flow.main` lifecycle tests, and a supported path for a genuine rerun reaching
the same verdict. Digest inequality alone must not be described as proof that
QA executed; unchanged bytes may be ambiguous, not necessarily a never-run QA.
These are implementation requirements in progress, not verified outcomes.

### Independent Claude engine rerun

The coordinator ran `node --test
'claude/meta-skill/knowledge/run-engine/tests/**/*.test.js'` on the integration
checkout: **82 passed, 0 failed**, duration 50.667ms. Coverage includes the
mixed-wave terminal outcomes, per-QA budgets, restart budget handling, repair/QA
rerun/closure order and inline engine parity. These are scripted engine tests,
not actual Claude host proof. The current active runtime worker owns Codex files,
so this rerun does not claim to validate its unfinished attempt-binding changes.

### In-flight boundary recheck (02:30 UTC)

The planning worker now validates recorded graph shapes before normalization.
A read-only probe of `_plan_shape_errors` rejects null, string and mixed-type
edge values and accepts a valid empty edge list. This is helper evidence, not
yet a public-gate or combined-suite acceptance.

The runtime worker's proposed content-or-mtime attempt evidence still admits a
touch-only change. A read-only call to current `attempt_evidence` with equal
digests, `written: 1` before and `written: 2` after, and the same binding returned
the unchanged report in `produced`. Coordinator `msg_ce0a4299cb8a` rejects this
alternative and requires a `flow.main` regression whose executor only touches
the old report. Identical semantic verdicts must use real attempt-specific
evidence or be diagnosed as ambiguous; time changes do not prove QA execution.

Worker `msg_c874d036cc8c` subsequently withdrew the content-or-mtime rule and is
implementing content-based production with explicit ambiguity diagnostics and a
same-verdict/new-attempt-identity positive through `flow.main`. This remains
unverified until the corrected tests and implementation settle.

Coordinator `msg_fb2d6278463c` also requests the previously-passing-QA recovery
case. `evidence_freshness.evaluate` prefers the contract for readiness but uses
prior evidence for its diff when present. The current runtime predicate and
snapshot selection may therefore deny a genuine new failed QA report after
inputs change and a new contract is observed. This is a source-review concern,
not yet a reproduced defect; test it without weakening actual input drift or
modifying planner-owned shared helpers without coordination.

### Attempt evidence regression rerun (02:34 UTC)

Coordinator focused pytest selection for touch, byte-identical ambiguity,
repeated-verdict identity, changed/re-observed inputs, post-attempt observation,
worker-authored evidence, driver recording and legacy laundering: **8 passed,
76 deselected in 2.69s** on the in-flight tree. This supports those scoped
checks only.

Source inspection also found that the `flow.main` lifecycle tests force
`first_pending_node` to return the QA node. The touch test's final selector
assertion therefore calls that same stub. Those tests can verify recorded
evidence but cannot prove the actual scheduler refuses or dispatches repair.
`msg_7b76fd060073` requests real-selector negative and positive driver tests,
recording dispatched node ids and proving repair → QA rerun → closure order.
Controlled executor results and unrelated preflight stubs may remain; the
selection/routing under test must not be stubbed. Final acceptance stays open.

### Canonical repair-loop acceptance withheld (02:45 UTC)

The subsequent focused real-routing/recovery selection passed **5 tests,
84 deselected in 3.16s**. Source inspection nevertheless found that
`routing_project` removes repair `source_inputs`, explicitly because repair
cannot publish evidence while its QA dependency is failing. Its closure also
depends only on repair, omitting the planner-required QA dependency. This
proves a legacy-support fixture, not a fully declared generated workflow.

Completion `msg_5cb2bbdb3a70` reports 89 Codex tests and 82 Node tests, but is
not accepted for this boundary. The exact Opus terminal was immediately reused
for task `task_83657ee64666`, dispatch `ctx_76fd61432c85`, before delivery
`delivery_a26da0258fc8` was acknowledged. Planner coordination message
`msg_95819d84d6bd` preserves shared-file ownership. Required evidence is a
planner-valid, fully declared real-driver failure → repair → QA rerun → closure
sequence with actual freshness admission/publication, plus stale-touch refusal.
No new actual host proof, commit, main merge or worktree deletion occurred.

Worker reproduction `msg_f517881f7c44` confirms the fully declared deadlock:
all three input contracts are valid, QA failure is admitted, repair writes its
artifact, but its independent gate returns false and evidence publication returns
`stale` because upstream QA has no passing evidence. Consequently repair never
completes, QA never reruns, and the attempt budget is not consumed. This is
worker-reported executable evidence; the coordinator independently inspected
the conflicting dependency/publication checks, not the reproduction script yet.

The proposed driver-side delivery/progression change remains under review.
`msg_9951c3c18af7` requires attempt-bound delivery rather than old/touched files,
durable exactly-once budget accounting, real source-changing repair in the
positive case, and refusal of closure if a subsequent repair execution changes
the source after QA passes. Claude parity remains a required assessment; a
Codex-only test must not silently stand in for both platforms.

Coordinator `msg_a1cebea97dca` assigns the same runtime worker the bounded Claude
parity reproduction/correction in `engine-core.js`, its exact inline workflow
mirror and repair-loop tests. Source inspection shows Claude's `runNode` also
requires the independent artifact gate before releasing a successful repair;
this is a parity concern, not yet an executable Claude reproduction.

The next in-flight report claims 91 Codex tests and 82 Node tests. Inspection
found its planner-validity test calls only the readiness repair-loop validator,
not bootstrap's closure-to-QA routing validator, and its delivery predicate
accepts nonempty `produced` even with a null binding. Coordinator
`msg_653340e843f7` returns those exact gaps for correction. These reported test
counts do not establish canonical-loop acceptance.

### Plan confirmation focused rerun (02:56 UTC)

Coordinator ran `python3 -B -m pytest
claude/meta-skill/tests/unit/test_plan_confirmation_gate.py -q --tb=short`:
**34 passed in 7.59s** on the in-flight integration tree. The dedicated tests now
cover missing confirmation, fabricated references, invalid user-session claims,
retraction, malformed recorded graphs/intents, added/rewired/dropped nodes and
historical delta revisions. This is focused regression evidence, not a stable
combined-tree or actual-host acceptance; planner remains active.

Coordinator also reran `test_planning_audit_contracts.py`: **15 passed in
2.57s**, covering structural loop routing, deferred effect ownership and document
verification declarations at the copied bootstrap CLI. This is not semantic
host-dialogue proof.

### Claude real-helper boundary rerun (03:04 UTC)

Worker `msg_2c41698e3529` reports the Claude deadlock reproduced and corrected,
with 98 Codex / 85 Node tests, but explicitly identifies a remaining delivery
provenance gap: Claude's deferred gate trusts `NODE_RESULT` rather than measuring
the repair attempt. Coordinator `msg_74519d1ec17e` withholds acceptance and asks
for a supported independent measurement boundary, not a model boolean or an
invented Workflow API.

Independent `node --test .../tests/declared-loop.test.js`: **3 passed in
2444.286625ms**. These confirm the real gate's failed-upstream refusal, positive
loop progression, and no commit for delivery-only repair. They do not prove the
missing/touched/errored/unbound-delivery negatives or actual Claude host behavior.

### Runtime completion independently rerun (03:28 UTC)

Completion `msg_3ea34f4d008b` reports fully declared routing on both adapters,
including independent before/after helper measurements on Claude. The coordinator
released the settled dispatch `ctx_76fd61432c85` (transcript captured) before
acknowledging delivery `delivery_6089c35b27f5`; helper integration guidance was
forwarded to its actual owner in `msg_cc5590c6d4a3`.

Independent working-tree reruns:

- `python3 -B -m pytest codex/meta-skill/test_flow.py -q --tb=short`:
  **98 passed in 29.64s**.
- `node --test 'claude/meta-skill/knowledge/run-engine/tests/**/*.test.js'`:
  **95 passed in 3307.97375ms**, including the 13 declared-loop tests.
- `git diff --check`: exit 0.

These replace the earlier missing-measurement test snapshot, not the pending
actual-host acceptance. The helper and acceptance-allocation workers remain
live; their files are still mutable, so this is not a stable combined-tree
acceptance. In particular helper snapshot coherence/malformed-record corrections
remain subject to its completion review. No actual host launch, commit, main
merge or worktree deletion occurred in this checkpoint.

### Acceptance allocation and helper checkpoint (03:29 UTC)

Independent `python3 -B -m pytest
claude/meta-skill/tests/unit/test_acceptance_allocation.py -q --tb=short`:
**10 passed in 6.08s**. Inspection of the in-flight report confirms the intended
boundary: full inherited criteria remain unchanged, while documentation owes
stage-local document proof and a deferred effect retains an owning requirement.
The tests exercise generated CLI projects; they are not evidence that a real
host interprets that obligation correctly. The report still lists separate
boilerplate criterion and host-dialogue findings, so no global acceptance follows.

Current helper source still contains the previously identified separate state
read and permissive observation shape. Coordinator `msg_d73a01611562` explicitly
reminds its active owner to resolve `msg_1ca735f1e9fb` before settlement; passing
the broader suite does not discharge these specific findings.

### Acceptance allocation settled (03:36 UTC)

Worker completion `msg_9bf60a76182c` reports 10 focused tests and 780 full
unit tests (294.44s in its final report). Coordinator's independent focused
result remains 10 passed in 6.08s. Dispatch `ctx_6087d489e492` was released
with transcript captured before acknowledging `delivery_d5b48df50be4`.
Only the helper worker remains active; its 27-test status message is not a
completion and does not resolve the outstanding coherence findings.

Report qualification: the acceptance-allocation report retains a historical C3
boilerplate defect as if current. Coordinator inspection found that phrase
absent across current `claude/meta-skill`; the current question-answer branch
records an answer without generating that acceptance string. The historical
finding remains valid for its frozen candidate, but a present semantic defect
requires reproduction. A1/A2 similarly remain fresh-host checks rather than
newly proven current-code defects. Guidance `msg_18ab24bc1967` records this
distinction; no historical evidence was rewritten.

### Helper hardening independently rerun (03:39 UTC)

The active helper worker has now added canonical snapshot/kind shape checks
and a controlled rebind-between-reads regression. Independent command
`python3 -B -m pytest claude/meta-skill/tests/unit/test_check_artifacts_measurement.py
-q --tb=short`: **48 passed in 6.49s**. This supersedes the prior observation
that those corrections had not landed. Final source review, settled-worker
report and stable combined-tree verification remain pending; no actual-host
acceptance is implied.

### Descriptor/read-error boundary reproduction (03:40 UTC)

Source review identified two new-helper regressions and sent
`msg_ea77d36e2883` to its active owner. A bounded independent subprocess probe
in a disposable temporary directory reproduced both: `artifact_digest` on a
FIFO timed out after 2 seconds (the probe killed and reaped only its own child),
and `read_state_text` on invalid UTF-8 raised uncaught `UnicodeDecodeError`.
The FIFO is opened before the non-regular-file check, so that check cannot
prevent the blocking open. The state reader catches OSError but not decoding
errors. Both must be corrected before accepting the helper; the preceding
48-test pass does not cover them. Temporary probe files were automatically
removed; no repository source or campaign evidence was modified by the probe.

### Coordinator closes the two omitted helper failures (03:48 UTC)

Helper completion `msg_8ef3a802cb55` reported 804 unit / 105 Codex /
95 Node / 122 shared tests, but omitted the FIFO and decoding failures already
reported in `msg_ea77d36e2883`. Dispatch `ctx_eebb7b40614f` was released with
transcript captured before delivery `delivery_9bfaf252a454` was acknowledged.
No editors remain active.

Coordinator added two bounded behavioral regressions: **2 failed, 48 deselected
in 3.04s** before the correction. Opening with nonblocking mode lets the existing
fstat refusal reject a FIFO without waiting for a writer; catching UnicodeError
in the state reader returns no binding for invalid UTF-8. Afterwards the helper
suite is **50 passed in 6.44s**, and the Node suite is **95 passed in
3029.339375ms**. This is a narrow helper correction under skill-creator's
preserve-scope/observable-behavior guidance; no new workflow rule was added.
The stable combined Claude unit + Codex flow/install suite is running. No host
acceptance, commit, main merge or worktree cleanup is claimed.

### Stable-tree combined verification (03:53 UTC)

With every worker settled and no production edits during execution:

- Claude unit + Codex flow/install: **911 passed in 317.41s**.
- Shared orchestrator tests: **122 passed in 3.58s**.
- T15–T18 harness plus campaign acceptance tests, importlib collection:
  **111 passed in 165.46s**.
- Meta contracts and generalization-boundary validators: exit 0.
- Codex parity and generated-run smoke: passed, no errors or warnings.

These are deterministic regression and preparation checks, not the 60 required
actual-host cells. A local repair checkpoint and fixed-commit independent review
are next; acceptance and main integration remain unclaimed.
