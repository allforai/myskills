---
name: bootstrap
description: >
  Internal skill for /bootstrap command. Performs lightweight project analysis,
  generates project-specific node-specs and workflow.json, validates products,
  and writes to target project. Use when user runs /bootstrap.
---

# Bootstrap Protocol v0.2.0

## Overview

Bootstrap analyzes a target project and generates project-specific configurations:
- node-specs (one per workflow node, fully specialized)
- workflow.json (node graph + transition log)
- .claude/commands/run.md (orchestrator entry point)

All generated products are written to the target project directory.
Products are disposable — regenerate anytime with `/bootstrap`.

---

## Step 1: Lightweight Analysis

> Goal: Understand the project enough to generate good node-specs.
> NOT a deep scan — just "what does this project look like?"

### 1.0 Detect Existing State

Before analyzing code, check if this project already has artifacts:

```bash
ls .allforai/product-map/ .allforai/experience-map/ .allforai/use-case/ .allforai/bootstrap/ 2>/dev/null
```

Record what exists:
- `has_product_artifacts`: true if product-map/task-inventory.json exists
- `has_experience_map`: true if experience-map/experience-map.json exists
- `has_bootstrap`: true if bootstrap/workflow.json exists (previous /bootstrap run)
- `has_code`: true if any code files detected in Step 1.1
- `has_iteration_feedback`: true if product-concept/iteration-feedback.json exists (previous concept-acceptance feedback)
- `has_product_concept`: true if product-concept/product-concept.json exists
- `has_decision_journal`: true if product-concept/decision-journal.json exists (previous /journal records)
- `has_concept_drift`: true if product-concept/concept-drift.json exists AND its `resolved` field is false

This affects Step 1.5 options:
- has_product_artifacts + has_code → verification/demo/tune options are relevant
- has_bootstrap → offer to reuse or regenerate
- no code + no artifacts → only "create" option
- has_iteration_feedback → LLM reads feedback in Step 2, prioritizes fixing previous gaps in Step 3
- has_concept_drift → Step 3 uses incremental re-planning (Step 3.0) instead of full planning

### 1.1 Read Root Indicators

Read these files if they exist (skip missing ones silently):

**Package managers / language markers:**
- package.json, package-lock.json, yarn.lock, pnpm-lock.yaml
- go.mod, go.sum
- Cargo.toml, Cargo.lock
- pubspec.yaml, pubspec.lock
- Podfile, Podfile.lock
- build.gradle, build.gradle.kts, settings.gradle
- requirements.txt, pyproject.toml, setup.py, Pipfile
- Gemfile, composer.json, pom.xml, *.csproj, *.sln

