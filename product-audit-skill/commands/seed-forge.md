---
description: "种子数据锻造：按 product-map 角色/频次/场景生成真实感种子数据。模式: full / plan / fill / clean"
argument-hint: "[mode: full|plan|fill|clean]"
allowed-tools: ["Read", "Write", "Grep", "Glob", "Bash", "Task", "AskUserQuestion", "WebSearch", "WebFetch"]
---

# Seed Forge — 种子数据锻造

用户请求: $ARGUMENTS

## 插件根目录

所有文档路径基于插件安装目录: `${CLAUDE_PLUGIN_ROOT}`

## 模式路由

- **无参数 或 `full`** → 完整流程：Step 0 → Step 1 → Step 2 → Step 3 → Step 4
- **`plan`** → 只设计方案：Step 0 → Step 1 → Step 2（不需要应用运行）
- **`fill`** → 加载已有方案：加载已有 seed-plan.json → Step 3 → Step 4
- **`clean`** → 清理种子数据：加载 forge-data.json → 二次确认 → 直接操作数据库删除

## 前置检查

执行前必须检查：

1. **两阶段加载（索引优先）**：
   - 检查 `.allforai/product-map/task-index.json`
     - 存在 → 加载索引（< 5KB），Step 1-B 数据量设计直接使用索引的 frequency 数据
     - 不存在 → 回退到全量加载
   - 检查 `.allforai/product-map/product-map.json`
   - 若 `product-map.json` 也不存在 → 输出「请先运行 /product-map 建立产品地图」，**立即终止**

2. **fill 模式额外检查**：检查 `.allforai/seed-forge/seed-plan.json`
   - 若不存在 → 输出「请先运行 /seed-forge plan 生成种子方案」，终止

3. **clean 模式额外检查**：检查 `.allforai/seed-forge/forge-data.json`
   - 若不存在 → 输出「没有可清理的数据，forge-data.json 不存在」，终止
   - 若存在 → **强制执行二次确认**：
     - 输出警告：「⚠️ 警告：即将删除所有种子数据，此操作不可逆。请输入 "确认清理" 继续，或输入其他内容取消。」
     - 等待用户输入，仅当用户输入完全匹配 "确认清理" 时才继续执行

## 执行流程

1. 参考已加载的 `skills/seed-forge.md` 中的目标定义和铁律
2. 从 `.allforai/product-map/product-map.json` 加载产品地图（角色、任务频次、场景链路、约束）
3. 按模式执行对应步骤
4. 数据量按帕累托分布：高频任务数据占总量 70%+，中频 20%，低频仅保证存在
5. **【强制】执行完毕后，必须在对话中直接输出完整的报告摘要**

## 详细文档（按需用 Read 工具加载）

- `${CLAUDE_PLUGIN_ROOT}/skills/seed-forge.md` — 完整工作流、Step 详述、铁律

## Step 执行要求

每个 Step 完成后：
1. 将结果写入 `.allforai/seed-forge/` 目录下对应的 JSON 文件（**输出目录保持 .allforai/seed-forge/，向后兼容**）
2. 向用户展示结果摘要
3. 等待用户确认后才进入下一个 Step

输出文件（均在 `.allforai/seed-forge/` 下）：
- `model-mapping.json`（Step 0，替代旧的 project-analysis.json）
- `api-gaps.json`（Step 0+4）
- `seed-plan.json`（Step 1，替代旧的 forge-plan.json）
- `style-profile.json`（Step 2，替代旧的 industry-profile.json）
- `assets-manifest.json`（Step 3）
- `forge-log.json`（Step 4）
- `forge-data.json`（Step 4，供 clean 使用）

**Breaking Change 说明**：文件名已更新（旧 `forge-plan.json` → 新 `seed-plan.json`），旧版 `demo-forge plan` 生成的方案文件不兼容新版 `seed-forge fill`，请重新执行 `plan`。

## 报告输出要求（强制执行）

执行完成后，必须在对话中直接输出以下报告摘要：

```
## 种子数据锻造报告摘要

> 执行时间: {时间}
> 执行模式: {full/plan/fill/clean}

### 总览

| 维度 | 结果 |
|------|------|
| 角色账号 | {角色1}: X 个，{角色2}: X 个，... |
| 总数据量 | X 条记录 |
| 场景链路 | X 条完整链路 |
| 约束违规 | X 处（已修正）|
| API 缺口 | X 个 |

### 数据量明细（按频次分层）

| 频次层 | 任务数 | 数据量 | 占比 |
|--------|--------|--------|------|
| 高频 | X | X 条 | ~70% |
| 中频 | X | X 条 | ~20% |
| 低频 | X | X 条 | ~10% |

### 约束违规记录

（逐条列出：约束名、违规描述、处理方式）

### 下一步

1. 启动应用并验证种子数据显示正确
2. 查看 API 缺口报告，补充缺失端点
3. 演示完成后运行 /seed-forge clean 清理数据

> 种子方案: `.allforai/seed-forge/seed-plan.json`
> 灌入日志: `.allforai/seed-forge/forge-log.json`
> 数据清单: `.allforai/seed-forge/forge-data.json`（含 ID，供 clean 使用）
> API 缺口: `.allforai/seed-forge/api-gaps.json`
```

---

## 铁律（强制执行）

> 完整定义见 `${CLAUDE_PLUGIN_ROOT}/skills/seed-forge.md` 的「6 条铁律」章节。

1. **频次决定数量，场景决定关联** — 高频任务数据多，按场景链路关联
2. **约束是硬规则** — constraints.json 中的约束必须在数据中体现
3. **优先 API，按需直写数据库** — 触发业务逻辑的走 API，配置表/历史数据/无 API 的实体走 DB 直写，清理统一走数据库
4. **图片必须真实，禁止占位符** — 所有图片字段用真实图片，找不到合适图片就减少记录数，不灌占位图
5. **竞品图片仅用于内部演示** — 不公开传播
6. **API 缺口如实报告** — 有任务无对应 API 时记录到 api-gaps.json，不替用户补代码
