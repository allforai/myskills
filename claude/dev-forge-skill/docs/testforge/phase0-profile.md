## Phase 0：项目画像 + 测试基础设施探测

### Step 0.1: 消费上游决策

按上游消费链优先级获取子项目列表、技术栈、测试框架。

### Step 0.2: 测试基础设施探测

对每个子项目，扫描以下维度：

| 维度 | 探测方式 | 产出 |
|------|---------|------|
| 单元测试框架 | 扫描项目配置文件和依赖声明，推理出使用的单元测试框架 | unit_framework |
| 测试配置 | Read 测试框架配置文件 → 提取 environment, setupFiles, include patterns | config_summary |
| Setup 文件 | Read setupFiles 路径 → 提取 mock 列表和 plugin 注册 | setup_summary |
| Test Helpers | Glob 常见测试辅助目录（`**/test/helpers/**` `**/__tests__/{render,helpers,utils,factories}.*` 等） | helpers_list |
| Factories | Glob 常见 factory 目录 | factory_list |
| 现有单元测试 | Glob 项目中已有的单元测试文件（按语言和框架惯例匹配） | existing_unit_tests[] |
| 测试脚本 | Read 项目配置（package.json / Makefile / pubspec.yaml 等）→ 提取测试命令 | test_commands |
| E2E 框架 | 扫描项目中已有的 E2E 测试配置和目录（LLM 自行推理，不限定具体框架）。**必须同时检查平台/框架内建测试能力**（如 Android Espresso、iOS XCUITest、Flutter integration_test），不能只看第三方依赖 | e2e_framework |
| 现有 E2E 测试 | Glob 项目中已有的 E2E 测试文件 | existing_e2e_tests[] |
| 前端路由表 | 根据项目框架扫描路由文件（pages 目录 / 路由配置文件等） | page_routes[] |
| API 路由表 | Grep 后端路由注册模式（根据项目语言和框架推理） | api_endpoints[] |
| 子项目端口 | 读 .env / project-manifest / 配置文件中的 port 定义 | ports_map |
| E2E 工具可用性 | **LLM 推理**：根据项目平台和技术栈，检测可用的 E2E 测试工具（平台内建工具 + MCP 工具列表 + `which` CLI 探测 + 项目依赖声明）。探测顺序：① 平台/框架内建 → ② 项目已安装的第三方 → ③ 环境中的 CLI 工具 | e2e_tools_available |
| 跨平台目标 | 见下方「跨平台探测」 | target_platforms[] |
| 平台测试环境 | 见下方「跨平台探测」 | available_platforms[] |

**跨平台探测**（任何跨平台框架）：

跨平台框架一份代码编译到多个平台。testforge 的原则是**能测几个平台就测几个平台**。

Step 1: 识别目标平台

**LLM 自行推理**：扫描项目根目录的配置文件、依赖声明和目录结构，推理出：
- 使用的跨平台框架（Flutter / React Native / .NET MAUI / KMP / Tauri / Electron / 等）
- 目标平台列表（从目录结构、构建配置、target 声明中推断）

> 不硬编码框架清单。LLM 根据项目实际配置文件推理，新框架出现时自动适配。

Step 2: 检测平台测试环境可用性

**LLM 自行推理**：根据识别出的目标平台，逐一检测当前环境是否支持该平台的测试：
- **主机测试**（unit/widget）：始终可用
- **Web E2E**：检测可用的浏览器自动化工具（MCP 工具列表 + CLI 探测）
- **移动端**：检测模拟器/真机可用性（`adb devices` / Simulator 等）
- **桌面端**：检测当前 OS 是否匹配目标平台
- **工具不可用时**：记录降级方案（见下方）

**移动端降级到桌面原生**（Flutter / RN 等跨平台框架专用）：

当 Android/iOS 模拟器或真机不可用时，如果当前操作系统有对应的桌面目标（Linux 有 `linux/`、macOS 有 `macos/`、Windows 有 `windows/`），降级为桌面原生运行 + 手机分辨率窗口：

