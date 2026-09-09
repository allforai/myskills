# Real-host campaign — e30ccc7c

Candidate: `e30ccc7cec9120815f0d9bc92204adf465f666d4`, including main `4e34c684`.
The normal merge-commit hook passed 647 unit tests and all validators. Main is
unchanged; integration branch owns this candidate.

Fresh packet roots: `/private/tmp/meta-intent-host-campaign.XX6yRo/T15` through
`T18`. All four manifests bind the same production tree fingerprint:
`c1114a94d89c2ea8d8e7bc8c496576b9750957e347769980dc75dee006704fc4`.
60 primary cells are required. No semantic pass has been admitted yet.

## Current host observations

Claude missing-product-docs: `task_0183f16263ac` / `ctx_711325d4829c` failed at
dispatch input with `agent_prompt_stalled`. Terminal evidence shows the workspace
trust check, followed by the shell prompt. The scenario input was not accepted.
Capture under that cell's `capture-001` is terminal evidence only. The failed
worker was released and its output archived. User was asked to manually open and
trust `/private/tmp/meta-intent-host-campaign.XX6yRo/T15/claude/missing-product-docs/project`.
No trust setting was changed by the coordinator.

Codex accepted three fresh real-host sessions. The prior quota report does not
describe these successful launches:

| Cell | Task | Dispatch |
|---|---|---|
| missing-product-docs | task_e7b6a9f84198 | ctx_99be2c71a3e0 |
| large-code-local-button | task_1f6124b04caa | ctx_d19bc67f4ff4 |
| new-product | task_04209e89dedd | ctx_0cc4dd1dd6c8 |

Each project was initialized as a synthetic Git repository solely for Orca
placement. Product source was not altered by that initialization; `.git` metadata
is excluded from source-preservation comparisons. Full generated actor-input.md
was supplied as the Task spec, with no evaluator oracle or expected result.

## Recorded interaction checkpoints

Every answered question below has a project archive taken before the reply in
the cell directory (`before-answer-001.tar.gz`, and `002` where applicable).

- Missing docs: `msg_6cae4306360a` asked local export scope. Reply
  `msg_bae8d6070e96` is the oracle's missing-docs answer verbatim.
- Missing docs: `msg_85d5d9a2541f` requested plan confirmation. Coordinator read
  workflow.json: all five nodes bind only `order-export` revision 1. Reply
  `msg_1d547f13875a` is an evaluator-authored scoped plan confirmation, not a
  verbatim prewritten line; it preserves the already supplied requirements,
  explicit runtime/authentication prerequisites and the no-implementation boundary.
- Large code: `msg_afadf924f375` reported that resume treated the historical
  export requirement as pending because journal goal/reason did not match.
  Reply `msg_42a0a767bb18` is the oracle's local-button answer verbatim. Evaluate
  whether this re-questioning is legitimate provenance handling or an unwanted
  repeat; do not assume it passes merely because a reply was supplied.
- New product: `msg_0ec2b7e33229` asked primary users. Reply
  `msg_c1d16a28306d` supplies the oracle's coordinator/volunteer, problem/value
  choices only, without approving an unseen full scope.
- New product: `msg_c867b042c633` proposed a lifecycle and privacy choice. Reply
  `msg_2748377d7472` supplies oracle group verification, volunteer claim,
  requester-confirmed fulfillment, concurrency, free/grant-funded service,
  privacy priority and exclusions. It corrects coordinator-confirmed fulfillment
  rather than approving that proposal unchanged.

## Evidence limitations and remaining work

Early capture uses the existing capture_worker.py with exact Dispatch IDs and
returned cursors. Codex captures are hook-attested transcripts but report oversized
text clipping. Do not claim full raw-history admission until chronology and the
clipped content are corroborated; preserve the original raw pages. Initial capture
directories for all three actors exist; missing-docs also has captures 002 and 003.
Continue from the latest capture.json for each actor, not an invented cursor.

