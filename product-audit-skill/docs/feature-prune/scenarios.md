# Step 1: 核心场景识别

> 先搞清楚用户拿这个产品做什么，再判断哪些功能该留。

---

## 1. 场景提取策略

场景是用户使用产品时的"做事目的"。提取场景有两条路径，优先文档驱动，无文档时降级到代码驱动。

### 1.1 文档驱动

从已有的需求文档中提取场景，这是最可靠的来源。

**扫描目标:**

| 文档类型 | 定位章节 | 解析方式 |
|----------|----------|----------|
| PRD / 需求文档 | `用户场景` / `User Stories` / `Use Cases` / `核心流程` | 每个章节标题（h2/h3）视为一个场景边界 |
| README | `功能` / `Features` / `What it does` | 将 bullet list 按相关性分组，每组归纳为一个场景 |
| OpenAPI / Swagger | `tags` 分组 | 每个 tag 视为一个场景候选 |

**解析规则:**

```
1. 定位 PRD 中标题含 "场景" / "Stories" / "Use Cases" / "流程" 的章节
2. h2 (##) 视为场景边界
3. h3 (###) 视为场景内的子流程
4. 该场景下提及的功能点 → 归入 core_features
5. 如果 PRD 无明确场景章节 → 退而求其次，用 h2 功能模块做分组推导
```

**README 分组推导:**

当 PRD 无场景章节，但 README 有功能列表时：

```
1. 提取 ## Features / ## 功能 下的 bullet list
2. 按关键词聚类:
   - "用户" + "注册" + "登录" + "权限" → 用户管理场景
   - "订单" + "下单" + "支付" + "退款" → 订单场景
   - "报表" + "统计" + "导出" + "图表" → 数据分析场景
3. 无法归类的功能项暂标 "待归类"，等后续映射阶段处理
```

### 1.2 代码驱动（No-Doc Fallback）

当 PRD、README 的功能章节、OpenAPI tags 均无有效场景信息时，从代码结构推导场景。

**推导信号（按信号强度排序）:**

| 信号来源 | 推导规则 | 示例 |
|----------|----------|------|
| 路由前缀 | 相同前缀的路由归为一个场景 | `/users/*` → 用户管理场景 |
| 模块目录 | `src/modules/` 或 `src/features/` 下的子目录 | `src/modules/order/` → 订单场景 |
| 菜单层级 | 顶层菜单项 → 场景，子菜单项 → 场景内功能 | 侧边栏 "订单管理" → 订单场景 |
| Controller 分组 | 同一 Controller 下的路由 | `OrderController` → 订单场景 |

**路由前缀聚类规则:**

```
1. 提取所有路由路径
2. 按第一段路径分组: /users/*, /orders/*, /settings/*
3. 每组视为一个场景候选
4. 路由数量 < 2 的分组标记为 "弱场景"，可能是独立功能而非场景
5. 嵌套路由的父路由优先作为场景边界
```

**模块目录聚类规则:**

```
1. 扫描 src/modules/*, src/features/*, src/domains/*, src/pages/* 的子目录
2. 每个子目录视为一个场景候选
3. 子目录下的文件数量反映场景复杂度
4. 仅含 1-2 个文件的目录 → 可能是辅助模块，不一定是独立场景
```

### 1.3 必须告知用户

当使用代码驱动时，**必须**输出以下提示：

```
⚠ 场景从代码结构推导而来，非来自需求文档。
推导来源：路由前缀 / 模块目录 / 菜单层级
置信度：低（code-derived）

请仔细确认以下场景划分是否符合实际业务逻辑。
代码结构不一定等于业务场景 — 技术模块可能不等于用户场景。
```

---

## 2. 场景结构

