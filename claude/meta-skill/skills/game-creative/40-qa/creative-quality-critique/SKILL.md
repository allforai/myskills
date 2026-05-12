---
name: creative-quality-critique
description: Evaluate cross-disciplinary game creative quality with evidence-typed findings, Chinese review HTML, repair routing, and non-fake-objective scoring.
---

# Creative Quality Critique

## Purpose

Evaluate the upper-limit quality of a game's concept, design, art direction,
UI, audio, and playable presentation. This skill exists because specialist
contracts can all pass while the game still feels generic, confusing,
unattractive, emotionally flat, or mismatched with its target audience.

The output is a critique and repair routing artifact. It is not a substitute
for specialist generation, runtime import, or human taste approval.

## Input Contract

Read every available artifact that applies to the current project. Missing
optional artifacts must be recorded as `insufficient_evidence` instead of being
silently ignored.

| Input | Required | Purpose |
|---|---:|---|
| `.allforai/game-design/design/game-design-doc.json` | yes | Product concept, target player, pillars, loop, systems, content, and downstream ownership. |
| `.allforai/game-design/review-dashboard.html` | no | Human-facing approval status and design review context. |
| `.allforai/game-design/design/art-input-handoff.json` | no | Consolidated product-to-art input and art production priorities. |
| `.allforai/game-design/design/program-development-node-handoff.json` | no | Program-facing design handoff and implementation node expectations. |
| `.allforai/game-art/design/art-direction-input-contract.json` | no | Art input contract including human preferences and runtime constraints. |
| `.allforai/game-art/design/art-concept-validation.json` | no | Art concept alignment gate and unresolved visual risks. |
| `.allforai/game-art/design/visual-style-tokens.json` | no | Palette, shape, camera, material, typography, and motion style rules. |
| `.allforai/game-art/qa/art-preview-qa.json` | no | Visual QA issues and repair routes. |
| `.allforai/game-runtime/art/engine-ready-art-manifest.json` | no | Program-facing art output and import readiness. |
| `.allforai/game-ui/qa/ui-review.json` | no | UI clarity, hierarchy, responsiveness, and gameplay fit evidence. |
| `.allforai/game-audio/qa/audio-review.json` | no | BGM/SFX mood, timing, loop, and mix evidence. |
| `.allforai/game-frontend/qa/runtime-architecture-qa.json` | no | Frontend implementation fit and missing runtime evidence. |
| `.allforai/game-frontend/qa/playable-client-smoke.json` | no | Playable browser/runtime smoke result when available. |
| `.allforai/game-frontend/screenshots/` | no | Screenshot evidence for layout, readability, first-look appeal, and promise-to-product fit. |
| `.allforai/approval/approval-records.json` | no | Current approval state and unresolved human comments. |

If a project uses different artifact names, accept them only when the invoking
node supplies a clear mapping. Preserve the normalized output schema below.

## Output Contract

Write:

```text
.allforai/game-creative/creative-quality-critique.json
.allforai/game-creative/creative-quality-critique.html
```

The JSON must contain:

