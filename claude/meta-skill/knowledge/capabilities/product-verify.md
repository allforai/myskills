# Product Verify Capability

> Functional verification of implemented product against design artifacts.
> Static analysis + dynamic testing (Playwright for web, platform-native for mobile).

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

### Dynamic Verification (Web — Playwright)
- Launch app (dev server)
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

Output: `.allforai/product-verify/verify-report.json` + `verify-report.md`

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
