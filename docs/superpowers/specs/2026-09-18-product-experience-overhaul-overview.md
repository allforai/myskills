# 产品体验改造（product-experience-overhaul）— 总览

状态：Phase 0 完成，注册表与授权信封已冻结；Phase 1 自主执行中。
运行目录：`docs/superpowers/runs/2026-09-18-product-experience-overhaul/`。分支：`product-experience-overhaul`。

## 目标

系统性改造 myskills 中与产品相关的 skill，使 meta-skill 在无人值守的 `/run` 下，
产出体验良好的应用或游戏，而不是"功能正确但设计低级"的交付。

## 触发证据（ink-scent，2026-09-14 至 09-16 的 new-product 运行）

- 工作流 13 个节点：契约、内容库、6 个 implement、若干 verify/repair；**零个体验/界面设计节点**。
- `goals = [create, implement, product-verify, quality-checks]`；`knowledge/capabilities/` 下没有 `create.md`，
  bootstrap Step 2 只加载"文件名与 goals 匹配的 capability"，因此 product-concept、app-design、
  consumer-maturity-patterns、journey-emotion-schema 无一被加载。
- 意图确认的 6 个话题没有体验维度；"recommendations … are not actions"、
  "New needs require user provenance" 使模型只能记录用户原话。"碎片化学习"被直译为
  "2/5/10 分钟选择器 + 题型清单"。
- `experience_priority` 被 7 个知识文件读取，bootstrap 从不设置。
- 规格未定义最终用户如何获得服务地址与访问凭证；实现节点自行发明了
  `mobile/src/ServiceSettings.tsx`（最终用户界面里的"服务地址 / 访问凭证"输入框），验证节点只对契约核对，放行。
- `bootstrap-planning.md` 的 Must #8（创意质量门）限定游戏项目；应用无对应质量门，也无应用设计覆盖审计。

## Environment capabilities（Phase -1，2026-09-18 探测）

| 能力 | 判定 | 说明 |
|---|---|---|
| 必备 skill：superpowers:brainstorming / writing-plans / executing-plans | available | 已在 Skill 注册表中 |
| Python 3.14.7 + pytest、Node v26.7.0 | available | 目标仓库的全部自动验收手段 |
| codex CLI、pi CLI | available（已安装） | 仅证明可执行文件存在；真实宿主对话行为未探测 |
| 显示/UI、模拟器、真机 | 不适用 | 目标是 skill 仓库（Markdown + Python），无运行时界面 |
| 真实宿主下的 bootstrap 对话质量 | absent | 无法在本环境自动证明"真实 LLM 宿主按新协议产出好的体验方向"；属 reality gate 候选 |
| 远端 `git@github.com:allforai/myskills.git` | 未探测 | 是否允许 push 由授权信封决定 |

机器：18 核 / 128 GB。目标仓库不是会话 cwd（会话在 `ink-scent`），**worktree 隔离无效**，
冲突组对主树串行写入。

### 测试基线（改造前，干净 main @ 6a59fe44）

- `claude/meta-skill`: `python3 -m pytest tests/unit -q` → 1198 passed, **4 failed**, 342 s。既有失败：
  - `test_decision_gate.py::test_a_resolved_choice_restores_readiness_only_with_fresh_evidence[claude|codex]`
  - `test_evidence_freshness.py::test_fresh_contract_allows_execution_but_cannot_claim_completion[claude|codex]`
- `claude/superstorm/scripts`: `python3 -m pytest -q` → 255 passed, 7 s。

既有失败不属于本次范围，也不得被计为本次回归；全量套件约 6 分钟，任务级验收使用定向测试文件。

## 已批准的决定

