# Meta-Skill Architecture Design

> 将 myskills 全部 6 个 skill 统一为 meta-skill 体系：一个泛化生成器 + 项目专属特化产物 + LLM 驱动的状态机调度。

## 1. 问题

现有 6 个 skill（code-replicate, dev-forge, code-tuner, ui-forge, product-design, demo-forge）共享同一个痛点：**泛化与特化的冲突**。

- 代码层 skill 的执行逻辑强依赖技术栈，但 skill 文件必须写成泛化的
- LLM 运行时同时理解框架规则 + 推理特化逻辑，注意力被稀释
- 产物层 skill（product-design, demo-forge）虽不依赖技术栈，但依赖业务领域，同样靠 LLM 运行时推理
- 现有管线是线性的（Phase 1→2→3→4），但 LLM 工作本质上是状态迁移——任何环节都可能不足，需要回退补充

## 2. 核心决策记录

| # | 决策 | 选项 | 选择 | 原因 |
|---|------|------|------|------|
| 1 | 改造范围 | 只改 code-replicate / 统一 meta-skill | 统一 | code-replicate 依赖下游 dev-forge，单独改造形成耦合 |
| 2 | 翻译目标平台 | 仅前端移动端 / 全栈通用 | 全栈通用 | 但前后端验收方式不同，由生成的 node-spec 特化 |
| 3 | 验收泛化 | 硬编码技术栈命令 / LLM 推理 | LLM 推理 | skill 是泛化的，验收命令由生成器特化写入 node-spec |
| 4 | 架构模式 | 运行时泛化 / 生成时特化（meta-skill） | 生成时特化 | 生成的 skill 短、具体、零推理开销，用户可检查和修改 |
| 5 | 覆盖范围 | 仅代码层 4 个 skill / 全部 6 个 | 全部 6 个 | 产物层也依赖业务领域，同样受益于特化 |
| 6 | 实现方案 | 单层 / 两层（meta + orchestrator）/ 单体 | 两层 | 保持模块化（skill 可单独执行）+ 统一 orchestrator 处理跨 skill 回退 |
| 7 | 生成器 Discovery 深度 | 复用 Phase 2 / 轻量 / 两轮（轻量 + 深度 + 自我修正） | 两轮 | 轻量生成骨架，执行时深度 Discovery，发现不足时 skill 自我修正 |
| 8 | 生成产物注入方式 | .allforai/ / Claude Code skill 路径 / JSON 配置 | skill 路径 | .claude/commands/ 是 Claude Code 项目级命令目录，自动可用 |
| 9 | 生成产物生命周期 | 保留复用 / 用完即弃 | 用完即弃 | 项目在变，每次重新生成成本低 |
| 10 | 独立命令 vs 单一入口 | /replicate + /forge + /tune / /bootstrap + /run | 两个命令 | 同一状态机不同目标，多命令没意义 |
| 11 | 状态迁移 | 硬编码 transitions / LLM 自主决策 + safety 兜底 | LLM + safety | 参考 DeerFlow：不预定义迁移条件，LLM 看 state + error 自行路由 |
| 12 | 外部状态管理框架 | LangGraph MCP / 纯 Claude Code 工具 | 纯 Claude Code | 状态管理复杂度在推理层不在管道层，JSON 文件 + 小脚本足够 |
| 13 | 失败回溯方式 | 逐跳回溯 / 全链路诊断 | 全链路诊断 | 逐跳慢且扩展推理分散，一次诊断定位根因 + 同类 gap + 完整修复计划 |
| 14 | 上下文管理 | 依赖对话历史 / 状态文件为 ground truth | 文件 | state-machine.json 是唯一状态源，对话历史可压缩，跨会话可恢复 |
| 15 | 跨项目经验 | 每次从零 / 累积学习 | 累积学习 | knowledge/learned/ 存储实际执行发现，下次 bootstrap 时参考 |
| 16 | 反馈闭环 | 本地积累 / 匿名上报 | 两者兼有 | 通用改进匿名提交 GitHub Issue（用户确认），项目特有经验仅留本地 |

## 3. 整体架构

### 两层架构

