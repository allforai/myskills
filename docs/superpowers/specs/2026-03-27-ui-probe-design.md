# UI Probe — 可观测 UI 测试基础设施

> 需求文档 | 2026-03-27
> 状态：需求定义（待独立项目实施）

---

## 1. 问题陈述

当前 AI 驱动的测试和验收（testforge / cr-visual）是**纯黑盒**模式：

- 截图 → LLM 看图 → 猜测"DataGrid 有没有数据"
- Playwright 操作 → 等固定时间 → 检查 DOM 文本
- 联动验证 → 触发 → 等 500ms-2s → 看结果

这带来三个核心问题：

| 问题 | 根因 | 后果 |
|------|------|------|
| **效率低** | 每次验证都要截图、等待、重试 | 60 个页面的验收需要 2+ 小时 |
| **不稳定** | 依赖时序（网络延迟、渲染时机） | 同一个测试有时过有时不过 |
| **深度不够** | 只能看到外部表现，看不到内部状态 | "有数据"但不知道数据是否正确、来源是否对 |

**根本原因**：UI 不会"说话"。测试工具只能从外部观察，无法从内部获取信息。

## 2. 目标

构建一套**轻侵入、强表达**的 UI 可观测基础设施，让 UI 具备以下能力：

1. **可识别**：每个关键控件有唯一语义标识
2. **可查询**：LLM/测试工具能直接查询控件状态，不靠截图猜
3. **可感知**：状态变化有事件通知，不靠固定等待
4. **可诊断**：问题发生时能追溯到数据来源和触发链路

最终效果：

```
黑盒（现在）：
  screenshot → LLM read image → "看起来有数据" → 可能误判

白盒可观测（目标）：
  probe.query('#order-list') → {
    component: "DataGrid",
    state: "loaded",
    rows: 8,
    dataSource: "GET /api/orders → 200 OK",
    lastUpdated: "2026-03-27T10:30:00Z"
  }
```

## 3. 设计原则

| 原则 | 说明 |
|------|------|
| **零业务逻辑耦合** | 不读业务代码来设计测试，只观测 UI 层的显示对象和状态 |
| **轻侵入** | 开发者仅需在关键控件上加 HTML 属性标注，一个页面 5-10 个，总成本 < 30 分钟 |
| **生产零影响** | 收集器仅在测试环境注入，生产构建完全不包含 |
| **跨框架通用** | React / Vue / Svelte / Angular / 原生 HTML / WebView 均适用 |
| **LLM 友好** | 查询接口返回结构化 JSON，不是 DOM 树 |

## 4. 两层架构

### 第一层：轻标注规范（开发时）

在 UI 控件上添加语义化的 `data-probe-*` 属性：

```html
<!-- 数据容器 -->
<table
  data-probe-id="order-list"
  data-probe-type="data-container"
  data-probe-state="loaded"
  data-probe-source="GET /api/orders"
  data-probe-rows="8"
>

<!-- 选择器 -->
<select
  data-probe-id="status-filter"
  data-probe-type="selector"
  data-probe-state="ready"
  data-probe-options-count="5"
  data-probe-source="GET /api/order-statuses"
>

<!-- 联动关系 -->
<select
  data-probe-id="province-select"
  data-probe-type="selector"
  data-probe-linkage-target="city-select"
  data-probe-linkage-type="options_update"
>

<!-- 页面级状态 -->
<div
  data-probe-page="order-management"
  data-probe-page-state="ready"
  data-probe-page-ready-when="order-list.state === loaded AND status-filter.state === ready"
>
```

**标注类型**：

