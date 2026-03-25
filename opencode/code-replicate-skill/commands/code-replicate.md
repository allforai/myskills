---
name: code-replicate
description: "Code replication: reverse-engineer existing codebase -> generate allforai artifacts -> hand off to dev-forge pipeline. Modes: interface / functional / architecture / exact"
version: "2.1.0"
---

# Code Replicate — Code Replication

## Parameters

Infer from the user's natural language request:

| Parameter | Format | Description |
|-----------|--------|-------------|
| `mode` | positional #1 | interface / functional / architecture / exact |
| `path` | positional #2 | Local path or Git URL |
| `--type` | backend / frontend / fullstack / module | Project type (default: auto-detect) |
| `--scope` | full / modules / feature / free text | Analysis scope |
| `--module` | path | Module path for module-level replication |
| `--from-phase` | 1-4 | Resume from specified phase (preserves earlier artifacts) |

### Git URL Support

Supports the following formats, with optional `#branch` suffix:

- HTTPS: `https://github.com/org/repo.git`
- SSH: `git@github.com:org/repo.git`
- GitHub shorthand: `org/repo` (auto-expands to `https://github.com/org/repo.git`)
- Branch/Tag: `https://github.com/org/repo#v2.0`

When a Git URL is detected, clone to a temporary directory before analysis.

## Missing Parameter Guidance

When the user's request is missing required parameters, ask naturally in a single consolidated question:

1. **Source path** (if missing): "Where is the source code you want to replicate?" Options: current directory `.` / local path / Git URL
2. **Fidelity level** (if missing): "What level of replication do you need?" Options: interface (API contracts only) / functional (business logic, recommended) / architecture (with architecture analysis) / exact (100% including bugs)
3. **Project type** (if missing and cannot auto-detect): "What type of project is this?" Options: backend / frontend / fullstack / auto-detect (recommended)

Collect all missing parameters in one question, then proceed.

## Project Type Auto-Detection

When `--type` is not specified, scan the codebase:

- **backend**: routes/controllers/middleware/models directories or files
- **frontend**: components/pages/store/hooks/screens directories or files
- **fullstack**: frontend and backend code coexist (monorepo or fullstack framework)
- **module**: requires explicit `--type module --module <path>`

## Skill Dispatch

Based on project type, load the corresponding skill file and execute its full workflow:

1. **backend** (or auto-detected as backend) -> load `./skills/cr-backend.md`
2. **frontend** (or auto-detected as frontend) -> load `./skills/cr-frontend.md`
3. **fullstack** (or auto-detected as fullstack) -> load `./skills/cr-fullstack.md`
4. **module** -> load `./skills/cr-module.md` (requires `--module` parameter)

All skill files internally load `./skills/code-replicate-core.md` as the 4-phase protocol foundation.

## Shortcut Equivalents

| Shortcut | Equivalent |
|----------|-----------|
| `cr-backend` | `code-replicate --type backend` |
| `cr-frontend` | `code-replicate --type frontend` |
| `cr-fullstack` | `code-replicate --type fullstack` |
| `cr-module` | `code-replicate --type module` |
| `cr-interface` | `code-replicate interface` |
| `cr-exact` | `code-replicate exact` |

## Quick Reference

```
code-replicate                                      # Interactive guided
code-replicate functional ./src                     # Backend replicate business behavior (auto-detect type)
code-replicate functional ./src --type frontend     # Frontend replicate business behavior
code-replicate functional ./src --type fullstack    # Fullstack replicate (cross-layer validation)
code-replicate functional ./src --scope "user registration and login"  # Replicate specific feature
code-replicate interface ./src                      # Replicate API contracts only
code-replicate exact ./src                          # 100% replication (including bugs)
code-replicate functional https://github.com/org/repo.git      # Remote repo
code-replicate functional https://github.com/org/repo#v2.0     # Specify branch/tag
code-replicate functional git@github.com:org/repo.git           # SSH address
code-replicate functional org/repo                              # GitHub shorthand
code-replicate functional ./src --type module --module src/user # Module replicate
code-replicate --from-phase 3                                   # Resume from Phase 3
```

## Fidelity Quick Reference

| Level | Use Case |
|-------|----------|
| `interface` | Backend rewrite, frontend unchanged; API-compatible migration |
| `functional` | Tech stack migration, preserving business logic (**recommended default**) |
| `architecture` | Large-scale refactoring, preserving architectural decisions |
| `exact` | Zero-tolerance behavioral regression; regulatory compliance |

## Next Steps

After replication analysis completes, continue with the dev-forge pipeline:

```
code-replicate   ->  Reverse analysis, generate .allforai/ artifacts
    |
project-setup    ->  Initialize target project based on artifacts
    |
design-to-spec   ->  Generate target tech stack implementation specs
    |
task-execute     ->  Generate code task by task
```
