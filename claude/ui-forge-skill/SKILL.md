---
name: ui-forge
description: >
  Implementation-stage UI refinement plugin for professional engineers. Use when
  frontend functionality already exists and the user wants to polish the UI,
  improve visual quality, strengthen interaction details, or restore the screen
  to match design specs, tokens, or screenshots. Prioritize design fidelity
  before aesthetic enhancement. Forked from frontend-design, but constrained for
  real product codebases and post-implementation use.
version: "1.0.0"
---

# UI Forge — 实现阶段 UI 锻造

> 基于 `frontend-design` 的 fork，但定位收窄为：功能完成后，对真实项目界面做增强或还原。

## 定位

`ui-forge` 不是产品设计插件，也不是主实现编排器。

- 不负责定义产品结构
- 不负责首次完成业务功能
- 不替代 `dev-forge`
- 只处理实现阶段的 UI 质量问题

适用场景：

- 页面已可用，但视觉质量一般
- 页面功能正确，但和设计稿 / token / screenshots 偏差较大
- 需要在不改业务语义的前提下提升成品感

## 包含内容

### 1. ui-forge — 单入口技能

> 详见 `${CLAUDE_PLUGIN_ROOT}/skills/ui-forge.md`

统一入口，内部先判断设计偏差，再决定动作：

- `fidelity-check` — 先判断实现是否偏离设计基线
- `restore` — 按设计规格、token、截图做还原修复
- `polish` — 在已基本对齐设计的前提下，强化视觉、层次、响应式、状态设计、微交互

### 2. /ui-forge — 单命令入口

> 详见 `${CLAUDE_PLUGIN_ROOT}/commands/ui-forge.md`

手动触发执行。当前版本不接入 `dev-forge` 自动编排。

## 设计原则

- `function-first` — 功能先完成，UI 后锻造
- `restore-before-polish` — 先对齐设计，再做增强
- `constraint-aware` — 优先遵守 spec、token、component contract
- `non-invasive` — 默认不改业务流程、不改接口契约、不重写页面语义
- `technical-team-oriented` — 面向专业研发，不使用空泛设计话术

## 执行引擎阶段声明

```yaml
# execution-engine: ${CLAUDE_PLUGIN_ROOT}/docs/execution-engine.md

phases:
  - id: fidelity-check
    subagent_task: "还原度检测：对比设计规格与当前实现的偏差"
    input: [".allforai/ui-design/", "前端代码库"]
    output: ".allforai/ui-forge/fidelity-assessment.json"
    rules: ["${CLAUDE_PLUGIN_ROOT}/docs/fidelity-checklist.md"]

  - id: restore
    subagent_task: "还原修复：按设计规格修复实现偏差"
    input: [".allforai/ui-forge/fidelity-assessment.json", ".allforai/ui-design/"]
    output: "代码变更"
    rules: ["${CLAUDE_PLUGIN_ROOT}/skills/ui-forge.md"]
    depends_on: [fidelity-check]

  - id: polish
    subagent_task: "视觉打磨：层次、响应式、状态设计、微交互增强"
    input: [".allforai/ui-design/", "前端代码库"]
    output: "代码变更"
    rules: ["${CLAUDE_PLUGIN_ROOT}/skills/ui-forge.md"]
    depends_on: [restore]
```

## full 模式执行

读取 `${CLAUDE_PLUGIN_ROOT}/docs/execution-engine.md` 获取调度协议。

主流程作为纯调度器执行：
1. 按 phases 声明的 depends_on 拓扑排序
2. 逐阶段 dispatch subagent，使用协议中的任务模板
3. 收集阶段摘要，选择性注入给下一阶段
4. 收到 UPSTREAM_DEFECT 时按协议回退
5. 所有阶段为线性依赖（fidelity-check → restore → polish），无并行机会

---

## 参考文档

- 定位说明：`${CLAUDE_PLUGIN_ROOT}/docs/positioning.md`
- 输入与边界：`${CLAUDE_PLUGIN_ROOT}/docs/input-contract.md`
- 还原度检查清单：`${CLAUDE_PLUGIN_ROOT}/docs/fidelity-checklist.md`