1. **检测桌面目标**：`flutter devices` 列出可用设备，选择当前操作系统的桌面设备
2. **设置手机分辨率**：在桌面平台的窗口配置中设置为手机尺寸（如 393x852 或 414x896）
   - Flutter Linux: 修改 `linux/runner/my_application.cc` 中的 `gtk_window_set_default_size`
   - Flutter macOS: 修改 `macos/Runner/MainFlutterWindow.swift` 中的 window frame
   - Flutter Windows: 修改 `windows/runner/main.cpp` 中的窗口尺寸
3. **运行集成测试**：`flutter test integration_test/ -d linux`（或 macos/windows）
4. **标记为降级测试**：报告中标注 `DESKTOP_SUBSTITUTE`，说明"在 {desktop} 上以 {resolution} 手机分辨率运行，替代 {android/ios} 测试"

> **这不等同于真机测试**——桌面原生不测手势、推送、传感器、权限弹窗等移动端特有行为。
> 但它**能测到**：路由导航、状态管理、API 调用、数据渲染、业务逻辑——覆盖了 80% 的 E2E 价值。
> 比 NOT_TESTED 好得多。

降级优先级：桌面原生（手机分辨率）> PLAN_ONLY > NOT_TESTED

> **Flutter Web (`-d chrome`) 不是有效的移动端降级**。Flutter Web 用的是 Web 渲染引擎（HTML/CanvasKit），跟原生 UI 框架完全不同——Widget 行为、手势处理、平台通道全部不一样。在 Chrome 上测通过不代表原生端没问题。桌面原生（`-d linux`/`-d macos`）虽然也不是移动端，但至少用的是同一套 Flutter 原生渲染管线。

Step 2.5: Web 应用路由模式和渲染模式探测

**路由模式探测**（影响 E2E 测试的 URL 构造）：

| 框架 | 探测方式 | 结果 |
|------|---------|------|
| Flutter Web | 检查 `web/index.html` 中 `<base href>` + GoRouter 配置中 `urlPathStrategy` | hash → URL 用 `/#/path`；path → URL 直接用 `/path` |
| Nuxt/Next | 默认 history 模式 | path routing |
| Vue Router | `router/index` 中 `createWebHashHistory` vs `createWebHistory` | hash 或 history |
| React Router | `<HashRouter>` vs `<BrowserRouter>` | hash 或 history |

路由模式写入 `test-profile.json` 的 `routing_mode` 字段。E2E 测试生成时，hash 模式下所有 URL 自动加 `/#` 前缀。

**WebGL/渲染模式探测**（影响 Flutter Web E2E 策略）：

| 条件 | 检测 | E2E 策略 |
|------|------|---------|
| WSL2 环境 | `uname -r` 含 `microsoft` 或 `WSL` | 标记 `WEBGL_UNSTABLE` |
| 无 GPU | `lspci` 无 GPU 或 `glxinfo` 失败 | 标记 `WEBGL_UNSTABLE` |
| WEBGL_UNSTABLE | — | Flutter Web 用 `--web-renderer html` 替代 canvaskit；Playwright 增加 `retries: 3` + `workers: 1` |
| WebGL 正常 | — | 默认 canvaskit，正常并行 |

输出示例：
```
跨平台目标: [android, ios, web, macos]
可用测试环境: [主机 ✓, web ✓, android ✗(无模拟器), ios ✗(非macOS), macos ✗(非macOS)]
→ 可执行: 主机测试(unit/widget) + Web E2E
→ 仅生成脚本: Android/iOS/macOS 集成测试
```

### Step 0.2.8: 测试基础设施健康检查

**在跑基线前，检查已有测试配置的潜在问题：**

| 检查项 | 检测方式 | 修复 |
|--------|---------|------|
| conftest teardown 用 DROP SCHEMA/DROP TABLE | Grep conftest 中 `DROP SCHEMA\|DROP TABLE` | 改为 TRUNCATE（保留表结构，E2E 共享 DB） |
| vitest/jest 扫了 e2e 目录 | 检查 include/exclude 配置 + 是否有 playwright.config | 添加 `exclude: ['**/e2e/**']` |
| vitest/jest 扫了 node_modules | 检查 exclude 配置 | 确保排除 node_modules |
| pytest 和 E2E 混跑 | 检查 tests/ 下是否有 e2e/ 子目录 | E2E 用 `--ignore=tests/e2e` 隔离，或 e2e/ 有自己的 conftest 覆盖 |

