# Demo Forge Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create `demo-forge-skill/` as an independent plugin with 4 skills (demo-design, media-forge, demo-execute, demo-verify) + orchestrator command, supporting multi-round quality iteration.

**Architecture:** Independent plugin following existing myskills conventions. Migrates seed-forge content from dev-forge, adds media pipeline with Brave Search + WebSearch fallback, adds Playwright-based verification with 5-route issue routing (design/media/execute/dev_task/skip), and multi-round iteration (up to 3 rounds, 95% pass threshold).

**Tech Stack:** Claude Code plugin system (YAML frontmatter skills/commands), Brave Search MCP, Playwright MCP, ffmpeg/ImageMagick for media processing.

**Design doc:** `docs/plans/2026-03-05-seed-forge-restructure-design.md`

---

### Task 1: Plugin Skeleton

**Files:**
- Create: `demo-forge-skill/.claude-plugin/plugin.json`
- Create: `demo-forge-skill/SKILL.md`

**Step 1: Create plugin.json**

```json
{
  "name": "demo-forge",
  "description": "Demo Forge: prepare production-ready demo environments with realistic data, rich media, and iterative quality verification. Four skills: demo-design (plan what data to create), media-forge (acquire + process + upload images/videos), demo-execute (generate + populate data), demo-verify (Playwright verification + issue routing). Multi-round iteration until 95% pass rate. 演示锻造：设计演示数据方案、采集加工上传富媒体、灌入数据、Playwright 验证，多轮迭代至 95% 通过率。",
  "version": "1.0.0",
  "author": { "name": "dv" }
}
```

**Step 2: Create SKILL.md**

SKILL.md should follow the pattern from code-replicate-skill/SKILL.md and dev-forge-skill/SKILL.md:
- YAML frontmatter with name + description
- Plugin overview and positioning within the 5-layer architecture
- List all 4 skills with descriptions and command examples
- Show the data contract (.allforai/demo-forge/ structure)
- Show multi-round iteration flow

Content outline:

```markdown
---
name: demo-forge
description: >
  Demo Forge: prepare production-ready demo environments with realistic data,
  rich media (images/videos/documents), and iterative quality verification.
  Includes demo-design (data planning), media-forge (media acquisition + processing + upload),
  demo-execute (data generation + population), demo-verify (Playwright verification + routing).
  演示锻造：设计→采集→灌入→验证，多轮迭代打磨至演示级品质。
version: "1.0.0"
---

# Demo Forge — 演示锻造套件

> 让产品看起来像有真实用户在真实使用。

## 前置依赖

- `product-design` 插件的 `.allforai/product-map/` 输出
- 应用代码已完成（dev-forge Phase 7+）
- 应用正在运行（execute + verify 阶段需要）

## 全流程编排

/demo-forge              # 全流程（多轮自动迭代）
/demo-forge design       # 仅设计阶段
/demo-forge media        # 仅富媒体管线
/demo-forge execute      # 仅数据灌入
/demo-forge verify       # 仅验证
/demo-forge clean        # 清理已灌入数据
/df-status               # 查看进度

## 包含的技能（4 个）

### 1. demo-design
### 2. media-forge
### 3. demo-execute
### 4. demo-verify

## 定位

product-design（产品层）  概念→地图→界面→用例→查漏→剪枝
dev-forge（开发层）       引导→规格→脚手架→执行→验证→验收
demo-forge（演示层）      设计→采集→灌入→验证→迭代 ← 你在这里
deadhunt（QA 层）         死链→CRUD完整性→字段一致性
code-tuner（架构层）      合规→重复→抽象→评分

## 多轮迭代模型

Round 0: Design -> Media -> Execute -> Verify
Round 1+: Fix(design/media/execute) -> Verify (max 3 rounds, 95% threshold)

## 输出

.allforai/demo-forge/ 完整目录结构
```

**Step 3: Create docs directory**

```bash
mkdir -p demo-forge-skill/.claude-plugin demo-forge-skill/skills demo-forge-skill/commands demo-forge-skill/docs
```

**Step 4: Commit**