The refreshed ledgers and launch lists initially failed their own checks: omitted
new prompt paths, incompatible blocker formats, a noncanonical final-status value,
and a T18 assertion that repair must remain open forever. Paths/formats/status
were corrected. T18 now retains refusal of the old reference but permits an
accepted new candidate only with a different commit/root and a recomputed export
fingerprint matching its actual launch manifest. No production asset or actor
candidate was changed. Results-pin tests now pass: T15 3, T16 9, T17 12, T18 13.
The unchanged other helper tests passed in the preceding runs; no host pass is
inferred from these material checks.

Next: supervise these actors, preserve later questions and captures, independently
evaluate completed artifacts and generated public gates, then continue the matrix.
Claude remains dependent on manual workspace trust. Do not merge to main or remove
task worktrees while the required real-host proof is incomplete.

## First completed actor — not passed

Missing-docs Codex reported `worker_done` outcome failed in `msg_49d140cce244`.
It generated scoped artifacts but reports QA-to-repair reachability, integration
ordering and documentation-contract gaps, in addition to missing runtime/auth
prerequisites. Final capture is `capture-004`; actor was released. No scenario pass
is recorded. Independent read-only evaluation is now dispatched as
`task_983608c3a4c5` / `ctx_7499e12c795d` (Opus in the integration checkout), report
target `T15-codex-missing-docs-evaluation.md`. It must distinguish candidate defects,
actor deviations, fixture prerequisites and incomplete evidence before repair.

New-product question `msg_8688deadb4e5` summarized matching scope; after snapshot
003, reply `msg_cc47a503d266` explicitly approved that scope using the oracle's
release-scope reply. Large-code and new-product actors remain active.

Large-code plan question `msg_b806cbeb3ea5` was checked against the actual
three-node graph, all bound to export revision 2; snapshot 002 precedes
`msg_a1e3edf1c79b`, an evaluator-authored confirmation limited to prior export
choices and planning only. New-product question `msg_ba787de5e172` introduced
additional unresolved execution choices; snapshot 004 precedes evaluator reply
`msg_2a4bcbdbfe69`. That reply approves only previously settled planning scope,
explicitly leaves new choices undecided, and requires dependent work to remain
blocked. This pending-choice branch must be considered in the semantic evaluation;
it is not evidence that a fully executable product plan was completed.

New-product actor completed in `msg_2b2f70e96861`, outcome succeeded for its
planning deliverable, not an admitted scenario pass. Its report explicitly leaves
independent A0/reverse audits unperformed and expansion audit failed. Final capture
003 was taken and the actor released. Independent evaluation is
`task_42cbe217b0d2` / `ctx_e7b30781011f`, report target
`T15-codex-new-product-evaluation.md`. It must separate permitted pending product
choices from unperformed required planning audits.

Large-code question `msg_373675a05658` proposed splitting verify/repair/acceptance;
snapshot 003 precedes reply `msg_61672aa5833a`, which confirms that internal
granularity change without adding product decisions or implementation authority.

Large-code primary actor completed in `msg_5383962153be`, outcome succeeded for
planning. Root independently ran copied `check_decision_inputs.py .` (exit 0) and
`validate_bootstrap.py .allforai/bootstrap` (passed true) and archived the project
as `before-bom-contrast.tar.gz`. Capture 003 preserves the primary actor end.
The same exact agent terminal was immediately reused, without reset, for the
oracle's BOM contrast: `task_eb55ae29c116` / `ctx_2492b68bb8e4`. The Task spec is
only the prescribed user turn: record UTF-8 BOM choice before changing the plan,
then pause. After it settles, snapshot and run the actual decision-input gate
before supplying the oracle's plan-update follow-up. If it already wires the
decision despite the pause, record that and leave the contrast incomplete rather
than manufacturing an unwired state. Primary completion is not scenario admission.

