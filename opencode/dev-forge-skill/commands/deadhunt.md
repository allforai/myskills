---
description: "猎杀死链，验证产品完整性。支持模式: static / deep / full / incremental"
---

# DeadHunt — 猎杀死链，验证产品完整性

## 模式路由

根据用户参数决定执行模式：

- **无参数 或 `full`** → 完整验证：Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5
- **`static`** → 仅静态分析：Phase 0 → Phase 1 → Phase 4
- **`deep`** → 仅深度测试：Phase 0 → Phase 2 → Phase 3（Web 用 Playwright，Flutter 用 Patrol）→ Phase 4 → Phase 5
- **`incremental`** → 增量验证：检测 git 改动涉及的模块，只对这些模块做静态 + 深度测试 + 补测试

## 执行流程

1. 参考已加载的 SKILL.md 中的目标定义和注意事项（技能触发时已自动加载，无需重复读取）
2. **Phase 0 前置：尝试消费上游决策**（见下方"上游消费链"）
3. 根据模式按需读取对应阶段的详细文档
4. 按工作流执行
5. **【强制】执行完毕后，必须在对话中直接输出完整的报告摘要（见下方"报告输出要求"）**
6. **【强制】报告输出后，执行 Phase 5: 补充回归测试（见下方"回归测试要求"）**

### 上游消费链（Front-load Decisions）

Phase 0 的 3 个决策项可从上游产物自动获取，**已从上游获取的决策直接采用（展示一行摘要），仅缺失或冲突项才询问用户**：

```
优先级 1: .allforai/deadhunt/deadhunt-decisions.json（自身 resume 缓存）
    ↓ 不存在或过期
优先级 2: .allforai/project-forge/project-manifest.json（project-setup 产出）
    ↓ 不存在
优先级 3: 自动检测（扫描代码推断）
    ↓ 无法推断
优先级 4: 直接向用户提问
```

**字段映射表**：

| Phase 0 决策项 | project-manifest.json 字段 |
|---------------|--------------------------|
| module-classification | `sub_projects[].modules[]`（按子项目分组的模块列表） |
| crud-distribution | — （需自动扫描，但模块列表可缩小扫描范围） |
| client-roles | `sub_projects[].tech_stack`（前端子项目 = 客户端角色） |

**执行逻辑**：

1. 尝试读取 `deadhunt-decisions.json` → 已有决策的步骤自动跳过
2. 尝试读取 `project-manifest.json` → 存在则提取 `module-classification` 和 `client-roles`
3. 自动填充的项展示「✓ module-classification: 12 个模块 — 来自 project-manifest」
4. 仅 `crud-distribution`（必须扫描代码）和无法映射的项需要用户确认

## 外部能力快检

> 统一协议见 `product-design-skill/docs/skill-commons.md`「外部能力探测协议」。

Phase 3 深度测试依赖 Playwright（Web）或 Patrol（Flutter），Phase 0 检测可用性：

| 能力 | 探测方式 | 重要性 | 降级行为 |
|------|---------|--------|---------|
| Playwright | `mcp__playwright__browser_navigate` 可用性 | deep/full 必需 | static 模式可跳过；deep/full 阻塞，提示安装 |

**输出格式**：

```
外部能力:
  Playwright  ✓ 就绪   深度测试（Phase 3）
```

**交互式安装引导**（统一协议见 `product-design-skill/docs/skill-commons.md`）：

- **static 模式**：不需要 Playwright，不阻塞
- **deep/full 模式 + Playwright 未就绪**：向用户提问并提供安装选项（「是，帮我安装」/「跳过，仅跑静态分析」/「查看详情」）

---

## 详细文档（按需用 Read 工具加载）

