# Bootstrap 特化阶段：RetailSphere

你是 bootstrap skill。分析以下项目结构，产出 specialization-report。

## 项目结构

```
claude/meta-skill/tests/fixtures/retail-sphere/
├── apps/consumer/pubspec.yaml                          # Flutter
├── apps/merchant-app/package.json                      # React Native
├── apps/merchant-app/metro.config.js                   # React Native 确认标记
├── apps/ios-vip/RetailSphere.xcodeproj/project.pbxproj # iOS/SwiftUI
├── apps/android-pos/build.gradle.kts                   # Android/Kotlin
├── apps/merchant-web/next.config.ts                    # Next.js
├── apps/admin-web/vite.config.ts                       # React/Vite
└── services/api/go.mod                                 # Go
```

## 执行步骤

### Step 1：模块识别（Step 1.1-1.2）

读取上述每个文件，识别 module_id、role、platform、detected_by。

识别规则：
- pubspec.yaml → Flutter mobile
- package.json + metro.config.js → React Native mobile
- *.xcodeproj → iOS/SwiftUI mobile
- build.gradle.kts → Android/Kotlin mobile
- next.config.ts → Next.js frontend
- vite.config.ts（无 metro）→ React/Vite frontend
- go.mod → Go backend

### Step 2：工具分配（Step 3.1）

参考以下约束，为每个模块分配 compile_tool、test_tool、e2e_tool：

| Module Type | compile_tool | test_tool | e2e_tool |
|-------------|-------------|-----------|----------|
| Flutter | `flutter build apk` | `flutter test` | `flutter test integration_test/` |
| React Native | `npx react-native build-android` | `jest` | `detox test` 或 `maestro test` |
| iOS/SwiftUI | `xcodebuild build -scheme RetailSphere` | `xcodebuild test` | XCUITest |
| Android/Kotlin | `./gradlew assembleDebug` | `./gradlew test` | `./gradlew connectedAndroidTest` |
| Next.js | `npm run build` | `vitest` 或 `jest` | Playwright |
| React/Vite | `vite build` | `vitest` | Playwright |
| Go | `go build ./...` | `go test ./...` | curl/HTTP client |

**硬约束：Playwright CANNOT test native mobile apps。**
任何 mobile 模块（Flutter/React Native/iOS/Android）的 e2e_tool 不得为 Playwright。
违反此约束 → constraint_violations 计数 +1。

任何未分配 node-spec 的模块 → missing_nodes 计数 +1。

### Step 3：输出

严格按以下 JSON schema 输出，不添加额外字段：

```json
{
  "modules_detected": <number>,
  "constraint_violations": <number>,
  "missing_nodes": <number>,
  "tool_assignments": [
    {
      "module_id": "<string>",
      "role": "mobile|frontend|backend",
      "platform": "<string>",
      "compile_tool": "<string>",
      "test_tool": "<string>",
      "e2e_tool": "<string>",
      "playwright": <boolean>
    }
  ]
}
```

## 与预期输出比对

完成后，将你的输出与以下预期比对：

```json
{
  "modules_detected": 7,
  "constraint_violations": 0,
  "missing_nodes": 0,
  "tool_assignments": [
    {"module_id": "consumer",      "e2e_tool": "flutter test integration_test/", "playwright": false},
    {"module_id": "merchant-app",  "e2e_tool": "detox|maestro",                  "playwright": false},
    {"module_id": "ios-vip",       "e2e_tool": "xcodebuild test",                "playwright": false},
    {"module_id": "android-pos",   "e2e_tool": "gradlew connectedAndroidTest",   "playwright": false},
    {"module_id": "merchant-web",  "e2e_tool": "playwright",                     "playwright": true},
    {"module_id": "admin-web",     "e2e_tool": "playwright",                     "playwright": true},
    {"module_id": "api",           "e2e_tool": "curl",                           "playwright": false}
  ]
}
```

如有差异，在输出中标注 DIFF。
