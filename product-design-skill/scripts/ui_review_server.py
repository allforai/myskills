#!/usr/bin/env python3
"""UI Review Server — local HTTP server for reviewing UI design screens.

Reads .allforai/ui-design/ output and serves a review interface where
reviewers can browse all screens, see design rationale, pin comments
at specific positions, and submit structured feedback.

Feedback is saved to .allforai/ui-design/review-feedback.json.

Usage:
    python3 ui_review_server.py <BASE_PATH> [--port 18903] [--host localhost]
    python3 ui_review_server.py <BASE_PATH> --host 0.0.0.0  # LAN access
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
PORT = int(args.get("port", "18903"))
HOST = args.get("host", "localhost")
NO_OPEN = args.get("no-open", "false").lower() in ("true", "1", "yes")

UI_DIR = os.path.join(BASE, "ui-design")
SM_DIR = os.path.join(BASE, "experience-map")
FEEDBACK_PATH = os.path.join(UI_DIR, "review-feedback.json")

# ── Load data ─────────────────────────────────────────────────────────────────

def load_spec():
    """Load ui-design-spec.json and normalize screens to list format."""
    raw = C.load_json(os.path.join(UI_DIR, "ui-design-spec.json")) or {}
    screens = raw.get("screens", [])
    # If screens is a dict (keyed by id), convert to list
    if isinstance(screens, dict):
        normalized = []
        for sid, sdata in screens.items():
            if isinstance(sdata, dict):
                if "id" not in sdata:
                    sdata["id"] = sid
                normalized.append(sdata)
        raw["screens"] = normalized
    return raw

def load_experience_map():
    """Load experience-map.json for design rationale."""
    op_lines, screen_index, loaded = C.load_experience_map(BASE)
    if loaded:
        return C.build_screen_by_id_from_lines(op_lines)
    return {}

def load_stitch_index():
    """Load stitch-index.json for Stitch screen mappings."""
    return C.load_json(os.path.join(UI_DIR, "stitch-index.json")) or {}

def load_feedback():
    """Load existing feedback or create empty."""
    fb = C.load_json(FEEDBACK_PATH)
    if fb:
        return fb
    return {"round": 1, "submitted_at": None, "screens": {}}

def save_feedback(fb):
    """Save feedback to disk."""
    C.write_json(FEEDBACK_PATH, fb)

def get_stitch_html(screen_id):
    """Read Stitch-generated HTML for a screen."""
    path = os.path.join(UI_DIR, "stitch", f"{screen_id}.html")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return f.read()
    return None

def get_stitch_image(screen_id):
    """Check if Stitch screenshot exists."""
    for ext in ("png", "jpg", "webp"):
        path = os.path.join(UI_DIR, "stitch", f"{screen_id}.{ext}")
        if os.path.exists(path):
            return path
    return None

def get_preview_html(screen_id, spec):
    """Extract preview HTML from preview/ files or generate skeleton."""
    # Try to find in preview/*.html files
    preview_dir = os.path.join(UI_DIR, "preview")
    if os.path.isdir(preview_dir):
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
    return generate_skeleton(screen_spec, spec.get("design_tokens", {}))

def generate_skeleton(screen, tokens):
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
        section_html += f'<div style="background:#f3f4f6;border-radius:{radius};padding:24px;margin:8px 0;min-height:60px;display:flex;align-items:center;justify-content:center;color:#6b7280;font-size:14px">{sec}</div>'

    states_html = ""
    for state_name, state_desc in states.items():
        color = "#10b981" if state_name == "empty" else "#f59e0b" if state_name == "loading" else "#ef4444"
        states_html += f'<div style="display:inline-block;background:{color}20;color:{color};padding:4px 12px;border-radius:12px;font-size:12px;margin:4px">{state_name}: {state_desc}</div>'

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
body{{margin:0;padding:24px;font-family:-apple-system,system-ui,sans-serif;background:{bg}}}
</style></head><body>
<div style="max-width:800px;margin:0 auto">
<div style="font-size:11px;color:#9ca3af;margin-bottom:8px">LAYOUT: {layout}</div>
<div style="font-size:20px;font-weight:600;color:{primary};margin-bottom:16px">{name}</div>
{section_html}
<div style="margin-top:16px">{states_html}</div>
</div>
</body></html>"""

