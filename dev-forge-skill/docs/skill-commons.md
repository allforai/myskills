# 技能通用增强协议

> 本文档定义三项增强协议的**通用框架**。各 skill 仅需引用本文件并补充自身定制内容。

---

## 一、动态趋势补充（WebSearch）

执行任何技能时，除经典理论外，建议补充近 12–24 个月的实践文章与案例：

- **来源优先级**：P1 官方文档/规范 > P2 知名作者（Martin, Fowler, Cockburn）> P3 技术媒体（InfoQ, ThoughtWorks Radar）> P4 社区帖
- **决策留痕**：对关键结论记录 `ADOPT|REJECT|DEFER` 与理由，避免"只收集不决策"
- **来源写入**：`.allforai/project-forge/trend-sources.json`（跨阶段共用）

各技能提供自身领域的搜索关键词示例（见各 skill 文件）。

---

## 二、外部能力探测协议

> 统一探测、降级模式。完整注册表和规范见 `product-design-skill/docs/skill-commons.md`「外部能力探测协议」章节。

dev-forge 涉及的外部能力：

| 能力 | 使用技能 | 重要性 | 降级行为 |
|------|---------|--------|---------|
| `playwright` | e2e-verify, product-verify | 条件必需（验证阶段） | 阻塞，提示安装 |
| `openrouter_mcp` | design-to-spec, task-execute, e2e-verify, product-verify | 可选 | 跳过 XV，输出提示 |

**提示格式**：`{step_name} ⊘ {能力名} 不可用，{降级动作}`

---

## 三、多级上下文协议（Push-Pull）

> 完整定义见 `product-design-skill/docs/skill-commons.md`「三、多级上下文协议」。

dev-forge 的所有阶段（design-to-spec、task-execute、product-verify）均自动加载概念蒸馏基线（`.allforai/product-concept/concept-baseline.json`），确保产品设计阶段的核心决策（产品定位、角色粒度、治理风格、ERRC 要点）在开发阶段不丢失。

**推（Push）**：concept-baseline.json 自动加载，提供全局业务判断背景。
**拉（Pull）**：各阶段按需从 product-mechanisms.json、role-value-map.json 拉取具体字段（如 governance_styles.downstream_implications → 决定是否生成审核模块）。

---

## 四、开发阶段 FVL 使命：补全负空间

> 完整理论见 `product-design-skill/docs/skill-commons.md` §4.4「产品设计 vs 开发」。

产品设计阶段的 verify loop 关注「正空间」——正常流程是否正确、完整。开发阶段的 FVL 使命根本不同：**补全负空间，实现 100% 闭环**。

**核心区别**：产品设计标记的 exceptions/on_failure 是**线索**，不是完整清单。开发阶段必须：
1. 以正常流程为输入，**主动推导**所有异常路径（网络异常、并发竞态、数据边界、权限变更、外部服务降级、状态不一致、资源耗尽）
2. 对六类闭环做**实现级**而非发现级审计（配置→有端点+默认值+热更新；监控→有埋点+告警+仪表盘；异常→穷举+重试+降级+提示）
3. FVL 阶段 2 的 V7 (Closure) 检查每个模块的闭环完整度，不通过标记 `CLOSURE_*`

**推导出的异常标注 `[DERIVED]`**，以区分产品设计原始标记和开发推导。

**推导收敛**：见 `product-design-skill/docs/skill-commons.md` §五「回补收敛原则」。开发阶段负责 Ring 2+，但同样遵循收敛三条件（概念定边界、推导半径递减、规模反转即停）。negative-space-supplement.json 的 `convergence` 字段记录推导收敛过程。

---

## 五、工程保真增强（4E + 4V）

执行任何阶段时，建议同步参考：`docs/engineering-fidelity.md`。

- **E2 Provenance**：关键产出标注 `_Source: T001, F001, CN001_`，确保可追溯到 product-map。
- **E3 Guardrails**：高频/高风险任务的 rules / exceptions / audit / sla 映射到 spec，不遗漏业务边界。
- **E4 Context**：保留 value / risk_level / frequency，让下游理解"为什么重要"。
- **4V 覆盖**：高频+高风险任务至少覆盖 api + data + behavior 三个工程视角。

各技能根据自身产出类型，定义具体的保真重点（见各 skill 文件）。

---

## 六、跨模型增强（OpenRouter）

通过 OpenRouter MCP (`mcp__plugin_product-design_ai-gateway__ask_model`) 调用不同模型家族，利用各模型专长增强特定阶段的产出质量。

### 专家模型路由矩阵 (The Expert Matrix)

> 根据任务领域自动选择最强审计模型，利用各模型长处进行 XV 交叉验证。

| 审计领域 | 推荐模型家族 | 擅长领域 | 应用场景示例 |
|-----------|-------------|---------|--------------|
| **架构与 API** | **GPT-4o** | 工业级标准遵循、RESTful 规范、OpenAPI 结构 | `api_design_review`, 契约漂移判定 |
| **数据与算法** | **DeepSeek** | RDBMS 性能优化、复杂 SQL、逻辑严密性、算法一致性 | `data_model_review`, 后端逻辑审计 |
| **UI 与 视觉** | **Gemini / GPT-4o-mini** | 多模态推理、布局感知、CSS 原语映射、Stitch 还原度 | `ui_consistency_review`, 前端组件审计 |
| **安全与合规** | **GPT-4o** | 漏洞模式识别、SAST 结果解读、敏感信息脱敏 | `security_audit`, DevSecOps 风险评估 |
| **测试与边界** | **Gemini** | 创意发散、异常路径设想、复杂 Mock 数据构造 | `test_scenario_gap`, 情感诱导数据设计 |

