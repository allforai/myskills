# Experience Map — Validation Steps (Step 3 / 3.1 / 3.5 / 3.6 / 4)

> Loaded by the experience-map orchestrator after generation completes.
> Covers: self-review loop, quality refinement, Playwright wireframe validation, pattern scan, and output.

---

### Step 3：LLM 自审验收（loop）

设计完成后，LLM 切换到验收者视角，检查以下规则：

**硬性规则（不通过 → 必须修正）**：

| 验收项 | 规则 | 检查方法 |
|--------|------|---------|
| 任务覆盖率 | 每个 task_id（含 independent_operations 和 orphan_tasks）至少出现在一个 screen 的 `tasks` 中 | 遍历 task-inventory 全部任务，检查未覆盖任务 |
| 屏幕归属 | 每个 screen 至少被一个 operation_line 的某个 node 引用 | 遍历所有 screen，检查是否在某个 node.screens 中 |
| 业务流连续性 | business-flows 中相邻节点对应的界面之间有 flow_context 连接 | 遍历每条流，检查 prev/next 链路 |
| 平台一致性 | consumer 角色的界面全部 mobile-ios，professional 全部 desktop-web | 按角色检查 platform 字段 |
| 界面非空 | 每个 screen 至少有 1 个 action 和 1 个 data_field | 遍历检查 |
| data_fields 格式 | 每个 data_field 必须是 `{name, label, type, input_widget, required}` 对象 | 遍历检查字段类型 |
| node.screens 完整性 | 每个 node.screens 元素必须是完整 screen 对象（含 id/name/platform 等），不能是引用 | 检查 node.screens[0] 是否有 id 和 name 字段 |
| 操作线内去重 | 同一个 operation_line 内不应有重复的 screen_id | 按操作线检查 screen_id 唯一性 |

**上游基线验收（硬性，LLM 判断）**：

> 详见 `./docs/skill-commons.md`「上游基线验收」。

LLM 同时加载 journey-emotion-map.json（情绪基线）和 experience-map.json（当前产出），逐条操作线对照审查：

| 审查视角 | LLM 判断什么 |
|---------|-------------|
| 情绪意图落地 | 每个 emotion_node 的 design_hint 是否在对应 screen 的 `emotion_design` 和 `interaction_pattern` 中有实质性体现？（不是照抄，而是判断设计是否回应了情绪需求） |
| 高风险保护 | risk=high/critical 的节点，对应 screen 的设计是否考虑了防错、确认、可逆性？ |
| 情绪弧线连贯 | 操作线中情绪从 anxious → delighted 的变化，在界面序列中有对应的体验递进吗？还是所有界面千篇一律？ |
| 旅程线完整 | 每条 journey_line 在 experience-map 中有对应的 operation_line |

**不通过 → 与硬性规则同等处理，LLM 修正对应 screen 后重新验收。**

**设计质量规则（硬性，不通过 → 必须修正）**：

| 验收项 | 规则 | 检查方法 |
|--------|------|---------|
| description 深度 | 每个 screen 的 `description` ≥ 40 字，且包含设计意图（不仅仅重复屏幕名称） | 遍历检查字符数，检查是否与 `name` 高度重复 |
| states 业务特定 | 每个 screen 的 `states` 除 4 个基础状态外，至少有 1 个业务特定状态 | 检查 states key 数量 > 4 |
| states 差异化 | 同类屏幕（相同 interaction_type）的 states 不能完全相同 | 按 interaction_type 分组，检查 states values 是否有差异 |
| emotion_design 结构 | 有 `_emotion_ref` 的 screen，`emotion_design` 必须是包含 `source_emotion` 和 `design_response` 的对象 | 检查类型和必填字段 |
| emotion_design 实质性 | `emotion_design.design_response` 必须是可操作的设计指令，不能是"保持简洁"等空泛描述 | LLM 判断是否可操作 |
| layout_type 多样性 | (a) 任何单一 layout_type 占比不超过全部屏幕的 15%（如 80 个屏幕中最多 12 个用同一 layout_type）；(b) layout_type 不能是 interaction_type 的简单复制（如 "form"、"list"、"MG2-L"）；(c) 每个 layout_type 必须是语义化名称，描述业务目的而非交互模式（如 `auth_card`、`priority_queue`、`structured_editor`） | 统计 layout_type 分布，检查占比超限的类型，检查是否与 interaction_type 重名 |
| layout_description 独特性 | 每个 screen 必须有 `layout_description` 字段（1-2 句话描述空间布局），且同一应用内不同 screen 的 layout_description 不能高度重复 | 按应用分组，检查 layout_description 是否存在且是否与其他 screen 的描述相似度 < 70% |
| interaction_type 准确性 | 创建操作不应是 CT2（内容阅读），删除操作不应是 MG1（只读），充值/提现等提交操作不应是 MG1（只读） | 交叉检查 actions 语义与 interaction_type 是否矛盾 |
| components 非空 | 每个 screen 至少 2 个 components，且每个 component 有 type/purpose/behavior/render_as | 遍历检查，render_as 必须在 12 值枚举内（data_table/input_form/key_value/bar_chart/search_filter/action_bar/tab_nav/media_grid/card_grid/tree_view/timeline/text_block） |
| actions 语义匹配 | actions 中不应出现与屏幕无关的操作（如查看页面出现"保存"） | LLM 判断 actions 与 screen 业务场景是否匹配 |

