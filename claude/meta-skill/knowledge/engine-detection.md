# Engine and stack detection

Read during bootstrap Step 1. Classify `architecture_pattern`, `is_game_project`, modules, and runtime needs. Skip missing marker files. Do not ask the user to restate what these files already say.

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

### 1.3 Sample Core Files

Read the most informative files until the profile's remaining questions are answered — there
is no required sample count; a monorepo needs a sample per module, a single service may need
three files. Typically:
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


### 1.5.1 Runtime Environment Awareness (when goals include code implementation)

When goals include translate/rebuild/create/implement (b/c/d/l), demo-forge will run and needs a live
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

