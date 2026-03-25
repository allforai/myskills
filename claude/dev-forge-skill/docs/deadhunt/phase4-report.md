## Phase 4: 报告生成

### 4.0 保存基线 & 增量对比

每次验证完成后，保存当前结果作为基线：

```typescript
// 保存基线
async function saveBaseline(outputDir: string, report: ValidationReport) {
  const baselinePath = path.join(outputDir, 'reports', 'baseline.json');
  const baseline = {
    saved_at: new Date().toISOString(),
    summary: report.summary,
    dead_links: report.dead_links.map(l => ({ url: l.url, layer: l.layer, intent: l.intent })),
    crud_issues: report.crud_issues.map(i => ({ module: i.module, missing: i.missing })),
    ghost_apis: report.ghost_apis.map(a => ({ method: a.method, path: a.path })),
  };
  fs.writeFileSync(baselinePath, JSON.stringify(baseline, null, 2));
}

// 与上次对比
function compareWithBaseline(
  current: ValidationReport, baselinePath: string
): IncrementalDiff {
  const baseline = JSON.parse(fs.readFileSync(baselinePath, 'utf-8'));

  return {
    new_issues: current.all_issues.filter(i =>
      !baseline.all_issues.some((b: any) => b.url === i.url && b.layer === i.layer)
    ),
    fixed_issues: baseline.all_issues.filter((b: any) =>
      !current.all_issues.some((i: any) => i.url === b.url && i.layer === b.layer)
    ),
    unchanged_issues: current.all_issues.filter(i =>
      baseline.all_issues.some((b: any) => b.url === i.url && b.layer === i.layer)
    ),
  };
}
```

增量报告在报告顶部显示变化摘要：

```markdown
## 📈 与上次对比 (baseline: 2026-02-14)

| 变化 | 数量 |
|------|------|
| 🆕 新增问题 | 3 |
| ✅ 已修复 | 5 |
| ⏳ 未变化 | 8 |

### 🆕 新增问题
| 类型 | 位置 | 说明 |
|------|------|------|
| 死链 L2 | 商品 > 新按钮 | 新加的按钮指向 404 |

### ✅ 已修复（上次有这次没有）
| 类型 | 位置 | 说明 |
|------|------|------|
| 死链 L1 | 菜单 > 日报管理 | 菜单已清理 ✅ |
| 死链 L2 | 用户 > 查看按钮 | 路由已修复 ✅ |
```

### 4.0.1 收敛分析报告

如果本次验证执行了多轮收敛，在报告中展示收敛过程。

读取 `static-analysis/convergence.json` 和 `reports/convergence-deep.json`（如果存在），生成以下段落：

```markdown
### 收敛分析

| 阶段 | 基线发现 | 收敛追加 | 追加率 | 收敛轮次 |
|------|---------|---------|--------|---------|
| 静态分析 | {baseline} | +{bonus} | +{rate}% | {rounds}轮 |
| 深度测试 | {baseline} | +{bonus} | +{rate}% | {rounds}轮 |

> 如果不做多轮收敛，将漏掉 {total_bonus} 个问题（总 {total} 个中的 {miss_rate}%）
```

**每个 finding 的 source 标签也体现在详细问题列表中**，让用户知道哪些问题是收敛追加轮次发现的：

```markdown
| 层级 | 位置 | 问题 | 发现方式 | 建议 |
|------|------|------|---------|------|
| L1 | 菜单 > 日报管理 | /reports/daily 404 | 基线扫描 | 删菜单 |
| L2 | 商品 > 智能推荐按钮 | /products/ai-recommend 404 | 模式学习 | 隐藏按钮 |
| L3 | 用户 > 导入接口 | POST /api/users/import 无入口 | 交叉验证 | 添加导入按钮 |
| L1 | 支付 > 退款列表 | /payments/refund 404 | 扩散搜索 | 修复路由 |
```

`发现方式` 列取自 finding 的 `source` 字段，映射为中文：
- `baseline` → `基线扫描`
- `pattern_learning` → `模式学习`
- `cross_validation` → `交叉验证`
- `diffusion` → `扩散搜索`

### 4.1 单端报告

每个前端生成独立的 `validation-report-{client_id}.md`：

