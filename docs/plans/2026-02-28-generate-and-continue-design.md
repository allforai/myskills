# "生成即继续" 改造设计

> 日期: 2026-02-28
> 范围: dev-forge-skill — Phase 1 (project-setup) + Phase 2 (design-to-spec)

## 问题

Phase 1 和 Phase 2 采用"每步确认"模式，每生成一份文档都停下来等用户审阅。在 preflight 已收集偏好后，Phase 1 仍有 5 个交互点，Phase 2 有 5 个交互点。用户希望中间不停。

## 改造目标

将逐步确认改为**生成即继续 + 阶段末汇总确认**：中间步骤连续执行不停，阶段结束时展示汇总摘要，用户一次确认。

---

## 改造一：Phase 1 (project-setup) — 合并确认

### 改前（5 个交互点）

```
Step 0: AskUserQuestion 确认模式              ← IP-1
Step 1: AskUserQuestion 确认子项目列表        ← IP-2
Step 3: AskUserQuestion 确认模块分配          ← IP-3
Step 4: AskUserQuestion 确认端口和配置        ← IP-4
Step 5: AskUserQuestion 用户最终确认          ← IP-5
```

### 改后（1 个交互点）

```
Step 0: 模式识别
  → 若从 project-forge 调用 → 模式已由参数决定，跳过 AskUserQuestion
  → 若单独 /project-setup → 保持 AskUserQuestion（兼容模式）
Step 1: 子项目拆分（生成即继续，不停）
Step 2: 技术栈选择（preflight 已覆盖，直接读取）
Step 3: 模块分配（智能推荐，生成即继续，不停）
Step 4: 基础配置（端口自动分配，auth 已 preflight，生成即继续）
Step 5: 生成 manifest → 展示完整汇总 → AskUserQuestion 一次确认/调整  ← 唯一交互点
```

### 具体改动

**Step 0** (line 100): 添加 forge 调用检测
```
  → 若从 project-forge 编排调用（forge-decisions.json 存在）→ 模式已确定，跳过 AskUserQuestion
  → 若单独 /project-setup → 保持 AskUserQuestion 确认模式
```

**Step 1** (line 110): 删除子项目列表确认
```
  改前: AskUserQuestion: 确认/调整子项目列表
  改后: → 生成子项目列表（不停，汇总到 Step 5）
```

**Step 3** (line 129): 删除模块分配确认
```
  改前: AskUserQuestion: 确认/调整每个子项目的模块分配
  改后: → 按智能推荐分配（不停，汇总到 Step 5）
```

**Step 4** (line 136): 删除端口确认
```
  改前: AskUserQuestion: 确认端口和配置
  改后: → 自动分配端口（不停，汇总到 Step 5）
```

**Step 5** (line 138-140): 改为完整汇总确认
```
  改前: 写入 manifest → AskUserQuestion: 用户最终确认
  改后: 写入 manifest → 展示完整汇总表:

  ## Project Manifest 汇总

  | 子项目 | 类型 | 技术栈 | 模块 | 端口 |
  |--------|------|--------|------|------|
  | api-backend | backend | Go+Gin | M001,M002,M003 | 8080 |
  | merchant-admin | admin | Next.js | M001,M003 | 3000 |
  | ... | ... | ... | ... | ... |

  | 配置项 | 值 |
  |--------|---|
  | Monorepo | manual |
  | Auth | JWT |

  模块覆盖率: 100% (全部已分配)

  AskUserQuestion:
    - "确认" → 继续 Phase 2
    - "调整" → 逐项修改（展示各项选项），修改后重新生成 manifest
```

### 向后兼容

- 单独 `/project-setup`（无 forge-decisions.json）→ Step 0 的模式确认保留
- 但 Step 1/3/4 的中间确认无论何种模式都取消，统一到 Step 5

### 铁律 #2 更新

```
改前: ### 2. 每步确认，不跳步（preflight 除外）
改后: ### 2. 阶段末汇总确认（preflight 偏好 + 中间步骤均不单独确认）
```

### 效果

