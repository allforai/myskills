# Content Roadmap Spec Skill

> Internal sub-skill for game-content pipelines. Status: bundled, inactive, not wired.

## Overview

Defines content sequence, scope, release order, dependency plan, coverage, and
cadence for campaign, live, or staged content.

## Input Contract

Required: content registry and core loop/progression context.

Optional: level design, narrative quest spec, economy spec, liveops event spec,
and production capacity.

## Output Contract

Writes `.allforai/game-design/content/content-roadmap-spec.json` and a report.
Roadmap entries include `roadmap_id`, `content_refs`, `release_phase`,
`player_goal`, `dependency_refs`, `required_assets`, `required_data`,
`scope_risk`, `state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_dependencies`, `blocked_by_scope`.

## Invocation Contract

```json
{"skill":"game-content/content-roadmap-spec","mode":"spec_validate","input_paths":{},"output_root":".allforai/game-design/content"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check that roadmap phases serve the loop, dependencies are ordered, required
content has owners, and scope fits the declared production constraints.

Repair routing: orphan content routes to content-registry; pacing defects route
to content-pacing-qa; scope gaps route to implementation feasibility.

## Completion Conditions

Return `COMPLETED` when the roadmap is ordered and owned. Return
`FAILED_VALIDATION` when dependencies or scope block delivery.
