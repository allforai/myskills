---
name: seed-forge
description: >
  Use when the user asks to "generate demo data", "create seed data",
  "populate demo environment", "make my app look lived-in",
  "prepare data for product demo", "generate realistic test data",
  "seed-forge", "种子数据锻造",
  "演示数据生成", "生成种子数据", "灌入演示数据", "让产品看起来有人用",
  "准备产品演示", "数据锻造", "生成仿真数据",
  or mentions demo data population, seed data, realistic sample data,
  or demo environment preparation.
  Requires product-map to have been run first.
  Requires a running application for data population (Step 3-4).
version: "2.0.0"
---

# Seed Forge — 种子数据锻造

> 让产品看起来像有真实用户在真实使用

## 目标

以 `product-map` 为蓝本，生成有业务逻辑、有人物关系、有时间分布的种子数据：

1. **谁在用** — 按角色创建真实感用户账号
2. **做了什么** — 按任务频次生成业务数据（高频任务多生成，低频少生成）
3. **怎么关联** — 按场景生成完整数据链路，不是孤立的随机记录
4. **符合规则** — 按业务约束设置数据状态（不可逆操作、审批链、金额限制）

---

## 定位

```
product-map（现状+方向）   功能查漏（查缺口）   功能剪枝（查多余）   seed-forge（造数据）
产品应该长什么样           地图说有的有没有      地图里有的该不该留   按地图生成真实感数据
基础层                    基于 product-map     基于 product-map     基于 product-map
```

**前提**：必须先运行 `product-map`，生成 `.allforai/product-map/product-map.json`。
数据灌入（Step 3-4）需要应用正在运行。

---

## 快速开始

```
/seed-forge              # 完整流程（设计→采集→灌入）
/seed-forge plan         # 只设计种子方案，不灌入（不需要应用运行）
/seed-forge fill         # 加载已有方案，直接采集+灌入
/seed-forge clean        # 清理已灌入的种子数据
```

---

## 工作流

```
前置：加载 .allforai/product-map/product-map.json
      若文件不存在 → 提示用户先运行 /product-map，终止
      ↓
Step 0: 数据模型映射
      代码实体 ↔ product-map 任务/角色 对应关系
      → 用户确认映射
      ↓
Step 1: 种子方案设计（核心）
      角色 → 用户账号设计
      任务频次 → 数据量设计
      场景 → 数据关联链路设计
      约束 → 数据规则设计
      → 用户确认方案
      ↓
Step 2: 行业风格设定
      名称风格、价格范围、图片关键词
      → 用户确认风格
      ↓
Step 3: 素材采集
      竞品图片优先，免费图库兜底
      ↓
Step 4: 数据灌入
      按场景顺序，通过 API 逐层创建
```

---

### Step 0：数据模型映射

从代码提取数据模型（Entity、Model、Schema），与 `product-map` 中的任务和角色建立对应关系：

```
product-map 任务「创建退款单」  →  代码实体 Refund
product-map 角色「客服专员」    →  代码实体 User（role=agent）
product-map 场景「退款审批流」  →  实体关系 Refund → Approval → Notification
```

同步检测 API 缺口：有实体无对应创建端点、有任务无对应 API，标记为 `API_GAP`。

**用户确认**：映射关系对吗？有遗漏的实体吗？

输出：`.allforai/seed-forge/model-mapping.json`、`.allforai/seed-forge/api-gaps.json`

---

### Step 1：种子方案设计

这是最核心的一步，product-map 直接给出了所有决策依据。

#### 1-A 用户账号设计（按角色）

为 `role-profiles.json` 中每个角色创建对应数量的测试账号：

```
客服专员（R001）  →  5 个账号（team_lead × 1，agent × 4）
财务审核（R002）  →  2 个账号
管理员（R003）    →  1 个账号
```

每个账号有真实感信息：姓名、头像、入职时间、所在部门。

#### 1-B 数据量设计（按频次）

直接读取 `task-inventory.json` 中每个任务的 `frequency` 字段，按帕累托比例分配数据量：

| 任务频次 | 数据量策略 | 示例 |
|----------|------------|------|
| 高 | 大量，占总数据 70%+ | 退款单 80 条 |
| 中 | 适量，占总数据 20% | 批量退款 15 条 |
| 低 | 少量，仅保证存在 | 退款政策配置 2 条 |

