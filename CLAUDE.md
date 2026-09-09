# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

This is **myskills** — a dual-platform (Claude Code / Codex) plugin collection covering the full pipeline from product design → development forge → QA validation → architecture governance. It is a **plugin development repository**, not a product codebase. The plugins are applied to external user projects.

## Directory Structure

```
myskills/
├── claude/                   # Claude Code platform
│   ├── meta-skill/           # Unified meta-skill (replaces 6 static plugins)
│   │   ├── .claude-plugin/   # Plugin + marketplace manifests
│   │   ├── skills/           # bootstrap/SKILL.md (project analysis + generation)
│   │   └── knowledge/        # Capability templates, orchestrator, protocols
│   ├── superstorm/
│   └── grillstorm/
│
├── codex/                    # Codex platform (fully native)
│   ├── meta-skill/           # AGENTS.md + SKILL.md adapter
│   ├── superstorm-skill/
│   ├── grillstorm/
│   └── cross-exam-skill/
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
│   └── bootstrap/SKILL.md   # Project analysis + node-spec generation
├── hooks/
│   ├── hooks.json           # PreToolUse Skill gate registration
│   └── user-only-skills.sh  # Refuses model-side calls to /bootstrap and /setup
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
├── discovery/               # source-summary.json, file-catalog.json, infrastructure-profile.json, reuse-assessment.json
├── product-concept/         # product-concept.json, concept-baseline.json, decision-journal.json
├── product-map/             # role-profiles, task-inventory, task-index, business-flows, constraints
├── experience-map/          # journey-emotion-map, experience-map, interaction-gate
├── use-case/                # use-case-tree (JSON, machine), use-case-report (Markdown, human)
├── feature-gap/             # gap-tasks.json, gap-report.md
├── feature-prune/           # prune-tasks.json, frequency-tier.json, prune-report.md
├── tech-spec/               # api-spec.json, db-schema.md, protocol-spec.md (from design-to-spec)
├── infra-design/            # infra-design.json, infra-design.md
├── security-design/         # security-design.json, security-design.md
├── data-architecture/       # data-architecture.json, data-architecture.md
├── design-audit/            # audit-report (JSON + Markdown)
├── ui-design/               # ui-design-spec.md, tokens.json, interaction-spec.md, preview/*.html
├── game-design/             # system-spec.json, config-schema.json, protocol-spec.md (game-specific generate-artifacts outputs)
├── generate-artifacts/      # cli/pipeline/service/sdk archetype artifacts (command-tree, dag-spec, etc.)
├── demo-forge/              # demo-plan.json, forge-data.json, verify-report.json (demo + integration testing)
├── product-verify/          # static-report, dynamic-report, verify-report, ui-helper-profile.json
├── spec-compliance/         # spec-compliance-report.json
├── pipeline-closure/        # pipeline-closure-report.json
├── security-verify/         # security-verify-report.json
├── quality-checks/          # deadhunt-report.json, fieldcheck-report.json (from quality-checks capability)
├── deadhunt/                # validation-profile, static-analysis/, tests/, fix-tasks
├── code-tuner/              # tuner-profile, phase1-4 JSONs, tuner-report, tuner-tasks
├── concept-acceptance/      # acceptance-report.json
├── runtime-smoke/           # smoke-report.json
├── visual-verify/           # visual-verify-report.json, screenshots/
├── test-verify/             # test-verify-report.json
├── translate/               # translation-manifest.json
├── launch-prep/             # competitive-research, compliance-checklist, launch-checklist
└── bootstrap/               # workflow.json, bootstrap-profile.json, plan-confirmation.json,
                             # plan-confirmation-journal.json, repair-authorizations.json,
                             # safety-quarantine.json, node-specs/, scripts/, learned/
```

**Output contract**: JSON files are machine-readable (complete fields, for AI agents and automation); Markdown `*-report.md` files are human-readable summaries. Never duplicate JSON content in Markdown.

## Installing Plugins

Follow each harness's own install surface. Do not use repo `install.sh` scripts.

**Claude Code** — each plugin dir is a marketplace; register then install:

```text
claude plugin marketplace add /path/to/myskills/claude/meta-skill
claude plugin install meta-skill@meta-skill

claude plugin marketplace add /path/to/myskills/claude/superstorm
claude plugin install superstorm@superstorm
```

Optional: `claude/grillstorm` → `grillstorm@grillstorm`. Restart `claude` after install.
Grillstorm requires official Matt Pocock skills (`grilling`, `to-spec`, `to-tickets`, `tdd`, `code-review`, …). If they are missing, it asks once and can install them via `scripts/install_official_skills.py`. It never calls official `implement`.

**Codex** — discover `SKILL.md` folders from `$CODEX_HOME/skills` (default `~/.codex/skills`):

```text
~/.codex/skills/meta-skill   →  myskills/codex/meta-skill
~/.codex/skills/superstorm    →  myskills/codex/superstorm-skill
~/.codex/skills/cross-exam   →  myskills/codex/cross-exam-skill
~/.codex/skills/grillstorm   →  myskills/codex/grillstorm
```

