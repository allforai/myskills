---
name: deadhunt
description: >
  This skill should be used when the user asks to find dead links, broken routes, or 404 errors
  in a web or mobile project; hunt ghost features or unused API endpoints; verify CRUD completeness
  for each module; check field consistency across UI, API, Entity, and DB layers; scan navigation
  for unreachable pages; or run a product integrity scan. Typical requests include "find broken links
  in my project", "check if all routes work", "scan for 404s", "verify CRUD coverage",
  "check field names across frontend and backend", "validate my project", "hunt dead links",
  "帮我找死链", "验证我的项目", "检查字段一致性", "做产品完整性扫描", "做增量验证".
  Supports multi-client architectures (Admin/Merchant/Customer) with bidirectional analysis.
  Works with React, Vue, Angular, Next.js, Flutter, React Native, and WeChat Mini Programs.
version: "1.9.0"
---

# DeadHunt

> 猎杀死链，验证产品完整性

## 目标

在 Playwright 等自动化测试之后、人工验收之前，系统化地发现：

1. **死链 (Dead Links)** — 按钮、菜单、链接点击后 404 或空白页
2. **模块不完整 (Incomplete Modules)** — 缺少必要的增删改查入口
3. **幽灵功能 (Ghost Features)** — 后端已实现但界面上不可达的功能
4. **废弃残留 (Stale UI)** — 功能已砍/废弃但入口未清理
5. **导航不可达 (Unreachable Routes)** — 路由已注册但界面上无入口可达
6. **权限遮蔽 (Permission Blindspots)** — 因权限配置导致功能入口被隐藏
7. **数据展示异常 (Data Display Issues)** — 页面能打开但数据显示不正确（空列表、缺字段、乱码）
8. **流程断裂 (Broken Flows)** — 多步操作中某一步中断（如新增→保存→返回列表看不到）
9. **环境一致性 (Environment Parity)** — 开发/测试/生产环境之间的差异导致的问题

---

## 快速开始

> 详见 `${CLAUDE_PLUGIN_ROOT}/docs/quick-start.md`

**三步跑通第一次验证：**

1. **静态分析（不需要启动应用）** — 对 Claude 说：`请用 deadhunt 技能对我的项目做静态分析。项目路径是 /path/to/my-project。`
2. **确认项目概况** — Claude 生成 `validation-profile.json` 后请你确认模块分类
3. **深度测试（需要启动应用 + 登录）** — 对 Claude 说：`请用 deadhunt 技能做深度测试。应用跑在 http://localhost:3000。测试账号：admin / 123456。`

文件结构见 `${CLAUDE_PLUGIN_ROOT}/docs/quick-start.md` 的"文件结构"章节。

---

## 工作流总览

> 详细的状态检测、流程决策逻辑和对话模式见 `${CLAUDE_PLUGIN_ROOT}/docs/workflow.md`

```
首次使用:                           后续使用:

  Phase 0: 项目分析 ──→ 保存          检测 .allforai/deadhunt/output/
  (Claude 自动初始化)                  (直接跑)
       ↓                  ↓                ↓
  Phase 1: 静态分析      ↓          有 validation-profile.json?
       ↓                  ↓            ├── 有 → 跳过 Phase 0，直接用
  Phase 2: 制定测试计划   ↓            └── 没有 → 走首次流程
       ↓                  ↓
  Phase 3: 深度测试      ↓          有 .auth/*.json?
       ↓                  ↓            ├── 有 → 跳过登录，直接用
  Phase 4: 报告          ↓            └── 没有 → 重新登录
                         ↓
              .allforai/deadhunt/output/    有 上次报告?
              (所有状态都保存在这里)    ├── 有 → 增量对比，只报告变化
                                     └── 没有 → 全量报告
```

核心原则：**初始化一次，后续复用**。Profile、auth state、上次报告都持久保存在 `.allforai/deadhunt/output/`。

---

### Phase 0: 项目分析

> 先理解项目，再做验证。这是最关键的一步。
> 详见 `${CLAUDE_PLUGIN_ROOT}/docs/phase0-analyze.md`

识别技术栈、模块类型、多端架构（角色+平台定位），输出 `validation-profile.json` 请用户确认。

**模块类型速查：**

