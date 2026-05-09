# Game Subskill Depth Pass

## Goal

Deepen subskills that are contract-usable but still too shallow. The target is
not implementation code; it is stronger executable contracts: schema fields,
state machines, consumers, repair routing, root-cause classification, and
specialized validation rules.

## Target Scope

Primary targets:
- `game-systems/*`
- `game-level/*`
- `game-audio/*`
- `game-narrative/*`

Secondary targets:
- newly added lightweight `game-art` asset/QA skills when they need consumer or
  model-profile detail.

## Round 1: Schema And State

- [x] Add required schema fields to thin outputs.
- [x] Add allowed state/status values where artifacts progress over time.
- [x] Clarify required IDs and path roots.
- [x] Ensure no generated/runtime asset can be treated as approved without QA.

## Round 2: Consumers And Repair Routing

- [x] Add downstream consumer lists to relevant outputs.
- [x] Add root-cause categories for QA and generation failures.
- [x] Add repair routing rules so failures return to the correct upstream skill.
- [x] Add cross-pack references for UI, art, level, audio, narrative, and systems.

## Round 3: Consistency Checks

- [x] Verify all target skills include standard contract sections.
- [x] Verify image-backed skills declare `generation_profile.task_type`.
- [x] Verify top-level pack files expose canonical invocation paths.
- [x] Verify no known thin target lacks schema/state/repair detail.

## Completion Definition

This pass is complete when all three rounds are checked off and automated grep
checks report no missing standard contract sections or image profile references.
