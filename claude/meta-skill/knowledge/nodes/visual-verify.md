# Visual Verify Node Template

> Screenshot-based UI comparison between source and target apps.

## Purpose

Capture screenshots of source and target apps, compare per-screen,
identify layout/style/content discrepancies, fix in repair loop.

## Sub-Agent Architecture

- capture agent: screenshot collection (source + target)
- structural agent: layout/style comparison per screen
- data-integrity agent: data content verification
- linkage agent: navigation/link validation
- report agent: scoring + report generation
- repair agent: code fixes for visual discrepancies

## Protocol

1. Capture: source + target screenshots per screen per role
2. Plan: enumerate comparison subtasks
3. Execute: parallel per-screen (structural + data + linkage)
4. Report: aggregate scores
5. Repair loop: fix -> re-capture -> re-compare (max 30 rounds)

## Modes

| Mode | What |
|------|------|
| `full` | capture -> compare -> report -> repair loop |
| `analyze` | capture -> compare -> report (no code changes) |
| `fix` | repair from last report (no re-capture) |

## Rules

1. **Real screenshots only**: No DOM manipulation for state setup. ViewModel calls OK, direct DOM changes forbidden.
2. **Platform adaptation exclusion**: Differences matching stack-mapping.platform_adaptation are not_a_gap.
3. **Multi-role**: role-view-matrix.json triggers per-role comparison.
4. **5-layer validation**: Static page, CRUD states, dynamic effects, API logs, composite milestones.
5. **Data injection tiers**: User interaction > ViewModel call > Network mock > UNREACHABLE.
6. **Pre-condition**: Visual verify runs last — after cr-fidelity + product-verify + testforge all pass.
7. **Encoding**: All output files must use UTF-8. JSON with `ensure_ascii=False`. Scrub GBK mojibake on read-back.
8. **Linkage verify**: If interaction-recordings.json exists, execute same business flow chains (not just screenshots).

## Phases

### Phase A: Screenshot Capture

- Dynamic screens inject minimal test data via ViewModel (not test account presets)
- Source and target both captured; both missing = error; source only missing = CAPTURE_UNAVAILABLE compensation
- Capture per screen per role (from experience-map.json, route-map.json, replicate-config.json)

### Phase B: Task Planning

Explicit comparison task list generated before execution (no direct jump to compare).

### Phase C: Parallel Comparison

Per-screen agents run in parallel:
- Structural: layout hierarchy, element positions, color/typography
- Data integrity: actual data values, empty/loading/error states
- Linkage: navigation targets, action handlers (when interaction-recordings.json present)

### Phase D: Report + Repair

- Aggregate per-screen scores into composite visual fidelity score
- `full` mode: auto-repair -> re-capture -> re-compare until convergence (max 30 rounds)

## What Bootstrap Specializes

- Screenshot capture method per platform (XCUITest, Espresso, Playwright)
- App startup commands + URLs
- Role credentials for multi-role screenshots
- Platform adaptation rules from stack-mapping
