#!/usr/bin/env python3
"""Wireframe Review Server — low-fidelity structural review before ui-design.

Reads experience-map.json (operation_lines, screens, actions, emotions) and
serves a wireframe review interface. Reviewers validate IA structure, screen
flows, and feature completeness BEFORE investing in visual design.

Feedback is categorized by route target:
  - product-map: missing/excess features, wrong task decomposition
  - experience-map: flow issues, wrong screen structure
  - concept: fundamental product direction issues

Output: .allforai/wireframe-review/review-feedback.json

Usage:
    python3 wireframe_review_server.py <BASE_PATH> [--port 18902] [--host localhost]
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
PORT = int(args.get("port", "18902"))
HOST = args.get("host", "localhost")
NO_OPEN = args.get("no-open", "false").lower() in ("true", "1", "yes")

WF_DIR = os.path.join(BASE, "wireframe-review")
C.ensure_dir(WF_DIR)
FEEDBACK_PATH = os.path.join(WF_DIR, "review-feedback.json")

# ── Load data ─────────────────────────────────────────────────────────────────

def load_data():
    """Load all data needed for wireframe rendering."""
    op_lines, screen_index, loaded = C.load_experience_map(BASE)
    if not loaded:
        print("ERROR: experience-map.json is required", file=sys.stderr)
        sys.exit(1)

    inv = C.require_json(
        os.path.join(BASE, "product-map/task-inventory.json"),
        "task-inventory.json"
    )
    tasks = {t["id"]: t for t in inv["tasks"]}

    roles = C.load_role_profiles_full(BASE)
    role_map = {r["id"]: r["name"] for r in roles}

    gate = C.load_interaction_gate(BASE)
    gate_issues = {}
    if gate:
        for lr in gate.get("lines", []):
            for issue in lr.get("issues", []):
                nid = issue.get("node", "")
                gate_issues.setdefault(nid, []).append(issue)

    return op_lines, tasks, roles, role_map, gate_issues


def build_screens_with_context(op_lines, tasks, role_map, gate_issues):
    """Build screen list with full context for wireframe rendering."""
    screens = []
    for ol in op_lines:
        for node in ol.get("nodes", []):
            nid = node["id"]
            for s in node.get("screens", []):
                sid = s["id"]
                # Determine role from tasks
                screen_role = ""
                for tid in s.get("tasks", []):
                    task = tasks.get(tid)
                    if task and not screen_role:
                        screen_role = role_map.get(task["owner_role"], "")

                screens.append({
                    "id": sid,
                    "name": s.get("name", ""),
                    "module": s.get("module", ""),
                    "notes": s.get("notes", ""),
                    "tasks": s.get("tasks", []),
                    "actions": s.get("actions", []),
                    "non_negotiable": s.get("non_negotiable", []),
                    "role": screen_role,
                    "operation_line": ol["id"],
                    "operation_line_name": ol.get("name", ol["id"]),
                    "node_id": nid,
                    "emotion_state": node.get("emotion_state", "neutral"),
                    "emotion_intensity": node.get("emotion_intensity", 5),
                    "ux_intent": node.get("ux_intent", ""),
                    "gate_issues": gate_issues.get(nid, []),
                })
    return screens


def load_feedback():
    fb = C.load_json(FEEDBACK_PATH)
    if fb:
        return fb
    return {"round": 1, "submitted_at": None, "screens": {}}


def save_feedback(fb):
    C.write_json(FEEDBACK_PATH, fb)


# ── Wireframe HTML generation ────────────────────────────────────────────────

EMOTION_COLORS = {
    "curious": "#4FC3F7", "anxious": "#FF8A65", "satisfied": "#81C784",
    "frustrated": "#E57373", "neutral": "#B0BEC5", "exploring": "#64B5F6",
    "confident": "#66BB6A", "confused": "#FFB74D",
}


def generate_wireframe(screen):
    """Generate a low-fidelity wireframe HTML for a screen."""
    name = screen["name"]
    actions = screen.get("actions", [])
    notes = screen.get("notes", "")
    emo = screen.get("emotion_state", "neutral")
    emo_color = EMOTION_COLORS.get(emo, "#B0BEC5")
    ux_intent = screen.get("ux_intent", "")
    non_neg = screen.get("non_negotiable", [])
    tasks = screen.get("tasks", [])

    high_actions = [a for a in actions if a.get("frequency") == "高"]
    other_actions = [a for a in actions if a.get("frequency") != "高"]

    # Build action buttons (gray wireframe style)
    primary_btns = ""
    for a in high_actions[:4]:
        crud = a.get("crud", "R")
        crud_color = {"C": "#4CAF50", "U": "#FF9800", "D": "#F44336", "R": "#78909C"}.get(crud, "#78909C")
        primary_btns += f'<button class="wf-btn wf-btn-primary"><span class="crud-dot" style="background:{crud_color}"></span>{_esc(a["label"])}</button>'

    secondary_btns = ""
    for a in other_actions[:4]:
        crud = a.get("crud", "R")
        crud_color = {"C": "#4CAF50", "U": "#FF9800", "D": "#F44336", "R": "#78909C"}.get(crud, "#78909C")
        secondary_btns += f'<button class="wf-btn wf-btn-secondary"><span class="crud-dot" style="background:{crud_color}"></span>{_esc(a["label"])}</button>'

    # Non-negotiable constraints
    constraints_html = ""
    if non_neg:
        constraints_html = '<div class="wf-constraints"><span class="wf-label">Non-negotiable:</span> ' + ", ".join(f"<b>{_esc(n)}</b>" for n in non_neg) + "</div>"

    # Gate issues
    gate_html = ""
    gate_issues = screen.get("gate_issues", [])
    if gate_issues:
        items = "".join(f'<div class="wf-gate-issue">{_esc(i.get("detail", ""))}</div>' for i in gate_issues[:3])
        gate_html = f'<div class="wf-gate"><span class="wf-label">Quality Gate Issues:</span>{items}</div>'

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
body{{margin:0;padding:24px;font-family:-apple-system,system-ui,sans-serif;background:#f8f9fa;color:#333}}
.wf-container{{max-width:480px;margin:0 auto;background:#fff;border:2px solid #dee2e6;border-radius:4px;overflow:hidden}}
.wf-header{{background:#e9ecef;padding:12px 16px;border-bottom:2px solid #dee2e6;display:flex;align-items:center;gap:8px}}
.wf-header-title{{font-size:14px;font-weight:600;color:#495057;flex:1}}
.wf-emo{{font-size:11px;padding:2px 8px;border-radius:10px;font-weight:500}}
.wf-body{{padding:16px}}
.wf-purpose{{font-size:13px;color:#6c757d;margin-bottom:16px;padding:8px;background:#f8f9fa;border-left:3px solid #adb5bd;border-radius:0 4px 4px 0}}
.wf-section{{background:#f1f3f5;border:1px dashed #adb5bd;border-radius:4px;padding:16px;margin:8px 0;min-height:48px;display:flex;align-items:center;justify-content:center;color:#868e96;font-size:13px}}
.wf-actions{{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0}}
.wf-btn{{padding:8px 16px;border-radius:4px;font-size:13px;cursor:default;display:flex;align-items:center;gap:6px;border:none}}
.wf-btn-primary{{background:#dee2e6;color:#495057;font-weight:600;border:2px solid #adb5bd}}
.wf-btn-secondary{{background:#f8f9fa;color:#6c757d;border:1px dashed #ced4da}}
.crud-dot{{width:8px;height:8px;border-radius:50%;flex-shrink:0}}
.wf-states{{margin-top:12px;display:flex;gap:8px;flex-wrap:wrap}}
.wf-state{{font-size:11px;padding:4px 8px;border-radius:4px;background:#f8f9fa;color:#868e96;border:1px solid #e9ecef}}
.wf-tasks{{font-size:11px;color:#adb5bd;margin-top:12px}}
.wf-constraints{{font-size:12px;color:#e65100;background:#fff3e0;padding:8px;border-radius:4px;margin-top:8px}}
.wf-gate{{margin-top:8px}}
.wf-gate-issue{{font-size:12px;color:#c62828;background:#ffebee;padding:4px 8px;border-radius:4px;margin-top:4px}}
.wf-label{{font-size:11px;font-weight:600;color:#666}}
.wf-intent{{font-size:12px;color:#5c6bc0;background:#e8eaf6;padding:6px 8px;border-radius:4px;margin-bottom:12px}}
</style></head><body>
<div class="wf-container">
  <div class="wf-header">
    <div class="wf-header-title">{_esc(name)}</div>
    <span class="wf-emo" style="background:{emo_color}22;color:{emo_color}">{_esc(emo)}</span>
  </div>
  <div class="wf-body">
    {f'<div class="wf-intent">UX Intent: {_esc(ux_intent)}</div>' if ux_intent else ''}
    <div class="wf-purpose">{_esc(notes) if notes else 'No description'}</div>
    <div class="wf-section">Content Area</div>
    {f'<div class="wf-actions">{primary_btns}</div>' if primary_btns else ''}
    {f'<div class="wf-actions">{secondary_btns}</div>' if secondary_btns else ''}
    <div class="wf-states">
      <span class="wf-state">Empty</span>
      <span class="wf-state">Loading</span>
      <span class="wf-state">Error</span>
      <span class="wf-state">Success</span>
    </div>
    {constraints_html}
    {gate_html}
    <div class="wf-tasks">{len(tasks)} tasks linked</div>
  </div>
</div>
</body></html>"""


