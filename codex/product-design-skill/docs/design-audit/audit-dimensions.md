# Design Audit — Audit Dimensions

> Extracted from `skills/design-audit.md`. All dimension definitions for the design audit pipeline.

---

## Phase A：确定性检查（脚本串行）

**执行命令**：

```bash
python3 ../../shared/scripts/product-design/gen_design_audit.py <BASE> [--mode auto]
```

脚本自动完成以下所有步骤，输出 `audit-report.json`（基线报告）和 `audit-report.md`。

### 前置：两阶段加载 + 产物探测

**Phase 1 — 加载索引**（始终安全，< 5KB）：

| 索引文件 | 路径 |
|----------|------|
| task-index | `.allforai/product-map/task-index.json` |
| screen-index | `.allforai/experience-map/screen-index.json` |
| flow-index | `.allforai/product-map/flow-index.json` |

任一索引存在 → 加载索引，按需决定是否加载完整数据。
所有索引不存在 → 回退全量加载 `product-map.json`。

**Phase 2 — 产物探测**：

检查以下目录/文件是否存在，构建 `available_layers[]`：

| 层 | 必须/可选 | 检测文件 |
|----|----------|----------|
| product-map | 必须 | `.allforai/product-map/product-map.json` |
| experience-map | 必须（不存在则自动运行 experience-map） | `.allforai/experience-map/experience-map.json` |
| use-case | 可选 | `.allforai/use-case/use-case-tree.json` |
| feature-gap | 可选 | `.allforai/feature-gap/gap-tasks.json` |
| ui-design | 可选 | `.allforai/ui-design/ui-design-spec.md` |

- `product-map` 不存在 → 输出「请先执行 product-map 工作流建立产品地图」，**立即终止**
- 可选层不存在 → 跳过相关校验项，在报告中标注「层缺失，已跳过」

**`role` 模式额外处理**：从 `task-index.json` 按 `owner_role` 筛选匹配任务 ID 列表，后续所有校验仅涉及这些任务及其关联产物。

---

### Step 1：逆向追溯（Trace）

从下游产物往上游反查，验证每个产物项是否有合法的上游引用。

| # | 校验 | 条件 | 逻辑 |
|---|------|------|------|
| T1 | screen → task | experience-map 存在 | 每个 screen 的 `task_refs` 中的 task_id 必须在 task-inventory 中存在 |
| T2 | use-case → task | use-case 存在 | 每条 use-case 的 `task_id` 必须在 task-inventory 中存在 |
| T3 | use-case → screen | use-case + experience-map 存在 | 每条 use-case 的 `screen_ref` 必须在 experience-map 中存在 |
| T4 | gap-finding → task | feature-gap 存在 | 每个 gap 的 `task_id` 必须在 task-inventory 中存在 |

**执行逻辑**：

1. 仅执行条件满足（相关层在 `available_layers[]` 中）的校验项
2. 逐条检查引用关系，标记结果
3. 向用户展示结果摘要，等待确认

**结果标记**：

| 标记 | 含义 |
|------|------|
| `PASS` | 引用合法，上游源头存在 |
| `ORPHAN` | 无源头，下游产物引用了不存在的上游 ID |

每个 orphan 项列出：check_id、source 层、item_id、item_name、缺失的上游 ID。

---

### Step 2：覆盖洪泛（Coverage）

从上游 task-inventory 往下游洪泛，验证每个任务是否被下游层完整消费。

| # | 校验 | 条件 | 逻辑 |
|---|------|------|------|
| C1 | task → screen | experience-map 存在 | 每个 task 至少有一个 screen 引用它（通过 screen 的 `task_refs` 反查） |
| C2 | task → use-case | use-case 存在 | 每个 task 至少有一条正常流用例 |
| C3 | task → gap-checked | feature-gap 存在 | 每个 task 在 gap 报告中被检查过 |
| C4 | task → ui-design | ui-design 存在 | 每个 task 在 UI 设计中有体现（检查 ui-design-spec.md 中是否提及该任务名或关联界面） |
| C5 | role → full journey | experience-map + use-case 存在 | 按角色追踪：tasks → screens → use-cases，检测断链（某任务有 screen 但无 use-case，或反过来） |

**执行逻辑**：

