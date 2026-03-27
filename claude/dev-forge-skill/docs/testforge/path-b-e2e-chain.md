# 路径 B：E2E 链锻造 — 操作驱动

> **核心范式：每条链以操作产生数据为驱动，不是读取已有数据验证。**
>
> 错误示范（"看"）：导航到列表页 → 断言有数据 → 导航到详情页 → 断言有内容
> 正确范式（"做"）：创建实体 → 操作实体 → 验证实体跨页面流转 → 验证关联影响

## 前置条件

- Step 4.0（静态接缝预检）+ Step 4.0.5（Chain 0 冒烟）已通过
- Path A（unit）+ Path D（integration）+ Path C（platform UI）已完成
- Chain 0 登录态可复用（storageState）

## B.1 链路推导

从上游产物推导 E2E 链，**不硬编码任何页面路径或业务域**（铁律 #13）：

```
来源（按优先级）：
1. .allforai/project-forge/e2e-scenarios.json（已有规划 → 直接采用）
2. .allforai/product-map/business-flows.json（推导每条 flow 为一条链）
3. API 路由表 + 页面路由表（无上游时，从代码推导实体生命周期链）

推导规则：
  对每条 business-flow / e2e-scenario：
    a. 提取关键动词 → 映射为 UI 操作（创建、编辑、删除、审批、分配…）
    b. 提取涉及的子项目（前端 A → 后端 → 前端 B）
    c. 提取涉及的角色（不同角色看到不同结果）
    d. 生成链路定义（见 B.2 结构）
```

**每条链必须跨 ≥2 个子项目**（否则降为 integration 测试）。

## B.2 链路结构：五段式操作链

每条 E2E 链由 5 个阶段组成，**每个阶段都是操作（Action），不是观察**：

```
┌─────────────────────────────────────────────────────────────┐
│ Phase 1: Seed（操作产生种子数据）                              │
│   用 UI 操作创建测试所需的基础数据                              │
│   例：注册用户 → 创建组织 → 邀请成员                           │
├─────────────────────────────────────────────────────────────┤
│ Phase 2: Act（核心业务操作）                                   │
│   执行被测业务流的核心动作                                      │
│   例：提交订单 → 发起审批 → 上传文件                           │
├─────────────────────────────────────────────────────────────┤
│ Phase 3: Ripple（涟漪验证 — 跨页面/跨角色/跨子项目）            │
│   验证 Phase 2 的操作结果在其他页面/角色/子项目正确流转          │
│   例：管理端看到新订单 → 通知出现 → 统计数字更新                │
├─────────────────────────────────────────────────────────────┤
│ Phase 4: Mutate（状态变迁操作）                                │
│   对 Phase 2 产生的数据执行状态变更                             │
│   例：审批通过 → 修改订单 → 取消订单                           │
├─────────────────────────────────────────────────────────────┤
│ Phase 5: Cascade（级联验证 — 变更后的跨端影响）                  │
│   验证 Phase 4 的变更在所有关联位置正确反映                     │
│   例：审批后订单状态变更 → 库存扣减 → 用户收到通知              │
└─────────────────────────────────────────────────────────────┘
```

**与传统 Arrange-Act-Assert 的区别**：
- 传统：Arrange（准备数据，可能用 API/seed）→ Act → Assert
- 操作驱动：Seed 也通过 UI 操作完成（铁律 #16 禁止 API 捷径）。Ripple/Cascade 不只是断言，还包含切换角色/页面的操作。

## B.3 操作驱动的链步骤生成协议

**每个步骤必须是一个用户可执行的 UI 操作，而非一个读取断言。**