**业务语义校验规则（硬性，不通过 → 必须修正）**：

> 这些规则检查 LLM 设计的业务合理性，防止"结构正确但业务错误"的屏幕通过验收。需要加载 `product-concept.json`（治理风格、角色操作频度）作为校验基准。

| 验收项 | 规则 | 检查方法 |
|--------|------|---------|
| **屏幕内容相似度** | 同一操作线内的屏幕，data_fields + components 的 jaccard 相似度不应 > 60% | 按操作线分组，计算每对屏幕的字段/组件名集合的 jaccard 系数。> 60% 的标记为"合并候选"，LLM 判断是否应合并为同一屏幕的不同状态/Tab |
| **功能-上下文适配** | 屏幕中的功能组件必须在该屏幕的业务上下文中合理 | LLM 逐屏审查：对每个 component/filter/sort/action 执行「数据语义三问」——(a) 这个组件预设的数据来源是什么？（全局聚合/用户私有/实时流/静态配置） (b) 当前屏幕的数据实际来源是什么？ (c) 两者是否匹配？**不匹配 → 删除该组件**。同时检查：发现型组件（筛选/排序/推荐）只出现在公共数据的浏览屏幕，不出现在用户私有数据的管理屏幕；注册/认证等流程的表单复杂度必须与 `_governance_hint` 匹配 |
| **概念治理规则回溯** | 屏幕设计必须符合 `_governance_hint`（骨架注入）或 `product-mechanisms.json` 中的 `governance_styles` | 对每个涉及审核/审批/注册的屏幕，检查对应业务流的治理风格：(a) 治理风格为 lenient → **不应有审核队列/审核状态屏幕** (b) 治理风格为 auto_review → 只需异常队列，**不需要人工审核工作台** (c) 治理风格为 strict → 必须有审核+状态跟踪+审核员工作台 (d) `system_boundary.external` 中的功能 → 不在本系统屏幕中出现为可编辑表单，只保留最小信息+外部系统入口 (e) `downstream_implications` 中声明的屏幕需求 → 必须有对应屏幕存在 |
| **孤立屏幕检测** | 每个屏幕应有概念层依据（对应的 task、business-flow 节点、或 governance 需求） | 如果一个屏幕的 `tasks` 引用为空且不在任何 business-flow 中，标记为"无概念依据"。LLM 判断是否应删除或补充对应的 task |
| **交互类型×应用适配** | 交互类型必须与应用类型匹配 | 检查规则：(a) app=website + platform=mobile-ios 的屏幕不应使用 MG2-L（重列表管理，应用 CT1 或简化列表） (b) app=admin/merchant + platform=desktop-web 的屏幕不应使用 CT1（休闲浏览 Feed，应用 MG1 或 MG2-L） (c) 参考 `operation_profile.screen_granularity`：merchant 角色的相关任务应优先合并为同页多功能（而非拆成多个独立屏幕） |
| **跨应用数据泄露** | 屏幕不应展示只属于其他应用的数据 | 检查规则：(a) app=provider 的屏幕不应包含"全平台统计"、"所有服务提供者"等平台级数据字段 (b) app=admin 的屏幕不应包含单个服务提供者的日常运营数据（如"我的工单"） (c) app=website 的屏幕不应包含后台管理字段（如"审核状态管理"） |

**软性规则（不通过 → 警告但不阻塞）**：

| 验收项 | 规则 |
|--------|------|
| 状态完整 | 每个界面应定义 empty/error 状态 |
| 导航可达 | 每个界面至少有一个 entry_point |
| 创新覆盖 | product-concept 中的创新概念应有对应的独特界面 |

**用户端成熟度规则（当 `experience_priority.mode = consumer` 或 `mixed` 时为硬性，否则跳过）**：

