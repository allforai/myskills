# chatgpt-image-gen Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a `/chatgpt-image-gen` slash command that reads a JSON file of categorized prompts, uses `chrome-devtools-mcp` to generate images on ChatGPT, and downloads them into per-category subfolders.

**Architecture:** Single markdown command file containing directive prose for Claude to follow. No runtime code — the implementation IS the instructions. Browser automation via `chrome-devtools-mcp` MCP tools; file operations via Bash (`mkdir`, `curl`). Verified via smoke tests with a minimal fixture JSON.

**Tech Stack:** `chrome-devtools-mcp` (navigate_page, take_snapshot, click, fill, press_key, wait_for, evaluate_script), Bash curl, Claude Code slash command format.

---

## File Structure

```
.claude/commands/chatgpt-image-gen.md          ← main slash command (CREATE)
.claude/commands/examples/chatgpt-image-test.json  ← smoke test fixture (CREATE)
```

---

### Task 1: Create smoke test fixture

**Files:**
- Create: `.claude/commands/examples/chatgpt-image-test.json`

This fixture uses 2 categories × 1 prompt each for fast manual testing.

- [ ] **Step 1: Create the examples directory and fixture file**

```bash
mkdir -p .claude/commands/examples
```

Write `.claude/commands/examples/chatgpt-image-test.json`:

```json
{
  "outputDir": "./chatgpt-images-test",
  "categories": {
    "landscapes": ["a misty mountain at sunrise"],
    "portraits": ["a samurai warrior in armor, dramatic lighting"]
  }
}
```

- [ ] **Step 2: Verify the file is valid JSON**

```bash
python3 -m json.tool .claude/commands/examples/chatgpt-image-test.json
```

Expected output: the pretty-printed JSON with no errors.

- [ ] **Step 3: Commit**

```bash
git add .claude/commands/examples/chatgpt-image-test.json
git commit -m "feat: add chatgpt-image-gen smoke test fixture"
```

---

### Task 2: Create command file — skeleton and input validation

**Files:**
- Create: `.claude/commands/chatgpt-image-gen.md`

- [ ] **Step 1: Write the command file with frontmatter and input validation section**

Write `.claude/commands/chatgpt-image-gen.md`:

```markdown
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
```

- [ ] **Step 2: Smoke test — invalid input should fail gracefully**

In Claude Code, run:
```
/chatgpt-image-gen /nonexistent/path.json
```
Expected: Claude prints an error about the file not existing and stops. No browser opens.

- [ ] **Step 3: Smoke test — invalid JSON structure**

Create a temp invalid file:
```bash
echo '{"outputDir": "./out"}' > /tmp/bad.json
```

Run: `/chatgpt-image-gen /tmp/bad.json`

Expected: Claude prints an error about missing `categories` field and stops.

- [ ] **Step 4: Commit**

```bash
git add .claude/commands/chatgpt-image-gen.md
git commit -m "feat: add chatgpt-image-gen command skeleton with input validation"
```

---

### Task 3: Add directory initialization section

**Files:**
- Modify: `.claude/commands/chatgpt-image-gen.md`

- [ ] **Step 1: Append Step 2 to the command file**

Add after the Step 1 section:

```markdown
## Step 2: Initialize Output Directories

Before processing any prompts, create all required output directories:

For each category key in `categories`, run:
```bash
mkdir -p "<outputDir>/<category>"
```

Print: `Initialized output directories under <outputDir>/`
```

- [ ] **Step 2: Smoke test — verify directories are created**

Run: `/chatgpt-image-gen .claude/commands/examples/chatgpt-image-test.json`

Claude should stop after creating directories (it hasn't been given Step 3 yet — it will say it doesn't know what to do next). Verify:

```bash
ls -la ./chatgpt-images-test/
```

Expected: `landscapes/` and `portraits/` directories exist.

- [ ] **Step 3: Clean up test output**

```bash
rm -rf ./chatgpt-images-test/
```

- [ ] **Step 4: Commit**

```bash
git add .claude/commands/chatgpt-image-gen.md
git commit -m "feat: chatgpt-image-gen — add output directory initialization"
```

---

### Task 4: Add browser automation section (navigate → submit → wait)

**Files:**
- Modify: `.claude/commands/chatgpt-image-gen.md`

- [ ] **Step 1: Append the browser interaction section**

Add after Step 2:

```markdown
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
```

- [ ] **Step 2: Smoke test — navigate and submit flow**

Ensure you are logged into ChatGPT in Chrome (persistent profile). Run:

```
/chatgpt-image-gen .claude/commands/examples/chatgpt-image-test.json
```

Observe in the browser: Claude should open chatgpt.com, click New Chat, verify GPT-4o is selected, type the first prompt, and wait. The command will stall waiting after `wait_for` completes (no download step yet).

Verify in the browser that the prompt was submitted and an image appeared.

