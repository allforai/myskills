# 设计文档：design-to-spec 多子项目并行优化

> 日期：2026-03-02

## 背景

design-to-spec 当前对所有子项目串行执行 Step 1→2→3（requirements → design → tasks）。但分析表明：

- 各子项目的 Step 1-3 产出写入独立目录（`.allforai/project-forge/sub-projects/{name}/`），无文件冲突
- 唯一依赖：前端 design.md 需引用后端 design.md 中的 API 端点定义（API-first 约束）
- 后端完成后，多个前端子项目可并行执行

## 决策记录

- 并行粒度：Step 级并行（后端 Agent 完整执行 Step 1→2→2.5→3，然后前端 Agent 各自完整执行 Step 1→2→3）
- Step 2.5（OpenRouter 交叉审查）：在后端 Agent 内部执行，不增加额外同步点
- barrier 数量：2 个（后端完成 → 前端启动；前端全部完成 → Step 4）
- 改动文件：`design-to-spec.md` + `project-forge.md`，各 skill/template 零修改

## 当前串行流程（改前）

```
Step 0: 模块映射验证（全局）
    ↓
Step 1: Requirements 生成（逐子项目串行：backend → admin → web-customer → mobile）
    ↓
Step 2: Design 生成（逐子项目串行：backend 先 → 各前端依次）
    ↓
Step 2.5: Design 交叉审查（仅后端 design.md，OpenRouter）
    ↓
Step 3: Tasks 生成（逐子项目串行：backend → admin → web-customer → mobile）
    ↓
Step 4: 跨子项目依赖分析
    ↓
Step 5: 阶段末汇总确认
```

## 改后并行流程

```
Step 0: 模块映射验证（全局，编排器直接执行）
    ↓
Phase A — 后端 Agent（1 个 Agent 调用）:
    Agent(backend): Step 1 → Step 2 → Step 2.5 → Step 3
    ↓ 完成后
Phase B — 前端并行 Agent（单条消息发出 N 个 Agent 调用）:
    ┌── Agent(admin):         Step 1 → Step 2 → Step 3
    ├── Agent(web-customer):  Step 1 → Step 2 → Step 3
    └── Agent(mobile):        Step 1 → Step 2 → Step 3
    全部完成 ↓
Step 4: 跨子项目依赖分析（编排器直接执行）
    ↓
Step 5: 阶段末汇总确认（编排器直接执行）
```

## 改动清单（逐步平铺）

### 改动 1: project-forge.md — allowed-tools 增加 Agent

**文件**: `dev-forge-skill/commands/project-forge.md`
**位置**: frontmatter `allowed-tools` 行

在 allowed-tools 数组末尾追加 `"Agent"`。

### 改动 2: project-forge.md — Phase 2 流程描述更新

**文件**: `dev-forge-skill/commands/project-forge.md`
**位置**: Phase 2 描述区域

将 Phase 2 的描述从"逐子项目串行"改为"后端先行 + 前端并行"。更新进度展示文案。

### 改动 3: design-to-spec.md — 工作流总览更新

**文件**: `dev-forge-skill/skills/design-to-spec.md`
**位置**: `## 工作流` 代码块

将工作流总览图从串行改为并行结构。Step 0 和 Step 4-5 保持不变，Step 1-3 改为 Phase A + Phase B 结构。

### 改动 4: design-to-spec.md — Step 1-3 改为并行执行

**文件**: `dev-forge-skill/skills/design-to-spec.md`
**位置**: Step 1、Step 2、Step 2.5、Step 3 的描述

将 Step 1-3 从"逐子项目"串行描述改为"由 Agent 并行执行"。具体变化：

**Step 1 原文**:
```
Step 1: Requirements 生成（逐子项目）
  对每个子项目:
    a. 过滤...
    b. 加载...
    ...
```

**Step 1 改后**:
```
Step 1: Requirements 生成
  （由 Agent 在 Phase A/B 内执行，不再由编排器逐子项目调度）
  每个 Agent 对其负责的子项目执行:
    a. 过滤...
    b. 加载...
    ...
```

