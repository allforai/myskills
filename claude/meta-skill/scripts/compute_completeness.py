#!/usr/bin/env python3
"""Two-column completeness — the report that cannot lie.

Buckets every node into verified / unverified / failed using the evidence-derived
state (check_evidence.derive_state), and reports `verified_pct` as the headline.
`unverified` (generated but unproven) is surfaced loudly and is NEVER counted in
the numerator — so a product that self-attested 94.65% but has no real evidence
reads as e.g. "verified 28% / unverified 67%", matching reality.
"""
import json
import os
import sys

from check_evidence import derive_state


def compute_completeness(workflow, base_dir="."):
    tl = workflow.get("transition_log", [])
    by_node = {}
    for e in tl:
        nid = e.get("node") or e.get("node_id")
        if nid:
            by_node[nid] = e  # last entry for a node wins
    states = {nid: derive_state(e, base_dir) for nid, e in by_node.items()}
    total = len(states)

    def count(s):
        return sum(1 for v in states.values() if v == s)

    verified, unverified, failed = count("verified"), count("unverified"), count("failed")

    def pct(n):
        return round(100.0 * n / total, 1) if total else 0.0

    critical = {n["node_id"] for n in workflow.get("nodes", []) if n.get("critical")}
    critical_unverified = sorted(nid for nid in critical if states.get(nid) != "verified")

    return {
        "total": total,
        "verified": verified,
        "unverified": unverified,
        "failed": failed,
        "verified_pct": pct(verified),
        "unverified_pct": pct(unverified),
        "failed_pct": pct(failed),
        "by_node": [
            {"node_id": nid, "state": states[nid],
             "method": (by_node[nid].get("verification") or {}).get("method", "none")}
            for nid in sorted(states)
        ],
        "critical_unverified": critical_unverified,
    }


def main(argv):
    base = argv[1] if len(argv) > 1 else "."
    wf_path = os.path.join(base, ".allforai/bootstrap/workflow.json")
    with open(wf_path) as f:
        wf = json.load(f)
    r = compute_completeness(wf, base)
    out_path = os.path.join(base, ".allforai/bootstrap/completeness-report.json")
    with open(out_path, "w") as f:
        json.dump(r, f, indent=2)
    print(f"Completeness (evidence-anchored, {r['total']} nodes):")
    print(f"  VERIFIED   真验过:      {r['verified']:>4}  ({r['verified_pct']}%)   <- headline")
    print(f"  unverified 只生成没验:  {r['unverified']:>4}  ({r['unverified_pct']}%)")
    print(f"  failed:                {r['failed']:>4}  ({r['failed_pct']}%)")
    if r["critical_unverified"]:
        print(f"  ! critical flows lacking real evidence: {', '.join(r['critical_unverified'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
