# Auditor Validation Steps — design-to-spec

> This file is loaded by the Auditor Agent for **validation only** (V1-V12 + closedness + XV).
> Auditor is a SEPARATE agent — reviewer ≠ author.
> After validation, the orchestrator loads `auditor-enrich.md` for quality enrichment (fresh agent call).
>
> **大型项目模块分批模式**：当编排器指定了模块组时，Auditor 只验证该模块组的 tasks + design 段落。
> 跨模块维度（V4 一致性、V8 跨子项目、V12 DNA）在所有模块组验证完后由 Auditor-Enrich 统一检查。

---

## 锻造-验证-闭环 (Forge-Verify-Loop, FVL) — 验证维度定义

> 本技能不再使用简单的规则映射，而是采用基于 LLM 的生成与审计闭环。**上游产物（Intermediate Artifacts）被视为不可逾越的「硬约束」 (Inviolable Constraints)。**

### 阶段 1：Agent 生成 (Generation)
*   **输入**：`.allforai/` 全量 JSON（product-map, experience-map, ui-design-spec 等） + `project-manifest.json` + 技术栈模板。
*   **核心约束**：Agent 必须严格遵守 `entity-model.json` 的字段定义、`api-contracts.json` 的结构约定、`constraints.json` 的业务规则，以及 `experience-dna.json` 的体验差异化契约（DIFF-xxx 视觉规格）。
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

*   **闭环完整度**：对六类闭环逐一检查覆盖度（见下方 V7）。

---

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

    11. **Experience DNA Coverage (V12)**: 验证前端子项目 design.md 页面规格是否覆盖 experience-dna.json 的差异化契约。

        LLM Agent 读取 experience-dna.json 的 differentiators 列表和各前端子项目的 design.md pages 章节，判断：
        每个 DIFF 的 visual_contracts 中指定的 component，在对应 placement 屏幕的 page spec 中是否有具体组件规格？

        - CRITICAL — protection_level=core 的 DIFF，其 visual_contract 未出现在任何前端 page spec 中
        - WARNING — protection_level=defensible 的 DIFF 未覆盖
        - OK — nice_to_have 或已覆盖

        **跳过条件**：experience-dna.json 不存在 → 跳过 V12（向后兼容）

        **修正方式**：在对应前端子项目的 design.md page spec 中补充「体验差异化」章节

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
*   **审查重点**：识别任何偏离上游设计产物的"私自改动"，除非具备极强的技术理由。
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

## Step 4.3: Tasks 验证循环（4D/6V+V9/XV/闭环 — 由 Auditor Agent 执行）

> **执行者：独立的 Auditor Agent**（不是 Architect 或 Decomposer Agent）。
> 审查者 ≠ 作者，这是防止"自己审自己"的核心机制。
> Auditor 以全新的上下文读取 requirements + design + tasks，不带生成时的偏见。
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
| **V12 Experience DNA** | **体验差异化任务完整度**：experience-dna.json 中每个 core/defensible DIFF 是否有对应的独立 B3.DNA 原子任务？该任务是否包含完整的 visual_contract（component + spec + behavior + must_not）？ | `TASK_DIFF_MISSING` / `TASK_DIFF_UNDERSPECIFIED` |

**V9 覆盖率、V10 溯源、V11 验收条件、V12 体验差异化是强制审计维度**，CRITICAL 级遗漏必须修复后才能退出循环。

---
---

> 验证完成后，编排器加载 auditor-enrich.md 执行质量补充。
