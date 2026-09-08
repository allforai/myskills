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


def test_scrollable_surface_requires_scroll_state():
    axes = {a: ['default'] for a in AXES}
    with pytest.raises(ValueError, match='scrollable surface without scroll- state'):
        expand([{'id': 'feed', 'scrollable': True, 'axes': axes}])
    ok = expand([{'id': 'feed', 'scrollable': True,
                  'axes': {**axes, 'state': ['default', 'scroll-bottom']}}])
    assert {c['state'] for c in ok} == {'default', 'scroll-bottom'}


THRESHOLDS = [{'width': 768, 'basis': 'tailwind.config.js:5'}, {'width': 1024, 'basis': 'tailwind.config.js:5'}]
RANGE = {'min': 900, 'max': 1920, 'basis': 'main.ts:12 minWidth 900; 外接显示器 1920'}


def _axes(devices, orientation=('landscape',)):
    return {**{a: ['default'] for a in AXES}, 'device': list(devices), 'orientation': list(orientation)}


def test_single_screen_size_cannot_satisfy_thresholds():
    with pytest.raises(ValueError, match='misses layout threshold 768'):
        expand([{'id': 'chat', 'axes': _axes(['1512x982@2'])}], THRESHOLDS)


def test_device_axis_must_straddle_every_threshold_and_reach_range_ends():
    ok = expand([{'id': 'chat', 'axes': _axes(['900x600@2', '1000x700@2', '1512x982@2', '1920x1080@1'])}],
                THRESHOLDS, RANGE)
    assert len(ok) == 4
    with pytest.raises(ValueError, match='misses width range end 900..1920'):
        expand([{'id': 'chat', 'axes': _axes(['900x600@2', '1000x700@2', '1512x982@2'])}], THRESHOLDS, RANGE)


def test_threshold_outside_range_is_skipped():
    # 768 lies below the declared minimum window width, so no device can straddle it
    ok = expand([{'id': 'chat', 'axes': _axes(['900x600@2', '1024x700@2', '1920x1080@1'])}], THRESHOLDS, RANGE)
    assert len(ok) == 3


def test_orientation_changes_effective_width():
    # iPad 1024x768: portrait width 768 (< 1024), landscape width 1024 (>= 1024) → straddles with one device
    expand([{'id': 'home', 'axes': _axes(['1024x768@2'], ('portrait', 'landscape'))}],
           [{'width': 1024, 'basis': 'HomeView.swift:40 horizontalSizeClass'}])
    with pytest.raises(ValueError, match='misses layout threshold 1024'):
        expand([{'id': 'home', 'axes': _axes(['1024x768@2'], ('portrait',))}],
               [{'width': 1024, 'basis': 'HomeView.swift:40'}])


def test_named_devices_resolve_through_inventory_table():
    devices = {'iPhone SE (3rd generation)': {'width': 375, 'height': 667, 'scale': 2, 'basis': 'simctl devicetypes'},
               'iPad Pro 13-inch (M4)': {'width': 1032, 'height': 1376, 'scale': 2, 'basis': 'simctl devicetypes'}}
    t = [{'width': 600, 'basis': 'ContentView.swift:18 GeometryReader width > 600'}]
    expand([{'id': 'home', 'axes': _axes(list(devices), ('portrait',))}], t, devices=devices)
    with pytest.raises(ValueError, match='neither WxH@scale nor a mapped device'):
        expand([{'id': 'home', 'axes': _axes(['Pixel 8'], ('portrait',))}], t, devices=devices)


def test_surface_width_range_narrows_thresholds():
    # a desktop-only admin page declares its own range; the 768 threshold no longer applies to it
    admin = {'id': 'admin', 'width_range': {'min': 1200, 'max': 1920, 'basis': 'admin route gated to desktop'},
             'axes': _axes(['1200x800@2', '1920x1080@1'])}
    assert len(expand([admin], THRESHOLDS, RANGE)) == 2


def test_threshold_without_basis_is_refused():
    with pytest.raises(ValueError, match='invalid layout threshold'):
        expand([{'id': 'chat', 'axes': _axes(['700x500@2', '1920x1080@1'])}], [{'width': 768}])


