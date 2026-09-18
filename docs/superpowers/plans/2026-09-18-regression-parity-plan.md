# M5 regression-parity — 实施计划（任务契约）

- 设计：`docs/superpowers/specs/2026-09-18-regression-parity-design.md`（需求 R-M5-01…07 + `## Detailed design` U1–U7）
- 总览与冻结注册表：`docs/superpowers/specs/2026-09-18-product-experience-overhaul-overview.md`
- 分支 `product-experience-overhaul`。执行方不做任何 git 变更；提交由编排器完成。
- 所有 `acceptance_cmd` 以仓库根为 cwd 执行。路径一律仓库相对。

## 全局约束（每个任务都适用）

1. M5 在 M1、M2、M3、M4、M6 之后执行。凡引用它们产物的地方，**以落地后的文件为准**：先读 canonical 原句，术语逐字沿用；
   不得凭本计划或设计文档里的转述去猜字段名、阻断码、产物路径。
   **这条次序写进了 DAG，不靠约定。** 调度器按依赖就绪派发，不按模块排队；`requires` → `implements` 的派生边只够得着上游的
   *早期*任务（T-M1-01/02/04、T-M2-04/05/06、T-M3-02/05、T-M4-01），够不着 M5 真正依赖的那些——T-M2-07
   （`ui_product_without_experience_direction`，R-M5-01 点名的码）、T-M2-08（claude 模板的披露句，T-M5-02/04 的蓝本）、
   T-M3-07/08（Must #9 与抑制规则，T-M5-01/02 的第四条与 E5/E6 的受测文本）、T-M4-02（E4 的受测文本）、M6 全部（E7/E8 的受测文本，
   M6 不暴露任何接口）。因此 M5 的七个根任务（T-M5-01、02、03、04、06、08、12）的 `depends_on` 都带上上游各模块的**汇点任务**：
   `T-M1-07`、`T-M2-10`、`T-M3-10`、`T-M4-07`、`T-M4-08`、`T-M6-03`、`T-M6-04`、`T-M6-05`（每个汇点传递覆盖其模块全部任务）；
   其余 M5 任务经模块内依赖继承。这些外部 id 是稳定的；上游计划若改了汇点编号，同步改这七处。
2. M5 **不得为让自己的测试通过而修改** `validate_bootstrap.py`、`product_intent.py`、`check_decision_inputs.py`、
   `validate_unattended_readiness.py`、`bootstrap-planning.md`、`test_validate_bootstrap.py`、`test_bootstrap_scope.py`。
   上游未注册校验、码名不符 = 上游缺陷，任务以 blocked 上报并附三门完整码集。
3. 替换规则：Codex 本地文件不得出现 `${CLAUDE_PLUGIN_ROOT}`；Pi **模板**不得出现 `.claude/commands/run.md` /
   `.codex/commands/run.md`；Pi 无 `AskUserQuestion`（Pi bootstrap 适配器里既有的 `${CLAUDE_PLUGIN_ROOT}` 说明句是合法且被钉住的，不要动）。
4. pytest 只点名文件；绝不 `pytest pi/meta-skill` 或 `pytest codex/meta-skill`；`claude/superstorm/scripts` 与
   `codex/cross-exam-skill/scripts` 不得同一次调用。meta-skill 全量套件只有 T-M5-14 能跑。
5. 授权信封：不调用 codex/pi CLI，不 push，不写 `/Users/aa/workspace/ink-scent`，不改 4 个既有失败测试，不删既有测试/夹具。
6. 版本字符串原地精确替换，不 `json.load/dump` 重序列化。

## 任务图

```
T-01 codex bootstrap 适配器 ─┐
T-03 flow-template + test_flow ─┼─► T-05 parity 脚本 + 破坏性用例 ─┐
T-04 codex orchestrator 模板 ──┘                                   │
T-02 Pi 适配器 + 模板 + test_contract ─────────────────────────────┤
T-06 bad 夹具 + 用例 1 ─► T-07 good 夹具 + 用例 2/3 (implements data:regressionFixtures)
T-08 模型运行夹具（答案键）                                        │
T-09 冻结思维测试判据 ─► T-10 运行并记录 ─► T-11 失败回路收口 ◄────┘
T-12 文档
T-13 版本（在 T-11 之后）
T-14 全量验证（在以上全部之后）─► T-15 release 提交正文草稿
T-16 真实宿主验收（reality gate，不被任何任务依赖）

七个根任务（01、02、03、04、06、08、12）← 上游汇点 T-M1-07、T-M2-10、T-M3-10、T-M4-07、T-M4-08、T-M6-03、T-M6-04、T-M6-05
```

---

## T-M5-01 Codex bootstrap 适配器补入体验优先级/方向/质量门（U4a，R-M5-04）

**行为。** `codex/meta-skill/skills/bootstrap.md` 在 `### 1. Plugin Root Resolution` 之前新增
`### 0b. Experience Priority, Direction and Quality Gate`，只写宿主差异与不可省的锚点（适配器是"全文读 canonical 再替换"），四条：
(1) 按 canonical Step 1.6 写 `experience_priority {mode, reason}`，Codex 同为唯一生产者；
(2) 产品路线且 `mode != none` 时加载 `<canonical-root>/knowledge/capabilities/product-concept.md`、`consumer-maturity-patterns.md`、
`journey-emotion-schema.md`、`capabilities/app-design.md` 或 `game-design.md`；
(3) `experience-direction` 话题：先 `propose`（2–3 条、一条推荐）以纯文本呈现；用户选定记 `select`，用户明说"你定"记 `delegate`；
assume-and-declare 不能产生 `select`/`delegate`，沉默与推荐不是动作；协议出处写 `<canonical-root>/knowledge/product-intent-confirmation.md`；
(4) 按 canonical `bootstrap-planning.md` 规划 design / runtime 两阶段体验质量门、收尾受其阻断、在修复回路内；生成前三道门必须通过。
消费 `api:productIntentPropose` / `api:productIntentSelect` / `api:productIntentDelegate`（操作名以 M2 落地文本为准）。

**检查意图。** 纯文本任务：钉住标题与各锚点字面量（今天该文件 `experience-direction` 出现 0 次），并跑 parity 脚本证明没有引入
`${CLAUDE_PLUGIN_ROOT}`、既有 Codex 契约未破。

**Acceptance.**
```bash
grep -q '^### 0b\. Experience Priority, Direction and Quality Gate' codex/meta-skill/skills/bootstrap.md && for s in experience_priority experience-direction propose delegate product-intent-confirmation.md consumer-maturity-patterns.md journey-emotion-schema.md capabilities/product-concept.md; do grep -q -- "$s" codex/meta-skill/skills/bootstrap.md || exit 1; done && ! grep -q 'CLAUDE_PLUGIN_ROOT' codex/meta-skill/skills/bootstrap.md && python3 shared/scripts/orchestrator/check_codex_meta_skill_parity.py
```
**Write set.** `codex/meta-skill/skills/bootstrap.md`
**depends_on.** 上游汇点 T-M1-07、T-M2-10、T-M3-10、T-M4-07、T-M4-08、T-M6-03、T-M6-04、T-M6-05（见全局约束 1）

## T-M5-02 Pi 适配器、Pi 模板与 Pi 契约钉住（U4b + U4c-Pi + U4e，R-M5-04）

