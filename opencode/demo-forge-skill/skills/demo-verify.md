---
name: demo-verify
description: >
  Use when the user asks to "verify demo data", "check demo quality",
  "demo-verify", "demo check", or mentions demo verification,
  visual verification, demo quality check.
  Requires forge-data.json and a running application.
version: "1.1.0"
---

# Demo Verify — Verification and Issue Routing

> Data structure correct does not mean visual correct. Open the product, verify each item.

## Goal

Use Playwright as the automation tool to verify demo data's **functional correctness + visual correctness** in the real product:

1. **Can log in** — every role account logs in and sees permission-appropriate data
2. **Has data** — list pages have records, detail pages have complete fields, reports show non-zero numbers
3. **Looks right** — images load, videos play, no placeholder residue
4. **Calculates right** — Dashboard totals match detail sums, trend charts have multi-month data
5. **Doesn't crash** — terminal state records viewable, boundary data doesn't error
6. **Zero external links** — no external media URLs in DOM (media-forge iron rule final check)
7. **Fully alive** — every screen/button has data to operate on, every state has records to display, data flow causal chains unbroken
8. **Issue routing** — structured issue list, routed by type to corresponding phase or dev-forge

---

## Positioning

```
demo-forge internal stages:
  demo-design  →  media-forge + demo-execute  →  demo-verify (this skill)
  Plan what data to generate   Acquire assets + populate data    Verify each item
  Pure design, no execution    Consume the design plan           Route issues back
```

---

## Prerequisites

| Condition | Description |
|-----------|-------------|
| forge-data.json exists | Data populated, `.allforai/demo-forge/forge-data.json` |
| Application running and accessible | Browser-accessible URL |
| Playwright MCP available | `mcp__playwright__*` series tools ready |

If prerequisites not met, tell user to run demo-execute, start the application, or install Playwright MCP.

---

## Workflow

### V1: Login Verification

**Goal**: confirm all role accounts can log in and see correct permission data.

**Steps**:

1. Read `demo-plan.json` credentials section for all role accounts
2. For each role account:
   - `browser_navigate` to login page
   - `browser_fill_form` with username/email + password
   - `browser_click` submit login
   - `browser_wait_for` redirect completion
   - Verify redirect to correct Dashboard/home page
   - `browser_snapshot` check: role-specific data visible, permissions correct (hidden menus not shown)
   - `browser_take_screenshot` save: `screenshots/v1-round{N}-{role}.png`

**Pass criteria**: all roles can log in, data matches permissions.

---

### V2: List Page Verification

**Goal**: confirm list pages have data, correct sorting, images load, no placeholder text.

**Steps**:

1. For each role's main list views:
   - `browser_navigate` to list page
   - `browser_snapshot` read DOM, check:

   | Check | Method | Pass criteria |
   |-------|--------|---------------|
   | Records > 0 | Count list rows/cards | Page not empty |
   | Sort correct | Read time/ID fields | Most recent first (descending) |
   | Pagination works | Find pagination component | Pagination exists when data sufficient |
   | Images load | `browser_evaluate`: check `img.naturalWidth > 0 && img.complete` | No broken images |
   | No placeholder text | Full text scan | No "Lorem ipsum", "test", "TODO", "undefined", "null", "placeholder" |

   - `browser_take_screenshot` save: `screenshots/v2-round{N}-{list_name}.png`

---

### V3: Detail Page Verification

**Goal**: confirm detail page fields complete, related data correct, media loads.

**Steps**:

1. Sample N records per entity type (N = min(3, entity total))
2. For each record:
   - `browser_navigate` to detail page
   - `browser_snapshot` check:

   | Check | Method | Pass criteria |
   |-------|--------|---------------|
   | Fields complete | Traverse visible field areas | No null/undefined/empty/"—" placeholders |
   | Related data | Check sub-entity lists | Sub-lists have records (e.g., order has line items) |
   | Status history | Find status flow area | Has operation records (create/review/complete) |
   | Media loads | Check img/video elements | Images display, videos have valid src |

   - `browser_take_screenshot` save: `screenshots/v3-round{N}-{entity}-{id}.png`

---

### V4: Dashboard / Report Verification

**Goal**: confirm Dashboard numbers non-zero, trend charts multi-month, totals match details.

**Steps**:

1. Navigate to each Dashboard / report page:
   - `browser_snapshot` + `browser_evaluate` check:

   | Check | Method | Pass criteria |
   |-------|--------|---------------|
   | Numbers non-zero | Read stat card text | Key metrics > 0 |
   | Trend multi-month | Check chart data points | >= 3 months data |
   | Totals consistent | Compare Dashboard total vs list detail sum | Total = detail sum (allow 1% tolerance) |
   | Charts render | Check canvas/svg elements | Not blank / not zero height |

   - `browser_take_screenshot` save: `screenshots/v4-round{N}-{dashboard}.png`

