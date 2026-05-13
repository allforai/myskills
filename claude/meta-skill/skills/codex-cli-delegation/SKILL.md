---
name: codex-cli-delegation
description: Internal bundled meta-skill module for low-token ClaudeCode orchestration of Codex CLI delegated tasks; use when Claude should delegate file-reading, visual review, generation, QA, or repair work to Codex CLI without copying input file contents into Claude context.
---

# Codex CLI Delegation Skill Pack

> Internal bundled sub-skill pack for meta-skill.
> Status: bundled, inactive, not wired.

## Purpose

This pack owns the low-token delegation pattern for calling Codex CLI from
ClaudeCode. ClaudeCode orchestrates, but Codex CLI reads project files, reasons,
writes outputs, and returns only a final summary.

## Current Children

| Layer | Child skill | Responsibility |
|---|---|---|
| `30-execute` | `codex-cli-task` | Run a bounded Codex CLI task with a short prompt, target working directory, sandbox policy, output contract, and final-result-only return. |

## Canonical Invocation Paths

Use this path when another skill needs Codex CLI delegation:

```text
${CLAUDE_PLUGIN_ROOT}/skills/codex-cli-delegation/30-execute/codex-cli-task/SKILL.md
```

## Delegation Rule

Never have ClaudeCode read large input files and paste their contents into a
Codex prompt. Give Codex CLI file paths, goals, output paths, and acceptance
criteria. Let Codex read and write inside the target workspace.
