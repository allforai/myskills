---
description: "服务端代码调优：架构合规、重复检测、抽象分析、验证规范。模式: full / compliance / duplication / abstraction / report"
argument-hint: "[mode: full|compliance|duplication|abstraction|report] [--lifecycle pre-launch|maintenance]"
allowed-tools: ["Read", "Write", "Grep", "Glob", "Bash", "Task", "AskUserQuestion"]
---

# Code-Tuner — 服务端代码调优

用户请求: $ARGUMENTS

## 插件根目录

所有文档路径基于插件安装目录: `${CLAUDE_PLUGIN_ROOT}`

## 模式路由

根据用户参数决定执行模式：

- **无参数 或 `full`** → 完整分析：Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 4
- **`compliance`** → 仅架构合规：Phase 0 → Phase 1 → Phase 4
- **`duplication`** → 仅重复检测：Phase 0 → Phase 2 → Phase 4
- **`abstraction`** → 仅抽象分析：Phase 0 → Phase 3 → Phase 4
- **`report`** → 重新生成报告：读取已有的 phase 输出，重新生成 Phase 4

## 生命周期模式

从参数中解析 `--lifecycle`：

- **`pre-launch`（默认）** → 未上线模式，激进优化建议
- **`maintenance`** → 维护期模式，保守优化建议

如果用户未指定，询问用户项目状态。

## 前置检查：项目类型验证（强制执行）

在执行任何分析之前，必须先验证目标项目是否为服务端代码项目。

**检测方法：** 在项目根目录扫描以下配置文件是否存在至少一个：
- `pom.xml`, `build.gradle`, `build.gradle.kts` (Java)
- `go.mod` (Go)
- `package.json` (Node.js) — 需含后端框架依赖（express, nestjs, koa, fastify 等）
- `requirements.txt`, `pyproject.toml`, `setup.py`, `manage.py` (Python)
- `*.csproj`, `*.sln` (C#/.NET)
- `Cargo.toml` (Rust)
- `composer.json` (PHP)
- `Gemfile` (Ruby)

**如果找不到任何服务端技术栈配置文件：**

直接告知用户并终止，不执行后续任何 Phase：

```
code-tuner 专为服务端代码（Java/Go/Node.js/Python/.NET/Rust/PHP/Ruby 后端项目）设计。

当前项目未检测到服务端技术栈配置文件，不是 code-tuner 的最佳分析对象。

如需分析此项目，可考虑其他工具。
```

**不要勉强分析非服务端项目。** 对前端项目、纯 Markdown 项目、配置仓库、文档仓库等，code-tuner 的规则体系不适用，分析结果无意义。

---

## 执行流程

1. **【强制】执行前置检查**（见上方"项目类型验证"），不通过则终止
2. 用 Read 工具读取 `${CLAUDE_PLUGIN_ROOT}/SKILL.md` 获取完整目标定义和关键原则
3. 根据模式按需读取对应阶段的详细文档
4. 按工作流执行
5. **【强制】执行完毕后，必须在对话中直接输出完整的报告摘要（见下方"报告输出要求"）**

## 详细文档（按需用 Read 工具加载）

- `${CLAUDE_PLUGIN_ROOT}/SKILL.md` — 目标、关键原则、工作流总览
- `${CLAUDE_PLUGIN_ROOT}/references/phase0-profile.md` — Phase 0: 项目画像详解
- `${CLAUDE_PLUGIN_ROOT}/references/phase1-compliance.md` — Phase 1: 架构合规规则
- `${CLAUDE_PLUGIN_ROOT}/references/phase2-duplicates.md` — Phase 2: 重复检测方法
- `${CLAUDE_PLUGIN_ROOT}/references/phase3-abstractions.md` — Phase 3: 抽象机会分析
- `${CLAUDE_PLUGIN_ROOT}/references/phase4-report.md` — Phase 4: 评分与报告生成
- `${CLAUDE_PLUGIN_ROOT}/references/layer-mapping.md` — 跨语言层级映射速查

## Phase 0 执行要求

Phase 0 是所有模式的必经阶段。执行前先检查项目中是否已存在 `.allforai/code-tuner/tuner-profile.json`：

- **已存在** → 读取并展示给用户确认是否仍然有效，有效则跳过 Phase 0
- **不存在** → 执行完整 Phase 0，生成画像后请用户确认

画像确认内容：
1. 技术栈识别结果
2. 架构类型（三层 / 两层 / DDD / 混合）
3. 层级映射（实际目录 → 逻辑角色）
4. 模块列表
5. 数据模型概况（实体数、DTO/VO数、公共字段）

**以上五项都必须用户确认后才能进入后续 Phase。**

## 各 Phase 执行要求

每个 Phase 执行前，用 Read 工具加载对应的 reference 文档获取详细规则和检测方法。

每个 Phase 完成后，将结果写入 `.allforai/code-tuner/` 目录下对应的 JSON 文件。

## 报告输出要求（强制执行）

分析完成后，必须做两件事：

### 1. 保存报告文件

将完整报告写入 `.allforai/code-tuner/` 目录：
- `tuner-report.md` — 综合报告
- `tuner-tasks.json` — 重构任务清单

### 2. 在对话中直接输出报告摘要

**不要只说"报告已完成"或"报告已保存"。必须在对话中直接展示以下内容：**

```
## 代码调优报告摘要

> 分析时间: {时间}
> 分析模式: {full/compliance/duplication/abstraction}
> 生命周期: {pre-launch/maintenance}
> 项目规模: {文件数} 文件 / {代码行数} 行 / {模块数} 个模块

### 综合评分

| 维度 | 得分 | 权重 | 加权分 |
|------|------|------|--------|
| 架构合规度 | XX/100 | 25% | XX |
| 代码重复率 | XX/100 | 25% | XX |
| 抽象合理度 | XX/100 | 20% | XX |
| 验证规范度 | XX/100 | 15% | XX |
| 数据模型规范度 | XX/100 | 15% | XX |
| **综合评分** | | | **XX/100** |

### 问题总览

| 级别 | 数量 |
|------|------|
| 🔴 Critical (必须修复) | X |
| 🟡 Warning (建议修复) | X |
| 🔵 Info (参考) | X |

### 🔴 Critical 问题列表
(逐条列出：规则ID、位置、问题描述、修复建议)

### 🟡 Warning 问题列表
(逐条列出)

### 重复热力图
(哪些模块之间重复最多)

### 下一步建议
1. 优先修复 🔴 Critical 问题
2. 按 tuner-tasks.json 中的任务顺序逐步执行
3. 修复后可以重新运行 `/code-tuner report` 查看分数变化

> 完整报告已保存至: `.allforai/code-tuner/tuner-report.md`
> 重构任务清单: `.allforai/code-tuner/tuner-tasks.json`
```

**关键：摘要必须包含具体的问题列表和修复建议，不能只给统计数字。用户看完摘要就能知道出了什么问题、在哪里、怎么修。**
