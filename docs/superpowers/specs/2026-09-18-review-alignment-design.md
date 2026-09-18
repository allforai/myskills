# M6 review-alignment — 事后评审对齐

总览：`2026-09-18-product-experience-overhaul-overview.md`。依赖 M2（`data:experienceDirectionIntent`）、
M3（`data:experienceReviewDoc`、`data:experienceLensVocabulary`）、M4（`data:settingsAudience`）。
范围决定 D2：用户要求把事后评审纳入本轮。

## 现状判断

`/product-review` 与 `/cross-exam` 本身未发现缺陷；product-review 的第 4 问镜头本就压缩自
`consumer-maturity-patterns.md`。要对齐的是它们与运行内新机制之间的接缝：

- 运行内质量门（M3）若用另一套维度名，会出现"运行内放行、事后打回"的双重标准。
- product-review 采信 cross-exam 报告作既有证据（`SKILL.md:80`），但不读 `.allforai/`（`:20`），
  因此看不到运行内评审结论，会重复评审。
- cross-exam §1b 的旅程候选来自 census 操作面与需求基准（`SKILL.md:175-179`）；
  用户确认过的体验方向与任务故事是更直接的旅程来源，目前不在其中。
- 两者都没有"部署方配置暴露给最终用户"这一观察点。

双写规则：`claude/superstorm/skills/cross-exam/SKILL.md` ↔ `codex/cross-exam-skill/SKILL.md`，
`claude/superstorm/skills/product-review/SKILL.md` ↔ `codex/cross-exam-skill/product-review.md` 是手工孪生，
每个任务同提交双写（替换规则：`/cross-exam` → `cross-exam` 等，见既有差异）。Pi 的 cross-exam 适配器指向
Codex 协议，不单独改；product-review 不在 Pi 上。

## 需求

- **R-M6-01 镜头同名。** product-review 第 4 问的五个镜头与 M3 的五个同名维度一一对应
  （引导=`onboarding`、过程反馈=`process_feedback`、下一步=`next_step`、状态一致=`state_consistency`、
  回来理由=`return_reason`）。在 product-review 的 Lenses 表下加一行对应关系。
  新增契约测试 `shared/scripts/orchestrator/test_experience_lens_parity.py`：M3 的 SKILL.md、
  product-review（claude 与 codex 两份）都包含这五个标识符。
- **R-M6-02 运行内评审可被采信。** product-review 的 "Prior evidence" 规则扩展：若存在
  `docs/experience-review/runtime.md`（M3 产出），读最新一份；其各镜头观察是第 4 问的既有证据，
  其 must-fix 清单里仍未关闭的项写进 `Prior evidence` 行并可作 `depends_on`。
  与采信 cross-exam 报告同一纪律：产品在那之后动过就标过期，不在这里重判；这里的观察不覆盖那份结论；
  已知的 must-fix 不再占 `R` 号。"No `.allforai/`" 不变。报告模板的 `## Prior evidence` 行相应补一种来源。
- **R-M6-03 旅程候选增加体验基线来源。** cross-exam §1b 第 1 步"整理候选"的可选数据源增加：
  `.allforai/product-concept/product-concept.json` 中 `topic == "experience-direction"` 的已确认需求
  （其 `who/circumstance` 直接给出三元组的前两元），以及 `.allforai/app-design/concept/job-story-spec.json`。
  与 `task-inventory.json` 同一地位：存在就读，只是可选数据源；不另派 agent 读代码的纪律不变。
  来自 `auto_decided: true` 意图的候选在呈现给用户时标注"此方向由模型受托选定"。
- **R-M6-04 观察点：受众泄漏。** product-review 第 4 问镜头表增加一行"最终用户界面里有没有
  部署方/开发者才该碰的配置（服务地址、凭证、模型、环境）"，归 `不够商业级`；自检清单的该主张示例补上这一点。
  cross-exam 的 `knowledge/cross-exam/lenses.md`（及 codex 孪生）在细节质量镜头下加同一观察点。
- **R-M6-05 不破坏既有守卫。** `test_superstorm_contract.py` 不覆盖这两个 skill；
  `test_rule_consistency.py:292-297` 字节比较的三个规则资源不改。若改动触及
  `journey_candidates` 等渲染器读取的字段名则禁止（本模块不改字段名）。
  `check_skill_refs.py` 仍通过。

## 接口

- 暴露：无（终端消费者）。
- 消费：`data:experienceDirectionIntent`（M2）、`data:experienceReviewDoc`、
  `data:experienceLensVocabulary`（M3）、`data:settingsAudience`（M4）。

