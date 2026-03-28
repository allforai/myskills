---
name: demo-verify
description: >
  Use when the user asks to "verify demo data", "check demo quality",
  "demo-verify", "验证演示数据", "检查演示效果", "demo check",
  or mentions demo verification, visual verification, demo quality check.
  Requires forge-data.json and a running application.
version: "1.1.0"
---

# Demo Verify — 演示验证与问题路由

> 数据结构正确不等于视觉正确。打开产品，逐项确认。

## 目标

以 Playwright 为自动化工具，逐项验证演示数据在真实产品中的**功能正确性 + 视觉正确性**：

1. **能登录** — 每个角色账号都能正常登入并看到权限内的数据
2. **有数据** — 列表页有记录、详情页字段完整、报表数字非零
3. **看得到** — 图片加载正常、视频可播放、无占位符残留
4. **算得对** — Dashboard 汇总与明细一致、趋势图有多月数据
5. **不崩溃** — 终态记录可查看、边界数据不报错
6. **零外链** — DOM 中无外部媒体 URL（media-forge 铁律的最终校验）
7. **全活性** — 每个界面每个按钮都有数据可操作，每种状态都有记录可展示，数据流因果链不断裂
8. **问题路由** — 结构化问题清单，按类型路由回对应阶段或 dev-forge

---

## 定位

```
demo-forge 内部三阶段:
  demo-design  →  media-forge + demo-execute  →  demo-verify（本技能）
  规划该生成什么数据    采集素材 + 灌入数据           打开产品逐项验证
  纯设计不执行         消费设计方案                  产出问题清单路由回修
```

---

## 前提

| 条件 | 说明 |
|------|------|
| forge-data.json 存在 | 数据已灌入，`.allforai/demo-forge/forge-data.json` |
| 应用正在运行且可访问 | 能通过浏览器打开的 URL |
| Playwright MCP 可用 | `mcp__playwright__*` 或 `mcp__plugin_playwright_playwright__*` 系列工具已就绪（任一前缀可用即可） |

如前提不满足，提示用户先运行 `demo-execute` 灌入数据、启动应用、或安装 Playwright MCP。

---

## 快速开始

```
/demo-forge verify              # 全部验证（V1-V7）
/demo-forge verify --round 1    # 仅验证上轮修复项（回归验证）
```

---

## 工作流

### V0: 全界面穷举扫描

> **验证必须穷举所有客户端界面，不能抽样。** 这是发现空页面和渲染崩溃的第一道防线。

**目标**: 自主发现应用的所有界面，逐个验证是否有数据、是否能正常渲染。不依赖预定义的页面列表。

**执行方式**: `subagent` — 主流程 dispatch subagent 做穷举扫描，自身准备 V1-V7 的验证计划。subagent 返回界面清单和状态后，主流程据此决定后续验证重点和问题路由。

**subagent 任务描述**:
> 打开应用，发现所有用户可达的界面。对每个界面判断：有数据 / 空页面 / 渲染崩溃 / 配置表单页。
> 返回完整界面清单及每个界面的状态。

**subagent 输入**: 应用 URL + 登录凭据 + `page-entity-mapping.json`（若存在）
**subagent 输出**: 界面扫描结果 JSON（界面名、状态、问题描述）

**subagent 内部步骤**:

1. 打开应用首页，读取页面结构（snapshot / 截图）
2. 从当前页面中提取所有导航入口（LLM 自行理解导航结构——侧边栏、顶栏、标签页、底部导航、菜单等，不硬编码选择器）
3. 对每个导航入口，访问并读取页面内容
4. LLM 判断每个页面的状态：

| 状态 | 判断依据 | 处理 |
|------|---------|------|
| **有数据** | 列表有行、表格有记录、统计非零、内容区域有实质内容 | PASS |
| **空页面** | "No data"、"not found"、空表格、全零统计、空列表 | route_to=execute |
| **渲染崩溃** | 报错信息、空白主区域、控制台 Error、加载卡住 | route_to=dev_task |
| **配置/表单页** | 页面本身是输入表单，不需要预填数据 | SKIP |

