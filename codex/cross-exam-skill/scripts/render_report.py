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

Usage: python3 render_report.py <run_dir>    # run_dir 内含 ledger.json
写出 <run_dir>/completion-report.md。exit 0=渲染成功（有拒渲仍为 0，报告内声明）；
exit 1=ledger 不可读或缺必填键。
"""
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PATH_LINE = re.compile(r'[\w./\-]+\.[A-Za-z0-9]+:\d+')
IMAGE_SUFFIXES = {'.png', '.jpg', '.jpeg'}

import importlib.util

# Load this package's own visual validator by path under a unique module name: a `validation`
# module already on sys.path (another package, a test process) must never stand in for it.
_VISUAL_VALIDATION = Path(__file__).resolve().parents[1] / "visual/validation.py"
_spec = importlib.util.spec_from_file_location("cross_exam_visual_validation", _VISUAL_VALIDATION)
_visual = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_visual)
visual_reason, visual_section = _visual.visual_reason, _visual.visual_section

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
    d = (entry.get("evidence") or {}).get("dir")
    if not d:
        return False
    p = Path(d) if Path(d).is_absolute() else run_dir / d
    p = p.resolve()
    evidence_root = (run_dir / "evidence").resolve()
    if evidence_root not in p.parents:
        return False
    return p.is_dir() and any(p.iterdir())


def _evidence_files(entry, run_dir):
    d = (entry.get("evidence") or {}).get("dir") or ""
    p = Path(d) if Path(d).is_absolute() else run_dir / d
    return [f for f in p.iterdir() if f.is_file()] if p.is_dir() else []


def _content_reason(e, run_dir):
    """ledger_version 2 的证据内容门：目录非空只说明有文件，不说明有取证。
    code 介质要有 路径:行号 的摘录；runtime 介质要有截图或输出文件、且不少于当初要求的状态数，并记请求去向；
    unprovable 的原因文件要写得出尝试了什么；经过 mock 层的 runtime 不能算 done。"""
    if not _parse_time(e.get("probed_at")):
        return "缺 probed_at（ISO 8601）"
    files = _evidence_files(e, run_dir)
    medium, verdict = e.get("medium"), e.get("verdict")
    text = "".join(f.read_text(encoding="utf-8", errors="ignore") for f in files if f.suffix not in IMAGE_SUFFIXES)
    if verdict == "unprovable":
        return "" if len(text.strip()) >= 40 else "无法自证缺原因文件（尝试了什么、卡在哪）"
    if medium == "code" and not PATH_LINE.search(text):
        return "代码摘录无 路径:行号"
    if medium == "runtime":
        images = [f for f in files if f.suffix.lower() in IMAGE_SUFFIXES]
        outputs = [f for f in files if f.suffix.lower() in {".txt", ".log", ".json", ".md"}]
        if not images and not outputs:
            return "运行时证据无截图或输出文件"
        wanted = e.get("states_to_capture")
        if isinstance(wanted, list) and wanted and len(files) < len(wanted):
            return f"要求 {len(wanted)} 个状态只落了 {len(files)} 个文件"
        served = e.get("served_by")
        if not isinstance(served, dict) or not served.get("host") or not served.get("process") \
                or not isinstance(served.get("mock_layers"), list):
            return "缺请求去向 served_by（host / process / mock_layers）"
        if served["mock_layers"] and verdict == "done":
            return "经 mock 层（" + ", ".join(map(str, served["mock_layers"])) + "）的 runtime 不能判 done"
    return ""


def _transcript_reason(e, run_dir):
    """实测官 transcript 核对：ledger 记了子 agent 的 output_file，transcript 就必须能证明证据是实测官写的——
    证据目录里每个文件名都出现在 transcript 里，或 transcript 提到过该证据目录（脚本循环生成的文件名不会
    逐个出现，但写入目录会）。两者都没有，拒渲。文件不在（换机器、临时目录已清）只标不可核，不拒渲。"""
    task = e.get("agent_task") or {}
    out = task.get("output_file")
    if not out:
        return ""
    p = Path(out)
    if not p.is_file():
        e["transcript_note"] = "transcript 不可核（文件不在）"
        return ""
    body = p.read_text(encoding="utf-8", errors="ignore")
    names = [f.name for f in _evidence_files(e, run_dir)]
    absent = [n for n in names if n not in body]
    if not names or not absent:
        return ""
    d = ((e.get("evidence") or {}).get("dir") or "").strip().rstrip("/")
    d = d[2:] if d.startswith("./") else d
    if d and d in body:
        return ""
    return "证据文件未出现在实测官 transcript，transcript 也未提及证据目录 %s：%s" % (d or "?", "、".join(absent))


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
    return (f"- **{label}**{jtag}{gtag}{facet_tag}{ref} {e.get('q', '?')} — {ev.get('key_observation', '')}"
            f"（证据：{ev.get('dir', '')}）")


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


def _parse_time(value):
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


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
           f"{head}（证据：{ev.get('dir', '')}）"]
    out.extend(f"- {s.get('n', '?')} {s.get('status', '?')} {s.get('action', '')}"
               f" → {s.get('observed', '')}" for s in steps)
    return out


def render(run_dir):
    run_dir = Path(run_dir)
    ledger = _load(run_dir)
    journeys = ledger.get("journeys") or []
    journey_ids = {j.get("id") for j in journeys}
    admitted, refused = [], []
    for e in ledger["entries"]:
        reason = _refusal_reason(e, journey_ids)
        if not reason:
            reason = visual_reason(e, ledger, run_dir)
        if not reason and not _has_evidence(e, run_dir):
            reason = "无证据目录"
        if not reason and ledger.get("ledger_version", 1) >= 2:
            reason = _content_reason(e, run_dir) or _transcript_reason(e, run_dir)
        if not reason:
            missing = _missing_step_files(e, run_dir)
            if missing:
                reason = "步骤证据文件缺失：" + "、".join(missing)
        if reason:
            e["refusal_reason"] = reason
            refused.append(e)
        else:
            admitted.append(e)
    plain = [e for e in admitted if not e.get("journey")]
    _assign_gap_ids(plain)
    admitted_by_q = {e.get("q"): e for e in admitted}
    examined_j = [(j, admitted_by_q[j.get("entry_q")]) for j in journeys
                  if j.get("entry_q") in admitted_by_q
                  and admitted_by_q[j.get("entry_q")].get("journey") == j.get("id")
                  and j.get("id")]
    examined_j_ids = {j.get("id") for j, _ in examined_j}
    unexamined_j = [j for j in journeys if j.get("id") not in examined_j_ids]

    facets_with_entry = {e.get("facet") for e in admitted}
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
    policy = ledger.get("model_policy")
    if isinstance(policy, dict):
        out.append("")
        judgment = policy.get("judgment", "session")
        if judgment != "session":
            out.append(f"> 非法模型策略：judgment 只能是 session，ledger 写了 {judgment}——普查官 / 视觉 reviewer / 复核官不可降档。")
        obs = policy.get("observation") or "session"
        out.append(f"> 本 run 取证类子 agent（实测官、枚举官）用 {obs}，用户于 {policy.get('confirmed_at', '?')} 确认："
                   f"「{policy.get('confirmed_by_user', '')}」。裁决与普查仍用会话模型。")
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

    unprov = [e for e in admitted if e.get("verdict") == "unprovable"]
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
