---
name: cr-frontend
description: >
  Use when user wants to "replicate frontend", "component rewrite", "前端复刻",
  "React迁移", "Vue迁移", "Flutter迁移", "React Native迁移", "clone UI",
  "port frontend to", "migrate frontend", "rewrite client app", "组件复刻",
  "UI 复刻", "移动端复刻", or mentions converting existing frontend/mobile
  code to a different framework while preserving behavior.
version: "1.0.0"
---

# CR Frontend — 前端复刻

> 先加载协议基础: `${CLAUDE_PLUGIN_ROOT}/skills/code-replicate-core.md`

> **Phase 委托**：本技能覆盖 Phase 2/4/6 前端特有部分。Phase 1/3/5/7 由 core 协议处理。

前端专用逆向分析：组件树、路由结构、状态管理、API 调用层、UI 状态机、移动端导航。

---

## 项目类型检测表

Phase 2 完成技术栈识别后，确认项目属于以下类型之一：

| 类型 | 检测特征 | 分析重心 |
|------|---------|---------|
| **前端 Web** | `components/`、`pages/`、`store/`、`hooks/`、`src/app/`（Next.js）、路由配置文件 | 组件树、页面路由、状态管理、API 调用层 |
| **前端移动** | `screens/`、`widgets/`、`navigation/`、`pubspec.yaml`（Flutter）、`android/ios/` 目录 | 导航结构、状态管理、原生模块调用、平台差异 |

**混合单体检测**：若发现后端代码（`routes/`、`controllers/`、`middleware/`、`services/`、ORM 配置）→ 输出提示：

```markdown
### 检测到混合单体项目

后端部分: {path}（{backend_stack}）
建议：对后端部分单独运行 `/code-replicate --type backend` 分析。
```

---

## Phase 2：源码解构（前端版，自动执行，不停顿）

### 1a. 技术栈识别

扫描以下文件识别技术栈（优先顺序：依赖文件 > 目录结构 > 文件扩展名）：

| 文件 | 技术栈 |
|------|--------|
| `package.json` | 框架从 dependencies 推断（React/Vue/Angular/Svelte/Next.js/Nuxt） |
| `next.config.*` / `nuxt.config.*` | Next.js / Nuxt.js（SSR 框架） |
| `vite.config.*` / `webpack.config.*` | 构建工具 |
| `tsconfig.json` | TypeScript（版本和配置） |
| `pubspec.yaml` | Dart/Flutter |
| `react-native.config.js` / `app.json`（含 expo） | React Native |
| `angular.json` | Angular |

记录到 `source_analysis.json` 的 `source_stack` 字段，附证据 `[CONFIRMED:file]`。

### 1b. 模块树提取

扫描目录结构，识别前端典型模块模式：

```
pages/ | views/ | screens/ | app/    → 页面/视图层
components/ | widgets/ | ui/         → 组件层
hooks/ | composables/ | utils/       → 逻辑复用层
store/ | stores/ | state/ | redux/   → 状态管理层
services/ | api/ | lib/              → API 调用层
layouts/ | templates/                → 布局层
assets/ | styles/ | public/          → 静态资源层
navigation/ | router/                → 路由/导航层
```

对每个模块生成条目（含 id, name, path, inferred_responsibility, confidence, evidence, key_files 字段）。模块职责无法确定时：标注 `"confidence": "low"` + `[INFERRED]`，加入歧义 log，**不停下询问**。

> 模块条目格式详见 `${CLAUDE_PLUGIN_ROOT}/docs/schema-reference.md`（模块树条目）

### 1c. 代码规模评估

统计：总文件数、代码行数（估算）、页面/路由数量（估算）、组件数量。

写入 `.allforai/code-replicate/source-analysis.json`，输出进度「Phase 2 ✓ {N} 模块 | {N}± 页面 | {N}± 组件 | {source_stack} | 类型: 前端」。

**下一步**：进入 Phase 3 目标确认（见 core 协议）— 展示源码全貌，让用户确认复刻范围、目标技术栈、业务方向，确认后自动继续 Phase 4。

---

## Phase 4：信度专项分析 — 前端 Web 项目

按信度等级叠加执行（每个模式包含上一级全部内容）。所有歧义收集到内部 `ambiguity_log`，不停下询问。

### 粒度适配

