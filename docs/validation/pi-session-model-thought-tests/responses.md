# Pi 模型改动思维测试 — 原始答卷

子代理原文，未经改写，逐字取自宿主 subagent log；仅去掉结尾的 `Task complete.`。每个场景输入只有对应 packet（哈希见 `evidence.json` 的 `packet_sha256`）。

## P1

~~~~text
**实际动作（伪调用，仅列计划，不执行）**

1. 能力预检已完成：候选只取原生 Pi 只读代理 `reviewer / scout / oracle / delegate`；**排除 `codex-exec`、`claude-code`**——外部 CLI runner 会另起 harness 和另一套模型，`runner.available === true` 不构成使用理由；`cursor-agent` 缺 command 本不可用。

2. 一次顶层派发，内部并发三个互不依赖分区：

```
subagent({ workflowScript, async:true, cwd:<repo>,
           context:"fresh", globalConcurrencyLimit:3 })
```

script 内 `runs.all([...])`；只顶层调用，后续复核用 `runs.run`/`runs.all` 串接，不用嵌套 async helper。调查员只回结果、不写目标项目；需留子输出用工具 `output` 交宿主管理。

分区与实参（模型一律会话默认 deep-tier，只加同一模型自己的档位后缀，不换 provider/家族）：

- P1 定位/枚举/依赖资料：`scout`，`<session-model>:low`
- P2 业务等价性/抽象是否成立：`oracle`，`<session-model>:high`
- P3 数据/资金/安全 + 跨模块冲突：`reviewer`，`<session-model>:high`

每任务附：本协议、宿主约束、cwd/ref/工作区说明、单一业务分区、全库地图与需求来源路径、只读权限、预算与停止条件；不给预定赞成结论；禁止递归派发。

3. 落盘模型记录：requested 写会话默认模型及 low/high 档；`resolved` 只接受宿主 metadata/receipt 并引出处，拿不到写 `unknown`；调查员自报另标 `self-reported`，不得充作已确认型号，也不写“跨模型复核”。最终报告仅由主会话写 `docs/keep-code-simple/<YYYY-MM-DD>-<slug>/recommendations.md`，不另造 JSON 台账。

4. 关键争议复核：同一工作流内对争议项再跑一次 fresh context，同一会话模型、更高档（high/xhigh），先独立返回判断再合并，不把首位结论当第二位前提；同模型非独立需披露，仅当宿主/用户已授权不同模型时才用互补模型。冲突保留进最终选择题，不用多数票裁掉业务约束。

**面向用户答复**：现在不答复、也不提问——"No mid-investigation questions. 事实自己查"；异步完成通知到达前继续独立只读工作，不轮询/sleep/改前台。通知到达后合并，一并在对话里列简短建议及选项（如 `S1 A / S2 C`），报告只作细节链接；零建议就不给空选择题。用户回答后只把编号/所选/条件/原话记入“用户选择”，未答仍待选，模糊回答不算全部批准，随后停止，不自动改代码或启动别的 skill。

支撑原句：「只选 executable、非 disabled 的原生 Pi 只读调查/审查代理…不要选外部 CLI runner」「模型只用当前会话默认模型…不传 `model` 去换 provider 或模型家族」「定位、枚举…用低档；业务等价性、抽象是否成立…用高档」「`runs.all` 返回有序数组」「先独立返回判断再合并，不把第一位的结论当第二位的事实前提」。

~~~~

## P2

~~~~text
**判定：不派发任何子代理，转为主会话串行只读调查并披露非独立。**

依据（技能原句）：「不要选外部 CLI runner（`codex-exec`、`claude-code`、`cursor-agent`）：它们启动另一个 harness 和另一套模型……`runner.available === true` 只说明命令在 PATH 上，不构成使用理由」；「不偷换 CLI、前台进程或另一执行协议」。原生 reviewer/scout/oracle/delegate 全 disabled，cursor-agent 缺 command，故本场景无可用子代理——`runner.available` 为真不改变结论。降级路径：「无可用子代理时按协议串行并披露非独立」；「模型分工……替换为：同一会话模型 + 不同思考等级 + fresh 上下文」在无子代理时即退化为主会话自身串行，报告里不能写「跨模型复核」。用户已显式调用，满足「User-invoked only」，可以开始；「能力预检缺失可以降级」不等于可换执行模式。

