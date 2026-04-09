# Product Concept Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the product concept loop with bootstrap-time coverage self-check and execution-time concept-acceptance verification.

**Architecture:** Two changes to the meta-skill plugin: (1) insert Step 3.5 into bootstrap.md for coverage self-check, (2) create concept-acceptance.md capability file. Both are pure markdown — no scripts, no code.

**Tech Stack:** Markdown skill files with YAML references

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `claude/meta-skill/skills/bootstrap.md` | Modify | Add Step 3.5, iteration-feedback detection in Step 1.0, concept-acceptance auto-append in Step 1.5, coverage-matrix.json in Step 6.3 |
| `claude/meta-skill/knowledge/capabilities/concept-acceptance.md` | Create | Capability reference for concept-level experience verification |

---

### Task 1: Add iteration-feedback detection to Step 1.0

**Files:**
- Modify: `claude/meta-skill/skills/bootstrap.md:28-40`

- [ ] **Step 1: Add `has_iteration_feedback` detection**

In Step 1.0 "Detect Existing State", after the existing `has_code` line (line 40), add a new detection item. The existing block is:

```markdown
Record what exists:
- `has_product_artifacts`: true if product-map/task-inventory.json exists
- `has_experience_map`: true if experience-map/experience-map.json exists
- `has_bootstrap`: true if bootstrap/workflow.json exists (previous /bootstrap run)
- `has_code`: true if any code files detected in Step 1.1
```

Add after `has_code`:

```markdown
- `has_iteration_feedback`: true if product-concept/iteration-feedback.json exists (previous concept-acceptance feedback)
- `has_product_concept`: true if product-concept/product-concept.json exists
```

- [ ] **Step 2: Add iteration-feedback to Step 1.5 context**

After line 42 ("This affects Step 1.5 options:"), add:

```markdown
- has_iteration_feedback → LLM reads feedback in Step 2, prioritizes fixing previous gaps in Step 3
```

- [ ] **Step 3: Verify change reads correctly**

Read the modified section of bootstrap.md and confirm the new lines integrate naturally with existing content.

- [ ] **Step 4: Commit**

```bash
git add claude/meta-skill/skills/bootstrap.md
git commit -m "feat(meta-skill): detect iteration-feedback in bootstrap Step 1.0"
```

---

### Task 2: Add iteration-feedback loading to Step 2

**Files:**
- Modify: `claude/meta-skill/skills/bootstrap.md:282-315`

- [ ] **Step 1: Add Step 2.5 Load Iteration Feedback**

After Step 2.3 (Load Cross-Phase Knowledge, which ends with loading `product-design-theory.md`), insert a new subsection before Step 2.4:

```markdown
### 2.5 Load Iteration Feedback (if re-bootstrapping)

If `has_iteration_feedback` (from Step 1.0):

Read `.allforai/product-concept/iteration-feedback.json`. This contains:
- Previous concept-acceptance score and verdict
- Gaps found in the last iteration
- Recommended actions (fix_gap, simplify_flow, reconsider_concept, deprioritize)
- User decisions from re-bootstrap

LLM uses this in Step 3 to:
- Prioritize nodes that address previous gaps
- Avoid repeating the same planning mistakes
- If user made decisions (e.g., "move social sharing to post-launch"), respect them

If `has_product_concept` (from Step 1.0):

Read `.allforai/product-concept/product-concept.json`. This is needed for Step 3.5 Coverage Self-Check.
```

- [ ] **Step 2: Renumber existing Step 2.4 if needed**

Check if adding 2.5 conflicts with existing 2.4 (Load Tech Stack Mappings). If 2.4 already exists, insert 2.5 after it — the numbering becomes 2.4, 2.5. No renumbering needed.

- [ ] **Step 3: Verify change reads correctly**

Read the modified section and confirm it flows naturally after 2.3/2.4.

- [ ] **Step 4: Commit**

```bash
git add claude/meta-skill/skills/bootstrap.md
git commit -m "feat(meta-skill): load iteration-feedback in bootstrap Step 2"
```

---

### Task 3: Add concept-acceptance auto-append to Step 1.5 goal mapping

**Files:**
- Modify: `claude/meta-skill/skills/bootstrap.md:181-192`

- [ ] **Step 1: Add concept-acceptance to auto-append rules**

After the existing demo-forge auto-append explanation (line 192), add:

```markdown
- **concept-acceptance is automatically added** to any goal that includes code implementation (translate/rebuild/create) AND `has_product_concept` is true. Reason: without verifying the final product experience against the original concept, the development loop never closes — product-verify checks code vs design artifacts, but not experience vs concept.
```

- [ ] **Step 2: Update goal mapping entries**

Update the goal mappings for b, c, d (lines 182-184) to include concept-acceptance. Change:

```markdown
- (b) → `goals: ["analyze", "translate", "demo"]`, record target_stacks. demo-forge is auto-included because translate produces code that needs integration testing.
- (c) → `goals: ["analyze", "rebuild", "demo"]`, record target_stacks. demo-forge is auto-included because rebuild produces code that needs integration testing.
- (d) → `goals: ["create", "demo"]`, record target_stacks + product_vision. demo-forge is auto-included because new code needs integration testing.
```

