# Dev Forge — 开发锻造设计思想与经典理论

> 从产品设计产物到可运行代码：每个阶段背后的理论锚点与工程哲学

## 总纲

Dev Forge 的六个阶段（项目引导 → 设计转规格 → 脚手架生成 → 种子数据 → 跨端验证 → 产品验收）不是凭直觉拼凑，而是扎根于经典软件工程理论。每个阶段的决策都可追溯到具体的理论依据。

### 十大工程原则

| # | 原则 | 理论来源 | 在 Dev Forge 中的体现 |
|---|------|---------|---------------------|
| 1 | **做一件事，做好它** | Unix Philosophy (McIlroy, 1978) | 子项目单一职责、原子任务设计、模块隔离 |
| 2 | **架构映射组织** | Conway's Law (Conway, 1968) | 子项目拆分反映团队/角色边界 |
| 3 | **依赖向内，不向外** | Clean Architecture (Martin, 2017) | 分层 Batch 结构、依赖方向控制 |
| 4 | **约定优于配置** | Convention over Configuration (DHH, 2004) | 模板驱动脚手架、命名约定统一 |
| 5 | **先合约，后实现** | API-First / Contract-First Design | 先表结构 + API 端点，再展开前端 |
| 6 | **测试在左，验证在右** | Shift-Left Testing + Acceptance Testing | 种子数据 → 单元测试 → E2E → 产品验收 |
| 7 | **简单优于完美** | Worse is Better (Gabriel, 1989) | 先出 mock-server 快速跑通，不等完美后端 |
| 8 | **曳光弹先行** | Tracer Bullet (Hunt & Thomas, 1999) | scaffold 先打通端到端最小路径，再逐步填充 |
| 9 | **你不会需要它** | YAGNI (Jeffries / XP, 1999) | scaffold 只生成必要文件，不过度工程化 |
| 10 | **端口与适配器** | Hexagonal Architecture (Cockburn, 2005) | 前端连 mock 与连真实 API 只是换适配器 |

### 双证据机制

与 product-design-skill 一致，Dev Forge 采用 **经典理论 + Web 趋势** 双证据：

```
经典理论（稳定锚点）          Web 热门文章（动态补充）
Conway's Law                  "monorepo vs polyrepo 2025"
Clean Architecture            "Go project layout best practices"
Twelve-Factor App             "Flutter state management trends"
...                           ...
↓                             ↓
决策依据 = 理论 + 最新实践 + 用户偏好
```

---

## 阶段理论映射表

| 阶段 | 经典理论锚点 | 代表来源 |
|------|-------------|---------|
| **project-setup** | Conway's Law, Unix Philosophy, Bounded Context (DDD), Twelve-Factor App, C4 Model | Conway 1968, McIlroy 1978, Evans 2003, Wiggins 2011, Brown 2018 |
| **design-to-spec** | Clean Architecture, SOLID, Hexagonal Architecture, REST Maturity Model, Database Normalization, User Story Mapping, C4 Model | Martin 2017, Martin 2003, Cockburn 2005, Richardson 2008, Codd 1970, Patton 2014, Brown 2018 |
| **project-scaffold** | Convention over Configuration, Separation of Concerns, DRY, Unix Philosophy, Worse is Better, Tracer Bullet, YAGNI | DHH 2004, Dijkstra 1974, Hunt & Thomas 1999, McIlroy 1978, Gabriel 1989, Jeffries 1999 |
| **seed-forge** | Boundary Value Analysis, Equivalence Partitioning, Property-Based Testing, Faker Pattern | Myers 1979, QuickCheck (Claessen & Hughes 2000) |
| **e2e-verify** | Test Pyramid, Test Trophy, Contract Testing, BDD, Shift-Left Testing | Cohn 2009, Dodds 2019, Pact, North 2006, Forrester 2016 |
| **product-verify** | ATDD, Heuristic Evaluation, Shift-Left Quality, Hexagonal Architecture (端口验证) | Beck 2003, Nielsen 1994, Forrester 2016, Cockburn 2005 |

---

## 三段理论分布

### 前段：架构决策（project-setup）

> 核心问题：如何将产品设计产物正确映射为技术架构？

**指导理论**：

