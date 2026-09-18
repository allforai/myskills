# M3 experience-gate — 体验质量门

总览：`2026-09-18-product-experience-overhaul-overview.md`。依赖 M1（`data:experiencePriority`、
`data:experienceDesignArtifacts`）、M2（`data:experienceDirectionIntent`）。

## 问题

- 应用没有质量门。`skills/app-design/40-qa/` 只有 `flow-coverage-qa`（路径是否存在）与
  `app-design-closure-qa`（追溯是否闭合），都判"有没有"，不判"好不好"。
- 游戏的 Must #8（`bootstrap-planning.md:162`）只是散文。`validate_game_creative_pipeline.py` 只检查
  插件源码里的措辞接线，且**无任何调用方**；生成的项目里没有任何检查要求评审节点存在，或要求
  `concept-acceptance` `hard_blocked_by` 它。`capabilities/concept-acceptance.md` 不提创意评审。
  应用与游戏是同一个漏洞。
- 好坏判断完全在事后（`user_steps: ["/cross-exam", "/product-review"]`），无人值守运行内部无自我纠正。

## 需求

- **R-M3-01 新子 skill：`skills/app-design/40-qa/experience-quality-critique/SKILL.md`。**
  结构对齐 `skills/game-creative/40-qa/creative-quality-critique/SKILL.md`。两个阶段，同一 skill：
  - `stage: "design"`（实现前）：输入 M1 的应用设计产物、M2 的体验方向意图及其 `acceptance`；
  - `stage: "runtime"`（实现后）：再加截图清单、`.allforai/verify/` 下的视觉评审与运行时报告。
  缺失的可选输入记为 `insufficient_evidence`，不得静默忽略。
- **R-M3-02 输出契约。** `.allforai/app-design/qa/experience-quality-critique-<stage>.json` 与同名
  `.html`（`review_language: "zh-CN"`）。finding 形状与游戏侧一致：`finding_id`、`dimension`、
  `judgment_type ∈ {contract_defect, evidence_based_critique, llm_judgment, insufficient_evidence}`、
  `severity ∈ {blocker, major, minor, note}`、`confidence`、`claim`、`reasoning`、`evidence_refs[]`、
  `counterexample_or_comparison`、`repair_route{owner_skill, owner_artifact, requested_change,
  rerun_from_node_id}`、`blocks[]`。阶段门：`must_fix_before_implementation`、
  `must_fix_before_release`、`recommended_iterations`。沿用游戏侧规则：纯 `llm_judgment` 不得成为硬阻断；
  硬阻断须是 `contract_defect` 或高置信、指到具体产物/界面/截图的 `evidence_based_critique`。
- **R-M3-03 判据（维度）。** 与 `/product-review` 同源的五个镜头：`onboarding`（引导）、
  `process_feedback`（过程反馈）、`next_step`（下一步）、`state_consistency`（状态一致）、
  `return_reason`（回来理由）；另加 `mainline`（主线不是功能入口网格）、
  `direction_fidelity`（是否兑现 M2 体验方向的 `acceptance`，是否把用户用语直译成功能）、
  `audience_leak`（部署方/开发者配置出现在最终用户界面，判据见 M4）。反面对照
  `consumer-maturity-patterns.md` §B 三个反模式。每条 finding 必须指到谁、什么情境、哪件事、
  观察到什么；指不出观察的只是口味，不写入。
- **R-M3-04 独立评审。** 评审必须由未编写被评产物的 fresh-context 评审方执行，语义沿用 ADR-0002/0003
  的独立视觉评审；node-spec 写明评审方不得读取作者节点的推理过程，只读产物与证据。
- **R-M3-05 登记。** `skills/app-design/PACK.md` 增加该子项与 canonical 路径，并加判定类型与输出根
  一节（对齐 `game-creative/PACK.md:40-81`）；`capabilities/app-design.md` 的 Canonical Node Registry
  与 Sub-Skill Mapping 增加该节点。满足 `validate_skills.py:166-167` 的孤儿检查。
- **R-M3-06 规划法 Must #9。** `bootstrap-planning.md` 新增 "Experience quality gate (products with UI)"：
  `experience_priority.mode ∈ {consumer, mixed}` 的非游戏产品路线，设计产物完成后、任何界面实现节点之前
  跑 `stage: "design"`；最后一个 UI/product-verify/visual QA 之后跑 `stage: "runtime"`；
  收尾/验收节点 `hard_blocked_by` runtime 评审；`must_fix_*` 走所属 pack 的修复回路。
  `suppress-rules.md` 增加一行：`experience_priority.mode = none` → 抑制体验质量门。
  `capabilities/concept-acceptance.md` 写明其受创意/体验评审阻断。
- **R-M3-07 无人值守修复路由。** 评审的 `must_fix_*` 非空即该产物不通过：
  `scripts/orchestrator/check_artifacts.py` 的硬失败子集（`:439-451`）纳入
  `must_fix_before_implementation`、`must_fix_before_release`。
  设计阶段的 must-fix 由产出该设计产物的节点修复并重跑设计评审；运行阶段的 must-fix 归入
  `experience_gaps`，由实现修复节点处理并重跑受影响的 QA 与 runtime 评审。两者都在
  `unattended-run-readiness-spec.json.required_repair_loops` 中声明，`max_attempts` 沿用既有预算规则。
  预算耗尽时按既有 Run Policy 处理，不新增询问。
- **R-M3-08 确定性校验：应用与游戏同时覆盖。** `validate_bootstrap.py` 新增
  `validate_experience_gate_flow(bdir)`，注册进 `main()`、`__all__`、`structural_gate_blockers`。
  触发：产品路线且 `experience_priority.mode ∈ {consumer, mixed}` 且工作流含实现节点。阻断码：
  - `missing_experience_gate`：应用无引用 `experience-quality-critique` 的节点 / 游戏无引用
    `creative-quality-critique` 的节点；
  - `implementation_not_blocked_by_design_critique`：（应用）界面实现节点不传递依赖设计阶段评审；
  - `closure_not_blocked_by_experience_gate`：收尾/`concept-acceptance`/`pipeline-closure-verify`
    节点不传递依赖运行阶段评审（游戏：实现后的那次创意评审）；
  - `experience_gate_without_repair_loop`：评审节点不在任何 `required_repair_loops.qa_node_ids` 内。
- **R-M3-09 源码接线校验。** 新增 `scripts/orchestrator/validate_app_experience_pipeline.py`
  （对齐 `validate_game_creative_pipeline.py`：PACK 列出每个子 skill、必备术语、bootstrap 语料提及）。
  两个 pipeline 校验器都加入 `.githooks/pre-commit` 的校验器清单，使其不再无人调用。
  `validate_meta_contracts.py` 新增 `validate_experience_gate_contract(errors)` 钉住 Must #9 与新术语。
