"""A locally frozen user scope is the freshness observation's provenance."""
import json

import pytest

from .test_evidence_freshness import setup, invoke as freshness
from .test_product_intent_session import invoke, decide


@pytest.mark.parametrize('host', ['claude', 'codex'])
def test_local_scope_version_is_retained_without_rewriting_global_baseline(tmp_path, host):
    setup(tmp_path, host)
    (tmp_path / '.allforai/bootstrap/local-requirements.json').unlink()
    item = {'id': 'export', 'topic': 'scenarios', 'goal': 'Export account orders',
            'scope': ['orders'], 'business_rules': ['Account isolation'],
            'acceptance': ['Other accounts are excluded']}
    result = invoke(tmp_path, {'operation': 'admit', 'route': 'local-change',
        'goal': 'Add account CSV export', 'areas': ['orders'], 'items': [item]})
    assert result.returncode == 0, result.stdout
    assert decide(tmp_path, [{'operation': 'confirm', 'id': 'export', 'reason': 'Privacy'}]).returncode == 0
    frozen = invoke(tmp_path, {'operation': 'freeze', 'include': ['export'], 'exclude': {},
        'batch_id': 'local-scope', 'user_reference': 'user scope turn', 'reason': 'Account export only'})
    assert frozen.returncode == 0, frozen.stdout
    expected = json.loads(frozen.stdout)['baseline']['version']
    baseline = tmp_path / '.allforai/product-concept/concept-baseline.json'
    before = baseline.read_bytes() if baseline.exists() else None
    result, observed = freshness(tmp_path, 'observe', node_id='deliver-export')
    assert result.returncode == 0, observed
    assert observed['baseline_version'] == expected
    assert (baseline.read_bytes() if baseline.exists() else None) == before
