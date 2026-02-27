---
description: "设计审计：跨层校验产品设计全链路一致性。逆向追溯 / 覆盖洪泛 / 横向一致性。模式: full / trace / coverage / cross / role"
argument-hint: "[mode: full|trace|coverage|cross|role] [角色名]"
allowed-tools: ["Read", "Write", "Grep", "Glob", "Bash", "Task", "AskUserQuestion", "WebSearch"]
---

# Design Audit — 设计审计

用户请求: $ARGUMENTS

## 插件根目录

所有文档路径基于插件安装目录: `${CLAUDE_PLUGIN_ROOT}`

## 模式路由

根据用户参数决定执行模式：

- **无参数 或 `full`** → 三合一全量校验：Step 1（逆向追溯）→ Step 2（覆盖洪泛）→ Step 3（横向一致性）→ Step 4（汇总报告）
- **`trace`** → 仅逆向追溯：Step 1 → Step 4
- **`coverage`** → 仅覆盖洪泛：Step 2 → Step 4
- **`cross`** → 仅横向一致性：Step 3 → Step 4
- **`role <角色名>`** → 指定角色全链路校验：同 full 完整流程，但仅分析属于指定角色的任务和产物

## 前置检查

执行前必须检查：

1. **两阶段加载（索引优先）**：
   - 检查三个索引文件：
     - `.allforai/product-map/task-index.json` → 任务索引
     - `.allforai/screen-map/screen-index.json` → 界面索引
     - `.allforai/product-map/flow-index.json` → 业务流索引
   - 任一索引存在 → 加载索引（< 5KB），按需决定是否加载完整数据
   - 所有索引不存在 → 回退到全量加载

2. **产物探测**：
   - `.allforai/product-map/` → **必须存在**（product-map.json 不存在 → 输出「请先运行 /product-map 建立产品地图」，**立即终止**）
   - `.allforai/screen-map/` → 必须（不存在则自动运行 screen-map 生成）
   - `.allforai/use-case/` → 可选
   - `.allforai/feature-gap/` → 可选
   - `.allforai/feature-prune/` → 可选
   - `.allforai/ui-design/` → 可选
   - 标记 `available_layers[]`，仅校验已有层

## 执行流程

1. 参考已加载的 `skills/design-audit.md` 中的工作流和铁律
2. 根据产物探测结果决定可执行的校验项
3. 根据模式按需执行对应步骤
4. 按工作流执行，**每个 Step 必须有用户确认环节**
5. **【强制】执行完毕后，必须在对话中直接输出完整的报告摘要**

## 详细文档（按需用 Read 工具加载）

- `${CLAUDE_PLUGIN_ROOT}/skills/design-audit.md` — 完整工作流、Step 详述、铁律

## Step 执行要求

每个 Step 完成后：
1. 将结果写入 `.allforai/design-audit/` 目录下对应的 JSON 文件
2. 向用户展示结果摘要
3. 等待用户确认后才进入下一个 Step

## 报告输出要求（强制执行）

执行完成后，必须在对话中直接输出以下报告摘要：

```
## 设计审计报告摘要

> 执行时间: {时间}
> 执行模式: {full/trace/coverage/cross/role}
> 可用层: {已探测到的层列表}

### 总览

| 维度 | 检查项 | 通过 | 问题 |
|------|--------|------|------|
| 逆向追溯 | X | X | X (ORPHAN) |
| 覆盖洪泛 | X | X | X (GAP)，覆盖率 XX% |
| 横向一致性 | X | X | X (CONFLICT/WARNING/BROKEN_REF) |

### 问题清单（按严重度排序）

（逐条列出：CONFLICT > ORPHAN > GAP > WARNING > BROKEN_REF）

### 下一步

1. 修复 CONFLICT：解决跨层矛盾
2. 修复 ORPHAN：为孤儿产物补充源头或清理
3. 补充 GAP：提升覆盖率
4. 检查 WARNING：评估是否需要调整

> 完整报告: `.allforai/design-audit/audit-report.md`
> 机器版: `.allforai/design-audit/audit-report.json`
```

---

## 铁律（强制执行）

> 完整定义见 `${CLAUDE_PLUGIN_ROOT}/skills/design-audit.md` 的「铁律」章节。

1. **只读不改** — 审计只报告问题，不修改任何上游产物
2. **已有产物决定校验范围** — 缺失的层自动跳过，不报错
3. **product-map 是锚点** — 所有追溯和洪泛以 product-map 为根
4. **按严重度排序** — CONFLICT > ORPHAN > GAP > WARNING > BROKEN_REF
5. **幂等** — 多次运行结果一致（无副作用、无决策缓存）
