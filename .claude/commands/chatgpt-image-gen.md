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