**原因**：这些配置问题导致单独跑通但混跑失败，是 testforge 首轮失败的常见根因。前置检查比事后修复高效得多。

### Step 0.3: 基线测试运行

**在审计之前，必须先跑一遍现有测试建立基线。** 不跑基线 → Phase 4 分不清"新测试暴露的 bug"还是"原来就坏的测试"。

对每个子项目，使用探测到的测试命令运行全量测试：

```
逐子项目运行（可并行，各子项目互不影响）：
  - 从项目配置中读取测试命令（package.json scripts.test / Makefile test target / 框架 CLI 等）
  - LLM 根据探测到的技术栈推理正确的测试运行命令，不硬编码
  - E2E：使用项目已有的 E2E 测试命令运行（仅已有脚本，不生成新的）
        ⚠ E2E 基线需要应用运行；先检查端口可达性，不可达则跳过，标记 E2E_BASELINE_SKIPPED

记录：
  baseline_tests: {总测试数}
  baseline_pass: {通过数}
  baseline_fail: {失败数}
  baseline_skip: {跳过数}
  pre_existing_failures: [{文件, 测试名, 错误信息}]

处理：
  全部通过 → 基线清洁，继续
  有失败 → 记录为 PRE_EXISTING_FAILURE，Phase 4 的 CG-1 排除这些测试
  环境问题导致无法运行（如 Redis 不可用）→ 记录 ENV_ISSUE，该子项目基线标记为 PARTIAL
```

### Step 0.4: 输出画像摘要

```
## 测试画像

| 子项目 | 类型 | 单元框架 | E2E 框架 | 测试数 | 通过 | 失败 | Helpers | Factories |
|--------|------|---------|---------|-------|------|------|---------|-----------|
| ... | frontend/backend/cross-platform | ... | ... | ... | ... | ... | ... | ... |
```

写入 `.allforai/testforge/test-profile.json`。

### Step 0.5: 加载上游文档（按需）

检查并加载以下上游产物（存在则加载，不存在则标注缺失，不阻断）：

| 产物 | 路径 | 用途（Phase） |
|------|------|-------------|
| design.md | `.allforai/project-forge/sub-projects/*/design.md` | Phase 1 Layer 1 |
| design.json | `.allforai/project-forge/sub-projects/*/design.json` | Phase 1 Layer 1（API 端点提取） |
| tasks.md | `.allforai/project-forge/sub-projects/*/tasks.md` | Phase 1 Layer 2 |
| business-flows.json | `.allforai/product-map/business-flows.json` | Phase 1 Layer 3, Phase 3 Layer B, **Phase 4 E2E 链推导** |
| constraints.json | `.allforai/product-map/product-map.json` 中 constraints | Phase 1 Layer 3, Phase 5 |
| concept-baseline.json | `.allforai/product-concept/concept-baseline.json` | Phase 5 |
| role-profiles.json | `.allforai/product-map/role-profiles.json` | Phase 2 H2, Phase 3 Layer C, Phase 5 |
| use-case-tree.json | `.allforai/product-map/use-case-tree.json` | Phase 1 Layer 3, **Phase 4 E2E 负向场景** |
| e2e-scenarios.json | `.allforai/project-forge/e2e-scenarios.json` | Phase 4 E2E 链（已有规划则复用） |
| experience_priority | `.allforai/product-map/product-map.json` | Phase 1 Layer 3, Phase 3 Layer B/C, Phase 4 路径 B/C/D |

**无上游文档时的降级**：
- 无 design.md/design.json → Phase 1 跳过 Layer 1，仅做 Layer 0（代码级审计）
- 无 tasks.md → Phase 1 跳过 Layer 2
- 无 product-map → Phase 1 跳过 Layer 3，Phase 3 跳过 Layer B/C，Phase 5 跳过
- 无 business-flows + 无 e2e-scenarios → Phase 4 跳过 E2E 链锻造，仅做单元/组件测试
- 全部缺失 → 仅做 Layer 0 代码级审计 + Phase 3 Layer A 代码级负空间 + Phase 4 单元测试锻造

写入 `testforge-decisions.json`。

---
