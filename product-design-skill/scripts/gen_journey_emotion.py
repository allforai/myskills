#!/usr/bin/env python3
"""Phase 3: Generate journey-emotion-map from product-map data.

Usage:
    python3 gen_journey_emotion.py <BASE_PATH> [--mode auto]
"""
import sys, os, json, datetime

sys.path.insert(0, os.path.dirname(__file__))
import _common as C


def main():
    if len(sys.argv) < 2:
        print("Usage: gen_journey_emotion.py <BASE_PATH> [--mode auto]")
        sys.exit(1)

    BASE = sys.argv[1]
    mode = "auto"
    if "--mode" in sys.argv:
        idx = sys.argv.index("--mode")
        if idx + 1 < len(sys.argv):
            mode = sys.argv[idx + 1]

    # ── load inputs ──
    roles = C.load_role_profiles(BASE)
    flows = C.load_business_flows(BASE)
    tasks_inv = C.load_task_inventory(BASE)

    if not flows:
        print("ERROR: business-flows.json not found or empty. Run product-map first.")
        sys.exit(1)

    # ── build journey lines from business flows ──
    journey_lines = []
    for i, flow in enumerate(flows):
        fid = flow.get("id") or flow.get("flow_id") or f"F{i+1:02d}"
        fname = flow.get("name") or flow.get("flow_name") or f"Flow {i+1}"
        frole = flow.get("role", flow.get("owner_role", ""))

        nodes_raw = C.get_flow_nodes(flow)
        emotion_nodes = []
        for step_idx, node in enumerate(nodes_raw):
            # Support both task_ref (canonical) and task_id (legacy)
            tid = node.get("task_ref", node.get("task_id", node.get("id", "")))
            task = tasks_inv.get(tid, {})
            # Extract action from node name, then task name, then placeholder
            action = node.get("name", node.get("action", task.get("name", f"Step {step_idx+1}")))
            # Extract role from node, then flow
            node_role = node.get("role", frole)

            emotion_nodes.append({
                "step": step_idx + 1,
                "action": action,
                "role": node_role,
                "emotion": "neutral",
                "intensity": 3,
                "risk": "low",
                "design_hint": "",
            })

        journey_lines.append({
            "id": f"JL{i+1:02d}",
            "name": fname,
            "role": frole,
            "source_flow": fid,
            "emotion_nodes": emotion_nodes,
            "human_decision": True,
        })

    result = {
        "journey_lines": journey_lines,
        "decision_log": [],
        "generated_at": datetime.datetime.now().isoformat(),
    }

    # ── write output ──
    out_dir = os.path.join(BASE, "experience-map")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "journey-emotion-map.json")
    C.write_json(out_path, result)
    print(f"OK: {out_path} ({len(journey_lines)} journey lines)")

    # ── pipeline decision ──
    C.append_pipeline_decision(BASE, "journey-emotion", {
        "journey_line_count": len(journey_lines),
        "total_emotion_nodes": sum(len(jl["emotion_nodes"]) for jl in journey_lines),
    })


if __name__ == "__main__":
    main()
