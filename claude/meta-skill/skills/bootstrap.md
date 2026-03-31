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

This affects Step 1.5 options:
- has_product_artifacts + has_code → verification/demo/tune options are relevant
- has_bootstrap → offer to reuse or regenerate
- no code + no artifacts → only "create" option

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
   h) 功能验收（静态 + Playwright 动态验证）
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
- (b) → `goals: ["analyze", "translate", "demo"]`, record target_stacks. demo-forge is auto-included because translate produces code that needs integration testing.
- (c) → `goals: ["analyze", "rebuild", "demo"]`, record target_stacks. demo-forge is auto-included because rebuild produces code that needs integration testing.
- (d) → `goals: ["create", "demo"]`, record target_stacks + product_vision. demo-forge is auto-included because new code needs integration testing.
- (e) → `goals: ["tune"]`
- (f) → `goals: ["demo"]`
- (g) → `goals: ["ui-forge"]`
- (h) → `goals: ["product-verify"]`
- (i) → `goals: ["visual-verify"]`
- (j) → `goals: ["quality-checks"]`
- Combinations: user can select e.g. "a + e" or "h + i + j" (full verification suite)
- **demo-forge is automatically added** to any goal that includes code implementation (translate/rebuild/create). Reason: API-driven data population is the strongest integration test — it exposes runtime issues that compile-verify cannot catch (wrong routes, missing fields, broken relationships, auth failures).

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

> **After Step 2, do NOT ask the user anything.** Proceed to planning.

---

## Step 3: Plan Workflow (LLM Free Planning)

> Goal: Design a project-specific workflow. NOT selecting from templates.
> LLM has absorbed all knowledge in Step 2. Now freely plan what nodes
> this specific project needs.

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
If the project has ANY frontend (web, admin, mobile web view), the workflow MUST include
a Playwright-based E2E testing node. This is NOT optional and NOT a sub-step of smoke-test.
It is a first-class node in the workflow that LLM must plan during Step 3.1.
- API-only testing (curl) catches backend bugs but misses: broken routing, missing
  components, CSS rendering, auth token flow in browser, CORS, client-side validation
- The E2E node must: open frontend → login with seeded credentials → navigate core
  flows → create/edit/delete entities → take screenshots as evidence → report issues
- If project has multiple frontends (admin + mobile), each gets its own E2E node

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
3. `.allforai/bootstrap/node-specs/*.md`
4. `.claude/commands/run.md`
5. `.allforai/bootstrap/scripts/check_artifacts.py`
6. `.allforai/bootstrap/scripts/validate_bootstrap.py`
7. `.allforai/bootstrap/protocols/*.md`

### 6.4 Confirm Completion

```
Bootstrap 完成。

已写入 {count} 个文件：
  .allforai/bootstrap/bootstrap-profile.json
  .allforai/bootstrap/workflow.json
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
