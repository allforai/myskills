# Game Production Subskills Consistency Spec

## Goal

Complete a coherent set of bundled, inactive, meta-skill subskills for game
production. Each subskill must be callable by future node-specs without relying
on conversation state, and every skill must define stable inputs, outputs,
invocation, automatic validation, and completion conditions.

## Shared Rules

Every new subskill must include:
- `Input Contract`
- `Output Contract`
- `Invocation Contract`
- `Automatic Validation`
- `Completion Conditions`

Every asset-producing skill must connect to the shared contracts when relevant:
- `.allforai/game-design/asset-registry.json`
- `.allforai/game-design/ui/ui-registry.json`
- `.allforai/game-design/art-style-guide.json`
- `game-art/30-generate/image-generation-contract/SKILL.md`

Generation skills must treat generated assets as provisional until validated.
Downstream failures that point to generated images must route feedback through
`image-generation-contract` before downstream workarounds are accepted.

## Task Checklist

### Game Art

- [x] Add `20-spec/visual-style-tokens`
- [x] Add `30-generate/background-generation`
- [x] Add `30-generate/prop-generation`
- [x] Add `30-generate/portrait-generation`
- [x] Add `30-generate/item-art-generation`
- [x] Add `20-spec/frame-animation-spec`
- [x] Add `30-generate/frame-animation-generation`
- [x] Add `30-generate/expression-set-generation`
- [x] Add `40-qa/art-preview-qa`
- [x] Add `40-qa/atlas-packaging`
- [x] Add `40-qa/runtime-import-check`
- [x] Update `game-art/SKILL.md`

### Game Level

- [x] Add `game-level/SKILL.md`
- [x] Add `00-env/level-registry`
- [x] Add `10-design/level-flow-design`
- [x] Add `20-spec/level-layout-spec`
- [x] Add `30-generate/level-blockout-generation`
- [x] Add `40-qa/level-playability-qa`

### Game Audio

- [x] Add `game-audio/SKILL.md`
- [x] Add `00-env/audio-registry`
- [x] Add `10-design/audio-style-design`
- [x] Add `20-spec/sfx-spec`
- [x] Add `20-spec/music-cue-spec`
- [x] Add `30-generate/sfx-generation`
- [x] Add `30-generate/music-prompt-generation`
- [x] Add `40-qa/audio-loudness-qa`

### Game Narrative

- [x] Add `game-narrative/SKILL.md`
- [x] Add `10-design/narrative-tone-design`
- [x] Add `20-spec/dialogue-spec`
- [x] Add `20-spec/quest-text-spec`
- [x] Add `30-generate/dialogue-generation`
- [x] Add `40-qa/text-consistency-qa`

### Game Systems

- [x] Add `game-systems/SKILL.md`
- [x] Add `10-design/core-loop-design`
- [x] Add `20-spec/economy-spec`
- [x] Add `20-spec/progression-spec`
- [x] Add `20-spec/combat-spec`
- [x] Add `40-qa/balance-sanity-qa`

## Completion Definition

The task is complete when:
- all checklist items above have corresponding `SKILL.md` files,
- all new child skills contain the five standard contract sections,
- top-level pack files list canonical invocation paths,
- image-backed art skills reference `image-generation-contract`,
- consistency checks report no missing standard sections.
