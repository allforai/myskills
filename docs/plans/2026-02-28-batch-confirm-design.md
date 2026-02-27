# Phase 4.5 批量确认改造设计

> 日期: 2026-02-28
> 范围: dev-forge-skill — product-verify + e2e-verify + project-forge Phase 4.5

## 问题

Phase 4.5 有 11 个交互点，其中最密集的是 product-verify 的逐步确认（S1-S4, D0-D4）和失败逐条分类。铁律明确"不允许自动归类"，但逐条交互严重打断流程。

## 核心原则

**不违反铁律精神**：用户仍确认每一条分类，但改为"自动建议 + 批量确认"替代"逐条交互"。用户在一张汇总表里看到所有自动建议，一次确认或逐条调整。

---

## 改造一：product-verify — 静态阶段 (S1-S4)

### 改前（4 个交互点）

```
S1 → 用户确认
S2 → 用户确认（或跳过）
S3 → 用户确认
S4 → 逐条确认 EXTRA 去留
```

### 改后（1 个交互点）

```
S1 → 输出进度: 「S1 Task→API ✓ covered:{N} missing:{M} partial:{K}」
S2 → 输出进度: 「S2 Screen→组件 ✓ covered:{N} missing:{M}」（或 WARNING 跳过）
S3 → 输出进度: 「S3 约束→代码 ✓ covered:{N} missing:{M}」
S4 → 输出进度: 「S4 Extra ✓ {N} 端点不在产品地图中」
↓
静态汇总确认:
  展示覆盖率表 + EXTRA 建议表

  | 检查项 | 已覆盖 | 缺失 | 部分 |
  |--------|--------|------|------|
  | S1 Task→API | 12 | 3 | 1 |
  | S2 Screen→组件 | 8 | 2 | — |
  | S3 约束→代码 | 15 | 4 | — |

  IMPLEMENT 候选: {N} 项（按频次排序）
  EXTRA 端点（自动建议）:
  | 端点 | 建议 | 理由 |
  |------|------|------|
  | /api/legacy/export | ignore | 无匹配任务，可能历史遗留 |
  | /api/internal/sync | ignore | 内部同步，不面向用户 |

  → AskUserQuestion: 确认全部 / 调整 EXTRA 决策
```

### EXTRA 自动建议规则

基础设施端点已在 S4 排除列表中自动跳过（health/auth/docs/static/framework）。
剩余 EXTRA 端点默认建议 `ignore`，用户批量确认时可改为 `add_to_map` 或 `mark_remove`。

---

## 改造二：product-verify — 动态阶段 (D0-D4)

### 改前（5 个交互点）

```
D0 → 询问 URL / 等待启动
D1 → 展示测试计划，确认
D2 → 执行正常流，确认
D3 → 执行 E2E 流，确认
D4 → 逐条失败分类
```

### 改后（1-2 个交互点）

```
D0 → 自动检测 URL
     可达 → 继续（不停）
     不可达 → AskUserQuestion: 启动后重试 / 跳过 dynamic     ← 条件触发（保留）
D1 → 自动推导测试序列（不停）
D2 → 执行正常流（不停，输出进度）
D3 → 执行 E2E 流（不停，输出进度）
D4 → 自动分类 + 批量确认                                    ← 唯一必须交互点
```

### 失败自动分类规则

| 错误特征 | 自动建议 | 理由 |
|---------|---------|------|
| HTTP 5xx 响应 | FIX_FAILING | 服务端错误 = 代码缺陷 |
| 404 on expected route | FIX_FAILING | 路由未实现 |
| 元素未找到 / 断言失败 | FIX_FAILING | 页面实现不完整 |
| Connection refused / timeout | ENV_ISSUE | 服务未启动或网络问题 |
| Database error in response | ENV_ISSUE | 数据库未初始化 |
| Auth redirect (unexpected) | FIX_FAILING | 权限配置错误 |
| CORS error | ENV_ISSUE | 开发环境跨域配置 |

### 批量确认展示格式

```
## 动态验收结果

通过: {N}/{M} 用例

失败项（自动建议分类）:
| 用例 | 失败步骤 | 错误 | 建议分类 | 理由 |
|------|---------|------|---------|------|
| UC001 创建订单 | Step 3 | 500 Internal Error | FIX_FAILING | HTTP 5xx |
| UC005 导出报表 | Step 1 | Connection refused | ENV_ISSUE | 连接拒绝 |
| UC008 批量删除 | Step 2 | Element not found | FIX_FAILING | 元素缺失 |

→ AskUserQuestion: 确认全部分类 / 逐条调整
```

