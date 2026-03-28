# code-replicate v5.6.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enhance code-replicate with LLM reasoning-driven improvements to prevent systematic UI feature omission, silent dimension skipping, and false completion judgments — based on real Flutter→WPF/.NET feedback.

**Architecture:** All changes are prompt instruction modifications to existing `.md` skill/doc files. No Python scripts or programmatic changes. Each change adds LLM reasoning blocks (JSON examples + guidelines) at specific insertion points within existing protocol files.

**Tech Stack:** Markdown skill files (Claude Code plugin system)

---

## File Structure

All files already exist — this plan modifies them. No new files created.

| File | Responsibility | Tasks |
|------|---------------|-------|
| `claude/code-replicate-skill/skills/code-replicate-core.md` | Main 4-phase protocol | 1, 2, 7, 8 |
| `claude/code-replicate-skill/docs/schema-reference.md` | Artifact JSON schemas | 3 |
| `claude/code-replicate-skill/docs/analysis-principles.md` | Source analysis framework | 4 |
| `claude/code-replicate-skill/skills/cr-fidelity.md` | Fidelity verification | 5 |
| `claude/code-replicate-skill/docs/fidelity/static-dimensions.md` | F1-F10 scoring rules | 6 |
| `claude/code-replicate-skill/skills/cr-visual.md` | Visual restoration | 9 |
| `claude/code-replicate-skill/docs/cr-visual/step-capture.md` | Screenshot capture | 9 |
| `claude/code-replicate-skill/SKILL.md` | Plugin entry + version | 10 |
| `claude/code-replicate-skill/.claude-plugin/plugin.json` | Plugin manifest | 10 |
| `claude/code-replicate-skill/.claude-plugin/marketplace.json` | Marketplace listing | 10 |

---

### Task 1: Add Adaptive Source Access to Phase 1

**Files:**
- Modify: `claude/code-replicate-skill/skills/code-replicate-core.md:25-52` (Phase 1 section)

This is Change 8 from the spec. It modifies Phase 1 Preflight to support three source access modes instead of mandatory git clone.

- [ ] **Step 1: Read the current Phase 1 section**

Read `claude/code-replicate-skill/skills/code-replicate-core.md` lines 25-52 to confirm the exact insertion point. The new content goes after step 3 ("源码获取") and replaces the current clone-only behavior.

- [ ] **Step 2: Replace Phase 1 step 3 with adaptive source access**

In `code-replicate-core.md`, find the Phase 1 section. Replace step 3:

```markdown
3. 源码获取：
   - 本地路径 → 直接使用
   - Git URL → `git clone --depth 1`（HTTPS / SSH / GitHub 短语法 `user/repo`）
   - 支持 `#branch` 后缀指定分支：`https://github.com/user/repo#develop`
```

With:

```markdown
3. 源码访问策略（自适应）：

   LLM 根据 source_path 类型自动选择访问模式，写入 replicate-config.json 的 `source_access` 字段：

   ```json
   {
     "source_access": {
       "source_path": "用户提供的路径或 URL",
       "detected_type": "remote_git | local_directory | same_repo_branch",
       "strategy": "clone | direct_read | git_show",
       "reasoning": "LLM 解释选择原因"
     }
   }
   ```

   **Mode 1: Clone（remote_git）**
   - 条件：source_path 是远程 URL（https://, git@, ssh://）
   - 操作：`git clone --depth 1` 到临时目录（支持 `#branch` 后缀：`https://github.com/user/repo#develop`）
   - GitHub 短语法 `user/repo` 也走 clone

   **Mode 2: Direct Read（local_directory）**
   - 条件：source_path 是本地文件系统路径
   - 操作：直接通过 Read 工具读取，不复制
   - 记录 consistency_anchor：
     ```json
     {
       "anchor_commit": "当前 HEAD commit hash",
       "anchor_timestamp": "ISO8601",
       "warning": "源码在分析期间变更时，建议从 Phase 2 重跑"
     }
     ```
   - 跨会话恢复时：检查 HEAD 是否仍等于 anchor_commit，偏移则警告用户

   **Mode 3: Git Show（same_repo_branch）**
   - 条件：source_path 是当前仓库中的分支名（如 `origin/flutter-app`）
   - 操作：用 `git show branch:path/to/file` 读取文件，不 checkout/worktree
   - 记录分支 HEAD 作为 anchor

   **Edge case**: source_path 是 zip/tarball → 解压到临时目录，按 Mode 1 处理

   **下游影响**：Phase 2+ 的所有文件读取遵循 source_access.strategy：
   - clone → Read clone_dir/path
   - direct_read → Read source_path/path
   - git_show → Bash: `git show branch:path`
