# M2 experience-intent — 体验意图与设计授权

总览：`2026-09-18-product-experience-overhaul-overview.md`。依赖 M1 的 `data:experiencePriority`。
已批准决定 D1：**先提案，可委托**。

## 问题

`knowledge/product-intent-confirmation.md` 把模型限制成记录员：

- 话题只有 `target-users / scenarios / core-problem / value-proposition / business-loop / tradeoffs`
  （`scripts/orchestrator/product_intent.py:371`），没有体验维度。
- `:21-22` "recommendations, displayed defaults, omitted answers and silence are not actions"，
  `decide/add` 强制 `origin="user-request"`（`product_intent.py:1229`）。模型提出的任何设计都没有
  合法的落点，只能以"未批准的建议"身份留在散文里，永远进不了冻结范围，也就进不了任何节点的验收。
- 结果：用户的一句"碎片化学习"被逐字翻译成功能（时长选择器 + 题型清单）。

约束（来自代码事实）：

- `freeze` 不读 `origin`；可冻结性只取决于 `status == "confirmed"` 与 `_confirmed`（`:477-506`）的日志核验。
  因此"提案不等于批准"**不能**靠给意图条目加一个 origin 值来表达。
- `_confirmed` 做 `decision["intent"] == item` 的整体相等比较（`:494`），`_intent_drift` 同理（`:779`）。
  意图条目上的任何新字段必须在记录日志的那一刻就写定，之后永不改动；也不得给旧条目注入默认字段。
- `experience` 已是 plan 的阶段名与 `not_applicable` 键（`:731-733`）。
- 测试里有一份硬编码的话题镜像（`tests/unit/test_product_intent_session.py:13`），被 9 个测试模块导入，
  并有 5 处对列表内容/顺序的精确断言。

## 需求

- **R-M2-01 新话题 `experience-direction`。** 加入 `TOPICS`（位于 `tradeoffs` 之前），同步
  `product-intent-confirmation.md` 的话题清单与散文清单，以及测试镜像。命名避开阶段名 `experience`；
  文档写明二者区别：话题是"产品给人的体验方向"，阶段是"节点承担的体验责任"。
  无界面产品在 `freeze` 时以理由显式排除 `gap-experience-direction`，沿用现有全覆盖规则，不加特例。
- **R-M2-02 提案单独存放。** `product-concept.json` 新增数组 `experience_proposals[]`，**不是**意图条目：
  不进入 `_latest`，不能被 `confirm`，不能被 `freeze` 的 `include` 引用。每条：
  `id`、`title`、`who`、`circumstance`（真实使用情境，含其规模/频次）、`core_loop_feel`
  （核心循环给人的感受与节奏）、`first_minute`（首次进入的第一分钟）、`return_reason`（为什么明天还来）、
  `anti_goals`（刻意不做什么）、`comparable`（同一份工作上的成熟产品及其做法）、`tradeoffs`，
  以及可直接成为意图条目的 `goal`、`scope`、`business_rules`、`acceptance`
  （`acceptance` 是可观察的体验判据，不是功能清单）。`origin` 固定为 `"model-proposal"`。
  id 在提案、意图、问题三个命名空间内唯一（并入 `_validate_question_ids`，`:819-827`）。
- **R-M2-03 操作 `propose`。** `{operation: "propose", proposals: [...], recommended_id, rationale}`：
  要求 2–3 条、恰有一条被推荐、`rationale` 非空、字段齐全；写入 `experience_proposals[]`，
  不写决策日志（提案不是决定）。重复 `propose` 追加新一轮（`round` 递增），旧轮保留为历史。
  `_discussion`（`:923-932`）与 `resume` 在 `experience-direction` 话题下呈现当前轮提案与推荐。
- **R-M2-04 `decide` 动作 `select`。** `{op: "select", proposal_id, reason}`：用户选定一条提案。
  据该提案生成 `topic: "experience-direction"` 的意图条目，`status: "confirmed"`，
  `origin: "model-proposal"`，`proposal_id` 写定，`confirmation.source: "user"`，其余确认字段沿用
  现有批次戳（`:1220-1222`）。用户可在同一批次用 `adjust` 改内容，走现有修订链。
- **R-M2-05 `decide` 动作 `delegate`。** `{op: "delegate", reason}`：用户明说"你定"。
  批次的 `user_reference` 必须是该委托话语所在的真实用户轮次。系统选定当前轮的推荐提案，生成同上的
  意图条目，并额外写定 `auto_decided: true`（沿用 `defensive-patterns.md` Pattern H 的既有命名）与
  `confirmation.delegated: true`。日志 decision 的 `operation` 记为 `"delegate"`。
  没有当前轮提案时拒绝（不得凭空委托）。委托是一次显式用户动作；沉默、默认值、推荐本身仍然不是动作。
- **R-M2-06 界面产品不得缺体验方向。** `validate_scope` 增加阻断码
  `ui_product_without_experience_direction`：profile 的 `experience_priority.mode ∈ {consumer, mixed}`、
  路线为产品路线、冻结范围内却没有已确认的 `experience-direction` 意图。三个公共门随之生效。
  `mode` 缺失时不报此码（那是 M1 的 `missing_experience_priority`）。
- **R-M2-07 委托披露。** 新增只读入口 `product_intent.py <root> --delegations`，输出所有
  `auto_decided: true` 的意图（id、提案标题、委托所在用户轮次、理由）。
  `knowledge/orchestrator-template.md` 的完成文本必须打印这份清单；`run-summary` 同。
  （codex/pi 的模板孪生归 M5。）
- **R-M2-08 协议文本改写。** `product-intent-confirmation.md`：
  - `:21-22` 改为：推荐、显示的默认值、未答、沉默都不是动作；**`select` 与 `delegate` 是动作**。
  - 新增"体验方向提案"一节：产品路线且 `experience_priority.mode != none` 时，模型在讨论
    `experience-direction` 话题前**必须**先 `propose`。提案质量要求：每条先回答
    谁、在什么情境、想要什么感受、为什么回来，再谈功能；对标一个在同一份工作上成熟的产品；
    三条之间必须是方向之别，不是同一方案的三种规模。明文禁止**直译**：用户的用语（如"碎片化学习"）
    是要为之设计的情境，不是要罗列的功能。引用 `consumer-maturity-patterns.md` §B 的三个反模式作为
    提案自检。
  - `decide` 动作目录（`:80-91`）补 `select`、`delegate`；`draft` 的 origin 清单补 `model-proposal`
    并注明它只出现在提案与由提案生成的条目上，`draft` 自身仍只接受原三值。
