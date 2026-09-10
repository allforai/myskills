"""Every check returns the refusal reason or ''; the assertions are the ones cross-exam's own suites make."""
import hashlib
import os
from datetime import datetime
from unittest import mock

import evidence
from evidence import (PROBE_WINDOW_TOLERANCE, artifact, bindings_reason, content_reason, entry_reason,
                      evidence_dir, images_reason, parse_time, probe_window_reason, probed_at_reason,
                      readback_reason, ref_digest_reason, served_by_reason)

PROBED_AT = '2026-09-07T10:00:00+08:00'
SERVED = {'host': 'localhost:3000', 'process': 'node next dev', 'mock_layers': []}


def _entry(verdict='done', medium='runtime', ev_dir='evidence/q1/', **extra):
    return {'facet': 'F1', 'q': 'q-1', 'verdict': verdict, 'medium': medium, 'build': 'abc-clean',
            'probed_at': PROBED_AT, 'evidence': {'dir': ev_dir, 'key_observation': 'ok'}, **extra}


def _run(tmp_path, entry, files):
    d = tmp_path / entry['evidence']['dir']
    d.mkdir(parents=True, exist_ok=True)
    for name, body in files.items():
        (d / name).write_bytes(body if isinstance(body, bytes) else body.encode('utf-8'))
    return tmp_path


# --- probed_at (from cross-exam TestProbeWindow / TestLedgerV2ContentGate) ---

def test_probed_at_must_be_iso_with_an_offset():
    assert probed_at_reason({}) == '缺 probed_at（ISO 8601）'
    assert probed_at_reason({'probed_at': 'yesterday'}) == '缺 probed_at（ISO 8601）'
    assert probed_at_reason({'probed_at': '2026-09-07T10:00:00'}) == 'probed_at 缺时区偏移（如 +08:00）'
    assert probed_at_reason({'probed_at': PROBED_AT}) == ''
    assert probed_at_reason({'probed_at': '2026-09-07T02:00:00Z'}) == ''
    assert parse_time(None) is None and parse_time('2026-09-07T02:00:00Z').tzinfo is not None


# --- served_by and mock layers (from cross-exam TestLedgerV2ContentGate) ---

def test_runtime_needs_served_by_and_rejects_mocked_done():
    missing = '缺请求去向 served_by（host / process / mock_layers）'
    assert served_by_reason(_entry()) == missing
    assert served_by_reason(_entry(served_by={'host': 'x', 'process': 'y'})) == missing
    assert served_by_reason(_entry(served_by={'host': 'x', 'process': 'y', 'mock_layers': 'msw'})) == missing
    mocked = {'host': 'localhost:3000', 'process': 'node next dev', 'mock_layers': ['msw']}
    assert served_by_reason(_entry(served_by=mocked)) == '经 mock 层（msw）的 runtime 不能判 done'
    assert served_by_reason(_entry(verdict='gap', served_by=mocked)) == ''       # gap through a mock is still a gap
    # layers that were checked and found inactive live in checked_absent, not mock_layers: done stays admissible
    assert served_by_reason(_entry(served_by={**SERVED, 'checked_absent': ['msw 未注册']})) == ''
    assert served_by_reason(_entry(medium='code')) == ''                       # only runtime has a request destination


# --- content gate (from cross-exam TestLedgerV2ContentGate) ---

def test_note_saying_looks_fine_is_refused_for_code_medium(tmp_path):
    run = _run(tmp_path, _entry(medium='code'), {'note.txt': '看过了，没问题'})
    assert content_reason(_entry(medium='code'), run) == '代码摘录无 路径:行号'


def test_code_excerpt_with_path_line_is_admitted(tmp_path):
    run = _run(tmp_path, _entry(medium='code'),
               {'q01-excerpt.md': 'src/api/refund.ts:42\n  if (order.refunded) return 409'})
    assert content_reason(_entry(medium='code'), run) == ''


def test_runtime_content_needs_files_states_and_served_by(tmp_path):
    run = _run(tmp_path, _entry(), {'q01-01.png': b'\x89PNG'})
    assert content_reason(_entry(), run) == '缺请求去向 served_by（host / process / mock_layers）'
    assert content_reason(_entry(served_by=SERVED), run) == ''
    e = _entry(served_by=SERVED, states_to_capture=['00', '01', '02'])
    assert content_reason(e, run) == '要求 3 个状态只落了 1 个文件'
    empty = _run(tmp_path / 'b', _entry(), {'notes.bin': b'\x00'})
    assert content_reason(_entry(served_by=SERVED), empty) == '运行时证据无截图或输出文件'