## 不做

- 不让 product-review 读 `.allforai/`，不让它在无人值守下运行，不改其"只给建议"的不变式。
- 不改 cross-exam 的裁决词汇、ledger schema、渲染器。
- 这两份 skill 的新条款只有散文约束，行为证明归 M5 的思维测试。

## 验收

```bash
python3 -m pytest -q shared/scripts/orchestrator/test_experience_lens_parity.py
python3 -m pytest -q claude/superstorm/scripts
python3 -m pytest -q codex/cross-exam-skill/scripts
python3 claude/superstorm/scripts/check_skill_refs.py
python3 -m pytest -q pi/cross-exam
```

## Detailed design

设计日期 2026-09-18，对照分支 `product-experience-overhaul` @ 80e707e1 的真实文件。
本模块只改散文（四份 skill/知识文件及其孪生）并新增一个契约测试；不改任何 Python 生产代码、schema、渲染器。

### Spec corrections（规格引用与现实的差异）

1. **codex 的 lenses 孪生不在 `knowledge/` 下。** R-M6-04 写"`knowledge/cross-exam/lenses.md`（及 codex 孪生）"；
   codex 孪生的真实路径是 `codex/cross-exam-skill/lenses.md`（codex 包是扁平布局，没有 `knowledge/` 目录）。
   两份当前**字节相同**（`diff` 为空），但不在 `test_rule_consistency.py` 的字节比较名单里
   （名单是 `rule_consistency.py`、`rule-consistency.md`、`prompts/rules.md`，真实行号 `:293-298`，规格写 `:292-297`）。
   设计：两份 lenses.md 写入同一段文字并保持字节相同。
2. **cross-exam §1b 行号。** 规格写 `SKILL.md:175-179`；现实是 claude `:177-181`、codex `:181-185`。两份该段文字相同。
3. **product-review 行号无漂移**：`:20`（No `.allforai/`）、`:60`（第 4 问镜头行）、`:76`（Facts 完成条件）、
   `:80`（Prior evidence）、`:120`（`不够商业级` 自检）、`:122`（gap restated 自检）、`:143-144`（模板）。
   codex 孪生同内容，行号整体 −2。
4. **孪生的既有差异只有 5 处**（frontmatter、调用说明、`Not cross-exam` 一句、两处 `/cross-exam` → `cross-exam`）。
   本模块新增文字里凡提到 cross-exam 命令的地方沿用同一替换；其余逐字相同。
5. **意图条目的存放位置。** R-M6-03 写"`product-concept.json` 中 `topic == "experience-direction"` 的已确认需求"；
   现实里意图条目在该文件的 `requirements[]` 数组，同一 `id` 有多个 `revision`，取最新一条
   （`product_intent.py:469-474` 的 `_latest`），已确认即 `status == "confirmed"`。
   M2 规格没有承诺意图条目本身带 `who`/`circumstance`（这两个字段定义在提案 `experience_proposals[]` 上）。
   `data:experienceProposals` 不在本模块的消费清单内，因此设计不读提案数组：条目带 `who`/`circumstance` 就直接用，
   不带就从 `goal`/`scope` 起草——§1b 第 3 步本来就要读回用户确认，起草不准不会漏进 ledger。
6. **基线**（本次设计时实跑）：`claude/superstorm/scripts` 255 passed、`codex/cross-exam-skill/scripts` 172 passed、
   `pi/cross-exam` 7 passed、`check_skill_refs.py` OK（33 个文件）。没有任何现有测试读取 product-review 或 lenses.md 的正文；
   `pi/cross-exam/test_contract.py` 只断言 `codex/cross-exam-skill/lenses.md` 存在和 Pi 适配器自己的字符串，不受影响。

### 架构

```
M3 experience-quality-critique/SKILL.md ──(五个维度标识符)──┐
                                                            ├─ U1 test_experience_lens_parity.py
product-review（claude + codex）──(Lenses 表下的对应行)─────┘
M3 写 docs/experience-review/runtime.md ──► U2 product-review §1 Prior evidence（采信，不重判）
M2 experience-direction 意图 / app-design job-story-spec ──► U3 cross-exam §1b 第 1 步候选来源
M4 受众词汇（end-user/operator/developer）──► U4 product-review 第 4 问观察点 + cross-exam 细节质量镜头
```

四个单元互不依赖，可按 U1→U4 顺序各一次提交；每个单元内 claude 与 codex 孪生同提交双写。