```

- [ ] **Step 3: Verify no broken cross-references**

Search `code-replicate-core.md` for other references to "git clone" or "源码获取" to ensure consistency. The step 3 replacement should be the only change needed.

- [ ] **Step 4: Commit**

```bash
git add claude/code-replicate-skill/skills/code-replicate-core.md
git commit -m "feat(code-replicate): adaptive source access — clone/direct_read/git_show modes in Phase 1"
```

---

### Task 2: Add Extraction Plan Self-Review to Phase 3-pre

**Files:**
- Modify: `claude/code-replicate-skill/skills/code-replicate-core.md:112-168` (Phase 3-pre section)

This is Change 1 from the spec. Insert EXTRACTION_PLAN_REVIEW step after extraction-plan.json generation (after line ~168 "生成原则" block) and before the artifacts section.

- [ ] **Step 1: Read the Phase 3-pre section**

Read `claude/code-replicate-skill/skills/code-replicate-core.md` lines 110-170 to confirm exact insertion point. The new block goes after the `extraction-plan.json` schema example and "生成原则" block, before "### extraction-plan.artifacts".

- [ ] **Step 2: Insert EXTRACTION_PLAN_REVIEW block**

After the "生成原则" list (currently ending around line 168: `dependency_map — LLM 读...`), insert:

```markdown
### EXTRACTION_PLAN_REVIEW（Phase 3-pre 末尾，extraction-plan 生成后立即执行）

LLM 切换到**审查者视角**，审视自己刚生成的 extraction-plan，输出 `plan_review`（写入 extraction-plan.json 的 `plan_review` 字段）：

```json
{
  "plan_review": {
    "modules_examined": [
      {
        "module": "M003",
        "total_files": 78,
        "key_files_selected": 4,
        "coverage_assessment": "key_files 仅覆盖顶层入口（主 widget + 状态管理）。子目录 widgets/message_types/ 有 24 个文件处理不同消息类型渲染，chat_input/ 有 8 个文件处理输入交互（语音/拖拽/粘贴/表情）。这些子文件承载独立的用户可见功能，不被顶层入口覆盖。",
        "blind_spots": ["描述未覆盖的子目录/文件及其承载的用户功能"],
        "decision": "扩充 key_files：追踪入口文件 import 链，加入承载独立用户功能的子文件。预计从 4 → 22 个。",
        "rationale": "这些不是工具类文件——每个都承载用户可直接感知的功能。漏掉任何一个 = 目标产物缺失该功能。"
      }
    ],
    "overall_confidence": "审查后覆盖率从 5% 提升至 28%。剩余 72% 为工具类/模型类/配置类，不含独立用户功能。"
  }
}
```

**审查推理指引**（非硬阈值）：
- **用户影响测试**：对每个模块，问自己："如果用户打开目标应用，哪些功能会因 key_files 未覆盖而缺失？用户会注意到吗？"
- **Import 链追踪**：从每个 key_file 出发，沿 import 链向下走一层，检查被引用文件是否承载独立功能（vs 纯 utility）
- **枚举/switch 检测**：如果 key_file 中有 switch(type) 且 case > 5，每个 case 对应的渲染文件值得加入
- **子目录采样**：对未被 import 链覆盖的子目录，读取前 3 个文件头部（class 名 + 公开方法签名），判断是否有遗漏的用户功能

审查完毕后，LLM 根据 plan_review 的结论更新 extraction-plan.json 的各 `*_sources` 字段（补充新发现的 key_files），然后继续。
```

- [ ] **Step 3: Commit**

```bash
git add claude/code-replicate-skill/skills/code-replicate-core.md
git commit -m "feat(code-replicate): extraction plan self-review — LLM audits key_files coverage before Phase 3"
```

---

### Task 3: Add Experience Map Schema Extensions

**Files:**
- Modify: `claude/code-replicate-skill/docs/schema-reference.md:75-100` (extraction-plan section, and add experience-map extensions)

This is the schema portion of Change 2. Add `interaction_triggers` and `state_variants` optional fields.

- [ ] **Step 1: Read schema-reference.md experience-map section**

Read `claude/code-replicate-skill/docs/schema-reference.md` to find where experience-map fields are documented (or where to add a new section if not present). Based on line 1-3, standard experience-map follows product-design definitions, so we add a "code-replicate extensions" subsection.

- [ ] **Step 2: Append experience-map extensions section**

At the end of `schema-reference.md`, append:

```markdown
---

