import hashlib
import json
from pathlib import Path

import pytest
from validation import AXES, CATEGORIES, visual_reason, visual_section
from matrix import expand
from PIL import Image

FLUID = {'rule': 'approved', 'pinned': False}   # every layout rule declares pinned or fluid (#51)


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
        k: {'rules': [FLUID] if k == 'layout' else ['approved'], 'confirmation': 'user approved',
            'confirmed_at': '2026-09-06', 'reference_images': references}
        for k in CATEGORIES}})
    cfg = {'facet_ids': ['F1'], 'baseline_status': 'confirmed',
           'baseline_ref': 'visual/baseline.json', 'baseline_digest': digest,
           'interaction_ref': 'visual/baseline.json', 'interaction_digest': digest,
           'review_mode': 'single', 'build': 'abc-clean',
           'inventory_ref': 'visual/inventory.json', 'matrix_ref': 'visual/matrix.json'}
    inventory = {'platform': 'ios', 'surfaces': [{'id': 'home', 'axes': {a: ['default'] for a in AXES}}]}
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
    inventory = {'platform': 'ios', 'surfaces': [{'id': 'home', 'axes': {**{a: ['default'] for a in AXES},
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
    inventory = {'platform': 'ios', 'surfaces': [{'id': 'home', 'axes': {**{a: ['default'] for a in AXES},
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
    inventory = {'platform': 'ios', 'surfaces': [{'id': 'home', 'axes': axes, 'groups': ['buttons']},
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
    inventory = {'platform': 'ios', 'surfaces': [{'id': 'feed', 'scrollable': True,
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
    inventory = {'platform': 'ios', 'locales': locales,
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
    inventory = {'platform': 'ios', 'axis_support': axis_support,
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


def _layout_reason(sample, rules, width_range='global', surfaces=None, readback_width='auto'):
    """Freeze a baseline whose layout rules are `rules` over an inventory with the given width range."""
    root, write, cfg, case, report, entry, ledger = sample
    baseline = json.loads((root / cfg['baseline_ref']).read_text())
    baseline['categories']['layout']['rules'] = rules
    cfg['baseline_digest'] = cfg['interaction_digest'] = write(cfg['baseline_ref'], baseline)
    for ref in ('evidence/q1/manifest.json', 'evidence/q1/review.json'):
        obj = json.loads((root / ref).read_text())
        for holder in obj.get('captures', [obj]):
            holder['baseline_digest'] = holder['interaction_digest'] = cfg['baseline_digest']
        write(ref, obj)
    if width_range == 'global':
        width_range = {'min': 1024, 'max': 1920, 'basis': 'minWidth + display'}
    if width_range is not None or surfaces is not None:
        inventory = json.loads((root / cfg['inventory_ref']).read_text())
        if surfaces is not None:
            inventory['surfaces'] = surfaces
        if width_range is not None:
            inventory['width_range'] = width_range
            for s in inventory['surfaces']:
                r = s.get('width_range') or width_range
                s['axes']['device'] = ['%dx768@1' % r['min'], '%dx1080@1' % r['max']]
        cfg['inventory_digest'] = write(cfg['inventory_ref'], inventory)
        rows = expand(inventory['surfaces'], width_range=inventory.get('width_range'))
        cfg['matrix_digest'] = write(cfg['matrix_ref'], rows)
        ledger['visual_cases'] = rows
        entry['visual_case_ids'] = [rows[0]['id']]
        for ref in ('evidence/q1/manifest.json', 'evidence/q1/review.json'):
            obj = json.loads((root / ref).read_text())
            for holder in obj.get('captures', [obj]):
                holder['inventory_digest'] = cfg['inventory_digest']
                holder['matrix_digest'] = cfg['matrix_digest']
                if 'case_id' in holder:
                    holder['case_id'] = rows[0]['id']
                    holder.update({a: rows[0][a] for a in AXES})
                    width = inventory['width_range']['min'] if readback_width == 'auto' else readback_width
                    if width is not None:
                        holder.setdefault('readback', {})['width'] = width
                    else:
                        holder.pop('readback', None)
            write(ref, obj)
    return visual_reason(entry, ledger, root)


GOOD_ENDS = {'1024': {'empty': '两侧各 ≤ 内容宽度 10%'}, '1920': {'empty': '两侧各 ≤ 内容宽度 40%，其余由侧栏与附件栏填充'}}
PINNED = {'rule': '消息列 820px 居中', 'pinned': True, 'ends': GOOD_ENDS}


@pytest.mark.parametrize('text', ['消息列 820px 居中', '侧栏固定在左侧', 'approved'])
def test_pinned_string_layout_rule_is_refused(sample, text):
    """A bare string in the layout category declares nothing; the reason names both shapes."""
    reason = _layout_reason(sample, [text])
    assert reason and text in reason and 'pinned: false' in reason and 'pinned: true, ends' in reason


def test_pinned_object_rule_with_both_ends_is_accepted(sample):
    assert _layout_reason(sample, [PINNED]) is None
    assert _layout_reason(sample, [{'rule': '侧栏固定在左侧', 'pinned': False}, PINNED]) is None


def test_pinned_rule_without_ends_is_refused(sample):
    reason = _layout_reason(sample, [{'rule': '消息列 820px 居中', 'pinned': True}])
    assert reason and '820px' in reason and 'ends' in reason


def test_fluid_rule_naming_a_width_is_refused(sample):
    reason = _layout_reason(sample, [{'rule': '消息列 820px 居中', 'pinned': False}])
    assert reason and '820px' in reason and '流式' in reason


def test_fluid_rule_carrying_ends_is_refused(sample):
    reason = _layout_reason(sample, [{'rule': '侧栏固定在左侧', 'pinned': False, 'ends': GOOD_ENDS}])
    assert reason and '侧栏固定在左侧' in reason and '流式' in reason


def test_pinned_rule_without_a_literal_is_checked_by_its_ends(sample):
    """'列宽等于设计稿' pins a width the text cannot show; the declaration makes it checkable."""
    assert _layout_reason(sample, [{'rule': '列宽等于设计稿', 'pinned': True, 'ends': GOOD_ENDS}]) is None
    reason = _layout_reason(sample, [{'rule': '列宽等于设计稿', 'pinned': True, 'ends': {'1024': {'empty': 'x'}}}])
    assert reason and '1920' in reason


@pytest.mark.parametrize('rule', [{'rule': '侧栏固定在左侧'}, {'rule': '侧栏固定在左侧', 'pinned': 'yes'},
                                  {'rule': '侧栏固定在左侧', 'pinned': 1}, {'rule': '侧栏固定在左侧', 'pinned': None}])
def test_undeclared_pinned_is_refused(sample, rule):
    reason = _layout_reason(sample, [rule])
    assert reason and 'pinned' in reason and '侧栏固定在左侧' in reason


@pytest.mark.parametrize('ends', [
    {'1024': {'empty': 'x'}},                                              # missing an end
    {'1024': {'empty': 'x'}, '1920': {'empty': 'x'}, '1440': {'empty': 'x'}},  # extra key
    {'1200': {'empty': 'x'}, '2000': {'empty': 'x'}},                      # not the frozen range's ends
    {'1024': {'empty': 'x'}, '1920': {'empty': '   '}},                    # blank allowance
    {'1024': 'x', '1920': {'empty': 'x'}},                                 # malformed end
    'wide ok',                                                             # malformed ends
])
def test_bad_ends_are_refused_with_a_reason(sample, ends):
    reason = _layout_reason(sample, [{**PINNED, 'ends': ends}])
    assert reason and '消息列 820px 居中' in reason


def test_pinned_rule_without_width_range_is_refused(sample):
    reason = _layout_reason(sample, [PINNED], width_range=None)
    assert reason and 'width_range' in reason


def test_fluid_rule_needs_no_width_range(sample):
    fluid = {'rule': '主列随窗口拉伸，侧栏固定', 'pinned': False}
    assert _layout_reason(sample, [fluid]) is None
    assert _layout_reason(sample, [fluid], width_range=None) is None


def test_malformed_layout_rule_shapes_yield_reasons(sample):
    for rules in ([42], [None], [{'pinned': True, 'ends': GOOD_ENDS}], [{'rule': '', 'pinned': True, 'ends': GOOD_ENDS}],
                  [{'rule': ['a'], 'pinned': False}], 'not a list', [{'rule': 'x', 'pinned': True, 'ends': None}]):
        reason = _layout_reason(sample, rules)
        assert isinstance(reason, str) and reason


def _two_surfaces():
    axes = {a: ['default'] for a in AXES}
    admin = {'id': 'admin', 'axes': {**axes}, 'width_range': {'min': 1280, 'max': 1920, 'basis': 'desktop-only route'}}
    return [{'id': 'home', 'axes': {**axes}}, admin]


ADMIN_ENDS = {'1280': {'empty': '表格撑满'}, '1920': {'empty': '表格撑满，右侧 ≤ 20% 留给筛选栏'}}


def test_surface_scoped_pinned_rule_checks_that_surface_range(sample):
    rule = {'rule': '管理表格最小 1200px', 'pinned': True, 'surface': 'admin', 'ends': ADMIN_ENDS}
    assert _layout_reason(sample, [rule], surfaces=_two_surfaces()) is None
    against_global = {**rule, 'ends': GOOD_ENDS}
    reason = _layout_reason(sample, [against_global], surfaces=_two_surfaces())
    assert reason and '1280' in reason and '1920' in reason


def test_surface_without_own_range_uses_the_global_range(sample):
    rule = {**PINNED, 'surface': 'home'}
    assert _layout_reason(sample, [rule], surfaces=_two_surfaces()) is None
    reason = _layout_reason(sample, [{**rule, 'ends': ADMIN_ENDS}], surfaces=_two_surfaces())
    assert reason and '1024' in reason


def test_unknown_surface_on_a_pinned_rule_is_refused(sample):
    rule = {**PINNED, 'surface': 'ghost'}
    reason = _layout_reason(sample, [rule], surfaces=_two_surfaces())
    assert reason and 'ghost' in reason


def test_old_run_without_form_factor_is_refused_readably(sample):
    """A run frozen before these checks: web inventory without form_factor and below the desktop floor."""
    root, write, cfg, case, report, entry, ledger = sample
    inventory = json.loads((root / cfg['inventory_ref']).read_text())
    inventory.update({'platform': 'web', 'width_range': {'min': 1200, 'max': 1512, 'basis': '用户显示器'}})
    inventory['surfaces'][0].update({'scrollable': False})
    inventory['surfaces'][0]['axes']['device'] = ['1200x800@2', '1512x982@2']
    cfg['inventory_digest'] = write(cfg['inventory_ref'], inventory)
    reason = visual_reason(entry, ledger, root)
    assert reason.startswith('视觉证据无效') and 'form_factor' in reason
    inventory['form_factor'] = 'desktop'
    cfg['inventory_digest'] = write(cfg['inventory_ref'], inventory)
    reason = visual_reason(entry, ledger, root)
    assert '1920' in reason and '1512' in reason


def test_old_baseline_with_string_layout_rules_is_refused_readably(sample):
    """A baseline frozen before #51 wrote layout rules as strings: refused with the two shapes, not a crash."""
    reason = _layout_reason(sample, ['approved', '主列随窗口拉伸'])
    assert reason.startswith('视觉证据无效') and 'pinned: false' in reason and 'approved' in reason


@pytest.mark.parametrize('text', ['消息列820px居中', '消息列 820PX 居中', '列宽 820 px', '最小 600pt 宽', '卡片 360dp'])
def test_width_literal_is_found_without_spaces_or_ascii_boundaries(sample, text):
    reason = _layout_reason(sample, [{'rule': text, 'pinned': False}])
    assert reason and '流式' in reason


def test_width_literal_ignores_non_width_tokens(sample):
    fluid = [{'rule': t, 'pinned': False} for t in ('pxl 图标', 'dpi 设置跟随系统', '2dpx')]
    assert _layout_reason(sample, fluid) is None


def test_odd_layout_shapes_name_the_problem_not_the_python_error(sample):
    reason = _layout_reason(sample, [{**PINNED, 'surface': ['home']}])
    assert reason and '页面' in reason and 'unhashable' not in reason
    root, write, cfg, case, report, entry, ledger = sample
    baseline = json.loads((root / cfg['baseline_ref']).read_text())
    baseline['categories']['layout'] = 'approved'
    cfg['baseline_digest'] = cfg['interaction_digest'] = write(cfg['baseline_ref'], baseline)
    for ref in ('evidence/q1/manifest.json', 'evidence/q1/review.json'):
        obj = json.loads((root / ref).read_text())
        for holder in obj.get('captures', [obj]):
            holder['baseline_digest'] = holder['interaction_digest'] = cfg['baseline_digest']
        write(ref, obj)
    reason = visual_reason(entry, ledger, root)
    assert reason and 'has no attribute' not in reason


def test_fixed_size_window_accepts_one_end(sample):
    rng = {'min': 1024, 'max': 1024, 'basis': 'kiosk window'}
    root, write, cfg, case, report, entry, ledger = sample
    rule = {'rule': '消息列 820px 居中', 'pinned': True, 'ends': {'1024': {'empty': '两侧各 ≤ 10%'}}}
    baseline = json.loads((root / cfg['baseline_ref']).read_text())
    baseline['categories']['layout']['rules'] = [rule]
    cfg['baseline_digest'] = cfg['interaction_digest'] = write(cfg['baseline_ref'], baseline)
    inventory = json.loads((root / cfg['inventory_ref']).read_text())
    inventory['width_range'] = rng
    inventory['surfaces'][0]['axes']['device'] = ['1024x768@1']
    cfg['inventory_digest'] = write(cfg['inventory_ref'], inventory)
    rows = expand(inventory['surfaces'], width_range=rng, platform='ios')
    cfg['matrix_digest'] = write(cfg['matrix_ref'], rows)
    ledger['visual_cases'] = rows
    entry['visual_case_ids'] = [rows[0]['id']]
    for ref in ('evidence/q1/manifest.json', 'evidence/q1/review.json'):
        obj = json.loads((root / ref).read_text())
        for holder in obj.get('captures', [obj]):
            holder.update({k: cfg[k] for k in ('baseline_digest', 'interaction_digest', 'inventory_digest', 'matrix_digest')})
            if 'case_id' in holder:
                holder['case_id'] = rows[0]['id']
                holder.update({a: rows[0][a] for a in AXES})
                holder['readback'] = {'width': 1024}
        write(ref, obj)
    assert visual_reason(entry, ledger, root) is None


def test_dangling_surface_is_refused_even_without_ends(sample):
    reason = _layout_reason(sample, [{'rule': '侧栏固定在左侧', 'pinned': False, 'surface': 'ghost'}],
                            surfaces=_two_surfaces())
    assert reason and 'ghost' in reason


def test_interaction_baseline_layout_literals_are_not_window_pins(sample):
    root, write, cfg, case, report, entry, ledger = sample
    interaction = {'categories': {k: {'rules': ['approved'], 'confirmation': 'ok', 'confirmed_at': '2026-09-06',
                                      'reference_images': {}} for k in CATEGORIES}}
    interaction['categories']['layout']['rules'] = ['抽屉从左侧滑出 280px', '下拉刷新阈值 80pt']
    cfg['interaction_ref'] = 'visual/interaction.json'
    cfg['interaction_digest'] = write(cfg['interaction_ref'], interaction)
    for ref in ('evidence/q1/manifest.json', 'evidence/q1/review.json'):
        obj = json.loads((root / ref).read_text())
        for holder in obj.get('captures', [obj]):
            holder['interaction_digest'] = cfg['interaction_digest']
        write(ref, obj)
    assert visual_reason(entry, ledger, root) is None


@pytest.mark.parametrize('text', ['视口 1440x900px 下侧栏展开', 'x820px 无意义', '版本 H.264 pt 无关'])
def test_width_literal_needs_a_whole_number(sample, text):
    assert _layout_reason(sample, [{'rule': text, 'pinned': False}]) is None


def test_a_pinned_width_hidden_in_another_category_is_refused(sample):
    root, write, cfg, case, report, entry, ledger = sample
    baseline = json.loads((root / cfg['baseline_ref']).read_text())
    baseline['categories']['spacing']['rules'] = ['消息列 820px 居中，两侧留白']
    cfg['baseline_digest'] = cfg['interaction_digest'] = write(cfg['baseline_ref'], baseline)
    for ref in ('evidence/q1/manifest.json', 'evidence/q1/review.json'):
        obj = json.loads((root / ref).read_text())
        for holder in obj.get('captures', [obj]):
            holder['baseline_digest'] = holder['interaction_digest'] = cfg['baseline_digest']
        write(ref, obj)
    reason = visual_reason(entry, ledger, root)
    assert reason and 'spacing' in reason and '820px' in reason


@pytest.mark.parametrize('blank', ['​', '﻿ ‍', '⠀'])
def test_invisible_allowance_is_not_an_allowance(sample, blank):
    ends = {'1024': {'empty': '两侧各 ≤ 10%'}, '1920': {'empty': blank}}
    reason = _layout_reason(sample, [{**PINNED, 'ends': ends}])
    assert reason and 'empty' in reason


@pytest.mark.parametrize('text', ['消息列 820 像素 居中', 'column 820 pixels centred', '主列 51.25rem 居中',
                                  '消息列 max-width: 820，居中'])
def test_a_width_written_around_the_literal_is_still_a_width(sample, text):
    reason = _layout_reason(sample, [{'rule': text, 'pinned': False}])
    assert reason and '流式' in reason


def test_capture_must_read_back_the_width_it_claims(sample):
    """A device value is a claim about the window; only the app can say how wide it actually rendered."""
    rule = PINNED
    assert _layout_reason(sample, [rule], readback_width=1024) is None
    reason = _layout_reason(sample, [rule], readback_width=None)
    assert reason and 'width' in reason
    reason = _layout_reason(sample, [rule], readback_width=2000)
    assert reason and '1024' in reason


def test_hidden_width_is_refused_even_when_layout_category_has_no_rules(sample):
    """Omitting the layout category entirely must not open a door for width literals elsewhere."""
    root, write, cfg, case, report, entry, ledger = sample
    baseline = json.loads((root / cfg['baseline_ref']).read_text())
    baseline['categories']['layout'] = {'rules': [], 'reason': '无布局规则', 'confirmation': 'ok',
                                        'confirmed_at': '2026-09-06', 'reference_images': {}}
    del baseline['categories']['layout']['rules']
    baseline['categories']['spacing']['rules'] = ['侧栏与主列间距 0px']
    cfg['baseline_digest'] = cfg['interaction_digest'] = write(cfg['baseline_ref'], baseline)
    for ref in ('evidence/q1/manifest.json', 'evidence/q1/review.json'):
        obj = json.loads((root / ref).read_text())
        for holder in obj.get('captures', [obj]):
            holder['baseline_digest'] = holder['interaction_digest'] = cfg['baseline_digest']
        write(ref, obj)
    reason = visual_reason(entry, ledger, root)
    assert reason and 'spacing' in reason


def _census_reason(sample, census, platform='ios', form_factor=None, thresholds=None,
                   width_range='global', surfaces=None, readback_width='auto'):
    """Put the census's verbatim width facts on the ledger top level and freeze an inventory against them."""
    root, write, cfg, case, report, entry, ledger = sample
    ledger.update(census)
    inventory = json.loads((root / cfg['inventory_ref']).read_text())
    inventory['platform'] = platform
    if form_factor is not None:
        inventory['form_factor'] = form_factor
    if thresholds is not None:
        inventory['layout_thresholds'] = thresholds
    write(cfg['inventory_ref'], inventory)          # digest follows in _layout_reason
    if surfaces is None:
        surfaces = [{'id': 'home', 'axes': {**{a: ['default'] for a in AXES}, 'state': ['default', 'resize-drag']}}]
    return _layout_reason(sample, ['approved'], width_range=width_range, surfaces=surfaces,
                          readback_width=readback_width)


CENSUS_RANGE = {'min': 1024, 'max': 1920, 'basis': 'electron main.ts:12 minWidth; 1920 display'}


def test_inventory_form_factor_cannot_be_weaker_than_census(sample):
    for read in ('desktop', 'both'):
        reason = _census_reason(sample, {'form_factor': read})            # ios implies mobile
        assert reason and 'mobile' in reason and read in reason
    reason = _census_reason(sample, {'form_factor': {'value': 'desktop', 'basis': 'electron main.ts:12'}})
    assert reason and 'mobile' in reason and 'desktop' in reason


def test_inventory_form_factor_may_be_stronger_than_census(sample):
    assert _census_reason(sample, {'form_factor': 'mobile'}, platform='macos') is None
    assert _census_reason(sample, {'form_factor': 'desktop'}, platform='macos', form_factor='both') is None
    assert _census_reason(sample, {'form_factor': {'value': 'desktop', 'basis': 'main.ts:12'}}, platform='macos') is None


def test_inventory_width_range_may_widen_but_never_narrow_the_census(sample):
    reason = _census_reason(sample, {'width_range': {**CENSUS_RANGE, 'max': 2560}})
    assert reason and '1920' in reason and '2560' in reason
    reason = _census_reason(sample, {'width_range': {**CENSUS_RANGE, 'min': 900}})
    assert reason and '1024' in reason and '900' in reason
    assert _census_reason(sample, {'width_range': {**CENSUS_RANGE, 'min': 1200, 'max': 1600}}) is None
    assert _census_reason(sample, {'width_range': CENSUS_RANGE}) is None


def test_inventory_without_width_range_cannot_hide_a_census_range(sample):
    surfaces = [{'id': 'home', 'axes': {a: ['default'] for a in AXES}}]
    reason = _census_reason(sample, {'width_range': CENSUS_RANGE}, width_range=None, surfaces=surfaces,
                            readback_width=None)
    assert reason and 'width_range' in reason and '1920' in reason


def test_inventory_cannot_drop_a_census_layout_threshold(sample):
    census = {'layout_thresholds': [{'width': 1280, 'unit': 'px', 'basis': 'app.css:3'},
                                    {'width': 1440, 'unit': 'px', 'basis': 'app.css:9'}]}
    reason = _census_reason(sample, census, thresholds=[{'width': 1280, 'basis': 'app.css:3'}])
    assert reason and '1440' in reason and '1280' not in reason
    added = [{'width': 1280, 'basis': 'app.css:3'}, {'width': 1440, 'basis': 'app.css:9'},
             {'width': 1600, 'basis': 'user: 1600 wide dock'}]
    assert _census_reason(sample, census, thresholds=added) is None


def _narrowed(min_width=1280, entry=None):
    axes = {a: ['default'] for a in AXES}
    admin = {'id': 'admin', 'axes': {**axes, 'state': ['default', 'resize-drag']},
             'width_range': {'min': min_width, 'max': 1920, 'basis': 'desktop-only route'}}
    if entry:
        admin['entry'] = entry
    return [{'id': 'home', 'axes': {**axes, 'state': ['default', 'resize-drag']}}, admin]


def test_narrowed_surface_needs_a_census_counterpart_with_a_width_range(sample):
    reason = _census_reason(sample, {'width_range': CENSUS_RANGE, 'ui_surfaces': []}, surfaces=_narrowed())
    assert reason and 'admin' in reason
    no_range = {'width_range': CENSUS_RANGE, 'ui_surfaces': [{'id': 'admin', 'name': 'Admin', 'entry': 'admin.tsx'}]}
    reason = _census_reason(sample, no_range, surfaces=_narrowed())
    assert reason and 'admin' in reason


def test_narrowed_surface_matching_the_census_is_accepted_and_narrower_is_refused(sample):
    read = {'id': 'U4', 'name': 'Admin', 'entry': 'src/routes/admin.tsx:Admin',
            'width_range': {'min': 1280, 'max': 1920, 'basis': 'router.tsx:40 innerWidth >= 1280'}}
    by_id = {'width_range': CENSUS_RANGE, 'ui_surfaces': [{**read, 'id': 'admin'}]}
    assert _census_reason(sample, by_id, surfaces=_narrowed()) is None
    by_entry = {'width_range': CENSUS_RANGE, 'ui_surfaces': [read]}
    assert _census_reason(sample, by_entry, surfaces=_narrowed(entry=read['entry'])) is None
    assert _census_reason(sample, by_id, surfaces=_narrowed(min_width=1200)) is None     # wider than read
    reason = _census_reason(sample, by_id, surfaces=_narrowed(min_width=1440))
    assert reason and 'admin' in reason and '1440' in reason and '1280' in reason


def test_missing_census_keys_are_not_checked(sample):
    assert _census_reason(sample, {}) is None
    assert _census_reason(sample, {}, surfaces=_narrowed()) is None          # narrowing unchecked without a census range


@pytest.mark.parametrize('census', [
    {'form_factor': 42}, {'form_factor': 'tablet'}, {'form_factor': {'basis': 'main.ts:12'}},
    {'width_range': 'wide'}, {'width_range': {'min': 'a', 'max': 1920}},
    {'layout_thresholds': 'x'}, {'layout_thresholds': [{'width': '1280'}]},
    {'width_range': CENSUS_RANGE, 'ui_surfaces': 'x'},
    {'width_range': CENSUS_RANGE, 'ui_surfaces': [{'id': 'admin', 'width_range': {'min': 'a', 'max': 1920}}]},
])
def test_malformed_census_shapes_yield_reasons(sample, census):
    reason = _census_reason(sample, census, surfaces=_narrowed())
    assert isinstance(reason, str) and '普查官' in reason
