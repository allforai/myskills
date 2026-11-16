"""Fix C2: when diagnosis resets a root-cause node, every node transitively
downstream (via hard_blocked_by) must also reset, else it runs on stale upstream.

Usage:
  compute_reset_closure.py <workflow.json> <root_id...>
      print the closure as a JSON list; changes nothing.
  compute_reset_closure.py <workflow.json> --apply --diagnosis <ref> <root_id...>
      reset the closure: every `completed` transition of a node in it becomes
      `superseded`, naming the diagnosis that reset it. Nothing is deleted, so the
      audit trail stays, and no reader of `completed` needs to know about resets.
  compute_reset_closure.py <workflow.json> --route-defects
      send each defect a node reported in another node's output back to that node: its
      correction is written, the nodes the change reaches are reset (the owner, the nodes
      that recorded reading the file, and what depends on those), and the defect recorded
      as routed. Prints
      {"routed": [...], "kept": [...]}; an empty `routed` changed nothing.
"""
import json
import os
import re
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


def apply_reset(workflow, root_ids, diagnosis_ref, now=None, members=None):
    """Supersede the closure's completed transitions in place; return (closure, count).

    `members` names the nodes to reset when the caller knows which ones the change reaches;
    without it the closure is every node downstream of the roots.
    """
    known = {n.get("node_id") for n in workflow.get("nodes", [])}
    unknown = sorted(set(root_ids) - known)
    if unknown:
        raise ValueError(f"unknown root node(s): {', '.join(unknown)}")
    closure = sorted(members) if members is not None else reset_closure(workflow.get("nodes", []), root_ids)
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


# A node that notices a defect in a file another node owns finishes and reports it as a
# warning of this shape (the node prompt's own-outputs rule).
DEFECT = re.compile(r"^defect in ([^:\s]+):\s*(.+)$", re.S)
# How many times one node is sent back for reported defects. The reporter reruns after the
# owner does and may word the same defect differently, so the routed text alone cannot
# bound the loop; this does. Past it a defect stays a warning.
ROUTE_LIMIT = 2


def route_defects(workflow, warnings, routed, corrections_of, now=None):
    """Decide which reported defects go back to their owner. Pure: returns what to write.

    A defect is routed once, to a node the plan has, while that node is under ROUTE_LIMIT.
    Each routed owner gets a correction, binding on its next run like a diagnosis
    correction; which nodes are reset with it is the caller's (`reached_by`). Returns (new routed entries, kept warnings,
    {owner: corrections file content}, diagnosis ref).
    """
    at = now or datetime.now(timezone.utc).isoformat()
    ref = "reported-defects:" + at
    known = {n.get("node_id") for n in workflow.get("nodes", [])}
    seen = {(r.get("owner"), r.get("defect")) for r in routed}
    rounds = {}                     # owner -> the earlier routings that sent it back
    for r in routed:
        rounds.setdefault(r.get("owner"), set()).add(r.get("diagnosis"))
    new, kept, files = [], [], {}
    for warning in warnings:
        match = DEFECT.match(warning) if isinstance(warning, str) else None
        if not match:
            continue
        owner, defect = match.group(1), match.group(2).strip()
        if (owner, defect) in seen:
            continue
        seen.add((owner, defect))
        if owner not in known:
            kept.append({"warning": warning, "reason": "no node of the plan is named " + owner})
        elif len(rounds.get(owner, ())) >= ROUTE_LIMIT:
            kept.append({"warning": warning,
                         "reason": f"{owner} was already sent back {ROUTE_LIMIT} times for reported defects"})
        else:
            new.append({"owner": owner, "defect": defect, "diagnosis": ref})
            previous = corrections_of(owner)
            content = files.setdefault(owner, previous if isinstance(previous, dict) and isinstance(
                previous.get("corrections"), list) else {"node_id": owner, "corrections": []})
            content["diagnosis"] = ref
            content["corrections"].append({
                "action": "Fix this defect in your own output, changing no other file you produce "
                          "unless the fix cannot be made without it: " + defect,
                "root_cause": "another node reported a defect in a file this node produces",
                "gaps": [defect]})
    return new, kept, files, ref


def defect_file(defect):
    """The file a reported defect names: the text before the dash in `<file> — <what is wrong>`."""
    head = re.split(r"\s+[—–-]\s+", defect, maxsplit=1)
    path = head[0].strip().strip("`") if len(head) == 2 else ""
    return path if path and not re.search(r"\s", path) else None


