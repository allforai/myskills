# 产品体验改造 — 思维测试记录

日期：2026-09-18。结论：**9 个场景按预先冻结的判据跑完，首轮 7 通过、2 未通过（E2、E5）；两处都是文本没写到位，不是受试者跑偏。两处已各补一句并各钉一处契约，修后重测 E2b、E5b 均通过，失败回路 `closed`。**

首轮受测版本为 commit `dfeadc8c`（分支 `product-experience-overhaul`），重测在 `762965c1` 之上带 T-M5-11 修复的工作树。判据在任何受测代理启动之前就已冻结（T-M5-09），**修复与重测都没有动它**：`evidence.json` 顶层与 `retests[0]` 的 `launch.fixtures` 是同一对 sha256。首轮只判定与记录，没有改动任何 skill 文本；文本修复、契约钉子与重测都在 T-M5-11 里做。

## 方法与证据

- 每个 case 一个独立 fresh-context 子会话（`claude -p`，`--allowedTools Read --strict-mcp-config --output-format stream-json`），四路并发。
- packet = `subject-prompt.md` 的受试者指令 + 该 case `skill` 列表里各文件全文（按列表顺序、各带仓库相对路径标题，有 `sections` 的作为阅读指引）+ 该 case 的 `situation`。`expected` 不进 packet，留在评估端。
- packet 写在**仓库外**的会话 scratchpad。cwd 是实现仓库，所以隔离靠轨迹核对：从宿主 stream-json 轨迹提取 `tool_use` 事件，九个子会话各只有一次 `Read`（自己的 packet 文件），没有读取仓库其它文件、没有搜索、没有派子代理。
- requested `opus`，resolved `claude-opus-5`，取自轨迹里的 `assistant message.model`，不是受试者自报。
- 场景与判据：[thought-tests.json](../../fixtures/product-experience/thought-tests.json)；输入包装：[subject-prompt.md](../../fixtures/product-experience/subject-prompt.md)。
- 平台如实写进 `platform_simulated`：**没有调用 codex 或 pi CLI**，Codex/Pi 适配器只作为输入文本参与。
- 作废一次：E5 的 packet 有 85 KB，超出宿主默认的单次文件读取输出预算，首跑被迫读了第二次，按「多读即作废」重跑；作废的那次不在 `cases[]` 里。重跑把 `CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS` 提到 120000，一次 `Read` 读全。其余八个 packet 都在默认预算内。

## 场景判定

