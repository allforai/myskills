#!/usr/bin/env python3
"""Content-bound observations and publication at bootstrap/resume boundaries."""
from __future__ import annotations

import hashlib
from contextlib import contextmanager
import json
import os
import subprocess
from pathlib import Path
import sys
import tempfile
import time
from typing import Any

WORKFLOW = '.allforai/bootstrap/workflow.json'
STATE = '.allforai/bootstrap/evidence-freshness.json'
OBSERVATIONS = '.allforai/bootstrap/input-observations'
READS = '.allforai/bootstrap/observed-input-dependencies.json'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def read_json(root, path, default=None):
    target = root / path
    return json.loads(target.read_text()) if target.exists() else default


def write_json(root, path, value):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(value, sort_keys=True, indent=2) + '\n'
    if not target.exists() or target.read_text() != content:
        with tempfile.NamedTemporaryFile(mode='w', dir=target.parent, delete=False) as stream:
            stream.write(content)
            temporary = Path(stream.name)
        try:
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)


@contextmanager
def publication_lock(root):
    lock = root / '.allforai/bootstrap/freshness-publication.lock'
    lock.parent.mkdir(parents=True, exist_ok=True)
    for _ in range(300):
        try:
            lock.mkdir()
            break
        except FileExistsError:
            time.sleep(.01)
    else:
        raise ValueError('Freshness publication is locked; retry or coordinate an abandoned writer')
    try:
        yield
    finally:
        lock.rmdir()


def fingerprint(root, path):
    target = (root / path).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ValueError('Input must be inside project: ' + path)
    return hashlib.sha256(target.read_bytes()).hexdigest() if target.is_file() else None


def expand_paths(root, paths):
    if not isinstance(paths, list) or not all(isinstance(p, str) and p for p in paths):
        raise ValueError('Input dependencies must be a list of project paths or globs')
    expanded: set[str] = set()
    for path in paths:
        if Path(path).is_absolute() or '..' in Path(path).parts:
            raise ValueError('Input must be a relative project path: ' + path)
        if any(c in path for c in '*?['):
            matches = [p for p in root.glob(path) if p.is_file()]
            expanded.update(p.relative_to(root).as_posix() for p in matches)
        elif (root / path).is_dir():
            expanded.update(p.relative_to(root).as_posix() for p in (root / path).rglob('*') if p.is_file())
        else:
            expanded.add(path)
    return expanded


def observed_reads(root):
    """The dynamic-read register: {node_id: [project paths]} recorded by ``read``.

    A malformed register is refused, never treated as empty: dropping a recorded
    read would let evidence claim provenance it no longer tracks. The file is
    left in place for repair.
    """
    prefix = 'Malformed observed-input dependencies (' + READS + '): '
    try:
        reads = read_json(root, READS, {})
    except ValueError as exc:
        raise ValueError(prefix + 'not valid JSON; restore recorded dependencies before retrying: ' + str(exc)) from None
    if not isinstance(reads, dict):
        raise ValueError(prefix + 'top level must be an object keyed by node_id; restore recorded dependencies before retrying')
    for node_id, paths in reads.items():
        if not isinstance(node_id, str) or not node_id:
            raise ValueError(prefix + 'node ids must be non-empty strings; restore recorded dependencies before retrying')
        if not isinstance(paths, list) or not all(isinstance(p, str) and p for p in paths):
            raise ValueError(prefix + 'entry for ' + node_id + ' must be a list of project paths; '
                             'restore recorded dependencies before retrying')
        for path in paths:
            if Path(path).is_absolute() or '..' in Path(path).parts:
                raise ValueError(prefix + 'entry for ' + node_id + ' must use relative project paths, not ' + path
                                 + '; restore recorded dependencies before retrying')
    return reads


def intent_baseline(root):
    profile = read_json(root, '.allforai/bootstrap/bootstrap-profile.json', {})
    if profile.get('intent_session_path') == '.allforai/bootstrap/local-requirements.json':
        return profile.get('intent_scope', {})
    return read_json(root, '.allforai/product-concept/concept-baseline.json', {}).get('intent_baseline', {})


