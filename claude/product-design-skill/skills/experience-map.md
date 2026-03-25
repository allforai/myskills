---
name: experience-map
description: >
  Phase 4 — Experience Map Generation. Use when the user asks to "generate experience map",
  "map experience", "operation lines", "experience-map", "体验地图", "操作线",
  "体验线路", "节点屏幕", "operation line mapping",
  or mentions generating operation lines from journey emotions,
  mapping nodes to screens, building experience maps from journey-emotion-map.
  Replaces the former screen-map skill with a richer experience-oriented structure.
  Requires journey-emotion and product-map to have been run first.
version: "2.8.0"
---

# Experience Map — 体验地图

> LLM 理解产品语义后自由设计界面结构，再用验收规则 loop 修正

## 目标

以产品地图（任务 + 数据模型 + 业务流）和旅程情绪图为输入，LLM 自由设计体验地图：

- **设计阶段**：LLM 理解产品定位、用户角色、情绪弧线、数据结构后，自主决定每个界面的布局、组件、交互方式、状态流转
- **验收阶段**：LLM 自审设计质量（任务覆盖率、业务流连续性、平台差异、情绪匹配），不通过的界面重新设计
- **输出**：operation_lines > nodes > screens 三层结构 JSON + 人类可读报告

当上游 `experience_priority.mode = consumer` 或 `mixed` 时，体验地图必须切换到用户端优先标准：不仅要能走通，还要像成熟产品。

---

## 核心理念：LLM 设计 + 规则验收

```
旧模式（已废弃）：task → 匹配 37 种交互类型 → 填充模板
新模式：LLM 理解产品语义 → 自由设计界面 → LLM 验收 → loop 修正
```

**交互类型不是生成入口**。LLM 根据产品上下文自主决定界面结构，但 `interaction_type` 必须从渲染器支持列表中选择（影响线框渲染布局）。自由设计意图通过 `description`、`components`、`interaction_pattern` 表达。

---

## 定位

```
journey-emotion（旅程情绪图）    experience-map（体验地图）       ui-design（界面设计）
每个节点的情绪、风险、设计提示    操作线 > 节点 > 屏幕结构          基于体验地图生成设计规格
情绪层语义（人工确认）           交互层语义（LLM 自由设计）         视觉层语义
```

---

## 快速开始

```
/experience-map              # 完整流程（Step 1-4）
/experience-map refresh      # 清空缓存，从头重新运行
/experience-map --variants 3 # 生成 3 套信息架构方案，对比后选择
```

---

## 增强协议（WebSearch + 4D+6V + XV）

> 详见 `${CLAUDE_PLUGIN_ROOT}/docs/skill-commons.md`「统一验收方法论」。

**WebSearch**：Step 2 设计界面时，对创新功能（如 AI 生成、角色扮演、沉浸式学习）搜索同类产品的交互设计案例，作为设计参考和 D2 证据（如搜索「immersive language learning app UX」「AI content generation interface patterns」），写入 screen 的 `source_refs`。

**4D+6V 重点**：每个 screen 的 `description` 回答 D1（是什么设计）+ D4（为什么这样设计而非其他方案）；`emotion_design` 回答 D2（基于 journey-emotion 的什么证据）；核心界面（承载 core 任务的 screen）覆盖至少 4/6 视角审查——user: 能完成任务吗？business: 支撑核心指标吗？tech: 可实现吗？ux: 交互一致吗？data: 可观测吗？risk: 有安全风险吗？

**XV**（可选）：将体验地图摘要（操作线数、屏幕数、任务覆盖率、平台分布）发送给第二个模型独立评审，重点审查信息架构合理性和遗漏。

---

## 生成方式

LLM 直接分析全部上游产物，理解产品定位、用户角色、数据结构、业务流程、情绪弧线后，**自主设计**每个界面。

**LLM 的设计输入**（全部加载到上下文）：

