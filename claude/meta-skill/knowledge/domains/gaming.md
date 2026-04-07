# Gaming Domain Knowledge

> 游戏领域的产品设计知识包。
> Bootstrap Step 2.4 加载本文件 → Step 3 用本文件特化产品设计 + 构建 + 运维节点。

---

## 一、领域特有的产品设计阶段

标准产品设计层有 9 个子阶段（见 product-concept.md）。游戏项目需要 **替代、补充、新增** 部分阶段。

### 替代关系

| 标准阶段 | 游戏领域替代为 | 理由 |
|---------|-------------|------|
| user-role-definition | **player-archetype-definition** | 游戏角色不是"用户角色"（admin/consumer），而是玩家原型（Bartle Types）+ 游戏内角色 |
| business-model | **monetization-design** | 游戏商业化有特有模型（F2P/Premium/Gacha/Battle Pass/Subscription），不是通用 Lean Canvas |
| feature-scoping | **core-mechanics-design** | 游戏的"功能"是"玩法机制"，用 MDA 框架而非 user story |

### 补充关系

| 标准阶段 | 游戏领域补充 | 说明 |
|---------|-----------|------|
| concept-crystallization | + **worldbuilding** | 世界观设定是游戏概念的核心组成部分 |
| ui-design | + **art-direction** | 游戏的视觉不是 UI 组件，是美术风格（像素/写实/卡通/赛博朋克） |
| concept-validation | + **paper-prototype-test** | 游戏概念验证通常用纸面原型/灰盒测试而非 MVP |

### 新增阶段（游戏特有）

| 新增阶段 | 理论锚点 | 说明 |
|---------|---------|------|
| **economy-design** | Sink-Source 模型, 双货币体系 | 游戏经济系统设计（资源产出/消耗/交易循环） |
| **progression-system** | Flow Theory, Difficulty Curve | 成长系统（等级/技能/装备/解锁曲线） |
| **level-design** | Pacing Theory, Teaching through Design | 关卡设计（难度曲线/节奏/引导） |
| **narrative-design** | Hero's Journey, Interactive Narrative | 叙事设计（剧情/对话/分支/世界观叙事） |
| **balance-testing** | Monte Carlo Simulation, Playtest Protocol | 数值平衡测试（DPS/经济/概率验证） |

---

## 二、完整的游戏产品设计节点图

```
problem-discovery（做什么类型的游戏？解决什么"玩"的需求？）
  ↓
assumption-zeroing（挑战品类共识：MMO 一定要公会？卡牌一定要抽卡？）
  ↓
market-research（品类分析：同类游戏对比，成功/失败案例）
  ↓
innovation-exploration（跨品类借鉴：把 roguelike 元素加到 RPG？）
  ↓
player-archetype-definition（玩家画像：Bartle Types + 自我决定理论）
  ↓
worldbuilding（世界观：背景/种族/势力/历史/规则）
  ↓
core-mechanics-design（核心玩法：MDA 框架 → 机制/动态/美学）
  ↓
economy-design（经济系统：资源/货币/产出/消耗/交易循环）
  ↓
progression-system（成长系统：等级/技能树/装备/解锁曲线）
  ↓
level-design（关卡/内容设计：难度曲线/节奏/教学关卡）
  ↓
narrative-design（叙事设计：主线/支线/对话/分支剧情）
  ↓
monetization-design（商业化：F2P/Premium/Gacha/Battle Pass/广告）
  ↓
art-direction（美术风格：Mood Board/风格指南/角色设计/场景概念）
  ↓
concept-crystallization（GDD 游戏设计文档结晶）
  ↓
concept-validation（纸面原型测试 + 数值仿真）
  ↓
balance-testing（数值平衡测试：蒙特卡洛模拟 + Playtest）
```

**并行机会：**
- assumption-zeroing + market-research（并行）
- worldbuilding + core-mechanics-design（可并行——世界观和玩法可以同时设计）
- economy-design + progression-system（可并行——但需要在后面对齐）
- narrative-design + level-design（可并行——叙事和关卡交织但可独立推进）

**LLM 决定包含哪些：**
- 简单休闲游戏（如 Flappy Bird）：跳过 worldbuilding/narrative/economy，只需 core-mechanics + level-design + monetization
- RPG/MMO：全部节点
- 卡牌/策略：跳过 level-design，加重 economy-design + balance-testing
- 叙事游戏（如 Detroit）：跳过 economy/progression，加重 narrative-design

---

## 三、每个阶段的理论锚点详解

### player-archetype-definition（玩家原型）

**替代标准的 user-role-definition**

| 理论 | 作者/年份 | 核心思想 | 在游戏设计中的应用 |
|------|----------|---------|-----------------|
| **Bartle Types** | Bartle (1996) | 4 类玩家：Achiever/Explorer/Socializer/Killer | 确定目标玩家类型，设计对应内容 |
| **Self-Determination Theory** | Deci & Ryan (2000) | 内在动机三要素：自主/胜任/关联 | 设计让玩家"想玩"而非"被迫玩"的系统 |
| **Player Motivation Model** | Quantic Foundry / Yee (2006) | 12 维动机（破坏/社交/精通/沉浸/创造/收集） | 精细化玩家画像 |

