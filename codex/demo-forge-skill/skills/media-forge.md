---
name: media-forge
description: >
  Use when the user asks to "collect media", "find images for demo",
  "upload demo images", "media-forge", "富媒体采集", "采集图片",
  "上传素材", "媒体锻造", "demo images", "demo videos",
  or mentions media acquisition, image collection, video sourcing for demos.
  Requires demo-plan.json with Step 1-M media field annotations.
version: "1.0.0"
---

# Media Forge — 富媒体锻造

> 搜索优先、AI 补缺、本地存储、应用上传——零外部链接的演示级素材管线。

## 铁律（4 条，强制执行）

1. **所有素材必须下载到本地 `assets/`，零外链** — 不得引用任何外部图床、CDN 或第三方 URL
2. **灌入时必须走应用上传 API，数据库只存服务端地址** — `server_url` 必须是应用自身域名路径
3. **Brave 搜索优先，WebSearch 降级，AI 生成兜底，禁止占位符** — 任何 placeholder / lorem ipsum 图片均视为失败
4. **`upload-mapping.json` 中 `external_url_count` 必须为 0（硬校验）** — 完成时扫描全部 `server_url`，含外部域名即报错

---

## 定位

```
demo-forge 内部三阶段 + 独立媒体管线:
  demo-design（规划）  →  media-forge（本技能）+ demo-execute（灌入）  →  demo-verify（验证）
  规划该生成什么数据       采集/生成/加工/上传素材       灌入业务数据              打开产品逐项验证
  纯设计不执行            独立可运行                  消费设计+素材             产出问题清单路由回修
```

**独立可运行**：可被 `demo-forge` 编排调用，也可单独使用（只要 `demo-plan.json` 存在）。

**前提**：必须先运行 `demo-design`，生成 `.allforai/demo-forge/demo-plan.json`（含 Step 1-M 媒体字段标注）。

---

## 快速开始

```
/demo-forge media              # 完整管线（M1 → M6）
/demo-forge media --type image # 仅处理图片类素材
/demo-forge media --reentry    # 从 verify-issues 重入，只处理问题项
```

**重入模式**：当 `demo-verify` 产出 `verify-issues.json` 且其中有 `route_to="media"` 的问题时，编排器会回调本技能。此时不全量重做，而是按问题类型回到对应步骤处理。详见「重入模式」章节。

---

## 工作流

### M1: 需求盘点

读取 `demo-plan.json` 中 Step 1-M 的 `media_fields` 数组，建立完整需求清单。

**操作**：

1. 解析每条 `media_fields` 记录：`entity`, `field`, `media_type`, `purpose`, `dimensions`, `count`, `search_keywords`, `style_notes`, `upload_endpoint`
2. 按 `media_type` 分组（image / video / document / audio）
3. 按 `purpose` 子分组（头像、封面、详情图、Banner 等）
4. 汇总每组需求量

**输出**：进度摘要表

```
媒体需求盘点:
  image:    120 项（头像 30 | 封面 50 | 详情图 30 | Banner 10）
  video:      8 项（产品视频 5 | 教程 3）
  document:   5 项（合同模板 5）
  audio:      3 项（语音消息 3）
  ────────────────
  总计:     136 项
```

---

### M2: 搜索采集（主力）

对 M1 盘点的每组需求，按优先级搜索并下载素材。

**搜索优先级**：

1. **Brave Search MCP**（首选）— `mcp__brave-search__brave_web_search`
2. **WebSearch 工具**（Brave 不可用或配额耗尽时降级）

**关键词构建**：

- 基础词：`search_keywords` 数组中的关键词
- 修饰词：从 `style_notes` 提取风格要求（如"白底"、"电商风格"）
- 组合策略：`"{keyword} {style} high resolution free stock"` / `"{keyword} {style} 高清 免费素材"`
- **同一 `purpose` 组使用同一组关键词**，保证风格一致性

**图片搜索**：