1. 仅执行条件满足的校验项
2. 遍历 task-inventory 中每个任务（`role` 模式下仅遍历指定角色的任务）
3. 逐条检查是否被下游消费
4. 统计覆盖率百分比：`covered / total × 100%`
5. 向用户展示结果摘要，等待确认

**结果标记**：

| 标记 | 含义 |
|------|------|
| `COVERED` | 任务被下游层完整消费 |
| `GAP` | 任务未被某下游层消费 |

每个 gap 项列出：check_id、task_id、name、missing_in（缺失的下游层）。

---

### Step 3：横向一致性（Cross-check）

相邻层之间的矛盾和不一致检测。

| # | 校验 | 条件 | 逻辑 |
|---|------|------|------|
| X1 | 频次 × 点击深度 | product-map + experience-map 存在 | 高频任务（frequency=高）在 experience-map 中 click_depth ≥ 3 → WARNING（高频操作被埋深） |
| X2 | use-case screen_ref | use-case + experience-map 存在 | 用例引用的 `screen_ref` 在 experience-map 中不存在 → BROKEN_REF |

**执行逻辑**：

1. 仅执行条件满足的校验项
2. 逐条检查相邻层之间的一致性
3. 向用户展示结果摘要，等待确认

> **搜索驱动原则**：展示审计结果前，先 网络搜索「design audit checklist {产品类型}」和「cross-layer consistency verification best practices」，用搜索结果补充审计维度。

**结果标记**：

| 标记 | 含义 | 严重度 |
|------|------|--------|
| `OK` | 无矛盾 | — |
| `CONFLICT` | 跨层矛盾，必须修复 | 最高 |
| `WARNING` | 设计合理性风险 | 中 |
| `BROKEN_REF` | 引用断裂 | 中 |

---

### Step 3.5：信息保真门禁（Fidelity）

在不改变现有主流程的前提下，补充两项统计门禁：

| # | 门禁 | 逻辑 | 建议阈值 |
|---|------|------|----------|
| F1 | Traceability 完整率 | 关键下游对象中，可追溯到上游证据/引用的比例 | ≥ 95% |
| F2 | Viewpoint 覆盖率 | 关键对象中，覆盖至少 4/6 视角（user/business/tech/ux/data/risk）的比例 | ≥ 90% |

**结果标记**：

| 标记 | 含义 |
|------|------|
| `PASS` | 达到阈值 |
| `BELOW_THRESHOLD` | 未达到阈值，建议回到上游补充上下文 |

---

### Step 3.7: 连贯性审计（Continuity Audit）

从 `interaction-gate.json` 读取质量门禁结果，检查：

| 指标 | 合格标准 |
|------|---------|
| 操作线步骤数 | ≤ 7 |
| 上下文切换 | ≤ 2 |
| 等待反馈覆盖率 | = 1.0 |
| 拇指热区合规率 | ≥ 0.8 |

不合格的操作线记入审计报告 `continuity_issues` 数组。

---

## Phase B：语义审计（LLM 并行 3 Agent）

Phase A 脚本完成后，以下 3 个语义审计任务并行执行。

每个 Agent 读取 Phase A 产出的 `audit-report.json` 作为上下文（只读），执行各自的审计维度，将结果写入独立的分片文件。

**Agent 分工**：

| Agent | 审计维度 | 分片输出 |
|-------|---------|---------|
| Agent 1 | Step 5 模式一致性 + Step 5.5 创新保真 | `.allforai/design-audit/audit-shard-pattern.json` |
| Agent 2 | Step 5.6 行为一致性 | `.allforai/design-audit/audit-shard-behavioral.json` |
| Agent 3 | Step 5.7 交互类型一致性 | `.allforai/design-audit/audit-shard-interaction.json` |

**并行任务 prompt 模板**：

~~~
你是设计审计流水线的并行审计器。

任务: 执行 {审计维度} 的完整检测流程。

上下文:
- 读取 .allforai/design-audit/audit-report.json（Phase A 基线报告，只读）
- 读取 .allforai/experience-map/experience-map.json
- 读取 .allforai/ui-design/ui-design-spec.md（如存在）
- 读取 .allforai/product-concept/adversarial-concepts.json（仅 Agent 1 需要）
- 读取 ./docs/interaction-types.md（仅 Agent 3 需要）

