# T15 — independent diagnosis of candidate defects C1, C2 (and C3)

Scope: the two candidate-level defects filed in
`T15-codex-new-product-evaluation.md` §4.2, diagnosed independently against the
immutable candidate `e30ccc7cec9120815f0d9bc92204adf465f666d4` at
`/private/tmp/meta-intent-host-campaign.XX6yRo/T15/candidate`. C3 is assessed only
where direct executable evidence exists.

Method: every claim below is backed by a run, not by reading strings. Experiments
were executed against throwaway copies in the session scratchpad
(`…/scratchpad/{c1,c1b,c2,c2p,c3,c3b,c3c,actor,repo2}`). Nothing under the evidence
root, the candidate, the fixtures, the actor's project or this repository was
modified; no gate was run against the real project with `--write-report`. Repair
prototypes exist only as scratch copies of the scripts.

Verified first: the four scripts in this diagnosis are byte-identical between the
candidate export and this checkout's `claude/meta-skill/`, so a repair lands on the
same code the candidate ran.

---

## Verdict summary

| # | Filed as | Diagnosis |
|---|---|---|
| C1 | filename-glob decision discovery causes orphan false positives | **Confirmed, and stronger than filed.** The contract's own required A0 artifact deterministically BLOCKS the gate that the same contract makes a precondition for `/run`. A protocol-compliant bootstrap cannot pass lens 1 without mis-wiring. |
| C2 | no gate consumes a pending-choice queue | **Confirmed by end-to-end reproduction.** An unresolved choice, wired exactly the way `bootstrap-audits.md:272` prescribes, passes lens 1, passes the readiness preflight (`status: "ready"`, zero blockers) and reaches node dispatch on the Codex path. Today's block is entirely incidental. |
| C3 | `product_intent.py` generates acceptance boilerplate | **Misattributed — reject as filed.** The string is actor-authored. A *different*, real, executable defect sits next to it: the candidate **forces** the undifferentiated acceptance block that the evaluation charged to the actor as A5. |

---

## C1 — decision discovery by filename

### The documented contract

`knowledge/bootstrap-audits.md` defines three artifact families that all live under
`.allforai/**` and all begin with `decision-`:

| Line | Artifact | Role |
|---|---|---|
| `:264`, `:270` | `.allforai/bootstrap/decision-coverage.json` | **Required** A0 audit output; validated by `validate_audit_outputs.py decision-coverage` |
| `:286`, `:287` | `.allforai/<domain>/decision-<id>.json` | Phase A **decision artifact**; validated by `validate_audit_outputs.py decision` |
| (`bootstrap-planning.md:45`) | `.allforai/product-concept/decision-journal.json` | Confirmation **journal**, referenced by requirement provenance |

Only the middle family is a decision to wire. `check_decision_inputs.py:46-47`
identifies all three by name:

```python
gathered = [os.path.relpath(p, base) for p in
            glob.glob(os.path.join(base, ".allforai/**/decision-*.json"), recursive=True)]
```

`bootstrap-audits.md:333`: "`/run` is offered only when lenses **1 and 2** return OK
and the node-spec audit below passes." Lens 1 is this script (`:311`).

### Counterexample 1 — the contract blocks itself (minimal, 2 files)

`…/scratchpad/c1/proj`: one node, empty `decision_inputs`, plus exactly the A0 output
`bootstrap-audits.md:264` requires.

```
$ python3 validate_audit_outputs.py decision-coverage .allforai/bootstrap/decision-coverage.json
OK                                                        exit=0     ← contract satisfied

$ python3 check_decision_inputs.py .
BLOCKED: decision wiring incomplete:
  - orphan (unwired): .allforai/bootstrap/decision-coverage.json     exit=1
```

Expected: OK — no decision artifact exists, so nothing can be orphaned.
Actual: BLOCKED. Running A0 as specified makes lens 1 unpassable, and lens 1 gates
`/run`. The only escapes are to skip a required audit, delete its output, or declare
an audit artifact to be a product decision.

### Counterexample 2 — the confirmation journal

`…/scratchpad/c1b/proj`: same workflow, `decision-journal.json` instead.

```
BLOCKED: decision wiring incomplete:
  - orphan (unwired): .allforai/product-concept/decision-journal.json   exit=1
```

The journal is normally rescued by `consumed_sources` — `product_intent.validate_scope`
adds a journal path only when it is reached through a *confirmed scoped requirement*
(`product_intent.py:139-140`). Any project holding a journal whose requirements are
not in the current `task_scope` — a legacy or local-change workflow, a scope narrowed
after freeze — loses that rescue and gets a false orphan on its own provenance record.

