# Requirements Document

## Introduction

`product-audit-skill` 经过整体重新设计后，技能层（`skills/`）已更新，但命令层（`commands/`）和插件配置仍停留在旧版。具体问题：

1. `feature-audit`、`feature-prune`、`demo-forge` 三个命令的描述、模式路由、Step 引用、报告模板、铁律均与新技能文件不一致
2. 新增的 `product-map` 技能缺少对应的技能文件和命令文件
3. 命令名称不贴近新功能语义：`feature-audit` 应改为 `feature-gap`（功能查漏），`demo-forge` 应改为 `seed-forge`（种子数据）

本次重构范围：新建 `product-map` 技能文件和命令，重命名 `feature-audit` → `feature-gap`、`demo-forge` → `seed-forge`，更新所有命令文件内容，并同步更新 `SKILL.md`、`README.md`、`plugin.json`。

## Alignment with Product Vision

product-audit-skill 的工作链路是 `product-map` → `feature-gap` → `feature-prune` → `seed-forge`。命令文件是用户进入每个技能的唯一入口，名称和行为必须准确反映这一分层关系和每个技能的新设计。

---

## Requirements

### Requirement 1：新建 product-map 技能文件和命令

**User Story:** As a PM, I want a `product-map` skill and `/product-map` command so that I can build a structured product map that all other skills use as their foundation.

#### Acceptance Criteria

1. WHEN `skills/product-map.md` is created THEN it SHALL define the 6-step workflow: 项目画像 → 用户角色识别 → 核心任务提取 → 界面与按钮梳理 → 冲突&冗余检测 → 约束识别 → 输出报告
2. WHEN the user runs `/product-map` THEN the system SHALL execute the full workflow (all 6 steps)
3. WHEN the user runs `/product-map quick` THEN the system SHALL skip Step 4（冲突&冗余检测）and Step 5（约束识别）
4. WHEN the user runs `/product-map refresh` THEN the system SHALL ignore any existing `.allforai/product-map/` cache and re-run from Step 0
5. WHEN the user runs `/product-map scope <模块名>` THEN the system SHALL limit analysis to tasks and screens belonging to the specified module
6. IF `.allforai/product-map/product-map-decisions.json` exists THEN the system SHALL automatically load prior decisions to skip re-confirmation of already-confirmed items
7. WHEN any step completes THEN the system SHALL write results to `.allforai/product-map/` and wait for user confirmation before proceeding to the next step
8. WHEN the full workflow completes THEN the system SHALL output a conversation summary including: role count, task count, screen count, high-frequency action list, and detected conflicts count

### Requirement 2：重命名 feature-audit → feature-gap 并重构命令内容

**User Story:** As a PM, I want a `/feature-gap` command that detects gaps against the product map so that I get a frequency-prioritized task list of what's missing or broken.

#### Acceptance Criteria

1. WHEN this requirement is implemented THEN `commands/feature-audit.md` SHALL be renamed to `commands/feature-gap.md`
2. WHEN the user runs `/feature-gap` THEN the system SHALL run full gap detection: task completeness (Step 1) + screen & button completeness (Step 2) + user journey validation (Step 3)
3. WHEN the user runs `/feature-gap quick` THEN the system SHALL run only Steps 1 and 2, skipping user journey validation
4. WHEN the user runs `/feature-gap journey` THEN the system SHALL run only Step 3 (user journey validation)
5. WHEN the user runs `/feature-gap role <角色名>` THEN the system SHALL limit analysis to tasks and screens belonging to the specified role
6. IF `.allforai/product-map/product-map.json` does not exist THEN the system SHALL halt and prompt the user to run `/product-map` first
7. IF `.feature-audit/audit-decisions.json` or `.allforai/feature-gap/gap-decisions.json` exists THEN the system SHALL load prior decisions automatically
8. WHEN gap tasks are generated THEN the system SHALL sort them by frequency priority (高频 task gaps first)
9. WHEN execution completes THEN the summary SHALL include: gap task list sorted by priority, per-role journey scores (X/4), and flag counts for CRUD_INCOMPLETE / NO_SCREEN / HIGH_FREQ_BURIED / NO_PRIMARY / HIGH_RISK_NO_CONFIRM / ORPHAN_SCREEN / ENTRY_BROKEN
10. WHEN writing output THEN the system SHALL use the new file names under `.allforai/feature-gap/`: `task-gaps.json`, `screen-gaps.json`, `journey-gaps.json`, `gap-tasks.json`, `gap-report.md`, `gap-decisions.json`

### Requirement 3：重构 feature-prune 命令内容

**User Story:** As a PM, I want `/feature-prune` to use frequency data from the product map so that pruning decisions are evidence-based rather than subjective.

