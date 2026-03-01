# 信息保真方法论（提高维度 + 多视角 + 跨模型）

> 目标：降低 `concept → map → screen → use-case → gap → prune → ui-design → audit` 的信息丢失与失真。

## 核心思想

信息从上游传到下游时，若只传「结论」，会不可避免地被压缩。为避免失真，统一采用三条原则：

1. **提高维度（4D）**：每条关键结论都携带上下文，而不是只有一句话结果。
2. **多视角（6V）**：同一对象至少从多个独立视角描述，避免单视角偏见。
3. **跨模型验证（XV）**：用不同 AI 模型交叉审视同一产物，弥补单一模型的知识偏差和推理盲区。

---

## 一、4D 信息卡（提高维度）

每个关键对象（任务/界面/用例/决策）建议带 4 层信息：

- **D1 结论层**：是什么（结论本身）
- **D2 证据层**：基于什么（来源与事实）
- **D3 约束层**：边界是什么（业务/技术/合规）
- **D4 决策层**：为什么这么定（取舍与理由）

建议最小字段（跨阶段通用）：

```json
{
  "source_refs": ["来源URL或产物ID"],
  "assumptions": ["关键假设"],
  "constraints": {
    "business": ["..."],
    "technical": ["..."],
    "risk": ["..."]
  },
  "decision_rationale": "为什么这么定",
  "confidence": 0.0,
  "owner": "角色或负责人"
}
```

---

## 二、6V 视角矩阵（多视角）

建议统一 6 个视角（可按阶段裁剪）：

- `user`：用户价值
- `business`：业务价值
- `tech`：技术可行
- `ux`：体验可用
- `data`：可观测与指标
- `risk`：风险与合规

建议最小结构：

```json
{
  "viewpoints": {
    "user": {"success": "...", "risk": "...", "validation": "..."},
    "business": {"success": "...", "risk": "...", "validation": "..."},
    "tech": {"success": "...", "risk": "...", "validation": "..."},
    "ux": {"success": "...", "risk": "...", "validation": "..."},
    "data": {"success": "...", "risk": "...", "validation": "..."},
    "risk": {"success": "...", "risk": "...", "validation": "..."}
  }
}
```

---

## 三、XV 跨模型验证

### 原理

4D 和 6V 提升了**单模型输出的信息密度**，但无法消除单一模型的系统性偏差 — 训练数据的知识偏向、推理路径的盲区、文化语境的局限。XV 通过引入第二个独立模型对关键产物进行审视，实现"换人看"效果：

- **知识互补**：不同模型在不同领域的训练深度各异，交叉验证可发现单模型遗漏的行业知识和边界条件。
- **推理多样性**：不同模型的推理风格（严谨/发散/结构化）可互相补充，降低单一推理路径的系统偏差。
- **置信度校准**：当两个模型对同一结论一致时，置信度提升；不一致时，暴露需要人工关注的争议点。

### 自动化策略

XV 验证完全自动、完全可选：

- **工具检测**：每个阶段在指定 Step 完成后，检测 `mcp__openrouter__ask_model` 工具是否可用。
- **可用时**：自动发起交叉验证调用，将结果写入产出的 `cross_model_review` 字段。不停下来询问用户。
- **不可用或调用失败时**：自动跳过，不阻塞流程，不生成 `cross_model_review` 字段。产出与未启用 XV 时完全一致。

### 调用方式

使用 `mcp__openrouter__ask_model` 工具，传入：

| 参数 | 说明 |
|------|------|
| `task_type` | 匹配 `defaults.ts` 中的路由键，自动选择模型（如 `competitive_analysis` → gemini） |
| `message` | 发送给验证模型的提示，包含当前阶段的关键产物摘要和验证问题 |

每阶段通常发起 2 次调用（不同 task_type），覆盖不同验证维度。

### 输出字段

验证结果统一写入产出 JSON 的顶层 `cross_model_review` 对象：

```json
{
  "cross_model_review": {
    "generated_at": "ISO timestamp",
    "reviews": [
      {
        "task_type": "competitive_analysis",
        "model_used": "gemini",
        "findings": ["发现1", "发现2"],
        "confidence": "high | medium | low"
      }
    ]
  }
}
```

---

## 四、在 8 阶段中的最小落地

