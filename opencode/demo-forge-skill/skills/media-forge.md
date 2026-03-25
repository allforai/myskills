---
name: media-forge
description: >
  Use when the user asks to "collect media", "find images for demo",
  "upload demo images", "media-forge", "demo images", "demo videos",
  or mentions media acquisition, image collection, video sourcing for demos.
  Requires demo-plan.json with Step 1-M media field annotations.
version: "1.0.0"
---

# Media Forge — Rich Media Forging

> Search-first, AI-supplement, local-storage, app-upload — zero external links in the demo.

## Iron Rules (4, mandatory)

1. **All assets must download to local `assets/`, zero external links** — no external CDN, image host, or third-party URL references
2. **Population must go through app upload API, database stores only server addresses** — `server_url` must be the app's own domain path
3. **Brave search first, 网络搜索 fallback, AI generation last, no placeholders** — any placeholder / lorem ipsum image is a failure
4. **`upload-mapping.json` `external_url_count` must be 0 (hard check)** — scan all `server_url` on completion, external domain = error

---

## Positioning

```
demo-forge internal stages + independent media pipeline:
  demo-design (plan)  →  media-forge (this skill) + demo-execute (populate)  →  demo-verify (verify)
  Plan what data to generate   Acquire/generate/process/upload assets   Populate business data    Verify each item
  Pure design, no execution    Independently runnable                   Consume design+assets     Route issues back
```

**Independently runnable**: can be called by demo-forge orchestrator, or used standalone (as long as `demo-plan.json` exists).

**Prerequisite**: demo-design must have run, producing `.allforai/demo-forge/demo-plan.json` (with Step 1-M media field annotations).

---

## Workflow

### M1: Requirements Inventory

Read `demo-plan.json` Step 1-M `media_fields` array, build complete requirements list.

**Operations**:

1. Parse each `media_fields` entry: `entity`, `field`, `media_type`, `purpose`, `dimensions`, `count`, `search_keywords`, `style_notes`, `upload_endpoint`
2. Group by `media_type` (image / video / document / audio)
3. Sub-group by `purpose` (avatars, covers, detail images, banners, etc.)
4. Summarize per-group demand

**Output**: progress summary table

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

For each M1 group, search and download assets by priority.

**Search priority**:

1. **Brave Search MCP** (preferred) — `mcp__brave-search__brave_web_search`
2. **网络搜索** (fallback when Brave unavailable or quota exhausted)

**Keyword construction**:

- Base: `search_keywords` array
- Modifiers: from `style_notes` (e.g., "white background", "e-commerce style")
- Combination: `"{keyword} {style} high resolution free stock"` / `"{keyword} {style} HD free"`
- **Same `purpose` group uses same keywords** for style consistency

**Download rules**:

- Target directory: `assets/{category}/` (category mapped from purpose: avatars→avatars, covers→covers, details→details, banners→banners, videos→videos)
- Naming: `{TYPE}-{NNN}.{ext}` (IMG-001.webp, VID-001.mp4, DOC-001.pdf, AUD-001.mp3)
- Download immediately to local, do not retain external links

**Progress tracking**:

```
M2 Search acquisition: 108/136 fulfilled, gap 28
  image:  100/120 (gap 20 — detail style mismatch skipped)
  video:    5/8   (gap 3 — short video resources insufficient)
  document: 0/5   (search not applicable, all to M3)
  audio:    3/3   (all fulfilled)
```

---

### M3: AI Generation (gap-fill)

**Only for M2 unfulfilled gaps**. Already-found assets are not regenerated.

**AI generation tools** (via ai-gateway MCP, auto-select by availability):

| Media type | Available tools (by priority) | Required Key |
|-----------|-------------------------------|-------------|
| Image | `mcp__ai-gateway__generate_image` (Google Imagen 4) → `mcp__ai-gateway__openrouter_generate_image` (GPT-5 Image) → `mcp__ai-gateway__flux_generate_image` (FLUX 2 Pro) | GOOGLE_API_KEY / OPENROUTER_API_KEY / FAL_KEY |
| Video | `mcp__ai-gateway__generate_video` (Google Veo 3.1) → `mcp__ai-gateway__kling_generate_video` (Kling 2.1) | GOOGLE_API_KEY / FAL_KEY |
| Audio | `mcp__ai-gateway__text_to_speech` (Google Cloud TTS) | GOOGLE_API_KEY |

**Prompt construction**: from `search_keywords` + `style_notes` + `dimensions`:

```
Image prompt: "A {style_notes} of {search_keywords}, {dimensions} aspect ratio, professional quality, no text overlay"
```

**Other types**:

| Media type | Generation method | Notes |
|-----------|-------------------|-------|
| Product demo recordings | Playwright screen recording | Free, most authentic — record app's own operations |
| Documents (PDF) | Template fill generation | Fill PDF templates with demo-plan business data |

**Degradation chain**:
- Image: Google Imagen 4 → OpenRouter GPT-5 Image → FLUX 2 Pro → skip
- Video: Google Veo 3.1 → Kling → Playwright recording → skip

**Download rules**: same `assets/{category}/` directory and naming, continue numbering after M2.

---

### M3.5: Asset Processing (on demand)

**Trigger**: M4 quality check finds non-conforming items, or pre-check after M2/M3 download.

**Processing operations and commands**:

| Problem | Operation | Command |
|---------|-----------|---------|
| Resolution insufficient | AI super-resolution (2x/4x) | `realesrgan-ncnn-vulkan -i input.jpg -o output.png -s 2` |
| Aspect ratio mismatch | Smart crop (preserve subject) | `ffmpeg -i input.jpg -vf "crop=w:h:x:y" output.jpg` |
| File too large | WebP compression | `cwebp -q 85 input.png -o output.webp` |
| Wrong format | Format conversion | `ffmpeg -i input.png output.webp` or `cwebp` |
| Video too long | Trim key segment | `ffmpeg -i input.mp4 -ss 00:00:05 -t 00:00:30 -c copy output.mp4` |
| Style inconsistent | Tone/brightness unify | `ffmpeg -i input.jpg -vf "eq=brightness=0.06:saturation=1.2" output.jpg` |

> Detailed command reference: `./docs/media-processing.md`

**After processing**: overwrite original (keep `.orig` backup), update `assets-manifest.json` dimensions/size, append to `processing_applied` array.

---

### M4: Quality Check

Check each asset item-by-item. All must pass to mark `verified: true`.

**Checklist**:

- [ ] **Resolution** >= UI render size x2 (Retina) — target 400x400 needs >= 800x800
- [ ] **Aspect ratio** matches target container — compare `demo-plan.json` `aspect_ratio` field
- [ ] **File size** compliant — images <= 2MB, avatars <= 200KB, videos by duration
- [ ] **Same-group style consistent** — same `purpose` assets share tone, composition, style
- [ ] **No adjacent duplicates** — same list has no visually identical assets
- [ ] **No watermarks** — search-downloaded images have no watermark residue
- [ ] **AI image no artifacts** — no extra fingers, garbled text, abnormal textures
- [ ] **Video playable** — correct encoding, reasonable duration (5s-60s), no black screen

**Non-conforming handling**:

- Mark `verified: false`, record failure reason
- Return to M2 (replace) / M3 (regenerate) / M3.5 (process), depending on issue
- Loop until pass or mark `NEEDS_MANUAL`

**Output**: `assets-manifest.json`

---

### M5: Upload to Application Server

Upload all `verified: true` assets through the app's own upload API.

**Flow**:

1. Read `upload_endpoint` from each `media_fields` entry in `demo-plan.json`
2. For each verified asset:
   - `POST` multipart/form-data to `upload_endpoint`
   - Parse response for `server_url` (server storage path) and `server_id` (server file ID)
3. Write to `upload-mapping.json`

**Failure handling**:

- Upload failure → retry 2 times (2s interval)
- Still fails → mark `status: "UPLOAD_FAILED"`, record error
- `upload_endpoint` doesn't exist → mark `API_GAP`, append to `api-gaps.json`

**Output**: `upload-mapping.json`

---

### M6: Completeness Confirmation

Final hard check ensuring pipeline output complies with iron rules.

**Check items**:

1. **Full coverage**: all `verified: true` assets have entries in `upload-mapping.json`
2. **Zero failures**: no `UPLOAD_FAILED` status remaining
3. **Zero external links (hard check)**: scan all `server_url` values:
   - Must start with `/` (relative path) or match app's own domain
   - Any external domain (`http://`, `https://` not matching app domain) → **immediate error, cannot continue**
   - `external_url_count` must be `0`

```
M6 Completeness confirmation:
  Uploaded:          132/136
  UPLOAD_FAILED:       0
  API_GAP:             4 (recorded in api-gaps.json)
  external_url_count:  0 ✓
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

---

## Reentry Mode

When `verify-issues.json` contains `route_to="media"` issues.

**Flow**:

1. Read `verify-issues.json`, filter `route_to="media"` entries
2. Classify by issue type and route to corresponding step:

| Issue type | Route | Handling |
|-----------|-------|----------|
| Broken image / 404 | M2 | Re-search replacement asset |
| Dimension/resolution mismatch | M3.5 | Process (upscale/crop) |
| External URL residue | M2 + M5 | Download to local + re-upload |
| Style inconsistent | M3.5 | Tone unification processing |
| Upload failed | M5 | Retry upload |
| Placeholder residue | M2/M3 | Search or generate replacement |

3. **Only process problem items**, leave passed assets untouched
4. After processing, re-execute M4 (problem items only) → M6

---

## Enhancement Protocol

**网络搜索 keywords** (when Brave unavailable):

- `"free stock photos {category} high resolution {year}"`
- `"stock video footage {category} short clip"`

**Tool dependencies**:

| Tool | Purpose | Required/Optional |
|------|---------|-------------------|
| `brave_web_search` / `brave_image_search` | Image/video search | Recommended (`BRAVE_API_KEY`) |
| 网络搜索 | Fallback search | Built-in |
| `mcp__ai-gateway__generate_image` / `mcp__ai-gateway__openrouter_generate_image` / `mcp__ai-gateway__flux_generate_image` | AI image generation | Optional (any Key) |
| `mcp__ai-gateway__generate_video` / `mcp__ai-gateway__kling_generate_video` | AI video generation | Optional (any Key) |
| `mcp__ai-gateway__text_to_speech` | TTS voice generation | Optional (`GOOGLE_API_KEY`) |
| Playwright | Screen recording, screenshot verification | Optional |
| ffmpeg | Video/image processing | Local install |
| cwebp | WebP conversion/compression | Local install |
| realesrgan-ncnn-vulkan | AI super-resolution | Local install, optional |