def test_thresholds_do_not_change_case_ids():
    plain = expand([{'id': 'chat', 'axes': _axes(['700x500@2', '1920x1080@1'])}])[0]
    ruled = expand([{'id': 'chat', 'axes': _axes(['700x500@2', '1920x1080@1'])}], THRESHOLDS)[0]
    assert plain['id'] == ruled['id']


def test_fixed_width_window_ignores_orientation():
    # a Slide Over window is 320pt wide in both orientations; without the flag landscape would read 1376
    devices = {'iPad Pro 13 slide-over': {'width': 320, 'height': 1376, 'scale': 2, 'fixed_width': True,
                                          'basis': 'Slide Over on iPad Pro 13'}}
    t = [{'width': 700, 'basis': 'RootView.swift:15 horizontalSizeClass'}]
    with pytest.raises(ValueError, match='misses layout threshold 700'):
        expand([{'id': 'home', 'axes': _axes(list(devices), ('portrait', 'landscape'))}], t, devices=devices)
    devices['iPad Pro 13 slide-over']['fixed_width'] = False
    expand([{'id': 'home', 'axes': _axes(list(devices), ('portrait', 'landscape'))}], t, devices=devices)


LOCALES = {'supported': ['zh-CN', 'en', 'ja', 'de', 'ar'], 'default': 'zh-CN', 'rtl': ['ar'],
           'basis': 'next.config.js:i18n.locales'}


def _laxes(locales):
    return {**{a: ['default'] for a in AXES}, 'locale': list(locales)}


def test_locale_axis_must_cover_every_shipped_locale():
    with pytest.raises(ValueError, match='misses shipped locale en, ja, de, ar'):
        expand([{'id': 'home', 'axes': _laxes(['zh-CN'])}], locales=LOCALES)
    expand([{'id': 'home', 'axes': _laxes(['zh-CN', 'en', 'ja', 'de', 'ar'])}], locales=LOCALES)


def test_declined_locales_need_the_users_confirmation():
    declined = {**LOCALES, 'declined': [{'locale': 'de', 'confirmation': '用户 2026-09-07：德语区暂不上线'},
                                        {'locale': 'ar', 'confirmation': '用户 2026-09-07：阿语先不做'}]}
    expand([{'id': 'home', 'axes': _laxes(['zh-CN', 'en', 'ja'])}], locales=declined)
    bad = {**LOCALES, 'declined': [{'locale': 'de'}]}
    with pytest.raises(ValueError, match="needs a supported tag and the user's confirmation"):
        expand([{'id': 'home', 'axes': _laxes(['zh-CN', 'en', 'ja', 'ar'])}], locales=bad)
    unknown = {**LOCALES, 'declined': [{'locale': 'fr', 'confirmation': 'x'}]}
    with pytest.raises(ValueError):
        expand([{'id': 'home', 'axes': _laxes(['zh-CN', 'en', 'ja', 'de', 'ar'])}], locales=unknown)


def test_compound_locale_values_match_by_token():
    axes = _laxes(['浏览器 zh-CN', 'zh-CN + 站点 en', 'ja/站点 ja', 'de', 'ar'])
    expand([{'id': 'home', 'axes': axes}], locales=LOCALES)
    with pytest.raises(ValueError, match='misses shipped locale en'):
        expand([{'id': 'home', 'axes': _laxes(['zh-CN', 'english', 'ja', 'de', 'ar'])}], locales=LOCALES)


def test_surface_locale_scope_narrows_with_basis():
    admin = {'id': 'admin', 'locales': {'only': ['zh-CN', 'en'], 'basis': 'admin routes are not localized beyond en'},
             'axes': _laxes(['zh-CN', 'en'])}
    expand([admin], locales=LOCALES)
    with pytest.raises(ValueError, match='invalid surface locales scope'):
        expand([{**admin, 'locales': {'only': ['zh-CN', 'en']}}], locales=LOCALES)


def test_rtl_must_be_subset_of_supported_and_locales_need_basis():
    with pytest.raises(ValueError, match='rtl locale not in supported'):
        expand([{'id': 'home', 'axes': _laxes(['zh-CN'])}], locales={'supported': ['zh-CN'], 'rtl': ['ar'], 'basis': 'x'})
    with pytest.raises(ValueError, match='invalid locales'):
        expand([{'id': 'home', 'axes': _laxes(['zh-CN'])}], locales={'supported': ['zh-CN']})


