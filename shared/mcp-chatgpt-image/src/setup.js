/**
 * Pre-flight checks for mcp-chatgpt-image.
 * Returns { ok, checks } where each check has { name, ok, message, fix? }
 */
import { execSync } from "child_process";
import { executeInChrome, activateChrome } from "./chrome.js";
import { platform } from "os";

export async function runSetupChecks() {
  const checks = [];

  // ── 1. macOS ───────────────────────────────────────────────────────────────
  const isMac = platform() === "darwin";
  checks.push({
    name: "macOS",
    ok: isMac,
    message: isMac ? "darwin" : `unsupported platform: ${platform()}`,
    fix: isMac ? null : "This tool only works on macOS (uses osascript)."
  });
  if (!isMac) return { ok: false, checks };

  // ── 2. osascript available ─────────────────────────────────────────────────
  let osascriptOk = false;
  try {
    execSync("which osascript", { stdio: "pipe" });
    osascriptOk = true;
  } catch {}
  checks.push({
    name: "osascript",
    ok: osascriptOk,
    message: osascriptOk ? "found" : "not found",
    fix: osascriptOk ? null : "osascript should be built into macOS — something is very wrong."
  });
  if (!osascriptOk) return { ok: false, checks };

  // ── 3. Chrome is running ───────────────────────────────────────────────────
  let chromeRunning = false;
  try {
    const out = execSync("pgrep -x 'Google Chrome'", { stdio: "pipe", encoding: "utf8" });
    chromeRunning = out.trim().length > 0;
  } catch {}
  checks.push({
    name: "Chrome running",
    ok: chromeRunning,
    message: chromeRunning ? "yes" : "not running",
    fix: chromeRunning ? null : "Open Google Chrome before running a batch."
  });
  if (!chromeRunning) return { ok: false, checks };

  // ── 4. osascript can talk to Chrome (Accessibility permission) ─────────────
  let canTalk = false;
  let talkError = "";
  try {
    activateChrome();
    const result = execSync(
      `osascript -e 'tell application "Google Chrome" to return (count of windows)'`,
      { encoding: "utf8", timeout: 8000, stdio: "pipe" }
    ).trim();
    canTalk = /^\d+$/.test(result);
  } catch (e) {
    talkError = e.stderr?.toString().trim() || e.message;
  }
  checks.push({
    name: "osascript → Chrome",
    ok: canTalk,
    message: canTalk ? "ok" : `failed: ${talkError}`,
    fix: canTalk ? null :
      "Go to System Settings → Privacy & Security → Accessibility → enable Terminal (or iTerm2)."
  });
  if (!canTalk) return { ok: false, checks };

  // ── 5. chatgpt.com tab is open ─────────────────────────────────────────────
  let chatgptOpen = false;
  try {
    const result = execSync(
      `osascript -e 'tell application "Google Chrome" to return URL of active tab of front window'`,
      { encoding: "utf8", timeout: 8000, stdio: "pipe" }
    ).trim();
    chatgptOpen = result.includes("chatgpt.com");
  } catch {}
  checks.push({
    name: "chatgpt.com tab",
    ok: chatgptOpen,
    message: chatgptOpen ? "open in front tab" : "not in front tab",
    fix: chatgptOpen ? null :
      "Open https://chatgpt.com in Chrome's front tab before running a batch."
  });
  if (!chatgptOpen) return { ok: false, checks };

  // ── 6. JS execution works ──────────────────────────────────────────────────
  let jsOk = false;
  let jsError = "";
  try {
    const result = executeInChrome(`document.location.hostname`);
    jsOk = result.includes("chatgpt.com");
  } catch (e) {
    jsError = e.message;
  }
  checks.push({
    name: "JS execution",
    ok: jsOk,
    message: jsOk ? "ok" : `failed: ${jsError}`,
    fix: jsOk ? null :
      "Check that Chrome's JavaScript is enabled and the tab has finished loading."
  });
  if (!jsOk) return { ok: false, checks };

  // ── 7. Logged into ChatGPT ─────────────────────────────────────────────────
  let loggedIn = false;
  try {
    const result = executeInChrome(`
      JSON.stringify({
        hasInput: !!document.querySelector('#prompt-textarea, [data-testid="prompt-textarea"], div[contenteditable="true"][data-id]'),
        hasLogin: /sign.?in|log.?in/i.test(document.body?.innerText?.slice(0, 500) ?? '')
      })
    `);
    const state = JSON.parse(result);
    loggedIn = state.hasInput && !state.hasLogin;
  } catch {}
  checks.push({
    name: "ChatGPT logged in",
    ok: loggedIn,
    message: loggedIn ? "yes" : "not logged in or page not ready",
    fix: loggedIn ? null :
      "Log into chatgpt.com in Chrome, wait for the chat input to appear, then retry."
  });

  const allOk = checks.every(c => c.ok);
  return { ok: allOk, checks };
}