每个识别出的场景用以下结构描述：

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `id` | string | 场景唯一标识，S-XXX 格式 | `S-001` |
| `name` | string | 场景名称，面向业务含义 | `用户管理` |
| `description` | string | 用户在这个场景中要完成什么目标 | `管理员创建、编辑、禁用系统用户` |
| `user_role` | string | 执行该场景的用户角色 | `管理员` / `普通用户` / `访客` |
| `source` | string | 场景的来源位置 | `docs/prd.md:15` 或 `code-derived` |
| `core_features` | string[] | 直接服务于该场景的功能 ID 列表 | `["F-001", "F-002", "F-003"]` |
| `related_features` | string[] | 与该场景间接相关的功能 ID 列表 | `["F-012"]` |

### core_features vs related_features 的区分

```
core_features — 该场景的核心流程中必须用到的功能
  例: "订单场景" 的 core → 下单、支付、查看订单

related_features — 从该场景可达但非核心路径的功能
  例: "订单场景" 的 related → 导出订单报表、打印发票

判断标准:
  - 删掉 core_feature，场景的主要用户旅程断裂 → 必须是 core
  - 删掉 related_feature，场景的主要用户旅程不受影响 → 是 related
```

---

## 3. 功能-场景映射规则

将 Step 0 产出的功能清单（`feature-inventory.json` 中的每个 feature）映射到场景。这是场景识别的核心动作。

### 3.1 映射信号（按信号强度排序）

| 信号强度 | 映射方式 | 说明 | 示例 | 置信度 |
|----------|----------|------|------|--------|
| 最强 | 显式 PRD 引用 | PRD 中将功能明确归类在某个场景标题下 | PRD 的 "## 订单管理" 下列出 "订单导出" | `high` |
| 强 | 路由前缀匹配 | 功能的路由路径与场景的路由前缀一致 | `/users/create` → 用户管理场景 | `high` |
| 中 | 模块目录匹配 | 功能的实现文件位于场景对应的模块目录下 | `src/modules/order/export.ts` → 订单管理场景 | `medium` |
| 中 | 关键词重叠 | 功能名称包含场景的核心关键词 | 功能 "订单导出" 含关键词 "订单" → 订单管理场景 | `medium` |
| 弱 | 弱关键词匹配 | 功能名称与场景仅有间接关联 | 功能 "数据备份" 含 "数据" → 数据管理场景？ | `low` |

### 3.2 映射执行流程

```
对每个功能 F:
  1. 检查 PRD 中 F 是否出现在某个场景标题下 → 如果是，映射为 core，置信度 high
  2. 检查 F 的路由路径前缀是否与某个场景匹配 → 如果是，映射为 core，置信度 high
  3. 检查 F 的实现文件目录是否与某个场景模块匹配 → 如果是，映射为 core/related，置信度 medium
  4. 检查 F 的名称关键词是否与某个场景重叠 → 如果是，映射为 related，置信度 medium
  5. 如果以上均无匹配 → F 标记为 orphan，置信度 none
```

### 3.3 多场景映射

一个功能可以映射到多个场景。此时需要区分 primary（主要归属）和 secondary（次要归属）：

```
例: 功能 "用户权限配置"
  - primary: 用户管理场景（直接服务于用户管理）
  - secondary: 系统设置场景（也可以从设置入口到达）

映射规则:
  - 信号最强的场景 → primary
  - 其余场景 → secondary
  - 如果信号强度相同 → 按路由距离（路由路径的匹配深度）决定
```

### 3.4 置信度体系

| 置信度 | 含义 | 映射来源 | 处理方式 |
|--------|------|----------|----------|
| `high` | 映射关系明确，几乎不会错 | 显式 PRD 引用，或路由前缀精确匹配 | 直接采纳 |
| `medium` | 映射关系合理但可能有误 | 关键词重叠，或模块目录推断 | 采纳但标记，等用户确认 |
| `low` | 映射关系很弱，可能是噪音 | 仅弱关键词匹配 | 标记为待确认，可能是孤立功能 |
| `none` | 没有任何映射信号 | 无匹配 | 归入孤立功能列表 |

---

## 4. 孤立功能识别

完成映射后，所有 `confidence: none` 的功能进入 `orphan_features` 列表。这些功能没有归属任何场景，是 feature-prune 中最强的 CUT 信号。

### 4.1 孤立功能的含义

