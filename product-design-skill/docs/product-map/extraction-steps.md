# Extraction Steps (Steps 0-2)

> Part of the **product-map** skill. Loaded by the orchestrator at runtime.

---

## Step 0: 项目画像

两类输入并行，相互补充：

| 类型 | 来源 | 说明 |
|------|------|------|
| 工程输入 | 代码（路由、菜单、权限配置、页面组件） | 了解项目现状，提取已有功能点 |
| 产品输入 | PRD、用户故事、原型图描述、PM 口述 | 补充业务语义，确认方向，标记差距 |

代码告诉我们**现在有什么**，PM 确认**应该有什么**。两者的差距就是需要改进的方向。

读取代码中的路由配置、菜单定义、权限枚举和守卫，将工程结构转换为产品语言：

- 有哪些功能模块（菜单项 → 功能区）
- 有哪些用户角色（权限枚举 → 角色草稿）
- 大致的操作入口分布

**规模判定**：统计代码中的路由/API 端点/菜单项总数，按规模适配表判定产品规模（小型/中型/大型）。在画像摘要中明确告知用户：「本产品预估 X 个任务，属于{规模}产品，后续将采用{交互策略}」。

**Fallback**：若代码中找不到路由配置、菜单定义或权限枚举（如纯后端服务、非标准框架），则切换为用户访谈模式 -- 直接询问用户描述产品的主要模块、角色和功能，手动构建初始画像。标记 `analysis_mode: "interview"` 以区别于代码分析结果。

若用户提供 PRD 或原型图描述，同步读取，标记代码中尚未实现的功能模块（`status: user_added`）和已废弃的模块（`status: user_removed`）。

生成 `role-profiles.json` **草稿**（仅在对话中展示，Step 1 用户确认后才写入磁盘）。

**竞品提问**（画像确认前，先问两个问题）：

> 1. 这个产品主要对标哪些竞品？（例如：Shopify、有赞、微盟；或「暂时没有参照」也可以）
> 2. 对比维度是什么？（平台功能对标 / 用户体验对标 / 商业模式对标 / 全方位对标）

根据用户回答：
- **有竞品**：记录名字列表和对比维度，生成 `competitor-profile.json` 草稿（写名字 + `comparison_scope`），Step 9 再做 Web 搜索
- **无竞品**：记录 `competitors: []`，`analysis_status` 设为 `"skipped"`，Step 9 只做完整性 + 冲突校验，跳过竞品差异部分

生成 `competitor-profile.json` 草稿：

> 以下示例以虚构业务为背景，仅用于说明输出格式。实际内容由 product-map 分析结果决定，不限行业。

```json
{
  "competitors": ["Shopify", "有赞"],
  "comparison_scope": "platform_features",
  "analysis_status": "pending",
  "analyzed_at": null
}
```

> 草稿此时只写入名字和对比维度，Step 9 执行完后补全竞品功能数据，`analysis_status` 改为 `"completed"`。
> `analysis_status` 取值：`"pending"`（待分析）/ `"skipped"`（无竞品，Step 9 跳过竞品差异）/ `"completed"`（已完成）
> `comparison_scope` 取值：`"platform_features"`（平台功能对标）/ `"user_experience"`（用户体验对标）/ `"business_model"`（商业模式对标）/ `"comprehensive"`（全方位对标）

**用户确认**：这个项目的功能全景对吗？有没有遗漏的模块？规模判定是否合理？

---

## Step 1: 用户角色识别

**角色粒度原则（必读）**：产品地图使用「概念层合并角色」，不使用 RBAC 的细分权限角色。

| 类型 | 示例 | 用途 |
|------|------|------|
| **概念层角色**（产品地图使用） | 终端用户 / 内容提供者 / 平台管理员 | 任务归属、业务流节点、频次/风险分析 |
| **实现层角色**（RBAC 权限系统） | 内容编辑 / 审核员 / 客服 | 权限控制、屏幕设计，不进入产品地图主结构 |

若代码中存在细粒度的 RBAC 角色（如内容编辑/内容审核员/运营专员/客服专员），**聚合**为对应的概念层角色，用 `impl_roles` 字段记录映射关系，不在主角色列表中逐一拆分。

若无 `product-concept.json`，按业务端分组聚合：用户侧 / 提供者侧 / 平台侧（超管 + 受限管理员），不按权限点一对一拆分。

从代码中的权限枚举、路由守卫、角色配置推导角色，补充业务语义：

> 以下示例以虚构业务为背景，仅用于说明输出格式。实际内容由 product-map 分析结果决定，不限行业。

```json
{
  "roles": [
    {
      "id": "R001",
      "name": "客服专员",
      "description": "处理客户投诉、异常申请、操作异常",
      "permission_boundary": ["异常处理", "记录查询", "用户信息查询（脱敏）"],
      "kpi": ["处理时效 < 2h", "处理错误率 < 0.1%"],
      "audience_type": "professional",
      "status": "confirmed"
    }
  ]
}
```