| 输入 | 来源 | LLM 用途 |
|------|------|---------|
| 产品定位 | product-concept.json | 理解产品调性、创新概念、目标用户 |
| 治理风格 | product-mechanisms.json → `governance_styles` | 知道每条业务流的治理策略（事前审核/事后追究/分级/自动），决定是否需要审核屏幕、系统边界 |
| 操作频度 | role-value-map.json → `operation_profile` | 知道每个角色的操作频度和屏幕粒度指导（同页多功能 vs 单任务聚焦），指导屏幕合并/拆分决策 |
| 任务清单 | task-inventory.json | 知道每个角色要完成什么任务 |
| 数据模型 | entity-model.json | 知道每个实体有哪些字段、关系、状态机 |
| 业务流 | business-flows.json | 知道任务之间的流转顺序和交接关系 |
| 视图对象 | view-objects.json | 知道每个界面需要展示/操作哪些数据 |
| 旅程情绪 | journey-emotion-map.json | 知道用户在每个节点的情绪状态和设计提示 |
| 角色画像 | role-profiles.json | 知道每个角色的平台、受众类型、KPI |
| 体验优先级 | product-map.json → `experience_priority` | 判断本轮是否按用户端成熟度标准设计，而不是只按功能覆盖设计 |

**LLM 的设计自由度**：

LLM 可以自主决定以下所有方面（不受预定义交互类型限制）：

- **界面结构**：一个任务对应几个界面？是否需要分步向导？是否合并多个任务到一个界面？
- **布局方式**：卡片堆叠、瀑布流、时间线、看板、树形、地图、全屏沉浸... LLM 根据内容类型和用户场景选择
- **交互方式**：滑动翻页、拖拽排序、长按菜单、双击编辑、手势操作... LLM 根据平台和场景选择
- **组件选择**：不限于标准 CRUD 表单/列表，可以设计对话式界面、游戏化界面、AI 辅助界面等
- **状态设计**：空态、加载态、错误态、成功态的具体交互方式和文案
- **微动效**：翻转、弹性、渐显、粒子效果... LLM 根据情绪弧线选择

**唯一的硬约束**：

| 约束 | 规则 | 原因 |
|------|------|------|
| 平台 | consumer 角色 → mobile-ios 单列布局；professional 角色 → desktop-web 侧边栏布局 | 物理设备差异 |
| 应用归属 | 每个屏幕必须有 `app` 字段，标注属于哪个独立应用。跨角色业务流中的屏幕按 node role 归属对应应用（不是按操作线的主角色） | 同为 desktop-web 的 merchant 和 admin 是不同的应用 |
| 任务覆盖 | 每个任务至少出现在一个界面中 | 功能完整性 |
| 业务流连续 | 业务流中相邻任务的界面之间必须有导航路径 | 流程可达性 |

### 用户端优先标准（新增）

当 `experience_priority.mode = consumer` 或 `mixed` 时，experience-map 的屏幕设计与验收必须额外关注：

- 首页是否有明确主线，而不是功能入口拼盘
- 每个核心 screen 是否告诉用户”刚发生了什么、现在该做什么、下一步做什么”
- 空态/加载态/错误态/成功态是否形成统一系统
- 是否存在持续使用触发点（进度、提醒、历史、推荐、订阅、连续反馈）
- 移动端路径是否符合单手、低注意力、碎片时间使用特征

禁止把用户端移动应用设计成”后台页面压缩版”或”概念 demo 页面集合”。

**consumer 端典型设计模式（LLM 设计 screen 时必须对照考虑）**：

成熟用户产品通常包含以下模式，LLM 在设计 consumer_apps 的 screen 时应逐项评估是否适用（不是全部必须，而是逐项判断”本产品是否需要”）：

