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
version: "2.0.0"
---

# Experience Map — 体验地图

> LLM 理解产品语义后自由设计界面结构，再用验收规则 loop 修正

## 目标

以产品地图（任务 + 数据模型 + 业务流）和旅程情绪图为输入，LLM 自由设计体验地图：

- **设计阶段**：LLM 理解产品定位、用户角色、情绪弧线、数据结构后，自主决定每个界面的布局、组件、交互方式、状态流转
- **验收阶段**：LLM 自审设计质量（任务覆盖率、业务流连续性、平台差异、情绪匹配），不通过的界面重新设计
- **输出**：operation_lines > nodes > screens 三层结构 JSON + 人类可读报告

---

## 核心理念：LLM 设计 + 规则验收

```
旧模式（已废弃）：task → 匹配 37 种交互类型 → 填充模板
新模式：LLM 理解产品语义 → 自由设计界面 → LLM 验收 → loop 修正
```

**交互类型不是生成入口**。LLM 根据产品上下文自主决定界面结构，交互类型仅作为标签词汇保留（方便下游引用和沟通），不限制设计自由度。

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

## 生成方式

LLM 直接分析全部上游产物，理解产品定位、用户角色、数据结构、业务流程、情绪弧线后，**自主设计**每个界面。

**LLM 的设计输入**（全部加载到上下文）：

| 输入 | 来源 | LLM 用途 |
|------|------|---------|
| 产品定位 | product-concept.json | 理解产品调性、创新概念、目标用户 |
| 任务清单 | task-inventory.json | 知道每个角色要完成什么任务 |
| 数据模型 | entity-model.json | 知道每个实体有哪些字段、关系、状态机 |
| 业务流 | business-flows.json | 知道任务之间的流转顺序和交接关系 |
| 视图对象 | view-objects.json | 知道每个界面需要展示/操作哪些数据 |
| 旅程情绪 | journey-emotion-map.json | 知道用户在每个节点的情绪状态和设计提示 |
| 角色画像 | role-profiles.json | 知道每个角色的平台、受众类型、KPI |

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
| 任务覆盖 | 每个任务至少出现在一个界面中 | 功能完整性 |
| 业务流连续 | 业务流中相邻任务的界面之间必须有导航路径 | 流程可达性 |

---

## 输出 schema

- 顶层 key 必须是 `operation_lines`（数组）+ `screen_index`（对象）
- 每个 operation_line 包含 `id`、`name`、`source_journey`、`role`、`nodes`
- 每个 node 包含 `seq`、`id`、`action`、`screens`（screen 对象数组）
- 每个 screen 必须包含：

| 字段 | 必须 | 说明 |
|------|------|------|
| `id` | 是 | S001 格式 |
| `name` | 是 | 界面名称（中文产品语言） |
| `description` | 是 | 界面用途和设计意图（2-3 句话，说明为什么这样设计） |
| `platform` | 是 | `mobile-ios` 或 `desktop-web` |
| `layout_type` | 是 | LLM 自选布局（如 `single-column`、`sidebar-content`、`full-screen-immersive`、`card-stack`、`split-view`、`timeline` 等，不限于预定义列表） |
| `tasks` | 是 | 引用的 task_id 数组 |
| `actions` | 是 | 用户在此界面可执行的操作列表 |
| `components` | 是 | **LLM 自由设计的组件清单**，每个组件包含 `type`（LLM 命名）、`purpose`、`behavior`、`data_source` |
| `interaction_pattern` | 是 | **LLM 自由描述的交互模式**（1-2 句话，如"卡片堆叠+左右滑动评分，翻转显示释义"） |
| `emotion_design` | 推荐 | 基于情绪弧线的设计决策（如"用户此处焦虑，减少信息密度，突出进度反馈"） |
| `states` | 是 | 界面状态（empty/loading/error/success 及其具体交互） |
| `flow_context` | 是 | 导航上下文（prev/next/entry_points/exit_points） |
| `vo_ref` | 推荐 | 关联的视图对象 |
| `api_ref` | 推荐 | 关联的 API 端点 |
| `data_fields` | 是 | 界面展示/操作的数据字段 |
| `interaction_type` | 推荐 | 后标注标签（从设计结果反推最接近的类型，如 CT2/MG1 等），仅供下游引用，不影响设计 |

---

## 工作流

```
前置检查：
  .allforai/experience-map/journey-emotion-map.json   必须存在
  .allforai/product-map/task-inventory.json            必须存在
  .allforai/product-map/role-profiles.json             可选
  .allforai/product-map/business-flows.json            可选
  .allforai/product-map/view-objects.json              可选
  .allforai/product-map/entity-model.json              可选
  .allforai/product-concept/product-concept.json       可选

Step 1: 加载全部上游数据
      读取所有可用的前置数据到上下文
      ↓
Step 2: LLM 自由设计体验地图
      LLM 理解产品语义后，自主设计每个界面
      按角色分组，每个角色的界面独立设计
      ↓
Step 3: LLM 自审验收（loop）
      验收规则检查，不通过的界面重新设计
      最多 loop 3 轮
      ↓
Step 4: 输出
      写入 experience-map.json + report
```

