# Compile Verify Capability

> Capability reference for full-build verification after translation.
> Bootstrap may create one or multiple nodes from this capability depending on project complexity.

## Purpose

Full build verification after all translation is complete.
Catches cross-component integration issues that per-component loops may miss
(shared type mismatches, import cycles, missing peer dependencies).

## Protocol

1. Run full build command(s)
2. Capture exit code + error output
3. On failure: categorize errors (see Error Taxonomy below), feed back to translate node for targeted fixes
4. On success: mark node complete, pass build artifact paths to test-verify

## Error Taxonomy

| Category | Examples | Action |
|----------|----------|--------|
| Syntax | Missing semicolons, malformed expressions | Return to translate — component-level fix |
| Type mismatch | Interface drift between modules | Return to translate — fix at boundary |
| Missing dependency | Unresolved import, absent package | Check mapping table — add to target stack |
| Configuration | Build config missing, env vars absent | Fix in node-spec build section |
| Integration | Cross-module circular dependency | Return to translate — restructure DAG |

## Rules

1. **Build commands from node-spec**: Not hardcoded. Bootstrap generates them per platform.
2. **Full build, not incremental**: Catches cross-component integration issues that incremental builds hide.
3. **Error categorization before retry**: LLM must classify each error before feeding back — prevents random fix attempts.
4. **Max 3 fix-and-rebuild cycles**: If not green after 3 cycles, surface unresolved errors as UPSTREAM_DEFECT.
5. **No silent partial success**: If build emits warnings that indicate runtime failure (deprecations, missing peer deps), treat as failure.
6. **Artifact path recording**: On success, record output artifact paths (dist/, build/, apk, etc.) for test-verify.

## Connection to Fidelity Verification

This node covers the R1 (Build) layer of the cr-fidelity runtime verification stack:
- R1 pass here = prerequisite cleared for test-verify (R2 Smoke, R3 Test Vectors, R4 Protocol Compat)
- R1 failure blocks all downstream fidelity scoring
- Build failure = composite fidelity score = 0 regardless of static analysis results

## Knowledge References

### Phase-Specific:
(No phase-specific knowledge beyond universal references)

## Platform-Specific Build Commands

Bootstrap MUST generate the correct build commands per platform:

| Platform | Build Command | Output |
|----------|--------------|--------|
| Web (Node.js) | `npm run build` / `vite build` | dist/ |
| Go backend | `go build ./...` | binary |
| Go backend (gRPC) | **Proto files must compile before Go source**: `buf generate && go build ./...` (buf.yaml) or `protoc ... && go build ./...` (raw protoc). Without this step `go build` fails — generated `.pb.go` files are missing imports. | binary |
| Flutter | `flutter build <target>` — target matches platform: `apk` / `ios` / `web` / `macos` / `linux` / `windows`. LLM selects target from bootstrap-profile.json module platform field. | build/ |
| iOS (Swift) | **Two-step**: `pod install` (if `Podfile` exists, generates `.xcworkspace`) → `xcodebuild build -workspace X.xcworkspace -scheme X -destination 'generic/platform=iOS'`. Running xcodebuild without pod install first fails with "Pods not integrated" errors. Swift Package Manager projects skip pod install; use `-project` flag instead. | .app |
| Android (Kotlin) | `./gradlew assembleDebug` | .apk |
| React Native | Expo managed: `npx expo export` for local bundle check (`npx expo build` is deprecated — use `eas build` for binaries). Bare workflow: `xcodebuild` (iOS) + `./gradlew assembleRelease` (Android). | bundle / .apk / .ipa |
| Electron | **Two-step**: renderer bundle first (`npm run build`), then Electron binary (`npm run make` or `npx electron-builder`). `npm run build` alone does NOT produce the Electron binary — check `package.json scripts` for the combined command. | dist/ |
| Tauri | `npm run tauri build` or `cargo tauri build`. Tauri v2: capabilities must exist in `src-tauri/capabilities/` or build succeeds but IPC calls fail at runtime. | .dmg/.exe/.AppImage |
| Rust (binary / CLI) | `cargo build --release` | target/release/<bin> |
| Rust (library / SDK) | `cargo test` — compile + doctests confirm public API surface | target/debug/deps/ |
| Kotlin Multiplatform (KMM) shared | `./gradlew :shared:build` — **must run BEFORE** iOS/Android compile nodes | shared/build/ |
| AWS SAM (serverless) | `sam build` | .aws-sam/build/ |
| Serverless Framework | `serverless package` | .serverless/ |
| Unity | `unity -batchmode -buildTarget <target> -executeMethod BuildScript.Build` | .apk/.app/.exe |
| Unreal Engine | `UnrealBuildTool` / `RunUAT BuildCookRun` | .pak + binary |
| Godot | `godot --headless --export-release "<platform>" output` | .apk/.app/.exe/.pck |
| Cocos Creator 3.x | **CLI build (no GUI required)**: `${COCOS_CREATOR_APP:-/Applications/CocosCreator.app}/Contents/MacOS/CocosCreator --project <project-dir> --build "platform=web-mobile"`. macOS app binary path is `CocosCreator.app/Contents/MacOS/CocosCreator`; set `COCOS_CREATOR_APP` env var to override. Available platforms: `web-mobile`, `web-desktop`, `android`, `ios`. TypeScript `module 'cc'` errors that appear under standalone `tsc` resolve automatically inside this build environment — do NOT report them as failures requiring GUI. First run is slow (project cache init). Exit code 0 = success. | build/ |
| Python | `python3 -m pytest --co -q` (collection-only syntax+import check for interpreted projects) | N/A |
| Twine / Twee | `tweego -o dist/index.html *.tw` (if tweego installed) OR skip | dist/index.html |
| Next.js + Prisma | **Schema before build**: `npx prisma migrate deploy && npm run build` — build may fail with type errors if schema is not synced first. | .next/ |
| .NET / ASP.NET Core | `dotnet build` / `dotnet publish -c Release` | bin/publish/ |
| Embedded firmware | `cmake -B build ... && cmake --build build` or `make all` (Makefile) | *.elf / *.bin |