Step 2、Step 2.5、Step 3 做类似改动。核心是：步骤内容不变，但执行方式从"编排器逐个调度"变为"Agent 内部自主执行"。

### 改动 5: design-to-spec.md — 新增并行执行编排段落

**文件**: `dev-forge-skill/skills/design-to-spec.md`
**位置**: Step 0 和 Step 1 之间（或工作流代码块之后）

新增一个 `## 并行执行编排` 段落，包含以下内容：

#### 5a: 子项目分类

```
编排器将子项目按类型分为两组:
  后端组: type = "backend" 的子项目（通常 1 个）
  前端组: 其余所有子项目（admin/web-customer/web-mobile/mobile-native）
```

#### 5b: Phase A — 后端 Agent

```
Phase A: 启动 1 个 Agent 处理后端子项目
  Agent prompt 包含:
    - 子项目信息（name, type, tech_stack, assigned_modules）
    - 产品设计产物路径
    - 执行 Step 1 → Step 2 → Step 2.5 → Step 3 的完整指令
  Agent 产出: .allforai/project-forge/sub-projects/{backend-name}/
    ├── requirements.md
    ├── design.md（含 Step 2.5 审查结果）
    └── tasks.md
```

#### 5c: Phase B — 前端并行 Agent

```
Phase B: 后端 Agent 完成后，用单条消息发出 N 个 Agent 调用
  每个前端 Agent prompt 包含:
    - 子项目信息
    - 产品设计产物路径
    - 后端 design.md 路径（用于引用 API 端点定义）
    - 执行 Step 1 → Step 2 → Step 3 的指令
  每个 Agent 产出: .allforai/project-forge/sub-projects/{frontend-name}/
    ├── requirements.md
    ├── design.md
    └── tasks.md
```

#### 5d: Agent prompt 模板

```
你是 design-to-spec 的并行执行器。

任务: 为子项目 {sub-project-name} 生成完整的 spec 文档。

执行步骤:
1. 用 Read 工具加载 ${CLAUDE_PLUGIN_ROOT}/skills/design-to-spec.md（仅参考规则，不重复全局步骤）
2. 按 Step 1 (requirements) → Step 2 (design) [→ Step 2.5 仅后端] → Step 3 (tasks) 执行
3. 产出写入 .allforai/project-forge/sub-projects/{sub-project-name}/

子项目信息:
- name: {name}
- type: {type}
- tech_stack: {tech_stack}
- assigned_modules: {modules}

上下文:
- project-manifest.json: .allforai/project-forge/project-manifest.json
- 产品设计产物: .allforai/product-map/, .allforai/screen-map/ 等
- 后端 design.md: {backend-design-path}（仅前端 Agent 引用）
{自动模式标记: __orchestrator_auto: true（若自动模式激活）}

重要:
- 仅处理本子项目，不读写其他子项目的产出目录
- 按端差异化规则生成（参考 design-to-spec.md 的各端差异化表格）
- 遵循两阶段加载（先 index 再 full data）
- 前端 Agent: API 调用必须引用后端 design.md 中已定义的端点 ID
- 预置脚本优先: 检查 ${CLAUDE_PLUGIN_ROOT}/scripts/ 是否有可用脚本
```

### 改动 6: design-to-spec.md — 错误处理

**文件**: `dev-forge-skill/skills/design-to-spec.md`
**位置**: 并行执行编排段落内