```
对每条链的每个步骤：

Step 1: 确定操作（从 business-flow 提取）
  - 动词 → UI 操作映射：
    "创建"  → 导航到表单页 → 填写字段 → 点击提交
    "审批"  → 切换角色 → 导航到待审列表 → 点击审批按钮 → 确认
    "编辑"  → 导航到详情页 → 点击编辑 → 修改字段 → 保存
    "删除"  → 导航到列表页 → 选中目标 → 点击删除 → 确认弹窗
    "分配"  → 导航到详情页 → 选择分配对象 → 确认
  - 每个操作必须产生可观测的状态变更

Step 2: 确定操作的输入数据
  - 必须使用当前链内前序步骤产生的数据（自给自足，铁律 #7）
  - 用唯一标识符（时间戳/UUID 后缀）避免与其他测试冲突
  - 示例：const orderName = `Order-${Date.now()}`
          填写订单名 → orderName
          后续步骤用 orderName 定位该订单

Step 3: 确定操作后的涟漪断言
  a. 当前页面断言（操作完成后）：
     - 成功提示出现（toast/snackbar/redirect）
     - 新创建/修改的数据在当前页面可见
  b. 跨页面断言（导航到其他页面）：
     - 列表页能找到刚才创建的实体（用唯一标识符搜索/筛选）
     - 详情页显示正确的字段值
  c. 跨角色断言（切换角色后）：
     - 另一角色的对应页面能看到该实体
     - 权限范围内的操作可执行
  d. 跨子项目断言（导航到另一个前端）：
     - 管理端/用户端/报表端的对应数据正确
```

## B.4 数据自给自足协议

> **铁律：链内的每一条数据都由链自己创建，不依赖任何预置 seed 或其他链的数据。**

```
数据创建策略（按场景选择）：

  ✓ beforeAll 中通过 API 创建前置数据（推荐用于种子数据）
    适用：前置数据创建不是被测流程本身（如：测审批流，需要先有 draft 场景包）
    优势：快速、可靠、确定性、不因 UI 变化而断裂
    要求：使用 Path E 建立的 e2e/helpers/api.ts

  ✓ 通过 UI 操作创建数据（推荐用于被测操作本身）
    适用：创建操作本身就是被测的业务流步骤
    优势：测到了 UI → API 接缝

  ✓ Chain 0 的真实登录后保存 storageState 复用

  ✓ afterAll 中通过 API 清理数据（try/catch 忽略错误）

禁止：
  ✗ 依赖数据库 seed 数据（seed 变了链就断）
  ✗ 依赖其他链创建的数据（链间耦合）
  ✗ 用 SQL INSERT 准备数据
  ✗ 用 cookie/localStorage 注入跳过创建流程

判断标准："这个数据创建操作是不是我要测的业务流的一部分？"
  是 → 通过 UI 创建（测接缝）
  不是 → 通过 API 创建（快速种子）

数据隔离：
  - 每条链用唯一前缀/后缀标记数据（时间戳或 UUID 片段）
  - afterAll 清理数据（不留垃圾），清理失败不阻断
  - 搜索/筛选定位数据时用唯一标识符，不假设"第一条就是我的"
```

## B.5 角色切换协议

多角色链（如"用户提交 → 管理员审批"）的角色切换：

```
方式 1: storageState 切换（推荐）
  Chain 0 为每个测试角色各登录一次，保存各自的 storageState
  链内切换角色 = 加载不同的 storageState → 刷新页面
  优势：快（无需重新登录），角色间干净隔离

方式 2: 多浏览器上下文
  为每个角色创建独立的 BrowserContext
  链内切换 = 切换到另一个 context 操作
  优势：可以并行操作两个角色（如测试实时通知）

禁止：
  ✗ 同一浏览器上下文内切换账号（状态污染）
  ✗ 用 API 模拟另一角色的操作（不测 UI）
```

## B.6 链锻造执行协议