- **R-M3-10 事后可采信的留痕。** 每次评审另写一份人读摘要到项目的
  `docs/experience-review/<stage>.md`（结论、must-fix、各镜头一行观察、证据限制、评审日期与被评提交）。
  这是 `/product-review` 能读到的位置（它不读 `.allforai/`）。
- **R-M3-11 测试。** `tests/unit/test_validate_bootstrap.py`：R-M3-08 四个码各一拒绝用例，应用与游戏各
  一通过用例，`mode == none` 与 `local-change` 不触发。新文件
  `tests/unit/test_validate_app_experience_pipeline.py`（接受最小夹具、拒绝未列出的子 skill、
  拒绝缺术语）。`tests/unit/test_check_artifacts_measurement.py` 或同类文件增加 must_fix 非空即失败的用例。
  `tests/unit/test_validate_unattended_readiness.py` 的回路夹具按需补新条目。

## 接口

- 暴露：`data:experienceCritiqueReport`（JSON 契约）、`data:experienceReviewDoc`（`docs/` 下的摘要）、
  `data:experienceLensVocabulary`（R-M3-03 的维度名单）、`api:validateExperienceGateFlow`（校验函数与四个码）。
- 消费：`data:experiencePriority`、`data:experienceDesignArtifacts`（M1）；
  `data:experienceDirectionIntent`（M2）；`data:settingsAudience`、`data:unspecifiedDecisionGap`（M4）。

## 不做

- 不改游戏创意评审 skill 的内容与输出 schema；只让它的存在与阻断关系被确定性校验。
- 不给评审打"客观分"冒充事实；分数仍带 `confidence`，硬阻断规则同游戏侧。
- 不在运行中向用户提问。

## 验收

```bash
python3 -m pytest -q claude/meta-skill/tests/unit/test_validate_bootstrap.py \
  claude/meta-skill/tests/unit/test_validate_app_experience_pipeline.py \
  claude/meta-skill/tests/unit/test_validate_unattended_readiness.py
python3 claude/meta-skill/scripts/orchestrator/validate_app_experience_pipeline.py
python3 claude/meta-skill/scripts/orchestrator/validate_game_creative_pipeline.py
python3 claude/meta-skill/scripts/orchestrator/validate_skills.py claude/meta-skill/skills
python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py
```

## Detailed design

设计日期 2026-09-18，对照分支 `product-experience-overhaul` @ `80e707e1` 的实际文件。以下路径除注明外均相对
`claude/meta-skill/`（canonical 树；codex/pi 的 `scripts/`、`tests/`、`knowledge/capabilities/` 经符号链接自动跟随，
本模块不碰任何手工孪生文件）。执行次序上 M1、M2、M4 先于 M3 落地；本设计写明了对它们的依赖点。

### Spec corrections（规格引用与现状不符之处，按现状设计）

1. **`validate_game_creative_pipeline.py` 并非"无任何调用方"。** `.githooks/pre-commit` 已在校验器清单里调用它
   （`python3 …/validate_game_creative_pipeline.py .`）。真正缺的是：(a) 应用侧没有对应校验器；
   (b) 两者都只查插件源码措辞，**生成的项目**里没有任何检查。R-M3-09 的 hook 改动因此缩为"只新增应用那一行"，
   游戏那一行已在，保持不动。R-M3-08 照原样覆盖 (b)。
2. **`.allforai/verify/` 目录不存在。** 视觉评审与运行时报告的真实位置是
   `.allforai/product-verify/`（`ui-screenshot-manifest.json`、`visual-review-1.json`、`verify-report.json`）与
   `.allforai/visual-verify/`（`screenshot-manifest.json`、`visual-review-1.json`、`visual-review-2.json`、
   `visual-verify-report.json`）。R-M3-01 runtime 阶段的输入表用这两处。
3. **游戏侧的阶段门嵌在 `gates{}` 里，不在顶层。** `creative-quality-critique` 的 JSON 是
   `{"gates": {"must_fix_before_release": [...]}}`；而 `check_artifacts._production_gap_error` 只读顶层键
   （`data.get(field)`）。只把两个字段名加进 `PRODUCTION_GAP_FIELDS` 与硬失败子集，对游戏报告（以及与之同形的
   应用报告）**不会生效**。设计见 U5：对这两个字段同时读顶层与 `gates.<field>`。
4. 行号漂移：硬失败子集现位于 `check_artifacts.py:408-420`（规格记 `:439-451`）；
   `game-creative/PACK.md` 的 Boundary/Shared Outputs 为 `:40-69`；孤儿检查为 `validate_skills.py:166-167`（一致）。
5. `tests/unit/test_validate_bootstrap.py` 现有用例**没有** host 参数化（`load("validate_bootstrap")` 单宿主，
   codex 侧是同一文件的符号链接）。本模块新增用例沿用该文件现状，不加 host 参数化。
6. `validate_app_design_flow`（`validate_bootstrap.py:1257-1320`）对 `capability == "app-design"` 的节点有两条既有约束：
   `app-design-finalize` 必须 `hard_blocked_by` 全部 app-design 节点；非 app-design 节点不得直接依赖
   `app-design-finalize`。这决定了两个评审节点的摆位与 capability（见 U6），否则会成环或误报。

### Architecture

同一个门的三面，七个单元：

```
 U1 experience-quality-critique/SKILL.md ──(data:experienceCritiqueReport, data:experienceLensVocabulary,
        │                                   data:experienceReviewDoc)
        ├─ U2 登记：app-design/PACK.md + capabilities/app-design.md           (R-M3-05)
        ├─ U6 规划法：bootstrap-planning Must #9 + suppress-rules + concept-acceptance (R-M3-06/07)
        │
 生成的项目 ─ workflow.json / node-specs / readiness-spec
        ├─ U3 validate_experience_gate_flow  (api:validateExperienceGateFlow)   (R-M3-08)  bootstrap 与 /run 边界
        └─ U5 check_artifacts must_fix 硬失败                                    (R-M3-07)  节点完成判定
 插件源码
        └─ U4 validate_app_experience_pipeline.py + validate_meta_contracts 钉住 + pre-commit (R-M3-09)
 U7 测试                                                                        (R-M3-11)
```

