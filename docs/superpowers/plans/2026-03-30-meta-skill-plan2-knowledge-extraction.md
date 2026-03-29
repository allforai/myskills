# Meta-Skill Plan 2: Knowledge Extraction

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Distill the core knowledge from 6 existing skills into `claude/meta-skill/knowledge/` templates that the bootstrap generator (Plan 3) can use to produce project-specific node-specs.

**Architecture:** Each knowledge file is a Markdown template containing the reusable protocol (phases, rules, patterns) stripped of tech-stack-specific details and linear pipeline ordering. The bootstrap generator will combine these templates with project-specific information to produce specialized node-specs.

**Tech Stack:** Markdown files only — no code, no tests. Verification is structural (files exist, sections present).

**Spec:** `docs/superpowers/specs/2026-03-29-meta-skill-architecture-design.md` Section 6 (Knowledge Base) + Section 8 (Extraction Table)

---

### Task 1: knowledge/nodes/discovery.md

**Files:**
- Create: `claude/meta-skill/knowledge/nodes/discovery.md`
- Source: `claude/code-replicate-skill/skills/code-replicate-core.md` (Phase 2), `claude/code-replicate-skill/docs/phase2/*.md`

Extract the Discovery protocol — how to scan and understand an existing project.

- [ ] **Step 1: Read source files**

Read these files to extract Discovery knowledge:
- `claude/code-replicate-skill/skills/code-replicate-core.md` lines 95-147 (Phase 2)
- `claude/code-replicate-skill/docs/phase2/stage-a-structure.md` (first 100 lines)
- `claude/code-replicate-skill/docs/phase2/stage-b-runtime.md` (first 100 lines)
- `claude/code-replicate-skill/docs/phase2/stage-c-resources.md` (first 50 lines)

- [ ] **Step 2: Write discovery.md**

Write `claude/meta-skill/knowledge/nodes/discovery.md` with this structure:

```markdown
# Discovery Node Template

> How to scan and understand an existing project. Used by bootstrap to generate
> project-specific discovery node-specs.

## Purpose

Scan source project to build a complete understanding: file structure, module boundaries,
tech stack, infrastructure, abstractions, cross-cutting concerns, visual assets.

## Phases

### Phase A: Structure Discovery

| Step | Output | What |
|------|--------|------|
| Scan root | discovery-profile.json | LLM reads root dir, generates module discovery rules |
| File scan | source-summary.json skeleton | Script scans files per discovery-profile |
| Key file reading | source-summary.json | LLM reads key_files per module, generates file cards |
| Coverage check | coverage report | Modules <50% coverage get supplementary header scans |
| Knowledge base | file-catalog.json + code-index.json | Aggregate file cards, build cross-reference index |
| Archetype | project_archetype | LLM identifies project core value type |

### Phase B: Runtime Foundation Discovery

| Step | Output | What |
|------|--------|------|
| Infrastructure | infrastructure-profile.json | Custom/proprietary components, substitution risk |
| Environment | env-inventory.json | Environment variable catalog |
| Third-party | third-party-services.json | External service dependencies |
| Cron | cron-inventory.json | Scheduled tasks |
| Error codes | error-catalog.json | Error code system |

### Phase C: Resource Discovery

| Step | Output | What |
|------|--------|------|
| Assets | asset-inventory.json | Frontend static resources |
| Seed data | seed-data-inventory.json | Backend base data |
| Abstractions | abstractions + cross_cutting | Reuse patterns + middleware/interceptors |
| Role-view matrix | role-view-matrix.json | Per-role UI differences |
| Interactions | interaction-recordings.json | End-to-end user journeys |
| Screenshots | visual/source/ | Multi-role screenshots + dynamic recordings |

### Phase D: Confirmation

User reviews discovery results. Last human interaction point before silent execution.

## Rules (Bootstrap Must Preserve)

1. **File coverage >= 50%** per module. Unread files get header scan (definition + method signatures).
2. **Quiz validation** per file card: 3-question self-check, re-read on inconsistency (max 2 retries).
3. **Infrastructure before business**: Phase B completes before Phase 3 generation.
4. **Config-as-code**: nginx.conf, routes.yaml, OpenAPI spec, rbac.yaml may contain business logic. Include in sources.
5. **Cannot-substitute flag**: Custom/proprietary infra components (encryption, custom protocols, native SDKs) must be flagged.
6. **Protocol structurization**: Custom protocols output protocol_spec (frame format + state machine + test vectors).
7. **Never skip files by name**: LLM cannot guess importance from filename. Sample-read first.
8. **code-index resident**: Phase 3 LLM calls load source-summary + code-index as global context.
9. **UI-driven closure**: Screenshots/recordings from Phase C feed into Phase 3 generation for completeness validation.

## Scripts Referenced

- `cr_discover.py --profile <discovery-profile>`: File scanning + module detection
- Output: source-summary.json, file-catalog.json, code-index.json

## What Bootstrap Specializes

When generating a project-specific discovery node-spec, bootstrap fills in:
- Module paths and boundaries (from bootstrap-profile.json)
- Which Phase B/C steps are relevant (backend-only projects skip assets/screenshots)
- Specific file patterns to scan (from detected tech stack)
- Coverage thresholds (may be adjusted per project complexity)
```

