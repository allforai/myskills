# Pipeline Closure Verify Capability

> Verify that every business flow completes end-to-end in actual code.
> Catches broken pipelines that compile-verify and product-verify miss:
> code exists but the flow never connects from trigger to final result.

## Goal

After code is written, verify that every business pipeline defined in product
artifacts has a complete code path. This is the runtime counterpart of bootstrap
Step 3.1's Functional Pipeline Completeness Check — planning checks "do nodes
exist for each pipeline", this capability checks "does code actually connect".

## What LLM Must Accomplish (not how)

### Required Outputs

| Output | What |
|--------|------|
| `pipeline-closure-report.json` | Per-pipeline verification: complete / broken / partial, with evidence |

**pipeline-closure-report.json field schema:**
```json
{
  "pipelines": [
    {
      "name": "<string — business flow name>",
      "status": "<enum: complete | broken | partial>",
      "stages": [
        {
          "stage": "<enum: trigger | process | store | deliver | display>",
          "exists": "<boolean>",
          "evidence": "<string — file:line or 'missing'>"
        }
      ],
      "broken_at": "<string — first missing stage, null if complete>"
    }
  ],
  "state_machines": [
    {
      "name": "<string — state machine name>",
      "status": "<enum: complete | broken>",
      "missing_transitions": ["<string — transition descriptions>"],
      "missing_behaviors": ["<string — state→behavior mappings not in code>"]
    }
  ],
  "closure_gaps": [
    {
      "feature": "<string>",
      "closure_type": "<enum: config | monitoring | exception | lifecycle | mapping | navigation | multi_surface>",
      "description": "<string — what's missing>",
      "severity": "<enum: high | medium | low>"
    }
  ],
  "summary": {
    "total_pipelines": "<number>",
    "complete": "<number>",
    "broken": "<number>",
    "partial": "<number>",
    "closure_gaps_count": "<number>"
  }
}
```

### Check Dimensions

**1. Business Pipeline Tracing**

For each business flow in product-map or product-concept:
- **Trigger**: Does code exist that initiates this flow? (API endpoint / cron job / event handler / user action)
- **Process**: Does code exist that handles the business logic? (service / handler / worker)
- **Store**: Does code persist the result? (DB write / cache update / file save)
- **Deliver**: Does code notify relevant parties? (push notification / email / WebSocket / API response)
- **Display**: Does client code show the result to the user? (UI component / screen / notification UI)

A pipeline is **broken** if any stage is missing. A pipeline is **partial** if
the stage exists but doesn't connect to the next stage (e.g., API writes to DB
but nothing reads it to push to client).

**2. State Machine Completeness**

For each state machine declared in product-concept (both Category 1 business
and Category 2 adaptive):
- **State storage**: Does code store the current state? (DB field / Redis key)
- **Transitions**: For each declared transition, does code exist that updates the state?
- **Behavior mappings**: For each declared behavior, does code read the state and act on it?

**3. Async Flow Verification**

Specifically check flows that cross process boundaries:
- Payment callbacks: payment initiated → callback URL → order status update
- Push notifications: event occurs → notification generated → delivered to device
- Scheduled jobs: cron trigger → job executes → result stored → user notified
- WebSocket events: server event → broadcast → client handler → UI update

These are the most commonly broken pipelines because they span multiple services
and are easy to forget one end of.

**4. Closure Types Verification**

For each feature in product-concept, verify the 6 closure types have code paths
(runtime counterpart of bootstrap Step 3.5 Level 2):

| Closure Type | Runtime Check |
|-------------|---------------|
| Config Closure | Feature has user-configurable behavior → config file/DB/env var exists + code reads it |
| Monitoring Closure | Feature is business-critical → logging/metrics/error tracking code exists |
| Exception Closure | Feature has known failure modes → error handler + recovery/retry path in code |
| Lifecycle Closure | Feature creates entities → cleanup/archival/expiry code exists |
| Mapping Closure | Feature has A↔B pair → both directions implemented (create↔delete, buy↔refund, follow↔unfollow) |
| Navigation Closure | Feature is UI entry point → exit/back path exists in code |

Report closure gaps alongside pipeline gaps in the same report. A closure gap
is less severe than a broken pipeline (pipeline = flow doesn't work at all,
closure = flow works but is incomplete in edge cases).

**5. Multi-Surface Consistency**

A single piece of data often appears in more than one UI surface — for example
a collection item appears both in a list row (with a summary/preview) and in
a detail view (with full content). When the underlying data mutates, every
surface that renders it must refresh. Single-surface coverage hides bugs where
surface-A is correct but surface-B is stale or empty.

For each entity declared in the product-map (messages, orders, items,
notifications, etc.):
- Enumerate every UI surface that renders any field of that entity
- For every mutation path that writes to the entity (creation / edit / delete)
  verify that each rendering surface receives a refresh signal (reactive
  binding, pub-sub event, list-invalidation, cache key update, etc.)
- Asymmetric coverage — detail updates but list stays stale, or list updates
  but detail stays stale — is a **partial** pipeline. The common offender is
  list-preview / list-summary fields that are updated independently from the
  detail content, and can end up empty because their update path runs in the
  wrong order or not at all.

Report these under `closure_gaps[]` with `closure_type: "multi_surface"`,
naming which surface is stale and why (e.g., "mutation runs INSERT on
details table while list_preview UPDATE expects row to already exist; row
order race").

### Required Quality

- Every business flow from product-map has an explicit verdict (complete/broken/partial)
- Every state machine has transition and behavior coverage checked
- Broken pipelines have specific evidence (which stage is missing, file:line of last connected stage)
- No silent skips — every flow must be checked and reported

## Methodology Guidance (not steps)

- **Artifact-driven**: Read product-map business-flows and product-concept adaptive_systems as the source of truth for what pipelines should exist
- **Code-tracing**: For each pipeline, trace from trigger to display through actual code paths (grep for handler → follow function calls → check DB writes → check notifications)
- **Evidence-based**: Every "exists" claim must have a file:line reference. Every "missing" must explain what was expected and not found.
- **Async focus**: Pay special attention to async flows (callbacks, cron, WebSocket) — these break most often

## Knowledge References

### Phase-Specific:
- cross-phase-protocols.md §Functional-Pipeline: pipeline stages definition
- cross-phase-protocols.md §B.3 Closure-Types: 6 closure types for completeness checking

## Composition Hints

### Single Node (default)
One pipeline-closure-verify node runs after all implementation and demo-forge complete, before concept-acceptance.

### Merge with Product Verify
For simple projects: add pipeline tracing as an additional check dimension within product-verify.

### Skip Entirely
For pure frontend projects, SDK/library projects, or projects with no async flows.
