#!/usr/bin/env python3
"""Mind Map Review Server — interactive mind map for reviewing product artifacts.

Transforms product-concept.json or product-map data into an interactive mind map.
Users can expand/collapse branches, click nodes to add comments, and approve or
flag nodes for revision.

Supports two data sources:
  --source concept     → reads product-concept.json
  --source product-map → reads role-profiles.json + task-inventory.json + business-flows.json

Output: .allforai/{source}-review/review-feedback.json

Usage:
    python3 mindmap_review_server.py <BASE_PATH> --source concept [--port 18900]
    python3 mindmap_review_server.py <BASE_PATH> --source product-map [--port 18901]
"""

import http.server
import json
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C

# ── Setup ─────────────────────────────────────────────────────────────────────
BASE, args = C.parse_args()
SOURCE = args.get("source", "concept")
DEFAULT_PORTS = {"concept": 18900, "product-map": 18901}
PORT = int(args.get("port", str(DEFAULT_PORTS.get(SOURCE, 3000))))
HOST = args.get("host", "localhost")
NO_OPEN = args.get("no-open", "false").lower() in ("true", "1", "yes")

REVIEW_DIR = os.path.join(BASE, f"{SOURCE}-review")
C.ensure_dir(REVIEW_DIR)
FEEDBACK_PATH = os.path.join(REVIEW_DIR, "review-feedback.json")

TITLES = {"concept": "Product Concept", "product-map": "Product Map"}

# ── Data loaders → tree ──────────────────────────────────────────────────────

def _node(nid, label, ntype="default", detail="", children=None, tags=None):
    n = {"id": nid, "label": label, "type": ntype}
    if detail:
        n["detail"] = detail
    if children:
        n["children"] = children
    if tags:
        n["tags"] = tags
    return n


def load_concept_tree():
    """Transform product-concept.json into a mind map tree."""
    data = C.load_json(os.path.join(BASE, "product-concept/product-concept.json"))
    if not data:
        return _node("root", "No concept data", "error")

    mission = data.get("mission", data.get("problem_domain", "Product"))
    children = []

    # Problem domain
    pd = data.get("problem_domain", "")
    if pd:
        children.append(_node("problem", "Problem Domain", "group", pd))

    # Roles — handle both flat list [{role_id, role_name}] and grouped dict {"consumer": [...]}
    raw_roles = data.get("roles", [])
    roles = []
    if isinstance(raw_roles, list):
        roles = raw_roles
    elif isinstance(raw_roles, dict):
        # Grouped by role_type: {"consumer": [...], "producer": [...]}
        for group_type, group_list in raw_roles.items():
            if isinstance(group_list, list):
                for r in group_list:
                    if isinstance(r, dict):
                        r.setdefault("role_type", group_type)
                        roles.append(r)
    if roles:
        role_nodes = []
        for r in roles:
            rid = r.get("role_id", r.get("id", ""))
            rname = r.get("role_name", r.get("name", rid))
            role_detail = r.get("description", "")
            role_children = []
            if r.get("role_type"):
                role_children.append(_node(f"{rid}-type", f"Type: {r['role_type']}", "info"))
            if r.get("impl_group"):
                role_children.append(_node(f"{rid}-impl", f"Impl: {r['impl_group']}", "info"))
            if r.get("jobs"):
                for j, job in enumerate(r["jobs"][:5]):
                    jtext = job.get("description", str(job)) if isinstance(job, dict) else str(job)
                    role_children.append(_node(f"{rid}-job-{j}", jtext, "info"))
            role_nodes.append(_node(rid, rname, "role", role_detail, role_children))
        children.append(_node("roles", f"Target Users ({len(roles)})", "group", children=role_nodes))

    # Business model
    bm = data.get("business_model", {})
    if bm:
        bm_children = []
        if bm.get("revenue_model"):
            bm_children.append(_node("bm-rev", f"Revenue: {bm['revenue_model']}", "info"))
        if bm.get("key_metrics"):
            for i, m in enumerate(bm["key_metrics"][:5]):
                bm_children.append(_node(f"bm-metric-{i}", str(m), "metric"))
        children.append(_node("business-model", "Business Model", "group", children=bm_children))

    # Mechanisms — handle both list [{id, module, chosen}] and dict {"key": "value"}
    raw_mechs = data.get("mechanisms", data.get("product_mechanisms", []))
    mechs = []
    if isinstance(raw_mechs, list):
        mechs = raw_mechs
    elif isinstance(raw_mechs, dict):
        # Dict format: {"key": "value"} or {"key": {details}}
        for k, v in raw_mechs.items():
            if isinstance(v, dict):
                v.setdefault("id", k)
                mechs.append(v)
            else:
                mechs.append({"id": k, "module": k, "chosen": str(v)})
    if mechs:
        mech_nodes = []
        for i, m in enumerate(mechs):
            mid = m.get("id", f"mec-{i}")
            mname = m.get("name", m.get("module", m.get("decision_point", mid)))
            mdesc = m.get("description", m.get("chosen", ""))
            mech_nodes.append(_node(mid, mname, "mechanism", mdesc))
        children.append(_node("mechanisms", f"Mechanisms ({len(mechs)})", "group", children=mech_nodes))

    # Innovation / adversarial concepts
    concepts = data.get("innovation_concepts", data.get("adversarial_concepts", []))
    if concepts:
        concept_nodes = []
        for i, c in enumerate(concepts):
            cid = c.get("id", "") or f"concept-{i}"
            tags = []
            if c.get("protection_level"):
                tags.append(c["protection_level"])
            if c.get("innovation_score"):
                tags.append(f"innovation:{c['innovation_score']}")
            concept_nodes.append(_node(cid, c.get("name", cid), "concept", c.get("description", ""), tags=tags))
        children.append(_node("concepts", f"Innovation Concepts ({len(concepts)})", "group", children=concept_nodes))

    # Pipeline preferences
    prefs = data.get("pipeline_preferences", {})
    if prefs:
        pref_children = []
        for k, v in prefs.items():
            if v and v != "undecided":
                pref_children.append(_node(f"pref-{k}", f"{k}: {v}", "config"))
        if pref_children:
            children.append(_node("prefs", "Pipeline Preferences", "group", children=pref_children))

    return _node("root", mission, "root", children=children)


