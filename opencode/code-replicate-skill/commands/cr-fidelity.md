---
name: cr-fidelity
description: "Fidelity verification: compare source vs target code, score across multiple dimensions, analyze -> fix -> re-score loop if below threshold. Modes: full / analyze / fix"
version: "2.0.0"
---

# CR Fidelity — Fidelity Verification

## Parameters

Infer from the user's natural language request:

| Parameter | Format | Description |
|-----------|--------|-------------|
| `mode` | positional #1 | full (complete loop) / analyze (report only) / fix (fix gaps from last analysis) |
| `--target` | path | Target code root directory (default: current directory) |
| `--threshold` | number | Pass score (default: 90, range 0-100) |

## Missing Parameter Guidance

When parameters are unclear, ask naturally:
1. **Target code location**: "Where is the dev-forge generated target code?"
2. **Verification mode**: "Do you want a full analysis+fix loop (recommended) or just a report?"

## Prerequisites

1. `.allforai/code-replicate/source-summary.json` must exist (code-replicate has run)
2. `.allforai/product-map/task-inventory.json` must exist (artifacts generated)
3. Target code directory must exist and contain code files

Missing any prerequisite -> prompt user to run `code-replicate` and `task-execute` first.

## Execution

> Details: `./skills/cr-fidelity.md`

## Quick Reference

```
cr-fidelity                              # Interactive guided
cr-fidelity full                         # Full loop: analyze -> fix -> retest until passing
cr-fidelity analyze                      # Report only, no fixing
cr-fidelity fix                          # Fix gaps found in last analysis
cr-fidelity full --threshold 95          # Set 95 as pass threshold
cr-fidelity full --target ./target-app   # Specify target code path
```