### Reproduction on the real cell

`…/scratchpad/actor/proj` (copy of `T15/codex/new-product/project`):

```
as shipped                                        → OK                exit=0
same graph, decision-coverage.json un-wired       → BLOCKED: orphan   exit=1
```

The actor's gate passes only because `product-direction.decision_inputs` carries
`.allforai/bootstrap/decision-coverage.json` — an audit output declared as a product
decision input. That is the workaround the false positive forces, and it is exactly
what the evaluation observed. The renaming of `decision-request-{1,2}.json` →
`cli-input-{1,2}.json` is the same pressure applied to the actor's own CLI inputs.

### Root cause

Identity by filename, where the naming convention is shared by three artifact
families with different roles. **The candidate already ships the discriminator**:
`validate_audit_outputs.validate_decision_artifact` (`validate_audit_outputs.py:35-38`)
defines a Phase A decision as `{id, decision, rationale}`, and `bootstrap-audits.md:287`
requires every Phase A artifact to pass it. `decision-coverage.json` (`captured`/`missing`)
and `decision-journal.json` (`schema_version`/`batches`) both lack `decision`.

### Proposed repair (narrow, backward compatible)

Replace the name test with a shape test that consumes the existing schema. Do **not**
import `validate_audit_outputs` — `skills/bootstrap/SKILL.md:749-767` does not copy it
into generated projects, so inline the three-key predicate:

```python
DECISION_KEYS = ("id", "decision", "rationale")

def is_decision_artifact(path):
    """True when path holds a Phase A decision artifact. Unreadable stays True (fail closed)."""
    try:
        with open(path, encoding="utf-8") as f:
            obj = json.load(f)
    except (OSError, ValueError):
        return True
    return isinstance(obj, dict) and all(key in obj for key in DECISION_KEYS)
```

then filter the glob with it in `main()`. Backward compatible in both directions: every
genuine Phase A artifact must already validate as `{id, decision, rationale}`, so none
is dropped; an unreadable `decision-*.json` still blocks. `find_orphan_decisions` and
`check_decision_inputs` are untouched, so
`shared/scripts/orchestrator/test_check_decision_inputs.py` (4 tests, passes both
before and after — it calls `find_orphan_decisions` directly) needs no change.

Prototype: `…/scratchpad/patchtree/check_decision_inputs.py`. Results across six
fixtures — F1 A0 output un-wired **OK**, F2 journal un-wired **OK**, F3 real project
with the audit artifact un-wired **OK**, F5 resolved decision **OK**, F4/F6 unresolved
decision **BLOCKED** (the C2 half, below).

Once this lands, the actor's `product-direction.decision_inputs` should drop
`.allforai/bootstrap/decision-coverage.json` — the wiring exists only to clear this
false positive.

---

## C2 — an unresolved choice is not blocked by any gate

### What is *not* the problem

Three real safeguards were ruled out one at a time:

- **`validate_scope`** — genuinely enforces requirement provenance, revision currency,
  user confirmation, journal projection and per-node `requirement_refs` wiring
  (`product_intent.py:93-155`). It has no concept of a *decision artifact's content*.
- **Freshness** — `input_dependencies` is a `FRESHNESS_FIELDS` member
  (`check_artifacts.py:293`), so the queue file is hashed into every node's contract.
- **`missing_runtime_command` / `stale_evidence`** — correct consequences of an
  unpublished, un-stacked plan (evaluation F1/F4), orthogonal to the choice itself.

### Reproduction of the escape

`…/scratchpad/c2/proj`, starting from the actor's project. Two changes, neither of
which resolves, invents or excludes any product choice:

1. Wire one pending choice **exactly the protocol's way** (`bootstrap-audits.md:272`):
   a new `.allforai/tech-spec/decision-platform-stack.json` =
   `{"id": "platform-stack", "decision": null, "status": "pending", "rationale": "The user has not chosen a platform stack."}`,
   added to `technical-contract.decision_inputs`, `decision_mode: "brainstorm"`.
2. Close the two orthogonal blocker classes: set the readiness spec's
   `runtime_command.commands` to a binary that exists, and publish the eight node
   *contracts* through the public `evidence_freshness` `observe` → `publish` API
   (verification command `["true"]`; all eight returned `valid`).