### U1 — 镜头同名（R-M6-01）

**做什么。** 在 product-review 的 Lenses 表之后、`## 0. Intake` 之前，加一段（两份孪生逐字相同）：

> 第 4 问的五个镜头与运行内体验质量门（meta-skill `experience-quality-critique`）的五个维度同名同义：
> 引导 = `onboarding` · 过程反馈 = `process_feedback` · 下一步 = `next_step` · 状态一致 = `state_consistency` ·
> 回来理由 = `return_reason`。运行内放行与事后审视用的是同一把尺；该门另有的 `mainline`、`direction_fidelity`、
> `audience_leak` 不是这五格之一。

第 12 行"nothing here requires those files to be installed"不变：对应行只给名字，不要求读 meta-skill 文件。

**新文件** `shared/scripts/orchestrator/test_experience_lens_parity.py`。风格对齐同目录的
`test_codex_contract_checks.py`：pytest 函数式、`ROOT = Path(__file__).resolve().parents[3]`、
`read_text(encoding="utf-8")`、无 fixture 依赖（目录 `conftest.py` 的 autouse fixture 对纯文本测试无副作用，
已用 `test_loop_detection.py` 验证该目录可从仓库根按文件名收集）。

```python
LENSES = {"onboarding": "引导", "process_feedback": "过程反馈", "next_step": "下一步",
          "state_consistency": "状态一致", "return_reason": "回来理由"}
GATE   = ROOT / "claude/meta-skill/skills/app-design/40-qa/experience-quality-critique/SKILL.md"
REVIEWS = [ROOT / "claude/superstorm/skills/product-review/SKILL.md",
           ROOT / "codex/cross-exam-skill/product-review.md"]
```

用例：
- `test_gate_and_both_reviews_name_every_lens`（对 `[GATE, *REVIEWS]` 参数化）：文件存在，且每个标识符以
  反引号形式 `` `onboarding` `` 出现。GATE 缺失即失败（不 skip——M3 先于 M6 执行，缺失就是回归）。
- `test_reviews_pair_each_identifier_with_its_lens`（对 REVIEWS 参数化）：存在同一行同时含中文镜头名与其标识符
  （`f"{zh} = `{ident}`"` 子串），防止五个名字在但配错对。
- `test_review_twins_carry_the_same_mapping_line`：两份 product-review 中含 `` `onboarding` `` 的那一行字节相同。

GATE 只断言"包含标识符"，不断言其格式，避免把 M3 的内部排版钉死。

### U2 — 运行内评审可被采信（R-M6-02）

全部改动在 product-review（两份孪生），四处：

1. **Invariants `No .allforai/` 一条**：句末 "`docs/cross-exam/` is readable input." 改为
   "`docs/cross-exam/` and `docs/experience-review/` are readable input."。禁读 `.allforai/` 的句子一字不动。
2. **§1 `Prior evidence` 段之后新增一段 `Prior evidence — runtime experience review.`**（不改写原段）：
   - 若 `docs/experience-review/runtime.md` 存在就读它（该路径每次评审覆盖写，存在的那份即最新一份）；
     不读 `design.md`——那份判的是设计产物，不是运行中的产品。
   - 其各镜头一行观察是第 4 问的既有证据：对应工作的 `商业级` 行里，被它覆盖的格直接写
     `有|缺 <它的观察>（runtime review <评审日期>）`，不重新检查；它没覆盖的镜头、没覆盖的工作照常自己看。
   - 其 must-fix 清单里列着的项即仍未关闭的项：凡挡住 in-scope 工作的，按它在文件里写的 id 列进 `Prior evidence` 行；
     等它的建议在 `depends_on` 里写同一个 id。已知的 must-fix 不再占 `R` 号。
   - 过期纪律与 cross-exam 报告相同：产品在"被评提交"之后动过，就记下评审日期、被评提交与看到的差异，
     把受影响的格标成过期，不在这里重判；说一次重跑该评审属于产品自己的 meta-skill 运行。这里的观察永不覆盖那份结论。
   - 该文件自己的"证据限制"并入本报告 `Evidence limits` 的 consequence 子句。
   - 不存在 → 该来源写 `none`。
3. **§2 `depends_on` 定义**：`other R ids, cross-exam G or J ids, or empty` → 增加
   `experience-review must-fix ids`。**Self-check** 的 `the item is not a cross-exam gap restated` 改为
   `the item is not a cross-exam gap or an experience-review must-fix restated`。