def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


# ── Dashboard rendering ──────────────────────────────────────────────────────

def _render_card(s, feedback):
    """Render a single screen card."""
    sid = s["id"]
    name = s["name"]
    role = s.get("role", "")
    emo = s.get("emotion_state", "neutral")
    emo_color = EMOTION_COLORS.get(emo, "#B0BEC5")
    actions = s.get("actions", [])
    ol_name = s.get("operation_line_name", "")
    journey = s.get("operation_line", "")
    gate_count = len(s.get("gate_issues", []))

    fb = feedback.get("screens", {}).get(sid, {})
    status = fb.get("status", "pending")
    pin_count = len(fb.get("pins", []))

    status_badge = {
        "pending": '<span class="badge pending">Pending</span>',
        "approved": '<span class="badge approved">Approved</span>',
        "revision": '<span class="badge revision">Revision</span>',
    }.get(status, '<span class="badge pending">Pending</span>')

    action_summary = f"{len([a for a in actions if a.get('frequency') == '高'])}H + {len([a for a in actions if a.get('frequency') != '高'])}L"
    pin_indicator = f'<span class="pin-count">{pin_count} pins</span>' if pin_count else ''
    gate_indicator = f'<span class="gate-warn">{gate_count} issues</span>' if gate_count else ''

    return f"""
    <a href="/screen/{sid}" class="card" data-role="{_esc(role)}" data-status="{status}" data-journey="{_esc(journey)}">
      <div class="card-header">
        <span class="card-title">{_esc(name)}</span>
        {status_badge}
      </div>
      <div class="card-meta">
        <span class="emo-badge" style="background:{emo_color}22;color:{emo_color}">{_esc(emo)}</span>
        <span class="action-count">{action_summary}</span>
        {gate_indicator}
        {pin_indicator}
      </div>
      <div class="card-notes">{_esc(s.get('notes', '')[:60])}</div>
    </a>"""


