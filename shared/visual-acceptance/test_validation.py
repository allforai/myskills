import hashlib
import json
from pathlib import Path

import pytest
from validation import AXES, CATEGORIES, visual_reason, visual_section
from matrix import expand
from PIL import Image


@pytest.fixture
def sample(tmp_path):
    def write(ref, obj):
        p = tmp_path / ref
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(obj))
        return hashlib.sha256(p.read_bytes()).hexdigest()
    (tmp_path / 'evidence/q1').mkdir(parents=True)
    image = tmp_path / 'evidence/q1/image.png'
    Image.new('RGB', (16, 16), 'white').save(image)
    image_hash = hashlib.sha256(image.read_bytes()).hexdigest()
    references = {'evidence/q1/image.png': image_hash}
    digest = write('visual/baseline.json', {'categories': {
        k: {'rules': ['approved'], 'confirmation': 'user approved', 'confirmed_at': '2026-09-06',
            'reference_images': references}
        for k in CATEGORIES}})
    cfg = {'facet_ids': ['F1'], 'baseline_status': 'confirmed',
           'baseline_ref': 'visual/baseline.json', 'baseline_digest': digest,
           'interaction_ref': 'visual/baseline.json', 'interaction_digest': digest,
           'review_mode': 'single', 'build': 'abc-clean',
           'inventory_ref': 'visual/inventory.json', 'matrix_ref': 'visual/matrix.json'}
    inventory = {'surfaces': [{'id': 'home', 'axes': {a: ['default'] for a in AXES}}]}
    case = expand(inventory['surfaces'])[0]
    cfg['inventory_digest'] = write(cfg['inventory_ref'], inventory)
    cfg['matrix_digest'] = write(cfg['matrix_ref'], [case])
    bound = {k: cfg[k] for k in ('build','baseline_digest','interaction_digest','inventory_digest','matrix_digest')}
    cap = {**case, 'case_id': case['id'], **bound, 'captured_at': 'now',
           'images': ['q1/image.png'], 'image_digests': {'q1/image.png': image_hash}}
    write('evidence/q1/manifest.json', {'captures': [cap]})
    report = {'platform': 'codex', 'session_id': 'fresh-1', 'independent': True,
              **bound, 'inspected_images': ['q1/image.png'],
              'image_digests': {'q1/image.png': image_hash}, 'reference_images': references,
              'status': 'passed', 'findings': []}
    write('evidence/q1/review.json', report)
    entry = {'facet': 'F1', 'verdict': 'done', 'medium': 'runtime', 'visual_case_ids': [case['id']],
             'evidence_manifest': 'q1/manifest.json', 'review_reports': ['q1/review.json']}
    ledger = {'visual_acceptance': cfg, 'visual_cases': [case]}
    return tmp_path, write, cfg, case, report, entry, ledger


def test_single(sample):
    root, _, _, _, _, entry, ledger = sample
    assert visual_reason(entry, ledger, root) is None


@pytest.mark.parametrize('change', ['unconfirmed', 'digest', 'code', 'missing', 'fake', 'escape', 'unseen', 'unknown', 'motion'])
def test_rejects_invalid_evidence(sample, change):
    root, write, cfg, case, report, entry, ledger = sample
    if change == 'unconfirmed': cfg['baseline_status'] = 'unconfirmed'
    if change == 'digest': cfg['baseline_digest'] = 'wrong'
    if change == 'code': entry['medium'] = 'code'
    if change == 'missing': (root / 'evidence/q1/image.png').unlink()
    if change == 'fake': (root / 'evidence/q1/image.png').write_text('not image')
    if change == 'escape': entry['evidence_manifest'] = '../../outside.json'
    if change == 'unseen':
        report['inspected_images'] = []
        write('evidence/q1/review.json', report)
    if change == 'unknown': entry['visual_case_ids'] = ['missing']
    if change == 'motion': case['motion'] = True
    assert visual_reason(entry, ledger, root)


def test_dual_union_and_degradation(sample):
    root, write, cfg, _, report, entry, ledger = sample
    cfg['review_mode'] = 'dual'
    report = {**report, 'platform': 'claude', 'session_id': 'fresh-2', 'status': 'findings',
              'findings': [{'id': 'R1', 'severity': 'medium', 'rule': 'color',
                            'observation': 'wrong color', 'images': ['q1/image.png']}]}
    write('evidence/q1/other.json', report)
    entry['review_reports'].append('q1/other.json')
    entry['reconciliation_ref'] = 'q1/reconciliation.json'
    write('evidence/q1/reconciliation.json', {'blocking_findings': [], 'disagreements': []})
    entry['verdict'] = 'gap'
    assert visual_reason(entry, ledger, root)
    write('evidence/q1/reconciliation.json', {'blocking_findings': ['fresh-2:R1'], 'disagreements': []})
    assert visual_reason(entry, ledger, root) is None
    entry['verdict'] = 'done'
    assert visual_reason(entry, ledger, root)
    entry['review_mode'] = 'dual_degraded'
    entry['review_reports'] = ['q1/review.json']
    assert visual_reason(entry, ledger, root)
    entry['degradation_ref'] = 'q1/failure.json'
    write('evidence/q1/failure.json', {'platform': 'claude', 'attempts': [
        {'reason': 'failed', 'attempted_at': 'first'}, {'reason': 'failed', 'attempted_at': 'retry'}]})
    assert visual_reason(entry, ledger, root) is None


