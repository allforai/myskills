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
| 4D 覆盖率 | D:{d}% I:{i}% L:{l}% U:{u}% |

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
> 常见原因：移动端模拟器不可用、Patrol/Maestro 未安装、非 macOS 无法测 iOS。
> 每个 NOT_TESTED 项列出：测试名称 + 原因 + 需要的环境。
| 最终测试通过率 | {N}% |

### 测试金字塔覆盖 [full/fix]

| 层级 | 锻造前 | 锻造后 | 变化 |
|------|--------|--------|------|
| Unit | {N} tests | {N} tests | +{delta} |
| Component | {N} tests | {N} tests | +{delta} |
| Integration | {N} tests | {N} tests | +{delta} |
| E2E Chain | {N} chains | {N} chains | +{delta} |
| Platform UI | {N} tests × {P} platforms | {N} tests × {P} platforms | +{delta} |

### 覆盖率变化（4D） [full/fix]

| 维度 | 锻造前 | 锻造后 | 变化 |
|------|--------|--------|------|
| Data | {before}% | {after}% | +{delta}% |
| Interface | {before}% | {after}% | +{delta}% |
| Logic | {before}% | {after}% | +{delta}% |
| UX | {before}% | {after}% | +{delta}% |

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
| 4D 跨端覆盖 | D:{d}% I:{i}% L:{l}% U:{u}% → {E2E_PASS/FAIL} |

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

### 下一步建议（条件化输出，仅列出实际需要的项）

(若有 KNOWN_FAILURE) 1. 处理 KNOWN_FAILURE 项
(若 Path B 未执行，如 analyze 模式) 2. 运行 /testforge fix 执行锻造（含 E2E 链）
(若有 deadhunt/fieldcheck 修复) 3. 运行 /deadhunt incremental 回归验证
(若无 CI 覆盖率门禁) 4. 考虑配置 CI 覆盖率门禁
(若有 PRE_EXISTING_FAILURE) 5. 修复基线中已存在的 {N} 个失败测试
```

**关键：摘要必须包含具体的 bug 清单和修复详情，不能只给统计数字。用户看完报告就能知道修了什么、还剩什么。**

---

## 决策日志

每次用户确认决策时，追加记录到 `testforge-decisions.json`：

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
4. **Mock 最小化** — 只 mock 外部依赖（HTTP、DB），不 mock 被测模块的内部方法
5. **一个测试一个断言意图** — 可以有多个 expect/assert，但必须验证同一个行为
6. **错误路径必测** — 每个 catch/error return/throw 至少一个测试
7. **E2E 链数据自给自足** — 每条链在测试内创建所需数据，不依赖外部 seed 或其他链
8. **导航路径封装** — E2E/Integration test 中反复出现的导航操作（登录→首页→议题详情→会议室）必须抽取为 helper 函数或 Page Object 类。每个测试直接调 `loginAndGoToHome()` / `navigateToTopic(id)`，不在每个测试里重复写 find/tap 导航代码。导航路径变化时只改一处
9. **认证状态复用** — 多个测试共享同一登录态时，第一个测试执行真实登录并保存状态，后续测试复用（Flutter: 共享 app 实例；Web: storageState）。不每个测试都重新登录（太慢）

---

