# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

This is **myskills** — a Claude Code + OpenCode dual-platform plugin collection covering the full pipeline from product design → development forge → QA validation → architecture governance. It is a **plugin development repository**, not a product codebase. The plugins are applied to external user projects.

## Five-Layer Architecture

```
Layer         Plugin            Coverage
────────────  ────────────────  ─────────────────────────────────────────────
Product       product-design    concept→map→journey-emotion→experience-map→gate→ui→use-cases→gaps→prune→audit
Development   dev-forge         setup→spec→scaffold→execute→e2e→seed→verify
Demo          demo-forge        design→media→execute→verify→iterate
QA            deadhunt          dead links→CRUD completeness→ghost features→field consistency
Architecture  code-tuner        compliance→duplication→abstraction→scoring
```

Each plugin lives in its own subdirectory (`product-design-skill/`, `dev-forge-skill/`, `demo-forge-skill/`, `deadhunt-skill/`, `code-tuner-skill/`) and is independently installable.

## Plugin Structure (per plugin)

```
{plugin}-skill/
├── .claude-plugin/
│   ├── plugin.json          # Plugin manifest (name, version, description)
│   └── marketplace.json     # Marketplace listing
├── skills/                  # Skill definition files (*.md) — loaded by Claude on invocation
├── commands/                # Slash command definitions (*.md) — user-invocable
├── docs/                    # Design principles, guides, reference docs
├── templates/               # Tech stack templates (dev-forge only)
├── scripts/                 # Pre-built Python scripts for data transforms (product-design only)
└── SKILL.md                 # Root skill loaded when plugin is invoked
```

The `SKILL.md` in each plugin root is the entry point — it describes all sub-skills and links to them via `${CLAUDE_PLUGIN_ROOT}/skills/*.md`.

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

**Claude Code:**
```bash
claude plugin add /path/to/myskills/product-design-skill
claude plugin add /path/to/myskills/dev-forge-skill
claude plugin add /path/to/myskills/demo-forge-skill
claude plugin add /path/to/myskills/deadhunt-skill
claude plugin add /path/to/myskills/code-tuner-skill
```

**OpenCode (local dev):**
```bash
./install-opencode.sh   # writes ~/.config/opencode/skills.json
```

**OpenCode (remote/production):**
```bash
./install-remote.sh     # clones to ~/.opencode/skills/myskills and configures globally
```

After remote install, update with: `~/.opencode/skills/myskills/update-skills.sh`

## Key Dependency: mcp-ai-gateway

`product-design-skill/` bundles a unified AI Gateway MCP server at `mcp-ai-gateway/`. It provides OpenRouter (cross-model XV + image gen) + Google AI (Imagen 4 / Veo 3.1 / TTS) + fal.ai (FLUX 2 Pro / Kling) in a single process:

```bash
cd product-design-skill/mcp-ai-gateway
npm install
npm run build        # produces dist/index.js
```

Requires `OPENROUTER_API_KEY` for cross-model queries and image generation. Optionally `GOOGLE_API_KEY` for Imagen 4/Veo 3.1/TTS, `FAL_KEY` for FLUX 2 Pro/Kling. Config in `.allforai/openrouter-config.yaml`.

## External Service Keys

Four optional API keys enhance plugin capabilities. Configure all at once with `/setup`:

| Service | Env Variable | Used By | Purpose |
|---------|-------------|---------|---------|
| OpenRouter | `OPENROUTER_API_KEY` | product-design, demo-forge | Cross-model XV + image generation (GPT-5 Image) |
| Brave Search | `BRAVE_API_KEY` | demo-forge | Media search (images/videos) |
| Google AI | `GOOGLE_API_KEY` | demo-forge | Imagen 4 (image) + Veo 3.1 (video) + TTS |
| fal.ai | `FAL_KEY` | demo-forge | FLUX 2 Pro (image) + Kling (video) |

Degradation chains: Image: Imagen 4 → GPT-5 Image → FLUX 2 Pro → skip. Video: Veo 3.1 → Kling → skip.

All services are optional — plugins work without them, skipping enhanced features.

## Prebuilt Python Scripts (product-design)

Phases 3–7 of product-design have prebuilt transform scripts in `product-design-skill/scripts/`. They are invoked automatically when available; Claude falls back to LLM generation if they don't exist.

```bash
python3 product-design-skill/scripts/gen_xxx.py <BASE_PATH> [--mode auto]
```

Scripts: `gen_journey_emotion.py`, `gen_experience_map.py`, `gen_interaction_gate.py`, `gen_use_cases.py`, `gen_feature_gap.py`, `gen_feature_prune.py`, `gen_ui_design.py`, `gen_design_audit.py`. Shared utilities in `_common.py`.

## Skill Development Conventions

- **Skill files** (`skills/*.md`) use YAML frontmatter with `name:` and `description:` fields. The description is the trigger text that determines when Claude invokes the skill.
- **Command files** (`commands/*.md`) define slash commands. They support YAML frontmatter for arguments and can include `AskUserQuestion` patterns for interactive flows.
- **`${CLAUDE_PLUGIN_ROOT}`** is the runtime variable resolving to the plugin's root directory. Use it in skill files to reference sibling files.
- Skills reference sub-documents with `> 详见 ${CLAUDE_PLUGIN_ROOT}/docs/xxx.md` — these are loaded on demand, not eagerly.

## Two-Phase Index Loading (product-design)

For large products (400+ tasks), full JSON loading is expensive. Three lightweight index files enable on-demand loading:

| Index | Producer | Size |
|-------|----------|------|
| `task-index.json` | product-map Step 6 | ~4KB |
| `flow-index.json` | product-map Step 6 | ~2KB |
| `screen_index` (embedded) | experience-map Step 1 | ~3KB |

When indexes don't exist, skills fall back to full data loading (backward compatible).

## Recommended Workflow (for users of the plugins)

```
/product-concept          # Discover product vision (optional, from scratch)
    ↓
/concept-review           # Mind map review of product concept (mandatory)
    ↓
/product-map              # Build product map (always first if no concept)
    ↓
/map-review               # Mind map review of product map (mandatory)
    ↓
/journey-emotion          # Emotion journey mapping (human decision point)
    ↓
/experience-map           # Experience map (replaces screen-map)
    ↓
/wireframe-review         # Low-fi structural review (structure lock gate)
    ↓
/use-case / /feature-gap / /feature-prune / /ui-design   # Any order (after structure lock)
    ↓
/ui-review                # High-fi visual review
    ↓
/design-audit             # Final cross-layer consistency check
    ↓
/design-to-spec           # Convert design artifacts to dev specs
/project-scaffold         # Generate project skeleton
/task-execute             # Execute tasks with progress tracking
    ↓
/seed-forge               # Generate dev seed data (minimal, for development)
/product-verify           # Static + dynamic acceptance
    ↓
/demo-forge               # Demo-ready data: design→media→execute→verify→iterate
/demo-forge verify        # Playwright verification with multi-round iteration
    ↓
/deadhunt                 # Dead link and CRUD completeness check
/code-tuner               # Architecture quality analysis
```

Or run `/product-design full` / `/project-forge full` / `/demo-forge` for automated end-to-end orchestration.
