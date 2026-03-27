## Phase 6：报告输出

### 保存报告文件

- `.allforai/testforge/testforge-analysis.json` — 审计分析数据
- `.allforai/testforge/testforge-fixes.json` — 修复记录
- `.allforai/testforge/testforge-report.md` — 人类可读报告
- `.allforai/testforge/e2e-chains.json` — E2E 链定义（如有生成）

### 报告输出要求（强制执行）

**不要只说"锻造完成"或"报告已保存"。你必须在对话中直接展示以下内容：**

**模式条件化**：标注 `[full/fix]` 的章节在 analyze 模式下省略（analyze 模式只输出审计结果，不输出锻造/修复/E2E 相关章节）。未标注的章节所有模式都输出。

```
## TestForge 质量锻造报告

> 执行时间: {时间}
> 执行模式: {full/analyze/fix}
> 覆盖范围: {N} 个子项目, {M} 个模块

### 审计总览

| 指标 | 数值 |
|------|------|
| 审计缺口总数 | {N}（unit:{u} component:{c} integration:{i} platform_ui:{p} e2e_chain:{e}） |
| 负空间推导场景数 | {N} |
| 基线测试 | 总数:{N} 通过:{pass} 失败:{fail} PRE_EXISTING_FAILURE:{N} |
| 4D+1 覆盖率 | D:{d}% I:{i}% L:{l}% U:{u}% DB:{db}% |

### 锻造总览 [full/fix]

| 指标 | 数值 |
|------|------|
| 补全测试数 | {N} |
| 发现业务 bug 数 | {N} |
| 修复业务 bug 数 | {N} |
| 负空间中发现真实 bug | {M} |
| 锻造轮次 | {N} |
| **未测试项 (NOT_TESTED)** | **{N}**（{原因列表}） |

> NOT_TESTED 项必须在报告中醒目展示。这些不是"通过"也不是"失败"——是"没有测到"。
> 常见原因：移动端模拟器不可用、E2E 测试工具未安装、当前 OS 不支持目标平台。
> 每个 NOT_TESTED 项列出：测试名称 + 原因 + 需要的环境。
| 最终测试通过率 | {N}% |
| **断言深度** | **L3:{n3}% L2:{n2}% L1:{n1}% L0:{n0}%** |

> 断言深度（Rule 28）：L3=值正确性 L2=结构性 L1=量化性 L0=存在性。
> L3 ≥ 60% = 优秀 | L3 ≥ 40% = 合格 | L3 < 40% = 惰性测试风险。

### 测试金字塔覆盖 [full/fix]

| 层级 | 锻造前 | 锻造后 | 变化 |
|------|--------|--------|------|
| Unit | {N} tests | {N} tests | +{delta} |
| Component | {N} tests | {N} tests | +{delta} |
| Integration | {N} tests | {N} tests | +{delta} |
| E2E Chain | {N} chains | {N} chains | +{delta} |
| Platform UI | {N} tests × {P} platforms | {N} tests × {P} platforms | +{delta} |

### 覆盖率变化（4D+1） [full/fix]

| 维度 | 锻造前 | 锻造后 | 变化 |
|------|--------|--------|------|
| Data | {before}% | {after}% | +{delta}% |
| Interface | {before}% | {after}% | +{delta}% |
| Logic | {before}% | {after}% | +{delta}% |
| UX | {before}% | {after}% | +{delta}% |
| DataBinding | {before}% | {after}% | +{delta}% |

### E2E 链清单 [full/fix]

| # | 链路名称 | 类型 | 步数 | 涉及子项目 | 状态 |
|---|---------|------|------|-----------|------|
| 1 | {从 business-flow 推导的链名} | 正向/负向 | {N} | {sub-projects} | ✅ PASS / ❌ FAIL / 📋 PLAN_ONLY |
...

### E2E 失败诊断（6V） [full/fix]

| 链路 | 失败步骤 | 主因维度 | 诊断结论 | 分类 | 修复线索 |
|------|---------|---------|---------|------|---------|
| ... | Step N | V1-V6 | ... | FIX_REQUIRED/CONTRACT_SYNC/ENV_ISSUE | ... |
...

### 跨平台 UI 覆盖 [full/fix, 仅跨平台项目]

| 子项目 | 框架 | 目标平台 | 可用平台 | 场景数 | 通过/失败 | PLATFORM_SPECIFIC_BUG |
|--------|------|---------|---------|--------|----------|----------------------|
| ... | Flutter/RN | android,ios,web | web ✓ android ✗ ios ✗ | {N} | {pass}/{fail} | {N} |

### 静态接缝预检修复（Step 4.0 deadhunt + fieldcheck） [full/fix]

| 工具 | 扫描结果 | Critical 修复 | Warning 记录 |
|------|---------|--------------|-------------|
| deadhunt | {dead_links} 死链, {crud_gaps} CRUD 缺口 | 修复 {N} 项 | {M} 项 |
| fieldcheck | {field_issues} 字段不一致 | 修复 {N} 项 | {M} 项 |

### 跨端数据流 & 状态机 [full/fix]

| 检查项 | 状态 |
|--------|------|
| 数据流完整性 | flows:{N} breaks:{M} |
| 状态机完备性 | transitions:{N} failures:{M} |
| 4D+1 跨端覆盖 | D:{d}% I:{i}% L:{l}% U:{u}% DB:{db}% → {E2E_PASS/FAIL} |

### 修复的业务 Bug 清单 [full/fix]

| # | 子项目 | 文件 | Bug 描述 | 发现来源 | 测试引用 |
|---|--------|------|---------|---------|---------|
| 1 | ... | ... | ... | ... | ... |
...

### 横向审计发现

| 类型 | 数量 | 示例 |
|------|------|------|
| MOCK_DRIFT | {N} | ... |
| ERROR_ASYMMETRY | {N} | ... |
| CHAIN_MISSING | {N} | ... |
...

### 外循环校验结果 [full]

| 检查项 | 状态 |
|--------|------|
| 意图保真（mission 覆盖） | ✓ / 缺 {N} 项 |
| 硬约束穿透 | ✓ / 缺 {N} 项 |
| 角色 CRUD 完整性 | ✓ / 缺 {N} 项 |
| 角色 E2E 链完整性 | ✓ / 缺 {N} 项 |

### KNOWN_FAILURE（未解决） [full/fix]

(仍失败的测试，附原因和建议)

### ⚠️ 上游产物覆盖矩阵（UPSTREAM_COVERAGE）— 哪些业务要求被验证了，哪些没有

> **这是报告中最重要的部分。** 自动化测试全绿 ≠ 产品没问题。如果 business-flows 里有 10 条流程但只有 6 条被 E2E 覆盖，那 4 条未覆盖的就是产品的验收盲区。

**生成规则**：逐个读取 `.allforai/` 中的上游产物，对每个条目检查"有没有自动化测试覆盖它"。未覆盖的条目 = 人工必验项。

```
## Business Flows 覆盖（读 business-flows.json）

