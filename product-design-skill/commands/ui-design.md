---
description: "UI 设计规格：从产品地图 + 界面地图推导高层 UI 设计规格，结合风格选择和设计原则，输出设计规格文档 + 按角色拆分的 HTML 预览。模式: full / refresh"
argument-hint: "[mode: full|refresh]"
allowed-tools: ["Read", "Write", "Grep", "Glob", "Bash", "Task", "AskUserQuestion", "WebSearch"]
---

# UI Design — UI 设计规格生成

用户请求: $ARGUMENTS

## 插件根目录

所有文档路径基于插件安装目录: `${CLAUDE_PLUGIN_ROOT}`

## 模式路由

- **无参数 或 `full`** → 完整流程：Step 1 → Step 2 → Step 3 → Step 4 → Step 5
- **`refresh`** → 将 `ui-design-decisions.json` 重命名为 `.bak`，清除缓存，完整重跑

## 前置检查

执行前必须检查：

1. `.allforai/product-map/product-map.json` 必须存在，否则输出「请先运行 /product-map 建立产品地图」并**立即终止**
2. `.allforai/screen-map/screen-map.json` 必须，不存在则自动运行 screen-map 生成界面地图
3. `.allforai/product-concept/product-concept.json` 可选，存在则提取产品定位和价值主张用于配色基调
4. **历史决策加载**：检查 `.allforai/ui-design/ui-design-decisions.json`，存在则加载，已决策项（如风格选择）自动跳过

## 执行流程

1. 加载 `${CLAUDE_PLUGIN_ROOT}/skills/ui-design.md` 中的完整工作流和铁律
2. 根据模式执行对应步骤
3. 每个 Step 完成后展示摘要，等待用户确认
4. **【强制】执行完毕后，必须在对话中直接输出完整的报告摘要**

## 详细文档（按需用 Read 工具加载）

- `${CLAUDE_PLUGIN_ROOT}/skills/ui-design.md` — 完整工作流、Step 详述、风格列表、HTML 生成规则、铁律

## Step 执行要求

每个 Step 完成后：
1. 将结果写入 `.allforai/ui-design/` 目录下对应文件
2. 向用户展示结果摘要
3. 等待用户确认后才进入下一个 Step

## 报告输出要求（强制执行）

执行完成后，必须在对话中直接输出以下报告摘要：

```
## UI 设计规格报告摘要

> 执行时间: {时间}
> 选用风格: {风格名}
> 设计原则来源: {WebSearch 检索到的主要文档名/URL}

### 总览

| 维度 | 结果 |
|------|------|
| 覆盖角色 | X 个 |
| 覆盖界面 | X 个（来自 screen-map / 任务推导） |
| 生成 HTML 文件 | X 个（index + 各角色） |

### 设计规格要点

（每个角色/界面的布局模式、配色语义、组件库建议摘要）

### 输出文件

> 设计规格: `.allforai/ui-design/ui-design-spec.md`
> HTML 预览: `.allforai/ui-design/preview/index.html`
> 角色预览: `.allforai/ui-design/preview/ui-role-{角色名}.html`
> 决策日志: `.allforai/ui-design/ui-design-decisions.json`
```

---

## 铁律（强制执行）

> 完整定义见 `${CLAUDE_PLUGIN_ROOT}/skills/ui-design.md` 的「4 条铁律」章节。

1. **只出规格不出代码** — 输出是设计语言描述，不生成 React/Vue 组件代码
2. **screen-map 优先，缺席则推导** — 有 screen-map 按界面生成；没有则从高频任务自动推导主要界面
3. **WebSearch 摘要展示，用户确认后才应用** — 检索到的设计原则必须摘要给用户确认，不自动静默应用
4. **风格选择不可省略** — 设计风格必须在 Step 2 由用户明确选择或确认沿用历史风格；未确认风格前不得生成规格和预览
