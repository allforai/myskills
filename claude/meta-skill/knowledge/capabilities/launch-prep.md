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
| Bootstrap profile | `.allforai/bootstrap/bootstrap-profile.json` | Yes — need module roles, platform, detected tech stack, and architecture_pattern to tailor compliance checks and gap analysis |
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

**Output:** Update `.allforai/product-concept/business-model.json`. For `concept-baseline.json`: NEVER overwrite it unconditionally — the baseline is the canonical cross-phase reference and overwriting it mid-workflow breaks consumers that have already loaded it. Instead, append finalization decisions to a new file `.allforai/launch-prep/concept-finalization.json`, and emit a `concept-baseline-patch.json` with only the delta fields changed (e.g., updated `errc_highlights.must_have`, updated `pipeline_preferences`). The orchestrator can apply the patch to concept-baseline.json only after all downstream concept-baseline consumers have completed.

### Phase 3: Implementation Gap Analysis (缺口分析)

Compare finalized concept against current implementation. Gap categories vary by architecture_pattern:

**Mobile app (iOS/Android):**
- Payment integration (IAP/StoreKit/Google Play)
- Feature gating enforcement
- Pricing display
- Trial flow
- Missing features promised in paid tier

**Web app / SaaS:**
- Stripe/payment provider integration
- Subscription management UI
- Free tier usage limits enforced
- Billing portal

**macOS native app (SwiftUI/AppKit):**
- Sandbox entitlement vs feature parity (sandboxed apps have restricted file system access)
- Keychain usage for all secrets (not UserDefaults, not env vars)
- Hardened runtime: all entitlements declared, no `disable-library-validation` unless justified
- Notarization pipeline in CI (automated signing + notarytool submission)
- Universal binary or correct architecture target (Apple Silicon / Intel / both)

**GitHub Action / CLI tool / Library/SDK:**
- Documentation completeness (README, usage examples, API docs)
- Input validation and error messages
- Version compatibility matrix
- Migration guide (if breaking changes)
- Example workflows / code samples

**Game (Steam/console):**
- Achievement integration
- Cloud save implementation
- Platform overlay support
- Demo build scoped correctly
- Content rating asset compliance (screenshots, trailer)

1. **List all gaps** between concept and code (using archetype-appropriate categories above)

2. **Prioritize gaps**
   - P0 Blocker: cannot launch without this (e.g., IAP not working)
   - P1 Important: should have for launch (e.g., restore purchases)
   - P2 Nice-to-have: can launch without, add post-launch

3. **Generate implementation plan**
   - Per gap: what code changes needed, estimated complexity
   - Dependency ordering (IAP before pricing display)

**Output:** `.allforai/launch-prep/implementation-gaps.json`

### Phase 4: Platform Compliance (平台合规)

Check platform-specific requirements based on target launch platform (read from bootstrap-profile.json `architecture_pattern` and user input):

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

**Web / Browser (SPA, PWA, WASM):**
- Privacy policy URL + cookie consent banner (GDPR/ePrivacy)
- Content Security Policy (CSP) headers configured
- HTTPS enforced (no mixed content)
- Accessibility (WCAG 2.1 AA minimum)
- Core Web Vitals targets (LCP < 2.5s, CLS < 0.1, INP < 200ms)
- Service worker scope correct (PWA only)
- Cross-browser compatibility confirmed (Chrome, Firefox, Safari minimum)

**GitHub Marketplace (GitHub Actions):**
- `action.yml` manifest complete (name, description, author, branding icon/color)
- All `inputs:` and `outputs:` documented with descriptions
- Permissions declared (read/write scopes) — principle of least privilege
- README with usage examples and quickstart
- Verified publisher badge eligibility (if applicable)
- License file present (required for marketplace listing)
- No hardcoded tokens or secrets in workflow examples
- Test coverage with example workflows in `.github/workflows/`

