---
name: code-replicate-codex
description: >
  Use this skill when the user asks to "replicate code", "reverse engineer codebase",
  "migrate tech stack", "代码复刻", "技术栈迁移", "逆向分析", "clone backend to Go",
  "port frontend to Flutter", "rewrite in another stack", "cross-stack migration",
  "code replication", "复刻", "replicate API", "verify replication fidelity",
  "还原度验证", "visual comparison", "视觉还原", "screenshot diff",
  or mentions converting existing code to a different tech stack while preserving behavior.
---

# Code-Replicate (Codex Native)

## Role

Code replication bridge: reverse-engineer existing codebases (any tech stack) into
`.allforai/` artifacts compatible with the dev-forge pipeline. Supports 4 fidelity
levels (interface, functional, architecture, exact) and cross-stack migration.

## Available Workflows

| Workflow | Description |
|----------|-------------|
| code-replicate | Full 4-phase pipeline: preflight > discovery > artifact generation > verification. Modes: interface / functional / architecture / exact. Types: backend / frontend / fullstack / module |
| cr-fidelity | Source vs target code fidelity verification. Modes: full (analyze+fix loop) / analyze (report only) / fix (repair from last report) |
| cr-visual | Visual fidelity: screenshot/video comparison of source vs target app. Modes: full / analyze / fix |

## Quick Start

Read `./execution-playbook.md` for phase-by-phase orchestration instructions.
Read `./SKILL.md` for domain knowledge, fidelity levels, and output structure.

## Key Principles

- **Extract intent, not implementation** -- capture "what it does" not "how it does it"
- **Source-summary stays in context** -- all Phase 3 calls include source-summary + code-index
- **Scripts merge, LLM extracts** -- LLM generates per-module fragments, scripts handle cross-module merge + ID assignment
- **Fidelity controls depth, not breadth** -- all levels produce the same files, higher fidelity fills more fields
- **Infrastructure before business** -- Phase 2 Stage B (infra) must complete before Phase 3 extraction
- **UI-driven closure** -- Phase 3 cross-references Phase 2.13 screenshots/recordings to validate extraction completeness
- **4D self-check on every fragment** -- conclusion / evidence / constraints / decisions
- **No file skipping** -- every module must reach >= 50% file coverage
- **Artifacts are free-form** -- LLM decides what artifacts to produce based on project_archetype, not a hardcoded list

## Downstream Handoff

```
code-replicate  >  design-to-spec  >  task-execute
      |
cr-fidelity (code-level fidelity, replication-specific)
      |
product-verify (functional acceptance, shared with creation path)
      |
cr-visual (visual fidelity, requires stable running app)
```

## Script Location

All Python scripts are at `../../shared/scripts/code-replicate/`.
