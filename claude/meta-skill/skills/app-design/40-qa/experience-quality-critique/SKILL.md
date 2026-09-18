---
name: app-design-40-qa-experience-quality-critique
description: Judge whether an app design or a running build adds up to an experience worth using, with evidence-typed findings, Chinese review HTML, repair routing, and a human-readable review doc.
---

# Experience Quality Critique

## Purpose

Judge whether the app-design contracts, and later the running build, add up to
an experience a real person would get through, come back to, and recognize as
the direction that was confirmed. Every specialist spec can validate while the
product still opens on a feature menu, tells nobody what just happened, ends
every task in a dead end, or quietly asks the end user for a service endpoint.

This is an **in-run self-correction gate**, not the delivery verdict. Whether
the work is finished and whether it is any good stay with the post-run entries
`/cross-exam` and `/product-review` (ADR-0008). This skill neither calls them
nor lends its name to a node: a node id or capability containing `cross-exam`
or `product-review` is rejected by `verdict_entry_planned_as_node` in
`validate_unattended_readiness.py`. What this skill produces is a critique plus
repair routing, consumed inside the same run.

## Stages

Two stages, selected by the invoking node through the Invocation Contract
`mode`:

- `stage: "design"` — after the app-design spec nodes and before UI or program
  implementation. Evidence is the spec set; the only gate it may fill is
  `must_fix_before_implementation`.
- `stage: "runtime"` — after the last UI, product-verify, and visual QA node.
  Evidence is screenshots, visual reviews, and runtime reports; the only gate
  it may fill is `must_fix_before_release`.

The stage is written into the report, into the output file names, and into the
review doc name. A stage that disagrees with its file name is a failure.

## Reviewer Independence

The review is run by a fresh-context reviewer that did not author the artifacts
under review, following ADR-0002/0003: a review context must not be the context
that produced the reviewed artifact, and same-context self-review is a
degradation that never counts as a pass.

The node-spec must state that the reviewer reads only the artifacts and
evidence listed in the Input Contract. It must **not** read the authoring
node's reasoning, its conversation transcript, or the execution notes in its
node-spec; the artifacts have to carry the claim on their own.

Record this in the report as
`reviewer: {"context": "fresh-subagent|other-platform-cli", "authored_reviewed_artifacts": false}`.
When `authored_reviewed_artifacts` is `true`, the only legal status is
`FAILED_VALIDATION`.

## Input Contract

Read every applicable artifact. A missing **optional** input is recorded in
`evidence_inventory[]` with `available: false` and produces one finding with
`judgment_type: "insufficient_evidence"`; it is never silently ignored. A
missing **required** input returns `UPSTREAM_DEFECT`.

| Input | design | runtime | Source |
|---|---:|---:|---|
| `.allforai/app-design/concept/job-story-spec.json` | yes | yes | app-design artifacts |
| `.allforai/app-design/spec/user-flow-spec.json` | yes | yes | app-design artifacts |
| `.allforai/app-design/spec/screen-requirements-spec.json` | yes | yes | app-design artifacts |
| `.allforai/app-design/spec/permissions-notifications-settings-spec.json` | no | no | settings `audience` / `provisioning` |
| `.allforai/app-design/spec/app-surface-topology-spec.json` (`service_endpoints[]`) | no | no | endpoint `audience` / `provisioning` |
| `.allforai/product-concept/product-concept.json`, the confirmed `topic == "experience-direction"` intents and their `acceptance` | yes | yes | experience direction |
| `.allforai/bootstrap/bootstrap-profile.json`, `experience_priority.mode` | yes | yes | experience priority |
| `.allforai/app-design/qa/experience-quality-critique-design.json` | — | no | the previous stage's conclusions |
| `.allforai/product-verify/ui-screenshot-manifest.json`, `.allforai/visual-verify/screenshot-manifest.json` | — | at least one | screenshot manifests |
| `.allforai/product-verify/visual-review-1.json`, `.allforai/visual-verify/visual-review-{1,2}.json` | — | no | visual review |
| `.allforai/product-verify/verify-report.json`, `.allforai/visual-verify/visual-verify-report.json` | — | no | runtime reports |
| `contract_gaps[]` entries with `kind == "unspecified_user_visible_decision"` in implementation and verification artifacts | — | no | decisions the design still owes |

