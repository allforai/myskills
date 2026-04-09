# Product Concept Closure Design

> Two mechanisms that close the concept-to-product loop: (1) bootstrap-time coverage self-check ensures all concept features are planned into workflow nodes, (2) concept-acceptance capability verifies the final product experience against the original concept, with iteration feedback for re-bootstrap.

## Problem

Two gaps break the product concept closure loop:

1. **Planning gap**: Bootstrap Step 3 relies on LLM free planning. No verification that planned nodes cover all features in `product-concept.json`. Missing features are only discoverable during execution — too late.

2. **Experience gap**: After build/test/demo complete, `product-verify` checks code against design artifacts (experience-map, task-inventory), but never closes back to `product-concept.json`. The final product may implement all screens correctly yet fail to deliver the original value proposition.

```
product-concept.json
    ↓ bootstrap (GAP 1: planning coverage)
workflow nodes → /run → build → test → demo
    ↓ product-verify (checks code vs design artifacts)
    ↓ (GAP 2: no concept-level experience verification)
    ✗ loop never closes back to product-concept.json
```

## Solution

Two complementary mechanisms:

1. **Step 3.5: Coverage Self-Check** — bootstrap-time, ensures all concept features have workflow nodes
2. **concept-acceptance capability** — execution-time final node, verifies product experience against concept, with iteration feedback

```
product-concept.json
    ↓ Step 3.5 coverage check (planning gap closed)
workflow nodes
    ↓ /run
build → test → demo
    ↓
concept-acceptance (experience gap closed)
    ↓ pass → done
    ↓ needs_iteration → stop, human decides
iteration-feedback.json
    ↓ user adjusts concept
re-bootstrap (auto-reads feedback)
    ↓
next iteration
```

---

## Part 1: Step 3.5 Coverage Self-Check

### Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Source | `product-concept.json` only | Without structured concept, no meaningful coverage check |
| No concept → behavior | Skip Step 3.5 entirely | No interruption, no degraded mode |
| User confirmation | None | Must not interrupt bootstrap flow |
| Uncovered features | LLM auto-adds/extends nodes | Fully automatic |
| Check method | Pure LLM semantic judgment | Feature descriptions are natural language |
| Convergence | Reuse existing Closure + Backfill rules | Unified with execution-phase mechanisms |

### Trigger

After Step 3.3 (Pre-Generate Node-Specs) completes. Pre-check: does `.allforai/product-concept/product-concept.json` exist?

- Yes → execute Step 3.5
- No → skip to Step 3.4

### 3.5.1 Extract Feature Inventory

From `product-concept.json`, LLM extracts all declared features. Source fields vary by schema (LLM semantic understanding, not hardcoded paths):

- `features[]` (structured feature list)
- `errc_highlights.must_have[]` + `errc_highlights.differentiators[]`
- `mvp_features[]` + `post_launch_features[]`
- Any other field that declares "the product will do X"

Output: a flat list of feature descriptions, each a natural-language statement.

### 3.5.2 Closure-Driven Coverage Check

For each feature, two levels of verification:

**Level 1 — Direct Coverage:**
Does at least one node's `goal`, `exit_artifacts`, or node-spec body semantically cover this feature?

**Level 2 — Closure Completeness (6 types from cross-phase-protocols.md §B.3):**

| Closure Type | Check |
|-------------|-------|
| Config Closure | Feature needs configuration → is there a node for config management? |
| Monitoring Closure | Feature needs observability → is there a node for monitoring setup? |
| Exception Closure | Feature has failure modes → are recovery paths covered by a node? |
| Lifecycle Closure | Feature creates entities → is there cleanup/archival in some node? |
| Mapping Closure | Feature has A↔B pair → is B covered? (e.g., create↔delete, buy↔refund) |
| Navigation Closure | Feature is an entry point → is there an exit path in some node? |

Closure checks are discovery-level (as defined in §B.6 Phase Transition Mindset): identify and mark what should exist, not exhaustive implementation-level checks.

### 3.5.3 Convergence-Controlled Auto-Fix

When uncovered features or broken closures are found, LLM decides:

- **Extend existing node** — if the gap is closely related to an existing node's domain (same business area, same tech module). Update that node's `goal`, `exit_artifacts`, and node-spec.
- **Create new node** — if the gap is a distinct concern not covered by any existing node. Append to `workflow.json` nodes[] and generate new node-spec.

**Convergence rules (from cross-phase-protocols.md §E Reverse Backfill):**

1. **Concept Sets the Boundary** — Only fix gaps derivable from `product-concept.json`. Features not in the concept are out of scope.
2. **Derivation Radius Decreases** — Bootstrap only fixes Ring 0 (directly missing features) and Ring 1 (first-order closure gaps, e.g., "login" exists → "password recovery" missing). Ring 2+ is deferred to execution-phase Reverse Backfill.
3. **Layer Cutoff** — Bootstrap = product design phase boundary. Ring 2+ belongs to development phase.

**Stop conditions (any one triggers stop):**

| Condition | Meaning |
|-----------|---------|
| Zero output | All features covered, all closures checked, no new gaps found |
| All downgraded | All remaining gaps are Ring 2+ (beyond bootstrap scope) |
| Scale reversal | A "gap" item's scope exceeds its parent feature → not a gap, it's a new feature |

### 3.5.4 Audit Record

Write `.allforai/bootstrap/coverage-matrix.json`:

```json
{
  "source": "product-concept.json",
  "checked_at": "<ISO timestamp>",
  "total_features": 25,
  "covered_before_check": 22,
  "auto_fixed": 3,
  "deferred_ring2_plus": 1,
  "final_coverage_rate": "100%",
  "matrix": [
    {
      "feature": "<feature description>",
      "covered_by": ["<node-id>"],
      "status": "covered"
    },
    {
      "feature": "<feature description>",
      "closure_type": "exception",
      "derived_from": "<parent feature>",
      "ring": 1,
      "status": "auto_added",
      "action": "extended node <node-id>"
    },
    {
      "feature": "<feature description>",
      "ring": 2,
      "status": "deferred",
      "reason": "ring2_cutoff | scale_reversal | all_downgraded"
    }
  ]
}
```

---

## Part 2: concept-acceptance Capability

### Purpose

