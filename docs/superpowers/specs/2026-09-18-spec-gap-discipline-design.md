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

## Detailed design

设计日期 2026-09-18，对照分支 `product-experience-overhaul` @ 80e707e1 的实际文件。下文路径除注明外均相对
`claude/meta-skill/`。

### Spec corrections（对照现状核实的结果）

| 规格说法 | 现状 | 设计取向 |
|---|---|---|
| `check_artifacts.py` 在 `:439-451` 把 `contract_gaps` 列为硬失败 | 字段登记在 `PRODUCTION_GAP_FIELDS`（`:73`），硬失败分支在 `_production_gap_error`（`:400-428`，`contract_gaps` 位于 `:413` 的集合里）。该分支在检查 `ALLOWED_PRODUCTION_GAP_FLAGS` **之前**返回，所以 `allowed_by_production_policy: true` 也放不过去。已用临时项目实测：含该条目的产物 `status_error.field == "contract_gaps"`。 | 不改 `check_artifacts.py`，只加测试；测试同时钉住"放行标志无效"。 |
| Knowledge References 锚定 `defensive-patterns.md#pattern-i` / `#pattern-j` | 标题 `## Pattern I: …` 的自然锚是 `#pattern-i-…`，`#pattern-i` 不存在。 | 在两个新标题上方各放一行显式锚 `<a id="pattern-i"></a>` / `<a id="pattern-j"></a>`，并由契约校验钉住。既有 A–H 不补锚。 |
| "修复回路把它路由回拥有该设计产物的节点" | `execution-repair-loop/SKILL.md:82` 对 `contract_gaps` 只返回 `blocked_by_contract`，自身不回路由。真正的回路由是 `orchestrator-template.md` 的 `needs_diagnosis` → `diagnosis.md` 定位根因节点（`suspected_root_node`）→ `compute_reset_closure.py` 重置根节点及其下游。 | Pattern I 的 Protocol 用这条既有机制表述：`suggested_owner_artifact` 出现在哪个节点的 `exit_artifacts`，那个节点就是根因节点。不改 `execution-repair-loop`、`orchestrator-template.md`、`diagnosis.md`。 |
| `capabilities/ui-design.md:27-29`、`skills/app-design/PACK.md:66-68` | 属实（PACK.md 实为 `:66-69`）。 | 无影响。 |
| 三个子 skill（R-M4-07） | R-M4-03/04 实际改动四个子 skill（settings、topology、handoff、closure-qa）。 | `validate_skills.py` 对整棵 `skills/` 树运行，四个都覆盖。 |
| 多端孪生 | `codex/meta-skill/knowledge/defensive-patterns.md` 是指向 canonical 的符号链接，`codex/.../capabilities/` 是目录符号链接；`node-spec-template.md` 与 `skills/app-design/**` 在 codex/pi 下不存在。 | M4 没有任何手工孪生文件需要双写。 |
| 无 `validate_meta_contracts.py` 的单元测试文件 | 属实（`tests/` 下无引用）。 | 不新建；验收靠脚本退出码，红灯靠实施次序证明（见"测试"）。 |

### 架构

M4 全部是文本契约加一个钉住函数与一个单元用例，没有新脚本、没有新运行时行为。同一条纪律在五个位置各落一次，
位置之间用两个数据形状连接：

```
设计期   settings-spec.settings_groups[].items[]{audience, provisioning, surface, requirement_ref}   ┐ data:settingsAudience
         topology-spec.service_endpoints[]{endpoint_id, audience, provisioning, …}                  ┘
   ↓ program-handoff-generation 原样携带 → handoff.settings_items[] / service_endpoints[] 及每个实现条目的引用
   ↓ app-design-closure-qa：缺 audience / 非 end-user 项出现在界面规格 → missing_contracts + needs_revision
规划期   node-spec "## User-visible decisions"：逐项列界面/设置项 + 来源产物路径（来源取自 data:experienceDesignArtifacts）
执行期   Pattern I：表里没有的用户可见决定 → 不实现，写 contract_gaps[]{kind: unspecified_user_visible_decision,…}  ← data:unspecifiedDecisionGap
         Pattern J：operator/developer 项走 build-time / remote-config / deploy-env，不进最终用户界面
   ↓ check_artifacts.py 既有硬失败 → 节点不完成 → needs_diagnosis → 拥有 suggested_owner_artifact 的设计节点重跑
验证期   product-verify "Audience Leak Check"：走查最终用户可达的设置/配置界面 → contract_gaps 或 code_gaps
```

