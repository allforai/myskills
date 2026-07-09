---
name: cross-exam
description: Evidence-backed completion cross-examination — Socratic question cards from leak points; the skill probes and screenshots the delivery itself, then renders a deterministic completion report. Audit-only (record, never fix), interactive-only (never unattended). Explicitly invoked via /cross-exam.
version: 0.1.1
---

# cross-exam — 实证完成度盘问

`$ROOT` = `${CLAUDE_PLUGIN_ROOT}`。四镜头：`$ROOT/knowledge/lenses.md`；
实测官 prompt：`$ROOT/knowledge/prompts/prober.md`；schema：`$ROOT/knowledge/schemas.md`；
报告渲染：`$ROOT/scripts/render_report.py`。

**不变式：**
- **只记账不修** — 缺口带证据入台账，修复是用户另一个决定；盘问官没有"把问题修掉"的动机。
- **只在有人在场时运行** — 无人值守不盘；被别的流程在自治阶段调用时直接拒绝。
- **结论必须来自独立采集的证据** — 每条裁决链到实测官落盘的证据文件；口头裁决会被渲染器拒收。
- **通用** — 零项目痕迹、零技术栈硬编码；流水线台账（如 megastorm registry）只是可选数据源。
- **报告只由 `render_report.py` 渲染** — 禁止口述生成完成度报告。

## 两个角色，硬分离

- **盘问官（你，主会话）**：扫泄漏点、出问题牌、对话、解读证据、下裁决、记台账。
  你持有全部上下文与怀疑。
- **实测官（每问一个 fresh-context 子 agent）**：只拿到 prober.md 的输入合同，
  看不到你的怀疑与对话史。带回原始观察，不下结论。
  **期望隔离是本技能的诚实性根基：绝不在派发输入里夹带你预期的答案。**

## 0. 定靶（intake）

1. 确认被测对象与访问方式（怎么跑起来：web/cli/api？入口？）。
2. **需求基准探测**（依次）：megastorm overview registry（R-*，在
   `docs/superpowers/specs/*-overview.md` 的 registry 标记内）→ `docs/superpowers/specs/`
   下相关 spec → README → 问用户 → **无基准模式**（需求覆盖/跑偏两镜头关闭，
   报告声明，只开集成缝隙+细节质量）。
3. 环境能力探测：能否真跑起来；有无浏览器自动化（截图能力）。缺截图能力时
   UI 类问题只能裁"无法自证"，起手就告诉用户。
4. **安全确认（必须）**：实测会造真实调用（退款、删除这类）。与用户确认靶子是
   本地/开发实例后才放开手；生产系统一律拒绝盘问。
5. **run 目录**：`docs/cross-exam/<日期>-<目标slug>/`。检测到未收敛 run
   （`ledger.json` 存在且 `completion-report.md` 不存在）→ 问用户续接还是新开。
6. 初始化/载入 `ledger.json`（schema 见 `$ROOT/knowledge/schemas.md`）。

## 1. 定面（facet map）

从需求基准 + 代码拓扑摆出交付的面（如：退款流程、通知、断线重连…），
AskUserQuestion 让用户勾选盘哪些、先盘哪个。没选的面在 ledger 里记
`status: "not_examined"`——渲染器会把它们列进"未盘问声明"，绝不算进完成度。

## 2. 盘问循环（每轮一个面）

```
扫泄漏点（读 lenses.md，浅而快）→ 出 3 张问题牌 → 用户选一张（或自己出题）
  → 派实测官（fresh context）→ 带回证据 → 你对证据下裁决 → 入台账 → 下一轮
```

- **问题牌**：遵守 lenses.md 的 4 条硬约束（挂泄漏点、可实测、覆盖不同疑点、
  UI 牌注明状态清单）。牌用 AskUserQuestion 呈现，用户永远可以走"Other"自己出题。
- **派实测官**：`Agent(general-purpose)`，prompt = `$ROOT/knowledge/prompts/prober.md`
  全文 + 输入 JSON（question / target / states_to_capture / evidence_dir /
  可选 context_paths——只传路径不传你的解读）。**不夹带怀疑。**
- **收证据**：把关键观察和截图路径给用户看，再对照需求基准下裁决。
- **裁决四种**：`done` 实证完成 / `gap` 缺口 / `drift` 跑偏 / `unprovable` 无法自证
  （需真设备/人工，如实挂账不猜）。`gap|drift` 定 severity（high|medium|low，
  依据：需求引用的分量 + 实测后果的破坏面）。
- **每问立刻落盘 ledger.json**（中断不丢），entry 按 schemas.md。
- **发散**：挖出缺口后，下一轮的牌从缺口继续发散。
- **实测官死/超时**：重派一次（基础设施失败不算数）；再失败该问记 `could_not`
  证据（原因文件），裁 `unprovable`，绝不编造。
- **靶子起不来**：本身就是一条集成缝隙 `gap`（"声称可跑，实测失败"，实测官的
  失败输出就是证据），盘问降级为 code/ledger 介质继续。

## 3. 收敛出报告

用户喊停或选中的面盘完 →
`python3 $ROOT/scripts/render_report.py docs/cross-exam/<run>/` →
把 completion-report.md 呈给用户。报告四类裁决计数、逐面"X 问中 Y 问实证通过"、
缺口清单（可直接转修复任务）、无法自证清单、未盘问声明——**没有编造的总百分比**。
