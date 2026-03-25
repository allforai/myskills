# Migration Guide — Multi-Platform Restructure

## What Changed

The repository has been reorganized from a single Claude Code plugin directory into three fully native platform directories. Each platform (Claude Code, Codex, OpenCode) now has its own complete, independently optimized copy of all 6 plugins.

```
BEFORE                          AFTER
myskills/                       myskills/
├── product-design-skill/       ├── claude/
├── dev-forge-skill/            │   ├── product-design-skill/
├── demo-forge-skill/           │   └── ...
├── code-tuner-skill/           ├── codex/
├── code-replicate-skill/       │   ├── product-design-skill/
├── ui-forge-skill/             │   └── ...
├── codex-native/               ├── opencode/
├── opencode-native/            │   ├── product-design-skill/
└── .claude-plugin/             │   └── ...
                                └── shared/
                                    ├── scripts/
                                    └── mcp-ai-gateway/
```

## Re-install Steps

### Claude Code Users

```bash
# Remove old plugins
claude plugin remove product-design
claude plugin remove dev-forge
claude plugin remove demo-forge
claude plugin remove code-tuner
claude plugin remove code-replicate
claude plugin remove ui-forge

# Re-install from new location
cd /path/to/myskills
bash claude/install.sh
```

### OpenCode Users

```bash
cd /path/to/myskills
bash opencode/install.sh
```

This overwrites `~/.config/opencode/skills.json` with updated paths.

### Codex Users

```bash
cd /path/to/myskills
bash codex/install.sh
```

Point Codex to the `codex/` directory. Each plugin has an `AGENTS.md` entry point.

### Remote Install Users

The old `install-remote.sh` has been removed. To update:

```bash
cd ~/.opencode/skills/myskills   # or wherever you cloned
git pull
bash opencode/install.sh         # or claude/install.sh or codex/install.sh
```

## Breaking Changes

| Affected | Change | User Action |
|----------|--------|-------------|
| Claude Code | Plugin path moved into `claude/` subdirectory | Re-run `claude/install.sh` |
| OpenCode | skills.json paths changed | Re-run `opencode/install.sh` |
| Codex | New directory structure with `AGENTS.md` entry | Run `codex/install.sh` |
| Remote users | `install-remote.sh` removed | `git pull` then re-run platform install |

## Version Bump

All plugins received a major version bump with this restructure:

| Plugin | Old Version | New Version |
|--------|-------------|-------------|
| product-design | 4.17.1 | 5.0.0 |
| dev-forge | 5.9.1 | 6.0.0 |
| demo-forge | 1.3.2 | 2.0.0 |
| code-tuner | 1.1.2 | 2.0.0 |
| code-replicate | 4.0.0 | 5.0.0 |
| ui-forge | 0.1.2 | 1.0.0 |
