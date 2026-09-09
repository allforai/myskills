# Systematic remediation — structural gate robustness

Workstream 2 of `systematic-remediation-plan.md`: *"Make validation reject malformed input with a
current structured verdict. Validate shape before semantic graph operations; stale ready files cannot
grant admission, including when report generation fails."* Plus the safety-halt readiness consumption
the coordinator assigned mid-task (ADR 0006).

Owned and changed:

- `claude/meta-skill/scripts/orchestrator/validate_bootstrap.py`
- `claude/meta-skill/scripts/orchestrator/validate_unattended_readiness.py`
- `claude/meta-skill/tests/unit/test_validate_bootstrap.py`
- `claude/meta-skill/tests/unit/test_validate_unattended_readiness.py`
- `claude/meta-skill/tests/unit/test_planning_audit_contracts.py`

Nothing else. No host engine, ledger, driver template, skill document, test-isolation loader,
`run_safety.py`, commit, install or host launch. `codex/meta-skill/scripts` is a symlink to
`claude/meta-skill/scripts`, so both hosts execute these two files as the same inodes; there is no
adapter copy to keep in agreement. `shared/scripts/orchestrator/validate_bootstrap.py` is a separate
legacy validator with a deliberately different contract (`id`/`node` fields) and was not touched.

## The governing idea

Three rules, applied everywhere below.

1. **A node identifier is what a graph rule can address.** Every rule keys a map by it, orders a
   report by it and anchors a blocker to it. Only a non-empty string does all three. A list or dict
   raises when hashed; a number raises when ordered against a string; none of them name anything a
   user can act on. So the identifier's shape is decided *before* any rule reads the graph, by one
   gate, and the rules read only the addressable map.
2. **A gate that raises has decided nothing.** A traceback is not a verdict. Both hosts consume this
   as a JSON report plus an exit code, so every fault reachable from a user's current
   `workflow.json` has to come back as a typed blocker.
3. **A published report is a claim about the current graph.** A previous `ready` that outlives the
   run which supersedes it is a stale verdict presented as a current one. Publication therefore
   replaces or removes the old report; it never silently leaves it standing.

## Defects reproduced and corrected

### D1 — the run-boundary gate raised on a malformed node list and left a stale `ready` (B1)

`T15-parity-gates-independent-review.md`'s blocking defect. `structural_gate_blockers` ran before any
shape check, and `effect_stage_ownership_findings` sorted a map keyed by the raw `node_id`.

Red, on the working tree as found, exactly the review's repro:

```
File ".../validate_unattended_readiness.py", line 331, in validate_unattended_readiness
    blockers.extend(structural_gate_blockers(project_root))
File ".../validate_bootstrap.py", line 1825, in effect_stage_ownership_findings
    for node_id, node in sorted(nodes.items()):
TypeError: '<' not supported between instances of 'str' and 'int'
EXIT=1
--- report on disk:
{"status":"ready"}
```

Green, same fixture:

```json
{"status": "not_ready",
 "blockers": [{"code": "malformed_workflow_node",
               "message": "workflow.json nodes[0] node_id must be a non-empty string, got 1; an
                           identifier that cannot key the graph names no node in a plan, a
                           dependency edge or a blocker"}, ...]}
--- report on disk: not_ready
```

### D2 — an unhashable identifier crashed *both* public CLIs

Wider than D1: a non-empty list or dict `node_id` raised out of the bootstrap CLI as well.

Red, as found:

```
dict-id  validate_bootstrap.py             TypeError: cannot use 'dict' as a set element
dict-id  validate_unattended_readiness.py  TypeError: cannot use 'dict' as a dict key
list-id  validate_bootstrap.py             TypeError: cannot use 'list' as a set element
list-id  validate_unattended_readiness.py  TypeError: cannot use 'list' as a dict key
```

The bootstrap-CLI crash sat at `validate_workflow:499` (`node_ids = {_node_id(n) for n in ...}`) and,
once past it, inside `check_artifacts.freshness_admission` — a semantic reader being handed a node it
cannot address. Green: both CLIs exit 1 with an empty stderr and a named `node_id` fault.

### D3 — `validate_workflow` accepted an identifier no rule could use

At base, `{"node_id": 1}` and a duplicated `node_id` both returned `[]` from `validate_workflow`
(verified against `HEAD:validate_bootstrap.py`, which the concurrent T15 worker had not modified in
this function). The presence test `if not node.get("node_id")` asked only whether something was
there. Now the type is checked, duplicates are reported, and a non-object node entry is refused
before it is dereferenced.

### D4 — a scalar `qa_node_ids` raised out of the repair-loop gate

Found by the new malformed-collection tests, on code the T15 worker had left unchanged:

```
qa_nodes = [n for n in (loop.get("qa_node_ids") or loop.get("qa_nodes") or []) if _text(n)]
TypeError: 'int' object is not iterable
```

