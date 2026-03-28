---
name: demo-forge
description: >
  Demo Forge: prepare production-ready demo environments with realistic data,
  rich media (images/videos/documents), and iterative quality verification.
  Includes demo-design (data planning), media-forge (media acquisition + processing + upload),
  demo-execute (data generation + population), demo-verify (Playwright verification + routing).
  演示锻造：设计→采集→灌入→验证，多轮迭代打磨至演示级品质。
version: "2.0.0"
---

# Demo Forge — 演示锻造套件

> 让产品看起来像有真实用户在真实使用。

## 前置依赖

本插件依赖以下条件：

1. **product-design 产物** — `.allforai/product-map/` 目录必须存在（角色画像、任务清单、业务流、体验地图）。请先运行 `/product-design full` 完成产品设计。
2. **应用代码已完成** — dev-forge Phase 7+（任务执行完毕），核心功能可用。
3. **应用正在运行** — demo-execute 和 demo-verify 需要可访问的应用实例（本地或远程）。

## 阶段声明

```yaml
# execution-engine: ./docs/execution-engine.md

phases:
  - id: design
    subagent_task: "设计 demo 数据方案：实体清单、场景链路、API 端点映射"
    input: [".allforai/product-map/", ".allforai/experience-map/"]
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

## 全流程编排

```
/demo-forge                  # 完整流程：设计→采集→灌入→验证→迭代
/demo-forge design           # 仅设计演示数据方案
/demo-forge media            # 仅采集+加工+上传媒体素材
/demo-forge execute          # 仅生成+灌入演示数据
/demo-forge verify           # 仅 Playwright 验证
/demo-forge clean            # 清理已灌入的演示数据
/demo-forge status           # 查看当前进度和产物状态
```

完整流程按 `design → media → execute → verify` 顺序执行，verify 失败时自动进入修复轮次（最多 3 轮），直到通过率达到 95%。

## full 模式执行

读取 `./docs/execution-engine.md` 获取调度协议。

主流程作为纯调度器执行：
1. 按 phases 声明的 depends_on 拓扑排序
2. 逐阶段 dispatch subagent，使用协议中的任务模板
3. 收集阶段摘要，选择性注入给下一阶段
4. verify 阶段发现问题时，通过 UPSTREAM_DEFECT 信号回退到 design/media/execute 或跨 skill 回退到 dev-forge
5. 同一 {source, target} 对最多回退 2 次，超过标记 UNRESOLVED_DEFECT
6. 所有阶段完成后输出最终报告

## Overview

Demo Forge transforms a working application into a demo-ready product by generating realistic data, acquiring rich media, populating everything through API endpoints only (no DB direct writes), and verifying the result visually with Playwright. The injection process itself IS integration testing — every API call validates authentication, permissions, validation, and business logic. Missing APIs are flagged as `API_MISSING_BLOCKER` and must be built before population.

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

## 包含的技能（4 个）

### 1. demo-design — 演示数据方案设计

> 详见 `./skills/demo-design.md`

从 product-map 蓝图出发，规划演示环境所需的全部数据：账号体系、数据量级、业务链条、枚举覆盖、时间分布、行为模式、媒体字段、约束条件。

**核心产出**：`demo-plan.json`（完整数据方案）、`model-mapping.json`（模型与 API 映射）、`api-gaps.json`（缺失 API 清单 — API_MISSING_BLOCKER，必须先补建）。

### 1. demo-design — Data Plan Design

> Details: `./skills/demo-design.md`

From the product-map blueprint, plan all data needed for the demo environment: account hierarchy, data volume, business chains, enum coverage, time distribution, behavior patterns, media fields, constraints.

**Key outputs**: `demo-plan.json` (complete data plan), `model-mapping.json` (model-to-API mapping), `api-gaps.json` (missing API list — `API_MISSING_BLOCKER`, must be built before population).

### 2. media-forge — 媒体素材锻造

> 详见 `./skills/media-forge.md`

为 demo-plan 中的媒体字段采集、生成、加工、上传素材。搜索链路：Brave Search → WebSearch 兜底 → AI 生成（生图：Imagen 4 / GPT-5 Image / FLUX 2 Pro；生视频：Veo 3.1 / Kling）。后处理包括裁剪、压缩、格式转换。上传到应用服务器，确保零外部链接。

**核心产出**：`assets/` 目录（本地素材文件）、`assets-manifest.json`（素材清单）、`upload-mapping.json`（上传后 URL 映射）、`style-profile.json`（视觉风格画像）。

### 2. media-forge — Media Asset Forging

> Details: `./skills/media-forge.md`

Acquire, generate, process, and upload media assets for all media fields in demo-plan. Search chain: Brave Search → 网络搜索 fallback → AI generation (Imagen 4 / GPT-5 Image / FLUX 2 Pro for images; Veo 3.1 / Kling for videos). Post-processing includes crop, compress, format conversion. Upload to application server — zero external links.

**Key outputs**: `assets/` directory (local media files), `assets-manifest.json` (asset inventory), `upload-mapping.json` (uploaded URL mapping), `style-profile.json` (visual style profile).

### 3. demo-execute — 数据生成与灌入

> 详见 `./skills/demo-execute.md`

根据 demo-plan 生成确定性数据，全部通过 API 端点灌入应用（无数据库直写）。灌入过程即集成测试，处理字段依赖顺序、关联关系。缺失 API 标记为 API_MISSING_BLOCKER，必须先补建。

**核心产出**：`forge-data-draft.json`（生成的原始数据）、`forge-data.json`（灌入后的实际数据，含服务端生成 ID）、`forge-log.json`（灌入日志）。无 E4 派生字段修正阶段 — API 自动处理派生字段。

### 3. demo-execute — Data Generation and Population

> Details: `./skills/demo-execute.md`

Generate deterministic data from demo-plan and populate the application through API endpoints only (no DB direct writes). The injection process IS integration testing — every API call validates the full business logic stack. Missing APIs are flagged as `API_MISSING_BLOCKER`. No E4 derived field correction phase — API handles derived fields automatically.

**Key outputs**: `forge-data-draft.json` (generated raw data), `forge-data.json` (populated data with server IDs), `forge-log.json` (population log).

### 4. demo-verify — Playwright 验证与问题路由

> 详见 `./skills/demo-verify.md`

使用 Playwright 对灌入后的应用执行 V1-V7 七层验证（页面加载、数据展示、图片加载、列表数量、详情正确性、业务流串联、媒体完整性） + V8 汇总路由（**UI 活性+状态全覆盖+数据流闭环**汇总）。验证失败的问题自动分类并路由到 5 条修复通道：

| 路由 | 目标 | 说明 |
|------|------|------|
| `design` | demo-design | 数据方案缺陷（字段缺失、枚举不全） |
| `media` | media-forge | 媒体问题（图片 404、尺寸错误） |
| `execute` | demo-execute | 灌入问题（数据缺失、关联断裂） |
| `dev_task` | dev-forge | 应用 bug（API 报错、UI 渲染异常） |
| `skip` | 跳过 | 非关键问题，不阻塞通过 |

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

## 定位

```
product-design（产品层）  概念→地图→界面→用例→查漏→剪枝
dev-forge（开发层）       引导→规格→脚手架→执行→验证→验收
demo-forge（演示层）      设计→采集→灌入→验证→迭代 ← 你在这里
deadhunt（QA 层）         死链→CRUD完整性→字段一致性
code-tuner（架构层）       合规→重复→抽象→评分
```

**核心洞察**：dev-forge 的 seed-forge 生成的是开发用种子数据（少量、功能验证），demo-forge 生成的是演示级数据（丰富、有真实感、有视觉冲击力）。两者互补而非替代。

## 多轮迭代模型

```
Round 0（首轮）
  design → media → execute → verify
      ↓
  通过率 >= 95%?  → 完成
      ↓ 否
