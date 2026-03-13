# FVL 三维验证架构

> Forge-Verify-Loop 的完整理论框架。跨 product-design 和 dev-forge 两个 pipeline 共用。
> 各 plugin 的 `skill-commons.md` 引用本文件，补充自身定制内容。

---

## 一、三维概览

```
              纵向 FVL        横向 FVL         内外循环
              (深度)          (广度)           (层级)
              ───────        ───────          ───────
作用          产物 ↔ 上游     兄弟 ↔ 兄弟      终点 ↔ 起点
问题          生成的对不对？   兄弟一致吗？      还在正确路上吗？
视野          一跳            同层              N 跳
时机          每个阶段        每个阶段          里程碑
防住什么      映射断裂         契约断裂          概念漂移
历史案例      字段名不匹配     49个端点缺失      5个MUST功能缺失
```

三个维度互补：
- **纵向**确保每一步忠于上一步
- **横向**确保同层兄弟不矛盾
- **内外循环**确保 N 步之后仍忠于第一步

---

## 二、纵向 FVL — 产物 ↔ 上游基准

> "生成的对不对？"

每个阶段生成产物后，以**上一级产物为基准**验证当前产物的正确性和完整性。

### 验证基准链

| 阶段 | 当前产物 | 验证基准（上一级） |
|------|---------|--------------|
| concept | product-concept.json | 用户需求描述 |
| product-map | task-inventory + business-flows | product-concept.json |
| journey-emotion | journey-emotion-map.json | business-flows.json |
| experience-map | experience-map.json | journey-emotion + task-inventory + entity-model |
| design-to-spec | requirements + design + tasks | experience-map + product-map |
| task-execute | 项目代码 | tasks.md + design.md |
| product-verify | 验证结果 | tasks.md (spec) |

### 审计框架

纵向验证统一使用 **4D/6V/闭环** 审计框架：

**4D 工程维度**：
- D1 结论正确：产出中的结论有事实支撑吗？
- D2 有证据：每个声称的能力有具体实现（不是笼统描述）？
- D3 约束识别：已识别所有约束（权限、性能、安全）？
- D4 决策有据：每个设计决策有 rationale（不是随意选择）？

**6V 视角**：
- User：用户能端到端完成任务吗？
- Tech：技术实现可行且高效吗？
- UX：用户体验流畅、无死胡同吗？
- Data：数据全链路可达（输入→处理→存储→展示）？
- Business：业务规则和约束被正确实现？
- Risk：高风险操作有保护措施？

**六类闭环**：
| 闭环类型 | 审计问题 | 不通过标记 |
|---------|---------|----------|
| 配置闭环 | 可配置项有端点/默认值/热更新？ | `CLOSURE_CONFIG` |
| 监控闭环 | 关键操作有埋点/告警/可观测性？ | `CLOSURE_MONITOR` |
| 异常闭环 | 每个操作的异常路径有处理/提示/恢复？ | `CLOSURE_EXCEPTION` |
| 生命周期闭环 | 数据有 TTL/归档/级联删除？ | `CLOSURE_LIFECYCLE` |
| 映射闭环 | A↔B 关系有外键/索引/孤儿检测？ | `CLOSURE_MAPPING` |
| 导航闭环 | 页面有守卫/404/回退/深链接？ | `CLOSURE_NAVIGATION` |

---

## 三、横向 FVL — 兄弟产物交叉验证

> **原则：凡是 pipeline 产生了 N >= 2 个同层产物（兄弟），必须加横向 FVL。**
> "兄弟之间一致吗？"

### 问题根因

纵向 FVL 只验证"当前产物 ↔ 上游产物"，缺少"同层兄弟产物之间的一致性验证"。导致各产物内部自洽但跨产物契约断裂。

历史教训：admin/merchant 前端调用了 ~49 个 server 未实现的端点，直到 Phase 5 deadhunt 才发现。根因是 design-to-spec 各子项目 tasks.md 独立生成、独立验证，没有横向交叉检查。

### 通用框架

```
1. 识别兄弟关系：哪些产物是同一阶段生成的对等产物？
2. 定义横向闭环：兄弟之间应该满足什么一致性约束？
3. 执行交叉验证：用 4D/6V/闭环框架验证这些约束
4. 自动修复：CRITICAL 缺口自动补全，WARNING 记录
```

### 横向 FVL 注册表

