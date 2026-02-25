#!/usr/bin/env python3
"""Generate product-map-visual.svg — role-task tree map."""
import json

BASE = "/home/dv/myskills/.allforai/product-map"

with open(f"{BASE}/role-profiles.json") as f:
    roles = json.load(f)["roles"]
with open(f"{BASE}/task-inventory.json") as f:
    tasks = json.load(f)["tasks"]
with open(f"{BASE}/conflict-report.json") as f:
    conflicts = json.load(f)

# Build role → tasks mapping
role_tasks = {}
for r in roles:
    role_tasks[r["id"]] = {"name": r["name"], "tasks": []}
for t in tasks:
    rid = t["owner_role"]
    if rid in role_tasks:
        role_tasks[rid]["tasks"].append(t)

# Conflict affected tasks
conflict_tasks = set()
for c in conflicts.get("conflicts", []):
    for tid in c.get("affected_tasks", []):
        conflict_tasks.add(tid)

# Colors
COLORS = {
    "role_fill": "#3B82F6",
    "freq_high": "#22C55E",
    "freq_mid": "#F59E0B",
    "freq_low": "#9CA3AF",
    "risk_high": "#EF4444",
    "conflict": "#F97316",
    "line": "#CBD5E1",
}

# Layout
ROLE_X = 30
ROLE_W = 160
ROLE_H = 40
TASK_X = 260
TASK_W = 260
TASK_H = 28
TASK_GAP = 6
ROLE_GROUP_GAP = 20
LEGEND_H = 50

def freq_color(f):
    if f == "高": return COLORS["freq_high"]
    if f == "中": return COLORS["freq_mid"]
    return COLORS["freq_low"]

def escape(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

# Calculate total height
y = LEGEND_H + 20
for rid, data in role_tasks.items():
    count = len(data["tasks"])
    group_h = max(ROLE_H, count * (TASK_H + TASK_GAP))
    y += group_h + ROLE_GROUP_GAP

total_h = y + 20
total_w = TASK_X + TASK_W + 60

# Build SVG
svg = []
svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total_w} {total_h}" width="{total_w}" height="{total_h}">')
svg.append('<style>text { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }</style>')
svg.append(f'<rect width="{total_w}" height="{total_h}" fill="white"/>')

# Legend
legend_items = [
    ("高频", COLORS["freq_high"]),
    ("中频", COLORS["freq_mid"]),
    ("低频", COLORS["freq_low"]),
    ("高风险", COLORS["risk_high"]),
    ("冲突", COLORS["conflict"]),
]
lx = 30
for label, color in legend_items:
    svg.append(f'<rect x="{lx}" y="15" width="16" height="16" rx="3" fill="{color}"/>')
    svg.append(f'<text x="{lx+22}" y="28" font-size="12" fill="#374151">{label}</text>')
    lx += 80

# Role-task groups
y = LEGEND_H + 20
for rid, data in role_tasks.items():
    task_list = data["tasks"]
    count = len(task_list)
    group_h = max(ROLE_H, count * (TASK_H + TASK_GAP))

    # Role box (vertically centered)
    ry = y + (group_h - ROLE_H) // 2
    svg.append(f'<rect x="{ROLE_X}" y="{ry}" width="{ROLE_W}" height="{ROLE_H}" rx="6" fill="{COLORS["role_fill"]}"/>')
    svg.append(f'<text x="{ROLE_X + ROLE_W//2}" y="{ry + ROLE_H//2 + 5}" text-anchor="middle" font-size="13" font-weight="bold" fill="white">{escape(data["name"])}</text>')

    # Tasks
    for i, t in enumerate(task_list):
        ty = y + i * (TASK_H + TASK_GAP)
        fc = freq_color(t["frequency"])

        # Connection line
        line_y1 = ry + ROLE_H // 2
        line_y2 = ty + TASK_H // 2
        svg.append(f'<path d="M{ROLE_X + ROLE_W} {line_y1} C{ROLE_X + ROLE_W + 30} {line_y1} {TASK_X - 30} {line_y2} {TASK_X} {line_y2}" stroke="{COLORS["line"]}" fill="none" stroke-width="1.5"/>')

        # Task box
        svg.append(f'<rect x="{TASK_X}" y="{ty}" width="{TASK_W}" height="{TASK_H}" rx="4" fill="{fc}"/>')

        # Task name (truncate if too long)
        tname = t["task_name"]
        if len(tname) > 16:
            tname = tname[:15] + "…"
        svg.append(f'<text x="{TASK_X + 8}" y="{ty + TASK_H//2 + 4}" font-size="11" fill="white">{escape(t["id"])} {escape(tname)}</text>')

        # Risk badge
        if t["risk_level"] == "高":
            bx = TASK_X + TASK_W - 20
            by = ty + 4
            svg.append(f'<circle cx="{bx}" cy="{by + 5}" r="5" fill="{COLORS["risk_high"]}"/>')
            svg.append(f'<text x="{bx}" y="{by + 9}" text-anchor="middle" font-size="8" fill="white">!</text>')

        # Conflict marker
        if t["id"] in conflict_tasks:
            cx = TASK_X + TASK_W - 36
            cy = ty + 4
            svg.append(f'<polygon points="{cx},{cy} {cx+5},{cy+10} {cx-5},{cy+10}" fill="{COLORS["conflict"]}"/>')

    y += group_h + ROLE_GROUP_GAP

svg.append('</svg>')

with open(f"{BASE}/product-map-visual.svg", "w", encoding="utf-8") as f:
    f.write("\n".join(svg))
print(f"Generated product-map-visual.svg ({total_w}x{total_h})")
