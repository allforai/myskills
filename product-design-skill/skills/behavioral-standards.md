---
name: behavioral-standards
description: >
  Use when "行为规范", "行为一致性", "behavioral standards", "behavioral consistency",
  "交互一致性", "删除确认规范", "空状态规范", "加载模式规范", or automatically called by
  product-design Phase 3.6. Scans experience-map to detect cross-screen behavioral inconsistencies
  (delete confirmation, empty states, loading patterns, error display, form validation, etc.),
  proposes product-level standards via ONE-SHOT confirmation, then writes
  behavioral-standards.json (including screen behavioral tag mappings) + behavioral-standards-report.md.
  Does NOT modify upstream files.
version: "1.0.0"
---

# Behavioral Standards — 产品行为规范

> 扫描 experience-map → 检测跨界面行为不一致 → 用户确认 → 输出 behavioral-standards.json（含界面标签映射）+ behavioral-standards-report.md

## 目标

在 UI 设计开始前识别产品中跨界面的行为不一致，通过统一标准保证"同类交互同种体验"：

1. **扫描** — 读取 experience-map.json，检测 9 类行为不一致
2. **用户确认** — ONE-SHOT 展示分析结果（唯一停顿点）
3. **写入** — 生成 behavioral-standards.json（含 screen 标签映射）+ behavioral-standards-report.md

---

## 定位

```
Phase 4: experience-map → experience-map.json              ← 输入
Phase 4.5: interaction-gate → gate-report.json      ← 可选输入
Phase 4.6: behavioral-standards → behavioral-standards.json ← 本技能
Phase 5-8: 并行组（ui-design 消费 behavioral-standards）    ← 下游
Phase 9: design-audit → Behavioral Consistency 维度        ← 事后
```

**前提**：
- 必须有 `.allforai/experience-map/experience-map.json`（来自 experience-map）
- 可选有 `.allforai/design-pattern/pattern-catalog.json`（来自 design-pattern，增强分析）

---

## 工作流

```
Preflight: 检查前置文件存在性
    ↓ 自动
Step 1: 行为扫描（扫描 experience-map，分类 9 类行为方案）
    ↓ 自动
Step 2: ONE-SHOT 用户确认（唯一停顿点）
    ↓ 用户确认后
Step 3: 写入产物（自动，不停顿）
```

---

## Preflight: 前置检查

检查必需文件：
- `.allforai/experience-map/experience-map.json` — 不存在 → 输出「请先完成 Phase 4（experience-map）」，终止

可选加载：
- `.allforai/design-pattern/pattern-catalog.json` — 存在 → 加载，用于增强行为检测（如 PT-CRUD 实例的删除确认分析）；不存在 → 跳过

---

## Step 1: 行为扫描

> 目标：检测 experience-map.json 中跨界面的 9 类行为不一致。

对每个界面，提取 `states`、`actions`、`requires_confirm`、`on_failure`、`validation_rules` 等字段，分类归入行为类别。

### 9 类行为类别

| ID | 名称 | 检测来源 | 统一什么 |
|----|------|----------|----------|
| `BC-DELETE-CONFIRM` | 破坏性操作确认 | `requires_confirm` + `crud=D` actions | 弹窗确认 vs 行内确认 vs 无确认 |
| `BC-EMPTY-STATE` | 空状态展示 | `states.empty` across screens | 图文引导 vs 纯文字 vs 空白 |
| `BC-LOADING` | 加载模式 | `states.loading` across screens | 骨架屏 vs 转圈 vs 渐进加载 |
| `BC-ERROR-DISPLAY` | 错误展示 | `states.error` across screens | Toast vs 行内提示 vs 整页错误 |
| `BC-FORM-VALIDATION` | 表单校验反馈 | `validation_rules` + `on_failure` | 实时校验 vs 提交时校验 vs 混合 |
| `BC-SUCCESS-FEEDBACK` | 成功反馈 | action success handling | Toast vs 跳转 vs 行内反馈 |
| `BC-PERMISSION-DENIED` | 权限不足 | `states.permission_denied` | 重定向 vs 禁用/灰化 vs 隐藏 |
| `BC-PAGINATION` | 分页行为 | list/table screens | 无限滚动 vs 分页器 |
| `BC-UNSAVED-GUARD` | 未保存变更守卫 | screens with `crud=U` | 浏览器原生提示 vs 自定义弹窗 vs 无守卫 |

**扫描逻辑**：
1. 遍历所有 screens
2. 对每个 screen，提取相关字段（states, actions, requires_confirm, on_failure, validation_rules）
3. 通过关键词匹配（中英文）分类当前方案
4. 计算每个类别的跨界面分布
5. 提出推荐标准：多数方案 >= 60% → 推荐采用；否则标记待用户决策

**跳过条件**：
若某行为类别影响界面 < 3 个，或所有界面方案完全一致（无分歧 > 30%），跳过该类别。

若所有 9 类均跳过 → 输出「Phase 3.6: 所有行为模式一致，跳过」，不生成产物文件。

---

## Step 2: ONE-SHOT 用户确认（唯一停顿点）

展示完整扫描结果，一次性收集用户决策。

**展示格式**：

