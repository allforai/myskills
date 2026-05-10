---
name: bootstrap
description: >
  Internal skill for /bootstrap command. Performs lightweight project analysis,
  generates project-specific node-specs and workflow.json, validates products,
  and writes to target project. Use when user runs /bootstrap.
---

# Bootstrap Protocol v0.2.0

## Overview

Bootstrap analyzes a target project and generates project-specific configurations:
- node-specs (one per workflow node, fully specialized)
- workflow.json (node graph + transition log)
- .claude/commands/run.md (orchestrator entry point)

All generated products are written to the target project directory.
Products are disposable — regenerate anytime with `/bootstrap`.

---

## Step 1: Lightweight Analysis

> Goal: Understand the project enough to generate good node-specs.
> NOT a deep scan — just "what does this project look like?"

### 1.0 Detect Existing State

Before analyzing code, check if this project already has artifacts:

```bash
ls .allforai/product-map/ .allforai/experience-map/ .allforai/use-case/ .allforai/bootstrap/ 2>/dev/null
```

Record what exists:
- `has_product_artifacts`: true if product-map/task-inventory.json exists
- `has_experience_map`: true if experience-map/experience-map.json exists
- `has_bootstrap`: true if bootstrap/workflow.json exists (previous /bootstrap run)
- `has_code`: true if source code files (*.ts, *.tsx, *.js, *.mjs, *.go, *.py, *.cs, *.rs, *.dart, *.swift, *.kt, *.java, *.cpp, *.c, *.rb, *.lua, *.luau, *.server.luau, *.client.luau, *.gd, *.hx, *.p8, *.p8.png, *.twee, *.tw, etc.) are detected in Step 1.1. Config-only files (package.json, Cargo.toml, go.mod, pubspec.yaml, pom.xml with no src/) do NOT set has_code = true. Notes: *.p8 PICO-8 cartridges embed Lua code; *.luau is Roblox's Luau dialect (Rojo projects use .luau not .lua); *.twee/*.tw are Twine story source files.
- `has_iteration_feedback`: true if product-concept/iteration-feedback.json exists (previous concept-acceptance feedback)
- `has_product_concept`: true if product-concept/product-concept.json exists
- `has_decision_journal`: true if product-concept/decision-journal.json exists (previous /journal records)
- `has_concept_drift`: true if ANY of the following conditions hold:
  - `product-concept/concept-drift.json` exists AND its `resolved` field is false
  - `.allforai/game-design/approval-records.json` exists AND any record has `gate_status == "revision-requested"` (in-flight revision cycle on a design gate)
  - `.allforai/game-design/approval-records.json` exists AND any record has non-empty `revision_notes` AND `gate_status == "approved"` (a previous revision was re-approved — downstream consumers may need re-execution)
  - (when `is_game_project = false`) `.allforai/app-design/approval-records.json` exists AND any record has `gate_status == "revision-requested"` (in-flight revision cycle on an app design gate)
  - (when `is_game_project = false`) `.allforai/app-design/approval-records.json` exists AND any record has `gate_status == "approved"` AND `revision_notes` is non-empty (a previous app-design revision was re-approved — downstream consumers may need re-execution)
  
  When `has_concept_drift` is true due to approval-records (not concept-drift.json), set:
  - `concept_drift_source: "product-concept"` — when triggered by concept-drift.json (condition 1 above)
  - `concept_drift_source: "game-design-gate"` — when triggered by either game-design approval-records.json condition (conditions 2 or 3 above)
  - `concept_drift_source: "app-design-gate"` — when triggered by either app-design approval-records.json condition (conditions 4 or 5 above, when `is_game_project = false`)

This affects Step 1.5 options:
- has_product_artifacts + has_code → verification/demo/tune options are relevant
- has_bootstrap → offer to reuse or regenerate
- no code + no artifacts → only "create" option
- has_iteration_feedback → LLM reads feedback in Step 2, prioritizes fixing previous gaps in Step 3
- has_concept_drift → Step 3 uses incremental re-planning (Step 3.0) instead of full planning

### 1.1 Read Root Indicators

Read these files if they exist (skip missing ones silently):

**Package managers / language markers:**
- package.json, package-lock.json, yarn.lock, pnpm-lock.yaml
- bun.lockb (Bun runtime lock file — treat as `runtime: bun`; also check `package.json` scripts for `bun run` to confirm)
- app.json with `"expo"` key at root, OR eas.json, OR package.json with `expo` in dependencies → `framework: Expo (React Native)`. Then check for bare workflow: if `ios/Podfile` AND `android/build.gradle` both exist → `architecture_pattern: 'mobile-rn-bare'` (bare workflow; use Xcode/Gradle + EAS Build; Detox/Maestro for E2E). If NOT present → `architecture_pattern: 'mobile-rn-expo'` (managed workflow; use `npx expo export` for local bundle check + EAS Build for binaries; Maestro preferred for E2E).
- go.mod, go.sum
- go.work (Go multi-module workspace — treat as monorepo; each `use ./sub` entry is a separate Go module; list all modules as separate backend modules in bootstrap-profile.json)
- Cargo.toml, Cargo.lock
- pubspec.yaml, pubspec.lock
- Podfile, Podfile.lock
- build.gradle, build.gradle.kts, settings.gradle
- requirements.txt, pyproject.toml, setup.py, Pipfile
- Gemfile, composer.json, pom.xml, *.csproj, *.sln
- mix.exs (Elixir/Phoenix)
- Package.swift (Swift Package Manager / Vapor backend)
- oh-package.json5 (HarmonyOS / ArkTS)
- *.proto files present in any directory (gRPC service definition; set `api_style: gRPC`; proto compile step required before tests — add `protoc` / `buf generate` step to node-spec)
- package.json with `@trpc/server` (tRPC API; set `api_style: tRPC`; ⚠ no REST routes to enumerate — procedures live in router definition file)
- buf.yaml at root (Buf CLI for proto schema management — always companion to gRPC; confirms proto-based API)

