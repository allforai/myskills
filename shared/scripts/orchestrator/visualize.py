#!/usr/bin/env python3
"""Generate an HTML visualization of state-machine.json.

Usage:
    python visualize.py .allforai/bootstrap/state-machine.json [-o status.html] [--open]

Produces a standalone HTML file with:
  - Mermaid.js DAG (nodes colored by status, edges from file dependencies)
  - Transition log timeline
"""

import argparse
import html
import json
import os
import subprocess
import sys
from typing import Any, Dict, List, Set


def _extract_file_deps(requires: list) -> Set[str]:
    """Extract file_exists paths from require declarations."""
    paths = set()
    for req in (requires or []):
        if isinstance(req, dict) and "file_exists" in req:
            paths.add(req["file_exists"])
    return paths


def _build_edges(nodes: List[Dict]) -> List[tuple]:
    """Build edges from file dependencies: producer.exit → consumer.entry."""
    # Map: file_path → producer node id
    producers = {}
    for n in nodes:
        nid = n.get("id", "")
        for f in _extract_file_deps(n.get("exit_requires", [])):
            producers[f] = nid

    edges = []
    for n in nodes:
        nid = n.get("id", "")
        for f in _extract_file_deps(n.get("entry_requires", [])):
            if f in producers and producers[f] != nid:
                edges.append((producers[f], nid))
    return edges


def _node_status(nid: str, progress: dict) -> str:
    """Determine node status from progress."""
    if nid in progress.get("completed_nodes", []):
        return "completed"
    if nid == progress.get("current_node"):
        return "running"
    # Check transition_log for failures
    for entry in reversed(progress.get("transition_log", [])):
        if entry.get("node") == nid:
            if entry.get("to_status") == "failure":
                return "failed"
            break
    return "waiting"


STATUS_COLORS = {
    "completed": "#22c55e",
    "running": "#eab308",
    "failed": "#ef4444",
    "waiting": "#9ca3af",
}

STATUS_MERMAID_CLASS = {
    "completed": "fill:#22c55e,stroke:#16a34a,color:#fff",
    "running": "fill:#eab308,stroke:#ca8a04,color:#fff",
    "failed": "fill:#ef4444,stroke:#dc2626,color:#fff",
    "waiting": "fill:#e5e7eb,stroke:#9ca3af,color:#374151",
}


def _extract_backtrack_edges(transition_log: list) -> List[Dict]:
    """Extract backward transitions from transition_log.

    A backtrack happens when node B fails, diagnosis runs, and the next
    transition is to an upstream node A (which was already completed).
    """
    backtracks = []
    for i in range(1, len(transition_log)):
        prev = transition_log[i - 1]
        curr = transition_log[i]
        prev_node = prev.get("node", "")
        curr_node = curr.get("node", "")
        # Backtrack = previous node failed/completed, current node is different
        # and current node was previously completed (re-execution)
        if prev_node != curr_node and curr.get("from_status") in ("completed", "failed"):
            if prev.get("to_status") == "failure":
                backtracks.append({
                    "from": prev_node,
                    "to": curr_node,
                    "iter": curr.get("iter", "?"),
                    "reason": prev.get("summary", ""),
                })
    return backtracks


def _extract_retry_counts(transition_log: list) -> Dict[str, int]:
    """Count how many times each node appears in the log."""
    counts: Dict[str, int] = {}
    for entry in transition_log:
        nid = entry.get("node", "")
        counts[nid] = counts.get(nid, 0) + 1
    return counts


