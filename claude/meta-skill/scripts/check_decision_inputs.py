"""Bootstrap-time invariant: every node's decision_inputs artifact must exist
before /run is allowed to start. A missing artifact is a planning bug (Phase A
should have produced it)."""
import json
import os
import sys


def check_decision_inputs(workflow, base_dir="."):
    """Return list of {node_id, missing} for nodes whose decision_inputs are absent."""
    missing = []
    for node in workflow.get("nodes", []):
        for path in node.get("decision_inputs", []) or []:
            resolved = path if os.path.isabs(path) else os.path.join(base_dir, path)
            if not os.path.exists(resolved):
                missing.append({"node_id": node.get("node_id"), "missing": path})
    return missing


def find_orphan_decisions(workflow, decision_paths):
    """Fix C4 (reverse direction): every gathered decision-*.json must be referenced by
    >=1 node's decision_inputs. Return decision paths that no node consumes."""
    referenced = set()
    for node in workflow.get("nodes", []):
        for path in node.get("decision_inputs", []) or []:
            referenced.add(os.path.normpath(path))
    return [p for p in decision_paths if os.path.normpath(p) not in referenced]


def main(argv):
    import glob
    base = argv[1] if len(argv) > 1 else "."
    wf_path = os.path.join(base, ".allforai/bootstrap/workflow.json")
    with open(wf_path) as f:
        workflow = json.load(f)
    missing = check_decision_inputs(workflow, base_dir=base)
    # Orphan direction (fix C4): every gathered decision-*.json must be referenced by a node.
    gathered = [os.path.relpath(p, base) for p in
                glob.glob(os.path.join(base, ".allforai/**/decision-*.json"), recursive=True)]
    orphans = find_orphan_decisions(workflow, gathered)
    if missing or orphans:
        print("BLOCKED: decision wiring incomplete:")
        for m in missing:
            print(f"  - missing: {m['node_id']} -> {m['missing']}")
        for o in orphans:
            print(f"  - orphan (unwired): {o}")
        return 1
    print("OK: decision_inputs present and every decision is wired to a consumer")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