数据流（无人值守 `/run`）：设计节点产出 `data:experienceDesignArtifacts` → **design 评审节点**（fresh-context）
读产物 + `data:experienceDirectionIntent` → 写 `experience-quality-critique-design.{json,html}` 与
`docs/experience-review/design.md` → `check_artifacts` 见 `gates.must_fix_before_implementation` 非空判该节点未完成 →
编排器按 `required_repair_loops` 派发设计修复节点 → 评审重跑 → 通过后 `app-design-finalize` / 实现节点解锁 →
实现 + verify → **runtime 评审节点** 同理（字段 `must_fix_before_release`，并镜像进 `experience_gaps`）→
实现修复节点 → 重跑受影响 QA 与 runtime 评审 → 收尾节点解锁。预算耗尽走既有 Run Policy，不新增询问。

### U1 — 子 skill `experience-quality-critique`（R-M3-01/02/03/04/10）

**文件（create）：** `skills/app-design/40-qa/experience-quality-critique/SKILL.md`

**Frontmatter：** `name: app-design-40-qa-experience-quality-critique`（沿用同目录 `app-design-40-qa-app-design-closure-qa`
的命名式）；`description` 一句英文，含 "evidence-typed findings, Chinese review HTML, repair routing"。

**章节（与 `creative-quality-critique/SKILL.md` 逐节对齐）：** Purpose / Stages / Reviewer Independence /
Input Contract / Output Contract / Invocation Contract / Lenses / Method / Judgment Rules /
Review Doc / Automatic Validation / Completion Conditions。

- **Purpose** 必须写明：这是运行内的自我纠正门，不是交付裁决；"做没做完 / 好不好"的最终判断仍属运行后的
  `/cross-exam` 与 `/product-review`（ADR-0008）。本 skill 不调用它们，也不以它们命名节点
  （`validate_unattended_readiness.py` 的 `verdict_entry_planned_as_node` 会拒绝 id/capability 含
  `cross-exam`、`product-review` 的节点）。
- **Stages：** `stage: "design"` 与 `stage: "runtime"`，由调用节点经 Invocation Contract 的 `mode` 传入。
- **Reviewer Independence（R-M3-04）：** 评审由未编写被评产物的 fresh-context 评审方执行，语义沿用 ADR-0002/0003
  （评审上下文不得是产出被评产物的上下文；同上下文自评是降级，不得计为通过）。node-spec 必须写明：评审方只读
  Input Contract 列出的产物与证据，**不得读取作者节点的推理过程**、对话转录或其 node-spec 的执行笔记。
  JSON 记录 `reviewer: {context: "fresh-subagent|other-platform-cli", authored_reviewed_artifacts: false}`；
  为 `true` 时状态只能是 `FAILED_VALIDATION`。
- **Input Contract（表格，Required 列）：**

  | Input | design | runtime | 来源 |
  |---|---|---|---|
  | `.allforai/app-design/concept/job-story-spec.json` | yes | yes | `data:experienceDesignArtifacts`（M1） |
  | `.allforai/app-design/spec/user-flow-spec.json` | yes | yes | 同上 |
  | `.allforai/app-design/spec/screen-requirements-spec.json` | yes | yes | 同上 |
  | `.allforai/app-design/spec/permissions-notifications-settings-spec.json` | no | no | 同上；其 `audience`/`provisioning` 即 `data:settingsAudience`（M4） |
  | `.allforai/app-design/spec/app-surface-topology-spec.json`（`service_endpoints[]`） | no | no | `data:settingsAudience`（M4） |
  | `.allforai/product-concept/product-concept.json` 中 `topic == "experience-direction"` 的已确认意图及其 `acceptance` | yes | yes | `data:experienceDirectionIntent`（M2） |
  | `.allforai/bootstrap/bootstrap-profile.json` 的 `experience_priority.mode` | yes | yes | `data:experiencePriority`（M1） |
  | `.allforai/app-design/qa/experience-quality-critique-design.json` | — | no | 上一阶段结论 |
  | `.allforai/product-verify/ui-screenshot-manifest.json`、`.allforai/visual-verify/screenshot-manifest.json` | — | yes（至少其一） | 截图清单 |
  | `.allforai/product-verify/visual-review-1.json`、`.allforai/visual-verify/visual-review-{1,2}.json` | — | no | 视觉评审 |
  | `.allforai/product-verify/verify-report.json`、`.allforai/visual-verify/visual-verify-report.json` | — | no | 运行时报告 |
  | 各实现/验证节点产物里的 `contract_gaps[]`（`kind == "unspecified_user_visible_decision"`） | — | no | `data:unspecifiedDecisionGap`（M4） |

  缺失的可选输入：在 `evidence_inventory[]` 记 `available: false`，并产生一条 `judgment_type: "insufficient_evidence"`
  的 finding；不得静默忽略。缺失的必需输入：返回 `UPSTREAM_DEFECT`。体验方向意图带 `auto_decided: true` 时照常评审，
  并在报告 `direction.delegated: true` 留痕（不因委托而放宽或加严）。
- **Output Contract（`data:experienceCritiqueReport`）：**
  `.allforai/app-design/qa/experience-quality-critique-<stage>.json` 与同名 `.html`，`<stage> ∈ {design, runtime}`。

  ```json
  {
    "schema_version": "1.0",
    "stage": "design|runtime",
    "status": "COMPLETED|COMPLETED_WITH_LIMITS|FAILED_VALIDATION|UPSTREAM_DEFECT",
    "project_id": "string",
    "review_language": "zh-CN",
    "reviewed_at": "<ISO-8601 with offset>",
    "reviewed_commit": "<git sha | 'uncommitted' | 'no-git'>",
    "reviewer": {"context": "fresh-subagent", "authored_reviewed_artifacts": false},
    "direction": {"intent_id": "string", "delegated": false, "acceptance": ["string"]},
    "evidence_inventory": [{"artifact_path": ".allforai/...", "artifact_type": "json|html|image|runtime_report|directory",
                            "available": true, "used_for": ["onboarding"], "limitations": []}],
    "lenses": {"<dimension>": {"observation": "有|缺|未查", "summary": "string", "confidence": 0.0}},
    "findings": [{
      "finding_id": "experience-001",
      "dimension": "onboarding|process_feedback|next_step|state_consistency|return_reason|mainline|direction_fidelity|audience_leak",
      "judgment_type": "contract_defect|evidence_based_critique|llm_judgment|insufficient_evidence",
      "severity": "blocker|major|minor|note",
      "confidence": 0.0,
      "claim": "string", "reasoning": "string",
      "observation": {"who": "string", "circumstance": "string", "task": "string", "observed": "string"},
      "evidence_refs": [".allforai/..."],
      "counterexample_or_comparison": "string",
      "repair_route": {"owner_skill": "app-design/<child>|implement|bootstrap", "owner_artifact": ".allforai/...|<source path>",
                       "requested_change": "string", "rerun_from_node_id": "string"},
      "blocks": ["must_fix_before_implementation"]
    }],
    "gates": {"must_fix_before_implementation": [], "must_fix_before_release": [], "recommended_iterations": []},
    "experience_gaps": [],
    "overall_recommendation": {"decision": "proceed|iterate_before_implementation|iterate_before_release|blocked_by_missing_evidence",
                               "rationale": "string", "top_repairs": []}
  }
  ```

  finding 形状与游戏侧逐字段一致，仅多一个 `observation{}`（R-M3-03 的"谁/情境/哪件事/观察到什么"）。阶段门与游戏侧
  一样放在 `gates{}` 内，元素为 `finding_id`。`design` 阶段只可填 `must_fix_before_implementation`，`runtime` 阶段只可填
  `must_fix_before_release`；另一项恒为 `[]`。`runtime` 阶段把每条 `must_fix_before_release` 镜像为
  `experience_gaps[]` 的一项 `{finding_id, where, requested_change}`（R-M3-07 的路由载体）；`design` 阶段
  `experience_gaps` 恒为 `[]`。`lenses.*` 不是客观分：只有 `有|缺|未查` 加 `confidence`，没有数值分。
