---
name: design-to-spec
description: >
  Use when the user wants to "convert design to spec", "generate requirements from product map",
  "create tasks from design", "design to specification", "设计转规格", "生成需求文档",
  "生成任务列表", "从产品设计产物生成开发规格", "产物转换",
  or needs to transform product-design artifacts into per-sub-project requirements, design docs, and atomic task lists.
  Also handles shared-utilities analysis (cross-task pattern resonance, third-party library selection, B1 task injection).
  Requires project-manifest.json (from project-setup) and product-map artifacts.
version: "3.3.0"
---

# Design to Spec — 设计转规格

> 从产品设计产物自动生成按子项目划分的 requirements + design + tasks

## 目标

以 `project-manifest.json` 和 product-design 产物为输入，为每个子项目生成三份开发规格文档：

1. **requirements.md** — 用户故事 + 验收条件 + 非功能需求
2. **design.md** — 接口定义 / 页面路由 / 数据模型 / 组件架构 / 时序图
3. **event-schema.md** — 埋点事件定义 / 漏斗 / 北极星指标
4. **tasks.md** — 原子任务列表，按开发层分 Batch（B0-B5）
5. **task-context.json** — 任务上下文预计算（旅程位置 / 情绪 / 约束溯源 / 消费者 / 验证建议）

---

## 定位

```
project-setup（架构层）   design-to-spec（规格层）   task-execute（实现层）
拆子项目/选技术栈         生成 spec 文档/任务列表      逐任务执行代码
manifest.json            req + design + events + tasks  项目代码 + build-log
```

**前提**：
- 必须先运行 `project-setup`，生成 `.allforai/project-forge/project-manifest.json`
- 必须先运行 `product-map`，生成 `.allforai/product-map/` 产物

---

## 快速开始

```
/design-to-spec           # 全量生成（全部子项目）
/design-to-spec full      # 同上
/design-to-spec sp-001    # 仅指定子项目
```

---

## 增强协议（WebSearch + 4E+4V + OpenRouter）

> 通用框架见 `docs/skill-commons.md`，以下仅列本技能定制。

**WebSearch 关键词**：
- `"{framework} API design patterns {year}"`
- `"{database} schema design best practices"`
- `"{protocol} interface naming conventions {year}"`（protocol = REST/GraphQL/gRPC/等）
- `"clean architecture {language} example {year}"`

**4E+4V 重点**（design-to-spec 是产品→工程的核心桥梁）：
- **E2 Provenance**: requirements.md 每个需求项标注 `_Source: T001, F001, CN001_`
- **E3 Guardrails**: task.rules → Business Rules 节；task.exceptions → Error Scenarios 节；task.audit → Audit Requirements 节；task.sla → SLA 标注；task.approver_role → Approval 节
- **E4 Context**: task.value → Value 注释；task.risk_level → Risk 标签；task.frequency → Priority
- **4V**: 高频+高风险任务的 design.md 至少覆盖 api + data + behavior 三个视角

**OpenRouter 交叉审查**（design.md 是全链路咽喉，此处质量提升下游全受益）：
- **`interface_design_review`** (GPT) — 后端 design.md 生成后，发送接口定义给 GPT 审查：
  - 接口命名是否遵循目标协议惯例（REST: 资源复数 + HTTP 动词；GraphQL: Query/Mutation 命名；gRPC: Service/RPC 命名）
  - 请求/响应结构与数据模型的字段一致性
  - 缺失的常见接口（列表查询、批量操作、健康检查/探针）
  - 错误响应格式统一性
  - 输出: `{ "issues": [{ "interface", "type", "suggestion" }], "missing": [...] }`
- **`data_model_review`** (DeepSeek) — 数据模型设计生成后，发送给 DeepSeek 检查：
  - 数据建模合理性（RDBMS: 范式与反范式权衡；Document DB: 嵌套 vs 引用；KV: key 设计与访问模式）
  - 查询性能（缺失索引、N+1 风险、热点 key）
  - 关联完整性（孤立实体、循环依赖、级联规则）
  - 命名一致性（实体名/字段名风格统一）
  - 输出: `{ "violations": [{ "entity", "field", "type", "fix" }] }`
- 审查结果合并到 design.md 的 `## Review Notes` 附录（仅有问题时生成）
- OpenRouter 不可用 → 跳过审查，不阻塞生成

---

## 锻造-验证-闭环 (Forge-Verify-Loop, FVL)

> 本技能不再使用简单的规则映射，而是采用基于 LLM 的生成与审计闭环。**上游产物（Intermediate Artifacts）被视为不可逾越的「硬约束」 (Inviolable Constraints)。**

### 阶段 1：Agent 生成 (Generation)
*   **输入**：`.allforai/` 全量 JSON（product-map, experience-map, ui-design-spec 等） + `project-manifest.json` + 技术栈模板。
*   **核心约束**：Agent 必须严格遵守 `entity-model.json` 的字段定义、`api-contracts.json` 的结构约定以及 `constraints.json` 的业务规则。
*   **动作**：生成 `requirements.md`, `design.md`, `tasks.md` 初稿。
*   **要求**：必须覆盖 **4D 工程维度** (Data, Interface, Logic, UX)。

### 阶段 1.5：负空间推导 (Negative Space Derivation)

> 产品设计是「正空间」——关注正常流程；开发必须补全「负空间」——穷举所有异常。
> 见 `product-design-skill/docs/skill-commons.md` §3.E「阶段转换思维」。

产品设计的 exceptions/on_failure 是**线索而非完整清单**。LLM 以正常流程为输入，系统性推导负空间：

*   **输入**：阶段 1 生成的初稿 + 上游 task.exceptions + action.on_failure + concept-baseline.governance_styles
*   **推导维度**（对每个接口/页面/状态机逐一审查）：

    **单体维度**（对每个接口/页面/状态机逐一审查）：

    | 维度 | 推导方法 | 示例 |
    |------|---------|------|
    | **网络异常** | 每个 API 调用 → 超时/断连/重试/降级 | 表单提交超时 → 幂等重试 + 客户端防重 |
    | **并发竞态** | 每个写操作 → 乐观锁/悲观锁/幂等键 | 同一记录并发修改 → 乐观锁 + 冲突提示 |
    | **数据边界** | 每个输入字段 → 空值/极值/非法格式/注入 | 数值字段 → 负数/零/超大值/精度溢出 |
    | **权限变更** | 每个角色操作 → 操作中途权限被撤销 | 用户编辑内容中途被禁用 → 提交时校验 |
    | **外部服务** | 每个第三方依赖 → 不可用/超时/数据不一致 | 外部网关超时 → 异步回调 + 补偿查询 |
    | **状态不一致** | 每个状态流转 → 非法状态转换/孤儿数据 | 已取消记录收到异步回调 → 自动回滚 |
    | **资源耗尽** | 每个批量/列表操作 → 分页上限/内存溢出/存储满 | 导出 10 万条 → 流式导出 + 进度条 |

    **关系维度**（跨实体/跨时间/跨角色审查）：

    | 维度 | 推导方法 | 示例 |
    |------|---------|------|
    | **跨实体级联** | 读取 entity-model.json 的 `invariants`，对每个不变量 → 验证 spec 中有对应的 enforcement 代码 | 撤销操作→关联资源退回、删除主记录→子记录清理、禁用账户→未完成任务处理 |
    | **时间窗口** | 每个异步/跨时间操作 → 操作期间可能发生的状态变化 | 活动截止前提交、截止后处理→以提交时规则为准；异步回调延迟→主记录已超时取消 |
    | **业务变体** | 读取 entity-model.json 的 `flow_variants`，对每个变体 → 验证 spec 中有对应的分支设计 | 部分处理→多批次追踪；部分撤销→资源分摊；拆分操作→各子集独立处理 |
    | **业务滥用** | 每个面向用户的操作 → 如果被批量/自动化/恶意使用会怎样 | 频率限制、行为检测、上限约束、人机验证 |
    | **冷启动** | 系统从零开始 → 无数据/无用户/无内容时的体验 | 空列表引导、默认数据、新手引导流程 |

*   **输出分两类**：

    **A 类：已有功能的异常补全**（量大，直接补）
    将推导出的异常路径补充到 design.md 对应章节（Error Scenarios / 降级策略 / 边界处理），标注 `[DERIVED]` 以区分产品设计原始标记和开发推导。
    示例：登录 API → `[DERIVED] 密码错误 5 次锁定 30 分钟`

    **B 类：缺失的支撑功能**（量少但影响大，需完整规格）
    推导过程中发现某个核心功能缺少**独立的支撑功能/恢复机制**时（如认证 → 凭证恢复、提交 → 操作撤销、异步操作 → 对账机制），这些不是异常处理，而是**完整的新功能**，需要独立的屏幕、API、数据模型。

    B 类发现的处理流程：
    1. 记录到 `.allforai/project-forge/negative-space-supplement.json`
    2. 为每个 B 类发现生成完整规格（requirements + design + tasks），标注 `[NEGATIVE-SPACE]`
    3. 生成的任务追加到 `tasks-supplement.json`（复用已有补充机制）
    4. 与 `tasks-supplement.json` 的其他补充任务一样，task-execute 加载时动态合并

    **negative-space-supplement.json 结构**：
    ```json
    {
      "created_at": "ISO8601",
      "discoveries": [
        {
          "id": "NS-001",
          "trigger": "模块名 — 闭环缺失描述",
          "derived_from": "任务名（T0xx）的能力级闭环推导",
          "derivation_ring": 1,
          "severity": "MUST",
          "description": "缺失功能描述：触发条件→处理流程→恢复状态",
          "scope": {
            "screens": ["相关页面列表"],
            "apis": ["相关接口列表"],
            "entities": ["相关实体列表"],
            "external_services": ["相关外部服务"]
          },
          "tasks_generated": ["SN-001", "SN-002", "SN-003"],
          "design_section": "design.md ## 模块名 — 功能名"
        }
      ],
      "convergence": {
        "ring_0_tasks": "N（核心任务数）",
        "ring_1_discoveries": "M（一阶推导发现数）",
        "ring_2_deferred": "K（二阶推导，标记移交开发实现级）",
        "stopped_reason": "zero_output | all_deferred | scale_reversal"
      },
      "summary": {
        "total": 1,
        "must": 1,
        "should": 0,
        "product_design_gap": "产品设计阶段关注主流程（正确），开发阶段补全支撑功能"
      }
    }
    ```

    **B 类推导维度**（对每个核心功能追问能力级闭环）：

    | 追问 | 示例 |
    |------|------|
    | 凭证/权限丢失 → 恢复机制？ | 忘记密码、会话过期重登、权限申请 |
    | 操作失败 → 补偿/撤销机制？ | 操作回滚、提交撤销、资源释放 |
    | 数据不一致 → 对账/修复机制？ | 异步对账、数据盘点、状态同步 |
    | 批量操作 → 进度/中断恢复？ | 批量导入中断后续传、导出进度查询 |
    | 通知送达 → 失败重试/替代通道？ | 邮件退信→短信、推送失败→站内信 |

    **B 类逆向补漏**（见 `product-design-skill/docs/skill-commons.md` §五「逆向补漏协议」）：

    下游是用来补上游的漏，不是用来开新战线的。B 类发现必须先判定：是上游的漏还是全新领域？
    - 能从已有任务/实体的闭环推导出 → **回补上游**：直接追加到 task-inventory.json、experience-map.json、use-case-tree.json（标注 `_backfill: true`），然后基于完整的上游数据正向生成 spec
    - 推导不出来 → **不补**，记入 `_uncertainty.unexplored_areas`

    回补流程：
    1. 追加任务到 `task-inventory.json`（标注 `_backfill`，含 `derivation_ring`）
    2. 追加屏幕到 `experience-map.json`（标注 `_backfill`）
    3. 追加用例到 `use-case-tree.json`（标注 `_backfill`）
    4. 基于已回补的上游，正常生成 requirements + design + tasks
    5. 记录到 `negative-space-supplement.json`（留痕，含 `convergence` 收敛记录）

    **收敛控制**（见 `product-design-skill/docs/skill-commons.md` §五「回补收敛原则」）：
    - 一阶推导（Ring 1）：从核心任务闭环推导 → 正常回补
    - 二阶推导（Ring 2）：从回补任务闭环推导 → 仅标记，移交实现级闭环处理
    - 规模反转：某个补漏比父任务还大 → 判定为新领域，不补
    - 收敛过程记录在 `negative-space-supplement.json` 的 `convergence` 字段

    **不变量验证**：
    读取 entity-model.json 的 `invariants` 字段（产品设计阶段 Step 7 产出）。
    对每个不变量，验证 spec 中是否有对应的 enforcement 设计。
    无 enforcement → 标记 `INVARIANT_UNCOVERED`，在 design.md 中补充。

