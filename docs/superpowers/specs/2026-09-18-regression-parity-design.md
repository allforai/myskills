# M5 regression-parity — 回归与多端一致

总览：`2026-09-18-product-experience-overhaul-overview.md`。依赖 M1、M2、M3、M4、M6 全部完成。

## 事实基础（探查结论）

- `claude/meta-skill/` 是 canonical。`codex/meta-skill/{scripts,tests}` 与
  `pi/meta-skill/scripts` 是符号链接；`codex/meta-skill/knowledge/` 下的 `capabilities/` 与 13 个理论文件
  （含 `defensive-patterns.md`、`consumer-maturity-patterns.md`、`journey-emotion-schema.md`）也是符号链接。
  这些改动自动到达 Codex/Pi。
- **手工孪生、会漂移**：`codex/meta-skill/{SKILL.md,AGENTS.md,execution-playbook.md,skills/bootstrap.md}`、
  `codex/meta-skill/knowledge/{orchestrator-template.md,flow-template.py}`、
  `pi/meta-skill/skills/bootstrap/SKILL.md`、`pi/meta-skill/knowledge/orchestrator-template.md`。
  替换规则：Codex 本地文件不得出现 `${CLAUDE_PLUGIN_ROOT}`；Pi 模板不得提 `.claude/commands/run.md` 或
  `.codex/commands/run.md`；Pi 无 `AskUserQuestion`。
- `bootstrap-planning.md`、`bootstrap-audits.md`、`product-intent-confirmation.md`、`suppress-rules.md`、
  `node-spec-template.md` 只存在于 claude 树，Codex/Pi 经 canonical 根按路径读取。
- `check_codex_meta_skill_parity.py:104-111` 的 `disclosed_protocols` 不含
  `product-intent-confirmation.md`。
- 无 CI；`.githooks/pre-commit` 跑快速门，meta-skill 全量套件（约 6 分钟，1202 例，4 个既有失败）不在其中。
- 直接以目录方式 `pytest pi/meta-skill` 或 `pytest codex/meta-skill` 会因符号链接收集冲突失败，必须点名文件。
- 版本：`meta-skill 0.19.2`、`superstorm 0.42.2`；版本字符串**原地编辑**，不得重序列化 JSON；
  根 marketplace、各 `plugin.json`、各 `marketplace.json` 必须一致（`test_package_manifests.py`）；
  `codex/meta-skill/SKILL.md` 版本须为 `<claude bootstrap SKILL.md version>-codex.<n>`。

## 需求

- **R-M5-01 ink-scent 形状的回归夹具（确定性）。** 新增
  `claude/meta-skill/tests/fixtures/consumer-learning-app/`：
  - `bad-workflow/`：脚本化的 profile + workflow + node-specs，复刻 ink-scent 的形状——
    `task_route: new-product`、Expo 移动应用 + 服务端、13 个节点、零体验设计节点、无体验方向意图、
    无质量门。
  - `good-workflow/`：同一产品，含体验方向意图（`select` 产生）、体验设计节点、design/runtime 两次评审、
    修复回路。
  新测试 `tests/unit/test_consumer_product_regression.py`（host 参数化）：`bad-workflow` 被三个公共门拒绝，
  且阻断码集合**至少**包含 `missing_experience_design_node`、`missing_experience_gate`、
  `ui_product_without_experience_direction`；`good-workflow` 三个门全过。
  夹具是供门检查的显式产物，不是语义规划器的替身（沿用 `test_bootstrap_scope.py:1-4` 的声明）。
- **R-M5-02 模型运行夹具（答案键）。** 新增 `tests/prompts/new-product-consumer-app.md` 与
  `tests/expected/new-product-consumer-app-expected.json`，形状对齐 `specialization.md` 那一对：
  受测方扮演 bootstrap 面对一个消费级学习应用的 new-product 请求。答案键以**产物路径**断言
  （工作流须含产出 `.allforai/app-design/spec/user-flow-spec.json` 等的节点、含两阶段评审、
  profile 的 `experience_priority.mode == "consumer"`），不以节点名断言。另加 `-codex` 变体。
- **R-M5-03 思维测试战役。** 先冻结判据，再运行：
  - 判据：`fixtures/product-experience/thought-tests.json`（`method`、`subject_under_test`、`cases[]`），
    claude 与 codex 平台的 case 混排。至少覆盖：
    `E1` 用户说"碎片化学习"→ 提案不得直译成时长选择器/题型清单；
    `E2` 用户说"你定"→ 记 `delegate`，不得当作沉默处理，也不得在无提案时委托；
    `E3` 用户什么都没选 → 不得自行确认体验方向；
    `E4` 实现节点缺"服务地址从哪来"的规格 → 上报 `unspecified_user_visible_decision`，不造输入框；
    `E5` CLI 项目 → `mode: none`，不规划体验设计与质量门；
    `E6` 游戏项目 → 创意评审节点存在且收尾受其阻断；
    `E7` product-review 面对已有 `docs/experience-review/runtime.md` → 采信，不重评；
    `E8` cross-exam 旅程候选含体验方向来源并标注受托选定。
  - 每个 case 一个 fresh-context 受测代理；packet 放仓库外；隔离性从运行轨迹核对，不凭自述。
  - 记录：`docs/validation/product-experience-thought-tests.md` +
    `docs/validation/product-experience-thought-tests/{evidence.json,responses.md}`，含
    `## 尚未验证`。失败的 case：修 skill 文本、加一行契约钉住新句、以 `b` 后缀在修后的文本上重测。
- **R-M5-04 Codex/Pi 孪生同步。** 在 `codex/meta-skill/skills/bootstrap.md`、
  `pi/meta-skill/skills/bootstrap/SKILL.md` 补入：`experience_priority` 的设置、产品路线的设计知识加载、
  `experience-direction` 话题与 `propose/select/delegate`（Pi 无 `AskUserQuestion`，用其原生提问方式）、
  体验质量门。在 `codex/meta-skill/knowledge/orchestrator-template.md`、
  `pi/meta-skill/knowledge/orchestrator-template.md`、`codex/meta-skill/knowledge/flow-template.py`
  的完成输出中打印委托清单（`product_intent.py --delegations`）。遵守各自替换规则。
  `check_codex_meta_skill_parity.py` 的 `disclosed_protocols` 加入 `product-intent-confirmation.md`。
  `pi/meta-skill/test_contract.py` 增加对新增 Pi 文本的最小钉住（话题名、`delegate`、`--delegations`）。
