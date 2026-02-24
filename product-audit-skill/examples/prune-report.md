# 功能剪枝报告

> 剪枝时间: 2024-01-15 11:00
> 剪枝模式: full
> 项目: /path/to/my-project
> 需求源: docs/prd-v1.md, README.md, docs/openapi.yaml

## 剪枝总览

| 分类 | 数量 | 占比 |
|------|------|------|
| CORE | 5 | 63% |
| DEFER | 1 | 13% |
| CUT | 2 | 25% |

## 核心场景

| 场景 | 角色 | 核心功能数 | 相关功能数 |
|------|------|-----------|-----------|
| S-001 用户管理 | 管理员 | 3 | 1 |
| S-002 订单管理 | 运营人员 | 2 | 0 |

## 功能剪枝地图

### S-001 用户管理（管理员）

```
┌─ 用户管理 ─────────────────────────────────────────────────────┐
│  入口: 侧边栏 → /users                                        │
│  ├── F-001 用户登录 ✅ CORE                                    │
│  │   POST /api/auth/login → src/modules/auth/auth.controller.ts:15 │
│  ├── F-002 用户列表 ✅ CORE                                    │
│  │   GET /api/users → src/modules/user/user.controller.ts:12   │
│  ├── F-003 创建用户 ✅ CORE                                    │
│  │   POST /api/users → src/modules/user/user.controller.ts:25  │
│  └── F-006 批量导入用户 ⏸ DEFER                                │
│      docs/prd-v1.md:88 — 未找到对应实现                         │
└────────────────────────────────────────────────────────────────┘
```

### S-002 订单管理（运营人员）

```
┌─ 订单管理 ──────────────────────────────────────────────────────┐
│  入口: 侧边栏 → /orders                                        │
│  ├── F-004 订单列表 ✅ CORE                                     │
│  │   GET /api/orders → src/modules/order/order.controller.ts:10 │
│  └── F-005 订单导出 ✅ CORE                                     │
│      GET /api/orders/export → src/modules/order/order.controller.ts:38 │
└─────────────────────────────────────────────────────────────────┘
```

### 孤立功能（无场景归属）

```
┌─ 孤立功能 ──────────────────────────────────────────────────────┐
│  ├── F-007 系统日志 ⏸ DEFER (用户修改: CUT → DEFER)            │
│  │   /system/logs → src/pages/system/LogList.tsx:1              │
│  │   GET /api/logs → src/modules/log/log.controller.ts:8       │
│  │   标记: UNPLANNED — 未在需求源中提及                          │
│  └── F-008 数据可视化大屏 ✂ CUT                                 │
│      docs/prd-v1.md:105 — 未找到对应实现                         │
│      预估: 12 files, 3 endpoints, WebSocket + realtime          │
└─────────────────────────────────────────────────────────────────┘
```

## CORE 功能列表

| ID | 功能名称 | 来源 | 场景 | 场景关联度 | 依赖程度 | 复杂度比 |
|----|----------|------|------|-----------|----------|---------|
| F-001 | 用户登录 | both | S-001 | strong | high | justified |
| F-002 | 用户列表 | both | S-001 | strong | medium | cheap |
| F-003 | 创建用户 | both | S-001 | strong | low | cheap |
| F-004 | 订单列表 | both | S-002 | strong | medium | cheap |
| F-005 | 订单导出 | both | S-002 | strong | low | cheap |

## DEFER 功能详情

### F-006 批量导入用户

```
来源: planned (docs/prd-v1.md:88)
场景: S-001 用户管理 (related)
```

| 维度 | 评分 | 证据 |
|------|------|------|
| 场景关联度 | medium | 出现在 S-001(用户管理) 的 related_features 中 |
| 依赖程度 | low | 0 个功能依赖此功能（尚未实现） |
| 复杂度比 | medium | 预估 4 files, 2 endpoints, 涉及 file-upload（estimated） |

**分类理由**: 与用户管理场景间接相关但非核心路径，尚未实现，涉及文件上传技术，建议分类为 DEFER。

**建议时机**: 核心场景（用户管理 + 订单管理）稳定后，用户量增长到手动创建效率不足时实现。

---

### F-007 系统日志