```
Phase A 错误处理:
  后端 Agent 成功 → 进入 Phase B
  后端 Agent 失败 →
    向用户报告错误原因
    询问: 重试 / 中止
    注: 后端失败不可跳过（前端依赖后端 design.md）

Phase B 错误处理:
  全部成功 → 进入 Step 4
  部分失败 →
    成功的 Agent: 正常收集产出
    失败的 Agent: 记录错误信息
    向用户报告:
      "前端并行执行结果:
       ✓ admin: 完成 (requirements: N, design: N API, tasks: N)
       ✗ web-customer: 失败 — {错误原因}
       ✓ mobile: 完成 (requirements: N, design: N 页面, tasks: N)"
    询问:
      1. 重试失败的子项目（仅重跑失败的 Agent）
      2. 跳过继续到 Step 4（依赖分析标注缺失子项目）
      3. 中止流程
  全部失败 →
    向用户报告所有错误
    询问: 全部重试 / 中止

自动模式:
  后端 Agent 失败 → ERROR（停）
  前端 Agent 部分失败 → WARNING（记日志继续到 Step 4）
  前端 Agent 全部失败 → ERROR（停）
```

### 改动 7: design-to-spec.md — Resume 模式

**文件**: `dev-forge-skill/skills/design-to-spec.md`
**位置**: 并行执行编排段落内（或现有 resume 相关位置）

```
resume 模式检测 Step 1-3 完成状态:
  检测方式: 检查 .allforai/project-forge/sub-projects/{name}/ 下三件套是否齐全
    - requirements.md 存在
    - design.md 存在
    - tasks.md 存在
  三件全 → 该子项目已完成

  判定:
    后端 + 所有前端三件套全存在 → 跳过 Step 1-3，进入 Step 4
    后端三件套存在，部分前端缺失 → 跳过 Phase A，Phase B 仅启动缺失子项目的 Agent
    后端三件套缺失 → 从 Phase A 重新开始
```

### 改动 8: design-to-spec.md — 铁律更新

**文件**: `dev-forge-skill/skills/design-to-spec.md`
**位置**: `## 5 条铁律` 末尾

新增第 6 条铁律：

```
### 6. 并行 Agent 产出隔离

Phase A/B 的并行 Agent 各自写入独立子项目目录，不读写其他 Agent 的产出。
唯一跨 Agent 引用：前端 Agent 只读后端 design.md（API 端点定义），不修改。
```

### 改动 9: design-to-spec.md — 汇总模板更新

**文件**: `dev-forge-skill/skills/design-to-spec.md`
**位置**: Step 5 汇总确认模板

更新汇总模板，展示 Phase A/B 分组执行结果：

```
Phase A (后端):
| 子项目 | requirements | design | tasks | Step 2.5 审查 |
|--------|-------------|--------|-------|--------------|
| {backend} | {N} 需求项 | {N} API端点 | {N} 任务 | {issues} |

Phase B (前端并行):
| 子项目 | requirements | design | tasks | 状态 |
|--------|-------------|--------|-------|------|
| {admin} | {N} 需求项 | {N} 页面 | {N} 任务 | 完成/失败 |
| {web}   | ... | ... | ... | ... |
| {mobile}| ... | ... | ... | ... |
```

## 不改动的文件

以下文件不做任何修改：
- `skills/project-setup.md` — 项目引导逻辑不变
- `skills/project-scaffold.md` — 脚手架生成不变
- `skills/task-execute.md` — 已有自己的并行策略
- `skills/e2e-verify.md` — 验证逻辑不变
- `skills/seed-forge.md` — 种子数据不变
- `skills/product-verify.md` — 产品验收不变
- `templates/` — 技术栈模板不变

## 性能预期

串行耗时 = T_后端 + T_前端1 + T_前端2 + ... + T_前端N
并行耗时 = T_后端 + max(T_前端1, ..., T_前端N)

典型 3 前端子项目：加速约 2-3x
单子项目（仅后端）：无影响，退化为纯串行

## 风险评估

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| 前端 Agent 引用后端 API 端点有误 | 低 | 前端 design.md 引用不存在的端点 | 后端 design.md 在前端启动前已完成且固定 |
| 前端 Agent 上下文不足 | 中 | 产出质量下降 | prompt 完整传递子项目信息 + 产品设计产物路径 |
| Agent 并发超过平台限制 | 低 | 部分 Agent 排队 | 退化为部分并行，不影响正确性 |
| 单子项目产品（仅后端） | 无 | — | 无前端 Agent 启动，自动退化为纯串行 |