*   **闭环完整度**：对六类闭环逐一检查覆盖度（见下方阶段 2 V7）。

### 阶段 2：4D/6V 审计 (Engineering Audit)
*   **基准**：以上游 `experience-map.json` 和 `product-map.json` 为真值 (Ground Truth)。
*   **硬约束检查**：
    1.  **Contract (V1)**: 验证生成的 API 是否与 `api-contracts.json` 保持 100% 签名一致。
    2.  **Schema (V2)**: 验证数据模型是否违背了 `entity-model.json` 中的关系与约束。
    3.  **Rule Coverage (V3)**: 验证 `constraints.json` 中的每一条规则是否都有对应的工程落地设计。
    4.  **Consistency (V4)**: 跨子项目命名规范、目录结构、模式选型是否统一（如 API 命名风格、错误码体系、DTO 命名模式），不一致项标注 `DRIFT`。
    5.  **Capability (V5)**: 架构设计是否支撑 `task.sla`（响应时间/并发量）和 `task.audit`（审计日志/操作留痕）的非功能需求。对 `_Risk: HIGH_` 任务额外检查异常处理和降级方案。
    6.  **Context (V6)**: 是否回应了 `emotion_context`（journey-emotion-map）揭示的用户情绪痛点，在 UX 维度设计中是否体现了缓解措施（加载提示、操作确认、进度反馈）。
    7.  **Closure (V7)**: 六类闭环实现级完整度审计（阶段转换思维落地）。对每个模块/接口/页面逐一检查：

        | 闭环类型 | 审计问题 | 不通过标记 |
        |---------|---------|----------|
        | 配置闭环 | 可配置项有配置端点/表 + 默认值 + 热更新机制吗？ | `CLOSURE_CONFIG` |
        | 监控闭环 | 关键操作有埋点 + 告警规则 + 可观测性设计吗？ | `CLOSURE_MONITOR` |
        | 异常闭环 | 每个 API/操作的异常路径都有处理 + 用户提示 + 恢复策略吗？ | `CLOSURE_EXCEPTION` |
        | 生命周期闭环 | 创建的数据有 TTL/归档/级联删除策略吗？ | `CLOSURE_LIFECYCLE` |
        | 映射闭环 | A↔B 关系有外键/索引 + 一致性校验 + 孤儿检测吗？ | `CLOSURE_MAPPING` |
        | 导航闭环 | 页面路由有守卫 + 404 + 回退 + 深链接吗？ | `CLOSURE_NAVIGATION` |

    8.  **Cross-Sub-Project Correctness (V8)**: 跨子项目正确性审计 — 验证多个子项目的 spec **彼此是否一致**（V1-V7 检查的是 spec vs 上游产物，V8 检查的是 spec A vs spec B）。

        > **核心问题**：design-to-spec 为每个子项目独立生成 spec，但子项目之间有隐含契约（server 的 API 响应结构必须与前端的类型定义一致）。V8 验证这些隐含契约。

        **触发条件**：子项目数 ≥ 2 且包含 backend + 至少一个 frontend

        **核心原则：LLM 语义判断优先，不依赖固定规则**
        > V8 的本质是让 LLM 像资深全栈工程师一样，同时阅读多个子项目的 spec，判断它们连接时是否会断裂。
        > 以下维度是 LLM 的「审查视角」指引，帮助 LLM 知道从哪些角度去看，而不是机械式检查清单。
        > 不同项目类型的隐含契约不同，LLM 需结合业务上下文自主判断哪些不一致是致命的、哪些是可接受的。

        **V8 审计视角**（LLM 语义驱动，读取多子项目 spec 综合判断）：

        LLM Agent 同时读取所有子项目的 design.md（重点关注 API 章节 + 数据模型章节），以 backend spec 为基准，用全栈工程师的视角判断各子项目 spec 之间是否存在「连接时会断裂」的不一致。

        **审查视角**（非穷举，LLM 可根据项目特点扩展）：
        - API 契约：路由路径、HTTP method、请求/响应结构是否对齐
        - 数据契约：字段名映射、嵌套结构、类型（特别是 i18n 等特殊字段）是否一致
        - 状态/枚举：server 定义的状态值 vs 前端渲染/过滤使用的值是否完全覆盖
        - 认证机制：token 管理方案（单/双 token、刷新流程、字段名）是否统一
        - 通用格式：分页响应、错误码体系等跨接口共用格式是否匹配

        同类前端子项目之间也应比对（如 admin vs merchant 对同一实体的处理是否一致）。

        **严重度由 LLM 判断**：
        - CRITICAL — LLM 认为连接时必然断裂（如结构性不匹配、无自动转换）
        - WARNING — LLM 认为可能不匹配但项目中有 fallback 机制（如 axios 自动命名转换）

        **修正方式**：V8 发现的不一致由阶段 4（Auto-Fix）统一修正 — 以 backend spec 为权威源，修正各前端 spec。

    9.  **Coverage (V9)**: 产品任务 → 端点任务覆盖率审计 — 验证**每个产品任务都有对应的实现任务**，防止功能遗漏。

        > **核心问题**：V1-V8 验证的是「已生成内容的正确性」，V9 验证的是「是否遗漏了内容」。
        > 这是历史上最常见的质量缺陷来源——spec 内容正确但不完整，导致实现阶段漏掉整个功能。

        **触发条件**：始终执行（V9 是强制审计维度）

        **覆盖率检查流程**：

        **V9.1 产品任务 → B2 端点覆盖**（后端子项目）：
        1. 读取 `task-inventory.json` 的全量任务列表（T001-T{N}）
        2. 读取 `tasks.md` 的全部 B2 任务
        3. 对每个产品任务，LLM 语义判断：
           - 该任务涉及的**每个独立业务操作**是否都有对应的 B2 端点任务？
           - 不是 1:1 映射（一个产品任务可能需要多个端点），而是语义覆盖
        4. 输出覆盖率矩阵：

        | 产品任务 | 需要的端点 | 已有 B2 任务 | 状态 |
        |---------|-----------|-------------|------|
        | T071 生成邀请码 | POST /invite-codes, GET /invite-codes, DELETE /invite-codes/:id | — | ✗ MISSING |
        | T058 充值广告余额 | POST /merchant/ad-balance/topup | — | ✗ MISSING |
        | T018 提交订单 | POST /consumer/orders | B2.15 | ✓ COVERED |

        **V9.2 产品任务 → B3 页面覆盖**（前端子项目）：
        1. 对分配给该子项目的产品任务，检查 B3 任务是否覆盖了所有需要的页面/组件
        2. 特别关注：admin/merchant 的审核、统计、详情页是否遗漏

        **V9.3 B2→B5 测试覆盖**：
        1. 每个 B2 端点任务是否有对应的 B5 测试任务
        2. 高风险（_Risk: HIGH_）任务必须有集成测试

        **严重度**：
        - CRITICAL — 产品 CORE 任务无对应 B2/B3 任务（功能完全缺失）
        - WARNING — 产品 BASIC 任务无对应 B2/B3 任务（可 DEFER）
        - INFO — B2 任务无对应 B5 测试任务

        **修正方式**：V9 CRITICAL 发现由阶段 4（Auto-Fix）自动补充缺失的 B2/B3 任务到 tasks.md。

    10. **Data Provenance (V10)**: 数据溯源闭环 — 验证**每个被读取的聚合/统计数据都有可追溯的写入路径**，防止"有消费无生产"的数据断裂。

        > **核心问题**：V9 验证的是"功能是否有任务"，V10 验证的是"数据从哪来"。
        > 典型漏网场景：广告系统有「查看展示/点击统计」端点，但没有「上报展示/点击」端点——读端存在但写端缺失。

        **触发条件**：始终执行（V10 是强制审计维度）

        **溯源检查流程**：

        **V10.1 聚合字段溯源**（后端子项目）：
        1. 扫描 `entity-model.json` 中所有聚合/统计类字段（命名模式：`*_count`, `*_total`, `impressions`, `clicks`, `views`, `rating`, `average_*`, `total_*`）
        2. 扫描 `api-contracts.json` 中所有返回统计数据的 GET 端点（响应包含 stats/analytics/dashboard/overview 语义）
        3. 对每个聚合字段/统计端点，LLM 判断写入来源属于以下哪类：
           - **A) 用户操作端点**：存在对应的 POST/PUT/PATCH 端点直接写入（如 `POST /reviews` 写入评分 → 更新 `average_rating`）
           - **B) 系统内部逻辑**：由其他业务操作的副作用产生（如下单时 `order_count += 1`）
           - **C) 前端行为上报**：需要客户端主动上报的行为数据（如浏览量、广告展示/点击、搜索关键词）
           - **D) 定时任务聚合**：由 cron/worker 定期计算（如日活统计、月度 GMV）
        4. 类型 C 且**无对应上报端点** → `DATA_PROVENANCE_MISSING`
        5. 类型 A/B 且**无可追溯的写入代码路径** → `DATA_PROVENANCE_WARNING`

        **V10.2 跨角色数据链**（全子项目）：
        1. 识别跨角色数据流：角色 A 的操作产生数据 → 角色 B 消费
        2. 检查数据传递链路是否完整：
           - 消费者行为 → 商户统计面板（如商品浏览量、广告点击）
           - 商户操作 → Admin 监管面板（如商户销售额、广告花费）
           - 系统事件 → 通知推送（如订单状态变更 → 通知用户）
        3. 链路中任一环节缺失端点/任务 → `DATA_CHAIN_BROKEN`

        **输出溯源矩阵**：

        | 聚合字段/统计端点 | 数据来源类型 | 写入路径 | 状态 |
        |----------------|-----------|---------|------|
        | ad_campaigns.impressions | C) 前端行为上报 | — | ✗ DATA_PROVENANCE_MISSING |
        | ad_campaigns.clicks | C) 前端行为上报 | — | ✗ DATA_PROVENANCE_MISSING |
        | products.average_rating | A) 用户操作 | POST /reviews → 触发聚合 | ✓ TRACED |
        | products.view_count | C) 前端行为上报 | — | ✗ DATA_PROVENANCE_MISSING |
        | GET /admin/ad-stats | 依赖 impressions/clicks | — | ✗ DATA_CHAIN_BROKEN |

        **严重度**：
        - CRITICAL — 类型 C 数据无上报端点（功能完全断裂，统计数据永远为 0）
        - WARNING — 类型 A/B 写入路径存在但未在 tasks.md 中体现为实现要点
        - INFO — 类型 D 定时任务未定义但数据非关键

        **修正方式**：V10 CRITICAL 发现由阶段 4（Auto-Fix）自动补充缺失的行为上报端点（B2 任务）和前端上报组件（B3 任务）到 tasks.md。

### 阶段 3：XV 交叉审查 (Cross-Verification)
*   **模型路由**：遵循 `docs/skill-commons.md` 专家模型矩阵——API/架构审计 → GPT-4o，数据模型/算法 → DeepSeek，UI/视觉 → Gemini，安全/合规 → GPT-4o。
*   **审查重点**：识别任何偏离上游设计产物的”私自改动”，除非具备极强的技术理由。
*   **执行规则**：
    1.  **Scope 限定**：XV 仅审查 Phase 2 标注 `DRIFT` 或 `WARN` 的条目 + 随机抽样 20% 通过项（成本控制）。
    2.  **Prompt 模板**：向专家模型发送 `{上游产物片段} + {生成 Spec 片段} + {Phase 2 审计结果}`，要求输出 `CONFIRM | REJECT | SUGGEST` + 理由。
    3.  **分歧处理**：若专家模型与 Phase 2 审计结论矛盾，以更严格的结论为准（宁可多修不可漏放）。
    4.  **降级**：OpenRouter 不可用时跳过 XV，在输出中标注 `XV_SKIPPED`，Phase 2 审计结果直接生效。

### 阶段 4：自动修正 (Auto-Fix)
*   汇总 6V + XV 的失败项，由生成 Agent 重新执行，直到审计通过或达到最大轮次（默认 3 轮）。

---

## 验证基准 (Verification Baseline)

> 审计 Agent 应参照以下基准验证生成的 Spec 质量。

