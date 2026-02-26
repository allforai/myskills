---
description: "脚手架生成：按技术栈模板生成项目骨架 + Mock 后端。模式: full / existing / 指定子项目"
argument-hint: "[mode: full] [sub-project-id]"
allowed-tools: ["Read", "Write", "Grep", "Glob", "Bash", "Task", "AskUserQuestion"]
---

# Project Scaffold — 脚手架生成

用户请求: $ARGUMENTS

## 插件根目录

所有文档路径基于插件安装目录: `${CLAUDE_PLUGIN_ROOT}`

## 模式路由

- **无参数 或 `full`** → 全量生成（monorepo 根 + 全部子项目 + mock-server）
- **`sp-XXX`** → 仅指定子项目的骨架

## 前置检查

1. **project-manifest.json**：
   - 检查 `.allforai/project-forge/project-manifest.json`
   - 不存在 → 输出「请先运行 /project-setup 建立项目结构」，终止

2. **design 文档**：
   - 检查各子项目的 `.allforai/project-forge/sub-projects/{name}/design.md`
   - 不存在 → 输出「请先运行 /design-to-spec 生成设计文档」，终止

3. **技术栈模板**：
   - 从 tech-profile.json 获取 template_id
   - 加载 `${CLAUDE_PLUGIN_ROOT}/templates/stacks.json`
   - 加载对应模板文件（如 `${CLAUDE_PLUGIN_ROOT}/templates/backend/nestjs-typeorm.md`）

4. **可选产物**：
   - `.allforai/seed-forge/seed-plan.json` → mock 数据丰富度提升

## 执行流程

1. 用 Read 工具加载 `${CLAUDE_PLUGIN_ROOT}/skills/project-scaffold.md` 获取完整工作流
2. 加载 `${CLAUDE_PLUGIN_ROOT}/templates/monorepo.md` — monorepo 配置模板
3. 加载 `${CLAUDE_PLUGIN_ROOT}/templates/mock-server.md` — mock 后端模板
4. 按 Step 0 → 1 → 2 → 3 → 4 → 5 → 6 顺序执行
5. 每个 Step 完成后向用户展示结果摘要，等待确认

## Step 执行要求

每个 Step 完成后：
1. 将生成的文件写入项目目录
2. 更新 scaffold-manifest.json
3. 向用户展示结果摘要（生成了多少文件、哪些子项目）
4. 等待用户确认后才进入下一个 Step

## 报告输出要求（强制执行）

执行完成后，必须在对话中直接输出报告摘要：

```
## 脚手架生成报告

> 模式: {new/existing}

### 生成统计

| 子项目 | 类型 | 技术栈 | 文件数 | 状态 |
|--------|------|--------|--------|------|
| monorepo-root | infra | {tool} | X | 完成 |
| shared-types | package | TypeScript | X | 完成 |
| api-backend | backend | NestJS | X | 完成 |
| merchant-admin | admin | Next.js | X | 完成 |
| mock-server | infra | Express | X | 完成 |
| e2e | test | Playwright | X | 完成 |

### Mock 后端

- 端点数: X
- Fixture 实体数: X
- 数据来源: seed-plan.json / 最小占位

### 启动指令

1. pnpm install
2. pnpm mock（启动 mock-server）
3. curl http://localhost:4000/health

### 产出文件

> 脚手架清单: `.allforai/project-forge/sub-projects/{name}/scaffold-manifest.json`
```

## 铁律

> 完整定义见 `${CLAUDE_PLUGIN_ROOT}/skills/project-scaffold.md` 的铁律章节。

1. **骨架是桩** — 只生成结构和配置，不填充业务逻辑
2. **existing 绝不覆盖** — 仅补缺文件
3. **Mock 数据来自 seed-forge** — 优先使用 seed-plan.json
4. **文件清单全记录** — scaffold-manifest.json 追踪所有生成文件
5. **启动验证必须** — 提示用户安装并验证 mock-server