def test_unprovable_and_coverage(sample):
    root, write, cfg, case, _, entry, ledger = sample
    cfg['baseline_status'] = 'unconfirmed'
    entry['verdict'] = 'unprovable'
    entry['visual_failure_ref'] = 'q1/failure.json'
    write('evidence/q1/failure.json', {'reason': 'cannot launch'})
    assert visual_reason(entry, ledger, root) is None
    ledger['visual_cases'] += [{**case, 'id': 'V2'}, {**case, 'id': 'V3',
        'applicability': 'not_applicable', 'reason': 'unsupported', 'basis': 'confirmed scope'}]
    out = '\n'.join(visual_section(ledger, [entry]))
    assert 'unprovable: 1' in out and 'not_examined: 1' in out and 'not_applicable: 1' in out


def test_old_ledger():
    assert visual_reason({'verdict': 'done'}, {}, Path('.')) is None
    assert visual_section({}, []) == []


@pytest.mark.parametrize('change,reason', [
    ('old_build', '证据绑定不匹配: build'),
    ('changed_interaction', '证据绑定不匹配: interaction_digest'),
    ('silent_single', '禁止静默变更审查模式'),
    ('reviewer_old_image', 'reviewer 图片内容绑定不匹配'),
    ('missing_references', '缺可解码的参考图片'),
])
def test_thought_test_regressions(sample, change, reason):
    root, write, cfg, _, report, entry, ledger = sample
    if change == 'old_build':
        cfg['build'] = 'new-build'
    elif change == 'changed_interaction':
        cfg['interaction_ref'] = 'visual/interaction-new.json'
        cfg['interaction_digest'] = write(cfg['interaction_ref'], {'categories': {}})
    elif change == 'silent_single':
        cfg['review_mode'] = 'dual'
        entry['review_mode'] = 'single'
    elif change == 'reviewer_old_image':
        report['image_digests']['q1/image.png'] = 'old-content'
        write('evidence/q1/review.json', report)
    else:
        data = json.loads((root / cfg['baseline_ref']).read_text())
        for value in data['categories'].values(): value['reference_images'] = {}
        cfg['baseline_digest'] = cfg['interaction_digest'] = write(cfg['baseline_ref'], data)
    assert reason in visual_reason(entry, ledger, root)


def test_header_only_image_rejected_by_decoder(sample):
    root, _, _, _, _, entry, ledger = sample
    (root / 'evidence/q1/image.png').write_bytes(b'\x89PNG\r\n\x1a\n')
    assert visual_reason(entry, ledger, root)


def test_frozen_matrix_omission_is_visible(sample):
    root, write, cfg, case, report, entry, ledger = sample
    inv = json.loads((root / cfg['inventory_ref']).read_text())
    inv['surfaces'].append({'id': 'settings', 'axes': {a:['default'] for a in AXES}})
    cfg['inventory_digest'] = write(cfg['inventory_ref'], inv)
    cfg['matrix_digest'] = write(cfg['matrix_ref'], expand(inv['surfaces']))
    assert '完整矩阵不一致' in visual_reason(entry, ledger, root)
    out = '\n'.join(visual_section(ledger, [], root))
    assert 'settings' in out and 'not_examined: 2' in out


def test_frozen_matrix_itself_cannot_drop_a_surface(sample):
    root, write, cfg, _, _, entry, ledger = sample
    inv = json.loads((root / cfg['inventory_ref']).read_text())
    inv['surfaces'].append({'id':'settings','axes':{a:['default'] for a in AXES}})
    cfg['inventory_digest'] = write(cfg['inventory_ref'], inv)
    assert '未覆盖完整页面清单' in visual_reason(entry, ledger, root)


@pytest.mark.parametrize('bad', ['repeated_path', 'same_pixels', 'reencoded_pixels', 'missing_time', 'reversed_time', 'nan_time', 'negative_time',
                                 'missing_recording', 'recording_digest', 'recording_is_frame', 'reviewer_skipped_recording',
                                 'reviewer_unreadable_done', 'reviewer_unreadable_gap', None])
