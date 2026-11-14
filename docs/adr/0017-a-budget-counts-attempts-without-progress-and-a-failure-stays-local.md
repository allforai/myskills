---
status: accepted
---

# A budget counts attempts without progress, and a failure stays local

A live product run on 0.30.0 was started eight times in four days and never finished. Each start ended at a stop that told the user to return to interactive bootstrap. Two of the causes needed a person: an unanswered product decision and an unconfirmed plan change. The rest did not.

1. The repair ledger counted attempts for the life of the plan. Two loops had each spent their three attempts in 48 minutes on a defect of the engine itself (ADR-0016, item 1), with no QA rerun between them. After the fix they still had nothing left, and the only way to a new budget was to plan a new repair node.
2. The run template stopped as UNRESOLVED once `diagnosis_history` held five entries. The history is never emptied, so from the fifth entry on every failure stopped the run without a diagnosis.
3. A fixed budget stopped a loop that was converging: one QA node's blocking findings had fallen from 117 to 28 when its third attempt ran out.
4. The graph made each finding expensive. One freeze node waited for ten others, among them art QA and an experience critique, and every implementation node waited for it: 28 findings about shop images held up all server work. Art was listed, generated and judged as one batch. Two server checks waited for the client. Thirty-six implementation nodes were judged by seven QA nodes at the very end. Every node of a stage carried the same acceptance list.

ADR-0006 made an attempt a durable charge that nothing refunds. That stays true of an attempt. What changes is which attempts a budget counts.

## Decision

**A. A budget bounds one invocation.** Attempts granted before the latest `run_started` event in the run log are history: the ledger keeps them and leaves them out of the spend. A plan revised between invocations is the plan, so only a bound that moves under attempts still being counted is a `budget_conflict`. The diagnosis cap follows the same boundary: `run_started` records how long `diagnosis_history` was, and `record_run_event.py --diagnosis-budget` counts what came after.

**B. A budget counts attempts without progress.** Each failed QA verdict of a declared loop is recorded in the ledger with its number of blocking findings. A count lower than every earlier one of the invocation is progress, and the spend starts again from there. `max_attempts` is therefore the number of attempts in a row that did not lower the count. One obligation is never granted more than ten attempts in an invocation, or its `max_attempts` when that is higher, so a loop that removes one finding at a time still ends.

**C. A stop says what it needs.** A loop that stopped or a cap that was reached is reported with its open findings and "run again to continue". Only an unanswered product decision, an unconfirmed plan change, or a defect in the plan itself sends the user to interactive bootstrap.

**D. A node may be reviewed in place.** A node that declares `inline_review` is reviewed as soon as it passes, by an agent that did not produce its output, against its own acceptance and the criteria of the QA node named in the declaration. Findings go to `.allforai/bootstrap/inline-review/<node_id>.json`; the node is run again to fix them in its own files. Reviews continue while each finds fewer findings than the best so far, six at most. When they stop falling the node completes with the file as the record of what is open, and the QA node downstream judges it. Only a revision that fails the node's own gate fails the node. Reviewer, reviser and controller each run in a fresh context and exchange files only.

**E. The plan keeps a failure local.** `bootstrap-planning.md` § Keep a failure local states what must be true of the graph: a node depends on what it reads; a QA node waits only for what it judges; bulk output is produced, judged and repaired in parts; every node states its own acceptance; a producer judged for quality declares `inline_review`. The node-expansion audit rejects a graph that breaks these as `failure_not_local`. `validate_bootstrap.py` refuses an `inline_review` that cannot be carried out.

## Alternatives rejected

- Renewing the budget whenever the engine starts. The run template restarts the engine after each diagnosis, so a loop would never run out within one invocation.
- Counting only attempts whose repair was judged by a QA rerun. A repair that never delivers would then cost nothing and could repeat without end; the invocation boundary already returns what an engine defect wasted.
- Judging progress by comparing finding texts. Reviewers word the same defect differently on each run; a count is the one figure that can be compared.
- Failing a node whose inline review does not converge. The review would then add stops, and the planned QA node already judges the same output.
- Refusing at validation any nodes that share an acceptance list. Every project planned before this would stop at its next run, and producers of parallel parts rightly share one list; whether a list is a copied stage goal is left to the node-expansion audit.

## Cross-host (ADR-0004)

| Decision | Claude | Codex | Pi |
|---|---|---|---|
| A | Shared `repair_authorization.py`; run template step 3 reads `--diagnosis-budget` | Same ledger; `flow.py` counts stagnation per run already | Same ledger |
| B | Engine sends `verdict` before routing, from the QA node's `blocking_count` | `flow.py` sends it after a failed QA attempt, counting the report files | Template tells the orchestrator to send it |
| C | Template clause `run-invocation-allowance` | Stamped copy | Stamped copy |
| D | `runNodeWithReview` in the engine | `run_inline_review` in `flow.py` | Template rule; needs `subagent`, otherwise skipped and disclosed |
| E | Shared planning guide and audit skill | Same | Same |

## Consequences

- A project needs its scripts, engine and run entry refreshed by `/bootstrap` before A–C apply. Its old ledger is read as it is.
- The count in B comes from the QA node on Claude and Pi and from report files on Codex. A QA node that under-counts keeps its loop running to the ceiling of ten; nothing checks the count against the report.
- A run can take longer and cost more than under a fixed budget of three: up to ten repair attempts per obligation and six reviews per reviewed node in one invocation.
- D and E apply only to graphs planned after this. An existing plan gains them when it is replanned.
- On Codex the generic consecutive-failure and stagnation caps now rise to the ceiling for every node of a declared loop, whatever its `max_attempts`.
- A grant left without an outcome by an interrupted run still stops the next start for reconciliation (ADR-0006). That stop is unchanged.
