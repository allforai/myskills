# Contract Wiring QA Skill

> Internal sub-skill for game-design pipelines. Status: bundled, inactive, not wired.

## Overview

Validates that mapped game-design sub-skills are not merely present on disk but
can exchange artifacts through the bootstrap workflow, final aggregation, and
`product-analysis` handoff.

## Input Contract

Required: game-design capability mapping, selected node-specs, game-design
registry, approval records, and all selected child-skill output artifacts.

Optional: bootstrap workflow, product-analysis mapping rules, generated
`game-design-doc.json`, `art-input-handoff.json`, and
`program-development-node-handoff.json`.

## Output Contract

Writes `.allforai/game-design/design/contract-wiring-qa-report.json`.

Findings must include `finding_id`, `node_id`, `sub_skill_path`,
`contract_axis`, `severity`, `expected`, `actual`, `evidence_paths`,
`repair_target`, `blocks_finalization`, and `state`.

Allowed contract axes: `input_missing`, `output_missing`,
`schema_mismatch`, `state_mismatch`, `dependency_gap`, `consumer_gap`,
`repair_route_missing`, `validation_gap`, `handoff_gap`.

Allowed states: `passed`, `passed_with_warnings`, `needs_revision`,
`blocked_by_missing_artifacts`, `failed_validation`.

## Invocation Contract

```json
{
  "skill": "game-design/contract-wiring-qa",
  "mode": "validate",
  "input_paths": {
    "capability": "claude/meta-skill/knowledge/capabilities/game-design.md",
    "workflow": ".allforai/bootstrap/workflow.json",
    "approval_records": ".allforai/game-design/approval-records.json",
    "game_design_doc": ".allforai/game-design/game-design-doc.json",
    "program_handoff": ".allforai/game-design/design/program-development-node-handoff.json"
  },
  "output_root": ".allforai/game-design/design"
}
```

Supported modes: `validate`, `validate_mapping_only`, `repair_targets`.

## Automatic Validation

For every selected node with `sub_skill_paths`, check:

- each `SKILL.md` path exists and has input/output/invocation/validation
  sections;
- required upstream artifact names match actual selected predecessor outputs;
- declared outputs are included in either `game-design-doc.json`, final handoff
  artifacts, or a documented downstream consumer;
- states can flow into finalization (`validated` or explicitly non-blocking);
- each validation failure has a repair target, not a silent fallback.

For every selected node with `—`, report `needs_revision` unless the capability
explicitly marks it as an intentional LLM fallback. Do not mark a path verified
only because it exists.

## Completion Conditions

Return `COMPLETED` when selected game-design nodes have artifact-level
traceability from inputs to outputs to downstream consumers. Return
`FAILED_VALIDATION` when a selected node lacks a producer, consumer, schema
bridge, or repair route.