APPEARANCE = {'supported': ['light', 'dark'], 'basis': 'tailwind.config.js darkMode: class; values-night/'}


def _axes_with(**over):
    return {**{a: ['default'] for a in AXES}, **{k: list(v) for k, v in over.items()}}


def test_generic_axis_support_requires_every_supported_value():
    with pytest.raises(ValueError, match='appearance axis misses supported value light'):
        expand([{'id': 'home', 'axes': _axes_with(appearance=['dark'])}], axis_support={'appearance': APPEARANCE})
    expand([{'id': 'home', 'axes': _axes_with(appearance=['light', 'dark'])}], axis_support={'appearance': APPEARANCE})


def test_generic_declined_values_with_confirmation():
    spec = {**APPEARANCE, 'declined': [{'value': 'light', 'confirmation': '用户 2026-09-07：我们只发深色'}]}
    expand([{'id': 'home', 'axes': _axes_with(appearance=['dark'])}], axis_support={'appearance': spec})
    with pytest.raises(ValueError, match="declined appearance needs a supported value"):
        expand([{'id': 'home', 'axes': _axes_with(appearance=['dark'])}],
               axis_support={'appearance': {**APPEARANCE, 'declined': [{'value': 'light'}]}})


def test_compound_values_match_by_segment():
    dt = {'supported': ['zoom 100%', 'zoom 150%'], 'basis': 'rem-based sizing'}
    expand([{'id': 'home', 'axes': _axes_with(dynamic_type=['zoom 100%', 'zoom 150% + 字号 20px'])}],
           axis_support={'dynamic_type': dt})
    with pytest.raises(ValueError, match='dynamic_type axis misses supported value zoom 150%'):
        expand([{'id': 'home', 'axes': _axes_with(dynamic_type=['zoom 100%', 'zoom 125%'])}],
               axis_support={'dynamic_type': dt})
    # system dark + in-app light is one value that carries both tokens; the readback check at capture
    # time is what decides which one it actually proves
    expand([{'id': 'home', 'axes': _axes_with(appearance=['system dark + app light', 'dark'])}],
           axis_support={'appearance': APPEARANCE})


def test_axis_scope_and_unknown_axis():
    scope = {'id': 'print', 'axis_scope': {'appearance': {'only': ['light'], 'basis': 'print preview is light-only'}},
             'axes': _axes_with(appearance=['light'])}
    expand([scope], axis_support={'appearance': APPEARANCE})
    with pytest.raises(ValueError, match='unknown axis'):
        expand([{'id': 'home', 'axes': _axes_with()}], axis_support={'theme': APPEARANCE})


def test_locales_and_axis_support_locale_cannot_both_be_declared():
    with pytest.raises(ValueError, match='declare the locale axis once'):
        expand([{'id': 'home', 'axes': _axes_with(locale=['zh-CN'])}], locales=LOCALES,
               axis_support={'locale': LOCALES})


def _big_axes():
    return {'state': ['default', 'empty', 'error'], 'device': ['1440x900@2', '390x844@3'],
            'os': ['Chromium 131'], 'appearance': ['light', 'dark'], 'dynamic_type': ['zoom 100%', 'zoom 150%'],
            'locale': ['zh-CN', 'en', 'ar'], 'orientation': ['landscape']}


ABS = [{'axis': 'locale', 'basis': 'locale only swaps strings; RTL kept coupled', 'confirmation': '用户 2026-09-07 确认',
        'keep_coupled': ['ar']},
       {'axis': 'dynamic_type', 'basis': 'rem sizing, no layout branches on zoom', 'confirmation': '用户确认'}]


