# Code Replicate Execution Playbook For Codex Native

This playbook adapts `code-replicate` into a Codex-native reverse-engineering
workflow.

## Purpose

Use this workflow to reverse-engineer an existing codebase into standardized
`.allforai/` artifacts that downstream workflows can consume.

It is for:

- extracting business intent from an existing system
- producing `product-map`, `experience-map`, and `use-case` style artifacts
- preparing an existing codebase for downstream forge workflows

It is not for:

- generating implementation code
- rewriting the source codebase
- performing arbitrary modernization without producing artifacts

## Inputs to collect

Minimum inputs:

- source path or Git URL
- fidelity level: `interface`, `functional`, `architecture`, or `exact`

Optional but important inputs:

- project type: `backend`, `frontend`, `fullstack`, `module`
- scope: `full`, `modules`, `feature`, or custom scope text
- module path when using `module`
- target stack intent, if cross-stack migration matters

Ask the user only when the missing input is genuinely blocking. Otherwise:

- infer project type from code layout
- default fidelity to `functional`
- default scope to `full`

## Fidelity mapping

| Fidelity | Meaning |
|---|---|
| `interface` | contracts and external surface only |
| `functional` | business behavior extraction, recommended default |
| `architecture` | behavior plus dependency and architecture structure |
| `exact` | highest-fidelity extraction including constraints and bug-compatible behavior notes |

## Workflow phases

### Phase 1: Preflight

Objectives:

- normalize source input
- clone remote repository if needed
- collect missing parameters
- initialize `.allforai/code-replicate/`

Key outputs:

- `.allforai/code-replicate/replicate-config.json`
- `.allforai/code-replicate/fragments/`

### Phase 2: Discovery and confirmation

Objectives:

- discover structure
- summarize modules and key files
- inspect runtime and infrastructure
- inspect assets and supporting resources
- generate a source summary and extraction plan inputs

Key outputs:

- `.allforai/code-replicate/discovery-profile.json`
- `.allforai/code-replicate/source-summary.json`
- `.allforai/code-replicate/infrastructure-profile.json`
- `.allforai/code-replicate/asset-inventory.json`
- `.allforai/code-replicate/stack-mapping.json`

This phase may require one final confirmation pass if the inferred project model
is ambiguous.

### Phase 3: Generate

Objectives:

- generate structured fragments by module
- merge fragments into standardized artifacts
- generate indexes and summary artifacts

Expected outputs may include:

- `.allforai/product-map/`
- `.allforai/experience-map/`
- `.allforai/use-case/`
- `.allforai/code-replicate/extraction-plan.json`

### Phase 4: Verify and handoff

Objectives:

- validate schema and artifact completeness
- write a replication report
- identify downstream handoff expectations

Key outputs:

- `.allforai/code-replicate/replicate-report.md`
- `.allforai/code-replicate/fidelity-report.json` when fidelity verification is performed

## Project type routing

| Type | Primary source focus |
|---|---|
| `backend` | handlers, services, repositories, models, infrastructure |
| `frontend` | routes, pages, components, stores, interaction states |
| `fullstack` | both surfaces plus interaction between them |
| `module` | one bounded module path only |

## Codex translation rules

- Treat `/code-replicate` and subcommands as workflow labels, not literal shell commands.
- Replace `AskUserQuestion` with direct questions only for truly blocking gaps.
- Keep source code read-only unless the user explicitly broadens the task.
- Preserve the original `.allforai/` contract and fragment structure.
- Prefer explicit artifact generation over vague summaries.

## Resume and incremental behavior

If `.allforai/code-replicate/replicate-config.json` exists, reuse it to detect:

- current phase
- completed steps
- previously chosen fidelity and scope

When the user asks for incremental rerun behavior:

- keep unaffected artifacts
- rerun only affected steps when the source of truth supports it

## Final response contract

After execution, Codex should report:

1. source analyzed
2. chosen fidelity and project type
3. phases completed
4. artifacts generated
5. major ambiguity or confidence limits
6. next downstream workflow that can consume the outputs
