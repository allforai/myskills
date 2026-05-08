# Test Verify Capability

> Capability reference for test verification (smoke, test vectors, protocol compat).
> Bootstrap may create one or multiple nodes from this capability depending on project complexity.

## Purpose

Run test suites against translated code. Entry point is a passing compile-verify
(R1 build). Covers runtime smoke, functional test vectors, and protocol compatibility.

## Protocol

1. Run test command(s)
2. Capture results (pass/fail counts, error details)
3. On failure: categorize (logic error vs missing mock vs integration issue)
4. Feed failures back to translate or compile-verify as appropriate

## Verification Layers (from cr-fidelity)

| Layer | Name | What | How |
|-------|------|------|-----|
| R1 | Build | Code compiles | Build command (handled by compile-verify node — prerequisite) |
| R2 | Smoke | App starts | Launch + health check endpoint |
| R3 | Test vectors | Known input→output | Execute extracted test vectors against target |
| R4 | Protocol compat | Custom protocol behavior | Protocol-specific test suite (only if discovery flagged custom protocols) |

Composite score = static * 0.5 + runtime * 0.5. R1 failure = everything fails.

### Adaptive Dimension Selection

LLM evaluates which layers apply per project before running tests.
Outputs `verification_reasoning[]` in test-verify-report.json:

```json
{
  "verification_reasoning": [
    {
      "layer": "R2",
      "applicable": true,
      "reasoning": "Project has HTTP server with /health endpoint. Smoke check is trivial and high-value.",
      "risk_if_skipped": "medium"
    },
    {
      "layer": "R4",
      "applicable": false,
      "reasoning": "No custom protocols detected during discovery. Standard HTTP/REST only.",
      "risk_if_skipped": "low"
    }
  ]
}
```

No silent skips — every layer must appear in reasoning, either `applicable: true` or `applicable: false` with justification.

## Failure Routing

| Failure Type | Root Cause | Route To |
|-------------|------------|----------|
| App won't start (R2) | Missing config, port conflict, env var | compile-verify or node-spec fix |
| Test vector mismatch (R3) | Logic divergence from source | translate node — intent_rebuild for affected component |
| Mock resolution error | Test harness not adapted for target platform | translate node — test file fix |
| Protocol incompatibility (R4) | Custom protocol not faithfully reproduced | translate node — protocol_spec driven rebuild |

## Pass Threshold

Bootstrap sets `min_pass_rate` per layer (default: R2 = 100%, R3 = 90%, R4 = 100%).
If actual rate < threshold → trigger fix loop (max 3 cycles).
If not resolved → surface as UPSTREAM_DEFECT with per-layer breakdown.

## Output Contract

**test-verify-report.json field schema:**
```json
{
  "results": [
    {
      "module_id": "<string — matches bootstrap-profile.json modules[].id>",
      "layer": "<enum: R2 | R3 | R4>",
      "pass_rate": "<number 0.0-1.0>",
      "passed": "<number>",
      "failed": "<number>",
      "failures": ["<string — failure description>"]
    }
  ],
  "composite_score": "<number 0.0-1.0 — static * 0.5 + runtime * 0.5>",
  "verification_reasoning": [
    {
      "layer": "<string>",
      "applicable": "<boolean>",
      "reasoning": "<string>",
      "risk_if_skipped": "<enum: low | medium | high>"
    }
  ]
}
```
`composite_score` is consumed by downstream nodes (visual-verify, code-tuner, launch-prep).
`results[].module_id` MUST reference a module declared in bootstrap-profile.json.

## Rules

1. **Test commands from node-spec**: Bootstrap generates them per platform and test framework.
2. **R1 (build) is prerequisite**: Do not run tests if compile-verify has not passed.
3. **Adaptive dimensions**: LLM evaluates which verification layers apply per project — not all projects need R4.
4. **No silent skip**: Each verification layer must be explicitly evaluated with reasoning before being excluded.
5. **Failure routing before retry**: Classify failure type before retrying — prevents misdirected fixes.
6. **Score persistence**: Write composite score to test-verify-report.json for downstream nodes (visual-verify, tune) to reference.
7. **Playwright constraint**: Playwright CANNOT test native mobile apps. Never assign Playwright to Flutter/iOS/Android/React Native modules. Each mobile module MUST use its platform-native test framework (see Platform-Specific Test Commands table). This is a hard constraint — assigning Playwright to mobile silently produces passing CI with zero mobile coverage.

## Knowledge References

### Phase-Specific:
- cross-phase-protocols.md §Upstream-Baseline-Validation: test results validated against product artifacts

## Platform-Specific Test Commands

Bootstrap MUST generate the correct test commands per platform:

| Platform | Unit/Widget Tests | Integration/E2E Tests |
|----------|------------------|-----------------------|
| Web (Node.js) | `npm run test` / `vitest run` / `jest` | Playwright E2E |
| Go backend | `go test ./...` | API integration tests |
| Flutter | `flutter test` | Patrol (`patrol test`) → fallback `flutter test integration_test/` |
| iOS (Swift) | `xcodebuild test -scheme X -destination 'platform=iOS Simulator'` | XCUITest |
| Android (Kotlin) | `./gradlew test` | `./gradlew connectedAndroidTest` |
| React Native | `npx jest` | Detox / Maestro |
| Unity | `Unity.exe -runTests -testPlatform EditMode -projectPath .` | PlayMode: `-testPlatform PlayMode` |
| Godot | GUT: `godot --headless --script addons/gut/gut_cmdln.gd` (check `addons/gut/` exists). GdUnit4: `godot --headless -s addons/gdUnit4/bin/GdUnitCmdTool.gd` (check `addons/gdUnit4/bin/` exists). If neither found, mark R3 as `applicable: false` — no test runner detected. | Manual scene tests (if no framework present) |
| Go backend (gRPC) | `go test ./...` per service module | Protocol compat: `buf lint` (style) + `buf breaking --against '.git#branch=main'` (backward compat check against previous proto version). **buf breaking is R4 for gRPC** — a passing `go test` does not guarantee proto schema backward compatibility. |
| Roblox (Rojo) | TestEZ via `rojo test` or custom runner | Manual in Roblox Studio |
| Rust game (Bevy/macroquad) | `cargo test` for logic | Rendering: manual test scenarios |
| GBStudio | **No automated test runner** — manual verification only | N/A |
| PICO-8 | **No automated test runner** — manual verification only | N/A |
| Twine / Ren'Py | Playwright E2E on exported HTML bundle (`npx serve dist/` then Playwright) | passage navigation, variable tracking, ending states |
| Discord bot (discord.js) | `jest` or `vitest` with mocked `discord.js` interaction objects | Unit tests for command handlers; integration tests against a real test guild with `DISCORD_TEST_GUILD_ID` |
| Discord bot (discord.py / nextcord / py-cord) | `pytest` with `unittest.mock.AsyncMock` for interaction mocking; `pytest-asyncio` for async command tests | Unit tests mock `ctx` / `interaction`; integration tests use `discord.py` test utilities with real bot token + test guild |
| tRPC backend | `npm run test` / `vitest run` using `createCallerFactory(router)(ctx)` (no HTTP client — tRPC has no REST routes; call procedures as functions in tests) | For E2E: Playwright on the Next.js frontend; tRPC calls are made client-side via `trpc.procedure.query()` — no curl/HTTP testing of procedures |
| HarmonyOS (ArkTS) | `ohosTest` framework: run tests via DevEco Studio or `hvigorw test` CLI | Component tests on HarmonyOS simulator or real device; ArkUI test framework for UI component testing |
| Ruby on Rails | `bundle exec rspec` (RSpec) or `bundle exec rails test` (Minitest) for unit/integration tests | System tests: `bundle exec rails test:system` (Capybara + Selenium/Chrome). Action Cable R4: test WebSocket channel subscribe/broadcast lifecycle via ActionCable test helpers |
| Kotlin Spring Boot | `./gradlew test` per module for unit tests; `./gradlew integrationTest` for Spring integration tests (requires running DB/Kafka) | R4 protocol: API compatibility via SpringDoc/OpenAPI diff if springdoc-openapi present |
| Deno (Fresh / runtime) | `deno test` (built-in test runner, no npm needed). For Fresh: `deno test --allow-net tests/` | E2E: Playwright on built Fresh output (`deno task start` + Playwright) |
| Flutter (macOS desktop) | `flutter test` for unit/widget tests; `flutter test integration_test/ --device-id=macos` for E2E on macOS (requires macOS device target). CI: `macos-latest` GitHub Actions runner required. | N/A |
| .NET / ASP.NET Core | `dotnet test` (discovers all *Tests.csproj in the solution). For integration tests: `dotnet test --filter Category=Integration` (requires running DB or test containers). Use `dotnet test --logger trx` for CI result output. | Testcontainers or SQL Server LocalDB for DB-dependent tests |
| Obsidian plugin | `npm run test` (vitest or jest with Obsidian API mocks). Note: full integration testing requires loading the plugin into Obsidian dev vault manually — automated headless testing is limited to unit tests of pure logic. | Manual vault load for full E2E |
| VS Code extension | `npm run test` (runs `@vscode/test-electron` which launches VS Code with the extension loaded; exits with test results). Command: `node ./out/test/runTest.js` (typical convention). | `@vscode/test-electron` extension host tests |

**Key rule:** Mobile test frameworks are fundamentally different from web. `flutter test` ≠ `npm test`. Bootstrap must detect the platform and emit the correct command.

**No-test-runner guard**: If bootstrap detects `architecture_pattern` matching GBStudio, PICO-8, or Ren'Py, mark R3/R4 as `applicable: false` with reasoning "Platform has no automated test runner — manual verification only." Do not attempt to run a test command.

## Downstream Consumers

> Bootstrap reads this table to generate Context Pull sections for downstream node-specs.
> `required` = subagent reports error if file missing; `optional` = warning + continue.

| Artifact | Field Path | Consumer Capability | Required | Reason |
|----------|------------|---------------------|----------|--------|
| `test-verify-report.json` | `composite_score`, `results[]` | product-verify | optional | 产品验证参考测试分数决定是否值得动态验证 |
| `test-verify-report.json` | `composite_score` | tune | optional | 代码治理参考测试覆盖率 |

## Composition Hints

### Single Node (default)
For small-to-medium projects: one test-verify node runs all verification layers (R2-R4) sequentially.

### Split by Platform (REQUIRED for multi-platform projects)
For projects with web + mobile: split into platform-specific nodes.
Each platform has distinct test runners, simulators, and failure modes.
**Do NOT put Flutter tests and Playwright tests in the same node.**

- `test-verify-api` — Go backend: `go test ./...`
- `test-verify-web` — Next.js/React/Vue: `vitest` + Playwright E2E
- `test-verify-mobile` — Flutter: `flutter test` + `flutter test integration_test/`; React Native: `jest` + Detox; iOS: `xcodebuild test`; Android: `./gradlew connectedAndroidTest`

This ensures no module is silently skipped and enables parallel execution.

### Split per Test Layer
For large single-platform projects: split per test layer (test-verify-unit, test-verify-integration, test-verify-e2e) to isolate failure domains and allow parallel execution.

### Merge with Another Capability
For very simple projects (single platform, no custom protocols): merge compile-verify + test-verify into a single build-and-test node.
