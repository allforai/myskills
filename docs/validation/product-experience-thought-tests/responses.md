# E1–E9 原始答卷

2026-09-18。每个 case 一个 fresh-context 子代理，收到的只有 `subject-prompt.md` 的受试者指令、该 case `skill` 列表里各文件全文与该 case 的 `situation`，不含 `expected`。原文保留，未修稿；`<...>` 占位符按原文。


## E1（claude 适配）—— 新产品消费级首轮体验方向提案

## 实际动作

1. 当前是 `new-product` 路线，`experience_priority.mode = consumer`，所以在讨论 `experience-direction` 话题前必须先提出方向（`propose`）。这一轮只做 `propose`：
```
product_intent.py . < {operation:"propose", recommended_id:"dir-queue-review",
 rationale:"你要的是用零碎时间背单词、还能坚持下去。A 打开就能答题，30 秒被打断也不丢进度，最贴近你说的零碎时间",
 proposals:[A,B,C]}
```
每个提案都写满以下字段：`id/title/who/circumstance/core_loop_feel/first_minute/return_reason/goal/anti_goals/tradeoffs/scope/business_rules/acceptance/comparable`。不写 `origin`、`recommended`、`round`，这些由 CLI 标记。
2. 这一轮不做 `decide`，不做 `select` 或 `delegate`，也不回答 `gap-experience-direction`。

**A `dir-queue-review` 排队间隙的单手速记**
- 面向：通勤的上班族。
- 场合：站着排队、等地铁，每天 5 到 8 次，每次 30 秒到 2 分钟，常被打断。
- 核心循环：打开第一屏就是今天该复习的词，单手滑一下判断记住还是没记住，没有任何选单。
- 回来的理由：复习按遗忘曲线排好，已到期的词数一眼可见。
- 对标：墨墨背单词。它按记忆曲线安排每天的复习量。
- 验收：从点开图标到答第一题不超过 3 秒；中途被打断，再打开能接着上次；全程单手完成。
- 不做：课程目录、首页仪表盘。

**B `dir-work-context` 从工作语境里学词**
- 面向：想用英语写邮件、开会的上班族。
- 场合：午休或下班路上，每天 1 到 2 次，每次 5 到 10 分钟。
- 核心循环：读一段职场短文，点不认识的词收进词库，之后在新的短文里再次遇到它。
- 回来的理由：学过的词真的出现在自己的工作里。
- 对标：LingQ。它在阅读中收词，并追踪这些词后来在哪里再次出现。

**C `dir-team-streak` 同事小队一起坚持**
- 面向：自己背不下去的人。
- 场合：每天固定一次，3 到 5 分钟。
- 核心循环：2 到 4 人组队，各自完成当天的量，队友能看到谁完成了。
- 回来的理由：怕拖累队友。
- 对标：多邻国的好友任务。两位好友合作完成每周目标。

每轮都按 §B 自查过：
- 三个方向各自回答"为什么会回来"，不同的是方向，不是规模。
- 没有做成"碎片模块"。
- 不是给用户的管理后台，也不是功能清单。

## 面向用户的答复

"坚持下去"的方式我整理了三个方向，差别在于靠什么让你坚持：
- **A 排队间隙单手速记**（推荐）：点开就答，30 秒被打断也不丢进度，复习节奏由记忆曲线安排。
- **B 从工作语境学词**：在职场短文里遇到词、收词，再在新短文里遇到它。适合能整块抽出几分钟的时候。
- **C 同事小队打卡**：靠同伴之间的约定坚持下去。

请选一个，也可以说哪里要改。如果想让我替你定，请直接说，我会按推荐的 A 记下，并在运行结束时向你列明这一项是我代你决定的。

## 关键原句

- "`propose` is mandatory before the `experience-direction` topic is discussed"
- "A recommendation is not an action. Only the user's own `select`, or a `delegate` they asked for in that turn, creates a confirmed experience direction"
- "a direction that answers it with a "fragments" module has translated the phrase instead of designing for what it describes"
- "Two or three directions differ in direction, not in size"


## E2（codex 适配）—— Codex 两种情形下的 delegate

**情形甲（第 1 轮已记录 propose，推荐 D2，用户说「你定吧……按你推荐的来」）**

实际调用：
```
decide {
  batch_id: "exp-dir-r1-delegate",
  topic: "experience-direction",
  user_reference: "<本轮用户原话：你定吧，我不懂这些，你按你推荐的来>",
  actions: [
    {operation: "delegate", reason: "用户本轮明确要求按推荐决定"},
    {operation: "answer", id: "gap-experience-direction", answer: "<D2 的 title>", reason: "同上"}
  ]
}
```
- `delegate` 不带 `proposal_id`。CLI 会自动取本轮推荐的 D2，生成 `experience-direction-D2`，写入 `origin: model-proposal`、`auto_decided: true`、`confirmation.delegated: true`。
- 理由：当前有提案轮次，用户在本轮亲口把决定交给我。依据原句：「it is legal only where the user said in that very turn to decide for them, and the batch `user_reference` must be that real user turn」。
- 对用户说：「好，按推荐定为 D2〈标题〉。这条会标为『代你决定』，运行结束时会列出来给你看。想换随时说。」

**情形乙（还没有任何 propose，用户开场说「体验方向你定，别问我」）**

1. 先调用 `propose`，写 2–3 条方向。每条都要有 who、circumstance、core_loop_feel、first_minute、return_reason、comparable 等字段，几条之间是方向不同，不是同一个想法的大小档位。另外写 `recommended_id` 和用用户自己的话讲的 `rationale`。这一步不需要 `user_reference`。
2. propose 成功后，在同一轮调用 `decide`：
   - `batch_id: "exp-dir-r1-delegate"`，`topic: "experience-direction"`
   - `user_reference`：用户开场那句原话（不是我展示方向的那一轮，也不是推荐本身）
   - actions：`delegate`，以及 `answer gap-experience-direction`（值为推荐方向的标题）
3. 用纯文本列出这几条方向，标明哪条是代为决定的，说明运行结束时会披露，也可以随时改（先 `remove` 再 `select`）。

理由有两条：
- 没有提案轮次时直接 delegate 会被拒。依据：「Without a current proposal round both are refused」，以及「`propose` is mandatory before the `experience-direction` topic is discussed」。
- 用户这一轮确实明确说了让我定，所以可以代为决定。依据：「Deciding for the user is allowed only because it is later visible」。

**assume-and-declare 能做和不能做的**
- 能做：给出推荐、陈述理由、披露我做了什么。
- 不能做：产生 `select` 或 `delegate`。两种情形里的 delegate 都来自用户本轮的原话，不是来自这个约定。
- 依据：「the Codex assume-and-declare convention cannot produce a `select` or a `delegate`. A recommendation, a displayed default and silence are not actions」。如果用户没回应，这一轮就只是提案，这个话题仍然待定。


