# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

This is **myskills** — a Claude Code + OpenCode dual-platform plugin collection covering the full pipeline from product design → development forge → QA validation → architecture governance. It is a **plugin development repository**, not a product codebase. The plugins are applied to external user projects.

## Four-Layer Architecture

```
Layer         Plugin            Coverage
────────────  ────────────────  ─────────────────────────────────────────────
Product       product-design    concept→map→screens→ui→use-cases→gaps→prune→audit
Development   dev-forge         setup→spec→scaffold→execute→e2e→seed→verify
QA            deadhunt          dead links→CRUD completeness→ghost features→field consistency
Architecture  code-tuner        compliance→duplication→abstraction→scoring
```

Each plugin lives in its own subdirectory (`product-design-skill/`, `dev-forge-skill/`, `deadhunt-skill/`, `code-tuner-skill/`) and is independently installable.

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
├── screen-map/              # screen-map, screen-index, screen-conflict
├── use-case/                # use-case-tree (JSON, machine), use-case-report (Markdown, human)
├── feature-gap/             # task-gaps, screen-gaps, journey-gaps, gap-tasks, gap-report
├── feature-prune/           # frequency-tier, prune-decisions, prune-tasks, prune-report
├── design-audit/            # audit-report (JSON + Markdown)
├── ui-design/               # ui-design-spec.md + preview/*.html (per-role HTML previews)
├── seed-forge/              # seed-plan, forge-data, assets/
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

## Key Dependency: mcp-openrouter

`product-design-skill/` bundles a TypeScript MCP server at `mcp-openrouter/`. It must be built before the plugin can use multi-model queries:

```bash
cd product-design-skill/mcp-openrouter
npm install
npm run build        # produces dist/index.js
```

Requires `OPENROUTER_API_KEY` environment variable. Config in `.allforai/openrouter-config.yaml`.

## Prebuilt Python Scripts (product-design)

Phases 4–8 of product-design have prebuilt transform scripts in `product-design-skill/scripts/`. They are invoked automatically when available; Claude falls back to LLM generation if they don't exist.

```bash
python3 product-design-skill/scripts/gen_xxx.py <BASE_PATH> [--mode auto]
```

Scripts: `gen_use_cases.py`, `gen_feature_gap.py`, `gen_feature_prune.py`, `gen_ui_design.py`, `gen_design_audit.py`, `gen_screen_map_split.py`. Shared utilities in `_common.py`.

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
| `screen-index.json` | screen-map Step 1 | ~3KB |

When indexes don't exist, skills fall back to full data loading (backward compatible).

## Recommended Workflow (for users of the plugins)

```
/product-map              # Always first
    ↓
/screen-map               # Required before most downstream skills
    ↓
/use-case / /feature-gap / /feature-prune / /ui-design   # Any order
    ↓
/design-audit             # Final cross-layer consistency check
    ↓
/design-to-spec           # Convert design artifacts to dev specs
/project-scaffold         # Generate project skeleton
/task-execute             # Execute tasks with progress tracking
    ↓
/seed-forge               # Generate seed data
/product-verify           # Static + dynamic acceptance
/deadhunt                 # Dead link and CRUD completeness check
/code-tuner               # Architecture quality analysis
```

Or run `/product-design full` / `/project-forge full` for automated end-to-end orchestration.
