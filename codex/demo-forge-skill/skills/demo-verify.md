---
name: demo-verify
description: >
  Use when the user asks to "verify demo data", "check demo quality",
  "demo-verify", "demo check", or mentions demo verification, visual verification, demo quality check.
  Requires forge-data.json and a running application.
version: "1.1.0"
---

# Demo Verify — Verification and Issue Routing

> Data structure correctness does not equal visual correctness. Open the product and confirm item by item.

## Goal

Use Playwright to verify demo data in the real product for **functional + visual correctness**:

1. **Can log in** — every role account can log in and see permission-appropriate data
2. **Has data** — list pages have records, detail pages have complete fields, reports show nonzero numbers
3. **Visually correct** — images load, videos play, no placeholder remnants
4. **Mathematically correct** — Dashboard totals match details, trend charts have multi-month data
5. **Does not crash** — terminal state records viewable, boundary data does not error
6. **Zero external links** — no external media URLs in DOM (final enforcement of media-forge iron rule)
7. **Full liveness** — every screen has data to operate on, every state has records to display, data flow causality is unbroken
8. **Issue routing** — structured issue list, routed by type to the corresponding phase or dev-forge

---

## Position

```
demo-forge internal stages:
  demo-design  ->  media-forge + demo-execute  ->  demo-verify (this skill)
  Plan data         Acquire media + populate         Open product and verify item by item
  Pure design       Consumes scheme                  Produces issue list routed back for fixes
```

---

## Prerequisites

| Condition | Description |
|-----------|-------------|
| forge-data.json exists | Data has been populated, `.allforai/demo-forge/forge-data.json` |
| Application running and accessible | URL reachable via browser |
| Playwright MCP available | Playwright browser automation tools ready |

If prerequisites not met, prompt to run demo-execute, start the app, or install Playwright MCP.

---

## Workflow

### V1: Login Verification

**Goal**: Confirm all role accounts can log in and see correct permission data.

**Steps**:

1. Read `demo-plan.json` credentials section for all role accounts
2. For each role account:
   - Navigate to login page
   - Fill username/email + password
   - Submit login
   - Wait for redirect
   - Verify correct Dashboard/home page
   - Check: role-specific data visible, unauthorized menus absent
   - Screenshot: `screenshots/v1-round{N}-{role}.png`

**Pass criteria**: All roles can log in and see permission-appropriate data.

---

### V2: List Page Verification

**Goal**: Confirm list pages have data, correct sorting, working images, no placeholder text.

**Steps**:

For each role's main list views:
- Navigate to list page
- Check DOM:

| Check Item | Method | Pass Criteria |
|-----------|--------|---------------|
| Record count > 0 | List row/card count | Page not empty |
| Sort correct | Read time/ID fields | Newest first (descending) |
| Pagination works | Find pagination component | Exists when data sufficient |
| Images load | JS: `img.naturalWidth > 0 && img.complete` | No broken images |
| No placeholder text | Full text scan | No "Lorem ipsum", "test", "TODO", "undefined", "null", "placeholder" |

- Screenshot: `screenshots/v2-round{N}-{list_name}.png`

---

### V3: Detail Page Verification

**Goal**: Confirm detail page fields complete, related data correct, media loads.

**Steps**:

Sample N records per entity type (N = min(3, entity total)):
- Navigate to detail page
- Check:

| Check Item | Method | Pass Criteria |
|-----------|--------|---------------|
| Fields complete | Scan visible field areas | No null/undefined/empty/dash placeholders |
| Related data | Check child entity lists | Child lists have records |
| Status history | Find status flow area | Has operation records |
| Media loads | Check img/video elements | Images display, videos have valid src |

- Screenshot: `screenshots/v3-round{N}-{entity}-{id}.png`

---

### V4: Dashboard / Report Verification

**Goal**: Confirm Dashboard numbers nonzero, trend charts have multi-month data, totals match details.

| Check Item | Method | Pass Criteria |
|-----------|--------|---------------|
| Numbers nonzero | Read stat card text | Main metrics > 0 |
| Trend chart multi-month | Check chart data points | >= 3 months of data |
| Totals consistent | Compare Dashboard total vs list detail sum | Total = detail sum (1% tolerance) |
| Charts rendered | Check canvas/svg elements | Non-blank, non-zero height |

