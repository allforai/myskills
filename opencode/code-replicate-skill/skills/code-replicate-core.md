---
name: code-replicate-core
description: >
  Internal shared protocol for code replication. Do NOT invoke directly —
  loaded by cr-backend.md, cr-frontend.md, cr-fullstack.md, or cr-module.md.
version: "2.1.0"
---

# Code Replicate Core Protocol v2.1

## Overview

Code Replicate is a reverse-engineering bridge: read existing codebases, generate standard `.allforai/` artifacts (product-map, experience-map, use-case) so that the dev-forge pipeline (`design-to-spec` -> `task-execute`) can consume them directly.

This skill's sole responsibility is extracting **business intent** (what it does) from source code, not copying **implementation decisions** (how it does it). Source code's sync/async model, error handling conventions, communication protocols, etc. are implementation decisions replaced by target ecosystem's architectural conventions.

---

## 4-Phase Pipeline

### Phase 1: Preflight

1. Check for replicate-config.json (checkpoint resume — see below)
2. Parse parameters: mode, path/url, --type, --scope, --module, --from-phase
3. Source acquisition:
   - Local path -> use directly
   - Git URL -> `git clone --depth 1` (HTTPS / SSH / GitHub shorthand `user/repo`)
   - Supports `#branch` suffix: `https://github.com/user/repo#develop`
4. Collect missing parameters (ask naturally, consolidate into one question):
   - Fidelity (interface / functional / architecture / exact)
     > Details: `./docs/fidelity-guide.md`
   - Project type (backend / frontend / fullstack / module)
   - Scope (full / modules / feature)
   - Target tech stack (same stack or cross-stack + target name)
   - Business direction (replicate / slim / extend)
   - Source App runtime info (for Phase 2 screenshots + `cr-visual` use):
     - Start commands (frontend + backend)
     - URL
     - Login credentials (**multi-role**: one set per role that needs screenshots, including 2FA bypass if applicable)
     - Test data preparation command (seed script or demo accounts)
     - Platform type
   > **Input audit**: After user answers, check **intent closure** (does code behavior match what user wants?) and **boundary closure** (code handles normal path, what about exceptions user expects?). Ask follow-up for MUST-level gaps as multiple-choice.
5. Write replicate-config.json -> `.allforai/code-replicate/` (including `source_app` field)
6. Create fragments directory structure: `.allforai/code-replicate/fragments/{roles,screens,tasks,flows,usecases,constraints}/`

---

### Phase 2: Discovery + Confirm

Phase 2 has 4 stages, 15 steps total. Detailed protocols for each stage are loaded on demand.

#### Stage A — Structure Discovery (what does the project look like)

| Step | Output | What |
|------|--------|------|
| 2.1 | discovery-profile.json | LLM reads root dir -> generates module discovery rules |
| 2.2 | source-summary.json skeleton | cr_discover.py scans files |
| 2.3 | source-summary.json initial | LLM reads key_files per module -> summaries |
| 2.3.5 | File coverage scan | Unread file header scan -> find gaps -> supplement -> coverage >= 50% |
| 2.3.7 | file-catalog + code-index | Assemble file cards -> knowledge base (file-catalog.json + code-index.json) |
| 2.4 | project_archetype | LLM identifies project core value type |

> Details: `./docs/phase2/stage-a-structure.md`

#### Stage B — Runtime Foundation Discovery (what does the project run on)

| Step | Output | What |
|------|--------|------|
| 2.5 | infrastructure-profile.json | In-house infrastructure inventory |
| 2.6 | env-inventory.json | Environment variable inventory |
| 2.7 | third-party-services.json | Third-party service inventory |
| 2.8 | cron-inventory.json | Scheduled task inventory |
| 2.9 | error-catalog.json | Error code catalog |

> Details: `./docs/phase2/stage-b-runtime.md`

#### Stage C — Resource Discovery (what assets/data does the project carry)

| Step | Output | What |
|------|--------|------|
| 2.10 | asset-inventory.json | Frontend asset inventory |
| 2.11 | seed-data-inventory.json | Backend base data |
| 2.12 | abstractions + cross_cutting | Reuse patterns + cross-cutting concerns |
| 2.12.5 | role-view-matrix.json | Role-view difference matrix |
| 2.12.8 | interaction-recordings.json | Business flow chains (end-to-end interaction + multi-role + exception states) |
| 2.13 | visual/source/ (screenshots + recordings) | Multi-role screenshots + dynamic effect recordings |

> Details: `./docs/phase2/stage-c-resources.md`

#### Stage D — Confirm + Mapping