```
Layer 1: Meta-Skill（生成器）—— 仓库里维护的唯一代码层 skill
  输入：目标项目目录
  过程：轻量分析（技术栈、业务领域、模块结构）
  输出：项目专属的 state-machine + node-specs + commands

Layer 2: 生成产物（全部特化，用完即弃）
  orchestrator  — 项目专属状态机调度器（/run 命令）
  node-specs/*  — 每个状态节点的完整 subagent 指令
  state-machine.json — 节点列表 + safety 规则 + 进度
```

### 执行流程

```
用户 /bootstrap → meta-skill 轻量分析 → 生成特化产物 → 写入项目
用户 /run [目标] → orchestrator 循环 → 派发 subagent 执行 node-spec
                  → LLM 评估状态 → 前进 / 回退 / 自我修正 / 中断
                  → safety 机械兜底（循环检测、进度单调性）
```

### 用户命令

| 命令 | 来源 | 功能 |
|------|------|------|
| `/bootstrap` | meta-skill plugin | 分析项目 → 生成特化 skill |
| `/run [目标描述]` | 生成到 .claude/commands/ | 执行状态机，目标由 LLM 从描述匹配 |

`/run` 的目标示例：
- `/run 逆向分析` → 跑到 generate-artifacts
- `/run 复刻到 SwiftUI` → 跑到 compile-verify
- `/run 代码治理` → 跑 tune 节点
- `/run 视觉验收` → 跑到 visual-verify

## 4. 状态机模型

### 设计原则（参考 DeerFlow）

1. **不硬编码迁移条件** — 不需要 `transitions` 字段。orchestrator LLM 看 state + error context 自行决定下一步
2. **错误不 crash，变成上下文** — subagent 返回的失败信息作为 LLM 的决策输入，不需要显式的 correction_signal 格式
3. **循环检测用 hash + 滑动窗口** — `hash(node_id + 关键上下文)`，warn 3 / stop 5，不限制具体哪些循环合法
4. **safety 是机械层** — 不经过 LLM，硬逻辑兜底

### state-machine.json 格式

```json
{
  "nodes": [
    {
      "id": "discovery-structure",
      "description": "扫描 React+Express 项目结构...",
      "entry_requires": ["replicate-config.json exists"],
      "exit_requires": ["file-catalog.json exists", "module coverage >= 50%"],
      "hints": ["React 组件在 src/components/", "Express 路由在 server/routes/"]
    }
  ],
  "safety": {
    "loop_detection": { "warn_threshold": 3, "stop_threshold": 5 },
    "max_global_iterations": 30,
    "progress_monotonicity": { "check_interval": 5, "violation_action": "output current best + TODO list" },
    "max_concurrent_nodes": 3
  },
  "progress": {
    "completed_nodes": [],
    "current_node": null,
    "iteration_count": 0,
    "corrections_applied": []
  }
}
```

### Orchestrator 核心循环

```
loop:
  1. 读 state-machine.json（progress + 节点列表 + 各节点摘要）
     — 状态全部从文件读，不依赖对话历史
  2. 机械评估 entry/exit_requires（调 check_requires.py）
  3. LLM 评估（仅在需要决策时）：
     - 多个节点就绪 → 选哪个
     - exit 不满足 → 自循环 / 回退 / 中断
     - 失败 → 触发全链路诊断（Section 9）
  4. 更新 progress + 写回 state-machine.json
  5. 派发 subagent 执行目标节点（读对应 node-spec）
  6. subagent 返回结果
  7. 压缩结果为 ≤500 字摘要，写入 state-machine.json 的 node_summaries
     — 完整返回不留在对话历史，需要时诊断 subagent 通过 Read tool 读产物文件
  8. safety 检查（循环检测、进度单调性）
  9. 回到 1

终止：目标节点 exit_requires 满足 / safety 触发 / 用户中断

并行：多个节点 entry_requires 同时满足且互不依赖 → Agent tool 并行派发
```

### 上下文管理

orchestrator LLM 每次循环看到的上下文：

```
固定部分（每次从文件读）：
  - state-machine.json: 节点列表 + safety 规则 + progress + node_summaries
  - 当前目标描述

滑动窗口（对话历史中保留）：
  - 最近 2-3 个节点的完整返回
  - 最近 1 次诊断结果（如有）

不在上下文中（需要时按需读取）：
  - 旧节点的完整返回 → 诊断 subagent 通过 Read tool 读
  - 产物文件内容 → subagent 自行读取
  - node-spec 文件 → subagent 执行时读取
```

