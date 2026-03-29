---
name: bootstrap
description: >
  Internal skill for /bootstrap command. Performs lightweight project analysis,
  generates project-specific node-specs and state-machine.json, validates products,
  and writes to target project. Use when user runs /bootstrap.
---

# Bootstrap Protocol v0.1.0

## Overview

Bootstrap analyzes a target project and generates project-specific configurations:
- node-specs (one per workflow node, fully specialized)
- state-machine.json (node list + safety rules + progress tracking)
- .claude/commands/run.md (orchestrator entry point)

All generated products are written to the target project directory.
Products are disposable — regenerate anytime with `/bootstrap`.

---

## Step 1: Lightweight Analysis

> Goal: Understand the project enough to generate good node-specs.
> NOT a deep scan — just "what does this project look like?"

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

Ask the user ONE combined question covering:

1. **Goal**: What do you want to do? (analyze only / translate to another stack / both)
2. **Target tech stack** (if translating): What's the target? (e.g., "SwiftUI + Go Gin", "Flutter", "React Native")
3. **UI fidelity** (if translating frontend): faithful (pixel-match) or native (platform-idiomatic)?

Format as a single AskUserQuestion with multiple choice where possible:

```
Bootstrap 分析完成。请确认目标：

1. 目标：
   a) 仅分析（生成 .allforai/ 产物，不生成代码）
   b) 跨栈复刻（分析 + 翻译到目标技术栈）
   c) 同栈重建（分析 + 按目标架构重新生成）

2. 目标技术栈（仅 b/c 需回答）：
   前端：___
   后端：___

3. UI 还原度（仅有前端翻译时）：
   a) faithful — 像素级还原
   b) native — 允许平台风格差异
```

