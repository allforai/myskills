# Bootstrap planning Protocol

Read before designing `workflow.json`. This is the planning law. Node names below are *examples of closures*, not a menu.

See `docs/adr/0001-bootstrap-free-planning.md`.

## Free planning

Design the smallest node graph that achieves the user's goals for *this* project.

- Capabilities are reference, not a menu.
- Prefer fewer nodes with one primary outcome each.
- Parallelize siblings that only read a shared predecessor (`alignment_refs`); use `hard_blocked_by` only for true data dependencies.
- Goal combination order: reverse-concept → analyze → implement/translate/rebuild/create → demo → verify/tune/quality-checks → launch-prep.
- Separate outcome from route. When the user's named means (an engine, a module, a requested node) may not be the best route to the underlying product outcome, record it as a Phase A decision input with the alternative and let the human choose. Never silently swap the route.
  Exception, and the only one: art dimension is a pipeline capability limit, not a route. This pipeline produces 2D / 2.5D assets only because 3D assets cannot be generated; `dimension=3d` and skeletal-animation requests are remapped to 2D frame animation (see `bootstrap-art-pipeline.md`). That remap is never a Phase A option, but it is stated to the user once in the Phase A summary — a recorded remap that nobody was told about is still a silent swap.

## After the pipeline: user steps

See `docs/adr/0008-verdicts-leave-the-run-the-engine-is-shared.md`.

The graph ends where the author's evidence ends. Whether the delivery is *done* and
whether it is *good* are judged by a party that did not write it, so every workflow
carries, after its last node, the two entries the user types next:

```json
"user_steps": ["/cross-exam", "/product-review"]
```

- They are listed, never planned: no node is named after either, no node-spec invokes
  either, and no engine dispatches them. `validate_unattended_readiness.py` refuses a
  workflow that plans one as a node (`verdict_entry_planned_as_node`).
- The order is fixed and is the one CLAUDE.md's "Which entry for which situation" table
  gives: first "is it done", then "is it good". The planning summary and the completion
  text print the two steps and point at that table for the reason; they never restate it.
- The only exemption is a suppress rule (`suppress-rules.md`): a CLI or library-sdk
  project has no UI and no product to examine, so `user_steps` is `[]` and the summary
  says why. Any other project gets both steps; a goal that is "just implement" is not a
  reason to drop them.

For reconstruction and new-product routes, execute `product-intent-confirmation.md`
at interactive bootstrap/resume. Its journal-backed baseline, generated projection
and public gates apply before planning executable product work.

## Goal and requirement scope

Capture `bootstrap-profile.json.task_goal` from the current user request and
select `task_route` by its meaning: `local-change`, `product-reconstruction`, or
`new-product`. Ask a concise goal question only if needed. Do not derive the route
from `has_code`, missing documents, or the old capability goal list.

For local work, inspect only relevant code, documents and recorded decisions.
Capture goal, business rules and observable acceptance before planning dependent
work. A clear user request can itself supply confirmation; ask only for missing
or changed product choices. Existing decisions are reusable only for their
applicable scope and with actual user provenance. Legacy/code-derived records
without that provenance remain evidence; they do not require a full interview.

Use the existing product record if it exposes the requirement contract below;
otherwise keep a local requirement projection at
`.allforai/bootstrap/local-requirements.json`. This is scoped requirement input,
not a replacement decision journal or a second whole-product baseline. Preserve
old journal batches and concept files. When reusing a journal decision, retain
its original identity and source reference; never fabricate a new user decision.
Use `confirmation.reference` in the form
`.allforai/product-concept/decision-journal.json#<batch_id>/decisions/<zero-based-index>`
for canonical schema `1.0` journals. The selected batch must come from
`user_session` and contain an explicit choice; pending, removed or superseded
decisions cannot authorize the projection. A `supersedes` reference may use the
same full reference or its `<batch_id>/decisions/<index>` fragment.
The referenced decision must also record this projection: a decision carrying
the full `intent` payload must equal the requirement; a goal-only choice
(`chosen`/`rationale` without `intent`, the shape the Codex `journal` command
records) must match the requirement's `goal` and `confirmation.reason`, and even
then evidences the goal alone. Its scope, business rules and acceptance stay the
model's projection: the gates report `pending_requirement` for the consuming nodes
until the user confirms them, and `product_intent.py` `resume` presents the item
pending with `legacy_reuse` (evidenced `goal`; unconfirmed `scope`,
`business_rules`, `acceptance`) and its retained reference. A mismatched choice is
pending without `legacy_reuse`. One explicit `decide` `confirm` records the full
payload in a new journal batch, keeps the old reference as `prior_confirmation`,
leaves earlier batches and the file's revisions unchanged, and the gates pass
again without a session marker or plan rewrite. `resume` reads this file whenever
the profile has no `intent_session_path` and the route is not a product route;
`admit` still refuses to overwrite it.
All three public gates validate that source. The decision-input gate counts
the validated journal as consumed through the scoped requirement projection;
other gathered decision files still need consumers, including retained nodes
for historical work. Do not wire an unrelated journal merely to silence a gate.