**核心原则：state-machine.json 是 ground truth，不是对话历史。** 即使对话被压缩或跨会话恢复，orchestrator 读文件就能完整恢复状态。

### Skill 自我修正

不需要显式修正协议。修正是 orchestrator 的正常行为：

```
subagent 返回 "编译失败，styled-components 没有映射"
  → orchestrator LLM 看到错误
  → 决定：补充映射表 → Edit node-spec → 重新派发
```

node-spec 的修改是 orchestrator 用 Edit tool 做的普通文件编辑。

## 5. Node-Spec 格式

每个 node-spec 是一个完整的 subagent 指令，包含执行所需的全部上下文。subagent 不需要读别的文件。

```markdown
---
node: translate-frontend
entry_requires:
  - dag.json exists
  - upstream dependencies compiled
exit_requires:
  - target code compiles
---

# 任务：将 React 前端组件翻译为 SwiftUI

## 项目上下文
- 源：React 18 + Redux Toolkit + React Router v6
- 目标：SwiftUI + @Observable + NavigationStack
- 构建命令：xcodebuild -scheme MyApp build

## 翻译策略
- low 复杂度（纯 UI）→ direct_translate
- medium（有状态）→ translate_with_adapt
- high（复杂业务）→ intent_rebuild，读 .allforai/ 产物而非源码

## 映射表
| React | SwiftUI |
|-------|---------|
| useState | @State |
| useEffect(,[]) | .task |
| useContext | @Environment |
| Redux useSelector | @Observable class |
| ... | ... |

## 验收命令
xcodebuild -scheme MyApp build 2>&1 | tail -20

## 编译自循环
翻译后编译，失败把错误喂回去重新翻译。

## Hints
- feature-sliced design，每个 feature/ 下有独立的 components/hooks/api
- Redux store 在 src/store/，12 个 slice
```

**关键特性**：
- 全部特化，零条件分支
- 不同项目生成的 node-spec 内容完全不同，但格式相同
- 映射表、验收命令、hints 全部是项目专属的

### 翻译策略选择

按组件复杂度（Analyzer 阶段已评估）自动选择：

| 策略 | 适用 | LLM 输入 | 输出 |
|------|------|---------|------|
| direct_translate | low（纯 UI，无业务逻辑） | 源组件代码 + 映射表 | 语法转换，保持结构 |
| translate_with_adapt | medium（有状态，逻辑可控） | 源组件代码 + 目标平台 patterns | 翻译逻辑，重构状态管理和导航 |
| intent_rebuild | high（复杂业务，跨模块依赖） | JSON 产物规格（不看源码） | 从意图生成，目标平台原生风格 |

## 6. Meta-Skill 生成器

### 轻量分析范围

不做 file card、不做 quiz 校验、不做覆盖率检查。只看懂项目「长什么样」：

1. 读根目录文件（package.json, go.mod, Cargo.toml...）→ 语言、框架、包管理器
2. 扫描顶层目录（1-2 层）→ 模块边界、前后端分离方式
3. 读配置文件（tsconfig, docker-compose, CI/CD）→ 构建工具链
4. 读 README / docs → 业务领域、项目目的
5. 采样读 3-5 个核心文件 → 代码风格、架构模式

产出 `bootstrap-profile.json`：

```json
{
  "project_name": "my-ecommerce",
  "business_domain": "电商",
  "business_context": "B2C 在线商城，核心流程：商品浏览→购物车→下单→支付→履约",
  "tech_stacks": [
    { "role": "frontend", "language": "TypeScript", "framework": "React 18", "state": "Redux Toolkit" },
    { "role": "backend", "language": "Go", "framework": "Gin", "orm": "GORM", "db": "PostgreSQL" }
  ],
  "modules": [
    { "id": "M001", "path": "src/components/", "role": "frontend" },
    { "id": "M002", "path": "server/handlers/", "role": "backend" }
  ],
  "build_commands": { "frontend": "npm run build", "backend": "go build ./cmd/server" },
  "detected_patterns": ["REST API", "JWT auth", "Redis cache", "S3 file storage"]
}
```

### 知识库结构

