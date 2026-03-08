---
description: "演示锻造全流程：design → media → execute → verify，多轮迭代至 95% 通过率。模式: full / design / media / execute / verify / clean"
argument-hint: "[mode: full|design|media|execute|verify|clean]"
allowed-tools: ["Read", "Write", "Grep", "Glob", "Bash", "Agent", "AskUserQuestion"]
---

# Demo Forge — 演示锻造全流程编排

用户请求: $ARGUMENTS

## 插件根目录

所有文档路径基于插件安装目录: `${CLAUDE_PLUGIN_ROOT}`

> **编排命令是导航员**。
> - Phase 1-4 通过 `${CLAUDE_PLUGIN_ROOT}/skills/` 路径加载技能，不直接实现具体逻辑。
> - 各阶段产物通过 `.allforai/demo-forge/` 目录作为层间合约。
> - 质量门禁不可跳过，不达标则阻塞。
> - 用户可在任意阶段中止，`resume` 模式可从断点续行。

### 阶段→技能速查表

| Phase | 技能文件 | 做什么 | 完成标志 |
|-------|---------|--------|---------|
| 1 | `skills/demo-design.md` | 数据方案设计 | `demo-plan.json` 存在且实体数 > 0 |
| 2 | `skills/media-forge.md` | 富媒体采集 + 加工 + 上传 | `upload-mapping.json` 存在且 `external_url_count=0` |
| 3 | `skills/demo-execute.md` | 数据生成 + 灌入 | `forge-data.json` 存在且记录数 > 0 |
| 4 | `skills/demo-verify.md` | Playwright 验证 | `verify-report.json` 存在 |

---

## 模式路由

根据用户参数决定执行模式：

- **无参数 或 `full`** → 全流程，Design → Media → Execute → Verify，自动多轮迭代
- **`design`** → 仅 Phase 1（数据方案设计）
- **`media`** → 仅 Phase 2（富媒体管线）
- **`execute`** → 仅 Phase 3（数据生成 + 灌入）
- **`verify`** → 仅 Phase 4（验证）
- **`clean`** → 加载 `demo-execute.md` clean 模式，清理已灌入数据
- **`resume`** → 检测已有产物，从第一个未完成阶段继续

---

## Phase 0：产物检测 + 初始化

### 0-A 上游检查

product-map 产物必须存在：
```
.allforai/product-map/task-inventory.json  # 必须
.allforai/product-map/role-profiles.json   # 必须
```
缺失 → 中止，提示先运行 `/product-map`。

### 0-B 产物扫描

扫描 `.allforai/demo-forge/` 下已有产物，确定各阶段完成状态：

| 产物文件 | 对应阶段 | 存在 = 完成 |
|---------|---------|------------|
| `demo-plan.json` | Phase 1 Design | 文件存在且 entities 数组非空 |
| `assets-manifest.json` + `upload-mapping.json` | Phase 2 Media | 两文件存在且 `external_url_count=0` |
| `forge-data.json` | Phase 3 Execute | 文件存在且 records 数组非空 |
| `verify-report.json` | Phase 4 Verify | 文件存在 |

### 0-C 续行判断

如果 `round-history.json` 存在：
- 读取最后一轮的 `final_status`
- 若为 `in_progress` → 提示用户：「检测到未完成的迭代（Round N），是否继续？」
- 用户确认 → resume 模式，从最后未完成阶段继续
- 用户拒绝 → 询问是否从头开始（会清空历史）

### 0-D 外部能力快检

> 统一协议见 `product-design-skill/docs/skill-commons.md`「外部能力探测协议」。

检测本流水线涉及的外部能力并输出状态：

| 能力 | 探测方式 | 重要性 | 降级行为 |
|------|---------|--------|---------|
| Playwright | `mcp__plugin_playwright_playwright__browser_navigate` 可用性 | Phase 4 必需 | 阻塞 verify，提示安装 |
| Brave Search | `brave_web_search` 可用性 或 `BRAVE_API_KEY` | Phase 2 推荐 | 降级到 WebSearch |
| AI 生图 | `generate_image` / `openrouter_generate_image` / `flux_generate_image` 任一可用 | Phase 2 可选 | Imagen 4 → GPT-5 Image → FLUX 2 Pro → 跳过 |
| AI 生视频 | `generate_video` / `kling_generate_video` 任一可用 | Phase 2 可选 | Veo 3.1 → Kling → 跳过 |

**输出格式**：

