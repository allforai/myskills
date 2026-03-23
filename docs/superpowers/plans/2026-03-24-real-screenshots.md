# Real Screenshots Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace faked Phase 2.13 screenshots with real business-flow-driven captures using a three-tier strategy (user interaction → ViewModel call → network mock).

**Architecture:** Redesign `interaction-recordings.json` from independent operations to business flow chains with role-aware steps. Add iron law 27 prohibiting DOM manipulation. Update execution protocol with three-tier strategy and failure handling.

**Tech Stack:** Markdown skill files (Chinese), JSON schema examples

**Spec:** `docs/superpowers/specs/2026-03-24-real-screenshots-design.md`

---

### Task 1: Rewrite 2.12.8 in stage-c-resources.md

**Files:**
- Modify: `code-replicate-skill/docs/phase2/stage-c-resources.md` (section 2.12.8, lines 73-135)

- [ ] **Step 1: Read the current 2.12.8 section**

Already read. The section runs from line 73 (`## 2.12.8 交互行为清单`) to line 135 (end of parallel execution guidance, before `## 2.13`).

- [ ] **Step 2: Replace the entire 2.12.8 section**

Replace lines 73-136 (from `## 2.12.8` up to but not including `## 2.13`) with:

```markdown
## 2.12.8 业务流程链 → `interaction-recordings.json`（仅 frontend/fullstack）

LLM 读源码中的**所有用户交互行为**，按**业务流程**组织为端到端的流程链，而非独立操作。

**核心原则：每张截图必须是真实业务操作的自然结果，不允许伪造 UI 状态。**

```json
{
  "generated_at": "ISO8601",
  "flows": [
    {
      "name": "order_lifecycle",
      "description": "订单从创建到审批的完整生命周期",
      "steps": [
        {"role": "R001", "action": "login"},
        {"role": "R001", "action": "navigate", "target": "/orders/new"},
        {"role": "R001", "action": "fill", "target": "订单表单", "data": {"name": "测试订单", "amount": 1000}},
        {"role": "R001", "action": "click", "target": "提交按钮"},
        {"role": "R001", "action": "wait", "condition": "成功提示出现"},
        {"role": "R001", "action": "screenshot", "name": "order_created", "expected_result": {
          "screenshot_after": "订单创建成功，状态为待审批",
          "ui_changes": ["订单列表新增一条记录", "成功提示出现"],
          "feedback": "创建成功"
        }},

        {"role": "R002", "action": "login"},
        {"role": "R002", "action": "navigate", "target": "/orders"},
        {"role": "R002", "action": "click", "target": "刚创建的订单"},
        {"role": "R002", "action": "click", "target": "审批按钮"},
        {"role": "R002", "action": "wait", "condition": "审批成功提示"},
        {"role": "R002", "action": "screenshot", "name": "order_approved", "expected_result": {
          "screenshot_after": "订单状态变为已审批",
          "ui_changes": ["状态标签从'待审批'变为'已审批'", "审批按钮消失"],
          "feedback": "审批成功"
        }}
      ],
      "source_files": ["src/handlers/order_handler.go", "src/services/order_service.go"]
    }
  ],
  "unreachable": [
    {
      "state": "并发编辑冲突",
      "reason": "需要两个用户同时编辑同一订单并同时提交，无法可靠模拟精确并发时序",
      "source_file": "src/services/order_service.go:handleConflict"
    }
  ]
}
```

**流程链 vs 独立操作**：每个 flow 是完整的业务场景，步骤串联 — 前一步的结果是后一步的前置条件。screenshot 是流程中的里程碑，不是独立采集动作。

**角色感知**：每个 step 带 `role` 字段。角色切换时自动清除 session → 重新登录（凭证来自 `role-view-matrix.json`）。

**Step action 类型**：

| Action | 字段 | 说明 |
|--------|------|------|
| `login` | role | 用该角色凭证登录 |
| `navigate` | target（URL/路由） | 导航到页面 |
| `click` | target（自然语言描述，执行时 LLM 解析为 Playwright selector） | 点击 UI 元素 |
| `fill` | target, data | 填写表单 |
| `type` | target, value | 逐键输入 |
| `select` | target, value | 选择下拉选项 |
| `drag` | source, target | 拖拽 |
| `hover` | target | 悬浮 |
| `wait` | condition | 等待条件（元素可见、文本出现、导航完成） |
| `screenshot` | name, expected_result | 在此里程碑截图 |
| `vm_call` | method（JS 表达式）, args（可选）, wait_after（可选条件） | 调用 ViewModel/Store 方法（Tier 2 fallback） |
| `mock_route` | url（method + path）, response（status, body） | Mock API 响应（Tier 3） |
| `clear_mock` | （无） | 清除所有 route mock |

**`expected_result` 保留结构化格式**：`screenshot_after`、`ui_changes`、`navigation`、`feedback`、`sound` — 与 cr-visual 和 Phase 3 音效迁移兼容。

**`source_files` 追溯**：每个 flow 关联源码文件，保留 Phase 3 迁移可追溯性。

**flow `type` 字段**：可选，默认 `functional_action`。设为 `visual_effect` 时触发录像而非截图。

**`unreachable` 数组**：三个层级都无法到达的状态。记录原因和源码位置 — 替代伪造。

**LLM 生成指导 — 穷举提取**：

**原则：源码中每一个会引起 UI 变化的事件处理函数 = 至少一张截图。不手工挑选，穷举。**

LLM 读每个页面/组件的源码 → 找出所有绑定了事件处理的 UI 元素 → 按业务实体的生命周期组织为流程链（create → read → update → delete）。

- 跨角色审批/审核/权限操作 → 在同一 flow 中切换角色
- 服务端错误 → `mock_route`（Tier 3）。客户端校验错误 → 直接用 Tier 1 提交不完整表单
- 后台任务完成、外部回调等 UI 交互无法到达的状态 → `vm_call`（Tier 2）
- 真正不可达 → 放入 `unreachable` 数组

**删除安全**：CRUD 流程中用刚创建的测试数据做 Delete（自产自销）。无法安全删除 → 只截确认弹窗，标记 `DELETE_SKIPPED_SAFETY`。

**流程独立 + 并行优化**：流程间无数据依赖（每个 flow 创建自己的测试数据）。大项目（100+ 截图）不同模块的 flow 可用 Agent 并行执行。同一 flow 内步骤始终串行。
```