```
关键词: "{search_keywords} {style_notes} high resolution"
示例:  "家居用品 白底产品图 电商风格 high resolution free stock photo"
```

**视频搜索**：

```
关键词: "{search_keywords} {style_notes} video footage"
示例:  "厨房电器 产品展示 short video clip"
```

**下载规范**：

- 目标目录：`assets/{category}/`（category 由 purpose 映射：头像→avatars、封面→covers、详情图→details、横幅→banners、视频→videos）
- 文件命名：`{TYPE}-{NNN}.{ext}`
  - 图片：`IMG-001.webp`, `IMG-002.webp`
  - 视频：`VID-001.mp4`, `VID-002.mp4`
  - 文档：`DOC-001.pdf`
  - 音频：`AUD-001.mp3`
- 每个搜索结果立即下载到本地，不保留外部链接

**进度跟踪**：

```
M2 搜索采集: 108/136 已满足，缺口 28
  image:  100/120（缺口 20 — 详情图风格不符被跳过）
  video:    5/8  （缺口 3 — 短视频资源不足）
  document: 0/5  （搜索不适用，全部交 M3）
  audio:    3/3  （全部满足）
```

---

### M3: AI 生成补缺

**仅对 M2 未满足的缺口项执行**。已搜索到的素材不重复生成。

**AI 生成工具**（通过 ai-gateway MCP，按可用性自动选择）：

| 媒体类型 | 可用工具（按优先级） | 所需 Key |
|---------|---------------------|---------|
| 图片 | `generate_image`（Google Imagen 4）→ `openrouter_generate_image`（GPT-5 Image）→ `flux_generate_image`（FLUX 2 Pro） | GOOGLE_API_KEY / OPENROUTER_API_KEY / FAL_KEY |
| 视频 | `generate_video`（Google Veo 3.1）→ `kling_generate_video`（Kling 2.1） | GOOGLE_API_KEY / FAL_KEY |
| 音频 | `text_to_speech`（Google Cloud TTS） | GOOGLE_API_KEY |

**Prompt 构建**：从 `search_keywords` + `style_notes` + `dimensions` 组合：

```
Image prompt: "A {style_notes} of {search_keywords}, {dimensions} aspect ratio, professional quality, no text overlay"
```

**其他类型**：

| 媒体类型 | 生成方式 | 说明 |
|---------|---------|------|
| 产品操作演示 | Playwright 录屏 | 免费，最真实——录制应用自身操作流程 |
| 文档（PDF） | 模板填充生成 | 用 demo-plan 中的业务数据填充 PDF 模板 |

**降级策略**：
- 生图：Google Imagen 4 → OpenRouter GPT-5 Image（无额外 Key）→ FLUX 2 Pro → 跳过
- 生视频：Google Veo 3.1 → Kling → Playwright 录屏 → 跳过

**下载规范**：与 M2 相同的 `assets/{category}/` 目录和命名规则，紧接 M2 编号继续。

```
M3 AI 生成: 28 项补缺完成
  生图(Imagen 4/GPT-5/FLUX): 20 张图片
  PDF 模板: 5 份文档
  生视频(Veo 3.1/Kling):    3 段视频
```

---

### M3.5: 素材加工（按需）

**触发条件**：M4 质量验收发现不达标项时回到此步加工。首轮也可在 M2/M3 下载后预检触发。

**加工操作与命令**：

| 问题 | 操作 | 命令 |
|-----|------|------|
| 分辨率不足 | AI 超分辨率（2x/4x） | `realesrgan-ncnn-vulkan -i input.jpg -o output.png -s 2` |
| 宽高比不匹配 | 智能裁剪（保留主体） | `ffmpeg -i input.jpg -vf "crop=w:h:x:y" output.jpg` |
| 文件过大 | WebP 压缩 | `cwebp -q 85 input.png -o output.webp` |
| 格式不对 | 格式转换 | `ffmpeg -i input.png output.webp` 或 `cwebp` |
| 视频过长 | 裁剪关键片段 | `ffmpeg -i input.mp4 -ss 00:00:05 -t 00:00:30 -c copy output.mp4` |
| 风格不一致 | 色调/亮度统一 | `ffmpeg -i input.jpg -vf "eq=brightness=0.06:saturation=1.2" output.jpg` |