| Step | Output | What |
|------|--------|------|
| 2.14 | User confirmation | Show discoveries -> last interaction |
| 2.15 | stack-mapping.json | Cross-stack mapping |

> Details: `./docs/phase2/stage-d-confirm.md`

> **=== After Phase 2, no more configuration questions ===**

---

### Phase 3: Generate (Silent Execution)

**Step 3-pre** — LLM generates `extraction-plan.json` (project-specific extraction rules)

LLM reads source-summary.json (module inventory, tech stacks, key_files), generates extraction plan specific to **this project**, written to `.allforai/code-replicate/extraction-plan.json`:

```json
{
  "role_sources": [
    {"module": "M003", "file": "internal/middleware/auth.go", "how": "RoleType enum defines 4 roles"}
  ],
  "task_sources": [
    {"module": "M001", "file": "cmd/api/handlers/*.go", "how": "each exported handler function = one task"}
  ],
  "flow_sources": [
    {"module": "M002", "file": "internal/service/order_service.go", "how": "CreateOrder call chain = one complete flow"}
  ],
  "screen_sources": [
    {"module": "M010", "file": "src/app/*/page.tsx", "how": "each page.tsx = one screen, layout.tsx in same dir provides layout info"}
  ],
  "usecase_sources": [
    {"module": "M001", "file": "cmd/api/handlers/*.go", "how": "if/switch branches in handler = boundary/exception use case"}
  ],
  "constraint_sources": [
    {"module": "M004", "file": "internal/model/*.go", "how": "validate struct tags = input constraints"}
  ],
  "cross_cutting": [
    {"concern": "auth", "files": ["internal/middleware/auth.go"], "applies_to": ["M001", "M002"]}
  ],
  "abstraction_sources": [
    {"file": "lib/core/base_bloc.dart", "how": "15 feature Blocs inherit this, provides unified loading/error state handling"}
  ],
  "asset_sources": [
    {"path": "LLM points to asset directories from asset-inventory", "migration": "copy | transform | replace"}
  ],
  "event_sources": [
    {"file": "LLM points to event bus implementation files", "how": "LLM extracts all event types + publishers + subscribers"}
  ],
  "infrastructure_sources": [
    {"file": "LLM points to infra implementation files", "how": "LLM describes implementation mechanism"}
  ],
  "dependency_map": [
    {"from": "M001", "to": "M003", "via": "require('app.service.user_service')", "type": "direct_call"}
  ]
}
```

**Generation principles**:
- LLM **must** read source-summary.json module key_files before generating
- Each source entry's `how` field describes extraction logic **specific to this project**, not a framework template
- `dependency_map` — LLM reads key_files import/require statements to populate
- **`artifacts` — LLM decides which artifacts to produce for this project** (see below)

### extraction-plan.artifacts — LLM freely decides artifact list

extraction-plan adds an `artifacts` field: LLM decides **what to produce, what schema, where to store** based on project_archetype.

**No hardcoded Step 3.1-3.6**. LLM plans the artifact list:

```json
"artifacts": [
  {
    "name": "LLM names it (e.g., task-inventory / system-spec / dag-spec / command-tree)",
    "path": "output path (e.g., product-map/task-inventory.json)",
    "schema": "LLM describes schema (free-form) or references standard schema",
    "sources": [{"module": "...", "file": "...", "how": "..."}],
    "merge_script": "corresponding merge script path or null (LLM outputs complete artifact)"
  }
]
```

**Standard Web App** artifacts (LLM naturally generates, not hardcoded):
- role-profiles -> `cr_merge_roles.py`
- experience-map -> `cr_merge_screens.py` (when UI exists)
- task-inventory -> `cr_merge_tasks.py`
- business-flows -> `cr_merge_flows.py`
- use-case-tree -> `cr_merge_usecases.py`
- constraints -> `cr_merge_constraints.py` (exact only)
- test-vectors -> null (LLM outputs directly)
- indexes + product-map -> gen scripts

**Non-standard projects** artifacts (LLM decides freely):
- Game server -> system-spec (ECS system defs) + config-schema + protocol-spec
- Data pipeline -> dag-spec + transform-catalog + schema-registry
- CLI tool -> command-tree + plugin-interface
- Microservice consolidation -> service-boundary-map

**Artifacts with merge scripts** (standard .allforai/ artifacts) use the script merge flow.
**Artifacts without merge scripts** (project-specific) are output directly by LLM as complete JSON, stored in `.allforai/code-replicate/`.

dev-forge and cr-fidelity adaptively consume **whatever artifacts actually exist** (existing mechanism).