```markdown
## Phase 3.6 — 产品行为规范分析

### 检测到的行为不一致（{N} 类）

| 类别 | 影响界面数 | 方案分布 | 推荐标准 |
|------|-----------|---------|---------|
| 破坏性操作确认 | 12 | modal_confirm(5) / no_confirm(7) | modal_confirm |
| 空状态展示 | 8 | illustration_text(3) / text_only(5) | text_only |
| 加载模式 | 15 | skeleton(10) / spinner(5) | skeleton |

### 推荐标准详情

#### BC-DELETE-CONFIRM: 破坏性操作确认
- **推荐**: modal_confirm — 所有 crud=D 或高风险操作使用模态弹窗确认
- **当前分布**: 5 个界面用弹窗确认，7 个界面无确认
- **例外**: 批量操作可使用 inline 确认条

#### BC-EMPTY-STATE: 空状态展示
- **推荐**: text_only — 统一使用引导文案
- **当前分布**: 3 个界面用图文引导，5 个界面用纯文字

### 一致的类别（无需标准化）
- BC-PAGINATION — 所有列表界面均使用分页器
- BC-PERMISSION-DENIED — 所有界面统一禁用/灰化处理
```

用 **AskUserQuestion** 确认推荐标准：

```
确认以上行为规范推荐？可逐条调整或整体确认。
```

---

## Step 3: 写入产物（自动，不停顿）

用户确认后，自动执行以下操作，不再停顿。不修改任何上游文件。

### 3a. 写入 `behavioral-standards.json`

```json
{
  "created_at": "ISO8601",
  "total_categories_detected": 7,
  "categories": [
    {
      "category_id": "BC-DELETE-CONFIRM",
      "name": "破坏性操作确认",
      "detection_summary": {
        "total_screens_affected": 12,
        "approach_distribution": {
          "modal_confirm": { "count": 5, "screen_ids": ["S001", "..."] },
          "no_confirm": { "count": 7, "screen_ids": ["S002", "..."] }
        }
      },
      "recommended_standard": {
        "approach": "modal_confirm",
        "description": "所有 crud=D 或 risk_level>=中 的操作使用模态弹窗确认",
        "exceptions": "批量操作使用 inline 确认条"
      },
      "user_decision": "confirmed"
    }
  ],
  "screen_behavioral_tags": {
    "S001": {
      "_behavioral": ["BC-DELETE-CONFIRM", "BC-EMPTY-STATE"],
      "_behavioral_standards": {
        "BC-DELETE-CONFIRM": "modal_confirm",
        "BC-EMPTY-STATE": "illustration_text"
      }
    }
  },
  "screens_tagged": 20,
  "inconsistencies_found": 3,
  "inconsistencies_resolved": 3
}
```

- `screen_behavioral_tags` — 键为 screen_id，值含 `_behavioral`（类别 ID 列表）和 `_behavioral_standards`（该界面应遵循的标准方案）
- 下游技能通过 `screen_behavioral_tags[screen_id]` 查找行为标准

### 3b. 写入 `behavioral-standards-report.md`

人类可读摘要，不重复 JSON 的完整数据，只呈现关键统计和决策。

**输出**：`Phase 3.6 ✓ {N} 类行为不一致，标注 {M} 个 screens，{K} 处不一致已解决`，自动继续。

---

## 全自动模式

**激活条件**（同时满足）：
1. `.allforai/product-concept/product-concept.json` 存在且含 `pipeline_preferences` 字段
2. 上下文含 `__orchestrator_auto: true`（由 `/product-design full` 编排器传入）

**未同时满足** → 保持标准交互模式（当前行为不变）。

**行为变化**：

| 步骤 | 标准模式 | 全自动模式 |
|------|----------|-----------|
| **Step 2 用户确认** | AskUserQuestion 确认 | 自动确认（多数方案自动采用），记入 `pipeline-decisions.json` |

**安全护栏**（自动模式下仍然停下来问用户）：
- 某类别无明显多数方案（所有方案均 < 60%）→ 回退交互模式

---

## 预置脚本（优先使用）

检查 `${CLAUDE_PLUGIN_ROOT}/scripts/gen_behavioral_standards.py` 是否存在：
- **存在** → `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gen_behavioral_standards.py <BASE> --mode auto [--shard behavioral-standards]`
- **不存在** → 回退到 LLM 生成（向后兼容）

预置脚本保证 schema 一致性和零语法错误。支持 `--shard` 参数用于并行流水线集成。

---

## 输出文件

```
.allforai/behavioral-standards/
├── behavioral-standards.json          # 主产物（JSON 机器版，含 screen 标签映射）
└── behavioral-standards-report.md     # 人类可读摘要
```

不修改上游文件（experience-map.json）。下游技能通过 behavioral-standards.json 中的 `screen_behavioral_tags` 查找行为标准。

---

## 3 条铁律

### 1. 用户只停顿一次

Step 2 是唯一的用户交互点。Step 1 全自动执行，Step 3 用户确认后全自动完成，不再询问。

### 2. 只读不改上游

行为标准数据写入独立文件 behavioral-standards.json（含 `screen_behavioral_tags` 映射），不修改 experience-map.json。

### 3. 无不一致时优雅跳过

若扫描后所有 9 类行为类别均一致或影响界面不足 3 个，直接输出「Phase 3.6 ✓ 所有行为模式一致，跳过」，不生成 behavioral-standards.json（下游技能将判断文件是否存在）。
