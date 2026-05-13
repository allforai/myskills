---
description: Batch generate images on ChatGPT and download/organize by category
argument-hint: <path-to-prompts.json>
---

# ChatGPT Image Generator

Generate images in batch from ChatGPT using a JSON prompt file, organized into per-category local folders.
Uses **Chrome MCP** (browsermcp) — connects to your existing logged-in Chrome session, no login required.
Downloads images entirely through the browser (hover → download button → move from ~/Downloads).

## Step 1: Read and Validate Input

The argument passed to this command is the path to a JSON file (available as `$ARGUMENTS`).

Read the file and validate:
- File exists and contains valid JSON
- Top-level `outputDir` field is a non-empty string
- Top-level `categories` field is an object with at least one key, each value being a non-empty array of strings

If any validation check fails, print a descriptive error and stop immediately. Do not proceed.

Example of a valid input file:
```json
{
  "outputDir": "./chatgpt-images",
  "categories": {
    "landscapes": ["a sunset over mountains", "misty forest at dawn"],
    "portraits": ["a samurai warrior", "a Victorian lady"]
  }
}
```

## Step 2: Initialize Output Directories

Before processing any prompts, create all required output directories:

For each category key in `categories`, run:
```bash
mkdir -p "<outputDir>/<category>"
```

Print: `Initialized output directories under <outputDir>/`

## Step 3: Select the Best Image Generation Model (once per session)

Do this only once at the start, before processing any prompts.

1. Call `browser_navigate` with `url: "https://chatgpt.com"`.
2. Call `browser_snapshot`. Look for the model selector — it is typically a button or clickable element near the top of the page or the input area showing the current model name (e.g., "ChatGPT", "GPT-4o", "o3", etc.).
3. Click the model selector to open the dropdown.
4. Call `browser_snapshot` on the dropdown. Look for the best available image generation option. Priority order:
   - Any option explicitly mentioning "Image generation", "DALL·E", or "Image"
   - Otherwise use the most capable general model available (typically the highest-tier GPT or o-series model listed)
5. Click that option to select it.
6. Call `browser_snapshot` to confirm selection.

If no model selector is found, proceed with the current default model.

## Step 4: Generate Images

For each category, for each prompt in that category, follow these sub-steps:

### 4a. Open a fresh ChatGPT conversation

1. Call `browser_navigate` with `url: "https://chatgpt.com"`.
2. Call `browser_snapshot`. If a "New chat" button or link is visible, click it. If the page already shows a fresh empty chat (no previous messages), skip the click.

### 4b. Submit the prompt

**Important**: Do NOT use `submit: true` in `browser_type` — it causes a 30-second timeout waiting for ChatGPT to finish. Instead, type first, then press Enter separately.

1. Call `browser_snapshot`. Find the element with role `textbox` (the chat input). Note its `ref`.
2. Call `browser_type` with:
   - `ref`: the textbox ref from the snapshot
   - `element: "chat input"`
   - `text`: the current prompt text
   - `submit: false`
3. Call `browser_press_key` with `key: "Enter"` to submit.
   - If `browser_press_key` times out, **treat it as submitted** and proceed to Step 4c. Do not retry.

### 4c. Wait for generation to complete

Poll every 5 seconds by calling `browser_snapshot` and examining the result:

- **Complete** when: the snapshot contains an `img` element whose accessible name starts with `"Generated image:"` AND no button or element with accessible name containing `"Stop generating"` is visible.
- **Rate limited** when: visible text in the snapshot contains any of: `"plan limit"`, `"image generation limit"`, `"too many requests"`, `"limit reached"`.
  - Wait 60 seconds, poll once more. If still rate-limited: record `RATE_LIMITED`, skip all remaining prompts in this category, continue with the next category.
- **Timeout** after 120 seconds with no completion: record `TIMEOUT`, print `⚠ TIMEOUT: [category] "<prompt>"`, move to next prompt.

### 4d. Download the image via browser

Once generation is complete:

1. Call `browser_snapshot`. Find the generated image element (accessible name starts with `"Generated image:"`). Note its `ref`.

2. Call `browser_hover` with `ref` and `element: "generated image"` to reveal the action buttons overlay.

3. Call `browser_snapshot` again. Look for a download button — it may be labeled `"Download"`, `"下载"`, have an accessible name containing "download", or show as a button with a download icon near the image. Use its `ref` and call `browser_click` with `element: "download button"`.
   - If no download button appears after hover, click on the image itself to open it full-screen, then look for a download button in the full-screen overlay.

4. Wait for the download to complete:
   ```bash
   sleep 4
   ```

5. Find the most recently downloaded image file:
   ```bash
   DOWNLOADED=$(ls -t ~/Downloads/*.png ~/Downloads/*.jpg ~/Downloads/*.webp ~/Downloads/*.jpeg 2>/dev/null | head -1)
   ```

6. If `DOWNLOADED` is empty, record `DOWNLOAD_FAILED` and move to next prompt.

7. Compute the filename slug:
   - Take the prompt text, lowercase it, keep only the first 40 characters
   - Replace spaces with `_`
   - Strip all characters that are not alphanumeric or `_`

8. Determine the sequence number:
   ```bash
   COUNT=$(ls "<outputDir>/<category>/<slug>"_*.* 2>/dev/null | wc -l | tr -d ' ')
   N=$(printf "%02d" $((COUNT + 1)))
   EXT="${DOWNLOADED##*.}"
   ```

9. Move the file to the destination:
   ```bash
   mv "$DOWNLOADED" "<outputDir>/<category>/<slug>_${N}.${EXT}"
   ```

   **On success:** Print: `✓ <category>/<slug>_${N}.${EXT}`
   **On failure:** Record `DOWNLOAD_FAILED`. Print: `⚠ DOWNLOAD_FAILED: [category] "<prompt>"`.

## Step 5: Print Final Summary

After all categories have been processed, print a summary in this format:

```
=== chatgpt-image-gen Summary ===
Total prompts:  X
Downloaded:     Y images
Skipped:        Z prompts

Skipped details:
- [category] "prompt text" → ERROR_CODE
```

Error codes:
- `TIMEOUT` — ChatGPT did not finish generating within 120 seconds
- `RATE_LIMITED` — ChatGPT returned a rate limit response; remaining prompts in that category were also skipped
- `DOWNLOAD_FAILED` — No downloaded image found in ~/Downloads after clicking download

If all prompts succeeded, print: `All prompts completed successfully.` instead of the skipped section.