> 读取 `.allforai/product-map/product-map.json` 的 `experience_priority` 字段。若不存在或 `mode = admin` → 跳过本段全部检查。
>
> **scope 限定**：仅检查用户端 app 的 screen（app 字段为 website/consumer/mobile 等面向终端用户的应用，排除 app=admin/merchant/backoffice）。mixed 模式下后台端 screen 不受这些规则约束。

| 验收项 | 规则 | 检查方法 |
|--------|------|---------|
| 主线清晰 | 用户端首页（home/dashboard/feed）必须有 1 条明确主线（而非功能入口拼盘），actions 中包含核心动作且标注为 primary | LLM 审查用户端 app 首页 screen 的 actions 和 components，判断是否存在单一核心路径 |
| 下一步引导 | 每个核心操作完成后的 screen 必须有"下一步"提示（actions 中含 navigate/continue/recommend 类动作） | 遍历用户端 app 中核心 task 对应的操作线末端 screen，检查 actions 是否包含引导性动作 |
| 状态系统统一 | 用户端 app 全部 screen 的 `states` 中的同类状态（empty/error/loading/success）设计响应必须一致 | 按用户端 app 分组，检查同名 state 的 description 是否表达一致的设计语言 |
| 回访理由 | 用户端 app 至少有 1 个 screen 包含持续使用触发点（进度/历史/提醒/推荐/订阅相关的 data_field 或 component） | 遍历用户端 app screens，检查是否存在 progress/history/reminder/recommendation 相关字段 |
| 移动端节奏 | platform=mobile 的 screen，actions 数量 ≤ 5（单手可达），核心动作居于视觉焦点位置。**例外**：支付/结算/表单提交类 screen（interaction_type 含 checkout/payment/form-wizard）允许 ≤ 8，因合规和安全需要较多确认步骤 | 遍历 mobile screen，按 interaction_type 区分阈值后检查 actions 数量 |

**XV Consumer Screen 评审（OpenRouter 可用 且 experience_priority = consumer/mixed 时，在 Loop 第 1 轮验收后触发）**：

向第二模型发送 consumer_apps 的 screen 名称列表 + 首页 actions 摘要（控制在 500 token 内），prompt：

```
你是 {产品类型} 的重度用户。以下是这个 App 的全部屏幕名称：
{screen_names}
首页内容：{home_screen_actions}

以用户身份判断：这像一个你会每天打开的成熟产品，还是像一个开发中的原型？
列出最关键的 3 个缺失体验（不给解决方案，只说"作为用户我缺什么"）。
回复 JSON: {"verdict": "mature|prototype|crud", "missing_as_user": ["...", ...]}
```

- verdict = "crud" → missing_as_user 作为 Loop 修正方向
- verdict != "crud" → 记录 missing_as_user，不阻塞
- OpenRouter 不可用 → 跳过（`XV ⊘`）

**Loop 机制**：

```
生成体验地图 → 硬性规则检查 + 设计质量规则 + 上游基线验收（LLM 判断）
  → consumer/mixed 时追加 XV consumer 评审
  全部通过 → Step 3.1 质量提升 loop
  不通过 →
    列出具体问题（哪些任务未覆盖、哪些情绪意图未落地、哪些高风险节点缺保护 + XV missing_as_user）
    LLM 修正对应界面
    → 重新验收（最多 3 轮）
  3 轮后仍不通过 → 记录剩余问题，WARNING 继续
```

---

### Step 3.1：质量提升 loop（设计精炼）

> Step 3 的合格性验收确保"没有错误"，Step 3.1 的质量提升确保"足够好"。这是两个不同的目标——合格性是底线，质量是天花板。

Step 3 通过后，进入质量提升 loop。该 loop 的目标不是修复错误，而是**持续提升设计质量**，因为 experience-map 的质量直接决定下游前端代码的质量。

#### 3.1.1 质量评分（每轮开始时执行）

LLM 对每个 screen 进行 5 维度打分（1-5 分），输出评分矩阵：