- [ ] **Step 3: Remove .gitkeep and commit**

```bash
rm claude/meta-skill/knowledge/nodes/.gitkeep
git add claude/meta-skill/knowledge/nodes/discovery.md
git commit -m "knowledge(nodes): discovery.md — project scanning protocol template"
```

---

### Task 2: knowledge/nodes/product-analysis.md

**Files:**
- Create: `claude/meta-skill/knowledge/nodes/product-analysis.md`
- Source: `claude/product-design-skill/SKILL.md`, product-design sub-skills

- [ ] **Step 1: Read source**

Read `claude/product-design-skill/SKILL.md` (full file).

- [ ] **Step 2: Write product-analysis.md**

```markdown
# Product Analysis Node Template

> How to analyze a project's business domain and produce product artifacts.
> Covers: product-map, journey-emotion, experience-map, use-cases.

## Purpose

Transform source code understanding into business-level artifacts: roles, tasks,
business flows, experience maps, use cases. These artifacts are consumed by
downstream nodes (generate-artifacts, translate, demo-forge).

## Sub-Phases

### Product Map
- Role identification (from auth/permission code)
- Task expansion (from handlers/routes/pages)
- Constraint extraction (from validation rules)
- Business flow construction (from service orchestration)
- Data model mapping (from ORM/schema definitions)

Output: role-profiles.json, task-inventory.json, business-flows.json, product-map.json

### Experience Map (if frontend exists)
- Screen inventory (from pages/routes)
- Component mapping (from UI components)
- State variants per screen (empty/loading/error/success)
- Interaction triggers (click/input/scroll/timer/remote-event)
- Global components (nav, toast, modal)

Output: experience-map.json

### Use Cases
- 4-layer tree: role -> functional area -> task -> use case
- Per task: 1 happy path + N exception flows + M boundary cases
- Given/When/Then format

Output: use-case-tree.json

## Rules (Bootstrap Must Preserve)

1. **experience_priority classification**: consumer (end-user facing) / admin (professional) / mixed. Drives maturity thresholds downstream.
2. **Closure validation**: From observed features, infer complementary operations (CRUD completeness, error states, validation).
3. **Product language**: Artifacts speak in business terms (roles, tasks, flows), not technical terms.
4. **Exception mapping**: Every screen has empty/error/permission states.
5. **Button-level exception flows**: Every operation has on_failure, validation_rules, exception_flows.
6. **Structured fields**: inputs/outputs/audit as objects (not simple arrays).
7. **Required downstream fields**: experience_priority, protection_level, audience_type, render_as must be generated.
8. **4D self-check**: Each generated fragment checked for conclusion/evidence/constraint/decision completeness.

## What Bootstrap Specializes

- Business domain context (from bootstrap-profile.json: ecommerce, fintech, healthcare...)
- Which sub-phases are relevant (backend-only skips experience-map)
- Domain-specific role templates (ecommerce: buyer/seller/admin; healthcare: patient/doctor/admin)
- Domain-specific flow patterns (ecommerce: browse->cart->order->pay->fulfill)
```

- [ ] **Step 3: Commit**

```bash
git add claude/meta-skill/knowledge/nodes/product-analysis.md
git commit -m "knowledge(nodes): product-analysis.md — business domain analysis template"
```

---

### Task 3: knowledge/nodes/generate-artifacts.md

**Files:**
- Create: `claude/meta-skill/knowledge/nodes/generate-artifacts.md`
- Source: `claude/code-replicate-skill/skills/code-replicate-core.md` (Phase 3)

- [ ] **Step 1: Read source**

Read `claude/code-replicate-skill/skills/code-replicate-core.md` lines 150-345 (Phase 3 + iron laws).

- [ ] **Step 2: Write generate-artifacts.md**

