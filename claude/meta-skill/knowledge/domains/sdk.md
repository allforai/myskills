# SDK / Library Domain Knowledge

> SDK/Library 领域的产品设计知识包。
> Bootstrap Step 2.4 加载本文件 → Step 3 用本文件特化产品设计 + 构建 + 运维节点。

---

## 一、领域核心特征

SDK/Library 产品和消费级 App 有本质区别：

| 维度 | App | SDK/Library |
|------|-----|------------|
| 用户 | 终端用户（非技术） | 开发者（技术人员） |
| 交互方式 | UI 界面 | API 调用 |
| 评判标准 | 好不好用 | 好不好集成 |
| 文档重要性 | 辅助 | **核心产品的一部分** |
| 成功指标 | DAU/留存 | 集成数/开发者满意度/issue 响应时间 |
| 竞争壁垒 | 用户体验/网络效应 | API 设计/性能/生态/迁移成本 |

---

## 二、领域特有的产品设计阶段

### 替代关系

| 标准阶段 | SDK 领域替代为 | 理由 |
|---------|-------------|------|
| user-role-definition | **developer-persona-definition** | 只有一类用户：开发者。但开发者分层（初级/高级/架构师）决定 API 复杂度 |
| feature-scoping | **api-surface-design** | SDK 的"功能"是 API 形状，不是 UI 页面 |
| business-model | **distribution-model** | SDK 商业化模式特殊（开源/freemium/enterprise license/usage-based） |
| ui-design | **documentation-design** | 文档 = SDK 的 UI，文档差 = 产品差 |
| experience-map | **developer-journey-map** | 开发者旅程：发现 → 评估 → 集成 → 使用 → 扩展 → 贡献 |

### 补充关系

| 标准阶段 | SDK 领域补充 | 说明 |
|---------|-----------|------|
| concept-crystallization | + **api-philosophy** | API 设计哲学是 SDK 概念的核心（Convention over Configuration? Explicit over Implicit?） |
| concept-validation | + **dogfooding** | 用自己的 SDK 构建一个示例项目是最强的验证 |

### 新增阶段（SDK 特有）

| 新增阶段 | 理论锚点 | 说明 |
|---------|---------|------|
| **api-ergonomics-design** | Principle of Least Astonishment, Progressive Disclosure | API 人机工程学：调用姿势是否自然 |
| **error-design** | Error Model (Midori), Rust Error Handling | 错误设计：错误类型/消息/可恢复性/调试信息 |
| **versioning-strategy** | Semantic Versioning, API Evolution | 版本策略：向后兼容/废弃路径/迁移工具 |
| **ecosystem-design** | Plugin Architecture, Extension Points | 生态设计：插件体系/中间件/适配器模式 |
| **benchmark-validation** | 性能测试方法论 | 性能是 SDK 的核心卖点之一 |

---

## 三、完整的 SDK 产品设计节点图

```
problem-discovery（解决什么开发痛点？现有方案差在哪？）
  ↓
market-research（API 生态分析：同类 SDK 对比，采用率，社区活跃度）
  ↓
assumption-zeroing（挑战 SDK 设计共识："ORM 一定要 Active Record？""HTTP 库一定要链式调用？"）
  ↓
innovation-exploration（跨语言/跨领域借鉴：Rust 的错误处理思想能用到 Go SDK 吗？）
  ↓
developer-persona-definition（开发者画像：初级/高级/架构师，各自期望什么？）
  ↓
api-philosophy（API 设计哲学：显式 vs 隐式？配置 vs 约定？最小 API vs 全能 API？）
  ↓
api-surface-design（API 表面设计：核心类型/函数/方法/参数/返回值）
  ↓
api-ergonomics-design（API 人机工程学：调用链是否自然？5 分钟能否跑通 Hello World？）
  ↓
error-design（错误设计：错误类型层次/消息格式/可恢复性/调试友好度）
  ↓
versioning-strategy（版本策略：SemVer/兼容性承诺/废弃流程/迁移指南）
  ↓
ecosystem-design（生态设计：插件/中间件/适配器/官方扩展 vs 社区扩展）
  ↓
distribution-model（分发模式：开源协议/注册表发布/商业许可/定价）
  ↓
documentation-design（文档设计：Getting Started/API Reference/Guides/Examples/Migration）
  ↓
concept-crystallization（SDK 设计文档结晶）
  ↓
dogfooding（用自己的 SDK 构建示例项目）
  ↓
benchmark-validation（性能基准测试 + 对比竞品）
```