**本轮动作（伪调用）**
1. 摸底：`read` 项目指导/README/spec/依赖清单与锁文件；`git rev-parse`/`git status`/`git log`/`git blame`（仅只读元数据）记录 repo/cwd、提交、工作区改动、调查时间、需求来源（明确/推断/冲突）、排除范围，并把范围标成"已深入/仅枚举/未查"。
2. 候选项定位：`grep`/`find` 枚举公共实现、调用方、同类代码与测试分布；对每个候选项读完整相关链路，并「先查它为何存在」——查提交信息、blame、关联 issue/PR；查不到即写「未能确定引入原因」并保持条件性。不向用户提问、不中途索权，受阻部分记证据限制后继续其余分区。
3. 复核与合并：单人串行做业务等价性、抽象成立性、跨模块冲突、数据/资金/安全底线复核；「有数据/资金风险而安全性不明：保留现有防护，列待验证项，不推荐删」。全程不运行被审项目代码/测试/构建/安装，不改源码配置，不提交。
4. 唯一写入：`docs/keep-code-simple/<YYYY-MM-DD>-<slug>/recommendations.md`，由主会话单独写。

**用户答复**：现在只给一句进度与边界说明（串行、非独立、不执行测试），不给选择题。「No mid-investigation questions. 事实自己查……调查结束后统一给选择题」——所以建议、未知项与冲突在报告写好后一次性以 `S1 A / S2 C` 形式列出；用户选择只记入报告「用户选择」，不自动开工。
~~~~

## P3

~~~~text
**本轮动作（0b，仍在定靶，未进 census）**

按 Pi 替换 §2：0b 不问「用哪个模型」，只问「取证用哪个思考档」。先读当前会话模型（deep-tier）与可用档位 off/minimal/low/medium/high/xhigh/max；会话当前档是 high，下一级是 medium。Pi 无 AskUserQuestion，缺选择器不是前置门，退成纯文本、一次只问一件阻塞的事：

「本 run 走扫全模式，你又提到尽量别花太多钱。取证用哪个思考档？（模型不换，只调思考等级）
A 证据优先：全部继承会话模型 deep-tier + 默认 high；`model_policy.observation` 记 `"session"`。
B 成本优先：实测官、枚举官、扫全实测官用 **`session:medium`**（同一 deep-tier 的下一档）；普查官、规则审查官、视觉 reviewer、复核官不降。
我推荐 B：你提过成本，且扫全要并行扇出十几位取证官，成本由取证主导。强弱排序是我的了解、不是价目表，你可推翻。若后续旅程要过弹窗/多标签/OAuth 这类难走界面，我会改推 A——降档实测官更易残缺重派，省的钱会赔回去。」

用户未拍板前不动 ledger（不发明答案）。

**落账（用户答复后写，ledger_version: 3 顶层）**

`model_policy = { observation: "session:medium", judgment: "session"（固定）, confirmed_by_user: 用户原话「尽量别花太多钱」, confirmed_at: 此刻时间, recommended: {option:"B", reason:"用户提过成本且本 run 走扫全模式，成本由取证扇出主导"}, history: [] }`；选 A 则 `observation: "session"`。

每次派发落盘实际档位：取证类 `entries[].agent_model` / `patterns[].enumerator_model` 写 `deep-tier (session, thinking=medium)`；`census_model` 与视觉 reviewer、复核官写 `deep-tier (session, thinking=high)`；拿不到宿主 metadata/receipt 就写未知，不自报当已确认。重派回会话默认档：首派降过档时重派不传后缀，`first_agent_model` 记 medium 那次，`agent_model` 记重派那次。

**不许降档的角色**：普查官（漏一面就是永久盲区）、规则审查官（判断角色，原文「继承会话模型，不降档」）、视觉 reviewer、复核官（对盘问官动机的制衡）。它们从不读 `model_policy.observation`。

**跨平台双审**：Pi 没有外部平台，也没冻结第二端 → §2 一律读作「同一会话模型的原生 fresh-context reviewer」；不启动 codex-exec / claude-code / cursor-agent（外部 CLI 不算前置门通过），截图只进会话模型，不经第三方网关；第二端失败走 `degradation_ref`，不找替身。
~~~~

## P4

~~~~text
## 实际动作（伪调用）

