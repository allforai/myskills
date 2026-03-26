---
name: cr-visual
description: >
  Use when user wants to "compare UI visually", "visual fidelity", "screenshot comparison",
  "UI fidelity", "visual comparison", "screenshot diff",
  or mentions comparing source and target app screenshots for UI fidelity.
version: "1.0.0"
---

# Visual Fidelity — CR Visual v1.1

> Source App vs Target App screen-by-screen screenshot/recording -> compare -> fix -> re-compare -> until visually consistent

## Positioning

cr-visual is the **last step** in the replication flow — executed after cr-fidelity + product-verify + testforge all pass.

```
cr-fidelity -> product-verify -> testforge -> cr-visual (here)
```

**Prerequisite**: tests all green, App can run stably. Screenshot comparison requires a working App.

**Platform difference auto-exclusion**: If `stack-mapping.json` has `platform_adaptation` -> cr-visual auto-loads transformation rules at startup. Differences matching platform_adaptation (e.g., mobile bottom nav -> desktop sidebar) are auto-marked as `not_a_gap`, LLM comparison skips them without deducting points.

**Multi-role comparison**: If `role-view-matrix.json` exists -> screenshot per role and compare separately.

**Interaction behavior comparison**: If `interaction-recordings.json` exists -> source App evidence was collected in Phase 2.13. cr-visual executes **the same business flow chains** on the target App:

Per flow execution (following interaction-recordings.json flows structure):
1. Execute same operation sequence on target App per flow.steps (role switch, form fill, click, wait)
2. Screenshot at each screenshot milestone -> compare with source App's corresponding screenshot
3. Simultaneously capture target App's API logs -> compare with source App's api.json

Five-layer verification:
1. **Static pages**: source screenshot vs target screenshot -> layout/component/data display consistent?
2. **CRUD full state**: flow chain naturally covers CRUD lifecycle -> per-milestone screenshot comparison
3. **Dynamic effects** (type=visual_effect flows): source recording vs target recording -> animation/transition consistent?
4. **API logs**: source api.json vs target api.json -> same operations trigger same requests?
5. **Combined**: same flow -> every milestone screenshot + API all consistent = high

Each interaction outputs match_level: high / medium / low / mismatch

---

## Flow

```
Step 1: Get screen list (from experience-map)
Step 2: Get source App screenshots/recordings (Phase 2 collected or live capture)
Step 3: Get target App screenshots/recordings
Step 4: LLM per-screen comparison (structural + dynamic effects)
Step 4.5: Control data integrity audit (empty control tracing + score correction)
Step 4.6: Control linkage verification (executed when interaction-recordings has linkage_verify)
Step 5: Difference report + scoring
Step 6: Fix differences (LLM modifies target code)
Step 7: Re-screenshot/record -> re-compare -> exit when passing
```

`full` mode = Step 1-7 loop (max 3 rounds)
`analyze` mode = Step 1-5 report only
`fix` mode = Step 6-7 fix based on last report

---

## Step 1: Screen List + Route Mapping

From `.allforai/experience-map/experience-map.json` extract all screens, build route mapping:

```
1. Extract each screen's name, route (if any), layout_type from experience-map
2. Read .allforai/code-replicate/visual/route-map.json (Phase 2c-visual generated route->screenshot mapping)
3. Build pairing: screen name <-> route path <-> source screenshot filename
   - experience-map screen has route -> direct match route-map
   - experience-map screen has no route -> LLM matches by semantic similarity between screen name and route-map
4. Skip unpaired screens
```

---

## Step 1.5: Source App Startup Info

cr-visual needs to know how to start and navigate the source App. Information sources (priority):

