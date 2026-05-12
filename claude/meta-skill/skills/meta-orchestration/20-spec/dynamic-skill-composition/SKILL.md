---
name: dynamic-skill-composition
description: Select and connect the right bundled skills for a project based on concept, business domain, surfaces, technical shape, risks, and requested goals.
---

# Dynamic Skill Composition Skill

> Internal sub-skill for meta-orchestration. Status: bundled,
> bootstrap-support.

## Overview

Generates a project-specific skill composition plan instead of relying on a
fixed workflow graph. The plan is declarative: it names selected skills, why
they are selected, what artifacts they require, what artifacts they produce,
and how bootstrap should turn them into nodes.

## Input Contract

Required: bootstrap profile, product concept or reverse-product inference,
detected business domain, goals, target surfaces, known technology stack, and
available bundled skill index.

Optional: existing workflow, existing node-specs, human preferences,
domain-knowledge files, codebase scan findings, package manifests, UI/runtime
test capability, and previous failure reports.

## Output Contract

Writes:

- `.allforai/orchestration/skill-composition-plan.json`
- `.allforai/orchestration/artifact-contract-graph.json`

`skill-composition-plan.json` must include `project_facts`,
`selection_rules_applied`, `selected_skills`, `skipped_skills`,
`conditional_skills`, `node_groups`, `dependency_edges`, `required_artifacts`,
`produced_artifacts`, `approval_gates`, `blocked_scopes`, `repair_routes`,
`state`, and `consumer_refs`.

Each `selected_skills[]` entry must include `skill_path`, `selection_reason`,
`triggering_facts`, `required_inputs`, `expected_outputs`, `hard_blocked_by`,
`unlocks`, `node_id_hint`, `human_gate`, `owner`, `state`, and `consumer_refs`.

`artifact-contract-graph.json` must include `artifacts[]`, `producers[]`,
`consumers[]`, `edges[]`, `missing_producers[]`, `orphan_outputs[]`,
`cycles[]`, `blocked_items[]`, `state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_missing_concept`, `blocked_by_skill_index`.

## Invocation Contract

```json
{"skill":"meta-orchestration/dynamic-skill-composition","mode":"compose_validate","input_paths":{"bootstrap_profile":".allforai/bootstrap/bootstrap-profile.json","concept":".allforai/product-concept/concept-baseline.json","skill_index":"${CLAUDE_PLUGIN_ROOT}/skills"},"output_root":".allforai/orchestration"}
```

Supported modes: `compose_validate`, `validate_existing`, `repair_existing`.

## Selection Method

1. Classify the project facts: domain, surfaces, runtime shape, data intensity,
   payment/order/security needs, content needs, game/app boundary, art/audio
   needs, and verification capability.
2. Select always-required skills for the requested goal.
3. Select conditional skills only when triggering facts exist. Example:
   ecommerce facts select `app-domain/ecommerce`; mobile surfaces select
   platform-specific UI verification; game-art needs select game-art children.
4. For every selected skill, copy its declared required inputs, outputs,
   validation mode, completion state, and repair routing into the plan.
5. Build dependency edges from required inputs to producing skills. If no
   producer exists, mark the skill blocked or route the missing artifact to a
   producer skill; do not silently invent data.
6. Keep skipped skills explicit with a reason so the graph can be audited.

## Automatic Validation

Check every selected skill path exists and has a `SKILL.md`. Check every
required input is produced by an earlier selected skill, supplied by bootstrap,
or listed as a blocked external prerequisite. Check no dependency cycle exists.
Check every produced artifact has at least one consumer unless it is a final
review/report artifact.

When the graph cannot be closed, set `state: "needs_revision"` or a blocked
state and identify the exact missing producer, missing consumer, or cycle. Do
not fall back to generic LLM execution without recording the failure.

## Completion Conditions

Return `COMPLETED` when the composition plan is validated and bootstrap can
generate node-specs from it. Return `FAILED_VALIDATION` when selected skills
cannot be connected by explicit artifacts.
