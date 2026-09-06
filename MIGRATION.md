# Migration Guide

## megastorm renamed to superstorm (2026-09-06)

The plugin, its skill, and both platform directories are now `superstorm`: `claude/superstorm`
(skills `/superstorm`, `/cross-exam`, `/product-review`) and `codex/superstorm-skill`. The name
mirrors `grillstorm`: grill → Matt Pocock's official skills as the design front end, super →
superpowers brainstorming. It also stops colliding with `meta-skill` in the `/me` completion.

- Claude Code: `claude plugin uninstall megastorm@myskills`, then
  `claude plugin marketplace add /path/to/myskills/claude/superstorm` and
  `claude plugin install superstorm@superstorm`; restart `claude`.
- Codex: repoint `~/.codex/skills/superstorm` at `myskills/codex/superstorm-skill` and remove the
  old `megastorm` symlink.
- Env vars are `SUPERSTORM_CODEX_COMMAND` / `SUPERSTORM_CODEX_WRAPPER_CONTRACT`; the
  `MEGASTORM_*` spellings are still read as a fallback.
- Runs recorded before the rename keep their `megastorm-registry` overview markers, commit
  trailers (`megastorm-confirmed:`), and `refs/megastorm/runs/*` refs. New runs use the
  `superstorm` spellings; resuming an old Codex run under the new scripts is not supported.
- Historical design docs under `docs/superpowers/` and `docs/validation/` keep the old name.

## Codex layer skills retired

The six Codex standalone packs are gone:

- `codex/product-design-skill`
- `codex/dev-forge-skill`
- `codex/demo-forge-skill`
- `codex/code-tuner-skill`
- `codex/code-replicate-skill`
- `codex/ui-forge-skill`

Those jobs now go through `codex/meta-skill` (`bootstrap` → `.codex/commands/run.md` / `.allforai/codex/flow.py`), same install surface as Claude: meta-skill + superstorm + grillstorm. Codex also still ships standalone `cross-exam`.

If `$CODEX_HOME/skills` still points at a deleted pack, remove that symlink.

**Follow-up (not in this cut):** the old `/review` hub (`review_hub_server.py:18900`) was not migrated into meta-skill. The shared copy remains at `shared/scripts/product-design/review_hub_server.py` if someone later wants to wire it.

The 37-type / MG-CT interaction catalog is retired. Do not assign screens from that list.

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
├── demo-forge-skill/           │   ├── superstorm/
├── code-tuner-skill/           │   └── grillstorm/
├── code-replicate-skill/       ├── codex/
├── ui-forge-skill/             │   ├── meta-skill/
├── codex-native/               │   ├── superstorm-skill/
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

claude plugin marketplace add /path/to/myskills/claude/superstorm
claude plugin install superstorm@superstorm
```

### Codex Users

Link `SKILL.md` packages into `$CODEX_HOME/skills` (default `~/.codex/skills`):
`codex/meta-skill`, `codex/superstorm-skill`, `codex/cross-exam-skill`, `codex/grillstorm`.

## Breaking Changes

| Affected | Change | User Action |
|----------|--------|-------------|
| Claude Code | Plugin path moved into `claude/` subdirectory | `claude plugin marketplace add` + `install <name>@<marketplace>` |
| Codex | Layer packs removed; meta-skill is the only layer entry | Relink `$CODEX_HOME/skills/meta-skill` and drop old pack symlinks |
| OpenCode | Platform support removed | Stop using `opencode/install.sh` / `install-remote.sh` |