A declared node list is a collection of identifiers or it declares nothing; `_declared_node_ids` now
says so once, and the readiness gate reports the container's own shape.

### D5 — a closure whose `hard_blocked_by` was a string was admitted as ready

A correctness hole, not only a crash. `qa_node_id not in "runtime-repair"` is a substring test, so a
closure node whose edges were a bare string satisfied the "closure must be blocked by the repair"
rule. Red, against the base module:

```
HEAD: string hard_blocked_by admits closure  -> []      # no blockers at all: status ready
```

Green: `closure_not_blocked_by_repair_loop`.

### D6 — an undecodable node-spec and a non-file approval path raised

Red, against the base module:

```
HEAD: undecodable node-spec            -> RAISES UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff
HEAD: non-string approval_record_path  -> RAISES TypeError: unsupported operand type(s) for /: 'PosixPath' and 'int'
```

Both are now typed blockers — `unreadable_node_spec`, `pending_human_gate`. An unreadable brief is
not an accepted one: the non-interactive, fallback and long-task rules are all decided from that
text, so a node whose brief cannot be read has no verdict to give, and no verdict is not an
acceptance.

### D7 — a raising gate left the previous `ready` on disk as this run's answer

Red, against the base module:

```
HEAD: main() when the gate raises     -> RAISES RuntimeError: store unreadable
HEAD: report left on disk             -> ready
HEAD: main() with a read-only dir     -> RAISES PermissionError: ...unattended-run-readiness.md
```

Green: `main` returns a `readiness_gate_error` refusal in the report's own shape and publishes it;
and `_publish` replaces the report atomically where it can, writes in place when only the file is
writable, and removes the superseded report when neither works.

### D8 — a recorded safety halt did not block the run (coordinator scope)

ADR 0006: *"A safety halt stops new dispatch across the current run."* Red, against the base module:

```
HEAD: quarantined project ->  ready
HEAD: held safety lock    ->  ready
```

Green: `unresolved_safety_quarantine`, `invalid_safety_quarantine`, `unreconciled_safety_halt`.

## What changed

### `validate_bootstrap.py`

- `_addressable_id` / `_addressable_nodes` — one definition of "a value that can name a node", and
  the map every graph rule reads. Entries that cannot be addressed are dropped, never repaired:
  giving one a synthetic id would let a malformed record participate in routing decisions.
- `validate_workflow` — refuses a non-object node entry, refuses an identifier that is not a
  non-empty string, refuses a reference entry that is not one, and stops the per-node semantic checks
  for an unaddressable node instead of handing it to `check_artifacts`.
- `_declared_node_ids` — a repair-loop declaration's node list is read as a collection or as nothing.
- `workflow_shape_findings` / `workflow_shape_blockers` — the one gate that owns node shape,
  including duplicate identifiers (one entry silently replaces the other in every map, so the
  validated graph would not be the graph on disk).
- `structural_gate_blockers` — shape first, and alone. The routing and ownership rules are now safe
  on a malformed graph, but a verdict computed from the addressable subset describes a graph the user
  does not have, and reporting it beside the shape fault invites repairing the wrong thing. The
  bootstrap CLI reaches the same ordering through `validate_workflow`, which `main` runs first.

The rendering wrappers `validate_repair_loop_declaration` / `validate_effect_stage_ownership` are
unchanged and still emit `code: message`; the new shape findings enter the bootstrap CLI through
`validate_workflow`, which owns that entry, rather than as a second producer.

### `validate_unattended_readiness.py`

- `_safety_halt_blockers` — decided first, before anything about the plan. The marker's mere
  presence blocks (`lexists`, so a broken symlink or a directory counts); its content is read only to
  say *what* is quarantined, never to decide whether it counts, and a marker that cannot be read is
  additionally reported as invalid. The `.lock` blocks on its own: it is left behind when a
  quarantine could not be published, and the missing marker is then exactly what is untrustworthy.
  Neither record is ever cleared here — clearing one is a reconciliation decision requiring
  independent revalidation.
- Shape gate before the structural gate, with the graph-reading checks (`freshness_states`, the
  per-node loop, `_validate_repair_loop_spec`) deferred while a shape fault holds — the same
  deferral idiom the file already used for `scope_blockers`.
- Typed blockers for an unreadable node-spec, a non-file `approval_record_path`, a non-list declared
  node list, an unaddressable QA or closure identifier, and a non-list `hard_blocked_by`.
- `_publish` (used by both the JSON and the Markdown report) and a `main` that converts an
  undecided gate and an unpublishable verdict into refusals.

Preserved unchanged: every plan-confirmation gate and its provenance rules, the freshness and
external-change contracts, `_validate_policy_spec`, the repair-budget rules, and the ADR-0003
codex-CLI warning.

## Evidence

New tests, all parametrized over both host trees where they run through the copied public CLI.

