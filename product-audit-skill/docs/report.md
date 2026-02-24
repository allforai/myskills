# Step 4: 报告生成 (Report Generation)

> 本步骤汇总前三步结果，生成最终审计报告和可操作任务清单。

---

## 1. 报告生成流程

报告生成严格按以下顺序执行：

1. **汇总前序结果** — 聚合 Step 1（需求清单）、Step 2（Gap 分析）、Step 3（闭环验证）的全部数据
2. **生成 3 个输出文件**：
   - `audit-report.md` — 完整审计报告（人类可读）
   - `audit-tasks.json` — 可操作任务清单（工具可消费）
   - `audit-decisions.json` — 用户决策日志（跨次审计持久化）
3. **在对话中输出摘要** — 这是**强制行为**，不可省略，不可仅生成文件而不展示

三个文件写入项目根目录（或用户指定的输出目录）。

---

## 2. audit-report.md 模板

完整报告使用以下 markdown 模板：

```markdown
# 功能审计报告

> 审计时间: {timestamp}
> 审计模式: {mode}
> 项目: {project_path}
> 需求源: {sources}

## 功能覆盖总览

| 分类 | 数量 | 占比 |
|------|------|------|
| COMPLETE | X | X% |
| PARTIAL | X | X% |
| MISSING | X | X% |
| UNPLANNED | X | X% |
| DEFERRED | X | X% |

## 闭环验证总览（仅 full/verify 模式）

| 评分 | 功能数 | 功能列表 |
|------|--------|----------|
| 4/4 完整闭环 | X | ... |
| 3/4 基本闭环 | X | ... |
| 2/4 部分闭环 | X | ... |
| 1/4 严重断裂 | X | ... |
| 0/4 无闭环 | X | ... |

## 功能地图

（按功能模块分组，展示每个功能的拓扑图）

### {模块名}

#### {功能名} (PF-XXX) — {COMPLETE|PARTIAL|MISSING}

用户旅程拓扑：

触发点 → 处理逻辑 → 反馈机制 → 结果可见
{file:line} → {file:line} → {file:line} → {file:line}

（如有断裂，在断裂处标注 [断裂]）

## MISSING 功能详情

| ID | 功能名称 | 需求源位置 | 用户决策 |
|----|----------|------------|----------|
| PF-XXX | {name} | {file}:{line} | {DEFERRED/待决策} |

逐项说明：

### PF-XXX: {功能名称}

- **需求源**: {file}:{line}
- **需求描述**: （原文引用）
- **搜索范围**: （列出搜索过的目录和关键词）
- **结论**: 未找到对应实现
- **用户决策**: {如有}

## PARTIAL 功能详情

| ID | 功能名称 | 已实现部分 | 缺失部分 |
|----|----------|------------|----------|
| PF-XXX | {name} | {what exists} | {what's missing} |

逐项说明：

### PF-XXX: {功能名称}

- **已实现**: {描述} — 证据: {file}:{line}
- **缺失**: {描述} — 在需求源 {file}:{line} 中要求但未找到实现
- **闭环评分**: X/4

## 闭环断裂详情

（仅列出评分 ≤ 3/4 的功能）

### PF-XXX: {功能名称} — 评分 X/4

功能地图：

触发点: {file}:{line} ✓
处理逻辑: {file}:{line} ✓
反馈机制: [断裂] 未找到用户反馈实现
结果可见: {file}:{line} ✓

- **断裂检查点**: {列出失败的检查点}
- **断裂模式**: {如: "静默操作" / "无反馈" / "结果不可见"}
- **证据**: {file}:{line} — {具体描述}

## UNPLANNED 功能详情

| ID | 功能名称 | 代码位置 | 用户决策 |
|----|----------|----------|----------|
| UF-XXX | {name} | {file}:{line} | {待决策} |

逐项说明：

### UF-XXX: {功能名称}

- **代码位置**: {file}:{line}
- **功能描述**: （从代码推断的功能描述）
- **未在以下需求源中提及**: {列出所有需求源}
- **用户决策**: {如有}

## DEFERRED 功能记录

| ID | 功能名称 | 原因 | 决策者 |
|----|----------|------|--------|
| PF-XXX | {name} | {reason} | 用户 / 上次审计 |

## 用户决策日志

（汇总本次审计中所有用户交互决策）

| 时间 | 功能 | 原分类 | 决策 | 原因 |
|------|------|--------|------|------|
| {time} | PF-XXX {name} | MISSING | DEFERRED | {reason} |
```

### 模板使用规则

- `{timestamp}` — ISO 8601 格式，如 `2024-01-15T10:30:00Z`
- `{mode}` — `quick` / `full` / `verify` / `incremental`
- 占比计算基于功能总数（COMPLETE + PARTIAL + MISSING + DEFERRED，不含 UNPLANNED）
- 闭环验证总览仅在 `full` 或 `verify` 模式下生成
- 所有 "详情" 部分，如果该分类数量为 0，输出 "无" 而不是省略该节

