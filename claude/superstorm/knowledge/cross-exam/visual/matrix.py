"""Expand explicitly approved per-surface axes; never sample or cap cases."""
import argparse
import itertools
import hashlib
import json
from pathlib import Path
AXES = ('state', 'device', 'os', 'appearance', 'dynamic_type', 'locale', 'orientation')


def expand(surfaces):
    cases = []
    seen = set()
    for surface in surfaces:
        sid = surface['id']
        if sid in seen:
            raise ValueError('duplicate surface: ' + sid)
        seen.add(sid)
        groups = surface.get('groups', [])
        if not isinstance(groups, list) or any(not isinstance(g, str) or not g for g in groups) or len(set(groups)) != len(groups):
            raise ValueError('invalid comparison groups: ' + sid)
        axes = surface['axes']
        if surface.get('scrollable') is True and not any(
                isinstance(s, str) and s.startswith('scroll-') for s in (axes.get('state') or [])):
            raise ValueError('scrollable surface without scroll- state: ' + sid)
        for axis in AXES:
            values = axes.get(axis)
            if not isinstance(values, list) or not values or any(not isinstance(v, str) or not v for v in values):
                raise ValueError('missing concrete axis: ' + sid + '/' + axis)
            if len(set(values)) != len(values):
                raise ValueError('duplicate axis values: ' + axis)
        for values in itertools.product(*(axes[a] for a in AXES)):
            row = dict(zip(AXES, values))
            identity = json.dumps({'surface': sid, **row}, sort_keys=True, ensure_ascii=False)
            case_id = 'V-' + hashlib.sha256(identity.encode()).hexdigest()
            cases.append({'id': case_id, 'surface': sid, **row,
                          'motion': row['state'] in surface.get('motion_states', []),
                          'groups': sorted(groups)})
    return cases


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('inventory')
    args = p.parse_args()
    print(json.dumps(expand(json.loads(Path(args.inventory).read_text())['surfaces']), ensure_ascii=False, indent=2))