## E3（claude 适配）—— 「继续吧」不是选择

**实际动作（伪调用）**

1. `product_intent.py . < {"operation":"resume"}`：读取待决话题。预期 `topics` 里仍有 `experience-direction`，其下 `proposals` 是第 1 轮的 D1/D2/D3，`recommended_id:"D1"`，另有待答问题 `gap-experience-direction`。
2. 不调用 `decide`，不写 `select`，也不写 `delegate`，journal 里不增加任何记录。
3. 不再次 `propose`。第 1 轮仍是当前轮，用户也没有否定它。
4. 不调用 `freeze`。

**`experience-direction` 当前状态**

仍是 pending，只有提案，没有确认的方向。不存在 `experience-direction-D1` 这个已确认项，`gap-experience-direction` 也还没回答。D1 高亮只是展示给用户的默认项。「行，继续吧」回应的是数据库问题，不是在选方向，也不是让我替他选。

**能否 freeze：不能**

- `include` 只能写已确认的 intent ID，而现在没有任何已确认的体验方向可以放进去。
- 如果把 `gap-experience-direction` 写进 `exclude`，理由只能由我编造，用户没说过要排除。把它排除掉也不能授权依赖这个选择的工作。
- 本项目 `mode = "mixed"`，是有界面的产品，不是“没人看的产品”，排除体验方向不成立。
- 到了 plan 阶段，`not_applicable.experience` 也会被拒绝，报 `experience_not_applicable_on_ui_product`。

**面向用户的答复**

> 好，接着来。数据库按刚才说的定下就行。进入下一步之前，还差一个决定需要你来做：产品的体验方向。上一轮给了三条：
> - D1《…》（我推荐的）：适合谁、在什么情境下用、核心体验……
> - D2《…》：……
> - D3《…》：……
>
> 我推荐 D1，理由是……。不过推荐不算你的决定，界面上 D1 高亮也不算。请直接回复选哪一条，也可以说要怎么改。如果你想让我替你定，明确说一句「你帮我定」，我就按 D1 记录，并标注为“由我代为决定”，运行结束时会把这条列出来给你看。这一项没定之前，范围没法冻结。

**依据原句**

- “recommendations, displayed defaults, omitted answers and silence are not actions; `select` and `delegate` are actions.”
- “a displayed default nobody answered stays a proposal.”
- “`delegate` … is legal only where the user said in that very turn to decide for them”
- “Never restore by relabeling old code or interpreting continue/accept as a product choice.”
- “`include` names confirmed intent IDs … Excluding a question cannot authorize work that depends on its unanswered choice.”
- “A product nobody looks at excludes `gap-experience-direction`”


## E4（claude 适配）—— UI 节点遇到无人规定的用户可见决定

## 本轮动作

1. **实现并验证已有规格的 11 条屏幕要求**：导出页的字段、状态、文案都做完，照常写 Effect Verification 证据。
2. **导出完成后的去向一行都不实现**：不写默认跳转，不加"返回首页"之类的临时处理，也不做占位页。
3. **在节点产物的 `contract_gaps[]` 追加一条**（伪调用 append）：
```json
{
  "kind": "unspecified_user_visible_decision",
  "where": "export screen — 导出成功后的导航去向",
  "needed_decision": "导出完成后用户落到哪里：留在导出页并显示结果、回到来源页，还是进入导出文件/分享页？user-flow-spec 中这条边为空，产品概念和其他上游产物都没有覆盖，目前没有任何需求覆盖这个决定。",
  "blocking_intent_ids": [],
  "suggested_owner_artifact": ".allforai/app-design/spec/user-flow-spec.json"
}
```
   场景没有给出本节点 `requirement_refs[].id` 里覆盖导出流程的需求，所以按规则填 `[]`，并在 `needed_decision` 里写明。如果 refs 里确有导出需求 id，就填那个 id。
4. **让节点失败**：`check_artifacts.py` 不通过，节点不标记完成。不清空这个字段，不改成 `known_gaps`，也不降低 `kind`。
5. **走诊断路径**：`suspected_root_node` 是 `exit_artifacts` 里包含 user-flow-spec.json 的那个设计节点。诊断会重置它和它的下游，由它补上这条边，然后本节点重跑。
6. **在 /run 内不向用户提问。**

## 面向用户的答复

> `export-screen-implement` 已实现并验证 11 条有规格的导出页要求。只有「导出完成后用户去哪」这一条，没有任何上游设计产物做过决定（user-flow-spec 里这条边是空的），我没有自行决定，也没有做占位跳转，已作为 `contract_gaps` 记录。因此这个节点按设计判为未完成，已交给诊断：由产出 user-flow-spec.json 的设计节点补上这个决定，之后本节点会自动重跑。如果诊断判断这个决定必须由你来定，它会在下一次 `/run` 开始前作为阻塞项请你确认。

## 判断依据（原句）

- "**Do not implement the decision** and do not ship a placeholder surface for it."
- "**Finish and evidence the covered remainder** of the node as usual."
- "`blocking_intent_ids` may be `[]` when no requirement covers the decision at all — say so in `needed_decision`."
- "**Let the node fail.** … never empty the field, relabel the entry as `known_gaps`, or soften the `kind`"
- "Never ask the user inside `/run` — a product decision that genuinely needs the user becomes a preflight blocker for the next `/run`"
- "Silence in the contract is a gap, not a delegation."


## E5（codex 适配）—— 无界面的 API 服务：mode = none 的全链路

## 实际动作（伪调用）

1. 写入 `.allforai/bootstrap/bootstrap-profile.json`：
```json
"experience_priority": {"mode": "none", "reason": "纯 HTTP API 计费对账服务，只供两个后端服务调用，运维只看日志和 Grafana，没有任何终端用户界面。"}
```
   `task_route: "new-product"`、`is_game_project: false`。用了 Vite/React 工具链不影响判断。

2. Step 2 不加载第 9 项那组体验知识，也就是 product-concept.md、consumer-maturity-patterns.md、journey-emotion-schema.md、app-design.md。仍按第 1 项加载与 goals（create / implement / launch-prep 等）同名的能力文件，第 4 项的 cross-phase-protocols 和 defensive-patterns 也照常加载。

3. 节点图里没有体验节点：不规划体验设计节点，也不规划 design 和 runtime 两个体验质检节点，`required_repair_loops` 里也不声明这两个节点的修复回路。`user_steps` 仍写 `["/cross-exam", "/product-review"]`，因为豁免规则只免 cli 和 library-sdk。

