# Codex Meta-Skill 思维测试结果

**测试日期**：2026-04-09  
**测试对象**：`codex/meta-skill`  
**测试方法**：场景化脑内执行（不跑真实 bootstrap，不生成真实 target project）  
**测试目标**：验证 Codex 适配层是否已经从“占位入口”升级为“可解释、可迁移、可闭环”的 meta-skill 运行面

---

## 结论

**当前结论：大体通过，但仍未做真实 bootstrap 运行验证。**

- **入口与契约层**：PASS
- **生成模板与运行契约层**：PASS
- **真实项目端到端运行层**：未验证

更准确地说：

> `codex/meta-skill` 已经达到 **adapter-contract usable**，并且 generated run 模板缺口已被补上；但还没有达到 **real bootstrap execution proven**。

也就是说，现在它已经不是空壳，也不是只能靠 `AGENTS.md` 自证兼容；但如果以“真实项目里 `/bootstrap` 后稳定生成并执行 Codex 原生 `run`”为标准，仍然存在高优先级风险。

---

## 测试场景

本轮按 5 个典型场景做脑内执行。

### 场景 1：Codex 发现并进入 meta-skill

检查点：

- `codex/meta-skill/SKILL.md` 存在
- `AGENTS.md` 不再是唯一入口说明
- `workflow.json` 被声明为主合同

结果：**PASS**

原因：

- 入口层文件已经补齐
- `SKILL.md`、`AGENTS.md`、`execution-playbook.md` 三处都已声明 `workflow.json`
- `.codex/commands/run.md` 作为生成目标路径已被显式写入

### 场景 2：空项目 / 新项目执行 bootstrap

脑内路径：

1. 用户在 Codex 下进入 `meta-skill`
2. 调用 `bootstrap`
3. 读取 `codex/meta-skill/commands/bootstrap.md`
4. 跳到 `codex/meta-skill/skills/bootstrap.md`
5. 再由适配层引用 Claude canonical bootstrap 协议
6. 生成 `.allforai/bootstrap/workflow.json`
7. 生成 `.codex/commands/run.md`

结果：**PARTIAL PASS**

通过点：

- 适配层已经明确要求把生成入口写到 `.codex/commands/run.md`
- 明确要求以 `workflow.json` 为主

风险点：

- Codex 版 `bootstrap.md` 目前还是“适配层说明”，不是完整重写的执行协议
- 真正的 canonical bootstrap 文档仍然包含 Claude 专有生成路径和命令说明
- 成功依赖执行者正确理解“引用 canonical 协议时要套用 Codex 替换规则”

结论：

- 对高能力 agent 来说可以工作
- 对严格协议执行来说仍不够机械化

### 场景 3：已有代码项目执行 setup

脑内路径：

1. 用户调用 `setup`
2. Codex wrapper 指向 Claude canonical setup
3. 适配规则说明如何替换 plugin root、如何解释 `AskUserQuestion`

结果：**PARTIAL PASS**

通过点：

- 已明确 `mcp-ai-gateway` 本地路径
- 已明确 Claude 专有 frontmatter 不应直接依赖
- 已明确 `AskUserQuestion` 在 Codex 中使用普通问答流

风险点：

- 目前仍是“说明如何适配”，不是一份完全 Codex-native 的 setup 协议正文
- Claude canonical setup 中包含大量具体 MCP 名称与 Claude 交互语义；Codex wrapper 只给了映射原则，没有逐段转译

结论：

- setup 的能力模型已迁移
- setup 的执行文本仍未完全 Codex 化

### 场景 4：对话中记录 journal，再执行 journal-merge

脑内路径：

1. 用户调用 `journal`
2. 适配层要求沿用 Claude canonical journal 协议
3. 用户再调用 `journal-merge`
4. 适配层要求保留冲突解决语义并输出 `concept-drift.json`
5. 完成后要求重新运行 `bootstrap`

结果：**PASS with caveat**

通过点：

- 输入文件、输出文件、schema 语义都没有漂
- `journal-merge` 后重新 bootstrap 的链路是清楚的

保留 caveat：

- 交互问题流仍依赖“Codex normal question flow”的解释，没有专门行为测试

### 场景 5：bootstrap 生成 run 并在目标项目执行

脑内路径：

1. bootstrap 生成 `.codex/commands/run.md`
2. 用户在目标项目中调用生成的 run
3. run 读取 `.allforai/bootstrap/workflow.json`
4. run 读取 node-specs 和 protocols
5. run 写 transition log 并可恢复执行