Example of an explicitly confirmed local requirement (replace every example
value with the actual user request/decision):

```json
{
  "requirements": [{
    "id": "order-export",
    "revision": 1,
    "scope": ["orders"],
    "goal": "Export the current account's orders as CSV",
    "business_rules": ["Only the signed-in account's orders may be exported"],
    "acceptance": ["Another account's orders never appear in the CSV"],
    "status": "confirmed",
    "confirmation": {
      "source": "user",
      "reference": "<actual user turn or existing journal decision reference>",
      "decision_id": "<stable original decision identity>",
      "reason": "<recorded purpose or reason for this decision>"
    }
  }]
}
```

`goal` is non-empty text; `scope`, `business_rules` and `acceptance` are non-empty
arrays of concrete statements. An unfinished record has `status: pending` and
no invented confirmation. A changed requirement gets a new positive integer
revision with fresh confirmation, retaining earlier revisions. Do not edit
confirmed content in place or relabel code observations as user decisions.
User additions need no implementation evidence. Discussion does not change
product source. Validate proposed input before replacing any approved record;
interruption preserves the prior authority and leaves unanswered items pending.

In the profile write `task_scope: {areas: [...], requirement_refs: [...]}`.
Each reference is `{path, id, revision}` with a project-relative JSON path and
current requirement revision. Empty references leave local requirements or
product confirmation pending. `areas` name the relevant boundaries, and each
referenced requirement must apply to at least one of them. Product-reconstruction
and new-product continue their own product confirmation process; routing is not
product approval, and the local record does not replace full product discovery.

For each local requirement, freely design implementation, documentation and
verification responsibilities. Nodes may combine these obligations or divide
them across dependencies. Every new node in this scoped workflow, including
a prerequisite, must consume at least one in-scope requirement; absent or empty
references cannot authorize extra work. Retained unrelated completed branches
keep their historical contracts. On each consuming node emit `requirement_refs`,
`responsibilities` (the applicable entries from `implementation`, `documentation`,
`verification`), the reference paths in `decision_inputs`, and `source_inputs`:
the project-relative product source the node traces to, or explicit `[]` only
when no product source is relevant. The public gates refuse a scoped node that
omits or malforms this declaration; freshness is not opt-in. The Node-spec
mirrors these fields and explains the actual code boundary, relevant document
updates, acceptance evidence and repair owner. This is a responsibility contract,
not a fixed node menu. Audits inspect semantic adequacy; labels alone are not proof.

Preserve unrelated nodes, artifacts, decisions and transition history through
reconciliation. Never fill whole-product gaps during a local request. Apply
visual/runtime verification and suppress rules to the work actually requested.
Shared `product_intent.py` validates scope for bootstrap, decision-input and
unattended-readiness gates; copy it with those scripts. Failure returns to the
interactive prerequisite, with no prompt or inferred answer inside `/run`.

## Musts (Protocol)