```
孤立功能 = 没有任何用户场景需要它

可能原因:
  1. 历史遗留 — 曾经有用，现在对应的场景已废弃
  2. 过度设计 — 开发时 "觉得以后会用到"，但实际无场景
  3. 技术债务 — 为某个一次性需求开发的功能，需求完成后未清理
  4. 映射遗漏 — 实际有场景，但映射信号太弱未检出（需用户确认排除）
```

### 4.2 孤立功能的处理

```
不要直接建议删除 — 先确认。

处理流程:
  1. 列出所有孤立功能，附带功能描述和实现文件
  2. 询问用户: "这些功能确实没有对应的使用场景吗？"
  3. 用户确认后:
     - 确认无场景 → 标记为 CUT 候选，进入后续裁剪评估
     - 实际有场景 → 用户指出场景，更新映射，调整置信度为 high（用户确认）
     - 不确定 → 保留，标记为 needs_investigation
```

### 4.3 孤立功能的呈现格式

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
孤立功能（未归入任何场景）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. F-015 数据备份
   描述: 手动触发全库数据备份
   实现: src/modules/backup/BackupPage.tsx
   路由: /admin/backup
   原因: 无场景关键词匹配，无 PRD 引用

2. F-018 系统日志查看
   描述: 查看系统操作日志
   实现: src/pages/admin/Logs.tsx
   路由: /admin/logs
   原因: 无场景关键词匹配，无 PRD 引用

请确认: 这些功能是否确实没有使用场景？
如果某个功能实际属于某个场景，请指出。
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 5. 用户确认点

场景识别完成后，**必须**向用户展示以下内容并等待确认。**不要自动跳过确认。**

### 5.1 展示内容

**Part 1: 场景列表**

```
已识别 N 个核心场景:

S-001 用户管理
  描述: 管理员创建、编辑、禁用系统用户
  角色: 管理员
  来源: docs/prd.md:15
  核心功能: F-001 用户列表, F-002 创建用户, F-003 编辑用户, F-004 禁用用户
  相关功能: F-012 用户权限配置

S-002 订单管理
  描述: 用户下单、支付、查看和管理订单
  角色: 普通用户
  来源: docs/prd.md:42
  核心功能: F-005 订单列表, F-006 创建订单, F-007 订单详情, F-008 订单支付
  相关功能: F-013 订单导出

...
```

**Part 2: 功能-场景映射表（按场景分组）**

```
功能-场景映射:

[S-001 用户管理]
  ✓ F-001 用户列表        core    high    route:/users
  ✓ F-002 创建用户        core    high    route:/users/create
  ✓ F-003 编辑用户        core    high    route:/users/:id/edit
  ✓ F-004 禁用用户        core    high    prd:docs/prd.md:18
  ~ F-012 用户权限配置    related medium  keyword:用户

[S-002 订单管理]
  ✓ F-005 订单列表        core    high    route:/orders
  ...

[孤立功能]
  ✗ F-015 数据备份        orphan  none
  ✗ F-018 系统日志查看    orphan  none
```

**Part 3: 孤立功能列表**

见上方第 4 节的呈现格式。

### 5.2 确认问题

```
请确认:
1. 场景划分合理吗？有遗漏的场景吗？
2. 功能-场景映射准确吗？有功能被分错场景的吗？
3. 孤立功能中有实际属于某个场景的吗？
```

### 5.3 处理用户反馈

```
用户可能的反馈类型:

1. 补充场景 → 新增 S-XXX，将用户指出的功能重新映射
2. 合并场景 → 将两个场景合并为一个，合并 core_features
3. 拆分场景 → 将一个场景拆分为多个，重新分配功能
4. 修正映射 → 将功能从场景 A 移到场景 B
5. 认领孤立功能 → 将孤立功能归入某个场景，置信度更新为 high
6. 确认孤立 → 孤立功能确认无场景，保持 orphan 状态

收到用户确认后:
  - confirmed_by_user = true
  - 更新 scenarios 和 feature_scenario_map
  - 进入 Step 2
```

---

## 6. 输出格式