| 理论/框架 | 核心主张 | 在 project-setup 中的落地 |
|-----------|---------|-------------------------|
| **Unix Philosophy** (McIlroy, 1978) | "做一件事，做好它"；程序应该小而专注，通过组合解决复杂问题 | 每个子项目只承担一个职责（API / Admin / Consumer）；子项目间通过 API 组合 |
| **Conway's Law** (Conway, 1968) | 系统架构不可避免地映射组织的沟通结构 | 子项目拆分参照角色边界（商户团队 → merchant-admin，消费者团队 → customer-web） |
| **Bounded Context** (Evans, 2003) | 每个限界上下文有独立的领域模型和语言 | 模块分配时，同一业务概念在不同端可有不同视角 |
| **Twelve-Factor App** (Wiggins, 2011) | 配置外置、端口绑定、依赖显式声明等 12 条准则 | 每子项目端口配置、.env 管理、依赖隔离 |
| **Microservices Patterns** (Richardson, 2018) | 服务拆分策略：按业务能力 / 按子域 | 子项目拆分策略参考（按角色 vs 按业务域 vs 按技术栈） |

**参考文献**：
- McIlroy, M. D. (1978). *Unix Time-Sharing System: A Retrospective*
- Conway, M. E. (1968). *How Do Committees Invent?*
- Evans, E. (2003). *Domain-Driven Design: Tackling Complexity in the Heart of Software*
- Wiggins, A. (2011). *The Twelve-Factor App*. https://12factor.net
- Richardson, C. (2018). *Microservices Patterns*. Manning Publications

---

### 中段：规格与实现（design-to-spec + project-scaffold）

> 核心问题：如何将需求转化为可执行的原子任务和可生成的代码骨架？

**指导理论**：

| 理论/框架 | 核心主张 | 在 design-to-spec / scaffold 中的落地 |
|-----------|---------|--------------------------------------|
| **Clean Architecture** (Martin, 2017) | 依赖规则：外层依赖内层，内层不知道外层 | Batch 分层（B1 Foundation → B2 API → B3 UI → B4 Integration）遵循依赖方向 |
| **SOLID Principles** (Martin, 2003) | 单一职责、开放封闭、里氏替换、接口隔离、依赖倒置 | 原子任务设计（1-3 文件、单一目的）；模块间接口清晰 |
| **REST Maturity Model** (Richardson, 2008) | Level 0-3：从 RPC 到超媒体 | API 端点设计遵循 Level 2（资源 + HTTP 动词 + 状态码） |
| **Database Normalization** (Codd, 1970) | 1NF → 2NF → 3NF → BCNF 消除冗余 | 表结构设计从 product-map entities 推导，遵循 3NF |
| **User Story Mapping** (Patton, 2014) | 按用户活动组织故事，横轴=流程，纵轴=优先级 | requirements.md 中用户故事按角色+流程组织 |
| **API-First Design** (Swagger/OpenAPI) | 先定义 API 合约，再实现两端 | design.md 先生成后端 API 端点，前端引用之 |
| **Convention over Configuration** (DHH, 2004) | 遵循约定减少配置，框架提供合理默认值 | 模板驱动脚手架，目录结构/命名约定预定义 |
| **Separation of Concerns** (Dijkstra, 1974) | 将系统分解为不重叠的关注点 | 目录结构按关注点划分（models / services / controllers / views） |
| **DRY** (Hunt & Thomas, 1999) | 每一份知识在系统中只有一个权威表述 | shared-types 包提取、API 客户端从 Swagger 生成 |
| **Hexagonal Architecture** (Cockburn, 2005) | 端口与适配器：核心逻辑不依赖外部，通过端口与外部交互 | 前端连 mock-server 与连真实 API 只是换适配器（base URL），核心代码不变 |
| **Worse is Better** (Gabriel, 1989) | 简单性优先于正确性和完整性，先能用再完美 | mock-server 先行：宁可数据不完美但前端能立即开发，不等后端 100% 完成 |
| **Tracer Bullet** (Hunt & Thomas, 1999) | 先打通端到端最小路径，验证架构可行，再逐步填充 | scaffold 生成的骨架就是曳光弹：一条完整的请求→响应路径已跑通 |
| **YAGNI** (Jeffries / XP, 1999) | "你不会需要它"，不为假设的未来需求编码 | scaffold 只生成当前 spec 要求的文件，不预设抽象层 |
| **C4 Model** (Brown, 2018) | 四层架构可视化：Context → Container → Component → Code | design.md 按 C4 层级组织：系统全景 → 子项目容器 → 模块组件 → 关键代码 |

**Unix Philosophy 在脚手架中的具体体现**：

```
"做一件事做好" → 每个文件只有一个职责（一个 model / 一个 service / 一个 handler）
"组合优于继承" → 小模块通过 import/require 组合，不用大型框架基类
"文本是通用接口" → JSON 作为层间合约（product-map → spec → scaffold）
"快速原型" → mock-server 先行，前端不等后端
"沉默是金" → 脚手架只生成必要文件，不加冗余注释
```

