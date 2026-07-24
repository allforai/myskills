# Post-Delivery Probe Sampler

Build a stratified, risk-weighted probe plan from the approved specs, decisions, tasks,
runtime evidence, implementation diff, and current repository.

Use the supplied frozen `requirements-state-registry.json` as the complete population. Do
not add, omit, or rename requirement/state cells. Classify each cell as
`implemented-and-probed`, `implemented-evidence-only`, `missing`, `contradictory`,
`verification-failed`, or `not-applicable`. Sampling deepens this census; it does not
replace it.

Produce two independent sample banks:

- `logic-alignment`: whether architecture, domain model, algorithms, policies, ownership,
  interfaces, and lifecycle implement the user's intended logic;
- `feature-state-completeness`: whether behavior and detail are complete across applicable
  states, transitions, side effects, failures, and recovery.

Cover every applicable stratum at least once, oversample high-risk boundaries and repaired
areas, identify the unsampled population, and do not infer completeness from green samples.
Prefer probes that can falsify an important claim.

Return only:

```json
{
  "round": 1,
  "census": [
    {
      "requirement": "R-001",
      "state": "success|empty|loading|degraded|invalid|denied|failure|retry|concurrent|recovery|other",
      "status": "implemented-and-probed|implemented-evidence-only|missing|contradictory|verification-failed|not-applicable",
      "evidence": ["paths, tests, runtime artifacts, or rationale"]
    }
  ],
  "sampling_frame": [{"stratum": "name", "population": ["IDs"], "risk": "high|medium|low"}],
  "probes": [
    {
      "id": "P-001",
      "axis": "logic-alignment|feature-state-completeness",
      "targets": [{"requirement": "R-001", "state": "success"}],
      "hypothesis": "claim under test",
      "action": "inspection or runtime action",
      "observation_channel": "code|document|browser|api|cli|library|data|device|external",
      "expected_evidence": "observable result",
      "falsifier": "what would show a gap",
      "selection_reason": "stratum/risk/rotation",
      "related_neighborhood_keys": ["symbols, IDs, states, paths"]
    }
  ],
  "unsampled": [
    {"requirement": "R-002", "state": "error",
     "reason": "rotation|lower-risk"}
  ]
}
```

Logic-alignment probes use only `code` or `document`. Feature-state-completeness probes must
use a runtime channel. Every high-risk registry cell must be probed in the current plan.