**输出：** `player-archetypes.json`

---

### core-mechanics-design（核心玩法）

**替代标准的 feature-scoping**

| 理论 | 作者/年份 | 核心思想 | 应用 |
|------|----------|---------|------|
| **MDA Framework** | Hunicke, LeBlanc, Zubek (2004) | Mechanics → Dynamics → Aesthetics | 从底层机制设计推导出玩家体验 |
| **Core Loop** | 行业通用 | 核心循环：行动 → 反馈 → 奖励 → 更强 → 行动 | 定义游戏的最小可玩单元 |
| **Meta Loop** | 行业通用 | 外循环：Session → Progress → New Content → Session | 定义长期留存驱动力 |
| **Meaningful Choices** | Sid Meier | "游戏是一系列有趣的决策" | 每个机制必须给玩家有意义的选择 |

**输出：** `core-mechanics.json`

---

### economy-design（经济系统）

| 理论 | 核心思想 | 应用 |
|------|---------|------|
| **Sink-Source Model** | 资源有产出源（Source）和消耗池（Sink），平衡 = 产出 ≈ 消耗 | 设计货币/资源循环 |
| **Dual Currency** | 软货币（游戏内获取）+ 硬货币（付费购买），分离免费/付费体验 | 商业化基础 |
| **Inflation Control** | 经济膨胀导致新玩家追不上老玩家 | 设计消耗机制控制通胀 |
| **Exchange Rate** | 不同资源之间的兑换关系 | 确保任何路径的单位时间收益平衡 |

**输出：** `economy-model.json`

---

### progression-system（成长系统）

| 理论 | 核心思想 | 应用 |
|------|---------|------|
| **Flow Theory** | Csikszentmihalyi (1990) | 心流 = 挑战与技能的平衡区 | 难度曲线不能太简单也不能太难 |
| **Difficulty Curve** | 行业通用 | 难度随进度非线性上升，带"呼吸节奏" | 交替紧张和放松 |
| **Mastery Progression** | 行业通用 | 新手 → 进阶 → 精通，每阶段有明确的"成长感" | 设计技能/装备/等级解锁节奏 |
| **Rubber Banding** | 行业通用 | 落后的玩家获得加速，领先的玩家获得减速 | 控制玩家间差距 |

**输出：** `progression-curve.json`

---

### level-design（关卡设计）

| 理论 | 核心思想 | 应用 |
|------|---------|------|
| **Pacing** | 节奏交替：紧张 → 放松 → 紧张 | 关卡排列的节奏设计 |
| **Teaching through Design** | 不用教程，通过关卡设计教玩家 | 前几关隐性教学 |
| **Difficulty Spike vs Curve** | 突然变难 = 流失；渐进变难 = 成就感 | 避免难度断层 |
| **Content Gating** | 通过进度/技能/资源控制内容解锁 | 防止玩家跳过内容 |

**输出：** `level-design.json`

---

### narrative-design（叙事设计）

| 理论 | 核心思想 | 应用 |
|------|---------|------|
| **Hero's Journey** | Campbell (1949) | 12 步叙事结构：普通世界 → 冒险召唤 → 试炼 → 回归 | 主线剧情骨架 |
| **Interactive Narrative** | 行业通用 | 玩家选择影响剧情走向 | 分支对话/多结局设计 |
| **Environmental Storytelling** | 行业通用 | 通过环境细节（而非对话）讲故事 | 场景设计承载叙事 |
| **Lore Bible** | 行业通用 | 世界观设定集：历史/地理/势力/人物 | 保持叙事一致性 |

**输出：** `narrative-design.json`、`worldbuilding-bible.md`

---

### monetization-design（商业化）

**替代标准的 business-model**

| 模式 | 适用品类 | 关键设计点 |
|------|---------|-----------|
| **Premium** (买断) | 主机/PC/独立游戏 | 定价策略、DLC 规划、Season Pass |
| **F2P + IAP** | 手游/网游 | 付费点设计（不 P2W）、鲸鱼管理、VIP 系统 |
| **Gacha/抽卡** | 卡牌/RPG | 概率公示、保底机制、概率衰减 |
| **Battle Pass** | 竞技/射击 | 赛季节奏、免费 vs 付费轨道、奖励密度 |
| **Subscription** | MMO/服务型 | 月卡价值感、续费留存 |
| **Ad-based** | 休闲/超休闲 | 广告频率、激励视频时机、eCPM 优化 |

**输出：** `monetization-design.json`

---

### art-direction（美术风格）

**补充标准的 ui-design**