#### Acceptance Criteria

1. WHEN the user runs `/feature-prune` THEN the system SHALL run full prune: frequency tier (Step 1) → scenario alignment (Step 2) → competitive benchmarking (Step 3) → user decision session (Step 4) → generate task list (Step 5)
2. WHEN the user runs `/feature-prune quick` THEN the system SHALL skip Step 3 (competitive benchmarking)
3. WHEN the user runs `/feature-prune scope <模块名>` THEN the system SHALL limit analysis to the specified module
4. IF `.allforai/product-map/product-map.json` does not exist THEN the system SHALL halt and prompt the user to run `/product-map` first
5. WHEN reading frequency data THEN the system SHALL load it directly from `.allforai/product-map/task-inventory.json` without re-collecting
6. WHEN a task has `frequency=高` THEN the system SHALL automatically exclude it from prune candidates unless the user explicitly initiates its evaluation
7. IF `.allforai/feature-prune/prune-decisions.json` exists THEN the system SHALL load prior decisions automatically
8. WHEN execution completes THEN the summary SHALL include: CORE/DEFER/CUT counts, full CUT list with evidence, full DEFER list with timing recommendations
9. WHEN writing output THEN the system SHALL use the new file names under `.allforai/feature-prune/`: `frequency-tier.json`, `scenario-alignment.json`, `competitive-ref.json`, `prune-decisions.json`, `prune-tasks.json`, `prune-report.md`

### Requirement 4：重命名 demo-forge → seed-forge 并重构命令内容

**User Story:** As a developer, I want a `/seed-forge` command that generates seed data based on the product map so that demo data has realistic role distribution, frequency-proportional volumes, coherent scenario chains, and business-rule compliance.

#### Acceptance Criteria

1. WHEN this requirement is implemented THEN `commands/demo-forge.md` SHALL be renamed to `commands/seed-forge.md`
2. WHEN the user runs `/seed-forge` THEN the system SHALL run the full flow: model mapping (Step 0) → seed plan (Step 1) → style profile (Step 2) → asset collection (Step 3) → data population (Step 4)
3. WHEN the user runs `/seed-forge plan` THEN the system SHALL run Steps 0–2 only (no population required, app does not need to be running)
4. WHEN the user runs `/seed-forge fill` THEN the system SHALL load the existing seed plan and proceed to Steps 3–4
5. WHEN the user runs `/seed-forge clean` THEN the system SHALL delete seeded records by querying the database directly using IDs from `forge-data.json`
6. IF `.allforai/product-map/product-map.json` does not exist THEN the system SHALL halt and prompt the user to run `/product-map` first
7. WHEN designing data volumes THEN the system SHALL read `frequency` from `.allforai/product-map/task-inventory.json` and apply 80/20 distribution (high-frequency tasks receive ≥70% of total record count)
8. WHEN generating record relationships THEN the system SHALL follow scenario chains from `.allforai/product-map/screen-map.json` rather than creating random associations
9. WHEN generating record field values THEN the system SHALL enforce all rules from `.allforai/product-map/constraints.json`
10. WHEN execution completes THEN the summary SHALL show: user accounts created per role, record counts per task grouped by frequency tier, scenario chains populated, and any constraint violations caught
11. WHEN writing output THEN the system SHALL use the new file names under `.allforai/seed-forge/`: `model-mapping.json`, `seed-plan.json`, `style-profile.json`, `assets-manifest.json`, `forge-log.json`, `forge-data.json`, `api-gaps.json`

### Requirement 5：同步更新插件配置和文档

**User Story:** As a plugin user, I want `SKILL.md`, `README.md`, and `plugin.json` to reflect the new skill names and commands so that installation and discovery work correctly.

#### Acceptance Criteria

1. WHEN `plugin.json` is updated THEN it SHALL register `product-map`, `feature-gap`, `feature-prune`, `seed-forge` as the four active skills and commands
2. WHEN `SKILL.md` is updated THEN it SHALL list the new skill names, new command invocations, and updated descriptions
3. WHEN `README.md` is updated THEN it SHALL replace all references to old command names (`/feature-audit`, `/demo-forge`) with new names (`/feature-gap`, `/seed-forge`)

## Non-Functional Requirements

### Performance
- 命令文件加载的详细文档（`docs/`）使用按需 Read，避免一次性加载所有文档导致 context 膨胀

### Security
- `seed-forge clean` 模式直接操作数据库，必须在命令文件中要求用户二次确认后才执行

### Reliability
- 所有命令文件必须在 Step 开始前检查前置文件是否存在，缺失时给出明确提示，不得静默失败

### Usability
- 每个命令文件的模式路由（mode routing）必须在文件开头清晰列出，用户一眼能看到支持哪些参数