- **R-M5-05 全量验证与基线对比。** 运行并记录：
  ```bash
  python3 -m pytest -q claude/meta-skill/tests/unit          # 期望：失败数 == 4 且为同四个既有失败
  python3 -m pytest -q claude/superstorm/scripts
  python3 -m pytest -q codex/cross-exam-skill/scripts
  python3 -m pytest -q shared/evidence-engine
  python3 -m pytest -q shared/visual-acceptance
  python3 -m pytest -q shared/scripts/orchestrator shared/keep-code-simple pi/cross-exam
  python3 -m pytest -q pi/meta-skill/test_contract.py codex/meta-skill/test_flow.py codex/meta-skill/test_install.py
  python3 shared/scripts/orchestrator/check_codex_meta_skill_parity.py
  python3 claude/superstorm/scripts/check_skill_refs.py
  ```
  第五个失败即本次回归。结果写入运行目录的验证记录。
- **R-M5-06 版本与发布提交。** 次版本号递增（新增能力，向后兼容）：meta-skill `0.19.2 → 0.20.0`，
  superstorm `0.42.2 → 0.43.0`；同步根 marketplace、两份 `plugin.json`、两份 `marketplace.json`、
  `pi/meta-skill/package.json`（`0.20.0-pi.1`）、`claude/meta-skill/SKILL.md` 与
  `skills/bootstrap/SKILL.md` frontmatter、`codex/meta-skill/SKILL.md`（`<新值>-codex.1`）。
  `pi/cross-exam/package.json` 仅当 Pi 包内容变化时才动。原地编辑版本字符串。
  `release:` 提交正文记录验证数字与既有失败所在的上游 SHA。是否 push 由授权信封决定。
- **R-M5-07 文档。** `CLAUDE.md`（仓库根）"Which entry for which situation" 与 meta-skill 结构说明中补一句
  体验方向/质量门；`README.md` 如有 bootstrap 流程描述则同步。不新增 CHANGELOG（仓库无此惯例）。

## 接口

- 暴露：`data:regressionFixtures`。
- 消费：`api:validateExperienceDesignCoverage`（M1）、`api:productIntentPropose`、
  `api:productIntentSelect`、`api:productIntentDelegate`、`data:delegationDisclosure`（M2）、
  `api:validateExperienceGateFlow`、`data:experienceCritiqueReport`（M3）、
  `data:unspecifiedDecisionGap`（M4）。

## Reality gate 候选

- **真实宿主对话质量。** 思维测试是模拟决策，不是真实宿主验收。"真实 Claude Code / Codex / Pi 会话里，
  bootstrap 面对真实用户产出了好的体验方向并据此交付了体验良好的产品"在本环境无法自动证明。
  runbook：用改造后的版本对 ink-scent 的原始请求重跑 `/bootstrap` → `/run`，再跑 `/product-review`，
  对照本轮诊断的三个症状（直译、无设计节点、服务地址输入框）。

## 不做

- 不新增 `tests/brain-test/` 快照（那是人工驱动运行的留档，需真实宿主）。
- 不修 4 个既有失败测试。

## 验收

见 R-M5-05 的命令组，加：

```bash
python3 -m pytest -q claude/meta-skill/tests/unit/test_consumer_product_regression.py
python3 -m pytest -q claude/superstorm/scripts/test_package_manifests.py
```

## Detailed design

设计日期 2026-09-18。对照的代码状态：分支 `product-experience-overhaul` @ `80e707e1`（M1–M4、M6 尚未落地；
本模块在它们之后执行，凡依赖它们产出的地方都写明"以落地后的文件为准"）。

### Spec corrections（探查与现实不符之处，按现实设计）

1. **frontmatter 版本不是 0.19.2。** `claude/meta-skill/SKILL.md:7,10`、
   `claude/meta-skill/skills/bootstrap/SKILL.md:4` 现为 `0.19.1`；`codex/meta-skill/SKILL.md:10,13` 现为
   `0.19.1-codex.2`。manifest（根 marketplace、两份 plugin.json、两份 marketplace.json）才是 `0.19.2`，
   `pi/meta-skill/package.json` 是 `0.19.2-pi.1`。R-M5-06 的目标值不变（全部到 `0.20.0` / `0.20.0-codex.1` /
   `0.20.0-pi.1`），只是 frontmatter 的起点是 `0.19.1`，且 `SKILL.md` 里各有一行 `# Meta-Skill v…` 标题要同改。
2. **`disclosed_protocols` 在 `check_codex_meta_skill_parity.py:102-109`**（规格写 104-111），循环在 `:110`。
3. **三个公共门不会在同一次调用里报全三个码。** `validate_bootstrap.py` 的 `main()`（`:2151-2175`）
   在 `validate_scope` 有错时跳过全部跨节点检查；`check_decision_inputs.py:57-75` 只调 `validate_scope`，
   从不调 `structural_gate_blockers`。因此 ink-scent 形状的工作流上：
   `check_decision_inputs.py` 与 `validate_bootstrap.py` 只会报 M2 的 `ui_product_without_experience_direction`；
   只有 `validate_unattended_readiness.py`（`:578-615`，结构门与 scope 不互相短路）能同时报三个码。
   R-M5-01 的"阻断码集合"按**三个门输出的并集**断言，并另外断言 readiness 报告单独含全部三个码。
4. **`product_intent.py plan` 自己就会拒绝 bad-workflow。** `plan` 在写盘前调 `validate_scope`（`:1110-1112`）。
   R-M2-06 落地后，consumer profile + 无体验方向意图的图无法经公共 CLI 生成。夹具构建需绕过这道前门
   （见 U1 的 `force_past_front_door`），并把"前门也关着"作为一条断言。
5. **Pi 适配器里出现 `${CLAUDE_PLUGIN_ROOT}` 是合法的**（`pi/meta-skill/test_contract.py:63` 反而钉住它，
   作为"解析为 canonical-root"的说明）。禁用 `${CLAUDE_PLUGIN_ROOT}` 的只有 Codex 本地文件
   （parity `:129`）。Pi 的禁词只针对 Pi **模板**（`test_contract.py:87-89`）。