| 属性 | 用途 | 示例 |
|------|------|------|
| `data-probe-id` | 唯一语义标识 | `order-list`, `submit-btn` |
| `data-probe-type` | 控件类型 | `data-container`, `selector`, `display-binding`, `chart`, `media`, `form`, `action` |
| `data-probe-state` | 当前状态 | `loading`, `loaded`, `error`, `empty`, `disabled`, `submitting` |
| `data-probe-source` | 数据来源 | `GET /api/orders`, `computed:quantity*price`, `static:enum` |
| `data-probe-rows` | 数据行数（容器类） | `8`, `0` |
| `data-probe-options-count` | 选项数（选择器类） | `5`, `0` |
| `data-probe-value` | 当前值（绑定类） | 实际显示值 |
| `data-probe-linkage-target` | 联动目标 | `city-select` |
| `data-probe-linkage-type` | 联动类型 | `options_update`, `visibility_toggle`, `enabled_toggle`, `value_update`, `data_filter` |
| `data-probe-page` | 页面标识 | `order-management` |
| `data-probe-page-state` | 页面整体状态 | `loading`, `ready`, `error` |
| `data-probe-page-ready-when` | 页面就绪条件 | 表达式，所有关键控件 loaded |

**动态更新**：`data-probe-state` 和 `data-probe-rows` 等属性需随实际状态实时更新（通过框架绑定或 MutationObserver 自动同步）。

### 第二层：运行时收集器（测试时注入）

一段独立脚本，在测试环境启动时通过 Playwright `addInitScript` 或 `<script>` 标签注入：

**核心 API**（暴露为 `window.__probe__`）：

```typescript
interface UIProbe {
  // === 查询 ===
  query(id: string): ProbeElement | null;
  queryAll(type: string): ProbeElement[];
  queryPage(): PageState;

  // === 状态监听 ===
  waitForState(id: string, state: string, timeout?: number): Promise<void>;
  waitForPageReady(timeout?: number): Promise<void>;
  onStateChange(id: string, callback: (old, new) => void): Unsubscribe;

  // === 联动验证 ===
  verifyLinkage(triggerId: string, action: string): Promise<LinkageResult>;

  // === 网络关联 ===
  getNetworkLog(): NetworkEntry[];
  getDataSourceStatus(id: string): DataSourceInfo;

  // === 快照 ===
  snapshot(): ProbeSnapshot;  // 所有控件状态的完整快照
  diff(a: ProbeSnapshot, b: ProbeSnapshot): SnapshotDiff[];
}

interface ProbeElement {
  id: string;
  type: string;
  state: string;
  source: string;
  rows?: number;
  optionsCount?: number;
  value?: string;
  disabled?: boolean;
  visible?: boolean;
  linkageTargets?: string[];
  element: HTMLElement;  // 底层 DOM 引用
}

interface PageState {
  page: string;
  state: string;  // loading | ready | error
  readyCondition: string;
  elements: ProbeElement[];
  unreadyElements: string[];  // 哪些控件还没 ready
}

interface LinkageResult {
  trigger: string;
  action: string;
  effects: Array<{
    target: string;
    expectedType: string;
    beforeState: any;
    afterState: any;
    result: 'pass' | 'fail' | 'timeout';
    duration: number;  // 联动响应时间 ms
  }>;
}

interface DataSourceInfo {
  url: string;
  method: string;
  status: number;
  responseTime: number;
  payload?: any;  // 可选：API 返回的数据
}
```

**收集器职责**：

```
启动时：
  1. 扫描所有 data-probe-* 标注 → 构建组件注册表
  2. 启动 MutationObserver → 监听标注属性变化 → 自动更新状态
  3. 拦截 fetch/XHR → 关联 API 调用与 data-probe-source
  4. 监听 WebSocket/SSE → 追踪推送事件

运行时：
  5. 响应 query/queryAll → 返回结构化组件信息
  6. 响应 waitForState → 基于 MutationObserver 的事件驱动等待（非轮询）
  7. 响应 waitForPageReady → 等所有关键控件的 state 达到 ready/loaded
  8. 响应 verifyLinkage → 自动读联动目标的 before/after 状态

不做：
  - 不修改 DOM
  - 不拦截用户操作
  - 不影响业务逻辑
  - 不在生产环境加载
```

## 5. 与测试工具的集成

### 5.1 testforge 集成

