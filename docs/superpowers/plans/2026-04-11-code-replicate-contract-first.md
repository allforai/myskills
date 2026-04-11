# Code-Replicate Contract-First Replication Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Phase 1.2 (runability gate), Phase 2.5 (contract extraction), and Phase 3 reverse-check + three-tier closed loop to the code-replicate skill in both codex/ and opencode/.

**Architecture:** Three additions to the existing 4-phase pipeline. Phase 1.2 inserts a runability assessment + fidelity ceiling declaration before any analysis begins. Phase 2.5 inserts a contract extraction pass after discovery, producing `acceptance-contracts.json` as the oracle. Phase 3 is enhanced to use reverse contract extraction (extract contracts from generated code, diff against oracle) instead of subjective self-checks, with a three-tier feedback loop.

**Tech Stack:** Markdown skill files. No code compilation. All verification is "read the file and confirm the content is present and consistent."

---

## File Map

| Action | File | Responsibility |
|--------|------|---------------|
| Modify | `codex/code-replicate-skill/execution-playbook.md` | Phase overview table + Phase 1.2 section + Phase 2.5 section + Phase 3 update + Phase 4 update |
| Modify | `opencode/code-replicate-skill/execution-playbook.md` | English mirror of above |
| Modify | `codex/code-replicate-skill/skills/code-replicate-core.md` | Phase 1.2 protocol + Phase 2.5 reference + Phase 3 reverse-check + three-tier loop + new iron rules |
| Modify | `opencode/code-replicate-skill/skills/code-replicate-core.md` | English mirror of above |
| Create | `codex/code-replicate-skill/docs/phase2/stage-e-contracts.md` | Full Phase 2.5 contract extraction protocol (Chinese) |
| Create | `opencode/code-replicate-skill/docs/phase2/stage-e-contracts.md` | Full Phase 2.5 contract extraction protocol (English) |
| Modify | `codex/code-replicate-skill/docs/phase4/verify-handoff.md` | Add Step 4g: gap pattern analysis (large loop) |
| Modify | `opencode/code-replicate-skill/docs/phase4/verify-handoff.md` | English mirror of above |

---

## Task 1: Update phase overview table in both execution-playbooks

**Files:**
- Modify: `codex/code-replicate-skill/execution-playbook.md`
- Modify: `opencode/code-replicate-skill/execution-playbook.md`

- [ ] **Step 1: Replace the phase overview table in codex/execution-playbook.md**

Find and replace the Phase Overview table:

Old:
```markdown
| Phase | Goal | Key Outputs | Completion Signal |
|-------|------|-------------|-------------------|
| 1 | Preflight | `replicate-config.json`, fragments dirs | Config written, source accessible |
| 2 | Discovery + Confirm | `source-summary.json`, `infrastructure-profile.json`, `stack-mapping.json`, visual captures | User confirmation (last interaction) |
| 3 | Generate | Standard `.allforai/` artifacts (role-profiles, task-inventory, business-flows, etc.) | All extraction-plan artifacts merged |
| 4 | Verify & Handoff | `replicate-report.md`, validated artifacts | Schema valid, 6V audit complete |
```

New:
```markdown
| Phase | Goal | Key Outputs | Completion Signal |
|-------|------|-------------|-------------------|
| 1 | Preflight | `replicate-config.json`, `acceptance-ceiling.json`, fragments dirs | Config written, **user confirmed fidelity ceiling** |
| 2 | Discovery + Confirm | `source-summary.json`, `infrastructure-profile.json`, `stack-mapping.json`, visual captures | User confirmation (last interaction) |
| 2.5 | Contract Extraction | `acceptance-contracts.json` | All backend + UI contracts extracted |
| 3 | Generate + Reverse-Check | Standard `.allforai/` artifacts, `known_gaps.json` | All units pass diff or marked as known_gap |
| 4 | Verify & Handoff | `replicate-report.md`, validated artifacts, gap pattern analysis | Schema valid, 6V audit + gap report complete |
```

- [ ] **Step 2: Add Phase 1.2 section to codex/execution-playbook.md**

After the existing Phase 1 list (after step 6 "Create fragment directory structure"), insert:

