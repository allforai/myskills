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
| Go backend (gRPC) | `buf generate && go build ./...` (when `buf.yaml` present) OR `protoc --go_out=. --go-grpc_out=. proto/*.proto && go build ./...` (when raw protoc). **Proto compilation MUST run before `go build`** — generated `.pb.go` files are required imports. | binary |
| Go multi-module (go.work) | Run `buf generate` once at workspace root (if buf.yaml present), then `go build ./...` per service module listed in go.work `use ./` entries. | binary per service |
| Flutter (mobile) | `flutter build apk` / `flutter build ios` | build/ |
| Flutter (web) | `flutter build web` | build/web/ |
| Flutter (macOS desktop) | `flutter build macos` | build/macos/Build/Products/Release/ (.app bundle) |
| Flutter (Linux desktop) | `flutter build linux` | build/linux/x64/release/bundle/ |
| Flutter (Windows desktop) | `flutter build windows` | build/windows/runner/Release/ |
| iOS (Swift) | `xcodebuild build -scheme X -destination 'generic/platform=iOS'` | .app |
| Android (Kotlin) | `./gradlew assembleDebug` | .apk |
| React Native (Expo managed) | Local bundle: `npx expo export --platform android` + `npx expo export --platform ios` (checks JS bundle compiles without errors). Full binary: `eas build --platform ios/android` (cloud build — requires EAS account; produces .apk/.ipa). Note: `npx expo build` is DEPRECATED — use `eas build` instead. | build/ (local export) or EAS artifact |
| Node.js / TypeScript CLI | `npm run build` (check `package.json` scripts.build; fallback `npx tsc`) — produces compiled JS in `dist/`. Verify `bin` entry points exist and are executable. | dist/cli.js (or configured output) |
| React Native (bare - iOS) | `xcodebuild -workspace ios/<AppName>.xcworkspace -scheme <AppName> -configuration Release -destination 'generic/platform=iOS Simulator'` | .app |
| React Native (bare - Android) | `./gradlew assembleRelease` (production) or `./gradlew assembleDebug` (development) | .apk |
| Electron (desktop app) | `npm run build` (builds renderer bundle) followed by `npm run make` or `npx electron-builder` (packages .dmg/.exe/.AppImage). Note: `npm run build` alone only builds the React/Vue frontend — the full Electron binary/installer requires electron-builder. Check `package.json scripts` for the combined `build:electron` or `package` command. | dist/ (.dmg/.exe/.AppImage/.deb) |
| Tauri v1 | `npm run tauri build` (preferred, if build script exists) OR `cargo tauri build` | .dmg/.exe/.AppImage |
| Tauri v2 | `npm run tauri build` OR `cargo tauri build` — check `src-tauri/Cargo.toml` for `tauri` version. Note: v2 requires capabilities defined in `src-tauri/capabilities/` folder. | .dmg/.exe/.AppImage |
| Rust (binary / CLI) | `cargo build --release` | target/release/<bin> |
| Rust (library / SDK) | `cargo test` | target/debug/deps/ — compile + doctests confirm public API surface |
| Kotlin Multiplatform (KMM) shared | `./gradlew :shared:build` | shared/build/ — must run BEFORE iOS/Android compile nodes |
| AWS SAM (serverless) | `sam build` | .aws-sam/build/ |
| Serverless Framework | `serverless package` | .serverless/ |
| Unity | `unity -batchmode -buildTarget Android/iOS/StandaloneWindows64 -executeMethod BuildScript.Build` | .apk/.app/.exe |
| Unreal Engine | `UnrealBuildTool` / `RunUAT BuildCookRun` | .pak + binary |
| Godot | `godot --headless --export-release "platform" output` | .apk/.app/.exe/.pck |
| Python (desktop/script) | `python -m pytest --co -q` (collection-only; fastest syntax+import check) | N/A (interpreted) |
| Twine / Twee (narrative) | `tweego -o dist/index.html *.tw` (if tweego installed) OR skip | dist/index.html |
| Ruby on Rails | `bundle install && bundle exec rails assets:precompile && bundle exec rails db:schema:load RAILS_ENV=test` (order matters: assets before schema; or `db:migrate` if incremental). Build success = no Sprockets errors + schema loads. | public/assets/ |
| Kotlin Spring Boot (Gradle) | `./gradlew build` (single module) or `./gradlew :service1:build :service2:build` (multi-service monorepo with settings.gradle). For monorepos: check `settings.gradle` `include` entries to enumerate all service modules. | build/libs/*.jar per module |
| Deno Fresh (SSR) | `deno task build` (check `deno.json` `tasks.build` entry) OR `deno check` for type-checking without bundle output | dist/ (if build task exists) |
| HarmonyOS (ArkTS) | `hvigorw build` or `npm run build` (check `oh-package.json5` scripts). HarmonyOS uses `hvigor` build tool (Harmony equivalent of Gradle). Output: `.hap` module file. Requires DevEco Studio SDK or hvigor CLI installed. | entry/build/default/outputs/*.hap |
| Next.js + Prisma | `npx prisma migrate deploy && npm run build` — Prisma schema MUST be deployed before Next.js build (build may fail or type errors occur if schema not synced). | .next/ |
| .NET / ASP.NET Core | `dotnet build` (debug) OR `dotnet publish -c Release -o bin/publish` (production). For solutions with multiple projects: `dotnet build <Solution>.sln`. | bin/publish/ (production) or bin/Debug/net*/dll |
| Obsidian plugin | `npm run build` (esbuild compiles TypeScript → main.js in project root). Verify output: `main.js` + `styles.css` (if styles present) + `manifest.json`. | main.js |
| VS Code extension | `npm run compile` (TypeScript → out/) OR `vsce package` (produces .vsix distributable). Check `package.json` scripts for actual command. | out/ or *.vsix |
| Embedded C / C++ firmware (ARM) | `cmake -B build -DCMAKE_TOOLCHAIN_FILE=arm-none-eabi.cmake && cmake --build build` | build/*.elf / build/*.bin / build/*.hex |
| Embedded C (bare-metal, no CMake) | `make all` (Makefile-driven cross-compile with `arm-none-eabi-gcc`) | *.elf / *.bin |

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