def test_dynamic_frames(sample, bad):
    root, write, cfg, case, report, entry, ledger = sample
    inv = json.loads((root / cfg['inventory_ref']).read_text())
    inv['surfaces'][0]['motion_states'] = ['default']
    case['motion'] = True
    cfg['inventory_digest'] = write(cfg['inventory_ref'], inv)
    cfg['matrix_digest'] = write(cfg['matrix_ref'], [case])
    cap = json.loads((root / 'evidence/q1/manifest.json').read_text())['captures'][0]
    Image.new('RGB', (16,16), 'white' if bad in {'same_pixels', 'reencoded_pixels'} else 'black').save(root/'evidence/q1/frame2.png', compress_level=0 if bad == 'reencoded_pixels' else 6)
    cap['images'].append('q1/image.png' if bad == 'repeated_path' else 'q1/frame2.png')
    cap['image_digests']['q1/frame2.png'] = hashlib.sha256((root/'evidence/q1/frame2.png').read_bytes()).hexdigest()
    cap['frame_times_ms'] = [] if bad == 'missing_time' else [200,100] if bad == 'reversed_time' else [0,200]
    if bad == 'nan_time': cap['frame_times_ms'] = [0, float('nan')]
    if bad == 'negative_time': cap['frame_times_ms'] = [-100, 0]
    for key in ('matrix_digest','inventory_digest'):
        cap[key] = report[key] = cfg[key]
    clip = root / 'evidence/q1/clip.mov'
    clip.write_bytes(b'not really a movie but non-empty')
    cap['recording'] = 'q1/clip.mov'
    cap['recording_digest'] = hashlib.sha256(clip.read_bytes()).hexdigest()
    if bad == 'missing_recording': del cap['recording']
    if bad == 'recording_digest': cap['recording_digest'] = 'f' * 64
    if bad == 'recording_is_frame': cap['recording'] = 'q1/frame2.png'
    report['inspected_images'] = cap['images']
    report['image_digests'] = cap['image_digests']
    unreadable = bad in {'reviewer_unreadable_done', 'reviewer_unreadable_gap'}
    report['inspected_recordings'] = [] if bad == 'reviewer_skipped_recording' or unreadable else ['q1/clip.mov']
    if unreadable: report['recording_unreadable'] = 'codex exec 无视频读取工具，只审了帧序列'
    if bad == 'reviewer_unreadable_gap':
        report['status'] = 'findings'
        report['findings'] = [{'id': 'M1', 'severity': 'medium', 'rule': 'motion', 'observation': '帧 2 与帧 3 之间 Sheet 位置跳变', 'images': ['q1/frame2.png']}]
        entry['verdict'] = 'gap'
    write('evidence/q1/manifest.json', {'captures':[cap]})
    write('evidence/q1/review.json', report)
    reason = visual_reason(entry, ledger, root)
    if bad in {None, 'reviewer_unreadable_gap'}: assert reason is None
    elif bad == 'reviewer_unreadable_done': assert reason and '录屏无人审阅' in reason
    elif bad in {'missing_recording', 'recording_digest', 'recording_is_frame'}: assert reason and '录屏' in reason
    elif bad == 'reviewer_skipped_recording': assert reason and '未审阅录屏' in reason
    else: assert reason and ('动态' in reason or '重复截图' in reason)


def test_renderer_rejects_visual_done_without_images(sample):
    import importlib.util
    root, write, _, _, _, entry, ledger = sample
    repo = next((p for p in Path(__file__).resolve().parents if (p / 'codex/cross-exam-skill').is_dir()), None)
    if repo is None:
        pytest.skip('repository integration test')
    for relative in ('codex/cross-exam-skill/scripts/render_report.py', 'claude/superstorm/scripts/render_report.py'):
        spec = importlib.util.spec_from_file_location('visual_renderer_test', repo / relative)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        entry.update(q='visual question', evidence={'dir': 'evidence/q1', 'key_observation': 'observed'})
        ledger.update(target='fixture', baseline='user', facets=[{'id':'F1','name':'visual','status':'examined'}], entries=[entry])
        write('ledger.json', ledger)
        assert 'done: 1' in module.render(root)
        image = root / 'evidence/q1/image.png'
        data = image.read_bytes()
        image.unlink()
        report = module.render(root)
        assert '违规裁决' in report and 'not_examined: 1' in report
        image.write_bytes(data)


def test_blocking_findings_scoped_to_entry_images(sample):
    # 一批两个用例共用一份报告；high 只指向 error 图 → default 用例的 entry 可 done，error 用例的不可。
    root, write, cfg, _, report, entry, ledger = sample
    inventory = {'surfaces': [{'id': 'home', 'axes': {**{a: ['default'] for a in AXES},
                                                     'state': ['default', 'error']}}]}
    cases = expand(inventory['surfaces'])
    cfg['inventory_digest'] = write(cfg['inventory_ref'], inventory)
    cfg['matrix_digest'] = write(cfg['matrix_ref'], cases)
    ledger['visual_cases'] = cases
    bound = {k: cfg[k] for k in ('build', 'baseline_digest', 'interaction_digest', 'inventory_digest', 'matrix_digest')}
    ok, bad = cases
    error_image = root / 'evidence/q1/error.png'
    Image.new('RGB', (16, 16), 'red').save(error_image)
    hashes = {'q1/image.png': report['image_digests']['q1/image.png'],
              'q1/error.png': hashlib.sha256(error_image.read_bytes()).hexdigest()}
    write('evidence/q1/manifest.json', {'captures': [
        {**ok, 'case_id': ok['id'], **bound, 'captured_at': 'now',
         'images': ['q1/image.png'], 'image_digests': {'q1/image.png': hashes['q1/image.png']}},
        {**bad, 'case_id': bad['id'], **bound, 'captured_at': 'now',
         'images': ['q1/error.png'], 'image_digests': {'q1/error.png': hashes['q1/error.png']}}]})
    shared = {**report, **bound, 'status': 'findings', 'inspected_images': list(hashes), 'image_digests': hashes,
              'findings': [{'id': 'R1', 'severity': 'high', 'rule': 'color',
                            'observation': 'bad contrast', 'images': ['q1/error.png']}]}
    write('evidence/q1/review.json', shared)
    good = {**entry, 'visual_case_ids': [ok['id']], 'verdict': 'done'}
    tainted = {**entry, 'visual_case_ids': [bad['id']], 'verdict': 'done'}
    assert visual_reason(good, ledger, root) is None
    assert '阻断' in visual_reason(tainted, ledger, root)
    assert visual_reason({**tainted, 'verdict': 'gap'}, ledger, root) is None
    # finding 指向 reviewer 没打开过的图片仍然非法
    write('evidence/q1/review.json', {**shared, 'findings': [{**shared['findings'][0], 'images': ['q1/ghost.png']}]})
    assert '发现引用' in visual_reason(good, ledger, root)