1. **replicate-config.json `source_app` field** (collected in code-replicate Phase 1):
   ```json
   "source_app": {
     "start_command": "npm run dev",
     "backend_start_command": "cd server && npm start",
     "seed_command": "npm run db:seed",
     "url": "http://localhost:3000",
     "login": {
       "username": "test@example.com",
       "password": "test123",
       "bypass_command": "env var/API call to bypass 2FA (if any)"
     },
     "platform": "web | mobile | desktop"
   }
   ```
   Phase 1 Preflight should ask the user:
   - How to start the source App? Need to start backend first?
   - Is there test data? What's the seed command?
   - Need to login? Has CAPTCHA/2FA? How to bypass?

2. **User provides URL directly via `--source` parameter**

3. **User provides existing screenshots via `--screenshots`**

If replicate-config has no `source_app` and user didn't pass parameters -> ask the user naturally.

---

## Step 2: Source App Screenshots

**Method A (preferred) — Phase 2 already collected**:
- Check if `.allforai/code-replicate/visual/source/` already has screenshots
- Already has -> reuse directly (Phase 2c-visual collected early in replication, source project env may no longer exist)

**Method B — User provides screenshot directory**:
- Read image files from `--screenshots` directory
- LLM matches image filenames with experience-map screen names

**Method C — Source App still runnable**:
- Follow Phase 2c-visual full protocol (start backend -> seed data -> start frontend -> login -> screenshot)
- Any precondition failure (backend unavailable, database empty, login failed) -> don't screenshot, report specific failure reason

**No screenshots available** -> error exit: "Source App screenshots unavailable. Provide --screenshots directory, or ensure source App environment is complete (backend + data + login credentials)."

---

## Step 3: Target App Screenshots

**Screenshot tool is decided by LLM based on target tech stack**. LLM reads project tech stack -> selects suitable UI automation tool -> executes screenshot commands via Bash.

LLM reads target project tech stack -> searches for and selects appropriate UI automation tools -> executes via Bash. No fixed tool list.

**If LLM cannot find a usable automation tool** -> prompt user to manually screenshot to `visual/target/`. This is last resort, not default behavior.

---

## Step 4: LLM Per-Screen Comparison

For each screenshot pair (source/screen_name.png vs target/screen_name.png), LLM views both images:

**Structural comparison (do)**:
- Are region divisions equivalent? (header/content/footer/sidebar)
- Are key UI elements present? (buttons, inputs, lists, cards)
- Is data display area positioned reasonably?
- Are navigation entries visible? (menus, tabs, back buttons)
- Is information hierarchy consistent? (title > subtitle > body hierarchy)

