#!/usr/bin/env python3
"""Freeze Grillstorm task path and acceptance contracts before parallel dispatch."""
import hashlib
import json
from pathlib import PurePosixPath
import sys


CONTROL_PATHS = [
    "docs/grillstorm/**",
]


def build_contract(task):
    task_id = task.get("id")
    paths = task.get("touched_paths")
    command = task.get("acceptance_cmd")
    if not isinstance(task_id, str) or not task_id.strip():
        raise ValueError("<missing id>: id is required")
    if not isinstance(paths, list) or not paths:
        raise ValueError(f"{task.get('id', '<missing id>')}: touched_paths is required")
    if not isinstance(command, str) or not command.strip():
        raise ValueError(f"{task.get('id', '<missing id>')}: acceptance_cmd is required")

    rules = []
    for path in paths:
        parsed = PurePosixPath(path) if isinstance(path, str) else None
        if (
            parsed is None
            or not path.strip()
            or parsed.is_absolute()
            or "\\" in path
            or "\0" in path
            or any(part in ("", ".", "..") for part in parsed.parts)
        ):
            raise ValueError(f"{task.get('id', '<missing id>')}: invalid touched path")
        kind = "glob" if any(char in path for char in "*?[") else "literal"
        rules.append({
            "kind": kind,
            "pattern": path,
            "operations": ["create", "modify", "delete", "rename"],
        })

    return {
        "schema_version": 1,
        "task_id": task_id,
        "path_rules": rules,
        "required_outputs": list(task.get("required_outputs") or []),
        "forbidden_paths": CONTROL_PATHS,
        "max_files_changed": int(task.get("max_files_changed") or max(len(paths) * 2, 4)),
        "acceptance_cmd_sha256": hashlib.sha256(command.encode()).hexdigest(),
        "interface_assertions": list(task.get("interface_assertions") or []),
    }


def freeze_tasks(tasks):
    frozen = []
    for task in tasks:
        item = dict(task)
        expected = build_contract(item)
        existing = item.get("artifact_contract")
        if existing is not None and existing != expected:
            raise ValueError(f"{item.get('id', '<missing id>')}: stale artifact_contract")
        item["artifact_contract"] = expected
        frozen.append(item)
    return frozen


def main(argv):
    source = argv[1] if len(argv) > 1 else "-"
    target = argv[2] if len(argv) > 2 else "-"
    if source == "-":
        raw = sys.stdin.read()
    else:
        with open(source, encoding="utf-8") as handle:
            raw = handle.read()
    payload = json.loads(raw)
    wrapped = isinstance(payload, dict)
    tasks = payload.get("tasks", []) if wrapped else payload
    try:
        result = freeze_tasks(tasks)
    except (TypeError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 1
    output = json.dumps({"tasks": result} if wrapped else result, indent=2) + "\n"
    if target == "-":
        sys.stdout.write(output)
    else:
        with open(target, "w", encoding="utf-8") as handle:
            handle.write(output)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
