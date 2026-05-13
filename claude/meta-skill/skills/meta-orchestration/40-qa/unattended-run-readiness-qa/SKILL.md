---
name: meta-orchestration-40-qa-unattended-run-readiness-qa
description: Validate before /run that a workflow can execute unattended without human prompts, mid-run approval gates, missing tools, missing keys, hidden fallbacks, or unbounded long-task stops.
---

# Unattended Run Readiness QA Skill

> Internal sub-skill for meta-orchestration. Status: bundled,
> bootstrap-support, run-preflight.

## Overview

Validates whether the current project can run for hours without human
interruption. This skill does not execute product, art, frontend, or code work.
It moves stop conditions to `/bootstrap` or the beginning of `/run`, so a long
run either starts ready or fails early with a concrete blocker list.

The goal is sleep-safe execution: after product, art direction, and technology
framework choices are discussed and frozen, `/run` must not ask humans for
missing decisions. It may auto-repair, retry, or fail with evidence, but it must
not pause for approval, keys, tools, screenshots, MCP setup, model selection, or
runtime command discovery.

## Input Contract

Required:
- `.allforai/bootstrap/workflow.json`
- `.allforai/bootstrap/node-specs/`
- `.allforai/bootstrap/bootstrap-profile.json`
- `.allforai/bootstrap/scripts/validate_bootstrap.py`
- `.allforai/bootstrap/scripts/check_artifacts.py`

Optional:
- `.allforai/game-design/approval-records.json`
- `.allforai/app-design/approval-records.json`
- `.allforai/game-design/design/program-development-node-handoff.json`
- `.allforai/game-design/art-pipeline-config.json`
- `.allforai/bootstrap/runtime-env.json`
- `.allforai/visual-qa/visual-model-routing-report.json`
- `.claude/settings.json`
- project-local tool capability registries and environment reports.

## Output Contract

Writes:

```text
.allforai/bootstrap/unattended-run-readiness-spec.json
.allforai/bootstrap/unattended-run-readiness.json
.allforai/bootstrap/unattended-run-readiness.md
```

`unattended-run-readiness.json` must include:
- `status`: `ready | not_ready`
- `checked_at`
- `blockers[]`
- `warnings[]`
- `required_capabilities[]`
- `approval_gate_findings[]`
- `non_interactive_findings[]`
- `external_tool_findings[]`
- `fallback_findings[]`
- `long_task_findings[]`
- `recommended_pre_run_actions[]`

Allowed blocker codes:
- `pending_human_gate`
- `node_spec_allows_user_prompt`
- `missing_node_spec`
- `missing_workflow`
- `missing_bootstrap_validator`
- `missing_codex_cli`
- `missing_visual_model_route`
- `missing_mcp_image_batch`
- `missing_google_key`
- `missing_fal_key`
- `missing_runtime_command`
- `missing_playwright_or_engine_automation`
- `forbidden_completed_with_limits`
- `unexpanded_program_handoff`
- `missing_long_task_recovery`

## Invocation Contract

```json
{
  "skill": "meta-orchestration/unattended-run-readiness-qa",
  "mode": "preflight",
  "input_paths": {
    "workflow": ".allforai/bootstrap/workflow.json",
    "node_specs": ".allforai/bootstrap/node-specs",
    "bootstrap_profile": ".allforai/bootstrap/bootstrap-profile.json"
  },
  "output_root": ".allforai/bootstrap"
}
```

Supported modes: `bootstrap_spec`, `preflight`, `repair_check`.

## Bootstrap Responsibilities

Bootstrap must generate `.allforai/bootstrap/unattended-run-readiness-spec.json`
before writing `run.md`. The spec declares which capabilities are required by
the selected workflow, including:
- human gates that must already be approved or converted to final-only review;
- Codex CLI visual review requirements;
- Playwright, engine, or UI automation requirements;
- `mcp-image-batch` image generation requirements;
- Google/fal/OpenRouter/audio provider key requirements;
- LoRA dataset/training/runtime requirements when strict identity lock is used;
- runtime command, dev server, simulator, or engine launch requirements;
- long-task recovery policy and retry budgets;
- disallowed fallback states such as `COMPLETED_WITH_LIMITS` for production
  deliverables unless explicitly allowed by the project.

Bootstrap may report `not_ready`, but it must do so before `/run`. Do not let
the first blocker appear several hours into execution.

## Run Preflight Responsibilities

At the beginning of `/run`, execute the project-local readiness script before
starting any workflow node:

```bash
python3 .allforai/bootstrap/scripts/validate_unattended_readiness.py . --write-report
```

If the report status is `not_ready`, stop immediately and show the blocker
summary. Do not execute partial nodes, do not ask the user mid-run, and do not
silently weaken validation.

## Automatic Validation

The readiness check must reject:
- any selected human gate whose approval record is missing or not approved;
- any node-spec that permits `AskUserQuestion`, interactive approval, or
  runtime user prompts during execution;
- any node-spec missing from the workflow;
- visual QA workflows without Codex CLI or visual model routing;
- generated image workflows without a valid image provider or `mcp-image-batch`
  route when batch generation is required;
- audio workflows without required provider keys when audio generation is
  selected;
- runtime/frontend QA workflows without executable runtime commands,
  screenshots, or automation capability;
- strict identity/style lock workflows without LoRA adapter, dataset/training
  path, or explicit allowed fallback;
- production workflows that can complete with `COMPLETED_WITH_LIMITS` without
  an explicit project allowance;
- long tasks that do not define file-based handoff, polling, retry, timeout,
  and resume evidence.

## Repair Routing

Route blockers before `/run`:
- approval blockers -> review dashboard / discussion phase;
- missing tools -> `/setup check` or install task;
- missing keys -> `/setup` key configuration;
- missing runtime commands -> bootstrap runtime-env setup;
- unexpanded handoff -> re-bootstrap or program-development node expansion;
- forbidden fallback -> tighten project readiness spec or lower scope before
  running;
- missing long-task policy -> update the node-spec or child skill before
  executing.

## Completion Conditions

Return `COMPLETED` only when `status=ready` and no blockers remain.

Return `FAILED_VALIDATION` when one or more blockers remain. This is a
pre-run failure, not a partial execution failure.