```
当前（黑盒）：
  test('order list has data', async () => {
    await page.goto('/orders');
    await page.waitForTimeout(2000);  // 固定等待 ← 不稳定
    const rows = await page.$$('tr.order-row');
    expect(rows.length).toBeGreaterThan(0);  // Level 1 惰性断言
  });

改后（白盒可观测）：
  test('order list has data', async () => {
    await page.goto('/orders');
    await page.evaluate(() => window.__probe__.waitForPageReady());  // 智能等待
    const list = await page.evaluate(() => window.__probe__.query('order-list'));
    expect(list.state).toBe('loaded');              // Level 2
    expect(list.rows).toBeGreaterThanOrEqual(1);    // Level 2
    expect(list.source).toContain('/api/orders');    // Level 3: 验证数据来源正确
    const sourceInfo = await page.evaluate(() => window.__probe__.getDataSourceStatus('order-list'));
    expect(sourceInfo.status).toBe(200);            // Level 3: API 真的返回了 200
  });
```

关键改进：
- `waitForPageReady()` 替代固定 `waitForTimeout` → 消除时序不稳定
- `query()` 替代 DOM 选择器 → 语义化查询
- `getDataSourceStatus()` → 验证数据来源正确性（不只是"有数据"）

### 5.2 cr-visual 集成

```
当前（黑盒）：
  Step 4.5 data-integrity agent:
    Read 截图 → LLM 看图 → "DataGrid 看起来有数据" → 可能误判

改后（白盒可观测）：
  Step 4.5 data-integrity agent:
    probe.queryAll('data-container') → [{id: 'order-list', state: 'loaded', rows: 8, source: 'GET /api/orders'}]
    probe.queryAll('selector') → [{id: 'status-filter', state: 'ready', optionsCount: 5}]
    → 精确判定，零误判
```

### 5.3 联动验证集成

```
当前（黑盒）：
  Step 4.6 linkage agent:
    select "广东省" → wait 2s → 截图 → LLM 看城市下拉有没有变化

改后（白盒可观测）：
  const result = await page.evaluate(() =>
    window.__probe__.verifyLinkage('province-select', 'select:广东省')
  );
  // result = {
  //   trigger: 'province-select',
  //   effects: [{
  //     target: 'city-select',
  //     expectedType: 'options_update',
  //     beforeState: { optionsCount: 0 },
  //     afterState: { optionsCount: 21, source: 'GET /api/cities?province=广东' },
  //     result: 'pass',
  //     duration: 340  // 340ms 响应
  //   }]
  // }
```

### 5.4 异步接缝四态集成

```
当前（黑盒）：
  Rule 27 Pending 态：throttle 慢网 → 截图 → LLM 看有没有 loading

改后（白盒可观测）：
  // 提交订单
  await page.click('#submit-btn');
  // 立即查询状态（不等待）
  const pending = await page.evaluate(() => window.__probe__.query('submit-btn'));
  expect(pending.state).toBe('submitting');  // 按钮进入 submitting 态
  expect(pending.disabled).toBe(true);       // 按钮禁用

  // 等待完成
  await page.evaluate(() => window.__probe__.waitForState('submit-btn', 'idle'));
  const done = await page.evaluate(() => window.__probe__.queryPage());
  expect(done.state).toBe('ready');
```

## 6. 平台覆盖策略

| 平台 | 标注方式 | 收集器注入 | 覆盖度 |
|------|---------|-----------|--------|
| **React/Next.js** | `data-probe-*` HTML 属性 | Playwright `addInitScript` | 完整 |
| **Vue/Nuxt** | `data-probe-*` HTML 属性 | Playwright `addInitScript` | 完整 |
| **Svelte/SvelteKit** | `data-probe-*` HTML 属性 | Playwright `addInitScript` | 完整 |
| **Angular** | `data-probe-*` HTML 属性 | Playwright `addInitScript` | 完整 |
| **Flutter Web** | `data-probe-*` 通过 `Semantics` widget | Playwright `addInitScript` | 完整 |
| **Flutter Mobile** | `Semantics` label + Flutter Driver | Flutter integration_test | 需适配器 |
| **SwiftUI** | `accessibilityIdentifier` | XCUITest | 需适配器 |
| **Jetpack Compose** | `testTag` | UI Automator | 需适配器 |
| **React Native** | `testID` prop | Detox/Appium | 需适配器 |

