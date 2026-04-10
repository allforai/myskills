---
name: bootstrap
description: >
  Codex adapter for the canonical meta-skill bootstrap protocol. Use the shared
  bootstrap logic from the Claude meta-skill, but rewrite platform-specific paths
  and generated entrypoints for Codex.
---

# Bootstrap Protocol — Codex Adapter

## Canonical Source

The canonical bootstrap protocol is maintained at:

- `../../claude/meta-skill/skills/bootstrap.md`

Use that protocol in full, but apply the Codex-specific substitutions below.

## Required Codex Substitutions

### 1. Plugin Root Resolution

Whenever the canonical protocol references a Claude-specific plugin-root variable, resolve it as:

- `codex/meta-skill/`

Repository-relative examples:

- `../../claude/meta-skill/knowledge/...` for canonical knowledge text
- `./scripts/...` or `./mcp-ai-gateway/...` for Codex-local linked runtime helpers

### 2. Generated Run Entry

When the canonical protocol says:

- read the orchestrator template from `knowledge/orchestrator-template.md`
- write `.claude/commands/run.md`

For Codex, do this instead:

- read `../knowledge/orchestrator-template.md` as the Codex-native generation template
- write the generated run entry to `.codex/commands/run.md` in the target project

### 3. Canonical Bootstrap Graph

When the canonical protocol mentions `state-machine.json`, treat that as legacy wording.

For Codex generation:

- write `.allforai/bootstrap/workflow.json`
- validate against `workflow.json`
- only read `state-machine.json` for backward compatibility if older outputs exist

### 4. Project-Local Runtime Copies

The generated workflow must still copy project-local helper assets into the target project:

- `.allforai/bootstrap/scripts/*`
- `.allforai/bootstrap/protocols/*`

Those copied assets must reference only project-local paths at run time.
When product inference is emitted, include a project-local `check_product_summary.py` validator in `.allforai/bootstrap/scripts/`.

Codex-only runtime helpers must not be mixed into the shared bootstrap tree.

Write Codex-only execution helpers under:

- `.allforai/codex/*`

Example:

- `.allforai/codex/flow.py` for a Codex non-stop outer driver

Generation rule:

- materialize `../knowledge/flow-template.py` into `.allforai/codex/flow.py`
- the generated file must invoke `codex exec --dangerously-bypass-approvals-and-sandbox`
- it should work with zero arguments by default
- it may accept legacy positional arguments `<goal> <max_iterations>` for compatibility, but must not require them
- it must treat `workflow.json` plus `transition_log` as the runtime source of truth
- after 3 consecutive failures on the same node, it must stop retries, run diagnosis, and record `diagnosis_history`
- after 5 consecutive transitions with no new artifacts, it must stop instead of looping forever

### 5. User Invocation Text

When the canonical protocol tells the user to run `/run [goal]`, adapt the instruction to:

- use the generated Codex run entry at `.codex/commands/run.md`
- invoke it through Codex's command mechanism in the target project

### 6. Research-First Specialization

Codex bootstrap should prefer:

1. research from the real project
2. LLM synthesis from evidence
3. hard minimum responsibility packs only for high-risk domains

Do not overfit bootstrap into a library of rigid templates.

When uncertainty can be reduced by reading the real codebase, upstream `.allforai/` artifacts,
or user-supplied references, prefer that over generic assumptions.

### 7. High-Risk Domain Specialization Hook

For domains where generic planning often misses hidden complexity:

- read `../knowledge/high-risk-specialization.md`
- detect whether any high-risk specialization applies
- if yes, inject the corresponding minimum responsibility floor

Rules:

- the floor defines responsibilities, not fixed node names
- research and LLM synthesis still determine the final workflow shape
- once a high-risk domain is confirmed, the required responsibilities may not be omitted

### 8. IM / Realtime Messaging Specialization

For Telegram / WhatsApp / Discord / secure-messaging style products:

- read `../knowledge/im-specialization.md`
- classify whether the product is truly `im_realtime`
- if yes, inject the mandatory IM responsibility pack at workflow-planning time

Important:

- the mandatory pack defines logical responsibilities, not rigid node names
- LLM may merge or split nodes
- LLM may not omit realtime / sync / state / moderation / media verification responsibilities once `im_realtime` is confirmed

### 9. Reverse Product Inference

When the repository contains enough evidence to infer the product shape:

- read `../knowledge/product-inference.md`
- synthesize an evidence-backed product picture from real code, protocols, UI/page names, configs, and runtime modules
- write `.allforai/bootstrap/product-summary.json`

Rules:

- this is a standard bootstrap output when supported by evidence
- prefer expressing this responsibility as a standard workflow node, for example `infer-product-shape`
- it should describe user-facing systems, not just tech stacks
- if confidence is low, emit open questions instead of pretending certainty

### 10. Phase 1 Structured Node-Specs

During the first `spec/design/task` migration phase, keep `node-specs/*.md` as the runtime contract,
but standardize each generated node-spec around these sections:

- `## Spec`
- `## Design`
- `## Task`

Rules:

- `## Spec` defines goal, evidence scope, exit artifacts, and acceptance constraints
- `## Design` records current approach, tradeoffs, and open risks
- `## Task` defines the immediate executable work
- YAML frontmatter with `node:` remains required
- generated run continues to read `node-specs/*.md` first during this phase

Recommended shape:

```md
---
node: <node-id>
---

# Node

## Spec

- goal
- evidence inputs
- exit artifacts
- acceptance / invariants

## Design

- approach
- alternatives or tradeoffs
- open risks

## Task

- immediate actions
- concrete file or surface targets
- local verification
- completion signal
```

## Validation Requirements

After generation, verify all of the following:

- `.allforai/bootstrap/bootstrap-profile.json` exists
- `.allforai/bootstrap/workflow.json` exists
- `.allforai/bootstrap/node-specs/*.md` exist
- `.codex/commands/run.md` exists
- project-local helper copies exist under `.allforai/bootstrap/`
- `.allforai/codex/flow.py` exists for Codex targets

For Phase 1 structured node-spec migration, also verify:

- each non-trivial node-spec includes `## Spec`
- each non-trivial node-spec includes `## Design`
- each non-trivial node-spec includes `## Task`

When product inference is supported by repository evidence, also verify:

- `.allforai/bootstrap/product-summary.json` exists
- `.allforai/bootstrap/scripts/check_product_summary.py` exists
- it contains at least 3 evidence entries
- it includes at least one user-facing system or product classification

For `im_realtime` workflows, also verify:

- at least one realtime infrastructure responsibility exists
- at least one sync responsibility exists
- at least one message-state responsibility exists
- at least one IM-specific verification responsibility exists

For any future high-risk domain hook, also verify:

- the domain's minimum responsibility floor exists in the generated workflow
