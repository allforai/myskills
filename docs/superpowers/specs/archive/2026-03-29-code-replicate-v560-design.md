# code-replicate v5.6.0 Design Spec

> Based on real-world feedback from a cross-framework replication project (Flutter → WPF/.NET, 78 files / 19000+ lines).

## Problem Statement

code-replicate v5.5.2 achieved cr-fidelity static 87 / runtime 94 on a large module, but after adding the previously skipped U (UI) dimensions, the composite score dropped from 93 to 82 — below the 90 threshold. Root cause: 39 user-visible features were missed (primarily UI interactions), while 14 features were incorrectly flagged as missing by analysis that didn't read the code.

Six interconnected issues identified, plus one architectural improvement (adaptive source access), addressed through LLM reasoning enhancement rather than hardcoded rules.

## Design Principle

**LLM reasoning over rigid rules.** Only two categories get hard validation:

1. **Silent failures** — when the system skips work without reporting it (#4, #6)
2. **Everything else** — solved via self-review prompts, reasoning examples, and adaptive depth decisions

No project-specific thresholds (e.g., "≥30% coverage", "lines < 50 = stub"). All judgments made by LLM based on the specific project's characteristics.

---

## Change 1: Extraction Plan Self-Review (P0)

**File**: `skills/code-replicate-core.md` — Phase 3-pre, after extraction-plan.json generation

**Problem**: A 78-file module got only 4 key_files (5%). Features distributed across sub-widgets/sub-views were systematically missed because extraction-plan sources only pointed to top-level entry files.

**Design**: Insert EXTRACTION_PLAN_REVIEW step where LLM switches to reviewer perspective and examines its own plan for blind spots.

### LLM outputs `plan_review` for each module:

```json
{
  "review_perspective": "extraction-plan audit",
  "modules_examined": [
    {
      "module": "M003",
      "total_files": 78,
      "key_files_selected": 4,
      "coverage_assessment": "key_files only cover top-level entries (main widget + state management). Sub-directory widgets/message_types/ has 24 files handling distinct message type rendering. chat_input/ has 8 files for input interactions (voice, drag, paste, emoji). These sub-files contain independent user-visible features not covered by top-level entries.",
      "blind_spots": [
        "widgets/message_types/*.dart — 74 message type rendering branches",
        "chat_input/voice_recorder.dart — voice recording feature",
        "chat_input/file_drop_handler.dart — drag-and-drop file send",
        "overlays/ — popup interactions (emoji picker, @mention, forward panel)"
      ],
      "decision": "Expand key_files: trace import chains from entry files, add sub-files carrying independent user features. Estimated 4 → 22.",
      "rationale": "These are not utility files — each carries a user-perceivable feature. Missing any = target product lacks that feature."
    }
  ],
  "overall_confidence": "Post-review coverage from 5% to 28%. Remaining 72% are utility/model/config files without independent user features."
}
```

### Review reasoning guidelines (not hard thresholds):

- **User-impact test**: For each module, ask: "If a user opens the target app, which features would be missing due to uncovered key_files?"
- **Import chain tracing**: From each key_file, follow imports one level down. Check if referenced files carry independent features (vs pure utilities).
- **Enum/switch detection**: If a key_file contains switch(type) with > 5 cases, each case's rendering file is worth including.
- **Sub-directory sampling**: For sub-directories not reached by import chains, read the first 3 files' headers (class name + public method signatures) to check for missed user features.

---

## Change 2: Experience Map Adaptive Depth (P0)

**Files**: `skills/code-replicate-core.md` (Phase 3 experience-map generation) + `docs/schema-reference.md` (schema extension)

**Problem**: experience-map.json stayed at stub fidelity — each screen listed only top-level component names. Lost: interaction events (click/drop/longpress/keydown/paste), state variants (loading/empty/error/disabled), and enum-driven rendering branches (74 message types collapsed into one component).

**Design**: LLM autonomously decides analysis depth per screen, outputting a `depth_decision`. When depth = deep, two new schema fields are populated.

### Per-screen depth decision:

```json
{
  "screen": "chat_main",
  "depth": "deep",
  "depth_reasoning": "Core component MessageList has switch(message.type) with 74 branches, each with independent interaction behavior (image→tap to fullscreen, voice→longpress to play, file→drag to download, location→embedded map). Stub level can only record 'MessageList exists', cannot distinguish 74 different user experiences.",
  "complexity_signals": [
    "switch/enum branches: 74",
    "distinct interaction event types: click/longpress/drag/paste/keydown",
    "state variants: loading/sending/failed/recalled/expired"
  ]
}
```

### Signals LLM uses to decide depth (not rules):

- Screen's source file imports > 10 files → likely needs deep
- Contains switch/if-else chain with > 5 branches → suggests deep
- Component has multiple interaction events (not just click) → suggests deep
- Pure display screen (settings, about page) → stub sufficient

### New schema fields (optional, populated when depth = deep):

**`interaction_triggers`** on `components[]`:

```json
{
  "component": "MessageBubble",
  "interaction_triggers": [
    {"trigger": "tap", "target": "image message", "response": "fullscreen preview"},
    {"trigger": "long_press", "target": "any message", "response": "action menu (forward/save/delete)"},
    {"trigger": "double_tap", "target": "text message", "response": "text selection mode"}
  ]
}
```

**`state_variants`** on `components[]`:

```json
{
  "component": "VoiceMessage",
  "state_variants": [
    {"state": "recording", "visual": "red pulse animation + duration counter"},
    {"state": "recorded_preview", "visual": "waveform + play/delete buttons"},
    {"state": "sending", "visual": "upload progress bar"},
    {"state": "sent", "visual": "static waveform + duration label"},
    {"state": "playing", "visual": "playback progress animation + pause button"},
    {"state": "expired", "visual": "greyed out + 'expired' label"}
  ]
}
```

### Enum-driven rendering expansion:

When switch/enum pattern detected with > 5 branches, LLM expands each branch into an independent component or variant entry rather than collapsing into a single generic component.

### Backward compatibility:

Both fields are optional. Stub-level screens omit them. Existing consumers of experience-map.json are unaffected.

### Schema ownership note:

The canonical experience-map schema is owned by product-design-skill. These new fields (`interaction_triggers`, `state_variants`) are **code-replicate extensions** — optional fields that code-replicate populates but product-design does not. Documented in code-replicate's `docs/schema-reference.md` with a cross-reference note: "Extended fields beyond product-design base schema."

---

## Change 3: UI Layer Reasoning in Analysis Principles (P1)

**File**: `docs/analysis-principles.md` — new 7th principle

**Problem**: The "extract business intent, not implementation decisions" principle worked for backend (replacing ORM/DB is reasonable) but caused LLM to misclassify UI features as "implementation decisions" — drag-and-drop file send, emoji picker, clipboard paste image, voice recording, fullscreen preview all got dropped.

**Design**: Add principle #7 "Identifying User-Perceivable Capabilities" with reasoning framework, examples, and the "disappearance test".

### The Disappearance Test:

> "If this capability vanishes from the target application, would an end user notice during normal usage?"
> - Would notice → **user feature** (must extract)
> - Would not notice → **implementation detail** (replaceable)

### Reasoning examples:

| Capability | Disappearance Test | Classification |
|------------|-------------------|---------------|
| Drag file to send | User could do it before, can't now → notices | User feature |
| Emoji picker | User could pick emojis, now can't → notices | User feature |
| Clipboard paste image | Ctrl+V worked before, doesn't now → notices | User feature |
| Voice record/play | User could send voice, now can't → notices | User feature |
| Fullscreen image preview | User could tap to enlarge, now can't → notices | User feature |
| BLoC vs Provider state management | Same UX either way → doesn't notice | Implementation detail |
| GridView vs ListView rendering | Same data and interaction → doesn't notice | Implementation detail |
| Long-press menu with 6 options | User had 6 actions, now has 2 → notices | Each option = user feature |

### Three-Layer Model (reasoning aid, not rigid classification):

1. **User Capability Layer** (What + How user triggers it) — must extract to task-inventory / experience-map
   - Examples: send voice message, fullscreen preview, drag-sort list
2. **Interaction Implementation Layer** (Which library/component) — record in stack-mapping, replaceable in target
   - Examples: flutter_sound vs just_audio, Hero animation vs custom transition
3. **Code Structure Layer** (Code patterns/architecture) — do not copy
   - Examples: BLoC vs MVVM, single-file vs split components, mixin vs inheritance

### Boundary disambiguation:

> When unsure, apply the "apology test": if this capability disappears, would you need to apologize to users in release notes? If yes → user feature. If only developers would notice in code review → implementation detail.

---

## Change 4: Dimension Applicability Reasoning in cr-fidelity (P1)

**File**: `skills/cr-fidelity.md` — Phase 0 dimension selection

**Problem**: experience-map.json existed, U1-U6 should have been enabled, but the previous analysis silently skipped all UI dimensions, producing a 93 score. With U dimensions included, actual score was 82. Problem was hidden until user manually discovered it.

**Design**: Replace mechanical "artifact exists → enable dimension" mapping with LLM reasoning about each dimension group's applicability and importance for this specific project.

### Dimension applicability reasoning:

For each dimension group (F/U/I/A/B), LLM outputs:

```json
{
  "dimension_group": "U",
  "applicable": true,
  "reasoning": "experience-map.json contains 12 screen definitions, 8 with components and actions fields. Target is WPF desktop app where UI is the primary value delivery layer. Skipping U dimensions would leave ~40% of functional coverage unassessed.",
  "artifacts_examined": ["experience-map.json", "source-summary.json"],
  "risk_if_skipped": "high — 12 screens with 40+ components would escape evaluation"
}
```

### Self-contradiction detection:

If `risk_if_skipped = high` AND `applicable = false` → triggers CONTRADICTION warning. LLM must re-examine its reasoning (not auto-flip, but reconsider). Reconsideration is **one-shot**: if LLM reaches the same conclusion after re-examination, the decision stands with `contradiction_acknowledged: true` in the output.

### Dynamic weight reasoning:

LLM must explain weight allocation for the composite score:

> "This project is ~60% UI / ~40% backend. U dimensions weight adjusted from default 1.0 to 1.2. F dimensions remain at 1.0."

Weights determined by LLM reasoning about the project, not a fixed formula. A pure API backend and a UI-heavy chat app should have completely different dimension weights.

**Scoring formula change**: Simple average `sum(scores) / N` replaced with weighted average `sum(score_i × weight_i) / sum(weight_i)`. Weights and reasoning persisted in `fidelity-report.json` under `dimension_reasoning[]` for traceability.

### No silent skipping:

Every dimension group must appear in `dimension_reasoning[]` — either as `applicable: true` (scored) or `applicable: false` (with explicit reasoning and risk assessment). No dimension group may be absent from the report.

---

## Change 5: Screenshot Unavailability Compensation (P1)

**Files**: `skills/cr-visual.md` + `docs/cr-visual/step-capture.md`

**Problem**: Phase 2.13 screenshots are the last line of defense for UI verification. For desktop apps requiring specific OS environments, screenshot capture may be impossible, causing this safety net to fail silently.

**Design**: When screenshots are unavailable, LLM autonomously decides compensation strategy instead of failing or silently continuing.

### CAPTURE_UNAVAILABLE handling:

```json
{
  "capture_status": {
    "source_screenshots": "unavailable",
    "target_screenshots": "available",
    "reason": "Source app is Flutter iOS, no iOS simulator in current environment"
  },
  "compensation_strategy": {
    "reasoning": "Screenshots are the last defense for UI verification. Missing source screenshots means visual comparison impossible. Must compensate this information gap through other means.",
    "actions": [
      {
        "action": "Upgrade experience-map analysis depth",
        "detail": "Promote all depth=stub screens to deep. Supplement interaction_triggers and state_variants through deeper code reading.",
        "rationale": "What screenshots reveal at a glance must now be reconstructed from code"
      },
      {
        "action": "Build textual screen descriptions",
        "detail": "For each screen, generate natural language description: 'Chat main: top nav bar (back + title + more menu), center message list (reverse chronological, each with avatar + bubble + time), bottom input bar (emoji + attach + input field + send button)'",
        "rationale": "Serves as screenshot substitute for structural comparison"
      },
      {
        "action": "Elevate Completeness Sweep Dimension B",
        "detail": "User journey walkthrough upgraded from auxiliary to primary verification. Every role's journey steps must be individually verified.",
        "rationale": "Without screenshots, journey walkthrough is the only experience-level validation"
      }
    ],
    "residual_risk": "Cannot verify pixel-level visual restoration (colors/spacing/fonts). Only functional and interaction completeness verifiable. Recommend user run /cr-visual analyze when target environment becomes available.",
    "screenshot_coverage": "0% (source) / 100% (target)",
    "confidence_adjustment": "Visual dimension confidence downgraded from high to medium. Report marked VISUAL_PARTIALLY_VERIFIED."
  }
}
```

LLM freely combines compensation actions based on the specific unavailability scenario. Core principle: **missing screenshots → compensate with deeper code comprehension.**

### Exit behavior change in step-capture.md:

Current behavior: "无截图可用 → 报错退出" applies unconditionally. Modified to:
- **Both** source AND target screenshots unavailable → error exit (unchanged — nothing to compare)
- **Only source** unavailable → activate compensation strategy (new behavior above)
- **Only target** unavailable → error exit with message "target app must be runnable for visual verification"

---

## Change 6: Code Comprehension Evidence in Scoring (P1 → bug fix)

**File**: `docs/fidelity/static-dimensions.md`

**Problem**: An external analysis report labeled a 500-750 line complete ViewModel as "empty shell ~5% completion". 14 actually-implemented features were misjudged as missing. The "read first, score second" rule exists but lacks enforcement.

**Design**: Require LLM to produce code comprehension summaries proving it understood what the code does, not just that files exist.

### Evidence structure for each scoring item:

```json
{
  "item": "OrderViewModel — order management",
  "verdict": "implemented",
  "code_comprehension": {
    "files_read": ["ViewModels/OrderViewModel.cs"],
    "lines_examined": "1-580",
    "summary": "ViewModel contains LoadOrders() loading paginated data via IOrderService, CreateOrder()/UpdateOrder() for CRUD, ExportToExcel() for export. 15 RelayCommand bindings to View. Not a shell — complete business logic with validation, error handling, and state management.",
    "call_chain": "View.xaml → OrderViewModel.LoadOrders() → OrderService.GetPagedAsync() → Repository.QueryAsync()",
    "confidence": "high — read complete implementation, not inferred from filename"
  }
}
```

### LLM self-check anti-patterns:

- If `summary` contains only surface descriptions ("file exists", "class defined") → LLM must acknowledge insufficient evidence and re-read the code
- If `call_chain` is broken (definition exists but no caller) → cannot judge as `implemented`, should be `dead_code`
- If `lines_examined` range < 20 for a verdict of "implemented" → LLM must explain why so little code suffices for the judgment

No hardcoded "empty shell" thresholds. Instead, the LLM must demonstrate understanding. If it can't articulate what the code does in natural language, it hasn't read it.

---

## Change 7: Completeness Sweep (Safety Net)

**File**: `skills/code-replicate-core.md` — end of Phase 3, step ID `"3.sweep"`

**Problem**: Even with per-step improvements, systematic blind spots can persist because each step's self-review is local (Change 1 reviews per-module, Change 2 reviews per-screen). Need a **global-perspective** safety net — this is defense-in-depth, not redundancy.

**Design**: Dual-dimension sweep — source code coverage (Dimension A) + source app experience walkthrough (Dimension B).

### Progress tracking:

- Step ID: `"3.sweep"` — recorded in `replicate-config.json` progress tracking
- `--from-phase 4` skips the sweep (it belongs to Phase 3)
- `--from-phase 3.sweep` re-runs only the sweep

### Dimension A: Source Code Coverage

LLM traverses source project directory structure (not extracted artifacts) and classifies each file:

- **Covered**: Referenced in extraction-plan sources
- **Indirectly covered**: Not directly referenced but functionality included via parent file
- **Uncovered**: Neither referenced nor covered by parent

For uncovered files, LLM reads file headers and classifies:
- Utility/config/test → reasonable to skip, record reason
- Independent user feature → `late_discovery`, supplement to artifacts

### Dimension B: Source App Experience Walkthrough

LLM constructs per-role user journeys and checks each step against artifacts:

```json
{
  "role": "regular user",
  "journey": [
    "Open app → what appears? (splash/main/login)",
    "Enter main screen → what entry points? (bottom tabs/sidebar/top nav)",
    "Enter chat → what can I do? (text/image/voice/file/location/...)",
    "Receive message → what can I do? (view/reply/forward/save/delete/...)",
    "Long-press message → what pops up? (which menu options?)",
    "Tap image → what happens? (fullscreen? swipe? save?)",
    "Go offline → what do I see? (offline notice? draft saved? retry button?)"
  ]
}
```

For each journey step, LLM checks:
- Screen present in experience-map?
- Interaction captured in task-inventory or interaction_triggers?
- State variant captured in state_variants?

### Information source priority for journey construction:

1. Phase 2 screenshots/recordings (if available) — most direct
2. Source code route table / navigation config — all screen entries
3. Source code event bindings (onTap/onClick/onDrag/...) — interaction inventory
4. Source code state enums / conditional rendering — state variants
5. Source code permission checks — role-specific differences

Multiple signals cross-validated, not dependent on any single source.

### Output and merge:

Dimension A `late_discovery` items + Dimension B `gaps` → deduplicated → generate **supplemental fragments** (not direct JSON edits) → feed through existing merge scripts (cr_merge_tasks.py, cr_merge_screens.py, etc.) to respect ID ranges and iron law 4 ("LLM 不负责跨模块合并或 ID 分配") → then proceed to Phase 4.

Late discovery fragments follow the same format as Phase 3 per-module fragments, tagged with `"source": "sweep"` for traceability.

```json
{
  "total_source_files": 78,
  "covered": 22,
  "indirectly_covered": 38,
  "uncovered": 18,
  "late_discoveries": 5,
  "journey_steps_checked": 28,
  "journey_gaps_found": 6,
  "merged_back": 8,
  "sweep_confidence": "After supplement, user-perceivable feature coverage estimated from ~85% to ~93%"
}
```

---

## Change 8: Adaptive Source Access (Phase 1 Optimization)

**File**: `skills/code-replicate-core.md` — Phase 1 (Preflight)

**Problem**: Phase 1 always performs `git clone` of source code to a local directory, even when the source is already a local path or a branch in the same repository. This is unnecessary overhead and adds complexity (disk space, permission configuration). More importantly, with the v5.6.0 changes (EXTRACTION_PLAN_REVIEW, Completeness Sweep Dimension A/B), the LLM needs frequent random access to source files — the access pattern matters, not where the bits live.

**Design**: Replace mandatory clone with adaptive source access strategy. LLM determines the optimal access mode based on where the source code is.

### Source location detection and strategy:

```json
{
  "source_access": {
    "source_path": "user-provided path or URL",
    "detected_type": "remote_git | local_directory | same_repo_branch",
    "strategy": "clone | direct_read | git_show",
    "reasoning": "..."
  }
}
```

### Three access modes:

**Mode 1: Clone (remote_git)**
- When: `source_path` is a remote URL (https://, git@, ssh://)
- Action: `git clone` to temporary directory (current behavior)
- Reason: No other way to access the files

**Mode 2: Direct Read (local_directory)**
- When: `source_path` is a local filesystem path (e.g., `/Users/xx/projects/source-app/`)
- Action: Read files directly via `Read` tool, no copy
- Phase 1 records `consistency_anchor`:
  ```json
  {
    "access_mode": "direct_read",
    "source_path": "/Users/xx/projects/source-app/",
    "anchor_commit": "a1b2c3d",
    "anchor_timestamp": "2026-03-29T10:30:00Z",
    "warning": "If source files change during analysis, re-run from Phase 2"
  }
  ```
- Reason: Source already on disk, clone is pure waste. Commit hash provides consistency reference — if user modifies source during analysis, the anchor detects drift.

**Mode 3: Git Show (same_repo_branch)**
- When: `source_path` is a branch name in the current repository (e.g., `origin/flutter-app`)
- Action: Use `git show branch:path/to/file` to read files without checkout
- Phase 1 records branch HEAD as anchor
- Reason: Avoids checkout/worktree overhead while keeping access to all files

### Impact on downstream phases:

Phase 1 writes `source_access.strategy` to `replicate-config.json`. All subsequent phase instructions reference this field to determine how to read source files. No code abstraction layer is needed — the LLM follows the recorded strategy as a **prompt instruction pattern**:

```
Phase 2+ file access:
  replicate-config.json says strategy = "direct_read", source_path = "/Users/xx/projects/source-app/"
  → LLM uses Read tool on /Users/xx/projects/source-app/lib/widgets/chat_input.dart

  replicate-config.json says strategy = "clone", clone_dir = "/tmp/cr-source-abc/"
  → LLM uses Read tool on /tmp/cr-source-abc/lib/widgets/chat_input.dart

  replicate-config.json says strategy = "git_show", branch = "origin/flutter-app"
  → LLM uses Bash: git show origin/flutter-app:lib/widgets/chat_input.dart
```

### Consistency safeguard:

For Mode 2 (direct_read), if the analysis spans multiple sessions:
- Phase resumption checks if source repo HEAD still matches `anchor_commit`
- If diverged, warn user: "Source code changed since analysis started (anchor: a1b2c3d, current: e4f5g6h). Recommend re-running from Phase 2."
- LLM decides whether the changes affect already-extracted artifacts (may not need full re-run if changes are in unrelated files)

### Edge case: source is a zip/tarball:

- Extract to temp directory, treat as Mode 1 (clone equivalent)
- Record extraction path as source_path

---

## Version Bump

- v5.5.2 → v5.6.0 (minor: new capabilities, backward compatible)
- Update in 3 locations: `plugin.json`, `marketplace.json`, `SKILL.md`

## Files Changed Summary

| File | Changes |
|------|---------|
| `skills/code-replicate-core.md` | +EXTRACTION_PLAN_REVIEW, +experience-map depth_decision, +COMPLETENESS_SWEEP, +adaptive source access (Phase 1) |
| `docs/schema-reference.md` | +interaction_triggers, +state_variants optional fields |
| `docs/analysis-principles.md` | +Principle #7: User-Perceivable Capabilities |
| `skills/cr-fidelity.md` | +dimension_reasoning[], +dynamic weight, +no-silent-skip |
| `skills/cr-visual.md` | +CAPTURE_UNAVAILABLE compensation framework |
| `docs/cr-visual/step-capture.md` | +compensation_strategy decision block |
| `docs/fidelity/static-dimensions.md` | +code_comprehension evidence, +anti-pattern self-check |
| `.claude-plugin/plugin.json` | version 5.5.2 → 5.6.0 |
| `.claude-plugin/marketplace.json` | version 5.5.2 → 5.6.0 |
| `SKILL.md` | version 5.5.2 → 5.6.0 |
