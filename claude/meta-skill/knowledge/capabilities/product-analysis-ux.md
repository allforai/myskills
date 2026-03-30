# Product Analysis UX Capability

> Capability reference for the UX layer of product analysis:
> journey-emotion mapping, experience map, interaction gate.
> This is the second of 3 product-analysis nodes.

## Purpose

Map how users experience the product: emotional journey, screen interactions,
state variants, and quality gates. Bridges the gap between "what the system does"
(core) and "whether it's complete" (verify).

## Data Dependencies (Pull)

This node reads from `.allforai/product-map/` (produced by product-analysis-core):
- `role-profiles.json` — who the users are, experience_priority
- `task-inventory.json` — what operations each screen supports
- `business-flows.json` — end-to-end flows to walk through

**If any of these files are missing or incomplete, this node fails with a backtrack
to product-analysis-core.** The orchestrator handles the retry.

## Sub-Phases

### Journey-Emotion (if experience_priority = consumer or mixed)

- Per-role end-to-end emotional journey
- Touchpoints: moments where user interacts with the system
- Emotional valence per touchpoint: anxiety / frustration / satisfaction / delight
- Emotion low points → design opportunities for improvement
- Peak moments → features to preserve and amplify

Output: `.allforai/experience-map/journey-emotion-map.json`

**Sequencing rule**: Journey-emotion MUST precede experience-map.
Emotional context informs interaction quality expectations.

### Experience Map (if frontend exists)

- Screen inventory (from routes/pages in task-inventory)
- Component mapping per screen
- State variants per screen: empty / loading / error / success / permission-denied
- Interaction triggers: click / input / scroll / timer / remote-event
- Global components: nav, toast, modal, bottom-sheet
- Button-level exception flows: on_failure, validation_rules, exception_flows
- Screen-level conflict detection: redundant entries, unconfirmed high-risk ops, unhandled exceptions
- If experience_priority = consumer|mixed: first-screen main path, next-step guidance, return motivation, mobile rhythm, state system maturity

Output: `.allforai/experience-map/experience-map.json`, `.allforai/experience-map/screen-conflict.json`

### Interaction Gate (quality gate)

- Interaction consistency check (same action type → same interaction pattern)
- Usability check (primary actions reachable in ≤2 taps, destructive actions require confirmation)
- Accessibility compliance check (contrast, focus order, screen reader labels)
- **Gate**: downstream sub-phases (verify, ui-design) only proceed if gate passes

Output: `.allforai/experience-map/interaction-gate.json`

## Output Files (exit_requires)

All written to `.allforai/experience-map/`:
- `journey-emotion-map.json` (if consumer/mixed)
- `experience-map.json`
- `screen-conflict.json`
- `interaction-gate.json`

## Data Contract — What Downstream Nodes Pull

| Consumer | Pulls | Why |
|----------|-------|-----|
| product-analysis-verify | experience-map, interaction-gate | Needs screens for use-case tree + feature-gap screen coverage |
| ui-design | experience-map, journey-emotion-map | Needs screens + emotional context for design spec |
| implement / translate | experience-map | Needs screens, states, interactions to build UI |
| visual-verify | experience-map | Needs expected screens for screenshot comparison |

## Backtrack Triggers

**This node may backtrack to product-analysis-core when:**
- Screen references a role not in role-profiles → missing role
- Screen references a task not in task-inventory → missing task
- Flow in business-flows references a screen not mappable → incomplete flow

**Other nodes may trigger a backtrack to this node when:**
- **product-analysis-verify** finds use-cases that reference non-existent screens → missing screen
- **feature-gap** finds screen states not defined → incomplete experience-map
- **design-audit** finds interaction inconsistencies → gate needs re-evaluation

On re-execution: re-read product-map artifacts (may have been updated by core re-run),
regenerate affected experience-map artifacts, preserve unchanged files.

## Rules (Bootstrap Must Preserve)

1. **Journey-emotion before experience-map**: Emotional journey informs interaction expectations.
2. **Interaction gate is mandatory**: Must pass before downstream phases begin.
3. **Exception mapping**: Every screen has empty/error/permission states.
4. **Button-level exception flows**: Every operation has on_failure, validation_rules.
5. **Consumer maturity bar**: Consumer/mixed products evaluated against mature product standards.
6. **Conflict detection**: Screen-level conflicts surface here (complementary to core's task-level detection).
7. **Required downstream fields**: experience_priority, protection_level, audience_type, render_as must propagate from core artifacts.

## Non-Web-App Archetypes

| Archetype | Journey-emotion | Experience-map | Interaction gate |
|-----------|----------------|----------------|-----------------|
| CLI | Skip | Skip (no UI) | Skip |
| Data pipeline | Skip | Skip | Skip |
| Game server | Optional (player experience) | Game UI screens if exists | Skip |
| Library/SDK | Skip | Skip | Skip |

For CLI/pipeline/library, this entire node is skipped. Bootstrap does not generate it.

## Composition Hints

### Single Node (default)
One node for most projects. All 3 sub-phases run sequentially.

### Split by Platform
Multi-platform projects with very different UX: product-analysis-ux-mobile, product-analysis-ux-web.

### Skip
No frontend → skip entirely. CLI / data pipeline / library → skip.

### Merge
Very simple projects: merge with product-analysis-core into a single node.