def test_not_applicable_rows_survive_frozen_comparison(sample):
    # 文档要求不适用行加 applicability/reason/basis；这不能让整个 run 的视觉 entry 被拒
    root, write, cfg, _, report, entry, ledger = sample
    inventory = {'surfaces': [{'id': 'home', 'axes': {**{a: ['default'] for a in AXES},
                                                     'state': ['default', 'landscape-only']}}]}
    cases = expand(inventory['surfaces'])
    cfg['inventory_digest'] = write(cfg['inventory_ref'], inventory)
    cfg['matrix_digest'] = write(cfg['matrix_ref'], cases)
    tested, skipped = cases
    ledger['visual_cases'] = [tested, {**skipped, 'applicability': 'not_applicable',
                                        'reason': 'iPhone 不支持横屏', 'basis': 'Info.plist UISupportedInterfaceOrientations'}]
    bound = {k: cfg[k] for k in ('build', 'baseline_digest', 'interaction_digest', 'inventory_digest', 'matrix_digest')}
    write('evidence/q1/manifest.json', {'captures': [
        {**tested, 'case_id': tested['id'], **bound, 'captured_at': 'now',
         'images': ['q1/image.png'], 'image_digests': report['image_digests']}]})
    write('evidence/q1/review.json', {**report, **bound})
    done = {**entry, 'visual_case_ids': [tested['id']], 'verdict': 'done'}
    assert visual_reason(done, ledger, root) is None
    section = '\n'.join(visual_section(ledger, [done], root))
    assert 'not_applicable: 1' in section and 'done: 1' in section
    # 多出三个键之外的字段仍算矩阵不一致
    ledger['visual_cases'][1]['extra'] = 'x'
    assert '冻结完整矩阵不一致' in visual_reason(done, ledger, root)


def test_category_confirmed_with_reason_only(sample):
    root, write, cfg, _, _, entry, ledger = sample
    baseline = json.loads((root / cfg['baseline_ref']).read_text())
    baseline['categories']['motion'] = {'rules': [], 'reason': 'App 无动画', 'confirmation': 'user confirmed n/a',
                                        'confirmed_at': '2026-09-06', 'reference_images': {}}
    cfg['baseline_digest'] = cfg['interaction_digest'] = write(cfg['baseline_ref'], baseline)
    for ref in ('evidence/q1/manifest.json', 'evidence/q1/review.json'):
        obj = json.loads((root / ref).read_text())
        for holder in obj.get('captures', [obj]):
            holder['baseline_digest'] = holder['interaction_digest'] = cfg['baseline_digest']
        write(ref, obj)
    assert visual_reason(entry, ledger, root) is None
    baseline['categories']['motion']['reason'] = ''
    cfg['baseline_digest'] = cfg['interaction_digest'] = write(cfg['baseline_ref'], baseline)
    assert '基线缺逐类确认: motion' in visual_reason(entry, ledger, root)


def test_corrupt_png_is_refused_not_raised(sample):
    root, _, _, _, _, entry, ledger = sample
    image = root / 'evidence/q1/image.png'
    data = bytearray(image.read_bytes())
    data[-8] ^= 0xFF          # 破坏 IEND/IDAT 附近的 CRC
    image.write_bytes(bytes(data))
    reason = visual_reason(entry, ledger, root)
    assert reason and '图片无法解码' in reason


def test_malformed_visual_fields_do_not_crash(sample):
    root, _, _, case, _, entry, ledger = sample
    plain = {'facet': 'F9', 'verdict': 'done', 'q': 'x'}
    assert visual_reason(plain, {'visual_acceptance': {'facet_ids': None}}, root) is None
    assert visual_reason(plain, {'visual_acceptance': 'F1'}, root) is None
    assert '视觉用例引用无效' in visual_reason({**entry, 'visual_case_ids': None}, ledger, root)
    # facet_ids 写成字符串按单个 facet 处理，不做子串匹配
    assert visual_reason({'facet': 'F', 'verdict': 'done'}, {'visual_acceptance': {'facet_ids': 'F1'}}, root) is None
    assert '视觉用例引用无效' in visual_reason({'facet': 'F1', 'verdict': 'done'}, {'visual_acceptance': {'facet_ids': 'F1'}}, root)
    broken = {'visual_acceptance': {'facet_ids': ['F1']}, 'visual_cases': [{'surface': 'home'}, 'junk']}
    text = '\n'.join(visual_section(broken, [{**entry, 'visual_case_ids': None, 'verdict': 'done'}], run=None))
    assert '（无 id）' in text


