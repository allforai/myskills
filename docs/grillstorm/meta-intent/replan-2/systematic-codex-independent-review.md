# Independent review — Codex driver canonical-ledger integration

Read-only review of the Codex host-integration task against the approved plan and ADRs
0004–0007. Scope: `codex/meta-skill/knowledge/flow-template.py`,
`codex/meta-skill/test_flow.py`, `codex/meta-skill/knowledge/orchestrator-template.md`,
and the claims in `systematic-codex-integration-report.md`. Nothing was edited; every
finding below was reproduced with a temporary pytest file outside the repository, driving
the real driver and the real `repair_authorization.py` / `run_safety.py` helpers. The
repros are reproduced verbatim at the end so they can be re-run without trusting this
document.

## Verdict

The write-ahead ledger integration itself is sound: `authorize` → `start` → executor →
`settle`, unknown-never-settles, all-or-none charging, memoised reads keyed to the ledger's
own bytes. I could not break the charge accounting, the replay refusal, or the
unresolved-grant block. What is not sound is what the driver does *around* the ledger —
node selection. Two of the four contracts the task was measured against fail in shapes ADR
0006 explicitly declares supported:

| # | Severity | Contract | Status |
|---|---|---|---|
| 1 | **High** | ADR 0006 — "success in one role cannot cancel another role's blocker" | **fails** |
| 2 | **High** | ADR 0005 — "an exhausted obligation … final acceptance still requires satisfying that sibling" | **fails** (same defect, end-to-end) |
| 3 | Medium | ADR 0006 / template — a halt "survives a restart and is released only by independent revalidation" | **fails when `run_safety.py` is absent** |
| 4 | Medium | template — "no node dispatchable but pending nodes remain → report blocked nodes"; independent branches keep running | **fails**: one obligation's blocked accounting kills the whole run before untouched branches ever run |
| 5 | Low | receipt validation, settle-verdict handling, blocked-report detail, per-iteration gate cost | see below |