---

Execute per extraction-plan.artifacts list: LLM reads sources -> generates fragments -> **UI closure verification** -> **4D self-check** -> merge.

### UI-Driven Closure Understanding (Phase 2.13 evidence as Phase 3 input)

**Source code is only half the truth** — code has dead code, uncalled functions, commented-out features. What appears in screenshots is what users actually use.

During Phase 3 artifact generation, LLM reads not just source code but **also references Phase 2.13 evidence**:
- Screenshots -> what UI does the user actually see
- Recordings -> what interactions does the user actually experience
- API logs -> what requests do user actions actually trigger
- result.json -> what actually changes on screen after operations

**Closure reasoning**: From observed UI behavior, infer "what else should exist". LLM reasons across four dimensions without fixed rules:

- **Functional closure**: From observed operations, infer complementary operations for the same entity
- **Interaction closure**: From observed UI states, infer matching paired states
- **API closure**: From captured API requests, infer complete operation set for the same resource
- **Data closure**: From screenshot data fields, trace back to source code retrieval/computation/formatting logic

**Execution**: After generating each module's fragments, LLM views that module's screenshots and API logs -> asks "does my artifact cover everything visible in screenshots?" -> fills gaps.

### 4D Fragment Self-Check (executed immediately after each Step)

After generating each module's fragment, LLM validates with four-dimensional questioning:

| Dimension | Question | If fails |
|-----------|----------|----------|
| **D1 Conclusion** | Do extracted tasks/roles/flows completely cover this module's source code business logic? Any missing entry points? | Add missing items |
| **D2 Evidence** | Can each acceptance_criteria trace back to which source file/logic? What's the basis for protection_level? | Add `_evidence` internal notes |
| **D3 Constraints** | Missing preconditions? Exception paths covered? Cross-module dependencies annotated? | Add prerequisites/exceptions |
| **D4 Decisions** | Rationale for categorizing as core vs basic? Is audience_type judgment reasonable? | Correct judgment or add rationale |

4D self-check is **a thinking process embedded in each Step**, not producing additional files. If issues found, LLM corrects the fragment before passing to merge script.

### Standard Artifact Step Reference

> Only loaded when extraction-plan.artifacts includes standard .allforai/ artifacts.
> Details: `./docs/phase3/standard-artifact-steps.md`

### Phase 4: Verify & Handoff

> Details: `./docs/phase4/verify-handoff.md`

---

## Iron Laws