## experience-map.json — Code-Replicate Extensions

> 以下字段是 code-replicate 对标准 experience-map schema 的扩展。product-design 不生成这些字段。字段均为可选——depth=stub 的 screen 不包含。

### components[].interaction_triggers（可选，depth=deep 时填充）

记录用户触发方式和预期响应。用于 cr-fidelity U6 评分和 Completeness Sweep 维度 B 验证。

```json
{
  "component": "MessageBubble",
  "interaction_triggers": [
    {"trigger": "tap", "target": "图片消息", "response": "全屏预览"},
    {"trigger": "long_press", "target": "任意消息", "response": "操作菜单（转发/收藏/删除）"},
    {"trigger": "double_tap", "target": "文本消息", "response": "文本选择模式"}
  ]
}
```

**字段说明**：
- `trigger` — 用户交互事件类型（tap/click/long_press/drag/drop/paste/keydown/hover 等）
- `target` — 触发该交互的具体目标（消息类型/按钮/区域）
- `response` — 预期的 UI 响应（页面跳转/弹窗/状态变化/动画）

### components[].state_variants（可选，depth=deep 时填充）

记录组件的完整状态空间，超越默认的 loading/error/empty。

```json
{
  "component": "VoiceMessage",
  "state_variants": [
    {"state": "recording", "visual": "红色脉冲动画 + 时长计数"},
    {"state": "recorded_preview", "visual": "波形图 + 播放/删除按钮"},
    {"state": "sending", "visual": "上传进度条"},
    {"state": "sent", "visual": "静态波形 + 时长标签"},
    {"state": "playing", "visual": "播放进度动画 + 暂停按钮"},
    {"state": "expired", "visual": "灰色 + '已过期' 标签"}
  ]
}
```

**字段说明**：
- `state` — 状态名称
- `visual` — 该状态的视觉表现描述

### 向后兼容性

两个字段均为可选。不填充时，现有 experience-map 消费者（dev-forge、cr-fidelity U1-U5）不受影响。cr-fidelity U6 和 Completeness Sweep 维度 B 读取这些字段时，字段不存在视为"未做 deep 分析"，不扣分。
```

- [ ] **Step 3: Commit**

```bash
git add claude/code-replicate-skill/docs/schema-reference.md
git commit -m "feat(code-replicate): add interaction_triggers + state_variants to experience-map schema"
```

---

### Task 4: Add Principle #7 to Analysis Principles

**Files:**
- Modify: `claude/code-replicate-skill/docs/analysis-principles.md` (append after principle 6, line 143)

This is Change 3 from the spec.

- [ ] **Step 1: Append principle #7 at end of file**

After the existing principle 6 ("Inferring Cross-Cutting Concerns") ending at line 143, append:

```markdown

---

## 7. Identifying User-Perceivable Capabilities

User-perceivable capabilities are features that end users directly interact with or notice. They sit at the boundary between "business intent" (must extract) and "implementation decision" (replaceable).

**The Disappearance Test:**

> "If this capability vanishes from the target application, would an end user notice during normal usage?"
> - Would notice → **user feature** (must extract to task-inventory / experience-map)
> - Would not notice → **implementation detail** (replaceable, record in stack-mapping)

**Reasoning examples:**

| Capability | Disappearance Test | Classification |
|------------|-------------------|---------------|
| Drag file to chat window to send | User could do it before, can't now → notices | User feature |
| Emoji picker popup | User could pick emojis, now can't → notices | User feature |
| Clipboard paste image (Ctrl+V) | Ctrl+V sent screenshots before, doesn't now → notices | User feature |
| Voice recording and playback | User could send/receive voice, now can't → notices | User feature |
| Fullscreen image preview on tap | User could tap to enlarge, now can't → notices | User feature |
| Long-press context menu (6 options) | User had 6 actions, now has 2 → notices 4 missing | Each option = user feature |
| BLoC vs Provider state management | Same UX either way → doesn't notice | Implementation detail |
| GridView vs ListView rendering | Same data and interaction → doesn't notice | Implementation detail |
| flutter_sound vs just_audio library | Same record/play UX → doesn't notice | Implementation detail |

