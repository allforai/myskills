# Implementation Plan

## Task Overview

按组件顺序逐步重构 `product-audit-skill`：先建立基础技能文件，再写命令文件，最后更新配置。每个任务独立可验证，前面任务不阻塞后续任务的开始，但命令文件依赖对应技能文件的完成。

## Steering Document Compliance

- 复用现有命令文件（`commands/feature-audit.md`）的结构模式：YAML frontmatter → 模式路由 → 前置检查 → 执行流程 → 详细文档引用 → Step 执行要求 → 报告模板 → 铁律
- `${CLAUDE_PLUGIN_ROOT}` 变量用于所有文档引用路径
- 新技能文件沿用现有技能文件（`skills/demo-forge.md`）的结构：YAML frontmatter → 目标 → 定位 → 快速开始 → 工作流 → 输出文件结构 → 铁律

## Atomic Task Requirements

- **File Scope**: 每个任务最多涉及 1-2 个文件
- **Time Boxing**: 15-30 分钟内完成
- **Single Purpose**: 每个任务一个明确的可验证产出
- **Specific Files**: 每个任务明确指定文件路径
- **Agent-Friendly**: 清晰的输入输出，无需跨任务上下文切换

## Task Format Guidelines

- 使用 checkbox 格式：`- [ ] 任务编号. 任务描述`
- 每个任务必须指定具体的文件路径
- 使用 `_Requirements: X.Y_` 引用需求条目
- 使用 `_Leverage: path/to/file_` 标注可复用的现有文件
- 仅包含文件编写类任务，不包含部署、用户测试等操作

## Tasks

- [ ] 1. 新建 `skills/product-map.md`
  - File: `skills/product-map.md`（新建）
  - 参考 `docs/plans/2026-02-24-product-map-design.md` 的完整设计内容
  - 结构沿用 `skills/demo-forge.md`：YAML frontmatter（name/description/version: "2.0.0"） → 目标 → 定位 → 快速开始 → 工作流（Step 0–6）→ 输出文件结构 → 铁律
  - description 触发词：涵盖"产品地图"/"功能点梳理"/"用户角色识别"/"界面梳理"/"product map"等关键词
  - 工作流包含：Step 0（项目画像）→ Step 1（角色识别）→ Step 2（任务提取）→ Step 3（界面梳理）→ Step 4（冲突检测）→ Step 5（约束识别）→ Step 6（输出报告）
  - 输出文件：`.allforai/product-map/` 下的 role-profiles.json、task-inventory.json、screen-map.json、conflict-report.json、constraints.json、product-map.json、product-map-report.md、product-map-decisions.json
  - 铁律：产品语言输出、不改代码只分析、用户是权威、每步确认后才继续、product-map 是其他技能的唯一数据源
  - _Requirements: 1.1_
  - _Leverage: skills/demo-forge.md（结构参考）, docs/plans/2026-02-24-product-map-design.md（内容来源）_

- [ ] 2. 新建 `commands/product-map.md`
  - File: `commands/product-map.md`（新建）
  - 结构完全沿用 `commands/feature-audit.md` 的模式
  - YAML frontmatter: description（一句话 + 模式列表）、argument-hint、allowed-tools（不含 WebSearch/WebFetch）
  - 模式路由：`full`（默认，Step 0–6）/ `quick`（跳过 Step 4 冲突检测和 Step 5 约束识别）/ `refresh`（忽略缓存，从 Step 0 重跑）/ `scope <模块名>`（限定模块范围）
  - 前置检查：检测 `.allforai/product-map/product-map-decisions.json`，存在则自动加载历史决策
  - 详细文档引用：`${CLAUDE_PLUGIN_ROOT}/skills/product-map.md`
  - Step 执行要求：每步完成写入 `.allforai/product-map/` 对应文件，向用户展示摘要，等待确认后继续
  - 报告模板：角色数、任务数、界面数、高频操作列表、冲突数
  - 铁律引用：`${CLAUDE_PLUGIN_ROOT}/skills/product-map.md` 的铁律章节
  - _Requirements: 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8_
  - _Leverage: commands/feature-audit.md（结构参考）_

- [ ] 3. 新建 `skills/feature-gap.md`（重命名自 feature-audit.md）
  - File: `skills/feature-gap.md`（新建，`skills/feature-audit.md` 已有更新内容，直接以其为基础）
  - 读取现有 `skills/feature-audit.md`（已重写为功能查漏版本）
  - 更新 YAML frontmatter：name 改为 `feature-gap`，version 保持 "2.0.0"，description 触发词更新为 "feature-gap"/"功能查漏"/"缺口检测" 等
  - 更新文件内所有 `/feature-audit` 命令引用为 `/feature-gap`
  - 更新所有输出路径引用 `.feature-audit/` → `.allforai/feature-gap/`（输出文件名：task-gaps.json、screen-gaps.json、journey-gaps.json、gap-tasks.json、gap-report.md、gap-decisions.json）
  - 旧文件 `skills/feature-audit.md` 保留不删除（由后续任务统一清理）
  - _Requirements: 2.1, 2.10_
  - _Leverage: skills/feature-audit.md（内容来源）_

