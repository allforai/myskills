## Anonymous Meta-Skill Feedback

Category: freshness-parallel-branches
Meta-skill version: unknown

### Failure Pattern

evidence_freshness treats outputs consumed by no node as unmapped input for every non-downstream root, so independent parallel branches invalidate each other and all downstream publication is refused; bootstrap should wire unconsumed write scopes (e.g. to the closure node's input_dependencies) automatically, and node-specs should require capture_evidence/v1 records since plain-log evidence counts as unverified

### Expected Behavior

The meta-skill should record or repair this class of workflow issue without exposing project-specific information.

### Suggested Fix

Update the relevant skill, bootstrap rule, validator, or orchestrator helper so future projects do not hit the same failure pattern.
