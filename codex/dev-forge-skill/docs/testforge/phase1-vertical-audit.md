## Phase 1：纵向审计 — tests ↔ 上游基准

> "每个该测的点，有测试守护吗？"

**跨子项目并行**：各子项目的审计互相独立，使用 execute in parallel。

### 验证基准链（从浅到深）

**Layer 0: tests ↔ 源代码**（始终执行）

对每个子项目的每个可测试源文件：

1. **覆盖映射**：将已有测试文件与源文件配对（按项目实际的测试目录结构匹配）
2. **标记状态**：
   - `COVERED` — 有对应测试文件且测试函数 ≥ 1，且源文件有实质逻辑
   - `PARTIAL` — 有测试文件但覆盖不足（分支覆盖 < 50%）
   - `UNCOVERED` — 无对应测试文件
   - `TRIVIAL` — 文件太简单不需要测试（纯类型定义、常量、re-export）
   - `HOLLOW` — 源文件本身是空壳实现。LLM 读代码后判断："如果用户真的使用这个功能，能得到有价值的结果吗？"不能 → HOLLOW。不要靠匹配 `TODO`/`() {}`等模式判断——要理解代码意图。即使有测试文件也标为 HOLLOW——测试覆盖空壳代码没有价值。HOLLOW 文件应优先作为 Phase 4 的修复目标而非测试目标
3. **分支分析**：对 COVERED 和 PARTIAL 文件，LLM 读源码提取：
   - if/switch/ternary 分支 → 测试覆盖了哪些分支？
   - error return / catch / throw → 错误路径有测试吗？
   - 边界条件（空值、零值、极值）→ 有边界测试吗？
4. **测试类型标注**：对每个缺口标注应在金字塔哪层测试：

```
test_type 分类逻辑（通用规则，不特化任何框架）：
├── unit        — 纯函数、工具函数、验证逻辑、状态管理、服务层、数据模型
├── component   — UI 组件渲染 + 用户交互 + 事件触发（含 Flutter widget test，主机运行无需设备）
├── integration — 多模块协作（API client + 状态管理 + 组件联动）
├── e2e_chain   — 跨 ≥2 个子项目的业务流（需要浏览器自动化或 API 串联）
└── platform_ui — 跨平台 UI 自动化测试（同一场景在每个可用平台各跑一遍）
                  Flutter/RN widget test 不属于此类（它们在主机运行，归入 component）
                  此类仅限需要真实平台环境的 UI 自动化：浏览器、模拟器、真机
```

**Layer 1: tests ↔ design.md**（有 design.md 时执行）

LLM 读 design.md / design.json，提取：
- API 端点定义 → 每个端点的正常响应 + 错误码有测试吗？
- 状态机定义 → 每个状态转换有测试覆盖吗？
- 数据模型关联 → 级联操作（删除父记录时子记录？）有测试吗？

**Layer 2: tests ↔ tasks.md**（有 tasks.md 时执行）

LLM 读 tasks.md，对每个 task 提取：
- `exceptions` → 每个异常路径有对应测试？
- `rules` → 每个业务规则有测试验证？
- `_Acceptance_` → 验收条件有对应断言？

**Layer 3: tests ↔ product-map**（有 product-map 时执行）

LLM 读 product-map，提取：
- `business-flows` 的关键节点 → 有测试守护该节点的逻辑？
- `constraints` 中 `enforcement: "hard"` → 有测试穿透验证约束生效？
- `use-case-tree` 的验收用例 → 有对应集成测试？
- **跨子项目业务流** → 有 E2E 链测试覆盖完整流程吗？（无 → 标为 `e2e_chain` 缺口）

若 `experience_priority.mode = consumer | mixed`，还必须追加：
- 首页主线/主 CTA 是否有测试守护？
- loading / empty / error / success / progress 等关键状态是否有测试守护？
- 下一步引导、结果回流、持续关系入口（历史/提醒/通知/进度/最近活动）是否至少有相关测试覆盖？
- 若用户端只测“页面存在”和“按钮可点”，未测成熟度关键节点 → 标记为 UX 维度缺口

### 4D+1 维度聚合

将所有 Layer 的缺口按 4D+1 维度归类：