```bash
git add demo-forge-skill/.claude-plugin/plugin.json demo-forge-skill/SKILL.md
git commit -m "feat(demo-forge): create plugin skeleton with manifest and entry point"
```

---

### Task 2: demo-design.md (Design Phase)

**Files:**
- Create: `demo-forge-skill/skills/demo-design.md`

**Step 1: Write demo-design.md**

Migrate from `dev-forge-skill/skills/seed-forge.md` Steps 0-2, with these changes:
- Rename seed-plan -> demo-plan throughout
- Add Step 1-M (media field annotation) — new section
- Add reentry mode section (for verify routing back)
- Remove Steps 3-4 and everything after (those move to other skills)
- Update all `.allforai/seed-forge/` references to `.allforai/demo-forge/`
- Keep the enhanced protocol section (WebSearch + 4E+4V + OpenRouter) but scoped to design only
- Keep the seed data generation principles table (boundary values, equivalence classes, etc.)

Key sections to include:
1. YAML frontmatter with triggers for "demo design", "演示数据设计", "demo-plan"
2. Objective and positioning
3. Quick start (modes: full, reentry)
4. Prerequisites (product-map must exist)
5. Workflow: Step 0 (model mapping) -> Step 1 (demo plan: 1-A through 1-M) -> Step 2 (style + templates) -> Step 2.5 (text diversity)
6. Step 1-M media field annotation (from design doc)
7. Data generation principles (migrate from current seed-forge)
8. Common omission patterns (migrate from current seed-forge)
9. Reentry mode (incremental updates from verify-issues)
10. Output files: model-mapping.json, api-gaps.json, demo-plan.json, style-profile.json
11. Iron rules (frequency determines quantity, constraints are hard rules)

**Source material:**
- `dev-forge-skill/skills/seed-forge.md` lines 1-384 (Steps 0-2.5)
- `dev-forge-skill/skills/seed-forge.md` lines 617-661 (iron rules + common omissions)
- `docs/plans/2026-03-05-seed-forge-restructure-design.md` Section "阶段一：demo-design"

**Step 2: Commit**

```bash
git add demo-forge-skill/skills/demo-design.md
git commit -m "feat(demo-forge): add demo-design skill — data planning with media field annotation"
```

---

### Task 3: media-forge.md (Rich Media Pipeline)

**Files:**
- Create: `demo-forge-skill/skills/media-forge.md`
- Create: `demo-forge-skill/docs/media-processing.md`

**Step 1: Write media-forge.md**

This is entirely new. Structure:

1. YAML frontmatter with triggers for "media forge", "富媒体", "采集图片", "上传素材", "media-forge"
2. Objective: acquire, process, upload all media assets for demo environment
3. Iron rules (4 rules from design doc: local only, upload API, search-first, zero external URLs)
4. Prerequisites: demo-plan.json must exist (specifically Step 1-M media annotations)
5. Quick start: `/demo-forge media` or standalone `/media-forge`
6. Workflow M1-M6:

   **M1: Needs Inventory**
   - Read demo-plan.json media_fields section
   - Group by media_type and purpose
   - Calculate totals per category
   - Output progress, don't stop

   **M2: Search Acquisition (primary)**
   - Priority chain: Brave Search MCP -> WebSearch fallback
   - Brave tools: `mcp__brave-search__brave_web_search` for images, video keywords
   - WebSearch fallback when Brave unavailable or quota exhausted
   - Download to `assets/{category}/` with sequential naming (IMG-001, VID-001, etc.)
   - Same keyword group per purpose for style consistency
   - Track fulfilled vs gap counts

   **M3: AI Generation (gap filling only)**
   - Only for M2 unfulfilled gaps
   - Uses Google Vertex AI via GOOGLE_API_KEY:
     - Image: Imagen 3 (`imagen-3.0-generate-002`)
     - Video: Veo 2 (`veo-2.0-generate-exp`)
     - Audio: Google Cloud TTS
   - Product operation demos: Playwright screen recording (free, most realistic)
   - Document: PDF template fill
   - Google AI unavailable -> fallback to DALL-E / local Stable Diffusion

   **M3.5: Post-Processing**
   - Resolution insufficient -> AI upscale (Real-ESRGAN CLI / upscale API)
   - Aspect ratio mismatch -> smart crop (ffmpeg crop with gravity center)
   - File too large -> compress (cwebp / ffmpeg quality adjust)
   - Wrong format -> convert (PNG->WebP via cwebp, MOV->MP4 via ffmpeg)
   - Video too long -> trim key segment (ffmpeg -ss -t)
   - Style inconsistent -> color/brightness normalize (ffmpeg eq filter)
   - Tools reference: `${CLAUDE_PLUGIN_ROOT}/docs/media-processing.md`

   **M4: Quality Validation**
   - Per-asset checklist (resolution, aspect ratio, size, style, watermark, AI artifacts, video playback)
   - Rejected -> loop back to M2/M3/M3.5
   - Output assets-manifest.json

   **M5: Upload to App Server**
   - Read upload_endpoint from demo-plan.json per media field
   - Multipart upload via curl/API call
   - Parse response for server_url and server_id
   - Retry 2x on failure, then UPLOAD_FAILED
   - Missing endpoint -> API_GAP in api-gaps.json
   - Output upload-mapping.json

   **M6: Completeness Check**
   - All verified assets have upload-mapping entries
   - No UPLOAD_FAILED remaining
   - external_url_count == 0 (hard validation)

