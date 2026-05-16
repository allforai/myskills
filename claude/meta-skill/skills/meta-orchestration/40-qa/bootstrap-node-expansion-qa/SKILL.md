---
name: meta-orchestration-40-qa-bootstrap-node-expansion-qa
description: Validate that bootstrap expanded project guidance into enough concrete workflow nodes using reverse reasoning, closure loops, and acceptance-driven effect verification.
---

# Bootstrap Node Expansion QA Skill

> Internal sub-skill for meta-orchestration. Status: bundled,
> bootstrap-support, pre-run gate.

## Overview

Bootstrap can fail silently by generating a small legal-looking workflow that
does not represent a mature product. This skill validates the generated
workflow before `/run`: it checks whether bootstrap expanded the guiding
philosophy into concrete nodes, dependencies, artifacts, and verification
evidence.

This is not a domain implementation skill. It is a meta QA gate for node
coverage and node completion standards.

## Guiding Philosophy

Every production workflow must be expanded through four lenses:

- **Reverse reasoning**: infer the shipped product surfaces, runtime modules,
  data containers, assets, integrations, and acceptance evidence from the final
  user experience, then backfill required nodes.
- **Closure loops**: every QA, visual review, runtime smoke, platform test, or
  artifact audit must route repairable findings into a repair-and-revalidation
  loop with a bounded retry budget.
- **Acceptance-driven execution**: node completion must include effect
  verification. "Code was written", "file exists", or "function is callable" is
  implementation evidence, not completion evidence.
- **Dimension elevation thinking**: raise the reasoning level above the current
  node list and above the user's named means. Do not merely add more
  categories. First distinguish the user's goal from the proposed route: "buy a
  plane ticket" may actually mean "arrive at a destination on time", where a
  train ticket could satisfy the goal better. For product automation, do not
  treat "use Cocos", "generate Canvas2D nodes", or "add this module" as the
  final objective until the underlying desired product outcome is clear. Model
  the workflow as an automated production system: what invariants, contracts,
  evidence, dependency closures, and failure-recovery mechanisms must exist for
  the system to reliably produce that outcome unattended? Then project that
  higher-level model back down into required nodes, node completion standards,
  validators, and repair routes.

## Input Contract

Required:

```text
.allforai/bootstrap/workflow.json
.allforai/bootstrap/node-specs/
.allforai/bootstrap/bootstrap-profile.json
```

Optional:

```text
.allforai/bootstrap/canvas2d-game-client-profile.json
.allforai/orchestration/skill-composition-plan.json
.allforai/game-design/game-design-doc.json
.allforai/app-design/app-design-doc.json
.allforai/concept-contract.json
.allforai/product-concept/concept-baseline.json
```

## Output Contract

Writes:

```text
.allforai/bootstrap/bootstrap-node-expansion-qa-report.json
.allforai/bootstrap/bootstrap-node-expansion-qa-report.md
```

The JSON report must include:

```json
{
  "status": "passed | failed",
  "checked_at": "<iso8601>",
  "reverse_reasoning_findings": [],
  "closure_loop_findings": [],
  "acceptance_driven_findings": [],
  "underexpanded_scope_findings": [],
  "node_completion_findings": [],
  "required_repairs": []
}
```

Allowed blocker codes:

- `underexpanded_product_surface`
- `missing_reverse_inference_node`
- `missing_runtime_or_surface_node`
- `missing_effect_verification`
- `missing_visual_acceptance`
- `missing_runtime_probe`
- `missing_io_effect_qa`
- `missing_platform_qa`
- `missing_dimension_elevation_review`
- `missing_high_level_product_dimension`
- `missing_repair_loop`
- `repair_loop_not_blocked_by_qa`
- `acceptance_not_blocked_by_repair_loop`
- `qa_report_without_revalidation`
- `code_only_completion`
- `fallback_completion_allowed`

## Automatic Validation

Reject the workflow when any of these conditions hold:

- product/runtime evidence implies multiple surfaces/modules, but bootstrap only
  generated scaffold/build/smoke nodes;
- bootstrap treats a named means, technology, module, or requested node as the
  final goal without checking the underlying product outcome and alternative
  routes;
- the workflow only follows the current implementation path and does not raise
  the reasoning level to production-system invariants, contract closure,
  evidence quality, dependency closure, and failure-recovery requirements;
- a game or app implementation workflow has QA nodes but no repair-and-
  revalidation loop;
- final acceptance or closure does not depend on the repair loop;
- a visible runtime node has no screenshot, runtime probe, or visual acceptance
  evidence;
- an I/O node has only mocks or function-call assertions, without real effect
  proof;
- a generated module node does not require production consumer wiring proof;
- a rewritten module node does not require import/export compatibility checks;
- node completion says `done`, `implemented`, or `file exists` without an
  effect verification artifact;
- QA outputs can be `partial`, `conditional_pass`, `accepted_with_warnings`, or
  fallback completion while still unlocking downstream production nodes.

## Canvas2D / Web Canvas Specialization

For Canvas2D/Web Canvas/WebView Canvas game clients, delegate the concrete
family matrix to:

```text
${CLAUDE_PLUGIN_ROOT}/knowledge/engines/canvas2d.md
```

The workflow must include or explicitly block the mature game-client families:
runtime core, interface cards, asset bundle, scenes, gameplay systems, browser
QA, gameplay visual QA, performance/DPR QA, repair loop, and concept
acceptance. Mobile targets must include high-DPR screenshot QA before native
build acceptance.

## Completion Conditions

Return `COMPLETED` only when `status == "passed"` and every production node has
effect verification. Return `FAILED_VALIDATION` if the workflow is
under-expanded, has code-only completion, lacks repair loops, or lets fallback
states unlock downstream nodes.