4. **§3 模板 `## Prior evidence`** 改为两行（每个来源一行，各自可为 `none`）：

   ```markdown
   ## Prior evidence
   docs/cross-exam/<run>/completion-report.md — G1 blocks JOB1; J2 (gap, no_feedback) blocks JOB1; G2, G3 no job in scope | none
   docs/experience-review/runtime.md (<review date>, <reviewed commit>) — <must-fix id> (next_step) blocks JOB1; lens cells adopted: JOB1 引导, 过程反馈 | none
   ```

   原段里的 `Absent → write \`Prior evidence: none\`` 保持原样（它说的是 cross-exam 来源那一行）。

§1 的 Completion 行 `prior evidence folded in` 已覆盖新来源，不改。

### U3 — 旅程候选增加体验基线来源（R-M6-03）

改 `claude/superstorm/skills/cross-exam/SKILL.md` §1b 第 1 步与 codex 孪生的同一段（文字相同）。
在既有括号 `（registry、spec、README；…task-inventory.json 存在也读，它只是可选数据源）` 之后、
`每条候选写成三元组草稿` 之前插入：

> 同一地位的可选数据源还有两处，存在就读、不存在不算缺：`.allforai/product-concept/product-concept.json` 的
> `requirements[]` 里 `topic == "experience-direction"`、`status == "confirmed"` 的条目（同 id 取最新 `revision`）——
> 用户确认过的体验方向；条目带 `who`/`circumstance` 就直接作三元组前两元，不带就从 `goal`/`scope` 起草，
> `progress` 从它的 `acceptance` 起草。以及 `.allforai/app-design/concept/job-story-spec.json` 的 job stories
> （`audience_ref` → who，`situation`/`trigger`/`frequency` → circumstance，`desired_outcome` → progress）。
> 条目 `auto_decided: true` 的，候选在摆给用户时句末标注"（此方向由模型受托选定）"。

紧随其后的"不另派 agent 读代码……"与 census 失败分支一字不动。标注是候选一句话里的文字：
落到 `journey_candidates[].body` 或读回的三元组时照常是字符串，**不新增字段**，
`schemas.md`（`:237-238`）、ledger schema、渲染器不动。第 2–4 步不改：用户仍要勾选、读回、确认，
体验方向意图不会自动成为旅程。

### U4 — 观察点：受众泄漏（R-M6-04）

**product-review（两份孪生）。** 采用"观察点"而非第六个镜头：§1 Completion 的"五个镜头各写一格"与模板 `商业级` 行不变
（与 M3 把 `audience_leak` 放在五个同名维度之外一致）。

1. Lenses 表在 `4 商业级够不够` 行之后加一行：

   | Question | Where to look | Lineage |
   |---|---|---|
   | 4 商业级够不够 · 受众泄漏 | 最终用户界面里有没有部署方/开发者才该碰的配置（服务地址、访问凭证、密钥、模型选择、环境名、功能开关）。每个设置项只有一个受众：`end-user` / `operator` / `developer`；非 `end-user` 项出现在最终用户可达的界面就是观察，归 `不够商业级`。例外：用户点名的工作本身就是自行接入服务器（自托管类产品） | meta-skill defensive-patterns Pattern J |

2. Self-check 的 `claim: 不够商业级` 一条，括号里的示例清单补一项：
   `…同类状态两套说法、最终用户设置页里要填服务地址或访问凭证…`。

受众词汇取自 `data:settingsAudience`（M4）的三个值；product-review 只用词汇，不读 `.allforai/` 里的设置规格。

**cross-exam lenses（两份，字节相同）。** `细节质量` 行的"泄漏点示例"单元格句末追加：
`；最终用户界面里出现部署方/开发者才该碰的配置（服务地址、访问凭证、模型、环境）——规格给设置项标了受众就对受众查，没标就把"这一项是给谁填的"做成问题牌`。
只改这一格，表结构与其它行不动。

### 数据流与错误处理

本模块没有运行时代码，"错误处理"即散文里的缺席分支，全部沿用既有纪律：

| 情况 | 行为 |
|---|---|
| `docs/experience-review/runtime.md` 不存在 | 该来源写 `none`，第 4 问照常自己看 |
| runtime.md 早于产品现状 | 标过期，不重判，不覆盖其结论 |
| runtime.md 缺某个镜头的观察 | 该格照常本次观察 |
| `.allforai/` 两个数据源不存在或不可解析 | 不是缺口，候选只来自 census 与需求基准；不另派 agent |
| 意图条目不带 `who`/`circumstance` | 从 `goal`/`scope` 起草，第 3 步读回确认 |
| M3 的 SKILL.md 缺失或改名了某维度 | U1 契约测试失败（预期的守卫行为） |