```markdown
# 产品验证报告 — Admin 后台

> 验证对象: Admin 管理后台 (super_admin)
> 验证时间: 2026-02-16
> 运行地址: http://localhost:3000

## 总览

| 指标 | 数值 |
|------|------|
| 本端涉及模块 | 12 |
| 已测试 | 12 |
| 测试用例总数 | 48 |
| 通过 | 39 |
| 失败 | 7 |
| 警告 | 2 |
| 跨端分工（正常跳过） | 3 |

## 🔴 严重问题 (需立即修复)

### 1. 死链 / 404 问题（按处置意图分类）

#### 🔴 FIX — 功能需要，修复代码 (8 个)
| 层级 | 位置 | 问题 | 判定依据 | 建议 |
|------|------|------|---------|------|
| L2 | 用户列表 > 查看按钮 | /users/123/detail 404 | API✅ 组件✅ 其他拼写 |
| L3 | 仪表盘加载 | GET /admin/dashboard/stats 404 | 页面需要此数据 | 修复后端接口 |
| L3 | 订单筛选 | GET /admin/orders?status=refund 404 | 筛选条件必需 | 后端缺少筛选参数支持 |

#### 🟡 CLEAN — 功能已废弃，清理入口 (7 个)
| 层级 | 位置 | 问题 | 判定依据 | 清理范围 |
|------|------|------|---------|---------|
| L1 | 菜单 > 日报管理 | /reports/daily 404 | API❌ 组件12行 TODO 30天未动 | 删菜单+删路由+删组件 |
|  | 菜单 > 旧版报表 | /legacy/reports 404 | API❌ 路由❌ 组件❌ | 删菜单配置 |
| L4 | 全局 | /assets/ReportPage-xxx.js chunk 404 | 关联的日报管理已废弃 | 随日报管理一起清理 |

#### 🟠 HIDE — 开发中，隐藏入口 (4 个)
| 层级 | 位置 | 问题 | 判定依据 | 建议 |
|------|------|------|---------|------|
| L1 | 菜单 > 数据中心 | /data-center 白屏 | 组件有 TODO 最近有修改 | 菜单加 feature flag |
| L2 | 商品列表 > 智能推荐 | /products/ai-recommend 404 | API 还没做 前端刚提交 | 按钮加 v-if 控制 |

#### 🔵 PERM — 不该看到，修复权限 (2 个)
| 层级 | 位置 | 问题 | 判定依据 | 建议 |
|------|------|------|---------|------|
| L2 | 系统设置 > 审计管理 | 普通用户能看到按钮 | API 有权限控制但前端没过滤 | v-permission 失效 |

#### ❓ UNKNOWN — 需人工确认 (2 个)
| 层级 | 位置 | 问题 | 现有线索 |
|------|------|------|---------|
| L2 | 商品列表 > 对比功能 | /products/compare 404 | 组件存在(80行) 但30天未动, API 存在但返回 500 |
| L3 | 个人中心 | GET /api/user/points 404 | 积分系统不确定是否上线 |

### 2. 模块不完整（本端职责范围内的缺失）
| 模块 | 缺失功能 | 本端应有? | 建议 |
|------|---------|----------|------|
| 商品管理 | 无批量导入 | ✅ 是 (admin 应有) | 添加导入按钮 |
| 订单管理 | 无导出 | ✅ 是 (admin 应有) | 添加导出功能 |

## 🟢 跨端正常分工（非问题）
 | 本端无此操作 | 原因 | 负责端 |
|------|------------|------|--------|
| 订单 | 无新增入口 | 下单由客户端完成 | customer_h5, customer_app |
| 评价 | 无新增入口 | 评价由客户端提交 | customer_h5, customer_app |
| 评价 | 无编辑入口 | 用户自行修改评价 | customer_h5, customer_app |

## 🟡 警告 (建议修复)
... (同之前)

## ✅ 通过的模块
- 商品管理 (CRUD + 审核上架 完整)
- 用户管理 (CRUD 完整)
- 商户管理 (CRUD 完整)
- 系统配置 (CR 正常)
```

### 4.2 跨端汇总报告（批量验证时生成）

当验证多个前端时，额外生成 `validation-report-summary.md`：