根据 Phase 3 确定的 `analysis_granularity`（scope=full 时按代码规模自动判定）：
- **fine**：逐个组件/页面完整分析（4D + 6V），逐个状态流追踪完整交互路径
- **standard**：逐个组件/页面分析，高风险项完整 6V，普通项省略 business/risk 视角
- **coarse**：按页面聚合，仅核心交互流做完整分析，其余提取 Props 签名 + 路由 + 关键状态（省略细粒度 UI 状态机）

### 所有模式：组件与 API 合约分析 → `api-contracts.json`

> 前端"接口"有双重含义 — 组件 Props 接口（内部契约）和后端 API 调用（外部依赖）。两者都需要分析。

对每个页面/组件提取条目：

**组件 Props 接口**（内部契约）：
- component_id, name, source_file, source_line
- props 定义（类型、是否必填、默认值）
- slots/children 模式
- emits/callbacks

**API 调用点**（外部依赖）：
- 每个 API 调用点（service/hook 层）
- endpoint, method, request params, response shape
- 调用时机（mount/click/submit/polling）

若 Props 类型定义与实际使用不一致 → 标注 `[CONFLICT]`，加入 ambiguity_log，**不停下**。

> 完整端点 JSON 示例详见 `${CLAUDE_PLUGIN_ROOT}/docs/schema-reference.md`（api-contracts.json）

---

### functional 模式加：行为规格分析 → `behavior-specs.json`

对前端行为提取以下维度：

| 维度 | 分析内容 |
|------|---------|
| **路由结构** | 所有路由路径、路由守卫、懒加载边界、动态路由参数 |
| **状态管理** | Store 结构、action 类型、selector 模式、状态持久化 |
| **UI 状态机** | Modal/Loading/Error/Empty 状态、状态转换触发条件 |
| **表单流程** | 验证规则、提交流程、错误回显、多步表单状态 |
| **实时更新** | WebSocket/SSE 订阅、轮询策略、乐观更新 |

无测试覆盖的行为 → 标注 `[UNTESTED]`，加入 ambiguity_log，继续。

> 完整行为 JSON 示例详见 `${CLAUDE_PLUGIN_ROOT}/docs/schema-reference.md`（behavior-specs.json）

---

### architecture 模式加：架构地图 → `arch-map.json`

提取：
- **组件层级树**：页面 → 区域组件 → 原子组件，含 Props 依赖
- **路由架构**：嵌套路由、layout 共享、守卫链
- **状态架构**：全局 store vs 局部 state、数据流方向
- **依赖关系**：组件间引用、shared hooks/utils

发现架构歧义 → 若 `ambiguity_policy = strict` 且影响架构走向 → 即时停下询问；否则标注加入 log 继续。

> 完整架构地图 JSON 示例详见 `${CLAUDE_PLUGIN_ROOT}/docs/schema-reference.md`（arch-map.json）

---

### exact 模式加：Bug 注册表 → `bug-registry.json`

逐一记录发现的 bug。

**前端典型 bug 类型**（重点扫描）：
- 状态泄漏（组件卸载后仍更新 state）
- Stale closures（useEffect/useCallback 依赖遗漏）
- 异步渲染竞态（多次请求只取最后一次）
- 内存泄漏（未清理的 subscription/timer）
- SSR 水合不匹配（hydration mismatch）
- 无障碍问题（缺失 ARIA 属性、键盘导航断裂）

若 `bug_replicate_default = ask` → 将每个 bug 的决策加入 Phase 5 的"待确认列表"，不即时停下。

> 完整 bug 条目 JSON 示例详见 `${CLAUDE_PLUGIN_ROOT}/docs/schema-reference.md`（bug-registry.json）

---

## Phase 4（移动项目）：移动端专项分析

若 Phase 2 检测到前端移动类型，Phase 4 额外关注：

| 维度 | 分析内容 | 对应产物 |
|------|---------|---------|
| **导航结构** | 页面栈、Tab 切换、深链接路由、Modal 导航 | `arch-map.json` 导航层 |
| **平台差异代码** | `Platform.isIOS`、`dart:io`、条件编译 → 标注为跨栈映射决策点 | `behavior-specs.json` |
| **原生模块调用** | 相机、定位、推送、生物识别、文件系统 → 加入 Phase 5 映射决策 | `api-contracts.json` 原生依赖 |
| **状态持久化** | SharedPreferences/Hive/AsyncStorage/MMKV → 目标平台等价物 | `behavior-specs.json` |
| **动画系统** | 手势驱动动画、页面转场、共享元素过渡 | `behavior-specs.json` |

