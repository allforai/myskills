# Auditor Enrichment Steps — design-to-spec

> This file is loaded by the Auditor Agent AFTER validation (auditor-validate.md) completes.
> Auditor's second job: read validated tasks.md → supplement quality sub-tasks.
> This is a SEPARATE agent call from validation — fresh attention for enrichment.

---

### Auditor 第二职责：注意力分离补充（审查完 V9-V12 后执行）

> Decomposer 只生成平铺的功能任务（B0-B5）。Auditor 审查后，**主动补充**质量子任务。
> 这比让 Decomposer 自己分离更可靠——Auditor 是独立 Agent，有全新注意力，且已读完全部产出。

**Auditor 补充流程**：

1. **异常加固子任务**（后端 B2 任务）：
   对每个 _Risk: HIGH/MEDIUM_ 的 B2 任务，Auditor 评估：
   - 该端点有哪些 Decomposer 未覆盖的异常场景？（边界/并发/降级/状态非法）
   - 有 → 生成 `B2.HARDEN.{seq}` 子任务，含具体异常清单
   - 无 → 跳过

2. **体验 DNA 子任务**（前端 B3 任务，experience-dna.json 存在时）：
   读取 design.md 的 `_DIFF:` 标注 + experience-dna.json，
   为每个 core/defensible DIFF 生成 `B3.DNA.{seq}` 子任务：
   ```
   - [ ] B3.DNA.{seq} [{sub-project}] [DNA-CRITICAL] {DIFF.name}
     - Component: {visual_contract.component}
     - Placement: {visual_contract.placement}
     - Spec: {visual_contract.spec}
     - Behavior: {visual_contract.behavior}
     - Must NOT: {visual_contract.must_not}
     - _DNA: DIFF-{id}_
     - _Risk: HIGH_
   ```

3. **其他质量维度子任务**（Auditor 自主判断）：
   Auditor 扫描 B3 主任务，识别缺失的质量维度并补充。常见维度（非穷举）：
   | 维度 | 子任务 Round 名 | 触发条件 |
   |------|---------------|---------|
   | 四态（empty/error） | B3.POLISH.{seq} | 页面规格有 states 但主任务只覆盖 loaded |
   | 国际化 | B3.i18n.{seq} | 前端子项目有 i18n 配置 |
   | 无障碍 | B3.a11y.{seq} | 项目要求 a11y |
   | 性能 | B3.PERF.{seq} | 页面有长列表/大图/复杂计算 |
   Auditor 可按项目特点创建新维度（如离线同步、动效等），不限于此表。

