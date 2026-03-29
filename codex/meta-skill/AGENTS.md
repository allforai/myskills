# AGENTS.md — Meta-Skill Generator

> Codex-native entry for the meta-skill generator.
> Analyzes projects and generates project-specific workflow configurations.

## Commands

| # | Command | Purpose |
|---|---------|---------|
| 1 | bootstrap | Analyze project → generate node-specs + state-machine + /run command |

## How It Works

1. Run `bootstrap` on a target project
2. Bootstrap performs lightweight analysis (tech stack, modules, domain)
3. Generates project-specific node-specs in `.allforai/bootstrap/`
4. Generates orchestrator command (run.md) in project root
5. Use `run [goal]` to execute any workflow

## Generated Outputs

```
.allforai/bootstrap/
  bootstrap-profile.json    — project analysis
  state-machine.json        — nodes + safety + progress
  node-specs/*.md           — per-node subagent instructions
  scripts/                  — evaluation scripts
  protocols/                — diagnosis + learning + feedback
```

## Knowledge Base

Shared with Claude Code and OpenCode platforms:
- `knowledge/capabilities/` — 15 capability references
- `knowledge/mappings/` — tech stack mapping tables
- `knowledge/domains/` — business domain knowledge

## Entry Points

| Goal | Starting Capability |
|------|-------------------|
| New product | product-concept |
| Replicate existing code | discovery |
| Code governance | discovery + tune |
| Verification | product-verify / visual-verify |