执行:
1. 按下方对应 Step 的检测项逐一执行
2. 前置条件不满足 → 该维度 status="skipped"，仍写分片文件
3. 结果写入分片文件: .allforai/design-audit/audit-shard-{shard_name}.json

分片 JSON Schema:
{
  "shard": "{shard_name}",
  "generated_at": "ISO8601",
  "sections": {
    "{section_key}": {
      "status": "pass | issues_found | skipped",
      ...维度特定字段...
      "issues": [...]
    }
  }
}

重要:
- 禁止修改 audit-report.json（Phase A 产出）
- 禁止读写其他 Agent 的分片文件
- 前置条件不满足时写 skipped 分片而非不写文件
~~~

**quick 模式**: 仅执行 Phase A 脚本，跳过 Phase B 并行 Agent（LLM 审计步骤全部跳过）。Phase C 直接以 Phase A 的 audit-report.json 为最终报告。

---

### Step 5：模式一致性审计（Pattern Consistency）

> 目标：验证相同功能模式的界面/任务是否遵循了统一的设计套路。
> **前提**：experience-map.json 中至少有一个 screen 含 `_pattern` 字段（由 experience-map Step 3.6 写入）。无 _pattern 字段 → 跳过本步骤。

#### 检测项

**5a. 界面模板一致性**

对 experience-map.json 中所有含 `_pattern_group` 字段的 screen，按 group 分组：
- 读取该 group 所有 screen_ids 在 ui-design-spec.md 中的设计描述
- 检测主布局模板是否一致（操作栏位置、列表样式、表单入口方式）
- 不一致 → `PATTERN_DRIFT`（模式漂移）

**5b. 跨实体 CRUD 一致性**

对所有 PT-CRUD 实例：
- 检查「新建」按钮位置是否一致（统一右上角或统一行内）
- 检查「删除」确认方式是否一致（统一弹窗确认或统一行内确认）
- 不一致 → `CRUD_INCONSISTENCY`

**5c. 审批流状态标签体系**

对所有 PT-APPROVAL 实例：
- 检查各流程的状态标签（待审/通过/拒绝）颜色语义是否统一
- 不一致 → `APPROVAL_COLOR_DRIFT`

**5d. 状态机操作按钮**

对所有 PT-STATE 实例：
- 检查状态转换操作按钮（如「通过」「拒绝」「归档」）的呈现位置是否一致（顶部操作栏/详情底部/行内）
- 不一致 → `STATE_ACTION_DRIFT`

#### 输出格式

```json
{
  "pattern_consistency": {
    "status": "pass | issues_found | skipped",
    "issues": [
      {
        "type": "PATTERN_DRIFT | CRUD_INCONSISTENCY | APPROVAL_COLOR_DRIFT | STATE_ACTION_DRIFT",
        "pattern_id": "PT-CRUD",
        "pattern_group": "orders-crud",
        "description": "orders 管理台用弹窗表单，但 users 管理台用侧边栏",
        "affected_screens": ["S-05", "S-06", "S-11"],
        "severity": "MEDIUM",
        "recommendation": "统一使用弹窗表单（已在 Phase 3.5 确认选型）"
      }
    ],
    "total_patterns_checked": 4,
    "clean_patterns": 3,
    "drift_patterns": 1
  }
}
```

**严重度分级**：
- `HIGH`：核心路径（CRUD/审批流）出现漂移，用户认知成本高
- `MEDIUM`：次要路径（导出/状态机）漂移，影响一致性感知
- `LOW`：细节（按钮标签文本）差异，可接受

**输出处理**：
- 所有 issues 追加到 `audit-report.json` 的 `pattern_consistency` 字段
- issues_found → 在 audit-report.md 中新增「模式一致性」章节展示漂移列表
- 不阻塞流程，仅报告

---

### Step 5.5：创新保真审计（Innovation Fidelity）

> 目标：验证 product-concept 阶段定义的核心创新概念是否在全链路中存活且未被稀释。
> **前提**：`.allforai/product-concept/adversarial-concepts.json` 存在且含 `protection_level=core` 概念。不存在 → 跳过本步骤。

#### 检测项

**5.5a. 创新概念存活率**

