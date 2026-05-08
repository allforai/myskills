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

LLM applies these rules to each module during bootstrap, selecting the correct smoke approach from the project's actual stack. Rules are principles — not exhaustive per-technology scripts.

**Suppress (no runtime surface to test):**

| Pattern | Action |
|---------|--------|
| `library-sdk`, `cli` | Suppress — no persistent runtime; test via test-verify instead. CLI exception: if the project has a companion HTTP service, smoke that. |
| `embedded-firmware` | Suppress — requires physical device; document manual test scenarios |
| `ide-plugin-*` | Suppress — plugin runs inside host IDE process; cannot launch headlessly. Use product-verify instead. |
| `github-action` | Suppress — CI action has no persistent launch |

**Adapt (non-HTTP or multi-process runtime):**

| Pattern | Adaptation Principle |
|---------|---------------------|
| Desktop app (Electron / Tauri / Flutter desktop / native) | No HTTP endpoint. Success = binary launches without crash + main window appears + one IPC roundtrip responds. LLM selects the appropriate launch command and window verification tool for the detected framework. |
| Serverless | Use the framework's local emulator as the live environment (e.g., `sam local`, `serverless-offline`, `wrangler dev`). Curl the emulated health/function endpoint. |
| Narrative / static web export | Headless browser opens index.html; verify page canvas/container loads; no console errors. Do NOT rely on document.title. |
| Game client (Unity / Unreal / Godot / etc.) | Game clients require display — skip binary launch. If backend module present: smoke the backend only. If offline (`offline_first: true`): suppress entirely. |
| Bot (webhook-based: Telegram / Slack HTTP mode) | POST a mock event payload to the webhook endpoint; verify 200 OK and signature validation logic executes. Do NOT call the live platform API — use locally-posted mock. |
| Bot (gateway/socket-mode: Discord / Slack Socket Mode) | Verify process starts and connects to gateway without error (log check). No HTTP endpoint to curl — success = gateway connect logged. |
| API + async worker (Celery / Sidekiq / Bull / Kafka consumer / etc.) | **Two-process smoke required**: (1) API health check → 200; (2) worker health check → worker is reachable and consuming. Worker-down with API-up = failure. LLM determines the worker health check command from the detected queue technology. |
| Microservices (N services, each with own port) | **All-services smoke required**: every service in `bootstrap-profile.json.modules[]` with `role: "backend"` must pass its own health check. One service down = overall failure, even if N-1 pass. Inter-service: if service A calls service B via gRPC/HTTP internally, the smoke for service A must include one cross-service call (or check that service B is reachable via service A's health endpoint). |
| gRPC with HTTP gateway | Both ports must pass: gRPC health probe on gRPC port + HTTP curl on gateway port. A service missing its HTTP gateway layer is partially broken. |
| Non-HTTP protocol service (TURN/STUN, MQTT broker, raw TCP/UDP) | No `curl` available. Use the protocol's native client: TURN → `turnutils_uclient` / `stunserver`; MQTT → `mosquitto_sub -t '$SYS/#'`; raw UDP → `nc -u`. Success = protocol handshake completes within timeout. Document the check command in smoke-report.json `smoke_endpoint` field using protocol:// prefix (e.g., `turn://0.0.0.0:3478`). |

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