- **R-M2-09 向后兼容。** 旧日志、旧条目不改、不补字段；新字段只出现在新生成的条目上。
  既有 172 个相关测试（探查记录的 10 个文件）保持通过。
- **R-M2-10 测试。** 新文件 `tests/unit/test_experience_direction.py`，沿用
  `test_product_intent_session.py` 的 `invoke/draft/decide` 子进程风格与 host 参数化，覆盖：
  `propose` 的数量/推荐/字段校验；提案不可 `confirm`、不可 `freeze include`；`select` 生成的条目可冻结且
  通过三个门；`delegate` 写定 `auto_decided` 与 `delegated`、无提案时拒绝、`--delegations` 列出；
  `ui_product_without_experience_direction` 的触发与不触发；无界面产品排除 gap 后可冻结；
  旧日志读入无漂移。同步修正 5 处话题精确断言
  （`test_product_intent_session.py:116,160,207`、`test_evidence_freshness.py:428`、
  `test_intent_review_corrections.py:65`）。

## 接口

- 暴露：`data:experienceProposals`、`api:productIntentPropose`、`api:productIntentSelect`、
  `api:productIntentDelegate`、`data:experienceDirectionIntent`（冻结范围内的体验方向意图，其
  `acceptance` 经 `requirement_refs` 流入节点验收）、`data:delegationDisclosure`（`--delegations` 输出）。
- 消费：`data:experiencePriority`（M1）。

## 不做

- 不让模型在没有用户 `select`/`delegate` 动作的情况下自行确认任何意图。
- 不改 `freeze` 的全覆盖规则、不改日志批次 schema、不引入按动作的 `user_reference`。
- 不实现多模型对抗生成（`innovation-protocols.md` §A 已有方法，可被提案环节引用，但不是本模块的代码）。

## 验收

```bash
python3 -m pytest -q claude/meta-skill/tests/unit/test_experience_direction.py
python3 -m pytest -q claude/meta-skill/tests/unit/test_product_intent_session.py \
  claude/meta-skill/tests/unit/test_product_intent_resume.py \
  claude/meta-skill/tests/unit/test_freeze_idempotence.py \
  claude/meta-skill/tests/unit/test_product_question_identity.py \
  claude/meta-skill/tests/unit/test_product_retained_scope.py \
  claude/meta-skill/tests/unit/test_intent_review_corrections.py \
  claude/meta-skill/tests/unit/test_legacy_profile_authority.py \
  claude/meta-skill/tests/unit/test_legacy_projection_authority.py \
  claude/meta-skill/tests/unit/test_local_reopen_scope.py \
  claude/meta-skill/tests/unit/test_acceptance_allocation.py
```

## Detailed design

设计日期 2026-09-18。以下全部对照 `claude/meta-skill/` 的现行文件核实过（分支
`product-experience-overhaul` @ 80e707e1，M1 尚未落地）。路径均相对 `claude/meta-skill/`，除非另注。
codex/pi 通过符号链接读到同一份 `scripts/` 与 `tests/`，本模块不写任何手工孪生文件。

### Spec corrections（规格引用与现实的出入）

1. **R-M2-10 列的 5 处"话题精确断言"全部由镜像驱动，不需要改。** 在隔离副本里只改
   `product_intent.py:371` 与测试镜像 `test_product_intent_session.py:13`（在 `tradeoffs` 前插入
   `experience-direction`）后实跑：`test_product_intent_session.py:116,160,207`、
   `test_evidence_freshness.py:428`、`test_intent_review_corrections.py:65` 全部原样通过
   （它们写的是 `TOPICS[:-1]`、`TOPICS`、`TOPICS[1:]`、`TOPICS[:3]/[3:]`，随镜像伸缩）。
   真正因插入话题而失败的只有 `test_product_intent_session.py` 里的两个测试（6 个参数化用例）：
   - `test_revised_baseline_generates_full_applicable_plan_and_gates_reject_drift`（`:48`、`:57`）：
     `TOPICS[:-2]` 现在含 `business-loop`、不含 `experience-direction`，导致 `business-loop` 同时出现在
     `include` 与 `exclude`，且 `experience-direction` 无人确认。
   - `test_four_explicit_operations_preserve_history_and_user_additions`（`:146`）：硬编码
     `["scenarios", "core-problem", "tradeoffs"]`，现在中间多出 `experience-direction`。
   设计按现实修这两处（见 U7），其余 5 处只复核、不动。基线实测：验收第二条命令的 10 个文件
   改造前为 172 passed（75 s），与规格一致。
2. **`summarize_run_log.py` 是 `run-summary` 的唯一生产者**（`scripts/orchestrator/summarize_run_log.py`，
   132 行；`orchestrator-template.md:376-380` 调用）。R-M2-07 的"`run-summary` 同"落在这个脚本上，
   规格的"主要落点"没有点名它。它与 `product_intent.py` 同在 bootstrap 复制清单
   （`skills/bootstrap/SKILL.md:782,797`），复制清单不需要改。
3. **`gap-experience-direction` 在 `select`/`delegate` 之后仍是 pending。** 现行 `add` 也不会替缺口问题
   作答（`freeze` 的全覆盖规则 `:1138-1142` 把每个 pending 问题都算进去）。规格没有说缺口怎么关；
   本设计沿用现行做法：宿主在同一批次里追加一条 `answer`（见 Assumptions A3），不给 `select`/`delegate`
   加"一条动作写两条日志决定"的特例。
4. 行号漂移：无实质漂移。`TOPICS` 在 `:371`，`_confirmed` `:477-506`，`_intent_drift` 的整体相等在 `:779`，
   `_validate_question_ids` `:819-827`，`_discussion` 的话题循环 `:923-932`，批次戳 `:1220-1222`，
   `add` 的 `origin` 在 `:1229`，`__main__` `:1365-1377`。

### Architecture

一份脚本、一份协议文本、一份模板文本、一个汇总脚本、一个新测试文件。全部新增逻辑都在
`product_intent.py` 内，形态是"新常量 + 新私有函数 + 在既有分派点各加一个分支"：

```
host ──propose──▶ session() ─▶ _propose() ─▶ product-concept.json.experience_proposals[]   （不写日志）
host ──decide[select|delegate]──▶ session()/decide 循环 ─▶ _direction_intent()
        └▶ requirements[] 追加一条 confirmed 意图 + journal decision{operation, intent 全量拷贝}
host ──freeze/plan──▶ 既有路径，不改
gates(validate_bootstrap / check_decision_inputs / validate_unattended_readiness)
        └▶ validate_scope() ─▶ _experience_direction_blockers()  ← 读 profile.experience_priority.mode（M1）
/run 收尾 ──▶ product_intent.py . --delegations ─▶ delegations()  ← summarize_run_log.py 复用同一函数
```