```markdown
# Generate Artifacts Node Template

> How to generate structured .allforai/ artifacts from source code analysis.
> Fragment-based: per-module generation -> script merge -> final products.

## Purpose

Transform discovery results (source-summary, file-catalog, code-index) into
standard .allforai/ artifacts that downstream nodes consume.

## Protocol

### Pre-step: Extraction Plan
LLM generates extraction-plan.json — project-specific rules for what to extract from which files.
Fields: role_sources, task_sources, flow_sources, screen_sources, usecase_sources,
constraint_sources, cross_cutting, abstraction_sources, asset_sources, dependency_map.

LLM also determines artifact list via `artifacts[]` field — standard web apps produce
task-inventory + flows + roles; game servers produce system-spec + config-schema; etc.

### Per-Artifact Execution
For each artifact in extraction-plan.artifacts:
1. LLM reads sources (per extraction-plan)
2. Generates per-module JSON fragments
3. UI closure validation (compare with screenshots/API logs from discovery)
4. 4D self-check (conclusion/evidence/constraint/decision)
5. Merge script aggregates fragments -> final artifact

### Completeness Sweep (final step)
- Dimension A: Source coverage — iterate all source files, check covered/uncovered
- Dimension B: User experience — walk each role's journeys, verify screens/endpoints/states
- Reconcile: late-discovered items tagged `"source": "sweep"`

## Fragment Model

```
fragments/{roles,tasks,flows,screens,usecases,constraints}/
  M001.json, M002.json, ...  (per-module)
```

Merge scripts: cr_merge_roles.py, cr_merge_tasks.py, cr_merge_flows.py, etc.
Merge handles: deduplication by (name, owner_role), sequential ID assignment, case-insensitive matching.

## Rules (Bootstrap Must Preserve)

1. **Extraction-plan drives generation**: Every step follows plan's file specs, not framework templates.
2. **Single LLM call = single target**: One artifact type, one module per call.
3. **Scripts merge, not LLM**: LLM generates fragments, scripts handle cross-module merge + ID assignment.
4. **LLM semantic judgment first**: protection_level, audience_type, render_as from LLM understanding, not keyword matching.
5. **Business intent only**: Extract "what it does", not "how it's implemented".
6. **Abstraction transfer**: High-reuse source patterns must map to target equivalents via stack-mapping.
7. **UI-driven closure**: Compare fragments with screenshots to verify completeness.
8. **4D self-check per fragment**: Fix issues before merge, don't wait for Phase 4.

## Scripts Referenced

- cr_merge_roles.py, cr_merge_tasks.py, cr_merge_flows.py, cr_merge_screens.py
- cr_merge_usecases.py, cr_merge_constraints.py
- cr_gen_indexes.py, cr_gen_product_map.py
- cr_validate.py (schema validation)

## What Bootstrap Specializes

- Which artifacts to generate (based on project archetype from discovery)
- Specific extraction-plan sources (from discovered module structure)
- Which merge scripts are relevant
- Custom artifact schemas for non-standard projects
```

- [ ] **Step 3: Commit**

```bash
git add claude/meta-skill/knowledge/nodes/generate-artifacts.md
git commit -m "knowledge(nodes): generate-artifacts.md — fragment-based artifact generation template"
```

---

### Task 4: knowledge/nodes/translate.md + compile-verify.md + test-verify.md

**Files:**
- Create: `claude/meta-skill/knowledge/nodes/translate.md`
- Create: `claude/meta-skill/knowledge/nodes/compile-verify.md`
- Create: `claude/meta-skill/knowledge/nodes/test-verify.md`
- Source: `claude/dev-forge-skill/SKILL.md` (design-to-spec, task-execute), `claude/code-replicate-skill/skills/cr-fidelity.md`

- [ ] **Step 1: Read sources**

Read:
- `claude/dev-forge-skill/SKILL.md` (task-execute section)
- `claude/code-replicate-skill/skills/cr-fidelity.md` lines 1-80

- [ ] **Step 2: Write translate.md**

```markdown
# Translate Node Template

> How to translate source code to target tech stack. Three strategies based on
> component complexity: direct_translate, translate_with_adapt, intent_rebuild.

## Purpose

Generate target platform code from source code + .allforai/ artifacts.
Strategy selection per component, compile-verify loop per module.

## Strategy Selection

| Complexity | Strategy | LLM Input | Output |
|-----------|----------|-----------|--------|
| low (pure UI, no logic) | direct_translate | Source code + mapping table | Syntax-converted code |
| medium (stateful, controllable logic) | translate_with_adapt | Source code + target platform patterns | Translated + restructured state/navigation |
| high (complex business, cross-module) | intent_rebuild | .allforai/ artifacts (not source code) | Native target code from business intent |

## Protocol

### DAG Planning
1. Topological sort components by dependency
2. Identify parallel groups (independent components)
3. Critical path calculation

### Per-Component Translation
1. Select strategy based on complexity rating
2. Load appropriate context (source code or artifacts)
3. Load mapping table (from node-spec, project-specific)
4. Generate target code
5. Compile immediately (compile-verify loop)
6. On failure: feed error back, retry (max 3)

### Compile Self-Loop
```
translate -> write files -> compile -> pass? -> next component
                                    -> fail? -> feed error to LLM -> retry (max 3)
                                             -> exceeded? -> per error_strategy (skip-and-log or fail-fast)
