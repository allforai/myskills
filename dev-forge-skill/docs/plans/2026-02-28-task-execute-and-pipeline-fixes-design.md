# 设计文档：task-execute skill + 流水线断点修复

> 日期：2026-02-28

## 背景

Phase 4（实现阶段）是最耗时的环节，但缺少 skill 辅助。同时流水线存在 3 个数据流断点。

## 决策记录

- 执行者：Claude Code agent（非人类开发者）
- 验证粒度：每 Round 结束时
- 方案选择：方案 B — 新建独立 task-execute skill
- 执行策略：自动推断（per-Round，基于文件交叉检测）

## 改动清单

### 1. 新建 skills/task-execute.md

**职责**：加载 tasks.md → 逐 Round 执行 → 进度追踪(build-log.json) → 增量验证

**工作流**：
- Step 0: 加载 + 初始化 build-log.json
- Step 1: 执行策略推断（文件交叉检测 → subagent-driven / dispatching-parallel）
- Step 2: 逐任务执行（委托 superpowers skill）
- Step 3: Round 质量检查（lint/test）
- Step 4: Round 增量验证（scope 模式 product-verify）

**build-log.json**: Round 级状态机，任务级完成追踪，执行策略 per-Round。

**Resume**: 读 build-log.json current_round → 从第一个非 completed 任务继续。

### 2. 修改 skills/seed-forge.md — 补 4E 字段消费

Step 1-D 约束规则设计：显式读 task.rules + task.exceptions，不仅读 constraints.json。

### 3. 修改 skills/e2e-verify.md — 补负向用例消费

Step 1 场景推导：除 E2E 类型外，从 use-case-tree.json 提取 exception/boundary 类型用例作为负向测试场景。

### 4. 修改 commands/project-forge.md — Phase 4 调用 task-execute + 验证闭环

Phase 4 改为调用 /task-execute。新增 Phase 4.5 验证闭环：product-verify/e2e-verify 失败 → 生成修复任务 → 追加到 tasks.md → task-execute 执行修复 Round。

### 5. 修改 skills/product-verify.md — 新增 scope 模式

/product-verify scope --tasks T001,T002 --sub-projects api-backend
仅 S1+S3 范围过滤，S2/S4/Dynamic 跳过。