# ── HTML Templates ────────────────────────────────────────────────────────────

def _render_card(s, sm, feedback):
    """Render a single screen card HTML."""
    sid = s.get("id", "")
    name = s.get("name", "")
    role = s.get("role", "")
    itype = s.get("interaction_type", "")
    audience = s.get("audience_type", "default")
    layout = s.get("layout", "")
    sm_screen = sm.get(sid, {})
    flags = sm_screen.get("flags", [])
    emo = s.get("emotion_context", {})
    emo_state = emo.get("state", "")
    journey = emo.get("operation_line", "")

    fb = feedback.get("screens", {}).get(sid, {})
    status = fb.get("status", "pending")
    pin_count = len(fb.get("pins", []))

    has_stitch = os.path.exists(os.path.join(UI_DIR, "stitch", f"{sid}.html"))

    status_badge = {
        "pending": '<span class="badge pending">Pending</span>',
        "approved": '<span class="badge approved">Approved</span>',
        "revision": '<span class="badge revision">Revision</span>',
    }.get(status, '<span class="badge pending">Pending</span>')

    flags_html = "".join(f'<span class="flag">{f}</span>' for f in flags)
    stitch_indicator = '<span class="stitch-dot" title="Stitch visual available"></span>' if has_stitch else ''
    pin_indicator = f'<span class="pin-count">{pin_count} pins</span>' if pin_count else ''

    emo_colors = {
        "curious": "#4FC3F7", "anxious": "#FF8A65", "satisfied": "#81C784",
        "frustrated": "#E57373", "neutral": "#B0BEC5", "exploring": "#64B5F6",
        "confident": "#66BB6A", "confused": "#FFB74D",
    }
    emo_color = emo_colors.get(emo_state, "#B0BEC5")
    emo_badge = f'<span class="emo-badge" style="background:{emo_color}20;color:{emo_color}">{emo_state}</span>' if emo_state else ''

    return f"""
    <a href="/screen/{sid}" class="card" data-role="{role}" data-status="{status}" data-journey="{journey}">
      <div class="card-header">
        <span class="card-title">{name}</span>
        {stitch_indicator}
        {status_badge}
      </div>
      <div class="card-meta">
        <span class="itype">{itype}</span>
        <span class="audience">{audience}</span>
        {emo_badge}
        {pin_indicator}
      </div>
      <div class="card-layout">{layout}</div>
      <div class="card-flags">{flags_html}</div>
    </a>"""