4. `freeze` 这一批里的 `gap-experience-direction`：product-intent-confirmation.md 没有内联，我不知道 `freeze` 对这个 gap 的具体字段和操作。我不会编造"用户选定了某个体验方向"的记录，也不会替用户选。这一步待定，要先读到那份协议再按它处理。协议如果允许把这项标为"不适用"，理由写 `experience_priority.mode = none`；如果不允许，就在交互阶段直接问用户，不留到 `/run`。

## 面向用户的答复

> 这个项目是纯后端计费对账 API，没有终端用户界面，所以 `experience_priority` 记为 `none`。体验方向、体验设计节点和两段体验质量门都不适用，这份总结里写明这项豁免。流水线结束后仍请依次运行 `/cross-exam` 和 `/product-review`。体验方向这一项在确认阶段怎么收尾，还要看意图确认协议的规定；我不会替你编一个决定。

## 依据原句

- "`none` = there is no end-user interface. Use `none` only when … or the project is pure backend/API."
- "Judge by who the product serves, not by the tech stack"
- 第 9 项："when `task_route` is `new-product` or `product-reconstruction` and `experience_priority.mode != none`, always load …"
- Must #9："On non-game product routes whose profile records `experience_priority.mode` as `consumer` or `mixed`, plan two critique nodes"
- 体验设计节点规则："whose `experience_priority.mode` is `consumer` or `mixed`, the workflow contains node(s) … experience design artifacts"
- 豁免表："`experience_priority.mode = none` | experience quality gate (Must #9) nodes | no end-user UI to judge; the summary states the exemption"
- `user_steps`："The only exemption is a suppress rule … CLI or library-sdk"


## E6（claude 适配）—— 游戏路线的两道创意质量门

**实际动作（伪调用，写入 workflow.json 和 readiness spec）**

1. 放两个创意质量评审节点，都执行 `${CLAUDE_PLUGIN_ROOT}/skills/game-creative/40-qa/creative-quality-critique/SKILL.md`：
   - `creative-quality-critique-design`：`hard_blocked_by: ["game-design-finalize"]`。美术、音频和前端实现节点都 `hard_blocked_by` 它（这一条是按 Must #9 的“同一条法则”推断的）。
   - `creative-quality-critique-runtime`：`hard_blocked_by` 最后一个美术、UI、音频、前端 QA 节点，也就是视觉 QA 和运行时 smoke。
   - 两个节点都由一个新开上下文的评审者执行，只读 Input Contract 里列出的产物和证据。节点 id 里不出现 `cross-exam` 或 `product-review`。
2. `concept-acceptance.hard_blocked_by` 加入 `"creative-quality-critique-runtime"`。`pipeline-closure-verify` 也加上同样的依赖（按 Must #9 类推）。
3. `required_repair_loops` 每个评审节点各声明一条：
   - 设计评审：`{qa_node_ids:["creative-quality-critique-design"], repair_node_id:"game-design-critique-repair", closure_node_ids:[<第一批美术/音频/前端实现节点>], max_attempts:3}`。修复节点由发现问题所属的设计 pack 负责重跑。
   - 运行时评审：`{qa_node_ids:["creative-quality-critique-runtime"], repair_node_id:"game-impl-critique-repair", closure_node_ids:["concept-acceptance","pipeline-closure-verify"], max_attempts:3}`。修复节点属于对应的美术、UI、音频或前端 pack；修完重跑受影响的 QA 和运行时评审。
   - 预算用完时按 Run Policy 处理，运行中不向用户提问。
4. 保留 `"user_steps": ["/cross-exam", "/product-review"]`。

**面向用户的答复**

> 创意质量评审放了两个。第一个在 `game-design-finalize` 之后、所有美术/音频/前端实现之前，先确认设计本身不平庸。第二个在最后的视觉 QA 和 smoke 之后，评审实际跑起来的游戏。`concept-acceptance` 和 `pipeline-closure-verify` 都要等第二个评审完成。每个评审在 readiness spec 里各有一条修复回路，最多修 3 次，must-fix 问题交给所属 pack 修复。只要 `must_fix_*` 列表非空，评审节点就不算完成，下游验收不会启动。验收只核对覆盖，不打分；“做完没有”和“好不好”留给跑完后你手动执行的 `/cross-exam` 和 `/product-review`。

**依据**

- Must #8：“After `game-design-finalize`, and again after the last art/UI/audio/frontend QA … `concept-acceptance` is `hard_blocked_by` it; `must_fix_*` findings route to the owning pack's repair loop.”
- Must #9：“Item 8 states the same law for games” / “Declare one loop per critique node” / “max_attempts from the Must #2 budget”。
- concept-acceptance.md：“While that critique's `must_fix_*` list is non-empty the critique node is not complete, so this gate does not start.”

**说明**：Must #8 明文只写了 `concept-acceptance` 被阻塞。`pipeline-closure-verify` 的阻塞、实现节点等待设计评审、以及两条回路的具体字段，都是我按 Must #9 的“同一条法则”推出来的。


## E7（codex 适配）—— product-review 采信既有体验评审

**本轮动作（伪调用）**

1. `read docs/experience-review/runtime.md`。被评提交 abc1234 与 HEAD 一致，不算过期。
2. 不读 `docs/experience-review/design.md`、`.allforai/` 和 `product-concept.json`。`docs/cross-exam/` 不存在，跳过。
3. 写 `docs/product-review/2026-09-18-<slug>/recommendations.md`，关键字段如下：

```
- JOB1 — who: 上班族 / circumstance: 通勤路上 / progress: 把今天要背的单词过一遍
  - 前提: 本次观察（未验收） · <入口与终态观察>
  - 商业级: 引导 缺 <runtime 观察原文>（runtime review 2026-09-10）· 缺时: 已知 must-fix EX2，不立项
    · 过程反馈 有|缺 <runtime 观察原文>（runtime review 2026-09-10）
    · 下一步 未查 · 状态一致 缺 单词卡错误态与空态两套样式 · R1
    · 回来理由 未查
Prior evidence:
none（cross-exam）
docs/experience-review/runtime.md (2026-09-10, abc1234) — EX2 (onboarding) blocks JOB1; lens cells adopted: JOB1 引导, 过程反馈
### R1 — 单词卡错误态与空态不是同一套
- job: JOB1 · kind: ui_friction · claim: 不够商业级 · depends_on: (空) · recommend: adopt
- tradeoff: 统一两种状态要改卡片组件的样式
- evidence: <组件路径/界面状态>（无浏览器时标 code-only）
### R2 — 离线时没有任何提示
- job: JOB1 · kind: interaction_gap · claim: 不够商业级 · depends_on: (空) · recommend: adopt
- tradeoff: 需要加网络状态检测和一套离线文案
- evidence: <离线时的界面观察或代码行>（无浏览器时标 code-only）
```