If user chose (a), set `target_stacks: null` and skip translate/compile/test nodes.
If user chose (b) or (c), record target_stacks in bootstrap-profile.json.

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
  "goal": "analyze | translate | rebuild",
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
  "complexity_estimate": "low | medium | high"
}
```

---

## Step 2: Select Relevant Knowledge

Based on bootstrap-profile.json, load knowledge files:

### 2.1 Node Templates (always load all)

Read all files in `${CLAUDE_PLUGIN_ROOT}/knowledge/nodes/*.md`.
Each file's "What Bootstrap Specializes" section tells you what to customize.

### 2.2 Determine Which Nodes Are Needed

| Condition | Nodes to generate |
|-----------|-------------------|
| Any project | discovery-structure, discovery-runtime |
| Any project | product-analysis, generate-artifacts |
| Has target tech stack (cross-stack) | plan-dag, translate-*, compile-verify |
| Has frontend | visual-verify |
| Has tests | test-verify |
| User wants governance | tune-* |
| Has frontend + needs polish | ui-forge |
| Needs demo data | demo-forge |

If the user hasn't specified a target (just analysis, no translation), skip translate/compile/test nodes.

### 2.3 Tech Stack Mappings

Check if `${CLAUDE_PLUGIN_ROOT}/knowledge/mappings/<source>-<target>.md` exists for the detected stack pair. If yes, load it. If no, note that mappings will be LLM-generated (no preset).

Also check `${CLAUDE_PLUGIN_ROOT}/knowledge/learned/<source>-<target>.md` for prior experience.

### 2.4 Domain Knowledge

Check if `${CLAUDE_PLUGIN_ROOT}/knowledge/domains/<domain>.md` matches the detected business_domain. If yes, load it. If no, skip (LLM will infer domain patterns from code).

### 2.5 Safety Template

Read `${CLAUDE_PLUGIN_ROOT}/knowledge/safety.md` for default safety configuration.

> **After Step 2, do NOT ask the user anything yet.** Proceed to generation,
> then present the summary in Step 5.5 for confirmation.

---

## Step 3: Generate Node-Specs

For each node determined in Step 2.2, generate a project-specific node-spec file.

### Node-Spec Format

Every node-spec is a Markdown file with YAML frontmatter:

```yaml
---
node: <node-id>
entry_requires:
  - <require declaration using check_requires.py primitives>
exit_requires:
  - <require declaration using check_requires.py primitives>
---
```

Followed by a complete subagent instruction in Markdown.

### Require Declaration Primitives

Use these formats in entry_requires / exit_requires:

```yaml
# File existence
- file_exists: .allforai/product-map/task-inventory.json

# Shell command succeeds (exit code 0)
- command_succeeds: "npm run build 2>&1 | tail -1 | grep -q 'compiled successfully'"

# JSON numeric field >= threshold
- json_field_gte: [.allforai/product-map/task-inventory.json, "$.length", 1]

# JSON array length >= minimum
- json_array_length_gte: [.allforai/product-map/task-inventory.json, "$", 1]
```

**Use project-relative paths.** The orchestrator runs from the project root.

### Generation Process

For each node:

1. Read the corresponding knowledge template (`knowledge/nodes/<name>.md`)
2. Read the "What Bootstrap Specializes" section
3. For each item in that section, fill it with project-specific information from bootstrap-profile.json
4. If a mapping file was loaded (Step 2.3), embed the mapping table in translate node-specs
5. If a domain file was loaded (Step 2.4), embed domain hints in product-analysis node-spec
6. Write entry_requires based on what upstream nodes produce
7. Write exit_requires based on what this node must produce

### Node Dependency Chain (for entry/exit_requires)

```
discovery-structure
  exit: file-catalog.json, source-summary.json
    ↓
discovery-runtime
  entry: source-summary.json
  exit: infrastructure-profile.json
    ↓
product-analysis
  entry: source-summary.json
  exit: task-inventory.json, role-profiles.json, business-flows.json
    ↓
generate-artifacts
  entry: task-inventory.json
  exit: product-map.json, use-case-tree.json
    ↓
plan-dag (if translating)
  entry: product-map.json, source-summary.json
  exit: dag.json
    ↓
translate-frontend / translate-backend (parallel if both exist)
  entry: dag.json
  exit: target code compiles
    ↓
compile-verify
  entry: target code exists
  exit: full build succeeds
    ↓
test-verify
  entry: build succeeds
  exit: tests pass
    ↓
visual-verify (if frontend)
  entry: build succeeds, app runs
  exit: visual comparison passes
```

Tune, ui-forge, demo-forge are optional branches — entry_requires = build succeeds or artifacts exist.

### Node-Spec Body Structure

Each node-spec body should contain:

```markdown
# Task: <human-readable description>

## Project Context
<From bootstrap-profile: tech stack, modules, architecture pattern>

## Protocol
<From knowledge template: phases, steps, rules>
<Specialized with project-specific details>

## Scripts
<Which Python scripts to call, with exact paths and arguments>
<Paths relative to project root>

## Verification
<Exit criteria in human-readable form>

## Hints
<Project-specific tips from bootstrap analysis>
<e.g., "React components are in src/features/*/components/">
```

### Output Directory

Write generated node-specs to: `.allforai/bootstrap/node-specs/<node-id>.md`

Create the directory if it doesn't exist.

---

## Step 4: Generate state-machine.json

Build state-machine.json from the generated node-specs.

### 4.1 Collect Nodes

For each node-spec file in `.allforai/bootstrap/node-specs/`:
1. Parse YAML frontmatter
2. Extract: node (id), entry_requires, exit_requires
3. Read the body for description (first `# Task:` line) and hints

### 4.2 Build Node List

```json
{
  "schema_version": "1.0",
  "nodes": [
    {
      "id": "<from frontmatter node field>",
      "description": "<from # Task: line>",
      "entry_requires": ["<from frontmatter>"],
      "exit_requires": ["<from frontmatter>"],
      "hints": ["<from ## Hints section, one string per bullet>"],
      "output_files": ["<glob patterns of files this node writes>"]
    }
  ],
  "safety": {
    "loop_detection": { "warn_threshold": 3, "stop_threshold": 5 },
    "max_global_iterations": 30,
    "progress_monotonicity": {
      "check_interval": 5,
      "violation_action": "output current best + TODO list"
    },
    "max_concurrent_nodes": 3,
    "max_node_execution_time": 600
  },
  "progress": {
    "completed_nodes": [],
    "current_node": null,
    "iteration_count": 0,
    "node_summaries": {},
    "corrections_applied": [],
    "diagnosis_history": []
  }
}
```