```

## Rules (Bootstrap Must Preserve)

1. **Mapping table is project-specific**: Generated by bootstrap from knowledge/mappings/ + learned/.
2. **Compile after every component**: Don't batch — catch errors early.
3. **intent_rebuild reads artifacts, not source**: Prevents copying technical debt.
4. **TODO(migration) for unmappable items**: Code comment, not silent skip.
5. **Abstraction preservation**: Don't expand shared base classes into N copies.

## What Bootstrap Specializes

- Complete mapping table (source framework -> target framework)
- Compile/build commands
- Component complexity ratings (from discovery)
- Error strategy preference (skip-and-log vs fail-fast)
- DAG order (from dependency graph)
```

- [ ] **Step 3: Write compile-verify.md**

```markdown
# Compile Verify Node Template

> Verify that translated code compiles and builds successfully.

## Purpose

Full build verification after all translation is complete.
Distinct from per-component compile loops in translate — this is the final gate.

## Protocol

1. Run full build command(s)
2. Capture exit code + error output
3. On failure: categorize errors, feed back to translate node for targeted fixes
4. On success: mark node complete

## Rules

1. **Build commands from node-spec**: Not hardcoded. Bootstrap generates them.
2. **Full build, not incremental**: Catches cross-component integration issues.
3. **Error categorization**: Syntax vs missing dependency vs type mismatch — affects which node to revisit.

## What Bootstrap Specializes

- Exact build commands per platform (frontend, backend, mobile)
- Expected success output patterns
- Known build quirks for this tech stack
```

- [ ] **Step 4: Write test-verify.md**

```markdown
# Test Verify Node Template

> Verify that translated code passes tests.

## Purpose

Run test suites against translated code. Combines existing source tests
(adapted) and new tests generated during translation.

## Protocol

1. Run test command(s)
2. Capture results (pass/fail counts, error details)
3. On failure: categorize (logic error vs missing mock vs integration issue)
4. Feed failures back to translate or compile-verify as appropriate

## Verification Layers (from cr-fidelity)

| Layer | What | How |
|-------|------|-----|
| R1: Build | Code compiles | Build command |
| R2: Smoke | App starts | Launch + health check |
| R3: Test vectors | Known input->output | Execute extracted test vectors |
| R4: Protocol compat | Custom protocol behavior | Protocol-specific test suite |

Composite score = static * 0.5 + runtime * 0.5. Build failure = everything fails.

## Rules

1. **Test commands from node-spec**: Bootstrap generates them.
2. **R1 (build) is prerequisite**: Don't run tests if build fails.
3. **Adaptive dimensions**: LLM evaluates which verification layers apply per project.
4. **No silent skip**: Each verification layer must be explicitly evaluated with reasoning.

## What Bootstrap Specializes

- Test commands per platform
- Which verification layers apply
- Test vector file locations
- Expected pass thresholds
```

- [ ] **Step 5: Commit**

```bash
git add claude/meta-skill/knowledge/nodes/translate.md claude/meta-skill/knowledge/nodes/compile-verify.md claude/meta-skill/knowledge/nodes/test-verify.md
git commit -m "knowledge(nodes): translate + compile-verify + test-verify templates"
```

---

### Task 5: knowledge/nodes/visual-verify.md + tune.md + ui-forge.md + demo-forge.md

**Files:**
- Create: `claude/meta-skill/knowledge/nodes/visual-verify.md`
- Create: `claude/meta-skill/knowledge/nodes/tune.md`
- Create: `claude/meta-skill/knowledge/nodes/ui-forge.md`
- Create: `claude/meta-skill/knowledge/nodes/demo-forge.md`
- Source: cr-visual.md, code-tuner SKILL.md, ui-forge SKILL.md, demo-forge SKILL.md

- [ ] **Step 1: Read sources**

Read first 80 lines of each source SKILL.md.

- [ ] **Step 2: Write visual-verify.md**

