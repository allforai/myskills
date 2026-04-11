---
name: requirements
description: >
  Use when the user asks to confirm requirements, "需求确认", "核对需求",
  or when product-concept finishes and auto-triggers requirements confirmation.
  Runs Stage A (core path confirmation) → Stage B (standard module sign-off)
  → Stage C (boundary decisions). Outputs requirements-brief.json.
  Auto-triggered at end of product-concept. Also runnable standalone as /requirements.
---

# Requirements Confirmation — 需求确认

> 在 product-map 展开前，从粗到细确认核心路径、标准模块、关键边界。
> 输出 `requirements-brief.json`，作为 product-map 的确认基础。

---

## 触发条件

- **自动触发**：product-concept 生成 `concept-baseline.json` 后立即进入本阶段
- **手动触发**：用户运行 `/requirements`（需求范围变更后重新确认）

---

## Stage A — 核心路径确认

**输入：** `.allforai/product-concept/concept-baseline.json`  
**目标：** 在任何展开前，锁定 2-4 条主干用户路径。

读取 concept-baseline 中的 roles + business_model，推导 2-4 条核心路径。每条路径包含：

| 字段 | 说明 |
|------|------|
| `actor` | 执行该路径的角色 |
| `trigger` | 触发条件（什么事件启动这条路径） |
| `steps` | 主干步骤序列（只含 happy path，不含异常） |
| `success_outcome` | 路径完成时系统所处的状态 |

**示例展示格式：**

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

**确认规则：**
- 用户明确回复（"确认" / "continue" / "无修改" / 指出修改点）→ 锁定路径，进入 Stage B
- 无回复 / 会话中断 → `status: "pending"`，不自动推进

---

## Stage B — 标准模块批量 Sign-off

**输入：** Stage A 确认的路径 + 项目类型（fullstack / backend / frontend）  
**目标：** 一条消息确认标准基础设施，不做逐项讨论。

### 模块目录（三层结构）

**Tier 1 — foundation_defaults**（默认启用，用户可关闭）

| 模块 ID | 模块名 | 默认方案 | inclusion_rule | fullstack | backend | frontend |
|---------|--------|---------|----------------|-----------|---------|----------|
| SM-auth | 认证 | 邮箱密码 + Google OAuth | always | ✓ | ✓ | ✓ |
| SM-session | 会话 | JWT，7天有效期，refresh token | always | ✓ | ✓ | — |
| SM-rbac | 权限 | RBAC，admin / user 两级 | always | ✓ | ✓ | — |
| SM-email | 通知-邮件 | 注册确认 / 密码重置 | always | ✓ | ✓ | — |
| SM-softdelete | 软删除 | 用户/订单数据逻辑删除保留 | has_user_data OR has_order_data | ✓ | ✓ | — |

**Tier 2 — domain_defaults**（LLM 从 Stage A 路径推断，展示时加 `[推断]` 标签）

| 领域信号（来自 Stage A 路径） | 推断模块 |
|------------------------------|---------|
| 电商路径（购买/订单/支付） | 支付+退款, 物流追踪, 商品评价 |
| 社交路径（关注/内容/互动） | 关注关系, 消息通知, 内容审核 |
| 企业管理路径（审批/权限/报表） | 操作审计日志, 多租户, SSO |
| SaaS 路径（订阅/用量/账单） | 订阅计费, 用量统计, Webhook |

**Tier 3 — optional_candidates**（不默认展示，列在"可选项"区）

实时聊天 / 文件存储 / 全文搜索 / 多语言(i18n) / 离线支持(PWA)

### 展示格式

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

**确认规则：**
- "确认" / "confirm" / "continue" / "无修改" → 所有展示模块写 `status: "confirmed"`
- 指出修改 → 修改项写 `decision_source: "user_override"`，其余写 `status: "confirmed"`
- 无回复 / 中断 → 所有模块写 `status: "pending"`

---

## Stage C — 关键边界决策

**输入：** Stage A 路径 + Stage B 模块  
**目标：** 用选择题关闭 3-5 个无法推断的歧义点。

### 提问选择规则

只提问满足以下至少一项的歧义：
1. **影响数据实体**：需要新增实体、字段或关系
2. **影响权限模型**：谁能做 / 谁不能做
3. **影响关键状态转换**：核心路径中的分支状态
4. **影响外部集成选择**：选哪家第三方，或是否集成
5. **影响计费/合规约束**：付费规则、数据保留要求

可合理设默认值的歧义：跳过提问，在输出中记录 `decision_source: "default"`。

**提问格式（每次一个问题，必须给选项）：**

```
路径"买家结账"有一个需要确认的点：

支付失败后订单保留多久？
  a) 30分钟自动取消
  b) 24小时（用户可重新支付）
  c) 不自动取消，人工处理
```

最多 5 个问题。全部回答后 Stage C 完成。

---

## 输出：requirements-brief.json

写入 `.allforai/product-concept/requirements-brief.json`：

```json
{
  "schema_version": "1.1",
  "generated_at": "<ISO 8601>",
  "confirmed_at": "<ISO 8601 or null>",
  "confirmed_status": "fully_confirmed | partially_confirmed | pending",
  "source_command": "/product-concept | /requirements",
  "based_on_concept_baseline_version": "<hash or timestamp>",

  "core_paths": [
    {
      "id": "CP-001",
      "actor": "买家",
      "trigger": "选定商品后发起购买",
      "steps": ["搜索商品", "加购", "结账", "支付"],
      "success_outcome": "形成待履约订单，库存锁定，等待卖家发货",
      "status": "confirmed | pending",
      "notes": null
    }
  ],

  "standard_modules": [
    {
      "id": "SM-auth",
      "name": "认证",
      "tier": "foundation_default",
      "default": "邮箱密码 + Google OAuth",
      "status": "confirmed | pending | excluded",
      "decision_source": "default | user_confirmed | user_override | inferred",
      "override": null
    }
  ],

  "boundary_decisions": [
    {
      "id": "BD-001",
      "question": "支付失败后订单保留多久？",
      "options": ["30分钟自动取消", "24小时（用户可重新支付）", "不自动取消，人工处理"],
      "selected_option": "30分钟自动取消",
      "decision_source": "user_selected | default",
      "rationale": null,
      "impact_scope": ["CP-001", "SM-payment"],
      "affects_path": "CP-001"
    }
  ],

  "unconfirmed_areas": []
}
```

**`confirmed_status` 判断逻辑：**
- `fully_confirmed`：所有 core_paths + standard_modules + boundary_decisions 均为 confirmed
- `partially_confirmed`：至少一项为 pending，但 Stage A/B/C 已完成
- `pending`：Stage A/B/C 未完成（会话中断）

---

## product-map 消费规则

| confirmed_status | product-map 行为 |
|-----------------|----------------|
| `fully_confirmed` | 跳过方向性问题；用 core_paths 生成 business-flows 骨架；standard_modules 直接生成 tasks |
| `partially_confirmed` | 跳过已确认部分；对 pending 项继续提问再展开 |
| `stale`（schema 版本不匹配） | 警告用户；回退到常规流程 |
| 文件不存在 | 提示用户先运行 /requirements；或以 unconfirmed 状态继续 |

standard_modules 生成的 tasks 带 `"source": "standard_module"` 标签，在 review 中与业务 tasks 视觉区分。