- **Invocation Contract**（须过 `validate_skills.py` 的 json 块规则：`skill`、`mode`、`output_root`、路径以 `.allforai/` 起）：

  ```json
  {"skill":"app-design/experience-quality-critique","mode":"design","input_paths":{"job_stories":".allforai/app-design/concept/job-story-spec.json","user_flows":".allforai/app-design/spec/user-flow-spec.json","screen_requirements":".allforai/app-design/spec/screen-requirements-spec.json","settings":".allforai/app-design/spec/permissions-notifications-settings-spec.json","product_concept":".allforai/product-concept/product-concept.json","profile":".allforai/bootstrap/bootstrap-profile.json"},"output_root":".allforai/app-design/qa"}
  ```

  Supported modes: `design`, `runtime`。SKILL.md 内其它 json 围栏块（Output schema）含 `|` 枚举串但必须是**可解析 JSON**
  （`validate_skills.py` 会解析每个 json 块；沿用游戏侧把枚举写进字符串值的做法，注释一律不写进块内）。
- **Lenses（`data:experienceLensVocabulary`，R-M3-03）：** 八个标识符按此顺序、此拼写出现：
  `onboarding`、`process_feedback`、`next_step`、`state_consistency`、`return_reason`、`mainline`、
  `direction_fidelity`、`audience_leak`。前五个写明"与 `/product-review` 第 4 问五个镜头同名同义"
  （引导/过程反馈/下一步/状态一致/回来理由；M6 的 `test_experience_lens_parity.py` 会在本文件里找这五个标识符）。
  每个镜头一段：问什么、design 阶段看哪份产物、runtime 阶段看哪类证据。
  `direction_fidelity`：逐条核对体验方向意图的 `acceptance`；并检查**直译**——用户用语被逐字变成功能/控件
  （例："碎片化学习" → 时长选择器 + 题型清单）。`audience_leak`：判据不在此重述，引用
  `${CLAUDE_PLUGIN_ROOT}/knowledge/defensive-patterns.md` Pattern J 与
  `${CLAUDE_PLUGIN_ROOT}/knowledge/capabilities/product-verify.md` 的 "audience leak" 检查（M4）；
  design 阶段读设置规格的 `audience`/`provisioning`，runtime 阶段读截图与 verify 报告。
  反面对照：`${CLAUDE_PLUGIN_ROOT}/knowledge/consumer-maturity-patterns.md` §B 三个反模式
  （The Compressed Admin Panel / The Concept Demo / Feature Checklist Design），命中时写进
  `counterexample_or_comparison`。
  **口味过滤：** `observation` 四个字段任一写不出具体内容的 finding 不写入报告。
- **Judgment Rules：** 四个 `judgment_type` 的定义与游戏侧一致；硬阻断规则逐句沿用：纯 `llm_judgment` 永不进入
  `must_fix_*`，只能进 `recommended_iterations`；`must_fix_*` 只接受 `contract_defect`，或 `confidence >= 0.8` 且
  `evidence_refs` 指到具体产物字段/界面 id/截图路径的 `evidence_based_critique`。M4 的
  `unspecified_user_visible_decision` 缺口、缺 `audience` 的设置项、非 `end-user` 项出现在界面规格，均属
  `contract_defect`。
- **Review Doc（`data:experienceReviewDoc`，R-M3-10）：** 每次评审另写项目仓库内的
  `docs/experience-review/<stage>.md`（覆盖写，始终是最新一次）。固定小节与顺序：
  `# 体验评审 — <stage>`；`评审日期` / `被评提交` / `评审方` 三行；`## 结论`（`overall_recommendation.decision` + 一句理由；
  体验方向为委托选定时注明）；`## Must-fix`（每条：finding_id、镜头、观察、所属产物、状态 `open`）；
  `## 各镜头观察`（八行，每行 `<标识符>（中文名）: 有|缺|未查 · <一句观察>`）；`## 证据限制`。
  摘要必须自足：`/product-review` 不读 `.allforai/`，所以观察与 must-fix 要写成整句，不能只留一个指向 `.allforai/` 的路径。
  该路径要作为评审节点的 `exit_artifacts` 之一（见 U6），否则没人保证它被写出。
- **Automatic Validation / Completion Conditions：** 对齐游戏侧清单，替换字段名；增加三条：`stage` 与文件名后缀一致；
  另一阶段的 `must_fix_*` 为空；`docs/experience-review/<stage>.md` 存在且 Must-fix 小节与 `gates` 一致。

### U2 — 登记（R-M3-05）

- **`skills/app-design/PACK.md`（edit，纯追加）：** Current Children 表加一行
  `40-qa | experience-quality-critique | Evidence-typed experience critique in two stages (design, runtime) across the eight experience lenses, with repair routing.`；
  Canonical Invocation Paths 加
  `${CLAUDE_PLUGIN_ROOT}/skills/app-design/40-qa/experience-quality-critique/SKILL.md`；在 `## Boundary` 之后新增两节：
  `## Judgment Types`（四类定义 + "Only `contract_defect` and high-confidence `evidence_based_critique` may create hard
  blockers"，文字对齐 `game-creative/PACK.md` 的 Boundary 段）与 `## Shared Outputs`
  （`.allforai/app-design/qa/` 为评审输出根；`docs/experience-review/` 为人读摘要根；中文人读、英文稳定键）。
  frontmatter `description` 末尾由 "then closure QA" 改为 "then closure QA and the experience quality gate"。
