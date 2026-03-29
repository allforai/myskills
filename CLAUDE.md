# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

This is **myskills** — a tri-platform (Claude Code / Codex / OpenCode) plugin collection covering the full pipeline from product design → development forge → QA validation → architecture governance. It is a **plugin development repository**, not a product codebase. The plugins are applied to external user projects.

## Directory Structure

```
myskills/
├── claude/                   # Claude Code platform
│   ├── meta-skill/           # Unified meta-skill (replaces 6 static plugins)
│   │   ├── .claude-plugin/   # Plugin + marketplace manifests
│   │   ├── skills/           # bootstrap.md (project analysis + generation)
│   │   └── knowledge/        # Capability templates, orchestrator, protocols
│   └── install.sh
│
├── codex/                    # Codex platform (fully native)
│   ├── product-design-skill/ # AGENTS.md entry + execution-playbook
│   ├── ...
│   └── install.sh
│
├── opencode/                 # OpenCode platform (fully native)
│   ├── product-design-skill/ # SKILL.md entry + execution-playbook
│   ├── ...
│   └── install.sh
│
├── shared/                   # Platform-agnostic assets
│   ├── scripts/
│   │   ├── product-design/   # Python data transform scripts
│   │   └── code-replicate/   # Python reverse-engineering scripts
│   └── mcp-ai-gateway/       # Unified MCP gateway (Node)
│
├── CLAUDE.md                 # This file
└── MIGRATION.md              # Migration guide from old structure
```

## Four-Layer Architecture

```
All capabilities are now unified under **meta-skill** — a single plugin that generates
project-specific node-specs and orchestrator configs via `/bootstrap`, then executes them via `/run`.

The four original layers (product-design, dev-forge, demo-forge, code-tuner) plus
code-replicate and ui-forge are preserved as capability templates in
`claude/meta-skill/knowledge/capabilities/`.
```

## Claude Meta-Skill Structure

```
claude/meta-skill/
├── .claude-plugin/
│   ├── plugin.json          # Plugin manifest
│   └── marketplace.json     # Marketplace listing
├── skills/
│   └── bootstrap.md         # Project analysis + node-spec generation
├── knowledge/
│   ├── capabilities/        # 15 capability templates (discovery, translate, tune, etc.)
│   ├── orchestrator-template.md  # Template for generating run.md
│   ├── diagnosis.md         # Full-chain diagnosis protocol
│   ├── learning-protocol.md # Cross-session learning
│   ├── feedback-protocol.md # Anonymous feedback submission
│   └── safety.md            # Default safety configuration
└── commands/
    └── bootstrap.md         # /bootstrap slash command
```

User workflow: `/bootstrap` analyzes the target project → generates `.allforai/bootstrap/` (state-machine.json + node-specs) → `/run <goal>` executes the generated workflow.

## Shared Data Contract: `.allforai/`

All plugins read/write to a project-local `.allforai/` directory. This is the inter-plugin data bus. **product-design must run first**; downstream plugins depend on its output.

```
.allforai/
├── product-map/             # role-profiles, task-inventory, task-index, business-flows, constraints
├── experience-map/          # journey-emotion-map, experience-map, interaction-gate
├── use-case/                # use-case-tree (JSON, machine), use-case-report (Markdown, human)
├── feature-gap/             # task-gaps, screen-gaps, journey-gaps, gap-tasks, gap-report
├── feature-prune/           # frequency-tier, prune-decisions, prune-tasks, prune-report
├── design-audit/            # audit-report (JSON + Markdown)
├── ui-design/               # ui-design-spec.md + preview/*.html (per-role HTML previews)
├── seed-forge/              # seed-plan, forge-data, assets/ (dev seed data)
├── demo-forge/              # demo-plan, forge-data, assets/, verify-report, round-history
├── product-verify/          # static-report, dynamic-report, verify-report
├── deadhunt/                # validation-profile, static-analysis/, tests/, fix-tasks
└── code-tuner/              # tuner-profile, phase1-4 JSONs, tuner-report, tuner-tasks
```

**Output contract**: JSON files are machine-readable (complete fields, for AI agents and automation); Markdown `*-report.md` files are human-readable summaries. Never duplicate JSON content in Markdown.

