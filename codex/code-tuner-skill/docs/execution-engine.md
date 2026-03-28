# Execution Engine Protocol

> 本文件定义所有 skill 通用的执行引擎协议。主流程（调度器）和 subagent（执行者）都必须遵守。

## 1. 主流程角色：纯调度器

主流程**不执行任何业务逻辑**。职责仅有三项：

1. **读状态**：当前阶段、上一个 subagent 返回结果
2. **决策路由**：正常 → 下一阶段；UPSTREAM_DEFECT → 回退到目标阶段
3. **Dispatch subagent**：按任务模板组装 prompt → Agent tool 发出

### 主流程 context 只包含

- 本 skill 的 phase 声明（SKILL.md 中的 YAML）
- 当前进度（哪些阶段已完成、当前在哪）
- 最近阶段的摘要（≤500 字/阶段）
- 累积的 UPSTREAM_DEFECT 记录（如有）

### 不在主流程 context 里

- 铁律/规则全文 → subagent 自己 Read
- 源代码 → subagent 自己 Read
- 中间产物详情 → 写入 .allforai/，subagent 自己 Read

## 2. Subagent 任务模板

每个 subagent 被 dispatch 时，主流程用以下模板组装 prompt：

```
## 任务
{phase.id}：{phase.subagent_task}

## 输入
- 读取以下产物文件：{phase.input 列表，每行一个路径}
- 上游摘要：{主流程选择性注入的前序阶段摘要，仅注入与当前阶段相关的}
{仅回退时}
- 修复上下文：{UPSTREAM_DEFECT 信号全文，含 evidence 和 suggested_fix}

## 规则
读取以下规则文件后执行（按顺序读取，全部读完再开始执行）：
{phase.rules 列表，每行一个路径}

## 输出要求
1. 产物文件：写入 {phase.output}
2. 阶段摘要：任务完成后返回 ≤500 字摘要，包含：
   - 关键决策（做了什么、为什么这么做）
   - 发现的异常/风险
   - 下游需要注意的事项
3. 缺陷信号：若发现上游产物有问题（缺失、矛盾、不完整），按以下格式返回：
   {"signal":"UPSTREAM_DEFECT","source_phase":"当前阶段","target_phase":"应该修的阶段","defect_type":"LLM自行描述","evidence":"具体证据","severity":"blocker|warning","suggested_fix":"建议修复方向"}
   无上游问题则不返回此字段。
```

## 3. 信息共享机制

### 3.1 产物文件（主通道）

每个阶段的 subagent 将产出写入 `.allforai/` 目录。下游 subagent 通过 Read 工具按需读取。

### 3.2 阶段摘要（辅助通道）

每个 subagent 完成时返回 ≤500 字摘要。主流程判断哪些摘要与下一阶段相关，选择性注入。

**选择性注入原则**：
- 直接前置阶段的摘要：默认注入
- 非直接前置阶段：仅当其摘要中提到与当前阶段相关的风险/注意事项时注入
- 摘要总量控制：注入给单个 subagent 的摘要总计不超过 1500 字

## 4. 下游回退协议

### 4.1 回退决策

```
severity = blocker → 立即暂停当前阶段，dispatch 目标阶段 subagent 修复
severity = warning → 记录，继续当前阶段，当前阶段完成后再 dispatch 修复
```

### 4.2 回退执行

1. 主流程解析 target_phase → 找到对应阶段声明
2. Dispatch 修复 subagent：注入 UPSTREAM_DEFECT 信号作为修复任务（不重跑整个阶段）
3. 修复 subagent 更新产物文件 → 返回修复摘要
4. 主流程把修复摘要注入当前阶段 subagent → 从断点继续

### 4.3 防无限回退

- 同一 {source_phase, target_phase} 对最多回退 2 次
- 第 3 次 → 标记 UNRESOLVED_DEFECT，继续执行，最终报告标红
- 此约束协议级，与具体 skill 无关

### 4.4 跨 skill 回退

协议不区分 skill 内和跨 skill。target_phase 格式为 `{skill}.{phase}`（如 `product-design.use-case`）。主流程加载目标 skill 的阶段声明，dispatch 修复 subagent。

