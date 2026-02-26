---
description: "设计转规格：product-design 产物 → 按子项目生成 requirements + design + tasks。支持全量或指定子项目"
argument-hint: "[mode: full] [sub-project-id]"
allowed-tools: ["Read", "Write", "Grep", "Glob", "Bash", "Task", "AskUserQuestion"]
---

# Design to Spec — 设计转规格

用户请求: $ARGUMENTS

## 插件根目录

所有文档路径基于插件安装目录: `${CLAUDE_PLUGIN_ROOT}`

## 模式路由

- **无参数 或 `full`** → 全量生成（全部子项目）
- **`sp-XXX`** → 仅指定子项目

## 前置检查

1. **project-manifest.json**：
   - 检查 `.allforai/project-forge/project-manifest.json`
   - 不存在 → 输出「请先运行 /project-setup 建立项目结构」，**立即终止**

2. **product-map 产物**（两阶段加载）：
   - 检查 `.allforai/product-map/task-index.json` → 加载索引
   - 不存在 → 回退到 `.allforai/product-map/product-map.json`
   - 若都不存在 → 输出「请先运行 /product-map 建立产品地图」，终止

3. **可选产物**：
   - `.allforai/screen-map/screen-index.json` / `screen-map.json` → 界面规格
   - `.allforai/use-case/use-case-tree.json` → 验收条件增强
   - `.allforai/feature-prune/prune-decisions.json` → CORE/DEFER/CUT 过滤
   - `.allforai/ui-design/ui-design-spec.md` → 设计 token

## 执行流程

1. 用 Read 工具加载 `${CLAUDE_PLUGIN_ROOT}/skills/design-to-spec.md` 获取完整工作流定义
2. 加载各子项目的 tech-profile.json（从 `.allforai/project-forge/sub-projects/{name}/`）
3. 按 Step 0 → 1 → 2 → 3 → 4 顺序执行
4. 每个 Step 完成后向用户展示结果摘要，等待确认

## Step 执行要求

每个 Step 完成后：
1. 将结果写入 `.allforai/project-forge/sub-projects/{name}/` 对应文件
2. 向用户展示结果摘要（任务数、需求项数、覆盖率等）
3. 等待用户确认后才进入下一个 Step

输出文件（每子项目）：
- `requirements.md`（Step 1）
- `design.md`（Step 2）
- `tasks.md`（Step 3）

## 报告输出要求（强制执行）

执行完成后，必须在对话中直接输出报告摘要：

```
## 设计转规格报告

### 各子项目规格概况

| 子项目 | 类型 | 需求项 | API 端点 | 页面 | 任务数 | CORE | DEFER |
|--------|------|--------|----------|------|--------|------|-------|
| api-backend | backend | X | X | — | X | X | X |
| merchant-admin | admin | X | — | X | X | X | X |
| ... | ... | ... | ... | ... | ... | ... | ... |

### 跨项目依赖

- 后端 B2 → 前端 B4（API 就绪后切换 mock）
- shared-types → 全部子项目 B1（类型定义共享）

### 执行顺序

Round 0: B0 Monorepo Setup
Round 1: 全部子项目 B1 (Foundation) 并行
Round 2: Backend B2 (API) ∥ Frontend B3 (UI)
Round 3: api-client + Frontend B4 (Integration)
Round 4: 全部子项目 B5 (Testing)

### 产出文件

> 每子项目: `.allforai/project-forge/sub-projects/{name}/requirements.md`
> 每子项目: `.allforai/project-forge/sub-projects/{name}/design.md`
> 每子项目: `.allforai/project-forge/sub-projects/{name}/tasks.md`
```

## 铁律

> 完整定义见 `${CLAUDE_PLUGIN_ROOT}/skills/design-to-spec.md` 的铁律章节。

1. **CORE 优先** — 仅 CORE 任务进入执行计划
2. **两阶段加载** — 先索引后全量，节省 token
3. **按端差异化** — 不同端类型生成不同 spec 内容
4. **任务必须原子** — 1-3 文件、15-30 分钟、单一目的
5. **跨项目依赖显式** — 写入 execution_order
