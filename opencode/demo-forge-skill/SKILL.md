---
name: demo-forge
description: >
  Demo Forge: prepare production-ready demo environments with realistic data,
  rich media (images/videos/documents), and iterative quality verification.
  Includes demo-design (data planning), media-forge (media acquisition + processing + upload),
  demo-execute (data generation + population), demo-verify (Playwright verification + routing).
version: "1.3.1"
---

# Demo Forge — 演示锻造套件

> 让产品看起来像有真实用户在真实使用。

## Overview

Demo Forge transforms a working application into a demo-ready product by generating realistic data, acquiring rich media, populating everything through APIs/DB, and verifying the result visually with Playwright.

## Prerequisites

1. **product-design artifacts** — `.allforai/product-map/` must exist (role profiles, task inventory, business flows, experience map). Run product-design first.
2. **Application code complete** — dev-forge Phase 7+ (task execution done), core features working.
3. **Application running** — demo-execute and demo-verify need an accessible application instance (local or remote).

## Available Workflows

| Mode | Phases | Description |
|------|--------|-------------|
| full (default) | 0 → 1 → 2 → 3 → 4 → 5 | Complete: design → media → execute → verify → report |
| design | 0 → 1 | Data plan design only |
| media | 0 → 2 | Media acquisition + processing + upload only |
| execute | 0 → 3 | Data generation + population only |
| verify | 0 → 4 | Playwright verification only |
| clean | — | Clean populated demo data |
| status | — | Show current progress and artifact status |

Full mode executes `design → media → execute → verify` in sequence. Verify failures trigger automatic fix rounds (up to 3), iterating until 95% pass rate.

## Skills (4)

### 1. demo-design — Data Plan Design

> Details: `./skills/demo-design.md`

From the product-map blueprint, plan all data needed for the demo environment: account hierarchy, data volume, business chains, enum coverage, time distribution, behavior patterns, media fields, constraints.

**Key outputs**: `demo-plan.json` (complete data plan), `model-mapping.json` (model-to-API mapping), `api-gaps.json` (missing API list).

### 2. media-forge — Media Asset Forging

> Details: `./skills/media-forge.md`

Acquire, generate, process, and upload media assets for all media fields in demo-plan. Search chain: Brave Search → 网络搜索 fallback → AI generation (Imagen 4 / GPT-5 Image / FLUX 2 Pro for images; Veo 3.1 / Kling for videos). Post-processing includes crop, compress, format conversion. Upload to application server — zero external links.

**Key outputs**: `assets/` directory (local media files), `assets-manifest.json` (asset inventory), `upload-mapping.json` (uploaded URL mapping), `style-profile.json` (visual style profile).

### 3. demo-execute — Data Generation and Population

> Details: `./skills/demo-execute.md`

Generate deterministic data from demo-plan and populate the application through API/DB hybrid strategy. Handle field dependency ordering, relationships, derived field correction.

**Key outputs**: `forge-data-draft.json` (generated raw data), `forge-data.json` (populated data with server IDs), `forge-log.json` (population log).

### 4. demo-verify — Playwright Verification and Routing

> Details: `./skills/demo-verify.md`

Use Playwright to run V1-V8 eight-layer verification (page load, data display, image load, list count, detail correctness, business flow chaining, media integrity, UI liveness + state coverage + data flow). Failed checks auto-classify and route to 5 fix channels:

| Route | Target | Description |
|-------|--------|-------------|
| `design` | demo-design | Data plan deficiency (missing fields, incomplete enums) |
| `media` | media-forge | Media issues (image 404, wrong dimensions) |
| `execute` | demo-execute | Population issues (missing data, broken relationships) |
| `dev_task` | dev-forge | Application bugs (API errors, UI rendering issues) |
| `skip` | Skip | Non-critical issues, do not block pass |

## Multi-Round Iteration Model

```
Round 0 (initial)
  design → media → execute → verify
      ↓
  pass_rate >= 95%?  → Done
      ↓ no
Round 1 (fix round)
  Route by verify-issues:
    design issues → rerun design (incremental) → media → execute → verify
    media issues  → rerun media (incremental) → execute → verify
    execute issues → rerun execute (incremental) → verify
    dev_task issues → generate fix tasks → hand to dev-forge /task-execute
      ↓
  pass_rate >= 95%?  → Done
      ↓ no
Round 2 → Round 3 (max 3 fix rounds)
      ↓
  After 3 rounds still below target → output final report + known issues list
```

Each round's verification results and fix actions are recorded in `round-history.json` for resume support.

## Positioning

```
product-design (product layer)    concept → map → screens → use-cases → gaps → prune
dev-forge (development layer)     setup → spec → scaffold → execute → verify → accept
demo-forge (demo layer)           design → acquire → populate → verify → iterate ← you are here
deadhunt (QA layer)               dead links → CRUD completeness → field consistency
code-tuner (architecture layer)   compliance → duplication → abstraction → scoring
```

**Key insight**: dev-forge's seed-forge generates development seed data (minimal, for functional validation). demo-forge generates demo-grade data (rich, realistic, visually impactful). They complement each other, not replace.

## Output

```
.allforai/demo-forge/
├── model-mapping.json          # App model ↔ API endpoint mapping
├── api-gaps.json               # Missing API list (needs dev-forge)
├── demo-plan.json              # Complete data plan (accounts + volume + chains + constraints)
├── style-profile.json          # Visual style profile (colors + image style + brand tone)
├── assets/                     # Local media assets
│   ├── avatars/                # User avatars
│   ├── covers/                 # Cover images
│   ├── details/                # Detail images
│   ├── banners/                # Banners
│   └── videos/                 # Video assets
├── assets-manifest.json        # Asset inventory (filename + size + purpose + source)
├── upload-mapping.json         # Upload URL mapping (local path → server URL)
├── forge-data-draft.json       # Generated raw data (before population)
├── forge-data.json             # Populated actual data (with server IDs)
├── forge-log.json              # Population log (success/failure/retry)
├── verify-report.json          # Verification report (V1-V7 results)
├── verify-issues.json          # Failed check issues (with route classification)
├── screenshots/                # Verification screenshots
└── round-history.json          # Multi-round iteration history (per-round results + fix actions)
```