```markdown
# Visual Verify Node Template

> Screenshot-based UI comparison between source and target apps.

## Purpose

Capture screenshots of source and target apps, compare per-screen,
identify layout/style/content discrepancies, fix in repair loop.

## Sub-Agent Architecture

- capture agent: screenshot collection (source + target)
- structural agent: layout/style comparison per screen
- data-integrity agent: data content verification
- linkage agent: navigation/link validation
- report agent: scoring + report generation
- repair agent: code fixes for visual discrepancies

## Protocol

1. Capture: source + target screenshots per screen per role
2. Plan: enumerate comparison subtasks
3. Execute: parallel per-screen (structural + data + linkage)
4. Report: aggregate scores
5. Repair loop: fix -> re-capture -> re-compare (max 30 rounds)

## Rules

1. **Real screenshots only**: No DOM manipulation for state setup. ViewModel calls OK, direct DOM changes forbidden.
2. **Platform adaptation exclusion**: Differences matching stack-mapping.platform_adaptation are not_a_gap.
3. **Multi-role**: role-view-matrix.json triggers per-role comparison.
4. **5-layer validation**: Static page, CRUD states, dynamic effects, API logs, composite milestones.
5. **Data injection tiers**: User interaction > ViewModel call > Network mock > UNREACHABLE.

## What Bootstrap Specializes

- Screenshot capture method per platform (XCUITest, Espresso, Playwright)
- App startup commands + URLs
- Role credentials for multi-role screenshots
- Platform adaptation rules from stack-mapping
```

- [ ] **Step 3: Write tune.md**

```markdown
# Tune Node Template

> Architecture compliance, duplication detection, abstraction analysis.

## Purpose

Audit target code quality across 4 dimensions: compliance, duplication,
abstraction, validation. Output: scored report + task list.

## Phases

### Phase 0: Project Profile
- Detect architecture type (3-tier, 2-tier, DDD, modular)
- Map logical layers (Entry/Business/Data/Utility) by dependency direction
- User confirms profile before proceeding

### Phase 1: Architecture Compliance
- Check dependency directions per architecture type
- Validate layer responsibilities
- Flag cross-layer violations

### Phase 2: Duplication Detection
- 4-layer scan: API/Entry, Service/Business, Data/Query, Utility
- >70% structural similarity = candidate duplicate

### Phase 3: Abstraction Analysis
- Vertical: similar classes -> base class opportunity
- Horizontal: scattered code -> shared method opportunity
- Over-abstraction: 1 impl + 1 call site + transparent passthrough = over-engineered

### Phase 4: Synthesis
- 5D scoring: compliance(25%) + duplication(25%) + abstraction(20%) + validation(15%) + data-model(15%)
- Output: tuner-report.md + tuner-tasks.json

## Rules

1. **Backend code only**: Frontend/docs repos rejected.
2. **Understand-then-scan**: LLM reads project rules once, then batch scans.
3. **No auto-refactoring**: Report + task list only.
4. **Pre-launch vs maintenance**: Each finding has aggressive (pre-launch) and conservative (maintenance) variants.
5. **Responsibility over naming**: Layer assignment by dependency patterns, not folder names.
6. **Over-abstraction detection**: Simultaneously check "should abstract" and "shouldn't have abstracted".

## What Bootstrap Specializes

- Architecture type and layer mapping (from discovery)
- Language-specific compliance rules
- Framework-specific patterns to check
- Pre-launch vs maintenance mode selection
```

- [ ] **Step 4: Write ui-forge.md**

```markdown
# UI Forge Node Template

> Post-implementation UI refinement: fidelity check, restore, polish.

## Purpose

After code is functionally complete, verify UI matches design spec,
restore deviations, then polish visual quality.

## Phases

1. **Fidelity Check**: Compare implementation vs design baseline (spec + tokens + screenshots)
2. **Restore**: Fix deviations to match design spec
3. **Polish**: Visual hierarchy, responsive, state design, micro-interactions

## Rules

1. **Restore before polish**: Align to design before enhancing.
2. **No business logic changes**: UI-only modifications.
3. **Spec/token/component are binding constraints**.
4. **Function-first**: Feature must be complete before UI tuning.

## What Bootstrap Specializes

- Design spec file locations
- Token/design system references
- UI framework (Tailwind, styled-components, SwiftUI modifiers...)
- Component library patterns
```

- [ ] **Step 5: Write demo-forge.md**

```markdown
# Demo Forge Node Template

> Generate realistic demo data via API-driven population.

## Purpose

Create demo-ready data sets that showcase the product's capabilities.
Design data schema from product map, populate via API calls, verify visually.

## Phases

1. **Design**: Product map -> data scheme (accounts, volume, flows, enums, time distribution, media)
2. **Media**: Search/generate images+videos, upload to app server (zero external links)
3. **Execute**: API-driven data population with integrity checking
4. **Verify**: Playwright verification (7 layers), iterate until 95% pass rate

## Rules

1. **Product-map prerequisite**: product-map must exist before demo-forge.
2. **App must be running**: execute + verify need live app instance.
3. **API-driven insertion**: Validate data integrity during population, not after.
4. **Zero external links**: All media assets uploaded to app server.
5. **95% convergence**: Iterate design->execute->verify until 95% pass (max 3 rounds).

## What Bootstrap Specializes

- API endpoint discovery (from task-inventory or route scan)
- Data model schema (from discovery)
- Media style profile (from existing app screenshots)
- App startup commands + URLs
- Account/credential setup for data population
```

