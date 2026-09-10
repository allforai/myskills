# Test Verify Capability

> Capability reference for test verification (smoke, test vectors, protocol compat).
> Bootstrap may create one or multiple nodes from this capability depending on project complexity.

## Purpose

Run test suites against translated code. Entry point is a passing compile-verify
(R1 build). Covers runtime smoke, functional test vectors, and protocol compatibility.

## Protocol

1. Run test command(s)
2. Capture results (pass/fail counts, error details)
3. For every UI automation path, capture screenshot evidence and run reviewer one visual review
4. On failure: categorize (logic error vs missing mock vs integration issue vs visual/UI defect)
5. Feed failures back to translate or compile-verify as appropriate

## UI Screenshot Evidence And reviewer one Review

任何带用户界面的测试节点，不能只依赖 DOM 断言、测试框架断言或接口返回。只要节点覆盖 Web、移动端、桌面端、游戏客户端、管理后台、商户后台、浏览器扩展等 UI 表面，就必须产出截图证据，并由 reviewer one 对截图进行二次视觉验收。

### 最低输出

UI 测试节点必须写入：

- `.allforai/verify/ui-screenshots/<module_id>/...`：关键路径截图，至少覆盖启动页、主导航页、核心表单/操作页、成功状态、错误/空状态；
- `.allforai/verify/ui-screenshot-manifest.json`：截图清单，记录 module、surface、role、flow、step、viewport/device、screenshot_path、expected_source_ref；
- `.allforai/verify/visual-review-1.json`：reviewer one 对截图的视觉验收结果；
- `.allforai/verify/visual-review-1.md`：中文人类可读复核报告。

`visual-review-1.json` 最低结构：

```json
{
  "state": "passed | passed_with_warnings | failed_visual_review | blocked_by_missing_screenshots | blocked_by_unreadable_screenshot",
  "reviewed_at": "<ISO timestamp>",
  "screenshots_reviewed": [
    {
      "module_id": "<string>",
      "surface_id": "<string>",
      "flow_id": "<string>",
      "step_id": "<string>",
      "screenshot_path": "<string>",
      "result": "pass | warning | fail",
      "issues": [
        {
          "severity": "blocker | major | minor",
          "type": "blank_screen | layout_overlap | clipped_text | unreadable_text | broken_navigation | wrong_state | visual_regression | missing_required_content | accessibility_risk",
          "description": "<中文说明>",
          "repair_target": "<node_id or file/module>"
        }
      ]
    }
  ],
  "blocking_issues": ["<string>"]
}
```

### 验收规则

- UI 自动化节点没有截图，不能通过；返回 `blocked_by_missing_screenshots`。
- 截图空白、无法读取、被遮挡或不是目标页面，不能通过；返回 `blocked_by_unreadable_screenshot`。
- reviewer one 视觉复核发现 blocker / major UI 问题时，测试节点不能标记为通过，即使 Playwright / XCUITest / Espresso / Detox / Maestro 的断言全部通过。
- 如果运行环境无法启动浏览器、模拟器或设备，必须暴露 `BLOCKED_ENV`，不得用静态检查或人工文字说明替代截图验收。
- 截图验收不是替代测试断言；它是 UI 自动化测试之后的额外质量 gate。

## Verification Layers (from cr-fidelity)

| Layer | Name | What | How |
|-------|------|------|-----|
| R1 | Build | Code compiles | Build command (handled by compile-verify node — prerequisite) |
| R2 | Smoke | App starts | Launch + health check endpoint |
| R3 | Test vectors | Known input→output | Execute extracted test vectors against target |
| R4 | Protocol compat | Custom protocol behavior | Protocol-specific test suite (only if discovery flagged custom protocols) |

