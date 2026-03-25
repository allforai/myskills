# Execution Playbook — Product Design 10-Phase Pipeline

> Full pipeline orchestration: concept -> map -> journey -> experience-map -> gate -> use-case -> feature-gap -> ui-design -> design-audit

## Pipeline Overview

```
Phase 0:  Artifact Detection + Scale Check + External Capability Probe
Phase 1:  product-concept (optional)
Phase 1.5: concept-baseline generation (auto)
Phase 2:  product-map (9 steps: profile -> roles -> tasks -> flows -> conflicts -> constraints -> output -> data-model -> view-objects -> validation)
Phase 3:  journey-emotion (LLM emotion annotation + human confirmation)
Phase 4:  experience-map (LLM design + validation loop) + interaction-gate
Phase 5:  Stitch decision point (visual design tooling check)
  |
  +-- Phases 6-8 can execute in parallel after Phase 5 --+
  |                                                       |
Phase 6:  use-case (happy/exception/boundary/e2e)         |
Phase 7:  feature-gap (task/screen/journey/flow/state)    |
Phase 8:  ui-design (style -> principles -> spec -> HTML) |
  |                                                       |
  +-------------------------------------------------------+
  |
Phase 9:  design-audit (trace + coverage + cross-check + pattern + behavioral + interaction-type)
```

## Phase Details

### Phase 0: Artifact Detection

Scan `.allforai/` to determine completion status of each phase. Also:
- Detect product scale (standard / large / super-large) by estimated roles and modules
- Probe external capabilities (OpenRouter, Stitch, Playwright, WebSearch)
- Output status dashboard

### Phase 1: product-concept

Skill: `./skills/product-concept.md`

Skip conditions: user specifies `skip: concept`, or resume mode with concept already complete.

Steps: problem discovery (first-principles) -> assumption zeroing (multi-model) -> competitive search -> role & value mapping (VPC) -> business model -> product mechanisms -> governance styles -> adversarial generation (multi-model) -> concept crystallization

Pipeline preferences collected in Step 3.5 (UI style, competitors, scope strategy, Stitch preference, infrastructure).

### Phase 1.5: concept-baseline generation

After concept verify loop passes, extract compact baseline from concept artifacts into `.allforai/product-concept/concept-baseline.json` (~2KB). This is consumed by all downstream skills as background context.

### Phase 2: product-map

Skill: `./skills/product-map.md`

Detailed steps defined in:
- `./docs/product-map/extraction-steps.md` (Step 0-2)
- `./docs/product-map/modeling-steps.md` (Step 3-6.5)
- `./docs/product-map/data-modeling-steps.md` (Step 7-8)
- `./docs/product-map/validation-steps.md` (Step 9)

Key outputs: role-profiles.json, task-inventory.json (split into basic + core), business-flows.json, entity-model.json, api-contracts.json, view-objects.json, experience-dna.json, product-map.json (summary with experience_priority).

When `experience_priority = consumer|mixed`, multi-model consumer experience completion runs after Step 2 (via OpenRouter MCP if available).

### Phase 3: journey-emotion

Skill: `./skills/journey-emotion.md`

LLM analyzes business-flow nodes to annotate emotion/intensity/risk/design_hint. Self-review loop (max 3 rounds) checks coverage, consistency, and closure. Human confirmation required in standard mode; auto-confirmed in pipeline auto-mode (except risk=critical nodes).

### Phase 4: experience-map + interaction-gate

**experience-map**: Skill `./skills/experience-map.md`

LLM freely designs screens based on all upstream inputs (tasks, data model, business flows, view objects, journey emotions, role profiles, experience priority). Validation loop checks task coverage, flow continuity, platform differences, emotion matching.

Detailed steps in:
- `./docs/experience-map/output-schema.md` (schema + design principles)
- `./docs/experience-map/generation-steps.md` (Steps 1-2)
- `./docs/experience-map/validation-steps.md` (Steps 3-4)

**interaction-gate**: Skill `./skills/interaction-gate.md`

