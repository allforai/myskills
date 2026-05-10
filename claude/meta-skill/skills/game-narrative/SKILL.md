# Game Narrative Skill Pack

> Internal bundled sub-skill pack for meta-skill. Status: bundled, inactive, not wired.

## Purpose

Game Narrative owns tone, dialogue, quest text, tutorial text, and consistency QA
for games that need written content.

## Current Children

| Layer | Child skill | Responsibility |
|---|---|---|
| `10-design` | `narrative-tone-design` | Voice, tone, world language, character voice rules. |
| `10-design` | `world-bible-spec` | World rules, factions, locations, terminology, tone, and constraints. |
| `10-design` | `character-arc-spec` | Character roles, motivations, arcs, relationships, voice, and portrait needs. |
| `20-spec` | `story-structure-spec` | Acts, beats, branches, convergence, endings, and emotional pacing. |
| `20-spec` | `narrative-event-trigger-spec` | Story/quest triggers, flags, variables, conditions, and runtime handoff. |
| `20-spec` | `dialogue-spec` | Dialogue structure, speakers, states, triggers, variables. |
| `20-spec` | `quest-text-spec` | Quest/objective/tutorial/reward text contracts. |
| `30-generate` | `dialogue-generation` | Dialogue drafts, variants, localization-ready manifests. |
| `40-qa` | `text-consistency-qa` | Tone, terminology, variables, length, and continuity checks. |

## Canonical Invocation Paths

```text
${CLAUDE_PLUGIN_ROOT}/skills/game-narrative/10-design/narrative-tone-design/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-narrative/10-design/world-bible-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-narrative/10-design/character-arc-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-narrative/20-spec/story-structure-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-narrative/20-spec/narrative-event-trigger-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-narrative/20-spec/dialogue-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-narrative/20-spec/quest-text-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-narrative/30-generate/dialogue-generation/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-narrative/40-qa/text-consistency-qa/SKILL.md
```

## Layering Rules

Dependencies flow from earlier numbered layers to later numbered layers only.
