# Art Concept Skill

> 美术概念确认阶段。在游戏文档设计（art-direction）完成后、art-spec-design 执行前运行。
> 通过搜索驱动的交互式对话确定美术技术规格，产出 `art-pipeline-config.json`。
>
> **触发方式：**
> - Bootstrap 自动串联（art-direction approved → 检查 art-pipeline-config.json → 不存在则调起此 skill）
> - 用户手动运行 `/art-concept` 修订美术决策

## 知识库加载

执行前读取以下文件作为参考上下文：
- `${CLAUDE_PLUGIN_ROOT}/knowledge/domains/art-methodology.md` — 美术类型分类法、理论锚点、决策树骨架、权衡框架
- `${CLAUDE_PLUGIN_ROOT}/knowledge/domains/art-tools.md` — AI 可调用工具能力矩阵、CLI 命令模板

## 输出文件

`.allforai/game-design/art-pipeline-config.json`

---

## 执行流程

### Step 0：验收 art-direction 输出

从 `.allforai/game-design/art-style-guide.json` 拉取 `art_overview` 字段：

```
检查字段：
  ✓ art_overview.dimension: "2d" | "3d" | "2.5d"
  ✓ art_overview.style: "cartoon" | "pixel" | "realistic" | "hand_drawn" | "vector"
  ✓ art_overview.animation_system: "frame" | "spine" | "3d_skeletal" | "mixed"

若字段缺失：
  → 提示 art-direction 节点需补充 art_overview 字段，暂停执行
  
若字段存在：
  → 展示已决策内容，问一个问题：
    "以上美术方向是否需要修订？（修订请先更新 art-direction 节点）"
  → 确认无误 → 进入 Step 0.5
```

### Step 0.5：竞品美术研究

从 `.allforai/game-design/game-design-doc.json`（若存在）或 `product-concept.json` 读取 `genre`。

执行搜索（中英文各一轮）：

```
1. "{genre} game art style {dimension} {year}"
2. "{style} game asset production pipeline tools"
3. "{genre} top mobile games art direction breakdown"
```

源质量优先级：P1 GDC演讲/官方美术指南 → P2 游戏开发博客 → P3 r/gamedev → P4 泛SEO（不引用）

**输出**：各维度的推荐选项列表（内部使用，不单独展示，用于 Step 1 选项生成）

### Step 1：按维度逐一问答

**铁律：从不问开放性问题。每问提供 2-4 个选项，选项必须来自 Step 0.5 搜索结论，附带证据。**

根据 `art_overview.dimension` 和 `art_overview.style` 选择分支：

---

#### 分支 A：2D 通用（dimension=2d，style≠pixel）

**Q1：地砖系统？**
选项示例（实际选项来自搜索）：
- 正交网格（最普遍，{genre}中占X%）
- 等距斜视（策略/模拟经营常用）
- 无地砖/自由场景（纯角色驱动叙事游戏）
→ 驱动：`tileset.type`；选"无地砖"时 active_nodes 移除 `tile-art-gen`

**Q2：角色动画方案？**
- 无骨骼（帧序列，手工质感，文件较大）
- Spine Lite（骨骼动画，支持换装，成本中等）
- Spine Full（骨骼+网格，最平滑，需授权）
→ 驱动：`character.rig`

**Q3：特效方案？**
- 帧序列（Aseprite/Photoshop制作，精细可控）
- Spine FX（与角色同骨骼系统）
- Shader 粒子（引擎内置，实时，无需额外资产）
→ 驱动：`vfx.approach`

**Q4：场景层次？**
- 单层（最简，无视差）
- 2-3 层视差（主流手游，增加空间感）
- 完整多层视差（5层+，精细但制作成本高）
→ 驱动：`environment.parallax_layers`

**Q5：需要概念原画（Concept Art）吗？**
- 不需要（直接进入 AI 生图阶段）
- 角色设定图（用于确定角色形象后再生产资产）
- 场景概念图（用于确定环境风格）
- 两者都要
→ 驱动：`concept_art.types[]`；非"不需要"时 active_nodes 加入 `concept-art-gen`

