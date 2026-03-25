# Modeling Steps (Steps 3-6.5)

> Part of the **product-map** skill. Loaded by the orchestrator at runtime.

---

## Step 3: 业务流建模

Step 2 完成后执行，所有模式均不可跳过。

### 生成方式

LLM 直接分析 task-inventory.json，理解业务领域语境后分组业务流。脚本无法理解领域语义（已验证会产出单个 "unknown" 流），因此由 LLM 主导。

**输出 schema 约束**（详见 `docs/schemas/business-flows-schema.md`）：
- `flows` 必须是数组，每个 flow 包含 `id`、`name`、`description`、`trigger`、`roles`、`nodes`
- `nodes` 中的 `task_ref` 必须引用 task-inventory 中已有的 task ID
- 每个 flow 应有明确的业务触发场景，不允许出现 "unknown" 或 "其他" 兜底流

### 候选流自动识别

Claude 分析 `task-inventory.json`，寻找任务间的状态衔接关系：若任务 A 的 `outputs.states` 与任务 B 的 `prerequisites` 匹配，视为候选流节点对，自动组合成候选业务流，展示给用户确认。

### 跨系统引用

若业务流涉及其他系统（如用户端 → 管理后台），用户可提供其他系统的 `task-inventory.json` 路径：

```
如果这条业务流涉及其他系统，请提供对应系统的 task-inventory 路径：
/path/to/other-system/.allforai/product-map/task-inventory.json
未提供时，跨系统节点标记为 gap_type: "UNVERIFIED"，不阻断流程。
```

`task_ref` 格式规则：

| 格式 | 含义 |
|------|------|
| `T001` | 当前系统的 T001 |
| `merchant-backend:T015` | merchant-backend 系统的 T015 |

### 流级缺口类型

| Flag | 含义 |
|------|------|
| `MISSING_TASK` | 流节点引用的 task 在对应系统不存在 |
| `BROKEN_HANDOFF` | 节点间有 handoff，但下游 task 的 prerequisites 对不上 |
| `INDEPENDENT_OPERATION` | task 未被任何流引用，但属于独立操作（如导出、设置、档案管理），无需纳入流 |
| `ORPHAN_TASK` | task 未被任何流引用，且不属于独立操作，可能是建模遗漏 |
| `MISSING_TERMINAL` | 流没有用户侧可感知的终止节点 |

**孤立任务分类规则**：未被任何流引用的任务，按以下规则自动分类：
- **INDEPENDENT_OPERATION**：任务名包含「导出」「设置」「配置」「查看列表」「管理档案」等独立操作关键词，或 `cross_dept` 为 false 且无 `approver_role`
- **ORPHAN_TASK**：不符合 INDEPENDENT_OPERATION 条件的孤立任务，可能是遗漏的流节点

只有 `ORPHAN_TASK` 标记为需关注的潜在问题；`INDEPENDENT_OPERATION` 仅作为信息记录。

### 自审计子步骤（中型/大型产品强制执行）

业务流初步生成后，自动验证：

1. **Handoff 连续性**：检查每条流中相邻节点的 handoff 是否连贯（前一节点的 outputs.states 是否匹配后一节点的 prerequisites）
2. **终止节点检查**：每条流必须有明确的用户可感知终止节点（如「任务完成」「处理结果通知」）
3. **高频任务覆盖**：所有 frequency="高" 的任务应至少出现在一条流中（否则标记为 ORPHAN_TASK 候选）
4. **状态供需平衡**（新增，通用版）：
   - 提取所有任务的 `outputs.states` → 生产者清单
   - 提取所有任务的 `prerequisites` → 消费者清单
   - 检测**孤儿状态**：有生产无消费（任何领域都应该避免）
   - 检测**幽灵状态**：有消费无生产（任何领域都零容忍）
   - 展示：「自审计发现 X 个孤儿状态 / X 个幽灵状态」

5. **状态契约检查**（新增，通用版）：
   - 对每个含 `outputs.states` 的任务，检查其 `exceptions` 是否覆盖所有可能错误
   - 对每个含 `prerequisites` 的任务，检查其 `on_failure` 是否定义
   - 检测**契约缺失**：状态转换无异常处理（如某操作无对应的失败处理）
   - 检测**超时缺失**：长时间操作（>30s）无超时转换定义
   - 展示：「自审计发现 X 个状态转换缺少异常处理 / X 个长时间操作无超时定义」
5. **展示审计结果**：在用户确认前，展示「自审计发现 X 个断裂交接 / X 个缺失终止节点 / X 个高频孤立任务 / X 个孤儿状态 / X 个幽灵状态」

### 用户确认

展示候选流 + 识别到的缺口 + 自审计结果，用户可：
- 确认/修改候选流
- 补充未被识别的跨系统节点
- 确认孤立任务分类（INDEPENDENT_OPERATION vs ORPHAN_TASK）

确认后写入 `business-flows.json` 和 `business-flows-report.md`。

### `business-flows.json` Schema

> 详见 ${CLAUDE_PLUGIN_ROOT}/docs/schemas/business-flows-schema.md