**Reading the experience direction.** Take the entries of
`product-concept.json` `requirements[]` whose `topic` is `experience-direction`
and whose `status` is `confirmed` (a superseded revision carries `superseded`
and drops out by itself). When the reviewing node's own `requirement_refs` is
non-empty, take only the ids it names. There may be several — at most one from
a model proposal, plus any the user wrote themselves. `direction.intent_ids`
lists them all, `direction.acceptance` is the union of their `acceptance`
lists, and `direction.delegated` is `true` when any entry has
`auto_decided: true`. A delegated direction is reviewed exactly like a chosen
one: the flag is disclosure, never a reason to relax or tighten the bar. The
`who` and `circumstance` of a proposal-born entry (read with `.get`; a
user-written entry has neither) are the baseline audience and situation for
`observation.who` / `observation.circumstance`. No confirmed entry at all is a
missing required input: return `UPSTREAM_DEFECT`, because a UI product without
an experience direction should already have been stopped at bootstrap by
`ui_product_without_experience_direction`.

## Output Contract

Write, with `<stage>` one of `design` or `runtime`:

```text
.allforai/app-design/qa/experience-quality-critique-design.json
.allforai/app-design/qa/experience-quality-critique-design.html
.allforai/app-design/qa/experience-quality-critique-runtime.json
.allforai/app-design/qa/experience-quality-critique-runtime.html
```

The JSON must contain:

```json
{
  "schema_version": "1.0",
  "stage": "design|runtime",
  "status": "COMPLETED|COMPLETED_WITH_LIMITS|FAILED_VALIDATION|UPSTREAM_DEFECT",
  "project_id": "string",
  "review_language": "zh-CN",
  "reviewed_at": "<ISO-8601 with offset>",
  "reviewed_commit": "<git sha | 'uncommitted' | 'no-git'>",
  "reviewer": {"context": "fresh-subagent", "authored_reviewed_artifacts": false},
  "direction": {"intent_ids": ["string"], "delegated": false, "acceptance": ["string"]},
  "evidence_inventory": [
    {
      "artifact_path": ".allforai/...",
      "artifact_type": "json|html|image|runtime_report|directory",
      "available": true,
      "used_for": ["onboarding"],
      "limitations": []
    }
  ],
  "lenses": {
    "<dimension>": {"observation": "有|缺|未查", "summary": "string", "confidence": 0.0}
  },
  "findings": [
    {
      "finding_id": "experience-001",
      "dimension": "onboarding|process_feedback|next_step|state_consistency|return_reason|mainline|direction_fidelity|audience_leak",
      "judgment_type": "contract_defect|evidence_based_critique|llm_judgment|insufficient_evidence",
      "severity": "blocker|major|minor|note",
      "confidence": 0.0,
      "claim": "string",
      "reasoning": "string",
      "observation": {"who": "string", "circumstance": "string", "task": "string", "observed": "string"},
      "evidence_refs": [".allforai/..."],
      "counterexample_or_comparison": "string",
      "repair_route": {
        "owner_skill": "app-design/<child>|implement|bootstrap",
        "owner_artifact": ".allforai/...|<source path>",
        "requested_change": "string",
        "rerun_from_node_id": "string"
      },
      "blocks": ["must_fix_before_implementation"]
    }
  ],
  "gates": {
    "must_fix_before_implementation": [],
    "must_fix_before_release": [],
    "recommended_iterations": []
  },
  "experience_gaps": [],
  "overall_recommendation": {
    "decision": "proceed|iterate_before_implementation|iterate_before_release|blocked_by_missing_evidence",
    "rationale": "string",
    "top_repairs": []
  }
}
```

Stage gates live inside `gates{}` and their elements are `finding_id`s. The
`design` stage may fill only `must_fix_before_implementation`; the `runtime`
stage may fill only `must_fix_before_release`; the other one stays `[]`. The
`runtime` stage mirrors every `must_fix_before_release` entry into
`experience_gaps[]` as `{finding_id, where, requested_change}`, which is what
carries the repair downstream; in the `design` stage `experience_gaps` stays
`[]`.

`lenses.*` is not a fake objective score. Each lens carries `有|缺|未查` plus a
`confidence` and a one-sentence `summary` — there is no numeric score anywhere
in this report.

The HTML is human-readable Chinese and shows the lens table with confidence,
the evidence inventory including what is missing, findings grouped by repair
owner, blockers separated from recommended iterations, and relative paths to
screenshots, review pages, and source JSON where they exist. Machine-readable
keys stay stable English identifiers.

## Invocation Contract

```json
{"skill":"app-design/experience-quality-critique","mode":"design","input_paths":{"job_stories":".allforai/app-design/concept/job-story-spec.json","user_flows":".allforai/app-design/spec/user-flow-spec.json","screen_requirements":".allforai/app-design/spec/screen-requirements-spec.json","settings":".allforai/app-design/spec/permissions-notifications-settings-spec.json","product_concept":".allforai/product-concept/product-concept.json","profile":".allforai/bootstrap/bootstrap-profile.json"},"output_root":".allforai/app-design/qa"}
```

