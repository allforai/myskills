# Art Tools — AI 可调用工具能力矩阵

> 以 AI 可调用性为第一维度组织。
> 不按工具用途分类，而按"AI 如何调用它"分类。
> 供 art-concept skill 和各 art-gen 节点执行时选择策略。

---

## 一、MCP 直接调用（ai-gateway 工具）

### flux_generate_image

```
invoke:  MCP tool — mcp__plugin_meta-skill_ai-gateway__flux_generate_image
model:   FLUX 2 Pro（fal.ai）
格式:    square(1:1) / portrait_4_3(3:4) / portrait_16_9(9:16)
requires_install: false（需 FAL_KEY 环境变量）

擅长:
  - 2D 卡通/手绘风格角色立绘
  - 游戏地砖（卡通/写实风格）
  - UI 图标（质感类，如货币/道具）
  - 环境场景（卡通风格）

限制:
  - 像素风效果差（边缘不硬，调色板不受控）
  - 无法控制精确构图（右上角放特定物体等）
  - 文字渲染不可靠
  - 透明背景支持有限

fallback: generate_image（Imagen 4）
```

### generate_image（Imagen 4）

```
invoke:  MCP tool — mcp__plugin_meta-skill_ai-gateway__generate_image
model:   Google Imagen 4
格式:    1:1 / 3:4 / 9:16（portrait 系）
requires_install: false（需 GOOGLE_API_KEY 环境变量）

擅长:
  - 环境/背景场景（写实/半写实）
  - 9:16 竖版场景（全屏背景）
  - 自然光照场景（森林/海边/建筑）

限制:
  - 小尺寸 UI 图标细节不佳
  - 纯卡通/夸张风格弱于 FLUX
  - 像素风不可用

fallback: flux_generate_image
```

### openrouter_generate_image（GPT / Gemini 生图）

```
invoke:  MCP tool — mcp__plugin_meta-skill_ai-gateway__openrouter_generate_image
model:   通过 model 参数指定（如 gpt-image-1、gemini-2.0-flash-exp-image-generation）
requires_install: false（需 OPENROUTER_API_KEY 环境变量）

擅长:
  - 风格多样（通过 model 参数切换）
  - 概念设计/情绪板参考图
  - 特殊风格需求

限制:
  - 速度慢于 FLUX/Imagen
  - 成本较高
  - 可用 model 随 OpenRouter 接入变化

fallback: flux_generate_image
```

### ask_model（XV 交叉验证）

```
invoke:  MCP tool — mcp__plugin_meta-skill_ai-gateway__ask_model
用途:    XV 交叉验证（art-concept Step 3）
requires_install: false（需 OPENROUTER_API_KEY 环境变量）
fallback: 跳过 XV，输出 "XV cross-validation unavailable"
```

---

## 二、Bash CLI 工具

### ImageMagick

```
invoke:  Bash — convert / mogrify / composite / identify
requires_install: true
  macOS:  brew install imagemagick
  Linux:  apt-get install imagemagick
  检测:   which convert

能力:
  - 格式转换（PNG/JPEG/WebP/GIF/BMP）
  - 批量缩放（mogrify -resize 128x128 *.png）
  - 图片合成（composite）
  - 颜色空间转换
  - 元数据读取（identify -verbose）

常用命令模板:
  缩放:    convert input.png -resize 128x128! output.png  （!强制拉伸，不保持比例）
  格式转:  convert input.png output.webp
  批量转:  mogrify -format png *.jpg

limitation: 不适合像素风（缩放默认用 Lanczos 插值，导致模糊）
fallback:   Python PIL（像素风必须用 PIL + Image.NEAREST）
```

### pngquant

