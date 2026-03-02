# 设计文档：product-design Phase 4-7 并行优化

> 日期：2026-03-02

## 背景

product-design 的 8 阶段流水线当前完全串行执行（Phase 1→2→3→4→5→6→7→8）。但源码分析证实 Phase 4 (use-case)、Phase 5 (feature-gap)、Phase 6 (feature-prune)、Phase 7 (ui-design) 之间无数据依赖，可以并行执行。

## 决策记录

- 优化范围：仅 product-design 内部并行，跨层（full-pipeline Layer 1-4）保持串行
- 并行方案：Phase 4-7 四路全并行（方案 A），非保守两组并行
- 竞态处理：分片写 + 聚合（pipeline-decisions-{skill}.json → 合并）
- 改动范围：仅 `product-design-skill/commands/product-design.md`，各 skill 文件零修改

## 数据依赖分析

实际依赖图（经源码验证）：

```
Phase 1: concept
    ↓
Phase 2: product-map (需要 concept)
    ↓
Phase 3: screen-map (需要 product-map)
    ↓
    ├── Phase 4: use-case      (需要 product-map + screen-map)
    ├── Phase 5: feature-gap   (需要 product-map + screen-map)
    ├── Phase 6: feature-prune (需要 product-map + screen-map)
    └── Phase 7: ui-design     (需要 product-map + screen-map + optional concept)
         ↓
Phase 8: design-audit (需要全部上游，use-case/gap/prune 为可选)
```

关键发现：
- feature-gap **不依赖** use-case（当前编排假设串行是不必要的）
- feature-prune **不依赖** feature-gap（只需 product-map + screen-map）
- ui-design **不依赖** gap/prune（只需 product-map + screen-map）
- 4 个 skill 的输出目录完全隔离，无文件冲突

## 改动清单

### 1. 修改 `product-design-skill/commands/product-design.md`

#### 1.1 Phase 4-7 执行方式

**当前**：
```
Phase 3 → checkpoint → Phase 4 → checkpoint → Phase 5 → checkpoint → Phase 6 → checkpoint → Phase 7 → checkpoint → Phase 8
```

**改后**：
```
Phase 3 → checkpoint →
    ┌─ Agent(use-case)
    ├─ Agent(feature-gap)
    ├─ Agent(feature-prune)
    └─ Agent(ui-design)
    全部完成 → 聚合 checkpoint → Phase 8
```

编排器在 Phase 3 checkpoint 通过后，用**单条消息发出 4 个 Agent tool 调用**并行执行。Agent tool 的屏障同步机制保证全部完成后才继续。

#### 1.2 每个 Agent 的 prompt 结构

```
Agent prompt 模板:
  1. 用 Read 工具加载 ${CLAUDE_PLUGIN_ROOT}/skills/{skill-name}.md
  2. 按 skill 工作流完整执行
  3. 产出写入 .allforai/{skill-name}/ 目录
  4. 自动模式: 携带 __orchestrator_auto: true 上下文标记
  5. pipeline-decisions: 写入 .allforai/pipeline-decisions-{skill-name}.json（分片，不写共享文件）
```

#### 1.3 pipeline-decisions 分片写入

并行阶段，每个 Agent 写各自的临时文件：

```
Agent(use-case)      → .allforai/pipeline-decisions-use-case.json
Agent(feature-gap)   → .allforai/pipeline-decisions-feature-gap.json
Agent(feature-prune) → .allforai/pipeline-decisions-feature-prune.json
Agent(ui-design)     → .allforai/pipeline-decisions-ui-design.json
```

聚合阶段（Phase 8 前）编排器：
1. 读取 4 个临时文件
2. 按 `phase` 字段去重合并到 `pipeline-decisions.json`
3. 删除 4 个临时文件

#### 1.4 聚合 checkpoint

4 个 Agent 全部返回后，编排器执行聚合 checkpoint：

**产出检查**：
| 产出 | 检查 |
|------|------|
| `.allforai/use-case/use-case-tree.json` | 存在 |
| `.allforai/feature-gap/gap-tasks.json` | 存在 |
| `.allforai/feature-prune/prune-decisions.json` | 存在 |
| `.allforai/ui-design/ui-design-spec.md` | 存在 |

**轻量校验**（原分散在各 checkpoint 中，现统一到聚合阶段）：
- 每个 task 至少有 1 条用例（use-case 校验）
- gap×prune 矛盾检测：feature-gap 报缺口的 task 被 feature-prune 标 CUT
- CORE 任务在 UI 设计中有体现（ui-design 校验）

**pipeline-decisions 合并**：读取 4 个分片文件 → 合并 → 写入 → 清理

#### 1.5 错误处理

```
4 个 Agent 返回:
  全部成功 → 聚合 checkpoint → Phase 8
  部分失败 →
    成功的: 正常收集产出
    失败的: 记录错误信息
    向用户报告:
      - 哪些 skill 成功
      - 哪些 skill 失败 + 错误原因
    询问用户:
      - 重试失败的 skill（仅重跑失败的）
      - 跳过继续到 Phase 8（design-audit 对这些依赖标注为可选）
      - 中止流程
```

自动模式下的 ERROR：Agent 内部停下并返回失败结果，不影响其他 3 个 Agent。编排器按上述逻辑处理。

### 2. 不改动的文件

以下文件不做任何修改：
- `skills/use-case.md` — 内部逻辑不变
- `skills/feature-gap.md` — 内部逻辑不变
- `skills/feature-prune.md` — 内部逻辑不变
- `skills/ui-design.md` — 内部逻辑不变
- `skills/design-audit.md` — 内部逻辑不变
- `commands/full-pipeline.md` — 跨层编排不变

## 性能预期

Phase 4-7 串行执行耗时 = T4 + T5 + T6 + T7
Phase 4-7 并行执行耗时 = max(T4, T5, T6, T7)

理论加速: 最高 4x（如果 4 个 skill 耗时相近）
实际加速: 预估 2-3x（受 API 并发限制和最慢 skill 瓶颈影响）

## 风险评估

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| Agent 并发超过平台限制 | 低 | 部分 Agent 排队 | 退化为部分并行，不影响正确性 |
| 某个 Agent 上下文不足 | 中 | 产出质量下降 | Agent prompt 中完整传递所需上下文 |
| pipeline-decisions 合并冲突 | 无 | — | 分片写保证无竞态 |
| 聚合 checkpoint 发现矛盾多 | 低 | 需要用户处理 | 与串行时 design-audit 终审兜底一致 |
