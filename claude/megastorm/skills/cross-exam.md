---
name: cross-exam
description: Evidence-backed completion cross-examination — Socratic question cards from leak points; the skill probes and screenshots the delivery itself, then renders a deterministic completion report. Audit-only (record, never fix), interactive-only (never unattended). Explicitly invoked via /cross-exam. Generic — works on any delivery, not only megastorm runs.
---

# cross-exam — 实证完成度盘问

`$ROOT` = `${CLAUDE_PLUGIN_ROOT}`。四镜头：`$ROOT/knowledge/cross-exam/lenses.md`；
实测官 prompt：`$ROOT/knowledge/cross-exam/prompts/prober.md`；
schema：`$ROOT/knowledge/cross-exam/schemas.md`；报告渲染：`$ROOT/scripts/render_report.py`。

**不变式：**
- **只记账不修** — 缺口带证据入台账，修复是用户另一个决定；盘问官没有"把问题修掉"的动机。
- **只在有人在场时运行** — 无人值守不盘；被别的流程在自治阶段调用时直接拒绝。
- **结论必须来自独立采集的证据** — 每条裁决链到实测官落盘的证据文件；口头裁决会被渲染器拒收。
- **实测官独立不可降级——缺了就拒跑，绝不自审。** cross-exam 的诚实性完全建立在"每问一个
  fresh-context 实测官独立取证"上。若本 harness 派不出独立子 agent（如 Codex 未开 `multi_agent`，
  或任何无并发子 agent 的环境），**当场停，明说"这里跑不了 cross-exam"，绝不降级成"盘问官自己
  检查自己的交付"**。自审恰恰是 cross-exam 存在要抓的那种假完成——一个没有独立实测官的 cross-exam，
  看起来盘过了、实际什么都没验，是最坏的假成功。**宁可说跑不了，不可假装盘过。**
- **通用** — 零项目痕迹、零技术栈硬编码；流水线台账（如 megastorm registry）只是可选数据源。
- **报告只由 `render_report.py` 渲染** — 禁止口述生成完成度报告。

## 两个角色，硬分离

- **盘问官（你，主会话）**：扫泄漏点、出问题牌、对话、解读证据、下裁决、记台账。
  你持有全部上下文与怀疑。
- **实测官（每问一个 fresh-context 子 agent）**：只拿到 prober.md 的输入合同，
  看不到你的怀疑与对话史。带回原始观察，不下结论。
  **期望隔离是本技能的诚实性根基：绝不在派发输入里夹带你预期的答案。**

## 0. 定靶（intake）

0. **能力前置门（先于一切，硬拒绝）：** 确认本 harness 能派出**独立的 fresh-context 子 agent**
   （Claude Code: `Agent`；Codex: `spawn_agent`/`wait_agent`，需 `~/.codex/config.toml` 开
   `[features] multi_agent = true`）。**派不出 → 当场停，告诉用户"这里跑不了 cross-exam：它必须靠
   独立实测官取证，本环境没有；请开多智能体或换环境，我不会降级成自审"，然后结束。** 不要继续定靶、
   不要摆面、不要用主会话冒充实测官。（`AskUserQuestion` 有没有结构化选择器**不是**前置门——那只是
   问法，退成纯文本问答不影响方法；能力门只卡"独立取证"这一件事。）
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
   （`ledger.json` 存在且 `completion-report.md` 不存在）→ 问用户续接还是新开；
   续接时读旧 ledger 的 `open_threads` 作为起手牌候选。
6. 初始化/载入 `ledger.json`（schema 见 `$ROOT/knowledge/cross-exam/schemas.md`）。

## 1. 定面（facet map）

**先独立 census 播种，再由你摆面——别让"你想到要盘什么"成为覆盖上限。** facet 表最危险的
盲区是"你根本没想到要盘的那块"：盘问官持怀疑但也带盲区，只凭 hunch + 读代码摆面，交付里整类
问题会因"没进 facet 表"而永远盘不到（实战教训：一整族假成功操作，只因盘问官碰巧把其中一个做成
了牌才被抓出，那类本身从没有独立 facet）。所以定面分两步：
1. **独立 surface 枚举**：派一个 fresh-context agent，用覆盖法（不是 hunch）从代码拓扑穷举交付
   的操作面——每个用户可触发操作 / 每个端点 / 每个 store 方法 / 每个契约（RPC/handler）。它不看
   你的怀疑，只产出"这交付一共有哪些面 + 每个面的入口"。死端点/契约 census（见 lenses.md 新增
   镜头）是最省的播种法。
2. **合并 + 摆面**：把 census 面与你自己想到的面合并去重，**标出"census 有、你没想到"的面**（那
   往往正是盲区）。然后 AskUserQuestion 让用户勾选盘哪些、先盘哪个。

没选的面在 ledger 里记 `status: "not_examined"`，**并按风险排序**（需求引用的分量 + 若真坏的破坏
面），让人清楚把什么留在了桌上——渲染器把它们列进"未盘问声明"，绝不算进完成度。

