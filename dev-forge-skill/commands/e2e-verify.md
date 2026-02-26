---
description: "跨端验证：从 business-flows 推导跨子项目 E2E 场景，Playwright 执行。模式: full / plan / run"
argument-hint: "[mode: full|plan|run]"
allowed-tools: ["Read", "Write", "Grep", "Glob", "Bash", "Task", "AskUserQuestion"]
---

# E2E Verify — 跨端验证

用户请求: $ARGUMENTS

## 插件根目录

所有文档路径基于插件安装目录: `${CLAUDE_PLUGIN_ROOT}`

## 模式路由

- **无参数 或 `full`** → 推导场景 + 执行全部
- **`plan`** → 仅推导场景，不执行（不需要应用运行）
- **`run`** → 加载已有 e2e-scenarios.json 并执行（需要应用运行）

## 前置检查

1. **project-manifest.json**：
   - 检查 `.allforai/project-forge/project-manifest.json`
   - 不存在 → 输出「请先运行 /project-setup 建立项目结构」，终止

2. **business-flows**：
   - 检查 `.allforai/product-map/flow-index.json`（索引优先）
   - 不存在 → 回退到 `.allforai/product-map/business-flows.json`
   - 若都不存在 → 输出「请先运行 /product-map 建立产品地图（包含业务流）」，终止

3. **run 模式额外检查**：
   - 检查 `.allforai/project-forge/e2e-scenarios.json`
   - 不存在 → 输出「请先运行 /e2e-verify plan 推导场景」，终止

4. **可选产物**：
   - `.allforai/use-case/use-case-tree.json` → E2E 级别用例补充

## 执行流程

1. 用 Read 工具加载 `${CLAUDE_PLUGIN_ROOT}/skills/e2e-verify.md` 获取完整工作流
2. 按 Step 0 → 1 → 2 → 3 → 4 顺序执行
3. plan 模式仅执行 Step 1（场景推导）
4. run 模式跳过 Step 1，直接从 Step 0 → 2 → 3 → 4

## Step 执行要求

每个 Step 完成后：
1. 将结果写入 `.allforai/project-forge/` 对应文件
2. 向用户展示结果摘要
3. 等待用户确认后才进入下一个 Step

输出文件：
- `e2e-scenarios.json`（Step 1）
- `e2e-report.json`（Step 4，机器版）
- `e2e-report.md`（Step 4，人类版）

## 报告输出要求（强制执行）

执行完成后，必须在对话中直接输出报告摘要：

```
## 跨端 E2E 验证报告

> 场景来源: business-flows.json
> 执行模式: {full/plan/run}

### 总览

| 维度 | 结果 |
|------|------|
| 场景总数 | X |
| 通过 | X |
| 失败 | X |
| 跳过 | X |

### 各子项目参与情况

| 子项目 | 参与场景数 | 失败数 | 待修复 |
|--------|-----------|--------|--------|
| merchant-admin | X | X | X |
| customer-web | X | X | X |
| api-backend | X | X | X |

### 需修复项

| # | 场景 | 失败步骤 | 子项目 | 分类 | 描述 |
|---|------|----------|--------|------|------|
| 1 | E2E-001 | Step 2 | customer-web | FIX_REQUIRED | ... |

### 产出文件

> 场景定义: `.allforai/project-forge/e2e-scenarios.json`
> 测试报告: `.allforai/project-forge/e2e-report.md`
> 截图目录: `e2e/screenshots/`
```

## 铁律

> 完整定义见 `${CLAUDE_PLUGIN_ROOT}/skills/e2e-verify.md` 的铁律章节。

1. **场景来自业务流** — 不凭空编造
2. **用户确认场景** — 执行前确认列表
3. **失败分类需确认** — 不自动归类
4. **不修改代码** — 只记录问题
5. **原生端降级** — 标记为手动验证点