```markdown
### Step 1.2: Runability Assessment (Gate)

Evaluate whether source and target environments can run. Output `acceptance-ceiling.json` and present findings to user before proceeding.

**Detection steps:**
1. Attempt source build: run `build_command` from replicate-config if present, else try `npm run build` / `go build ./...` / `flutter build` / `python -m py_compile`
2. Check source start: verify `start_command` or detect one from package.json/Makefile
3. Check target env: verify target language runtime, framework CLI, and database availability
4. Compute fidelity ceiling from table below

**Fidelity ceiling:**

| Condition | UI Verification Capability | Fidelity Ceiling |
|-----------|---------------------------|-----------------|
| Source + target both runnable, screenshots available | Full runtime verification | ~100% |
| Runnable, no screenshot environment | Structural verification only | ~70% |
| Source or target cannot run | Static contract diff only | ~40% |

**Gate rule:** Write `acceptance-ceiling.json` to `.allforai/code-replicate/`. Present ceiling and `known_gaps` list to user. **Wait for explicit user confirmation before proceeding to Phase 2.** If user declines, stop.

```json
{
  "source_runnable": true,
  "source_build_cmd": "npm run build",
  "target_env_ready": false,
  "target_missing": ["Node.js 18+", "PostgreSQL"],
  "screenshot_available": false,
  "fidelity_ceiling": 0.7,
  "known_gaps": ["runtime UI verification", "visual diff against running target"],
  "user_confirmed": false,
  "confirmed_at": null
}
```
```

- [ ] **Step 3: Add Phase 2.5 section to codex/execution-playbook.md**

After the Phase 2 section and before Phase 3, insert:

```markdown
## Phase 2.5: Contract Extraction

**Reference:** `./docs/phase2/stage-e-contracts.md`

Runs after Stage D confirm. Extracts acceptance contracts from source code — the oracle used by Phase 3 reverse-check.

| Step | Output | Action |
|------|--------|--------|
| 2.5.1 | backend_contracts[] | Extract per-endpoint: inputs, outputs, error conditions, side effects, cross-module rules |
| 2.5.2 | ui_contracts[] | Extract per-screen: states, user_actions (with preconditions), transitions, intent |
| 2.5.3 | acceptance-contracts.json | Merge all contracts, write to `.allforai/code-replicate/` |

**Extraction principle:** Extract INTENT, not implementation. Cross-module rules that appear scattered across files must be consolidated here — if a rule requires three files to state completely, the contract states it once.

Output: `.allforai/code-replicate/acceptance-contracts.json`
```

- [ ] **Step 4: Update Phase 3 description in codex/execution-playbook.md**

Find the Phase 3 section heading and replace its subtitle and Artifact Generation description:

Old:
```markdown
## Phase 3: Generate (Silent)
```

New:
```markdown
## Phase 3: Generate + Reverse-Check (Silent)
```

Find and replace the Artifact Generation block:

Old:
```markdown
### Artifact Generation

For each artifact in extraction-plan.artifacts:
1. LLM reads specified source files per module
2. Generates JSON fragment per module
3. **UI closure check**: cross-reference Phase 2.13 screenshots/API logs
4. **4D self-check**: conclusion / evidence / constraints / decisions
5. Merge via script (standard artifacts) or LLM direct output (custom artifacts)
```

New:
```markdown
### Artifact Generation

For each artifact in extraction-plan.artifacts:
1. Load acceptance contracts for this module from `acceptance-contracts.json`
2. LLM reads specified source files per module
3. Generates JSON fragment per module
4. **UI closure check**: cross-reference Phase 2.13 screenshots/API logs
5. **4D self-check**: conclusion / evidence / constraints / decisions
6. **Reverse contract extraction**: extract contracts B from generated fragment
7. **Diff(A, B)**: compare extracted contracts B against source contracts A
   - Empty diff → pass, proceed to merge
   - Non-empty diff → fix → re-extract → max 3 rounds → mark as `known_gap` with full diff
8. Merge via script (standard artifacts) or LLM direct output (custom artifacts)

Three-tier loop:
- **Small** (unit): fix within current generation unit, max 3 rounds
- **Medium** (contract): if 3 rounds fail, back to Phase 2.5 to re-examine source contract
- **Large** (methodology): Phase 4 aggregates all known_gap patterns → improve extraction strategy
```

- [ ] **Step 5: Mirror all changes to opencode/execution-playbook.md**

Apply identical changes (translated to English — opencode uses English throughout). The content structure is identical; only language differs.