- Screenshot: `screenshots/v4-round{N}-{dashboard}.png`

**Consistency check method**: Read total from Dashboard, navigate to corresponding list page and accumulate details, compare. Difference > 1% -> mark as `data_integrity` issue.

---

### V5: Edge Case Verification

**Goal**: Confirm terminal state records, search functionality, boundary data do not error.

1. **Terminal state records**: Navigate to CLOSED / REJECTED / CANCELED record detail pages
   - Check: page renders normally, no errors, fields complete

2. **Search/filter**: Execute search on list pages
   - Fill known-existing keyword (from forge-data.json)
   - Check: results non-empty, results match keyword

3. **Boundary data**:
   - Long text records: check no overflow/truncation causing layout break
   - Zero amount records: check displays correctly ("0.00" not empty or NaN)
   - Screenshot boundary cases

---

### V6: Media Integrity Verification (critical)

**Goal**: The most critical check — confirm zero external links, zero broken images, zero placeholders in the product. External URLs mean the media-forge iron rule was violated.

**Steps**:

For each page with media, execute JavaScript scan of all media elements:

```javascript
const appBaseUrl = window.location.origin;
const issues = [];

// Check all images
document.querySelectorAll('img[src]').forEach((img, i) => {
  const src = img.src;
  if (img.naturalWidth === 0 || !img.complete) {
    issues.push({ type: 'broken_image', src, index: i });
  }
  if (src.startsWith('http') && !src.startsWith(appBaseUrl)) {
    issues.push({ type: 'external_url', src, index: i });
  }
  if (/placeholder|data:image\/svg|picsum|via\.placeholder|placehold/i.test(src)) {
    issues.push({ type: 'placeholder', src, index: i });
  }
});

// Check all videos
document.querySelectorAll('video[src], video source[src]').forEach((el, i) => {
  const src = el.src || el.getAttribute('src');
  if (!src) issues.push({ type: 'missing_video_src', index: i });
  if (src && src.startsWith('http') && !src.startsWith(appBaseUrl)) {
    issues.push({ type: 'external_video_url', src, index: i });
  }
});

// Check video playability
document.querySelectorAll('video').forEach((video, i) => {
  if (video.readyState === 0) {
    issues.push({ type: 'video_not_ready', src: video.src, index: i });
  }
});

// Check duplicate images in same list
const imgSrcs = [...document.querySelectorAll('img[src]')].map(i => i.src);
const duplicates = imgSrcs.filter((s, i) => imgSrcs.indexOf(s) !== i);
if (duplicates.length > 0) {
  issues.push({ type: 'duplicate_images', srcs: [...new Set(duplicates)] });
}

return issues;
```

| Check Item | Severity | Description |
|-----------|----------|-------------|
| Broken image (naturalWidth === 0) | high | Image 404 or load failure |
| External URL (src not matching app base URL) | high | media-forge iron rule violated |
| Placeholder pattern | high | Placeholders forbidden |
| Aspect ratio anomaly (>20% deviation) | medium | Severe stretch/compress |
| Video not playable (readyState === 0) | high | Invalid video source |
| Duplicate images in same list | medium | Data diversity insufficient |

All issues from this step categorized as `media`, route_to="media" for media-forge re-entry.

---

### V7: UI Liveness + Data Flow Verification

**Goal**: Reverse-verify from design artifacts — every screen/action in experience-map has data support so every screen is "alive" during demo.

#### V7-A: UI Liveness Guarantee

**Baseline**: experience-map.json (required) + demo-plan.json

**Verification rules** (per screen, per action, Playwright check):

| UI Element Type | Minimum Data Guarantee | Check Method |
|----------------|----------------------|--------------|
| List page | >= 2 records (shows sorting) | Count list rows/cards |
| Detail page | >= 1 complete-field record | Check no null/undefined/empty |
| Action buttons | >= 1 operable target record | Button not disabled, has target |
| Search/filter | >= 2 distinguishable records | Search results change (not full return) |
| Status tags/badges | At least 1 per state | Verify against `task.outputs.states` |
| Dashboard/charts | >= 1 month span data | Chart non-empty, numbers nonzero |
| Empty state pages | Verify empty state display | No blank/error when no data |

