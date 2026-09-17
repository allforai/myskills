# product-review — 思维测试记录

日期：2026-09-15。结论：**3 个场景按预先写下的判据全部通过；同一轮测出一处规则冲突，属于缩范围那一步的漏改，已修，修复未在本轮受测。** 这是 product-review 的第一份验证记录——在此之前它没有任何验证。

受测版本为 commit `3a7ff89a`（缩范围 + `decoration` 之后、`claim` 拆分之前）。

## 方法与证据

- 每个场景一个独立 fresh-context 子任务，三个并发；受试者只收到对应平台的协议全文与该场景，判据留在评估端。
- 宿主为 Claude Code 的 Agent 工具。requested `opus`，resolved `claude-opus-5`，来自宿主子任务轨迹的 assistant metadata，不是受试者自报。
- 隔离：协议与场景拼成单个 packet 文件放在会话 scratchpad，受试者读该文件而不是把全文内联进提示——这样协议一字不差，但 cwd 是实现仓库，所以隔离靠轨迹核对：主会话提取 tool_use 事件，三个子任务各只有一次 Read（packet 文件），与自报一致，没有读取仓库其它文件或搜索。
- 场景与判据：[thought-tests.json](../../fixtures/product-review/thought-tests.json)；输入包装：[subject-prompt.md](../../fixtures/product-review/subject-prompt.md)。
- 受试者没有真实产品可看，动作写成伪调用；本轮没有任何产品被运行或修改。

## 场景判定

| 场景 | 受测规则 | 实际回答 | 判定 |
|---|---|---|---|
| P01 / claude：旅程已判 done，但产品是概念 demo 级 | 前提采信不重走；`J` 覆盖下不得用 missing_job/broken_path；第 4 问仍要有产出 | 采信 J1(done) 未重走，只答第 3/4 问，出四条（20 秒静默、首屏 14 项菜单无引导、完成后无下一步、空错态两套样式），全部标 `code-only` | 通过 |
| P02 / claude：一份工作无旅程覆盖 + 报告后代码已变 | 无覆盖时 missing_job 成立；被覆盖的留在 Prior evidence；不自行重走 | JOB1 出 missing_job；JOB2 的 J1(gap) 只进 Prior evidence 不占 `R` 号；只读 git log 仅用于记漂移，前提标过期并指回 cross-exam | 通过 |
| P03 / codex：装饰页，且查不到它为何存在 | 按 `decoration` 写；两个前置条件不成立时只能 defer；成本必须写出 | 写成 decoration + defer，指出两条前置条件各自独立不成立，`tradeoff` 写了 900 行维护面与每次进首页的聚合请求，并写明它可能服务未点名的工作 | 通过 |

判据之外做对的两处，都在**收敛**方向：P01 拒绝把另外 13 个菜单项写成 `decoration`（工作集未覆盖产品主要用途、未查明为何存在）；P03 拒绝顺手加一条 `ui_friction`，理由是「凭『应该会变慢』写条目过不了自查」。新加的 `decoration` 约束第一次运行就在挡住滥用，而不是制造条目。

## 测出的规则冲突

自检规则原文：`evidence` 要显示这份工作的进展被卡住或降级，「没有它也能用」就删。

缩范围之后，第 4 问「商业级够不够」的产出恰恰全是「没有它也能把事做完」的东西——无引导、核心动作没有过程反馈、做完之后没有去处、同类状态两套说法。按字面，这个 skill 现在的核心产出全部该删。P01 就撞上了：R3 自述「工作本身仍能完成」却仍被保留，R4 自评「四条里最弱」。

成因不是这句话写错，而是缩范围那一步只改了「产出什么」，没同步改「怎么筛掉」。修法是新增 `claim`（`进展受阻` | `不够商业级`），删除规则按 claim 分两支：进展类照旧要证明进展被卡或变难；商业级类要指出让陌生人不敢当成正经产品的**具体那一点**，不要求它妨碍把事做完，但说不出具体哪一点、只剩「体验不好」仍然删。

**这处修复没有在本轮受测。** 三份答卷对的是 `3a7ff89a`；修复后的定向回归见下节。

## 第二轮：claim 拆分后的定向回归

日期：2026-09-15，受测版本 `d1abe3f3`。结论：**三个场景全部通过；被修的那处不再靠感觉绕，新规则也没有变成后门。**

| 场景 | 受测规则 | 实际回答 | 判定 |
|---|---|---|---|
| C01 / claude：与 P01 同一场景重跑 | 第 4 问的产出不再被「没有它也能用」判死 | 四条全部 `claim: 不够商业级`、全部 `adopt`，各自指出具体那一点；不再出现「工作本身仍能完成」这种自相矛盾措辞，也没有自评最弱的条目 | 通过 |
| C02 / claude：四条候选逐条去留 | 新规则会不会变成什么都能写 | (a)「观感不精致」删除且不改写；(b) 三层菜单 `claim: 进展受阻`（因 J1 覆盖用 `ui_friction` 而非 `broken_path`）；(c) `claim: 不够商业级` 并给出具体那一点；(d) 惯例不是缺口，删除，且拒绝塞进 Out of scope | 通过 |
| C03 / codex：调查员把推测标成了进展受阻 | 进展这一支能否被推测混过、会不会改标保命 | 驳回该 claim，明说以 `进展受阻` 提交必须删除而不是改写措辞；没有改标成不够商业级；还拒绝降级成 `ui_friction` 充数；改按 `decoration` + `defer`，claim 留空，并说明升级需要什么证据 | 通过 |

C01 与 P01 的对比就是这次修复的全部意义：同一个场景、同一批观察，之前是「留下条目但自陈工作仍能完成」，现在是四条各自声明主张并各自证明。C03 额外堵住了一条我判据里没写的退路（换 kind 保留同一条无观察的推理）。

一处待观察，不是 claim 规则的问题：`ui_friction` 与 `interaction_gap` 的边界模糊，同类条目在 C01/C02 里被分到不同 kind。按镜头表原意，Nielsen 只用于给已观察到的摩擦命名，所以不影响去留判断。

[第二轮原始答卷](product-review-thought-tests/responses-c01-c03.md) · [第二轮证据](product-review-thought-tests/evidence-c01-c03.json)

## 尚未验证

- 每个场景各一次运行、同一模型，不是重复采样或跨模型复核。
- 仍是模拟决策，不是原生宿主验收：P03 的 codex 适配只作为输入文本，没有启动 Codex；Claude 侧也没有真实 `/product-review` 会话。
- 竞品搜索与来源分级、以及人对报告开 grilling 之后的流程，都未测（`claim` 拆分本身已由第二轮覆盖）。
- 没有在真实产品上跑过，报告质量与噪声率未知。

[原始答卷](product-review-thought-tests/responses.md) · [证据](product-review-thought-tests/evidence.json)

后续：发现能力（受试者自己在埋了缺陷的代码库上找问题）见 [product-review-discovery-tests.md](product-review-discovery-tests.md)（2026-09-17）。
