"""Expand explicitly approved per-surface axes; never sample or cap cases."""
import argparse
import itertools
import hashlib
import json
import re
from pathlib import Path
AXES = ('state', 'device', 'os', 'appearance', 'dynamic_type', 'locale', 'orientation')
DEVICE_RE = re.compile(r'^(\d+)x(\d+)@(\d+(?:\.\d+)?)$')


def device_dims(value, devices=None):
    """`WxH@scale` or a name mapped in the inventory's `devices` table → (width, height) in logical units."""
    m = DEVICE_RE.match(value)
    if m:
        return int(m.group(1)), int(m.group(2))
    entry = (devices or {}).get(value)
    if not isinstance(entry, dict) or not all(isinstance(entry.get(k), int) and entry[k] > 0 for k in ('width', 'height')):
        raise ValueError('device value is neither WxH@scale nor a mapped device: ' + value)
    return entry['width'], entry['height']


def effective_width(device, orientation, devices=None):
    """Layout width the page actually gets: the short side in portrait, the long side in landscape.
    A multitasking window (Slide Over, split screen, free-form) keeps its width when the device
    rotates: mark it `fixed_width: true` in the devices table and its width is used as declared."""
    w, h = device_dims(device, devices)
    if (devices or {}).get(device, {}).get('fixed_width') is True:
        return w
    if 'portrait' in orientation:
        return min(w, h)
    if 'landscape' in orientation:
        return max(w, h)
    return w


def _check_range(rng, label):
    if not isinstance(rng, dict) or not all(isinstance(rng.get(k), int) and rng[k] > 0 for k in ('min', 'max')) \
            or rng['min'] > rng['max'] or not isinstance(rng.get('basis'), str) or not rng['basis']:
        raise ValueError('invalid width_range (needs int min <= max and basis): ' + label)


def check_widths(surface, thresholds, width_range, devices):
    """The device axis must straddle every layout threshold and reach both ends of the width range,
    or the adaptive layout at those widths is untested by construction."""
    sid = surface['id']
    axes = surface['axes']
    widths = {effective_width(d, o, devices) for d in axes['device'] for o in axes['orientation']}
    rng = surface.get('width_range', width_range)
    if rng is not None:
        _check_range(rng, sid)
        if min(widths) > rng['min'] or max(widths) < rng['max']:
            raise ValueError('device axis misses width range end %d..%d: %s' % (rng['min'], rng['max'], sid))
    for t in thresholds or []:
        if not isinstance(t, dict) or not isinstance(t.get('width'), int) or t['width'] <= 0 \
                or not isinstance(t.get('basis'), str) or not t['basis']:
            raise ValueError('invalid layout threshold (needs int width and basis)')
        w = t['width']
        if rng is not None and not (rng['min'] < w <= rng['max']):
            continue   # outside this surface's declared width range: cannot be hit
        if not any(x < w for x in widths) or not any(x >= w for x in widths):
            raise ValueError('device axis misses layout threshold %d: %s' % (w, sid))


LOCALE_SPLIT = re.compile(r'[\s+/,;]+')


def locale_tokens(value):
    """A locale axis value may be compound ("zh-CN + 站点 en"); the tag must appear as its own token."""
    return set(LOCALE_SPLIT.split(value.strip()))


def required_locales(locales):
    """Locales the product ships minus the ones the user declined on the record."""
    if not isinstance(locales, dict) or not isinstance(locales.get('supported'), list) or not locales['supported'] \
            or any(not isinstance(l, str) or not l for l in locales['supported']) \
            or not isinstance(locales.get('basis'), str) or not locales['basis']:
        raise ValueError('invalid locales (needs non-empty supported list and basis)')
    supported = locales['supported']
    if len(set(supported)) != len(supported):
        raise ValueError('duplicate supported locale')
    declined = set()
    for d in locales.get('declined') or []:
        if not isinstance(d, dict) or d.get('locale') not in supported \
                or not isinstance(d.get('confirmation'), str) or not d['confirmation'].strip():
            raise ValueError('declined locale needs a supported tag and the user\'s confirmation')
        declined.add(d['locale'])
    rtl = locales.get('rtl') or []
    if not set(rtl) <= set(supported):
        raise ValueError('rtl locale not in supported list')
    return [l for l in supported if l not in declined]


def check_locales(surface, locales):
    sid = surface['id']
    required = required_locales(locales)
    scope = surface.get('locales')
    if scope is not None:
        if not isinstance(scope, dict) or not isinstance(scope.get('only'), list) or not scope['only'] \
                or not isinstance(scope.get('basis'), str) or not scope['basis'] \
                or not set(scope['only']) <= set(locales['supported']):
            raise ValueError('invalid surface locales scope (needs only[] within supported and basis): ' + sid)
        required = [l for l in required if l in scope['only']]
    present = set()
    for v in surface['axes']['locale']:
        present |= locale_tokens(v)
    missing = [l for l in required if l not in present]
    if missing:
        raise ValueError('locale axis misses shipped locale %s: %s' % (', '.join(missing), sid))


def expand(surfaces, thresholds=None, width_range=None, devices=None, locales=None):
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
        if thresholds or width_range or surface.get('width_range'):
            check_widths(surface, thresholds, width_range, devices)
        if locales is not None:
            check_locales(surface, locales)
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
    inv = json.loads(Path(args.inventory).read_text())
    print(json.dumps(expand(inv['surfaces'], inv.get('layout_thresholds'), inv.get('width_range'), inv.get('devices'),
                            inv.get('locales')), ensure_ascii=False, indent=2))