**行为。**
- `pi/meta-skill/skills/bootstrap/SKILL.md`：在 `## Validation` 之前追加 `### 7. 体验方向与体验质量门`（不重排 1–6），T-M5-01 同四条的中文版；
  提问方式写"用纯文本逐条列出提案并标明推荐，等用户回复"；明写"用户回复'你定'记 `delegate`；没有回复不是委托"。
  既有的 `Pi 没有 \`AskUserQuestion\`` 一句保留，不得出现把 `AskUserQuestion` 当可用工具的正向用法。
- `pi/meta-skill/knowledge/orchestrator-template.md`：`## Termination` 第一条末尾补——成功报告在 `user_steps` 之前打印
  `python3 .allforai/bootstrap/scripts/product_intent.py . --delegations` 的输出（受托选定的体验方向：id、提案标题、委托所在用户轮次、理由），
  清单为空写明"无受托决定"；`## Post-Completion` 增加同一条命令为一步。措辞以 M2 落地后的 claude `orchestrator-template.md` 对应句为蓝本。
  消费 `data:delegationDisclosure`。

**测试意图（先写，先红）。** `pi/meta-skill/test_contract.py`，unittest 风格：
- `EntryTests.test_bootstrap_carries_experience_direction`：Pi bootstrap 含 `experience_priority`、`experience-direction`、`delegate`、`propose`；
  仍含既有的"Pi 没有 `AskUserQuestion`"句；不含正向用法（如"用 `AskUserQuestion`"/"调用 `AskUserQuestion`"）。
  这证明 Pi 用户走的是原生提问而非不存在的工具。
- `TemplateTests.test_completion_discloses_delegations`：Pi 模板含 `--delegations`。与既有 `test_orchestrator_template_is_pi_native` 的禁词断言一起，
  证明披露被加上且没有带进别家宿主的路径。

**Acceptance.**（按 node id 选择，测试不存在时 pytest 以非零退出）
```bash
python3 -m pytest -q "pi/meta-skill/test_contract.py::EntryTests::test_bootstrap_carries_experience_direction" "pi/meta-skill/test_contract.py::TemplateTests::test_completion_discloses_delegations" && python3 -m pytest -q pi/meta-skill/test_contract.py && grep -q '^### 7\. 体验方向与体验质量门' pi/meta-skill/skills/bootstrap/SKILL.md && [ "$(grep -c -- '--delegations' pi/meta-skill/knowledge/orchestrator-template.md)" -ge 2 ] && ! grep -q '\.claude/commands/run\.md\|\.codex/commands/run\.md' pi/meta-skill/knowledge/orchestrator-template.md
```
**Write set.** `pi/meta-skill/skills/bootstrap/SKILL.md`、`pi/meta-skill/knowledge/orchestrator-template.md`、`pi/meta-skill/test_contract.py`
**depends_on.** 上游汇点 T-M1-07、T-M2-10、T-M3-10、T-M4-07、T-M4-08、T-M6-03、T-M6-04、T-M6-05（见全局约束 1）

## T-M5-03 Codex flow 驱动在完成 payload 披露受托决定（U4c-flow，R-M5-04）

**行为。** `codex/meta-skill/knowledge/flow-template.py` 纯加法：新增
```python
def delegation_disclosure(project_root: Path):
    """Model-delegated product choices, disclosed at completion. Never blocks completion."""
```
经既有 `run_script(project_root, "product_intent.py", [".", "--delegations"])` 取 stdout 的 JSON 并**原样**返回（不解释字段）；
`run_script` 返回 `None`、非零退出、或 stdout 非 JSON → 返回字符串 `"unavailable"`。成功完成处的 payload 增加键
`"delegations": delegation_disclosure(project_root)`。披露是告知不是门：任何披露失败都不改变 `passed` / `done`。
消费 `data:delegationDisclosure`。

**测试意图（先写，先红）。** `codex/meta-skill/test_flow.py` 追加两例，沿用该文件既有的加载/打桩方式：
- `test_completion_discloses_delegations`：打桩 `run_script` 对 `--delegations` 返回 `{"delegations":[…]}`，断言完成输出的 `delegations` 键等于该清单且 `done` 为 true。
- `test_delegation_disclosure_failure_never_blocks_completion`：打桩返回非零（另一参数化或同例内再测 `None` / 非 JSON）→ 输出 `"delegations": "unavailable"`，`done` 仍为 true。
  这一条证明旧项目里不识别该参数的 `product_intent.py` 不会把完成变成失败。

**Acceptance.**
```bash
python3 -m pytest -q "codex/meta-skill/test_flow.py::test_completion_discloses_delegations" "codex/meta-skill/test_flow.py::test_delegation_disclosure_failure_never_blocks_completion" && python3 -m pytest -q codex/meta-skill/test_flow.py && grep -q '^def delegation_disclosure(project_root: Path)' codex/meta-skill/knowledge/flow-template.py
```
（若第二例参数化，node id 带 `[…]` 后缀会使精确 node id 选不中——那就不要参数化，把三种失败形态写在同一个测试函数里。）

**Write set.** `codex/meta-skill/knowledge/flow-template.py`、`codex/meta-skill/test_flow.py`
**depends_on.** 上游汇点 T-M1-07、T-M2-10、T-M3-10、T-M4-07、T-M4-08、T-M6-03、T-M6-04、T-M6-05（见全局约束 1）

## T-M5-04 Codex orchestrator 模板的完成输出打印委托清单（U4c-codex，R-M5-04）

**行为。** `codex/meta-skill/knowledge/orchestrator-template.md`：`## Termination` 第一条末尾与 `## Post-Completion` 各补一处，
内容同 T-M5-02 的 Pi 模板（打印 `python3 .allforai/bootstrap/scripts/product_intent.py . --delegations`，空清单写明无受托决定），
语言与该文件既有语言一致。不得出现 `${CLAUDE_PLUGIN_ROOT}`、`.claude/commands/run.md`。消费 `data:delegationDisclosure`。

**检查意图。** 该文件今天 `--delegations` 出现 0 次；要求 ≥2 处（Termination + Post-Completion）且完整命令字面量在；parity 脚本仍过。

**Acceptance.**
```bash
[ "$(grep -c -- '--delegations' codex/meta-skill/knowledge/orchestrator-template.md)" -ge 2 ] && grep -q 'product_intent.py . --delegations' codex/meta-skill/knowledge/orchestrator-template.md && ! grep -q 'CLAUDE_PLUGIN_ROOT\|\.claude/commands/run\.md' codex/meta-skill/knowledge/orchestrator-template.md && python3 shared/scripts/orchestrator/check_codex_meta_skill_parity.py
```
**Write set.** `codex/meta-skill/knowledge/orchestrator-template.md`
**depends_on.** 上游汇点 T-M1-07、T-M2-10、T-M3-10、T-M4-07、T-M4-08、T-M6-03、T-M6-04、T-M6-05（见全局约束 1）

## T-M5-05 parity 脚本披露新协议并钉住 Codex 侧新文本（U4d，R-M5-04）

**行为。** `shared/scripts/orchestrator/check_codex_meta_skill_parity.py`：
- `disclosed_protocols` 追加 `"product-intent-confirmation.md"`；
- 紧随其后一个加法检查块：`bootstrap_text` 缺 `experience_priority`、`experience-direction`、`delegate` 任一 → 追加一条含子串
  **`experience direction`** 的错误；`run_template_text + flow_template_text` 不含 `--delegations` → 追加一条含子串
  **`delegation disclosure`** 的错误。（这两个子串是下面破坏性用例的匹配键；注意既有用例 id `delegation` / 期望串 `delegate` 已被 install.sh 用例占用，不要复用。）
  这个检查块也是 T-M5-11 失败回路给 Codex 适配器钉新句的落点。

