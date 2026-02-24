---
description: "产品概念发现：从问题出发，搜索+选择题引导，帮你发现心中的产品。模式: full / reverse"
argument-hint: "[mode: full|reverse]"
allowed-tools: ["Read", "Write", "Grep", "Glob", "Bash", "Task", "AskUserQuestion", "WebSearch"]
---

# Product Concept — 产品概念发现

用户请求: $ARGUMENTS

## 插件根目录

所有文档路径基于插件安装目录: `${CLAUDE_PLUGIN_ROOT}`

## 模式路由

根据用户参数决定执行模式：

- **无参数 或 `full`** → 发现模式：Step 0 → Step 1 → Step 2 → Step 3
- **`reverse`** → 提炼模式：Step 0 → Step 1 → Step 2（从现有代码/地图反推）

## 前置检查

执行前先检查：

1. 确保输出目录存在：`mkdir -p .allforai/product-concept`
2. 如果 `.allforai/product-concept/concept-decisions.json` 存在，自动加载历史决策，跳过已确认项
3. **reverse 模式额外检查**：
   - 如果 `.allforai/product-map/product-map.json` 存在 → 直接读取作为反推输入
   - 否则扫描项目代码（路由/权限/菜单）作为反推输入

## 执行流程

1. 参考已加载的 `skills/product-concept.md` 中的目标定义、工作流和铁律
2. 根据模式按需执行对应步骤
3. **每个 Step 必须先 WebSearch 搜索（至少 2-3 轮，多角度），再基于搜索结果生成 AskUserQuestion 选择题**
4. **搜索是核心能力**：中英双语搜索、逐层聚焦、主动找反面证据。详见 `skills/product-concept.md` 的「搜索策略」章节
5. 每个 Step 必须有用户确认环节
6. **【强制】执行完毕后，必须在对话中直接输出完整的报告摘要**

## 详细文档（按需用 Read 工具加载）

- `${CLAUDE_PLUGIN_ROOT}/skills/product-concept.md` — 完整工作流、Step 详述、铁律、JSON Schema

## Step 执行要求

每个 Step 完成后：
1. 向用户展示结果摘要
2. 等待用户确认
3. **用户确认后**才将结果写入 `.allforai/product-concept/` 目录下对应的 JSON 文件
4. 进入下一个 Step

## 报告输出要求（强制执行）

执行完成后，必须在对话中直接输出以下报告摘要：

```
## 产品概念报告摘要

> 执行时间: {时间}
> 执行模式: {forward/reverse}

### 产品使命

{一句话产品使命}

### 核心问题

| # | 问题 | 严重度 |
|---|------|--------|
| （逐行列出所有核心问题） | | |

### 目标角色

| 角色 | 核心痛点 | 期望收益 |
|------|----------|----------|
| （每角色一行） | | |

### 商业模式

- 收费模式: {收费模式}
- 核心竞争力: {不可复制优势}
- 关键指标: {关键指标}

### 竞品定位（ERRC 矩阵）

| 维度 | 内容 |
|------|------|
| 剔除 | {行业标配但我们不做的} |
| 减少 | {降低投入的} |
| 增加 | {超出行业水平的} |
| 创造 | {行业从未有过的} |

### 参考来源

（列出搜索过程中的关键 URL）

### 下一步

1. 运行 /product-map 基于产品概念建立完整功能地图
2. 运行 /product-concept reverse 从已有代码反推概念（如适用）

> 产品概念: `.allforai/product-concept/product-concept.json`
> 可读报告: `.allforai/product-concept/product-concept-report.md`
> 决策日志: `.allforai/product-concept/concept-decisions.json`
```

**关键：摘要必须包含具体的问题、角色和 ERRC 内容，不能只给统计数字。**

---

## 铁律（强制执行）

> 完整定义见 `${CLAUDE_PLUGIN_ROOT}/skills/product-concept.md` 的「9 条铁律」章节。

1. **只问选择题，不问开放题** — 所有问题都基于搜索结果生成选项
2. **搜索先行，选项后生** — 每轮提问前必须先 WebSearch
3. **每步确认，增量复用** — 决策写入 concept-decisions.json
4. **产品语言输出** — 不出现技术术语
5. **只标不改** — 概念文档是建议，用户是权威
6. **证据留痕** — 所有搜索来源 URL 记录在输出中
7. **选项基于行为，不基于观点** — Mom Test：问"怎么做的"而非"觉得好不好"
8. **指标必须是成果，不是产出** — Build Trap：key_metrics 必须是 outcome
9. **先拆本质，再看竞品** — First Principles：先拆解问题本质，再搜索竞品