**Configuration:**
- tsconfig.json, jsconfig.json
- vite.config.*, webpack.config.*, next.config.*
- docker-compose.yml, Dockerfile
- .github/workflows/*.yml, .gitlab-ci.yml, Jenkinsfile
- .env.example, .env.template

**Documentation:**
- README.md, README.rst
- docs/ directory (list contents, read first .md file)
- ARCHITECTURE.md, CONTRIBUTING.md

From these, extract:
- Language(s) + version hints
- Framework(s) + version
- Package manager
- Build tool
- State management (frontend)
- ORM / database (backend)
- CI/CD tool
- Containerization

### 1.2 Scan Directory Structure (1-2 levels deep)

```bash
ls -la  # root level
```

For each top-level directory that looks like a code module (not node_modules, .git, etc.):
```bash
ls <dir>/  # one level deeper
```

From this, identify:
- Module boundaries (frontend vs backend vs shared vs mobile vs infra)
- Monorepo structure (if applicable)
- Frontend/backend separation pattern

### 1.3 Sample Core Files (3-5 files)

Read these (pick the most informative):
- Main entry point (main.go, index.ts, app.py, App.tsx, etc.)
- Primary router/route definition file
- One data model / schema file
- One UI component (if frontend exists)
- One configuration/middleware file

From these, extract:
- Architecture pattern (MVC, Clean, Layered, Feature-sliced, etc.)
- Code style (naming conventions, file organization)
- State management approach
- API style (REST, GraphQL, gRPC)

### 1.4 Read README/Docs for Business Context

If README.md exists, read it for:
- Project purpose / business domain
- Core user flows described
- Technology decisions explained

### 1.5 Collect Target Information (Interactive)

Ask the user ONE combined question. Format depends on detected state (from Step 1.0):

**If code + artifacts exist (has_code + has_product_artifacts):**

```
检测到已有代码和 .allforai/ 产物。请确认目标（可多选）：

   a) 逆向分析（重新生成 .allforai/ 产物）
   b) 跨栈复刻（翻译到目标技术栈）
   c) 同栈重建（按目标架构重新生成）
   e) 代码治理（架构合规 + 重复检测 + 抽象分析）
   f) 演示数据（生成 demo-ready 数据集）
   g) UI 精修（UI 还原度修复）
   h) 功能验收（静态 + 全模块 E2E 动态验证）
   i) 视觉验收（截图对比）
   j) 质量检查（死链 + 字段一致性）
```

**If code exists but no artifacts (has_code, no has_product_artifacts):**

```
Bootstrap 分析完成。请确认目标（可多选）：

   a) 逆向分析（生成 .allforai/ 产物，理解业务）
   b) 跨栈复刻（分析 + 翻译到目标技术栈）
   c) 同栈重建（分析 + 按目标架构重新生成）
   e) 代码治理（架构合规 + 重复检测 + 抽象分析）

目标技术栈（仅 b/c 需回答）：
   前端：___
   后端：___

UI 还原度（仅有前端翻译时）：
   a) faithful — 像素级还原
   b) native — 允许平台风格差异
```

**If no code exists (empty project or only README):**

```
当前目录没有检测到已有代码。请确认目标：

1. 目标：
   d) 从零构建新产品

2. 产品愿景（一句话描述你要做什么）：
   ___

3. 目标技术栈：
   前端：___
   后端：___
   移动端：___（如有）

4. 业务领域：
   a) 电商  b) 金融  c) 医疗  d) SaaS  e) 社交  f) 游戏  g) 其他：___
```

**Goal mapping (can combine multiple):**
- (a) → `goals: ["analyze"]`
- (b) → `goals: ["analyze", "translate", "demo", "concept-acceptance"]`, record target_stacks. demo-forge is auto-included because translate produces code that needs integration testing. concept-acceptance is auto-included when product-concept.json exists.
- (c) → `goals: ["analyze", "rebuild", "demo", "concept-acceptance"]`, record target_stacks. demo-forge is auto-included because rebuild produces code that needs integration testing. concept-acceptance is auto-included when product-concept.json exists.
- (d) → `goals: ["create", "demo", "concept-acceptance"]`, record target_stacks + product_vision. demo-forge is auto-included because new code needs integration testing. concept-acceptance is auto-included when product-concept.json exists.
- (e) → `goals: ["tune"]`
- (f) → `goals: ["demo"]`
- (g) → `goals: ["ui-forge"]`
- (h) → `goals: ["product-verify"]`
- (i) → `goals: ["visual-verify"]`
- (j) → `goals: ["quality-checks"]`
- Combinations: user can select e.g. "a + e" or "h + i + j" (full verification suite)
- **demo-forge is automatically added** to any goal that includes code implementation (translate/rebuild/create). Reason: API-driven data population is the strongest integration test — it exposes runtime issues that compile-verify cannot catch (wrong routes, missing fields, broken relationships, auth failures).
- **concept-acceptance is automatically added** to any goal that includes code implementation (translate/rebuild/create) AND `has_product_concept` is true. Reason: without verifying the final product experience against the original concept, the development loop never closes — product-verify checks code vs design artifacts, but not experience vs concept.

### 1.5.1 Runtime Environment Awareness (when goals include code implementation)

When goals include translate/rebuild/create (b/c/d), demo-forge will run and needs a live
environment. Bootstrap does NOT collect env details here — that is the job of a generated
node-spec.

**What bootstrap does in this step:**

1. Note that goals require runtime environment
2. In Step 3 (Plan Workflow), if the project needs runtime environment setup (databases,
   caches, AI services, storage, auth, etc.), LLM should include a runtime environment
   setup node as an **early node before any code execution** (before demo-forge, before
   any service startup). The node name should be project-specific (e.g.,
   `setup-env-go-pg-redis`, `configure-aws-services`).
3. The runtime environment node-spec is **project-specific** — LLM generates it based on
   Step 1.1-1.4 analysis (detected databases, caches, AI services, storage, auth, etc.)

**What the generated runtime environment node does (at /run time):**

1. Read `.env.example`, `docker-compose.yml`, config files to identify all required env vars
2. Check what's already configured (`.env` exists? docker-compose covers it? service reachable?)
3. Ask the user for ONLY missing items (project-specific, not a fixed template)
4. Write/update `.env`, verify services are reachable
5. Record runtime state in `.allforai/bootstrap/runtime-env.json`

**Why a node, not a bootstrap step?**
- Bootstrap is a template — it doesn't know project-specific env vars
- The node-spec is generated by LLM after analyzing the project — it knows exactly what to ask
- The node runs at `/run` time with interactive access to the user
- If the user re-runs `/run` later, the node re-validates (env may have changed)

### 1.6 Output bootstrap-profile.json

Write to `.allforai/bootstrap/bootstrap-profile.json`:

```json
{
  "schema_version": "1.0",
  "project_name": "<from directory name or package.json name>",
  "business_domain": "<inferred: ecommerce/fintech/healthcare/saas/social/gaming/...>",
  "business_context": "<1-2 sentence description of what this project does>",
  "tech_stacks": [
    {
      "role": "frontend | backend | mobile | shared",
      "language": "<language>",
      "language_version": "<version if detectable>",
      "framework": "<framework name + version>",
      "state_management": "<if applicable>",
      "router": "<if applicable>",
      "orm": "<if applicable>",
      "db": "<if applicable>",
      "build_tool": "<vite/webpack/go build/cargo/...>"
    }
  ],
  "goals": ["analyze | translate | rebuild | create | tune | demo | ui-forge"],
  "product_vision": "<one sentence, only for goals includes create>",
  "target_stacks": [
    {
      "role": "frontend | backend | mobile",
      "language": "<target language>",
      "framework": "<target framework>"
    }
  ],
  "ui_fidelity": "faithful | native | null",
  "modules": [
    {
      "id": "M001",
      "path": "<relative path>",
      "role": "frontend | backend | shared | mobile | infra",
      "description": "<what this module contains>"
    }
  ],
  "build_commands": {
    "<role>": "<build command>"
  },
  "test_commands": {
    "<role>": "<test command>"
  },
  "detected_patterns": ["<REST API>", "<JWT auth>", "<Redis cache>", "..."],
  "architecture_pattern": "<MVC/Clean/Layered/Feature-sliced/...>",
  "complexity_estimate": "low | medium | high",
  "requires_runtime_env": true
}
}
```

---

## Step 2: Load Knowledge (Reference, Not Menu)

> Goal: Absorb all available knowledge before planning.
> Capabilities are REFERENCE material — LLM reads them for methodology
> guidance, NOT as a list of nodes to select from.

### 2.1 Load All Capabilities

Read all files in `${CLAUDE_PLUGIN_ROOT}/knowledge/capabilities/*.md`.
These describe WHAT each type of work involves and WHAT methodology to apply.
They are NOT a menu — LLM will freely design nodes that may combine, split,
skip, or go beyond what any single capability describes.

### 2.2 Load Domain Knowledge

Check if `${CLAUDE_PLUGIN_ROOT}/knowledge/domains/<domain>.md` matches the
detected business_domain. If yes, load it — it contains domain-specific
design stages, theory anchors, and output artifacts that override or
supplement standard capabilities.

### 2.3 Load Cross-Phase Knowledge

Always load these (they apply to ALL nodes regardless of type):
- `${CLAUDE_PLUGIN_ROOT}/knowledge/cross-phase-protocols.md`
- `${CLAUDE_PLUGIN_ROOT}/knowledge/defensive-patterns.md`
- `${CLAUDE_PLUGIN_ROOT}/knowledge/product-design-theory.md`

### 2.4 Load Tech Stack Mappings (if translating)

Check if `${CLAUDE_PLUGIN_ROOT}/knowledge/mappings/<source>-<target>.md` exists.
Also check `${CLAUDE_PLUGIN_ROOT}/knowledge/learned/` and
`.allforai/bootstrap/learned/` for prior experience.

### 2.5 Load Iteration Feedback (if re-bootstrapping)

If `has_iteration_feedback` (from Step 1.0):

Read `.allforai/product-concept/iteration-feedback.json`. This contains:
- Previous concept-acceptance score and verdict
- Gaps found in the last iteration
- Recommended actions (fix_gap, simplify_flow, reconsider_concept, deprioritize)
- User decisions from re-bootstrap

LLM uses this in Step 3 to:
- Prioritize nodes that address previous gaps
- Avoid repeating the same planning mistakes
- If user made decisions (e.g., "move social sharing to post-launch"), respect them

If `user_decisions` is empty but `recommended_actions` exists, LLM infers decisions
by comparing the current `product-concept.json` against the previous iteration's gaps:
- Feature removed from concept → user decided to deprioritize
- Feature moved to post_launch → user decided to defer
- Feature still in must_have → user wants it fixed
Record inferred decisions in `iteration-feedback.json` → `user_decisions[]` for audit.

If `has_product_concept` (from Step 1.0):

Read `.allforai/product-concept/product-concept.json`. This is needed for Step 3.5 Coverage Self-Check.

### 2.6 Load Decision Journal (if exists)

Check if `.allforai/product-concept/decision-journal.json` exists. If yes, read it.

This file contains product decisions made during previous development sessions,
recorded via the `/journal` command. Each batch has a timestamp, topic, and
list of decisions with question/chosen/rationale.

LLM uses this in Step 3 to:
- **Respect previous decisions**: if user decided "login: email + Apple + Google, no WeChat",
  do not plan a WeChat login node
- **Detect conflicts**: if a decision contradicts the product-map, flag it (the decision
  is newer and likely correct — suggest updating the product-map)
- **Avoid re-asking**: if a question was already answered in the journal, don't ask again
  in Step 1.5

The journal is append-only. Later batches can supersede earlier ones (check `supersedes` field).
When decisions conflict, the latest batch wins.

> **After Step 2, do NOT ask the user anything.** Proceed to planning.

---

## Step 3: Plan Workflow (LLM Free Planning)

> Goal: Design a project-specific workflow. NOT selecting from templates.
> LLM has absorbed all knowledge in Step 2. Now freely plan what nodes
> this specific project needs.

### 3.0 Incremental Re-Planning (when concept-drift exists)

> This section only applies when `has_concept_drift` is true AND an existing
> `workflow.json` exists. Otherwise, skip to 3.1 for full planning.

When concept has drifted since last bootstrap:

1. Read `.allforai/product-concept/concept-drift.json` → changes[]
2. Read existing `.allforai/bootstrap/workflow.json` → nodes[] + transition_log[]
3. For each change, determine affected nodes:

| Change Type | Node Action |
|-------------|-------------|
| feature_removed | Remove nodes whose goal is primarily about this feature. Add a `cleanup-{feature}` node if code already exists (detected from transition_log). |
| feature_added | Add new implementation + verification nodes for the feature. |
| feature_modified | Update affected nodes' goal and regenerate their node-specs. |
| role_removed | Remove role-specific nodes (e.g., e2e-test for that role's app). Update shared nodes to exclude this role. |
| tech_changed | Replace implementation + compile-verify + e2e nodes for the affected module with new tech stack equivalents. |
| client_removed | Remove the implementation + compile-verify + e2e triplet for that client. If the role becomes single-client, Level 3 parity check no longer applies. |
| client_added | Add implementation + compile-verify + e2e triplet for the new client. Trigger Level 3 parity check. |
| module_merged | Remove nodes for merged services. Extend the target service node's goal to absorb merged functionality. |
| module_split | Create new service nodes for the split-out module. Reduce the source service node's goal. |

4. **Preserve unaffected nodes**: nodes whose goal does not relate to any drift change
   remain in workflow.json with their transition_log entries intact. Completed work is not lost.
   **Cross-change dependencies**: a tech_changed may also affect infrastructure nodes
   (e.g., Flutter→SwiftUI means FCM push is no longer needed, only APNs). LLM must
   trace second-order effects of each change on ALL nodes, not just the obvious ones.

5. **Handle affected completed nodes**:
   - Node removed → transition_log entry stays for audit, but node removed from nodes[]
   - Node goal modified → clear its transition_log entry (needs re-execution)
   - New node added → no transition_log entry yet

6. Write updated workflow.json with modified nodes[] and preserved transition_log[].
7. Regenerate node-specs for all affected nodes at `.allforai/bootstrap/node-specs/`.
8. Proceed to Step 3.5 (Coverage Self-Check) — concept has changed, coverage must be re-verified.
9. After Step 3.5 completes, mark drift as resolved:
   read concept-drift.json, set `"resolved": true`, write back.

**After incremental re-planning, skip 3.1-3.3** (they are for full planning) and go directly
to Step 3.4 (Confirm with User) → Step 3.5 (Coverage Self-Check) → Step 4.

### 3.1 Design the Node Graph

Based on project analysis (Step 1) + absorbed knowledge (Step 2), design
a set of nodes that will achieve the user's goal. Consider:

- What needs to happen? (understand code, design product, write code, verify, populate data...)
- What order makes sense for THIS project?
- What can run in parallel?
- What can be skipped or merged?

**There is no fixed template.** A game project might have nodes for
"design-economy-system" and "balance-test-combat". An SDK project might
have "design-api-surface" and "write-getting-started-guide". A consumer
app might have "design-onboarding-flow" and "setup-push-notifications".

**Node granularity is project-dependent.** A simple CLI tool might need
3 nodes. A microservice platform might need 20. LLM decides.

**Cross-Module Consistency Check (MANDATORY for rebuild/translate goals):**
When goals include rebuild or translate, LLM MUST check EVERY module in
`bootstrap-profile.json.modules[]` against the product definition (product-map
artifacts, README, or product vision). For each module, answer:

1. Does this module's code reflect the current product direction?
2. Does it implement the entities/flows defined in the product-map?
3. Is it consistent with other modules that have already been rebuilt?

If a module is **stale or inconsistent** (e.g., API has new features but
mobile still has old UI), it MUST get an **implementation node** before any
verification node. Verification without implementation is useless — it only
proves that outdated code runs, not that the product works.

**Implementation-before-Verification Rule:**
For each module, nodes must follow this order:
```
implement (if needed) → demo/seed (if applicable) → verify
```
A verification node for a module without a corresponding implementation node
is only valid if the module's code is already up-to-date with the product
definition. If the code is stale, plan the implementation node first.

Checklist (LLM must iterate before finalizing workflow):
```
For each module in bootstrap-profile.json.modules[]:
  □ Is code consistent with product-map? → YES: verify only / NO: implement first
  □ Has implementation node (if needed)?
  □ Has verification node?
  □ Verification depends on implementation?
```

**Functional Pipeline Completeness Check (MANDATORY):**
After module-level checks, LLM MUST also check that cross-module functional
pipelines are complete end-to-end. A "pipeline" is a product flow that spans
multiple components (trigger → generation → storage → delivery → display).

Check method: Read `product-map/role-profiles.json` trigger_conditions[] and
`product-map/business-flows.json` flows[]. For each trigger/flow, trace the
full pipeline:

```
For each trigger_condition or async business flow:
  □ Trigger source exists? (cron job / event handler / user action)
  □ Generation logic exists? (service that creates the data)
  □ Storage exists? (DB table / queue)
  □ Delivery mechanism exists? (API endpoint / push notification / WebSocket)
  □ Client display exists? (UI that shows the result)
```

If any step in a pipeline is missing, the workflow MUST include a node to
implement it. Common gaps that LLM must watch for:

| Product Requirement | Often Missing | What to Check |
|-------------------|---------------|---------------|
| "Send X when Y happens" | Background scheduler/cron | Is there a goroutine/cron/worker that checks Y? |
| "Push notification" | APNs/FCM integration | Is there push infra in the codebase? |
| "Proactive messages" | Generation job | Endpoint exists to READ, but does anything WRITE? |
| "Daily/weekly summary" | Aggregation job | Is there a scheduled job that aggregates data? |
| "Real-time updates" | WebSocket/SSE | Is there a push channel, or only polling? |

Example: product-map says "SRS item due → send review card". Pipeline:
1. Trigger: cron job checks SRS due dates ← **missing if no scheduler**
2. Generate: create ProactiveMessage record ← **missing if only read endpoint**
3. Store: proactive_messages table ← exists
4. Deliver: GET /messages/pending ← exists (but only pull, no push)
5. Display: Front Desk UI ← exists
→ Workflow needs: "implement-background-scheduler" + "implement-push-notifications"

**Adaptive State Machine Check (MANDATORY):**
After pipeline checks, LLM MUST check for **adaptive state machines** defined
in the product-map. Products with personalization, learning, or recommendation
features have user states that evolve over time. The system must read the
current state to decide behavior, and update the state after each interaction.

This is NOT a linear pipeline check. It's a state machine check:

```
                    ┌─── event ───┐
                    ▼              │
    ┌──────────────────────┐      │
    │   User State         │      │
    │  ┌─ dimension_1: val │      │
    │  ├─ dimension_2: val │──────┘
    │  └─ dimension_3: val │  state determines
    └──────────────────────┘  system behavior
              │                     │
              ▼                     ▼
    ┌──────────────┐     ┌──────────────────┐
    │ Transition   │     │ Behavior Mapping │
    │ event + rule │     │ state → action   │
    │ → new state  │     │ (what AI does)   │
    └──────────────┘     └──────────────────┘
```

Check method: Read `product-map/task-inventory.json` tasks[]. For each task
that describes adaptive behavior (keywords: "based on", "adjust", "personalize",
"reinforce", "inject", "adapt", "track", "proficiency-based", "level"),
verify three things:

**1. State Definition — is the user state model complete?**
```
For each adaptive dimension in the product:
  □ Is there a DB table/field that holds this state?
  □ Does it store CURRENT value (for behavior decisions)?
  □ Does it store HISTORY (for trend/progress reporting)?
  □ Is the initial state defined (what value for new users)?
```

**2. State Transitions — do events update the state?**
```
For each user event that should change state:
  □ Is there code that runs AFTER the event to update state?
     (e.g., after conversation ends → update grammar_profiles, proficiency, streak)
  □ Is the transition rule correct? (not just increment — weighted, decayed, etc.)
  □ Does the transition handle edge cases? (first time, reset, regression)
```

**3. State→Behavior Mapping — does the system ACT on the state?**
```
For each adaptive behavior the product promises:
  □ Does the code READ the user state before deciding what to do?
     (e.g., conversation_service reads grammar_profiles before building prompt)
  □ Does the behavior CHANGE based on state values?
     (e.g., hint_mode=full vs keywords vs none produces different UI)
  □ Is the mapping granular enough? (not just on/off but graduated response)
```

If any of the three is incomplete, the "adaptive" feature is actually static.
The workflow MUST include implementation nodes to complete the state machine.

Common state machine gaps:

| Product Promise | State Definition | Transitions | Behavior Mapping |
|----------------|-----------------|-------------|------------------|
| "Adapt to user level" | proficiency table ✓ | **Missing**: no auto-update after conversation | hint UI exists but always shows same mode |
| "Reinforce weaknesses" | grammar_profiles ✓ | errors collected ✓ | **Missing**: not injected into Persona prompt |
| "Personalized recommendations" | **Missing**: no preference tracking | N/A | content list is same for all users |
| "Progress over time" | current snapshot only | **Missing**: no historical snapshots | cannot show "you improved this week" |
| "Intimacy-driven outreach" | intimacy table ✓ | level updates ✓ | **Missing**: no proactive message generation based on level |

Example — FlyDict learning state machine:
```
User Learning State:
  proficiency_level: beginner|intermediate|advanced
  weakness_profile: {grammar_category: mastery_score, ...}
  hint_mode: full_with_translation|keywords_only|none
  persona_familiarity: {persona_id: intimacy_level, ...}
  scene_coverage: {tag: practiced_count, ...}

Events that trigger transitions:
  conversation_end → update weakness_profile, proficiency, scene_coverage
  review_card_answer → update SRS schedule, weakness mastery
  growth_test_pass → upgrade proficiency_level, adjust hint_mode

State→Behavior mappings:
  weakness_profile → injected into Persona system prompt (top 3 weaknesses)
  hint_mode → determines flash card display style
  proficiency_level → determines hint duration, quiz difficulty
  scene_coverage → Coco recommends uncovered Persona tags
  persona_familiarity → Persona correction directness, topic depth
```

For each mapping, check: does the code path exist from state read → behavior change?
If a state exists in DB but nothing reads it to change behavior → broken mapping.
If behavior is supposed to adapt but always reads a hardcoded default → broken mapping.

### 3.2 Write workflow.json

```json
{
  "schema_version": "2.0",
  "project": "<project name>",
  "goal": "<user's goal>",
  "planned_at": "<ISO timestamp>",
  "nodes": [
    {
      "id": "<project-specific name>",
      "goal": "<one sentence: what this node achieves>",
      "exit_artifacts": ["<file paths that prove this node is done>"],
      "knowledge_refs": ["<which knowledge files this node should reference>"],
      "consumers": ["<node IDs that read this node's exit_artifacts>"]
    }
  ],
  "transition_log": []
}
```

**Node fields:**
- `id`: Project-specific. NOT from a fixed vocabulary.
- `goal`: One sentence. Clear enough that a subagent knows what to do.
- `exit_artifacts`: File paths. Node is complete when these files exist.
- `knowledge_refs`: Which knowledge files to inject into the node-spec.
- `consumers`: Which downstream nodes read this node's output. Used to generate
  the Downstream Contract section in the node-spec — tells the subagent "who
  will consume your output and what they need from it".

**No entry_requires.** The orchestrator's LLM decides execution order at runtime.

**exit_artifacts 路径规范（重要）：**
- 必须是**精确的项目相对路径**，从项目根目录开始
- ❌ `.env`（模糊——哪个目录的 .env？）
- ✅ `flydict-api/.env`（精确——明确是 API 子目录）
- ❌ `config.json`（模糊）
- ✅ `.allforai/bootstrap/migration-result.json`（精确）
- 对于 monorepo，路径必须包含子项目前缀
- 路径必须是执行 `check_artifacts.py` 时从项目根目录能找到的
- 生成 workflow.json 前，LLM 应检查项目目录结构确认路径正确

### 3.3 Pre-Generate Node-Specs

For each node in workflow.json, generate a complete node-spec markdown file
at `.allforai/bootstrap/node-specs/<id>.md`.

**Why pre-generate?** Saves execution-time attention. Bootstrap has the
fullest context (all knowledge loaded). Each subagent at /run time only
needs to read its own node-spec.

**Maximum Realism Principle (applies to ALL node-specs):**
When the user has provided real credentials (API keys, database connections, service URLs),
generated node-specs MUST instruct subagents to use the REAL service, not mocks/stubs.
Dev-mode code should check for real credentials and use them when available. Stubs are
ONLY acceptable when no credentials are provided. This ensures demo-forge and smoke-test
exercise the full real stack, not a fake one. Every stub is a gap in integration testing.

**Full E2E Testing Principle (applies to workflow planning):**
Every module in `bootstrap-profile.json.modules[]` MUST have a corresponding verification
node in the workflow. No module may be silently skipped. This is NOT optional.

**Coverage rule**: When planning nodes in Step 3.1, LLM MUST iterate over every module
in the bootstrap profile and ensure each has at least one verification node. If a module
has no verification node, the workflow is incomplete.

**Verification strategy per module role:**

| Module Role | Verification Tool | Node Pattern |
|-------------|------------------|--------------|
| backend (API) | curl / HTTP client | api-integration-test |
| frontend (web) | Playwright browser E2E | e2e-test-{name} |
| admin (web) | Playwright browser E2E | e2e-test-admin |
| mobile (Flutter) | `flutter test integration_test/` + `flutter build` | e2e-test-{name} |
| mobile (React Native) | `detox test` or Maestro | e2e-test-{name} |
| mobile (SwiftUI/Kotlin) | XCUITest / Espresso | e2e-test-{name} |
| shared / infra | covered by consumers' tests | no separate node needed |

**Why per-module nodes matter:**
- API-only testing (curl) misses: broken routing, missing UI components, CSS rendering,
  auth token flow in browser, client-side validation, CORS problems
- Web Playwright misses: native mobile layout, platform-specific gestures, offline behavior
- Each app is a separate deployment surface with its own failure modes
- A passing API test does NOT prove the mobile app works

**Each module's E2E node must:**
- Use the appropriate tool for that module's tech stack (see table above)
- Exercise core user flows end-to-end (login → navigate → CRUD → verify)
- Produce evidence (screenshots, test reports, logs)
- Report pass/fail per flow

**Node-spec format:**

```yaml
---
node: <id>
exit_artifacts:
  - <file path>
---
```

Followed by:

```markdown
# Task: <goal, expanded into a clear task description>

## Project Context
<From bootstrap-profile: tech stack, modules, architecture>

## Theory Anchors
<Classical frameworks for this work, from knowledge files>

## Knowledge References
<Relevant sections from cross-phase-protocols, defensive-patterns,
 domain knowledge, capability methodology — embedded, not just linked>

## Guidance
<LLM-generated execution guidance based on absorbed knowledge.
 NOT fixed steps — principles, goals, quality bars, methodology.>

## Exit Artifacts
<What files must exist when done, with expected content description>

## Downstream Contract
<Who consumes this node's output, and what they need from it.
 Generated from the consumers field in workflow.json.
 For each consumer node: which fields/sections of the artifact they read,
 and what format/depth they expect.>

Example:
  → design-loot-economy reads: mechanics[].name (weapon list), meta_loop.currencies
  → implement-combat-system reads: mechanics[].parameters (concrete numbers needed)
  → design-dungeon-generation reads: core_loop.steps (room encounter design)

## Integration Points
<Which OTHER parallel nodes produce components that THIS node must integrate.
 When nodes run in parallel, their outputs may need to connect at specific
 touchpoints. List each integration point explicitly so the subagent knows
 to leave hooks or import the sibling node's components.>

Example:
  ← implement-ios-learning produces: FlashHintOverlay.swift
    → THIS node's ChatView must: import and display FlashHintOverlay when
      user taps "hint" button, reading hint_full/hint_translation from
      Message.metadata
  ← implement-ios-learning produces: WordCardView.swift
    → THIS node's MessageBubble must: make tappable words trigger WordCardView
```

**Integration Points Rule (MANDATORY for parallel implementation nodes):**
When multiple implementation nodes run in parallel within the same module
(e.g., implement-ios-conversations + implement-ios-learning both produce
files inside flydict-ios/), the bootstrap MUST identify integration points
where their outputs need to connect.

For each product flow that spans multiple parallel nodes:
1. Trace the UI interaction path (e.g., user in ChatView taps word → WordCard)
2. Identify which node produces the trigger (ChatView) and which produces the
   target (WordCardView)
3. Add an Integration Points section to BOTH node-specs:
   - The trigger node: "must call/import X from sibling node Y"
   - The target node: "must expose X as a reusable component callable from Y"

If integration points are too complex for parallel execution, the nodes should
be sequenced instead (one depends on the other), or a dedicated integration
node should follow the parallel batch to wire everything together.

**Integration Stitch Node (MANDATORY after parallel implementation batch):**
When 2+ implementation nodes run in parallel within the same module, the
workflow MUST include a dedicated `stitch-{module}` node immediately after
the parallel batch completes, BEFORE compile-verify and E2E.

The stitch node's job:
1. Read all parallel nodes' exit artifacts (the files they created)
2. Read product-map business-flows to identify cross-component interactions
3. For each business flow, trace the UI path across files from different nodes
4. Detect disconnections: component A exists, component B exists, but A doesn't
   import/call B (or vice versa)
5. Fix each disconnection: add imports, wire up callbacks, connect data flow
6. Run compile check after fixes to ensure nothing broke
7. Produce a stitch report listing all connections made

```
Parallel impl nodes → stitch-{module} → compile-verify → E2E
                         ↑
                   Finds and fixes:
                   - Missing imports between sibling files
                   - UI triggers not wired to target components
                   - Data passed from API but not parsed by UI
                   - Callbacks/delegates not connected
                   - Navigation links pointing to placeholder instead of real view
```

The stitch node is lightweight (reads + patches, no new features) but catches
the integration gaps that parallel agents cannot see. It is the cheapest place
to catch these bugs — far cheaper than discovering them in E2E.

Exit artifact: `.allforai/bootstrap/stitch-{module}-report.json` with a list
of all connections made and any issues found.

**Node-spec for stitch nodes should include:**
- The list of parallel nodes whose outputs need stitching
- The product-map flows that cross node boundaries
- Specific integration points from the parallel nodes' specs
- Compile verification after all patches

**Enum Exhaustiveness Check (MANDATORY in stitch nodes):**
When the codebase defines an enum or type set (e.g., `SemanticType` with 13 values,
`ContentType` with 5 values, user roles, status codes, etc.), the stitch node MUST
verify that **every enum value has a code path in every consumer**.

```
For each enum/type set defined in the codebase:
  □ List all values (e.g., 13 semanticTypes)
  □ For each consumer of this enum:
    - API: is there code that GENERATES this value? (creation path)
    - Client: is there code that RENDERS this value? (display path)
    - E2E: is there a test that exercises this value? (test path)
  □ Any value missing a path in any consumer → gap to fix
```

This prevents the common failure pattern where a data model defines N types but
only M < N are actually handled downstream:
- API defines 13 semanticTypes → conversation_service only generates 3
- iOS MessageBubble switch has 5 cases → 8 fall through to default
- E2E tests only exercise "chat" messages → 12 types untested

The stitch node must produce a coverage matrix in its report:
```json
{
  "enum_coverage": {
    "SemanticType": {
      "total_values": 13,
      "api_generates": ["chat", "recast", "..."],
      "ios_renders": ["chat", "recast", "..."],
      "e2e_tests": ["chat"],
      "gaps": [
        {"value": "weekly_report", "missing_in": ["api", "e2e"]}
      ]
    }
  }
}
```

### 3.5 Coverage Self-Check (Concept → Workflow Closure)

> Goal: Verify that all features in product-concept.json are covered by at least one
> workflow node. Auto-fix gaps using Closure Thinking and Reverse Backfill convergence
> rules. Runs silently — no user confirmation needed.

**Trigger**: `has_product_concept` is true (from Step 1.0). If false, skip to Step 3.4 (Confirm with User).

#### 3.5.1 Extract Feature Inventory

From `.allforai/product-concept/product-concept.json`, extract all declared features.
Source fields vary by schema — LLM uses semantic understanding, not hardcoded paths:

- `features[]` (structured feature list)
- `errc_highlights.must_have[]` + `errc_highlights.differentiators[]`
- `mvp_features[]` + `post_launch_features[]`
- Any other field that declares "the product will do X"

Output: a flat list of feature descriptions, each a natural-language statement.

#### 3.5.2 Closure-Driven Coverage Check

For each feature, two levels of verification:

**Level 1 — Direct Coverage:**
Does at least one node's `goal`, `exit_artifacts`, or node-spec body semantically
cover this feature? This is LLM semantic judgment, not string matching.

**Level 2 — Closure Completeness (6 types from cross-phase-protocols.md §B.3):**

| Closure Type | Check |
|-------------|-------|
| Config Closure | Feature needs configuration → is there a node for config management? |
| Monitoring Closure | Feature needs observability → is there a node for monitoring setup? |
| Exception Closure | Feature has failure modes → are recovery paths covered by a node? |
| Lifecycle Closure | Feature creates entities → is there cleanup/archival in some node? |
| Mapping Closure | Feature has A↔B pair → is B covered? (e.g., create↔delete, buy↔refund) |
| Navigation Closure | Feature is an entry point → is there an exit path in some node? |

Closure checks are **discovery-level** (as defined in §B.6): identify and mark what
should exist, not exhaustive implementation-level checks.

**Level 3 — Multi-Client Parity (when roles have multiple clients):**

If any role in product-concept.json has `clients[]` (multi-client declaration) with
`feature_parity` = `full` or `partial`:

For each such role:
1. List all clients declared for this role
2. For each MVP feature accessible to this role:
   - Check if EVERY client has a corresponding implementation node
   - A feature "covered" by one client but missing on another = gap
3. For `partial` parity: skip features listed in `parity_exceptions`

Auto-fix for multi-client gaps:
- If a feature has an implementation node for client A but not client B →
  create or extend a node for client B
- Each client needs its own compile-verify and E2E node (different tech stacks
  require different build/test tools)

**Backward compatibility**: if a role has only `client_type` (single client, legacy format),
skip Level 3 for that role — Level 1 and 2 are sufficient.

Example gap detection:
```
R1 消费者 (feature_parity: full, 3 clients):
  "商品搜索":
    buyer-ios:     implement-buyer-ios ✓
    buyer-android: implement-buyer-android ✓
    buyer-web:     ??? ← GAP: no implementation node for web client
    → auto-fix: create implement-buyer-web node
```

#### 3.5.3 Convergence-Controlled Auto-Fix

When uncovered features or broken closures are found, LLM decides:

- **Extend existing node** — if the gap is closely related to an existing node's domain
  (same business area, same tech module). Update that node's `goal`, `exit_artifacts`,
  and node-spec.
- **Create new node** — if the gap is a distinct concern not covered by any existing node.
  Append to `workflow.json` nodes[] and generate new node-spec at
  `.allforai/bootstrap/node-specs/<new-id>.md`.

**Convergence rules (from cross-phase-protocols.md §E Reverse Backfill):**

1. **Concept Sets the Boundary** — Only fix gaps derivable from `product-concept.json`.
   Features not in the concept are out of scope.
2. **Derivation Radius Decreases** — Bootstrap only fixes Ring 0 (directly missing
   features) and Ring 1 (first-order closure gaps, e.g., "login" exists → "password
   recovery" missing). Ring 2+ is deferred to execution-phase Reverse Backfill.
3. **Layer Cutoff** — Bootstrap = product design phase boundary. Ring 2+ belongs to
   development phase.

**Stop conditions (any one triggers stop):**

| Condition | Meaning |
|-----------|---------|
| Zero output | All features covered, all closures checked, no new gaps found |
| All downgraded | All remaining gaps are Ring 2+ (beyond bootstrap scope) |
| Scale reversal | A "gap" item's scope exceeds its parent feature → not a gap, it's a new feature |

#### 3.5.4 Write Coverage Matrix

Write `.allforai/bootstrap/coverage-matrix.json`:

```json
{
  "source": "product-concept.json",
  "checked_at": "<ISO timestamp>",
  "total_features": 25,
  "covered_before_check": 22,
  "auto_fixed": 3,
  "closure_derived": 2,
  "deferred_ring2_plus": 1,
  "final_coverage_rate": "100%",
  "matrix": [
    {
      "feature": "<feature description>",
      "covered_by": ["<node-id>"],
      "status": "covered"
    },
    {
      "feature": "<feature description>",
      "closure_type": "exception",
      "derived_from": "<parent feature>",
      "ring": 1,
      "status": "auto_added",
      "action": "extended node <node-id>"
    },
    {
      "feature": "<feature description>",
      "ring": 2,
      "status": "deferred",
      "reason": "ring2_cutoff | scale_reversal | all_downgraded"
    }
  ]
}
```

### 3.4 Confirm with User

Present summary:

```
Bootstrap 完成。

项目：{project_name}
目标：{goal}
技术栈：{tech stacks}

规划了 {N} 个节点：
  {list each node id + goal}

确认正确吗？
```

User confirms → proceed to Step 4.

---

## Step 4: Generate run.md

Read `${CLAUDE_PLUGIN_ROOT}/knowledge/orchestrator-template.md` for the template.
Write the result to `.claude/commands/run.md` in the target project.

No customization needed beyond what the template provides — the orchestrator
reads workflow.json at runtime, which already contains all project-specific information.

---

## Step 5: Validate

Run:
```bash
python .allforai/bootstrap/scripts/validate_bootstrap.py .allforai/bootstrap/
```

If errors: fix and re-validate (max 3 attempts).

---

## Step 6: Write Files to Target Project

### 6.1 Create Directories (preserve learned/)

```bash
mkdir -p .claude/commands
mkdir -p .allforai/bootstrap/node-specs
mkdir -p .allforai/bootstrap/learned   # preserved across re-bootstrap
```

**Re-bootstrap behavior:**
If `.allforai/bootstrap/` already exists (previous run):
- **Preserve**: `.allforai/bootstrap/learned/` (project experience, never delete)
- **Overwrite**: everything else (workflow.json, node-specs/, scripts/, protocols/)
- This means re-bootstrap resets workflow progress but keeps learned experience

### 6.2 Copy Orchestrator Scripts

Copy scripts and protocol files to the target project so `/run` works independently:

```bash
mkdir -p .allforai/bootstrap/scripts
mkdir -p .allforai/bootstrap/protocols
cp ${CLAUDE_PLUGIN_ROOT}/scripts/orchestrator/check_artifacts.py .allforai/bootstrap/scripts/
cp ${CLAUDE_PLUGIN_ROOT}/scripts/orchestrator/validate_bootstrap.py .allforai/bootstrap/scripts/
cp ${CLAUDE_PLUGIN_ROOT}/knowledge/diagnosis.md .allforai/bootstrap/protocols/
cp ${CLAUDE_PLUGIN_ROOT}/knowledge/learning-protocol.md .allforai/bootstrap/protocols/
cp ${CLAUDE_PLUGIN_ROOT}/knowledge/feedback-protocol.md .allforai/bootstrap/protocols/
```

> **Why copy?** The meta-skill plugin is installed in Claude's plugin cache.
> The target project needs its own copy so `/run` works even if the plugin
> is uninstalled or updated. All run.md references use project-local paths.

### 6.3 Write Files

Write these files (they were generated in memory during Steps 3-5, now persist them):

1. `.allforai/bootstrap/bootstrap-profile.json`
2. `.allforai/bootstrap/workflow.json`
3. `.allforai/bootstrap/coverage-matrix.json` (from Step 3.5, only if product-concept.json exists)
4. `.allforai/bootstrap/node-specs/*.md`
5. `.claude/commands/run.md`
6. `.allforai/bootstrap/scripts/check_artifacts.py`
7. `.allforai/bootstrap/scripts/validate_bootstrap.py`
8. `.allforai/bootstrap/protocols/*.md`

### 6.4 Confirm Completion

```
Bootstrap 完成。

已写入 {count} 个文件：
  .allforai/bootstrap/bootstrap-profile.json
  .allforai/bootstrap/workflow.json
  .allforai/bootstrap/coverage-matrix.json (覆盖率: {coverage_rate})
  .allforai/bootstrap/node-specs/ ({node_count} 个节点)
  .claude/commands/run.md

现在可以使用 /run [目标] 执行工作流。例如：
  /run 逆向分析
  /run 复刻到 SwiftUI
  /run 代码治理
```

---

## Error Recovery

If bootstrap fails at any step:
- Steps 1-2 (analysis): Likely a file access issue. Check project path.
- Step 3 (generation): Retry with more context from source files.
- Step 4-5 (run.md/validation): Fix based on validation errors.
- Step 6 (file writing): Check directory permissions.

All intermediate products are in memory until Step 6.
If bootstrap is interrupted, nothing is written. Run `/bootstrap` again.
