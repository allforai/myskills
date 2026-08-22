# Migration Guide

## OpenCode support removed

OpenCode is no longer a supported platform. The `opencode/` tree, `install-opencode.sh`,
`install-remote.sh`, and `.opencode.template` are gone. Existing clones that still have a
local OpenCode install under `~/.config/opencode` or `~/.opencode/skills/myskills` are
outside this repo; uninstall those yourself if you no longer need them.

This repository now ships two native platform directories: `claude/` and `codex/`.

## What Changed (earlier multi-platform restructure)

The repository was reorganized from a single Claude Code plugin directory into native
platform directories. Each remaining platform (Claude Code, Codex) has its own complete,
independently optimized copy of the plugins.

```
BEFORE                          AFTER
myskills/                       myskills/
├── product-design-skill/       ├── claude/
├── dev-forge-skill/            │   ├── product-design-skill/
├── demo-forge-skill/           │   └── ...
├── code-tuner-skill/           ├── codex/
├── code-replicate-skill/       │   ├── product-design-skill/
├── ui-forge-skill/             │   └── ...
├── codex-native/               └── shared/
├── opencode-native/                ├── scripts/
└── .claude-plugin/                 └── mcp-ai-gateway/
```

## Re-install Steps

### Claude Code Users

Remove the old plugin names (`product-design`, `dev-forge`, …), then install from the
new marketplaces with Claude's own CLI:

```text
claude plugin marketplace add /path/to/myskills/claude/meta-skill
claude plugin install meta-skill@meta-skill

claude plugin marketplace add /path/to/myskills/claude/megastorm
claude plugin install megastorm@megastorm
```

### Codex Users

Link `SKILL.md` packages into `$CODEX_HOME/skills` (default `~/.codex/skills`):
`codex/meta-skill`, `codex/megastorm-skill`, `codex/cross-exam-skill`, `codex/grillstorm`.
Point Codex at a `codex/*-skill` directory to pick up that plugin's `AGENTS.md`.

## Breaking Changes

| Affected | Change | User Action |
|----------|--------|-------------|
| Claude Code | Plugin path moved into `claude/` subdirectory | `claude plugin marketplace add` + `install <name>@<marketplace>` |
| Codex | New directory structure with `AGENTS.md` / `SKILL.md` | Place skills under `~/.codex/skills` |
| OpenCode | Platform support removed | Stop using `opencode/install.sh` / `install-remote.sh` |

## Version Bump

All plugins received a major version bump with the original restructure:

| Plugin | Old Version | New Version |
|--------|-------------|-------------|
| product-design | 4.17.1 | 5.0.0 |
| dev-forge | 5.9.1 | 6.0.0 |
| demo-forge | 1.3.2 | 2.0.0 |
| code-tuner | 1.1.2 | 2.0.0 |
| code-replicate | 4.0.0 | 5.0.0 |
| ui-forge | 0.1.2 | 1.0.0 |