| Suite | Result |
|---|---|
| `test_validate_bootstrap.py` — 28 existing + 7 new functions (37 cases) | 65 passed |
| `test_validate_unattended_readiness.py` — 15 existing + 20 new functions (58 cases) | 73 passed |
| `test_planning_audit_contracts.py` — 21 existing + 11 new functions (44 cases) | 65 passed |
| `test_run_safety.py` (the helper's own suite, unchanged) | 5 passed |
| `test_bootstrap_scope.py`, `test_plan_confirmation_gate.py`, `test_acceptance_allocation.py` with the gate suites | 235 passed |
| `codex/meta-skill/test_flow.py` | 108 passed |
| `claude/meta-skill/tests/unit`, full, less one concurrent worker's in-flight file | **957 passed, 0 failed** (5m29s) |

What the new tests hold, beyond the refusals above:

- **Valid input is unchanged.** `test_a_well_formed_graph_still_reaches_the_structural_rules` and
  `test_the_canonical_loop_is_still_admitted_after_the_shape_gate` assert that the gate that refuses
  an unroutable loop still admits the routable one, and that the shape gate did not become a blanket
  refusal. `test_a_project_with_no_safety_record_is_still_admitted` does the same for the halt.
- **No rule answers from the addressable subset.** When a malformed identifier is present, the
  readiness report carries only the shape code (and `invalid_scope`, the scope gate independently
  refusing the same record) — never `unowned_effect_stage`, `undeclared_repair_loop_routing` or
  `missing_node_spec`.
- **Both hosts, one rule.** Every CLI test runs against both `claude` and `codex` script trees, and
  the bootstrap CLI is asserted to refuse the same graphs `/run` refuses.
- **The stale report does not survive.** Each CLI refusal test first establishes a `ready` report on
  disk, then asserts the published report equals the refusal that superseded it.

## Limits, stated rather than papered over

- **`test_validate_unattended_readiness.py` cannot be run by bare `pytest` in this tree right now**,
  for a reason that predates and is independent of this work. The concurrent test-isolation worker
  moved the suite to `..module_isolation.load`; `validate_unattended_readiness` imports
  `check_artifacts` and `evidence_freshness` lazily inside the function body (unchanged, at
  `HEAD:...:349` and `:376`), and those bare imports no longer resolve after the loader restores
  `sys.path`. All results above were therefore obtained with
  `PYTHONPATH=claude/meta-skill/scripts/orchestrator`. That harness is a workaround, not a fix, and
  the fix belongs to the isolation workstream — it is the loader's contract for lazily-importing
  modules, and changing it was outside this task's boundary. Without it, 15 pre-existing failures
  appear in that file, none of them related to any change here.
- **Import sections were preserved, not reverted.** Per the coordinator, the import worker's
  `..module_isolation.load` form is kept in all three test files. Two import lines were *extended*
  (extra `_validate_bootstrap.X` bindings; `_readiness = load(...)` so `main` and the module object
  are reachable for the publication tests) without changing the isolation mechanism or the names
  already bound. One pre-existing test body still contains a bare
  `import validate_unattended_readiness as m`, which the isolation change also breaks; it was left
  for that worker rather than rewritten here.
- **`tests/unit/test_repair_authorization.py` is failing, and is not this work's.** It and
  `scripts/orchestrator/repair_authorization.py` are untracked files another worker is editing right
  now; they reference neither owned validator (verified by grep). The full-suite run 20 minutes
  before this report showed 3 failures there and 1012 passes elsewhere; run alone minutes later it
  showed 53 — it is a moving target, not a regression from these changes.
- **One rule that can only be honoured by the exit code.** If the report's directory *and* the
  report file are both unwritable, the superseded `ready` cannot be replaced or removed. The gate
  still returns a `unpublished_readiness_report` refusal on stdout and exits 1, which is what both
  hosts act on (Codex `run_preflight` → 6; Claude's readiness prompt requires the command to
  succeed). `test_an_unpublishable_verdict_is_still_a_refusal` asserts exactly that and no more; the
  neighbouring test asserts the read-only-directory case *is* fully replaced in place.
- **No live host session.** Both hosts execute the same file through a symlinked tree, and the tests
  drive each host's copied script tree by `subprocess` as `/run` does, but no Claude `/run` or Codex
  `codex exec` was launched — consistent with this task's boundary. The 60 host acceptance cells are
  unchanged by this work.
- **Duplicate node identifiers are a new refusal.** No existing fixture in the repository relies on
  them (full suite green), but a project graph that happens to repeat an id will now be blocked where
  it previously ran with one entry silently shadowing the other.
- **`unresolved_safety_quarantine` blocks on existence alone**, including a marker whose recorded
  `status` is not `quarantined`. That is deliberate per the coordinator's instruction and ADR 0006:
  no automatic clearance, and a status field is not authority to resume.