Final workflow node. After all build/test/demo nodes complete, verify the running product delivers the experience promised by `product-concept.json`. This is NOT code-vs-design verification (that's product-verify) — this is experience-vs-concept verification.

### Trigger in Workflow

Bootstrap Step 3 auto-appends a concept-acceptance node to the workflow when:
- Goals include code-producing work (translate/rebuild/create), AND
- `product-concept.json` exists

Same auto-append pattern as demo-forge.

### Static Verification (LLM Review)

LLM reads all produced artifacts + code, cross-referenced against `product-concept.json`:

| Dimension | Check |
|-----------|-------|
| Value proposition | Is the product positioning reflected in actual functionality? |
| Core features | Every `must_have` feature is functional and accessible? |
| Differentiators | `differentiators` features deliver genuine differentiation, not just exist? |
| Role coverage | Every defined role has a complete usage path? |
| Business model | Key commercial flows (payment, subscription, etc.) work end-to-end? |
| Eliminated items | `errc.eliminate` features confirmed NOT implemented? |

### Dynamic Verification (E2E Experience)

Platform-specific — bootstrap generates the concrete tool in the node-spec based on `bootstrap-profile.json` tech_stacks. The capability defines principles only:

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
4. Score: completeness (can the flow be completed?) + fluency (any unnecessary steps, dead ends, confusion?)

### Output Artifacts

```
.allforai/concept-acceptance/
├── acceptance-report.json    # Structured scoring
└── acceptance-report.md      # Human-readable summary
```

**acceptance-report.json:**

```json
{
  "source": "product-concept.json",
  "verified_at": "<ISO timestamp>",
  "iteration": 1,
  "overall_score": 78,
  "pass_threshold": 80,
  "verdict": "pass | needs_iteration",
  "dimensions": [
    {
      "dimension": "value_proposition | core_features | differentiators | role_coverage | business_model | eliminated_items",
      "score": 85,
      "evidence": "<summary of what was checked>",
      "gaps": [
        {
          "feature": "<feature name>",
          "status": "not_implemented | partial | poor_experience",
          "severity": "core | important | minor",
          "detail": "<what's wrong>"
        }
      ]
    }
  ],
  "iteration_feedback": {
    "recommended_actions": [
      {
        "type": "fix_gap | simplify_flow | reconsider_concept | deprioritize",
        "target": "<feature or flow name>",
        "suggestion": "<actionable recommendation>"
      }
    ]
  }
}
```

**Verdict logic:**
- `pass` — overall_score >= pass_threshold AND no `core` severity gaps
- `needs_iteration` — overall_score < pass_threshold OR any `core` severity gap exists

### Human Intervention Point

When verdict = `needs_iteration`, orchestrator:

1. Outputs acceptance-report.md summary
2. Stops execution
3. Presents options:

```
概念验收未通过（得分 78/80）。

核心差距：
  - 密码找回未实现
  - 结算流程体验不佳（5步→建议3步）

建议操作：
  a) 修复差距后重新验收 → /run concept-acceptance
  b) 调整产品概念后重新 bootstrap → 编辑 product-concept.json 后 /bootstrap
  c) 接受当前状态 → 标记为 v1 发布
```

User decides. No automatic action.

---

## Part 3: Iteration Feedback Mechanism

### Feedback Persistence

When concept-acceptance completes (regardless of verdict), write `.allforai/product-concept/iteration-feedback.json`:

```json
{
  "iteration": 1,
  "feedback_at": "<ISO timestamp>",
  "source": "concept-acceptance",
  "overall_score": 78,
  "verdict": "needs_iteration",
  "gaps": [
    {
      "feature": "密码找回",
      "severity": "core",
      "status": "not_implemented"
    }
  ],
  "recommended_actions": [
    {
      "type": "fix_gap",
      "target": "密码找回",
      "suggestion": "implement-auth 节点遗漏了此功能"
    }
  ],
  "user_decisions": []
}
```

`user_decisions` is populated by the next bootstrap run after the user acts.

### Bootstrap Auto-Read

Bootstrap Step 1.0 (Detect Existing State) adds:

```
has_iteration_feedback: true if product-concept/iteration-feedback.json exists
```

Bootstrap Step 2 (Load Knowledge) auto-loads `iteration-feedback.json` when present.

Bootstrap Step 3 (Plan Workflow) uses the feedback to:
- Prioritize nodes that address previous gaps
- Avoid repeating the same planning mistakes
- Record user decisions from this round in `iteration-feedback.json` → `user_decisions[]`

### Iteration Counter

Each concept-acceptance run increments the iteration counter. History is preserved:

```
.allforai/product-concept/
├── iteration-feedback.json           # Current (latest) feedback
└── iteration-history/
    ├── iteration-1.json              # Archived after iteration 2 starts
    └── iteration-2.json              # Archived after iteration 3 starts
```

---

## Change Scope

| File | Change |
|------|--------|
| `claude/meta-skill/skills/bootstrap.md` | Step 1.0: detect iteration-feedback. Step 2: auto-load feedback. Step 3: auto-append concept-acceptance node. Step 3.5: coverage self-check. Step 6.3: add coverage-matrix.json to write list. |
| `claude/meta-skill/knowledge/capabilities/concept-acceptance.md` | **New file.** Capability reference for concept-level experience verification. |

Two files total: one modified, one new.

## Relationship to Existing Mechanisms

```
                    Bootstrap Phase                    Execution Phase
                    ──────────────                     ───────────────
Planning coverage:  Step 3.5 Coverage Self-Check       §E Reverse Backfill
                    Ring 0 + Ring 1                    Ring 2+
                    Closure discovery-level            Closure implementation-level
                    → coverage-matrix.json             → negative-space-supplement.json

Code verification:  (n/a)                              product-verify
                                                       code vs design artifacts
                                                       → verify-report.json

Experience closure: (n/a)                              concept-acceptance (NEW)
                                                       product experience vs concept
                                                       → acceptance-report.json

Iteration loop:     bootstrap reads                    concept-acceptance writes
                    iteration-feedback.json            iteration-feedback.json
```

The three verification layers form a complete pyramid:
1. **Planning** (Step 3.5): are we building the right things?
2. **Implementation** (product-verify): did we build them correctly?
3. **Experience** (concept-acceptance): does the result deliver the promised value?