5. 若发现子导航（二级菜单、Tab 切换等），递归检查
6. 若 `page-entity-mapping.json` 存在，交叉验证：mapping 说应该有数据的界面是否真的有数据

**主流程收到结果后**：
- 空页面和崩溃页面写入 verify-issues.json
- 输出进度：`V0 界面扫描: {total} 界面, {alive} 有数据, {empty} 空页面, {crash} 崩溃`

**关键原则**：
- **穷举不抽样** — 导航中每一个可点击的入口都必须访问
- **平台无关** — 不限定 web/mobile/desktop，LLM 根据应用类型选择验证方式
- **空页面是灌入未完成** — 除表单页外，任何数据展示页面为空都视为 execute 阶段遗漏

---

### V1: 登录验证

**目标**: 确认所有角色账号都能登录并看到正确权限数据。

**步骤**:

1. 读取 `demo-plan.json` 中的 credentials 段，获取所有角色账号
2. 对每个角色账号执行:
   - `browser_navigate` 到登录页
   - `browser_fill_form` 填入用户名/邮箱 + 密码
   - `browser_click` 提交登录
   - `browser_wait_for` 等待跳转完成
   - 验证跳转到正确的 Dashboard/首页
   - `browser_snapshot` 检查: 角色专属数据可见、权限正确（不该看到的菜单没出现）
   - `browser_take_screenshot` 保存: `screenshots/v1-round{N}-{role}.png`

**通过标准**: 所有角色都能登录，且看到的数据与其权限一致。

---

### V2: 列表页验证

**目标**: 确认列表页有数据、排序正确、图片加载正常、无占位文本。

**步骤**:

1. 对每个角色的主要列表视图:
   - `browser_navigate` 到列表页
   - `browser_snapshot` 读取 DOM，检查:

   | 检查项 | 方法 | 通过标准 |
   |--------|------|---------|
   | 记录数 > 0 | 列表行/卡片计数 | 页面不为空 |
   | 排序正确 | 读取时间/ID 字段 | 最新在前（descending） |
   | 分页可用 | 查找分页组件 | 数据量足够时分页存在 |
   | 图片加载 | `browser_evaluate`: 检查 `img.naturalWidth > 0 && img.complete` | 无 broken image |
   | 无占位文本 | 全文扫描 | 不含 "Lorem ipsum"、"test"、"TODO"、"undefined"、"null"、"placeholder" |

   - `browser_take_screenshot` 保存: `screenshots/v2-round{N}-{list_name}.png`

**Playwright 技巧**:
- `browser_evaluate` 执行 JS 检查图片: `document.querySelectorAll('img').forEach(img => { if (img.naturalWidth === 0 || !img.complete) report.push(img.src) })`
- `browser_evaluate` 扫描文本: 遍历 `document.body.innerText` 匹配占位符正则

---

### V3: 详情页验证

**目标**: 确认详情页字段完整、关联数据正确、媒体加载正常。

**步骤**:

1. 每种实体类型抽样 N 条记录（N = min(3, 该实体总数)）
2. 对每条记录:
   - `browser_navigate` 到详情页
   - `browser_snapshot` 检查:

   | 检查项 | 方法 | 通过标准 |
   |--------|------|---------|
   | 字段完整 | 遍历可见字段区域 | 无空值/null/undefined/"—" 占位 |
   | 关联数据 | 检查子实体列表 | 子列表有记录（如订单有明细行） |
   | 状态历史 | 查找状态流转区域 | 有操作记录（创建/审核/完成等） |
   | 媒体加载 | 检查 img/video 元素 | 图片显示、视频有有效 src |

   - `browser_take_screenshot` 保存: `screenshots/v3-round{N}-{entity}-{id}.png`