def render_dashboard(screens, feedback):
    """Render dashboard grouped by role and journey."""
    total = len(screens)
    reviewed = sum(1 for s in screens
                   if feedback.get("screens", {}).get(s["id"], {}).get("status") in ("approved", "revision"))

    # Group by role
    roles_set = sorted(set(s.get("role", "") for s in screens if s.get("role")))
    role_groups = {}
    for s in screens:
        role = s.get("role", "Unassigned")
        role_groups.setdefault(role, []).append(s)

    # Group by journey
    journey_groups = {}
    for s in screens:
        journey = s.get("operation_line", "Unlinked")
        journey_name = s.get("operation_line_name", journey)
        journey_groups.setdefault((journey, journey_name), []).append(s)

    # Render role sections
    role_sections = ""
    for role in (roles_set if roles_set else ["Unassigned"]):
        slist = role_groups.get(role, [])
        if not slist:
            continue
        role_reviewed = sum(1 for s in slist
                           if feedback.get("screens", {}).get(s["id"], {}).get("status") in ("approved", "revision"))
        cards = "".join(_render_card(s, feedback) for s in slist)
        role_sections += f"""
        <div class="group-section" data-group-type="role">
          <div class="group-header" onclick="this.parentElement.classList.toggle('collapsed')">
            <span class="group-title">{_esc(role)}</span>
            <span class="group-meta">{len(slist)} screens / {role_reviewed}/{len(slist)} reviewed</span>
            <span class="group-chevron">&#9662;</span>
          </div>
          <div class="group-grid">{cards}</div>
        </div>"""

    # Render journey sections
    journey_sections = ""
    for (jid, jname), slist in journey_groups.items():
        emo_states = [s.get("emotion_state", "") for s in slist if s.get("emotion_state")]
        emo_flow = " &rarr; ".join(dict.fromkeys(emo_states)) if emo_states else ""
        j_reviewed = sum(1 for s in slist
                         if feedback.get("screens", {}).get(s["id"], {}).get("status") in ("approved", "revision"))
        cards = "".join(_render_card(s, feedback) for s in slist)
        journey_sections += f"""
        <div class="group-section" data-group-type="journey">
          <div class="group-header" onclick="this.parentElement.classList.toggle('collapsed')">
            <span class="group-title">{_esc(jname)}</span>
            <span class="group-emo-flow">{emo_flow}</span>
            <span class="group-meta">{len(slist)} screens / {j_reviewed}/{len(slist)} reviewed</span>
            <span class="group-chevron">&#9662;</span>
          </div>
          <div class="group-grid">{cards}</div>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="zh"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Wireframe Review</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,system-ui,'Segoe UI',sans-serif;background:#f8f9fa;color:#212529}}
.header{{background:#fff;border-bottom:2px solid #dee2e6;padding:20px 32px;position:sticky;top:0;z-index:10}}
.header h1{{font-size:20px;font-weight:600;color:#495057}}
.header-sub{{font-size:12px;color:#868e96;margin-top:2px}}
.header-meta{{font-size:13px;color:#868e96;margin-top:4px}}
.progress{{margin-top:12px;height:4px;background:#e9ecef;border-radius:2px}}
.progress-bar{{height:100%;background:#51cf66;border-radius:2px;transition:width .3s}}
.toolbar{{display:flex;gap:8px;padding:16px 32px;flex-wrap:wrap;align-items:center}}
.view-toggle{{display:flex;gap:0;border:1px solid #dee2e6;border-radius:6px;overflow:hidden}}
.view-btn{{padding:6px 16px;border:none;background:#fff;cursor:pointer;font-size:13px;color:#495057;transition:all .15s}}
.view-btn.active{{background:#495057;color:#fff}}
.status-filter{{margin-left:auto;display:flex;gap:6px}}
.tab{{padding:6px 16px;border-radius:6px;border:1px solid #dee2e6;background:#fff;cursor:pointer;font-size:13px;color:#495057}}
.tab.active{{background:#495057;color:#fff;border-color:#495057}}
.content{{padding:0 32px 32px}}
.group-section{{margin-bottom:20px;border:1px solid #dee2e6;border-radius:8px;background:#fff;overflow:hidden}}
.group-header{{display:flex;align-items:center;gap:12px;padding:14px 20px;cursor:pointer;user-select:none;transition:background .15s}}
.group-header:hover{{background:#f8f9fa}}
.group-title{{font-weight:600;font-size:15px;color:#495057}}
.group-emo-flow{{font-size:12px;color:#7c3aed;background:#f3f0ff;padding:2px 10px;border-radius:10px}}
.group-meta{{font-size:12px;color:#868e96;margin-left:auto}}
.group-chevron{{color:#adb5bd;font-size:14px;transition:transform .2s}}
.group-section.collapsed .group-chevron{{transform:rotate(-90deg)}}
.group-section.collapsed .group-grid{{display:none}}
.group-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px;padding:0 16px 16px}}
.card{{display:block;background:#f8f9fa;border:1px solid #dee2e6;border-radius:6px;padding:12px;text-decoration:none;color:inherit;transition:box-shadow .15s,border-color .15s}}
.card:hover{{box-shadow:0 2px 8px rgba(0,0,0,.08);border-color:#adb5bd}}
.card[data-status="approved"]{{border-left:3px solid #51cf66}}
.card[data-status="revision"]{{border-left:3px solid #fcc419}}
.card-header{{display:flex;align-items:center;gap:8px;margin-bottom:6px}}
.card-title{{font-weight:600;font-size:14px;flex:1;color:#495057}}
.card-meta{{display:flex;gap:6px;margin-bottom:4px;font-size:11px;flex-wrap:wrap}}
.card-notes{{font-size:12px;color:#868e96;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.emo-badge{{padding:2px 8px;border-radius:4px;font-size:11px;font-weight:500}}
.action-count{{background:#e9ecef;color:#495057;padding:2px 8px;border-radius:4px;font-size:11px}}
.badge{{padding:2px 8px;border-radius:4px;font-size:11px;font-weight:500}}
.badge.pending{{background:#f1f3f5;color:#868e96}}
.badge.approved{{background:#d3f9d8;color:#2b8a3e}}
.badge.revision{{background:#fff3bf;color:#e67700}}
.gate-warn{{background:#ffebee;color:#c62828;padding:2px 6px;border-radius:3px;font-size:11px}}
.pin-count{{color:#e67700;font-weight:500;font-size:11px}}
.footer{{text-align:center;padding:32px}}
.submit-btn{{padding:12px 48px;background:#495057;color:#fff;border:none;border-radius:8px;font-size:15px;cursor:pointer;font-weight:500}}
.submit-btn:hover{{background:#343a40}}
.submit-btn:disabled{{background:#adb5bd;cursor:not-allowed}}
.legend{{padding:8px 32px;font-size:11px;color:#868e96;display:flex;gap:16px;flex-wrap:wrap}}
.legend-item{{display:flex;align-items:center;gap:4px}}
.legend-dot{{width:10px;height:10px;border-radius:50%}}
</style></head><body>
<div class="header">
  <h1>Wireframe Review</h1>
  <div class="header-sub">Low-fidelity structural review &mdash; validate IA, flows, and features before visual design</div>
  <div class="header-meta">Round {feedback.get('round', 1)} / {reviewed}/{total} reviewed</div>
  <div class="progress"><div class="progress-bar" style="width:{reviewed/total*100 if total else 0:.0f}%"></div></div>
</div>
<div class="legend">
  <span class="legend-item"><span class="legend-dot" style="background:#4CAF50"></span> Create</span>
  <span class="legend-item"><span class="legend-dot" style="background:#FF9800"></span> Update</span>
  <span class="legend-item"><span class="legend-dot" style="background:#F44336"></span> Delete</span>
  <span class="legend-item"><span class="legend-dot" style="background:#78909C"></span> Read</span>
</div>
<div class="toolbar">
  <div class="view-toggle">
    <button class="view-btn active" data-view="role">By Role</button>
    <button class="view-btn" data-view="journey">By Journey</button>
  </div>
  <div class="status-filter">
    <button class="tab active" data-status="all">All</button>
    <button class="tab" data-status="pending">Pending</button>
    <button class="tab" data-status="approved">Approved</button>
    <button class="tab" data-status="revision">Revision</button>
  </div>
</div>
<div class="content" id="content">
  <div id="roleView">{role_sections}</div>
  <div id="journeyView" style="display:none">{journey_sections}</div>
</div>
<div class="footer">
  <button class="submit-btn" onclick="submitAll()" id="submitBtn">Submit Feedback</button>
</div>
<script>
document.querySelectorAll('.view-btn').forEach(btn=>{{
  btn.onclick=()=>{{
    document.querySelectorAll('.view-btn').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
    const view=btn.dataset.view;
    document.getElementById('roleView').style.display=view==='role'?'':'none';
    document.getElementById('journeyView').style.display=view==='journey'?'':'none';
  }};
}});
document.querySelectorAll('.tab[data-status]').forEach(t=>{{
  t.onclick=()=>{{
    document.querySelectorAll('.tab[data-status]').forEach(b=>b.classList.remove('active'));
    t.classList.add('active');
    filterCards();
  }};
}});
function filterCards(){{
  const status=document.querySelector('.tab[data-status].active')?.dataset.status||'all';
  document.querySelectorAll('.card').forEach(c=>{{
    c.style.display=(status==='all'||c.dataset.status===status)?'':'none';
  }});
  document.querySelectorAll('.group-section').forEach(g=>{{
    const anyVisible=Array.from(g.querySelectorAll('.card')).some(c=>c.style.display!=='none');
    g.style.display=anyVisible?'':'none';
  }});
}}
function submitAll(){{
  if(!confirm('Submit wireframe feedback?'))return;
  fetch('/api/submit',{{method:'POST'}}).then(()=>{{
    document.getElementById('submitBtn').disabled=true;
    document.getElementById('submitBtn').textContent='Submitted!';
    const overlay=document.createElement('div');
    overlay.style.cssText='position:fixed;inset:0;background:rgba(255,255,255,.85);z-index:200;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:12px;backdrop-filter:blur(4px)';
    overlay.innerHTML='<div style="font-size:48px">✅</div><div style="font-size:20px;font-weight:600;color:#065f46">Feedback Submitted</div><div style="font-size:14px;color:#64748b">Server is shutting down. Claude will automatically process the feedback.</div>';
    document.body.appendChild(overlay);
  }});
}}
</script></body></html>"""


