---
name: codex-cli-delegation-30-execute-codex-cli-task
description: Execute a bounded Codex CLI task from ClaudeCode with minimal prompt tokens, workspace-local file access, sandbox controls, final-result-only output, and auditable command metadata.
---

# Codex CLI Task

## Overview

Delegate a bounded task to Codex CLI while minimizing ClaudeCode token use.
ClaudeCode provides a short instruction and file paths; Codex CLI reads files,
does the work, writes artifacts, and returns a concise final result.

Use this for visual review, generated asset QA, batch document review, repair
passes, test investigation, or any task where Codex can operate directly in the
workspace.

## Input Contract

Required:
- target working directory;
- short task prompt;
- output paths Codex must write;
- sandbox policy;
- completion criteria.

Optional:
- selected model;
- evidence directories;
- allowed write roots;
- timeout;
- previous reports to read.

## Output Contract

The caller must record:

```text
<output_root>/codex-cli-task-command.json
<output_root>/codex-cli-task-final.md
```

`codex-cli-task-command.json` must include:
- `cwd`
- `sandbox`
- `selected_model`
- `prompt`
- `output_paths`
- `return_all_messages: false`
- `started_at`
- `exit_code`

## Invocation Contract

```json
{
  "skill": "codex-cli-delegation/codex-cli-task",
  "mode": "execute_short_prompt",
  "cwd": "/absolute/project/path",
  "sandbox": "workspace-write",
  "selected_model": "codex-default",
  "prompt": "Read the listed files, perform the task, write the requested reports, and summarize changed files.",
  "output_root": ".allforai/codex-delegation",
  "output_paths": []
}
```

Supported modes: `execute_short_prompt`, `execute_visual_review`,
`execute_repair_rerun`.

## Low-Token Rules

- Keep ClaudeCode's prompt short: goal, file paths, output paths, and strict
  success condition.
- Do not paste large file contents into the prompt.
- Do not ask ClaudeCode to summarize input files before delegation.
- Do not enable `--return-all-messages`.
- Ask Codex CLI to write reports to files, then have ClaudeCode read only the
  final summary and the specific report fields needed for closure audit.
- Prefer `workspace-write` sandbox for project-local writes. Use read-only only
  for pure review. Do not use unrestricted execution unless the caller's
  workflow explicitly requires it.

## Pull Mode Delegation

Use pull mode by default. A short prompt is not a vague prompt: ClaudeCode gives
Codex CLI the target cwd, input paths, evidence directories, output paths,
allowed write roots, and success/failure conditions. Codex CLI then pulls the
needed context from the workspace, reads the files directly, performs the task,
and writes auditable reports.

Pull mode is required for visual review, screenshot review, product/design
review, skill review, and batch QA work. Do not push file contents, screenshots,
large JSON, or long Markdown summaries through ClaudeCode unless the file is
unavailable to Codex in the target cwd.

If any declared input path is missing, unreadable, or outside the allowed
workspace, return `blocked_by_missing_input_paths` instead of asking ClaudeCode
to restate the missing content in the prompt.

## Command Shape

Use a command shape equivalent to:

```bash
codex exec \
  --cd "/absolute/project/path" \
  --sandbox workspace-write \
  --json \
  --output "<output_root>/codex-cli-task-final.json" \
  "Read <input paths>. Write <output paths>. Return only a concise final summary with files written and blocking issues."
```

If a wrapper such as `scripts/codex_bridge.py` exists in the project, prefer it
when it preserves the same rules:
- target cwd is explicit;
- sandbox is explicit;
- prompt is short and path-based;
- return-all-messages is disabled;
- final report is written to files.

## Completion Conditions

Return `COMPLETED` when Codex CLI exits successfully and all required output
paths exist.

Return `blocked_by_missing_codex_cli` when Codex CLI is unavailable.
Return `FAILED_VALIDATION` when Codex CLI exits nonzero, omits required outputs,
or returns only prose without the required files.
