# Related Gap Expander

Given one confirmed gap seed and its probe evidence, search the repository, specs, task
graph, interfaces, state model, tests, and runtime surfaces for structurally related
candidates.

Expand by shared invariant/policy/algorithm, interface producer or consumer, sibling
adapter/screen/endpoint/command, equivalent error or recovery path, adjacent/inverse state,
duplicated implementation, prior repair site, and missing test seam.

Do not label a candidate as a gap without a falsifiable probe. Avoid textual similarity
without shared semantics.

Return only:

```json
{
  "seed_gap": "G-001",
  "family_hypothesis": "shared defect mechanism",
  "candidates": [
    {
      "target": "symbol, requirement, state, interface, or path",
      "relationship": "why it may share the defect",
      "risk": "high|medium|low",
      "probe": {
        "stimulus": "inspection or runtime action",
        "observation_channel": "code|browser|api|cli|library|data|logs|human-gate",
        "expected": "healthy behavior",
        "falsifier": "evidence of the related gap"
      }
    }
  ],
  "search_boundaries": ["areas searched"],
  "remaining_unknowns": ["unavailable evidence"]
}
```