`data:experienceDesignArtifacts`（M1）的消费方式：Pattern I 的"上游设计产物"与 `suggested_owner_artifact` 的取值域，
以及 node-spec 新节的"来源产物路径"，都指 R-M1-04 的那组路径（应用四个 `.allforai/app-design/...` 产物；游戏的
`.allforai/game-design/game-design-doc.json`——M1 设计已更正为该规范路径，`.allforai/game-design/design/game-design-doc.json`
作为同一产物同样被接受，M4 的文本写规范路径）。M4 只引用路径，不改 M1 的文件。

### 数据形状（冻结接口的具体字段）

**`data:unspecifiedDecisionGap`** —— 节点产物 `contract_gaps[]` 的一项：

```json
{
  "kind": "unspecified_user_visible_decision",
  "where": "mobile/src/screens/Settings — service address input",
  "needed_decision": "How does the end user obtain the service address and credential?",
  "blocking_intent_ids": ["I-003"],
  "suggested_owner_artifact": ".allforai/app-design/spec/permissions-notifications-settings-spec.json"
}
```

五个键全部必填。`blocking_intent_ids` 取节点自身 `requirement_refs[].id`——即
`.allforai/product-concept/product-concept.json` 的 `requirements[]` 里已确认意图的 id（仓库里不存在
`product-intent.json` 这个文件；闭环评审更正）；示例里的 `"I-003"` 只是占位。无法对应时写 `[]` 并在 `needed_decision`
里说明。`suggested_owner_artifact` 是项目相对路径，必须是某个上游节点 `exit_artifacts` 里的路径；找不到拥有者时写
最接近的 `data:experienceDesignArtifacts` 路径。

**`data:settingsAudience`** —— 两处同名字段：

| 字段 | 取值 | 必填条件 |
|---|---|---|
| `audience` | `end-user` \| `operator` \| `developer` | 每个设置项、每个 service endpoint 必填，恰好一个 |
| `provisioning` | `build-time` \| `remote-config` \| `deploy-env` | `audience != "end-user"` 时必填；`end-user` 项不写 |
| `surface` | topology 的 `surface_id`，或 `"none"` | 设置项必填。`audience != "end-user"` 时只能是 `"none"`，或 `surface_type ∈ {admin_console, operator_console, cli}` 的 surface |
| `requirement_ref` | 已确认需求的 id | 仅 Pattern J 例外项：本属 `operator` 的内容（服务地址、凭证）因自托管需求而标为 `end-user` 时必填 |

设置项落在既有的 `settings_groups` 内：`settings_groups[].items[]`，每项 `{setting_id, label, audience, surface,
provisioning?, requirement_ref?}`。`service_endpoints[]` 每项 `{endpoint_id, purpose, consumer_surface_refs,
audience, provisioning, requirement_ref?}`；endpoint 的 `audience` 指"谁提供这个值"，默认 `operator`。

### 单元

#### U1 契约钉住函数（R-M4-07）

- 文件：`scripts/orchestrator/validate_meta_contracts.py`（edit，热点文件）。
- 改动严格两处：在 `validate_public_entrypoint_surface` 之后、`main()` 之前新增
  `validate_spec_gap_discipline_contract(errors: list[str]) -> None`；在 `main()` 的调用序列末尾
  （`validate_public_entrypoint_surface(errors)` 之后）加一行注册。不改任何既有函数与既有字面量。
- 写法仿 `validate_execution_repair_loop_contract`（`:140-176`）：按文件读文本，逐词 `if term not in text`，
  错误信息格式 `"<file>: missing spec-gap discipline term <term>"`；文件缺失时追加一条
  `"<file>: missing"` 并跳过该文件的词表（不抛异常）。
