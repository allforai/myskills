---
name: code-replicate
description: >
  Code Replication Bridge: reverse-engineer existing codebases (any tech stack) into
  .allforai/ artifacts compatible with the dev-forge pipeline. 4 fidelity levels:
  interface (API contracts only), functional (business behavior), architecture (module
  structure + patterns), exact (100% replicate including bugs). Hands off to
  /design-to-spec → /task-execute for target-stack code generation.
  代码复刻桥接：逆向工程已有代码库，生成 allforai 产物，交还 dev-forge 流水线
  （/design-to-spec → /task-execute）生成目标技术栈代码。
version: "1.0.0"
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

## 命令列表

### `/code-replicate` — 主命令（推荐入口）

```
/code-replicate                          # 交互式选择信度等级
/code-replicate interface ./src          # 仅复刻 API 合约
/code-replicate functional ./src         # 复刻业务行为（推荐默认）
/code-replicate architecture ./src       # 复刻模块结构
/code-replicate exact ./src              # 百分百复刻（含 bug）
```

### `/cr-interface` — 快捷接口复刻

固定 `interface` 模式，适合"后端重写，前端不动"场景。

### `/cr-exact` — 快捷精准复刻

固定 `exact` 模式，适合行为零容忍回归或监管合规场景。

> ⚠️ 此模式耗时最长，建议仅用于关键模块。

### `/cr-status` — 查看进度

读取 `.allforai/code-replicate/replicate-config.json`，展示当前步骤进度和产物状态。

## 技能详情

> 详见 `${CLAUDE_PLUGIN_ROOT}/skills/code-replicate.md`

## 信度等级速查

| 等级 | 复刻什么 | 适用场景 | 产物 |
|------|---------|---------|------|
| `interface` | API 合约 | 后端重写，前端不动 | task-inventory + api-contracts |
| `functional` | 业务行为 | 技术栈迁移 | + business-flows + use-case-tree |
| `architecture` | 模块结构 | 大规模重构 | + arch-map |
| `exact` | 百分百复刻 | 行为零容忍 | + bug-registry + constraints |

## 增强协议（4D + 6V + XV）

> 通用框架见 `docs/information-fidelity.md`，代码复刻方向定制见 `skills/code-replicate.md`

源码是信息，失真发生在读取→提取→映射三个环节。

- **4D 信息卡**：每个行为/端点携带结论层（做什么）+ 证据层（代码位置引用）+ 约束层（内嵌业务/技术约束）+ 决策层（为什么这样实现）
- **6V 视角矩阵**：高风险行为从 user/business/tech/ux/data/risk 六视角描述，重点是 `tech.mapping_risk`（跨栈映射风险）和 `risk.if_wrong`（复刻偏差后果）
- **XV 跨模型验证**：Step 2 后自动执行（检测 `OPENROUTER_API_KEY`）— 行为遗漏检测 + 跨栈语义漂移风险；高严重度发现自动追加到产物，不问用户
- **ONE-SHOT 决策**：所有歧义在 Step 3 汇总后一次性处理，不拦截分析流程
- **决策持久化**：跨 session 复用历史映射决策

## 项目类型感知

本技能自动识别源码项目类型并调整分析策略：

| 类型 | 检测特征 | 重点分析 |
|------|---------|---------|
| **后端 API** | routes/controllers/middleware | API 合约、业务逻辑、ORM 映射 |
| **前端 Web** | components/pages/store/hooks | 组件树、路由、状态管理、API 调用 |
| **前端移动** | screens/widgets/navigation | 导航结构、状态管理、原生调用 |
| **微服务** | proto/queue/events/saga | 服务契约、消息格式、事件流 |
| **混合单体** | 多类型混合 | 拆分建议 + 各部分独立分析 |

> 详见 `${CLAUDE_PLUGIN_ROOT}/skills/code-replicate.md` 「项目类型感知分析」段落

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
    ├── stack-mapping.json
    ├── stack-mapping-decisions.json ← 持久化决策
    └── replicate-report.md
```

## 文档

- `${CLAUDE_PLUGIN_ROOT}/docs/fidelity-guide.md` — 信度等级详解
- `${CLAUDE_PLUGIN_ROOT}/docs/stack-mappings.md` — 跨栈映射参考