| 产品设计产物 | 验证基准（必须在 Spec 中体现） | 4E 标注要求 |
|---|---|---|
| role-profiles.json | requirements.md 按角色分组的用户故事 | E1 |
| task-inventory.json | 任务优先级 (frequency) 与 风险等级 (risk_level) | E4 |
| acceptance_criteria | requirements.md 中的验收条件字段 | E1 |
| use-case-tree.json | 接口/UI 的 Given/When/Then 逻辑链 | E1 |
| constraints.json | 非功能需求（安全/性能/业务规则） | E3 |
| experience-map.json | 页面路由、Actions 接口映射、四态设计 (states) | E1/E3 |
| ui-design-spec.md | Design Token 引用、组件库选型一致性 | E1 |
| ui-design/screenshots/ | 视觉约束截图，生成后 Playwright 截图对比验证还原度 | — |
| task.rules/exceptions | design.md 中的业务规则与异常处理章节 | E3 |
| task.audit | design.md 中的审计中间件/日志表设计 | E3 |

---

## 规格生成原则 (FVL 强制执行)

| 原则 | 具体规则 |
|------|---------|
| 分层依赖方向 | B1(数据模型) → B2(业务逻辑/接口) → B3(UI/展示层) → B4(集成) 严格内→外。展示层不直接访问数据层，必须经过业务逻辑层 |
| 单一职责任务 | 每个原子任务 1-3 文件、15-30 分钟、单一可测结果。禁止出现"实现 XX 系统"这种宽泛任务 |
| 隔离外部调用 | 外部 API/SDK 调用封装为独立 service/adapter 文件，业务层通过接口调用，不直接 import SDK |
| 接口设计遵循目标协议惯例 | REST: 资源复数 + HTTP 动词 + `{ code, message, details }` 错误格式；GraphQL: schema-first + Query/Mutation 分离；gRPC: proto-first + status code；其他协议按其社区最佳实践 |
| 数据模型遵循存储引擎最佳实践 | RDBMS: 范式化设计（反范式需标注理由）；Document DB: 嵌套 vs 引用按访问模式决策；KV: key 结构按查询模式设计。design.md 中标注建模决策依据 |
| 用户故事按角色组织 | requirements.md 按角色分组（"As a {role}"），每组内按 frequency 排序（高频在前） |
| 后端优先生成顺序 | **先生成后端 design.md（数据模型→接口定义），再生成前端 design.md（引用已定义的接口）**。前端 design 中的接口调用必须引用后端 design 中的定义 |
| 前后端 API 契约精确匹配 | 前端 design.md 必须包含**精确 API URL**（含后端实际注册的路由前缀）+ **精确响应 JSON 结构**（字段名、嵌套层级、分页格式）。不允许抽象描述（如"调用用户列表"），必须写明精确的 method + path + 请求参数 + 响应结构。字段名必须与后端 DTO 一致（若前后端命名风格不同如 camelCase vs snake_case，则在设计中标注映射规则）。**前后端独立生成后，必须用 XV 交叉验证接口签名一致性（Step 3.5）** |
| 前端 spec 从后端产物读取 | 前端 design.md 生成时，LLM 必须先读取已生成的后端 design.json（API 端点列表），**直接引用**后端定义的 URL 和响应结构，不允许凭记忆或猜测重新描述。若后端有路由前缀分组（如按角色/模块分组），前端必须使用完整前缀。LLM 发现后端 design.json 不存在时 → 报错要求先生成后端 spec |
| 设计分层展开 | design.md 从数据模型开始，逐层展开到接口 → 页面 → 组件。每层引用上一层定义 |
| 输入验证在边界层 | 所有外部输入在接入层统一验证（whitelist 模式）。防注入（参数化查询/转义/沙箱）。认证在接入层声明，不在业务代码中手动检查 |
| 统一错误处理 | 全局错误拦截（中间件/拦截器/错误边界），返回统一格式。业务错误用自定义错误类型（含错误码），日志分级 ERROR/WARN/INFO，敏感信息不进日志 |
| 测试与实现对称 | 每个 B2 业务逻辑/接口任务必须对应 B5 测试任务。测试间无共享可变状态，每条测试独立可运行 |
| 性能基线内建 | 集合查询强制分页/游标（默认批次 ≤ 50 条），高频查询路径建索引，避免 N+1 问题。大数据量操作走异步任务 |
| 写操作幂等 | 创建类操作支持幂等键（协议级 header 或业务唯一约束），更新类操作使用乐观锁（version 字段或条件更新），并发冲突返回对应协议的冲突状态 |
| 前端 CRUD 套路一致 | 同类型子项目的列表/新建/编辑/删除/详情必须使用相同组件套路和数据流模式。详见「前端 CRUD 实现套路」章节 |
| 多语言全覆盖 | 所有用户可见文本必须通过 i18n 函数获取（禁止硬编码），新增文本必须同步所有语言文件。design.md 中标注 i18n 方案，tasks.md 中每个涉及 UI 文本的任务标注 `_i18n: sync all locales_` |

---

## 各端差异化 Spec 生成

### backend

| 维度 | 内容 |
|------|------|
| requirements 侧重 | 接口合约、并发、幂等、事务一致性 |
| design 侧重 | 接口设计、数据模型（Entity + 关系）、中间件/拦截器链 |
| 非功能需求 | 吞吐量、事务一致性、错误响应规范 |
| 从 experience-map 取 | 不取（无 UI） |
| 从 ui-design 取 | 不取 |

### admin

| 维度 | 内容 |
|------|------|
| requirements 侧重 | CRUD 完整性、批量操作、权限矩阵 |
| design 侧重 | 页面布局、组件树、表单验证规则、CRUD 套路（见「前端 CRUD 实现套路」） |
| 非功能需求 | 角色权限矩阵、审计日志 |
| 从 experience-map 取 | actions → CRUD 页面规格；states → 四态设计；on_failure + exception_flows → 错误反馈；validation_rules → 表单 Schema；requires_confirm → 确认弹窗 |
| 从 ui-design 取 | 全量设计 token |
| CRUD 套路 | design.md 必须包含「CRUD 实现套路」章节，指定列表/表单/删除/详情的组件选型和数据流（详见下方独立章节） |

### web-customer

| 维度 | 内容 |
|------|------|
| requirements 侧重 | SEO、加载速度、可访问性 |
| design 侧重 | SSR/SSG 策略、meta 标签、结构化数据 |
| 非功能需求 | Lighthouse 分数、Core Web Vitals |
| 从 experience-map 取 | actions → 页面组件规格；states → 四态设计（empty 状态需 SEO 友好）；on_failure + exception_flows → 用户友好错误页；validation_rules → 表单 Schema |
| 从 ui-design 取 | 全量设计 token + 性能约束 |

### web-mobile

| 维度 | 内容 |
|------|------|
| requirements 侧重 | 触屏可用性、离线场景 |
| design 侧重 | 移动优先布局、PWA 配置 |
| 非功能需求 | 弱网容忍、Service Worker |
| 从 experience-map 取 | actions → 触屏交互规格；states → 四态设计（loading 需骨架屏、error 需离线提示）；on_failure → 弱网重试 UI；validation_rules → 移动端表单验证 |
| 从 ui-design 取 | 移动适配的设计 token |

### mobile-native (React Native / Flutter)

| 维度 | 内容 |
|------|------|
| requirements 侧重 | 离线同步、推送、设备权限 |
| design 侧重 | 导航栈（RN: React Navigation / Flutter: GoRouter）、原生组件、存储策略 |
| 非功能需求 | 电池/流量优化、后台任务 |
| 从 experience-map 取 | actions → Screen 组件规格（RN: Screen 组件 / Flutter: Screen Widget）；states → 四态设计（离线态额外处理）；on_failure + exception_flows → 原生错误提示；validation_rules → 表单验证 |
| 从 ui-design 取 | 原生端设计 token（如有） |
| 测试工具 | iOS: XCUITest / Android: Maestro (Espresso) / RN: Detox / Maestro / Flutter: Patrol / integration_test |

---

## 前端页面交互套路

> 前端子项目的 design.md 必须为每个页面标注交互类型，并遵循对应的数据流模式。
> 不同交互类型的页面使用不同的组件组合和数据流套路，**同类型页面必须使用相同套路**。
> **existing 模式下**：先扫描已有代码提取实际套路，以已有套路为准。以下为默认套路。

### 套路检测（existing 模式专用）

existing 模式下，Step 3 生成 design.md 之前，先执行套路检测：

1. **Request 层**：扫描 `src/utils/request*` 或 `src/requestConfig*`，识别 HTTP 客户端
2. **列表组件**：扫描 pages 目录，识别列表组件（ProTable / Table / DataGrid）
3. **表单组件**：扫描 `*Create*` / `*Edit*` / `*Form*`，识别表单模式
4. **状态操作**：扫描 `approve` / `reject` / `suspend` / `ship` 等操作模式
5. **删除确认**：扫描 `Modal.confirm` / `Popconfirm` 调用模式
6. **编辑回填**：扫描 `setFieldsValue` / `initialValues` 使用模式
7. **i18n**：扫描 `useIntl` / `useTranslations` / `t()` 调用模式
8. **枚举管理**：扫描 `constants/enum*` / `valueEnum` 定义模式

检测结果写入 design.md 的「页面交互套路」章节。

### 行为原语实现映射

> Step 2 识别出原语后，结合 context7 文档搜索和技术栈能力推导实现方案。
> 可参考 `${CLAUDE_PLUGIN_ROOT}/docs/primitive-impl-map.md` 作为历史参考，但以项目实际技术栈为准。

---

### 图片字段处理规范

> 详见 `${CLAUDE_PLUGIN_ROOT}/docs/field-specs/image-field.md`
> 包含：上传策略（预签名URL/预上传/Multipart）、编辑回填（10技术栈）、多图管理规则、移动端选图入口、显示尺寸规格（服务端URL参数）。
### 视频字段处理规范

> 详见 `${CLAUDE_PLUGIN_ROOT}/docs/field-specs/video-field.md`
> 包含：上传策略（简单POST/分片/预签名URL）、转码状态轮询（10技术栈）、编辑回填（10技术栈）、封面图处理。
### 页面交互类型分类

> **类型定义与推断规则**：见 `product-design-skill/docs/interaction-types.md`（单一事实来源）。
> experience-map Step 1 已为每个 screen 标注 `interaction_type` 字段，design-to-spec 直接读取使用。

37 种交互类型（MG/CT/EC/WK/RT/SB/SY/TU）完整定义见 `product-design-skill/docs/interaction-types.md`。experience-map Step 1 已为每个 screen 标注 `interaction_type` 字段，design-to-spec 直接读取使用。

---

### 按技术栈的各类型套路

#### UmiJS + Ant Design Pro（admin / merchant 类）

> 详见 `${CLAUDE_PLUGIN_ROOT}/docs/tech-stack-patterns/umijs.md`
> 包含：公共基础层（请求层/枚举/字段→组件映射）+ MG1~MG8 全类型套路。
#### Next.js（web-customer 类）

> 详见 `${CLAUDE_PLUGIN_ROOT}/docs/tech-stack-patterns/nextjs.md`
> 包含：C端页面套路概览 + CT1 Feed流 / EC1 详情页 / EC2 收藏夹 / WK1 IM 详细实现。
#### Flutter（mobile-native 类）

> 详见 `${CLAUDE_PLUGIN_ROOT}/docs/tech-stack-patterns/flutter.md`
> 包含：移动端套路概览 + CT1 Feed流 / EC1 详情页 / WK1 IM 详细实现。
### 多语言实现规范

> 通用规范见 `docs/interaction-types.md`。以下为各技术栈的实现差异。

| 技术栈 | i18n 方案 | 翻译文件位置 | hook/函数 |
|--------|----------|-------------|-----------|
| UmiJS (admin/merchant) | `@umijs/max` 内置 | `src/locales/` | `useIntl()` + `intl.formatMessage()` |
| Next.js (website) | `next-intl` | `src/messages/` | `useTranslations()` |
| Flutter (mobile) | `flutter_localizations` | `lib/l10n/*.arb` | `AppLocalizations.of(context)` |

**通用规则**（所有技术栈）：
- 所有用户可见文本通过 i18n 函数获取，禁止硬编码
- 新增文本必须同步所有语言文件
- Key 按 `{模块}.{页面}.{元素}` 分层命名
- tasks.md 中每个涉及 UI 文本的任务附加 `_i18n: sync all locales_` 标注

---

### design.md 中的输出格式

生成 frontend 子项目的 design.md 时，在页面规格之前插入「页面交互套路」章节。每个页面规格中标注交互类型：

~~~markdown
## 页面交互套路

> 本项目各页面按交互类型分类，同类型页面必须遵循相同的组件选型和数据流。

### 请求层
{从套路检测结果或默认套路填写}