对每个 `protection_level=core` 的创新概念：
- 在 `task-inventory.json` 中是否有 `innovation_task=true` 的对应任务？
- 在 `ui-design-spec.md/json` 中是否有专属设计节？
- 缺失任一层 → `INNOVATION_DILUTED`

**5.5b. 创新概念完整度**

对每个存活的核心创新概念：
- 其跨领域参考（adversarial_concept_ref）是否在 ui-design 中体现？
- 完整度不足 → `INNOVATION_INCOMPLETE`

#### 输出格式

```json
{
  "innovation_fidelity": {
    "status": "pass | issues_found | skipped",
    "core_concepts_total": 3,
    "survived": 3,
    "diluted": 0,
    "incomplete": 1,
    "issues": [
      {
        "type": "INNOVATION_DILUTED | INNOVATION_INCOMPLETE",
        "concept_id": "IC001",
        "concept_name": "...",
        "missing_in": ["ui-design"],
        "severity": "HIGH",
        "recommendation": "在 ui-design 中补充 IC001 专属设计节"
      }
    ]
  }
}
```

**严重度**：核心创新被稀释 → HIGH（产品差异化风险）。

---

### Step 5.6：行为一致性审计（Behavioral Consistency）

> 目标：验证所有界面是否遵循确认的行为规范。
> **前提**：experience-map.json 中至少有一个 screen 含 `_behavioral` 字段（由 experience-map Step 3.6 写入）。无 _behavioral 字段 → 跳过本步骤。

#### 检测项

**5.6a. 行为标准合规检查**

对 experience-map.json 中所有含 `_behavioral_standards` 字段的 screen，按 category 分组：
- 读取每个 screen 的 `_behavioral_standards` 方案
- 在 ui-design-spec.md/json 中检查该 screen 的设计是否匹配标准方案
- 不匹配 → `BEHAVIORAL_DRIFT`（行为漂移）

**5.6b. 破坏性操作确认合规**

对每个 screen 的 `crud=D` action 且 `requires_confirm=false`：
- 若 BC-DELETE-CONFIRM 标准为 `modal_confirm` →
  `BEHAVIORAL_VIOLATION`（界面违反已确认的行为规范）

#### 输出格式

```json
{
  "behavioral_consistency": {
    "status": "pass | issues_found | skipped",
    "total_categories_checked": 7,
    "compliant_screens": 18,
    "violating_screens": 2,
    "issues": [
      {
        "type": "BEHAVIORAL_DRIFT | BEHAVIORAL_VIOLATION",
        "category_id": "BC-DELETE-CONFIRM",
        "id": "S-05",
        "expected": "modal_confirm",
        "actual": "no_confirm",
        "severity": "MEDIUM",
        "recommendation": "添加模态确认弹窗"
      }
    ]
  }
}
```

**严重度分级**：
- `HIGH`：破坏性操作无确认（`BEHAVIORAL_VIOLATION`），用户数据安全风险
- `MEDIUM`：行为漂移（`BEHAVIORAL_DRIFT`），一致性体验受损
- `LOW`：细微偏差（加载方式略有不同），可接受

**输出处理**：
- 所有 issues 追加到 `audit-report.json` 的 `behavioral_consistency` 字段
- issues_found → 在 audit-report.md 中新增「行为一致性」章节展示违规列表
- 不阻塞流程，仅报告

---

### Step 5.7：交互类型一致性审计（Interaction Type Consistency）

> 目标：验证相同交互类型的界面是否遵循统一的布局约束和行为模式。

**前置检查**：
1. `.allforai/experience-map/experience-map.json` 是否存在
   - 不存在 → 提示「请先执行 experience-map 工作流生成体验地图」，终止
2. experience-map 中每个 screen 是否含 `interaction_type` 字段
   - 缺失 → 提示「experience-map 未标注 interaction_type，请执行 experience-map refresh 重新生成」，终止

---

#### 检测项

**5.7a. 同类型界面布局一致性**

从 `./docs/interaction-types.md` 提取布局约束：