6. **思维测试判据的位置是仓库根 `fixtures/product-experience/`**（与 `fixtures/product-review/`、
   `fixtures/pi-session-model/` 同级），不在 `claude/meta-skill/tests/fixtures/` 下。

### 架构

M5 是收口模块，不新增运行时代码路径，只有四类产出：

```
U1 回归夹具 + 测试      tests/fixtures/consumer-learning-app/**  →  tests/unit/test_consumer_product_regression.py
U2 模型运行夹具（答案键） tests/prompts/*.md + tests/expected/*.json          （静态，无执行方）
U3 思维测试战役          fixtures/product-experience/**  →  docs/validation/product-experience-thought-tests*
U4 孪生同步              codex/pi 适配器 + 三个模板 + parity 脚本 + Pi 契约测试
U5 全量验证              只跑命令、写记录，不改源码
U6 版本                  9 个文件的版本字符串原地替换 + release 提交正文草稿
U7 文档                  CLAUDE.md、README.md
```

执行次序：U4 → U1 → U2 → U3（U3 的失败修复可能回改 skill 文本）→ U7 → U6 → U5（U5 必须最后，
对着最终文本与最终版本号跑；U6 的提交正文里的数字取自 U5，故 U6 先改版本、U5 跑完后回填正文草稿）。

### U1 回归夹具与确定性测试（R-M5-01，暴露 `data:regressionFixtures`）

**做什么。** 提供一份 ink-scent 形状的脚本化 bootstrap 对话（bad）与同一产品的正确对话（good），
经**复制到生成项目里的公共 CLI**重放，证明三个公共门对前者拒绝、对后者放行。

**夹具不是静态的 `.allforai/` 快照，而是重放输入。** 理由：通过门的工作流依赖 `product_intent.py`
写出的 journal 引用、`product_baseline`、节点投影（`decision_inputs/product_goals/acceptance`）、
plan-confirmation 与 freshness 合约；手写这些等于在夹具里复制一份 `plan` 的实现，M2 一改就静默失真。
沿用 `test_acceptance_allocation.py:29-83`（`frozen_new_product` / `plan_request` / `accepted_plan`）的做法，
只是把请求体放进 JSON 文件。

目录（`claude/meta-skill/tests/fixtures/consumer-learning-app/`）：

| 文件 | 内容 |
|---|---|
| `README.md` | 两句话：来源（ink-scent 2026-09-14~16 new-product 运行的形状，非其内容拷贝）；"显式产物，不是语义规划器替身" |
| `bad-workflow/profile.json` | 合并进 `bootstrap-profile.json` 的字段：`task_goal`、`architecture_pattern`、`modules`（Expo 移动端 + Node 服务端，键名取 `_profile_has_mobile_ui_module` `validate_bootstrap.py:626-676` 能识别的形状）、`experience_priority: {"mode":"consumer","reason":…}` |
| `bad-workflow/dialogue.json` | 有序的 `product_intent.py` 请求数组：`draft`（route `new-product`，`origin: user-request`，六个旧话题；"碎片化学习"被直译为"2/5/10 分钟时长选择 + 题型清单"的 `acceptance`）→ `decide`（全部 `confirm`）→ `freeze`（`exclude: {"gap-experience-direction": "<当时无此话题>"}`，确切 gap id 以 M2 落地后的 `resume` 输出为准） |
| `bad-workflow/plan.json` | `plan` 请求：**13 个节点**（1 契约、1 内容库、6 implement、其余 verify/repair；实现节点把 `experience` 写进自己的 `responsibilities`——ink-scent 正是这样让"阶段全覆盖"通过的），无任何节点产出 `.allforai/app-design/**`，无节点引用 `experience-quality-critique`；每节点含 `body`（≥ `ATTENTION_CONTRACT_BODY` 的术语） |
| `bad-workflow/readiness-spec.json` | `_minimal_project` 同形，`required_repair_loops: []` |
| `good-workflow/profile.json` | 同 bad |
| `good-workflow/dialogue.json` | `draft`（同六话题）→ `propose`（3 条方向、1 条推荐，字段按 R-M2-02；`comparable` 为 `{product, approach}` 对象，见 M2 设计 A2）→ `decide`（六话题 `confirm` + `{"operation":"select","proposal_id":…,"reason":…}` + 对 `gap-experience-direction` 的 `{"operation":"answer",…}`；动作键是 `operation`，见 `product_intent.py:1217`）→ `freeze`（include 含由 select 生成的体验方向意图 `experience-direction-<proposal_id>`） |
| `good-workflow/plan.json` | 同一产品：体验设计节点（`exit_artifacts` 覆盖 R-M1-04 四个应用产物路径）→ design 阶段评审 → 界面实现节点（传递 `hard_blocked_by` 设计评审）→ verify → runtime 阶段评审 → 收尾节点（`hard_blocked_by` runtime 评审）→ 两个修复节点。节点**不用** `capability: "app-design"` 也不用 `APP_DESIGN_REQUIRED_NODES` 里的 id，避免触发 `validate_app_design_flow`（`:1257-1320`）的固定六节点要求——R-M1-04 的契约是产物路径不是节点名 |
| `good-workflow/readiness-spec.json` | `required_repair_loops` 两条：design 评审回路、runtime 评审回路（形状取 `test_validate_unattended_readiness.py:122-169` 的 `_repair_loop`，`qa_node_ids` 含两个评审节点） |

约束：每个冻结意图必须有消费节点，且这些节点的 `responsibilities` 并集覆盖六个阶段
（`product_intent.py:736-741`），否则 `plan` 以 "lacks applicable full-process responsibilities" 拒绝。

与上游各门的对接约束（闭环评审补充；都是夹具形状，不改上游代码）：

- **界面实现节点必须被 M1 的识别函数认出。** M1 的 `_ui_implementation_nodes` 要求节点 `capability ∈ {implement, translate,
  ui-forge}` 或 `responsibilities` 含 `implementation`，**并且**节点条目/`body` 命中界面词项（`screen`、`frontend`、`react native`、
  `界面`、`页面`，或 profile 中 `role ∈ {frontend, mobile}` 模块的 `"<path>/"`）。bad 与 good 两份计划的移动端实现节点的 goal/`body`
  都要写出 `screen` 与模块路径（如 `mobile/`）。否则 M1 第 7 步、M3 触发条件 3 直接返回空，`missing_experience_design_node` /
  `missing_experience_gate` 不会出现，测试会因夹具形状而不是上游缺陷失败。