---

### V4: Dashboard / 报表验证

**目标**: 确认 Dashboard 数字非零、趋势图有多月数据、汇总与明细一致。

**步骤**:

1. 导航到每个 Dashboard / 报表页面:
   - `browser_snapshot` + `browser_evaluate` 检查:

   | 检查项 | 方法 | 通过标准 |
   |--------|------|---------|
   | 数字非零 | 读取统计卡片文本 | 主要指标 > 0 |
   | 趋势图多月 | 检查图表数据点 | >= 3 个月数据 |
   | 汇总一致 | 对比 Dashboard 汇总 vs 列表明细 | 汇总 = 明细之和（允许 1% 误差） |
   | 图表渲染 | 检查 canvas/svg 元素 | 非空白/非零高度 |

   - `browser_take_screenshot` 保存: `screenshots/v4-round{N}-{dashboard}.png`

**汇总一致性检查方法**: 从 Dashboard 读汇总数字，再导航到对应列表页累计明细，两者比对。若差异 > 1% 标记为 data_integrity 问题。

---

### V5: 异常场景验证

**目标**: 确认终态记录、搜索功能、边界数据不出错。

**步骤**:

1. **终态记录**: 导航到状态为 CLOSED / REJECTED / CANCELED 的记录详情页
   - 检查: 页面正常渲染、不报错、字段完整

2. **搜索/筛选**: 在列表页执行搜索
   - `browser_fill_form` 输入关键词（从 forge-data.json 取已知存在的值）
   - 检查: 搜索结果非空、结果与关键词匹配

3. **边界数据**:
   - 超长文本记录: 检查无溢出/截断导致的布局崩坏
   - 零金额记录: 检查显示正确（"0.00" 而非空或 NaN）
   - `browser_take_screenshot` 保存边界 case 截图

---

### V6: 媒体完整性验证（重点）

**目标**: 这是最关键的检查——确认产品中零外链、零 broken、零占位符。外部 URL 意味着 media-forge 铁律被违反。

**步骤**:

1. 对每个包含媒体的页面，执行 `browser_evaluate` 扫描所有媒体元素:

```javascript
// 扫描脚本（由 Playwright evaluate 执行）
const appBaseUrl = window.location.origin;
const issues = [];

// 检查所有图片
document.querySelectorAll('img[src]').forEach((img, i) => {
  const src = img.src;
  // Broken image
  if (img.naturalWidth === 0 || !img.complete) {
    issues.push({ type: 'broken_image', src, index: i });
  }
  // 外部 URL
  if (src.startsWith('http') && !src.startsWith(appBaseUrl)) {
    issues.push({ type: 'external_url', src, index: i });
  }
  // 占位符模式
  if (/placeholder|data:image\/svg|picsum|via\.placeholder|placehold/i.test(src)) {
    issues.push({ type: 'placeholder', src, index: i });
  }
});

// 检查所有视频
document.querySelectorAll('video[src], video source[src]').forEach((el, i) => {
  const src = el.src || el.getAttribute('src');
  if (!src) issues.push({ type: 'missing_video_src', index: i });
  if (src && src.startsWith('http') && !src.startsWith(appBaseUrl)) {
    issues.push({ type: 'external_video_url', src, index: i });
  }
});

// 检查视频可播放性
document.querySelectorAll('video').forEach((video, i) => {
  if (video.readyState === 0) {
    issues.push({ type: 'video_not_ready', src: video.src, index: i });
  }
});

// 检查同列表重复图片
const imgSrcs = [...document.querySelectorAll('img[src]')].map(i => i.src);
const duplicates = imgSrcs.filter((s, i) => imgSrcs.indexOf(s) !== i);
if (duplicates.length > 0) {
  issues.push({ type: 'duplicate_images', srcs: [...new Set(duplicates)] });
}

return issues;
```

