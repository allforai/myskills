#!/usr/bin/env python3
"""Two-column completeness — the report that cannot lie.

Buckets every node into verified / unverified / failed using the evidence-derived
state (check_evidence.derive_state), and reports `verified_pct` as the headline.
`unverified` (generated but unproven) is surfaced loudly and is NEVER counted in
the numerator — so a product that self-attested 94.65% but has no real evidence
reads as e.g. "verified 28% / unverified 67%", matching reality.

Hollowness (ADR-0008): the judgement "is this feature fake" left /run with the
hollowness-detector capability; it is cross-exam's, made by a party that did not
write the code. What stays here is machine-decidable and needs no judgement: a
runtime entry whose request went through a mock layer, or whose response is the
canned fixture the mock serves, is refused with the reason strings cross-exam's
renderer uses (`_content_reason`) and read as `unverified`. `served_by` is the
ledger-entry field: `{host, process, mock_layers[], fixtures[]?}`, on the entry's
`verification` or beside it. The fixture comparison and its literals live in
check_evidence, where the ledger-entry gate (#59) refuses with the same words.
"""
import json
import os
import sys

from check_evidence import derive_state, fixture_match_reason, response_text


def _served_by(entry):
    v = entry.get("verification") or {}
    served = v.get("served_by")
    if not isinstance(served, dict):
        served = entry.get("served_by")
    return served if isinstance(served, dict) else {}


def _response_text(entry, base_dir):
    """The body the evidence answered with: a capture record's stdout, else the file as-is."""
    ev = (entry.get("verification") or {}).get("evidence_path")
    if not ev:
        return None
    return response_text(ev if os.path.isabs(ev) else os.path.join(base_dir, ev))


# a runtime method exercises the product; the node must say where its requests went. real-test is a
# suite run — a mechanical gate — and needs no destination.
RUNTIME_METHODS = ("real-run", "real-api", "db-query", "screenshot")


def hollow_reason(entry, base_dir="."):
    """Why a green entry may not count, in cross-exam's words; "" when it may."""
    served = _served_by(entry)
    method = (entry.get("verification") or {}).get("method")
    if method in RUNTIME_METHODS and not served:
        return "runtime 节点未报请求去向 served_by（host / process / mock_layers），不计 verified"
    layers = served.get("mock_layers")
    if isinstance(layers, list) and layers:
        return "经 mock 层（" + ", ".join(map(str, layers)) + "）的 runtime 不能判 done"
    response = _response_text(entry, base_dir)
    return fixture_match_reason([] if response is None else [response], served.get("fixtures"), base_dir)


def compute_completeness(workflow, base_dir="."):
    tl = workflow.get("transition_log", [])
    by_node = {}
    for e in tl:
        nid = e.get("node") or e.get("node_id")
        if nid:
            by_node[nid] = e  # last entry for a node wins
    states, reasons = {}, {}
    for nid, e in by_node.items():
        state = derive_state(e, base_dir)
        reason = hollow_reason(e, base_dir) if state == "verified" else ""
        states[nid] = "unverified" if reason else state
        reasons[nid] = reason
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
             "method": (by_node[nid].get("verification") or {}).get("method", "none"),
             "reason": reasons[nid]}
            for nid in sorted(states)
        ],
        "refused": [{"node_id": nid, "reason": reasons[nid]} for nid in sorted(states) if reasons[nid]],
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
    for item in r["refused"]:
        print(f"  ! refused, not counted: {item['node_id']} — {item['reason']}")
    if r["critical_unverified"]:
        print(f"  ! critical flows lacking real evidence: {', '.join(r['critical_unverified'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
