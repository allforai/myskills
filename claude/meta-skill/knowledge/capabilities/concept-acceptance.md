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
- Pass requires: overall_score >= 80 AND zero `core` severity gaps

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
1. Authenticate as that role (using demo-forge seeded credentials)
2. Walk through each core flow end-to-end
3. Capture evidence (screenshots/recordings/logs per platform)
4. Score: completeness (can the flow be completed?) + fluency (unnecessary steps,
   dead ends, confusion?)

### Phase 3: Scoring and Verdict

Aggregate dimension scores into overall_score. Apply verdict logic:
- `pass`: overall_score >= 80 AND no `core` severity gaps
- `needs_iteration`: overall_score < 80 OR any `core` severity gap

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

### Phase 5: Human Intervention (orchestrator responsibility)

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
