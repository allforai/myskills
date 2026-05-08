# Capability: runtime-smoke-verify

Verify that each built artifact **actually runs and reaches its backend** when
launched outside any test harness, with the same env vars / config a real
user would have. Catches runtime contract bugs that test-harness verification
can't see — e.g., env var dual-contracts, broken URL prefixes, missing
auth-redirect wiring, missing Info.plist entitlements, broken deep links.

## Why this exists (the blind spot)

XCUITest / Playwright / integration tests verify the app **inside** a test
harness. The harness often provides:
- Its own environment / base URLs (tests prepend paths the app doesn't)
- Mocks / stubs for external services
- A specific launch flag (`-UITest`) that activates test-only code paths
- Lenient timeouts and retry loops

Bugs that exist **outside** the harness include:
- Env var whose value is interpreted differently by tests vs runtime
- First-launch path that requires a TLS cert / CA chain not present in tests
- Crash-on-launch from missing signing / provisioning config
- Network layer that assumes a proxy header tests always send

Symptom: **"all tests green, user sees a 404 / crash / blank screen"**.

## When to include this node

Include for any goal that implements or deploys code (`translate`, `rebuild`,
`create`, `launch-prep`), specifically when the workflow already has
`product-verify-<module>` tied to a test harness. runtime-smoke-verify runs
**after** the test harness passes and **before** any "launch-checklist"
sign-off.

If goals are static-only (`analyze`, `tune`, `quality-checks`), this
capability is N/A.

## What the node does

For each module listed in `bootstrap-profile.json.modules[]`:

1. **Build the release artifact**
   - Backend: build binary / container image with prod config flags
   - Mobile: archive via `xcodebuild archive` or `gradlew assembleRelease`
     (NOT just `build` which is the dev/debug path)
   - Admin/Website: `npm run build` + serve the output statically, do NOT
     use the dev server
2. **Launch with realistic environment**
   - Write the env vars the real deployment uses (from `.env.production`,
     Docker Compose, App Store Connect Xcconfig, etc.)
   - For mobile: install signed ipa/apk to simulator/emulator with
     `simctl install` and launch via `simctl launch` (use
     `SIMCTL_CHILD_*` prefix for env)
3. **Hit one primary endpoint per artifact's own code path** (not via tests)
   - Backend: `curl` health, then `curl` one realistic unauthenticated
     endpoint (e.g., `/auth/login` with dummy creds expecting 401)
   - Mobile: take a screenshot ~5s after launch; verify it's not a
     "network error" / "404" / blank state by OCR or pixel heuristic;
     capture the first API call's URL via `mitmproxy` / `tcpdump` on the
     simulator loopback
   - Web: headless Chrome visit `/`, record `console.error`, network 4xx,
     and the `document.title`
4. **Record evidence** per artifact: screenshot + network log + exit code.
   Store under `.allforai/runtime-smoke/<artifact-id>/`.
5. **Fail loudly** if any step doesn't produce a clean first-API 2xx (or
   expected 4xx for auth-required endpoints) — the failure mode is the
   whole point of the node.

## Key checks specifically designed to catch env-var contracts

When the module has env var consumers at 2+ call sites, explicitly:
- Enumerate all `ProcessInfo.environment[...]` / `os.Getenv(...)` /
  `process.env.*` / `viper.Get*` references for each env var name.