**测试意图（先写，先红）。** `shared/scripts/orchestrator/test_codex_contract_checks.py` 的
`test_bundle_contract_regressions_are_rejected` 参数表追加两个 damage：
`experience_direction`（把 `skills/bootstrap.md` 里的 `experience-direction` 全部替换掉 → 期望错误含 `experience direction`）、
`delegation_disclosure`（把 `knowledge/orchestrator-template.md` **和** `knowledge/flow-template.py` 里的 `--delegations` 都替换掉 →
期望含 `delegation disclosure`）。现有的单文件替换字典容不下双文件破坏，按需小幅扩展该测试的破坏逻辑，保留
"fixture mutation did not apply" 守卫。破坏后必红、当前 bundle 必绿，二者合起来证明检查块真的在看这些字面量。

**Acceptance.**
```bash
python3 -m pytest --co -q shared/scripts/orchestrator/test_codex_contract_checks.py | grep -q 'experience_direction' && python3 -m pytest --co -q shared/scripts/orchestrator/test_codex_contract_checks.py | grep -q 'delegation_disclosure' && python3 -m pytest -q shared/scripts/orchestrator/test_codex_contract_checks.py && grep -q '"product-intent-confirmation.md"' shared/scripts/orchestrator/check_codex_meta_skill_parity.py && python3 shared/scripts/orchestrator/check_codex_meta_skill_parity.py
```
**Write set.** `shared/scripts/orchestrator/check_codex_meta_skill_parity.py`、`shared/scripts/orchestrator/test_codex_contract_checks.py`
**depends_on.** T-M5-01、T-M5-03、T-M5-04（检查块要求这些文本已在）

---

## T-M5-06 ink-scent 形状的 bad-workflow 夹具 + "三门皆拒"用例（U1 前半，R-M5-01）

**行为。** 新增重放输入夹具（不是静态 `.allforai/` 快照）`claude/meta-skill/tests/fixtures/consumer-learning-app/`：
- `README.md`：来源（ink-scent 2026-09-14~16 new-product 运行的**形状**，非内容拷贝）；"显式产物，不是语义规划器替身"。
- `bad-workflow/profile.json`：`task_goal`、`architecture_pattern`、`modules`（Expo 移动端 + Node 服务端，键名取
  `_profile_has_mobile_ui_module` 能识别的形状，移动模块 `role` 为 `mobile`/`frontend`、路径 `mobile/`）、`experience_priority {mode:"consumer", reason}`。
- `bad-workflow/dialogue.json`：有序 `product_intent.py` 请求数组 `draft`（route `new-product`、`origin: user-request`、六个旧话题；
  "碎片化学习"被直译为"2/5/10 分钟时长选择 + 题型清单"的 `acceptance`）→ `decide`（全 `confirm`，动作键 `operation`）→
  `freeze`（以理由 `exclude` 体验方向缺口；确切 gap id 取 M2 落地后 `resume` 的输出）。
- `bad-workflow/plan.json`：`plan` 请求，**恰 13 个节点**（1 契约、1 内容库、6 implement、其余 verify/repair）；实现节点把 `experience` 写进自己的
  `responsibilities`（ink-scent 正是这样让阶段全覆盖通过）；无节点 `exit_artifacts` 以 `.allforai/app-design/` 开头；无节点引用
  `experience-quality-critique`；每节点 `body` ≥ `ATTENTION_CONTRACT_BODY` 的术语；移动端实现节点的 goal/`body` 写出 `screen` 与 `mobile/`，
  使 M1 的界面实现节点识别函数与 M3 触发条件认得出它（否则期望码不出现是夹具形状问题而非上游缺陷）。
  每个冻结意图都有消费节点，且这些节点的 `responsibilities` 并集覆盖六阶段。
- `bad-workflow/readiness-spec.json`：`_minimal_project` 同形，`required_repair_loops: []`。

新测试文件 `claude/meta-skill/tests/unit/test_consumer_product_regression.py`：模块 docstring 沿用 `test_bootstrap_scope.py:1-4` 的声明；
helper 导入不复制（`from .test_bootstrap_scope import confirm_plan, gate, project, publish_contract, write`、
`from .test_product_intent_session import invoke`）；host 参数化 `["claude","codex"]`。文件私有 helper 的签名即契约：
```python
FIXTURE = Path(__file__).resolve().parents[1] / "fixtures/consumer-learning-app"
GATES = ("validate_bootstrap.py", "check_decision_inputs.py", "validate_unattended_readiness.py")
def build(root, host, *, dialogue, plan, readiness, force_past_front_door=False) -> dict
def codes(root) -> dict[str, set[str]]   # 每门一次；三种输出各自的解析方式见设计 U1
```
`build`：`project(root, host=host, source_inputs=None)` → 清掉 local-change 残留 → 逐条 `invoke(dialogue)` → 合并 `profile.json`（以 `consumer` 覆盖夹具自带的 `none`）→
写 readiness-spec → `invoke(plan)` → `confirm_plan(stage="plan-projection")` → 对每个声明 `source_inputs` 的节点 `publish_contract`。
`force_past_front_door=True`：**先断言**带 consumer profile 的 `plan` 被拒且 stdout 含 `ui_product_without_experience_direction`（前门也关着），
再临时让 `experience_priority` 不生效、`plan`、写回 `consumer`。

**测试意图。** `test_ink_scent_shaped_workflow_is_refused_at_every_public_gate[host]`：三门 `returncode == 1`；三门码**并集** ⊇
`{missing_experience_design_node, missing_experience_gate, ui_product_without_experience_direction}`；readiness 报告**单独** ⊇ 同一集合
（只有它不被 scope 短路）；`check_decision_inputs` 的码含 `ui_product_without_experience_direction`；工作流节点数 == 13 且无
`.allforai/app-design/` 产物（守住夹具自身形状）。任何 `invoke`/`publish_contract` 非零即带 `(stdout, stderr)` 断言失败；期望码缺失时失败信息打印三门完整码集。
这证明触发本次改造的事故在确定性层面会被拒绝。消费 `api:validateExperienceDesignCoverage`、`api:validateExperienceGateFlow`。

**Acceptance.**
```bash
python3 -m pytest --co -q claude/meta-skill/tests/unit/test_consumer_product_regression.py | grep -q 'test_ink_scent_shaped_workflow_is_refused_at_every_public_gate\[codex\]' && python3 -m pytest -q claude/meta-skill/tests/unit/test_consumer_product_regression.py && python3 -c 'import json; p=json.load(open("claude/meta-skill/tests/fixtures/consumer-learning-app/bad-workflow/plan.json")); s=json.dumps(p); assert ".allforai/app-design/" not in s and "experience-quality-critique" not in s'
```
**Write set.** `claude/meta-skill/tests/fixtures/consumer-learning-app/README.md`、
`…/bad-workflow/profile.json`、`…/bad-workflow/dialogue.json`、`…/bad-workflow/plan.json`、`…/bad-workflow/readiness-spec.json`、
`claude/meta-skill/tests/unit/test_consumer_product_regression.py`
**depends_on.** 上游汇点 T-M1-07、T-M2-10、T-M3-10、T-M4-07、T-M4-08、T-M6-03、T-M6-04、T-M6-05（见全局约束 1）