| 模块类型 | CRUD 要求 | 示例 |
|---------|----------|------|
| 标准业务模块 | 完整 CRUD | 用户管理、商品管理 |
| 配置模块 | CR(U) | 系统设置 |
| 只读模块 | R | 操作日志、统计报表 |
| 工作流模块 | CRUD + 状态操作 | 审批流、工单 |
| 跨端协作模块 | 按当前端职责判定 | 用户反馈(App创建+后台管理) |

**多端角色模型：**
```
┌─────────────────────────────────────────────────────────────────────────┐
│                           共享后端 API                                   │
└──┬──────────┬───────────┬──────────┬──────────┬──────────┬─────────────┘
   │          │           │          │          │          │
┌──▼──┐  ┌───▼───┐  ┌────▼───┐ ┌───▼───┐ ┌───▼───┐ ┌───▼────┐
│Admin│  │商户后台│  │客户 Web│ │客户 H5│ │客户App│ │客户小程序│
└─────┘  └───────┘  └───────┘ └──────┘ └──────┘ └───────┘
角色:超管  角色:商户   角色:客户  角色:客户  角色:客户  角色:客户
平台:web  平台:web   平台:web  平台:h5  平台:app 平台:miniprogram
                    ╰──────── 同角色 peer group ──────────╯
                    核心功能应一致，差异来自平台能力
```

---

### 登录认证策略

> 详见 `${CLAUDE_PLUGIN_ROOT}/docs/auth-strategy.md`

原则：**绝不侵入项目已有的 Playwright 配置和测试**。验证用独立的 `.allforai/deadhunt/playwright.config.ts`。

---

### Phase 1: 静态分析

> 不运行应用，仅通过代码分析发现问题。**核心原则：双向分析**
> 详见 `${CLAUDE_PLUGIN_ROOT}/docs/phase1-static.md`

```
方向 A: 界面 → 数据 (Forward)          方向 B: 数据 → 界面 (Reverse)
"界面上有的，后面能通吗？"              "后端有的，界面上找得到吗？"

两方向交叉得出四种状态：
┌──────────────┬──────────────────┬─────────────────────┐
│              │ 数据层存在        │ 数据层不存在          │
├──────────────┼──────────────────┼─────────────────────┤
│ 界面有入口    │ ✅ 健康           │ 🔴 死链 (点了就 404)  │
│ 界面无入口    │ 🔴 幽灵功能       │ ✅ 正常(未实现)       │
│              │ (不可达的功能)     │                     │
└──────────────┴──────────────────┴─────────────────────┘
```

6 步分析（路由、链接、CRUD、API 反向、路由反向、数据模型反向）+ 多轮收敛（模式学习→交叉验证→扩散搜索，最多 10 轮）。

---

### Phase 2: 制定测试计划

> 基于静态分析结果，生成 `test-plan.json`。
> 详见 `${CLAUDE_PLUGIN_ROOT}/docs/phase2-plan.md`

测试用例生成规则：
1. 读取 `crud_by_client` 中当前端的配置，只生成该端应有操作的测试用例
2. 对每个模块，按该端的 `crud` 字段生成对应用例
3. 对每个 `extra_actions` 生成额外操作验证用例
4. 对静态分析发现的死链、孤儿路由，各生成验证用例
5. 对导航菜单所有入口，生成遍历测试用例
6. 跨端一致性和全局覆盖率检查（批量模式）

---

### Phase 3: 深度测试

> 通过 Playwright（Web/H5）或 Patrol（Flutter）自动化执行测试。
> 详见 `${CLAUDE_PLUGIN_ROOT}/docs/phase3-test.md`（索引文件，按需加载子文件）

**3 级验证策略：**

| 级别 | 时间 | 内容 | 适用场景 |
|------|------|------|---------|
| Level 1: 快速扫描 | 30 秒 | 只跑静态分析 | 每次 git commit 前 |
| Level 2: 标准验证 | 2-3 分钟 | 静态 + 浏览器快速遍历 | 每日开发结束前 |
| Level 3: 完整验证 | 10-15 分钟 | 全部 Phase + CRUD 闭环 | 发版前 |

**死链意图判定（发现 404 后的分类）：**

| 意图 | 含义 | 行动 |
|------|------|------|
| FIX | 后端/路由坏了 | 修复代码 |
| CLEAN | 功能已废弃 | 删除入口 |
| HIDE | 功能开发中 | 隐藏入口 |
| PERM | 权限控制失效 | 修复权限 |

