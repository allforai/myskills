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