1. **Visual acceptance before screenshot QA.** Any workflow that implements or verifies visible UI/runtime must produce visual acceptance criteria first. Downstream screenshot QA hard-blocks on that node. Per-screen archetype standards (map-like, list-like, board-like, combat-like, dialogue-like, shop-like, or other specialized screens) are generated from the project's concept, UI registry, art direction, scene flow, and runtime handoff into the project-local criteria artifact before `/run`; runtime visual QA must not invent them.
2. **QA repair loop.** Two or more QA/verify/smoke/visual/runtime nodes require a repair-and-revalidation loop (max 3 attempts) before closure. Follow `${CLAUDE_PLUGIN_ROOT}/skills/meta-orchestration/40-qa/execution-repair-loop/SKILL.md`. QA/verify/smoke/visual/runtime nodes classify findings as `code_gaps`, `test_gaps`, `asset_gaps`, `contract_gaps`, or `environment_blockers`; a blocker report with repairable `code_gaps` is not closure. After repair, rerun affected QA evidence before any closure node passes.
3. **Suppress rules.** After classification, apply `${CLAUDE_PLUGIN_ROOT}/knowledge/suppress-rules.md`. Emitting a suppressed node is a planning error.
4. **Verification honesty.** Node-specs follow `${CLAUDE_PLUGIN_ROOT}/knowledge/verification-protocol.md`. Existence is not completion when the artifact declares `blocked`, `placeholder`, or non-empty quality/effect gaps. This is quality-driven acceptance: reports may not use `existence_only`, `structure_only`, `function_only`, `not_good_enough`, or `quality_failed` as a passing state, and non-empty `quality_gaps`, `effect_gaps`, `experience_gaps`, `visual_quality_gaps`, or `perceptual_gaps` block production unless scope was explicitly lowered before `/run`.
5. **Maximum realism.** Real credentials ⇒ real services. Stubs only when credentials are absent.
6. **Every affected module gets a verifier** matching its role. Load `${CLAUDE_PLUGIN_ROOT}/knowledge/node-spec-template.md` plus the verification notes in engine-detection. Playwright is not a native-mobile or game-client test.
7. **Runtime knowledge.** When the detected game runtime has `${CLAUDE_PLUGIN_ROOT}/knowledge/engines/<runtime>.md`, read it before designing nodes and record which runtime node families it declares are covered or explicitly omitted (with reason) in a project-local runtime profile artifact. A game workflow with only scaffold/build/smoke nodes is incomplete for production or unattended goals.
8. **Creative quality gate (game projects).** Specialist contracts can all pass while the game still feels generic. After `game-design-finalize`, and again after the last art/UI/audio/frontend QA when goals include implementation, run `${CLAUDE_PLUGIN_ROOT}/skills/game-creative/40-qa/creative-quality-critique/SKILL.md`. `concept-acceptance` is `hard_blocked_by` it; `must_fix_*` findings route to the owning pack's repair loop.

## Game implementation handoff expansion

For `implement`, inspect
`.allforai/game-design/design/program-development-node-handoff.json` before
writing workflow nodes. If it contains `game_frontend`, expand the listed
frontend implementation/QA requirements into concrete downstream nodes that read
the `game-frontend` sub-skills. If it contains `game_2d_production`, expand the
listed `required_closure_skills` into concrete downstream nodes.

Do **not** hard-code 2D production node order in bootstrap. Declare
`expanders: ["expand_game_2d_production.py"]` and run:

```bash
python3 .allforai/bootstrap/scripts/expand_game_2d_production.py .
```

The expander is idempotent. If bootstrap cannot expand this handoff, mark the
downstream 2D implementation scope blocked; do not leave the
`game_2d_production` handoff as inert JSON. Preserve
`game-2d-production-closure-qa` via
`game-2d-production/40-qa/2d-production-closure-qa`.

Genre-tight extra validation belongs in a project-local
`<specialization_id>-2d-production` skill under
`.allforai/bootstrap/specialized-skills/`.

       **Game frontend handoff:** When generating `game-design-finalize`, require
       `.allforai/game-design/design/program-development-node-handoff.json` to
       include the `game_frontend` block from `game-design.md` §Conditional
       Sub-Skill Expansion Rules / Frontend handoff whenever the overall goal
       includes implementation. This does NOT create a game-design node for
       `game-frontend`. It tells downstream program/frontend nodes to invoke
       the `game-frontend` pack and preserve required QA skills, including
       `game-frontend/40-qa/runtime-gameplay-visual-acceptance`.

       **2D game production handoff:** When the selected game target is a 2D
       client/runtime and the overall goal includes implementation, require
       `.allforai/game-design/design/program-development-node-handoff.json` to
       include the `game_2d_production` block from `game-design.md`
       §Conditional Sub-Skill Expansion Rules / Frontend handoff. This does
       NOT create a game-design node for `game-2d-production`; it tells
       downstream program/frontend nodes to invoke the `game-2d-production`
       pack after approved art/UI/audio/frontend/runtime contracts exist and
       preserve `game-2d-production/40-qa/2d-production-closure-qa`.

Delegating node-specs must resolve every mapped sub-skill path to an existing
`${CLAUDE_PLUGIN_ROOT}/skills/<path>/SKILL.md` with `Input Contract`,
`Output Contract`, `Invocation Contract`, `Automatic Validation`, and
`Completion Conditions`. Missing path or section → `BOOTSTRAP_SUB_SKILL_MAPPING_INVALID`.

## Specialization

