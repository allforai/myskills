"""Freshness behavior at copied bootstrap/resume and gate CLIs, not host proof."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import pytest

from .test_bootstrap_scope import project, write, SCRIPTS, REQUIREMENTS

WORKFLOW = '.allforai/bootstrap/workflow.json'


def invoke(root, operation, **request):
    if operation == 'publish' and 'verification_command' not in request:
        request['verification_command'] = [sys.executable, '-c',
            "from pathlib import Path; import json; "
            "assert all(json.loads(p.read_text()).get('status') == 'passed' "
            "for p in Path('.allforai/bootstrap').glob('*report.json'))"]
    result = subprocess.run([sys.executable, str(root / '.allforai/bootstrap/scripts/evidence_freshness.py'),
                             str(root)], input=json.dumps(dict(operation=operation, **request)),
                            text=True, capture_output=True, cwd=root)
    return result, json.loads(result.stdout) if result.stdout else {}


def setup(root, host):
    project(root, confirmed=True, host=host, source_inputs=None)
    source = SCRIPTS if host == 'claude' else Path(__file__).resolve().parents[4] / 'codex/meta-skill/scripts'
    for name in ('evidence_freshness.py', 'reconcile_bootstrap_workflow.py'):
        shutil.copy2(source / 'orchestrator' / name, root / '.allforai/bootstrap/scripts' / name)
    workflow = json.loads((root / WORKFLOW).read_text())
    workflow['nodes'][0]['source_inputs'] = ['orders.py']
    write(root, WORKFLOW, workflow)
    write(root, '.allforai/bootstrap/export-report.json', {'status': 'passed'})


@pytest.mark.parametrize('host', ['claude', 'codex'])
def test_observe_a_change_b_rejects_publication_until_b_is_reverified(tmp_path, host):
    setup(tmp_path, host)
    result, observed = invoke(tmp_path, 'observe', node_id='deliver-export')
    assert result.returncode == 0, result.stderr
    (tmp_path / 'orders.py').write_text('def list_orders(account): return [account]\n')
    result, rejected = invoke(tmp_path, 'publish', observation=observed['observation'])
    assert result.returncode == 1 and rejected['status'] == 'stale'
    result, current = invoke(tmp_path, 'observe', node_id='deliver-export')
    assert current['observation'] != observed['observation']
    # The verifier runs against B and produces its report before publishing B.
    write(tmp_path, '.allforai/bootstrap/export-report.json', {'status': 'passed', 'verified': 'account returned'})
    result, published = invoke(tmp_path, 'publish', observation=current['observation'])
    assert result.returncode == 0 and published['status'] == 'valid'
    result, checked = invoke(tmp_path, 'check')
    assert checked['nodes']['deliver-export']['status'] == 'valid'


@pytest.mark.parametrize('host', ['claude', 'codex'])
def test_source_drift_propagates_through_resume_and_both_gates_preserving_other_branch(tmp_path, host):
    setup(tmp_path, host)
    workflow = json.loads((tmp_path / WORKFLOW).read_text())
    workflow['nodes'] += [
        {'node_id': 'verify-export', 'source_inputs': [], 'hard_blocked_by': ['deliver-export'],
         'exit_artifacts': ['.allforai/bootstrap/verify.json']},
        {'node_id': 'warehouse', 'source_inputs': ['warehouse.py'],
         'exit_artifacts': ['.allforai/bootstrap/stock.json']},
    ]
    (tmp_path / 'warehouse.py').write_text('stock = 10\n')
    write(tmp_path, WORKFLOW, workflow)
    for node in workflow['nodes']:
        write(tmp_path, node['exit_artifacts'][0], {'status': 'passed'})
        _, observation = invoke(tmp_path, 'observe', node_id=node['node_id'])
        result, _ = invoke(tmp_path, 'publish', observation=observation['observation'])
        assert result.returncode == 0
    (tmp_path / 'orders.py').write_text('def list_orders(account): return [42]\n')
    _, checked = invoke(tmp_path, 'check')
    assert checked['nodes']['deliver-export']['status'] == 'stale'


    assert checked['nodes']['verify-export']['status'] == 'stale'
    assert checked['nodes']['warehouse']['status'] == 'valid'
    scripts = tmp_path / '.allforai/bootstrap/scripts'
    reconcile = subprocess.run([sys.executable, str(scripts / 'reconcile_bootstrap_workflow.py'),
                                str(tmp_path), '--write'], text=True, capture_output=True)
    assert reconcile.returncode == 0, reconcile.stderr
    plan = json.loads(reconcile.stdout)['reconciliation_plan']
    assert next(i for i in plan['items'] if i['node_id'] == 'verify-export')['action'] == 'invalidate'
    for node, expected in [('deliver-export', False), ('verify-export', False), ('warehouse', True)]:
        checked = subprocess.run([sys.executable, str(scripts / 'check_artifacts.py'), str(tmp_path / WORKFLOW),
                                  '--node', node, '--json'], text=True, capture_output=True)
        assert json.loads(checked.stdout)['all_exist'] is expected
    readiness = subprocess.run([sys.executable, str(scripts / 'validate_unattended_readiness.py'), str(tmp_path)],
                               text=True, capture_output=True)
    assert readiness.returncode == 1 and 'stale_evidence' in readiness.stdout


@pytest.mark.parametrize('host', ['claude', 'codex'])
def test_unknown_source_impact_and_output_tampering_cannot_prove_completion(tmp_path, host):
    setup(tmp_path, host)
    _, observation = invoke(tmp_path, 'observe', node_id='deliver-export')
    invoke(tmp_path, 'publish', observation=observation['observation'])
    (tmp_path / 'new_behavior.py').write_text('enabled = True\n')
    _, checked = invoke(tmp_path, 'check')
    assert checked['nodes']['deliver-export']['status'] == 'uncertain'
    assert checked['uncertain_inputs'] == ['new_behavior.py']
    (tmp_path / 'new_behavior.py').unlink()
    write(tmp_path, '.allforai/bootstrap/export-report.json', {'status': 'passed', 'unverified': True})
    _, checked = invoke(tmp_path, 'check')
    assert checked['nodes']['deliver-export']['status'] == 'stale'


@pytest.mark.parametrize('host', ['claude', 'codex'])
def test_baseline_and_additional_reads_invalidate_without_generated_self_loop(tmp_path, host):
    setup(tmp_path, host)
    (tmp_path / 'policy.txt').write_text('region = JP')
    _, original = invoke(tmp_path, 'observe', node_id='deliver-export')
    result, observed = invoke(tmp_path, 'read', observation=original['observation'], path='policy.txt')
    assert result.returncode == 0 and observed['content'] == 'region = JP'
    result, _ = invoke(tmp_path, 'publish', observation=observed['observation'])
    assert result.returncode == 0
    before = (tmp_path / '.allforai/bootstrap/evidence-freshness.json').read_bytes()
    write(tmp_path, '.allforai/bootstrap/sync-report.json', {'status': 'passed'})
    for _ in range(2):
        _, checked = invoke(tmp_path, 'check')
        assert checked['nodes']['deliver-export']['status'] == 'valid'
    assert (tmp_path / '.allforai/bootstrap/evidence-freshness.json').read_bytes() == before
    (tmp_path / 'policy.txt').write_text('region = US')
    _, checked = invoke(tmp_path, 'check')
    assert checked['nodes']['deliver-export']['status'] == 'stale'


    # Additional reads stay dependencies on later observation, not only the first one.
    _, observation = invoke(tmp_path, 'observe', node_id='deliver-export')
    invoke(tmp_path, 'publish', observation=observation['observation'])
    requirements = json.loads((tmp_path / REQUIREMENTS).read_text())
    requirements['requirements'][0]['revision'] = 2
    requirements['requirements'][0]['goal'] = 'User revised export direction'
    write(tmp_path, REQUIREMENTS, requirements)
    _, checked = invoke(tmp_path, 'check')
    assert checked['nodes']['deliver-export']['status'] == 'stale'


@pytest.mark.parametrize('host', ['claude', 'codex'])
def test_failed_verification_or_edit_during_verification_never_publishes(tmp_path, host):
    setup(tmp_path, host)
    _, observation = invoke(tmp_path, 'observe', node_id='deliver-export')
    result, rejected = invoke(tmp_path, 'publish', observation=observation['observation'],
                              verification_command=[sys.executable, '-c', 'raise SystemExit(1)'])
    assert result.returncode == 1 and rejected['status'] == 'failed_verification'
    result, rejected = invoke(tmp_path, 'publish', observation=observation['observation'],
                              verification_command=[sys.executable, '-c',
                                  "from pathlib import Path; Path('orders.py').write_text('changed = True')"])
    assert result.returncode == 1 and rejected['status'] == 'stale'
    assert not (tmp_path / '.allforai/bootstrap/evidence-freshness.json').exists()


@pytest.mark.parametrize('host', ['claude', 'codex'])
def test_fresh_contract_allows_execution_but_cannot_claim_completion(tmp_path, host):
    setup(tmp_path, host)
    _, observed = invoke(tmp_path, 'observe', node_id='deliver-export', kind='contract')
    result, published = invoke(tmp_path, 'publish', observation=observed['observation'])
    assert result.returncode == 0, published
    scripts = tmp_path / '.allforai/bootstrap/scripts'
    ready = subprocess.run([sys.executable, str(scripts / 'validate_unattended_readiness.py'), str(tmp_path)],
                           text=True, capture_output=True)
    assert ready.returncode == 0, ready.stdout
    done = subprocess.run([sys.executable, str(scripts / 'check_artifacts.py'), str(tmp_path / WORKFLOW),
                           '--node', 'deliver-export', '--json'], text=True, capture_output=True)
    assert json.loads(done.stdout)['all_exist'] is False
    (tmp_path / 'orders.py').write_text('changed = True\n')
    ready = subprocess.run([sys.executable, str(scripts / 'validate_unattended_readiness.py'), str(tmp_path)],
                           text=True, capture_output=True)
    assert ready.returncode == 1 and 'stale_evidence' in ready.stdout


@pytest.mark.parametrize('host', ['claude', 'codex'])
def test_baseline_scope_changes_and_artifact_dependencies_invalidate_transitively(tmp_path, host):
    setup(tmp_path, host)
    baseline = '.allforai/product-concept/concept-baseline.json'
    write(tmp_path, baseline, {'intent_baseline': {'version': 1, 'requirement_refs':
        [{'path': REQUIREMENTS, 'id': 'export', 'revision': 1}], 'excluded': {}}})
    workflow = json.loads((tmp_path / WORKFLOW).read_text())
    workflow['nodes'].append({'node_id': 'consumer', 'source_inputs': [],
        'input_dependencies': ['.allforai/bootstrap/export-report.json'],
        'exit_artifacts': ['.allforai/bootstrap/consumer.json']})
    write(tmp_path, WORKFLOW, workflow)
    write(tmp_path, '.allforai/bootstrap/consumer.json', {'status': 'passed'})
    for node in workflow['nodes']:
        _, observed = invoke(tmp_path, 'observe', node_id=node['node_id'])
        assert invoke(tmp_path, 'publish', observation=observed['observation'])[0].returncode == 0
    write(tmp_path, baseline, {'intent_baseline': {'version': 2, 'requirement_refs': [],
                                                 'excluded': {'export': 'User deferred export'}}})
    _, checked = invoke(tmp_path, 'check')
    assert checked['nodes']['deliver-export']['status'] == 'stale'
    assert checked['nodes']['consumer']['status'] == 'stale'


@pytest.mark.parametrize('host', ['claude', 'codex'])
def test_glob_membership_and_missing_dependency_declarations_are_not_zero_impact(tmp_path, host):
    setup(tmp_path, host)
    workflow = json.loads((tmp_path / WORKFLOW).read_text())
    workflow['nodes'][0]['source_inputs'] = ['*.py']
    write(tmp_path, WORKFLOW, workflow)
    _, observed = invoke(tmp_path, 'observe', node_id='deliver-export')
    assert invoke(tmp_path, 'publish', observation=observed['observation'])[0].returncode == 0
    (tmp_path / 'new_behavior.py').write_text('enabled = True')
    _, checked = invoke(tmp_path, 'check')
    assert checked['nodes']['deliver-export']['status'] == 'stale'
    del workflow['nodes'][0]['source_inputs']
    write(tmp_path, WORKFLOW, workflow)
    result, observed = invoke(tmp_path, 'observe', node_id='deliver-export')
    assert result.returncode == 1 and 'source_inputs' in observed['reason']


@pytest.mark.parametrize('host', ['claude', 'codex'])
def test_revalidating_producer_does_not_revive_consumers_old_evidence(tmp_path, host):
    setup(tmp_path, host)
    workflow = json.loads((tmp_path / WORKFLOW).read_text())
    workflow['nodes'].append({'node_id': 'consumer', 'source_inputs': [], 'hard_blocked_by': ['deliver-export'],
                              'exit_artifacts': ['.allforai/bootstrap/consumer.json']})
    write(tmp_path, WORKFLOW, workflow)
    write(tmp_path, '.allforai/bootstrap/consumer.json', {'status': 'passed'})
    for node in workflow['nodes']:
        _, observed = invoke(tmp_path, 'observe', node_id=node['node_id'])
        invoke(tmp_path, 'publish', observation=observed['observation'])
    (tmp_path / 'orders.py').write_text('orders = [42]')
    _, observed = invoke(tmp_path, 'observe', node_id='deliver-export')
    invoke(tmp_path, 'publish', observation=observed['observation'])
    _, checked = invoke(tmp_path, 'check')
    assert checked['nodes']['deliver-export']['status'] == 'valid'
    assert checked['nodes']['consumer']['status'] == 'stale'


@pytest.mark.parametrize('host', ['claude', 'codex'])
def test_failed_publication_retains_additional_dependency_for_next_observation(tmp_path, host):
    setup(tmp_path, host)
    (tmp_path / 'policy.txt').write_text('A')
    _, observed = invoke(tmp_path, 'observe', node_id='deliver-export')
    _, observed = invoke(tmp_path, 'read', observation=observed['observation'], path='policy.txt')
    (tmp_path / 'policy.txt').write_text('B')
    assert invoke(tmp_path, 'publish', observation=observed['observation'])[0].returncode == 1
    _, observed = invoke(tmp_path, 'observe', node_id='deliver-export')
    assert 'policy.txt' in observed['inputs']['files']
    assert invoke(tmp_path, 'publish', observation=observed['observation'])[0].returncode == 0


@pytest.mark.parametrize('host', ['claude', 'codex'])
def test_same_commit_distinct_dirty_states_and_unrelated_baseline_revisions(tmp_path, host, monkeypatch):
    setup(tmp_path, host)
    # Git hooks export repository/index variables: fixture Git must never inherit them.
    enclosing = SCRIPTS.parents[2]
    fixture_env = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
    enclosing_git = subprocess.check_output(['git', 'rev-parse', '--absolute-git-dir'],
                                            cwd=enclosing, env=fixture_env, text=True).strip()
    enclosing_index = Path(subprocess.check_output(['git', 'rev-parse', '--path-format=absolute', '--git-path', 'index'],
                                                   cwd=enclosing, env=fixture_env, text=True).strip())
    enclosing_head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=enclosing, env=fixture_env)
    index_before = enclosing_index.read_bytes()
    config_path = Path(subprocess.check_output(['git', 'rev-parse', '--path-format=absolute', '--git-common-dir'],
                                               cwd=enclosing, env=fixture_env, text=True).strip()) / 'config'
    config_before = config_path.read_bytes()
    monkeypatch.setenv('GIT_DIR', enclosing_git)
    monkeypatch.setenv('GIT_WORK_TREE', str(enclosing))
    monkeypatch.setenv('GIT_INDEX_FILE', str(enclosing_index))
    fixture_env = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
    for args in [['init', '-q'], ['add', 'orders.py'],
                 ['-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', '-c', 'commit.gpgsign=false',
                  '-c', 'core.hooksPath=/dev/null', 'commit', '-qm', 'Fixture']]:
        subprocess.run(['git', *args], cwd=tmp_path, env=fixture_env, check=True, capture_output=True)
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=tmp_path, env=fixture_env)
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=enclosing, env=fixture_env) == enclosing_head
    assert enclosing_index.read_bytes() == index_before
    assert config_path.read_bytes() == config_before
    baseline = '.allforai/product-concept/concept-baseline.json'
    selected = {'path': REQUIREMENTS, 'id': 'export', 'revision': 1}
    write(tmp_path, baseline, {'intent_baseline': {'version': 1, 'requirement_refs': [selected]}})
    (tmp_path / 'orders.py').write_text('orders = [1]')
    _, a = invoke(tmp_path, 'observe', node_id='deliver-export')
    assert invoke(tmp_path, 'publish', observation=a['observation'])[0].returncode == 0
    (tmp_path / 'orders.py').write_text('orders = [2]')
    _, b = invoke(tmp_path, 'observe', node_id='deliver-export')
    assert a['observation'] != b['observation']
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=tmp_path, env=fixture_env) == head
    assert invoke(tmp_path, 'publish', observation=b['observation'])[0].returncode == 0
    write(tmp_path, baseline, {'intent_baseline': {'version': 2, 'requirement_refs':
        [selected, {'path': REQUIREMENTS, 'id': 'stock', 'revision': 2}]}})
    _, checked = invoke(tmp_path, 'check')
    assert checked['nodes']['deliver-export']['status'] == 'valid'


@pytest.mark.parametrize('host', ['claude', 'codex'])
def test_broad_source_selection_excludes_generated_documents_and_copied_helpers(tmp_path, host):
    setup(tmp_path, host)
    workflow = json.loads((tmp_path / WORKFLOW).read_text())
    workflow['nodes'][0].update(source_inputs=['.'], required_documents=['docs/order-facts.md'])
    write(tmp_path, WORKFLOW, workflow)
    _, observed = invoke(tmp_path, 'observe', node_id='deliver-export')
    verifier = [sys.executable, '-c',
        "from pathlib import Path; import json\n"
        "namespace = {}; exec(Path('orders.py').read_text(), namespace)\n"
        "assert namespace['list_orders']('account') == []\n"
        "Path('docs').mkdir(exist_ok=True)\n"
        "Path('docs/order-facts.md').write_text('Observed list_orders returns an empty list')\n"
        "Path('.allforai/bootstrap/export-report.json').write_text(json.dumps({'status': 'passed', 'executed': True}))\n"]
    result, published = invoke(tmp_path, 'publish', observation=observed['observation'], verification_command=verifier)
    assert result.returncode == 0, published
    assert (tmp_path / 'docs/order-facts.md').read_text() == 'Observed list_orders returns an empty list'
    assert json.loads((tmp_path / '.allforai/bootstrap/export-report.json').read_text())['executed'] is True
    _, checked = invoke(tmp_path, 'check')
    assert checked['nodes']['deliver-export']['status'] == 'valid'


@pytest.mark.parametrize('host', ['claude', 'codex'])
def test_parallel_publication_preserves_both_unrelated_records(tmp_path, host):
    setup(tmp_path, host)
    workflow = json.loads((tmp_path / WORKFLOW).read_text())
    workflow['nodes'].append({'node_id': 'warehouse', 'source_inputs': [],
                              'exit_artifacts': ['.allforai/bootstrap/stock.json']})
    write(tmp_path, WORKFLOW, workflow)
    write(tmp_path, '.allforai/bootstrap/stock.json', {'status': 'passed'})
    observations = [invoke(tmp_path, 'observe', node_id=n['node_id'])[1] for n in workflow['nodes']]
    def publish(observed):
        command = [sys.executable, '-c',
            "from pathlib import Path; import time\n"
            f"Path('.allforai/bootstrap/ready-{observed['node_id']}').touch()\n"
            "for _ in range(300):\n"
            " if len(list(Path('.allforai/bootstrap').glob('ready-*'))) == 2: break\n"
            " time.sleep(.01)\n"
            "else: raise SystemExit(1)\n"]
        return invoke(tmp_path, 'publish', observation=observed['observation'], verification_command=command)[0]
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(publish, observations))
    assert all(result.returncode == 0 for result in results)
    _, checked = invoke(tmp_path, 'check')
    assert all(record['status'] == 'valid' for record in checked['nodes'].values())


@pytest.mark.parametrize('host', ['claude', 'codex'])
def test_bootstrap_rejects_node_spec_that_omits_declared_source_contract(tmp_path, host):
    setup(tmp_path, host)
    result = subprocess.run([sys.executable, str(tmp_path / '.allforai/bootstrap/scripts/validate_bootstrap.py'),
                              str(tmp_path / '.allforai/bootstrap')], text=True, capture_output=True)
    assert result.returncode == 1 and 'source_inputs' in result.stdout


@pytest.mark.parametrize('host', ['claude', 'codex'])
def test_selected_intent_payload_drift_in_real_producer_baseline_is_stale(tmp_path, host):
    from .test_product_intent_session import invoke as product_session, draft, decide, TOPICS
    from .test_validate_bootstrap import ATTENTION_CONTRACT_BODY
    setup(tmp_path, host)
    assert product_session(tmp_path, draft()).returncode == 0
    assert decide(tmp_path, [{'operation': 'confirm', 'id': 'target-users', 'reason': 'Chosen customers'}]).returncode == 0
    freeze = {'operation': 'freeze', 'batch_id': 'scope', 'user_reference': 'Explicit user scope',
              'reason': 'Focus first release', 'include': ['target-users'],
              'exclude': {topic: 'Deferred by user' for topic in [*TOPICS[1:], 'conflict']}}
    assert product_session(tmp_path, freeze).returncode == 0
    plan = {'operation': 'plan', 'nodes': [{'node_id': 'deliver-export', 'capability': 'implement',
            'goal': 'Serve confirmed customers', 'intent_ids': ['target-users'], 'source_inputs': ['orders.py'],
            'responsibilities': ['product', 'technical', 'implementation', 'documentation', 'verification'],
            'exit_artifacts': ['.allforai/bootstrap/export-report.json'], 'body': ATTENTION_CONTRACT_BODY}],
            'not_applicable': {'experience': 'Headless service'}}
    assert product_session(tmp_path, plan).returncode == 0
    _, observed = invoke(tmp_path, 'observe', node_id='deliver-export')
    assert invoke(tmp_path, 'publish', observation=observed['observation'])[0].returncode == 0
    baseline_path = '.allforai/product-concept/concept-baseline.json'
    baseline = json.loads((tmp_path / baseline_path).read_text())
    baseline['intent_baseline']['intents'][0]['goal'] = 'Unapproved replacement customers'
    baseline['intent_baseline']['version'] += 1
    write(tmp_path, baseline_path, baseline)
    _, checked = invoke(tmp_path, 'check')
    assert checked['nodes']['deliver-export']['status'] == 'stale'
    assert checked['nodes']['deliver-export']['readiness_status'] == 'stale'