## T-M5-07 good-workflow 夹具 + "已选方向不豁免" 与 "三门皆过" 用例（U1 后半，R-M5-01）— implements `data:regressionFixtures`

**行为。** 补齐 `good-workflow/`，使 `data:regressionFixtures`（bad + good 两份重放输入及其回归测试）可被消费：
- `profile.json`：同 bad。
- `dialogue.json`：`draft`（同六话题）→ `propose`（3 条方向、1 条推荐，字段按 M2 落地的校验；`comparable` 为 `{product, approach}`）→
  `decide`（六话题 `confirm` + `{"operation":"select","proposal_id":…,"reason":…}` + 紧随其后对 `gap-experience-direction` 的
  `{"operation":"answer",…}`——`select` 不自动关缺口）→ `freeze`（include 含派生意图 `experience-direction-<proposal_id>`）。
- `plan.json`：体验设计节点（`exit_artifacts` 覆盖 R-M1-04 四个应用产物路径，以 M1 落地常量为准）→ design 阶段评审（`exit_artifacts` 含
  `.allforai/app-design/qa/experience-quality-critique-design.json` 及其 `.html`、`docs/experience-review/design.md`）→ 界面实现节点
  （传递 `hard_blocked_by` 设计评审；goal/`body` 含 `screen` 与 `mobile/`）→ verify（含一个满足既有 `validate_mobile_ui_coverage` 对
  `react-native` 平台要求的 UI 自动化节点，带 runner evidence 措辞）→ runtime 阶段评审（`…-runtime.json`/`.html`/`docs/experience-review/runtime.md`）→
  收尾节点（`hard_blocked_by` runtime 评审；capability 首选 M3 `EXPERIENCE_GATE_CLOSURE_CAPABILITIES` 之一，若牵出其它固定要求成本过高则退回普通
  capability 并在 README 注明）→ 两个修复节点。**不用** `capability: "app-design"`、不用 `APP_DESIGN_REQUIRED_NODES` 里的 id；
  节点 id 不含 `product-review` / `cross-exam`。评审产物路径以 M3 落地的 critique skill 为准（消费 `data:experienceCritiqueReport`）。
- `readiness-spec.json`：`required_repair_loops` 两条（design / runtime 评审回路；形状取 `test_validate_unattended_readiness.py` 的 `_repair_loop`；
  `qa_node_ids` 含两个评审节点；closure 节点直接 `hard_blocked_by` 评审节点与 repair 节点）。

**测试意图。** 同一测试文件追加两例（host 参数化）：
- `test_chosen_direction_does_not_excuse_a_graph_without_design_or_gate`：good 对话 + bad 计划（测试内把体验方向意图 id 追加到 bad 计划各实现节点
  `intent_ids`）→ `plan` 成功；`validate_bootstrap.py` **自身** `returncode == 1` 且码 ⊇ `{missing_experience_design_node, missing_experience_gate}`。
  补上"scope 有错即短路跨节点检查"留下的盲区。
- `test_designed_and_gated_workflow_passes_every_public_gate`：good + good → 三门 `returncode == 0`、`stderr` 空、readiness `status == "ready"`；
  冻结范围内恰一条 `topic == "experience-direction"`、`origin == "model-proposal"` 的意图；重跑三门前后项目文件字节不变。
  证明门不是"一律拒绝"，正确形状能过。消费 `api:productIntentPropose`、`api:productIntentSelect`、`api:validateExperienceDesignCoverage`、`api:validateExperienceGateFlow`。

**Acceptance.**（三个用例 × 两个 host = 至少 6 个被收集；good 计划确实声明了四个关键产物）
```bash
[ "$(python3 -m pytest --co -q claude/meta-skill/tests/unit/test_consumer_product_regression.py | grep -c '::test_')" -ge 6 ] && python3 -m pytest --co -q claude/meta-skill/tests/unit/test_consumer_product_regression.py | grep -q 'test_designed_and_gated_workflow_passes_every_public_gate\[codex\]' && python3 -m pytest --co -q claude/meta-skill/tests/unit/test_consumer_product_regression.py | grep -q 'test_chosen_direction_does_not_excuse_a_graph_without_design_or_gate\[claude\]' && python3 -m pytest -q claude/meta-skill/tests/unit/test_consumer_product_regression.py && python3 -c 'import json; s=json.dumps(json.load(open("claude/meta-skill/tests/fixtures/consumer-learning-app/good-workflow/plan.json"))); assert all(k in s for k in ("experience-quality-critique-design.json","experience-quality-critique-runtime.json","user-flow-spec.json","screen-requirements-spec.json"))'
```
**Write set.** `…/consumer-learning-app/good-workflow/{profile,dialogue,plan,readiness-spec}.json`、`…/consumer-learning-app/README.md`、
`claude/meta-skill/tests/unit/test_consumer_product_regression.py`
**depends_on.** T-M5-06

---

## T-M5-08 模型运行夹具：消费级 new-product 的提示与答案键（U2，R-M5-02）

**行为。** 四个静态文件（仓库里无读取方，与 `specialization` 那一对同性质）：
- `claude/meta-skill/tests/prompts/new-product-consumer-app.md`：结构对齐 `prompts/specialization.md`（标题 / 角色句 / 输入 / 执行步骤 / 严格输出 schema）；
  角色"你是 bootstrap skill"；输入为空仓库 + 一段用户请求（消费级语言学习应用、Expo + 服务端、"碎片化时间学习"，**不出现 ink-scent 专名**）；
  要读的文件用 `claude/meta-skill/...` 仓库相对路径（含 `claude/meta-skill/skills/bootstrap/SKILL.md`）；输出 schema 只含答案键核对的字段：
  `profile.task_route`、`profile.experience_priority.mode`、`loaded_knowledge[]`、`experience_direction{proposed_count, recommended, user_action}`、
  `workflow.nodes[]{node_id, exit_artifacts[], hard_blocked_by[], skill_refs[]}`、`required_repair_loops[]`。
- `…/prompts/new-product-consumer-app-codex.md`：同场景，入口换成 `codex/meta-skill/skills/bootstrap.md` + canonical 根；不出现 `${CLAUDE_PLUGIN_ROOT}`、`AskUserQuestion`。
- `…/expected/new-product-consumer-app-expected.json` 与 `…-codex-expected.json`：键形如设计 U2 的 JSON——`profile{"task_route","experience_priority.mode"}`、
  `loaded_knowledge_includes[]`、`experience_direction{proposed_count:[2,3], recommended:1, user_action_in:["select","delegate"], must_not:"self-confirmed"}`、
  `some_node_exit_artifacts_include[]`（四条产物路径）、`ordering[]`、`repair_loops_cover[]`、`forbidden[]`（含 `"assert by node_id"`）。
  **以产物路径/集合谓词断言，不含任何节点名。** 评审产物路径以 M3 落地文本为准（消费 `data:experienceCritiqueReport`）。

**检查意图。** 解析两份答案键并核对关键谓词；核对答案键里的两条评审产物路径确实出现在 M3 落地的 canonical 文本里（答案键不得自造路径）；提示文件的禁词与入口路径。

