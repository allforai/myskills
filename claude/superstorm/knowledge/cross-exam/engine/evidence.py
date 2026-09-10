"""Evidence engine: what a ledger entry must carry before any verdict can rest on it.

Extracted from cross-exam's renderer (probed_at, served_by / mock layers, the content gate, the probe window)
and the visual acceptance validator (digest binding of refs, in-app readback of applied axes). Every check
returns '' when the entry passes and the refusal reason otherwise; nothing here raises on a malformed entry,
because a traceback names no rule. Reason strings are the ones cross-exam already prints."""
import hashlib
import os
import re
from datetime import datetime
from pathlib import Path

PATH_LINE = re.compile(r'[\w./\-]+\.[A-Za-z0-9]+:\d+')
IMAGE_SUFFIXES = {'.png', '.jpg', '.jpeg'}
OUTPUT_SUFFIXES = {'.txt', '.log', '.json', '.md'}
PROBE_WINDOW_TOLERANCE = 120   # 秒：实测官最后一次写证据与 transcript 收尾落盘之间容许的偏差
MEDIA = ('runtime', 'code', 'ledger')
VERDICTS = ('done', 'gap', 'drift', 'unprovable')
SEGMENT_SPLIT = re.compile(r'[+/,;]')
TOKEN_SPLIT = re.compile(r'[\s+/,;]+')


# --- digests and refs ---

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def artifact(root, ref):
    """(resolved file, '') for a ref under `root`, or (None, reason): a ref that escapes the root or names
    nothing on disk is not a frozen input."""
    if not isinstance(ref, str) or not ref:
        return None, '缺文件引用'
    root = Path(root)
    path = (root / ref).resolve()
    if root.resolve() not in path.parents or not path.is_file():
        return None, '文件缺失或越界: ' + ref
    return path, ''


def ref_digest_reason(root, ref, expected, label):
    """A frozen input is bound by digest: the file at `ref` must hash to `expected` or the run reads a
    document nobody confirmed. `label` names the input in the reason (基线, 页面清单, 普查官原件...)."""
    path, reason = artifact(root, ref)
    if reason:
        return reason
    if not isinstance(expected, str) or digest(path) != expected:
        return label + '摘要不匹配'
    return ''


def bindings_reason(obj, config, keys):
    """Every binding key on `obj` must equal the frozen run configuration; an empty config value binds nothing
    and is refused too."""
    for key in keys:
        if not isinstance(config, dict) or not config.get(key) \
                or not isinstance(obj, dict) or obj.get(key) != config[key]:
            return '证据绑定不匹配: ' + str(key)
    return ''


# --- time ---

def parse_time(value):
    try:
        return datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    except (TypeError, ValueError):
        return None


def probed_at_reason(entry):
    probed = parse_time((entry or {}).get('probed_at')) if isinstance(entry, dict) else None
    if not probed:
        return '缺 probed_at（ISO 8601）'
    if probed.tzinfo is None:   # 无偏移的时间在每台渲染机上都是另一个探测窗口
        return 'probed_at 缺时区偏移（如 +08:00）'
    return ''


# --- where the evidence lives ---

def evidence_dir(entry, run_dir):
    """(directory, '') when entry.evidence.dir is a non-empty directory under <run>/evidence, else
    (None, '无证据目录'): "." or the run directory itself is not evidence of anything."""
    ev = entry.get('evidence') if isinstance(entry, dict) else None
    d = ev.get('dir') if isinstance(ev, dict) else None
    if not isinstance(d, str) or not d:
        return None, '无证据目录'
    run_dir = Path(run_dir)
    p = (Path(d) if Path(d).is_absolute() else run_dir / d).resolve()
    try:
        if (run_dir / 'evidence').resolve() not in p.parents or not p.is_dir() or not any(p.iterdir()):
            return None, '无证据目录'
    except OSError:
        return None, '无证据目录'
    return p, ''


def evidence_files(entry, run_dir):
    p, reason = evidence_dir(entry, run_dir)
    return [] if reason else [f for f in p.iterdir() if f.is_file()]


# --- served_by and the content gate ---