## 2. 盘问循环（每轮一个面）

```
扫泄漏点（读 lenses.md，浅而快）→ 出 3 张问题牌 → 用户选一张（或自己出题）
  → 派实测官（fresh context）→ 带回证据 → 你对证据下裁决 → 入台账 → 下一轮
```

**两种模式，按目标选。** 上面的循环是**深挖模式**（Socratic 牌）：逐面出牌、用户选、单实测官
深证——答"这条线成不成立"。当目标是"消灭某一类 / 交付完整性"时，先切**扫全模式（census
sweep）**：并行扇出覆盖式实测官把整个 surface 扫一遍（每个操作/端点逐条查"契约是否兑现"），拿
到全集后再对高风险线回到深挖。**深挖答不了"我们有没有到处都看过"——那是扫全模式的活；只做深挖
等于用 3 张牌去覆盖一整个交付。** 深挖中途抓到"一类的实例"时也会升级——见下面"孤例还是一类"。

- **问题牌**：遵守 lenses.md 的 4 条硬约束（挂泄漏点、可实测、覆盖不同疑点、
  UI 牌注明状态清单）。牌用 AskUserQuestion 呈现，用户永远可以走"Other"自己出题。
- **派实测官**：`Agent(general-purpose)`，prompt = `$ROOT/knowledge/cross-exam/prompts/prober.md`
  全文 + 输入 JSON（question / target / states_to_capture / evidence_dir /
  可选 context_paths——只传路径不传你的解读）。**不夹带怀疑。**
- **收证据**：把关键观察和截图路径给用户看，再对照需求基准下裁决。
- **裁决四种**：`done` 实证完成 / `gap` 缺口 / `drift` 跑偏 / `unprovable` 无法自证
  （需真设备/人工，如实挂账不猜）。`gap|drift` 定 severity（high|medium|low，
  依据：需求引用的分量 + 实测后果的破坏面）。
- **自审 bias-guard（盘问官==交付作者时必开）**：取证独立 ≠ 裁决独立。作者给自己的活定 severity
  有往轻里判的动机。此时 `gap` 默认从严——把 gap 降成 low 或判 done，需要**额外独立证据**（另一
  个 fresh agent 复核，或明确的"生产不可达"实证），不能只凭盘问官一句"影响不大"。
- **每问立刻落盘 ledger.json**（中断不丢），entry 按 schemas.md。
- **弃牌不蒸发**：每轮发牌后，未被选中的牌**立即**记入 ledger 的 `open_threads`
  （q/facet/leak_point）；某线后来被实测则移入 entries 并从 open_threads 删除。
  报告会把它们渲染成"未拉的线"，续盘从这里接手。
- **孤例还是一类（每条 `gap|drift` 落账时必答）**：这个缺口是这一处独有，还是某个结构模式的
  实例（一个契约类缺同一种防护/接线）？判"一类"则**当即两个动作**，不等用户表态：
  ① `ledger.patterns` 建 pattern（`hypothesis` 一句话缺陷模式，schema 见 schemas.md）；
  ② 派**同类位点枚举官**（fresh-context，只枚举不取证，成本一问一 agent）：给它结构模式的
  中立描述（"列出所有具有 X 结构的位点及入口，逐个报告其 Y 契约现状"），**绝不夹带首例的
  裁决**（"我们发现 A 坏了，看看别的坏没坏"就是把期望塞给它）——期望隔离在横向扫描时最容易破。
  枚举回来的位点全部进 pattern 的 `sites`，然后向用户提议：对该类切 mini-census 扫掉，或逐点
  出牌，或先放着。**用户不接也已落账**——渲染器会把未查位点逐个点名，同类嫌疑不许蒸发，也不许
  塞进 open_threads（那是牌的槽位，装不下横跨多面的类假设）。类怀疑的去处只有 patterns。
- **发散（纵横两个方向）**：挖出缺口后，下一轮的牌从缺口**纵向**发散（顺同一条线追后果，
  open_threads 里的旧牌也是候选）；**横向**发散不出牌——走上面"孤例还是一类"的 patterns 路径，
  按名册清点，别靠下一轮碰巧想到。
- **实测官死/超时**：重派一次（基础设施失败不算数）；再失败该问记 `could_not`
  证据（原因文件），裁 `unprovable`，绝不编造。
- **靶子起不来**：本身就是一条集成缝隙 `gap`（"声称可跑，实测失败"，实测官的
  失败输出就是证据），盘问降级为 code/ledger 介质继续。

## 3. 收敛出报告

用户喊停或选中的面盘完 →
`python3 $ROOT/scripts/render_report.py docs/cross-exam/<run>/` →
把 completion-report.md 呈给用户。报告四类裁决计数、逐面"X 问中 Y 问实证通过"、
缺口清单（可直接转修复任务）、无法自证清单、未盘问声明、缺陷模式（patterns：每类
"共 N 位点，实证 M，未查 K"，未查位点逐个点名）、未拉的线（open_threads，
续盘接手点）——**没有编造的总百分比**。
