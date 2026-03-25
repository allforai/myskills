# Enricher Steps — design-to-spec

> This file is loaded by the Enricher Agent (runs in parallel where possible).
> Enricher's job: generate event-schema.json + task-context.json.
> event-schema can parallel Decomposer; task-context must wait for tasks.md.

---

## Step 3.8: 埋点规格生成（Event Schema）

基于 requirements 和 design 产物，自动推导埋点方案。

**输入**：
- requirements.json（用户故事 + 验收标准）
- design.json（API 端点 / 页面路由）
- task-inventory.json（frequency、risk_level）
- experience-map.json（screen actions、on_failure）

**生成规则**：

1. **关键事件推导**（语义分析，非规则映射）：
   - 从 requirements + design + experience-map 中识别值得追踪的用户行为和系统事件
   - 按业务重要性筛选，不机械 1:1 映射（不是每个页面/按钮都需要事件）
   - 事件粒度按产品实际分析需求决定

2. **漏斗定义**：
   - 从 business-flows.json 提取核心流程
   - 每个流程 → 1 个漏斗（funnel）
   - 漏斗节点 = 流程中的关键步骤

3. **事件属性规范**：
   每个事件必须包含：
   - event_name: snake_case 命名
   - event_category: page_view | user_action | form | error | system
   - properties: { key: type } 映射
   - trigger: 触发条件描述
   - requirement_ref: 关联需求 ID
   - screen_ref: 关联界面 ID（前端事件）

4. **北极星指标关联**：
   - 从 product-concept.json 提取 success_metrics（如有）
   - 每个北极星指标 → 关联事件 + 计算公式

**输出**：
```
.allforai/project-forge/sub-projects/{name}/event-schema.json
.allforai/project-forge/sub-projects/{name}/event-schema.md
```

**event-schema.json 结构**：
```json
{
  "sub_project": "admin",
  "generated_at": "ISO8601",
  "events": [
    {
      "event_name": "user_registration_completed",
      "event_category": "user_action",
      "properties": {
        "user_id": "string",
        "registration_method": "string",
        "time_to_complete_ms": "number"
      },
      "trigger": "用户完成注册表单提交且服务端返回成功",
      "requirement_ref": "R-001",
      "screen_ref": "S-003",
      "priority": "P0"
    }
  ],
  "funnels": [
    {
      "funnel_name": "user_onboarding",
      "flow_ref": "F-001",
      "steps": [
        { "step": 1, "event": "landing_page_view", "label": "落地页" },
        { "step": 2, "event": "registration_started", "label": "开始注册" },
        { "step": 3, "event": "registration_completed", "label": "完成注册" },
        { "step": 4, "event": "first_action_completed", "label": "首次操作" }
      ]
    }
  ],
  "metrics": [
    {
      "metric_name": "activation_rate",
      "formula": "count(first_action_completed) / count(registration_completed)",
      "target": "≥ 60%",
      "related_events": ["registration_completed", "first_action_completed"]
    }
  ]
}
```

**event-schema.md** 内容：
- 事件清单表（event_name | category | trigger | priority）
- 漏斗可视化（Mermaid flowchart）
- 指标定义表（metric | formula | target）

→ 写入 .allforai/project-forge/sub-projects/{name}/event-schema.json + event-schema.md
→ 输出进度: 「{name}/event-schema ✓ ({N} events, {M} funnels, {K} metrics)」（不停，汇总到 Step 6）

---

## Step 3.9: Dev Bypass 接口设计

当 `forge-decisions.json` 中 `dev_mode.enabled = true` 时执行，否则跳过。

**生成规则**：

对 dev_mode.bypasses 中每项，在 design.md 中追加 `## Dev Mode Bypass` 章节：

1. **接口隔离设计**：
   - 定义 bypass 接口（与生产接口相同签名）
   - 标注隔离方式：Go build tag (`//go:build dev`) / TS 条件导入 (`process.env.NODE_ENV`)
   - 文件命名约定：`{service}_dev.go` / `{service}.dev.ts`

2. **bypass 行为规格**：
   - 每种策略的具体行为（magic_value 返回什么、auto_callback 延迟多少）
   - 日志输出要求：每次 bypass 执行必须输出 `[DEV_BYPASS] {type}: {action}` 日志

3. **安全守卫设计**：
   - 运行时守卫：非 development 环境加载 dev 文件时 panic/throw
   - 构建时剔除：build tag / tree-shaking 配置
   - CI 规则：扫描 `_dev\.(go|ts|tsx)$` 文件不被生产代码直接 import

