/**
 * ChatGPT image generation workflow.
 * All browser interactions go through osascript → Chrome JS execution.
 */
import { executeInChrome, navigateChrome, sleepSync, copyImageToClipboard, pasteInChrome, copyTextToClipboard, pressReturnInChrome } from "./chrome.js";
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
  // Focus and select-all in ChatGPT's main input.
  // ChatGPT's React blocks insertText via execCommand, so we use clipboard paste.
  const focused = executeInChrome(`
    (function() {
      const el = document.querySelector(
        '#prompt-textarea, [data-testid="prompt-textarea"], ' +
        'div[contenteditable="true"][data-id]'
      );
      if (!el) return 'no_input';
      el.focus();
      document.execCommand('selectAll', false, null);
      document.execCommand('delete', false, null);
      return 'focused';
    })()
  `);
  if (focused !== 'focused') return { ok: false, error: `focus_failed:${focused}` };

  if (!copyTextToClipboard(text)) return { ok: false, error: 'clipboard_failed' };
  sleepSync(100);
  pasteInChrome();
  sleepSync(400);

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
    imageCount: (${GENERATED_IMG_JS}).length,
    done: (${GENERATED_IMG_JS}).length > 0
      && !document.querySelector('[data-testid="stop-button"], [aria-label="Stop generating"]'),
    generating: !!document.querySelector('[data-testid="stop-button"], [aria-label="Stop generating"]'),
    rateLimited: /plan limit|image generation limit|too many requests|limit reached/i.test(document.body.innerText)
  })
`;

export function waitForImageGeneration(timeoutMs = 180000, log = () => {}, minImageCount = 0) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const raw = executeInChrome(CHECK_JS);
      const state = JSON.parse(raw);
      if (state.rateLimited) return { ok: false, error: "RATE_LIMITED" };
      if (state.done && state.imageCount > minImageCount) return { ok: true };
      log(state.generating ? "generating..." : "waiting...");
    } catch (e) {
      log(`poll_error: ${e.message}`);
    }
    sleepSync(5000);
  }
  return { ok: false, error: "TIMEOUT" };
}

export function countGeneratedImages() {
  try {
    const raw = executeInChrome(`JSON.stringify({ count: (${GENERATED_IMG_JS}).length })`);
    return JSON.parse(raw).count;
  } catch {
    return 0;
  }
}

// ─── Download via Browser fetch ────────────────────────────────────────────

export function downloadImageViaBrowser(slug, n) {
  const filename = `${slug}_${String(n).padStart(2, "0")}.png`;

  // Step 1: open fullscreen dialog (click on the most recent image button)
  executeInChrome(`
    (function() {
      const btn = [...document.querySelectorAll('button')]
        .filter(b => b.querySelector('img[alt*="Generated image"]') || b.textContent.includes('已生成图片'))
        .at(-1);
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

// ─── Image Upload (img2img) ────────────────────────────────────────────────

export function uploadImageToChat(imagePath) {
  // Focus the chat input
  executeInChrome(`
    (function() {
      const el = document.querySelector(
        '#prompt-textarea, [data-testid="prompt-textarea"], div[contenteditable="true"]'
      );
      if (el) el.focus();
    })()
  `);
  sleepSync(300);

  // Copy image to clipboard and paste into ChatGPT
  if (!copyImageToClipboard(imagePath)) return { ok: false, error: "clipboard_copy_failed" };
  sleepSync(300);
  if (!pasteInChrome()) return { ok: false, error: "paste_failed" };
  sleepSync(2500);

  // Verify attachment appeared — any blob: image in the textarea area counts
  const result = executeInChrome(`
    JSON.stringify({
      ok: !!(
        document.querySelector('[data-testid*="file-attachment"]') ||
        document.querySelector('button[aria-label*="Remove"]') ||
        document.querySelector('[class*="attachment"]') ||
        document.querySelector('img[src^="blob:"]') ||
        [...document.querySelectorAll('[role="button"]')]
          .find(b => b.querySelector('img[src^="blob:"]')) ||
        document.querySelector('#prompt-textarea img') ||
        [...document.querySelectorAll('[contenteditable] img')].length > 0
      )
    })
  `);
  try {
    const { ok } = JSON.parse(result);
    // Treat as success even if we can't verify — paste was sent, continue
    return { ok: true, verified: ok ?? false };
  } catch {
    return { ok: true, verified: false, error: "verify_parse_failed" };
  }
}

// ─── Edit Mode (in-painting) ───────────────────────────────────────────────

export function clickEditOnImage(imageIndex = 0) {
  // Hover over the target image to make the 编辑 button visible
  executeInChrome(`
    (function() {
      const imgs = [...document.querySelectorAll('main img')]
        .filter(i => i.src && (
          i.src.includes('chatgpt.com/backend-api') ||
          i.src.includes('oaiusercontent.com') ||
          i.src.includes('estuary/content')
        ) && i.naturalWidth > 0);
      const img = imgs.at(${imageIndex});
      if (!img) return;
      [img, img.closest('button, [role="button"], figure, div')].filter(Boolean)
        .forEach(el => el.dispatchEvent(new MouseEvent('mouseover', { bubbles: true })));
    })()
  `);
  sleepSync(700);

  const result = executeInChrome(`
    (function() {
      const editBtns = [
        ...document.querySelectorAll('button[aria-label*="Edit"], button[aria-label*="编辑"]'),
        ...document.querySelectorAll('[data-testid*="edit-image"], [data-testid*="image-edit"]'),
        ...[...document.querySelectorAll('button')].filter(b =>
          b.textContent.trim() === '编辑' || b.textContent.trim() === 'Edit'
        )
      ];
      const btn = editBtns.at(${imageIndex});
      if (!btn) return 'no_edit_button';
      btn.click();
      return 'clicked';
    })()
  `);
  return { ok: result === 'clicked', error: result !== 'clicked' ? result : null };
}

export function waitForEditorCanvas(timeoutMs = 25000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const raw = executeInChrome(`JSON.stringify({
        editorDialog: !!document.querySelector('[role="dialog"]'),
        hasInput: !!(
          document.querySelector('[role="dialog"] [contenteditable]') ||
          document.querySelector('[role="dialog"] textarea') ||
          document.querySelector('[placeholder*="Describe"], [placeholder*="描述"]')
        ),
        hasCanvas: !!document.querySelector('[role="dialog"] canvas'),
        url: window.location.pathname
      })`);
      const s = JSON.parse(raw);
      if (s.editorDialog && s.hasInput) return { ok: true, found: s };
    } catch {}
    sleepSync(1000);
  }
  // Return partial info for debugging even on timeout
  try {
    const raw = executeInChrome(`JSON.stringify({
      allCanvases: document.querySelectorAll('canvas').length,
      allDialogs:  document.querySelectorAll('[role="dialog"]').length,
      url: window.location.pathname,
      bodyText: document.body.innerText.slice(0,200)
    })`);
    return { ok: false, error: 'canvas_not_found', debug: JSON.parse(raw) };
  } catch {
    return { ok: false, error: 'canvas_not_found' };
  }
}