**第一阶段**：Web 平台（覆盖 React/Vue/Svelte/Angular/Flutter Web）— 统一的 `data-probe-*` + JS 收集器
**第二阶段**：移动原生（Flutter/SwiftUI/Compose）— 平台专属适配器，但暴露相同的 `ProbeElement` 接口

## 7. 标注自动生成

### 7.1 dev-forge 生成时自动标注

`/task-execute` 生成前端组件代码时，自动为关键控件添加 `data-probe-*` 属性：

```
生成规则（写入 design-to-spec 的代码生成规范）：
  - 每个数据容器（Table/List/Tree）→ 加 data-probe-id + type + source
  - 每个选择器（Select/Dropdown）→ 加 data-probe-id + type + source
  - 每个表单提交按钮 → 加 data-probe-id + type
  - 每个有联动关系的控件 → 加 linkage-target + linkage-type
  - 每个页面根容器 → 加 data-probe-page + page-state + ready-when
```

### 7.2 已有项目自动注入

`/instrument` 命令：扫描已有前端项目 → 识别 UI 组件 → 自动添加标注：

```
LLM 读每个页面/组件源文件 → 识别关键控件 → 添加 data-probe-* 属性
优先级：数据容器 > 选择器 > 表单 > 显示绑定
```

### 7.3 标注验证

收集器启动时自动验证标注完整性：

```
warnings:
  - "order-list has data-probe-id but no data-probe-source — 无法追踪数据来源"
  - "page order-management has no data-probe-page-ready-when — 无法判断页面就绪"
  - "province-select has linkage-target but target city-select has no data-probe-id — 联动不可观测"
```

## 8. 与 myskills 的关系

UI Probe 是**独立项目**，myskills 插件通过以下方式集成：

```
独立项目：
  @allforai/ui-probe        ← 收集器 + 查询 API
  @allforai/ui-probe-cli    ← /instrument 命令行工具

myskills 集成点：
  dev-forge /task-execute    → 生成代码时自动带 data-probe-* 标注
  testforge Phase 4          → 生成测试时用 probe API 替代 DOM 查询
  cr-visual step-*           → 用 probe API 替代截图猜测
  code-replicate Phase 2     → 逆向时提取源 App 的 probe 标注（如有）
```

## 9. 效果预期

| 指标 | 黑盒（现在） | 白盒可观测（目标） |
|------|------------|-------------------|
| 数据完整性检查准确率 | ~80%（LLM 看图） | ~99%（直接查询状态） |
| 联动验证准确率 | ~70%（固定等待+截图） | ~99%（事件驱动+状态 diff） |
| 单页面验证耗时 | 10-30s（截图+LLM 分析） | 1-3s（直接查询） |
| 60 页面完整验收 | 2+ 小时 | 15-30 分钟 |
| 时序不稳定导致的误判 | 高（固定 wait） | 极低（事件驱动 wait） |
| 异步接缝测试深度 | 表面（看到 loading 了吗） | 内部（state=submitting, disabled=true, source=pending） |

## 10. 实施路线

```
Phase 1: 核心收集器（Web）
  - data-probe-* 标注规范定稿
  - JS 收集器（query/waitForState/waitForPageReady/snapshot）
  - Playwright 集成示例

Phase 2: 联动 + 网络关联
  - verifyLinkage API
  - fetch/XHR 拦截 + data-probe-source 关联
  - WebSocket/SSE 事件追踪

Phase 3: 自动标注工具
  - /instrument CLI（扫描已有项目 → 自动加标注）
  - 标注完整性验证器

Phase 4: myskills 集成
  - testforge 测试生成模板适配 probe API
  - cr-visual step-data-integrity 用 probe 替代截图
  - dev-forge 代码生成自动带标注

Phase 5: 移动原生适配器
  - Flutter Driver 适配器
  - SwiftUI/XCUITest 适配器
  - Jetpack Compose 适配器
```