- **`knowledge/capabilities/app-design.md`（edit）：**
  - Canonical Node Registry 表在 `app-design-finalize` 行**之前**加两行：
    `experience-critique-design | independent-reviewer | app-design/qa/experience-quality-critique-design.html | app-design/qa/experience-quality-critique-design.json | 所选全部 spec 节点（ia-design、user-flow-design、interaction-design 及所选可选节点）`；
    `experience-design-repair | lead-ux | — | 被修复的 spec 产物 | experience-critique-design`。
    表下 "Required nodes" 一句后追加：这两个节点在 `experience_priority.mode ∈ {consumer, mixed}` 时必选（规则见
    `bootstrap-planning.md` Must #9），`mode == none/admin` 时不加；**不**把它们加入
    `validate_bootstrap.APP_DESIGN_REQUIRED_NODES`（存在性由 U3 按产物判定，不按节点名）。
  - Sub-Skill Mapping 表加三行：`experience-critique-design → app-design/40-qa/experience-quality-critique`（mode `design`）；
    `experience-design-repair → finding.repair_route.owner_skill 所指的 app-design 子 skill`；
    `experience-critique-runtime → app-design/40-qa/experience-quality-critique`（mode `runtime`），并注明它**不是**
    app-design 阶段节点：`capability` 不得为 `app-design`（否则 `validate_app_design_flow` 会要求 finalize 等它，成环），
    位于最后一个 UI/product-verify/visual QA 之后。
  - 若 M1 已按 R-M1-05 改写 Human Gate 段，本模块不再碰该段；两个新节点一律 `human_gate: false`。
- 孤儿检查：PACK 的 canonical 路径 + capability 文件里的 slug `app-design/40-qa/experience-quality-critique`
  都落在 `validate_skills._reference_roots` 内，`validate_skills.py:166-167` 通过。

### U3 — `validate_experience_gate_flow`（R-M3-08，`api:validateExperienceGateFlow`）

**文件（edit）：** `scripts/orchestrator/validate_bootstrap.py`。全部为追加：常量 + 两个函数紧接在 M1 的
`validate_experience_design_coverage` 之后（若其位置不同，则放在 `validate_app_design_flow` 之后）；`main()` 里
`validate_app_design_flow` 那组调用后加一行；`__all__` 加两名；`structural_gate_blockers` 的 return 表达式尾部加一项。

```python
EXPERIENCE_GATE_PRODUCT_ROUTES = ("new-product", "product-reconstruction")
EXPERIENCE_GATE_MODES = ("consumer", "mixed")
APP_EXPERIENCE_CRITIQUE = "experience-quality-critique"
GAME_CREATIVE_CRITIQUE = "creative-quality-critique"
EXPERIENCE_GATE_CLOSURE_CAPABILITIES = ("concept-acceptance", "pipeline-closure-verify")

def experience_gate_flow_findings(bdir: str) -> list:   # typed: [{code, message, node_id?}] via _structural
def validate_experience_gate_flow(bdir: str) -> list:   # return _rendered(experience_gate_flow_findings(bdir))
```

沿用 `repair_loop_declaration_findings` / `validate_repair_loop_declaration` 的 findings + rendered 双函数式，
因为 `structural_gate_blockers` 要的是类型化 dict，CLI 要的是 `code: message` 字符串。

**读取：** `bootstrap-profile.json`、`workflow.json`、`node-specs/`（只经 M1 的界面实现节点识别函数间接读）、
`unattended-run-readiness-spec.json`。任一必需文件缺失/不可解析/根不是 object、`nodes` 不是 list → 返回 `[]`
（形状故障归 `workflow_shape_findings` 等既有门，不在此重述）。全程用 `_addressable_nodes`，任何输入下不抛异常。

**触发（全部满足才检查）：**
1. `profile["task_route"] in EXPERIENCE_GATE_PRODUCT_ROUTES`（`local-change` 与缺失均不触发）；
2. `profile["experience_priority"]` 是 dict 且其 `mode in EXPERIENCE_GATE_MODES`（缺失、`none`、`admin`、旧的平铺字符串
   均不触发——缺失由 M1 的 `missing_experience_priority` 负责；因此 M1 之前生成的旧项目在 `/run` 边界不会被本门误伤）；
3. 界面实现节点集合 `impl` 非空。**`impl` 必须取自 M1 为 `validate_experience_design_coverage` 落地的那个识别函数**
   （R-M1-07："复用 `validate_mobile_ui_coverage` 与 `_matching_nodes` 的既有办法"）。M3 不得另写一套启发式；
   若 M1 把识别逻辑内联在其校验函数里，M3 的第一步是把它原样抽成模块级私有函数（行为不变、M1 的测试不变）再复用。

**节点分类（按产物，不按节点名、不按 capability）：**
- 游戏与否：`profile.get("is_game_project") is True`。
- 评审节点：`_artifact_paths(node["exit_artifacts"])` 中任一路径含子串 `APP_EXPERIENCE_CRITIQUE`（应用）/
  `GAME_CREATIVE_CRITIQUE`（游戏）。仅在 node-spec 正文里"提到"该 skill 的节点（修复节点、收尾节点会读评审报告）
  不算评审节点——这是对规格"引用…的节点"的收紧，理由是避免读者节点被误当成门。
- 应用的阶段：路径以 `experience-quality-critique-design.json` 结尾 → design 评审；以 `-runtime.json` 结尾 → runtime 评审。
- 游戏的"实现后的那次"：评审节点 `c` 满足存在 `i ∈ impl` 使 `_downstream_of(nodes, i["node_id"], c_id)` 为真
  （`c` 传递依赖某个实现节点）。游戏 skill 的输出路径固定，两次评审同路径，故用图位置而非文件名区分。
- 收尾节点：`capability in EXPERIENCE_GATE_CLOSURE_CAPABILITIES`。（`<gate>-rerun` 也是 `concept-acceptance`，
  它经 `<gate>` 传递依赖评审，自然满足。）

**四个阻断码（消息为英文，风格同邻近函数；`node_id` 锚到违规节点）：**

| code | 条件 |
|---|---|
| `missing_experience_gate` | 应用：缺 design 评审节点或缺 runtime 评审节点（各报一条，消息点名缺的阶段与应写的产物路径）。游戏：没有任何评审节点（一条）。 |
| `implementation_not_blocked_by_design_critique` | 仅应用，且存在 design 评审节点时：对每个 `i ∈ impl`，不存在 design 评审节点 `d` 使 `_downstream_of(nodes, d, i)`。 |
| `closure_not_blocked_by_experience_gate` | 存在收尾节点时：对每个收尾节点 `k`，不存在"runtime 评审（应用）/ 实现后的创意评审（游戏）"节点 `r` 使 `_downstream_of(nodes, r, k)`。没有这样的 `r` 时每个收尾节点各报一条。 |
| `experience_gate_without_repair_loop` | 对每个评审节点 `c`（应用两阶段、游戏全部）：`c` 不在任何 `required_repair_loops[*]` 的 `_declared_node_ids(loop, "qa_node_ids", "qa_nodes")` 内。readiness spec 缺失或 `required_repair_loops` 不是 list 视同未声明。 |

