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
- `update`: refresh install guidance
- `impact [from_ref]`: analyze meta-skill changes and recommend which current project nodes should be rerun

## Capability Model

Optional capabilities are grouped into three classes:

### MCP-backed tools

| Capability | Codex check | Purpose |
|------------|-------------|---------|
| browser automation | look for a Playwright-capable tool in the current session | UI verification and automation |

### Agent CLIs

Cross-model validation needs no service of its own: hand the summary to another platform's agent CLI installed on this machine (`claude`, `grok`), or to a fresh-context sub-agent when there is none.

| Capability | Codex check | Purpose |
|------------|-------------|---------|
| image generation | Codex's own image generation (this harness) | the only image source; see game-art `image-generation-contract` |
| video generation | `command -v grok` + `grok --no-auto-update models` shows a login | the only video source; needs a plan with video and video not disabled by zero data retention |

### API-key-backed services

| Capability | Env var |
|------------|---------|
| OpenRouter | `OPENROUTER_API_KEY` |
| Google AI (Lyria music generation) | `GOOGLE_API_KEY` |

### Built-in fallback

| Capability | Fallback |
|------------|----------|
| search | Codex web/search capability |
| question flow | normal Codex user-question flow |

## Step 1: Status Dashboard

Report at least:

- browser automation readiness
- OpenRouter key readiness
- Google AI key readiness
- Grok CLI install and login readiness

Include downgrade guidance:

- no browser automation -> skip dynamic browser verification
- no Grok CLI -> video requests return `blocked_by_missing_video_cli`; there is no other video source

## Step 2: Remediation Guidance

If the user is in `check` mode, stop after the dashboard.

Otherwise:

- for missing env vars: ask the user to provide or configure them
- for missing browser automation: explain installation prerequisites and the degraded workflow

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