### 页面类型分布
| 类型 | 页面数 | 代表页面 |
|------|--------|---------|
| MG1 只读列表 | {N} | 审计日志、积分历史 |
| MG2 CRUD 集群 | {N} | 内容管理、分类管理 |
| MG3 状态机驱动 | {N} | 流程管理 |
| MG4 审批流 | {N} | 内容审核 |
| MG5 主从详情 | {N} | 用户详情 |
| MG6 树形管理 | {N} | 分类管理 |
| MG7 仪表盘 | {N} | 首页 |
| MG8 配置页 | {N} | 系统设置 |
| CT/EC/WK/RT/SB/SY | {N} | Feed流、详情页、IM等 |

### 各类型标准数据流
{按类型列出组件选型 + 数据流 + Service 函数签名}

### 字段→组件映射
{字段类型对照表}

### 枚举管理
{定义位置 + 使用方式}

### 多语言
{i18n 方案 + 语言文件位置 + 同步要求}
~~~

每个具体页面规格标注类型：
~~~markdown
#### 内容列表页 [类型: MG2-完整CRUD]
#### 审计日志页 [类型: MG1-只读列表]
#### 任务详情页 [类型: MG5-主从详情 + MG3-状态机驱动]
~~~

一个页面可以组合多个类型（如「任务详情」= 主从详情 + 状态机操作）。

---

## 工作流

```
前置: 概念蒸馏基线 + 两阶段加载
  概念蒸馏基线（推拉协议 — 见 product-design-skill/docs/skill-commons.md §三.A）:
    .allforai/product-concept/concept-baseline.json → 自动加载，不存在则 WARNING
    → 提供产品定位、角色粒度、治理风格、ERRC 要点作为全局背景知识
    → 指导 requirements/design/tasks 生成时的业务判断
  跨级原始数据拉取（推拉协议 §三.B）:
    product-mechanisms.json:
      - governance_styles[].downstream_implications → 决定是否生成审核模块/队列
      - governance_styles[].system_boundary         → 决定哪些功能只写集成接口
    role-value-map.json:
      - roles[].operation_profile                   → 决定路由策略、缓存策略、批量操作设计
  Phase 1 — 加载索引（< 5KB）:
    project-manifest.json → 子项目列表
    task-index.json → 任务 id/name/frequency/module
    experience-map.json → 界面 id/name/action_count（可选）
    flow-index.json → 业务流 id/name（可选）
  Phase 2 — 按需加载 full 数据（仅加载当前子项目需要的模块）
  若 project-manifest.json 不存在 → 提示先运行 /project-setup，终止
  若 product-map.json 不存在 → 提示先运行 /product-map，终止
  加载 prune-decisions.json → 过滤: 仅 CORE 和 DEFER 任务进入范围
  加载 forge-decisions.json → 读取 technical_spikes + coding_principles（存在时）
  Load: forge-decisions.json → dev_mode（如有：bypass 类型、策略、隔离方式）
  ↓
前置: 上游过期检测
  加载输入文件时，比较关键上游文件的修改时间与本技能上次输出的生成时间：
  - project-manifest.json 在 requirements.md / design.md / tasks.md 生成后被更新
    → ⚠ 警告「project-manifest.json 在 requirements.md/design.md/tasks.md 生成后被更新，数据可能过期，建议重新运行 project-setup」
  - product-map.json 在 requirements.md / design.md / tasks.md 生成后被更新
    → ⚠ 警告「product-map.json 在 requirements.md/design.md/tasks.md 生成后被更新，数据可能过期，建议重新运行 product-map」
  - 仅警告不阻断，用户可选择继续或先刷新上游
  ↓
Step 0: 模块映射验证
  检查 manifest 中所有子项目的 assigned_modules
  合并后与 task-index 的全量模块对照
  未覆盖的模块：
    → 自动分配到最匹配的子项目（按模块类型推断），记录决策（不停）
  → 写入 `.allforai/project-forge/module-assignment-supplement.json`（追加分配条目）
  → **不修改** project-manifest.json（上游产物只读）
  → task-execute 加载时自动合并 manifest + supplement
  ↓
并行执行编排（详见「## 并行执行编排」段落）:
  子项目分类:
    后端组: type = "backend"（通常 1 个）
    前端组: 其余所有子项目（admin/web-customer/web-mobile/mobile-native）
  Phase A — 后端 Agent（1 个 Agent 调用）:
    Agent(backend): Step 1 → Step 2 → Step 3a → Step 3b
    ↓ Step 3b 完成后（API 定义就绪），立即启动 Phase B，同时后端继续:
    Agent(backend-continued): Step 3.5 → Step 3.8 → Step 3.9 → Step 4 → Step 4.5
    ∥ 并行
  Phase B — 前端并行 Agent（单条消息发出 N 个 Agent 调用）:
    ┌── Agent(前端1): Step 1 → Step 2 → Step 3a → Step 3b → Step 3.8 → Step 3.9 → Step 4 → Step 4.5
    ├── Agent(前端2): Step 1 → Step 2 → Step 3a → Step 3b → Step 3.8 → Step 3.9 → Step 4 → Step 4.5
    └── Agent(前端N): Step 1 → Step 2 → Step 3a → Step 3b → Step 3.8 → Step 3.9 → Step 4 → Step 4.5
    全部完成 ↓
  以下 Step 1-4.5 描述每个 Agent 内部执行的步骤内容:
  ↓
Step 1: Requirements 生成
  每个 Agent 对其负责的子项目:
    a. 过滤该子项目的 assigned_modules → 获取模块内的任务列表
    b. 加载对应 full 数据（task-inventory + constraints + use-cases）
    b2. 读取 product-concept.json 的 `pipeline_preferences.infrastructure`（如存在），
        将基础设施需求（暗色模式/i18n/a11y 等）纳入需求和任务生成
    c. 按子项目类型（backend/admin/web-customer/web-mobile/mobile-native）
       应用差异化 requirements 模板
    d. 生成 requirements.md（4E 增强模板）:
       每个需求项包含：
       - 优先级 + 角色（基于上游产物全局上下文判定优先级 + owner_role）
       - Value 注释（← E4 Context，from task.value）
       - 用户故事（As a {role}, I want... So that...）
       - 验收条件（Given/When/Then，来自 use-case-tree）
       - Business Rules（← E3 Guardrails，from task.rules）
       - Error Scenarios（← E3 Guardrails，from task.exceptions）
       - SLA（← E3 Guardrails，from task.sla）
       - Prerequisites（← E3 Guardrails，from task.prerequisites）
       - Approval（← E3 Guardrails，from task.approver_role）
       - Audit（← E3 Guardrails，from task.audit）
       - Config（← E3 Guardrails，from task.config_items）
       - 非功能需求（来自 constraints + 子项目类型特有需求）
       - _Source: T001, F001, CN001_（← E2 Provenance）
       注: 字段不存在或为空时省略对应节，不生成空占位
    → 写入 .allforai/project-forge/sub-projects/{name}/requirements.md
    → 输出进度: 「{name}/requirements.md ✓ ({N} 需求项)」（不停，汇总到 Step 6）
  ↓
Step 2: 行为原语识别 → 共享组件规划
  （仅前端子项目执行；后端子项目跳过此步直接进入 Step 3）
  ↓
Step 2.5: 组件规格导入（component-spec.json 存在时执行）
  **触发条件**：`<BASE>/ui-design/component-spec.json` 存在
  **跳过**：文件不存在 → 直接进入 Step 3（向后兼容）

  **ui-design 产出消费方式**：
  - `tokens.json` — 直接消费，生成 CSS 变量 / Tailwind theme / Flutter theme
  - `component-spec.json` — 直接消费，task-execute 阶段实现共享组件
  - `ui-design-spec.json` — 直接消费，屏幕布局、数据绑定、交互模式的确定性规格
  - `screenshots/` — 视觉约束参考，读取 `<BASE>/ui-design/screenshots/` 目录下的截图，
    dev-forge 生成页面后可用 Playwright 截图与设计截图做视觉对比验证还原度（辅助验证，不阻断）

  **Layer 1（通用，始终执行）**：
  1. 读取 `component-spec.json` 的 `shared_components`
  2. 对每个共享组件：
     a. 从 `primitive-impl-map.md` 查找当前技术栈的 primitives 实现
     b. 写入 design.md 的 `## 共享组件` 章节：
        - 组件名、出现屏幕、Props 接口
        - 交互原语 + 技术栈实现方案
        - 变体矩阵（size/state）
        - a11y 要求（role、aria 属性、键盘导航）
  3. 对 `screen_components` 中的每个屏幕：
     将 used_shared + page_specific 写入对应页面规格
  4. 生成键盘导航矩阵写入 design.md

  **Layer 2（Stitch 增强，`stitch-index.json` 存在且有 success 屏幕时）**：
  5. 读取 `stitch-index.json`
  6. 对每个 `status=success` 的屏幕：
     a. 读取 `stitch/*.html`，提取精确 DOM 结构
     b. 提取内联样式 → design token 映射
     c. 补充 design.md 的组件结构（增强 Layer 1 的推断）
  7. 记录 pipeline-decision

  ↓
Step 3a: 加载产品设计数据模型（可选增强）
  检查 .allforai/product-map/ 下是否存在产品设计阶段的数据模型:
    - entity-model.json → ER 设计起点（实体、字段、关系、状态机）
    - api-contracts.json → API 设计起点（端点、请求/响应结构）
    - view-objects.json → 前端组件规格起点（VO 字段、Action Binding）

  **存在** → 作为 design 生成的基础输入:
    - entities 从 entity-model.json 加载（而非从零推导）
    - endpoints 从 api-contracts.json 加载（而非从零推导）
    - 前端 screens 从 view-objects.json 提取字段定义和交互类型
    - 每个节点保留 source_entity, source_api, source_vo 字段溯源到 product-design 原始 ID
    - 输出进度: 「Step 3a ✓ 加载产品设计数据模型: {N} entities, {M} endpoints, {K} VOs」

  **不存在** → 回退到 Step 3b 的从零推导（向后兼容）
    - 输出进度: 「Step 3a ⊘ 无产品设计数据模型，从零推导」
  ↓