Do not install retired Codex layer packs (`product-design`, `dev-forge`, `demo-forge`, `code-tuner`, `code-replicate`, `ui-forge`). Those jobs go through `codex/meta-skill`.

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
| OpenRouter | `OPENROUTER_API_KEY` | meta-skill capabilities | Cross-model XV + image generation (GPT-5 Image) |
| Brave Search | `BRAVE_API_KEY` | demo-forge capability | Media search (images/videos) |
| Google AI | `GOOGLE_API_KEY` | demo-forge capability | Imagen 4 (image) + Veo 3.1 (video) + TTS |
| fal.ai | `FAL_KEY` | demo-forge capability | FLUX 2 Pro (image) + Kling (video) |

All services are optional — plugins work without them, skipping enhanced features.

## Prebuilt Python Scripts

Scripts in `shared/scripts/` are platform-agnostic data transform tools:

- `shared/scripts/product-design/` — product-map generation, experience-map, design-audit, etc.
- `shared/scripts/code-replicate/` — reverse-engineering discovery, merge, validation

Claude plugins also keep a copy in their own `scripts/` directory (since `${CLAUDE_PLUGIN_ROOT}` resolves to the plugin cache, not the repo source).

## Skill Development Conventions

- **Skill files** live at `skills/<name>/SKILL.md` and use YAML frontmatter with `name:` and `description:` fields. The description is the trigger text that determines when Claude invokes the skill. A flat `skills/<name>.md` still works as a user-typed `/name` but never enters the model's skill list, so do not use that layout.
- **Command files** (`commands/*.md`) define slash commands. They support YAML frontmatter for arguments and can include `AskUserQuestion` patterns for interactive flows.
- **`${CLAUDE_PLUGIN_ROOT}`** is the runtime variable resolving to the plugin's root directory. Use it in Claude skill files to reference sibling files.
- Skills reference sub-documents with `> 详见 ${CLAUDE_PLUGIN_ROOT}/docs/xxx.md` — these are loaded on demand, not eagerly.

## Platform-Specific Notes

| Aspect | Claude Code | Codex |
|--------|------------|-------|
| Entry point | SKILL.md (plugin auto-load) | AGENTS.md |
| Interaction | AskUserQuestion (structured) | Assume + declare |
| Tools | `${CLAUDE_PLUGIN_ROOT}` paths | Relative paths |
| MCP naming | `mcp__plugin_{name}_{server}__*` | Generic descriptions |

## Recommended Workflow (for users of the plugins)

```
/bootstrap                # Analyze the target project and generate the workflow
    ↓
/run <goal>               # Execute generated nodes (Codex: .codex/commands/run.md)
```

Product, implementation, demo, verify, and tune jobs are meta-skill capabilities, not standalone slash commands.

### Which entry for which situation

Every entry below is user-invoked only. Do **not** set `disable-model-invocation` on them: that drops the entry from the model's skill list entirely, and the user wants them listed. Instead each plugin ships `hooks/user-only-skills.sh`, a `PreToolUse` gate on the Skill tool that refuses model-side calls to these names; a user-typed `/name` is expanded by the CLI and never reaches the hook. Never start one yourself; if it fits, tell the user the command exists.

| Situation | Entry | Why this one |
|---|---|---|
| A project that must go from product design through implementation to verification (product concept, experience map, art, game design, verify nodes) | `/bootstrap` → `/run` | The only pipeline with the product-design capabilities and the `.allforai/` data bus |
| One large engineering goal to finish autonomously, decisions front-loaded, no product-design phase | `/superstorm` | superpowers brainstorming/plans as the design front end; artifacts under `docs/superpowers/` |
| Same goal shape, but design must follow Matt Pocock's official skills (grilling → to-spec → to-tickets → tdd → code-review) | `/grillstorm` | Official skills own design; Grillstorm owns routing, DAG, worktree execution, resume, handoff; artifacts under `docs/grillstorm/` |
| A finished delivery that may be fake-complete; independent evidence wanted | `/cross-exam` | Fresh-context probers gather evidence, deterministic report, records only, refuses to run unattended; user-declared journeys walked end-to-end and judged against an oracle |
| A finished product; is it useful and sellable for the jobs the user names | `/product-review` | Product-thinking critique, competitor comparison, advice only; same package as cross-exam, different protocol |

`/superstorm` and `/grillstorm` share the execution shape (front-loaded decisions, DAG, concurrent worktrees, supervision, resume); they differ only in the design front end. `/cross-exam` then `/product-review` is the natural order after any of the three: first "is it done", then "is it good".

## Agent skills

### Issue tracker

Issues live in GitHub Issues for `allforai/myskills` via `gh`. See `docs/agents/issue-tracker.md`.

### Triage labels

Default roles: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: root `CONTEXT.md` and `docs/adr/`. See `docs/agents/domain.md`.
