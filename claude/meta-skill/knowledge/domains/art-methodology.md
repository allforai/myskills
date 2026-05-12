# Art Methodology

> 游戏美术方法论知识库。
> 供 art-concept skill 和各 art-gen 节点加载使用。
> 只存稳定的分类法、框架和权衡结构——不存工具版本、市场数据、竞品信息。

---

## 一、美术类型分类法

### 2D 通用（卡通 / 写实 / 手绘）

资产形式：PNG 位图，支持透明通道  
动画形式：帧序列（PNG 序列） 或 DragonBones 骨骼动画（JSON）  
典型资产：角色立绘、地砖图集、UI 图标、背景场景  
AI 生图可用性：**直接可用**（FLUX / Imagen 均支持）

### 2D 像素风（独立子类，特殊约束）

资产形式：限制调色板的 PNG，整数分辨率  
动画形式：帧序列（不用骨骼动画，插值会破坏像素硬边）  
典型分辨率：8×8 / 16×16 / 32×32 / 64×64 px per tile  
AI 生图可用性：**间接可用**（AI 生高分辨率图 → 程序化降采样 + 调色板量化）  
关键约束：
- 只能整数倍缩放（1x/2x/3x），任何分数缩放导致模糊
- 调色板必须锁定，运行时不得引入新颜色
- 抖动技术用于模拟调色板范围外的渐变

### 2D 矢量（SVG / Flash 风格）

资产形式：SVG（XML 文本），支持无损缩放  
动画形式：CSS/GSAP 补间，或转为位图帧序列  
典型用途：UI 图标、简单几何形状角色  
AI 生图可用性：**AI 直接写 SVG XML**（适合简单几何形图标，不适合质感类）

### 3D（低模 / 写实 / NPR 卡通渲染）

资产形式：GLB / FBX 网格 + 贴图（PNG/KTX）  
动画形式：骨骼动画（3D skeletal，存于 GLB 或单独 .anim 文件）  
典型格式：Blender → GLB/FBX → 游戏引擎  
AI 生图可用性：**不可直接生成**（AI 生参考图，程序化 Blender 脚本生低模占位）

### DragonBones 2D 骨骼动画

资产形式：DragonBones-compatible JSON + Atlas PNG；DragonBones 工程文件只是可选编辑源  
制作工具：项目内 JSON/Atlas 生成器 + Cocos Creator 内置运行时；DragonBones Pro GUI 只是可选人工编辑器  
AI 生图可用性：**部分可用**  
- AI 可直接生成 DragonBones-compatible JSON（变换动画：缩放/透明度/位移）  
- AI 可生成分层参考图（各骨骼部件独立层）  
- 复杂 IK/网格变形动画若无自动生成器与运行时验证，必须降级为自动 fallback 或标记 automation_limited；不得要求人工 GUI 作为自动闭环

### VFX 特效

常见形式：
- 帧序列（PNG sequence）：AI + ffmpeg 可生成
- DragonBones FX：简单变换可 AI 生成 JSON；复杂粒子路径需人工
- Shader 粒子：引擎内置，无需外部资产
- 程序化粒子：引擎粒子系统参数配置（AI 可生成配置文档）

---

## 二、理论锚点

### 通用视觉基础（全类型适用）

**色彩理论**（Itten《色彩的艺术》1961 / Albers《色彩互动》1963）
- 互补色对比：提高视觉活力（用于特殊地砖、BOSS 提示）
- 类比色和谐：统一章节色调（同一章节地砖使用相邻色相）
- 暖冷对比：修复前灰冷 → 修复后暖金（进度感设计）
- **游戏应用**：每章节色 token 应从色彩理论推导，不随意选色

**格式塔原则**（Wertheimer/Köhler 1920s）
- 接近性：相近的元素被感知为一组 → UI 分组、HUD 布局
- 相似性：相似的视觉属性 → 同类型资产共享形状语言
- 图底关系：前景与背景的清晰分离 → 避免角色与背景融为一体
- **游戏应用**：地砖边缘设计、UI 图标与背景的对比度

**轮廓可读性**（迪士尼角色设计传统）
- 原则：角色从纯黑剪影即可辨认，不依赖颜色或细节
- **游戏应用**：移动端 32-64px 小尺寸角色 → 剪影必须独特可辨
- 测试方法：将角色图片转为纯黑剪影，若仍可辨认则通过

**色彩功能编码**（游戏行业惯例）
- 危险/负面：红色系（炸弹、毒素、伤害）
- 安全/正面：绿色系（治愈、增益）
- 特殊/稀有：金/紫色系（稀有道具、特殊机制）
- **游戏应用**：特殊地砖（炸弹/闪电/彩虹）的颜色必须符合行业功能色编码