```
claude/meta-skill/knowledge/
├── nodes/              # 节点模板（从现有 skill 提炼的通用协议）
│   ├── discovery.md
│   ├── product-analysis.md
│   ├── generate-artifacts.md
│   ├── translate.md
│   ├── compile-verify.md
│   ├── test-verify.md
│   ├── visual-verify.md
│   ├── tune.md
│   ├── ui-forge.md
│   └── demo-forge.md
├── mappings/           # 技术栈映射（预置 + 可扩展）
│   ├── react-swiftui.md
│   ├── react-compose.md
│   ├── express-gin.md
│   └── ...
├── domains/            # 业务领域知识
│   ├── ecommerce.md
│   ├── fintech.md
│   └── ...
├── learned/            # 跨项目经验（从实际执行中自动提取）
│   ├── react-swiftui.md      # 实际跑出来的映射补充
│   ├── express-gin.md         # 运行时发现的映射问题
│   └── discovery-patterns.md  # 常见的 discovery 盲区
├── safety.md           # safety 规则模板
└── orchestrator-template.md  # /run 命令模板
```

### 跨项目经验学习

`/run` 执行完成后，orchestrator 提取本次执行中的关键发现，写入 `knowledge/learned/`：

**提取来源：**
- state-machine.json 的 `corrections_applied`（node-spec 被修正的记录）
- `diagnosis_history`（诊断发现的 gap 模式）
- `prevention` 规则（运行时发现需要加入的检查项）

**提取格式（每个文件追加）：**
```markdown
## [2026-03-30] my-ecommerce 项目

### 映射补充
- styled-components css`` → SwiftUI ViewModifier（生成器遗漏，运行时修正）
- ThemeProvider → @Environment(\.theme)

### Discovery 盲区
- server/handlers/ 目录需要全量扫描，不能只看 key_files
- 配置文件（routes.yaml）可能包含路由定义，不能跳过

### 验收补充
- 订单域发现 CRUD 不完整，建议 product-analysis 节点检查每个业务域的操作完整性
```

**消费方式：** 下次 `/bootstrap` 生成 node-spec 时，除了读 `knowledge/mappings/`（预置），还读 `knowledge/learned/`（经验）。如果经验和预置冲突，经验优先（因为它来自实际执行验证）。

**与 Decision 9「用完即弃」不冲突**——node-spec 文件丢弃，但从中提取的经验持久化到知识库。

### 上游反馈：匿名 Issue 提交

执行过程中发现的 skill 改进机会（映射缺失、Discovery 盲区、验收规则不足等），如果具有通用价值（不是项目特有的），orchestrator 在执行结束时向用户提议提交到 myskills 的 GitHub Issues。

**隐私规则：**
- 不包含项目名称、公司名称、代码片段、文件路径、业务描述
- 不包含用户身份信息（用户名、邮箱、IP）
- 只提交**抽象化的改进建议**，例如：
  - "react-swiftui 映射表缺少 styled-components → ViewModifier 的映射"
  - "discovery 节点对 handler 目录的默认覆盖率阈值(50%)偏低，建议提升到 80%"
  - "全链路诊断在深度 >4 跳时收敛较慢，建议调整收敛控制"

**流程：**
```
/run 执行完毕
  ↓
orchestrator 从 corrections_applied + diagnosis_history 中筛选通用改进项
  ↓
脱敏：去除所有项目特定信息，抽象为技术栈级别的描述
  ↓
展示给用户：
  "本次执行发现了 2 条可能对 meta-skill 有改进价值的经验：
   1. react-swiftui 映射缺少 styled-components 支持
   2. discovery 对 handler 目录的覆盖率阈值偏低

   是否愿意匿名提交到 myskills GitHub Issues？(y/n)"
  ↓
用户确认 → gh issue create（标签: feedback/auto, 技术栈标签）
用户拒绝 → 仅写入本地 knowledge/learned/
```

**Issue 格式：**
```markdown
## [Auto Feedback] {技术栈对} — {一句话描述}

**来源**: meta-skill 自动反馈（匿名）
**技术栈**: {source} → {target}
**类别**: mapping-gap / discovery-blind-spot / convergence / safety

### 描述
{脱敏后的改进建议}

### 建议改动
{具体应修改的 knowledge 文件和内容}
```

### 生成过程