对每条 business-flow：
  - 有 E2E chain 测试覆盖 → ✅ 自动化已验证
  - 仅有 unit/integration 测试覆盖 → ⚠️ 部分覆盖（自动化验了逻辑，人工需走通端到端）
  - 无任何测试覆盖 → ❌ HUMAN_REQUIRED — 附具体步骤：「以角色 X 登录 → 执行步骤 1/2/3 → 验证结果」

| Flow | 描述 | 自动化覆盖 | 人工验证 |
|------|------|-----------|---------|
| F001 | {flow_name} | ✅ E2E Chain 1 | — |
| F002 | {flow_name} | ⚠️ unit only | □ 以 {role} 身份端到端走通 |
| F003 | {flow_name} | ❌ 无 | □ 完整执行：{step1} → {step2} → {step3} → 验证 {expected_result} |

## Constraints 覆盖（读 constraints.json）

对每条 enforcement: "hard" 的约束：
  - 有穿透测试（unit/integration 直接验证约束条件）→ ✅
  - 无测试 → ❌ HUMAN_REQUIRED — 附具体步骤：「尝试违反此约束，验证系统是否拒绝」

| Constraint | 描述 | 自动化覆盖 | 人工验证 |
|------------|------|-----------|---------|
| C001 | {constraint_text} | ✅ unit test TG-xxx | — |
| C003 | {constraint_text} | ❌ 无 | □ 尝试：{violation_action} → 预期：系统拒绝并提示 {error_msg} |