| # | 阶段 | 兄弟产物 | 横向验证内容 | 实现位置 |
|---|------|---------|------------|---------|
| H1 | product-map | tasks[] ↔ flows[] ↔ entities[] ↔ constraints[] | entity→flow 映射、flow→task 反向映射、constraint→task enforcement | product-map verify loop |
| H2 | experience-map | screens(role-A) ↔ screens(role-B) | 跨角色交互闭环：触发事件的目标角色有接收屏幕？ | experience-map verify loop |
| H3 | Phase 6 聚合 | use-case ↔ feature-gap ↔ ui-design | 覆盖性验证：每个 screen 被 use-case 覆盖？gap-task 有 UI？ | aggregation checkpoint |
| H4 | design-to-spec | server/tasks ↔ frontend/tasks | API 契约闭环（7 类）：调用/消费/角色CRUD/数据流/字段/权限/路径 | design-to-spec Step 6.5 |
| H5 | task-execute | Round N 代码 ↔ Round N+1 代码 | 跨 Round 回归：后续 Round 是否破坏前序 Round 功能？ | task-execute CC7 |
| H6 | Phase 5 扫描 | verify ↔ deadhunt ↔ fieldcheck | 交叉去重：同一问题的多个发现合并为单个修复任务 | Phase 5 Step 2 聚合 |

### 横向闭环类型定义

跨项目契约闭环（H4 详细定义，其他 H* 参照此模式）：

| 闭环类型 | 验证问题 | 不通过标记 |
|---------|---------|----------|
| 调用闭环 | 前端 API 调用 → server 有对应端点？ | `CONTRACT_CALL_MISSING` |
| 消费闭环 | server 端点 → 至少被一个前端消费？ | `CONTRACT_ORPHAN_ENDPOINT` |
| 角色 CRUD 闭环 | 实体 × 角色 → 该角色需要的操作完整？ | `CONTRACT_CRUD_GAP` |
| 数据流闭环 | 前端展示的聚合数据 → server 有写入路径？ | `CONTRACT_PROVENANCE_GAP` |
| 字段闭环 | server 返回字段名 ↔ 前端引用字段名一致？ | `CONTRACT_FIELD_MISMATCH` |
| 权限闭环 | 端点权限组 ↔ 前端 auth 上下文匹配？ | `CONTRACT_AUTH_MISMATCH` |
| 路径闭环 | URL 前缀 ↔ server 路由分组一致？ | `CONTRACT_PREFIX_MISMATCH` |

### 纵向与横向的关系

```
纵向 FVL（深度）：产物 ↔ 上游基准 — "生成的对不对？"
横向 FVL（广度）：产物 ↔ 兄弟产物 — "兄弟之间一致吗？"

两者互补，缺一不可：
- 纵向确保每个产物忠于上游意图
- 横向确保同层产物之间不矛盾、不遗漏
```

---

## 四、内外双循环 — FVL 层级架构

> **原则：内循环保证局部正确，外循环保证全局一致。两者嵌套运行。**
> "走了这么多步，还在正确的路上吗？"

### 问题根因

纵向和横向验证都是**内循环**——在单个阶段内快速迭代、局部收敛。但 pipeline 跨越 8+ 个阶段，每一跳 95% 保真，8 跳后累积保真率约 66%。三分之一的原始意图可能在阶段传导中丢失。

历史教训：H1 交叉验证发现 5 个 MUST 级功能缺失（积分过期、超时取消、自动收货、结算生成、积分扣款）。constraint 在 concept 层定义，task 在 map 层生成，两者隔一跳，内循环各自验证都通过，但**没有人检查终点产物是否仍然忠于起点意图**。

### 双循环架构

```
                    ┌─── 外循环（大循环）──────────────────────────┐
                    │                                             │
                    ▼                                             │
concept ──→ map ──→ experience ──→ spec ──→ code ──→ scan ──→ OL 审计
  ↕          ↕          ↕            ↕        ↕        ↕         │
 内循环     内循环      内循环       内循环    内循环    内循环       │
(纵+横)    (纵+横H1)   (纵+横H2)   (纵+横H4) (纵+CC6) (纵+H6)    │
                                                                 │
                    ◀─── 反馈回路（触发上游修正）─────────────────┘
```

### 内循环（小循环）

| 特性 | 定义 |
|------|------|
| **作用** | 快速、局部、阶段内验证 |
| **视野** | 当前产物 ↔ 上一级产物（一跳）+ 兄弟产物（同层） |
| **频率** | 每个阶段 1-3 轮 |
| **速度** | 快（秒级，增量检查） |
| **发现类型** | 字段遗漏、格式错误、映射断裂、兄弟不一致 |
| **组成** | 纵向 FVL + 横向 FVL |

内循环是 pipeline 的**心跳**——每个阶段都在做的基础验证。

### 外循环（大循环）

