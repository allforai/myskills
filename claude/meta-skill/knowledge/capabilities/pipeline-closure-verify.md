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
  "summary": {
    "total_pipelines": "<number>",
    "complete": "<number>",
    "broken": "<number>",
    "partial": "<number>"
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