`pending-choices.json` was left untouched — all five choices `status: "pending"`,
`choice: null`, `excluded: false`, file-level `status: "pending"` — as were the
readiness spec's own `pending_decisions: [5 items]` and
`execution_authorized_in_this_task: false`.

| Gate | Expected | Actual |
|---|---|---|
| `validate_audit_outputs.py decision decision-platform-stack.json` | reject an unmade choice | `OK` exit 0 |
| `check_decision_inputs.py .` (lens 1) | block | `OK: decision_inputs present and every decision is wired to a consumer` exit 0 |
| `validate_dag_structure.py .` (lens 2) | — | `OK` exit 0 |
| `validate_unattended_readiness.py .` | `not_ready` | **`status: "ready"`, `blockers: []`, `warnings: []`**, exit 0 |
| `flow.py:run_preflight()` | 6 (refuse) | **0 (proceed)** |
| `flow.py:first_pending_node()` | none dispatchable | **`product-direction`** |

`/run` starts. `product-direction` is dispatched; `technical-contract` — the node that
owns the unmade platform choice — becomes dispatchable as soon as its DAG predecessors
close. The five choices are still `pending`.

### The inversion

Same fixture, one further change — **resolve** one choice in `pending-choices.json`:

```
readiness → not_ready, 8 × stale_evidence
```

Freshness fires on the *answer* and is silent on its *absence*. The queue file is
hashed, never read. That is a re-verification hook, not a decision gate, and the
evaluation's §3.5 reading is right: today's block is incidental.

### Where the guard is missing on each host

`bootstrap-audits.md:19` and the Codex `bootstrap.md:181-184` run
`check_decision_inputs.py` at **bootstrap time only**. Neither host's `/run` runs it:

- **Claude** — `orchestrator-template.md:32-38` and `run-engine/engine-core.js:137-142`
  (`readinessPrompt`) run `validate_unattended_readiness.py --write-report` and nothing
  else. That script contains no `decision_mode`, no `decision_inputs` and no
  pending-choice concept (verified by grep and by reading all 560 lines).
- **Codex** — `flow-template.py:420-437` (`run_preflight`) calls only
  `validate_unattended_readiness.py`. `independent_artifact_gate` (`:453-465`) shells
  `check_artifacts.py --node`, which status-checks **exit** artifacts;
  `input_dependencies` are never status-checked.

The only in-run guards are prose in the node prompt, and they are asymmetric:

- Claude `engine-core.js:173` (and `run-engine.workflow.js:183`) — *"First read these
  required decision inputs: … — if any is **missing**, return outcome hard_fail"*. An
  **existence** instruction: an artifact with `decision: null` is present, so it does
  not trip. `:191` adds *"an unresolved product choice is a hard failure"* — a correct
  rule with no artifact to evaluate it against.
- Codex `flow-template.py:523-543` (`build_prompt`) — **does not mention
  `decision_inputs` at all**. Its nearest analogue is item 9, "unresolved product
  requirements remain failures". `grep decision_mode flow.py` → nothing;
  `grep pending-choices flow.py` → nothing. The Codex path, which is the path this
  cell ran, has strictly less protection than the Claude one.

Meanwhile `orchestrator-template.md:69-70` states the intended contract plainly —
"Run Policy is never a product decision: unresolved decision_inputs return to
interactive bootstrap and cannot be approved by continue/accept" — and `:96-97`
promises "A product-decision owner is a preflight blocker for the next `/run`". The
vocabulary exists (`evidence_freshness.repair_responsibility:339-343` already routes
`pending_requirement` / `pending_product_confirmation` to
`{owner: "interactive-bootstrap", responsibilities: ["product-decision"]}`). Nothing
computes an *unresolved decision*.

Also inert: `unattended-run-readiness-spec.json`'s `pending_decisions` and
`execution_authorized_in_this_task: false`. `validate_unattended_readiness.py` reads
only `forbid_mid_run_user_prompts`, `forbid_hidden_fallback_completion`,
`max_repair_attempts`, `long_task_policy`, `required_repair_loops` and
`required_capabilities`. The actor's most explicit "do not execute" declaration is
never read by the gate that decides whether to execute.

### Proposed repair (one function, three existing consumers)

Do **not** add a gate. `validate_scope` is already called by lens 1
(`check_decision_inputs.py:42`), by the readiness preflight
(`validate_unattended_readiness.py:324`) and by
`evidence_freshness.scope_blockers:267-277` → `repair_responsibility`. Emitting one
new typed blocker there reaches all three with no new plumbing:

```python
DECISION_KEYS = ("id", "decision", "rationale")   # shared with the C1 repair

def _pending_decisions(root, workflow):
    """Blockers for wired decisions the user has not made.
    Presence is not resolution: an empty placeholder satisfies the existence gate."""
    blockers = []
    for node in workflow.get("nodes", []):
        for path in node.get("decision_inputs", []) or []:
            artifact = _decision_artifact(root, path)      # None when not a decision artifact
            if artifact is None:
                continue
            if artifact.get("decision") in (None, "", [], {}) or artifact.get("status") == "pending":
                blockers.append({"code": "pending_decision", "node_id": node.get("node_id"),
                                 "message": f"{path}: the product choice is not made; return to "
                                            "interactive bootstrap. An unattended run never chooses it."})
    return blockers
```

called once inside `validate_scope`, plus three lines in
`repair_responsibility` routing `pending_decision` to the **existing**
`{owner: "interactive-bootstrap", responsibilities: ["product-decision"]}`. No new
schema, no new file, no new architecture: the unresolved-ness test is the
`decision` field that `validate_decision_artifact` already mandates.

Prototype: `…/scratchpad/patch2/orchestrator/{product_intent,evidence_freshness}.py`,
installed into `…/scratchpad/c2p/proj` (the *ready* escape fixture).

```
unresolved:
  check_decision_inputs.py .           BLOCKED  - pending_decision: …decision-platform-stack.json   exit=1
  validate_unattended_readiness.py .   status = not_ready
                                       - pending_decision technical-contract
                                       (technical-contract's freshness repair owner becomes
                                        "interactive-bootstrap (product-decision)")
  flow.py run_preflight()              6      ← /run refuses

resolved (decision: "Node + Postgres", contracts republished):
  check_decision_inputs.py .           OK       exit=0
  validate_unattended_readiness.py .   status = ready, blockers = 0
```

Blocks only while the choice is unmade; silent once it is made. Note this repair is
what makes `decision_mode: "brainstorm"` + a future `decision_inputs` path
(`bootstrap-audits.md:272`) load-bearing rather than declarative — which is precisely
the mechanism the evaluation's A2 says the actor should have used.

**Ordering note.** The C1 repair must land with or before the C2 repair. Without C1,
adding a real `.allforai/<domain>/decision-<id>.json` to the plan is safe, but the
required `decision-coverage.json` still forces the mis-wiring that C2's blocker would
then read.

### Optional, smaller, complementary

`validate_unattended_readiness._validate_policy_spec` could reject a spec whose
`execution_authorized_in_this_task` is `false` or whose `pending_decisions` is
non-empty. That is a one-branch change against a key the actor already wrote. It is a
belt on top of the fix above, not a substitute — it depends on a planner writing that
key, whereas `pending_decision` derives from the artifact.

---

## C3 — assessed on executable evidence only

### As filed: misattributed

The evaluation attributes `"The product direction explicitly addresses: <goal>"` to
`product_intent.py`'s "gap-question path".

```
$ grep -rn "explicitly addresses" <candidate>/            → no matches
$ grep -n "explicitly addresses" <project>/.allforai/bootstrap/cli-input-1.json
44:  "The product direction explicitly addresses: Match local needs to available help."
64:  "The product direction explicitly addresses: Provide reliable, private coordination."
```

`cli-input-1.json` is the actor's own hand-written input to `product_intent.py`. The
string appears in no candidate source file and in no `coordinator-answer-*.txt`. The
script copies acceptance verbatim from its input; it synthesises none. **C3 as filed
should be withdrawn from the candidate's defect list and, if kept at all, recorded as
an actor wording deviation.**

### The real defect next to it: the acceptance block is candidate-forced

`product_intent.py:888`, in the `plan` operation:

```python
node["acceptance"] = [a for i in selected for a in i["acceptance"]]
```

Every node's acceptance is the **union** of every acceptance statement of every
requirement it references — and `:593-594` then *enforces* that equality, raising
`stale_requirement` for any node whose acceptance differs.

`…/scratchpad/c3/proj` — apply the evaluation's own repair step 4 (scope acceptance
per node) by dropping the atomic-claim line from `operator-documentation`, 9 → 8
statements:

```
validate_scope   → {'code': 'stale_requirement', 'node_id': 'operator-documentation',
                    'message': 'operator-documentation: Product goals and acceptance differ from confirmed intent'}
readiness        → not_ready
```

