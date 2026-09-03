---
name: meta-orchestration-40-qa-bootstrap-node-expansion-qa
description: Audit every generated node-spec before /run for completion standards that prove effect and quality (not existence), a bounded attention contract, and QA-to-repair-to-closure wiring; step 4 of bootstrap-audits, after the three-lens DAG gate.
---

# Bootstrap Node Expansion QA Skill

> Internal sub-skill for meta-orchestration. Status: bundled,
> bootstrap-support, pre-run gate. Invoked by
> `${CLAUDE_PLUGIN_ROOT}/knowledge/bootstrap-audits.md` step 4.

## Overview

The three-lens DAG gate proves the node *graph* is sound: decisions closed,
no cycles, every goal traced. This skill proves each *node-spec* is sound. A
graph can pass every structural lens while its nodes still say "done when the
file exists". This audit reads every node-spec in
`.allforai/bootstrap/node-specs/` and rejects the workflow when any production
node has a weak completion standard, an unbounded attention contract, or a QA
finding with nowhere to go.

This is not a domain implementation skill and it does not judge graph coverage
(Coverage Self-Check and the reverse critic own that). It judges node
completion standards, attention boundaries, and repair wiring.

## What Every Production Node Must Carry

- **Acceptance-driven execution**: completion includes effect verification.
  "Code was written", "file exists", or "function is callable" is
  implementation evidence, not completion evidence.
  Reject code-only or existence-only completion.
- **Quality-driven acceptance**: completion asks "is it good enough for the
  approved project promise?", not only "does it exist?". Each user-facing,
  runtime, visual, audio, content, or integration node carries
  project-specific quality questions, evidence requirements, failure codes,
  and repair routes. Non-empty `quality_gaps`, `effect_gaps`,
  `experience_gaps`, `visual_quality_gaps`, or `perceptual_gaps` block
  downstream production nodes.
- **Attention management**: the node declares its primary outcome (the
  underlying product result, not a named means or file-writing task),
  non-goals, must-read inputs, optional inputs, the quality questions that stay
  in focus, stop conditions, and the repair targets it may emit. A node-spec
  that invites broad repository reading, vague context gathering, or unbounded
  "improve this" work is not suitable for unattended execution.
- **Bootstrap context compression**: the node executes in pull mode, reading
  exactly the inputs its attention contract names. Project understanding,
  routing, specialization, and contract writing were bootstrap's job; a node
  that must re-derive them is under-specified.
- **Closure wiring**: every QA, visual review, runtime smoke, platform test, or
  artifact audit node routes repairable findings into a repair-and-revalidation
  node with a bounded retry budget, and final acceptance or closure is
  hard-blocked by that repair node.

## Input Contract

Required:

```text
.allforai/bootstrap/workflow.json
.allforai/bootstrap/node-specs/
.allforai/bootstrap/bootstrap-profile.json
```

Optional:

```text
.allforai/bootstrap/dag-critique.json
.allforai/orchestration/skill-composition-plan.json
.allforai/game-design/game-design-doc.json
.allforai/app-design/app-design-doc.json
.allforai/concept-contract.json
.allforai/product-concept/concept-baseline.json
```

## Output Contract

Writes:

```text
.allforai/bootstrap/bootstrap-node-expansion-qa-report.json
.allforai/bootstrap/bootstrap-node-expansion-qa-report.md
```

The JSON report must include:

```json
{
  "status": "passed | failed",
  "checked_at": "<iso8601>",
  "nodes_checked": 0,
  "node_completion_findings": [],
  "attention_management_findings": [],
  "closure_wiring_findings": [],
  "required_repairs": []
}
```

Every finding names the `node_id`, the blocker code, the offending node-spec
section, and the repair (regenerate the node-spec section, add a repair node,
add a `hard_blocked_by` edge).

Allowed blocker codes:

- `code_only_completion`
- `existence_only_completion`
- `missing_effect_verification`
- `missing_quality_acceptance`
- `missing_quality_questions`
- `unresolved_quality_gaps`
- `fallback_completion_allowed`
- `missing_attention_contract`
- `missing_non_goals`
- `missing_stop_conditions`
- `unbounded_context_pull`
- `missing_visual_acceptance`
- `missing_runtime_probe`
- `missing_repair_loop`
- `repair_loop_not_blocked_by_qa`
- `acceptance_not_blocked_by_repair_loop`
- `qa_report_without_revalidation`

## Automatic Validation

Reject the workflow when any production node-spec matches one of these:

- completion says `done`, `implemented`, or `file exists` without an effect
  verification artifact;
- completion uses existence/structure/function-call checks without
  project-specific quality acceptance questions;
- a report may declare non-empty `quality_gaps`, `effect_gaps`,
  `experience_gaps`, `visual_quality_gaps`, or `perceptual_gaps` while still
  unlocking downstream production nodes;
- QA outputs may be `partial`, `conditional_pass`, `accepted_with_warnings`,
  or fallback completion while still unlocking downstream production nodes;
- the node-spec lacks an `Attention Contract` with primary outcome, non-goals,
  must-read inputs, quality questions, stop conditions, and repair targets;
- the node-spec asks the executor to read broad context or scan the whole
  repository without justifying repository-wide evidence as the task itself;
- the node-spec has no stop condition for missing inputs, unavailable runtime,
  failed effect evidence, unresolved quality gaps, or environment blockers;
- a visible runtime node has no screenshot, runtime probe, or visual
  acceptance evidence;
- an I/O node has only mocks or function-call assertions, without real effect
  proof;
- a generated module node does not require production consumer wiring proof;
- a rewritten module node does not require import/export compatibility checks;
- a QA node's repairable findings have no repair-and-revalidation node, or that
  node is not `hard_blocked_by` the QA node;
- final acceptance or closure is not `hard_blocked_by` the repair node;
- a QA node may pass on a prior report without rerunning after repair.

Runtime-specific evidence requirements (DPR screenshots, probe schemas, build
export checks) come from the project-local runtime profile and specialized
skills that bootstrap already wrote; this audit checks that the node-spec
references them, not what they contain.

## Completion Conditions

Return `COMPLETED` only when `status == "passed"` and every production node has
an attention contract, effect verification, quality acceptance, and closure
wiring. Return `FAILED_VALIDATION` when any node has code-only or
existence-only completion, lacks attention boundaries, lacks quality questions,
carries unresolved quality gaps, lets fallback states unlock downstream nodes,
or leaves a QA finding without a repair route. On failure bootstrap regenerates
the named node-specs and reruns this audit; it does not offer `/run`.
