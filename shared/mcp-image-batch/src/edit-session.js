/**
 * Synchronous edit-mode session driver.
 *
 * Used by the MCP tools prepare_edit_session and run_edit_prompt.
 * All browser control via osascript (no Browser MCP needed here).
 * Claude Code uses Browser MCP tools between calls for visual verification.
 */
import { readFileSync, writeFileSync, existsSync, mkdirSync, readdirSync, renameSync } from "fs";
import { join, extname } from "path";
import { activateChrome, sleepSync } from "./chrome.js";
import {
  openFreshChat,
  selectBestImageModel,
  uploadImageToChat,
  submitPrompt,
  waitForImageGeneration,
  downloadImageViaBrowser,
  makeSlug,
  clickEditOnImage,
  waitForEditorCanvas,
  drawMaskOnCanvas,
  submitEditPrompt,
} from "./workflow.js";

// ─── Session state files ─────────────────────────────────────────────────────

function sessionFiles(outputDir) {
  return {
    progress: join(outputDir, ".progress.json"),
    job:      join(outputDir, ".job.json"),
    log:      join(outputDir, ".log.txt"),
  };
}

function appendLog(logFile, msg) {
  const line = `[${new Date().toISOString()}] ${msg}\n`;
  try { writeFileSync(logFile, line, { flag: "a" }); } catch {}
}

function loadProgress(progressFile) {
  if (!existsSync(progressFile)) return {};
  try { return JSON.parse(readFileSync(progressFile, "utf8")); } catch { return {}; }
}

function saveProgress(progressFile, done) {
  writeFileSync(progressFile, JSON.stringify(done, null, 2));
}

// ─── prepare_edit_session ────────────────────────────────────────────────────

/**
 * Open a fresh ChatGPT session, upload reference image, generate the base image.
 * Returns { ok, chatUrl?, error? }
 *
 * @param {string} outputDir
 * @param {object} editMode  { contextImage?, basePrompt?, maskRegion }
 */
export function prepareEditSession(outputDir, editMode) {
  mkdirSync(outputDir, { recursive: true });
  const { log: logFile, job: jobFile } = sessionFiles(outputDir);

  const saveJob = (extra) => {
    const existing = existsSync(jobFile) ? JSON.parse(readFileSync(jobFile, "utf8")) : {};
    writeFileSync(jobFile, JSON.stringify({ ...existing, ...extra }, null, 2));
  };

  saveJob({ status: "preparing", startedAt: new Date().toISOString() });
  appendLog(logFile, "=== prepare_edit_session start ===");

  activateChrome();
  openFreshChat();
  const model = selectBestImageModel();
  appendLog(logFile, `Model selected: ${model}`);

  if (editMode.contextImage) {
    appendLog(logFile, `Uploading reference: ${editMode.contextImage}`);
    const up = uploadImageToChat(editMode.contextImage);
    appendLog(logFile, `Upload result: ${JSON.stringify(up)}`);
    if (!up.ok) appendLog(logFile, "  ⚠ reference upload failed — continuing");
    sleepSync(1500);
  }

  let hasBaseImage = false;
  if (editMode.basePrompt) {
    appendLog(logFile, `Submitting base prompt: "${editMode.basePrompt.slice(0, 60)}..."`);
    const sub = submitPrompt(editMode.basePrompt);
    if (!sub.ok) {
      appendLog(logFile, `  ⚠ base prompt submit failed: ${sub.error}`);
      saveJob({ status: "failed", error: sub.error });
      return { ok: false, error: `base_submit_failed:${sub.error}` };
    }
    const gen = waitForImageGeneration(180000, (msg) => appendLog(logFile, `  [base] ${msg}`), 0);
    if (!gen.ok) {
      appendLog(logFile, `  ⚠ base generation failed: ${gen.error}`);
      saveJob({ status: "failed", error: gen.error });
      return { ok: false, error: `base_gen_failed:${gen.error}` };
    }
    hasBaseImage = true;
    appendLog(logFile, "  Base image ready.");
    sleepSync(1500);
  }

  saveJob({ status: "session_ready", hasBaseImage });
  appendLog(logFile, "=== session ready — waiting for run_edit_prompt calls ===");

  return { ok: true, hasBaseImage };
}

// ─── run_edit_prompt ─────────────────────────────────────────────────────────

