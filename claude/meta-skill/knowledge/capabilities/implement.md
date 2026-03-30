# Implement Capability

> Capability reference for generating new code from .allforai/ artifacts (no source code).
> Bootstrap may create one or multiple nodes from this capability depending on project complexity.

## Purpose

Generate target platform code from .allforai/ artifacts when no source codebase exists.
This is the "from scratch" counterpart to translate (which reads source code).

## How It Differs from Translate

| Aspect | translate | implement |
|--------|----------|-----------|
| Input | Source code + artifacts | Artifacts only |
| Strategy | direct / adapt / rebuild per component | Always artifact-driven |
| Reference | Source code's architecture and patterns | ui-design-spec + experience-map behavior descriptions |
| Coverage check | Source→target route parity | Artifacts→code coverage (every task has code) |

## Protocol

### Step 0: Target Project Scaffold

Same as translate Step 0. Initialize target project per tech stack.
Scaffold is idempotent. Verify with build command before writing code.

### Step 1: Read Artifacts

Load the following from `.allforai/`:
- `product-map/task-inventory.json` — what operations each page/module supports
- `product-map/role-profiles.json` — who uses the system
- `product-map/business-flows.json` — end-to-end flows
- `experience-map/experience-map.json` — screens, states (empty/loading/error/success), interactions
- `ui-design/ui-design-spec.md` — visual spec, component hierarchy, design tokens
- `ui-design/tokens.json` — design tokens (colors, spacing, typography)
- `design-audit/audit-report.json` — cross-layer consistency (confirms artifacts are clean)

### Step 2: Module Planning

From bootstrap-profile.json modules:
1. Identify shared/foundation modules (models, utilities, API client) — implement first
2. Identify feature modules — implement after shared
3. Each module maps to a set of tasks from task-inventory

### Step 3: Per-Module Implementation

For each module:
1. Read relevant tasks from task-inventory
2. Read relevant screens from experience-map
3. Read relevant UI spec from ui-design-spec
4. Generate code (data models, API handlers, UI components, state management)
5. Compile immediately (compile self-loop, max 3 retries)
6. On 3 failures: classify as BLOCKED, record error, continue to next module

### Compile Self-Loop

```
implement -> write files -> compile -> pass? -> next module
                                    -> fail? -> feed error to LLM -> retry (max 3)
                                             -> exceeded? -> BLOCKED + continue
```

### Step 4: Coverage Check

After all modules implemented:
- Every task in task-inventory should have corresponding code
- Every screen in experience-map should have a corresponding view/page
- Missing items = coverage gaps → report as warnings

## Rules (Bootstrap Must Preserve)

1. **Artifacts are the spec**: Code must implement what artifacts describe, nothing more.
2. **Compile after every module**: Don't batch — catch errors early.
3. **Shared modules first**: Data models, API clients, utilities before feature modules.
4. **State variants mandatory**: Every screen must handle empty/loading/error/success.
5. **Design tokens binding**: Use tokens.json values, not hardcoded colors/spacing.
6. **Single LLM call = single module**: Match translate's "single target per call" discipline.
7. **Consumer-priority flag propagation**: If experience_priority = consumer | mixed, UI completeness bar is higher.
8. **Round-based checkpointing**: Persist build-log.json after each round.
9. **No invented features**: If it's not in the artifacts, don't add it.
10. **Coverage check at exit**: Verify every task and screen has code before marking complete.

## What Bootstrap Specializes

- Target tech stack scaffolding commands (framework init, dependency install)
- Module list and implementation order (from bootstrap-profile.json modules)
- Code style conventions (from target framework idioms)
- Design token consumption pattern (CSS variables / SwiftUI modifiers / Compose theme)
- API structure pattern (REST routes, GraphQL schema, gRPC proto — from artifacts)

## Composition Hints

### Split into Multiple Nodes (default)
Split per target platform: implement-web, implement-api, implement-ios.
For large projects: further split per feature domain (implement-web-orders, implement-web-chat).

### Single Node
Only for single-platform projects with a small codebase (< 20 tasks in task-inventory).

### Fan-Out
When one platform has many independent modules: use fan_out on bootstrap-profile.json modules.
Each subagent implements one module with the same protocol.

### Merge with Another Capability
For very simple projects: merge implement + compile-verify into a single node.