BOM recording completed (`msg_7e913c050280`): confirmed export revision 3 with
the old revision 2 plan unchanged. Root archived `after-bom-before-plan.tar.gz`
and ran the real copied decision-input gate: exit 1, five `stale_requirement`
errors for implement/stitch/verify/repair/accept-export, each stating the reference
does not select the current revision. Capture `capture-bom-001` preserves this
phase. The same actor was reused again for the oracle's update-plan reply,
Task `task_591de0cf0ae7`; verify recovery after it settles. This is observed gate
rejection over a real host-recorded user decision, not a synthetic fixture edit.

## Evaluation and recovery checkpoint (2026-09-09)

BOM plan recovery completed in `msg_47cd17008d66` on
`task_591de0cf0ae7` / `ctx_ecaa06f0f8de`. Root reran the copied
decision-input check (exit 0) and bootstrap validator (`passed: true`, exit 0).
`capture-bom-recovery-001` preserves two pages; capture returned exit 1 and does
not establish complete dialogue. The worker was released. This proves the
observed stale-revision rejection followed by plan-check recovery, not a full
scenario pass. Independent large-code evaluation now runs as
`task_34242318605e` / `ctx_6d4a39e2cef8` against the frozen export.

Missing-docs evaluation completed in `msg_6a6166609eff`; report
`T15-codex-missing-docs-evaluation.md` rejects a scenario pass. It verifies local
routing, confirmed scope and unchanged product source, but finds unreachable
QA-to-repair scheduling, post-confirmation graph changes, premature effect proof,
and an undeclared delivery-document contract. Evaluator released. A sole
production editor, `task_74fd254b5586` / `ctx_309907d34e02` (Opus), is repairing
these four issues across the actual Claude/Codex consumed paths. Frozen campaign
bytes and actor artifacts must not be patched; repaired candidates need reruns.

New-product evaluation completed in `msg_e387ae227339`; report
`T15-codex-new-product-evaluation.md` also rejects a pass. Intent provenance,
requester-controlled fulfillment and source preservation hold. Incorrect
capability routing, unscoped acceptance, unsupported attribution of skipped
audits, and weak pending-choice blocking remain. Evaluator released. Filename
discovery and pending-choice gate findings require independent executable
diagnosis before selecting fixes; unresolved user choices must stay unresolved.

No real-host pass is admitted. Main merge and task-worktree removal remain pending.

Root preserved the settled BOM recovery project (excluding `.git`) as
`after-bom-plan-recovery.tar.gz` in the large-code cell, SHA-256
`d8c3d7cc1570fdf817e77d38f81cc7f50dfdbff43f9d291642598220fb4a9111`.
This completes the before-choice / choice-before-plan / updated-plan snapshot
sequence without modifying any actor output. Separate read-only decision-gate
diagnosis is `task_35899218b5f8` / `ctx_43414f5c2d4d`.

After the evaluation-ledger updates, root reran all four preparation/helper
suites separately: T15 20 passed (63.84s), T16 22 passed (34.15s), T17 31 passed
(45.08s), T18 31 passed (60.32s), 104 total. The initial combined pytest
invocation failed collection with six same-basename module import conflicts;
separate invocations resolved that runner issue without edits or deletions.
These checks cover packet preparation and evidence bookkeeping, not host
behavior or the production repairs now in progress.

## Large-code evaluation disposition and admission repair

`msg_22136658223a` completes independent large-code evaluation at
`T15-codex-large-code-evaluation.md`; evaluator released. Root accepts its
independent BOM stale-state rejection/recovery and source/history preservation
observations, but not its broad executable-plan PASS: structural checks do not
close the shared failed-QA-to-repair dispatch defect identified by the other
evaluation. No scenario pass is admitted. The suggestion to remove internal
graph confirmation also conflicts with the current confirmation repair and is
not automatically adopted. The legacy question payload finding is retained
for scoped investigation, not permission to infer unconfirmed fields.