def load_product_map_tree():
    """Transform product-map data into a mind map tree."""
    roles_data = C.load_json(os.path.join(BASE, "product-map/role-profiles.json"))
    inv_data = C.load_json(os.path.join(BASE, "product-map/task-inventory.json"))
    flows_data = C.load_json(os.path.join(BASE, "product-map/business-flows.json"))
    pm_data = C.load_json(os.path.join(BASE, "product-map/product-map.json"))

    if not inv_data:
        return _node("root", "No product-map data", "error")

    project_name = ""
    if pm_data:
        project_name = pm_data.get("project_name", "")
    if not project_name:
        concept = C.load_product_concept(BASE)
        project_name = concept.get("mission", "Product") if concept else "Product"

    roles = roles_data.get("roles", []) if roles_data else []
    tasks = inv_data.get("tasks", [])
    flows = flows_data.get("flows", []) if flows_data else []

    role_map = {r["id"]: r for r in roles}
    tasks_by_role = {}
    for t in tasks:
        tasks_by_role.setdefault(t.get("owner_role", ""), []).append(t)

    children = []

    # Roles + tasks
    for r in roles:
        rid = r["id"]
        rname = r.get("name", rid)
        rtasks = tasks_by_role.get(rid, [])

        core_tasks = [t for t in rtasks if t.get("category") == "core"]
        basic_tasks = [t for t in rtasks if t.get("category") != "core"]

        def _task_node(t):
            tid = t["id"]
            tname = t.get("name", t.get("task_name", tid))
            tags = []
            freq = t.get("frequency", "")
            if freq:
                tags.append(freq)
            risk = t.get("risk_level", "")
            if risk and risk != "low":
                tags.append(f"risk:{risk}")
            detail = t.get("value", "")
            return _node(tid, tname, "task", detail, tags=tags)

        role_children = []
        if core_tasks:
            core_nodes = [_task_node(t) for t in core_tasks]
            role_children.append(_node(f"{rid}-core", f"Core Tasks ({len(core_tasks)})", "task-group", children=core_nodes))
        if basic_tasks:
            basic_nodes = [_task_node(t) for t in basic_tasks]
            role_children.append(_node(f"{rid}-basic", f"Basic Tasks ({len(basic_tasks)})", "task-group", children=basic_nodes))

        at = r.get("audience_type", "")
        tags = [at] if at else []
        children.append(_node(rid, rname, "role", r.get("description", ""), role_children, tags))

    # Business flows
    if flows:
        flow_nodes = []
        for f in flows:
            fid = f["id"]
            fname = f.get("name", fid)
            nodes = f.get("nodes", [])
            step_nodes = []
            for n in nodes[:8]:
                task_ref = n.get("task_ref", "")
                role = n.get("role", "")
                gap = n.get("gap_type")
                tags = [f"@{role}"] if role else []
                if gap:
                    tags.append(f"GAP:{gap}")
                step_nodes.append(_node(f"{fid}-{n.get('seq', 0)}", task_ref, "flow-step", tags=tags))
            flow_nodes.append(_node(fid, f"{fname} ({len(nodes)} steps)", "flow", f.get("description", ""), step_nodes))
        children.append(_node("flows", f"Business Flows ({len(flows)})", "group", children=flow_nodes))

    return _node("root", project_name, "root", children=children)


def load_tree():
    if SOURCE == "concept":
        return load_concept_tree()
    elif SOURCE == "product-map":
        return load_product_map_tree()
    else:
        return _node("root", f"Unknown source: {SOURCE}", "error")


def collect_all_node_ids(tree, ids=None):
    """Collect all node IDs from tree."""
    if ids is None:
        ids = []
    ids.append(tree["id"])
    for child in tree.get("children", []):
        collect_all_node_ids(child, ids)
    return ids


# ── Feedback ─────────────────────────────────────────────────────────────────

def load_feedback():
    fb = C.load_json(FEEDBACK_PATH)
    if fb:
        return fb
    return {"round": 1, "submitted_at": None, "source": SOURCE, "nodes": {}}