- 钉住表（文件 → 字面量）：

  | 文件 | 字面量 |
  |---|---|
  | `knowledge/defensive-patterns.md` | `<a id="pattern-i"></a>`、`## Pattern I: Specification Gap Escalation`、`<a id="pattern-j"></a>`、`## Pattern J: Audience Isolation`、`unspecified_user_visible_decision`、`needed_decision`、`blocking_intent_ids`、`suggested_owner_artifact`、`` `end-user` ``、`` `operator` ``、`` `developer` ``、`requirement_ref` |
  | `knowledge/node-spec-template.md` | `## User-visible decisions`、`defensive-patterns.md#pattern-i`、`defensive-patterns.md#pattern-j`、`contract_gaps`、`unspecified_user_visible_decision` |
  | `skills/app-design/20-spec/permissions-notifications-settings-spec/SKILL.md` | `audience`、`end-user`、`operator`、`developer`、`provisioning`、`build-time`、`remote-config`、`deploy-env`、`requirement_ref` |
  | `skills/app-design/20-spec/app-surface-topology-spec/SKILL.md` | `service_endpoints`、`provisioning`、`deploy-env` |
  | `skills/app-design/30-generate/program-handoff-generation/SKILL.md` | `settings_items`、`audience`、`provisioning` |
  | `skills/app-design/40-qa/app-design-closure-qa/SKILL.md` | `missing_audience`、`non_end_user_item_in_screen_spec`、`missing_contracts` |
  | `knowledge/capabilities/product-verify.md` | `### Audience Leak Check`、`audience_leak`、`defensive-patterns.md#pattern-j` |

  规格点名的四类（两标题、gap kind、三个受众值、模板新节标题）全部在表内；其余是同一契约在下游的落点，
  防止只改一半。
- 依赖：无（不 import 其它模块）。`ROOT` 为相对路径，脚本必须从仓库根运行（既有约定）。

#### U2 Pattern I / Pattern J（R-M4-01、R-M4-02）

- 文件：`knowledge/defensive-patterns.md`（edit）。在文件末尾（Pattern H 之后）追加 `---` 分隔与两节；
  不动 A–H。文件头部若有模式清单式的概述句，不改（现状没有逐项清单）。
- 两节都用既有四段式，段标题字面量与 Pattern B 一致：`**Trigger condition**:`、`**Protocol**:`、
  `**Key principles**:`、`**Example**:`。正文英文（与全文件一致）。
- **Pattern I: Specification Gap Escalation** 要点：
  - Trigger：implementation 或 UI 节点需要一个用户可见决定——screen、setting、entry point、copy promise、
    permission request、default value——而节点的 `source_inputs`、node-spec 的 `## User-visible decisions`
    与上游设计产物都没有覆盖它。
  - Protocol：(1) 不实现该决定，也不放占位界面；(2) 在节点产物的 `contract_gaps[]` 追加上面的五键条目；
    (3) 其余已覆盖的部分照常完成并照常取证；(4) 产物因非空 `contract_gaps` 不通过
    `check_artifacts.py`，节点不算完成——这是预期结果，不得为了通过而清空字段或改写成 `known_gaps`；
    (5) 路由：`suggested_owner_artifact` 所在 `exit_artifacts` 的节点即根因节点，诊断按
    `suspected_root_node` 重置它与其下游，设计节点补上决定后本节点重跑；`/run` 内不问用户，
    需要用户拍板的产品决定按既有规则成为下一次 `/run` 的 preflight blocker。
  - Key principles：未覆盖 ≠ 可自由发挥；最便宜的实现（加一个输入框）通常就是错误答案；
    一条 gap 只写一个决定；纯内部决定（命名、文件组织、无用户可见后果的实现细节）不触发本模式。
  - Example：服务地址输入框。契约只写 `Authorization: Bearer <token>` 与"可本地启动的服务端"，
    没有任何产物定义最终用户如何得到服务地址与凭证；节点不建"服务设置"页，写出上文那条 JSON，
    `suggested_owner_artifact` 指向 settings spec。例子不出现具体项目名。
