# T15 evaluation — Codex / missing-product-docs (completed real host attempt)

Evaluator report. Read-only. This document is the only file this evaluation wrote.
No candidate, source, fixture, test, ledger, receipt or campaign artifact was modified.
No product implementation, install, settings change, `/run`, push, issue write or
subagent spawn occurred.

## 1. Subject and identity

| Item | Value |
|---|---|
| Cell | `/private/tmp/meta-intent-host-campaign.XX6yRo/T15/codex/missing-product-docs` |
| Host | Codex in Orca, hook-attested `provider: codex` |
| Codex session / thread | `01a08380-8346-7002-84b4-e60683133a1f` |
| Orca terminal | `term_e46ba203-1dae-4fd1-ab0c-adf7ae8be969` |
| Actor task / dispatch | `task_e7b6a9f84198` / `ctx_99be2c71a3e0` |
| Transcript source identity | `T-fkX8onvf4J5oIVYP11gBHw2GsInMWB` (stable across all four captures) |
| Actor outcome | `worker_done --outcome failed`, released |
| Candidate (campaign manifest) | `source_commit` = `production_commit` = `e30ccc7cec9120815f0d9bc92204adf465f666d4`, `tree_sha256` `c1114a94d89c2ea8d8e7bc8c496576b9750957e347769980dc75dee006704fc4`, 504 files |

Candidate supersession note: `T15/evaluator-private.md` still names `ed430dfc…`
(tree `27d6e622…`) as the accepted candidate and points at the retired
`/private/tmp/meta-intent-T15-ed430dfc` export. The live campaign root pins
`e30ccc7c…`. That is the candidate this task named, and the manifest in the
current root agrees. Treated as documented history, not a discrepancy.
Ledger drift, coordinator-owned, not evaluated here: `evaluator-private.md`
records Git init only for the first Claude large-code project (`eb52d16`); this
Codex project also carries a coordinator-made synthetic commit
`a2ffa80 Synthetic scenario initial source`. Source preservation is unaffected
(see §3.6).

## 2. Evidence admissibility

### 2.1 Candidate identity — verified

Recomputed independently:

- All 504 manifest `sha256` entries match the exported candidate bytes: **0 mismatches**.
- All 51 `loaded_assets` entries in the actor receipt match both the pinned
  manifest hash **and** the current on-disk bytes: **0 mismatches**, **0 assets
  absent from the manifest**.
- `admit_evidence.py` reported `mode_mismatches: []` and `symlink_mismatches: []`
  and did not report `missing-manifest-git-modes`, so recorded Git modes and
  symlink targets match the actual exported filesystem.

### 2.2 Bounded admission CLI — `unverified`

`admit_evidence.py` against the unmodified actor receipt:

```
{"status": "unverified",
 "reasons": ["candidate-mismatch", "missing-raw-dialogue", "missing-session-identity"],
 "semantic_verdict": "not-evaluated", "mode_mismatches": [], "symlink_mismatches": []}
```
exit 1.

The receipt shape does **not** match the CLI contract. The CLI expects
`session_id`, `source_root`, `loaded_files[{path,sha256}]`, `raw_dialogue{path,sha256}`;
the actor wrote `session_identity{…}`, `candidate_root`, `loaded_assets[…]`,
`transcript{…}`. Two of the three reasons are therefore field-naming artifacts,
not substantive failures. Isolated with an evaluator-side scratchpad copy that
renamed fields only and deliberately left `raw_dialogue` absent:

```
{"status": "unverified", "reasons": ["missing-raw-dialogue"], ...}
```

So after normalization every candidate-identity check passes and exactly one
substantive reason remains: **no raw-dialogue artifact is registered in the
receipt**. Normalization is the coordinator's prerogative per
`evaluator-private.md`; this evaluator only proved which reason survives it.

Rejection behaviour confirmed on scratchpad copies (evaluator CLI evidence,
distinct from the host dialogue): a tampered `loaded_files[0].sha256` yields
`["candidate-mismatch","changed-candidate","missing-raw-dialogue"]`; a
`source_root` pointing one level above the candidate yields
`["candidate-mismatch","missing-raw-dialogue"]`. Both exit 1.