Supported modes: `design`, `runtime`.

## Lenses

Eight lenses, in this order and this spelling. The first five —
`onboarding`, `process_feedback`, `next_step`, `state_consistency`,
`return_reason` — are the same names and the same meanings as the five lenses
of `/product-review` question 4 (引导 / 过程反馈 / 下一步 / 状态一致 /
回来理由); a finding written under one of them means the same thing in both
places.

- `onboarding` — does a first-time user get from "app opened" to "first useful
  outcome" without being asked to configure anything first? design: the
  onboarding and empty-state flows of the flow spec and the first-run states of
  the screen spec. runtime: the first screenshots of the manifest and the
  first-run path of the verify report.
- `process_feedback` — while a task runs, does the person know it started, how
  far it got, and that it finished? design: per-screen loading, progress,
  success, and error states. runtime: screenshots of the in-progress and
  completion states, and the visual review's notes on them.
- `next_step` — at the end of every task, is there a designed next move rather
  than a dead end? design: flow-spec exits and per-screen follow-up actions.
  runtime: screenshots of terminal screens and the reviewer's walk of what is
  reachable from them.
- `state_consistency` — does the product remember what the person did last
  time, and does the same state read the same way on every surface that shows
  it? design: persisted state in the screen and flow specs. runtime: return
  visits in the verify report and screenshots of the same entity on two
  surfaces.
- `return_reason` — is there a designed reason to come back tomorrow beyond a
  notification: progress, rhythm, unfinished items, accumulated value? design:
  job stories and the flow spec's return paths. runtime: whatever the run
  actually shows on a second session.
- `mainline` — is there one personalized main path through the product, or is
  the home screen a grid of features and every screen an equal-weight entry?
  design: information architecture and the flow spec's primary flow. runtime:
  the home screenshot and the reviewer's walk of the primary journey.
- `direction_fidelity` — check the confirmed experience direction's
  `acceptance` line by line against what the artifacts actually deliver, and
  check for **literal translation**: the user's words turned verbatim into
  features or controls (for example "碎片化学习" becoming a duration picker plus
  a list of question types). Literal translation is a finding even when every
  `acceptance` line is nominally satisfied.
- `audience_leak` — the criterion is not restated here: it is
  `${CLAUDE_PLUGIN_ROOT}/knowledge/defensive-patterns.md` Pattern J (Audience
  Isolation) plus the "audience leak" check in
  `${CLAUDE_PLUGIN_ROOT}/knowledge/capabilities/product-verify.md`. design:
  read `settings_groups[].items[]` of the settings spec — `audience`
  (`end-user` / `operator` / `developer`), `provisioning` (`build-time` /
  `remote-config` / `deploy-env`), `surface`, `requirement_ref` — and
  `service_endpoints[]` of the topology spec with the same two fields. runtime:
  read the screenshots and the verify reports, including the `contract_gaps` /
  `code_gaps` entries product-verify writes with `kind: "audience_leak"`.

**Anti-pattern contrast.** When a finding matches one of the three
anti-patterns in `${CLAUDE_PLUGIN_ROOT}/knowledge/consumer-maturity-patterns.md`
§B — The Compressed Admin Panel, The Concept Demo, Feature Checklist Design —
name it in `counterexample_or_comparison`.

**Taste filter.** A finding whose `observation` cannot fill all four of `who`,
`circumstance`, `task`, and `observed` with something concrete is not written
into the report. A lens with nothing concrete to say is `未查` or `有`, not a
vague blocker.

## Method

1. Build the evidence inventory first. Mark every expected artifact available
   or missing and record what each one can and cannot prove.
2. Read the experience direction as described in the Input Contract, and read
   `experience_priority.mode` from the bootstrap profile; record
   `direction.intent_ids`, `direction.acceptance`, and `direction.delegated`.
3. Walk the eight lenses in order against the stage's evidence and fill
   `lenses.*` with `有|缺|未查`, a one-sentence summary, and a confidence.
4. Turn each `缺` — and each contradiction found along the way — into a
   finding carrying `judgment_type`, `severity`, `confidence`, `observation`,
   `evidence_refs`, `counterexample_or_comparison`, and `repair_route`. Apply
   the taste filter before writing it.
5. Fill this stage's gate from the findings that qualify under Judgment Rules,
   leave the other stage's gate `[]`, and in the `runtime` stage mirror each
   `must_fix_before_release` entry into `experience_gaps[]`.
6. Route every repair to its owning skill through `repair_route` and
   `rerun_from_node_id`. Never rewrite a source contract from here.
7. Generate the Chinese HTML from the JSON, then write the review doc.

## Judgment Rules