def render_dashboard(spec, sm, feedback):
    """Render the main dashboard page grouped by role or journey."""
    screens = spec.get("screens", [])
    style = spec.get("design_style", spec.get("style", "Unknown"))
    product = spec.get("product", spec.get("product_name", "Product"))
    total = len(screens)
    reviewed = sum(1 for s in screens
                   if feedback.get("screens", {}).get(s.get("id", ""), {}).get("status") in ("approved", "revision"))
    revision_count = sum(1 for s in screens
                         if feedback.get("screens", {}).get(s.get("id", ""), {}).get("status") == "revision")

    # Group screens by role
    roles_set = sorted(set(s.get("role", "") for s in screens if s.get("role")))
    role_groups = {}
    for s in screens:
        role = s.get("role", "未分配")
        role_groups.setdefault(role, []).append(s)

    # Group screens by journey (operation_line)
    journey_groups = {}
    for s in screens:
        emo = s.get("emotion_context", {})
        journey = emo.get("operation_line", "未关联")
        journey_groups.setdefault(journey, []).append(s)

    # Render role-grouped sections
    role_sections = ""
    for role in (roles_set if roles_set else ["未分配"]):
        slist = role_groups.get(role, [])
        if not slist:
            continue
        role_reviewed = sum(1 for s in slist
                           if feedback.get("screens", {}).get(s.get("id", ""), {}).get("status") in ("approved", "revision"))
        cards = "".join(_render_card(s, sm, feedback) for s in slist)
        role_sections += f"""
        <div class="group-section" data-group-type="role">
          <div class="group-header" onclick="this.parentElement.classList.toggle('collapsed')">
            <span class="group-title">{role}</span>
            <span class="group-meta">{len(slist)} screens · {role_reviewed}/{len(slist)} reviewed</span>
            <span class="group-chevron">▾</span>
          </div>
          <div class="group-grid">{cards}</div>
        </div>"""

    # Render journey-grouped sections
    journey_sections = ""
    for journey_id, slist in journey_groups.items():
        # Get emotion flow summary for this journey
        emo_states = [s.get("emotion_context", {}).get("state", "") for s in slist if s.get("emotion_context", {}).get("state")]
        emo_flow = " → ".join(dict.fromkeys(emo_states)) if emo_states else ""
        journey_reviewed = sum(1 for s in slist
                               if feedback.get("screens", {}).get(s.get("id", ""), {}).get("status") in ("approved", "revision"))
        cards = "".join(_render_card(s, sm, feedback) for s in slist)
        journey_sections += f"""
        <div class="group-section" data-group-type="journey">
          <div class="group-header" onclick="this.parentElement.classList.toggle('collapsed')">
            <span class="group-title">{journey_id}</span>
            <span class="group-emo-flow">{emo_flow}</span>
            <span class="group-meta">{len(slist)} screens · {journey_reviewed}/{len(slist)} reviewed</span>
            <span class="group-chevron">▾</span>
          </div>
          <div class="group-grid">{cards}</div>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="zh"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>UI Review - {product}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,system-ui,'Segoe UI',sans-serif;background:#fafafa;color:#18181b}}
.header{{background:#fff;border-bottom:1px solid #e5e7eb;padding:20px 32px;position:sticky;top:0;z-index:10}}
.header h1{{font-size:20px;font-weight:600}}
.header-meta{{font-size:13px;color:#71717a;margin-top:4px}}
.progress{{margin-top:12px;height:4px;background:#e5e7eb;border-radius:2px}}
.progress-bar{{height:100%;background:#10b981;border-radius:2px;transition:width .3s}}
.toolbar{{display:flex;gap:8px;padding:16px 32px;flex-wrap:wrap;align-items:center}}
.tab{{padding:6px 16px;border-radius:6px;border:1px solid #e5e7eb;background:#fff;cursor:pointer;font-size:13px;color:#52525b;transition:all .15s}}
.tab.active{{background:#18181b;color:#fff;border-color:#18181b}}
.view-toggle{{display:flex;gap:0;border:1px solid #e5e7eb;border-radius:6px;overflow:hidden}}
.view-btn{{padding:6px 16px;border:none;background:#fff;cursor:pointer;font-size:13px;color:#52525b;transition:all .15s}}
.view-btn.active{{background:#18181b;color:#fff}}
.status-filter{{margin-left:auto;display:flex;gap:6px}}
.content{{padding:0 32px 32px}}
.group-section{{margin-bottom:24px;border:1px solid #e5e7eb;border-radius:12px;background:#fff;overflow:hidden}}
.group-header{{display:flex;align-items:center;gap:12px;padding:16px 20px;cursor:pointer;user-select:none;transition:background .15s}}
.group-header:hover{{background:#f9fafb}}
.group-title{{font-weight:600;font-size:16px}}
.group-emo-flow{{font-size:12px;color:#7c3aed;background:#ede9fe;padding:2px 10px;border-radius:10px}}
.group-meta{{font-size:12px;color:#71717a;margin-left:auto}}
.group-chevron{{color:#a1a1aa;font-size:14px;transition:transform .2s}}
.group-section.collapsed .group-chevron{{transform:rotate(-90deg)}}
.group-section.collapsed .group-grid{{display:none}}
.group-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px;padding:0 16px 16px}}
.card{{display:block;background:#fafafa;border:1px solid #e5e7eb;border-radius:8px;padding:14px;text-decoration:none;color:inherit;transition:box-shadow .15s,border-color .15s}}
.card:hover{{box-shadow:0 4px 12px rgba(0,0,0,.08);border-color:#a1a1aa}}
.card[data-status="approved"]{{border-left:3px solid #10b981}}
.card[data-status="revision"]{{border-left:3px solid #f59e0b}}
.card-header{{display:flex;align-items:center;gap:8px;margin-bottom:6px}}
.card-title{{font-weight:600;font-size:14px;flex:1}}
.card-meta{{display:flex;gap:6px;margin-bottom:4px;font-size:11px;flex-wrap:wrap}}
.card-layout{{font-size:11px;color:#71717a}}
.card-flags{{margin-top:4px}}
.itype{{background:#ede9fe;color:#7c3aed;padding:2px 8px;border-radius:4px}}
.audience{{background:#e0f2fe;color:#0369a1;padding:2px 8px;border-radius:4px}}
.emo-badge{{padding:2px 8px;border-radius:4px;font-size:11px;font-weight:500}}
.badge{{padding:2px 8px;border-radius:4px;font-size:11px;font-weight:500}}
.badge.pending{{background:#f4f4f5;color:#71717a}}
.badge.approved{{background:#dcfce7;color:#15803d}}
.badge.revision{{background:#fef3c7;color:#b45309}}
.flag{{background:#fef2f2;color:#dc2626;padding:2px 6px;border-radius:3px;font-size:11px;margin-right:4px}}
.stitch-dot{{width:8px;height:8px;background:#8b5cf6;border-radius:50%;display:inline-block;flex-shrink:0}}
.pin-count{{color:#f59e0b;font-weight:500}}
.footer{{text-align:center;padding:32px}}
.submit-btn{{padding:12px 48px;background:#18181b;color:#fff;border:none;border-radius:8px;font-size:15px;cursor:pointer;font-weight:500}}
.submit-btn:hover{{background:#27272a}}
.submit-btn:disabled{{background:#a1a1aa;cursor:not-allowed}}
</style></head><body>
<div class="header">
  <h1>UI Review</h1>
  <div class="header-meta">{product} / {style} / Round {feedback.get('round', 1)} / {reviewed}/{total} reviewed</div>
  <div class="progress"><div class="progress-bar" style="width:{reviewed/total*100 if total else 0:.0f}%"></div></div>
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
// View toggle
document.querySelectorAll('.view-btn').forEach(btn=>{{
  btn.onclick=()=>{{
    document.querySelectorAll('.view-btn').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
    const view=btn.dataset.view;
    document.getElementById('roleView').style.display=view==='role'?'':'none';
    document.getElementById('journeyView').style.display=view==='journey'?'':'none';
  }};
}});
// Status filter
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
  // Hide empty groups
  document.querySelectorAll('.group-section').forEach(g=>{{
    const visible=g.querySelectorAll('.card[style=""], .card:not([style])').length
      + Array.from(g.querySelectorAll('.card')).filter(c=>!c.style.display||c.style.display!=='none').length;
    // Simplified: just check if any card is visible
    const anyVisible=Array.from(g.querySelectorAll('.card')).some(c=>c.style.display!=='none');
    g.style.display=anyVisible?'':'none';
  }});
}}
function submitAll(){{
  if(!confirm('Submit all feedback and close the review server?'))return;
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


def render_screen_detail(screen_id, spec, sm, feedback):
    """Render screen detail page with preview + pin comments."""
    screens = spec.get("screens", [])
    screen = None
    screen_idx = -1
    for i, s in enumerate(screens):
        sid = s.get("id", "")
        if sid == screen_id:
            screen = s
            screen_idx = i
            break
    if not screen:
        return "<h1>Screen not found</h1>"

    sid = screen.get("id", "")
    name = screen.get("name", "")
    role = screen.get("role", "")
    itype = screen.get("interaction_type", "")
    audience = screen.get("audience_type", "default")
    layout = screen.get("layout", "")
    sections = screen.get("sections", [])
    states = screen.get("states", {})
    task_refs = screen.get("task_refs", [])

    sm_screen = sm.get(sid, {})
    flags = sm_screen.get("flags", [])
    actions = sm_screen.get("actions", [])
    purpose = sm_screen.get("primary_purpose", screen.get("primary_purpose", ""))
    description = sm_screen.get("description", "")

    fb = feedback.get("screens", {}).get(sid, {"status": "pending", "pins": []})
    status = fb.get("status", "pending")
    pins = fb.get("pins", [])

    # Navigation
    prev_id = screens[screen_idx - 1].get("id", "") if screen_idx > 0 else ""
    next_id = screens[screen_idx + 1].get("id", "") if screen_idx < len(screens) - 1 else ""

    prev_btn = f'<a href="/screen/{prev_id}" class="nav-btn">Prev</a>' if prev_id else '<span class="nav-btn disabled">Prev</span>'
    next_btn = f'<a href="/screen/{next_id}" class="nav-btn">Next</a>' if next_id else '<span class="nav-btn disabled">Next</span>'

    # Determine preview source
    stitch_html = get_stitch_html(sid)
    has_stitch = stitch_html is not None
    preview_source = "stitch" if has_stitch else "skeleton"

    # Design rationale
    rationale_items = []
    if purpose:
        rationale_items.append(f"<dt>Purpose</dt><dd>{purpose}</dd>")
    if description:
        rationale_items.append(f"<dt>Description</dt><dd>{description}</dd>")
    if layout:
        rationale_items.append(f"<dt>Layout</dt><dd>{layout}</dd>")
    if itype:
        rationale_items.append(f"<dt>Interaction Type</dt><dd><span class='itype'>{itype}</span></dd>")
    if audience:
        rationale_items.append(f"<dt>Audience</dt><dd><span class='audience'>{audience}</span></dd>")
    if sections:
        rationale_items.append(f"<dt>Sections</dt><dd>{', '.join(sections)}</dd>")
    if states:
        states_str = " / ".join(f"<b>{k}</b>: {v}" for k, v in states.items())
        rationale_items.append(f"<dt>States</dt><dd>{states_str}</dd>")
    if flags:
        flags_str = "".join(f'<span class="flag">{f}</span>' for f in flags)
        rationale_items.append(f"<dt>Flags</dt><dd>{flags_str}</dd>")
    if actions:
        act_str = "".join(f"<li>{a.get('label','')} <span class='crud'>{a.get('crud','')}</span> freq={a.get('frequency','')}</li>" for a in actions[:10])
        rationale_items.append(f"<dt>Actions</dt><dd><ul>{act_str}</ul></dd>")

    rationale_html = "".join(rationale_items)

    # Pins JSON for JS
    pins_json = json.dumps(pins, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="zh"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{name} - UI Review</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,system-ui,'Segoe UI',sans-serif;background:#fafafa;color:#18181b}}
.topbar{{background:#fff;border-bottom:1px solid #e5e7eb;padding:12px 24px;display:flex;align-items:center;gap:16px;position:sticky;top:0;z-index:20}}
.topbar a{{color:#3b82f6;text-decoration:none;font-size:14px}}
.topbar h2{{font-size:16px;font-weight:600;flex:1}}
.nav-btn{{padding:6px 16px;border-radius:6px;border:1px solid #e5e7eb;background:#fff;text-decoration:none;color:#18181b;font-size:13px}}
.nav-btn:hover{{background:#f4f4f5}}
.nav-btn.disabled{{color:#a1a1aa;pointer-events:none}}
.main{{display:grid;grid-template-columns:1fr 380px;height:calc(100vh - 53px)}}
.preview-panel{{position:relative;overflow:auto;background:#f4f4f5;border-right:1px solid #e5e7eb}}
.preview-container{{position:relative;min-height:100%}}
.preview-container iframe{{width:100%;height:100%;border:none;min-height:calc(100vh - 53px)}}
.pin{{position:absolute;width:24px;height:24px;background:#f59e0b;color:#fff;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;cursor:pointer;transform:translate(-50%,-50%);z-index:5;box-shadow:0 2px 4px rgba(0,0,0,.2);transition:transform .1s}}
.pin:hover{{transform:translate(-50%,-50%) scale(1.2)}}
.pin.active{{background:#ef4444}}
.click-hint{{position:absolute;top:8px;left:50%;transform:translateX(-50%);background:rgba(0,0,0,.7);color:#fff;padding:6px 16px;border-radius:6px;font-size:12px;pointer-events:none;z-index:10;opacity:0.8}}
.side-panel{{overflow-y:auto;background:#fff;display:flex;flex-direction:column}}
.section{{padding:16px 20px;border-bottom:1px solid #f4f4f5}}
.section-title{{font-size:12px;font-weight:600;color:#71717a;text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px}}
dl{{font-size:13px}}
dt{{font-weight:600;color:#52525b;margin-top:8px}}
dd{{color:#71717a;margin-top:2px}}
dd ul{{margin:4px 0 0 16px}}
.itype{{background:#ede9fe;color:#7c3aed;padding:2px 8px;border-radius:4px;font-size:12px}}
.audience{{background:#e0f2fe;color:#0369a1;padding:2px 8px;border-radius:4px;font-size:12px}}
.flag{{background:#fef2f2;color:#dc2626;padding:2px 6px;border-radius:3px;font-size:11px;margin-right:4px}}
.crud{{background:#f0fdf4;color:#15803d;padding:1px 6px;border-radius:3px;font-size:11px}}
.review-section{{flex:1;display:flex;flex-direction:column}}
.status-toggle{{display:flex;gap:8px;margin-bottom:12px}}
.status-btn{{flex:1;padding:10px;border:2px solid #e5e7eb;border-radius:8px;background:#fff;cursor:pointer;font-size:14px;text-align:center;transition:all .15s}}
.status-btn.approved-btn.selected{{border-color:#10b981;background:#dcfce7}}
.status-btn.revision-btn.selected{{border-color:#f59e0b;background:#fef3c7}}
.pins-list{{flex:1;overflow-y:auto}}
.pin-item{{padding:10px 12px;border:1px solid #e5e7eb;border-radius:6px;margin-bottom:8px;font-size:13px;display:flex;gap:8px;align-items:flex-start}}
.pin-item .pin-num{{width:20px;height:20px;background:#f59e0b;color:#fff;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;flex-shrink:0;margin-top:2px}}
.pin-item textarea{{flex:1;border:1px solid #e5e7eb;border-radius:4px;padding:6px;font-size:13px;resize:vertical;min-height:40px;font-family:inherit}}
.pin-item .del-btn{{color:#a1a1aa;cursor:pointer;font-size:16px;flex-shrink:0}}
.pin-item .del-btn:hover{{color:#ef4444}}
.add-hint{{text-align:center;color:#a1a1aa;font-size:13px;padding:16px}}
.source-badge{{font-size:11px;padding:2px 8px;border-radius:4px;background:#8b5cf620;color:#8b5cf6}}
</style></head><body>
<div class="topbar">
  <a href="/">Home</a>
  <h2>{sid} {name}</h2>
  <span class="source-badge">{preview_source}</span>
  {prev_btn} {next_btn}
</div>
<div class="main">
  <div class="preview-panel">
    <div class="preview-container" id="previewContainer">
      <div class="click-hint">Click anywhere to add a comment pin</div>
    </div>
  </div>
  <div class="side-panel">
    <div class="section">
      <div class="section-title">Design Rationale</div>
      <dl>{rationale_html}</dl>
    </div>
    <div class="section review-section">
      <div class="section-title">Review</div>
      <div class="status-toggle">
        <button class="status-btn approved-btn {' selected' if status=='approved' else ''}" onclick="setStatus('approved')">Approved</button>
        <button class="status-btn revision-btn {' selected' if status=='revision' else ''}" onclick="setStatus('revision')">Needs Revision</button>
      </div>
      <div class="pins-list" id="pinsList"></div>
      <div class="add-hint">Click on the preview to pin a comment</div>
    </div>
  </div>
</div>
<script>
const SCREEN_ID="{sid}";
let pins={pins_json};
let status="{status}";

// ── Preview loading ──
const container=document.getElementById('previewContainer');
const iframe=document.createElement('iframe');
iframe.src='/preview/{sid}';
iframe.onload=()=>{{
  // Add click listener on iframe content
  try{{
    iframe.contentDocument.addEventListener('click',(e)=>{{
      const rect=iframe.getBoundingClientRect();
      const x=((e.pageX)/iframe.contentDocument.documentElement.scrollWidth*100).toFixed(1);
      const y=((e.pageY)/iframe.contentDocument.documentElement.scrollHeight*100).toFixed(1);
      addPin(parseFloat(x),parseFloat(y));
    }});
    iframe.contentDocument.body.style.cursor='crosshair';
  }}catch(err){{
    // Fallback: click on container
    container.addEventListener('click',(e)=>{{
      if(e.target===container||e.target===iframe){{
        const rect=container.getBoundingClientRect();
        const x=((e.clientX-rect.left)/rect.width*100).toFixed(1);
        const y=((e.clientY-rect.top+container.scrollTop)/(container.scrollHeight)*100).toFixed(1);
        addPin(parseFloat(x),parseFloat(y));
      }}
    }});
  }}
}};
container.appendChild(iframe);

// ── Pin management ──
function renderPins(){{
  // Render dots on preview
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
  // Render list
  const list=document.getElementById('pinsList');
  list.innerHTML='';
  pins.forEach((p,i)=>{{
    const div=document.createElement('div');
    div.className='pin-item';
    div.id='pin-item-'+i;
    div.innerHTML=`
      <span class="pin-num">${{i+1}}</span>
      <textarea placeholder="What needs to change here?" oninput="updatePin(${{i}},this.value)">${{p.comment||''}}</textarea>
      <span class="del-btn" onclick="deletePin(${{i}})">&times;</span>
    `;
    list.appendChild(div);
  }});
}}

function addPin(x,y){{
  pins.push({{id:Date.now(),x,y,comment:''}});
  if(status==='pending'||status==='approved')setStatus('revision');
  renderPins();
  saveFeedback();
  // Focus the new textarea
  setTimeout(()=>{{
    const items=document.querySelectorAll('.pin-item textarea');
    if(items.length)items[items.length-1].focus();
  }},50);
}}

function updatePin(idx,comment){{
  pins[idx].comment=comment;
  saveFeedback();
}}

function deletePin(idx){{
  pins.splice(idx,1);
  renderPins();
  saveFeedback();
  if(pins.length===0&&status==='revision')setStatus('pending');
}}

function highlightPin(idx){{
  const el=document.getElementById('pin-item-'+idx);
  if(el){{el.scrollIntoView({{behavior:'smooth'}});el.style.background='#fef3c7';setTimeout(()=>el.style.background='',1500)}}
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

class ReviewHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/":
            spec = load_spec()
            sm = load_experience_map()
            fb = load_feedback()
            html = render_dashboard(spec, sm, fb)
            self._html(html)

        elif path.startswith("/screen/"):
            screen_id = path.split("/screen/")[1]
            spec = load_spec()
            sm = load_experience_map()
            fb = load_feedback()
            html = render_screen_detail(screen_id, spec, sm, fb)
            self._html(html)

        elif path.startswith("/preview/"):
            screen_id = path.split("/preview/")[1]
            spec = load_spec()
            # Try Stitch first
            stitch = get_stitch_html(screen_id)
            if stitch:
                self._html(stitch)
                return
            # Try preview files or skeleton
            preview = get_preview_html(screen_id, spec)
            if preview:
                self._html(preview)
            else:
                self._html("<h2>No preview available</h2>")

        elif path.startswith("/stitch-image/"):
            screen_id = path.split("/stitch-image/")[1]
            img_path = get_stitch_image(screen_id)
            if img_path:
                ext = os.path.splitext(img_path)[1]
                mime = {"png": "image/png", "jpg": "image/jpeg", "webp": "image/webp"}.get(ext.lstrip("."), "image/png")
                with open(img_path, "rb") as f:
                    data = f.read()
                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            else:
                self.send_response(404)
                self.end_headers()

        elif path == "/api/screens":
            spec = load_spec()
            self._json(spec)

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
            print(f"UI feedback submitted! Saved to {FEEDBACK_PATH}")
            print(f"  Round:    {fb.get('round', 1)}")
            print(f"  Approved: {len(approved)}")
            print(f"  Revision: {len(revision)}")
            if revision:
                print(f"\nScreens needing revision:")
                for sid in revision:
                    pins = screens[sid].get("pins", [])
                    print(f"  - {sid}: {len(pins)} pin(s)")
                    for p in pins:
                        print(f"      {p.get('comment','')}")
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
        pass  # Suppress default logging


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # Kill any other review servers to avoid multiple browser windows
    C.kill_other_review_servers(PORT)

    server = http.server.HTTPServer((HOST, PORT), ReviewHandler)
    url = f"http://{HOST}:{PORT}"
    if HOST == "0.0.0.0":
        import socket
        local_ip = socket.gethostbyname(socket.gethostname())
        print(f"UI Review Server started:")
        print(f"  Local:   http://localhost:{PORT}")
        print(f"  Network: http://{local_ip}:{PORT}")
    else:
        print(f"UI Review Server started: {url}")
    print(f"Reading from: {UI_DIR}")
    print(f"Feedback:     {FEEDBACK_PATH}")
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