- [ ] 4. 新建 `commands/feature-gap.md`（重命名自 feature-audit.md）
  - File: `commands/feature-gap.md`（新建）
  - YAML frontmatter: description（功能查漏：基于 product-map 检测任务/界面/旅程缺口。模式: full / quick / journey / role）、allowed-tools（不含 WebSearch/WebFetch）
  - 模式路由：`full`（默认，Step 1+2+3）/ `quick`（Step 1+2，跳过旅程验证）/ `journey`（仅 Step 3）/ `role <角色名>`（限定角色范围）
  - 前置检查：
    - `.allforai/product-map/product-map.json` 不存在 → 提示"请先运行 /product-map"，终止
    - 优先加载 `.allforai/feature-gap/gap-decisions.json`；不存在则尝试 `.feature-audit/audit-decisions.json`（只读，不写回旧路径）
  - 详细文档引用：`${CLAUDE_PLUGIN_ROOT}/skills/feature-gap.md`
  - Step 执行要求：每步完成写入 `.allforai/feature-gap/` 对应文件，等待用户确认
  - 报告模板：gap 任务清单（按频次排序）、各角色旅程评分（X/4）、flag 分类统计（CRUD_INCOMPLETE / NO_SCREEN / HIGH_FREQ_BURIED / NO_PRIMARY / HIGH_RISK_NO_CONFIRM / ORPHAN_SCREEN / ENTRY_BROKEN 各自计数）
  - Breaking changes 说明：不再支持 incremental / verify 模式，输出目录变更
  - 铁律引用：`${CLAUDE_PLUGIN_ROOT}/skills/feature-gap.md`
  - _Requirements: 2.1–2.10_
  - _Leverage: commands/feature-audit.md（结构参考）_

- [ ] 5. 修正 `skills/feature-prune.md` 中的文件引用错误
  - File: `skills/feature-prune.md`（修改）
  - 定位 Step 2（场景对齐）中引用 `scenario-map.json` 的文本
  - 将 `scenario-map.json` 替换为 `screen-map.json`（位于 `.allforai/product-map/screen-map.json`）
  - 同时检查文件中是否还有其他不存在于 product-map 输出中的文件名引用，一并修正
  - _Requirements: 3.5（频次数据来源对齐）_
  - _Leverage: skills/feature-prune.md（待修改），docs/plans/2026-02-24-product-map-design.md（product-map 输出文件列表）_

- [ ] 6. 重写 `commands/feature-prune.md`
  - File: `commands/feature-prune.md`（修改，覆盖现有内容）
  - YAML frontmatter: description（功能剪枝：基于 product-map 频次数据评估功能去留。模式: full / quick / scope）、allowed-tools（含 WebSearch/WebFetch，用于竞品搜索）
  - 模式路由：`full`（默认，Step 1–5）/ `quick`（Step 1+2+4+5，跳过 Step 3 竞品参考）/ `scope <模块名>`（限定模块）
  - 前置检查：
    - `.allforai/product-map/product-map.json` 不存在 → 提示"请先运行 /product-map"，终止
    - `scope` 模式：检查 `.allforai/feature-prune/frequency-tier.json`，不存在则提示先跑 `full`
    - 自动加载 `.allforai/feature-prune/prune-decisions.json` 历史决策
  - 执行流程说明：从 Step 1 开始（Step 0 已由 product-map 承担），频次数据直接读取 `.allforai/product-map/task-inventory.json`，高频任务自动受保护
  - 详细文档引用：`${CLAUDE_PLUGIN_ROOT}/skills/feature-prune.md`
  - Step 执行要求：每步完成写入 `.allforai/feature-prune/` 对应文件，等待用户确认
  - 报告模板：CORE/DEFER/CUT 数量统计、完整 CUT 清单（含证据）、完整 DEFER 清单（含时机建议）
  - 铁律引用：`${CLAUDE_PLUGIN_ROOT}/skills/feature-prune.md`
  - _Requirements: 3.1–3.9_
  - _Leverage: commands/feature-audit.md（结构参考）, skills/feature-prune.md_

- [ ] 7. 新建 `skills/seed-forge.md`（重命名自 demo-forge.md）
  - File: `skills/seed-forge.md`（新建）
  - 读取现有 `skills/demo-forge.md`（已重写为种子数据锻造版本）
  - 更新 YAML frontmatter：name 改为 `seed-forge`，version 保持 "2.0.0"，description 触发词更新（"seed-forge"/"种子数据"/"seed data" 等）
  - 更新文件内所有 `/demo-forge` 命令引用为 `/seed-forge`
  - 内容保持不变（demo-forge.md 已完整重写）
  - 旧文件 `skills/demo-forge.md` 保留不删除
  - _Requirements: 4.1_
  - _Leverage: skills/demo-forge.md（内容来源）_

