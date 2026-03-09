#!/usr/bin/env python3
"""Phase 4.5: Interaction quality gate — validate experience-map continuity.

Evaluates operation lines for step count, context switches, wait feedback,
and thumb zone compliance. Back-fills quality_score into experience-map.

Usage:
    python3 gen_interaction_gate.py <BASE_PATH> [--threshold 70]
"""
import sys, os, json, datetime

sys.path.insert(0, os.path.dirname(__file__))
import _common as C

DEFAULT_THRESHOLD = 70
MAX_STEPS_IDEAL = 7
MAX_CONTEXT_SWITCHES = 2


def evaluate_line(ol, xv_findings=None):
    """Evaluate a single operation line, return score dict."""
    cont = ol.get("continuity", {})
    total_steps = cont.get("total_steps", len(ol.get("nodes", [])))
    context_switches = cont.get("context_switches", 0)
    wait_points = cont.get("wait_points", [])

    nodes = ol.get("nodes", [])
    issues = []

    # ── Step count score (0-30) ──
    if total_steps <= MAX_STEPS_IDEAL:
        step_score = 30
    elif total_steps <= MAX_STEPS_IDEAL + 2:
        step_score = 20
    else:
        step_score = max(0, 30 - (total_steps - MAX_STEPS_IDEAL) * 5)
        issues.append({
            "node": "-",
            "type": "step_count",
            "detail": f"Operation line has {total_steps} steps (ideal <= {MAX_STEPS_IDEAL})",
        })

    # ── Context switch score (0-25) ──
    if context_switches <= MAX_CONTEXT_SWITCHES:
        ctx_score = 25
    else:
        ctx_score = max(0, 25 - (context_switches - MAX_CONTEXT_SWITCHES) * 10)
        issues.append({
            "node": "-",
            "type": "context_switch",
            "detail": f"{context_switches} context switches (ideal <= {MAX_CONTEXT_SWITCHES})",
        })

    # ── Wait feedback coverage (0-25) ──
    wait_coverage = 1.0 if not wait_points else 0.8
    wait_score = int(25 * wait_coverage)

    # ── Thumb zone compliance (0-20) ──
    nn_count = 0
    total_screens = 0
    for node in nodes:
        for s in node.get("screens", []):
            total_screens += 1
            if s.get("non_negotiable"):
                nn_count += 1

    thumb_compliance = nn_count / max(total_screens, 1)
    thumb_score = int(20 * thumb_compliance)
    if thumb_compliance < 0.5 and total_screens > 0:
        issues.append({
            "node": "-",
            "type": "thumb_zone",
            "detail": f"Only {nn_count}/{total_screens} screens have non_negotiable constraints",
        })

    score = step_score + ctx_score + wait_score + thumb_score

    # ── XV finding penalties ──
    if xv_findings:
        screen_ids_in_line = {s["id"] for n in nodes for s in n.get("screens", [])}
        for finding in xv_findings:
            raw = finding.get("raw_findings", {})
            if not isinstance(raw, dict):
                continue
            for iss in raw.get("issues", []):
                sev = iss.get("severity", "low")
                desc = iss.get("description", "")
                # Check if this finding relates to any screen in this line
                if any(sid in desc for sid in screen_ids_in_line):
                    if sev == "high":
                        score -= 5
                    elif sev == "critical":
                        score -= 10
        score = max(0, score)

    return {
        "line_id": ol["id"],
        "steps": total_steps,
        "context_switches": context_switches,
        "wait_feedback_coverage": round(wait_coverage, 2),
        "thumb_zone_compliance": round(thumb_compliance, 2),
        "score": score,
        "issues": issues,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: gen_interaction_gate.py <BASE_PATH> [--threshold 70]")
        sys.exit(1)

    BASE = sys.argv[1]
    threshold = DEFAULT_THRESHOLD
    if "--threshold" in sys.argv:
        idx = sys.argv.index("--threshold")
        if idx + 1 < len(sys.argv):
            threshold = int(sys.argv[idx + 1])

    # ── load experience-map ──
    op_lines, screen_index, loaded = C.load_experience_map(BASE)
    if not loaded:
        print("ERROR: experience-map.json not found. Run experience-map first.")
        sys.exit(1)

    # ── load full context (for XV findings) ──
    ctx = C.load_full_context(BASE)

    # ── evaluate each line ──
    line_results = []
    for ol in op_lines:
        line_results.append(evaluate_line(ol, xv_findings=ctx.xv_findings))

    # ── determine overall result ──
    all_pass = all(lr["score"] >= threshold for lr in line_results)
    total_issues = sum(len(lr["issues"]) for lr in line_results)

    gate = {
        "gate_result": "pass" if all_pass else "warn",
        "lines": line_results,
        "threshold": threshold,
        "recommendation": f"{'pass' if all_pass else 'review'}, {total_issues} issue(s) to address",
        "generated_at": datetime.datetime.now().isoformat(),
    }

    # ── write gate output ──
    out_dir = os.path.join(BASE, "experience-map")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "interaction-gate.json")
    C.write_json(out_path, gate)
    print(f"OK: {out_path} (result={gate['gate_result']}, {total_issues} issues)")

    # ── back-fill quality_score into experience-map ──
    em_path = os.path.join(BASE, "experience-map/experience-map.json")
    em_data = C.load_json(em_path)
    if em_data and isinstance(em_data, dict):
        score_map = {lr["line_id"]: lr["score"] for lr in line_results}
        for ol in em_data.get("operation_lines", []):
            if ol["id"] in score_map:
                ol.setdefault("continuity", {})["quality_score"] = score_map[ol["id"]]
        C.write_json(em_path, em_data)
        print(f"OK: back-filled quality_score into {em_path}")

    # ── pipeline decision ──
    C.append_pipeline_decision(BASE, "interaction-gate", {
        "gate_result": gate["gate_result"],
        "threshold": threshold,
        "total_issues": total_issues,
        "line_scores": {lr["line_id"]: lr["score"] for lr in line_results},
    })


if __name__ == "__main__":
    main()
