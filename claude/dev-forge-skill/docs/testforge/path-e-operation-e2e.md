# 路径 E：E2E 操作链 — 单站操作驱动测试

> **核心原则：测试必须"做"，不能只"看"。每条链以操作产生数据为驱动。**
>
> 与 Path B（跨站业务链）的区别：
> - Path E 在**单个前端子项目**内测试完整 CRUD 操作链路（不跨站）
> - Path B 测试**跨 ≥2 个子项目**的业务流（需要角色切换）
> - Path E 排在 Chain 0 之后**立即执行**（最高优先级）
> - Path B 排在 Path A/D/C 之后执行

## 为什么需要 Path E

实战发现：Path B 的设计要求"全靠 UI 种子数据"（B.4），在实际执行中有两个致命问题：

1. **太慢太脆弱**：通过 UI 创建一个 draft 场景包需要填表单 → 选模板 → 提交 → 等待，一步失败整条链断裂
2. **导致退化为"只读巡视"**：因为 UI 种子太难，LLM 倾向跳过种子，直接"看已有数据"→ 变成烟雾测试

Path E 的解决方案：**API 种子 + UI 操作 = 最佳平衡**

```
API 种子（beforeAll）：快速、可靠、确定性
  ↓ 数据就位
UI 操作（test body）：真实模拟用户操作，测接缝层
  ↓ 操作完成
跨页面验证：操作的结果在另一个页面/组件可见
```

## E.1 前置条件

- Chain 0 冒烟通过（应用可达 + 登录可行）
- 后端 API 运行中
- 前端 dev server 运行中

**不依赖** Path A/D/C 的完成。Path E 和 Path A 可并行执行。

## E.2 测试基础设施要求

每个有前端的子项目必须有：

```
e2e/helpers/
  auth.ts   — UI 登录 helper（已有）
  api.ts    — API 数据种子 helper（Path E 新增）
```

### api.ts 标准规范

```typescript
// 管理端 API 基础地址
const API_BASE = 'http://localhost:{backend_port}';

// --- 必须实现的函数 ---

// 管理端登录 → 返回 JWT token
export async function getAdminToken(): Promise<string>

// 注册消费者测试用户 → 返回 { token, userId }
export async function registerTestUser(suffix: string): Promise<{ token: string; userId: string }>

// 每个可写实体的 create + delete 函数
export async function createXxx(token: string, ...args): Promise<string>  // 返回 ID
export async function deleteXxx(token: string, id: string): Promise<void>

// --- 设计原则 ---
// 1. 所有函数直接调后端 REST API，不经过前端
// 2. 返回值只返回 ID 或简单 DTO，不返回完整响应
// 3. 错误时抛出包含 HTTP 状态码和消息的 Error
// 4. 用于 beforeAll 种子数据 + afterAll 清理
```

## E.3 操作链推导

从 Phase 1 的 operation_inventory（见下方 Phase 1 新增维度）推导：

```
对每个前端页面的每个 mutation 操作（按钮/表单/确认框）：
  → 生成一条 E2E 操作链 test case

操作分类：
  CREATE  — 通过表单创建实体
  UPDATE  — 编辑已有实体
  DELETE  — 删除实体
  STATE   — 状态变迁（approve/reject/archive/disable/enable）
  ACTION  — 独立操作（reply/export/test-connection）
```

## E.4 正向+负向配对（铁律 #31 — 强制要求）

**每个 mutation 操作必须成对测试正向和负向路径：**

| 操作 | 正向测试 | 负向测试（至少一个） |
|------|---------|-------------------|
| CREATE | 填写有效数据 → 提交 → 验证出现 | 空必填字段 → 提交 → 验证表单错误提示 |
| DELETE | 删除无关联实体 → 验证消失 | **删除有关联数据的实体 → 验证拒绝 + 错误 toast + 数据仍在** |
| UPDATE | 修改为有效值 → 保存 → 验证变化 | 修改为无效值 → 保存 → 验证拒绝 |
| STATE | 合法状态转换 → 验证 badge 变化 | 非法状态转换 → 验证拒绝 |
| ACTION | 正常执行 → 验证结果 | 依赖不可用时执行 → 验证错误提示 |

