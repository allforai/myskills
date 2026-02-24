---
description: "检查前后端字段名的全链路一致性。支持范围: full / frontend / backend / endtoend"
argument-hint: "[scope: full|frontend|backend|endtoend] [--module <name>]"
allowed-tools: ["Read", "Write", "Grep", "Glob", "Bash", "Task", "AskUserQuestion", "Skill"]
---

# FieldCheck — 字段一致性检查

用户请求: $ARGUMENTS

## 插件根目录

所有文档路径基于插件安装目录: `${CLAUDE_PLUGIN_ROOT}`

## Scope 路由

根据用户参数决定检查范围：

- **无参数 或 `full`** → 全链路: L1(UI) ↔ L2(API) ↔ L3(Entity) ↔ L4(DB)
- **`frontend`** → 仅前端: L1(UI) ↔ L2(API)
- **`backend`** → 仅后端: L2(API) ↔ L3(Entity) ↔ L4(DB)
- **`endtoend`** → 端到端: L1(UI) ↔ L4(DB)

`--module <name>` 可限制只分析指定模块（如 `--module user`）。

## 执行流程

1. 用 Read 工具读取 `${CLAUDE_PLUGIN_ROOT}/docs/fieldcheck/overview.md` 获取完整执行流程和注意事项
2. 根据 scope 按需读取对应的详细文档
3. 按 Step 0 → Step 1 → Step 2 → Step 3 → Step 3.5 → Step 4 执行
4. **【强制】执行完毕后，必须在对话中直接输出完整的报告摘要**

## 详细文档（按需用 Read 工具加载）

- `${CLAUDE_PLUGIN_ROOT}/docs/fieldcheck/overview.md` — 执行流程总览、问题分类、注意事项
- `${CLAUDE_PLUGIN_ROOT}/docs/fieldcheck/extractors.md` — 各层字段提取方法详解（含所有技术栈）
- `${CLAUDE_PLUGIN_ROOT}/docs/fieldcheck/matching.md` — 智能匹配算法详解
- `${CLAUDE_PLUGIN_ROOT}/docs/fieldcheck/report.md` — 报告格式定义和 JSON schema

---

## 执行步骤（详见 overview.md）

注意：fieldcheck 不强制要求完整的 deadhunt Phase 0，无 validation-profile.json 时做轻量探测即可。

| Step | 做什么 | 产出 |
|------|-------|------|
| Step 0 | 项目画像获取（检测/复用技术栈和模块列表） | 技术栈 + 模块确认 |
| Step 1 | 字段提取 L4→L3→L2→L1 | `field-profile.json` |
| Step 2 | 跨层映射（按模块分组智能匹配） | `field-mapping.json` |
| Step 3 | 问题检测（GHOST/TYPO/GAP/STALE/SEMANTIC/TYPE） | `field-issues.json` |
| Step 3.5 | 全链路矩阵交叉验证（仅 full/backend scope） | `field-matrix.json` + 问题升降级 |
| Step 4 | 报告生成 + **对话中输出完整摘要** | `field-report.md` + 对话摘要 |

所有产出写入 `.allforai/deadhunt/output/field-analysis/` 目录。

> **Flutter 项目注意**：当检测到 Flutter 客户端时，L1 提取会扫描 `.dart` Widget 文件，L2 提取会扫描 Dart 模型类（`fromJson`/`@JsonKey`）。同时启用 Flutter 特有问题类型检测（PLATFORM_GAP、SERIALIZE_MISMATCH、NULL_SAFETY）。详见 `${CLAUDE_PLUGIN_ROOT}/docs/fieldcheck/extractors.md`。

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