```
外部能力:
  Playwright     ✓ 就绪     验证（Phase 4 必需）
  Brave Search   ✗ 未就绪   媒体搜索（降级到 WebSearch）
  AI 生图        ✗ 未就绪   Imagen 4 / GPT-5 Image / FLUX 2 Pro（降级到搜索补缺）
  AI 生视频      ✗ 未就绪   Veo 3.1 / Kling（降级到 Playwright 录屏）
```

**交互式安装引导**（统一协议见 `product-design-skill/docs/skill-commons.md`）：

- **Playwright 未就绪 + full/verify 模式**：用 AskUserQuestion 提供一键安装选项（「是，帮我安装」/「跳过」/「查看详情」）
- **Playwright 未就绪 + design/media/execute 模式**：仅输出一行提示，不阻塞
- **Brave/Google AI 未就绪**：提示运行 `/setup` 配置（Key 存储在插件 `.mcp.json`，不污染 shell 环境变量）

### 0-E 初始化

- 确保 `.allforai/demo-forge/` 目录存在
- 初始化或更新 `round-history.json`（若不存在则创建空结构）

### 0-E 运行信息收集

对于 `execute` / `verify` / `full` 模式，需要收集：
- **应用 URL**：`AskUserQuestion` 询问应用访问地址（如 `http://localhost:3000`）
- **登录凭据**：如果 `demo-plan.json` 中有角色账号定义则复用，否则询问

将收集到的信息写入 `round-history.json` 的 `runtime_config`。

---

## Phase 1：Design（数据方案设计）

> 加载技能: `${CLAUDE_PLUGIN_ROOT}/skills/demo-design.md`

### 执行

加载 demo-design skill 并执行完整工作流（Step 0 → Step 2.5）。

### 质量门禁

- `demo-plan.json` 存在
- `demo-plan.json` 中 entities 数组长度 > 0
- 每个 entity 有 `records_count > 0`

**PASS** → 进入 Phase 2
**FAIL** → 中止，报告缺失项

---

## Phase 2：Media（富媒体采集 + 加工 + 上传）

> 加载技能: `${CLAUDE_PLUGIN_ROOT}/skills/media-forge.md`

### 前置检查

- `demo-plan.json` 必须存在（Phase 1 已完成）
- `demo-plan.json` 中有媒体字段标注（Step 1-M 产物）

若无媒体字段 → 跳过 Phase 2，直接进入 Phase 3。

### 执行

加载 media-forge skill 并执行完整管线（M1 → M6）。

### 质量门禁

- `assets-manifest.json` 存在
- `upload-mapping.json` 存在
- `upload-mapping.json` 中 `validation.external_url_count === 0`（硬校验）
- `upload-mapping.json` 中无 `UPLOAD_FAILED` 状态

**PASS** → 进入 Phase 3
**FAIL** → 中止，报告未满足条件

---

## Phase 3：Execute（数据生成 + 灌入）

> 加载技能: `${CLAUDE_PLUGIN_ROOT}/skills/demo-execute.md`

### 前置检查

- `demo-plan.json` 必须存在
- 若有媒体字段：`upload-mapping.json` 必须存在
- 应用 URL 必须已收集（Phase 0-E）

### 执行

加载 demo-execute skill 并执行完整工作流（E1 → E4）。

### 质量门禁

- `forge-data.json` 存在
- `forge-data.json` 中记录数 > 0
- `forge-log.json` 中无 `CHAIN_FAILED` 状态（链路级失败）

**PASS** → 进入 Phase 4
**FAIL** → 中止，报告灌入失败项

---

## Phase 4：Verify（验证）

> 加载技能: `${CLAUDE_PLUGIN_ROOT}/skills/demo-verify.md`

### 前置检查

- `forge-data.json` 必须存在
- 应用 URL 必须可访问

### 执行

加载 demo-verify skill 并执行完整验证（V1 → V7）。

### 质量门禁

- `verify-report.json` 存在
- 计算通过率时排除 `DEFERRED_TO_DEV` 项
- `pass_rate >= 95%`（不含 DEFERRED_TO_DEV）

**PASS** → 进入 Phase 5（最终报告）
**FAIL** → 进入 Phase 4.5（迭代修复）

---

## Phase 4.5：迭代修复

当 verify 未达 95% 通过率时，进入修复迭代。最多 3 轮自动迭代（Round 0 首轮 + Round 1-2 修复轮）。

### 4.5-A 读取问题清单

读取 `verify-issues.json`，按 `route_to` 字段分组：

| route_to | 处理方式 |
|----------|---------|
| `design` | 重入 `demo-design.md`（增量模式，仅修改 demo-plan 对应部分） |
| `media` | 重入 `media-forge.md`（增量模式，补采/再加工/重传问题项） |
| `execute` | 重入 `demo-execute.md`（增量模式，补灌缺失/修正派生） |
| `dev_task` | 生成修复任务写入 `.allforai/project-forge/sub-projects/{name}/tasks.md`，标记 `DEFERRED_TO_DEV` |
| `skip` | 记录但不处理，属于应用开发范畴 |

