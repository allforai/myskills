---
name: demo-forge
description: >
  Demo Forge: prepare production-ready demo environments with realistic data,
  rich media (images/videos/documents), and iterative quality verification.
  Includes demo-design (data planning), media-forge (media acquisition + processing + upload),
  demo-execute (data generation + population), demo-verify (Playwright verification + routing).
version: "2.0.0"
---

# Demo Forge — Demo Environment Suite

> Make the product look like real users are really using it.

## Prerequisites

1. **product-design artifacts** — `.allforai/product-map/` must exist (role profiles, task inventory, business flows, experience map). Run product-design first.
2. **Application code complete** — dev-forge Phase 7+ (task execution done), core features working.
3. **Application running** — demo-execute and demo-verify need an accessible application instance (local or remote).

## Execution Engine Phase Declarations

```yaml
# execution-engine: ./docs/execution-engine.md

phases:
  - id: design
    subagent_task: "设计 demo 数据方案：实体清单、场景链路、API 端点映射"
    input: [".allforai/product-map/", ".allforai/experience-map/", "项目代码库"]
    output: ".allforai/demo-forge/demo-plan.json"
    rules: ["./skills/demo-design.md"]

  - id: media
    subagent_task: "获取/生成 demo 媒体素材并上传"
    input: [".allforai/demo-forge/demo-plan.json"]
    output: ".allforai/demo-forge/upload-mapping.json"
    rules: ["./skills/media-forge.md"]
    depends_on: [design]

  - id: execute
    subagent_task: "通过 API 灌入全部 demo 数据（灌入即集成测试）"
    input: [".allforai/demo-forge/demo-plan.json", ".allforai/demo-forge/upload-mapping.json"]
    output: ".allforai/demo-forge/forge-data.json"
    rules: ["./skills/demo-execute.md"]
    depends_on: [design, media]

  - id: verify
    subagent_task: "验证 demo 数据的视觉完整性（V1-V7 层 + UPSTREAM_DEFECT 回退）"
    input: [".allforai/demo-forge/forge-data.json"]
    output: ".allforai/demo-forge/verify-report.json"
    rules: ["./skills/demo-verify.md"]
    depends_on: [execute]
```

## full Mode Execution

Read `./docs/execution-engine.md` for the dispatch protocol.

The main flow operates as a pure dispatcher:
1. Topological sort by phases depends_on
2. Dispatch subagents per phase, using the task template from the protocol
3. Collect phase summaries, selectively inject into next phase
4. On UPSTREAM_DEFECT from verify, route back to design/media/execute or cross-skill to dev-forge
5. Same {source, target} pair retries max 2 times, then mark UNRESOLVED_DEFECT
6. Output final report when all phases complete

## Workflow Modes

```
full                     # Full pipeline: design -> media -> execute -> verify -> iterate
design                   # Design only: data scheme planning
media                    # Media only: acquisition + processing + upload
execute                  # Execute only: data generation + population
verify                   # Verify only: Playwright verification
clean                    # Clean: remove populated demo data
status                   # Status: check progress and artifact state
```

The full pipeline runs `design -> media -> execute -> verify` in sequence. When verify fails, it enters fix rounds (up to 3) until 95% pass rate is reached.

## Skills (4)

### 1. demo-design — Demo Data Scheme Design

> See `skills/demo-design.md`

From the product-map blueprint, plan all data needed for the demo environment: account system, data volume, business chains, enum coverage, time distribution, behavior patterns, media fields, constraints.

**Core output**: `demo-plan.json` (full data scheme), `model-mapping.json` (model-to-API mapping), `api-gaps.json` (missing API list).

### 2. media-forge — Rich Media Pipeline

> See `skills/media-forge.md`

Acquire, generate, process, and upload media for demo-plan media fields. Search chain: Brave Search -> web search fallback -> AI generation (Image: Imagen 4 / GPT-5 Image / FLUX 2 Pro; Video: Veo 3.1 / Kling). Post-processing includes crop, compress, format conversion. Upload to app server ensuring zero external links.