**`audience_type` 字段**（recommended）：

标记角色面向的用户群体，供 experience-map 选择交互设计标准。

| 值 | 含义 | 适用场景 |
|----|------|----------|
| `consumer` | 消费侧用户（C端） | App 用户、网站访客、终端用户 |
| `professional` | 专业/内部用户（B端） | 运营后台、管理员、服务提供者、客服 |

**推导规则**（按优先级）：
1. 若 `role-value-map.json` 存在且角色有 `role_type`：`consumer` → `consumer`，`producer` / `admin` → `professional`
2. 若无 product-concept，Step 1 确认时询问用户标注
3. 未标注时缺省，下游技能使用 default 阈值（v2.3.0 行为不变）

PM 可补充代码未体现的角色（业务上存在但权限系统未区分），也可删除已废弃角色。

**用户确认**：角色列表完整吗？职责描述准确吗？权限边界有没有遗漏？

输出：`.allforai/product-map/role-profiles.json`

---

## Step 2: 核心任务提取

<!-- NOTE: This step has multiple sub-concerns (field layering, task schema, category rules,
     config levels, self-audit, debug tasks, closed-loop audit); the LLM should process
     them sequentially, not all at once. -->

按角色展开，从路由、菜单项、权限点提取任务，转换为业务语言。

### 任务字段分层

字段分为 **required**（必填，缺失视为质量问题）和 **recommended**（推荐，缺失仅提示）：

| 层级 | 字段 | 说明 |
|------|------|------|
| **required** | `id`, `name`, `owner_role`, `frequency`, `risk_level`, `main_flow`, `status`, `category` | 任务身份和核心属性，缺失将导致下游技能无法正常工作 |
| **recommended** | `value`, `approver_role`, `viewer_roles`, `cross_dept`, `cross_dept_roles`, `sla`, `prerequisites`, `rules`, `config_items`, `inputs`, `outputs`, `exceptions`, `audit`, `acceptance_criteria` | 丰富任务语义，提升地图质量，但非强制 |

**生成策略**：
- **小型产品（<=30 任务）**：尽量填写所有字段，包括 recommended
- **中型/大型产品（>30 任务）**：优先保证所有 required 字段完整；recommended 字段按优先级填写：高频+高风险任务填写全部 recommended 字段，中低频任务至少填写 `rules` 和 `exceptions`

### 任务 Schema

> 详见 ${CLAUDE_PLUGIN_ROOT}/docs/schemas/task-schema.md

### 任务分类规则（category）

每个任务必须标注 `category` 字段，分为两类：

| category | 含义 | 判定标准 | 典型模块 |
|----------|------|---------|---------|
| `basic` | 基本功能 -- 换个产品一样需要 | 认证/账户/支付/管理/支持/引导/通知/反馈 | 注册登录、个人设置、订阅付费、系统管理、用户支持 |
| `core` | 核心功能 -- 产品差异化价值 | 本产品独有或核心的业务能力 | 学习/对话/AI/内容创作/数据分析/游戏化 |

**判定优先级**（按顺序匹配，首条命中即停）：

1. 认证相关（注册/登录/重置密码/注销/SSO）→ `basic`
2. 支付相关（订阅/购买/退款/续费/账单）→ `basic`
3. 系统管理（配置参数/权限角色/用户账户管理）→ `basic`
4. 通用支撑（通知中心/意见反馈/新手引导/个人设置）→ `basic`
5. 其余 → `core`

**输出拆分**：Step 2 完成后，除 `task-inventory.json`（全量）外，额外生成：
- `task-inventory-basic.json` -- 仅含 `category=basic` 的任务
- `task-inventory-core.json` -- 仅含 `category=core` 的任务

两个拆分文件与全量文件共享同一 schema，仅在顶层增加 `"category"` 和 `"description"` 字段标识归属。

### 配置级别（config_level）

任务的 `rules` 中涉及数值、策略、阈值等参数时，使用 `config_items` 字段标注每个可配置参数的实现级别。不同级别决定了参数的改动成本和管理方式。

| config_level | 含义 | 改动成本 | 示例 |
|-------------|------|----------|------|
| `frontend_hardcode` | 界面写死 | 前端发版 | 注册方式列表、排行榜维度、可选语言 |
| `code_constant` | 代码写死 | 后端发版 | AI难度适配范围、排行榜周期 |
| `config_file` | 启动配置文件（.env / config.yaml） | 重启/重新部署 | API Key、密码策略、支付渠道、推荐算法权重 |
| `general_config` | 通用配置模块（增删改查） | 热更新，运营后台可调 | 免费额度、告警阈值、审核时限、连胜恢复次数 |
| `dedicated_config` | 专用配置模块（专属管理界面） | 热更新，需专属界面 | 成就模板管理、订阅方案配置、场景难度定义、推送文案 |

