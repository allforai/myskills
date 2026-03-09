#!/usr/bin/env python3
"""Review Hub Server — unified review server for all product-design artifacts.

Serves 6 tabs (concept, map, data-model, wireframe, ui, spec) on a single port.
Auto-detects which tabs have data available and renders interactive mind maps
with shared navigation, feedback, and comment panels.

Usage:
    python3 review_hub_server.py <BASE_PATH> [--port 18900] [--no-open true]
"""

import http.server
import json
import os
import re
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C

# ── Setup ─────────────────────────────────────────────────────────────────────
BASE, args = C.parse_args()
PORT = int(args.get("port", "18900"))
HOST = args.get("host", "localhost")
NO_OPEN = args.get("no-open", "false").lower() in ("true", "1", "yes")

# ── Tab Definitions ───────────────────────────────────────────────────────────

TAB_DEFS = [
    {"id": "concept", "name": "概念", "path": "/concept"},
    {"id": "map", "name": "地图", "path": "/map"},
    {"id": "data-model", "name": "数据模型", "path": "/data-model"},
    {"id": "wireframe", "name": "线框", "path": "/wireframe"},
    {"id": "ui", "name": "UI", "path": "/ui"},
    {"id": "spec", "name": "规格", "path": "/spec"},
]


def detect_tabs():
    """Detect which tabs have data available."""
    tabs = {}
    tabs["concept"] = os.path.exists(os.path.join(BASE, "product-concept/product-concept.json"))
    tabs["map"] = os.path.exists(os.path.join(BASE, "product-map/task-inventory.json"))
    tabs["data-model"] = os.path.exists(os.path.join(BASE, "product-map/entity-model.json"))
    tabs["wireframe"] = os.path.exists(os.path.join(BASE, "experience-map/experience-map.json"))
    tabs["ui"] = os.path.exists(os.path.join(BASE, "ui-design/ui-design-spec.json"))
    tabs["spec"] = _has_spec_data()
    return tabs


def _has_spec_data():
    sp_dir = os.path.join(BASE, "project-forge/sub-projects")
    if not os.path.isdir(sp_dir):
        return False
    for name in os.listdir(sp_dir):
        if os.path.exists(os.path.join(sp_dir, name, "design.json")):
            return True
    return False


# ── Helpers ───────────────────────────────────────────────────────────────────

def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;")


def _node(nid, label, ntype="default", detail="", children=None, tags=None):
    n = {"id": nid, "label": label, "type": ntype}
    if detail:
        n["detail"] = detail
    if children:
        n["children"] = children
    if tags:
        n["tags"] = tags
    return n


def _auto_group_children(node, max_fanout=8):
    """Recursively group children into sub-groups when fan-out exceeds max_fanout.

    If a node has >max_fanout children, split them into groups of ~max_fanout
    with auto-generated group labels based on first/last child labels.
    """
    children = node.get("children", [])
    # Recurse first
    for c in children:
        _auto_group_children(c, max_fanout)

    if len(children) <= max_fanout:
        return

    # Group by type if possible (different types get their own group)
    type_groups = {}
    for c in children:
        t = c.get("type", "default")
        type_groups.setdefault(t, []).append(c)

    # If type grouping produces reasonable sizes, use it
    if len(type_groups) > 1 and all(len(g) <= max_fanout for g in type_groups.values()):
        return  # already manageable by type

    # Otherwise chunk into groups of max_fanout
    groups = []
    for i in range(0, len(children), max_fanout):
        chunk = children[i:i + max_fanout]
        if len(chunk) == 1:
            groups.append(chunk[0])
        else:
            first_label = chunk[0].get("label", "")[:6]
            last_label = chunk[-1].get("label", "")[:6]
            group_label = f"{first_label} … {last_label}"
            gid = f"{node['id']}_g{i // max_fanout}"
            groups.append(_node(gid, group_label, "group", children=chunk))
    node["children"] = groups


def collect_all_node_ids(node):
    ids = [node["id"]]
    for c in node.get("children", []):
        ids.extend(collect_all_node_ids(c))
    return ids


# ── Shared Nav Bar ────────────────────────────────────────────────────────────

def render_nav(active_tab):
    """Render shared top navigation bar HTML."""
    avail = detect_tabs()
    tabs_html = []
    for t in TAB_DEFS:
        tid = t["id"]
        name = t["name"]
        path = t["path"]
        is_active = tid == active_tab
        is_available = avail.get(tid, False)

        if is_active:
            cls = "nav-tab active"
            indicator = "●"
            tabs_html.append(f'<span class="{cls}">{indicator} {_esc(name)}</span>')
        elif is_available:
            cls = "nav-tab available"
            indicator = "●"
            tabs_html.append(f'<a class="{cls}" href="{path}">{indicator} {_esc(name)}</a>')
        else:
            cls = "nav-tab unavailable"
            indicator = "○"
            tabs_html.append(f'<span class="{cls}">{indicator} {_esc(name)}</span>')

    return f"""<nav class="hub-nav">
  <a class="hub-title" href="/">Review Hub</a>
  <div class="hub-tabs">{''.join(tabs_html)}</div>
</nav>
<style>
.hub-nav{{display:flex;align-items:center;gap:16px;background:#fff;border-bottom:1px solid #e2e8f0;padding:0 24px;height:52px;font-family:-apple-system,system-ui,'Segoe UI',sans-serif;z-index:30;position:relative}}
.hub-title{{font-size:15px;font-weight:700;color:#1e293b;text-decoration:none;white-space:nowrap}}
.hub-title:hover{{color:#6366f1}}
.hub-tabs{{display:flex;gap:6px;margin-left:16px}}
.nav-tab{{display:inline-flex;align-items:center;gap:4px;padding:6px 14px;border-radius:8px;font-size:13px;font-weight:500;text-decoration:none;transition:all .15s;white-space:nowrap}}
.nav-tab.active{{background:#334155;color:#fff}}
.nav-tab.available{{background:#fff;color:#334155;border:1px solid #e2e8f0;cursor:pointer}}
.nav-tab.available:hover{{background:#f1f5f9;border-color:#cbd5e1}}
.nav-tab.unavailable{{background:#f8fafc;color:#cbd5e1;cursor:default}}
</style>"""


# ── Shared Mind Map Renderer ──────────────────────────────────────────────────

def render_mindmap_page(tree, feedback, title, tab_id, categories, extra_node_css=""):
    """Render XMind-style mind map page with shared nav bar.

    Args:
        tree: Root node dict {id, label, type, detail, children, tags}
        feedback: Feedback dict {round, submitted_at, nodes: {node_id: {status, comments}}}
        title: Page title (Chinese)
        tab_id: Active tab ID for nav highlighting
        categories: List of feedback category strings
        extra_node_css: Additional CSS for tab-specific node types
    Returns: Full HTML string
    """
    all_ids = collect_all_node_ids(tree)
    total = len(all_ids)
    fb_nodes = feedback.get("nodes", {})
    reviewed = sum(1 for nid in all_ids if fb_nodes.get(nid, {}).get("status") in ("approved", "revision"))
    tree_json = json.dumps(tree, ensure_ascii=False)
    feedback_json = json.dumps(fb_nodes, ensure_ascii=False)

    cat_options = "\n".join(f'      <option value="{_esc(c)}">{_esc(c)}</option>' for c in categories)

    nav_html = render_nav(tab_id)

    return f"""<!DOCTYPE html>
<html lang="zh"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_esc(title)} - Review Hub</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,system-ui,'Segoe UI',sans-serif;background:#f8fafc;overflow:hidden;height:100vh}}
/* ── Header ── */
.header{{background:#fff;border-bottom:1px solid #e2e8f0;padding:12px 24px;display:flex;align-items:center;gap:20px;z-index:20;position:relative}}
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
.zoom-info{{font-size:11px;color:#94a3b8;width:48px;text-align:center;border:1px solid transparent;border-radius:4px;padding:2px 4px;background:transparent;cursor:text}}.zoom-info:hover{{border-color:#475569}}.zoom-info:focus{{border-color:#3b82f6;outline:none;background:#1e293b}}
/* ── Canvas ── */
.canvas-wrap{{position:relative;width:100%;height:calc(100vh - 104px);overflow:hidden;cursor:grab}}
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
{extra_node_css}
/* ── Comment panel ── */
.comment-panel{{position:fixed;right:0;top:104px;width:380px;height:calc(100vh - 104px);background:#fff;border-left:1px solid #e2e8f0;box-shadow:-4px 0 20px rgba(0,0,0,.06);z-index:50;transform:translateX(100%);transition:transform .25s ease;display:flex;flex-direction:column}}
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
{nav_html}
<div class="header">
  <h1>{_esc(title)}</h1>
  <div class="header-meta">Round {feedback.get('round',1)} &middot; {reviewed}/{total} reviewed</div>
  <div class="progress"><div class="progress-bar" style="width:{reviewed/total*100 if total else 0:.0f}%"></div></div>
  <div class="toolbar">
    <button onclick="setDepth(2)">Level 2</button>
    <button onclick="setDepth(3)">Level 3</button>
    <button onclick="setDepth(Infinity)">All</button>
    <button onclick="fitView()">Fit</button>
    <input type="text" class="zoom-info" id="zoomInfo" value="100%" onkeydown="if(event.key==='Enter')applyZoomInput(this)" onblur="applyZoomInput(this)">
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
{cat_options}
    </select>
    <button class="add-btn" onclick="saveComment()">Add Comment</button>
    <div class="comment-list" id="commentList"></div>
  </div>
</div>
<script>
const TAB_ID='{_esc(tab_id)}';
const TREE={tree_json};
let feedback={feedback_json};
let currentNodeId=null;
let maxDepth=Infinity;
const collapsedNodes=new Set();  // per-node collapse state

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

function isCollapsed(node,depth){{
  return collapsedNodes.has(node.id)||(depth>=maxDepth);
}}

function countLeaves(node,depth){{
  if(isCollapsed(node,depth)||!node.children||!node.children.length)return 1;
  return node.children.reduce((s,c)=>s+countLeaves(c,depth+1),0);
}}

function layoutSubtree(node,x,yStart,side,branchColor,depth){{
  node._depth=depth;
  const w=nodeWidth(node);
  const h=NODE_H;
  const nodeCollapsed=isCollapsed(node,depth);
  const children=(!nodeCollapsed&&node.children)?node.children:[];
  const hasHiddenChildren=(!!(node.children&&node.children.length))&&nodeCollapsed;

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
    if(isCollapsed(node,depth)||!node.children)return;
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
        badge.textContent='\\u2713';
        div.querySelector('.label').appendChild(badge);
      }}else if(fb.status==='revision'){{
        badge.className='badge revision';
        badge.textContent='!';
        div.querySelector('.label').appendChild(badge);
      }}
    }}

    // Collapse/expand dot (per-node toggle, XMind style)
    if(p.node.children&&p.node.children.length){{
      const dot=document.createElement('span');
      dot.className='collapse-dot';
      if(p.collapsed){{
        dot.textContent=p.node.children.length;
        dot.title='展开 ('+p.node.children.length+' children)';
      }}else{{
        dot.textContent='−';
        dot.title='折叠';
        dot.style.opacity='0';
        div.addEventListener('mouseenter',()=>{{dot.style.opacity='1';}});
        div.addEventListener('mouseleave',()=>{{dot.style.opacity='0';}});
      }}
      if(p.side==='right'||p.side==='center'){{
        dot.style.right='-24px';dot.style.top='50%';dot.style.transform='translateY(-50%)';
      }}else{{
        dot.style.left='-24px';dot.style.top='50%';dot.style.transform='translateY(-50%)';
      }}
      dot.onclick=(e)=>{{
        e.stopPropagation();
        if(collapsedNodes.has(id))collapsedNodes.delete(id);
        else collapsedNodes.add(id);
        renderMap();
      }};
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
  document.getElementById('zoomInfo').value=Math.round(scale*100)+'%';
}}

function applyZoomInput(el){{
  const v=parseInt(el.value);
  if(!isNaN(v)&&v>=15&&v<=300){{
    const ww=wrap.clientWidth/2,wh=wrap.clientHeight/2;
    const oldScale=scale;
    scale=v/100;
    panX=ww-(ww-panX)*(scale/oldScale);
    panY=wh-(wh-panY)*(scale/oldScale);
    applyTransform();
  }}else{{
    el.value=Math.round(scale*100)+'%';
  }}
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

function setDepth(d){{maxDepth=d;collapsedNodes.clear();renderMap();fitView();}}

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
  else if(fb.status==='approved'){{badge.className='badge approved';badge.textContent='\\u2713';}}
  else if(fb.status==='revision'){{badge.className='badge revision';badge.textContent='!';}}
  else return;
  el.querySelector('.label').appendChild(badge);
}}
function updateProgress(){{
  const allIds={json.dumps(all_ids)};
  const reviewed=allIds.filter(id=>{{const f=feedback[id];return f&&(f.status==='approved'||f.status==='revision');}}).length;
  const pct=allIds.length?Math.round(reviewed/allIds.length*100):0;
  document.querySelector('.progress-bar').style.width=pct+'%';
  document.querySelector('.header-meta').textContent=`Round {feedback.get('round',1)} \\u00b7 ${{reviewed}}/${{allIds.length}} reviewed`;
}}

// ── Persistence ──
let saveTimer=null;
function persistFeedback(){{
  clearTimeout(saveTimer);
  saveTimer=setTimeout(()=>{{
    fetch('/api/'+TAB_ID+'/feedback',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(feedback)}});
  }},300);
}}
function submitAll(){{
  if(!confirm('Submit review feedback?'))return;
  clearTimeout(saveTimer);
  fetch('/api/'+TAB_ID+'/feedback',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(feedback)}})
  .then(()=>fetch('/api/'+TAB_ID+'/submit',{{method:'POST'}}))
  .then(()=>{{
    const btn=document.getElementById('submitBtn');
    btn.disabled=true;
    btn.textContent='\\u2713 Submitted';
    btn.style.background='#10b981';
    const overlay=document.createElement('div');
    overlay.style.cssText='position:fixed;inset:0;background:rgba(255,255,255,.85);z-index:200;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:12px;backdrop-filter:blur(4px)';
    overlay.innerHTML='<div style="font-size:48px">\\u2705</div><div style="font-size:20px;font-weight:600;color:#065f46">Feedback Submitted</div><div style="font-size:14px;color:#64748b">You can close this tab or continue reviewing other sections.</div>';
    document.body.appendChild(overlay);
  }});
}}

// ── Init ──
renderMap();
setTimeout(fitView,50);
document.addEventListener('keydown',(e)=>{{if(e.key==='Escape')closePanel();}});
</script></body></html>"""


# ── Placeholder Page Renderers ────────────────────────────────────────────────

def _placeholder_page(tab_id, title):
    nav = render_nav(tab_id)
    return f"""<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_esc(title)} - Review Hub</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,system-ui,'Segoe UI',sans-serif;background:#f8fafc;height:100vh}}
.placeholder{{display:flex;flex-direction:column;align-items:center;justify-content:center;height:calc(100vh - 52px);color:#94a3b8}}
.placeholder h2{{font-size:24px;font-weight:600;margin-bottom:8px;color:#64748b}}
.placeholder p{{font-size:14px}}
</style></head><body>
{nav}
<div class="placeholder">
  <h2>{_esc(title)}</h2>
  <p>Coming soon</p>
</div>
</body></html>"""


