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