Evidence limits 还要把 runtime.md 自带的证据限制并入 consequence 那一句。

**给用户的答复**

我读了 `docs/experience-review/runtime.md`。它的被评提交和当前 HEAD 一致，所以它的结论直接采用。design.md 判的是设计产物，我没读。`.allforai/` 和 `product-concept.json` 按规则不碰。

仓库里没有 cross-exam 报告，所以 JOB1「有没有入口、能不能走完」只按我这次看到的写，标成未验收。要正式判完成度，入口是 cross-exam。

商业级这几格这样填：
- **引导、过程反馈**：直接搬评审里的观察。引导那格是缺，对应 EX2，这个问题已经记过，不再占 R 号，只在 Prior evidence 写「EX2 卡住 JOB1」。
- **状态一致**：填「缺」，对应 R1（错误态和空态是两套样式）。
- **离线无提示**：进 R2。如果离线时单词根本加载不出来、背不下去，就把 R2 改成 broken_path，主张改为「进展受阻」。
- **下一步、回来理由**：还没查，填「未查」。

这份文件可以作为 `$grill-me` 的上游输入。我到此为止，不开始 grill，也不改代码。

**依据原句**
- 「Do not read `design.md` — 那份判的是设计产物」
- 「No `.allforai/`. Do not read or write that tree.」
- 「被它覆盖的格直接写 `有|缺 <它的观察>（runtime review <评审日期>）`，不重新检查」
- 「已知的 must-fix 不再占 `R` 号」
- 「写成 `缺` 的每一格，要么对应一条 `R`，要么在同一格用一句话说明为何不立项」
- 「没有报告就记成未验收前提，并说一次 cross-exam 是判这件事的入口」


## E8（claude 适配）—— cross-exam 旅程采集里的受托方向

## 实际动作

1. 只读 `.allforai/product-concept/product-concept.json`，从 `requirements[]` 里筛出 `topic == "experience-direction"` 且 `status == "confirmed"` 的条目。同一个 id 有多条时取 `revision` 最大的那条。结果是 D1 和 D3。我不调用 `product_intent.py` 的任何写操作，因为 cross-exam 只记账、不修改，也不替用户确认。
2. 两条都有 `who` 和 `circumstance`，直接作为三元组的前两项；`progress` 从各自的 `acceptance` 起草。D3 带有 `auto_decided: true`，摆给用户时句末要加标注。
3. 从 README 的线索起草一条候选；census 的操作面按「入口 → 终态」归成候选，一并列出。
4. 用 `AskUserQuestion` 多选，保留 Other。

## 摆给用户的候选旅程

- J1：上班族自学者，在通勤路上的十来分钟里，完成〈D1 acceptance 起草的进展〉。
- J2：备考学生，在晚自习的整块时间里，完成〈D3 acceptance 起草的进展〉。（此方向由模型受托选定）
- J3：〈README 线索改写的三元组草稿〉。
- J4…：〈census 操作面归成的「入口 → 终态」候选〉。

## 面向用户的答复

> 下一步是旅程采集。候选来自三处：
> - 两条你确认过的体验方向。
> - README。
> - 普查官列出的操作面。
>
> 其中 J2 是你上一轮说「你定」之后由模型选定的方向，我已经标出来了。它是不是你真想验收的场景，请你这次亲自决定。
>
> 请勾选要盘的旅程，也可以在 Other 里补充。勾选后我会把每条改写成完整的三元组，并补上 oracle：做成是什么样（`done_looks_like`），卡死是什么样（`stuck_looks_like`）。改写结果会读回给你确认。
>
> 「通勤十来分钟」「晚自习整块时间」会作为决定成败的处境写进 circumstance，所以 `done` 只覆盖这些点。没勾的候选会写进 `journey_candidates[]` 并附上你的原话，报告里会点名，不会消失。

## 关键依据

- 「`requirements[]` 里 `topic == "experience-direction"`、`status == "confirmed"` 的条目（同 id 取最新 `revision`）」
- 「条目带 `who`/`circumstance` 就直接作三元组前两元……`progress` 从它的 `acceptance` 起草」
- 「条目 `auto_decided: true` 的，候选在摆给用户时句末标注"（此方向由模型受托选定）"」
- 「存在就读、不存在不算缺」
- 「不另派 agent 读代码，也不凭印象读代码定候选」
- 「未选的候选同样落账：写进顶层 `journey_candidates[]`」


## E9（pi 适配）—— Pi 纯文本提案与「你定」

## 本轮动作

**1. 先写提案，不提问（伪调用）**

```
python3 .allforai/bootstrap/scripts/product_intent.py . < request.json
{ "operation": "propose",
  "proposals": [
    { "id": "dir-a", "title": "<方向A>", "who": "…", "circumstance": "…(含规模与频次)",
      "core_loop_feel": "…", "first_minute": "…", "return_reason": "…", "goal": "…",
      "anti_goals": ["…"], "tradeoffs": ["…"], "scope": ["…"], "business_rules": ["…"],
      "acceptance": ["<可观察的体验判据>"], "comparable": {"product": "…", "approach": "…"} },
    { "id": "dir-b", … }, { "id": "dir-c", … } ],
  "recommended_id": "dir-a",
  "rationale": "<用用户自己的话说明为什么推荐>" }
```

请求里不写 `origin`、`status`、`recommended` 这些权限字段，由 CLI 自己盖章。场景没给出已确认的目标用户和场景内容，所以 `<…>` 要按那两个话题的确认结果填，我不编造具体方向。

**2. 发给用户的原文**

> 接下来确定体验方向，下面三条供你选：
> **A（推荐）<标题>**：给<谁>，用在<什么情境、多久用一次>。核心循环的感觉是……，第一分钟会……，让人回来的理由是……。参照<成熟产品>，它的做法是……。代价是……
> **B <标题>**：……
> **C <标题>**：……
> 推荐 A，因为<你说过的……>。请回复 A、B 或 C，也可以直接说"你定"。

发之前先对照 §B 自查：不能是压缩版管理后台，不能是概念演示，也不能用功能清单代替体验。三条方向要在方向上不同，不能只是同一个想法的大中小三档。

## 用户回「你定」之后

```
{ "operation": "decide", "batch_id": "exp-dir-1", "topic": "experience-direction",
  "user_reference": "<用户说「你定」那一轮的真实引用>",
  "actions": [
    { "operation": "delegate", "reason": "用户原话「你定」，委托我在推荐方向中决定" },
    { "operation": "answer", "id": "gap-experience-direction",
      "answer": "<dir-a 的 title>", "reason": "用户委托，采用推荐方向" } ] }
```

