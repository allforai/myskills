---
name: code-replicate
description: >
  Code Replication Bridge: reverse-engineer existing codebases (any tech stack) into
  .allforai/ artifacts compatible with the dev-forge pipeline. 4 fidelity levels:
  interface (API contracts), functional (business behavior), architecture (patterns),
  exact (including bugs). Supports cross-stack migration.
version: "5.0.0"
---

# Code Replicate v5.0.0 — Code Replication Plugin

> Reverse-engineering bridge: existing code -> standard `.allforai/` artifacts -> dev-forge pipeline

## Overview

Code Replicate reverse-engineers existing codebases into standard `.allforai/` artifacts that feed directly into the dev-forge pipeline. It does not generate code — only artifacts. Industry and tech stack agnostic.

## Available Workflows

| Mode | Description |
|------|-------------|
| `code-replicate` | Full reverse-engineering pipeline (interactive guided) |
| `code-replicate functional ./src` | Replicate business behavior from local source |
| `code-replicate interface ./src` | Replicate API contracts only |
| `code-replicate exact ./src` | 100% fidelity replication including bugs |
| `code-replicate functional https://github.com/org/repo` | Replicate from remote repo |
| `cr-fidelity` | Verify replication fidelity (source vs target code) |
| `cr-visual` | Visual fidelity comparison (screenshot-based) |

## 4-Phase Pipeline

| Phase | Name | Description | Interaction |
|-------|------|-------------|-------------|
| 1 | Preflight | Parameter collection + Git clone | User interaction point 1 |
| 2 | Discovery + Confirm | Source scan + module summary + infrastructure inventory + abstraction extraction + user confirmation | User interaction point 2 (last) |
| 3 | Generate | LLM generates fragments per extraction-plan -> script merge -> standard artifacts | Silent |
| 4 | Verify & Handoff | Schema validation + XV verification + report | Silent |

> Full protocol: `./skills/code-replicate-core.md`

## Fidelity Levels

| Level | Analysis Depth | Standard Artifact Output |
|-------|---------------|------------------------|
| `interface` | Entry-layer signatures only | task-inventory (slim) + role-profiles (with audience_type) + product-map (with experience_priority) |
| `functional` | Read function bodies, trace logic | Above + business-flows (with systems/handoff) + use-case-tree (flat array) + task structured fields |
| `architecture` | Additional module dependency analysis | Above + task adds module/prerequisites/cross_dept |
| `exact` | Additional bug/constraint marking | Above + constraints.json + task.flags |

> Details: `./docs/fidelity-guide.md`

## Sub-Skills

| Skill File | Purpose |
|-----------|--------|
| `skills/code-replicate-core.md` | 4-phase protocol + iron laws + script reference |
| `skills/cr-backend.md` | Backend analysis: entry / service / data / cross-cutting layers |
| `skills/cr-frontend.md` | Frontend analysis: pages / components / state / interactions |
| `skills/cr-fullstack.md` | Fullstack: dual-stack analysis + cross-validation + infrastructure scan |
| `skills/cr-module.md` | Module: dependency boundary scan + external interface recording |
| `skills/cr-fidelity.md` | Fidelity verification: source vs target multi-dimensional comparison + repair loop |
| `skills/cr-visual.md` | Visual fidelity: source vs target screenshot structural comparison |

## Project Type Detection

When `--type` is not specified, scan the codebase to determine project type:

- **backend**: routes/controllers/middleware/models directories or files
- **frontend**: components/pages/store/hooks/screens directories or files
- **fullstack**: frontend and backend code coexist (monorepo or fullstack framework)
- **module**: requires explicit `--type module --module <path>`

## Skill Dispatch

Based on project type, load the corresponding skill file and execute its full workflow:

1. **backend** (or auto-detected as backend) -> load `./skills/cr-backend.md`
2. **frontend** (or auto-detected as frontend) -> load `./skills/cr-frontend.md`
3. **fullstack** (or auto-detected as fullstack) -> load `./skills/cr-fullstack.md`
4. **module** -> load `./skills/cr-module.md` (requires `--module` parameter)