def test_abstraction_keeps_ofat_slice_and_marks_the_rest():
    rows = expand([{'id': 'home', 'axes': _big_axes()}], abstractions=ABS)
    assert len(rows) == 3 * 2 * 2 * 2 * 3            # full product still emitted (72)
    kept = [r for r in rows if not r['abstracted_by']]
    # coupled part: state × device × appearance × {zh-CN, ar} at zoom 100%  = 3*2*2*2 = 24
    # plus one-factor variants crossed with state (default cross_with): en×3 states + zoom 150%×3 states
    assert len(kept) == 30
    en = [r for r in kept if r['locale'] == 'en']
    assert len(en) == 3 and {r['state'] for r in en} == {'default', 'empty', 'error'}
    assert all(r['appearance'] == 'light' and r['device'] == '1440x900@2' for r in en)
    ar_dark = [r for r in kept if r['locale'] == 'ar' and r['appearance'] == 'dark']
    assert len(ar_dark) == 3 * 2                    # RTL stays fully coupled
    crossed = next(r for r in rows if r['locale'] == 'en' and r['appearance'] == 'dark')
    assert crossed['abstracted_by'] == ['locale']
    both = next(r for r in rows if r['locale'] == 'en' and r['dynamic_type'] == 'zoom 150%')
    assert both['abstracted_by'] == ['dynamic_type', 'locale']


def test_abstraction_does_not_change_case_ids():
    plain = {r['id'] for r in expand([{'id': 'home', 'axes': _big_axes()}])}
    ruled = {r['id'] for r in expand([{'id': 'home', 'axes': _big_axes()}], abstractions=ABS)}
    assert plain == ruled


def test_abstraction_needs_basis_confirmation_and_valid_values():
    with pytest.raises(ValueError, match='invalid abstraction'):
        expand([{'id': 'home', 'axes': _big_axes()}], abstractions=[{'axis': 'locale', 'basis': 'x'}])
    with pytest.raises(ValueError, match='keep_coupled names a value not on the axis'):
        expand([{'id': 'home', 'axes': _big_axes()}],
               abstractions=[{'axis': 'locale', 'basis': 'x', 'confirmation': 'y', 'keep_coupled': ['fr']}])
    with pytest.raises(ValueError, match='anchor value not on the axis'):
        expand([{'id': 'home', 'axes': _big_axes()}], abstractions=ABS, anchor={'appearance': 'sepia'})


def test_cross_with_can_be_narrowed_or_widened():
    only_anchor = [{**ABS[0], 'cross_with': []}, ABS[1]]
    rows = expand([{'id': 'home', 'axes': _big_axes()}], abstractions=only_anchor)
    assert len([r for r in rows if r['locale'] == 'en' and not r['abstracted_by']]) == 1
    wide = [{**ABS[0], 'cross_with': ['state', 'device']}, ABS[1]]
    rows = expand([{'id': 'home', 'axes': _big_axes()}], abstractions=wide)
    assert len([r for r in rows if r['locale'] == 'en' and not r['abstracted_by']]) == 6
    with pytest.raises(ValueError, match='cross_with must list other axes'):
        expand([{'id': 'home', 'axes': _big_axes()}], abstractions=[{**ABS[0], 'cross_with': ['locale']}])


def test_anchor_can_be_chosen():
    rows = expand([{'id': 'home', 'axes': _big_axes()}], abstractions=ABS, anchor={'appearance': 'dark'})
    en = next(r for r in rows if r['locale'] == 'en' and not r['abstracted_by'])
    assert en['appearance'] == 'dark'


def test_web_platform_requires_scrollable_declaration():
    axes = {a: ['default'] for a in AXES}
    with pytest.raises(ValueError, match='web surface must declare scrollable'):
        expand([{'id': 'home', 'axes': axes}], platform='web')
    expand([{'id': 'home', 'scrollable': False, 'axes': axes}], platform='web')


def test_expand_inventory_reads_every_top_level_key():
    from matrix import expand_inventory
    axes = {a: ['default'] for a in AXES}
    inv = {'platform': 'web', 'surfaces': [{'id': 'home', 'axes': axes}]}
    with pytest.raises(ValueError, match='must declare scrollable'):
        expand_inventory(inv)
    inv['surfaces'][0]['scrollable'] = False
    inv['width_range'] = {'min': 1024, 'max': 1024, 'basis': 'x'}
    inv['surfaces'][0]['axes']['device'] = ['1440x900@2']
    with pytest.raises(ValueError, match='misses width range end'):
        expand_inventory(inv)
    inv['surfaces'][0]['axes']['device'] = ['1024x768@1']
    assert expand_inventory(inv) == expand(inv['surfaces'], width_range=inv['width_range'], platform='web')