```
每批 1-2 条链（每条链是完整业务流）。

对每条链：

1. 推导链步骤（从 business-flow）
   读 business-flow 定义 → 提取操作序列 → 映射为 5 段式链结构
   每个步骤标注：
     - action: 具体 UI 操作描述
     - actor: 执行角色
     - sub_project: 在哪个前端执行
     - produces: 此步骤产生的数据（变量名）
     - consumes: 此步骤依赖的前序数据（变量名）
     - ripple_checks: 操作后需要验证的涟漪位置

2. 生成可执行测试代码
   a. 每条链 = 一个测试文件
   b. 链内步骤按顺序执行（不可并行 — 后步依赖前步的数据）
   c. 每个步骤内：
      - 操作代码（导航 + 填写 + 点击 + 等待）
      - 操作后断言（当前页面 + 跨页面 + 跨角色）
      - 断言深度 ≥ Level 3（值正确性，铁律 #28）
        ✓ expect(page.locator('[data-testid="order-name"]')).toHaveText(orderName)
        ✗ expect(page.locator('[data-testid="order-name"]')).toBeVisible()
   d. 选择器先看后写（铁律 #14）：
      先 browser_navigate + browser_snapshot → 从真实 DOM 提取选择器
      不凭猜测写选择器

3. 正向链 + 负向链
   正向链：happy path — 每个操作都成功，数据正常流转
   负向链（从 use-case-tree 的 exceptions 或 Phase 3 Layer D 推导）：
     - 操作被拒绝（权限不足、数据校验失败、并发冲突）
     - 操作部分成功（第 3 步失败，验证前 2 步的数据不被回滚/污染）
     - 操作超时（断网/慢网下操作，验证恢复后状态一致）

4. 运行 → 分类失败 → 修复 → 重跑
   失败分类：
     CHAIN_BUG  — 链步骤写错（选择器不对、等待不够）→ 修链
     SEAM_BUG   — 接缝问题（数据到了后端但前端没刷新）→ 修业务代码
     BIZ_BUG    — 业务逻辑错误（状态流转不对）→ 修业务代码
     ENV_ISSUE  — 环境问题 → 记录跳过

5. 收敛（CG-1）：max 3 轮，单调递减
```

## B.7 涟漪断言模式库

> 以下是常见的操作→涟漪模式，LLM 根据实际 business-flow 选择适用的模式。

```
模式 1: 创建→列表出现
  操作：在表单页创建实体（填写 uniqueName → 提交）
  涟漪：
    ✓ 导航到列表页 → 搜索 uniqueName → 断言行存在
    ✓ 断言行内关键字段值正确（状态、创建时间、创建人）
    ✓ 点击行 → 进入详情 → 断言所有字段与填写一致

模式 2: 操作→跨角色可见
  操作：角色 A 提交审批请求
  涟漪：
    ✓ 切换到角色 B → 导航到审批列表 → 断言请求出现
    ✓ 断言请求中包含角色 A 的操作内容
    ✓ 角色 B 执行审批 → 切换回角色 A → 断言状态变更

模式 3: 操作→统计更新
  操作：创建/删除/变更实体
  涟漪：
    ✓ 导航到 Dashboard → 断言对应统计数字变化
    ✓ 记录操作前数字 N → 操作 → 断言数字为 N±1（不是断言"有数字"）

模式 4: 操作→通知触达
  操作：触发通知事件（如分配任务、审批完成）
  涟漪：
    ✓ 切换到接收者角色 → 检查通知列表/铃铛图标
    ✓ 断言通知内容包含操作的关键信息（实体名、操作人、操作类型）

模式 5: 删除→级联消失
  操作：删除实体
  涟漪：
    ✓ 列表页不再出现该实体（搜索 uniqueName → 无结果）
    ✓ 关联页面的引用更新（如子记录列表为空或显示"已删除"）
    ✓ 其他角色的页面也不再显示该实体

模式 6: 状态变迁→全端同步
  操作：变更实体状态（如 draft → submitted → approved）
  涟漪：
    ✓ 当前页面状态标签更新
    ✓ 列表页的状态列更新
    ✓ 其他角色看到新状态
    ✓ 状态相关的操作按钮变化（如 approved 后"审批"按钮消失）
```