### 4.5 质量门禁阶段

部分阶段是质量门禁（quality gate）——其产出包含 pass/fail 判定。门禁阶段在 phase 声明中标记 `gate: true`。

门禁阶段的 subagent 返回时，除标准摘要外还必须包含：
- `gate_result: pass | fail | partial`
- `failed_items: [<未通过项的描述>]`（仅 fail/partial 时）

主流程收到门禁结果后的决策：
- `pass` → 正常进入下一阶段
- `fail` → 视为 UPSTREAM_DEFECT（severity: blocker），target_phase 为门禁的直接前置阶段，自动回退修复
- `partial` → 将 failed_items 作为 warning 级 UPSTREAM_DEFECT 记录，继续执行下游阶段，下游阶段可选择性跳过未通过项

门禁阶段不消耗 UPSTREAM_DEFECT 的 2 次回退配额——门禁回退是正常质量闭环，不是异常。

## 5. Phase 声明格式

每个 skill 在 SKILL.md 中用 YAML 声明阶段结构：

```yaml
phases:
  - id: <阶段ID>
    subagent_task: "<一句话任务描述>"
    input: [<产物文件路径>]
    output: "<输出路径>"
    rules: ["${CLAUDE_PLUGIN_ROOT}/<规则文件路径>"]
    depends_on: [<前置阶段ID>]
```

- depends_on 为空的阶段可并行 dispatch
- 主流程（LLM）直接理解 YAML，无需 parser

## 6. 讨论前置原则（Discussion-First）

**所有用户交互必须在执行开始前完成。** 执行阶段是纯 subagent 执行，零交互。

### 6.1 两阶段模型

```
讨论阶段：主流程与用户对话 → 所有决策落盘到 .allforai/
执行阶段：纯 subagent dispatch → 读落盘文件 → 执行 → 产出
```

### 6.2 讨论阶段的职责

在 dispatch 任何 subagent 之前，主流程必须：
1. 读取所有标记 `preflight: true` 的阶段的 rules 文件
2. 从 rules 中提取需要用户决策的问题清单
3. 逐个与用户讨论，直到所有问题解决
4. 将所有决策写入对应阶段的 output 文件（如 replicate-config.json、project-manifest.json）
5. 用户确认"开始执行"后，进入执行阶段

### 6.3 Phase 声明标记

需要预讨论的阶段标记 `preflight: true`：

```yaml
  - id: preflight
    preflight: true  # 讨论阶段处理，不进入执行调度
    subagent_task: "..."
```

主流程在执行阶段遇到 `preflight: true` 的阶段时直接跳过（已在讨论阶段完成）。

### 6.4 执行阶段禁止交互

执行阶段的 subagent **禁止**使用 AskUserQuestion 或任何用户交互工具。如果 subagent 发现缺少决策信息：
- 信息在上游产物文件中 → 读取
- 信息确实缺失 → 返回 UPSTREAM_DEFECT（target: 该 preflight 阶段），主流程暂停执行，回到讨论模式补充决策，然后恢复执行

## 7. 跨 skill 路由

当 UPSTREAM_DEFECT 的 target_phase 指向其他 skill 时（格式：`{skill}.{phase}`），主流程需要定位目标 skill 的阶段声明。

### 7.1 路由策略

主流程按以下优先级尝试定位：
1. 当前项目的 `.allforai/skill-registry.json`（如存在）
2. 用 Glob 工具搜索 `**/SKILL.md` 查找包含目标 phase 声明的文件
3. 以上均失败 → 将 UPSTREAM_DEFECT 降级为 `UNRESOLVED_DEFECT`，记录到最终报告，提示用户手动执行目标 skill 的修复

### 7.2 skill-registry.json 格式

```json
{
  "product-design": {"skill_md": "/path/to/product-design-skill/SKILL.md"},
  "dev-forge": {"skill_md": "/path/to/dev-forge-skill/SKILL.md"},
  "demo-forge": {"skill_md": "/path/to/demo-forge-skill/SKILL.md"}
}
```

此文件由各 skill 的 install 脚本或首次执行时自动生成。不存在时降级到策略 2。
