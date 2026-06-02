#!/usr/bin/env python3
"""Capture evidence — anti-fabrication L1 (provenance over content).

The agent chooses WHICH command to run; THIS script records what actually
happened — exit code, stdout, stderr, sha256. The agent cannot author the output,
so evidence is a structured, reproducible execution record rather than free text
it could fabricate.

Usage: capture_evidence.py <evidence_path> -- <cmd> [args...]
"""
import hashlib
import json
import os
import subprocess
import sys

SCHEMA = "capture_evidence/v1"


def capture(cmd):
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "schema": SCHEMA,
        "command": cmd,
        "exit_code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "stdout_sha256": hashlib.sha256(proc.stdout.encode()).hexdigest(),
    }


def write_capture(evidence_path, cmd):
    rec = capture(cmd)
    d = os.path.dirname(evidence_path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(evidence_path, "w") as f:
        json.dump(rec, f, indent=2)
    return rec


def main(argv):
    if "--" not in argv or len(argv) < 2:
        print("Usage: capture_evidence.py <evidence_path> -- <cmd> [args...]")
        return 2
    sep = argv.index("--")
    evidence_path = argv[1]
    cmd = argv[sep + 1:]
    if not cmd:
        print("no command after --")
        return 2
    rec = write_capture(evidence_path, cmd)
    print(f"captured: exit={rec['exit_code']} sha={rec['stdout_sha256'][:12]} -> {evidence_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
