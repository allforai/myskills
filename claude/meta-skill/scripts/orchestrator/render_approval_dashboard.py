#!/usr/bin/env python3
"""Render the game-design approval dashboard.

Generates static HTML served by serve_approval.py. Approval buttons POST
directly to /api/action — no Playwright or localStorage required.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--approval", required=True)
    parser.add_argument("--workflow", required=False)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    approval_path = Path(args.approval)
    workflow_path = Path(args.workflow) if args.workflow else None
    output_path = Path(args.output)

    approval = read_json(approval_path)
    workflow = read_json(workflow_path) if workflow_path else {}
    embedded = json.dumps(
        {"approval": approval, "workflow": workflow},
        ensure_ascii=False,
        separators=(",", ":"),
    ).replace("</", "<\\/")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>游戏设计审批看板</title>
<style>
*,*::before,*::after{{box-sizing:border-box}}
html,body{{margin:0;height:100%;font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif;color:#1a202c;background:#f0f2f5}}
a{{color:#2b6cb0;text-decoration:none}}
a:hover{{text-decoration:underline}}

/* ── Header ── */
.hd{{position:sticky;top:0;z-index:10;background:#1a365d;color:#fff;padding:0 20px;display:flex;align-items:center;gap:16px;height:52px;box-shadow:0 2px 8px rgba(0,0,0,.25)}}
.hd h1{{margin:0;font-size:16px;font-weight:700;letter-spacing:.3px;flex:1;white-space:nowrap}}
.hd-chips{{display:flex;gap:8px;flex-wrap:wrap}}
.stat-chip{{padding:3px 10px;border-radius:999px;font-size:12px;font-weight:600;cursor:pointer;border:none;color:#fff;transition:opacity .15s;white-space:nowrap}}
.stat-chip:hover{{opacity:.85}}
.chip-revision{{background:#c53030}}
.chip-review{{background:#2b6cb0}}
.chip-pending{{background:#718096}}
.chip-approved{{background:#276749}}
.hd-refresh{{padding:5px 12px;border-radius:6px;border:1px solid rgba(255,255,255,.3);background:rgba(255,255,255,.1);color:#fff;cursor:pointer;font-size:13px;white-space:nowrap;flex-shrink:0}}
.hd-refresh:hover{{background:rgba(255,255,255,.2)}}
.pulse{{display:inline-block;width:7px;height:7px;border-radius:50%;background:#68d391;margin-right:6px;animation:pulse 2s ease-in-out infinite}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.4}}}}

/* ── Layout ── */
.layout{{display:flex;height:calc(100vh - 52px)}}
.sidebar{{width:220px;min-width:180px;flex-shrink:0;background:#fff;border-right:1px solid #e2e8f0;padding:12px 0;overflow-y:auto}}
.sidebar-section{{margin-bottom:4px}}
.sidebar-label{{padding:4px 16px;font-size:11px;font-weight:700;color:#a0aec0;text-transform:uppercase;letter-spacing:.6px}}
.sidebar-item{{display:flex;align-items:center;gap:8px;padding:7px 16px;cursor:pointer;border-left:3px solid transparent;transition:background .1s}}
.sidebar-item:hover{{background:#f7fafc}}
.sidebar-item.active{{background:#ebf8ff;border-left-color:#3182ce;color:#2b6cb0;font-weight:600}}
.sidebar-item.s-revision{{border-left-color:#fc8181}}
.sidebar-item.s-review{{border-left-color:#63b3ed}}
.sidebar-item.s-pending{{border-left-color:#cbd5e0}}
.sidebar-item.s-approved{{border-left-color:#68d391}}
.sidebar-dot{{width:8px;height:8px;border-radius:50%;flex-shrink:0}}
.dot-revision{{background:#e53e3e}}
.dot-review{{background:#3182ce}}
.dot-pending{{background:#a0aec0}}
.dot-approved{{background:#38a169}}
.sidebar-name{{font-size:13px;flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}

/* ── Main panel ── */
.main{{flex:1;padding:20px;overflow-y:auto;min-width:0;transition:flex .2s}}

/* ── Preview panel ── */
.preview-panel{{width:0;flex-shrink:0;background:#fff;border-left:1px solid #e2e8f0;overflow:hidden;transition:width .2s ease;display:flex;flex-direction:column}}
.preview-panel.open{{width:55%}}
.preview-hd{{padding:8px 12px;background:#f7fafc;border-bottom:1px solid #e2e8f0;display:flex;align-items:center;gap:8px;flex-shrink:0;min-height:38px}}
.preview-title{{flex:1;font-size:12px;color:#4a5568;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.preview-close{{padding:3px 10px;border-radius:5px;border:1px solid #e2e8f0;background:#fff;cursor:pointer;font-size:12px;color:#4a5568;flex-shrink:0}}
.preview-close:hover{{background:#fed7d7;border-color:#fc8181;color:#c53030}}
.preview-iframe{{flex:1;border:none;width:100%;display:block}}
.section-head{{display:flex;align-items:center;gap:10px;margin:0 0 14px;padding-bottom:10px;border-bottom:2px solid #e2e8f0}}
.section-head h2{{margin:0;font-size:15px;font-weight:700;color:#2d3748}}
.section-badge{{padding:2px 9px;border-radius:999px;font-size:12px;font-weight:600}}
.badge-revision{{background:#fed7d7;color:#c53030}}
.badge-review{{background:#bee3f8;color:#2b6cb0}}
.badge-pending{{background:#e2e8f0;color:#4a5568}}
.badge-approved{{background:#c6f6d5;color:#276749}}
.cards{{display:flex;flex-direction:column;gap:14px;margin-bottom:28px}}

/* ── Card ── */
.card{{background:#fff;border-radius:10px;border:1px solid #e2e8f0;overflow:hidden;transition:box-shadow .15s}}
.card:hover{{box-shadow:0 4px 12px rgba(0,0,0,.08)}}
.card-bar{{height:4px}}
.bar-revision{{background:#e53e3e}}
.bar-review{{background:#3182ce}}
.bar-pending{{background:#a0aec0}}
.bar-approved{{background:#38a169}}
.card-body{{padding:16px}}
.card-header{{display:flex;align-items:flex-start;gap:10px;margin-bottom:10px}}
.card-title{{font-size:15px;font-weight:700;color:#1a202c;flex:1}}
.status-badge{{padding:3px 10px;border-radius:999px;font-size:12px;font-weight:600;white-space:nowrap}}
.badge-s-revision{{background:#fed7d7;color:#9b2c2c}}
.badge-s-review{{background:#bee3f8;color:#2c5282}}
.badge-s-pending{{background:#e2e8f0;color:#4a5568}}
.badge-s-approved{{background:#c6f6d5;color:#22543d}}
.card-meta{{font-size:12px;color:#718096;margin-bottom:12px;display:flex;flex-wrap:wrap;gap:10px;align-items:center}}
.card-meta a{{font-size:12px}}

/* Checklist */
.checklist{{margin:0 0 12px;padding:10px 12px;list-style:none;background:#f7fafc;border-radius:6px}}
.checklist li{{display:flex;align-items:flex-start;gap:8px;font-size:13px;color:#4a5568;padding:3px 0}}
.checklist li::before{{content:"☐";color:#a0aec0;flex-shrink:0;margin-top:1px}}
.checklist li.done::before{{content:"☑";color:#38a169}}

/* Notes */
.notes-row{{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px}}
@media(max-width:600px){{.notes-row{{grid-template-columns:1fr}}}}
.note-block label{{display:block;font-size:12px;font-weight:600;color:#4a5568;margin-bottom:4px}}
.note-block textarea{{width:100%;min-height:70px;resize:vertical;padding:8px;border:1px solid #e2e8f0;border-radius:6px;font:inherit;font-size:13px;color:#2d3748;background:#f7fafc}}
.note-block textarea:focus{{outline:none;border-color:#90cdf4;background:#fff}}
.note-block.revision-notes textarea{{border-color:#fc8181;background:#fff5f5}}

/* Existing notes (read-only) */
.existing-notes{{margin-bottom:12px}}
.existing-notes .note-label{{font-size:12px;font-weight:600;color:#9b2c2c;margin-bottom:4px}}
.existing-notes .note-body{{background:#fff5f5;border:1px solid #fc8181;border-radius:6px;padding:8px 10px;font-size:13px;color:#c53030;white-space:pre-wrap}}

/* Actions */
.actions{{display:flex;flex-wrap:wrap;gap:8px}}
.btn{{padding:7px 14px;border-radius:6px;border:1px solid #e2e8f0;background:#fff;cursor:pointer;font-size:13px;font-weight:500;transition:all .15s}}
.btn:hover{{background:#f7fafc}}
.btn:disabled{{opacity:.5;cursor:default}}
.btn-approve{{background:#276749;border-color:#276749;color:#fff}}
.btn-approve:hover:not(:disabled){{background:#22543d}}
.btn-revision{{background:#c53030;border-color:#c53030;color:#fff}}
.btn-revision:hover:not(:disabled){{background:#9b2c2c}}
.btn-save{{background:#2b6cb0;border-color:#2b6cb0;color:#fff}}
.btn-save:hover:not(:disabled){{background:#2c5282}}

/* Toast */
.toast{{position:fixed;bottom:24px;right:24px;padding:12px 20px;border-radius:8px;background:#276749;color:#fff;font-size:14px;font-weight:600;opacity:0;transform:translateY(8px);transition:all .25s;z-index:200;pointer-events:none;box-shadow:0 4px 12px rgba(0,0,0,.2)}}
.toast.show{{opacity:1;transform:translateY(0)}}
.toast.error{{background:#c53030}}
</style>
</head>
<body>
<header class="hd">
  <h1><span class="pulse"></span>游戏设计审批看板</h1>
  <div class="hd-chips" id="hd-stats"></div>
  <button class="hd-refresh" onclick="reloadRecords()">刷新</button>
</header>
<div class="layout">
  <nav class="sidebar" id="sidebar"></nav>
  <main class="main" id="main"></main>
  <div class="preview-panel" id="preview-panel">
    <div class="preview-hd">
      <span class="preview-title" id="preview-title"></span>
      <button class="preview-close" onclick="closePreview()">✕ 关闭</button>
    </div>
    <iframe id="preview-iframe" class="preview-iframe" src="about:blank"></iframe>
  </div>
</div>
<div class="toast" id="toast"></div>
<script>
const EMBEDDED = {embedded};
let state = EMBEDDED;
let activeFilter = null;

const STATUS_ORDER = ["revision-requested","in-review","pending","approved"];
const STATUS_LABELS = {{"revision-requested":"要求修改","in-review":"审核中","pending":"待执行","approved":"已批准"}};
const STATUS_CHIP = {{"revision-requested":"chip-revision","in-review":"chip-review","pending":"chip-pending","approved":"chip-approved"}};
const STATUS_BADGE = {{"revision-requested":"badge-revision","in-review":"badge-review","pending":"badge-pending","approved":"badge-approved"}};
const STATUS_BADGE_S = {{"revision-requested":"badge-s-revision","in-review":"badge-s-review","pending":"badge-s-pending","approved":"badge-s-approved"}};
const STATUS_BAR = {{"revision-requested":"bar-revision","in-review":"bar-review","pending":"bar-pending","approved":"bar-approved"}};
const STATUS_DOT = {{"revision-requested":"dot-revision","in-review":"dot-review","pending":"dot-pending","approved":"dot-approved"}};
const STATUS_SIDEBAR = {{"revision-requested":"s-revision","in-review":"s-review","pending":"s-pending","approved":"s-approved"}};

async function loadApproval() {{
  try {{
    const r = await fetch("approval-records.json?ts="+Date.now(),{{cache:"no-store"}});
    if (r.ok) state.approval = await r.json();
  }} catch(e) {{}}
}}

function getNodeId(rec) {{ return rec.node_id || ""; }}

function htmlOutputFor(rec) {{
  if (rec.html_output) return rec.html_output;
  const nid = getNodeId(rec);
  const map = {{
    "core-loop-design":"core-loop.html","character-arc-design":"character-arc.html",
    "ftue-design":"ftue.html","monetization-design":"monetization.html",
    "retention-hook-design":"retention-hook.html","meta-game-design":"meta-game.html",
    "level-design":"level-design.html","puzzle-design":"puzzle-design.html",
    "progression-curve-design":"progression-curve.html","audio-design":"audio-design.html",
    "worldbuilding":"worldbuilding.html","art-direction":"art-direction.html",
    "art-spec-design":"art-spec-design.html","tile-art-gen":"tile-art-review.html",
    "character-art-gen":"character-art-review.html","environment-art-gen":"environment-art-review.html",
    "ui-art-gen":"ui-art-review.html","vfx-art-gen":"vfx-art-review.html",
    "art-qa":"art-qa-report.html","game-design-finalize":"game-design-dashboard.html"
  }};
  return map[nid] || null;
}}

function getText(id) {{ const el=document.getElementById(id); return el?el.value:""; }}

function setButtons(nid, disabled) {{
  ["approve-"+nid,"revision-btn-"+nid,"save-"+nid].forEach(id => {{
    const el = document.getElementById(id);
    if (el) el.disabled = disabled;
  }});
}}

async function submitAction(action) {{
  action.created_at = new Date().toISOString();
  const nid = action.node_id;
  setButtons(nid, true);
  try {{
    const r = await fetch("/api/action", {{
      method: "POST",
      headers: {{"Content-Type": "application/json"}},
      body: JSON.stringify(action)
    }});
    if (!r.ok) {{
      const err = await r.json().catch(() => ({{}}));
      throw new Error(err.error || r.statusText);
    }}
    showToast("✓ 操作已保存");
    await reloadRecords();
  }} catch(e) {{
    showToast("✗ " + e.message, true);
    setButtons(nid, false);
  }}
}}

function approve(nodeId) {{
  submitAction({{action:"approve",node_id:nodeId,approved_by:"discipline_owner",
    reviewer_notes:getText("reviewer-"+nodeId),revision_notes:""}});
}}

function requestRevision(nodeId) {{
  const notes = getText("revision-"+nodeId);
  if (!notes.trim()) {{ alert("请填写修改意见后再提交"); return; }}
  submitAction({{action:"request_revision",node_id:nodeId,
    reviewer_notes:getText("reviewer-"+nodeId),revision_notes:notes}});
}}

function saveNotes(nodeId) {{
  submitAction({{action:"save_notes",node_id:nodeId,
    reviewer_notes:getText("reviewer-"+nodeId),revision_notes:getText("revision-"+nodeId)}});
}}

function showToast(msg, isError) {{
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.className = "toast" + (isError ? " error" : "");
  requestAnimationFrame(() => {{ t.classList.add("show"); }});
  clearTimeout(t._timer);
  t._timer = setTimeout(() => t.classList.remove("show"), 2500);
}}

function filterBy(status) {{
  activeFilter = activeFilter === status ? null : status;
  render();
}}

function scrollTo(nodeId) {{
  const el = document.getElementById("card-"+nodeId);
  if (el) el.scrollIntoView({{behavior:"smooth",block:"start"}});
}}

function renderCard(rec) {{
  const nid = getNodeId(rec);
  const st = rec.gate_status || "pending";
  const outputHref = htmlOutputFor(rec);
  const outputLink = outputHref ? `<a href="javascript:void(0)" onclick="openPreview('${{escapeJs(outputHref)}}','${{escapeJs(nid)}}')">查看输出 ▶</a>` : "";
  const reviewers = (rec.discipline_reviewers||[]).join(", ");

  const checklist = (rec.review_checklist||[]).map(item => {{
    const text = typeof item==="string" ? item : (item.item||"");
    const checked = typeof item==="object" && item.checked;
    return `<li class="${{checked?"done":""}}">${{escapeHtml(text)}}</li>`;
  }}).join("");
  const checklistHtml = checklist ? `<ul class="checklist">${{checklist}}</ul>` : "";

  const existingRevision = rec.revision_notes ?
    `<div class="existing-notes"><div class="note-label">⚠ 待修改意见</div><div class="note-body">${{escapeHtml(rec.revision_notes)}}</div></div>` : "";

  const existingReviewer = rec.reviewer_notes ?
    `<div class="existing-notes" style="margin-bottom:8px"><div class="note-label" style="color:#2b6cb0">📝 评审备注</div><div class="note-body" style="border-color:#90cdf4;background:#ebf8ff;color:#2c5282">${{escapeHtml(rec.reviewer_notes)}}</div></div>` : "";

  const isApproved = st === "approved";
  return `<div class="card" id="card-${{escapeAttr(nid)}}">
  <div class="card-bar ${{STATUS_BAR[st]||"bar-pending"}}"></div>
  <div class="card-body">
    <div class="card-header">
      <div class="card-title">${{escapeHtml(nid)}}</div>
      <span class="status-badge ${{STATUS_BADGE_S[st]||"badge-s-pending"}}">${{STATUS_LABELS[st]||st}}</span>
    </div>
    <div class="card-meta">
      <span>负责人：<strong>${{escapeHtml(rec.discipline_owner||"")}}</strong></span>
      ${{reviewers ? `<span>评审员：${{escapeHtml(reviewers)}}</span>` : ""}}
      ${{rec.approved_by&&rec.approved_by.length ? `<span style="color:#276749">✓ 批准：${{escapeHtml((rec.approved_by||[]).join(", "))}}</span>` : ""}}
      ${{outputLink}}
    </div>
    ${{checklistHtml}}
    ${{existingRevision}}${{existingReviewer}}
    ${{isApproved ? "" : `
    <div class="notes-row">
      <div class="note-block">
        <label>评审备注</label>
        <textarea id="reviewer-${{escapeAttr(nid)}}" placeholder="评审员备注（不影响审批状态）">${{escapeHtml(rec.reviewer_notes||"")}}</textarea>
      </div>
      <div class="note-block revision-notes">
        <label>修改意见</label>
        <textarea id="revision-${{escapeAttr(nid)}}" placeholder="填写修改意见后点击&ldquo;要求修改&rdquo;">${{escapeHtml(rec.revision_notes||"")}}</textarea>
      </div>
    </div>
    <div class="actions">
      <button id="approve-${{escapeAttr(nid)}}" class="btn btn-approve" onclick="approve('${{escapeJs(nid)}}')">✓ 批准</button>
      <button id="revision-btn-${{escapeAttr(nid)}}" class="btn btn-revision" onclick="requestRevision('${{escapeJs(nid)}}')">↩ 要求修改</button>
      <button id="save-${{escapeAttr(nid)}}" class="btn btn-save" onclick="saveNotes('${{escapeJs(nid)}}')">💾 保存备注</button>
    </div>`}}
  </div>
</div>`;
}}

function render() {{
  const records = state.approval.records || [];
  const grouped = {{}};
  for (const st of STATUS_ORDER) grouped[st] = [];
  for (const rec of records) {{
    const st = rec.gate_status || "pending";
    if (!grouped[st]) grouped[st] = [];
    grouped[st].push(rec);
  }}

  // Header chips
  const statsHtml = STATUS_ORDER
    .filter(st => grouped[st].length)
    .map(st => `<button class="stat-chip ${{STATUS_CHIP[st]}}" onclick="filterBy('${{st}}')">
      ${{STATUS_LABELS[st]}} ${{grouped[st].length}}
    </button>`).join("");
  document.getElementById("hd-stats").innerHTML = statsHtml;

  // Sidebar
  let sidebarHtml = "";
  for (const st of STATUS_ORDER) {{
    const items = grouped[st];
    if (!items.length) continue;
    sidebarHtml += `<div class="sidebar-section">
      <div class="sidebar-label">${{STATUS_LABELS[st]}}</div>`;
    for (const rec of items) {{
      const nid = getNodeId(rec);
      sidebarHtml += `<div class="sidebar-item ${{STATUS_SIDEBAR[st]||""}}" onclick="scrollTo('${{escapeJs(nid)}}')" title="${{escapeAttr(nid)}}">
        <span class="sidebar-dot ${{STATUS_DOT[st]||"dot-pending"}}"></span>
        <span class="sidebar-name">${{escapeHtml(nid)}}</span>
      </div>`;
    }}
    sidebarHtml += "</div>";
  }}
  document.getElementById("sidebar").innerHTML = sidebarHtml;

  // Main content
  const toShow = activeFilter
    ? STATUS_ORDER.filter(st => st === activeFilter)
    : STATUS_ORDER.filter(st => st !== "approved");

  let mainHtml = "";
  for (const st of toShow) {{
    const items = grouped[st];
    if (!items.length) continue;
    mainHtml += `<div class="section-head">
      <h2>${{{{"revision-requested":"⚠ 需要修改","in-review":"🔍 审核中","pending":"⏳ 待执行","approved":"✅ 已批准"}}[st]||st}}</h2>
      <span class="section-badge ${{STATUS_BADGE[st]||"badge-pending"}}">${{items.length}} 个节点</span>
    </div>
    <div class="cards">${{items.map(renderCard).join("")}}</div>`;
  }}

  if (!activeFilter && grouped["approved"].length) {{
    mainHtml += `<details style="margin-bottom:20px"><summary style="cursor:pointer;font-weight:600;color:#276749;padding:8px 0">✅ 已批准节点 (${{grouped["approved"].length}})</summary>
      <div class="cards" style="margin-top:10px">${{grouped["approved"].map(renderCard).join("")}}</div>
    </details>`;
  }}

  document.getElementById("main").innerHTML = mainHtml;
}}

async function reloadRecords() {{
  await loadApproval();
  const focused = document.activeElement;
  if (focused && (focused.tagName === "TEXTAREA" || focused.tagName === "INPUT")) {{
    return;
  }}
  render();
}}

function openPreview(href, nodeId) {{
  const panel = document.getElementById("preview-panel");
  const iframe = document.getElementById("preview-iframe");
  const title = document.getElementById("preview-title");
  title.textContent = href;
  iframe.src = href + "?ts=" + Date.now();
  panel.classList.add("open");
  if (nodeId) {{
    setTimeout(() => {{
      const el = document.getElementById("card-" + nodeId);
      if (el) el.scrollIntoView({{behavior:"smooth", block:"nearest"}});
    }}, 50);
  }}
}}

function closePreview() {{
  const panel = document.getElementById("preview-panel");
  const iframe = document.getElementById("preview-iframe");
  panel.classList.remove("open");
  setTimeout(() => {{ iframe.src = "about:blank"; }}, 200);
}}

function escapeHtml(v) {{ return String(v).replace(/[&<>"']/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c])); }}
function escapeAttr(v) {{ return escapeHtml(v); }}
function escapeJs(v) {{ return String(v).replace(/['\\\\]/g,"\\\\$&"); }}

render();
setInterval(reloadRecords, 15000);
</script>
</body>
</html>
""",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
