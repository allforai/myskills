"""Expand explicitly approved per-surface axes; never sample or cap cases."""
import argparse
import inspect
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


PLATFORMS = ('web', 'ios', 'android', 'macos')
DESKTOP_WIDTH_FLOOR = 1920           # an external display; the widest common desktop window
FORM_FACTORS = ('desktop', 'mobile', 'both')
IMPLIED_FORM_FACTOR = {'macos': 'desktop', 'ios': 'mobile', 'android': 'mobile'}


def effective_form_factor(platform, form_factor):
    """web must say whether it targets a desktop window, a phone, or both; native platforms imply it."""
    implied = IMPLIED_FORM_FACTOR.get(platform)
    if form_factor is None:
        if platform == 'web':
            raise ValueError('web inventory must declare form_factor desktop|mobile|both')
        return implied
    if form_factor not in FORM_FACTORS:
        raise ValueError('invalid form_factor (desktop|mobile|both): ' + str(form_factor))
    if implied and form_factor != implied:
        raise ValueError('form_factor %s contradicts platform %s (implies %s)' % (form_factor, platform, implied))
    return form_factor


def check_desktop_floor(width_range, form_factor):
    """A desktop target that never reaches a wide display has an untested wide end by construction."""
    if form_factor in ('desktop', 'both'):
        if width_range is None:
            raise ValueError('%s inventory must declare a global width_range (its max is checked against '
                             'the desktop floor %d)' % (form_factor, DESKTOP_WIDTH_FLOOR))
        _check_range(width_range, 'inventory')
        if width_range['max'] < DESKTOP_WIDTH_FLOOR:
            raise ValueError('desktop width floor %d not reached: width_range.max is %d'
                             % (DESKTOP_WIDTH_FLOOR, width_range['max']))


def _check_range(rng, label):
    if not isinstance(rng, dict) or not all(isinstance(rng.get(k), int) and rng[k] > 0 for k in ('min', 'max')) \
            or rng['min'] > rng['max'] or not isinstance(rng.get('basis'), str) or not rng['basis']:
        raise ValueError('invalid width_range (needs int min <= max and basis): ' + label)


def check_widths(surface, thresholds, width_range, devices):
    """The device axis must straddle every layout threshold, reach both ends of the width range and stay
    inside it, or the adaptive layout at those widths is untested by construction. Returns the range the
    surface was checked against (its own narrowed one, or the global one)."""
    sid = surface['id']
    axes = surface['axes']
    widths = {effective_width(d, o, devices) for d in axes['device'] for o in axes['orientation']}
    rng = surface.get('width_range') or width_range
    if rng is not None:
        _check_range(rng, sid)
        if width_range is not None and rng is not width_range:
            _check_range(width_range, 'inventory')
            if rng['min'] < width_range['min'] or rng['max'] > width_range['max']:
                raise ValueError('surface width_range %d..%d outside the global width_range %d..%d: %s'
                                 % (rng['min'], rng['max'], width_range['min'], width_range['max'], sid))
        if min(widths) > rng['min'] or max(widths) < rng['max']:
            raise ValueError('device axis misses width range end %d..%d: %s' % (rng['min'], rng['max'], sid))
        if min(widths) < rng['min'] or max(widths) > rng['max']:
            raise ValueError('device axis outside width range %d..%d (widen the range or drop the device): %s'
                             % (rng['min'], rng['max'], sid))
    for t in thresholds or []:
        if not isinstance(t, dict) or not isinstance(t.get('width'), int) or t['width'] <= 0 \
                or not isinstance(t.get('basis'), str) or not t['basis']:
            raise ValueError('invalid layout threshold (needs int width and basis)')
        w = t['width']
        if rng is not None and not (rng['min'] < w <= rng['max']):
            continue   # outside this surface's declared width range: cannot be hit
        if not any(x < w for x in widths) or not any(x >= w for x in widths):
            raise ValueError('device axis misses layout threshold %d: %s' % (w, sid))
    return rng


SEGMENT_SPLIT = re.compile(r'[+/,;]')
TOKEN_SPLIT = re.compile(r'[\s+/,;]+')