| 类型 | 布局约束 | 禁止项 |
|------|----------|--------|
| **MG1 只读列表** | 列表/表格/网格 | 表单、向导 |
| **MG2-L 列表** | 列表/表格 | 内嵌表单（新建应在独立页/弹窗） |
| **MG2-C 新建** | 表单页/弹窗 | — |
| **MG2-E 编辑** | 表单页/弹窗，必须回填旧值 | — |
| **MG3 状态机** | 状态标签（专用列）+ 操作下拉/Swipe | — |
| **MG5 主从详情** | 主实体区 + 子实体Tab | 无子实体的单层详情 |
| **MG6 树形管理** | 树形组件 + 编辑区联动 | — |
| **EC1 内容详情** | 图片轮播 + 规格选择 + 底部操作栏 | 无规格选择 |
| **EC2 待处理列表** | 列表 + 底部汇总区 | — |
| **WK1 对话/IM** | 消息流 + 底部输入框 | — |
| **WK5 看板** | 水平多列 + 卡片 | 单列列表 |

完整约束见 `interaction-types.md` 第 107-950 行各类型的「平台矩阵」。

**检测逻辑**：

```python
def check_layout_consistency(screens, layout_constraints):
    issues = []

    # 按 interaction_type 分组
    by_type = group_by(screens, 'interaction_type')

    for type_key, type_screens in by_type.items():
        constraints = layout_constraints.get(type_key, {})

        # 检查布局模式
        allowed_layouts = constraints.get('allowed_layouts', [])
        forbidden_layouts = constraints.get('forbidden_layouts', [])

        for screen in type_screens:
            layout = detect_layout_type(screen)  # 从 screen 结构推断

            # 检查禁止项
            if layout in forbidden_layouts:
                issues.append({
                    'type': 'LAYOUT_FORBIDDEN',
                    'id': screen['id'],
                    'screen_name': screen['name'],
                    'interaction_type': type_key,
                    'layout': layout,
                    'forbidden': forbidden_layouts,
                    'severity': 'HIGH',
                    'recommendation': f'{type_key} 不应使用 {layout} 布局'
                })

            # 检查允许项（可选，宽松模式）
            elif allowed_layouts and layout not in allowed_layouts:
                issues.append({
                    'type': 'LAYOUT_DRIFT',
                    'id': screen['id'],
                    'screen_name': screen['name'],
                    'interaction_type': type_key,
                    'layout': layout,
                    'allowed': allowed_layouts,
                    'severity': 'MEDIUM',
                    'recommendation': f'建议使用 {allowed_layouts} 之一'
                })

    return issues
```

---

**5.7b. 同类型界面布局偏差检测**

对同一 `interaction_type` 的多个 screen，检测布局偏差：

```python
def detect_layout_drift(type_screens):
    """检测同类界面的布局偏差"""
    layouts = [(s['id'], detect_layout_type(s)) for s in type_screens]

    # 所有布局是否一致
    unique_layouts = set(l[1] for l in layouts)

    if len(unique_layouts) > 1:
        return {
            'type': 'INCONSISTENT_LAYOUT',
            'screens': [l[0] for l in layouts],
            'layouts': list(unique_layouts),
            'severity': 'MEDIUM',
            'recommendation': '同类型界面应使用统一布局模式'
        }

    return None
```

示例：
- `MG2-L` 类型有 5 个 screen，其中 4 个用表格，1 个用卡片 → **LAYOUT_DRIFT**

---

**5.7c. 类型-上下文匹配度验证**

验证每个 screen 的 `interaction_type` 是否匹配「产品类型 × 用户属性 × 平台」的预设频率：

| 匹配度 | 检测 |
|--------|------|
| `excluded` 类型出现 | **TYPE_CONTEXT_MISMATCH**（该类型不应出现在此上下文） |
| `low` 类型占比过高 | **LOW_TYPE_OVERREPRESENTED**（低频类型超过 30%） |

```python
def check_type_context_match(screens, product_type, audience, platform):
    preset = load_type_preset(product_type, audience, platform)

    issues = []
    type_counts = Counter(s.get('interaction_type', '') for s in screens)
    total = len(screens)

    # 检查 excluded 类型
    for itype in preset.get('excluded', []):
        if type_counts.get(itype, 0) > 0:
            issues.append({
                'type': 'TYPE_CONTEXT_MISMATCH',
                'interaction_type': itype,
                'count': type_counts[itype],
                'severity': 'HIGH',
                'recommendation': f'{itype} 在 {product_type}/{audience}/{platform} 上下文中不应出现'
            })

    # 检查低频类型占比
    low_types = preset.get('低频', [])
    low_count = sum(type_counts.get(t, 0) for t in low_types)
    low_ratio = low_count / total if total > 0 else 0

    if low_ratio > 0.3:
        issues.append({
            'type': 'LOW_TYPE_OVERREPRESENTED',
            'low_type_ratio': f'{low_ratio:.1%}',
            'threshold': '30%',
            'severity': 'MEDIUM',
            'recommendation': '低频类型占比过高，考虑精简'
        })

    return issues
```