| 元素 | 说明 |
|------|------|
| **Mood Board** | 视觉参考集合（色调/氛围/质感） |
| **Style Guide** | 角色设计规范、场景设计规范、UI 规范 |
| **Color Palette** | 主色/辅色/强调色/势力色 |
| **Character Design** | 角色比例/风格/服装/表情 |
| **Environment Design** | 场景构成/光影/氛围 |
| **UI Style** | HUD/菜单/弹窗/字体/图标风格 |

**输出：** `art-direction.md`、`art-tokens.json`

---

### balance-testing（数值平衡测试）

**特化标准的 demo-forge**

| 方法 | 说明 |
|------|------|
| **Monte Carlo 模拟** | 随机模拟 N 次战斗/经济循环，统计分布 |
| **Spreadsheet Model** | 用表格建模经济/成长曲线，检查极端情况 |
| **Playtest Protocol** | 结构化测试流程：目标/步骤/数据收集/分析 |
| **A/B Testing** | 不同数值版本对比留存/付费数据 |

**输出：** `balance-report.json`

---

## 四、领域特有的产出物

| 产出物 | 格式 | 对应阶段 |
|--------|------|---------|
| `player-archetypes.json` | JSON | player-archetype-definition |
| `core-mechanics.json` | JSON | core-mechanics-design |
| `economy-model.json` | JSON | economy-design |
| `progression-curve.json` | JSON | progression-system |
| `level-design.json` | JSON | level-design |
| `narrative-design.json` | JSON | narrative-design |
| `worldbuilding-bible.md` | Markdown | worldbuilding |
| `monetization-design.json` | JSON | monetization-design |
| `art-direction.md` | Markdown | art-direction |
| `art-tokens.json` | JSON | art-direction |
| `balance-report.json` | JSON | balance-testing |
| `game-design-document.md` | Markdown | concept-crystallization (替代 product-definition.md) |

所有产出写入 `.allforai/product-concept/` 和 `.allforai/game-design/`。

---

## 五、领域特有的运维层差异

| 标准运维节点 | 游戏领域差异 |
|------------|------------|
| setup-runtime-env | + 游戏引擎环境（Unity/Unreal/Godot SDK） |
| run-migrations | + 游戏配置表导入（关卡/数值/物品表） |
| seed-essential-data | + 初始游戏配置（默认角色/初始装备/教学关卡数据） |
| demo-forge | + 模拟玩家数据（不同进度的玩家存档） |
| smoke-test | + 核心玩法验证（能否完成一局/通过教学关卡） |
| balance-testing | **新增**（标准产品没有） |

---

## 六、常见游戏品类的节点选择参考

| 品类 | 核心节点 | 可跳过 |
|------|---------|--------|
| **RPG/MMO** | 全部 15 个节点 | — |
| **卡牌/策略** | player-archetype, core-mechanics, economy, monetization, balance | level-design, narrative |
| **休闲/超休闲** | core-mechanics, level-design, monetization(ad-based) | worldbuilding, narrative, economy, progression |
| **叙事/AVG** | narrative, worldbuilding, art-direction | economy, balance, progression |
| **塔防/TD** | core-mechanics, level-design, economy, progression, balance, monetization(gacha+ad) | worldbuilding, narrative（轻量背景可嵌入 level-design）。注意塔协同效果设计是核心深度来源 |
| **暗黑类/Loot-ARPG** | core-mechanics, economy, progression, balance, level-design, narrative, worldbuilding, monetization(premium) | assumption-zeroing, innovation。额外需要 Step 2.7 研究：词缀生成/掉落表/合成系统/交易系统 |
| **竞技/MOBA/FPS** | core-mechanics, balance, player-archetype, monetization(battle-pass) | narrative, worldbuilding |
| **沙盒/开放世界** | worldbuilding, core-mechanics, economy, progression, level-design | — (几乎全要) |
| **独立/实验** | core-mechanics, art-direction | 按需选择，可非常精简 |

---

## 七、研究触发器

以下场景超出本文件覆盖范围。当项目涉及这些子领域时，bootstrap Step 2.7
应通过 WebSearch 研究对应设计模式。

| 触发条件 | 研究方向 |
|---------|---------|
| 产品包含多人联机 | Netcode 架构（P2P vs 专用服务器）、状态同步、延迟补偿、反作弊 |
| 产品包含 UGC 关卡编辑器 | 关卡编辑器 UI、用户内容审核、关卡分享/评分 |
| 产品包含赛季/赛事系统 | 排名算法（Elo/Glicko）、赛季重置、奖励结算 |
| 产品包含观战/回放系统 | 录制架构（关键帧 vs 指令流）、回放同步、观战延迟、存储格式 |
| 产品包含游戏内社交 | 好友系统、战队/公会、游戏内聊天、组队邀请、社交关系链 |
| 产品包含跨平台存档 | 云存档同步、平台账号绑定、进度合并冲突处理 |
| 产品包含 VR/AR | 空间交互设计、运动病预防、手部追踪、空间音频 |
| 产品使用特定引擎 | 引擎特定的构建管线、资源管理、性能优化最佳实践 |
