---
description: "项目引导：交互式拆分子项目 + 选技术栈 + 分配模块。模式: new / existing"
argument-hint: "[mode: new|existing]"
allowed-tools: ["Read", "Write", "Grep", "Glob", "Bash", "Task", "AskUserQuestion"]
---

# Project Setup — 项目引导

用户请求: $ARGUMENTS

## 插件根目录

所有文档路径基于插件安装目录: `${CLAUDE_PLUGIN_ROOT}`

## 模式路由

- **无参数 或 `new`** → 新项目，从空白开始
- **`existing`** → 已有项目，扫描代码 → 识别缺口

## 前置检查

1. **两阶段加载（索引优先）**：
   - 检查 `.allforai/product-map/task-index.json` → 加载索引
   - 不存在 → 回退到加载 `.allforai/product-map/product-map.json`
   - 若都不存在 → 输出「请先运行 /product-map 建立产品地图」，**立即终止**
2. 加载 `${CLAUDE_PLUGIN_ROOT}/templates/stacks.json` — 技术栈注册表

## 执行流程

1. 用 Read 工具加载 `${CLAUDE_PLUGIN_ROOT}/skills/project-setup.md` 获取完整工作流定义
2. 按 Step 0 → 1 → 2 → 3 → 4 → 5 顺序执行
3. 每个 Step 完成后输出结果摘要，自动进入下一个 Step

## Step 执行要求

每个 Step 完成后：
1. 将中间结果暂存对话上下文
2. 输出结果摘要
3. 自动进入下一个 Step（不停）

最终自动写入文件：
- `.allforai/project-forge/project-manifest.json`
- `.allforai/project-forge/project-manifest-report.md`
- `.allforai/project-forge/forge-decisions.json`
- `.allforai/project-forge/sub-projects/{name}/tech-profile.json`（每个子项目）

## 报告输出要求（强制执行）

执行完成后，必须在对话中直接输出报告摘要：

```
## 项目引导报告

> 执行模式: {new/existing}

### 子项目列表

| # | 名称 | 类型 | 技术栈 | 端口 | 模块数 |
|---|------|------|--------|------|--------|
| 1 | api-backend | backend | NestJS + TypeORM | 3001 | X |
| 2 | merchant-admin | admin | Next.js + Tailwind | 3000 | X |
| ... | ... | ... | ... | ... | ... |

### Monorepo 配置

- 工具: {pnpm-workspace/turborepo/nx/manual}
- Auth 策略: {jwt/session/oauth}

### 模块覆盖

- 总模块数: X
- 已分配: X (100%)
- 未分配: X (需关注)

### 产出文件

> `.allforai/project-forge/project-manifest.json`
> `.allforai/project-forge/project-manifest-report.md`
```

## 铁律

> 完整定义见 `${CLAUDE_PLUGIN_ROOT}/skills/project-setup.md` 的铁律章节。

1. **只问选择题** — 选项基于 product-map 和 stacks.json
2. **自动推进** — 每步完成后自动继续，不停等确认
3. **模块全覆盖** — 所有模块必须被分配
4. **模板内选择** — 只推荐已注册技术栈
5. **manifest 是合约** — 下游 skill 消费 project-manifest.json