- [ ] **Step 6: Commit**

```bash
git add claude/meta-skill/knowledge/nodes/visual-verify.md claude/meta-skill/knowledge/nodes/tune.md claude/meta-skill/knowledge/nodes/ui-forge.md claude/meta-skill/knowledge/nodes/demo-forge.md
git commit -m "knowledge(nodes): visual-verify + tune + ui-forge + demo-forge templates"
```

---

### Task 6: knowledge/mappings/ seed files

**Files:**
- Create: `claude/meta-skill/knowledge/mappings/react-swiftui.md`
- Create: `claude/meta-skill/knowledge/mappings/react-compose.md`
- Create: `claude/meta-skill/knowledge/mappings/express-gin.md`
- Remove: `claude/meta-skill/knowledge/mappings/.gitkeep`
- Source: `claude/code-replicate-skill/docs/stack-mappings.md`

- [ ] **Step 1: Read stack-mappings.md fully**

Read `claude/code-replicate-skill/docs/stack-mappings.md` (entire file).

- [ ] **Step 2: Write react-swiftui.md**

Extract React-specific mappings from stack-mappings.md and add SwiftUI-specific equivalents. Include component mapping, state management, lifecycle, navigation, and async patterns.

```markdown
# React -> SwiftUI Mapping

## Component Mapping

| React | SwiftUI |
|-------|---------|
| `<div>` | `VStack` / `HStack` / `ZStack` |
| `<span>` / `<p>` | `Text` |
| `<img>` | `AsyncImage` / `Image` |
| `<input>` | `TextField` / `SecureField` |
| `<button>` | `Button` |
| `<select>` | `Picker` |
| `<textarea>` | `TextEditor` |
| `<ul>` / `<li>` | `List` / `ForEach` |
| `<a>` / `<Link>` | `NavigationLink` |
| `{condition && <X/>}` | `if condition { X() }` |
| `{items.map(i => <X/>)}` | `ForEach(items) { X() }` |

## State Management

| React | SwiftUI |
|-------|---------|
| `useState` | `@State` |
| `useReducer` | `@State` + enum action pattern |
| `useContext` | `@Environment` / `@EnvironmentObject` |
| `useRef` | Local variable (not in body) |
| `useMemo` | Computed property |
| `useCallback` | Method on View/ViewModel |
| Redux store | `@Observable` class |
| Redux useSelector | Property access on `@Observable` |
| Redux dispatch | Method call on `@Observable` |
| React Query | Async method on ViewModel |

## Lifecycle

| React | SwiftUI |
|-------|---------|
| `useEffect(fn, [])` | `.task { }` |
| `useEffect(fn, [dep])` | `.onChange(of: dep) { }` / `.task(id: dep) { }` |
| `useEffect` cleanup | `.onDisappear { }` / Task cancellation |
| `componentDidMount` | `.onAppear { }` |

## Navigation

| React | SwiftUI |
|-------|---------|
| React Router `<Routes>` | `NavigationStack` |
| `<Route path="/">` | `.navigationDestination(for:)` |
| `useNavigate()` | `NavigationPath` / `@Environment(\.dismiss)` |
| `<Link to="/">` | `NavigationLink` |
| URL params | Path-based navigation values |

## Async Patterns

| React | SwiftUI |
|-------|---------|
| `async/await` in useEffect | `Task { }` / `.task { }` |
| `Promise.all` | `async let` / `TaskGroup` |
| Loading state pattern | `@State var isLoading` + `ProgressView` |
| Error boundary | `do/catch` + `@State var error` |

## Styling

| React | SwiftUI |
|-------|---------|
| CSS className | View modifiers |
| styled-components | ViewModifier + custom Shape |
| Tailwind flex | HStack/VStack |
| Tailwind padding/margin | `.padding()` |
| CSS media query | `@Environment(\.horizontalSizeClass)` |
```

- [ ] **Step 3: Write react-compose.md**

Similar structure for React -> Jetpack Compose. Key differences from SwiftUI mapping.