Phase 1 交互: 5 → 1（仅 Step 5 汇总确认）
（单独 /project-setup 时: 5 → 2，多一个 Step 0 模式确认）

---

## 改造二：Phase 2 (design-to-spec) — 生成即继续

### 改前（5 个交互点）

```
Step 0: AskUserQuestion 未覆盖模块解决       ← IP-1（条件触发）
Step 1: 展示 requirements.md 摘要 → 确认     ← IP-2（逐子项目）
Step 2: 展示 design.md 摘要 → 确认           ← IP-3（逐子项目）
Step 3: 展示 tasks.md 摘要 → 确认            ← IP-4（逐子项目）
Step 4: 展示依赖图 → 确认                    ← IP-5
```

### 改后（2 个交互点）

```
Step 0: AskUserQuestion 未覆盖模块解决       ← 保留（条件触发，需用户决策）
Step 1: 生成 requirements.md（不停）
Step 2: 生成 design.md（不停）
Step 3: 生成 tasks.md（不停）
Step 4: 跨子项目依赖分析（不停）
Step 5: 【新增】阶段末汇总确认              ← 唯一必须交互点
```

### 具体改动

**Step 1** (line 219): 删除逐子项目确认
```
  改前: → 写入 requirements.md → 展示摘要 → 用户确认
  改后: → 写入 requirements.md → 输出进度: 「{name}/requirements.md ✓ ({N} 需求项)」
```

**Step 2** (line 255-256): 删除逐子项目确认
```
  改前: → 写入 design.md → 展示摘要 → 用户确认
  改后: → 写入 design.md → 输出进度: 「{name}/design.md ✓ ({N} API端点, {M} 页面)」
```

**Step 3** (line 271-272): 删除逐子项目确认
```
  改前: → 写入 tasks.md → 展示摘要 → 用户确认
  改后: → 写入 tasks.md → 输出进度: 「{name}/tasks.md ✓ ({N} 任务, B0-B5)」
```

**Step 4** (line 280-281): 删除依赖图确认
```
  改前: → 更新 manifest → 展示依赖图 → 用户确认
  改后: → 更新 manifest → 输出进度: 「跨项目依赖图 ✓ ({N} 条依赖)」
```

**新增 Step 5**: 阶段末汇总确认
```
Step 5: 阶段末汇总
  展示全部生成结果摘要:

  ## Design-to-Spec 汇总

  | 子项目 | requirements | design | tasks |
  |--------|-------------|--------|-------|
  | api-backend | 12 需求项 | 8 API端点, 5 实体 | 24 任务 (B0-B5) |
  | merchant-admin | 8 需求项 | 6 页面, 12 组件 | 18 任务 (B1,B3-B5) |
  | ... | ... | ... | ... |

  跨项目依赖: {N} 条
  执行顺序: B0 → B1(并行) → B2 → B3(并行) → B4 → B5
  总任务数: CORE {N} + DEFER {M}

  AskUserQuestion:
    - "确认，继续" → 进入 Phase 2.5
    - "需要调整" → 指定要修改的子项目和文档，重新生成该部分
```

### 铁律更新

design-to-spec.md 无对应铁律需更新（其铁律关注的是 CORE/DEFER、两阶段加载、原子性等，不涉及确认流程）。

### 效果

Phase 2 交互: 5 → 2（Step 0 条件触发 + Step 5 汇总确认）

---

## 总效果

| 阶段 | 改前 | 改后 | 变化 |
|------|------|------|------|
| Phase 0 | 2 | 2 | — |
| Phase 1 | 5 | 1 | -4 |
| Phase 2 | 5 | 2 | -3 |
| 其他 | 21 | 21 | — |
| **合计** | **33** | **26** | **-7** |

## 改造文件清单

| 文件 | 改动 |
|------|------|
| `skills/project-setup.md` | Step 0 forge 检测、Step 1/3/4 删中间确认、Step 5 改为汇总确认、铁律 #2 更新、版本 1.1.0 → 1.2.0 |
| `skills/design-to-spec.md` | Step 1-4 删逐文档确认、新增 Step 5 汇总确认、版本 1.1.0 → 1.2.0 |