| 场景 | 受测规则 | 实际回答 | 判定 |
|---|---|---|---|
| E1 / claude：consumer 路线首开 `experience-direction` | 先 `propose` 再讨论；提案先答谁/情境/核心循环感受/回来的理由；点名成熟对标；推荐不等于确认 | 只发 `propose`（三条方向 + 恰好一条推荐），各自点名墨墨背单词 / LingQ / 多邻国及其做法，acceptance 写成可观察判据；显式按 §B 自查并拒绝把「碎片化」直译成时长切分器 | 通过 |
| E2 / codex：有提案轮 vs 无提案轮的「你定」 | 有轮次按推荐记 `delegate`；无轮次 `delegate` 被拒，先提案并等用户回复 | 情形甲全对（`delegate` 无 `proposal_id` 取 D2、`user_reference` 指向真实发言、`auto_decided` / `confirmation.delegated`、同批次 `answer`）；情形乙**同一轮里先 `propose` 再立刻 `delegate`**，用户没见过提案就产生了确认 | **未通过** |
| E3 / claude：用户只回「行，继续吧」 | 推荐、展示的默认值、沉默都不是动作；话题保持 pending；不靠 `exclude` 绕过 | 不记任何动作、话题保持 pending、拒绝 `freeze`，并补出两条判据之外的正确理由（`include` 只收已确认 ID；`mixed` 下 `not_applicable.experience` 会被拒） | 通过 |
| E4 / claude：UI 节点遇到无人规定的用户可见决定 | 发 `contract_gaps.kind = unspecified_user_visible_decision`；其余覆盖部分照常实现；`/run` 内不提问 | 条目 `kind` 写对、`needed_decision` 点名 user-flow-spec 的空边、`blocking_intent_ids: []` 并说明；其余 11 条实现并留证据；不造输入框、不编默认目的地、不改上游 spec | 通过 |
| E5 / codex：无界面的计费对账 API | `mode = none` 按谁在用判断；不加载体验知识、不排两道门；`freeze` 把 `gap-experience-direction` 放进 `exclude`；`plan` 用 `not_applicable.experience` | 前四项全对（含按 suppress-rules 在摘要写明豁免）；**`freeze` 那一步答成「待定，要先读到那份协议」并说可能在交互阶段直接问用户**，正是判据说的悬空待答问题；也没提 `not_applicable.experience` | **未通过** |
| E6 / claude：游戏路线的两道创意质量门 | 两个评审节点的落点、`concept-acceptance.hard_blocked_by` 指向实现后那次、每个评审各一条修复回路、must-fix 非空即未完成 | 六点全中，并自报了推断边界（`pipeline-closure-verify` 的阻塞是按 Must #9 的同一条法则推的，Must #8 明文只写了 `concept-acceptance`） | 通过 |
| E7 / codex：已有 runtime 体验评审在场 | 采信被覆盖的镜头格、不读 `design.md`、未关闭 must-fix 进 Prior evidence 不占 `R` 号、未覆盖的自己看 | 直接搬 runtime.md 的观察并标 `（runtime review 2026-09-10）`，EX2 只进 Prior evidence；错误态/空态两套样式与离线无提示成为 R1/R2，各带 kind / claim / recommend / evidence / tradeoff；不碰 `.allforai/` | 通过 |
| E8 / claude：cross-exam §1b 旅程采集 | 体验方向条目作候选来源；`auto_decided` 的标注受托选定；用户自选的不标注；只采集不进盘问 | 两条方向都进候选、`who` / `circumstance` 直接当前两元，D3 句末标「（此方向由模型受托选定）」而 D1 不标；未选的写进 `journey_candidates[]`；停在等用户定 | 通过 |
| E9 / pi：纯文本提案与「你定」 | 纯文本、无结构化控件；「你定」那一轮才记 `delegate`；沉默/中断不是委托 | 发给用户的原文是三条方向加推荐理由，全程没有 `AskUserQuestion`；`propose` 不带 `user_reference`；「你定」才 `delegate` 并同批次 `answer`；中断时 `resume` 原样重摆当前轮 | 通过 |

判据之外做对的几处都在**收敛**方向：E3 自己找到 `experience_not_applicable_on_ui_product` 这条拒绝；E6 主动把「哪些是文本明写、哪些是我推的」分开；E7 拒绝把 EX2 重述成新发现。

## 测出的缺陷与修复

首轮测出两处缺陷，T-M5-11 各补一句、各钉一处契约，并以 `E<n>b` 在修后的文本上按同样的隔离方式重测。

**缺陷 1（E2）—— 自建提案轮再同轮委托，canonical 没堵。**
`product-intent-confirmation.md` 的原句是「`Without a current proposal round both are refused`」。它只禁「没有轮次」，没禁「同一轮里自己先 `propose` 造出轮次、再立刻 `delegate`」。受试者引的正是这句，然后在情形乙里对着开场那句「体验方向你定，别问我」做了 `propose` + `decide/delegate`——用户一条方向都没看到，确认就成立了。`user_reference` 也确实指向一条真实用户发言，所以现有的 `user_reference` 约束拦不住它。缺的是一句：委托必须是用户**看过该轮提案之后**的回应，同一轮新建的提案轮不能就地被委托掉。

**缺陷 2（E5）—— `mode = none` 的收尾在 bootstrap 侧的文本里断了。**
`freeze` 把 `gap-experience-direction` 放进 `exclude`、以及 `plan` 用 `not_applicable.experience`，这两条只写在 `product-intent-confirmation.md` 里。E5 的受测文本是 `bootstrap/SKILL.md` + `bootstrap-planning.md` + `suppress-rules.md`——这三份里 `gap-experience-direction` 和 `not_applicable` 一次都没出现。`suppress-rules.md` 第 20 行只豁免了 Must #9 的质量门节点，没说这个 gap 怎么收尾。受试者于是诚实地停住（「要先读到那份协议」），还提出可能在交互阶段直接问用户——恰好是判据禁止的悬空待答。缺的是一句：`experience_priority.mode = none` 时，`gap-experience-direction` 在 `freeze` 里按「没有人看的界面」进 `exclude`，`plan` 可用 `not_applicable.experience`。

两处都不是判据写得苛刻：E2 的漏洞会让「用户没看过提案」的确认成立，E5 的断点会把一个本该自动收尾的 gap 变成向用户提问。