1. **Preflight + Discovery collects all parameters** — No configuration questions after Phase 2
2. **source-summary stays in context** — All Phase 3 LLM calls include it as global context
3. **Single target per LLM call** — One call generates one artifact type for one module fragment
4. **Scripts merge artifacts** — LLM does not handle cross-module merging or ID assignment
5. **Standard artifact paths** — task-inventory / business-flows / role-profiles -> `product-map/`, use-case-tree -> `use-case/`, CR process files -> `code-replicate/`
6. **Fragments are not final artifacts** — fragments/ temporary JSON is only for merge script consumption, not for dev-forge
7. **Business intent first** — Extract "what it does", don't copy "how it does it"; implementation decisions filled by target ecosystem
8. **Downstream required fields** — `experience_priority` (product-map), `protection_level` (task), `audience_type` (role), `render_as` (component) must be generated; dev-forge depends on these throughout
9. **Structured fields** — `inputs`/`outputs`/`audit` must use object format (not simple arrays), `then` (use-case) must be an array
10. **LLM direct output first** — `audience_type`, `protection_level`, `render_as` and other semantic fields must be output directly by LLM in fragments (based on source code semantic understanding); scripts only do fallback. Do not rely on name keyword pattern matching as primary judgment
11. **extraction-plan driven** — Each Phase 3 Step must work per extraction-plan.json specified files and extraction methods, not framework templates. extraction-plan itself is generated by LLM based on source-summary, ensuring adaptation to any tech stack
12. **Abstraction reuse propagation** — Source code reuse patterns (source-summary.abstractions) must propagate to target code. Cross-stack via stack-mapping.abstraction_mapping; same-stack dev-forge reads abstractions directly. Never expand N-module shared base class/mixin/DI into N copies of duplicated code
13. **4D fragment self-check** — Every Phase 3 Step must execute 4D questioning after generating fragments, fix on the spot, don't wait for Phase 4
14. **6V multi-dimensional audit** — Phase 4 must audit from user/business/tech/data/ux/risk perspectives to prevent single-dimension blind spots
15. **Inner loop convergence** — Phase 4a repair loop follows CG-1: max 3 rounds, monotonic decrease, violate = stop. Prevents infinite repair loops
16. **Outer loop intent fidelity** — Phase 4d returns to source-summary origin to verify extraction coverage, follows CG-3: gap additions <= 20% of total items, max 1 round
17. **Cross-platform adaptation** — When source and target platforms have different interaction models (mobile<->desktop), must generate `platform_adaptation`. UX patterns cannot be transferred as-is to different platform targets
18. **Config as code** — Non-code config files (nginx.conf, routes.yaml, OpenAPI spec, etc.) may contain business logic. extraction-plan must include these, using `"module": null` for root-level files
19. **Infrastructure before business** — Phase 2b-infra must complete before business extraction (Phase 3). LLM inventories all infrastructure by reading code behavior, not package names. `cannot_substitute: true` components cannot be approximately replaced
20. **Protocols must be structured** — Custom protocol/encryption/serialization components must output `protocol_spec` (frame format + state machine + test vectors), not just text descriptions
21. **Runtime verification** — cr-fidelity cannot only do code comparison (static), must include runtime: build (R1), smoke start (R2), test vectors (R3), protocol compatibility (R4). Combined = static x 0.5 + runtime x 0.5
22. **Project archetype driven + artifact freedom** — LLM identifies project_archetype in Phase 2.4, freely decides artifacts in extraction-plan.artifacts. Standard Web apps naturally choose task-inventory + flows; games choose system-spec + config-schema
23. **Assets as code** — Frontend static resources (icons, images, fonts, animations, theme variables, i18n text) are part of the code. Missing = runtime broken images/missing fonts/raw keys
24. **UI-driven closure** — Phase 3 extraction references Phase 2.13 screenshots/recordings/API logs alongside source code. What's visible in screenshots is what users actually use
25. **Don't skip files** — LLM cannot skip files based on filename guessing. Phase 2.3.5 requires sampling unread files. Each module coverage >= 50%
26. **code-index always in context** — Phase 3 every LLM call must load both source-summary.json and code-index.json
27. **No screenshot fabrication** — Phase 2.13 screenshots must come from real business operations. `page.evaluate()` only allowed for ViewModel/Store method calls (Tier 2) or reading state. Three-tier strategy: user interaction (Tier 1) -> ViewModel call (Tier 2) -> network mock (Tier 3) -> unreachable = mark UNREACHABLE

---

## Fidelity Control

Fidelity does not determine which CR files are generated, but which fields in standard artifacts are populated and to what depth.

| Level | Analysis Depth | Artifact Output |
|-------|---------------|----------------|
| interface | Entry-layer signatures only | task-inventory (slim) + role-profiles (with audience_type) + product-map (with experience_priority) |
| functional | Read function bodies, trace logic | Above + business-flows (with systems/handoff) + use-case-tree (flat array) + task structured fields |
| architecture | Additional module dependency analysis | Above + task adds module/prerequisites/cross_dept + innovation_use_case |
| exact | Additional bug/constraint marking | Above + constraints.json + task.flags |

> Full details: `./docs/fidelity-guide.md`

---

## Checkpoint Resume

replicate-config.json `progress` field tracks completion state per step:

```json
"progress": {
  "current_phase": 2,
  "current_step": "2.8",
  "completed_steps": [
    {"step": "2.1", "duration_ms": 12000},
    {"step": "2.2", "duration_ms": 8000},
    {"step": "2.3", "duration_ms": 45000}
  ],
  "completed_artifacts": ["discovery-profile.json", "source-summary.json", "infrastructure-profile.json"]
}
```

**After completing each Step**, LLM immediately updates `progress` (writes replicate-config.json). Crash then restart -> resume from `current_step`.

- Phase 2 steps are precise to `"2.1"` ~ `"2.15"` (including `"2.3.7"`)
- Phase 3 each artifact is precise to `"3.task-inventory"` / `"3.system-spec"` etc.
- `--from-step 2.5` -> restart from Step 2.5 (clear 2.5+ progress + artifacts)
- `--from-phase 3` -> restart from Phase 3 (preserve all Phase 2 artifacts)

## Incremental Replication

After source code changes, no need to rerun the entire pipeline:

```
code-replicate --incremental
```

**Incremental detection**:
1. Compare source current git hash vs `replicate-config.progress.source_hash`
2. `git diff` to find changed files
3. Map changed files -> affected modules (source-summary.modules)
4. Only re-execute for affected modules

## Skip Modules

Some modules in source_path don't need replication:

```
code-replicate --skip payment-service,legacy-tool
```

Skipped modules: not analyzed in Phase 2, no artifacts in Phase 3, not verified in Phase 4. But still recorded as **external dependencies** in dependency_map.

## Parallelization

Phase 2 Stage B steps (2.5-2.9) are independent -> can run in parallel.
Phase 3 module fragment generation can also be parallelized.
LLM decides whether to parallelize — small projects are simpler serial, large projects are faster parallel.

## Progress Visibility

After each Step, LLM outputs progress:

```
Phase 2 > Stage A [████████████████████] 4/4 done
Phase 2 > Stage B [████████████░░░░░░░░] 3/5 running 2.8 cron-inventory...
```

## Database Schema Migration

LLM extracts Schema info in Step 2.11, written to `seed-data-inventory.json` extended fields.

dev-forge reads this schema -> generates equivalent database migrations for the target stack.

---

## Error Handling

| Scenario | Handling |
|----------|----------|
| Git clone fails | Phase 1 error exit |
| Source is empty | Phase 2a error exit |
| LLM returns invalid JSON | Retry once, still fails -> skip module, mark in report |
| cr_validate.py fails | Error list given to LLM for correction, max 2 rounds |
| Module source too large (>100KB) | Read only key_files, mark partial_analysis |
| Script doesn't exist | LLM generates complete artifact directly (degraded mode) |

---

## Artifact Paths

**Standard artifacts** (dev-forge consumable):
- `.allforai/product-map/`: product-map.json, task-inventory.json, role-profiles.json, business-flows.json, constraints.json, task-index.json, flow-index.json
- `.allforai/experience-map/`: experience-map.json (frontend/fullstack stub)
- `.allforai/use-case/`: use-case-tree.json, use-case-report.md

**CR-specific process files**:
- `.allforai/code-replicate/`: replicate-config.json, source-summary.json, discovery-profile.json, extraction-plan.json, stack-mapping.json, replicate-report.md
- `.allforai/code-replicate/fragments/`: intermediate fragments (can delete after merge)

---

## Script Reference

All scripts at `../../shared/scripts/code-replicate/`:

```bash
# Phase 2: Discovery (with optional LLM-generated profile)
python3 ../../shared/scripts/code-replicate/cr_discover.py <source_path> <output_path> [--profile <profile_path>]

# Phase 3: Merge scripts
python3 ../../shared/scripts/code-replicate/cr_merge_roles.py <base_path> <fragments_dir>
python3 ../../shared/scripts/code-replicate/cr_merge_screens.py <base_path> <fragments_dir>
python3 ../../shared/scripts/code-replicate/cr_merge_tasks.py <base_path> <fragments_dir>
python3 ../../shared/scripts/code-replicate/cr_merge_flows.py <base_path> <fragments_dir>
python3 ../../shared/scripts/code-replicate/cr_merge_usecases.py <base_path> <fragments_dir>
python3 ../../shared/scripts/code-replicate/cr_merge_constraints.py <base_path> <fragments_dir>

# Phase 3: Generation scripts
python3 ../../shared/scripts/code-replicate/cr_gen_usecase_report.py <base_path>
python3 ../../shared/scripts/code-replicate/cr_gen_indexes.py <base_path>
python3 ../../shared/scripts/code-replicate/cr_gen_product_map.py <base_path>

# Phase 4: Validation & Report
python3 ../../shared/scripts/code-replicate/cr_validate.py <base_path>
python3 ../../shared/scripts/code-replicate/cr_gen_report.py <base_path>
```

**Merge script conventions**:
- Read `<fragments_dir>/*.json` -> merge/dedup -> assign sequential IDs -> write to `<base_path>` standard paths
- Fragment filename format: `{module_name}.json` (one fragment file per module)
- Merge auto-handles: ID renumbering, cross-fragment reference fixing, duplicate deduplication

**Gen script conventions**:
- Read merged artifacts -> generate derived files (report / index / summary)
- Do not modify merged standard artifacts

**LLM fragment generation format**:
- Each LLM call outputs one module's JSON fragment
- Fragments use temporary IDs (e.g., `TMP-001`), merge scripts renumber
- Cross-module references use `$ref:module_name:tmp_id` placeholders, merge scripts resolve
- **Fragments must include semantic fields** (cannot omit for scripts to guess):
  - Role fragments: `audience_type` (consumer / professional)
  - Task fragments: `protection_level` (core / defensible / nice_to_have), structured `inputs`/`outputs`
  - Screen fragments: each component's `render_as` (12-value enum), `layout_type` (semantic name)