- **评审节点按 `exit_artifacts` 被认出（M3 U3）。** good 计划的 design 评审节点 `exit_artifacts` 含
  `.allforai/app-design/qa/experience-quality-critique-design.json`（及 `.html`、`docs/experience-review/design.md`），runtime 评审节点含
  `…-runtime.json`（及 `.html`、`docs/experience-review/runtime.md`）；两个评审节点的 id 都在某条回路的 `qa_node_ids` 里，
  回路的 closure 节点直接 `hard_blocked_by` 该评审节点与 repair 节点（`repair_loop_declaration_findings` 的既有要求）。
  节点 id 不含 `product-review` / `cross-exam`。
- **收尾节点的 capability** 取 M3 `EXPERIENCE_GATE_CLOSURE_CAPABILITIES` 之一（首选 `pipeline-closure-verify`），使
  `closure_not_blocked_by_experience_gate` 这条检查在 good 图上真正被走到；若该 capability 牵出其它校验器的固定要求而夹具
  成本过高，退回普通 capability 并在 README 注明该码只由 M3 自己的单测覆盖。
- **Expo 移动模块会同时触发既有的 `validate_mobile_ui_coverage`**（`_profile_has_mobile_ui_module` +
  `_required_mobile_ui_platforms` 见 "expo" 即要求 react-native 平台 UI 自动化节点）。good 计划的 verify 段必须含一个满足
  `_ui_node_present(…, "react-native")` 的 UI 自动化节点（带 runner evidence 措辞），否则 `validate_bootstrap.py` 不会 exit 0。
  bad 计划可含可不含（断言是 ⊇）。
- **体验方向意图的 id** 是 `experience-direction-<proposal_id>`（M2 设计 A1）；good 的 `freeze.include` 与各消费节点的
  `intent_ids` 用这个派生 id，`decide` 批次里在 `select` 之后追加 `{"operation":"answer", …}` 关闭
  `gap-experience-direction`（M2 设计 A3：`select` 不自动关缺口，漏写则 `freeze` 失败）。
- **共享夹具 `project()`** 在 M1 落地后自带 `experience_priority: {"mode": "none", …}`；`build` 合并 `profile.json` 时以夹具的
  `consumer` 覆盖它。`force_past_front_door` 的"临时移除"等价于临时保持 `none`，两种写法都可。

**测试文件** `claude/meta-skill/tests/unit/test_consumer_product_regression.py`。风格：模块 docstring 沿用
`test_bootstrap_scope.py:1-4` 的声明；helper 从既有模块导入，不复制：
`from .test_bootstrap_scope import confirm_plan, gate, project, publish_contract, write`、
`from .test_product_intent_session import invoke`。host 参数化 `["claude","codex"]`（`project(host=…)`
已按 host 选择脚本来源）。

内部 helper（本文件私有）：

```python
FIXTURE = Path(__file__).resolve().parents[1] / "fixtures/consumer-learning-app"
GATES = ("validate_bootstrap.py", "check_decision_inputs.py", "validate_unattended_readiness.py")

def build(root, host, *, dialogue, plan, readiness, force_past_front_door=False) -> dict
    # project(root, host=host, source_inputs=None) 取得复制好的脚本；删掉它留下的 local-change 残留
    # (orders.py、local-requirements.json)；逐条 invoke(dialogue)；把 profile.json 合并进 profile；
    # 写 readiness-spec；invoke(plan)；confirm_plan(stage="plan-projection")；
    # 对每个声明 source_inputs 的节点 publish_contract。
    # force_past_front_door=True：先断言带 consumer profile 的 plan 被拒且 stdout 含
    # ui_product_without_experience_direction；再临时移除 profile.experience_priority、plan、写回。
def codes(root) -> dict[str, set[str]]
    # 每个门跑一次。validate_bootstrap.py：解析 stdout JSON，errors[i].split(":")[0]；
    # check_decision_inputs.py：正则 r"^\s+- (\w+):" 取 stdout；
    # validate_unattended_readiness.py --write-report：读 unattended-run-readiness.json 的 blockers[].code。
```

用例（均 host 参数化）：

| 用例 | 构建 | 断言 |
|---|---|---|
| `test_ink_scent_shaped_workflow_is_refused_at_every_public_gate` | bad 对话 + bad 计划，`force_past_front_door=True` | 三个门 `returncode == 1`；三门码的并集 ⊇ `{missing_experience_design_node, missing_experience_gate, ui_product_without_experience_direction}`；readiness 报告单独 ⊇ 同一集合；`check_decision_inputs` 的码含 `ui_product_without_experience_direction`；工作流节点数 == 13 且无节点 `exit_artifacts` 以 `.allforai/app-design/` 开头（守住夹具自身形状） |
| `test_chosen_direction_does_not_excuse_a_graph_without_design_or_gate` | good 对话 + bad 计划（测试内把体验方向意图 id 追加到 bad 计划各实现节点的 `intent_ids`，使冻结范围有消费者） | `plan` 成功（scope 已干净）；`validate_bootstrap.py` **自身** `returncode == 1` 且码 ⊇ `{missing_experience_design_node, missing_experience_gate}`——补上 Spec correction 3 指出的盲区 |
| `test_designed_and_gated_workflow_passes_every_public_gate` | good 对话 + good 计划 | 三门 `returncode == 0`、`stderr` 为空、readiness `status == "ready"`；冻结范围内恰有一条 `topic == "experience-direction"`、`origin == "model-proposal"` 的意图；重跑三门前后项目文件字节不变（沿用 `test_bootstrap_scope.py:217-221`） |

**依赖。** `api:validateExperienceDesignCoverage`（M1，须已注册进 `structural_gate_blockers`）、
`api:productIntentPropose` / `api:productIntentSelect`、R-M2-06 的 scope 码（M2）、
`api:validateExperienceGateFlow`（M3）。`api:productIntentDelegate` 与 `data:delegationDisclosure`
由 U3（E2/E8/E9）与 U4 消费，不在 U1 重复 M2 自己的单测。

