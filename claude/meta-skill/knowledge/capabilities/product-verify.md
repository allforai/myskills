# Product Verify Capability

> Functional verification of implemented product against design artifacts.
> Static analysis + dynamic E2E testing (tool matched to each module's tech stack).

## Purpose

After code is written, verify it actually implements what was designed:
- Static: check routes, API endpoints, page titles match artifacts
- Dynamic: navigate the running app, verify screens render, buttons work,
  forms submit, data flows correctly.

## Protocol

### Static Verification
- Route parity: every screen in experience-map has a route in the code
- API parity: every task in task-inventory has an API endpoint
- Field parity: form fields in UI match API request schemas
- Permission check: role-restricted routes have auth guards

### Dynamic Verification (per module type)

Every module in the project must be verified using its appropriate tool:

| Module Type | Tool | Method |
|-------------|------|--------|
| Web (Next.js, React, Vue) | Playwright | Browser navigate + interact + screenshot |
| Flutter mobile | `flutter test integration_test/` | Compile + run integration tests on emulator/device |
| React Native | Detox or Maestro | Native E2E test runner |
| iOS native (SwiftUI) | XCUITest | Xcode test runner |
| Android native (Kotlin) | Espresso | Gradle test runner |
| API-only backend | curl / HTTP client | Endpoint integration test |

For each module:
- Launch app (dev server / emulator / device)
- Per role: login → navigate each screen → verify elements exist
- Form submission: fill + submit → verify response
- Error states: trigger errors → verify error UI renders
- Empty states: verify empty state when no data

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

### Split Static vs Dynamic
For large apps: static verification as one node, dynamic as another.

### Merge with Test Verify
For simple apps: combine product-verify + test-verify into one verification node.