Round 1（修复轮）
  按 verify-issues 路由：
    design 类 → 重跑 design（增量）→ media → execute → verify
    media 类  → 重跑 media（增量）→ execute → verify
    execute 类 → 重跑 execute（增量）→ verify
    dev_task 类 → 生成修复任务 → 交给 dev-forge /task-execute
      ↓
  通过率 >= 95%?  → 完成
      ↓ 否
Round 2 → Round 3（最多 3 轮修复）
      ↓
  3 轮后仍未达标 → 输出最终报告 + 未解决问题清单
```

每轮的验证结果和修复动作记录在 `round-history.json`，支持断点续作。

## 输出

```
.allforai/demo-forge/
├── model-mapping.json          # 应用模型 ↔ API 端点映射
├── api-gaps.json               # 缺失 API 清单（需 dev-forge 补建）
├── demo-plan.json              # 完整数据方案（账号+数据量+链条+约束）
├── style-profile.json          # 视觉风格画像（配色+图片风格+品牌调性）
├── assets/                     # 本地媒体素材
│   ├── avatars/                # 用户头像
│   ├── covers/                 # 封面图
│   ├── details/                # 详情图
│   ├── banners/                # 横幅广告
│   └── videos/                 # 视频素材
├── assets-manifest.json        # 素材清单（文件名+尺寸+用途+来源）
├── upload-mapping.json         # 上传后 URL 映射（本地路径→服务端 URL）
├── forge-data-draft.json       # 生成的原始数据（灌入前）
├── forge-data.json             # 灌入后的实际数据（含服务端 ID）
├── forge-log.json              # 灌入日志（成功/失败/重试）
├── verify-report.json          # 验证报告（V1-V7 结果汇总）
├── verify-issues.json          # 验证失败问题（含路由分类）
├── screenshots/                # 验证截图
└── round-history.json          # 多轮迭代历史（每轮结果+修复动作）
```