7. Reentry mode (from verify-issues route_to="media")
8. Output files: assets/, assets-manifest.json, upload-mapping.json
9. JSON schema examples for assets-manifest.json and upload-mapping.json

**Step 2: Write docs/media-processing.md**

Reference doc for media processing commands:

```markdown
# Media Processing Reference

## Image Operations

### Upscale (Real-ESRGAN)
realesrgan-ncnn-vulkan -i input.jpg -o output.jpg -s 2

### Convert to WebP
cwebp -q 85 input.png -o output.webp

### Resize maintaining aspect ratio
ffmpeg -i input.jpg -vf "scale=800:-1" output.jpg

### Smart crop to aspect ratio
ffmpeg -i input.jpg -vf "crop=ih*1:ih" output.jpg  # 1:1
ffmpeg -i input.jpg -vf "crop=ih*16/9:ih" output.jpg  # 16:9

### Compress JPEG
ffmpeg -i input.jpg -q:v 3 output.jpg

## Video Operations

### Convert MOV to MP4
ffmpeg -i input.mov -c:v libx264 -crf 23 -c:a aac output.mp4

### Trim video
ffmpeg -i input.mp4 -ss 00:00:05 -t 00:00:30 -c copy output.mp4

### Compress video
ffmpeg -i input.mp4 -crf 28 -preset medium output.mp4

### Extract thumbnail
ffmpeg -i input.mp4 -ss 00:00:01 -vframes 1 thumbnail.jpg

## Batch Operations

### Bulk WebP conversion
for f in *.png; do cwebp -q 85 "$f" -o "${f%.png}.webp"; done

### Bulk resize
for f in *.jpg; do ffmpeg -i "$f" -vf "scale=800:-1" "resized/$f"; done
```

**Step 3: Commit**

```bash
git add demo-forge-skill/skills/media-forge.md demo-forge-skill/docs/media-processing.md
git commit -m "feat(demo-forge): add media-forge skill — Brave search + processing + upload pipeline"
```

---

### Task 4: demo-execute.md (Execution Phase)

**Files:**
- Create: `demo-forge-skill/skills/demo-execute.md`

**Step 1: Write demo-execute.md**

Migrate from `dev-forge-skill/skills/seed-forge.md` Steps 3-4 + self-check + clean, with these changes:
- Remove Step 3 (image acquisition) — now in media-forge
- Rename seed-plan -> demo-plan, seed-forge -> demo-forge throughout
- Add E1: Data Generation step (forge-data-draft.json with deterministic logic)
- Add E2: Pre-flight Self-Check (migrate existing self-check, add media association check)
- Refactor Step 4 into E3: Data Population (same logic, cleaner structure)
- Add E4: Derived Data Correction (new — SUM/COUNT/balance recalculation)
- Add forge-data-draft.json concept (generated data with temp IDs, separate from forge-data.json with real IDs)
- Add reentry mode section
- Keep Clean mode