def render_screen_detail(screen, all_screens, feedback):
    """Render screen detail page with wireframe + pin comments + feedback category."""
    sid = screen["id"]
    name = screen["name"]
    role = screen.get("role", "")
    emo = screen.get("emotion_state", "neutral")
    emo_color = EMOTION_COLORS.get(emo, "#B0BEC5")
    ux_intent = screen.get("ux_intent", "")
    actions = screen.get("actions", [])
    tasks = screen.get("tasks", [])
    non_neg = screen.get("non_negotiable", [])
    gate_issues = screen.get("gate_issues", [])
    ol_name = screen.get("operation_line_name", "")

    fb = feedback.get("screens", {}).get(sid, {"status": "pending", "pins": []})
    status = fb.get("status", "pending")
    pins = fb.get("pins", [])

    # Navigation
    idx = next((i for i, s in enumerate(all_screens) if s["id"] == sid), -1)
    prev_id = all_screens[idx - 1]["id"] if idx > 0 else ""
    next_id = all_screens[idx + 1]["id"] if idx < len(all_screens) - 1 else ""
    prev_btn = f'<a href="/screen/{prev_id}" class="nav-btn">&larr; Prev</a>' if prev_id else '<span class="nav-btn disabled">&larr; Prev</span>'
    next_btn = f'<a href="/screen/{next_id}" class="nav-btn">Next &rarr;</a>' if next_id else '<span class="nav-btn disabled">Next &rarr;</span>'

    # Rationale
    rationale = ""
    rationale += f"<dt>Journey</dt><dd>{_esc(ol_name)}</dd>"
    rationale += f"<dt>Role</dt><dd>{_esc(role)}</dd>"
    rationale += f"<dt>Emotion</dt><dd><span style='background:{emo_color}22;color:{emo_color};padding:2px 8px;border-radius:4px'>{_esc(emo)}</span></dd>"
    if ux_intent:
        rationale += f"<dt>UX Intent</dt><dd>{_esc(ux_intent)}</dd>"
    if actions:
        act_items = ""
        for a in actions[:10]:
            crud = a.get("crud", "R")
            freq = a.get("frequency", "")
            act_items += f"<li>{_esc(a.get('label', ''))} <span class='crud-tag {crud}'>{crud}</span> <span class='freq'>{freq}</span></li>"
        rationale += f"<dt>Actions ({len(actions)})</dt><dd><ul>{act_items}</ul></dd>"
    if tasks:
        rationale += f"<dt>Tasks</dt><dd>{', '.join(_esc(t) for t in tasks)}</dd>"
    if non_neg:
        rationale += f"<dt>Non-negotiable</dt><dd style='color:#e65100'>{', '.join(_esc(n) for n in non_neg)}</dd>"
    if gate_issues:
        gate_items = "".join(f"<li style='color:#c62828'>{_esc(i.get('detail', ''))}</li>" for i in gate_issues)
        rationale += f"<dt>Gate Issues</dt><dd><ul>{gate_items}</ul></dd>"

    pins_json = json.dumps(pins, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="zh"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_esc(name)} - Wireframe Review</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,system-ui,'Segoe UI',sans-serif;background:#f8f9fa;color:#212529}}
