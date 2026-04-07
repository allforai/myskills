# Translate Capability

> Generate target platform code from source code + .allforai/ artifacts.
> Internal execution is LLM-driven — strategy selected per component.

## Goal

Generate target platform code from source code + .allforai/ artifacts.
Strategy selection per component, compile-verify loop per module.

## What LLM Must Accomplish (not how)

### Required Outcomes

- Target project scaffold initialized and building
- All components translated with appropriate strategy
- Compile-verify loop passed for each component
- Route parity verified (every source route has a target equivalent)
- Model-to-route traceability verified
- Prune scope respected: load `.allforai/feature-prune/prune-tasks.json` before planning component scope. Only implement tasks where `decisions[].included = true`. Tasks with `included = false` must NOT be implemented — create a `TODO(excluded-by-prune)` comment at most.

### Strategy Selection (per component, LLM decides)

| Complexity | Strategy | LLM Input | Output |
|-----------|----------|-----------|--------|
| Low (pure UI, no logic) | direct_translate | Source code + mapping | Syntax-converted code |
| Medium (stateful, controllable) | translate_with_adapt | Source code + target patterns | Translated + restructured |
| High (complex business, cross-module) | intent_rebuild | .allforai/ artifacts (not source) | Native target code from intent |

### Required Quality

- Compile after every component — don't batch
- `TODO(migration)` for unmappable items — not silent skip
- Abstraction preservation — don't expand shared base classes into N copies
- Route parity — every source route/endpoint has a target equivalent
- Consumer-priority: if experience_priority = consumer/mixed, UI completion bar is higher

## Methodology Guidance (not steps)

- **Scaffold first**: Initialize target project, verify it builds before any translation
- **Topological order**: Translate by dependency (foundations first, UI last)
- **Compile after every component**: Catch errors early
- **intent_rebuild reads artifacts, not source**: Prevents copying technical debt
- **Round-based checkpointing**: Persist progress after each round

## Knowledge References

### Phase-Specific:
- cross-phase-protocols.md §Upstream-Baseline-Validation: verify translated code against product artifacts
- experience-map-schema.md: screen contracts for UI translation

## Composition Hints

### Split into Multiple Nodes (default)
ALWAYS split per target platform: translate-ios, translate-api, translate-web.

### Single Node
Only for single-platform projects with a small codebase.
