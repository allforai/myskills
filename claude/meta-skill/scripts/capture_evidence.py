#!/usr/bin/env python3
"""Capture evidence — anti-fabrication L1 (provenance over content).

The agent chooses WHICH command to run; THIS script records what actually
happened — exit code, stdout, stderr, sha256. The agent cannot author the output,
so evidence is a structured, reproducible execution record rather than free text
it could fabricate.

Usage: capture_evidence.py <evidence_path> -- <cmd> [args...]

Ledger-shaped entries (ADR-0008, #59): a runtime gate hands in a draft entry —
what it observed (medium, verdict, served_by, readback, evidence dir, images,
key observation) — and this script adds what the gate must not author: the
build identity of the whole tree (shared engine), probed_at with an offset
when the draft has none, the screenshot digests and the author marker. The
entry is validated the way the gate will be checked and appended to
`<run>/evidence-entries/<node_id>.json`; a refused draft writes nothing.

Usage: capture_evidence.py entry <run_dir> <draft.json> --node <node_id> --capability <name>
                           [--root .] [--artifact <path>...]
"""
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from check_evidence import AUTHOR_PIPELINE, BUILD_EXCLUDES, ENTRIES_SCHEMA, engine, entries_path, entry_reason

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


# --- ledger-shaped entries ---

def _image_digests(entry, run_dir):
    """SHA-256 of every listed screenshot under the entry's evidence directory; a ref the engine cannot
    resolve is left for the validator to name."""
    ev = engine("evidence")
    directory, reason = ev.evidence_dir(entry, run_dir)
    if reason or not isinstance(entry.get("images"), list):
        return {}
    digests = {}
    for ref in entry["images"]:
        path, reason = ev.artifact(directory, ref)
        if not reason:
            digests[ref] = ev.digest(path)
    return digests


def write_entry(run_dir, draft, root, node_id, capability, artifacts=(), now=None):
    """(entry, '') after appending the completed entry to <run_dir>/evidence-entries/<node_id>.json, or
    (entry, reason) with nothing written; (None, reason) when the tree at `root` cannot be identified."""
    if not isinstance(draft, dict):
        return None, "条目须是对象"
    identity = engine("identity")
    if identity is None:
        return None, "证据引擎不可用：scripts/engine 未随插件安装"
    artifacts = [Path(root) / a for a in artifacts]
    build = identity.build_identity(root, artifacts, BUILD_EXCLUDES)
    if build["reason"]:
        return None, build["reason"]
    run_dir = Path(run_dir)
    entry = dict(draft)
    entry["build"] = build["build"]
    entry["build_excludes"] = list(BUILD_EXCLUDES)
    if artifacts:   # what entered the artifact digest, so a reader recomputes the same value
        entry["build_artifacts"] = [a.resolve().relative_to(Path(root).resolve()).as_posix() for a in artifacts]
    if not entry.get("probed_at"):
        entry["probed_at"] = (now or datetime.now().astimezone()).isoformat(timespec="seconds")
    entry["author"] = {"pipeline": AUTHOR_PIPELINE, "node_id": node_id, "capability": capability}
    if isinstance(entry.get("images"), list):
        entry["image_digests"] = _image_digests(entry, run_dir)
    reason = entry_reason(entry, run_dir, root, node_id, artifacts)
    if reason:
        return entry, reason
    path = entries_path(run_dir, node_id)
    try:
        stored = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    except (OSError, ValueError, UnicodeError) as exc:
        return entry, "证据条目文件不可读: %s（%s）" % (path.as_posix(), exc)
    entries = stored.get("entries") if isinstance(stored, dict) and isinstance(stored.get("entries"), list) else []
    entries.append(entry)
    path.parent.mkdir(parents=True, exist_ok=True)
    root = Path(root).resolve()
    shown = run_dir.resolve().relative_to(root).as_posix() if root in run_dir.resolve().parents else run_dir.as_posix()
    path.write_text(json.dumps({"schema": ENTRIES_SCHEMA, "run_dir": shown, "entries": entries},
                               ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return entry, ""


def entry_command(argv):
    import argparse
    parser = argparse.ArgumentParser(prog="capture_evidence.py entry")
    parser.add_argument("run_dir")
    parser.add_argument("draft")
    parser.add_argument("--node", required=True)
    parser.add_argument("--capability", required=True)
    parser.add_argument("--root", default=".")
    parser.add_argument("--artifact", action="append", default=[])
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    try:
        draft = json.loads(Path(args.draft).read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError) as exc:
        print("REFUSED: 草稿不可读 %s（%s）" % (args.draft, exc))
        return 1
    run_dir = Path(args.run_dir) if Path(args.run_dir).is_absolute() else root / args.run_dir
    entry, reason = write_entry(run_dir, draft, root, args.node, args.capability, args.artifact)
    if reason:
        print("REFUSED: " + reason)
        return 1
    print("entry recorded: build=%s probed_at=%s -> %s" % (
        entry["build"], entry["probed_at"], entries_path(args.run_dir, args.node).as_posix()))
    return 0


def main(argv):
    if len(argv) > 1 and argv[1] == "entry":
        return entry_command(argv[2:])
    if "--" not in argv or len(argv) < 2:
        print("Usage: capture_evidence.py <evidence_path> -- <cmd> [args...]\n"
              "       capture_evidence.py entry <run_dir> <draft.json> --node <node_id> --capability <name>")
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