- **Pattern J: Audience Isolation** 要点：
  - Trigger：设计、实现或验证任何 configuration item / setting。
  - Protocol：(1) 每项恰好一个受众：`end-user`、`operator`（deploying party）、`developer`；
    (2) 只有 `end-user` 项可以出现在最终用户界面；(3) service endpoints、access credentials、
    vendor keys、model selection、feature flags、environment names 属于 `operator`/`developer`，
    经 `build-time`、`remote-config` 或 `deploy-env` 提供；(4) 唯一例外：已确认的产品需求明确要求最终用户
    自行接入服务器（self-hosted 类产品），此时该项标 `end-user` 且必须带 `requirement_ref`；
    (5) 受众未标注的项按 Pattern I 上报，不得猜。
  - Key principles：判据是"谁有权且有能力给出这个值"，不是"放哪里实现最省事"；
    文案出现"由部署方提供""ask your administrator"即受众错位的信号；operator 面（admin/operator console、CLI）
    不是最终用户界面。
  - Example：一张三行小表（service URL → operator / deploy-env；reminder time → end-user；
    self-hosted server URL with `requirement_ref: REQ-012` → end-user）。

#### U3 node-spec 模板（R-M4-05）

- 文件：`knowledge/node-spec-template.md`（edit，属 bootstrap 语料；只增不删，既有被钉字面量
  `## Attention Contract`、`Repair targets`、`## Effect Verification`、`## Quality Acceptance`、
  `Bootstrap should spend context once`、`execute in pull mode` 等原样保留）。
- 四处改动：
  1. 第 3 行那句之后追加一句：实现界面的节点同样不得省略 `User-visible decisions`。
  2. Attention Contract 的 `Repair targets` 条目：在既有枚举之后追加一句——实现/UI 节点必须把
     `contract_gaps` 列为可发出的字段，其中 `kind: "unspecified_user_visible_decision"` 的形状见
     `defensive-patterns.md#pattern-i`。既有的 `code_gaps … experience_gaps` 枚举不改。
  3. `## Knowledge References` 占位块内追加一段：实现界面的节点必须锚定
     `${CLAUDE_PLUGIN_ROOT}/knowledge/defensive-patterns.md#pattern-i` 与
     `${CLAUDE_PLUGIN_ROOT}/knowledge/defensive-patterns.md#pattern-j`，各带两三句承重句
     （沿用该节既有的"锚 + 承重句"规则）。
  4. 在 `## Guidance` 与 `## Exit Artifacts` 之间新增 `## User-visible decisions` 占位节：
     - 适用：任何实现或修改最终用户可见界面的节点（implementation/UI/mobile/web/game-client）；
       无界面节点写 `Not applicable — no end-user surface` 一行。
     - 内容：一张表 `Decision | Kind (screen/setting/entry/copy promise/permission/default) | Source artifact path | Audience`，
       逐项列出本节点将实现的界面与设置项；来源路径必须是上游设计产物的项目相对路径
       （应用即 M1 的四个 app-design 产物）；设置项的 `Audience` 从 settings spec 抄录。
     - 规则：表是闭集。执行中需要表外的用户可见决定 → Pattern I；表内某设置项受众非 `end-user` 却被要求
       放进最终用户界面 → Pattern J，同样记 `contract_gaps`。bootstrap 写表时找不到来源路径的条目不得写入
       ——那是规划期缺口，回到设计节点的职责里。
- 不为这一节新增确定性校验（见 Assumptions A4）。

#### U4 设置规格与拓扑规格（R-M4-03）

