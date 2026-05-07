# Meta-Skill 游戏项目专化设计规格

**日期：** 2026-05-08  
**范围：** 方案 B — GDD Capability 优先，其余 capability 渐进迭代
**术语约定：** 游戏品类模板（Game Scenario Template）— 按游戏品类选出的节点集合，英文用 `game-scenario`，中文用"品类模板"，不用"剧情模板"  
**状态：** 待实现

---

## 1. 问题陈述

现有 meta-skill 对游戏项目的支持停留在各 capability 里零散的一行描述（如 `| Game | Asset pipeline, game loop... |`），存在三个根本性缺口：

1. **没有游戏设计文档（GDD）能力** — 没有核心循环、战斗系统、经济体系、叙事结构等专项设计节点
2. **没有美术替代管线** — 游戏美术生产周期远长于功能开发，pipeline 必须在无 final 美术的情况下持续运转
3. **输出格式不适合人读** — 现有 JSON/MD 输出无法让策划/美术/程序直接介入审核；游戏开发需要跨职能早期对齐

本 spec 设计 `game-design` capability 作为第一个交付物，解决上述三个问题。

---

## 2. 核心架构原则

### 2.1 Bootstrap 是唯一专化入口

所有游戏专化逻辑在 `/bootstrap` 阶段完成，而非运行时：

```
/bootstrap 分析项目
  → 检测游戏引擎 / 用户声明
  → 读取 game-scenario-templates/*.json 选出节点集
  → 生成游戏专化 node-specs（含职能归属、HTML 路径、human_gate）
  → 写入 workflow.json

/run 按 node-spec 执行（不含专化逻辑，只执行 bootstrap 的决策）
```

`game-design.md` 是 bootstrap 的**知识参考库**，不是执行脚本。

### 2.2 游戏 Pipeline 与 App Pipeline 的根本差异

| 维度 | App Pipeline | 游戏 Pipeline |
|------|-------------|--------------|
| 节点归属 | AI agent | 职能角色（策划/美术/程序）|
| 执行模式 | 顺序自动化 | 多轨并行，节点间有依赖契约 |
| 人工介入 | 里程碑审批 | **每个节点都有职能 gate** |
| 主要输出 | JSON + MD | **HTML 可视化** + JSON 数据 |
| 角色概念 | 产品用户角色 | 双层：玩家角色 + 开发团队职能 |
| 节点选择 | 通用流程 | 按游戏类型（剧情）选节点集 |
| 美术流程 | 设计完即交付 | 替代资产贯穿全程，分阶段替换 |

### 2.3 与 gaming.md 的继承关系

`knowledge/domains/gaming.md` 已定义游戏领域的完整知识层：15 个设计节点、理论锚点、每节点 artifact 内容定义、按品类的节点选择建议。

`game-design.md`（本 spec 要新建的 capability）是其**执行层**，不重写知识，而是引用并扩展：

| 层 | 文件 | 职责 |
|----|------|------|
| 知识层 | `domains/gaming.md` | 节点定义、理论锚点、artifact 内容、品类节点选择 |
| 执行层 | `capabilities/game-design.md` | HTML 输出规格、human gate 协议、美术替代管线、AI 图片生成、团队职能分配 |

**Artifact 协调规则：**
- `gaming.md` 定义的各节点 artifact（`player-archetypes.json`、`core-mechanics.json`、`economy-model.json` 等）维持不变，写入 `.allforai/game-design/systems/` 子目录
- 新增 `game-design-doc.json` 作为**聚合索引**：引用各系统 artifact 路径，加上 `team_roles`、`art_direction`、`art_asset_inventory_ref` 等执行层字段
- `bootstrap` 读取 `gaming.md` 获取节点内容知识，读取 `game-design.md` 获取执行层规格，生成合并后的 node-spec

### 2.4 Pipeline 位置

```
product-concept
  ↓
[game-design]  ← 本 spec 的新增 capability
  ├─ core-loop-design
  ├─ combat-system-design      （按剧情类型选择）
  ├─ economy-design
  ├─ narrative-structure-design
  ├─ art-direction
  ├─ art-spec-design
  └─ ai-art-generation         （自动节点，无 human gate）
  ↓
product-analysis（消费 game-design-doc.json 作为 concept baseline）
  ↓
generate-artifacts
```

---

## 3. 游戏品类模板（Game Scenario Templates）