The evaluator found an extra Python cache inside the frozen candidate export.
Root preserved it and added a public admission-CLI regression for extra cache,
hidden file and broken symlink. All three cases incorrectly returned admissible
before the fix. The admission CLI now rejects unmanifested files/links; all 11
admission tests pass (0.46s). Running it read-only with `python3 -B` against the
actual export now returns `candidate-extra-files`, naming exactly
`claude/meta-skill/scripts/orchestrator/__pycache__/product_intent.cpython-314.pyc`.
Original receipt shape and missing dialogue reasons remain; none was suppressed.
No frozen candidate bytes were repaired and no transcript completeness claimed.

Planning repair worker completed in `msg_cba1514f6652` and was released.
`T15-planning-repair-report.md` records real dispatch changes in both hosts,
the three planning-contract corrections, 70 engine tests, 647 Claude unit
tests and 43 Codex flow/install tests reported passing. Root staged only those
14 repair/report files for a local checkpoint; the normal pre-commit hook is
running, without skipped checks. This is not independent repair acceptance or
host proof. Root's admission repair and campaign/evaluation records remain
separate unstaged changes. Decision-gate diagnosis remains active.

The checkpoint committed as `2cc347afc4cfdbfac8c628eb0f652b02ac476e81`;
normal hook passed 647 tests in 245.71s and all listed validators, exit 0.
Two independent fixed-commit reviews now compare `e30ccc7c...2cc347af`:
Standards `task_3bdf037018d3` / `ctx_6107695fe04f`, Spec
`task_d8815e981c3d` / `ctx_9be1e31f0467`. They must inspect committed bytes,
not source that the next editor may change.

Decision-gate diagnosis completed in `msg_bc864576689f`, evaluator released.
`T15-decision-gate-diagnosis.md` confirms C1 false orphan detection and C2 an
actual pending-decision preflight escape. The earlier claim that the candidate
generated acceptance boilerplate is withdrawn: that string was actor input.
However, per-node acceptance duplication has a candidate-enforced cause and
requires a separate scoped design correction; do not simply loosen global
acceptance or stage coverage to pass this fixture. The prototype's full unit
result is **645 passed / 2 no-git errors at both baseline and prototype**, not
647 green. Current repair must verify in a real Git checkout.

C1/C2 repair is `task_3b4fa906aeab` / `ctx_18ef736a8d9b`, sole production
editor. Scope explicitly includes partial/empty/malformed decision negatives,
true orphan refusal, unrelated audit/journal positives and real copied public
gate recovery. C3 acceptance design and legacy-question precision remain
unresolved; neither is silently treated as complete. No new host pass admitted.

Standards review completed in `msg_663aed0cb492`, reviewer released. Its own
axis reports three hard findings and three heuristic smells in
`T15-2cc347af-standards-review.md`: mixed-wave terminal Run Policy signals can
be swallowed, per-QA repair budgets differ between hosts, and the templates
overstate readiness budget validation. Root withholds acceptance of 2cc347af;
Spec review remains separate and active. Corrections dispatched as
`task_270a7b095e26` / `ctx_b8ffbd5b1934`, owning the runtime loop files and
budget validation, not the three decision-gate files owned by the other editor.
No concurrent commits are allowed during these edits. Acceptance allocation
analysis is preserved separately in `T15-acceptance-allocation-analysis.md` and
is explicitly not an applied repair or a host pass.

Spec review completed in `msg_c4feab7645d3`, reviewer released. Its separate
axis reports six findings in `T15-2cc347af-spec-review.md`: reset budgets on
Claude resume, stale/non-QA Codex report admission, prose-only audit checks,
missing persisted graph-confirmation baseline, skipped mixed-wave terminal
signals, and missing regression coverage. Runtime findings 1/2/5/6 have been
forwarded to `ctx_b8ffbd5b1934`. Planning findings 3/4 are assigned to
`task_5f7a5ae305b8` / `ctx_a377a4a12a25`, owning bootstrap planning entries,
audit contracts and bootstrap validation; cross-owner gate hooks require
coordination. Both review axes withhold acceptance, independently; the fixed
commit's green unit suites are not a completion claim.
