#!/usr/bin/env python3
"""Append one node transition to .allforai/bootstrap/workflow.json and print a receipt.

`/run` records how each node attempt ended. On Claude and Pi that record used to be
written by a model editing workflow.json by hand; a cheap model that wrote it wrong left
nothing to catch it. This helper is the only writer the run relays to, and its receipt
is what the run checks.

    printf '%s' '<request json>' | python3 .allforai/bootstrap/scripts/record_transition.py <project_root>

Request: {"node_id", "status": "completed"|"failed", "artifacts_created": [...],
          "started_at"?: str, "verification"?: {...}, "error"?: str (required when failed),
          "assumed_decisions"?: [...], "clear_corrections"?: bool}
Receipt (exit 0): {"status": "recorded", "node_id", "transition_index", "replayed"}
Refusal (exit 1): {"status": "refused", "node_id", "reason"}

A request identical to the node's latest transition (every field but completed_at) is a
replay: a relay that ran the command but lost its answer may run it again, and that must
not leave a second entry behind.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import tempfile

BOOTSTRAP = Path('.allforai/bootstrap')
STATUSES = ('completed', 'failed')
ENTRY_FIELDS = ('status', 'started_at', 'artifacts_created', 'verification', 'error')


class Refused(Exception):
    pass


def write_json(target: Path, value) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', dir=target.parent, delete=False) as stream:
        stream.write(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
        stream.flush()
        os.fsync(stream.fileno())
    Path(stream.name).replace(target)


def read_request(text: str) -> dict:
    try:
        request = json.loads(text)
    except json.JSONDecodeError as error:
        raise Refused(f'request is not JSON: {error}')
    if not isinstance(request, dict):
        raise Refused('request is not a JSON object')
    if not isinstance(request.get('node_id'), str) or not request['node_id']:
        raise Refused('node_id must be a non-empty string')
    if request.get('status') not in STATUSES:
        raise Refused(f'status must be one of {list(STATUSES)}')
    artifacts = request.get('artifacts_created', [])
    if not isinstance(artifacts, list) or not all(isinstance(a, str) for a in artifacts):
        raise Refused('artifacts_created must be a list of paths')
    if request['status'] == 'failed' and not request.get('error'):
        raise Refused('a failed transition needs a one-line error')
    if not isinstance(request.get('assumed_decisions', []), list):
        raise Refused('assumed_decisions must be a list')
    return request


def same_node(entry: dict, node_id: str) -> bool:
    return entry.get('node_id', entry.get('node')) == node_id


def record(root: Path, request: dict) -> dict:
    workflow_path = root / BOOTSTRAP / 'workflow.json'
    try:
        workflow = json.loads(workflow_path.read_text())
    except FileNotFoundError:
        raise Refused(f'{workflow_path} does not exist')
    except (OSError, json.JSONDecodeError) as error:
        raise Refused(f'{workflow_path} is unreadable: {error}')
    if not isinstance(workflow, dict) or not isinstance(workflow.get('transition_log', []), list):
        raise Refused('workflow.json has no transition_log list')

    decisions = request.get('assumed_decisions') or []
    decisions_path = root / BOOTSTRAP / 'assumed-decisions.json'
    existing = []
    if decisions and decisions_path.exists():
        try:
            existing = json.loads(decisions_path.read_text())
        except (OSError, json.JSONDecodeError) as error:
            raise Refused(f'{decisions_path} is unreadable: {error}')
        if not isinstance(existing, (list, dict)):
            raise Refused(f'{decisions_path} is neither a list nor an object')

    # Decisions first, and only the ones not already there: a retry after a write that
    # died halfway completes it instead of losing them or recording them twice.
    if decisions:
        target = existing.setdefault('decisions', []) if isinstance(existing, dict) else existing
        new = [d for d in decisions if d not in target]
        if new:
            target.extend(new)
            write_json(decisions_path, existing)

    node_id = request['node_id']
    entry = {'node_id': node_id, 'status': request['status'],
             'artifacts_created': request.get('artifacts_created', [])}
    for field in ('started_at', 'verification', 'error'):
        if request.get(field) is not None:
            entry[field] = request[field]

    log = workflow.setdefault('transition_log', [])
    latest = next(((i, e) for i, e in reversed(list(enumerate(log)))
                   if isinstance(e, dict) and same_node(e, node_id)), None)
    if latest and all(latest[1].get(f) == entry.get(f) for f in ENTRY_FIELDS) \
            and latest[1].get('node_id') == node_id:
        index, replayed = latest[0], True
    else:
        entry['completed_at'] = datetime.now(timezone.utc).isoformat(timespec='seconds')
        log.append(entry)
        write_json(workflow_path, workflow)
        index, replayed = len(log) - 1, False

    if request.get('clear_corrections'):
        (root / BOOTSTRAP / 'diagnosis-corrections' / f'{node_id}.json').unlink(missing_ok=True)

    return {'status': 'recorded', 'node_id': node_id, 'transition_index': index,
            'replayed': replayed}


def main(argv: list[str]) -> int:
    root = Path(argv[1] if len(argv) > 1 else '.').resolve()
    node_id = None
    try:
        request = read_request(sys.stdin.read())
        node_id = request['node_id']
        receipt = record(root, request)
    except Refused as refusal:
        print(json.dumps({'status': 'refused', 'node_id': node_id, 'reason': str(refusal)}))
        return 1
    print(json.dumps(receipt))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
