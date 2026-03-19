---
name: design-audit
description: >
  Use when the user asks to "verify design consistency", "audit design pipeline",
  "check design coverage", "trace design artifacts", "design-audit", "设计审计",
  "设计校验", "链路一致性", "覆盖率检查", "逆向追溯", "洪泛验证",
  or mentions cross-layer verification, design traceability, artifact consistency.
  Requires product-map to have been run first.
version: "1.1.0"
---

# Design Audit — 设计审计

> 跨层校验产品设计全链路一致性：逆向追溯、覆盖洪泛、横向一致性。

## 加载指令

执行本技能前，**必须加载以下补充文档**（完整审计维度和规则定义）：

1. `${CLAUDE_PLUGIN_ROOT}/docs/design-audit/audit-dimensions.md` — 所有审计维度定义（Phase A/B/C 步骤、检测项、输出格式、JSON Schema、Markdown 报告结构）
2. `${CLAUDE_PLUGIN_ROOT}/docs/design-audit/fix-rules.md` — 增强协议、全自动模式、防御性规范、铁律

---

## 目标

以 `product-map` 为锚点，从三个维度校验设计产物链路：

1. **逆向追溯（Trace）** — 每个下游产物是否有上游源头？
2. **覆盖洪泛（Coverage）** — 每个上游节点是否被下游完整消费？
3. **横向一致性（Cross-check）** — 相邻层之间有无矛盾？
4. **信息保真（Fidelity）** — 关键对象是否可追溯且具备多视角覆盖？
5. **模式一致性（Pattern Consistency）** — 相同功能模式是否使用了一致的设计套路？（仅当 experience-map.json screen 节点含 _pattern* 字段时激活）
6. **行为一致性（Behavioral Consistency）** — 跨界面行为是否遵循已确认的行为规范？（仅当 experience-map.json screen 节点含 _behavioral* 字段时激活）
7. **交互类型一致性（Interaction Type Consistency）** — 相同交互类型的界面是否遵循统一的布局约束？（仅当 experience-map 含 interaction_type 时激活）
8. **用户端成熟度一致性（Consumer Maturity Consistency）** — 若 `experience_priority = consumer|mixed`，下游产物是否持续保持用户端成熟产品标准，而非回落成后台式或概念式表达

发现问题只报告，不修改任何上游产物。

---

## 定位

```
product-map（锚点）
    ↓ 逆向追溯（从下往上）
    experience-map ← use-case ← feature-gap ← ui-design
    ↓ 覆盖洪泛（从上往下）
    task → screen → use-case → gap → ui-design
    ↓ 横向一致性（相邻层对比）
    frequency × depth / use-case × screen
    ↓ 模式一致性（仅当 experience-map.json screen 含 _pattern* 字段）
    experience-map screen._pattern* → ui-design-spec（_pattern_group 界面是否设计一致）
    ↓ 行为一致性（仅当 experience-map.json screen 含 _behavioral* 字段）
    experience-map screen._behavioral* → ui-design-spec（界面是否遵循行为规范）
```

**前提**：必须先运行 `product-map`，生成 `.allforai/product-map/product-map.json`。

若 `product-map.json` 含 `experience_priority`，design-audit 必须把它作为全链路审计基线之一。

---

## 快速开始

```
/design-audit              # 三合一全量校验
/design-audit trace        # 仅逆向追溯
/design-audit coverage     # 仅覆盖洪泛
/design-audit cross        # 仅横向一致性
/design-audit pattern        # 仅模式一致性检查（需 experience-map screen 含 _pattern* 字段）
/design-audit behavioral     # 仅行为一致性检查（需 experience-map screen 含 _behavioral* 字段）
/design-audit role 运营专员  # 指定角色全链路校验
```

---

## 工作流（三阶段并行架构）

```
前置：
      概念蒸馏基线（推拉协议 §三.A）：
        .allforai/product-concept/concept-baseline.json → 自动加载，不存在则 WARNING
      ↓
Phase A（脚本，串行）: 确定性检查
      gen_design_audit.py 执行：
        前置：两阶段加载 + 产物探测
        Step 1: 逆向追溯（Trace）
        Step 2: 覆盖洪泛（Coverage）
        Step 3: 横向一致性（Cross-check）
        Step 3.5: 信息保真门禁（Fidelity）
        Step 3.7: 连贯性审计（Continuity）
        Step 3.8: 用户端成熟度审计（当 `experience_priority = consumer|mixed`）
        XV 交叉验证（如可用）
      输出: audit-report.json（基线报告）+ audit-report.md
      ↓
Phase B（LLM，并行 3 Agent）: 语义审计
      Agent 1: 模式一致性(Step 5) + 创新保真(Step 5.5)
        → 写入 .allforai/design-audit/audit-shard-pattern.json
      Agent 2: 行为一致性(Step 5.6)
        → 写入 .allforai/design-audit/audit-shard-behavioral.json
      Agent 3: 交互类型一致性(Step 5.7)
        → 写入 .allforai/design-audit/audit-shard-interaction.json
      ↓（屏障同步：3 Agent 全部完成后继续）
Phase C（合并）: 汇总报告
      读取 audit-report.json（Phase A 基线）
      读取 3 个 audit-shard-*.json 分片
      合并到 audit-report.json 最终版
      重新生成 audit-report.md（含全部维度）
```

> 详细步骤定义见 `docs/design-audit/audit-dimensions.md`。
> 增强协议、全自动模式、防御性规范见 `docs/design-audit/fix-rules.md`。

若 `experience_priority.mode = consumer` 或 `mixed`，design-audit 额外检查：

- product-map 是否定义了主线闭环与持续关系
- experience-map 是否保留了首页主线、下一步引导、状态系统
- ui-design 是否把这些要求落实为视觉与交互规格
- feature-gap / use-case 是否仍能识别用户端成熟度缺口

若链路中任一层把用户端退化成“功能入口拼盘”“后台页面压缩版”或“概念 demo 页面集合”，应记为一致性问题。

---

## 输出文件结构

```
.allforai/design-audit/
├── audit-report.json     # 全量校验结果（机器可读）
└── audit-report.md       # 人类可读摘要
```
