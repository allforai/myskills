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

## Musts (Protocol)

1. **Visual acceptance before screenshot QA.** Any workflow that implements or verifies visible UI/runtime must produce visual acceptance criteria first. Downstream screenshot QA hard-blocks on that node. Per-screen archetype standards (map-like, list-like, board-like, combat-like, dialogue-like, shop-like, or other specialized screens) are generated from the project's concept, UI registry, art direction, scene flow, and runtime handoff into the project-local criteria artifact before `/run`; runtime visual QA must not invent them.
2. **QA repair loop.** Two or more QA/verify/smoke/visual/runtime nodes require a repair-and-revalidation loop (max 3 attempts) before closure. Follow `${CLAUDE_PLUGIN_ROOT}/skills/meta-orchestration/40-qa/execution-repair-loop/SKILL.md`. QA/verify/smoke/visual/runtime nodes classify findings as `code_gaps`, `test_gaps`, `asset_gaps`, `contract_gaps`, or `environment_blockers`; a blocker report with repairable `code_gaps` is not closure. After repair, rerun affected QA evidence before any closure node passes.
3. **Suppress rules.** After classification, apply `${CLAUDE_PLUGIN_ROOT}/knowledge/suppress-rules.md`. Emitting a suppressed node is a planning error.
4. **Verification honesty.** Node-specs follow `${CLAUDE_PLUGIN_ROOT}/knowledge/verification-protocol.md`. Existence is not completion when the artifact declares `blocked`, `placeholder`, or non-empty quality/effect gaps. This is quality-driven acceptance: reports may not use `existence_only`, `structure_only`, `function_only`, `not_good_enough`, or `quality_failed` as a passing state, and non-empty `quality_gaps`, `effect_gaps`, `experience_gaps`, `visual_quality_gaps`, or `perceptual_gaps` block production unless scope was explicitly lowered before `/run`.
5. **Maximum realism.** Real credentials ⇒ real services. Stubs only when credentials are absent.
6. **Every module gets a verifier** matching its role. Load `${CLAUDE_PLUGIN_ROOT}/knowledge/node-spec-template.md` plus the verification notes in engine-detection. Playwright is not a native-mobile or game-client test.
7. **Runtime knowledge.** When the detected game runtime has `${CLAUDE_PLUGIN_ROOT}/knowledge/engines/<runtime>.md`, read it before designing nodes and record which runtime node families it declares are covered or explicitly omitted (with reason) in a project-local runtime profile artifact. A game workflow with only scaffold/build/smoke nodes is incomplete for production or unattended goals.

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

**UI screenshot + Codex CLI visual review hard gate:**

Every verification node that exercises a user-facing UI MUST include screenshot
capture and Codex CLI visual review in its node-spec. This applies to Web
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
- Visual review is dual-reviewer. The node must write both reviewers' reports
  plus reconciliation and closure audit:
  - `.allforai/verify/codex-ui-visual-review.json`
  - `.allforai/verify/codex-ui-visual-review.md`
  - `.allforai/verify/claude-code-visual-review.json`
  - `.allforai/verify/claude-code-visual-review.md`
  - `.allforai/verify/ui-visual-reconciliation.json`
  - `.allforai/verify/ui-visual-closure-audit.json`
  - `.allforai/verify/ui-visual-closure-audit.md`
- Both reviewers must check blank screens, loading stuck states,
  clipped/overlapped text, unreadable contrast, missing required content, broken
  navigation state, modal/keyboard obstruction, wrong language, and responsive
  layout breakage.
- Claude Code inspects the screenshots itself and writes its own review; it must
  not read the Codex report before doing so, and it must not skip its own review
  to save tokens. Blocking findings are the union of both reviews. Claude Code
  then performs reconciliation plus closure audit: report existence, inspected
  evidence paths, failure routing, repair execution, and rerun records.
- The node cannot pass when screenshots are missing, unreadable, stale, or when
  either reviewer reports blocker/major visual issues. Return
  `blocked_by_missing_screenshots`, `blocked_by_unreadable_screenshot`, or
  `failed_visual_review` instead. Return `blocked_by_missing_codex_cli` when
  Codex CLI cannot run.
- If the browser, emulator, simulator, device, or game runtime cannot launch,
  return `BLOCKED_ENV` / `FAILED_ENV`. Do not substitute DOM inspection, static
  code review, or manual prose for screenshot-based acceptance.