Bootstrap 按检测结果匹配品类模板，选出对应节点集。节点 ID 与 `domains/gaming.md` 第六节保持一致。

| 品类 ID | 适用类型 | 必选节点 | 可选节点 |
|--------|---------|---------|---------|
| `casual-mobile` | 超休闲/中度手游 | `core-loop-design`, `ftue-design`, `monetization-design` | `retention-hook-design`, `meta-game-design` |
| `action-rpg` | 动作/卡牌/RPG | `core-loop-design`, `combat-system-design`, `skill-tree-design`, `progression-curve-design`, `economy-design` | `narrative-design`, `level-design`, `worldbuilding` |
| `multiplayer-online` | MMO/MOBA/FPS | `core-loop-design`, `network-architecture-design`, `matchmaking-design`, `competitive-balance-design` | `social-system-design`, `anti-cheat-design`, `live-ops-design` |
| `roguelike` | 肉鸽/Roguelite | `core-loop-design`, `run-structure-design`, `meta-progression-design`, `procedural-gen-spec` | `build-variety-design` |
| `strategy-sim` | 策略/模拟经营 | `core-loop-design`, `economy-design`, `ai-faction-design`, `tech-tree-design` | `map-generation-spec` |
| `narrative-adventure` | 叙事/视觉小说/AVG | `core-loop-design`, `narrative-design`, `branching-structure-design`, `character-arc-design` | `dialogue-system-spec` |

所有品类模板存放于：`knowledge/game-scenario-templates/<scenario-id>.json`

Bootstrap 在 Step 1.5 无法自动判断时，向用户呈现选择题（不开放输入）。

### 3.1 规范节点总表（Canonical Node Registry）

> Bootstrap 生成 node-spec 时必须从此表取值，不得自行造名。

| node_id | discipline_owner | html_output | json_output | gaming.md 对应阶段 |
|---------|-----------------|-------------|-------------|------------------|
| `core-loop-design` | `lead-designer` | `game-design/core-loop.html` | `game-design/systems/core-mechanics.json` | core-mechanics-design |
| `ftue-design` | `ux-designer` | `game-design/ftue.html` | `game-design/systems/ftue.json` | level-design（教学关卡） |
| `monetization-design` | `monetization-designer` | `game-design/monetization.html` | `game-design/systems/monetization-design.json` | monetization-design |
| `retention-hook-design` | `systems-designer` | `game-design/retention-hook.html` | `game-design/systems/retention-hook.json` | progression-system |
| `meta-game-design` | `systems-designer` | `game-design/meta-game.html` | `game-design/systems/meta-game.json` | progression-system |
| `combat-system-design` | `combat-designer` | `game-design/combat-system.html` | `game-design/systems/combat-system.json` | core-mechanics-design |
| `skill-tree-design` | `combat-designer` | `game-design/skill-tree.html` | `game-design/systems/skill-tree.json` | progression-system |
| `progression-curve-design` | `numeric-designer` | `game-design/progression-curve.html` | `game-design/systems/progression-curve.json` | progression-system |
| `economy-design` | `numeric-designer` | `game-design/economy.html` | `game-design/systems/economy-model.json` | economy-design |
| `narrative-design` | `narrative-designer` | `game-design/narrative.html` | `game-design/systems/narrative-design.json` | narrative-design |
| `level-design` | `level-designer` | `game-design/level-design.html` | `game-design/systems/level-design.json` | level-design |
| `worldbuilding` | `narrative-designer` | `game-design/worldbuilding.html` | `game-design/systems/worldbuilding-bible.md` | worldbuilding |
| `network-architecture-design` | `backend-programmer` | `game-design/network-arch.html` | `game-design/systems/network-architecture.json` | （bootstrap Step 2.7 扩展）|
| `matchmaking-design` | `backend-programmer` | `game-design/matchmaking.html` | `game-design/systems/matchmaking.json` | （同上）|
| `competitive-balance-design` | `numeric-designer` | `game-design/competitive-balance.html` | `game-design/systems/balance-report.json` | balance-testing |
| `run-structure-design` | `lead-designer` | `game-design/run-structure.html` | `game-design/systems/run-structure.json` | core-mechanics-design |
| `meta-progression-design` | `systems-designer` | `game-design/meta-progression.html` | `game-design/systems/meta-progression.json` | progression-system |
| `procedural-gen-spec` | `gameplay-programmer` | `game-design/procedural-gen.html` | `game-design/systems/procedural-gen.json` | （引擎专化）|
| `ai-faction-design` | `ai-programmer` | `game-design/ai-faction.html` | `game-design/systems/ai-faction.json` | core-mechanics-design |
| `tech-tree-design` | `systems-designer` | `game-design/tech-tree.html` | `game-design/systems/tech-tree.json` | progression-system |
| `branching-structure-design` | `narrative-designer` | `game-design/branching-structure.html` | `game-design/systems/branching-structure.json` | narrative-design |
| `character-arc-design` | `narrative-designer` | `game-design/character-arc.html` | `game-design/systems/character-arc.json` | narrative-design |
| `art-direction` | `art-director` | `game-design/art-direction.html` | `game-design/art-style-guide.json` | art-direction |
| `art-spec-design` | `concept-artist` | `game-design/art-spec.html` | `game-design/art-asset-inventory.json` | art-direction |
| `ai-art-generation` | _(自动节点，无 discipline_owner)_ | _(更新 art-direction.html)_ | 更新 `art-asset-inventory.json` | — |