def test_unprovable_reason_must_be_substantive(tmp_path):
    run = _run(tmp_path, _entry(verdict='unprovable'), {'reason.md': '起不来'})
    assert content_reason(_entry(verdict='unprovable'), run) == '无法自证缺原因文件（尝试了什么、卡在哪）'
    run = _run(tmp_path / 'b', _entry(verdict='unprovable'),
               {'reason.md': '起不来：npm run dev 在 3000 端口报 EADDRINUSE，换 3001 后页面白屏，控制台无任何输出'})
    assert content_reason(_entry(verdict='unprovable'), run) == ''


def test_content_gate_names_a_naive_probed_at_first(tmp_path):
    run = _run(tmp_path, _entry(), {'q01-01.png': b'\x89PNG'})
    e = _entry(served_by=SERVED, probed_at='2026-09-07T10:00:00')
    assert content_reason(e, run) == 'probed_at 缺时区偏移（如 +08:00）'


# --- evidence directory ---

def test_evidence_dir_must_be_a_non_empty_directory_under_run_evidence(tmp_path):
    (tmp_path / 'evidence/q1').mkdir(parents=True)
    assert evidence_dir(_entry(), tmp_path) == (None, '无证据目录')
    (tmp_path / 'evidence/q1/a.png').write_bytes(b'x')
    path, reason = evidence_dir(_entry(), tmp_path)
    assert reason == '' and path == (tmp_path / 'evidence/q1').resolve()
    for bad in ('.', 'evidence', '../evidence/q1', '', 7):
        assert evidence_dir(_entry(ev_dir=bad), tmp_path)[1] == '无证据目录'
    assert evidence_dir({'evidence': 'not a dict'}, tmp_path)[1] == '无证据目录'
    assert evidence_dir({}, tmp_path)[1] == '无证据目录'


# --- probe window (from cross-exam TestProbeWindow) ---

T0 = datetime.fromisoformat(PROBED_AT).timestamp()


def _window(tmp_path, files, transcript_mtime, probed_at=PROBED_AT):
    """files: {name: seconds relative to T0}; transcript_mtime likewise."""
    e = _entry(medium='code', probed_at=probed_at)
    run = _run(tmp_path, e, {name: 'a/b.ts:1 x' for name in files})
    for name, offset in files.items():
        os.utime(run / 'evidence/q1' / name, (T0 + offset, T0 + offset))
    transcript = tmp_path / 'agent.output'
    transcript.write_text('Files written to evidence/q1/.')
    os.utime(transcript, (T0 + transcript_mtime, T0 + transcript_mtime))
    return e, sorted(f for f in (run / 'evidence/q1').iterdir() if f.is_file()), transcript


def test_file_after_window_is_refused_naming_file_and_window(tmp_path):
    reason = probe_window_reason(*_window(tmp_path, {'q01-late.md': 600 + 200}, 600))
    assert '证据文件写于探测窗口之外' in reason
    assert 'q01-late.md（2026-09-07T10:13:20+08:00）' in reason
    assert '窗口 [2026-09-07T10:00:00+08:00, 2026-09-07T10:12:00+08:00]' in reason
    assert PROBE_WINDOW_TOLERANCE == 120


def test_every_offending_file_is_named(tmp_path):
    reason = probe_window_reason(*_window(tmp_path, {'q01-a.md': 900, 'q01-b.md': 901, 'q01-ok.md': 60}, 600))
    assert 'q01-a.md' in reason and 'q01-b.md' in reason and 'q01-ok.md（' not in reason


def test_file_before_probed_at_is_refused(tmp_path):
    reason = probe_window_reason(*_window(tmp_path, {'q01-stale.md': -60}, 600))
    assert '证据文件写于探测窗口之外' in reason and 'q01-stale.md' in reason


def test_files_inside_window_or_within_tolerance_pass(tmp_path):
    assert probe_window_reason(*_window(tmp_path, {'q01-00.md': 300, 'q01-01.md': 599}, 600)) == ''
    assert probe_window_reason(*_window(tmp_path / 'b', {'q01-excerpt.md': 600 + 60}, 600)) == ''