## Use Cases 覆盖（读 use-case-tree.json）

对每个 use-case 的 acceptance_criteria：
  - 有对应断言 → ✅
  - 无对应测试 → ❌ HUMAN_REQUIRED — 附验收条件原文

| Use Case | 验收条件 | 自动化覆盖 | 人工验证 |
|----------|---------|-----------|---------|
| UC-001 | {acceptance} | ✅ | — |
| UC-007 | {acceptance} | ❌ | □ 验证：{acceptance_criteria_原文} |

## Role Permissions 覆盖（读 role-profiles.json）

对每个角色的权限边界：
  - 有正向测试（角色能做该做的事）→ ✅
  - 有反向测试（角色不能做不该做的事）→ ✅
  - 缺反向测试 → ❌ HUMAN_REQUIRED — 附越权测试步骤

| 角色 | 权限项 | 正向测试 | 反向测试 | 人工验证 |
|------|--------|---------|---------|---------|
| R001 管理员 | 删除用户 | ✅ | ✅ | — |
| R002 普通用户 | 删除用户 | — | ❌ | □ 用 R002 账号尝试调 DELETE /api/users/{id} → 预期 403 |

## Experience Map Screens 覆盖（读 experience-map.json，cr-visual 未执行时）

对每个 screen：
  - 有 platform_ui 或 E2E 测试覆盖 → ✅
  - 无测试 → ❌ HUMAN_REQUIRED — 附访问路径

> 如果上游产物（business-flows/constraints/use-case-tree/role-profiles）不存在 → 该维度跳过，但在报告中醒目标注：「⚠️ 无 {artifact_name}，无法评估业务覆盖率，建议补充上游产物后重新审计」
```

### ⚠️ 人工测试清单（HUMAN_REQUIRED）— 自动化无法覆盖的技术验证点

> 除上述业务覆盖盲区外，以下是 LLM/自动化工具在**技术层面**无法可靠验证的维度。LLM 根据项目特征动态生成。

```
## 感知质量（LLM 无法判断"感觉好不好"）

(若有动画/过渡效果) □ 动画流畅度 — 过渡是否丝滑？有没有掉帧/卡顿？
(若有移动端)       □ 触控响应 — 点击延迟是否可接受？滑动惯性是否自然？
(若有音视频)       □ 音视频同步 — 播放是否流畅？有没有音画不同步？
(若有深色模式)     □ 深色模式完整性 — 所有页面都适配了吗？有没有漏染的白色区域？
(始终)             □ 首屏加载体感 — 冷启动时用户看到内容的等待感是否可接受？

## 真实设备（自动化工具运行在桌面/模拟器，不等于真机）

(若有移动端)       □ 真机测试 — iOS Safari + Android Chrome 各一台真机走核心流程
(若有移动端)       □ 键盘遮挡 — 输入框聚焦后软键盘是否遮挡提交按钮？
(若有移动端)       □ 手势冲突 — 左滑返回与页面内左滑操作是否冲突？
(若有平板)         □ 平板布局 — 非手机非桌面的中间尺寸布局是否合理？

## 无障碍（自动化只能检查 ARIA 标签存在，无法验证体验）

(始终)             □ 键盘导航 — Tab 顺序是否符合视觉逻辑？焦点是否可见？
(始终)             □ 屏幕阅读器 — VoiceOver/TalkBack 朗读内容是否有意义？
(若有图片)         □ 图片 alt 文本 — alt 是否描述了图片业务含义（非"image1.png"）？
(若有颜色编码)     □ 色盲友好 — 仅靠颜色区分的信息（红绿状态）有没有文字/图标辅助？

## 安全（自动化测试覆盖了功能层，安全层需要专项审查）

(始终)             □ 敏感数据暴露 — 浏览器 Network 面板看 API 响应，有没有泄露密码/token/内部 ID？
(若有文件上传)     □ 恶意文件 — 上传 .exe/.html/.svg 文件，服务端是否拒绝或安全处理？
(若有富文本)       □ XSS — 输入 <script>alert(1)</script>，是否被转义？
(若有用户输入)     □ SQL 注入 — 输入 ' OR 1=1 -- ，后端是否参数化查询？
(若有权限系统)     □ 越权访问 — 用普通用户 token 直接调管理员 API，是否返回 403？

