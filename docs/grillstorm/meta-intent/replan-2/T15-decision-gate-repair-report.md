# T15 — repair of diagnosed C1 and C2 (decision-gate discrimination and the unresolved choice)

Scope: exactly the two defects `T15-decision-gate-diagnosis.md` confirmed. C3 is not
touched — it is an acceptance-scope design change with product consequences and belongs
to the coordinator. No required stage was relaxed, no user choice invented, and no
real-host fixture, candidate export or campaign record was modified.

Base: `2cc347afc4cfdbfac8c628eb0f652b02ac476e81` — committed, **not accepted**: both
independent reviews rejected it (mixed-wave terminal outcome loss, shared repair budget
mismatch, misleading shape-validation claim). It is the tree this repair was written
against, not an approved baseline. No commit made here.

---

## What changed

| File | Change |
|---|---|
| `claude/meta-skill/scripts/orchestrator/product_intent.py` | `decision_record` / `_decision_artifact` / `_unresolved` / `_pending_decisions`; one call inside `validate_scope`, carried through every return path |
| `claude/meta-skill/scripts/check_decision_inputs.py` | the gathered glob is filtered by `decision_record` (C1) |
| `claude/meta-skill/scripts/orchestrator/evidence_freshness.py` | `pending_decision` joins the existing `product-decision` routing branch (C2) |
| `claude/meta-skill/knowledge/bootstrap-audits.md` | lens 1: what the gathered set is, and that presence is not resolution |
| `claude/meta-skill/tests/unit/test_decision_gate.py` | new; 42 cases, both hosts, through the copied public CLIs |

`codex/meta-skill/scripts` is a symlink to `claude/meta-skill/scripts`, so both host
adapters ship the same three files; the tests copy them per host and exercise the
generated-project flat layout on each.

`validate_unattended_readiness.py` needed no change: it already extends its blockers
with `validate_scope`'s output. `find_orphan_decisions` and `check_decision_inputs`
(the functions) are untouched, so `shared/scripts/orchestrator/test_check_decision_inputs.py`
still passes unchanged.

---

## C1 — identity by shape, not by filename

`decision_record(project_root, path)` answers "is this a decision record?" for a
`decision-*.json` path:

- Not named `decision-*` → not a record.
- Unreadable, malformed, or not a JSON object → an **empty record**, never a
  non-record. A shape test discriminates families; it must not dismiss a decision it
  cannot read. This is the prototype's sharpest edge case: the three-key
  `all(k in obj)` predicate proposed in the diagnosis would have made
  `{}`, `{"id": …, "status": "pending"}` and a truncated file invisible to the gate.
- Carries a decision marker — `decision`, `rationale`, or a queued `status`
  (`pending` / `unresolved` / `open` / `deferred`) → it is a product choice, and **no
  sibling family's keys can override that**.
- Otherwise, and only if it holds a sibling family's *whole* contract shape:
  the A0 coverage audit (`captured` and `missing` lists, every `missing` entry naming
  `id`, `rationale` and `consumer_node`, `bootstrap-audits.md:264`), a recorded CLI
  request envelope (a non-empty `operation`, no decision `id`), or a requirement source
  (a non-empty `requirements` list of items with ids, no decision `id`).

**Recognition is by the full shape, never by one key** — the correction the coordinator's
read-only probe forced. Two cases it reproduced against the first version, both now fail
closed and both are public-driver tests:

| Boundary case | First version | Now |
|---|---|---|
| `{id, status: "pending", operation: "choose"}` | dismissed as a CLI envelope | a pending decision: orphan when unwired, `pending_decision` when wired |
| `{id, status: "pending", decision: null, rationale: "", schema_version: 1, batches: []}` | dismissed as the journal | a pending decision at every driver |

A malformed sibling is likewise not a sibling: `{captured: "all", missing: null}` under a
`decision-*.json` name stays a decision record and blocks.

Consequences, all covered by tests:

- The contract no longer blocks itself. `decision-coverage.json` written exactly as A0
  prescribes, and validated by `validate_audit_outputs.py decision-coverage`, passes
  lens 1 unwired.
- A genuine unwired decision is still an orphan — complete, partial, empty, malformed
  or non-object alike.
- Once this lands, the actor's `product-direction.decision_inputs` can drop
  `.allforai/bootstrap/decision-coverage.json`; that wiring existed only to clear the
  false positive. **Not applied here** — it is the actor's frozen project, not a
  repair surface.

### Deliberate divergence from the diagnosis: the confirmation journal

The diagnosis's counterexample 2 asks for `decision-journal.json` to stop being an
orphan. **It is not excluded, and the behaviour is unchanged.** Reason:
`claude/meta-skill/tests/unit/test_legacy_profile_authority.py:236` codifies the
opposite as intended — a decision recorded in the journal that the plan does not
consume is named unwired "until the scope is planned". That is a *true unconsumed
decision*, and the brief forbids dropping one. The journal already has its legitimate
rescue: `validate_scope` adds it to `consumed_sources` when it is reached through a
confirmed scoped requirement, and `test_bootstrap_scope.py` asserts that path.

