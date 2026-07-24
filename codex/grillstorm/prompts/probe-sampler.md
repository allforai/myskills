# Post-Delivery Probe Sampler

Build a stratified, risk-weighted probe plan from the approved specs, decisions, tasks,
runtime evidence, implementation diff, and current repository.

Before sampling, enumerate the complete requirement-by-state population and classify each
cell as `implemented-and-probed`, `implemented-evidence-only`, `missing`, `contradictory`,
`unverifiable`, or `not-applicable`. Sampling deepens this census; it does not replace it.

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
      "status": "implemented-and-probed|implemented-evidence-only|missing|contradictory|unverifiable|not-applicable",
      "evidence": ["paths, tests, runtime artifacts, or rationale"]
    }
  ],
  "sampling_frame": [{"stratum": "name", "population": ["IDs"], "risk": "high|medium|low"}],
  "probes": [
    {
      "id": "P-001",
      "axis": "logic-alignment|feature-state-completeness",
      "target": "requirement/state/invariant/interface ID",
      "hypothesis": "claim under test",
      "stimulus": "inspection or runtime action",
      "observation_channel": "code|browser|api|cli|library|data|logs|human-gate",
      "expected_evidence": "observable result",
      "falsifier": "what would show a gap",
      "selection_reason": "stratum/risk/rotation",
      "related_neighborhood_keys": ["symbols, IDs, states, paths"]
    }
  ],
  "unsampled": [{"target": "ID", "reason": "rotation|reality-gate|lower-risk"}]
}
```
