# 界面地图 Schema（screen-map.json + screen-index.json）

## 界面 Schema（screen-map.json）

> 以下示例以虚构业务为背景，仅用于说明输出格式。实际内容由 screen-map 分析结果决定，不限行业。
> **交互类型推断**：每个界面基于其 actions 自动推断 `interaction_type`，规则详见 `docs/interaction-types.md`。

```json
{
  "screens": [
    {
      "id": "S001",
      "name": "场景流首页",
      "description": "用户进入 APP 后直接开始场景对话，无课程概念",
      "interaction_type": "MG1",
      "innovation_screen": true,
      "adversarial_concept_ref": "IC001",
      "innovation_direction": "去课程化学习",
      "primary_purpose": "让用户像刷抖音一样刷场景学习",
      "primary_action": "上下滑动切换场景",
      "entry_point": "打开 APP 直接进入",
      "audience_type": "consumer",
      "tasks": ["T001"],
      "states": {
        "empty": "暂无退款申请，提示用户新建",
        "loading": "表单加载中，显示骨架屏",
        "error": "网络错误，显示重试按钮",
        "permission_denied": "权限不足，跳转到错误页"
      },
      "actions": [
        {
          "label": "提交退款申请",
          "crud": "C",
          "frequency": "高",
          "click_depth": 1,
          "is_primary": true,
          "roles": ["R001"],
          "requires_confirm": false,
          "on_failure": "高亮必填字段，顶部显示错误汇总",
          "validation_rules": ["金额 > 0", "金额 ≤ 原订单金额", "退款原因必填"],
          "exception_flows": [
            "订单已全额退款 → 顶部红色提示「该订单已全额退款，不可重复申请」",
            "支付信息缺失 → 弹窗提示「支付信息异常，请联系技术支持」附工单入口",
            "权限不足 → 按钮置灰，hover 显示「请申请退款权限」"
          ]
        },
        {
          "label": "撤回退款",
          "crud": "D",
          "frequency": "低",
          "click_depth": 2,
          "is_primary": false,
          "roles": ["R001", "R002"],
          "requires_confirm": true,
          "on_failure": "提示撤回失败原因（如：审批已完成，无法撤回）",
          "validation_rules": [],
          "exception_flows": []
        }
      ],
      "pareto": {
        "high_freq_actions": ["提交退款申请"],
        "low_freq_buried": [],
        "high_freq_buried": []
      },
      "flags": []
    }
  ]
}
```

**帕累托计算方法**：将该界面内所有按钮按 `frequency` 降序排列，累计占比达到 80% 的按钮标记为 `high_freq_actions`。`click_depth ≥ 3` 的高频按钮标记为 `high_freq_buried`；`click_depth ≤ 1` 的低频按钮标记为 `low_freq_buried`（疑似冗余快捷入口）。

## 界面字段说明

| 字段 | 含义 |
|------|------|
| `interaction_type` | 页面交互类型：`MG1 / MG2(MG2-L/D/C/E/ST) / MG3 / MG4 / MG5 / MG6 / MG7 / MG8 / CT1–CT8 / EC1–EC3 / WK1–WK7 / RT1–RT4 / SB1 / SY1–SY2 / TU1–TU4`。由 actions 自动推断（规则见 `docs/interaction-types.md`），组合类型用数组表示。PM 可覆盖 |
| `primary_purpose` | 这个页面最重要的目标（用户视角一句话） |
| `primary_action` | 频次最高的操作，由帕累托分析自动推导，PM 可调整 |
| `states` | 界面的各类状态：`empty`（空数据）/ `loading`（加载中）/ `error`（错误）/ `permission_denied`（无权限）等 |
| `audience_type` | 界面受众类型：`consumer` / `professional` / `default`，由关联角色自动推导 |
| `innovation_screen` | `true` / `false` — 是否为创新概念定义的界面（自动推导） |
| `adversarial_concept_ref` | 指向 `adversarial-concepts.json` 的概念 ID（如 `IC001`） |
| `innovation_direction` | 创新方向描述（如"去课程化学习"、"紧急场景速成"） |

## 按钮字段说明

| 字段 | 含义 |
|------|------|
| `label` | 按钮文字（界面上显示的） |
| `crud` | `C` 新增 / `R` 查看 / `U` 修改 / `D` 删除 |
| `frequency` | 操作频次：高 / 中 / 低 |
| `click_depth` | 触达该按钮需要几次点击（1=直接可见，2=需要展开，3+=深度隐藏） |
| `is_primary` | 由频次自动推导（frequency=高 且 click_depth 在受众档案范围内：consumer/default ≤ 1，professional ≤ 2），PM 可覆盖 |
| `roles` | 哪些角色可见/可操作此按钮 |
| `requires_confirm` | 是否需要二次确认弹窗 |
| `on_failure` | 操作失败时界面如何响应（提示文案、高亮字段、错误位置） |
| `validation_rules` | 前端校验规则列表（表单提交前执行） |
| `exception_flows` | 每条对应 task.exceptions 中一个异常的界面处理方式 |

**以下字段必须显式生成，不得省略**：
- `is_primary`: true/false（由频次自动推导，但必须显式写入）
- `on_failure`: string（无则 `""`）
- `on_success`: string（无则 `""`）
- `requires_confirm`: true/false
- `validation_rules`: []（无则空数组）
- `exception_flows`: []（无则空数组）

**字段名规范**：screen-map.json 中用 `tasks`（任务 ID 列表），screen-index.json 中用 `task_refs`。两处含义相同，名称不同是因为索引层简写。

---

## `screen-index.json` Schema

从 `screen-map.json` 提取关键字段，按模块分组。模块归组：按关联任务的 `name` 语义聚类，与 `task-index.json` 的模块一致。

```json
{
  "generated_at": "2026-02-25T10:00:00Z",
  "source": "screen-map.json",
  "screen_count": 12,
  "concept_eliminated_count": 2,
  "innovation_count": 3,
  "modules": [
    {
      "name": "退款管理",
      "screens": [
        {
          "id": "S001",
          "name": "退款申请页",
          "task_refs": ["T001"],
          "action_count": 2,
          "audience_type": "professional",
          "interaction_type": "MG3",
          "has_gaps": false
        }
      ]
    }
  ]
}
```

`has_gaps` 判定：界面存在任一 flag（`OVERLOADED`、`HIGH_FREQ_BURIED`、`PRIMARY_MISMATCH`、`ORPHAN`、`CONCEPT_ELIMINATED`、`NO_ENTRY`）或任一按钮缺少 `on_failure` 定义时为 `true`。

**生成规则**：
- 索引随 Step 1 输出一起生成
- `scope` 模式下索引仍生成完整内容，确保下游技能自行筛选
- 下游技能加载索引时若发现索引不存在，回退到全量加载，行为与旧版完全一致