```
Step 1: 轻量分析 → bootstrap-profile.json
Step 2: 选择相关知识（节点模板 + 映射 + 领域）
Step 3: LLM 基于 profile + 知识 → 生成每个 node-spec
Step 4: 生成 state-machine.json（节点列表 + safety）
Step 5: 生成 .claude/commands/run.md（orchestrator 模板）
Step 5.5: 生成产物验收（自动 + 用户确认）
Step 6: 写入文件
```

无预置映射时（如 dart-kotlin），LLM 基于通用 translate.md 模板 + bootstrap-profile 自行推理生成。

### 生成产物验收（Step 5.5）

生成完成后、写入文件前，执行三层验收：

**Layer 1: 结构验证（自动，脚本执行）**
- 所有 node-spec 的 YAML frontmatter 可解析
- 必填字段存在（node, entry_requires, exit_requires）
- entry/exit_requires 语法合法（符合 check_requires.py 的四种原语格式）
- state-machine.json schema 合法（nodes 数组非空，safety 字段完整）

**Layer 2: 图连通性 + 构建 + 安全验证（自动）**
- 所有节点从初始节点可达（不存在孤岛节点）
- 至少一个终态节点存在
- bootstrap-profile 中的 build_commands 实际执行一次，验证退出码
- 失败的 build_command → 标记为验收问题，提示用户
- 扫描所有 node-spec 中的 `command_succeeds` 条目，检查危险命令模式（`rm -rf`, `sudo`, `chmod 777`, `> /dev/` 等）→ 匹配则标记为验收问题，阻止写入

**Layer 3: 摘要展示 + 用户确认（交互）**

向用户展示：
```
技术栈识别：{source_stacks} → {target_stacks}
业务域：{domain} — {business_context}
节点数：{count}（列出各节点名称）
关键映射抽查：（翻译映射表随机抽 4-5 条展示）
构建命令验证：{每条 build_command 的结果}
验收问题：{Layer 1-2 发现的问题，如有}

确认这些配置正确吗？如有问题请指出。
```

**用户回应处理：**
- 确认 → 进入 Step 6 写入文件
- 指出问题 → 修正对应的 node-spec 或 bootstrap-profile → 重新执行 Layer 1-2 → 再次展示
- 最多 3 轮修正，超出 → 建议用户手动编辑生成文件后执行 `/run`

## 7. 生成产物目录

```
{project}/
├── .claude/commands/
│   └── run.md                          # orchestrator 入口
└── .allforai/bootstrap/
    ├── bootstrap-profile.json          # 轻量分析结果
    ├── state-machine.json              # 节点 + safety + progress
    └── node-specs/                     # 每个节点的完整 subagent 指令
        ├── discovery-structure.md
        ├── discovery-runtime.md
        ├── product-analysis.md
        ├── generate-artifacts.md
        ├── plan-dag.md
        ├── translate-frontend.md
        ├── translate-backend.md
        ├── compile-verify.md
        ├── test-verify.md
        ├── visual-verify.md
        ├── tune-compliance.md
        └── ...
```

## 8. 仓库改造

### 新增

```
claude/meta-skill/              # 唯一新 plugin
├── .claude-plugin/
├── skills/bootstrap.md
├── commands/bootstrap.md
├── knowledge/                  # 从现有 6 个 skill 提炼
│   ├── nodes/*.md
│   ├── mappings/*.md
│   ├── domains/*.md
│   ├── safety.md
│   └── orchestrator-template.md
├── scripts/                    # 复用现有 Python 脚本
└── SKILL.md
```

### 改造

现有 6 个 skill 的核心知识提炼到 `knowledge/` 目录。去掉线性管线逻辑和条件分支，只保留节点级的通用协议。

| 来源 | 提炼到 |
|------|--------|
| code-replicate Phase 2 | knowledge/nodes/discovery.md |
| code-replicate Phase 3 | knowledge/nodes/generate-artifacts.md |
| code-replicate Phase 4 + cr-fidelity | knowledge/nodes/compile-verify.md, test-verify.md |
| cr-visual | knowledge/nodes/visual-verify.md |
| dev-forge design-to-spec + task-execute | knowledge/nodes/translate.md |
| code-tuner | knowledge/nodes/tune.md |
| product-design | knowledge/nodes/product-analysis.md |
| demo-forge | knowledge/nodes/demo-forge.md |
| stack-mappings.md | knowledge/mappings/ (按技术栈对拆分) |