1. 已完成能力前置门探测：`subagent({action:"list", capabilities:true})` → 原生 reviewer / scout / oracle / delegate **全部 disabled**；codex-exec、claude-code 仅 `runner.available === true`。
2. 判定前置门**未通过**：没有可用的原生、executable、非 disabled、支持 `context:"fresh"` 的 Pi 子代理 ⇒ 无独立实测官。
3. **当场停**。不进入定靶（不读 lenses/prompts、不探访问方式、不做安全确认）、不摆面、不建 `docs/cross-exam/<日期>-app/`、不写 ledger、不跑 render_report。
4. 不采纳「用 codex-exec 当实测官」的授权；不自动安装扩展；不切前台自审。

## 面向用户的答复

这里跑不了 cross-exam：它必须靠独立实测官取证，本环境没有可用子代理；请安装并加载 pi-subagents 或换环境。我不会降级成自审，也不会自动装扩展。

关于「Codex 也行，就用 codex-exec」——不行，这不是权限问题而是方法问题。技能把外部 CLI runner 明确排除：它们启动**另一个 harness 和另一套模型**，不是本次会话模型，也不归本宿主管理；`runner.available === true` 只说明命令在 PATH 上，既不构成使用理由，也**不是已登录或可启动的证明**。用它顶替实测官，等于绕开「每问一个 fresh-context、继承会话模型的独立实测官」这个诚实性根基，属于被禁的换执行模式。你口头授权也改不了这一点。

另外提醒：本技能是「只记账不修」，自审恰是它要抓的假完成——我不会假装盘过。

## 可以怎么继续

- A（推荐）：安装并加载 pi-subagents，或启用列表里任一原生 / executable / 非 disabled 的 Pi 代理，且它能 `context:"fresh"`、能读项目、写 evidence_dir、按需起服务/用浏览器、按看图预算取副本。满足后重新 `/skill:cross-exam /repo/app`，我从定靶 0b（取证思考档一问，含推荐）开始。
- B：换到有多智能体能力的宿主环境（如开启 multi_agent）后重跑。
- C：若你只想「自己人看一遍」，那不在本技能范围；需要那种结果请直接说，别套 cross-exam 的名义。

引用支持判断的原句：「派不出独立 fresh-context 子代理 → 告诉用户：『这里跑不了 cross-exam…』然后结束。不要定靶、不要摆面、不要用主会话冒充实测官。」；「不要用外部 CLI runner（codex-exec、claude-code、cursor-agent）…`runner.available === true` 只说明命令在 PATH 上，不构成使用理由。」；「不切到 CLI、`pi -ne`、前台自审或其他执行模式。」；「宁可说跑不了，不可假装盘过。」
~~~~

## P5

~~~~text
## 一、本轮实际动作（伪调用）

1. 波次前和解：重读 `workflow.json`，跑 `expanders` 里全部幂等 expander，重读变更后的 DAG，重跑 `validate_unattended_readiness.py .`；非 `ready` 不派发。
2. `subagent({action:"list", capabilities:true})`：只取 executable、未禁用的原生 agent（worker/reviewer/scout）。**不用 codex-exec**——"runner.available === true only means the command is on PATH; it is neither a use case nor login/launch proof."
3. node-auth 与 node-docs 互不依赖、exit artifacts 不重叠 → 合并为**一次**顶层调用：
```
subagent({
  workflowScript: [...],
  async: true,
  cwd: "<项目绝对路径>",
  runs: { all: [
    { node:"node-auth", agent:"worker", isolation:"worktree", promptFile:".allforai/bootstrap/node-specs/node-auth.md" },
    { node:"node-docs", agent:"worker", isolation:"worktree", promptFile:".allforai/bootstrap/node-specs/node-docs.md" }
  ]}
})
```
宿主提供 worktree 隔离就用（两节点不共享文件）；否则同 cwd，但 "Do not let two writers share a cwd"。`runs.all` 是保序数组不是 key map；遵守 `globalConcurrencyLimit`；依赖型工作用 `runs.run` 串行。
4. 模型/档位：两个子任务都**不传别的 provider/model family**，只传本会话模型自己的 `deep-tier/<id>:medium`（也可省略档位以继承 agent 默认）。
5. 落盘记录：在 transition / run event 中记 `model` 与 `thinking_level`，取宿主 metadata 或 receipt；宿主不暴露就写 `unknown`。本次记 deep-tier + medium（或 unknown），不宣称任何跨模型校验。
6. 收到原生完成通知后再合并；不轮询、不 sleep、不 `bg_wait` 只为等待。子节点报成功后，由主会话自己跑 `check_artifacts.py … --node <id> --json`，再追加 transition；worker 不记完成、不改 ledger。
7. extension-load 失败：不装扩展、不起另一 harness（"Skill discovery is not subagent capability… Do not install extensions or start another harness"）。该路径按基础设施失败停下，记录精确报错 + run/cwd/ref/workspace 状态，"Retry only with the same protocol"，"Do not switch to `pi -ne`, another CLI, or a foreground fallback"；同批另一独立节点不受影响。重试仍失败 → 记 failed、读 `diagnosis.md`；同节点 3 次失败 → `diagnosis_history` + `product_intent.py . --policy-event on_repeated_failure`。