**错误处理。** 任何 `invoke`/`publish_contract` 非零即 `assert` 带 `(stdout, stderr)` 失败，不吞。
若某个期望码缺失，失败信息打印三门的完整码集，便于判断是夹具形状不对还是上游模块未注册进
`structural_gate_blockers`。后者是上游模块缺陷：M5 执行方**不得**为过测试去改
`validate_bootstrap.py` / `product_intent.py`，应上报。

### U2 模型运行夹具（R-M5-02）

静态文件，无执行方（与 `specialization` 那一对相同，仓库里没有读取它们的代码）。

- `claude/meta-skill/tests/prompts/new-product-consumer-app.md`：结构对齐 `prompts/specialization.md`
  （标题 / 角色句 / 输入 / 执行步骤 / 严格输出 schema）。角色："你是 bootstrap skill"；输入：空仓库 +
  一段用户请求（消费级语言学习应用，Expo + 服务端，"碎片化时间学习"，不出现 ink-scent 专名）；
  要读的文件用 `claude/meta-skill/...` 仓库相对路径；输出 schema 只含答案键会核对的字段：
  `profile.task_route`、`profile.experience_priority.mode`、`loaded_knowledge[]`、
  `experience_direction{proposed_count, recommended, user_action}`、
  `workflow.nodes[]{node_id, exit_artifacts[], hard_blocked_by[], skill_refs[]}`、`required_repair_loops[]`。
- `claude/meta-skill/tests/prompts/new-product-consumer-app-codex.md`：同一场景，读取入口换成
  `codex/meta-skill/skills/bootstrap.md` + canonical 根；不出现 `${CLAUDE_PLUGIN_ROOT}`、`AskUserQuestion`。
- `claude/meta-skill/tests/expected/new-product-consumer-app-expected.json` 与
  `…-codex-expected.json`：断言写成路径/集合谓词，不含任何节点名：

```json
{ "profile": {"task_route": "new-product", "experience_priority.mode": "consumer"},
  "loaded_knowledge_includes": ["capabilities/product-concept.md", "capabilities/app-design.md",
      "consumer-maturity-patterns.md", "journey-emotion-schema.md"],
  "experience_direction": {"proposed_count": [2, 3], "recommended": 1,
      "user_action_in": ["select", "delegate"], "must_not": "self-confirmed"},
  "some_node_exit_artifacts_include": [
      ".allforai/app-design/spec/user-flow-spec.json",
      ".allforai/app-design/spec/screen-requirements-spec.json",
      ".allforai/app-design/qa/experience-quality-critique-design.json",
      ".allforai/app-design/qa/experience-quality-critique-runtime.json"],
  "ordering": ["every UI implementation node transitively depends on the design-stage critique producer",
      "the closure node transitively depends on the runtime-stage critique producer"],
  "repair_loops_cover": ["design-stage critique producer", "runtime-stage critique producer"],
  "forbidden": ["assert by node_id", "not_applicable.experience present"] }
```

评审产物路径以 M3 落地后的 `experience-quality-critique/SKILL.md` 为准。

### U3 思维测试战役（R-M5-03）

**判据先冻结。** 两个文件在任何受测代理启动之前写好并单独成一步（其 sha256 记入 evidence）：

- `fixtures/product-experience/thought-tests.json`：`method`（沿用 `fixtures/pi-session-model` 的措辞）、
  `subject_under_test`（受测文件清单）、`cases[]`，每条 `{id, platform, skill, situation, expected[]}`。
- `fixtures/product-experience/subject-prompt.md`：沿用 `fixtures/product-review/subject-prompt.md` 的隔离指令
  （不读其它文件、动作写成伪调用、不猜预期），末尾的拼装说明改为"按 case 的 `skill` 列表内联全文"。

case 分配（平台混排；E9 是对 Pi 新增文本的一条补充，规格说"至少覆盖"）：

| id | platform | 内联的受测文本（`skill`） | 判定要点（`expected`） |
|---|---|---|---|
| E1 | claude | `knowledge/product-intent-confirmation.md` | 提案先答"谁/情境/感受/为何回来"；三条是方向之别；不出现时长选择器/题型清单式的直译 |
| E2 | codex | 同上 + `codex/meta-skill/skills/bootstrap.md` | "你定"记 `delegate`，`user_reference` 指向该轮；无当前轮提案时先 `propose` 不委托；不用 assume-and-declare 代替 |
| E3 | claude | 同 E1 | 用户未选 → 不 `select`/`delegate`/`confirm`，话题保持 pending，不进入 freeze |
| E4 | claude | `knowledge/defensive-patterns.md`（Pattern I/J）+ `knowledge/node-spec-template.md` | 报 `contract_gaps[].kind == "unspecified_user_visible_decision"`，其余照常完成，不造输入框 |
| E5 | codex | `skills/bootstrap/SKILL.md`（Step 1.6、Step 2）+ `knowledge/bootstrap-planning.md` + `knowledge/suppress-rules.md` | `mode: none` 带理由；不规划体验设计与质量门；`gap-experience-direction` 以理由排除 |
| E6 | claude | `knowledge/bootstrap-planning.md`（Must #8/#9）+ `capabilities/concept-acceptance.md` | 创意评审节点存在；收尾 `hard_blocked_by` 实现后的那次评审；评审在修复回路内 |
| E7 | codex | `codex/cross-exam-skill/product-review.md` | 读 `docs/experience-review/runtime.md` 作既有证据，不重评；未关 must-fix 进 `Prior evidence`，不占 `R` 号；不读 `.allforai/` |
| E8 | claude | `claude/superstorm/skills/cross-exam/SKILL.md`（§1b） | 候选含体验方向来源；`auto_decided` 的候选标注"此方向由模型受托选定" |
| E9 | pi | `pi/meta-skill/skills/bootstrap/SKILL.md` + E1 的协议 | 用纯文本提问呈现提案；"你定"记 `delegate`；不提 `AskUserQuestion` |

**运行。** 每 case 一个 fresh-context 子代理，可并发（信封 `max_concurrency: 4`）。packet =
`subject-prompt.md` + 各受测文件全文 + 该 case 的 `situation`，写到**仓库外**的会话 scratchpad，
`expected` 不进 packet。隔离性从宿主轨迹核对：受测代理的工具调用应只有对 packet 的一次 `Read`；
多读了别的文件即该 case 记 `invalid` 并重跑，不算 pass。不调用 codex/pi CLI（信封禁止付费外部调用）——
`platform` 是被模拟的平台，如实写入 `platform_simulated`。