- [ ] **Step 6: Verify both files**

Read `codex/code-replicate-skill/execution-playbook.md` and confirm:
- Phase overview table has 5 rows including Phase 2.5
- Step 1.2 section exists with fidelity ceiling table and gate rule
- Phase 2.5 section exists with steps 2.5.1–2.5.3
- Phase 3 heading says "Generate + Reverse-Check"
- Artifact Generation list has 8 steps including reverse contract extraction and diff

Read `opencode/code-replicate-skill/execution-playbook.md` and confirm same structure in English.

- [ ] **Step 7: Commit**

```bash
git add codex/code-replicate-skill/execution-playbook.md opencode/code-replicate-skill/execution-playbook.md
git commit -m "feat(code-replicate): add Phase 1.2 gate and Phase 2.5 to execution playbook"
```

---

## Task 2: Create stage-e-contracts.md (Phase 2.5 protocol doc)

**Files:**
- Create: `codex/code-replicate-skill/docs/phase2/stage-e-contracts.md`
- Create: `opencode/code-replicate-skill/docs/phase2/stage-e-contracts.md`

- [ ] **Step 1: Create codex/dev-forge-skill/docs/phase2/stage-e-contracts.md**

Create file at `codex/code-replicate-skill/docs/phase2/stage-e-contracts.md` with this exact content:

```markdown
# Phase 2.5: 合约提取协议

> Phase 2 Discovery 结束后执行。从源码提取验收合约，作为 Phase 3 逆向检查的 oracle。
> 不改变 Phase 2 产物，不生成 .allforai/ 标准产物，只输出 `acceptance-contracts.json`。

---

## 核心原则

**提取意图，不提取实现。**

换了技术栈，交互意图不变；组件代码完全不同。合约描述"做什么"，不描述"用什么 API 做"。

跨模块的隐性规则（散落在多个文件中、没有显式断言的约束）必须在这里整合为一条合约，不能留给各自的生成单元各自推断。

---

## Step 2.5.1: 后端行为合约提取

**来源文件：** routes / controllers / service 层（参考 extraction-plan.task_sources）

**每个接口提取：**

```json
{
  "contract_id": "BC-001",
  "module_id": "M001",
  "endpoint": "POST /api/orders",
  "inputs": {
    "fields": ["user_id", "items[]", "coupon_code"],
    "required": ["user_id", "items[]"],
    "constraints": ["items[] must not be empty", "coupon_code must be valid if provided"]
  },
  "outputs": {
    "success": { "status": 201, "body": ["order_id", "estimated_delivery"] },
    "errors": [
      { "condition": "items empty", "status": 422 },
      { "condition": "coupon expired", "status": 400 },
      { "condition": "insufficient stock", "status": 409 }
    ]
  },
  "side_effects": ["inventory.decrement", "notification.send_confirmation", "audit_log.write"],
  "cross_module_rules": [
    "User must not be banned (checked in auth middleware before handler)",
    "Order total recalculated server-side; client-provided total is ignored"
  ]
}
```

**提取要点：**
- `cross_module_rules`：专门收集散落在多个文件中的隐性约束。搜索调用链上所有中间件、装饰器、guard 的副作用
- `side_effects`：只记录写操作（写库、发消息、推通知、写日志）；读操作不是 side_effect
- `errors`：从 service 层的 throw/return error 分支提取，不要漏 guard clause

**不提取：**
- 具体 ORM 查询语句（实现）
- 框架特定的装饰器名称（实现）
- 函数名、变量名（实现）

---

## Step 2.5.2: UI 交互意图合约提取

**来源文件：** components / screens / state management（参考 extraction-plan.screen_sources）

**每个屏幕提取：**

```json
{
  "contract_id": "UI-001",
  "module_id": "M002",
  "screen": "BattleScreen",
  "states": ["loading", "in_battle", "paused", "victory", "defeat"],
  "user_actions": [
    {
      "action": "tap_attack",
      "precondition": "state == in_battle AND attack_cooldown == 0",
      "outcome": "trigger combat_handler, update hp display"
    },
    {
      "action": "open_inventory",
      "precondition": "state != in_battle",
      "outcome": "navigate to InventoryScreen"
    },
    {
      "action": "pause",
      "precondition": "state == in_battle",
      "outcome": "state → paused, show pause menu"
    }
  ],
  "transitions": [
    { "from": "loading", "trigger": "battle data loaded", "to": "in_battle" },
    { "from": "in_battle", "trigger": "enemy hp <= 0", "to": "victory" },
    { "from": "in_battle", "trigger": "player hp <= 0", "to": "defeat" }
  ],
  "intent": "玩家在此屏幕执行回合制战斗操作，战斗结束时过渡到结算界面"
}
```

**提取要点：**
- `states`：业务状态，不是 React/Flutter 的 widget state。问："用户处于哪个阶段？"
- `user_actions[].precondition`：从代码中的 disabled/guard/conditional render 提取
- `transitions`：从状态机、条件导航、router.push 调用提取触发条件
- `intent`：一句话，说用户在这个屏幕想完成什么

**对于 Web 应用（无移动端手势）：**
- `user_actions` 聚焦 click / submit / input change
- 跨 App flow（OAuth、支付跳转）标记 `"cross_app": true`

**不提取：**
- 具体 CSS 类名（实现）
- 组件库 API（实现）
- 像素级布局（实现）

---

## Step 2.5.3: 输出 acceptance-contracts.json

写入 `.allforai/code-replicate/acceptance-contracts.json`：

```json
{
  "schema_version": "1.0",
  "generated_at": "<ISO 8601 timestamp>",
  "source_path": "<source project path>",
  "total_backend_contracts": 12,
  "total_ui_contracts": 8,
  "backend_contracts": [ ... ],
  "ui_contracts": [ ... ]
}
```

**质量检查（写入前执行）：**
1. 每个 backend_contract 有至少一个 error condition（纯查询接口除外）
2. 每个 ui_contract 有至少两个 states（loading + 一个业务状态）
3. cross_module_rules 不为空的合约：确认规则来自真实的跨文件约束，不是臆测
4. 总合约数 ≥ source-summary.modules 中 UI 模块数量（每个 UI 模块至少一个 UI 合约）

---

## 逆向提取（Phase 3 使用）

Phase 3 生成目标代码后，用同一套规则从目标代码中提取合约 B：

- 后端合约 B：从目标路由/控制器提取，与源码合约 A 格式相同
- UI 合约 B：从目标屏幕/组件提取，与源码合约 A 格式相同

**Diff(A, B) 结构：**

```json
{
  "contract_id": "BC-005",
  "missing_error_conditions": [
    { "condition": "user_banned", "status": 403 }
  ],
  "missing_side_effects": ["audit_log.write"],
  "extra_error_conditions": [],
  "intent_mismatch": null
}
```

空 diff = 合约满足 = 通过。非空 diff = 精确差距 = 修复目标。
```