2. 逐项检查清单:

   | 检查项 | 严重程度 | 说明 |
   |--------|---------|------|
   | Broken image (naturalWidth === 0 或 complete === false) | high | 图片 404 或加载失败 |
   | 外部 URL (src 不匹配 app base URL) | high | media-forge 铁律违反 |
   | 占位符模式 (placeholder / picsum / data:image/svg) | high | 禁止占位符 |
   | 宽高比异常 (width/height 偏差 > 20%) | medium | 严重拉伸/压缩 |
   | 视频无法播放 (readyState === 0) | high | 视频源无效 |
   | 同列表重复图片 (相同 src 出现多次) | medium | 数据多样性不足 |

3. 对所有标记项 `browser_take_screenshot` 截图存证

**注意**: 此步骤发现的问题全部归类为 `media` category，route_to="media"，由 media-forge 重入处理。

---

### V7: UI 活性 + 数据闭环验证

**目标**: 从设计产物反向验证——experience-map 定义的每个 screen/action 是否都有数据支撑，让演示时每个界面都"活"着。

#### V7-A: UI 活性保障 (UI Liveness Guarantee)

**基准**: experience-map.json（必须）+ seed-plan.json / demo-plan.json

**验证规则**（逐 screen 逐 action Playwright 检查）:

| UI 元素类型 | 最低数据保障 | 检查方法 |
|------------|------------|---------|
| 列表页 | ≥ 2 条记录（能看到排序效果） | `browser_evaluate` 计数列表行/卡片 |
| 详情页 | ≥ 1 条完整字段记录 | 检查无 null/undefined/空值/"—" 占位 |
| 操作按钮 | ≥ 1 条可操作的目标数据 | 按钮非 disabled 且有目标记录 |
| 搜索/筛选 | ≥ 2 条可区分记录 | 搜索后结果变化（非全量返回） |
| 状态标签/徽章 | 每种状态至少 1 条 | 对照 `task.outputs.states` 逐状态验证 |
| Dashboard/图表 | ≥ 1 个月跨度数据 | 图表渲染非空、数字非零 |
| 空态页面 | 专门验证 empty state | 无数据时 empty state 正确展示（而非空白/报错） |

**逆向验证链**:
```
experience-map.screen.actions[]
  → 每个 action 需要什么前置数据？（如"审批"按钮需 PENDING 记录）
  → demo-plan.json 是否规划了该数据？
  → 运行时该数据是否真正存在？
```

**活性评分**: `有数据支撑的 action 数 / screen 总 action 数`
- ≥ 90% → PASS
- 70-89% → WARNING（部分演示受限）
- < 70% → FAIL（严重影响演示效果）

活性不足的 screen → route_to = "design"（补充 demo-plan 数据链路）

#### V7-B: 状态全覆盖验证 (State Coverage for Demo)

**目标**: 演示数据必须覆盖 task.outputs.states 的所有枚举值，否则演示时无法展示完整业务生命周期。

**基准**: task-inventory.json 中每个实体的 `outputs.states`

**验证矩阵**:
| 实体 | 定义状态 | 列表页可见 | 详情页可访问 | 状态标签正确 |
|------|---------|----------|------------|-----------|
| Order | PENDING | ✅ 3 条 | ✅ | ✅ |
| Order | PAID | ✅ 5 条 | ✅ | ✅ |
| Order | REFUNDED | ❌ 0 条 | — | — |
| Order | CANCELED | ✅ 1 条 | ✅ | ✅ |

**重点检查终态和异常态**（最容易漏）:
- REJECTED / CANCELED / EXPIRED / FAILED / CLOSED — 专门检查
- 终态记录详情页不能报错或空白

缺失状态 → route_to = "design"（demo-plan 补充该状态数据链路）

#### V7-C: 数据流完整性追踪 (Data Flow Integrity)

**目标**: 验证演示数据的业务逻辑链是否连贯——创建→流转→审批→完成的因果链不断裂。