不变量（设计的硬约束）：

- **提案永远不在 `requirements[]` 里**，所以 `_latest`、`confirm`、`freeze include` 天然够不着它，
  不需要为"提案不可确认/不可冻结"写任何拒绝分支——现有的 `KeyError`/"explicit scope" 拒绝就是证明，
  测试只需断言它。
- **意图条目在写日志那一刻定型。** `select`/`delegate` 先把条目的全部字段（含 `origin`、`proposal_id`、
  `auto_decided`、`confirmation.delegated`）写好，再由既有的 `:1303-1306` 做 `copy.deepcopy(item)` 入日志；
  之后任何代码都不再改这条 revision。`_confirmed` 的 `decision["intent"] == item` 因而恒成立。
- **不给旧条目注入字段。** 所有新读取都用 `.get(...)`，缺省即"无"；`_discussion` 的新键只在有提案时出现，
  旧项目的 `resume` 输出逐字节不变。
- **日志批次 schema 不变。** `decision` 仍是 `{question, chosen, rationale, operation, supersedes, intent}`，
  只是 `operation` 多了两个取值。

### Units

#### U1 话题常量与缺口问题 — R-M2-01

- 文件：`scripts/orchestrator/product_intent.py`。
- 改动：`TOPICS`（`:371`）在 `"tradeoffs"` 前插入 `"experience-direction"`；紧随其后新增
  `EXPERIENCE_TOPIC = "experience-direction"`，供 U3–U5 引用，避免散落字面量。
- 行为：`draft` 的缺口循环（`:1350-1353`）自动为缺该话题的草稿生成 `gap-experience-direction`；
  `_discussion` 的话题顺序自动把它排在 `tradeoffs` 前。无界面产品在 `freeze` 的 `exclude` 里写
  `{"gap-experience-direction": "<理由>"}`，走既有全覆盖规则，无新代码。
- 依赖：无。

#### U2 提案存储、校验与 id 命名空间 — R-M2-02

- 文件：`scripts/orchestrator/product_intent.py`。
- 新私有常量：
  - `PROPOSAL_ORIGIN = "model-proposal"`
  - `_PROPOSAL_TEXT = ("id", "title", "who", "circumstance", "core_loop_feel", "first_minute", "return_reason", "goal")`
  - `_PROPOSAL_LISTS = ("anti_goals", "tradeoffs", "scope", "business_rules", "acceptance")`
  - `comparable` 是对象 `{"product": <非空串>, "approach": <非空串>}`（见 A2）。
- 新私有函数 `_proposal(value) -> dict`：校验一条提案并返回其深拷贝。规则：是 dict；键集合**恰为**
  `_PROPOSAL_TEXT ∪ _PROPOSAL_LISTS ∪ {"comparable"}`（多余键一律拒绝，因此宿主无法塞入 `origin`、
  `status`、`confirmation`、`round`、`recommended`）；文本字段过 `_text`；列表字段是非空的非空串列表；
  `comparable` 两个子键过 `_text`。任一不满足 `raise ValueError("Experience proposal needs <field>")`。
- 存储形状（`product-concept.json.experience_proposals[]` 的每个元素，即 `data:experienceProposals`）：
  提案的全部输入字段 + `origin: "model-proposal"` + `round: <int ≥ 1>` + `recommended: <bool>`；
  被推荐的那条另带 `rationale: <propose 请求的 rationale>`。数组只追加，从不改写旧元素。
- 新私有函数 `_current_proposals(concept) -> list`：返回 `round` 最大的那一轮；无提案返回 `[]`。
- 扩展 `_validate_question_ids(concept)`（`:819-827`）：在既有问题循环之后追加提案循环——
  `concept.get("experience_proposals", [])` 必须是列表；每条 `id` 过 `_text`，且不在意图 id、问题 id、
  已见提案 id 之中，否则 `raise ValueError("Proposal identities must be unique and separate from intent and
  question identities")`。既有问题循环再补一个条件：问题 id 不得等于任何提案 id（同一条报错信息）。
  键缺失时两个循环都是空转，旧概念文件行为不变。既有报错文案一字不改（有测试依赖其语义）。
- 依赖：无。被 U3、U4、U6 使用。

#### U3 操作 `propose` — R-M2-03（`api:productIntentPropose`）

- 文件：`scripts/orchestrator/product_intent.py`。
- 新私有函数 `_propose(root, profile, concept_path, concept, request) -> dict`，在 `session()` 的
  `resume` 分支旁加一行分派：`if operation == "propose": return _propose(...)`。
- 请求：`{operation: "propose", proposals: [<U2 提案>...], recommended_id, rationale}`。
- 校验顺序（全部通过才落盘，失败时文件不变）：
  1. `concept_path == CONCEPT` 且 `profile.get("task_route") in ("product-reconstruction", "new-product")`，
     否则 `"Experience proposals belong to a product session; draft the product first"`；
  2. `proposals` 是长度 2–3 的列表，否则 `"Propose two or three experience directions"`；
  3. 每条过 `_proposal`；本次请求内 id 互不相同；
  4. `recommended_id` 恰等于其中一条的 id，否则 `"Exactly one proposal must be recommended"`；
  5. `_text(rationale)`，否则 `"A recommendation needs its rationale"`；
  6. 追加后过 `_validate_question_ids`（保证与历史轮提案、意图、问题不撞 id）。
- 写入：`round = max((p["round"] for p in existing), default=0) + 1`；逐条补
  `origin`/`round`/`recommended`（及推荐条的 `rationale`）后 `concept.setdefault("experience_proposals", []).extend(...)`；
  只 `_write(root, CONCEPT, concept)`。**不读不写 `decision-journal.json`，不要求 `user_reference`**
  （提案不是用户动作）。
- 返回：`_discussion(root, concept)`（见 U6）。
- 依赖：U2、U6。

#### U4 `decide` 动作 `select` / `delegate` — R-M2-04、R-M2-05（`api:productIntentSelect`、`api:productIntentDelegate`，产出 `data:experienceDirectionIntent`）