```
invoke:  Bash — pngquant --colors N --quality min-max input.png
requires_install: true
  macOS:  brew install pngquant
  Linux:  apt-get install pngquant
  检测:   which pngquant

能力:
  - PNG 调色板量化（将 True Color PNG 减少到 N 色）
  - 核心用途：像素风调色板锁定
  - 输出：input-fs8.png（默认命名）

常用命令模板:
  量化到 16 色:  pngquant --colors 16 --quality 80-100 input.png -o output.png
  量化到 32 色:  pngquant --colors 32 input.png -o output.png
  覆盖原文件:    pngquant --colors 16 --ext .png --force input.png

limitation: 只减色，不改变分辨率；Floyd-Steinberg 抖动可能引入噪点
fallback:   Python PIL.Image.quantize()（质量略差）
```

### Aseprite CLI（batch 模式）

```
invoke:  Bash — aseprite --batch [options] input.png -o output.png
requires_install: true（商业软件，约 $20；或从源码编译免费版）
  macOS:  /Applications/Aseprite.app/Contents/MacOS/aseprite
  检测:   which aseprite  或  test -f /Applications/Aseprite.app/Contents/MacOS/aseprite
  注意:   需将 aseprite 加入 PATH 或使用完整路径

能力（CLI batch 模式）:
  - 颜色模式转换（RGB → Indexed，绑定调色板）
  - 帧序列导出（--save-as frames/frame{frame}.png）
  - 调色板应用（--palette palette.gpl）
  - 图层平铺

常用命令模板:
  转为 indexed 模式:
    aseprite --batch input.png --color-mode indexed --palette-size 16 -o output.png
  导出帧序列:
    aseprite --batch animation.ase --save-as frames/frame{frame}.png
  应用调色板:
    aseprite --batch input.png --palette lospec-palette.gpl -o output.png

limitation:
  - GUI 功能（绘制、骨骼、手工描边）不可用于 CLI
  - 源码编译版不包含 Skia 渲染器（某些功能受限）

fallback: Python PIL（无调色板绑定能力，但可做降采样+量化）
```

### TexturePacker CLI

```
invoke:  Bash — TexturePacker --sheet output.png --data output.json input_folder/
requires_install: true（商业软件，有免费版功能限制）
  macOS:  /usr/local/bin/TexturePacker
  检测:   which TexturePacker

能力:
  - Sprite Atlas 打包（多 PNG → 单图集 + 坐标 JSON）
  - 支持 Cocos Creator / Unity / Phaser 等多种数据格式
  - 自动旋转、修剪透明边缘、最大化填充

常用命令模板:
  基础打包:
    TexturePacker --format cocos2d --sheet atlas.png --data atlas.plist input/
  JSON 格式:
    TexturePacker --format json --sheet atlas.png --data atlas.json input/

limitation: 免费版有帧数限制；需安装（非所有 CI 环境预装）
fallback:   Cocos Creator 内置 Atlas 自动打包（项目内无需外部工具）
            Python PIL 手工合图（质量较低，坐标需手工记录）
```

### ffmpeg

```
invoke:  Bash — ffmpeg [options]
requires_install: true（部分系统预装，macOS 不预装）
  macOS:  brew install ffmpeg
  Linux:  apt-get install ffmpeg
  检测:   which ffmpeg

能力:
  - 帧序列 → 视频预览（用于 art-qa 的 VFX 预览）
  - 视频 → 帧序列（拆分参考视频）
  - GIF 生成（用于 HTML 报告中的动画预览）
  - 格式转换

常用命令模板:
  帧序列 → MP4:
    ffmpeg -framerate 24 -i frames/frame%04d.png -c:v libx264 -pix_fmt yuv420p output.mp4
  帧序列 → GIF:
    ffmpeg -framerate 12 -i frames/frame%04d.png output.gif
  视频 → 帧序列:
    ffmpeg -i input.mp4 frames/frame%04d.png

limitation: 大文件转换耗时；GIF 质量/体积比差于 WebP
fallback:   跳过视频预览，HTML 报告中仅展示静帧
```

---

## 三、Python 脚本（PIL/Pillow）

```
requires_install: pip install Pillow
  检测:   python3 -c "from PIL import Image; print('ok')"
  通常预装于项目 Python 环境或可快速安装
```