```json
{
  "schema_version": "1.0",
  "status": "COMPLETED|COMPLETED_WITH_LIMITS|FAILED_VALIDATION|UPSTREAM_DEFECT",
  "project_id": "string",
  "review_language": "zh-CN",
  "evidence_inventory": [
    {
      "artifact_path": ".allforai/...",
      "artifact_type": "json|html|image|audio|video|runtime_report|directory",
      "available": true,
      "used_for": ["hook_score"],
      "limitations": []
    }
  ],
  "scores": {
    "hook_score": {"score": 0, "confidence": 0.0, "summary": "string"},
    "coherence_score": {"score": 0, "confidence": 0.0, "summary": "string"},
    "novelty_score": {"score": 0, "confidence": 0.0, "summary": "string"},
    "readability_score": {"score": 0, "confidence": 0.0, "summary": "string"},
    "emotional_curve_score": {"score": 0, "confidence": 0.0, "summary": "string"},
    "production_fit_score": {"score": 0, "confidence": 0.0, "summary": "string"},
    "market_fit_score": {"score": 0, "confidence": 0.0, "summary": "string"},
    "audiovisual_sync_score": {"score": 0, "confidence": 0.0, "summary": "string"},
    "frontend_experience_score": {"score": 0, "confidence": 0.0, "summary": "string"}
  },
  "findings": [
    {
      "finding_id": "creative-001",
      "dimension": "hook|coherence|novelty|readability|emotion|production_fit|market_fit|audiovisual_sync|frontend_experience",
      "judgment_type": "contract_defect|evidence_based_critique|llm_judgment|insufficient_evidence",
      "severity": "blocker|major|minor|note",
      "confidence": 0.0,
      "claim": "string",
      "reasoning": "string",
      "evidence_refs": [".allforai/..."],
      "counterexample_or_comparison": "string",
      "repair_route": {
        "owner_skill": "game-design|game-art|game-ui|game-audio|game-frontend|bootstrap",
        "owner_artifact": ".allforai/...",
        "requested_change": "string",
        "rerun_from_node_id": "string"
      },
      "blocks": ["must_fix_before_art_gen"]
    }
  ],
  "gates": {
    "must_fix_before_art_gen": [],
    "must_fix_before_frontend": [],
    "must_fix_before_release": [],
    "recommended_iterations": []
  },
  "overall_recommendation": {
    "decision": "proceed|iterate_before_generation|iterate_before_frontend|iterate_before_release|blocked_by_missing_evidence",
    "rationale": "string",
    "top_repairs": []
  }
}
```

Score scale is 0-5:

- `0`: missing or broken.
- `1`: present but weak or incoherent.
- `2`: usable but generic, unclear, or fragile.
- `3`: solid baseline with known risks.
- `4`: strong and differentiated.
- `5`: unusually strong for the target scope and audience.

The HTML must be human-readable Chinese and show:

- score summary with confidence;
- evidence inventory and missing evidence;
- findings grouped by repair owner;
- blockers separated from recommended iterations;
- links or relative paths to screenshots, HTML pages, previews, audio samples,
  and source JSON where available.

## Invocation Contract

```json
{
  "skill": "game-creative/creative-quality-critique",
  "mode": "critique_validate",
  "input_paths": {
    "game_design_doc": ".allforai/game-design/design/game-design-doc.json",
    "approval_records": ".allforai/approval/approval-records.json",
    "art_handoff": ".allforai/game-design/design/art-input-handoff.json",
    "art_concept_validation": ".allforai/game-art/design/art-concept-validation.json",
    "engine_ready_art_manifest": ".allforai/game-runtime/art/engine-ready-art-manifest.json",
    "ui_review": ".allforai/game-ui/qa/ui-review.json",
    "audio_review": ".allforai/game-audio/qa/audio-review.json",
    "frontend_runtime_qa": ".allforai/game-frontend/qa/runtime-architecture-qa.json",
    "frontend_screenshots": ".allforai/game-frontend/screenshots/"
  },
  "output_root": ".allforai/game-creative/",
  "outputs": {
    "json": ".allforai/game-creative/creative-quality-critique.json",
    "html": ".allforai/game-creative/creative-quality-critique.html"
  }
}
```

## Method

1. Build the evidence inventory first. Mark every expected artifact as
   available or missing, and record what each artifact can and cannot prove.
2. Extract the product promise: target player, genre mix, emotional promise,
   core loop, first-session goal, visual hook, audio mood, platform, session
   length, production constraints, and approval comments.
3. Evaluate design quality:
   - `hook_score`: whether the first 10 seconds and first screenshot convey a
     desirable reason to play.
   - `coherence_score`: whether pillars, mechanics, rewards, art, UI, and audio
     reinforce the same promise.
   - `novelty_score`: whether the game has a specific twist, pairing, or
     presentation angle beyond genre defaults.
   - `emotional_curve_score`: whether tension, relief, mastery, curiosity, and
     reward are intentionally placed.
   - `market_fit_score`: whether scope, audience expectation, platform behavior,
     and monetization or retention assumptions match.
