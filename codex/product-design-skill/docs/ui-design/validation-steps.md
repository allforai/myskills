# UI Design — Validation Steps

> Steps that validate, audit, and enforce consistency on design output.
> Loaded by `skills/ui-design.md` orchestrator.

---

## Step 4.5：Pattern Consistency Check

扫描本次已生成的所有界面设计，使用 experience-map.json 的 screen._pattern* 字段进行模式一致性检查：

**检测 1**: 同 `_pattern_group` 的界面是否使用了一致的主布局（顶部栏/侧边栏/主内容区比例相同）
  → 不一致 → 自动对齐到该 group 中最先生成的界面的布局
  → 记录调整: `pattern_alignment: [screen_id → aligned to screen_id]`

**检测 2**: 同一模式类型（如 PT-CRUD）的界面是否使用了相同的操作按钮位置（新建/编辑/删除）
  → 不一致 → 自动统一到推荐位置（右上角主操作 + 行内次操作）
  → 记录调整同上

**检测 3**: 同一审批流（PT-APPROVAL）的状态标签颜色体系是否统一（待审=黄/通过=绿/拒绝=红）
  → 不一致 → 标记为 WARNING，在 ui-design-spec.md 中备注「需统一颜色体系」

**检测 4**: 同一 `interaction_type` 的界面布局一致性检查
  检查所有 interaction_type 相同的界面：
    → 布局模式是否一致（如所有 `MG1` 都使用 侧边导航+表格区）
    → 关键区域划分是否一致（如所有 `MG2` 的新建按钮位置统一）
    → 不一致 → 自动对齐到该类型的推荐布局（见 `docs/interaction-types.md`）
    → 记录调整同上

**检测 5**: 行为规范合规检查
  对每个有 screen._behavioral_standards 字段的界面：
    检查生成的设计是否匹配标准方案（如 BC-LOADING 标准为 skeleton，但设计中写了 spinner → 不匹配）
    不匹配 → `BEHAVIORAL_DRIFT` 告警，记录到模式一致性记录中
    匹配 → 无操作

结果追加到 ui-design-spec.md 末尾的「模式一致性记录」章节：

```markdown
## 模式一致性记录

| Pattern Group | 对齐项目 | 调整说明 |
|--------------|---------|---------|
| records-crud | 操作按钮位置 | 统一到右上角主操作 |
| approval-flows | 状态标签颜色 | ⚠ 需在组件库中统一 |
```

不阻塞，自动继续输出最终 ui-design-spec.md。

---

## Step 4.7：LLM 自审验证（Loop）

设计规格生成后，LLM 切换审查者视角，对照上游基线验证设计意图还原度。

**上游基线验收（experience-map.json）**：

LLM 同时持有 experience-map.json（上游）和 ui-design-spec.md（当前产出），逐界面对照审查：

| 审查视角 | LLM 判断什么 |
|---------|-------------|
| 交互意图还原 | experience-map 中 screen 的 `interaction_pattern` 和 `description` 的设计意图，是否在 UI 规格的布局、组件、交互描述中有实质性体现？ |
| 情绪设计落地 | screen 的 `emotion_design` 中的情绪引导（如「减少焦虑感」「营造成就感」），是否在配色、留白、反馈机制中有对应设计？ |
| 创新概念保真 | `innovation_ui: true` 的界面是否保留了跨领域参考特征？还是退化为普通 CRUD？ |
| 高风险安全 | experience-map 中高风险操作（删除、提交、权限变更），UI 规格是否包含确认弹窗、撤销入口、错误恢复？ |
| 数据字段完整 | experience-map screen 的 `data_fields` 是否在 UI 规格中有对应的表单/展示组件？ |

**4D+6V 追问**（对 FAIL 的界面）：
- D2: 哪个上游字段/意图被遗漏或走样？
- D4: 是设计取舍还是疏忽？如果是取舍需记录理由

**Loop 机制**：

```
生成 UI 规格 → 上游基线验收
  全部通过 → Step 5
  不通过 →
    列出具体问题（哪些界面的设计意图未还原、哪些创新概念退化）
    LLM 修正对应界面规格
    → 重新验收（最多 2 轮）
  2 轮后仍不通过 → 记录剩余问题，WARNING 继续
```

---

## 闭环审计

LLM 生成 UI 设计后，追问闭环完整性：

| 闭环类型 | 追问 |
|---------|------|
| **导航闭环** | 每个界面是否有明确的返回/退出路径？是否存在导航死胡同（进得去出不来）？ |
| **异常闭环** | 每个表单/操作界面是否设计了错误状态和恢复路径？网络异常时用户看到什么？ |
| **映射闭环** | 每个 experience-map 中定义的 screen 是否在 UI 规格中有对应设计？ |

闭环缺失 → LLM 补充对应设计 → 重新验证。

---

## 防御性规范

> 通用模式定义见 `docs/defensive-patterns.md`，以下为本技能的具体应用。

### 加载校验
- **`ui-design-decisions.json`**：加载时用 `python -m json.tool` 验证 JSON 合法性。解析失败 → 检查 `.bak` → 提示恢复或重新运行 `/ui-design refresh`。
- **`product-map.json` / `task-inventory.json`**：前置加载时验证 JSON 合法性。解析失败 → 提示用户重新运行 `/product-map`，终止执行。

### 零结果处理
- **无 experience-map 且无高/中频任务**：⚠ 明确告知「无法推导界面列表 — experience-map 不存在，且 task-inventory 中无高/中频任务可用于推导界面。请先执行 experience-map 或 /product-map 补充任务频次」，**终止执行**（不生成空规格）。
- **Step 1 推导 0 界面**：同上处理。
- **Step 3 搜索 0 设计原则**：若搜索正常但无有用结果 → 告知用户，提供选项：(a) 使用所选风格的默认 CSS 变量 (b) 用户手动提供设计参考。

### 规模自适应
- **阈值**：以界面数为计量对象（来自 experience-map 或推导数量）。small ≤15 / medium 16–40 / large >40。
- **small**（≤15 界面）：逐界面生成设计规格，逐步确认。
- **medium**（16–40 界面）：按模块分组生成规格，摘要确认。
- **large**（>40 界面）：脚本生成规格文件 + 仅展示高频界面预览。

### 网络搜索不可用
- **Step 3 设计原则搜索**：
  - 工具不可用 → 告知用户「⚠ 网络搜索暂不可用」→ 提供选项：(a) 跳过搜索，使用风格默认 CSS 变量参数 (b) 用户手动提供设计参考 URL。
  - **品牌定制风（Brand Custom）+ 搜索无结果**：回退到 Flat/Minimal 风格的默认 CSS 变量 + ⚠ 警告「品牌定制风搜索无结果，已回退到 Flat/Minimal 默认参数，建议用户后续提供品牌设计规范」。

### 上游过期检测
- **`experience-map.json`**（若存在）：加载时比较 `generated_at` 与 `ui-design-decisions.json` 最新 `decided_at`。上游更新 → ⚠ 警告「experience-map 在 ui-design 上次运行后被更新，界面列表可能过期，建议重新执行 ui-design refresh」。
- **`task-inventory.json`**：同理检查时间戳。
- 仅警告不阻断。

### 执行失败保护

- 任何步骤遇到不可恢复错误 → 写入 `.allforai/ui-design/ui-design-error.json`，包含 `{"error": "...", "step": "...", "timestamp": "..."}`。