**验证方式**:
1. 从 `demo-plan.json` 提取数据链路定义
2. 对每条链路，逐节点 Playwright 验证:
   - 用户 A 的操作记录 → 是否在用户 B 的待办中出现？
   - 父实体的子实体列表 → 数量和状态是否一致？
   - Dashboard 汇总 → 是否等于明细之和？
3. 链路中任一节点数据断裂 → route_to = "execute"（灌入逻辑问题）

→ 输出进度: 「V7 活性:{rate}% 状态覆盖:{n}/{m} 数据流:{pass}/{total}」

---

### V8: 问题汇总 + 路由

**目标**: 汇总 V1-V7 全部失败项，分类定级，路由到对应阶段。

**步骤**:

1. **汇总**: 收集 V0-V7 所有检查结果
2. **分类**: 对每个失败项判定 category + severity + route_to

**路由规则**:

| 问题类型 | category | route_to | 典型场景 |
|---------|----------|----------|---------|
| V0 空页面（界面无数据） | empty_page | execute | 界面存在但无数据可展示 |
| V0 渲染崩溃（界面报错） | code_bug | dev_task | 界面有数据但渲染失败 |
| 数据缺失、枚举未覆盖、链路不完整 | coverage | design | 实体 0 条记录，缺 REJECTED 状态 |
| 图片 broken、视频不播放、外链残留、占位图 | media | media | 404、拉伸、灰块 |
| 外键断裂、灌入失败 | data_integrity | execute | 关联数据缺失、链路断裂 |
| 派生字段不一致 | data_integrity | dev_task | Dashboard 汇总 != 明细之和（BIZ_BUG，API 业务逻辑问题） |
| API 500、前端渲染 bug、SQL 错误、代码崩溃 | code_bug | dev_task | 应用代码 bug，非数据问题 |
| UI 活性不足（列表空、按钮无目标、状态缺失） | liveness | design | screen action 无数据支撑 |
| 数据流断裂（因果链不连贯、关联数据缺失） | data_flow | execute | 父实体有子列表为空 |
| 纯样式偏好、与数据无关的 UI 微调 | style_preference | skip | 记录但不路由 |

3. **6V 深度诊断**（针对 `code_bug` 和 `data_integrity` 类问题）:
   - 对每个 high severity 的 `code_bug` / `data_integrity` 问题，用 LLM 从 6 个工程视角诊断根因：
     - **V1 Contract**: API 签名/响应格式是否偏离了 `api-contracts.json`
     - **V2 Conformance**: 数据是否违背了 `entity-model.json` 的约束（类型/外键/唯一性）
     - **V3 Correctness**: 业务逻辑是否正确（如金额计算、状态流转规则）
     - **V4 Consistency**: 同类操作在不同页面/角色下行为是否一致
     - **V5 Capability**: 是否因数据量/并发触发了性能瓶颈
     - **V6 Context**: 错误是否与特定用户角色/场景相关（权限/数据隔离问题）
   - 诊断结果写入 issue 的 `diagnosis` 字段：`{ "viewpoint": "V2", "root_cause": "...", "fix_hint": "..." }`
   - 这使得 dev_task 回流给 dev-forge 时携带精准修复线索，而非仅凭表面现象分类

4. **输出**: 写入 verify-report.json（全量）+ verify-issues.json（失败项 + 路由 + 6V 诊断）

---

## verify-report.json 结构

