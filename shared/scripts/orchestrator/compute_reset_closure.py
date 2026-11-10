"""Fix C2: when diagnosis resets a root-cause node, every node transitively
downstream (via hard_blocked_by) must also reset, else it runs on stale upstream.

Usage:
  compute_reset_closure.py <workflow.json> <root_id...>
      print the closure as a JSON list; changes nothing.
  compute_reset_closure.py <workflow.json> --apply --diagnosis <ref> <root_id...>
      reset the closure: every `completed` transition of a node in it becomes
      `superseded`, naming the diagnosis that reset it. Nothing is deleted, so the
      audit trail stays, and no reader of `completed` needs to know about resets.
"""
import json
import os
import sys
import tempfile
from datetime import datetime, timezone


def reset_closure(nodes, root_ids):
    reset = set(root_ids)
    changed = True
    while changed:
        changed = False
        for n in nodes:
            nid = n.get("node_id")
            if nid in reset:
                continue
            if any(dep in reset for dep in n.get("hard_blocked_by", []) or []):
                reset.add(nid)
                changed = True
    return list(reset)


def apply_reset(workflow, root_ids, diagnosis_ref, now=None):
    """Supersede the closure's completed transitions in place; return (closure, count)."""
    known = {n.get("node_id") for n in workflow.get("nodes", [])}
    unknown = sorted(set(root_ids) - known)
    if unknown:
        raise ValueError(f"unknown root node(s): {', '.join(unknown)}")
    closure = reset_closure(workflow.get("nodes", []), root_ids)
    members = set(closure)
    at = now or datetime.now(timezone.utc).isoformat()
    count = 0
    for entry in workflow.get("transition_log", []) or []:
        if not isinstance(entry, dict) or entry.get("status") != "completed":
            continue
        if entry.get("node_id", entry.get("node")) in members:
            entry["status"] = "superseded"
            entry["superseded_by"] = {"diagnosis": diagnosis_ref, "at": at}
            count += 1
    return closure, count


def _write_atomic(path, data):
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(path)), suffix=".tmp")
    with os.fdopen(fd, "w") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    os.replace(tmp, path)


def main(argv):
    args = argv[1:]
    if not args:
        print(__doc__, file=sys.stderr)
        return 2
    path, rest = args[0], args[1:]
    apply = "--apply" in rest
    diagnosis = None
    if "--diagnosis" in rest:
        i = rest.index("--diagnosis")
        if i + 1 >= len(rest):
            print("--diagnosis needs a value", file=sys.stderr)
            return 2
        diagnosis = rest[i + 1]
        rest = rest[:i] + rest[i + 2:]
    roots = [a for a in rest if a != "--apply"]
    if not roots:
        print("name at least one root node", file=sys.stderr)
        return 2
    with open(path) as fh:
        wf = json.load(fh)
    if not apply:
        print(json.dumps(reset_closure(wf.get("nodes", []), roots)))
        return 0
    if not diagnosis:
        print("--apply needs --diagnosis <ref>: a reset must name the diagnosis that caused it",
              file=sys.stderr)
        return 2
    try:
        closure, count = apply_reset(wf, roots, diagnosis)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    _write_atomic(path, wf)
    print(json.dumps({"reset": sorted(closure), "superseded": count, "diagnosis": diagnosis}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