- 文件：`scripts/orchestrator/product_intent.py`。
- 新私有函数 `_direction_intent(concept, concept_path, action, op) -> dict`，返回**尚未带 confirmation** 的意图条目：
  1. `concept_path != CONCEPT` → `"Experience directions belong to a product session"`；
  2. `current = _current_proposals(concept)`；为空 → `"No current experience proposals; propose before
     select or delegate"`（R-M2-05 的"不得凭空委托"，`select` 同理）；
  3. `select`：`action["proposal_id"]` 必须命中 `current` 中的一条（历史轮不可选，见 A4），否则
     `"Select one proposal of the current round"`；
     `delegate`：动作里出现 `proposal_id` 即拒绝（`"Delegate takes the recommended proposal; use select to
     name one"`），取 `current` 中 `recommended is True` 的那条；
  4. `_latest(concept)` 中已有 `status == "confirmed"` 且带 `proposal_id` 的条目 → 拒绝
     `"An experience direction is already selected; remove it before choosing another"`（见 A5）；
  5. 生成 id `EXPERIENCE_TOPIC + "-" + proposal["id"]`（见 A1）；若已在 `_latest(concept)` 中 →
     `"Added intent needs an unused stable identity"`（沿用 `add` 的文案）；
  6. 条目：`{id, topic: EXPERIENCE_TOPIC, goal, scope, business_rules, acceptance}`（后四项从提案深拷贝）
     → 过 `_item` → `update(revision=1, origin=PROPOSAL_ORIGIN, evidence=[], status="confirmed",
     proposal_id=proposal["id"], who=proposal["who"], circumstance=proposal["circumstance"])`；
     `delegate` 再 `update(auto_decided=True)`。
     `who`/`circumstance` 从提案原样带到条目上（闭环评审补充）：R-M6-03 要求 cross-exam 从体验方向意图的
     `who/circumstance` 直接取旅程三元组的前两元，而 M6 不消费 `data:experienceProposals`；`_item` 不限制多余键
     （`proposal_id` 同理），两字段与其它字段一样在写日志那一刻定型，`adjust` 的 `deepcopy` 会带到新 revision。
- **`data:experienceDirectionIntent` 的最终形状**（M3、M6 按此读取；位置是 `product-concept.json.requirements[]`，
  同 id 取 `status == "confirmed"` 的那条 revision）：
  `{id: "experience-direction-<proposal_id>", topic: "experience-direction", goal, scope[], business_rules[], acceptance[],
  revision, origin: "model-proposal", evidence: [], status: "confirmed", proposal_id, who, circumstance,
  auto_decided?: true（仅 delegate）, confirmation: {source: "user", reference, decision_id, reason, user_reference,
  delegated?: true（仅 delegate）}}`。用户自述（`origin: "user-request"`）的体验方向条目没有
  `proposal_id`/`who`/`circumstance`/`auto_decided`，读者一律用 `.get(...)`。
- 动作的键名：既有 `decide` 动作一律以 `action["operation"]` 取动作名（`:1217` `op = action["operation"]`）。
  规格 R-M2-04/05 里写的 `{op: "select", …}` 是简写；`select`/`delegate` 与其它动作同形，请求体是
  `{"operation": "select", "proposal_id": …, "reason": …}` / `{"operation": "delegate", "reason": …}`，不另引入 `op` 键
  （M5 的重放夹具按此书写）。
- `decide` 循环（`:1216-1306`）在 `if op == "add"` 之后、`elif op in ("confirm", ...)` 之前加一个分支：

  ```python
  elif op in ("select", "delegate"):
      item = _direction_intent(concept, concept_path, action, op)
      if op == "delegate":
          confirmation["delegated"] = True
      item["confirmation"] = confirmation
      concept.setdefault("requirements", []).append(item)
  ```

  `confirmation` 仍是 `:1220-1222` 的批次戳（`source: "user"`、`reference`、`decision_id`、`reason`、
  `user_reference`），`previous` 保持 `None`。随后既有的 `:1303-1306` 写日志 decision：
  `question = item["id"]`、`chosen = item["goal"]`、`operation = "select" | "delegate"`、
  `supersedes = None`、`intent = deepcopy(item)`。
- 末尾兜底报错（`:1302`）的文案改为列全九种动作：
  `"Only explicit confirm/add/adjust/remove/answer/reopen/restore/select/delegate operations are supported"`
  （无测试钉住旧文案，已 grep）。
- 同批 `adjust`：宿主用确定性 id `experience-direction-<proposal_id>` 指向刚生成的条目，走既有修订链
  （`:1246-1256`）。`deepcopy(item)` 会把 `origin`、`proposal_id`、`auto_decided` 带到新 revision；
  新 revision 的 `confirmation` 是 adjust 自己的批次戳（不含 `delegated`）。这是既有语义，不另加代码；
  委托轮次的追溯由 U5b 沿 revision 链完成。
- `user_reference` 的真实性：CLI 只能校验非空（既有 `:1207`）；"必须是委托话语所在的真实用户轮次"
  由协议文本约束（U8），与现有全部 `decide` 动作同一信任模型。
- 原子性：`decide` 既有结构是"全部动作成功后才 `_write`"，新分支里的任何 `raise` 都让 concept 与 journal
  保持原样（与 `test_invalid_batch_leaves_prior_authority_unchanged` 同一保证）。
- 依赖：U2。

#### U5a 阻断码 `ui_product_without_experience_direction` — R-M2-06（消费 `data:experiencePriority`）

- 文件：`scripts/orchestrator/product_intent.py`。
- 新私有函数 `_experience_direction_blockers(root, profile, refs) -> list`：
  - `priority = profile.get("experience_priority")`；不是 dict，或 `priority.get("mode") not in ("consumer", "mixed")`
    → `[]`（`mode` 缺失/非法属 M1 的 `missing_experience_priority`，`admin`/`none` 不触发）；
  - `latest = _latest(_read(root, CONCEPT, {}))`；若存在 `ref ∈ refs` 使得
    `latest.get(ref["id"])` 的 `topic == EXPERIENCE_TOPIC`、`status == "confirmed"`、
    `revision == ref["revision"]` → `[]`；
  - 否则返回一条**全局**阻断（无 `node_id`，与 `pending_product_confirmation` 同形）：
    `{"code": "ui_product_without_experience_direction", "message": "experience_priority.mode is <mode> but the
    frozen scope holds no confirmed experience-direction intent; return to interactive bootstrap, propose
    directions and record the user's select or delegate, then refreeze and replan"}`。
  - 来源核验不在这里重做：条目的日志核验已由 `_product_contract → _intent_drift → _confirmed` 负责。
    任何 origin 的已确认体验方向（用户自述的 `user-request` 也算）都满足本检查。
- 注册：`validate_scope` 的产品路线分支（`:145-146`）内，`_product_contract` 之后追加一行
  `blockers.extend(_experience_direction_blockers(root, profile, scope["requirement_refs"]))`。
  分支条件已含"产品路线且 `requirement_refs` 非空"；空范围由既有 `pending_product_confirmation` 负责。
  `local-change` 不进该分支，天然不触发。
