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