**`config_items` 字段 Schema**：

```json
"config_items": [
  {
    "param": "参数名",
    "current": "当前值或待定",
    "config_level": "general_config"
  }
]
```

**生成策略**：
- 遍历每个任务的 `rules`，识别其中的数值/策略/阈值
- 对每个可配置参数，与用户确认其 config_level
- `task-inventory.json` 的顶层增加 `config_level_summary` 统计各级别数量
- Step 9 校验时，检查所有 `general_config` 参数是否被 R007（或同等管理员角色）的「配置系统参数」任务覆盖

### 自审计子步骤（中型/大型产品强制执行）

任务清单初步生成后，执行代码路由审计：

1. **扫描代码路由/Handler**：遍历后端路由定义（如 Go 的 `router.Group` / Express 的 `app.get` / Next.js 的 `app/` 目录），提取所有 API 端点
2. **扫描前端菜单/页面**：遍历前端菜单配置和页面组件，提取所有用户可访问的操作入口
3. **交叉比对**：将扫描结果与已生成的任务清单比对，标记：
   - **代码有 → 任务无**：遗漏任务，自动补充并标记 `"source": "code_audit"`
   - **任务有 → 代码无**：用户期望功能，保留并标记 `status: "user_added"`
4. **展示审计结果**：在用户确认前，展示「自审计发现 X 个代码中存在但初始遗漏的功能」

审计结果记入 decisions.json，`decision` 类型为 `"auto_audited"`。

### 调试支持任务（不可遗漏）

调试与开发辅助功能是产品的组成部分，必须纳入任务清单，不可因"纯工程工具"理由跳过。常见调试支持任务包括：

| 类别 | 示例 | 归属角色 |
|------|------|---------|
| 健康检查 | 查看系统健康状态、服务存活探针 | 管理员/运维 |
| 日志与监控 | 查看应用日志、追踪请求链路、查看错误报告 | 管理员/运维 |
| 特性开关 | 管理 Feature Flag、灰度发布控制 | 管理员 |
| 测试工具 | 重置测试数据、触发测试通知、模拟业务事件 | 开发/管理员 |
| 调试面板 | 查看队列状态、查看缓存状态、强制刷新配置 | 管理员/运维 |
| 数据修复 | 手动补偿数据、重触发失败任务 | 管理员/运维 |

**纳入规则**：
- 归属管理员角色（R003/R004 或专属运维角色），统一归入 `"module": "开发支持"` 或 `"module": "系统运维"`
- `frequency` 标注为「低」，`risk_level` 按实际情况标注（日志查看=低，数据修复=高）
- 自审计扫描路由时，`/debug/`、`/admin/dev/`、`/internal/`、`/health`、`/metrics` 路径下的端点均视为调试支持任务
- product-map 阶段必须完整收录

### 闭环完整性审计（所有模式必须执行）

**原理**：产品中的每个功能都存在于大大小小的循环中，不存在孤立的功能。闭环思维要求：对每个任务，追问它在循环中的位置，检查循环是否完整。

**四类闭环**：

| 闭环类型 | 追问 | 示例 |
|---------|------|------|
| **配置闭环** | 这个功能靠什么运行？谁来配置它？ | 有「使用X」就要有「配置X」 |
| **监控闭环** | 这个功能运行得好不好？谁来看？ | 有「执行操作」就要有「查看效果/数据」 |
| **异常闭环** | 这个功能失败了怎么办？谁来处理？ | 有「正常路径」就要有「异常处理/回退」 |
| **生命周期闭环** | 这个东西创建了，最终去哪？ | 有「创建」就要有「归档/过期/清理」 |

**审计方法**：

1. 遍历 `product_mechanisms` 中提到的每个能力/服务/技术
2. 遍历已生成任务清单中的每个功能任务
3. 对每个功能任务，逐一追问四类闭环：
   - **配置闭环**：该功能依赖的外部服务/能力/算法，是否有对应的配置管理任务？
   - **监控闭环**：该功能的运行效果，是否有对应的数据查看/统计任务？
   - **异常闭环**：该功能失败时的处理，是否体现在某个任务的 main_flow 或 exceptions 中？
   - **生命周期闭环**：该功能产生的数据/内容，是否有过期/清理/归档机制？
4. 缺失的闭环环节 → 补充对应任务或在已有任务中补充 main_flow 步骤
5. 展示：「闭环审计：X 个任务已检查，Y 个闭环缺失已补充」

**用户确认**：任务清单完整吗？审计发现的遗漏是否都应纳入？

输出：`.allforai/product-map/task-inventory.json`（全量）、`.allforai/product-map/task-inventory-basic.json`（基本功能）、`.allforai/product-map/task-inventory-core.json`（核心功能）