> 详细命令参考：`${CLAUDE_PLUGIN_ROOT}/docs/media-processing.md`

**加工后**：覆盖原文件（保留备份 `.orig`），更新 `assets-manifest.json` 中的尺寸/大小信息，`processing_applied` 数组追加操作记录。

---

### M4: 质量验收

逐项检查每个素材，全部通过才标记 `verified: true`。

**检查清单**：

- [ ] **分辨率** >= UI 渲染尺寸 x2（Retina 适配）— 如目标 400x400 则素材需 >= 800x800
- [ ] **宽高比**与目标容器匹配 — 对比 `demo-plan.json` 中的 `aspect_ratio` 字段
- [ ] **文件大小**合规 — 图片 <= 2MB，头像 <= 200KB，视频按时长合理
- [ ] **同组风格一致** — 同 `purpose` 的素材色调、构图、风格统一
- [ ] **无相邻重复** — 同一列表中不出现视觉相同的素材
- [ ] **无水印/版权标记** — 搜索下载的图片不含水印残留
- [ ] **AI 图片无瑕疵** — 无多余手指、乱码文字、异常纹理等常见 AI 生成问题
- [ ] **视频可播放** — 编码正确、时长合理（5s-60s）、无黑屏/花屏

**不合格处理**：

- 标记 `verified: false`，记录失败原因
- 回到 M2（替换素材）/ M3（重新生成）/ M3.5（加工修正），取决于问题性质
- 循环直到该项通过或标记为 `NEEDS_MANUAL`

**输出**：`assets-manifest.json`

---

### M5: 上传到应用服务器

将所有 `verified: true` 的素材通过应用自身的上传 API 传到服务器。

**操作流程**：

1. 从 `demo-plan.json` 每个 `media_fields` 条目读取 `upload_endpoint`
2. 对每个已验收素材：
   - `POST` multipart/form-data 上传到 `upload_endpoint`
   - 解析响应获取 `server_url`（服务端存储路径）和 `server_id`（服务端文件 ID）
3. 写入 `upload-mapping.json`

**失败处理**：

- 上传失败 → 重试 2 次（间隔 2s）
- 仍失败 → 标记 `status: "UPLOAD_FAILED"`，记录错误信息
- `upload_endpoint` 不存在 → 标记 `API_GAP`，追加到 `api-gaps.json`

**输出**：`upload-mapping.json`

---

### M6: 完整性确认

最终硬校验，确保管线产出符合铁律。

**校验项**：

1. **全量覆盖**：所有 `verified: true` 的素材在 `upload-mapping.json` 中都有对应条目
2. **零失败**：无 `UPLOAD_FAILED` 状态残留（有则报错，需人工介入或重试）
3. **零外链（硬校验）**：扫描所有 `server_url` 值，逐一验证：
   - 必须以 `/` 开头（相对路径）或匹配应用自身域名
   - 包含任何外部域名（`http://`, `https://` 且非应用域名）→ **立即报错，不允许继续**
   - `external_url_count` 必须为 `0`

```
M6 完整性确认:
  已上传:        132/136
  UPLOAD_FAILED:   0
  API_GAP:         4（已记录到 api-gaps.json）
  external_url_count: 0 ✓
  状态: PASSED
```

---

## 输出文件

### assets-manifest.json

