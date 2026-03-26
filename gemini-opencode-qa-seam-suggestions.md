# 注入“接缝与动态状态”及“黑盒 QA”视角的架构演进建议 (myskills 演进白皮书)

**文档目标**：针对 `myskills` 工具链（特别聚焦 `dev-forge/testforge` 和 `code-replicate/cr-visual`），系统性引入高级 QA 的“接缝（Seam）与动态状态”思维，填补当前 AI 编码智能体在瞬态交互、并发以及异常路径上的盲区。

---

## 1. 核心洞察 (Core Insight)：接缝与动态状态哲学

在现代前端与全栈架构中，**80% 难以复现的严重缺陷（Bug）并不存在于静态页面的渲染中，而是潜伏在系统“接缝（Seams）”与“动态状态（Dynamic States）”的转换之中。**

*   **接缝 (Seams)**：前端与后端的 API 边界、组件之间的状态传递边界、异步任务的交接点。
*   **动态状态 (Dynamic States)**：系统在等待、重试、超时或遭遇竞态时的瞬时表现。

当前大多数 AI Agent（包括早期的开发智能体）习惯于基于“静态快照”进行断言（即：输入 A -> 期望看到 B）。然而，真实的资深黑盒 QA 知道，真正的风险在于“输入 A -> **(网络延迟/失败/并发) -> 处于中间态 C** -> 最终呈现 B 或 D”。忽视这些状态会导致静默失败（Silent Failures）、重复提交（Double Submit）、以及幽灵状态残留（Ghost States）。我们需要赋予 `myskills` 捕捉时间维度的能力。

---

## 2. 现状分析 (Current State Analysis)

目前 `myskills` 体系在端到端（E2E）保障与视觉还原上已经具备了坚实的基础，但也存在典型的“AI 盲区”：

*   **关于 `dev-forge/testforge`**：
    *   **优势**：确立了“铁律（Iron Rules）”和测试金字塔中的 E2E 优先级，能够自动化跑通业务主流程。
    *   **盲区（Happy Path 偏见）**：过于侧重“理想路径”。测试用例倾向于在完美网络和单用户串行操作下进行，忽略了对按钮防抖、加载态遮罩、以及异步错误捕获的破坏性断言。
*   **关于 `code-replicate/cr-visual`**：
    *   **优势**：通过 Sub-Agent 架构实现了高保真的视觉克隆和静态元素校验。
    *   **盲区（静态快照依赖）**：当前的抓取和重放逻辑多为“动作前（Before）”与“动作后（After）”。缺失了对“动作中（During）”瞬态（如 Loading Spinner、骨架屏、Skeleton、乐观更新动画）的记录与校验。

---

## 3. 针对 `dev-forge` (testforge) 的可执行建议

为了让 `testforge` 具备资深 QA 的破坏性思维，建议在生成测试规范和 Playwright 脚本时注入以下检查项：

### 3.1 引入瞬态与错误接缝检查 (Transient & Error Seam Checks)
在每一个涉及网络请求的 E2E 动作中，强制要求 AI 插入对 Promise 生命周期的全面断言：
*   **Pending 态断言**：点击提交后，立刻断言按钮必须呈现 `disabled` 或拥有 `loading` 标识，阻止二次点击。
*   **Rejected/Timeout 态断言**：通过 Playwright 的 `route.abort()` 或 `route.continue({ delay: 5000 })` 人为制造接缝断裂，强制断言系统必须抛出优雅的 Error Toast 或 Fallback UI，而非白屏或控制台静默报错。

### 3.2 引入并发与竞态条件审计 (Concurrency & Race Condition Audits)
*   **极速连击测试 (Rapid Fire clicks)**：在 Playwright 脚本中加入模拟用户暴躁连击的用例，断言数据库不会产生重复的记录（防抖/幂等性校验）。
*   **乱序响应测试**：当触发连续搜索（如输入框联想词）时，拦截并颠倒 API 响应顺序，断言 UI 总是渲染最后一次请求的结果，防止脏数据覆盖。