| 维度 | 审计问题 | 基准来源 |
|------|---------|---------|
| **Data** | 数据操作（CRUD、关联、级联）有测试吗？ | design.md entities + tasks.md |
| **Interface** | API 正常/异常响应有测试吗？参数校验有测试吗？ | design.md endpoints + tasks.md rules |
| **Logic** | 业务规则、状态流转、权限判断有测试吗？ | tasks.md rules/exceptions + constraints |
| **UX** | 组件渲染、交互、错误提示、loading 状态有测试吗？ | experience-map screens/actions |
| **DataBinding** | 数据绑定控件是否有数据完整性测试？ | experience-map screens + design.md endpoints |

**DataBinding 维度**（与 UX 维度互补：UX 检查"控件能渲染能交互"，DataBinding 检查"控件里有没有真实数据"）：

LLM 扫描前端源代码中的数据绑定控件，对每个控件审计：

```
数据容器类（Table / DataGrid / List / Tree / TreeView）:
  → 有测试验证该控件在正常 API 响应下显示 ≥1 行数据吗？
  → 有测试验证该控件在空响应下显示空状态提示（非白屏）吗？

选择器类（ComboBox / Select / Dropdown / RadioGroup）:
  → 有测试验证选项列表从 API/配置加载后非空吗？
  → 有测试验证默认选中值正确吗？

显示绑定类（Label / Badge / Counter / Chip 绑定了变量的）:
  → 有测试验证绑定值在 API 返回后正确显示（非 undefined/null/NaN）吗？

可视化类（Chart / Graph / ProgressBar）:
  → 有测试验证图表在正常数据下有渲染输出吗？
```

缺少上述测试的控件 → 标记为 `DATABINDING_GAP`，`test_type` 根据复杂度标注为 `component`（单控件）或 `platform_ui`（需真实 API）。

**Linkage 子维度**（DataBinding 的延伸：DataBinding 检查"有没有数据"，Linkage 检查"操作 A 后 B 有没有正确变化"）：

LLM 扫描前端源代码中的控件联动关系（onChange/onSelect → setState/dispatch/emit/computed），对每组联动审计：

```
级联选择（select A → select B 选项更新）:
  → 有测试先选 A 再验证 B 的选项列表变化吗？

条件显隐（checkbox/radio → 控件 visible/hidden）:
  → 有测试切换条件后验证目标控件出现/消失吗？

条件启禁（表单状态 → 按钮 disabled/enabled）:
  → 有测试验证在不同表单状态下按钮的 disabled 属性吗？

自动计算（input A × input B → label C）:
  → 有测试修改输入值后验证计算结果正确吗？（不只是"有值"，还要"值对"）

联动筛选（tab/filter → 列表数据变化）:
  → 有测试切换筛选条件后验证列表内容变化吗？

主从联动（list click → detail panel）:
  → 有测试点击不同行后验证详情面板显示对应行数据吗？
```

缺少上述测试的联动对 → 标记为 `LINKAGE_GAP`，`test_type` 根据复杂度标注为 `component`（纯前端状态联动）或 `platform_ui`（联动涉及 API 调用）。

**Pagination 子维度**（DataBinding 的延伸：DataBinding 检查"首屏有没有数据"，Pagination 检查"翻页/滚动加载时数据链路是否正确"）：

LLM 扫描前端源代码中的分页/无限滚动控件，对每个分页点审计：

```
分页控件识别（不限框架，按语义理解）：
  - 显式分页：Pagination 组件、页码按钮、"上一页/下一页"
  - 无限滚动：InfiniteScroll、onReachBottom、Intersection Observer、scroll listener + loadMore
  - 游标分页：cursor-based pagination（hasNextPage + endCursor）
  - 加载更多按钮："Load More"、"查看更多"

对每个分页控件审计：

1. 翻页数据正确性：
   → 有测试加载第 2 页后验证数据与第 1 页不重复吗？
   → 有测试验证第 2 页的数据确实是下一批（非第 1 页的副本）吗？

2. 并发翻页安全：
   → 有测试快速连续翻页（page=2 和 page=3 几乎同时请求）后数据顺序正确吗？
   → 有测试翻页中途切换筛选条件 → 分页是否重置为第 1 页吗？

3. 边界状态：
   → 有测试加载到最后一页后"加载更多"按钮消失或禁用吗？
   → 有测试空结果页（筛选后 0 条）的 Empty State 吗？
   → 有测试只有 1 条数据时分页组件是否正确隐藏吗？

4. 翻页 + 排序交互：
   → 有测试切换排序后分页是否重置吗？
   → 有测试排序后第 2 页的数据是否按新排序规则排列吗？

5. 翻页加载态：
   → 有测试翻页时是否显示 loading 指示（skeleton/spinner）吗？
   → 有测试翻页 loading 中是否禁止重复触发吗？（防抖/节流）
```

