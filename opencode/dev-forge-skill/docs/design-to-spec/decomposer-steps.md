# Decomposer Steps — design-to-spec

> This file is loaded by the Decomposer Agent. It covers Step 4.
> Decomposer's job: read design.md → generate flat B0-B5 functional tasks.
> Decomposer does NOT generate quality sub-tasks (HARDEN/DNA/POLISH) — that's Auditor's job.

---

## Step 4: Tasks 生成（由 Decomposer Agent 执行）

> Decomposer 读 Architect 产出的 design.md → 拆分为 B0-B5 平铺功能任务。
> 质量子任务（B2.HARDEN / B3.DNA / B3.POLISH / B3.i18n 等）由 Auditor 在 Step 4.3 补充，不是 Decomposer 的职责。
>
> **大型项目模块分批模式**：当编排器指定了模块组（如"只处理 auth+users 模块"）时，
> Decomposer 只读 design.md 中对应的 `## Module: {name}` 段落，只为这些模块生成任务。
> 数据模型部分（B1）仍需读完整实体列表（跨模块共用），但 B2 端点只处理指定模块。
> 未指定模块组时（小/中型项目），正常读全量 design.md。

按开发层分 Batch，每任务遵循原子标准:
  - 1-3 文件，15-30 分钟，单一目的
  - 指明具体文件路径（基于技术栈 template 约定）
  - 标注 _Requirements_ 和 _Leverage_ 引用
  - 标注 _Guardrails_（← E3，溯源 task.rules/exceptions/audit ID）
  - 标注 _Risk_（← E4，from task.risk_level，HIGH 任务优先 review）
  - 标注 _Acceptance_（← 验收条件，每个 B2 任务必须包含，见下方「验收条件规范」）

> B3.DNA / B2.HARDEN / B3.POLISH / B5 细粒度测试等子任务由 **Auditor 在 Step 4.3** 补充生成。
> Decomposer 不需要关心这些——专注于功能分解即可。

---

### 验收条件规范（B2 任务强制）

> 每个 B2 端点任务必须包含 `_Acceptance_` 字段，列出可执行的验收条件。
> 验收条件是 Phase 5 product-verify 的判定基准 — 没有验收条件的任务等于没有完成标准。
> 这是防止「代码有但行为不对」和「功能缺失漏到 Phase 5 才发现」的核心防线。

**验收条件格式**：
```
_Acceptance_:
- `METHOD /path` → expected_status, response_assertion
- `METHOD /path` (edge_case) → expected_status, "error_message"
```

**验收条件粒度规则**：
| 任务风险 | 最低验收条件数 | 必须覆盖 |
|---------|-------------|---------|
| _Risk: HIGH_ | ≥ 4 条 | happy path + 权限拒绝 + 边界条件 + 幂等/并发 |
| _Risk: MEDIUM_ | ≥ 3 条 | happy path + 权限拒绝 + 一个异常路径 |
| _Risk: LOW_ | ≥ 2 条 | happy path + 一个异常路径 |

**验收条件来源优先级**：
1. `use-case-tree.json` 的 Given/When/Then（最权威）
2. `task-inventory.json` 的 exceptions / rules（业务规则）
3. LLM 基于 API 语义推导的边界条件（兜底）

**B3 前端任务的验收条件**（推荐但非强制）：
```
_Acceptance_:
- 页面加载后显示列表数据
- 点击操作按钮 → 弹出确认对话框
- 操作成功后列表自动刷新
```

---

### 后端 B2 端点级原子性规则（强制）

> 后端 B2 任务必须按**端点组**拆分，不允许按 controller 级别合并。
> 违反此规则是 design-to-spec 历史上最常见的质量缺陷——controller 级任务导致
> 执行 agent 只实现"最显眼"的端点，漏掉子功能（如只做 GET list，漏 approve/reject/stats）。

**拆分粒度规则**：
| 场景 | 拆分方式 | 示例 |
|------|---------|------|
| 同一实体的标准 CRUD | 可合并为 1 个任务（增删改查紧耦合） | `B2.x 用户 CRUD (GET list + GET detail + POST + PUT + DELETE)` |
| 独立业务逻辑端点 | 必须拆为独立任务 | `B2.x 商户审批 (POST /merchants/:id/approval)` |
| 状态变更端点 | 每个状态变更 = 1 个任务 | `B2.x 广告审核通过`, `B2.y 广告审核驳回` |
| 聚合/统计端点 | 独立任务 | `B2.x 广告统计数据 (GET /ad-campaigns/:id/stats)` |
| 关联操作端点 | 独立任务 | `B2.x 邀请码生成 (POST /invite-codes)` |

**反模式（禁止）**：
```
✗ B2.45 [backend] Admin ad management controller
  - 实现广告管理控制器（列表、审核、统计）
  → 太粗！agent 只会实现列表，漏掉审核和统计

✓ B2.45 [backend] Admin 广告活动列表
  Files: handler/admin_ad_handler.go, service/ad_service.go
  - GET /admin/ad-campaigns（分页、筛选）
✓ B2.46 [backend] Admin 广告活动审核（approve/reject）
  Files: handler/admin_ad_handler.go, service/ad_service.go
  - POST /admin/ad-campaigns/:id/approve
  - POST /admin/ad-campaigns/:id/reject
  - 审核需更新状态 + 通知商户
✓ B2.47 [backend] Admin 广告统计数据
  Files: handler/admin_ad_handler.go, service/ad_stats_service.go
  - GET /admin/ad-campaigns/:id/stats
  - 聚合展示/点击/消费数据
```

