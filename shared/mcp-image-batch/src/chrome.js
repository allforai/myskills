/**
 * Chrome control via macOS osascript.
 * Executes JavaScript in the user's logged-in Chrome — no Playwright, no login.
 */
import { execSync } from "child_process";
import { writeFileSync, unlinkSync } from "fs";
import { tmpdir } from "os";
import { join } from "path";

function tmpPath(ext) {
  return join(tmpdir(), `mcp_cgpt_${Date.now()}_${Math.random().toString(36).slice(2)}.${ext}`);
}

/**
 * Execute JS in Chrome's front tab, return result as string.
 * For async code, store result in window.__mcpResult and poll with checkAsyncResult().
 */
export function executeInChrome(jsCode) {
  const jsFile = tmpPath("js");
  const asFile = tmpPath("applescript");

  writeFileSync(jsFile, jsCode);
  writeFileSync(asFile,
    `set src to (do shell script "cat '${jsFile}'")\n` +
    `tell application "Google Chrome" to execute front window's active tab javascript src`
  );

  try {
    return execSync(`osascript '${asFile}'`, { encoding: "utf8", timeout: 30000 }).trim();
  } finally {
    try { unlinkSync(jsFile); } catch {}
    try { unlinkSync(asFile); } catch {}
  }
}

/**
 * Navigate Chrome's front tab to a URL and wait for page load (up to 20s).
 */
export function navigateChrome(url) {
  const asFile = tmpPath("applescript");
  writeFileSync(asFile,
    `tell application "Google Chrome" to set URL of front window's active tab to "${url.replace(/"/g, '\\"')}"`
  );
  try {
    execSync(`osascript '${asFile}'`, { encoding: "utf8", timeout: 15000 });
  } finally {
    try { unlinkSync(asFile); } catch {}
  }

  // Poll until readyState === complete
  const deadline = Date.now() + 20000;
  while (Date.now() < deadline) {
    try {
      if (executeInChrome("document.readyState") === "complete") return true;
    } catch {}
    sleepSync(500);
  }
  return false; // partial load ok, continue
}

/**
 * Bring Chrome to front.
 */
export function activateChrome() {
  try {
    execSync(`osascript -e 'tell application "Google Chrome" to activate'`, { timeout: 5000 });
  } catch {}
}

/**
 * Copy an image file to the macOS clipboard using AppleScript.
 * Supports PNG and JPEG.
 */
export function copyImageToClipboard(imagePath) {
  const ext = imagePath.split('.').pop().toLowerCase();
  const asType = (ext === 'jpg' || ext === 'jpeg') ? '«class JPEG»' : '«class PNGf»';
  const asFile = tmpPath("applescript");
  const escaped = imagePath.replace(/\\/g, "\\\\").replace(/"/g, '\\"');
  writeFileSync(asFile,
    `set the clipboard to (read (POSIX file "${escaped}") as ${asType})`
  );
  try {
    execSync(`osascript '${asFile}'`, { encoding: "utf8", timeout: 10000 });
    return true;
  } catch {
    return false;
  } finally {
    try { unlinkSync(asFile); } catch {}
  }
}

/**
 * Copy plain text to the macOS clipboard via pbcopy.
 * Use this before pasteInChrome() to bypass ChatGPT's React event blocking.
 */
export function copyTextToClipboard(text) {
  try {
    execSync(`printf '%s' ${JSON.stringify(text)} | pbcopy`, { timeout: 5000 });
    return true;
  } catch {
    return false;
  }
}

/**
 * Press Return/Enter in Chrome via System Events.
 */
export function pressReturnInChrome() {
  const asFile = tmpPath("applescript");
  writeFileSync(asFile,
    `tell application "Google Chrome" to activate\n` +
    `delay 0.2\n` +
    `tell application "System Events" to key code 36`
  );
  try {
    execSync(`osascript '${asFile}'`, { encoding: "utf8", timeout: 5000 });
    return true;
  } catch {
    return false;
  } finally {
    try { unlinkSync(asFile); } catch {}
  }
}

/**
 * Send Cmd+V to Chrome's front tab via System Events (pastes clipboard).
 */
export function pasteInChrome() {
  const asFile = tmpPath("applescript");
  writeFileSync(asFile,
    `tell application "Google Chrome" to activate\n` +
    `delay 0.3\n` +
    `tell application "System Events" to keystroke "v" using command down`
  );
  try {
    execSync(`osascript '${asFile}'`, { encoding: "utf8", timeout: 5000 });
    return true;
  } catch {
    return false;
  } finally {
    try { unlinkSync(asFile); } catch {}
  }
}

export function sleepSync(ms) {
  execSync(`sleep ${(ms / 1000).toFixed(2)}`, { timeout: ms + 2000 });
}