## 业务正确性（自动化验证了"代码实现"，业务逻辑需要人判断）

(始终)             □ 核心业务流程走通 — 以真实用户身份，从注册到完成核心操作走一遍
(若有支付)         □ 金额计算 — 手动计算订单金额，与页面显示是否一致？
(若有多角色)       □ 角色权限体验 — 每个角色登录后看到的内容是否符合业务预期？
(若有通知)         □ 通知触达 — 操作后是否收到了预期的邮件/短信/推送？内容对吗？
(若有多语言)       □ 翻译质量 — 自动翻译是否有语法错误或文化不适？

## 环境特异性（自动化测试的环境与生产环境不同）

(若部署到云)       □ 生产环境冒烟 — 部署后在生产 URL 走核心流程
(若有 CDN)         □ CDN 缓存 — 新版本部署后，CDN 是否正确更新？旧资源是否清理？
(若有 SSR)         □ SEO/OG 标签 — 分享到社交媒体时预览卡片是否正确？
(若有定时任务)     □ 定时任务验证 — cron job 是否按预期时间触发？结果是否正确？
```

> 清单生成规则：LLM 读项目的技术栈、功能特征、部署方式，动态裁剪以上条目。不适用的条目不输出。每个输出的条目必须附上**具体的测试步骤**（不是泛泛的"测一下"）。

### 下一步建议（条件化输出，仅列出实际需要的项）

(若有 KNOWN_FAILURE) 1. 处理 KNOWN_FAILURE 项
(若有 HUMAN_REQUIRED) 2. **完成人工测试清单中的所有项** — 这些是自动化无法覆盖的
(若 Path B 未执行，如 analyze 模式) 3. 运行 /testforge fix 执行锻造（含 E2E 链）
(若有 deadhunt/fieldcheck 修复) 4. 运行 /deadhunt incremental 回归验证
(若无 CI 覆盖率门禁) 5. 考虑配置 CI 覆盖率门禁
(若有 PRE_EXISTING_FAILURE) 6. 修复基线中已存在的 {N} 个失败测试
```

**关键：摘要必须包含具体的 bug 清单和修复详情，不能只给统计数字。用户看完报告就能知道修了什么、还剩什么、还要自己测什么。**

---

## 决策日志

每次用户通过 AskUserQuestion 确认决策时，追加记录到 `testforge-decisions.json`：

```json
{
  "decisions": [
    {
      "step": "Phase 0",
      "item_id": "scope",
      "decision": "confirmed",
      "value": "all sub-projects",
      "decided_at": "ISO8601"
    }
  ]
}
```

**输出路径**：`.allforai/testforge/testforge-decisions.json`

**resume 模式**：已有 decisions.json 时，已确认步骤自动跳过（展示一行摘要），从第一个无决策记录的步骤继续。

---

## 测试代码规范（跨技术栈通用原则）

生成测试代码时遵循以下原则（不特化任何框架）：

1. **行为驱动命名** — describe/group 按功能分组，不按方法名
2. **Given-When-Then 结构** — 每个测试：准备数据 → 执行操作 → 验证结果
3. **表驱动优先**（多参数场景）— 同一逻辑的多个输入用 table-driven / parameterized
4. **禁止 Mock** — 所有测试必须连真实依赖（DB/缓存/后端 API/service/repository）。依赖不可用 = NOT_TESTED。唯一例外：不可控的外部第三方（支付/OAuth/短信）可在 adapter 层 mock
5. **一个测试一个断言意图** — 可以有多个 expect/assert，但必须验证同一个行为
6. **错误路径必测** — 每个 catch/error return/throw 至少一个测试
7. **E2E 链数据自给自足** — 每条链在测试内创建所需数据，不依赖外部 seed 或其他链
8. **导航路径封装** — E2E/Integration test 中反复出现的导航操作（登录→首页→议题详情→会议室）必须抽取为 helper 函数或 Page Object 类。每个测试直接调 `loginAndGoToHome()` / `navigateToTopic(id)`，不在每个测试里重复写 find/tap 导航代码。导航路径变化时只改一处
9. **认证状态复用** — 多个测试共享同一登录态时，第一个测试执行真实登录并保存状态，后续测试复用（Flutter: 共享 app 实例；Web: storageState）。不每个测试都重新登录（太慢）

---