- 生效面：三个公共门都调用 `validate_scope`（`validate_bootstrap.py:2153`、`check_decision_inputs.py:57`、
  `validate_unattended_readiness.py:615`）且都把 `code` 打到 stdout；`plan` 操作（`:1110`）也因此在规划时
  就拒绝。**不改这三个门的任何代码**，也不碰 `validate_bootstrap.py` 等共享热点文件。
- 依赖：M1 的 `data:experiencePriority`（只读 profile 字段；M1 未落地时字段缺失 → 不触发，无耦合故障）。

#### U5b 委托披露 — R-M2-07（`data:delegationDisclosure`）

- 文件：`scripts/orchestrator/product_intent.py`、`scripts/orchestrator/summarize_run_log.py`、
  `knowledge/orchestrator-template.md`。
- `product_intent.py` 新**公开**函数 `delegations(root) -> dict`（只读）：
  - `concept = _read(Path(root), CONCEPT, {})`；对 `_latest(concept)` 中 `auto_decided is True` 且
    `status == "confirmed"` 的每个条目，在 `concept["requirements"]` 同 id 的各 revision 里找
    `confirmation.get("delegated") is True` 的那条（委托当时的 revision；找不到则退回条目自身），输出
    `{id, revision, proposal_id, proposal_title, user_reference, reason}`：
    `proposal_title` 取 `experience_proposals` 中 id 匹配者的 `title`（缺失为 `null`）；
    `user_reference`/`reason` 取委托 revision 的 `confirmation`。
  - 返回 `{"status": "delegations", "delegations": [...]}`；无概念文件 → 空列表。不写任何文件。
- CLI：`__main__`（`:1368-1370`）的请求映射加一支
  `{"operation": "delegations"} if sys.argv[2:] == ["--delegations"]`；`session()` 顶部（`run-policy` 分派旁）加
  `if request.get("operation") == "delegations": return delegations(root)`。退出码 0；概念文件损坏走既有
  `blocked` + exit 1。
- `summarize_run_log.py`：
  - 顶层 `try: from product_intent import delegations as _delegations` / `except ImportError: _delegations = None`
    （必须顶层导入：单测经 `tests/module_isolation.load` 加载，`sys.path` 只在加载期间含脚本目录；
    生成项目里两脚本同目录）。
  - `summarize()` 返回值新增键 `"delegations"`：`_delegations(project_root)["delegations"]`；函数不可用或抛
    `(OSError, ValueError, TypeError, KeyError, AttributeError, IndexError)` 时为 `[]`，并在后一种情况另写
    `"delegations_error": str(exc)`——披露读不出来必须可见，但不得让收尾汇总失败。
  - `write_reports()` 在 "Recent Failures" 之后追加 `## Delegated Decisions` 段：每条
    ``- `<id>` proposal=`<proposal_title>` user_turn=`<user_reference>` reason=`<reason>` ``；空则 `- none`；
    有 `delegations_error` 则多一行 `- unreadable: <error>`。
  - `schema_version` 保持 `"1.0"`（只增键）。
- `knowledge/orchestrator-template.md` 的 `## Post-Completion`（`:373` 起），在第 0 步之后插入第 0b 步：
  运行 `python3 .allforai/bootstrap/scripts/product_intent.py . --delegations`；完成文本**必须**在
  "Decisions you delegated to the model" 标题下逐条打印 id、提案标题、委托所在用户轮次、理由；
  列表为空打印 "No delegated decisions."；无论成功或提前停止都执行；此处不得提问。
  插入点在既有"Run log summary"与"Mark concept drift resolved"之间，不删改任何既有句子
  （`validate_meta_contracts.py:104-176` 钉住的字面量都不在该区域，已核对）。
- 依赖：U4。

#### U6 `_discussion` / `resume` 呈现提案 — R-M2-03

- 文件：`scripts/orchestrator/product_intent.py`，只动 `:923-932`。
- 在话题循环前取 `current = _current_proposals(concept)` 与
  `direction_open = not any(i["topic"] == EXPERIENCE_TOPIC and i["status"] == "confirmed" for i in latest.values())`。
- 循环内：`show = topic == EXPERIENCE_TOPIC and current and direction_open`；入选条件由
  `if items or questions` 改为 `if items or questions or show`；当 `topic == EXPERIENCE_TOPIC and current` 时
  给该话题条目补三个键：`"proposals": current`、`"recommended_id"`、`"rationale"`（取自推荐条）。
- 返回对象在 `concept.get("experience_proposals")` 非空时补 `"experience_proposals": [...]`（全部轮次，
  供恢复上下文）；为空时**不出现该键**，保证旧项目与既有测试 `resumed == output` 的逐字节等价。
- 依赖：U2。

#### U7 测试镜像与既有测试的两处修正 — R-M2-01、R-M2-09、R-M2-10

- 文件：`tests/unit/test_product_intent_session.py`（唯一被改的既有测试文件）。
  - `:13` 镜像在 `"tradeoffs"` 前插入 `"experience-direction"`。
  - `test_revised_baseline_…`：把 `TOPICS[:-2]` 换成局部变量
    `kept = [t for t in TOPICS if t not in ("business-loop", "tradeoffs")]`，`:48` 的 confirm 列表与 `:57` 的
    `include` 都用 `kept`（语义不变：确认其余话题、移除 `business-loop`、调整 `tradeoffs`、新增 `offline`）。
  - `test_four_explicit_operations_…` `:146`：期望改为
    `["scenarios", "core-problem", "experience-direction", "tradeoffs"]`。
- 规格点名的另外 5 处（含 `test_evidence_freshness.py:428`、`test_intent_review_corrections.py:65`）
  经实跑确认无需改动；实现者复核即可。`test_evidence_freshness.py` 内的 2 个既有失败不得触碰。

#### U8 协议文本 — R-M2-01、R-M2-08

