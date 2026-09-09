---
name: meta-orchestration-40-qa-bootstrap-node-expansion-qa
description: Audit every generated node-spec before /run for completion standards that prove effect and quality (not existence), a bounded attention contract, and QA-to-repair-to-closure wiring; step 4 of bootstrap-audits, after the three-lens DAG gate.
---

# Bootstrap Node Expansion QA Skill

> Internal sub-skill for meta-orchestration. Status: bundled,
> bootstrap-support, pre-run gate. Invoked by
> `${CLAUDE_PLUGIN_ROOT}/knowledge/bootstrap-audits.md` step 4.

## Overview

Bootstrap can fail silently by generating a small legal-looking workflow that
does not represent a mature product. This skill validates the generated
workflow before `/run`: it checks whether bootstrap expanded the guiding
philosophy into concrete nodes, dependencies, artifacts, and verification
evidence.

The three-lens DAG gate proves the node *graph* is sound: decisions closed,
no cycles, every goal traced. This skill proves each *node-spec* is sound. A
graph can pass every structural lens while its nodes still say "done when the
file exists". This audit reads every node-spec in
`.allforai/bootstrap/node-specs/` and rejects the workflow when any production
node has a weak completion standard, an unbounded attention contract, or a QA
finding with nowhere to go.

This is not a domain implementation skill. It is a meta QA gate. The Guiding
Philosophy below is how the auditor thinks about any project; the checks after
it are the known failure modes that thinking has already caught. When a
node-spec is wrong in a way no listed blocker code names, reason from the
philosophy, reject it anyway, and record the finding under the closest code.

## Guiding Philosophy

Every production workflow must be expanded through these lenses:

- **Reverse reasoning**: infer the shipped product surfaces, runtime modules,
  data containers, assets, integrations, and acceptance evidence from the final
  user experience, then backfill required nodes. Coverage Self-Check and the
  reverse critic in `bootstrap-audits.md` run this over the graph; this audit
  applies it per node and reports what they missed as under-expansion.
- **Closure loops**: every QA, visual review, runtime smoke, platform test, or
  artifact audit must route repairable findings into a repair-and-revalidation
  loop with a bounded retry budget, and closure must depend on that loop. A wired
  edge is not yet a reachable route: a failed QA node never completes, so the
  repair must also be declared in
  `unattended-run-readiness-spec.json.required_repair_loops`, which is what the
  orchestrators consume to dispatch it. Audit reachability, not only topology.
- **Acceptance-driven execution**: node completion must include effect
  verification. "Code was written", "file exists", or "function is callable" is
  implementation evidence, not completion evidence.
- **Quality-driven acceptance**: node completion must ask "is it good enough
  for the approved project promise?" not only "does it exist?" Bootstrap must
  generate project-specific quality questions, evidence requirements, failure
  codes, and repair routes for user-facing, runtime, visual, audio, content,
  and integration deliverables.
- **Attention management**: every node must declare what it is optimizing for,
  what it is not doing, which inputs are mandatory, which inputs are optional,
  which quality questions stay in focus, when it must stop, and which repair
  targets it may emit. A node-spec that invites broad repository reading,
  vague context gathering, or unbounded "improve this" work is not suitable for
  unattended execution.
- **Bootstrap context compression**: do more project understanding, routing,
  specialization, and contract writing in bootstrap so `/run` can execute by
  pulling exact inputs instead of re-reading the whole project. Bootstrap should
  spend context to create durable node-specs, interface cards, visual
  acceptance standards, and repair loops; execution nodes should spend context
  only on their declared attention contract and current evidence.
- **Dimension elevation thinking**: raise the reasoning level above the current
  node list and above the user's named means. Do not merely add more
  categories. First distinguish the user's goal from the proposed route: "buy a
  plane ticket" may actually mean "arrive at a destination on time", where a
  train ticket could satisfy the goal better. For product automation, do not
  treat "use Cocos", "generate Canvas2D nodes", or "add this module" as the
  final objective until the underlying desired product outcome is clear. Model
  the workflow as an automated production system: what invariants, contracts,
  evidence, dependency closures, and failure-recovery mechanisms must exist for
  the system to reliably produce that outcome unattended? Then project that
  higher-level model back down into required nodes, node completion standards,
  validators, and repair routes. When the better route differs from the user's
  named means, the finding is a Phase A decision input with the alternative,
  never a silent swap.

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
  hard-blocked by that repair node. The same loop is declared in
  `unattended-run-readiness-spec.json.required_repair_loops` as
  `{scope, qa_node_ids, repair_node_id, closure_node_ids, max_attempts}`, so the
  repair is reachable while its QA node is failed and closure still waits for the
  QA rerun.
- **Documentation contract**: a node that promises a generated fact document
  declares it at planning time in `required_documents`, with its
  `document_verification` argv. A document promised only in prose has no gate.

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
.allforai/bootstrap/<runtime>-game-client-profile.json
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
  "reverse_reasoning_findings": [],
  "dimension_elevation_findings": [],
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

- `underexpanded_product_surface`
- `missing_reverse_inference_node`
- `missing_runtime_or_surface_node`
- `missing_dimension_elevation_review`
- `missing_high_level_product_dimension`
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
- `missing_io_effect_qa`
- `missing_platform_qa`
- `missing_runtime_family`
- `missing_repair_loop`
- `repair_loop_not_blocked_by_qa`
- `acceptance_not_blocked_by_repair_loop`
- `qa_report_without_revalidation`
- `undeclared_repair_loop_routing`
- `unowned_effect_stage`
- `missing_document_contract`

## What the gates already prove, and what this audit must judge