def served_by_reason(entry):
    """A runtime probe records where its requests went; through an active mock layer it can show a gap
    (mock 下都坏，真后端只会更坏) but never a done."""
    if not isinstance(entry, dict) or entry.get('medium') != 'runtime':
        return ''
    served = entry.get('served_by')
    if not isinstance(served, dict) or not served.get('host') or not served.get('process') \
            or not isinstance(served.get('mock_layers'), list):
        return '缺请求去向 served_by（host / process / mock_layers）'
    if served['mock_layers'] and entry.get('verdict') == 'done':
        return '经 mock 层（' + ', '.join(map(str, served['mock_layers'])) + '）的 runtime 不能判 done'
    return ''


def content_reason(entry, run_dir):
    """A non-empty directory only shows files exist, not that anyone probed: code needs a 路径:行号 excerpt,
    runtime needs screenshots or outputs (no fewer than the states asked for) and a request destination,
    unprovable needs a reason file that says what was tried."""
    if not isinstance(entry, dict):
        return '缺 probed_at（ISO 8601）'
    reason = probed_at_reason(entry)
    if reason:
        return reason
    files = evidence_files(entry, run_dir)
    medium, verdict = entry.get('medium'), entry.get('verdict')
    text = ''.join(f.read_text(encoding='utf-8', errors='ignore') for f in files if f.suffix not in IMAGE_SUFFIXES)
    if verdict == 'unprovable':
        return '' if len(text.strip()) >= 40 else '无法自证缺原因文件（尝试了什么、卡在哪）'
    if medium == 'code' and not PATH_LINE.search(text):
        return '代码摘录无 路径:行号'
    if medium == 'runtime':
        images = [f for f in files if f.suffix.lower() in IMAGE_SUFFIXES]
        outputs = [f for f in files if f.suffix.lower() in OUTPUT_SUFFIXES]
        if not images and not outputs:
            return '运行时证据无截图或输出文件'
        wanted = entry.get('states_to_capture')
        if isinstance(wanted, list) and wanted and len(files) < len(wanted):
            return '要求 %d 个状态只落了 %d 个文件' % (len(wanted), len(files))
        return served_by_reason(entry)
    return ''


# --- probe window ---

def mtime(path):
    return os.stat(path).st_mtime


def probe_window(entry, files, transcript, read_mtime=None):
    """探测窗口 [probed_at, transcript mtime + PROBE_WINDOW_TOLERANCE]：实测官从开始到返回的这段时间。
    证据目录里每个文件的修改时间都要落在窗口内，transcript 点了名的也不例外——点名只证明实测官打算写它，
    不证明这一份就是它写的；probed_at 晚于 transcript 落盘则窗口为空，一个都不认。
    The facts alone, for a consumer whose report pins its own sentence: None when probed_at is unusable
    (naive or absent: the content gate names that first), else {start: aware datetime, end: timestamp or
    None when the transcript's time is unreadable, outside: [(name, timestamp)], unreadable: [name]}.
    `read_mtime` is the file-time reader (default `mtime`); a consumer's tests may hand in their own."""
    read = read_mtime or mtime
    start = parse_time(entry.get('probed_at')) if isinstance(entry, dict) else None
    if not start or start.tzinfo is None:
        return None
    window = {'start': start, 'end': None, 'outside': [], 'unreadable': []}
    try:
        window['end'] = read(transcript) + PROBE_WINDOW_TOLERANCE
    except OSError:
        return window
    for f in files:
        try:
            m = read(f)
        except OSError:
            window['unreadable'].append(f.name)
            continue
        if not start.timestamp() <= m <= window['end']:
            window['outside'].append((f.name, m))
    return window


def probe_window_reason(entry, files, transcript, read_mtime=None):
    """The probe window as a refusal: every offender named with its time, or '' with a note on the entry
    (entry['transcript_note']) when a time could not be read——文件系统抹掉 mtime 是属性，不是造假。"""
    window = probe_window(entry, files, transcript, read_mtime)
    if window is None:
        return ''
    if window['end'] is None:
        entry['transcript_note'] = 'transcript 时间不可读，探测窗口未核'
        return ''
    start = window['start']
    stamp = lambda t: datetime.fromtimestamp(t, start.tzinfo).isoformat()
    if window['outside']:
        return '证据文件写于探测窗口之外，窗口 [%s, %s]：%s' % (
            start.isoformat(), stamp(window['end']), '、'.join('%s（%s）' % (n, stamp(m)) for n, m in window['outside']))
    if window['unreadable']:
        entry['transcript_note'] = '证据文件时间不可读，探测窗口未核：' + '、'.join(window['unreadable'])
    return ''


