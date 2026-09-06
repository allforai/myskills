"""Visual evidence contract. Structural validation cannot prove image provenance or taste."""
import hashlib
import importlib.util
import json
import math
from pathlib import Path


def _sibling(name):
    """Load a sibling module by path under a unique name so a same-named module on sys.path cannot shadow it."""
    spec = importlib.util.spec_from_file_location('cross_exam_visual_' + name, Path(__file__).with_name(name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


expand = _sibling('matrix').expand
ANNOTATION_KEYS = {'applicability', 'reason', 'basis'}
_VERIFIED_IMAGES = set()   # content digests already decoded and verified in this process

CATEGORIES = {'direction', 'color', 'typography', 'layout', 'spacing', 'icons',
              'components', 'navigation', 'feedback', 'states', 'motion', 'environment'}
AXES = ('state', 'device', 'os', 'appearance', 'dynamic_type', 'locale', 'orientation')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def image_digest(path):
    try:
        from PIL import Image
    except ImportError as exc:
        raise ValueError('视觉校验需要 Pillow 解码；不能降级为文件头检查') from exc
    content = digest(path)
    if content in _VERIFIED_IMAGES:   # same bytes already decoded: baseline refs repeat per category and per entry
        return content
    try:
        with Image.open(path) as img:
            if img.format not in {'PNG', 'JPEG'}:
                raise ValueError('仅接受 PNG/JPEG 原图')
            img.verify()
        with Image.open(path) as img:
            img.load()
    except ValueError:
        raise
    except Exception as exc:  # Pillow raises SyntaxError / DecompressionBombError / OSError on bad files
        raise ValueError('图片无法解码: ' + path.name + ': ' + str(exc)) from exc
    _VERIFIED_IMAGES.add(content)
    return content


def frozen_cases(run, config):
    for key in ('inventory', 'matrix'):
        path = artifact(run, config.get(key + '_ref'))
        if digest(path) != config.get(key + '_digest'):
            raise ValueError('页面清单/矩阵摘要不匹配')
    inventory = read(run, config['inventory_ref'])
    expected = {c['id']: c for c in expand(inventory['surfaces'])}
    rows = read(run, config['matrix_ref'])
    actual = {c.get('id'): c for c in rows}
    if len(rows) != len(actual) or actual.keys() != expected.keys():
        raise ValueError('冻结矩阵未覆盖完整页面清单')
    for cid, case in expected.items():
        if any(actual[cid].get(k) != v for k, v in case.items()):
            raise ValueError('冻结用例身份或属性不一致')
    return actual


def same_matrix(ledger_rows, frozen):
    """ledger.visual_cases must be the frozen matrix; rows may add only the not_applicable annotation keys."""
    rows = {c.get('id'): c for c in ledger_rows}
    if len(rows) != len(ledger_rows) or rows.keys() != frozen.keys():
        return False
    for cid, row in rows.items():
        base = frozen[cid]
        if any(row.get(k) != v for k, v in base.items()):
            return False
        if set(row) - set(base) - ANNOTATION_KEYS:
            return False
    return True


def frame_digest(path):
    from PIL import Image
    try:
        with Image.open(path) as img:
            pixels = img.convert('RGBA')
            return hashlib.sha256(str(pixels.size).encode() + pixels.tobytes()).hexdigest()
    except Exception as exc:
        raise ValueError('动态帧无法解码: ' + path.name + ': ' + str(exc)) from exc


def bindings(obj, config):
    for key in ('build', 'baseline_digest', 'interaction_digest', 'inventory_digest', 'matrix_digest'):
        if not config.get(key) or obj.get(key) != config[key]:
            raise ValueError('证据绑定不匹配: ' + key)


def artifact(root, ref):
    if not isinstance(ref, str) or not ref:
        raise ValueError('缺文件引用')
    path = (root / ref).resolve()
    if root.resolve() not in path.parents or not path.is_file():
        raise ValueError('文件缺失或越界: ' + ref)
    return path


def read(root, ref):
    return json.loads(artifact(root, ref).read_text())


def baseline(run, config):
    if config.get('baseline_status') != 'confirmed':
        raise ValueError('视觉基线未确认')
    confirmed = set()
    references = {}
    for key in ('baseline', 'interaction'):
        path = artifact(run, config.get(key + '_ref'))
        if hashlib.sha256(path.read_bytes()).hexdigest() != config.get(key + '_digest'):
            raise ValueError('基线摘要不匹配')
        for category, value in json.loads(path.read_text()).get('categories', {}).items():
            if value.get('confirmed_at') and value.get('confirmation') and (value.get('rules') or value.get('reason')):
                confirmed.add(category)
            for ref, expected_digest in value.get('reference_images', {}).items():
                if image_digest(artifact(run, ref)) != expected_digest:
                    raise ValueError('基线参考图片已改变')
                references[ref] = expected_digest
    if not CATEGORIES <= confirmed:
        raise ValueError('基线缺逐类确认: ' + ', '.join(sorted(CATEGORIES - confirmed)))
    if not references:
        raise ValueError('视觉基线缺可解码的参考图片')
    return references


ENV_AXES = tuple(a for a in AXES if a != 'state')


def split_groups(cases, ids):
    """Cases sharing a comparison group in the same environment must be judged in one entry, or nobody compared them."""
    chosen = [cases[i] for i in ids]
    for case in chosen:
        for group in case.get('groups') or []:
            env = tuple(case.get(a) for a in ENV_AXES)
            peers = [c for c in cases.values() if group in (c.get('groups') or [])
                     and tuple(c.get(a) for a in ENV_AXES) == env and c.get('id') not in ids]
            if peers:
                return group + ' 缺 ' + ', '.join(sorted(p.get('surface', '?') for p in peers))
    return ''


def _visual_facets(config):
    facets = config.get('facet_ids') or []
    return facets if isinstance(facets, list) else [facets]


def visual_reason(entry, ledger, run):
    config = ledger.get('visual_acceptance') or {}
    if not isinstance(config, dict):
        config = {}
    try:
        ids = entry.get('visual_case_ids') or []
        if not ids and entry.get('facet') not in _visual_facets(config):
            return None
        ledger_rows = ledger.get('visual_cases') or []
        cases = {c.get('id'): c for c in ledger_rows}
        if len(cases) != len(ledger_rows) or None in cases:
            raise ValueError('视觉用例 id 重复或缺失')
        if not isinstance(ids, list) or not ids or len(ids) != len(set(ids)) or not set(ids) <= cases.keys():
            raise ValueError('视觉用例引用无效')
        if entry.get('verdict') == 'unprovable':
            artifact(run / 'evidence', entry.get('visual_failure_ref'))
            return None
        frozen = frozen_cases(run, config)
        if not same_matrix(ledger_rows, frozen):
            raise ValueError('ledger 用例与冻结完整矩阵不一致')
        reference_images = baseline(run, config)
        if entry.get('medium') != 'runtime':
            raise ValueError('视觉裁决必须使用运行证据')
        evidence = run / 'evidence'
        manifest = read(evidence, entry.get('evidence_manifest'))
        images = set()
        image_hashes = {}
        recordings = {}
        captures = {c['case_id']: c for c in manifest['captures']}
        if len(captures) != len(manifest['captures']):
            raise ValueError('截图用例 id 重复')
        for cid in ids:
            case = cases[cid]
            capture = captures[cid]
            bindings(capture, config)
            if any(capture.get(k) != case.get(k) or not capture.get(k) for k in AXES):
                raise ValueError('截图环境与用例不匹配: ' + cid)
            if not capture.get('build') or not capture.get('captured_at'):
                raise ValueError('缺构建或截图时间')
            if capture.get('baseline_digest') != config['baseline_digest']:
                raise ValueError('截图引用过期基线')
            refs = capture.get('images', [])
            if not refs or (case.get('motion') and len(refs) < 2):
                raise ValueError('缺真实截图或动态关键帧')
            if len(refs) != len(set(refs)):
                raise ValueError('重复截图引用不能作为动态帧')
            for ref in refs:
                actual_digest = image_digest(artifact(evidence, ref))
                if capture.get('image_digests', {}).get(ref) != actual_digest:
                    raise ValueError('截图内容摘要不匹配')
                image_hashes[ref] = actual_digest
                images.add(ref)
            if case.get('motion'):
                times = capture.get('frame_times_ms', [])
                if (len(times) != len(refs) or any(type(t) not in (int, float) or not math.isfinite(t) or t < 0 for t in times)
                        or any(a >= b for a, b in zip(times, times[1:]))
                        or len({frame_digest(artifact(evidence, r)) for r in refs}) < 2):
                    raise ValueError('动态证据缺有效时序或不同帧内容')
                clip = capture.get('recording')
                if not clip or clip in refs:
                    raise ValueError('动态用例缺录屏: ' + cid)
                clip_path = artifact(evidence, clip)
                if clip_path.stat().st_size == 0:
                    raise ValueError('动态用例缺录屏: ' + cid)
                if capture.get('recording_digest') != digest(clip_path):
                    raise ValueError('录屏摘要不匹配: ' + cid)
                recordings[clip] = capture['recording_digest']
        peers_missing = split_groups(cases, ids)
        if peers_missing:
            raise ValueError('比较组被拆开，同组同环境用例须同批: ' + peers_missing)
        reports = [read(evidence, p) for p in entry.get('review_reports', [])]
        mode = entry.get('review_mode', config.get('review_mode'))
        locked = config.get('review_mode')
        if locked not in {'single', 'dual'} or mode not in ({'single'} if locked == 'single' else {'dual', 'dual_degraded'}):
            raise ValueError('禁止静默变更审查模式')
        expected = 2 if mode == 'dual' else 1
        if mode not in {'single', 'dual', 'dual_degraded'} or len(reports) != expected:
            raise ValueError('审查拓扑与报告数量不符')
        if mode == 'dual_degraded':
            failure = read(evidence, entry.get('degradation_ref'))
            if (failure.get('platform') not in {'claude', 'codex'} or
                    len(failure.get('attempts', [])) < 2 or
                    not all(a.get('reason') and a.get('attempted_at') for a in failure['attempts'])):
                raise ValueError('降级缺两次实际失败记录')
        platforms, sessions, blocking = set(), set(), set()
        recordings_reviewed = False
        for report in reports:
            bindings(report, config)
            if any(report.get('image_digests', {}).get(r) != h for r, h in image_hashes.items()):
                raise ValueError('reviewer 图片内容绑定不匹配')
            if any(report.get('reference_images', {}).get(r) != h for r, h in reference_images.items()):
                raise ValueError('reviewer 未检查冻结参考图片')
            platforms.add(report['platform'])
            sessions.add(report['session_id'])
            if not report['session_id'] or report.get('independent') is not True:
                raise ValueError('缺独立 reviewer 身份')
            if report.get('baseline_digest') != config['baseline_digest']:
                raise ValueError('reviewer 使用过期基线')
            if not images <= set(report.get('inspected_images', [])):
                raise ValueError('reviewer 未检查全部原图')
            if recordings and set(recordings) <= set(report.get('inspected_recordings') or []):
                recordings_reviewed = True
            elif recordings:
                if not (isinstance(report.get('recording_unreadable'), str) and report['recording_unreadable'].strip()):
                    raise ValueError('reviewer 未审阅录屏也未说明无法读取')
            if report.get('status') not in {'passed', 'findings'}:
                raise ValueError('reviewer 未完成')
            inspected = set(report.get('inspected_images', []))
            for finding in report.get('findings', []):
                if not finding.get('rule') or not finding.get('observation') or not finding.get('images'):
                    raise ValueError('发现缺规则、观察或图片')
                if not set(finding['images']) <= inspected or finding.get('severity') not in {'high','medium','low'}:
                    raise ValueError('发现引用或严重度无效')
                # 阻断按 finding 指向的用例计：同一份报告可被同批拆出的多条 entry 共用，
                # 只有指向本 entry 原图的 high/medium 才阻断本 entry。
                if finding['severity'] in {'high', 'medium'} and set(finding['images']) & images:
                    blocking.add(report['session_id'] + ':' + finding['id'])
        if not platforms <= {'claude', 'codex'} or len(sessions) != expected:
            raise ValueError('reviewer 身份无效或重复')
        if mode == 'dual_degraded' and failure['platform'] in platforms:
            raise ValueError('降级保留了失败方的报告')
        if mode == 'dual':
            if platforms != {'claude', 'codex'}:
                raise ValueError('双审需 Claude 和 Codex')
            reconciliation = read(evidence, entry.get('reconciliation_ref'))
            if not blocking <= set(reconciliation.get('blocking_findings', [])):
                raise ValueError('双审阻断项并集缺失')
            if not isinstance(reconciliation.get('disagreements'), list):
                raise ValueError('缺双审分歧记录')
        if blocking and entry.get('verdict') == 'done':
            raise ValueError('存在未解决阻断发现')
        if recordings and not recordings_reviewed and entry.get('verdict') == 'done':
            raise ValueError('录屏无人审阅，动态用例不能判 done')
    except (ValueError, KeyError, TypeError, AttributeError, IndexError, OSError) as exc:
        return '视觉证据无效: ' + str(exc)
    return None


def visual_section(ledger, admitted, run=None):
    config = ledger.get('visual_acceptance')
    if not config:
        return []
    out = ['', '## 视觉基线与矩阵覆盖', '',
           f"基线：{config.get('baseline_status')} · {config.get('baseline_ref')} · {config.get('interaction_ref')}",
           f"审查模式：{config.get('review_mode')}；文件校验不代替实际看图。", '']
    counts = dict.fromkeys(['done','gap','drift','unprovable','not_examined','not_applicable'], 0)
    rows = [c for c in (ledger.get('visual_cases') or []) if isinstance(c, dict)]
    if run is not None:
        try:
            frozen = frozen_cases(run, config)
            # Frozen cases remain visible even when an examiner omitted ledger rows;
            # ledger rows keep their not_applicable annotation on top of the frozen identity.
            by_id = {c.get('id'): c for c in rows}
            rows = [{**base, **{k: by_id[cid][k] for k in ANNOTATION_KEYS if cid in by_id and k in by_id[cid]}}
                    for cid, base in frozen.items()] + [c for c in rows if c.get('id') not in frozen]
        except (ValueError, KeyError, TypeError, AttributeError, OSError) as exc:
            out.append('矩阵无法自证，不能声称完整覆盖：' + str(exc))
    for case in rows:
        cid = case.get('id') or '（无 id）'
        matches = [e for e in admitted if cid in (e.get('visual_case_ids') or [])]
        state = 'not_examined'
        if matches:
            # Conservative across repeated results: an old failure cannot silently disappear.
            state = next(v for v in ('gap','drift','unprovable','done')
                         if any(e['verdict'] == v for e in matches))
        elif case.get('applicability') == 'not_applicable' and case.get('reason') and case.get('basis'):
            state = 'not_applicable'
        counts[state] += 1
        out.append(f"- {cid} {case.get('surface')} — {state} · " +
                   ' / '.join(str(case.get(k, '?')) for k in AXES))
        for entry in matches:
            out.append(f"  证据：{entry.get('evidence_manifest', entry.get('visual_failure_ref'))} · "
                       f"reviewers：{entry.get('review_reports', [])} · "
                       f"模式：{entry.get('review_mode', config.get('review_mode'))} · "
                       f"分歧：{entry.get('reconciliation_ref', '无')} · 降级：{entry.get('degradation_ref', '无')}")
    out.insert(5, ' · '.join(f'{k}: {v}' for k, v in counts.items()))
    return out