### 修复与钉住的字面量

| 缺陷 | 改动文件（孪生同一次改动双写） | 钉住的字面量 | 契约落点 |
|---|---|---|---|
| 1（E2） | `claude/meta-skill/knowledge/product-intent-confirmation.md` 的 `decide` 条目、`codex/meta-skill/skills/bootstrap.md` §0b | `a round opened in that same turn is not yet a current round` | `validate_meta_contracts.py::validate_experience_gate_contract`（`pins` 表新增 `knowledge/product-intent-confirmation.md` 一项）；`check_codex_meta_skill_parity.py` 的体验方向 parity 检查块；破坏性用例 `test_codex_contract_checks.py::…[self_opened_round-not yet a current round]` |
| 2（E5） | `claude/meta-skill/knowledge/bootstrap-planning.md` 的 Must #9、`codex/meta-skill/skills/bootstrap.md` 的体验质量门段 | ``excludes `gap-experience-direction` and states `not_applicable.experience` `` | `validate_meta_contracts.py::validate_experience_gate_contract`（bootstrap 语料字面量）；`check_codex_meta_skill_parity.py` 同一检查块钉住 Codex 孪生句 |

补进 canonical 的那句是：委托必须是用户**读过该轮提案之后**的回应，`propose` 之后同一轮 `delegate` 等于确认一个用户从没看过的方向，「你定」在没有轮次时的正确回应是开一轮、不是关一轮。补进 Must #9 的那句是：`experience_priority.mode` 为 `none` 时既没有门要排、也没有方向要确认，`freeze` 按「没有人看的界面」把 `gap-experience-direction` 放进 `exclude`，`plan` 写 `not_applicable.experience`（该键只在这个 mode 下合法），不把这个 gap 留成悬空待答。

### 重测（E2b、E5b）

| 场景 | 第 1 轮漏掉的 | 重测结果 | 判定 |
|---|---|---|---|
| E2b / codex | 情形乙同一轮 `propose` + `delegate` | 本轮只调 `propose`，纯文本列方向并点名推荐，话题保持待定，明说下一轮用户再说「你定」才按情形甲记 `delegate`；情形甲仍全对 | 通过 |
| E5b / codex | `freeze` 的 `exclude`、`plan` 的 `not_applicable.experience` | `gap-experience-direction` 进 `exclude` 并写明「这个产品没有人看界面」、明说不留成待答；`plan` 带 `not_applicable.experience` 及同一理由；前四项仍全对 | 通过 |

两次重测各只有一次 `Read`（自己的 packet），轨迹核对同第 1 轮。E2b 作废过一次：首跑的提示词没关掉 `Bash`，受试者用 `cat` 读 packet 并多读了一个文件，按「多读即作废」重跑，作废的那次不在 `cases[]` 里。`failure_loop.status` 记为 `closed`。

## 尚未验证

- **真实宿主对话质量未覆盖**：这九个都是单轮模拟决策，多轮真实会话里的提案质量、追问与改主意都没测；那条线见本计划的 T-M5-16。
- **真实 codex / pi CLI 未调用**：E2/E5/E7 的 codex 适配与 E9 的 pi 适配只作为输入文本参与，没有启动任何一个 CLI，所以只验证了适配器文本能否把决策带对，没验证它在原生宿主里的加载与执行。
- **`/run` 内评审的真实截图输入未覆盖**：E6 的体验/创意质量门只测了节点图与阻塞关系，design / runtime 两阶段评审真正吃到截图之后的判定质量没有测。
- 每个场景各一次运行、同一模型（`claude-opus-5`），不是重复采样或跨模型复核；重测同样是各一次。
- 受试者没有真实项目可操作，所有工具调用与产物写入都是回答里的伪调用；「不改上游 spec」「不碰 `.allforai/`」只在其声明的动作层面成立。
- 修复只重测了 E2、E5 两个场景。改动落在 `product-intent-confirmation.md`、`codex` 适配器与 `bootstrap-planning.md`，读同批文本的 E1/E3/E8/E9 没有回归重跑，只由契约钉子与既有单测兜底。
- 这两句新文本同样只在单轮模拟里验证过：真实多轮会话里用户在提案轮之后改口、或在一轮里既问又委托的情形没有测。

[原始答卷](product-experience-thought-tests/responses.md) · [证据](product-experience-thought-tests/evidence.json)