| 模式 | 说明 | 对应 screen 类型 |
|------|------|----------------|
| 首次引导 | 新用户不直接进首页，而是走引导流（目标设定/偏好收集/个性化生成） | onboarding wizard |
| 个性化主线 | 首页根据用户状态动态展示下一步（不是静态功能列表） | smart home / today feed |
| 过程体验 | 核心操作不只是”提交表单”，而是有进度、实时反馈、阶段性结果（健身=实时追踪、教育=交互关卡、创作=实时预览） | live tracking / interactive challenge / step-by-step |
| 完成仪式 | 核心操作完成后有庆祝/复盘/分享/推荐下一步（不是只回列表） | completion / review / share |
| 连续激励 | 连续使用天数/里程碑/成就/等级（让用户有理由明天再来） | streak / achievements |
| 智能提醒 | 基于行为习惯的推送（不是手动配置的定时提醒） | notification center |
| 社交层 | 关注/动态/对比/挑战（让用户因为其他人而留下来） | social feed / challenge |
| 进度可视 | 长期目标的进度可视化（周报/月报/趋势图） | progress dashboard |
| 沉浸消费 | 全屏无干扰的内容体验（阅读/视频/听/学习），有进度条和手势控制 | immersive reader / player |
| 创作工具 | 用户在产品内创造内容（画布/编辑器/录制），有实时预览和撤销 | canvas / editor / recorder |
| 决策漏斗 | 多步骤决策过程（购物/预订/投资），每步提供正向反馈（省了多少/还差多少/预估结果），减少放弃率 | cart → checkout → confirmation |

> 以上模式不是清单打勾——LLM 根据产品类型判断哪些适用。社交产品可能全部适用，工具产品可能只需 3-4 项。关键是**主动评估**而非**被动忽略**。
>
> **适用性判断原则**：
> - 某些模式在特定领域**不只是不需要，而是有害的**。判断时问自己：**如果用户看到这个模式，会觉得产品更专业，还是更不靠谱？** 例：医疗 App 的"连续吃药 7 天获得徽章"、金融 App 的"投资完成🎉庆祝动画"→ 这些会让用户质疑产品的严肃性
> - 模式的**基调**要匹配产品语境。"完成仪式"在游戏中是庆祝，在医疗中是安抚和下一步指引，在金融中是确认和安全感。不要照搬描述中的娱乐化用词
> - 当不确定某模式是否适用时，**问第二个问题：这个领域的成熟竞品有这个模式吗？** 好大夫没有成就系统，支付宝没有连续打卡火苗（它有但是金融场景外的营销，不是核心体验）

---

## 步骤详情加载

本技能的详细步骤定义拆分为三个文件，按需加载：

### 输出 Schema 与设计原则（Step 2 设计时必读）

Read `${CLAUDE_PLUGIN_ROOT}/docs/experience-map/output-schema.md`

包含：输出 JSON schema、字段格式规范（render_as / data_fields / emotion_design / states / view_modes）、前后台交互指导思想、后台屏幕范式、布局差异化设计原则、interaction_type 渲染器支持列表。

### 生成步骤（Step 1 / 1.5 / 2）

Read `${CLAUDE_PLUGIN_ROOT}/docs/experience-map/generation-steps.md`

包含：工作流概览、前置检查、上游数据加载（Step 1）、骨架生成（Step 1.5）、LLM 自由设计（Step 2 Phase A/B/C）、大文件分批策略、批次脚本模板。

### 验收步骤（Step 3 / 3.1 / 3.5 / 3.6 / 4）

Read `${CLAUDE_PLUGIN_ROOT}/docs/experience-map/validation-steps.md`

包含：自审验收 loop（Step 3）、质量提升 loop（Step 3.1）、Playwright 线框验证（Step 3.5）、模式扫描 + 行为规范（Step 3.6）、最终输出（Step 4）。

---

## Variants 模式（--variants N）

当指定 `--variants N`（N >= 2）时，生成 N 套不同的信息架构方案：

**Step 2v: 多方案发散**
- 每套方案采用不同的信息架构策略：
  - 方案 A：任务驱动型（按用户任务组织界面）
  - 方案 B：对象驱动型（按数据实体组织界面）
  - 方案 C：流程驱动型（按业务流程组织界面）
  - 方案 D：角色驱动型（按角色工作台组织界面）
  - 方案 E：混合型（高频任务前置 + 对象导航）
- 使用 Agent 并发生成 N 套 experience-map
- 每套方案输出到 `.allforai/experience-map/variants/variant-{n}/`

**Step 2v.1: 对抗式评审**
- 如果 OPENROUTER_API_KEY 可用，使用 ask_model 从 5 个视角评审每套方案
- 输出对比矩阵 + 推荐方案

