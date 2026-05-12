# 技术架构概念验证 Capability

> 节点：`architecture-concept-validation`。
> 用途：在程序实现节点开始前，验证技术框架与技术架构决策是否已经从产品 / App / 游戏设计交付物闭合到可实现、可构建、可运行、可验收的程序契约。

## 目标

产出技术架构 HTML gate 与 JSON 验证结果，作为下游实现节点的强输入契约。

本 capability 不直接写业务代码。它负责确认下游代码节点不会在以下状态下启动：

- 技术栈未定；
- 多端项目形态不清；
- 模块边界、数据/API/状态归属冲突；
- 安全与权限要求缺失；
- 第三方依赖、运行时、引擎或导入器无法验证；
- 实现节点没有明确输入、输出和验收命令。

## 必需输出

| 输出 | 说明 |
|---|---|
| `.allforai/architecture/architecture-concept-validation.html` | 中文人类阅读 gate，展示技术架构决策、风险和阻塞项 |
| `.allforai/architecture/architecture-concept-validation.json` | 机器可读验证结果，包含 `state`、阻塞项、下游节点映射 |
| `.allforai/architecture/architecture-concept-validation-report.json` | 详细检查报告，供后续修复和审计使用 |

## 输入

| 输入 | 必需性 | 用途 |
|---|---|---|
| `.allforai/bootstrap/bootstrap-profile.json` | 必需 | 判断项目类型、技术栈、目标平台、项目形态 |
| `.allforai/bootstrap/workflow.json` | 必需 | 找到下游实现节点并建立 readiness 映射 |
| `.allforai/product-concept/concept-baseline.json` | 必需 | 读取产品范围、用户、核心价值、约束 |
| `.allforai/concept-contract.json` | 推荐 | 读取冻结后的概念契约 |
| `.allforai/app-design/handoff/program-development-node-handoff.json` | App 项目必需 | App 设计给程序实现的输入契约 |
| `.allforai/game-design/design/program-development-node-handoff.json` | 游戏项目必需 | 游戏设计给程序实现的输入契约 |
| `.allforai/product-concept/tech-architecture.json` | 可选 | 继承用户或前置概念阶段已选择的技术栈 |
| `.allforai/game-runtime/art/engine-ready-art-manifest.json` | 游戏前端涉及素材时必需 | 验证美术输出能被运行时消费 |

## 方法论

### 项目形态判定

先判定项目属于哪种形态：

- 纯客户端；
- 纯后端；
- 多前端；
- 管理后台 + 业务后台 + mobile + website + 统一后端；
- 浏览器游戏；
- 原生游戏；
- 2D 运行时 + 3D 辅助生产；
- 既有项目延续；
- 多仓库或 monorepo。

项目形态决定后续技术栈、模块边界、验证命令和下游节点拆分方式。

### 技术栈验证

必须把技术栈拆到可执行层级：

- 语言与运行时；
- 框架；
- 构建工具；
- 包管理器；
- 数据库与迁移方式；
- API 风格；
- 状态管理；
- 认证与会话；
- 部署目标；
- 测试框架；
- UI 自动化方式；
- 游戏引擎、素材导入器或渲染运行时。

如果仓库已有代码，必须以仓库证据为准。若要迁移技术栈，必须明确迁移范围和风险，不得静默覆盖已有技术路线。

### 下游实现节点映射

对 workflow 中每个下游实现、编译、测试、运行时冒烟、导入验证节点，必须写明：

- 读取哪些上游交付物；
- 负责哪个模块或端；
- 输出哪些文件或报告；
- 需要哪些构建 / 测试 / 运行命令证明结果有效；
- 如果当前环境无法验证，阻塞原因是什么。

## 验收规则

`architecture-concept-validation.json.state` 只能在以下情况为 `passed` 或 `passed_with_warnings`：

- 所有必需设计交付物存在；
- 技术栈与仓库证据不冲突；
- 每个下游实现节点都有明确输入、输出、模块边界和验证方式；
- 数据/API/状态归属没有冲突；
- 安全敏感流程具备验证方式；
- 需要运行、构建、导入或 UI 自动化验证的部分，具备真实执行路径。

如果无法运行、构建、导入或验证，必须返回 blocked 状态。不得用静态检查或文字说明替代验收。

## 下游消费者

| Artifact | 字段 | Consumer Capability | Required | 原因 |
|---|---|---|---|---|
| `.allforai/architecture/architecture-concept-validation.json` | `selected_technical_stack` | translate | required | 实现节点需要知道技术栈和运行时 |
| `.allforai/architecture/architecture-concept-validation.json` | `downstream_implementation_mapping` | translate | required | 实现节点需要明确模块、输入、输出和验证路径 |
| `.allforai/architecture/architecture-concept-validation.json` | `build_test_run_validation_plan` | compile-verify | required | 编译验证需要真实命令 |
| `.allforai/architecture/architecture-concept-validation.json` | `build_test_run_validation_plan` | test-verify | required | 测试验证需要测试范围与命令 |
| `.allforai/architecture/architecture-concept-validation.json` | `build_test_run_validation_plan` | runtime-smoke-verify | required | 运行时冒烟不能依赖猜测 |
| `.allforai/architecture/architecture-concept-validation.json` | `blocked_validation_items` | pipeline-closure-verify | required | 闭环验证必须暴露无法验收的事项 |