输出追加到 design.md 的末尾章节。

Progress: "Dev bypass 接口设计 ✓ ({N} bypasses)"

---

## Step 4.5: 任务上下文预计算（Task Context）

为每个任务预计算完整上下文包，供 task-execute 消费，减少"概念→代码"失真。

**输入**：
- tasks.json（本步骤 Step 4 产出）
- requirements.json（Step 1 产出）
- design.json（Step 3 产出）
- use-case-tree.json（如有）
- journey-emotion.json（如有）
- constraints.json（如有）
- business-flows.json（如有）
- cross-project-dependencies.json（Step 5 产出，第二轮补充）

**生成规则**：

对 tasks.json 中每个任务，计算以下上下文字段：

1. **journey_position**（旅程位置）：
   - 从 use-case-tree.json 查找包含该任务 source_ref 的用例
   - 提取：use_case_id, use_case_name, step_index, total_steps, prev_task, next_task
   - 无匹配 → `null`

2. **emotion_context**（情绪上下文）：
   - 从 journey-emotion.json 查找该任务关联触点的情绪
   - 提取：emotion（期待/满意/焦虑/沮丧）, emotion_intensity(1-5), design_implication
   - 无匹配 → `null`

3. **constraint_rationale**（约束溯源）：
   - 对 task.guardrails 中每条规则，反查 constraints.json 找到来源约束
   - 输出：{ rule_text: string, constraint_refs: [{ id, name, reason, severity }] }

4. **consumers**（消费者清单）：
   - 对后端 API 任务：从其他子项目的 design.json 扫描引用该端点的前端页面
   - 输出：[{ sub_project, screen_id, usage_description }]
   - 前端任务 → `[]`

5. **frequency_weight**（流量权重）：
   - 从 task-inventory.json 提取 frequency 字段
   - 映射：daily+ → "critical", weekly → "high", monthly → "medium", rare → "low"

6. **risk_level**（风险等级）：
   - 直接从 task-inventory.json 提取

7. **verification_hint**（验证建议）：
   - frequency_weight=critical + risk_level=high → "integration_test + load_test"
   - frequency_weight=critical → "integration_test"
   - risk_level=high → "unit_test + code_review"
   - 其他 → "unit_test"

8. **flow_position**（业务流位置）：
   - 从 business-flows.json 查找包含该任务的流程
   - 提取：flow_id, flow_name, position_in_flow, upstream_tasks, downstream_tasks

**输出**：
```
.allforai/project-forge/sub-projects/{name}/task-context.json
```

```json
{
  "sub_project": "backend",
  "generated_at": "ISO8601",
  "contexts": [
    {
      "task_id": "BE-T001",
      "journey_position": {
        "use_case_id": "UC-003",
        "use_case_name": "用户下单流程",
        "step_index": 2,
        "total_steps": 5,
        "prev_task": "BE-T000",
        "next_task": "BE-T002"
      },
      "emotion_context": {
        "emotion": "anxious",
        "emotion_intensity": 4,
        "design_implication": "需要明确的进度反馈和错误恢复"
      },
      "constraint_rationale": [
        {
          "rule_text": "确认后不可变",
          "constraint_refs": [
            { "id": "CN-005", "name": "GDPR 合规", "reason": "审计追踪完整性", "severity": "critical" },
            { "id": "CN-008", "name": "反欺诈", "reason": "防止数据篡改", "severity": "high" }
          ]
        }
      ],
      "consumers": [
        { "sub_project": "web-customer", "screen_id": "S-003", "usage_description": "核心业务表单提交" },
        { "sub_project": "mobile-app", "screen_id": "S-M012", "usage_description": "移动端提交" }
      ],
      "frequency_weight": "critical",
      "risk_level": "high",
      "verification_hint": "integration_test + load_test",
      "flow_position": {
        "flow_id": "F-002",
        "flow_name": "核心业务处理流程",
        "position_in_flow": 2,
        "upstream_tasks": ["BE-T000"],
        "downstream_tasks": ["BE-T002", "BE-T005"]
      }
    }
  ]
}
```

→ 写入 .allforai/project-forge/sub-projects/{name}/task-context.json
→ 输出进度: 「{name}/task-context.json ✓ ({N} tasks enriched, {M} with journey, {K} with constraints)」（不停，汇总到 Step 6）