def snapshot(root, node, extra=(), seen=()):
    if node['node_id'] in seen:
        raise ValueError('Cyclic input dependency; impact is uncertain')
    extra = set(extra) | set(observed_reads(root).get(node['node_id'], []))
    workflow = read_json(root, WORKFLOW, {})
    source_files = expand_paths(root, node.get('source_inputs', []))
    product_files = inventory(root, workflow)
    source_files = {p for p in source_files if p in product_files or not (root / p).exists()}
    paths = source_files | expand_paths(root, node.get('input_dependencies', [])) | extra
    refs = node.get('requirement_refs', [])
    ref_paths = {ref['path'] for ref in refs}
    # A shared concept document can carry unrelated decisions. Bind selected items.
    paths.update(p for p in node.get('decision_inputs', []) if isinstance(p, str) and p not in ref_paths
                 and p != '.allforai/product-concept/concept-baseline.json')
    inputs = {path: fingerprint(root, path) for path in sorted(paths)}
    requirements = {}
    for ref in refs:
        data = read_json(root, ref['path'], {})
        items = [item for item in data.get('requirements', []) if item.get('id') == ref['id']]
        requirements[ref['path'] + '#' + ref['id']] = digest(items)
    baseline = intent_baseline(root)
    selected = {ref['id'] for ref in refs}
    baseline_scope = {'requirement_refs': [ref for ref in baseline.get('requirement_refs', []) if ref['id'] in selected],
                      'intents': [item for item in baseline.get('intents', []) if item['id'] in selected],
                      'excluded': {k: v for k, v in baseline.get('excluded', {}).items() if k in selected}}
    by_id = {n['node_id']: n for n in workflow.get('nodes', [])}
    state = read_json(root, STATE, {'nodes': {}})
    upstream = {}
    for dep in dependencies(root, node, workflow):
        if dep not in by_id:
            raise ValueError('Missing dependency ' + dep + '; impact is uncertain')
        upstream[dep] = snapshot(root, by_id[dep], state['nodes'].get(dep, {}).get('extra', []),
                                 (*seen, node['node_id']))
    return {'files': inputs, 'requirements': requirements, 'contract': digest(node),
            'baseline_scope': baseline_scope, 'upstream': upstream}


def dependencies(root, node, workflow):
    producers = {item['path'] if isinstance(item, dict) else item: n['node_id']
                 for n in workflow.get('nodes', [])
                 for item in [*n.get('exit_artifacts', []), *n.get('required_documents', [])]}
    state = read_json(root, STATE, {'nodes': {}})
    consumed = expand_paths(root, node.get('input_dependencies', []))
    consumed.update(observed_reads(root).get(node['node_id'], []))
    for bucket in ('nodes', 'contracts'):
        consumed.update(state.get(bucket, {}).get(node['node_id'], {}).get('extra', []))
    return sorted(set(node.get('hard_blocked_by', [])) |
                  {producers[p] for p in consumed if p in producers and producers[p] != node['node_id']})


def outputs(root, node, kind='evidence'):
    """Outputs a publication binds: the Node-spec for a contract; the required
    fact documents, Node-spec and exit artifacts for delivered evidence."""
    paths = []
    spec = '.allforai/bootstrap/node-specs/' + node['node_id'] + '.md'
    if kind == 'evidence':
        paths.extend(node.get('required_documents', []))
    if (root / spec).exists() or kind == 'contract':
        paths.append(spec)
    if kind == 'evidence':
        paths.extend(item['path'] if isinstance(item, dict) else item for item in node.get('exit_artifacts', []))
    return {p: fingerprint(root, p) for p in paths}


def input_diff(recorded, current):
    """Explicit differences between a recorded input snapshot and the current one."""
    diff: dict[str, Any] = {}
    files = {}
    for path in sorted(set(recorded.get('files', {})) | set(current.get('files', {}))):
        if recorded.get('files', {}).get(path) != current.get('files', {}).get(path):
            files[path] = ('added' if path not in recorded.get('files', {}) else
                           'removed' if path not in current.get('files', {}) else 'changed')
    if files:
        diff['files'] = files
    requirements = sorted(key for key in set(recorded.get('requirements', {})) | set(current.get('requirements', {}))
                          if recorded.get('requirements', {}).get(key) != current.get('requirements', {}).get(key))
    if requirements:
        diff['requirements'] = requirements
    if recorded.get('baseline_scope') != current.get('baseline_scope'):
        diff['baseline_scope'] = 'changed'
    if recorded.get('contract') != current.get('contract'):
        diff['contract'] = 'changed'
    upstream = sorted(dep for dep in set(recorded.get('upstream', {})) | set(current.get('upstream', {}))
                      if recorded.get('upstream', {}).get(dep) != current.get('upstream', {}).get(dep))
    if upstream:
        diff['upstream'] = upstream
    return diff


