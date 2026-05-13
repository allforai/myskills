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

import { openFreshChat, selectBestImageModel, submitPrompt, waitForImageGeneration, downloadImageViaBrowser, makeSlug } from "./workflow.js";
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

const { outputDir, categories } = config;
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

// ── Select model once ────────────────────────────────────────────────────────

activateChrome();
openFreshChat();
const modelSelected = selectBestImageModel();
log(`Model selected: ${modelSelected}`);

// ── Process prompts ──────────────────────────────────────────────────────────

let downloaded = 0;
const skipped = [];

outer: for (const [category, prompts] of Object.entries(categories)) {
  for (const prompt of prompts) {
    const key = `${category}::${prompt}`;

    if (done[key]) {
      log(`⏭ skip (done): [${category}] "${prompt}"`);
      downloaded++;
      continue;
    }

    log(`\n→ [${category}] "${prompt}"`);

    openFreshChat();

    const submitResult = submitPrompt(prompt);
    if (!submitResult.ok) {
      log(`  ⚠ submit failed: ${submitResult.error}`);
      skipped.push({ category, prompt, error: "SUBMIT_FAILED" });
      continue;
    }
    log("  submitted, waiting for generation...");

    const genResult = waitForImageGeneration(180000, (msg) => log(`  ${msg}`));
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