**Acceptance.**
```bash
python3 -c 'import json; P="claude/meta-skill/tests/expected/new-product-consumer-app"; docs=[json.load(open(P+s)) for s in ("-expected.json","-codex-expected.json")]; need={".allforai/app-design/spec/user-flow-spec.json",".allforai/app-design/spec/screen-requirements-spec.json",".allforai/app-design/qa/experience-quality-critique-design.json",".allforai/app-design/qa/experience-quality-critique-runtime.json"}; assert all(need<=set(d["some_node_exit_artifacts_include"]) and d["profile"]["task_route"]=="new-product" and d["profile"]["experience_priority.mode"]=="consumer" and "assert by node_id" in d["forbidden"] and set(d["experience_direction"]["user_action_in"])=={"select","delegate"} for d in docs)' && grep -rq --exclude-dir=tests 'experience-quality-critique-design.json' claude/meta-skill && grep -rq --exclude-dir=tests 'experience-quality-critique-runtime.json' claude/meta-skill && grep -q 'claude/meta-skill/skills/bootstrap/SKILL.md' claude/meta-skill/tests/prompts/new-product-consumer-app.md && grep -q 'codex/meta-skill/skills/bootstrap.md' claude/meta-skill/tests/prompts/new-product-consumer-app-codex.md && grep -q 'experience_priority' claude/meta-skill/tests/prompts/new-product-consumer-app.md && grep -q 'experience_priority' claude/meta-skill/tests/prompts/new-product-consumer-app-codex.md && ! grep -qi 'ink-scent' claude/meta-skill/tests/prompts/new-product-consumer-app.md claude/meta-skill/tests/prompts/new-product-consumer-app-codex.md && ! grep -q 'CLAUDE_PLUGIN_ROOT\|AskUserQuestion' claude/meta-skill/tests/prompts/new-product-consumer-app-codex.md
```
**Write set.** 上述四个文件。
**depends_on.** 上游汇点 T-M1-07、T-M2-10、T-M3-10、T-M4-07、T-M4-08、T-M6-03、T-M6-04、T-M6-05（见全局约束 1）

---

## T-M5-09 冻结思维测试判据（U3 第一步，R-M5-03）

**行为。** 在任何受测代理启动之前单独成步：
- `fixtures/product-experience/thought-tests.json`：`method`（沿用 `fixtures/pi-session-model/thought-tests.json` 的措辞）、`subject_under_test`（受测文件清单）、
  `cases[]`，每条 `{id, platform, skill[], situation, expected[]}`。`skill` 是**仓库相对路径字符串**数组（每条必须是存在的文件）；
  需要限定章节时用可选的 `sections` 说明，不写进路径。case 与平台分配固定为设计 U3 的表：
  E1 claude、E2 codex、E3 claude、E4 claude、E5 codex、E6 claude、E7 codex、E8 claude、E9 pi；各 case 的受测文本与判定要点照该表
  （E4 消费 `data:unspecifiedDecisionGap`：期望 `contract_gaps[].kind == "unspecified_user_visible_decision"`；
  E2/E9 消费 `api:productIntentDelegate`；E8 消费 `data:delegationDisclosure` 的"受托选定"标注）。
- `fixtures/product-experience/subject-prompt.md`：沿用 `fixtures/product-review/subject-prompt.md` 的隔离指令（不读其它文件、动作写成伪调用、不猜预期），
  末尾拼装说明改为"按 case 的 `skill` 列表内联全文"。

**检查意图。** 结构与覆盖：九个 id 齐全、平台分配与表一致、每条 `expected` 与 `situation` 非空、每个 `skill` 路径真实存在。
判据此后不得再改——T-M5-10 的验收会用 sha256 对照。

**Acceptance.**
```bash
python3 -c 'import json,os; d=json.load(open("fixtures/product-experience/thought-tests.json")); assert d["method"] and d["subject_under_test"]; c={x["id"]:x for x in d["cases"]}; want={"E1":"claude","E2":"codex","E3":"claude","E4":"claude","E5":"codex","E6":"claude","E7":"codex","E8":"claude","E9":"pi"}; assert {k:c[k]["platform"] for k in want}==want, c.keys(); assert all(x["situation"] and x["expected"] and x["skill"] and all(os.path.isfile(p) for p in x["skill"]) for x in c.values())' && grep -q 'unspecified_user_visible_decision' fixtures/product-experience/thought-tests.json && grep -q 'delegate' fixtures/product-experience/thought-tests.json && test -s fixtures/product-experience/subject-prompt.md
```
**Write set.** `fixtures/product-experience/thought-tests.json`、`fixtures/product-experience/subject-prompt.md`
**depends_on.** T-M5-01、T-M5-02（E2/E9 的受测文本须已是同步后的适配器）

## T-M5-10 运行思维测试战役并留档（U3 第二步，R-M5-03）

**行为。** 每个 case 一个 fresh-context 子代理（执行方自行派生，可并发 ≤4）。packet = `subject-prompt.md` + 各受测文件全文 + 该 case 的 `situation`，
写到**仓库外**的会话 scratchpad；`expected` 不进 packet。隔离性从宿主轨迹核对：受测代理的工具调用应只有对 packet 的一次 `Read`；多读即该 case 作废重跑
（作废的那次不留在 `cases[]` 里，只在 `notes` 记一笔）。不调用 codex/pi CLI，`platform` 如实写入 `platform_simulated`。
**本任务只判定与记录，不修 skill 文本**；verdict 可以是 `fail`。

产物：
- `docs/validation/product-experience-thought-tests/evidence.json`：字段沿用 `docs/validation/product-review-thought-tests/evidence.json`——
  `round`、`date`、`host`、`tested_version{commit, <受测文件>: sha256}`、`launch{method, isolation, fixtures{path: sha256}}`、
  `cases[]{id, platform_simulated, under_test, prompt_sha256, requested_model, resolved_model, model_source, observed_tool_calls[], duration_ms, verdict, notes}`、
  `responses`、`found_defect`、`limits[]`、`responses_sha256`。
- `docs/validation/product-experience-thought-tests/responses.md`：各 case 受测回答原文，每个 case 一节，标题以 `## E<n>` 开头
  （沿用 `product-review-thought-tests/responses.md` 的 `## P01（…）` 体例；验收按此标题核对九节齐全）。
- `docs/validation/product-experience-thought-tests.md`：`## 方法与证据`、`## 场景判定`（表）、`## 测出的缺陷与修复`、`## 尚未验证`
  （必含：真实宿主对话质量——指向本计划 T-M5-16；真实 codex/pi CLI 未调用；`/run` 内评审的真实截图输入未覆盖）。

**检查意图。** 九个 case 各有 `pass|fail` 判定；每个 case 的观察到的工具调用恰为一次 `Read`；`launch.fixtures` 里记录的 sha256 与判据文件当前内容一致
（证明判据在运行后未被改动）；`responses_sha256` 与 `responses.md` 一致；`responses.md` 里九个 `## E<n>` 小节齐全、每个 case 的
`under_test` / `notes` / `resolved_model` 非空（只有文件存在或只有判定而无答卷原文都过不了）；记录含 `## 尚未验证`。