结果：**PASS at contract level / runtime not yet executed**

通过点：

- 现在已存在 Codex 本地模板：
  [`codex/meta-skill/knowledge/orchestrator-template.md`](/Users/aa/workspace/myskills/codex/meta-skill/knowledge/orchestrator-template.md)
- 模板目标路径已经是 `.codex/commands/run.md`
- 模板正文已以 Codex 命令描述为主，不再要求生成 `.claude/commands/run.md`

仍未完成的部分：

- 还没有在真实 target project 上跑一次 bootstrap，验证模板是否被正确写出并可被 Codex 执行
- 还没有真实运行 generated run entry

这就是当前最关键的未闭环点。

---

## 结果汇总

| 场景 | 状态 | 说明 |
|------|------|------|
| 入口发现 | PASS | `SKILL.md`、`workflow.json`、Codex run 路径已声明 |
| 新项目 bootstrap | PARTIAL PASS | 适配规则已存在，但 canonical bootstrap 仍是 Claude 文本 |
| setup | PARTIAL PASS | 能力映射已定义，完整 Codex 化正文仍缺 |
| journal / journal-merge | PASS with caveat | 语义链路清楚，但交互行为未机械验证 |
| 生成并执行 run | PASS at contract level | 已有真实 Codex-native orchestrator template，但缺少真实运行证据 |

---

## 主要发现

### Finding 1

**严重级别**：Medium

**问题**：缺少真实 target-project bootstrap -> generated run 执行证据。

证据：

- 已存在 Codex 本地 orchestrator template
- 但尚未在真实 target project 中验证 bootstrap 会正确生成并执行该 run entry

影响：

- 当前更多是“设计与静态合同已闭环”
- 不是“真实生成与执行已证实”

建议：

- 用最小 fixture 跑一次 bootstrap
- 验证 `.codex/commands/run.md` 被正确生成
- 再对生成后的 run 做一次最小执行 smoke

### Finding 2

**严重级别**：Medium

**问题**：`setup`、`journal`、`journal-merge` 仍主要是 wrapper，不是完整 Codex-native 协议正文。

影响：

- 能力定义已经迁移
- 但执行文本仍依赖 agent 理解“去读 canonical Claude 文本并套用 Codex 规则”

建议：

- 把 wrapper 升级为完整 Codex 命令正文
- 至少把所有 Claude 专有交互语义和路径说明直接内联到 Codex 版

### Finding 3

**严重级别**：Medium

**问题**：当前 parity 检查脚本只验证了入口层和 contract 层，没有验证 generated run 模板是否真实可产出。

影响：

- 会出现“静态检查全绿，但真实生成仍断”的假阳性

建议：

- 增加一条思维/fixture 级检查：
  - Codex bootstrap 是否能生成 `.codex/commands/run.md`
  - 生成内容是否不再依赖 Claude command frontmatter

### Finding 4

**严重级别**：Low

**问题**：共享资产目前通过软链接复用，source-of-truth 清晰，但对某些分发/打包环境可能脆弱。

影响：

- 在当前仓库本地开发环境中是优点
- 在未来如果做打包发布，可能需要改成生成式同步或显式复制

建议：

- 当前阶段保留软链接
- 如果后续进入发布态，再把共享资产同步方式收紧

---

## 当前判定

### 已达到

- `codex/meta-skill` 不再是占位目录
- 入口层、安装层、MCP 注册层、contract 层已经成形
- `workflow.json` 已经被 Codex 侧确认为主合同
- `.codex/commands/run.md` 已被确认为目标生成路径
- Codex 本地 orchestrator template 已存在

### 尚未达到

- 真实 bootstrap -> generate run -> execute run 的执行证据
- setup 的全量交互式能力验证
- journal / journal-merge 的真实冲突分支行为验证

---

## 最短下一步

1. 用最小 fixture 跑一次 bootstrap
2. 验证 `.codex/commands/run.md` 被正确生成
3. 对 generated run 做一次最小 smoke
4. 视结果再补 setup / journal 的行为级测试

---

## 最终判断

如果标准是：

- **“Codex 下已有真实 meta-skill 入口与适配层”**
  - 结论：**通过**

- **“Codex 下已经可以 100% 无歧义复现 Claude 的 bootstrap -> run 生成闭环”**
  - 结论：**静态合同层接近通过，运行证据层尚未通过**
