---
description: "检查前后端字段名的全链路一致性。支持范围: full / frontend / backend / endtoend"
---

# FieldCheck — 字段一致性检查



## Scope 路由

根据用户参数决定检查范围：

- **无参数 或 `full`** → 全链路: L1(UI) ↔ L2(API) ↔ L3(Entity) ↔ L4(DB)
- **`frontend`** → 仅前端: L1(UI) ↔ L2(API)
- **`backend`** → 仅后端: L2(API) ↔ L3(Entity) ↔ L4(DB)
- **`endtoend`** → 端到端: L1(UI) ↔ L4(DB)

`--module <name>` 可限制只分析指定模块（如 `--module user`）。

## 执行流程

1. 读取 `./docs/deadhunt/fieldcheck/overview.md` 获取完整执行流程和注意事项
2. 根据 scope 按需读取对应的详细文档
3. 按 Step 0 → Step 1 → Step 2 → Step 3 → Step 3.5 → Step 4 执行
4. **【强制】执行完毕后，必须在对话中直接输出完整的报告摘要**

## 详细文档（按需加载）

- `./docs/deadhunt/fieldcheck/overview.md` — 执行流程总览、问题分类、注意事项
- `./docs/deadhunt/fieldcheck/extractors.md` — 各层字段提取方法详解（含所有技术栈）
- `./docs/deadhunt/fieldcheck/matching.md` — 智能匹配算法详解
- `./docs/deadhunt/fieldcheck/report.md` — 报告格式定义和 JSON schema

---

## 上游消费链（Front-load Decisions）

Step 0 的 2 个决策项可从上游产物自动获取，**已从上游获取的决策直接采用（展示一行摘要），仅缺失或冲突项才询问用户**：

```
优先级 1: .allforai/deadhunt/fieldcheck-decisions.json（自身 resume 缓存）
    ↓ 不存在或过期
优先级 2: .allforai/deadhunt/deadhunt-decisions.json（deadhunt 已确认的画像）
    ↓ 不存在
优先级 3: .allforai/project-forge/project-manifest.json（project-setup 产出）
    ↓ 不存在
优先级 4: 轻量探测（扫描代码推断）
    ↓ 无法推断
优先级 5: 假设合理默认值（仅在阻塞时才询问用户）
```

**字段映射表**：

| Step 0 决策项 | deadhunt-decisions.json | project-manifest.json |
|--------------|------------------------|----------------------|
| tech-stack | `decisions[item_id=tech-stack].value`（若 deadhunt 已跑过） | `sub_projects[].tech_stack` |
| module-list | `decisions[item_id=module-classification].value` | `sub_projects[].modules[]` |

**执行逻辑**：

1. 尝试读取 `fieldcheck-decisions.json` → 已有决策的步骤自动跳过
2. 尝试读取 `deadhunt-decisions.json` → deadhunt 已确认的技术栈和模块可直接复用
3. 尝试读取 `project-manifest.json` → 提取技术栈和模块列表
4. 自动填充的项展示「✓ tech-stack: Go (Gin) — 来自 deadhunt-decisions」
5. 仅无法映射的缺失项做轻量探测或询问用户

---

## 执行步骤（详见 overview.md）

注意：fieldcheck 不强制要求完整的 deadhunt Phase 0，优先从上游消费链获取画像，无上游时做轻量探测即可。

| Step | 做什么 | 产出 |
|------|-------|------|
| Step 0 | 项目画像获取（上游消费 → 检测/复用技术栈和模块列表） | 技术栈 + 模块确认 |
| Step 1 | 字段提取 L4→L3→L2→L1 | `field-profile.json` |
| Step 2 | 跨层映射（按模块分组智能匹配） | `field-mapping.json` |
| Step 3 | 问题检测（GHOST/TYPO/GAP/STALE/SEMANTIC/TYPE） | `field-issues.json` |
| Step 3.5 | 全链路矩阵交叉验证（仅 full/backend scope） | `field-matrix.json` + 问题升降级 |
| Step 4 | 报告生成 + **对话中输出完整摘要** | `field-report.md` + 对话摘要 |

所有产出写入 `.allforai/deadhunt/output/field-analysis/` 目录。

决策日志写入 `.allforai/deadhunt/fieldcheck-decisions.json`。

> **Flutter 项目注意**：当检测到 Flutter 客户端时，L1 提取会扫描 `.dart` Widget 文件，L2 提取会扫描 Dart 模型类（`fromJson`/`@JsonKey`）。同时启用 Flutter 特有问题类型检测（PLATFORM_GAP、SERIALIZE_MISMATCH、NULL_SAFETY）。详见 `./docs/deadhunt/fieldcheck/extractors.md`。

---

## 决策日志

每次用户确认决策时，追加记录到 `fieldcheck-decisions.json`：

```json
{
  "decisions": [
    {
      "step": "Step 0",
      "item_id": "tech-stack",
      "decision": "confirmed",
      "value": "...",
      "decided_at": "ISO8601"
    }
  ]
}
```

**输出路径**：`.allforai/deadhunt/fieldcheck-decisions.json`

**记录时机**：Step 0 中的以下决策点：
- `tech-stack` — 技术栈确认
- `module-list` — 模块列表确认

**resume 模式**：已有 decisions.json 时，已确认步骤自动跳过（展示一行摘要），从第一个无决策记录的步骤继续。

---

### 规模自适应

根据字段总数调整报告展示策略：
- **小规模**（≤50 个字段）：逐条展示所有字段映射和问题
- **中规模**（51-200 个字段）：按模块分组摘要，仅展开 SEMANTIC 和 MISSING 问题详情
- **大规模**（>200 个字段）：统计概览（各层字段数、各类问题计数）+ 仅展示严重问题

---

## 报告输出要求（强制执行）

**不要只说"报告已完成"或"报告已保存"。你必须在对话中直接展示以下内容：**

```
## 字段一致性检查报告

> 分析时间: {时间}
> 分析范围: {模块数} 个模块, {scope} 模式
> 字段总数: L1={n} / L2={n} / L3={n} / L4={n}

### 总览
| 层级对比 | 字段数 | 一致 | 不一致 | 覆盖率 |
|---------|--------|------|--------|--------|
| L1↔L2   | xxx    | xxx  | xxx    | xx.x%  |
| L2↔L3   | xxx    | xxx  | xxx    | xx.x%  |
| L3↔L4   | xxx    | xxx  | xxx    | xx.x%  |

### 🔴 严重问题 (Critical)
(逐条列出：ID、类型、模块、字段、位置、修复建议)

### 🟡 警告 (Warning)
(逐条列出)

### ❓ 需人工确认
(语义歧义等，说明为什么无法自动判定)

### 字段热力图
(哪些模块不一致最多)

### 下一步建议
1. 优先修复 🔴 Critical
2. 对 ❓ 项逐个确认
3. Stale 字段建议下次迭代清理
4. 修复后重新运行 `/deadhunt:fieldcheck`

> 完整报告: `.allforai/deadhunt/output/field-analysis/field-report.md`
> 问题清单: `.allforai/deadhunt/output/field-analysis/field-issues.json`
```

**关键：摘要必须包含具体的问题列表和修复建议，不能只给统计数字。用户看完摘要就能知道出了什么问题、在哪里、怎么修。**
