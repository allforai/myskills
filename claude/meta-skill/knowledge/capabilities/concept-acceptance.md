# Concept Acceptance Capability

> Final workflow node. Verify the running product delivers the experience promised
> by product-concept.json. This is NOT code-vs-design verification (that's product-verify)
> — this is experience-vs-concept verification, closing the product iteration loop.

## Goal

After all build/test/demo nodes complete, answer: "Does this product deliver
the value promised in the original concept?" Score the result and produce
actionable feedback for the next iteration.

## Prerequisite

`product-concept.json` must exist. Without it, this capability has no baseline
to verify against. Bootstrap auto-appends this node only when product-concept exists.

## What LLM Must Accomplish (not how)

### Required Outputs

| Output | What |
|--------|------|
| `acceptance-report.json` | Structured scoring across all concept dimensions |
| `acceptance-report.md` | Human-readable summary with gaps and recommendations |
| `iteration-feedback.json` | Written to product-concept/ for next bootstrap cycle |

### Verification Dimensions

| Dimension | Check |
|-----------|-------|
| Value proposition | Is the product positioning reflected in actual functionality? |
| Core features | Every `must_have` feature is functional and accessible? |
| Differentiators | `differentiators` features deliver genuine differentiation, not just exist? |
| Role coverage | Every defined role has a complete usage path? |
| Business model | Key commercial flows (payment, subscription, etc.) work end-to-end? |
| Eliminated items | `errc.eliminate` features confirmed NOT implemented? |

### Required Quality

- Every dimension scored 0-100 with evidence
- Every gap is actionable (type + target + suggestion)
- Verdict is binary: `pass` or `needs_iteration`
- Pass requires: overall_score >= pass_threshold AND zero `core` severity gaps
- pass_threshold defaults to 80, but bootstrap can customize it in the node-spec based on project type (MVP/prototype: 60, standard product: 80, high-bar consumer: 90+)

## Protocol

### Phase 1: Static Verification (LLM Review)

LLM reads all produced artifacts + source code, cross-referenced against
`product-concept.json`. For each dimension, judge whether the implementation
faithfully delivers the concept's intent. Not mechanical matching — semantic
judgment of whether the product experience matches the concept promise.

### Phase 2: Dynamic Verification (E2E Experience)

Platform-specific — bootstrap generates the concrete tool in the node-spec
based on `bootstrap-profile.json` tech_stacks. This capability defines
principles only:

| Module Type | Tool (selected by bootstrap) |
|-------------|------------------------------|
| Web (Next.js, React, Vue) | Playwright |
| Flutter mobile | flutter test integration_test/ |
| React Native | Detox / Maestro |
| iOS native (SwiftUI) | XCUITest |
| Android native (Kotlin) | Espresso |
| API-only backend | curl / HTTP client |
| CLI tool | Shell script execution |
| Desktop (Electron, Tauri) | Platform-specific E2E |

For each role defined in product-concept.json:

**Single-client roles** (legacy `client_type` field):
1. Authenticate as that role (using demo-forge seeded credentials)
2. Walk through each core flow end-to-end
3. Capture evidence (screenshots/recordings/logs per platform)
4. Score: completeness (can the flow be completed?) + fluency (unnecessary steps,
   dead ends, confusion?)

**Multi-client roles** (`clients[]` array with `feature_parity`):
For EACH client declared in the role:
1. Use the appropriate E2E tool for that client's `client_type` (see table above)
2. Authenticate as that role on THIS specific client
3. Walk through each core flow end-to-end on THIS client
4. Capture evidence per client
5. Score per client: completeness + fluency

After all clients are tested, perform **parity check**:
- `feature_parity: full` → every feature must work on every client
- `feature_parity: partial` → every feature must work on every client, except those in `parity_exceptions`
- `feature_parity: explicit` → each client is tested ONLY on its declared `supported_features[]`.
  Score per client reflects only those features. A voice client scoring 90 on 3 features
  is not compared against an iOS client scoring 85 on 10 features — different scopes.
- Score parity: flag significant score differences between clients for the same flow
  (e.g., buyer-ios: 90, buyer-web: 60 → flag as "web experience significantly worse")
- Parity failures are reported as gaps with severity based on the feature's importance

### Phase 2.5: Adaptive Behavior Verification (when concept has adaptive_systems)

If `product-concept.json` contains `adaptive_systems[]`, verify that state machines
actually work at runtime — not just that the code exists, but that behaviors change
based on state.

For each adaptive system:

1. **Trigger state transitions**: use demo-forge seeded data or live interaction to
   trigger events defined in `transitions[]`. Example: submit 5 wrong answers to
   trigger frustration_index increase.

2. **Verify state updates**: after triggering events, read the user's state from the
   API or database. Confirm dimensions were updated as expected.

3. **Verify behavior changes**: after state changes, trigger the behavior that reads
   that state. Confirm the output differs from the default. Example: after
   frustration_index > 0.7, the next exercise should be easier than before.

4. **Test boundary conditions**:
   - New user (all dimensions at initial values) → default behavior correct?
   - Edge values (mastery = 0.0, mastery = 1.0) → no crashes, reasonable behavior?
   - State regression (user was advanced, now answers wrong) → difficulty decreases?

Evidence format: for each adaptive system, record a before/after state snapshot
with the triggering events and observed behavior change. This is the strongest
proof that personalization works — static code review cannot verify this.

**MVP scope**: only verify behavior_mappings that reference MVP features. Mappings
that reference post_launch features are skipped (flagged by Step 3.5 Level 4 as
"premature mapping").

### Phase 3: Scoring and Verdict

Aggregate dimension scores into overall_score. Apply verdict logic:
- `pass`: overall_score >= pass_threshold AND no `core` severity gaps
- `needs_iteration`: overall_score < pass_threshold OR any `core` severity gap

### Phase 4: Iteration Feedback

Write `.allforai/product-concept/iteration-feedback.json`:

```json
{
  "iteration": 1,
  "feedback_at": "<ISO timestamp>",
  "source": "concept-acceptance",
  "overall_score": 78,
  "verdict": "needs_iteration",
  "gaps": [
    {
      "feature": "<feature name>",
      "severity": "core | important | minor",
      "status": "not_implemented | partial | poor_experience",
      "detail": "<what's wrong>"
    }
  ],
  "recommended_actions": [
    {
      "type": "fix_gap | simplify_flow | reconsider_concept | deprioritize",
      "target": "<feature or flow name>",
      "suggestion": "<actionable recommendation>"
    }
  ],
  "user_decisions": []
}
```

Archive previous feedback to `.allforai/product-concept/iteration-history/iteration-{N}.json`.

**Always write feedback**, regardless of verdict. On `pass`, gaps[] and recommended_actions[]
will be empty or contain only minor items — the file serves as audit trail for the iteration.

### Phase 5: Human Intervention (orchestrator responsibility)

When verdict = `pass`: orchestrator proceeds to normal completion (success report).
No human intervention needed. The iteration loop is closed.

When verdict = `needs_iteration`, the orchestrator (run.md) must:

1. Output acceptance-report.md summary
2. Stop execution
3. Present options:
   - a) Fix gaps then re-verify → `/run concept-acceptance`
   - b) Adjust concept then re-bootstrap → edit product-concept.json, `/bootstrap`
   - c) Accept current state → mark as v1