- [ ] **Step 2: Create opencode mirror**

Create `opencode/code-replicate-skill/docs/phase2/stage-e-contracts.md` with English translation of the same content. Structure is identical; all headers, field names, JSON schemas are the same; prose is in English.

Key English translations:
- "合约提取协议" → "Contract Extraction Protocol"
- "提取意图，不提取实现" → "Extract intent, not implementation"
- "后端行为合约提取" → "Backend Behavior Contract Extraction"
- "UI 交互意图合约提取" → "UI Interaction Intent Contract Extraction"
- All JSON field names remain identical (they are schema — language-neutral)

- [ ] **Step 3: Verify both files exist and contain the three steps**

Confirm both files have sections: Step 2.5.1, Step 2.5.2, Step 2.5.3, and the reverse extraction diff structure.

- [ ] **Step 4: Commit**

```bash
git add codex/code-replicate-skill/docs/phase2/stage-e-contracts.md opencode/code-replicate-skill/docs/phase2/stage-e-contracts.md
git commit -m "feat(code-replicate): add Phase 2.5 contract extraction protocol doc"
```

---

## Task 3: Update code-replicate-core.md — Phase 1.2 + Phase 2.5

**Files:**
- Modify: `codex/code-replicate-skill/skills/code-replicate-core.md`
- Modify: `opencode/code-replicate-skill/skills/code-replicate-core.md`

- [ ] **Step 1: Add Step 1.2 to Phase 1 in codex/code-replicate-core.md**

After step 5 (`写 replicate-config.json → ...`) in the Phase 1 section, insert:

```markdown
**Step 1.2 — 可运行性评估（门禁）**

1. 检测源项目能否构建：尝试 build 命令（package.json scripts.build / go build / flutter build / Makefile）
2. 检测目标栈运行环境：检查目标语言运行时版本、框架 CLI、数据库服务可用性
3. 根据检测结果计算保真度上限：

   | 条件 | UI 验收能力 | 保真度上限 |
   |------|------------|-----------|
   | 源 + 目标均可运行，可截图 | 完整运行时验收 | ~100% |
   | 可运行，无截图环境 | 结构验收，无视觉对比 | ~70% |
   | 源或目标无法运行 | 仅静态合约 diff | ~40% |

4. 写 `acceptance-ceiling.json` 到 `.allforai/code-replicate/`
5. 向用户展示保真度上限和 `known_gaps` 列表
6. **等待用户显式确认后才继续。** 未确认则停止，不进入 Phase 2。
```

- [ ] **Step 2: Add Phase 2.5 reference section to codex/code-replicate-core.md**

After the Phase 2 section (after `> **=== Phase 2 结束后不再问任何配置问题 ===**`), insert:

```markdown
---

### Phase 2.5: 合约提取

> 详见 ./docs/phase2/stage-e-contracts.md

Phase 2 Stage D 确认后立即执行。从源码提取验收合约，作为 Phase 3 逆向检查的 oracle。

| Step | 产出 | 做什么 |
|------|------|--------|
| 2.5.1 | backend_contracts[] | 逐接口提取：输入/输出/错误条件/副作用/跨模块规则 |
| 2.5.2 | ui_contracts[] | 逐屏幕提取：状态列表/用户操作（含前置条件）/状态转换/意图 |
| 2.5.3 | acceptance-contracts.json | 合并写入 `.allforai/code-replicate/` |

**核心原则：提取意图，不提取实现。** 换了技术栈，意图不变；组件代码完全不同。
散落在多个文件中的跨模块隐性规则必须在这里整合为显式合约项。

---
```

- [ ] **Step 3: Mirror changes to opencode/code-replicate-core.md**

Apply identical changes in English to `opencode/code-replicate-skill/skills/code-replicate-core.md`.

- [ ] **Step 4: Verify**

Read both files. Confirm:
- Step 1.2 block exists in Phase 1, contains fidelity ceiling table and gate rule
- Phase 2.5 section exists after Phase 2, with reference to stage-e-contracts.md and 3-step table

- [ ] **Step 5: Commit**

```bash
git add codex/code-replicate-skill/skills/code-replicate-core.md opencode/code-replicate-skill/skills/code-replicate-core.md
git commit -m "feat(code-replicate): add Phase 1.2 runability gate and Phase 2.5 reference to core"
```

---

## Task 4: Update code-replicate-core.md — Phase 3 reverse-check + three-tier loop

**Files:**
- Modify: `codex/code-replicate-skill/skills/code-replicate-core.md`
- Modify: `opencode/code-replicate-skill/skills/code-replicate-core.md`

- [ ] **Step 1: Replace Phase 3 artifact generation preamble in codex/code-replicate-core.md**

Find the line:
```
按 extraction-plan.artifacts 列表顺序，逐产物执行：LLM 读 sources → 生成片段 → **UI 闭环验证** → **4D 自检** → 合并。
```

Replace with:
```markdown
按 extraction-plan.artifacts 列表顺序，逐产物执行：LLM 读 sources → 生成片段 → **UI 闭环验证** → **4D 自检** → **逆向合约提取 + Diff** → 合并。
```

- [ ] **Step 2: Add the reverse-check + three-tier loop section to Phase 3 in codex/code-replicate-core.md**

After the `### 4D 片段自检（每个 Step 生成后立即执行）` section and before `### 标准产物 Step 参考`, insert:

```markdown
### 逆向合约提取 + Diff（4D 自检之后，合并之前）

**执行时机：** 每个模块片段完成 4D 自检后，合并脚本运行前。

**流程：**

```
1. 从 acceptance-contracts.json 取本模块的合约 A（BC-xxx + UI-xxx）
2. 从已生成的目标代码片段逆向提取合约 B
   - 后端片段 → 按 stage-e-contracts.md §Step 2.5.1 规则提取
   - UI 片段   → 按 stage-e-contracts.md §Step 2.5.2 规则提取
