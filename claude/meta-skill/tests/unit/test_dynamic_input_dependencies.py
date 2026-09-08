"""Observed and globbed artifact inputs participate in public freshness gates."""
import json
import subprocess
import sys

import pytest

from .test_evidence_freshness import setup, invoke, write, WORKFLOW


@pytest.mark.parametrize('host', ['claude', 'codex'])
@pytest.mark.parametrize('binding', ['runtime-read', 'declared-glob'])
@pytest.mark.parametrize('produced_as', ['exit_artifacts', 'required_documents'])
def test_consumed_artifact_producer_invalidates_transitive_consumers(tmp_path, host, binding, produced_as):
    setup(tmp_path, host)
    workflow = json.loads((tmp_path / WORKFLOW).read_text())
    if produced_as == 'required_documents':
        workflow['nodes'][0]['required_documents'] = workflow['nodes'][0].pop('exit_artifacts')
        # A required document declares how it is checked against current source (#13).
        workflow['nodes'][0]['document_verification'] = {'.allforai/bootstrap/export-report.json': [
            sys.executable, '-c', "import json; assert json.load(open('.allforai/bootstrap/export-report.json'))['status'] == 'passed'"]}
    consumer = {'node_id': 'consumer', 'source_inputs': [],
                'exit_artifacts': ['.allforai/bootstrap/consumer-report.json']}
    if binding == 'declared-glob':
        consumer['input_dependencies'] = ['.allforai/bootstrap/export-*.json']
    workflow['nodes'] += [consumer,
        {'node_id': 'downstream', 'source_inputs': [], 'hard_blocked_by': ['consumer'],
         'exit_artifacts': ['.allforai/bootstrap/downstream-report.json']},
        {'node_id': 'unrelated', 'source_inputs': ['warehouse.py'],
         'exit_artifacts': ['.allforai/bootstrap/warehouse-report.json']}]
    write(tmp_path, WORKFLOW, workflow)
    (tmp_path / 'warehouse.py').write_text('stock = 1\n')
    for node in workflow['nodes']:
        write(tmp_path, node.get('exit_artifacts', node.get('required_documents'))[0], {'status': 'passed'})

    def publish(node_id, discover=False):
        result, observed = invoke(tmp_path, 'observe', node_id=node_id)
        assert result.returncode == 0, observed
        if discover:
            result, observed = invoke(tmp_path, 'read', observation=observed['observation'],
                                      path='.allforai/bootstrap/export-report.json')
            assert result.returncode == 0, observed
        result, published = invoke(tmp_path, 'publish', observation=observed['observation'])
        assert result.returncode == 0, published

    for node in workflow['nodes']:
        publish(node['node_id'], binding == 'runtime-read' and node['node_id'] == 'consumer')
    _, before = invoke(tmp_path, 'check')
    assert all(item['status'] == 'valid' for item in before['nodes'].values())
    source = tmp_path / 'orders.py'
    source.write_text(source.read_text() + '\n# Producer input maintenance\n')
    _, changed = invoke(tmp_path, 'check')
    for node_id in ('deliver-export', 'consumer', 'downstream'):
        assert changed['nodes'][node_id]['status'] == 'stale'
        assert changed['nodes'][node_id]['readiness_status'] == 'stale'
    assert changed['nodes']['unrelated']['status'] == 'valid'
    checked = subprocess.run([sys.executable,
        str(tmp_path / '.allforai/bootstrap/scripts/check_artifacts.py'), str(tmp_path / WORKFLOW),
        '--node', 'consumer', '--json'], text=True, capture_output=True)
    assert json.loads(checked.stdout)['all_exist'] is False

    publish('deliver-export')
    _, producer_repaired = invoke(tmp_path, 'check')
    assert producer_repaired['nodes']['consumer']['status'] == 'stale'
    publish('consumer')
    _, consumer_repaired = invoke(tmp_path, 'check')
    assert consumer_repaired['nodes']['consumer']['status'] == 'valid'
    assert consumer_repaired['nodes']['downstream']['status'] == 'stale'
    publish('downstream')
    _, restored = invoke(tmp_path, 'check')
    assert all(item['status'] == 'valid' for item in restored['nodes'].values())


@pytest.mark.parametrize('host', ['claude', 'codex'])
@pytest.mark.parametrize('kind', ['contract', 'evidence'])
def test_publication_cannot_preapprove_a_consumer_of_stale_producer(tmp_path, host, kind):
    setup(tmp_path, host)
    workflow = json.loads((tmp_path / WORKFLOW).read_text())
    workflow['nodes'].append({'node_id': 'consumer', 'source_inputs': [],
        'hard_blocked_by': ['deliver-export'],
        'exit_artifacts': ['.allforai/bootstrap/consumer-report.json']})
    write(tmp_path, WORKFLOW, workflow)
    write(tmp_path, '.allforai/bootstrap/consumer-report.json', {'status': 'passed'})
    (tmp_path / '.allforai/bootstrap/node-specs/consumer.md').write_text('Verify export report\n')
    _, producer = invoke(tmp_path, 'observe', node_id='deliver-export', kind=kind)
    assert invoke(tmp_path, 'publish', observation=producer['observation'])[0].returncode == 0
    source = tmp_path / 'orders.py'
    source.write_text(source.read_text() + '\n# New producer state\n')
    _, consumer = invoke(tmp_path, 'observe', node_id='consumer', kind=kind)
    result, rejected = invoke(tmp_path, 'publish', observation=consumer['observation'])
    assert result.returncode == 1 and rejected['status'] == 'stale', rejected
    _, producer = invoke(tmp_path, 'observe', node_id='deliver-export', kind=kind)
    assert invoke(tmp_path, 'publish', observation=producer['observation'])[0].returncode == 0
    _, checked = invoke(tmp_path, 'check')
    field = 'readiness_status' if kind == 'contract' else 'status'
    assert checked['nodes']['consumer'][field] == 'stale'
    _, consumer = invoke(tmp_path, 'observe', node_id='consumer', kind=kind)
    assert invoke(tmp_path, 'publish', observation=consumer['observation'])[0].returncode == 0
    _, checked = invoke(tmp_path, 'check')
    assert checked['nodes']['consumer'][field] == 'valid'
    if kind == 'contract':
        assert checked['nodes']['consumer']['status'] == 'stale'