### 不变

- `shared/scripts/` — Python 脚本全部保留
- `.allforai/` 产物格式 — 完全兼容
- 现有 skill 文件 — 保留作为知识来源参考

### 平台适配

| 平台 | meta-skill 形式 | 生成产物位置 |
|------|----------------|-------------|
| Claude Code | plugin | .claude/commands/ |
| Codex | AGENTS.md | 项目根目录 .md |
| OpenCode | skills.json | 项目根目录 .md |

三平台知识库相同，只是生成产物的格式和写入位置不同。

## 9. 全链路诊断协议

### 问题

下游节点失败时，根因往往不在相邻上游，而在链路最前端。例如：

```
demo-forge 调 POST /orders/create → 404
  → translate 没生成这个 API
    → generate-artifacts 没有这个 task
      → product-analysis 没识别这个功能
        → discovery 对订单模块扫描不充分
```

逐跳回溯（每次退一个节点）效率低，且每跳的扩展推理分散——可能每个节点各修一个 gap，但同类 gap 仍然散落在各处。

### 解决：诊断 Subagent

任何节点失败时，orchestrator 不立即回退，而是先派发一个**诊断 subagent**，一次性完成全链路分析。

**诊断 subagent 输入：**
- 失败节点 + 错误信息
- 所有已完成节点的产出摘要（从 state-machine.json 的 progress 读取）
- 所有 node-spec 的 exit_requires（用于判断哪个节点「该挡住但没挡住」）
- diagnosis_history（避免对同一根因重复诊断）

**诊断 subagent 任务：**

```
1. 根因定位
   从失败节点沿依赖链追溯，找到最上游的缺失点。
   不是逐跳试探——读所有相关节点的产出，一步到位。

2. 全链路影响分析
   这个根因影响了哪些中间节点的产出？列出完整的影响链。

3. 同类扩展
   以根因为模式，扫描所有节点产出找同类 gap。
   例：如果「创建订单」漏了，检查「取消订单」「退款」「修改订单」是否也漏了。
   再扩展：如果订单域有遗漏，支付域、物流域是否有类似盲区？

4. 修复计划
   从最上游到最下游，列出每个需要重跑的节点 + 具体修复动作 + 携带的 gap_list。

5. 预防规则
   是否需要修改某个 node-spec 的 exit_requires 或 hints，防止同类问题再发生？
```

**诊断 subagent 输出：**

```json
{
  "root_cause": {
    "node": "discovery-structure",
    "description": "对 server/handlers/ 目录扫描不充分，遗漏了订单相关 handler"
  },
  "impact_chain": ["discovery-structure", "product-analysis", "generate-artifacts", "translate", "test-verify"],
  "gaps_found": [
    { "domain": "订单", "missing": ["创建订单", "取消订单", "退款"], "severity": "high" },
    { "domain": "支付", "missing": ["支付回调处理"], "severity": "medium" }
  ],
  "repair_plan": [
    { "node": "discovery-structure", "action": "补充 server/handlers/ 全量扫描", "scope": "订单+支付模块" },
    { "node": "product-analysis", "action": "补充 4 个功能到 business-flows 和 task-inventory", "depends_on_previous": true },
    { "node": "generate-artifacts", "action": "补充 4 个 task + 对应 flows + use-cases", "depends_on_previous": true },
    { "node": "translate", "action": "生成 4 个 API + 对应 UI 页面", "depends_on_previous": true },
    { "node": "test-verify", "action": "补充 4 个功能的边界测试", "depends_on_previous": true }
  ],
  "prevention": [
    { "node_spec": "discovery-structure", "add_to_exit_requires": "所有 handler/controller 目录的文件覆盖率 >= 80%" },
    { "node_spec": "product-analysis", "add_to_hints": "对每个识别到的业务域，检查 CRUD 完整性" }
  ]
}
```

### 执行流程

```
节点失败
  ↓
orchestrator 派发诊断 subagent（不回退）
  ↓
诊断返回 repair_plan
  ↓
orchestrator 按 repair_plan 从最上游开始逐节点执行：
  每个节点携带完整 gaps_found 作为上下文
  每个节点完成后，下一个节点能利用上游的修复结果
  ↓
执行 prevention：Edit 对应 node-spec 文件
  ↓
repair_plan 全部完成 → 重新验证原始失败节点
  ↓
通过 → 继续正常流程
未通过 → 再次诊断（但 diagnosis_history 防止同因重诊）
```