| 维度 | 1 分（差） | 3 分（及格） | 5 分（优秀） | 权重 |
|------|-----------|-------------|-------------|------|
| **D1 描述深度** | 重复屏幕名称，无设计意图 | 说明了用途但缺少"为什么"，< 60 字 | 清晰回答 D1+D4，≥ 80 字，包含设计权衡和替代方案理由 | 20% |
| **D2 状态完整性** | 只有 4 个基础状态 | 有 1-2 个业务状态但描述空泛 | ≥ 3 个业务特定状态，每个有具体交互描述，覆盖正常+异常+边界场景 | 25% |
| **D3 情绪落地** | emotion_design 为 null 或空泛字符串 | 有结构化对象但 design_response 是通用原则 | design_response 是该屏幕特有的可操作设计指令，与 source_emotion 强关联 | 15% |
| **D4 组件精确性** | 组件名通用（form, table），缺少 behavior | 有 purpose 但 behavior 空泛 | 每个组件的 behavior 描述了具体交互细节（触发条件、动画、反馈方式），data_source 指向正确实体 | 25% |
| **D5 交互适配** | interaction_type 与业务矛盾，layout_type 千篇一律 | interaction_type 基本正确，layout_type 合理 | interaction_type 精确匹配业务场景，layout_type 充分利用平台特性（mobile 手势、desktop 多列），interaction_pattern 描述独特交互 | 15% |

**加权总分** = D1×0.20 + D2×0.25 + D3×0.15 + D4×0.25 + D5×0.15

**质量阈值**：
- 每个 screen 加权总分 ≥ 3.5
- 全局平均分 ≥ 4.0
- 无任何 screen 在任何维度 ≤ 1

#### 3.1.2 识别提升目标

评分完成后，按优先级排序需要提升的 screen：

```
1. 任何维度 ≤ 1 的 screen → 最高优先级（质量缺陷）
2. 加权总分 < 3.5 的 screen → 高优先级（低于阈值）
3. 加权总分 3.5-4.0 且承载 core 任务的 screen → 中优先级（核心屏幕应更高）
4. 全局平均分 < 4.0 → 选取最低分的 20% screen 提升
```

对每个需要提升的 screen，生成**具体的提升指令**（不是"请改进"，而是"S020 的 states 缺少 payment_timeout 状态，需要添加超时后的用户引导交互"）。

#### 3.1.3 执行提升

按提升指令逐个 screen 重新设计。重新设计时 LLM 必须：

1. **重新阅读该 screen 的上游数据**（对应 task、entity 字段、emotion_node），不凭记忆
2. **参考同角色其他高分 screen 的设计模式**，保持一致性
3. **对比修改前后**，确认每个维度的分数确实提升了

**产品经理视角审查**（每个被修改的 screen 必须回答）：

| 审查问题 | 不合格信号 |
|---------|-----------|
| 用户在这个界面要完成什么任务？界面设计是否让任务路径最短？ | 操作步骤冗余、关键 CTA 不突出 |
| 用户从哪里来、到哪里去？前后界面的衔接是否自然？ | flow_context 断裂、缺少返回路径 |
| 用户在这一步的情绪是什么？设计是否回应了这个情绪？ | 焦虑场景缺少安全感设计、成就场景缺少正向反馈 |
| 如果操作失败了，用户能恢复吗？ | 缺少错误状态、没有重试/回退路径 |
| 这个界面的数据字段是用户需要看到/填写的吗？有没有系统字段泄露？ | 出现 id、created_at 等系统字段；缺少用户真正需要的字段 |
| 同类界面（如所有审批页）的交互模式是否一致？ | 同类型屏幕的组件布局/操作方式不统一 |

#### 3.1.4 Loop 控制

```
Step 3 合格性验收通过
  ↓
Round 1: 质量评分 → 识别低分 screen → 提升 → 重新评分
  全局平均 ≥ 4.0 且无 screen < 3.5 → Step 3.5
  ↓
Round 2: 聚焦 core 任务 screen → 对标竞品设计 → 提升 → 重新评分
  全局平均 ≥ 4.0 且无 screen < 3.5 → Step 3.5
  ↓
Round 3: 跨屏一致性审查 → 统一同类 screen 的交互模式 → 最终评分
  → Step 3.5（无论是否达标，记录最终评分到报告）
```

**每轮的侧重点不同**：
- **Round 1**：修补短板 — 把低分 screen 拉到及格线以上
- **Round 2**：提升核心 — 重点打磨承载 core 任务的 screen，可网络搜索参考竞品设计
- **Round 3**：统一风格 — 确保同类 screen（如所有 MG4 审批页、所有 CT2 详情页）的交互模式一致

**自动模式行为**：全自动模式下 3 轮全部自动执行，不停顿。每轮输出一行摘要：
```
Quality Round 1: avg 3.6→4.1, improved 12 screens, lowest S020(3.2→3.8)
Quality Round 2: avg 4.1→4.3, improved 5 core screens
Quality Round 3: avg 4.3→4.4, unified 3 pattern groups
```

**评分结果持久化**：最终评分写入 `experience-map-report.md` 的质量评分 section，每个 screen 的得分也写入 screen 对象的 `_quality_score` 字段（供下游 design-audit 参考）：

