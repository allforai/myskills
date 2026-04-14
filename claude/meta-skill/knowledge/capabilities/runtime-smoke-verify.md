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
      "smoke_endpoint": "POST /api/v1/auth/login",
      "smoke_status": 404,
      "evidence": ".allforai/runtime-smoke/M003/first-screen.png",
      "failure_cause": "base URL env var UITEST_API_BASE_URL missing /api/v1 suffix; APIClient.setBaseURL consumed it verbatim",
      "fix": "either (a) APIClient auto-appends /api/v1 when absent, (b) tests and app agree on same convention, or (c) document expected format in APIClient.resolveBaseURL"
    }
  ],
  "contract_drift_warnings": [
    {
      "symbol": "UITEST_API_BASE_URL",
      "consumers": [
        {"path": "FlyDictUITests/APIHelper.login", "expected_shape": "bare host, test prepends /api/v1"},
        {"path": "FlyDictApp.swift", "expected_shape": "full URL including /api/v1"}
      ],
      "severity": "P1"
    }
  ],
  "overall": "pass|fail"
}
```

## Downstream consumers

- `launch-checklist` reads `overall` — must be `pass` for release sign-off
- `learned/blind-spots.md` updated when the node catches a new class of bug
- `quality-checks` reads `contract_drift_warnings[]` and merges into its
  fieldcheck-report

## Required inputs from upstream nodes

- `bootstrap-profile.json` — module list + build commands
- `product-verify-*` reports — must all pass before smoke (smoke runs
  additional verification, not a replacement)
- `.env.example` / deployment config files from the project — to know
  what env vars a real deployment sets

## Implementation notes

- **Do not mock external services** — the point is to hit reality. If the
  artifact depends on OpenAI / Stripe / APNs, use sandbox / staging
  credentials, not stubs. If no sandbox exists, flag that as an issue
  (the artifact has no path to smoke-verify without real infra).
- **Different from XCUITest**: the simulator launch here does NOT use
  `-UITest` launch arg. The app should run as a user would experience.
- **Different from production deploy**: we're on localhost/simulator, not
  pushing to stores / servers. This is the last gate before deploy.