def save_feedback(fb):
    C.write_json(FEEDBACK_PATH, fb)


# ── HTML rendering — XMind-style radial mind map ─────────────────────────────

def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;")


def render_page(tree, feedback):
    """Render XMind-style mind map with radial layout, SVG curves, zoom/pan."""
    title = TITLES.get(SOURCE, SOURCE)
    all_ids = collect_all_node_ids(tree)
    total = len(all_ids)
    fb_nodes = feedback.get("nodes", {})
    reviewed = sum(1 for nid in all_ids if fb_nodes.get(nid, {}).get("status") in ("approved", "revision"))
    tree_json = json.dumps(tree, ensure_ascii=False)
    feedback_json = json.dumps(fb_nodes, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="zh"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_esc(title)} Review</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,system-ui,'Segoe UI',sans-serif;background:#f8fafc;overflow:hidden;height:100vh}}
/* ── Header ── */
.header{{background:#fff;border-bottom:1px solid #e2e8f0;padding:12px 24px;display:flex;align-items:center;gap:20px;z-index:30;position:relative}}
.header h1{{font-size:17px;font-weight:600;color:#1e293b;white-space:nowrap}}
.header-meta{{font-size:12px;color:#64748b}}
.progress{{width:120px;height:4px;background:#e2e8f0;border-radius:2px;overflow:hidden}}
.progress-bar{{height:100%;background:#10b981;border-radius:2px;transition:width .3s}}
.toolbar{{display:flex;gap:6px;margin-left:auto}}
.toolbar button{{padding:5px 12px;border-radius:6px;border:1px solid #e2e8f0;background:#fff;cursor:pointer;font-size:12px;color:#475569}}
.toolbar button:hover{{background:#f1f5f9}}
.toolbar button.primary{{background:#334155;color:#fff;border-color:#334155}}
.toolbar button.primary:hover{{background:#1e293b}}
.toolbar button.primary:disabled{{background:#94a3b8;cursor:not-allowed}}
.zoom-info{{font-size:11px;color:#94a3b8;min-width:40px;text-align:center}}
/* ── Canvas ── */
.canvas-wrap{{position:relative;width:100%;height:calc(100vh - 52px);overflow:hidden;cursor:grab}}
.canvas-wrap.dragging{{cursor:grabbing}}
.canvas{{position:absolute;transform-origin:0 0}}
svg.lines{{position:absolute;top:0;left:0;overflow:visible;pointer-events:none}}
/* ── Nodes ── */
.mm-node{{position:absolute;white-space:nowrap;cursor:pointer;transition:box-shadow .15s,border-color .15s}}
.mm-node .label{{display:inline-flex;align-items:center;gap:5px;padding:6px 14px;border-radius:20px;font-size:13px;font-weight:500;border:2px solid transparent;background:#fff;box-shadow:0 1px 4px rgba(0,0,0,.08);user-select:none;position:relative}}
.mm-node .label:hover{{box-shadow:0 2px 12px rgba(0,0,0,.12)}}
.mm-node.active .label{{border-color:#3b82f6;box-shadow:0 0 0 3px rgba(59,130,246,.15)}}
.mm-node .tags{{display:inline-flex;gap:3px;margin-left:2px}}
.mm-node .tag{{font-size:9px;padding:1px 5px;border-radius:3px;font-weight:600;line-height:1.4}}
.mm-node .badge{{position:absolute;top:-6px;right:-6px;min-width:16px;height:16px;border-radius:8px;font-size:9px;font-weight:700;display:flex;align-items:center;justify-content:center;padding:0 4px}}
.mm-node .badge.comments{{background:#fbbf24;color:#92400e}}
.mm-node .badge.approved{{background:#34d399;color:#065f46}}
.mm-node .badge.revision{{background:#fbbf24;color:#92400e}}
/* Node type colors */
.mm-node[data-type="root"] .label{{background:linear-gradient(135deg,#6366f1,#8b5cf6);color:#fff;font-size:16px;font-weight:700;padding:12px 28px;border-radius:28px;box-shadow:0 4px 20px rgba(99,102,241,.3)}}
.mm-node[data-type="group"] .label{{background:#f1f5f9;color:#334155;font-weight:600;border-color:#cbd5e1}}
.mm-node[data-type="role"] .label{{background:#f5f3ff;color:#6d28d9;border-color:#c4b5fd}}
.mm-node[data-type="task"] .label{{background:#fff;color:#334155;font-weight:400}}
.mm-node[data-type="task-group"] .label{{background:#faf5ff;color:#7c3aed;font-weight:600;font-size:12px;border-color:#ddd6fe}}
.mm-node[data-type="flow"] .label{{background:#ecfeff;color:#0e7490;border-color:#a5f3fc}}
.mm-node[data-type="flow-step"] .label{{background:#f0fdfa;color:#115e59;font-weight:400;font-size:12px}}
.mm-node[data-type="concept"] .label{{background:#fdf4ff;color:#a21caf;border-color:#f0abfc}}
.mm-node[data-type="mechanism"] .label{{background:#ecfdf5;color:#047857;border-color:#6ee7b7}}
.mm-node[data-type="info"] .label,.mm-node[data-type="config"] .label{{background:#f8fafc;color:#64748b;font-size:12px;font-weight:400}}
.mm-node[data-type="error"] .label{{background:#fef2f2;color:#dc2626;border-color:#fca5a5}}
.mm-node[data-type="metric"] .label{{background:#eff6ff;color:#1d4ed8;font-size:12px}}
/* Collapse indicator */
.mm-node .collapse-dot{{width:18px;height:18px;border-radius:50%;background:#e2e8f0;color:#64748b;font-size:10px;display:flex;align-items:center;justify-content:center;border:1px solid #cbd5e1;cursor:pointer;position:absolute}}
/* Tags */
.tag-高,.tag-high{{background:#dcfce7;color:#15803d}}
.tag-中,.tag-medium{{background:#fef3c7;color:#b45309}}
.tag-低,.tag-low{{background:#f1f5f9;color:#64748b}}
.tag-risk{{background:#fef2f2;color:#dc2626}}
.tag-GAP{{background:#fef2f2;color:#dc2626;font-weight:700}}
.tag-consumer{{background:#e0f2fe;color:#0369a1}}
.tag-professional{{background:#f3e8ff;color:#7c3aed}}
.tag-innovation{{background:#fce7f3;color:#be185d}}
/* ── Comment panel ── */
.comment-panel{{position:fixed;right:0;top:52px;width:380px;height:calc(100vh - 52px);background:#fff;border-left:1px solid #e2e8f0;box-shadow:-4px 0 20px rgba(0,0,0,.06);z-index:50;transform:translateX(100%);transition:transform .25s ease;display:flex;flex-direction:column}}
.comment-panel.open{{transform:translateX(0)}}
.cp-header{{padding:16px 20px;border-bottom:1px solid #e2e8f0}}
.cp-header h3{{font-size:15px;color:#1e293b;margin-bottom:2px}}
.cp-header .cp-detail{{font-size:12px;color:#64748b}}
.cp-close{{position:absolute;right:16px;top:14px;background:none;border:none;font-size:20px;color:#94a3b8;cursor:pointer}}
.cp-close:hover{{color:#334155}}
.cp-body{{flex:1;overflow-y:auto;padding:16px 20px}}
.status-toggle{{display:flex;gap:8px;margin-bottom:16px}}
.status-btn{{flex:1;padding:10px;border:2px solid #e2e8f0;border-radius:8px;background:#fff;cursor:pointer;font-size:13px;text-align:center;transition:all .15s}}
.status-btn.approved.selected{{border-color:#10b981;background:#dcfce7;color:#065f46}}
.status-btn.revision.selected{{border-color:#f59e0b;background:#fef3c7;color:#92400e}}
.cp-body textarea{{width:100%;border:1px solid #e2e8f0;border-radius:6px;padding:10px;font-size:13px;resize:vertical;min-height:70px;font-family:inherit;margin-bottom:6px}}
.cp-body select{{width:100%;border:1px solid #e2e8f0;border-radius:6px;padding:7px;font-size:12px;margin-bottom:12px;background:#fff}}
.cp-body .add-btn{{width:100%;padding:8px;border-radius:6px;background:#334155;color:#fff;border:none;font-size:13px;cursor:pointer;margin-bottom:16px}}
.cp-body .add-btn:hover{{background:#1e293b}}
.comment-list .comment-item{{background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;padding:10px;margin-bottom:6px;font-size:12px;position:relative}}
.comment-item .cm{{font-size:10px;color:#94a3b8;margin-bottom:3px}}
.comment-item .cdel{{position:absolute;right:8px;top:8px;color:#cbd5e1;cursor:pointer;font-size:14px}}
.comment-item .cdel:hover{{color:#ef4444}}
</style></head><body>
<div class="header">
  <h1>{_esc(title)} Review</h1>
  <div class="header-meta">Round {feedback.get('round',1)} &middot; {reviewed}/{total} reviewed</div>
  <div class="progress"><div class="progress-bar" style="width:{reviewed/total*100 if total else 0:.0f}%"></div></div>
  <div class="toolbar">
    <button onclick="setDepth(1)">Level 1</button>
    <button onclick="setDepth(2)">Level 2</button>
    <button onclick="setDepth(3)">All</button>
    <button onclick="fitView()">Fit</button>
    <span class="zoom-info" id="zoomInfo">100%</span>
    <button class="primary" onclick="submitAll()" id="submitBtn">Submit</button>
  </div>
</div>
<div class="canvas-wrap" id="canvasWrap">
  <div class="canvas" id="canvas">
    <svg class="lines" id="svgLines"></svg>
  </div>
</div>
<!-- Comment side panel -->
<div class="comment-panel" id="commentPanel">
  <div class="cp-header">
    <h3 id="cpTitle">Node</h3>
    <div class="cp-detail" id="cpDetail"></div>
    <button class="cp-close" onclick="closePanel()">&times;</button>
  </div>
  <div class="cp-body">
    <div class="status-toggle">
      <button class="status-btn approved" id="btnApproved" onclick="setNodeStatus('approved')">&#10003; Approved</button>
      <button class="status-btn revision" id="btnRevision" onclick="setNodeStatus('revision')">&#9998; Revision</button>
    </div>
    <textarea id="commentText" placeholder="Write a comment..."></textarea>
    <select id="commentCategory">
      <option value="general">General</option>
      <option value="product-map">Feature / Task</option>
      <option value="concept">Concept</option>
      <option value="flow">Flow</option>
    </select>
    <button class="add-btn" onclick="saveComment()">Add Comment</button>
    <div class="comment-list" id="commentList"></div>
  </div>
</div>
<script>
const TREE={tree_json};
let feedback={feedback_json};
let currentNodeId=null;
let maxDepth=2;

// ── Branch colors (XMind style — each top-level branch gets a color) ──
const BRANCH_COLORS=[
  '#6366f1','#ec4899','#f59e0b','#10b981','#3b82f6','#8b5cf6','#ef4444','#14b8a6','#f97316','#06b6d4'
];

// ── Layout config ──
const NODE_H=36, NODE_GAP_Y=6, LEVEL_GAP_X=180, ROOT_PAD=60;

// ── Layout engine — horizontal tree, root center, children L/R ──
const nodePositions={{}};  // id → {{x,y,w,h,side,branchColor,depth,collapsed,node}}
const nodeElements={{}};   // id → DOM element

function measureText(text,fontSize){{
  const c=document.createElement('canvas').getContext('2d');
  c.font=`${{fontSize}}px -apple-system,system-ui,sans-serif`;
  return c.measureText(text).width;
}}

function nodeWidth(node){{
  const depth=node._depth||0;
  const fs=depth===0?16:depth===1?13:12;
  const tags=(node.tags||[]);
  let tw=measureText(node.label,fs)+32;
  if(tags.length)tw+=tags.reduce((a,t)=>a+measureText(t,9)+14,8);
  return Math.max(tw,60);
}}

function countLeaves(node,depth){{
  if(depth>=maxDepth||!node.children||!node.children.length)return 1;
  return node.children.reduce((s,c)=>s+countLeaves(c,depth+1),0);
}}

function layoutSubtree(node,x,yStart,side,branchColor,depth){{
  node._depth=depth;
  const w=nodeWidth(node);
  const h=NODE_H;
  const children=(depth<maxDepth&&node.children)?node.children:[];
  const hasHiddenChildren=(!!(node.children&&node.children.length))&&(depth>=maxDepth);

  if(!children.length){{
    const y=yStart;
    nodePositions[node.id]={{x,y,w,h,side,branchColor,depth,collapsed:hasHiddenChildren,node}};
    return y+h+NODE_GAP_Y;
  }}

  let cy=yStart;
  for(const child of children){{
    const childX=side==='right'?x+w+LEVEL_GAP_X:x-nodeWidth(child)-LEVEL_GAP_X;
    cy=layoutSubtree(child,childX,cy,side,branchColor,depth+1);
  }}

  const firstChild=nodePositions[children[0].id];
  const lastChild=nodePositions[children[children.length-1].id];
  const centerY=(firstChild.y+lastChild.y)/2;

  nodePositions[node.id]={{x,y:centerY,w,h,side,branchColor,depth,collapsed:hasHiddenChildren,node}};
  return cy;
}}

function layoutTree(){{
  // Clear
  for(const k in nodePositions)delete nodePositions[k];
  TREE._depth=0;

  const children=TREE.children||[];
  if(!children.length){{
    nodePositions[TREE.id]={{x:0,y:0,w:nodeWidth(TREE),h:NODE_H,side:'right',branchColor:BRANCH_COLORS[0],depth:0,collapsed:false,node:TREE}};
    return;
  }}

  // Split children: first half right, second half left
  const half=Math.ceil(children.length/2);
  const rightChildren=children.slice(0,half);
  const leftChildren=children.slice(half);

  const rootW=nodeWidth(TREE);

  // Layout right side
  let rightY=0;
  rightChildren.forEach((child,i)=>{{
    const bc=BRANCH_COLORS[i%BRANCH_COLORS.length];
    const childX=rootW/2+ROOT_PAD;
    rightY=layoutSubtree(child,childX,rightY,'right',bc,1);
  }});

  // Layout left side
  let leftY=0;
  leftChildren.forEach((child,i)=>{{
    const bc=BRANCH_COLORS[(half+i)%BRANCH_COLORS.length];
    const childW=nodeWidth(child);
    const childX=-rootW/2-ROOT_PAD-childW;
    leftY=layoutSubtree(child,childX,leftY,'left',bc,1);
  }});

  // Center root
  const totalH=Math.max(rightY,leftY);
  const rootY=totalH/2-NODE_H/2;
  nodePositions[TREE.id]={{x:-rootW/2,y:rootY,w:rootW,h:NODE_H,side:'center',branchColor:'#6366f1',depth:0,collapsed:false,node:TREE}};
}}

// ── Render ──
function renderMap(){{
  layoutTree();
  const canvas=document.getElementById('canvas');
  const svg=document.getElementById('svgLines');

  // Clear old nodes (keep svg)
  canvas.querySelectorAll('.mm-node').forEach(e=>e.remove());
  svg.innerHTML='';

  // Find bounds for centering
  let minX=Infinity,minY=Infinity,maxX=-Infinity,maxY=-Infinity;
  for(const p of Object.values(nodePositions)){{
    minX=Math.min(minX,p.x);
    minY=Math.min(minY,p.y);
    maxX=Math.max(maxX,p.x+p.w);
    maxY=Math.max(maxY,p.y+p.h);
  }}
  const pad=80;
  const offsetX=-minX+pad;
  const offsetY=-minY+pad;

  // Draw SVG curves
  function drawCurves(node,depth){{
    if(depth>=maxDepth||!node.children)return;
    const parent=nodePositions[node.id];
    if(!parent)return;
    const px=parent.x+offsetX;
    const py=parent.y+offsetY;

    for(const child of node.children){{
      const cp=nodePositions[child.id];
      if(!cp)continue;
      const cx=cp.x+offsetX;
      const cy=cp.y+offsetY;

      // Connection points
      let x1,y1,x2,y2;
      if(cp.side==='right'){{
        x1=px+parent.w; y1=py+parent.h/2;
        x2=cx; y2=cy+cp.h/2;
      }}else{{
        x1=px; y1=py+parent.h/2;
        x2=cx+cp.w; y2=cy+cp.h/2;
      }}

      const dx=Math.abs(x2-x1)*0.5;
      const path=document.createElementNS('http://www.w3.org/2000/svg','path');
      path.setAttribute('d',`M${{x1}},${{y1}} C${{x1+(cp.side==='right'?dx:-dx)}},${{y1}} ${{x2+(cp.side==='right'?-dx:dx)}},${{y2}} ${{x2}},${{y2}}`);
      path.setAttribute('fill','none');
      path.setAttribute('stroke',cp.branchColor);
      path.setAttribute('stroke-width',depth===0?'3':'2');
      path.setAttribute('opacity',depth===0?'0.6':'0.35');
      svg.appendChild(path);

      drawCurves(child,depth+1);
    }}
  }}
  drawCurves(TREE,0);

  // Create node elements
  for(const [id,p] of Object.entries(nodePositions)){{
    const div=document.createElement('div');
    div.className='mm-node';
    div.dataset.id=id;
    div.dataset.type=p.node.type||'default';
    div.style.left=(p.x+offsetX)+'px';
    div.style.top=(p.y+offsetY)+'px';

    let tagsHtml='';
    if(p.node.tags&&p.node.tags.length){{
      tagsHtml='<span class="tags">'+p.node.tags.map(t=>{{
        const cls=t.split(':')[0];
        return `<span class="tag tag-${{cls}}">${{t}}</span>`;
      }}).join('')+'</span>';
    }}

    // Color the left border with branch color for non-root
    let borderStyle='';
    if(p.depth>0){{
      borderStyle=`border-left:3px solid ${{p.branchColor}};border-radius:4px 20px 20px 4px;`;
    }}

    div.innerHTML=`<div class="label" style="${{borderStyle}}">${{p.node.label}}${{tagsHtml}}</div>`;

    // Badge for comments/status
    const fb=feedback[id];
    if(fb){{
      const badge=document.createElement('span');
      if(fb.comments&&fb.comments.length){{
        badge.className='badge comments';
        badge.textContent=fb.comments.length;
        div.querySelector('.label').appendChild(badge);
      }}else if(fb.status==='approved'){{
        badge.className='badge approved';
        badge.textContent='✓';
        div.querySelector('.label').appendChild(badge);
      }}else if(fb.status==='revision'){{
        badge.className='badge revision';
        badge.textContent='!';
        div.querySelector('.label').appendChild(badge);
      }}
    }}

    // Collapse dot for hidden children
    if(p.collapsed){{
      const dot=document.createElement('span');
      dot.className='collapse-dot';
      dot.textContent=p.node.children.length;
      if(p.side==='right'||p.side==='center'){{
        dot.style.right='-24px';dot.style.top='50%';dot.style.transform='translateY(-50%)';
      }}else{{
        dot.style.left='-24px';dot.style.top='50%';dot.style.transform='translateY(-50%)';
      }}
      dot.onclick=(e)=>{{e.stopPropagation();maxDepth++;renderMap();fitView();}};
      div.querySelector('.label').appendChild(dot);
    }}

    div.onclick=(e)=>{{e.stopPropagation();openPanel(id);}};
    canvas.appendChild(div);
    nodeElements[id]=div;
  }}

  // Size canvas
  const cw=maxX-minX+pad*2;
  const ch=maxY-minY+pad*2;
  canvas.style.width=cw+'px';
  canvas.style.height=ch+'px';
  svg.setAttribute('width',cw);
  svg.setAttribute('height',ch);
}}

// ── Zoom & Pan ──
let scale=1,panX=0,panY=0,isDragging=false,dragStartX=0,dragStartY=0,panStartX=0,panStartY=0;
const wrap=document.getElementById('canvasWrap');
const canvas=document.getElementById('canvas');

function applyTransform(){{
  canvas.style.transform=`translate(${{panX}}px,${{panY}}px) scale(${{scale}})`;
  document.getElementById('zoomInfo').textContent=Math.round(scale*100)+'%';
}}

wrap.addEventListener('wheel',(e)=>{{
  e.preventDefault();
  const rect=wrap.getBoundingClientRect();
  const mx=e.clientX-rect.left;
  const my=e.clientY-rect.top;
  const oldScale=scale;
  const delta=e.deltaY>0?0.9:1.1;
  scale=Math.max(0.15,Math.min(3,scale*delta));
  panX=mx-(mx-panX)*(scale/oldScale);
  panY=my-(my-panY)*(scale/oldScale);
  applyTransform();
}},{{passive:false}});

wrap.addEventListener('mousedown',(e)=>{{
  if(e.target.closest('.mm-node,.comment-panel'))return;
  isDragging=true;dragStartX=e.clientX;dragStartY=e.clientY;panStartX=panX;panStartY=panY;
  wrap.classList.add('dragging');
}});
window.addEventListener('mousemove',(e)=>{{
  if(!isDragging)return;
  panX=panStartX+(e.clientX-dragStartX);
  panY=panStartY+(e.clientY-dragStartY);
  applyTransform();
}});
window.addEventListener('mouseup',()=>{{isDragging=false;wrap.classList.remove('dragging');}});

function fitView(){{
  const ww=wrap.clientWidth,wh=wrap.clientHeight;
  const cw=parseFloat(canvas.style.width)||2000;
  const ch=parseFloat(canvas.style.height)||1000;
  scale=Math.min(ww/cw,wh/ch,1)*0.9;
  panX=(ww-cw*scale)/2;
  panY=(wh-ch*scale)/2;
  applyTransform();
}}

function setDepth(d){{maxDepth=d;renderMap();fitView();}}

// ── Comment panel ──
function openPanel(nid){{
  currentNodeId=nid;
  // Highlight node
  document.querySelectorAll('.mm-node.active').forEach(el=>el.classList.remove('active'));
  const el=nodeElements[nid];
  if(el)el.classList.add('active');

  const p=nodePositions[nid];
  document.getElementById('cpTitle').textContent=p?p.node.label:nid;
  document.getElementById('cpDetail').textContent=p?.node.detail||'';

  const fb=feedback[nid]||{{status:'pending',comments:[]}};
  document.getElementById('btnApproved').classList.toggle('selected',fb.status==='approved');
  document.getElementById('btnRevision').classList.toggle('selected',fb.status==='revision');
  document.getElementById('commentText').value='';
  renderComments(nid);
  document.getElementById('commentPanel').classList.add('open');
}}
function closePanel(){{
  document.getElementById('commentPanel').classList.remove('open');
  document.querySelectorAll('.mm-node.active').forEach(el=>el.classList.remove('active'));
  currentNodeId=null;
}}
function setNodeStatus(status){{
  if(!currentNodeId)return;
  if(!feedback[currentNodeId])feedback[currentNodeId]={{status:'pending',comments:[]}};
  feedback[currentNodeId].status=status;
  document.getElementById('btnApproved').classList.toggle('selected',status==='approved');
  document.getElementById('btnRevision').classList.toggle('selected',status==='revision');
  updateBadge(currentNodeId);
  updateProgress();
  persistFeedback();
}}
function saveComment(){{
  if(!currentNodeId)return;
  const text=document.getElementById('commentText').value.trim();
  if(!text)return;
  const cat=document.getElementById('commentCategory').value;
  if(!feedback[currentNodeId])feedback[currentNodeId]={{status:'pending',comments:[]}};
  feedback[currentNodeId].comments.push({{id:Date.now(),text,category:cat}});
  if(feedback[currentNodeId].status==='pending'){{
    feedback[currentNodeId].status='revision';
    document.getElementById('btnApproved').classList.remove('selected');
    document.getElementById('btnRevision').classList.add('selected');
  }}
  document.getElementById('commentText').value='';
  renderComments(currentNodeId);
  updateBadge(currentNodeId);
  updateProgress();
  persistFeedback();
}}
function deleteComment(nid,idx){{
  if(!feedback[nid])return;
  feedback[nid].comments.splice(idx,1);
  if(!feedback[nid].comments.length&&feedback[nid].status==='revision')feedback[nid].status='pending';
  renderComments(nid);
  updateBadge(nid);
  updateProgress();
  persistFeedback();
}}
function renderComments(nid){{
  const list=document.getElementById('commentList');
  const fb=feedback[nid]||{{comments:[]}};
  list.innerHTML='';
  fb.comments.forEach((c,i)=>{{
    const div=document.createElement('div');
    div.className='comment-item';
    div.innerHTML=`<span class="cdel" onclick="deleteComment('${{nid}}',${{i}})">&times;</span><div class="cm">${{c.category||'general'}}</div>${{c.text}}`;
    list.appendChild(div);
  }});
}}
function updateBadge(nid){{
  const el=nodeElements[nid];
  if(!el)return;
  el.querySelectorAll('.badge').forEach(b=>b.remove());
  const fb=feedback[nid];
  if(!fb)return;
  const badge=document.createElement('span');
  if(fb.comments&&fb.comments.length){{badge.className='badge comments';badge.textContent=fb.comments.length;}}
  else if(fb.status==='approved'){{badge.className='badge approved';badge.textContent='✓';}}
  else if(fb.status==='revision'){{badge.className='badge revision';badge.textContent='!';}}
  else return;
  el.querySelector('.label').appendChild(badge);
}}
function updateProgress(){{
  const allIds={json.dumps(all_ids)};
  const reviewed=allIds.filter(id=>{{const f=feedback[id];return f&&(f.status==='approved'||f.status==='revision');}}).length;
  const pct=allIds.length?Math.round(reviewed/allIds.length*100):0;
  document.querySelector('.progress-bar').style.width=pct+'%';
  document.querySelector('.header-meta').textContent=`Round {feedback.get('round',1)} · ${{reviewed}}/${{allIds.length}} reviewed`;
}}

// ── Persistence ──
let saveTimer=null;
function persistFeedback(){{
  clearTimeout(saveTimer);
  saveTimer=setTimeout(()=>{{
    fetch('/api/feedback',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(feedback)}});
  }},300);
}}
function submitAll(){{
  if(!confirm('Submit mind map review feedback?'))return;
  // Flush latest feedback before submitting (cancel any pending debounce)
  clearTimeout(saveTimer);
  fetch('/api/feedback',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(feedback)}})
  .then(()=>fetch('/api/submit',{{method:'POST'}}))
  .then(()=>{{
    const btn=document.getElementById('submitBtn');
    btn.disabled=true;
    btn.textContent='✓ Submitted';
    btn.style.background='#10b981';
    // Show full-page success overlay
    const overlay=document.createElement('div');
    overlay.style.cssText='position:fixed;inset:0;background:rgba(255,255,255,.85);z-index:200;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:12px;backdrop-filter:blur(4px)';
    overlay.innerHTML='<div style="font-size:48px">✅</div><div style="font-size:20px;font-weight:600;color:#065f46">Feedback Submitted</div><div style="font-size:14px;color:#64748b">Server is shutting down. Claude will automatically process the feedback.</div>';
    document.body.appendChild(overlay);
  }});
}}

// ── Init ──
renderMap();
setTimeout(fitView,50);
// Close panel on Escape
document.addEventListener('keydown',(e)=>{{if(e.key==='Escape')closePanel();}});
</script></body></html>"""


# ── HTTP Handler ──────────────────────────────────────────────────────────────

class MindmapHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path == "/":
            tree = load_tree()
            fb = load_feedback()
            html = render_page(tree, fb)
            self._html(html)
        elif path == "/api/feedback":
            self._json(load_feedback())
        elif path == "/api/tree":
            self._json(load_tree())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}

        if path == "/api/feedback":
            fb = load_feedback()
            fb["nodes"] = body
            save_feedback(fb)
            self._json({"ok": True})
        elif path == "/api/submit":
            fb = load_feedback()
            fb["submitted_at"] = C.now_iso()
            save_feedback(fb)
            self._json({"ok": True})
            # Print feedback summary to stdout so Claude receives it
            nodes = fb.get("nodes", {})
            approved = [nid for nid, n in nodes.items() if n.get("status") == "approved"]
            revision = [nid for nid, n in nodes.items() if n.get("status") == "revision"]
            print(f"\n{'='*60}")
            print(f"Feedback submitted! Saved to {FEEDBACK_PATH}")
            print(f"  Round:    {fb.get('round', 1)}")
            print(f"  Approved: {len(approved)}")
            print(f"  Revision: {len(revision)}")
            if revision:
                print(f"\nNodes needing revision:")
                for nid in revision:
                    node = nodes[nid]
                    comments = node.get("comments", [])
                    print(f"  - {nid}: {len(comments)} comment(s)")
                    for c in comments:
                        print(f"      [{c.get('category','general')}] {c.get('text','')}")
            print(f"{'='*60}")
            print(f"\n>>> FEEDBACK_JSON_PATH={FEEDBACK_PATH}")
            sys.stdout.flush()
            import threading
            threading.Timer(1.0, lambda: os._exit(0)).start()
        else:
            self.send_response(404)
            self.end_headers()

    def _html(self, content):
        data = content.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _json(self, obj):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *a):
        pass


def main():
    # Kill any other review servers to avoid multiple browser windows
    C.kill_other_review_servers(PORT)

    server = http.server.HTTPServer((HOST, PORT), MindmapHandler)
    url = f"http://{HOST}:{PORT}"
    title = TITLES.get(SOURCE, SOURCE)
    if HOST == "0.0.0.0":
        import socket
        local_ip = socket.gethostbyname(socket.gethostname())
        print(f"{title} Review Server started:")
        print(f"  Local:   http://localhost:{PORT}")
        print(f"  Network: http://{local_ip}:{PORT}")
    else:
        print(f"{title} Review Server started: {url}")
    print(f"Source:   {SOURCE}")
    print(f"Reading:  {BASE}")
    print(f"Feedback: {FEEDBACK_PATH}")
    print(f"\nPress Ctrl+C to stop.\n")

    if not NO_OPEN:
        import webbrowser
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()


if __name__ == "__main__":
    main()