### 4.5-B 按路由执行修复

按顺序处理各组问题：

1. **design 类** → 加载 `${CLAUDE_PLUGIN_ROOT}/skills/demo-design.md`，传入问题项，增量修改 `demo-plan.json`
2. **media 类** → 加载 `${CLAUDE_PLUGIN_ROOT}/skills/media-forge.md`，传入问题项，补采/再加工/重传
3. **execute 类** → 加载 `${CLAUDE_PLUGIN_ROOT}/skills/demo-execute.md`，传入问题项，补灌/修正
4. **dev_task 类** → 生成结构化任务（格式与 dev-forge tasks.md 一致），追加到对应子项目 tasks.md 的 B-FIX round。demo-forge 当轮标记为 `DEFERRED_TO_DEV`，不阻塞自身迭代

### 4.5-C 回归验证

修复完成后，重新运行 verify：
- 加载 `${CLAUDE_PLUGIN_ROOT}/skills/demo-verify.md`
- 验证范围：修复项 + 回归（已通过项抽检）
- `dev_task` 项跳过（已 DEFERRED_TO_DEV）

### 4.5-D 迭代控制

- 检查通过率（不含 DEFERRED_TO_DEV）
- `pass_rate >= 95%` → 跳出迭代，进入 Phase 5
- `pass_rate < 95%` 且当前轮次 < 3 → 回到 4.5-A 继续下一轮
- 当前轮次 >= 3 → 输出剩余问题为已知问题（known issues），进入 Phase 5

### 4.5-E 更新迭代历史

每轮结束后更新 `round-history.json`：
- 记录本轮执行的阶段
- 记录本轮处理的问题 ID 列表
- 记录本轮 verify 结果

---

## Phase 5：最终报告

### 5-A 汇总表

输出以下汇总信息：

```
=== Demo Forge 完成报告 ===

迭代轮次：{total_rounds} 轮
通过率变化：Round 0 ({rate_0}%) → Round 1 ({rate_1}%) → ... → Round N ({rate_n}%)
最终通过率：{final_rate}%（不含 DEFERRED_TO_DEV）
DEFERRED_TO_DEV 任务：{dev_task_count} 项
已知问题（未修复）：{known_issue_count} 项
```

### 5-B 演示登录凭据表

从 `demo-plan.json` 提取角色账号，输出凭据表：

```
| 角色 | 用户名 | 密码 | 入口 URL |
|------|--------|------|---------|
| 管理员 | admin@demo.com | demo123 | {app_url}/admin |
| 普通用户 | user1@demo.com | demo123 | {app_url}/ |
| ... | ... | ... | ... |
```

### 5-C 更新 round-history.json

写入最终状态：

```json
{
  "final_status": "passed | passed_with_known_issues | max_rounds_reached",
  "total_rounds": 2,
  "dev_tasks_generated": 3,
  "known_issues": []
}
```

---

## round-history.json 完整结构

```json
{
  "runtime_config": {
    "app_url": "http://localhost:3000",
    "collected_at": "ISO8601"
  },
  "rounds": [
    {
      "round": 0,
      "started_at": "ISO8601",
      "phases_executed": ["design", "media", "execute", "verify"],
      "verify_result": {
        "total_checks": 86,
        "passed": 71,
        "failed": 15,
        "deferred_to_dev": 2,
        "pass_rate": "82.6%"
      }
    },
    {
      "round": 1,
      "started_at": "ISO8601",
      "phases_executed": ["design", "media", "execute", "verify"],
      "issues_addressed": ["VI-001", "VI-002", "VI-003"],
      "verify_result": {
        "total_checks": 86,
        "passed": 82,
        "failed": 2,
        "deferred_to_dev": 2,
        "pass_rate": "97.6%"
      }
    }
  ],
  "final_status": "passed",
  "total_rounds": 2,
  "dev_tasks_generated": 2,
  "known_issues": []
}
```

---

## 铁律

1. **质量门禁不跳过** — 每个 Phase 的完成标志必须满足才能进入下一阶段
2. **编排命令是导航员** — 加载 skill 文件，不直接实现具体逻辑
3. **`.allforai/` 是层间合约** — 所有产物读写通过 `.allforai/demo-forge/` 目录
4. **用户可在任意阶段中止** — `resume` 模式可从断点续行
5. **`dev_task` 不阻塞自身迭代** — 代码问题路由到 dev-forge，demo-forge 继续自身迭代闭环