Findings 1 and 2 are the same code path and should be fixed together. They are reachable
only through a cross-loop role overlap, which `validate_bootstrap.py:1814` permits by
design (it refuses only a repair node listed as its *own* loop's QA/closure node) and which
ADR 0006 states must remain supported.

---

## Finding 1 (High) — a repair-role dispatch bypasses the node's own exhausted-obligation blocker

**Location** `codex/meta-skill/knowledge/flow-template.py:1084-1099` (`_pending_state`),
specifically line 1086.

```python
for node in nodes:
    node_id = node_identity(node)
    if node_id in repair_nodes:          # ← checked first, before every blocker
        if selected is None:
            selected = node
        continue
    if complete.get(node_id):
        continue
    if (node_id in routed or node_id in closure_blocked or node_id in unbounded
            or node_id in exhausted):    # ← never reached for a repair node
        blocked.append(node_id)
```

`repair_nodes` is the set of repair nodes of currently-open loops. The membership test runs
*before* the `exhausted` / `unbounded` / `routed` / `closure_blocked` tests, so a node that
is a repairer in loop A and a QA obligation in loop B is dispatched as a repairer even when
its own loop-B budget is spent and the driver has otherwise decided it must be blocked.

**Failure scenario** — loop A `{qa: qa1, repair: shared, max_attempts: 2}`, loop B
`{qa: shared, repair: fixer, max_attempts: 1}`; `qa1` and `shared` have both failed with
current reports; loop B's single attempt is spent and settled `failed`.

Expected (ADR 0005/0006): `shared` is an exhausted obligation → blocked and reported.
Observed:

```
selected: shared
blocked:  ['qa1', 'fixer', 'closeA', 'closeB']      # 'shared' is absent
```

**Proposed correction.** Move the blocker tests ahead of the repair-role test, i.e. compute
the blocked sets first and refuse to select a repair node that is itself blocked in another
role:

```python
blocked_now = routed | closure_blocked | unbounded | exhausted
for node in nodes:
    node_id = node_identity(node)
    if node_id in blocked_now:
        blocked.append(node_id)
        continue
    if node_id in repair_nodes:
        ...
```

A repairer that is itself an exhausted obligation is a stopped run, not a dispatch. The
existing shared-repair test (`test_a_shared_repair_charges_only_the_obligations_that_still_have_budget`)
does not catch this because there the exhausted sibling is a pure QA node.

---

## Finding 2 (High) — the run reaches `done: true` with an exhausted, never-repaired obligation

**Location** consequence of Finding 1, via `_pending_state:1077`
(`if complete.get(qa_node_id) or last_failed_transition(...) is None: continue`) and
`main:1808-1816` (`all_ready` → transition `completed`).

Once Finding 1 dispatches `shared` in its repair role, the attempt writes `shared`'s own
exit artifact. `independent_artifact_gate` then reports `shared` complete, so line 1077
drops it from the `exhausted` set, its loop-B blocker disappears, and the run finishes.
The obligation was satisfied by the node writing its own verdict during a dispatch
authorized against a *different* loop's budget — exactly the "repairer independently
accepting its own work" shape ADR 0006 rules out, and the "silently treated as accepted"
outcome ADR 0005 rules out.

**Failure scenario** — same fixture, driven end-to-end through the real `main()`:

```
executed: ['shared', 'qa1', 'fixer', 'closeA', 'closeB']
ledger:   [('fixer', ['shared'], 'settled', 'failed'),      # loop B: 1/1 spent, delivered nothing
           ('shared', ['qa1'],   'settled', 'delivered')]   # loop A only
stdout:   {"passed": true, "done": true, "iterations": 5}
```

Two things to note in that trace beyond the acceptance itself:

- `fixer` — the repair node whose budget is exhausted — was **executed with no
  authorization at all** (no third ledger entry). `main:1756` only charges when
  `qa_nodes_routed_to` is non-empty; once `shared` read as complete, `fixer` became an
  ordinary pending node and got a free repair dispatch after its budget was spent.
- The `orchestrator-template.md` rule this contradicts is explicit: "the run may not
  finish around it either — an exhausted obligation is refused, never accepted."

**Proposed correction.** Fixing Finding 1 removes the dispatch that starts this. In
addition, an obligation whose budget is spent should stay blocked on the *ledger's* record
until its own QA rerun records a passing transition, rather than being dropped by
`complete.get(qa_node_id)` alone — completeness measured from artifacts on disk is exactly
what a repairer can manufacture. A cheap guard: in the `exhausted` loop, only skip the
obligation when its **latest transition** is `completed` *and* that transition is the QA
node's own attempt, not a repair-role dispatch. `qa_nodes_routed_to` should likewise refuse
to authorize a repair node that is a blocked obligation elsewhere, so the two paths cannot
disagree.

---

## Finding 3 (Medium) — with `run_safety.py` absent, a halt leaves no durable fence

**Location** `flow-template.py:326-345` (`quarantine_outputs`, returns `False` when
`run_script` finds no helper), `main:1780-1793`.

The template and the task report both state the halt "survives a restart and is released
only by independent revalidation". That holds only when `run_safety.py` is present: it is
`run_safety.py` that writes the marker and, on failure, deliberately leaves
`safety-quarantine.lock` behind as the fence. When the helper is missing, `run_script`
returns `None`, `quarantine_outputs` returns `False`, and the driver reports
`quarantine_persisted: false` and exits 4 — with no marker, no lock, and nothing in the
run state that any later gate consults.

**Failure scenario** — routing project without the helper; the executor writes its exit
artifact and a warning; Run Policy `on_safety_warning: halt`:

```
halt payload: {"error": "recorded Run Policy halted on safety warning",
               "quarantined_outputs": ["verify.json"], "quarantine_persisted": false, ...}
marker exists: False   lock exists: False   safety_halted(): False
outputs still ready: [True]
after clearing run-warnings.json → safety_halted(): False; blocked = ['accept']
```

i.e. the quarantined node reads as **completed** from its own outputs, and its closure is
the only thing still blocked. The only surviving fence is `run-warnings.json` plus a
mutable Run Policy — the two things `run_safety.py`'s own recovery note says must not
release a quarantine ("Do not clear quarantine merely because Run Policy changed or a
worker reported success"). The driver already writes a durable `failed` transition naming
the quarantined artifacts, but no gate reads it.

This is reachable in practice for any project bootstrapped before `run_safety.py` was added
to the helper list (`codex/meta-skill/skills/bootstrap.md:148`, added on this branch), and
neither `run_preflight` nor `validate_unattended_readiness.py` checks that the helper
exists.

**Proposed correction.** Two options, either sufficient: (a) treat an unpersisted
quarantine as itself a halt the driver records — write the lock path directly when
`quarantine_outputs` returns `False`, since `safety_halted()` already honours it; or
(b) refuse to start at all when a declared run has no `run_safety.py`, the same fail-closed
shape `repair_ledger_unreadable` gives the ledger. (a) is the smaller change and keeps the
"never assume persistence" property, because the lock means "a quarantine was attempted".

---

## Finding 4 (Medium) — an unresolved grant on one obligation stops the whole run before untouched branches run

**Location** `main:1756-1770`.

When a repair node is selected and `authorize_repair_dispatch` returns `None` — an
unresolved earlier grant is the realistic case, exactly what a killed driver leaves — the
driver `return 6`s immediately. Node selection happens in list order, so a repair node that
precedes an independent branch ends the run before that branch is ever dispatched.

**Failure scenario** — the standard four-node loop plus an untouched `independent` node,
with one grant left in state `started` (killed between claim and outcome):

```
executed: []          # nothing ran at all
stderr:   {"error": "repair dispatch was not authorized; no attempt may run without a
                     durable per-obligation grant", "obligations": ["verify"]}
```

The scenario fixture `ordinary_qa_failure_with_independent_branch` and the template both
say an independent branch keeps running while a QA obligation is blocked; ADR 0005 scopes
untrusted state to "affected work". An unresolved authorization is per-obligation
(`consumption` returns `status: ok` and reports it under `unresolved`; only `authorize`
refuses), so the affected work is that loop, not the run.

**Proposed correction.** Treat an unauthorizable repair dispatch as a *blocked node*, not a
run-ending error: add the repair node and its obligations to the blocked set inside
`_pending_state` (by asking the ledger for `unresolved` on those obligations), let the rest
of the graph drain, and end through the existing "no dispatchable node; pending nodes remain
blocked" path — which already has a place to name the reason, next to
`invalid_repair_attempt_history` and `unbounded_repair_loops`. That also fixes the
reporting gap in Finding 5b.

---

## Finding 5 (Low) — four smaller ones

**5a. `settle`'s verdict is discarded.** `settle_repair_dispatch:618-628` ignores the
helper's return entirely, so a refused settlement (helper gone, ledger lock held by an
abandoned writer, an outcome the state does not permit) is indistinguishable from a
successful one. Verified: `settle_repair_dispatch(root, {'authorization_id': 'never-granted'},
'delivered')` returns `None` while the helper returns
`{'status': 'blocked', 'untrusted': 'unknown_authorization', ...}`. The run continues and
the next dispatch for that obligation is then refused with a message about authorization
rather than about the settlement that silently failed. Correction: check the verdict; a
failed settle should be reported on the iteration line at minimum.

**5b. The refusal names no authorization ids.** `authorize_repair_dispatch` already holds
the `consumption` verdict, which carries `unresolved: [{authorization_id, state, ...}]`.
The `"repair dispatch was not authorized"` payload drops it, so the operator is told to run
a reconcile without being told what to reconcile. One field, no behaviour change.

**5c. Receipt identity is not checked.** `authorize_repair_dispatch:607/612` validates
`status == "authorized"` and `execution_allowed is True`, but never that the returned
`authorization_id`/`run_id` are the ones it asked for; `settle` is then sent an id the
driver assumes. Against a *worker*-tampered helper this changes nothing (the helper is the
authority and lives in the workspace-write sandbox), so this is a helper-bug guard, not a
security control — but it is two comparisons and it is the kind of mismatch that otherwise
surfaces as a mis-attributed charge. Related: `run_codex` returning 127 (CLI not found —
nothing executed) is settled `failed`, asserting an execution that never started; the
charge is correct either way, but `aborted` is the outcome the ledger has for it and the
grant is already `started`, so if this matters it belongs in the `start` ordering, not in
`settle`.

**5d. Two full artifact-gate passes per iteration.** `_pending_state` computes
`independent_artifact_gate` for every node, and `qa_nodes_routed_to:630-636` computes the
same map again for the selected node's charge; `blocked_pending_nodes` computes a third on
the reporting path. Each call is a subprocess. On a 60-node graph that is ~120–180 helper
spawns per iteration. Passing the already-computed `complete` map into
`qa_nodes_routed_to` removes a third of it with no behaviour change.

---

## What I checked and found correct

- **Write-ahead accounting.** `authorize` then `start`, both durable before `run_codex`;
  execution proceeds only on `execution_allowed: true`; the charge is at the grant, not the
  delivery. Matches ADR 0006.
- **Unknown never settles.** 124/130 and the safety-halt path skip `settle`, leaving the
  grant unresolved; an uncaught exception in the executor path leaves the same state.
  `SETTLEABLE` on the helper side refuses `unknown`. No path refunds an attempt.
- **Run identity.** `consumption` first, `initialize` only on `untrusted: missing_ledger`
  with a fresh id; an existing/ambiguous ledger returns `None` and blocks. `initialize`
  itself re-verifies the workflow shows no execution. No driver-side reset exists, and
  `adopt_history`/`reconcile` are correctly absent from the run path (ADR 0007).
- **Memoised reads.** Keyed by `(project_root, ledger digest)`; every helper write changes
  the digest, so a stale verdict cannot be served after a charge. The unbounded-cache note
  in the task report is accurate and immaterial.
- **Ledger unreadable → nothing runs.** `repair_ledger_unreadable` blocks every node for a
  run with declared loops, and the payload names the recovery. Correct per ADR 0005.
- **Shared repair, funded obligations only.** `eligible_obligations` filters exhausted
  siblings, and the helper's all-or-none `authorize` makes a partial charge impossible.
  The sibling is not discharged — *except* through Findings 1/2.
- **Safety halt is run-wide** in `_pending_state:1034` and `open_repair_loops:1006`, marker
  *or* lock, and is not answered by a repair route. Correct — subject to Finding 3 for
  durability.
- **Declared budgets outrank the generic caps.** `failure_threshold` / `stagnation_limit`
  raise only, stay finite, and leave non-loop nodes at the generic value. (Observation, not
  a finding: `count_consecutive_failures` counts only *contiguous* trailing entries for a
  node, so in an interleaved QA↔repair loop the count resets to 1 each cycle and the raised
  threshold is rarely the operative bound. Pre-existing behaviour, unchanged by this task.)
- **Tests are behavioural.** The scenario tests drive the real selection or the real
  `main()` and compare against the fixture's `expect`; the fixture is never asserted against
  itself. The four retargeted expectations kept their original coverage — I checked each
  against its pre-change assertions and found none weakened.

## Accuracy notes on `systematic-codex-integration-report.md`

- §6 states `codex/meta-skill/skills/bootstrap.md` "is not mine to edit, and whether the
  generator actually copies them was not verified". On this branch that file *has* been
  edited (+6 lines) and now lists both helpers at lines 147–148, and
  `claude/.../bootstrap/SKILL.md:779-780` copies them. The bullet is stale; the residual
  risk is legacy `.allforai/` trees, which is Finding 3.
- §6's "If either is absent at runtime the driver fails closed … a missing `run_safety.py`
  means the halt is reported with `quarantine_persisted: false` — but that is a fail-closed
  run" is not correct for `run_safety.py`. It is fail-closed for the ledger; for the
  quarantine the run stops *this* invocation but records nothing durable, and the outputs
  read as complete on the next one (Finding 3).
- §3's "An exhausted obligation is blocked, not re-run … the run cannot finish around it"
  holds only when the obligation is a pure QA node (Findings 1/2).
- Everything else I spot-checked in the report matches the code, including the ledger
  table in §2 and the test inventory in §5.

---

## Repros

Save as `test_review_repro.py` **outside** the repo (it imports the owned files read-only)
and run with `python3 -m pytest <file> -q -s` from the repo root. Every assertion below is
written to state the contract, so a failure is the finding.

```python
import importlib.util, json, sys
from pathlib import Path

REPO = Path('<repo root>')
spec = importlib.util.spec_from_file_location('tf', REPO / 'codex/meta-skill/test_flow.py')
tf = importlib.util.module_from_spec(spec)
sys.path.insert(0, str(REPO / 'codex/meta-skill'))
spec.loader.exec_module(tf)
flow, write = tf.flow, tf.write


def overlap_project(tmp_path, spent_on_shared=1, budget_b=1):
    """'shared' is the repair node of loop A and a QA obligation of loop B."""
    nodes = [
        {'node_id': 'qa1', 'hard_blocked_by': [], 'exit_artifacts': ['qa1.json']},
        {'node_id': 'shared', 'hard_blocked_by': ['qa1'], 'exit_artifacts': ['shared.json']},
        {'node_id': 'fixer', 'hard_blocked_by': ['shared'], 'exit_artifacts': ['fixer.json']},
        {'node_id': 'closeA', 'hard_blocked_by': ['qa1', 'shared'], 'exit_artifacts': ['closeA.json']},
        {'node_id': 'closeB', 'hard_blocked_by': ['shared', 'fixer'], 'exit_artifacts': ['closeB.json']},
    ]
    write(tmp_path / '.allforai/bootstrap/workflow.json', {'nodes': nodes, 'transition_log': []})
    tf.install_repair_ledger(tmp_path)
    write(tmp_path / '.allforai/bootstrap/unattended-run-readiness-spec.json', {
        'version': 1, 'required_repair_loops': [
            {'scope': 'A', 'qa_node_ids': ['qa1'], 'repair_node_id': 'shared',
             'closure_node_ids': ['closeA'], 'max_attempts': 2},
            {'scope': 'B', 'qa_node_ids': ['shared'], 'repair_node_id': 'fixer',
             'closure_node_ids': ['closeB'], 'max_attempts': budget_b}]})
    workflow = {'nodes': nodes, 'transition_log': [tf.qa_failed('qa1'), tf.qa_failed('shared')]}
    write(tmp_path / 'qa1.json', {'status': 'failed'})
    write(tmp_path / 'shared.json', {'status': 'failed'})
    write(tmp_path / '.allforai/bootstrap/workflow.json', workflow)
    tf.stamp_attempt_evidence(tmp_path, workflow, 'qa1')
    tf.stamp_attempt_evidence(tmp_path, workflow, 'shared')
    for _ in range(spent_on_shared):
        tf.repair_dispatched(tmp_path, workflow, qa_node_id='shared',
                             repair_node_id='fixer', settle='failed')
    return workflow


def test_finding_1_exhausted_obligation_is_dispatched_because_it_is_also_a_repairer(tmp_path, monkeypatch):
    workflow = overlap_project(tmp_path)
    tf.gate_by_ready_artifacts(tmp_path, monkeypatch)
    assert flow.repair_attempts_spent(tmp_path, 'fixer', 'shared') == 1
    blocked = flow.blocked_pending_nodes(tmp_path, workflow)
    assert 'shared' in blocked, f'exhausted obligation not blocked; blocked={blocked}'


def test_finding_2_run_finishes_with_an_exhausted_obligation(tmp_path, monkeypatch, capsys):
    overlap_project(tmp_path)
    tf.gate_by_ready_artifacts(tmp_path, monkeypatch)
    def executor(project_root, node_id, attempt):
        write(project_root / f'{node_id}.json', {'status': 'passed'})
    _, executed = tf.drive_real_routing(tmp_path, monkeypatch, executor, max_iterations=12)
    out = capsys.readouterr().out
    ledger = json.loads((tmp_path / flow.REPAIR_LEDGER).read_text())['authorizations']
    print('executed:', executed)
    print('ledger:', [(e['repair_node_id'], e['obligations'], e['state'], e['outcome'])
                      for e in ledger])
    assert '"done": true' not in out, ("the run reached final acceptance while loop B's "
                                       'obligation was exhausted and never repaired')


def test_finding_3_halt_without_the_quarantine_helper_leaves_no_durable_fence(tmp_path, monkeypatch, capsys):
    tf.routing_project(tmp_path)                      # note: no install_run_safety
    def executor(project_root, node_id, attempt):
        write(project_root / f'{node_id}.json', {'status': 'passed'})
        write(project_root / '.allforai/bootstrap/run-warnings.json',
              {'warnings': ['workspace escape attempted']})
    _, executed = tf.drive_real_routing(tmp_path, monkeypatch, executor, on_safety_warning='halt')
    print('halt payload:', capsys.readouterr().err.strip().splitlines()[-1])
    workflow = flow.load_json(tmp_path / '.allforai/bootstrap/workflow.json')
    node = next(n for n in workflow['nodes'] if n['node_id'] == executed[0])
    print('outputs still ready:', [flow.artifact_ready(tmp_path, flow.artifact_path(a))
                                   for a in node['exit_artifacts']])
    write(tmp_path / '.allforai/bootstrap/run-warnings.json', {'warnings': []})
    tf.gate_by_ready_artifacts(tmp_path, monkeypatch)
    print('blocked after the warnings file is cleared:',
          flow.blocked_pending_nodes(tmp_path, workflow))
    assert flow.safety_halted(tmp_path), 'nothing durable records the halt'


def test_finding_4_an_unauthorized_repair_dispatch_stops_an_independent_branch(tmp_path, monkeypatch, capsys):
    workflow = tf.repair_project(tmp_path, qa_report={'status': 'failed'},
                                 transition_log=[tf.qa_failed('verify')])
    workflow['nodes'].append({'node_id': 'independent', 'hard_blocked_by': [],
                              'exit_artifacts': ['independent.json']})
    write(tmp_path / '.allforai/bootstrap/workflow.json', workflow)
    tf.repair_dispatched(tmp_path, workflow, settle=None)   # killed between claim and outcome
    tf.gate_by_ready_artifacts(tmp_path, monkeypatch)
    def executor(project_root, node_id, attempt):
        write(project_root / f'{node_id}.json', {'status': 'passed'})
    _, executed = tf.drive_real_routing(tmp_path, monkeypatch, executor, max_iterations=6)
    print('stderr:', capsys.readouterr().err.strip().splitlines()[-1])
    assert 'independent' in executed, ('an unresolved grant on one obligation ended the whole '
                                       f'run before an untouched branch ran; executed={executed}')


def test_finding_5a_settle_verdict_is_discarded(tmp_path):
    tf.repair_project(tmp_path, qa_report={'status': 'failed'},
                      transition_log=[tf.qa_failed('verify')])
    assert flow.settle_repair_dispatch(tmp_path, {'authorization_id': 'never-granted'},
                                       'delivered') is None
    verdict = flow.authorization_request(tmp_path, {'operation': 'settle',
                                                    'authorization_id': 'never-granted',
                                                    'outcome': 'delivered'})
    assert verdict['status'] == 'blocked', verdict   # the driver never sees this
```

Observed results (2026-09-10, at `47ea2855`): findings 1–4 fail as written; 5a passes,
which *is* the finding (the refusal is real and the driver drops it). No repository file
was modified by this review other than this document, and no broad suite was run — only
the temporary repro file above.