**Reverse verification chain**:
```
experience-map.screen.actions[]
  -> What prerequisite data does each action need?
  -> Does demo-plan.json plan that data?
  -> Does it actually exist at runtime?
```

**Liveness score**: `actions with data support / total screen actions`
- >= 90% -> PASS
- 70-89% -> WARNING
- < 70% -> FAIL

Insufficient liveness -> route_to = "design"

#### V7-B: State Coverage Verification

Every entity's `outputs.states` enum values must have demo data. Focus on terminal and exception states.

Missing states -> route_to = "design"

#### V7-C: Data Flow Integrity

Verify business logic chain continuity — create -> transit -> approve -> complete causality unbroken.

1. Extract chain definitions from `demo-plan.json`
2. Per chain, verify each node via Playwright:
   - User A's operation -> appears in User B's pending list?
   - Parent entity's child list -> count and status consistent?
   - Dashboard total -> equals detail sum?
3. Any broken node -> route_to = "execute"

---

### V8: Issue Summary + Routing

**Goal**: Aggregate all V1-V7 failures, classify severity, route to corresponding phase.

**Routing rules**:

| Issue Type | category | route_to | Typical Scenario |
|-----------|----------|----------|-----------------|
| Missing data, uncovered enums, incomplete chains | coverage | design | Entity 0 records, missing REJECTED state |
| Broken images, unplayable video, external links, placeholders | media | media | 404, stretch, gray blocks |
| FK breakage, derived inconsistency, population failure | data_integrity | execute | Dashboard total != detail sum |
| API 500, frontend render bug, SQL error, code crash | code_bug | dev_task | Application code bug, not data issue |
| UI liveness insufficient | liveness | design | Screen action has no data support |
| Data flow breakage | data_flow | execute | Parent entity has empty child list |
| Pure style preference, unrelated to data | style_preference | skip | Record but do not route |

**6V Deep Diagnosis** (for `code_bug` and `data_integrity` high-severity issues):
- V1 Contract: API signature/response format deviation
- V2 Conformance: data violates entity-model constraints
- V3 Correctness: business logic error
- V4 Consistency: same operation behaves differently across pages/roles
- V5 Capability: performance bottleneck triggered by data volume
- V6 Context: error tied to specific role/scenario (permission/isolation)
- Diagnosis written to issue `diagnosis` field: `{ "viewpoint": "V2", "root_cause": "...", "fix_hint": "..." }`

**Output**: verify-report.json (full) + verify-issues.json (failures + routing + 6V diagnosis)

---

## dev_task Backflow Mechanism

When issues have `route_to="dev_task"`, generate dev-forge compatible fix tasks:

```markdown
### B-FIX-{N}: {title}

**Source**: demo-verify Round {N}, {issue_id}
**Evidence**: {screenshot_path}
**Description**: {description}
**Acceptance**: {fix description}
```

Append to `.allforai/project-forge/sub-projects/{name}/tasks.md` B-FIX round. Mark in verify-issues.json as `DEFERRED_TO_DEV`. Demo-forge does not wait for fix, continues processing other issue types.

---

## Screenshot Storage

All screenshots in `.allforai/demo-forge/screenshots/`:

```
screenshots/
├── v1-round{N}-{role}.png
├── v2-round{N}-{list_name}.png
├── v3-round{N}-{entity}-{id}.png
├── v4-round{N}-{dashboard}.png
├── v5-round{N}-{scenario}.png
└── v6-round{N}-{page}-{issue}.png
```

Each round keeps independent screenshots (round number increments) for before/after comparison.

---

## Regression Verification Mode

When running regression (specific round), verify only previous round's fix items:

1. Read previous round verify-issues.json
2. Filter out `route_to="skip"` and `DEFERRED_TO_DEV` items
3. Re-execute corresponding V-checks for each pending item
4. Also sample full regression (ensure fixes did not introduce new issues)
5. Output new round verify-report.json + verify-issues.json

---

## Output Files

| File | Location | Description |
|------|----------|-------------|
| verify-report.json | `.allforai/demo-forge/` | Full verification report (V1-V7 all check results) |
| verify-issues.json | `.allforai/demo-forge/` | Failed items + routing targets |
| screenshots/ | `.allforai/demo-forge/screenshots/` | Verification screenshots (named by step + round) |