> **为什么负向 DELETE 是最重要的负向测试**：
> 数据库有 FK 约束，后端会返回 409 CONFLICT，但前端的错误处理链路（API interceptor → mutation onError → toast → dialog 状态）是最容易断的接缝。
> 实战数据：删除有关联分类时前端报错 — 因为 ConfirmDialog 的 onConfirm 吞掉了 mutateAsync 的异常。
> 这种 bug 单元测试永远测不到（不经过真实 HTTP 调用），只有 E2E 负向操作能暴露。

## E.5 链结构：API Seed + UI Operate + Cross-Page Verify

每条 E2E 操作链的结构：

```typescript
test.describe.serial("Chain: {实体名} {操作类型} Lifecycle", () => {
  let adminToken: string;
  let seededId: string;  // API 创建的种子数据 ID

  test.beforeAll(async () => {
    // 1. API 登录获取 token
    adminToken = await getAdminToken();
    // 2. API 种子必要数据（快速、可靠）
    seededId = await createXxx(adminToken, { ... });
    // 3. 如果需要关联数据，也通过 API 创建
  });

  test("正向：通过 UI 执行操作", async ({ page }) => {
    await adminLogin(page);
    // 导航 → 找到种子数据 → 执行 UI 操作 → 验证结果
  });

  test("负向：操作被拒绝时的 UI 行为", async ({ page }) => {
    await adminLogin(page);
    // 导航 → 构造失败条件 → 执行 UI 操作 → 验证错误提示 + 数据未变
  });

  test("跨页面验证：操作结果在审计日志可见", async ({ page }) => {
    await adminLogin(page);
    // 导航到审计日志 → 验证操作记录存在
  });

  test.afterAll(async () => {
    // API 清理种子数据（try/catch 忽略错误）
  });
});
```

## E.6 跨页面验证清单（每条链至少覆盖一个）

| 验证模式 | 含义 | 示例 |
|----------|------|------|
| 操作→审计日志 | 操作后审计日志页有对应记录 | 创建分类 → 审计日志有 POST /categories |
| 操作→列表页 | 创建/删除后列表页数据变化 | 创建分类 → 分类树出现新节点 |
| 操作→统计 | 操作后 Dashboard 统计变化 | 发布场景包 → Scene Packs 计数 +1 |
| 操作→状态级联 | 状态变更后关联按钮/标签变化 | 审批通过 → "Approve" 按钮消失 |
| 操作→toast | 操作成功/失败的即时反馈 | 删除成功 → toast "Category deleted" |

## E.7 错误 toast 验证协议

**Sonner/shadcn toast 在 Playwright 中的选择器**：

```typescript
// Sonner toast 在 <region role="region" aria-label="Notifications"> 容器中
const toastRegion = page.getByRole("region", { name: /notification/i });

// 验证成功 toast
await expect(toastRegion.getByText("Category deleted")).toBeVisible({ timeout: 5000 });

// 验证错误 toast
await expect(toastRegion.getByText(/cannot delete/i)).toBeVisible({ timeout: 5000 });

// 不要用 page.getByText() — toast 可能在 portal 容器中，getByText 找不到
```

## E.8 与 Path B 的关系

```
Path E（单站操作链）        Path B（跨站业务链）
├─ 单个前端子项目内         ├─ 跨 ≥2 个子项目
├─ API 种子 + UI 操作       ├─ UI 种子 + UI 操作（或 API 种子在 beforeAll）
├─ Chain 0 后立即执行       ├─ Path A/D/C 完成后执行
├─ 测单个 CRUD 操作链路     ├─ 测完整业务流跨端流转
├─ 正向+负向配对            ├─ 正向链+负向链
└─ 发现：接缝 bug、错误处理  └─ 发现：数据穿透、角色越权
```

Path E 通过后，Path B 可以复用 Path E 创建的 api.ts helpers。
Path E 发现的 BIZ_BUG 应在 Path B 之前修复（否则 Path B 也会失败）。

## E.9 收敛

- 每个前端子项目独立计数
- 正向测试 max 3 轮 CG-1
- 负向测试不消耗 CG-1 轮次（负向测试失败 = 发现了 BIZ_BUG，立即修复）
