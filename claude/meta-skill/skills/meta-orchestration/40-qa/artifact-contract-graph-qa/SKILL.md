---
name: artifact-contract-graph-qa
description: Validate that a dynamic skill composition graph has explicit producers, consumers, dependency order, repair routes, and no hidden fallback paths.
---

# Artifact Contract Graph QA Skill

> Internal sub-skill for meta-orchestration. Status: bundled,
> bootstrap-support.

## Overview

Checks the artifact graph emitted by dynamic skill composition before bootstrap
uses it to generate workflow nodes. It is a graph QA layer, not a business or
implementation QA layer.

## Input Contract

Required: skill composition plan, artifact contract graph, available bundled
skill index, and bootstrap profile.

Optional: existing workflow, node-specs, approval records, previous validator
reports, and domain-extension handoffs.

## Output Contract

Writes `.allforai/orchestration/artifact-contract-graph-qa-report.json`.

The report must include `graph_status`, `skill_path_findings`,
`producer_consumer_findings`, `dependency_order_findings`,
`cycle_findings`, `blocked_scope_findings`, `repair_route_findings`,
`handoff_findings`, `validator_hints`, `state`, and `consumer_refs`.

Allowed states: `passed`, `failed`, `needs_revision`, `blocked_by_missing_plan`.

## Invocation Contract

```json
{"skill":"meta-orchestration/artifact-contract-graph-qa","mode":"validate","input_paths":{"composition_plan":".allforai/orchestration/skill-composition-plan.json","artifact_graph":".allforai/orchestration/artifact-contract-graph.json","bootstrap_profile":".allforai/bootstrap/bootstrap-profile.json","skill_index":"${CLAUDE_PLUGIN_ROOT}/skills"},"output_root":".allforai/orchestration"}
```

Supported modes: `validate`, `repair_check`.

## Automatic Validation

Reject the graph when:

- a selected skill path does not exist,
- a required input has no producer and is not declared external,
- a selected skill has no expected output,
- an intermediate output has no consumer,
- a cycle is present,
- a repair route points to a missing skill,
- a downstream handoff ignores a selected domain extension,
- a node would need hidden conversation memory instead of artifacts.

Final review HTML, QA reports, approval records, and human dashboards may be
terminal outputs with no further consumer.

## Completion Conditions

Return `COMPLETED` only when the report state is `passed`. Return
`FAILED_VALIDATION` when the graph requires hidden fallback, implicit memory, or
unresolved artifacts.