## B.8 链定义输出格式

写入 `.allforai/testforge/e2e-chains.json`：

```json
{
  "generated_at": "ISO8601",
  "chains": [
    {
      "id": "CHAIN-001",
      "name": "从 business-flow 推导的链名",
      "source": "business-flows.json#F003",
      "direction": "positive",
      "actors": ["admin", "user"],
      "sub_projects": ["web-admin", "api-server", "web-client"],
      "steps": [
        {
          "phase": "seed",
          "action": "以 admin 身份在管理端创建商品",
          "actor": "admin",
          "sub_project": "web-admin",
          "produces": ["productName", "productId"],
          "consumes": [],
          "ui_operations": [
            "导航到商品管理页",
            "点击新增按钮",
            "填写商品名 = productName",
            "填写价格 = 99.00",
            "点击保存"
          ],
          "ripple_checks": [
            {
              "location": "web-admin 商品列表",
              "assertion": "搜索 productName → 行存在且价格=99.00"
            }
          ]
        },
        {
          "phase": "act",
          "action": "以 user 身份在客户端下单购买该商品",
          "actor": "user",
          "sub_project": "web-client",
          "produces": ["orderName", "orderId"],
          "consumes": ["productName"],
          "ui_operations": [
            "导航到商品详情页（搜索 productName）",
            "点击购买",
            "填写收货信息",
            "提交订单"
          ],
          "ripple_checks": [
            {
              "location": "web-client 我的订单",
              "assertion": "订单列表出现 orderName，状态=待支付"
            },
            {
              "location": "web-admin 订单管理",
              "assertion": "切换 admin → 订单列表出现 orderName"
            }
          ]
        },
        {
          "phase": "mutate",
          "action": "以 admin 身份审批发货",
          "actor": "admin",
          "sub_project": "web-admin",
          "produces": [],
          "consumes": ["orderName"],
          "ui_operations": [
            "导航到订单管理",
            "搜索 orderName",
            "点击发货按钮",
            "确认发货"
          ],
          "ripple_checks": []
        },
        {
          "phase": "cascade",
          "action": "验证发货后的跨端状态同步",
          "actor": "user",
          "sub_project": "web-client",
          "produces": [],
          "consumes": ["orderName"],
          "ui_operations": [
            "切换 user → 导航到我的订单",
            "搜索 orderName"
          ],
          "ripple_checks": [
            {
              "location": "web-client 我的订单",
              "assertion": "orderName 状态 = 已发货"
            },
            {
              "location": "web-admin Dashboard",
              "assertion": "今日发货数 +1（相对链开始时）"
            }
          ]
        }
      ],
      "status": "PASS | FAIL | PLAN_ONLY"
    }
  ]
}
```

## B.9 异步接缝四态（与 B.6 正向链配合）

正向链通过后，为链中每个跨网络操作追加四态测试（铁律 #27）：

```
对链中每个涉及 API 调用的步骤（Phase 2 Act 和 Phase 4 Mutate）：

优先级：高频操作优先（创建、提交、审批），低频操作标记 DEFERRED

Pending 测试：
  throttle 慢网 → 执行操作 → 断言 loading 态 + 按钮 disabled

Rejected 测试：
  构造真实错误输入（空必填字段 / 非法值）→ 操作 → 断言错误提示 + 表单数据保留

Timeout 测试：
  断网 → 操作 → 断言超时提示 → 恢复网络 → 断言可重试且数据不丢
```

## B.10 链与链之间的关系

```
独立性原则：
  - 每条链独立运行，不依赖其他链的执行顺序或产生的数据
  - 每条链创建自己的全部所需数据
  - 并行运行多条链不会冲突（靠唯一标识符隔离）

推导关系：
  - 正向链 → 对应的负向链（同一 business-flow 的异常路径）
  - 正向链通过后才锻造负向链（正向都走不通，负向没意义）
```