Interrupt with Ctrl+C once you confirm the browser flow works.

- [ ] **Step 3: Commit**

```bash
git add .claude/commands/chatgpt-image-gen.md
git commit -m "feat: chatgpt-image-gen — add browser navigation, submit, and wait logic"
```

---

### Task 5: Add image extraction and download section

**Files:**
- Modify: `.claude/commands/chatgpt-image-gen.md`

- [ ] **Step 1: Append the extraction and download section**

Add after Step 3c:

```markdown
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
```

- [ ] **Step 2: Smoke test — full end-to-end**

Run the full command:

```
/chatgpt-image-gen .claude/commands/examples/chatgpt-image-test.json
```

Expected behavior:
1. Directories created
2. Browser opens, submits each prompt, waits for image
3. Downloads each image with curl
4. Prints `✓` lines

Verify:
```bash
ls -lh ./chatgpt-images-test/landscapes/
ls -lh ./chatgpt-images-test/portraits/
```

Expected: one `.png` file per prompt, non-zero size.

- [ ] **Step 3: Clean up test output**

```bash
rm -rf ./chatgpt-images-test/
```

- [ ] **Step 4: Commit**

```bash
git add .claude/commands/chatgpt-image-gen.md
git commit -m "feat: chatgpt-image-gen — add evaluate_script extraction and curl download"
```

---

### Task 6: Add summary output section

**Files:**
- Modify: `.claude/commands/chatgpt-image-gen.md`

- [ ] **Step 1: Append the summary section**

Add after Step 3:

```markdown
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
- `URL_EXPIRED` — Image URL returned 403 even after refreshing via `evaluate_script`

If all prompts succeeded, print: `All prompts completed successfully.` instead of the skipped section.
```

- [ ] **Step 2: Smoke test — verify summary output**

Run the full command again:

```
/chatgpt-image-gen .claude/commands/examples/chatgpt-image-test.json
```

Verify the final output contains the summary block with correct counts.

- [ ] **Step 3: Clean up test output**

```bash
rm -rf ./chatgpt-images-test/
```

- [ ] **Step 4: Commit**

```bash
git add .claude/commands/chatgpt-image-gen.md
git commit -m "feat: chatgpt-image-gen — add final summary output section"
```

---

### Task 7: Full end-to-end smoke test with multi-category fixture

**Files:** None created. Verification only.

- [ ] **Step 1: Create a multi-category test fixture**

```bash
cat > /tmp/chatgpt-multi-test.json << 'EOF'
{
  "outputDir": "./chatgpt-images-multi-test",
  "categories": {
    "landscapes": [
      "a misty mountain at sunrise",
      "an ocean cliff at sunset"
    ],
    "portraits": [
      "a samurai warrior in armor, dramatic lighting"
    ]
  }
}
EOF
```

- [ ] **Step 2: Run the full command**

```
/chatgpt-image-gen /tmp/chatgpt-multi-test.json
```

- [ ] **Step 3: Verify output structure**

```bash
find ./chatgpt-images-multi-test -type f | sort
```

Expected output (exact filenames will vary by slug):
```
./chatgpt-images-multi-test/landscapes/a_misty_mountain_at_sunrise_01.png
./chatgpt-images-multi-test/landscapes/an_ocean_cliff_at_sunset_01.png
./chatgpt-images-multi-test/portraits/a_samurai_warrior_in_armor_dra_01.png
```

- [ ] **Step 4: Verify file sizes are non-zero**

```bash
find ./chatgpt-images-multi-test -name "*.png" -size 0
```

Expected: no output (all files have content).

- [ ] **Step 5: Clean up**

```bash
rm -rf ./chatgpt-images-multi-test/
rm /tmp/chatgpt-multi-test.json
```

- [ ] **Step 6: Final commit**

```bash
git add .claude/commands/chatgpt-image-gen.md
git commit -m "feat: chatgpt-image-gen — complete slash command"
```

---

## Spec Coverage Check

| Spec Requirement | Task |
|-----------------|------|
| JSON input with `outputDir` + `categories` | Task 2 |
| Per-category subdirectory creation | Task 3 |
| navigate → new chat → model check → fill → submit | Task 4 |
| wait_for with 120s timeout | Task 4 |
| Rate limit detection + 60s retry | Task 4 |
| evaluate_script to extract URLs + cookies | Task 5 |
| curl with cookies + Referer header | Task 5 |
| File naming slug + sequence number | Task 5 |
| Never overwrite existing files | Task 5 |
| Multi-image per prompt handled | Task 5 |
| URL expiry → re-evaluate + retry | Task 5 |
| TIMEOUT / RATE_LIMITED / NO_IMAGE_FOUND / DOWNLOAD_FAILED / URL_EXPIRED | Tasks 4–5 |
| Final summary with error list | Task 6 |
| Skill frontmatter (description + argument-hint) | Task 2 |