> 这让演示时高频场景数据丰富，低频场景不喧宾夺主。

#### 1-C 数据链路设计（按场景）

不生成孤立数据，而是按场景生成完整链路。以退款场景为例：

```
场景「客服处理退款」（cross_dept: 财务+仓储）：
  客户用户 × 5
    └── 订单 × 20（已完成状态）
          └── 退款申请 × 15（已提交）
                └── 退款审批 × 10（已审核通过）
                      └── 退款通知 × 10（已发送）
```

每个场景生成的数据，时间戳连贯、状态流转合理、外键关联完整。

#### 1-C-2 灌入方式标注（按实体）

在 1-C 确定场景链路时，同步为每个实体标注灌入方式：

| 灌入方式 | 适用场景 |
|---------|---------|
| `api` | 需要触发业务逻辑的实体（创建订单、触发通知、状态流转、写审计日志） |
| `db` | 无业务逻辑副作用的实体（配置表、字典表、历史归档数据、API 尚未实现的实体） |

优先选 `api`；以下情况选 `db`：
- 该实体在 `api-gaps.json` 中标记为 `API_GAP`
- 需要构造"跳过正常流程"的终态数据（如已关闭很久的历史工单）
- 批量数据量大且 API 没有批量接口

#### 1-D 约束规则设计（按业务约束）

读取 `constraints.json`，将约束转为数据生成规则：

| 业务约束 | 数据规则 |
|----------|----------|
| 退款金额不超过原订单金额 | refund.amount ≤ order.amount |
| 高金额退款需要上级审批 | amount > 1000 → approval.level = 2 |
| 退款单不可逆，无删除状态 | 不生成 status=deleted 的记录 |
| 审批有 SLA（2h 内） | created_at 和 approved_at 间隔 < 2h |

#### 1-E 枚举全覆盖检查（硬性规则）

遍历 `task-inventory.json` 所有任务的 `main_flow` 和 `outputs.states`，提取全部状态枚举值，确认每个值都有对应记录：

```
✗ 错误：所有退款单 status = COMPLETED
✓ 正确：PENDING / SUBMITTED / APPROVED / REJECTED / COMPLETED / CANCELED 各至少 1 条
```

**重点检查终态和异常态**（最容易漏）：
- `REJECTED / CANCELED / EXPIRED / FAILED / CLOSED` — 专门分配记录，不能因为"业务上少见"就跳过
- 高风险任务的 `exceptions` 中提到的状态，也必须在数据中存在

**用户确认**：数据量合理吗？场景链路对吗？约束规则有遗漏吗？所有枚举值都有覆盖？

输出：`.allforai/seed-forge/seed-plan.json`

---

### Step 2：行业风格设定

基于用户提供的行业关键词（或从 product-map 推断），通过 WebSearch 获取该行业的数据风格：

- 人名风格（中文/英文/混合）
- 金额范围和货币格式
- 分类命名习惯
- 图片关键词（用于素材采集）

**用户确认**：风格对吗？要调整哪些维度？

输出：`.allforai/seed-forge/style-profile.json`

---

### Step 3：素材采集

根据种子方案中的图片需求，采集图片素材：

1. 优先从竞品网站爬取（仅用于内部演示，不公开传播）
2. 不足时用 Unsplash / Pexels 补充
3. 最终用占位图兜底

下载到 `.allforai/seed-forge/assets/` 目录，记录来源 URL 和本地路径。

输出：`.allforai/seed-forge/assets-manifest.json`

---

### 灌入前自检

在灌入之前，逐项确认：

```
实体完整性
□ 是否有实体一条记录都没有？
□ 配置表、字典表是否全量填入？

枚举覆盖
□ 每个状态字段，所有值都有记录？
□ 终态和异常态（REJECTED / CANCELED / EXPIRED / FAILED）没有遗漏？

外键完整性
□ 每个外键 ID 在本次种子数据中都有对应记录？
□ 没有假设数据库里已有某条记录？

演示可达性
□ 每个角色账号能登录？
□ 每个角色主视图有数据？
□ 每个核心流程有完整数据链路？

数据真实性
□ 金额、数量、日期合理（不全是 1、0、test）？
□ 状态流转符合业务逻辑（如退款单必须先有对应订单）？
□ 时间序列正确（created_at < updated_at，下单 < 支付 < 发货）？
```

