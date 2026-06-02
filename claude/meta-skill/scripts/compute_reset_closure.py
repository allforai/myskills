"""Fix C2: when diagnosis resets a root-cause node, every node transitively
downstream (via hard_blocked_by) must also reset, else it runs on stale upstream."""
import json
import sys


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


def main(argv):
    # argv: workflow.json path, then one or more root node_ids
    wf = json.load(open(argv[1]))
    roots = argv[2:]
    print(json.dumps(reset_closure(wf.get("nodes", []), roots)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