def test_probed_at_after_transcript_is_an_empty_window(tmp_path):
    assert '证据文件写于探测窗口之外' in probe_window_reason(*_window(tmp_path, {'q01-00.md': -50}, -100))


def test_unreadable_mtime_is_a_note_not_a_refusal(tmp_path):
    real = evidence.mtime

    def flaky(path):
        if path.name == 'q01-00.md':
            raise OSError('no mtime')
        return real(path)
    e, files, transcript = _window(tmp_path, {'q01-00.md': 300, 'q01-01.md': 300}, 600)
    with mock.patch.object(evidence, 'mtime', flaky):
        assert probe_window_reason(e, files, transcript) == ''
    assert e['transcript_note'] == '证据文件时间不可读，探测窗口未核：q01-00.md'
    e, files, _ = _window(tmp_path / 'b', {'q01-00.md': 300}, 600)
    assert probe_window_reason(e, files, tmp_path / 'gone.output') == ''
    assert e['transcript_note'] == 'transcript 时间不可读，探测窗口未核'


def test_probe_window_without_a_usable_probed_at_checks_nothing(tmp_path):
    e, files, transcript = _window(tmp_path, {'q01-00.md': 9999}, 600, probed_at='nonsense')
    assert probe_window_reason(e, files, transcript) == ''


# --- readback (from visual acceptance test_supported_axis_requires_in_app_readback) ---

DARK = {'appearance': {'supported': ['dark'], 'basis': 'values-night/', 'declined': []}}


def test_supported_axis_requires_in_app_readback():
    case = {'id': 'home/dark', 'appearance': 'dark'}
    assert 'appearance 轴缺应用内读回值' in readback_reason(case, {}, DARK)
    assert 'appearance 轴缺应用内读回值' in readback_reason(case, {'readback': {'appearance': '  '}}, DARK)
    assert 'appearance 轴读回值 light 与用例 dark 不符' in readback_reason(case, {'readback': {'appearance': 'light'}}, DARK)
    assert readback_reason(case, {'readback': {'appearance': 'dark'}}, DARK) == ''
    assert readback_reason(case, {'readback': 'dark'}, DARK).startswith('appearance 轴缺应用内读回值')
    assert readback_reason(case, {}, {}) == ''                     # no declared support, nothing to read back


def test_compound_case_value_is_proven_by_its_readback():
    both = {'appearance': {'supported': ['light', 'dark'], 'basis': 'darkMode: class'}}
    case = {'id': 'home/mixed', 'appearance': 'system dark + app light'}
    assert readback_reason(case, {'readback': {'appearance': 'light'}}, both) == ''
    assert '与用例' in readback_reason(case, {'readback': {'appearance': 'sepia'}}, both)


# --- digest binding of refs ---

def test_ref_digest_binding(tmp_path):
    p = tmp_path / 'visual/baseline.json'
    p.parent.mkdir()
    p.write_text('{}')
    good = hashlib.sha256(p.read_bytes()).hexdigest()
    assert ref_digest_reason(tmp_path, 'visual/baseline.json', good, '基线') == ''
    assert ref_digest_reason(tmp_path, 'visual/baseline.json', 'deadbeef', '基线') == '基线摘要不匹配'
    assert ref_digest_reason(tmp_path, 'visual/baseline.json', None, '基线') == '基线摘要不匹配'
    assert ref_digest_reason(tmp_path, '', good, '基线') == '缺文件引用'
    assert ref_digest_reason(tmp_path, 'visual/gone.json', good, '基线') == '文件缺失或越界: visual/gone.json'
    assert ref_digest_reason(tmp_path, '../baseline.json', good, '基线') == '文件缺失或越界: ../baseline.json'
    assert artifact(tmp_path, 'visual/baseline.json') == (p.resolve(), '')
    assert artifact(tmp_path, 3) == (None, '缺文件引用')


