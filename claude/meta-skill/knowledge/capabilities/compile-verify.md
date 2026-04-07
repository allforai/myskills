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
| Flutter | `flutter build apk` / `flutter build ios` / `flutter build web` | build/ |
| iOS (Swift) | `xcodebuild build -scheme X -destination 'generic/platform=iOS'` | .app |
| Android (Kotlin) | `./gradlew assembleDebug` | .apk |
| React Native | `npx react-native build-android` / `build-ios` | .apk/.app |
| Rust | `cargo build` | target/ |
| Unity | `unity -batchmode -buildTarget Android/iOS/StandaloneWindows64 -executeMethod BuildScript.Build` | .apk/.app/.exe |
| Unreal Engine | `UnrealBuildTool` / `RunUAT BuildCookRun` | .pak + binary |
| Godot | `godot --headless --export-release "platform" output` | .apk/.app/.exe/.pck |

## Composition Hints

### Single Node (default)
For most projects: one compile-verify node runs the full build after all translation is complete.

### Split by Platform (REQUIRED for multi-platform projects)
For projects with web + mobile + backend: one compile-verify node per platform.
Each has distinct build toolchains that may require different environments:
- `compile-verify-web` — Node.js + bundler
- `compile-verify-api` — Go/Python/Java
- `compile-verify-flutter` — Flutter SDK + Dart
- `compile-verify-ios` — Xcode + CocoaPods/SPM
- `compile-verify-android` — Android SDK + Gradle
- `compile-verify-unity` — Unity Editor (batchmode) + target SDK
- `compile-verify-unreal` — Unreal Build Tool + target SDK

**Do NOT combine `flutter build` and `npm run build` in one node** — different SDKs,
different failure modes, different fix strategies.

### Merge with Another Capability
For single-platform projects with few components: merge translate + compile-verify into a single node.