### 收敛控制

- 同一根因最多诊断 2 次（第 3 次 → 标记 UNRESOLVED，输出当前最优结果 + TODO）
- repair_plan 的节点总数不超过 impact_chain 长度（不允许修复计划比影响链还长）
- 每次诊断后，**已识别的 gap 必须被解决**（允许发现新 gap，但旧 gap 不能复现）。如果同一批 gap 在两次修复后仍未解决 → 停止
- repair_plan 中某个步骤执行失败 → 触发新的诊断（携带更新后的上下文），嵌套诊断深度上限 1 层

### 诊断 subagent 输入边界

诊断 subagent 需要读所有节点产出摘要，但上下文不能无限膨胀：
- 每个节点的产出摘要由 orchestrator 在该节点完成时生成，≤500 字
- 诊断 subagent 输入总量 = 失败信息 + 节点摘要（最多 12 节点 × 500 字 = 6000 字）+ diagnosis_history
- 需要精确信息时，诊断 subagent 可通过 Read tool 读具体产物文件

### prevention 规则的生效范围

- prevention 修改的 exit_requires 仅对**未来执行**生效
- 已标记为 completed 的节点不追溯重验——如果 prevention 导致旧节点不达标，orchestrator 在下次经过该节点时自然会重新评估

### state-machine.json 扩展

progress 新增 `diagnosis_history`：

```json
{
  "progress": {
    "completed_nodes": [...],
    "iteration_count": 9,
    "diagnosis_history": [
      {
        "trigger": { "node": "demo-forge", "error": "POST /orders/create 404" },
        "root_cause": "discovery-structure 对订单模块扫描不充分",
        "gaps_found_count": 4,
        "repair_plan_executed": true,
        "resolved": true
      }
    ]
  }
}
```

## 10. Safety 实现细节

### entry_requires / exit_requires 评估

评估由一个小型 Python 脚本完成（`shared/scripts/orchestrator/check_requires.py`），不依赖 LLM：

```python
# 评估原语
file_exists(path)                    # os.path.exists
command_succeeds(cmd)                # subprocess exit code == 0
json_field_gte(file, json_path, value)  # 读 JSON 比较数值
json_array_length_gte(file, json_path, min_length)  # 数组长度检查
```

node-spec 的 entry/exit_requires 使用这些原语的声明式格式：

```yaml
exit_requires:
  - file_exists: .allforai/product-map/task-inventory.json
  - json_array_length_gte: [.allforai/product-map/task-inventory.json, "$", 1]
  - command_succeeds: "xcodebuild -scheme MyApp build 2>&1 | tail -1 | grep 'BUILD SUCCEEDED'"
```

### 循环检测

```
hash 输入 = node_id + exit_requires 的评估结果（每个条件 true/false）
滑动窗口 = 最近 10 次 iteration
warn_threshold = 3（同一 hash 出现 3 次 → 警告 LLM）
stop_threshold = 5（强制停止）
```

hash 不包含时间戳等易变数据，确保真正「卡在同一状态」时才触发。

### 进度单调性

```
progress = len(completed_nodes) / len(total_nodes)
total_nodes 在 bootstrap 时固定，prevention 规则修改 exit_requires 不改变节点数量
check_interval = 5（每 5 次 iteration 检查）
violation = progress 未增加 → 输出当前最优结果 + TODO 清单
```

### Subagent 超时

```
max_node_execution_time = 600 秒（10 分钟）
超时处理 = 视为 failure，进入诊断流程（Section 9）
orchestrator 通过 Bash tool 的 timeout 参数控制
```

### bootstrap-profile 版本化

bootstrap-profile.json 和 state-machine.json 均包含 `schema_version` 字段：

```json
{ "schema_version": "1.0", ... }
```

meta-skill 生成器升级后如果 schema 不兼容，读到旧版本 → 提示用户重新 `/bootstrap`。

### 并发冲突

并行节点必须写入不相交的文件集。生成器在生成 state-machine.json 时标记每个节点的 `output_files`，orchestrator 并行派发前检查无交集。