---

#### 输出格式

```json
{
  "interaction_type_consistency": {
    "status": "pass | issues_found | skipped",
    "total_types_checked": 12,
    "consistent_types": 10,
    "drift_types": 2,
    "issues": [
      {
        "type": "LAYOUT_FORBIDDEN",
        "id": "S015",
        "screen_name": "内容管理",
        "interaction_type": "MG1",
        "layout": "form",
        "forbidden": ["form", "wizard"],
        "severity": "HIGH",
        "recommendation": "MG1 只读列表不应使用表单布局"
      },
      {
        "type": "INCONSISTENT_LAYOUT",
        "interaction_type": "MG2-L",
        "screens": ["S010", "S011", "S012", "S013", "S014"],
        "layouts": ["table", "card"],
        "severity": "MEDIUM",
        "recommendation": "MG2-L 类型界面应统一布局（建议 table）"
      },
      {
        "type": "TYPE_CONTEXT_MISMATCH",
        "interaction_type": "MG4",
        "count": 3,
        "severity": "HIGH",
        "recommendation": "MG4(审批) 在 C端用户/Mobile App 上下文中不应出现"
      }
    ]
  }
}
```

---

#### 严重度分级

| 严重度 | 问题类型 | 影响 |
|--------|----------|------|
| `HIGH` | LAYOUT_FORBIDDEN / TYPE_CONTEXT_MISMATCH | 用户认知混乱或上下文不匹配 |
| `MEDIUM` | INCONSISTENT_LAYOUT / LAYOUT_DRIFT | 一致性体验受损 |
| `LOW` | LOW_TYPE_OVERREPRESENTED | 可优化但不阻塞 |

---

#### 输出处理

- 所有 issues 追加到 `audit-report.json` 的 `interaction_type_consistency` 字段
- issues_found → 在 audit-report.md 中新增「交互类型一致性」章节展示问题列表
- 不阻塞流程，仅报告

---

## Phase C：合并分片报告

3 个并行任务全部完成后，编排器执行合并。

**执行步骤**：

1. 读取 Phase A 基线报告：`.allforai/design-audit/audit-report.json`
2. 读取 3 个分片文件（缺失的分片视为 skipped）：
   - `audit-shard-pattern.json` → 合并到 `pattern_consistency` + `innovation_fidelity`
   - `audit-shard-behavioral.json` → 合并到 `behavioral_consistency`
   - `audit-shard-interaction.json` → 合并到 `interaction_type_consistency`
3. 将分片中的 `sections` 内容合并到 `audit-report.json` 的 `summary` 和顶层字段
4. 重新生成 `audit-report.md`（包含全部维度的摘要和问题清单）
5. 删除 `audit-shard-*.json` 分片文件（已合并到主报告）

**合并逻辑**（伪代码）：

```python
report = load_json("audit-report.json")  # Phase A 基线

for shard_name in ["pattern", "behavioral", "interaction"]:
    shard_path = f"audit-shard-{shard_name}.json"
    if not exists(shard_path):
        continue
    shard = load_json(shard_path)
    for section_key, section_data in shard["sections"].items():
        report["summary"][section_key] = {
            k: v for k, v in section_data.items() if k != "issues"
        }
        report[f"{section_key}_issues"] = section_data.get("issues", [])

write_json("audit-report.json", report)
regenerate_markdown("audit-report.md", report)
delete_shards()
```

**quick 模式**: 跳过合并（Phase B 未执行），Phase A 的 audit-report.json 即最终报告。

---

## Step 6：汇总报告

合并三个维度的校验结果，生成最终报告。

**输出文件**：
- `.allforai/design-audit/audit-report.json` — 全量校验结果（机器可读）
- `.allforai/design-audit/audit-report.md` — 人类可读摘要

**JSON Schema**：