- 文件：`knowledge/product-intent-confirmation.md`。全部为局部替换或新增段落；M1 先行改动的是 `plan`
  条目（`:122-123` 的 `not_applicable`），与以下位置不重叠。
  1. `:10-11` 散文清单补 "experience direction"（`… business loop, experience direction and tradeoffs`）。
  2. `:21-22` 改为：`recommendations, displayed defaults, omitted answers and silence are not actions;
     `select` and `delegate` are actions.`
  3. `:40` 的 origin 清单后补一句：`model-proposal` 只出现在提案与由提案生成的条目上；`draft` 自身仍只接受
     `inference`、`unknown`、`user-request`。
  4. `:41-42` 话题清单在 `business-loop` 与 `tradeoffs` 之间补 `experience-direction`，并加两句区别说明：
     话题 `experience-direction` 是"产品给人的体验方向"；`plan` 的阶段/`not_applicable` 键 `experience` 是
     "节点承担的体验责任"，二者不可互换。无界面产品在 `freeze` 以理由排除 `gap-experience-direction`。
  5. 在 `resume` 条目之后新增条目 `propose`：请求形状、字段表（U2）、2–3 条/恰一推荐/`rationale`、
     重复提案开新轮、旧轮为历史、不写日志、`resume` 在 `experience-direction` 话题下返回
     `proposals`/`recommended_id`/`rationale`。
  6. `decide` 动作目录（`:80-91`）补：`select` 选定当前轮一条提案（`proposal_id`）；`delegate` 仅在用户明说
     "你定"时使用，批次 `user_reference` 必须是该话语所在的真实用户轮次，系统取当前轮推荐；两者生成 id 为
     `experience-direction-<proposal_id>` 的已确认条目（`origin: model-proposal`，并带提案的 `who`/`circumstance`；`delegate` 另有
     `auto_decided: true` 与 `confirmation.delegated: true`）；同一批次可接 `adjust`；同一批次须用 `answer`
     关闭 `gap-experience-direction`（答案写所选提案标题）；无当前轮提案时两者都被拒绝；已有选定方向时须先
     `remove`。
  7. 新增一节 `## Experience direction proposals`（放在 "Discussion responsibility" 之后）：
     - 触发：产品路线且 `bootstrap-profile.json` 的 `experience_priority.mode != none` 时，讨论
       `experience-direction` 话题前**必须**先 `propose`；
     - 质量：每条先回答谁、在什么情境（含规模/频次）、想要什么感受、为什么回来，再谈功能；对标一个在同一份
       工作上成熟的产品及其做法；各条之间是方向之别，不是同一方案的三种规模；`acceptance` 是可观察的体验
       判据，不是功能清单；
     - **禁止直译**：用户用语（如 "fragmented learning / 碎片化学习"）是要为之设计的情境，不是要罗列的功能；
     - 自检：引用 `consumer-maturity-patterns.md` §B 的三个反模式（The Compressed Admin Panel、
       The Concept Demo、Feature Checklist Design）；
     - 授权边界：推荐本身不是动作；只有用户的 `select` 或明说的 `delegate` 才产生已确认意图；
       委托在 `/run` 收尾经 `--delegations` 披露（命名沿用 `defensive-patterns.md` Pattern H 的
       `auto_decided`）。可选引用 `innovation-protocols.md` §A 作为生成方法，不是本协议的要求。
  8. 文末 CLI 段补一句 `--delegations` 是只读入口。
- 不删除任何被 `validate_meta_contracts.py` 钉住的字面量（该文件不钉本协议文本，已 grep）。
- 遵守 M1 U2 的不变量（M1 验收第 4 条 grep，M1 先于本模块落地）：本文件里任何提到 `experience_priority` 的行必须
  同行含字面量 `experience_priority.mode`；写完后重跑
  `grep -rn "experience_priority" claude/meta-skill/knowledge | grep -v "experience_priority.mode" | grep -v bootstrap`，期望为空。

#### U9 新测试文件 — R-M2-10（并覆盖 R-M2-01…09 的可执行证明）

- 文件：`tests/unit/test_experience_direction.py`（新建）。
- 风格：从 `.test_product_intent_session` 导入 `invoke, draft, decide, TOPICS, CONCEPT, JOURNAL`；从
  `.test_bootstrap_scope` 导入 `project, write, gate, confirm_plan, publish_contract`；从
  `.test_validate_bootstrap` 导入 `ATTENTION_CONTRACT_BODY`。全部用例
  `@pytest.mark.parametrize("host", ["claude", "codex"])`，经复制到 `tmp_path` 的 CLI 以子进程驱动。
- 本文件的私有助手：
  - `proposal(identity, **overrides)`：返回字段齐全的提案；其 `goal`/`scope`/`business_rules`/`acceptance` 的措辞
    **不得含 M1 的界面词项**（`screen`、`frontend`、`界面`、`页面` 等，见 M1 `UI_IMPLEMENTATION_TERMS`）——这些文本会经
    `plan` 投影进 node-spec 正文，而 M1/M3 的界面实现节点识别正是对 node-spec 正文做词项匹配（见 A10）；
  - `propose(root, ids=("calm-ritual", "quick-burst"), recommended="calm-ritual")`；
  - `new_product_draft()`：`draft()` 的 new-product 变体，**去掉** `experience-direction` 话题的条目
    （从而生成 `gap-experience-direction`），`questions=[]`；
  - `set_mode(root, mode)`：读改写 `bootstrap-profile.json` 的 `experience_priority = {"mode": mode, "reason": "test"}`；
  - `cli(root, *args)`：带 argv 调 CLI（同 `test_intent_review_corrections.py:50-52` 的写法）；
  - `plan_request(intent_ids)`：单节点计划，`responsibilities` 含全部六个阶段（含 `experience`），不写
    `not_applicable.experience`。