def render_home():
    avail = detect_tabs()
    nav = render_nav("")
    tab_cards = []
    for t in TAB_DEFS:
        tid = t["id"]
        name = t["name"]
        path = t["path"]
        available = avail.get(tid, False)
        status = "available" if available else "unavailable"
        indicator = "●" if available else "○"
        link_open = f'<a href="{path}" style="text-decoration:none;color:inherit">' if available else ""
        link_close = "</a>" if available else ""
        tab_cards.append(f'{link_open}<div class="card {status}"><span class="indicator">{indicator}</span> {_esc(name)}</div>{link_close}')
    return f"""<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Review Hub</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,system-ui,'Segoe UI',sans-serif;background:#f8fafc;height:100vh}}
.home{{display:flex;flex-direction:column;align-items:center;justify-content:center;height:calc(100vh - 52px);gap:32px}}
.home h1{{font-size:28px;font-weight:700;color:#1e293b}}
.home p{{font-size:14px;color:#64748b}}
.cards{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;max-width:480px}}
.card{{padding:20px 28px;border-radius:12px;font-size:15px;font-weight:500;text-align:center;border:1px solid #e2e8f0;transition:all .15s}}
.card.available{{background:#fff;color:#334155;cursor:pointer}}
.card.available:hover{{background:#f1f5f9;border-color:#cbd5e1;box-shadow:0 2px 8px rgba(0,0,0,.06)}}
.card.unavailable{{background:#f8fafc;color:#cbd5e1}}
.indicator{{font-size:10px}}
</style></head><body>
{nav}
<div class="home">
  <h1>Review Hub</h1>
  <p>Select a tab to begin reviewing</p>
  <div class="cards">{''.join(tab_cards)}</div>
</div>
</body></html>"""


# ── Concept Tab ────────────────────────────────────────────────────────────────

CONCEPT_FEEDBACK_DIR = os.path.join(BASE, "concept-review")
C.ensure_dir(CONCEPT_FEEDBACK_DIR)
CONCEPT_FEEDBACK_PATH = os.path.join(CONCEPT_FEEDBACK_DIR, "review-feedback.json")


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
        # Normalize: strings become dicts, dicts pass through
        for i, item in enumerate(raw_mechs):
            if isinstance(item, str):
                mechs.append({"id": f"mec-{i}", "name": item[:40], "description": item})
            elif isinstance(item, dict):
                mechs.append(item)
    elif isinstance(raw_mechs, dict):
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

    tree = _node("root", mission, "root", children=children)
    _auto_group_children(tree)
    return tree


def load_concept_feedback():
    fb = C.load_json(CONCEPT_FEEDBACK_PATH)
    return fb if fb else {"round": 1, "submitted_at": None, "nodes": {}}


def render_concept_page():
    tree = load_concept_tree()
    feedback = load_concept_feedback()
    categories = ["General", "Feature", "Concept", "Flow"]
    return render_mindmap_page(tree, feedback, "产品概念", "concept", categories)


# ── Map Tab ────────────────────────────────────────────────────────────────────

MAP_FEEDBACK_DIR = os.path.join(BASE, "product-map-review")
C.ensure_dir(MAP_FEEDBACK_DIR)
MAP_FEEDBACK_PATH = os.path.join(MAP_FEEDBACK_DIR, "review-feedback.json")


def load_product_map_tree():
    """Transform product-map data into a mind map tree with shared patterns branch."""
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
    tasks = [C._normalize_task(t) for t in inv_data.get("tasks", [])]
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

        def _task_node(t, _rid=rid):
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
            fid = f.get("id") or f.get("flow_id", "")
            fname = f.get("name") or f.get("flow_name", fid)
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

    # Shared patterns branch (NEW)
    patterns = C.load_json(os.path.join(BASE, "design-pattern/pattern-catalog.json"))
    standards = C.load_json(os.path.join(BASE, "behavioral-standards/behavioral-standards.json"))

    pattern_children = []
    if patterns:
        for p in patterns.get("patterns", []):
            pid = p.get("pattern_id", p.get("id", ""))
            pattern_children.append(_node(pid, p.get("name", pid), "concept", p.get("description", "")))
    if standards:
        for s in standards.get("standards", standards.get("behaviors", [])):
            sid = s.get("id", "")
            pattern_children.append(_node(f"bs_{sid}", s.get("name", sid), "mechanism", s.get("description", "")))
    if pattern_children:
        children.append(_node("patterns", "共性模式", "group", "", pattern_children))

    tree = _node("root", project_name, "root", children=children)
    _auto_group_children(tree)
    return tree


def load_map_feedback():
    fb = C.load_json(MAP_FEEDBACK_PATH)
    return fb if fb else {"round": 1, "submitted_at": None, "nodes": {}}


def render_map_page():
    tree = load_product_map_tree()
    feedback = load_map_feedback()
    categories = ["General", "Role", "Task", "Flow", "Pattern"]
    return render_mindmap_page(tree, feedback, "产品地图", "map", categories)


# ── Data-Model Tab ─────────────────────────────────────────────────────────────

DM_FEEDBACK_DIR = os.path.join(BASE, "data-model-review")
C.ensure_dir(DM_FEEDBACK_DIR)
DM_FEEDBACK_PATH = os.path.join(DM_FEEDBACK_DIR, "review-feedback.json")


def load_datamodel_tree():
    """Transform entity-model + api-contracts + view-objects into a mind map tree."""
    entities, relationships = C.load_entity_model(BASE)
    endpoints = C.load_api_contracts(BASE)
    view_objects = C.load_view_objects(BASE)

    if not entities and not endpoints and not view_objects:
        return _node("root", "No data model data", "error")

    # Build lookup maps
    eps_by_entity = {}
    for ep in endpoints:
        eref = ep.get("entity_ref", "")
        if eref:
            eps_by_entity.setdefault(eref, []).append(ep)

    vos_by_entity = {}
    for vo in view_objects:
        eref = vo.get("entity_ref", "")
        if eref:
            vos_by_entity.setdefault(eref, []).append(vo)

    children = []

    for entity in entities:
        eid = entity.get("id", "")
        ename_zh = entity.get("name_zh", entity.get("name", eid))
        emodule = entity.get("module", "")
        fields = entity.get("fields", [])
        state_machine = entity.get("state_machine", None)

        entity_children = []

        # ── Fields group ──
        if fields:
            field_nodes = []
            for f in fields:
                fname = f.get("name", "")
                ftype = f.get("type", "")
                fpk = f.get("primary_key", False) or f.get("pk", False)
                frequired = f.get("required", False)
                constraints = f.get("constraints", [])

                suffix = ""
                if fpk:
                    fnode_type = "field-pk"
                    suffix = " (PK)"
                elif frequired:
                    fnode_type = "field-required"
                    suffix = " ✱"
                else:
                    fnode_type = "field"

                flabel = f"{fname}: {ftype}{suffix}"
                fdetail = f"字段: {fname}\n类型: {ftype}\n必填: {'yes' if frequired else 'no'}"
                if constraints:
                    fdetail += f"\n约束: {constraints}"

                field_nodes.append(_node(
                    f"{eid}-f-{fname}", flabel, fnode_type, fdetail
                ))
            field_summary = ", ".join(f.get("name", "") for f in fields[:6])
            if len(fields) > 6:
                field_summary += f" +{len(fields) - 6}"
            entity_children.append(_node(
                f"{eid}-fields", f"字段({len(fields)}): {field_summary}", "field-group", children=field_nodes
            ))

        # ── State machine group ──
        if state_machine:
            transitions = state_machine.get("transitions", [])
            if transitions:
                trans_nodes = []
                for t in transitions:
                    action = t.get("action", t.get("trigger", ""))
                    target = t.get("to", t.get("target", ""))
                    task_ref = t.get("task_ref", "")
                    needs_input = t.get("needs_input", False)

                    tlabel = f"{action} → {target}"
                    tdetail = f"操作: {action}\n任务: {task_ref}\n需要输入: {'yes' if needs_input else 'no'}"
                    trans_nodes.append(_node(
                        f"{eid}-sm-{action}", tlabel, "transition", tdetail
                    ))
                entity_children.append(_node(
                    f"{eid}-sm", "状态机", "state-machine", children=trans_nodes
                ))

        # ── API group ──
        entity_eps = eps_by_entity.get(eid, [])
        if entity_eps:
            api_nodes = []
            for ep in entity_eps:
                method = ep.get("method", "GET")
                path = ep.get("path", "")
                ep_type = ep.get("type", "")
                task_refs = ep.get("task_refs", [])
                req_body = ep.get("request_body", ep.get("request_fields", []))

                alabel = f"{method} {path}"
                atags = [ep_type] if ep_type else []
                adetail = f"接口: {method} {path}\n类型: {ep_type}\n来源任务: {task_refs}"
                if req_body:
                    adetail += f"\n请求体: {req_body}"

                api_nodes.append(_node(
                    f"{eid}-api-{method}-{path}", alabel, "api", adetail, tags=atags
                ))
            entity_children.append(_node(
                f"{eid}-apis", "接口", "api-group", children=api_nodes
            ))

        # ── View objects group ──
        entity_vos = vos_by_entity.get(eid, [])
        if entity_vos:
            vo_nodes = []
            for vo in entity_vos:
                void = vo.get("id", "")
                voname = vo.get("name_zh", vo.get("name", void))
                vo_itype = vo.get("interaction_type", "")
                vo_fields = vo.get("fields", [])
                vo_actions = vo.get("actions", [])

                volabel = f"{voname} ({void})" if void else voname
                votags = [void] if void else []
                vo_field_names = ", ".join(f.get("name", "") for f in vo_fields[:6])
                if len(vo_fields) > 6:
                    vo_field_names += f" +{len(vo_fields) - 6}"
                vodetail = (
                    f"视图: {voname}\n交互类型: {vo_itype}"
                    f"\n字段({len(vo_fields)}): {vo_field_names}"
                    f"\n操作数: {len(vo_actions)}"
                )

                vo_children = []
                for act in vo_actions:
                    alabel_act = act.get("label", act.get("name", ""))
                    atype = act.get("type", "")
                    aapi_ref = act.get("api_ref", "")
                    atrigger = act.get("trigger", "")
                    aon_success = act.get("on_success", "")

                    adetail = (
                        f"按钮: {alabel_act}\n类型: {atype}\n接口: {aapi_ref}"
                        f"\n触发: {atrigger}\n成功: {aon_success}"
                    )
                    vo_children.append(_node(
                        f"{void}-act-{alabel_act}", alabel_act, "action", adetail
                    ))

                vo_nodes.append(_node(
                    f"{eid}-vo-{void}", volabel, "vo", vodetail, vo_children, votags
                ))
            entity_children.append(_node(
                f"{eid}-vos", "视图", "vo-group", children=vo_nodes
            ))

        # Entity detail
        entity_api_count = len(entity_eps)
        entity_field_count = len(fields)
        crud_methods = set()
        for ep in entity_eps:
            m = ep.get("method", "").upper()
            t = ep.get("type", "").lower()
            if m == "POST" or t == "create":
                crud_methods.add("C")
            if m == "GET" or t in ("list", "detail", "read"):
                crud_methods.add("R")
            if m in ("PUT", "PATCH") or t == "update":
                crud_methods.add("U")
            if m == "DELETE" or t == "delete":
                crud_methods.add("D")
        crud_str = ",".join(sorted(crud_methods)) if crud_methods else "-"

        edetail = (
            f"实体: {ename_zh}\n来源模块: {emodule}"
            f"\n字段数: {entity_field_count}\n接口数: {entity_api_count}"
            f"\nCRUD: {crud_str}"
        )

        children.append(_node(
            eid, f"{eid} {ename_zh}", "entity", edetail, entity_children
        ))

    # ── Relationships group ──
    if relationships:
        rel_nodes = []
        for rel in relationships:
            rfrom = rel.get("from", rel.get("source", ""))
            rto = rel.get("to", rel.get("target", ""))
            rtype = rel.get("type", rel.get("cardinality", ""))
            rlabel = f"{rfrom} {rtype} {rto}"
            rel_nodes.append(_node(
                f"rel-{rfrom}-{rto}", rlabel, "relation", rlabel
            ))
        children.append(_node(
            "relations", "关系", "relation-group", children=rel_nodes
        ))

    tree = _node("root", "数据模型", "root", children=children)
    _auto_group_children(tree)
    return tree


def load_dm_feedback():
    fb = C.load_json(DM_FEEDBACK_PATH)
    return fb if fb else {"round": 1, "submitted_at": None, "nodes": {}}


def render_datamodel_page():
    tree = load_datamodel_tree()
    feedback = load_dm_feedback()
    categories = ["Entity", "API", "VO", "Action", "State Machine", "Product Map"]
    extra_css = """
.mm-node[data-type="entity"] .label{background:#dbeafe;color:#1e40af;font-weight:600;border-color:#93c5fd}
.mm-node[data-type="field-pk"] .label{background:#fef3c7;color:#92400e;font-weight:600}
.mm-node[data-type="field-fk"] .label{background:#e0e7ff;color:#4338ca}
.mm-node[data-type="field-required"] .label{background:#fff;color:#334155;font-weight:500}
.mm-node[data-type="field-required"] .label::after{content:" ✱";color:#ef4444}
.mm-node[data-type="state-machine"] .label{background:#f0fdfa;color:#115e59;border-color:#99f6e4}
.mm-node[data-type="transition"] .label{background:#f0fdf4;color:#166534;font-size:12px}
.mm-node[data-type="api-group"] .label{background:#eff6ff;color:#1d4ed8;font-weight:600}
.mm-node[data-type="api"] .label{background:#eff6ff;color:#1d4ed8;font-size:12px}
.mm-node[data-type="vo-group"] .label{background:#faf5ff;color:#7c3aed;font-weight:600}
.mm-node[data-type="vo"] .label{background:#f5f3ff;color:#6d28d9;font-weight:500}
.mm-node[data-type="vo-field"] .label{background:#fff;color:#64748b;font-size:12px}
.mm-node[data-type="action"] .label{background:#fef2f2;color:#dc2626;font-size:12px}
.mm-node[data-type="relation-group"] .label{background:#f1f5f9;color:#475569;font-weight:600}
.mm-node[data-type="relation"] .label{background:#f8fafc;color:#64748b;font-size:12px}
"""
    return render_mindmap_page(tree, feedback, "数据模型", "data-model", categories, extra_css)


# ── Wireframe Tab ─────────────────────────────────────────────────────────────

WF_FEEDBACK_DIR = os.path.join(BASE, "wireframe-review")
C.ensure_dir(WF_FEEDBACK_DIR)
WF_FEEDBACK_PATH = os.path.join(WF_FEEDBACK_DIR, "review-feedback.json")

EMOTION_COLORS = {
    "curious": "#4FC3F7", "anxious": "#FF8A65", "satisfied": "#81C784",
    "frustrated": "#E57373", "neutral": "#B0BEC5", "exploring": "#64B5F6",
    "confident": "#66BB6A", "confused": "#FFB74D",
}


def load_wf_feedback():
    fb = C.load_json(WF_FEEDBACK_PATH)
    if fb:
        return fb
    return {"round": 1, "submitted_at": None, "screens": {}}


def load_wireframe_data():
    """Load all data for wireframe tab."""
    op_lines, screen_index, loaded = C.load_experience_map(BASE)
    if not loaded:
        return [], {}, {}, {}, {}, {}

    inv = C.load_json(os.path.join(BASE, "product-map/task-inventory.json"))
    tasks = {t["id"]: C._normalize_task(t) for t in (inv.get("tasks", []) if inv else [])}

    roles = C.load_role_profiles_full(BASE)
    role_map = {r["id"]: r["name"] for r in roles}

    gate = C.load_interaction_gate(BASE)
    gate_issues = {}
    if gate:
        for lr in gate.get("lines", []):
            for issue in lr.get("issues", []):
                nid = issue.get("node", "")
                gate_issues.setdefault(nid, []).append(issue)

    vos = C.load_view_objects(BASE)
    vo_map = {v.get("id") or v.get("vo_id", ""): v for v in vos} if vos else {}
    apis = C.load_api_contracts(BASE)
    api_map = {a.get("id") or a.get("api_id", ""): a for a in apis} if apis else {}

    return op_lines, tasks, role_map, gate_issues, vo_map, api_map