---

## 改造三：e2e-verify

### 改前（3 个交互点）

```
Step 0 → 不可达处理 (条件)
Step 1 → 场景列表确认
Step 3 → 逐条失败分类
```

### 改后（1-2 个交互点）

```
Step 0 → 自动检测，不可达时 AskUserQuestion          ← 条件触发（保留）
Step 1 → 自动推导场景（不停）
         → 输出进度: 「E2E 场景 ✓ 正向 {N} + 负向 {M}」
Step 2 → 执行（不停，逐场景输出进度）
Step 3 → 自动分类 + 批量确认                         ← 唯一必须交互点（同 product-verify D4 规则）
Step 4 → 报告（不停）
```

### 铁律调整

e2e-verify 铁律 #2「用户确认场景列表」→ 改为「场景列表包含在批量确认中」。
场景推导完成后直接执行，执行结果 + 场景列表 + 失败分类在 Step 3 的批量确认表中一并展示。

---

## 改造四：project-forge Phase 4.5 编排

### 改前（2 个交互点）

```
Step 4: AskUserQuestion 确认修复任务列表
Step 6: 回归失败 → AskUserQuestion 再次修复 / 接受
```

### 改后（1 个交互点）

```
Step 4: 自动生成修复任务列表
        → 输出: 「修复任务 ✓ IMPLEMENT:{N} FIX_FAILING:{M}」
        → 直接执行（不停）
Step 6: 回归失败
        → 仍有失败 → AskUserQuestion: 再次修复 / 记录已知问题    ← 保留（需决策）
        → 全部通过 → 继续（不停）
```

修复任务列表不再单独确认（来源是已经用户批量确认过的验证结果，无需二次确认）。

---

## 铁律调整汇总

### product-verify 铁律变更

```
改前 #4: 用户确认 EXTRA 归属 — EXTRA 代码由用户逐条决定
改后 #4: 用户确认 EXTRA 归属 — EXTRA 代码在静态汇总中批量展示（含自动建议），用户一次确认或逐条调整

改前 #5: 动态失败需用户确认分类 — 必须逐条由用户确认后才写入 FIX_FAILING；不允许自动归类
改后 #5: 动态失败需用户确认分类 — 基于错误特征自动建议分类，在动态汇总中批量展示，用户一次确认或逐条调整；自动建议不等于自动归类，用户仍是最终决策者
```

### e2e-verify 铁律变更

```
改前 #2: 用户确认场景列表 — 必须经用户确认后才执行
改后 #2: 场景列表可追溯 — 场景从 business-flows 推导，执行后与结果一并展示，用户在批量确认时可审阅场景

改前 #3: 失败分类需用户确认 — 必须逐条由用户确认分类，不允许自动归类
改后 #3: 失败分类需用户确认 — 基于错误特征自动建议分类，批量展示，用户一次确认或逐条调整
```

---

## 效果

| 阶段 | 改前 | 改后 | 变化 |
|------|------|------|------|
| product-verify 静态 | 4 | 1 | -3 |
| product-verify 动态 | 5 | 1-2 | -3~4 |
| e2e-verify | 3 | 1-2 | -1~2 |
| Phase 4.5 编排 | 2 | 1 | -1 |
| **Phase 4.5 合计** | **11** | **3-5** | **-6~8** |

## 全流程交互点

| 阶段 | 改前 | 改后 |
|------|------|------|
| Phase 0 | 2 | 2 |
| Phase 1 | 1 | 1 |
| Phase 2 | 2 | 2 |
| Phase 2.5 | 4 | 4 |
| Phase 3 | 2 | 2 |
| Phase 4 | 0 | 0 |
| Phase 4.5 | 11 | 4 |
| Phase 5 | 4 | 4 |
| **合计** | **26** | **19** |

## 改造文件清单

| 文件 | 改动 |
|------|------|
| `skills/product-verify.md` | S1-S3 删逐步确认，S4 改批量建议，D1-D3 删逐步确认，D4 改自动建议+批量确认，铁律 #4/#5 更新，版本 → 1.3.0 |
| `skills/e2e-verify.md` | Step 1 删场景确认，Step 3 改自动建议+批量确认，铁律 #2/#3 更新，版本 → 1.2.0 |
| `commands/project-forge.md` | Phase 4.5 Step 4 删修复任务确认 |
