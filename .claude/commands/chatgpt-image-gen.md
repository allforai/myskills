---
description: Batch generate images on ChatGPT and download/organize by category
argument-hint: <path-to-prompts.json>
---

# ChatGPT Image Generator

Generate images in batch from ChatGPT using a JSON prompt file, organized into per-category local folders.

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

## Step 3: Generate Images

For each category, for each prompt in that category, follow these sub-steps:

### 3a. Bootstrap the browser tab

1. Call `browser_tabs` with `action: "list"` to see open tabs.
2. If no tabs exist, call `browser_tabs` with `action: "new"` and `url: "https://chatgpt.com"`, then skip to Step 3b item 2.
3. If tabs exist, call `browser_tabs` with `action: "select"` and `index: 0` to select the first tab.

### 3b. Open a fresh ChatGPT conversation

1. Call `browser_navigate` with `url: "https://chatgpt.com"`.
2. Call `browser_snapshot`. Check whether the snapshot contains "Log in" or "Sign up" text anywhere.
   - If login UI is visible: print `⏳ ChatGPT login required. Please log in in the Playwright browser window, then press Enter here to continue.` and pause (call `AskUserQuestion` with the question "Press Enter once you have logged in to ChatGPT in the browser window."). After the user responds, call `browser_snapshot` again to confirm login succeeded (no "Log in" / "Sign up" text). If still not logged in, stop with an error.
3. Call `browser_snapshot`. Find the element whose accessible name is "New chat". Use its `ref` value as `target` and call `browser_click` with `element: "New chat button"`.

### 3c. Verify model supports image generation

1. Call `browser_snapshot`. Read the model selector label at the top of the page.
   - If the label is not "GPT-4o" or "GPT-4": find the model selector element in the snapshot, use its `ref` as `target`, and call `browser_click` with `element: "model selector"`.
   - Then call `browser_snapshot`, find the "GPT-4o" option in the dropdown, use its `ref` as `target`, and call `browser_click` with `element: "GPT-4o option"`.
   - GPT-4o supports image generation natively. Do not look for a separate "DALL-E" option.

### 3d. Submit the prompt

1. Call `browser_snapshot`. Find the element with role `textbox` (the chat input). Use its `ref` as `target`.
2. Call `browser_type` with:
   - `target`: the textbox ref from the snapshot
   - `element: "chat input"`
   - `text`: the current prompt text
   - `submit: true` (this types the text and presses Enter)

### 3e. Wait for generation to complete

1. Call `browser_evaluate` with this function to check if generation is complete:

```javascript
() => {
  const imgs = [...document.querySelectorAll('img')].filter(
    img => img.src.startsWith('https://files.oaiusercontent.com')
  );
  const stillGenerating = !!document.querySelector('[aria-label="Stop generating"]');
  return { done: imgs.length > 0 && !stillGenerating };
}
```

Wait 5 seconds, then repeat. If `done` is `true`, proceed. If 120 seconds elapse and `done` is still `false`, treat as TIMEOUT.

   **If TIMEOUT:** Record as `TIMEOUT`. Print: `⚠ TIMEOUT: [category] "<prompt>"`. Move to the next prompt.

   **If the page displays a rate-limit message** (call `browser_evaluate` with `() => document.body.innerText.toLowerCase()` and check if the result contains "plan limit", "image generation limit", "too many requests", or "limit reached"):
   Wait 60 seconds. Retry the polling loop once. If still rate-limited, record as `RATE_LIMITED`, skip all remaining prompts in the current category, and continue with the next category.

### 3f. Extract image URLs

1. Call `browser_evaluate` with the following function:

```javascript
() => {
  const imgs = [...document.querySelectorAll('img')].filter(
    img => img.src.startsWith('https://files.oaiusercontent.com')
  );
  return { urls: imgs.map(i => i.src) };
}
```

If the returned `urls` array is empty:
- Compute the slug (see Step 3g item 1) then call `browser_take_screenshot` with `filename: "<outputDir>/<category>/debug_<slug>.png"` and `type: "png"`.
- Record as `NO_IMAGE_FOUND`. Print: `⚠ NO_IMAGE_FOUND: [category] "<prompt>"`. Move to the next prompt.

### 3g. Download images

1. Compute the filename slug:
   - Take the prompt text, lowercase it, keep only the first 40 characters
   - Replace spaces with `_`
   - Strip all characters that are not alphanumeric or `_`
   - Example: `"A Sunset Over Mountains!"` → `a_sunset_over_mountains`

2. Determine the sequence number:
   ```bash
   ls "<outputDir>/<category>/<slug>"_*.png 2>/dev/null | wc -l
   ```
   Add 1 to the count and zero-pad to 2 digits (e.g., `01`, `02`). This ensures existing files are never overwritten.

3. For each URL in the extracted list:

```bash
curl -L "<url>" \
  -H "Referer: https://chatgpt.com/" \
  --retry 1 \
  --retry-delay 5 \
  -o "<outputDir>/<category>/<slug>_<N>.png"
```

Note: `files.oaiusercontent.com` URLs are signed and self-authenticating — no session cookie is required.

`<N>` is the sequence number for the first URL, incrementing for each additional URL.

**If curl exits with non-zero and the HTTP status was 403:**
Re-run the `browser_evaluate` from Step 3f to refresh the URL (they expire within minutes), then retry curl once. If still failing, record as `URL_EXPIRED`.

**If curl exits with non-zero for any other reason after retries:**
Record as `DOWNLOAD_FAILED`.

**On success:** Print: `✓ <category>/<slug>_<N>.png`

## Step 4: Print Final Summary

After all categories have been processed, print a summary in this format:

```
=== chatgpt-image-gen Summary ===
Total prompts:  X
Downloaded:     Y images
Skipped:        Z prompts

Skipped details:
- [category] "prompt text" → ERROR_CODE
```

Error codes and their meanings:
- `TIMEOUT` — ChatGPT did not finish generating within 120 seconds
- `RATE_LIMITED` — ChatGPT returned a rate limit response; remaining prompts in that category were also skipped
- `NO_IMAGE_FOUND` — Generation completed but no `files.oaiusercontent.com` image was found in the DOM
- `DOWNLOAD_FAILED` — `curl` failed after retries (non-403 error)
- `URL_EXPIRED` — Image URL returned 403 even after refreshing via `browser_evaluate`

If all prompts succeeded, print: `All prompts completed successfully.` instead of the skipped section.
