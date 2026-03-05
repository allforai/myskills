---
description: "查看代码复刻分析进度：哪些阶段已完成、哪些待续、产物文件状态。"
allowed-tools: ["Read", "Glob"]
---

# CR Status — 复刻进度查询

## 执行方式

读取当前项目的复刻状态，展示进度摘要。

### 读取配置

检查 `.allforai/code-replicate/replicate-config.json`：
- **不存在** → 输出「尚未开始代码复刻。运行 `/code-replicate` 开始。」，终止。
- **存在** → 读取配置，继续。

### 检查产物文件

逐一检查以下文件是否存在：

| 产物文件 | 对应阶段 |
|---------|---------|
| `.allforai/code-replicate/source-analysis.json` | Phase 2 完成 |
| `.allforai/code-replicate/api-contracts.json` | Phase 4 完成（interface+） |
| `.allforai/code-replicate/behavior-specs.json` | Phase 4 完成（functional+） |
| `.allforai/code-replicate/arch-map.json` | Phase 4 完成（architecture+） |
| `.allforai/code-replicate/bug-registry.json` | Phase 4 完成（exact） |
| `.allforai/code-replicate/stack-mapping-decisions.json` | Phase 5 完成 |
| `.allforai/product-map/task-inventory.json` | Phase 6 完成 |
| `.allforai/code-replicate/replicate-report.md` | Phase 7 完成 |

**fullstack 模式额外检查**（`project_type = fullstack` 时）：

| 产物文件 | 对应阶段 |
|---------|---------|
| `.allforai/code-replicate/backend/source-analysis.json` | Phase 2 后端完成 |
| `.allforai/code-replicate/frontend/source-analysis.json` | Phase 2 前端完成 |
| `.allforai/code-replicate/infrastructure.json` | Phase 2 基础设施完成 |
| `.allforai/code-replicate/backend/api-contracts.json` | Phase 4 后端完成 |
| `.allforai/code-replicate/frontend/api-contracts.json` | Phase 4 前端完成 |
| `.allforai/code-replicate/api-bindings.json` | Phase 4 交叉验证完成 |
| `.allforai/code-replicate/schema-alignment.json` | Phase 4 交叉验证完成 |
| `.allforai/code-replicate/constraint-reconciliation.json` | Phase 4 交叉验证完成 |
| `.allforai/code-replicate/auth-propagation.json` | Phase 4 交叉验证完成 |
| `.allforai/code-replicate/error-mapping.json` | Phase 4 交叉验证完成 |
| `.allforai/code-replicate/fullstack-report.md` | Phase 7 完成 |

**module 模式额外检查**（存在 `module-boundaries.json` 时）：

| 产物文件 | 对应阶段 |
|---------|---------|
| `.allforai/code-replicate/module-boundaries.json` | Phase 2 依赖边界扫描完成 |

### 展示进度报告

```markdown
## 代码复刻进度

**配置**：
- 项目类型: {project_type}
- 信度等级: {fidelity}
- 源码地址: {source_path 或 source_url}
- 复刻范围: {scope}（{scope_detail}）
- 目标技术栈: {target_stack 或 "待确认（Phase 3）"}
- 业务方向: {business_direction 或 "待确认（Phase 3）"}
- 分析粒度: {analysis_granularity 或 "待确认（Phase 3）"}
- 最后更新: {last_updated}

**进度**：

| Phase | 阶段 | 状态 | 产物 |
|-------|------|------|------|
| 1 | Preflight | ✅ 完成 | replicate-config.json |
| 2 | 源码解构 | ✅ / ⏳ / ❌ | source-analysis.json |
| 3 | 目标确认 | ✅ / ⏳ / ❌ | config 更新（scope_filter, target_stack, business_direction, expected_outputs） |
| 4 | 深度分析 | ✅ / ⏳ / ❌ | api-contracts.json 等 |
| 5 | 汇总确认 | ✅ / ⏳ / ❌ | stack-mapping-decisions.json |
| 6 | 生成产物 | ✅ / ⏳ / ❌ | task-inventory.json, business-flows.json 等 |
| 7 | 交接完成 | ✅ / ⏳ | replicate-report.md |

**fullstack 模式展示**（`project_type = fullstack`）：

在标准进度表后追加双栈进度：

| 子阶段 | 状态 | 产物 |
|--------|------|------|
| 2a 后端扫描 | ✅ / ⏳ / ❌ | backend/source-analysis.json |
| 2b 前端扫描 | ✅ / ⏳ / ❌ | frontend/source-analysis.json |
| 2c 基础设施 | ✅ / ⏳ / ❌ | infrastructure.json |
| 4a 后端分析 | ✅ / ⏳ / ❌ | backend/api-contracts.json 等 |
| 4b 前端分析 | ✅ / ⏳ / ❌ | frontend/api-contracts.json 等 |
| 4c 交叉验证 | ✅ / ⏳ / ❌ | api-bindings.json, schema-alignment.json 等 |

**下一步**：

{Phase 1-5 未完成} 运行 `/code-replicate` 继续（会自动检测到现有进度并询问断点续作）。

{Phase 6-7 未完成} 运行 `/code-replicate` 继续生成产物。

{全部完成} 运行 `/design-to-spec` 生成目标技术栈实现规格，然后 `/task-execute` 逐任务生成代码。
```