- For each consumer, derive the **expected shape** of the value by
  reading the surrounding code (what's the string concatenated to?
  what's parsed out?).
- If two consumers expect different shapes → contract drift; record in
  the smoke report as `contract_drift_warnings[]` even if the current
  launch happened to succeed.

## Exit artifacts

Write `.allforai/runtime-smoke/smoke-report.json`:

```json
{
  "checked_at": "<ISO>",
  "artifacts": [
    {
      "module_id": "M001",
      "role": "backend",
      "build_result": "pass",
      "launch_result": "pass",
      "smoke_endpoint": "GET /health",
      "smoke_status": 200,
      "evidence": ".allforai/runtime-smoke/M001/smoke.log"
    },
    {
      "module_id": "M003",
      "role": "mobile",
      "build_result": "pass",
      "launch_result": "fail",
      "smoke_endpoint": "<HTTP method> <path>",
      "smoke_status": 404,
      "evidence": ".allforai/runtime-smoke/M003/first-screen.png",
      "failure_cause": "base URL env var consumed verbatim by the app's HTTP client; tests prepend an API stem the app does not, so the app emits requests against the wrong path",
      "fix": "either (a) HTTP client normalizes / detects the missing stem at use site, (b) tests and app agree on a single shared format, or (c) document the expected format at the env-var declaration site"
    }
  ],
  "contract_drift_warnings": [
    {
      "symbol": "<env var name>",
      "consumers": [
        {"path": "<test-side consumer file:line>", "expected_shape": "bare host, caller prepends API stem"},
        {"path": "<app-side consumer file:line>", "expected_shape": "full URL including API stem"}
      ],
      "severity": "P1"
    }
  ],
  "overall": "pass|fail"
}
```

## Downstream Consumers

> Bootstrap reads this table to generate Context Pull sections for downstream node-specs.
> `required` = subagent reports error if file missing; `optional` = warning + continue.

| Artifact | Field Path | Consumer Capability | Required | Reason |
|----------|------------|---------------------|----------|--------|
| `.allforai/runtime-smoke/smoke-report.json` | `overall` | launch-prep | required | 上架前需要烟雾测试全通过才能放行 |
| `.allforai/runtime-smoke/smoke-report.json` | `contract_drift_warnings[]` | quality-checks | optional | 字段一致性检查合并合约漂移警告 |

## Suppression and Adaptation Rules

| architecture_pattern | Action |
|----------------------|--------|
| `embedded-firmware` | Suppress — document manual device test scenarios |
| `ide-plugin-obsidian` | Suppress — cannot automate desktop GUI headlessly |
| `ide-plugin-vscode` | Suppress — cannot automate extension host headlessly |
| `library-sdk` | Suppress — no runtime surface; library has no launch |
| `github-action` | Suppress — CI action has no persistent launch |
| `desktop-app-electron` | Adapt — smoke = `npm run start` launches Electron binary without crash; verify main window renders using `electron-playwright-helpers` or launch the built binary directly; record window screenshot; verify no uncaught exceptions in DevTools console (accessible via `mainWindow.webContents.getURL()` / `console.error` listener). No HTTP endpoint — success = window visible + IPC roundtrip responds. |
| `desktop-app-tauri` | Adapt — smoke = `npm run tauri dev` or launch the built binary; verify app window opens; issue one IPC invoke via `tauri-driver` + WebdriverIO; verify response received. No HTTP endpoint — success = window visible + IPC response. Record `src-tauri/capabilities/` list to verify Tauri v2 capability set is as designed. |
| `browser-extension` | Adapt — use `chrome --load-extension` + WebDriver; record extension load success/failure |
| `serverless-sam` | Adapt — use `sam local start-api` as live environment; smoke = curl health endpoint |
| `serverless-framework` | Adapt — use `serverless-offline` as live environment |
| `serverless-cf-workers` | Adapt — use `wrangler dev` as live environment |
| Twine/Ren'Py (narrative, web export) | Adapt — smoke = headless Chrome `open index.html`, verify page loaded (presence of #game canvas or `#ren_py` container), no console errors. Do NOT rely on `document.title` — Ren'Py export template may not set it. |
| Elixir/Phoenix (LiveView) | Adapt — smoke = `mix phx.server` starts without crash; curl `http://localhost:4000/` returns 200 (LiveView pages return HTML, no separate /health needed). Check supervision tree logs for crash reports (`[error]`). |
| Rust CLI | Adapt — smoke = run binary with `--help` or `--version`, verify exit code 0 and expected output on stdout. For TUI: run with a test input file or `--dry-run` flag if supported; verify exit code and no panic output. No HTTP endpoint — success is non-zero exit code check inverted (0 = success). |
| Backend with Celery async workers | Adapt — **two-process smoke required**: (1) `curl /health` on the FastAPI/Django API process → verify 200 OK; (2) worker health check: `celery -A <app> inspect active` OR `redis-cli KEYS celery*` (should return active task metadata keys). Enqueue a fast test task via API (`POST /test-task`), poll Redis result backend for `state == "SUCCESS"` within 10s. Both API and worker must pass — worker-down with API-up is a failure. |
| gRPC backend (with gRPC-Gateway) | Adapt — smoke = verify BOTH the gRPC port AND the HTTP transcoding gateway: (1) gRPC health: `grpc_health_probe -addr=:50051` or `grpcurl -plaintext localhost:50051 grpc.health.v1.Health/Check`; (2) REST transcoding: `curl http://localhost:8080/healthz` → 200. Both must pass — gRPC services that lost the HTTP gateway layer are partially broken. |
| Rails + Sidekiq | Adapt — two-process smoke required: (1) `rails server` starts; `curl /health` (or `curl /up` for Rails 7.1) → 200; (2) worker health: `bundle exec sidekiq status` or check Redis for Sidekiq process heartbeat (`SMEMBERS sidekiq:processes`). Enqueue a fast test job and verify Redis removes it from `sidekiq:queue:default` within 5s. Both API and worker must pass. |
| Spring Boot + Kafka | Adapt — two-process smoke required: (1) `curl http://localhost:8080/actuator/health` → `{"status":"UP"}`; (2) Kafka consumer health: `kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group <app-group>` — verify `LAG == 0` or consumer is STABLE. A service with HTTP UP but Kafka consumer STOPPED is partially broken. |
| Deno Fresh (SSR) | Adapt — smoke = `deno run --allow-net --allow-read dev.ts` (or `deno task start`) starts without crash; `curl http://localhost:8000/` → 200 with HTML content (Fresh renders SSR pages on-demand, no JSON health endpoint). Verify no `console.error` in server logs. |
| mobile-flutter-desktop (macOS) | Adapt — smoke = launch built .app bundle directly (`open build/macos/Build/Products/Release/MyApp.app`) or via `flutter run -d macos`; verify window appears within 5s (no crash); capture screenshot; check for Flutter framework errors in console log. No HTTP endpoint — success = macOS window visible + no crash. |

## Required inputs from upstream nodes

- `bootstrap-profile.json` — module list + build commands
- `product-verify-*` reports — required only when `product-verify` is in the workflow graph; waived when runtime-smoke-verify runs directly before launch-prep without product-verify
- `.env.example` / deployment config files from the project — to know what env vars a real deployment sets

## Implementation notes

- **Do not mock external services** — the point is to hit reality. If the
  artifact depends on OpenAI / Stripe / APNs, use sandbox / staging
  credentials, not stubs. If no sandbox exists, flag that as an issue
  (the artifact has no path to smoke-verify without real infra).
- **Different from XCUITest**: the simulator launch here does NOT use
  `-UITest` launch arg. The app should run as a user would experience.
- **Different from production deploy**: we're on localhost/simulator, not
  pushing to stores / servers. This is the last gate before deploy.
