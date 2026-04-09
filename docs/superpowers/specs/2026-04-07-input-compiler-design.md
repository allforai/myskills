# Input Compiler 设计

> 为 meta-skill 的 node-spec 增加结构化上下文拉取能力，解决 subagent 接收噪音上下文的问题。

## 问题

当前 orchestrator 派发 subagent 时，subagent 只读 node-spec 文件。node-spec 里包含执行指令，但没有说明如何从上游节点产物中提取相关上下文。结果是 subagent 要么自行决定读什么文件（不稳定），要么只靠 node-spec 里写死的信息（信息不足）。

## 架构契约变更

现有架构承诺："每个 node-spec 包含执行所需的全部上下文，subagent 不需要读别的文件。"

**本设计更新该契约为**：

> node-spec 包含三类内容：任务指令、Context Pull 规则、以及必需的静态上下文。
> subagent 在执行前按 Context Pull 规则主动拉取上游产物，这是 node-spec 执行的一部分，不是例外。

总架构文档（`docs/superpowers/specs/2026-03-29-meta-skill-architecture-design.md` Section 5）需同步更新该表述。

## 设计决策

| 决策 | 选择 | 原因 |
|------|------|------|
| 推模式 vs 拉模式 | 拉模式 | subagent 自己按规则拉取，orchestrator 不介入，职责清晰 |
| 规则来源 | capabilities/*.md 定义可拉字段 + bootstrap LLM 决定拉哪些 | 特化阶段有结构约束，运行时有项目适配 |
| 规则格式 | 自然语言指令 | 与现有 node-spec 格式一致，LLM 可直接执行 |
| 失败处理 | required 缺失报错，optional 缺失记 warning 继续 | 避免低价值缺失阻塞整体吞吐 |

## 方案

### 核心模式：Context Pull 段落

每个 bootstrap 生成的 node-spec 新增一个 **Context Pull** 段落，位于执行指令之前。

格式：

```markdown
## Context Pull

在开始执行前，从以下上游产物读取上下文：

**必需（缺失则报错返回）：**
- 从 `.allforai/bootstrap/source-summary.json` 读取 `tech_stacks` 字段，
  用于了解当前项目的技术栈，作为翻译策略选择的依据。

**可选（缺失则记录 warning 后继续）：**
- 从 `.allforai/bootstrap/reuse-assessment.json` 读取 `per_component` 字段，
  用于了解每个组件的复用评估结果，决定哪些组件需要重写而非直接翻译。
  缺失时按默认策略（全部翻译）继续。
```

### Capability 字段模型

capabilities/*.md 的 `Required Outputs` 表扩展为以下结构，能够表达每个字段对下游的消费关系：

```markdown
| Artifact | Field Path | Consumer Capability | Required | Reason |
|----------|------------|---------------------|----------|--------|
| `source-summary.json` | `tech_stacks` | translate, compile-verify | required | 翻译策略和编译命令都依赖技术栈信息 |
| `source-summary.json` | `architecture_pattern` | product-analysis | optional | 有助于识别模式但不影响核心分析 |
| `reuse-assessment.json` | `per_component` | translate | optional | 缺失时按全量翻译降级 |
```

字段说明：
- **Artifact**：产物文件路径（相对于 `.allforai/bootstrap/`）
- **Field Path**：JSON 字段路径（支持嵌套，如 `modules[].role`）
- **Consumer Capability**：哪些 capability 的节点需要消费这个字段
- **Required**：required = 缺失阻塞执行；optional = 缺失降级继续
- **Reason**：为什么这个字段对该 consumer 重要

### Node → Capability 绑定规则

bootstrap 生成 node-spec 时，必须能确定性地找到产物文件路径。绑定规则：

1. **每个 capability 的产物文件名由 capability 固定定义**，不由 node 自定义。
   例如：discovery capability 固定产出 `source-summary.json`，不管项目叫什么。

2. **workflow.json 记录每个 node 对应的 capability**：

   ```json
   {
     "nodes": [
       {
         "id": "discovery-structure",
         "capability": "discovery",
         "exit_artifacts": ["source-summary.json", "file-catalog.json"]
       }
     ]
   }
   ```

3. **bootstrap 生成 Context Pull 的逻辑**：
   - 找当前 node 的上游 node（通过 workflow.json 依赖关系）
   - 读上游 node 的 `capability` 字段，找到对应 `capabilities/*.md`
   - 从该 capability 的字段模型表中，过滤 `consumer_capability` 匹配当前节点的行
   - 根据 `bootstrap-profile.json` 做项目相关性裁剪（LLM 判断）
   - 生成 Context Pull 自然语言指令，按 required/optional 分组

### 失败策略（两级）

| 级别 | 条件 | 行为 |
|------|------|------|
| 报错返回 | required 字段对应文件不存在 | subagent 返回错误，说明缺少哪个文件，orchestrator 触发诊断流程 |
| Warning 继续 | optional 字段对应文件不存在 | subagent 记录"缺少 X，使用降级策略"，继续执行 |

### 改动范围

**1. `capabilities/*.md`（每个 capability 文件）**

将现有 `Required Outputs` 表替换为上述字段模型表（Artifact / Field Path / Consumer Capability / Required / Reason）。

**2. `skills/bootstrap.md`**

在生成 node-spec 的步骤里加入 Context Pull 生成指令，引用 Node → Capability 绑定规则。

**3. `knowledge/orchestrator-template.md`**

不需要改动。orchestrator 的派发逻辑不变，失败处理复用现有诊断流程。

**4. `docs/superpowers/specs/2026-03-29-meta-skill-architecture-design.md`**

更新 Section 5 的 node-spec 契约表述（见"架构契约变更"一节）。

## 验收标准

**结构验证：**
- 生成的 node-spec 包含 Context Pull 段落，且 required/optional 分组清晰
- Context Pull 引用的文件名与对应 capability 的固定产物名一致
- 字段选择与项目类型相关（不同项目生成不同的 Context Pull）

**行为验证：**
- subagent 执行前预检：required 文件存在 → 继续；required 文件缺失 → 报错返回
- optional 文件缺失时 subagent 输出 warning 并继续，不触发 orchestrator 诊断
- orchestrator 收到 required 缺失报错后，触发诊断流程

## 非目标

- 不改变 orchestrator 的派发逻辑
- 不引入新的编译步骤或中间文件
- 不做字段内容校验（只做文件存在性预检）
- 不在本次处理"输入相关性"的效果验证（留后续迭代）
