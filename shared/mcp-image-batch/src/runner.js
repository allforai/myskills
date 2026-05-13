#!/usr/bin/env node
/**
 * Standalone batch runner — spawned by the MCP server as a detached process.
 * Writes progress to {outputDir}/.progress.json, log to {outputDir}/.log.txt,
 * and job state to {outputDir}/.job.json.
 *
 * Usage: node runner.js <prompts_file>
 */
import { readFileSync, writeFileSync, mkdirSync, existsSync, readdirSync, renameSync, appendFileSync } from "fs";
import { join, extname } from "path";

import { openFreshChat, selectBestImageModel, submitPrompt, waitForImageGeneration, downloadImageViaBrowser, makeSlug, countGeneratedImages, uploadImageToChat, clickEditOnImage, waitForEditorCanvas, drawMaskOnCanvas, submitEditPrompt } from "./workflow.js";
import { activateChrome } from "./chrome.js";

const promptsFile = process.argv[2];
if (!promptsFile) {
  console.error("Usage: node runner.js <prompts_file>");
  process.exit(1);
}

let config;
try {
  config = JSON.parse(readFileSync(promptsFile, "utf8"));
} catch (e) {
  console.error(`Cannot read ${promptsFile}: ${e.message}`);
  process.exit(1);
}

const { outputDir, categories, sessionMode = "per-category", categoryConfig = {} } = config;
if (!outputDir || typeof categories !== "object") {
  console.error("Invalid prompts file: needs outputDir + categories");
  process.exit(1);
}

// ── State files ──────────────────────────────────────────────────────────────

mkdirSync(outputDir, { recursive: true });
for (const cat of Object.keys(categories)) {
  mkdirSync(join(outputDir, cat), { recursive: true });
}

const stateFile   = join(outputDir, ".progress.json");
const logFile     = join(outputDir, ".log.txt");
const jobFile     = join(outputDir, ".job.json");

function log(msg) {
  const line = `[${new Date().toISOString()}] ${msg}`;
  console.log(line);
  appendFileSync(logFile, line + "\n");
}

function saveJob(extra = {}) {
  const existing = existsSync(jobFile)
    ? JSON.parse(readFileSync(jobFile, "utf8"))
    : {};
  writeFileSync(jobFile, JSON.stringify({ ...existing, ...extra }, null, 2));
}

// ── Load resume state ────────────────────────────────────────────────────────

let done = {};
if (existsSync(stateFile)) {
  try { done = JSON.parse(readFileSync(stateFile, "utf8")); } catch {}
}

const total = Object.values(categories).reduce((s, a) => s + a.length, 0);
saveJob({ pid: process.pid, status: "running", startedAt: new Date().toISOString(), promptsFile, total });
log(`=== runner started, pid=${process.pid}, total=${total} prompts ===`);

// ── Session management ───────────────────────────────────────────────────────

activateChrome();

function startSession() {
  openFreshChat();
  const model = selectBestImageModel();
  log(`Model selected: ${model}`);
}

// "shared" mode: one session for all categories
if (sessionMode === "shared") startSession();

// ── Process prompts ──────────────────────────────────────────────────────────

let downloaded = 0;
const skipped = [];