- `contract_defect`: an artifact contradicts another artifact, a required
  artifact is missing, or a downstream contract cannot be satisfied. A
  `contract_gaps` entry with `kind == "unspecified_user_visible_decision"`, a
  settings item with no `audience`, and a non-`end-user` item appearing in an
  end-user interface spec are all `contract_defect`.
- `evidence_based_critique`: the critique depends on a screenshot, review page,
  or runtime report, and that evidence exists.
- `llm_judgment`: a reasoned, comparative, or preference-based judgment. Say
  why it is plausible and give a counterexample or comparison target.
- `insufficient_evidence`: the claim would need a screenshot, runtime report,
  or artifact that does not exist.
- A pure `llm_judgment` never enters `must_fix_before_implementation` or
  `must_fix_before_release`; it may only populate `recommended_iterations`.
- A gate entry is accepted only from a `contract_defect`, or from an
  `evidence_based_critique` with `confidence >= 0.8` whose `evidence_refs`
  point at a concrete artifact field, interface id, or screenshot path.
- Never use placeholder evidence. If a screenshot or runtime check could not
  run, declare it unverified.

## Review Doc

Every review also writes a human-readable summary into the project repository
at `docs/experience-review/<stage>.md`, overwriting the previous one so the
file is always the latest review. Fixed sections, in this order:

```text
# 体验评审 — <stage>
评审日期: <ISO-8601 with offset>
被评提交: <git sha | uncommitted | no-git>
评审方: <fresh-subagent | other-platform-cli>

## 结论
<overall_recommendation.decision> · <一句理由>
（体验方向为委托选定时在此注明）

## Must-fix
- <finding_id> · <镜头> · <观察> · <所属产物> · 状态 open

## 各镜头观察
onboarding（引导）: 有|缺|未查 · <一句观察>
process_feedback（过程反馈）: 有|缺|未查 · <一句观察>
next_step（下一步）: 有|缺|未查 · <一句观察>
state_consistency（状态一致）: 有|缺|未查 · <一句观察>
return_reason（回来理由）: 有|缺|未查 · <一句观察>
mainline（主线）: 有|缺|未查 · <一句观察>
direction_fidelity（方向忠实）: 有|缺|未查 · <一句观察>
audience_leak（受众泄漏）: 有|缺|未查 · <一句观察>

## 证据限制
- <缺了什么证据，因此哪条判断没做>
```

The summary must be self-sufficient. `/product-review` does not open
`.allforai/`, so each observation and each must-fix is a whole sentence that
stands on its own; a bare path pointing into `.allforai/` is not an
observation. The reviewing node must list `docs/experience-review/<stage>.md`
among its `exit_artifacts`, otherwise nothing guarantees the file is written.

## Automatic Validation

Before marking complete:

- Confirm the stage's `.json` and `.html` both exist under
  `.allforai/app-design/qa/`.
- Confirm `stage` matches the file-name suffix of the artifacts just written.
- Confirm `review_language` is `zh-CN` and every human-facing HTML string is
  Chinese.
- Confirm every lens key exists — `onboarding`, `process_feedback`,
  `next_step`, `state_consistency`, `return_reason`, `mainline`,
  `direction_fidelity`, `audience_leak` — and each carries `observation`,
  `summary`, and `confidence`, with no numeric score field.
- Confirm every finding carries `judgment_type`, `severity`, `confidence`, a
  four-field `observation`, `evidence_refs`, `counterexample_or_comparison`,
  and a `repair_route` with `rerun_from_node_id`.
- Confirm every `contract_defect` and `evidence_based_critique` references at
  least one available artifact, except when the finding is about a missing
  required artifact.
- Confirm every gate element appears in `findings`, and that no
  `llm_judgment`-only finding sits in `must_fix_before_implementation` or
  `must_fix_before_release`.
- Confirm the other stage's `must_fix_*` list is empty, and that in the
  `runtime` stage `experience_gaps` mirrors `must_fix_before_release` exactly.
- Confirm `docs/experience-review/<stage>.md` exists and its Must-fix section
  matches `gates`.

## Completion Conditions

Return `COMPLETED` when every required input existed, all eight lenses are
filled, every finding is evidence-typed with repair routing, and the review doc
is written.

Return `COMPLETED_WITH_LIMITS` when the critique is usable but optional
screenshots, visual reviews, or runtime reports are missing and are explicitly
represented as `insufficient_evidence` findings.

Return `UPSTREAM_DEFECT` when a required spec, the experience direction, or the
bootstrap profile is missing or malformed.

Return `FAILED_VALIDATION` when the outputs are missing, schema fields are
missing, the HTML is not Chinese, evidence-backed claims lack evidence, a gate
rests only on subjective judgment, or the reviewer authored the artifacts under
review.