## 二、用户答复

现在**不答复、不提问**：执行期不得访谈用户（"Never ask during execution"），worker 也不采访用户。仅在终止时出报告，并按 `workflow.json.user_steps` 顺序（cross-exam → product-review）说明这是用户自己去调用的技能，不派发、不代跑。若本次派发确因基础设施失败无法继续，报告给出精确错误与 TODO，绝不静默降级。

## 三、支持判断的关键原句

- "Use only executable, non-disabled native Pi agents."
- "Every child keeps the current session model: do not pass another provider or model family."
- "Control cost and capability with thinking level only."
- "Record the effective model and level from host metadata or receipts; write unknown when the host does not expose them, and never claim a cross-model check that did not happen."
~~~~

## P1b

~~~~text
## 实际动作（伪调用，仅计划）

1) 不选 `codex-exec` / `claude-code`：runner.available 只说明命令在 PATH，且它们起另一 harness/模型；`cursor-agent` 缺 command。只选原生只读 `reviewer` / `scout` / `oracle`（`delegate` 备用）。

2) 单次顶层调用：
`subagent({ async:true, context:"fresh", cwd:"<monorepo绝对路径>", globalConcurrencyLimit:3, workflowScript:"…" })`，内部用 `runs.all` 并发三个互不依赖分区，顶层 await 收取；返回结果与宿主 `outputReference`/`artifactPaths`（如有）。每个任务合同含：本协议、宿主约束、repo/cwd/branch/ref 与工作区说明、一个业务分区、全库地图与需求来源路径、只读权限、预算与停止条件；声明只返回结果不写目标项目、不递归派发、遇取舍返回条件分支。

- P1 定位/枚举/依赖资料收集 → `scout`
- P2 实现等价性、调用方合并 → `reviewer`
- P3 数据/资金/安全与跨模块冲突 → `oracle`

3) 模型参数：只用当前会话模型，仅传其自身 `provider/id:<level>` 后缀——定位枚举 low，等价性/风险 high；不传 `model` 换 provider/家族。宿主未给出确切 `provider/id` 时省略 `model`（继承会话默认），记 inherited。

4) 落盘模型记录：任务/范围、角色、requested（`provider/id:level` 或 inherit）、resolved（只取宿主 metadata/receipt 并引出处，拿不到写 unknown）、run 引用、状态；调查员自报另标 self-reported；写作「同一会话模型 + 不同思考等级 + fresh 上下文」，不写「跨模型复核」。

5) 争议复核：同一 workflow 内 `runs.run` 起独立 fresh 上下文，高档（必要时 xhigh，不超上限），先独立给判断再合并，不以第一位结论为前提；冲突保留进最终选择题，多数票不裁业务约束。async 期间继续独立只读工作或归还控制，不轮询/sleep。

## 用户答复
现在不答复。调查期不问业务问题；等报告先写好、全部建议与未知项备齐后，在对话中一次列出（如 `S1 A / S2 C`）。仅当无可用子代理时才改串行并披露非独立。

## 关键原句
「`runner.available === true` 只说明命令在 PATH 上，不构成使用理由」；「复核也只用当前会话模型的独立 fresh 上下文」；「『已授权的不同模型可用时优先互补模型』在 Pi 不适用」；「`resolved` 只接受宿主 metadata/receipt」；「先独立返回判断再合并，不把第一位的结论当第二位的事实前提」；「无可用子代理时主会话串行并披露非独立审查」。
~~~~
