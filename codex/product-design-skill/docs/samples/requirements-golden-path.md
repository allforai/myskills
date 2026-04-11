# Requirements Confirmation — Golden Path Transcript

Demonstrates the full Stage A → B → C → product-map flow for an e-commerce product.

## Context

User just completed `/product-concept` for a marketplace product. `concept-baseline.json` was written to `.allforai/product-concept/`.

---

## Stage A — Core Path Confirmation

**LLM output:**

```
核心路径：

1. 买家
   触发：选定商品后发起购买
   步骤：搜索商品 → 加购 → 结账 → 支付
   成功结果：形成待履约订单，库存锁定，等待卖家发货

2. 卖家
   触发：有新订单待处理
   步骤：查看订单 → 备货 → 填写快递信息 → 发货确认
   成功结果：订单进入物流阶段，买家收到发货通知

3. 管理员
   触发：收到用户投诉
   步骤：查看投诉 → 审核证据 → 处置（警告/封禁）
   成功结果：投诉关闭，处置记录留存

确认以上路径，或告知遗漏/错误：
```

**User reply:** `确认，但买家还有一个退款申请路径`

LLM adds CP-004 and proceeds to Stage B.

---

## Stage B — Standard Module Sign-off

**LLM output:**

```
标准模块 — 明确回复"确认"或指出修改项后继续：

基础层（默认启用）
  [认证]    邮箱密码 + Google OAuth
  [会话]    JWT，7天有效期，refresh token
  [权限]    RBAC，admin / user 两级
  [通知]    邮件（注册确认/密码重置）
  [软删除]  用户/订单数据逻辑删除保留

领域层（推断自核心路径）
  [支付]    第三方网关，支持退款申请  [推断]
  [评价]    买家对订单评价，卖家可回复  [推断]
  [站内通知] 按类型分组，支持已读/未读  [推断]

可选项（如需请告知）
  实时聊天 / 文件存储 / 全文搜索 / i18n / PWA 离线

回复"确认"继续，或说明要修改的项：
```

**User reply:** `支付改成支持微信支付和支付宝，其余确认`

LLM writes SM-payment with `decision_source: "user_override"`, all others `user_confirmed`. Proceeds to Stage C.

---

## Stage C — Boundary Decisions

**LLM question 1:**

```
路径"买家退款申请"有一个需要确认的点：

买家申请退款后，退款处理方式是？
  a) 卖家处理（卖家同意/拒绝）
  b) 平台客服处理（买家卖家都可申诉）
  c) 自动退款（无需审批，直接退回）
```

**User reply:** `b`

**LLM question 2:**

```
关于权限模型需要确认：

管理员是否分级（超级管理员 vs 普通运营）？
  a) 是，超级管理员可封号，普通运营只能处理投诉
  b) 否，所有管理员权限相同
  c) 暂不分级，后续扩展
```

**User reply:** `a`

No more qualifying questions. Stage C complete.

---

## Output

`requirements-brief.json` written with `confirmed_status: "fully_confirmed"`.

---

## product-map Step 0

LLM reads requirements-brief.json, sees `confirmed_status: "fully_confirmed"`:

```
需求已确认（fully_confirmed）。

将基于以下内容展开产品地图：
- 4 条核心路径（买家购买/退款、卖家发货、管理员处理投诉）
- 7 个已确认标准模块（认证/会话/权限/通知/软删除/支付/评价）
- 2 个边界决策（退款平台介入、管理员分级）

直接进入 Step 1...
```

Product-map seeds business-flows from core_paths and auto-generates standard module tasks without asking directional questions.