def value_tokens(value):
    """An axis value may be compound ("浏览器 zh-CN + 站点 en", "zoom 150% + 字号 20px"). A supported value
    is present when it equals the whole value, one of its separator-delimited segments, or one whitespace token."""
    v = value.strip()
    return {v} | {s.strip() for s in SEGMENT_SPLIT.split(v) if s.strip()} | set(TOKEN_SPLIT.split(v))


locale_tokens = value_tokens   # kept for callers written against the locale-only version


def required_values(axis, spec):
    """Values the code supports on this axis minus the ones the user declined on the record."""
    key = 'locale' if axis == 'locale' else 'value'
    noun = 'locales' if axis == 'locale' else axis + ' support'
    if not isinstance(spec, dict) or not isinstance(spec.get('supported'), list) or not spec['supported'] \
            or any(not isinstance(v, str) or not v for v in spec['supported']) \
            or not isinstance(spec.get('basis'), str) or not spec['basis']:
        raise ValueError('invalid %s (needs non-empty supported list and basis)' % noun)
    supported = spec['supported']
    if len(set(supported)) != len(supported):
        raise ValueError('duplicate supported value on ' + axis)
    declined = set()
    for d in spec.get('declined') or []:
        tag = d.get(key) if isinstance(d, dict) else None
        if tag is None and isinstance(d, dict):
            tag = d.get('value') or d.get('locale')
        if tag not in supported or not isinstance(d.get('confirmation'), str) or not d['confirmation'].strip():
            raise ValueError("declined %s needs a supported %s and the user's confirmation"
                             % (axis, 'tag' if axis == 'locale' else 'value'))
        declined.add(tag)
    if axis == 'locale' and not set(spec.get('rtl') or []) <= set(supported):
        raise ValueError('rtl locale not in supported list')
    return [v for v in supported if v not in declined]


required_locales = lambda locales: required_values('locale', locales)


def check_axis_support(surface, axis, spec):
    sid = surface['id']
    if axis not in AXES:
        raise ValueError('axis_support names an unknown axis: ' + axis)
    required = required_values(axis, spec)
    scope = surface.get('locales') if axis == 'locale' else (surface.get('axis_scope') or {}).get(axis)
    if scope is not None:
        if not isinstance(scope, dict) or not isinstance(scope.get('only'), list) or not scope['only'] \
                or not isinstance(scope.get('basis'), str) or not scope['basis'] \
                or not set(scope['only']) <= set(spec['supported']):
            raise ValueError('invalid surface %s scope (needs only[] within supported and basis): %s'
                             % ('locales' if axis == 'locale' else axis, sid))
        required = [v for v in required if v in scope['only']]
    present = set()
    for v in surface['axes'][axis]:
        present |= value_tokens(v)
    missing = [v for v in required if v not in present]
    if missing:
        raise ValueError('%s axis misses %s %s: %s' % (axis, 'shipped locale' if axis == 'locale' else 'supported value',
                                                     ', '.join(missing), sid))


def check_locales(surface, locales):
    check_axis_support(surface, 'locale', locales)


def merged_support(axis_support, locales):
    """`locales` is the locale axis's support declaration; `axis_support` carries every other axis."""
    support = dict(axis_support or {})
    if locales is not None:
        if 'locale' in support:
            raise ValueError('declare the locale axis once: locales or axis_support.locale')
        support['locale'] = locales
    return support


def _abstraction_plan(surface, abstractions, anchor):
    """Which axes are declared independent for this surface, which of their values stay coupled (e.g. an RTL
    locale), and the anchor value every other axis sits at while one independent axis varies."""
    axes = surface['axes']
    plan = {}
    for ab in list(abstractions or []) + list(surface.get('abstractions') or []):
        axis = ab.get('axis') if isinstance(ab, dict) else None
        if axis not in AXES or not isinstance(ab.get('basis'), str) or not ab['basis'] \
                or not isinstance(ab.get('confirmation'), str) or not ab['confirmation'].strip():
            raise ValueError('invalid abstraction (needs axis, basis and the user\'s confirmation): ' + surface['id'])
        keep = ab.get('keep_coupled') or []
        if not set(keep) <= set(axes[axis]):
            raise ValueError('keep_coupled names a value not on the axis: %s/%s' % (surface['id'], axis))
        cross = ab.get('cross_with', ['state'])
        if not isinstance(cross, list) or not set(cross) <= set(AXES) or axis in cross:
            raise ValueError('cross_with must list other axes: %s/%s' % (surface['id'], axis))
        plan[axis] = {'keep': set(keep), 'cross': set(cross)}
    anchors = {}
    for axis in AXES:
        value = (surface.get('anchor') or anchor or {}).get(axis, axes[axis][0])
        if value not in axes[axis]:
            raise ValueError('anchor value not on the axis: %s/%s' % (surface['id'], axis))
        anchors[axis] = value
    return plan, anchors