def output_diff(recorded, current):
    """Missing or changed published outputs, keyed by path."""
    diff = {}
    for path in sorted(set(recorded) | set(current)):
        if current.get(path) is None:
            diff[path] = 'missing'
        elif recorded.get(path) != current.get(path):
            diff[path] = 'changed' if path in recorded else 'added'
    return diff


def missing_outputs(current):
    return {path: 'missing' for path, value in current.items() if value is None}


def scope_blockers(root, workflow):
    """The shared scope contract's blockers, keyed by consuming node (None = global)."""
    try:
        from product_intent import validate_scope
    except ImportError:
        return {}
    grouped: dict[str | None, set[str]] = {}
    for blocker in validate_scope(root, workflow):
        grouped.setdefault(blocker.get('node_id'), set()).add(blocker.get('code'))
    return grouped


def repair_responsibility(root, node, diff, blockers=None):
    """Who repairs an inconsistency and which responsibility drifted.

    An unresolved or unreplanned product decision belongs to interactive
    bootstrap; stale producers repair before their consumers; everything else
    returns to the node that owns the delivery. A diff never authorizes a
    product choice, and a Run Policy never resolves one.
    """
    if blockers is None:
        blockers = scope_blockers(root, read_json(root, WORKFLOW, {}))
    codes = blockers.get(None, set()) | blockers.get(node['node_id'], set())
    if 'pending_requirement' in codes or 'pending_product_confirmation' in codes:
        return {'owner': 'interactive-bootstrap', 'responsibilities': ['product-decision']}
    if 'stale_requirement' in codes:
        return {'owner': 'interactive-bootstrap', 'responsibilities': ['replan']}
    own = {k: v for k, v in diff.items() if k != 'upstream'}
    if not own and diff.get('upstream'):
        return {'owner': diff['upstream'][0], 'responsibilities': ['upstream']}
    responsibilities = []
    spec = '.allforai/bootstrap/node-specs/' + node['node_id'] + '.md'
    documents = set(node.get('required_documents', []))
    changed_outputs = diff.get('outputs', {})
    if 'requirements' in diff or 'baseline_scope' in diff:
        responsibilities.append('requirement-sync')
    if 'contract' in diff or spec in changed_outputs:
        responsibilities.append('contract')
    if 'files' in diff:
        responsibilities.append('implementation')
    if any(path in documents for path in changed_outputs):
        responsibilities.append('documentation')
    if any(path not in documents and path != spec for path in changed_outputs) or diff.get('evidence') == 'unpublished':
        responsibilities.append('verification')
    return {'owner': node['node_id'], 'responsibilities': responsibilities}


def inventory(root, workflow):
    generated = {item['path'] if isinstance(item, dict) else item
                 for node in workflow.get('nodes', []) for item in node.get('exit_artifacts', [])}
    generated.update(workflow.get('generated_outputs', []))
    generated.update(p for node in workflow.get('nodes', []) for p in node.get('required_documents', []))
    result = {}
    for directory, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in {'.git', '.allforai', '.claude', '.codex',
                                                      '__pycache__', '.pytest_cache', 'node_modules', '.venv'})
        for name in sorted(files):
            path = (Path(directory) / name).relative_to(root).as_posix()
            if path not in generated and name != '.git':
                result[path] = fingerprint(root, path)
    return result