def _infer_interaction_type(screen, tasks):
    """Infer interaction_type from CRUD and task names when VO is absent.

    Returns MG* code: MG1 (readonly list), MG2-L (CRUD list), MG2-C (create form),
    MG2-E (edit form), MG2-D (detail), MG3 (state machine), MG4 (approval).
    """
    actions = screen.get("actions", [])
    if not actions:
        return "MG1"

    # Collect all CRUD types and task names
    cruds = set()
    all_names = []
    for a in actions:
        crud = a.get("crud", "R") if isinstance(a, dict) else "R"
        cruds.add(crud)
        label = a.get("label", "") if isinstance(a, dict) else str(a)
        all_names.append(label)

    # Also check original task names for richer keywords
    for tid in screen.get("tasks", []):
        task = tasks.get(tid, {})
        tname = task.get("task_name", task.get("name", ""))
        if tname:
            all_names.append(tname)

    joined = " ".join(all_names)

    # Approval keywords → MG4
    if any(kw in joined for kw in ["审核", "审批", "批准", "驳回", "approve", "reject"]):
        return "MG4"

    # State-change keywords → MG3
    if any(kw in joined for kw in ["确认", "取消", "启用", "禁用", "上架", "下架", "发布",
                                     "完成", "处理", "分配", "接单", "签收"]):
        return "MG3"

    # Create → MG2-C
    if "C" in cruds:
        return "MG2-C"

    # Update → MG2-E
    if "U" in cruds:
        return "MG2-E"

    # Delete → MG3 (state change / destructive action)
    if "D" in cruds:
        return "MG3"

    # Read: detail vs list
    if any(kw in joined for kw in ["详情", "detail", "查看", "信息"]):
        return "MG2-D"

    # Read with management keywords → MG2-L (CRUD list with actions)
    if any(kw in joined for kw in ["管理", "列表", "搜索", "筛选", "导出"]):
        return "MG2-L"

    # Default: readonly list
    return "MG1"


def build_screens_with_context(op_lines, tasks, role_map, gate_issues, vo_map=None, api_map=None):
    """Build screen list with full context for wireframe rendering."""
    if vo_map is None:
        vo_map = {}
    if api_map is None:
        api_map = {}

    screens = []
    for ol in op_lines:
        for node in ol.get("nodes", []):
            nid = node["id"]
            for s in node.get("screens", []):
                sid = s["id"]
                screen_role = ""
                for tid in s.get("tasks", []):
                    task = tasks.get(tid)
                    if task and not screen_role:
                        screen_role = role_map.get(task.get("owner_role") or task.get("role_id", ""), "")

                vo_ref = s.get("vo_ref", "")
                vo = vo_map.get(vo_ref, {}) if vo_ref else {}
                data_fields = s.get("data_fields", []) or vo.get("fields", [])
                interaction_type = s.get("interaction_type", "") or vo.get("interaction_type", "")
                vo_actions = s.get("vo_actions", []) or vo.get("actions", [])

                # Infer interaction_type from CRUD + screen name when absent
                if not interaction_type:
                    interaction_type = _infer_interaction_type(s, tasks)
                states = s.get("states", {})
                flow_context = s.get("flow_context", {})

                screens.append({
                    "id": sid,
                    "name": s.get("name", ""),
                    "module": s.get("module", ""),
                    "notes": s.get("notes", ""),
                    "description": s.get("description", ""),
                    "tasks": s.get("tasks", []),
                    "actions": s.get("actions", []),
                    "vo_actions": vo_actions,
                    "non_negotiable": s.get("non_negotiable", []),
                    "role": screen_role,
                    "operation_line": ol["id"],
                    "operation_line_name": ol.get("name", ol["id"]),
                    "node_id": nid,
                    "emotion_state": node.get("emotion_state", "neutral"),
                    "emotion_intensity": node.get("emotion_intensity", 5),
                    "ux_intent": node.get("ux_intent", ""),
                    "gate_issues": gate_issues.get(nid, []),
                    "vo_ref": vo_ref,
                    "api_ref": s.get("api_ref", "") or vo.get("api_ref", ""),
                    "interaction_type": interaction_type,
                    "data_fields": data_fields,
                    "states": states,
                    "flow_context": flow_context,
                    "filters": vo.get("filters", []),
                    "entity_name": vo.get("entity_name", ""),
                })
    return screens


# ── Wireframe CSS ──────────────────────────────────────────────────────────

WF_CSS = """
body{margin:0;padding:24px;font-family:-apple-system,system-ui,sans-serif;background:#f8f9fa;color:#333}
.wf-container{max-width:480px;margin:0 auto;background:#fff;border:2px solid #dee2e6;border-radius:4px;overflow:hidden}
.wf-header{background:#e9ecef;padding:12px 16px;border-bottom:2px solid #dee2e6;display:flex;align-items:center;gap:8px}
.wf-header-title{font-size:14px;font-weight:600;color:#495057;flex:1}
.wf-emo{font-size:11px;padding:2px 8px;border-radius:10px;font-weight:500}
.wf-itype{font-size:10px;padding:2px 6px;border-radius:3px;background:#e8eaf6;color:#5c6bc0;font-weight:600}
.wf-body{padding:16px}
.wf-purpose{font-size:13px;color:#6c757d;margin-bottom:16px;padding:8px;background:#f8f9fa;border-left:3px solid #adb5bd;border-radius:0 4px 4px 0}
.wf-section{background:#f1f3f5;border:1px dashed #adb5bd;border-radius:4px;padding:16px;margin:8px 0;min-height:48px;display:flex;align-items:center;justify-content:center;color:#868e96;font-size:13px}
.wf-actions{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0}
.wf-btn{padding:8px 16px;border-radius:4px;font-size:13px;cursor:default;display:flex;align-items:center;gap:6px;border:none}
.wf-btn-primary{background:#dee2e6;color:#495057;font-weight:600;border:2px solid #adb5bd}
.wf-btn-secondary{background:#f8f9fa;color:#6c757d;border:1px dashed #ced4da}
.crud-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}
.wf-states{margin-top:12px;display:flex;gap:8px;flex-wrap:wrap}
.wf-state{font-size:11px;padding:4px 8px;border-radius:4px;background:#f8f9fa;color:#868e96;border:1px solid #e9ecef}
.wf-tasks{font-size:11px;color:#adb5bd;margin-top:12px}
.wf-constraints{font-size:12px;color:#e65100;background:#fff3e0;padding:8px;border-radius:4px;margin-top:8px}
.wf-gate{margin-top:8px}
.wf-gate-issue{font-size:12px;color:#c62828;background:#ffebee;padding:4px 8px;border-radius:4px;margin-top:4px}
.wf-label{font-size:11px;font-weight:600;color:#666}
.wf-intent{font-size:12px;color:#5c6bc0;background:#e8eaf6;padding:6px 8px;border-radius:4px;margin-bottom:12px}
.wf-table{width:100%;border-collapse:collapse;font-size:12px;margin:8px 0}
.wf-table th{background:#e9ecef;color:#495057;font-weight:600;padding:6px 8px;text-align:left;border:1px solid #dee2e6}
.wf-table td{padding:6px 8px;border:1px solid #dee2e6;color:#6c757d}
.wf-table tr:nth-child(even) td{background:#f8f9fa}
.wf-tag{display:inline-block;padding:1px 6px;border-radius:3px;background:#e8eaf6;color:#5c6bc0;font-size:10px}
.wf-toolbar{display:flex;gap:8px;align-items:center;margin-bottom:10px}
.wf-search{flex:1;padding:6px 10px;border:1px solid #dee2e6;border-radius:4px;background:#f8f9fa;color:#adb5bd;font-size:12px}
.wf-filters{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px}
.wf-filter-chip{padding:3px 10px;border-radius:12px;background:#f1f3f5;color:#868e96;font-size:11px;border:1px solid #dee2e6}
.wf-pagination{text-align:center;color:#adb5bd;font-size:12px;margin-top:8px}
.wf-form-field{margin-bottom:12px}
.wf-form-label{font-size:12px;color:#495057;font-weight:500;margin-bottom:4px;display:flex;align-items:center;gap:4px}
.wf-form-required{color:#e53935;font-weight:700}
.wf-form-input{width:100%;padding:6px 10px;border:1px solid #dee2e6;border-radius:4px;background:#f8f9fa;color:#adb5bd;font-size:12px;box-sizing:border-box}
.wf-form-textarea{width:100%;padding:6px 10px;border:1px solid #dee2e6;border-radius:4px;background:#f8f9fa;color:#adb5bd;font-size:12px;min-height:60px;box-sizing:border-box}
.wf-form-hint{font-size:10px;color:#adb5bd;margin-top:2px}
.wf-form-buttons{display:flex;gap:8px;justify-content:flex-end;margin-top:16px}
.wf-detail-row{display:flex;padding:6px 0;border-bottom:1px solid #f1f3f5;font-size:12px}
.wf-detail-label{width:120px;flex-shrink:0;color:#495057;font-weight:500}
.wf-detail-value{color:#6c757d;flex:1}
.wf-detail-actions{margin-top:12px;padding-top:8px;border-top:1px solid #dee2e6}
.wf-api-ref{font-size:10px;color:#adb5bd;margin-top:2px}
.wf-state-tabs{display:flex;gap:0;margin-bottom:10px;border:1px solid #dee2e6;border-radius:4px;overflow:hidden}
.wf-state-tab{padding:6px 12px;font-size:11px;background:#f8f9fa;color:#868e96;border-right:1px solid #dee2e6;flex:1;text-align:center}
.wf-state-tab:last-child{border-right:none}
.wf-state-tab.active{background:#495057;color:#fff}
.wf-transition{font-size:10px;color:#7c3aed;margin-top:2px}
.wf-approval-card{border:1px solid #dee2e6;border-radius:6px;padding:10px 12px;margin-bottom:8px;background:#fff}
.wf-approval-card-header{font-size:12px;color:#495057;font-weight:500;margin-bottom:6px}
.wf-approval-card-fields{font-size:11px;color:#868e96;margin-bottom:8px}
.wf-approval-btns{display:flex;gap:8px;justify-content:flex-end}
.wf-approval-reject{padding:4px 12px;border:1px solid #e57373;color:#e57373;border-radius:4px;background:#fff;font-size:11px}
.wf-approval-approve{padding:4px 12px;border:1px solid #66BB6A;color:#fff;border-radius:4px;background:#66BB6A;font-size:11px}
.wf-pending-badge{font-size:12px;color:#e65100;background:#fff3e0;padding:2px 8px;border-radius:4px}
.wf-4d{margin-top:16px;background:#f8f9fa;border:1px solid #e9ecef;border-radius:4px;padding:8px 12px}
.wf-4d-row{display:flex;align-items:center;gap:6px;padding:3px 0;font-size:12px}
.wf-4d-icon{font-size:14px;width:20px;text-align:center}
.wf-4d-label{font-weight:600;color:#495057;width:48px;flex-shrink:0}
.wf-4d-value{color:#6c757d;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
"""


# ── 4D Panel ───────────────────────────────────────────────────────────────

def _build_4d_panel(screen):
    """Build the 4D information panel (Data, Action, State, Flow)."""
    fields = screen.get("data_fields", [])
    field_names = ", ".join(f.get("label", f.get("name", "")) for f in fields[:6])
    if len(fields) > 6:
        field_names += "..."
    rw_count = sum(1 for f in fields if not f.get("readonly"))
    ro_count = len(fields) - rw_count
    rw_summary = f"{rw_count}rw/{ro_count}ro" if fields else ""
    data_val = f"{field_names} ({len(fields)} fields, {rw_summary})" if fields else "No fields"

    vo_actions = screen.get("vo_actions", [])
    actions = screen.get("actions", [])
    all_action_labels = [a.get("label", "") for a in vo_actions[:4] if isinstance(a, dict)] or [
        (a.get("label", "") if isinstance(a, dict) else str(a)) for a in actions[:4]
    ]
    action_labels = ", ".join(al for al in all_action_labels if al)
    api_refs = ", ".join(a.get("api_ref", "") for a in vo_actions if isinstance(a, dict) and a.get("api_ref"))
    action_val = f"{action_labels}" + (f" ({api_refs})" if api_refs else "") if action_labels else "No actions"

    states = screen.get("states", {})
    empty_desc = states.get("empty", "blank")
    loading_desc = states.get("loading", "skeleton")
    error_desc = states.get("error", "toast")
    state_val = f"\u7a7a:{_esc(str(empty_desc))} | \u52a0\u8f7d:{_esc(str(loading_desc))} | \u9519\u8bef:{_esc(str(error_desc))}"

    flow = screen.get("flow_context", {})
    prev_ids = flow.get("prev", []) + flow.get("entry_points", [])
    next_ids = flow.get("next", []) + flow.get("exit_points", [])
    prev_str = ", ".join(str(p) for p in prev_ids[:3]) if prev_ids else "\u2013"
    next_str = ", ".join(str(n) for n in next_ids[:3]) if next_ids else "\u2013"
    flow_val = f"\u2190 {prev_str} \u2192 {next_str}"

    return f"""<div class="wf-4d">
  <div class="wf-4d-row"><span class="wf-4d-icon">\U0001f4ca</span><span class="wf-4d-label">Data</span><span class="wf-4d-value">{_esc(data_val)}</span></div>
  <div class="wf-4d-row"><span class="wf-4d-icon">\u26a1</span><span class="wf-4d-label">Action</span><span class="wf-4d-value">{_esc(action_val)}</span></div>
  <div class="wf-4d-row"><span class="wf-4d-icon">\U0001f504</span><span class="wf-4d-label">State</span><span class="wf-4d-value">{state_val}</span></div>
  <div class="wf-4d-row"><span class="wf-4d-icon">\U0001f500</span><span class="wf-4d-label">Flow</span><span class="wf-4d-value">{_esc(flow_val)}</span></div>
</div>"""


# ── Sample data helpers ────────────────────────────────────────────────────

_SAMPLE_VALUES = {
    "string": "\u2591\u2591\u2591\u2591\u2591",
    "text": "\u2591\u2591\u2591\u2591\u2591\u2591\u2591\u2591",
    "enum": "\u25cftag",
    "number": "128",
    "decimal": "\u00a5128.00",
    "integer": "42",
    "date": "2025-03-01",
    "datetime": "2\u5206\u949f\u524d",
    "boolean": "\u2713",
    "file": "\U0001f4ce file.pdf",
    "image": "\U0001f5bc\ufe0f img.png",
}

_INPUT_INDICATORS = {
    "string": "[____]",
    "text": "[====]",
    "enum": "[\u25be]",
    "number": "[###]",
    "decimal": "[###.##]",
    "integer": "[###]",
    "date": "[\U0001f4c5]",
    "datetime": "[\U0001f4c5]",
    "boolean": "[\u2610]",
    "file": "[\U0001f4ce]",
    "image": "[\U0001f5bc\ufe0f]",
}


def _sample_val(field):
    ftype = field.get("type", "string")
    if field.get("display_format") == "currency" or ftype == "decimal":
        return "\u00a5128.00"
    return _SAMPLE_VALUES.get(ftype, "\u2591\u2591\u2591\u2591")


def _input_indicator(field):
    ftype = field.get("type", "string")
    return _INPUT_INDICATORS.get(ftype, "[____]")


# ── Type-specific wireframe templates ─────────────────────────────────────

def _wf_table_headers(fields):
    return "".join(f"<th>{_esc(f.get('label', f.get('name', '')))}</th>" for f in fields[:5])


def _wf_table_row(fields):
    tds = ""
    for f in fields[:5]:
        val = _sample_val(f)
        ftype = f.get("type", "string")
        if ftype == "enum":
            tds += f'<td><span class="wf-tag">{_esc(val)}</span></td>'
        else:
            tds += f"<td>{_esc(val)}</td>"
    return tds


