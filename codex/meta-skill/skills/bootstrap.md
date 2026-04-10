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

### 0. Task Capture Before Generation

Before generating any bootstrap artifacts, capture the user's concrete task goal for this run.

Rules:

- if the invoking message already contains a clear goal, treat that as the bootstrap task goal
- if the goal is missing or too vague, ask one concise plain-text question before generating artifacts
- do not let `flow.py` become the first place where the real task goal appears
- the captured task goal must shape workflow design, specialization detection, and node selection
- write the captured task goal into `.allforai/bootstrap/bootstrap-profile.json`

For replication and migration work, task capture must also classify fidelity intent before workflow generation.

Minimum classification fields to record in `.allforai/bootstrap/bootstrap-profile.json` when the project is a reproduction / port / migration:

- `source_platform`: `mobile | desktop | web | mixed | unknown`
- `ui_fidelity_mode`: `none | structural | visual | pixel_like`
- `interaction_fidelity`: `source_native | platform_adapted`
- `design_freedom`: `none | constrained | moderate`

Classification rules:

- if the user asks for `复刻`, `还原`, `faithful`, `像原版`, `高还原`, or similar, do not silently downgrade the request into generic feature parity
- if the source product is primarily mobile, default `source_platform = mobile` unless strong evidence contradicts it
- if the user wants a high-fidelity client rewrite and does not explicitly permit redesign, default:
  - `ui_fidelity_mode = visual`
  - `interaction_fidelity = source_native`
  - `design_freedom = none`
- when fidelity intent is still ambiguous, ask one concise follow-up before generation rather than letting downstream nodes guess
- if the user explicitly names source UI structure, interaction paths, visual hierarchy, or forbids browser-style redesign, preserve that wording in `task_goal` instead of narrowing it to only a playable slice

For high-fidelity replication, bootstrap must also record completion semantics in `.allforai/bootstrap/bootstrap-profile.json`:

- `completion_mode`: `slice_based | goal_based`
- `goal_acceptance_threshold`: `core_flow_only | major_surface_fidelity | full_requested_scope`

Default rules:

- if the user asks for faithful or high-fidelity reproduction, default `completion_mode = goal_based`
- if the user asks for faithful or high-fidelity reproduction, default `goal_acceptance_threshold = major_surface_fidelity`
- do not silently downgrade goal completion to "current slice accepted" unless the user explicitly asks to work slice-by-slice

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

Artifact placement rule:

- required node completion artifacts must live under `.allforai/bootstrap/`
- prefer `.allforai/bootstrap/records/` for node run records and `.allforai/bootstrap/artifacts/` for generated execution outputs
- `docs/bootstrap/` is a project documentation surface, not the canonical workflow completion surface
- generated workflows may update `docs/bootstrap/` as an optional mirror or long-lived project document, but `docs/bootstrap/*` must not be the only `exit_artifacts` used to decide node completion
- if a repository already contains `docs/bootstrap/*`, treat those files as evidence inputs unless the node also emits a fresh `.allforai/bootstrap/*` completion artifact for the current run

Goal-completion rule:

- for `completion_mode = goal_based`, bootstrap must generate workflow logic that distinguishes node completion from user-goal completion
- the workflow may mark a node or a slice complete while still requiring follow-on slices
- acceptance artifacts must explicitly say whether the overall user goal is done or whether another slice is required

Generation rule:

- materialize `../knowledge/flow-template.py` into `.allforai/codex/flow.py`
- the generated file must invoke `codex exec --dangerously-bypass-approvals-and-sandbox`
- it should work with zero arguments by default
- it may accept legacy positional arguments `<goal> <max_iterations>` for compatibility, but must not require them
- when no goal argument is provided, it should default to the captured bootstrap task goal from `.allforai/bootstrap/bootstrap-profile.json`
- it must treat `workflow.json` plus `transition_log` as the runtime source of truth
- after 3 consecutive failures on the same node, it must stop retries, run diagnosis, and record `diagnosis_history`
- after 5 consecutive transitions with no new artifacts, it must stop instead of looping forever

### 5. User Invocation Text

When the canonical protocol tells the user to run `/run [goal]`, adapt the instruction to:

- use the generated Codex run entry at `.codex/commands/run.md`
- invoke it through Codex's command mechanism in the target project
- prefer keeping the main task goal fixed at bootstrap time instead of introducing it only during run time

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

### 7b. Replication / Migration Specialization

For projects whose primary goal is to reproduce or port an existing system:

- read `../knowledge/replication-specialization.md`
- detect whether the project is actually a replication / migration workflow
- if yes, inject the replication responsibility floor during workflow planning

Important:

- do not let the workflow collapse into a long chain of planning-only nodes
- after the rewrite boundary is clear, prefer direct parity and implementation nodes
- if one runtime is explicitly stable, do not make rewriting it the center of the workflow
- if a legacy evidence source exists, make the source-to-target parity relationship explicit
- if `source_platform = mobile` and `ui_fidelity_mode != none`, do not collapse UI fidelity into a generic browser-native or desktop-native overlay task
- if `design_freedom = none`, generated UI nodes must treat source UI evidence as the baseline and must not reinterpret the information architecture as a fresh product design exercise
- node count and node names remain LLM-designed, but the required responsibilities may not be merged away into a single generic runtime-parity node when fidelity is a core user constraint
- if `completion_mode = goal_based`, do not end the workflow after a single accepted slice when major user-facing fidelity surfaces still remain below the requested threshold

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
- prefer generating `product-summary.json` during bootstrap itself when the evidence is already obvious from repository docs and current artifacts
- do not spend a mainline workflow node on product inference if it does not unblock the next implementation or verification decision
- it should describe user-facing systems, not just tech stacks
- if confidence is low, emit open questions instead of pretending certainty
- in fidelity-oriented replication projects with strong existing parity docs, product inference is supporting context, not a primary execution milestone

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

For UI-related replication nodes, `## Spec` must additionally include:

- source UI evidence paths or surfaces
- source platform assumptions
- explicit fidelity constraints
- forbidden redesigns
- acceptance by comparison, not just by feature existence

For replication workflows where `source_platform = mobile` and `ui_fidelity_mode != none`, the generated node-spec set as a whole must preserve three distinct responsibilities:

1. source UI evidence capture or refresh
2. source-led UI fidelity implementation
3. UI fidelity verification

These responsibilities may be merged only when the resulting node-spec still contains explicit acceptance criteria and task steps for all three. They may not disappear into a generic runtime-validation or gameplay-port node.

When the repository already contains current parity reports, validation docs, or acceptance artifacts that describe the present state with enough fidelity:

- do not generate extra baseline-preservation nodes whose only purpose is to restate or re-freeze the current state
- instead, treat those existing artifacts as evidence inputs for the next repair, implementation, verification, or acceptance nodes
- only emit a dedicated baseline-refresh node if the existing artifacts are clearly stale, contradictory, or missing the information needed to execute the next slice safely

For all generated workflows:

- every node must have at least one required completion artifact under `.allforai/bootstrap/`
- if a node also updates `docs/bootstrap/*`, list those as secondary outputs in the node-spec body, not as the only completion contract
- avoid reusing pre-existing project docs as the sole completion signal for a new workflow run

For goal-based replication workflows:

- include an acceptance node that evaluates overall goal completion, not only the current slice
- if that acceptance node finds high-priority fidelity gaps above the requested threshold, the workflow must continue with another repair or fidelity slice rather than terminating as fully done
- acceptance nodes may summarize a completed slice, but they must also state whether the user goal remains open

For UI-related replication nodes, `## Task` must require this order:

1. capture or read source UI evidence
2. compare source structure and interactions against the target
3. implement the selected fidelity slice
4. record residual deviations explicitly

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
- every node in `workflow.json` has at least one `exit_artifact` rooted under `.allforai/bootstrap/`

Also verify the bootstrap profile captures the task intent:

- `.allforai/bootstrap/bootstrap-profile.json` contains a non-empty task goal field
- the workflow node goals are consistent with that captured task goal
- replication workflows record fidelity intent fields when source reproduction is the main objective
- high-fidelity reproduction workflows do not narrow the task goal from source-faithful reproduction into only "playable", "usable", or "browser-native" language unless the user explicitly requested that tradeoff
- high-fidelity reproduction workflows record `completion_mode = goal_based` unless the user explicitly chose slice-based execution

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

- if `source_platform = mobile` and `ui_fidelity_mode != none`, the workflow contains explicit UI evidence capture or UI fidelity verification responsibilities
- if `design_freedom = none`, no UI implementation node is framed as open-ended redesign, browser-native reinterpretation, or desktop-first adaptation
- if `source_platform = mobile` and `ui_fidelity_mode != none`, UI evidence, UI implementation, and UI verification responsibilities all exist as distinct obligations even if the LLM chooses different node counts or names

- the domain's minimum responsibility floor exists in the generated workflow

For replication / migration workflows, also verify:

- at least one node locks the rewrite boundary and evidence source
- at least one node maps legacy evidence to target surfaces
- at least one implementation-oriented parity node exists
- at least one runtime or behavioral port node exists
- at least one local runnable validation node exists
- the workflow is not composed entirely of planning / audit nodes
- if parity reports and validation artifacts already exist, the workflow does not spend multiple early nodes merely preserving baseline documents before entering the next repair or fidelity slice
- `docs/bootstrap/*` files may appear as evidence inputs or optional mirrored outputs, but they are not the sole node completion artifacts
- if `completion_mode = goal_based`, acceptance logic cannot mark the workflow fully done while major requested fidelity surfaces still remain explicitly open