- [ ] 8. 新建 `commands/seed-forge.md`（重命名自 demo-forge.md）
  - File: `commands/seed-forge.md`（新建）
  - YAML frontmatter: description（种子数据锻造：按 product-map 角色/频次/场景生成真实感种子数据。模式: full / plan / fill / clean）、allowed-tools（含 WebSearch/WebFetch，用于行业风格搜索）
  - 模式路由：`full`（默认，Step 0–4）/ `plan`（Step 0–2，不需要应用运行）/ `fill`（加载已有方案，执行 Step 3–4）/ `clean`（删除种子数据，强制二次确认）
  - 前置检查：
    - `.allforai/product-map/product-map.json` 不存在 → 提示"请先运行 /product-map"，终止
    - `fill` 模式：检查 `.allforai/seed-forge/seed-plan.json`，不存在则提示先跑 `plan`
    - `clean` 模式：检查 `.allforai/seed-forge/forge-data.json`，不存在则提示"没有可清理的数据"；存在则强制输出警告并要求用户输入确认词后才执行
  - 输出目录：`.allforai/seed-forge/`（向后兼容），文件名按新设计（seed-plan.json、style-profile.json、model-mapping.json 等）
  - 详细文档引用：`${CLAUDE_PLUGIN_ROOT}/skills/seed-forge.md`
  - Step 执行要求：每步完成写入 `.allforai/seed-forge/` 对应文件，等待用户确认
  - 报告模板：各角色账号数、按频次分层的数据量统计、场景链路完成情况、约束违规记录
  - Breaking changes 说明：文件名变更（旧 forge-plan.json → 新 seed-plan.json），旧 plan 文件不兼容新 fill
  - 铁律引用：`${CLAUDE_PLUGIN_ROOT}/skills/seed-forge.md`
  - _Requirements: 4.1–4.11_
  - _Leverage: commands/demo-forge.md（结构参考）, skills/seed-forge.md_

- [ ] 9. 更新 `SKILL.md`
  - File: `SKILL.md`（修改）
  - 更新 YAML frontmatter：version 升至 "2.0.0"，description 更新为 4 个技能的简介（product-map / feature-gap / feature-prune / seed-forge）
  - 更新标题和定位描述
  - 替换"包含的技能"列表：
    - 删除 feature-audit 条目，新增 product-map 和 feature-gap 条目
    - 删除 demo-forge 条目，新增 seed-forge 条目
    - feature-prune 条目更新描述（现基于 product-map 频次数据）
  - 更新命令示例（`/feature-audit` → `/feature-gap`，`/demo-forge` → `/seed-forge`，新增 `/product-map`）
  - 更新定位图（4 个技能的层级关系）
  - _Requirements: 5.2_
  - _Leverage: SKILL.md（现有结构）_

- [ ] 10. 更新 `README.md`
  - File: `README.md`（修改）
  - 将"包含的技能"章节中 `feature-audit` 小节标题改为 `feature-gap`，内容描述更新
  - 将 `demo-forge` 小节标题改为 `seed-forge`，内容描述更新
  - 将"使用"章节中所有 `/feature-audit` 命令替换为 `/feature-gap`
  - 将所有 `/demo-forge` 命令替换为 `/seed-forge`
  - 更新输出文件表格：`.feature-audit/` → `.allforai/feature-gap/`，`audit-decisions.json` → `gap-decisions.json`
  - 更新"定位"章节的技能名称图
  - _Requirements: 5.3_
  - _Leverage: README.md（现有内容）_

- [ ] 11. 更新 `.claude-plugin/plugin.json`
  - File: `.claude-plugin/plugin.json`（修改）
  - version 升至 "2.0.0"
  - description 更新：列出 4 个技能名称（product-map / feature-gap / feature-prune / seed-forge），中英文各一句
  - _Requirements: 5.1_
  - _Leverage: .claude-plugin/plugin.json（现有结构）_

- [ ] 12. 删除已被替换的旧文件
  - Files: `skills/feature-audit.md`、`skills/demo-forge.md`、`commands/feature-audit.md`、`commands/demo-forge.md`
  - _Depends on: Tasks 3, 4, 7, 8_
  - 使用 Bash 删除 4 个旧文件
  - 验证 `skills/` 和 `commands/` 目录下只剩 product-map.md、feature-gap.md、feature-prune.md、seed-forge.md
  - _Requirements: 2.1（重命名即删旧建新）, 4.1_