To:

```markdown
- (b) → `goals: ["analyze", "translate", "demo", "concept-acceptance"]`, record target_stacks. demo-forge is auto-included because translate produces code that needs integration testing. concept-acceptance is auto-included when product-concept.json exists.
- (c) → `goals: ["analyze", "rebuild", "demo", "concept-acceptance"]`, record target_stacks. demo-forge is auto-included because rebuild produces code that needs integration testing. concept-acceptance is auto-included when product-concept.json exists.
- (d) → `goals: ["create", "demo", "concept-acceptance"]`, record target_stacks + product_vision. demo-forge is auto-included because new code needs integration testing. concept-acceptance is auto-included when product-concept.json exists.
```

- [ ] **Step 3: Verify change reads correctly**

Read lines 180-195 and confirm goal mappings are consistent.

- [ ] **Step 4: Commit**

```bash
git add claude/meta-skill/skills/bootstrap.md
git commit -m "feat(meta-skill): auto-append concept-acceptance to code-producing goals"
```

---

### Task 4: Insert Step 3.5 Coverage Self-Check

**Files:**
- Modify: `claude/meta-skill/skills/bootstrap.md:715` (between Step 3.3 end and Step 3.4)

This is the largest change. Insert the entire Step 3.5 section after the stitch node content (line ~715) and before Step 3.4 "Confirm with User" (line ~716).

- [ ] **Step 1: Insert Step 3.5 section**

Insert the following markdown block between Step 3.3 (ending at the stitch node content) and Step 3.4 (Confirm with User):

```markdown
### 3.5 Coverage Self-Check (Concept → Workflow Closure)

> Goal: Verify that all features in product-concept.json are covered by at least one
> workflow node. Auto-fix gaps using Closure Thinking and Reverse Backfill convergence
> rules. Runs silently — no user confirmation needed.

**Trigger**: `has_product_concept` is true (from Step 1.0). If false, skip to Step 3.4.

#### 3.5.1 Extract Feature Inventory

From `.allforai/product-concept/product-concept.json`, extract all declared features.
Source fields vary by schema — LLM uses semantic understanding, not hardcoded paths:

- `features[]` (structured feature list)
- `errc_highlights.must_have[]` + `errc_highlights.differentiators[]`
- `mvp_features[]` + `post_launch_features[]`
- Any other field that declares "the product will do X"

Output: a flat list of feature descriptions, each a natural-language statement.

#### 3.5.2 Closure-Driven Coverage Check

For each feature, two levels of verification:

**Level 1 — Direct Coverage:**
Does at least one node's `goal`, `exit_artifacts`, or node-spec body semantically
cover this feature? This is LLM semantic judgment, not string matching.

**Level 2 — Closure Completeness (6 types from cross-phase-protocols.md §B.3):**

| Closure Type | Check |
|-------------|-------|
| Config Closure | Feature needs configuration → is there a node for config management? |
| Monitoring Closure | Feature needs observability → is there a node for monitoring setup? |
| Exception Closure | Feature has failure modes → are recovery paths covered by a node? |
| Lifecycle Closure | Feature creates entities → is there cleanup/archival in some node? |
| Mapping Closure | Feature has A↔B pair → is B covered? (e.g., create↔delete, buy↔refund) |
| Navigation Closure | Feature is an entry point → is there an exit path in some node? |

Closure checks are **discovery-level** (as defined in §B.6): identify and mark what
should exist, not exhaustive implementation-level checks.

#### 3.5.3 Convergence-Controlled Auto-Fix

When uncovered features or broken closures are found, LLM decides:

- **Extend existing node** — if the gap is closely related to an existing node's domain
  (same business area, same tech module). Update that node's `goal`, `exit_artifacts`,
  and node-spec.
- **Create new node** — if the gap is a distinct concern not covered by any existing node.
  Append to `workflow.json` nodes[] and generate new node-spec at
  `.allforai/bootstrap/node-specs/<new-id>.md`.

**Convergence rules (from cross-phase-protocols.md §E Reverse Backfill):**

1. **Concept Sets the Boundary** — Only fix gaps derivable from `product-concept.json`.
   Features not in the concept are out of scope.
2. **Derivation Radius Decreases** — Bootstrap only fixes Ring 0 (directly missing
   features) and Ring 1 (first-order closure gaps, e.g., "login" exists → "password
   recovery" missing). Ring 2+ is deferred to execution-phase Reverse Backfill.
3. **Layer Cutoff** — Bootstrap = product design phase boundary. Ring 2+ belongs to
   development phase.

**Stop conditions (any one triggers stop):**

| Condition | Meaning |
|-----------|---------|
| Zero output | All features covered, all closures checked, no new gaps found |
| All downgraded | All remaining gaps are Ring 2+ (beyond bootstrap scope) |
| Scale reversal | A "gap" item's scope exceeds its parent feature → not a gap, it's a new feature |

#### 3.5.4 Write Coverage Matrix

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
```

