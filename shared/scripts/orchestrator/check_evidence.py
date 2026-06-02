#!/usr/bin/env python3
"""Evidence gate — the deterministic keystone of verification honesty.

Derives a node's TRUE state from its recorded `verification` evidence, downgrading
any "verified" claim that lacks real, on-disk, independently-produced proof. This
makes the lazy default path (write a PASS report, no evidence) score `unverified`
rather than inflating completeness — regardless of how the LLM behaves.

  verified    <- status != failed AND verification.method != 'none'
                 AND evidence_path EXISTS on disk
                 AND verifier present AND verifier != generator (no self-grading)
  unverified  <- generated but the above is not satisfied
  failed      <- status failed
"""
import json
import os
import sys


def derive_state(entry, base_dir="."):
    if entry.get("status") == "failed":
        return "failed"
    v = entry.get("verification") or {}
    method = v.get("method", "none")
    if method == "none":
        return "unverified"
    ev = v.get("evidence_path")
    if not ev:
        return "unverified"
    resolved = ev if os.path.isabs(ev) else os.path.join(base_dir, ev)
    if not os.path.exists(resolved):
        return "unverified"  # claimed evidence does not exist -> downgrade
    if not v.get("verifier"):
        return "unverified"
    gen = entry.get("generated_by")
    if gen and gen == v.get("verifier"):
        return "unverified"  # verifier == generator: self-graded homework
    return "verified"


def main(argv):
    base = argv[1] if len(argv) > 1 else "."
    wf_path = os.path.join(base, ".allforai/bootstrap/workflow.json")
    with open(wf_path) as f:
        wf = json.load(f)
    downgraded = []
    for e in wf.get("transition_log", []):
        nid = e.get("node") or e.get("node_id")
        v = e.get("verification") or {}
        if v.get("method", "none") != "none" and derive_state(e, base) != "verified":
            downgraded.append(nid)
    if downgraded:
        print("EVIDENCE-DOWNGRADED (claimed verified but evidence missing/self-graded):")
        for nid in downgraded:
            print(f"  - {nid}")
    else:
        print("OK: no false 'verified' claims (every verified node has real evidence)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
