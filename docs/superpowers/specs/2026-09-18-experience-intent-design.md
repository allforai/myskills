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