**Don't do**:
- Pixel-level color comparison (target can change theme)
- Exact font/size matching (target can use different fonts)
- Exact spacing/whitespace matching (target can redesign spacing)
- Animation/transition effects (screenshots can't show these)

**Cross-platform adjustments**:
- If stack-mapping has `platform_adaptation.ux_transformations`
- Evaluate per transformation expectations: mobile single column -> desktop multi-panel is not a gap
- Mobile bottom nav -> desktop sidebar is not a gap

**Each screen output**:
```json
{
  "screen": "screen name",
  "structural_match": "high | medium | low | mismatch",
  "structural_score": 100 | 70 | 40 | 0,
  "differences": "LLM free description of differences",
  "source_screenshot": "visual/source/xxx.png",
  "target_screenshot": "visual/target/xxx.png"
}
```

> Note: This step only outputs `structural_match` / `structural_score`. Final `match_level` / `score` are computed after Step 4.5.

---

## Step 4.5: Control Data Integrity Audit

> Step 4 checks "does the control exist?", Step 4.5 checks "does the control have data?". Both steps are required.

For each screen's target screenshot, LLM scans the following control types and compares against source screenshot for data completeness:

**1. Data Containers**: DataGrid / Table / List / Tree / TreeView
- Source has N data rows -> target must have >= 1 row of real data (exact row count match not required)
- Are table headers/columns consistent with source?
- Does tree have child nodes when expanded?

**2. Selectors**: ComboBox / Select / Dropdown / RadioGroup / Checkbox Group
- Source has selectable options -> target cannot have 0 options
- If possible, automate click/expand selector -> screenshot to verify option list is non-empty

**3. Display Bindings**: TextInput / Label / Badge / Counter / Chip / Tag
- Source shows bound values (e.g., "John Doe", "$128.00") -> target cannot be blank, "undefined", "null", "NaN"
- Placeholder text does not count as a bound value

**4. Visualizations**: Chart / Graph / Dashboard Widget / ProgressBar / Sparkline
- Source has rendered data -> target cannot show empty axes/empty pie chart/progress bar at 0

**For each empty control, mandatory root cause tracing**:

```
1. Mark as data_integrity_gap, record control_type + screen + control location description
2. Read target code -> find the control's data source:
   a. API endpoint? -> Check if URL is correct, if it's being called, if response is empty, if field mapping is correct
   b. Static data/enums? -> Check if initialization data or enum definitions are missing
   c. Computed/derived value? -> Check if computation logic has null/undefined paths
   d. State management? -> Check if store/state is correctly initialized and subscribed
3. Record trace result: { control_type, location, data_source, root_cause }
```

**Score correction**:

```
Penalty per data_integrity_gap:
  - Empty data container (Table/List/Tree zero rows)         -> -15 points
  - Empty selector (ComboBox/Select zero options)            -> -10 points
  - Empty binding (Label/Badge showing blank/undefined)      -> -5 points
  - Empty visualization (Chart with no data rendered)        -> -15 points

Final score calculation:
  final_score = structural_score - sum(data_integrity_penalties)
  final_score = max(0, final_score)  // floor at 0

match_level determined by final_score:
  >= 90 -> high | >= 60 -> medium | >= 30 -> low | < 30 -> mismatch
```

**Prohibited**:

- NO hardcoded fake data fixes (e.g., hardcoding `["Option1", "Option2"]` or `[{name: "Test"}]` in frontend)
- NO mock servers replacing real APIs
- NO temporary data injection before screenshots (e.g., `localStorage.setItem` with fake data)
- MUST fix the real data pipeline: frontend component -> API call -> backend logic -> database query
- MUST re-screenshot after fix to verify the control shows real data

**Each screen final output** (merged Step 4 + 4.5):
```json
{
  "screen": "screen name",
  "match_level": "high | medium | low | mismatch",
  "score": 85,
  "structural_score": 100,
  "data_integrity_score": 85,
  "differences": "Structure intact, but order list DataGrid is empty (0 rows), status filter ComboBox has no options",
  "data_integrity_gaps": [
    {
      "control_type": "DataGrid",
      "location": "center-page order list area",
      "expected": "Source screenshot has 8 order rows",
      "actual": "Target screenshot has header but 0 data rows",
      "data_source": "API: GET /api/orders",
      "root_cause": "Frontend calls /api/order (missing 's'), silently fails on 404",
      "penalty": -15
    }
  ],
  "source_screenshot": "visual/source/xxx.png",
  "target_screenshot": "visual/target/xxx.png"
}
```

---

## Step 4.6: Control Linkage Verification

> **Prerequisite**: `interaction-recordings.json` exists and contains `linkage_verify` steps. No such file or no linkage steps -> skip.

Step 4/4.5 check static state (what the screenshot shows), Step 4.6 checks **dynamic causality** (does action A -> B respond correctly).

**Execution protocol**:

For each `linkage_verify` step in interaction-recordings:

```
1. Execute trigger_action on target App (e.g., select "Guangdong Province")
2. Wait for linkage response (brief wait, typically 500ms-2s)
3. Verify each expected_effect:

   options_update (cascade selection):
     -> Expand downstream selector -> screenshot -> option list is non-empty and content relates to trigger value
     -> Compare with source App's same-step screenshot

   visibility_toggle (conditional show/hide):
     -> Check target control's visible state change
     -> Screenshot verify: control appears/disappears consistent with source App

   enabled_toggle (conditional enable/disable):
     -> Check target control's disabled/enabled state
     -> Screenshot comparison or DOM attribute check

   value_update (auto-calculation):
     -> Read target control's displayed value
     -> Compare with source App's corresponding value (or verify correctness based on known formula)
     -> Pay special attention: NaN, 0, blank = calculation chain broken

   data_filter (linked filtering):
     -> Screenshot after switching -> table/list content correctly filtered?
     -> Row count change reasonable (not full set, not zero rows)

   detail_load (master-detail linkage):
     -> Click a row in master control -> screenshot detail area
     -> Detail content corresponds to clicked row's data (strong assertion: field values match)

   reset (linkage reset):
     -> After parent changes -> child correctly cleared/restored to default

4. Each linkage checkpoint outputs:
   - linkage_result: pass / fail / partial
   - On failure record: trigger_control, target_control, effect_type, expected, actual
```

**Score impact**:

```
Each linkage checkpoint result:
  pass    -> no penalty
  partial -> -5 points (linkage triggered but result not fully correct, e.g., options exist but content wrong)
  fail    -> -10 points (linkage completely ineffective, downstream control unresponsive)

Linkage score computed independently, appended to screen's final_score:
  final_score = structural_score - data_integrity_penalties - linkage_penalties
```

**Each screen final output adds linkage fields**:
```json
{
  "linkage_results": [
    {
      "trigger_control": "Province dropdown",
      "trigger_action": "select Guangdong",
      "target_control": "City dropdown",
      "effect_type": "options_update",
      "result": "fail",
      "expected": "Options update to Guangdong cities",
      "actual": "Option list still empty",
      "root_cause": "onChange does not call fetchCities(), event binding lost",
      "penalty": -10
    }
  ],
  "linkage_score": 90
}
```

---

## Step 5: Report

Written to `.allforai/code-replicate/visual-report.json` + `visual-report.md`:

```json
{
  "generated_at": "ISO8601",
  "total_screens": 20,
  "compared": 18,
  "skipped": 2,
  "overall_score": 68,
  "structural_avg_score": 82,
  "data_integrity_avg_score": 65,
  "linkage_avg_score": 75,
  "total_data_integrity_gaps": 7,
  "total_linkage_failures": 3,
  "screens": [
    {
      "screen": "...", "match_level": "high", "score": 100,
      "structural_score": 100, "data_integrity_score": 100, "linkage_score": 100,
      "differences": "No notable differences", "data_integrity_gaps": [], "linkage_results": []
    },
    {
      "screen": "...", "match_level": "low", "score": 35,
      "structural_score": 70, "data_integrity_score": 55, "linkage_score": 80,
      "differences": "List layout changed from cards to table, missing filter bar",
      "data_integrity_gaps": [
        {"control_type": "DataGrid", "location": "...", "root_cause": "...", "penalty": -15}
      ],
      "linkage_results": [
        {"trigger_control": "...", "target_control": "...", "effect_type": "options_update", "result": "fail", "penalty": -10}
      ]
    }
  ]
}
```

`visual-report.md` includes:
- Each screen's screenshot path pair (user can view directly)
- Structural difference descriptions
- **Data integrity audit results** (empty control list + trace conclusions)
- **Control linkage verification results** (linkage checkpoint list + failure root causes)
- Overall score (structural score + data integrity score + linkage score = combined score)
- Fix recommendations for low-scoring screens (distinguishing structural fixes / data pipeline fixes / linkage fixes)

---

## Steps 6+7: Repair Loop

Visual fidelity aims for **100% consistency**, not "close enough". Continuously fix until perfect.

**Repair loop**:

```
Each round:
  1. Read visual-report.json -> find screens with match_level != high
  2. Sort by score ascending -> take the lowest scored 1 screen
  3. Read source screenshot/recording + target screenshot/recording -> identify specific differences
  4. Diagnose root cause layer:
     LLM views screenshot/recording differences -> judge which layer the root cause is in:

     UI layer (fix directly):
       - Layout structure -> modify template/CSS
       - Missing component -> add component
       - Theme variables -> correct variable values
       - Missing assets -> add icons/images/fonts
       - Missing animation -> add CSS transition / animation code

     Data integrity layer (Step 4.5 marked data_integrity_gap -> fix per trace results):
       - API not called/wrong URL -> fix frontend API call code
       - API returns empty -> check backend query logic/database has data -> fix backend or add seed
       - Field mapping error -> fix frontend data binding (e.g., response.data vs response.result)
       - Missing enum/static options -> add enum definitions (NO hardcoded fake data, must come from config or API)
       - Store/State not initialized -> fix state management initialization logic
       WARNING: Hardcoded fake data = invalid fix. Must use real data pipeline.

     Linkage layer (Step 4.6 marked linkage fail/partial -> fix per linkage type):
       - Event binding lost -> add onChange/onSelect/onClick binding to correct handler function
       - Linkage API not called -> fix event handler, add downstream data fetch logic
       - Linkage state not propagated -> fix setState/dispatch/emit, ensure downstream controls subscribe to correct data source
       - Missing computed/watch -> add reactive computation chain (e.g., quantity x price -> total)
       - Missing conditional visibility logic -> add v-if/v-show/visible binding condition
       - Missing conditional enable/disable logic -> add disabled binding condition
       - Missing linkage reset -> reset downstream control values and options when parent changes
       WARNING: After fix, must re-execute linkage_verify to confirm linkage restored

     Non-UI layer (root cause escalation -> fix then come back):
       - Permission button not hidden -> check RBAC logic -> maybe role-view-matrix not restored -> fix permission code
       - Request error -> check error code -> maybe error-catalog inconsistent -> fix error definitions
       - Broken icons/fonts -> check asset references -> maybe asset migration missed -> add assets
       - Infrastructure differences -> check infrastructure-profile -> maybe protocol/encryption layer issue

  5. Execute fix:
     UI layer -> directly Edit target code
     Data integrity layer -> fix real data pipeline per data_integrity_gap.root_cause
     Linkage layer -> fix event binding/state propagation/reactive computation chain -> re-run linkage_verify to verify
     Non-UI layer -> root cause escalation:
       a. Mark current screen as BLOCKED (waiting for upstream fix)
       b. Directly fix upstream code (backend/API/permissions/assets/infrastructure)
       c. Rebuild frontend and backend after fix
       d. Return to current screen to continue visual fixing

  6. Build verification (ensure compilation not broken)
  7. Re-screenshot/record the fixed screen
  8. Re-compare -> update visual-report.json
  9. Screen reaches high -> next screen
     Still not high -> continue fixing this screen (may have multi-layer differences)

Exit conditions:
  - All screens match_level = high -> 100% achieved
  - Or reach 30 round limit
```

**Key requirements**:

**Must use real data and real services**:
- Target App must connect to **real backend** when screenshotting (not mock server)
- Pages must show **real business data** (not sampled seed data)
- If source App screenshots used real data -> target App screenshots must use same data source
- Data differences causing UI differences are not visual bugs — but **empty data vs has data** differences are bugs

**Fix 1 screen per round**:
- Focus on one problem until perfect, don't jump around
- Fix one screen (high) then next
- Avoid "fixed A broke B" back-and-forth

**30 rounds is minimum guarantee, not upper limit**:
- 60 pages x possibly 1-3 rounds each -> need enough rounds
- If still screens not high after 30 rounds -> continue
- Only stop when all screens are high or user manually terminates

---

## Limitations

- LLM visual comparison is **subjective** — report includes screenshot paths, user should review
- Requires App to run and be navigable to each page (needs test accounts/data)
- Mobile screenshots depend on platform-specific UI automation tools or user manual screenshots
- Interaction behavior comparison depends on `interaction-recordings.json` flows structure — without this file, only static screenshot comparison

---

## Load Core Protocol

> Core protocol details: `./skills/code-replicate-core.md`