**并行机会：**
- assumption-zeroing + market-research（并行）
- api-ergonomics + error-design（可并行）
- versioning-strategy + ecosystem-design（可并行）
- documentation-design + dogfooding（可并行——写文档同时做示例）

**LLM 决定包含哪些：**
- 简单工具库（如日期处理）：跳过 ecosystem/versioning/benchmark，核心是 api-surface + ergonomics + docs
- 框架级 SDK（如 Web 框架）：全部节点
- 内部 SDK（企业内部使用）：跳过 distribution/market-research，加重 documentation
- 性能敏感 SDK（如数据库驱动）：加重 benchmark-validation

---

## 四、每个阶段的理论锚点详解

### developer-persona-definition（开发者画像）

| 理论 | 核心思想 | 应用 |
|------|---------|------|
| **Developer Experience (DX)** | 开发者体验 = API 设计 + 文档 + 错误信息 + 工具链 | 整体评估框架 |
| **Cognitive Dimensions** | Green & Petre (1996) | 13 个认知维度评估 API 可用性（抽象层次/一致性/可见性等） |
| **5-Minute Rule** | 行业共识 | 开发者应该在 5 分钟内跑通第一个示例 | Getting Started 设计标准 |

**LLM 在 node-spec 中应该：**
- 定义目标开发者层次（初级/高级/架构师）
- 每个层次期望什么样的 API 复杂度
- WebSearch 目标语言/领域的开发者社区（StackOverflow/GitHub Discussions）了解痛点
- 输出：`developer-personas.json`

---

### api-philosophy（API 设计哲学）

| 哲学 | 代表 | 核心取舍 |
|------|------|---------|
| **Convention over Configuration** | Rails, Spring Boot | 默认值好 → 减少配置；但隐式行为多 → 难调试 |
| **Explicit over Implicit** | Go, Rust | 所有行为显式声明 → 可预测；但代码量大 |
| **Progressive Disclosure** | jQuery → React | 简单场景简单 API，复杂场景暴露底层 → 兼顾两端 |
| **Minimal API** | Redis, SQLite | 核心 API 极少 → 学习成本低；但功能有限 |
| **Builder/Fluent** | Retrofit, OkHttp | 链式调用 → 可读性好；但 IDE 补全依赖重 |
| **Zero-Config** | Vite, Parcel | 零配置即可用 → 极速上手；但定制受限 |

**LLM 在 node-spec 中应该：**
- 列出候选哲学，结合目标语言生态的惯例
- WebSearch 目标语言社区对 API 风格的偏好
- AskUserQuestion：选择核心设计哲学
- 输出：`api-philosophy.json`

---

### api-surface-design（API 表面设计）

| 理论 | 核心思想 | 应用 |
|------|---------|------|
| **Principle of Least Astonishment** | 行为应符合开发者预期 | 方法名/参数/返回值不出人意料 |
| **Pit of Success** | Rico Mariani | API 应让正确用法比错误用法更容易 | 默认安全、类型约束 |
| **Huffman Coding for APIs** | 行业共识 | 最常用的操作应该最简洁 | 常用 1 行，罕用可以 5 行 |
| **Orthogonality** | 每个概念独立，不重叠 | 避免两种方式做同一件事 |

**LLM 在 node-spec 中应该：**
- 定义核心类型/接口
- 画出依赖关系图
- 对每个公开方法检查 Least Astonishment
- 输出：`api-surface.json`

---

### api-ergonomics-design（API 人机工程学）

| 检查点 | 验证方式 |
|--------|---------|
| **5 分钟上手** | 从 install 到 Hello World 跑通不超过 5 分钟 |
| **Copy-Paste 友好** | 文档示例可以直接复制运行 |
| **错误可搜索** | 错误信息包含错误码，Google 能搜到解决方案 |
| **类型安全** | IDE 自动补全能引导正确用法 |
| **Zero Import** | 核心功能不需要导入多个包 |
| **Sensible Defaults** | 零配置能工作，配置只在需要覆盖默认时 |
| **Graceful Degradation** | 缺少可选依赖时降级而非崩溃 |

**LLM 在 node-spec 中应该：**
- 用 dogfooding 视角走一遍集成流程
- 逐项检查上述检查点
- 输出：`ergonomics-checklist.json`

