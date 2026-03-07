# v4.1+ Improvement Roadmap

> Date: 2026-03-07
> Status: Proposed
> Prerequisite: v4.0.0 experience-design pipeline

## Already Shipped (v4.0.0)

- screen-map → experience-map, experience-oriented structure
- journey-emotion Phase 3 with human decision point
- interaction-quality-gate Phase 4.5
- design-audit continuity audit dimension

---

## Proposed Improvements

### 1. Design Intent → Code Generation Contracts (Highest Priority)

**Problem:** `tasks.md` specifies component patterns (overlay, bottom sheet, portal) but task-execute may simplify them to plain page routes. Design intent gets lost at the code boundary.

**Solution:** Add `implementation_contract` field to high-risk tasks:

```json
{
  "id": "T003",
  "implementation_contract": {
    "pattern": "bottom-sheet",
    "forbidden": ["page-route", "full-screen-modal"],
    "non_negotiable": ["swipe-to-dismiss", "backdrop-tap-close"],
    "verify": "static-analysis"
  }
}
```

After task-execute generates code, run static analysis to verify compliance. Violations trigger forced fix before continuing.

**Scope:** product-design (contract generation) + dev-forge (contract enforcement in task-execute)

---

### 2. Competitor Analysis via Playwright (Not WebSearch)

**Problem:** Current WebSearch reads secondhand descriptions of competitors, not the actual products. Conclusions are summaries of summaries.

**Solution:** In competitor analysis phases, use Playwright to:
1. Navigate real, publicly accessible competitor products
2. Screenshot key interaction nodes
3. Extract: operation line step count, interaction patterns, feedback mechanisms
4. Produce "first-hand verified" conclusions

**Constraints:**
- auto mode must NOT skip this step
- Only publicly accessible URLs (no login-wall products)
- Output: competitor-interaction-audit.json with screenshots

**Scope:** product-design (feature-gap, feature-prune competitor steps)

---

### 3. Micro-Interaction Specifications

**Problem:** Design spec covers page-level (components + states) but not the micro-interaction layer that determines product feel: animation duration/easing, state change visual feedback, mobile haptic feedback.

**Solution:** Add `micro_interactions` section to ui-design-spec, correlated with emotion nodes:

```json
{
  "screen_id": "S003",
  "micro_interactions": [
    {
      "trigger": "add-to-cart-tap",
      "animation": "scale-bounce",
      "duration_ms": 300,
      "easing": "cubic-bezier(0.34, 1.56, 0.64, 1)",
      "haptic": "impact-medium",
      "emotion_alignment": "satisfying confirmation at anxious moment"
    }
  ]
}
```

Must be mandatory input for task-execute (not optional decoration).

**Scope:** product-design (ui-design generation) + dev-forge (task-execute consumption)

---

### 4. Design Token Single Source of Truth

**Problem:** Design tokens defined in spec doc, manually copied to config files by task-execute. The two copies then evolve independently — drift is inevitable.

**Solution:**
1. Generate `.allforai/ui-design/tokens.json` as canonical source
2. B0 scaffold phase auto-generates framework config from tokens.json (Tailwind config / CSS variables / Flutter theme)
3. Token changes propagate via script: `sync-tokens.py tokens.json → framework config`
4. CI check: diff tokens.json vs generated config, fail on drift

```json
{
  "color": {
    "primary": "#6750A4",
    "secondary": "#625B71"
  },
  "spacing": {
    "unit": 4,
    "scale": [4, 8, 12, 16, 24, 32]
  },
  "radius": {
    "sm": 4, "md": 12, "lg": 16
  },
  "typography": {
    "body": {"size": 16, "weight": 400, "line_height": 24}
  }
}
```

**Scope:** product-design (token generation) + dev-forge (scaffold consumption + sync script)

---

### 5. LLM Cognitive Walkthrough Testing

**Problem:** E2E tests verify features work, but not whether users can discover them. A button may exist and function correctly yet be invisible to real users.

**Solution:** In Phase 8 (design-audit) or as a new Phase 8.5, add LLM-as-user walkthrough:
1. Set LLM persona: role + goal (e.g. "new user, want to place first order")
2. Do NOT provide route names, component IDs, or navigation hints
3. LLM explores via Playwright snapshots autonomously
4. Record: click count to complete task, stuck points, confusion nodes
5. Map findings to experience-map nodes — directly corresponding to real user discoverability issues

**Output:** `cognitive-walkthrough.json` with per-task completion metrics and stuck-point analysis.

**Scope:** product-design (design-audit or new phase) + Playwright MCP

---

### 6. Stitch Unavailability as Explicit Decision Point

**Problem:** When Stitch is unavailable, the pipeline silently falls back. Users may not realize visual quality was never verified.

**Solution:** Before Phase 5-7 parallel execution, if Stitch is unavailable:
1. AskUserQuestion with 3 options:
   - Upload design mockups manually
   - Skip visual acceptance (with explicit acknowledgment)
   - Configure Stitch and continue
2. If skipped: forge-report must prominently mark "Visual quality NOT verified"
3. No silent degradation

**Scope:** product-design (SKILL.md orchestration + ui-design skill)

---

## Priority and Dependency

```
P0: 1. Implementation Contracts     → blocks code quality
P1: 4. Token Single Source          → blocks design-code sync
P1: 3. Micro-Interactions          → blocks product feel
P2: 2. Playwright Competitor Analysis → enhances analysis quality
P2: 5. LLM Cognitive Walkthrough    → enhances usability validation
P3: 6. Stitch Decision Point        → process improvement
```

Items 1 + 4 are cross-plugin (product-design + dev-forge). Items 2 + 5 require Playwright MCP. Item 3 is product-design only. Item 6 is orchestration change only.
