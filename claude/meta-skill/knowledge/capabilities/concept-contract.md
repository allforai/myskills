# Concept Contract Capability

> Node: `concept-freeze`. Runs after all concept-phase human gates are approved.
> Captures all approved creative decisions into a canonical source of truth with
> a `canonical_registry` that maps every asset ID to a definitive file prefix.
>
> **Why this exists:** Execution nodes (art-gen, tile-gen, etc.) independently
> invent asset file names, causing naming mismatches (npc_ahai vs npc_kenzo).
> The canonical_registry is the single authoritative ID→filename mapping that
> all downstream nodes must follow.

## Goal

Emit `.allforai/concept-contract.json` — a frozen, version-stamped snapshot of
all approved concept-phase decisions, with a `canonical_registry` derived from
`art-asset-inventory.json`.

## Inputs

| File | Required fields |
|------|----------------|
| `.allforai/product-concept/product-concept.json` | `genre`, `target_platform`, `core_loop` |
| `.allforai/game-design/art-style-guide.json` | `art_overview` (incl. `animation_system`) |
| `.allforai/game-design/art-pipeline-config.json` | `dimension`, `style`, `active_nodes` |
| `.allforai/game-design/art-asset-inventory.json` | `assets[].asset_id`, `assets[].type`, `assets[].name` |
| `.allforai/game-design/approval-records.json` | all records with `gate_status` |

If `art-asset-inventory.json` is missing → report UPSTREAM_DEFECT and halt.
If any human_gate node has `gate_status != "approved"` → halt with error listing unapproved gates.

## Output

`.allforai/concept-contract.json`

## Protocol

### Step 1: Validate all gates approved

Read `.allforai/game-design/approval-records.json`. Every record must have
`gate_status == "approved"`. Collect any non-approved records and report them.
If any exist → halt. Do not produce the contract until all gates pass.

### Step 2: Build canonical_registry

Read `art-asset-inventory.json.assets[]`. For each asset:
- `asset_id` is the canonical slug (never invent a new one)
- Derive `file_prefix` by convention:
  - type=`character` → `npc_{asset_id}`
  - type=`tile` → `t_{asset_id}`
  - type=`environment` → `env_{asset_id}`
  - type=`ui` → `ui_{asset_id}`
  - type=`vfx` → `vfx_{asset_id}`
  - type=`icon` → `ico_{asset_id}`
  - type=`audio-cover` → `aud_{asset_id}`
  - other → `{asset_id}` (no prefix)
- Group into `characters[]`, `tiles[]`, `environments[]`, `ui[]`, `vfx[]`, `other[]`
- Types `icon` and `audio-cover` are grouped into `other[]` in the output schema,
  with their computed `file_prefix` stored in the entry alongside `asset_id` and `name`.

### Step 3: Write concept-contract.json

Stamp with `frozen_at` (ISO timestamp) and `schema_version: "1.0"`.

## Output Schema

```json
{
  "schema_version": "1.0",
  "frozen_at": "<ISO timestamp>",
  "project": {
    "genre": "<from product-concept.json>",
    "target_platform": "<from product-concept.json>",
    "dimension": "<2d | 3d | 2.5d>",
    "style": "<cartoon | pixel | realistic | hand_drawn | vector>",
    "animation_system": "<frame | dragonbones | 3d_skeletal | mixed>"
  },
  "canonical_registry": {
    "characters": [
      { "asset_id": "<slug>", "name": "<display name>", "file_prefix": "npc_<slug>" }
    ],
    "tiles": [
      { "asset_id": "<slug>", "name": "<display name>", "file_prefix": "t_<slug>" }
    ],
    "environments": [
      { "asset_id": "<slug>", "name": "<display name>", "file_prefix": "env_<slug>" }
    ],
    "ui": [
      { "asset_id": "<slug>", "name": "<display name>", "file_prefix": "ui_<slug>" }
    ],
    "vfx": [
      { "asset_id": "<slug>", "name": "<display name>", "file_prefix": "vfx_<slug>" }
    ],
    "other": [
      { "asset_id": "<slug>", "name": "<display name>", "file_prefix": "<derived prefix>" }
    ]
  },
  "active_art_nodes": ["<node ids from art-pipeline-config.active_nodes>"],
  "human_gates_approved": ["<list of approved node ids from approval-records.json>"]
}
```

## Downstream Consumers

| Consumer node | Fields read | Purpose |
|---------------|------------|---------|
| All `*-art-gen` nodes | `canonical_registry.*` | Authoritative file_prefix for every generated asset |
| `art-spec-design` | `canonical_registry.*` | Use as cross-reference when building asset list |
| `art-qa` | `canonical_registry.*`, `active_art_nodes` | Completeness check — every registry entry must have coverage |
| Code generation nodes | `canonical_registry.*` | Asset Registry (ID → path) must reference these prefixes |

## Completion Check

`.allforai/concept-contract.json` exists AND `schema_version == "1.0"`.