Composite score = static * 0.5 + runtime * 0.5, for reference; the authoritative result is `verdict` (pass | fail | blocked): R1 failure, any layer below its threshold, or a failed visual review is `fail` regardless of the number.

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
If actual rate < threshold → fix loop until a cycle fixes nothing new or reintroduces a fixed failure (progress, not a count, ends it).
If not resolved → surface as UPSTREAM_DEFECT with per-layer breakdown and the per-cycle trajectory.

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
  ],
  "ui_screenshot_manifest": ".allforai/verify/ui-screenshot-manifest.json",
  "visual_review_1": ".allforai/verify/visual-review-1.json"
}
```
`composite_score` is consumed by downstream nodes (visual-verify, code-tuner, launch-prep).
`results[].module_id` MUST reference a module declared in bootstrap-profile.json.

### Evidence Entries (ledger shape, ADR-0008)

Beside `test-verify-report.json`, the node writes machine entries in cross-exam's ledger-entry
shape to `.allforai/test-verify/evidence-entries/<node_id>.json` (`{"schema":
"evidence-entries/v1", "entries": [...]}`): one entry per `results[]` row — a layer (R2 / R3 / R4)
run for a module — and one per UI automation path with screenshots. The report keeps its name and
its pass rates; the entry is the machine record a later `/cross-exam` can verify and admit as
author evidence instead of rerunning every suite.

An entry is admissible when, and only when, all of the following hold. The shared engine
(`${CLAUDE_PLUGIN_ROOT}/scripts/engine`) decides the shape; `capture_evidence.py entry` records what
the node must not author and refuses a draft that fails; `check_evidence.py --entries
.allforai/test-verify --node <node_id>` re-checks every entry against the tree at gate time.
**`verdict` cannot be `pass` while any entry is refused, or while the file is missing or empty.**

- `medium` is `test` for a layer run (R2 / R3 / R4 for a module): a suite run is a mechanical gate,
  admitted on its captured output alone, and a later `/cross-exam` admits it as a gate instead of
  rerunning the suite (ADR-0008). `medium` is `runtime` for a UI automation path with screenshots;
  cross-exam treats those as context and probes the surface itself. `verdict` is `done` (the layer
  met its threshold against the real target), `gap` (it did not), or `unprovable` — a suite whose
  harness mocks the path under test proves the suite passes, not that the product works, and is
  recorded as `unprovable` with the passing capture as evidence. `pass_rate` stays in the report;
  it is not a verdict.
- `build` is the whole-tree identity from the engine (commit + working-tree snapshot digest +
  artifact digest), computed with `.allforai`, `.claude`, `.codex` outside it (`build_excludes` on the
  entry records exactly that scope; any other scope is refused). It must be the identity of the
  tree at gate time (`构建标识不匹配` otherwise): a suite run before a fix is not evidence for the
  tree after it.
- `probed_at` is ISO 8601 with a timezone offset; a naive timestamp is refused.
- `evidence.dir` is a non-empty directory under `.allforai/test-verify/evidence/` (recommended
  `evidence/<node_id>/<module_id>-<layer>/`) holding the test runner's captured output — the
  `capture_evidence/v1` record of the real command, never a pasted summary — and, for UI
  automation, a screenshot for every state asked for (`states_to_capture`);
  `evidence.key_observation` gives passed / failed counts and the first failure.
- `served_by` (runtime entries; a `test` entry carries none) names where the exercised code's requests went: `host`, `process` (the dev server,
  emulator or launched binary the tests drove; the runner alone is not a destination) and the mock
  layers **in effect** in the harness — MSW registered, a mocked client, nock, an in-memory DB
  (`mock_layers`, `[]` when none). Through a mock layer an entry may be `gap` or `unprovable`,
  never `done` (`经 mock 层（…）的 runtime 不能判 done`). `fixtures` lists the canned files a
  fixture-backed test could have answered with; an output identical to one cannot be `done`
  (`响应与 fixture 一致（…）的 runtime 不能判 done`) — the same field and literals
  `compute_completeness.py` applies to the transition log.
- `readback` carries, for every axis a UI automation path applied — viewport or device, theme,
  locale, role — the value the app itself reported, non-empty; for an API or protocol layer, the
  target version or endpoint the process reported.
- `images` lists the screenshots inside `evidence.dir`; `image_digests` (recorded by the writer) must
  match the files on disk.
- `author` is `{"pipeline": "meta-skill/run", "node_id": <this node>, "capability": "test-verify"}`:
  /run wrote it, as the author; cross-exam admits it only as evidence it can verify, never as a
  verdict.

`evidence_freshness` binds the entries file and every file the entries cite as this node's outputs.

## Rules

1. **Test commands from node-spec**: Bootstrap generates them per platform and test framework.
2. **R1 (build) is prerequisite**: Do not run tests if compile-verify has not passed.
3. **Adaptive dimensions**: LLM evaluates which verification layers apply per project — not all projects need R4.
4. **No silent skip**: Each verification layer must be explicitly evaluated with reasoning before being excluded.
5. **Failure routing before retry**: Classify failure type before retrying — prevents misdirected fixes.
6. **Score persistence**: Write composite score to test-verify-report.json for downstream nodes (visual-verify, tune) to reference.
7. **Playwright constraint**: Playwright CANNOT test native mobile apps. Never assign Playwright to Flutter/iOS/Android/React Native modules. Each mobile module MUST use its platform-native test framework (see Platform-Specific Test Commands table). This is a hard constraint — assigning Playwright to mobile silently produces passing CI with zero mobile coverage.
8. **UI screenshot review gate**: Every UI automation result must include screenshots plus reviewer one visual review. Missing screenshots or failed visual review blocks acceptance.

## Knowledge References

### Phase-Specific:
- cross-phase-protocols.md §Upstream-Baseline-Validation: test results validated against product artifacts

## Platform-Specific Test Commands

Bootstrap derives test commands from the project's own evidence first — test scripts, CI workflow, detected test frameworks and their config files. The table below is a reference for platform pitfalls (mobile frameworks, E2E prerequisites, platforms with no runner) to check against, not a source to copy from.

| Platform | Unit/Widget Tests | Integration/E2E Tests |
|----------|------------------|-----------------------|
| Web (Node.js) | `npm run test` / `vitest run` / `jest` | Playwright E2E |
| Go backend | `go test ./...` | API integration tests |
| Flutter | `flutter test` | Patrol → fallback `flutter test integration_test/`; for desktop targets add `--device-id=macos/linux/windows` |
| iOS (Swift) | `xcodebuild test -scheme X -destination 'platform=iOS Simulator'` | XCUITest |
| Android (Kotlin) | `./gradlew test` | `./gradlew connectedAndroidTest` |
| React Native (Expo managed) | `npx jest` | Maestro preferred — no native build config needed; Expo Go is insufficient for full E2E (sandbox restrictions), use EAS development build instead |
| React Native (bare workflow) | `npx jest` | Detox preferred (deeper RN bridge); Metro bundler must be running before E2E tests |
| Unity | `Unity.exe -runTests -testPlatform EditMode -projectPath .` | PlayMode: `-testPlatform PlayMode` |
| Godot | Detect test framework from `addons/` — GUT or GdUnit4 are common. If neither found, mark R3 `applicable: false`. | Manual scene tests if no framework present |
| Go backend (gRPC) | `go test ./...` per service module | **R4**: `buf lint` + `buf breaking --against '.git#branch=main'` — a passing `go test` does NOT guarantee proto schema backward compatibility |
| Roblox (Rojo) | TestEZ via `rojo test` or custom runner | Manual in Roblox Studio |
| Rust game | `cargo test` for logic | Rendering: manual test scenarios |
| GBStudio | **No automated test runner** — manual verification only | N/A |
| PICO-8 | **No automated test runner** — manual verification only | N/A |
| Twine / Ren'Py | Playwright E2E on exported HTML bundle | passage navigation, variable tracking, ending states |
| Bot projects (Discord / Telegram / Slack) | **Event-driven — no HTTP routes to curl.** Mock the event provider (mock discord.js client, mock telegram.Update, mock Bolt payload); call command handlers directly with mock objects. | Integration: real bot token against dedicated test guild/workspace/bot (not production). |
| tRPC backend | Call procedures directly via `createCallerFactory(router)(ctx)` — no HTTP client, no REST routes | For E2E: Playwright on the frontend; tRPC calls are client-side — never curl tRPC procedures |

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

For Android/Kotlin/Compose apps with user-facing screens, `connectedAndroidTest` is
the UI automation acceptance path, not an optional manual scenario. If no device or
emulator is connected, report `BLOCKED_ENV` and preserve the failed `adb devices`
evidence. Do not mark the UI layer accepted by writing manual test steps.

Apply the same no-manual-substitute rule to iOS (`xcodebuild test`/XCUITest),
Flutter (`flutter test integration_test/` or Patrol), React Native (Detox or
Maestro), and HarmonyOS (Hypium/ohosTest via `hdc`). Missing runtime targets are
environment blockers, not successful verification.

This ensures no module is silently skipped and enables parallel execution.

### Split per Test Layer
For large single-platform projects: split per test layer (test-verify-unit, test-verify-integration, test-verify-e2e) to isolate failure domains and allow parallel execution.

### Merge with Another Capability
For very simple projects (single platform, no custom protocols): merge compile-verify + test-verify into a single build-and-test node.