---

## 3. audit-tasks.json 格式

任务清单用于后续开发消费，每个发现的问题对应一个 task：

```json
{
  "audit_timestamp": "2024-01-15T10:30:00Z",
  "audit_mode": "full",
  "project_path": "/path/to/project",
  "tasks": [
    {
      "id": "T-001",
      "type": "MISSING",
      "feature_id": "PF-003",
      "feature_name": "批量导出",
      "description": "需求源 docs/prd.md:88 描述的批量导出功能未找到对应实现",
      "source_reference": "docs/prd.md:88",
      "priority": "user_decision",
      "status": "open"
    },
    {
      "id": "T-002",
      "type": "BROKEN_LOOP",
      "feature_id": "PF-005",
      "feature_name": "订单导出",
      "description": "用户旅程在第 3 步（反馈）和第 4 步（结果可见）中断",
      "broken_checkpoints": ["feedback", "result_visible"],
      "evidence": "src/pages/Orders.tsx:45",
      "priority": "medium",
      "status": "open"
    },
    {
      "id": "T-003",
      "type": "PARTIAL",
      "feature_id": "PF-007",
      "feature_name": "用户搜索",
      "description": "搜索功能已实现基础查询（src/search.ts:12），但缺少需求源 docs/prd.md:102 要求的模糊匹配和搜索建议",
      "missing_parts": ["模糊匹配", "搜索建议"],
      "implemented_parts": ["基础关键词查询"],
      "source_reference": "docs/prd.md:102",
      "priority": "medium",
      "status": "open"
    },
    {
      "id": "T-004",
      "type": "UNPLANNED",
      "feature_id": "UF-002",
      "feature_name": "调试面板",
      "description": "src/components/DebugPanel.tsx:1 实现了调试面板功能，未在任何需求源中提及",
      "code_location": "src/components/DebugPanel.tsx:1",
      "priority": "user_decision",
      "status": "open"
    }
  ]
}
```

### Task ID 规则

- `T-001` 起始，按发现顺序递增
- 同一功能可能产生多个 task（如既是 PARTIAL 又有 BROKEN_LOOP）

### Priority 规则

| 情况 | priority 值 | 原因 |
|------|-------------|------|
| MISSING 功能 | `user_decision` | 只有用户能决定是否需要实现 |
| 闭环断裂 score ≤ 2/4 | `high` | 用户旅程严重中断 |
| 闭环断裂 score = 3/4 | `medium` | 用户旅程基本可用但有缺陷 |
| UNPLANNED 功能 | `user_decision` | 只有用户能决定是否保留 |
| PARTIAL 功能 | `medium` | 功能存在但不完整 |

### Status 值

- `open` — 新发现，待处理
- `resolved` — 已修复（后续审计自动更新）
- `deferred` — 用户决策为延期
- `wontfix` — 用户决策为不修复

---

## 4. audit-decisions.json 格式

决策日志是**跨审计持久化**的核心文件：

```json
{
  "version": "1.0.0",
  "last_updated": "2024-01-15T10:30:00Z",
  "decisions": [
    {
      "feature_id": "PF-003",
      "feature_name": "批量导出",
      "classification": "DEFERRED",
      "reason": "计划 v2.0 实现",
      "decided_at": "2024-01-15T10:30:00Z",
      "audit_mode": "full"
    },
    {
      "feature_id": "UF-002",
      "feature_name": "调试面板",
      "classification": "ACCEPTED",
      "reason": "开发调试需要，保留",
      "decided_at": "2024-01-15T10:32:00Z",
      "audit_mode": "full"
    }
  ]
}
```

### 持久化规则

- **APPEND-ONLY** — 单次审计会话中只追加，不修改已有条目
- **跨次审计保留** — 下次运行 `incremental` 模式时自动读取并应用
- **同一功能多次决策** — 保留所有记录，以最新的 `decided_at` 为准
- **classification 可选值**: `DEFERRED` / `ACCEPTED` / `WONTFIX` / `MUST_IMPLEMENT`

### 自动应用逻辑

在 `incremental` 模式下读取此文件时：

1. 对于每个已有决策的功能，跳过用户交互，直接应用上次决策
2. 在报告中标注 "（自动应用上次决策）"
3. 仅对新发现的问题询问用户

---

## 5. 对话输出要求

生成文件后，**必须**在对话中输出报告摘要。这是强制行为，不可省略。

### 必须包含的内容

**覆盖率表格** — 与 audit-report.md 中的功能覆盖总览相同：

```
功能覆盖总览:
| 分类 | 数量 | 占比 |
|------|------|------|
| COMPLETE | 12 | 60% |
| PARTIAL | 3 | 15% |
| MISSING | 2 | 10% |
| UNPLANNED | 4 | — |
| DEFERRED | 3 | 15% |
```