### 4.3 Validate output_files Disjointness

For nodes that could run in parallel (e.g., translate-frontend + translate-backend),
verify their output_files globs don't overlap. If they do, add a note in the node
that they must run sequentially.

Write to: `.allforai/bootstrap/state-machine.json`

---

## Step 5: Generate .claude/commands/run.md

Generate the orchestrator command that users will invoke with `/run`.

Read `${CLAUDE_PLUGIN_ROOT}/knowledge/orchestrator-template.md` for the protocol structure.

The generated run.md should be a complete Claude Code command file:

````markdown
---
name: run
description: Execute the project-specific workflow orchestrator. Specify a goal like "逆向分析", "复刻到 SwiftUI", "代码治理", "视觉验收".
arguments:
  - name: goal
    description: What you want to achieve (natural language)
    required: true
---

# Orchestrator Protocol

You are the workflow orchestrator for this project.

## State File

Read `.allforai/bootstrap/state-machine.json` at the start of every iteration.
This is the ground truth — not your conversation history.

## Core Loop

```
loop:
  1. Read state-machine.json (nodes, safety, progress, node_summaries)
  2. Evaluate entry/exit_requires mechanically:
     Run: python <path-to-scripts>/check_requires.py .allforai/bootstrap/state-machine.json <node-id> --type exit --json
     for each completed node, and --type entry for candidate next nodes.
  3. Decide next node:
     - If only one node has entry_requires met and is not completed → go there
     - If multiple → choose based on goal description and dependency order
     - If current node exit not met → self-loop, retry, or diagnose
     - If failure → dispatch diagnosis subagent (see Diagnosis section)
  4. Update state-machine.json progress
  5. Dispatch subagent:
     Read the node-spec at .allforai/bootstrap/node-specs/<node-id>.md
     Dispatch Agent tool with the node-spec content as prompt
  6. Receive result (subagent returns JSON per response contract)
  7. Compress result to ≤500 char summary → write to state-machine.json node_summaries
  8. Safety checks:
     - Loop: hash(node_id + exit_requires results), sliding window 10, warn at 3, stop at 5
     - Progress: every 5 iterations, completed_nodes must have increased
  9. Back to 1
```

## Goal Matching

Match the user's goal description to target node(s):

| Goal pattern | Target |
|-------------|--------|
| 逆向分析, reverse engineer, analyze | generate-artifacts complete |
| 复刻, replicate, translate, migrate to X | compile-verify complete |
| 代码治理, tune, audit, quality | tune-* complete |
| 视觉验收, visual, screenshot | visual-verify complete |
| 测试验证, test, verify | test-verify complete |
| 产品分析, product analysis | product-analysis complete |
| 演示数据, demo | demo-forge complete |
| UI 精修, ui polish | ui-forge complete |

## Parallel Dispatch

If multiple nodes have entry_requires met and their output_files are disjoint,
dispatch them in parallel using multiple Agent tool calls in one message.
Max concurrent: {safety.max_concurrent_nodes}.

## Diagnosis Protocol

When a node fails (subagent returns status: "failure"):

1. Do NOT immediately retry or backtrack
2. Dispatch a diagnosis subagent with this prompt:

"You are diagnosing a workflow failure.
Failed node: <node-id>
Error: <error from subagent>
All node summaries: <from state-machine.json node_summaries>
All node exit_requires: <from state-machine.json nodes>

Tasks:
1. Root cause: trace from failed node to the earliest upstream gap
2. Impact chain: which intermediate nodes are affected
3. Same-class expansion: scan for similar gaps in other nodes/domains
4. Repair plan: ordered list of nodes to re-run with specific actions
5. Prevention: should any node-spec exit_requires be tightened?

Output JSON: { root_cause, impact_chain, gaps_found, repair_plan, prevention }"