**Core output**: `assets/` directory (local media files), `assets-manifest.json` (asset inventory), `upload-mapping.json` (upload URL mapping), `style-profile.json` (visual style profile).

### 3. demo-execute — Data Generation and Population

> See `skills/demo-execute.md`

Generate deterministic data from demo-plan and populate the application via API endpoints only (no DB direct write). Injection IS integration testing — every API call validates auth, permissions, validation, and business logic. Missing API = `API_MISSING_BLOCKER`, must be built first. No E4 derived correction — API handles derived fields automatically.

**Core output**: `forge-data-draft.json` (raw generated data), `forge-data.json` (populated data with server IDs), `forge-log.json` (population log).

### 4. demo-verify — Playwright Verification and Issue Routing

> See `skills/demo-verify.md`

Use Playwright to run V1-V8 eight-layer verification (page load, data display, image load, list counts, detail correctness, business flow chains, media integrity, UI liveness + state coverage + data flow integrity). Failed checks are auto-classified and routed to 5 fix channels:

| Route | Target | Description |
|-------|--------|-------------|
| `design` | demo-design | Data scheme defects (missing fields, incomplete enums) |
| `media` | media-forge | Media issues (image 404, size mismatch) |
| `execute` | demo-execute | Population issues (missing data, broken associations) |
| `dev_task` | dev-forge | App bugs (API errors, UI rendering issues) |
| `skip` | Skip | Non-critical issues, do not block pass |

## Position

```
product-design (product)  concept -> map -> screens -> use-cases -> gaps -> prune
dev-forge (development)   setup -> spec -> scaffold -> execute -> verify -> accept
demo-forge (demo)         design -> media -> execute -> verify -> iterate  <- you are here
deadhunt (QA)             dead links -> CRUD completeness -> field consistency
code-tuner (architecture) compliance -> duplication -> abstraction -> scoring
```

**Key insight**: dev-forge's seed-forge generates development seed data (minimal, functional verification). demo-forge generates demo-grade data (rich, realistic, visually impactful). They complement, not replace each other.

## Multi-Round Iteration

```
Round 0 (initial)
  design -> media -> execute -> verify
      |
  pass_rate >= 95%?  -> done
      | no
Round 1 (fix round)
  Route by verify-issues:
    design type  -> re-run design (incremental) -> media -> execute -> verify
    media type   -> re-run media (incremental) -> execute -> verify
    execute type -> re-run execute (incremental) -> verify
    dev_task type -> generate fix tasks -> hand to dev-forge
      |
  pass_rate >= 95%?  -> done
      | no
Round 2 -> Round 3 (max 3 fix rounds)
      |
  After 3 rounds still below target -> output final report + unresolved issues list
```

Each round's results and fix actions are recorded in `round-history.json`, supporting resume from breakpoint.

## Output

```
.allforai/demo-forge/
├── model-mapping.json          # App model <-> API endpoint mapping
├── api-gaps.json               # Missing API list (need dev-forge to build)
├── demo-plan.json              # Full data scheme (accounts + volume + chains + constraints)
├── style-profile.json          # Visual style profile (colors + image style + brand tone)
├── assets/                     # Local media assets
│   ├── avatars/                # User avatars
│   ├── covers/                 # Cover images
│   ├── details/                # Detail images
│   ├── banners/                # Banner ads
│   └── videos/                 # Video assets
├── assets-manifest.json        # Asset inventory (filename + size + purpose + source)
├── upload-mapping.json         # Upload URL mapping (local path -> server URL)
├── forge-data-draft.json       # Generated raw data (pre-population)
├── forge-data.json             # Populated actual data (with server IDs)
├── forge-log.json              # Population log (success/failure/retry)
├── verify-report.json          # Verification report (V1-V7 results summary)
├── verify-issues.json          # Failed checks (with routing classification)
├── screenshots/                # Verification screenshots
└── round-history.json          # Multi-round iteration history (per-round results + fix actions)
```
