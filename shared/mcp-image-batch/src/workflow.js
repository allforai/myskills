/**
 * ChatGPT image generation workflow.
 * All browser interactions go through osascript → Chrome JS execution.
 */
import { executeInChrome, navigateChrome, sleepSync } from "./chrome.js";
import { readdirSync, statSync } from "fs";
import { join, extname } from "path";
import { homedir } from "os";

const CHATGPT_URL = "https://chatgpt.com";
const DOWNLOADS_DIR = join(homedir(), "Downloads");

// ─── Navigation ────────────────────────────────────────────────────────────

export function openFreshChat() {
  navigateChrome(CHATGPT_URL);
  sleepSync(1500);
}

// ─── Model Selection ───────────────────────────────────────────────────────

export function selectBestImageModel() {
  // Try to open the model picker and select the best image generation option
  const result = executeInChrome(`
    (function() {
      // Look for model selector button (shows current model name)
      const modelBtn = document.querySelector(
        '[data-testid="model-switcher-dropdown-button"], ' +
        'button[id*="model"], ' +
        'button[aria-haspopup="listbox"]'
      );
      if (!modelBtn) return JSON.stringify({found: false});
      modelBtn.click();
      return JSON.stringify({found: true, label: modelBtn.textContent.trim().slice(0,50)});
    })()
  `);
  try {
    const { found } = JSON.parse(result);
    if (!found) return "no_selector";
    sleepSync(800);

    // Look for image generation option in dropdown
    const selected = executeInChrome(`
      (function() {
        const opts = [...document.querySelectorAll('[role="option"], [role="menuitem"], [data-testid*="model"]')];
        // Priority: image-specific > highest capability
        const imageOpt = opts.find(o => /image|dall/i.test(o.textContent));
        const target = imageOpt || opts[opts.length - 1]; // fallback: last = newest
        if (!target) return 'none';
        target.click();
        return target.textContent.trim().slice(0, 60);
      })()
    `);
    return selected;
  } catch {
    return "parse_error";
  }
}

// ─── Prompt Submission ─────────────────────────────────────────────────────

export function submitPrompt(text) {
  // Type text into ChatGPT's contenteditable input
  const sanitized = text.replace(/\\/g, "\\\\").replace(/`/g, "\\`").replace(/\$/g, "\\$");

  const typed = executeInChrome(`
    (function() {
      const el = document.querySelector(
        '#prompt-textarea, [data-testid="prompt-textarea"], ' +
        'div[contenteditable="true"][data-id]'
      );
      if (!el) return 'no_input';
      el.focus();
      // Clear existing content
      document.execCommand('selectAll', false, null);
      document.execCommand('delete', false, null);
      // Insert text
      document.execCommand('insertText', false, \`${sanitized}\`);
      return 'typed';
    })()
  `);

  if (typed !== "typed") return { ok: false, error: `type_failed:${typed}` };

  sleepSync(300);

  // Click send button
  const sent = executeInChrome(`
    (function() {
      const btn = document.querySelector(
        '[data-testid="send-button"], ' +
        'button[aria-label*="Send"], button[aria-label*="发送"]'
      );
      if (!btn) return 'no_button';
      if (btn.disabled) return 'disabled';
      btn.click();
      return 'sent';
    })()
  `);

  return { ok: sent === "sent", error: sent !== "sent" ? sent : null };
}

// ─── Wait for Generation ───────────────────────────────────────────────────

// Detect by image URL pattern — language-independent
const GENERATED_IMG_JS = `
  [...document.querySelectorAll('main img')]
    .filter(i => i.src && (
      i.src.includes('chatgpt.com/backend-api') ||
      i.src.includes('oaiusercontent.com') ||
      i.src.includes('estuary/content')
    ) && i.naturalWidth > 0)
`;

const CHECK_JS = `
  JSON.stringify({
    done: (${GENERATED_IMG_JS}).length > 0
      && !document.querySelector('[data-testid="stop-button"], [aria-label="Stop generating"]'),
    generating: !!document.querySelector('[data-testid="stop-button"], [aria-label="Stop generating"]'),
    rateLimited: /plan limit|image generation limit|too many requests|limit reached/i.test(document.body.innerText)
  })
`;

export function waitForImageGeneration(timeoutMs = 180000, log = () => {}) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const raw = executeInChrome(CHECK_JS);
      const state = JSON.parse(raw);
      if (state.rateLimited) return { ok: false, error: "RATE_LIMITED" };
      if (state.done) return { ok: true };
      log(state.generating ? "generating..." : "waiting...");
    } catch (e) {
      log(`poll_error: ${e.message}`);
    }
    sleepSync(5000);
  }
  return { ok: false, error: "TIMEOUT" };
}