Step 1 的最终输出为 `scenarios.json`，结构如下：

```json
{
  "scenarios": [
    {
      "id": "S-001",
      "name": "用户管理",
      "description": "管理员创建、编辑、禁用系统用户",
      "user_role": "管理员",
      "source": "docs/prd.md:15",
      "core_features": ["F-001", "F-002", "F-003", "F-004"],
      "related_features": ["F-012"]
    },
    {
      "id": "S-002",
      "name": "订单管理",
      "description": "用户下单、支付、查看和管理订单",
      "user_role": "普通用户",
      "source": "docs/prd.md:42",
      "core_features": ["F-005", "F-006", "F-007", "F-008"],
      "related_features": ["F-013"]
    }
  ],
  "feature_scenario_map": [
    {
      "feature_id": "F-001",
      "scenario_ids": ["S-001"],
      "relation": "core",
      "confidence": "high",
      "mapping_signal": "route:/users"
    },
    {
      "feature_id": "F-012",
      "scenario_ids": ["S-001"],
      "relation": "related",
      "confidence": "medium",
      "mapping_signal": "keyword:用户"
    },
    {
      "feature_id": "F-013",
      "scenario_ids": ["S-002"],
      "relation": "related",
      "confidence": "medium",
      "mapping_signal": "module:src/modules/order/"
    },
    {
      "feature_id": "F-015",
      "scenario_ids": [],
      "relation": "orphan",
      "confidence": "none",
      "mapping_signal": null
    },
    {
      "feature_id": "F-018",
      "scenario_ids": [],
      "relation": "orphan",
      "confidence": "none",
      "mapping_signal": null
    }
  ],
  "orphan_features": ["F-015", "F-018"],
  "code_derived": false,
  "confirmed_by_user": false
}
```

### 6.1 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `scenarios[].id` | string | 场景唯一标识，S-XXX 格式 |
| `scenarios[].name` | string | 场景名称 |
| `scenarios[].description` | string | 场景目标描述：用户要完成什么 |
| `scenarios[].user_role` | string | 执行角色：管理员 / 普通用户 / 访客 |
| `scenarios[].source` | string | 来源位置：`file:line` 或 `code-derived` |
| `scenarios[].core_features` | string[] | 核心功能 ID 列表 |
| `scenarios[].related_features` | string[] | 相关功能 ID 列表 |
| `feature_scenario_map[].feature_id` | string | 功能 ID |
| `feature_scenario_map[].scenario_ids` | string[] | 归属场景 ID 列表，空数组表示孤立 |
| `feature_scenario_map[].relation` | string | `core` / `related` / `orphan` |
| `feature_scenario_map[].confidence` | string | `high` / `medium` / `low` / `none` |
| `feature_scenario_map[].mapping_signal` | string\|null | 映射依据：`route:X` / `module:X` / `keyword:X` / `prd:X` / `null` |
| `orphan_features` | string[] | 孤立功能 ID 列表（feature_scenario_map 中 relation=orphan 的汇总） |
| `code_derived` | boolean | 场景是否从代码推导（非文档来源） |
| `confirmed_by_user` | boolean | 用户是否已确认场景划分和映射 |

---

## 7. 铁律提醒 — 场景为锚

```
场景是 feature-prune 的锚点。

后续所有裁剪判断都以场景为基准:
  - 功能有场景 → 有存在理由，需要进一步评估使用频率和 ROI
  - 功能无场景 → 没有存在理由，是最强的 CUT 信号
  - 场景内功能过多 → 可能场景拆分不够细，回头检查
  - 场景内功能过少 → 可能场景合并太粗，或功能缺失

不要跳过场景识别直接裁剪功能。
没有场景锚定的裁剪建议是无根据的 — 你不知道用户要做什么，就不能判断哪些功能该留。
```

---

> **铁律速查** — 场景为锚：一切裁剪判断的起点是场景，不是功能本身。
> 本步骤强相关：**来源绑定**（每个场景必须记录 source）、**用户确认**（场景划分和孤立功能必须经过用户确认，不要自动跳过）。