### 像素化管道（像素风核心，最重要）

```python
# 步骤：AI 生高分辨率图 → 最近邻降采样 → 调色板量化

from PIL import Image

def pixelate(input_path: str, output_path: str, target_size: tuple, palette_colors: int = 32):
    """
    input_path:    AI 生成的高分辨率图（如 1024x1024）
    target_size:   目标像素分辨率（如 (32, 32)）
    palette_colors: 调色板颜色数（8/16/32/256）
    """
    img = Image.open(input_path).convert("RGBA")
    
    # 最近邻插值（保留硬边，像素风关键）
    # 绝对不能用 BILINEAR 或 LANCZOS（会导致模糊）
    img_small = img.resize(target_size, Image.NEAREST)
    
    # 调色板量化（可选，配合 pngquant CLI 效果更好）
    img_rgb = img_small.convert("RGB")
    img_quantized = img_rgb.quantize(colors=palette_colors, method=Image.Quantize.MEDIANCUT)
    
    img_quantized.save(output_path)

# 调用示例（在 art-gen 节点中使用）：
# pixelate("ai_generated_1024.png", "tile_pixel_32.png", (32, 32), palette_colors=32)
# 然后用 pngquant 进一步锁定调色板：
# pngquant --colors 32 --ext .png --force tile_pixel_32.png
```

**重要**：降采样必须用 `Image.NEAREST`（最近邻插值），这是不可妥协的技术约束。其他插值方法（BILINEAR/BICUBIC/LANCZOS）会在像素边缘产生混合颜色，破坏像素风效果。

### Atlas 合图（TexturePacker 不可用时的降级方案）

```python
from PIL import Image
import json

def pack_atlas(image_paths: list, output_image: str, output_json: str, padding: int = 2):
    """简单的行式 Atlas 打包，适合小规模资产"""
    images = [(path, Image.open(path)) for path in image_paths]
    total_width = sum(img.width + padding for _, img in images) - padding
    max_height = max(img.height for _, img in images)
    
    atlas = Image.new("RGBA", (total_width, max_height), (0, 0, 0, 0))
    frames = {}
    x_offset = 0
    
    for path, img in images:
        atlas.paste(img, (x_offset, 0))
        name = path.split("/")[-1].replace(".png", "")
        frames[name] = {"x": x_offset, "y": 0, "w": img.width, "h": img.height}
        x_offset += img.width + padding
    
    atlas.save(output_image)
    with open(output_json, "w") as f:
        json.dump({"frames": frames, "meta": {"image": output_image}}, f, indent=2)
```

### 程序化占位帧生成（DragonBones/人工资产的占位）

```python
from PIL import Image, ImageDraw, ImageFont

def generate_placeholder_frame(width: int, height: int, label: str, output_path: str,
                                 bg_color=(180, 180, 200), text_color=(60, 60, 80)):
    """生成带尺寸标注的占位帧，用于 DragonBones 复杂动画/3D 资产的 human_gate 期间"""
    img = Image.new("RGBA", (width, height), bg_color + (255,))
    draw = ImageDraw.Draw(img)
    
    # 边框
    draw.rectangle([0, 0, width-1, height-1], outline=text_color, width=2)
    # 对角线（占位符标准样式）
    draw.line([0, 0, width, height], fill=text_color, width=1)
    draw.line([width, 0, 0, height], fill=text_color, width=1)
    # 标签
    draw.text((width//2, height//2), label, fill=text_color, anchor="mm")
    draw.text((width//2, height//2 + 16), f"{width}×{height}", fill=text_color, anchor="mm")
    
    img.save(output_path)
```

---

## 四、AI 直接生成（无需外部工具）

### SVG 矢量图标

**适用场景**：简单几何形状的 UI 图标（home、close、back、check、menu 等）

AI 直接编写 SVG XML 文件，无需调用任何工具：