4. **测试任务细化**（所有子项目）：

   **核心原则：B3 前端任务也需要 Acceptance 条件**
   > B2 后端任务有 Acceptance（"POST /sessions → 200, status=in_progress"）→ 测试有据可依。
   > B3 前端任务没有 Acceptance → 测试不知道"验证什么" → 只测渲染不测行为 → bug 漏网。
   >
   > Auditor 为每个 B3 页面的交互控件（按钮/开关/表单/导航链接）生成**交互级 Acceptance**：
   > 描述"用户操作 X → 应该发生 Y"，供 B5 测试直接引用。

   **B3 交互级 Acceptance 生成方法**（LLM 语义推导）：
   Auditor 读取每个 B3 页面的 design.md 规格，对页面中每个用户可交互的控件：
   - 按钮 → "点击后应该：调 API / 导航到页面 / 弹出对话框 / 改变状态"
   - 开关/选择器 → "切换后应该：本地状态变化 + 视觉反馈 + (可选)保存到后端"
   - 表单 → "提交后应该：验证 → 调 API → 成功提示/导航 / 失败提示"
   - 列表项 → "点击后应该：导航到详情页"

   示例：
   ```
   B3 SettingsScreen _Acceptance_:
   - 切换 dark mode 开关 → app 主题立即切换为深色/浅色（不只是保存到后端）
   - 切换语言下拉框 → app 界面语言立即切换（不只是保存到后端）
   - 点击"订阅" → 导航到 /subscription
   - 点击"退出登录" → 清除 session → 跳转到 /login
   - 点击"删除账号" → 导航到确认页
   ```

   **后端子项目**：
   - 每个 B2 _Acceptance_ 条件 → 确保有对应的 B5 测试断言
   - 每个 B2.HARDEN 异常 → 生成 B5.HARDEN 测试

   **Web 前端子项目（Nuxt/Next/React）**：
   - 每个 B3 页面 → Auditor 生成交互级 Acceptance → B5 测试验证每条 Acceptance
   - 每个 B3.DNA → 生成 B5.DNA 行为测试
   - 粗粒度 E2E 测试保留（Playwright）

   **Flutter 移动端子项目（3 层测试策略）**：
   > Flutter 测试是当前短板。Auditor 必须为 Flutter 子项目生成 3 层测试任务：

   **层 1: B5.WIDGET — Widget 测试（`flutter test`，无需模拟器，CI 可跑）**
   - 每个 B3 屏幕 → 1 个 `test/screens/{screen}_test.dart`
   - 验证：组件渲染、状态切换（loading/loaded/error/empty）、用户交互响应
   - Mock API 层（MockApiClient），不需要真实后端
   - 覆盖目标：**所有屏幕**，不只是共享 widget
   ```
   - [ ] B5.WIDGET.{seq} [mobile-app] {ScreenName} Widget 测试
     - Files: `test/screens/{screen_name}_test.dart`
     - 测试 loaded 状态渲染正确的 Widget 树
     - 测试 loading 状态显示 LoadingIndicator
     - 测试 error 状态显示 ErrorView + 重试按钮
     - 测试关键用户交互（按钮点击、表单提交）
     - Mock: ApiClient, AuthService
   ```

   **层 2: B5.PROVIDER — Provider 测试（`flutter test`，无需模拟器）**
   - 每个 Riverpod Provider → 1 个测试文件
   - 验证：API 调用 → state 变化 → 正确通知 UI
   - Mock HTTP 层（MockDio），验证请求参数和响应处理
   ```
   - [ ] B5.PROVIDER.{seq} [mobile-app] {ProviderName} Provider 测试
     - Files: `test/providers/{provider_name}_test.dart`
     - 测试 load → success state
     - 测试 load → error state
     - 测试 mutation → optimistic update → server confirm
   ```

   **层 3: B5.E2E — 集成测试（Flutter 层 + 平台原生层）**

   > Flutter/RN 等跨平台框架在不同平台上行为不同。
   > `integration_test` 只测 Flutter 层，测不到原生层的集成（权限弹窗/推送/IAP/深链接/键盘）。
   > 所以层 3 分两个子层：

   **层 3a: Flutter 层集成测试（`integration_test`）**
   - 每条核心业务流 → 1 个 `integration_test/{flow_name}_test.dart`
   - 用 `flutter test integration_test/ -d {device}` 运行
   - 测试 Flutter 内的完整用户旅程（UI 交互 + API 调用 + 状态流转）
   - 不涉及原生平台特性
   ```
   - [ ] B5.E2E.{seq} [mobile-app] {FlowName} Flutter 集成测试
     - Files: `integration_test/{flow_name}_test.dart`
     - 设备: chrome(Web降级) / emulator / simulator
     - 测试完整用户旅程（登录→核心操作→结果验证）
   ```

   **层 3b: 平台原生集成测试（Platform-Specific）**
   - 仅当项目使用了平台原生特性时生成
   - Auditor 扫描 pubspec.yaml + ios/ + android/ 代码，识别原生集成点

   | 原生特性 | iOS 测试方式 | Android 测试方式 | 测试内容 |
   |---------|-------------|-----------------|---------|
   | 推送通知 | XCUITest / Patrol | Maestro / Patrol | 权限弹窗 → 授权 → 收到推送 → 点击跳转 |
   | IAP 支付 | XCUITest + StoreKit sandbox | Maestro + Google Play test track | 购买流程 → 回调 → 状态更新 |
   | OAuth 登录 | XCUITest（Safari WebView 交互） | Maestro（Chrome Custom Tab） | 跳转 → 授权 → 回调 → token |
   | 深链接 | XCUITest（Universal Links） | Maestro（App Links） | 链接打开 → 正确页面 |
   | 相机/相册 | XCUITest（权限 + 模拟选图） | Maestro | 权限弹窗 → 选图 → 上传 |
   | 生物识别 | XCUITest（模拟 FaceID/TouchID） | Maestro | 解锁流程 |
   | 键盘行为 | integration_test -d simulator | integration_test -d emulator | 输入框聚焦 → 键盘弹出 → 页面适配 |

   ```
   - [ ] B5.PLATFORM.{seq} [mobile-app] {Feature} 平台原生测试
     - Files: 由 task-execute Agent 根据工具可用性决定:
       Patrol 可用 → `integration_test/{feature}_platform_test.dart`（一套代码双平台）
       仅 iOS → `ios/RunnerTests/{feature}_test.swift`（XCUITest）
       仅 Android → `maestro/{feature}.yaml`（Maestro）
     - 执行前检测: `which patrol` / `which maestro` / `which xcodebuild`
     - 工具不可用 → 提醒用户安装，不写空壳测试脚本
   ```

   **工具选择由 task-execute Agent 在写代码时检测**（不在 spec 阶段硬编码）：
   - `which patrol` → 优先写 Patrol 测试（跨平台，一套代码）
   - 无 Patrol → `which xcodebuild` → 写 XCUITest（iOS only）
   - 无 Patrol → `which maestro` → 写 Maestro YAML（Android only）
   - 什么都没有 → 提醒用户安装测试工具，**不写空壳脚本**
   - Auditor 检查 `which patrol` / `which maestro` / `which xcodebuild` 决定使用哪个

   **Flutter 测试覆盖目标（更新）**：
   | 层级 | 覆盖目标 | CI 可跑？ | 工具 |
   |------|---------|----------|------|
   | Widget | 所有屏幕 | ✅ | `flutter test` |
   | Provider | 所有 Provider | ✅ | `flutter test` |
   | Flutter E2E | 核心业务流 | ⚠️ 需设备 | `integration_test` |
   | iOS 原生 | 原生集成点 | ⚠️ 需 Simulator | Patrol / XCUITest |
   | Android 原生 | 原生集成点 | ⚠️ 需 Emulator | Patrol / Maestro |

   **Flutter 测试覆盖目标**：
   | 层级 | 覆盖目标 | CI 可跑？ |
   |------|---------|----------|
   | Widget | 所有屏幕 | ✅ 是 |
   | Provider | 所有 Provider | ✅ 是 |
   | E2E | 核心业务流 | ⚠️ 需设备 |

   **React Native / Expo 子项目（同样 3 层策略）**：
   > RN 和 Flutter 类似但工具链不同。Auditor 根据 tech_stack 选择对应工具。

   **层 1: B5.COMPONENT — 组件测试（Jest + RNTL，无需设备，CI 可跑）**
   - 每个屏幕 → 1 个 `__tests__/{screen}.test.tsx`
   - 工具: Jest + @testing-library/react-native
   - Mock: MSW (Mock Service Worker) 拦截 API

   **层 2: B5.HOOK — Hook/状态测试（Jest，无需设备）**
   - 每个 custom hook / store → 1 个 test 文件
   - 工具: @testing-library/react-hooks 或 renderHook

   **层 3a: B5.E2E — Detox E2E（需设备）**
   - 核心业务流 → Detox test spec
   - 工具: Detox（优先）或 Maestro
   - 无设备 → NOT_TESTED

   **层 3b: B5.PLATFORM — 平台原生（同 Flutter）**
   - Maestro YAML（Android）/ Detox（iOS）

   | 层级 | 覆盖目标 | CI 可跑？ | 工具 |
   |------|---------|----------|------|
   | Component | 所有屏幕 | ✅ | Jest + RNTL |
   | Hook/Store | 所有 hooks | ✅ | Jest |
   | E2E | 核心业务流 | ⚠️ 需设备 | Detox / Maestro |
   | Platform | 原生集成点 | ⚠️ 需设备 | Maestro |

   **纯原生 iOS 子项目（Swift / SwiftUI）**：

   | 层级 | 工具 | CI 可跑？ | 说明 |
   |------|------|----------|------|
   | Unit | XCTest | ✅ | `xcodebuild test` 无需设备 |
   | UI/Screen | XCUITest | ⚠️ 需 Simulator | 每个屏幕 1 个 UI test |
   | E2E | XCUITest | ⚠️ 需 Simulator | 业务流端到端 |
   | Snapshot | swift-snapshot-testing | ✅ | 视觉回归（可选） |

   **纯原生 Android 子项目（Kotlin / Java）**：

   | 层级 | 工具 | CI 可跑？ | 说明 |
   |------|------|----------|------|
   | Unit | JUnit + Mockito | ✅ | 纯 JVM 测试 |
   | UI/Screen | Espresso 或 Maestro | ⚠️ 需 Emulator | 每个屏幕 1 个 UI test |
   | E2E | Maestro | ⚠️ 需 Emulator | YAML 脚本，易写易维护 |
   | Snapshot | Paparazzi | ✅ | 视觉回归（可选） |

   **桌面端子项目（Windows / macOS / Linux）**：

   | 平台 | 层级 | 工具 | 说明 |
   |------|------|------|------|
   | macOS (SwiftUI/AppKit) | Unit | XCTest | `xcodebuild test` |
   | macOS | UI | XCUITest | 需 macOS 运行环境 |
   | Windows (WinUI/.NET) | Unit | MSTest / xUnit | `dotnet test` |
   | Windows | UI | WinAppDriver 或 Playwright | 需 Windows 运行环境 |
   | Linux (GTK/Qt) | Unit | 语言原生测试框架 | `make test` |
   | Linux | UI | Playwright（如有 Web 界面）或 dogtail | 需 X11/Wayland |
   | **Electron / Tauri** | Unit | Jest / Vitest | ✅ CI 可跑 |
   | **Electron / Tauri** | E2E | **Playwright** | ✅ Playwright 原生支持 Electron |

   > 桌面端测试策略因平台差异大，Auditor 根据 tech_stack 从上表选择对应工具。
   > 工具不可用 → 提醒用户，标记 NOT_TESTED（和移动端同样原则）。

