# 功能审计报告

> 审计时间: 2024-01-15 10:30
> 审计模式: full
> 项目: /path/to/my-project
> 需求源: docs/prd-v1.md, README.md, docs/openapi.yaml

## 功能覆盖总览

| 分类 | 数量 | 占比 |
|------|------|------|
| COMPLETE | 3 | 50% |
| PARTIAL | 1 | 17% |
| MISSING | 1 | 17% |
| UNPLANNED | 1 | 17% |
| DEFERRED | 0 | 0% |

## 闭环验证总览

| 评分 | 功能数 | 功能列表 |
|------|--------|----------|
| 4/4 完整闭环 | 2 | 用户登录, 用户列表 |
| 3/4 基本闭环 | 1 | 创建用户 |
| 2/4 部分闭环 | 1 | 订单导出 |
| 1/4 严重断裂 | 0 | — |
| 0/4 无闭环 | 0 | — |

## 功能地图

### 用户管理模块

```
┌─ 用户管理 ─────────────────────────────────────────────┐
│  入口: 侧边栏 → /users                                │
│  ├── 用户列表 (GET /api/users) → 表格渲染 ✅ 4/4       │
│  ├── 新增用户 (按钮 → /users/create)                   │
│  │   └── 表单 → POST /api/users → Toast → ??? 3/4     │
│  └── 批量导入 (docs/prd-v1.md:88)                     │
│      └── ❌ MISSING — 未找到对应实现                    │
└────────────────────────────────────────────────────────┘
```

### 订单管理模块

```
┌─ 订单管理 ──────────────────────────────────────────┐
│  入口: 侧边栏 → /orders                            │
│  ├── 订单列表 (GET /api/orders) → 表格渲染 ✅ 4/4   │
│  └── 订单导出 (导出按钮 → GET /api/orders/export)   │
│      └── API 调用 → ??? → ??? 2/4                   │
└────────────────────────────────────────────────────┘
```

## MISSING 功能详情

| ID | 功能名称 | 需求来源 | 状态 |
|----|----------|----------|------|
| PF-006 | 批量导入用户 | docs/prd-v1.md:88 | 未找到对应实现 |

## PARTIAL 功能详情

| ID | 功能名称 | 已实现部分 | 未实现部分 |
|----|----------|-----------|-----------|
| PF-005 | 订单导出 | 导出按钮 + API 端点 | 下载触发逻辑、成功反馈 |

**证据**：
- 导出按钮: `src/pages/order/OrderList.tsx:45`
- API 端点: `GET /api/orders/export → src/modules/order/order.controller.ts:38`
- 未找到: 下载文件逻辑（未在 `src/pages/order/OrderList.tsx` 中发现 `download`, `blob`, `saveAs` 等关键词）
- 未找到: 成功/失败提示（未在导出处理函数中发现 `message.success`, `notification`, `toast` 等调用）

## 闭环断裂详情

### 创建用户 — 3/4（基本闭环）

```
功能地图: 侧边栏 → /users/create → 表单 → POST /api/users → Toast ✅ → 跳转列表 ❌
```

| 检查点 | 通过 | 证据 |
|--------|------|------|
| A 入口存在 | ✅ | `src/pages/user/UserList.tsx:23` — `<Button onClick={() => navigate('/users/create')}>` |
| B 操作可执行 | ✅ | `src/pages/user/UserCreate.tsx:45` — `handleSubmit → POST /api/users` |
| C 有反馈 | ✅ | `src/pages/user/UserCreate.tsx:52` — `message.success('创建成功')` |
| D 结果可见 | ❌ | 未找到 — 创建成功后未发现 `navigate('/users')` 或 `queryClient.invalidateQueries` 调用 |

**断裂模式**: 断尾流程 — 提交成功有提示，但用户需手动返回列表且列表可能未刷新。

### 订单导出 — 2/4（部分闭环）

```
功能地图: 订单列表 → 导出按钮 → GET /api/orders/export → ??? → ???
```

| 检查点 | 通过 | 证据 |
|--------|------|------|
| A 入口存在 | ✅ | `src/pages/order/OrderList.tsx:45` — `<Button>导出</Button>` |
| B 操作可执行 | ✅ | `src/pages/order/OrderList.tsx:48` — `handleExport → GET /api/orders/export` |
| C 有反馈 | ❌ | 未找到 — 导出操作无成功/失败提示 |
| D 结果可见 | ❌ | 未找到 — 无文件下载触发逻辑 |

**断裂模式**: 静默操作 — 用户点击导出后无任何反馈，不知道是否成功。

## UNPLANNED 功能详情

| ID | 功能名称 | 代码位置 | 状态 |
|----|----------|----------|------|
| IF-008 | 系统日志 | `src/pages/system/LogList.tsx:1`, 路由 `/system/logs` | 未在需求源中提及 |

## 用户决策日志

本次审计中用户确认的决策：

| 功能 | 初始分类 | 最终分类 | 原因 |
|------|---------|---------|------|
| (本示例中无 DEFERRED 决策) | — | — | — |

---

> 完整报告: `.feature-audit/audit-report.md`
> 待办清单: `.feature-audit/audit-tasks.json`
> 决策日志: `.feature-audit/audit-decisions.json`