def evaluate(root):
    workflow = read_json(root, WORKFLOW, {})
    state = read_json(root, STATE, {'nodes': {}})
    result: dict[str, dict[str, Any]] = {}
    current = inventory(root, workflow)
    owned = {p for n in workflow.get('nodes', [])
             for field in ('source_inputs', 'input_dependencies')
             for p in expand_paths(root, n.get(field, []))}
    owned.update(p for record in state['nodes'].values() for p in record.get('extra', []))
    owned.update(p for record in state['nodes'].values() for p in record.get('inputs', {}).get('files', {}))
    owned.update(p for paths in observed_reads(root).values() for p in paths)
    uncertain_inputs = set()
    blockers = scope_blockers(root, workflow)
    for node in workflow.get('nodes', []):
        evidence = state['nodes'].get(node['node_id'])
        contract = state.get('contracts', {}).get(node['node_id'])
        record = contract or evidence
        if record is None and 'source_inputs' not in node:
            result[node['node_id']] = {'status': 'undeclared', 'readiness_status': 'undeclared',
                                      'reason': 'No source declaration or observation; no provenance claimed'}
            continue
        valid = record and record['inputs'] == snapshot(root, node, record.get('extra', []))
        valid = valid and record.get('outputs') == outputs(root, node, record.get('kind', 'evidence'))
        evidence_valid = (valid and evidence and evidence['inputs'] == snapshot(root, node, evidence.get('extra', []))
                          and evidence['outputs'] == outputs(root, node))
        diff: dict[str, Any]
        if record is None:
            diff = {'contract': 'unpublished'}
        else:
            bound = evidence or record
            diff = input_diff(bound['inputs'], snapshot(root, node, bound.get('extra', [])))
            changed = output_diff(bound.get('outputs', {}), outputs(root, node, bound.get('kind', 'evidence')))
            if evidence is None:
                diff['evidence'] = 'unpublished'
                changed.update(missing_outputs(outputs(root, node)))
            if changed:
                diff['outputs'] = changed
        result[node['node_id']] = {'status': 'valid' if evidence_valid else 'stale',
                                  'readiness_status': 'valid' if valid else 'stale', 'diff': diff}
        if not evidence_valid:
            result[node['node_id']]['repair'] = repair_responsibility(root, node, diff, blockers)
        if record:
            previous = record.get('source_snapshot', {})
            unknown = {p for p in set(previous) | set(current) if previous.get(p) != current.get(p)} - owned
            uncertain_inputs.update(unknown)
            if unknown and valid:
                result[node['node_id']] = {'status': 'uncertain', 'readiness_status': 'uncertain',
                                          'reason': 'Unmapped product input changed'}
    for _ in workflow.get('nodes', []):
        for node in workflow['nodes']:
            stale_upstream = [dep for dep in dependencies(root, node, workflow)
                              if result.get(dep, {}).get('status') != 'valid']
            if stale_upstream:
                entry = result[node['node_id']]
                entry['status'] = 'stale'
                entry['reason'] = 'Upstream evidence is stale or missing'
                if entry.get('status') != 'undeclared':
                    stale_diff = entry.setdefault('diff', {})
                    stale_diff['upstream'] = sorted(set(stale_diff.get('upstream', [])) | set(stale_upstream))
                    entry['repair'] = repair_responsibility(root, node, stale_diff, blockers)
            if any(result.get(dep, {}).get('readiness_status') != 'valid' for dep in dependencies(root, node, workflow)):
                result[node['node_id']]['readiness_status'] = 'stale'
    return {'nodes': result, 'uncertain_inputs': sorted(uncertain_inputs)}


