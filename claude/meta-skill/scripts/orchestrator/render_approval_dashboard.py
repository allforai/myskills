#!/usr/bin/env python3
"""Render the game-design approval dashboard.

The dashboard is static HTML. It reads approval-records.json through fetch when
served from a local static server. Write-back is intentionally delegated to the
orchestrator/Playwright loop, which reads queued actions from the page and
applies them with apply_approval_action.py.
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
body {{ margin: 0; font: 14px/1.45 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #20242a; background: #f6f7f8; }}
header {{ position: sticky; top: 0; z-index: 2; display: flex; gap: 16px; align-items: center; justify-content: space-between; padding: 14px 20px; background: #fff; border-bottom: 1px solid #d9dde2; }}
h1 {{ margin: 0; font-size: 18px; }}
main {{ padding: 18px 20px 32px; }}
.summary {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px; }}
.pill {{ padding: 4px 9px; border: 1px solid #cbd2d9; border-radius: 999px; background: #fff; }}
.tree {{ display: flex; flex-direction: column; gap: 10px; }}
.branch {{ background: #fff; border: 1px solid #d9dde2; border-radius: 8px; }}
.branch summary {{ display: flex; gap: 10px; align-items: center; cursor: pointer; padding: 12px 14px; }}
.branch-title {{ font-weight: 700; }}
.branch-meta {{ color: #5b6470; }}
.branch-body {{ padding: 0 14px 14px; }}
.children {{ margin-left: 18px; padding-left: 14px; border-left: 2px solid #d9dde2; display: flex; flex-direction: column; gap: 10px; }}
.card {{ background: #fff; border: 1px solid #d9dde2; border-radius: 8px; padding: 14px; }}
.card h2 {{ margin: 0 0 6px; font-size: 16px; }}
.meta {{ color: #5b6470; margin-bottom: 10px; }}
.status {{ display: inline-block; padding: 2px 8px; border-radius: 999px; border: 1px solid #bcc5cf; background: #f9fafb; }}
.approved {{ border-color: #83b88b; background: #eef8f0; }}
.revision-requested {{ border-color: #d19a61; background: #fff5e8; }}
.in-review {{ border-color: #6f9ed8; background: #edf5ff; }}
label {{ display: block; margin-top: 10px; font-weight: 600; }}
textarea {{ box-sizing: border-box; width: 100%; min-height: 74px; resize: vertical; margin-top: 4px; padding: 8px; border: 1px solid #cbd2d9; border-radius: 6px; font: inherit; }}
.checks {{ margin: 10px 0; padding: 0; list-style: none; }}
.checks li {{ display: flex; gap: 7px; align-items: flex-start; margin: 6px 0; }}
.actions {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }}
button {{ border: 1px solid #aeb7c2; border-radius: 6px; background: #fff; padding: 7px 10px; cursor: pointer; }}
button.primary {{ color: #fff; background: #2367c9; border-color: #2367c9; }}
button.warn {{ color: #4a2600; background: #fff1db; border-color: #d19a61; }}
#pending {{ white-space: pre-wrap; margin: 0; color: #334155; }}
</style>
</head>
<body>
<header>
  <h1>游戏设计审批看板</h1>
  <div><button onclick="reloadRecords()">刷新</button></div>
</header>
<main>
  <section class="summary" id="summary"></section>
  <section class="card">
    <strong>待写回的 Playwright 操作</strong>
    <pre id="pending">无</pre>
  </section>
  <section class="tree" id="records"></section>
</main>
<script>
const EMBEDDED = {embedded};
const ACTION_KEY = "allforai.gameDesignApprovalAction";
let state = EMBEDDED;

async function loadApproval() {{
  try {{
    const response = await fetch("approval-records.json?ts=" + Date.now(), {{ cache: "no-store" }});
    if (response.ok) state.approval = await response.json();
  }} catch (error) {{
    // file:// fallback uses embedded bootstrap state.
  }}
}}

function queueAction(action) {{
  action.created_at = new Date().toISOString();
  localStorage.setItem(ACTION_KEY, JSON.stringify(action));
  renderPending();
}}

function getText(id) {{
  const node = document.getElementById(id);
  return node ? node.value : "";
}}

function approve(nodeId) {{
  queueAction({{
    action: "approve",
    node_id: nodeId,
    approved_by: "discipline_owner",
    reviewer_notes: getText("reviewer-" + nodeId),
    revision_notes: ""
  }});
}}

function requestRevision(nodeId) {{
  queueAction({{
    action: "request_revision",
    node_id: nodeId,
    reviewer_notes: getText("reviewer-" + nodeId),
    revision_notes: getText("revision-" + nodeId)
  }});
}}

function saveNotes(nodeId) {{
  queueAction({{
    action: "save_notes",
    node_id: nodeId,
    reviewer_notes: getText("reviewer-" + nodeId),
    revision_notes: getText("revision-" + nodeId)
  }});
}}

function renderPending() {{
  document.getElementById("pending").textContent = localStorage.getItem(ACTION_KEY) || "无";
}}

function render() {{
  const records = state.approval.records || [];
  const counts = records.reduce((acc, r) => {{
    acc[r.gate_status] = (acc[r.gate_status] || 0) + 1;
    return acc;
  }}, {{}});
  document.getElementById("summary").innerHTML = Object.keys(counts).sort()
    .map(k => `<span class="pill">${{k}}: ${{counts[k]}}</span>`).join("");
  document.getElementById("records").innerHTML = renderTree(records);
  renderPending();
}}

function renderTree(records) {{
  const nodes = records.map(record => ({{
    record,
    id: record.node_id,
    parent: findParent(record, records),
    children: []
  }}));
  const byId = new Map(nodes.map(node => [node.id, node]));
  const roots = [];
  for (const node of nodes) {{
    if (node.parent && byId.has(node.parent)) byId.get(node.parent).children.push(node);
    else roots.push(node);
  }}
  return roots.map(node => renderNode(node, 0)).join("");
}}

function findParent(record, records) {{
  const workflowNode = (state.workflow.nodes || []).find(node => node.node_id === record.node_id || node.id === record.node_id || node.node === record.node_id);
  const deps = workflowNode ? (workflowNode.hard_blocked_by || workflowNode.blocked_by || []) : [];
  const known = new Set(records.map(item => item.node_id));
  const parent = [...deps].reverse().find(dep => known.has(dep));
  if (parent) return parent;
  if (record.node_id.includes("-art-") || record.node_id === "art-qa") return "art-spec-design";
  if (record.node_id.includes("level") || record.node_id.includes("puzzle")) return "level-design";
  if (record.node_id.includes("combat") || record.node_id.includes("skill") || record.node_id.includes("balance")) return "combat-system-design";
  if (record.node_id.includes("narrative") || record.node_id.includes("dialogue") || record.node_id.includes("character-arc") || record.node_id.includes("world")) return "narrative-design";
  return null;
}}

function renderNode(node, depth) {{
  const record = node.record;
  const hasChildren = node.children.length > 0;
  const shouldOpen = depth === 0 || record.gate_status === "in-review" || record.gate_status === "revision-requested" || node.children.some(child => child.record.gate_status !== "approved");
  const card = renderCard(record);
  if (!hasChildren) return card;
  const childHtml = node.children.map(child => renderNode(child, depth + 1)).join("");
  return `<details class="branch" ${{shouldOpen ? "open" : ""}}>
    <summary>
      <span class="branch-title">${{escapeHtml(record.node_id)}}</span>
      <span class="status ${{escapeAttr(record.gate_status)}}">${{escapeHtml(record.gate_status)}}</span>
      <span class="branch-meta">${{node.children.length}} 个关联节点</span>
    </summary>
    <div class="branch-body">
      ${{card}}
      <div class="children">${{childHtml}}</div>
    </div>
  </details>`;
}}

function renderCard(record) {{
    const checklist = (record.review_checklist || []).map(item =>
      `<li><input type="checkbox" ${{item.checked ? "checked" : ""}} disabled><span>${{escapeHtml(item.item || item)}}</span></li>`
    ).join("");
    const output = record.html_output ? `<a href="${{escapeAttr(record.html_output)}}" target="_blank">打开节点输出</a>` : "";
    return `<article class="card" data-node-id="${{escapeAttr(record.node_id)}}">
      <h2>${{escapeHtml(record.node_id)}}</h2>
      <div class="meta"><span class="status ${{escapeAttr(record.gate_status)}}">${{escapeHtml(record.gate_status)}}</span>
      · 负责人：${{escapeHtml(record.discipline_owner || "")}} ${{output}}</div>
      <ul class="checks">${{checklist}}</ul>
      <label>评审备注<textarea id="reviewer-${{escapeAttr(record.node_id)}}">${{escapeHtml(record.reviewer_notes || "")}}</textarea></label>
      <label>修改意见<textarea id="revision-${{escapeAttr(record.node_id)}}">${{escapeHtml(record.revision_notes || "")}}</textarea></label>
      <div class="actions">
        <button onclick="saveNotes('${{escapeJs(record.node_id)}}')">保存备注</button>
        <button class="primary" onclick="approve('${{escapeJs(record.node_id)}}')">批准</button>
        <button class="warn" onclick="requestRevision('${{escapeJs(record.node_id)}}')">要求修改</button>
      </div>
    </article>`;
}}

async function reloadRecords() {{
  await loadApproval();
  render();
}}

function escapeHtml(value) {{
  return String(value).replace(/[&<>"']/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));
}}
function escapeAttr(value) {{ return escapeHtml(value); }}
function escapeJs(value) {{ return String(value).replace(/['\\\\]/g, "\\\\$&"); }}

window.__approvalDashboard = {{
  getPendingAction: () => localStorage.getItem(ACTION_KEY),
  clearPendingAction: () => {{ localStorage.removeItem(ACTION_KEY); renderPending(); }},
  reload: reloadRecords
}};

reloadRecords();
setInterval(reloadRecords, 3000);
</script>
</body>
</html>
""",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