```markdown
# React -> Jetpack Compose Mapping

## Component Mapping

| React | Compose |
|-------|---------|
| `<div>` flex row | `Row` |
| `<div>` flex column | `Column` |
| `<div>` stacked | `Box` |
| `<span>` / `<p>` | `Text` |
| `<img>` | `AsyncImage` (Coil) |
| `<input>` | `TextField` / `OutlinedTextField` |
| `<button>` | `Button` / `IconButton` |
| `<select>` | `DropdownMenu` + `ExposedDropdownMenuBox` |
| `<ul>` / `<li>` | `LazyColumn` / `LazyRow` |
| `<a>` / `<Link>` | Navigation composable |
| `{condition && <X/>}` | `if (condition) { X() }` |
| `{items.map(i => <X/>)}` | `items.forEach { X(it) }` |

## State Management

| React | Compose |
|-------|---------|
| `useState` | `remember { mutableStateOf() }` |
| `useReducer` | `remember { mutableStateOf() }` + sealed class action |
| `useContext` | `CompositionLocalProvider` / ViewModel via Hilt |
| Redux store | ViewModel + StateFlow |
| Redux useSelector | `collectAsState()` |
| Redux dispatch | ViewModel method call |

## Lifecycle

| React | Compose |
|-------|---------|
| `useEffect(fn, [])` | `LaunchedEffect(Unit) { }` |
| `useEffect(fn, [dep])` | `LaunchedEffect(dep) { }` |
| `useEffect` cleanup | `DisposableEffect { onDispose { } }` |

## Navigation

| React | Compose |
|-------|---------|
| React Router | Jetpack Navigation Compose |
| `<Route path="/">` | `composable("route") { }` |
| `useNavigate()` | `navController.navigate()` |
| URL params | `navController.currentBackStackEntry.arguments` |
```

- [ ] **Step 4: Write express-gin.md**

```markdown
# Express -> Gin (Go) Mapping

## Routing

| Express | Gin |
|---------|-----|
| `router.get("/path", handler)` | `r.GET("/path", handler)` |
| `router.post("/path", handler)` | `r.POST("/path", handler)` |
| `router.use(middleware)` | `r.Use(middleware)` |
| `router.group("/prefix")` | `r.Group("/prefix")` |
| `req.params.id` | `c.Param("id")` |
| `req.query.page` | `c.Query("page")` |
| `req.body` | `c.ShouldBindJSON(&body)` |
| `res.json(data)` | `c.JSON(200, data)` |
| `res.status(404).json(err)` | `c.JSON(404, err)` |

## Middleware

| Express | Gin |
|---------|-----|
| `app.use(cors())` | `r.Use(cors.Default())` |
| `app.use(morgan("dev"))` | `r.Use(gin.Logger())` |
| `app.use(express.json())` | Built-in (ShouldBindJSON) |
| Custom auth middleware | `func AuthMiddleware() gin.HandlerFunc` |
| `next()` | `c.Next()` |
| `req.user = decoded` | `c.Set("user", decoded)` / `c.Get("user")` |

## ORM (Sequelize -> GORM)

| Sequelize | GORM |
|-----------|------|
| `Model.findAll()` | `db.Find(&results)` |
| `Model.findByPk(id)` | `db.First(&result, id)` |
| `Model.create(data)` | `db.Create(&record)` |
| `Model.update(data, {where})` | `db.Model(&record).Updates(data)` |
| `Model.destroy({where})` | `db.Delete(&record, id)` |
| Migrations (sequelize-cli) | GORM AutoMigrate / goose |
| Associations (belongsTo/hasMany) | GORM tags (belongs_to/has_many) |

## Auth (Passport.js -> Go)

| Passport.js | Go |
|-------------|-----|
| JWT strategy | golang-jwt/jwt |
| OAuth2 strategy | golang.org/x/oauth2 |
| Session strategy | gorilla/sessions + Redis |

## Async

| Express/Node | Go |
|-------------|-----|
| `async/await` | goroutine |
| `Promise.all` | `errgroup` / `sync.WaitGroup` |
| Bull/BullMQ queue | asynq (Redis) / machinery |
| `setTimeout` | `time.After` / `time.NewTimer` |
| EventEmitter | Channel |
```

- [ ] **Step 5: Commit**

```bash
rm claude/meta-skill/knowledge/mappings/.gitkeep
git add claude/meta-skill/knowledge/mappings/
git commit -m "knowledge(mappings): react-swiftui + react-compose + express-gin seed mappings"
```

---

### Task 7: knowledge/domains/ seed files

**Files:**
- Create: `claude/meta-skill/knowledge/domains/ecommerce.md`
- Create: `claude/meta-skill/knowledge/domains/fintech.md`
- Remove: `claude/meta-skill/knowledge/domains/.gitkeep`

- [ ] **Step 1: Write ecommerce.md**

