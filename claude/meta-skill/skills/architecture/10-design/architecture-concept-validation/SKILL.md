---
name: architecture-10-design-architecture-concept-validation
description: 在程序实现前生成并验证中文 HTML gate，检查技术框架与技术架构决策是否与产品、App、游戏设计交付物闭合。
---

# 技术架构概念验证 Skill

> meta-skill 内置子 skill。
> 状态：随 meta-skill 安装，并通过 `architecture-concept-validation`
> 节点注入规则接入 bootstrap。

## 概述

本 skill 在程序实现前创建“技术框架 / 技术架构决策”验证 gate。它验证所选技术栈与架构是否能够承载产品概念、App 或游戏设计交付物、端与运行时形态、数据/API/状态边界、安全权限要求，以及自动化验证路径。

这不是代码生成 skill。它的职责是在下游实现节点开始前，阻断模糊、冲突、无法验收的技术决策。

## 输入契约

存在时必须读取：

- `.allforai/bootstrap/bootstrap-profile.json`
- `.allforai/bootstrap/workflow.json`
- `.allforai/product-concept/concept-baseline.json`
- `.allforai/concept-contract.json`
- App 程序交付：`.allforai/app-design/handoff/program-development-node-handoff.json`
- 游戏程序交付：`.allforai/game-design/design/program-development-node-handoff.json`
- 生成的节点规格：`.allforai/bootstrap/node-specs/`
- 仓库扫描证据：package 文件、lockfile、框架配置、构建脚本、引擎项目文件、部署文件、已有测试、运行入口

可选读取：

- `.allforai/product-concept/tech-architecture.json`
- `.allforai/app-domain/*/handoff/*.json`
- `.allforai/game-runtime/art/engine-ready-art-manifest.json`
- `.allforai/game-design/art/export/engine-ready-art-output-contract.json`
- 已有架构、安全、数据库、API、部署或测试报告

如果必需的上游交付物缺失，必须在输出 JSON 中声明。不得从对话记忆中补全完整架构。

## 输出契约

写入：

- `.allforai/architecture/architecture-concept-validation.html`
- `.allforai/architecture/architecture-concept-validation.json`
- `.allforai/architecture/architecture-concept-validation-report.json`

JSON 必须包含：

- `validation_id`
- `source_refs`
- `product_scope_summary`
- `project_shape`
- `selected_technical_stack`
- `surface_runtime_decisions`
- `module_boundaries`
- `data_api_state_boundaries`
- `security_permission_boundaries`
- `third_party_dependencies`
- `build_test_run_validation_plan`
- `downstream_implementation_mapping`
- `blocked_validation_items`
- `implementation_node_readiness`
- `risk_flags`
- `approval_summary`
- `state`
- `consumer_refs`

允许的 `state`：

- `passed`
- `passed_with_warnings`
- `needs_revision`
- `blocked_by_missing_design_handoff`
- `blocked_by_stack_conflict`
- `blocked_by_unverifiable_runtime`
- `failed_validation`

HTML 必须使用中文，面向人类阅读。相关决策必须组织为树状或可折叠结构，避免信息压迫。

## 调用契约

```json
{
  "skill": "architecture/architecture-concept-validation",
  "mode": "generate_validate",
  "input_paths": {
    "bootstrap_profile": ".allforai/bootstrap/bootstrap-profile.json",
    "workflow": ".allforai/bootstrap/workflow.json",
    "concept_contract": ".allforai/concept-contract.json",
    "product_concept": ".allforai/product-concept/concept-baseline.json",
    "app_program_handoff": ".allforai/app-design/handoff/program-development-node-handoff.json",
    "game_program_handoff": ".allforai/game-design/design/program-development-node-handoff.json",
    "tech_architecture": ".allforai/product-concept/tech-architecture.json"
  },
  "output_root": ".allforai/architecture"
}
```

支持模式：`generate_validate`、`validate_existing`、`repair_existing`。

## HTML Gate 要求

HTML 页面必须展示：

- 首屏摘要：产品/App/游戏范围、项目形态、选定技术栈、gate 状态、阻塞风险；
- 来源树：读取了哪些上游交付物，缺失了哪些证据；
- 项目形态：纯客户端、纯后端、多前端、后台加移动端加官网加统一后端、浏览器游戏、原生游戏、混合项目、既有代码延续等；
- 技术栈决策树：框架、语言、运行时、构建工具、包管理器、持久化、API 风格、认证/会话模型、部署目标、引擎或素材导入器；
- 端与运行时映射：每组 App 页面、游戏场景、后端服务、管理后台、任务 worker、导入器都必须映射到所属模块；
- 数据/API/状态边界：事实源、客户端缓存、服务端状态、本地持久化、同步/离线、迁移、契约测试；
- 安全与权限边界：认证、角色、密钥、支付、上传、审核、反滥用、平台权限、合规注意事项；
- 验证计划：能够证明架构可用的构建、测试、运行、UI 自动化、模拟器、浏览器或引擎导入命令；
- 下游节点就绪度：每个实现节点要么具备明确契约，要么带有修复路由并被阻塞。

不得把 blocker 藏在叙述文字中。每个 blocker 必须包含 `owner_skill`、`repair_target`、`blocks_implementation: true` 和具体缺失证据。

## 自动验证

必须检查：

- 当前项目类型具备对应设计交付物：App 项目读取 App 程序交付；游戏项目读取游戏程序交付；混合项目可能两者都需要；
- 选定技术栈与仓库证据兼容，或者明确标记为新技术栈迁移；
- 项目形态覆盖所有需要的端：移动端、网页端、管理后台、商户/经纪人后台、后端、worker、游戏运行时、编辑器/导入器、内容工具等；
- 每个下游实现节点至少具备一个所属模块、输入交付物、输出交付物和验证命令族；
- 数据、API、状态归属在多端之间没有冲突；
- 安全敏感流程具备负责人和验证方式；
- 第三方服务、SDK、引擎或素材导入器声明了安装、运行、验证要求；
- 运行时验证不能伪造。如果当前环境无法执行必要的运行、构建或导入验证，必须设置 `state: "blocked_by_unverifiable_runtime"`，或把具体事项写入 `blocked_validation_items`。

修复路由：

- 缺少 App 设计交付物，路由到 `app-design-finalize`；
- 缺少游戏设计交付物，路由到 `game-design-finalize`；
- 缺少美术运行时 manifest，路由到 `game-art/40-qa/engine-ready-art-output-contract`；
- 技术栈冲突，在上游概念或设计调整后，以 `repair_existing` 模式重新执行本 gate；
- 无法验证运行时，路由到对应环境/工具能力节点；如果没有可用工具，则报告硬阻塞验证项。

## 完成条件

只有当 HTML 和 JSON 都存在，且 JSON 的 `state` 为 `passed` 或 `passed_with_warnings` 时，才返回 `COMPLETED`。

当架构内部不一致或无法安全交付给实现节点时，返回 `FAILED_VALIDATION`。

当必需的运行、构建或导入验证无法执行时，必须返回 blocked 状态，不得返回 `COMPLETED`。

