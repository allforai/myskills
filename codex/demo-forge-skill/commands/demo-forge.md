---
description: "Demo forge full pipeline: design -> media -> execute -> verify, multi-round iteration to 95% pass rate. Modes: full / design / media / execute / verify / clean"
---

# Demo Forge — Full Pipeline Orchestration

## Overview

This is the orchestration entry point. It loads skill files for each phase and does not implement logic directly. All inter-phase data flows through `.allforai/demo-forge/`.

Quality gates cannot be skipped. User can abort at any phase.

See [execution-playbook.md](../execution-playbook.md) for the complete phase-by-phase orchestration protocol including quality gates, iteration control, and the round-history.json structure.

### Phase -> Skill Reference

| Phase | Skill File | What It Does | Completion Flag |
|-------|-----------|--------------|-----------------|
| 1 | `skills/demo-design.md` | Data scheme design | `demo-plan.json` exists with entities > 0 |
| 2 | `skills/media-forge.md` | Rich media acquisition + processing + upload | `upload-mapping.json` exists with `external_url_count=0` |
| 3 | `skills/demo-execute.md` | Data generation + population | `forge-data.json` exists with records > 0 |
| 4 | `skills/demo-verify.md` | Playwright verification | `verify-report.json` exists |

---

## Mode Routing

- **`full` (default)** -> Full pipeline: Design -> Media -> Execute -> Verify, with automatic multi-round iteration
- **`design`** -> Phase 1 only (data scheme design)
- **`media`** -> Phase 2 only (rich media pipeline)
- **`execute`** -> Phase 3 only (data generation + population)
- **`verify`** -> Phase 4 only (verification)
- **`clean`** -> Load `demo-execute.md` clean mode, remove populated data

---

## Phase 0: Detection + Initialization

### 0-A Upstream Check

product-map artifacts must exist:
```
.allforai/product-map/task-inventory.json  # required
.allforai/product-map/role-profiles.json   # required
```
Missing -> abort, prompt to run product-map first.

### 0-B Artifact Scan

Scan `.allforai/demo-forge/` for existing artifacts to determine phase completion status:

| Artifact | Phase | Complete When |
|----------|-------|---------------|
| `demo-plan.json` | Phase 1 Design | File exists and entities array non-empty |
| `assets-manifest.json` + `upload-mapping.json` | Phase 2 Media | Both files exist and `external_url_count=0` |
| `forge-data.json` | Phase 3 Execute | File exists and records array non-empty |
| `verify-report.json` | Phase 4 Verify | File exists |

### 0-C External Capability Check

| Capability | Detection | Importance | Degradation |
|-----------|-----------|------------|-------------|
| Playwright | Playwright MCP tools available | Phase 4 required | Block verify, prompt install |
| Brave Search | `brave_web_search` available or `BRAVE_API_KEY` set | Phase 2 recommended | Degrade to web search |
| AI Image Gen | OpenRouter MCP tools or Google/fal.ai generation tools available | Phase 2 optional | Imagen 4 -> GPT-5 Image -> FLUX 2 Pro -> skip |
| AI Video Gen | Google/fal.ai video generation tools available | Phase 2 optional | Veo 3.1 -> Kling -> skip |

**Output format**:

```
External capabilities:
  Playwright     OK       Verification (Phase 4 required)
  Brave Search   MISSING  Media search (degrade to web search)
  AI Image Gen   MISSING  Imagen 4 / GPT-5 Image / FLUX 2 Pro (degrade to search only)
  AI Video Gen   MISSING  Veo 3.1 / Kling (degrade to Playwright screen recording)
```

**Playwright not ready + full/verify mode**: Offer installation guidance. For design/media/execute modes, output a one-line notice only.

### 0-D Initialization

- Ensure `.allforai/demo-forge/` directory exists
- Initialize or update `round-history.json` (create empty structure if not present)

### 0-E Runtime Info Collection

For `execute` / `verify` / `full` modes, collect:
- **Application URL**: Check `round-history.json` first. If not found, assume `http://localhost:3000` and declare the assumption.
- **Login credentials**: Reuse from `demo-plan.json` role account definitions if available.

Write collected info to `round-history.json` `runtime_config`.

---

## Phase 1-4: Execution

See [execution-playbook.md](../execution-playbook.md) for detailed phase orchestration, quality gates, iterative fix protocol (Phase 4.5), and final report format (Phase 5).

---

## Iron Rules

1. **Quality gates are mandatory** — each phase's completion flag must be satisfied before proceeding
2. **Orchestrator is navigator** — load skill files, do not implement logic directly
3. **`.allforai/` is the contract** — all artifacts read/write through `.allforai/demo-forge/`
4. **User can abort at any phase** — re-run `full` mode to restart from scratch
5. **`dev_task` does not block iteration** — code bugs route to dev-forge, demo-forge continues its own iteration loop