**自检规则**（Step 4 生成完毕后立即执行）：
对每个后端 B2 任务，检查任务描述中包含的端点数量：
- 标准 CRUD (GET list + GET detail + POST + PUT + DELETE) → OK（最多 5 端点）
- 非 CRUD 端点 > 2 个且业务逻辑独立 → **必须拆分**
- 任务标题包含"管理"/"controller"/"全部" → **高危信号，LLM 重新检查是否应拆分**

---

### 聚合字段推导任务

按需在 tasks.md 末尾生成专用任务批次（从聚合字段推导）：
  - 审计日志任务（从 task.audit 聚合 → audit_logs 表+中间件+测试）
  - 审批流任务（从 task.approver_role 聚合 → 审批 API+状态机+测试）
  - 配置管理任务（从 config_items 聚合 → 配置表+端点+测试）

---

### Dev Bypass 任务生成（当 dev_mode.enabled = true）

在 B2（后端 API）之后、B3（UI）之前，插入 dev bypass 任务：

```
B2.5: Dev Bypass 实现
  - 每个 bypass → 1 个任务
  - 任务标记 `[DEV_ONLY]`，构建时剔除
  - 文件限定在 `*_dev.go` / `*.dev.ts`

  示例：
  - [ ] B2.5.1 [backend] [DEV_ONLY] 外部网关 dev bypass
    Files: `services/gateway/gateway_dev.go`
    行为：magic value 映射（test_ok→成功, test_fail→失败, test_timeout→超时），延迟 1s 触发回调
    守卫：`//go:build dev` + 运行时 env 检查
    _Bypass: external_gateway.auto_callback_

  - [ ] B2.5.2 [backend] [DEV_ONLY] 短信验证 dev bypass
    Files: `services/sms/sms_dev.go`
    行为：13800000001-09 + "123456" 万能码
    守卫：`//go:build dev` + 运行时 env 检查
    _Bypass: sms_verification.magic_value_
```

同时在 B5（测试）中追加：

```
  - [ ] B5.x [ci] [DEV_ONLY] Dev bypass 安全防线
    Files: `.github/workflows/dev-mode-lint.yml`, `.husky/pre-commit`（或等效）
    行为：CI 扫描 *_dev 文件不被生产代码 import；pre-commit hook 检查
    _Bypass: ci_rules_
```

---

### 功能分解边界

> B2 主任务只管 happy path + `[DERIVED]` 异常。
> HARDEN 子任务、测试细化等由 Auditor 在 Step 4.3 补充。

Decomposer 仍需生成粗粒度 B5 模块测试（按子项目 1-3 个）。
Auditor 在 Step 4.3 补充细粒度测试（从 Acceptance 派生）。

B5 中还应包含埋点验证任务：验证关键事件是否正确触发、属性是否完整、漏斗是否连通。

**B5 视觉还原度验证**（当 `<BASE>/ui-design/screenshots/` 存在时）：
生成的前端页面可用 Playwright 截图，与 `ui-design/screenshots/{screen_id}.png` 中的设计截图做视觉对比。
视觉对比是辅助验证手段，不作为阻断门 — 用于发现明显的布局偏移、配色错误、组件缺失等问题。
在 B5 测试任务中追加：
```
  - [ ] B5.x [frontend] 视觉还原度验证
    Files: `tests/visual/screenshot-compare.spec.ts`（或等效）
    行为：Playwright 逐页截图 → 与 ui-design/screenshots/ 设计稿截图对比
    阈值：根据组件重要性和视觉精度要求动态判定，记录差异报告
    _Source: ui-design/screenshots/_
```
→ Batch 结构因子项目类型而异（见下文）
→ 写入 .allforai/project-forge/sub-projects/{name}/tasks.md
→ 输出进度: 「{name}/tasks.md ✓ ({N} 任务, B0-B5)」（不停，汇总到 Step 4.5）

---

### B3 任务分批（component-spec.json 存在时）

当 component-spec.json 存在时，B3 任务分批调整：

**B3 Round 1**（共享组件优先）：
- 实现 component-spec.json 中的 shared_components
- 每个共享组件一个任务，含 variants + a11y 实现
- 任务元数据追加：`component_spec_ref: true`

**B3 Round 2+**（页面组件）：
- 页面级组件引用 Round 1 已实现的共享组件
- 如有 Stitch HTML → 任务追加 `stitch_ref: screen_id` + `stitch_html: 文件路径`

---

### 关键边界说明

**Decomposer 只做功能分解**：
> Decomposer 只管拆 B0-B5 平铺的功能任务（happy path + `[DERIVED]` 异常）。
> **不做**注意力分离拆分（HARDEN/DNA/POLISH/i18n 等）。
> 那些是 Auditor 的工作——见 Step 4.3 的「注意力分离补充」。
>
> 原因：让 Decomposer 既拆功能又拆质量维度 = 7 个关注点 → 注意力分散。
> Decomposer 做好一件事（功能分解），Auditor 做好一件事（质量补充）。

> B3.DNA / B2.HARDEN / B3.POLISH 等由 Auditor 补充。