**Q6：工具链约束？**
- 已有 Spine 商业授权
- 仅使用开源工具（DragonBones / 无骨骼）
- 有外包美术支持（可选更复杂方案）
→ 驱动：`toolchain.constraints`

---

#### 分支 B：2D 像素风（style=pixel）

**Q1：地砖分辨率？**
- 8×8 px（极简，复古风）
- 16×16 px（经典像素风，GameBoy/GBC 感）
- 32×32 px（主流，细节与风格平衡）
- 64×64 px（高精细，接近现代像素独立游戏）
→ 驱动：`tileset.tile_resolution` + `pixel.tile_size`

**Q2：调色板大小？**
- 8色（极限限制，极简美学）
- 16色（经典 CGA/EGA 感）
- 32色（主流像素风独立游戏）
- 256色（较宽松，接近早期 SNES）
→ 驱动：`pixel.palette_size`

**Q3：动画帧数预算？**
- 4帧（最精简，走路可信）
- 8帧（流畅，大多数像素风游戏选择）
- 16帧（精细，制作成本显著增加）
→ 驱动：`pixel.anim_frames`

**Q4：Aseprite 是否已安装？**
- 已安装（可用 Aseprite CLI batch 模式做像素化后处理）
- 未安装（用 Python PIL 降采样，效果略差）
→ 驱动：`toolchain.aseprite_available`

**Q5：需要概念原画？**（同分支A Q5）

**Q6：工具链约束？**（同分支A Q6，但"已有 Spine 授权"替换为"已有 Aseprite 授权"）

---

#### 分支 C：3D（dimension=3d）

**Q1：多边形面数预算？**
- 移动端低模（角色 500-2000 面，兼顾低端设备）
- 移动端中模（2000-5000 面，中高端设备）
- 不限制（PC/主机，开发期不考虑面数）
→ 驱动：`model_3d.poly_budget`

**Q2：贴图工作流？**
- PBR 金属度/粗糙度（写实风格行业标准）
- 卡通平涂（手绘/低多边形风格，无高光贴图）
- 手绘风格（纹理手绘感，接近 2D 油画）
→ 驱动：`model_3d.texture_workflow`

**Q3：骨骼动画来源？**
- Blender 无头导出（程序化+人工建模均可，需安装 Blender）
- 外包动画师（AI 只生成规格文档，human_gate 等待交付）
→ 驱动：`model_3d.anim_source`

**Q4：VFX 方案？**
- 引擎粒子系统（Unity VFX Graph / Cocos 内置）
- 帧序列叠加（2D sprite 覆盖在 3D 场景）
- Shader 特效（程序化，无额外资产）
→ 驱动：`vfx.approach`

**Q5：场景构建方式？**
- 手工建模（外包/团队建模，AI 生成规格文档）
- 程序化生成（Blender Python 脚本，AI 可执行）
- 混合（关键场景手工，背景程序化）
→ 驱动：`environment.build_method`

---

### Step 2：产出 art-pipeline-config.json 草稿

根据 Step 1 所有答案组装 JSON，写入 `.allforai/game-design/art-pipeline-config.json`，`status` 置为 `"draft"`。

**active_nodes 生成规则：**

```
基础集合（根据 dimension 选择）：
  2D 游戏:  ["character-art-gen", "environment-art-gen", "ui-art-gen", "vfx-art-gen"]
  3D 游戏:  ["environment-art-gen", "ui-art-gen", "vfx-art-gen"]

条件加入：
  Q1 选"正交网格"或"等距"→ 加入 "tile-art-gen"
  Q5 选非"不需要"       → 加入 "concept-art-gen"（首次出现须在 bootstrap 先生成 node-spec）
  3D Q3 选"Blender 无头" → 加入 "3d-model-gen"（首次出现须先生成 node-spec）

条件移除：
  Q1 选"无地砖"          → 移除 "tile-art-gen"（若存在）
  Q2 选"无骨骼"          → character-art-gen 保留但 rig="frame_sequence"
```

**skipped_nodes 填写**：从全集（所有可能节点）中减去 active_nodes。

### Step 3：XV 交叉验证（可选）