/**
 * Run one edit prompt: click 编辑 → draw mask → submit via clipboard → wait → download.
 * Returns { ok, savedPath?, error? }
 *
 * @param {string} outputDir
 * @param {string} category    sub-folder name for this category
 * @param {string} prompt      the edit prompt text
 * @param {number[]} maskRegion  [xFrac, yFrac, wFrac, hFrac]
 * @param {number} imageIndex   which base image to edit (default 0 = last)
 */
export function runEditPrompt(outputDir, category, prompt, maskRegion, imageIndex = 0) {
  const catDir = join(outputDir, category);
  mkdirSync(catDir, { recursive: true });
  const { progress: progressFile, log: logFile, job: jobFile } = sessionFiles(outputDir);

  const done = loadProgress(progressFile);
  const key = `${category}::${prompt}`;

  if (done[key]) {
    appendLog(logFile, `⏭ skip (already done): ${key}`);
    return { ok: true, skipped: true, savedPath: done[key] };
  }

  const saveJob = (extra) => {
    const existing = existsSync(jobFile) ? JSON.parse(readFileSync(jobFile, "utf8")) : {};
    writeFileSync(jobFile, JSON.stringify({ ...existing, ...extra }, null, 2));
  };

  appendLog(logFile, `\n→ [${category}] "${prompt}"`);

  // Count existing images so waitForImageGeneration can detect the NEW one
  const startCount = 0; // in per-prompt edit sessions, each prompt is a new reply

  // Step 1: Click 编辑 on the base image
  appendLog(logFile, `  [edit] clicking 编辑 on image index ${imageIndex}...`);
  const clickResult = clickEditOnImage(imageIndex);
  if (!clickResult.ok) {
    const err = `EDIT_BUTTON_NOT_FOUND: ${clickResult.error}`;
    appendLog(logFile, `  ⚠ ${err}`);
    return { ok: false, error: err };
  }
  sleepSync(3000); // wait for editor dialog animation

  // Step 2: Wait for editor canvas/dialog
  appendLog(logFile, "  [edit] waiting for editor dialog...");
  const canvasResult = waitForEditorCanvas(25000);
  if (!canvasResult.ok) {
    const err = `CANVAS_NOT_FOUND: ${JSON.stringify(canvasResult.debug ?? {})}`;
    appendLog(logFile, `  ⚠ ${err}`);
    return { ok: false, error: err };
  }
  appendLog(logFile, `  [edit] editor open: ${JSON.stringify(canvasResult.found)}`);

  // Step 3: Draw mask
  appendLog(logFile, `  [edit] drawing mask ${JSON.stringify(maskRegion)}`);
  const maskResult = drawMaskOnCanvas(maskRegion);
  appendLog(logFile, `  [edit] mask: ${JSON.stringify(maskResult)}`);
  sleepSync(400);

  // Step 4: Submit prompt via clipboard (bypasses React event blocking)
  appendLog(logFile, `  [edit] submitting prompt via clipboard...`);
  const submitResult = submitEditPrompt(prompt);
  if (!submitResult.ok) {
    const err = `SUBMIT_FAILED: ${submitResult.error}`;
    appendLog(logFile, `  ⚠ ${err}`);
    return { ok: false, error: err };
  }
  appendLog(logFile, "  submitted, waiting for generation...");

  // Step 5: Wait for the new generated image
  const genResult = waitForImageGeneration(
    180000,
    (msg) => appendLog(logFile, `  ${msg}`),
    startCount
  );
  if (!genResult.ok) {
    const err = genResult.error;
    appendLog(logFile, `  ⚠ generation failed: ${err}`);
    return { ok: false, error: err };
  }

  // Step 6: Download and save
  const slug = makeSlug(prompt);
  const existing = readdirSync(catDir).filter(f => f.startsWith(slug + "_")).length;
  const n = existing + 1;

  const dlResult = downloadImageViaBrowser(slug, n);
  if (!dlResult.ok) {
    appendLog(logFile, `  ⚠ download failed: ${dlResult.error}`);
    return { ok: false, error: `DOWNLOAD_FAILED: ${dlResult.error}` };
  }

  const ext = extname(dlResult.path) || ".png";
  const dest = join(catDir, `${slug}_${String(n).padStart(2, "0")}${ext}`);
  try {
    renameSync(dlResult.path, dest);
  } catch (e) {
    return { ok: false, error: `MOVE_FAILED: ${e.message}` };
  }

  done[key] = dest;
  saveProgress(progressFile, done);
  const downloaded = Object.keys(done).length;
  saveJob({ downloaded });
  appendLog(logFile, `  ✓ saved: ${category}/${slug}_${String(n).padStart(2, "0")}${ext}`);

  return { ok: true, savedPath: dest };
}
