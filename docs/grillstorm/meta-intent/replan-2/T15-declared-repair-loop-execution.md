# T15 — the canonical declared repair loop, executable

Corrects the downgrade root found in the previous dispatch's routing regression, and then
the same defect on the Claude engine. Scope grew twice during the dispatch, both times on
root's instruction (`msg_9951c3c18af7` hardening conditions, `msg_a1cebea97dca` Claude
parity), and both are covered below.

The starting point:
`routing_project` removed `repair.source_inputs`, turning the repair node legacy so it would
complete on the pre-freshness gate. That made the test pass and hid a real defect — a fully
declared loop could not advance at all. Scope: `codex/meta-skill/knowledge/flow-template.py`,
`codex/meta-skill/test_flow.py`, and the repair-loop bullet of
`codex/meta-skill/knowledge/orchestrator-template.md`. No shared file was changed. No commit.

## The defect, reproduced

`scratchpad/repro_declared_loop.py` builds a planner-valid graph — `verify` → `repair` →
`accept`, every node declaring `source_inputs`, the loop declared in the readiness spec, all
three contracts published `valid` — then fails the QA node and delivers the repair:

```
verify freshness : {"status":"stale","readiness_status":"valid","diff":{"evidence":"unpublished"},"admission":"declared"}
verify admitted  : True

repair freshness : {"status":"stale","readiness_status":"valid",
                    "diff":{"evidence":"unpublished","upstream":["verify"]},
                    "reason":"Upstream evidence is stale or missing","admission":"declared"}
repair gate      : False
repair evidence publish: stale - Upstream verification is stale or missing; repair it before
                                 publishing consumer evidence
repair gate after      : False
```

Two shared contracts contradict each other:

1. The declared loop requires `repair.hard_blocked_by = [qa]` — `validate_unattended_readiness`
   blocks `repair_loop_not_blocked_by_qa` otherwise.
2. `evidence_freshness` treats every `hard_blocked_by` edge as an evidence dependency: a
   consumer cannot publish evidence, and cannot be `valid`, while an upstream node's evidence
   is stale. A *failing* QA node's evidence is stale by definition.

So a fully declared repair node is unreachable-to-completion by construction. Since
`repair_progress` counted only `completed` repair transitions, the QA node never re-ran, the
budget was never consumed, and the driver re-dispatched `repair` until `max_iterations`.

## The boundary, and what changed

The reproduction and a proposed boundary went to the planner dispatch and the coordinator as
`msg_f517881f7c44` before any code moved, offering to drop this accommodation if
ctx_a377a4a12a25 would rather exclude a declared loop's QA edge from evidence dependencies
inside `evidence_freshness.py`. Nothing shared was touched either way.

The fix is one sentence of semantics in the driver: **the loop advances on the repair node
delivering, not on it completing.** `repair_delivered(entry)` accepts a completed transition,
or a failed one whose driver-recorded `qa_evidence.produced` shows the attempt wrote the
repair node's declared exit artifacts — the same evidence the driver already records for QA
attempts, now recorded for declared repair nodes too.

Nothing is waived, downgraded or hidden by that:

- the repair transition stays `failed` and the node stays **incomplete**;
- the attempt still spends a budgeted attempt, so the bound is unchanged;
- the QA rerun, never this record, decides whether the repair worked;
- once that rerun passes, the repair node is dispatched again as an ordinary node, publishes
  its evidence with its upstream now valid, and **completes on its own merits**;
- only then is closure reachable, and it still waits for the QA node itself.

## Hardening the delivery proof

`msg_9951c3c18af7` accepted the reproduction as evidence of the bug but not the fix, and
named the conditions. All are implemented and pinned:

- **A delivery must be an attempt that actually ran.** `attempt_evidence` records `ran`
  (the executor's exit status), and `repair_delivered` requires it. An executor that
  errored delivers nothing even if files are on disk.
- **A pre-existing or touched artifact is not a delivery.** `produced` is content change
  measured by the driver across the attempt, unchanged from the previous dispatch.
- **A blocked or environment report is not a delivery.** `deliverable_state` drops any
  exit artifact whose JSON carries a `NON_QA_REPORT_STATUSES` status before production is
  measured, so writing `failed_env` produces nothing.
- **A delivery is bound to an input snapshot.** The driver now records `binding` for
  declared repair nodes as well as QA nodes, and `repair_delivered` requires it. (An
  in-flight version accepted a non-empty `produced` with `binding: None`; root caught that
  in `msg_653340e843f7` and it is closed — `test_a_declared_repair_node_cannot_complete_while_its_qa_node_fails`
  now asserts all four refusals: empty produced, `ran: false`, `binding: None`, and no
  evidence at all.)
- **The budget is consumed exactly once, durably.** `repair_progress` derives from the
  transition log, so a restart re-derives the same count.
- **Convergence.** A real repair edits the source the QA node judges, which would
  invalidate the verification if the repair simply re-ran. The repair node's post-QA
  dispatch is therefore an explicit **evidence finalization**: `repair_awaiting_finalization`
  detects that the node already delivered and every QA node it answers has since completed,
  and `build_prompt` then instructs the node to publish the delivery already on disk and to
  change no source. If it changes source anyway, the QA evidence goes stale and closure does
  not happen — pinned by its own test.

## The same defect on the Claude engine

`msg_a1cebea97dca` asked whether `engine-core.js` shares this. It does, with a different
symptom. `runNode` sends a successful repair through `gateNodePrompt`; the real
`check_artifacts.py` withholds it on the failing QA upstream; the in-node artifact repair
loop burns its three attempts against a gate no repair can satisfy and returns
`exhausted_repair_loop`; `runEngine` finds no declared loop for the repair node, so the run
ends `needs_diagnosis`. Reproduced against the real helpers:

```
run did not close: {"status":"needs_diagnosis","hardFailures":[{"node_id":"repair",
  "blocking_findings":[{"type":"exhausted_repair_loop",
                        "detail":"artifact repair loop exhausted after 3 attempts"}]}]}
verify:1 repair:1 repair-publish:stale repair:2 repair-publish:stale
repair:3 repair-publish:stale repair:4 repair-publish:stale
```

The correction is the same lifecycle: `runNode` takes the open loop's QA node ids for the
declared repair node, and a **withheld** gate can then return `{delivered: true}` instead of
retrying. A `hard_fail` gate — environment, authority, cross-node — is untouched and still
stops the run. In `runEngine` a delivered result never commits, so the repair node stays out
of `done`, closes its loop so the QA node reruns, and is dispatched again afterwards as an
ordinary node that must pass the same gate on its own merits. `run-engine.workflow.js` is
the verbatim mirror; the sync-check passes.

### A delivery is measured, not asserted

The first version of that change trusted the node's own `NODE_RESULT` for the delivery,
which root refused (`msg_74519d1ec17e`) as the same unproven progression already refused on
Codex. It was refused rather than argued, and the capability constraint went back with a
proposed boundary; root chose option B.

The constraint is real: the Workflow engine has no controller-owned filesystem or command
access. `run-engine.workflow.js` receives `agent`, `pipeline`, `phase` and `log`, and every
fact it holds comes from a schema-validated sub-agent answer. Its one existing form of
independent measurement is the gate step — a *separate* agent running a shipped
deterministic command and reporting its output — so that is the boundary this uses, and its
trust limit is exactly that: the engine trusts an independent step to report a command's
output faithfully, and nothing beyond it. `measurePrompt` and `gateNodePrompt` both say, in
those words, to report what the command printed and not to compute, infer or fill in a field
it did not print.

The measurement contract was requested as a narrowly additive, read-only change to
`check_artifacts.py --json` (`msg_475f54639702`) and **has since landed**, owned by
`ctx_eebb7b40614f` and specified in `msg_f7b0cc479de6`:

- `artifacts[].digest` — sha256 hex, always printed, `null` with `digest_error` when the
  file is missing, outside the project root, or unreadable;
- `freshness.binding_identity` — sha256 over the canonical `{kind, inputs}` of the recorded
  observation (`contracts[node]` before `nodes[node]`), with `binding_kind`, paired with the
  existing `readiness_status`.

The engine reads exactly those. The same step runs once before the node and once after, and
`measuredDelivery` requires all of:

- every declared exit artifact present, with no `status_error` (which already covers
  `failed_env`, `blocked`, partial and gap statuses through `_artifact_status_error`);
- a non-null `digest` for each — an unreadable file is refused even when `exists` is true,
  which is why the helper deliberately left `exists` semantics alone for a symlink escape;
- the gate withheld this node **only** by its own loop's QA node — `withheld_by` non-empty
  and a subset of them;
- one `binding_identity`, unchanged between the before and after measurements, **and** a
  current `readiness_status: valid`. Both, because they answer different questions: after a
  source change a recorded observation can still match while the node is no longer current,
  so digest identity alone cannot establish a rebinding;
- at least one artifact whose content `digest` moved across the attempt.

Anything less is `unmeasured_repair_delivery`, a hard failure — never a quiet advance.
`tests/real-gate.js` computes none of this: it copies the checker's fields verbatim, and its
one derived mode strips them again to exercise the fail-closed path.

## Test evidence

```
python3 -m pytest codex/meta-skill/test_flow.py -q --tb=short             98 passed (was 89)
node --test 'claude/meta-skill/knowledge/run-engine/tests/**/*.test.js'   95/95 pass (was 82)
```

Re-run in a git-context scratch (`git archive HEAD` → `git init` → commit, this dispatch's
files overlaid), twice, because the Node suite now has a real integration dependency:

| scratch tree | Node | Codex |
|---|---|---|
| `HEAD` `check_artifacts.py` (no measurement fields) | 11 pass, **2 fail** | 98 passed |
| `ctx_eebb7b40614f`'s `check_artifacts.py` copied in read-only | **95/95 pass** | 98 passed |

The two failures in the first row are the end-to-end closure tests, and they fail for the
right reason: without the measurement fields the engine refuses the delivery. That is the
dependency stated plainly — **the Claude side of this correction needs the helper owner's
`check_artifacts.py` to land**, and until it does a fully declared Claude run fails closed
rather than closing. The Codex side has no such dependency.

`tests/declared-loop.test.js` is the Claude-side regression and it does **not** use a fake
gate. `tests/real-gate.js` builds the same fully declared project the Codex fixture uses,
publishes each node's contract through the real `evidence_freshness.py`, and answers every
`verify:<node>` prompt from the real `check_artifacts.py`. Its tests pin the gate boundary
itself (`upstream: ["verify"]`, publication `stale`, then `valid` once the QA node passes);
the fail-closed path when a checker does not publish the measurement fields
(`an unmeasurable delivery fails closed rather than advancing the loop` →
`needs_diagnosis` / `unmeasured_repair_delivery`, closure never runs); the loop closing end
to end against the **real** landed helper; and the dispatch order
`verify, repair, verify, repair, commit:repair, accept` — the repair node committing only
after the QA rerun passed, never on its delivery. Eight further tests pin what
`measuredDelivery` refuses: an unchanged or touched artifact, a missing one, a blocked one,
one whose digest is null with a `digest_error` even though it exists, an absent or
field-incomplete measurement, a null binding, a binding that moved mid-attempt, a
`readiness_status` that is anything but `valid`, an empty `withheld_by`, and one naming any
node outside the loop.

`routing_project` is now the canonical graph with **no node downgraded**: `verify`, `repair`
and `accept` all declare `source_inputs`, `repair` is `hard_blocked_by` `verify`, `accept` is
`hard_blocked_by` **both** `repair` and `verify`, and each publishes its own contract at
planning time. The QA closure edge was missing in the first version of this fixture, which
root caught (`msg_653340e843f7`): `validate_unattended_readiness` only requires
closure → repair, but `validate_bootstrap.validate_repair_loop_declaration` additionally
requires closure → every QA node, "it would otherwise close on the repair alone, without the
QA rerun that proves it". The Claude fixture in `tests/real-gate.js` carries the same edge.

- `test_the_routing_fixture_satisfies_the_planner_repair_loop_rules` asserts **both**
  validators over that graph: readiness's `_validate_repair_loop_spec` (no blockers, no
  warnings) and bootstrap's `validate_repair_loop_declaration` (no errors). It also removes
  the QA closure edge and asserts the bootstrap validator *does* complain, so the edge is
  proven load-bearing rather than merely present. Both calls adapt to the shared file's
  shape — the readiness validator's arity, and the presence of
  `validate_repair_loop_declaration`, which exists in the working tree but not at `HEAD` —
  so the test pins the wiring rather than a version of a file it does not own.