### 2D 动画

**动画12原则**（Thomas & Johnston《生命的幻觉》1981）
- 压扁拉伸（Squash & Stretch）：赋予物体重量感和弹性 → 消除特效的弹跳
- 预备动作（Anticipation）：动作前的反向运动 → 按钮按下前的微压缩
- 缓入缓出（Slow In & Out）：动作首尾慢、中间快 → DragonBones 动画曲线设置
- 弧线运动（Arcs）：有机物体沿弧线运动，而非直线
- 夸张（Exaggeration）：强化动作幅度以增强表达力 → VFX 的尺寸夸张
- **游戏应用**：DragonBones 动画曲线应遵循缓入缓出；VFX 的消除特效应有压扁-拉伸弹跳

**游戏手感 / Juice**（Nijman, GDC 2013《The Art of Screenshake》）
- 核心原则：每个玩家操作都应有即时、夸张的多感官反馈
- 具体手段：屏幕震动、粒子喷射、音效叠加、UI 数字弹出
- **游戏应用**：消除特效设计 → 地砖消除时有缩放 + 粒子扩散 + 闪光

### 像素风专项

**整数缩放约束**（物理定律，非惯例，不可妥协）
- 原理：像素艺术依赖精确的像素边界，任何分数缩放插值导致相邻像素混合 → 模糊
- 实现：目标设备分辨率必须是游戏逻辑分辨率的整数倍
- 常见错误：在 1920×1080 屏幕上运行 320×200 逻辑分辨率 → 只有 ×6（1920/320）才精确

**色相偏移调色板**（LoSpec 社区规范，Helm《Pixel Art for Game Developers》）
- 原理：纯粹降低明度得到的深色会变成"泥浆色"；正确做法是同时偏移色相（暗处偏暖或偏冷）
- 示例：绿色草地 → 亮部偏黄绿（HSL: H=100），暗部偏蓝绿（HSL: H=150）
- **游戏应用**：设计调色板时，从亮到暗必须同时调整 Hue，不只调 Lightness

**帧数经济学**
- 4帧：走路动画可信（常见于超简像素风）
- 8帧：走路流畅（主流像素风独立游戏标准）
- 16帧：精细（高质量，制作成本约为8帧的2倍）
- 原则：在预算内最大化关键帧数，次要动作（待机/受击）可用更少帧

**抖动技术（Dithering）**
- Bayer 矩阵：规则几何抖动，有秩序感，适合机械/科技风格
- 有序抖动：手工调整的抖动模式，更自然，接近手工像素艺术
- **用途**：在 16-32 色的调色板内模拟渐变效果，如天空渐变、阴影过渡

### 3D

**PBR（物理渲染，Physically Based Rendering）**
- 金属度/粗糙度工作流（Metallic/Roughness）：当前主流游戏引擎标准
- 贴图通道：Albedo + Normal + Metallic + Roughness（+ AO / Emissive）
- **移动端注意**：PBR 消耗较高，低端设备考虑简化着色器（Toon Shader）

**面数预算与 LOD**
- 移动端角色：500-2000 面（低端）/ 2000-5000 面（中高端）
- 移动端场景物件：100-500 面/件（可批量渲染的静态对象更经济）
- LOD（Level of Detail）：近处高模，远处低模，引擎自动切换

**卡通渲染 / NPR（Non-Photorealistic Rendering）**
- 描边：后处理描边（Shader，基于法线/深度检测）
- 色阶渲染：光照分区（2-3 色阶）替代平滑渐变 → 手绘感
- **适用场景**：动森类、塞尔达类风格化游戏首选，移动端性能优于写实 PBR

**UV 展开规范**
- 接缝位置：放在不显眼的区域（背面、腋下、发际线）
- 纹理密度均匀：关键面（正面、头部）分配更多 UV 空间
- 镜像使用：对称模型可 UV 镜像，贴图大小减半

### UI 美术

**Fitts 定律**
- 公式：点击时间 = a + b × log₂(2D/W)（D=距离，W=目标大小）
- **移动端最小触控区域：44×44 px**（iOS HIG / Android Material 标准）
- UI 图标的可视尺寸可小于 44px，但点击热区（hit area）不得小于 44px

**WCAG 2.1 对比度标准**
- 普通文字（<18pt）：前景色与背景色对比度 ≥ 4.5:1
- 大文字（≥18pt）/ 图标：对比度 ≥ 3:1
- **游戏应用**：HUD 文字、血条数字、道具计数必须满足 3:1 最低要求

**图标视觉隐喻**
- 功能图标需有普遍认知的视觉类比物（"家"→房子轮廓，"返回"→左箭头）
- 避免过度抽象或文化特定的隐喻（某些手势/符号在不同文化含义不同）
- **游戏专有图标**（如道具、货币）可打破惯例，但需在游戏内有明确教学