**Electron desktop app (Windows/macOS/Linux):**
- Windows (Authenticode): acquire code signing certificate (DigiCert/GlobalSign; EV cert for SmartScreen bypass); configure `electron-builder` `win.certificateFile` + `certificatePassword`; without signing, Windows SmartScreen shows "unverified publisher" warning
- macOS (Developer ID + Notarization): configure `electron-builder` `mac.identity`; notarize the .dmg or .app.zip using `xcrun notarytool`; staple: `xcrun stapler staple <app>.dmg`; Gatekeeper blocks on macOS Catalina+ without notarization
- Linux: create `.deb` / `.rpm` / `.AppImage` via electron-builder; optionally GPG-sign with `gpg --detach-sign`
- Auto-updater: integrate `electron-updater`; configure `publish` section in electron-builder config (GitHub Releases / S3); test auto-update on staging before 100% rollout
- Distribution format: electron-builder creates platform-appropriate installers (.exe NSIS, .msi, .dmg, .pkg, .deb, .rpm, .AppImage, .snap)

**Tauri desktop app (Windows/macOS/Linux):**
- Windows: code signing via `src-tauri/tauri.conf.json` → `bundle.windows.certificateThumbprint` (Authenticode); configure in CI with env vars
- macOS: notarization via `bundle.macOS.signingIdentity` + `bundle.macOS.providerShortName`; Tauri wraps `xcrun notarytool` internally when signing is configured
- Linux: `.AppImage` / `.deb` / `.rpm` via Tauri bundler
- All platforms: Tauri v2 capability audit before release — review `src-tauri/capabilities/*.json` for overly-broad permissions (path globs, network host wildcards)

**React Native bare workflow (iOS + Android):**
- iOS: Use Fastlane `match` for certificate management (sync certificates/profiles from encrypted git repo); `fastlane ios build` automates signing + TestFlight upload (`pilot upload`). Document `ios/fastlane/Fastfile`.
- Android: `fastlane android build` + `fastlane supply` for Play Console upload; signing keystore path/alias in `android/gradle.properties` (via CI env vars, never committed).

**macOS App Store:**
- Privacy policy URL required
- App Privacy labels (data collection declaration) in App Store Connect
- App Sandbox entitlement required (`com.apple.security.app-sandbox = true`)
- Hardened runtime required for notarization
- Content ratings (age ratings in App Store Connect)
- Same IAP/subscription disclosure rules as iOS (if app has paid features)

**macOS Developer ID (direct distribution, outside App Store):**
- Developer ID Application certificate (not Distribution certificate)
- Hardened runtime entitlements declared (`com.apple.security.hardened-runtime = true`)
- Notarization: `xcrun notarytool submit <app>.zip --apple-id <id> --team-id <tid> --password <app-specific-pwd>` — Apple requires notarization for all macOS software distributed outside the App Store since macOS Catalina
- Staple ticket to bundle: `xcrun stapler staple <app>.dmg` (must staple AFTER notarization approval)
- Gatekeeper check: `spctl --assess --type exec --verbose <app>` — must return "accepted"
- entitlements.plist must declare only the minimum required (network access, file access, hardened runtime flags) — excessive entitlements can fail notarization review
- Privacy policy URL must be accessible (Gatekeeper shows it to users at first launch)

**HarmonyOS (Huawei App Gallery Connect / AGC):**
- Privacy policy URL required (AGC requires it before review approval)
- Data safety labels (AGC Data Privacy section — similar to iOS App Privacy)
- Content ratings via AGC (required for App Gallery listing)
- Permissions declared in `module.json5` → `requestPermissions[]` (all requested permissions reviewed by AGC)
- Build signing: use Huawei Developer certificate + AGC signing config
- IAP: if app has paid features, use Huawei IAP service (NOT Google Play Billing) — `com.huawei.hms.iap` package
- Distribution: upload `.hap` file to AGC console; set age ratings, supported devices, supported HarmonyOS versions

**Deno Deploy:**
- Environment variables must be set in Deno Deploy project settings dashboard (not `.env` file — sandboxed runtime)
- GitHub integration configured for auto-deploy on push (if applicable)
- Deno KV data backup strategy documented (no automatic backup — implement Litestream or export cron if data loss is unacceptable)
- HTTPS: Deno Deploy provides automatic HTTPS/TLS; verify no mixed-content in frontend
- Error monitoring: Deno Deploy logs to stdout; configure external log aggregation (Datadog, Logtail) for production visibility

**Steam (Desktop game):**
- Steam SDK integrated (achievement API, cloud save, overlay)
- Steamworks partner portal app page complete
- Age ratings submitted (IARC or regional equivalents)
- GDPR compliance for EU accounts
- Build on all target platforms (Windows/Mac/Linux)

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