```json
{
  "id": "translate-frontend",
  "output_files": ["src/ios/**"],
  "parallel_safe_with": ["translate-backend"]
}
```

## 11. Python 脚本集成

`shared/scripts/code-replicate/` 的 13+ 脚本（cr_discover.py, cr_merge_*.py, cr_validate.py 等）在新架构中的角色：

| 脚本 | 被哪个 node-spec 调用 | 方式 |
|------|---------------------|------|
| cr_discover.py | discovery-structure | Bash tool: `python cr_discover.py --profile` |
| cr_merge_roles.py | generate-artifacts | Bash tool: `python cr_merge_roles.py` |
| cr_merge_tasks.py | generate-artifacts | 同上 |
| cr_merge_flows.py | generate-artifacts | 同上 |
| cr_merge_screens.py | generate-artifacts | 同上 |
| cr_merge_usecases.py | generate-artifacts | 同上 |
| cr_merge_constraints.py | generate-artifacts | 同上 |
| cr_gen_indexes.py | generate-artifacts | 同上 |
| cr_gen_product_map.py | generate-artifacts | 同上 |
| cr_gen_report.py | 任何节点完成后（可选） | 同上 |
| cr_validate.py | generate-artifacts 的自检 | 同上 |
| check_requires.py | orchestrator 每次循环 | Bash tool: `python check_requires.py node-id` |

脚本路径在 node-spec 中写死（生成时特化），不依赖 `${CLAUDE_PLUGIN_ROOT}`。

## 12. 用户迁移

### 命令映射

| 旧命令 | 新等价 |
|--------|--------|
| `/code-replicate` | `/run 逆向分析` |
| `/code-replicate` → `/design-to-spec` → `/task-execute` | `/run 复刻到 [目标技术栈]` |
| `/cr-fidelity` | `/run 还原度验证` |
| `/cr-visual` | `/run 视觉验收` |
| `/project-forge` | `/run 从零构建` |
| `/code-tuner` | `/run 代码治理` |
| `/product-design` | `/run 产品分析` |
| `/demo-forge` | `/run 演示数据` |
| `/deadhunt` | `/run 死链检测` |
| `/fieldcheck` | `/run 字段一致性` |

### 过渡期

1. meta-skill 发布后，现有 plugin 保持可用
2. 现有 plugin 的 SKILL.md 添加提示："推荐使用 /bootstrap + /run 替代本命令"
3. meta-skill 稳定运行 2 个版本周期后，废弃旧 plugin

## 13. 与 DeerFlow 的关键借鉴

| DeerFlow 模式 | 本设计的适配 |
|---|---|
| 无显式状态图，LLM 自主路由 | orchestrator 不预定义 transitions，LLM 看 state + error 决定 |
| 错误 → ToolMessage(status="error")，agent 继续 | subagent 失败信息作为 orchestrator 的决策上下文 |
| Loop Detection: hash + 滑动窗口 + warn/stop 阈值 | safety.loop_detection 机械执行 |
| Middleware 拦截层 | safety 规则作为 orchestrator 循环的机械检查层 |
| Command(goto=END) 中断 | 需要用户输入时保存 progress，中断等回应 |
| Subagent 并发限制 | max_concurrent_nodes 控制并行派发数 |

## 14. Subagent 响应契约

所有 node-spec subagent 返回统一格式，orchestrator 依赖此契约做决策：

```json
{
  "status": "success | failure | needs_input",
  "summary": "≤500 字，关键决策 + 发现 + 下游注意事项",
  "artifacts_created": ["file paths"],
  "errors": ["error descriptions, empty if success"],
  "user_prompt": "仅 needs_input 时，向用户展示的问题"
}
```

诊断 subagent 返回格式见 Section 9。

## 15. .allforai/ 兼容性

新架构的产出写入 `.allforai/bootstrap/`，与现有产物目录（`product-map/`, `experience-map/`, `use-case/` 等）无命名空间冲突。

generate-artifacts 节点产出的产物格式与现有完全相同（task-inventory.json, role-profiles.json 等），确保：
- 现有 Python 脚本（cr_merge_*.py, cr_validate.py）无需修改
- 下游 dev-forge 工具链（如果用户选择不走 meta-skill）仍可消费产物
- cr-fidelity / product-verify / testforge 等验证工具兼容