- 用例（每条对应的需求在括号内）：
  1. `test_topic_is_listed_before_tradeoffs_and_missing_direction_is_a_gap`（01）：脚本 `TOPICS` 与镜像一致、
     顺序正确；`new_product_draft()` 的输出含 `gap-experience-direction`。
  2. `test_propose_validates_count_recommendation_and_fields`（02、03）：1 条/4 条被拒；`recommended_id` 不在
     其中被拒；`rationale` 为空被拒；缺任一字段、空列表字段、`comparable` 缺子键、多余键（`origin`、`status`）被拒；
     每次拒绝后 `CONCEPT` 字节不变、`JOURNAL` 不存在。
  3. `test_propose_stores_rounds_without_journal_and_resume_presents_current_round`（02、03）：成功后
     `experience_proposals` 每条 `origin == "model-proposal"`、`round == 1`、恰一条 `recommended`；`JOURNAL`
     不存在；再次 `propose`（新 id）→ `round == 2`、旧轮原样保留；`resume` 在 `experience-direction` 话题下的
     `proposals` 只含第 2 轮，`recommended_id`/`rationale` 正确；未 draft 先 `propose` 被拒。
  4. `test_proposal_identity_is_unique_across_proposals_intents_and_questions`（02）：提案 id 撞意图 id、
     撞问题 id、撞历史轮提案 id 均被拒。
  5. `test_proposal_cannot_be_confirmed_or_frozen`（02）：`confirm` 提案 id → exit 1；`freeze` 的 `include`
     含提案 id → exit 1 且无 baseline 文件。
  6. `test_selected_direction_freezes_and_passes_all_public_gates`（04、06）：`set_mode(consumer)` →
     `propose` → 一个批次内 `select` + `answer gap-experience-direction` + 其余话题 `confirm` →
     条目断言（`topic`、`status`、`origin`、`proposal_id`、`who`/`circumstance` 等于提案原值、`confirmation.source == "user"`、无 `auto_decided`、
     日志 `operation == "select"` 且 `intent == 条目`）→ `freeze` → `plan` → `confirm_plan` →
     `publish_contract` → 三个门 exit 0。
  7. `test_select_then_adjust_in_one_batch_keeps_revision_lineage`（04）：同批 `select` + `adjust`
     （改 `acceptance`）→ 两个 revision，`superseded`/`confirmed`，新 revision 仍带 `origin`/`proposal_id`，可冻结。
  8. `test_delegate_records_auto_decision_and_is_disclosed`（05、07）：`delegate` 后条目取推荐提案内容、
     `auto_decided is True`、`confirmation.delegated is True`、`confirmation.user_reference == "user turn <batch>"`、
     日志 `operation == "delegate"`；`cli(root, "--delegations")` exit 0，列出 id、`proposal_title`、
     `user_reference`、`reason`，且前后 `CONCEPT`/`JOURNAL` 字节不变；后续批次 `adjust` 后披露仍在，且
     `user_reference` 仍是委托轮次；`select` 生成的条目不出现在披露里。
  9. `test_delegate_and_select_need_a_current_proposal_round`（05）：无提案时 `delegate`、`select` 均 exit 1，
     文件不变；`delegate` 携带 `proposal_id` 被拒；`select` 历史轮 id 被拒；已有选定方向时再 `select` 被拒。
  10. `test_ui_product_without_direction_is_blocked_at_every_gate`（06）：`new_product_draft()` → 确认其余话题 →
      `freeze` 排除 `gap-experience-direction` → 在 `mode` 缺失下 `plan` 成功并发布 → `set_mode("consumer")`
      → 三个门各自 exit 1 且 stdout 含 `ui_product_without_experience_direction`；再 `set_mode` 为
      `"mixed"` 同样触发；`plan` 在 `consumer` 下重跑被拒且 stdout 含该码。
  11. `test_direction_gate_stays_silent_when_it_does_not_apply`（06、01）：同一夹具下 `mode` 为 `none`、`admin`、
      字段缺失三种情形，stdout 均不含该码；`project()` 自带的 `local-change` 工作流在 `mode == consumer` 下也
      不含该码；无界面产品（`mode == none`）排除 gap 后 `freeze` 成功且三个门 exit 0
      （`not_applicable.experience` 给出理由）。
  12. `test_pre_existing_concept_and_journal_read_without_drift`（09）：draft 后从概念文件删掉
      `gap-experience-direction`（模拟改造前的概念），走完 confirm/freeze/plan → 三个门 exit 0；`resume`
      输出无 `experience_proposals` 键、任何话题条目无 `proposals` 键；`resume` 与 `--delegations` 前后
      `CONCEPT`/`JOURNAL` 字节不变；全部条目无 `proposal_id`/`auto_decided` 字段。
  13. `test_run_summary_and_completion_text_disclose_delegations`（07）：
      `load("product_intent", "summarize_run_log")`（`tests/module_isolation`）后，对一个含委托条目的
      `tmp_path` 调 `summarize`/`write_reports`：`summary["delegations"]` 一条、`run-summary.md` 含
      `## Delegated Decisions` 与提案标题；无概念文件时为 `[]` 与 `- none`。同一用例读取 canonical
      `knowledge/orchestrator-template.md`，断言 `## Post-Completion` 之后出现 `--delegations` 与
      `Decisions you delegated to the model`（此用例不参数化 host）。
  14. `test_protocol_text_names_the_new_topic_and_actions`（01、08）：读取 canonical
      `knowledge/product-intent-confirmation.md`，断言含 `experience-direction`、`` `select` and `delegate` are actions ``、
      `model-proposal`、`## Experience direction proposals`、`consumer-maturity-patterns.md`、`--delegations`，
      且旧句 `omitted answers and silence are not actions.` 已不存在（不参数化 host）。
  文本钉子放在本测试文件而不是 `validate_meta_contracts.py`：后者是与 M4 并行时的共享热点文件，M2 不碰它。

### Data flow

1. `draft`（new-product）不带体验方向条目 → 生成 `gap-experience-direction` → `resume`/`draft` 输出里出现
   `experience-direction` 话题。
2. 宿主按 U8 的质量要求调用 `propose` → `experience_proposals[]` 第 N 轮 → `_discussion` 在该话题下带出
   `proposals`/`recommended_id`/`rationale`，宿主据此向用户呈现 2–3 个方向与推荐。
3. 用户选一个 → `decide[select, answer gap]`；或明说"你定" → `decide[delegate, answer gap]`。生成的条目与日志
   decision 的 `intent` 同时定型。
4. `freeze include` 含 `experience-direction-<proposal_id>` → baseline `intents[]` 含该条目 → `plan` 把它的
   `acceptance` 经 `requirement_refs` 写入消费节点的 `acceptance` 与 Node-spec（既有 `:1107-1122`，不改）。
   这就是 `data:experienceDirectionIntent` 流入节点验收的路径，M3/M6 从 `product-concept.json` 的 `requirements[]` 里按
   `topic == "experience-direction"`、`status == "confirmed"` 读取，`auto_decided`、`who`、`circumstance` 随条目可见
   （形状见 U4）。可能同时存在多条（至多一条由提案生成，另可有用户自述的条目），读者须按列表处理。
5. 三个门经 `validate_scope` 执行 U5a；`/run` 收尾经 `--delegations` 与 `run-summary` 披露委托。

### Error handling

- 所有新拒绝都是 `ValueError`，由既有 `__main__` 统一转成 `{"status": "blocked", "error": ...}` + exit 1；
  不新增异常类型、不新增退出码。
- `propose` 与 `decide` 都是"先校验、后一次性落盘"；失败不留半写状态。
- `validate_scope` 的新检查在既有 `try` 内：概念文件不可读等异常仍折叠为 `invalid_scope`（既有行为）。
- `delegations()` 对缺失文件返回空列表；对损坏文件抛出，由 CLI 报 `blocked`，由 `summarize_run_log.py`
  记为 `delegations_error` 而不中断汇总。
- 损坏的 `experience_proposals`（非列表、缺 id、撞 id）经 `_validate_question_ids` 在 `session()` 入口与
  `_product_contract` 两处被拒——后者意味着手工破坏提案数组会让门报 `invalid_scope`，这是有意的失败关闭。

### Testing