## Downstream Consumers

> Bootstrap reads this table to generate Context Pull sections for downstream node-specs.
> `required` = subagent reports error if file missing; `optional` = warning + continue.

| Artifact | Field Path | Consumer Capability | Required | Reason |
|----------|------------|---------------------|----------|--------|
| build artifacts (paths) | `artifact_paths[]` | test-verify | required | 测试验证需要知道构建产物路径 |
| exit code | `exit_code` | test-verify | required | 构建失败则测试不应运行 |

## Composition Hints

### Single Node (default)
For most projects: one compile-verify node runs the full build after all translation is complete.

### Split by Build Target (REQUIRED for game + backend projects)
For game projects that also have a dedicated server or API backend: one compile-verify node per target, with backend built FIRST:
- `compile-verify-backend` — `dotnet publish` / `go build` / etc. (must complete before game client build if shared types/protos are involved)
- `compile-verify-game-client` — Unity batchmode / Godot export / etc.

This ordering ensures shared type safety: the server DLLs or generated proto files must exist before the game client builds against them.

### Multi-Service Backend with Shared Protos
For monorepos where multiple backend services share proto definitions: the service that GENERATES the `.pb.go` / `.pb.cc` / `*_grpc.pb.go` files must compile first. Downstream services that only IMPORT the generated files must declare a dependency edge in the workflow graph. Bootstrap detects shared proto ownership by looking for which service owns the `proto/` or `api/` directory containing the shared `.proto` files.

### Split by Platform (REQUIRED for multi-platform projects)
For projects with web + mobile + backend: one compile-verify node per platform.
Each has distinct build toolchains that may require different environments:
- `compile-verify-web` — Node.js + bundler
- `compile-verify-api` — Go/Python/Java
- `compile-verify-flutter` — Flutter SDK + Dart
- `compile-verify-kmm-shared` — Kotlin Multiplatform shared module (`./gradlew :shared:build`); must run BEFORE iOS/Android compile nodes
- `compile-verify-ios` — Xcode + CocoaPods/SPM
- `compile-verify-android` — Android SDK + Gradle
- `compile-verify-unity` — Unity Editor (batchmode) + target SDK
- `compile-verify-unreal` — Unreal Build Tool + target SDK

**Do NOT combine `flutter build` and `npm run build` in one node** — different SDKs,
different failure modes, different fix strategies.

### Merge with Another Capability
For single-platform projects with few components: merge translate + compile-verify into a single node.
