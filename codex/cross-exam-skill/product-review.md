---
name: product-review
description: Product-thinking critique of a shipped or running product. Names missing jobs, broken journeys, commercial UI/interaction gaps, and borrowable competitor positioning. Advice only — never edits product code. Explicitly invoked by naming product-review. Same package as cross-exam; different protocol. Asks "is it good for the user's jobs"; cross-exam asks "is it really done" and usually comes first.
---

# product-review — 产品思维审视

> Invoked only when the user names product-review. The agent must not start it on its own. No target given means start at Intake. Follow this skill from Intake.

This file is the whole protocol. The lenses below are compressed from meta-skill's `product-design-theory.md` and `consumer-maturity-patterns.md`; nothing here requires those files to be installed.

Not cross-exam. Do not follow `SKILL.md` below the package router, do not write a completion ledger, do not use done/gap/drift/unprovable. If the user has not yet verified the delivery is complete, say once that cross-exam does that and continue with this review.

## Invariants

- **Interactive only.** Invoked unattended or from an autonomous pipeline: refuse and stop.
- **Advice only.** Do not edit the product's source. The only writes are under `docs/product-review/<date>-<slug>/`.
- **意见不是决定。** 建议「移除 / 暂缓 / 不该做」都只是意见：功能只有「做」和「不做」，做不做由用户在范围确认时定（管线里已经没有替用户裁剪的节点了）。本审查不执行移除，也不产出范围清单。
- **No `.allforai/`.** Do not read or write that tree. Do not call meta-skill capabilities. `docs/cross-exam/` and `docs/experience-review/` are readable input.
- **No 37 interaction types. No token/pixel spec audit.** Commercial UI/interaction is in scope; design-system compliance is not.
- **不做第二遍完成度审计。** 「在不在」「走不走得完」是判断前提，不是本审查的产出：有完成度报告就按它的 `J`/`G` 判定采信，不重走旅程；没有报告就记成未验收前提，并说一次 cross-exam 是判这件事的入口。本审查产出的是「该不该有」「商业级够不够」和同一份工作上的竞品对照。
- **Do not start grilling.** After the report, tell the user they may `$grill-me` / grilling on that file. Wait.

## Guiding thought

Product-concept 用第一性原理是为了**发明**。这边是**审视已经做出来的东西**，对等思想不是再贴一遍第一性原理，而是：

**进展，不是功能。** 不可再拆的单位是「用户点名的那份工作，有没有让人做成一件可观察的事」。功能在不在、像不像某品类、竞品有没有按钮，都不是起点。

判一条意见之前先能指出：谁、在什么情景、想做成哪件事、你在产品里看到了什么进展或卡死。指不出观察，就只是口味，不要写入报告。

「这类产品都有 X」是惯例，不是缺口。竞品只用来对照**同一份工作**上别人如何让进展发生（ERRC 当比较，不当需求）。怎么打开这个产品由你看完再定，不要带品类检查表。

（思想来源：principled critique — 先问挑战/为谁/何以算成；Cagan/Torres — outcome over output；Ulwick — progress in a circumstance。Nielsen 启发式不是主思想。）

## Questions that apply the thought

For each **job in scope**，1 和 2 是前提，3 和 4 是本审查要回答的：

1. **在不在**（前提）— 有没有入口去推进这件工作？
2. **走不走得完**（前提）— 进展能不能做完，失败或反向有没有路？
3. **该不该有** — 这是核心进展还是装饰？
4. **商业级够不够** — 进展能完成的前提下，陌生人会不会把它当成能卖的产品？

前提有 `J` 判定覆盖就直接采信，不重走；没有覆盖就按看到的写一行观察并标未验收。只有在没有 `J` 覆盖、产品对这份工作连入口或终态都没有时，`missing_job` / `broken_path` 才是本审查的发现——那正是对着基线的完成度审计看不见的情况：产品从没承诺过这份工作。

第 3 问会得出「这东西不推进任何一份点名的工作」，按 `decoration` 写出来，不再默默丢掉。但装饰永远是**相对本次点名的工作集**而言：它可能在服务用户这次没点名的工作，所以推荐移除之前先查它为何存在（提交信息、blame、关联 issue、spec），查不到就只能 `defer`。