export function drawMaskOnCanvas(maskRegion) {
  // maskRegion: [xFrac, yFrac, widthFrac, heightFrac] — fractions of canvas bounds
  const [xF, yF, wF, hF] = maskRegion;
  const result = executeInChrome(`
    (function() {
      const canvas =
        document.querySelector('canvas') ||
        document.querySelector('[data-testid*="canvas"]');
      if (!canvas) return 'no_canvas';

      const rect = canvas.getBoundingClientRect();
      const x0 = rect.left + rect.width  * ${xF};
      const y0 = rect.top  + rect.height * ${yF};
      const x1 = rect.left + rect.width  * (${xF} + ${wF});
      const y1 = rect.top  + rect.height * (${yF} + ${hF});

      function fire(type, x, y) {
        const opts = { clientX: x, clientY: y, bubbles: true, cancelable: true,
                       pressure: (type !== 'pointerup') ? 0.5 : 0, pointerType: 'mouse' };
        [canvas, document.elementFromPoint(x, y)].filter(Boolean)
          .forEach(el => el.dispatchEvent(new PointerEvent(type, opts)));
      }

      // Horizontal raster strokes across the mask rectangle
      const rowStep = 16;
      for (let cy = y0; cy <= y1; cy += rowStep) {
        fire('pointerdown', x0, cy);
        for (let cx = x0 + 4; cx <= x1; cx += 4) fire('pointermove', cx, cy);
        fire('pointerup', x1, cy);
      }
      return 'drawn';
    })()
  `);
  return { ok: result === 'drawn', error: result !== 'drawn' ? result : null };
}

export function submitEditPrompt(text) {
  // Focus and select-all in the editor input via JS.
  // ChatGPT's React blocks synthetic insertText/execCommand for text entry,
  // so we use clipboard paste (pbcopy → Cmd+V) instead.
  const focused = executeInChrome(`
    (function() {
      const el =
        document.querySelector('[role="dialog"] [contenteditable="true"]') ||
        document.querySelector('[role="dialog"] textarea') ||
        document.querySelector('[placeholder*="Describe"], [placeholder*="描述"]');
      if (!el) return 'no_input';
      el.focus();
      el.click();
      document.execCommand('selectAll', false, null);
      return 'focused';
    })()
  `);
  if (focused !== 'focused') return { ok: false, error: `focus_failed:${focused}` };
  sleepSync(200);

  if (!copyTextToClipboard(text)) return { ok: false, error: 'clipboard_failed' };
  sleepSync(100);

  pasteInChrome();
  sleepSync(400);

  // Press Enter to submit
  pressReturnInChrome();
  return { ok: true };
}

// ─── Slug utility ──────────────────────────────────────────────────────────

export function makeSlug(text) {
  return text.toLowerCase().slice(0, 40).replace(/\s+/g, "_").replace(/[^a-z0-9_]/g, "");
}