```json
{
  "assets": [
    {
      "asset_id": "IMG-001",
      "target_entity": "Product",
      "target_field": "cover_image",
      "media_type": "image",
      "source": "brave_search",
      "source_url": "https://example.com/original.jpg",
      "local_path": "assets/covers/IMG-001.webp",
      "original_format": "jpeg",
      "dimensions": "1600x1600",
      "file_size_kb": 234,
      "aspect_ratio": "1:1",
      "processing_applied": ["upscale_2x", "webp_convert"],
      "quality_check": {
        "resolution_ok": true,
        "aspect_ratio_ok": true,
        "size_ok": true,
        "style_consistent": true,
        "no_watermark": true
      },
      "verified": true
    }
  ],
  "summary": {
    "total_needed": 156,
    "search_fulfilled": 130,
    "ai_generated": 18,
    "processed": 42,
    "rejected": 4,
    "verified": 152
  }
}
```

### upload-mapping.json

```json
{
  "mappings": [
    {
      "asset_id": "IMG-001",
      "local_path": "assets/covers/IMG-001.webp",
      "upload_endpoint": "POST /api/upload/image",
      "server_url": "/uploads/2024/03/abc123.webp",
      "server_id": "file_abc123",
      "uploaded_at": "2026-03-05T10:30:00Z",
      "status": "success"
    }
  ],
  "validation": {
    "external_url_count": 0,
    "all_local": true
  }
}
```

### 目录结构

```
.allforai/demo-forge/
├── assets/
│   ├── avatars/      # 头像（IMG-001 ~ IMG-030）
│   ├── covers/       # 封面（IMG-031 ~ IMG-080）
│   ├── details/      # 详情图（IMG-081 ~ IMG-110）
│   ├── banners/      # 横幅（IMG-111 ~ IMG-120）
│   └── videos/       # 视频（VID-001 ~ VID-008）
├── assets-manifest.json
└── upload-mapping.json
```

---

## 重入模式

当 `verify-issues.json` 中存在 `route_to="media"` 的问题时触发。

**处理流程**：

1. 读取 `verify-issues.json`，筛选 `route_to="media"` 的条目
2. 按问题类型分类并路由到对应步骤：

| 问题类型 | 路由目标 | 处理方式 |
|---------|---------|---------|
| Broken image / 图片 404 | M2 | 重新搜索替换素材 |
| 尺寸/分辨率不符 | M3.5 | 加工处理（超分/裁剪） |
| 外部 URL 残留 | M2 + M5 | 下载到本地 + 重新上传 |
| 风格不一致 | M3.5 | 色调统一加工 |
| 上传失败 | M5 | 重试上传 |
| 占位图残留 | M2/M3 | 搜索或生成替换 |

3. **只处理问题项**，已通过的素材不动
4. 处理完成后重新执行 M4（仅验收问题项）→ M6

---

## 增强协议

**WebSearch 关键词**（Brave 不可用时降级搜索）：

- `"free stock photos {category} high resolution {year}"`
- `"免费商用图片 {category} 高清"`
- `"stock video footage {category} short clip"`

**4E+4V 重点**：

- **E3 Guardrails**: 素材版权合规——优先 CC0/Unsplash License 来源；AI 生成素材标注来源
- **behavior 视角**: 同一列表相邻记录的素材视觉差异度 >= 30%（避免"复制粘贴"感）

**工具依赖**：

| 工具 | 用途 | 必需/可选 |
|-----|------|----------|
| `brave_web_search` / `brave_image_search` | 图片/视频搜索 | 推荐（`BRAVE_API_KEY`） |
| WebSearch | 降级搜索 | 内置 |
| `generate_image` / `openrouter_generate_image` / `flux_generate_image` | AI 生图 | 可选（任一 Key 即可） |
| `generate_video` / `kling_generate_video` | AI 生视频 | 可选（任一 Key 即可） |
| `text_to_speech` | TTS 语音生成 | 可选（`GOOGLE_API_KEY`） |
| Playwright | 录屏、截图验证 | 可选 |
| ffmpeg | 视频/图片加工 | 本地安装 |
| cwebp | WebP 转换压缩 | 本地安装 |
| realesrgan-ncnn-vulkan | AI 超分辨率 | 本地安装，可选 |