Step 3b: Design 生成 + 技术丰富（API-first 策略）
  **当 Step 3a 有数据时**: 在产品设计基础上补充技术细节:
    - 后端: + 索引策略 + 中间件链 + 错误响应结构 + 分页约束 + 幂等性设计
    - 前端: + 组件架构 + 状态管理 + 路由守卫 + 表单验证 Schema
    - 保持 source_* 字段溯源
  **当 Step 3a 无数据时**: 完整的从零推导（当前 Step 3 行为不变）

  **原则: 先表结构、后 API、再展开**
  每个 Agent 对其子项目，基于 tech-profile 映射:
    所有端共通（最先生成）:
      entities → 数据模型 / 表结构设计（ER 图 Mermaid）
      entity.fields → 字段类型 + 约束 + 索引
      entity.relations → 外键 + 关联关系
    backend（数据模型之后）:
      tasks → 接口设计（按目标协议生成：REST 路由 / GraphQL schema / gRPC proto / 等）
      约束冲突校验（每个接口生成后立即检查）:
        对每个接口定义，读取对应 task 的 rules + exceptions 字段:
        - 若 rules 含「本地处理」「离线」「不存库」「客户端缓存」等关键词
          → 该任务不应生成服务端接口，标记 `[LOCAL_ONLY]` 并跳过
        - 若 rules 含分页/筛选约束（「每页」「分页」「筛选」「排序」「搜索」）
          → 集合查询接口必须包含对应的分页/筛选参数
        - 若 exceptions 含特定错误场景 → 接口的错误响应必须覆盖
      集合查询参数强制提取:
        集合查询类接口生成时，强制读取对应 task 的:
        - main_flow → 提取筛选/搜索/排序操作描述
        - rules → 提取分页规则（默认批次大小、最大批次）、筛选字段、排序字段
        - 生成完整的查询参数文档（分页、排序、筛选）
        - 缺失时使用默认值: 每批 ≤ 20 条, 上限 50 条
      constraints → 中间件/拦截器链设计
      flows → 后端时序图
    前端类 (admin/web-customer/web-mobile):
      多后端服务连接推导:
        读取 manifest 中后端子项目/服务拓扑:
        - 单后端服务 → 生成单一 API 客户端实例
        - 多后端服务（不同地址/端口/协议）→ 自动推导多客户端架构:
          每个后端服务 → 1 个独立客户端实例（按服务职责命名）
          在 design.md 的「请求层」章节写明各实例的连接配置 + 负责的端点/接口范围
          tasks.md B1 中生成对应的客户端初始化任务
      screens → 页面路由 + 组件架构
      screen.states → 界面四态设计（empty/loading/error/permission_denied）
      actions → 交互规格（引用已定义的后端接口）
      action.on_failure + exception_flows → 操作异常 UI 反馈设计
      action.validation_rules → 表单验证 Schema
      action.requires_confirm → 确认弹窗组件规格
      flows → 前端状态流转图
      ui-design-spec → 设计 token 引用
    mobile-native:
      screens → 导航栈 + Screen 组件规格
      screen.states → 界面四态设计（同上）
      actions → 原生交互规格（引用已定义的后端接口）
      action.on_failure + exception_flows → 原生异常 UI 反馈设计
      action.validation_rules → 表单验证规则
    按需生成的 4E 增强章节（字段存在时才生成）:
      task.rules（聚合）→ 按规则语义选择最适合的工程实现方式
      task.outputs.states + task.exceptions → 状态机设计（Mermaid stateDiagram）
      task.audit（聚合）→ 按审计需求选择最适合的工程实现方式
      task.outputs.notifications → 通知/事件设计（事件触发规则）
      task.approver_role → 审批流 API（审批端点 + 状态流转）
      task.config_items → 配置管理设计（配置端点/表）
      task.cross_dept_roles → 集成点设计（webhook/回调端点）
    按需生成的 Coding Principles 章节（forge-decisions.json 存在 coding_principles 时）:
      ## Coding Principles
      ### 通用原则
        coding_principles.universal → 逐条列出
      ### 项目特定原则
        coding_principles.project_specific → 逐条列出（含 spike/constraint 溯源标记）
      此章节写在 design.md 开头（数据模型之前），作为全文件的架构约束前言
    按需生成的 Technical Spike 集成章节（forge-decisions.json 存在 technical_spikes 时）:
      过滤 technical_spikes 中 affected_tasks 与当前子项目任务有交集的 spike
      每个匹配的 spike → 生成 Third-Party Integrations 子章节:
        - Vendor + SDK（from spike.decision.vendor / spike.decision.sdk）
        - Integration approach（from spike.decision.approach）
        - Implementation principles（from spike.implementation_principles → 逐条列出）
        - Affected endpoints / components（根据子项目类型推导）
        - spike.status = "tbd" → 标注 [PENDING: 技术方案待定，后续确认后补充]
    → 写入 .allforai/project-forge/sub-projects/{name}/design.md
    → 同时写入 .allforai/project-forge/sub-projects/{name}/design.json
    design.json 为 design.md 的结构化版本，供 Review Hub 规格 tab 渲染:
    ```json
    {
      "sub_project": "{name}",
      "type": "backend|frontend|mobile",
      "data_models": [
        {
          "table": "orders",
          "source_entity": "E001",
          "fields": [
            {"name": "id", "type": "uuid", "constraints": ["PK", "NOT NULL"], "required": true},
            {"name": "status", "type": "enum", "constraints": ["NOT NULL"], "required": true, "values": ["pending", "paid", "shipped"]}
          ],
          "indexes": [{"name": "idx_status", "columns": ["status"], "type": "btree"}],
          "state_machine": {
            "field": "status",
            "transitions": [
              {"from": "pending", "to": "paid", "trigger": "payment_confirmed"},
              {"from": "paid", "to": "shipped", "trigger": "ship_order"}
            ]
          }
        }
      ],
      "endpoints": [
        {
          "source_api": "API001",
          "method": "GET",
          "path": "/orders",
          "description": "列表查询",
          "params": [{"name": "page", "type": "integer"}, {"name": "status", "type": "string"}],
          "response": {"type": "paginated_list", "item_ref": "orders"},
          "errors": [{"code": 400, "message": "Invalid parameters"}]
        }
      ],
      "pages": [
        {
          "route": "/records",
          "name": "记录列表",
          "source_vo": "VO001",
          "components": ["DataTable", "SearchBar", "Pagination"],
          "states": {"empty": "暂无记录", "loading": "加载中...", "error": "加载失败"}
        }
      ],
      "middleware": [
        {"name": "auth", "description": "JWT 认证"},
        {"name": "audit", "description": "操作审计"}
      ],
      "tasks": [
        {"id": "B1", "name": "项目初始化", "status": "pending"},
        {"id": "B2", "name": "数据模型实现", "status": "pending"}
      ]
    }
    ```
    每个节点的 `source_*` 字段溯源到 product-design 的原始 ID（entity-model/api-contracts/view-objects 中的 ID）。
    无 source 数据时（Step 3a 加载失败），`source_*` 字段省略。
    → 输出进度: 「{name}/design.md + design.json ✓ ({N} 接口, {M} 页面)」（不停，汇总到 Step 6）
  **生成顺序**: 后端 Step 3b 完成（API 定义就绪）后启动前端 Agent (Phase B)，与后端 Step 3.5-4.5 并行执行
  ↓
Step 3.5: Design 交叉审查（由后端 Agent 在 Phase A 内执行，OpenRouter 可用时）
  后端 design.md 生成后，触发两项交叉审查:
  审查 A — 接口设计审查 (GPT):
    提取 design.md 中所有接口定义（签名+请求/响应结构）
    调用: mcp__plugin_product-design_ai-gateway__ask_model(task: "structured_output", model_family: "gpt")
    审查: 协议惯例、数据结构一致性、缺失接口、错误响应统一
    输出: issues[] + missing[]
  审查 B — 数据模型审查 (DeepSeek):
    提取 design.md 中 ER 设计（Mermaid + 字段定义）
    调用: mcp__plugin_product-design_ai-gateway__ask_model(task: "technical_validation", model_family: "deepseek")
    审查: 建模合理性、查询性能、关联完整性、命名一致性
    输出: violations[]
  结果处理:
    有问题 → 在 design.md 末尾追加 ## Review Notes 附录（按问题严重度排列）
    无问题 → 不追加
    → 输出进度: 「Step 3.5 交叉审查 ✓ 接口 {N} issues, 数据模型 {M} violations」
  OpenRouter 不可用 → 跳过，输出: 「Step 3.5 ⊘ OpenRouter 不可用，跳过交叉审查」
  ↓
Step 3.8: 埋点规格生成（Event Schema）
  基于 requirements 和 design 产物，自动推导埋点方案。

  **输入**：
  - requirements.json（用户故事 + 验收标准）
  - design.json（API 端点 / 页面路由）
  - task-inventory.json（frequency、risk_level）
  - experience-map.json（screen actions、on_failure）

  **生成规则**：

  1. **关键事件推导**（语义分析，非规则映射）：
     - 从 requirements + design + experience-map 中识别值得追踪的用户行为和系统事件
     - 按业务重要性筛选，不机械 1:1 映射（不是每个页面/按钮都需要事件）
     - 事件粒度按产品实际分析需求决定

  2. **漏斗定义**：
     - 从 business-flows.json 提取核心流程
     - 每个流程 → 1 个漏斗（funnel）
     - 漏斗节点 = 流程中的关键步骤

  3. **事件属性规范**：
     每个事件必须包含：
     - event_name: snake_case 命名
     - event_category: page_view | user_action | form | error | system
     - properties: { key: type } 映射
     - trigger: 触发条件描述
     - requirement_ref: 关联需求 ID
     - screen_ref: 关联界面 ID（前端事件）

  4. **北极星指标关联**：
     - 从 product-concept.json 提取 success_metrics（如有）
     - 每个北极星指标 → 关联事件 + 计算公式

  **输出**：
  ```
  .allforai/project-forge/sub-projects/{name}/event-schema.json
  .allforai/project-forge/sub-projects/{name}/event-schema.md
  ```

  **event-schema.json 结构**：
  ```json
  {
    "sub_project": "admin",
    "generated_at": "ISO8601",
    "events": [
      {
        "event_name": "user_registration_completed",
        "event_category": "user_action",
        "properties": {
          "user_id": "string",
          "registration_method": "string",
          "time_to_complete_ms": "number"
        },
        "trigger": "用户完成注册表单提交且服务端返回成功",
        "requirement_ref": "R-001",
        "screen_ref": "S-003",
        "priority": "P0"
      }
    ],
    "funnels": [
      {
        "funnel_name": "user_onboarding",
        "flow_ref": "F-001",
        "steps": [
          { "step": 1, "event": "landing_page_view", "label": "落地页" },
          { "step": 2, "event": "registration_started", "label": "开始注册" },
          { "step": 3, "event": "registration_completed", "label": "完成注册" },
          { "step": 4, "event": "first_action_completed", "label": "首次操作" }
        ]
      }
    ],
    "metrics": [
      {
        "metric_name": "activation_rate",
        "formula": "count(first_action_completed) / count(registration_completed)",
        "target": "≥ 60%",
        "related_events": ["registration_completed", "first_action_completed"]
      }
    ]
  }
  ```

  **event-schema.md** 内容：
  - 事件清单表（event_name | category | trigger | priority）
  - 漏斗可视化（Mermaid flowchart）
  - 指标定义表（metric | formula | target）

  → 写入 .allforai/project-forge/sub-projects/{name}/event-schema.json + event-schema.md
  → 输出进度: 「{name}/event-schema ✓ ({N} events, {M} funnels, {K} metrics)」（不停，汇总到 Step 6）
  ↓
Step 3.9: Dev Bypass 接口设计
  当 `forge-decisions.json` 中 `dev_mode.enabled = true` 时执行，否则跳过。

  **生成规则**：

  对 dev_mode.bypasses 中每项，在 design.md 中追加 `## Dev Mode Bypass` 章节：

  1. **接口隔离设计**：
     - 定义 bypass 接口（与生产接口相同签名）
     - 标注隔离方式：Go build tag (`//go:build dev`) / TS 条件导入 (`process.env.NODE_ENV`)
     - 文件命名约定：`{service}_dev.go` / `{service}.dev.ts`

  2. **bypass 行为规格**：
     - 每种策略的具体行为（magic_value 返回什么、auto_callback 延迟多少）
     - 日志输出要求：每次 bypass 执行必须输出 `[DEV_BYPASS] {type}: {action}` 日志

  3. **安全守卫设计**：
     - 运行时守卫：非 development 环境加载 dev 文件时 panic/throw
     - 构建时剔除：build tag / tree-shaking 配置
     - CI 规则：扫描 `_dev\.(go|ts|tsx)$` 文件不被生产代码直接 import

  输出追加到 design.md 的末尾章节。

  Progress: "Dev bypass 接口设计 ✓ ({N} bypasses)"
  ↓