def test_renderers_load_their_own_mirror_validation():
    import importlib.util
    repo = next((p for p in Path(__file__).resolve().parents if (p / 'codex/cross-exam-skill').is_dir()), None)
    if repo is None:
        pytest.skip('repository integration test')
    for relative, mirror in (('codex/cross-exam-skill/scripts/render_report.py', 'codex/cross-exam-skill/visual'),
                             ('claude/superstorm/scripts/render_report.py', 'claude/superstorm/knowledge/cross-exam/visual')):
        spec = importlib.util.spec_from_file_location('visual_renderer_probe', repo / relative)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        loaded = Path(module.visual_reason.__code__.co_filename).resolve()
        assert loaded == (repo / mirror / 'validation.py').resolve(), loaded
        assert module.visual_reason.__module__ == 'cross_exam_visual_validation'


def test_verified_images_are_decoded_once_per_content(sample, monkeypatch):
    import PIL.Image
    from validation import image_digest, _VERIFIED_IMAGES
    root = sample[0]
    image = root / 'evidence/q1/image.png'
    _VERIFIED_IMAGES.discard(hashlib.sha256(image.read_bytes()).hexdigest())
    opened = []
    real_open = PIL.Image.open
    monkeypatch.setattr(PIL.Image, 'open', lambda *a, **k: (opened.append(a[0]), real_open(*a, **k))[1])
    first = image_digest(image)
    assert image_digest(image) == first and image_digest(image) == first
    assert len(opened) == 2          # verify() + load() on the first call only
    # changed bytes are decoded again
    Image.new('RGB', (16, 16), 'blue').save(image)
    assert image_digest(image) != first
    assert len(opened) == 4


def test_comparison_group_must_not_be_split_across_entries(sample):
    root, write, cfg, _, report, entry, ledger = sample
    axes = {a: ['default'] for a in AXES}
    inventory = {'surfaces': [{'id': 'home', 'axes': axes, 'groups': ['buttons']},
                              {'id': 'settings', 'axes': axes, 'groups': ['buttons']},
                              {'id': 'about', 'axes': axes}]}
    cases = expand(inventory['surfaces'])
    cfg['inventory_digest'] = write(cfg['inventory_ref'], inventory)
    cfg['matrix_digest'] = write(cfg['matrix_ref'], cases)
    ledger['visual_cases'] = cases
    bound = {k: cfg[k] for k in ('build', 'baseline_digest', 'interaction_digest', 'inventory_digest', 'matrix_digest')}
    home, settings, about = cases
    shot = root / 'evidence/q1/settings.png'
    Image.new('RGB', (16, 16), 'green').save(shot)
    hashes = {'q1/image.png': report['image_digests']['q1/image.png'],
              'q1/settings.png': hashlib.sha256(shot.read_bytes()).hexdigest()}
    write('evidence/q1/manifest.json', {'captures': [
        {**home, 'case_id': home['id'], **bound, 'captured_at': 'now', 'images': ['q1/image.png'],
         'image_digests': {'q1/image.png': hashes['q1/image.png']}},
        {**settings, 'case_id': settings['id'], **bound, 'captured_at': 'now', 'images': ['q1/settings.png'],
         'image_digests': {'q1/settings.png': hashes['q1/settings.png']}},
        {**about, 'case_id': about['id'], **bound, 'captured_at': 'now', 'images': ['q1/image.png'],
         'image_digests': {'q1/image.png': hashes['q1/image.png']}}]})
    write('evidence/q1/review.json', {**report, **bound, 'inspected_images': list(hashes), 'image_digests': hashes})
    alone = {**entry, 'visual_case_ids': [home['id']], 'verdict': 'done'}
    assert '比较组被拆开' in visual_reason(alone, ledger, root) and 'settings' in visual_reason(alone, ledger, root)
    together = {**entry, 'visual_case_ids': [home['id'], settings['id']], 'verdict': 'done'}
    assert visual_reason(together, ledger, root) is None
    ungrouped = {**entry, 'visual_case_ids': [about['id']], 'verdict': 'done'}
    assert visual_reason(ungrouped, ledger, root) is None


def _scroll_case(sample, write, capture_extra):
    """Rebuild the frozen matrix around a single scroll-state case and one capture for it."""
    root, _, cfg, case, report, entry, ledger = sample
    inventory = {'surfaces': [{'id': 'feed', 'scrollable': True,
                               'axes': {**{a: ['default'] for a in AXES}, 'state': ['scroll-bottom']}}]}
    scase = expand(inventory['surfaces'])[0]
    cfg['inventory_digest'] = write(cfg['inventory_ref'], inventory)
    cfg['matrix_digest'] = write(cfg['matrix_ref'], [scase])
    bound = {k: cfg[k] for k in ('build','baseline_digest','interaction_digest','inventory_digest','matrix_digest')}
    image_hash = report['image_digests']['q1/image.png']
    cap = {**scase, 'case_id': scase['id'], **bound, 'captured_at': 'now',
           'images': ['q1/image.png'], 'image_digests': {'q1/image.png': image_hash}, **capture_extra}
    write('evidence/q1/manifest.json', {'captures': [cap]})
    write('evidence/q1/review.json', {**report, **bound})
    entry['visual_case_ids'] = [scase['id']]
    ledger['visual_cases'] = [scase]
    return root, entry, ledger