**Three-Layer Model** (reasoning aid, not rigid classification):

1. **User Capability Layer** (What + How user triggers it)
   - Must extract to task-inventory and/or experience-map interaction_triggers
   - Examples: send voice message, fullscreen preview, drag-sort list items, paste image from clipboard

2. **Interaction Implementation Layer** (Which library/component implements it)
   - Record in stack-mapping.json, replaceable in target with equivalent
   - Examples: flutter_sound vs just_audio, Hero animation vs custom transition, native file picker vs web API

3. **Code Structure Layer** (Code patterns and architecture)
   - Do not copy — target ecosystem conventions apply
   - Examples: BLoC vs MVVM, single-file components vs split, mixin vs inheritance, dependency injection style

**Boundary disambiguation — the "apology test":**

> When unsure whether something is a user feature or implementation detail, apply:
> "If this capability disappears from the release, would we need to apologize to users in release notes?"
> - Yes → user feature (extract it)
> - Only developers would notice in code review → implementation detail (skip it)

**Application to extraction-plan:**
- For each screen_source and task_source, LLM should trace not just the main handler but also event bindings (onTap, onClick, onDrag, onPaste, onKeyDown, onLongPress, etc.)
- Each distinct user trigger that produces a user-visible response = one capability to extract
- Enum/switch rendering branches where each case produces distinct user-visible behavior should be extracted individually, not collapsed into a single component
```

- [ ] **Step 2: Commit**

```bash
git add claude/code-replicate-skill/docs/analysis-principles.md
git commit -m "feat(code-replicate): add principle #7 — user-perceivable capabilities with disappearance test"
```

---

### Task 5: Add Experience Map Adaptive Depth to Phase 3

**Files:**
- Modify: `claude/code-replicate-skill/skills/code-replicate-core.md:210-232` (Phase 3 generation section)

This is Change 2 from the spec. Insert depth_decision logic into the Phase 3 experience-map generation instructions.

- [ ] **Step 1: Read the Phase 3 generation section**

Read `claude/code-replicate-skill/skills/code-replicate-core.md` lines 210-250 to find the exact insertion point. The depth_decision goes after the "按 extraction-plan.artifacts 列表顺序" line (around 212) and before "### UI 驱动的闭环理解".

- [ ] **Step 2: Insert depth_decision block**

After line 212 (`按 extraction-plan.artifacts 列表顺序，逐产物执行：LLM 读 sources → 生成片段 → **UI 闭环验证** → **4D 自检** → 合并。`), insert:

```markdown

### Experience-Map 自适应深度（生成 experience-map 片段时）

生成 experience-map 的 screen 片段时，LLM 对每个 screen 自主决定分析深度：

```json
{
  "screen": "chat_main",
  "depth": "deep",
  "depth_reasoning": "核心组件 MessageList 有 switch(message.type) 分出 74 个渲染分支，每个分支有独立交互行为。stub 级别只能记录 'MessageList 存在'，无法区分 74 种不同用户体验。",
  "complexity_signals": ["switch/enum 分支数: 74", "交互事件类型: click/longpress/drag/paste", "状态变体: loading/sending/failed/recalled"]
}
```

**LLM 判断 depth 的信号**（非规则，推理参考）：
- 该 screen 源文件 import 数量 > 10 → 可能需要 deep
- 存在 switch/if-else 链且分支 > 5 → 建议 deep
- 组件有多种交互事件（不只是 click）→ 建议 deep
- 纯展示型 screen（设置页/关于页）→ stub 足够

**depth = deep 时额外提取**：
1. **interaction_triggers**：对每个 component，记录用户触发方式和预期响应（schema 见 `${CLAUDE_PLUGIN_ROOT}/docs/schema-reference.md` experience-map extensions 章节）
2. **state_variants**：对每个 component，记录完整状态空间（超越默认 loading/error/empty）
3. **枚举驱动渲染展开**：当检测到 switch/enum 模式且分支 > 5 时，逐分支提取为独立 component 或 variant 条目

