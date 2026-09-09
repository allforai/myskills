# Meta intent task catalog

## Mode And Status

Program; spec revision2 independently closed (three rounds). Task revision1 independently closed (two rounds); workflow revision2 pending closure and launch not yet frozen. Official #8 specification and #9–#18 published tickets are reused; no duplicate publication or parent mutation.

## Source Artifacts / Frozen Decisions

../program-spec.md, ../modules/*-spec.md, ../sources/issue-*.json, ../decisions.md and ../autonomous-decisions.md. R01–R30 preserve issue8 user-story numbering. T<number> equals GitHub issue number. New helper filenames below are task-local implementation choices inside the declared invariant owners, not new product scope.

## Module DAG

| Module | Task file | Dependency | State | Gate |
| --- | --- | --- | --- | --- |
| intent | intent.md | none | pending | focused #9–#11; unit/engine integration; #15/#16 |
| synchronization | synchronization.md | I-intent; I-resume for external decisions | pending | #12–#14; both-engine integration; #17/#18 |
| proof | proof.md | exact per-ticket native deps | pending | full required scenario/host denominator |

## Work units

| Task | GitHub | Depends on | Interface produced | Acceptance |
| --- | --- | --- | --- | --- |
| T9 | [#9](https://github.com/allforai/myskills/issues/9) | none | I-scope | `python3 -m pytest claude/meta-skill/tests/unit/test_bootstrap_scope.py -q` |
| T10 | [#10](https://github.com/allforai/myskills/issues/10) | T9 | I-intent | `python3 -m pytest claude/meta-skill/tests/unit/test_bootstrap_confirmation.py -q` |
| T11 | [#11](https://github.com/allforai/myskills/issues/11) | T10 | I-resume | `python3 -m pytest claude/meta-skill/tests/unit/test_bootstrap_resume.py -q` |
| T12 | [#12](https://github.com/allforai/myskills/issues/12) | T10 | I-freshness | `python3 -m pytest claude/meta-skill/tests/unit/test_bootstrap_freshness.py -q` |
| T13 | [#13](https://github.com/allforai/myskills/issues/13) | T12 | I-sync | `python3 -m pytest claude/meta-skill/tests/unit/test_bootstrap_synchronization.py -q` |
| T14 | [#14](https://github.com/allforai/myskills/issues/14) | T11, T13 | I-drift | `python3 -m pytest claude/meta-skill/tests/unit/test_bootstrap_external_drift.py -q` |
| T15 | [#15](https://github.com/allforai/myskills/issues/15) | T9, T10 | none | `python3 -m pytest claude/meta-skill/tests/scenarios/T15/test_evidence.py -q` |
| T16 | [#16](https://github.com/allforai/myskills/issues/16) | T11 | none | `python3 -m pytest claude/meta-skill/tests/scenarios/T16/test_evidence.py -q` |
| T17 | [#17](https://github.com/allforai/myskills/issues/17) | T12, T13 | none | `python3 -m pytest claude/meta-skill/tests/scenarios/T17/test_evidence.py -q` |
| T18 | [#18](https://github.com/allforai/myskills/issues/18) | T14 | none | `python3 -m pytest claude/meta-skill/tests/scenarios/T18/test_evidence.py -q` |

## Interface Delivery

I-scope T9 -> T10/T15; I-intent T10 -> T11/T12/T15; I-resume T11 -> T14/T16; I-freshness T12 -> T13/T17; I-sync T13 -> T14/T17; I-drift T14 -> T18. Meaning, failure, authority and compatibility are defined once in program-spec. Existing reset_closure is the shared hard-dependency traversal; no reset mutation is imported into prerequisite admission.

## Directory And Ownership Coverage

Canonical bootstrap/knowledge/journal/authority helpers: intent owns policy, synchronization owns freshness/sync integration. Canonical orchestrator/scripts and both run engines: policies stay in shared helpers; controller is serialized integration owner for touching task changes. Existing check_evidence/compute_completeness must not report stale work as currently verified. Codex journal wrappers and runtime/skill adapters consume canonical authority. Source and test paths are enumerated in each task. Proof scenario directories belong only to their T15–T18 evaluator; no evaluator writes production or control-plane state. Scenario subjects write only their unique fixture workspace. No marketplace/version/installer/visual architecture changes planned.

## Test-Seam Delivery

Highest seam remains bootstrap/resume inputs and outputs. Focused pytest files are created by the producing ticket; pytest exit5 on no collection is failure. Implementation tests call actual public helper/CLI/gate behavior and inspect fixtures, not private methods or prompt regex. Individual helper assertions supplement, never replace, real scripted host interactions. Thought acceptance reads actually captured evidence and asserts behavior/provenance/full required denominator; missing files/host/mismatch fails, never skip. Thought T15–T18 cannot depend on a new shared harness from another thought ticket.

## Ready Frontier

Workflow dispatch/admission is frozen in dispatch-contract.md and enforced by controller.py. All non-subject roles load hash-bound task/source/spec obligations. Only one evaluator may be live, with subject capacity reserved; this may defer a ready evaluator without adding task dependency edges. Pending subjects/completion reviews have priority over new builders/evaluators. Settled workers release slots before downstream supervision. The role dry-run covers T15/T16/T17 hold-and-wait prevention.

Only T9 after launch. After each confirmed serialized merge recompute ready set, no layer barriers. Informational frontier: T9 -> T10 -> {T11,T12,T15}; T13 follows T12, T16 follows T11, T14 follows T11+T13, T17 follows T12+T13, T18 follows T14. Only actual verified producer commits satisfy dependencies; GitHub issue numbers/edges are the topology, worker_done alone is not semantic completion. Tracker may remain open until delivery is published; do not change dependency edges or close issues to force readiness.

## Global Gates / Runtime Acceptance

scenario-matrix.json projects the full parent-and-child required denominator: 30 scenarios x2 actual hosts, including T15/new-product from parent R19. Every parent Testing Decision maps to these cases or the explicit SG-01/SG-02 public evidence guards; child issue lists cannot narrow parent acceptance. Matrix references and hashes travel in every evaluator/supervisor/review packet, never subject input.

Root runs canonical unit pytest, Codex flow/install pytest and Claude engine node --test once on final integration, plus each scenario evidence gate on current relevant candidate inputs. Baseline: 100+31+55=186, not feature proof. Each module gate runs after its tasks; changed producer/consumer seams get affected integration checks. Scenario subject input excludes criterion/oracle, tests candidate checkout not installed Skill, retains both actual hosts. Root launches subjects through Orca when evaluator provides raw brief; nested worker guards are not bypassed. Max3 live workers, including evaluator/subject/reviewer. Independent fixture directories avoid shared resources; explicitly mutex any discovered physical target before dispatch. Gates requiring missing authority/environment remain unverified with exact recovery, not substituted.

## Review Gates

Each candidate: builder TDD -> fresh supervisor acceptance rerun -> independent Standards and Spec review -> repairs -> serialized merge -> post-merge focused acceptance -> grillstorm-confirmed marker. Root owns integration and final fixed-ref two-axis review. Task writers never edit control plane. Stage only owned declared files, no git add -A/stash/cleanup; original checkout untouched. New required path or interface change goes to controller for bounded replan and revalidation.

## Execution Log / Deviations / Autonomous Decisions

No implementation launched. See state.json, autonomous-decisions.md and reviews/* ledger. Local run-owned commits allowed after review; no push/deploy/install. Main has unrelated external work: recheck before eventual merge. Scenario evidence outputs are task-owned under tests/scenarios/Tn; controller links them into execution reports. Do not mutate docs/grillstorm from task writers because frozen artifact contracts forbid control-plane writes.