输出：`.allforai/product-map/business-flows.json`、`.allforai/product-map/business-flows-report.md`

### SVG 生成：business-flows-visual.svg

`business-flows.json` 写入磁盘后，生成 `.allforai/product-map/business-flows-visual.svg`。

**生成方式**：使用 Python 脚本生成 SVG 文件。脚本读取 `business-flows.json`，按以下设计意图生成泳道图：

**设计意图**：
- 按流分区，每条流一个泳道区块
- 泳道按角色分行，节点按 seq 顺序从左到右排列
- 正常节点蓝框白底，缺口节点红色虚线框
- 相邻节点用箭头连接，handoff 信息标注在箭头上方
- 画布宽高自适应节点数量，确保所有内容可见

**颜色规范**：

| 元素 | 颜色 |
|------|------|
| 流标题栏背景 | `#1E293B`，白色文字 |
| 泳道标签背景 | `#F1F5F9`，`#475569` 文字 |
| 正常节点 | border `#3B82F6`，fill `#EFF6FF`，文字 `#1E3A8A` |
| 缺口节点 | border `#EF4444` 虚线，fill `#FEF2F2`，文字 `#991B1B` |
| handoff 箭头 | `#64748B`，marker-end arrow |
| seq 编号圆 | fill `#3B82F6`，白色文字 |

写入 `.allforai/product-map/business-flows-visual.svg`

---

## Step 4: 冲突 & 冗余检测

**与 Step 5 互不依赖，可并行执行。**

基于已确认的任务，**仅检测任务级问题**：

**任务级冲突（保留）**：
- 两个任务的 `rules` 或状态流转互相矛盾（业务冲突）
- `main_flow` 缺少必要操作类型（CRUD 缺口：有新增无查看、有创建无撤回等）

**界面级问题（不在此处检测，移至 experience-map）**：
- 同一操作在多个界面重复 → 由 experience-map 的 `REDUNDANT_ENTRY` flag 处理
- 高风险操作没有二次确认 → 由 experience-map 的 `HIGH_RISK_NO_CONFIRM` flag 处理

只标记，不修改，最终决定由用户做出。

**CRUD 缺口建议**：检测到 CRUD 缺口时，除了标记问题，同时给出建议的补充任务描述（任务名 + 所属角色 + 建议的 main_flow），供用户评估是否纳入。用户确认后，纳入的任务追加到 `task-inventory.json` 并更新 decisions.json。

> 以下示例以虚构业务为背景，仅用于说明输出格式。实际内容由 product-map 分析结果决定，不限行业。

```json
{
  "conflicts": [
    {
      "id": "C001",
      "type": "CONFLICT",
      "description": "T001 要求数据提交后不可修改，T003 允许编辑已提交数据",
      "affected_tasks": ["T001", "T003"],
      "severity": "高",
      "confirmed": false
    }
  ],
  "crud_gaps": [
    {
      "id": "CG001",
      "type": "CRUD_INCOMPLETE",
      "description": "T001 main_flow 只有创建和提交，缺少撤回/修改流程",
      "affected_tasks": ["T001"],
      "severity": "中",
      "confirmed": false,
      "suggested_task": {
        "name": "撤回已提交申请",
        "owner_role": "R001",
        "main_flow": ["选择待审核申请", "确认撤回", "释放锁定资源", "通知审核人"]
      }
    }
  ]
}
```

**用户确认**：检测结果有没有误报？哪些 CRUD 缺口需要补充？

**quick 模式冲突处理**：跳过 Step 4（独立冲突检测）和 Step 5（约束识别），但 Step 9 Part 2 仍执行完整冲突扫描（覆盖 CROSS_ROLE_CONFLICT、STATE_DEADLOCK、IDEMPOTENCY_CONFLICT）。quick 模式下 `conflict-report.json` 不生成，冲突结果仅出现在 `validation-report.json` 中。

输出：`.allforai/product-map/conflict-report.json`

---

## Step 5: 约束识别

**与 Step 4 互不依赖，可并行执行。**

识别两类约束：

**合规/审计要求**：操作留痕、数据可追溯、保留期限、导出需审批等

**业务约束**：不可逆操作、金额对账一致性、审批分级、SLA 硬限制等

**代码验证**（中型/大型产品推荐）：识别约束后，扫描代码验证哪些约束已有实现（如 bcrypt 密码哈希、GORM 软删除、定时任务自动确认收货等），在约束描述中标注实现状态：
- `"code_status": "implemented"` -- 代码已实现
- `"code_status": "partial"` -- 部分实现
- `"code_status": "missing"` -- 代码未实现（潜在风险）

> 以下示例以虚构业务为背景，仅用于说明输出格式。实际内容由 product-map 分析结果决定，不限行业。

```json
{
  "constraints": [
    {
      "id": "CN001",
      "type": "business",
      "description": "操作金额不可超过原始记录金额",
      "affected_tasks": ["T001"],
      "enforcement": "hard",
      "code_status": "implemented",
      "confirmed": true
    },
    {
      "id": "CN002",
      "type": "compliance",
      "description": "所有敏感操作必须留存操作日志，保留 3 年",
      "affected_tasks": ["T001", "T003"],
      "enforcement": "hard",
      "code_status": "missing",
      "confirmed": true
    }
  ]
}
```