3. Diff(A, B)
   → Diff 为空：通过，执行合并
   → Diff 不为空：进入小闭环修复
```

**小闭环（单元级，max 3 轮）：**
```
diff 不为空
→ 按 diff 精确修复片段（不重写整个片段，只补缺失的 error condition / side_effect / state / action）
→ 重新逆向提取合约 B
→ 重新 Diff(A, B)
→ 空 → 通过 → 合并
→ 仍非空 → 轮次 +1 → 最多 3 轮
→ 3 轮仍非空 → 标记为 known_gap（保留完整 diff）→ 进入合并（带 gap 标记）
```

**中闭环（合约级）：**
某合约 3 轮修复均失败时，回溯 Phase 2.5 重新检查源码：
- 该合约是否提取有误（规则理解偏差）？
- 源码中该规则是否有特殊的表达方式（如通过 DB 约束而非代码逻辑）？
修正合约 A → 重新执行当前生成单元（不重跑整个 Phase 3）。

**known_gap 格式（写入 `.allforai/code-replicate/known_gaps.json`）：**

```json
{
  "gaps": [
    {
      "contract_id": "BC-005",
      "type": "backend",
      "module_id": "M001",
      "diff": {
        "missing_error_conditions": [{ "condition": "user_banned", "status": 403 }],
        "missing_side_effects": ["audit_log.write"],
        "extra_error_conditions": [],
        "intent_mismatch": null
      },
      "fix_attempts": 3,
      "status": "known_gap",
      "manual_action": "Add 403 handler for banned users; add audit logging to order creation service"
    }
  ],
  "total_contracts": 20,
  "passing": 17,
  "known_gap_count": 3
}
```
```

- [ ] **Step 3: Mirror to opencode/code-replicate-core.md**

Apply identical changes in English. JSON schemas remain identical.

- [ ] **Step 4: Verify**

Read both files. Confirm:
- The preamble line now mentions "逆向合约提取 + Diff" / "Reverse Contract Extraction + Diff"
- The new section exists between "4D 片段自检" and "标准产物 Step 参考"
- known_gap JSON schema is present with `contract_id`, `diff`, `fix_attempts`, `status`, `manual_action`

- [ ] **Step 5: Commit**

```bash
git add codex/code-replicate-skill/skills/code-replicate-core.md opencode/code-replicate-skill/skills/code-replicate-core.md
git commit -m "feat(code-replicate): add Phase 3 reverse-check and three-tier closed loop"
```

---

## Task 5: Update Phase 4 — large loop gap pattern analysis

**Files:**
- Modify: `codex/code-replicate-skill/docs/phase4/verify-handoff.md`
- Modify: `opencode/code-replicate-skill/docs/phase4/verify-handoff.md`

- [ ] **Step 1: Read verify-handoff.md to locate the step table**

Read `codex/code-replicate-skill/docs/phase4/verify-handoff.md` to find the step table (4a through 4f).

- [ ] **Step 2: Add Step 4g to codex/verify-handoff.md**

After Step 4f (`Handoff: artifact list + next steps recommendation`), add:

```markdown
| 4g | Gap pattern analysis (large loop) | Aggregate `known_gaps.json` across all modules. Identify systematic failure patterns: (1) a contract TYPE that consistently fails (e.g., all `cross_module_rules` entries are known_gaps → extraction strategy is wrong for this pattern); (2) a TARGET STACK pattern that makes reverse extraction unreliable. Write findings to `replicate-report.md` §Gap Patterns. If pattern count ≥ 3 for any category, recommend re-running Phase 2.5 with refined extraction rules before next replication attempt. |
```

Also add to the report generation section (or after 4e), a note:

```markdown
**replicate-report.md §Gap Patterns format:**

```markdown
## Gap Patterns

| Pattern | Affected Contracts | Root Cause | Recommendation |
|---------|-------------------|------------|---------------|
| cross_module_rules extraction | BC-005, BC-012, BC-019 | Rules expressed via DB constraints not visible in service layer | Re-run Phase 2.5 with explicit DB constraint scan |
| UI precondition detection | UI-003, UI-007 | Preconditions encoded as CSS `disabled` attribute, not in JS logic | Add CSS-based precondition extraction to Phase 2.5.2 |
```
```

- [ ] **Step 3: Mirror to opencode/verify-handoff.md**