The only lawful narrowing is fewer `requirement_refs` — but `_product_contract`
(`:510-518`) requires, per requirement, that its consuming nodes' `responsibilities`
cover `{product, experience, technical, implementation, documentation, verification}`,
and `not_applicable` may omit **only** `experience` and `technical` (`:512`).
`…/scratchpad/c3c/proj`:

```
not_applicable = {}                        → OK
not_applicable = {"experience": "..."}     → OK
not_applicable = {"documentation": "..."}  → invalid_scope:
                                             "Product stage applicability needs explicit planning reasons"
```

So `product`, `implementation`, `documentation` and `verification` are mandatory for
**every** requirement. With six requirements and eight nodes, spreading refs to satisfy
that while keeping any node's ref list short is hard, and the all-refs-on-all-nodes
assignment is the trivially safe one — after which `:888` forces the identical
acceptance block, and `not_applicable: {}` and the tautological `coverage-matrix.json`
follow mechanically.

**This reclassifies evaluation A5 (and part of A2's "no applicability decision") from
actor deviation to candidate-generation gap.** The evaluation's repair step 4 is not
executable as written against this candidate. A bounded repair is either (a) allow
`not_applicable` to omit any stage with an explicit written reason, keeping the
"explicit planning reasons" requirement that already exists at `:512`, or (b) let a
node declare a subset of a referenced requirement's acceptance statements and check
subset-of rather than equality at `:593-594`. (a) is smaller and reuses the field's
existing semantics; both are bounded and consume existing schemas. Either way this is
a design change with product consequences and belongs to the coordinator, not to a
repair worker — I am recording it, not recommending it be applied unreviewed.

---

## Regression check

Prototypes were exercised in a scratch clone of this checkout (`…/scratchpad/repo2`),
never in the worktree. Both prototype files were installed into the clone and the
suites re-run.

| Suite | Baseline | With both prototypes |
|---|---|---|
| `claude/meta-skill/tests/unit` (all) | **645 passed, 2 failed** in 247s | **645 passed, 2 failed** in 246s |
| `shared/scripts/orchestrator/test_check_decision_inputs.py` | 4 passed | 4 passed |

The two failures are identical before and after and are environment artifacts of the
scratch clone, not code failures:
`test_evidence_freshness.py::test_same_commit_distinct_dirty_states_and_unrelated_baseline_revisions[claude|codex]`
fail with `fatal: not a git repository` because the clone was made without `.git`.
No regression is attributable to either prototype.

`claude/meta-skill/tests/unit` must be run alone: collecting it together with
`shared/scripts/orchestrator` produces 23 duplicate-basename collection errors even at
baseline.

A repair worker should still re-run `claude/meta-skill/tests/unit` inside a real git
checkout, so those two tests execute rather than error.

## Handoff notes for a repair worker

Repair sites, smallest first (all four files are byte-identical to the candidate in
this checkout as of this diagnosis):

| Order | File | Change |
|---|---|---|
| 1 | `claude/meta-skill/scripts/check_decision_inputs.py` | inline `DECISION_KEYS` / `is_decision_artifact`; filter the glob in `main()` (C1) |
| 2 | `claude/meta-skill/scripts/orchestrator/product_intent.py` | `_decision_artifact` / `_pending_decisions`; one call inside `validate_scope` (C2) |
| 3 | `claude/meta-skill/scripts/orchestrator/evidence_freshness.py` | route `pending_decision` in `repair_responsibility` (C2) |

`claude/meta-skill/scripts/orchestrator/validate_unattended_readiness.py` needs **no**
change: it already extends its blockers with `validate_scope`'s output
(`:324`), which is why the readiness preflight closes for free.

`claude/meta-skill/scripts/` is mirrored into generated projects
(`skills/bootstrap/SKILL.md:749-767`), and the actor's project holds 13 byte-identical
copies. Existing projects keep the old gate until re-bootstrapped; that is the normal
copy semantics, not a regression, but it means the fix does not retroactively block an
already-generated plan.

**Concurrency.** A separate production repair worker is active in this checkout and has
staged an unrelated repair-loop routing change to
`codex/meta-skill/knowledge/flow-template.py`. None of the three repair sites above is
touched by it. The `build_prompt` observation in the C2 section is against the candidate
version of `flow-template.py`; re-check it against that worker's result before acting on
it.

---

## What this diagnosis did not do

No source, test, fixture, candidate or campaign-artifact file was edited; no commit, no
install, no `/run`, no account, trust, remote or issue mutation, no nested agent. Gate
re-runs used scratchpad copies and never `--write-report` against the real project. The
repair prototypes exist only in the scratchpad and are proposals, not applied changes.