- `docs/deadhunt/quick-start.md` — 快速开始
- `docs/deadhunt/workflow.md` — 工作流详解
- `docs/deadhunt/phase0-analyze.md` — Phase 0: 项目分析
- `docs/deadhunt/auth-strategy.md` — 登录认证策略
- `docs/deadhunt/phase1-static.md` — Phase 1: 静态分析
- `docs/deadhunt/phase2-plan.md` — Phase 2: 测试计划
- `docs/deadhunt/phase3-test.md` — Phase 3: 深度测试（索引文件，指向子文件）
- `docs/deadhunt/phase3/overview.md` — Phase 3: 性能优化与分级策略
- `docs/deadhunt/phase3/404-scanner.md` — Phase 3: 全局 404 监控 + Layer 1-5
- `docs/deadhunt/phase3/intent-classification.md` — Phase 3: 死链意图判定
- `docs/deadhunt/phase3/validation.md` — Phase 3: CRUD 闭环 + 数据展示 + 业务流程
- `docs/deadhunt/phase3/convergence.md` — Phase 3: 多轮收敛机制
- `docs/deadhunt/phase3/patrol.md` — Phase 3: Patrol 引擎（Flutter）
- `docs/deadhunt/phase4-report.md` — Phase 4: 报告生成
- `docs/deadhunt/phase5-supplement-test.md` — Phase 5: 补充测试
- `docs/deadhunt/faq.md` — FAQ

---

## 决策日志

每次用户确认决策时，追加记录到 `deadhunt-decisions.json`：

```json
{
  "decisions": [
    {
      "step": "Phase 0",
      "item_id": "module-classification",
      "decision": "confirmed",
      "value": "...",
      "decided_at": "ISO8601"
    }
  ]
}
```

**输出路径**：`.allforai/deadhunt/deadhunt-decisions.json`

**记录时机**：Phase 0 中的以下决策点：
- `module-classification` — 模块分类确认
- `crud-distribution` — CRUD 分布确认
- `client-roles` — 客户端角色确认

**resume 模式**：已有 decisions.json 时，已确认步骤自动跳过（展示一行摘要），从第一个无决策记录的步骤继续。

---

## 报告输出要求（强制执行）

验证完成后，你必须做两件事：

### 1. 保存报告文件

将完整报告写入 `.allforai/deadhunt/output/` 目录：
- `validation-report-{client}.md` — 各端详细报告
- `fix-tasks.json` — 修复任务清单
- `deadhunt-decisions.json` — 决策日志（位于 `.allforai/deadhunt/deadhunt-decisions.json`）

### 2. 在对话中直接输出报告摘要

**不要只说"报告已完成"或"报告已保存"。你必须在对话中直接展示以下内容：**

```
## 验证报告摘要

> 验证时间: {时间}
> 验证模式: {static/deep/full/incremental}
> 验证范围: {模块数} 个模块

### 总览
| 指标 | 数值 |
|------|------|
| 扫描模块数 | X |
| 发现问题总数 | X |
| 🔴 严重 (需立即修复) | X |
| 🟡 警告 (建议修复) | X |
| 🟢 通过 | X |
| ❓ 需人工确认 | X |

### 🔴 严重问题列表
(逐条列出每个严重问题：位置、问题描述、处置建议)

### 🟡 警告列表
(逐条列出)

### ❓ 需人工确认
(逐条列出，说明为什么无法自动判定)

### 🟢 通过的模块
(列出所有正常的模块)

### 下一步建议
1. 优先修复 🔴 严重问题
2. 对 ❓ 项逐个确认后告诉我
3. 修复后可以跑 `/deadhunt:deadhunt incremental` 做回归验证

> 完整报告已保存至: `.allforai/deadhunt/output/xxx`
```

**关键：摘要必须包含具体的问题列表和修复建议，不能只给统计数字。用户看完摘要就能知道出了什么问题、在哪里、怎么修。**

---

## Phase 5: 补充测试（强制执行）

> 详见 `docs/deadhunt/phase5-supplement-test.md`

报告输出后，必须读取上述文档并按流程补充测试用例。包含两部分：
1. **补全现有测试的覆盖盲区** — 项目已有测试但覆盖不到的模块/场景
2. **为新发现的问题添加回归测试** — 防止问题修复后再次出现

**测试文件命名：**
- `deadhunt-regression.{test|spec}.ts` — Web 端回归测试
- `deadhunt-coverage.{test|spec}.ts` — Web 端覆盖盲区测试
- `deadhunt-regression.patrol_test.dart` — Flutter 端回归测试（Patrol 格式）
- `deadhunt-coverage.patrol_test.dart` — Flutter 端覆盖盲区测试（Patrol 格式）