Apply identical changes in English.

- [ ] **Step 4: Verify**

Read both files. Confirm Step 4g exists in the step table, and the Gap Patterns section format is documented.

- [ ] **Step 5: Commit**

```bash
git add codex/code-replicate-skill/docs/phase4/verify-handoff.md opencode/code-replicate-skill/docs/phase4/verify-handoff.md
git commit -m "feat(code-replicate): add Phase 4 gap pattern analysis (large feedback loop)"
```

---

## Task 6: Add new iron rules to code-replicate-core.md

**Files:**
- Modify: `codex/code-replicate-skill/skills/code-replicate-core.md`
- Modify: `opencode/code-replicate-skill/skills/code-replicate-core.md`

- [ ] **Step 1: Append three new iron rules to codex/code-replicate-core.md**

Find the iron rules section (## 铁律). After rule 27, append:

```markdown
28. **合约先于生成** — Phase 2.5 合约提取必须在 Phase 3 任何生成单元开始前全部完成。没有合约的生成单元无法执行逆向 Diff，等同于盲目生成
29. **逆向 Diff 是验收标准** — Phase 3 每个生成单元的完成条件是 Diff(A, B) 为空或标记为 known_gap，不是"代码看起来合理"。主观判断不是验收
30. **保真度上限用户确认** — Phase 1.2 评估结果必须向用户显式声明。用户未确认保真度上限 → Phase 2 不得启动。"跑不起来"不是障碍，是已知约束，但用户必须主动接受
```

- [ ] **Step 2: Mirror to opencode/code-replicate-core.md**

Append English equivalents:
```markdown
28. **Contracts before generation** — Phase 2.5 contract extraction must complete before any Phase 3 generation unit begins. A unit without contracts cannot run reverse diff — it is blind generation
29. **Reverse diff is the acceptance criterion** — A Phase 3 generation unit is done when Diff(A, B) is empty or marked known_gap, not when the code "looks reasonable." Subjective judgment is not acceptance
30. **Fidelity ceiling requires user confirmation** — Phase 1.2 assessment must be explicitly presented to the user. No user confirmation of fidelity ceiling → Phase 2 must not start. "Cannot run" is not a blocker, it is a known constraint — but the user must actively accept it
```

- [ ] **Step 3: Verify**

Read both files. Confirm rules 28, 29, 30 are present at the end of the iron rules list.

- [ ] **Step 4: Update artifact paths section in codex/code-replicate-core.md**

Find the `## 产物路径` section. In the **CR 专属过程文件** list, add:

```markdown
- `acceptance-ceiling.json` — Phase 1.2 保真度上限 + 用户确认状态
- `acceptance-contracts.json` — Phase 2.5 验收合约 oracle（后端 + UI）
- `known_gaps.json` — Phase 3 未收敛合约项 + 完整 diff
```

Mirror the same additions (in English) to opencode.

- [ ] **Step 5: Commit**

```bash
git add codex/code-replicate-skill/skills/code-replicate-core.md opencode/code-replicate-skill/skills/code-replicate-core.md
git commit -m "feat(code-replicate): add iron rules 28-30 and new artifact paths for contract-first flow"
```

---

## Task 7: Final verification and push

- [ ] **Step 1: Full read of codex execution-playbook**

Read `codex/code-replicate-skill/execution-playbook.md`. Verify:
- Phase overview table: 5 rows (1, 2, 2.5, 3, 4)
- Phase 1 has Step 1.2 section with fidelity ceiling table
- Phase 2.5 section exists
- Phase 3 heading says "Generate + Reverse-Check"
- Phase 4 step table includes 4g

- [ ] **Step 2: Full read of codex core**

Read `codex/code-replicate-skill/skills/code-replicate-core.md`. Verify:
- Phase 1 has Step 1.2 block
- Phase 2.5 reference section exists
- Phase 3 has reverse-check + three-tier loop section
- known_gap JSON schema is present
- Iron rules end at 30
- Artifact paths include 3 new files

- [ ] **Step 3: Spot-check opencode mirrors**

Read first 50 lines of `opencode/code-replicate-skill/execution-playbook.md` and `opencode/code-replicate-skill/skills/code-replicate-core.md` to confirm Phase 1.2 section is present in English.

- [ ] **Step 4: Push**

```bash
git push
```