**参考文献**：
- Martin, R. C. (2017). *Clean Architecture*. Prentice Hall
- Martin, R. C. (2003). *Agile Software Development: Principles, Patterns, and Practices*
- Richardson, L. (2008). *Justice Will Take Us Millions of Intricate Moves* (REST Maturity Model)
- Codd, E. F. (1970). *A Relational Model of Data for Large Shared Data Banks*
- Patton, J. (2014). *User Story Mapping*. O'Reilly Media
- Hunt, A. & Thomas, D. (1999). *The Pragmatic Programmer*. Addison-Wesley
- Dijkstra, E. W. (1974). *On the Role of Scientific Thought* (Separation of Concerns)
- Raymond, E. S. (2003). *The Art of Unix Programming*. Addison-Wesley
- Cockburn, A. (2005). *Hexagonal Architecture* (Ports and Adapters)
- Gabriel, R. P. (1989). *Worse is Better*. https://www.dreamsongs.com/WorseIsBetter.html
- Jeffries, R. (1999). *You Aren't Gonna Need It* (XP Practice)
- Brown, S. (2018). *The C4 Model for Visualising Software Architecture*. https://c4model.com

---

### 尾段：验证与交付（seed-forge + e2e-verify + product-verify）

> 核心问题：如何系统性地验证跨端业务完整性？

**指导理论**：

| 理论/框架 | 核心主张 | 在 验证阶段 中的落地 |
|-----------|---------|---------------------|
| **Test Pyramid** (Cohn, 2009) | 底层多单元测试、中层集成测试、顶层少 E2E | B5 Testing 按金字塔分层；e2e-verify 仅覆盖跨端关键路径 |
| **Test Trophy** (Dodds, 2019) | 集成测试投入最多，比单元测试更有价值 | 跨端场景来自 business-flows 实际业务流，非人为编造 |
| **Contract Testing** (Pact) | 消费者驱动的契约测试，验证 API 双方一致 | 前端→后端 API 调用的数据结构一致性验证 |
| **BDD** (North, 2006) | Given/When/Then 描述行为，场景来自业务 | E2E 场景从 business-flows 推导，步骤对应业务行为 |
| **Boundary Value Analysis** (Myers, 1979) | 测试边界条件比测试中间值更能发现缺陷 | seed-forge 生成边界数据（空值、极值、特殊字符） |
| **Equivalence Partitioning** (Myers, 1979) | 将输入域划分为等价类，每类取一个代表测试 | seed-forge 按角色/状态生成代表性数据集 |
| **Shift-Left Testing** (Forrester, 2016) | 尽早测试，缺陷发现越早修复成本越低 | mock-server 阶段即可运行前端 E2E；不等后端完成 |
| **ATDD** (Beck, 2003) | 验收测试驱动开发，先写验收条件再实现 | product-verify 基于 use-case 验收条件逐条验证 |
| **Heuristic Evaluation** (Nielsen, 1994) | 10 条启发式原则评估可用性 | product-verify 静态扫描检查 UI 可用性问题 |

**参考文献**：
- Cohn, M. (2009). *Succeeding with Agile*. Addison-Wesley
- Dodds, K. C. (2019). *Write Tests. Not Too Many. Mostly Integration.*
- North, D. (2006). *Introducing BDD*. Better Software
- Myers, G. J. (1979). *The Art of Software Testing*. Wiley
- Claessen, K. & Hughes, J. (2000). *QuickCheck: A Lightweight Tool for Random Testing*
- Nielsen, J. (1994). *Usability Engineering*. Morgan Kaufmann
- Beck, K. (2003). *Test-Driven Development: By Example*. Addison-Wesley

---

## 动态趋势补充机制

每个阶段在执行时，除了引用经典理论，还应通过 WebSearch 补充最新实践：

### 搜索策略

```
每阶段提供 2-3 组搜索关键词模板
优先级:
  P1 — 官方文档/规范（framework docs, RFC, spec）
  P2 — 知名作者博客（Martin Fowler, Kent C. Dodds, Dan Abramov 等）
  P3 — 技术媒体（InfoQ, ThoughtWorks Radar, dev.to 精选）
  P4 — 社区帖子（Stack Overflow, Reddit, 掘金, 知乎专栏）

采纳决策记录:
  ADOPT — 采纳，写入 spec/scaffold
  REJECT — 拒绝，记录原因
  DEFER — 暂缓，未来版本考虑
```

