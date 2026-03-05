---
description: "查看演示锻造进度：当前轮次、各阶段状态、通过率、产物文件。"
allowed-tools: ["Read", "Glob", "Bash"]
---

# Demo Forge Status — 演示锻造进度

用户请求: $ARGUMENTS

## 执行方式

读取当前项目的演示锻造状态，展示进度摘要。

### 读取基础目录

检查 `.allforai/demo-forge/` 目录：
- **不存在** → 输出「尚未开始演示锻造。运行 `/demo-forge` 开始。」，终止。
- **存在** → 继续探测产物。

### 产物探测

逐一检查以下文件是否存在，并提取关键指标：

| 产物文件 | 对应阶段 | 提取指标 |
|---------|---------|---------|
| `model-mapping.json` | Design | 存在即完成 |
| `demo-plan.json` | Design | `entities` 数量、`roles` 数量、含 `media_fields` 的字段数量 |
| `style-profile.json` | Design | 存在即完成 |
| `assets-manifest.json` | Media | `verified_count` / `total_count` |
| `upload-mapping.json` | Media | 含 `external_url` 的条目数量 |
| `forge-data-draft.json` | Execute | 顶层各 key 下记录总数 |
| `forge-data.json` | Execute | 顶层各 key 下记录总数 |
| `verify-report.json` | Verify | `pass_rate` |
| `verify-issues.json` | Verify | 按 `route` 分组的 issue 数量 |
| `round-history.json` | Orchestrator | `rounds` 数组长度、`final_status` |

所有文件路径前缀为 `.allforai/demo-forge/`。

### 阶段状态判定

**Design 阶段**：
- `demo-plan.json` 存在 → "完成"
- 否则 → "未开始"

**Media 阶段**：
- `assets-manifest.json` 不存在 → "未开始"
- 存在且 `verified_count == total_count` → "完成"
- 存在且 `verified_count < total_count` → "进行中"

**Execute 阶段**：
- `forge-data.json` 存在 → "完成"
- `forge-data-draft.json` 存在但 `forge-data.json` 不存在 → "进行中"
- 两者都不存在 → "未开始"

**Verify 阶段**：
- `verify-report.json` 存在 → "Round N 完成"（N 从 `round-history.json` 获取，无则为 0）
- 否则 → "未开始"

### 展示进度报告

```markdown
## Demo Forge 进度

| 阶段 | 状态 | 产出 |
|------|------|------|
| Design | {完成/未开始} | demo-plan.json ({N} 实体, {M} 角色, {K} 媒体字段) |
| Media | {完成/进行中/未开始} | {done}/{total} 素材已上传, 外链: {count} |
| Execute | {完成/进行中/未开始} | {N} 条记录已灌入, {M} 失败 |
| Verify | {Round N 完成/未开始} | 通过率: {rate}% |
```

**如果 `round-history.json` 存在，追加迭代历史**：

```markdown
### 迭代历史

| 轮次 | 通过率 | 修复项 |
|------|--------|--------|
| Round 0 | 82.6% | - |
| Round 1 | 97.7% | VI-001, VI-002, VI-003 |
```

从 `round-history.json` 的 `rounds` 数组读取每轮的 `pass_rate` 和 `fixed_issues`。

**当前状态汇总**：

```markdown
### 当前状态

- 当前轮次: Round {N}
- 未解决问题: {count} ({按 route 分组明细})
- Dev 任务已生成: {count}
- 最终状态: {passed/in_progress/not_started}
```

- `当前轮次`：从 `round-history.json` 的 `rounds` 长度推断；无历史则为 "Round 0"。
- `未解决问题`：从 `verify-issues.json` 读取，按 `route` 分组统计。
- `Dev 任务已生成`：统计 `verify-issues.json` 中含 `fix_task` 的条目数量。
- `最终状态`：从 `round-history.json` 的 `final_status` 读取；无文件则根据阶段推断。

**如果 `demo-plan.json` 含 `credentials`，追加登录信息**：

```markdown
### 登录信息

| 角色 | 账号 | 密码 |
|------|------|------|
| admin | admin@example.com | demo-pass-123 |
| user | user@example.com | demo-pass-456 |
```

从 `demo-plan.json` 的 `credentials` 数组读取 `role`、`username`（或 `email`）、`password`。

### 容错处理

- 任何文件读取失败（不存在、格式错误）→ 该阶段标记为"未开始"，不抛错。
- JSON 解析失败 → 提示「{文件名} 格式异常，请检查」，继续处理其余文件。
- 缺少预期字段 → 用 "-" 或 0 填充，不中断。

### 下一步建议

根据当前阶段状态给出建议：

- {Design 未完成} → 运行 `/demo-forge` 开始演示锻造流程。
- {Media 未完成} → 运行 `/demo-forge` 继续（会自动检测到现有进度并从 Media 阶段续作）。
- {Execute 未完成} → 运行 `/demo-forge` 继续灌入数据。
- {Verify 未通过} → 运行 `/demo-forge` 继续迭代修复（当前 Round {N}，通过率 {rate}%）。
- {全部通过} → 演示数据锻造完成！可交付验收或运行 `/product-verify` 做端到端验证。