```json
{
  "id": "S020",
  "_quality_score": {
    "description_depth": 4,
    "states_completeness": 5,
    "emotion_alignment": 4,
    "component_precision": 4,
    "interaction_fit": 5,
    "weighted_total": 4.4,
    "round_improved": 2
  }
}
```

---

### Step 3.5：Playwright 线框验证（loop）

> 需要 Playwright MCP 可用（`mcp__playwright__browser_navigate` 或 `mcp__playwright__browser_navigate`）。不可用时跳过此步骤，在报告中标注 `playwright_verified: false`。

experience-map.json 写入后，使用 Playwright 自动化浏览器验证 Review Hub 线框渲染质量。此步骤分三轮检查：**结构验证 → 逐屏渲染验证 → 业务合理性判断**。

---

#### 3.5.1 启动与结构验证

```
1. 确保 Review Hub 服务器运行中（http://localhost:18900/）
   不可达 → 启动: python3 ../../shared/scripts/product-design/review_hub_server.py <BASE> --port 18900
2. 导航到 /wireframe 页面
3. browser_snapshot 获取完整页面快照
4. 从快照中提取操作线树结构，执行结构验证
```

**结构验证规则**（从页面快照中检查）：

| 检查项 | 通过条件 | 自动修复 |
|--------|---------|---------|
| 操作线数量 | 页面操作线数 = JSON 中 operation_lines 数 | 若不一致，检查是否有空操作线（nodes=0）并移除 |
| 屏幕数量 | 每条操作线的屏幕数 = JSON 中对应 nodes 内屏幕总数 | 检查 node.screens 嵌入完整性 |
| 操作线内去重 | 同一操作线内无重复 screen_id | 自动删除重复引用，保留首次出现 |
| interaction_type 合法性 | 所有 screen 的 interaction_type 在渲染器支持列表中 | 替换为最接近的合法类型（见选型指南） |

**操作线内去重自动修复**：

```python
# 检查逻辑：遍历每条操作线的所有 nodes，收集 screen_id
# 同一操作线内出现重复 screen_id → 删除后续出现的重复引用
# 不同操作线之间共享同一 screen_id 是正常的（多条旅程经过同一界面）
for line in operation_lines:
    seen_ids = set()
    for node in line["nodes"]:
        node["screens"] = [s for s in node["screens"] if s["id"] not in seen_ids and not seen_ids.add(s["id"])]
```

**interaction_type 自动修复映射**：

```
自创类型 → 最接近的合法类型：
  WORKSPACE/EDITOR  → WK3（文档编辑器）
  DASHBOARD/MONITOR → MG7（仪表盘）
  ANALYTICS/VIZ     → MG7（图表）或 CT2（可视化内容）
  REVIEW/APPROVE    → MG4（审批队列）
  LOG/HISTORY       → MG1（只读列表）
  AI-GEN/WIZARD     → SY2（向导表单）
  CHAT/DIALOGUE     → CT2（对话内容）
  INBOX/NOTIFICATION → MG3（状态机列表）或 RT4（通知中心）
  PROFILE/SETTINGS  → CT3（个人主页）或 MG8（配置页）
```

若自动修复后文件有变更 → 重新写入 experience-map.json → 刷新 /wireframe 页面。

---

#### 3.5.2 批量渲染验证

优先使用 `browser_run_code` 批量提取验证数据（1 次导航 + 2 次 JS 执行），替代逐屏点击。

**Step A — 批量提取页面内嵌数据**：

```
1. browser_navigate 到 /wireframe
2. browser_run_code 提取结构数据：

(() => {
  const results = {};
  // ALL_SCREENS 是 {sid: screenObj} 的字典，TREE_DATA 是操作线树，SIXV 是 6V 标注
  const sids = Object.keys(ALL_SCREENS);
  for (const sid of sids) {
    const sc = ALL_SCREENS[sid] || {};
    const fc = sc.flow_context || {};
    results[sid] = {
      name: sc.name || '',
      interaction_type: sc.interaction_type || '',
      data_fields_count: Array.isArray(sc.data_fields) ? sc.data_fields.length : 0,
      data_fields_valid: Array.isArray(sc.data_fields) && sc.data_fields.length > 0
        && typeof sc.data_fields[0] === 'object',
      actions_count: Array.isArray(sc.actions) ? sc.actions.length : 0,
      flow_has_prev: Array.isArray(fc.prev) && fc.prev.length > 0,
      flow_has_next: Array.isArray(fc.next) && fc.next.length > 0,
    };
  }
  return {
    screen_count: sids.length,
    tree_op_line_count: TREE_DATA.length,
    screens: results,
  };
})()
```

