#!/usr/bin/env python3
"""Re-verify evidence — anti-fabrication L2 (independent reproduction).

Re-runs the command recorded in a capture_evidence/v1 record and confirms it still
passes. Fabricated evidence (a record claiming exit 0 for a command that does not
actually succeed) fails reproduction.

HONEST BOUND: this proves "the recorded command really passes now", NOT "the command
exercises the right feature." Relevance is the verify-protocol's / hollowness-detector's
job; reverify only kills records that don't reproduce.
"""
import hashlib
import json
import subprocess
import sys


def reverify(record):
    if not isinstance(record, dict) or record.get("schema") != "capture_evidence/v1":
        return {"ok": False, "reason": "not a capture_evidence/v1 record"}
    cmd = record.get("command")
    if not cmd:
        return {"ok": False, "reason": "no command in record"}
    proc = subprocess.run(cmd, capture_output=True, text=True)
    new_sha = hashlib.sha256(proc.stdout.encode()).hexdigest()
    claimed = record.get("exit_code")
    return {
        # success evidence must claim exit 0 AND reproduce exit 0
        "ok": claimed == 0 and proc.returncode == 0,
        "exit_match": proc.returncode == claimed,
        "claimed_exit": claimed,
        "actual_exit": proc.returncode,
        "sha_match": new_sha == record.get("stdout_sha256"),
    }


def main(argv):
    if len(argv) < 2:
        print("Usage: reverify.py <evidence_path.json>")
        return 2
    with open(argv[1]) as f:
        record = json.load(f)
    r = reverify(record)
    if r["ok"]:
        print(f"REPRODUCED: command re-ran exit=0 (sha_match={r.get('sha_match')})")
        return 0
    print(f"NOT REPRODUCED: {r.get('reason', '')} claimed_exit={r.get('claimed_exit')} actual_exit={r.get('actual_exit')}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
