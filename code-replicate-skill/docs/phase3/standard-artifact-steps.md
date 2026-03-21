### 标准产物 Step 参考（LLM 选择标准 .allforai/ 产物时使用）

> 以下 Step 3.1-3.6 仅在 extraction-plan.artifacts 包含对应标准产物时执行。
> 非标准项目（游戏/数据管道/CLI 等）的 artifacts 列表不含这些 Step → 跳过。

**Step 3.1** — role-profiles → `cr_merge_roles.py` → `product-map/role-profiles.json`
- LLM 按 extraction-plan.role_sources 读指定文件提取角色
- **LLM 片段必须输出 `audience_type`**（consumer / professional）— 基于角色在源码中的实际行为判断，不依赖名称关键词
- 可选：`operation_profile`（frequency/density/screen_granularity）

**Step 3.1.5** — experience-map stub（仅 frontend/fullstack）→ `cr_merge_screens.py` → `experience-map/experience-map.json`
- LLM 按 extraction-plan.screen_sources 读指定页面文件提取屏幕信息
- **LLM 片段必须输出每个 component 的 `render_as`**（12 值枚举）— 基于组件在页面中的实际用途判断
- **LLM 片段应输出 `layout_type`**（语义化布局名，如 auth_card、priority_queue，不用通用名如 "form"）

**Step 3.1.8** — 素材迁移（仅 frontend/fullstack 且 asset-inventory.json 存在时执行）

LLM 按 extraction-plan.asset_sources 处理每类素材：
- `copy` → 复制文件到目标项目对应目录 + 更新代码中的引用路径（源框架路径 → 目标框架路径）
- `transform` → LLM 读源主题/i18n 文件 → 生成目标框架等价配置（如 Ant Design token → Element Plus CSS Variables）
- `replace` → LLM 按 stack-mapping 转换格式（如 React SVG 组件 → Vue SFC 组件）

**路径映射**由 LLM 根据目标框架惯例决定：
- Next.js `public/` → Vite `public/`（直接映射）
- Next.js `app/*/icon.svg` (import) → Vue `src/assets/icons/` (import)
- 具体映射写入 `asset-migration-map.json` 供 cr-fidelity U7 验证

**Step 3.2** — task-inventory（两轮）→ `cr_merge_tasks.py` → `product-map/task-inventory.json`
- LLM 按 extraction-plan.task_sources 读指定文件提取任务
- 第一轮：骨架（id, title, module, type, role_id, category, protection_level）
- 第二轮：深层字段（acceptance_criteria, api_endpoint, prerequisites — 仅 functional+）
- **LLM 片段必须输出 `protection_level`**（core / defensible / nice_to_have）— 基于源码中该功能的业务重要性判断
- **LLM 片段必须输出结构化 `inputs`/`outputs`** — `inputs: {fields: [], defaults: {}}`，`outputs: {states: [], messages: [], records: [], notifications: []}`

**Step 3.3** — business-flows（functional+）→ `cr_merge_flows.py` → `product-map/business-flows.json`
- LLM 按 extraction-plan.flow_sources 读指定文件追踪完整业务流程
- 每个 flow 引用 task_id 列表（来自 Step 3.2 产物）

**Step 3.4** — use-case-tree + report（functional+）→ `cr_merge_usecases.py` + `cr_gen_usecase_report.py`
- 输出为**扁平 `use_cases` 数组**（v2.5.0+），每条包含显式 role_id、task_id、functional_area_name
- `then` 字段必须是**数组**（不是字符串）
- type 枚举已扩展至 13 种（含 journey_guidance, state_transition 等）
- report 由 gen 脚本从 JSON 自动生成，LLM 不直接写 Markdown

**Step 3.5** — constraints（exact only）→ `cr_merge_constraints.py` → `product-map/constraints.json`
- 标记源码中的硬约束：并发限制、数据一致性要求、外部 API 限流
- 标记已知 bug 和技术债（exact 保真度特有）

**Step 3.5.5** — 测试向量提取 → `test-vectors.json`

LLM 读 infrastructure-profile 中 `cannot_substitute: true` 或 `compatibility: exact` 的组件的源码实现，提取可验证的测试向量。

**向量模型由 LLM 根据 project_archetype 决定**（以下为常见模型，不限定）：

**模型 A — 单步（标准应用/加密/编解码）**：
```json
{"input": "...", "expected_output": "...", "description": "..."}
```

**模型 B — 多步序列（状态机/协议/SDK 调用链）**：
```json
{
  "initial_state": "...",
  "steps": [
    {"input": "...", "expected_state": "...", "expected_output": "..."},
    {"input": "...", "expected_state": "...", "expected_output": "..."}
  ]
}
```

**模型 C — 多角色并发（CRDT/协作/分布式）**：
```json
{
  "initial_state": "...",
  "operations": [
    {"actor": "A", "op": "...", "clock": "..."},
    {"actor": "B", "op": "...", "clock": "..."}
  ],
  "expected_merged_state": "...",
  "property": "LLM 描述该场景验证的形式化属性（如交换律、幂等性）"
}
```

**模型 D — ABI 签名（SDK/Library）**：
```json
{
  "function": "pm_process",
  "signature": {"params": ["pm_context_t*", "const pm_request_t*"], "return": "int"},
  "memory_ownership": {"param_0": "borrowed", "param_1": "borrowed", "return": "value"},
  "call_convention": "cdecl"
}
```

LLM 可以在同一个 test-vectors.json 中混合使用多种模型。

**向量来源**（优先级）：源码单元测试 > 标准测试向量（NIST/RFC） > 源码常量 > LLM 构造

**提取来源**（优先级）：
1. 源码的单元测试中已有的测试数据
2. 源码中的常量/fixture 数据
3. LLM 读懂算法后手动构造的测试向量

**用途**：dev-forge 生成目标代码后，用这些 test vectors 验证目标实现的行为与源码一致。cr-fidelity F8 基础设施还原可直接跑这些 vectors。

**Step 3.6** — 索引 + 汇总 → `cr_gen_indexes.py` + `cr_gen_product_map.py`
- task-index.json：轻量索引供下游按需加载
- flow-index.json：业务流索引
- product-map.json：全局汇总（统计 + 元信息 + **experience_priority**）
- `experience_priority` 从角色 audience_type 和任务分布自动推断 — dev-forge 全链路依赖此字段

**生成顺序有依赖**：role-profiles → task-inventory → business-flows → use-case-tree → constraints。
后续产物引用前序产物的 ID。

**每次 LLM 调用的上下文**：
- source-summary.json（~4-8 KB，常驻全局视角）
- 当前模块源码（~10-30 KB）
- 目标 schema 定义（~2-4 KB，按需加载）
- replicate-config 摘要（~1 KB）

---