All skill files internally load `./skills/code-replicate-core.md` as the 4-phase protocol foundation.

## Output Directory

```
.allforai/
├── product-map/          <- product-map, task-inventory, role-profiles,
│                           business-flows, constraints, indexes
├── experience-map/       <- experience-map.json (frontend/fullstack stub)
├── use-case/             <- use-case-tree, use-case-report
└── code-replicate/       <- replicate-config, source-summary,
                            discovery-profile, infrastructure-profile,
                            asset-inventory, extraction-plan,
                            stack-mapping, replicate-report,
                            fidelity-report
```

## Workflow Integration

```
code-replicate -> design-to-spec -> task-execute
    |
cr-fidelity (code-level fidelity — replicate-specific)
    |
product-verify (functional acceptance — shared with creation path)
    |
testforge (test quality — shared with creation path)
    |
cr-visual (visual fidelity — run after tests pass, App stable)
```

cr-fidelity verifies code replication. product-verify and testforge are shared with the creation path.
cr-visual runs last — requires a stable running App for screenshot comparison.

## Usage Examples

```
# Interactive guided mode
Tell the AI: "replicate this codebase"

# Replicate with specific fidelity
Tell the AI: "replicate functional ./src"
Tell the AI: "replicate exact ./src --type backend"

# Remote repository
Tell the AI: "replicate functional https://github.com/org/repo"
Tell the AI: "replicate functional org/repo#v2.0"

# Resume from specific phase
Tell the AI: "resume code-replicate from phase 3"

# After replication, verify fidelity
Tell the AI: "check replication fidelity"
Tell the AI: "compare visual fidelity"
```

## Documents

- `./docs/fidelity-guide.md` — Fidelity level details
- `./docs/analysis-principles.md` — General analysis guidance principles
- `./docs/stack-mappings.md` — Cross-stack mapping reference
- `./docs/schema-reference.md` — CR-specific schema definitions

## 执行引擎阶段声明

```yaml
# execution-engine: ./docs/execution-engine.md

phases:
  - id: preflight
    subagent_task: "预检：收集参数、克隆源码、确认复刻范围"
    input: ["用户输入"]
    output: ".allforai/code-replicate/replicate-config.json"
    rules: ["./skills/code-replicate-core.md"]

  - id: discovery
    subagent_task: "发现：扫描源码结构、模块摘要、基础设施清单、抽象提取"
    input: [".allforai/code-replicate/replicate-config.json", "源代码库"]
    output: ".allforai/code-replicate/discovery-profile.json, .allforai/code-replicate/extraction-plan.json"
    rules: ["./docs/analysis-principles.md"]
    depends_on: [preflight]

  - id: generate
    subagent_task: "生成：按模块 LLM 生成 → 脚本合并 → 标准产物"
    input: [".allforai/code-replicate/extraction-plan.json", "源代码库"]
    output: ".allforai/product-map/, .allforai/experience-map/"
    rules: ["./skills/code-replicate-core.md"]
    depends_on: [discovery]

  - id: verify
    subagent_task: "验证：schema 校验 + XV 交叉验证 + 还原度报告"
    input: [".allforai/product-map/", ".allforai/experience-map/", ".allforai/code-replicate/extraction-plan.json"]
    output: ".allforai/code-replicate/replicate-report.json"
    rules: ["./skills/cr-fidelity.md"]
    depends_on: [generate]
```

## full 模式执行

读取 `./docs/execution-engine.md` 获取调度协议。

主流程作为纯调度器执行：
1. 按 phases 声明的 depends_on 拓扑排序
2. 逐阶段 dispatch subagent，使用协议中的任务模板
3. 收集阶段摘要，选择性注入给下一阶段
4. 收到 UPSTREAM_DEFECT 时按协议回退
5. 所有阶段为线性依赖（preflight → discovery → generate → verify），无并行机会

## Orchestration

> Details: `./execution-playbook.md`