Key sections:
1. YAML frontmatter with triggers for "demo execute", "灌入数据", "populate demo", "demo-execute"
2. Objective: transform design into actual data in the running application
3. Prerequisites: demo-plan.json + style-profile.json + upload-mapping.json + running application
4. Workflow E1-E4
5. Data generation principles:
   - Text: random template selection from style-profile, no adjacent duplicates
   - Numbers: constraint ranges + boundary values
   - Time: weighted sampling (recent-dense, work-hours, monthly fluctuation)
   - Status: allocated per enum coverage requirements
   - Media: server_url/server_id from upload-mapping.json
   - Foreign keys: chain dependency auto-linking
   - Derived: mathematical calculation (SUM = detail total)
   - Behavior: power-law distribution (10% heavy -> 50% data)
6. Self-check checklist (8 items)
7. Population order (chain-based, not alphabetical)
8. Failure handling (independent fail -> log+continue, parent fail -> skip chain)
9. Derived data correction (DB direct-write补派生)
10. Clean mode
11. Reentry mode
12. Output files

**Source material:**
- `dev-forge-skill/skills/seed-forge.md` lines 459-595 (Steps 4, self-check, clean)
- `docs/plans/2026-03-05-seed-forge-restructure-design.md` Section "阶段二：demo-execute"

**Step 2: Commit**

```bash
git add demo-forge-skill/skills/demo-execute.md
git commit -m "feat(demo-forge): add demo-execute skill — data generation, population, derived correction"
```

---

### Task 5: demo-verify.md (Verification Phase)

**Files:**
- Create: `demo-forge-skill/skills/demo-verify.md`

**Step 1: Write demo-verify.md**

This is largely new (current seed-forge has a brief post-population checklist, this is a full Playwright-driven verification).

Key sections:
1. YAML frontmatter with triggers for "demo verify", "验证演示", "verify demo data", "demo-verify"
2. Objective: systematically verify the demo environment is presentation-ready
3. Prerequisites: forge-data.json exists + application running
4. Tools: Playwright MCP (`mcp__plugin_playwright_playwright__*`)
5. Workflow V1-V7:

   **V1: Login Verification**
   - Read demo-plan.json credentials section
   - For each role account: Playwright navigate to login -> fill credentials -> submit
   - Verify: redirect to correct dashboard, role-specific data visible
   - Screenshot each login state

   **V2: List Page Verification**
   - For each role's primary list views:
   - Check: data count > 0, sort order (newest first), pagination if enough data
   - Check: images loaded (no broken img tags, no placeholder gray blocks)
   - Check: no placeholder text ("Lorem ipsum", "test", "TODO", "undefined")
   - Screenshot each list

   **V3: Detail Page Verification**
   - Sample N records per entity (open detail page)
   - Check: all fields populated (no null/undefined/empty displays)
   - Check: related data present (sub-entity lists, status history)
   - Check: media loads (images display, videos playable)
   - Screenshot each detail

   **V4: Dashboard/Report Verification**
   - Navigate to each dashboard/report page
   - Check: numbers non-zero
   - Check: trend charts show multi-month data
   - Check: totals match (compare displayed sum with list data)
   - Screenshot each dashboard

   **V5: Edge Case Verification**
   - Navigate to terminal-state records (CLOSED, REJECTED, CANCELED)
   - Check: detail pages render correctly
   - Test search/filter functionality
   - Test boundary data records (very long text, zero amounts)
   - Screenshot edge cases

   **V6: Media Integrity Verification (重点)**
   - Playwright evaluate: scan all `img[src]`, `video[src]` in DOM
   - Check: no broken images (naturalWidth == 0)
   - Check: no external URLs (src not matching app domain)
   - Check: no placeholder patterns (data:image/svg, placeholder.com, via.placeholder)
   - Check: aspect ratios reasonable (not severely stretched)
   - Check: videos have valid src and can play
   - Check: no duplicate images in same list view
   - Screenshot flagged items

   **V7: Issue Summary + Routing**
   - Aggregate all failures from V1-V6
   - Classify each by category and assign route_to
   - Route rules:
     - data_coverage -> design
     - media_broken/placeholder/external_url -> media
     - fk_broken/derived_mismatch/chain_failed -> execute
     - api_500/render_bug/sql_error -> dev_task
     - style_preference -> skip
   - For dev_task routes: generate structured task compatible with dev-forge tasks.md format, append to `.allforai/project-forge/sub-projects/{name}/tasks.md` B-FIX round
   - Output verify-report.json (full) + verify-issues.json (failures only)