**注册（三处，各一行）：**
- `main()`：`errors.extend(validate_experience_gate_flow(bdir))`，放在跨节点检查组内。
- `__all__`：`"validate_experience_gate_flow"`、`"experience_gate_flow_findings"`。
- `structural_gate_blockers`：return 表达式追加 `+ experience_gate_flow_findings(bdir)`；docstring 补半句说明。
  效果：`validate_unattended_readiness.py` 在 `/run` 边界经此入口重判，bootstrap 放行后被手改坏的图同样被拒。

**错误处理：** 只读、纯函数、无副作用；不可解析输入返回 `[]`；环状 `hard_blocked_by` 由 `_downstream_of` 的 `seen` 集合兜住。

### U4 — 源码接线校验与契约钉住（R-M3-09）

- **`scripts/orchestrator/validate_app_experience_pipeline.py`（create）：** 以 `validate_game_creative_pipeline.py`
  为模板逐段对应（同样的 `_read`/`_bootstrap_corpus`/`_has_term`/`_canonical_refs`/`main(argv)`，`repo_root` 默认 `.`）。
  - 入口函数：`validate_app_experience_pipeline(repo_root: str) -> list[str]`。
  - 必需文件：`skills/app-design/PACK.md`、`skills/app-design/40-qa/experience-quality-critique/SKILL.md`；缺则只报缺失并返回。
  - 子 skill 全列：`skills/app-design/**/SKILL.md` 每个都须以 canonical 路径出现在 PACK
    （`_canonical_refs` 的正则前缀改为 `app-design/`）；错误文案 `app-design/PACK.md: missing canonical child path skills/<ref>`。
  - `REQUIRED_PARENT_TERMS`：`experience-quality-critique`、其 canonical 路径、四个 `judgment_type`、
    `.allforai/app-design/qa/`、`docs/experience-review/`。
  - `REQUIRED_CRITIQUE_TERMS`：两个阶段的四个输出路径（`…-design.json/.html`、`…-runtime.json/.html`）、
    `docs/experience-review/`、八个镜头标识符、四个 `judgment_type`、`must_fix_before_implementation`、
    `must_fix_before_release`、`recommended_iterations`、`experience_gaps`、`review_language`、`zh-CN`、
    `repair_route`、`counterexample_or_comparison`、`rerun_from_node_id`、`fresh-context`、`insufficient_evidence`。
  - `BOOTSTRAP_CORPUS`（与游戏版一样写成相对仓库根、带 `claude/meta-skill/` 前缀的路径，缺失文件跳过）：
    `skills/bootstrap/SKILL.md`、`knowledge/bootstrap-planning.md`、`knowledge/capabilities/app-design.md`；语料须含 `skills/app-design/40-qa/experience-quality-critique/SKILL.md`。
- **`/Users/aa/workspace/myskills/.githooks/pre-commit`（edit，仓库根）：** 在 `validate_game_creative_pipeline.py .` 一行之后加
  `python3 claude/meta-skill/scripts/orchestrator/validate_app_experience_pipeline.py .`。游戏那行已存在（见 Spec corrections #1），不重复加。
- **`scripts/orchestrator/validate_meta_contracts.py`（edit，追加）：** 新函数
  `validate_experience_gate_contract(errors)`，仿 `validate_execution_repair_loop_contract`；`main()` 注册列表末尾加一行。钉住：
  - bootstrap 语料（`_bootstrap_text()`）：`Experience quality gate (products with UI)`、
    `skills/app-design/40-qa/experience-quality-critique/SKILL.md`、`experience-quality-critique-design.json`、
    `experience-quality-critique-runtime.json`、`must_fix_before_implementation`、`must_fix_before_release`、
    `docs/experience-review/`、`experience_priority.mode = none`（suppress-rules 行；该文件在语料内）；
  - `knowledge/capabilities/concept-acceptance.md`：`creative-quality-critique` 与 `experience-quality-critique`；
  - `skills/app-design/PACK.md`：`experience-quality-critique`。
  只增不删：不触碰任何既有被钉字面量（含 `validate_implement_goal_contract` 的七条）。Must #9 正文不得出现
  `capability: "<新名字>"` 这种字面形式——`validate_capability_files` 会据此要求存在同名 capability 文件。

### U5 — `check_artifacts` 的 must_fix 硬失败（R-M3-07）

**文件（edit）：** `scripts/orchestrator/check_artifacts.py`。
- 新常量 `MUST_FIX_GATE_FIELDS = ("must_fix_before_implementation", "must_fix_before_release")`；
  `PRODUCTION_GAP_FIELDS` 末尾追加这两项（带一行注释：体验/创意评审的阶段门，非空即未通过）。
- `_production_gap_error`：取值处改为——`value = data.get(field)`；若 `field in MUST_FIX_GATE_FIELDS`、顶层为空且
  `isinstance(data.get("gates"), dict)`，则 `value = data["gates"].get(field)`。硬失败集合字面量追加这两个字段名。
  返回 dict 的 `field` 仍为字段名本身，`reason` 沿用既有那句。其余字段的行为一字不改。
- 后果（有意）：游戏 `creative-quality-critique.json` 的 `gates.must_fix_before_release` 非空也判未通过——这正是 Must #8
  "`must_fix_*` findings route to the owning pack's repair loop" 一直缺的确定性一半，且规格 R-M3-07 点名了这个字段。
  游戏 skill 的内容与 schema 不改。`must_fix_before_art_gen` / `must_fix_before_frontend` 不在规格内，本轮不纳入。
- `reconcile_bootstrap_workflow.GAP_FIELDS` 不改（规格未要求）。

### U6 — 规划法 Must #9、抑制规则、concept-acceptance（R-M3-06/07）