---

## 4. 节点结构规格

### 4.1 游戏节点 Node-Spec 扩展字段

每个游戏设计节点在标准 node-spec 基础上增加：

```json
{
  "node_id": "combat-system-design",
  "capability": "game-design",
  "scenario": "action-rpg",

  "discipline_owner": "combat-designer",
  "discipline_reviewers": ["gameplay-programmer", "art-director"],

  "html_output": ".allforai/game-design/combat-system.html",
  "json_output": ".allforai/game-design/systems/combat-system.json",
  "human_gate": true,
  "gate_requires_all_reviewers": false,
  "gate_approval_rule": "discipline_owner must approve; reviewers approval is advisory",

  "approval_record_path": ".allforai/game-design/approval-records.json",
  "gate_status": "pending | in-review | approved | revision-requested",

  "presentation": {
    "primary_audience": "combat-designer",
    "secondary_audience": "gameplay-programmer",
    "layout": "two-column",
    "required_visuals": ["skill-table-sortable", "state-machine-diagram"],
    "progressive_disclosure": {
      "above_fold": "system-overview + 3-key-decisions",
      "expanded": "full-skill-table + formulas",
      "collapsed": "edge-cases + boundary-conditions"
    },
    "language_rule": "left-column: gameplay language; right-column: technical language",
    "decision_callout_style": "warning-block"
  },

  "unlocks": ["skill-tree-design", "animation-state-machine-spec"],
  "blocked_by": ["core-loop-design"]
}
```

### 4.2 开发团队职能角色清单

以下职能 ID 用于 `discipline_owner` 和 `discipline_reviewers` 字段：

**策划（Design）**
- `lead-designer` — 主策划
- `combat-designer` — 战斗策划
- `systems-designer` — 系统策划
- `narrative-designer` — 剧情策划
- `level-designer` — 关卡策划
- `numeric-designer` — 数值策划
- `monetization-designer` — 商业化策划
- `ux-designer` — UI/UX 策划

**程序（Engineering）**
- `gameplay-programmer` — 玩法程序
- `backend-programmer` — 服务端程序
- `ui-programmer` — UI 程序
- `ai-programmer` — AI 程序
- `graphics-programmer` — 渲染程序
- `tools-programmer` — 工具程序

**美术（Art）**
- `art-director` — 美术总监
- `concept-artist` — 原画（角色/场景/道具）
- `ui-artist` — UI 美术
- `character-modeler` — 角色建模
- `environment-artist` — 场景美术
- `animator` — 动画师
- `vfx-artist` — 特效师
- `technical-artist` — 技术美术

**其他**
- `audio-director` — 音频总监
- `producer` — 制作人

---

## 5. 主要 Artifact 规格

### 5.1 `game-design-doc.json`（统一 GDD）