Step 4: Tasks 生成
  按开发层分 Batch，每任务遵循原子标准:
    - 1-3 文件，15-30 分钟，单一目的
    - 指明具体文件路径（基于技术栈 template 约定）
    - 标注 _Requirements_ 和 _Leverage_ 引用
    - 标注 _Guardrails_（← E3，溯源 task.rules/exceptions/audit ID）
    - 标注 _Risk_（← E4，from task.risk_level，HIGH 任务优先 review）
    - 标注 _Acceptance_（← 验收条件，每个 B2 任务必须包含，见下方「验收条件规范」）

  **⚠️ 验收条件规范（B2 任务强制）**：
  > 每个 B2 端点任务必须包含 `_Acceptance_` 字段，列出可执行的验收条件。
  > 验收条件是 Phase 5 product-verify 的判定基准 — 没有验收条件的任务等于没有完成标准。
  > 这是防止「代码有但行为不对」和「功能缺失漏到 Phase 5 才发现」的核心防线。

  **验收条件格式**：
  ```
  _Acceptance_:
  - `METHOD /path` → expected_status, response_assertion
  - `METHOD /path` (edge_case) → expected_status, "error_message"
  ```

  **验收条件粒度规则**：
  | 任务风险 | 最低验收条件数 | 必须覆盖 |
  |---------|-------------|---------|
  | _Risk: HIGH_ | ≥ 4 条 | happy path + 权限拒绝 + 边界条件 + 幂等/并发 |
  | _Risk: MEDIUM_ | ≥ 3 条 | happy path + 权限拒绝 + 一个异常路径 |
  | _Risk: LOW_ | ≥ 2 条 | happy path + 一个异常路径 |

  **验收条件来源优先级**：
  1. `use-case-tree.json` 的 Given/When/Then（最权威）
  2. `task-inventory.json` 的 exceptions / rules（业务规则）
  3. LLM 基于 API 语义推导的边界条件（兜底）

  **B3 前端任务必须引用后端端点（强制）**：
  > 每个 B3 前端任务的描述中必须明确列出它应调用的后端 B2 端点。
  > 格式：`_Backend_: POST /api/v1/consumer/orders (B2.15), GET /api/v1/consumer/addresses (B2.08)`
  > 这确保执行 agent 知道后端已有什么，不会因为"不确定后端有没有"而留空回调。
  >
  > **实战数据**：未标注后端端点的前端任务，80% 的交互回调会被留为空壳。

  **B3 前端任务的验收条件**（推荐但非强制）：
  ```
  _Acceptance_:
  - 页面加载后显示列表数据
  - 点击操作按钮 → 弹出确认对话框
  - 操作成功后列表自动刷新
  ```

  **⚠️ 后端 B2 端点级原子性规则（强制）**：
  > 后端 B2 任务必须按**端点组**拆分，不允许按 controller 级别合并。
  > 违反此规则是 design-to-spec 历史上最常见的质量缺陷——controller 级任务导致
  > 执行 agent 只实现"最显眼"的端点，漏掉子功能（如只做 GET list，漏 approve/reject/stats）。

  **拆分粒度规则**：
  | 场景 | 拆分方式 | 示例 |
  |------|---------|------|
  | 同一实体的标准 CRUD | 可合并为 1 个任务（增删改查紧耦合） | `B2.x 用户 CRUD (GET list + GET detail + POST + PUT + DELETE)` |
  | 独立业务逻辑端点 | 必须拆为独立任务 | `B2.x 商户审批 (POST /merchants/:id/approval)` |
  | 状态变更端点 | 每个状态变更 = 1 个任务 | `B2.x 广告审核通过`, `B2.y 广告审核驳回` |
  | 聚合/统计端点 | 独立任务 | `B2.x 广告统计数据 (GET /ad-campaigns/:id/stats)` |
  | 关联操作端点 | 独立任务 | `B2.x 邀请码生成 (POST /invite-codes)` |

  **⚠️ 集成任务分级标签（强制）**：
  > 每个任务必须标注 `_Integration_` 字段，分为三级：
  >
  > | 级别 | 含义 | 示例 | task-execute 行为 |
  > |------|------|------|-----------------|
  > | `none` | 纯代码，无外部依赖 | 商品列表页、订单详情页 | 正常执行 |
  > | `sdk` | 需要第三方 SDK 但可 mock | Stripe SDK、图片上传 SDK | 实现完整代码 + 可切换的 mock adapter |
  > | `config` | 需要外部账号/配置才能运行 | Apple OAuth、FCM 推送、Stripe webhook | 实现完整代码 + 配置检查 + 缺配置时显示"请配置 XXX" |
  >
  > **为什么需要**：task-execute 对 `none` 任务可以直接跑通验证。
  > 对 `sdk`/`config` 任务，如果留空壳 `() {}`，product-verify 会误判为 genuine。
  > 标注后，task-execute 知道该写 mock adapter 而非空回调，product-verify 知道该按 `integration_pending` 判定而非 genuine。
  >
  > **格式**：`_Integration_: sdk (Stripe SDK — payment processing)` 或 `_Integration_: none`

  **反模式（禁止）**：
  ```
  ✗ B2.45 [backend] Admin ad management controller
    - 实现广告管理控制器（列表、审核、统计）
    → 太粗！agent 只会实现列表，漏掉审核和统计

  ✓ B2.45 [backend] Admin 广告活动列表
    Files: handler/admin_ad_handler.go, service/ad_service.go
    - GET /admin/ad-campaigns（分页、筛选）
  ✓ B2.46 [backend] Admin 广告活动审核（approve/reject）
    Files: handler/admin_ad_handler.go, service/ad_service.go
    - POST /admin/ad-campaigns/:id/approve
    - POST /admin/ad-campaigns/:id/reject
    - 审核需更新状态 + 通知商户
  ✓ B2.47 [backend] Admin 广告统计数据
    Files: handler/admin_ad_handler.go, service/ad_stats_service.go
    - GET /admin/ad-campaigns/:id/stats
    - 聚合展示/点击/消费数据
  ```

  **自检规则**（Step 4 生成完毕后立即执行）：
  对每个后端 B2 任务，检查任务描述中包含的端点数量：
  - 标准 CRUD (GET list + GET detail + POST + PUT + DELETE) → OK（最多 5 端点）
  - 非 CRUD 端点 > 2 个且业务逻辑独立 → **必须拆分**
  - 任务标题包含"管理"/"controller"/"全部" → **高危信号，LLM 重新检查是否应拆分**

  按需在 tasks.md 末尾生成专用任务批次（从聚合字段推导）：
    - 审计日志任务（从 task.audit 聚合 → audit_logs 表+中间件+测试）
    - 审批流任务（从 task.approver_role 聚合 → 审批 API+状态机+测试）
    - 配置管理任务（从 config_items 聚合 → 配置表+端点+测试）
  **Dev Bypass 任务（当 dev_mode.enabled = true）**：

  在 B2（后端 API）之后、B3（UI）之前，插入 dev bypass 任务：

  ```
  B2.5: Dev Bypass 实现
    - 每个 bypass → 1 个任务
    - 任务标记 `[DEV_ONLY]`，构建时剔除
    - 文件限定在 `*_dev.go` / `*.dev.ts`

    示例：
    - [ ] B2.5.1 [backend] [DEV_ONLY] 外部网关 dev bypass
      Files: `services/gateway/gateway_dev.go`
      行为：magic value 映射（test_ok→成功, test_fail→失败, test_timeout→超时），延迟 1s 触发回调
      守卫：`//go:build dev` + 运行时 env 检查
      _Bypass: external_gateway.auto_callback_

    - [ ] B2.5.2 [backend] [DEV_ONLY] 短信验证 dev bypass
      Files: `services/sms/sms_dev.go`
      行为：13800000001-09 + "123456" 万能码
      守卫：`//go:build dev` + 运行时 env 检查
      _Bypass: sms_verification.magic_value_
  ```

  同时在 B5（测试）中追加：

  ```
    - [ ] B5.x [ci] [DEV_ONLY] Dev bypass 安全防线
      Files: `.github/workflows/dev-mode-lint.yml`, `.husky/pre-commit`（或等效）
      行为：CI 扫描 *_dev 文件不被生产代码 import；pre-commit hook 检查
      _Bypass: ci_rules_
  ```

  B5 中应包含埋点验证任务：验证关键事件是否正确触发、属性是否完整、漏斗是否连通。

  **B5 视觉还原度验证**（当 `<BASE>/ui-design/screenshots/` 存在时）：
  生成的前端页面可用 Playwright 截图，与 `ui-design/screenshots/{screen_id}.png` 中的设计截图做视觉对比。
  视觉对比是辅助验证手段，不作为阻断门 — 用于发现明显的布局偏移、配色错误、组件缺失等问题。
  在 B5 测试任务中追加：
  ```
    - [ ] B5.x [frontend] 视觉还原度验证
      Files: `tests/visual/screenshot-compare.spec.ts`（或等效）
      行为：Playwright 逐页截图 → 与 ui-design/screenshots/ 设计稿截图对比
      阈值：根据组件重要性和视觉精度要求动态判定，记录差异报告
      _Source: ui-design/screenshots/_
  ```
  → Batch 结构因子项目类型而异（见下文）
  → 写入 .allforai/project-forge/sub-projects/{name}/tasks.md
  → 输出进度: 「{name}/tasks.md ✓ ({N} 任务, B0-B5)」（不停，汇总到 Step 4.5）

  当 component-spec.json 存在时，B3 任务分批调整：

  **B3 Round 1**（共享组件优先）：
  - 实现 component-spec.json 中的 shared_components
  - 每个共享组件一个任务，含 variants + a11y 实现
  - 任务元数据追加：`component_spec_ref: true`

  **B3 Round 2+**（页面组件）：
  - 页面级组件引用 Round 1 已实现的共享组件
  - 如有 Stitch HTML → 任务追加 `stitch_ref: screen_id` + `stitch_html: 文件路径`

  ↓
Step 4.3: Tasks 验证循环（4D/6V+V9/XV/闭环 — 强制）
  > 本步骤对 Step 4 生成的 tasks.md 执行完整的验证闭环，确保任务列表的正确性**和完整性**。
  > 这是 design-to-spec 流水线中最关键的质量门禁——tasks.md 的质量直接决定实现阶段的完整度。

  **验证循环架构**：
  ```
  大循环（最多 3 轮）:
    ┌── 小循环 A: 4D/6V+V9+V10 审计
    │     每个子项目的 tasks.md 逐维度检查
    │     发现问题 → 自动修正 tasks.md → 重检该维度
    │     通过 → 进入小循环 B
    ├── 小循环 B: XV 交叉审查（可选，OpenRouter 可用时）
    │     专家模型审查任务完整性和原子性
    │     分歧 → 以更严格结论为准 → 修正 → 重检
    │     通过 → 进入小循环 C
    └── 小循环 C: 闭环审计
          检查 7 类闭环在任务层的完整度
          发现缺失 → 补充任务 → 重检
          通过 → 退出大循环
  ```

  **小循环 A: 4D/6V+V9+V10 任务审计**

  LLM 读取 tasks.md + design.md + requirements.md + task-inventory.json，执行以下审计：

  | 维度 | 审计内容 | 不通过标记 |
  |------|---------|----------|
  | **D1 Data** | 每个数据模型（entity）是否有 B1 定义任务 + B2 CRUD 任务？ | `TASK_DATA_GAP` |
  | **D2 Interface** | 每个 design.md 中的 API 端点是否有对应的 B2 任务？ | `TASK_API_GAP` |
  | **D3 Logic** | 每个业务规则（task.rules）是否在某个 B2 任务的 _Guardrails_ 中被引用？ | `TASK_RULE_GAP` |
  | **D4 UX** | 每个 experience-map screen 是否有对应的 B3 页面任务？ | `TASK_UX_GAP` |
  | **V1-V8** | 已有审计维度在任务层的映射（同阶段 2） | 复用标记 |
  | **V9 Coverage** | **产品任务→B2 端点覆盖率**（见阶段 2 V9 定义） | `TASK_COVERAGE_CRITICAL/WARNING` |
  | **V10 Provenance** | **数据溯源闭环**：返回聚合/统计数据的端点，其数据来源是否有写入路径？（见阶段 2 V10 定义） | `TASK_PROVENANCE_CRITICAL/WARNING` |
  | **V11 Acceptance** | **B2 任务验收条件完整性**（见下方 V11 定义） | `TASK_ACCEPTANCE_MISSING/INSUFFICIENT` |

  **V9 覆盖率、V10 溯源、V11 验收条件是强制审计维度**，CRITICAL 级遗漏必须修复后才能退出循环。

  **V11 验收条件完整性**（B2 任务强制）：
  > V9 回答"有没有对应的任务"，V10 回答"数据从哪来"，V11 回答"任务有没有可执行的验收标准"。
  > 没有验收条件的任务 = 没有完成标准 = Phase 5 验收时才发现「代码有但行为不对」。

  **V11.1 存在性检查**：每个 B2 任务是否有 `_Acceptance_` 字段？缺失 → `TASK_ACCEPTANCE_MISSING`（CRITICAL）
  **V11.2 粒度检查**：验收条件数量是否达到 `_Risk_` 级别要求？不达标 → `TASK_ACCEPTANCE_INSUFFICIENT`（WARNING）
  **V11.3 可执行性检查**：每条验收条件是否包含可验证断言（HTTP 方法 + 路径 → 状态码 / 响应字段 / 副作用）？模糊描述 → `TASK_ACCEPTANCE_INSUFFICIENT`（WARNING）

  **修正方式**：
  - `TASK_ACCEPTANCE_MISSING` → 基于 task-inventory 的 main_flow / exceptions / rules 自动生成 `_Acceptance_` 条件
  - `TASK_ACCEPTANCE_INSUFFICIENT` → 补充缺失的异常路径 / 边界条件
  - `TASK_API_GAP` → 在 tasks.md 中补充缺失的 B2 端点任务（遵循端点级原子性规则）
  - `TASK_COVERAGE_CRITICAL` → 从 task-inventory.json 推导缺失的端点，补充 B2 + B3 + B5 任务
  - `TASK_PROVENANCE_CRITICAL` → 补充行为上报端点（B2）+ 前端上报组件（B3）
  - `TASK_DATA_GAP` → 补充 B1 定义任务
  - `TASK_UX_GAP` → 补充 B3 页面任务
  - 修正后回到小循环 A 重检（最多 3 次内循环）

  **小循环 B: XV 交叉审查**（OpenRouter 可用时执行，否则跳过）

  向专家模型发送：
  ```
  {task-inventory.json 摘要} + {tasks.md 任务列表} + {小循环 A 审计结果}
  要求：
  1. 检查是否有产品功能在任务列表中完全缺失
  2. 检查 B2 任务粒度是否合理（是否有 controller 级别的粗粒度任务）
  3. 检查任务间依赖是否合理
  输出：CONFIRM | REJECT(缺失列表) | SUGGEST(优化建议)
  ```

  REJECT → 按缺失列表补充任务 → 重检
  SUGGEST → 记录建议，不阻塞

  **小循环 C: 闭环审计**

  对 tasks.md 中每个模块/功能域检查 6 类闭环：

  | 闭环类型 | 任务层审计问题 | 不通过标记 |
  |---------|-------------|----------|
  | 配置闭环 | 有 config_items 的功能是否有 B2 配置端点任务？ | `TASK_CLOSURE_CONFIG` |
  | 监控闭环 | 有 audit 的功能是否有 B2 审计中间件任务？ | `TASK_CLOSURE_MONITOR` |
  | 异常闭环 | 有 exceptions 的功能是否在 B2 任务的实现要点中提到？ | `TASK_CLOSURE_EXCEPTION` |
  | 生命周期闭环 | 有状态机的实体是否有完整的状态变更端点任务？ | `TASK_CLOSURE_LIFECYCLE` |
  | 映射闭环 | 有关联关系的实体是否有级联操作任务？ | `TASK_CLOSURE_MAPPING` |
  | 导航闭环 | 每个前端页面是否有路由守卫 + 404 + 回退任务？layout 组件（header/footer/sidebar）中的链接目标是否在 pages/ 有对应页面任务？ | `TASK_CLOSURE_NAVIGATION` |
  | 数据溯源闭环 | 返回聚合/统计数据的 GET 端点，其数据源是否有对应的写入端点/任务？（V10 的任务层投影） | `TASK_CLOSURE_PROVENANCE` |

  修正 → 回到小循环 C 重检

  **退出条件**：
  - V9 Coverage CRITICAL = 0（所有 CORE 产品任务有对应 B2 任务）
  - V10 Provenance CRITICAL = 0（所有聚合数据有可追溯的写入路径）
  - V11 Acceptance MISSING = 0（所有 B2 任务有验收条件）
  - 4D 无 GAP（或已修复）
  - 闭环无 CRITICAL 缺失

  **大循环 3 轮后仍有问题** → 记录为已知问题到 `pipeline-decisions.json`，输出警告，继续（不停）

  → 输出进度: 「Step 4.3 验证 ✓ V9 覆盖率: {X}%, V10 溯源: {Y}%, V11 验收: {Z}% 达标, 4D gaps: {N} fixed, 闭环: {M} fixed, XV: {status}」
  ↓
Step 4.5: 任务上下文预计算（Task Context）
  为每个任务预计算完整上下文包，供 task-execute 消费，减少"概念→代码"失真。

  **输入**：
  - tasks.json（本步骤 Step 4 产出）
  - requirements.json（Step 1 产出）
  - design.json（Step 3 产出）
  - use-case-tree.json（如有）
  - journey-emotion.json（如有）
  - constraints.json（如有）
  - business-flows.json（如有）
  - cross-project-dependencies.json（Step 5 产出，第二轮补充）

  **生成规则**：

  对 tasks.json 中每个任务，计算以下上下文字段：

  1. **journey_position**（旅程位置）：
     - 从 use-case-tree.json 查找包含该任务 source_ref 的用例
     - 提取：use_case_id, use_case_name, step_index, total_steps, prev_task, next_task
     - 无匹配 → `null`

  2. **emotion_context**（情绪上下文）：
     - 从 journey-emotion.json 查找该任务关联触点的情绪
     - 提取：emotion（期待/满意/焦虑/沮丧）, emotion_intensity(1-5), design_implication
     - 无匹配 → `null`

  3. **constraint_rationale**（约束溯源）：
     - 对 task.guardrails 中每条规则，反查 constraints.json 找到来源约束
     - 输出：{ rule_text: string, constraint_refs: [{ id, name, reason, severity }] }

  4. **consumers**（消费者清单）：
     - 对后端 API 任务：从其他子项目的 design.json 扫描引用该端点的前端页面
     - 输出：[{ sub_project, screen_id, usage_description }]
     - 前端任务 → `[]`

  5. **frequency_weight**（流量权重）：
     - 从 task-inventory.json 提取 frequency 字段
     - 映射：daily+ → "critical", weekly → "high", monthly → "medium", rare → "low"

  6. **risk_level**（风险等级）：
     - 直接从 task-inventory.json 提取

  7. **verification_hint**（验证建议）：
     - frequency_weight=critical + risk_level=high → "integration_test + load_test"
     - frequency_weight=critical → "integration_test"
     - risk_level=high → "unit_test + code_review"
     - 其他 → "unit_test"

  8. **flow_position**（业务流位置）：
     - 从 business-flows.json 查找包含该任务的流程
     - 提取：flow_id, flow_name, position_in_flow, upstream_tasks, downstream_tasks

  **输出**：
  ```
  .allforai/project-forge/sub-projects/{name}/task-context.json
  ```

  ```json
  {
    "sub_project": "backend",
    "generated_at": "ISO8601",
    "contexts": [
      {
        "task_id": "BE-T001",
        "journey_position": {
          "use_case_id": "UC-003",
          "use_case_name": "用户下单流程",
          "step_index": 2,
          "total_steps": 5,
          "prev_task": "BE-T000",
          "next_task": "BE-T002"
        },
        "emotion_context": {
          "emotion": "anxious",
          "emotion_intensity": 4,
          "design_implication": "需要明确的进度反馈和错误恢复"
        },
        "constraint_rationale": [
          {
            "rule_text": "确认后不可变",
            "constraint_refs": [
              { "id": "CN-005", "name": "GDPR 合规", "reason": "审计追踪完整性", "severity": "critical" },
              { "id": "CN-008", "name": "反欺诈", "reason": "防止数据篡改", "severity": "high" }
            ]
          }
        ],
        "consumers": [
          { "sub_project": "web-customer", "screen_id": "S-003", "usage_description": "核心业务表单提交" },
          { "sub_project": "mobile-app", "screen_id": "S-M012", "usage_description": "移动端提交" }
        ],
        "frequency_weight": "critical",
        "risk_level": "high",
        "verification_hint": "integration_test + load_test",
        "flow_position": {
          "flow_id": "F-002",
          "flow_name": "核心业务处理流程",
          "position_in_flow": 2,
          "upstream_tasks": ["BE-T000"],
          "downstream_tasks": ["BE-T002", "BE-T005"]
        }
      }
    ]
  }
  ```

  → 写入 .allforai/project-forge/sub-projects/{name}/task-context.json
  → 输出进度: 「{name}/task-context.json ✓ ({N} tasks enriched, {M} with journey, {K} with constraints)」（不停，汇总到 Step 6）
  ↓
Step 5: 跨子项目依赖分析
  识别跨项目依赖:
    后端接口定义 → 前端客户端
    共享类型定义 → 公共类型包
    后端 B2 完成 → 前端 B4 才能开始（切换开发桩 → 真实后端）
  生成跨项目任务排序 → execution_order
  → 写入 `.allforai/project-forge/cross-project-dependencies.json`（依赖图 + execution_order）
  → **不修改** project-manifest.json（上游产物只读）
  → 输出进度: 「跨项目依赖图 ✓ ({N} 条依赖)」（不停，汇总到 Step 6）
  ↓
Step 6: 阶段末汇总确认
  展示全部生成结果摘要:

  Phase A (后端):
  | 子项目 | requirements | design | tasks | task-context | event-schema | Step 3.5 审查 |
  |--------|-------------|--------|-------|-------------|--------------|--------------|
  | {backend} | {N} 需求项 | {N} 接口 | {N} 任务 | {N} enriched | {N} events | 接口 {N} issues, 模型 {M} violations |

  Phase B (前端并行):
  | 子项目 | requirements | design | tasks | task-context | event-schema | 状态 |
  |--------|-------------|--------|-------|-------------|--------------|------|
  | {admin} | {N} 需求项 | {N} 页面 | {N} 任务 | {N} enriched | {N} events | 完成/失败 |
  | {web} | {N} 需求项 | {N} 页面 | {N} 任务 | {N} enriched | {N} events | 完成/失败 |
  | {mobile} | {N} 需求项 | {N} 页面 | {N} 任务 | {N} enriched | {N} events | 完成/失败 |

  跨项目依赖: {N} 条
  执行顺序: B0 → B1(并行) → B2 → B3(并行) → B4 → B5
  总任务数: CORE {N} + DEFER {M}
  dev-bypass: {N} tasks [DEV_ONLY]（仅 dev_mode.enabled = true 时显示）

  → 输出汇总进度「Phase 2 ✓ {N} 子项目 × 5 文档 (Phase A 串行 + Phase B 并行), CORE {M} 任务」（不停）
  ↓
Step 6.5: 跨子项目 API 契约闭环审计（Cross-Project Contract Audit）
  > **问题根因**：各子项目 spec 独立生成，前端 tasks.md 中的 API 调用和 server tasks.md 中的端点可能不一致。
  > 此步骤在所有子项目 spec 生成完毕后、进入 Phase 4 之前，用 4D/6V/闭环框架交叉验证跨子项目 API 契约。
  > 历史教训：曾有 admin/merchant 前端调用了 ~49 个 server 未实现的端点，直到 Phase 5 deadhunt 才发现。

  **输入**：所有子项目的 tasks.md + design.md（已在 Step 1-6 生成完毕）

  **审计维度**（7 类闭环 + 4D + 6V 交叉验证）：

  === 闭环审计 ===

  | 闭环类型 | 审计方法 | 不通过标记 |
  |---------|---------|----------|
  | **调用闭环** | 前端 tasks.md 每个 API 调用路径 → server tasks.md 有对应端点？ | `CONTRACT_CALL_MISSING` |
  | **消费闭环** | server tasks.md 每个端点 → 至少被一个前端 tasks.md 引用？ | `CONTRACT_ORPHAN_ENDPOINT`（WARNING） |
  | **角色 CRUD 闭环** | 每个实体 × 每个角色（consumer/merchant/admin）→ 该角色需要的 CRUD 操作是否完整？ | `CONTRACT_CRUD_GAP` |
  | **数据流闭环** | 前端展示的聚合/统计数据 → server 有写入路径？（V10 跨项目投影） | `CONTRACT_PROVENANCE_GAP` |
  | **字段闭环** | server API 返回的字段名 → 前端 tasks.md 引用的字段名一致？ | `CONTRACT_FIELD_MISMATCH` |
  | **权限闭环** | 端点在 server design.md 的权限组 → 前端调用时在正确的 auth 上下文？ | `CONTRACT_AUTH_MISMATCH` |
  | **路径闭环** | 前端引用的 URL 路径前缀（/consumer/, /merchant/, /admin/）→ 与 server 路由分组一致？ | `CONTRACT_PREFIX_MISMATCH` |

  === 4D 审计 ===

  | 维度 | 审计问题 |
  |------|---------|
  | D1 结论正确 | "admin 可以管理产品" → tasks.md 里真的有 admin 的 list + detail + approve 端点？ |
  | D2 有证据 | 每个声称的能力 → 在 tasks.md 中有具体 task（不是笼统描述）？ |
  | D3 约束识别 | 角色权限边界 → 端点是否在正确的权限组（consumer 端点不能出现在 admin 组）？ |
  | D4 决策有据 | admin 只有 approve 没有 browse → 有意设计（记录 rationale）还是遗漏？ |

  === 6V 审计 ===

  | 视角 | 审计问题 |
  |------|---------|
  | User | 用户能端到端完成任务吗？（如：admin 审核产品 → 需要先浏览产品列表 → 需要 list 端点） |
  | Tech | 所有 API 调用路径能解析到 server 路由吗？HTTP method + path 完全匹配？ |
  | UX | 每个列表页有对应的详情页吗？每个详情页的数据字段 server 都返回了吗？ |
  | Data | 前端表单字段 → API request body → server model 字段 → DB column 全链路可达？ |
  | Business | 业务流中每个步骤的 API 调用在 server 都有实现？ |
  | Risk | 高频/高风险操作（支付/删除/权限变更）在 server 有对应的审计/确认机制？ |

  **执行方式**：

  1. 提取 server tasks.md 中所有 B2 端点（HTTP method + path + 权限组）→ 构建 `server_endpoints[]`
  2. 提取每个前端 tasks.md 中所有 API 调用（B3/B4 任务描述中的端点引用）→ 构建 `frontend_calls[sub_project][]`
  3. 提取 server design.md 中每个实体的字段定义 → 构建 `entity_fields[]`
  4. 逐条交叉验证（7 闭环 + 4D + 6V）
  5. 汇总结果

  **结果处理**：

  | 严重度 | 处理 |
  |--------|------|
  | CRITICAL（调用闭环/CRUD 缺口/数据流断裂） | 自动补全：在 server tasks.md 追加缺失的 B2 端点任务，在前端 tasks.md 修正错误路径 |
  | WARNING（孤儿端点/字段命名不一致） | 记录到 forge-decisions.json，不阻塞 |
  | INFO（权限建议/路径前缀建议） | 记录，不处理 |

  **自动补全规则**：
  - 缺失的 server 端点 → 按已有 B2 任务格式追加到 server/tasks.md 的对应 Batch
  - 前端引用了错误路径 → 修正 tasks.md 中的路径描述
  - CRUD 缺口 → 只补必要操作（admin 对产品需要 list + detail，不需要 create/delete）
  - 补全的任务标注 `[CONTRACT-FIX]`，便于追溯

  **输出**：
  - `.allforai/project-forge/contract-audit.json`（审计结果，含每条 finding）
  - 修改过的 tasks.md 文件（已补全缺失端点）
  - 修改过的 design.md 文件（已补全缺失接口定义）

  → 输出进度: 「Step 6.5 契约审计 ✓ 调用闭环: {N}/{M} 匹配, CRUD 闭环: {K} 缺口已补, 字段闭环: {L} 不一致」
  ↓
Step 7: 共享层分析（Shared Utilities Analysis）
  7a. 已有代码扫描（existing 模式执行） + 跨任务模式共振分析 + 三方库 WebSearch 选型 + 用户确认
  7b. 注入 B1 任务 + _Leverage_ 补丁 → tasks-supplement.json + shared-utilities-plan.json
  → 输出进度「Step 7 ✓ {N} 共享工具（复用 {M} 现有 + 新建 {K}）」
```