- 文件：`skills/app-design/20-spec/permissions-notifications-settings-spec/SKILL.md`（edit）。
  - Output Contract：在既有必含字段句之后追加一段，定义 `settings_groups[].items[]` 与上面"数据形状"表的四个字段
    及其必填条件；引用 `knowledge/defensive-patterns.md` Pattern J。既有字段清单与 Allowed states 不改。
  - Automatic Validation：追加拒绝条件——缺 `audience`；`audience` 不在三值内；非 `end-user` 项缺
    `provisioning` 或 `provisioning` 不在三值内；非 `end-user` 项的 `surface` 指向最终用户 surface；
    本属 operator 的内容标为 `end-user` 却无 `requirement_ref`。
  - Repair routing：追加"受众无法判定 → 不猜，记 `needs_revision`，路由到 job-story-spec / 产品概念"。
  - Completion Conditions：`FAILED_VALIDATION` 句追加"或任何设置项缺受众"。
- 文件：`skills/app-design/20-spec/app-surface-topology-spec/SKILL.md`（edit）。
  - Output Contract：追加一段 `service_endpoints[]`（顶层数组，可为空数组但字段必须存在；纯客户端应用写 `[]`），
    每项形状见"数据形状"。
  - Automatic Validation：追加——任何 `backend_dependency` 非空的 surface 必须有对应 endpoint 条目；
    endpoint 缺 `audience`/`provisioning` 即拒绝；`audience: "end-user"` 的 endpoint 必须带 `requirement_ref`。
- 两个文件的 frontmatter（`name`、`description`）与 Invocation Contract 的 JSON 块不动，保证
  `validate_skills.py` 继续通过。

#### U5 交接与收口 QA（R-M4-04）

- 文件：`skills/app-design/30-generate/program-handoff-generation/SKILL.md`（edit）。
  - Output Contract：追加一段——handoff JSON 顶层带 `settings_items[]`（从 settings spec 的
    `settings_groups[].items[]` 原样携带 `setting_id`、`audience`、`provisioning`、`surface`、`requirement_ref`）
    与 `service_endpoints[]`（从 topology 原样携带）；实现某设置项或消费某 endpoint 的实现条目在
    `source_refs` 里引用其 id。不得在交接时改写或补猜受众。既有实现条目必含字段句不改。
  - Automatic Validation：追加——settings spec 中每个设置项都出现在 `settings_items[]`；
    非 `end-user` 项不得被分派给 `surface_type` 为最终用户 surface 的实现条目作为界面工作，
    只能作为配置注入工作（`provisioning` 指明方式）。
  - Repair routing：追加"缺 `audience`/`provisioning` → 路由 permissions-notifications-settings-spec 或
    app-surface-topology-spec"。
- 文件：`skills/app-design/40-qa/app-design-closure-qa/SKILL.md`（edit）。
  - Automatic Validation：追加 "Settings audience closure" 一段，两条检查，命中即写入既有
    `missing_contracts[]` 且 `state: "needs_revision"`：
    - `missing_audience`：settings spec 或 handoff 里任一设置项 / service endpoint 缺 `audience`；
    - `non_end_user_item_in_screen_spec`：任一 `audience != "end-user"` 的项出现在
      `screen-requirements-spec.json` 或 UI handoff 的最终用户界面里（例外项凭 `requirement_ref` 放行）。
    每条记录 `{code, item_id, artifact, detail}`。
  - Input Contract：把 permissions/settings spec 从 Optional 句里补一句"存在设置项时为必读"（不移动原句）。
  - Repair routing：追加"两码均路由到 permissions-notifications-settings-spec；界面侧的引用由
    screen-requirements 的拥有 skill 移除"。
  - 不新增 state 值：`needs_revision` 已在 Allowed states 内。

#### U6 验证侧判据（R-M4-06）

- 文件：`knowledge/capabilities/product-verify.md`（edit；codex 侧经目录符号链接自动同步）。
- 在 `### Multi-Client Feature Parity Verification` 之后、`## Rules (Must Preserve)` 之前新增
  `### Audience Leak Check`：
  - 适用：有最终用户界面的模块；non-UI 项目按既有 Skip conditions 跳过。
  - 做法：动态走查最终用户角色可达的每个设置/配置/账户/调试界面（含隐藏入口、长按、开发者菜单），
    逐个输入项与开关对照 settings spec 的 `audience`；判据即 `defensive-patterns.md#pattern-j`。
  - 分类：发现 `operator`/`developer` 性质的项——规格没写受众（或根本没有该项）→ `contract_gaps`；
    规格写了非 `end-user` 而实现仍放进界面 → `code_gaps`。两种条目同形：
    `{kind: "audience_leak", where, item, observed_audience, spec_ref, evidence}`，`evidence` 为截图路径。
    带 `requirement_ref` 的例外项不算泄漏，但要核对引用的需求确实存在。
  - 一句指向：experience-quality critique 的 `audience_leak` 维度采用本节判据（M3 引用方向，M4 不改 M3 文件）。