## Installing Plugins

```bash
# Claude Code
bash claude/install.sh

# Codex
bash codex/install.sh

# OpenCode
bash opencode/install.sh
```

## Key Dependency: mcp-ai-gateway

`shared/mcp-ai-gateway/` provides OpenRouter (cross-model XV + image gen) + Google AI (Imagen 4 / Veo 3.1 / TTS) + fal.ai (FLUX 2 Pro / Kling) in a single process:

```bash
cd shared/mcp-ai-gateway
npm install
npm run build        # produces dist/index.js
```

Requires `OPENROUTER_API_KEY` for cross-model queries and image generation. Optionally `GOOGLE_API_KEY` for Imagen 4/Veo 3.1/TTS, `FAL_KEY` for FLUX 2 Pro/Kling.

## External Service Keys

Four optional API keys enhance plugin capabilities. Configure all at once with `/setup`:

| Service | Env Variable | Used By | Purpose |
|---------|-------------|---------|---------|
| OpenRouter | `OPENROUTER_API_KEY` | product-design, demo-forge | Cross-model XV + image generation (GPT-5 Image) |
| Brave Search | `BRAVE_API_KEY` | demo-forge | Media search (images/videos) |
| Google AI | `GOOGLE_API_KEY` | demo-forge | Imagen 4 (image) + Veo 3.1 (video) + TTS |
| fal.ai | `FAL_KEY` | demo-forge | FLUX 2 Pro (image) + Kling (video) |

All services are optional — plugins work without them, skipping enhanced features.

## Prebuilt Python Scripts

Scripts in `shared/scripts/` are platform-agnostic data transform tools:

- `shared/scripts/product-design/` — product-map generation, experience-map, design-audit, etc.
- `shared/scripts/code-replicate/` — reverse-engineering discovery, merge, validation

Claude plugins also keep a copy in their own `scripts/` directory (since `${CLAUDE_PLUGIN_ROOT}` resolves to the plugin cache, not the repo source).

## Skill Development Conventions

- **Skill files** (`skills/*.md`) use YAML frontmatter with `name:` and `description:` fields. The description is the trigger text that determines when Claude invokes the skill.
- **Command files** (`commands/*.md`) define slash commands. They support YAML frontmatter for arguments and can include `AskUserQuestion` patterns for interactive flows.
- **`${CLAUDE_PLUGIN_ROOT}`** is the runtime variable resolving to the plugin's root directory. Use it in Claude skill files to reference sibling files.
- Skills reference sub-documents with `> 详见 ${CLAUDE_PLUGIN_ROOT}/docs/xxx.md` — these are loaded on demand, not eagerly.

## Platform-Specific Notes

| Aspect | Claude Code | Codex | OpenCode |
|--------|------------|-------|----------|
| Entry point | SKILL.md (plugin auto-load) | AGENTS.md | skills.json → SKILL.md |
| Interaction | AskUserQuestion (structured) | Assume + declare | Natural conversation |
| Tools | `${CLAUDE_PLUGIN_ROOT}` paths | Relative paths | Relative paths |
| MCP naming | `mcp__plugin_{name}_{server}__*` | Generic descriptions | `mcp__{server}__*` |

## Recommended Workflow (for users of the plugins)

```
/product-concept          # Discover product vision (optional, from scratch)
    ↓
/review                   # Unified review hub (http://localhost:18900/) — concept tab
    ↓
/product-map              # Build product map (always first if no concept)
    ↓
/journey-emotion          # Emotion journey mapping (human decision point)
    ↓
/experience-map           # Experience map
    ↓
/use-case / /feature-gap / /feature-prune / /ui-design   # Any order
    ↓
/design-audit             # Final cross-layer consistency check
    ↓
/design-to-spec           # Convert design artifacts to dev specs
/task-execute             # Execute tasks with progress tracking
    ↓
/demo-forge               # Demo-ready data with multi-round iteration
    ↓
/deadhunt / /fieldcheck / /code-tuner   # Quality checks
```

Or run `/product-design full` / `/project-forge full` / `/demo-forge` for automated end-to-end orchestration.