Part of the closure, effect and documentation contracts is structured enough for the
copied `validate_bootstrap.py` to decide, and it does — before this audit runs, at both
the bootstrap and `/run` boundaries:

| Structured contract, enforced by the gate | Semantic judgment, yours |
|---|---|
| A declared `required_repair_loops` entry with no QA source, no closure holder, a repair node listed as its own QA/closure, or a closure node that does not wait for the QA rerun (`undeclared_repair_loop_routing`); `validate_unattended_readiness.py` checks the opposite direction, that a declared QA/closure node carries its `hard_blocked_by` edge | Whether a graph shape *is* a QA loop that needs declaring at all — which node produces repairable findings, which repair answers them, which closure must wait |
| A `downstream_effect_owner` that names a missing node, the node itself, a node that does not run after it, or one whose spec has no Effect Verification (`unowned_effect_stage`) | Whether a node's Effect Verification demands proof its own stage cannot produce, so a deferral (or a merge) was needed in the first place |
| A `required_documents` entry with no `document_verification` argv, and a document contract declared on the node-spec but not on the workflow node (`missing_document_contract`) | Whether a node's Task promises a document it never declared. Documentation responsibility alone is not that promise: a node may own updates to documents that already exist, and forcing a new fact document on every `documentation` responsibility is a false finding |

Report a structured failure under its code if you see it, but do not stop at the codes
the gate can decide: the judgments in the right-hand column are the reason this audit
exists, and they are read from the node-spec's own prose.

## Automatic Validation

Reject the workflow when any production node-spec matches one of these:

- product/runtime evidence implies multiple surfaces/modules, but bootstrap only
  generated scaffold/build/smoke nodes;
- bootstrap treats a named means, technology, module, or requested node as the
  final goal without checking the underlying product outcome and alternative
  routes, or swaps the route without a Phase A decision input;
- the workflow only follows the current implementation path and does not raise
  the reasoning level to production-system invariants, contract closure,
  evidence quality, dependency closure, and failure-recovery requirements;
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
- the node-spec declares no must-read inputs or no context budget at all (an
  undeclared reading set is unauditable); a declared floor that the executor may
  exceed on demand is correct and is not a finding — only a whole-repository scan
  presented as the task without repository-wide evidence being the task is;
- the node-spec has no stop condition for missing inputs, unavailable runtime,
  failed effect evidence, unresolved quality gaps, or environment blockers;
- a visible runtime node has no screenshot, runtime probe, or visual
  acceptance evidence;
- an I/O node has only mocks or function-call assertions, without real effect
  proof;
- a platform target (mobile, desktop, WebView, console, store build) has no
  platform QA node proving the build runs and renders on that target;
- a generated module node does not require production consumer wiring proof;
- a rewritten module node does not require import/export compatibility checks;
- a QA node's repairable findings have no repair-and-revalidation node, or that
  node is not `hard_blocked_by` the QA node;
- final acceptance or closure is not `hard_blocked_by` the repair node;
- a QA node may pass on a prior report without rerunning after repair;
- that repair loop is not declared in
  `.allforai/bootstrap/unattended-run-readiness-spec.json.required_repair_loops`
  with this QA node in `qa_node_ids`, the repair node as `repair_node_id`, the
  closure nodes in `closure_node_ids`, and a bounded `max_attempts`. The
  `hard_blocked_by` edge alone makes the repair unreachable: a failed QA node
  never completes, and both orchestrators dispatch the repair from this
  declaration. Report it as `undeclared_repair_loop_routing`;
- a node's Effect Verification demands proof of an effect that only exists after
  a later node (production wiring, integration, deployment) while naming no
  stage-local proof and no downstream owner. Either the deliverable is one node,
  or this node states the effect observable at its own stage and names the
  downstream node that proves the full effect — and that node's spec accepts it.
  An unowned deferral is `unowned_effect_stage`, and the owner is declared as the node's
  `downstream_effect_owner` so the deferral is checkable rather than only described;
- a node whose `responsibilities` include `documentation`, or whose Task promises
  a document it will write, carries an empty `required_documents` (or a required
  document without its `document_verification` argv). Deferring that declaration
  to run time is a planning gap, not a run-time detail: no gate can demand a
  document nobody declared. Report it as `missing_document_contract`.

## Runtime Specialization

When the detected runtime has a knowledge file, delegate the concrete node
family matrix to it:

```text
${CLAUDE_PLUGIN_ROOT}/knowledge/engines/<runtime>.md
.allforai/bootstrap/<runtime>-game-client-profile.json
```

The workflow must include or explicitly block every node family that file
declares for a mature client of that runtime (typically runtime core,
interface contracts, asset bundle, scenes, gameplay systems, runtime QA,
gameplay visual QA, performance QA, platform QA, repair loop, and concept
acceptance). A family that is neither present nor blocked with a reason in the
project-local runtime profile is `missing_runtime_family`. Mobile and
high-density targets must include high-DPR screenshot QA before native build
acceptance. This audit does not enumerate families itself; the runtime file
and the profile own the list.

Runtime-specific evidence requirements (DPR screenshots, probe schemas, build
export checks) also come from that file and the specialized skills bootstrap
already wrote; this audit checks that the node-spec references them, not what
they contain.

## Completion Conditions

Return `COMPLETED` only when `status == "passed"` and every production node has
an attention contract, effect verification, quality acceptance, and closure
wiring. Return `FAILED_VALIDATION` when any node has code-only or
existence-only completion, lacks attention boundaries, lacks quality questions,
carries unresolved quality gaps, lets fallback states unlock downstream nodes,
or leaves a QA finding without a repair route. On failure bootstrap regenerates
the named node-specs and reruns this audit; it does not offer `/run`.