**Step B — 批量 fetch 验证 iframe 渲染**：

```
3. browser_run_code 批量 fetch 所有 screen 的渲染 HTML：

(async () => {
  const sids = Object.keys(ALL_SCREENS);
  const results = {};
  // 并发 fetch，每个 screen 的独立渲染页
  const fetches = sids.map(async (sid) => {
    try {
      const resp = await fetch('/wireframe/screen/' + sid);
      const html = await resp.text();
      const name = (ALL_SCREENS[sid] || {}).name || '';
      results[sid] = {
        html_length: html.length,
        not_blank: html.length > 200,
        has_title: name ? html.includes(name) : null,
        has_button: /<button[\s>]/i.test(html) || /class="[^"]*btn[^"]*"/i.test(html),
      };
    } catch (e) {
      results[sid] = { error: e.message };
    }
  });
  await Promise.all(fetches);
  return results;
})()
```

**Step C — LLM 分析批量结果**：

将 Step A 和 Step B 的返回值合并，按以下检查规则逐屏判定 PASS / FAIL：

| 检查项 | 通过条件 | 数据来源 | 失败原因分析 |
|--------|---------|---------|-------------|
| iframe 加载 | `not_blank === true`（HTML > 200 字符） | Step B | node.screens 嵌入不完整，或 JSON 格式错误 |
| 标题渲染 | `has_title === true` | Step B | screen.name 字段缺失 |
| 布局匹配 | `interaction_type` 在 ZONE_MAP 26 种合法类型内 | Step A | interaction_type 不在 ZONE_MAP 中 |
| 数据字段 | `data_fields_count > 0` 且 `data_fields_valid === true` | Step A | data_fields 为空数组或格式错误（字符串而非对象） |
| 操作按钮 | `actions_count > 0` 且 `has_button === true` | Step A + B | actions 字段为空 |
| Flow 连接 | `flow_has_prev \|\| flow_has_next` 至少一个为 true（首屏可无 prev，末屏可无 next） | Step A | flow_context 字段缺失或值为 null |

**常见渲染故障的自动修复**：

| 故障现象 | 根因 | 自动修复 |
|---------|------|---------|
| 表单页（MG2-C/MG2-E）空白崩溃 | actions 是字符串数组，渲染器调用 `.get("label")` 报错 | 将字符串 action 转为 `{"label": action, "frequency": "中"}` |
| flow_context 面板报错 | prev/next/entry_points/exit_points 值为 null | 将 null 替换为空数组 `[]` |
| 数据字段表格无内容 | data_fields 元素是字符串而非对象 | 将字符串转为 `{"name": field, "label": field, "type": "string", "input_widget": "text_input", "required": false}` |
| 屏幕渲染为无差别表格 | interaction_type 不在 ZONE_MAP | 回到 3.5.1 的 interaction_type 自动修复 |

**修复 → 重验循环**：

```
批量验证 → 汇总失败项
  全部 PASS → 进入 3.5.3 业务合理性判断
  有 FAIL →
    按故障类型分组（格式/数据/类型）
    执行对应自动修复
    重新写入 experience-map.json
    刷新 /wireframe 页面
    → 重新执行 Step A + B + C 批量验证（最多 2 轮）
  2 轮后仍有 FAIL → 记录到报告，WARNING 继续
```

> **Fallback**：若 `browser_run_code` 不可用（返回错误或超时），退回逐屏点击方式：对 /wireframe 页面树中的每个操作线展开后，逐一点击屏幕条目 → 等待 iframe 加载 → `browser_snapshot` 获取内容 → 按上表检查规则判定 PASS/FAIL。如果屏幕数 > 20，可抽样验证（每条操作线首尾屏幕 + 随机 1-2 个中间屏幕），抽样失败的操作线再全量验证。

---

#### 3.5.3 业务合理性判断

渲染验证通过后，LLM 从 Playwright 获取的页面快照中审查业务合理性：

**操作线维度**：

| 检查项 | 合理标准 | 不合理信号 |
|--------|---------|-----------|
| 屏幕数量 | 核心业务流 ≥ 3 屏幕 | 仅 1 个屏幕的操作线（如"订阅流"只有方案页没有支付确认页） |
| 流程完整性 | 操作线覆盖从入口到出口的完整闭环 | 流程在中间断裂（缺少确认/结果页） |
| 角色匹配 | 操作线中的屏幕角色一致 | 消费者操作线中混入管理员界面 |