**Acceptance.**
```bash
python3 -c 'import json,hashlib; h=lambda p: hashlib.sha256(open(p,"rb").read()).hexdigest(); D="docs/validation/product-experience-thought-tests/"; e=json.load(open(D+"evidence.json")); c={x["id"]:x for x in e["cases"]}; assert set(c)>={"E%d"%i for i in range(1,10)}, sorted(c); assert all(x["verdict"] in ("pass","fail") and len(x["observed_tool_calls"])==1 and x["observed_tool_calls"][0]["name"]=="Read" and x["platform_simulated"] and x["prompt_sha256"] for x in c.values()); f=e["launch"]["fixtures"]; assert all(f[p]==h(p) for p in ("fixtures/product-experience/thought-tests.json","fixtures/product-experience/subject-prompt.md")); assert e["responses_sha256"]==h(D+"responses.md"); assert isinstance(e["found_defect"],bool) and e["limits"]; R=open(D+"responses.md",encoding="utf-8").read(); assert all(("\n## E%d"%i) in R for i in range(1,10)), "responses.md needs one ## E<n> section per case"; assert all(x["under_test"] and x["notes"] and x["resolved_model"] for x in c.values())' && grep -q '^## 尚未验证' docs/validation/product-experience-thought-tests.md && grep -q '^## 场景判定' docs/validation/product-experience-thought-tests.md && grep -q '^## 测出的缺陷与修复' docs/validation/product-experience-thought-tests.md
```
**Write set.** `docs/validation/product-experience-thought-tests.md`、`docs/validation/product-experience-thought-tests/evidence.json`、
`docs/validation/product-experience-thought-tests/responses.md`
**depends_on.** T-M5-09

## T-M5-11 思维测试失败回路收口（U3 第三步，R-M5-03）

**行为。** 对 T-M5-10 判 `fail` 的每个 case：(1) 改出错的 skill 文本——手工孪生同一次改动双写；(2) 加**一行**契约钉住新句，落点按文本归属：
claude/meta-skill 语料 → `validate_meta_contracts.py` 里所属模块**已有的** `validate_*_contract` 函数追加一个字面量（不新建函数、不动既有字面量）；
Codex 适配器 → T-M5-05 的 parity 检查块；Pi → `pi/meta-skill/test_contract.py`；product-review / cross-exam → M6 的
`shared/scripts/orchestrator/test_experience_lens_parity.py`，不合适时钉在 `claude/superstorm/scripts/test_superstorm_contract.py`；
(3) 以 `E<n>b` 在修后的文本上按 T-M5-10 同样的隔离方式重测。
记录约定：`evidence.json` 顶层保持第一轮原样，新增 `retests[]`（每项与顶层同形的一轮，case id 为 `E<n>b`）与
`failure_loop {status, fixed_files[], pinned[]}`；`status` 为 `not-needed`（第一轮无 fail）或 `closed`（所有 fail 的 case 重测 pass）。
`responses.md` 追加重测原文（每个重测一节，标题以 `## E<n>b` 开头）并更新 `responses_sha256`；`…thought-tests.md` 的 `## 测出的缺陷与修复` 写明每个缺陷、改动文件、钉住的字面量。
**不得修改判据文件**。重测仍 fail 且需改公共接口/需求才能修 → 以 blocked 上报，不自行扩范围；不为过关而把判定改成 pass。

**检查意图。** 每个 E 的最终判定（取最后一轮）为 pass；`failure_loop.status` 与第一轮事实一致（有 fail 必须是 `closed`，无 fail 必须是 `not-needed`——
该字段只由本任务写入，故命令在本任务完成前不可能通过）；第一轮每个 fail 的 case 在 `responses.md` 里有对应的 `## E<n>b` 重测小节，
且 `closed` 时 `fixed_files[]`、`pinned[]` 非空；判据 sha 仍与第一轮记录一致；所有可能被触碰的契约检查仍绿——包括 product-review 孪生的
差异行数仍为 12、M6 的镜头一致性测试、Codex 契约破坏性用例、`validate_app_experience_pipeline.py .` 与 M1 的同行不变量
（本任务的写集覆盖这些文件，修文本时不得把它们弄红）。

**Acceptance.**
```bash
python3 -c 'import json,hashlib; h=lambda p: hashlib.sha256(open(p,"rb").read()).hexdigest(); D="docs/validation/product-experience-thought-tests/"; e=json.load(open(D+"evidence.json")); final={}; [final.__setitem__(c["id"].rstrip("b"), c["verdict"]) for r in [e]+e.get("retests",[]) for c in r["cases"]]; ids={"E%d"%i for i in range(1,10)}; assert set(final)>=ids and all(final[i]=="pass" for i in ids), final; failed=any(c["verdict"]!="pass" for c in e["cases"]); assert e["failure_loop"]["status"]==("closed" if failed else "not-needed"); assert e["launch"]["fixtures"]["fixtures/product-experience/thought-tests.json"]==h("fixtures/product-experience/thought-tests.json"); assert e["responses_sha256"]==h(D+"responses.md"); R=open(D+"responses.md",encoding="utf-8").read(); fl=e["failure_loop"]; bad=[c["id"] for c in e["cases"] if c["verdict"]!="pass"]; assert all(("\n## %sb"%i) in R for i in bad), "each failed case needs a ## E<n>b retest section"; assert (not failed) or (fl["fixed_files"] and fl["pinned"]), "a closed loop names the fixed files and the pinned literal"' && python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py && python3 shared/scripts/orchestrator/check_codex_meta_skill_parity.py && python3 -m pytest -q pi/meta-skill/test_contract.py && python3 -m pytest -q claude/superstorm/scripts/test_superstorm_contract.py && python3 claude/superstorm/scripts/check_skill_refs.py && [ "$(diff claude/superstorm/skills/product-review/SKILL.md codex/cross-exam-skill/product-review.md | grep -c '^[<>]')" = "12" ] && python3 -m pytest -q shared/scripts/orchestrator/test_experience_lens_parity.py shared/scripts/orchestrator/test_codex_contract_checks.py && python3 claude/meta-skill/scripts/orchestrator/validate_app_experience_pipeline.py . && ! grep -rn "experience_priority" claude/meta-skill/knowledge | grep -v "experience_priority.mode" | grep -v bootstrap | grep -q .
```
**Write set.**（记录文件必写；其余仅在对应 case 失败时才动，且只动出错的那一处）
记录：`docs/validation/product-experience-thought-tests.md`、`docs/validation/product-experience-thought-tests/evidence.json`、
`docs/validation/product-experience-thought-tests/responses.md`。
受测文本及孪生：`claude/meta-skill/knowledge/product-intent-confirmation.md`、`codex/meta-skill/skills/bootstrap.md`、
`pi/meta-skill/skills/bootstrap/SKILL.md`、`claude/meta-skill/knowledge/defensive-patterns.md`、`claude/meta-skill/knowledge/node-spec-template.md`、
`claude/meta-skill/skills/bootstrap/SKILL.md`、`claude/meta-skill/knowledge/bootstrap-planning.md`、`claude/meta-skill/knowledge/suppress-rules.md`、
`claude/meta-skill/knowledge/capabilities/concept-acceptance.md`、`codex/cross-exam-skill/product-review.md`、
`claude/superstorm/skills/product-review/SKILL.md`、`claude/superstorm/skills/cross-exam/SKILL.md`、`codex/cross-exam-skill/SKILL.md`。
契约落点：`claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py`、`shared/scripts/orchestrator/check_codex_meta_skill_parity.py`、
`shared/scripts/orchestrator/test_codex_contract_checks.py`、`pi/meta-skill/test_contract.py`、
`shared/scripts/orchestrator/test_experience_lens_parity.py`、`claude/superstorm/scripts/test_superstorm_contract.py`。
**depends_on.** T-M5-10、T-M5-05、T-M5-02

---

## T-M5-12 文档：CLAUDE.md 与 README.md（U7，R-M5-07）