```xml
<!-- 示例：home 图标（48×48） -->
<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48">
  <!-- 屋顶 -->
  <polygon points="24,8 4,28 44,28" fill="#7EC8A0" stroke="#5A9A70" stroke-width="2" stroke-linejoin="round"/>
  <!-- 门 -->
  <rect x="18" y="30" width="12" height="16" rx="2" fill="#5A9A70"/>
  <!-- 主体 -->
  <rect x="6" y="26" width="36" height="20" rx="2" fill="#A8D8B0"/>
</svg>
```

**适用图标类型**：
- 导航类：home、back_arrow、close、menu
- 状态类：lock、check、star（骨架）
- 简单形状：circle、square、triangle 变体

**不适用**：
- 质感类图标（货币/道具，有光泽/渐变/细节）→ 用 flux_generate_image
- 复杂多层图标（需 20+ 个 SVG 元素）→ 用 flux_generate_image

### JSON 规格文档

art-gen 节点对复杂动画/3D高模资产生成规格文档或直接生成 DragonBones JSON：

**变换类 VFX（AI 直接生成 DragonBones JSON）：**
```json
{
  "frameRate": 30,
  "name": "fx_tile_disappear",
  "armature": [{
    "type": "Armature",
    "frameRate": 30,
    "bone": [{"name": "root"}, {"name": "tile", "parent": "root"}],
    "animation": [{
      "duration": 12,
      "name": "disappear",
      "bone": [{
        "name": "tile",
        "frame": [
          {"duration": 3, "tweenEasing": 0, "transform": {"scX": 1.15, "scY": 1.15, "a": 1}},
          {"duration": 5, "tweenEasing": 0, "transform": {"scX": 0.3, "scY": 0.3, "a": 0.6}},
          {"duration": 4, "tweenEasing": 0, "transform": {"scX": 0, "scY": 0, "a": 0}}
        ]
      }]
    }]
  }]
}
```

**复杂动画（IK/网格变形，仍需人工，生成规格文档）：**
```json
{
  "asset_id": "fx_firefly_chain",
  "type": "dragonbones_animation",
  "status": "spec_ready_pending_production",
  "production_notes": "IK 粒子路径动画，需 DragonBones GUI 制作",
  "keyframes": [
    {"frame": 1, "desc": "萤火虫从触发点聚集"},
    {"frame": 12, "desc": "光链完全延伸，全屏覆盖"}
  ]
}
```

### HTML 审查报告

art-qa、art-gen 各节点输出的 HTML 报告由 AI 直接生成（静态 HTML，深色主题）。

---

## 五、无头模式（需安装）

### Blender --background --python

```
invoke:  Bash — blender --background --python script.py
requires_install: true
  macOS:  brew install --cask blender  或从 blender.org 下载
  检测:   which blender  或  test -f /Applications/Blender.app/Contents/MacOS/blender
  PATH:   macOS 需 export PATH="/Applications/Blender.app/Contents/MacOS:$PATH"

能力（通过 Python bpy 模块）:
  - 程序化低多边形 3D 模型生成（几何体/参数化形状）
  - 材质/贴图应用（通过 Python 设置节点）
  - GLB/FBX/OBJ 导出
  - 批量渲染（生成参考图）
  - UV 自动展开（Smart UV Project）

示例：生成一个低模房子

fallback: 输出 3D 规格文档（JSON），标记 human_gate=true，等待外包建模交付
limitation: 程序化只适合规律性几何体（建筑/道具）；有机形体（角色）必须手工
```

---

## 六、需人工介入（不可自动化）

以下情况 art-gen 节点执行策略：**生成规格文档（JSON）+ 程序化占位资产（PNG）+ human_gate = true**