**Consistency check method**: read summary number from Dashboard, navigate to corresponding list page and sum details, compare. Difference > 1% → mark as data_integrity issue.

---

### V5: Edge Case Verification

**Goal**: confirm terminal state records, search, boundary data don't error.

**Steps**:

1. **Terminal state records**: navigate to records with status CLOSED / REJECTED / CANCELED
   - Check: page renders normally, no errors, fields complete

2. **Search/filter**: execute search on list pages
   - `browser_fill_form` with keywords (from forge-data.json known values)
   - Check: results non-empty, results match keywords

3. **Boundary data**:
   - Extra-long text records: check no overflow/truncation causing layout break
   - Zero amount records: check displays correctly ("0.00" not empty or NaN)
   - `browser_take_screenshot` save boundary case screenshots

---

### V6: Media Integrity Verification (critical)

**Goal**: the most critical check — confirm zero external links, zero broken, zero placeholders in the product. External URLs mean media-forge iron rule violated.

**Steps**:

1. For each page with media, execute `browser_evaluate` scanning all media elements:

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

2. Check severity:

   | Check | Severity | Description |
   |-------|----------|-------------|
   | Broken image (naturalWidth === 0 or complete === false) | high | Image 404 or load failure |
   | External URL (src doesn't match app base URL) | high | media-forge iron rule violation |
   | Placeholder pattern | high | Placeholders forbidden |
   | Aspect ratio anomaly (width/height deviation > 20%) | medium | Severe stretch/squeeze |
   | Video unplayable (readyState === 0) | high | Video source invalid |
   | Same-list duplicate images | medium | Data diversity insufficient |

3. `browser_take_screenshot` for all flagged items

**Note**: all issues from this step classified as `media` category, route_to="media", handled by media-forge reentry.

---

### V7: UI Liveness + Data Completeness Verification

**Goal**: reverse-verify from design artifacts — does every screen/action in experience-map have data support, making every screen "alive" for demos.

#### V7-A: UI Liveness Guarantee

**Baseline**: experience-map.json (required) + seed-plan.json / demo-plan.json

**Verification rules** (per screen, per action, Playwright check):

| UI element type | Minimum data guarantee | Check method |
|----------------|------------------------|-------------|
| List page | >= 2 records (visible sorting effect) | `browser_evaluate` count rows/cards |
| Detail page | >= 1 record with complete fields | Check no null/undefined/empty |
| Action buttons | >= 1 operable target record | Button not disabled and has target |
| Search/filter | >= 2 distinguishable records | Search results change (not full return) |
| Status badges | Each status at least 1 record | Check against `task.outputs.states` per state |
| Dashboard/charts | >= 1 month span data | Chart renders, numbers non-zero |
| Empty state page | Verify empty state specifically | Empty state displays correctly (not blank/error) |

**Reverse verification chain**:
```
experience-map.screen.actions[]
  → What prerequisite data does each action need? (e.g., "approve" button needs PENDING records)
  → Did demo-plan.json plan that data?
  → Does that data actually exist at runtime?
```

**Liveness score**: `actions with data support / total screen actions`
- >= 90% → PASS
- 70-89% → WARNING (some demo limited)
- < 70% → FAIL (severely impacts demo)

Insufficient liveness screens → route_to = "design" (supplement demo-plan data chains)

#### V7-B: State Coverage Verification

**Goal**: demo data must cover all `task.outputs.states` enum values, otherwise cannot demonstrate full business lifecycle.

**Baseline**: task-inventory.json `outputs.states` per entity

**Verification matrix**:
| Entity | Defined State | List Visible | Detail Accessible | Label Correct |
|--------|--------------|-------------|-------------------|---------------|
| Order | PENDING | 3 records | yes | yes |
| Order | PAID | 5 records | yes | yes |
| Order | REFUNDED | 0 records | — | — |
| Order | CANCELED | 1 record | yes | yes |

**Focus on terminal and exception states** (most easily missed):
- REJECTED / CANCELED / EXPIRED / FAILED / CLOSED — specifically check
- Terminal state detail pages must not error or show blank

Missing states → route_to = "design" (demo-plan supplement data chain for that state)

#### V7-C: Data Flow Integrity Tracking

**Goal**: verify demo data business logic chains are coherent — create → flow → approve → complete causal chains unbroken.

**Verification method**:
1. Extract data chain definitions from `demo-plan.json`
2. For each chain, Playwright-verify node by node:
   - User A's action record → appears in User B's to-do list?
   - Parent entity's child list → count and status consistent?
   - Dashboard totals → equal to detail sums?
3. Any chain node data break → route_to = "execute" (population logic issue)

---

### V8: Issue Summary + Routing

**Goal**: aggregate all V1-V7 failures, classify severity, route to corresponding phase.

**Steps**:

1. **Aggregate**: collect all V1-V7 check results
2. **Classify**: for each failure, determine category + severity + route_to

**Routing rules**:

| Issue type | category | route_to | Typical scenario |
|-----------|----------|----------|-----------------|
| Data missing, enum uncovered, chain incomplete | coverage | design | Entity 0 records, missing REJECTED state |
| Image broken, video unplayable, external link, placeholder | media | media | 404, stretch, grey block |
| FK broken, derived mismatch, population failure | data_integrity | execute | Dashboard total != detail sum |
| API 500, frontend render bug, SQL error, code crash | code_bug | dev_task | Application code bug, not data issue |
| UI liveness insufficient (empty list, disabled button, missing state) | liveness | design | Screen action has no data support |
| Data flow broken (causal chain incoherent, related data missing) | data_flow | execute | Parent entity has empty child list |
| Pure style preference, UI micro-adjustment unrelated to data | style_preference | skip | Record but do not route |

3. **6V Deep Diagnosis** (for `code_bug` and `data_integrity` issues):
   - For each high-severity `code_bug` / `data_integrity` issue, diagnose root cause from 6 engineering viewpoints:
     - **V1 Contract**: API signature/response format deviates from `api-contracts.json`?
     - **V2 Conformance**: data violates `entity-model.json` constraints (type/FK/uniqueness)?
     - **V3 Correctness**: business logic correct (amount calculation, state flow rules)?
     - **V4 Consistency**: same operation behaves consistently across pages/roles?
     - **V5 Capability**: data volume/concurrency triggered performance bottleneck?
     - **V6 Context**: error related to specific user role/scenario (permissions/data isolation)?
   - Diagnosis written to issue's `diagnosis` field: `{ "viewpoint": "V2", "root_cause": "...", "fix_hint": "..." }`
   - This gives dev_task issues precise fix hints when routed to dev-forge, beyond surface classification

4. **Output**: write verify-report.json (full) + verify-issues.json (failures + routing + 6V diagnosis)

---

## verify-report.json Structure

```json
{
  "round": 1,
  "timestamp": "ISO8601",
  "app_url": "http://localhost:3000",
  "checks": {
    "v1_login": {
      "status": "passed | partial | failed",
      "roles_checked": [
        {
          "role": "admin",
          "login_success": true,
          "correct_permissions": true,
          "screenshot": "screenshots/v1-round1-admin.png"
        }
      ]
    },
    "v2_list_pages": {
      "status": "passed | partial | failed",
      "pages_checked": [
        {
          "page": "/orders",
          "has_data": true,
          "record_count": 25,
          "sort_correct": true,
          "pagination_ok": true,
          "images_ok": true,
          "no_placeholder_text": true,
          "screenshot": "screenshots/v2-round1-orders.png"
        }
      ]
    },
    "v3_detail_pages": {
      "status": "passed | partial | failed",
      "entities_checked": [
        {
          "entity": "Order",
          "record_id": "ORD-001",
          "fields_complete": true,
          "related_data_present": true,
          "status_history_visible": true,
          "media_loaded": true,
          "screenshot": "screenshots/v3-round1-order-ORD001.png"
        }
      ]
    },
    "v4_dashboards": {
      "status": "passed | partial | failed",
      "dashboards_checked": [
        {
          "dashboard": "sales-overview",
          "numbers_nonzero": true,
          "trend_months": 6,
          "totals_consistent": true,
          "charts_rendered": true,
          "screenshot": "screenshots/v4-round1-sales-overview.png"
        }
      ]
    },
    "v5_edge_cases": {
      "status": "passed | partial | failed",
      "terminal_states_ok": true,
      "search_works": true,
      "boundary_data_ok": true
    },
    "v6_media_integrity": {
      "status": "passed | partial | failed",
      "pages_scanned": 12,
      "total_media_elements": 156,
      "broken_images": 0,
      "external_urls": 0,
      "placeholders": 0,
      "aspect_ratio_issues": 0,
      "video_issues": 0,
      "duplicate_images": 0
    },
    "v7_data_completeness": {
      "status": "passed | partial | failed",
      "ui_liveness": {
        "screens_checked": 15,
        "alive_screens": 13,
        "liveness_rate": "86.7%",
        "dead_screens": [
          { "screen": "Refund approval", "missing_actions": ["Approve", "Reject"], "reason": "No PENDING refund records" }
        ]
      },
      "state_coverage": {
        "entities_checked": 5,
        "total_states": 18,
        "covered_states": 15,
        "missing_states": [
          { "entity": "Order", "state": "REFUNDED", "impact": "Cannot demo refund flow" }
        ]
      },
      "data_flow_integrity": {
        "flows_checked": 4,
        "intact_flows": 3,
        "broken_flows": [
          { "flow": "Order→Pay→Ship", "break_point": "Ship node has no logistics records", "route_to": "execute" }
        ]
      }
    }
  },
  "summary": {
    "total_checks": 86,
    "passed": 82,
    "failed": 4,
    "pass_rate": "95.3%"
  }
}
```

---

## verify-issues.json Structure

```json
{
  "round": 1,
  "timestamp": "ISO8601",
  "summary": {
    "total_checks": 86,
    "passed": 71,
    "failed": 15,
    "pass_rate": "82.6%"
  },
  "issues": [
    {
      "id": "VI-001",
      "category": "media",
      "severity": "high",
      "check_phase": "V6",
      "description": "Product cover image external link residue, src points to picsum.photos",
      "page_url": "/products/123",
      "evidence": "screenshots/v6-round1-product-123.png",
      "route_to": "media",
      "suggested_fix": "media-forge re-acquire product cover and upload through app API"
    },
    {
      "id": "VI-002",
      "category": "data_integrity",
      "severity": "high",
      "check_phase": "V4",
      "description": "Dashboard sales total (98,500) inconsistent with order detail sum (102,300)",
      "page_url": "/dashboard/sales",
      "evidence": "screenshots/v4-round1-sales-overview.png",
      "route_to": "execute",
      "suggested_fix": "Rerun E4 derived data correction, recalculate aggregate fields"
    },
    {
      "id": "VI-003",
      "category": "coverage",
      "severity": "medium",
      "check_phase": "V2",
      "description": "Refund list empty, REFUNDED state has no data coverage",
      "page_url": "/refunds",
      "evidence": "screenshots/v2-round1-refunds.png",
      "route_to": "design",
      "suggested_fix": "demo-plan.json add refund scenario data chain"
    }
  ]
}
```

---

## dev_task Backflow Mechanism

When V7 routing contains `route_to="dev_task"` issues, generate dev-forge compatible fix tasks.

**Task format**:

```markdown
### B-FIX-{N}: {title}

**Source**: demo-verify Round {N}, {issue_id}
**Evidence**: {screenshot_path}
**Description**: {description}
**Acceptance criteria**: {fix description}
```

**Backflow process**:

1. Filter `route_to="dev_task"` from verify-issues.json
2. Generate one B-FIX task per issue
3. Append to `.allforai/project-forge/sub-projects/{name}/tasks.md` B-FIX round
4. Mark issue as `DEFERRED_TO_DEV` in verify-issues.json
5. demo-forge current round does not wait for fix, continues processing other issue types

---

## Screenshot Storage

All screenshots in `.allforai/demo-forge/screenshots/`:

```
.allforai/demo-forge/screenshots/
├── v1-round{N}-{role}.png           # Login verification
├── v2-round{N}-{list_name}.png      # List page verification
├── v3-round{N}-{entity}-{id}.png    # Detail page verification
├── v4-round{N}-{dashboard}.png      # Dashboard verification
├── v5-round{N}-{scenario}.png       # Edge case verification
└── v6-round{N}-{page}-{issue}.png   # Media integrity verification
```

Each round keeps independent screenshots (round number increments) for before/after comparison.

---

## Regression Verification Mode

When running as a regression round, verify only previous round's fix items:

1. Read previous round's verify-issues.json
2. Filter out `route_to="skip"` and `DEFERRED_TO_DEV` items
3. Re-execute corresponding V-check for each item
4. Simultaneously spot-check full regression (ensure fixes didn't introduce new issues)
5. Output new round's verify-report.json + verify-issues.json

---

## Output Files

| File | Location | Description |
|------|----------|-------------|
| verify-report.json | `.allforai/demo-forge/verify-report.json` | Full verification report (V1-V7 all results) |
| verify-issues.json | `.allforai/demo-forge/verify-issues.json` | Failure list + routing targets |
| screenshots/ | `.allforai/demo-forge/screenshots/` | Verification screenshots (by step + round) |