- **`knowledge/bootstrap-planning.md`（edit，纯追加）：** 在 Musts 列表第 8 条之后加第 9 条（单段，与 1–8 同体例）：

  > 9. **Experience quality gate (products with UI).** …

  必须包含的内容（措辞可润色，U4 钉住的字面量不可变）：适用于 `experience_priority.mode` 为 `consumer`/`mixed` 的非游戏产品路线；
  设计产物完成后、任何界面实现节点之前，以 `stage: "design"` 运行
  `${CLAUDE_PLUGIN_ROOT}/skills/app-design/40-qa/experience-quality-critique/SKILL.md`；最后一个 UI/product-verify/visual QA
  之后以 `stage: "runtime"` 再运行；两个节点的 `exit_artifacts` 分别含
  `.allforai/app-design/qa/experience-quality-critique-design.json` / `…-runtime.json`（及同名 `.html`）与
  `docs/experience-review/design.md` / `runtime.md`；评审由 fresh-context 评审方执行，node-spec 写明只读产物与证据、不读作者
  节点的推理过程；收尾/验收节点（`concept-acceptance`、`pipeline-closure-verify`）`hard_blocked_by` runtime 评审；
  非空 `must_fix_before_implementation` / `must_fix_before_release` 即该产物不通过（`check_artifacts.py`）；
  两个评审节点各在 `unattended-run-readiness-spec.json.required_repair_loops` 声明一条回路：
  design 回路——`qa_node_ids: [<design 评审>]`，`repair_node_id` 为重跑 `repair_route.owner_skill` 所指设计子 skill 的节点，
  `closure_node_ids` 为等待它的节点（用 canonical app-design 注册表时是 `app-design-finalize`；自由规划时是首批界面实现节点）；
  runtime 回路——runtime must-fix 归入 `experience_gaps`，`repair_node_id` 为实现修复节点，修复后重跑受影响的 QA 与 runtime
  评审，`closure_node_ids` 为收尾节点；`max_attempts` 沿用 Must #2 的预算；预算耗尽按 Run Policy 处理，运行中不提问。
  末句：同一规则对游戏由第 8 条表达；两者都由 `validate_bootstrap.py` 的 `validate_experience_gate_flow` 强制。
  第 8 条原文不改。
- **摆位约束（写进 Must #9 与 `capabilities/app-design.md`，源自 Spec corrections #6）：** 用 canonical 注册表时，
  design 评审节点与设计修复节点取 `capability: app-design`（行内代码、不带引号的 `capability:` 形式），位于各 spec 节点之后、
  `app-design-finalize` 之前——`validate_app_design_flow` 本来就要求 finalize `hard_blocked_by` 全部 app-design 节点，
  于是 finalize 天然成为 design 回路的 closure 节点，且满足 `repair_loop_declaration_findings` 对
  "closure 直接 `hard_blocked_by` QA 与 repair"的要求；实现节点经 `concept-freeze` 传递依赖 design 评审。
  runtime 评审节点不得取 `app-design`，建议取 `quality-checks`（U3 不看 capability）。节点 id 不得含 `product-review` /
  `cross-exam`。
- **`knowledge/suppress-rules.md`（edit）：** 表末加一行
  `| \`experience_priority.mode = none\` | experience quality gate (Must #9) nodes | no end-user UI to judge; the summary states the exemption |`。
  （`admin` 不在 Must #9 触发范围内，属"不适用"而非"抑制"，不写进表。）
- **`knowledge/capabilities/concept-acceptance.md`（edit）：** `## Prerequisite` 段末加一段：本节点 `hard_blocked_by`
  创意/体验评审——游戏为实现后的那次 `creative-quality-critique`（Must #8），带界面的应用为 runtime 阶段的
  `experience-quality-critique`（Must #9）；评审的 `must_fix_*` 未清空时评审节点未完成，本门不启动。并重申分工：评审判好坏并路由修复，
  本门仍只做覆盖核对、不打分（ADR-0008 不变）。
- **`knowledge/capabilities/game-design.md`：不改**（已写明 critique 在 concept-acceptance 之前）。

### U7 — 测试（R-M3-11）

风格统一：`from ..module_isolation import load`；模块顶部绑定被测函数；`tmp_path` 夹具；复用各文件现有的
`_write` / `_base_node` / `_bootstrap_dir`；无 host 参数化。

- **`tests/unit/test_validate_bootstrap.py`（edit，文件末尾追加一个分节 + 顶部绑定一行）：**
  绑定 `validate_experience_gate_flow`、`experience_gate_flow_findings`。本分节私有助手
  `_experience_gate_project(tmp_path, *, game=False, mode="consumer", route="new-product", nodes=None, loops=None)`：
  写 profile（`task_route`、`experience_priority: {"mode": mode, "reason": "fixture"}`、`is_game_project`）、`workflow.json`、
  各节点最小 node-spec、readiness spec；默认产出**通过**的图。界面实现节点复用 M1 在本文件里为
  `validate_experience_design_coverage` 写的实现节点夹具（保证两模块对"界面实现节点"的认定同源）。
  用例（断言取 `experience_gate_flow_findings` 的 `code`）：
  1. `test_experience_gate_app_passes`；2. `test_experience_gate_game_passes`；
  3. `…_rejects_app_without_critique_node`（`missing_experience_gate`，且缺单个阶段时点名该阶段）；
  4. `…_rejects_game_without_creative_critique`（同码）；
  5. `…_rejects_implementation_not_blocked_by_design_critique`；
  6. `…_rejects_closure_not_blocked_by_runtime_critique`（应用）与 7. 游戏版（只有实现前那次评审）；
  8. `…_rejects_critique_outside_repair_loop`（`experience_gate_without_repair_loop`；含 readiness spec 缺失的变体）；
  9. `…_not_triggered_when_mode_none`；10. `…_not_triggered_on_local_change`；
  11. `…_not_triggered_without_experience_priority`（旧项目）；
  12. `…_reader_node_is_not_a_gate`（只在正文提到 skill、不产出评审产物的节点不算）；
  13. `test_structural_gate_blockers_include_experience_gate`（经 `structural_gate_blockers(project_root)` 拿到同一 code）；
  14. `…_malformed_inputs_return_empty`（不可解析 profile / `nodes` 非 list 不抛异常）。
  既有 `test_app_design_flow_*` 等用例的 profile 不含 `experience_priority`，不触发，无需改。
- **`tests/unit/test_validate_app_experience_pipeline.py`（create）：** 镜像 `test_validate_game_creative_pipeline.py`：
  `_minimal_repo(tmp_path)` 写最小 bootstrap-planning、PACK、critique SKILL（逐行列出必备术语）；三例——
  `…_accepts_minimal_graph`、`…_rejects_unlisted_child`（断言 `missing canonical child path`）、
  `…_rejects_missing_term`（从 critique 夹具删去 `audience_leak`，断言 `missing required term audience_leak`）。