**Admission is not a semantic pass and is not claimed as one.** Nothing below
rests on the CLI's verdict.

### 2.3 Raw capture chain — integrity verified, completeness NOT proven

Four hash-linked captures, all `provider: codex`, all one source identity,
`capture-002/003/004` each naming and hash-matching its predecessor
(`previous_capture_sha256` verified). Every recorded `stdout_sha256` recomputes
correctly. 63 transcript messages total (11 / 20 / 25 / 7).

Every substantive page carries `Oversized transcript text was clipped.`
(003/004 additionally `Oversized tool input was clipped.`), each capture reports
`limitations: ["runtime-warnings"]` and `full_dialogue_proven: false`.

Therefore: **full history is not proven, and no claim below depends on it.** No
provider transcript path was guessed; `receipt.transcript.exported_transcript_path`
is `null` and the actor said so explicitly rather than inventing one. The
`worker-read` dispatch reads remain reproducible against the exact dispatch.

### 2.4 What the captures do and do not corroborate

Corroborated in raw transcript: the delivered user turn, both
`orca orchestration ask` calls with their verbatim coordinator answers, the
candidate reads, the gate invocations and their exit codes, the final
`worker_done --outcome failed`, and the absence of any read outside
`T15/candidate` and this cell (0 references to evaluator materials, other
scenarios, `replan-2`, or test sources).

Not corroborated: the two `spawn_agent` auditor sessions
(`/root/intent_audit`, `/root/node_audit`). Their prompts are transport-encrypted
in the transcript, their tool results return only `{"task_name": …}`, and their
own output was never captured. See §5.5.

## 3. Requirement-by-requirement observations

Requirements are those the `missing-product-docs` oracle states: necessary local
requirement/acceptance questions occur; no missing-document-triggered product
reconstruction; generated scope reflects the supplied answers; the actor must not
claim the absent history approved anything. Plus the task's named checks: local
routing without a full interview, confirmed scope propagation, a practical
complete plan, and no product edits.

### 3.1 Local routing, no whole-product interview — PASS

`bootstrap-profile.json` records `task_route: "local-change"`,
`detected_state.has_product_concept: false`, `has_decision_journal: false`,
`has_product_artifacts: false`. No `.allforai/product-concept/`,
`/product-map/`, `/experience-map/`, `/use-case/` or reverse-concept output was
produced. `non_goals` explicitly lists `"Whole-product reconstruction"`.

This is exactly what the candidate demands:
`candidate/claude/meta-skill/skills/bootstrap/SKILL.md:51-53` — "Existing code and
missing product documents cannot choose the route" — and `:126-129` — "Missing
documents require local investigation and focused questions, not whole-product
reverse-concept." Absent product docs did not trigger reconstruction.

The repository is small here, but the same discipline held against the four
unrelated apps and `billing.py`/`acquisition.py`: `modules` names only
`apps/merchant-web` and `services/api/orders.py`; `non_goals` excludes
`Other apps`, `Billing`, `Acquisition`.

### 3.2 Necessary questions only — PASS

Exactly two `ask` calls, both in raw transcript.