def _wf_readonly_list(screen):
    """MG1: Read-only list."""
    fields = screen.get("data_fields", [])
    filters = screen.get("filters", [])
    toolbar = '<div class="wf-toolbar"><div class="wf-search">\U0001f50d \u641c\u7d22...</div></div>'
    filter_html = ""
    if filters:
        chips = "".join(f'<span class="wf-filter-chip">{_esc(fn)} \u25be</span>' for fn in filters[:4])
        filter_html = f'<div class="wf-filters">{chips}</div>'
    if fields:
        headers = _wf_table_headers(fields)
        rows = "".join(f"<tr>{_wf_table_row(fields)}</tr>" for _ in range(3))
        table = f'<table class="wf-table"><thead><tr>{headers}</tr></thead><tbody>{rows}</tbody></table>'
    else:
        table = '<div class="wf-section">Read-only List</div>'
    return toolbar + filter_html + table + '<div class="wf-pagination">\u2190 1  2  3  ... \u2192</div>'


def _wf_crud_list(screen):
    """MG2-L: CRUD list with search, filters, table, pagination."""
    fields = screen.get("data_fields", [])
    filters = screen.get("filters", [])
    entity = screen.get("entity_name", "")
    toolbar = f'<div class="wf-toolbar"><div class="wf-search">\U0001f50d \u641c\u7d22...</div><button class="wf-btn wf-btn-primary">+ \u65b0\u5efa{_esc(entity)}</button></div>'
    filter_html = ""
    if filters:
        chips = "".join(f'<span class="wf-filter-chip">{_esc(fn)} \u25be</span>' for fn in filters[:4])
        filter_html = f'<div class="wf-filters">{chips}</div>'
    if fields:
        headers = _wf_table_headers(fields) + "<th>\u64cd\u4f5c</th>"
        rows = "".join(f"<tr>{_wf_table_row(fields)}<td>\u00b7\u00b7\u00b7</td></tr>" for _ in range(3))
        table = f'<table class="wf-table"><thead><tr>{headers}</tr></thead><tbody>{rows}</tbody></table>'
    else:
        table = '<div class="wf-section">Table Content</div>'
    return toolbar + filter_html + table + '<div class="wf-pagination">\u2190 1  2  3  ... \u2192</div>'


def _wf_create_form(screen):
    """MG2-C: Create form."""
    fields = screen.get("data_fields", [])
    entity = screen.get("entity_name", "")
    form_fields = ""
    for f in fields[:10]:
        label = f.get("label", f.get("name", ""))
        req_mark = '<span class="wf-form-required">\u2731</span>' if f.get("required") else ""
        indicator = _input_indicator(f)
        ftype = f.get("type", "string")
        inp = f'<div class="wf-form-textarea">{indicator}</div>' if ftype == "text" else f'<div class="wf-form-input">{indicator}</div>'
        form_fields += f'<div class="wf-form-field"><div class="wf-form-label">{_esc(label)} {req_mark}</div>{inp}</div>'
    buttons = f'<div class="wf-form-buttons"><button class="wf-btn wf-btn-secondary">\u53d6\u6d88</button><button class="wf-btn wf-btn-primary">\u521b\u5efa{_esc(entity)}</button></div>'
    return form_fields + buttons if fields else '<div class="wf-section">Create Form</div>'


def _wf_edit_form(screen):
    """MG2-E: Edit form."""
    fields = screen.get("data_fields", [])
    entity = screen.get("entity_name", "")
    form_fields = ""
    for f in fields[:10]:
        label = f.get("label", f.get("name", ""))
        req_mark = '<span class="wf-form-required">\u2731</span>' if f.get("required") else ""
        indicator = _input_indicator(f)
        ftype = f.get("type", "string")
        hint = '<div class="wf-form-hint">(\u56de\u586b)</div>'
        inp = (f'<div class="wf-form-textarea">{indicator}</div>{hint}' if ftype == "text"
               else f'<div class="wf-form-input">{indicator}</div>{hint}')
        form_fields += f'<div class="wf-form-field"><div class="wf-form-label">{_esc(label)} {req_mark}</div>{inp}</div>'
    buttons = f'<div class="wf-form-buttons"><button class="wf-btn wf-btn-secondary">\u53d6\u6d88</button><button class="wf-btn wf-btn-primary">\u4fdd\u5b58{_esc(entity)}</button></div>'
    return form_fields + buttons if fields else '<div class="wf-section">Edit Form</div>'


def _wf_detail(screen):
    """MG2-D: Detail view."""
    fields = screen.get("data_fields", [])
    vo_actions = screen.get("vo_actions", [])
    rows = ""
    for f in fields[:12]:
        label = f.get("label", f.get("name", ""))
        val = _sample_val(f)
        rows += f'<div class="wf-detail-row"><span class="wf-detail-label">{_esc(label)}</span><span class="wf-detail-value">{_esc(val)}</span></div>'
    action_html = ""
    if vo_actions:
        btns = ""
        for a in vo_actions[:4]:
            if isinstance(a, dict):
                style = a.get("style", "ghost")
                label = a.get("label", "")
                api = a.get("api_ref", "")
            else:
                style, label, api = "ghost", str(a), ""
            cls = "wf-btn-primary" if style == "primary" else "wf-btn wf-btn-secondary"
            btns += f'<button class="wf-btn {cls}">{_esc(label)}</button>'
            if api:
                btns += f'<div class="wf-api-ref">\u2193 API: {_esc(api)}</div>'
        action_html = f'<div class="wf-detail-actions"><div class="wf-label">\u2500\u2500\u2500 Actions \u2500\u2500\u2500</div><div class="wf-actions">{btns}</div></div>'
    return (rows + action_html) if fields else '<div class="wf-section">Detail View</div>'


def _wf_state_machine(screen):
    """MG3: State-machine list."""
    fields = screen.get("data_fields", [])
    states = screen.get("states", {})
    vo_actions = screen.get("vo_actions", [])
    state_names = []
    if isinstance(states, dict):
        for k, v in states.items():
            if k not in ("empty", "loading", "error"):
                state_names.append(str(v) if not isinstance(v, dict) else k)
    if not state_names:
        state_names = ["\u5168\u90e8", "\u5f85\u5904\u7406", "\u5df2\u5b8c\u6210"]
    tabs = '<span class="wf-state-tab active">\u5168\u90e8</span>'
    for sn in state_names[:5]:
        tabs += f'<span class="wf-state-tab">{_esc(sn)}</span>'
    state_tabs = f'<div class="wf-state-tabs">{tabs}</div>'
    if fields:
        headers = _wf_table_headers(fields) + "<th>\u64cd\u4f5c</th>"
        rows = ""
        for i in range(3):
            action_cell = ""
            for a in vo_actions[:2]:
                if isinstance(a, dict):
                    alabel = a.get("label", "")
                    api = a.get("api_ref", "")
                else:
                    alabel = str(a)
                    api = ""
                action_cell += f'<button class="wf-btn wf-btn-secondary" style="padding:2px 8px;font-size:10px">{_esc(alabel)}</button> '
                if api:
                    action_cell += f'<div class="wf-transition">\u2192 API: {_esc(api)}</div>'
            if not action_cell:
                action_cell = "\u00b7\u00b7\u00b7"
            rows += f"<tr>{_wf_table_row(fields)}<td>{action_cell}</td></tr>"
        table = f'<table class="wf-table"><thead><tr>{headers}</tr></thead><tbody>{rows}</tbody></table>'
    else:
        table = '<div class="wf-section">State Machine List</div>'
    return state_tabs + table


def _wf_approval(screen):
    """MG4: Approval queue."""
    fields = screen.get("data_fields", [])
    pending_badge = '<div style="text-align:right;margin-bottom:8px"><span class="wf-pending-badge">\u5f85\u5ba1 3 \u4ef6</span></div>'
    cards = ""
    for i in range(2):
        field_summary = ""
        for f in fields[:3]:
            label = f.get("label", f.get("name", ""))
            val = _sample_val(f)
            field_summary += f"{_esc(label)}: {_esc(val)}  "
        placeholder = "\u2591\u2591\u2591 \u2591\u2591\u2591\u2591\u2591 \u2591\u2591"
        card_num = i + 1001
        card_fields = field_summary if field_summary else placeholder
        cards += f"""<div class="wf-approval-card">
  <div class="wf-approval-card-header">#{card_num}</div>
  <div class="wf-approval-card-fields">{card_fields}</div>
  <div class="wf-approval-btns">
    <button class="wf-approval-reject">\u9a73\u56de</button>
    <button class="wf-approval-approve">\u2713 \u901a\u8fc7</button>
  </div>
</div>"""
    return pending_badge + cards


def _wf_default(screen):
    """Default wireframe."""
    fields = screen.get("data_fields", [])
    actions = screen.get("actions", [])
    non_neg = screen.get("non_negotiable", [])
    tasks = screen.get("tasks", [])
    if fields:
        headers = _wf_table_headers(fields)
        rows = "".join(f"<tr>{_wf_table_row(fields)}</tr>" for _ in range(2))
        content = f'<table class="wf-table"><thead><tr>{headers}</tr></thead><tbody>{rows}</tbody></table>'
    else:
        content = '<div class="wf-section">Content Area</div>'
    high_actions = [a for a in actions if isinstance(a, dict) and a.get("frequency") == "\u9ad8"]
    other_actions = [a for a in actions if not isinstance(a, dict) or a.get("frequency") != "\u9ad8"]
    primary_btns = ""
    for a in high_actions[:4]:
        crud = a.get("crud", "R")
        crud_color = {"C": "#4CAF50", "U": "#FF9800", "D": "#F44336", "R": "#78909C"}.get(crud, "#78909C")
        primary_btns += f'<button class="wf-btn wf-btn-primary"><span class="crud-dot" style="background:{crud_color}"></span>{_esc(a.get("label", ""))}</button>'
    secondary_btns = ""
    for a in other_actions[:4]:
        if isinstance(a, dict):
            crud = a.get("crud", "R")
            label = a.get("label", "")
        else:
            crud, label = "R", str(a)
        crud_color = {"C": "#4CAF50", "U": "#FF9800", "D": "#F44336", "R": "#78909C"}.get(crud, "#78909C")
        secondary_btns += f'<button class="wf-btn wf-btn-secondary"><span class="crud-dot" style="background:{crud_color}"></span>{_esc(label)}</button>'
    btns_html = ""
    if primary_btns:
        btns_html += f'<div class="wf-actions">{primary_btns}</div>'
    if secondary_btns:
        btns_html += f'<div class="wf-actions">{secondary_btns}</div>'
    states_html = '<div class="wf-states"><span class="wf-state">Empty</span><span class="wf-state">Loading</span><span class="wf-state">Error</span><span class="wf-state">Success</span></div>'
    constraints_html = ""
    if non_neg:
        constraints_html = '<div class="wf-constraints"><span class="wf-label">Non-negotiable:</span> ' + ", ".join(f"<b>{_esc(n)}</b>" for n in non_neg) + "</div>"
    gate_html = ""
    gate_issues = screen.get("gate_issues", [])
    if gate_issues:
        items = "".join(f'<div class="wf-gate-issue">{_esc(i.get("detail", ""))}</div>' for i in gate_issues[:3])
        gate_html = f'<div class="wf-gate"><span class="wf-label">Quality Gate Issues:</span>{items}</div>'
    return content + btns_html + states_html + constraints_html + gate_html + f'<div class="wf-tasks">{len(tasks)} tasks linked</div>'


def _wf_page(screen, body_html):
    """Wrap body with wireframe page structure."""
    name = screen.get("name", "")
    emo = screen.get("emotion_state", "neutral")
    emo_color = EMOTION_COLORS.get(emo, "#B0BEC5")
    itype = screen.get("interaction_type", "")
    ux_intent = screen.get("ux_intent", "")
    notes = screen.get("notes", "") or screen.get("description", "")
    itype_badge = f'<span class="wf-itype">{_esc(itype)}</span>' if itype else ""
    panel_4d = _build_4d_panel(screen)
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>{WF_CSS}</style></head><body>
<div class="wf-container">
  <div class="wf-header">
    <div class="wf-header-title">{_esc(name)}</div>
    {itype_badge}
    <span class="wf-emo" style="background:{emo_color}22;color:{emo_color}">{_esc(emo)}</span>
  </div>
  <div class="wf-body">
    {f'<div class="wf-intent">UX Intent: {_esc(ux_intent)}</div>' if ux_intent else ''}
    <div class="wf-purpose">{_esc(notes) if notes else 'No description'}</div>
    {body_html}
    {panel_4d}
  </div>
