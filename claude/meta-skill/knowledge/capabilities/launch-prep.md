# Launch Prep Capability

> Prepare an existing product for store/market launch. Covers competitive research,
> concept finalization, implementation gap closure, compliance checks, and launch checklist.
> This capability is for EXISTING products with code — not for new product creation.

## Purpose

An existing product needs to go from "works in development" to "ready for public launch."
This requires decisions that code alone can't answer: pricing, tier structure, compliance,
marketing positioning. These decisions should be research-informed, not guessed.

**Why this is a separate capability:**
- Product-concept is for creating NEW products from scratch (9 sub-phases)
- Reverse-concept is for extracting concept from existing code (backward)
- Launch-prep is for FINALIZING concept decisions for an existing product (forward from current state)
- It bridges the gap between "code works" and "product is ready for users to pay for"

## When to Use

- User says "I want to launch", "prepare for App Store", "go to market", "上架"
- Product has existing code + product artifacts (reverse-concept already done)
- There are unresolved product decisions (pricing, tier structure, compliance)

## Input Path

| Input | Source | Required |
|-------|--------|----------|
| Existing concept artifacts | `.allforai/product-concept/` | Yes — need to know current product concept |
| Existing product-map | `.allforai/product-map/` | Yes — need to know what's implemented |
| Static verify report | `.allforai/product-verify/` | Optional — if available, shows known gaps |
| Target platform | User input | Yes — iOS App Store / Google Play / Web / etc. |

## What LLM Must Accomplish

### Phase 1: Competitive Research (竞品调研)

Research competitors to inform decisions. Not the same as product-concept's market
research — this is focused on **pricing and positioning** for launch, not problem discovery.

1. **Identify direct competitors** in the same category
   - For language learning: Duolingo, HelloTalk, Speak, Elsa, LingQ, Busuu
   - WebSearch: "[category] app pricing 2025", "[competitor] subscription plans"

2. **Extract pricing intelligence**
   - Per competitor: free tier limits, paid tier pricing (monthly/yearly), features per tier
   - Regional pricing differences (especially for target market)
   - Trial duration and conversion patterns

3. **Extract positioning intelligence**
   - How do competitors describe themselves? (App Store descriptions)
   - What are their unique selling points?
   - What do user reviews praise/criticize?

4. **Synthesize competitive position**
   - Where does THIS product fit in the competitive landscape?
   - Price positioning: premium / mid-range / budget / freemium
   - Feature differentiation: what does this product do that competitors don't?

**Output:** `.allforai/launch-prep/competitive-research.json`

### Phase 2: Concept Finalization (概念定稿)

Based on competitive research + existing concept, finalize unresolved decisions:

1. **Pricing decision**
   - Recommend pricing based on competitive research
   - Present 2-3 pricing options with rationale (not ask user to pick blindly)
   - Include regional considerations (e.g., Apple Tier pricing for CNY/JPY/USD)

2. **Tier structure decision**
   - How many tiers? What's in each?
   - Feature gating: what's free vs paid?
   - Trial: duration, what's included?

3. **Positioning decision**
   - App Store category and keywords
   - One-line positioning statement
   - Key differentiators to highlight

4. **User confirmation**
   - Present all decisions with research backing
   - User confirms or adjusts
   - Write finalized decisions to concept artifacts

**Output:** Update `.allforai/product-concept/business-model.json` + `concept-baseline.json`

### Phase 3: Implementation Gap Analysis (缺口分析)

Compare finalized concept against current implementation:

1. **List all gaps** between concept and code
   - Payment integration (IAP/StoreKit/Google Play)
   - Feature gating enforcement
   - Pricing display
   - Trial flow
   - Missing features promised in paid tier

2. **Prioritize gaps**
   - P0 Blocker: cannot launch without this (e.g., IAP not working)
   - P1 Important: should have for launch (e.g., restore purchases)
   - P2 Nice-to-have: can launch without, add post-launch

3. **Generate implementation plan**
   - Per gap: what code changes needed, estimated complexity
   - Dependency ordering (IAP before pricing display)

**Output:** `.allforai/launch-prep/implementation-gaps.json`

### Phase 4: Platform Compliance (平台合规)

Check platform-specific requirements:

**iOS App Store:**
- Privacy policy URL required
- App Privacy labels (data collection declaration)
- IAP must use StoreKit (no external payment links)
- Subscription auto-renewal disclosure
- Restore purchases button required
- App Review Guidelines compliance
- Export compliance (encryption)
- Content ratings

**Google Play** (if applicable):
- Similar requirements with Play Billing Library
- Data Safety section

**Output:** `.allforai/launch-prep/compliance-checklist.json`

### Phase 5: Launch Checklist (上架清单)

Final checklist combining all above:

1. Implementation gaps resolved (from Phase 3)
2. Compliance items checked (from Phase 4)
3. App Store metadata prepared (description, screenshots, keywords)
4. Testing passed (product-verify)
5. Analytics/crash reporting configured
6. Support contact/URL configured

**Output:** `.allforai/launch-prep/launch-checklist.json` + `launch-checklist.md`

## Rules

1. **Research before decisions**: Never ask user to pick pricing without competitive data
2. **Evidence-based recommendations**: Every pricing/positioning recommendation cites competitor data
3. **Platform-specific**: Different platforms have different requirements — don't generalize
4. **Concept artifacts are source of truth**: Finalized decisions update concept artifacts, not just launch-prep files
5. **P0 gaps block launch**: If any P0 gap remains unresolved, launch checklist status = "not ready"

## Composition Hints

### Single Node (simple launch)
For apps with one platform and few gaps: one launch-prep node covers all 5 phases.

### Split by Phase
For complex launches: split into separate nodes:
- `competitive-research` — can run early, even before implementation is complete
- `finalize-concept` — depends on research, produces decisions
- `implement-launch-gaps` — depends on decisions, produces code changes
- `compliance-check` — can run in parallel with implementation
- `launch-verify` — final verification before submission

### Multi-Platform Split
For simultaneous iOS + Android launch: one compliance node per platform.

## Knowledge References

### Phase-Specific:
- product-design-theory.md §Phase-1: Kano, ERRC for positioning
- cross-phase-protocols.md §D: User Confirmation Gate — decisions before execution
- capabilities/product-verify.md: verification after gap implementation