5. **补充后重检**：
   新增的子任务也需要通过 V9-V12 验证（确保子任务本身的质量）。
   这在 Auditor 的验证循环内自然完成（最多 3 轮）。

---

### V11 验收条件完整性（B2 任务强制）

> V9 回答"有没有对应的任务"，V10 回答"数据从哪来"，V11 回答"任务有没有可执行的验收标准"。
> 没有验收条件的任务 = 没有完成标准 = Phase 5 验收时才发现「代码有但行为不对」。

**V11.1 存在性检查**：每个 B2 任务是否有 `_Acceptance_` 字段？缺失 → `TASK_ACCEPTANCE_MISSING`（CRITICAL）
**V11.2 粒度检查**：验收条件数量是否达到 `_Risk_` 级别要求？不达标 → `TASK_ACCEPTANCE_INSUFFICIENT`（WARNING）
**V11.3 可执行性检查**：每条验收条件是否包含可验证断言（HTTP 方法 + 路径 → 状态码 / 响应字段 / 副作用）？模糊描述 → `TASK_ACCEPTANCE_INSUFFICIENT`（WARNING）

**修正方式**：
- `TASK_ACCEPTANCE_MISSING` → 基于 task-inventory 的 main_flow / exceptions / rules 自动生成 `_Acceptance_` 条件
- `TASK_ACCEPTANCE_INSUFFICIENT` → 补充缺失的异常路径 / 边界条件
- `TASK_DIFF_MISSING`（core）→ CRITICAL — 在对应前端子项目 tasks.md 补充 B3 任务，实现 DIFF 视觉契约指定的组件
- `TASK_DIFF_MISSING`（defensible）→ WARNING — 记录但不阻塞
- `TASK_DIFF_UNDERSPECIFIED` → WARNING — 补充 DIFF 的完整 visual_contract 规格到任务描述中（从 experience-dna.json 复制 spec+behavior+must_not）
- `TASK_API_GAP` → 在 tasks.md 中补充缺失的 B2 端点任务（遵循端点级原子性规则）
- `TASK_COVERAGE_CRITICAL` → 从 task-inventory.json 推导缺失的端点，补充 B2 + B3 + B5 任务
- `TASK_PROVENANCE_CRITICAL` → 补充行为上报端点（B2）+ 前端上报组件（B3）
- `TASK_DATA_GAP` → 补充 B1 定义任务
- `TASK_UX_GAP` → 补充 B3 页面任务
- 修正后回到小循环 A 重检（最多 3 次内循环）

