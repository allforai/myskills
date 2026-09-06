import pytest
from matrix import expand
from validation import AXES


def test_complete_product_without_cap():
    axes = {a: ['a', 'b', 'c'] for a in AXES}
    cases = expand([{'id': 'home', 'axes': axes, 'motion_states': ['b']}])
    assert len(cases) == 2187
    assert len({tuple(c[a] for a in AXES) for c in cases}) == 2187
    assert sum(c['motion'] for c in cases) == 729


def test_incomplete_axis_refused():
    with pytest.raises(ValueError):
        expand([{'id': 'home', 'axes': {}}])


def test_ids_survive_reorder_and_added_surfaces():
    axes = {a: ['default'] for a in AXES}
    home, settings = [{'id': sid, 'axes': axes} for sid in ('home', 'settings')]
    before = {c['surface']: c['id'] for c in expand([home, settings])}
    after = {c['surface']: c['id'] for c in expand([settings, home, {'id':'new', 'axes':axes}])}
    assert all(after[k] == v for k, v in before.items())


def test_groups_pass_through_and_do_not_change_ids():
    axes = {a: ['default'] for a in AXES}
    plain = expand([{'id': 'home', 'axes': axes}])[0]
    grouped = expand([{'id': 'home', 'axes': axes, 'groups': ['nav', 'buttons']}])[0]
    assert plain['id'] == grouped['id']
    assert plain['groups'] == [] and grouped['groups'] == ['buttons', 'nav']
    with pytest.raises(ValueError):
        expand([{'id': 'home', 'axes': axes, 'groups': ['nav', 'nav']}])