```json
{
  "game_scenario": "action-rpg",
  "game_title": "",
  "generated_at": "",

  "team_roles": {
    "design": ["lead-designer", "combat-designer", "narrative-designer", "level-designer", "numeric-designer"],
    "engineering": ["gameplay-programmer", "backend-programmer", "ui-programmer", "ai-programmer"],
    "art": ["art-director", "concept-artist", "character-modeler", "animator", "vfx-artist", "ui-artist"]
  },

  "player_roles": [
    {
      "id": "R1",
      "name": "玩家",
      "audience_type": "consumer",
      "progression_stages": ["新手 0-10h", "成长 10-50h", "核心 50h+"],
      "clients": [
        { "app": "game-client", "client_type": "unity-pc", "platform": "pc" }
      ]
    }
  ],

  "core_loop": {
    "primary": { "actions": [], "feedback": [], "reward": [], "duration_seconds": 0 },
    "secondary": { "description": "", "duration_minutes": 0 },
    "tertiary": { "description": "", "duration_days": 0 }
  },

  "systems": [
    {
      "id": "S1",
      "name": "",
      "discipline_owner": "",
      "html_path": "",
      "status": "pending | in-review | approved | revision-requested",
      "approved_by": [],
      "parameters": {},
      "state_machine": {},
      "interfaces": {}
    }
  ],

  "economy": {
    "currencies": [],
    "sources": [],
    "sinks": [],
    "balance_targets": {},
    "monetization_model": ""
  },

  "progression": {
    "power_curve": {},
    "unlock_sequence": [],
    "difficulty_curve": {},
    "onboarding_beats": []
  },

  "narrative": {
    "structure": "linear | branching | open-world",
    "acts": [],
    "characters": [],
    "emotional_arc": []
  },

  "art_direction": {
    "visual_style": "",
    "style_prompt_prefix": "",
    "color_palette": {},
    "forbidden_styles": [],
    "reference_works": []
  },

  "audio_direction": {
    "music_tone": "",
    "sfx_philosophy": "",
    "reference_works": []
  },

  "technical_constraints": {
    "engine": "",
    "target_platforms": [],
    "performance_budgets": {}
  }
}
```

### 5.2 `art-asset-inventory.json`

```json
{
  "style_guide_ref": ".allforai/game-design/art-style-guide.json",
  "assets": [
    {
      "id": "CHAR-001",
      "type": "character | environment | ui-icon | ui-bg | vfx | animation | audio-sfx | audio-bgm",
      "name": "",
      "discipline": "",

      "art_spec": {
        "dimensions": "",
        "description": "",
        "palette_constraint": [],
        "states_needed": [],
        "style_note": "",
        "technical_constraints": {}
      },

      "ai_generatable": true,
      "ai_gen_target": "concept-reference | actual-asset | mood-reference",

      "substitution": {
        "placeholder": "",
        "temp": null,
        "alpha": null,
        "final": null
      },
      "current_state": "placeholder | temp | alpha | final",

      "milestone_gate": "alpha | beta | release",
      "blocks": []
    }
  ],

  "substitution_rules": {
    "character": "等比例 Capsule 几何体，头部贴角色名标签",
    "environment": "白盒几何，按区域用不同纯色标识功能分区",
    "animation": "简单 tween 位移，无骨骼动画",
    "vfx": "单色粒子圆形爆发",
    "ui-icon": "圆角色块 + 图标名文字",
    "ui-bg": "纯色 + 游戏标题文字",
    "audio-sfx": "440Hz 正弦波短音（命中）/ 200Hz（受伤）/ 880Hz（升级）",
    "audio-bgm": "静音 或 CC0 音乐库替代"
  },

  "ai_gen_config": {
    "model_preference": ["flux-pro", "gpt-image", "openrouter-imagen"],
    "style_prefix_field": "art-style-guide.json.style_prompt_prefix",
    "output_dir": "assets/ai-gen/",
    "naming_convention": "{asset_id}-{gen_target}.png"
  }
}
```

---

## 6. HTML 输出规格

### 6.0 v1 HTML 交付模型

**v1 采用静态 HTML，不依赖 JavaScript 写回。**

- HTML 文件由 `/run` 执行节点时生成，是**只读展示文档**
- 审批状态、修改意见均写入独立文件 `.allforai/game-design/approval-records.json`
- 人工审核后，由审核人（或 AI 代劳）手动更新 `approval-records.json` 对应条目
- `/run` 在推进下一节点前读取 `approval-records.json` 判断 gate 是否通过
- v2 再考虑 HTML 内嵌审批按钮（写回 JSON）

**`approval-records.json` 结构：**

