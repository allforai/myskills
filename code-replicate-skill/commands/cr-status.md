---
description: "查看代码复刻分析进度：哪些步骤已完成、哪些待续、产物文件状态。"
allowed-tools: ["Read", "Glob"]
---

# CR Status — 复刻进度查询

## 执行方式

读取当前项目的复刻状态，展示进度摘要。

### Step 1：读取配置

检查 `.allforai/code-replicate/replicate-config.json`：
- **不存在** → 输出「尚未开始代码复刻。运行 `/code-replicate` 开始。」，终止。
- **存在** → 读取配置，继续。

### Step 2：检查产物文件

逐一检查以下文件是否存在：

| 产物文件 | 对应步骤 |
|---------|---------|
| `.allforai/code-replicate/source-analysis.json` | Step 1 完成 |
| `.allforai/code-replicate/api-contracts.json` | Step 2 完成（interface+） |
| `.allforai/code-replicate/behavior-specs.json` | Step 2 完成（functional+） |
| `.allforai/code-replicate/arch-map.json` | Step 2 完成（architecture+） |
| `.allforai/code-replicate/bug-registry.json` | Step 2 完成（exact） |
| `.allforai/code-replicate/stack-mapping-decisions.json` | Step 3 完成 |
| `.allforai/product-map/task-inventory.json` | Step 4 完成 |
| `.allforai/code-replicate/replicate-report.md` | Step 4 完成 |

### Step 3：展示进度报告

```markdown
## 代码复刻进度

**配置**：
- 信度等级: {fidelity}
- 源码路径: {source_path}
- 目标技术栈: {target_stack}
- 最后更新: {last_updated}

**步骤进度**：

| 步骤 | 状态 | 产物 |
|------|------|------|
| Step 0: Preflight | ✅ 完成 | replicate-config.json |
| Step 1: 源码解构 | ✅ / ⏳ / ❌ | source-analysis.json |
| Step 2: 专项分析 | ✅ / ⏳ / ❌ | api-contracts.json 等 |
| Step 3: 映射决策 | ✅ / ⏳ / ❌ | stack-mapping-decisions.json |
| Step 4: 生成产物 | ✅ / ⏳ / ❌ | task-inventory.json 等 |
| Step 5: 交接完成 | ✅ / ⏳ | replicate-report.md |

**下一步**：

{如果未完成} 运行 `/code-replicate` 继续（会自动检测到现有进度并询问断点续作）。

{如果已完成} 运行 `/design-to-spec` 生成目标技术栈实现规格。
```
