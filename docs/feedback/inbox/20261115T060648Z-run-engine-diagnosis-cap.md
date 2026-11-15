## Anonymous Meta-Skill Feedback

Category: run-engine/diagnosis-cap
Meta-skill version: unknown

### Failure Pattern

In one /run invocation the engine's commit-failures step appends a hard_fail entry to diagnosis_history for every failed node, and the orchestrator appends its own diagnosis for the same failure. Both count toward the 5-entry diagnosis cap, so two ordinary cross-node republish cycles (stale upstream evidence, root fixed by republish only) exhausted the cap. Separately, a repair node that registers a read of a file owned by a node it is not ordered after causes republish ping-pong; bootstrap audits did not flag the missing edge.

### Expected Behavior

The meta-skill should record or repair this class of workflow issue without exposing project-specific information.

### Suggested Fix

Update the relevant skill, bootstrap rule, validator, or orchestrator helper so future projects do not hit the same failure pattern.