**记录。**

- `docs/validation/product-experience-thought-tests/evidence.json`：字段沿用
  `docs/validation/product-review-thought-tests/evidence.json`——`round`、`date`、`host`、
  `tested_version{commit, <受测文件>: sha256}`、`launch{method, isolation, fixtures{path: sha256}}`、
  `cases[]{id, platform_simulated, under_test, prompt_sha256, requested_model, resolved_model, model_source,
  observed_tool_calls[], duration_ms, verdict, notes}`、`responses`、`found_defect`、`limits[]`、`responses_sha256`。
- `docs/validation/product-experience-thought-tests/responses.md`：各 case 受测回答原文。
- `docs/validation/product-experience-thought-tests.md`：`## 方法与证据`、`## 场景判定`（表）、
  `## 测出的缺陷与修复`、`## 尚未验证`（必含：真实宿主对话质量——即本规格的 Reality gate 候选；
  真实 codex/pi CLI 未调用；`/run` 内评审的真实截图输入未覆盖）。

**失败回路。** 判 fail 的 case：(1) 改出错的 skill 文本——**若是手工孪生则同提交双写**；
(2) 加一行契约钉住新句，落点按文本归属：claude/meta-skill 语料 → `validate_meta_contracts.py` 里
**所属模块已有的** `validate_*_contract` 函数追加一个字面量（不新建函数、不动既有钉住的字面量）；
codex 适配器 → U4 在 parity 脚本里的检查块；Pi → `pi/meta-skill/test_contract.py`；
product-review / cross-exam → M6 的 `test_experience_lens_parity.py` 不合适时，钉在
`claude/superstorm/scripts/` 下该 skill 既有的契约测试里；(3) 以 `E<n>b` 在修后的文本上重测，
`evidence.json` 追加一轮，旧轮保留。重测仍 fail 且需要改动公共接口/需求才能修 → 上报，不自行扩范围。

### U4 Codex/Pi 孪生同步（R-M5-04；消费 `data:delegationDisclosure`）

两个适配器都是"全文读 canonical，再应用替换"，因此新增文本只写**宿主差异与不可省的锚点**，
不复述 canonical 步骤。实现时先读 M1/M2/M3 落地后的 canonical 原句，术语逐字沿用。

**U4a `codex/meta-skill/skills/bootstrap.md`**：在 `### 1. Plugin Root Resolution`（现 `:99`）之前插入
`### 0b. Experience Priority, Direction and Quality Gate`，四条：
(1) 按 canonical Step 1.6 写 `experience_priority {mode, reason}`，Codex 同为唯一生产者；
(2) 产品路线且 `mode != none` 时加载 `<canonical-root>/knowledge/capabilities/product-concept.md`、
`consumer-maturity-patterns.md`、`journey-emotion-schema.md`、`capabilities/app-design.md` 或 `game-design.md`；
(3) `experience-direction` 话题：讨论前先 `propose`（2–3 条、一条推荐），以纯文本呈现；用户选定记 `select`，
用户明说"你定"记 `delegate`；**assume-and-declare 不能产生 `select` 或 `delegate`**，沉默与推荐不是动作；
(4) 按 canonical `bootstrap-planning.md` 规划体验质量门（design / runtime 两阶段、收尾受其阻断、在修复回路内），
生成前三道门必须通过。路径一律 `<canonical-root>/…`，不得出现 `${CLAUDE_PLUGIN_ROOT}`。

**U4b `pi/meta-skill/skills/bootstrap/SKILL.md`**：在 `## Validation` 之前追加 `### 7. 体验方向与体验质量门`
（不重排既有 1–6），同四条的中文版；提问方式写"用纯文本逐条列出提案并标明推荐，等用户回复"；
明写"用户回复'你定'记 `delegate`；没有回复不是委托"。

**U4c 三个模板的完成输出。** 以 M2 落地后 `claude/meta-skill/knowledge/orchestrator-template.md` 的
对应句为蓝本：

- `codex/meta-skill/knowledge/orchestrator-template.md`、`pi/meta-skill/knowledge/orchestrator-template.md`：
  `## Termination` 第一条（现 `:442-445` / `:431-434`）末尾补一句——成功报告在 `user_steps` 之前打印
  `python3 .allforai/bootstrap/scripts/product_intent.py . --delegations` 的输出（受托选定的体验方向：id、
  提案标题、委托所在用户轮次、理由）；清单为空则写明"无受托决定"；`## Post-Completion` 增加同一条命令为一步。
  Pi 模板不得因此出现 `.claude/commands/run.md` / `.codex/commands/run.md`。
- `codex/meta-skill/knowledge/flow-template.py`：新增一个函数 + 一处调用，均为加法：

```python
def delegation_disclosure(project_root: Path):
    """Model-delegated product choices, disclosed at completion. Never blocks completion."""
    result = run_script(project_root, "product_intent.py", [".", "--delegations"])
    if result is None or result.returncode:
        return "unavailable"
    try:
        return json.loads(result.stdout)
    except ValueError:
        return "unavailable"
```

  完成处（现 `:2290`）的 payload 增加键 `"delegations": delegation_disclosure(project_root)`。
  披露失败不改变 `passed/done`（披露是告知，不是门）；旧项目里复制的 `product_intent.py` 不识别该参数时
  落到 `"unavailable"`。`test_flow.py:2291` 只做 `'"done": true' in out` 的子串断言，加键不破坏它。
  `codex/meta-skill/test_flow.py` 追加一例：打桩 `run_script` 返回 `{"delegations":[…]}`，断言完成输出含该清单；
  再一例返回非零 → `"unavailable"` 且 `done` 仍为 true。

**U4d `shared/scripts/orchestrator/check_codex_meta_skill_parity.py`**：`disclosed_protocols` 追加
`"product-intent-confirmation.md"`；紧随其后加一个加法检查块（供 U3 失败回路钉句用）：
`bootstrap_text` 须含 `experience_priority`、`experience-direction`、`delegate`；
`run_template_text + flow_template_text` 须含 `--delegations`。