Default extra pass: search live competitors only for how they create the same progress. Unmapped ideas go under "Out of scope".

## Lenses (镜头，不是清单)

原则可以否决镜头之外的情况，也可以否决镜头本身。镜头只回答"往哪看"。镜头没照到东西，不是缺口；照到了东西，仍要过"谁、情景、事、观察"四关才能写。

| Question | Where to look | Lineage |
|---|---|---|
| 2 走不走得完（前提，`J` 覆盖时不重走） | 每条路有没有终态；失败有没有恢复路；空态、加载、错误态是不是死路；反向操作（撤销、退出、删除）在不在 | feature-gap journey dimensions |
| 3 该不该有 | Kano：must-be 缺了是 `missing_job`、one-dimensional 弱是 `broken_path`（两者都只在无 `J` 覆盖时成立）或 `ui_friction`；attractive 缺了只在竞品对同一份工作做到时才是 `borrow_*`；indifferent 是装饰，按 `decoration` 写，代价写不出来就不是发现 | product-concept Kano anchor |
| 4 商业级够不够 | 首次进入有没有被引导；主线是不是功能菜单；核心动作有没有过程反馈；完成后有没有下一步；空态错误态是不是同一套；有没有回来的理由。反面：压缩版后台、概念 demo、功能清单式设计 | consumer-maturity-patterns |
| 4 商业级够不够 · 受众泄漏 | 最终用户界面里有没有部署方/开发者才该碰的配置（服务地址、访问凭证、密钥、模型选择、环境名、功能开关）。每个设置项只有一个受众：`end-user` / `operator` / `developer`；非 `end-user` 项出现在最终用户可达的界面就是观察，归 `不够商业级`。例外：用户点名的工作本身就是自行接入服务器（自托管类产品） | meta-skill defensive-patterns Pattern J |
| naming `ui_friction` / `interaction_gap` | 用 Nielsen 十条给**已观察到**的摩擦命名，让 grill 时有共同语言。不用它扫产品 | experience-map Nielsen anchor |

第 4 问的五个镜头与运行内体验质量门（meta-skill `experience-quality-critique`）的五个维度同名同义：引导 = `onboarding` · 过程反馈 = `process_feedback` · 下一步 = `next_step` · 状态一致 = `state_consistency` · 回来理由 = `return_reason`。运行内放行与事后审视用的是同一把尺；该门另有的 `mainline`、`direction_fidelity`、`audience_leak` 不是这五格之一。

## 0. Intake

Completion: target named; every job in scope written as a triple and read back; run directory decided; user still present.

1. Confirm a human is in the session.
2. Name the product and how to inspect it (repo, running local app, public site). Production write-actions are forbidden; read-only public marketing pages are allowed.
3. Jobs. The user names jobs; you rewrite each into a **triple** and read it back for confirmation:
   `who` / `in what circumstance` / `what observable progress`.
   A wish that stays a wish after one rewrite round ("make search better" with no who or circumstance) is not a job yet. Say which part is missing, and if you have already looked at the product, propose the triple you can see it implying ("as a returning shopper, on the results page, find the item I bought last month") for the user to confirm or reject. A confirmed proposal is a job; a rejected or unconfirmed one is left out. You never enter a job into scope on your own authority. No jobs after that → stop.
4. Run directory `docs/product-review/<YYYY-MM-DD>-<slug>/`. If `recommendations.md` already exists there, ask once: continue (keep ids, append) or new run (suffix the slug).

## 1. Facts

Completion: evidence limits recorded; prior evidence folded in; 每条工作的前提有来源（`J` 号或本次观察+未验收）；每条工作在第 4 问的五个镜头（引导 / 过程反馈 / 下一步 / 状态一致 / 回来理由）上各写一格：`有 <观察>` | `缺 <观察>` | `未查`，`J done` 只免掉第 1、2 问，不免这一行；写成 `缺` 的每一格，要么对应一条 `R`，要么在同一格用一句话说明为何不立项; 3/4 有证据; competitor notes only for jobs in scope.

