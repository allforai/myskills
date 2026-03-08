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
.zoom-info{{font-size:11px;color:#94a3b8;min-width:40px;text-align:center}}
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
        badge.textContent='\\u2713';
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


def render_concept_page():
    return _placeholder_page("concept", "概念 Review")


def render_map_page():
    return _placeholder_page("map", "地图 Review")


def render_datamodel_page():
    return _placeholder_page("data-model", "数据模型 Review")


def render_wireframe_page():
    return _placeholder_page("wireframe", "线框 Review")


def render_ui_page():
    return _placeholder_page("ui", "UI Review")


def render_spec_page():
    return _placeholder_page("spec", "规格 Review")


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
        elif path == "/ui":
            self._respond(render_ui_page())
        elif path == "/spec":
            self._respond(render_spec_page())
        else:
            self._respond_404()

    def do_POST(self):
        # Will be implemented in Task 8
        pass

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