```markdown
# 跨端验证汇总报告

## 验证范围
| 前端 | 角色 | 平台 | Peer Group | 测试方式 | 状态 | 问题数 |
|------|------|------|-----------|---------|------|-------|
| Admin 后台 | super_admin | web | — | Playwright | ✅ 已验证 | 7 |
| 商户后台 | merchant | web | — | Playwright | ✅ 已验证 | 5 |
| 客户 PC 网站 | customer | web | customer | Playwright | ✅ 已验证 | 2 |
| 客户 H5 | customer | h5 | customer | Playwright | ✅ 已验证 | 3 |
| 客户 App | customer | app | customer | patrol | ✅ 已验证 | 4 |
| 客户小程序 | customer | miniprogram | customer | mp_automator | ✅ 已验证 | 6 |

## 全局 CRUD 覆盖率
> 所有前端合计，每个模块的 CRUD 是否被完整覆盖

| 模块 | C | R | U | D | 额外操作 | 全覆盖? |
|------|---|---|---|---|---------|--------|
| 商品 | ✅ admin+merchant | ✅ 全部 | ✅ admin+merchant | ✅ admin | 审核✅ 导入✅ | ✅ |
| 订单 | ✅ customer | ✅ 全部 | ✅ admin | ✅ admin | 发货✅ 退款✅ | ✅ |
| 评价 | ✅ customer | ✅ 全部 | ✅ customer | ✅ admin | 审核✅ 回复✅ | ✅ |
| 优惠券 | ✅ admin+merchant | ✅ 全部 | ✅ admin | ✅ admin | 领取✅ | ✅ |
| 通知 | ✅ admin | ✅ 全部 | ✅ admin | ✅ admin | — | ⚠️ 商户端缺少通知列表 |

## 跨端一致性检查 (Peer Group)
> 同角色 (peer_group=customer) 的多端功能是否一致
> 差异分为：🟢平台专属(正常) vs 🔴核心缺失(问题)

| 模块 | 核心功能 | customer_web | customer_h5 | customer_app | customer_mp | 一致? |
|------|---------|-------------|-------------|-------------|-------------|-------|
| 商品浏览 | R+收藏+加购 | ✅ +对比🟢 | ✅ +微信分享🟢 | ✅ +AR🟢+扫码🟢 | ✅ +分享🟢 | ✅ 核心一致 |
| 下单 | CR+取消 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 评价 | CR | ✅ | ✅ | ✅ | 🔴 缺少评价入口 | ❌ 小程序缺失 |
| 个人中心 | RU | ✅ | ✅ | ✅ +生物识别🟢 | ✅ | ✅ 核心一致 |
| 退款 | 申请退款 | ✅ | ✅ | ✅ | 🔴 无退款入口 | ❌ 小程序缺失 |

> 🟢 = 平台专属差异 (platform_capabilities 中定义的能力)
> 🔴 = 核心功能缺失 (对等端有但此端没有，且非平台限制)

## 🔴 全局问题
> API 提供了操作但所有前端都没有对应入口

| API 端点 | 方法 | 各端是否有入口 | 结论 |
|----------|------|--------------|-----|
| /admin/coupons/batch-delete | DELETE | admin ❌ merchant ❌ | ⚠️ 批量删除无入口 |
| /api/user/avatar | PUT | h5 ❌ app ❌ | 🔴 用户无法更换头像 |
```

### 4.3 修复任务清单

输出 `fix-tasks.json`，每个任务标注归属的前端：

```json
{
  "tasks": [
    {
      "id": "FIX-001",
      "client": "admin",
      "title": "[死链] 侧边栏 > 日报管理 链接404",
      "severity": "critical",
      "module": "导航",
      "description": "菜单中的'日报管理'指向 /reports/daily，但该路由对应的组件不存在",
      "suggestion": "1. 创建日报管理页面组件\n2. 或从菜单配置中移除该入口",
      "file_hints": ["apps/admin/src/config/menu.ts:45"]
    },
    {
      "id": "FIX-002",
      "client": "merchant",
      "title": "[不完整] 商户后台-通知模块缺少列表入口",
      "severity": "high",
      "module": "通知",
      "description": "通知模块在商户后台没有入口，商户无法查看系统通知",
      "suggestion": "在商户后台菜单添加通知列表入口",
      "file_hints": ["apps/merchant/src/config/menu.ts"]
    },
    {
      "id": "FIX-003",
      "client": "customer_h5,customer_app",
      "title": "[不完整] 用户端缺少头像更换功能",
      "severity": "high",
      "module": "个人中心",
      "description": "API 提供了 PUT /api/user/avatar 但 H5 和 App 都没有对应的入口",
      "suggestion": "在个人中心页面添加头像更换功能",
      "file_hints": ["apps/h5/src/pages/profile/", "../flutter-app/lib/pas/profile/"]
    }
  ]
}
```
