---
name: game-creative
description: Internal bundled meta-skill module for cross-disciplinary game creative quality critique; use within generated bootstrap node-specs when this exact contract is selected.
---

# Game Creative Skill Pack

> Internal bundled sub-skill pack for meta-skill.
> Status: bundled, inactive, not wired.
> This directory is installed with meta-skill but is not automatically invoked by
> `/bootstrap` or `/run` until a node-spec explicitly reads a child skill path.

## Purpose

Game Creative evaluates whether game planning, art direction, UI, audio, and
frontend experience work together as a compelling player-facing product. It
does not replace the specialist `game-design`, `game-art`, `game-ui`,
`game-audio`, or `game-frontend` packs. It reads their outputs and produces a
cross-disciplinary critique with explicit evidence, confidence, and repair
routing.

Use this pack when the important question is not just "is the contract valid",
but "is this game likely to feel clear, attractive, memorable, and emotionally
coherent enough to justify the next production step".

## Current Children

| Layer | Child skill | Responsibility |
|---|---|---|
| `40-qa` | `creative-quality-critique` | Evidence-typed critique across hook, coherence, novelty, readability, emotional curve, production fit, market fit, audiovisual fit, and frontend feel. |

## Canonical Invocation Paths

Use these paths when a node-spec calls a child skill:

```text
${CLAUDE_PLUGIN_ROOT}/skills/game-creative/40-qa/creative-quality-critique/SKILL.md
```

## Boundary

Creative critique is not a deterministic compiler. The child skill must
separate four judgment types:

- `contract_defect`: deterministic contradiction, missing required artifact, or
  broken downstream contract.
- `evidence_based_critique`: critique backed by screenshots, HTML review
  pages, previews, audio samples, playable builds, or structured reports.
- `llm_judgment`: reasoned subjective judgment using design and art principles,
  references, and target audience fit.
- `insufficient_evidence`: the artifact set cannot support the claim.

Only `contract_defect` and high-confidence `evidence_based_critique` may create
hard blockers. `llm_judgment` may recommend iterations, focus tests, or
upstream repairs, but must not masquerade as objective validation.

## Shared Outputs

Creative critique writes under:

```text
.allforai/game-creative/
```

Reports must be in Chinese by default when intended for human review, while
machine-readable keys remain stable English identifiers.

## Layering Rules

Game Creative is normally late-stage QA and may read earlier planning,
generation, import, runtime, and approval evidence. It must not mutate source
contracts directly. Instead, it routes repairs back to the owning skill:

```text
game-design -> game-art -> game-ui -> game-audio -> game-frontend -> game-creative
```

If required evidence is missing, report `insufficient_evidence` and name the
upstream artifact that must be produced. Do not substitute static review for a
runtime, screenshot, audio, or import check when the claim depends on that
evidence.