**Game engines:**
- ProjectSettings/ProjectVersion.txt, Assets/ (Unity)
- *.uproject, Source/ (Unreal Engine)
- project.godot (Godot). **Test framework detection**: Check `addons/gut/gut.gd` → GUT framework; check `addons/gdUnit4/bin/GdUnitCmdTool.gd` → GdUnit4 framework. Record `godot_test_framework: "GUT" | "GdUnit4" | null` in bootstrap-profile.json. If null, mark R3 as non-applicable. **Offline-first detection**: If no HTTP client imports (`HTTPClient`, `HTTPRequest`, `WebSocketClient`) found in any `.gd` or `.cs` script in the project → set `offline_first: true`; suppress `demo-forge` and `runtime-smoke-verify`.
- *.love OR (main.lua + conf.lua at root) (LÖVE2D; *.love is the packaged output, main.lua+conf.lua is the dev project; ⚠ if build.settings is also present, this is Solar2D — not LÖVE2D; Solar2D takes precedence)
- Cargo.toml with `bevy` in dependencies (Bevy/Rust); for Cargo workspaces, also check member crates (e.g., `game/Cargo.toml`, `crates/*/Cargo.toml`) — the workspace root often has no direct dependencies
- Cargo.toml with `macroquad` in dependencies (Macroquad — lightweight Rust 2D game library; verification: `cargo test` for logic; rendering tests require display — document manual test scenarios for rendering)
- Cargo.toml with `ggez` in dependencies (ggez — Rust 2D game framework; verification: same as macroquad)
- Cargo.toml with `nannou` in dependencies (Nannou — Rust creative coding / game framework; verification: `cargo test` for non-rendering logic)
- pubspec.yaml with `flame` in dependencies (Flame/Flutter game engine)
- requirements.txt or pyproject.toml with `pygame` or `pygame-ce` in dependencies (pygame / pygame-ce community edition / Python)
- requirements.txt or pyproject.toml with `panda3d` in dependencies (Panda3D — Python/C++ 3D game engine)
- requirements.txt or pyproject.toml with `ursina` in dependencies (Ursina — Python 3D game engine built on Panda3D)
- cocos-project.json (Cocos Creator)
- *.rpy or renpy/ directory (Ren'Py visual novel engine; scenario hint: narrative-adventure)
- Game.rpgproject (RPG Maker MV/MZ; scenario hint: action-rpg)
- game.project + *.script or *.go (Defold; note: *.go here is Defold's game object format, not Go language; ⚠ if go.mod is present, *.go files are Go source — only match Defold *.go when go.mod is ABSENT)
- *.c3proj (Construct 3)
- *.mgcb (MonoGame/.NET)
- game.js + game.json at project root (WeChat Mini Game; distinguished from mini programs which use app.js)
- *.yyp (GameMaker Studio 2)
- *.twee or *.tw (Twine / interactive fiction; scenario hint: narrative-adventure)
- *.rbxlx or *.rbxl (Roblox Studio place files) or default.project.json containing a `"tree"` key with `"$className": "DataModel"` (Rojo workflow for Roblox; scenario hint: multiplayer-online — Roblox is always client-server multiplayer). Additional Rojo signals: wally.toml (Roblox package manager), *.server.luau / *.client.luau files, selene.toml (Roblox linter), or selene_defs/ directory. Note: Rojo projects do NOT store .rbxl files in git — detect via project.json + .luau + wally.toml combination.
- GameScene.swift at project root or in Sources/ (SpriteKit / SceneKit — Apple's 2D/3D game frameworks for iOS/macOS)
- package.json with `phaser` in dependencies (Phaser.js — popular HTML5 / WebGL game framework)
- package.json with `kaboom` in dependencies (Kaboom.js — JavaScript game library)
- package.json with `excalibur` in dependencies (Excalibur.js — TypeScript game engine)
- build.gradle or build.gradle.kts with `com.badlogicgames.gdx:gdx` (libGDX — Java/Kotlin cross-platform game framework)
- *.sdpkg or *.csproj with `Stride.Games` in dependencies (Stride — C#/.NET game engine, formerly Xenko)
- *.gbsproj (GBStudio — Game Boy / Game Boy Color game maker; scenario hint: casual-mobile; platform capability guard applies — no IAP/push/store)
- haxelib.json with `flixel` in dependencies (HaxeFlixel — Haxe 2D game framework)
- build.settings + main.lua at project root (Solar2D / Corona SDK — Lua mobile game engine; ≠ LÖVE2D which uses conf.lua instead of build.settings; ⚠ Solar2D detection takes precedence — if build.settings is present, suppress any LÖVE2D match from *.love glob)
- *.p8 or *.p8.png at project root (PICO-8 fantasy console cartridge)
- go.mod with `hajimehoshi/ebiten` in require block (Ebitengine — Go 2D game engine)
- go.mod with `g3n/engine` in require block (g3n — Go 3D game engine)
- build.gradle.kts with `com.soywiz.korlibs.korge` in dependencies OR `id("com.soywiz.korge")` in plugins block (KorGE — Kotlin/Multiplatform game engine)
- package.json with `littlejsengine` in dependencies (LittleJS — tiny JavaScript 2D game engine)
- requirements.txt or pyproject.toml with `arcade` in dependencies (Arcade — Python 2D game framework, alternative to pygame)
- `build.gradle` or `build.gradle.kts` with `net.fabricmc:fabric-loader` in dependencies → Minecraft mod (Fabric loader). Set `architecture_pattern: 'game-mod'`, `is_game_project = true`. Fabric signals: `fabric.mod.json` in `src/main/resources/`, `*.client.json` mixin configs. Verification: `./gradlew build` for compile; functional tests require a running Minecraft instance — document as manual test scenarios. **CRITICAL: game-mod ≠ library-sdk** — do NOT suppress demo-forge (mod testing = running inside a live Minecraft game) and do NOT set architecture_pattern to 'library-sdk'.
- `build.gradle` or `build.gradle.kts` with `net.minecraftforge:forge` in dependencies → Minecraft mod (Forge loader). Set `architecture_pattern: 'game-mod'`, `is_game_project = true`. Forge signals: `src/main/resources/META-INF/mods.toml`, `forge.cfg`. Same verification and demo-forge rules as Fabric above.

**Game + Backend Mixed Project Detection:**
If a game engine is detected (Unity / Unreal / Godot / Bevy / etc.) AND a backend module is ALSO detected (*.csproj / go.mod / requirements.txt with FastAPI/Flask/Django / Gemfile / etc.) in a subdirectory (e.g., `server/`, `backend/`, `dedicated-server/`):
→ Treat as a TWO-MODULE project: `game_client` module + `backend` module
→ Set `is_game_project = true`; `architecture_pattern` describes the game engine (e.g., `game-unity`)
→ In `bootstrap-profile.json.modules[]`: create one entry per module with distinct `role`, `path`, and `build_commands`
→ Example: `modules: [{ id: "M001", role: "game_client", path: ".", ... }, { id: "M002", role: "backend", path: "server/", ... }]`
→ Generate separate `compile-verify` nodes (backend FIRST — game client may depend on shared types); separate `test-verify` nodes
→ Do NOT suppress `demo-forge` — run demo-forge against the backend API only (not the game client)
→ `runtime-smoke-verify`: suppress game client launch; smoke-test backend module only

**Game engine SDK disambiguation heuristic:**
Some SDKs have "game" or "engine" in their name but are used for non-game purposes:
- `three.js` / `babylon.js` / `A-Frame` — 3D rendering / WebXR libraries; NOT game engines by default.
  Classify as game engine ONLY if the project also has a game loop (requestAnimationFrame with game state update), a scene graph with interactive entities, and either a physics integration or a level/scene definition file.
  Otherwise treat as visualization/web frontend.
- `cocos-js` in package.json (Cocos2d-x JS binding) — same heuristic as three.js; look for scene files.
- `matter-js` / `planck.js` / `rapier.js` — physics engines, NOT game engines; classify as 'physics-library'.
  Set `is_game_project = true` only if they are co-located with a rendering layer AND interactive gameplay logic.
- `PlayFab SDK` / `GameSparks SDK` / `Nakama SDK` — game backend SDKs; set `is_game_project = true` ONLY
  if a client-side game engine is also detected. A backend-only project with PlayFab is a SaaS/backend project.
- Unity Addressables / Unity DOTS / Unity ECS in isolation (without ProjectSettings/ProjectVersion.txt)
  — likely a Unity package author project; still classify as game, but note `architecture_pattern: 'unity-package'`.

**Mobile frameworks:**
- package.json with `react-native` in dependencies but NO expo key/dependency AND no eas.json → `framework: React Native (bare workflow), architecture_pattern: 'mobile-rn-bare'`. Verification: Detox (`@testing-library/react-native` + `detox`) or Maestro for E2E; iOS: `xcodebuild`, Android: `./gradlew`. Note: bare workflow requires separate iOS (Xcode) + Android (Gradle) build configs, unlike Expo managed.
- pubspec.yaml with `flutter` as an SDK dependency but NOT `flame` in dependencies (Flame is a game engine; detect Flutter app separately from Flutter game). To determine target platform, check `pubspec.yaml`'s `flutter.platforms` field or presence of `{macos,windows,linux}/` directories vs `android/` or `ios/`: if only desktop platform directories exist → `architecture_pattern: 'mobile-flutter-desktop'`; if iOS/Android present → `architecture_pattern: 'mobile-flutter'`. Verification: for desktop, `flutter test integration_test/` with desktop device target; for mobile, `flutter test integration_test/` on iOS Simulator / Android Emulator. **Offline-first exception**: if `drift` (or `drift_sqflite`) is in `pubspec.yaml` dependencies AND no backend module is detected (no go.mod, no Cargo.toml, no package.json with Express/FastAPI/etc.) → set `offline_first: true` in bootstrap-profile.json. Suppress `demo-forge` (no backend API to drive data population — Drift persists directly to local SQLite) and `runtime-smoke-verify` (no HTTP server to health-check). Note: "Offline-first Flutter+Drift detected — demo-forge and runtime-smoke-verify suppressed (no backend API)."
- build.gradle.kts with `kotlin("multiplatform")` plugin AND `sourceSets { commonMain ... iosMain ... androidMain }` → `framework: Kotlin Multiplatform Mobile (KMM), architecture_pattern: 'mobile-kmm'`. KMM shares business logic across iOS/Android; two separate client modules (iOS Swift + Android Kotlin) consume the shared Kotlin module. Verification: `./gradlew :shared:test` for shared module; platform-specific tests for iOS (XCTest) and Android (instrumentation). Cross-module stitch applies — shared module API must be validated against both platform consumers.

**Web SSR frameworks (additional detections):**
- package.json with `@sveltejs/kit` in dependencies OR `svelte.config.js` at root with `@sveltejs/kit/vite` adapter → `framework: SvelteKit, architecture_pattern: 'web-ssr-sveltekit'`. Verification: `npm run test` (vitest) for unit tests, Playwright for E2E (SvelteKit has first-class Playwright integration).
- package.json with `nuxt` OR `@nuxt/kit` in dependencies OR `nuxt.config.ts/js` at root → `framework: Nuxt (Vue SSR), architecture_pattern: 'web-ssr-nuxt'`. Verification: `nuxt test` (Nuxt's built-in testing module) or Playwright for E2E.
- astro.config.mjs or astro.config.ts at root OR package.json with `astro` in dependencies → `framework: Astro, architecture_pattern: 'web-ssg-astro'`. Verification: Playwright for E2E on built output; `astro check` for TypeScript/component errors.
- package.json with `@remix-run/node` OR `@remix-run/react` in dependencies → `framework: Remix, architecture_pattern: 'web-ssr-remix'`. Verification: Playwright for E2E; `remix vite:build` for compile check.
- package.json with `gatsby` in dependencies → `framework: Gatsby (React SSG), architecture_pattern: 'web-ssg-gatsby'`. Verification: `gatsby build` + Playwright on built site.

**Desktop app frameworks:**
- src-tauri/tauri.conf.json OR src-tauri/Cargo.toml → Tauri desktop app. Detect version: if `src-tauri/capabilities/` directory exists → Tauri v2 (new fine-grained Capabilities permission system); otherwise Tauri v1 (broad allowlist). Set `architecture_pattern: 'desktop-app-tauri'` and `tauri_major_version: 2` or `1` in bootstrap-profile.json. Build command: check `package.json` for `"tauri"` script → `npm run tauri build`; fallback `cargo tauri build`. Tauri v2 security note: IPC permissions now defined per-capability in `src-tauri/capabilities/*.json` — security-design must review capability scopes. demo-forge suppression: Tauri has a local web frontend; demo-forge runs against the Tauri dev server (`npm run tauri dev`). runtime-smoke-verify uses tauri-driver, not curl.
- electron.js OR electron-builder.json OR package.json with `electron` as a top-level dependency (Electron — desktop app with Node.js backend; architecture_pattern: 'desktop-app-electron')

**Library / SDK / published package:**
Detect a project as a publishable library (not an app) when ALL of the following hold:
- package.json has a `"main"` or `"exports"` field pointing to a dist/lib directory (NOT `"scripts.start"`) AND has no app-like entry points (no `src/App.tsx`, no `pages/`, no `app/`), OR
- pyproject.toml / setup.py / setup.cfg with a `[tool.poetry]` section that has `packages =` but no Django/Flask/FastAPI dependency in `[tool.poetry.dependencies]`, OR
- Cargo.toml with `[lib]` section and no `[[bin]]` section, OR
- pom.xml with `<packaging>jar</packaging>` (not war/ear), AND no `main()` entry class in src/main, OR
- haxelib.json present (HaxeFlixel/other Haxe libraries are themselves publishable packages)
Set: `architecture_pattern: 'library-sdk'`. **Verification note**: library projects do NOT need a running server; test with the language's native test runner (`npm test`, `cargo test`, `pytest`, `mvn test`). **demo-forge suppression**: when `architecture_pattern = 'library-sdk'`, suppress `demo-forge` from all goals — library projects have no running service to populate data into. Note in bootstrap output: "Library/SDK project detected — demo-forge omitted (no live server to populate)."

**CLI tool exception**: A package.json with a `"bin"` field (object mapping command names to entry scripts, e.g., `"bin": { "mycli": "dist/cli.js" }`) is a CLI tool, NOT a library. Set `architecture_pattern: 'cli'`, record `bin_commands: [<key names>]` in bootstrap-profile.json. Compile check: `npm run build` or `tsc`; smoke: `node dist/cli.js --help` → exit 0. demo-forge suppression: CLI has no running HTTP service — suppress demo-forge. **detection precedence**: if both `bin` and `main` exist (CLI + importable library), prefer 'cli' classification; note dual-use in bootstrap output.

**Embedded / firmware:**
- platformio.ini at root (PlatformIO — cross-platform embedded development for Arduino, ESP32, STM32, etc.; architecture_pattern: 'embedded-firmware'). Verification: `pio test` for unit tests (PlatformIO's native test runner runs on-device or via embedded simulator); full device tests require physical hardware or QEMU — document as manual test scenarios. demo-forge suppression: firmware has no HTTP service; suppress demo-forge. runtime-env setup: physical device or QEMU emulator setup may be needed.
- *.ino at project root with no game engine marker (Arduino sketch; architecture_pattern: 'embedded-firmware'). If platformio.ini is also present, platformio.ini takes precedence. ⚠ `.ino` files in game projects (e.g., Construct 3 exports) are NOT Arduino — only match when no game engine markers are present.

**CI/CD action / marketplace packages:**
- `action.yml` at root with a `runs:` key (GitHub Actions custom action / reusable action; architecture_pattern: 'github-action')
- `action.yaml` at root with a `runs:` key (same; yaml extension variant)

**Chat bots / event-driven services:**
- package.json with `discord.js` OR requirements.txt/pyproject.toml with `discord.py` / `nextcord` / `py-cord` → Discord bot. architecture_pattern: `'bot-discord'`. No HTTP routes — event-driven. Verification: mock Discord client (discord.js) / pytest+AsyncMock (discord.py). demo-forge suppression: suppress unless bot has a separate web dashboard or API.
- package.json with `@slack/bolt` OR `slack` OR requirements.txt with `slack-sdk` / `slack-bolt` → Slack bot. architecture_pattern: `'bot-slack'`. Verification: jest/vitest with mocked Slack payloads; `@slack/bolt` test utilities. Smoke: POST mock event JSON to `/slack/events` endpoint.
- package.json with `telegraf` OR `node-telegram-bot-api` → Telegram bot (Node.js). architecture_pattern: `'bot-telegram'`. Verification: jest with mocked Telegram Update objects. Smoke: POST fake update JSON to webhook endpoint.
- requirements.txt or pyproject.toml with `python-telegram-bot` OR `aiogram` OR `telebot` → Telegram bot (Python). architecture_pattern: `'bot-telegram'`. Verification: pytest with mocked `telegram.Update` and `ContextTypes`. Smoke: POST fake update to FastAPI/webhook handler.
- ⚠ Bots with a companion web API/backend (webhook handler + DB): create TWO modules — bot logic module + API/webhook module. Generate separate test-verify nodes for each. Bot smoke test hits the webhook endpoint directly.

**Desktop app plugin / extension frameworks:**
- `manifest.json` at root with both `"id"` and `"minAppVersion"` fields AND `package.json` with `obsidian` in `devDependencies` or `dependencies` (Obsidian plugin; architecture_pattern: 'ide-plugin-obsidian'). Note: do NOT rely on a `.obsidianplugin` file — it does not exist in the Obsidian ecosystem.
- package.json with `@types/vscode` in devDependencies AND `"contributes"` section OR `.vscodeignore` present (VS Code extension; architecture_pattern: 'ide-plugin-vscode')
- manifest.json at root with `"manifest_version"` key AND `"browser_action"` or `"action"` or `"background"` (Browser extension; architecture_pattern: 'browser-extension')

**Deployment platform markers:**
- `vercel.json` at root OR `package.json` scripts containing `"vercel"` as a value OR `vercel` as a direct devDependency → Vercel-deployed project. Set `deployment_platform: 'vercel'` in bootstrap-profile.json. Vercel IS the infrastructure — Step 3 MUST suppress the `infra-design` node. Note in bootstrap output: "Vercel deployment detected — infra-design omitted (Vercel is the infrastructure)." The `architecture_pattern` remains unchanged (e.g., Next.js stays 'web-nextjs' — Vercel is the deploy target, not the framework).
- `deno.json` with a `deploy` or `deployments` section, OR `.github/workflows/*.yml` containing `denoland/deployctl-action`, OR `import_map.json` with `deno.land/x/deployctl` imports → Deno Deploy deployment. Set `deployment_platform: 'deno-deploy'` in bootstrap-profile.json. Deno Deploy IS the infrastructure (KV store, Edge execution, HTTP routing) — Step 3 MUST suppress `infra-design`. Note: "Deno Deploy detected — infra-design omitted (Deno Deploy is the infrastructure)." Create minimal `infra-design.json` documenting Deno KV requirements and environment variable names.

**Backend-as-a-Service (BaaS) / cloud-native:**
BaaS projects have NO separate backend module — the backend IS the cloud service. Set `architecture_pattern: 'baas-<provider>'` and do NOT create a separate backend module in the workflow.
- package.json with `firebase` OR `firebase-admin` in dependencies → BaaS: Firebase. Runtime-env: `FIREBASE_PROJECT_ID`, Firebase emulator suite (`firebase emulators:start`) for local testing. Verification: Playwright for E2E on the frontend; Firebase emulator for integration tests (Auth, Firestore, Functions). architecture_pattern: 'baas-firebase'
- package.json with `@supabase/supabase-js` in dependencies → BaaS: Supabase (PostgreSQL + Auth + Realtime). Runtime-env: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, optionally `SUPABASE_SERVICE_ROLE_KEY`. Verification: Playwright for E2E; Supabase local dev (`supabase start`) for integration. architecture_pattern: 'baas-supabase'
- amplify.yml at root OR package.json with `aws-amplify` OR `@aws-amplify/backend` → BaaS: AWS Amplify. Runtime-env: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`. architecture_pattern: 'baas-amplify'
- package.json with `@appwrite/sdk` → BaaS: Appwrite. architecture_pattern: 'baas-appwrite'
- package.json with `pocketbase` npm package OR `pocketbase-sdk` → BaaS: PocketBase (self-hosted Go binary with embedded SQLite, serves REST API + realtime SSE, provides Auth + File storage + DB in one process). Runtime-env: `POCKETBASE_URL` (e.g., `http://localhost:8090`), `PB_ADMIN_EMAIL`, `PB_ADMIN_PASSWORD`. Local dev: `pocketbase serve`. Note: PocketBase runs as a single Go binary; there is no separate message queue, no separate auth service, no SDK-managed schema — schema is managed via PocketBase Admin UI. Verification: Playwright for E2E on the frontend; PocketBase Admin REST API for integration tests. architecture_pattern: 'baas-pocketbase'

**Serverless / FaaS (Function-as-a-Service):**
Serverless projects deploy functions; there is NO persistent server process to start. Verification is via local emulator, NOT `curl localhost`.
- serverless.yml or serverless.ts at root (Serverless Framework; deploys to AWS Lambda, Azure Functions, GCP Cloud Functions). Runtime-env: AWS credentials OR cloud credentials. Local testing: `serverless-offline` plugin for HTTP triggers. architecture_pattern: 'serverless-framework'
- `sam-template.yaml` or `template.yaml` with `AWSTemplateFormatVersion: 2010-09-09` → AWS SAM (Serverless Application Model). Local testing: `sam local start-api`. architecture_pattern: 'serverless-sam'
- functions/ directory with `wrangler.toml` at root → Cloudflare Workers. Local testing: `wrangler dev`. architecture_pattern: 'serverless-cf-workers'
- ⚠ Serverless projects: demo-forge suppression does NOT apply (functions handle HTTP requests). Use serverless-offline or SAM local as the "live environment" for demo-forge data population.

**Monorepo orchestrators:**
- pnpm-workspace.yaml + turbo.json → Turborepo monorepo. Each entry in `apps/` is a frontend/backend/mobile app module; each entry in `packages/` is a shared internal library (classify as `role: shared`). Set `architecture_pattern: 'monorepo-turborepo'`.
- nx.json at root + `apps/` + `libs/` directories → Nx monorepo. Each app in `apps/` is a separate module; `libs/` contains shared packages. Set `architecture_pattern: 'monorepo-nx'`. Check `nx.json.projects` or `project.json` files for per-app details.
- pnpm-workspace.yaml WITHOUT turbo.json → plain pnpm workspace (monorepo without task orchestration). Enumerate workspace `packages[]` glob to find modules.
⚠ For ALL monorepo types: enumerate EVERY app/package entry and create a separate module entry in `bootstrap-profile.json.modules[]` per deployable unit. Internal shared packages that are NOT standalone deployments get `role: shared`.

**Configuration:**
- tsconfig.json, jsconfig.json
- vite.config.*, webpack.config.*, next.config.*
- deno.json, deno.jsonc (Deno runtime — if also `islands/` and `routes/` directories are present, classify as Deno Fresh SSR framework; architecture_pattern: 'deno-fresh-islands'. Verification note: Deno Fresh uses `Deno.test` with `@std/testing` library; check for `deno task test` command in deno.json tasks.)
- docker-compose.yml, Dockerfile
- .github/workflows/*.yml, .gitlab-ci.yml, Jenkinsfile
- .env.example, .env.template

**Documentation:**
- README.md, README.rst
- docs/ directory (list contents, read first .md file)
- ARCHITECTURE.md, CONTRIBUTING.md

From these, extract:
- Language(s) + version hints
- Framework(s) + version
- Package manager
- Build tool
- State management (frontend)
- ORM / database (backend)
- CI/CD tool
- Containerization

### 1.2 Scan Directory Structure (1-2 levels deep)

```bash
ls -la  # root level
```

For each top-level directory that looks like a code module (not node_modules, .git, etc.):
```bash
ls <dir>/  # one level deeper
```

From this, identify:
- Module boundaries (frontend vs backend vs shared vs mobile vs infra)
- Monorepo structure (if applicable)
- Frontend/backend separation pattern

### 1.3 Sample Core Files (3-5 files)

Read these (pick the most informative):
- Main entry point (main.go, index.ts, app.py, App.tsx, etc.)
- Primary router/route definition file
- One data model / schema file
- One UI component (if frontend exists)
- One configuration/middleware file

From these, extract:
- Architecture pattern (MVC, Clean, Layered, Feature-sliced, etc.)
- Code style (naming conventions, file organization)
- State management approach
- API style (REST, GraphQL, gRPC)

### 1.4 Read README/Docs for Business Context

If README.md exists, read it for:
- Project purpose / business domain
- Core user flows described
- Technology decisions explained

### 1.5 Collect Target Information (Interactive)

Ask the user ONE combined question. Format depends on detected state (from Step 1.0):

**If code + artifacts exist (has_code + has_product_artifacts):**

```
检测到已有代码和 .allforai/ 产物。请确认目标（可多选）：

   a) 逆向分析（重新生成 .allforai/ 产物）
   b) 跨栈复刻（翻译到目标技术栈）
   c) 同栈重建（按目标架构重新生成）
   e) 代码治理（架构合规 + 重复检测 + 抽象分析）
   f) 演示数据（生成 demo-ready 数据集）
   g) UI 精修（UI 还原度修复）
   h) 功能验收（静态 + 全模块 E2E 动态验证）
   i) 视觉验收（截图对比）
   j) 质量检查（死链 + 字段一致性）
   k) 上架准备（竞品调研 → 概念定稿 → 缺口实现 → 合规 → 上架清单）
```

**If code exists but no artifacts (has_code, no has_product_artifacts):**

```
Bootstrap 分析完成。请确认目标（可多选）：

   a) 逆向分析（生成 .allforai/ 产物，理解业务）
   b) 跨栈复刻（分析 + 翻译到目标技术栈）
   c) 同栈重建（分析 + 按目标架构重新生成）
   d) 从零构建新产品（忽略已有代码，以产品愿景为起点重新设计）
   e) 代码治理（架构合规 + 重复检测 + 抽象分析）
   j) 质量检查（死链 + 字段一致性）
   k) 上架准备（竞品调研 → 概念定稿 → 缺口实现 → 合规 → 上架清单）

目标技术栈（仅 b/c/d 需回答）：
   前端：___
   后端：___

产品愿景（仅 d 需回答 — 一句话描述你要做什么）：
   ___

UI 还原度（仅有前端翻译时）：
   a) faithful — 像素级还原
   b) native — 允许平台风格差异
```

**If no code exists (empty project or only README):**

```
当前目录没有检测到已有代码。请确认目标：

1. 目标：
   d) 从零构建新产品

2. 产品愿景（一句话描述你要做什么）：
   ___

3. 目标技术栈：
   前端：___
   后端：___
   移动端：___（如有）

4. 业务领域：
   a) 电商  b) 金融  c) 医疗  d) SaaS  e) 社交  f) 游戏  g) 其他：___

5. 基础设施需求（可选，复杂项目建议回答）：
   实时通信：___（如 WebSocket/gRPC/SSE/无）
   消息队列：___（如 Kafka/NATS/Redis Pub-Sub/无）
   文件存储：___（如 S3/MinIO/本地/无）
   搜索引擎：___（如 Elasticsearch/Meilisearch/无）
```

**If game engine detected in Step 1.1 AND user has NOT explicitly selected 业务领域 f) 游戏:**

**If `game_engines_detected` has 2+ entries (multiple engines detected):** First disambiguate before game/non-game confirmation:

```
检测到多个游戏引擎标记：[engine1], [engine2]。请确认主引擎：
   a) 主引擎是 [engine1]（[engine2] 为工具/辅助依赖）
   b) 主引擎是 [engine2]（[engine1] 为工具/辅助依赖）
   c) 这不是游戏项目（引擎仅用于工具/可视化/仿真）
```

If user selects (c): `is_game_project = false`. Otherwise, keep only the selected primary engine in `game_engines_detected`.

**If `game_engines_detected` has exactly 1 entry:** Confirm the project type:

```
检测到 [引擎名] 项目，请确认项目类型：
   a) 游戏项目（继续选择游戏品类）
   b) 非游戏 VR/AR 体验（沉浸式可视化 / 训练仿真 / 工业 AR / 医疗 XR 等）
   c) 非游戏可视化/仿真工具（数据可视化、物理仿真、建筑可视化等）
   d) 其他非游戏用途（请说明）
```

If user selects (b): set `is_game_project = false`, `architecture_pattern: 'xr-experience'`. Treat
engine as tech stack context, load `knowledge/domains/xr.md` if available as supplementary reference.
If user selects (c): set `is_game_project = false`, `architecture_pattern: 'visualization-sim'`.
If user selects (d): set `is_game_project = false`, record user's description in `business_context`.
For all non-game selections: skip game scenario selection entirely and proceed with normal bootstrap flow.

**If business_domain = "gaming" confirmed (user selected (a) above, or explicitly chose
业务领域 f) 游戏 in the no-code prompt):**

After confirming the main goal, ask ONE additional question.

If the detected engine has a **scenario hint** (marked in the game engines list above as "scenario hint: X"), pre-mark that option with `[推荐]` in the list. The user can override — they are not locked in.

```
游戏品类（选一）：
   a) 超休闲/中度手游 (casual-mobile)
   b) 动作/卡牌/RPG (action-rpg)         ← [推荐] if RPG Maker detected
   c) 在线多人 MMO/MOBA/FPS (multiplayer-online)
   d) 肉鸽/Roguelite (roguelike)
   e) 策略/模拟经营 (strategy-sim)
   f) 叙事/视觉小说/AVG (narrative-adventure)  ← [推荐] if Ren'Py / Twine detected
```

If the user's game doesn't fit any template exactly, suggest the closest match:
- 体育/运动游戏 (FIFA/NBA style) → e) 策略/模拟经营 (team management + balance focus)
- 格斗游戏 (Street Fighter style) → b) 动作/卡牌/RPG (combat system focus)
- 沙盒/开放世界 (Minecraft style) → b) or e) depending on combat vs. economy emphasis
- 音乐/节奏游戏 (Guitar Hero style) → a) 超休闲/中度手游 (session design + retention focus)
- 益智/解谜 (Wordle/casual puzzle) → a) 超休闲/中度手游
- 放置/挂机/增量游戏 (idle/incremental — e.g. Cookie Clicker, AdVenture Capitalist) → e) 策略/模拟经营 (economy-design + progression-curve-design focus; session loop is offline accumulation, NOT retention-hook); note: present disambiguation to user if unclear between idle and strategy: "该游戏是否有实时操作（战斗/建造），还是主要依赖离线积累？"
- 放置 RPG (AFK-style idle with hero collection) → d) 肉鸽/Roguelite OR b) 动作/卡牌/RPG depending on whether each run is discrete; note: distinguish from pure idle (no runs, continuous offline progression)
- 教育/严肃游戏 (EdTech/serious game) → a) 超休闲/中度手游 (FTUE + session design focus); note to user: "combat-system-design 对教育类游戏通常不适用，请在可选节点中跳过"
- PICO-8 / 幻想主机 / 复古风格游戏 → a) 超休闲/中度手游; note: despite the "mobile" label, treat as general casual — apply platform capability guard below
- 平台移植 (same-engine platform port, e.g., Unity PC → Unity mobile) → goal (c) 同栈重建; add note: "platform port = rebuild with target platform constraints (touch input, resolution, performance budget)"

**Platform capability guard (applies during Step 3.1 node injection):**
Some game engines/platforms structurally cannot support IAP, push notifications, or retention systems.
For these platforms, suppress `monetization-design`, `retention-hook-design`, and `meta-game-design`
from BOTH (a) the `required_nodes` list AND (b) the canonical optional eligibility pool, regardless
of what the selected scenario template declares. If these nodes appear in a template's `required_nodes`,
remove them before building the workflow — the platform constraint overrides the template:
- PICO-8 (*.p8 detected) — no store integration, no push API
- LÖVE2D standalone (*.love or main.lua+conf.lua, no build.settings) — no native store
- GBStudio (*.gbsproj) — Game Boy cartridge, no runtime monetization
- Twine/Ren'Py web export — static web narrative, no IAP
- HaxeFlixel targeting HTML5/desktop only (haxelib.json + flixel, no mobile build config) — no native store
- Roblox (default.project.json or *.rbxl detected) — DOES have its own monetization (Robux, Developer Products, Game Passes, Limited Items via DevEx), but these use the **Roblox economy API**, NOT App Store IAP/StoreKit/Google Play Billing. Suppress generic `monetization-design` and `launch-prep` IAP compliance nodes. Instead inject `roblox-monetization-design` as optional node (covers Robux product setup, premium payouts, DevEx setup). Do NOT suppress retention-hook-design (Roblox supports daily login rewards via DataStore + RemoteEvent).
Note in the bootstrap output: "Platform [{engine}] does not support IAP/push — monetization/retention nodes removed from workflow (required and optional)."

The template is a STARTING POINT. The user can add or remove nodes via the optional node question that follows.

Map answer to `game_scenario` field in bootstrap-profile.json.
If no scenario hint and user is unsure, suggest `action-rpg` as default (broadest node set).

After the user selects a scenario, bootstrap reads the selected template's `bootstrap_note`
(if present). If the note lists ad-hoc optional nodes, present them as a follow-up question:

```
以下功能模块可选（非必需）：
   [list nodes from bootstrap_note, one per line with short description]
   需要加入哪些？（可多选，直接回车跳过）
```

**Canonical optional nodes** (those that appear in the template's `node_order`) form an *eligibility pool* — not an auto-include list. Bootstrap selects from the pool based on project signals. Examples of project signals:
- Include `narrative-design` / `branching-structure-design` / `character-arc-design` / `dialogue-system-spec` only if the game has explicit narrative or branching dialogue (not for hack-and-slash, idle, or sports games)
- Include `combat-system-design` and `competitive-balance-design` only if the game has combat or PvP mechanics
- Include `puzzle-design` only if the game has dedicated puzzle content
- Include `retention-hook-design` / `meta-game-design` for mobile games with session loops
- Include `monetization-design` as **strongly recommended** (annotate with `[推荐]` in opt-in question) for any `casual-mobile` scenario game targeting Android/iOS (detected from Unity mobile build targets, Android/iOS in *.uproject target platforms, `pubspec.yaml` Flutter targets, or similar). Exception: apply platform capability guard (PICO-8, LÖVE2D, etc.) first.
- Include `economy-design` / `tech-tree-design` for RTS games (in multiplayer-online scenario) or strategy games
- Include `level-design` for games with designed maps, levels, or zones

**Ad-hoc optional nodes** (those listed in `bootstrap_note` but NOT in `node_order`) MUST be explicitly presented to the user for opt-in. When parsing `bootstrap_note`, identify ad-hoc nodes as those with phrases like "not in canonical node registry" or those absent from `node_order`. Do NOT re-present canonical optional nodes (already in `node_order`) in the user opt-in question — they are handled automatically by bootstrap's context judgment.

**Goal mapping (can combine multiple):**
- (a) → `goals: ["reverse-concept", "analyze"]`. reverse-concept is mandatory for analyze — without it, product-analysis has no independent baseline and becomes circular (checking code against code-derived artifacts). reverse-concept produces concept-baseline.json which all downstream phases auto-load.
- (b) → `goals: ["analyze", "translate", "demo", "concept-acceptance"]`, record target_stacks. demo-forge is auto-included because translate produces code that needs integration testing. concept-acceptance is auto-included when product-concept.json exists. **Auto-prepend `reverse-concept` when `concept-baseline.json` does not exist** (required for analyze — without it product-analysis has no independent baseline; if concept-baseline.json already exists from a prior run, skip).
- (c) → `goals: ["analyze", "rebuild", "demo", "concept-acceptance"]`, record target_stacks. demo-forge is auto-included because rebuild produces code that needs integration testing. concept-acceptance is auto-included when product-concept.json exists. **Auto-prepend `reverse-concept` when `concept-baseline.json` does not exist** (same baseline requirement as (b)).
- (d) → `goals: ["create", "demo", "concept-acceptance"]`, record target_stacks + product_vision. demo-forge is auto-included because new code needs integration testing. concept-acceptance is auto-included when product-concept.json exists.
- (e) → `goals: ["tune"]`
- (f) → `goals: ["demo"]`
- (g) → `goals: ["ui-forge"]`
- (h) → `goals: ["product-verify"]`
- (i) → `goals: ["visual-verify"]`
- (j) → `goals: ["quality-checks"]`
- (k) → `goals: ["launch-prep"]`. When product-concept artifacts don't exist, auto-prepend `reverse-concept` (need concept baseline before making launch decisions). launch-prep includes competitive research → concept finalization → gap implementation → compliance → checklist. The competitive research phase MUST run before any pricing/tier decisions are presented to the user — never ask the user to pick a price without data.
- Combinations: user can select e.g. "a + e" or "h + i + j" (full verification suite)

**Goal Combination Ordering Rules (enforced in generated workflow.json):**
When the user selects multiple goals, the generated workflow MUST enforce this dependency order:
```
1. reverse-concept           (if needed as baseline — auto-prepended for analyze/launch-prep)
2. analyze / product-analysis (depends on reverse-concept)
3. translate / rebuild / create (depends on analyze if present)
4. demo-forge (depends on implementation)
5. quality-checks / tune     (can run on any completed implementation)
6. product-verify            (depends on implementation)
7. launch-prep               (depends on all: code + verify + concept)
```
Example: goal (a) + (j) → workflow order: reverse-concept → product-analysis → quality-checks (NOT quality-checks first)
Example: goal (b) + (k) → workflow order: analyze → translate → demo → product-verify → launch-prep (launch-prep BLOCKED BY product-verify)
Example: goal (h) + (i) + (j) → product-verify → visual-verify → quality-checks (can run in parallel after implementation)
These ordering rules are enforced via `blocked_by` in workflow.json — not left to LLM judgment at /run time.
- **demo-forge is automatically added** to any goal that includes code implementation (translate/rebuild/create). Reason: API-driven data population is the strongest integration test — it exposes runtime issues that compile-verify cannot catch (wrong routes, missing fields, broken relationships, auth failures).
- **concept-acceptance is automatically added** to any goal that includes code implementation (translate/rebuild/create) AND (`has_product_concept` is true OR `is_game_project` is true). For game projects, concept-acceptance uses `game-design-doc.json` as baseline (see `capabilities/concept-acceptance.md § Prerequisite`). Reason: without verifying the final product experience against the original concept, the development loop never closes — product-verify checks code vs design artifacts, but not experience vs concept.
- **runtime-smoke-verify is automatically added** to any goal that includes code implementation (translate/rebuild/create) OR launch-prep. Reason: test-harness verification cannot catch runtime contract bugs that only surface when the artifact launches outside the harness (env-var dual-contracts, URL prefix drift, missing signing / provisioning, deep-link breakage). See `knowledge/capabilities/runtime-smoke-verify.md`. Ordering: runs **after** product-verify passes (when product-verify is in the graph) OR immediately **before** launch-checklist (when goals include launch-prep but NOT product-verify — no product-verify gate to wait for). Added 2026-04-14 after a retrospective incident where a full UI test suite passed but manual app launch hit a 404 on the first request — same env-var name parsed differently between tests and the production runtime.

### 1.5.1 Runtime Environment Awareness (when goals include code implementation)

When goals include translate/rebuild/create (b/c/d), demo-forge will run and needs a live
environment. Bootstrap does NOT collect env details here — that is the job of a generated
node-spec.

**What bootstrap does in this step:**

1. Note that goals require runtime environment
2. In Step 3 (Plan Workflow), if the project needs runtime environment setup (databases,
   caches, AI services, storage, auth, etc.), LLM should include a runtime environment
   setup node as an **early node before any code execution** (before demo-forge, before
   any service startup). The node name should be project-specific (e.g.,
   `setup-env-go-pg-redis`, `configure-aws-services`).
3. The runtime environment node-spec is **project-specific** — LLM generates it based on
   Step 1.1-1.4 analysis (detected databases, caches, AI services, storage, auth, etc.)

**What the generated runtime environment node does (at /run time):**

1. Read `.env.example`, `docker-compose.yml`, config files to identify all required env vars.
   For **event-driven service projects** (Discord/Slack/Telegram bots, webhook consumers), also
   identify the primary service authentication token from `package.json` dependencies and `.env.example`:
   - `discord.js` dependency (Node.js) OR `discord.py` / `nextcord` / `py-cord` in requirements.txt (Python) → prompt for `DISCORD_TOKEN` + `DISCORD_APPLICATION_ID`
   - `@slack/bolt` dependency → prompt for `SLACK_BOT_TOKEN` + `SLACK_SIGNING_SECRET`
   - `telegraf` or `node-telegram-bot-api` (Node.js) OR `python-telegram-bot` in requirements.txt (Python) → prompt for `TELEGRAM_BOT_TOKEN`
   These tokens are the most critical runtime credentials for event-driven bots and are NOT
   covered by database/cache/auth service detection.
   For **Python async task queue projects** (detected from `requirements.txt` or `pyproject.toml`):
   - `celery` or `celery-beat` in requirements → prompt for `CELERY_BROKER_URL` (Redis: `redis://localhost:6379/0`; RabbitMQ: `amqp://...`) and `CELERY_RESULT_BACKEND`; record worker startup command (`celery -A <app_module> worker --loglevel=info`); if `celery-beat` present, record beat startup (`celery -A <app_module> beat`); if `flower` present, record dashboard port (default 5555).
   - `redis` or `redis-py` in requirements → prompt for `REDIS_URL`; double-check if this Redis is also used as Celery broker (common pattern = one Redis instance serving both roles).
   For **BaaS projects**, also identify service credentials from dependency analysis:
   - `firebase` / `firebase-admin` → prompt for `FIREBASE_PROJECT_ID`, `FIREBASE_API_KEY`, service account JSON path (for admin SDK); offer to configure Firebase Emulator Suite (`firebase emulators:start`)
   - `@supabase/supabase-js` → prompt for `SUPABASE_URL`, `SUPABASE_ANON_KEY`, optionally `SUPABASE_SERVICE_ROLE_KEY`; offer Supabase local (`supabase start`)
   - `aws-amplify` / `@aws-amplify/backend` → prompt for `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `AWS_USER_POOLS_ID`, `AWS_USER_POOLS_WEB_CLIENT_ID`
   - `@appwrite/sdk` → prompt for `APPWRITE_ENDPOINT`, `APPWRITE_PROJECT_ID`, `APPWRITE_API_KEY`
   For **Apple cloud services** (detected from entitlements files or Swift imports):
   - CloudKit entitlement (`*.entitlements` with `com.apple.developer.icloud-container-identifiers`) → note: CloudKit requires a real Apple Developer account + provisioned container; no local emulator available. Verify container name from entitlements file. Document as "CloudKit testing requires physical device or iOS Simulator with iCloud signed-in account."
   - Sign in with Apple (`com.apple.developer.applesignin` entitlement) → similar constraint: requires Apple account; mock via XCTest's `ASAuthorizationAppleIDProvider` mocking for unit tests.
2. Check what's already configured (`.env` exists? docker-compose covers it? service reachable?)
3. Ask the user for ONLY missing items (project-specific, not a fixed template)
4. Write/update `.env`, verify services are reachable
5. Record runtime state in `.allforai/bootstrap/runtime-env.json`

**Why a node, not a bootstrap step?**
- Bootstrap is a template — it doesn't know project-specific env vars
- The node-spec is generated by LLM after analyzing the project — it knows exactly what to ask
- The node runs at `/run` time with interactive access to the user
- If the user re-runs `/run` later, the node re-validates (env may have changed)

### 1.6 Output bootstrap-profile.json

Write to `.allforai/bootstrap/bootstrap-profile.json`:

```json
{
  "schema_version": "1.0",
  "project_name": "<from directory name or package.json name>",
  "business_domain": "<inferred: ecommerce/fintech/healthcare/saas/social/gaming/...>",
  "business_context": "<1-2 sentence description of what this project does>",
  "tech_stacks": [
    {
      "role": "frontend | backend | mobile | shared",
      "language": "<language>",
      "language_version": "<version if detectable>",
      "framework": "<framework name + version>",
      "state_management": "<if applicable>",
      "router": "<if applicable>",
      "orm": "<if applicable>",
      "db": "<if applicable>",
      "build_tool": "<vite/webpack/go build/cargo/...>"
    }
  ],
  "goals": ["reverse-concept | analyze | translate | rebuild | create | tune | demo | ui-forge | product-verify | visual-verify | quality-checks | launch-prep | concept-acceptance | runtime-smoke-verify"],
  "product_vision": "<one sentence, only for goals includes create>",
  "target_stacks": [
    {
      "role": "frontend | backend | mobile",
      "language": "<target language>",
      "framework": "<target framework>"
    }
  ],
  "ui_fidelity": "faithful | native | null",
  "modules": [
    {
      "id": "M001",
      "path": "<relative path>",
      "role": "frontend | backend | shared | mobile | infra",
      "description": "<what this module contains>"
    }
  ],
  "build_commands": {
    "<role>": "<build command>"
  },
  "test_commands": {
    "<role>": "<test command>"
  },
  "detected_patterns": ["<REST API>", "<JWT auth>", "<Redis cache>", "..."],
  "architecture_pattern": "<MVC/Clean/Layered/Feature-sliced/...>",
  "complexity_estimate": "low | medium | high",
  "is_game_project": false,
  "game_engines_detected": ["<engine name(s) from Step 1.1 detection, empty if none>"],
  "game_scenario": "casual-mobile | action-rpg | multiplayer-online | roguelike | strategy-sim | narrative-adventure | null",
  "deployment_platform": "vercel | null",  // vercel when vercel.json / vercel devDep detected; null otherwise
  "offline_first": false,  // true when Flutter+Drift without backend module detected
  "requires_runtime_env": false,  // true only when goals include translate/rebuild/create; false for analyze/tune/quality-checks
  "detected_state": {
    "has_code": false,
    "has_product_artifacts": false,
    "has_bootstrap": false,
    "has_product_concept": false,
    "has_experience_map": false,
    "has_iteration_feedback": false,
    "has_decision_journal": false,
    "has_concept_drift": false
  }
}
```

> **bootstrap-profile.json vs discovery source-summary.json — no conflict:**
> bootstrap-profile.json is produced during /bootstrap phase and lives in `.allforai/bootstrap/`.
> It is NOT consumed by /run-time subagents directly. If the workflow includes a discovery node,
> that node produces `source-summary.json` by reading source code directly — it does NOT read
> bootstrap-profile.json. The two artifacts have overlapping fields (tech_stacks, modules,
> architecture_pattern, detected_patterns) but are independent: bootstrap-profile captures
> the structural view needed for workflow planning; source-summary captures the deep semantic
> view needed for code generation. Downstream node-specs reference source-summary.json only.

---

## Step 2: Load Knowledge (Reference, Not Menu)

> Goal: Absorb all available knowledge before planning.
> Capabilities are REFERENCE material — LLM reads them for methodology
> guidance, NOT as a list of nodes to select from.

### 2.1 Load All Capabilities

Read all files in `${CLAUDE_PLUGIN_ROOT}/knowledge/capabilities/*.md`.
These describe WHAT each type of work involves and WHAT methodology to apply.
They are NOT a menu — LLM will freely design nodes that may combine, split,
skip, or go beyond what any single capability describes.

### 2.2 Load Domain Knowledge

Check if `${CLAUDE_PLUGIN_ROOT}/knowledge/domains/<domain>.md` matches the
detected business_domain. If yes, load it — it contains domain-specific
design stages, theory anchors, and output artifacts that override or
supplement standard capabilities.

**Special case — `business_domain = gaming` but `is_game_project = false`:**
This occurs when a user explicitly chose 业务领域 f) 游戏 in the no-code prompt
but then the game-engine confirmation step set `is_game_project = false` (e.g.,
user confirmed "this is a game backend / game analytics SaaS / game CMS, not a
game client"). In this case:
- Do NOT load `gaming.md` as the primary domain file (it defines game-design node
  injection which does not apply to non-game projects)
- Instead, load `gaming.md` as a **cross-domain supplementary reference only**
  (methodology sections: Sink-Source, Flow Theory, monetization patterns)
- The project's actual business domain should be re-inferred from Step 1.1–1.4
  analysis (e.g., saas, fintech, ecommerce) and that domain file loaded as primary
- If no better domain match is found, proceed without a primary domain file

### 2.2.1 Cross-Domain Methodology Loading

If the product description mentions design patterns from another domain, load
that domain's methodology sections as supplementary reference (not as primary
domain override).

**Common cross-domain patterns:**
- Product uses gamification (XP, streaks, leaderboards, leagues) but is NOT a game
  → load `gaming.md` for: Sink-Source, Flow Theory, progression-system, monetization patterns
- Product has real-time chat/messaging but is NOT an IM app
  → load `social-messaging.md` for: message sync, presence, typing indicators check dimensions
- Product has marketplace/transactions but is NOT an ecommerce platform
  → load `ecommerce.md` for: payment integration, order state machine check dimensions

**Rules:**
- Cross-domain files are REFERENCE only — do not apply their 替代关系 (replacement stages)
- Only load methodology sections (theory anchors, check dimensions), skip node graphs and category tables
- Primary domain file (if any) takes precedence on conflicts

### 2.3 Load Cross-Phase Knowledge

Always load these (they apply to ALL nodes regardless of type):
- `${CLAUDE_PLUGIN_ROOT}/knowledge/cross-phase-protocols.md`
- `${CLAUDE_PLUGIN_ROOT}/knowledge/defensive-patterns.md`
- `${CLAUDE_PLUGIN_ROOT}/knowledge/product-design-theory.md`

### 2.4 Load Tech Stack Mappings (if translating)

Check if `${CLAUDE_PLUGIN_ROOT}/knowledge/mappings/<source>-<target>.md` exists.
Also check `${CLAUDE_PLUGIN_ROOT}/knowledge/learned/` and
`.allforai/bootstrap/learned/` for prior experience.

### 2.4.1 Load Blind-Spot Retrospectives (MANDATORY)

If `.allforai/bootstrap/learned/blind-spots.md` exists (project-local) OR
`${CLAUDE_PLUGIN_ROOT}/knowledge/learned/blind-spots.md` (global), LLM must
read it before Step 3 planning.

Each entry in `blind-spots.md` records a class of bug that the previous
workflow **missed** and the minimum additional check required to catch it.
For each entry with `status: scheduled` or `status: open`:

- Locate the capability that would prevent it (listed in the entry)
- Verify that capability is in the current workflow's goals or will be
  auto-added based on Step 1.5 goal mapping
- If the preventing capability is NOT in the workflow → add it in Step 3.1
  and mark the entry `status: closed` once the node is planned

This is how the workflow **learns from its own failures**. Without this,
the same class of bug slips past every bootstrap run because the system
doesn't remember what it missed. Entries with `status: closed` stay for
audit.

Format of a single entry (reference `knowledge/learned/blind-spots.md` for
the canonical template):

```markdown
## <date> — <short name>

- **Class**: <category of bug>
- **Missed**: <concrete instance>
- **Why missed**: <which node was expected to catch + what it actually did>
- **Minimum prevention**: <smallest additional check>
- **Status**: open | scheduled | closed
```

### 2.5 Load Iteration Feedback (if re-bootstrapping)

If `has_iteration_feedback` (from Step 1.0):

Read `.allforai/product-concept/iteration-feedback.json`. This contains:
- Previous concept-acceptance score and verdict
- Gaps found in the last iteration
- Recommended actions (fix_gap, simplify_flow, reconsider_concept, deprioritize)
- User decisions from re-bootstrap

LLM uses this in Step 3 to:
- Prioritize nodes that address previous gaps
- Avoid repeating the same planning mistakes
- If user made decisions (e.g., "move social sharing to post-launch"), respect them

If `user_decisions` is empty but `recommended_actions` exists, LLM infers decisions
by comparing the current `product-concept.json` against the previous iteration's gaps:
- Feature removed from concept → user decided to deprioritize
- Feature moved to post_launch → user decided to defer
- Feature still in must_have → user wants it fixed
Record inferred decisions in `iteration-feedback.json` → `user_decisions[]` for audit.

If `has_product_concept` (from Step 1.0):

Read `.allforai/product-concept/product-concept.json`. This is needed for Step 3.5 Coverage Self-Check.

### 2.6 Load Decision Journal (if exists)

Check if `.allforai/product-concept/decision-journal.json` exists. If yes, read it.

This file contains product decisions made during previous development sessions,
recorded via the `/journal` command. Each batch has a timestamp, topic, and
list of decisions with question/chosen/rationale.

LLM uses this in Step 3 to:
- **Respect previous decisions**: if user decided "login: email + Apple + Google, no WeChat",
  do not plan a WeChat login node
- **Detect conflicts**: if a decision contradicts the product-map, flag it (the decision
  is newer and likely correct — suggest updating the product-map)
- **Avoid re-asking**: if a question was already answered in the journal, don't ask again
  in Step 1.5

The journal is append-only. Later batches can supersede earlier ones (check `supersedes` field).
When decisions conflict, the latest batch wins.

### 2.7 Knowledge Gap Research (if project scope exceeds loaded knowledge)

After loading all knowledge, LLM self-checks: does the loaded domain knowledge
cover ALL major subsystems in this project?

**Trigger:** One of the following:
1. The project description or product vision mentions subsystems, business models, or technical
   patterns NOT covered by the loaded domain file or capabilities.
2. The user's **target technology stack** (for translate/rebuild goals) includes a runtime,
   framework, or platform that differs significantly from the source stack AND LLM's general
   knowledge of the target stack's ecosystem gaps is < 70% confident. Translation gaps are a
   first-class research trigger — migrating between ecosystems (e.g., Deno→Bun, CRA→Vite,
   REST→tRPC, Redis Sessions→JWTs, Django ORM→SQLAlchemy async) often has non-obvious pitfalls.
3. The project uses a **niche or specialized platform** where LLM framework knowledge is < 70%
   confident, even for non-translate goals (analyze, create, quality-checks). In these cases,
   Step 2.7 research is needed to generate correct node-spec guidance, not just translation pitfalls.
   Examples: HarmonyOS/ArkTS (Ability lifecycle, ohosTest framework), Roblox Luau (Roblox API,
   DataStore, RemoteEvent architecture), GBStudio (Game Boy ROM constraints), Defold (message-passing
   architecture, collection proxies), Solar2D (transition library, composer scenes).

**Examples of gaps that trigger research:**
- Ecommerce project mentions "self-operated logistics" but domain file only covers
  third-party logistics → WebSearch: "WMS warehouse management system design patterns"
- Social app mentions "live streaming" but no domain file covers it →
  WebSearch: "live streaming architecture CDN RTMP WebRTC"
- Fintech project mentions "KYC/AML compliance" but no domain file covers it →
  WebSearch: "KYC AML compliance system design"
- Translate goal: source is Deno + Hono, target is Bun + Elysia →
  WebSearch: "Bun Elysia framework patterns 2024" + "Deno to Bun migration pitfalls"
- Translate goal: source is React Class components, target is Next.js 15 App Router →
  WebSearch: "Next.js 15 App Router migration class components server components"

**Action:** For each identified gap, run 1-2 WebSearch queries to understand:
- What are the core components of this subsystem?
- What are the key state machines / business flows?
- What are the common pitfalls?
- (For translation gaps) What idiomatic patterns does the target stack use that differ from source?

**Budget limits:** Max 5 gaps per research session; max 2 queries per gap; skip WebSearch if LLM general knowledge covers > 70% of the subsystem (use in-context knowledge directly).

Incorporate findings into Step 3 planning. Do NOT write findings to files — they are ephemeral context for the current bootstrap session only. **In-session dependency:** if bootstrap is interrupted between Step 2.7 and Step 3, re-run from Step 2.7 to regenerate the research context before generating ad-hoc node-specs.

**Skip when:** Domain knowledge covers the project well, or the project is simple
enough that LLM's general knowledge is sufficient.

> **After Step 2, do NOT ask the user anything.** Proceed to planning.

---

## Step 3: Plan Workflow (LLM Free Planning)

> Goal: Design a project-specific workflow. NOT selecting from templates.
> LLM has absorbed all knowledge in Step 2. Now freely plan what nodes
> this specific project needs.

### 3.0 Incremental Re-Planning (when concept-drift exists)

> This section only applies when `has_concept_drift` is true AND an existing
> `workflow.json` exists. Otherwise, skip to 3.1 for full planning.

**Goal Change Detection (runs BEFORE incremental re-planning):**
Before running §3.0, compare the user's current goal (from Step 1.5) against the `goals` field in the existing `workflow.json`:
- If goals are DIFFERENT (e.g., was `["analyze"]`, now `["create"]`): do NOT use incremental re-planning. Instead, clear `workflow.json.nodes[]` entirely and run full §3.1 planning. Preserve `transition_log[]` for audit. All existing node-specs are stale and must be regenerated.
- If goals are THE SAME but concept drifted: use §3.0 incremental re-planning (below).
- If `workflow.json` has no `goals` field (schema mismatch from older bootstrap): treat as "goals differ" → full re-planning.

When concept has drifted since last bootstrap:

1. Read `.allforai/product-concept/concept-drift.json` → changes[]
2. Read existing `.allforai/bootstrap/workflow.json` → nodes[] + transition_log[]
3. For each change, determine affected nodes:

| Change Type | Node Action |
|-------------|-------------|
| feature_removed | Remove nodes whose goal is primarily about this feature. Add a `cleanup-{feature}` node if code already exists (detected from transition_log). |
| feature_added | Add new implementation + verification nodes for the feature. |
| feature_modified | Update affected nodes' goal and regenerate their node-specs. |
| role_removed | Remove role-specific nodes (e.g., e2e-test for that role's app). Update shared nodes to exclude this role. |
| tech_changed | Replace implementation + compile-verify + e2e nodes for the affected module with new tech stack equivalents. |
| client_removed | Remove the implementation + compile-verify + e2e triplet for that client. If the role becomes single-client, Level 3 parity check no longer applies. |
| client_added | Add implementation + compile-verify + e2e triplet for the new client. Trigger Level 3 parity check. |
| module_merged | Remove nodes for merged services. Extend the target service node's goal to absorb merged functionality. |
| module_split | Create new service nodes for the split-out module. Reduce the source service node's goal. |

4. **Preserve unaffected nodes**: nodes whose goal does not relate to any drift change
   remain in workflow.json with their transition_log entries intact. Completed work is not lost.
   **Cross-change dependencies**: a tech_changed may also affect infrastructure nodes
   (e.g., Flutter→SwiftUI means FCM push is no longer needed, only APNs). LLM must
   trace second-order effects of each change on ALL nodes, not just the obvious ones.

5. **Handle affected completed nodes**:
   - Node removed → transition_log entry stays for audit, but node removed from nodes[]
   - Node goal modified → clear its transition_log entry (needs re-execution)
   - New node added → no transition_log entry yet

6. Write updated workflow.json with modified nodes[] and preserved transition_log[].
7. Regenerate node-specs for all affected nodes at `.allforai/bootstrap/node-specs/`.
8. Proceed to Step 3.5 (Coverage Self-Check) — concept has changed, coverage must be re-verified.
9. Do NOT mark drift as resolved here. The orchestrator (/run) marks drift resolved AFTER all nodes complete successfully. This prevents the case where bootstrap marks drift resolved but /run fails partway — next /bootstrap would then wrongly see drift as already resolved and skip re-planning.

**When `concept_drift_source == "game-design-gate"`:**

1. Read `.allforai/game-design/approval-records.json` → collect all records with non-empty `revision_notes`
2. For each revised node, identify which downstream nodes consume its output (from `consumers[]` in workflow.json)
3. Mark those downstream nodes as `"status": "needs-rerun"` in workflow.json — they must re-execute with the updated design input
4. Nodes whose `hard_blocked_by` does not include any revised node → preserve as-is (no re-execution needed)
5. Write revision summary to `.allforai/product-concept/concept-drift.json` if it doesn't exist yet:
   ```json
   {
     "source": "game-design-gate",
     "changes": [
       { "node": "<revised node id>", "revision_notes": "<notes from approval-records>", "detected_at": "<ISO>" }
     ],
     "resolved": false
   }
   ```
6. Do NOT mark drift as resolved here. The orchestrator (/run) marks it resolved after all re-run nodes complete successfully.

**After incremental re-planning, skip 3.1-3.3** (they are for full planning) and go directly
to Step 3.4 (Confirm with User) → Step 3.5 (Coverage Self-Check) → Step 4.

### 3.1 Design the Node Graph

Based on project analysis (Step 1) + absorbed knowledge (Step 2), design
a set of nodes that will achieve the user's goal. Consider:

- What needs to happen? (understand code, design product, write code, verify, populate data...)
- What order makes sense for THIS project?
- What can run in parallel?
- What can be skipped or merged?

**There is no fixed template.** A game project might have nodes for
"design-economy-system" and "balance-test-combat". An SDK project might
have "design-api-surface" and "write-getting-started-guide". A consumer
app might have "design-onboarding-flow" and "setup-push-notifications".

**Game project node injection (when `is_game_project = true`):**

**Skip injection entirely when goals are:** `tune`, `product-verify`, `quality-checks`,
`demo`, `launch-prep`, or `visual-verify`. These goals assume game design documents
already exist; injecting design nodes would be wasteful. If `approval-records.json`
already has all-approved records, also skip (partial pipeline: see game-design.md §Composition Hints).

**Inject when goals include:** `create`, `translate`, or `rebuild` (new or re-designed game).
For `analyze` goal, inject only if no `approval-records.json` exists (new project without prior design pass).

1. Read `${CLAUDE_PLUGIN_ROOT}/knowledge/game-scenario-templates/${game_scenario}.json`
2. Read `${CLAUDE_PLUGIN_ROOT}/knowledge/capabilities/game-design.md` §Canonical Node Registry
3. Insert game-design nodes into the workflow AFTER `product-concept` node and BEFORE `product-analysis` node
4. For each node in `required_nodes` + `always_include` (and selected `optional_nodes`):
   - Check if `node_id` exists in game-design.md Canonical Node Registry:
     - **Canonical node** (in registry AND node_order): look up `discipline_owner`, `html_output`, `json_output`, `presentation` from the registry. Set `hard_blocked_by` = **previous SELECTED node in `node_order`** (skip unselected optional nodes); `unlocks` = **next SELECTED node in `node_order`** (same skipping rule). Exception: `game-design-finalize` has `hard_blocked_by` = ALL other game-design nodes that are actually selected.

     **Parallelism rule:** After assigning the default serial `hard_blocked_by`, apply this override for sibling nodes that only READ a shared predecessor's output (not data-produce it): if two or more nodes both `hard_blocked_by` the same single predecessor and neither is in the other's consumers[], reclassify the later node's dependency on its sibling as `alignment_refs` instead of `hard_blocked_by`. Common parallel groups by scenario:
       - `casual-mobile`: once `core-loop-design` is approved → `economy-design`, `progression-design`, `retention-design` may all run concurrently (each `hard_blocked_by: ["core-loop-design"]`; each lists the other two as `alignment_refs` for graceful degradation reads)
       - `action-rpg`: once `core-loop-design` approved → `combat-system-design`, `character-design`, `progression-design` may run concurrently
       - `narrative-adventure`: once `core-loop-design` approved → `narrative-design`, `character-design`, `world-design` may run concurrently
       - Always serial (never parallelise): `art-direction → art-concept → art-spec-design` (each writes data the next needs)
       - Always serial: `game-design-finalize` (reads ALL — stays `hard_blocked_by` all selected nodes)
     - **Ad-hoc optional node** (in `optional_nodes` but absent from node_order or canonical registry): use Step 2.7 research to generate node-spec content; position it immediately before `game-design-finalize` in the generated workflow sequence; `hard_blocked_by` = last SELECTED canonical optional node in node_order sequence order (if no canonical optionals selected, `hard_blocked_by` = last required node in node_order); `unlocks` = game-design-finalize.
   - All nodes get: `capability: game-design`, `human_gate: true`, `approval_record_path: ".allforai/game-design/approval-records.json"`, `gate_status: "pending"`, `review_checklist: [<3–5 items from game-design.md checklist table for this node type; use discipline-appropriate generic items if node not in table>]`

**Art Concept Node Injection (always applies when `art-direction` is in the selected workflow):**

After inserting the `art-direction` node, also insert an `art-concept` node immediately following it:
- `node_id: "art-concept"`, `capability: "art-concept-skill"`, `human_gate: false`
- `hard_blocked_by: ["art-direction"]`; update `art-spec-design` to `hard_blocked_by: ["art-concept"]` (remove `art-direction` from its hard_blocked_by list)
- `unlocks: ["art-spec-design"]`
- **No approval-records entry** (art-concept is a skill invocation, not a human-reviewed document)
- **Node-spec content** for art-concept (write verbatim to `.allforai/bootstrap/node-specs/art-concept.md`):

```markdown
---
node: art-concept
human_gate: false
hard_blocked_by: [art-direction]
unlocks: [art-spec-design]
exit_artifacts:
  - .allforai/game-design/art-pipeline-config.json
---

# Task: 美术技术规格确认（Art Concept Skill Invocation）

## 执行方法

读取并执行 `${CLAUDE_PLUGIN_ROOT}/skills/art-concept.md` skill，完成交互式 Q&A 并产出 `art-pipeline-config.json`。

art-concept skill 完成后，依次调用以下 game-art 子 skill 细化策略（读取对应 SKILL.md 并执行）：

1. **资产来源策略：** `${CLAUDE_PLUGIN_ROOT}/skills/game-art/10-design/asset-source-strategy-spec/SKILL.md`
   - 输入：参见 SKILL.md 的 Invocation Contract
   - 输出：每类资产的来源策略（生成/外包/改造/混合）

2. **动画生产计划：** `${CLAUDE_PLUGIN_ROOT}/skills/game-art/10-design/2d-animation-production-plan/SKILL.md`
   - 输入：参见 SKILL.md 的 Invocation Contract
   - 输出：动画方案选择（帧动画/DragonBones/Tween/混合）及降级路径

3. **动效设计**（当游戏有动效需求时，即 art-pipeline-config.json 中存在动画资产时）：`${CLAUDE_PLUGIN_ROOT}/skills/game-art/10-design/motion-design/SKILL.md`
   - 输入：`art-pipeline-config.json`、`art-style-guide.json.art_overview`
   - 输出：关键帧意图、Timing 规则、可读性规范

## 完成条件

`.allforai/game-design/art-pipeline-config.json` 存在且 `status == "final"`。
```

**Concept Freeze Node Injection (applies when art-spec-design is in the selected workflow):**

After inserting `art-spec-design`, also insert a `concept-freeze` node immediately following it:
- `node_id: "concept-freeze"`, `capability: "concept-contract"`, `human_gate: false`
- `hard_blocked_by: ["art-spec-design"]`; update all art-gen nodes (`ai-art-generation`, `tile-art-gen`, `character-art-gen`, `environment-art-gen`, `vfx-art-gen`, etc.) to `hard_blocked_by: ["concept-freeze"]` (remove `art-spec-design` from their hard_blocked_by)
- `unlocks`: all art-gen nodes
- **No approval-records entry** (concept-freeze has `human_gate: false` — no discipline_owner review needed)
- **Node-spec content** for concept-freeze (write verbatim to `.allforai/bootstrap/node-specs/concept-freeze.md`):

```markdown
---
node: concept-freeze
human_gate: false
hard_blocked_by: [art-spec-design]
unlocks: []  # populated by bootstrap from workflow's art-gen nodes
exit_artifacts:
  - .allforai/concept-contract.json
  - .allforai/game-design/asset-registry.json
---

# Task: 概念合约冻结（Concept Freeze）

## 执行方法

读取并执行 `${CLAUDE_PLUGIN_ROOT}/knowledge/capabilities/concept-contract.md` capability，完成 canonical_registry 构建并写入 `concept-contract.json`。

concept-contract capability 完成后，依次调用以下 game-art 子 skill（读取对应 SKILL.md 并执行）：

1. **工具能力检测：** `${CLAUDE_PLUGIN_ROOT}/skills/game-art/00-env/production-tool-capability-registry/SKILL.md`
   - （输入/输出：参见 SKILL.md 的 Invocation Contract）
   - 将检测结果写回 `art-pipeline-config.json.toolchain.detected_capabilities`

2. **资产注册表初始化：** `${CLAUDE_PLUGIN_ROOT}/skills/game-art/00-env/asset-registry/SKILL.md`
   - （输入/输出：参见 SKILL.md 的 Invocation Contract）
   - 输出：`.allforai/game-design/asset-registry.json`（以 canonical_registry 为权威，资产 ID → 文件前缀 → 生命周期状态的单一可信注册表）

## 完成条件

`.allforai/concept-contract.json` 存在且 `schema_version == "1.0"` 且 `.allforai/game-design/asset-registry.json` 存在。

## 重要说明

所有后续 art-gen 节点必须从 `concept-contract.json` 读取 `canonical_registry`，使用其中的 `file_prefix` 作为生成文件的命名权威来源，不得自行命名。
```

**Art-Gen Node Injection (when `art-spec-design` and `concept-freeze` are in the selected workflow):**

After injecting `concept-freeze`, read `art-pipeline-config.json.active_nodes` and inject one node-spec per entry. Use the sub-skill mapping table below to determine which `game-art` sub-skills each node-spec should delegate to.

**Sub-Skill Mapping Table:**

| `node_id` | Pre-Spec Sub-Skills (read first) | Generate Sub-Skills (run after) | Condition |
|-----------|----------------------------------|--------------------------------|-----------|
| `tile-art-gen` | `skills/game-art/20-spec/tileset-spec/SKILL.md` | `skills/game-art/30-generate/tileset-generation/SKILL.md` | always |
| `tile-art-gen` | + `skills/game-art/20-spec/2-5d-production-mode-spec/SKILL.md` + `skills/game-art/20-spec/2-5d-lighting-shadow-spec/SKILL.md` | + `skills/game-art/30-generate/render-to-2d-asset-generation/SKILL.md` | when `dimension=2.5d` |
| `character-art-gen` | `skills/game-art/20-spec/character-layer-sheet/SKILL.md` + `skills/game-art/20-spec/visual-style-tokens/SKILL.md` | `skills/game-art/30-generate/skeletal-animation/SKILL.md` | when `character.rig` = `dragonbones`, `dragonbones_mesh`, or `skeletal_3d` |
| `character-art-gen` | same pre-spec | `skills/game-art/30-generate/frame-animation-generation/SKILL.md` | when `character.rig=frame_sequence` |
| `character-art-gen` | — | + `skills/game-art/30-generate/expression-set-generation/SKILL.md` | when `character.expressions=true` (append after primary generate) |
| `environment-art-gen` | `skills/game-art/20-spec/2d-view-mode-spec/SKILL.md` | `skills/game-art/30-generate/background-generation/SKILL.md` + `skills/game-art/30-generate/prop-generation/SKILL.md` | always |
| `environment-art-gen` | + `skills/game-art/20-spec/3d-source-asset-spec/SKILL.md` | + `skills/game-art/30-generate/render-to-2d-asset-generation/SKILL.md` | when `dimension=3d` or `2.5d` |
| `ui-art-gen` | `skills/game-art/20-spec/visual-style-tokens/SKILL.md` | `skills/game-art/30-generate/icon-generation/SKILL.md` | always |
| `ui-art-gen` | — | + `skills/game-art/30-generate/portrait-generation/SKILL.md` | when `concept_art.needed=true` |
| `vfx-art-gen` | `skills/game-art/20-spec/vfx-spec/SKILL.md` | `skills/game-art/30-generate/vfx-generation/SKILL.md` | always |

**Node-spec template for each `active_node` entry:**

Write `.allforai/bootstrap/node-specs/<node-id>.md` using this template, substituting `<TYPE>`, `<REGISTRY_KEY>`, `<CONFIG_SECTION>`, and `<DISCIPLINE_OWNER>` from the table below:

| `node_id` | `<TYPE>` | `<REGISTRY_KEY>` | `<CONFIG_SECTION>` | `<DISCIPLINE_OWNER>` |
|-----------|----------|-----------------|-------------------|---------------------|
| `tile-art-gen` | tile | `tiles` | `tileset` | `concept-artist` |
| `character-art-gen` | character | `characters` | `character` | `character-modeler` |
| `environment-art-gen` | environment | `environments` | `environment` | `environment-artist` |
| `ui-art-gen` | UI | `ui` + `other` | _(all remaining)_ | `ui-artist` |
| `vfx-art-gen` | VFX | `vfx` | `vfx` | `vfx-artist` |

```markdown
---
node: <node-id>
human_gate: true
hard_blocked_by: [concept-freeze]
unlocks: [art-qa]
exit_artifacts:
  - path: .allforai/game-design/<node-id>-review.html
  - path: .allforai/game-design/systems/<node-id>-spec.json
---

# Goal

Generate <TYPE> art assets for all entries in `.allforai/concept-contract.json` `canonical_registry.<REGISTRY_KEY>[]`.

## Inputs

- `.allforai/concept-contract.json` — `canonical_registry.<REGISTRY_KEY>[]` (authoritative asset IDs and `file_prefix` values; do not invent your own names)
- `.allforai/game-design/art-pipeline-config.json` — `<CONFIG_SECTION>` configuration and `toolchain.detected_capabilities`
- `.allforai/game-design/art-asset-inventory.json` — current asset states (skip assets with `current_state == "locked"`)
- `.allforai/game-design/asset-registry.json` — canonical registry built by concept-freeze

## Sub-Skill Invocation

Read and follow each sub-skill SKILL.md in order. Each sub-skill defines its own output contract — follow it exactly.

### Step 1 — Pre-Spec

<List the pre-spec sub-skill paths from the mapping table above for this node_id, with conditions>

### Step 2 — Generate

<List the generate sub-skill paths from the mapping table above for this node_id, with conditions>

## Completion Condition

`.allforai/game-design/systems/<node-id>-spec.json` exists AND `.allforai/game-design/<node-id>-review.html` exists AND all `canonical_registry.<REGISTRY_KEY>[]` entries have `current_state != "placeholder"`.

If any sub-skill returns `UPSTREAM_DEFECT` → halt and report the defect. Do not advance to `art-qa`.
```

**Key rules for art-gen injection:**
- `hard_blocked_by: ["concept-freeze"]` for ALL art-gen nodes (regardless of type)
- `unlocks: ["art-qa"]` for ALL art-gen nodes
- `human_gate: true` for ALL art-gen nodes (discipline-specific approval required)
- `approval_record_path: ".allforai/game-design/approval-records.json"` for ALL art-gen nodes
- `review_checklist`: use the checklist from `game-design.md` canonical registry table
- Do NOT inject a node-spec for entries in `skipped_nodes` — only `active_nodes` get node-specs

**App Design Node Injection (when `is_game_project = false` AND goal includes design phase):**

**Inject when `goals` includes `create` or `rebuild`** (new or re-designed app). For all other goals — `translate`, `analyze`, `tune`, `product-verify`, `quality-checks`, `demo`, `launch-prep`, `visual-verify` — **skip injection entirely** (app-design phases are already complete).

Inject app-design nodes using `knowledge/capabilities/app-design.md` Canonical Node Registry:

- Required nodes always injected: `ia-design`, `user-flow-design`, `interaction-design`, `app-design-finalize`
- Optional nodes injected when relevant: `content-design` (content-heavy apps), `data-model-design` (data-intensive apps — inject when user confirms data-intensive app (e.g., database schema, complex data model mentioned in discussion))
- Each node gets: `capability: "app-design"`, `human_gate: true`, `approval_record_path: ".allforai/app-design/approval-records.json"`, `gate_status: "pending"`, `discipline_owner` from app-design.md Canonical Node Registry, `review_checklist: [<3 role-appropriate quality checks>]` — generate 3 discipline-appropriate checklist items per node (e.g., for ia-design: "All primary user flows represented", "Screen hierarchy reflects priority", "Navigation patterns consistent")
- Ordering: `ia-design` first (no hard_blocked_by); `user-flow-design` and `content-design` and `data-model-design` each `hard_blocked_by: ["ia-design"]`; `interaction-design` `hard_blocked_by: ["user-flow-design"]`; `app-design-finalize` `hard_blocked_by:` ALL other selected app-design nodes
- `app-design-finalize` `unlocks:` subsequent execution nodes (same role as `game-design-finalize`)
- **No approval-records entry** for nodes with `human_gate: false` — only human_gate nodes get records
- After injecting, initialise `.allforai/app-design/approval-records.json` with one `pending` record per selected app-design node (same structure as game-design approval-records.json)

**Concept Freeze for app projects:** When `app-design-finalize` is in the workflow, also inject a `concept-freeze` node immediately after it:
- `node_id: "concept-freeze"`, `capability: "concept-contract"`, `human_gate: false`
- `hard_blocked_by: ["app-design-finalize"]`
- `exit_artifacts: [".allforai/concept-contract.json"]`
- After injecting, update all app execution nodes (any node that previously had `hard_blocked_by: ["app-design-finalize"]`) to instead `hard_blocked_by: ["concept-freeze"]`
- Node-spec file: Write `.allforai/bootstrap/node-specs/concept-freeze.md` using `knowledge/capabilities/concept-contract.md` Branch B (app project). In the node-spec, instruct the subagent to read from `.allforai/app-design/app-design-doc.json` and `.allforai/app-design/approval-records.json`.
- **No approval-records entry**

5. Initialise `.allforai/game-design/approval-records.json` with one `pending` record per game-design node
6. Ad-hoc nodes appearing in EITHER `optional_nodes` OR `bootstrap_note` (but absent from both the canonical registry AND `node_order`): these require user opt-in, presented in the opt-in question after scenario selection. Process them ONCE — if a node appears in both `optional_nodes` and `bootstrap_note`, treat it as a single ad-hoc opt-in candidate (do not generate two node-specs). If the user selects it, generate node-spec via Step 2.7 research and position per step 4 ad-hoc rule.
7. **Cross-scenario signal scan (hybrid games):** After loading the primary scenario template, scan Step 1.1–1.3 findings for multiplayer/network signals:
   - **Unity signals:** dependencies like `Mirror`, `Unity Netcode`, `Photon`, `Nakama`, `Colyseum`, `relay`, `WebSocket`, network socket code, or multiplayer room logic
   - **Unreal Engine 5 signals:** `.uproject` `Plugins` array containing `OnlineSubsystem`, `OnlineSubsystemSteam`, `OnlineSubsystemEOS`; C++ source containing `DOREPLIFETIME`, `NetMulticast`, `Server` UFUNCTION specifiers; `.Build.cs` files referencing `OnlineSubsystemUtils`
   - **General signals:** `WebSocket`/`gRPC`/`socket.io` in any package file; source files importing `net`/`socket` modules with multiplayer room or lobby patterns
   If any signal found AND `network-architecture-design` + `matchmaking-design` are NOT already in the primary scenario's `required_nodes`, present them as supplementary optional nodes in the opt-in question with note: "检测到联网/多人代码，建议补充选择以下节点".

**BaaS / Serverless verification in node graph:**
When `architecture_pattern` starts with `baas-` or `serverless-`:
- There is NO persistent backend server process. demo-forge populates data via the BaaS SDK or serverless local emulator, NOT via `curl localhost`.
- The runtime-env setup node MUST start the local emulator (Firebase Emulator, Supabase local, `serverless-offline`, `sam local start-api`) as a prerequisite for demo-forge and E2E verification nodes. Order: `setup-env → start-emulator → demo-forge → e2e-verify`.
- For BaaS: if no local emulator is available (e.g., Amplify some services), document in node-spec as "BaaS integration tests require staging environment — use staging credentials for this node."
- For Serverless: demo-forge invokes functions via local emulator CLI, not HTTP server; verification node runs function-level tests (not Playwright against a running server).

**Node granularity is project-dependent.** A simple CLI tool might need
3 nodes. A microservice platform might need 20. LLM decides.

**Cross-Module Consistency Check (MANDATORY for rebuild/translate goals):**
When goals include rebuild or translate, LLM MUST check EVERY module in
`bootstrap-profile.json.modules[]` against the product definition (product-map
artifacts, README, or product vision). For each module, answer:

1. Does this module's code reflect the current product direction?
2. Does it implement the entities/flows defined in the product-map?
3. Is it consistent with other modules that have already been rebuilt?

If a module is **stale or inconsistent** (e.g., API has new features but
mobile still has old UI), it MUST get an **implementation node** before any
verification node. Verification without implementation is useless — it only
proves that outdated code runs, not that the product works.

**Concept-before-Analysis Rule (for analyze goal):**
When goals include "analyze" (reverse analysis), the workflow MUST include a
reverse-concept node BEFORE product-analysis nodes. The dependency chain is:
```
discover → reverse-concept → product-analysis → generate-artifacts
```
Without reverse-concept, product-analysis has no independent baseline — it becomes
circular (extracting "what code does" without knowing "what code should do").
reverse-concept produces concept-baseline.json (see cross-phase-protocols.md §A.1)
which product-analysis and all downstream phases auto-load for consistency checking.

See `capabilities/reverse-concept.md` for methodology and output schemas.

**Implementation-before-Verification Rule:**
For each module, nodes must follow this order:
```
implement (if needed) → demo/seed (if applicable) → verify
```
A verification node for a module without a corresponding implementation node
is only valid if the module's code is already up-to-date with the product
definition. If the code is stale, plan the implementation node first.

Checklist (LLM must iterate before finalizing workflow):
```
For each module in bootstrap-profile.json.modules[]:
  □ Is code consistent with product-map? → YES: verify only / NO: implement first
  □ Has implementation node (if needed)?
  □ Has verification node?
  □ Verification depends on implementation?
```

**Functional Pipeline Completeness Check (MANDATORY):**
After module-level checks, LLM MUST also check that cross-module functional
pipelines are complete end-to-end. A "pipeline" is a product flow that spans
multiple components (trigger → generation → storage → delivery → display).

Check method: Read `product-map/role-profiles.json` trigger_conditions[] and
`product-map/business-flows.json` flows[]. For each trigger/flow, trace the
full pipeline:

```
For each trigger_condition or async business flow:
  □ Trigger source exists? (cron job / event handler / user action)
  □ Generation logic exists? (service that creates the data)
  □ Storage exists? (DB table / queue)
  □ Delivery mechanism exists? (API endpoint / push notification / WebSocket)
  □ Client display exists? (UI that shows the result)
```

If any step in a pipeline is missing, the workflow MUST include a node to
implement it. Common gaps that LLM must watch for:

| Product Requirement | Often Missing | What to Check |
|-------------------|---------------|---------------|
| "Send X when Y happens" | Background scheduler/cron | Is there a goroutine/cron/worker that checks Y? |
| "Push notification" | APNs/FCM integration | Is there push infra in the codebase? |
| "Proactive messages" | Generation job | Endpoint exists to READ, but does anything WRITE? |
| "Daily/weekly summary" | Aggregation job | Is there a scheduled job that aggregates data? |
| "Real-time updates" | WebSocket/SSE | Is there a push channel, or only polling? |

Example: product-map says "SRS item due → send review card". Pipeline:
1. Trigger: cron job checks SRS due dates ← **missing if no scheduler**
2. Generate: create ProactiveMessage record ← **missing if only read endpoint**
3. Store: proactive_messages table ← exists
4. Deliver: GET /messages/pending ← exists (but only pull, no push)
5. Display: Front Desk UI ← exists
→ Workflow needs: "implement-background-scheduler" + "implement-push-notifications"

**State Machine Completeness Check (MANDATORY):**
> **Scope**: This check applies to EXISTING CODE — verifying that code already in the
> codebase correctly implements state machines (state storage, transitions, behavior
> mappings). It runs during rebuild/translate goals when code exists. For NEW projects
> (goal=create), this check is N/A — Step 3.5 Level 4 handles coverage planning instead.

This check covers TWO categories of state machines:

**Category 1: Business State Machines (deterministic)**
Systems with well-defined states and transition rules driven by system events.
Examples:
- Message delivery: sent → delivered → read
- Order lifecycle: created → paid → shipped → delivered → completed
- User status: online → idle → offline (with last_seen timestamp)
- Group membership: invited → member → admin → owner
- Content moderation: pending → approved / rejected

**Category 2: Adaptive State Machines (probabilistic)**
Systems where state evolves based on user behavior and influences system behavior.
Examples:
- Learning proficiency: beginner → intermediate → advanced
- Recommendation preferences: tracks interaction patterns → personalizes content
- Engagement scoring: activity frequency → notification cadence

After pipeline checks, LLM MUST check for **state machines** (both categories) defined
in the product-map. Products with personalization, learning, or recommendation
features have user states that evolve over time. The system must read the
current state to decide behavior, and update the state after each interaction.

This is NOT a linear pipeline check. It's a state machine check:

```
                    ┌─── event ───┐
                    ▼              │
    ┌──────────────────────┐      │
    │   User State         │      │
    │  ┌─ dimension_1: val │      │
    │  ├─ dimension_2: val │──────┘
    │  └─ dimension_3: val │  state determines
    └──────────────────────┘  system behavior
              │                     │
              ▼                     ▼
    ┌──────────────┐     ┌──────────────────┐
    │ Transition   │     │ Behavior Mapping │
    │ event + rule │     │ state → action   │
    │ → new state  │     │ (what AI does)   │
    └──────────────┘     └──────────────────┘
```

Check method: Read `product-map/task-inventory.json` tasks[]. For each task
that describes adaptive behavior (keywords: "based on", "adjust", "personalize",
"reinforce", "inject", "adapt", "track", "proficiency-based", "level"),
verify three things:

**1. State Definition — is the user state model complete?**
```
For each adaptive dimension in the product:
  □ Is there a DB table/field that holds this state?
  □ Does it store CURRENT value (for behavior decisions)?
  □ Does it store HISTORY (for trend/progress reporting)?
  □ Is the initial state defined (what value for new users)?
```

**2. State Transitions — do events update the state?**
```
For each user event that should change state:
  □ Is there code that runs AFTER the event to update state?
     (e.g., after conversation ends → update grammar_profiles, proficiency, streak)
  □ Is the transition rule correct? (not just increment — weighted, decayed, etc.)
  □ Does the transition handle edge cases? (first time, reset, regression)
```

**3. State→Behavior Mapping — does the system ACT on the state?**
```
For each adaptive behavior the product promises:
  □ Does the code READ the user state before deciding what to do?
     (e.g., conversation_service reads grammar_profiles before building prompt)
  □ Does the behavior CHANGE based on state values?
     (e.g., hint_mode=full vs keywords vs none produces different UI)
  □ Is the mapping granular enough? (not just on/off but graduated response)
```

If any of the three is incomplete, the "adaptive" feature is actually static.
The workflow MUST include implementation nodes to complete the state machine.

Common state machine gaps:

| Product Promise | State Definition | Transitions | Behavior Mapping |
|----------------|-----------------|-------------|------------------|
| "Adapt to user level" | proficiency table ✓ | **Missing**: no auto-update after conversation | hint UI exists but always shows same mode |
| "Reinforce weaknesses" | grammar_profiles ✓ | errors collected ✓ | **Missing**: not injected into Persona prompt |
| "Personalized recommendations" | **Missing**: no preference tracking | N/A | content list is same for all users |
| "Progress over time" | current snapshot only | **Missing**: no historical snapshots | cannot show "you improved this week" |
| "Intimacy-driven outreach" | intimacy table ✓ | level updates ✓ | **Missing**: no proactive message generation based on level |

Example — FlyDict learning state machine:
```
User Learning State:
  proficiency_level: beginner|intermediate|advanced
  weakness_profile: {grammar_category: mastery_score, ...}
  hint_mode: full_with_translation|keywords_only|none
  persona_familiarity: {persona_id: intimacy_level, ...}
  scene_coverage: {tag: practiced_count, ...}

Events that trigger transitions:
  conversation_end → update weakness_profile, proficiency, scene_coverage
  review_card_answer → update SRS schedule, weakness mastery
  growth_test_pass → upgrade proficiency_level, adjust hint_mode

State→Behavior mappings:
  weakness_profile → injected into Persona system prompt (top 3 weaknesses)
  hint_mode → determines flash card display style
  proficiency_level → determines hint duration, quiz difficulty
  scene_coverage → Coco recommends uncovered Persona tags
  persona_familiarity → Persona correction directness, topic depth
```

For each mapping, check: does the code path exist from state read → behavior change?
If a state exists in DB but nothing reads it to change behavior → broken mapping.
If behavior is supposed to adapt but always reads a hardcoded default → broken mapping.

**Node Scope Self-Check (MANDATORY):**
After designing the node graph, LLM MUST review each implementation node and ask:
"Can a single subagent complete this node's goal in one execution with high quality?"

Signs that a node needs splitting:
- Node goal contains "and" connecting unrelated subsystems
  (e.g., "implement user auth AND messaging AND file storage")
- Node covers > 1 independent domain with no shared data model
- Estimated output exceeds what one subagent can reliably produce

If uncertain, split. Two focused nodes are better than one overloaded node.
Each split node gets its own node-spec, exit_artifacts, and verification.

**Large Project Decomposition (when total nodes > 30):**
After completing the node graph, count the total nodes. If > 30, the project
is likely too large for a single workflow execution. Suggest decomposition:

1. Identify independent business lines (e.g., B2C shopping + logistics + B2B)
2. Each business line becomes a separate /bootstrap → /run cycle
3. Shared infrastructure (auth, DB, messaging) goes in the first cycle
4. Present decomposition to user in Step 3.4 (Confirm with User):
   ```
   项目规模较大（{N} 个节点），建议分阶段执行：
     Phase 1: {core business line} ({M1} 个节点)
     Phase 2: {secondary line} ({M2} 个节点)
     Phase 3: {tertiary line} ({M3} 个节点)
   是否接受分阶段？还是一次性执行全部？
   ```
5. If user accepts: generate workflow.json for Phase 1 only, note Phase 2/3 as future
6. If user declines: proceed with full workflow (their choice, warn about execution time)

### 3.2 Write workflow.json

```json
{
  "schema_version": "2.0",
  "project": "<project name>",
  "goals": ["<user-selected goal codes, e.g. 'analyze', 'translate', 'quality-checks'>"],
  "planned_at": "<ISO timestamp>",
  "nodes": [
    {
      "id": "<project-specific name>",
      "capability": "<name of the capability this node is based on, e.g. discovery, product-analysis, translate>",
      "goal": "<one sentence: what this node achieves>",
      "exit_artifacts": [
        {
          "path": "<project-relative file path>",
          "validation_commands": []
        }
      ],
      "knowledge_refs": ["<which knowledge files this node should reference>"],
      "consumers": ["<node IDs that read this node's exit_artifacts>"],
      "hard_blocked_by": ["<node IDs that must complete before this node can start — strict execution gate>"],
      "alignment_refs": ["<node IDs this node reads from but can run concurrently — reads artifacts after they exist>"],
      "unlocks": ["<node IDs unblocked when this node completes>"],
      "human_gate": false,
      "discipline_owner": null
    }
  ],
  "transition_log": [],
  "diagnosis_history": [],
  "corrections_applied": []
}
```

**Node fields:**
- `id`: Project-specific. NOT from a fixed vocabulary.
- `capability`: Which capability this node is based on. Matches a file in
  `knowledge/capabilities/<capability>.md`. Used at Context Pull generation time
  to look up which upstream artifacts this node may consume.
- `goal`: One sentence. Clear enough that a subagent knows what to do.
- `exit_artifacts`: Array of artifact objects. Node is complete when all `path` files exist.
  Each entry has:
  - `path`: Project-relative file path. Node is complete when this file exists.
  - `validation_commands` (optional): Shell commands that must exit 0 after the file exists.
    Use for format checks beyond mere existence (e.g., `python3 -c "import json,sys; json.load(open('file.json'))"` for JSON validity,
    `grep -q '"status": "final"' file.json` for specific field checks).
    Empty array = existence check only. Bootstrap should populate these for JSON output files.
  
  **Shorthand:** Bootstrap may also use the string form `"<path>"` for artifacts with no
  validation_commands. check_artifacts.py accepts both forms.
- `knowledge_refs`: Which knowledge files to inject into the node-spec.
- `consumers`: Which downstream nodes read this node's output. Used to generate
  the Downstream Contract section in the node-spec — tells the subagent "who
  will consume your output and what they need from it".
  **How to populate**: For each node N, `consumers[]` = all node IDs M where N appears in M's `blocked_by[]` AND N's exit_artifacts are listed in the Downstream Consumers table of M's capability file. Bootstrap derives this during Step 3.1 node graph design — after blocked_by chains are established, traverse them in reverse to fill consumers.
- `hard_blocked_by`: Node IDs that must complete (exit_artifacts exist + human_gate approved if applicable) before this node can START. The orchestrator will not dispatch this node until all hard_blocked_by nodes are complete. Use for true data dependencies — this node's inputs don't exist until upstream finishes.
- `alignment_refs`: Node IDs this node reads artifacts FROM but does not strictly depend on for execution timing. The orchestrator may dispatch this node in parallel with alignment_refs nodes; the node-spec's Context Pull section must handle the case where alignment_refs artifacts may not yet exist (graceful degradation). Use for "I want to align with X's output but can work without it."

**Migration note:** The legacy `blocked_by` field is equivalent to `hard_blocked_by`. Both are accepted; `hard_blocked_by` is preferred for new bootstrap runs.
- `unlocks`: Node IDs unblocked when this node's gate is approved. Used by the orchestrator to advance the workflow after approval.
- `human_gate`: `true` for game-design nodes requiring discipline_owner approval; `false` for all others. Orchestrator reads this to decide whether to check `approval-records.json` in addition to `exit_artifacts`.
- `discipline_owner`: Role ID of the approver for human_gate nodes (e.g., `"lead-designer"`); `null` for non-gate nodes.

**No entry_requires.** The orchestrator's LLM decides execution order at runtime based on `blocked_by` and artifact existence.

**exit_artifacts 路径规范（重要）：**
- 必须是**精确的项目相对路径**，从项目根目录开始
- ❌ `.env`（模糊——哪个目录的 .env？）
- ✅ `flydict-api/.env`（精确——明确是 API 子目录）
- ❌ `config.json`（模糊）
- ✅ `.allforai/bootstrap/migration-result.json`（精确）
- 对于 monorepo，路径必须包含子项目前缀
- 路径必须是执行 `check_artifacts.py` 时从项目根目录能找到的
- 生成 workflow.json 前，LLM 应检查项目目录结构确认路径正确
- `validation_commands` 建议：对所有 JSON 输出文件，至少加入 JSON 合法性检查：
  `python3 -c "import json,sys; json.load(open('<path>'))"` 
  对有 `status` 字段的 JSON，追加：`grep -q '"status": "final"' <path>`

### 3.3 Pre-Generate Node-Specs

For each node in workflow.json, generate a complete node-spec markdown file
at `.allforai/bootstrap/node-specs/<id>.md`.

**Why pre-generate?** Saves execution-time attention. Bootstrap has the
fullest context (all knowledge loaded). Each subagent at /run time only
needs to read its own node-spec.

**Context Pull Generation (for each node-spec):**

For each node, generate a `Context Pull` section using this algorithm:

1. Find upstream nodes: scan workflow.json nodes[] for any node whose `consumers[]`
   includes the current node's id.
2. For each upstream node, read its `capability` field. Load
   `knowledge/capabilities/<capability>.md`.
3. In the Downstream Consumers table, keep rows where `Consumer Capability` contains
   the CURRENT node's capability name.
4. Filter by project relevance: skip rows where the producing capability is not
   included in this project's workflow (e.g., skip `reuse-assessment.json` rows
   if no node with capability=discovery produced it for this project).
5. Split remaining rows into two groups:
   - `required`: missing file → subagent must return error, naming the missing file
   - `optional`: missing file → subagent logs warning and continues with fallback
6. Write the Context Pull section as natural-language instructions (see template above).
   Use the `Reason` column to explain why each field matters for this node's work.

If a node has no upstream nodes (first in the graph), omit the Context Pull section entirely.

**Maximum Realism Principle (applies to ALL node-specs):**
When the user has provided real credentials (API keys, database connections, service URLs),
generated node-specs MUST instruct subagents to use the REAL service, not mocks/stubs.
Dev-mode code should check for real credentials and use them when available. Stubs are
ONLY acceptable when no credentials are provided. This ensures demo-forge and smoke-test
exercise the full real stack, not a fake one. Every stub is a gap in integration testing.

**Safety Constraint (applies to demo-forge node-specs):**
Read `${CLAUDE_PLUGIN_ROOT}/knowledge/safety.md §Demo Data Staging Constraint` when
generating demo-forge node-specs. The pre-flight credential check (staging vs production
detection) MUST be included in every generated demo-forge node-spec as the first step.

**Full E2E Testing Principle (applies to workflow planning):**
Every module in `bootstrap-profile.json.modules[]` MUST have a corresponding verification
node in the workflow. No module may be silently skipped. This is NOT optional.

**Coverage rule**: When planning nodes in Step 3.1, LLM MUST iterate over every module
in the bootstrap profile and ensure each has at least one verification node. If a module
has no verification node, the workflow is incomplete.

**Verification strategy per module role:**

| Module Role | Verification Tool | Node Pattern |
|-------------|------------------|--------------|
| backend (API) | curl / HTTP client | api-integration-test |
| frontend (web) | Playwright browser E2E | e2e-test-{name} |
| admin (web) | Playwright browser E2E | e2e-test-admin |
| mobile (Flutter) | `flutter test integration_test/` on simulator/emulator | e2e-test-{name} |
| mobile (React Native) | Detox or Maestro | e2e-test-{name} |
| mobile (iOS/SwiftUI) | XCUITest via `xcodebuild test` | e2e-test-{name} |
| mobile (Android/Kotlin) | Espresso via `./gradlew connectedAndroidTest` | e2e-test-{name} |
| desktop (Tauri v2) | `tauri-driver` (WebDriver binary) + WebdriverIO with `wdio-tauri-service` for UI E2E; `cargo test` for Rust IPC unit tests. ⚠️ Playwright does NOT work with Tauri v2 — use tauri-driver. Run Step 2.7 WebSearch for current tauri-driver setup if LLM confidence < 70% | e2e-test-{name} |
| desktop (Electron) | Playwright via `electron-playwright-helpers` (drives the Electron webview) | e2e-test-{name} |
| game client (Unity) | Unity Test Runner (EditMode + PlayMode) via `unity -runTests -testPlatform EditMode/PlayMode` | game-test-{name} |
| game client (Godot) | GUT (Godot Unit Testing) or `godot --test` | game-test-{name} |
| game client (Bevy/Rust) | `cargo test` with Bevy's headless test harness | game-test-{name} |
| game client (Phaser.js/web) | Jest or Playwright in headless browser (Phaser runs in jsdom or a real browser) | game-test-{name} |
| game client (pygame/Python) | pytest + `pygame.display.set_mode` in headless SDL (SDL_VIDEODRIVER=dummy) | game-test-{name} |
| game client (PICO-8) | Manual test only (no headless mode); document manual test scenarios | game-test-manual |
| game client (Roblox/Luau) | TestEZ framework (Roblox's built-in test runner); run via Roblox Studio Play mode or `run-in-roblox` CLI for headless server tests. Client-side tests require Studio GUI mode — document manual test scenarios for client flows | game-test-{name} |
| game client (GBStudio) | Manual ROM test in GB emulator (BGB or mGBA); automated testing not supported — document manual test checklist (start screen, progression, save/load, credits) | game-test-manual |
| game client (SpriteKit/SceneKit — iOS) | XCTest with headless iOS Simulator (`xcodebuild test -scheme {name} -destination 'platform=iOS Simulator,name=iPhone 15'`); game-specific flows via XCUITest; physics/rendering tests via in-process unit tests with `SKView(frame:)` | game-test-{name} |
| game client (Twine / interactive fiction — web export) | Playwright browser E2E on the exported HTML bundle (serve with `npx serve dist/` then run Playwright); test passage navigation, variable tracking, and ending states | e2e-test-{name} |
| game client (HaxeFlixel) | haxe + `FlxTest` for unit logic; full game requires headless Flash/OpenFL test runner (`lime test neko` or `lime test html5` with headless browser); document manual test scenarios for visual/audio flows | game-test-{name} |
| event-driven service (Discord bot / CLI / background worker) | jest/vitest + mock event provider (e.g., discord.js mock client, mock queue consumer); no HTTP routes to curl | e2e-test-{name} |
| GitHub Actions custom action | `act` (local Actions runner) for end-to-end workflow testing; jest/vitest for JS action unit tests; `@actions/core` mock for testing action I/O | action-test-{name} |
| mobile (HarmonyOS/ArkTS) | DevEco Studio ohosTest framework via `hdc` (Huawei Device Connector) on HarmonyOS emulator or real device; unit tests via `@ohos/hypium`. ⚠️ No Playwright/Detox/XCUITest support for HarmonyOS | e2e-test-{name} |
| IDE plugin (VS Code extension) | `@vscode/test-cli` or `@vscode/test-electron` via `npm run test`; Playwright unsupported inside VS Code host. For extensions contributing a Language Server (activationEvents includes `onLanguage:*` or `contributes.languages`), also add LSP integration tests via `vscode-languageserver-protocol` test harness. For Debug Adapter Protocol extensions, add DAP integration tests. | plugin-test-{name} |
| IDE plugin (Obsidian plugin) | `jest` with Obsidian vault fixture mock; full testing requires Obsidian CLI headless (if available) | plugin-test-{name} |
| browser extension | Playwright with `chrome.launch({ channel: 'chrome' })` + extension load via `args: ['--load-extension=./dist']` | e2e-test-{name} |
| backend API (tRPC) | jest/vitest with `@trpc/server` test client (no curl — tRPC has no REST routes). Create a tRPC caller via `createCallerFactory(router)(ctx)` and invoke procedures directly in tests. ⚠ Do NOT use curl or HTTP for tRPC backends — procedures are not HTTP-addressable by design. | api-test-{name} |
| backend API (GraphQL) | jest/vitest with `graphql-tag` + test server (`ApolloServer.executeOperation` or `graphql()` executor); for E2E, Playwright or `graphql-request` against a running dev server. Cross-module stitch must check GraphQL operations (queries, mutations, subscriptions) against schema — not just REST routes. | api-test-{name} |
| backend service (gRPC) | language-native test runner with gRPC test client (Go: `grpc.Dial("bufnet")` + `bufconn`; Node.js: `@grpc/grpc-js` test channel). ⚠ `.proto` files must be compiled before tests (add proto compile step to node-spec). No curl — gRPC uses binary Protobuf wire format. | api-test-{name} |
| library / SDK | Language native test runner only — `npm test` (Jest/Vitest), `cargo test`, `pytest`, `mvn test`, `go test ./...`. No E2E node needed (no running server). No Playwright/Detox. | lib-test-{name} |
| embedded / firmware | `pio test` (PlatformIO) for on-device/simulator unit tests; physical hardware tests documented as manual test scenarios; no HTTP/REST tests | firmware-test-{name} |
| shared / infra | covered by consumers' tests | no separate node needed |

**Playwright CANNOT test native mobile apps.** Never assign Playwright to a Flutter/iOS/Android
module. This is a hard constraint — violating it silently passes CI while leaving mobile untested.

**Game clients are NOT backend services.** Never assign `curl` or HTTP integration tests to a game
client module (Unity, Godot, Bevy, Phaser, pygame, PICO-8). Game clients communicate through
internal game loops and events, not REST endpoints. Curl-passing tests for a game client project
prove nothing about gameplay correctness.

**Event-driven services have no HTTP entry point.** Discord bots, CLI tools, cron workers, and
message queue consumers cannot be tested with curl or Playwright. Use unit tests with a mock
provider (mock Discord client, mock SQS consumer, mock cron scheduler). The test must exercise
the handler logic, not just the HTTP layer.

**Verification Node Merging (optional optimization):**
When multiple frontend modules share the same tech stack and build toolchain
(e.g., seller-web and admin-web are both React/Vite), they MAY share a single
compile-verify node to reduce total node count. Conditions for merging:
- Same build command (e.g., both use `npm run build`)
- Same test framework (e.g., both use vitest)
- No cross-module build dependencies
E2E nodes should NOT be merged — each module has distinct user flows and roles.

**Why per-module nodes matter:**
- API-only testing (curl) misses: broken routing, missing UI components, CSS rendering,
  auth token flow in browser, client-side validation, CORS problems
- Web Playwright misses: native mobile layout, platform-specific gestures, offline behavior
- Each app is a separate deployment surface with its own failure modes
- A passing API test does NOT prove the mobile app works

**Each module's E2E node must:**
- Use the appropriate tool for that module's tech stack (see table above)
- Exercise core user flows end-to-end (login → navigate → CRUD → verify)
- Produce evidence (screenshots, test reports, logs)
- Report pass/fail per flow

**Node-spec format:**

```yaml
---
node: <id>
exit_artifacts:
  - <file path>
---
```

Followed by:

```markdown
# Task: <goal, expanded into a clear task description>

## Project Context
<From bootstrap-profile: tech stack, modules, architecture>

## Context Pull

<Generated by bootstrap based on upstream nodes' Downstream Consumers tables.>
<Lists which upstream artifact fields this node must read before executing.>
<Split into required (missing = error return) and optional (missing = warning + continue).>
<If this node has no upstream nodes, this section is omitted.>

Example:

**必需（缺失则报错返回，不要继续执行）：**
- 从 `.allforai/bootstrap/source-summary.json` 读取 `tech_stacks` 字段，
  用于了解当前项目的技术栈，作为翻译策略选择的依据。

**可选（缺失则输出 warning 后继续，使用降级策略）：**
- 从 `.allforai/bootstrap/reuse-assessment.json` 读取 `per_component` 字段，
  用于了解每个组件的复用评估结果。缺失时按全量翻译策略继续。

## Theory Anchors
<Classical frameworks for this work, from knowledge files.

Bootstrap writes this section by reading the loaded capability file's own
`## Knowledge References → Phase-Specific` list and extracting the theory
framework names (e.g., "JTBD", "ERRC", "Clean Architecture"). List 2-4
framework names with a one-line description of how they apply to this node.
The subagent treats this as a complete reference — do NOT ask it to re-read
the capability file to find frameworks.>

## Knowledge References
<Relevant sections from cross-phase-protocols, defensive-patterns,
 domain knowledge, capability methodology — embedded, not just linked.

Bootstrap embeds the specific subsections of cross-phase-protocols.md and
defensive-patterns.md relevant to this node's capability (e.g., §B.3 Closure
Thinking for implementation nodes, §D User Confirmation Gate for decision
nodes). Do NOT just list file names — copy the relevant paragraph/table
verbatim so the subagent has complete context without re-reading source files.
The subagent treats this section as complete and does not re-read source files
unless the node-spec explicitly says to.>

## Guidance
<LLM-generated execution guidance based on absorbed knowledge.
 NOT fixed steps — principles, goals, quality bars, methodology.>

## Exit Artifacts
<What files must exist when done, with expected content description.

MUST include every path listed in the YAML frontmatter `exit_artifacts:` (which must match workflow.json).
May add descriptive guidance about expected content for each file.
Must NOT list additional files as artifacts beyond what's in the YAML frontmatter — `check_artifacts.py` validates exactly the YAML-listed paths.>

## Downstream Contract
<Who consumes this node's output, and what they need from it.

Algorithm: For each consumer node ID listed in workflow.json `consumers[]`:
1. Look up that consumer node's `capability` field in workflow.json
2. Load `knowledge/capabilities/<capability>.md` for that consumer
3. Find the row in the consumer capability's "Downstream Consumers" table where
   the artifact column matches this node's exit_artifact filename
4. Use the `Field Path` and `Reason` columns from that row to populate one contract line:
   "→ <consumer-node-id> reads: <Field Path> — <Reason>"
5. If the consumer capability has no Downstream Consumers table row for this artifact,
   write: "→ <consumer-node-id>: reads full artifact (no field-specific dependency declared)"

This algorithm mirrors the Context Pull algorithm (Step 3.3) but runs in the producing direction.>

Example:
  → design-loot-economy reads: mechanics[].name (weapon list), meta_loop.currencies
  → implement-combat-system reads: mechanics[].parameters (concrete numbers needed)
  → design-dungeon-generation reads: core_loop.steps (room encounter design)

## Integration Points
<Which OTHER parallel nodes produce components that THIS node must integrate.
 When nodes run in parallel, their outputs may need to connect at specific
 touchpoints. List each integration point explicitly so the subagent knows
 to leave hooks or import the sibling node's components.>

Example:
  ← implement-ios-learning produces: FlashHintOverlay.swift
    → THIS node's ChatView must: import and display FlashHintOverlay when
      user taps "hint" button, reading hint_full/hint_translation from
      Message.metadata
  ← implement-ios-learning produces: WordCardView.swift
    → THIS node's MessageBubble must: make tappable words trigger WordCardView
```

**Integration Points Rule (MANDATORY for parallel implementation nodes):**
**Parallel detection criterion**: Two nodes are considered parallel within the same module when:
(a) they share the same `blocked_by` set (both have the same dependencies, or both have empty `blocked_by`), AND
(b) their `exit_artifacts` paths share the same top-level directory prefix (e.g., both write into `flydict-ios/`).
Bootstrap detects this pattern during Step 3.1 node graph design and adds Integration Points sections to both node-specs.

When multiple implementation nodes run in parallel within the same module
(e.g., implement-ios-conversations + implement-ios-learning both produce
files inside flydict-ios/), the bootstrap MUST identify integration points
where their outputs need to connect.

For each product flow that spans multiple parallel nodes:
1. Trace the UI interaction path (e.g., user in ChatView taps word → WordCard)
2. Identify which node produces the trigger (ChatView) and which produces the
   target (WordCardView)
3. Add an Integration Points section to BOTH node-specs:
   - The trigger node: "must call/import X from sibling node Y"
   - The target node: "must expose X as a reusable component callable from Y"

If integration points are too complex for parallel execution, the nodes should
be sequenced instead (one depends on the other), or a dedicated integration
node should follow the parallel batch to wire everything together.

**Integration Stitch Node (MANDATORY after parallel implementation batch):**
When 2+ implementation nodes run in parallel within the same module, the
workflow MUST include a dedicated `stitch-{module}` node immediately after
the parallel batch completes, BEFORE compile-verify and E2E.

The stitch node's job:
1. Read all parallel nodes' exit artifacts (the files they created)
2. Read product-map business-flows to identify cross-component interactions
3. For each business flow, trace the UI path across files from different nodes
4. Detect disconnections: component A exists, component B exists, but A doesn't
   import/call B (or vice versa)
5. Fix each disconnection: add imports, wire up callbacks, connect data flow
6. Run compile check after fixes to ensure nothing broke
7. Produce a stitch report listing all connections made

```
Parallel impl nodes → stitch-{module} → compile-verify → E2E
                         ↑
                   Finds and fixes:
                   - Missing imports between sibling files
                   - UI triggers not wired to target components
                   - Data passed from API but not parsed by UI
                   - Callbacks/delegates not connected
                   - Navigation links pointing to placeholder instead of real view
```

The stitch node is lightweight (reads + patches, no new features) but catches
the integration gaps that parallel agents cannot see. It is the cheapest place
to catch these bugs — far cheaper than discovering them in E2E.

Exit artifact: `.allforai/bootstrap/stitch-{module}-report.json` with a list
of all connections made and any issues found.

**Node-spec for stitch nodes should include:**
- The list of parallel nodes whose outputs need stitching
- The product-map flows that cross node boundaries
- Specific integration points from the parallel nodes' specs
- Compile verification after all patches

**Enum Exhaustiveness Check (MANDATORY in stitch nodes):**
When the codebase defines an enum or type set (e.g., `SemanticType` with 13 values,
`ContentType` with 5 values, user roles, status codes, etc.), the stitch node MUST
verify that **every enum value has a code path in every consumer**.

```
For each enum/type set defined in the codebase:
  □ List all values (e.g., 13 semanticTypes)
  □ For each consumer of this enum:
    - API: is there code that GENERATES this value? (creation path)
    - Client: is there code that RENDERS this value? (display path)
    - E2E: is there a test that exercises this value? (test path)
  □ Any value missing a path in any consumer → gap to fix
```

This prevents the common failure pattern where a data model defines N types but
only M < N are actually handled downstream:
- API defines 13 semanticTypes → conversation_service only generates 3
- iOS MessageBubble switch has 5 cases → 8 fall through to default
- E2E tests only exercise "chat" messages → 12 types untested

The stitch node must produce a coverage matrix in its report:
```json
{
  "enum_coverage": {
    "SemanticType": {
      "total_values": 13,
      "api_generates": ["chat", "recast", "..."],
      "ios_renders": ["chat", "recast", "..."],
      "e2e_tests": ["chat"],
      "gaps": [
        {"value": "weekly_report", "missing_in": ["api", "e2e"]}
      ]
    }
  }
}
```

**Cross-Module Stitch Node (MANDATORY for multi-module projects):**
When the project has separate API and client modules (web/mobile), the workflow
MUST include a `cross-module-stitch` node after all implement + intra-module
stitch nodes complete, BEFORE compile-verify.

**Exemption — single-module game projects:** If the project is `is_game_project = true`
AND `bootstrap-profile.json.modules[]` has exactly ONE entry (the game client itself),
the cross-module-stitch node is NOT required. A single-module game has no API ↔ client
boundary to stitch. Skip to compile-verify (or game-test) directly after the intra-module
stitch. If the game has a dedicated backend (e.g., multiplayer server, leaderboard API as
a separate module), the exemption does not apply — stitch as normal.

**Exemption — library/SDK projects:** If `architecture_pattern = 'library-sdk'`, skip
cross-module-stitch entirely. Libraries are single consumable packages with no client/server
boundary — their "consumers" are external developers, not modules within the same project.
Internal packages within a library monorepo (e.g., packages/core + packages/react bindings)
DO still need intra-module stitch if they run in parallel, but not cross-module-stitch.

**Exemption — embedded/firmware projects:** If `architecture_pattern = 'embedded-firmware'`,
skip cross-module-stitch. Firmware communicates via hardware protocols, not HTTP APIs. If the
project includes both firmware AND a companion mobile/web app (e.g., BLE companion app),
cross-module stitch applies to the mobile↔API boundary only, not the firmware↔mobile boundary
(which is documented via protocol spec, not stitched via code analysis).

This extends the intra-module stitch (above) to cover cross-module integration.
Intra-module stitch catches missing imports within one codebase; cross-module
stitch catches API contract mismatches between separate codebases.

The cross-module stitch node's job:
1. Read API node's exit artifacts (route definitions, response schemas)
2. Read each client node's exit artifacts (API call sites, type definitions)
3. For each API endpoint, verify all consuming clients:
   - Parse the response correctly (field names, types, nesting)
   - Handle all response states (success, error, empty, paginated)
   - Send correct request format (query params, body schema, auth headers)
4. For each WebSocket/realtime message type (if applicable):
   - Server sends it → all clients handle it
   - Client sends it → server processes it
5. Fix mismatches: update client code to match API contract
6. Produce cross-module-stitch-report.json

```
Parallel impl nodes → stitch-{module} → cross-module-stitch → compile-verify → E2E
```

Exit artifact: `.allforai/bootstrap/cross-module-stitch-report.json`

**Node-spec for cross-module stitch should include:**
- The API node's exit artifacts (route/schema definitions)
- All client nodes' exit artifacts (API call sites)
- design-to-spec artifacts if available (api-spec.json as reference contract)
- WebSocket/protocol message types (if applicable)

**Game-protocol stitch (multiplayer/online games):**
When `is_game_project = true` AND the project has a dedicated server module (e.g., multiplayer
server, authoritative game server), the cross-module stitch must also verify the game
wire protocol — NOT just REST routes. Include in the stitch node-spec:
- WebSocket message schema (if game uses ws/socket.io) — client send ↔ server handler mapping
- UDP packet format (if game uses UDP; e.g., Godot's NetworkedMultiplayerENet, Unity's UTP)
- Authoritative server state synchronization: which game state fields the server owns vs. client predicts
- Client reconciliation flow: how server corrections are applied to client-side predicted state
- Verify: every message type the client sends has a matching server handler; every server broadcast has a matching client receiver

### 3.5 Coverage Self-Check (Concept → Workflow Closure)

> Goal: Verify that all features in product-concept.json are covered by at least one
> workflow node. Auto-fix gaps using Closure Thinking and Reverse Backfill convergence
> rules. Runs silently — no user confirmation needed.

**Trigger**: `has_product_concept` is true (from Step 1.0). If false AND `is_game_project` is true, run **Game Design Coverage Check** (§3.5.0) instead. If both false, skip to Step 3.4 (Confirm with User).

#### 3.5.0 Game Design Coverage Check (game projects without product-concept.json)

When `is_game_project = true` AND `has_product_concept = false`, run this abbreviated coverage check instead of the full §3.5 flow. The game-design nodes are themselves the design artifacts (equivalent role to product-concept.json), so coverage is checked against the selected game scenario template.

**Checks to run:**

| System Concern | Trigger Condition | Check |
|---------------|------------------|-------|
| Save/Load | game has progression (levels, stats, unlocks) | Is there a node covering save/load system or persistence design? If not, note as gap — document in bootstrap output as "Save system gap: game has progression but no save/load design node." |
| Audio | any audio-related content (music, SFX) referenced in narrative/world docs | Is `audio-design` in the selected nodes? If not, suggest opt-in. |
| Input/Control scheme | always applicable for game projects | Is input mapping covered in core-loop-design or a dedicated node? |
| Progression/Meta-loop | game has XP, levels, unlocks, or currency | Is `meta-game-design` or equivalent in selected nodes? |
| Tutorial / Onboarding | game has complex mechanics (action-rpg, strategy-sim, roguelike) | Is tutorial flow mentioned in any node's scope? |
| Platform-specific constraints | platform capability guard applied | Are suppressed monetization/retention nodes documented as "not applicable" in bootstrap output? |

If any gap is found: add a note to bootstrap output (not a blocker). Game projects in pure design mode proceed to game-design nodes regardless.

#### 3.5.1 Extract Feature Inventory

From `.allforai/product-concept/product-concept.json`, extract all declared features.
Source fields vary by schema — LLM uses semantic understanding, not hardcoded paths:

- `features[]` (structured feature list)
- `errc_highlights.must_have[]` + `errc_highlights.differentiators[]`
- `mvp_features[]` + `post_launch_features[]`
- Any other field that declares "the product will do X"

Output: a flat list of feature descriptions, each a natural-language statement.

#### 3.5.2 Closure-Driven Coverage Check

For each feature, two levels of verification:

**Level 1 — Direct Coverage:**
Does at least one node's `goal`, `exit_artifacts`, or node-spec body semantically
cover this feature? This is LLM semantic judgment, not string matching.

**Level 2 — Closure Completeness (6 types from cross-phase-protocols.md §B.3):**

| Closure Type | Check |
|-------------|-------|
| Config Closure | Feature needs configuration → is there a node for config management? |
| Monitoring Closure | Feature needs observability → is there a node for monitoring setup? |
| Exception Closure | Feature has failure modes → are recovery paths covered by a node? |
| Lifecycle Closure | Feature creates entities → is there cleanup/archival in some node? |
| Mapping Closure | Feature has A↔B pair → is B covered? (e.g., create↔delete, buy↔refund) |
| Navigation Closure | Feature is an entry point → is there an exit path in some node? |

**Game-specific closure types (added when `is_game_project = true`):**

| Closure Type | Check |
|-------------|-------|
| Save/Load Closure | Game has progression state → is there persistence/save-system implementation coverage? |
| Audio Closure | Game references music or SFX → is audio-design or audio-implementation covered? |
| Progression Closure | Game has XP/levels/unlocks → is meta-game-design or progression system covered? |
| Input Closure | Game requires player input → is controller/input scheme defined in core-loop or a dedicated node? |

Closure checks are **discovery-level** (as defined in §B.6): identify and mark what
should exist, not exhaustive implementation-level checks.

**Level 3 — Multi-Client Parity (when roles have multiple clients):**

If any role in product-concept.json has `clients[]` (multi-client declaration) with
`feature_parity` = `full`, `partial`, or `explicit`:

For each such role:
1. List all clients declared for this role
2. Determine check strategy based on parity mode:
   - `full`: every client must cover ALL MVP features for this role
   - `partial`: every client must cover all MVP features EXCEPT `parity_exceptions[]`
   - `explicit`: each client only needs to cover its own `supported_features[]`
3. For each feature × client pair that should be covered:
   - Check if that client has a corresponding implementation node
   - A feature that should be covered but has no node = gap

Auto-fix for multi-client gaps:
- If a feature has an implementation node for client A but not client B →
  create or extend a node for client B
- Each client needs its own compile-verify and E2E node (different tech stacks
  require different build/test tools)

**Backward compatibility**: if a role has only `client_type` (single client, legacy format),
skip Level 3 for that role — Level 1 and 2 are sufficient.

Example gap detection:
```
R1 消费者 (feature_parity: full, 3 clients):
  "商品搜索":
    buyer-ios:     implement-buyer-ios ✓
    buyer-android: implement-buyer-android ✓
    buyer-web:     ??? ← GAP: no implementation node for web client
    → auto-fix: create implement-buyer-web node
```

**Level 4 — Adaptive State Machine Coverage (when concept has adaptive_systems):**
> **Scope**: This check applies to WORKFLOW PLANNING — verifying that planned nodes
> cover all state machine implementation needs (storage, transitions, schedulers).
> It complements Step 3.1's check which verifies existing code. For new projects,
> Level 4 is the primary state machine check. For rebuild/translate, both run:
> Step 3.1 checks existing code gaps, Level 4 checks workflow node gaps.

If `product-concept.json` contains `adaptive_systems[]`, check each state machine for
three categories of gaps that Step 3.1's state machine check may have introduced:

1. **Dead state detection**: for each state dimension, verify at least one MVP-scope
   transition updates it. A dimension updated only by post_launch events (e.g.,
   `ai_tutor_session`) is a "dead state" in MVP — either remove it from MVP schema
   or add an alternative MVP-scope transition.

2. **Premature mapping detection**: for each behavior mapping, check if the behavior
   references a post_launch feature. If yes, the mapping cannot be implemented in MVP.
   Either defer the mapping or provide an MVP-scope fallback behavior.

3. **Background job detection**: for each transition or behavior that requires
   scheduled/periodic execution (keywords: "cron", "daily", "weekly", "window",
   "rolling", "periodic", "check every"), verify a scheduler/cron node exists in
   the workflow. Missing scheduler = the state will never be updated.

Auto-fix:
- Dead state → add alternative transition from MVP events, or mark dimension as post_launch
- Premature mapping → split into MVP behavior (simplified) + post_launch behavior (full)
- Missing scheduler → create a `scheduler-{name}` node

#### 3.5.3 Convergence-Controlled Auto-Fix

When uncovered features or broken closures are found, LLM decides:

- **Extend existing node** — if the gap is closely related to an existing node's domain
  (same business area, same tech module). Update that node's `goal`, `exit_artifacts`,
  and node-spec.
- **Create new node** — if the gap is a distinct concern not covered by any existing node.
  Append to `workflow.json` nodes[] and generate new node-spec at
  `.allforai/bootstrap/node-specs/<new-id>.md`.

**Convergence rules (from cross-phase-protocols.md §E Reverse Backfill):**

1. **Concept Sets the Boundary** — Only fix gaps derivable from `product-concept.json`.
   Features not in the concept are out of scope.
2. **Derivation Radius Decreases** — Bootstrap only fixes Ring 0 (directly missing
   features) and Ring 1 (first-order closure gaps, e.g., "login" exists → "password
   recovery" missing). Ring 2+ is deferred to execution-phase Reverse Backfill.
3. **Layer Cutoff** — Bootstrap = product design phase boundary. Ring 2+ belongs to
   development phase.

**Stop conditions (any one triggers stop):**

| Condition | Meaning |
|-----------|---------|
| Zero output | All features covered, all closures checked, no new gaps found |
| All downgraded | All remaining gaps are Ring 2+ (beyond bootstrap scope) |
| Scale reversal | A "gap" item's scope exceeds its parent feature → not a gap, it's a new feature |

#### 3.5.4 Write Coverage Matrix

Write `.allforai/bootstrap/coverage-matrix.json`:

```json
{
  "source": "product-concept.json",
  "checked_at": "<ISO timestamp>",
  "total_features": 25,
  "covered_before_check": 22,
  "auto_fixed": 3,
  "closure_derived": 2,
  "deferred_ring2_plus": 1,
  "final_coverage_rate": "100%",
  "matrix": [
    {
      "feature": "<feature description>",
      "covered_by": ["<node-id>"],
      "status": "covered"
    },
    {
      "feature": "<feature description>",
      "closure_type": "exception",
      "derived_from": "<parent feature>",
      "ring": 1,
      "status": "auto_added",
      "action": "extended node <node-id>"
    },
    {
      "feature": "<feature description>",
      "ring": 2,
      "status": "deferred",
      "reason": "ring2_cutoff | scale_reversal | all_downgraded"
    }
  ]
}
```

### 3.4 Confirm with User

Present summary:

```
Bootstrap 完成。

项目：{project_name}
目标：{goal}
技术栈：{tech stacks}

规划了 {N} 个节点：
  {list each node id + goal}

确认正确吗？
```

User confirms → proceed to Step 4.

---

## Step 4: Generate run.md

Read `${CLAUDE_PLUGIN_ROOT}/knowledge/orchestrator-template.md` for the template.
Write the result to `.claude/commands/run.md` in the target project.

No customization needed beyond what the template provides — the orchestrator
reads workflow.json at runtime, which already contains all project-specific information.

---

## Step 5: Validate

Run:
```bash
python .allforai/bootstrap/scripts/validate_bootstrap.py .allforai/bootstrap/
```

If errors: fix and re-validate (max 3 attempts).

---

## Step 6: Write Files to Target Project

### 6.1 Create Directories (preserve learned/)

```bash
mkdir -p .claude/commands
mkdir -p .allforai/bootstrap/node-specs
mkdir -p .allforai/bootstrap/learned   # preserved across re-bootstrap
```

**Re-bootstrap behavior:**
If `.allforai/bootstrap/` already exists (previous run):
- **Preserve**: `.allforai/bootstrap/learned/` (project experience, never delete)
- **Overwrite**: everything else (workflow.json, node-specs/, scripts/, protocols/)
- This means re-bootstrap resets workflow progress but keeps learned experience

### 6.2 Copy Orchestrator Scripts

Copy scripts and protocol files to the target project so `/run` works independently:

```bash
mkdir -p .allforai/bootstrap/scripts
mkdir -p .allforai/bootstrap/protocols
cp ${CLAUDE_PLUGIN_ROOT}/scripts/orchestrator/check_artifacts.py .allforai/bootstrap/scripts/
cp ${CLAUDE_PLUGIN_ROOT}/scripts/orchestrator/validate_bootstrap.py .allforai/bootstrap/scripts/
cp ${CLAUDE_PLUGIN_ROOT}/knowledge/diagnosis.md .allforai/bootstrap/protocols/
cp ${CLAUDE_PLUGIN_ROOT}/knowledge/learning-protocol.md .allforai/bootstrap/protocols/
cp ${CLAUDE_PLUGIN_ROOT}/knowledge/feedback-protocol.md .allforai/bootstrap/protocols/
```

> **Why copy?** The meta-skill plugin is installed in Claude's plugin cache.
> The target project needs its own copy so `/run` works even if the plugin
> is uninstalled or updated. All run.md references use project-local paths.

### 6.3 Write Files

Write these files (they were generated in memory during Steps 3-5, now persist them):

1. `.allforai/bootstrap/bootstrap-profile.json`
2. `.allforai/bootstrap/workflow.json`
3. `.allforai/bootstrap/coverage-matrix.json` (from Step 3.5, only if product-concept.json exists)
4. `.allforai/bootstrap/node-specs/*.md`
5. `.claude/commands/run.md`
6. `.allforai/bootstrap/scripts/check_artifacts.py`
7. `.allforai/bootstrap/scripts/validate_bootstrap.py`
8. `.allforai/bootstrap/protocols/*.md`

### 6.4 Confirm Completion

```
Bootstrap 完成。

已写入 {count} 个文件：
  .allforai/bootstrap/bootstrap-profile.json
  .allforai/bootstrap/workflow.json
  .allforai/bootstrap/coverage-matrix.json (覆盖率: {coverage_rate})
  .allforai/bootstrap/node-specs/ ({node_count} 个节点)
  .claude/commands/run.md

现在可以使用 /run [目标] 执行工作流。例如：
  /run 逆向分析
  /run 复刻到 SwiftUI
  /run 代码治理
```

---

## Error Recovery

If bootstrap fails at any step:
- Steps 1-2 (analysis): Likely a file access issue. Check project path.
- Step 3 (generation): Retry with more context from source files.
- Step 4-5 (run.md/validation): Fix based on validation errors.
- Step 6 (file writing): Check directory permissions.

All intermediate products are in memory until Step 6.
If bootstrap is interrupted, nothing is written. Run `/bootstrap` again.