**用户确认**：约束识别完整吗？有没有遗漏的隐性规则？代码实现状态是否准确？

输出：`.allforai/product-map/constraints.json`

---

## Step 6: 输出产品地图报告

汇总前步骤的所有已确认数据，生成两个文件。

### 生成方式

LLM 聚合前序步骤的所有已确认数据（role-profiles + task-inventory + business-flows + 冲突报告 + 约束），生成 product-map.json + report + task-index + flow-index + SVG。

此处必须同时写入 `experience_priority`，作为下游统一消费的全局判定契约，而不是只在文字报告里提及。

写入规则：

- 若存在用户端/移动端主界面，必须显式输出 `experience_priority`
- 若后台是主价值面，`mode = admin`
- 若用户端是主价值面，`mode = consumer`
- 若两端都重要，`mode = mixed`
- `reasoning` 至少写 2 条可解释依据，禁止只给枚举不给理由

**重要**：不得覆盖已存在的上游产物（如 entity-model.json、business-flows.json）。仅生成本步骤的新文件。

### `product-map.json` / 报告 / SVG / 索引

> 详见 ${CLAUDE_PLUGIN_ROOT}/docs/schemas/product-map-output.md

输出：`.allforai/product-map/product-map.json`、`.allforai/product-map/product-map-report.md`、`.allforai/product-map/product-map-visual.svg`

写入 `.allforai/product-map/task-index.json`、`.allforai/product-map/flow-index.json`

其中 `.allforai/product-map/product-map.json` 必须包含：

- `summary`
- `experience_priority`
- `roles`
- `tasks`
- `conflicts`
- `constraints`

---

## Step 6.5: Experience DNA 体验基因

> 把产品灵魂从"软上下文"变成"硬产物"。experience-dna.json 和 entity-model.json 同级别——不是建议，是合约。

**输入**：
- `concept-baseline.json` → core_mechanisms, errc_highlights.differentiators
- `product-map.json` → task-inventory（高频+核心任务）
- `competitor-profile.json` → 竞品对比（如有）
- `product-mechanisms.json` → governance_styles, mechanism decisions（如有）

**LLM 分析**：

Agent 以产品总监视角分析：
1. 读取 core_mechanisms，识别每个机制的「用户可感知差异点」
2. 对每个差异点，推导具体的视觉/交互契约：
   - 这个差异在 UI 上怎么被用户 3 秒内感知？
   - 竞品在这个维度的做法是什么？我们如何不同？
   - 如果把这个差异去掉，产品就"像普通 XX 应用"了
3. 推导关键过渡仪式（ceremony moments）——用户旅程中的 "wow" 时刻
4. 提取反模式——这个产品绝对不能看起来像什么

**输出**：`.allforai/product-map/experience-dna.json`

```json
{
  "generated_at": "ISO8601",
  "product_archetype": "LLM 推导的产品类型标签",
  "differentiators": [
    {
      "id": "DIFF-001",
      "name": "差异化体验名称",
      "mechanism_ref": "core_mechanisms[0]",
      "category": "interaction | visual | flow | feedback | information_architecture",
      "user_perception": "用户3秒内感知到的差异（一句话）",
      "competitive_gap": "竞品在这个维度的不足",
      "visual_contracts": [
        {
          "id": "VC-001",
          "component": "组件/Widget 名称",
          "placement": "出现在哪个屏幕/位置",
          "spec": "具体的视觉+交互规格（2-3句话）",
          "must_not": "反模式——不能做成什么样",
          "absence_impact": "CRITICAL | HIGH | MEDIUM"
        }
      ],
      "protection_level": "core | defensible | nice_to_have"
    }
  ],
  "ceremony_moments": [
    {
      "id": "CERE-001",
      "trigger": "触发时刻描述",
      "user_emotion": "用户此刻的期望情绪",
      "spec": "过渡仪式的具体规格",
      "duration": "建议持续时间",
      "rationale": "为什么这个时刻需要仪式感"
    }
  ],
  "anti_patterns": [
    "这个产品绝对不能看起来像 XX"
  ],
  "summary": {
    "total_differentiators": 0,
    "core": 0,
    "defensible": 0,
    "nice_to_have": 0,
    "total_visual_contracts": 0,
    "total_ceremonies": 0
  }
}
```

**确认方式**：
- 交互模式：展示差异化契约表，用户确认或调整 protection_level
- 自动模式：自动确认（DIFF 数 = 0 → WARNING 停下来，可能 concept-baseline 太空）

**质量门禁**（按规模弹性）：
- differentiators 数量 >= 1（必须有至少 1 个差异点，否则产品没有存在理由）
  - 标准/大型项目（模块 > 5）：建议 >= 3，不足时 WARNING 不阻塞
  - 小型项目（模块 ≤ 5）：>= 1 即可
- 每个 core 级 DIFF 至少有 1 个 visual_contract
- ceremony_moment >= 1（小型产品如无自然的 ceremony 可标注 `none_identified`，不阻塞）
