# Migration Guide

## Codex layer skills retired

The six Codex standalone packs are gone:

- `codex/product-design-skill`
- `codex/dev-forge-skill`
- `codex/demo-forge-skill`
- `codex/code-tuner-skill`
- `codex/code-replicate-skill`
- `codex/ui-forge-skill`

Those jobs now go through `codex/meta-skill` (`bootstrap` → `.codex/commands/run.md` / `.allforai/codex/flow.py`), same install surface as Claude: meta-skill + megastorm + grillstorm. Codex also still ships standalone `cross-exam`.

If `$CODEX_HOME/skills` still points at a deleted pack, remove that symlink.

**Follow-up (not in this cut):** the old `/review` hub (`review_hub_server.py:18900`) was not migrated into meta-skill. The shared copy remains at `shared/scripts/product-design/review_hub_server.py` if someone later wants to wire it.

The 37-type interaction catalog moved to `claude/meta-skill/knowledge/interaction-types.md`.

## OpenCode support removed

OpenCode is no longer a supported platform. The `opencode/` tree, `install-opencode.sh`,
`install-remote.sh`, and `.opencode.template` are gone. Existing clones that still have a
local OpenCode install under `~/.config/opencode` or `~/.opencode/skills/myskills` are
outside this repo; uninstall those yourself if you no longer need them.

This repository now ships two native platform directories: `claude/` and `codex/`.

## What Changed (earlier multi-platform restructure)

The repository was reorganized from a single Claude Code plugin directory into native
platform directories.

```
BEFORE                          AFTER
myskills/                       myskills/
├── product-design-skill/       ├── claude/
├── dev-forge-skill/            │   ├── meta-skill/
├── demo-forge-skill/           │   ├── megastorm/
├── code-tuner-skill/           │   └── grillstorm/
├── code-replicate-skill/       ├── codex/
├── ui-forge-skill/             │   ├── meta-skill/
├── codex-native/               │   ├── megastorm-skill/
├── opencode-native/            │   ├── grillstorm/
└── .claude-plugin/             │   └── cross-exam-skill/
                                └── shared/
                                    ├── scripts/
                                    └── mcp-ai-gateway/
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

## Breaking Changes

| Affected | Change | User Action |
|----------|--------|-------------|
| Claude Code | Plugin path moved into `claude/` subdirectory | `claude plugin marketplace add` + `install <name>@<marketplace>` |
| Codex | Layer packs removed; meta-skill is the only layer entry | Relink `$CODEX_HOME/skills/meta-skill` and drop old pack symlinks |
| OpenCode | Platform support removed | Stop using `opencode/install.sh` / `install-remote.sh` |