### 规模自适应

根据子项目任务数自动调整 Step 6 展示策略：
- **小规模**（≤30 tasks/子项目）：逐条展示完整任务列表
- **中规模**（31-80 tasks/子项目）：按 Batch 分组摘要，仅展示 HIGH-risk 任务详情
- **大规模**（>80 tasks/子项目）：统计概览（任务分布、风险分布、覆盖率）+ 仅列 HIGH-risk 项

---

## 并行执行编排 & 任务 Batch 结构

> 详见 `${CLAUDE_PLUGIN_ROOT}/docs/execution-batches.md`
> 包含：子项目分类（后端/前端组）、Phase A/B Agent 编排、Agent prompt 模板、错误处理、resume 模式、Batch 0-5 结构、各端 Batch 内容差异。

## 原子任务格式

每个任务遵循以下格式：

```markdown
- [ ] {batch}.{seq} [{sub-project}] {任务标题}
  - Files: `{file-path-1}`, `{file-path-2}`
  - 具体实现要点（2-4 条）
  - _Requirements: REQ-{id}_
  - _Leverage: {existing-file-or-package}_   ← 引用现有文件或三方包；Phase 5 完成后会自动追加 SU-xxx 引用，无需预填
  - _Guardrails: T001.rules[1,2], CN001_    ← 护栏溯源（from task.rules/exceptions/audit）
  - _Risk: HIGH | MEDIUM | LOW_              ← 风险标签（from task.risk_level）
```