def session(root, request):
    operation = request['operation']
    if operation == 'check':
        return evaluate(root)
    workflow = read_json(root, WORKFLOW, {})
    if operation == 'observe':
        node = next(n for n in workflow['nodes'] if n['node_id'] == request['node_id'])
        if 'source_inputs' not in node:
            raise ValueError('Missing source_inputs: impact is uncertain; declare relevant paths or explicit []')
        state = read_json(root, STATE, {'nodes': {}})
        extra = sorted(set(state['nodes'].get(node['node_id'], {}).get('extra', [])) |
                       set(state.get('contracts', {}).get(node['node_id'], {}).get('extra', [])) |
                       set(observed_reads(root).get(node['node_id'], [])))
        kind = request.get('kind', 'evidence')
        if kind not in {'contract', 'evidence'}:
            raise ValueError('Observation kind must be contract or evidence')
        observation = {'node_id': node['node_id'], 'inputs': snapshot(root, node, extra), 'extra': extra,
                       'source_snapshot': inventory(root, workflow), 'kind': kind,
                       'baseline_version': intent_baseline(root).get('version')}
        token = digest(observation)
        write_json(root, OBSERVATIONS + '/' + token + '.json', observation)
        return {'observation': token, **observation}
    if operation in {'read', 'publish'}:
        token = request['observation']
        if len(token) != 64 or any(c not in '0123456789abcdef' for c in token):
            raise ValueError('Invalid observation')
        observation = read_json(root, OBSERVATIONS + '/' + token + '.json')
        if digest(observation) != token:
            raise ValueError('Observation content does not match its identity')
        node = next(n for n in workflow['nodes'] if n['node_id'] == observation['node_id'])
        if (observation['inputs'] != snapshot(root, node, observation.get('extra', []))
                or observation['source_snapshot'] != inventory(root, workflow)):
            return {'status': 'stale', 'reason': 'Inputs changed after observation; reverify current inputs'}
        if operation == 'read':
            path = request['path']
            fingerprint(root, path)  # Validate project containment before reading.
            content = (root / path).read_bytes()
            observation['extra'] = sorted(set(observation.get('extra', [])) | {path})
            observation['inputs']['files'][path] = hashlib.sha256(content).hexdigest()
            with publication_lock(root):
                reads = observed_reads(root)
                reads[node['node_id']] = sorted(set(reads.get(node['node_id'], [])) | {path})
                write_json(root, READS, reads)
            expanded = snapshot(root, node, observation['extra'])
            prior = observation['inputs']
            if (any(expanded[key] != prior[key] for key in ('files', 'requirements', 'contract', 'baseline_scope'))
                    or any(expanded['upstream'].get(dep) != value for dep, value in prior['upstream'].items())
                    or observation['source_snapshot'] != inventory(root, workflow)):
                return {'status': 'stale', 'reason': 'Inputs changed while registering dependency; reobserve current inputs'}
            observation['inputs']['upstream'] = expanded['upstream']
            token = digest(observation)
            write_json(root, OBSERVATIONS + '/' + token + '.json', observation)
            return {'observation': token, 'content': content.decode()}
        command = request.get('verification_command')
        if not isinstance(command, list) or not command or not all(isinstance(s, str) and s for s in command):
            raise ValueError('Publication requires an explicit verification_command argv')
        verified = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=300)
        if verified.returncode:
            return {'status': 'failed_verification', 'returncode': verified.returncode,
                    'stdout': verified.stdout, 'stderr': verified.stderr}
        with publication_lock(root):
            workflow = read_json(root, WORKFLOW, {})
            node = next(n for n in workflow['nodes'] if n['node_id'] == observation['node_id'])
            if (observation['inputs'] != snapshot(root, node, observation.get('extra', []))
                    or observation['source_snapshot'] != inventory(root, workflow)):
                return {'status': 'stale', 'reason': 'Inputs changed during verification; reverify current inputs'}
            upstream = evaluate(root)['nodes']
            required_status = 'readiness_status' if observation['kind'] == 'contract' else 'status'
            if any(upstream.get(dep, {}).get(required_status) != 'valid'
                   for dep in dependencies(root, node, workflow)):
                return {'status': 'stale', 'reason': 'Upstream verification is stale or missing; repair it before publishing consumer evidence'}
            observation['verification'] = {'command': command, 'returncode': 0,
                                           'stdout': verified.stdout, 'stderr': verified.stderr}
            observation['outputs'] = outputs(root, node, observation['kind'])
            if any(value is None for value in observation['outputs'].values()):
                diff = {'outputs': missing_outputs(observation['outputs'])}
                return {'status': 'inconsistent', 'diff': diff, 'repair': repair_responsibility(root, node, diff),
                        'reason': 'Required documents or evidence are missing; delivery is incomplete'}
            state = read_json(root, STATE, {'nodes': {}})
            bucket = 'contracts' if observation['kind'] == 'contract' else 'nodes'
            state.setdefault(bucket, {})[node['node_id']] = observation
            if bucket == 'nodes':
                state.get('contracts', {}).pop(node['node_id'], None)
            write_json(root, STATE, state)
        return {'status': 'valid'}
    raise ValueError('Unknown operation')


def main():
    try:
        result = session(Path(sys.argv[1]).resolve(), json.load(sys.stdin))
    except (ValueError, KeyError, TypeError, OSError, StopIteration, subprocess.TimeoutExpired) as exc:
        result = {'status': 'invalid', 'reason': str(exc)}
    print(json.dumps(result, sort_keys=True))
    return 1 if result.get('status') in {'stale', 'invalid', 'inconsistent', 'failed_verification'} else 0


if __name__ == '__main__':
    raise SystemExit(main())