**U4e `pi/meta-skill/test_contract.py`**：`EntryTests` 增 `test_bootstrap_carries_experience_direction`
（Pi bootstrap 含 `experience_priority`、`experience-direction`、`delegate`、`propose`，且不含
"用 `AskUserQuestion`" 式的正向用法——既有的 `Pi 没有 \`AskUserQuestion\`` 一句仍须在）；
`TemplateTests` 增 `test_completion_discloses_delegations`（Pi 模板含 `--delegations`）。unittest 风格，与该文件一致。

不改：`codex/meta-skill/{AGENTS.md,execution-playbook.md}`（不描述意图话题，无需同步；若 U3 的 codex case
暴露缺口再按失败回路处理）、`codex/meta-skill/SKILL.md`（只在 U6 改版本）。

### U5 全量验证与基线对比（R-M5-05）

不改源码。按规格的九条命令加"验收"两条，逐条串行运行（meta-skill 全量约 6 分钟，信封要求一次只跑一个），
结果写入 `docs/superpowers/runs/2026-09-18-product-experience-overhaul/verification-M5.md`：
每条命令的原文、退出码、passed/failed 计数、耗时；meta-skill 全量另列失败用例 id 的完整清单并与基线四个
逐一比对（`test_decision_gate.py::test_a_resolved_choice_restores_readiness_only_with_fresh_evidence[claude|codex]`、
`test_evidence_freshness.py::test_fresh_contract_allows_execution_but_cannot_claim_completion[claude|codex]`），
以及相对基线（1198 passed / 4 failed @ `6a59fe44`；superstorm 255 passed）的通过数增量。
判定规则：失败集合 == 基线四个 → 通过；出现任何其它失败 → 本次回归，记录失败 id 与首段回溯，
状态 `regression`，M5 不得宣告完成（修复归引入它的模块；属 M5 自己文件的当场修）。
四个基线失败中若有变为通过，如实记录为"基线变化"，不算失败，也不去动它们。
另跑两条跨模块不变量并记入同一记录（M2、M3、M4 都往 `knowledge/` 写过字，M1 的不变量须在最终文本上复核）：
`grep -rn "experience_priority" claude/meta-skill/knowledge | grep -v "experience_priority.mode" | grep -v bootstrap`（期望为空）、
`python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py`（exit 0：M1/M3/M4 三个新钉住函数同时成立）。

### U6 版本（R-M5-06）

原地字符串替换（Edit 精确匹配，不 `json.load/dump`）：

| 文件 | 从 → 到 |
|---|---|
| `.claude-plugin/marketplace.json` `:9` / `:15` | `0.19.2`→`0.20.0`；`0.42.2`→`0.43.0` |
| `claude/meta-skill/.claude-plugin/plugin.json:4`、`…/marketplace.json:9` | `0.19.2`→`0.20.0` |
| `claude/superstorm/.claude-plugin/plugin.json:4`、`…/marketplace.json:9` | `0.42.2`→`0.43.0` |
| `pi/meta-skill/package.json:3` | `0.19.2-pi.1`→`0.20.0-pi.1` |
| `claude/meta-skill/SKILL.md:7,10` | `0.19.1`→`0.20.0`（frontmatter 与 `# Meta-Skill v…` 标题） |
| `claude/meta-skill/skills/bootstrap/SKILL.md:4` | `0.19.1`→`0.20.0` |
| `codex/meta-skill/SKILL.md:10,13` | `0.19.1-codex.2`→`0.20.0-codex.1` |

`pi/cross-exam/package.json`（`0.22.3-pi.1`）：M6 明确不单独改 Pi 的 cross-exam 适配器，包内容不变 → 不动；
实现时用 `git diff --stat <M6 起点>.. -- pi/cross-exam` 复核，若非空则补丁号 +1。
release 提交由编排器执行；本单元把提交正文草稿写到运行目录 `release-commit-message.txt`：
标题 `release: superstorm 0.43.0, meta-skill 0.20.0 (体验方向与体验质量门)`，正文含 U5 的各套件数字、
"4 个既有失败同 `6a59fe44`，未触碰"、思维测试 pass/fail 计数与 `## 尚未验证` 指针。不 push（信封 D6）。
正文另含一段**升级影响**（M1 设计 Error handling 点名要求由 M5 披露）：已 bootstrap 的产品路线项目在升级后的下一次 `/run`
会被 `missing_experience_priority` 拦下，需回到交互式 `/bootstrap` 补 `experience_priority`（界面产品随后还会被要求补体验方向、
体验设计节点与体验质量门）；`local-change` 路线与无 `task_route` 的遗留 profile 不受影响。

### U7 文档（R-M5-07）

- `CLAUDE.md`：`## Claude Meta-Skill Structure` 的 "User workflow" 句（`:75`）后补一句——有界面的产品路线上，
  bootstrap 设置 `experience_priority`、先提案体验方向（用户选定或明说委托）、规划体验设计节点与
  design/runtime 两阶段体验质量门，`/run` 完成时披露受托决定；`### Which entry for which situation` 表
  `/bootstrap → /run` 一行（`:226`）的 Why 列补"运行内含体验质量门，`/product-review` 采信其
  `docs/experience-review/` 留痕"。
- `README.md`：`:136` 的统一入口段补同义一句中文。其余 bootstrap 提及处（`:60,:98,:112`）是命令清单，不改。
- `CLAUDE.md` 的同一处再补一句升级影响（与 U6 提交正文同义）：旧的产品路线项目升级后首次 `/run` 会得到
  `missing_experience_priority`，回交互式 `/bootstrap` 即可。
- 不新增 CHANGELOG。

### 数据流

```
fixtures/consumer-learning-app/{bad,good}-workflow/*.json
   └─(test build: copied product_intent.py → draft/propose/decide/freeze/plan → confirm_plan → publish_contract)
        └─ tmp 项目 .allforai/**  ──► validate_bootstrap.py │ check_decision_inputs.py │ validate_unattended_readiness.py
                                         └─ 码集合断言（U1）
M2 product_intent.py --delegations ──► codex/pi 模板文本、flow.py 完成 payload（U4c）
最终 skill 文本 ──► packet（仓库外）──► fresh-context 受测代理 ──► responses.md / evidence.json（U3）
全部 ──► U5 命令组 ──► verification-M5.md ──► release-commit-message.txt（U6）
```

### 测试与验收命令