6. verify-issues.json schema (from design doc)
7. verify-report.json schema (full report with all checks, pass/fail/skip per item)
8. Screenshot storage convention: `.allforai/demo-forge/screenshots/v{check}-round{N}-{entity}.png`

**Step 2: Commit**

```bash
git add demo-forge-skill/skills/demo-verify.md
git commit -m "feat(demo-forge): add demo-verify skill — Playwright verification with 5-route issue routing"
```

---

### Task 6: demo-forge.md Orchestrator Command

**Files:**
- Create: `demo-forge-skill/commands/demo-forge.md`

**Step 1: Write demo-forge.md command**

YAML frontmatter:
```yaml
description: "演示锻造全流程：design → media → execute → verify，多轮迭代。模式: full / design / media / execute / verify / clean"
argument-hint: "[mode: full|design|media|execute|verify|clean]"
allowed-tools: ["Read", "Write", "Grep", "Glob", "Bash", "Agent", "AskUserQuestion"]
```

Command body:
1. Mode routing based on $ARGUMENTS
2. Prerequisites check:
   - product-map exists
   - For execute/verify: application running (prompt user for URL)
3. Full mode orchestration:

   **Phase 0: Product Detection + Init**
   - Check existing artifacts in `.allforai/demo-forge/`
   - If round-history.json exists -> resume mode
   - Initialize round-history.json

   **Phase 1: Design**
   - Load `${CLAUDE_PLUGIN_ROOT}/skills/demo-design.md`
   - Execute full design workflow
   - Quality gate: demo-plan.json exists with > 0 entities

   **Phase 2: Media**
   - Load `${CLAUDE_PLUGIN_ROOT}/skills/media-forge.md`
   - Execute full media pipeline
   - Quality gate: assets-manifest.json exists, upload-mapping.json has 0 external URLs

   **Phase 3: Execute**
   - Load `${CLAUDE_PLUGIN_ROOT}/skills/demo-execute.md`
   - Execute data generation + population
   - Quality gate: forge-data.json exists with > 0 records

   **Phase 4: Verify**
   - Load `${CLAUDE_PLUGIN_ROOT}/skills/demo-verify.md`
   - Execute full verification
   - Quality gate: pass_rate >= 95% (excluding DEFERRED_TO_DEV)

   **Phase 5: Iteration (if needed)**
   - Read verify-issues.json
   - Group by route_to
   - Re-enter each affected phase (design/media/execute)
   - Re-verify (scoped to fixed items + regression)
   - Max 3 rounds, then output remaining as known issues

   **Phase 6: Final Report**
   - Summary table: rounds completed, pass rate progression, dev tasks generated
   - Print credentials table for demo login

4. Single-phase modes: load corresponding skill directly
5. Clean mode: load demo-execute.md clean section
6. Update round-history.json after each round

**Step 2: Commit**

```bash
git add demo-forge-skill/commands/demo-forge.md
git commit -m "feat(demo-forge): add orchestrator command with multi-round iteration"
```

---

### Task 7: df-status.md Command

**Files:**
- Create: `demo-forge-skill/commands/df-status.md`

**Step 1: Write df-status.md**

YAML frontmatter:
```yaml
description: "查看演示锻造进度：当前轮次、各阶段状态、通过率。"
allowed-tools: ["Read", "Glob", "Bash"]
```

Command body:
1. Read `.allforai/demo-forge/round-history.json`
2. Read artifact existence for each phase
3. Output status table:

```
## Demo Forge 进度

| 阶段 | 状态 | 产出 |
|------|------|------|
| Design | 完成 | demo-plan.json (12 实体, 8 角色, 156 媒体字段) |
| Media | 完成 | 152/156 素材已上传 |
| Execute | 完成 | 342 条记录已灌入 |
| Verify | Round 1 进行中 | Round 0: 82.6% → Round 1: 97.7% |

当前轮次: Round 1
未解决问题: 2 (1 media, 1 execute)
Dev 任务已生成: 2
```

**Step 2: Commit**

```bash
git add demo-forge-skill/commands/df-status.md
git commit -m "feat(demo-forge): add df-status command for progress tracking"
```

---

### Task 8: Update dev-forge Integration

**Files:**
- Modify: `dev-forge-skill/SKILL.md` (update seed-forge reference)
- Modify: `dev-forge-skill/commands/project-forge.md` (Phase 4 reference)

**Step 1: Update SKILL.md**

In `dev-forge-skill/SKILL.md`:
- Change "seed-forge" section to reference demo-forge as external plugin
- Update the positioning diagram to show demo-forge as separate layer
- Update the output directory listing to remove seed-forge/ (now in demo-forge-skill)

Replace the seed-forge skill section (lines 92-103) with:

```markdown
### 6. demo-forge — 演示锻造（独立插件）

> 已独立为 `demo-forge-skill/` 插件。详见该插件文档。

按产品地图生成有业务逻辑、有人物关系、有时间分布的真实感演示数据，配合富媒体采集+加工+上传，Playwright 验证，多轮迭代打磨至演示级品质。

\`\`\`
/demo-forge              # 全流程
/demo-forge design       # 只设计方案
/demo-forge media        # 富媒体采集+上传
/demo-forge execute      # 数据灌入
/demo-forge verify       # 验证
/demo-forge clean        # 清理
\`\`\`
```

**Step 2: Update project-forge.md Phase 4**

In `dev-forge-skill/commands/project-forge.md`:
- Find Phase 4 section
- Change to reference demo-forge plugin instead of internal seed-forge skill
- Update the phase table entry
- Add Phase 8+ prompt to run full demo-forge after code stabilizes

In the phase table, change:
```
| 4 | `skills/seed-forge.md` | 种子数据方案 | `seed-plan.json` 存在 |
```
to:
```
| 4 | _(外部: demo-forge 插件)_ | 演示数据方案 | `demo-plan.json` 存在 |
```

In Phase 4 section, change from loading internal skill to:
```
Phase 4: 演示数据方案
  提示用户运行 /demo-forge design
  验证 .allforai/demo-forge/demo-plan.json 存在 -> 继续
  注: 完整灌入在 Phase 8 代码稳定后运行 /demo-forge
```

**Step 3: Do NOT delete seed-forge.md yet**

Keep `dev-forge-skill/skills/seed-forge.md` until demo-forge is fully tested. Add a deprecation note at the top:

```markdown
> **DEPRECATED**: This skill has been migrated to the independent `demo-forge-skill/` plugin.
> Use `/demo-forge` instead. This file will be removed in a future version.
```

**Step 4: Commit**

```bash
git add dev-forge-skill/SKILL.md dev-forge-skill/commands/project-forge.md dev-forge-skill/skills/seed-forge.md
git commit -m "refactor(dev-forge): update Phase 4 to reference external demo-forge plugin"
```

---

### Task 9: Extend setup-openrouter -> setup-services

**Files:**
- Modify: `product-design-skill/commands/setup-openrouter.md` (rename + extend)
- Create: `product-design-skill/commands/setup-services.md`

**Step 1: Create setup-services.md**

Create new command that handles OpenRouter, Brave Search, and Google AI:

YAML frontmatter:
```yaml
description: "配置外部服务 API Key：OpenRouter（跨模型交叉验证）+ Brave Search（媒体搜索）+ Google AI（生图/生视频/TTS）。检测状态、引导获取、验证连接、持久化。"
argument-hint: "[check|reset]"
allowed-tools: ["Read", "Write", "Grep", "Bash", "AskUserQuestion"]
```

Command body structure — extend the existing setup-openrouter flow:

1. **Step 0: MCP Server Build Check** (same as current)
2. **Step 1: Detect Status** — check all three keys:
   - `OPENROUTER_API_KEY` env var
   - `BRAVE_API_KEY` env var
   - `GOOGLE_API_KEY` env var
   - OpenRouter MCP tool availability
   - Brave Search MCP tool availability (`mcp__brave-search__brave_web_search` or similar)
3. **Step 2: Guide Key Acquisition** — for each missing key:
   - OpenRouter: same as current flow (openrouter.ai/keys)
   - Brave Search: guide to https://brave.com/search/api/ -> create key -> paste
   - Google AI: guide to console.cloud.google.com/apis/credentials -> create API Key
     - Prerequisite: enable Vertex AI API (`gcloud services enable aiplatform.googleapis.com`)
     - Key format: AIza...
     - Covers: Imagen 3 (生图) + Veo 2 (生视频) + Cloud TTS (语音)
4. **Step 3: Persist Keys** — write all to shell config
5. **Step 4: Verify** — status report for all services

Status report format:
```
## 外部服务状态

| 服务 | Key | 用途 |
|------|-----|------|
| OpenRouter | 已配置 | 跨模型交叉验证 |
| Brave Search | 已配置 | 媒体搜索 + 通用搜索增强 |
| Google AI | 已配置 | AI 生图(Imagen 3) + 生视频(Veo 2) + TTS |
```

**Step 2: Update setup-openrouter.md with deprecation redirect**

Add at top of existing file:
```markdown
> **重定向**: 此命令已升级为 `/setup-services`，同时配置 OpenRouter + Brave Search + Google AI。
> 运行 `/setup-services` 获取完整配置流程。
```

Keep the existing content functional as fallback.

**Step 3: Update product-design SKILL.md**

Add setup-services to the commands list, note the upgrade from setup-openrouter.

**Step 4: Commit**

```bash
git add product-design-skill/commands/setup-services.md product-design-skill/commands/setup-openrouter.md product-design-skill/SKILL.md
git commit -m "feat(product-design): add setup-services command — unified OpenRouter + Brave + Google AI configuration"
```

---

### Task 10: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

**Step 1: Update architecture table**

Add demo-forge as the 5th layer:

```
Layer         Plugin            Coverage
────────────  ────────────────  ─────────────────────────────────────────────
Product       product-design    concept→map→screens→ui→use-cases→gaps→prune→audit
Development   dev-forge         setup→spec→scaffold→execute→e2e→verify
Demo          demo-forge        design→media→execute→verify→iterate
QA            deadhunt          dead links→CRUD completeness→ghost features→field consistency
Architecture  code-tuner        compliance→duplication→abstraction→scoring
```

**Step 2: Update Shared Data Contract**

Add demo-forge section:
```
├── demo-forge/              # demo-plan, assets, forge-data, verify-issues, round-history
```

**Step 3: Update Recommended Workflow**

After `/code-tuner` add:
```
/demo-forge               # Demo environment preparation (design→media→execute→verify)
```

**Step 4: Update Plugin Structure section**

Add demo-forge-skill/ to the list.

**Step 5: Update Installing Plugins section**

Add:
```bash
claude plugin add /path/to/myskills/demo-forge-skill
```

**Step 6: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add demo-forge to architecture overview and workflow"
```

---

## Checkpoint Review

After Task 10, review the full plugin:

```bash
# Verify plugin structure
find demo-forge-skill -type f | sort

# Verify all cross-references
grep -r "seed-forge" demo-forge-skill/  # should be 0 matches
grep -r "demo-forge" dev-forge-skill/   # should find Phase 4 reference
grep -r "demo-forge" CLAUDE.md          # should find architecture + workflow
```

Expected structure:
```
demo-forge-skill/.claude-plugin/plugin.json
demo-forge-skill/SKILL.md
demo-forge-skill/skills/demo-design.md
demo-forge-skill/skills/media-forge.md
demo-forge-skill/skills/demo-execute.md
demo-forge-skill/skills/demo-verify.md
demo-forge-skill/commands/demo-forge.md
demo-forge-skill/commands/df-status.md
demo-forge-skill/docs/media-processing.md
```