---

## 三、生产流水线模式

每种美术类型一条标准链路（稳定结构，工具名不固定）：

```
2D 通用:
  概念图（AI生图/速写）→ 精修（位图编辑器）→ PNG 导出 → Atlas 打包 → 引擎导入

2D 像素风:
  AI 生高分辨率参考图 → PIL 降采样（最近邻插值）→ pngquant 调色板量化
  → [可选] Aseprite 手工修整 → Atlas 打包 → 引擎导入

DragonBones 骨骼动画:
  分层参考图（AI 生成各部件）→ 项目脚本生成 DragonBones-compatible JSON + Atlas
  → Preview 渲染 → Runtime 导入验证
  [可选] DragonBones Pro GUI 仅作为人工编辑器，不是自动化必需项

3D:
  概念图（AI参考）→ Blender 建模 → UV 展开 → 贴图绘制（PBR/手绘）
  → FBX/GLB 导出 → 引擎导入 → LOD 设置

矢量 UI 图标:
  AI 直写 SVG XML（几何形状）或 AI 生图（质感图标）→ 导出 PNG → Atlas 打包
```

---

## 四、决策树骨架（art-concept 问答框架）

```
入口：读取 art_overview.dimension + art_overview.style

dimension = "2d" AND style ≠ "pixel":
  → 地砖系统（grid/isometric/无地砖）
      └─ 无地砖 → 移除 tile-art-gen from active_nodes
  → 角色动画方案（frame/dragonbones-compatible/dragonbones_mesh 自动降级）
  → 特效方案（sprite_sheet/dragonbones_fx/shader_particle）
  → 场景层次（1层/2-3层/多层视差）
  → 概念原画需求（无/角色/场景/两者）
      └─ 有需求 → 加入 concept-art-gen（须先生成 node-spec）
  → 工具链约束（自动生成器/运行时导入/可选 GUI 编辑器）

dimension = "2d" AND style = "pixel":
  → 地砖分辨率（8/16/32/64 px）
  → 调色板大小（8/16/32/256色）
  → 动画帧数预算（4/8/16帧）
  → 帧动画自动化路径（PIL/脚本/可选 Aseprite CLI）
  → 概念原画需求（同上）
  → 工具链约束（自动化优先，GUI 仅可选）

dimension = "3d":
  → 面数预算（低模/中模/不限）
  → 贴图工作流（PBR/卡通平涂/手绘）
  → 骨骼动画来源（Blender无头/外包）
  → VFX方案（引擎粒子/帧序列叠加/Shader）
  → 场景构建（手工/程序化/混合）
```

---

## 五、权衡框架

### DragonBones vs 帧序列

| 维度 | DragonBones 胜出 | 帧序列胜出 |
|---|---|---|
| 换装/染色 | ✅（运行时替换纹理/骨骼） | ❌（需为每套服装单独制作） |
| 表情变体 | ✅（面部骨骼独立控制） | 中等（多表情需多帧） |
| 补间平滑 | ✅（骨骼自动插值） | ❌（帧间过渡不自然） |
| 手工质感 | ❌（骨骼动画有"数字感"） | ✅（帧帧手绘，有纸张感） |
| 复杂 VFX | ❌（骨骼不适合碎片/粒子） | ✅（帧序列可表达任意效果） |
| **LLM 可生成性**（主因） | ✅ **开放 JSON 格式，LLM 可直接生成变换动画** | ⚠️ 帧内容需逐帧生图，LLM 不擅长 |
| 工具授权成本 | ✅（格式/运行时可自动化；Pro GUI 可选） | 低（PIL/脚本可自动化；Aseprite GUI 可选） |
| 动画师学习曲线 | 中 | 低（逐帧绘制） |

**推荐规则**：
- AI/LLM 主导生产管线 → **DragonBones**（开放 JSON，LLM 可直接生成变换动画，是首选的核心理由）
- 角色数量多、有换装需求 → DragonBones
- 小团队、像素风 → 帧序列
- 简单 VFX（缩放/透明度/位移变换）→ DragonBones JSON（LLM 直接生成）
- 复杂 VFX（粒子/碎片/流体）→ 帧序列

### 2D vs 3D（移动端）

| 维度 | 2D 胜出 | 3D 胜出 |
|---|---|---|
| 制作周期 | ✅（美术资产快速迭代） | ❌（建模/绑骨周期长） |
| 文件体积 | ✅（PNG Atlas 可压缩） | ❌（网格+贴图体积大） |
| 视觉精细度 | 取决于风格 | ✅（光照/阴影更真实） |
| 摄像机自由 | ❌（固定视角或有限旋转） | ✅（任意角度） |
| 资产复用 | 中（换色/镜像） | ✅（不同贴图共用同骨骼） |
| 渲染性能 | ✅（Draw Call 可优化） | 视实现，通常更重 |