PROFILE = {'scroll_width': 1440, 'client_width': 1425, 'scroll_height': 4200, 'client_height': 900,
           'gutter_px': 15, 'overflow_x': 'visible', 'overflow_y': 'auto', 'nested_scrollers': []}


@pytest.mark.parametrize('extra', [
    {},                                                                    # 旧式 capture，没声明模式
    {'capture_mode': 'full_page', 'headless': True, 'scrollbars': 'hidden', 'scroll_profile': PROFILE},
    {'capture_mode': 'viewport', 'headless': True, 'scrollbars': 'hidden', 'scroll_profile': PROFILE},
    {'capture_mode': 'viewport', 'headless': False, 'scrollbars': 'native'},   # 缺 scroll_profile
])
def test_scroll_state_refuses_headless_full_page(sample, extra):
    root, write = sample[0], sample[1]
    root, entry, ledger = _scroll_case(sample, write, extra)
    assert '滚动态用例须视口截图' in visual_reason(entry, ledger, root)


def test_scroll_state_accepts_viewport_native_capture(sample):
    root, write = sample[0], sample[1]
    root, entry, ledger = _scroll_case(sample, write, {
        'capture_mode': 'viewport', 'headless': False, 'scrollbars': 'native',
        'scroll_profile': PROFILE, 'capture_tool': 'playwright headed'})
    assert visual_reason(entry, ledger, root) is None


def test_non_scroll_case_still_accepts_full_page(sample):
    root, write, cfg, case, report, entry, ledger = sample
    manifest = json.loads((root / 'evidence/q1/manifest.json').read_text())
    manifest['captures'][0].update({'capture_mode': 'full_page', 'headless': True, 'scrollbars': 'hidden'})
    write('evidence/q1/manifest.json', manifest)
    assert visual_reason(entry, ledger, root) is None


def test_invalid_capture_mode_is_refused(sample):
    root, write, cfg, case, report, entry, ledger = sample
    manifest = json.loads((root / 'evidence/q1/manifest.json').read_text())
    manifest['captures'][0]['capture_mode'] = 'fullscreen'
    write('evidence/q1/manifest.json', manifest)
    assert '截图模式无效' in visual_reason(entry, ledger, root)


def test_frozen_inventory_thresholds_are_enforced_on_replay(sample):
    """An inventory that declares layout thresholds its device axis cannot straddle is refused at
    validation time too — freezing a bad matrix does not launder it."""
    root, write, cfg, case, report, entry, ledger = sample
    inventory = json.loads((root / cfg['inventory_ref']).read_text())
    inventory['layout_thresholds'] = [{'width': 1024, 'basis': 'tailwind.config.js:5'}]
    inventory['surfaces'][0]['axes']['device'] = ['1512x982@2']
    cfg['inventory_digest'] = write(cfg['inventory_ref'], inventory)
    assert 'misses layout threshold 1024' in visual_reason(entry, ledger, root)


def _locale_case(sample, write, locale, capture_extra, locales):
    root, _, cfg, case, report, entry, ledger = sample
    inventory = {'locales': locales,
                 'surfaces': [{'id': 'home', 'axes': {**{a: ['default'] for a in AXES}, 'locale': [locale]}}]}
    lcase = expand(inventory['surfaces'], locales=locales)[0]
    cfg['inventory_digest'] = write(cfg['inventory_ref'], inventory)
    cfg['matrix_digest'] = write(cfg['matrix_ref'], [lcase])
    bound = {k: cfg[k] for k in ('build','baseline_digest','interaction_digest','inventory_digest','matrix_digest')}
    image_hash = report['image_digests']['q1/image.png']
    cap = {**lcase, 'case_id': lcase['id'], **bound, 'captured_at': 'now',
           'images': ['q1/image.png'], 'image_digests': {'q1/image.png': image_hash}, **capture_extra}
    write('evidence/q1/manifest.json', {'captures': [cap]})
    write('evidence/q1/review.json', {**report, **bound})
    entry['visual_case_ids'] = [lcase['id']]
    ledger['visual_cases'] = [lcase]
    return root, entry, ledger


AR = {'supported': ['ar'], 'default': 'ar', 'rtl': ['ar'], 'basis': 'Localizable.xcstrings'}


def test_rtl_case_requires_direction_read_back(sample):
    root, write = sample[0], sample[1]
    root, entry, ledger = _locale_case(sample, write, 'ar', {'readback': {'locale': 'ar'}}, AR)
    assert 'RTL 语言用例须读回 direction=rtl' in visual_reason(entry, ledger, root)
    root, entry, ledger = _locale_case(sample, write, 'ar', {'readback': {'locale': 'ar', 'direction': 'rtl'}}, AR)
    assert visual_reason(entry, ledger, root) is None
    root, entry, ledger = _locale_case(sample, write, 'ar', {'readback': {'direction': 'rtl'}}, AR)
    assert 'locale 轴缺应用内读回值' in visual_reason(entry, ledger, root)