</div>
</body></html>"""


def generate_wireframe(screen):
    """Generate interaction-type-specific wireframe HTML."""
    itype = screen.get("interaction_type", "")
    if itype == "MG1":
        body = _wf_readonly_list(screen)
    elif itype == "MG2-L":
        body = _wf_crud_list(screen)
    elif itype == "MG2-C":
        body = _wf_create_form(screen)
    elif itype == "MG2-E":
        body = _wf_edit_form(screen)
    elif itype == "MG2-D":
        body = _wf_detail(screen)
    elif itype == "MG3":
        body = _wf_state_machine(screen)
    elif itype == "MG4":
        body = _wf_approval(screen)
    else:
        body = _wf_default(screen)
    return _wf_page(screen, body)


# ── Wireframe 6V Tab builders ────────────────────────────────────────────

ZONE_MAP = {
    "MG1": ["header", "filter-chips", "read-only-list", "pagination"],
    "MG2-L": ["header", "search-bar", "filter-chips", "table", "pagination", "action-bar"],
    "MG2-C": ["header", "form-body", "field-group", "action-bar"],
    "MG2-E": ["header", "form-body", "field-group", "action-bar"],
    "MG2-D": ["header", "detail-fields", "action-bar"],
}

BEHAVIOR_DESC = {
    "MG1": ("Read-only List", "Displays a filterable, read-only collection. No create or edit actions. Optimized for scanning and lookup."),
    "MG2-L": ("CRUD List", "Full CRUD list with search, filter, sortable table, pagination, and bulk actions."),
    "MG2-C": ("Create Form", "Guided creation form with typed inputs, validation, and submit/cancel actions."),
    "MG2-E": ("Edit Form", "Pre-filled edit form. Same layout as create but loads existing data for modification."),
    "MG2-D": ("Detail View", "Read-focused detail layout with field-value pairs and contextual actions."),
}


def _build_6v_tabs_json(screen):
    """Return 6V tab content as a dict for JSON embedding in the page."""
    itype = screen.get("interaction_type", "")
    data_fields = screen.get("data_fields", [])
    states = screen.get("states", {})
    flow_ctx = screen.get("flow_context", {})
    emo = screen.get("emotion_state", "neutral")
    emo_color = EMOTION_COLORS.get(emo, "#B0BEC5")
    ux_intent = screen.get("ux_intent", "")
    emo_intensity = screen.get("emotion_intensity", 5)

    # Structure
    zones = ZONE_MAP.get(itype, ["header", "content", "action-bar"])
    zones_html = "".join(f"<li class='wf-zone-item'>{_esc(z)}</li>" for z in zones)
    structure = f"<div class='wf-zone-label'>Interaction type: <b>{_esc(itype or 'unknown')}</b></div><ul class='wf-zone-list'>{zones_html}</ul>"

    # Behavior
    bname, bdesc = BEHAVIOR_DESC.get(itype, (itype or "Custom", "Custom interaction pattern."))
    behavior = f"<div class='wf-beh-name'>{_esc(bname)}</div><p class='wf-beh-desc'>{_esc(bdesc)}</p>"
    if itype:
        behavior += f"<div class='wf-beh-code'>Code: <code>{_esc(itype)}</code></div>"

    # Data
    if data_fields:
        rows = ""
        for df in data_fields:
            mode = "input" if df.get("input_widget") else "display"
            req = "Yes" if df.get("required") else ""
            rows += f"<tr><td>{_esc(df.get('name',''))}</td><td>{_esc(df.get('label',''))}</td><td>{_esc(df.get('type',''))}</td><td>{mode}</td><td>{req}</td></tr>"
        data = f"<table class='wf-field-tbl'><thead><tr><th>Name</th><th>Label</th><th>Type</th><th>Mode</th><th>Req</th></tr></thead><tbody>{rows}</tbody></table>"
    else:
        data = "<p class='wf-empty-hint'>No data fields defined for this screen.</p>"

    # State
    state = ""
    for skey in ["empty", "loading", "error", "success"]:
        sval = states.get(skey, "\u2014")
        state += f"<div class='wf-state-row'><span class='wf-state-key'>{skey}</span><span class='wf-state-val'>{_esc(str(sval))}</span></div>"

    # Flow
    flow_prev = flow_ctx.get("prev", "\u2014")
    flow_next = flow_ctx.get("next", "\u2014")
    entry_pts = flow_ctx.get("entry_points", [])
    exit_pts = flow_ctx.get("exit_points", [])
    flow = f"<div class='wf-flow-row'><b>Prev:</b> {_esc(str(flow_prev))}</div>"
    flow += f"<div class='wf-flow-row'><b>Next:</b> {_esc(str(flow_next))}</div>"
    if entry_pts:
        flow += "<div class='wf-flow-row'><b>Entry points:</b> " + ", ".join(_esc(str(e)) for e in entry_pts) + "</div>"
    if exit_pts:
        flow += "<div class='wf-flow-row'><b>Exit points:</b> " + ", ".join(_esc(str(e)) for e in exit_pts) + "</div>"

    # Emotion
    emotion = f"<div class='wf-emo-detail'>"
    emotion += f"<div class='wf-emo-row'><b>State:</b> <span style='background:{emo_color}22;color:{emo_color};padding:2px 8px;border-radius:4px'>{_esc(emo)}</span></div>"
    emotion += f"<div class='wf-emo-row'><b>Intensity:</b> {emo_intensity}/10</div>"
    if ux_intent:
        emotion += f"<div class='wf-emo-row'><b>UX Intent:</b> {_esc(ux_intent)}</div>"
    # Design hints based on emotion
    hints = {
        "curious": "Use progressive disclosure. Reward exploration with rich previews.",
        "anxious": "Show clear status. Minimize choices. Provide escape routes.",
        "frustrated": "Simplify immediately. Show progress. Offer help.",
        "satisfied": "Maintain momentum. Offer next steps.",
        "confident": "Allow power-user shortcuts. Show advanced options.",
        "confused": "Add contextual help. Use familiar patterns. Reduce cognitive load.",
        "exploring": "Enable discovery. Show relationships. Provide breadcrumbs.",
    }
    hint = hints.get(emo, "")
    if hint:
        emotion += f"<div class='wf-emo-hint'>{_esc(hint)}</div>"
    emotion += "</div>"

    return {"structure": structure, "behavior": behavior, "data": data, "state": state, "flow": flow, "emotion": emotion}


# ── XV Results (load from previous run if available) ──────────────────────

def _load_xv_results():
    xv_path = os.path.join(WF_FEEDBACK_DIR, "xv-review.json")
    xv_data = C.load_json(xv_path)
    if xv_data and "by_screen" in xv_data:
        return xv_data["by_screen"]
    return {}


# ── Main wireframe page renderer ─────────────────────────────────────────

def render_wireframe_page():
    """Render the wireframe tab with tree + preview split layout."""
    op_lines, tasks, role_map, gate_issues, vo_map, api_map = load_wireframe_data()
    if not op_lines:
        return _placeholder_page("wireframe", "\u7ebf\u6846 Review - No Data")

    all_screens = build_screens_with_context(op_lines, tasks, role_map, gate_issues, vo_map, api_map)
    if not all_screens:
        return _placeholder_page("wireframe", "\u7ebf\u6846 Review - No Screens")

    screen_map = {s["id"]: s for s in all_screens}
    feedback = load_wf_feedback()
    xv_results = _load_xv_results()

    # Build tree data grouped by operation_line
    tree_data = []
    for ol in op_lines:
        ol_id = ol["id"]
        ol_name = ol.get("name", ol_id)
        ol_screens = []
        for node in ol.get("nodes", []):
            for s in node.get("screens", []):
                sid = s["id"]
                sc = screen_map.get(sid, {})
                fb_s = feedback.get("screens", {}).get(sid, {})
                xv_issues = xv_results.get(sid, [])
                xv_err = sum(1 for i in xv_issues if i.get("severity") == "error")
                xv_warn = sum(1 for i in xv_issues if i.get("severity") == "warning")
                ol_screens.append({
                    "id": sid,
                    "name": sc.get("name", s.get("name", sid)),
                    "itype": sc.get("interaction_type", ""),
                    "emotion": sc.get("emotion_state", "neutral"),
                    "gate_count": len(sc.get("gate_issues", [])),
                    "status": fb_s.get("status", "pending"),
                    "pin_count": len(fb_s.get("pins", [])),
                    "xv_err": xv_err,
                    "xv_warn": xv_warn,
                })
        if ol_screens:
            tree_data.append({"id": ol_id, "name": ol_name, "screens": ol_screens})

    # Pre-build 6V tabs for all screens
    all_6v = {}
    for s in all_screens:
        all_6v[s["id"]] = _build_6v_tabs_json(s)

    # Screen data JSON for client-side rendering
    screens_json = json.dumps({s["id"]: s for s in all_screens}, ensure_ascii=False, default=str)
    tree_json = json.dumps(tree_data, ensure_ascii=False)
    feedback_json = json.dumps(feedback, ensure_ascii=False)
    sixv_json = json.dumps(all_6v, ensure_ascii=False)
    emo_colors_json = json.dumps(EMOTION_COLORS, ensure_ascii=False)

    total = len(all_screens)
    fb_screens = feedback.get("screens", {})
    reviewed = sum(1 for s in all_screens if fb_screens.get(s["id"], {}).get("status") in ("approved", "revision"))

    nav = render_nav("wireframe")

    return f"""<!DOCTYPE html>