- `## Rules (Must Preserve)` 追加第 6 条：`Audience isolation` 一句话版。既有 1–5 不改、不重排。
- `## Knowledge References → Phase-Specific` 追加一行 `defensive-patterns.md#pattern-j`。

#### U7 单元用例（R-M4-07）

- 文件：`tests/unit/test_check_artifacts_measurement.py`（edit，文件末尾追加，不动既有用例与导入）。
- 沿用本文件的助手：`project(tmp_path, confirmed=True)`、`write(tmp_path, REPORT, …)`、`measure`、`artifact`。
- 新增一个参数化用例（两个参数值，算一个用例函数）：

  ```python
  @pytest.mark.parametrize("flags", [{}, {"allowed_by_production_policy": True}])
  def test_an_unspecified_user_visible_decision_gap_keeps_the_artifact_incomplete(tmp_path, flags):
      project(tmp_path, confirmed=True)
      gap = {"kind": "unspecified_user_visible_decision", "where": "...", "needed_decision": "...",
             "blocking_intent_ids": ["I-003"],
             "suggested_owner_artifact": ".allforai/app-design/spec/permissions-notifications-settings-spec.json",
             **flags}
      write(tmp_path, REPORT, {"status": "completed", "contract_gaps": [gap]})
      result = measure(tmp_path)
      assert result["all_exist"] is False
      assert result["artifacts"][0]["status_error"]["field"] == "contract_gaps"
      write(tmp_path, REPORT, {"status": "completed", "contract_gaps": []})
      assert "status_error" not in artifact(tmp_path)
  ```

  已在临时项目实测这组断言对现有 `check_artifacts.py` 成立（对照组只断言无 `status_error`，
  不断言 `all_exist`——该夹具下 `all_exist` 还受 freshness 影响）。
- 这是对既有行为的特征测试，写出即绿；它的作用是防回归（有人把 `contract_gaps` 移出硬失败集合，
  或让放行标志对它生效）。

### 数据流与错误处理

- 执行期：节点产物带 `contract_gaps` → `check_artifacts.py` 返回 `status_error{field: "contract_gaps"}` →
  节点不转完成 → 引擎 `needs_diagnosis` → 诊断取 `suggested_owner_artifact` 反查 `exit_artifacts` 得根因节点 →
  重置闭包 → 设计节点补决定 → 实现节点重跑。封顶沿用既有 `diagnosis_history` 的每因 2 次 / 全局 5 次上限，
  超限即 UNRESOLVED 停止并在收尾披露；M4 不新增计数器。
- 设计期：受众无法判定时 settings spec 自身 `needs_revision`，closure QA 兜底；都不进入实现。
- 验证期：`contract_gaps` 走上面的诊断路由；`code_gaps` 走既有 `execution-repair-loop`（三次预算）。
- 校验脚本：被钉文件缺失时报 `"<file>: missing"` 而非崩溃；任何缺词使脚本退出码 1，逐条打印到 stderr。

### 测试与验收

实施次序即红绿证明：先做 U1 并运行 `validate_meta_contracts.py`，应当**失败**并列出全部缺词（红）；
再做 U2–U6，脚本转绿；最后 U7。执行器须在任务报告里贴出红、绿两次输出。

验收命令（全部从仓库根 `/Users/aa/workspace/myskills` 运行）：

```bash
python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py
python3 claude/meta-skill/scripts/orchestrator/validate_skills.py claude/meta-skill/skills
python3 claude/meta-skill/scripts/orchestrator/validate_generalization_boundaries.py
python3 -m pytest -q claude/meta-skill/tests/unit/test_check_artifacts_measurement.py
python3 -m pytest -q claude/meta-skill/tests/unit/test_check_artifacts.py claude/meta-skill/tests/unit/test_validate_skills.py
```