5 层 404 扫描（导航→交互→API→资源→边界）+ CRUD 闭环测试 + 数据展示验证 + 多轮收敛。

---

### Phase 4: 报告生成

> 详见 `${CLAUDE_PLUGIN_ROOT}/docs/phase4-report.md`

**报告内容：**
- 基线保存 & 增量对比（新增/已修复/未变化）
- 单端报告 `validation-report-{client_id}.md`：按意图分类的死链、模块不完整、跨端正常分工、警告
- 跨端汇总报告 `validation-report-summary.md`（批量验证时）：全局 CRUD 覆盖率、Peer Group 一致性
- 修复任务清单 `fix-tasks.json`：可导入项目管理工具

**报告摘要示例：**
```
📊 验证报告摘要：
- 🔴 FIX (该修): 8 个
- 🟡 CLEAN (该删): 7 个
- 🟠 HIDE (该藏): 4 个
- 🔵 PERM (改权限): 2 个
- ❓ UNKNOWN (需确认): 2 个
- ✅ 正常: 39 个
```

---

### Phase 5: 补充测试

> 报告输出后，补充测试用例。
> 详见 `${CLAUDE_PLUGIN_ROOT}/docs/phase5-supplement-test.md`

**做什么：**
1. 检测项目现有测试框架（vitest/jest/playwright/cypress）
2. 分析现有测试的覆盖盲区（无测试模块、CRUD 不全、关键流程无 E2E）
3. 为覆盖盲区 + 本次发现的问题生成测试用例
4. 按项目现有风格写测试，不修改已有测试

**测试文件命名：**
- `deadhunt-regression.{test|spec}.ts` — 针对本次发现的问题的回归测试
- `deadhunt-coverage.{test|spec}.ts` — 补全现有测试覆盖盲区的测试
- `deadhunt-regression.patrol_test.dart` — Flutter 端回归测试（Patrol 格式）
- `deadhunt-coverage.patrol_test.dart` — Flutter 端覆盖盲区测试（Patrol 格式）

---

## 使用方式

### 场景 1: 新项目第一次验证

```
请用 deadhunt 技能验证我的项目。
项目路径是 /path/to/project。
这是 admin 后台，运行在 http://localhost:3000。
测试账号: admin / admin123。
```

### 场景 2: 多端项目

```
请用 deadhunt 技能验证我的项目。项目路径是 /path/to/monorepo。
需要验证:
- Admin 后台 (apps/admin)，运行在 http://localhost:3000，账号 admin/123
- 商户后台 (apps/merchant)，运行在 http://localhost:3001，账号 merchant/123
- 客户 H5 (apps/h5)，运行在 http://localhost:3002，账号 user/123
Flutter App 跳过。
```

### 场景 3: 快速扫描（最快，30 秒，不需要启动应用）

```
请用 deadhunt 技能做快速扫描。
项目路径是 /path/to/project。
```

### 场景 4: 标准验证（默认，2-3 分钟）

```
请用 deadhunt 技能验证我的项目。
项目路径是 /path/to/project。
应用跑在 http://localhost:3000。
```

### 场景 5: 完整验证（发版前）
```
请用 deadhunt 技能做完整验证。
项目路径是 /path/to/project。
应用跑在 http://localhost:3000，账号 admin/123。
包括 CRUD 闭环测试和多端一致性检查。
```

### 场景 6: 已有 profile，只跑深度测试

```
请用 deadhunt 技能做深度测试。
项目路径是 /path/to/project。
项目概况文件在 .allforai/deadhunt/output/validation-profile.json。
验证 admin 后台，运行在 http://localhost:3000。
```

### 场景 7: 增量验证（只验证改动的部分）
```
请用 deadhunt 技能做增量验证。
项目路径是 /path/to/project。
只验证最近一次提交变更涉及的模块。
```

### 场景 8: 上次报告有问题，重新验证某个模块

```
请用 deadhunt 技能重新验证"订单管理"模块。
项目路径是 /path/to/project。
运行在 http://localhost:3000，账号 admin/123。
上次报告说订单的删除入口缺失，我已经修了，请验证。
```

### 场景 9: 检查前后端字段一致性

```
/deadhunt:fieldcheck
/deadhunt:fieldcheck frontend --module user
```