```
若 mcp__plugin_meta-skill_ai-gateway__ask_model 可用：
  发送 art-pipeline-config.json 摘要（不含 cross_model_review）
  
  审查 prompt：
    "这是一个 {genre} 游戏的美术技术规格配置。
     请从技术风险、风格一致性、工具链可行性三个角度分析：
     1. active_nodes 组合是否有遗漏或冗余？
     2. 是否存在 AI 无法自动完成但被隐式假设为可用的步骤？
     3. 对 {dimension}/{style} 类型游戏有哪些同类产品踩过的坑？"
  
  将审查结论写入 config.cross_model_review[]（不自动修改其他字段，供用户参考）

若 ask_model 不可用：
  输出 "XV cross-validation unavailable"，跳过
```

### Step 4：写入最终 art-pipeline-config.json

将 `status` 从 `"draft"` 改为 `"final"`，合并 XV 结果，写回文件。

输出总结：
```
美术规格确认完成：
  维度：{dimension}，风格：{style}，动画：{animation_system}
  活跃节点：{active_nodes}
  [若有 XV 结果] XV 发现以下风险：{summary}

下一步：/run 将继续执行 art-spec-design 节点
```

---

## art-pipeline-config.json Schema

### 2D 卡通完整示例

```json
{
  "status": "final",
  "dimension": "2d",
  "style": "cartoon",
  "animation_system": "spine",
  "tileset": {
    "type": "grid",
    "tile_size": 128,
    "atlas": true
  },
  "character": {
    "rig": "spine_lite",
    "expressions": true,
    "bone_limit": 30
  },
  "vfx": {
    "approach": "sprite_sheet",
    "spine_fx": false
  },
  "environment": {
    "parallax_layers": 3
  },
  "concept_art": {
    "needed": false,
    "types": []
  },
  "toolchain": {
    "spine_licensed": true,
    "aseprite_available": false,
    "constraints": []
  },
  "active_nodes": [
    "tile-art-gen",
    "character-art-gen",
    "environment-art-gen",
    "ui-art-gen",
    "vfx-art-gen"
  ],
  "skipped_nodes": [],
  "cross_model_review": []
}
```

### 2D 像素风完整示例

```json
{
  "status": "final",
  "dimension": "2d",
  "style": "pixel",
  "animation_system": "frame",
  "tileset": {
    "type": "grid",
    "tile_resolution": "32x32",
    "atlas": true
  },
  "pixel": {
    "palette_size": 32,
    "anim_frames": 8,
    "dithering": "ordered"
  },
  "character": {
    "rig": "frame_sequence",
    "expressions": true
  },
  "vfx": {
    "approach": "sprite_sheet",
    "spine_fx": false
  },
  "environment": {
    "parallax_layers": 2
  },
  "concept_art": {
    "needed": false,
    "types": []
  },
  "toolchain": {
    "aseprite_available": true,
    "constraints": []
  },
  "active_nodes": [
    "tile-art-gen",
    "character-art-gen",
    "environment-art-gen",
    "ui-art-gen",
    "vfx-art-gen"
  ],
  "skipped_nodes": [],
  "cross_model_review": []
}
```

---

## 与下游节点的关系

| 下游节点 | 从 art-pipeline-config.json 读取的字段 | 用途 |
|---|---|---|
| `art-spec-design` | `tileset.*`, `character.*`, `vfx.*`, `pixel.*` | 生成资产清单时对齐规格（尺寸/骨骼/帧数） |
| `tile-art-gen` | `style`, `tileset.type`, `tileset.tile_size`, `pixel.*` | 切换生图策略（正常生图 vs 像素化管道） |
| `character-art-gen` | `character.rig`, `character.expressions` | 生成分层骨骼参考图 vs 帧动画参考图 |
| `vfx-art-gen` | `vfx.approach`, `vfx.spine_fx` | 决定帧序列规格 vs 参数文档 |
| `environment-art-gen` | `environment.parallax_layers`, `model_3d.*` | 图层数 / 3D 场景规格 |
| `ui-art-gen` | `style`, `toolchain.*` | 矢量图标 vs AI 生图图标策略 |