def _abstracted_by(row, plan, anchors):
    """[] keeps the case. Otherwise the independent axes whose off-anchor values this case crosses with
    something else that is also off-anchor — the combination the abstraction says need not be looked at."""
    off_independent = [a for a, spec in plan.items() if row[a] != anchors[a] and row[a] not in spec['keep']]
    if not off_independent:
        return []                                   # full product over the coupled part
    if len(off_independent) == 1:
        axis = off_independent[0]
        cross = plan[axis]['cross']
        others_at_anchor = all(row[a] == anchors[a] or a in cross for a in AXES if a != axis)
        if others_at_anchor:
            return []                               # one independent axis varied, crossed only with cross_with
    return sorted(off_independent)


def expand(surfaces, layout_thresholds=None, width_range=None, devices=None, locales=None, axis_support=None,
           abstractions=None, anchor=None, platform=None, form_factor=None):
    if platform is not None and platform not in PLATFORMS:
        raise ValueError('unknown platform %r (web|ios|android|macos)' % (platform,))
    check_desktop_floor(width_range, effective_form_factor(platform, form_factor))
    cases = []
    seen = set()
    reached_max = width_range is None
    for surface in surfaces:
        if platform == 'web' and not isinstance(surface.get('scrollable'), bool):
            raise ValueError('web surface must declare scrollable true|false: ' + surface['id'])
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
        if layout_thresholds or width_range or surface.get('width_range'):
            rng = check_widths(surface, layout_thresholds, width_range, devices)
            if width_range is not None and rng is not None and rng['max'] >= width_range['max']:
                reached_max = True
        for axis, spec in merged_support(axis_support, locales).items():
            check_axis_support(surface, axis, spec)
        plan, anchors = _abstraction_plan(surface, abstractions, anchor)
        for values in itertools.product(*(axes[a] for a in AXES)):
            row = dict(zip(AXES, values))
            identity = json.dumps({'surface': sid, **row}, sort_keys=True, ensure_ascii=False)
            case_id = 'V-' + hashlib.sha256(identity.encode()).hexdigest()
            case = {'id': case_id, 'surface': sid, **row,
                    'motion': row['state'] in surface.get('motion_states', []),
                    'groups': sorted(groups)}
            if plan:
                case['abstracted_by'] = _abstracted_by(row, plan, anchors)
            cases.append(case)
    if not reached_max:
        raise ValueError('no surface reaches width_range.max %d: every surface narrowed its range, so the wide '
                         'end is untested' % width_range['max'])
    return cases


# every keyword of expand() is an inventory top-level key of the same name
INVENTORY_KEYS = tuple(p for p in inspect.signature(expand).parameters if p != 'surfaces')


def expand_inventory(inventory):
    """Expand a surface inventory as frozen on disk: the one place that knows which top-level keys feed
    expansion, so the CLI and the validator's replay cannot drift apart."""
    if not isinstance(inventory.get('platform'), str):
        raise ValueError('inventory must declare platform (web|ios|android|macos)')
    return expand(inventory['surfaces'], **{k: inventory.get(k) for k in INVENTORY_KEYS})


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('inventory')
    args = p.parse_args()
    inv = json.loads(Path(args.inventory).read_text())
    rows = expand_inventory(inv)
    kept = [c for c in rows if not c.get('abstracted_by')]
    import sys
    print('cases: %d total, %d to capture, %d abstracted' % (len(rows), len(kept), len(rows) - len(kept)), file=sys.stderr)
    for axis in AXES:
        counts = {}
        for c in kept:
            counts[c[axis]] = counts.get(c[axis], 0) + 1
        print('  %s: %s' % (axis, ', '.join('%s=%d' % kv for kv in sorted(counts.items()))), file=sys.stderr)
    print(json.dumps(rows, ensure_ascii=False, indent=2))
