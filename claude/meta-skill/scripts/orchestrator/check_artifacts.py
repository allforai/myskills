#!/usr/bin/env python3
"""Check exit_artifacts for workflow nodes. Simplified from check_requires.py.

Usage:
  python check_artifacts.py <workflow.json> [--node <id>] [--json]

Without --node: checks all nodes, prints summary.
With --node: checks one node's exit_artifacts.
"""

import argparse
import json
import os
import sys


def check_node_artifacts(node: dict) -> dict:
    """Check if a node's exit_artifacts all exist."""
    node_id = node.get("id", "?")
    artifacts = node.get("exit_artifacts", [])
    results = []
    for path in artifacts:
        results.append({"path": path, "exists": os.path.exists(path)})
    return {
        "node": node_id,
        "goal": node.get("goal", ""),
        "all_exist": all(r["exists"] for r in results),
        "artifacts": results,
    }


def main():
    parser = argparse.ArgumentParser(description="Check workflow node exit artifacts")
    parser.add_argument("workflow_path", help="Path to workflow.json")
    parser.add_argument("--node", dest="node_id", help="Check specific node only")
    parser.add_argument("--json", dest="output_json", action="store_true")
    args = parser.parse_args()

    with open(args.workflow_path) as f:
        wf = json.load(f)

    nodes = wf.get("nodes", [])

    if args.node_id:
        node = next((n for n in nodes if n.get("id") == args.node_id), None)
        if not node:
            print(f"Node '{args.node_id}' not found", file=sys.stderr)
            sys.exit(2)  # 2 = actual error (node not found), not "pending"
        result = check_node_artifacts(node)
        if args.output_json:
            print(json.dumps(result, indent=2))
            sys.exit(0)  # --json always exits 0; status is in the JSON
        else:
            status = "DONE" if result["all_exist"] else "PENDING"
            print(f"[{status}] {result['node']}: {result['goal']}")
            for a in result["artifacts"]:
                mark = "\u2713" if a["exists"] else "\u2717"
                print(f"  {mark} {a['path']}")
            sys.exit(0 if result["all_exist"] else 1)
    else:
        results = [check_node_artifacts(n) for n in nodes]
        done = sum(1 for r in results if r["all_exist"])
        total = len(results)
        if args.output_json:
            print(json.dumps({"done": done, "total": total, "nodes": results}, indent=2))
            sys.exit(0)  # --json always exits 0; status is in the JSON
        else:
            print(f"Progress: {done}/{total} nodes complete\n")
            for r in results:
                status = "DONE" if r["all_exist"] else "PENDING"
                print(f"  [{status}] {r['node']}: {r['goal']}")
            sys.exit(0 if done == total else 1)


if __name__ == "__main__":
    main()