| # | 决定 | 用户原话 / 选择 | 时间 |
|---|---|---|---|
| D1 | 设计授权：**先提案，可委托**。bootstrap 交互阶段模型必须产出 2–3 个有主张的体验方向并给推荐；用户选一个，或明说"你定"（记为委托动作）。委托后由模型选定，独立评审门把关，收尾披露。`/run` 全程不问人。 | 选择"先提案，可委托 (Recommended)" | 2026-09-18 |
| D2 | 范围：M1–M5 加上事后评审对齐（M6）。 | 选择"把事后评审也纳入" | 2026-09-18 |
| D4 | 六份模块规格与总览批准，冻结注册表（49 条需求、16 个接口）。 | 选择"批准，冻结注册表" | 2026-09-18 |
| D5 | 模型策略 B：执行器用 opus；设计、评审、规划、监督继承会话模型（fable）。回落到会话模型始终被授权。 | 选择"B 成本优先" | 2026-09-18 |
| D6 | Git：在分支 `product-experience-overhaul` 上提交，不推送，不合并 main。 | 选择"开分支提交，不推送" | 2026-09-18 |
| D3 | 总目标含"无人值守"与"应用或游戏"两项约束。 | "让这个skill可以无人值守作为良好体验的app或者是游戏" | 2026-09-18 |

## 模块

| 模块 | 单一关注点 | 主要落点 | 依赖 |
|---|---|---|---|
| **M1 design-routing** 设计环节必达 | new-product/create 路线在有界面的产品上必然加载概念、设计与成熟度知识，并规划体验设计节点；bootstrap 设置 `experience_priority`；应用设计覆盖审计与确定性校验 | `skills/bootstrap/SKILL.md`、`knowledge/bootstrap-planning.md`、`knowledge/bootstrap-audits.md`、新校验脚本 | — |
| **M2 experience-intent** 体验意图与设计授权 | 意图确认协议新增 `experience` 话题、模型提案来源、委托动作；来源纪律不变 | `knowledge/product-intent-confirmation.md`、`scripts/orchestrator/product_intent.py` 及测试 | M1 |
| **M3 experience-gate** 体验质量门 | 应用版质量评审：实现前判设计产物，实现后判运行中的产品，均走无人值守修复回路；与游戏 Must #8 共用判定格式 | 新增 `skills/app-design/40-qa/experience-quality-critique`、`bootstrap-planning.md` Must #9、校验脚本 | M1、M2 |
| **M4 spec-gap-discipline** 规格留白纪律 | 规格未覆盖的用户可见决定记为 `contract_gap`，不得自行发明界面；部署方配置不得进入最终用户界面；设置项标注受众 | `knowledge/defensive-patterns.md`、`knowledge/node-spec-template.md`、设置规格子 skill | M1 |
| **M5 regression-parity** 回归与多端一致 | 消费级 new-product 夹具、思维测试场景、codex/pi 同步、版本与发布 | `tests/fixtures`、`tests/brain-test`、`codex/`、`pi/` | M1–M4、M6 |
| **M6 review-alignment** 事后评审对齐 | 运行内质量门与 `/product-review` 判据同源；运行内结论在 `docs/` 下留痕供事后采信；`/cross-exam` 旅程候选增加体验基线来源；两边增加"部署方配置暴露给最终用户"镜头 | `claude/superstorm/skills/product-review/SKILL.md`、`skills/cross-exam/SKILL.md` | M2、M3 |

## Roadmap（本轮不做）

- 游戏专项的深入审计（场景模板、各游戏 pack 的质量判据）。本轮已纳入的游戏侧改动：
  M2 的体验方向话题对游戏同样适用；M3 的确定性校验强制创意评审节点存在并阻断收尾。
  游戏创意评审 skill 自身的内容与 schema 本轮不改。
- 修复上述 4 个既有失败测试。
- 用改造后的 meta-skill 重跑 ink-scent 并返工其首页循环与设置页（属产品仓库的工作，不属本仓库）。

## 探查补充的事实（2026-09-18，三个只读探查）

- **游戏的 Must #8 同样未被强制。** `validate_game_creative_pipeline.py` 只查插件源码措辞，且无任何调用方；
  生成的项目里没有检查要求创意评审节点存在或阻断收尾。因此 M3 的确定性校验同时覆盖应用与游戏；
  原 Roadmap 中"游戏路线独立审计"缩小为"游戏意图确认的体验话题之外的其它游戏专项"。
- **app-design 现行文本无法无人值守运行**（`human_gate: true` ↔ `pending_human_gate`）。归 M1。
- **`experience_priority` 无生产者、无 schema。** 归 M1。
- **`product_intent.py` 全仓库唯一**，codex/pi 走符号链接；意图条目按整体相等核验，
  提案必须另存数组。归 M2。