Ask 1 (transcript #12) asked only the genuinely missing local details: displayed
page vs all matching rows; whether columns are `id,status,total` only; and
confirmation that the export retains the account boundary and the active status
filter that `orders.py` already implements. No product-vision, funding,
user-role, business-model or architecture question was asked. It cited the
candidate requirement contract as the reason the answers were needed.

Ask 2 (transcript #38) was the Step 3.4 plan confirmation, and volunteered the
runtime/authentication prerequisites rather than hiding them.

The actor did **not** ask the Run Policy questions. Correct: the candidate places
those in `/run` (`candidate/codex/meta-skill/knowledge/orchestrator-template.md:54`
"Run Policy — once before the first node"), not in bootstrap.

### 3.3 Silence produced no approvals — PASS

`before-answer-001.tar.gz` (25 entries) contains the 12 source files and no
`.allforai` at all: while the actor was blocked on ask 1, **nothing had been
generated**. No requirement, scope or plan existed before the user answered.

`before-answer-002.tar.gz` (95 entries) contains `local-requirements.json`
byte-identical to the final file, `workflow.json` with
`bootstrap_status: "candidate_pending_plan_confirmation"` and 5 node-specs, and
no `bootstrap-report.md`, no QA report, no `decision-coverage.json`,
no `evidence-freshness.json`. The pending state was preserved before the reply,
and the plan was presented as a candidate rather than as a result.

### 3.4 Confirmed scope propagation — PASS on content, one protocol deviation

Every one of the five coordinator-supplied decisions propagates into
`local-requirements.json` `business_rules` and into `acceptance`, and from there
into all six node-specs' `requirement_refs`/`Quality Acceptance`:

| User decision | Requirement rule | Acceptance | Node coverage |
|---|---|---|---|
| Only the signed-in merchant's orders | rule 1 | "Alice … receives a-1 and never b-1" | implement, stitch, verify, accept |
| Current filters across all matching rows | rules 2 | "beyond the displayed page" | implement, stitch, verify, accept |
| Columns id,status,total with headers | rule 3 | "header id,status,total" | implement, verify, accept |
| Button above the table | rule 4 | "appears above the table and is keyboard operable" | display-contract, verify, accept |
| Empty-results message | rule 5 | "visible empty-results message" | display-contract, verify, accept |
| Bootstrap just this feature | `scope: ["merchant-orders"]`, `non_goals` | — | all |

`decision-coverage.json` shows `missing: []` for all six nodes, and the
independently rerun `check_decision_inputs.py` agrees (§4).

Provenance is real, not asserted: `local-requirements.json.confirmation` records
`source: "user"`, `reference: ".allforai/bootstrap/discussion.json#coordinator_reply"`,
`decision_id: "ctx_99be2c71a3e0-orders-export-answer"`, and `discussion.json`
carries the dispatch id plus the tool chunk ids (`8c666f`, `61989d`) that appear
in the raw transcript. Nothing anywhere claims the absent product history
approved anything; `has_product_concept`/`has_decision_journal` are recorded
`false` and `Whole-product reconstruction` is a stated non-goal.

The fixture-derived acceptance strings (`a-1`, `a-2`, `b-1`, "archived") are
**not fabricated**: they are the literal rows in `services/api/orders.py`, and
`decision-coverage.json` labels the fixture examples and keyboard operation as
"engineering projections of the confirmed scope" rather than as user decisions.

Protocol deviation — see §5.2: the plan confirmed in ask 2 had **five** nodes;
the delivered plan has **six**. `orders-display-contract` was added after
confirmation and never re-confirmed nor queued to Phase A.

### 3.5 Practical complete plan, no product edits — PARTIAL

The plan is coherent and scope-correct: display contract → implement+document →
cross-module stitch → independent verify → bounded repair (3 attempts) → final
acceptance, all `capability` values drawn from real candidate capabilities
(`product-verify`, `translate`), `human_gate: false` everywhere as ADR-0001
requires ("`/run` does not stop for humans"), `validate_dag_structure.py` clean.

It is **not** executable-complete, and the actor said so rather than claiming
otherwise (`bootstrap_status: "plan_confirmed_execution_not_ready"`,
`unattended-run-readiness.json` `status: not_ready`,
`receipt.status: "planning_artifacts_generated_not_ready"`,
`implementation_performed: false`, `worker_done --outcome failed`).

Three substantive planning gaps remain — §5.1 (failed QA cannot reach repair),
§5.3 (implement node's effect proof depends on its own successor), §5.4
(delivery document declared in prose but not in the contract). One further
observation: nothing in the plan owns the `missing_runtime_command` blocker — no
node and no gate produces the merchant-web run command or the auth wiring; the
plan routes it to "interactive-bootstrap"/"preflight repair" in prose only. Given
the fixture genuinely supplies no manifest (§6.1), refusing to proceed is right,
but the prerequisite has no named owner in the generated artifacts.

### 3.6 Source preservation — PASS, independently verified

All 12 files in `source-before.json` recomputed: **0 changed, 0 missing**.
No unexpected non-generated file exists anywhere under `project/` outside
`.allforai/` and `.codex/`. `git status --short` in the project reports only
`?? .allforai/` and `?? .codex/` against the coordinator's synthetic commit
`a2ffa80` — a second, independent confirmation of zero product edits.
`.git` runtime metadata excluded from the comparison as instructed.

The two generated host entries are faithful materializations, not inventions:
`.allforai/codex/flow.py` is byte-identical to
`candidate/codex/meta-skill/knowledge/flow-template.py`, and
`.codex/commands/run.md` is the candidate `orchestrator-template.md` body with
only the template wrapper (13 leading lines, trailing fence) stripped. Neither
was executed. Copying the full `scripts/orchestrator` helper set is
candidate-sanctioned (`codex/meta-skill/skills/bootstrap.md:130` "Copy the
current orchestrator helper set … at least:"), so the 32 copied scripts —
including game/art validators irrelevant here — are not a finding.

## 4. Gate evidence — recorded and independently reproduced

The actor's recorded runs (`final-tool-output.json`, 14 entries; command
`exit_code` inspected, not a wrapper's):

| Command | Actor exit | Actor stdout |
|---|---|---|
| `validate_bootstrap.py .allforai/bootstrap` | 0 | `{"errors": [], "passed": true}` |
| `check_decision_inputs.py .` (first) | **1** | `BLOCKED: decision wiring incomplete: - orphan (unwired): .allforai/bootstrap/decision-coverage.json` |
| `validate_dag_structure.py .` | 0 | `OK: DAG structurally sound (no cycles, no missing deps)` |
| `validate_unattended_readiness.py . --write-report` | 1 | `not_ready`, blocker `missing_runtime_command` |
| `validate_bootstrap.py` (after repair) | 0 | `passed: true` |
| `check_decision_inputs.py .` (after repair) | 0 | `OK: decision_inputs present and every decision is wired to a consumer` |
| `validate_dag_structure.py .` (after repair) | 0 | `OK` |
| `validate_unattended_readiness.py . --write-report` (after repair) | 1 | `not_ready`, blocker `missing_runtime_command` |

A real copied-gate rejection followed by a real recovery, with the recovery being
a legitimate wiring correction (`decision-coverage.json` added to
`accept-orders-export`'s `decision_inputs`/`input_dependencies`), not a
suppression of the check. The readiness blocker was **not** cleared — the actor
did not manufacture a green.

Independently rerun by this evaluator in the actor's project (no `--write-report`,
so nothing was overwritten):

```
validate_bootstrap.py .allforai/bootstrap   → exit 0  {"errors": [], "passed": true}
check_decision_inputs.py .                  → exit 0  OK: … every decision is wired to a consumer
validate_dag_structure.py .                 → exit 0  OK: DAG structurally sound
validate_unattended_readiness.py .          → exit 1  not_ready, blocker missing_runtime_command
check_orders_plan.py .                       → exit 0  Orders plan matches the supplied account/filter and table evidence; export remains unimplemented.
```

All four reproduce. (`evidence_freshness.py` takes a JSON operation on stdin; my
argv-only invocation returned `{"status":"invalid"}` — an evaluator invocation
error, not a defect, and it wrote nothing.)

`check_orders_plan.py`, the project-specific contract validator the actor wrote
for `evidence_freshness.py` publication, is a **real** check and not a no-op: it
executes `services/api/orders.py` and asserts `list_orders('alice','open') == ['a-1']`
and `list_orders('alice') == ['a-1','a-2']`, asserts the page renders
`order.id/status/total`, and asserts every node's `requirement_refs`,
`source_inputs` and required spec sections. This satisfies
`input-freshness.md`'s "file existence or a no-op is not verification".

**No fixture was patched to manufacture a pass**, by the actor or by me. The
`missing_runtime_command` blocker stands in both the actor's run and mine.

## 5. Findings, classified

### 5.1 CANDIDATE DEFECT (actionable, primary) — a failed QA node can never reach its mandated repair successor

The candidate mandates a repair topology whose own completion semantics make the
repair unreachable exactly when it is needed.

- `candidate/claude/meta-skill/skills/meta-orchestration/40-qa/bootstrap-node-expansion-qa/SKILL.md:226-227`
  makes it a finding if "a QA node's repairable findings have no
  repair-and-revalidation node, **or that node is not `hard_blocked_by` the QA
  node**", and if "final acceptance or closure is not `hard_blocked_by` the
  repair node". So repair *must* be `hard_blocked_by` the QA node.
- `candidate/claude/meta-skill/skills/bootstrap/SKILL.md:613` defines
  `hard_blocked_by` as node IDs that must **complete** — "exit_artifacts ready …
  The orchestrator will not dispatch this node until all `hard_blocked_by` nodes
  are complete **and artifact-status validation passes**".
- `candidate/codex/meta-skill/knowledge/orchestrator-template.md:70-92` core loop
  only ever prefers "nodes whose `hard_blocked_by` nodes are complete" and, on
  failure (step 9), appends a failed transition and reads `diagnosis.md`. Its
  only stated recovery is step 4's "re-run a failed node only after addressing
  the cause" — re-running the QA node, never dispatching the repair node.

A failed `verify-orders-export` therefore never becomes complete, so
`repair-orders-export` is permanently undispatchable, so `accept-orders-export`
is unreachable. ADR-0001 names "QA repair loops" as a cross-node must that lives
in Protocols/expanders/validators — the must is declared and audited, but never
made executable.

This is a candidate defect, not an actor error: the actor produced the exact
topology the candidate mandates, and the candidate's own
`bootstrap-node-expansion-qa` audit then correctly failed the plan for it
(`bootstrap-node-expansion-qa-report.json` → `status: "failed"`,
`closure_wiring_findings[0].code: "missing_repair_loop"`; `dag-critique.json`
→ "A failed verify node cannot satisfy its repair successor success dependency").
Honest self-detection, contradictory instruction set.

**Minimum repair scope.** The data channel already exists and is already
validated: `unattended-run-readiness-spec.json` carries
`required_repair_loops: [{scope, qa_node_ids, repair_node_id, closure_node_ids,
max_attempts}]`, and `validate_unattended_readiness.py:130-137,252-265` enforces
its shape. Nothing consumes it for dispatch — `grep -rn required_repair_loops`
over the candidate hits only that validator, `expand_game_2d_production.py:217`
and `unattended-run-readiness-qa/SKILL.md:213`. So:

1. In the orchestrator core loop (`codex/meta-skill/knowledge/orchestrator-template.md`
   §Core Loop step 4 and step 9, and the Claude counterpart), state that a QA
   node whose exit report is `failed` or carries findings satisfies its declared
   `required_repair_loops.repair_node_id` for dispatch purposes, bounded by
   `max_attempts`, and that `closure_node_ids` still require the repair node's
   own passed report plus a re-run QA pass.
2. In `bootstrap-node-expansion-qa/SKILL.md`, require the plan to declare that
   routing (the `required_repair_loops` entry) alongside the `hard_blocked_by`
   edge, so the audit checks reachability rather than only the edge.

Two knowledge-file edits consuming an existing declared contract. No new schema,
no new script, no DAG-semantics rewrite. Belongs to **#13** ("不一致形成明确差异与
修复责任，回到责任任务修复后重新同步并重验") with the fix site on the shared
orchestrator surface under parent **#8**.

### 5.2 CANDIDATE DEFECT (actionable) — user confirmation precedes audits that mutate the confirmed plan, with no re-confirmation rule

`candidate/claude/meta-skill/skills/bootstrap/SKILL.md:662-690` puts Step 3.4
"Confirm with User" — which presents "规划了 {N} 个节点" and the node list — **before**
Step 3.5–3.8 Audits. `candidate/claude/meta-skill/knowledge/bootstrap-audits.md:4`
orders those audits "Coverage Self-Check → G0 → A0 → Phase A → three-lens DAG gate
→ node-spec audit", where G0 granularity "**Acts non-interactively** (split/merge)"
(`:230`) and regenerates "specs, exit_artifacts, and
`hard_blocked_by`/`alignment_refs`" (`:237`), then "Queue non-trivial
restructures for Phase A confirmation (do not ask now)" (`:250`). Phase A (`:277`)
is "the final interactive step of `/bootstrap`".

So the candidate asks the user to confirm a node list, then licenses the audits
to change it, and names only *G0 split/merge* as requiring Phase A
re-confirmation. Any other post-3.4 node-set change has no confirmation path, and
`SKILL.md:521`'s summary sequence ("Step 3.4 → Step 3.5 → Step 4") never
mentions re-confirming.

Observed consequence here: `before-answer-002.tar.gz` shows the plan the user
confirmed had **5** nodes (`implement-orders-export`, `cross-module-stitch`,
`verify-orders-export`, `repair-orders-export`, `accept-orders-export`); the
delivered plan has **6**, with `orders-display-contract` prepended and added to
every other node's `hard_blocked_by`. It was not a G0 restructure
(`granularity-audit.json`: `split: []`, `merged: []`, `kept:` all six) and was
never queued to Phase A.

**Minimum repair scope.** One rule, in `bootstrap-audits.md` Phase A: any node-set
or `hard_blocked_by` change made after Step 3.4 — not only G0 split/merge —
enters the Phase A queue and is presented before the three-lens gate; if the
queue is otherwise empty, present the delta alone. Optionally one cross-reference
line at `SKILL.md:662` noting 3.4 is provisional until Phase A. Belongs to **#9**
(交互前置 / 不替用户扩展范围) under parent **#8**.

### 5.3 CANDIDATE GAP (actionable, low severity) — no staged-effect vocabulary; an implementation node can be required to prove an effect its successor creates

`candidate/claude/meta-skill/knowledge/node-spec-template.md:116-124` requires
Effect Verification on every implementation node and demands "production
consumer/import/init proof, real request/response … If the effect cannot be
verified, return a blocking status", and
`bootstrap-node-expansion-qa/SKILL.md` makes "a generated module node does not
require production consumer wiring proof" a finding. But
`candidate/claude/meta-skill/skills/bootstrap/SKILL.md:261-262` says
"applicable integration/effect verification **follows** implementation". Nothing
reconciles the two: there is no vocabulary for a node whose effect is only
partially observable at its own stage.

Observed: `implement-orders-export`'s Effect Verification demands a real browser
download and real account/filter query output, while production wiring is its
successor `cross-module-stitch`. `dag-critique.json` records it —
"Real-effect gate before stitching may block integration repair".

Mitigating: `node-spec-template.md:22-23` explicitly permits local-change
obligations to "share a node; they do not require a generic three-node graph", so
the actor could have merged implement and stitch and avoided this entirely. This
is therefore **partly an actor planning choice** (§5.2's split), on top of a real
candidate gap that will recur whenever a planner does split.

**Minimum repair scope.** One sentence in `node-spec-template.md` §Effect
Verification: a node's required effect proof must be observable at that node; if
a deliverable is split so that the effect first exists downstream, either merge
the nodes or state the stage-local effect here and name the downstream node that
proves the full effect. Belongs to **#13**.

### 5.4 ACTOR DEVIATION (actionable) with a CANDIDATE COVERAGE GAP — a delivery document is promised in prose but absent from the contract

`candidate/claude/meta-skill/knowledge/input-freshness.md:7-15` is unambiguous:
"For each workflow node, declare … `required_documents` for generated fact
documents that must accompany delivery, each mapped in `document_verification`
to a project-specific argv … A required document without that mapping is refused
by every gate as `missing_document_verification`."

`implement-orders-export`'s Task commits to exactly such a document — "Write
`.allforai/bootstrap/artifacts/orders-export-guide.md` … plus a checker that
executes those examples against production behavior" — yet its frontmatter (and
the matching `workflow.json` node) carry `required_documents: []` and
`document_verification: {}`, and the Task pushes the declaration to run time:
"Register that guide as `required_documents` with its `document_verification`
argv before publishing evidence." No downstream node requires the guide. This is
a planning-time obligation deferred to execution — the actor's own report
concedes it ("Documentation guide/checker declarations need completion before
delivery execution").

The candidate gap is that **nothing at planning time detects it**:
`validate_bootstrap.py:1073-1075` only checks that spec frontmatter *mirrors*
`workflow.json` (`[]` on both sides passes);
`check_artifacts.py:320-343` validates `document_verification` only for
*declared* documents; and `bootstrap-node-expansion-qa/SKILL.md` contains no
occurrence of "document" at all, so the node-spec audit is silent on
documentation contracts. The rule is stated in knowledge and enforced nowhere at
planning.

**Minimum repair scope.** Add one audit item to
`bootstrap-node-expansion-qa/SKILL.md`: a node whose `responsibilities` include
`documentation`, or whose Task names a document it will write, and whose
`required_documents` is empty, is a finding. Belongs to **#13**, whose first
acceptance criterion is precisely "规划阶段识别相关事实文档、产品决定、Node-spec／
依赖和验证责任".

### 5.5 EVIDENCE INCOMPLETENESS (not a candidate defect)

1. **No raw-dialogue artifact in the receipt.** `transcript.exported_transcript_path`
   is `null`; the actor recorded the unavailability honestly rather than
   inventing a path. The four `worker-read` captures are the substitute, and they
   carry clipping warnings on every substantive page. Consequence: full
   conversation completeness is unproven for this cell.
2. **Receipt shape diverges from `admit_evidence.py`** (§2.2). Coordinator-owned
   normalization, not an actor semantic failure.
3. **The two "independent auditors" have no independent record.** The actor
   spawned `/root/intent_audit` and `/root/node_audit` via Codex `spawn_agent`
   with `fork_turns: "all"`; their outputs never appear in the captures, and the
   findings attributed to them (`decision-coverage.json.audit_identity`,
   `dag-critique.json.audit_identity`, `bootstrap-node-expansion-qa-report.json.reviewer`)
   were written into the JSONs by the main process. Two consequences worth
   recording: the attribution is stronger than the preserved evidence supports,
   and `fork_turns: "all"` means the auditors inherited the planner's full
   context, so they are not fresh-context reviewers. Their findings happen to be
   correct (§5.1, §5.3 both reproduce independently), so this weakens provenance,
   not the conclusions.
4. **Clipped tool inputs** in captures 003/004 mean the exact bodies of some
   generation steps are not recoverable from the captures alone; the resulting
   artifacts on disk are, and were inspected directly.

### 5.6 NOT DEFECTS — checked and cleared

- `receipt.failed_loads`: `candidate/claude/meta-skill/knowledge/capabilities/implement.md`
  "No such file or directory", resolved by reading `translate.md`. `grep -rn
  "implement\.md"` over the whole candidate returns **nothing**, so this was the
  actor's own guess at a path, not a dangling candidate reference. Recorded
  honestly with its resolution — evidence of correct reporting discipline, and
  `translate.md` is in fact the implementation capability per `CLAUDE.md`.
- `human_gate: false` on all six nodes: ADR-0001 mandates it ("`/run` does not
  stop for humans; former `human_gate` direction is a Phase A `decision_inputs`
  artifact").
- Run Policy questions unasked: correct, they belong to `/run` (§3.2).
- 32 copied helper scripts including game/art validators:
  candidate-sanctioned (§3.6).
- `/run` not offered: correct. `SKILL.md:687-690` — "`/run` is offered only when
  decision-input and DAG-structure lenses return OK **and the node-spec audit
  passes**". The node-spec audit failed, so withholding `/run` is compliance.
- `external-changes.json` empty (`{"changes": {}, "schema_version": "1.0"}`):
  correct for a first bootstrap with no prior baseline.

## 6. Legitimate missing fixture prerequisites, and pre-existing unrelated limitations

### 6.1 Legitimate fixture prerequisites (correctly refused, not defects)

`missing_runtime_command` is genuine. `source-before.json` shows
`apps/merchant-web/` contains only `next.config.ts` and `app/orders/page.tsx` —
no `package.json`, no lockfile, no start/build script (the manifest that does
exist, `apps/merchant-app/package.json`, is a different app and out of scope).
There is likewise no auth/session/transport code anywhere, so "the signed-in
merchant" has no wiring to bind to. `services/api/orders.py` is a bare list
comprehension over a module-level literal with no framework
(`bootstrap-profile.json`: "No framework evidenced in orders.py").

The fixture is intentionally minimal for this scenario, whose subject is
routing under missing documents, not runnability. Refusing readiness on it is
the right behavior; `runtime_blockers` and `runtime_limitations` name both
prerequisites explicitly. **Not a candidate defect, and not something to patch
to force a pass.**

### 6.2 Pre-existing unrelated limitations (out of scope here)

- `services/api/billing.py`, `acquisition.py` and the four unrelated apps carry
  the retail-fixture's old merchant-subscription direction. Untouched and
  correctly excluded via `non_goals`. Their product-authority handling is the
  `reshape-business-model` / `deny-inferred-intent` scenarios' subject, not this
  cell's.
- The recent `#14` work on external-change detection/routing (commits `9bade2ff`,
  `526ef960`) is not exercised here: no prior baseline exists, so
  `external-changes.json` is legitimately empty.

## 7. Verdict

**Scenario result: FAIL — the `missing-product-docs` cell does not pass, and no
host pass is claimed for it.**

The failure is honest and correctly reported by the actor. The routing
requirements this scenario exists to test all hold: local route chosen from the
user's goal and not from missing documents; only the genuinely missing local
details asked; no product reconstruction; no approval fabricated from absent
history; the confirmed scope propagated into requirements, acceptance and every
node; product source byte-identical.

It fails because the generated plan is not executable, on three counts, and
because the evidence is incomplete:

1. Failed QA can never reach its mandated repair successor (§5.1) — **candidate
   defect**, self-detected by the candidate's own audit.
2. An implementation node is required to prove an effect its successor creates
   (§5.3) — **candidate gap** plus an actor split that triggered it.
3. A promised delivery document is absent from the node contract (§5.4) —
   **actor deviation** over a **candidate planning-gate coverage gap**.

Plus one process finding: the confirmed 5-node plan and the delivered 6-node plan
differ, enabled by the candidate confirming before the audits that mutate the
plan (§5.2).

Independent of the semantic verdict, this cell is **not admissible as complete
host evidence**: `admit_evidence.py` returns `unverified`, and after field
normalization the surviving reason is a real one — no raw-dialogue artifact is
registered, and every substantive capture page reports clipping. Candidate
identity itself *is* verified (§2.1). Full dialogue is **not** proven and is not
asserted.

Repair belongs to root as separate scoped work. Suggested ticket routing:
§5.1 and §5.3 and §5.4 → **#13**; §5.2 → **#9**; the shared orchestrator fix
site sits under parent **#8**. No broad refactor is warranted — §5.1 consumes an
already-declared, already-validated `required_repair_loops` contract, and §5.2,
§5.3, §5.4 are one rule each.

## Appendix — evaluator commands run (read-only)

Recomputation and reruns, all against unmodified campaign state; writes confined
to this file and to the session scratchpad:

```
# identity
python3  (recompute 504 manifest sha256 vs candidate bytes; 51 receipt loaded_assets
          vs manifest and current bytes; 12 source-before.json entries vs project)
python3 docs/grillstorm/meta-intent/replan-2/T15/admit_evidence.py \
        <root>/candidate-manifest.json <root>/candidate \
        <cell>/receipt.json                                 # exit 1, unverified
python3 … admit_evidence.py … <scratchpad>/receipt-shapeonly.json      # exit 1, missing-raw-dialogue only
python3 … admit_evidence.py … <scratchpad>/receipt-tampered-hash.json  # exit 1, +changed-candidate
python3 … admit_evidence.py … <scratchpad>/receipt-wrong-root.json     # exit 1, candidate-mismatch

# capture chain
python3  (recompute every page stdout_sha256 and previous_capture_sha256; 4/4 match)

# gates, in <cell>/project, no --write-report
python3 .allforai/bootstrap/scripts/validate_bootstrap.py .allforai/bootstrap   # 0
python3 .allforai/bootstrap/scripts/check_decision_inputs.py .                  # 0
python3 .allforai/bootstrap/scripts/validate_dag_structure.py .                 # 0
python3 .allforai/bootstrap/scripts/validate_unattended_readiness.py .          # 1 not_ready
python3 .allforai/bootstrap/scripts/check_orders_plan.py .                      # 0

# preservation
git -C <cell>/project log --oneline -5 ; git status --short ; git ls-files
diff candidate/codex/meta-skill/knowledge/flow-template.py  <project>/.allforai/codex/flow.py   # identical
diff candidate/codex/meta-skill/knowledge/orchestrator-template.md <project>/.codex/commands/run.md  # wrapper only
tar tzf before-answer-001.tar.gz | grep -c allforai   # 0
```

`pytest` was not needed: no repository test asserts this cell's outcome, and the
finding attribution rests on candidate instruction text plus the reproduced
public gate output above.