def test_declined_locales_are_declared_in_the_visual_section(sample):
    root, write, cfg, case, report, entry, ledger = sample
    inventory = json.loads((root / cfg['inventory_ref']).read_text())
    inventory['locales'] = {'supported': ['zh-CN', 'de'], 'basis': 'i18n.ts',
                            'declined': [{'locale': 'de', 'confirmation': '用户 2026-09-07：德语区暂不上线'}]}
    inventory['surfaces'][0]['axes']['locale'] = ['zh-CN']
    cfg['inventory_digest'] = write(cfg['inventory_ref'], inventory)
    lcase = expand(inventory['surfaces'], locales=inventory['locales'])[0]
    cfg['matrix_digest'] = write(cfg['matrix_ref'], [lcase])
    ledger['visual_cases'] = [lcase]
    section = '\n'.join(visual_section(ledger, [], root))
    assert '未验收语言（用户确认放弃，不进任何计数）：de — 用户 2026-09-07：德语区暂不上线' in section


def test_inventory_cannot_drop_a_census_locale(sample):
    root, write, cfg, case, report, entry, ledger = sample
    ledger['locales'] = {'supported': ['zh-CN', 'de'], 'basis': 'i18n.ts'}     # census, verbatim
    inventory = json.loads((root / cfg['inventory_ref']).read_text())
    inventory['locales'] = {'supported': ['zh-CN'], 'basis': 'i18n.ts'}        # de silently removed
    inventory['surfaces'][0]['axes']['locale'] = ['zh-CN']
    cfg['inventory_digest'] = write(cfg['inventory_ref'], inventory)
    lcase = expand(inventory['surfaces'], locales=inventory['locales'])[0]
    cfg['matrix_digest'] = write(cfg['matrix_ref'], [lcase])
    ledger['visual_cases'] = [lcase]
    entry['visual_case_ids'] = [lcase['id']]
    manifest = json.loads((root / 'evidence/q1/manifest.json').read_text())
    manifest['captures'][0].update({**lcase, 'case_id': lcase['id'], 'inventory_digest': cfg['inventory_digest'],
                                    'matrix_digest': cfg['matrix_digest']})
    write('evidence/q1/manifest.json', manifest)
    assert '删掉了普查官列出的语言: de' in visual_reason(entry, ledger, root)


def _support_case(sample, write, axis, value, axis_support, capture_extra):
    root, _, cfg, case, report, entry, ledger = sample
    inventory = {'axis_support': axis_support,
                 'surfaces': [{'id': 'home', 'axes': {**{a: ['default'] for a in AXES}, axis: [value]}}]}
    scase = expand(inventory['surfaces'], axis_support=axis_support)[0]
    cfg['inventory_digest'] = write(cfg['inventory_ref'], inventory)
    cfg['matrix_digest'] = write(cfg['matrix_ref'], [scase])
    bound = {k: cfg[k] for k in ('build','baseline_digest','interaction_digest','inventory_digest','matrix_digest')}
    image_hash = report['image_digests']['q1/image.png']
    cap = {**scase, 'case_id': scase['id'], **bound, 'captured_at': 'now',
           'images': ['q1/image.png'], 'image_digests': {'q1/image.png': image_hash}, **capture_extra}
    write('evidence/q1/manifest.json', {'captures': [cap]})
    write('evidence/q1/review.json', {**report, **bound})
    entry['visual_case_ids'] = [scase['id']]
    ledger['visual_cases'] = [scase]
    return root, entry, ledger


DARK = {'appearance': {'supported': ['dark'], 'basis': 'values-night/',
                       'declined': []}}


def test_supported_axis_requires_in_app_readback(sample):
    root, write = sample[0], sample[1]
    root, entry, ledger = _support_case(sample, write, 'appearance', 'dark', DARK, {})
    assert 'appearance 轴缺应用内读回值' in visual_reason(entry, ledger, root)
    root, entry, ledger = _support_case(sample, write, 'appearance', 'dark', DARK, {'readback': {'appearance': 'light'}})
    assert 'appearance 轴读回值 light 与用例 dark 不符' in visual_reason(entry, ledger, root)
    root, entry, ledger = _support_case(sample, write, 'appearance', 'dark', DARK, {'readback': {'appearance': 'dark'}})
    assert visual_reason(entry, ledger, root) is None


def test_compound_case_value_is_proven_by_its_readback(sample):
    root, write = sample[0], sample[1]
    both = {'appearance': {'supported': ['light', 'dark'], 'basis': 'darkMode: class',
                           'declined': [{'value': 'light', 'confirmation': 'x'}]}}
    root, entry, ledger = _support_case(sample, write, 'appearance', 'system dark + app light', both,
                                        {'readback': {'appearance': 'light'}})
    assert visual_reason(entry, ledger, root) is None
    root, entry, ledger = _support_case(sample, write, 'appearance', 'system dark + app light', both,
                                        {'readback': {'appearance': 'sepia'}})
    assert '与用例' in visual_reason(entry, ledger, root)


def test_declined_axis_values_are_declared_in_the_visual_section(sample):
    root, write, cfg, case, report, entry, ledger = sample
    inventory = json.loads((root / cfg['inventory_ref']).read_text())
    inventory['axis_support'] = {'appearance': {'supported': ['light', 'dark'], 'basis': 'darkMode: class',
                                                'declined': [{'value': 'dark', 'confirmation': '用户：深色下版再验'}]}}
    inventory['surfaces'][0]['axes']['appearance'] = ['light']
    cfg['inventory_digest'] = write(cfg['inventory_ref'], inventory)
    scase = expand(inventory['surfaces'], axis_support=inventory['axis_support'])[0]
    cfg['matrix_digest'] = write(cfg['matrix_ref'], [scase])
    ledger['visual_cases'] = [scase]
    section = '\n'.join(visual_section(ledger, [], root))
    assert '未验收 appearance 值（用户确认放弃，不进任何计数）：dark — 用户：深色下版再验' in section