# --- readback of applied settings ---

def value_tokens(value):
    """An axis value may be compound ("浏览器 zh-CN + 站点 en", "zoom 150% + 字号 20px"). A supported value
    is present when it equals the whole value, one of its separator-delimited segments, or one whitespace token."""
    v = str(value).strip()
    return {v} | {s.strip() for s in SEGMENT_SPLIT.split(v) if s.strip()} | set(TOKEN_SPLIT.split(v))


def readback(capture):
    """The map of axis to in-app value a capture or entry carries, {} when it carries none."""
    rb = capture.get('readback') if isinstance(capture, dict) else None
    return rb if isinstance(rb, dict) else {}


def readback_reason(case, capture, support):
    """Setting an axis is not the same as the app rendering it: for every axis the code declares support on,
    the capture must carry the value read back inside the app, and it must be one the case claims."""
    rb = readback(capture)
    case = case if isinstance(case, dict) else {}
    for axis in (support or {}):
        got = rb.get(axis)
        if not isinstance(got, str) or not got.strip():
            return '%s 轴缺应用内读回值: %s' % (axis, case.get('id', '?'))
        if got.strip() not in value_tokens(case.get(axis, '')):
            return '%s 轴读回值 %s 与用例 %s 不符: %s' % (axis, got, case.get(axis), case.get('id', '?'))
    return ''


def readback_shape_reason(entry):
    """An entry's own readback (theme, locale, zoom, width... as the app reported them) is a map of axis to
    non-empty value; which axes must be present is the caller's contract, the shape is this one."""
    rb = entry.get('readback')
    if rb is None:
        return ''
    if not isinstance(rb, dict):
        return 'readback 须是轴到应用内读回值的对象'
    for axis, value in rb.items():
        if isinstance(value, bool) or (not isinstance(value, (str, int, float))) or (isinstance(value, str) and not value.strip()):
            return '%s 轴缺应用内读回值' % axis
    return ''


# --- images ---

def images_reason(holder, evidence_dir):
    """Screenshots an entry or capture lists must exist under its evidence directory and hash to the recorded
    digests; a listed image nobody can find or that changed since is not the image the verdict looked at."""
    refs = holder.get('images') if isinstance(holder, dict) else None
    if refs is None:
        return ''
    if not isinstance(refs, list) or any(not isinstance(r, str) for r in refs):
        return '截图引用须是列表'
    if len(refs) != len(set(refs)):
        return '重复截图引用'
    digests = holder.get('image_digests')
    digests = digests if isinstance(digests, dict) else {}
    for ref in refs:
        path, reason = artifact(evidence_dir, ref)
        if reason:
            return reason
        if digests.get(ref) != digest(path):
            return '截图内容摘要不匹配: ' + ref
    return ''


# --- the ledger-entry shape ---

def entry_reason(entry, run_dir):
    """The shape every evidence entry shares, whoever wrote it: a legal medium and verdict, a build identity,
    probed_at with an offset, a real evidence directory under the run, content that looks like a probe,
    served_by for runtime, a well-formed readback and bound images. '' admits; anything else names the rule."""
    if not isinstance(entry, dict):
        return '条目须是对象'
    if entry.get('medium') not in MEDIA:
        return '非法介质: %s' % entry.get('medium')
    if entry.get('verdict') not in VERDICTS:
        return '非法裁决：%s' % entry.get('verdict')
    build = entry.get('build')
    if not isinstance(build, str) or not build.strip():
        return '缺构建标识 build'
    reason = probed_at_reason(entry)
    if reason:
        return reason
    path, reason = evidence_dir(entry, run_dir)
    if reason:
        return reason
    try:
        reason = content_reason(entry, run_dir) or readback_shape_reason(entry) or images_reason(entry, path)
    except (OSError, UnicodeError) as exc:
        reason = '证据文件不可读: %s' % exc
    return reason
