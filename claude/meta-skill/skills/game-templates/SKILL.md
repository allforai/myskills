# Game Templates Skill Pack

> Internal bundled sub-skill pack for meta-skill.
> Status: bundled, inactive, not wired.

## Purpose

Game Templates owns the shared game data contract layer. It converts approved
design, content, balance, art, UI, audio, level, and runtime requirements into
stable template schemas and instances that frontend/runtime systems can load
without reading conversation state.

Templates are not owned by only design, program, or art. They are shared data
containers. Design defines meaning, balance defines numeric values, art/UI/audio
define resource refs, and frontend/runtime define loadability.

## Current Children

| Layer | Child skill | Responsibility |
|---|---|---|
| `00-env` | `template-registry` | Canonical template kinds, schema IDs, ownership, consumers, and lifecycle states. |
| `20-spec` | `template-schema-spec` | Common template envelope plus per-kind field schemas, required refs, defaults, and validation rules. |
| `20-spec` | `template-inheritance-spec` | Base templates, variants, override rules, merge policy, and cycle prevention. |
| `20-spec` | `template-reference-binding-spec` | Bind templates to design, balance, art, UI, audio, level, and runtime refs. |
| `30-generate` | `template-instance-generation` | Generate concrete template instances from approved content/system inputs. |
| `40-qa` | `template-reference-closure-qa` | Validate schema, source refs, resource refs, consumers, and orphan/cycle issues. |
| `40-qa` | `template-runtime-load-qa` | Validate frontend/runtime can parse/load templates with real or adapter evidence. |

## Canonical Invocation Paths

```text
${CLAUDE_PLUGIN_ROOT}/skills/game-templates/00-env/template-registry/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-templates/20-spec/template-schema-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-templates/20-spec/template-inheritance-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-templates/20-spec/template-reference-binding-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-templates/30-generate/template-instance-generation/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-templates/40-qa/template-reference-closure-qa/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-templates/40-qa/template-runtime-load-qa/SKILL.md
```

## Shared Template Envelope

All instances use a common outer shape:

```json
{
  "template_id": "enemy_slime_base",
  "template_kind": "enemy",
  "schema_id": "enemy.v1",
  "source_refs": [],
  "fields": {},
  "balance_refs": [],
  "art_refs": [],
  "audio_refs": [],
  "ui_refs": [],
  "level_refs": [],
  "runtime_consumers": [],
  "validation": {},
  "state": "draft | validated | needs_revision | blocked"
}
```

The `fields` object is governed by the per-kind schema. The outer refs connect
the template to upstream contracts and downstream consumers.

## Outputs

```text
.allforai/game-templates/template-registry.json
.allforai/game-templates/schemas/*.schema.json
.allforai/game-templates/instances/*.json
.allforai/game-templates/template-reference-map.json
.allforai/game-templates/qa/template-reference-closure-qa-report.json
.allforai/game-templates/qa/template-runtime-load-qa-report.json
```

## Boundary

Game Templates must not invent product requirements, generate art/audio, tune
final balance, or implement runtime code. It may assemble and validate data
containers only when every field and ref is traceable or explicitly optional.
Missing or unverifiable references block the template.