def reached_by(workflow, consumed, owner, path):
    """The nodes a change to `path` reaches, or None when that cannot be told.

    Freshness stales a node when a file it consumed changes, and then every node that
    depends on a stale one — through `hard_blocked_by` or by consuming its output. That is
    the set that has to run again and the only one: a node that waits for the owner
    without reading the file keeps valid evidence. `consumed` is what each node recorded
    reading ({node_id: paths}); None means no record exists, and the caller falls back to
    everything downstream of the owner.
    """
    if consumed is None or path is None:
        return None
    nodes = workflow.get("nodes", [])
    producer = {(item.get("path") if isinstance(item, dict) else item): n.get("node_id")
                for n in nodes for item in [*(n.get("exit_artifacts") or []), *(n.get("required_documents") or [])]}
    depends = {n.get("node_id"): set(n.get("hard_blocked_by") or [])
               | {producer[p] for p in consumed.get(n.get("node_id"), ()) if p in producer}
               for n in nodes}
    reached = {node_id for node_id, paths in consumed.items() if path in paths and node_id != owner}
    changed = True
    while changed:
        changed = False
        for node_id, deps in depends.items():
            if node_id not in reached and node_id != owner and deps & reached:
                reached.add(node_id)
                changed = True
    return reached | {owner}


def recorded_consumption(base):
    """{node_id: paths it recorded reading} from the freshness state, or None without one."""
    state = _read(os.path.join(base, "evidence-freshness.json"), None)
    if not isinstance(state, dict):
        return None
    consumed = {}
    for bucket in ("nodes", "contracts"):
        records = state.get(bucket)
        for node_id, record in records.items() if isinstance(records, dict) else []:
            inputs = record.get("inputs") if isinstance(record, dict) else None
            files = inputs.get("files") if isinstance(inputs, dict) else None
            consumed.setdefault(node_id, set()).update(files if isinstance(files, dict) else ())
            consumed[node_id].update(p for p in record.get("extra") or [] if isinstance(p, str))
    reads = _read(os.path.join(base, "observed-input-dependencies.json"), {})
    for node_id, paths in reads.items() if isinstance(reads, dict) else []:
        consumed.setdefault(node_id, set()).update(p for p in paths or [] if isinstance(p, str))
    return consumed


def _read(path, default):
    try:
        with open(path) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def apply_routed_defects(workflow_path):
    """`--route-defects`: read the run's warnings beside the workflow, write what routing decides."""
    base = os.path.dirname(os.path.abspath(workflow_path))
    with open(workflow_path) as fh:
        workflow = json.load(fh)
    warnings = _read(os.path.join(base, "run-warnings.json"), {})
    warnings = warnings.get("warnings") if isinstance(warnings, dict) else None
    ledger_path = os.path.join(base, "routed-defects.json")
    routed = _read(ledger_path, [])
    routed = [r for r in routed if isinstance(r, dict)] if isinstance(routed, list) else []
    directory = os.path.join(base, "diagnosis-corrections")
    new, kept, files, ref = route_defects(
        workflow, warnings if isinstance(warnings, list) else [], routed,
        lambda owner: _read(os.path.join(directory, owner + ".json"), None))
    reset = []
    if new:
        os.makedirs(directory, exist_ok=True)
        for owner, content in files.items():
            _write_atomic(os.path.join(directory, owner + ".json"), content)
        # Only what the change reaches runs again. Where that cannot be told for a defect —
        # no freshness record, or no file named — everything downstream of its owner does.
        consumed = recorded_consumption(base)
        members = set()
        for entry in new:
            reached = reached_by(workflow, consumed, entry["owner"], defect_file(entry["defect"]))
            members |= reached if reached is not None else set(
                reset_closure(workflow.get("nodes", []), [entry["owner"]]))
        reset, _ = apply_reset(workflow, sorted(files), ref, members=members)
        _write_atomic(workflow_path, workflow)
        _write_atomic(ledger_path, routed + new)
    return {"routed": [{"owner": r["owner"], "defect": r["defect"]} for r in new],
            "kept": kept, "reset": sorted(reset), "diagnosis": ref if new else None}


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
    if rest == ["--route-defects"]:
        print(json.dumps(apply_routed_defects(path), ensure_ascii=False))
        return 0
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
