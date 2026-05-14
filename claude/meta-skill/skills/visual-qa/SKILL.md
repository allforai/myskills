---
name: visual-qa
description: Internal bundled meta-skill module for reusable visual QA workflows; use when any project artifact needs batch screenshot/image/contact-sheet review through Codex CLI with auditable reports and repair loops.
---

# Visual QA Skill Pack

> Internal bundled sub-skill pack for meta-skill.
> Status: bundled, inactive, not wired.

## Purpose

Visual QA owns reusable visual evidence review mechanics. Domain packs such as
`game-art`, `game-ui`, `game-frontend`, app verification, and design gates
provide domain inputs; this pack derives explicit visual acceptance criteria
and handles batching, Codex CLI inspection, reports, feedback, and rerun
closure.

## Current Children

| Layer | Child skill | Responsibility |
|---|---|---|
| `00-env` | `visual-model-capability-registry` | Detect Codex CLI visual model availability and route batch tasks to suitable visual model profiles. |
| `20-spec` | `visual-acceptance-criteria` | Generate project/scene/asset/state visual standards, forbidden placeholders, evidence requirements, failure codes, and repair routes. |
| `40-qa` | `batch-visual-acceptance` | Batch Markdown visual review, mandatory Codex CLI inspection, JSON/Markdown report output, feedback, rerun, and closure audit. |

## Canonical Invocation Paths

Use these paths when a node-spec calls a child skill:

```text
${CLAUDE_PLUGIN_ROOT}/skills/visual-qa/00-env/visual-model-capability-registry/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/visual-qa/20-spec/visual-acceptance-criteria/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/visual-qa/40-qa/batch-visual-acceptance/SKILL.md
```

## Boundary

Visual criteria must be explicit before any visual batch runs. Use
`visual-acceptance-criteria` to derive reusable project/scene/asset/state
standards from domain inputs, then pass the generated JSON/Markdown criteria to
`batch-visual-acceptance`.

Callers must provide:
- domain inputs for criteria generation;
- evidence paths;
- batch grouping policy;
- repair routes or owner nodes.

Do not run visual QA from screenshots alone when
`.allforai/visual-qa/visual-acceptance-criteria.json` is missing for the visual
scope. Return `blocked_by_missing_visual_criteria` or `UPSTREAM_DEFECT`.

Codex CLI is the required visual reviewer. Claude Code should not duplicate the
visual judgment; it may audit closure, evidence references, feedback routing,
and rerun records.

High-risk visual batches must be routed through
`visual-model-capability-registry` before review. If model capability is missing
or unknown, the batch must block instead of passing with a weak substitute.