// ─── Download via Browser fetch ────────────────────────────────────────────

export function downloadImageViaBrowser(slug, n) {
  const filename = `${slug}_${String(n).padStart(2, "0")}.png`;

  // Step 1: open fullscreen dialog (click on image button)
  executeInChrome(`
    (function() {
      const btn = [...document.querySelectorAll('button')]
        .find(b => b.querySelector('img[alt*="Generated image"]') || b.textContent.includes('已生成图片'));
      if (btn) btn.click();
    })()
  `);
  sleepSync(1500);

  // Step 2: click 保存/Save in the dialog
  const clicked = executeInChrome(`
    (function() {
      // Try dialog save button first
      const dlg = document.querySelector('dialog, [role="dialog"]');
      if (dlg) {
        const saveBtn = [...dlg.querySelectorAll('button')]
          .find(b => /保存|save|download/i.test(b.textContent + b.getAttribute('aria-label')));
        if (saveBtn) { saveBtn.click(); return 'dialog_save'; }
      }
      // Fallback: use fetch to download directly
      return 'fallback_fetch';
    })()
  `);

  if (clicked === "dialog_save") {
    sleepSync(4000);
    return findLatestDownload(filename);
  }

  // Fallback: fetch the image from within the page and trigger download
  executeInChrome(`
    window.__mcpImgDownload = null;
    (async function() {
      const img = [...document.querySelectorAll('main img')]
        .find(i => i.src && (
          i.src.includes('chatgpt.com/backend-api') ||
          i.src.includes('oaiusercontent.com') ||
          i.src.includes('estuary/content')
        ) && i.naturalWidth > 0);
      if (!img) { window.__mcpImgDownload = 'no_image'; return; }
      try {
        const res = await fetch(img.src);
        const blob = await res.blob();
        const a = Object.assign(document.createElement('a'), {
          href: URL.createObjectURL(blob),
          download: '${filename}'
        });
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.__mcpImgDownload = 'ok';
      } catch(e) { window.__mcpImgDownload = 'err:' + e.message; }
    })();
    'initiated'
  `);

  // Poll for completion
  const deadline = Date.now() + 20000;
  while (Date.now() < deadline) {
    sleepSync(1000);
    const status = executeInChrome("window.__mcpImgDownload || 'pending'");
    if (status === "ok") break;
    if (status.startsWith("err:") || status === "no_image") {
      return { ok: false, path: null, error: status };
    }
  }

  sleepSync(2000);
  return findLatestDownload(filename);
}

function findLatestDownload(preferredName) {
  // Check if preferred filename exists
  const preferred = join(DOWNLOADS_DIR, preferredName);
  try {
    statSync(preferred);
    return { ok: true, path: preferred };
  } catch {}

  // Fall back to most recent image file in Downloads
  try {
    const files = readdirSync(DOWNLOADS_DIR)
      .filter(f => /\.(png|jpg|jpeg|webp)$/i.test(f))
      .map(f => ({ f, mtime: statSync(join(DOWNLOADS_DIR, f)).mtimeMs }))
      .sort((a, b) => b.mtime - a.mtime);

    if (files.length && Date.now() - files[0].mtime < 30000) {
      return { ok: true, path: join(DOWNLOADS_DIR, files[0].f) };
    }
  } catch {}

  return { ok: false, path: null, error: "not_in_downloads" };
}

// ─── Slug utility ──────────────────────────────────────────────────────────

export function makeSlug(text) {
  return text.toLowerCase().slice(0, 40).replace(/\s+/g, "_").replace(/[^a-z0-9_]/g, "");
}