```markdown
# E-Commerce Domain Knowledge

## Core Business Flows
- Browse -> Search -> Product Detail -> Add to Cart -> Checkout -> Payment -> Order Confirmation
- Order Management: Track -> Cancel -> Return -> Refund
- Seller: List Product -> Manage Inventory -> Process Orders -> Handle Returns

## Typical Roles
- Buyer (consumer, experience_priority: consumer)
- Seller/Merchant (professional, experience_priority: admin)
- Platform Admin (professional, experience_priority: admin)
- Customer Service (professional, experience_priority: admin)

## Critical Business Rules
- Inventory consistency (concurrent purchase race condition)
- Payment idempotency (double-charge prevention)
- Order state machine (pending -> paid -> shipped -> delivered -> completed)
- Price calculation (discounts, coupons, taxes, shipping)

## Common Entities
- User/Account, Product/SKU, Cart, Order, OrderItem, Payment, Address, Review, Category

## Domain-Specific Checks
- CRUD completeness per entity (especially Order lifecycle)
- Payment callback handling (async notification from payment provider)
- Stock deduction timing (optimistic vs pessimistic locking)
- Multi-currency support (if international)
```

- [ ] **Step 2: Write fintech.md**

```markdown
# Fintech Domain Knowledge

## Core Business Flows
- Account Opening -> KYC Verification -> Fund Account -> Transact -> Settle
- Lending: Apply -> Credit Check -> Approve -> Disburse -> Repay
- Investment: Browse -> Research -> Order -> Execute -> Portfolio View

## Typical Roles
- Customer (consumer, experience_priority: consumer)
- Compliance Officer (professional, experience_priority: admin)
- Risk Manager (professional, experience_priority: admin)
- Support Agent (professional, experience_priority: admin)

## Critical Business Rules
- Double-entry bookkeeping (every debit has matching credit)
- Transaction atomicity (ACID compliance)
- Regulatory compliance (KYC/AML/PCI-DSS)
- Audit trail (immutable transaction log)
- Rate limiting (fraud prevention)

## Common Entities
- Account, Transaction, Ledger, User, KYCRecord, Instrument, Portfolio, Order

## Domain-Specific Checks
- Transaction reversibility rules
- Settlement timing (T+0, T+1, T+2)
- Interest calculation accuracy
- Regulatory reporting completeness
```

- [ ] **Step 3: Commit**

```bash
rm claude/meta-skill/knowledge/domains/.gitkeep
git add claude/meta-skill/knowledge/domains/
git commit -m "knowledge(domains): ecommerce + fintech seed domain knowledge"
```

---

### Task 8: Verify Complete Knowledge Structure

- [ ] **Step 1: Verify all knowledge files exist**

```bash
find claude/meta-skill/knowledge -type f -name "*.md" | sort
```

Expected:
```
claude/meta-skill/knowledge/domains/ecommerce.md
claude/meta-skill/knowledge/domains/fintech.md
claude/meta-skill/knowledge/mappings/express-gin.md
claude/meta-skill/knowledge/mappings/react-compose.md
claude/meta-skill/knowledge/mappings/react-swiftui.md
claude/meta-skill/knowledge/nodes/compile-verify.md
claude/meta-skill/knowledge/nodes/demo-forge.md
claude/meta-skill/knowledge/nodes/discovery.md
claude/meta-skill/knowledge/nodes/generate-artifacts.md
claude/meta-skill/knowledge/nodes/product-analysis.md
claude/meta-skill/knowledge/nodes/test-verify.md
claude/meta-skill/knowledge/nodes/translate.md
claude/meta-skill/knowledge/nodes/tune.md
claude/meta-skill/knowledge/nodes/ui-forge.md
claude/meta-skill/knowledge/nodes/visual-verify.md
claude/meta-skill/knowledge/orchestrator-template.md
claude/meta-skill/knowledge/safety.md
```

17 files total (10 nodes + 3 mappings + 2 domains + safety + orchestrator-template).

- [ ] **Step 2: Verify each node template has required sections**

Check that each `knowledge/nodes/*.md` contains:
- `## Purpose`
- `## Rules (Bootstrap Must Preserve)` or `## Rules`
- `## What Bootstrap Specializes`

```bash
for f in claude/meta-skill/knowledge/nodes/*.md; do
  echo "=== $f ==="
  grep -c "## Purpose\|## Rules\|## What Bootstrap" "$f"
done
```

Expected: each file outputs `3` (has all 3 sections).

- [ ] **Step 3: Final commit**

```bash
git add -A
git commit -m "chore(meta-skill): Plan 2 complete — knowledge base with 10 nodes, 3 mappings, 2 domains"
```