- **手工孪生文件**（codex/pi 的 bootstrap 适配器、orchestrator 模板、cross-exam/product-review 的 codex 版）
  需同提交双写。归 M5、M6。

## 模块规格

| 模块 | 规格 | 需求数 |
|---|---|---|
| M1 | `2026-09-18-design-routing-design.md` | 9 |
| M2 | `2026-09-18-experience-intent-design.md` | 10 |
| M3 | `2026-09-18-experience-gate-design.md` | 11 |
| M4 | `2026-09-18-spec-gap-discipline-design.md` | 7 |
| M6 | `2026-09-18-review-alignment-design.md` | 5 |
| M5 | `2026-09-18-regression-parity-design.md` | 7 |

执行次序：M1 → (M2 ∥ M4) → M3 → M6 → M5。

## 粒度审计

| 模块 | 估计任务数 | 判定 | 动作 |
|---|---|---|---|
| M1 design-routing | 10 | 合适；单一关注点（路由与覆盖） | 保持 |
| M2 experience-intent | 13 | 合适；全部围绕一个脚本与一份协议，接口都在同侧 | 保持 |
| M3 experience-gate | 13 | 合适；"设计评审 + 运行评审 + 校验"是同一个门的三面，拆开会把 `data:experienceCritiqueReport` 切成两半 | 保持 |
| M4 spec-gap-discipline | 8 | 偏小，但与 M3 只共享两个数据接口，关注点不同（纪律 vs 评审） | 保持，不并入 M3 |
| M6 review-alignment | 6 | 偏小；落在另一个插件（superstorm），验收命令独立 | 保持 |
| M5 regression-parity | 12 | 合适；是收口模块，天然依赖全部 | 保持 |

冲突面（无 worktree 隔离，主树串行）：`scripts/orchestrator/validate_bootstrap.py`、
`validate_meta_contracts.py`、`knowledge/bootstrap-planning.md`、`tests/unit/test_validate_bootstrap.py`
被 M1/M3/M4 共同触碰；由 DAG 的 `isolate_groups` 串行化。

<!-- superstorm-registry:start -->
```json
{ "requirements": [
    "R-M1-01","R-M1-02","R-M1-03","R-M1-04","R-M1-05","R-M1-06","R-M1-07","R-M1-08","R-M1-09",
    "R-M2-01","R-M2-02","R-M2-03","R-M2-04","R-M2-05","R-M2-06","R-M2-07","R-M2-08","R-M2-09","R-M2-10",
    "R-M3-01","R-M3-02","R-M3-03","R-M3-04","R-M3-05","R-M3-06","R-M3-07","R-M3-08","R-M3-09","R-M3-10","R-M3-11",
    "R-M4-01","R-M4-02","R-M4-03","R-M4-04","R-M4-05","R-M4-06","R-M4-07",
    "R-M5-01","R-M5-02","R-M5-03","R-M5-04","R-M5-05","R-M5-06","R-M5-07",
    "R-M6-01","R-M6-02","R-M6-03","R-M6-04","R-M6-05" ],
  "interfaces": [
    "data:experiencePriority",
    "data:experienceDesignArtifacts",
    "api:validateExperienceDesignCoverage",
    "data:experienceProposals",
    "api:productIntentPropose",
    "api:productIntentSelect",
    "api:productIntentDelegate",
    "data:experienceDirectionIntent",
    "data:delegationDisclosure",
    "data:experienceCritiqueReport",
    "data:experienceReviewDoc",
    "data:experienceLensVocabulary",
    "api:validateExperienceGateFlow",
    "data:settingsAudience",
    "data:unspecifiedDecisionGap",
    "data:regressionFixtures" ],
  "models": { "executor": "opus", "recommended": "A",
              "why": "推荐 A：任务跨文件且需维护严格等式不变量；用户在知情后选择 B",
              "confirmed_by_user": "B 成本优先", "confirmed_at": "2026-09-18T15:31:22+09:00" } }
```
<!-- superstorm-registry:end -->

注册表已冻结（2026-09-18T15:31+09:00）。Phase 1 中 worker 不得扩充接口词表。