### R-M6-05 — 不破坏既有守卫（如何保证）

- 不触碰 `rule_consistency.py`、`rule-consistency.md`、`prompts/rules.md`（claude 与 codex 两侧）。
- 不触碰 `schemas.md`、`render_report.py`、`ledger_store.py`；不改 `journey_candidates` 等字段名。
- 不新增被 skill 以 `$ROOT/...` 引用的文件，`check_skill_refs.py` 的 REQUIRED 不需要改。
- 不改 `skills/superstorm/SKILL.md`，`test_superstorm_contract.py` 不受影响。
- 不改 `pi/cross-exam/`；不动版本号与 manifest（归 M5）。
- 不触碰任何 meta-skill 热点文件（`validate_bootstrap.py` 等），与 M1/M3/M4 无串行冲突。

### 测试与验收

新增测试仅 U1 一个文件；U2–U4 是散文条款，行为证明归 M5 的思维测试 E7、E8（规格"不做"第三条）。
每个单元提交前跑：

```bash
python3 -m pytest -q shared/scripts/orchestrator/test_experience_lens_parity.py
python3 -m pytest -q claude/superstorm/scripts            # 基线 255 passed
python3 -m pytest -q codex/cross-exam-skill/scripts       # 基线 172 passed
python3 claude/superstorm/scripts/check_skill_refs.py     # OK: all 33 referenced files present
python3 -m pytest -q pi/cross-exam                        # 基线 7 passed
```

双写核对（执行者手工跑，非测试）：

```bash
diff claude/superstorm/skills/product-review/SKILL.md codex/cross-exam-skill/product-review.md   # 仍只有既有 5 处差异
diff claude/superstorm/knowledge/cross-exam/lenses.md codex/cross-exam-skill/lenses.md           # 空
```

U1 先写测试并看它失败（product-review 尚无标识符），再加对应行使其通过。

### Assumptions

- A1 受众泄漏是第 4 问下的观察点，不是第六个镜头格；模板 `商业级` 行保持五格。依据：R-M6-04 称其为"观察点"，
  M3 也把 `audience_leak` 列在五个同名维度之外。
- A2 `docs/experience-review/runtime.md` 是单一路径、每次评审覆盖，"最新一份"即现存那份；must-fix 在其中带 id
  （M3 的 `finding_id`），product-review 原样引用，不另造前缀。若 M3 最终不写 id，就引用其 must-fix 的标题文字——
  `depends_on` 是 Markdown 自由文本，无解析器依赖。
- A3 只采信 `runtime.md`，不读 `design.md`（R-M6-02 只点名 runtime；design 判的不是已交付产品）。
- A4 不读 `experience_proposals[]`（见 Spec corrections 5）。若 M2 的设计让意图条目自带 `who`/`circumstance`，
  U3 的文字已直接受益，无需再改。
- A5 契约测试额外断言"中文名 = 标识符"成对与两份孪生对应行相同，属于 R-M6-01 的收紧，不是新需求。
- A6 `data:settingsAudience` 的消费方式是词汇对齐（三个受众值与"非 end-user 不进最终用户界面"的判据），
  事后评审两个 skill 都不解析 M4 的 JSON 字段。
- A7 对应行放在 Lenses 表之后的独立段落，而不是表内新行，避免与 U4 的表内新行互相挤占。

### File touch list

| 路径 | 动作 | 需求 |
|---|---|---|
| `shared/scripts/orchestrator/test_experience_lens_parity.py` | create | R-M6-01 |
| `claude/superstorm/skills/product-review/SKILL.md` | edit | R-M6-01、R-M6-02、R-M6-04 |
| `codex/cross-exam-skill/product-review.md` | edit（孪生双写） | R-M6-01、R-M6-02、R-M6-04 |
| `claude/superstorm/skills/cross-exam/SKILL.md` | edit（§1b 第 1 步） | R-M6-03 |
| `codex/cross-exam-skill/SKILL.md` | edit（孪生双写，§1b 第 1 步） | R-M6-03 |
| `claude/superstorm/knowledge/cross-exam/lenses.md` | edit（细节质量行） | R-M6-04 |
| `codex/cross-exam-skill/lenses.md` | edit（孪生，保持字节相同） | R-M6-04 |
| —（不改：三个规则资源、`schemas.md`、渲染器、`check_skill_refs.py`、`pi/cross-exam/`、manifest） | none | R-M6-05 |