---

### error-design（错误设计）

| 理论 | 核心思想 | 应用 |
|------|---------|------|
| **Error Model** (Midori / Joe Duffy) | 错误分类：Bug（程序错误）vs Failure（可恢复故障） | 决定 panic vs return error |
| **Rust Error Handling** | 类型化错误 + ? 操作符 + thiserror/anyhow | 错误链 + 上下文 + 可恢复性 |
| **Google API Error Model** | 错误码 + 消息 + 详情 + 重试指导 | RESTful API 错误标准 |
| **Actionable Errors** | 行业共识 | 错误消息告诉开发者"怎么修"，不只是"什么坏了" | 加速调试 |

**LLM 在 node-spec 中应该：**
- 定义错误类型层次
- 每个错误包含：码 + 消息 + 原因 + 建议修复
- 输出：`error-catalog.json`

---

### documentation-design（文档设计）

**替代标准的 ui-design — 文档 = SDK 的 UI**

| 文档类型 | 目的 | 读者 |
|---------|------|------|
| **Getting Started** | 5 分钟跑通 | 初次接触者 |
| **Tutorials** | 构建完整示例 | 初级开发者 |
| **How-to Guides** | 解决具体问题 | 中级开发者 |
| **API Reference** | 每个方法的精确文档 | 所有开发者 |
| **Architecture Guide** | 内部设计原理 | 高级/贡献者 |
| **Migration Guide** | 版本升级指南 | 现有用户 |
| **FAQ / Troubleshooting** | 常见问题 | 所有 |

**理论锚点：** Diátaxis Documentation Framework (Procida, 2017)
- 4 象限：Tutorials / How-to / Reference / Explanation
- 不同象限服务不同学习阶段

**LLM 在 node-spec 中应该：**
- 按 Diátaxis 框架规划文档结构
- 定义每个文档的目标读者和完成标准
- 输出：`documentation-plan.json`

---

## 五、领域特有的产出物

| 产出物 | 格式 | 对应阶段 |
|--------|------|---------|
| `developer-personas.json` | JSON | developer-persona-definition |
| `api-philosophy.json` | JSON | api-philosophy |
| `api-surface.json` | JSON | api-surface-design |
| `ergonomics-checklist.json` | JSON | api-ergonomics-design |
| `error-catalog.json` | JSON | error-design |
| `versioning-policy.json` | JSON | versioning-strategy |
| `ecosystem-architecture.json` | JSON | ecosystem-design |
| `distribution-plan.json` | JSON | distribution-model |
| `documentation-plan.json` | JSON | documentation-design |
| `sdk-design-document.md` | Markdown | concept-crystallization |
| `benchmark-report.json` | JSON | benchmark-validation |
| `example-project/` | Code | dogfooding |

所有产出写入 `.allforai/product-concept/` 和 `.allforai/sdk-design/`。

---

## 六、领域特有的运维层差异

| 标准运维节点 | SDK 领域差异 |
|------------|------------|
| setup-runtime-env | + 目标语言工具链（Go/Rust/Node/Python toolchain） |
| run-migrations | 通常不需要（SDK 无数据库） |
| seed-essential-data | 替换为：示例项目初始化 |
| demo-forge | 替换为：**dogfooding**（用 SDK 构建示例项目） |
| smoke-test | 替换为：**benchmark + 集成测试**（性能 + 正确性） |
| — | **新增：发布验证**（npm publish --dry-run / go mod tidy / cargo publish --dry-run） |

---

## 七、SDK 类型的节点选择参考

| SDK 类型 | 核心节点 | 可跳过 |
|---------|---------|--------|
| **框架级**（Web 框架/ORM） | 全部 16 个节点 | — |
| **工具库**（日期/加密/验证） | api-surface, ergonomics, error, docs, dogfooding | ecosystem, versioning(简化), benchmark |
| **客户端 SDK**（支付/推送/分析） | api-surface, ergonomics, error, docs, distribution | ecosystem, benchmark |
| **内部 SDK** | api-surface, ergonomics, error, docs | distribution, market-research |
| **性能敏感**（DB 驱动/序列化） | api-surface, error, benchmark, dogfooding | ecosystem(简化) |
| **平台 SDK**（iOS/Android/Flutter 插件） | + 平台适配节点, api-surface, docs, dogfooding | 按平台需求 |