<html lang="zh"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>\u7ebf\u6846 Review - Review Hub</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,system-ui,'Segoe UI',sans-serif;background:#f8fafc;height:100vh;overflow:hidden}}
.wf-main-header{{background:#fff;border-bottom:1px solid #e2e8f0;padding:10px 24px;display:flex;align-items:center;gap:16px}}
.wf-main-header h1{{font-size:16px;font-weight:600;color:#1e293b}}
.wf-main-header .meta{{font-size:12px;color:#64748b}}
.wf-progress{{width:120px;height:4px;background:#e2e8f0;border-radius:2px;overflow:hidden}}
.wf-progress-bar{{height:100%;background:#10b981;border-radius:2px;transition:width .3s}}
.wf-submit-btn{{margin-left:auto;padding:7px 20px;background:#334155;color:#fff;border:none;border-radius:6px;font-size:13px;cursor:pointer;font-weight:500}}
.wf-submit-btn:hover{{background:#1e293b}}
.wf-submit-btn:disabled{{background:#94a3b8;cursor:not-allowed}}
/* Layout */
.wf-layout{{display:flex;height:calc(100vh - 104px)}}
.wf-tree-panel{{width:300px;min-width:240px;max-width:400px;background:#fff;border-right:1px solid #e2e8f0;display:flex;flex-direction:column;overflow:hidden}}
.wf-tree-search{{padding:8px 12px;border-bottom:1px solid #e2e8f0}}
.wf-tree-search input{{width:100%;padding:6px 10px;border:1px solid #e2e8f0;border-radius:6px;font-size:12px;background:#f8fafc}}
.wf-tree-body{{flex:1;overflow-y:auto;padding:4px 0}}
.wf-tree-group{{margin-bottom:2px}}
.wf-tree-group-header{{display:flex;align-items:center;gap:6px;padding:8px 12px;cursor:pointer;font-size:12px;font-weight:600;color:#475569;user-select:none}}
.wf-tree-group-header:hover{{background:#f1f5f9}}
.wf-tree-group-chevron{{font-size:10px;color:#94a3b8;transition:transform .15s}}
.wf-tree-group.collapsed .wf-tree-group-chevron{{transform:rotate(-90deg)}}
.wf-tree-group.collapsed .wf-tree-group-items{{display:none}}
.wf-tree-item{{display:flex;align-items:center;gap:6px;padding:6px 12px 6px 28px;cursor:pointer;font-size:12px;color:#475569;transition:background .1s;border-left:3px solid transparent}}
.wf-tree-item:hover{{background:#f1f5f9}}
.wf-tree-item.active{{background:#eff6ff;border-left-color:#3b82f6;color:#1e40af;font-weight:500}}
.wf-tree-item.status-approved{{border-left-color:#10b981}}
.wf-tree-item.status-revision{{border-left-color:#f59e0b}}
.wf-tree-itype{{font-size:9px;padding:1px 5px;border-radius:3px;background:#e8eaf6;color:#5c6bc0;font-weight:600;flex-shrink:0}}
.wf-tree-emo{{width:8px;height:8px;border-radius:50%;flex-shrink:0}}
.wf-tree-badges{{display:flex;gap:3px;margin-left:auto;flex-shrink:0}}
.wf-tree-badge{{font-size:9px;padding:1px 4px;border-radius:3px;font-weight:600}}
.wf-tree-badge.gate{{background:#ffebee;color:#c62828}}
.wf-tree-badge.pins{{background:#fff3bf;color:#92400e}}
.wf-tree-badge.xv-err{{background:#ffebee;color:#c62828}}
.wf-tree-badge.xv-warn{{background:#fff8e1;color:#f57f17}}
.wf-tree-name{{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
/* Preview panel */
.wf-preview-panel{{flex:1;display:flex;flex-direction:column;overflow:hidden}}
.wf-preview-empty{{display:flex;align-items:center;justify-content:center;height:100%;color:#94a3b8;font-size:15px}}
.wf-preview-content{{display:none;flex:1;flex-direction:column;overflow:hidden}}
.wf-preview-content.visible{{display:flex}}
.wf-preview-area{{flex:1;position:relative;background:#e9ecef;overflow:auto}}
.wf-preview-area iframe{{width:100%;height:100%;border:none;min-height:500px}}
.wf-pin{{position:absolute;width:22px;height:22px;background:#fbbf24;color:#1e293b;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;cursor:pointer;transform:translate(-50%,-50%);z-index:5;box-shadow:0 2px 4px rgba(0,0,0,.2)}}
.wf-pin:hover{{transform:translate(-50%,-50%) scale(1.15)}}
.wf-click-hint{{position:absolute;top:8px;left:50%;transform:translateX(-50%);background:rgba(0,0,0,.6);color:#fff;padding:4px 14px;border-radius:6px;font-size:11px;pointer-events:none;z-index:10}}
/* Bottom panel: 6V tabs */
.wf-bottom-panel{{border-top:1px solid #e2e8f0;background:#fff}}
.wf-tab-bar{{display:flex;gap:0;border-bottom:1px solid #e2e8f0;padding:0 12px;background:#f8fafc}}
.wf-tab-btn{{padding:7px 12px;border:none;background:none;font-size:11px;font-weight:600;color:#94a3b8;cursor:pointer;border-bottom:2px solid transparent;margin-bottom:-1px;text-transform:uppercase;letter-spacing:.3px;white-space:nowrap}}
.wf-tab-btn:hover{{color:#475569}}
.wf-tab-btn.active{{color:#3b82f6;border-bottom-color:#3b82f6}}
.wf-tab-pane{{display:none;padding:10px 14px;font-size:12px;max-height:200px;overflow-y:auto}}
.wf-tab-pane.active{{display:block}}
.wf-zone-label{{color:#475569;margin-bottom:6px}}
.wf-zone-list{{list-style:none;display:flex;flex-wrap:wrap;gap:5px;margin:0;padding:0}}
.wf-zone-item{{background:#e0f2fe;color:#0369a1;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:500}}
.wf-beh-name{{font-size:14px;font-weight:600;color:#475569;margin-bottom:4px}}
.wf-beh-desc{{color:#64748b;margin:0 0 6px 0;line-height:1.4}}
.wf-beh-code{{font-size:11px;color:#94a3b8}}
.wf-beh-code code{{background:#f1f5f9;padding:1px 5px;border-radius:3px;color:#475569}}
.wf-field-tbl{{width:100%;border-collapse:collapse;font-size:11px}}
.wf-field-tbl th{{background:#f8fafc;text-align:left;padding:4px 6px;border-bottom:1px solid #e2e8f0;font-weight:600;color:#475569}}
.wf-field-tbl td{{padding:3px 6px;border-bottom:1px solid #f1f5f9;color:#475569}}
.wf-empty-hint{{color:#94a3b8;font-style:italic}}
.wf-state-row{{display:flex;gap:10px;padding:4px 0;border-bottom:1px solid #f1f5f9}}
.wf-state-key{{font-weight:600;color:#475569;text-transform:capitalize;min-width:60px}}
.wf-state-val{{color:#64748b}}
.wf-flow-row{{padding:4px 0;color:#475569;line-height:1.4}}
.wf-emo-detail{{line-height:1.6}}
.wf-emo-row{{padding:3px 0}}
.wf-emo-hint{{margin-top:8px;padding:8px;background:#fdf4ff;border-radius:4px;color:#7c3aed;font-size:12px;line-height:1.4}}
/* Side review panel */
.wf-review-side{{width:320px;min-width:260px;border-left:1px solid #e2e8f0;background:#fff;display:flex;flex-direction:column;overflow:hidden}}
.wf-review-side.hidden{{display:none}}
.wf-review-header{{padding:12px 16px;border-bottom:1px solid #e2e8f0;font-size:13px;font-weight:600;color:#1e293b;display:flex;align-items:center;gap:8px}}
.wf-review-header .sid{{font-size:11px;color:#64748b;font-weight:400}}
.wf-status-toggle{{display:flex;gap:6px;padding:12px 16px;border-bottom:1px solid #f1f5f9}}
.wf-status-btn{{flex:1;padding:8px;border:2px solid #e2e8f0;border-radius:6px;background:#fff;cursor:pointer;font-size:12px;text-align:center;transition:all .12s}}
.wf-status-btn.approved.selected{{border-color:#10b981;background:#dcfce7;color:#065f46}}
.wf-status-btn.revision.selected{{border-color:#f59e0b;background:#fef3c7;color:#92400e}}
.wf-pins-list{{flex:1;overflow-y:auto;padding:8px 16px}}
.wf-pin-item{{padding:8px 10px;border:1px solid #e2e8f0;border-radius:6px;margin-bottom:6px;font-size:12px}}
.wf-pin-item-header{{display:flex;align-items:center;gap:6px;margin-bottom:4px}}
.wf-pin-num{{width:18px;height:18px;background:#fbbf24;color:#1e293b;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:9px;font-weight:700;flex-shrink:0}}
.wf-pin-item textarea{{width:100%;border:1px solid #e2e8f0;border-radius:4px;padding:5px;font-size:12px;resize:vertical;min-height:36px;font-family:inherit}}
.wf-pin-item select{{border:1px solid #e2e8f0;border-radius:4px;padding:3px 6px;font-size:11px;background:#fff}}
.wf-pin-del{{color:#cbd5e1;cursor:pointer;font-size:14px;margin-left:auto}}
.wf-pin-del:hover{{color:#ef4444}}
.wf-add-hint{{text-align:center;color:#94a3b8;font-size:12px;padding:12px}}
</style></head><body>
{nav}
<div class="wf-main-header">
  <h1>\u7ebf\u6846 Review</h1>
  <div class="meta">Round {feedback.get('round', 1)} &middot; {reviewed}/{total} reviewed</div>
  <div class="wf-progress"><div class="wf-progress-bar" style="width:{reviewed/total*100 if total else 0:.0f}%"></div></div>
  <button class="wf-submit-btn" id="wfSubmitBtn" onclick="wfSubmit()">Submit Feedback</button>
</div>
<div class="wf-layout">
  <!-- Left: Screen Tree -->
  <div class="wf-tree-panel">
    <div class="wf-tree-search"><input type="text" id="wfTreeSearch" placeholder="Search screens..." oninput="wfFilterTree(this.value)"></div>
    <div class="wf-tree-body" id="wfTreeBody"></div>
  </div>
  <!-- Center: Preview -->
  <div class="wf-preview-panel">
    <div class="wf-preview-empty" id="wfPreviewEmpty">Select a screen from the tree to preview</div>
    <div class="wf-preview-content" id="wfPreviewContent">
      <div class="wf-preview-area" id="wfPreviewArea">
        <div class="wf-click-hint">Click to add feedback pin</div>
      </div>
      <div class="wf-bottom-panel">
        <div class="wf-tab-bar" id="wfTabBar">
          <button class="wf-tab-btn active" onclick="wfSwitchTab('structure',this)">Structure</button>
          <button class="wf-tab-btn" onclick="wfSwitchTab('behavior',this)">Behavior</button>
          <button class="wf-tab-btn" onclick="wfSwitchTab('data',this)">Data</button>
          <button class="wf-tab-btn" onclick="wfSwitchTab('state',this)">State</button>
          <button class="wf-tab-btn" onclick="wfSwitchTab('flow',this)">Flow</button>
          <button class="wf-tab-btn" onclick="wfSwitchTab('emotion',this)">Emotion</button>
        </div>
        <div id="wf-tab-structure" class="wf-tab-pane active"></div>
        <div id="wf-tab-behavior" class="wf-tab-pane"></div>
        <div id="wf-tab-data" class="wf-tab-pane"></div>
        <div id="wf-tab-state" class="wf-tab-pane"></div>
        <div id="wf-tab-flow" class="wf-tab-pane"></div>
        <div id="wf-tab-emotion" class="wf-tab-pane"></div>
      </div>
    </div>
  </div>
  <!-- Right: Review / Pins -->
  <div class="wf-review-side hidden" id="wfReviewSide">
    <div class="wf-review-header"><span id="wfReviewTitle">Review</span><span class="sid" id="wfReviewSid"></span></div>
    <div class="wf-status-toggle">
      <button class="wf-status-btn approved" id="wfBtnApproved" onclick="wfSetStatus('approved')">Approved</button>
      <button class="wf-status-btn revision" id="wfBtnRevision" onclick="wfSetStatus('revision')">Revision</button>
    </div>
    <div class="wf-pins-list" id="wfPinsList"></div>
    <div class="wf-add-hint">Click on wireframe to pin feedback</div>
  </div>
</div>
<script>
const TREE_DATA={tree_json};
const ALL_SCREENS={screens_json};
const SIXV={sixv_json};
const EMO_COLORS={emo_colors_json};
let feedback={feedback_json};
let currentSid=null;

// ── Tree rendering ──
function wfRenderTree(filter){{
  const body=document.getElementById('wfTreeBody');
  body.innerHTML='';
  const fl=(filter||'').toLowerCase();
  TREE_DATA.forEach(ol=>{{
    const screens=ol.screens.filter(s=>!fl||s.name.toLowerCase().includes(fl)||s.id.toLowerCase().includes(fl)||s.itype.toLowerCase().includes(fl));
    if(!screens.length)return;
    const group=document.createElement('div');
    group.className='wf-tree-group';
    const header=document.createElement('div');
    header.className='wf-tree-group-header';
    header.innerHTML='<span class="wf-tree-group-chevron">&#9662;</span>'+escH(ol.name)+' <span style="color:#94a3b8;font-weight:400;font-size:11px">('+screens.length+')</span>';
    header.onclick=()=>group.classList.toggle('collapsed');
    group.appendChild(header);
    const items=document.createElement('div');
    items.className='wf-tree-group-items';
    screens.forEach(s=>{{
      const item=document.createElement('div');
      item.className='wf-tree-item'+(s.id===currentSid?' active':'')+(s.status!=='pending'?' status-'+s.status:'');
      item.dataset.sid=s.id;
      let badges='';
      if(s.gate_count)badges+='<span class="wf-tree-badge gate">'+s.gate_count+'</span>';
      if(s.xv_err)badges+='<span class="wf-tree-badge xv-err">'+s.xv_err+'XV</span>';
      else if(s.xv_warn)badges+='<span class="wf-tree-badge xv-warn">'+s.xv_warn+'XV</span>';
      if(s.pin_count)badges+='<span class="wf-tree-badge pins">'+s.pin_count+'</span>';
      const emoColor=EMO_COLORS[s.emotion]||'#B0BEC5';
      item.innerHTML='<span class="wf-tree-emo" style="background:'+emoColor+'"></span>'
        +'<span class="wf-tree-name">'+escH(s.name)+'</span>'
        +(s.itype?'<span class="wf-tree-itype">'+escH(s.itype)+'</span>':'')
        +'<span class="wf-tree-badges">'+badges+'</span>';
      item.onclick=()=>wfSelectScreen(s.id);
      items.appendChild(item);
    }});
    group.appendChild(items);
    body.appendChild(group);
  }});
}}

function wfFilterTree(val){{wfRenderTree(val)}}

function escH(s){{return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}}

// ── Screen selection ──
function wfSelectScreen(sid){{
  currentSid=sid;
  // Update tree highlights
  document.querySelectorAll('.wf-tree-item').forEach(el=>{{
    el.classList.toggle('active',el.dataset.sid===sid);
  }});
  // Show preview
  document.getElementById('wfPreviewEmpty').style.display='none';
  const content=document.getElementById('wfPreviewContent');
  content.classList.add('visible');
  // Load wireframe in iframe
  const area=document.getElementById('wfPreviewArea');
  area.querySelectorAll('iframe,.wf-pin').forEach(el=>el.remove());
  const iframe=document.createElement('iframe');
  iframe.src='/wireframe/screen/'+sid;
  iframe.onload=()=>{{
    try{{
      iframe.style.height=iframe.contentDocument.documentElement.scrollHeight+'px';
      iframe.contentDocument.addEventListener('click',(e)=>{{
        const x=((e.pageX)/iframe.contentDocument.documentElement.scrollWidth*100).toFixed(1);
        const y=((e.pageY)/iframe.contentDocument.documentElement.scrollHeight*100).toFixed(1);
        wfAddPin(parseFloat(x),parseFloat(y));
      }});
      iframe.contentDocument.body.style.cursor='crosshair';
    }}catch(err){{}}
  }};
  area.appendChild(iframe);
  // Load 6V tabs
  const sixv=SIXV[sid]||{{}};
  ['structure','behavior','data','state','flow','emotion'].forEach(tab=>{{
    document.getElementById('wf-tab-'+tab).innerHTML=sixv[tab]||'';
  }});
  // Reset to structure tab
  document.querySelectorAll('.wf-tab-btn').forEach((b,i)=>b.classList.toggle('active',i===0));
  document.querySelectorAll('.wf-tab-pane').forEach((p,i)=>p.classList.toggle('active',i===0));
  // Show review panel
  const side=document.getElementById('wfReviewSide');
  side.classList.remove('hidden');
  const sc=ALL_SCREENS[sid]||{{}};
  document.getElementById('wfReviewTitle').textContent=sc.name||sid;
  document.getElementById('wfReviewSid').textContent=sid;
  // Load feedback
  const fb=feedback.screens[sid]||{{status:'pending',pins:[]}};
  wfCurrentStatus=fb.status;
  wfCurrentPins=JSON.parse(JSON.stringify(fb.pins||[]));
  wfRenderStatus();
  wfRenderPins();
}}

let wfCurrentStatus='pending';
let wfCurrentPins=[];

function wfRenderStatus(){{
  document.getElementById('wfBtnApproved').classList.toggle('selected',wfCurrentStatus==='approved');
  document.getElementById('wfBtnRevision').classList.toggle('selected',wfCurrentStatus==='revision');
}}

function wfSetStatus(s){{
  wfCurrentStatus=s;
  wfRenderStatus();
  wfSaveFeedback();
}}

function wfRenderPins(){{
  // Dots on preview
  const area=document.getElementById('wfPreviewArea');
  area.querySelectorAll('.wf-pin').forEach(el=>el.remove());
  wfCurrentPins.forEach((p,i)=>{{
    const dot=document.createElement('div');
    dot.className='wf-pin';
    dot.textContent=i+1;
    dot.style.left=p.x+'%';
    dot.style.top=p.y+'%';
    dot.onclick=(e)=>{{e.stopPropagation();wfHighlightPin(i)}};
    area.appendChild(dot);
  }});
  // List
  const list=document.getElementById('wfPinsList');
  list.innerHTML='';
  wfCurrentPins.forEach((p,i)=>{{
    const div=document.createElement('div');
    div.className='wf-pin-item';
    div.id='wf-pin-item-'+i;
    div.innerHTML='<div class="wf-pin-item-header">'
      +'<span class="wf-pin-num">'+(i+1)+'</span>'
      +'<select onchange="wfUpdateCategory('+i+',this.value)">'
      +'<option value="experience-map"'+(p.category==='experience-map'?' selected':'')+'>Flow/Structure</option>'
      +'<option value="product-map"'+(p.category==='product-map'?' selected':'')+'>Feature/Task</option>'
      +'<option value="concept"'+(p.category==='concept'?' selected':'')+'>Concept</option>'
      +'</select>'
      +'<span class="wf-pin-del" onclick="wfDeletePin('+i+')">&times;</span>'
      +'</div>'
      +'<textarea placeholder="Describe the issue..." oninput="wfUpdateComment('+i+',this.value)">'+escH(p.comment||'')+'</textarea>';
    list.appendChild(div);
  }});
}}

function wfAddPin(x,y){{
  wfCurrentPins.push({{id:Date.now(),x:x,y:y,comment:'',category:'experience-map'}});
  if(wfCurrentStatus==='pending'||wfCurrentStatus==='approved')wfSetStatus('revision');
  wfRenderPins();
  wfSaveFeedback();
  setTimeout(()=>{{
    const items=document.querySelectorAll('.wf-pin-item textarea');
    if(items.length)items[items.length-1].focus();
  }},50);
}}

function wfUpdateComment(idx,comment){{wfCurrentPins[idx].comment=comment;wfSaveFeedback()}}
function wfUpdateCategory(idx,cat){{wfCurrentPins[idx].category=cat;wfSaveFeedback()}}
function wfDeletePin(idx){{
  wfCurrentPins.splice(idx,1);
  wfRenderPins();
  wfSaveFeedback();
  if(wfCurrentPins.length===0&&wfCurrentStatus==='revision')wfSetStatus('pending');
}}
function wfHighlightPin(idx){{
  const el=document.getElementById('wf-pin-item-'+idx);
  if(el){{el.scrollIntoView({{behavior:'smooth'}});el.style.background='#fef3c7';setTimeout(()=>el.style.background='',1200)}}
}}

let wfSaveTimer=null;
function wfSaveFeedback(){{
  if(!currentSid)return;
  clearTimeout(wfSaveTimer);
  wfSaveTimer=setTimeout(()=>{{
    feedback.screens[currentSid]={{status:wfCurrentStatus,pins:wfCurrentPins}};
    fetch('/api/wireframe/feedback',{{
      method:'POST',
      headers:{{'Content-Type':'application/json'}},
      body:JSON.stringify({{screen_id:currentSid,status:wfCurrentStatus,pins:wfCurrentPins}})
    }});
    // Update tree item status
    document.querySelectorAll('.wf-tree-item').forEach(el=>{{
      if(el.dataset.sid===currentSid){{
        el.classList.remove('status-approved','status-revision');
        if(wfCurrentStatus!=='pending')el.classList.add('status-'+wfCurrentStatus);
      }}
    }});
  }},300);
}}

function wfSwitchTab(tabId,btn){{
  document.querySelectorAll('.wf-tab-pane').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('.wf-tab-btn').forEach(b=>b.classList.remove('active'));
  document.getElementById('wf-tab-'+tabId).classList.add('active');
  btn.classList.add('active');
}}

function wfSubmit(){{
  if(!confirm('Submit wireframe feedback?'))return;
  fetch('/api/wireframe/submit',{{method:'POST'}}).then(r=>r.json()).then(d=>{{
    if(d.ok){{
      const btn=document.getElementById('wfSubmitBtn');
      btn.disabled=true;btn.textContent='Submitted!';
    }}
  }});
}}

// Init
wfRenderTree();
</script></body></html>"""


def render_wireframe_html(screen_id):
    """Generate wireframe HTML for a single screen (used by iframe src)."""
    op_lines, tasks, role_map, gate_issues, vo_map, api_map = load_wireframe_data()
    if not op_lines:
        return "<h2>No wireframe data</h2>"
    all_screens = build_screens_with_context(op_lines, tasks, role_map, gate_issues, vo_map, api_map)
    screen_map = {s["id"]: s for s in all_screens}
    screen = screen_map.get(screen_id)
    if not screen:
        return "<h2>Screen not found</h2>"
    return generate_wireframe(screen)


# ── UI Tab ─────────────────────────────────────────────────────────────────────

UI_DIR = os.path.join(BASE, "ui-design")
UI_FEEDBACK_DIR = os.path.join(BASE, "ui-review")
C.ensure_dir(UI_FEEDBACK_DIR)
UI_FEEDBACK_PATH = os.path.join(UI_FEEDBACK_DIR, "review-feedback.json")


def load_ui_spec():
    """Load ui-design-spec.json and normalize screens to list format."""
    raw = C.load_json(os.path.join(UI_DIR, "ui-design-spec.json")) or {}
    screens = raw.get("screens", [])
    if isinstance(screens, dict):
        normalized = []
        for sid, sdata in screens.items():
            if isinstance(sdata, dict):
                if "id" not in sdata:
                    sdata["id"] = sid
                normalized.append(sdata)
        raw["screens"] = normalized
    return raw


def load_ui_experience_map():
    """Load experience-map for design rationale."""
    op_lines, screen_index, loaded = C.load_experience_map(BASE)
    if loaded:
        return C.build_screen_by_id_from_lines(op_lines)
    return {}


def load_ui_stitch_index():
    return C.load_json(os.path.join(UI_DIR, "stitch-index.json")) or {}


def load_ui_feedback():
    fb = C.load_json(UI_FEEDBACK_PATH)
    if fb:
        return fb
    return {"round": 1, "submitted_at": None, "screens": {}}


def get_ui_stitch_html(screen_id):
    """Read Stitch-generated HTML for a screen."""
    path = os.path.join(UI_DIR, "stitch", f"{screen_id}.html")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return f.read()
    return None


def get_ui_preview_html(screen_id, spec):
    """Extract preview HTML from preview/ files or generate skeleton."""
    # Try stitch HTML first
    stitch_dir = os.path.join(UI_DIR, "stitch")
    if os.path.isdir(stitch_dir):
        stitch_path = os.path.join(stitch_dir, f"{screen_id}.html")
        if os.path.exists(stitch_path):
            with open(stitch_path, encoding="utf-8") as f:
                return f.read()
    # Try preview directory
    preview_dir = os.path.join(UI_DIR, "preview")
    if os.path.isdir(preview_dir):
        # Try filename match first (e.g., S001.html)
        exact_path = os.path.join(preview_dir, f"{screen_id}.html")
        if os.path.exists(exact_path):
            with open(exact_path, encoding="utf-8") as f:
                return f.read()
        # Try content match
        for fname in os.listdir(preview_dir):
            if fname.endswith(".html") and fname != "index.html":
                fpath = os.path.join(preview_dir, fname)
                with open(fpath, encoding="utf-8") as f:
                    content = f.read()
                if screen_id in content:
                    return content
    # Fallback: generate skeleton from spec
    screen_spec = None
    for s in spec.get("screens", []):
        if s.get("id") == screen_id:
            screen_spec = s
            break
    if not screen_spec:
        return None
    return _generate_ui_skeleton(screen_spec, spec.get("design_tokens", {}))


def _generate_ui_skeleton(screen, tokens):
    """Generate a simple skeleton HTML from screen spec."""
    primary = tokens.get("colors", {}).get("primary", "#111827")
    bg = tokens.get("colors", {}).get("background", "#FFFFFF")
    radius = tokens.get("border_radius", "6px")
    name = screen.get("name", "Unknown")
    sections = screen.get("sections", [])
    layout = screen.get("layout", "")
    states = screen.get("states", {})

    section_html = ""
    for sec in sections:
        section_html += f'<div style="background:#f3f4f6;border-radius:{radius};padding:24px;margin:8px 0;min-height:60px;display:flex;align-items:center;justify-content:center;color:#6b7280;font-size:14px">{_esc(str(sec))}</div>'

    states_html = ""
    for state_name, state_desc in states.items():
        color = "#10b981" if state_name == "empty" else "#f59e0b" if state_name == "loading" else "#ef4444"
        states_html += f'<div style="display:inline-block;background:{color}20;color:{color};padding:4px 12px;border-radius:12px;font-size:12px;margin:4px">{_esc(str(state_name))}: {_esc(str(state_desc))}</div>'

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
body{{margin:0;padding:24px;font-family:-apple-system,system-ui,sans-serif;background:{bg}}}
</style></head><body>
<div style="max-width:800px;margin:0 auto">
<div style="font-size:11px;color:#9ca3af;margin-bottom:8px">LAYOUT: {_esc(layout)}</div>
<div style="font-size:20px;font-weight:600;color:{primary};margin-bottom:16px">{_esc(name)}</div>
{section_html}
<div style="margin-top:16px">{states_html}</div>
</div>
</body></html>"""


def render_ui_screen_html(screen_id):
    """Serve preview HTML for iframe embedding."""
    spec = load_ui_spec()
    stitch = get_ui_stitch_html(screen_id)
    if stitch:
        return stitch
    preview = get_ui_preview_html(screen_id, spec)
    if preview:
        return preview
    return "<h2>No preview available</h2>"


def render_ui_page():
    """Render the UI tab with tree + preview split layout."""
    spec = load_ui_spec()
    screens = spec.get("screens", [])
    if not screens:
        return _placeholder_page("ui", "UI Review - No Data")

    sm = load_ui_experience_map()
    stitch_index = load_ui_stitch_index()
    feedback = load_ui_feedback()
    fb_screens = feedback.get("screens", {})

    # Build tree data grouped by role
    role_groups = {}
    for s in screens:
        role = s.get("role", "未分配")
        role_groups.setdefault(role, []).append(s)

    tree_data = []
    for role in sorted(role_groups.keys()):
        role_screens = []
        for s in role_groups[role]:
            sid = s.get("id", "")
            fb_s = fb_screens.get(sid, {})
            has_stitch = os.path.exists(os.path.join(UI_DIR, "stitch", f"{sid}.html"))
            itype = s.get("interaction_type", "")
            role_screens.append({
                "id": sid,
                "name": s.get("name", sid),
                "itype": itype,
                "status": fb_s.get("status", "pending"),
                "pin_count": len(fb_s.get("pins", [])),
                "has_stitch": has_stitch,
            })
        if role_screens:
            tree_data.append({"id": role, "name": role, "screens": role_screens})

    # Screen detail data for side panel
    screen_details = {}
    for s in screens:
        sid = s.get("id", "")
        sm_screen = sm.get(sid, {})
        screen_details[sid] = {
            "name": s.get("name", ""),
            "role": s.get("role", ""),
            "layout": s.get("layout", ""),
            "interaction_type": s.get("interaction_type", ""),
            "audience_type": s.get("audience_type", ""),
            "sections": s.get("sections", []),
            "states": s.get("states", {}),
            "primary_purpose": sm_screen.get("primary_purpose", s.get("primary_purpose", "")),
        }

    total = len(screens)
    reviewed = sum(1 for s in screens if fb_screens.get(s.get("id", ""), {}).get("status") in ("approved", "revision"))

    tree_json = json.dumps(tree_data, ensure_ascii=False)
    details_json = json.dumps(screen_details, ensure_ascii=False, default=str)
    feedback_json = json.dumps(feedback, ensure_ascii=False)

    nav = render_nav("ui")

    return f"""<!DOCTYPE html>
<html lang="zh"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>UI Review - Review Hub</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,system-ui,'Segoe UI',sans-serif;background:#f8fafc;height:100vh;overflow:hidden}}
.ui-main-header{{background:#fff;border-bottom:1px solid #e2e8f0;padding:10px 24px;display:flex;align-items:center;gap:16px}}
.ui-main-header h1{{font-size:16px;font-weight:600;color:#1e293b}}
.ui-main-header .meta{{font-size:12px;color:#64748b}}
.ui-progress{{width:120px;height:4px;background:#e2e8f0;border-radius:2px;overflow:hidden}}
.ui-progress-bar{{height:100%;background:#10b981;border-radius:2px;transition:width .3s}}
.ui-submit-btn{{margin-left:auto;padding:7px 20px;background:#334155;color:#fff;border:none;border-radius:6px;font-size:13px;cursor:pointer;font-weight:500}}
.ui-submit-btn:hover{{background:#1e293b}}
.ui-submit-btn:disabled{{background:#94a3b8;cursor:not-allowed}}
/* Layout */
.ui-layout{{display:flex;height:calc(100vh - 104px)}}
.ui-tree-panel{{width:300px;min-width:240px;max-width:400px;background:#fff;border-right:1px solid #e2e8f0;display:flex;flex-direction:column;overflow:hidden}}
.ui-tree-search{{padding:8px 12px;border-bottom:1px solid #e2e8f0}}
.ui-tree-search input{{width:100%;padding:6px 10px;border:1px solid #e2e8f0;border-radius:6px;font-size:12px;background:#f8fafc}}
.ui-tree-body{{flex:1;overflow-y:auto;padding:4px 0}}
.ui-tree-group{{margin-bottom:2px}}
.ui-tree-group-header{{display:flex;align-items:center;gap:6px;padding:8px 12px;cursor:pointer;font-size:12px;font-weight:600;color:#475569;user-select:none}}
.ui-tree-group-header:hover{{background:#f1f5f9}}
.ui-tree-group-chevron{{font-size:10px;color:#94a3b8;transition:transform .15s}}
.ui-tree-group.collapsed .ui-tree-group-chevron{{transform:rotate(-90deg)}}
.ui-tree-group.collapsed .ui-tree-group-items{{display:none}}
.ui-tree-item{{display:flex;align-items:center;gap:6px;padding:6px 12px 6px 28px;cursor:pointer;font-size:12px;color:#475569;transition:background .1s;border-left:3px solid transparent}}
.ui-tree-item:hover{{background:#f1f5f9}}
.ui-tree-item.active{{background:#eff6ff;border-left-color:#3b82f6;color:#1e40af;font-weight:500}}
.ui-tree-item.status-approved{{border-left-color:#10b981}}
.ui-tree-item.status-revision{{border-left-color:#f59e0b}}
.ui-tree-itype{{font-size:9px;padding:1px 5px;border-radius:3px;background:#e8eaf6;color:#5c6bc0;font-weight:600;flex-shrink:0}}
.ui-tree-badges{{display:flex;gap:3px;margin-left:auto;flex-shrink:0}}
.ui-tree-badge{{font-size:9px;padding:1px 4px;border-radius:3px;font-weight:600}}
.ui-tree-badge.pins{{background:#fff3bf;color:#92400e}}
.ui-tree-badge.stitch{{background:#ede9fe;color:#7c3aed}}
.ui-tree-name{{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
/* Preview panel */
.ui-preview-panel{{flex:1;display:flex;flex-direction:column;overflow:hidden}}
.ui-preview-empty{{display:flex;align-items:center;justify-content:center;height:100%;color:#94a3b8;font-size:15px}}
.ui-preview-content{{display:none;flex:1;flex-direction:column;overflow:hidden}}
.ui-preview-content.visible{{display:flex}}
.ui-preview-area{{flex:1;position:relative;background:#e9ecef;overflow:auto}}
.ui-preview-area iframe{{width:100%;height:100%;border:none;min-height:500px}}
.ui-pin{{position:absolute;width:22px;height:22px;background:#fbbf24;color:#1e293b;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;cursor:pointer;transform:translate(-50%,-50%);z-index:5;box-shadow:0 2px 4px rgba(0,0,0,.2)}}
.ui-pin:hover{{transform:translate(-50%,-50%) scale(1.15)}}
.ui-click-hint{{position:absolute;top:8px;left:50%;transform:translateX(-50%);background:rgba(0,0,0,.6);color:#fff;padding:4px 14px;border-radius:6px;font-size:11px;pointer-events:none;z-index:10}}
/* Detail bar */
.ui-detail-bar{{border-top:1px solid #e2e8f0;background:#fff;padding:10px 16px;font-size:12px;color:#475569;max-height:120px;overflow-y:auto}}
.ui-detail-bar dt{{font-weight:600;color:#334155;display:inline}}
.ui-detail-bar dd{{display:inline;margin:0 12px 0 4px;color:#64748b}}
/* Side review panel */
.ui-review-side{{width:320px;min-width:260px;border-left:1px solid #e2e8f0;background:#fff;display:flex;flex-direction:column;overflow:hidden}}
.ui-review-side.hidden{{display:none}}
.ui-review-header{{padding:12px 16px;border-bottom:1px solid #e2e8f0;font-size:13px;font-weight:600;color:#1e293b;display:flex;align-items:center;gap:8px}}
.ui-review-header .sid{{font-size:11px;color:#64748b;font-weight:400}}
.ui-status-toggle{{display:flex;gap:6px;padding:12px 16px;border-bottom:1px solid #f1f5f9}}
.ui-status-btn{{flex:1;padding:8px;border:2px solid #e2e8f0;border-radius:6px;background:#fff;cursor:pointer;font-size:12px;text-align:center;transition:all .12s}}
.ui-status-btn.approved.selected{{border-color:#10b981;background:#dcfce7;color:#065f46}}
.ui-status-btn.revision.selected{{border-color:#f59e0b;background:#fef3c7;color:#92400e}}
.ui-pins-list{{flex:1;overflow-y:auto;padding:8px 16px}}
.ui-pin-item{{padding:8px 10px;border:1px solid #e2e8f0;border-radius:6px;margin-bottom:6px;font-size:12px}}
.ui-pin-item-header{{display:flex;align-items:center;gap:6px;margin-bottom:4px}}
.ui-pin-num{{width:18px;height:18px;background:#fbbf24;color:#1e293b;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:9px;font-weight:700;flex-shrink:0}}
.ui-pin-item textarea{{width:100%;border:1px solid #e2e8f0;border-radius:4px;padding:5px;font-size:12px;resize:vertical;min-height:36px;font-family:inherit}}
.ui-pin-del{{color:#cbd5e1;cursor:pointer;font-size:14px;margin-left:auto}}
.ui-pin-del:hover{{color:#ef4444}}
.ui-add-hint{{text-align:center;color:#94a3b8;font-size:12px;padding:12px}}
</style></head><body>
{nav}
<div class="ui-main-header">
  <h1>UI Review</h1>
  <div class="meta">Round {feedback.get('round', 1)} &middot; {reviewed}/{total} reviewed</div>
  <div class="ui-progress"><div class="ui-progress-bar" style="width:{reviewed/total*100 if total else 0:.0f}%"></div></div>
  <button class="ui-submit-btn" id="uiSubmitBtn" onclick="uiSubmit()">Submit Feedback</button>
</div>
<div class="ui-layout">
  <!-- Left: Screen Tree -->
  <div class="ui-tree-panel">
    <div class="ui-tree-search"><input type="text" id="uiTreeSearch" placeholder="Search screens..." oninput="uiFilterTree(this.value)"></div>
    <div class="ui-tree-body" id="uiTreeBody"></div>
  </div>
  <!-- Center: Preview -->
  <div class="ui-preview-panel">
    <div class="ui-preview-empty" id="uiPreviewEmpty">Select a screen from the tree to preview</div>
    <div class="ui-preview-content" id="uiPreviewContent">
      <div class="ui-preview-area" id="uiPreviewArea">
        <div class="ui-click-hint">Click to add feedback pin</div>
      </div>
      <div class="ui-detail-bar" id="uiDetailBar"></div>
    </div>
  </div>
  <!-- Right: Review / Pins -->
  <div class="ui-review-side hidden" id="uiReviewSide">
    <div class="ui-review-header"><span id="uiReviewTitle">Review</span><span class="sid" id="uiReviewSid"></span></div>
    <div class="ui-status-toggle">
      <button class="ui-status-btn approved" id="uiBtnApproved" onclick="uiSetStatus('approved')">Approved</button>
      <button class="ui-status-btn revision" id="uiBtnRevision" onclick="uiSetStatus('revision')">Revision</button>
    </div>
    <div class="ui-pins-list" id="uiPinsList"></div>
    <div class="ui-add-hint">Click on preview to pin feedback</div>
  </div>
</div>
<script>
const UI_TREE={tree_json};
const UI_DETAILS={details_json};
let uiFeedback={feedback_json};
let uiCurrentSid=null;
let uiCurrentStatus='pending';
let uiCurrentPins=[];

function uiEscH(s){{return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}}

// ── Tree rendering ──
function uiRenderTree(filter){{
  const body=document.getElementById('uiTreeBody');
  body.innerHTML='';
  const fl=(filter||'').toLowerCase();
  UI_TREE.forEach(role=>{{
    const screens=role.screens.filter(s=>!fl||s.name.toLowerCase().includes(fl)||s.id.toLowerCase().includes(fl)||s.itype.toLowerCase().includes(fl));
    if(!screens.length)return;
    const group=document.createElement('div');
    group.className='ui-tree-group';
    const header=document.createElement('div');
    header.className='ui-tree-group-header';
    header.innerHTML='<span class="ui-tree-group-chevron">&#9662;</span>'+uiEscH(role.name)+' <span style="color:#94a3b8;font-weight:400;font-size:11px">('+screens.length+')</span>';
    header.onclick=()=>group.classList.toggle('collapsed');
    group.appendChild(header);
    const items=document.createElement('div');
    items.className='ui-tree-group-items';
    screens.forEach(s=>{{
      const item=document.createElement('div');
      item.className='ui-tree-item'+(s.id===uiCurrentSid?' active':'')+(s.status!=='pending'?' status-'+s.status:'');
      item.dataset.sid=s.id;
      let badges='';
      if(s.has_stitch)badges+='<span class="ui-tree-badge stitch">S</span>';
      if(s.pin_count)badges+='<span class="ui-tree-badge pins">'+s.pin_count+'</span>';
      item.innerHTML='<span class="ui-tree-name">'+uiEscH(s.name)+'</span>'
        +(s.itype?'<span class="ui-tree-itype">'+uiEscH(s.itype)+'</span>':'')
        +'<span class="ui-tree-badges">'+badges+'</span>';
      item.onclick=()=>uiSelectScreen(s.id);
      items.appendChild(item);
    }});
    group.appendChild(items);
    body.appendChild(group);
  }});
}}

function uiFilterTree(val){{uiRenderTree(val)}}

// ── Screen selection ──
function uiSelectScreen(sid){{
  uiCurrentSid=sid;
  document.querySelectorAll('.ui-tree-item').forEach(el=>{{
    el.classList.toggle('active',el.dataset.sid===sid);
  }});
  document.getElementById('uiPreviewEmpty').style.display='none';
  const content=document.getElementById('uiPreviewContent');
  content.classList.add('visible');
  // Load preview in iframe
  const area=document.getElementById('uiPreviewArea');
  area.querySelectorAll('iframe,.ui-pin').forEach(el=>el.remove());
  const iframe=document.createElement('iframe');
  iframe.src='/ui/screen/'+sid;
  iframe.onload=()=>{{
    try{{
      iframe.style.height=iframe.contentDocument.documentElement.scrollHeight+'px';
      iframe.contentDocument.addEventListener('click',(e)=>{{
        const x=((e.pageX)/iframe.contentDocument.documentElement.scrollWidth*100).toFixed(1);
        const y=((e.pageY)/iframe.contentDocument.documentElement.scrollHeight*100).toFixed(1);
        uiAddPin(parseFloat(x),parseFloat(y));
      }});
      iframe.contentDocument.body.style.cursor='crosshair';
    }}catch(err){{}}
  }};
  area.appendChild(iframe);
  // Detail bar
  const d=UI_DETAILS[sid]||{{}};
  let detail='';
  if(d.layout)detail+='<dt>Layout</dt><dd>'+uiEscH(d.layout)+'</dd>';
  if(d.interaction_type)detail+='<dt>Type</dt><dd>'+uiEscH(d.interaction_type)+'</dd>';
  if(d.audience_type)detail+='<dt>Audience</dt><dd>'+uiEscH(d.audience_type)+'</dd>';
  if(d.primary_purpose)detail+='<dt>Purpose</dt><dd>'+uiEscH(d.primary_purpose)+'</dd>';
  if(d.sections&&d.sections.length)detail+='<dt>Sections</dt><dd>'+d.sections.map(s=>uiEscH(s)).join(', ')+'</dd>';
  document.getElementById('uiDetailBar').innerHTML=detail?'<dl>'+detail+'</dl>':'';
  // Show review panel
  const side=document.getElementById('uiReviewSide');
  side.classList.remove('hidden');
  document.getElementById('uiReviewTitle').textContent=d.name||sid;
  document.getElementById('uiReviewSid').textContent=sid;
  // Load feedback
  const fb=(uiFeedback.screens||{{}})[sid]||{{status:'pending',pins:[]}};
  uiCurrentStatus=fb.status;
  uiCurrentPins=JSON.parse(JSON.stringify(fb.pins||[]));
  uiRenderStatus();
  uiRenderPins();
}}

function uiRenderStatus(){{
  document.getElementById('uiBtnApproved').classList.toggle('selected',uiCurrentStatus==='approved');
  document.getElementById('uiBtnRevision').classList.toggle('selected',uiCurrentStatus==='revision');
}}

function uiSetStatus(s){{
  uiCurrentStatus=s;
  uiRenderStatus();
  uiSaveFeedback();
}}

function uiRenderPins(){{
  const area=document.getElementById('uiPreviewArea');
  area.querySelectorAll('.ui-pin').forEach(el=>el.remove());
  uiCurrentPins.forEach((p,i)=>{{
    const dot=document.createElement('div');
    dot.className='ui-pin';
    dot.textContent=i+1;
    dot.style.left=p.x+'%';
    dot.style.top=p.y+'%';
    dot.onclick=(e)=>{{e.stopPropagation();uiHighlightPin(i)}};
    area.appendChild(dot);
  }});
  const list=document.getElementById('uiPinsList');
  list.innerHTML='';
  uiCurrentPins.forEach((p,i)=>{{
    const div=document.createElement('div');
    div.className='ui-pin-item';
    div.id='ui-pin-item-'+i;
    div.innerHTML='<div class="ui-pin-item-header">'
      +'<span class="ui-pin-num">'+(i+1)+'</span>'
      +'<span class="ui-pin-del" onclick="uiDeletePin('+i+')">&times;</span>'
      +'</div>'
      +'<textarea placeholder="Describe the issue..." oninput="uiUpdateComment('+i+',this.value)">'+uiEscH(p.comment||'')+'</textarea>';
    list.appendChild(div);
  }});
}}

function uiAddPin(x,y){{
  uiCurrentPins.push({{id:Date.now(),x:x,y:y,comment:''}});
  if(uiCurrentStatus==='pending'||uiCurrentStatus==='approved')uiSetStatus('revision');
  uiRenderPins();
  uiSaveFeedback();
  setTimeout(()=>{{
    const items=document.querySelectorAll('.ui-pin-item textarea');
    if(items.length)items[items.length-1].focus();
  }},50);
}}

function uiUpdateComment(idx,comment){{uiCurrentPins[idx].comment=comment;uiSaveFeedback()}}
function uiDeletePin(idx){{
  uiCurrentPins.splice(idx,1);
  uiRenderPins();
  uiSaveFeedback();
  if(uiCurrentPins.length===0&&uiCurrentStatus==='revision')uiSetStatus('pending');
}}
function uiHighlightPin(idx){{
  const el=document.getElementById('ui-pin-item-'+idx);
  if(el){{el.scrollIntoView({{behavior:'smooth'}});el.style.background='#fef3c7';setTimeout(()=>el.style.background='',1200)}}
}}

let uiSaveTimer=null;
function uiSaveFeedback(){{
  if(!uiCurrentSid)return;
  clearTimeout(uiSaveTimer);
  uiSaveTimer=setTimeout(()=>{{
    if(!uiFeedback.screens)uiFeedback.screens={{}};
    uiFeedback.screens[uiCurrentSid]={{status:uiCurrentStatus,pins:uiCurrentPins}};
    fetch('/api/ui/feedback',{{
      method:'POST',
      headers:{{'Content-Type':'application/json'}},
      body:JSON.stringify({{screen_id:uiCurrentSid,status:uiCurrentStatus,pins:uiCurrentPins}})
    }});
    document.querySelectorAll('.ui-tree-item').forEach(el=>{{
      if(el.dataset.sid===uiCurrentSid){{
        el.classList.remove('status-approved','status-revision');
        if(uiCurrentStatus!=='pending')el.classList.add('status-'+uiCurrentStatus);
      }}
    }});
  }},300);
}}

function uiSubmit(){{
  if(!confirm('Submit UI feedback?'))return;
  fetch('/api/ui/submit',{{method:'POST'}}).then(r=>r.json()).then(d=>{{
    if(d.ok){{
      const btn=document.getElementById('uiSubmitBtn');
      btn.disabled=true;btn.textContent='Submitted!';
    }}
  }});
}}

// Init
uiRenderTree();
</script></body></html>"""


# ── Spec Tab ───────────────────────────────────────────────────────────────────

SPEC_FEEDBACK_DIR = os.path.join(BASE, "project-forge")
C.ensure_dir(SPEC_FEEDBACK_DIR)
SPEC_FEEDBACK_PATH = os.path.join(SPEC_FEEDBACK_DIR, "spec-review-feedback.json")


def load_spec_feedback():
    fb = C.load_json(SPEC_FEEDBACK_PATH)
    return fb if fb else {"round": 1, "submitted_at": None, "nodes": {}}


def load_spec_tree():
    """Transform design.json files from project-forge into a mind map tree."""
    forge_dir = os.path.join(BASE, "project-forge/sub-projects")
    if not os.path.isdir(forge_dir):
        return _node("root", "No spec data", "error")

    sp_children = []

    for name in sorted(os.listdir(forge_dir)):
        design_path = os.path.join(forge_dir, name, "design.json")
        design = C.load_json(design_path)
        if not design:
            continue

        sp_type = design.get("type", "unknown")
        sp_nodes = []

        # Data models branch
        dm_nodes = []
        for dm in design.get("data_models", []):
            table = dm.get("table", "unknown")
            source = dm.get("source_entity", "")
            field_nodes = []
            for f in dm.get("fields", []):
                fname = f.get("name", "")
                ftype = f.get("type", "")
                constraints = " ".join(f.get("constraints", []))
                ntype = "field-pk" if "PK" in constraints or "PRIMARY" in constraints else "field-required" if f.get("required") else "default"
                field_nodes.append(_node(f"f_{table}_{fname}", f"{fname}: {ftype}", ntype, constraints))

            # State machine
            sm = dm.get("state_machine", {})
            if sm:
                sm_nodes = []
                for transition in sm.get("transitions", []):
                    fr = transition.get("from", "")
                    to = transition.get("to", "")
                    trigger = transition.get("trigger", "")
                    sm_nodes.append(_node(f"sm_{table}_{fr}_{to}", f"{fr} \u2192 {to}", "transition", trigger))
                if sm_nodes:
                    field_nodes.append(_node(f"sm_{table}", "\u72b6\u6001\u673a", "state-machine", "", sm_nodes))

            # Indexes
            for idx in dm.get("indexes", []):
                idx_name = idx.get("name", "")
                idx_cols = ", ".join(idx.get("columns", []))
                field_nodes.append(_node(f"idx_{table}_{idx_name}", f"\u7d22\u5f15: {idx_cols}", "info"))

            label = f"{table}" + (f" [{source}]" if source else "")
            dm_nodes.append(_node(f"dm_{table}", label, "entity", "", field_nodes))

        if dm_nodes:
            sp_nodes.append(_node(f"dms_{name}", "\u6570\u636e\u6a21\u578b", "group", "", dm_nodes))

        # Endpoints branch
        ep_nodes = []
        for ep in design.get("endpoints", []):
            method = ep.get("method", "")
            path = ep.get("path", "")
            source = ep.get("source_api", "")
            label = f"{method} {path}" + (f" [{source}]" if source else "")
            ep_nodes.append(_node(f"ep_{name}_{method}_{path}", label, "api", ep.get("description", "")))

        if ep_nodes:
            sp_nodes.append(_node(f"eps_{name}", "API \u63a5\u53e3", "api-group", "", ep_nodes))

        # Pages branch (frontend)
        page_nodes = []
        for pg in design.get("pages", []):
            route = pg.get("route", "")
            pg_name = pg.get("name", route)
            page_nodes.append(_node(f"pg_{name}_{route}", pg_name, "concept", route))

        if page_nodes:
            sp_nodes.append(_node(f"pgs_{name}", "\u9875\u9762\u8def\u7531", "group", "", page_nodes))

        # Middleware
        mw_nodes = []
        for mw in design.get("middleware", []):
            mw_name = mw if isinstance(mw, str) else mw.get("name", "")
            mw_nodes.append(_node(f"mw_{name}_{mw_name}", mw_name, "mechanism"))

        if mw_nodes:
            sp_nodes.append(_node(f"mws_{name}", "\u4e2d\u95f4\u4ef6", "group", "", mw_nodes))

        # Tasks branch
        task_nodes = []
        for t in design.get("tasks", []):
            tid = t.get("id", "")
            tname = t.get("name", tid)
            status = t.get("status", "pending")
            tag = "\u25a1" if status == "pending" else "\u2713"
            task_nodes.append(_node(f"t_{name}_{tid}", f"{tid} {tname} [{tag}]", "task"))

        if task_nodes:
            sp_nodes.append(_node(f"tasks_{name}", f"\u4efb\u52a1 ({len(task_nodes)})", "task-group", "", task_nodes))

        type_label = {"backend": "\u540e\u7aef", "frontend": "\u524d\u7aef", "mobile": "\u79fb\u52a8\u7aef"}.get(sp_type, sp_type)
        sp_children.append(_node(f"sp_{name}", f"{name} ({type_label})", "role", "", sp_nodes))

    if not sp_children:
        return _node("root", "No spec data", "error")

    tree = _node("root", "\u5f00\u53d1\u89c4\u683c", "root", "", sp_children)
    _auto_group_children(tree)
    return tree


def render_spec_page():
    tree = load_spec_tree()
    feedback = load_spec_feedback()
    categories = ["Data Model", "API", "Task", "Dependency", "General"]
    extra_css = """
.mm-node[data-type="entity"] .label{background:#dbeafe;color:#1e40af;font-weight:600;border-color:#93c5fd}
.mm-node[data-type="api-group"] .label{background:#eff6ff;color:#1d4ed8;font-weight:600}
.mm-node[data-type="api"] .label{background:#eff6ff;color:#1d4ed8;font-size:12px}
.mm-node[data-type="state-machine"] .label{background:#f0fdfa;color:#115e59;border-color:#99f6e4}
.mm-node[data-type="transition"] .label{background:#f0fdf4;color:#166534;font-size:12px}
.mm-node[data-type="field-pk"] .label{background:#fef3c7;color:#92400e;font-weight:600}
.mm-node[data-type="field-required"] .label{background:#fff;color:#334155}
"""
    return render_mindmap_page(tree, feedback, "\u89c4\u683c", "spec", categories, extra_css)


# ── URL Router ────────────────────────────────────────────────────────────────

class ReviewHubHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path.rstrip("/")
        if path == "" or path == "/":
            self._respond(render_home())
        elif path == "/concept":
            self._respond(render_concept_page())
        elif path == "/map":
            self._respond(render_map_page())
        elif path == "/data-model":
            self._respond(render_datamodel_page())
        elif path == "/wireframe":
            self._respond(render_wireframe_page())
        elif path.startswith("/wireframe/screen/"):
            screen_id = path.split("/wireframe/screen/")[1]
            self._respond(render_wireframe_html(screen_id))
        elif path == "/ui":
            self._respond(render_ui_page())
        elif path.startswith("/ui/screen/"):
            screen_id = path.split("/ui/screen/")[1]
            self._respond(render_ui_screen_html(screen_id))
        elif path == "/spec":
            self._respond(render_spec_page())
        elif path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
        else:
            self._respond_404()

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path.rstrip("/")
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}

        # Feedback save: /api/<tab>/feedback
        if path == "/api/concept/feedback":
            fb = load_concept_feedback()
            fb["nodes"] = body
            C.write_json(CONCEPT_FEEDBACK_PATH, fb)
            self._respond_json({"ok": True})
        elif path == "/api/concept/submit":
            fb = load_concept_feedback()
            fb["submitted_at"] = C.now_iso()
            C.write_json(CONCEPT_FEEDBACK_PATH, fb)
            self._respond_json({"ok": True})
        elif path == "/api/map/feedback":
            fb = load_map_feedback()
            fb["nodes"] = body
            C.write_json(MAP_FEEDBACK_PATH, fb)
            self._respond_json({"ok": True})
        elif path == "/api/map/submit":
            fb = load_map_feedback()
            fb["submitted_at"] = C.now_iso()
            C.write_json(MAP_FEEDBACK_PATH, fb)
            self._respond_json({"ok": True})
        elif path == "/api/data-model/feedback":
            fb = load_dm_feedback()
            fb["nodes"] = body
            C.write_json(DM_FEEDBACK_PATH, fb)
            self._respond_json({"ok": True})
        elif path == "/api/data-model/submit":
            fb = load_dm_feedback()
            fb["submitted_at"] = C.now_iso()
            C.write_json(DM_FEEDBACK_PATH, fb)
            self._respond_json({"ok": True})
        elif path == "/api/wireframe/feedback":
            fb = load_wf_feedback()
            sid = body.get("screen_id")
            if sid:
                fb["screens"][sid] = {
                    "status": body.get("status", "pending"),
                    "pins": body.get("pins", []),
                }
            C.write_json(WF_FEEDBACK_PATH, fb)
            self._respond_json({"ok": True})
        elif path == "/api/wireframe/submit":
            fb = load_wf_feedback()
            fb["submitted_at"] = C.now_iso()
            C.write_json(WF_FEEDBACK_PATH, fb)
            self._respond_json({"ok": True})
        elif path == "/api/ui/feedback":
            fb = load_ui_feedback()
            sid = body.get("screen_id")
            if sid:
                fb["screens"][sid] = {
                    "status": body.get("status", "pending"),
                    "pins": body.get("pins", []),
                }
            C.write_json(UI_FEEDBACK_PATH, fb)
            self._respond_json({"ok": True})
        elif path == "/api/ui/submit":
            fb = load_ui_feedback()
            fb["submitted_at"] = C.now_iso()
            C.write_json(UI_FEEDBACK_PATH, fb)
            self._respond_json({"ok": True})
        elif path == "/api/spec/feedback":
            fb = load_spec_feedback()
            fb["nodes"] = body
            C.write_json(SPEC_FEEDBACK_PATH, fb)
            self._respond_json({"ok": True})
        elif path == "/api/spec/submit":
            fb = load_spec_feedback()
            fb["submitted_at"] = C.now_iso()
            C.write_json(SPEC_FEEDBACK_PATH, fb)
            self._respond_json({"ok": True})
        else:
            self._respond_404()

    def _respond(self, html, code=200):
        data = html.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _respond_json(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _respond_404(self):
        self._respond("<h1>404 Not Found</h1>", 404)

    def log_message(self, fmt, *a):
        pass


# ── Server startup ────────────────────────────────────────────────────────────

def main():
    C.kill_other_review_servers(PORT)

    server = http.server.HTTPServer((HOST, PORT), ReviewHubHandler)
    url = f"http://{HOST}:{PORT}"
    print(f"Review Hub started: {url}")
    print(f"Reading:  {BASE}")
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
