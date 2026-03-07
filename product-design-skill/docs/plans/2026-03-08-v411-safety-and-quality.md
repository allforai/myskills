# v4.1.1 Safety & Quality Fixes

> Date: 2026-03-08
> Status: Approved
> Scope: 4 small fixes across product-design + dev-forge

## Changes

### 1. journey-emotion: critical node safety gate

**File:** `skills/journey-emotion.md` (auto mode section)

In auto mode, `risk=critical` nodes must stop for user confirmation instead of auto-confirming. Critical nodes are typically payment/deletion/permission operations — wrong emotion assignment cascades into wrong micro-interactions and design constraints.

Only `critical`, not `high` — high nodes are too numerous (30-50%) and would defeat auto mode.

### 2. interaction-gate: score < 50 safety gate

**File:** `skills/interaction-gate.md` (auto mode section)

In auto mode, operation lines scoring below 50 must stop for user confirmation. Score 50 means at least two dimensions near zero — this is a severe UX problem that shouldn't be silently accepted.

### 3. journey-emotion: adjacent intensity cliff detection

**File:** `skills/journey-emotion.md` (Step 3 or validation)

After emotion nodes are generated, check adjacent node pairs. If `|intensity[i] - intensity[i+1]| >= 4`, flag as WARNING "情绪悬崖" with the two node IDs. Not a blocker — just a warning in the output.

### 4. product-verify S3.5: unknown pattern WARNING

**File:** `dev-forge-skill/skills/product-verify.md` (S3.5 section)

If a screen's `implementation_contract.pattern` is not one of the 5 known values, log WARNING instead of silently skipping.

## Version

These are patch fixes: product-design 4.1.0 → 4.1.1. dev-forge stays 2.7.0 (one-line doc change).