.topbar{{background:#fff;border-bottom:2px solid #dee2e6;padding:12px 24px;display:flex;align-items:center;gap:16px;position:sticky;top:0;z-index:20}}
.topbar a{{color:#339af0;text-decoration:none;font-size:14px}}
.topbar h2{{font-size:16px;font-weight:600;color:#495057;flex:1}}
.nav-btn{{padding:6px 16px;border-radius:6px;border:1px solid #dee2e6;background:#fff;text-decoration:none;color:#495057;font-size:13px}}
.nav-btn:hover{{background:#f1f3f5}}
.nav-btn.disabled{{color:#adb5bd;pointer-events:none}}
.main{{display:grid;grid-template-columns:1fr 380px;height:calc(100vh - 53px)}}
.preview-panel{{position:relative;overflow:auto;background:#e9ecef;border-right:1px solid #dee2e6}}
.preview-container{{position:relative;min-height:100%}}
.preview-container iframe{{width:100%;height:100%;border:none;min-height:calc(100vh - 53px)}}
.pin{{position:absolute;width:24px;height:24px;background:#fcc419;color:#212529;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;cursor:pointer;transform:translate(-50%,-50%);z-index:5;box-shadow:0 2px 4px rgba(0,0,0,.2);transition:transform .1s}}
.pin:hover{{transform:translate(-50%,-50%) scale(1.2)}}
.click-hint{{position:absolute;top:8px;left:50%;transform:translateX(-50%);background:rgba(0,0,0,.6);color:#fff;padding:6px 16px;border-radius:6px;font-size:12px;pointer-events:none;z-index:10}}
.side-panel{{overflow-y:auto;background:#fff;display:flex;flex-direction:column}}
.section{{padding:16px 20px;border-bottom:1px solid #f1f3f5}}
.section-title{{font-size:12px;font-weight:600;color:#868e96;text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px}}
dl{{font-size:13px}}
dt{{font-weight:600;color:#495057;margin-top:8px}}
dd{{color:#868e96;margin-top:2px}}
dd ul{{margin:4px 0 0 16px}}
.crud-tag{{padding:1px 6px;border-radius:3px;font-size:10px;font-weight:600;color:#fff}}
.crud-tag.C{{background:#4CAF50}}
.crud-tag.U{{background:#FF9800}}
.crud-tag.D{{background:#F44336}}
.crud-tag.R{{background:#78909C}}
.freq{{font-size:10px;color:#adb5bd}}
.review-section{{flex:1;display:flex;flex-direction:column}}
.status-toggle{{display:flex;gap:8px;margin-bottom:12px}}
.status-btn{{flex:1;padding:10px;border:2px solid #dee2e6;border-radius:8px;background:#fff;cursor:pointer;font-size:14px;text-align:center;transition:all .15s}}
.status-btn.approved-btn.selected{{border-color:#51cf66;background:#d3f9d8}}
.status-btn.revision-btn.selected{{border-color:#fcc419;background:#fff3bf}}
.pins-list{{flex:1;overflow-y:auto}}
.pin-item{{padding:10px 12px;border:1px solid #dee2e6;border-radius:6px;margin-bottom:8px;font-size:13px}}
.pin-item-header{{display:flex;align-items:center;gap:8px;margin-bottom:6px}}
.pin-num{{width:20px;height:20px;background:#fcc419;color:#212529;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;flex-shrink:0}}
.pin-item textarea{{width:100%;border:1px solid #dee2e6;border-radius:4px;padding:6px;font-size:13px;resize:vertical;min-height:40px;font-family:inherit}}
.pin-item select{{border:1px solid #dee2e6;border-radius:4px;padding:4px 8px;font-size:12px;background:#fff;color:#495057}}
.pin-item .del-btn{{color:#adb5bd;cursor:pointer;font-size:16px;flex-shrink:0;margin-left:auto}}
.pin-item .del-btn:hover{{color:#fa5252}}
.add-hint{{text-align:center;color:#adb5bd;font-size:13px;padding:16px}}
</style></head><body>
<div class="topbar">
  <a href="/">Home</a>
  <h2>{_esc(sid)} {_esc(name)}</h2>
  {prev_btn} {next_btn}
</div>
<div class="main">
  <div class="preview-panel">
    <div class="preview-container" id="previewContainer">
      <div class="click-hint">Click anywhere to add a feedback pin</div>
    </div>
  </div>
  <div class="side-panel">
    <div class="section">
      <div class="section-title">Screen Info</div>
      <dl>{rationale}</dl>
    </div>
    <div class="section review-section">
      <div class="section-title">Review</div>
      <div class="status-toggle">
        <button class="status-btn approved-btn {'selected' if status=='approved' else ''}" onclick="setStatus('approved')">Approved</button>
        <button class="status-btn revision-btn {'selected' if status=='revision' else ''}" onclick="setStatus('revision')">Needs Revision</button>
      </div>
      <div class="pins-list" id="pinsList"></div>
      <div class="add-hint">Click on the wireframe to pin feedback</div>
    </div>
  </div>
</div>
<script>
const SCREEN_ID="{sid}";
let pins={pins_json};
let status="{status}";

const container=document.getElementById('previewContainer');
const iframe=document.createElement('iframe');
iframe.src='/wireframe/{sid}';
iframe.onload=()=>{{
  try{{
    iframe.contentDocument.addEventListener('click',(e)=>{{
      const x=((e.pageX)/iframe.contentDocument.documentElement.scrollWidth*100).toFixed(1);
      const y=((e.pageY)/iframe.contentDocument.documentElement.scrollHeight*100).toFixed(1);
      addPin(parseFloat(x),parseFloat(y));
    }});
    iframe.contentDocument.body.style.cursor='crosshair';
  }}catch(err){{
    container.addEventListener('click',(e)=>{{
      if(e.target===container||e.target===iframe){{
        const rect=container.getBoundingClientRect();
        const x=((e.clientX-rect.left)/rect.width*100).toFixed(1);
        const y=((e.clientY-rect.top+container.scrollTop)/container.scrollHeight*100).toFixed(1);
        addPin(parseFloat(x),parseFloat(y));
      }}
    }});
  }}
}};
container.appendChild(iframe);

function renderPins(){{
  container.querySelectorAll('.pin').forEach(p=>p.remove());
  pins.forEach((p,i)=>{{
    const dot=document.createElement('div');
    dot.className='pin';
    dot.textContent=i+1;
    dot.style.left=p.x+'%';
    dot.style.top=p.y+'%';
    dot.onclick=(e)=>{{e.stopPropagation();highlightPin(i)}};
    container.appendChild(dot);
  }});
  const list=document.getElementById('pinsList');
  list.innerHTML='';
  pins.forEach((p,i)=>{{
    const div=document.createElement('div');
    div.className='pin-item';
    div.id='pin-item-'+i;
    div.innerHTML=`
      <div class="pin-item-header">
        <span class="pin-num">${{i+1}}</span>
        <select onchange="updateCategory(${{i}},this.value)">
          <option value="experience-map" ${{p.category==='experience-map'?'selected':''}}>Flow/Structure</option>
          <option value="product-map" ${{p.category==='product-map'?'selected':''}}>Feature/Task</option>
          <option value="concept" ${{p.category==='concept'?'selected':''}}>Concept</option>
        </select>
        <span class="del-btn" onclick="deletePin(${{i}})">&times;</span>
      </div>
      <textarea placeholder="Describe the issue..." oninput="updateComment(${{i}},this.value)">${{p.comment||''}}</textarea>
    `;
    list.appendChild(div);
  }});
}}

function addPin(x,y){{
  pins.push({{id:Date.now(),x,y,comment:'',category:'experience-map'}});
  if(status==='pending'||status==='approved')setStatus('revision');
  renderPins();
  saveFeedback();
  setTimeout(()=>{{
    const items=document.querySelectorAll('.pin-item textarea');
    if(items.length)items[items.length-1].focus();
  }},50);
}}
function updateComment(idx,comment){{ pins[idx].comment=comment; saveFeedback(); }}
function updateCategory(idx,cat){{ pins[idx].category=cat; saveFeedback(); }}
function deletePin(idx){{
  pins.splice(idx,1);
  renderPins();
  saveFeedback();
  if(pins.length===0&&status==='revision')setStatus('pending');
}}
function highlightPin(idx){{
  const el=document.getElementById('pin-item-'+idx);
  if(el){{el.scrollIntoView({{behavior:'smooth'}});el.style.background='#fff3bf';setTimeout(()=>el.style.background='',1500)}}
}}
function setStatus(s){{
  status=s;
  document.querySelectorAll('.status-btn').forEach(b=>b.classList.remove('selected'));
  if(s==='approved')document.querySelector('.approved-btn').classList.add('selected');
  if(s==='revision')document.querySelector('.revision-btn').classList.add('selected');
  saveFeedback();
}}
let saveTimer=null;
function saveFeedback(){{
  clearTimeout(saveTimer);
  saveTimer=setTimeout(()=>{{
    fetch('/api/feedback',{{
      method:'POST',
      headers:{{'Content-Type':'application/json'}},
      body:JSON.stringify({{screen_id:SCREEN_ID,status,pins}})
    }});
  }},300);
}}
renderPins();
</script></body></html>"""


# ── HTTP Handler ──────────────────────────────────────────────────────────────

# Load data once at startup
_op_lines, _tasks, _roles, _role_map, _gate_issues = load_data()
_all_screens = build_screens_with_context(_op_lines, _tasks, _role_map, _gate_issues)
_screen_map = {s["id"]: s for s in _all_screens}


class WireframeHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/":
            fb = load_feedback()
            html = render_dashboard(_all_screens, fb)
            self._html(html)

        elif path.startswith("/screen/"):
            screen_id = path.split("/screen/")[1]
            screen = _screen_map.get(screen_id)
            if not screen:
                self._html("<h1>Screen not found</h1>")
                return
            fb = load_feedback()
            html = render_screen_detail(screen, _all_screens, fb)
            self._html(html)

        elif path.startswith("/wireframe/"):
            screen_id = path.split("/wireframe/")[1]
            screen = _screen_map.get(screen_id)
            if not screen:
                self._html("<h2>Screen not found</h2>")
                return
            html = generate_wireframe(screen)
            self._html(html)

        elif path == "/api/screens":
            self._json({"screens": _all_screens})

        elif path == "/api/feedback":
            fb = load_feedback()
            self._json(fb)

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/feedback":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
            fb = load_feedback()
            sid = body.get("screen_id")
            if sid:
                fb["screens"][sid] = {
                    "status": body.get("status", "pending"),
                    "pins": body.get("pins", []),
                }
            save_feedback(fb)
            self._json({"ok": True})

        elif path == "/api/submit":
            fb = load_feedback()
            fb["submitted_at"] = C.now_iso()
            save_feedback(fb)
            self._json({"ok": True})
            # Print feedback summary to stdout so Claude receives it
            screens = fb.get("screens", {})
            approved = [s for s, d in screens.items() if d.get("status") == "approved"]
            revision = [s for s, d in screens.items() if d.get("status") == "revision"]
            print(f"\n{'='*60}")
            print(f"Wireframe feedback submitted! Saved to {FEEDBACK_PATH}")
            print(f"  Round:    {fb.get('round', 1)}")
            print(f"  Approved: {len(approved)}")
            print(f"  Revision: {len(revision)}")
            if revision:
                print(f"\nScreens needing revision:")
                for sid in revision:
                    pins = screens[sid].get("pins", [])
                    print(f"  - {sid}: {len(pins)} pin(s)")
                    for p in pins:
                        print(f"      [{p.get('category','experience-map')}] {p.get('comment','')}")
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


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # Kill any other review servers to avoid multiple browser windows
    C.kill_other_review_servers(PORT)

    server = http.server.HTTPServer((HOST, PORT), WireframeHandler)
    url = f"http://{HOST}:{PORT}"
    if HOST == "0.0.0.0":
        import socket
        local_ip = socket.gethostbyname(socket.gethostname())
        print(f"Wireframe Review Server started:")
        print(f"  Local:   http://localhost:{PORT}")
        print(f"  Network: http://{local_ip}:{PORT}")
    else:
        print(f"Wireframe Review Server started: {url}")
    print(f"Reading from: {BASE}")
    print(f"Feedback:     {FEEDBACK_PATH}")
    print(f"Screens:      {len(_all_screens)}")
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
