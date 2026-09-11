#!/usr/bin/env python3
"""cross-exam 完成度报告渲染器（确定性，禁止口述生成报告）。

诚实性红线在这里、在代码里，不在嘱咐里：
- status=="not_examined" 的面不进任何完成度统计，只进"未盘问声明"；
- 无证据 entry（缺 evidence.dir / 目录不在 run 目录的 evidence/ 之下 / 目录不
  存在 / 目录为空）以及 verdict 不在 done|gap|drift|unprovable 内的 entry，
  一律拒绝渲染进正文与计数，在"违规裁决"段点名并区分原因（无证据目录 /
  非法裁决）。合法裁决必有证据（could_not 也要落原因文件），被拒的只可能是
  绕过实测的口头裁决，或试图用"."、run 目录本身等非证据目录蒙混过关。

另渲染 ledger 可选的 `open_threads`（出过牌但未实测的线）为"未拉的线"专节——
不进任何计数，只为续盘留接手点（防弃牌蒸发）。

可选 `patterns`（缺陷模式=同类位点清点）渲染为"缺陷模式"专节。位点不许自报
"已查"：一个位点算实证，当且仅当它的 `entry_q` 精确匹配到一条被采信（有证据）
的 entry；对不上、或对上的是被拒渲的口头裁决，一律算未查并逐个点名。未查位点
不进任何裁决计数——同类嫌疑不许蒸发，也不许口头销账。

缺口清单里的普通 gap|drift 带 `G` 号：按 ledger 里 entries 的先后顺序编，不按严重度，
续盘只追加不重排所以编号稳定；被拒渲的不占号；旅程 entry 只带 `J` 号。product-review 的
`depends_on` 引用的就是这两种号。

旅程 entry 另有逐步证据合同：`steps[].evidence` 每步必写且文件必须真在 `evidence.dir` 下，
`terminal_state.snapshot` 同理；缺一个就整条拒渲并点名缺的文件——编造的步骤列表过不了这一层。

可选 `journeys`（旅程声明）渲染为"旅程完成度"专节。旅程没有自报"已查"的通道：
`entry_q` 精确匹配到被采信 entry 且该 entry 的 `journey` 等于旅程 id 才算已盘问，
否则进"未盘问声明"（前缀"旅程"）并按 risk 排序。entry 带 `journey` 但 journeys 里
查无此 id、或旅程 gap 的 `stuck_kind` 不在六种之内，一律拒渲并点名；旅程 drift 缺
`missed_waypoints` 同样拒渲并点名。旅程裁决计数与普通裁决计数分列，互不掺入。

覆盖分母（可选 `surfaces` / `requirements`）：census 的操作面原样入账后，facet 的"操作面 K 个，
裁决触及 T 个，未触及：…"由渲染器按被采信 entry 的 `surfaces[]` 算，facet 的 examined 也由
"有没有被采信 entry"推导——手写的 `status` 只保留 not_examined 的意图，不能把零证据的面算成盘过。
entry 引用了 `surfaces` 里没有的 id 一律不算触及并点名；没写 `surfaces` 的 entry 逐条点名。
`requirements`（需求基准逐条入账）渲染为"需求覆盖"专节：一条需求有裁决，当且仅当某条被采信 entry
的 `requirement_refs`/`requirement_ref` 引用了它；无裁决的按"落在哪个面、该面盘没盘"点名，
没落任何面的单独点名——需求侧的蒸发和操作面侧的蒸发一样，都必须在报告里留下名字。

作者证据（#60）：带 `author` 标记的 entry 是交付流水线写的，先过引擎的条目形状，再核 readback 非空与
`build` 是本仓库此刻的树。机械介质（build / test / contract）核过即作**门**，渲染进"作者证据"专节；
runtime 等其它介质永远只作上下文。门不是裁决：同一问没有实测官 entry 的门按无法自证入账并写明原因——
作者写的任何东西都关不掉一个 done / gap / drift；核不过的按引擎的理由拒渲。

Usage: python3 render_report.py <run_dir>    # run_dir 内含 ledger.json
写出 <run_dir>/completion-report.md。exit 0=渲染成功（有拒渲仍为 0，报告内声明）；
exit 1=ledger 不可读或缺必填键。
"""
import importlib.util
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

_PACKAGE = Path(__file__).resolve().parents[1]