前三条退出码 0；第四条全绿且比基线多 2 个用例项；第五条是邻近回归。不运行 `pytest pi/meta-skill` 或
`pytest codex/meta-skill` 目录；4 个既有失败（`test_decision_gate … fresh_evidence`、
`test_evidence_freshness … cannot_claim_completion`）不在上述文件内，不触碰。

### Assumptions

- A1 Pattern 标题定为 `Pattern I: Specification Gap Escalation`、`Pattern J: Audience Isolation`；正文用英文，
  与 `defensive-patterns.md` 全文一致。
- A2 显式 HTML 锚 `<a id="pattern-i"></a>` / `<a id="pattern-j"></a>` 让规格要求的短锚真实可达。
- A3 设置项放在 `settings_groups[].items[]`；`surface` 取 topology `surface_id` 或 `"none"`；
  operator 面限定为 `admin_console`、`operator_console`、`cli` 三种 `surface_type`。
- A4 不为 node-spec 的 `## User-visible decisions` 新增 `validate_bootstrap.py` 确定性检查：规格未要求，
  且那是 M1/M3 的串行热点文件。M4 因而不触碰 `validate_bootstrap.py`、`bootstrap-planning.md`、
  `test_validate_bootstrap.py`、`skills/bootstrap/SKILL.md`；热点文件只碰 `validate_meta_contracts.py`。
- A5 handoff 用顶层 `settings_items[]` + `service_endpoints[]` 携带受众，实现条目经 `source_refs` 引用 id，
  不给实现条目的必含字段清单加新必填键。
- A6 closure QA 的两个检查码 `missing_audience`、`non_end_user_item_in_screen_spec` 与 product-verify 的条目
  `kind: "audience_leak"` 是产物内的取值，不是注册表接口；`audience_leak` 与 M3 的维度名同词，便于对照。
- A7 回路由只用既有诊断机制表述，不改 `execution-repair-loop/SKILL.md`、`orchestrator-template.md`、
  `diagnosis.md`（后两者有 codex 手工孪生，属 M5）。
- A8 钉住表超出规格点名的四类，覆盖四个子 skill 与 product-verify 的落点词；均为本模块自己写入的词。
- A9 U7 用 `parametrize` 覆盖"放行标志无效"，仍是规格所说的一个用例函数。
- A10 不改 `skills/app-design/PACK.md`、`capabilities/app-design.md`、`capabilities/ui-design.md`；
  游戏侧 UI 规格不动（规格"不做"）。

### File touch list

| 路径（相对仓库根） | 动作 | 需求 |
|---|---|---|
| `claude/meta-skill/knowledge/defensive-patterns.md` | edit（末尾追加两节） | R-M4-01、R-M4-02 |
| `claude/meta-skill/skills/app-design/20-spec/permissions-notifications-settings-spec/SKILL.md` | edit | R-M4-03 |
| `claude/meta-skill/skills/app-design/20-spec/app-surface-topology-spec/SKILL.md` | edit | R-M4-03 |
| `claude/meta-skill/skills/app-design/30-generate/program-handoff-generation/SKILL.md` | edit | R-M4-04 |
| `claude/meta-skill/skills/app-design/40-qa/app-design-closure-qa/SKILL.md` | edit | R-M4-04 |
| `claude/meta-skill/knowledge/node-spec-template.md` | edit（一节新增 + 三处追加句，共四处） | R-M4-05 |
| `claude/meta-skill/knowledge/capabilities/product-verify.md` | edit（一节新增 + Rule 6 + 一行引用） | R-M4-06 |
| `claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py` | edit（一个新函数 + `main()` 一行） | R-M4-07 |
| `claude/meta-skill/tests/unit/test_check_artifacts_measurement.py` | edit（末尾追加一个用例） | R-M4-07 |

无新建文件；`check_artifacts.py`、`validate_skills.py` 不改；codex/pi 下无需双写。
