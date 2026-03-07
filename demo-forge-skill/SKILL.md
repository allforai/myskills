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

本插件依赖以下条件：

1. **product-design 产物** — `.allforai/product-map/` 目录必须存在（角色画像、任务清单、业务流、体验地图）。请先运行 `/product-design full` 完成产品设计。
2. **应用代码已完成** — dev-forge Phase 7+（任务执行完毕），核心功能可用。
3. **应用正在运行** — demo-execute 和 demo-verify 需要可访问的应用实例（本地或远程）。

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

## 包含的技能（4 个）

### 1. demo-design — 演示数据方案设计

> 详见 `${CLAUDE_PLUGIN_ROOT}/skills/demo-design.md`

从 product-map 蓝图出发，规划演示环境所需的全部数据：账号体系、数据量级、业务链条、枚举覆盖、时间分布、行为模式、媒体字段、约束条件。

**核心产出**：`demo-plan.json`（完整数据方案）、`model-mapping.json`（模型与 API 映射）、`api-gaps.json`（缺失 API 清单）。

```
/demo-forge design                    # 分析 product-map + 应用代码，生成数据方案
/demo-forge design --accounts 20      # 指定账号数量
/demo-forge design --focus role:admin  # 聚焦特定角色
```

### 2. media-forge — 媒体素材锻造

> 详见 `${CLAUDE_PLUGIN_ROOT}/skills/media-forge.md`

为 demo-plan 中的媒体字段采集、生成、加工、上传素材。搜索链路：Brave Search → WebSearch 兜底 → AI 生成（生图：Imagen 4 / GPT-5 Image / FLUX 2 Pro；生视频：Veo 3.1 / Kling）。后处理包括裁剪、压缩、格式转换。上传到应用服务器，确保零外部链接。

**核心产出**：`assets/` 目录（本地素材文件）、`assets-manifest.json`（素材清单）、`upload-mapping.json`（上传后 URL 映射）、`style-profile.json`（视觉风格画像）。

```
/demo-forge media                     # 按 demo-plan 采集全部媒体
/demo-forge media --type avatars      # 仅采集头像
/demo-forge media --regenerate        # 重新生成所有素材
```

### 3. demo-execute — 数据生成与灌入

> 详见 `${CLAUDE_PLUGIN_ROOT}/skills/demo-execute.md`

根据 demo-plan 生成确定性数据，通过 API / DB 混合策略灌入应用。处理字段依赖顺序、关联关系、派生字段修正。

**核心产出**：`forge-data-draft.json`（生成的原始数据）、`forge-data.json`（灌入后的实际数据，含服务端生成 ID）、`forge-log.json`（灌入日志）。

```
/demo-forge execute                   # 按 demo-plan 灌入全部数据
/demo-forge execute --dry-run         # 仅生成数据，不灌入
/demo-forge execute --model User      # 仅灌入指定模型
```

### 4. demo-verify — Playwright 验证与问题路由

> 详见 `${CLAUDE_PLUGIN_ROOT}/skills/demo-verify.md`

使用 Playwright 对灌入后的应用执行 V1-V7 七层验证（页面加载、数据展示、图片加载、列表数量、详情正确性、业务流串联、交互功能）。验证失败的问题自动分类并路由到 5 条修复通道：

| 路由 | 目标 | 说明 |
|------|------|------|
| `design` | demo-design | 数据方案缺陷（字段缺失、枚举不全） |
| `media` | media-forge | 媒体问题（图片 404、尺寸错误） |
| `execute` | demo-execute | 灌入问题（数据缺失、关联断裂） |
| `dev_task` | dev-forge | 应用 bug（API 报错、UI 渲染异常） |
| `skip` | 跳过 | 非关键问题，不阻塞通过 |

```
/demo-forge verify                    # 执行全部验证
/demo-forge verify --screen S-001     # 仅验证指定界面
/demo-forge verify --level V1-V3      # 仅执行指定层级
```

## 定位

```
product-design（产品层）  概念→地图→界面→用例→查漏→剪枝
dev-forge（开发层）       引导→规格→脚手架→执行→验证→验收
demo-forge（演示层）      设计→采集→灌入→验证→迭代 ← 你在这里
deadhunt（QA 层）         死链→CRUD完整性→字段一致性
code-tuner（架构层）      合规→重复→抽象→评分
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