3. Execute the repair plan from the diagnosis
4. Apply prevention rules (Edit node-spec files if needed)
5. Record in state-machine.json diagnosis_history

## Subagent Response Contract

All node subagents must return:
```json
{
  "status": "success | failure | needs_input",
  "summary": "≤500 chars",
  "artifacts_created": ["file paths"],
  "errors": ["descriptions"],
  "user_prompt": "only if needs_input"
}
```

## Termination

- Target node(s) exit_requires all met → report success + summary
- Safety stop triggered → output current progress + TODO list of remaining work
- User interrupts → save state (already in state-machine.json), can resume with /run

## Context Management

Each iteration, your context is:
- state-machine.json content (always re-read from file)
- Last 2-3 subagent results (in conversation)
- Last diagnosis result (if any)

Old subagent results are compressed to node_summaries. Don't rely on conversation history.
````

**Important:** Replace `<path-to-scripts>` with the actual path to `shared/scripts/orchestrator/` relative to the project root. Since the meta-skill plugin is installed in Claude's plugin cache, use an absolute path or document that the user needs the scripts available.

Write to: `{project}/.claude/commands/run.md`

---

## Step 5.5: Validate Generated Products

Before writing to the target project, validate everything.

### Layer 1: Structural Validation (automatic)

Run the validation script:
```bash
python <path-to-scripts>/validate_bootstrap.py .allforai/bootstrap/
```

This checks:
- All node-spec YAML frontmatter parseable
- Required fields present (node, entry_requires, exit_requires)
- state-machine.json schema valid (nodes non-empty, safety complete, schema_version)
- Graph connectivity (all nodes reachable from root)
- No dangerous commands in exit_requires

If validation fails:
- Read the error JSON output
- Fix the issues (re-generate affected node-specs or state-machine.json)
- Re-run validation
- Max 3 fix attempts, then present errors to user

### Layer 2: Build Command Verification (automatic)

For each build_command in bootstrap-profile.json:
```bash
<build_command>
```

Record exit codes. Failed commands = validation warnings (not blockers,
since the project may need setup first).

### Layer 3: User Confirmation (interactive)

Present a summary to the user:

```
Bootstrap 分析完成。

技术栈：{list each tech_stack with role + language + framework}
业务域：{business_domain} — {business_context}
架构：{architecture_pattern}

生成节点（{count} 个）：
  {list each node-id with one-line description}

{if mapping loaded} 映射：{source} → {target}（{mapping_file_name}）
{if no mapping} 映射：无预置映射，将由 LLM 推理生成

{if domain loaded} 领域知识：{domain_file_name}
{if no domain} 领域知识：无预置，将从代码推理

{if build_commands tested}
构建验证：
  {each command + result (pass/fail)}
{end if}

{if validation had warnings}
注意事项：
  {list warnings}
{end if}

确认这些配置正确吗？如有问题请指出。
```

**Handle user response:**
- User confirms → proceed to Step 6
- User points out issues → fix the specific issues, re-validate, re-present
- Max 3 rounds of correction

---

## Step 6: Write Files to Target Project

### 6.1 Create Directories

```bash
mkdir -p .claude/commands
mkdir -p .allforai/bootstrap/node-specs
```

### 6.2 Write Files

Write these files (they were generated in memory during Steps 3-5, now persist them):

1. `.allforai/bootstrap/bootstrap-profile.json` (from Step 1)
2. `.allforai/bootstrap/state-machine.json` (from Step 4)
3. `.allforai/bootstrap/node-specs/*.md` (from Step 3, one per node)
4. `.claude/commands/run.md` (from Step 5)

### 6.3 Confirm Completion

```
Bootstrap 完成。

已写入 {count} 个文件：
  .allforai/bootstrap/bootstrap-profile.json
  .allforai/bootstrap/state-machine.json
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
- Step 4-5 (state-machine/run.md): Fix based on validation errors.
- Step 5.5 (validation): Fix and re-validate (max 3 attempts).
- Step 6 (file writing): Check directory permissions.

All intermediate products are in memory until Step 6.
If bootstrap is interrupted, nothing is written. Run `/bootstrap` again.