### 3.3 增加破坏性/逆向探索 (Destructive/Negative Exploration)
*   **猴子测试 (Monkey Testing) 启发式**：要求 `testforge` 生成非标准输入的边界测试（如超长文本、特殊字符注入、断网恢复后的状态保持）。
*   **静默失败探测**：监控浏览器的 `console.error` 和未捕获的 Promise Rejection。只要在测试流中检测到控制台报错，即使 UI 表面显示成功（"Fake Green"），也判定该 E2E 用例失败。

### 3.4 引入双端并发断言 (Dual-Session Concurrency Assertions)
*   **角色碰撞 (Role Collision)**：在高级 E2E 场景中，启动两个隔离的 Browser Context。Role A 修改了资源，立刻断言 Role B 在其会话中（甚至不需要刷新，考察 WebSocket/SSE）或刷新后能否正确感知状态变化。

---

## 4. 针对 `code-replicate` (cr-visual) 的可执行建议

在逆向工程和视觉还原阶段，必须升级记录规范，使其能够“刻录”时间轴上的动态特征。

### 4.1 扩展交互 Schema 以捕获瞬态 (Expand Interaction Schema)
修改 `interaction-recordings.json` 等规范协议，将简单的状态对比升级为时序对比：
*   新增 `screenshot_during`：在触发动作但网络请求被拦截挂起时，捕获此时的 UI 状态（加载遮罩、骨架屏、乐观更新的即时反馈）。
*   新增 `optimistic_update` 标记：指示 Sub-Agent 该动作是否应当在 API 响应前就立刻发生 UI 变更。

### 4.2 增强 `data-integrity` Agent 防御“伪绿” (Prevent "Fake Green")
*   **UI 与网络载荷的强关联**：严禁前端存在硬编码（Hardcoded Mocks）导致的虚假测试通过。`data-integrity` Sub-Agent 必须提取真实的 Network Response JSON Payload，并交叉比对 DOM 中渲染的文本。若数据不一致，判定克隆失败。

### 4.3 增强 `linkage` Agent 捕获网络延迟状态 (Network Delay States)
*   在录制交互时，主动利用代理工具或 Playwright 注入 1000ms - 3000ms 的网络延迟。
*   明确记录该延迟期间页面元素的联动状态（Before -> During/Pending -> After），为后续 `testforge` 提供断言基准。

### 4.4 引入异常路径的视觉对比 (Unhappy Path Visual Comparisons)
*   逆向工程不能仅抓取成功态。必须主动录制目标系统在 404、500、401（未授权拦截）以及网络断开时的错误提示 UI。
*   生成对应的“优雅降级 (Graceful Degradation)” UI 断言，确保重构后的系统在崩溃边缘的视觉表现不逊于原版。

---

## 5. 实施路线图 (Implementation Roadmap)

建议遵循“由规约到执行”的顺序，分阶段将此 QA 哲学落地到 `myskills`：

*   **Phase 1: 规范与架构层定义 (即刻执行)**
    *   更新 `dev-forge` 目录下的 `iron-rules.md` / `SKILL.md`，硬性规定 AI 生成测试代码时必须包含对 Loading/Error 的断言。
    *   升级 `code-replicate` 的 `interaction-recordings.json` Schema，引入 `during_state`、`network_delay` 和 `error_fallback` 字段。
*   **Phase 2: 核心执行器升级 (执行脚本更新)**
    *   扩展 `testforge` 依赖的模板，封装内置的 `playwright` 网络拦截辅助函数（如 `mockDelay`, `mock500Error`）。
    *   在 `cr-visual` 的抓取引擎中，配置统一的网络拦截器以强制暴露瞬态。
*   **Phase 3: Sub-Agent Prompt 调优 (认知升级)**
    *   向 `data-integrity` 和 `linkage` Agent 注入“黑盒测试员”的角色 Prompt。教会它们在代码审查时，像挑剔的 QA 一样寻找“这里如果网络超时会怎样？”的逻辑漏洞。
*   **Phase 4: 全流程联调与案例验证**
    *   选择一个包含复杂表单提交、异步加载列表、WebSocket 联动的靶机项目。运行完整的 `code-replicate` -> `dev-forge` 流水线，验证产出的代码是否免疫竞态条件并具备高质量的错误处理。