### 各阶段搜索关键词

| 阶段 | 搜索关键词模板 |
|------|---------------|
| project-setup | `"{tech-stack} project structure best practices {year}"`, `"monorepo vs polyrepo {language} 2025"`, `"{framework} clean architecture layout"` |
| design-to-spec | `"{framework} API design patterns"`, `"{ORM} database schema design"`, `"REST API naming conventions {year}"` |
| project-scaffold | `"{framework} starter template {year}"`, `"{framework} boilerplate best practices"`, `"{tech-stack} recommended packages {year}"` |
| seed-forge | `"{ORM} seed data strategies"`, `"realistic test data generation {language}"` |
| e2e-verify | `"Playwright cross-project E2E {year}"`, `"Patrol Flutter integration testing"`, `"contract testing {framework}"` |
| product-verify | `"automated acceptance testing {framework}"`, `"Lighthouse CI best practices {year}"` |

### 趋势来源共享

```
.allforai/project-forge/trend-sources.json

[
  {
    "phase": "project-setup",
    "topic": "Go project layout",
    "title": "Standard Go Project Layout",
    "url": "https://github.com/golang-standards/project-layout",
    "source_level": "P2",
    "published_at": "2024-01-15",
    "adoption": "ADOPT",
    "reason": "Go 社区广泛接受的目录结构标准"
  }
]
```

---

## Unix 编程哲学在 Dev Forge 中的全面应用

Unix Philosophy 不仅是 project-setup 的拆分依据，而是贯穿所有阶段的工程哲学。

### 九条 Unix 原则 × Dev Forge 映射

| # | Unix 原则 | 原文 (McIlroy / Raymond) | Dev Forge 落地 |
|---|----------|------------------------|----------------|
| 1 | **做一件事做好** | "Make each program do one thing well" | 子项目单一职责、原子任务 1-3 文件、每文件单一关注 |
| 2 | **组合** | "Expect the output of every program to become the input to another" | `.allforai/` JSON 产物是层间合约，上游输出 = 下游输入 |
| 3 | **快速原型** | "Build a prototype as soon as possible" | mock-server 先行，前端不等后端，scaffold 快速生成骨架 |
| 4 | **文本流** | "Use text as the universal interface" | JSON (机器) + Markdown (人类) 双格式，文本驱动全流程 |
| 5 | **沉默是金** | "When a program has nothing surprising to say, it should say nothing" | 脚手架不加冗余注释，只生成必要文件 |
| 6 | **最小意外** | "Follow the Rule of Least Surprise" | 命名约定统一、目录结构可预测（Convention over Configuration） |
| 7 | **经济性** | "Programmer time is more expensive than machine time" | 模板驱动生成节省手工编码时间，自动化验证代替人工检查 |
| 8 | **可修复** | "Design for failure; make recovering easy" | E2E 失败分类（FIX/ENV/DEFER）、resume 断点续作 |
| 9 | **透明** | "Design for visibility to make inspection and debugging easier" | forge-decisions.json 记录全程决策，build-log.json 追踪进度 |

### Raymond 补充原则

| 原则 | Dev Forge 落地 |
|------|----------------|
| **模块化** (Modularity) | Monorepo 中子项目隔离，shared-types 显式共享 |
| **清晰** (Clarity) | 代码胜于技巧 — scaffold 生成简单直观的代码 |
| **可扩展** (Extensibility) | 模板库可自由新增技术栈，不改核心流程 |
| **生成** (Generation) | 高层描述（product-map）→ 自动生成低层代码（scaffold） |
| **多样** (Diversity) | 支持 16 种技术栈，不强制统一 |

**参考文献**：
- McIlroy, M. D. (1978). *Unix Time-Sharing System: A Retrospective*. Bell System Technical Journal
- Raymond, E. S. (2003). *The Art of Unix Programming*. Addison-Wesley
- Salus, P. H. (1994). *A Quarter Century of UNIX*. Addison-Wesley
- Pike, R. (1989). *Notes on Programming in C* (simplicity, clarity)

---

## 信息保真增强（引用）

Dev Forge 复用 product-design-skill 的信息保真机制：

→ 详见 `product-design-skill/docs/information-fidelity.md`

在 Dev Forge 中的最小落地：
- **4D 信息卡**：每个关键决策包含 结论 + 依据 + 约束 + 决策理由
- **decision_rationale**：project-manifest.json 和 forge-decisions.json 中记录
- **source_refs**：趋势搜索的 URL 引用
