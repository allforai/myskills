---
name: meta-orchestration
description: Dynamically select, connect, and validate bundled skills based on project concept, domain, surfaces, risks, required artifacts, and downstream execution needs.
---

# Meta Orchestration Skill Pack

> Internal bundled sub-skill pack for meta-skill pipelines. Status: bundled,
> bootstrap-support, used to compose non-fixed skill graphs.

## Purpose

Meta Orchestration turns concept analysis into a project-specific skill graph.
It does not produce business, UI, art, or code specs. It decides which bundled
skills should run, how their artifacts connect, and whether the resulting graph
is contract-closed enough for bootstrap to generate node-specs.

Use this pack when a project may require different skills depending on concept,
domain, app surfaces, game genre, art pipeline, commerce/payments, security,
runtime, or verification needs.

## Current Children

| Layer | Child skill | Responsibility |
|---|---|---|
| `20-spec` | `dynamic-skill-composition` | Select required/optional skills and produce a project-specific skill composition plan. |
| `40-qa` | `artifact-contract-graph-qa` | Validate artifact producers, consumers, dependencies, repair routes, and blocked scopes. |
| `40-qa` | `bootstrap-node-expansion-qa` | Validate that bootstrap expanded the guiding philosophy into enough concrete nodes: reverse reasoning, closure loops, and acceptance-driven effect verification. |
| `40-qa` | `unattended-run-readiness-qa` | Validate before `/run` that the workflow can execute unattended without human prompts, missing tools, or hidden fallback completion. |
| `40-qa` | `execution-repair-loop` | Generic QA-discovered implementation repair and revalidation loop for app, game, frontend, backend, UI, and runtime workflows. |

## Canonical Invocation Paths

```text
${CLAUDE_PLUGIN_ROOT}/skills/meta-orchestration/20-spec/dynamic-skill-composition/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/meta-orchestration/40-qa/artifact-contract-graph-qa/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/meta-orchestration/40-qa/bootstrap-node-expansion-qa/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/meta-orchestration/40-qa/unattended-run-readiness-qa/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/meta-orchestration/40-qa/execution-repair-loop/SKILL.md
```

## Shared Output Root

All children write under `.allforai/orchestration`.

Bootstrap may consume `.allforai/orchestration/skill-composition-plan.json` as
the source of truth for generated node-specs when present. If the plan is absent
or failed, bootstrap may use legacy capability rules but must mark dynamic
composition as unavailable in the bootstrap report.

## Boundary

Do not invent domain requirements here. Use domain skills to define domain
content. This pack only selects skills, connects artifacts, validates graph
closure, and blocks `/run` before execution when the workflow is not ready for
unattended execution.