```json
{
  "round": 1,
  "timestamp": "ISO8601",
  "app_url": "http://localhost:3000",
  "checks": {
    "v1_login": {
      "status": "passed | partial | failed",
      "roles_checked": [
        {
          "role": "admin",
          "login_success": true,
          "correct_permissions": true,
          "screenshot": "screenshots/v1-round1-admin.png"
        }
      ]
    },
    "v2_list_pages": {
      "status": "passed | partial | failed",
      "pages_checked": [
        {
          "page": "/orders",
          "has_data": true,
          "record_count": 25,
          "sort_correct": true,
          "pagination_ok": true,
          "images_ok": true,
          "no_placeholder_text": true,
          "screenshot": "screenshots/v2-round1-orders.png"
        }
      ]
    },
    "v3_detail_pages": {
      "status": "passed | partial | failed",
      "entities_checked": [
        {
          "entity": "Order",
          "record_id": "ORD-001",
          "fields_complete": true,
          "related_data_present": true,
          "status_history_visible": true,
          "media_loaded": true,
          "screenshot": "screenshots/v3-round1-order-ORD001.png"
        }
      ]
    },
    "v4_dashboards": {
      "status": "passed | partial | failed",
      "dashboards_checked": [
        {
          "dashboard": "sales-overview",
          "numbers_nonzero": true,
          "trend_months": 6,
          "totals_consistent": true,
          "charts_rendered": true,
          "screenshot": "screenshots/v4-round1-sales-overview.png"
        }
      ]
    },
    "v5_edge_cases": {
      "status": "passed | partial | failed",
      "terminal_states_ok": true,
      "search_works": true,
      "boundary_data_ok": true
    },
    "v6_media_integrity": {
      "status": "passed | partial | failed",
      "pages_scanned": 12,
      "total_media_elements": 156,
      "broken_images": 0,
      "external_urls": 0,
      "placeholders": 0,
      "aspect_ratio_issues": 0,
      "video_issues": 0,
      "duplicate_images": 0
    },
    "v7_data_completeness": {
      "status": "passed | partial | failed",
      "ui_liveness": {
        "screens_checked": 15,
        "alive_screens": 13,
        "liveness_rate": "86.7%",
        "dead_screens": [
          { "screen": "退款审批", "missing_actions": ["审批通过", "审批拒绝"], "reason": "无 PENDING 退款记录" }
        ]
      },
      "state_coverage": {
        "entities_checked": 5,
        "total_states": 18,
        "covered_states": 15,
        "missing_states": [
          { "entity": "Order", "state": "REFUNDED", "impact": "无法演示退款流程" }
        ]
      },
      "data_flow_integrity": {
        "flows_checked": 4,
        "intact_flows": 3,
        "broken_flows": [
          { "flow": "下单→支付→发货", "break_point": "发货节点无物流记录", "route_to": "execute" }
        ]
      }
    }
  },
  "summary": {
    "total_checks": 86,
    "passed": 82,
    "failed": 4,
    "pass_rate": "95.3%"
  }
}
```

---

## verify-issues.json 结构

```json
{
  "round": 1,
  "timestamp": "ISO8601",
  "summary": {
    "total_checks": 86,
    "passed": 71,
    "failed": 15,
    "pass_rate": "82.6%"
  },
  "issues": [
    {
      "id": "VI-001",
      "category": "media",
      "severity": "high",
      "check_phase": "V6",
      "description": "Product 封面图外链残留，src 指向 picsum.photos",
      "page_url": "/products/123",
      "evidence": "screenshots/v6-round1-product-123.png",
      "route_to": "media",
      "suggested_fix": "media-forge 补采该产品封面图并通过上传 API 本地化"
    },
    {
      "id": "VI-002",
      "category": "data_integrity",
      "severity": "high",
      "check_phase": "V4",
      "description": "Dashboard 销售总额 (98,500) 与订单明细之和 (102,300) 不一致",
      "page_url": "/dashboard/sales",
      "evidence": "screenshots/v4-round1-sales-overview.png",
      "route_to": "execute",
      "suggested_fix": "派生字段不一致 = BIZ_BUG，路由 dev-forge 修复业务逻辑"
    },
    {
      "id": "VI-003",
      "category": "coverage",
      "severity": "medium",
      "check_phase": "V2",
      "description": "退款记录列表为空，REFUNDED 状态无数据覆盖",
      "page_url": "/refunds",
      "evidence": "screenshots/v2-round1-refunds.png",
      "route_to": "design",
      "suggested_fix": "demo-plan.json 增加退款场景数据链路"
    },
    {
      "id": "VI-004",
      "category": "code_bug",
      "severity": "high",
      "check_phase": "V3",
      "description": "订单详情页加载报 500 错误，API /api/orders/456 返回 Internal Server Error",
      "page_url": "/orders/456",
      "evidence": "screenshots/v3-round1-order-456.png",
      "route_to": "dev_task",
      "suggested_fix": "检查 orders API 的 ID 查询逻辑，可能是字段类型不匹配"
    },
    {
      "id": "VI-005",
      "category": "style_preference",
      "severity": "low",
      "check_phase": "V2",
      "description": "列表页卡片间距略大，视觉上偏空",
      "page_url": "/products",
      "evidence": "screenshots/v2-round1-products.png",
      "route_to": "skip",
      "suggested_fix": "CSS 间距调整，非数据问题"
    }
  ]
}
```

