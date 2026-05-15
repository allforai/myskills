## Anonymous Meta-Skill Feedback

Category: discovery-blind-spot
Meta-skill version: unknown

### Failure Pattern

CC3 preview serves stale compiled JS bundles from library/ cache — source .ts edits have no effect until compiled output is also updated. AI agents that fix .ts files must also update the compiled cache or verify compilation occurred. Symptom: source is correct, but runtime behavior unchanged.

### Expected Behavior

The meta-skill should record or repair this class of workflow issue without exposing project-specific information.

### Suggested Fix

Update the relevant skill, bootstrap rule, validator, or orchestrator helper so future projects do not hit the same failure pattern.