**行为。**
- `CLAUDE.md`：`## Claude Meta-Skill Structure` 的 "User workflow" 句后补一句——有界面的产品路线上，bootstrap 设置 `experience_priority`、先提案体验方向
  （用户选定或明说委托）、规划体验设计节点与 design/runtime 两阶段体验质量门，`/run` 完成时披露受托决定；同处再补一句升级影响：旧的产品路线项目升级后首次
  `/run` 会得到 `missing_experience_priority`，回交互式 `/bootstrap` 即可。`### Which entry for which situation` 表 `/bootstrap → /run` 行的 Why 列补
  "运行内含体验质量门，`/product-review` 采信其 `docs/experience-review/` 留痕"。
- `README.md`：统一入口段补同义一句中文（含"体验方向"与"体验质量门"）。命令清单处不改。不新增 CHANGELOG。

**检查意图。** 这些字面量今天在两个文件里出现 0 次；逐一钉住。

**Acceptance.**
```bash
grep -q 'experience_priority' CLAUDE.md && grep -q 'missing_experience_priority' CLAUDE.md && grep -q 'docs/experience-review/' CLAUDE.md && grep -q '体验质量门' CLAUDE.md && grep -q '体验方向' README.md && grep -q '体验质量门' README.md
```
**Write set.** `CLAUDE.md`、`README.md`
**depends_on.** 上游汇点 T-M1-07、T-M2-10、T-M3-10、T-M4-07、T-M4-08、T-M6-03、T-M6-04、T-M6-05（见全局约束 1）

## T-M5-13 版本：meta-skill 0.20.0 / superstorm 0.43.0（U6 前半，R-M5-06）

**行为。** 原地精确替换（不重序列化 JSON）：

| 文件 | 从 → 到 |
|---|---|
| `.claude-plugin/marketplace.json` | `0.19.2`→`0.20.0`；`0.42.2`→`0.43.0` |
| `claude/meta-skill/.claude-plugin/{plugin.json,marketplace.json}` | `0.19.2`→`0.20.0` |
| `claude/superstorm/.claude-plugin/{plugin.json,marketplace.json}` | `0.42.2`→`0.43.0` |
| `pi/meta-skill/package.json` | `0.19.2-pi.1`→`0.20.0-pi.1` |
| `claude/meta-skill/SKILL.md` | frontmatter 与 `# Meta-Skill v…` 标题：`0.19.1`→`0.20.0` |
| `claude/meta-skill/skills/bootstrap/SKILL.md` | frontmatter `0.19.1`→`0.20.0`（**只动版本行**） |
| `codex/meta-skill/SKILL.md` | frontmatter 与标题：`0.19.1-codex.2`→`0.20.0-codex.1` |

`pi/cross-exam/package.json` 默认不动；用 `git diff --stat ad5796c4.. -- pi/cross-exam`（只读命令）复核，非空才补丁号 +1。

**检查意图。** `test_package_manifests.py` 证明 manifest 三处一致且仍是合法 JSON；parity 脚本证明 codex 版本跟随 claude bootstrap 版本；
grep 钉住这两者都不覆盖的 frontmatter、标题与 Pi 包版本，并确认旧值已无残留。

**Acceptance.**
```bash
python3 -m pytest -q claude/superstorm/scripts/test_package_manifests.py && python3 shared/scripts/orchestrator/check_codex_meta_skill_parity.py && python3 -m pytest -q pi/meta-skill/test_contract.py && grep -q '^version: "0.20.0"' claude/meta-skill/SKILL.md && grep -q '^# Meta-Skill v0.20.0' claude/meta-skill/SKILL.md && grep -q '^version: "0.20.0"' claude/meta-skill/skills/bootstrap/SKILL.md && grep -q 'version: "0.20.0-codex.1"' codex/meta-skill/SKILL.md && grep -q '^# Meta-Skill v0.20.0-codex.1' codex/meta-skill/SKILL.md && grep -q '"version": "0.20.0-pi.1"' pi/meta-skill/package.json && grep -q '"version": "0.20.0"' .claude-plugin/marketplace.json && grep -q '"version": "0.43.0"' .claude-plugin/marketplace.json && grep -q '"version": "0.20.0"' claude/meta-skill/.claude-plugin/plugin.json && grep -q '"version": "0.43.0"' claude/superstorm/.claude-plugin/plugin.json && ! grep -q '0\.19\.[12]\|0\.42\.2' .claude-plugin/marketplace.json claude/meta-skill/.claude-plugin/plugin.json claude/meta-skill/.claude-plugin/marketplace.json claude/superstorm/.claude-plugin/plugin.json claude/superstorm/.claude-plugin/marketplace.json pi/meta-skill/package.json claude/meta-skill/SKILL.md claude/meta-skill/skills/bootstrap/SKILL.md codex/meta-skill/SKILL.md
```
**Write set.** 上表九个文件 + `pi/cross-exam/package.json`（仅当复核非空）。
**depends_on.** T-M5-11（失败回路可能改同一批 SKILL.md；版本行最后动）

---

## T-M5-14 全量验证与基线对比（U5，R-M5-05）

**行为。** 不改源码。逐条**串行**运行 R-M5-05 的九条命令 + "验收"两条 + 两条跨模块不变量，把结果写入
`docs/superpowers/runs/2026-09-18-product-experience-overhaul/verification-M5.md`：每条命令原文、退出码、passed/failed 计数、耗时；
meta-skill 全量另列失败用例 id 完整清单并与基线四个逐一比对，以及相对基线（1198 passed / 4 failed @ `6a59fe44`；superstorm 255 passed）的通过数增量。
判定：失败集合 ⊆ 基线四个 → 记录中写一行 `status: pass`；出现任何其它失败/收集错误 → `status: regression`，记失败 id 与首段回溯，M5 不得宣告完成
（属 M5 自己文件的当场修并重跑；属别的模块的上报）。基线四个中若有变为通过，记为"基线变化"，不算失败，也不去动它们。

**检查意图。** 验收命令自己重跑整套，不信任记录文件：meta-skill 全量用 `-rfE` 取失败/错误 node id 集合，要求其 ⊆ 基线四个且通过数 ≥ 1198
（零收集、收集报错都会使它失败）；其余套件要求 exit 0；不变量 grep 期望为空；最后核对记录文件已写且结论为 pass。耗时约 8–10 分钟，一次只跑一个。

**Acceptance.**
```bash
python3 -c 'import subprocess,re,sys; r=subprocess.run([sys.executable,"-m","pytest","-q","-rfE","claude/meta-skill/tests/unit"],capture_output=True,text=True); out=r.stdout; bad={l.split()[1] for l in out.splitlines() if l.startswith(("FAILED ","ERROR "))}; U="claude/meta-skill/tests/unit/"; base={U+"test_decision_gate.py::test_a_resolved_choice_restores_readiness_only_with_fresh_evidence[claude]",U+"test_decision_gate.py::test_a_resolved_choice_restores_readiness_only_with_fresh_evidence[codex]",U+"test_evidence_freshness.py::test_fresh_contract_allows_execution_but_cannot_claim_completion[claude]",U+"test_evidence_freshness.py::test_fresh_contract_allows_execution_but_cannot_claim_completion[codex]"}; m=re.search(r"(\d+) passed",out); print(out[-2000:]); print("unexpected:",sorted(bad-base)); sys.exit(0 if r.returncode in (0,1) and m and int(m.group(1))>=1198 and bad<=base else 1)' && python3 -m pytest -q claude/superstorm/scripts && python3 -m pytest -q codex/cross-exam-skill/scripts && python3 -m pytest -q shared/evidence-engine && python3 -m pytest -q shared/visual-acceptance && python3 -m pytest -q shared/scripts/orchestrator && python3 -m pytest -q shared/keep-code-simple && python3 -m pytest -q pi/cross-exam && python3 -m pytest -q pi/meta-skill/test_contract.py codex/meta-skill/test_flow.py codex/meta-skill/test_install.py && python3 shared/scripts/orchestrator/check_codex_meta_skill_parity.py && python3 claude/superstorm/scripts/check_skill_refs.py && python3 -m pytest -q claude/meta-skill/tests/unit/test_consumer_product_regression.py && python3 -m pytest -q claude/superstorm/scripts/test_package_manifests.py && python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py && ! grep -rn "experience_priority" claude/meta-skill/knowledge | grep -v "experience_priority.mode" | grep -v bootstrap | grep -q . && grep -q '^status: pass' docs/superpowers/runs/2026-09-18-product-experience-overhaul/verification-M5.md && grep -q '6a59fe44' docs/superpowers/runs/2026-09-18-product-experience-overhaul/verification-M5.md
```
**Write set.** `docs/superpowers/runs/2026-09-18-product-experience-overhaul/verification-M5.md`
**depends_on.** T-M5-02、T-M5-05、T-M5-07、T-M5-08、T-M5-11、T-M5-12、T-M5-13