```json
{
  "generated_at": "ISO8601",
  "mode": "full|trace|coverage|cross|role",
  "role_filter": "角色名（仅 role 模式）",
  "available_layers": ["product-map", "experience-map", "..."],
  "summary": {
    "trace": { "total": 0, "pass": 0, "orphan": 0 },
    "coverage": { "total": 0, "covered": 0, "gap": 0, "rate": "0%" },
    "cross": { "total": 0, "ok": 0, "conflict": 0, "warning": 0, "broken_ref": 0 },
    "fidelity": {
      "traceability_rate": "0%",
      "traceability_status": "PASS|BELOW_THRESHOLD",
      "viewpoint_coverage_rate": "0%",
      "viewpoint_status": "PASS|BELOW_THRESHOLD"
    },
    "pattern_consistency": {
      "status": "pass|issues_found|skipped",
      "total_patterns_checked": 0,
      "clean_patterns": 0,
      "drift_patterns": 0
    },
    "innovation_fidelity": {
      "status": "pass|issues_found|skipped",
      "core_concepts_total": 0,
      "survived": 0,
      "diluted": 0,
      "incomplete": 0
    },
    "behavioral_consistency": {
      "status": "pass|issues_found|skipped",
      "total_categories_checked": 0,
      "compliant_screens": 0,
      "violating_screens": 0
    },
    "interaction_type_consistency": {
      "status": "pass|issues_found|skipped",
      "total_types_checked": 0,
      "consistent_types": 0,
      "drift_types": 0
    }
  },
  "trace_issues": [
    {
      "check_id": "T1",
      "type": "ORPHAN",
      "source": "experience-map",
      "item_id": "S003",
      "item_name": "界面名",
      "missing_ref": "T999",
      "detail": "screen S003 引用了不存在的 task T999"
    }
  ],
  "coverage_issues": [
    {
      "check_id": "C2",
      "type": "GAP",
      "task_id": "T015",
      "name": "任务名",
      "missing_in": "use-case",
      "detail": "任务 T015 没有对应的用例"
    }
  ],
  "cross_issues": []
}
```

**Markdown 报告结构**：

```markdown
# 设计审计报告

## 摘要

- 执行模式：{mode}
- 可用层：{available_layers}
- 逆向追溯：X 项检查，X PASS，X ORPHAN
- 覆盖洪泛：X 项检查，X COVERED，X GAP，覆盖率 XX%
- 横向一致性：X 项检查，X OK，X CONFLICT，X WARNING，X BROKEN_REF
- 信息保真：追溯完整率 XX%（PASS/BELOW_THRESHOLD） · 视角覆盖率 XX%（PASS/BELOW_THRESHOLD）
- 模式一致性：X 类模式检查，X 漂移（pass/issues_found/skipped）
- 创新保真：X 核心概念，X 存活，X 稀释，X 不完整（pass/issues_found/skipped）
- 行为一致性：X 类别检查，X 合规界面，X 违规界面（pass/issues_found/skipped）
- 交互类型一致性：X 种类型检查，X 漂移（pass/issues_found/skipped）

## 问题清单（按严重度排序）

### CONFLICT（跨层矛盾）
| # | 检查项 | 任务 | 说明 |
|---|--------|------|------|
| ... | ... | ... | ... |

### ORPHAN（无源头）
| # | 检查项 | 来源层 | 项目 | 说明 |
|---|--------|--------|------|------|
| ... | ... | ... | ... | ... |

### GAP（未覆盖）
| # | 检查项 | 任务 | 缺失层 | 说明 |
|---|--------|------|--------|------|
| ... | ... | ... | ... | ... |

### WARNING（风险）
| # | 检查项 | 任务 | 说明 |
|---|--------|------|------|
| ... | ... | ... | ... |

### BROKEN_REF（引用断裂）
| # | 检查项 | 来源 | 说明 |
|---|--------|------|------|
| ... | ... | ... | ... |

### LAYOUT_DRIFT（布局漂移）
| # | 类型 | 界面 | 布局偏差 | 建议 |
|---|------|------|----------|------|
| ... | ... | ... | ... | ... |

### TYPE_CONTEXT_MISMATCH（类型上下文不匹配）
| # | 类型 | 出现次数 | 上下文 | 建议 |
|---|------|----------|--------|------|
| ... | ... | ... | ... | ... |
```