```json
{
  "records": [
    {
      "node_id": "combat-system-design",
      "gate_status": "approved",
      "discipline_owner": "combat-designer",
      "approved_by": ["combat-designer", "gameplay-programmer"],
      "revision_notes": "",
      "approved_at": "2026-05-08T10:30:00Z",
      "unblocks": ["skill-tree-design", "animation-state-machine-spec"]
    },
    {
      "node_id": "art-direction",
      "gate_status": "revision-requested",
      "discipline_owner": "art-director",
      "approved_by": [],
      "revision_notes": "色板中主色太暗，需要提高明度 10%，参考《空洞骑士》的蓝色而非深海蓝",
      "approved_at": null,
      "unblocks": ["art-spec-design", "ai-art-generation"]
    }
  ]
}
```

`/run` 的 gate 判断逻辑：`gate_status == "approved"` → 解锁 `unblocks[]` 中的节点；`revision-requested` → 重新执行该节点（读取 `revision_notes` 作为修改指令）。

### 6.1 `game-design-dashboard.html`（项目总览）

**读者：** 制作人、主策划、各职能负责人  
**目标：** 5 秒内看清当前状态，知道哪里需要自己介入  
**格式：** 静态 HTML，读取时从 `approval-records.json` 和 `art-asset-inventory.json` 嵌入当前数据

**必须包含：**
- Tab 导航：按职能分组（设计/美术/程序/音频）
- 每个节点：状态徽章（待审 / 审核中 / 已批准 / 需修改）+ 归属职能 + 最后更新时间
- 美术进度热力图：各类资产的 placeholder/temp/alpha/final 数量
- 当前 Milestone 完成度：gate 资产达标数 / 总数
- 快捷跳转：点击节点直接打开对应 HTML

### 6.2 `core-loop.html`

**读者：** 主策划  
**目标：** 验证循环设计意图，确认节奏感

| 区域 | 内容 | 格式 |
|------|------|------|
| Above fold | 循环可视化图（Primary/Secondary/Tertiary 三层）| SVG 流程图 |
| 次要区域 | 设计意图（2-3 句，策划语言）| 引用块 |
| 待决策 | 未解决的设计选择 | ⚠️ 警告块 + 选项对比 |
| 底部 | [标记批准] [请求修改：文本框] | 操作按钮 |

### 6.3 `combat-system.html`

**读者：** 战斗策划（主）、玩法程序（次）  
**目标：** 验证技能设计意图 + 确认实现接口

| 区域 | 内容 | 格式 |
|------|------|------|
| Above fold | 系统概述（策划语言）+ 3 个关键设计决策 | 双栏：设计意图 \| 技术规格 |
| 展开 | 技能总表 | 可排序数据表（伤害/冷却/消耗/范围/状态效果）|
| 展开 | 状态机图 | SVG 节点连线图 |
| 折叠 | 详细公式 / 边界条件 / 异常处理 | 代码块 + 表格 |
| 底部 | 各审核人独立批准按钮 | 按职能分列 |

**语言规则：** 左列用游戏语言（"向前突进，命中触发灼烧"），右列用技术语言（`State: Grounded, Duration: 0.4s`）。

### 6.4 `economy-design.html`

**读者：** 数值策划  
**目标：** 验证货币流向平衡 + 成长曲线合理性

| 区域 | 内容 | 格式 |
|------|------|------|
| Above fold | 货币流向图 | 桑基图（宽度=流量）|
| 展开 | 成长曲线 | 折线图，可切换维度 |
| 展开 | 平衡红线 | 高亮临界值 + ⚠️ 说明 |
| 折叠 | 详细参数表 | 数据表 |

### 6.5 `art-direction.html`

**读者：** 美术总监  
**目标：** 确认视觉调性方向，批准后解锁 AI 生图

| 区域 | 内容 | 格式 |
|------|------|------|
| Above fold | 气氛图（大图） | 全宽图片 |
| 次要区域 | 色板 + 禁止风格 | 色块 + 标签 |
| 次要区域 | 参考作品 | 缩略图横排 |
| 次要区域 | AI 生成初稿（4 宫格）| 图片网格 + 点击放大 |
| 底部 | [✓ 方向正确] [需调整：文本框] | 操作区 |

**原则：** 图像优先，文字最少。禁止在美术文档里出现超过 3 行连续文字描述。

### 6.6 `art-spec-design.html`