def _by_path(name, path):
    """Load a package module by path under a unique module name: a `validation` or `evidence` module
    already on sys.path (another package, a test process) must never stand in for this package's own."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_visual = _by_path("cross_exam_visual_validation", _PACKAGE / "visual/validation.py")
visual_reason, visual_section = _visual.visual_reason, _visual.visual_section
# The evidence engine (ADR-0008) owns what an entry must carry before it is read: probed_at, the evidence
# directory, the content gate per medium, served_by, the probe window. This renderer keeps the names its
# tests patch as aliases and decides nothing the engine already decides.
_engine = _by_path("cross_exam_engine_evidence", _PACKAGE / "engine/evidence.py")
PROBE_WINDOW_TOLERANCE = _engine.PROBE_WINDOW_TOLERANCE
_evidence_files = _engine.evidence_files
_content_reason = _engine.content_reason
_parse_time = _engine.parse_time

# Author evidence (#60): an entry the delivery pipeline wrote carries an `author` marker. It walks the engine's
# entry shape plus the build identity of the tree now; a mechanical medium gates, runtime is context, neither
# is a verdict — the examiner_is_author bias-guard covers every such entry.
_identity = _by_path("cross_exam_engine_identity", _PACKAGE / "engine/identity.py")
GATE_MEDIA = _engine.GATE_MEDIA
AUTHOR_KEYS = ("pipeline", "node_id", "capability")
HOST_DIR = re.compile(r"^\.[\w.-]+$")   # 宿主隐藏目录（.allforai、.claude、.codex）：作者只能把这些排在构建标识之外
GATE_STATES = {"done": "门通过", "gap": "门未通过", "drift": "门未通过", "unprovable": "门未核"}

VERDICT_LABELS = {"done": "实证完成", "gap": "缺口",
                  "drift": "跑偏", "unprovable": "无法自证"}
SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}
STUCK_KINDS = {"no_entry": "无入口", "not_found": "找不到", "misleading": "误导",
               "no_feedback": "无反馈", "no_recovery": "无恢复路径", "broken": "系统报错"}
AUTHOR_DETECTED_NOTE = ("检测到当前 git 用户 {email} 是目标仓库最近 50 次提交的作者之一，而 ledger 未标 "
                        "examiner_is_author：按作者自审处理，bias-guard 应生效（gap 从严，降级需额外独立证据）。")
AUTHOR_NOTE = ("盘问官即交付作者（examiner_is_author）：bias-guard 生效——gap 从严，"
               "降级为 low 或 done 需额外独立证据。")
BASELINE_NONE_NOTE = ("需求基准缺失（baseline: none）：需求覆盖、需求跑偏两镜头"
                      "因无基准关闭，本报告未盘问这两个维度。")
AUTHOR_EVIDENCE_NOTE = ("作者证据（{pipelines}，带 author 标记）：机械门 {gates} 条经引擎核验后采信，作门不作裁决；"
                        "运行时等其它介质 {context} 条仅作上下文。bias-guard 对每条作者证据生效——没有独立实测官 entry "
                        "的问题按无法自证入账，运行时问题仍须独立取证。")
GATE_ALONE_NOTE = "作者证据只作门（{medium} {state}），裁决须独立实测官取证"


def _load(run_dir):
    path = run_dir / "ledger.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise SystemExit(f"ledger unreadable: {path}: {e}")
    for key in ("target", "baseline", "facets", "entries"):
        if key not in data:
            raise SystemExit(f"ledger missing required key: {key}")
    return data


def _has_evidence(entry, run_dir):
    return not _engine.evidence_dir(entry, run_dir)[1]


def _status_rank(status):
    """done 排 0，其它（stuck / could_not / 任何坏值）排 1——合并时只在乎"这是不是一个失败读数"，
    失败读数永远不被 done 盖过，不管哪份报告先到。"""
    return 0 if status == "done" else 1


def _prober_steps(body):
    """实测官在 transcript 里当场返回的 steps，合并成台账必须兜底的下限；一份都解析不出来就
    返回 None（缺证不定罪）。

    自检那条规则只写在 prompt 里（「只改格式与措辞，不改任何 status，不删 could_not」），没人核。
    transcript 允许出现多份（重试、自检后重发），这里把每一份能解析出 `steps` 列表的 JSON 都收
    进来取**并集**——不是以最后一份为准：自检重发一旦更短（漏了一步、把 steps 清空成 []），旧版
    "以最后一份为准"就会把已经报过的卡住步骤从下限里抹掉。按 `n` 转字符串为键；同一份报告里缺
    `n` 的步骤按它在这份报告里的 1-based 序号定位（不是全局序号），不再被静默丢弹。两份报告在
    同一个键上给出不同 status 时，留下失败的那份：`stuck` / `could_not` 盖过 `done`，无论谁先
    到——自检只能改格式与措辞，不能把一个失败读数洗白成 done。"""
    merged = None
    for match in re.finditer(r'\{[^{}]*"steps"\s*:\s*\[', body):
        start = match.start()
        depth = 0
        for index in range(start, len(body)):
            if body[index] == '{':
                depth += 1
            elif body[index] == '}':
                depth -= 1
                if depth == 0:
                    try:
                        candidate = json.loads(body[start:index + 1])
                    except ValueError:
                        break
                    if isinstance(candidate.get("steps"), list):
                        if merged is None:
                            merged = {}
                        for position, step in enumerate(candidate["steps"], start=1):
                            if not isinstance(step, dict):
                                continue
                            n = step.get("n")
                            key = str(n) if n is not None else str(position)
                            status = step.get("status")
                            if key not in merged or _status_rank(status) > _status_rank(merged[key]):
                                merged[key] = status
                    break
    return merged


def _prober_agreement_reason(e, body, journeys=None):
    """实测官报过的 steps（并集，见 `_prober_steps`）是台账必须兜底的下限：报了的每一步台账都得
    有对应条目，status 要对得上；没报的这一层不管——缺证不定罪。实测官没返回可解析的 JSON 就不比。

    报了 steps 却发现这条 entry 没挂 journey：只有当某条**声明的**旅程（`journeys[].entry_q`
    精确等于这条 entry 的 `q`）本该落在这条 entry 上时，才说明台账把实测官走过的旅程丢了——
    没有旅程声明认领这条 entry 时，transcript 里凑巧出现 steps 形状的 JSON（贴的示例、不相关
    的工具日志）什么都不证明，不能拒渲。journey 的其它检查全靠 `e.get("journey")` 才会跑，删
    掉这个字段就把它们全部关掉，所以真被声明认领时这一层不等 journey 存在就先比对 reported，
    缺了就点名，不放过"删 journey 字段"这条最省事的绕过。"""
    reported = _prober_steps(body)
    if reported is None:
        return ""
    if not e.get("journey"):
        entry_q = e.get("q")
        claimed = any(j.get("entry_q") == entry_q for j in (journeys or []))
        if not claimed:
            return ""
        return "实测官返回了旅程 steps，但这条 entry 没有 journey：台账把实测官走过的旅程丢了"
    ledger = e.get("steps")
    ledger = ledger if isinstance(ledger, list) else []
    ledger_by_n = {}
    for index, step in enumerate(ledger):
        if isinstance(step, dict):
            ledger_by_n[str(step.get("n", index + 1))] = step.get("status")
    missing = [n for n in reported if n not in ledger_by_n]
    if missing:
        return ("实测官报了第 %s 步，台账 steps 里没有：删条目、清空数组、把 n 改到不存在的号，"
                "都不能让报过的步骤在台账里消失" % "、".join(missing))
    for n, status in reported.items():
        if ledger_by_n[n] != status:
            return (f"第 {n} 步台账记 {ledger_by_n[n]}，实测官返回的是 {status}："
                    f"自检只改格式与措辞，不改 status")
    return ""


def _transcript_reason(e, run_dir, journeys=None):
    """实测官 transcript 核对：ledger 记了子 agent 的 output_file，transcript 就必须能证明证据是实测官写的——
    证据目录里每个文件名都出现在 transcript 里，或 transcript 提到过该证据目录（脚本循环生成的文件名不会
    逐个出现，但写入目录会）。两者都没有，拒渲。文件不在（换机器、临时目录已清）只标不可核，不拒渲。
    名字过了关再核 steps[] 与实测官返回的是否一致，最后核探测窗口（见 _window_sentence）：
    提过目录不等于目录里后来加的文件也是实测官写的。`journeys` 是 ledger 顶层声明——透传给
    `_prober_agreement_reason` 判断"entry 没挂 journey"是否真的是被声明认领的旅程被丢了。"""
    task = e.get("agent_task") or {}
    out = task.get("output_file")
    if not out:
        return ""
    p = Path(out)
    if not p.is_file():
        e["transcript_note"] = "transcript 不可核（文件不在）"
        return ""
    body = p.read_text(encoding="utf-8", errors="ignore")
    files = _evidence_files(e, run_dir)
    absent = [f.name for f in files if f.name not in body]
    d = ((e.get("evidence") or {}).get("dir") or "").strip().rstrip("/")
    d = d[2:] if d.startswith("./") else d
    if absent and not (d and d in body):
        return "证据文件未出现在实测官 transcript，transcript 也未提及证据目录 %s：%s" % (d or "?", "、".join(absent))
    agreement = _prober_agreement_reason(e, body, journeys)
    if agreement:
        return agreement
    return _window_sentence(e, files, p)


def _window_sentence(e, files, transcript):
    """探测窗口由引擎算（engine.probe_window：probed_at 起，transcript 写完加容差止，证据目录里每个文件都要落在
    窗口内，点过名的也一样）；这里只把引擎给的事实写成本端报告的句子——逐个点名越窗文件，修改时间读不出来只记
    note 不拒渲。窗口不从 ledger 自身时间戳凭空造：transcript 不在就不核（上游已标不可核）。"""
    window = _engine.probe_window(e, files, transcript)
    if window is None:
        return ""
    if window["end"] is None:
        e["transcript_note"] = "transcript 时间不可读，探测窗口未核"
        return ""
    start = window["start"]
    stamp = lambda t: datetime.fromtimestamp(t, tz=start.tzinfo).isoformat(timespec="seconds")
    if window["outside"]:   # name every offender: one at a time is a slower argument with the same ending
        return "证据文件 %s，不在探测窗口 [%s, %s] 内" % (
            "、".join("%s 写于 %s" % (name, stamp(m)) for name, m in window["outside"]),
            start.isoformat(timespec="seconds"), stamp(window["end"]))
    if window["unreadable"]:
        e["transcript_note"] = "证据文件 %s 修改时间不可读，探测窗口未核" % "、".join(window["unreadable"])
    return ""


def _repo_root(run_dir):
    """run 目录所在仓库的顶层；不在仓库里就交回 run 目录，让引擎自己说"不是 git 仓库"。"""
    try:
        top = subprocess.run(["git", "-C", str(run_dir), "rev-parse", "--show-toplevel"], capture_output=True,
                             text=True, timeout=5, check=True).stdout.strip()
        return Path(top) if top else run_dir
    except Exception:
        return run_dir


def _author_reason(e, run_dir):
    """作者证据入账前的核验：先过引擎的条目形状（介质、裁决、build、probed_at 偏移、证据目录与内容、readback 形状、
    截图摘要），再加作者独有的三条——author 标记齐全；readback 非空（工具自己报的运行对象，如 runner 与用例数，
    和应用读回一个道理）；记录的 build 是本仓库此刻的树，按 entry 声明的宿主目录加本 run 目录排除后重算。
    作者只能排除宿主隐藏目录：把产品路径排在身份之外，身份就什么都不说了。"""
    author = e.get("author")
    if not isinstance(author, dict) or not all(isinstance(author.get(k), str) and author[k].strip() for k in AUTHOR_KEYS):
        return "作者标记不完整（pipeline / node_id / capability）"
    reason = _engine.entry_reason(e, run_dir)
    if reason:
        return reason
    if e.get("medium") == "runtime" and not _engine.readback(e):   # a suite run has nothing to read back
        return "作者证据缺读回 readback"
    excludes = e.get("build_excludes") if isinstance(e.get("build_excludes"), list) else []
    bad = [str(x) for x in excludes if not isinstance(x, str) or not HOST_DIR.match(x)]
    if bad:
        return "构建标识排除范围只能是宿主隐藏目录（如 .allforai）: " + "、".join(bad)
    artifacts = e.get("build_artifacts") if isinstance(e.get("build_artifacts"), list) else []
    repo = _repo_root(run_dir)
    try:
        own = run_dir.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError:
        own = ""
    return _identity.build_reason(e.get("build"), repo, [repo / str(a) for a in artifacts],
                                  excludes + ([own] if own and own != "." else []))


def _author_line(e, admitted_by_q):
    """作者证据一行：门通过与否或"仅上下文"，谁写的、什么介质、哪个 build，以及同一问有没有独立实测官的裁决。"""
    a, ev = e["author"], e.get("evidence", {})
    gate = e.get("medium") in GATE_MEDIA
    probe = admitted_by_q.get(e.get("q"))
    if probe:
        tail = f"独立实测：{VERDICT_LABELS[probe['verdict']]}"
    else:
        tail = "未独立实测，按无法自证入账" if gate else "待独立实测官取证"
    return (f"- **{e['gate_state'] if gate else '仅上下文'}** [{e.get('facet', '?')}] {e.get('q', '?')} — {ev.get('key_observation', '')}"
            f"（{a['pipeline']} · {a['node_id']} · {a['capability']} · 介质 {e.get('medium')} · build {e.get('build')}"
            f" · 证据：{ev.get('dir', '')}）· {tail}")


def _risk_key(facet):
    level = (facet.get("risk") or {}).get("level")
    return SEVERITY_ORDER.get(level, 3)


def _missing_step_files(e, run_dir):
    """旅程 entry 的逐步证据合同：steps[].evidence 与 terminal_state.snapshot 必须真在 evidence.dir 下。"""
    if not e.get("journey"):
        return []
    d = (e.get("evidence") or {}).get("dir") or ""
    base = Path(d) if Path(d).is_absolute() else run_dir / d
    missing = []
    for st in e.get("steps", []):
        name = st.get("evidence")
        if not name:
            missing.append(f"第 {st.get('n', '?')} 步未写 evidence")
        elif not (base / name).is_file():
            missing.append(name)
    snap = (e.get("terminal_state") or {}).get("snapshot")
    if snap and not (base / snap).is_file():
        missing.append(snap)
    return missing


def _not_examined_line(name, item):
    risk = item.get("risk") or {}
    level = risk.get("level")
    if level in SEVERITY_ORDER:
        tag = f"风险 {level}：{risk.get('why', '')}"
    else:
        tag = "未评估风险"
    return f"- {name}（{item.get('id', '?')}）— 未盘问，不计入任何完成度 · {tag}"


def _entry_line(e):
    label = VERDICT_LABELS.get(e.get("verdict"), e.get("verdict"))
    jtag = f" [{e['journey']}]" if e.get("journey") else ""
    gtag = f" [{e['gap_id']}]" if e.get("gap_id") else ""
    facet_tag = f" [{e.get('facet', '?')}]"
    ref = f" [{e['requirement_ref']}]" if e.get("requirement_ref") else ""
    ev = e.get("evidence", {})
    atag = " [作者证据]" if e.get("author") else ""
    note = "".join(f" · {e[k]}" for k in ("transcript_note", "author_note") if e.get(k))
    return (f"- **{label}**{atag}{jtag}{gtag}{facet_tag}{ref} {e.get('q', '?')} — {ev.get('key_observation', '')}"
            f"（证据：{ev.get('dir', '')}）{note}")


SHORTHAND = re.compile(r"^(.*?-)(\d+)((?:/\d+)+)$")


def _requirement_ids(e):
    """entry 引用的需求 id：`requirement_refs` 列表为准；旧字段 `requirement_ref` 兼容"R-09"、"R-09, R-10"，
    以及 "R-moment-01/03/07" 这种共享前缀的简写（展开成 R-moment-01、R-moment-03、R-moment-07）。"""
    ids = set(e.get("requirement_refs") or [])
    ref = e.get("requirement_ref")
    for chunk in re.split(r"[,，、\s]+", ref or ""):
        if not chunk:
            continue
        m = SHORTHAND.match(chunk)
        if m:
            prefix, first, rest = m.groups()
            ids.add(prefix + first)
            ids.update(prefix + n for n in rest.strip("/").split("/"))
        else:
            ids.update(t for t in chunk.split("/") if t)
    return ids


def _git_author_overlap(run_dir):
    """run 目录所在仓库：当前 git 用户是否是最近 50 次提交的作者之一。任何失败都当作"不可判"。"""
    try:
        git = lambda *a: subprocess.run(["git", "-C", str(run_dir), *a], capture_output=True, text=True,
                                        timeout=5, check=True).stdout.strip()
        email = git("config", "user.email")
        authors = set(git("log", "-n", "50", "--format=%ae").splitlines())
        return email if email and email in authors else ""
    except Exception:
        return ""


def _timing_lines(admitted):
    """v2 的 probed_at：打印取证跨度，相邻 runtime 问间隔不足 60 秒逐对点名——不是证据，是让人看一眼的线索。"""
    stamped = [(e, _parse_time(e.get("probed_at"))) for e in admitted]
    stamped = [(e, t) for e, t in stamped if t]
    if not stamped:
        return []
    times = [t for _, t in stamped]
    span = max(times) - min(times)
    out = [f"取证时间：首问 {min(times).isoformat()} · 末问 {max(times).isoformat()} · 跨 {int(span.total_seconds() // 60)} 分钟"]
    fast = []
    for (a, ta), (b, tb) in zip(stamped, stamped[1:]):
        if a.get("medium") == "runtime" and b.get("medium") == "runtime" and abs((tb - ta).total_seconds()) < 60:
            fast.append(f"{a.get('q', '?')} → {b.get('q', '?')}（{int(abs((tb - ta).total_seconds()))} 秒）")
    if fast:
        out.append("相邻 runtime 问间隔不足 60 秒，请核对是否真实取证：" + "；".join(fast))
    return out


def _requirement_section(requirements, facets, examined_ids, admitted):
    by_req = {}
    for e in admitted:
        for rid in _requirement_ids(e):
            by_req.setdefault(rid, []).append(e)
    covered = [r for r in requirements if r.get("id") in by_req]
    uncovered = [r for r in requirements if r.get("id") not in by_req]
    out = ["", f"## 需求覆盖（基准 {len(requirements)} 条，有裁决 {len(covered)} 条，"
               f"无裁决 {len(uncovered)} 条）"]
    for r in covered:
        verdicts = " · ".join(f"{VERDICT_LABELS[e['verdict']]}（{e.get('q', '?')}）"
                              for e in by_req[r["id"]])
        out.append(f"- {r['id']} {r.get('text', '')} — {verdicts}")
    for r in uncovered:
        holders = [f for f in facets if r.get("id") in (f.get("requirement_refs") or [])]
        if not holders:
            why = "未落任何面"
        else:
            why = "；".join(f"面 {f['id']} {'已盘问但无裁决引用它' if f['id'] in examined_ids else '未盘问'}"
                           for f in holders)
        out.append(f"- {r['id']} {r.get('text', '')} — 无裁决（{why}）")
    return out


def _assign_gap_ids(plain):
    """按 ledger 先后给普通 gap|drift 编 G 号（不按严重度）。续盘只追加不重排，编号稳定；
    被拒渲的不占号；旅程 entry 用 J 号，不占 G 号。product-review 的 depends_on 引用它。"""
    n = 0
    for e in plain:
        if e.get("verdict") in ("gap", "drift"):
            n += 1
            e["gap_id"] = f"G{n}"


STEP_STATUSES = ("done", "stuck", "could_not")
STEP_FAILURE_STATUSES = ("stuck", "could_not")


def _step_verdict_reason(e):
    """旅程 steps 的两条底线：① 每步 status 只能是 done/stuck/could_not 之一——这是台账形状的
    最低要求，不看 verdict，"Stuck"/"STUCK" 这种大小写花招在这里就是非法值，不是漏网的 stuck；
    ② entry 判 done 时自己的 steps 里就不能有 stuck / could_not。

    实测官返回的逐步 status 是它当场的观察；把 entry 改成 done 而不动这些 status，
    裁决就跑在了证据前面。这一层只看 entry 自身，不需要 transcript。"""
    if not e.get("journey"):
        return ""
    steps = e.get("steps")
    if steps is None:
        return ""
    if not isinstance(steps, list):
        return "旅程 steps 须是列表"
    verdict_done = e.get("verdict") == "done"
    for index, step in enumerate(steps):
        if not isinstance(step, dict):
            return f"旅程 steps 第 {index + 1} 项不是对象"
        status = step.get("status")
        if status not in STEP_STATUSES:
            return f"旅程第 {step.get('n', index + 1)} 步状态不是 done/stuck/could_not 之一：{status}"
        if verdict_done and status in STEP_FAILURE_STATUSES:
            return (f"旅程判 done，但第 {step.get('n', index + 1)} 步实测官报 {status}"
                    f"（{step.get('action', '')}）：裁决不能跑在自己的证据前面")
    return ""


def _refusal_reason(e, journey_ids):
    verdict = e.get("verdict")
    if verdict not in VERDICT_LABELS:
        return f"非法裁决：{verdict}"
    if e.get("journey") and e["journey"] not in journey_ids:
        return f"旅程引用不存在：{e['journey']}"
    if e.get("journey") and verdict == "gap" and e.get("stuck_kind") not in STUCK_KINDS:
        return f"非法卡死类型：{e.get('stuck_kind')}"
    if e.get("journey") and verdict == "drift" and not e.get("missed_waypoints"):
        return "缺 missed_waypoints"
    step_reason = _step_verdict_reason(e)
    if step_reason:
        return step_reason
    if verdict in ("gap", "drift") and e.get("severity") not in SEVERITY_ORDER:
        return f"非法严重度：{e.get('severity')}"
    return None


def _journey_body(j):
    return f"{j.get('who', '?')} · {j.get('circumstance', '?')} · {j.get('progress', '?')}"


def _journey_title(j):
    return f"{j.get('id', '?')} {_journey_body(j)}"


def _dangling_note(j, admitted):
    jid = j.get("id")
    if not jid:
        return ""
    notes = [e.get("q", "?") for e in admitted
             if e.get("journey") == jid and e.get("q") != j.get("entry_q")]
    return "".join(f" · 有 journey={jid} 的 entry 但 entry_q 对不上：{q}" for q in notes)


def _journey_block(j, e):
    steps = e.get("steps", [])
    verdict = e.get("verdict")
    label = VERDICT_LABELS[verdict]
    ev = e.get("evidence", {})
    note = "".join(f" · {e[k]}" for k in ("transcript_note", "author_note") if e.get(k))
    if verdict == "done":
        head = f"走通，{len(steps)} 步"
    elif verdict == "gap":
        label = f"{label}（{e.get('severity', '?')}，{STUCK_KINDS.get(e.get('stuck_kind'))}）"
        stuck = next((s for s in steps if s.get("status") == "stuck"), None)
        if stuck:
            head = (f"走了 {len(steps)} 步，卡在第 {stuck.get('n', '?')} 步："
                    f"{stuck.get('action', '')} → {stuck.get('observed', '')}")
        else:
            head = f"走了 {len(steps)} 步，预算内未到进展"
    elif verdict == "drift":
        label = f"{label}（{e.get('severity', '?')}）"
        head = "走通但绕过 waypoint：" + "、".join(e.get("missed_waypoints", []))
    else:
        head = ev.get("key_observation", "")
    out = ["", f"### {_journey_title(j)} — {label}",
           f"{head}（证据：{ev.get('dir', '')}）{note}"]
    out.extend(f"- {s.get('n', '?')} {s.get('status', '?')} {s.get('action', '')}"
               f" → {s.get('observed', '')}" for s in steps)
    return out


def render(run_dir):
    run_dir = Path(run_dir)
    ledger = _load(run_dir)
    journeys = ledger.get("journeys") or []
    journey_ids = {j.get("id") for j in journeys}
    admitted, refused, author_gates, author_context = [], [], [], []
    for e in ledger["entries"]:
        if "author" in e:   # 交付流水线写的：机械门或上下文，从来不是裁决
            reason = _author_reason(e, run_dir)
            if reason:
                e["refusal_reason"] = reason
                refused.append(e)
            elif e.get("medium") in GATE_MEDIA:
                e["gate_state"] = GATE_STATES[e["verdict"]]
                author_gates.append(e)
            else:
                author_context.append(e)
            continue
        reason = _refusal_reason(e, journey_ids)
        if not reason:
            reason = visual_reason(e, ledger, run_dir)
        if not reason and not _has_evidence(e, run_dir):
            reason = "无证据目录"
        if not reason and ledger.get("ledger_version", 1) >= 2:
            reason = _content_reason(e, run_dir) or _transcript_reason(e, run_dir, journeys)
        if not reason:
            missing = _missing_step_files(e, run_dir)
            if missing:
                reason = "步骤证据文件缺失：" + "、".join(missing)
        if reason:
            e["refusal_reason"] = reason
            refused.append(e)
        else:
            admitted.append(e)
    admitted_by_q = {e.get("q"): e for e in admitted}
    # 没有独立实测官 entry 的机械门入账为无法自证并说明为什么——作者写的任何东西都关不掉一个裁决
    gate_alone = [g for g in author_gates if g.get("q") not in admitted_by_q]
    for g in gate_alone:
        g["author_note"] = GATE_ALONE_NOTE.format(medium=g.get("medium"), state=g["gate_state"])
        g["verdict"] = "unprovable"
    plain = [e for e in admitted if not e.get("journey")] + gate_alone
    _assign_gap_ids(plain)
    examined_j = [(j, admitted_by_q[j.get("entry_q")]) for j in journeys
                  if j.get("entry_q") in admitted_by_q
                  and admitted_by_q[j.get("entry_q")].get("journey") == j.get("id")
                  and j.get("id")]
    examined_j_ids = {j.get("id") for j, _ in examined_j}
    unexamined_j = [j for j in journeys if j.get("id") not in examined_j_ids]

    facets_with_entry = {e.get("facet") for e in admitted + gate_alone}
    facets_with_verdict = {e.get("facet") for e in admitted if e.get("verdict") in ("done", "gap", "drift")}
    examined = [f for f in ledger["facets"] if f.get("id") in facets_with_entry]
    only_unprovable = [f for f in examined if f.get("id") not in facets_with_verdict]
    not_examined = [f for f in ledger["facets"] if f.get("id") not in facets_with_entry]
    examined_ids = {f.get("id") for f in examined}

    surfaces = ledger.get("surfaces")
    surface_by_id = {s.get("id"): s for s in (surfaces or [])}
    touched, unknown_by_facet = set(), {}
    for e in admitted:
        for sid in e.get("surfaces") or []:
            if sid in surface_by_id:
                touched.add(sid)
            else:
                unknown_by_facet.setdefault(e.get("facet"), []).append(sid)
    counts = {v: 0 for v in VERDICT_LABELS}
    for e in plain:
        counts[e["verdict"]] += 1
    jcounts = {v: 0 for v in VERDICT_LABELS}
    for _, e in examined_j:
        jcounts[e["verdict"]] += 1

    out = [f"# 完成度报告 — {ledger['target']}", ""]
    head = (f"需求基准：{ledger['baseline']} · 共 {len(ledger['facets'])} 面，"
            f"盘问 {len(examined) - len(only_unprovable)} 面"
            + (f"（另 {len(only_unprovable)} 面仅无法自证）" if only_unprovable else "")
            + f" · 实测 {len(plain)} 问")
    if journeys:
        head += f" · 旅程 {len(journeys)} 条，盘问 {len(examined_j)} 条"
    if surfaces is not None:
        head += f" · 操作面 {len(surface_by_id)} 个，裁决触及 {len(touched)} 个"
    out.append(head)
    out.append("")
    out.append("## 总览")
    out.append("")
    by_medium = {m: 0 for m in ("runtime", "code", "ledger")}
    for e in plain:
        if e.get("verdict") == "done" and e.get("medium") in by_medium:
            by_medium[e["medium"]] += 1
    done_split = (f"（运行时 {by_medium['runtime']} · 代码 {by_medium['code']}"
                  f" · 台账 {by_medium['ledger']}）")
    out.append(" · ".join(f"{VERDICT_LABELS[v]}：{counts[v]}"
                          + (done_split if v == "done" and counts[v] else "")
                          for v in VERDICT_LABELS))
    if journeys:
        out.append("旅程裁决：" + " · ".join(f"{VERDICT_LABELS[v]}：{jcounts[v]}"
                                          for v in VERDICT_LABELS))
    if ledger["baseline"] == "none":
        out.append("")
        out.append(f"> {BASELINE_NONE_NOTE}")
    detected = "" if ledger.get("examiner_is_author") else _git_author_overlap(run_dir)
    if ledger.get("examiner_is_author"):
        out.append("")
        out.append(f"> {AUTHOR_NOTE}")
    elif detected:
        out.append("")
        out.append(f"> {AUTHOR_DETECTED_NOTE.format(email=detected)}")
    if author_gates or author_context:
        out.append("")
        out.append("> " + AUTHOR_EVIDENCE_NOTE.format(
            pipelines="、".join(sorted({e["author"]["pipeline"] for e in author_gates + author_context})),
            gates=len(author_gates), context=len(author_context)))
    policy = ledger.get("model_policy")
    if isinstance(policy, dict):
        out.append("")
        judgment = policy.get("judgment", "session")
        if judgment != "session":
            out.append(f"> 非法模型策略：judgment 只能是 session，ledger 写了 {judgment}——普查官 / 视觉 reviewer / 复核官不可降档。")
        obs = policy.get("observation") or "session"
        out.append(f"> 本 run 取证类子 agent（实测官、枚举官）用 {obs}，用户于 {policy.get('confirmed_at', '?')} 确认："
                   f"「{policy.get('confirmed_by_user', '')}」。裁决与普查仍用会话模型。")
        rec = policy.get("recommended")
        if isinstance(rec, dict) and rec.get("option"):
            out.append(f"> 定靶时盘问官推荐的是选项 {rec['option']}（{rec.get('why', '')}）。")
        for past in policy.get("history") or []:
            if isinstance(past, dict):
                out.append(f"> 此前策略：取证用 {past.get('observation', '?')}，用户于 {past.get('confirmed_at', '?')} 确认；"
                           f"那段时间落账的 entry 以各自 `agent_model` 为准。")
    backend = ledger.get("target_backend") or {}
    if backend.get("kind") in ("mock", "mixed"):
        out.append("")
        out.append(f"> 本 run 的开发实例后端为 {backend['kind']}（{backend.get('how_known', '')}）：runtime 裁决经过 mock 层，"
                   "渲染器已拒收经 mock 的 done。")
    timing = _timing_lines(admitted)
    if timing:
        out.append("")
        out.extend(timing)

    requirements = ledger.get("requirements")
    if requirements is not None:
        out.extend(_requirement_section(requirements, ledger["facets"], examined_ids, admitted))

    out.append("")
    out.append("## 逐面完成度")
    for f in examined:
        fe = [e for e in plain if e.get("facet") == f["id"]]
        done = len([e for e in fe if e.get("verdict") == "done"])
        title = f"### {f['name']}（{f['id']}）— {len(fe)} 问中 {done} 问实证通过"
        if surfaces is not None:
            sids = [sid for sid in (f.get("surface_ids") or []) if sid in surface_by_id]
            if sids:
                missed = [sid for sid in sids if sid not in touched]
                title += f" · 操作面 {len(sids)} 个，裁决触及 {len(sids) - len(missed)} 个"
                if missed:
                    title += "，未触及：" + "、".join(
                        f"{sid} {surface_by_id[sid].get('name', '')}" for sid in missed)
            else:
                title += " · 操作面未登记，覆盖不可算"
            if unknown_by_facet.get(f["id"]):
                title += " · 未登记的操作面 id：" + "、".join(unknown_by_facet[f["id"]])
        out.append("")
        out.append(title)
        for e in fe:
            line = _entry_line(e)
            if surfaces is not None and "surfaces" not in e:
                line += " · 本问未登记触及的操作面"
            out.append(line)

    out.append("")
    out.append("## 旅程完成度")
    if examined_j:
        for j, e in examined_j:
            out.extend(_journey_block(j, e))
    else:
        out.append("（无旅程声明）" if not journeys else "（旅程均未盘问，见未盘问声明）")

    gaps = [e for e in admitted if e.get("verdict") in ("gap", "drift")]
    gaps.sort(key=lambda e: SEVERITY_ORDER.get(e.get("severity"), 3))
    out.append("")
    out.append("## 缺口清单（按严重度）")
    if gaps:
        out.extend(f"- **{e.get('severity', '?')}** {_entry_line(e)[2:]}" for e in gaps)
    else:
        out.append("（无）")

    unprov = [e for e in admitted + gate_alone if e.get("verdict") == "unprovable"]
    out.append("")
    out.append("## 无法自证清单（待人工验证，不计为完成也不计为失败）")
    if unprov:
        out.extend(_entry_line(e) for e in unprov)
    else:
        out.append("（无）")

    out.append("")
    out.append("## 未盘问声明（按风险排序）")
    unexamined_items = ([(f["name"], f, "facet") for f in not_examined]
                        + [("旅程 " + _journey_body(j), j, "journey") for j in unexamined_j])
    if unexamined_items:
        unexamined_items.sort(key=lambda it: _risk_key(it[1]))
        for name, item, kind in unexamined_items:
            line = _not_examined_line(name, item)
            if kind == "journey":
                line += _dangling_note(item, admitted)
            out.append(line)
    else:
        out.append("（所有面均已盘问或部分盘问）")

    threads = ledger.get("open_threads", [])
    out.append("")
    out.append("## 未拉的线（已发现泄漏点、未实测——续盘从这里接手）")
    if threads:
        out.extend(f"- [{t.get('facet', '?')}] {t.get('q', '?')} — "
                   f"泄漏点：{t.get('leak_point', '')}" for t in threads)
    else:
        out.append("（无）")

    patterns = ledger.get("patterns", [])
    out.append("")
    out.append("## 缺陷模式（同类位点清点——未查位点不进任何完成度）")
    if patterns:
        for p in patterns:
            sites = p.get("sites", [])
            proven = [(s, admitted_by_q[s["entry_q"]]) for s in sites
                      if s.get("entry_q") in admitted_by_q]
            unexamined = [s for s in sites
                          if s.get("entry_q") not in admitted_by_q]
            out.append("")
            not_enum = ("" if p.get("enumerated", True)
                        else "（枚举官无返回，同类位点全集未清点）")
            out.append(f"### {p.get('pattern_id', '?')} {p.get('hypothesis', '?')}"
                       f" — 共 {len(sites)} 位点：实证 {len(proven)}，"
                       f"未查 {len(unexamined)}{not_enum}")
            for s, e in proven:
                label = VERDICT_LABELS.get(e.get("verdict"), e.get("verdict"))
                out.append(f"- **{label}** {s.get('site', '?')}"
                           f" — {e.get('q', '?')}")
            for s in unexamined:
                out.append(f"- **未查** {s.get('site', '?')}"
                           f"（[{s.get('facet', '?')}] 同类嫌疑，未实证）")
    else:
        out.append("（无）")

    if author_gates or author_context:
        out.append("")
        out.append("## 作者证据（交付流水线写入——机械门核验后只作门，运行时只作上下文，都不是裁决）")
        out.extend(_author_line(e, admitted_by_q) for e in author_gates + author_context)

    out.extend(visual_section(ledger, admitted, run_dir))

    if refused:
        out.append("")
        out.append("## 违规裁决（无证据或非法裁决，已拒渲）")
        out.append(f"以下 {len(refused)} 条 entry 不计入任何统计：")
        for e in refused:
            out.append(f"- {e.get('q', '?')}（{e.get('refusal_reason', '?')}）")

    out.append("")
    return "\n".join(out)


def main(argv):
    if len(argv) != 2:
        raise SystemExit(__doc__)
    run_dir = Path(argv[1])
    report = render(run_dir)
    (run_dir / "completion-report.md").write_text(report, encoding="utf-8")
    print(f"wrote {run_dir / 'completion-report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