纯静态分析，不需要启动应用。检查 UI 显示字段、API 接口字段、Entity 字段、数据库列名的全链路一致性。

---

## 文件结构

```
your-project/
└── .allforai/deadhunt/
    ├── playwright.config.ts          # 验证专用配置（不侵入项目原有 Playwright 配置）
    ├── .auth/                        # 验证专用登录状态
    │   └── admin.json
    └── output/                       # 验证产出（自动生成）
        ├── validation-profile.json   # 项目概况（初始化后持久复用）
        ├── static-analysis/          # Phase 1 静态分析结果
        ├── tests/                    # 生成的验证测试脚本
        ├── dead-links-report.json    # 死链报告
        ├── validation-report-*.md    # 可读报告（按客户端分文件）
        ├── fix-tasks.json            # 修复任务清单
        └── field-analysis/           # /fieldcheck 输出
            ├── field-profile.json    # 跨层字段提取结果
            ├── field-mapping.json    # 字段对应关系
            ├── field-issues.json     # 问题清单
            └── field-report.md       # 可读报告
```

---

## FAQ

> 详见 `${CLAUDE_PLUGIN_ROOT}/docs/faq.md`

---

## 注意事项

### 验证前检查清单 (Pre-flight Checklist)

开始验证之前必须确认的事项，否则会产生大量误报：

```
□ 测试环境应用已启动且可访问
□ 测试数据库已初始化（有种子数据或测试数据）
□ 测试账号可用（建议用最高权限账号）
□ 后端 API 服务已启动
□ 没有未完成的数据库迁移
□ 环境变量/配置文件已正确设置
□ 如有微服务依赖，确认依赖服务都在线
□ 确认没有人正在同一环境做部署或数据清理
□ 测试环境关闭了验证码/人机验证
□ 确认 mock 数据 / feature flag 的状态与生产一致（除非刻意不同）
```

### 关键原则

1. **先静态后动态**：静态分析成本低、覆盖广，应先执行
2. **用户确认不可省**：模块分类必须经用户确认，避免误判
3. **多端分工是误判最大来源**：如果模块的 CRUD 分布在多个客户端上（如 Flutter 创建 + 后台管理），当前客户端缺少某操作是正常的，不应报为问题
4. **区分角色差异和平台差异**：
   - **角色差异**（Admin vs 客户）→ 不同角色有不同操作，这是设计
   - **平台差异**（App 有扫码，Web 没有）→ 平台能力限制，不是缺失
   - **对等缺失**（H5 有退款但小程序没有）→ 同角色应一致，缺失就是 bug
5. **Peer Group 一致性检查**：同 `peer_group` 的客户端，核心功能（CRUD + 非平台专属的 extra_actions）必须一致。差异需与 `platform_capabilities` / `platform_limitations` 对照，能解释的是正常差异，不能解释的是缺失
6. **优先通过 API 层判断分工**：如果有 Swagger/OpenAPI 文档，对比 API 提供的操作 vs 当前端调用的操作，可以快速推断职责分工
7. **权限影响结果**：使用最高权限账号测试，避免权限遮蔽导致误报
8. **死链要判意图**：发现 404 不要无脑报"修复"——先判断是该修(FIX)、该删(CLEAN)、该藏(HIDE)还是改权限(PERM)
9. **数据依赖**：某些功能需要已有数据才能测试（如编辑、删除），需提前准备测试数据
10. **异步加载**：SPA 应用页面可能异步加载，等待 networkidle 或关键元素出现
11. **动态菜单**：部分系统菜单从后端动态获取，需要先登录才能获取完整菜单
12. **非 Web 端的测试方式**：Flutter 用 Patrol（`patrol test`）做深度测试，小程序用 `miniprogram-automator`。deadhunt Phase 3 已内置 Patrol 引擎支持，与 Playwright 并行执行。静态分析（Phase 1）和字段一致性检查（FieldCheck）对所有平台通用
13. **不确定就问用户**：任何无法自动判断的模块职责，都应标记 `needs_confirmation` 并询问用户，宁可多问不要误报

### 常见误报及规避

> 详见 `${CLAUDE_PLUGIN_ROOT}/docs/phase3-test.md` 和 `${CLAUDE_PLUGIN_ROOT}/docs/phase0-analyze.md` 中的详细误报场景和多端架构误判场景表。