outer: for (const [category, prompts] of Object.entries(categories)) {
  const catCfg = categoryConfig[category] ?? {};

  if (sessionMode === "per-category") {
    startSession();
    const editMode = catCfg.editMode;

    if (editMode) {
      // Upload reference image and generate the "base" that will be edited
      if (editMode.contextImage) {
        log(`Uploading base reference for [${category}]: ${editMode.contextImage}`);
        const up = uploadImageToChat(editMode.contextImage);
        log(`Reference upload: ${JSON.stringify(up)}`);
        if (!up.ok) log(`  ⚠ reference upload failed — continuing without reference`);
        sleepSync(1000);
      }
      if (editMode.basePrompt) {
        log(`Generating base image: "${editMode.basePrompt.slice(0, 60)}..."`);
        const baseSubmit = submitPrompt(editMode.basePrompt);
        if (!baseSubmit.ok) {
          log(`  ⚠ base prompt submit failed: ${baseSubmit.error}`);
        } else {
          const baseGen = waitForImageGeneration(180000, (msg) => log(`  [base] ${msg}`), 0);
          log(`  Base image: ${baseGen.ok ? 'ready' : baseGen.error}`);
          sleepSync(1500);
        }
      }
    } else if (catCfg.contextImage) {
      log(`Uploading context image for [${category}]: ${catCfg.contextImage}`);
      const up = uploadImageToChat(catCfg.contextImage);
      log(`Context image upload: ${JSON.stringify(up)}`);
      if (up.ok) sleepSync(2000);
    }
  }

  for (const prompt of prompts) {
    const key = `${category}::${prompt}`;

    if (done[key]) {
      log(`⏭ skip (done): [${category}] "${prompt}"`);
      downloaded++;
      continue;
    }

    log(`\n→ [${category}] "${prompt}"`);

    if (sessionMode === "per-prompt") {
      startSession();
    }

    // Count existing images so waitForImageGeneration can detect the NEW one
    const startImageCount = sessionMode !== "per-prompt" ? countGeneratedImages() : 0;

    const editMode = catCfg?.editMode;
    let submitResult;

    if (editMode) {
      // In-painting: click 编辑 on the base image (index 0), draw mask, submit prompt
      log(`  [edit] clicking 编辑 on base image...`);
      const clickResult = clickEditOnImage(0);
      if (!clickResult.ok) {
        log(`  ⚠ edit button not found: ${clickResult.error}`);
        skipped.push({ category, prompt, error: "EDIT_BUTTON_NOT_FOUND" });
        continue;
      }
      const canvasResult = waitForEditorCanvas(15000);
      if (!canvasResult.ok) {
        log(`  ⚠ editor canvas not open`);
        skipped.push({ category, prompt, error: "CANVAS_NOT_FOUND" });
        continue;
      }
      log(`  [edit] drawing mask ${JSON.stringify(editMode.maskRegion)}`);
      const maskResult = drawMaskOnCanvas(editMode.maskRegion);
      log(`  [edit] mask: ${JSON.stringify(maskResult)}`);
      sleepSync(400);
      submitResult = submitEditPrompt(prompt);
    } else {
      submitResult = submitPrompt(prompt);
    }

    if (!submitResult.ok) {
      log(`  ⚠ submit failed: ${submitResult.error}`);
      skipped.push({ category, prompt, error: "SUBMIT_FAILED" });
      continue;
    }
    log("  submitted, waiting for generation...");

    const genResult = waitForImageGeneration(180000, (msg) => log(`  ${msg}`), startImageCount);
    if (!genResult.ok) {
      log(`  ⚠ ${genResult.error}`);
      skipped.push({ category, prompt, error: genResult.error });
      if (genResult.error === "RATE_LIMITED") {
        const remaining = prompts.slice(prompts.indexOf(prompt) + 1);
        for (const p of remaining) skipped.push({ category, prompt: p, error: "RATE_LIMITED" });
        break; // next category
      }
      continue;
    }

    const slug = makeSlug(prompt);
    const existing = readdirSync(join(outputDir, category))
      .filter(f => f.startsWith(slug + "_")).length;
    const n = existing + 1;

    const dlResult = downloadImageViaBrowser(slug, n);
    if (!dlResult.ok) {
      log(`  ⚠ download failed: ${dlResult.error}`);
      skipped.push({ category, prompt, error: "DOWNLOAD_FAILED" });
      continue;
    }

    const ext = extname(dlResult.path) || ".png";
    const dest = join(outputDir, category, `${slug}_${String(n).padStart(2, "0")}${ext}`);
    try {
      renameSync(dlResult.path, dest);
      const saved = `${category}/${slug}_${String(n).padStart(2, "0")}${ext}`;
      log(`  ✓ saved: ${saved}`);
      downloaded++;
      done[key] = dest;
      writeFileSync(stateFile, JSON.stringify(done, null, 2));
      saveJob({ downloaded, skipped: skipped.length });
    } catch (e) {
      log(`  ⚠ move failed: ${e.message}`);
      skipped.push({ category, prompt, error: "MOVE_FAILED" });
    }
  }
}

// ── Final summary ─────────────────────────────────────────────────────────────

log("\n=== chatgpt-image Summary ===");
log(`Total:      ${total}`);
log(`Downloaded: ${downloaded}`);
log(`Skipped:    ${skipped.length}`);
if (skipped.length) {
  for (const s of skipped) log(`  - [${s.category}] "${s.prompt}" → ${s.error}`);
} else {
  log("All prompts completed successfully.");
}

saveJob({ status: "done", finishedAt: new Date().toISOString(), downloaded, skipped: skipped.length });