---

### Step 4：数据灌入

**前提**：用户提供应用 URL 和管理员账号（API 灌入部分需要）；直连数据库凭据（DB 灌入部分需要）。

灌入顺序由场景链路决定（不是按模型字母顺序），确保外键依赖正确：

```
1. DB 灌入：先写无业务逻辑的基础数据（配置表、字典表、API_GAP 实体）
2. API 灌入：创建角色用户账号（所有场景依赖用户）
3. API/DB 混合：按场景优先级灌入（高频 → 中频 → 低频）
   - 每个场景内按链路顺序：父实体 → 子实体 → 关联实体
   - 每个实体按 Step 1-C-2 标注的方式选择 API 或 DB
4. 有图片字段的，先上传图片再创建记录（API 灌入时）
```

**DB 灌入注意事项**：
- 直接写入时跳过业务逻辑（如触发器、回调），需手动补写派生字段（计数、汇总金额等）
- 若有 ORM 的 `created_at` / `updated_at` 自动填充，DB 直写时需显式指定
- DB 灌入的记录同样写入 `forge-data.json`，clean 时直接 DELETE

失败的记录写入日志，不中断整体流程。

输出：
- `.allforai/seed-forge/forge-log.json` — 灌入日志（每条记录的状态）
- `.allforai/seed-forge/forge-data.json` — 已创建数据清单（含 ID，供 clean 使用）
- `.allforai/seed-forge/api-gaps.json` — 更新后的 API 缺口报告

---

## 输出文件结构

```
.allforai/seed-forge/
├── model-mapping.json     # Step 0: 代码实体 ↔ product-map 映射
├── api-gaps.json          # Step 0+4: API 缺口报告
├── seed-plan.json         # Step 1: 种子方案（用户/数量/链路/约束）
├── style-profile.json     # Step 2: 行业风格
├── assets-manifest.json   # Step 3: 素材清单
├── assets/                # Step 3: 下载的图片
│   ├── avatars/
│   ├── products/
│   └── banners/
├── forge-log.json         # Step 4: 灌入日志
└── forge-data.json        # Step 4: 已创建数据清单
```

---

## 5 条铁律

### 1. 频次决定数量，场景决定关联

高频任务的数据要多，低频任务的数据要少。数据之间的关联关系按场景链路设计，不随机拼凑。

### 2. 约束是硬规则

`constraints.json` 中的业务约束必须在数据中体现。金额上限、审批链、不可逆状态，生成的数据不得违反。

### 3. 优先 API，按需直写数据库

需要触发业务逻辑的数据（订单创建、状态流转、通知）走 API，保证数据一致性。配置表、字典表、历史归档数据、API 尚未实现的实体走数据库直写。每个实体在 Step 1-C-2 标注灌入方式，混合使用，互不替代。清理统一走数据库（速度快，一次性删除）。

### 4. 竞品图片仅用于内部演示

竞品爬取的图片只用于内部 Demo，不公开传播。

### 5. API 缺口如实报告

发现缺口就记录。有任务但没有对应 API、有实体但没有创建端点，记录到 `api-gaps.json`，不替用户补代码。

---

## 常见遗漏模式

| 遗漏类型 | 具体表现 | 预防方法 |
|---------|---------|---------|
| 终态缺失 | 所有记录都"进行中" | 1-E 枚举全覆盖检查，逐一确认所有状态值 |
| 异常态缺失 | 没有失败、拒绝、封禁的数据 | 专门为"坏路径"分配记录 |
| 日志表为空 | 操作日志、消息、流水没有数据 | Step 0 模型映射时专门列出日志类实体 |
| 孤立账号 | 有账号但没有任何关联业务数据 | 演示账号必须有关联业务链路数据 |
| 中间表遗漏 | 多对多关系表没有记录 | Step 0 扫描无主键列的关联表，单独确认 |
| 配置表为空 | 系统参数、模板等没有数据 | 配置类实体单独列出并全量填入 |
| 时间逻辑错误 | 发货早于下单，未来时间出现在历史记录 | 用相对时间偏移（NOW-7d）而非固定日期 |