- [ ] **Step 2: Verify insertion position**

Read the area around Step 3.4 to confirm Step 3.5 is between 3.3 and 3.4, and that Step 3.4 still starts with "### 3.4 Confirm with User".

- [ ] **Step 3: Commit**

```bash
git add claude/meta-skill/skills/bootstrap.md
git commit -m "feat(meta-skill): add Step 3.5 coverage self-check with closure + convergence"
```

---

### Task 5: Add coverage-matrix.json to Step 6.3 write list

**Files:**
- Modify: `claude/meta-skill/skills/bootstrap.md:536-540`

- [ ] **Step 1: Add to file write list**

In Step 6.3 "Write Files", after the existing list item for `workflow.json`, add `coverage-matrix.json`. The existing list is:

```markdown
1. `.allforai/bootstrap/bootstrap-profile.json`
2. `.allforai/bootstrap/workflow.json`
3. `.allforai/bootstrap/node-specs/*.md`
4. `.claude/commands/run.md`
5. `.allforai/bootstrap/scripts/check_artifacts.py`
6. `.allforai/bootstrap/scripts/validate_bootstrap.py`
7. `.allforai/bootstrap/protocols/*.md`
```

Add after item 2:

```markdown
3. `.allforai/bootstrap/coverage-matrix.json` (from Step 3.5, only if product-concept.json exists)
```

Renumber subsequent items (3→4, 4→5, etc.).

- [ ] **Step 2: Update Step 6.4 confirmation output**

In Step 6.4 "Confirm Completion", add coverage-matrix.json to the output listing. After the `workflow.json` line:

```markdown
  .allforai/bootstrap/coverage-matrix.json (覆盖率: {coverage_rate})
```

- [ ] **Step 3: Commit**

```bash
git add claude/meta-skill/skills/bootstrap.md
git commit -m "feat(meta-skill): include coverage-matrix.json in bootstrap output"
```

---

### Task 6: Create concept-acceptance capability file

**Files:**
- Create: `claude/meta-skill/knowledge/capabilities/concept-acceptance.md`

- [ ] **Step 1: Write the capability file**

Create `claude/meta-skill/knowledge/capabilities/concept-acceptance.md` with the following content:

```markdown
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
```

- [ ] **Step 2: Verify file exists and is well-formed**

Read the created file and confirm YAML-compatible structure, all tables render correctly, and JSON examples are valid.

- [ ] **Step 3: Commit**

```bash
git add claude/meta-skill/knowledge/capabilities/concept-acceptance.md
git commit -m "feat(meta-skill): add concept-acceptance capability for concept closure loop"
```

---

### Task 7: Update orchestrator template for concept-acceptance stop behavior

**Files:**
- Modify: `claude/meta-skill/knowledge/orchestrator-template.md:77-82`

- [ ] **Step 1: Add concept-acceptance termination rule**

In the orchestrator template, in the "Termination" section (line ~77), after "All nodes' exit_artifacts exist → success report", add:

```markdown
- concept-acceptance verdict = needs_iteration → output acceptance-report.md, present iteration options (fix/re-bootstrap/accept), stop
```

- [ ] **Step 2: Verify change reads correctly**

Read the Termination section and confirm it integrates with existing rules.

- [ ] **Step 3: Commit**

```bash
git add claude/meta-skill/knowledge/orchestrator-template.md
git commit -m "feat(meta-skill): orchestrator stops on concept-acceptance needs_iteration"
```

---

### Task 8: Final verification — read through all changes

**Files:**
- Read: `claude/meta-skill/skills/bootstrap.md` (Step 1.0, Step 1.5, Step 2, Step 3.5, Step 6.3, Step 6.4)
- Read: `claude/meta-skill/knowledge/capabilities/concept-acceptance.md`
- Read: `claude/meta-skill/knowledge/orchestrator-template.md` (Termination section)

- [ ] **Step 1: Verify bootstrap.md flow**

Read bootstrap.md and trace the full flow:
1. Step 1.0 detects `has_product_concept` and `has_iteration_feedback` ✓
2. Step 1.5 includes concept-acceptance in auto-append goals ✓
3. Step 2.5 loads iteration-feedback.json and product-concept.json ✓
4. Step 3.5 runs coverage self-check with closure + convergence ✓
5. Step 6.3 writes coverage-matrix.json ✓
6. Step 6.4 reports coverage rate ✓

- [ ] **Step 2: Verify concept-acceptance capability**

Read concept-acceptance.md and confirm:
- No hardcoded tools (platform-specific via bootstrap) ✓
- iteration-feedback.json schema matches what Step 2.5 expects to read ✓
- Verdict logic is clear (score >= 80 AND no core gaps) ✓
- Orchestrator stop behavior documented ✓

- [ ] **Step 3: Verify orchestrator template**

Read orchestrator-template.md and confirm concept-acceptance stop rule is in Termination section ✓

- [ ] **Step 4: Cross-check with spec**

Read `docs/superpowers/specs/2026-04-01-bootstrap-coverage-selfcheck-design.md` and verify every spec requirement has a corresponding task in this plan.