- `test_a_declared_repair_node_cannot_complete_while_its_qa_node_fails` pins the constraint
  itself: the `upstream: ["verify"]` diff, the refused gate, and the `stale` publication.
- `test_real_routing_drives_the_declared_loop_to_closure` is the end-to-end regression, with
  the real `first_pending_node` (wrapped by a spy, not replaced), the real `check_artifacts`
  gate including real freshness admission, and real `evidence_freshness` publication. It
  asserts the executed order `verify, repair, verify, repair, accept`; that the repair node's
  first publication is refused `stale` and its second is `valid`; that the transition log ends
  as `verify: [failed, completed]`, `repair: [failed, completed]`, `accept: [completed]`; and
  that `first_pending_node` finally returns `None`.
- `test_real_routing_never_executes_repair_for_a_touched_leftover` runs on that same fully
  declared graph: a touch-only executor never selects or executes `repair`, and `accept`
  never runs.

New Codex regressions for the hardening conditions:
`test_real_routing_converges_when_the_repair_changes_the_source` (source-changing repair,
finalization does not touch the verified source, closure runs with QA evidence current for
the final source), `test_a_repair_that_mutates_after_the_qa_pass_does_not_reach_closure`,
`test_a_repair_attempt_that_delivers_nothing_never_releases_the_qa_rerun` (four modes:
writes-nothing, touches-only, executor-error, blocked-report — none spends a budgeted
attempt), and `test_a_spent_repair_budget_is_counted_once_across_a_restart`.