缺少上述测试的分页点 → 标记为 `PAGINATION_GAP`，`test_type` 标注为 `platform_ui`（需要真实 API 和滚动交互）。

若 `experience_priority.mode = consumer | mixed`，UX 维度还必须覆盖：

- 首页主线与主 CTA
- 核心状态系统（loading/empty/error/success/progress）
- 下一步引导与结果回流
- 持续关系入口（history/reminder/notification/progress/recent activity 等相关项）

### 输出

写入 `.allforai/testforge/testforge-analysis.json`：

```json
{
  "analyzed_at": "ISO8601",
  "sub_projects": [{
    "name": "...",
    "source_files": 120,
    "test_files": 52,
    "file_coverage": { "COVERED": 45, "PARTIAL": 12, "UNCOVERED": 55, "TRIVIAL": 8 },
    "gaps": [
      {
        "id": "TG-001",
        "dimension": "Logic",
        "layer": 0,
        "source_file": "src/services/order.ts",
        "upstream_ref": null,
        "description": "订单服务 — 无测试覆盖",
        "severity": "CRITICAL",
        "test_type": "unit"
      },
      {
        "id": "TG-050",
        "dimension": "Logic",
        "layer": 3,
        "source_file": null,
        "upstream_ref": "business-flows.json#F003",
        "description": "交易闭环业务流 — 无跨端 E2E 链测试",
        "severity": "HIGH",
        "test_type": "e2e_chain"
      }
    ],
    "coverage_by_dimension": {
      "Data": { "covered": 45, "gaps": 12, "rate": "78.9%" },
      "Interface": { "covered": 38, "gaps": 8, "rate": "82.6%" },
      "Logic": { "covered": 30, "gaps": 18, "rate": "62.5%" },
      "UX": { "covered": 25, "gaps": 15, "rate": "62.5%" },
      "DataBinding": { "covered": 18, "gaps": 9, "rate": "66.7%" }
    },
    "control_inventory": [
      {
        "source_file": "src/pages/OrderList.vue",
        "screen": "订单管理",
        "controls": [
          {"control_type": "DataGrid", "control_id": "订单列表", "data_source": "GET /api/orders", "has_test": false},
          {"control_type": "ComboBox", "control_id": "状态筛选", "data_source": "GET /api/order-statuses", "has_test": false}
        ],
        "linkages": [
          {"trigger": "状态筛选.onChange", "target": "订单列表", "effect_type": "data_filter", "data_source": "local_filter | GET /api/orders?status=", "has_test": false}
        ],
        "paginations": [
          {"control_id": "订单列表", "type": "offset", "api": "GET /api/orders?page=&size=", "has_test": false}
        ]
      }
    ]
  }]
}
```

**`control_inventory` 字段**（DataBinding + Linkage 维度的细粒度任务清单）：

Phase 1 审计时，LLM 不只标记"这个文件有 DATABINDING_GAP"，还要**逐控件枚举**：

```
对每个前端页面/组件源文件：
1. 扫描所有数据绑定控件 → 记录 control_type + control_id + data_source + has_test
2. 扫描所有联动关系 → 记录 trigger + target + effect_type + has_test
3. 写入 control_inventory（与 gaps 平行的字段）
```

Phase 4 的 Path C agent 读 `control_inventory` 作为任务清单：
- 逐 control 生成测试（不靠 agent 自己判断"该检查哪些控件"）
- 逐 linkage 生成测试（不靠 agent 自己发现联动关系）
- 每完成一个 control/linkage 的测试 → 更新 has_test → true

**验收**：Phase 4 结束后检查 control_inventory — has_test = false 的项 = 遗漏 → 补执行。

→ 输出进度：「Phase 1 纵向审计 ✓ L0:{a} L1:{b} L2:{c} L3:{d} 缺口（unit:{u} component:{c} integration:{i} platform_ui:{p} e2e:{e}）控件清单：{N} controls + {M} linkages」

---