4. Evaluate presentation quality:
   - `readability_score`: silhouette, small-size icons, tile/piece distinction,
     text hierarchy, contrast, safe area, animation timing, and feedback clarity.
   - `production_fit_score`: whether the proposed quality bar is feasible with
     available tools, asset pipeline, engine import, and budget.
   - `audiovisual_sync_score`: whether music/SFX/VFX/UI feedback support the
     same emotional and mechanical beats.
   - `frontend_experience_score`: whether the playable surface, input feel,
     loading, camera, HUD, and responsiveness support the intended experience.
5. For each weak score or contradiction, create a finding. Every finding must
   include `judgment_type`, `severity`, `confidence`, `evidence_refs`,
   `counterexample_or_comparison`, and `repair_route`.
6. Route repairs to the owner skill. Do not directly rewrite source artifacts.
7. Generate the Chinese HTML report from the JSON, preserving stable English
   identifiers in code-like fields.

## Judgment Rules

- Use `contract_defect` when an artifact contradicts another artifact, an owner
  artifact is missing after being declared required, or a downstream contract
  cannot be satisfied.
- Use `evidence_based_critique` when the critique depends on visible, audible,
  playable, or import evidence and that evidence exists.
- Use `llm_judgment` when the critique is creative, comparative, or preference
  based. State why the judgment is plausible and give a counterexample or
  comparison target.
- Use `insufficient_evidence` when a claim would require a screenshot, audio
  sample, runtime report, import check, or approval record that does not exist.
- Never convert a pure `llm_judgment` into a hard blocker. It may populate
  `recommended_iterations`, but `must_fix_before_art_gen`,
  `must_fix_before_frontend`, and `must_fix_before_release` require
  `contract_defect` or high-confidence `evidence_based_critique`.
- Do not use placeholder evidence. If a runtime, screenshot, audio, or import
  check cannot run, declare it unverified.

## Automatic Validation

Before marking complete:

- Confirm `.allforai/game-creative/creative-quality-critique.json` and
  `.allforai/game-creative/creative-quality-critique.html` exist.
- Confirm `review_language` is `zh-CN` and all human-facing HTML text is
  Chinese.
- Confirm every score exists: `hook_score`, `coherence_score`,
  `novelty_score`, `readability_score`, `emotional_curve_score`,
  `production_fit_score`, `market_fit_score`, `audiovisual_sync_score`, and
  `frontend_experience_score`.
- Confirm every score has `score`, `confidence`, and `summary`.
- Confirm every finding has `judgment_type`, `severity`, `confidence`,
  `evidence_refs`, `counterexample_or_comparison`, and `repair_route`.
- Confirm every `evidence_based_critique` and `contract_defect` references at
  least one available evidence artifact, except when the finding itself is
  about a missing required artifact.
- Confirm every gate item appears in `findings`.
- Confirm no `llm_judgment` appears in `must_fix_before_art_gen`,
  `must_fix_before_frontend`, or `must_fix_before_release` unless paired with a
  separate blocking `contract_defect` or `evidence_based_critique` finding.

## Completion Conditions

Return `COMPLETED` when all required baseline artifacts exist, all scores are
present, and every finding is evidence-typed with repair routing.

Return `COMPLETED_WITH_LIMITS` when the critique is usable but important
screenshots, audio samples, playable reports, import reports, or approval
records are missing and explicitly represented as `insufficient_evidence`.

Return `UPSTREAM_DEFECT` when the game-design baseline or required mapping is
missing or malformed.

Return `FAILED_VALIDATION` when the output files are missing, schema fields are
missing, HTML is not Chinese, evidence-backed claims lack evidence, or hard
gates are based only on subjective LLM judgment.