**屏幕维度**：

| 检查项 | 合理标准 | 不合理信号 |
|--------|---------|-----------|
| 功能密度 | 每屏 1-3 个核心任务 | 单屏 > 5 个任务（功能堆叠）或 0 个任务（空壳屏幕） |
| 差异化 | 创新功能有独特交互 | 产品核心创新功能用普通表单（MG2-C）而非专用类型 |
| 模板-组件一致性 | interaction_type 渲染模板与 components 描述的交互形态匹配 | components 描述了可视化/画布/图表，但 interaction_type 用了列表/详情/表格模板 |
| 平台交互适配 | mobile 用触摸原生组件，desktop 用鼠标原生组件 | mobile 界面出现分页器（应为无限滚动）、右键菜单；desktop 出现滑动手势 |
| 平台差异 | mobile 和 desktop 布局明显不同 | desktop 界面也是单列竖屏布局 |
| 组件语义前提 | 每个组件隐含的数据假设必须被当前屏幕的数据模型支撑 | 组件预设的数据特征（作用域、基数、统计来源、更新频率）与屏幕实际数据不匹配 — 如组件需要多用户聚合统计但屏幕数据是单用户私有的，或组件需要实时流但数据是静态快照 |
| actions 相关性 | 操作与屏幕业务场景匹配 | 屏幕 A 的 actions 引用了属于屏幕 B 业务域的不相关任务 |

**render_as 语义验证（PM 视角）**：

> 产品经理视角：线框中每个组件的渲染形态必须与其业务用途匹配。Playwright 逐屏点击截图，LLM 以 PM 身份审查线框是否「看起来对」。

逐屏检查每个 component 的 `render_as` 是否与 `purpose` + `behavior` 语义匹配：

| 语义信号 | 正确 render_as | 常见误分配 |
|---------|--------------|-----------|
| purpose 含"切换/标签页/tabs/状态筛选" | `tab_nav` | key_value, data_table |
| purpose 含"按钮/登录/注册/提交/确认" 且**单一动作** | `action_bar` | data_table, input_form |
| purpose 含"选择器/切换/排序/步进/toggle" 且**单控件** | `action_bar` | input_form（4个 Field 的表单明显过度） |
| purpose 含"图表/趋势/统计/ROI/转化/分析" | `bar_chart` | input_form, data_table |
| purpose 含"步进器/数量调节/stepper" | `action_bar` | timeline |
| purpose 含"勾选/checkbox/同意" | `action_bar` | input_form |
| 组件只有1个操作入口（如单个按钮） | `action_bar` | input_form, data_table |

**验证方式**：

```
Playwright 逐屏验证 render_as 语义:
  1. 对每条核心操作线，点击首屏 + 末屏 + 1-2 个中间屏
  2. 从 iframe snapshot 中读取每个组件的渲染结构
  3. LLM 以 PM 视角判断：这个组件的线框「看起来像它应该的样子吗？」
     - 排序选择器渲染成了4个输入框？→ 不对，应该是 action_bar
     - 第三方登录按钮渲染成了数据表格？→ 不对，应该是 action_bar
     - 状态标签页渲染成了键值对？→ 不对，应该是 tab_nav
     - 广告效果面板渲染成了表单？→ 不对，应该是 bar_chart
  4. 收集所有 FAIL 的组件 → 批量修正 render_as → 回到步骤 1 重验
```

**不合理项处理**：

```
业务合理性审查 + render_as 语义验证 → 汇总不合理项
  全部合理 → Step 4
  有不合理项 →
    LLM 修正对应屏幕/操作线：
      - 补充缺失屏幕（如订阅流添加支付确认页）
      - 拆分过度堆叠的屏幕
      - 修正错误的 actions/tasks 引用
      - 调整 interaction_type
      - **修正 render_as 语义错误**（最高优先级，直接影响线框视觉质量）
    重新写入 experience-map.json
    → 回到 3.5.1 重新验证（最多 2 轮）
  2 轮后仍有问题 → 记录到报告，WARNING 继续
```

---

#### 3.5.4 验证报告输出

验证完成后，输出结构化验证结果（写入 experience-map-report.md）：

```
## Playwright 验证结果

验证轮次: N
总屏幕数: X
验证通过: Y / X

### 自动修复记录
| 屏幕 | 问题 | 修复动作 |
|------|------|---------|
| S006 | interaction_type 非最佳匹配 | → 调整为更合适的类型 |
| S019 | 操作线内重复出现 | 删除重复引用 |

### 业务合理性
| 操作线 | 屏幕数 | 判断 | 备注 |
|--------|--------|------|------|
| 核心业务流 | 7 | 合理 | 核心流程完整 |
| 支付链路 | 1 | ⚠ 不合理 | 缺少支付确认页 |

### 最终状态
playwright_verified: true / false
auto_fixes_applied: N
remaining_issues: M
```