- `delegate` 不带 `proposal_id`，默认取本轮推荐的方向。
- 结果会记下一条已确认的 `experience-direction-dir-a`，带 `origin: model-proposal`、`auto_decided: true`、`confirmation.delegated: true`。

给用户的答复：

> 按你的委托选了 A。这是我替你做的决定，运行结束时会在完成清单里列出来；想换随时说。

## 没有回复或会话中断

- 不记录任何 `select` 或 `delegate`，推荐的那条仍然只是提案，话题保持待定，不 `freeze`，不规划节点。
- 重新进入时用 `{"operation":"resume"}` 取回当前这一轮提案，原样再给用户，只问这个待定话题，不重新 `propose`。

## 依据原句

- "推荐和展示的默认值不是动作，沉默、中断、没有回复都不是委托。"
- "`delegate` … legal only where the user said in that very turn to decide for them, and the batch `user_reference` must be that real user turn, never the recommendation or the turn it was displayed in."
- "must `answer` `gap-experience-direction` with the chosen direction's title."
- "disclosed back to the user at run completion through `product_intent.py . --delegations`."


---

# 重测（第 2 轮 · T-M5-11 失败回路）

2026-09-18。只重跑第 1 轮判 `fail` 的 E2、E5，case id 加后缀 `b`。判据文件一字未动（`launch.fixtures` 的
sha256 与第 1 轮记录相同），改的只是受测的 skill 文本；packet 按第 1 轮同样的方式重新拼装，因此 packet 的
sha256 与第 1 轮不同——差异就是这次的修复。隔离方式相同：仓库外 scratchpad 的单个 packet 文件，
子会话只允许 `Read`，轨迹核对工具调用。

## E2b（codex 适配 · 重测）—— Codex 两种情形下的 delegate

## 情形甲：已有第 1 轮，用户这一轮说“你定吧”

**实际调用**：`decide`
```json
{"operation":"decide",
 "batch_id":"exp-dir-r1-delegate",
 "topic":"experience-direction",
 "user_reference":"<本轮用户消息的引用：「你定吧，我不懂这些，你按你推荐的来」>",
 "actions":[
  {"operation":"delegate",
   "reason":"用户原话：你定吧，我不懂这些，你按你推荐的来"},
  {"operation":"answer","id":"gap-experience-direction",
   "answer":"<D2 的 title>",
   "reason":"用户委托按推荐方向 D2 决定"}]}
```
- `delegate` 不带 `proposal_id`，自动取第 1 轮推荐的 D2。
- 结果会生成已确认的条目 `experience-direction-D2`：`origin: model-proposal`，`auto_decided: true`，`confirmation.delegated: true`。

**理由**：
- 第 1 轮已经在上一轮以纯文本给用户看过，所以现在是“当前轮”。
- 用户在这一轮明确说了让我替他们决定。
- `user_reference` 必须是这句用户原话，不能是展示推荐的那一轮。
- 运行结束时，用 `product_intent.py . --delegations` 把这个替用户做的决定告诉用户。

**给用户的答复**：“好，按我推荐的 D2 定下。这个方向会记为‘由我代为决定’，运行结束时会再提醒你一次，到时想换可以改。”

## 情形乙：没有任何 propose，用户第一句就说“体验方向你定，别问我”

**实际调用**：只调用 `propose`，本轮不调用 `decide`。
```json
{"operation":"propose",
 "proposals":[<2–3 条方向，每条的键恰好是：id、title、who、circumstance、core_loop_feel、first_minute、return_reason、goal、anti_goals、tradeoffs、scope、business_rules、acceptance、comparable{product, approach}>],
 "recommended_id":"<其中一条>",
 "rationale":"<用用户自己的说法解释为什么推荐>"}
```
- 不写 `origin`、`status`、`round`、`recommended` 这些字段，由 CLI 自己加。
- 不需要 `user_reference`。

**理由**：
- 没有当前轮时，`select` 和 `delegate` 都会被拒绝。
- 同一轮里先 `propose` 再 `delegate`，等于确认了一个用户从没看过的方向。
- 因此这一轮以纯文本列出几条方向、标明推荐项，然后结束，话题保持待定。

**给用户的答复**：“我先写了三个方向，推荐 X。你回一句‘按推荐’或选一个就行，看都不用细看。”

用户下一轮如果再说“你定”，就按情形甲处理 `delegate`，`user_reference` 用那一轮的原话。

## Codex 的 assume-and-declare 约定在这里的作用

**能做的**：只能用在不涉及产品意图批准的地方。这里的体验方向必须等用户回复，所以它帮不上忙。

**不能做的**：
- 不能产生 `select` 或 `delegate`。
- 不能把推荐、展示的默认项或用户没说话当成确认。
- 没人回复的一轮仍然只是提案，话题仍待定。

## 关键原句
- “a round opened in that same turn is not yet a current round … the turn that opens a round ends with the proposals presented and the topic pending”
- “"decide it for me" said before any round exists is answered by opening one, not by closing it”
- “legal only where the user said in that very turn to decide for them, and the batch `user_reference` must be that real user turn”
- “the Codex assume-and-declare convention cannot produce a `select` or a `delegate`”

## E5b（codex 适配 · 重测）—— 无界面的 API 服务：mode = none 的全链路

## 本轮动作（伪调用）

1. 写入 `.allforai/bootstrap/bootstrap-profile.json`：
```json
"architecture_pattern": "rest-api-service",
"experience_priority": {"mode": "none", "reason": "纯 HTTP API 对账服务，没有终端用户界面，只由两个后端服务调用，运维只看日志和 Grafana"}
```
Vite 和 React 生态工具链只是构建工具，不会让 mode 变成 consumer、admin 或 mixed。

2. Step 2 不加载体验那组知识（第 9 项，包括 product-concept.md、consumer-maturity-patterns、journey-emotion-schema、app-design.md）。只按 goals 加载 implement 和 launch-prep 对应的能力文件，再加上 cross-phase-protocols 和 defensive-patterns。

3. 节点图里没有体验相关节点：
   - 不规划体验设计产物节点，比如 job-story-spec、user-flow-spec。
   - 不规划 Must #9 的两个 experience-quality-critique 节点（design 和 runtime）。
   - `required_repair_loops` 里也不声明这两个节点的修复回路。

4. `freeze` 批次：用 `product_intent.py` 把 `gap-experience-direction` 放进 `exclude`，理由写“这个产品没有人看界面”。不让它作为待回答问题挂着。`plan` 带上：
```json
"not_applicable": {"experience": "纯后端 API，无终端用户界面，没有人看这个产品"}
```

5. `user_steps` 仍然是 `["/cross-exam", "/product-review"]`。只有 cli 或 library-sdk 能豁免这两步，这个项目两者都不是。