**读者：** 各美术职能  
**目标：** 按职能过滤查看自己负责的资产规格，确认后触发 AI 生图

| 区域 | 内容 | 格式 |
|------|------|------|
| 筛选栏 | 按职能/类型/状态过滤 | 标签筛选 |
| 资产卡片 | 规格描述 + AI 生成结果（如有）+ 状态 | 卡片网格 |
| 每张卡片 | 尺寸/描述/色板约束/milestone 门控 | 紧凑信息块 |
| 底部 | [批准该资产规格] [修改说明] | 逐卡操作 |

### 6.7 `narrative-structure.html`

**读者：** 剧情策划  
**目标：** 验证叙事结构、分支逻辑、情感弧线

| 区域 | 内容 | 格式 |
|------|------|------|
| Above fold | 故事树（可交互，节点可展开）| SVG 树形图 |
| 展开 | 情感曲线 | 折线图（X: 进度，Y: 情感强度）标注高潮/低谷/转折 |
| 展开 | 角色弧度时间线 | 横向时间线，每角色一行 |
| 折叠 | 对白节点详情 | 点击展开 |

---

## 7. AI 图片生成集成

### 7.1 触发条件

- `art-direction` 节点被批准后，自动触发 `ai-art-generation` 节点
- `ai-art-generation` 是**自动节点**，无 human gate，完成后更新 dashboard

### 7.2 Prompt 构造规则

```
final_prompt = art-style-guide.json.style_prompt_prefix
             + ", "
             + asset.art_spec.description
             + ", "
             + target_suffix[ai_gen_target]

target_suffix = {
  "concept-reference": "character concept sheet, front side back views, white background",
  "actual-asset":      "game UI icon, isolated, transparent background, no shadow",
  "mood-reference":    "environment concept art, cinematic composition, dramatic lighting"
}
```

### 7.3 工具优先级

以下工具 ID 在 **meta-skill ai-gateway MCP 已配置**时可用（`shared/mcp-ai-gateway/` 已安装且 `OPENROUTER_API_KEY` / `GOOGLE_API_KEY` 已设置）：

```
优先：mcp__plugin_meta-skill_ai-gateway__flux_generate_image   (FLUX Pro)
次选：mcp__plugin_meta-skill_ai-gateway__generate_image         (Google Imagen 4)
兜底：mcp__plugin_meta-skill_ai-gateway__openrouter_generate_image
```

**工具不可用时（降级）：** 维持 placeholder 状态，HTML 中显示规格文字 + 尺寸占位框，`ai_generatable` 字段保留供后续补跑。不阻塞 pipeline 继续执行。

### 7.4 资产状态更新

```
ai_gen_target = "actual-asset"
  → current_state: placeholder → temp
  → substitution.temp = "assets/ai-gen/{id}-actual-asset.png"

ai_gen_target = "concept-reference" | "mood-reference"
  → current_state 保持 placeholder
  → ai_generated.path 记录生成路径（参考用，不入游戏）
```

### 7.5 可 AI 生成的资产类型

| 类型 | 可生成内容 | 是否直接可用 | 人工必须做 |
|-----|-----------|------------|----------|
| 角色（3D 游戏） | 概念参考图 | 参考用 | 建模/绑定/动画 |
| 角色立绘（2D）| 立绘草稿 | ✅ temp 可用 | 线稿精修 |
| UI 图标 | 实际图标 | ✅ temp 可用 | 品控精修 |
| UI 背景/插画 | 实际背景 | ✅ temp 可用 | 精修 |
| 场景环境 | 气氛参考图 | 参考用 | 3D 建模/灯光 |
| VFX | 效果参考截图 | 参考用 | 粒子系统制作 |
| 动画 | ❌ 不可生成 | — | 动画师制作 |
| 3D 模型 | ❌ 不可生成 | — | 建模师制作 |
| 音频 | ❌ 不可生成 | — | 音效师制作 |

---

## 8. 美术替代管线

### 8.1 四个正式阶段

| 阶段 | 描述 | 程序/Demo 可用性 |
|------|------|----------------|
| `placeholder` | 几何体/色块/占位图 | ✅ 始终可用 |
| `temp` | AI 生成资产 或 免费素材 | ✅ Demo/测试可用 |
| `alpha` | 人工美术初稿 | ✅ Alpha Milestone 可用 |
| `final` | 上线质量 | ✅ Release |