---

### Step 3.6：模式扫描 + 行为规范（自动，不停顿）

验收和线框验证通过后，自动执行功能模式识别和行为规范检测，将标签直接写入 experience-map.json 的 screen 节点。

#### 3.6.1 功能模式识别

LLM 扫描 task-inventory.json + experience-map.json，检测 8 类功能模式：

| 模式 ID | 模式名 | 检测规则 |
|---------|--------|---------|
| `PT-CRUD` | CRUD 管理台 | 同实体 tasks 涵盖 create + list/query + edit/update + delete |
| `PT-LIST-DETAIL` | 列表+详情对 | 同模块存在 list 类型界面 + detail 类型界面 |
| `PT-APPROVAL` | 审批流 | business-flows 中出现 submit→review→approve/reject 序列 |
| `PT-SEARCH` | 搜索+筛选+分页 | actions 同时含 search/filter + paginate |
| `PT-EXPORT` | 导出/报表 | task 标题或 actions 含 export/report/download |
| `PT-NOTIFY` | 通知触发 | business-flows 节点后紧跟 notify/send/push 节点 |
| `PT-PERMISSION` | 权限矩阵 | 同实体被 3+ 角色访问且每角色权限不同 |
| `PT-STATE` | 状态机 | task 涉及 status/state 字段 + 状态转换动作 |

对匹配的 screen，写入 `_pattern` 和 `_pattern_group` 字段。**注意**：`_pattern` 只标识功能模式（如 CRUD、审批流），**不推荐具体布局**——布局由 LLM 在 Step 2 根据业务目的三问独立决定，不应被功能模式倒推。

```json
{
  "id": "S005",
  "name": "工单管理",
  "_pattern": ["PT-CRUD", "PT-SEARCH"],
  "_pattern_group": "records-crud",
  ...
}
```

#### 3.6.2 行为规范检测

LLM 扫描 experience-map.json 中所有 screen 的 states、actions、requires_confirm、on_failure、validation_rules 字段，检测 9 类行为不一致：

| ID | 名称 | 统一什么 |
|----|------|----------|
| `BC-DELETE-CONFIRM` | 破坏性操作确认 | 弹窗确认 vs 行内确认 vs 无确认 |
| `BC-EMPTY-STATE` | 空状态展示 | 图文引导 vs 纯文字 vs 空白 |
| `BC-LOADING` | 加载模式 | 骨架屏 vs 转圈 vs 渐进加载 |
| `BC-ERROR-DISPLAY` | 错误展示 | Toast vs 行内提示 vs 整页错误 |
| `BC-FORM-VALIDATION` | 表单校验反馈 | 实时校验 vs 提交时校验 |
| `BC-SUCCESS-FEEDBACK` | 成功反馈 | Toast vs 跳转 vs 行内反馈 |
| `BC-PERMISSION-DENIED` | 权限不足 | 重定向 vs 禁用/灰化 vs 隐藏 |
| `BC-PAGINATION` | 分页行为 | 无限滚动 vs 分页器 |
| `BC-UNSAVED-GUARD` | 未保存变更守卫 | 浏览器原生 vs 自定义弹窗 vs 无守卫 |

对有不一致的类别（影响 >= 3 个界面且分歧 > 30%），采用多数方案作为标准。对每个 screen 写入 `_behavioral` 和 `_behavioral_standards` 字段：

```json
{
  "id": "S001",
  "_behavioral": ["BC-DELETE-CONFIRM", "BC-EMPTY-STATE"],
  "_behavioral_standards": {
    "BC-DELETE-CONFIRM": "modal_confirm",
    "BC-EMPTY-STATE": "illustration_text"
  },
  ...
}
```

**跳过条件**：若所有 9 类行为均一致或影响界面 < 3 个，跳过行为标签写入。

#### 输出

Step 3.6 完成后，screen 节点已包含 `_pattern*` 和 `_behavioral*` 字段，不生成独立文件。下游 ui-design 和 design-audit 直接从 experience-map.json 读取这些字段。

---

### Step 4：输出

写入最终产物：

- `experience-map.json` — 机器可读完整结构
- `experience-map-report.md` — 人类可读报告（操作线总览 + 平台分布 + 高风险节点 + 验收结果 + Playwright 验证结果）
- `experience-map-decisions.json` — 决策记录