---

### Phase 4 完成

写入所有 JSON 文件，更新 `replicate-config.json`。

#### Phase 4 产物自检（写入后、继续前执行）

对已写入的产物执行四项一致性校验，结果写入 `source-analysis.json` 顶层 `self_check` 字段：

**① 组件覆盖率**
- 比对 `api-contracts.json` 实际组件数 vs Phase 2 组件扫描估算数（`source-analysis.json` 中记录的组件数量）
- 偏差 >20% → 状态 `warn`，写入 `self_check.component_coverage`

**② 页面覆盖率**
- 比对已分析页面数 vs Phase 2 路由/页面估算数（`source-analysis.json` 中记录的页面数量）
- 偏差 >20% → 状态 `warn`，写入 `self_check.page_coverage`

**③ 模块覆盖率**
- 检查 `scope_filter.included_modules` 中每个模块是否在 `api-contracts.json` 或 `behavior-specs.json` 中有至少 1 个条目
- 零产出模块 → 状态 `warn`，对该模块**重新执行 Phase 4 分析**（仅该模块），追加到现有产物中

**④ 高风险 6V 完整性**
- 筛选所有 `risk_level: high` 或 `risk.severity: high|critical` 的组件/行为
- 检查其 `viewpoints` 是否包含全部 6 个视角（user, business, tech, ux, data, risk）
- 缺失视角 → 自动补全（标注 `[SELF_CHECK:补全]`），状态 `补全`

**自检结果写入格式**（`source-analysis.json` 顶层）：

```json
{
  "self_check": {
    "component_coverage": { "expected": 80, "actual": 75, "ratio": 0.94, "status": "pass|warn" },
    "page_coverage": { "expected": 20, "actual": 18, "ratio": 0.90, "status": "pass|warn" },
    "module_coverage": { "included": 6, "with_output": 6, "zero_output": [], "status": "pass|warn" },
    "high_risk_6v": { "total_high_risk": 8, "complete_6v": 7, "补全": 1, "status": "pass|补全" },
    "checked_at": "ISO8601"
  }
}
```

**输出格式**：

- 全部通过：`Phase 4 自检 ✓ 组件覆盖 {ratio}% | 页面覆盖 {ratio}% | 模块 {with_output}/{included} | 高风险 6V {complete}/{total}`
- 有警告：`Phase 4 自检 ⚠ 组件覆盖 {ratio}%（预期 {expected}，实际 {actual}，偏差 >20%）| 页面覆盖 {ratio}% | 模块 {with_output}/{included}（{module} 零产出，回补中...）| 高风险 6V {complete}/{total}（{N} 项已补全）`

自检完成后，自动继续 Phase 4 XV（或 Phase 5）。

---

## Phase 6：生成 allforai 产物（前端专有部分）

> 6a/6e/6f 由 core 统一生成，以下为前端特有产物。
> **注意路径**：6b/6d 写到 `.allforai/product-map/`，6c 写到 `.allforai/use-case/`，不是 `.allforai/code-replicate/`。

### 6b. `.allforai/product-map/business-flows.json`（functional+ 模式）

从用户交互流提取，转换为 product-map 兼容格式（与 `/product-map` 产出结构一致）。

重点：
- 用户操作流（点击/输入/导航 → 状态变化 → UI 更新）
- 表单提交流（填写 → 验证 → 提交 → 反馈）
- 数据加载流（进入页面 → 请求 → Loading → 成功/失败）

### 6c. `.allforai/use-case/use-case-tree.json`（functional+ 模式）

从 UI 行为生成用例树，格式兼容 product-design `use-case/` 目录。

前端用例来源：
- 每个页面/路由 → 一组用例
- 用户交互（按钮点击、表单提交、搜索）→ 用例的主流
- UI 状态切换（Empty/Loading/Error/Success）→ 备选流
- 路由守卫拦截 → 异常流

### 6d. `.allforai/product-map/constraints.json`（exact 模式）

将 `bug-registry.json` 中 `replicate_decision: "replicate"` 的 bug 转为约束（含 constraint_id, source_bug, description, enforcement, affects）。