**原子性标准**：
- 1-3 文件：每任务最多涉及 3 个相关文件
- 15-30 分钟：单人可在此时间内完成
- 单一目的：一个可测试的结果
- 具体路径：基于技术栈 template 的命名约定
- 引用明确：标注依赖的 requirements 和可复用的代码
- 护栏溯源：标注该任务需遵守的业务规则/异常/审计 ID
- 风险标签：HIGH 标签任务优先 code review

---

## 输出文件

```
.allforai/project-forge/sub-projects/
  {sub-project-name}/
  ├── requirements.md        # Step 1 输出（人类可读）
  ├── requirements.json      # Step 1 输出（机器可读）
  ├── design.md              # Step 2+3 输出（人类可读）
  ├── design.json            # Step 2+3 输出（机器可读）
  ├── event-schema.md        # Step 3.8 输出（人类可读）
  ├── event-schema.json      # Step 3.8 输出（机器可读）
  ├── tasks.md               # Step 4 输出（人类可读）
  ├── tasks.json             # Step 4 输出（机器可读）
  └── task-context.json      # Step 4.5 输出（任务上下文预计算）

.allforai/project-forge/
  ├── negative-space-supplement.json # 阶段 1.5 负空间推导发现的缺失支撑功能（B 类）
  ├── shared-utilities-plan.json     # Step 7 主产物
  ├── tasks-supplement.json          # Step 7 B1 任务 + 阶段 1.5 SN 任务 + _Leverage_ 补丁
  └── existing-utilities-index.json  # Step 7 已有工具清单（existing 模式）
```

---

## JSON 对应件（机器可读格式）

每个 Markdown 规格文件同时生成 JSON 对应件，供下游技能（task-execute、product-verify）直接解析，避免正则匹配 Markdown 的脆弱性。

### requirements.json

```json
{
  "sub_project": "backend",
  "generated_at": "ISO8601",
  "requirements": [
    {
      "id": "R-001",
      "title": "用户注册",
      "source_refs": ["T-001", "F-001"],
      "priority": "high",
      "acceptance_criteria": ["..."],
      "constraints": ["CN-001"]
    }
  ]
}
```

### design.json

```json
{
  "sub_project": "admin",
  "generated_at": "ISO8601",
  "shared_components": [
    {
      "primitive": "VirtualList",
      "used_by_screens": ["S001", "S005", "S012"],
      "suggested_name": "<DataList>",
      "tech_stack_impl": "ProTable 内置虚拟化"
    },
    {
      "primitive": "StateMachine",
      "used_by_screens": ["S003", "S008"],
      "suggested_name": "useStateMachine",
      "tech_stack_impl": "自定义 hook（枚举 + 合法转换 Map）"
    }
  ],
  "api_endpoints": [
    {
      "id": "EP-001",
      "signature": "CreateUser",
      "requirement_ref": "R-001",
      "request_schema": {},
      "response_schema": {},
      "error_responses": [],
      "protocol_detail": {}
    }
  ],
  "data_models": [
    {
      "name": "User",
      "storage": "users",
      "fields": []
    }
  ]
}
```

---

## Step 7: 共享层分析（Shared Utilities Analysis）

> 在所有子项目 spec 生成完毕后执行。扫描已有代码 + 跨任务模式共振分析 + 三方库选型 → 生成共享层 B1 任务注入。
> 原 shared-utilities 独立技能合并于此，输出格式不变，task-execute 加载时合并 `tasks-supplement.json`。

### 7a. 已有代码扫描 + 模式共振分析

**已有代码扫描**（existing 模式执行，new 模式跳过）：

扫描项目代码，提取工具库存。**扫描目标**（按优先级）：

| 优先级 | 目标位置 | 识别内容 |
|--------|---------|---------|
| 1 | `utils/` `helpers/` `common/` `shared/` `pkg/` | 工具函数 |
| 2 | `services/` | 外部服务封装（email、sms、storage…） |
| 3 | `middleware/` `interceptors/` `guards/` | 横切关注点 |
| 4 | `package.json` / `go.mod` / `requirements.txt` | 已有三方依赖 |

每个已有工具记录为 EU-xxx（Existing Utility）：

```json
{
  "id": "EU-001",
  "type": "email-service | validator | http-client | pagination | logger | ...",
  "location": "src/utils/email.ts",
  "coverage": "发送模板邮件、HTML 邮件",
  "quality": "good | needs-refactor | partial",
  "usable_as_is": true
}
```

质量评估标准：
- `good`：有完整类型定义、有错误处理、无明显技术债
- `needs-refactor`：功能可用但缺少类型/错误处理，或与项目规范不符
- `partial`：仅覆盖部分场景，需要补充

→ 写入 `.allforai/project-forge/existing-utilities-index.json`

**模式共振分析**（Pattern Resonance Analysis）：

Agent 分析所有子项目 `tasks.md`，识别跨任务的逻辑共振：

1. **跨任务语义聚类**：对具有相似逻辑复杂度和技术挑战的任务进行聚类
2. **抽象可行性评估**：评估抽象后的"认知成本降低"与"耦合风险"
3. **共振识别指标**：
   - **逻辑重叠度**：逻辑链条的重合程度
   - **领域稳定性**：该业务逻辑在 `product-map` 中的变化频率（越稳定越值得抽象）
   - **技术通用性**：是否属于目标技术栈中常见的共性问题

**三方库选型**（WebSearch）：

对识别出的 NEW 共享工具类型，WebSearch 调研推荐库。搜索词模板（基于 preflight 已选技术栈动态拼接）：

```
"{framework} {utility_type} best library {year}"
```

推荐方向参考（WebSearch 确认后使用）：

| 类型 | Node.js/TS | Python | Go |
|------|-----------|--------|-----|
| 校验 | class-validator / zod | pydantic | go-playground/validator |
| HTTP client | axios / got | httpx | resty |
| 日期 | dayjs / date-fns | python-dateutil | carbon |
| 日志 | pino / winston | loguru | zap |
| 邮件 | nodemailer | fastapi-mail | gomail |
| 文件上传 | multer | python-multipart | standard lib |
| 分页 | 3行自实现 | 3行自实现 | 3行自实现 |
| 缓存 | ioredis / node-cache | redis-py | go-redis |

每个 NEW 类型给出 1-2 个推荐选项（含推荐理由）。

**用户确认**：

- 当 `__orchestrator_auto: true` 时，**自动采纳推荐选项（选项 A）**，不停顿。仅当检测到 ERROR 级冲突时才停顿。
- 非 auto-mode：展示完整分析结果，一次性收集用户决策（ONE-SHOT）。
- 已有代码（EU-xxx）无需确认，直接采用。

### 7b. 共享层任务注入

用户确认后（或 auto-mode 自动采纳后），自动执行以下操作：

**生成共享工具 B1 任务**：

为每个 SU-xxx 生成原子任务，写入 `.allforai/project-forge/tasks-supplement.json`（**不修改**原始 tasks.md，上游产物只读）：

```json
{
  "created_at": "ISO8601",
  "source": "shared-utilities",
  "b1_tasks": [
    {
      "id": "1.x",
      "sub_project": "api-backend",
      "title": "创建 {utility_type} 共享工具",
      "files": ["src/utils/{name}.ts", "src/utils/index.ts"],
      "details": "封装 {library}，导出统一接口和类型定义",
      "shared_utility_ref": "SU-001",
      "risk": "MEDIUM"
    }
  ],
  "leverage_patches": [
    {
      "task_id": "2.3",
      "append_leverage": ["SU-001 (class-validator)", "SU-003 (ExceptionFilter)"]
    }
  ],
  "refactor_tasks": [
    {
      "id": "1.x",
      "sub_project": "api-backend",
      "title": "重构 {utility_type}（EU-{id}）以符合项目规范",
      "files": ["{existing_location}"],
      "details": "补充类型定义和错误处理",
      "shared_utility_ref": "EU-001",
      "risk": "LOW"
    }
  ]
}
```

**task-execute 加载时合并**：task-execute 启动时检查 `tasks-supplement.json` 是否存在，若存在则：
- 将 `b1_tasks` 追加到后端子项目 tasks 的 Batch 1 末尾
- 将 `leverage_patches` 中的引用合并到对应任务的 `_Leverage_` 字段
- 将 `refactor_tasks` 追加到 Batch 1（EU-xxx 复用已有，quality=needs-refactor 时）

**_Leverage_ 补丁**（写入 supplement，不修改原文件）：

扫描所有子项目 tasks.md，找到 `affects_tasks` 中匹配的任务 ID，将 SU-xxx 引用记录到 `tasks-supplement.json` 的 `leverage_patches` 数组。

**写入 `shared-utilities-plan.json`**：

```json
{
  "created_at": "ISO8601",
  "mode": "new | existing",
  "existing_utilities": [
    {
      "id": "EU-001",
      "type": "email-service",
      "location": "src/utils/email.ts",
      "quality": "good",
      "action": "reuse | refactor"
    }
  ],
  "shared_utilities": [
    {
      "id": "SU-001",
      "type": "validator",
      "library": "class-validator",
      "decision": "use-third-party | self-implement",
      "b1_task_id": "1.5",
      "affects_tasks": ["2.3", "2.7", "3.1"]
    }
  ],
  "tasks_updated": 24,
  "b1_tasks_added": 4
}
```

→ 输出进度: 「Step 7 ✓ {N} 共享工具（复用 {M} 现有 + 新建 {K}），{P} 个任务更新了 _Leverage_」

### Step 7 输出文件

```
.allforai/project-forge/
├── shared-utilities-plan.json          # 主产物，Step 7 完成标志
├── tasks-supplement.json               # B1 任务 + _Leverage_ 补丁（task-execute 加载时合并）
└── existing-utilities-index.json       # existing 模式下的已有工具清单
```

各子项目 tasks.md **不被修改**。B1 任务和 _Leverage_ 补丁写入 `tasks-supplement.json`，由 task-execute 在加载时动态合并。
