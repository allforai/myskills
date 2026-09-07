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