### 调用规范 (XV 自动路由)

执行 XV 审计时，Agent 应根据任务的 `batch` 类型自动映射模型：
- **B1 (Data/Foundation)** -> DeepSeek
- **B2 (Interface/API)** -> GPT-4o
- **B3 (UI/Component)** -> Gemini
- **B5 (Testing/Security)** -> GPT-4o / Gemini

---

## 七、横向 FVL — 兄弟产物交叉验证

> **原则：凡是 pipeline 产生了 N >= 2 个同层产物（兄弟），必须加横向 FVL。**

### 问题根因

现有 FVL 只做**纵向验证**（当前产物 ↔ 上游产物），缺少**横向验证**（同层兄弟产物之间的一致性）。导致各子项目 spec 内部自洽但跨项目 API 契约断裂。

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
| H1 | product-map | tasks[] ↔ flows[] ↔ entities[] | entity→flow 映射（flow 引用的 entity 存在？）、flow→task 反向映射 | product-map verify loop |
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

### 与纵向 FVL 的关系

```
纵向 FVL（深度）：产物 ↔ 上游基准 — "生成的对不对？"
横向 FVL（广度）：产物 ↔ 兄弟产物 — "兄弟之间一致吗？"

两者互补，缺一不可：
- 纵向确保每个产物忠于上游意图
- 横向确保同层产物之间不矛盾、不遗漏
```

---

## 八、内外双循环 — FVL 层级架构

> **原则：内循环保证局部正确，外循环保证全局一致。两者嵌套运行。**

### 问题根因

FVL 的纵向验证和横向验证都是**内循环**——在单个阶段内快速迭代、局部收敛。但 pipeline 跨越 8+ 个阶段，每一跳 95% 保真，8 跳后累积保真率约 66%。三分之一的原始意图可能在阶段传导中丢失。

历史教训：H1 交叉验证发现 5 个 MUST 级功能缺失（积分过期、超时取消、自动收货、结算生成、积分扣款）。这些 constraint 在 concept 层定义，task 在 map 层生成，两者隔一跳，内循环各自验证都通过，但**没有人检查终点产物是否仍然忠于起点意图**。

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
| **组成** | 纵向 FVL（V1-V10, CC1-CC6）+ 横向 FVL（H1-H6） |

内循环是 pipeline 的**心跳**——每个阶段都在做的基础验证。已经在 §四（负空间）、§七（横向）中详细定义。

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

### 外循环 vs 内循环的关系

```
内循环（快、局部）：产物 ↔ 邻居 — "这一步对吗？"
外循环（慢、全局）：终点 ↔ 起点 — "走了这么多步，还在正确的路上吗？"

两者嵌套运行：
- 内循环在每个阶段持续执行（心跳）
- 外循环在里程碑处执行（体检）
- 外循环发现问题 → 定位到具体阶段 → 内循环在该阶段修正
```

### 外循环反馈回路

外循环发现问题后的处理流程：

```
OL 发现 → 分类：
  │
  ├─ 实现 bug（代码层）→ 生成 fix task → task-execute 修复（不回溯上游）
  │
  ├─ Spec 遗漏（规格层）→ 补全 tasks.md → 重跑 task-execute 对应任务
  │
  ├─ 产品漏洞（概念层）→ 回补上游（逆向补漏协议 §五）：
  │   1. 追加到 task-inventory.json（标注 _backfill + _ol_source）
  │   2. 追加到 experience-map.json（标注 _backfill）
  │   3. 正向重新生成 spec + code
  │   4. 记录到 pipeline-decisions.json（decision: "ol_backfill"）
  │
  └─ 新领域（超出 concept 边界）→ 不补，记入 _uncertainty.unexplored_areas
```

**收敛控制**：外循环回补遵循 §五 的收敛原则——概念定边界、推导半径递减、规模反转即停。外循环不是无限回溯的借口。

### 外循环与现有机制的区别

| 维度 | design-audit (Phase 8) | product-verify (Phase 5) | 外循环 |
|------|----------------------|-------------------------|--------|
| 方向 | 正向洪泛（concept → 下游覆盖？） | 正向检查（spec → code 匹配？） | **双向**（终点 → 起点漂移？起点 → 终点完整？） |
| 时机 | 产品设计结束时（一次） | 代码完成后（一次） | **每个里程碑**（OL-1/2/3） |
| 跨度 | 产品设计 pipeline 内 | 开发 pipeline 内 | **跨两个 pipeline** |
| 基准 | experience-map 为基准 | spec 为基准 | **concept 为基准**（最上游） |
| 反馈 | 只报告 | 生成 fix task | **触发上游修正**（回补 concept/map） |

### FVL 三维完整架构

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

## 九、优雅降级与成本控制