4-dimension scoring (step_count, context_switches, wait_feedback, thumb_zone) per operation line. Lines below threshold require user decision. Scores written back to experience-map.json.

### Phase 5: Stitch Decision Point

Check Stitch MCP availability. If unavailable, present three options:
1. Upload design files
2. Skip visual review (record in pipeline-decisions as `stitch_skipped`)
3. Configure Stitch

### Phases 6-8: Parallel Execution

After Phase 5, the following three phases can execute in parallel (they share upstream dependencies but do not depend on each other):

| Phase | Skill | Key Output |
|-------|-------|------------|
| 6 use-case | `./skills/use-case.md` | use-case-tree.json + use-case-report.md |
| 7 feature-gap | `./skills/feature-gap.md` | gap-tasks.json + gap-report.md |
| 8 ui-design | `./skills/ui-design.md` | ui-design-spec.json + tokens.json + HTML previews |

All three skills read from product-map and experience-map artifacts. They write to separate `.allforai/` subdirectories with no conflicts.

### Phase 9: design-audit (Final Audit)

Skill: `./skills/design-audit.md`

Three-phase architecture:
- **Phase A (script, serial)**: Deterministic checks via `../../shared/scripts/product-design/gen_design_audit.py` -- trace, coverage, cross-check, fidelity, continuity, consumer maturity
- **Phase B (LLM, 3 parallel tasks)**: Semantic audits -- pattern consistency, behavioral consistency, interaction type consistency
- **Phase C (merge)**: Combine Phase A baseline + Phase B shards into final audit-report.json + audit-report.md

Detailed dimensions in `./docs/design-audit/audit-dimensions.md`.
Rules and protocols in `./docs/design-audit/fix-rules.md`.

## Verify Loop (All Phases)

Each phase follows a unified verify loop template:

```
loop (max 3 rounds):
  1. Run verification (script or LLM self-review)
  2. Check against upstream baseline:
     - 4D: conclusion correct? evidence? constraints? decision rationale?
     - 6V: user/business/tech/ux/data/risk perspectives
     - Closure: config/monitoring/exception/lifecycle/mapping/navigation
  3. Issues found -> auto-fix -> re-verify
     No issues -> proceed to next phase
```

Verification baseline chain:

| Phase | Current Artifact | Baseline (upstream) |
|-------|-----------------|-------------------|
| 1 concept | product-concept.json | user requirements |
| 2 product-map | task-inventory + business-flows | product-concept.json |
| 3 journey-emotion | journey-emotion-map.json | business-flows.json |
| 4 experience-map | experience-map.json | journey-emotion + task-inventory + entity-model |
| 5-7 use-case/gap/ui | respective outputs | task-inventory + experience-map + business-flows |

## Auto-Mode

Activates when `product-concept.json` contains `pipeline_preferences`.

Three-level checkpoint evaluation:

| Level | Condition | Behavior |
|-------|-----------|----------|
| ERROR | Required fields missing, references broken, task count = 0, required files absent | Pause and present details to user |
| WARNING | Recommended fields missing, coverage below expected, minor inconsistencies | Log to pipeline-decisions.json, auto-continue |
| PASS | All checks pass | Auto-continue with one-line summary |

All auto-mode decisions recorded in `.allforai/pipeline-decisions.json` for post-hoc review.

## Phase Transition Rules

1. **Zero-pause transitions**: Never ask "continue?" between phases. Checkpoint PASS -> load next skill immediately. Only ERROR-level issues may pause.
2. **Each phase loads its skill file**: Complete execution per skill workflow, no shortcuts.
3. **Checkpoints must verify**: Validate output existence and integrity after each phase.
4. **Read-only upstream**: Later phases report upstream issues but never auto-modify upstream artifacts.
5. **User can abort at any phase**: Save existing outputs, produce partial summary.
6. **Review is optional**: Users can run `/review` at any time to inspect artifacts. The pipeline never proactively asks if the user wants to review.