## T-M5-15 release 提交正文草稿（U6 后半，R-M5-06）

**行为。** 写 `docs/superpowers/runs/2026-09-18-product-experience-overhaul/release-commit-message.txt`（提交由编排器执行，不 push）：
标题 `release: superstorm 0.43.0, meta-skill 0.20.0 (体验方向与体验质量门)`；正文含 T-M5-14 记录里的各套件数字（原样取自 `verification-M5.md`，不另编）、
"4 个既有失败同 `6a59fe44`，未触碰"、思维测试 pass/fail 计数与 `docs/validation/product-experience-thought-tests.md` 的 `## 尚未验证` 指针、
以及**升级影响**一段：已 bootstrap 的产品路线项目升级后下一次 `/run` 会被 `missing_experience_priority` 拦下，需回交互式 `/bootstrap` 补
`experience_priority`（界面产品随后还会被要求补体验方向、体验设计节点与体验质量门）；`local-change` 路线与无 `task_route` 的遗留 profile 不受影响。

**Acceptance.**
```bash
F=docs/superpowers/runs/2026-09-18-product-experience-overhaul/release-commit-message.txt; head -1 "$F" | grep -q '^release: superstorm 0.43.0, meta-skill 0.20.0' && grep -q '6a59fe44' "$F" && grep -q 'missing_experience_priority' "$F" && grep -q 'local-change' "$F" && grep -q '尚未验证' "$F" && grep -Eq '[0-9]+ passed' "$F" && grep -q '^status: pass' docs/superpowers/runs/2026-09-18-product-experience-overhaul/verification-M5.md
```
**Write set.** `docs/superpowers/runs/2026-09-18-product-experience-overhaul/release-commit-message.txt`
**depends_on.** T-M5-14

---

## T-M5-16 真实宿主验收（reality gate）

`reality_gate: true`。不被任何任务依赖；不阻塞 release 提交。思维测试是模拟决策，"真实会话里 bootstrap 面对真实用户产出好的体验方向并据此交付体验良好的产品"
只能由人在真实宿主里验证。

### Runbook: real-host bootstrap run

人工步骤（由仓库所有者执行；**不要**在 `/Users/aa/workspace/ink-scent` 里操作——授权信封禁止写入该目录）：

1. 安装本分支版本的插件（meta-skill 0.20.0 / superstorm 0.43.0），在 Claude Code 里确认 `/bootstrap` 可用。
2. 新建一个空目录（如 `~/workspace/ink-scent-rerun`），`git init`，在其中开启新的 Claude Code 会话。
3. 把 ink-scent 当初的**原始请求原文**（取自 ink-scent 2026-09-14 的会话记录）粘贴给 `/bootstrap`。正常对话，不要提示它"要做体验设计"。
4. 观察并记录 bootstrap 对话：
   - 是否在讨论体验之前先给出 2–3 条体验方向提案并标明推荐；提案是否回答"谁/什么情境/什么感受/为何回来"，而不是把"碎片化学习"直译成时长选择器/题型清单（症状 1）；
   - 你选定或说"你定"之后，它记的是 `select` 还是 `delegate`；你沉默时它是否自行确认。
5. bootstrap 结束后检查 `.allforai/bootstrap/workflow.json`：是否存在产出 `.allforai/app-design/spec/user-flow-spec.json` 等的体验设计节点，是否有 design / runtime 两阶段体验评审且收尾受其阻断（症状 2）。
6. 执行 `/run` 到完成。打开产物应用：首次使用是否出现要求用户手填"服务地址"之类的输入框；若实现节点遇到未规定的用户可见决定，运行记录里是否出现 `unspecified_user_visible_decision` 而不是自造界面（症状 3）。完成输出是否打印受托决定清单。
7. 执行 `/product-review`：它是否采信 `docs/experience-review/runtime.md` 而不重评。
8. 可选：在 Codex 与 Pi 宿主各重复步骤 2–5，核对适配器行为一致（Pi 用纯文本提问）。
9. 把结果写入 `docs/validation/product-experience-host-run.md`：`## 环境`（宿主、版本、日期、目录）、`## 症状对照`（三行表：`症状 1 直译`、`症状 2 无设计节点`、`症状 3 服务地址输入框`，每行 `verdict: fixed|not-fixed|partial` + 证据指针）、`## 对话摘录`、`## 结论`（一行 `host-run: pass` 或 `host-run: fail`）。

**Acceptance.**
```bash
F=docs/validation/product-experience-host-run.md; grep -q '^## 症状对照' "$F" && grep -q '症状 1' "$F" && grep -q '症状 2' "$F" && grep -q '症状 3' "$F" && [ "$(grep -c 'verdict: \(fixed\|not-fixed\|partial\)' "$F")" -ge 3 ] && grep -q '^host-run: pass' "$F"
```
**Write set.** `docs/validation/product-experience-host-run.md`
**depends_on.** T-M5-14
**runbook_ptr.** `docs/superpowers/plans/2026-09-18-regression-parity-plan.md#runbook-real-host-bootstrap-run`

---

## 需求覆盖

| 需求 | 任务 |
|---|---|
| R-M5-01 | T-M5-06、T-M5-07 |
| R-M5-02 | T-M5-08 |
| R-M5-03 | T-M5-09、T-M5-10、T-M5-11 |
| R-M5-04 | T-M5-01、T-M5-02、T-M5-03、T-M5-04、T-M5-05 |
| R-M5-05 | T-M5-14 |
| R-M5-06 | T-M5-13、T-M5-15 |
| R-M5-07 | T-M5-12 |
| Reality gate 候选 | T-M5-16 |

## 接口

- 暴露 `data:regressionFixtures` — 由 T-M5-07 实现（其验收证明 bad 被拒、good 放行，夹具可被消费）。
- 消费（`requires` 标注）：`api:validateExperienceDesignCoverage`（06、07）、`api:validateExperienceGateFlow`（06、07）、
  `api:productIntentPropose` / `api:productIntentSelect`（01、02、07）、`api:productIntentDelegate`（01、02、09）、
  `data:delegationDisclosure`（02、03、04、09）、`data:experienceCritiqueReport`（07、08）、`data:unspecifiedDecisionGap`（09）。
