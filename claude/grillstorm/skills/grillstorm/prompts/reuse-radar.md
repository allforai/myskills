# Reuse Radar

Inspect the repository and approved goal before module boundaries are frozen.

Identify existing deep modules, algorithms, policies, state machines, adapters, integrations,
and third-party libraries relevant to the goal. Flag likely shared capabilities, duplicated
knowledge, and dependency direction constraints.

Return only:

```json
{
  "candidates": [
    {
      "concept": "stable concept or invariant",
      "locations": ["code paths"],
      "likely_consumers": ["goal areas"],
      "classification": "reuse|extend|possible-extract|keep-local",
      "evidence": "why",
      "risk": "main coupling or premature-abstraction risk"
    }
  ]
}
```

This is non-binding. Do not create modules or interfaces before complete consumer specs
exist.