- [ ] **Step 3: Verify the edit**

Run: `grep -n "flows\|vm_call\|mock_route\|unreachable\|穷举" code-replicate-skill/docs/phase2/stage-c-resources.md`
Expected: Multiple matches in the new 2.12.8 section.

- [ ] **Step 4: Commit**

```bash
git add code-replicate-skill/docs/phase2/stage-c-resources.md
git commit -m "docs(code-replicate): redesign 2.12.8 from independent operations to business flow chains"
```

---

### Task 2: Update 2.13 execution in stage-c-resources.md

**Files:**
- Modify: `code-replicate-skill/docs/phase2/stage-c-resources.md` (section 2.13, the "交互行为采集" subsection and execution pseudocode)

- [ ] **Step 1: Replace the interaction execution subsection**

Find the `### 交互行为采集` subsection in 2.13 (starts with `如果 interaction-recordings.json 存在 → 按清单逐项执行并采集`). Replace the execution pseudocode block (the block between ` ``` ` markers that starts with `对每个 recording:`) with the three-tier execution protocol:

```markdown
### 交互行为采集

如果 `interaction-recordings.json` 存在 → 按流程链逐步执行并采集：

**铁律（iron law 27）：禁止用 `page.evaluate()` 修改 DOM 或 View 控件状态。`page.evaluate()` 仅允许用于：(1) `vm_call` 调用 ViewModel/Store/Bloc 方法，(2) 读取状态用于断言。违反 = 伪造截图 = 无价值。**

**三级执行策略**：

| 优先级 | 策略 | 适用场景 | Playwright API |
|--------|------|---------|----------------|
| Tier 1 | 用户交互 | 正向业务流程 | page.click / page.fill / page.type 等 |
| Tier 2 | ViewModel 调用 | UI 交互无法到达的状态 | page.evaluate() 调用 Store/Bloc 方法 |
| Tier 3 | 网络 Mock | 异常/错误状态 | page.route() 拦截 + Mock 响应 |

**Tier 选择规则**：
```
用户交互能到达？→ YES → Tier 1（包括客户端校验错误 — 提交不完整表单即可）
  → NO → ViewModel 调用能到达？→ YES → Tier 2（vm_call）
    → NO → 是网络/错误状态？→ YES → Tier 3（mock_route）
      → NO → 标记 UNREACHABLE
```

**Tier 2 说明**：LLM 必须从 Phase 2 源码分析中确定具体的调用表达式，不依赖已知框架模式。源 App 须在开发模式运行（生产构建可能移除调试入口）。`vm_call` 后须等待 UI 更新完成再截图。

**执行流程**：
```
对每个 flow:
  current_role = null
  for each step in flow.steps:
    if step.role != current_role:
      清除 cookies + localStorage
      导航到登录页
      用 step.role 凭证登录（来自 role-view-matrix）
      current_role = step.role

    执行 step.action:
      login      → 清除 session + 登录
      navigate   → page.goto(target)
      click      → page.click(resolved_selector)  [Tier 1]
      fill       → page.fill(resolved_selector, data)  [Tier 1]
      type       → page.type(resolved_selector, value)  [Tier 1]
      select     → page.selectOption(resolved_selector, value)  [Tier 1]
      drag       → page.dragAndDrop(resolved_source, resolved_target)  [Tier 1]
      hover      → page.hover(resolved_selector)  [Tier 1]
      wait       → page.waitForSelector / waitForURL / 自定义条件
      screenshot → page.screenshot() → 保存到 visual/source/interactions/
      vm_call    → page.evaluate(() => expr(args)) + wait_after  [Tier 2]
      mock_route → page.route(url, handler)  [Tier 3]
      clear_mock → page.unroute('**')  [Tier 3]

    step 失败时:
      重试 1 次
      仍失败:
        记录失败原因
        非 screenshot 步骤 → 跳到下一个 screenshot 里程碑
        screenshot 步骤 → 标记失败，继续
      绝对不伪造状态

  flow 失败（登录失败/环境不可用）→ 中止该 flow，记录原因，继续下一个 flow
  3+ flow 因同一环境问题失败 → 中止所有剩余 flow
```
```

- [ ] **Step 2: Verify the edit**

Run: `grep -n "iron law 27\|Tier 1\|Tier 2\|Tier 3\|vm_call\|mock_route\|伪造" code-replicate-skill/docs/phase2/stage-c-resources.md`
Expected: Multiple matches in the 2.13 section.

- [ ] **Step 3: Commit**

```bash
git add code-replicate-skill/docs/phase2/stage-c-resources.md
git commit -m "docs(code-replicate): add three-tier execution strategy and iron law 27 to Phase 2.13"
```

---

### Task 3: Update code-replicate-core.md

**Files:**
- Modify: `code-replicate-skill/skills/code-replicate-core.md`

- [ ] **Step 1: Update Stage C table row for 2.12.8**

Find the Stage C table (around line 83-91). Change the 2.12.8 row from:

```
| 2.12.8 | interaction-recordings.json | 动态效果录制清单 |
```

To:

```
| 2.12.8 | interaction-recordings.json | 业务流程链（端到端交互 + 多角色 + 异常状态） |
```

- [ ] **Step 2: Add iron law 27**

Find iron law 26 (line ~281). After it, add:

```
27. **禁止伪造截图** — Phase 2.13 截图必须来自真实业务操作。禁止用 `page.evaluate()` 修改 DOM/View 控件状态。`page.evaluate()` 仅允许调用 ViewModel/Store 方法（Tier 2）或读取状态。三级策略：用户交互（Tier 1）→ ViewModel 调用（Tier 2）→ 网络 Mock（Tier 3）→ 不可达则标记 UNREACHABLE
```

- [ ] **Step 3: Verify**

Run: `grep -n "27\.\|业务流程链\|禁止伪造" code-replicate-skill/skills/code-replicate-core.md`
Expected: Matches for all three additions.

- [ ] **Step 4: Commit**

```bash
git add code-replicate-skill/skills/code-replicate-core.md
git commit -m "docs(code-replicate): update Stage C table for 2.12.8 and add iron law 27"
```

---

### Task 4: Update cr-visual.md references

**Files:**
- Modify: `code-replicate-skill/skills/cr-visual.md`

- [ ] **Step 1: Update interaction comparison section**

Find line 27 (`**交互行为对比**：如果 interaction-recordings.json 存在 → 源 App 的证据已在 Phase 2.13 采集。cr-visual 对目标 App 执行**同样的操作步骤**：`).

Replace lines 27-45 (the interaction comparison block through `每个交互输出 match_level: high / medium / low / mismatch`) with:

```markdown
**交互行为对比**：如果 `interaction-recordings.json` 存在 → 源 App 的证据已在 Phase 2.13 采集。cr-visual 对目标 App 执行**同样的业务流程链**：

逐 flow 执行（按 interaction-recordings.json 的 flows 结构）：
1. 按 flow.steps 在目标 App 上执行同样的操作序列（角色切换、填表、点击、等待）
2. 在每个 screenshot 里程碑截图 → 与源 App 的对应截图对比
3. 同时采集目标 App 的 API 日志 → 与源 App 的 api.json 对比

五层验证：
1. **静态页面**：源截图 vs 目标截图 → 布局/组件/数据展示一致吗？
2. **CRUD 全状态**：flow 链自然覆盖 CRUD 生命周期 → 逐里程碑截图对比
3. **动态效果**（type=visual_effect 的 flow）：源录像 vs 目标录像 → 动画/过渡一致吗？
4. **API 日志**：源 api.json vs 目标 api.json → 同样的操作触发了同样的请求吗？
5. **综合**：同一 flow → 每个里程碑截图 + API 都一致 = high

每个交互输出 match_level: high / medium / low / mismatch
```

- [ ] **Step 2: Fix line 278 contradiction**

Find line 278 (`- 不覆盖交互行为（只能看静态截图，不能验证点击/滑动）`).

Replace with:

```markdown
- 交互行为对比依赖 `interaction-recordings.json` 的 flows 结构 — 无此文件时仅做静态截图对比
```

- [ ] **Step 3: Verify**

Run: `grep -n "flows\|flow 链\|业务流程链\|里程碑" code-replicate-skill/skills/cr-visual.md`
Expected: Multiple matches confirming updated references.

- [ ] **Step 4: Commit**

```bash
git add code-replicate-skill/skills/cr-visual.md
git commit -m "docs(code-replicate): update cr-visual to use flows[] structure from interaction-recordings"
```

---

### Task 5: Cross-reference verification

**Files:**
- Read: all 3 modified files

- [ ] **Step 1: Verify consistency**

```bash
grep -n "flows\|flow" code-replicate-skill/docs/phase2/stage-c-resources.md code-replicate-skill/skills/cr-visual.md | head -20
grep -n "iron law 27\|禁止伪造\|Tier" code-replicate-skill/skills/code-replicate-core.md code-replicate-skill/docs/phase2/stage-c-resources.md
grep -n "interaction-recordings" code-replicate-skill/skills/code-replicate-core.md code-replicate-skill/skills/cr-visual.md code-replicate-skill/docs/phase2/stage-c-resources.md
```

Verify:
1. stage-c-resources.md 2.12.8 uses `flows[]` structure
2. stage-c-resources.md 2.13 has three-tier execution + iron law 27
3. code-replicate-core.md Stage C table says "业务流程链" for 2.12.8
4. code-replicate-core.md has iron law 27
5. cr-visual.md references `flows[]` not `recordings[]`
6. cr-visual.md line 278 no longer contradicts

- [ ] **Step 2: Run existing tests**

```bash
cd code-replicate-skill/scripts && python3 -m unittest discover -q
```

Expected: All existing tests pass (no Python scripts were modified).