**depth = stub 时**：保持现有行为——只记录顶层 component 列表 + 基本 states 字典。
```

- [ ] **Step 3: Commit**

```bash
git add claude/code-replicate-skill/skills/code-replicate-core.md
git commit -m "feat(code-replicate): experience-map adaptive depth — LLM decides stub vs deep per screen"
```

---

### Task 6: Add Dimension Applicability Reasoning to cr-fidelity

**Files:**
- Modify: `claude/code-replicate-skill/skills/cr-fidelity.md:32-68` (Phase 0 section)
- Modify: `claude/code-replicate-skill/skills/cr-fidelity.md:121-132` (scoring formula)

This is Change 4 from the spec.

- [ ] **Step 1: Read Phase 0 dimension selection**

Read `claude/code-replicate-skill/skills/cr-fidelity.md` lines 32-68 to understand current mechanical mapping.

- [ ] **Step 2: Replace dimension selection with reasoning block**

Replace the current "### 自适应维度选择" section (lines 39-66, from "LLM 扫描 `.allforai/` 产物" through the closing ``` block) with:

```markdown
### 自适应维度选择（LLM 推理版）

LLM 扫描 `.allforai/` 产物，对每个维度族（F/U/I/A/B）输出**适用性论证**，写入 fidelity-report.json 的 `dimension_reasoning[]`：

```json
{
  "dimension_reasoning": [
    {
      "dimension_group": "F",
      "applicable": true,
      "reasoning": "task-inventory.json 含 45 个 task，business-flows.json 含 12 条流程。后端业务逻辑是本项目的核心价值层。",
      "artifacts_examined": ["task-inventory.json", "business-flows.json", "role-profiles.json"],
      "risk_if_skipped": "high — 45 个 API 端点 + 12 条业务流将逃逸评估",
      "weight": 1.0
    },
    {
      "dimension_group": "U",
      "applicable": true,
      "reasoning": "experience-map.json 含 12 个 screen，其中 8 个有 components 和 actions。目标是 WPF 桌面应用，UI 是用户价值的主要载体。",
      "artifacts_examined": ["experience-map.json", "source-summary.json"],
      "risk_if_skipped": "high — 12 个 screen、40+ 个组件将逃逸评估",
      "weight": 1.2
    }
  ]
}
```

**产物存在性仍是起点**——LLM 检查各产物文件是否存在，但不机械映射。对每个维度族：
1. 检查相关产物是否存在
2. 评估该维度族对**本项目**的重要性
3. 输出 reasoning + risk_if_skipped + weight

**自相矛盾检测**：
- 如果 `risk_if_skipped = high` 且 `applicable = false` → 触发 CONTRADICTION 警告
- LLM 必须重新审视一次（one-shot）：重新得出相同结论 → `contradiction_acknowledged: true`，决策生效

**动态权重**：
- LLM 根据项目特征为每个维度族分配 weight（默认 1.0）
- 纯 API 后端 → F weight 高，U weight 低或 N/A
- UI 密集型应用 → U weight 提升至 1.2+，F weight 保持 1.0
- 权重和 reasoning 持久化到 fidelity-report.json，可追溯

**不允许静默跳过**：每个维度族必须出现在 `dimension_reasoning[]` 中——要么 `applicable: true`（评分），要么 `applicable: false`（带 reasoning 和 risk 评估）。报告中不得有维度族缺席。

读取各维度详细规则的方式不变：
> 详见 ${CLAUDE_PLUGIN_ROOT}/docs/fidelity/static-dimensions.md（F1-F10）
> 详见 ${CLAUDE_PLUGIN_ROOT}/docs/fidelity/ui-dimensions.md（U1-U6）
> 详见 ${CLAUDE_PLUGIN_ROOT}/docs/fidelity/runtime-verification.md（R1-R5）
> 详见 ${CLAUDE_PLUGIN_ROOT}/docs/fidelity/infra-critical-dimensions.md（I1-I5）
> 详见 ${CLAUDE_PLUGIN_ROOT}/docs/fidelity/algorithm-dimensions.md（A1-A3）
> 详见 ${CLAUDE_PLUGIN_ROOT}/docs/fidelity/abi-dimensions.md（B1-B4）
```

- [ ] **Step 3: Replace scoring formula**

Replace lines 121-132 (the "## 综合评分" section):

```markdown
## 综合评分

```
静态分 = sum(维度分_i × weight_i) / sum(weight_i)
  — weight_i 来自 dimension_reasoning[].weight
  — N/A 维度（总数为 0）不参与计算

