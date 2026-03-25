---
name: cr-visual
description: "Visual fidelity: screenshot + recording comparison -> fix differences -> re-compare -> until visually consistent. Modes: full / analyze / fix"
version: "1.0.0"
---

# CR Visual — Visual Fidelity Comparison

## Parameters

Infer from the user's natural language request:

| Parameter | Format | Description |
|-----------|--------|-------------|
| `--source` | URL or path | Source App address (e.g., http://localhost:3000) or start command |
| `--target` | URL or path | Target App address (e.g., http://localhost:5000) or start command |
| `--screenshots` | directory path | Source App screenshot directory (alternative to --source when source App is unavailable) |

## Missing Parameter Guidance

When parameters are unclear, ask naturally:
1. **Source App screenshots**: "Can the source App run? If so, provide the URL. Otherwise, do you have a screenshot directory?"
2. **Target App address**: "What is the target App URL or how do you start it?"

## Prerequisites

- `.allforai/experience-map/experience-map.json` must exist (provides screen list)
- Source App or source screenshots — at least one must be available
- Target App must be accessible

## Execution

> Details: `./skills/cr-visual.md`

## Quick Reference

```
cr-visual                                            # Interactive guided
cr-visual --source http://localhost:3000 --target http://localhost:5000
cr-visual --screenshots ./source-screenshots --target http://localhost:5000
```
