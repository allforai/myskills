# Product Verify Capability

> Functional verification of implemented product against design artifacts.
> Static analysis + dynamic E2E testing (tool matched to each module's tech stack).

## Purpose

After code is written, verify it actually implements what was designed:
- Static: check routes, API endpoints, page titles match artifacts
- Dynamic (Web): Playwright navigates the running app, verifies screens render,
  buttons work, forms submit, data flows correctly.
- Dynamic (Mobile): Platform-native testing frameworks verify app functionality
  on simulators/emulators or real devices.

## Protocol

### Static Verification
- Route parity: every screen in experience-map has a route in the code
- API parity: every task in task-inventory has an API endpoint
- Field parity: form fields in UI match API request schemas
- Permission check: role-restricted routes have auth guards

### Dynamic Verification (per module type)

Every module in the project must be verified using its appropriate tool.
**Playwright CANNOT test native mobile apps** — this is a hard constraint.

| Module Type | Tool | Method |
|-------------|------|--------|
| Web (Next.js, React, Vue) | Playwright | Browser navigate + interact + screenshot |
| Flutter mobile | `flutter test integration_test/` | Compile + run integration tests on emulator/device |
| React Native | Detox or Maestro | Native E2E test runner |
| iOS native (SwiftUI) | XCUITest | Xcode test runner |
| Android native (Kotlin) | Espresso | Gradle test runner |
| API-only backend | curl / HTTP client | Endpoint integration test |
| Unity | Unity Test Framework (`-runTests -testPlatform PlayMode`) | Automated playmode tests on target platform |
| Unreal Engine | Gauntlet / Automation Framework | Automated functional tests |
| Godot | GdUnit4 / GUT | Scene-based integration tests |

For each module:
- Launch app (dev server / emulator / device)
- Per role: login → navigate each screen → verify elements exist
- Form submission: fill + submit → verify response
- Error states: trigger errors → verify error UI renders
- Empty states: verify empty state when no data

### Dynamic Verification (Mobile — Platform-Native)

**Flutter:**
- Run `flutter test` for widget/unit tests
- Run `flutter test integration_test/` for integration tests on simulator/emulator
- Use `flutter drive` for full E2E with screenshots
- Key checks: screen renders, navigation works, forms submit, API calls succeed, offline handling

**iOS (Swift/SwiftUI):**
- Run `xcodebuild test` with XCTest/XCUITest
- Verify launch, navigation, data display, form submission on Simulator

**Android (Kotlin/Compose):**
- Run `./gradlew connectedAndroidTest` with Espresso/Compose UI tests
- Verify on emulator or connected device

**React Native:**
- Run Detox or Maestro E2E tests
- Use `npx react-native start` + test framework

**Game Engines (Unity/Unreal/Godot):**
- Run automated playmode/functional tests in headless mode
- Verify: game launches, main menu loads, core gameplay loop completes, save/load works
- Verify: server connection (login, matchmaking, data sync) if multiplayer
- Game-specific: combat sequence completes, economy transactions process, progression saves
- Playwright/Detox CANNOT test game engine clients — use engine-native test frameworks only

**Common mobile verification layers:**
1. V1: App launches on simulator/emulator without crash
2. V2: All screens reachable via navigation
3. V3: Content renders correctly (no blank screens, no undefined data)
4. V4: Forms submit and data persists
5. V5: API integration works (login, CRUD, real-time)
6. V6: Error handling (network off, invalid input, server error)
7. V7: Platform-specific (push notifications, deep links, permissions)

### Verification Layers (V1-V7)
1. V1: App launches without error
2. V2: All routes reachable
3. V3: Page content matches spec (title, key elements)
4. V4: Forms submit successfully
5. V5: CRUD operations work end-to-end
6. V6: Error handling works (invalid input, network error)
7. V7: Role-based access enforced

### UI Test Helper Generation (per-module, framework-agnostic)

Before writing integration/E2E tests for any UI module, generate a framework-specific helper
that supplements the test framework's native capabilities without replacing them.

**Pre-step — Framework Capability Assessment:**
For each UI module, evaluate the test framework's native coverage across 8 fragile layers,
then write the assessment to `.allforai/deadhunt/ui-helper-profile.json` (keyed by `module_id`):

```json
{
  "modules": [
    {
      "module_id": "M002",
      "framework": "Patrol",
      "layers": {
        "element_discovery":  { "native": "partial",   "helper": "supplement" },
        "button_trigger":     { "native": "partial",   "helper": "supplement" },
        "gesture":            { "native": "partial",   "helper": "supplement" },
        "async_wait":         { "native": "partial",   "helper": "supplement" },
        "system_dialog":      { "native": "covered",   "helper": "thin" },
        "keyboard_ime":       { "native": "uncovered", "helper": "full" },
        "scroll_container":   { "native": "uncovered", "helper": "full" },
        "cross_app":          { "native": "partial",   "helper": "supplement" }
      }
    }
  ]
}
```

**The 8 Fragile Layers (goals — LLM decides implementation):**

| Layer | Goal |
|-------|------|
| 1. Element Discovery | Find elements with failure semantics; multi-tier fallback when testID coverage is low |
| 2. Button Trigger | Confirm element is in viewport, visible, and interactable before tap/click |
| 3. Touch Gesture | Wait for animation/page-transition to settle before gesture |
| 4. Async Wait | Wait for data-ready signal (loading disappears / list appears); timeout reports specific target |
| 5. System Dialog | Auto-handle known permission dialogs; best-effort dismiss unknown ones |
| 6. Keyboard & IME | Keep subsequent tap targets in operable area; for IME projects block other interactions during composing state |
| 7. Scroll Container | Ensure target element is rendered into the view tree before interaction |
| 8. Cross-App Flow | Track app-leave and app-return state; verify context is correct after redirect back |

**Helper principle:** Supplement, not replace. Layers already covered natively get thin wrappers only.
Backend-only modules skip helper generation entirely.

**Framework降级 (when preferred framework CLI is unavailable):**
- Flutter: Patrol → `flutter test integration_test/`
- Android / React Native: Maestro → Espresso (Android) / Detox (RN)
- iOS: XCUITest (no降级; required for native iOS UI tests)

Output: `.allforai/product-verify/verify-report.json` + `verify-report.md`

**verify-report.json field schema:**
```json
{
  "static_score": "<number 0-100>",
  "dynamic_score": "<number 0-100>",
  "composite_score": "<number 0-100 — weighted average>",
  "issues": [
    {
      "type": "<enum: route_missing | api_missing | field_mismatch | permission_gap | render_fail | form_fail>",
      "severity": "<enum: critical | major | minor>",
      "description": "<string>",
      "evidence": "<string — screenshot path or response body reference>"
    }
  ],
  "screenshots": ["<string — file path, optional>"]
}
```
`static_score`, `dynamic_score`, `composite_score` are consumed by code-tuner and launch-prep.

### Multi-Client Feature Parity Verification

When product-concept declares multiple clients for a role (e.g., buyer-web + buyer-mobile),
verify that features are implemented consistently across all clients:

1. Extract feature list from product-concept for this role
2. For each feature × client pair:
   - Does the client have a UI entry point for this feature?
   - Does the client call the corresponding API endpoint?
   - Are the user flows equivalent (same steps, same outcomes)?
3. Report parity gaps: feature exists in client A but not client B

This is the runtime counterpart of bootstrap Step 3.5 Level 3 (Multi-Client Parity).
cross-module-stitch checks API CONTRACT consistency (fields, types, formats);
this check verifies FEATURE consistency (same features available on all clients).

Parity modes from product-concept:
- `full`: every feature must exist on every client → any gap is a finding
- `partial`: every feature except `parity_exceptions[]` → exceptions are allowed
- `explicit`: each client declares `supported_features[]` → only check declared features

## Rules (Must Preserve)

1. **Static before dynamic**: Cheaper checks first, catch obvious gaps early.
2. **Per-role verification**: Each role's journey tested independently.
3. **App must be running**: Dynamic verification requires live app. Fail if app can't start.
4. **Evidence-based**: Each check records screenshot or response body as proof.

## Knowledge References

### Phase-Specific:
- design-audit-dimensions.md: 8-dimension audit framework
- consumer-maturity-patterns.md: consumer maturity scoring
- experience-map-schema.md §Interaction-Gate: gate scoring for verification

## Downstream Consumers

> Bootstrap reads this table to generate Context Pull sections for downstream node-specs.
> `required` = subagent reports error if file missing; `optional` = warning + continue.

| Artifact | Field Path | Consumer Capability | Required | Reason |
|----------|------------|---------------------|----------|--------|
| `verify-report.json` | `composite_score` | tune | optional | 代码治理参考验收分数决定优化优先级 |
| `verify-report.json` | `composite_score`, `issues[]` | launch-prep | required | 上架准备需要验收报告确认产品就绪 |
| `verify-report.json` | `issues[]` | concept-acceptance | optional | 概念验收参考已知问题列表 |

## Composition Hints

### Single Node (default)
Run after compile-verify passes and app is launchable.

### Split by Platform (REQUIRED for multi-platform projects)
Projects with both web AND mobile MUST have separate verify nodes:
- `product-verify-web` — Playwright for web frontends
- `product-verify-mobile` or `product-verify-flutter/ios/android` — platform-native tests

**Playwright cannot test native mobile apps.** This split is mandatory, not optional.
If bootstrap detects a mobile module (Flutter/iOS/Android), it MUST generate a
platform-specific verify node using the appropriate test framework.

### Split Static vs Dynamic
For large apps: static verification as one node, dynamic as another.

### Merge with Test Verify
For simple apps: combine product-verify + test-verify into one verification node.
