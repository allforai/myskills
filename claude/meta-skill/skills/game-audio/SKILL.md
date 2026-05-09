# Game Audio Skill Pack

> Internal bundled sub-skill pack for meta-skill. Status: bundled, inactive, not wired.

## Purpose

Game Audio owns sound and music planning/generation contracts. It consumes game
events, UI events, narrative tone, and style direction.

## Current Children

| Layer | Child skill | Responsibility |
|---|---|---|
| `00-env` | `audio-registry` | Audio IDs, paths, states, owners, consumers. |
| `10-design` | `audio-style-design` | Sonic palette, mood, instrumentation, mix direction. |
| `20-spec` | `sfx-spec` | Event SFX semantics, timing, layers, variants, loudness target. |
| `20-spec` | `music-cue-spec` | Music cues, loops, transitions, stems, states. |
| `30-generate` | `sfx-generation` | SFX prompts/specs, generated/registered files, validation. |
| `30-generate` | `music-prompt-generation` | Music prompt/stem specs and generation manifest. |
| `40-qa` | `audio-loudness-qa` | Loudness, clipping, duration, loop, and mix validation. |

## Canonical Invocation Paths

```text
${CLAUDE_PLUGIN_ROOT}/skills/game-audio/00-env/audio-registry/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-audio/10-design/audio-style-design/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-audio/20-spec/sfx-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-audio/20-spec/music-cue-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-audio/30-generate/sfx-generation/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-audio/30-generate/music-prompt-generation/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-audio/40-qa/audio-loudness-qa/SKILL.md
```

## Layering Rules

Dependencies flow from earlier numbered layers to later numbered layers only.
