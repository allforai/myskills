---
name: cr-visual
description: >
  Use when user wants to "compare UI visually", "visual fidelity", "screenshot comparison",
  "UI fidelity", "visual comparison", "screenshot diff",
  or mentions comparing source and target app screenshots for UI fidelity.
version: "1.0.0"
---

# Visual Fidelity — CR Visual v1.0

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
  "match_level": "high | medium | low | mismatch",
  "score": 100 | 70 | 40 | 0,
  "differences": "LLM free description of differences",
  "source_screenshot": "visual/source/xxx.png",
  "target_screenshot": "visual/target/xxx.png"
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
  "overall_score": 82,
  "screens": [
    {"screen": "...", "match_level": "high", "score": 100, "differences": "No notable differences"},
    {"screen": "...", "match_level": "low", "score": 40, "differences": "List layout changed from cards to table, missing filter bar"}
  ]
}
```

`visual-report.md` includes:
- Each screen's screenshot path pair (user can view directly)
- Difference descriptions
- Overall score
- Fix recommendations for low-scoring screens

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

     Non-UI layer (root cause escalation -> fix then come back):
       - Empty list/wrong data -> check API call -> maybe backend field mismatch -> fix backend code
       - Permission button not hidden -> check RBAC logic -> maybe role-view-matrix not restored -> fix permission code
       - Request error -> check error code -> maybe error-catalog inconsistent -> fix error definitions
       - Broken icons/fonts -> check asset references -> maybe asset migration missed -> add assets
       - Infrastructure differences -> check infrastructure-profile -> maybe protocol/encryption layer issue

  5. Execute fix:
     UI layer -> directly Edit target code
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
