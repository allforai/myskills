# M4 spec-gap-discipline — 规格留白纪律

总览：`2026-09-18-product-experience-overhaul-overview.md`。依赖 M1（`data:experienceDesignArtifacts`）。

## 问题

ink-scent 的契约只写了 `Authorization Bearer INK_SCENT_ACCESS_TOKEN; one configured token is one client`
和"可本地启动的 AI 服务端"，从未定义最终用户如何得到服务地址与凭证。实现节点自行填洞，把部署方配置做成了
最终用户的设置页（`mobile/src/ServiceSettings.tsx`，文案还写着"配置由部署方提供"）。验证只对契约核对，放行。

探查确认仓库里没有任何规则覆盖这两件事：

- "实现节点不得自行发明规格未覆盖的用户可见决定"——最近的只有 `capabilities/ui-design.md:27-29`
  （"Do not invent screens … return `UPSTREAM_DEFECT`"）与 `skills/app-design/PACK.md:66-68`，都不约束实现节点。
- "部署/基础设施配置不得出现在最终用户界面"——无任何条目。

## 需求

- **R-M4-01 Pattern I：规格留白上报，不自行发明。** `knowledge/defensive-patterns.md` 新增 Pattern I，
  沿用既有四段式（Trigger condition / Protocol / Key principles / Example）。触发：实现或 UI 节点需要一个
  用户可见的决定（界面、设置项、入口、文案承诺、权限请求、默认值），而其 `source_inputs` 与上游设计产物都没有
  覆盖。协议：不实现该决定；在节点产物的 `contract_gaps[]` 追加
  `{kind: "unspecified_user_visible_decision", where, needed_decision, blocking_intent_ids,
  suggested_owner_artifact}`；其余已覆盖部分照常完成。修复回路把它路由回拥有该设计产物的节点。
  例子用服务地址输入框。
- **R-M4-02 Pattern J：受众隔离。** 新增 Pattern J。每个配置项/设置项有且只有一个受众：
  `end-user`、`operator`（部署方）、`developer`。只有 `end-user` 项可以出现在最终用户界面。
  服务端点、访问凭证、供应商密钥、模型选择、功能开关、环境名属于 `operator`/`developer`，通过构建期配置、
  远程配置或部署环境提供。例外只有一种：已确认的产品需求明确要求最终用户自行接入服务器
  （自托管类产品），此时该需求的 id 必须写在设置项上。
- **R-M4-03 设置规格携带受众。** `skills/app-design/20-spec/permissions-notifications-settings-spec/SKILL.md`
  的输出 schema：每个设置项必填 `audience`；`audience != "end-user"` 的项必填 `provisioning ∈
  {build-time, remote-config, deploy-env}`，且 `surface` 不得为最终用户界面；R-M4-02 的例外项必填
  `requirement_ref`。`skills/app-design/20-spec/app-surface-topology-spec/SKILL.md` 增加
  `service_endpoints[]`，每项含 `provisioning` 与 `audience`。
- **R-M4-04 交接与 QA 传递。** `30-generate/program-handoff-generation` 把设置项的 `audience` 与
  `provisioning` 带进 `.allforai/app-design/handoff/program-development-node-handoff.json`；
  `40-qa/app-design-closure-qa` 新增检查：任何缺 `audience` 的设置项、任何非 `end-user` 项出现在界面规格中，
  记为 `missing_contracts`，状态 `needs_revision`。
- **R-M4-05 node-spec 模板。** `knowledge/node-spec-template.md`：实现界面的节点必须含
  "User-visible decisions" 一节，逐项列出本节点将实现的界面/设置项及其来源产物路径；Knowledge References
  必须锚定 `defensive-patterns.md#pattern-i` 与 `#pattern-j`。Repair targets 清单补
  `contract_gaps`（`unspecified_user_visible_decision`）。
- **R-M4-06 验证侧。** `knowledge/capabilities/product-verify.md` 增加一条检查 "audience leak"：
  走查最终用户可达的每个设置/配置界面，发现 `operator`/`developer` 项即记 `contract_gaps`
  （若规格本来就没写受众）或 `code_gaps`（规格写了、实现违反）。M3 的 `audience_leak` 维度引用本条判据。
- **R-M4-07 契约钉住与测试。** `validate_meta_contracts.py` 新增
  `validate_spec_gap_discipline_contract(errors)`：钉住 Pattern I/J 标题、
  `unspecified_user_visible_decision`、三个受众值、node-spec 模板的新节标题。
  `check_artifacts.py` 已把 `contract_gaps` 列为硬失败（`:439-451`），增加一个单元用例证明
  含 `unspecified_user_visible_decision` 的产物不通过。`validate_skills.py` 对改动后的三个子 skill 仍通过。

## 接口

- 暴露：`data:settingsAudience`（设置项与服务端点上的 `audience`/`provisioning` 字段）、
  `data:unspecifiedDecisionGap`（`contract_gaps[]` 里的 `unspecified_user_visible_decision` 条目形状）。
- 消费：`data:experienceDesignArtifacts`（M1）。

## 不做

- 不写扫描应用源码找"可疑输入框"的静态分析器；泄漏由设计规格、交接、评审与验证四处把关。
- 不改游戏侧的 UI 规格。

## 验收

```bash
python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py
python3 claude/meta-skill/scripts/orchestrator/validate_skills.py claude/meta-skill/skills
python3 -m pytest -q claude/meta-skill/tests/unit/test_check_artifacts_measurement.py
```