**闭环评分分布**（仅 full/verify 模式）：

```
闭环验证:
- 4/4 完整闭环: 8 个功能
- 3/4 基本闭环: 3 个功能
- ≤2/4 断裂: 2 个功能
```

**每一个 MISSING 功能** — 必须列出，附需求源引用：

```
未实现功能:
- PF-003 批量导出 — 需求源: docs/prd.md:88
- PF-011 数据备份 — 需求源: docs/requirements.md:45
```

**每一个 PARTIAL 功能** — 必须列出，附缺失部分：

```
部分实现功能:
- PF-007 用户搜索 — 缺少: 模糊匹配, 搜索建议
- PF-009 报表生成 — 缺少: PDF 导出
```

**每一个闭环断裂** (score ≤ 3/4) — 必须列出，附功能地图和断裂点：

```
闭环断裂:
- PF-005 订单导出 (2/4) — 断裂: 反馈机制, 结果可见
  触发点 ✓ → 处理逻辑 ✓ → 反馈机制 ✗ → 结果可见 ✗
- PF-012 批量删除 (3/4) — 断裂: 结果可见
  触发点 ✓ → 处理逻辑 ✓ → 反馈机制 ✓ → 结果可见 ✗
```

**每一个 UNPLANNED 功能** — 必须列出，附代码位置：

```
计划外功能:
- UF-001 调试面板 — src/components/DebugPanel.tsx:1
- UF-003 彩蛋页面 — src/pages/Easter.tsx:1
```

### 禁止省略

- 不可用 "等 X 个功能" 省略任何条目
- 不可用 "详见报告文件" 替代对话输出
- 每个分类如果数量为 0，输出 "无"

---

## 6. incremental 模式报告差异

`incremental` 模式的报告在标准模板基础上增加差异分析：

### 额外的报告节

在功能覆盖总览之后，插入：

```markdown
## 增量审计差异

基准审计: {previous_audit_timestamp}
变更范围: {git_diff_summary}

### 新增问题

| ID | 类型 | 功能 | 说明 |
|----|------|------|------|
| T-XXX | {type} | {name} | {description} |

### 已解决问题

| ID | 类型 | 功能 | 说明 |
|----|------|------|------|
| T-XXX | {type} | {name} | 上次为 {status}，本次已实现 |

### 未变化问题

| ID | 类型 | 功能 | 说明 |
|----|------|------|------|
| T-XXX | {type} | {name} | 与上次审计结果一致 |
```

### 增量模式行为

1. **只重新评估受 git diff 影响的功能** — 其余功能沿用上次结果
2. **自动应用上次决策** — 读取 `audit-decisions.json`，对已有决策的功能不再询问
3. **对比上次 audit-tasks.json** — 标记哪些 task 已解决、哪些是新增、哪些未变
4. **报告中明确标注** — 每个功能的评估来源（"本次重新评估" vs "沿用上次结果"）

---

## 7. 词汇纪律检查

在输出报告前，执行自检。报告中的每一句话必须是**事实陈述**。

### 禁用词汇（出现即违规）

| 禁用表达 | 应替换为 |
|----------|----------|
| 应该添加 | 未找到实现 |
| 建议实现 | 需求源 {file}:{line} 描述的功能未找到对应实现 |
| 最佳实践 | （删除，不输出） |
| 建议优化 | 当前实现为 {描述}，需求源要求 {描述} |
| 可以考虑 | （删除，不输出） |
| 推荐使用 | （删除，不输出） |
| 应当改进 | 用户旅程在第 X 步中断 |

### 合规表达示例

合规：
- "未找到 PF-003（批量导出）的实现代码 — 需求源: docs/prd.md:88"
- "PF-005（订单导出）用户旅程在第 3 步（反馈机制）中断 — src/pages/Orders.tsx:45 的导出操作无 loading 状态或完成提示"
- "UF-002（调试面板）未在 docs/prd.md、docs/requirements.md 中提及 — 代码位置: src/components/DebugPanel.tsx:1"

违规：
- "建议添加批量导出功能以提升用户体验"
- "应该为订单导出添加 loading 状态，这是最佳实践"
- "可以考虑将调试面板移到开发环境专用构建中"

### 引用要求

每一条发现必须附带 `file:line` 引用：

- MISSING — 引用需求源位置（如 `docs/prd.md:88`）
- PARTIAL — 引用已实现代码位置 + 需求源位置
- BROKEN_LOOP — 引用断裂点的代码位置
- UNPLANNED — 引用代码位置

无法提供引用的发现不应出现在报告中。

---

## 8. 输出文件写入顺序

1. 先写 `audit-report.md`（完整报告）
2. 再写 `audit-tasks.json`（任务清单）
3. 再写/追加 `audit-decisions.json`（决策日志）
4. 最后在对话中输出摘要

如果 `audit-decisions.json` 已存在，读取后追加新决策，不覆盖已有内容。
