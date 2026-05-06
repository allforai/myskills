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

### 3a. Open a fresh ChatGPT conversation

1. Call `navigate_page` with URL `https://chatgpt.com`
2. Call `take_snapshot`. Find the element with accessible name "New chat" and call `click` on it.
3. Call `take_snapshot`. Read the model selector label displayed at the top center of the page.
   - If the label is not "GPT-4o": call `click` on the model selector, then `take_snapshot`, then `click` on "GPT-4o" in the dropdown.
   - GPT-4o supports image generation natively. Do not look for a separate "DALL-E" option.

### 3b. Submit the prompt

4. Call `take_snapshot`. Find the prompt input element (role: textbox) and call `fill` with the current prompt text.
5. Call `press_key` with key `Enter`.

### 3c. Wait for generation to complete

6. Poll every 5 seconds using `wait_for` for the following condition to be true:
   - An `<img>` element whose `src` attribute starts with `https://files.oaiusercontent.com` is present in the page, AND
   - The "Stop generating" button (or spinner) is no longer visible.
   - Maximum wait: 120 seconds.

   **If generation times out (120s elapsed):**
   Record this prompt as `TIMEOUT`. Print: `⚠ TIMEOUT: [category] "<prompt>"`. Move to the next prompt.

   **If the page displays a rate-limit message** (page text contains "rate limit", "too many requests", or "limit reached"):
   Wait 60 seconds. Retry the `wait_for` loop once. If still rate-limited, record as `RATE_LIMITED`, skip all remaining prompts in the current category, and continue with the next category.

### 3d. Extract image URLs and session cookies

7. Call `evaluate_script` with the following JavaScript:

```javascript
(() => {
  const imgs = [...document.querySelectorAll('img')].filter(
    img => img.src.startsWith('https://files.oaiusercontent.com')
  );
  return {
    urls: imgs.map(i => i.src),
    cookies: document.cookie
  };
})()
```

If the returned `urls` array is empty:
- Call `take_screenshot` and save it to `<outputDir>/<category>/debug_<slug>.png` for diagnosis.
- Record as `NO_IMAGE_FOUND`. Print: `⚠ NO_IMAGE_FOUND: [category] "<prompt>"`. Move to the next prompt.

### 3e. Download images

8. Compute the filename slug:
   - Take the prompt text, lowercase it, keep only the first 40 characters
   - Replace spaces with `_`
   - Strip all characters that are not alphanumeric or `_`
   - Example: `"A Sunset Over Mountains!"` → `a_sunset_over_mountains`

9. Determine the sequence number:
   ```bash
   ls "<outputDir>/<category>/<slug>"_*.png 2>/dev/null | wc -l
   ```
   Add 1 to the count and zero-pad to 2 digits (e.g., `01`, `02`). This ensures existing files are never overwritten.

10. For each URL in the extracted list (index `i`, starting at 1):

```bash
curl -L "<url>" \
  --cookie "<cookies>" \
  -H "Referer: https://chatgpt.com/" \
  --retry 1 \
  --retry-delay 5 \
  -o "<outputDir>/<category>/<slug>_<N>.png"
```

Where `<N>` is the sequence number for the first URL, incrementing for subsequent URLs.

**If curl exits with non-zero and the HTTP status was 403:**
Re-run the `evaluate_script` from Step 3d to refresh the URL (they expire within minutes), then retry curl once. If still failing, record as `URL_EXPIRED`.

**If curl exits with non-zero for any other reason after retries:**
Record as `DOWNLOAD_FAILED`.

**On success:** Print: `✓ <category>/<slug>_<N>.png`