---

## dev_task 回流机制

当 V7 路由结果中存在 `route_to="dev_task"` 的问题时，生成 dev-forge 兼容的修复任务。

**任务格式**:

```markdown
### B-FIX-{N}: {title}

**来源**: demo-verify Round {N}, {issue_id}
**证据**: {screenshot_path}
**描述**: {description}
**验收标准**: {fix description}
```

**回流流程**:

1. 从 verify-issues.json 筛选 `route_to="dev_task"` 的问题
2. 为每个问题生成一条 B-FIX 任务
3. 追加到 `.allforai/project-forge/sub-projects/{name}/tasks.md` 的 B-FIX round
4. verify-issues.json 中该问题标记为 `DEFERRED_TO_DEV`
5. demo-forge 当轮不等待修复，继续处理其他类型问题

**示例**:

```markdown
### B-FIX-1: 订单详情页 API 500 错误

**来源**: demo-verify Round 1, VI-004
**证据**: .allforai/demo-forge/screenshots/v3-round1-order-456.png
**描述**: 订单详情页加载报 500 错误，API /api/orders/456 返回 Internal Server Error
**验收标准**: /api/orders/{id} 对所有已灌入订单 ID 正常返回 200，详情页完整渲染
```

用户修复代码后可运行 `/demo-forge verify` 回归验证。

---

## 截图存储

所有截图统一存放在 `.allforai/demo-forge/screenshots/` 下:

```
.allforai/demo-forge/screenshots/
├── v1-round{N}-{role}.png           # 登录验证
├── v2-round{N}-{list_name}.png      # 列表页验证
├── v3-round{N}-{entity}-{id}.png    # 详情页验证
├── v4-round{N}-{dashboard}.png      # Dashboard 验证
├── v5-round{N}-{scenario}.png       # 异常场景验证
└── v6-round{N}-{page}-{issue}.png   # 媒体完整性验证
```

每轮验证保留独立截图（round 编号递增），方便对比前后轮差异。

---

## 回归验证模式

当指定 `--round N` 时，仅验证上轮 verify-issues.json 中的修复项:

1. 读取上轮 verify-issues.json
2. 过滤掉 `route_to="skip"` 和 `DEFERRED_TO_DEV` 的项
3. 对每个待验证项重新执行对应的 V-check
4. 同时抽样执行全量回归（确保修复没引入新问题）
5. 输出新一轮 verify-report.json + verify-issues.json

---

## 输出文件

| 文件 | 位置 | 说明 |
|------|------|------|
| verify-report.json | `.allforai/demo-forge/verify-report.json` | 全量验证报告（V1-V7 所有检查结果） |
| verify-issues.json | `.allforai/demo-forge/verify-issues.json` | 失败项清单 + 路由目标 |
| screenshots/ | `.allforai/demo-forge/screenshots/` | 验证截图（按步骤+轮次命名） |
