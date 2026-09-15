"""Read-only gate reuse must reduce DAG work without hiding moving inputs."""
import json
from pathlib import Path

import pytest

from ..module_isolation import load


def put(root, path, value):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value))


def graph(root, module, count=12):
    nodes = [{'node_id': f'n{i}', 'source_inputs': ['src/**'],
              'hard_blocked_by': [f'n{j}' for j in range(max(0, i - 2), i)],
              'exit_artifacts': []} for i in range(count)]
    put(root, 'src/data.json', {'version': 1})
    put(root, module.WORKFLOW, {'nodes': nodes})
    @module._read_only_gate
    def observe(root):
        source = module.inventory(root, {'nodes': nodes})
        return {'nodes': {n['node_id']: {'inputs': module.snapshot(root, n),
                'outputs': {}, 'source_snapshot': source} for n in nodes}}
    put(root, module.STATE, observe(root))
    return nodes


def test_shared_ancestor_gate_reads_and_snapshots_scale_with_nodes(tmp_path, monkeypatch):
    module = load('evidence_freshness')
    nodes = graph(tmp_path, module)
    snapshots, reads = [], []
    original_snapshot, original_read = module._snapshot, Path.read_bytes
    def snapshot(*args, **kwargs):
        snapshots.append(args[1]['node_id'])
        return original_snapshot(*args, **kwargs)
    def read(path):
        reads.append(path)
        return original_read(path)
    monkeypatch.setattr(module, '_snapshot', snapshot)
    monkeypatch.setattr(Path, 'read_bytes', read)
    assert all(n['status'] == 'valid' for n in module.evaluate(tmp_path)['nodes'].values())
    assert len(snapshots) == len(nodes)  # Includes external-change and validity/diff checks.
    assert reads.count(tmp_path / module.STATE) == 2  # Initial read and boundary check.
    assert reads.count(tmp_path / 'src/data.json') <= 3  # Independent final tree check too.
    assert module._READ_EVALUATION.get() is None


def test_next_gate_sees_source_and_dynamic_read_changes(tmp_path):
    module = load('evidence_freshness')
    graph(tmp_path, module, 3)
    assert module.evaluate(tmp_path)['nodes']['n0']['status'] == 'valid'
    put(tmp_path, 'src/data.json', {'version': 2})
    assert module.evaluate(tmp_path)['nodes']['n0']['status'] == 'stale'
    put(tmp_path, 'src/data.json', {'version': 1})
    assert module.evaluate(tmp_path)['nodes']['n0']['status'] == 'valid'
    put(tmp_path, module.READS, {'n0': ['new-dependency.json']})
    put(tmp_path, 'new-dependency.json', {'version': 1})
    assert module.evaluate(tmp_path)['nodes']['n0']['status'] == 'stale'


@pytest.mark.parametrize('change', ['edit', 'add', 'missing_dependency'])
def test_input_change_during_cached_gate_is_refused(tmp_path, monkeypatch, change):
    module = load('evidence_freshness')
    graph(tmp_path, module, 3)
    original = module.outputs
    changed = False
    def outputs(*args, **kwargs):
        nonlocal changed
        result = original(*args, **kwargs)
        if not changed:
            changed = True
            if change == 'edit':
                put(tmp_path, 'src/data.json', {'version': 2})
            elif change == 'add':
                put(tmp_path, 'src/added.json', {'version': 1})
            else:
                put(tmp_path, module.READS, {'n0': ['new.json']})
        return result
    monkeypatch.setattr(module, 'outputs', outputs)
    with pytest.raises(ValueError, match='changed during freshness evaluation'):
        module.evaluate(tmp_path)
    assert module._READ_EVALUATION.get() is None


def test_cached_snapshot_still_rejects_dependency_cycle(tmp_path):
    module = load('evidence_freshness')
    nodes = graph(tmp_path, module, 3)
    nodes[0]['hard_blocked_by'] = ['n2']
    put(tmp_path, module.WORKFLOW, {'nodes': nodes})
    with pytest.raises(ValueError, match='Cyclic input dependency'):
        module.evaluate(tmp_path)


def test_readonly_scope_refuses_publication_and_discards_cache_on_error(tmp_path):
    module = load('evidence_freshness')
    @module._read_only_gate
    def bad_gate(root):
        module.write_json(root, module.STATE, {})
    with pytest.raises(ValueError, match='Cannot publish'):
        bad_gate(tmp_path)
    assert module._READ_EVALUATION.get() is None
    module.write_json(tmp_path, module.STATE, {'nodes': {}})
    assert (tmp_path / module.STATE).exists()


def test_gate_cache_does_not_survive_real_publish_verification(tmp_path, monkeypatch):
    import sys
    from .test_evidence_freshness import setup
    module = load('evidence_freshness')
    setup(tmp_path, 'claude')
    observed = module.session(tmp_path, {'operation': 'observe', 'node_id': 'deliver-export'})
    module.evaluate(tmp_path)  # Prime and discard a read-only gate in THIS interpreter.
    original = module.subprocess.run
    called = []
    def run(*args, **kwargs):
        assert module._READ_EVALUATION.get() is None
        called.append(True)
        return original(*args, **kwargs)
    monkeypatch.setattr(module.subprocess, 'run', run)
    result = module.session(tmp_path, {'operation': 'publish', 'observation': observed['observation'],
        'verification_command': [sys.executable, '-c',
            "from pathlib import Path; Path('orders.py').write_text('changed during real verification')"]})
    assert called
    assert result['status'] == 'stale'
    assert module._READ_EVALUATION.get() is None


def test_cached_json_directory_is_not_treated_as_missing_state(tmp_path):
    module = load('evidence_freshness')
    graph(tmp_path, module, 2)
    path = tmp_path / module.STATE
    path.unlink()
    path.mkdir()
    with pytest.raises(IsADirectoryError):
        module.evaluate(tmp_path)