## 给用户的答复

> 你的服务只提供 HTTP API，调用方是两个后端服务，运维只看日志和 Grafana，没有终端用户界面，所以体验优先级记为 `none`。这次不加载体验设计方法，也不规划体验设计和体验质量评审节点。“体验方向”这个问题我已明确标为不适用并写明原因，不会作为待答问题留着。构建工具用了 Vite，但这不影响判断。流水线结束后，仍然请你依次手动执行 /cross-exam 和 /product-review。

## 判断依据（原句）

- “`none` = there is no end-user interface. Use `none` only when … or the project is pure backend/API. Judge by who the product serves, not by the tech stack”
- “when `task_route` is `new-product` or `product-reconstruction` and `experience_priority.mode != none`, always load …”
- “`experience_priority.mode = none` | experience quality gate (Must #9) nodes | no end-user UI to judge”
- “the run excludes `gap-experience-direction` and states `not_applicable.experience` … `freeze` maps that gap question into `exclude` … Suppressing the gate never means going quiet about the question it came from.”
- “The only exemption is a suppress rule … a CLI or library-sdk project … Any other project gets both steps”

---

# 第 3 轮（最终文本，2026-09-18，受测提交 cbeac167）

## E1c（claude 适配）

### 本轮动作

1. **自检（`consumer-maturity-patterns.md` §B）**：三个方向都没有"碎片模块"之类的功能名，也不是同一个想法换三种预算。
2. **调用 `product_intent.py`**（伪调用）：

```
python3 .allforai/bootstrap/scripts/product_intent.py . < request.json
{"operation":"propose","recommended_id":"dir-queue-minute",
 "rationale":"你说要用零碎时间、还要能坚持：排队那一分钟打开就能背完一组，第二天有东西在等你，才坚持得住",
 "proposals":[
  {"id":"dir-queue-minute","title":"排队一分钟","who":"通勤、排队、等电梯的上班族",
   "circumstance":"一天 5–10 次，每次 30–90 秒，单手操作，随时会被打断",
   "core_loop_feel":"打开就背，不用选，也不用加载","first_minute":"不注册，直接背 5 个词",
   "return_reason":"到期要复习的词在等你，断了的进度不清零",
   "goal":"把零散的几分钟攒成稳定的记忆","anti_goals":["长课程","开屏选菜单"],
   "tradeoffs":["放弃深度讲解"],"scope":["间隔复习","中断续背"],
   "business_rules":["一组不超过 90 秒"],
   "acceptance":["冷启动 3 秒内出现第一个词","中途被打断，回来还在原位置"],
   "comparable":{"product":"Duolingo","approach":"几分钟一课，连续打卡加定时提醒"}},
  {"id":"dir-work-context","title":"工作里遇到的词","who":"要读英文邮件和文档的职员",
   "circumstance":"工作中碰到生词，回头利用空档背","core_loop_feel":"背的词都是自己真用得上的",...,
   "comparable":{"product":"LingQ","approach":"从用户自己读的材料里收词"}},
  {"id":"dir-buddy","title":"和同事结伴","who":"一个人容易放弃的人",
   "circumstance":"两三人一组，每天互相看到对方进度","core_loop_feel":"不想拖别人后腿",...,
   "comparable":{"product":"Duolingo 联赛","approach":"每周排名加好友互相督促"}}]}
```

后两个方向的 `first_minute`、`return_reason`、`goal`、`anti_goals`、`tradeoffs`、`scope`、`business_rules`、`acceptance` 同样写成非空的文本或列表。

3. **本轮不调用 `decide`**：不 `select`，不 `delegate`，不回答 `gap-experience-direction`。话题保持待定。

### 给用户的答复

体验方向我写了三个，它们是三种不同的做法，不是同一个方案的大小版本：

- **A 排队一分钟（推荐）**：打开就背，90 秒一组，被打断了回来接着背。每天有到期要复习的词，帮你坚持。参照的是 Duolingo 的短课加连续打卡。
- **B 工作里遇到的词**：只背你在工作中真碰到的词，有用，所以你愿意回来背。参照的是 LingQ。
- **C 和同事结伴**：靠彼此看得见的进度坚持下去。参照的是 Duolingo 联赛。

我推荐 A，因为它最直接对应你说的"零碎时间"和"坚持"。推荐只是我的建议，不算替你做了决定。请选一个，或者告诉我怎么改；你也可以说"你帮我定"。

### 依据原句

- "propose is mandatory before the experience-direction topic is discussed"
- "The user's words are the circumstance to design for, never vocabulary to transcribe."
- "the turn that opens a round ends with the proposals presented and the topic pending"
- "A recommendation is not an action."

## E2c（codex 适配）

### 情形甲（第 1 轮已展示，用户本轮说「你定吧……按你推荐的来」）

**实际调用：**
```
product_intent.py . < {
  operation: "decide",
  batch_id: "exp-dir-r1-delegate",
  topic: "experience-direction",
  user_reference: "<本轮用户原话所在的 user turn：『你定吧，我不懂这些，你按你推荐的来』>",
  actions: [
    { operation: "delegate", reason: "用户本轮明确要求按推荐方向替其决定" },
    { operation: "answer", id: "gap-experience-direction", answer: "<D2 的 title>", reason: "用户委托，采用推荐方向 D2" }
  ]
}
```
这里 delegate 不带 `proposal_id`，CLI 会取第 1 轮推荐的 D2。它记下已确认的 `experience-direction-D2`：`origin: model-proposal`，`auto_decided: true`，`confirmation.delegated: true`。

**理由：** 当前已有一轮建议，而且是上一轮展示给用户、用户已经读过的。用户在本轮亲口要求替他定。`user_reference` 必须填本轮用户的发言，不能填推荐本身，也不能填上一轮展示方向的那一轮。

**给用户的答复：** 「好，按推荐的 D2《…》来。这是替你做的决定，会标记为委托，跑完时会通过 `--delegations` 列给你看。以后想换，随时说。」

### 情形乙（还没有任何 propose，用户开场说「体验方向你定，别问我」）

**实际调用：**
```
product_intent.py . < {
  operation: "propose",
  proposals: [D1, D2, D3],
  recommended_id: "D2",
  rationale: "<用用户自己的话说明为什么推荐>"
}
```
每条方向都写满 `id/title/who/circumstance/core_loop_feel/first_minute/return_reason/goal/anti_goals/tradeoffs/scope/business_rules/acceptance/comparable{product,approach}`，不带 `origin/status/recommended` 这类权限字段。本轮**不调用 decide，也不 delegate**。用纯文本列出三条方向并点明推荐 D2，本轮到此结束，这个话题保持待定。

**理由：** 原文写道：「Without a current proposal round both are refused, and a round opened in that same turn is not yet a current round」，以及「`propose` and then `delegate` in one turn confirms a direction the user never saw」。Codex 适配器也写明：「'decide it for me' said before any round exists is answered by opening one, not by closing it」。

**给用户的答复：** 「可以替你定。不过得先有写好的方向，才谈得上替你选。下面是三个方向，我推荐 D2，理由是……你回一句『就按推荐』，我就按委托记下，跑完时会告诉你这是我替你定的。」

### Codex 的 assume-and-declare 约定

**能做的：**
- 在纯文本里声明推荐哪条、理由是什么。
- 声明其它非权限性质的技术假设。

**不能做的：**
- 原文：「the Codex assume-and-declare convention cannot produce a `select` or a `delegate`. A recommendation, a displayed default and silence are not actions」。
- 所以它不能把推荐当成用户已选，也不能在用户没回应时把方向记成已确认。没人回应的一轮始终只是建议。

## E3c（claude 适配）

**本轮实际动作**

1. 不调用 `decide`，也就是不写 `select` 或 `delegate`。原因是「行，继续吧」只是让我往下走，没有选任何方向。
2. 伪调用 `product_intent.py . < {"operation":"resume"}`。它会返回待处理的话题 `topics`，其中 `experience-direction` 下挂着当前第 1 轮的 `proposals`，还有 `recommended_id:"D1"` 和 `rationale`。我用这些内容把三条方向重新摆给用户。
3. 不再 `propose` 开新一轮。第 1 轮用户还没回答，仍是当前轮，用户应该从这三条里选。
4. 不 `freeze`，不 `plan`。

**`experience-direction` 话题现在的状态**

仍然待定（pending）。D1 只是推荐，也是界面默认高亮的一项，但还只是提议，不是已确认的方向。`gap-experience-direction` 还没有答案，也没有生成 `experience-direction-D1` 这个已确认条目。

**能不能 freeze**

不能。理由有三条：

- `freeze` 的 `include` 只能放已确认的条目。现在没有已确认的体验方向。
- 如果把 `gap-experience-direction` 放进 `exclude`，协议只允许在「没人看的产品」上这样做。当前 `mode="mixed"`，这是会被人看到的 UI 产品，排除理由不成立。而且排除一个未回答的问题，也不能授权依赖它的工作。
- 如果我自己把「继续吧」当成 `delegate`，就是自作主张替用户做了决定。用户这一轮没有说「你替我定」。

**面向用户的答复**

> 数据库那边就按刚才说的办。现在回到还没定的一步：产品的体验方向。上一轮我写了三条方向，分别是 D1、D2、D3，每条都包括是给谁用、在什么场景下用、核心体验是什么感觉、用户为什么会回来，还有一个做同类事情的成熟产品作对照。我推荐 D1，理由是〔rationale〕。但推荐不算你的选择，界面上高亮的默认项也不算。
>
> 「继续吧」我不会当成选了 D1。请你直接回我下面三种之一：
> - 选 D1、D2 或 D3，也可以说想改哪里；
> - 说「你替我定」，我就采用 D1，把它标成替你做的决定，跑完时会明确告诉你；
> - 都不满意，说说原因，我重新写一轮方向。
>
> 方向定下来之前，我不会冻结范围，也不会生成执行计划。

**支持判断的关键原句**

- "recommendations, displayed defaults, omitted answers and silence are not actions; `select` and `delegate` are actions."
- "A recommendation is not an action. Only the user's own `select`, or a `delegate` they asked for in that turn, creates a confirmed experience direction; a displayed default nobody answered stays a proposal."
- "`delegate` … is legal only where the user said in that very turn to decide for them"
- "Never restore by relabeling old code or interpreting continue/accept as a product choice."
- "A product nobody looks at excludes `gap-experience-direction` at `freeze`"
- "Excluding a question cannot authorize work that depends on its unanswered choice."

## E5c（codex 适配）

**实际动作**

1. 写入 `bootstrap-profile.json`：
```json
"experience_priority": {"mode": "none", "reason": "纯 HTTP API 计费对账服务，没有终端用户界面，消费方是两个后端服务，运维只看日志和 Grafana。"}
```
工具链里的 React 和 Vite 不影响判断。

2. Step 2 第 9 项不加载。这四份文件都不强制加载：product-concept.md、consumer-maturity-patterns.md、journey-emotion-schema.md、app-design.md。`create` 没有对应的能力文件。按 `goals` 该加载的仍然照常加载，比如 implement、launch-prep、cross-phase-protocols。

3. 节点图不放体验设计节点，也不放 design 和 runtime 两个 experience-quality-critique 节点。`required_repair_loops` 不写体验回路。规划摘要里写明豁免原因：没有终端用户界面，没有东西可评。
   `user_steps` 保持 `["/cross-exam", "/product-review"]`。这个项目的类型不是 cli，也不是 library-sdk，不在豁免范围内。

4. 处理 freeze 这一批（伪调用）：
```
product_intent.py freeze → gap-experience-direction 映射为 exclude，
  reason: "无终端用户界面，没有人看这个产品"
product_intent.py plan → not_applicable: {experience: "无终端用户界面，没有人看这个产品"}
```
这样这个问题不会一直挂在待定里，也不会因为跳过而没有说明。

**面向用户的答复**

这个项目只提供 HTTP API，调用方是两个后端服务，没有终端用户界面。所以我把体验优先级定为 `none`：不提体验方向，不规划体验设计节点和体验质量门。"体验方向"这个问题已经在 freeze 里明确排除，并记下了原因。计划里也写了体验不适用及原因。

流水线跑完后，仍建议你依次执行 `/cross-exam` 和 `/product-review`。如果将来要给这个服务加管理后台，请重新运行 `/bootstrap` 改分类。

**依据原句**

- 「`none` = there is no end-user interface. Use `none` only when … the project is pure backend/API. Judge by who the product serves, not by the tech stack」
- Step 2 第 9 项：「when `task_route` is `new-product` … and `experience_priority.mode != none`, always load …」
- Must #9：「Where `experience_priority.mode` is `none` there is no gate to plan and no direction to confirm: the run excludes `gap-experience-direction` and states `not_applicable.experience` … `freeze` maps that gap question into `exclude`」
- suppress-rules：「`experience_priority.mode = none` | experience quality gate (Must #9) nodes | … the summary states the exemption」
- 「"Smallest" never means omitting experience design. On a … route whose `experience_priority.mode` is `consumer` or `mixed`」：这条只约束 consumer 和 mixed，不约束 none。

## E6c（claude 适配）

### 本轮动作（伪调用）

**1. 放两个创意质量评审节点**，两个都执行 `${CLAUDE_PLUGIN_ROOT}/skills/game-creative/40-qa/creative-quality-critique/SKILL.md`：
- `creative-critique-design`：`hard_blocked_by: ["game-design-finalize"]`。美术、音频、前端实现节点都 `hard_blocked_by` 它。
- `creative-critique-runtime`：`hard_blocked_by` 最后一个美术/UI/音频/前端 QA 节点，也就是视觉 QA 和运行时 smoke。
- 两个节点都不用 `experience-quality-critique`，那是非游戏产品用的。节点 id 里不出现 `cross-exam` 或 `product-review`。产物路径按该 skill 的 Output Contract 写，我不另起名字。

**2. 收尾节点的依赖**
- `concept-acceptance.hard_blocked_by: ["creative-critique-runtime", ...原有依赖]`
- `pipeline-closure-verify` 也 `hard_blocked_by` `creative-critique-runtime`。依据是 Must #9 对产品这样要求，并说明 Must #8 是同一条法则。

**3. `required_repair_loops` 每个评审声明一个循环**
```json
[{"qa_node_ids":["creative-critique-design"],
  "repair_node_id":"game-design-creative-repair",
  "closure_node_ids":["<首批美术/音频/前端实现节点>"],
  "max_attempts":3},
 {"qa_node_ids":["creative-critique-runtime"],
  "repair_node_id":"game-impl-creative-repair",
  "closure_node_ids":["concept-acceptance","pipeline-closure-verify"],
  "max_attempts":3}]
```
- 设计循环里，must-fix 交给出问题的那个设计 pack 的修复节点重跑。
- 运行时循环里，先修实现，再重跑受影响的视觉 QA 和 smoke，最后重跑 `creative-critique-runtime`。
- 修复预算用尽时按 Run Policy 处理，运行中不再问用户。

**4. 其余配套**
- workflow 写入 `"user_steps": ["/cross-exam", "/product-review"]`。
- `game-design-finalize` 的 exit_artifacts 包含 `.allforai/game-design/game-design-doc.json`，实现节点间接 `hard_blocked_by` 它。
- 规划后跑 `validate_bootstrap.py`，由 `validate_experience_gate_flow` 检查。

### 给用户的答复

创意质量评审放两个：一个在游戏设计定稿后、动手实现前，另一个在最后的视觉 QA 和 smoke 之后。`concept-acceptance` 和 `pipeline-closure-verify` 都要等第二个评审通过。两个评审各有一个修复循环，最多修 3 次。

评审报告里的 must-fix 清单只要不为空，评审节点就不算完成，收尾的覆盖检查也不会开始。评审负责判断质量并把问题分派去修；`concept-acceptance` 仍然只查概念里声明的行为有没有证据，不打分。跑完后，你接着输入 `/cross-exam` 和 `/product-review`。

### 依据原句

- Must #8："After `game-design-finalize`, and again after the last art/UI/audio/frontend QA … `concept-acceptance` is `hard_blocked_by` it; `must_fix_*` findings route to the owning pack's repair loop."
- Must #9："Item 8 states the same law for games"
- concept-acceptance："While that critique's `must_fix_*` list is non-empty the critique node is not complete, so this gate does not start."
- Must #2："max 3 attempts"

## E9c（pi 适配）

### 本轮动作（开第一轮提案）

还没有任何提案轮次，所以这一轮只开一轮提案，不记录任何决定。场景没给出已确认的 target-users 和 scenarios 的具体内容，下面用〈〉占位。实际填写时，每条都要按已确认的内容写完整。

```
product_intent.py . < {
 "operation":"propose",
 "proposals":[
  {"id":"exp-dir-a","title":"〈A〉","who":"…","circumstance":"〈含规模与频率〉",
   "core_loop_feel":"…","first_minute":"…","return_reason":"…","goal":"…",
   "anti_goals":[…],"tradeoffs":[…],"scope":[…],"business_rules":[…],
   "acceptance":["〈可观察的体验标准〉"],
   "comparable":{"product":"〈成熟产品〉","approach":"〈它实际怎么做〉"}},
  {"id":"exp-dir-b",…},{"id":"exp-dir-c",…}],
 "recommended_id":"exp-dir-a",
 "rationale":"〈用用户自己的话说明为什么推荐〉"}
```

发给用户的原文：

> 接下来定体验方向。下面三条是方向不同，不是同一个想法的大小档位：
> **A.〈标题〉（推荐）**：给〈谁〉，在〈什么情境、多频繁〉下用；核心循环的感觉是〈…〉；第一分钟〈…〉；回来的理由是〈…〉；参照〈产品〉，它〈做法〉；代价是〈…〉。
> **B.〈标题〉**：…
> **C.〈标题〉**：…
> 我推荐 A，因为〈理由〉。请选一条，也可以说要改哪里，或者让我来定。

这一轮到此结束，话题保持待定。

### 用户下一轮回「你定」

用户已经看过这一轮提案，而且是在这一轮明说让我来定，所以可以记 `delegate`：

```
product_intent.py . < {
 "operation":"decide","batch_id":"exp-direction-1","topic":"experience-direction",
 "user_reference":"〈用户那一轮的真实发言：「你定」〉",
 "actions":[
  {"operation":"delegate","reason":"用户说「你定」，委托我按推荐方向决定"},
  {"operation":"answer","id":"gap-experience-direction","answer":"〈A 的 title〉",
   "reason":"用户委托，采用推荐方向 A"}]}
```

- 这一步会生成一条已确认的 `experience-direction-exp-dir-a`，`origin: model-proposal`，`auto_decided: true`，`confirmation.delegated: true`。
- `delegate` 不带 `proposal_id`。
- 回复用户：「按你的委托选了 A。这个决定会标成替你定的，运行结束时会再列给你看。想换的话随时说。」

### 用户没回，或会话被打断

- 不记 `select`，也不记 `delegate`，什么都不写。
- 再进入时先调 `resume`，把当前这一轮的 `proposals` / `recommended_id` 原样再出示一遍，继续等用户答复。
- 这个话题待定期间，不 freeze 也不 plan 依赖它的工作。Pi 上也不能用 assume-and-declare 代替用户同意。

### 支持判断的关键原句

- 「a round opened in that same turn is not yet a current round … the turn that opens a round ends with the proposals presented and the topic pending」
- 「`delegate` … is legal only where the user said in that very turn to decide for them, and the batch `user_reference` must be that real user turn」
- 「must `answer` `gap-experience-direction` with the chosen direction's title」
- 「沉默、中断、没有回复都不是委托」
- 「assume-and-declare 产生不了 `select`，也产生不了 `delegate`」
- 「disclosed back to the user at run completion through `product_intent.py . --delegations`」
