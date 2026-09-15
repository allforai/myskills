---
name: cross-exam
description: >
  Evidence-backed completion audit of a delivery, including user-declared journeys;
  records, never fixes. User-invoked only via /skill:cross-exam; never invoke it
  yourself. Requires independent fresh-context subagents; refuse rather than self-audit.
---

# cross-exam — Pi Adapter

用户显式调用 `/skill:cross-exam [target]` 才运行。空参数进入定靶。模型不得自行启动。
这是完成度盘问，不是 keep-code-simple，也不是 product-review。不要读或执行 `product-review.md`。

**只记账不修。只在有人在场时运行。无人值守或被自治流程调用时直接拒绝。**

## 0. 能力前置门（先于一切，硬拒绝）

cross-exam 的诚实性建立在「每问一个 fresh-context 实测官独立取证」上。
Pi 能发现 skill **不等于**有子代理。只使用当前已加载的能力，**不自动安装扩展**，不启动另一 harness。

1. 没有 `subagent` 工具 → 当场停。
2. 有则先 `subagent({action:"list", capabilities:true})`。只认 executable、非 disabled 的代理。
   外部 CLI 还须 `runner.available === true`（预检，不是已登录证明）。runner 必须能跑本次取证
   （读项目、写证据目录、按需起服务/用浏览器），且支持 `context:"fresh"` 或等价的不继承盘问官对话。
3. 派不出独立 fresh-context 子代理 → 告诉用户：
   「这里跑不了 cross-exam：它必须靠独立实测官取证，本环境没有可用子代理；请安装并加载 pi-subagents 或换环境。我不会降级成自审，也不会自动装扩展。」
   然后结束。不要定靶、不要摆面、不要用主会话冒充实测官。

结构化提问有没有选择器**不是**前置门。缺了就用纯文本问。

## Canonical Source

包根目录是本文件上两级（含 `package.json` 的 `pi/cross-exam/`）。按顺序解析 `$ROOT`：

1. `<package-root>/../../codex/cross-exam-skill/`（myskills 源码布局）
2. `<package-root>/canonical/`（可选独立快照）

两者都不存在则停止，说明需要从 myskills 源码安装或放入 `canonical/`。不要猜路径。

`$ROOT` 是协议资源根，不是被测项目 cwd。镜头、prompt、schema、脚本、visual、engine 都从 `$ROOT` 读：

- `$ROOT/lenses.md`
- `$ROOT/prompts/{prober,census,sites,sweep}.md`
- `$ROOT/schemas.md`
- `$ROOT/scripts/ledger_store.py`（有则用来加锁写 ledger）
- `$ROOT/scripts/render_report.py`
- `$ROOT/visual/visual-acceptance.md`（用户选了视觉 facet 之后）

读完 `$ROOT/SKILL.md` 从 `# cross-exam — 实证完成度盘问` 起的全文（跳过文件开头的 package router），执行该协议，并只应用下列 Pi 替换。不要继续 router 里的 product-review / keep-code-simple 分支。

## Required Pi Substitutions

### 1. 派发

主会话是盘问官：出牌、对话、解读证据、裁决、写 ledger、跑 `render_report.py`。
实测官 / 普查官 / 枚举官 / 扫全实测官 / 视觉 reviewer / 复核官都是 **fresh-context 子代理**。
期望隔离：派发输入只含协议规定的 prompt 全文 + 输入 JSON；**不夹带怀疑、预期答案、oracle、waypoints**。

每当 canonical 写 `spawn_agent` / `wait_agent` / `Agent(...)` / `fork_turns:"none"`：

- 用 **一个顶层** `subagent` 调用，`workflowScript`、`async:true`、明确 `cwd`（被测项目）、`context:"fresh"`。
- 普查官、复核官、视觉 reviewer：一次一个 `runs.run`。
- 互不依赖的实测官（扫全扇出、并行旅程）用同一工作流里的 `runs.all`。`runs.all` 返回有序数组。
- **不要用 git worktree 隔离实测官。** 他们必须打同一棵被测树、同一本地/开发实例。隔离的是对话上下文，不是工作区。同一模拟器/设备一次只由一个实测官操作。
- 子代理只许写派发给它的 `evidence_dir`（及该问约定的截图/视觉批次目录）。禁止改产品源码，禁止写 `ledger.json` 或 `completion-report.md`。
- 原生 Pi 子代理可在支持的 `model` 参数上按 `model_policy` 传档位；缺省不传，继承会话模型。外部 runner 不默认支持 native model/context/toolBudget；不传未经确认支持的参数。
- 异步运行已有原生完成通知：继续独立的盘问官工作或归还控制，通知到达再合并。不轮询、不 sleep、不仅为了等待调用 `bg_wait`。
- 派发开始后的基础设施失败：停止该路径，记录精确错误和 run/cwd/ref/工作区状态。只能按协议重派一次实测官。不切到 CLI、`pi -ne`、前台自审或其他执行模式。
- `agent_task` 记 Pi 子代理的 run/child id（或宿主给出的 session/output 引用），不是 `spawn_agent` id。

### 2. 模型

技能不写死模型字面量。定靶 0b 读**当前**可派模型列表（`subagent` list / 当前会话模型），推荐规则与 canonical 相同。
派发时读 ledger `model_policy`，不读记忆。普查官、视觉 reviewer、复核官从不降档。

### 3. 提问

Pi 没有 `AskUserQuestion`。牌、定面勾选、旅程确认、扫全模板过目、安全确认一律纯文本。
一次问一件阻塞的事。不要发明答案。

### 4. 台账与报告

新 run 写 `ledger_version: 2`。有 `ledger_store.py` 就用它加锁写；没有则直接写 `docs/cross-exam/<日期>-<目标slug>/ledger.json`，仍须每问立刻落盘。
报告只由 `python3 $ROOT/scripts/render_report.py docs/cross-exam/<run>/` 渲染。禁止口述生成完成度报告。

### 5. 后续用户步骤

报告呈完后可以提：产品层面用 Claude/Codex 的 `/product-review`（Pi 尚未移植）。不要在本技能里启动它。
keep-code-simple 是本包另一个入口，与完成度盘问分开调用。