| 特性 | 定义 |
|------|------|
| **作用** | 慢速、全局、跨阶段验证 |
| **视野** | 终点产物 ↔ 起点产物（N 跳） |
| **频率** | 关键里程碑执行（见下方检查点） |
| **速度** | 慢（需要读全量上下文） |
| **发现类型** | 概念漂移、意图丢失、累积偏移、constraint 无 enforcement |
| **核心问题** | "经过 N 次转化后，最终产物是否仍然忠于最初的意图？" |

### 外循环检查点注册表

| # | 检查点 | 时机 | 起点产物 | 终点产物 | 验证问题 | 实现位置 |
|---|--------|------|---------|---------|---------|---------|
| OL-1 | Spec 完整性 | design-to-spec 完成后 | concept + constraints | 全部 tasks.md | 每个产品机制/约束都有实现任务吗？ | design-to-spec 尾部 |
| OL-2 | Code 保真度 | task-execute 完成后 | concept + role-value-map | 运行中的代码 | 代码行为 = 概念描述的行为？角色价值链完整？ | product-verify 前置 |
| OL-3 | 问题溯源 | Phase 5 scan 完成后 | concept | scan 发现列表 | 问题是实现 bug 还是概念漏洞？概念漏洞需回补上游 | Phase 5 Step 3 |

### 外循环审计维度

每个外循环检查点执行以下审计（以 concept-baseline.json 为基准）：

**OL-D1 意图保真**：
- 读取 concept 的 `mission`（产品定位）→ 终点产物是否仍然服务于这个定位？
- 读取 concept 的 `roles[].jobs`（用户任务）→ 每个任务在终点产物中有实现？
- 读取 concept 的 `strategy.errc`（ERRC 策略）→ create 项有实现？reduce 项没过度实现？eliminate 项确实不存在？

**OL-D2 约束执行**：
- 读取 constraints.json 的每个 `enforcement: "hard"` 约束 → 终点产物有执行机制？
- 不只是"task 存在"，而是"task 的实现逻辑确实 enforce 了这个约束"
- 典型缺口：定时类约束（过期、超时）需要 cron/scheduler 任务，不能只靠业务流

**OL-D3 角色完整性**：
- 读取 role-profiles.json 的每个角色 → 该角色的完整 CRUD 生命周期在终点产物中闭合？
- 特别关注：admin 通常需要管理所有实体但最容易遗漏；merchant 的 profile 编辑常被忘记
- 交叉对比：role-A 触发的事件 → role-B 有接收和处理路径？

**OL-D4 机制落地**：
- 读取 product-mechanisms.json 的每个机制 → 终点产物中有对应的技术实现？
- 收费机制有支付集成？推荐机制有算法实现？通知机制有推送通道？

### 外循环反馈回路

外循环发现问题后的处理流程：

```
OL 发现 → 分类：
  │
  ├─ 实现 bug（代码层）→ 生成 fix task → task-execute 修复（不回溯上游）
  │
  ├─ Spec 遗漏（规格层）→ 补全 tasks.md → 重跑 task-execute 对应任务
  │
  ├─ 产品漏洞（概念层）→ 回补上游（逆向补漏协议）：
  │   1. 追加到 task-inventory.json（标注 _backfill + _ol_source）
  │   2. 追加到 experience-map.json（标注 _backfill）
  │   3. 正向重新生成 spec + code
  │   4. 记录到 pipeline-decisions.json（decision: "ol_backfill"）
  │
  └─ 新领域（超出 concept 边界）→ 不补，记入 _uncertainty.unexplored_areas
```

**收敛控制**：外循环回补遵循收敛原则——概念定边界、推导半径递减、规模反转即停。外循环不是无限回溯的借口。

### 内外循环关系

```
内循环（快、局部）：产物 ↔ 邻居 — "这一步对吗？"
外循环（慢、全局）：终点 ↔ 起点 — "走了这么多步，还在正确的路上吗？"

两者嵌套运行：
- 内循环在每个阶段持续执行（心跳）
- 外循环在里程碑处执行（体检）
- 外循环发现问题 → 定位到具体阶段 → 内循环在该阶段修正
```

### 外循环与现有机制的区别（对比表）

| 维度 | design-audit (Phase 8) | product-verify (Phase 5) | 外循环 |
|------|----------------------|-------------------------|--------|
| 方向 | 正向洪泛（concept → 下游覆盖？） | 正向检查（spec → code 匹配？） | **双向**（终点 → 起点漂移？起点 → 终点完整？） |
| 时机 | 产品设计结束时（一次） | 代码完成后（一次） | **每个里程碑**（OL-1/2/3） |
| 跨度 | 产品设计 pipeline 内 | 开发 pipeline 内 | **跨两个 pipeline** |
| 基准 | experience-map 为基准 | spec 为基准 | **concept 为基准**（最上游） |
| 反馈 | 只报告 | 生成 fix task | **触发上游修正**（回补 concept/map） |