So the journal stays a decision record for the consumption invariant (C1) while being
excluded from the *resolution* judgement (C2) — a batch of many choices has no single
`decision` field to read. The exclusion needs a *well-formed* journal (a string
`schema_version`, non-empty `batches` with `batch_id` and a `decisions` list) and no
decision marker; anything less is not a journal and is judged.

**The coordinator confirmed this disposition** (`msg_ebe50e236ea9`): preserve the journal
consumption invariant for now; there is no requirement to weaken an existing true
unconsumed-choice guard. The open contract question — whether lens 1 should keep naming an
unconsumed journal at all — is recorded, not decided here.

---

## C2 — an unmade choice is a typed blocker, not a gap

`_pending_decisions` runs once inside `validate_scope`, so the three existing consumers
inherit it with no new plumbing: lens 1 (`check_decision_inputs.py:42`), the readiness
preflight (`validate_unattended_readiness.py:324`, which is what `/run` refuses on for
both hosts) and `evidence_freshness.scope_blockers` → `repair_responsibility`.

A wired `decision_inputs` entry is judged unresolved when it is missing, unreadable, an
empty placeholder, a partial artifact missing any of `{id, decision, rationale}`, has an
empty or `null` `decision`, or carries `status: pending | unresolved | open | deferred`.
Two things are deliberately *not* judged:

- a path that is also one of the node's `requirement_refs` — the scope contract owns
  its confirmation, and rereading it as a choice would block every existing scoped plan;
- the sibling families above, so the actor's `decision-coverage.json` workaround does
  not become a new blocker.

Routing reuses the existing owner verbatim:
`{owner: "interactive-bootstrap", responsibilities: ["product-decision"]}`. No new
schema, no new file, no new gate.

The blocker carries `node_id`, so `scope_blockers` groups it per node and an unrelated
node keeps its own repair owner. Recovery is the existing freshness contract, not a
special case: resolving the choice clears `pending_decision` immediately, but the node
whose contract consumed the artifact is stale until it is re-observed and republished
(`snapshot()` already fingerprints `decision_inputs`). Readiness returns to `ready` only
then.

`validate_unattended_readiness._validate_policy_spec` was **not** extended to read
`execution_authorized_in_this_task` / `pending_decisions`. The diagnosis calls it a
belt, not a substitute; it depends on a planner writing the key, whereas
`pending_decision` derives from the artifact.

---

## Evidence

All runs in a real git checkout, `--tb=short`. The diagnosis's "645 passed, 2 failed" was a
no-`.git` scratch-clone artifact; here the same suite is fully green.

A parallel correction worker (see below) was rewriting `validate_bootstrap.py`,
`test_bootstrap_scope.py`, the JS run-engine, `flow-template.py` and the readiness-spec
validation *inside this worktree while I worked*. A suite run against the live worktree at
09:26 therefore reported **105 failed, 578 passed** — every failure traced to their
in-flight state (their new "unconfirmed node set … presented as a delta" error out of
`validate_bootstrap.py`, which the shared `project()` fixture trips during
`publish_contract`, plus their own run-policy driver tests). That number is not
attributable to this repair and is recorded here only so it is not mistaken for one.

To get a number that *is* attributable, the suite was re-run in a throwaway
`git clone` of this repository checked out at `2cc347af`, with **only these five files**
copied in (`git status` in the clone shows exactly them and nothing else):

| Suite | Baseline at `2cc347af` | `2cc347af` + this repair |
|---|---|---|
| `claude/meta-skill/tests/unit` | **647 passed** ¹ | **689 passed** (647 + the 42 new) |
| `codex/meta-skill/{test_flow,test_install}.py` | 43 passed ² | 43 passed ² |
| `shared/scripts/orchestrator` | 109 passed ² | 109 passed ² |
| `claude/meta-skill/tests/unit/test_decision_gate.py` | 42 failed ³ | 42 passed |

¹ measured in this worktree before the parallel editors touched it.
² measured in the clone, baseline column with the three production files reset to their
`HEAD` content and restored afterwards.
³ measured in the clone with the same reset: 42 failed at `HEAD`, 42 passed with the
repair restored. Baseline swaps were moved into the clone after the coordinator pointed
out that in-place swaps in the shared checkout invalidate the other editors' concurrent
gate runs; the shared checkout now holds only the repaired state of my files, verified
byte-identical to the clone.

Exact commands (from the clone root, `python3` = CPython 3.14.7):

```
python3 -m pytest claude/meta-skill/tests/unit -q --tb=short -p no:cacheprovider
python3 -m pytest codex/meta-skill/test_flow.py codex/meta-skill/test_install.py -q --tb=line -p no:cacheprovider
cd shared/scripts/orchestrator && python3 -m pytest . -q --tb=line -p no:cacheprovider
```

`claude/meta-skill/tests/unit` must be run alone; collecting it together with
`shared/scripts/orchestrator` produces duplicate-basename collection errors at baseline
too.

`validate_meta_contracts.py` and `validate_generalization_boundaries.py` both exit 0 after
the `bootstrap-audits.md` edit. `shared/scripts/orchestrator/check_codex_meta_skill_parity.py`
fails, but only on `codex/meta-skill/install.sh`, `flow-template.py` and the plugin version
files — none of which this task touched; pre-existing, reported, not repaired here.