**Step 2v.2: 用户选择**
- 展示对比矩阵，用户选择一个方案
- 选中方案复制到主目录

---

## 全自动模式

**激活条件**（同时满足）：
1. `.allforai/product-concept/product-concept.json` 存在且含 `pipeline_preferences` 字段
2. 上下文含 `__orchestrator_auto: true`

**行为变化**：

| 步骤 | 标准模式 | 全自动模式 |
|------|----------|-----------|
| **Step 3 验收** | 展示验收结果 → 用户确认 | 自动 loop 修正，仅 ERROR 级停 |
| **--variants** | 用户选择方案 | 自动选择推荐方案 |

**基础设施偏好消费**：

读取 `pipeline_preferences.infrastructure` 数组，若非空则在界面清单中体现对应的基础设施需求（如设置页面、语言切换入口、主题切换等）。具体界面设计由 LLM 根据产品上下文判定。

---

## 输出文件结构

```
.allforai/experience-map/
├── experience-map.json              # 机器可读：操作线 > 节点 > 屏幕完整结构
├── experience-map-report.md         # 人类可读：体验地图摘要报告
├── experience-map-decisions.json    # 决策记录
├── journey-emotion-map.json         # 上游输入（由 journey-emotion 生成）
├── journey-emotion-decisions.json   # 上游输入（由 journey-emotion 生成）
├── variants/                        # --variants 模式
│   ├── variant-1/
│   │   └── experience-map.json
│   └── comparison-matrix.json
```

---

## 防御性规范

### 加载校验
- `journey-emotion-map.json`：解析失败 → 终止
- `task-inventory.json`：解析失败 → 终止

### 零结果处理
- 生成 0 个操作线 → 终止
- 生成 0 个屏幕 → 终止

### 执行失败保护
- 任何步骤遇到不可恢复错误 → 写入 `.allforai/experience-map/experience-map-error.json`，包含 `{"error": "...", "step": "...", "timestamp": "..."}`

### 上游过期检测
- **`journey-emotion-map.json`**：加载时比较 `generated_at` 与已有 `experience-map.json` 的 `generated_at`。上游更新 → 警告「journey-emotion 在 experience-map 上次运行后被更新，建议重新运行 /experience-map」。
- **`task-inventory.json`**：加载时比较 `generated_at`。上游更新 → 警告「task-inventory 在 experience-map 上次运行后被更新」。
- **`business-flows.json`**：同上。
- 仅警告不阻断。

---

## 4 条铁律

### 1. LLM 自由设计，规则只做验收

LLM 根据产品语义自主设计界面结构、交互方式、组件选择。`interaction_type` 必须从渲染器支持列表中选择最接近的类型（影响线框布局），但实际设计意图通过 `description`、`components`、`interaction_pattern` 完整表达。验收规则检查硬性约束（覆盖率、连续性、平台），不评判设计风格。

### 5. 用户端不只验“能用”，还验“是否成熟”

若 `experience_priority.mode = consumer` 或 `mixed`，验收时必须额外检查：

- 主线是否清楚
- 页面之间是否有节奏连续性
- 核心动作是否足够突出
- 是否有下一步引导
- 是否存在回访理由

这些检查属于结构与交互成熟度，不等到 ui-design 再补。

### 2. 三层结构完整对齐

operation_lines > nodes > screens 三层结构必须完整。每个操作线至少一个节点，每个节点至少一个屏幕。

### 3. 前后台交互思想不可混用

consumer（人多低频）和 professional（人少高频）的界面必须在信息密度、引导程度、页面粒度、操作方式上有本质差异。不是换个宽度的同一套设计——用前端的低密度引导式设计套后台是浪费专业用户时间，用后台的高密度效率式设计套前端是劝退大众用户。

### 4. 业务正确性优先于结构完整性

结构正确（字段存在、状态数量够）但业务错误（收藏夹加了内容筛选、注册页加了不该有的认证表单）的屏幕比结构不完整更危险——因为后者容易被自动检测，前者只能被人工审核发现。LLM 设计每个屏幕时必须回答：「这个功能/组件/字段在这个业务场景下是否合理？」概念阶段收集的治理风格和操作频度是判断合理性的基准。