**Red before the fix**, in scratch copies — scratch only, no shared file swapped:

```
# Codex: repair_delivered reverted to completion-only
cd <scratch>; python3 -m pytest codex/meta-skill/test_flow.py -q --tb=no   4 failed, 86 passed

# Claude: the deliveryOnly deferral removed from runNode
cd <scratch>; node --test '.../tests/declared-loop.test.js'                2 failed, 1 passed
```

On the Claude side the two failures are `runEngine drives the declared loop to closure
against the real gate` and `runEngine does not commit a repair node that only delivered`;
the gate-boundary test passes either way, because the boundary is the system's, not the
engine's.

`test_a_declared_repair_node_cannot_complete_while_its_qa_node_fails` and
`test_real_routing_drives_the_declared_loop_to_closure` are the two that fail on the rule; the
other two, `test_canonical_entry_is_resolvable` and
`test_standalone_installer_keeps_canonical_entry`, fail only because that scratch holds a
partial tree and pass in both full trees.

The legacy-compatibility tests are retained unchanged: `legacy_project`, the touched-legacy
negative, the laundering rejection, the observe-then-rerun recovery, and the stale-evidence
recovery all still pass.

## Parity

Both hosts now apply one lifecycle: **the loop advances on the repair delivering, and the
repair node completes on its own merits afterwards.** Both measure that delivery across the
attempt rather than accepting a claim, and both refuse the same things: a touched or
pre-existing artifact, a blocked or environment report, an attempt that did not run, and a
delivery not bound to one input snapshot. Neither waives a gate, and neither edits a shared
helper.

They differ in *who* measures. The Codex driver measures directly — it owns the filesystem
it runs on. The Claude engine cannot, so it measures through an independent gate agent
running the same shipped checker, before and after; its trust limit is that step reporting a
command's output faithfully, which is the same trust the existing artifact gate already
rests on. The practical difference today is that the checker prints the fields Codex reads
from disk but not the two the engine needs, so Codex is fully proven and Claude fails closed
until that additive contract lands.

## Remaining limitations

- **The Claude side depends on `ctx_eebb7b40614f`'s `check_artifacts.py`.** It is verified
  against that file as it stands, but that file is uncommitted and owned elsewhere; if its
  field names or shapes change, `real-gate.js` and `measuredDelivery` follow. Against the
  committed helper the Claude loop fails closed, visibly, with
  `unmeasured_repair_delivery` — the honest state, not a silent regression.
- **The engine trusts the gate step to report a command faithfully.** That is the whole of
  its measurement, and it is the same trust the existing independent artifact gate already
  rests on; there is no controller-owned filesystem to do better with. Both prompts say to
  report what the command printed and not to compute, infer or fill in anything.
- **The underlying contradiction is still there**, and it is not mine to resolve. Any declared
  repair node will keep failing its own gate for as long as its QA node is failing; the driver
  now works with that rather than around it. If the planner would rather exclude the loop's QA
  edge from evidence dependencies, this accommodation should be withdrawn.
- **A repair node needs one extra dispatch** to complete after its QA node passes. That is
  visible in the transition log and in the executed order above, and it costs one iteration.
- **No host proof.** No real Codex run drove `flow.py` and no real Workflow run drove the
  engine; the executors are controlled stubs. Every gate, freshness state and publication
  around them is real, which is a step up from the previous dispatch but is not a host run.
- **The finalization instruction is a prompt, not an enforcement.** A node that ignores it
  and edits the source anyway is caught by the QA evidence going stale — closure does not
  happen — but the run then does not converge on its own; it burns iterations until a
  threshold stops it. That is the `test_a_repair_that_mutates_after_the_qa_pass_does_not_reach_closure`
  behaviour, and it is fail-closed rather than self-healing.
- **`repair_delivered` trusts the driver's own `qa_evidence`.** A transition without it — an
  older log, or one written by something else — is not a delivery, which is fail-closed but
  costs an in-flight run one re-dispatch after an upgrade.
- The external-change gate, the `binding_identity`/`readiness_status` coupling to planner-owned
  shapes, and the byte-identical-verdict requirement recorded in
  `T15-legacy-repair-admission.md` are unchanged.