def test_bindings_reason_names_the_first_key_that_differs():
    config = {'build': 'abc-clean', 'baseline_digest': 'b1', 'matrix_digest': 'm1'}
    keys = ('build', 'baseline_digest', 'matrix_digest')
    assert bindings_reason({'build': 'abc-clean', 'baseline_digest': 'b1', 'matrix_digest': 'm1'}, config, keys) == ''
    assert bindings_reason({'build': 'abc-dirty', 'baseline_digest': 'b1', 'matrix_digest': 'm1'}, config, keys) == '证据绑定不匹配: build'
    assert bindings_reason({'build': 'abc-clean', 'baseline_digest': 'b1'}, config, keys) == '证据绑定不匹配: matrix_digest'
    assert bindings_reason({'build': 'abc-clean'}, {'build': ''}, ('build',)) == '证据绑定不匹配: build'
    assert bindings_reason('not an object', config, keys) == '证据绑定不匹配: build'


# --- images ---

def test_images_must_exist_under_the_evidence_dir_with_matching_digests(tmp_path):
    d = tmp_path / 'evidence/q1'
    d.mkdir(parents=True)
    (d / 'shot.png').write_bytes(b'\x89PNG-1')
    good = hashlib.sha256(b'\x89PNG-1').hexdigest()
    assert images_reason({'images': ['shot.png'], 'image_digests': {'shot.png': good}}, d) == ''
    assert images_reason({}, d) == ''
    assert images_reason({'images': ['shot.png'], 'image_digests': {'shot.png': 'stale'}}, d) == '截图内容摘要不匹配: shot.png'
    assert images_reason({'images': ['shot.png']}, d) == '截图内容摘要不匹配: shot.png'
    assert images_reason({'images': ['gone.png'], 'image_digests': {}}, d) == '文件缺失或越界: gone.png'
    (tmp_path / 'evidence/outside.png').write_bytes(b'\x89PNG-1')
    assert images_reason({'images': ['../outside.png'], 'image_digests': {'../outside.png': good}}, d) == '文件缺失或越界: ../outside.png'
    assert images_reason({'images': ['shot.png', 'shot.png'], 'image_digests': {'shot.png': good}}, d) == '重复截图引用'
    assert images_reason({'images': 'shot.png'}, d) == '截图引用须是列表'


# --- the ledger-entry shape, end to end ---

def _good(tmp_path):
    e = _entry(served_by=SERVED, readback={'theme': 'dark', 'locale': 'zh-CN'})
    run = _run(tmp_path, e, {'q01-01.png': b'\x89PNG'})
    e['images'] = ['q01-01.png']
    e['image_digests'] = {'q01-01.png': hashlib.sha256(b'\x89PNG').hexdigest()}
    return e, run


def test_entry_shape_admits_a_complete_runtime_entry(tmp_path):
    e, run = _good(tmp_path)
    assert entry_reason(e, run) == ''
    code = _entry(medium='code')
    run = _run(tmp_path / 'c', code, {'q01-excerpt.md': 'src/a.ts:1 x'})
    assert entry_reason(code, run) == ''


def test_entry_shape_refuses_by_name(tmp_path):
    e, run = _good(tmp_path)
    assert entry_reason({**e, 'medium': 'oral'}, run) == '非法介质: oral'
    assert entry_reason({**e, 'verdict': 'maybe'}, run) == '非法裁决：maybe'
    assert entry_reason({**e, 'build': ''}, run) == '缺构建标识 build'
    assert entry_reason({k: v for k, v in e.items() if k != 'build'}, run) == '缺构建标识 build'
    assert entry_reason({**e, 'probed_at': '2026-09-07T10:00:00'}, run) == 'probed_at 缺时区偏移（如 +08:00）'
    assert entry_reason({**e, 'evidence': {'dir': '.'}}, run) == '无证据目录'
    assert entry_reason({k: v for k, v in e.items() if k != 'served_by'}, run) == '缺请求去向 served_by（host / process / mock_layers）'
    assert entry_reason({**e, 'readback': ['dark']}, run) == 'readback 须是轴到应用内读回值的对象'
    assert entry_reason({**e, 'readback': {'theme': ''}}, run) == 'theme 轴缺应用内读回值'
    assert entry_reason({**e, 'image_digests': {'q01-01.png': 'stale'}}, run) == '截图内容摘要不匹配: q01-01.png'


def test_entry_shape_never_raises(tmp_path):
    for bad in (None, 3, 'entry', [], {'evidence': None}, {'evidence': {'dir': 7}, 'medium': None, 'build': 1}):
        reason = entry_reason(bad, tmp_path)
        assert isinstance(reason, str) and reason
    assert entry_reason({}, tmp_path / 'missing-run') != ''
