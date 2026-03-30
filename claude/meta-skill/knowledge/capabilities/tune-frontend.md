# Tune Frontend Capability

> Capability reference for frontend architecture governance: component duplication,
> state management consistency, style governance, dependency direction, bundle analysis.
> Bootstrap may create one or multiple nodes from this capability depending on project complexity.

## Purpose

Audit frontend code architecture quality. Parallel to tune (backend-only).
Not ui-forge (visual fidelity) — this is structural, not visual.

## How It Differs from Related Capabilities

| Capability | What it checks | Example finding |
|-----------|---------------|-----------------|
| tune | Backend architecture (layers, duplication, abstraction) | "Service A and B have 80% identical code" |
| tune-frontend | Frontend architecture (components, state, styles) | "ConfirmDialog and DeleteDialog are 90% identical" |
| ui-forge | Visual fidelity (pixels, spacing, colors vs design spec) | "Button corner radius is 4px, spec says 8px" |
| quality-checks | Cross-layer data consistency (field names, types) | "UI sends `userName` but API expects `user_name`" |

## Phases

### Phase 0: Frontend Profile

- Detect framework (React / Vue / Svelte / Angular / SwiftUI / Compose)
- Detect state management (Redux / Zustand / Pinia / Context / Combine / MobX)
- Detect styling approach (CSS Modules / Tailwind / styled-components / inline / SCSS)
- Detect component organization pattern (feature-sliced / atomic / flat / domain)
- Scan component inventory (count, average size, nesting depth)
- Output: tune-frontend-profile.json

### Phase 1: Component Duplication

- Scan all components for structural similarity
- >70% structural overlap = candidate duplicate
- Classify: exact duplicate / near duplicate (differs by props) / pattern duplicate (same layout, different data)
- For each candidate: propose merged component with configurable props
- Output: phase1-component-duplicates.json

### Phase 2: State Management Consistency

- Detect all state management patterns used across the project
- Flag mixed patterns (Redux in one page, Context in another, Zustand in a third)
- Check state granularity: global state holding page-local data = over-centralized
- Check prop drilling depth: >3 levels without Context/store = under-centralized
- Check derived state: computed values stored in state instead of derived = stale data risk
- Output: phase2-state-consistency.json

### Phase 3: Style Governance

- Scan for magic numbers (hardcoded px/color/opacity not from design tokens)
- Detect unused CSS/styles (defined but never applied)
- Check style deduplication (same color/spacing defined in multiple places)
- Verify design token usage (tokens.json exists → check if actually consumed)
- Detect inline style proliferation (>30% of components use inline styles = flag)
- Output: phase3-style-governance.json

### Phase 4: Dependency Direction

- Map component dependency graph
- Flag violations:
  - Atomic/shared component imports page-level or feature-level module
  - Component directly calls API (fetch/axios) instead of going through service/hook layer
  - Circular dependencies between feature modules
- Check import depth: component importing from >2 layers away = coupling smell
- Output: phase4-dependency-direction.json

### Phase 5: Bundle Analysis (if build tool detected)

- Run build and analyze output size
- Identify large dependencies (>100KB individual packages)
- Detect barrel file re-exports that break tree-shaking
- Check dynamic import opportunities (large pages not code-split)
- Output: phase5-bundle-analysis.json

### Phase 6: Synthesis

- 5D scoring: components(25%) + state(20%) + styles(20%) + dependencies(20%) + bundle(15%)
- Two modes (same as tune): pre-launch (aggressive) vs maintenance (conservative)
- Output: tune-frontend-report.md + tune-frontend-tasks.json

## Rules

1. **Frontend code only**: Backend/API code ignored.
2. **Understand-then-scan**: LLM reads project structure once, derives rules, then batch scans.
3. **No auto-refactoring**: Report + task list only. No code changes.
4. **Framework-aware**: Rules adapt to framework idioms (React hooks ≠ Vue composition API).
5. **Design tokens are authority**: If tokens.json exists, hardcoded values that deviate are violations.
6. **Pre-launch vs maintenance**: Each finding carries both aggressive and conservative variants.
7. **Skip Phase 5 if no build tool**: Bundle analysis requires Vite/Webpack/esbuild.

## What Bootstrap Specializes

- Frontend framework and version
- State management solution
- Styling approach
- Component directory structure pattern
- Design token file location (if exists)
- Build tool and config location

## Composition Hints

### Single Node (default)
For most frontend projects: one tune-frontend node runs all phases sequentially.

### Split into Multiple Nodes
For very large frontends (>200 components): split per phase
(tune-frontend-components, tune-frontend-state, tune-frontend-styles).

### Parallel with tune
tune (backend) and tune-frontend have disjoint output_files — run in parallel.

### Skip
Skip for backend-only projects, CLIs, data pipelines, or any project without a frontend.

### Merge with Another Capability
Rarely merged. Independent audit that runs after implementation is complete.