```
来源: implemented (仅代码中存在)
场景: 无场景归属 (orphan) → 用户修改归属为 DEFER
标记: UNPLANNED
```

| 维度 | 评分 | 证据 |
|------|------|------|
| 场景关联度 | weak | 未出现在任何场景中 |
| 依赖程度 | low | 0 个功能依赖此功能 |
| 复杂度比 | cheap | 4 files, 1 endpoint, 无特殊技术 |

**代码位置**:
- 路由: `/system/logs` → `src/pages/system/LogList.tsx:1`
- 组件: `src/pages/system/LogList.tsx:1`
- 列表渲染: `src/pages/system/LogList.tsx:28` — `<Table>` 组件
- API: `GET /api/logs` → `src/modules/log/log.controller.ts:8`
- Service: `src/modules/log/log.service.ts:12`

**初步分类**: CUT — 无场景归属，未在需求源中提及。

**用户修改**: CUT → DEFER — "运维排查问题时需要查看日志，暂时保留，后续归入系统运维场景。"

**建议时机**: 下一次场景梳理时明确系统运维场景后归入。

## CUT 功能详情

### F-008 数据可视化大屏

```
来源: planned (docs/prd-v1.md:105)
场景: 无场景归属 (orphan)
```

| 维度 | 评分 | 证据 |
|------|------|------|
| 场景关联度 | weak | 未出现在任何场景中 |
| 依赖程度 | low | 0 个功能依赖此功能（尚未实现） |
| 复杂度比 | excessive | 预估 12 files, 3 endpoints, WebSocket + realtime（estimated） |

**需求来源**: `docs/prd-v1.md:105` — "数据可视化大屏：实时展示订单数据、用户增长趋势、GMV 变化等核心指标"

**分类理由**: 无明确场景归属，预估实现涉及 12 个文件、3 个端点，依赖 WebSocket 实时推送，复杂度远超当前项目阶段的需要。

**竞品参考**: 竞品在同阶段普遍不包含此功能（0/3 覆盖）。

## 竞品参考摘要

产品类型: 电商后台管理系统

| 竞品 | 用户管理 | 订单管理 | 订单导出 | 批量导入 | 系统日志 | 数据大屏 |
|------|---------|---------|---------|---------|---------|---------|
| 有赞微商城后台 | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Shopify Admin | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| 商派 ECstore | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ |

| 功能 | 竞品覆盖率 | 信号 |
|------|-----------|------|
| F-006 批量导入用户 | 2/3 (67%) | weaken_cut — 竞品在同阶段多数具备 |
| F-007 系统日志 | 1/3 (33%) | — |
| F-008 数据可视化大屏 | 0/3 (0%) | strengthen_cut — 竞品在同阶段普遍不包含 |

仅竞品有而本项目没有的功能（仅标注，不建议添加）：
- 多语言支持（2/3 竞品具备）
- 操作审计日志（2/3 竞品具备）

## 用户决策日志

本次剪枝中用户确认的决策：

| 功能 | 初始分类 | 最终分类 | 原因 |
|------|---------|---------|------|
| F-001 用户登录 | CORE | CORE | 确认 |
| F-002 用户列表 | CORE | CORE | 确认 |
| F-003 创建用户 | CORE | CORE | 确认 |
| F-004 订单列表 | CORE | CORE | 确认 |
| F-005 订单导出 | CORE | CORE | 确认 |
| F-006 批量导入用户 | DEFER | DEFER | 确认 |
| F-007 系统日志 | CUT | **DEFER** | 用户修改: "运维排查问题时需要查看日志，暂时保留，后续归入系统运维场景" |
| F-008 数据可视化大屏 | CUT | CUT | 确认 |

## 下一步

1. 确认 CUT 分类，从需求文档中移除或归档 F-008(数据可视化大屏)
2. 确认 DEFER 分类，F-006(批量导入用户) 建议在用户量增长后实现，F-007(系统日志) 待系统运维场景明确后归入
3. 重新评估: `/feature-prune`
4. 配合功能审计交叉验证: `/feature-audit`

---

> 完整报告: `.allforai/feature-prune/prune-report.md`
> 行动清单: `.allforai/feature-prune/prune-actions.json`
> 决策日志: `.allforai/feature-prune/prune-decisions.json`
