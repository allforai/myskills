---
name: code-replicate
description: >
  Code Replication Bridge: reverse-engineer existing codebases (any tech stack) into
  .allforai/ artifacts compatible with the dev-forge pipeline. 4 fidelity levels:
  interface (API contracts only), functional (business behavior), architecture (module
  structure + patterns), exact (100% replicate including bugs). Supports backend,
  frontend, fullstack (cross-validation), and module-level (dependency boundary)
  replication modes. Hands off to /design-to-spec → /task-execute for target-stack
  code generation. 代码复刻桥接：逆向工程已有代码库，生成 allforai 产物，交还
  dev-forge 流水线（/design-to-spec → /task-execute）生成目标技术栈代码。
  支持后端、前端、全栈（交叉验证）、模块级（依赖边界）四种复刻模式。
version: "1.1.1"
---

# Code Replicate — 代码复刻插件

> 逆向工程桥梁：已有代码 → `.allforai/` 产物 → dev-forge 流水线 → 目标技术栈代码

## 定位

```
product-design（产品层）     概念→地图→界面→用例→查漏→剪枝
dev-forge（开发层）          引导→规格→脚手架→执行→验证→验收
code-replicate（桥接层）     已有代码→逆向分析→allforai产物 → 接入 dev-forge ← 你在这里
deadhunt（QA 层）            死链→CRUD完整性→字段一致性
code-tuner（架构层）         合规→重复→抽象→评分
```

**核心洞察**：不是又一个代码生成工具，而是**逆向产品设计桥梁** — 将已有代码转化为 allforai 产物，复用整个 dev-forge 基础设施。

## 全流程使用

```
/code-replicate functional ./src   # 分析源码（选择信度等级）
    ↓
/design-to-spec                    # 基于 allforai 产物生成目标技术栈规格
    ↓
/task-execute                      # 逐任务生成代码
```

## 命令

只有一个入口：`/code-replicate`。通过参数控制信度等级、项目类型和范围。

```
/code-replicate                                                  # 交互式引导
/code-replicate functional ./src                                 # 后端复刻（自动检测类型）
/code-replicate functional ./src --type frontend                 # 前端复刻
/code-replicate functional ./src --type fullstack                # 全栈（前后端交叉验证）
/code-replicate functional ./src --type module --module src/user # 模块级复刻
/code-replicate interface ./src                                  # 仅复刻 API 合约
/code-replicate architecture ./src                               # 复刻模块结构
/code-replicate exact ./src                                      # 百分百复刻（含 bug）
/code-replicate functional https://github.com/org/repo.git       # 远程仓库
/code-replicate --from-phase 4                                   # 从 Phase 4 重跑（源码更新后）
/code-replicate status                                           # 查看进度
```

## 技能详情

本插件包含 5 个技能文件：

| 技能 | 类型 | 说明 |
|------|------|------|
| `code-replicate-core.md` | 内部共享 | 4D/6V/XV 协议、Phase 1/3/5/6/7、铁律 |
| `cr-backend.md` | 后端专用 | 后端 Phase 2/4/6：API 合约、Service 逻辑、ORM、微服务 |
| `cr-frontend.md` | 前端专用 | 前端 Phase 2/4/6：组件树、路由、状态管理、移动端导航 |
| `cr-fullstack.md` | 全栈专用 | 双栈 Phase 2/4 + 交叉验证层：API 绑定、Schema 对齐、认证传播 |
| `cr-module.md` | 模块专用 | 依赖边界扫描：外部依赖、事件契约、共享层识别 |

> cr-backend / cr-frontend / cr-fullstack / cr-module 各自加载 core 作为协议基础。

## 信度等级速查

| 等级 | 复刻什么 | 适用场景 | 产物 |
|------|---------|---------|------|
| `interface` | API 合约 | 后端重写，前端不动 | task-inventory + api-contracts |
| `functional` | 业务行为 | 技术栈迁移 | + business-flows + use-case-tree |
| `architecture` | 模块结构 | 大规模重构 | + arch-map |
| `exact` | 百分百复刻 | 行为零容忍 | + bug-registry + constraints |

## 增强协议（4D + 6V + XV）

> 代码复刻方向的 4D/6V/XV 定制协议见 `skills/code-replicate-core.md`

源码是信息，失真发生在读取→提取→映射三个环节。

- **4D 信息卡**：每个行为/端点携带结论层（做什么）+ 证据层（代码位置引用）+ 约束层（内嵌业务/技术约束）+ 决策层（为什么这样实现）
- **6V 视角矩阵**：高风险行为从 user/business/tech/ux/data/risk 六视角描述，重点是 `tech.mapping_risk`（跨栈映射风险）和 `risk.if_wrong`（复刻偏差后果）
- **XV 跨模型验证**：Phase 4 后自动执行（检测 `OPENROUTER_API_KEY`）— 行为遗漏检测 + 跨栈语义漂移风险；高严重度发现自动追加到产物，不问用户
- **ONE-SHOT 决策**：所有歧义在 Phase 5 汇总后一次性处理，不拦截分析流程
- **决策持久化**：跨 session 复用历史映射决策

## 项目类型感知

本技能自动识别源码项目类型并调整分析策略：

| 类型 | 检测特征 | 重点分析 | 使用技能 |
|------|---------|---------|---------|
| **后端 API** | routes/controllers/middleware | API 合约、业务逻辑、ORM 映射 | cr-backend |
| **微服务** | proto/queue/events/saga | 服务契约、消息格式、事件流 | cr-backend |
| **前端 Web** | components/pages/store/hooks | 组件树、路由、状态管理、API 调用 | cr-frontend |
| **前端移动** | screens/widgets/navigation | 导航结构、状态管理、原生调用 | cr-frontend |
| **全栈项目** | 前后端代码共存（monorepo/全栈框架） | 双栈分析 + 交叉验证 | cr-fullstack |
| **混合单体** | 多类型混合 | 拆分后分别用 cr-backend + cr-frontend | 两者 |

> **模块级复刻**不是项目类型，而是分析模式。使用 `--type module` 时，项目类型（后端/前端）从源码自动检测，额外增加依赖边界扫描。

## 输出目录

```
.allforai/
├── product-map/
│   ├── task-inventory.json          ← 所有模式
│   ├── business-flows.json          ← functional+
│   └── constraints.json             ← exact
├── use-case/
│   └── use-case-tree.json           ← functional+
└── code-replicate/
    ├── replicate-config.json
    ├── source-analysis.json
    ├── api-contracts.json
    ├── behavior-specs.json          ← functional+
    ├── arch-map.json                ← architecture+
    ├── bug-registry.json            ← exact
    ├── module-boundaries.json       ← cr-module 模式
    ├── stack-mapping.json
    ├── stack-mapping-decisions.json ← 持久化决策
    ├── replicate-report.md
    ├── backend/                     ← fullstack 模式：后端产物
    ├── frontend/                    ← fullstack 模式：前端产物
    ├── api-bindings.json            ← fullstack 交叉验证
    ├── schema-alignment.json        ← fullstack 交叉验证
    ├── constraint-reconciliation.json ← fullstack 交叉验证
    ├── auth-propagation.json        ← fullstack 交叉验证
    ├── error-mapping.json           ← fullstack 交叉验证
    ├── infrastructure.json          ← fullstack 基础设施
    └── fullstack-report.md          ← fullstack 统一报告
```

## 文档

- `${CLAUDE_PLUGIN_ROOT}/docs/fidelity-guide.md` — 信度等级详解
- `${CLAUDE_PLUGIN_ROOT}/docs/stack-mappings.md` — 跨栈映射参考