def test_inventory_cannot_drop_a_census_axis_value(sample):
    root, write, cfg, case, report, entry, ledger = sample
    ledger['axis_support'] = {'appearance': {'supported': ['light', 'dark'], 'basis': 'values-night/'}}
    inventory = json.loads((root / cfg['inventory_ref']).read_text())
    inventory['axis_support'] = {'appearance': {'supported': ['dark'], 'basis': 'values-night/'}}   # light removed
    inventory['surfaces'][0]['axes']['appearance'] = ['dark']
    cfg['inventory_digest'] = write(cfg['inventory_ref'], inventory)
    scase = expand(inventory['surfaces'], axis_support=inventory['axis_support'])[0]
    cfg['matrix_digest'] = write(cfg['matrix_ref'], [scase])
    ledger['visual_cases'] = [scase]
    entry['visual_case_ids'] = [scase['id']]
    manifest = json.loads((root / 'evidence/q1/manifest.json').read_text())
    manifest['captures'][0].update({**scase, 'case_id': scase['id'], 'inventory_digest': cfg['inventory_digest'],
                                    'matrix_digest': cfg['matrix_digest'], 'readback': {'appearance': 'dark'}})
    write('evidence/q1/manifest.json', manifest)
    assert '删掉了普查官列出的appearance 值: light' in visual_reason(entry, ledger, root)


def test_web_platform_captures_need_mode_fields(sample):
    root, write, cfg, case, report, entry, ledger = sample
    inventory = json.loads((root / cfg['inventory_ref']).read_text())
    inventory['platform'] = 'web'
    inventory['form_factor'] = 'mobile'
    inventory['surfaces'][0]['scrollable'] = False
    cfg['inventory_digest'] = write(cfg['inventory_ref'], inventory)
    scase = expand(inventory['surfaces'], platform='web', form_factor='mobile')[0]
    cfg['matrix_digest'] = write(cfg['matrix_ref'], [scase])
    ledger['visual_cases'] = [scase]
    manifest = json.loads((root / 'evidence/q1/manifest.json').read_text())
    manifest['captures'][0].update({'inventory_digest': cfg['inventory_digest'], 'matrix_digest': cfg['matrix_digest']})
    write('evidence/q1/manifest.json', manifest)
    assert 'Web capture 缺 capture_mode, headless, scrollbars, scroll_profile, capture_tool' in visual_reason(entry, ledger, root)
    manifest['captures'][0].update({'capture_mode': 'viewport', 'headless': False, 'scrollbars': 'native',
                                    'scroll_profile': {}, 'capture_tool': 'playwright headed'})
    write('evidence/q1/manifest.json', manifest)
    write('evidence/q1/review.json', {**report, 'inventory_digest': cfg['inventory_digest'],
                                      'matrix_digest': cfg['matrix_digest']})
    assert visual_reason(entry, ledger, root) is None


def test_abstracted_cases_are_counted_apart_and_doubted_on_gap(sample):
    root, write, cfg, case, report, entry, ledger = sample
    inventory = json.loads((root / cfg['inventory_ref']).read_text())
    inventory['surfaces'][0]['axes']['locale'] = ['zh-CN', 'en']
    inventory['surfaces'][0]['axes']['appearance'] = ['light', 'dark']
    inventory['abstractions'] = [{'axis': 'locale', 'basis': 'strings only', 'confirmation': '用户确认'}]
    cfg['inventory_digest'] = write(cfg['inventory_ref'], inventory)
    rows = expand(inventory['surfaces'], abstractions=inventory['abstractions'])
    cfg['matrix_digest'] = write(cfg['matrix_ref'], rows)
    ledger['visual_cases'] = rows
    section = '\n'.join(visual_section(ledger, [], root))
    assert 'abstracted: 1' in section                       # en × dark is the crossed case
    assert '已抽象（locale）' in section
    assert '逐轴覆盖' in section and 'locale：' in section
    en_kept = next(r for r in rows if r['locale'] == 'en' and not r['abstracted_by'])
    gap = {'verdict': 'gap', 'visual_case_ids': [en_kept['id']]}
    section = '\n'.join(visual_section(ledger, [gap], root))
    assert '独立性假设存疑' in section and 'locale ←' in section
    assert '独立性存疑，需重展开' in section


def test_frozen_inventory_desktop_floor_is_enforced_on_replay(sample):
    root, write, cfg, case, report, entry, ledger = sample
    inventory = json.loads((root / cfg['inventory_ref']).read_text())
    inventory.update({'platform': 'macos', 'width_range': {'min': 1024, 'max': 1440, 'basis': 'display'}})
    inventory['surfaces'][0]['axes']['device'] = ['1024x768@1', '1440x900@2']
    cfg['inventory_digest'] = write(cfg['inventory_ref'], inventory)
    reason = visual_reason(entry, ledger, root)
    assert '1920' in reason and '1440' in reason