---

## 五、收敛控制 — 防止过度验证与范围膨胀

> **原则：FVL 防漏也防胀。漏是缺失，胀是多余。两者对称但治法不同。**

### 问题根因

FVL 的纵向/横向/外循环全部在找"缺什么"（leak detection）。如果不加收敛控制，会产生三种膨胀：

| 膨胀类型 | 表现 | 根因 |
|---------|------|------|
| **Loop 死转** | verify loop 每轮修一个问题、引入两个新问题，永不收敛 | 修复产生副作用，缺退出条件 |
| **Scope 膨胀** | 某阶段补漏时开新战线（本来补一个缺失字段，顺带加了整个功能） | 补漏和新增未分离 |
| **概念漂移** | 外循环回补上游时，concept 越来越大，偏离最初 mission | 回补没有边界约束 |

### 三级收敛机制

收敛不需要在每个验证阶段都放。正确位置是三个层级：

#### CG-1: Micro 收敛 — verify loop 内部

> 位置：每个 verify loop 内部（已有机制，补强规则）

| 规则 | 实现 |
|------|------|
| **Max rounds = 3** | loop 硬限制，第 3 轮仍有问题 → 记录为 WARNING 继续，不再迭代 |
| **单调递减** | 每轮问题数必须 ≤ 上一轮。如果 round 2 问题数 > round 1 → 回滚 round 2 修改，按 round 1 结果继续 |
| **修复范围锁定** | 修复 A 问题时，只允许修改 A 相关的字段/代码。禁止"顺便"修改其他部分 |

#### CG-2: Meso 收敛 — Phase 之间

> 位置：每个 Phase 完成时的质量门禁（新增 scope diff 检查）

```
Phase N 产出完成时：
  scope_delta = Phase_N_产出的实体/任务/屏幕集合 - Phase_N_输入的实体/任务/屏幕集合

  scope_delta 中的每一项必须有以下之一：
    ✓ 上游产物中有明确依据（traceability link）
    ✓ 标注为 _backfill + _source（逆向补漏，有来源）
    ✓ 标注为 _negative_space + _trigger（负空间推导，有触发功能）

  无依据的新增项 → WARNING: "Phase N 新增了 {item}，无上游依据。是补漏还是 scope creep？"
```

**核心原则**：`产出 scope ⊆ 上游 scope + 已标注补漏`。补漏可以，开新战线不行。

#### CG-3: Macro 收敛 — 外循环回补边界

> 位置：外循环反馈回路（OL-1/2/3 回补时）

| 规则 | 实现 |
|------|------|
| **概念定边界** | 回补到 concept 的内容必须服务于已有 `mission`。偏离 mission 的需求 → 记入 `_uncertainty.unexplored_areas`，不回补 |
| **推导半径递减** | 第 1 轮回补可新增 task + screen；第 2 轮只能补字段/规则；第 3 轮只能修 bug。每轮允许的修改范围递减 |
| **规模反转即停** | 如果回补量 > 原始阶段产出量的 20% → 停止回补，标记为"需要重新规划"，交人工决策 |
| **补漏不开新战线** | 回补是"发现遗漏的支撑功能" → 只加最小必要实现。不是"发现新机会" → 那是新迭代的事 |

### 收敛与防漏的对称关系

```
        防漏（FVL 核心）              收敛（FVL 边界）
        ─────────────              ─────────────
目标     找到缺失的东西              防止多余的东西
问题     "少了什么？"               "多了什么？"
机制     纵向/横向/外循环           CG-1/CG-2/CG-3
位置     每个验证阶段               三个层级（不是每阶段）
关系     先防漏，再收敛              收敛是防漏的刹车

互相制衡：
- 防漏说"这里少了 X" → 收敛说"X 有上游依据吗？"
- 防漏说"concept 漏了 Y" → 收敛说"Y 服务于 mission 吗？超 20% 了吗？"
- 没有收敛的防漏 = 无限膨胀
- 没有防漏的收敛 = 做完就算（产品不完整）
```

### 收敛检查不在每个验证阶段的原因

1. **防漏检查天然适合每阶段** — 因为漏洞在任何环节都可能产生
2. **收敛检查只需要在边界处** — 因为膨胀是累积效应，不是瞬时事件：
   - Loop 内部膨胀 → CG-1 管（max rounds + 单调递减）
   - Phase 间膨胀 → CG-2 管（scope diff）
   - Pipeline 膨胀 → CG-3 管（回补边界）
3. **每阶段都放收敛 = verify loop 内防漏和收敛互相拉扯** — 左手补洞右手砍，loop 永远不收敛
