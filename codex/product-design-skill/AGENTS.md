# AGENTS.md — Product Design Suite (Layer 0 Entry)

> Codex-native orchestration layer for product-design-skill.

## Sub-Skills

| # | Skill | File | Purpose |
|---|-------|------|---------|
| 1 | product-concept | ./skills/product-concept.md | Discover product vision from scratch (search + choice-driven) or reverse-engineer from existing code |
| 1.6 | requirements | ./skills/requirements.md | Progressive requirements confirmation: Stage A (core paths) → Stage B (standard modules) → Stage C (boundary decisions). Auto-triggered after product-concept; also runnable as /requirements |
| 2 | product-map | ./skills/product-map.md | Map roles, tasks, business flows, constraints, data model, view objects (9 steps) |
| 3 | journey-emotion | ./skills/journey-emotion.md | Annotate emotion/intensity/risk/design-hint per business-flow node (human decision point) |
| 4 | experience-map | ./skills/experience-map.md | LLM-designed screens with operation_lines > nodes > screens structure + validation loop |
| 4.5 | interaction-gate | ./skills/interaction-gate.md | 4-dimension usability scoring per operation line; gate before UI design |
| 5 | use-case | ./skills/use-case.md | Derive happy/exception/boundary/e2e use cases in JSON + Markdown dual format |
| 6 | feature-gap | ./skills/feature-gap.md | Detect missing features, broken journeys, state machine gaps |
| 7 | ui-design | ./skills/ui-design.md | Generate UI design spec + tokens + HTML previews from product-map + experience-map |
| 8 | design-audit | ./skills/design-audit.md | Cross-layer consistency audit: trace + coverage + cross-check + pattern + behavioral |

## Orchestration

### Full Pipeline

Described in: `./commands/product-design.md`

```
Phase 0: artifact detection
Phase 1: product-concept (optional, skippable)
Phase 1.6: requirements confirmation (auto — Stage A→B→C, outputs requirements-brief.json)
Phase 2: product-map
Phase 3: journey-emotion
Phase 4: experience-map + interaction-gate
Phase 5: feature-gap
Phase 6: design-audit (final audit)
```

Modes:
- **full** — run all phases from start; skip concept with `skip: concept`
- **resume** — detect completed phases, continue from first incomplete

Auto-mode activates when `product-concept.json` contains `pipeline_preferences` field. In auto-mode, only ERROR-level issues pause for user input; WARNING/INFO are logged and auto-continued.

### Parallel Execution (Phases 4-7 in full pipeline context)

When running the full pipeline, phases 5 (use-case), 6 (feature-gap), and 7 (ui-design) can execute in parallel after experience-map + interaction-gate complete. See `./execution-playbook.md` for the 10-phase pipeline detail.

### Skip / Resume

Resume mode checks `.allforai/` artifact presence:

| Phase | Completion marker |
|-------|-------------------|
| 1 concept | `.allforai/product-concept/` exists |
| 1.6 requirements | `.allforai/product-concept/requirements-brief.json` exists AND `confirmed_status` != `"pending"` |
| 2 product-map | `.allforai/product-map/task-inventory.json` exists, task count > 0 |
| 3 journey-emotion | `.allforai/experience-map/journey-emotion-map.json` exists |
| 4 experience-map | `.allforai/experience-map/experience-map.json` exists, screen count > 0 |
| 4.5 interaction-gate | `.allforai/experience-map/interaction-gate.json` exists |
| 5 feature-gap | `.allforai/feature-gap/gap-tasks.json` exists |
| 6 design-audit | `.allforai/design-audit/audit-report.json` exists |

## Setup

Described in: `./commands/setup.md`

One-stop detection and configuration of all external capabilities:
- **OpenRouter** (cross-model XV + image generation)
- **Google AI** (Imagen 4 / Veo 3.1 / TTS)
- **fal.ai** (FLUX 2 Pro / Kling)
- **Brave Search** (media search)
- **Playwright** (UI automation)
- **Stitch UI** (high-fidelity visual generation)

All external capabilities are optional. Core skills work without them.

Modes: (no args) full guided setup | `check` status dashboard | `reset` reconfigure | `update` update all plugins/MCP/skills

## Review Hub

Described in: `./commands/review.md`

Unified review site at `http://localhost:18900/` with 6 tabs:
- Concept (mindmap)
- Map (mindmap: roles/tasks/flows)
- Data Model (mindmap: entities/APIs/VOs)
- Wireframe (tree + preview panel)
- UI (tree + preview panel)
- Spec (mindmap: dev specs)

Modes: `start` (launch) | `process` (read all feedback) | `process <tab>` (process specific tab)

## Key Documents

| Document | Path | Purpose |
|----------|------|---------|
| Design principles | ./docs/product-design-principles.md | First-principles, JTBD, Kano, Nielsen, WCAG theory |
| Skill commons | ./docs/skill-commons.md | Shared protocols: 4D+6V+XV, upstream baseline, external capability detection |
| Defensive patterns | ./docs/defensive-patterns.md | Load validation, zero-result handling, scale adaptation |
| Interaction types | ./docs/interaction-types.md | 37 interaction type definitions (MG/CT/EC/WK/RT/SB/SY/TU) |
| Schemas | ./docs/schemas/*.md | JSON output schemas for all artifacts |

## Output Contract

All artifacts write to project-local `.allforai/` directory. JSON files are machine-readable (complete fields, for AI agents and automation); Markdown `*-report.md` files are human-readable summaries. Never duplicate JSON content in Markdown.

## Experience Priority

When the product includes consumer/mobile surfaces, `product-map` outputs an `experience_priority` field (`consumer` / `admin` / `mixed`). All downstream skills inherit this field and switch design/validation standards accordingly. Consumer/mixed products must meet mature product standards, not just "feature exists".