| 资产类型 | 原因 | 节点策略 |
|---|---|---|
| DragonBones 复杂动画（IK/网格） | 复杂骨骼/网格变形需 DragonBones GUI | AI 生成变换类 JSON + 关键帧参考图；复杂部分 human_gate |
| 高质量像素手绘 | 色相偏移/手工描边/精细抖动需人眼判断 | 生成低质量程序化像素化占位 |
| PBR 贴图精修 | Substance Painter 无 CLI；质量靠审美 | 生成贴图规格 JSON + AI 参考图 |
| ZBrush 高模雕刻 | 纯 GUI，无自动化接口 | 生成低模占位（Blender）+ 规格文档 |
| Live2D 面部动画 | Live2D Cubism 无 CLI | 生成 Live2D 参数规格 JSON |
| 复杂角色 3D 建模 | 有机形体需艺术家审美和技巧 | Blender 生成几何占位 + 详细规格 |

---

## 工具能力矩阵（节点执行策略速查）

| 资产类型 | MCP 生图 | Bash CLI | Python PIL | AI 直写 | 人工必须 |
|---|---|---|---|---|---|
| 2D 地砖（卡通） | ✅ flux | - | - | - | QA |
| 2D 地砖（像素风） | ⚠️ 生高分图→降采样 | ✅ pngquant | ✅ resize(NEAREST) | - | QA |
| 角色立绘（卡通） | ✅ flux | - | - | - | QA |
| 角色骨骼分层参考 | ✅ flux(分层参考) | - | - | - | QA → DragonBones制作 |
| DragonBones 变换动画 | ❌ | ❌ | ❌ | ✅ 直接生成JSON | QA 验收 |
| DragonBones IK/网格动画 | ❌ | ❌ | ❌ | ✅ 规格JSON | ✅ 人工GUI制作 |
| 3D 低模（程序化） | ❌ | ✅ Blender无头 | - | ✅ 规格JSON | QA |
| 3D 高质量模型 | ❌ | ❌ | ❌ | ✅ 规格JSON | ✅ |
| UI 图标（矢量形状） | - | - | - | ✅ SVG | QA |
| UI 图标（质感类） | ✅ flux | - | - | - | QA |
| VFX 参考帧 | ✅ flux | - | - | - | QA |
| VFX 帧序列占位 | - | ✅ ffmpeg | ✅ PIL绘占位 | - | QA |
| 背景/环境场景 | ✅ Imagen | - | - | - | QA |
| 概念原画（参考） | ✅ flux/Imagen | - | - | - | QA |
| Sprite Atlas 打包 | - | ✅ TexturePacker | ✅ PIL合图 | - | - |

**图例**：✅ 可用 / ⚠️ 间接可用 / ❌ 不可用 / QA = 需人工 QA 验收

---

## 工具可用性检测脚本（art-gen 节点执行前运行）

```python
import shutil, subprocess, sys

def check_tools() -> dict:
    """检测当前环境下哪些工具可用，供 art-gen 节点选择策略"""
    results = {}
    
    # MCP 工具（由 skill 环境决定，此处只检测 API Key）
    import os
    results["flux"] = bool(os.environ.get("FAL_KEY"))
    results["imagen"] = bool(os.environ.get("GOOGLE_API_KEY"))
    results["openrouter"] = bool(os.environ.get("OPENROUTER_API_KEY"))
    
    # CLI 工具
    results["imagemagick"] = bool(shutil.which("convert"))
    results["pngquant"] = bool(shutil.which("pngquant"))
    results["ffmpeg"] = bool(shutil.which("ffmpeg"))
    results["texturepacker"] = bool(shutil.which("TexturePacker"))
    
    # Aseprite（多路径检测）
    aseprite_paths = [
        shutil.which("aseprite"),
        "/Applications/Aseprite.app/Contents/MacOS/aseprite",
    ]
    results["aseprite"] = any(p and __import__("os").path.isfile(p) for p in aseprite_paths if p)
    
    # Blender
    blender_paths = [
        shutil.which("blender"),
        "/Applications/Blender.app/Contents/MacOS/blender",
    ]
    results["blender"] = any(p and __import__("os").path.isfile(p) for p in blender_paths if p)
    
    # Python PIL
    try:
        from PIL import Image
        results["pillow"] = True
    except ImportError:
        results["pillow"] = False
    
    return results
```
