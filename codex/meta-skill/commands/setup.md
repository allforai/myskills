---
description: "Detect and configure optional external capabilities for the Codex meta-skill adapter."
---

# Setup — Codex External Capability Management

## Path Convention

All paths are relative to `codex/meta-skill/`.

## Modes

- no argument: full guided check and remediation
- `check`: status only
- `reset`: clear assumptions and re-evaluate from scratch
- `update`: rebuild local gateway and refresh install guidance
- `impact [from_ref]`: analyze meta-skill changes and recommend which current project nodes should be rerun

## Capability Model

Optional capabilities are grouped into three classes:

### MCP-backed tools

| Capability | Codex check | Purpose |
|------------|-------------|---------|
| browser automation | look for a Playwright-capable tool in the current session | UI verification and automation |
| Stitch UI | look for a Stitch-capable tool in the current session | high-fidelity visual generation |
| ai-gateway | `.mcp.json` present + `./mcp-ai-gateway/dist/index.js` exists | model gateway for search / image / model calls |

### API-key-backed services

| Capability | Env var |
|------------|---------|
| OpenRouter | `OPENROUTER_API_KEY` |
| Google AI | `GOOGLE_API_KEY` |
| fal.ai | `FAL_KEY` |
| Brave Search | `BRAVE_API_KEY` |

### Built-in fallback

| Capability | Fallback |
|------------|----------|
| search | Codex web/search capability |
| question flow | normal Codex user-question flow |

## Step 0: Build Check

Before checking keys, verify the gateway build:

1. Check `./mcp-ai-gateway/dist/index.js`
2. If missing:
   - run `cd ./mcp-ai-gateway && npm install`
   - run `cd ./mcp-ai-gateway && npm run build`
3. Report whether the build is ready

## Step 1: Status Dashboard

Report at least:

- gateway build status
- browser automation readiness
- Stitch readiness
- OpenRouter key readiness
- Google AI key readiness
- fal.ai key readiness
- Brave Search key readiness

Include downgrade guidance:

- no browser automation -> skip dynamic browser verification
- no Stitch -> use text-only visual specs
- no Brave Search -> use Codex web search or user-provided references
- no image/video services -> skip media generation enhancements

## Step 2: Remediation Guidance

If the user is in `check` mode, stop after the dashboard.

Otherwise:

- for missing gateway build: instruct or execute build steps
- for missing env vars: ask the user to provide or configure them
- for missing browser automation / Stitch: explain installation prerequisites and the degraded workflow

## Step 3: Update Impact Analysis

If the user is in `impact` mode, do not configure external services. Generate a rerun recommendation report for the current project.

Run from the current project root:

```bash
python3 <myskills_repo>/claude/meta-skill/scripts/orchestrator/analyze_skill_update_impact.py \
  --repo-root <myskills_repo> \
  --project-root . \
  --from-ref <from_ref> \
  --output-root .allforai/setup
```

If no `<from_ref>` is provided, still run the analyzer without `--from-ref`; the report will ask for a change source. If the repo is not a git checkout, pass one or more `--changed-file` arguments instead.

Required outputs:

```text
.allforai/setup/skill-update-impact.json
.allforai/setup/skill-update-impact.md
```

Use the report to decide whether to rerun `/bootstrap`, a specific node, a QA node, or a downstream handoff. Do not execute the rerun automatically from setup.

## Codex Interaction Rule

When the canonical Claude protocol uses `AskUserQuestion`, use the normal Codex question flow:

- ask only when the missing information blocks setup
- prefer a direct question over a Claude-specific UI instruction