- `product-concept`：结论外必须附带「证据 + 假设 + 反假设」。XV：Step 4 后由 gemini 挑战假设、gpt 验证用户画像。
- `product-map`：每个任务附 `decision_rationale` 与至少 4 个视角。XV：Step 5 后由 gemini 审查任务完整性、gpt 检测隐藏冲突。
- `screen-map`：每个界面附「用户目标 + 失败恢复 + 风险提示」。XV：Step 2 后由 gpt 审查 UX 一致性、gemini 检查无障碍缺陷。
- `use-case`：每条用例补「业务成功 + 技术成功 + 体验成功」三重 then。XV：Step 3 后由 deepseek 补充边界条件、gpt 审查验收标准。
- `feature-gap`：缺口按视角分类（user/business/tech/ux/data/risk）。XV：Step 4 后由 gemini 验证旅程断点、gpt 修正优先级。
- `feature-prune`：每个 `DEFER/CUT` 必须有替代路径和延迟成本说明。XV：Step 4 后由 deepseek 挑战误剪、gemini 补充竞品参照。
- `ui-design`：每个关键界面保留设计决策理由与可访问性约束。XV：Step 4 后由 gpt 审查视觉层级、gemini 检测一致性缺陷。
- `design-audit`：新增「追溯完整率 + 视角覆盖率」门禁。XV：Step 3 后由 gpt 验证跨层矛盾、deepseek 补充覆盖盲区。

---

## 五、推荐门禁指标

1. **Traceability 完整率**：下游对象能追溯到上游证据的比例，建议 `>= 95%`。
2. **Viewpoint 覆盖率**：关键对象覆盖至少 4/6 视角的比例，建议 `>= 90%`。

这两个指标可作为现有 ORPHAN / COVERAGE / CONFLICT 的补充门禁。

---

## 六、创新概念的信息保真

> 核心原则：**创新保真 ≠ 特殊处理**，而是通过提高信息敏感度确保 4D+6V+XV 协议有效执行。

创新概念是产品差异化的核心，在信息传递链中需要特殊保护。本节定义创新概念从 `product-concept` 到 downstream 各阶段的信息保真机制。

### 6.1 源头标记（product-map）

product-map 阶段负责将 `product-concept` 中定义的创新概念标记为特殊任务，供下游技能识别。

**读取输入**：
- `.allforai/product-concept/adversarial-concepts.json` 的 `concepts[]` 数组
- `.allforai/product-concept/product-concept.json` 的 `innovation_preferences` 字段

**输出标记**：
```json
{
  "innovation_tasks": [
    {
      "task_id": "T001",
      "source": "concept_defined",
      "protection_level": "core",
      "innovation_score": 9,
      "adversarial_concept_ref": "IC001"
    }
  ]
}
```

**保护级别语义**：
| 级别 | 含义 | downstream 影响 |
|------|------|----------------|
| `core` | 核心创新，产品差异化根本 | 不可剪枝、优先实现、ERROR 级完整性要求 |
| `defensible` | 防御性创新，可增强竞争力 | 用户确认、WARNING 级完整性要求 |
| `experimental` | 实验性创新，可探索 | INFO 级完整性要求、允许延后 |

---

### 6.2 下游传递（按技能拆分）

#### 6.2.1 screen-map 阶段
- **读取**：`task-inventory.json` 的 `innovation_tasks` 字段
- **输出**：界面 Schema 增加 `innovation_screen: true` + `adversarial_concept_ref: IC001`
- **自动推导**：任务 `innovation_task=true` → 界面 `innovation_screen=true`
- **保真关键位**：`on_failure` / `exception_flows` 缺失 → 优先级提升一级

#### 6.2.2 ui-design 阶段
- **读取**：`task-inventory.json` 的 `innovation_tasks` 字段
- **输出**：设计规格增加「创新概念 UI 规格」专节
- **设计原则**：必须体现跨领域参考（如"抖音"、"游戏赛季"）

#### 6.2.3 task-execute 阶段
- **读取**：`tasks.md` 的 `_Source: T001_` + `task-inventory.json` 的 `innovation_tasks`
- **优先级修正**：`core` → Round 1，`defensible` → Round 2，`experimental` → Round 3+
- **验证增强**：创新任务必须动态验收（不能只静态扫描）

