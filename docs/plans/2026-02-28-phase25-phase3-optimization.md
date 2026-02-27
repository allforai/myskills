# Phase 2.5 + Phase 3 交互优化设计

> 日期: 2026-02-28
> 范围: dev-forge-skill — seed-forge (Phase 2.5) + project-scaffold (Phase 3) + project-forge 编排

## 问题

Phase 2.5 有 4 个交互点（seed-forge Steps 0-2 逐步确认 + 编排层 AskUserQuestion），Phase 3 有 2 个交互点（脚手架文件清单确认 + 启动验证等待用户）。总计 6 个交互点可优化。

## 核心模式

沿用已验证的两个模式：
- **生成即继续**：中间步骤连续执行不停，阶段末汇总确认
- **自动验证 + 条件交互**：能自动验证的自动做，仅失败时交互

---

## 改造一：seed-forge — 生成即继续（plan 模式）

### 改前（4 个交互点）

```
project-forge Phase 2.5:
  → AskUserQuestion: 已完成 seed-forge plan / 跳过 / 需要帮助     ← IP-1

seed-forge plan 模式:
  Step 0: 数据模型映射 → 用户确认映射                               ← IP-2
  Step 1: 种子方案设计 → 用户确认方案                               ← IP-3
  Step 2: 行业风格设定 → 用户确认风格                               ← IP-4
```

### 改后（1 个交互点）

```
project-forge Phase 2.5:
  → 自动调用 seed-forge plan（不停，不再"提示用户执行"）

seed-forge plan 模式:
  Step 0: 数据模型映射（不停）
    → 输出进度: 「Step 0 模型映射 ✓ {N} 实体, {M} API缺口」
  Step 1: 种子方案设计（不停）
    → 输出进度: 「Step 1 种子方案 ✓ {N} 账号, {M} 实体, {K} 场景链路」
  Step 2: 行业风格设定（不停）
    → 输出进度: 「Step 2 风格模板 ✓ {industry} 风格, {N} 文本模板」
  ↓
  Plan 汇总确认（单次交互）:                                        ← 唯一交互点
    ## Seed Plan 汇总

    | 项目 | 详情 |
    |------|------|
    | 实体映射 | {N} 实体已映射, {M} API缺口 |
    | 用户账号 | {N} 个（按角色: {breakdown}） |
    | 数据量 | 高频 {N} 条, 中频 {M} 条, 低频 {K} 条 |
    | 场景链路 | {N} 条完整链路 |
    | 枚举覆盖 | {N}/{M} 状态值已覆盖 |
    | 时间跨度 | {N} 天 |
    | 行业风格 | {industry} |
    | 文本模板 | {N} 类, {M} 个变体 |

    → AskUserQuestion: 确认 / 调整
```

### Forge 调用检测

seed-forge.md 添加 forge 检测（与 project-setup 模式相同）：

```
前置检查:
  若 .allforai/project-forge/forge-decisions.json 存在
    → Forge 编排模式: Steps 0-2 生成即继续，plan 结束时单次汇总确认
  若不存在
    → 独立模式: 保持原有逐步确认行为
```

### 向后兼容

- 单独 `/seed-forge plan`（无 forge-decisions.json）→ 保持原有 3 次逐步确认
- `/seed-forge full`/`fill`/`clean` → 不受影响（这些模式不在 Phase 2.5 范围内）

---

## 改造二：project-scaffold — 自动验证

### 改前（2 个交互点）

```
Step 1: 展示文件清单 → AskUserQuestion 确认                         ← IP-1
Step 6: 提示用户安装依赖+启动 → 等待用户确认结果                      ← IP-2
```

### 改后（0-1 个交互点）

```
Step 1: 生成文件清单（不停）
  → 输出进度: 「Step 1 脚手架规划 ✓ {N} 文件 ({breakdown by sub-project})」
Steps 2-5: 生成文件（不停，逐步输出进度）
  → 「Step 2 Monorepo 根 ✓ {N} 文件」
  → 「Step 3 子项目骨架 ✓ {N} 文件 × {M} 子项目」
  → 「Step 4 Mock 后端 ✓ {N} 文件, {M} 端点」
  → 「Step 5 E2E 骨架 ✓」
Step 6: 自动启动验证
  Bash: pnpm install（自动执行）
  Bash: pnpm mock &（自动启动 mock-server）
  Bash: curl -s -o /dev/null -w "%{http_code}" http://localhost:4000/health
  全部通过 → 输出: 「Step 6 启动验证 ✓ 依赖安装成功, mock-server 可达」→ 继续（不停）
  失败 → AskUserQuestion: 手动排查后重试 / 跳过验证                  ← 条件触发
```

### Forge 调用检测

project-scaffold.md 同样添加 forge 检测：

```
前置检查:
  若 .allforai/project-forge/forge-decisions.json 存在
    → Forge 编排模式: Step 1 不确认, Step 6 自动验证
  若不存在
    → 独立模式: 保持 Step 1 确认 + Step 6 手动验证
```

### 铁律 #5 更新

```
改前: Step 6 必须提示用户安装依赖并启动 mock-server 验证。不可跳过。
改后: Step 6 启动验证是必须的。Forge 编排模式下自动执行验证（pnpm install + mock 启动 + health check），仅失败时交互。独立模式下仍提示用户手动验证。
```

---

## 改造三：project-forge 编排层

### Phase 2.5 改动

```
改前:
  提示用户执行: /seed-forge plan
  AskUserQuestion: 已完成 / 跳过 / 需要帮助

改后:
  自动调用 seed-forge plan（直接 Read 加载 skill，按 plan 模式执行）
  seed-forge plan 内部完成后（含汇总确认）→ 验证 seed-plan.json 存在 → 继续
  用户在汇总确认时选择"跳过" → 记录决策，mock-server 使用最小占位数据
```

### Phase 3 质量门禁改动

```
改前:
  | 依赖安装 | 用户确认 pnpm install 成功 |
  | mock 启动 | 用户确认 mock-server 可访问 |

改后:
  | 依赖安装 | 自动执行 pnpm install，检查退出码 |
  | mock 启动 | 自动启动 mock-server，curl health check 返回 2xx |
```

---

## 效果

| 阶段 | 改前 | 改后 | 变化 |
|------|------|------|------|
| Phase 2.5 (seed-forge) | 4 | 1 | -3 |
| Phase 3 (scaffold) | 2 | 0-1 | -1~2 |
| **小计** | **6** | **1-2** | **-4~5** |

## 全流程交互点

| 阶段 | 之前优化后 | 本次优化后 |
|------|-----------|-----------|
| Phase 0 | 2 | 2 |
| Phase 1 | 1 | 1 |
| Phase 2 | 2 | 2 |
| Phase 2.5 | 4 | 1 |
| Phase 3 | 2 | 0-1 |
| Phase 4 | 0 | 0 |
| Phase 4.5 | 4 | 4 |
| Phase 5 | 4 | 4 |
| **合计** | **19** | **14-15** |

## 改造文件清单

| 文件 | 改动 |
|------|------|
| `skills/seed-forge.md` | 工作流添加 forge 检测，Steps 0-2 改为生成即继续，新增 plan 汇总确认，版本 2.4.0 → 2.5.0 |
| `skills/project-scaffold.md` | 工作流添加 forge 检测，Step 1 删文件清单确认，Step 6 改为自动验证，铁律 #5 更新，版本 1.0.1 → 1.1.0 |
| `commands/project-forge.md` | Phase 2.5 改为自动调用，Phase 3 质量门禁改为自动验证 |