def generate_mermaid(nodes: List[Dict], edges: List[tuple], progress: dict) -> str:
    """Generate Mermaid flowchart definition."""
    lines = ["graph TD"]
    transition_log = progress.get("transition_log", [])
    retry_counts = _extract_retry_counts(transition_log)
    backtracks = _extract_backtrack_edges(transition_log)

    for n in nodes:
        nid = n.get("id", "")
        safe_id = nid.replace("-", "_")
        fan_out = n.get("fan_out")
        label = f"{nid}"
        if fan_out:
            label += " [fan_out]"
        count = retry_counts.get(nid, 0)
        if count > 1:
            label += f" x{count}"
        lines.append(f'    {safe_id}["{label}"]')

    # Static dependency edges (grey, thin)
    for src, dst in edges:
        safe_src = src.replace("-", "_")
        safe_dst = dst.replace("-", "_")
        lines.append(f"    {safe_src} --> {safe_dst}")

    # Backtrack edges (red, dashed, with label)
    for bt in backtracks:
        safe_from = bt["from"].replace("-", "_")
        safe_to = bt["to"].replace("-", "_")
        lines.append(f'    {safe_from} -.->|"iter {bt["iter"]} backtrack"| {safe_to}')

    # Self-retry loops (orange, for nodes retried in place)
    seen_retries = set()
    for i in range(1, len(transition_log)):
        prev = transition_log[i - 1]
        curr = transition_log[i]
        if prev.get("node") == curr.get("node") and prev.get("to_status") == "failure":
            nid = curr.get("node", "")
            if nid not in seen_retries:
                safe_id = nid.replace("-", "_")
                lines.append(f'    {safe_id} -.->|"retry"| {safe_id}')
                seen_retries.add(nid)

    # Node styles
    for n in nodes:
        nid = n.get("id", "")
        safe_id = nid.replace("-", "_")
        status = _node_status(nid, progress)
        style = STATUS_MERMAID_CLASS.get(status, "")
        lines.append(f"    style {safe_id} {style}")

    # Backtrack edge styles
    for i, bt in enumerate(backtracks):
        safe_from = bt["from"].replace("-", "_")
        safe_to = bt["to"].replace("-", "_")
        lines.append(f"    linkStyle {len(edges) + i} stroke:#ef4444,stroke-width:2px,stroke-dasharray:5")

    return "\n".join(lines)


def generate_log_html(transition_log: list) -> str:
    """Generate HTML for transition log timeline."""
    if not transition_log:
        return '<p class="empty">No transitions recorded yet.</p>'

    rows = []
    for entry in transition_log:
        iter_n = entry.get("iter", "?")
        node = html.escape(str(entry.get("node", "")))
        from_s = entry.get("from_status", "")
        to_s = entry.get("to_status", "")
        ts = entry.get("ts", "")
        summary = html.escape(str(entry.get("summary", "")))
        suggest = entry.get("suggest_next", "")

        color = STATUS_COLORS.get(to_s, "#9ca3af")
        suggest_html = f' <span class="suggest">→ {html.escape(str(suggest))}</span>' if suggest else ""

        rows.append(
            f'<tr>'
            f'<td class="iter">#{iter_n}</td>'
            f'<td class="node">{node}</td>'
            f'<td><span class="badge" style="background:{color}">{from_s} → {to_s}</span></td>'
            f'<td class="summary">{summary}{suggest_html}</td>'
            f'<td class="ts">{ts}</td>'
            f'</tr>'
        )

    return (
        '<table>'
        '<thead><tr><th>Iter</th><th>Node</th><th>Transition</th><th>Summary</th><th>Time</th></tr></thead>'
        '<tbody>' + "\n".join(rows) + '</tbody>'
        '</table>'
    )


def generate_stats_html(nodes: list, progress: dict) -> str:
    """Generate summary stats."""
    total = len(nodes)
    completed = len(progress.get("completed_nodes", []))
    iterations = progress.get("iteration_count", 0)
    diagnoses = len(progress.get("diagnosis_history", []))

    pct = int(completed / total * 100) if total else 0

    return (
        f'<div class="stats">'
        f'<div class="stat"><span class="num">{completed}/{total}</span><span class="label">Nodes Done</span></div>'
        f'<div class="stat"><span class="num">{pct}%</span><span class="label">Progress</span></div>'
        f'<div class="stat"><span class="num">{iterations}</span><span class="label">Iterations</span></div>'
        f'<div class="stat"><span class="num">{diagnoses}</span><span class="label">Diagnoses</span></div>'
        f'</div>'
    )


HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Orchestrator Status</title>
<script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #0f172a; color: #e2e8f0; padding: 24px; }
  h1 { font-size: 20px; font-weight: 600; margin-bottom: 8px; }
  h2 { font-size: 16px; font-weight: 500; margin: 24px 0 12px; color: #94a3b8; }
  .stats { display: flex; gap: 16px; margin: 16px 0; }
  .stat { background: #1e293b; border-radius: 8px; padding: 12px 20px; text-align: center; }
  .stat .num { display: block; font-size: 24px; font-weight: 700; color: #f8fafc; }
  .stat .label { font-size: 12px; color: #64748b; }
  .legend { display: flex; gap: 16px; margin: 12px 0; font-size: 13px; }
  .legend span { display: flex; align-items: center; gap: 4px; }
  .legend .dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
  .graph-container { background: #1e293b; border-radius: 8px; padding: 20px; margin: 16px 0;
                     overflow-x: auto; }
  .mermaid { display: flex; justify-content: center; }
  table { width: 100%; border-collapse: collapse; margin: 8px 0; font-size: 13px; }
  thead { color: #64748b; text-transform: uppercase; font-size: 11px; letter-spacing: 0.05em; }
  th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid #1e293b; }
  tr:hover { background: #1e293b; }
  .iter { color: #64748b; font-variant-numeric: tabular-nums; }
  .node { font-family: monospace; color: #38bdf8; }
  .badge { padding: 2px 8px; border-radius: 4px; font-size: 11px; color: #fff; }
  .summary { max-width: 400px; }
  .suggest { color: #a78bfa; font-style: italic; }
  .ts { color: #64748b; font-size: 11px; white-space: nowrap; }
  .empty { color: #64748b; font-style: italic; padding: 20px; }
  .refresh { position: fixed; top: 16px; right: 16px; background: #334155; border: none;
             color: #e2e8f0; padding: 8px 16px; border-radius: 6px; cursor: pointer;
             font-size: 13px; }
  .refresh:hover { background: #475569; }
</style>
</head>
<body>
<h1>Orchestrator Status</h1>

{stats}

<div class="legend">
  <span><span class="dot" style="background:#22c55e"></span> Completed</span>
  <span><span class="dot" style="background:#eab308"></span> Running</span>
  <span><span class="dot" style="background:#ef4444"></span> Failed</span>
  <span><span class="dot" style="background:#9ca3af"></span> Waiting</span>
</div>

<h2>Dependency Graph</h2>
<div class="graph-container">
  <pre class="mermaid">
{mermaid}
  </pre>
</div>

<h2>Transition Log</h2>
{log}

<button class="refresh" onclick="location.reload()">Refresh</button>

<script>
  mermaid.initialize({ startOnLoad: true, theme: 'dark', flowchart: { curve: 'basis' } });
</script>
</body>
</html>
"""


def main(argv=None):
    parser = argparse.ArgumentParser(description="Visualize orchestrator state machine")
    parser.add_argument("state_machine", help="Path to state-machine.json")
    parser.add_argument("-o", "--output", default=None, help="Output HTML path (default: <dir>/status.html)")
    parser.add_argument("--open", action="store_true", help="Open in browser after generating")
    args = parser.parse_args(argv)

    with open(args.state_machine) as f:
        data = json.load(f)

    nodes = data.get("nodes", [])
    progress = data.get("progress", {})

    edges = _build_edges(nodes)
    mermaid = generate_mermaid(nodes, edges, progress)
    stats = generate_stats_html(nodes, progress)
    log = generate_log_html(progress.get("transition_log", []))

    html_content = HTML_TEMPLATE.replace("{mermaid}", mermaid).replace("{stats}", stats).replace("{log}", log)

    output_path = args.output
    if not output_path:
        output_path = os.path.join(os.path.dirname(args.state_machine), "status.html")

    with open(output_path, "w") as f:
        f.write(html_content)

    print(f"Generated: {output_path}")

    if args.open:
        if sys.platform == "darwin":
            subprocess.run(["open", output_path])
        elif sys.platform == "linux":
            subprocess.run(["xdg-open", output_path])
        else:
            print(f"Open {output_path} in your browser")


if __name__ == "__main__":
    main()