运行时分 = (有效 R* 之和) / 有效运行时维度数

综合分 = 静态分 × 0.5 + 运行时分 × 0.5

特殊规则：I 维度（关键基础设施）有任何一个评 0 分
  → 综合分标记为 CRITICAL_INFRA_FAILURE
  → 不管其他维度多高分，报告首行标红警告
  → 修复阶段优先处理 I 维度的 gap
```
```

- [ ] **Step 4: Commit**

```bash
git add claude/code-replicate-skill/skills/cr-fidelity.md
git commit -m "feat(cr-fidelity): dimension applicability reasoning + dynamic weights + no-silent-skip"
```

---

### Task 7: Add Code Comprehension Evidence to Static Dimensions

**Files:**
- Modify: `claude/code-replicate-skill/docs/fidelity/static-dimensions.md:1-30` (scoring rules section)

This is Change 6 from the spec.

- [ ] **Step 1: Read the current scoring rules**

Read `claude/code-replicate-skill/docs/fidelity/static-dimensions.md` lines 1-30 to see the current "先读后评" and "存在 ≠ 使用" rules.

- [ ] **Step 2: Insert code comprehension evidence block**

After line 29 (end of the "evidence 必须包含代码引用" paragraph, before the `---` separator), insert:

```markdown

### 代码理解摘要（所有 F/U 维度的每条评分项必须输出）

LLM 对每条评分项不只输出 match/gap + evidence 引用，还必须输出**代码理解摘要**，证明 LLM 真正理解了目标代码做什么：

```json
{
  "item": "OrderViewModel — 订单管理",
  "verdict": "implemented",
  "code_comprehension": {
    "files_read": ["ViewModels/OrderViewModel.cs"],
    "lines_examined": "1-580",
    "summary": "该 ViewModel 包含 LoadOrders() 通过 IOrderService 加载分页数据，CreateOrder()/UpdateOrder() 实现 CRUD，ExportToExcel() 处理导出。有 15 个 RelayCommand 绑定到 View。不是空壳——业务逻辑完整，包含验证、错误处理和状态管理。",
    "call_chain": "View.xaml → OrderViewModel.LoadOrders() → OrderService.GetPagedAsync() → Repository.QueryAsync()",
    "confidence": "high — 实际读取了完整实现，非仅文件名推断"
  }
}
```

**反模式自查**（LLM 在填写每条评分项时检查自己）：
- 如果 `summary` 只有表层描述（"文件存在"/"类已定义"）→ 必须承认 evidence 不足，重新读取代码
- 如果 `call_chain` 中断（定义存在但无调用者）→ 不能判为 `implemented`，应判为 `dead_code`
- 如果 `lines_examined` 范围 < 20 行而 verdict 为 "implemented" → 必须解释为何这么少的代码就能判定完成度

没有硬编码"空壳"阈值。LLM 必须用自然语言说明代码做了什么——如果说不出来，就是没读。
```

- [ ] **Step 3: Commit**

```bash
git add claude/code-replicate-skill/docs/fidelity/static-dimensions.md
git commit -m "feat(cr-fidelity): code comprehension evidence — LLM must prove it read and understood the code"
```

---

### Task 8: Add Completeness Sweep to Phase 3

**Files:**
- Modify: `claude/code-replicate-skill/skills/code-replicate-core.md:249-253` (between Phase 3 end and Phase 4)

This is Change 7 from the spec. Insert the dual-dimension sweep between Phase 3 artifacts generation and Phase 4 verify-handoff.

- [ ] **Step 1: Read Phase 3/4 boundary**

Read `claude/code-replicate-skill/skills/code-replicate-core.md` lines 245-255 to find the exact insertion point. The sweep goes after "### 标准产物 Step 参考" and before "### Phase 4: Verify & Handoff".

- [ ] **Step 2: Insert Completeness Sweep section**

Before the line `### Phase 4: Verify & Handoff` (around line 251), insert:

```markdown

### COMPLETENESS_SWEEP（Step 3.sweep — Phase 3 最后一步，Phase 4 之前）

> 进度追踪 step ID: `"3.sweep"`。`--from-phase 4` 跳过此步，`--from-phase 3.sweep` 仅重跑此步。
> 这是纵深防御——即使 EXTRACTION_PLAN_REVIEW（per-module）和 depth_decision（per-screen）已改善覆盖，仍需要**全局视角**兜底。

LLM 从两个相反的方向审视产物完整性：

#### 维度 A：源码覆盖（从文件出发）

LLM 遍历源项目目录结构（不是从已提取产物出发），对每个源文件分类：

- **已覆盖**（covered）：被 extraction-plan 的某个 source 引用
- **间接覆盖**（indirectly_covered）：未被直接引用，但其功能被上层文件包含
- **未覆盖**（uncovered）：既未被引用，也未被上层包含

对所有未覆盖文件，LLM 读取文件头部（class 名 + 公开方法签名），判断：
- 工具类/配置/测试 → 合理跳过，记录原因
- 独立用户功能 → `late_discovery`，补充到产物

#### 维度 B：源 App 体验走查（从用户出发）

LLM 基于 role-profiles，为每个角色构建一条**典型使用旅程**：

```json
{
  "role": "普通用户",
  "journey": [
    "打开 app → 看到什么？",
    "进入主界面 → 有哪些入口？",
    "进入核心功能 → 能做什么？",
    "操作完成 → 有什么反馈？",
    "异常情况 → 看到什么？"
  ]
}
```

对旅程中的每一步，LLM 检查：
- 该步骤的 screen 是否在 experience-map 中？
- 该步骤的交互是否在 task-inventory 或 interaction_triggers 中？
- 该步骤的状态变体是否在 state_variants 中？

**信息来源优先级**（构建旅程时）：
1. Phase 2 截图/录像（如果存在）→ 最直观
2. 源码路由表/导航配置 → 所有 screen 入口
3. 源码事件绑定（onTap/onClick/onDrag/...）→ 交互清单
4. 源码状态枚举/条件渲染 → 状态变体
5. 源码权限检查 → 角色差异

多信号交叉验证，不依赖单一来源。

#### 合并协议

维度 A 的 `late_discovery` + 维度 B 的 `gaps` → 去重 → 生成**补充片段**（格式与 Phase 3 per-module 片段相同，tagged `"source": "sweep"`）→ 通过现有 merge 脚本（cr_merge_tasks.py 等）合并，尊重 ID 范围和铁律 4。

#### 输出

写入 `.allforai/code-replicate/completeness-sweep.json`：

```json
{
  "total_source_files": 78,
  "covered": 22,
  "indirectly_covered": 38,
  "uncovered": 18,
  "uncovered_analysis": [
    {"file": "...", "verdict": "late_discovery | skip", "reason": "...", "action": "..."}
  ],
  "journey_checks": [
    {"role": "...", "steps_checked": 28, "gaps_found": 6, "gaps": [...]}
  ],
  "late_discoveries_count": 5,
  "journey_gaps_count": 6,
  "merged_fragments": 8,
  "sweep_confidence": "补充后用户可感知功能覆盖率预计从约 85% 提升至 93%"
}
```
```

- [ ] **Step 3: Add 3.sweep to progress tracking example**

In the "断点续跑" section (around line 306-327), add `"3.sweep"` to the step examples. Find the line:

```markdown
- Phase 3 的每个 artifact 精确到 `"3.task-inventory"` / `"3.system-spec"` 等
```

Replace with:

```markdown
- Phase 3 的每个 artifact 精确到 `"3.task-inventory"` / `"3.system-spec"` / `"3.sweep"` 等
```

- [ ] **Step 4: Commit**

```bash
git add claude/code-replicate-skill/skills/code-replicate-core.md
git commit -m "feat(code-replicate): completeness sweep — dual-dimension safety net before Phase 4"
```

---

### Task 9: Add Screenshot Compensation to cr-visual

**Files:**
- Modify: `claude/code-replicate-skill/skills/cr-visual.md:72-73` (capture agent failure condition)
- Modify: `claude/code-replicate-skill/docs/cr-visual/step-capture.md:59` (exit behavior)

This is Change 5 from the spec.

- [ ] **Step 1: Read cr-visual.md capture agent section**

Read `claude/code-replicate-skill/skills/cr-visual.md` lines 62-74 to see the current "失败条件：无可用截图 → 报错退出" line.

- [ ] **Step 2: Replace failure condition in cr-visual.md**

Find the line (around line 73):
```
   - 失败条件：无可用截图 → 报错退出
```