Red-then-green was verified on the *final* tests, not only on drafts: with the three
production files restored to their `HEAD` content and the new test file unchanged, 42/42
fail; with the repair, 42/42 pass. The C2 escape is reproduced inside the red run — an
unresolved choice wired the protocol's way yields `status: "ready"` before the fix.

### What the new tests actually assert

Every case runs the copied CLIs in a temporary project, parametrized over both host
adapters (`claude` and `codex` script trees copied into `.allforai/bootstrap/scripts/`) —
no unit call stands in for a host gate.

| Test | Covers |
|---|---|
| `test_required_audit_output_and_cli_request_are_not_orphan_decisions` | audit + CLI-envelope positives; the A0 output is validated by its own contract validator first, then all three gates pass and readiness is `ready` |
| `test_an_unwired_decision_artifact_still_blocks_whatever_its_shape` | genuine orphan negative across complete / partial / placeholder / malformed / non-object / envelope-keys / journal-keys / malformed-audit, with the audit output present and not reported |
| `test_an_unresolved_wired_choice_blocks_every_public_driver_and_routes_to_bootstrap` | ten unresolved shapes — absent, `null`, blank, `status: pending`, no `decision` key, `{}`, and the four mixed sibling-key cases (envelope, journal, requirement, malformed audit) — block lens 1, `validate_bootstrap.py` and readiness, and the node's freshness repair owner becomes `interactive-bootstrap (product-decision)` |
| `test_a_resolved_choice_restores_readiness_only_with_fresh_evidence` | resolution clears the blocker, readiness stays `not_ready` on stale evidence, and returns to `ready` only after republication |
| `test_settled_and_non_decision_inputs_leave_unrelated_work_executable` | a resolved choice, a wired A0 audit output and a wired well-formed journal do not block; a second node's unmade choice blocks only that node, and the first node's repair owner is unchanged |

---

## Concurrency

A parallel correction worker owns the JS run-engine and its mirror, `flow-template.py`,
both `orchestrator-template.md` files, `validate_bootstrap.py`, the readiness *spec*
validation (`_validate_repair_loop_spec`) and the fixtures in `test_bootstrap_scope.py` /
`test_validate_unattended_readiness.py`. It was writing to this worktree throughout this
task; the coordinator confirmed the split (status `msg_049c4f42ef46`) and I escalated the
overlap when I saw it.

The two changes to `validate_unattended_readiness.py` are independent: theirs adds
repair-loop budget blockers and warnings, mine reaches that gate only through
`validate_scope`, which they do not touch. Nothing in this repair edits a file that
worker owns; `knowledge/bootstrap-audits.md` is not one of theirs — it is lens 1's own
contract text, changed here only to describe what the gate now does.

The practical consequence is the one in the Evidence section: a suite run against the
live worktree measures both workers mid-flight, so the attributable run was done in an
isolated clone. **Whoever integrates these branches should re-run the full suite on the
merged tree** — no worker has seen another's finished state.

### For the planning worker (`ctx_a377a4a12a25`), which owns `bootstrap-audits.md`

I made one hunk in that file and will make no further edits to it. Preserve it, or fold
its content into whatever replaces that section. It is the only text in the repository
that states what lens 1 now does. Exact location: the **"1. 闭环 — decision closure"**
block of "Final gate: three-lens DAG validation". Line 4 of the block changes
`` `decision-*.json` is referenced by ≥1 node `` to `decision record is referenced by ≥1
node`, and two paragraphs follow it: one saying identity is the artifact's shape rather
than its filename (naming `decision-coverage.json`, a CLI request envelope and a
requirement source as the families that are not orphan decisions, and that an unreadable,
partial or placeholder artifact still is one), and one saying presence is not resolution
(an absent, empty or `pending` `decision` is a `pending_decision` blocker at lens 1, at
`validate_unattended_readiness.py` and at the freshness repair owner, routed to
interactive bootstrap as a `product-decision`).

One refinement landed in code after that hunk was written and is *not* reflected in it:
a sibling family is recognised by its **whole** contract shape and a decision marker
overrides every sibling shape. If that section is rewritten, that sentence is worth
carrying; the existing hunk is not wrong without it.

---

## Not done, and why

- **C3** — acceptance-scope design change; recorded by the diagnosis as the
  coordinator's call.
- **The journal exclusion from lens 1** — see the divergence note above; the coordinator
  confirmed the current invariant stands, so the contract question is recorded, not acted on.
- **`shared/scripts/orchestrator/check_decision_inputs.py`** — a copy that had already
  diverged from the plugin script before this task (it has no `validate_scope` call).
  Neither host loads it: `codex/meta-skill/scripts` symlinks to the Claude tree and
  generated projects copy from there. Left as found; flagged as pre-existing drift.
- **The actor's frozen project** — `product-direction.decision_inputs` still carries
  the audit output. Unwiring it is now safe but belongs to a re-bootstrap, not here.
- No commit, install, `/run`, remote, issue or nested agent.