```bash
# U1
python3 -m pytest -q claude/meta-skill/tests/unit/test_consumer_product_regression.py
# U2 / U3 静态形状
python3 -c "import json,sys;[json.load(open(p)) for p in sys.argv[1:]]" \
  claude/meta-skill/tests/expected/new-product-consumer-app-expected.json \
  claude/meta-skill/tests/expected/new-product-consumer-app-codex-expected.json \
  fixtures/product-experience/thought-tests.json \
  docs/validation/product-experience-thought-tests/evidence.json
grep -n "^## 尚未验证" docs/validation/product-experience-thought-tests.md
# U4
python3 shared/scripts/orchestrator/check_codex_meta_skill_parity.py
python3 -m pytest -q pi/meta-skill/test_contract.py codex/meta-skill/test_flow.py codex/meta-skill/test_install.py
python3 -m pytest -q shared/scripts/orchestrator
# U6
python3 -m pytest -q claude/superstorm/scripts/test_package_manifests.py
# U5：R-M5-05 的九条命令原样，最后跑
```

绝不以目录方式跑 `pytest pi/meta-skill` 或 `pytest codex/meta-skill`。

### Assumptions（内部选择）

- A1 夹具以"重放输入"（profile / dialogue / plan / readiness-spec）而非静态 `.allforai/` 快照存放；
  规格中的"脚本化的 profile + workflow + node-specs"由 `plan.json`（节点 + `body`）经公共 `plan` 投影得到。
- A2 "阻断码集合"取三门并集，并加 readiness 报告单独含全三码的更强断言（Spec correction 3）。
- A3 增加第三个用例（已选方向 + ink-scent 图），只用两份夹具的现成部件拼出，不新增夹具目录。
- A4 good-workflow 不使用 `capability: "app-design"` 与固定节点 id，以产物路径满足 M1。
- A5 `--delegations` 的 stdout 是 JSON（`product_intent.py:1372` 的既有输出约定）；flow.py 原样嵌入，不解释其字段，
  故不依赖 M2 对内部键名的选择。
- A6 思维测试增加 `subject-prompt.md` 与一条 Pi case（E9），均沿用既有 `fixtures/*` 先例。
- A7 parity 脚本里新增的四个字面量检查、`test_flow.py` 的两例，是 R-M5-04 的"最小钉住"在 Codex 侧的对称物。
- A8 验证记录文件名 `verification-M5.md`、提交正文草稿 `release-commit-message.txt`，都在运行目录。
- A9 M1/M3 的校验已按各自规格注册进 `structural_gate_blockers`；若未注册，U1 第一例的 readiness 断言会失败，
  这是上游缺陷，上报而非在 M5 内改共享热文件。M5 **不触碰任何共享热文件**
  （`validate_bootstrap.py`、`bootstrap-planning.md`、`test_validate_bootstrap.py`、`skills/bootstrap/SKILL.md` 除版本行外）；
  `validate_meta_contracts.py` 仅在 U3 失败回路里可能追加字面量。

### File touch list

| 路径 | 动作 | 需求 |
|---|---|---|
| `claude/meta-skill/tests/fixtures/consumer-learning-app/README.md` | create | R-M5-01 |
| `claude/meta-skill/tests/fixtures/consumer-learning-app/bad-workflow/{profile,dialogue,plan,readiness-spec}.json` | create | R-M5-01 |
| `claude/meta-skill/tests/fixtures/consumer-learning-app/good-workflow/{profile,dialogue,plan,readiness-spec}.json` | create | R-M5-01 |
| `claude/meta-skill/tests/unit/test_consumer_product_regression.py` | create | R-M5-01 |
| `claude/meta-skill/tests/prompts/new-product-consumer-app.md` | create | R-M5-02 |
| `claude/meta-skill/tests/prompts/new-product-consumer-app-codex.md` | create | R-M5-02 |
| `claude/meta-skill/tests/expected/new-product-consumer-app-expected.json` | create | R-M5-02 |
| `claude/meta-skill/tests/expected/new-product-consumer-app-codex-expected.json` | create | R-M5-02 |
| `fixtures/product-experience/thought-tests.json` | create | R-M5-03 |
| `fixtures/product-experience/subject-prompt.md` | create | R-M5-03 |
| `docs/validation/product-experience-thought-tests.md` | create | R-M5-03 |
| `docs/validation/product-experience-thought-tests/evidence.json` | create | R-M5-03 |
| `docs/validation/product-experience-thought-tests/responses.md` | create | R-M5-03 |
| （仅失败回路）出错的 skill 文本及其孪生、对应契约文件 | edit | R-M5-03 |
| `codex/meta-skill/skills/bootstrap.md` | edit | R-M5-04 |
| `pi/meta-skill/skills/bootstrap/SKILL.md` | edit | R-M5-04 |
| `codex/meta-skill/knowledge/orchestrator-template.md` | edit | R-M5-04 |
| `pi/meta-skill/knowledge/orchestrator-template.md` | edit | R-M5-04 |
| `codex/meta-skill/knowledge/flow-template.py` | edit | R-M5-04 |
| `codex/meta-skill/test_flow.py` | edit | R-M5-04 |
| `shared/scripts/orchestrator/check_codex_meta_skill_parity.py` | edit | R-M5-04 |
| `pi/meta-skill/test_contract.py` | edit | R-M5-04 |
| `docs/superpowers/runs/2026-09-18-product-experience-overhaul/verification-M5.md` | create | R-M5-05 |
| `.claude-plugin/marketplace.json` | edit | R-M5-06 |
| `claude/meta-skill/.claude-plugin/{plugin.json,marketplace.json}` | edit | R-M5-06 |
| `claude/superstorm/.claude-plugin/{plugin.json,marketplace.json}` | edit | R-M5-06 |
| `pi/meta-skill/package.json` | edit | R-M5-06 |
| `claude/meta-skill/SKILL.md`、`claude/meta-skill/skills/bootstrap/SKILL.md`（仅版本行） | edit | R-M5-06 |
| `codex/meta-skill/SKILL.md`（仅版本行） | edit | R-M5-06 |
| `docs/superpowers/runs/2026-09-18-product-experience-overhaul/release-commit-message.txt` | create | R-M5-06 |
| `CLAUDE.md` | edit | R-M5-07 |
| `README.md` | edit | R-M5-07 |
