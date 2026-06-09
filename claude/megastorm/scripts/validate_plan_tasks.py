# claude/megastorm/scripts/validate_plan_tasks.py
#!/usr/bin/env python3
"""§4.3 gate: every plan task MUST carry a non-empty touched_paths list and a
non-blank acceptance_cmd. touched_paths feeds the §4.5 concurrency DAG;
acceptance_cmd feeds the §4.6 anti-fake-completion supervisor's objective rerun.
Plans failing this are bounced back to the plan agent."""
import json
import sys


def validate_tasks(tasks):
    """Return {ok, errors}. Each task needs id, non-empty touched_paths, non-blank acceptance_cmd."""
    errors = []
    for i, t in enumerate(tasks):
        tid = t.get("id")
        label = tid if tid else f"<task #{i} missing id>"
        if not tid:
            errors.append(f"{label}: missing 'id'")
        paths = t.get("touched_paths")
        if not isinstance(paths, list) or len(paths) == 0:
            errors.append(f"{label}: missing or empty 'touched_paths'")
        cmd = t.get("acceptance_cmd")
        if not isinstance(cmd, str) or not cmd.strip():
            errors.append(f"{label}: missing or blank 'acceptance_cmd'")
    return {"ok": len(errors) == 0, "errors": errors}


def main(argv):
    path = argv[1] if len(argv) > 1 else "-"
    raw = sys.stdin.read() if path == "-" else open(path).read()
    tasks = json.loads(raw)
    if isinstance(tasks, dict):
        tasks = tasks.get("tasks", [])
    result = validate_tasks(tasks)
    if result["ok"]:
        print(f"OK: {len(tasks)} tasks each carry touched_paths + acceptance_cmd")
        return 0
    print("BLOCKED: plan tasks missing required fields (return to plan agent):")
    for e in result["errors"]:
        print(f"  - {e}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