**Evidence limits, before opening anything.** Record three facts: can the product run here; is a browser or screenshot tool available; is WebSearch available. These become the report's `Evidence limits` line. Without a browser, every `ui_friction` / `interaction_gap` item carries `evidence: code-only` and says so. Never describe an inspection method you did not use.

**Prior evidence.** If `docs/cross-exam/*/completion-report.md` exists, read the newest one. Its gap list and its 旅程完成度 section are prior evidence: for each gap (`G` id) or journey verdict (`J` id) that blocks a job in scope, list it on the `Prior evidence` line with that job. A journey that cross-exam walked through (`done`) is evidence for 在不在 and 走不走得完 on the matching job; a journey `gap` with its `stuck_kind` is the observation. 过没过期要核，不凭印象：取表头「被评构建：」里的 commit（`-` 之前那段），跑 `git log --oneline <commit>..HEAD -- . ':!docs'` 和 `git status --short -- . ':!docs'`；有输出就是产品在那之后动过，也不在这里重走旅程补判：记下被评构建与这两条命令的输出摘要，把受影响工作的前提标成过期，并说一次 cross-exam 是重新判它的入口。这里的观察永不覆盖那份报告的判定。 A known gap or blocked journey never becomes an `R` item; items that wait on it write its id in `depends_on` (`G1`, `J1`). 表头写「被评构建：未记录」、没有这一行（旧报告）、或这两条命令跑不了（不是 git 仓库、commit 不在本仓库）→ 在 `Prior evidence` 行写 `新鲜度未核：<原因>`，照常引用它的 `G` / `J` 号，但不把它当成对当前产品的观察，也不写成「未过期」。Absent → write `Prior evidence: none`.

**Prior evidence — runtime experience review.** If `docs/experience-review/runtime.md` exists, read it (该路径每次评审覆盖写，存在的那份即最新一份). Do not read `design.md` — 那份判的是设计产物，不是运行中的产品。Its per-lens observation lines are already evidence for question 4: 对应工作的 `商业级` 行里，被它覆盖的格直接写 `有|缺 <它的观察>（runtime review <评审日期>）`，不重新检查；它没覆盖的镜头、没覆盖的工作照常自己看。Its must-fix list is the list of items still open: for each one that blocks a job in scope, list it on the `Prior evidence` line by the id it carries in that file; an item that waits on it writes the same id in `depends_on`. 已知的 must-fix 不再占 `R` 号。过期纪律与 cross-exam 报告相同，同样要核：用该文件的「被评提交」跑同样两条命令；有输出就记下评审日期、被评提交与输出摘要，把受影响的格标成过期，不在这里重判；「被评提交」是 `uncommitted` / `no-git` 或命令跑不了 → 写 `新鲜度未核：<原因>`，不写成未过期；说一次重跑该评审属于产品自己的 meta-skill 运行。这里的观察永不覆盖那份结论。That file's own evidence limits fold into this report's `Evidence limits` consequence clause. Absent → that source line is `none`.

Find facts yourself (repo, running UI, WebSearch). Do not ask the user for anything look-up-able.

After you see the product, decide what to open and what to compare. Write down that inspection plan in one short paragraph in the report so the review is auditable — not a hidden rubric.

**Competitor sources.** Search only for how a competitor creates the same progress. Grade every source:

| Grade | Source |
|---|---|
| P1 | official docs, specs, standards |
| P2 | research bodies, analyst reports |
| P3 | first-party product-team writing, the product itself |
| P4 | community posts, social media |

P4 supports no item on its own. Record the grade and an adopt/reject reason per competitor note.

## 2. Recommendations

Completion: `recommendations.md` written in the template below. Every item is one grill-able decision.

Each item:

- `id` stable (`R1`…)
- `job` one triple from Jobs in scope, by its label
- `kind`: `missing_job` | `broken_path` | `ui_friction` | `interaction_gap` | `decoration` | `borrow_positioning` | `borrow_feature`；`missing_job` / `broken_path` 只用于没有 `J` 判定覆盖的工作，被覆盖的留在 Prior evidence，不占 `R` 号
- `claim`: `进展受阻` | `不够商业级` —— 这条建议主张的是哪一件事；`decoration` 与 `borrow_*` 不填
- `depends_on` other `R` ids, cross-exam `G` or `J` ids, experience-review must-fix ids, or empty
- `recommend`: `adopt` | `defer` for kinds observed in the product; `adopt` | `defer` | `reject` for `borrow_*`。`decoration` 的 `adopt` 含义是**移除**它；只有当本次点名的工作集覆盖了产品的主要用途、且已查明它为何存在时才可 `adopt`，否则 `defer` 并写明它可能服务未点名的工作

- `reject` / `defer` / `decoration` 的 `adopt`（移除）都是写给用户看的意见：报告要写清「为什么不值得」，但不得写成「已砍掉」或「必须砍」。
- `tradeoff` one sentence
- `evidence` paths, URLs, or UI observations — not vibes; `code-only` when no browser

Competitor ideas that do not map to a job in scope go to Out of scope, never into the tree.

**Self-check before writing.** An item that fails any line is deleted, not reworded:

- `job` is one of the triples in scope
- `evidence` is an observation (path, URL, screen state, code line), not "this category has X"
- `evidence` provenance matches Evidence limits
- `claim: 进展受阻` → `evidence` 显示这份工作的进展被卡住或变难；"works without it" means delete
- `claim: 不够商业级` → `evidence` 指出让陌生人不敢把它当正经产品的**具体那一点**（无引导、核心动作没有过程反馈、做完之后没有去处、同类状态两套说法、最终用户设置页里要填服务地址或访问凭证…）；不要求它妨碍把事做完，但说不出具体是哪一点、只剩「体验不好」就删
- `reject` appears only on `borrow_positioning` / `borrow_feature`; a product-observed kind you would reject was not friction — delete
- the item is not a cross-exam gap or an experience-review must-fix restated
- `missing_job` / `broken_path` 不落在已被 `J` 判定覆盖的工作上
- `decoration` 的 evidence 显示它不推进**任何**一份 in-scope 工作，`tradeoff` 写出它在占用的注意力或维护成本；两者缺一就删
- `decoration` 推荐 `adopt` 时，报告里有它为何存在的出处；只查到「找不到原因」就降为 `defer`
- no item rests on a P4 source alone

## 3. Write and stop

Write `docs/product-review/<run>/recommendations.md`:

```markdown
# Product review — <product>

## Jobs in scope
- JOB1 — who: … / circumstance: … / progress: …
  - 前提: J2 (done) | 本次观察（未验收） · <one clause>
  - 商业级: 引导 <有|缺|未查 · 观察 · 缺时: R号或不立项原因> · 过程反馈 <…> · 下一步 <…> · 状态一致 <…> · 回来理由 <…>

## Evidence limits
runs here: yes|no · browser: yes|no · WebSearch: yes|no · consequence: <one clause>

## Prior evidence
docs/cross-exam/<run>/completion-report.md — G1 blocks JOB1; J2 (gap, no_feedback) blocks JOB1; G2, G3 no job in scope | none
docs/experience-review/runtime.md (<review date>, <reviewed commit>) — <must-fix id> (next_step) blocks JOB1; lens cells adopted: JOB1 引导, 过程反馈 | none

## Inspection plan
<one short paragraph: what you chose to open on THIS product and why>

## Decision tree

### R1 — <title>
- job: JOB1
- kind:
- claim: 进展受阻 | 不够商业级
- depends_on:
- recommend: adopt | defer | reject
- tradeoff:
- evidence:

<!-- when no item survives the self-check, the tree is exactly: -->
No item survived the self-check.
- JOB1 · 在不在: <observation> · 走不走得完: <observation> · 该不该有: <observation> · 商业级: <observation>

## Competitors (jobs in scope only)
- <name> [P1..P4]: positioning. how it makes the same progress. borrow or reject, why.

## Out of scope
- seen elsewhere, not a job in scope
```

Then stop. One line: this file is upstream for `$grill-me`. Do not grill. Do not implement.
