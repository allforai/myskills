---
status: accepted
---

# A run asks nothing and takes its own recommendation

`/run` kept stopping. Before the first node it asked three Run Policy questions. In the middle, a node that met a user-visible rule the frozen intent did not settle failed with `unresolved_product_decision`, parked its subgraph, and the run ended `needs_product_decision` (ADR-0011 D); readiness then refused the next run until interactive bootstrap had answered. Each stop was correct by its own rule, and each one meant an unattended run that had delivered less than it could when the user came back.

The user's rule is simpler than the ones it replaces: **`/bootstrap` is where questions are asked. `/run` goes from its first line to its report unattended, takes the recommended option wherever a choice is open, and says at the end what it chose.**

## Decision

**A. Run Policy is recorded, never asked.** With no usable `run-policy.json`, `product_intent.py --run-policy` records the first option of each event, marked `chosen_by: default`, and returns `run_policy_ready`. It never returns a question. Explicit answers with an actual user reference replace a policy at any time outside a run; whatever a write replaces is kept in `run-policy-repairs.json`. The defaults keep the conservative end for the coverage gate (`halt_with_report`): that gate is the last node, so stopping there loses no work, and `auto_fix_once` needs a declared repair loop a plan may not have.

**B. A node takes an unsettled product choice on its recommendation.** A node that owns a user-visible rule the frozen intent and decision journal do not settle weighs at least two options, builds with the one it recommends, and writes `.allforai/bootstrap/run-decisions/<node_id>.json` (`decision_id`, `needed_decision`, `options`, `recommended`, `taken`, `why`, `blocking_intent_ids`). It then passes or fails on its work like any other node. It never takes a choice that contradicts a recorded decision, and it never chooses silently.

**C. Completion discloses every decision made for the user.** `product_intent.py --delegations` returns, beside the directions the user delegated, `run_decisions` (every record under B) and `run_policy_defaults` (the choices under A nobody made). The three run templates print each list under its own heading; the clause is registered in `shared/seam-contracts/clauses.json`.

**D. Bootstrap is where a taken choice is confirmed or overturned.** Phase A's queue includes every `run-decisions/` record. A confirmed choice is wired into the node's `decision_inputs` and changes nothing; an overturned one makes that node's output stale, so it runs again. A `run-decisions/` record never blocks readiness.

## What this reverses

- ADR-0011 D's last rule, "a recommendation nobody answered is not an action — that rule stays in force inside `/run`". It stays in force at bootstrap, where the user is present. Inside a run the node's recommendation is the action, and the record is what makes that acceptable.
- The one-time Run Policy interview at the run entry, and "invalid policy blocks for interactive repair".

ADR-0011 A, B and C stand: decision coverage, per-node rehearsal and the dimension × state crossing still mine decisions before the run, so that B here stays rare. The `needs_product_decision` path in both engines and the `pending_product_decision` readiness blocker remain for workflows bootstrapped under ADR-0011, whose generated drivers and prompts still park.

## Not changed

A run still stops when it cannot go on: readiness not `ready` before the first node, a safety halt, an exhausted repair budget, a defect in the plan. Those are reports, not questions, and none of them asks the user to choose mid-run.

## Consequences

- A product may ship a rule the user would have chosen differently. The cost is one rerun of the nodes downstream of that rule, and the user sees the choice in the completion text rather than discovering it.
- A project bootstrapped earlier keeps its generated run entry and driver until `/bootstrap` is rerun.