This is the orchestrator's job, not the subagent's. The subagent produces the
report and feedback; the orchestrator decides whether to stop.

## Rules (Must Preserve)

1. **Static before dynamic**: Cheaper checks first, catch obvious gaps early.
2. **Per-role verification**: Each role's journey tested independently.
3. **Concept is the baseline**: Not design artifacts, not code structure — the original
   product concept is the single source of truth for this verification.
4. **Evidence-based**: Each dimension score must cite specific evidence (screenshots,
   code paths, test results).
5. **Feedback is structured**: iteration-feedback.json must be machine-readable so
   the next bootstrap can consume it automatically.

## Knowledge References

### Phase-Specific:
- cross-phase-protocols.md §A: Push-Pull for loading concept baseline
- cross-phase-protocols.md §B: 4D+6V+Closure for verification rigor
- cross-phase-protocols.md §C: Upstream Baseline Validation (concept = ultimate upstream)
- consumer-maturity-patterns.md: consumer maturity scoring for experience quality

## Composition Hints

### Single Node (default)
Run after all build/test/demo/verify nodes complete. Final node in workflow.

### Split Static vs Dynamic
For large multi-platform projects: static verification as one node, dynamic per platform.

### Skip Entirely
When `product-concept.json` does not exist (pure code analysis, tune, quality-checks goals).
