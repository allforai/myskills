#!/usr/bin/env python3
"""Simulate a Grillstorm DAG without dispatching agents or mutating Git."""
import argparse
import json
from pathlib import Path


def descendants(effective_deps):
    children = {task_id: set() for task_id in effective_deps}
    for task_id, deps in effective_deps.items():
        for dep in deps:
            children.setdefault(dep, set()).add(task_id)

    result = {}
    for task_id in effective_deps:
        seen = set()
        stack = list(children.get(task_id, ()))
        while stack:
            child = stack.pop()
            if child in seen:
                continue
            seen.add(child)
            stack.extend(children.get(child, ()))
        result[task_id] = sorted(seen)
    return result


def simulate(tasks, orchestration):
    task_ids = [task["id"] for task in tasks]
    known = set(task_ids)
    deps = orchestration.get("effective_deps") or {
        task["id"]: list(task.get("depends_on") or []) for task in tasks
    }
    unknown = sorted(
        {dep for values in deps.values() for dep in values if dep not in known}
        | (set(deps) - known)
    )
    if orchestration.get("ok") is False or unknown:
        return {
            "ok": False,
            "errors": list(orchestration.get("errors") or [])
            + ([f"unknown task/dependency IDs: {unknown}"] if unknown else []),
        }

    done = set()
    waves = []
    while len(done) < len(task_ids):
        ready = [
            task_id for task_id in task_ids
            if task_id not in done and all(dep in done for dep in deps.get(task_id, []))
        ]
        if not ready:
            break
        waves.append(ready)
        done.update(ready)

    unreachable = [task_id for task_id in task_ids if task_id not in done]
    return {
        "ok": not unreachable,
        "initial_ready": waves[0] if waves else [],
        "dependency_waves_informational": waves,
        "max_ready_width": max((len(wave) for wave in waves), default=0),
        "path_merge_groups": list(orchestration.get("isolate_groups") or []),
        "resource_mutexes": dict(orchestration.get("resource_groups") or {}),
        "derived_edges": list(orchestration.get("derived_edges") or []),
        "failure_blast_radius": descendants(deps),
        "unreachable": unreachable,
        "warnings": list(orchestration.get("warnings") or []),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("orchestration")
    parser.add_argument("tasks")
    parser.add_argument("--output")
    args = parser.parse_args(argv)

    orchestration = json.loads(Path(args.orchestration).read_text(encoding="utf-8"))
    payload = json.loads(Path(args.tasks).read_text(encoding="utf-8"))
    tasks = payload.get("tasks", []) if isinstance(payload, dict) else payload
    result = simulate(tasks, orchestration)
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