---

### Step 1：加载全部上游数据

加载所有可用的前置数据。LLM 需要充分理解：

1. **产品是什么** — product-concept 的定位、创新概念、目标用户
2. **用户要做什么** — task-inventory 的全部任务（区分 basic/core）
3. **数据长什么样** — entity-model 的实体、字段、关系、状态机
4. **流程怎么走** — business-flows 的业务流节点和交接关系
5. **每步什么感受** — journey-emotion 的情绪弧线和设计提示
6. **界面需要什么数据** — view-objects 的字段和操作绑定

---

### Step 2：LLM 自由设计体验地图

LLM 基于 Step 1 的完整上下文，**像产品设计师一样思考**，为每个角色设计界面：

**设计思路（LLM 内部推理）**：

1. **从业务流出发**：每条业务流是一条操作线，流中的每个节点需要一个或多个界面
2. **理解数据结构**：entity-model 告诉你每个界面需要展示什么字段、有哪些状态转换
3. **匹配情绪弧线**：journey-emotion 告诉你用户在每个节点的情绪，指导交互密度和反馈方式
4. **尊重平台差异**：
   - consumer (mobile-ios)：单手操作、竖屏、底部导航、手势交互、沉浸体验
   - professional (desktop-web)：大屏多列、鼠标键盘、侧边栏导航、批量操作、数据密集
5. **创新界面**：product-concept 中的创新概念（如角色扮演、AI 即时生成）应该有独特的交互设计，不套用标准模板

**设计输出**：对每个界面写出 `description`（设计意图）、`components`（组件清单）、`interaction_pattern`（交互模式描述），而不仅仅是一个交互类型标签。

**大文件处理**：当 screen 数 > 30 时，使用 Python 脚本生成 JSON（避免 Write 工具超限），脚本中 LLM 的设计决策以数据结构形式编码。

---

### Step 3：LLM 自审验收（loop）

设计完成后，LLM 切换到验收者视角，检查以下规则：

**硬性规则（不通过 → 必须修正）**：

| 验收项 | 规则 | 检查方法 |
|--------|------|---------|
| 任务覆盖率 | 每个 task_id 至少出现在一个 screen 的 `tasks` 中 | 遍历 task-inventory，检查未覆盖任务 |
| 业务流连续性 | business-flows 中相邻节点对应的界面之间有 flow_context 连接 | 遍历每条流，检查 prev/next 链路 |
| 平台一致性 | consumer 角色的界面全部 mobile-ios，professional 全部 desktop-web | 按角色检查 platform 字段 |
| 界面非空 | 每个 screen 至少有 1 个 action 和 1 个 data_field | 遍历检查 |

**软性规则（不通过 → 警告但不阻塞）**：

| 验收项 | 规则 |
|--------|------|
| 情绪匹配 | 高焦虑节点的界面应有减压设计（进度反馈、简化操作） |
| 状态完整 | 每个界面应定义 empty/error 状态 |
| 导航可达 | 每个界面至少有一个 entry_point |
| 创新覆盖 | product-concept 中的创新概念应有对应的独特界面 |

**Loop 机制**：

```
生成体验地图 → 验收检查
  全部通过 → Step 4
  硬性规则不通过 →
    列出具体问题（哪些任务未覆盖、哪些流断裂）
    LLM 修正对应界面
    → 重新验收（最多 3 轮）
  3 轮后仍不通过 → 记录剩余问题，WARNING 继续
```

---

### Step 4：输出

写入最终产物：

- `experience-map.json` — 机器可读完整结构
- `experience-map-report.md` — 人类可读报告（操作线总览 + 平台分布 + 高风险节点 + 验收结果）
- `experience-map-decisions.json` — 决策记录

---

### Variants 模式（--variants N）

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

---

## 3 条铁律

### 1. LLM 自由设计，规则只做验收

LLM 根据产品语义自主设计界面结构、交互方式、组件选择。预定义的交互类型（MG1/CT2 等）仅作为后标注标签，不参与设计过程。验收规则检查硬性约束（覆盖率、连续性、平台），不评判设计风格。

### 2. 三层结构完整对齐

operation_lines > nodes > screens 三层结构必须完整。每个操作线至少一个节点，每个节点至少一个屏幕。

### 3. 平台差异不可忽略

consumer 角色和 professional 角色的界面必须在布局、导航、交互方式上有本质差异，不是换个宽度的同一套设计。