- 新文件：`claude/meta-skill/tests/unit/test_experience_direction.py`（U9）。
- 改动的既有测试：仅 `claude/meta-skill/tests/unit/test_product_intent_session.py`（U7）。
- 验收命令（规格原有两条保持不变，另加两条回归，均显式点名文件，不以目录方式跑 codex/pi）：

```bash
python3 -m pytest -q claude/meta-skill/tests/unit/test_experience_direction.py
python3 -m pytest -q claude/meta-skill/tests/unit/test_product_intent_session.py \
  claude/meta-skill/tests/unit/test_product_intent_resume.py \
  claude/meta-skill/tests/unit/test_freeze_idempotence.py \
  claude/meta-skill/tests/unit/test_product_question_identity.py \
  claude/meta-skill/tests/unit/test_product_retained_scope.py \
  claude/meta-skill/tests/unit/test_intent_review_corrections.py \
  claude/meta-skill/tests/unit/test_legacy_profile_authority.py \
  claude/meta-skill/tests/unit/test_legacy_projection_authority.py \
  claude/meta-skill/tests/unit/test_local_reopen_scope.py \
  claude/meta-skill/tests/unit/test_acceptance_allocation.py      # 期望仍为 172 passed
python3 -m pytest -q claude/meta-skill/tests/unit/test_run_logging.py          # summarize_run_log 回归
python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py      # 模板/协议改动未删钉住的字面量
```

  `test_evidence_freshness.py` 含 2 个既有失败，不列入验收；如需复核其 `:428`，只跑
  `-k "not cannot_claim_completion"`。

### Assumptions（内部选择）

- **A1 生成条目的 id 为 `experience-direction-<proposal_id>`。** 规格要求 id 在三个命名空间内唯一，所以条目
  不能复用提案 id；确定性派生让宿主在同一批次里就能 `adjust` 它，也让"同一提案选两次"落入既有的
  "unused stable identity" 拒绝。
- **A2 `comparable` 是 `{product, approach}` 对象；`anti_goals`、`tradeoffs` 是非空字符串列表。** 规格只给了
  语义（"成熟产品及其做法"），对象形态让"产品"与"做法"都不可缺。M5 的夹具按此形状写。
- **A3 `select`/`delegate` 不自动关闭 `gap-experience-direction`**；宿主在同一批次追加 `answer`。与现行 `add`
  行为一致，避免一条动作写两条日志 decision（会牵动 `reference` 下标的计算）。漏写时 `freeze` 以既有的
  "explicit scope for every intent and unresolved question" 失败关闭。
- **A4 只能 `select` 当前轮的提案。** 规格称旧轮"保留为历史"；`delegate` 已限定当前轮，`select` 取同一口径。
- **A5 同时至多一条由提案生成的已确认方向。** 再选之前先 `remove`。这是防止两条互斥方向同时进入冻结范围的
  最小护栏；用户自述（`user-request`）的体验方向条目不受此限。
- **A6 `_discussion` 的新键按需出现**（无提案则无键），以保住旧输出的逐字节等价。
- **A7 `propose` 不读 `experience_priority`。** "何时必须提案"是协议文本义务（R-M2-08），代码侧的强制点是
  U5a 的阻断码；给 `propose` 再加 mode 判断属于未被要求的功能。
- **A8 `propose` 要求已存在产品会话**（profile 的 `task_route` 为产品路线），即先 `draft` 后 `propose`。
- **A9 披露文本的英文标题** "Decisions you delegated to the model" / "No delegated decisions." 为本模块选定的
  字面量；M5 在 codex/pi 模板孪生中沿用。
- **A10 与 M1、M3 的集成假设。** U9 第 6、11 条用例要求 `mode == consumer` 下三个门 exit 0，夹具是无界面措辞的
  单个 `implement` 节点（`orders.py`）。M1 的 `validate_experience_design_coverage` 与之后落地的 M3
  `validate_experience_gate_flow` 都只在"存在界面实现节点"时才要求设计节点/评审节点/修复回路，识别方式是对节点条目与
  node-spec 正文做词项匹配（已核对：共用的 `ATTENTION_CONTRACT_BODY` 不含任何 M1 界面词项）。因此本模块的首选做法是
  **让夹具保持无界面**：`proposal()` 助手、`plan_request` 的 goal/body 均不写界面词项，profile 不带 `role ∈ {frontend, mobile}`
  的模块。这样 M3 落地后这两条用例无需回改。只有在无法避免被识别为界面实现节点时，才按 M1 的产物路径契约补设计节点
  （M3 落地后还须补两阶段评审节点与回路）；任何情况下都不放宽断言、不改 M1/M3 的检查。M1 对 `project()` 夹具的
  `experience_priority` 补齐（R-M1-09，值为 `none`）不与本模块冲突：本模块的用例一律经 `set_mode` 显式写入；
  用例 10 所说"`mode` 缺失下 `plan` 成功"在 M1 落地后实际是 `mode == none`，两者对 U5a 等价（均不触发）。
- **A11 不改 `skills/bootstrap/SKILL.md`。** 它是共享热点文件且 bootstrap 步骤文本归 M1；本模块的协议入口是
  `product-intent-confirmation.md`，SKILL.md 已经把产品路线指向该协议。

### File touch list

| 路径（相对仓库根） | 动作 | 需求 |
|---|---|---|
| `claude/meta-skill/scripts/orchestrator/product_intent.py` | edit | R-M2-01、02、03、04、05、06、07、09 |
| `claude/meta-skill/scripts/orchestrator/summarize_run_log.py` | edit | R-M2-07 |
| `claude/meta-skill/knowledge/product-intent-confirmation.md` | edit | R-M2-01、R-M2-08 |
| `claude/meta-skill/knowledge/orchestrator-template.md` | edit（仅 `## Post-Completion` 插入第 0b 步） | R-M2-07 |
| `claude/meta-skill/tests/unit/test_experience_direction.py` | create | R-M2-10（并证明 01–09） |
| `claude/meta-skill/tests/unit/test_product_intent_session.py` | edit（`:13` 镜像、`:48/:57`、`:146`） | R-M2-01、R-M2-09、R-M2-10 |

不触碰：`validate_bootstrap.py`、`validate_meta_contracts.py`、`knowledge/bootstrap-planning.md`、
`tests/unit/test_validate_bootstrap.py`、`skills/bootstrap/SKILL.md`（共享热点文件）；
`check_decision_inputs.py`、`validate_unattended_readiness.py`（经 `validate_scope` 自动生效）；
`knowledge/defensive-patterns.md`、`knowledge/consumer-maturity-patterns.md`（只引用）；
codex/pi 的任何手工孪生文件（归 M5）。