### 8.2 Milestone 门控规则

- **Alpha Milestone：** 所有 `milestone_gate = "alpha"` 的资产必须达到 alpha 状态
- **Beta Milestone：** 所有 `milestone_gate = "beta"` 的资产必须达到 alpha 状态（允许 beta 延迟）
- **Release：** 所有资产必须达到 final 状态
- `demo-forge` 和 `product-verify` 在 placeholder/temp 状态下照常执行，不以缺少 final 美术为阻塞条件

### 8.3 Art-Agnostic 代码要求

`generate-artifacts` 节点需在 node-spec 中包含约束：

> 代码引用资产时必须通过资产 ID 解析层（Asset Registry），禁止硬编码文件路径。资产路径由 `art-asset-inventory.json` 的 `substitution[current_state]` 字段在运行时解析。

`quality-checks` 节点新增扫描项：检测代码中是否存在硬编码资产路径（绕过资产 ID 系统）。

---

## 9. 与现有 Capabilities 的集成

### 9.1 Bootstrap（修改）

**新增检测逻辑（Step 1.1）：**
- 检测 `project.godot` → Godot
- 检测 `*.uproject` + `Source/` → Unreal Engine
- 检测 `Assets/` + `ProjectSettings/ProjectVersion.txt` → Unity
- 检测 `*.love` → LÖVE2D
- 检测 `Cargo.toml` + `bevy` 依赖 → Bevy (Rust)

**新增 Step 1.5 选项（当检测到游戏引擎时）：**
- 在目标选择中增加游戏剧情类型选择
- 当无法自动判断时，呈现 6 个剧情选项（见第 3 节）

**新增 Step 3 节点生成逻辑：**
- 读取对应 `game-scenario-templates/<id>.json`
- 在 `product-concept` 节点之后插入 game-design 节点链
- 为每个 game-design 节点生成带 `discipline_owner`、`html_output`、`human_gate` 的专化 node-spec

### 9.2 Product Analysis（下游消费方）

游戏项目中，`product-analysis` 消费 `game-design-doc.json` 作为 concept baseline：

- `role-profiles.json` 增加 `team_roles` 段（开发职能）和 `player_roles` 段（玩家类型）
- `task-inventory.json` 对游戏项目使用"系统规格"格式代替 CRUD 任务格式
- `experience-map.json` 映射到游戏屏幕（HUD、主菜单、关卡选择、背包、对话等）

### 9.3 Demo Forge（下游消费方）

- 读取 `art-asset-inventory.json` 确认当前可用资产状态
- 在 placeholder/temp 状态下正常运行，不以缺少 final 美术阻塞
- 游戏项目 demo 数据设计来源：`game-design-doc.json.progression`（玩家存档在不同进度阶段的状态）

### 9.4 Quality Checks（下游消费方）

新增游戏专项扫描：
- `balance-parameters-audit`：对照 `game-design-doc.json.economy.balance_targets` 验证数值参数
- `art-agnostic-check`：检测代码中硬编码资产路径
- `milestone-gate-check`：验证当前 milestone 对应的资产 state 是否达标

---

## 10. 本 Spec 的实现范围

### 本次实现（方案 B 第一步）

- [ ] 新建 `claude/meta-skill/knowledge/capabilities/game-design.md`
- [ ] 新建 `claude/meta-skill/knowledge/game-scenario-templates/` 目录 + 6 个剧情模板 JSON
- [ ] 修改 `claude/meta-skill/skills/bootstrap.md`（游戏引擎检测 + 节点注入逻辑）

### 渐进迭代（后续 spec）

- 深化 `discovery.md` 游戏专化（资产管线、ECS、游戏循环）
- 深化 `product-analysis.md` 游戏专化（系统规格格式）
- 深化 `ui-design.md` 游戏专化（HUD 设计、手柄输入、无障碍）
- 深化 `demo-forge.md` 游戏专化
- `quality-checks.md` 游戏专项检查完整实现

---

## 11. 不在本 Spec 范围内

- 游戏服务器架构设计（属于 infra-design 专化）
- 多人游戏网络同步实现（属于 generate-artifacts 专化）
- 音频生成（当前 meta-skill 无音频生成能力）
- 3D 资产生成（当前无 3D 生成工具）
- 具体 HTML 模板的 CSS/JS 实现（属于实现阶段）