#### 6.2.4 feature-prune 阶段
- **读取**：`task-inventory.json` 的 `innovation_tasks` 字段
- **剪枝修正**：`core` 跳过频次过滤，自动 CORE；`defensible` 用户确认
- **延迟成本**：`core`=高，`defensible`=中，`experimental`=低

#### 6.2.5 design-audit 阶段
- **读取**：`innovation_tasks` + 各层创新标记
- **审计增强**：追溯完整率（创新任务有下游产物）、视角覆盖率（6/6 视角）
- **保真门禁**：追溯完整率 >= 95%，视角覆盖率 >= 90%

---

### 6.3 核心原则

1. **高敏感度 ≠ 特殊处理**：显式读取 `innovation_task` 字段，自动标注创新标记
2. **可追溯**：创新概念的所有下游产物必须可追溯到 `adversarial-concepts.json`
3. **多视角**：创新界面强制覆盖 6/6 视角（常规界面 4/6 即可）
4. **交叉验证**：创新概念需要专用 XV 验证（`innovation_review` / `innovation_design_review` / `innovation_priority_review`）

---

### 6.4 信息失真模式与防护

| 失真模式 | 发生阶段 | 防护措施 |
|---------|---------|---------|
| 创新稀释 | screen-map / ui-design | 标注 `innovation_screen` + `adversarial_concept_ref` |
| 创新延后 | task-execute | `protection_level` → Round 优先级映射 |
| 创新误剪 | feature-prune | `core` 跳过频次过滤 |
| 创新误解 | 全部阶段 | 6V 强制覆盖 + XV 验证 |
| 创新孤立 | design-audit | 追溯完整率 >= 95% 门禁 |

---

### 6.5 量化指标

| 指标 | 目标值 | 最低门禁 | 计算方式 |
|------|-------|---------|---------|
| 创新任务追溯完整率 | 100% | >= 95% | 有下游的创新任务数 / 创新任务总数 |
| 创新概念视角覆盖率 | 100% | >= 90% | 覆盖 6/6 视角的创新界面数 / 创新界面总数 |
| 创新任务 Round 1 完成率 | 100%（core） | 不可低于 100% | Round 1 完成的 core 任务数 / core 任务总数 |
| 创新界面保真度 | >= 9/10 | >= 8/10 | AI 评分：界面设计是否体现创新方向 |

---

### 6.6 状态闭环保真（新增，通用版）

**核心原则**：每个状态必须有生产者 + 消费者，形成完整闭环（不依赖特定行业）

**检测机制**：
- **product-concept**：定义创新概念的状态机（初始状态 → 中间状态 → 终止状态）
- **product-map**：粗粒度统计（0 次引用/0 次产生的状态）
- **feature-gap**：细粒度验证（孤儿状态/幽灵状态/语义鸿沟/创新概念状态缺口）
- **use-case**：动态验证（E2E 用例覆盖状态流转）

**量化指标**（通用）：
- 状态闭环率 = (有生产有消费的状态数) / (总状态数) >= 95%
- 孤儿状态数 <= 总状态数的 5%
- 幽灵状态数 = 0（零容忍，任何领域都应该避免）
- 创新概念状态完整性 = 符合定义的状态转换数 / 总转换数 >= 90%

**通用性保障**：
- 不预设具体状态名称（如"已支付"、"已发货"等电商术语）
- 仅验证结构完整性（是否有初始/终止/异常恢复）
- 适用于任何领域：电商/内容/教育/金融/医疗/SaaS 等

---

## 七、总结：创新保真 = 高敏感度 + 4D+6V+XV

创新概念的信息保真不是创造新机制，而是：
1. **高敏感度**：显式读取 `innovation_task` 字段，自动标注创新标记
2. **4D 增强**：创新概念携带完整的 `source_refs` / `constraints` / `decision_rationale`
3. **6V 覆盖**：创新界面强制覆盖 6/6 视角，不低于 4/6
4. **XV 验证**：创新特性的交叉验证，确保创新方向不被误解

**核心公式**：
```
创新保真 = (源头标记 × 下游敏感度 × 追溯完整性) / 信息压缩率
```

**目标**：确保 `product-concept` 中定义的创新概念在 downstream 各阶段不被稀释、不误解、不延后，最终实现的产品与最初创新愿景一致。