---

### 小循环 B: XV 交叉审查（OpenRouter 可用时执行，否则跳过）

向专家模型发送：
```
{task-inventory.json 摘要} + {tasks.md 任务列表} + {小循环 A 审计结果}
要求：
1. 检查是否有产品功能在任务列表中完全缺失
2. 检查 B2 任务粒度是否合理（是否有 controller 级别的粗粒度任务）
3. 检查任务间依赖是否合理
输出：CONFIRM | REJECT(缺失列表) | SUGGEST(优化建议)
```

REJECT → 按缺失列表补充任务 → 重检
SUGGEST → 记录建议，不阻塞

---

### 小循环 C: 闭环审计

对 tasks.md 中每个模块/功能域检查 6 类闭环：

| 闭环类型 | 任务层审计问题 | 不通过标记 |
|---------|-------------|----------|
| 配置闭环 | 有 config_items 的功能是否有 B2 配置端点任务？ | `TASK_CLOSURE_CONFIG` |
| 监控闭环 | 有 audit 的功能是否有 B2 审计中间件任务？ | `TASK_CLOSURE_MONITOR` |
| 异常闭环 | 有 exceptions 的功能是否在 B2 任务的实现要点中提到？ | `TASK_CLOSURE_EXCEPTION` |
| 生命周期闭环 | 有状态机的实体是否有完整的状态变更端点任务？ | `TASK_CLOSURE_LIFECYCLE` |
| 映射闭环 | 有关联关系的实体是否有级联操作任务？ | `TASK_CLOSURE_MAPPING` |
| 导航闭环 | 每个前端页面是否有路由守卫 + 404 + 回退任务？layout 组件（header/footer/sidebar）中的链接目标是否在 pages/ 有对应页面任务？ | `TASK_CLOSURE_NAVIGATION` |
| 数据溯源闭环 | 返回聚合/统计数据的 GET 端点，其数据源是否有对应的写入端点/任务？（V10 的任务层投影） | `TASK_CLOSURE_PROVENANCE` |

修正 → 回到小循环 C 重检

---

### 退出条件

- V9 Coverage CRITICAL = 0（所有 CORE 产品任务有对应 B2 任务）
- V10 Provenance CRITICAL = 0（所有聚合数据有可追溯的写入路径）
- V11 Acceptance MISSING = 0（所有 B2 任务有验收条件）
- 4D 无 GAP（或已修复）
- 闭环无 CRITICAL 缺失
- V12 DIFF CRITICAL = 0（所有 core 级体验差异化契约在前端页面中有对应实现任务）
- Auditor 补充完成：HIGH risk 任务的子任务已补充，Acceptance 测试已派生

**大循环 3 轮后仍有问题** → 记录为已知问题到 `pipeline-decisions.json`，输出警告，继续（不停）

→ 输出进度: 「Step 4.3 验证 ✓ V9:{X}% V10:{Y}% V11:{Z}% V12 DNA:{W}% | 补充: HARDEN:{H} DNA:{D} POLISH:{P} 测试:{T} | gaps:{N} fixed | XV:{status}」