Replace with:
```
   - 失败条件：源端 + 目标端**均**无截图 → 报错退出
   - 仅源端无截图 → 启动 CAPTURE_UNAVAILABLE 补偿策略（见 step-capture.md）
   - 仅目标端无截图 → 报错退出（"目标应用必须可运行才能做视觉验证"）
```

- [ ] **Step 3: Read step-capture.md exit behavior**

Read `claude/code-replicate-skill/docs/cr-visual/step-capture.md` lines 55-60 to see the current "无截图可用 → 报错退出" line.

- [ ] **Step 4: Replace exit behavior in step-capture.md**

Find the line (around line 59):
```
**无截图可用** → 报错退出。
```

Replace with:
```markdown
**截图可用性判定**：

- 源端 + 目标端均有截图 → 正常流程（继续 Step 3）
- **仅源端无截图** → 启动 CAPTURE_UNAVAILABLE 补偿策略：

  LLM 自主决定补偿方案，输出 compensation_strategy：

  ```json
  {
    "capture_status": {
      "source_screenshots": "unavailable",
      "target_screenshots": "available",
      "reason": "LLM 描述具体原因（如：源 App 为 Flutter iOS，当前环境无 iOS 模拟器）"
    },
    "compensation_strategy": {
      "reasoning": "截图是 UI 闭环验证的最后防线。缺少源端截图意味着无法做视觉比对。需用其他手段补偿信息缺口。",
      "actions": [
        {
          "action": "升级 experience-map 分析深度",
          "detail": "将所有 depth=stub 的 screen 升级为 deep，通过更深的代码阅读弥补截图缺失",
          "rationale": "截图一眼看到的 UI 元素和状态，现在只能通过读代码还原"
        },
        {
          "action": "构建文本化 screen 描述",
          "detail": "对每个 screen 生成自然语言描述，作为截图替代物供 structural 比对",
          "rationale": "文本描述替代视觉截图"
        },
        {
          "action": "加重 Completeness Sweep 维度 B",
          "detail": "体验走查从辅助验证升级为主要验证手段",
          "rationale": "没有截图时，用户旅程走查是唯一的体验层验证"
        }
      ],
      "residual_risk": "无法验证像素级视觉还原。建议用户在目标环境可用时补跑 /cr-visual analyze",
      "confidence_adjustment": "visual 维度置信度从 high 降为 medium，报告标注 VISUAL_PARTIALLY_VERIFIED"
    }
  }
  ```

  LLM 根据具体不可用场景自由组合补偿手段，不限于上述三种。核心原则：**截图缺失 → 用更深的代码理解补偿信息缺口**。

- **仅目标端无截图** → 报错退出："目标应用必须可运行才能做视觉验证"
- **源端 + 目标端均无截图** → 报错退出（不变）
```

- [ ] **Step 5: Commit**

```bash
git add claude/code-replicate-skill/skills/cr-visual.md claude/code-replicate-skill/docs/cr-visual/step-capture.md
git commit -m "feat(cr-visual): screenshot unavailability compensation — LLM decides fallback strategy"
```

---

### Task 10: Version Bump to v5.6.0

**Files:**
- Modify: `claude/code-replicate-skill/SKILL.md:8`
- Modify: `claude/code-replicate-skill/.claude-plugin/plugin.json:4`
- Modify: `claude/code-replicate-skill/.claude-plugin/marketplace.json:9`

- [ ] **Step 1: Update SKILL.md version**

In `claude/code-replicate-skill/SKILL.md`, change line 8:
```
version: "5.5.2"
```
to:
```
version: "5.6.0"
```

- [ ] **Step 2: Update plugin.json version**

In `claude/code-replicate-skill/.claude-plugin/plugin.json`, change:
```json
"version": "5.5.2",
```
to:
```json
"version": "5.6.0",
```

- [ ] **Step 3: Update marketplace.json version**

In `claude/code-replicate-skill/.claude-plugin/marketplace.json`, change:
```json
"version": "5.5.2",
```
to:
```json
"version": "5.6.0",
```

- [ ] **Step 4: Commit**

```bash
git add claude/code-replicate-skill/SKILL.md claude/code-replicate-skill/.claude-plugin/plugin.json claude/code-replicate-skill/.claude-plugin/marketplace.json
git commit -m "bump: code-replicate 5.5.2 → 5.6.0 — LLM reasoning enhancements"
```
