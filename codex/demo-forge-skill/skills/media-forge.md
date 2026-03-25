---
name: media-forge
description: >
  Use when the user asks to "collect media", "find images for demo",
  "upload demo images", "media-forge", "demo images", "demo videos",
  or mentions media acquisition, image collection, video sourcing for demos.
  Requires demo-plan.json with Step 1-M media field annotations.
version: "1.0.0"
---

# Media Forge — Rich Media Pipeline

> Search first, AI fill gaps, local storage, app upload — zero external links.

## Iron Rules (4, mandatory)

1. **All assets must be downloaded to local `assets/`, zero external links** — no external image hosts, CDNs, or third-party URLs
2. **Population must use app upload API, database stores only server addresses** — `server_url` must be app's own domain path
3. **Brave search first, WebSearch fallback, AI generation backstop, no placeholders** — any placeholder / lorem ipsum image is a failure
4. **`upload-mapping.json` `external_url_count` must be 0 (hard validation)** — scan all `server_url` on completion, any external domain triggers error

---

## Position

```
demo-forge internal stages + independent media pipeline:
  demo-design (planning)  ->  media-forge (this skill) + demo-execute (population)  ->  demo-verify
  Plan what data to generate    Acquire/generate/process/upload media    Populate business data     Verify
  Pure design, no execution     Independently runnable                  Consumes design + media     Route issues back
```

**Independently runnable**: Can be called by demo-forge orchestration or used standalone (as long as `demo-plan.json` exists).

**Prerequisite**: demo-design must have run first, generating `.allforai/demo-forge/demo-plan.json` (with Step 1-M media field annotations).

---

## Workflow

### M1: Requirements Inventory

Read `demo-plan.json` Step 1-M `media_fields` array, build complete requirements list.

1. Parse each `media_fields` record: `entity`, `field`, `media_type`, `purpose`, `dimensions`, `count`, `search_keywords`, `style_notes`, `upload_endpoint`
2. Group by `media_type` (image / video / document / audio)
3. Sub-group by `purpose` (avatars, covers, details, banners, etc.)
4. Summarize per-group demand

**Output**: Progress summary table

```
Media requirements inventory:
  image:    120 items (avatars 30 | covers 50 | details 30 | banners 10)
  video:      8 items (product videos 5 | tutorials 3)
  document:   5 items (contract templates 5)
  audio:      3 items (voice messages 3)
  ────────────────
  Total:    136 items
```

---

### M2: Search Acquisition (primary)

For each M1 requirement group, search and download assets by priority.

**Search priority**:

1. **Brave Search MCP** (preferred)
2. **WebSearch** (when Brave unavailable or quota exhausted)

**Keyword construction**:

- Base keywords: from `search_keywords` array
- Modifiers: from `style_notes` (e.g., "white background", "e-commerce style")
- Strategy: `"{keyword} {style} high resolution free stock"` / `"{keyword} {style} high-res free stock"`
- **Same `purpose` group uses same keyword set** for style consistency

**Download conventions**:

- Target directory: `assets/{category}/` (category mapped from purpose: avatars, covers, details, banners, videos)
- File naming: `{TYPE}-{NNN}.{ext}`
  - Images: `IMG-001.webp`, `IMG-002.webp`
  - Videos: `VID-001.mp4`, `VID-002.mp4`
  - Documents: `DOC-001.pdf`
  - Audio: `AUD-001.mp3`
- Every search result downloaded to local immediately, no external links retained

---

### M3: AI Generation (gap filling)

**Only for M2 unfulfilled gaps**. Already-acquired assets are not regenerated.

**AI generation tools** (via ai-gateway MCP, auto-select by availability):

| Media Type | Available Tools (by priority) | Required Key |
|-----------|------------------------------|-------------|
| Image | Imagen 4 (Google) -> GPT-5 Image (OpenRouter) -> FLUX 2 Pro (fal.ai) | GOOGLE_API_KEY / OPENROUTER_API_KEY / FAL_KEY |
| Video | Veo 3.1 (Google) -> Kling 2.1 (fal.ai) | GOOGLE_API_KEY / FAL_KEY |
| Audio | Google Cloud TTS | GOOGLE_API_KEY |

**Prompt construction**: Combine `search_keywords` + `style_notes` + `dimensions`:

```
Image prompt: "A {style_notes} of {search_keywords}, {dimensions} aspect ratio, professional quality, no text overlay"
```

**Other types**:

| Media Type | Generation Method | Notes |
|-----------|------------------|-------|
| Product operation demos | Playwright screen recording | Free, most realistic — record app's own operation flow |
| Documents (PDF) | Template fill generation | Fill PDF templates with demo-plan business data |

**Degradation chain**:
- Image: Imagen 4 -> GPT-5 Image (OpenRouter) -> FLUX 2 Pro -> skip
- Video: Veo 3.1 -> Kling -> Playwright screen recording -> skip

**Download conventions**: Same `assets/{category}/` directory and naming rules as M2, continuing M2 numbering.

---

### M3.5: Asset Processing (on demand)

**Trigger**: M4 quality check finds non-compliant items, or pre-check after M2/M3 download.

**Processing operations and commands**:

| Issue | Operation | Command |
|-------|-----------|---------|
| Low resolution | AI upscale (2x/4x) | `realesrgan-ncnn-vulkan -i input.jpg -o output.png -s 2` |
| Wrong aspect ratio | Smart crop (preserve subject) | `ffmpeg -i input.jpg -vf "crop=w:h:x:y" output.jpg` |
| File too large | WebP compression | `cwebp -q 85 input.png -o output.webp` |
| Wrong format | Format conversion | `ffmpeg -i input.png output.webp` or `cwebp` |
| Video too long | Trim key segment | `ffmpeg -i input.mp4 -ss 00:00:05 -t 00:00:30 -c copy output.mp4` |
| Inconsistent style | Color/brightness unification | `ffmpeg -i input.jpg -vf "eq=brightness=0.06:saturation=1.2" output.jpg` |

> Detailed command reference: `docs/media-processing.md`

**After processing**: overwrite original file (keep `.orig` backup), update `assets-manifest.json` dimensions/size info, append to `processing_applied` array.

---

### M4: Quality Check

Item-by-item check. All must pass before marking `verified: true`.

**Checklist**:

- [ ] **Resolution** >= UI render size x2 (Retina) — target 400x400 means asset needs >= 800x800
- [ ] **Aspect ratio** matches target container — compare against `demo-plan.json` `aspect_ratio`
- [ ] **File size** compliant — images <= 2MB, avatars <= 200KB, video reasonable by duration
- [ ] **Same-group style consistent** — same `purpose` assets have unified color tone, composition, style
- [ ] **No adjacent duplicates** — same list does not show visually identical assets
- [ ] **No watermarks/copyright marks** — search-downloaded images free of watermark remnants
- [ ] **AI images clean** — no extra fingers, garbled text, abnormal textures
- [ ] **Video playable** — correct encoding, reasonable duration (5s-60s), no black/corrupt screens

**Non-compliant handling**:

- Mark `verified: false`, record failure reason
- Route back to M2 (replace) / M3 (regenerate) / M3.5 (process), depending on issue type
- Loop until item passes or marked `NEEDS_MANUAL`

**Output**: `assets-manifest.json`

---

### M5: Upload to Application Server

Upload all `verified: true` assets through the application's own upload API.

**Flow**:

1. Read `upload_endpoint` from each `media_fields` entry in `demo-plan.json`
2. For each verified asset:
   - `POST` multipart/form-data to `upload_endpoint`
   - Parse response for `server_url` (server storage path) and `server_id` (server file ID)
3. Write to `upload-mapping.json`

**Failure handling**:
- Upload failure -> retry 2x (2s interval)
- Still failing -> mark `status: "UPLOAD_FAILED"`, record error
- `upload_endpoint` does not exist -> mark `API_GAP`, append to `api-gaps.json`

**Output**: `upload-mapping.json`

---

### M6: Integrity Confirmation

Final hard validation ensuring pipeline output meets iron rules.

**Validation items**:

1. **Full coverage**: all `verified: true` assets have corresponding entries in `upload-mapping.json`
2. **Zero failures**: no `UPLOAD_FAILED` status remaining
3. **Zero external links (hard validation)**: scan all `server_url` values:
   - Must start with `/` (relative path) or match app's own domain
   - Any external domain (`http://`, `https://` not matching app domain) -> **immediate error, cannot proceed**
   - `external_url_count` must be `0`

```
M6 Integrity confirmation:
  Uploaded:          132/136
  UPLOAD_FAILED:       0
  API_GAP:             4 (recorded in api-gaps.json)
  external_url_count:  0
  Status: PASSED
```

---

## Output Files

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

### Directory Structure

```
.allforai/demo-forge/
├── assets/
│   ├── avatars/      # Avatars (IMG-001 ~ IMG-030)
│   ├── covers/       # Covers (IMG-031 ~ IMG-080)
│   ├── details/      # Detail images (IMG-081 ~ IMG-110)
│   ├── banners/      # Banners (IMG-111 ~ IMG-120)
│   └── videos/       # Videos (VID-001 ~ VID-008)
├── assets-manifest.json
└── upload-mapping.json
```

---

## Re-entry Mode

Triggered when `verify-issues.json` contains `route_to="media"` issues.

**Flow**:

1. Read `verify-issues.json`, filter `route_to="media"` entries
2. Classify by issue type and route to corresponding step:

| Issue Type | Route Target | Handling |
|-----------|-------------|---------|
| Broken image / 404 | M2 | Re-search replacement asset |
| Size/resolution mismatch | M3.5 | Process (upscale/crop) |
| External URL remaining | M2 + M5 | Download to local + re-upload |
| Style inconsistency | M3.5 | Color unification processing |
| Upload failure | M5 | Retry upload |
| Placeholder remaining | M2/M3 | Search or generate replacement |

3. **Only process problem items**, verified assets untouched
4. After processing, re-run M4 (verify problem items only) -> M6

---

## Enhancement Protocol

**WebSearch keywords** (when Brave unavailable):

- `"free stock photos {category} high resolution {year}"`
- `"stock video footage {category} short clip"`

**Tool dependencies**:

| Tool | Purpose | Required/Optional |
|------|---------|-------------------|
| Brave Search | Image/video search | Recommended (BRAVE_API_KEY) |
| WebSearch | Fallback search | Built-in |
| OpenRouter MCP tools | AI image generation | Optional |
| Google AI generation tools | Imagen 4, Veo 3.1, TTS | Optional (GOOGLE_API_KEY) |
| fal.ai generation tools | FLUX 2 Pro, Kling | Optional (FAL_KEY) |
| Playwright | Screen recording, screenshot verification | Optional |
| ffmpeg | Video/image processing | Local install |
| cwebp | WebP conversion/compression | Local install |
| realesrgan-ncnn-vulkan | AI super-resolution | Local install, optional |