**推荐规则**：
- 休闲/卡通/故事驱动游戏 → 2D
- 需要摄像机旋转、深度感玩法、大量角色复用 → 3D

### AI 生图 vs 人工（AI 可用性边界）

| 资产类型 | AI 直接可用 | 需人工介入 |
|---|---|---|
| 2D 卡通角色立绘 | ✅ 生成后需 QA | 最终精修 |
| 2D 环境背景 | ✅ Imagen 4 擅长 | 最终精修 |
| 像素风地砖 | ⚠️ 间接（降采样管道） | 精细像素手工 |
| DragonBones 骨骼动画 | ⚠️ 变换类 AI 可生成 JSON | ✅ 复杂动画需人工 |
| 3D 网格模型 | ❌（低模可 Blender 脚本） | 高质量必须人工 |
| UI 矢量图标 | ✅ 直写 SVG | 品牌级图标需精修 |
| 概念原画 | ✅ 参考用 | 最终稿需人工 |
| PBR 贴图 | ❌ | ✅ 必须人工 |

---

## 六、质量评审维度（art-qa 验收标准来源）

art-qa 节点对所有 `current_state=temp` 的资产按以下5个维度逐类评分（1-5分）：

1. **风格一致性（Style Consistency）**
   - 所有资产是否共享同一视觉语言（相同的线条粗细、圆角半径、色调风格）
   - 不同类别（地砖/角色/UI）之间无明显断层
   - 评分 < 3 → 对应 art-gen 节点回到 revision-requested

2. **颜色合规性（Color Compliance）**
   - 配色是否符合 `art-tokens.json` 中的标准色值
   - 各章节地砖是否使用了对应的 color token
   - UI 图标是否仅使用规范色值

3. **功能可识别性（Functional Legibility）**
   - 特殊地砖（炸弹/闪电/彩虹）在 32px 展示尺寸下功能是否可辨
   - UI 图标在 32px 下是否清晰
   - 地图区域的修复前/后状态是否有足够视觉差异

4. **角色一致性（Character Consistency）**
   - 所有 NPC 的比例、轮廓线粗细是否统一
   - 主角在不同表情变体间是否保持身份可辨

5. **资产完整性（Coverage）**
   - 已生成样本是否覆盖所有关键视觉区域
   - 记录缺口清单（gap list）供下次迭代

---

## Asset Lifecycle States

| State | Meaning | Set by | Can overwrite? |
|-------|---------|--------|----------------|
| `placeholder` | Geometry shape / solid color stand-in | art-spec-design | Yes |
| `temp` | AI-generated or free asset, unreviewed | ai-art-generation | Yes |
| `alpha` | Passed initial QA (score ≥ 3/5) | art-qa | Yes |
| `final` | Approved by discipline_owner | art-qa gate | Yes (only by re-approval) |
| `locked` | Accepted into release build | launch-prep | **No** — create new asset_id |

**Regression rule:** States may only advance forward. A `final` asset cannot regress to `alpha`
unless a new revision cycle is opened (gate_status → revision-requested). A `locked` asset
is immutable — do not regenerate it; if replacement is needed, create a new asset_id.

## 七、常见失误模式

| 失误 | 症状 | 预防 |
|---|---|---|
| 过早细化 | art-concept 阶段就定死像素级数值，样本验收后无法调整 | Step 1 只问方向性决策，具体数值留 art-spec-design |
| 风格混搭 | 不同资产类别使用不同风格参考图，导致视觉割裂 | 所有 AI 生图 prompt 共享同一 `style_prompt_prefix` |
| 忽略工具链约束 | 选了 dragonbones_mesh 但没有自动生成器/运行时导入 adapter，或选了 Aseprite CLI 但未安装 | Step 1 Q6 明确问自动化工具链约束，写入 config 后节点执行时检查 |
| 低估特效复杂度 | 将 DragonBones FX 粒子路径动画标记为 AI 可完全自动化，但没有可执行生成器与预览验收 | 区分变换类（AI 可生成）vs 网格/IK/粒子路径（需自动 fallback 或 automation_limited） |
| 像素化参数错误 | PIL resize 使用双线性插值（BILINEAR）而非最近邻（NEAREST），导致边缘模糊 | art-concept skill 中明确注明 `Image.NEAREST` |
| 忽略整数缩放 | 像素风地砖在非整数倍分辨率屏幕上显示模糊 | 验收时必须在目标设备分辨率测试，而非 PC 模拟器 |