- **`tests/unit/test_check_artifacts.py`（edit，追加；选它而非 `_measurement` 是因为硬失败用例都在这里
  （`test_quality_gaps_are_not_complete` 一带），且避开 M4 要改的 `_measurement` 文件）：**
  `test_must_fix_before_implementation_in_gates_is_not_complete`、`test_must_fix_before_release_in_gates_is_not_complete`、
  `test_top_level_must_fix_is_not_complete`、`test_empty_must_fix_gates_are_complete`
  （`gates` 三项皆 `[]` 且 `recommended_iterations` 非空时仍通过——建议不阻断）。断言 `status_error["field"]`。
- **`tests/unit/test_validate_unattended_readiness.py`（edit，追加一例）：**
  `test_unattended_readiness_accepts_experience_gate_repair_loops`——最小 UI 产品图带 design/runtime 两条回路，
  `status == "ready"` 且无 `*repair_loop*` 阻断；证明 Must #9 描述的回路形状被既有就绪门接受。复用 `_repair_loop`、`_write`。
  `validate_unattended_readiness.py` 本身**不改**。

### 验收命令（在规格"验收"一节基础上补全；均在 `/Users/aa/workspace/myskills` 根目录执行）

```bash
python3 -m pytest -q claude/meta-skill/tests/unit/test_validate_bootstrap.py \
  claude/meta-skill/tests/unit/test_validate_app_experience_pipeline.py \
  claude/meta-skill/tests/unit/test_validate_game_creative_pipeline.py \
  claude/meta-skill/tests/unit/test_check_artifacts.py \
  claude/meta-skill/tests/unit/test_check_artifacts_measurement.py \
  claude/meta-skill/tests/unit/test_validate_unattended_readiness.py \
  claude/meta-skill/tests/unit/test_validate_skills.py
python3 claude/meta-skill/scripts/orchestrator/validate_app_experience_pipeline.py .
python3 claude/meta-skill/scripts/orchestrator/validate_game_creative_pipeline.py .
python3 claude/meta-skill/scripts/orchestrator/validate_skills.py claude/meta-skill/skills
python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py
python3 -m py_compile claude/meta-skill/scripts/orchestrator/*.py
grep -n "validate_app_experience_pipeline.py" .githooks/pre-commit   # 期望 1 行
```

不得以目录形式运行 `pytest codex/meta-skill` 或 `pytest pi/meta-skill`。全量套件的 4 个既有失败不属本模块，不触碰。

### Assumptions（内部选择，不改变模块边界与公开接口）

1. 阶段门放在 `gates{}` 内（与游戏侧同形），`check_artifacts` 同时读顶层与 `gates.<field>`；而非把应用报告改成顶层字段。
2. 评审节点按 `exit_artifacts` 路径子串识别，应用阶段按文件名后缀、游戏"实现后"按图位置识别；不按节点 id、不按 capability。
   这比规格"引用…的节点"更严，避免把读报告的节点误当成门。
3. `missing_experience_gate` 对应用按阶段各报一条（design、runtime 都必需）；对游戏只要求至少一个评审节点，
   "实现后那次"的缺失由 `closure_not_blocked_by_experience_gate` 暴露（游戏在 implement-only 目标下按 suppress-rules
   不注入设计期节点，故不强求设计期评审）。
4. 触发条件第 2 条对缺失/非法 `experience_priority` 不触发；这使旧项目在 `/run` 边界不被追溯拦截，缺失本身归 M1 的码。
5. findings/rendered 双函数；`experience_gate_flow_findings` 进 `__all__`，但注册表接口名仍只有
   `api:validateExperienceGateFlow`（它涵盖"校验函数与四个码"）。
6. design 评审与设计修复节点取 `capability: app-design` 并置于 `app-design-finalize` 之前；runtime 评审节点建议
   `quality-checks`。不新增 capability 文件。
7. must_fix 的 check_artifacts 用例放 `test_check_artifacts.py`（规格允许"或同类文件"）。
8. `docs/experience-review/<stage>.md` 覆盖写、只留最新；历史靠项目自身的 git。M6 读 `runtime.md`。
9. `lenses.*` 用 `有|缺|未查`（与 `/product-review` 报告行同词），不设数值分；`confidence` 保留。
   高置信阈值定为 `>= 0.8`（游戏侧只写"high-confidence"未给数；此阈值只写在应用 skill 内）。
10. 界面实现节点的识别完全委托给 M1 的函数；若 M1 未抽函数，M3 先做零行为变化的抽取。

### File touch list

| Path（相对仓库根） | create/edit | Requirement |
|---|---|---|
| `claude/meta-skill/skills/app-design/40-qa/experience-quality-critique/SKILL.md` | create | R-M3-01, R-M3-02, R-M3-03, R-M3-04, R-M3-10 |
| `claude/meta-skill/skills/app-design/PACK.md` | edit | R-M3-05 |
| `claude/meta-skill/knowledge/capabilities/app-design.md` | edit | R-M3-05, R-M3-06 |
| `claude/meta-skill/knowledge/bootstrap-planning.md` | edit（追加 Must #9） | R-M3-06, R-M3-07, R-M3-04, R-M3-10 |
| `claude/meta-skill/knowledge/suppress-rules.md` | edit（加一行） | R-M3-06 |
| `claude/meta-skill/knowledge/capabilities/concept-acceptance.md` | edit（加一段） | R-M3-06 |
| `claude/meta-skill/scripts/orchestrator/check_artifacts.py` | edit | R-M3-07 |
| `claude/meta-skill/scripts/orchestrator/validate_bootstrap.py` | edit（常量 + 2 函数 + 3 处注册） | R-M3-08 |
| `claude/meta-skill/scripts/orchestrator/validate_app_experience_pipeline.py` | create | R-M3-09 |
| `claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py` | edit（1 函数 + 1 注册行） | R-M3-09 |
| `.githooks/pre-commit` | edit（加一行） | R-M3-09 |
| `claude/meta-skill/tests/unit/test_validate_bootstrap.py` | edit（追加分节） | R-M3-11, R-M3-08 |
| `claude/meta-skill/tests/unit/test_validate_app_experience_pipeline.py` | create | R-M3-11, R-M3-09 |
| `claude/meta-skill/tests/unit/test_check_artifacts.py` | edit（追加 4 例） | R-M3-11, R-M3-07 |
| `claude/meta-skill/tests/unit/test_validate_unattended_readiness.py` | edit（追加 1 例） | R-M3-11, R-M3-07 |

不触碰：`skills/game-creative/**`、`knowledge/capabilities/game-design.md`、`validate_game_creative_pipeline.py`、
`validate_unattended_readiness.py`、`reconcile_bootstrap_workflow.py`、`skills/bootstrap/SKILL.md`、codex/pi 的任何手工孪生
（归 M5/M6）、4 个既有失败测试。