Follow `${CLAUDE_PLUGIN_ROOT}/knowledge/domains/game-genre-specialization.md`.
Write project-local skills under `.allforai/bootstrap/specialized-skills/`.
Each generated specialized skill must include:
`Input Contract`, `Output Contract`, `Invocation Contract`, `Automatic Validation`,
`Repair Routing`, and `Completion Conditions`.

## Unattended readiness

Write `.allforai/bootstrap/unattended-run-readiness-spec.json` with exact
commands, keys, MCP servers, QA/repair/closure node ids, and human decisions
that must already exist. `/run` begins with readiness validation.

### The coverage gate's repair loop

When the run policy may answer `on_needs_iteration: auto_fix_once` and the workflow carries the
concept-acceptance coverage gate, `required_repair_loops` declares a loop naming that gate in
`qa_node_ids`, and the workflow plans its two nodes: `<gate>-repair` (capability `implement`,
`hard_blocked_by: [<gate>]`, the one bounded repair) and `<gate>-rerun` (capability
`concept-acceptance`, `hard_blocked_by: [<gate>-repair, <gate>]`, the rerun that proves it). Without
the loop, `auto_fix_once` halts at run time as an unauthorized repair (ADR-0006) and the user cannot
see that the plan was the cause; the readiness gate refuses such a plan
(`missing_coverage_repair_loop`). `halt_with_report` and `accept` need no loop.

**UI screenshot + reviewer two visual review hard gate:**

Every verification node that exercises a user-facing UI MUST include screenshot
capture and reviewer two visual review in its node-spec. This applies to Web
Playwright, Electron, Tauri WebView, browser extensions, Flutter, iOS, Android,
React Native, HarmonyOS, and game clients with visible runtime scenes.

Required node-spec obligations:

- Capture screenshots for every tested critical state: launch, loaded screen,
  navigation target, primary form/action, success state, error/empty state, and
  any permission/offline state covered by the flow.
- Write a screenshot manifest:
  `.allforai/verify/ui-screenshot-manifest.json` or a node-specific equivalent
  under `.allforai/product-verify/` / `.allforai/visual-verify/`.
- After screenshots are captured, use the shared batch visual acceptance skill:
  `${CLAUDE_PLUGIN_ROOT}/skills/visual-qa/40-qa/batch-visual-acceptance/SKILL.md`
  and delegate visual inspection through
  `${CLAUDE_PLUGIN_ROOT}/skills/codex-cli-delegation/30-execute/codex-cli-task/SKILL.md`.
- Visual review is dual-reviewer (ADR-0003): reviewer one is a fresh-context sub-agent of the
  session; reviewer two is the other platform's CLI when it is installed and can open images,
  otherwise a second fresh-context sub-agent. Neither may be the context that produced the
  screenshots. The node must write both reviewers' reports plus reconciliation and closure audit:
  - `.allforai/verify/visual-review-2.json`
  - `.allforai/verify/visual-review-2.md`
  - `.allforai/verify/visual-review-1.json`
  - `.allforai/verify/visual-review-1.md`
  - `.allforai/verify/ui-visual-reconciliation.json`
  - `.allforai/verify/ui-visual-closure-audit.json`
  - `.allforai/verify/ui-visual-closure-audit.md`
- Both reviewers must check blank screens, loading stuck states,
  clipped/overlapped text, unreadable contrast, missing required content, broken
  navigation state, modal/keyboard obstruction, wrong language, and responsive
  layout breakage.
- reviewer one inspects the screenshots itself and writes its own review; it must
  not read the reviewer two report before doing so, and it must not skip its own review
  to save tokens. Blocking findings are the union of both reviews. reviewer one
  then performs reconciliation plus closure audit: report existence, inspected
  evidence paths, failure routing, repair execution, and rerun records.
- The node cannot pass when screenshots are missing, unreadable, stale, or when
  either reviewer reports blocker/major visual issues. Return
  `blocked_by_missing_screenshots`, `blocked_by_unreadable_screenshot`, or
  `failed_visual_review` instead. When the cross-platform CLI cannot run, record
  `missing_cross_platform_cli` in the visual model routing report and run reviewer two as a
  second fresh-context sub-agent; return `blocked_by_missing_second_review` only when two
  independent reports cannot be produced at all (ADR-0003).
- If the browser, emulator, simulator, device, or game runtime cannot launch,
  return `BLOCKED_ENV` / `FAILED_ENV`. Do not substitute DOM inspection, static
  code review, or manual prose for screenshot-based acceptance.
