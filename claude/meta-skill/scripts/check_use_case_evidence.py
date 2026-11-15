#!/usr/bin/env python3
"""product-verify gate — every use case is walked, and the walk is shown (ADR-0010 receiver guard).

product-analysis writes the acceptance cases (`.allforai/use-case/use-case-tree.json`, Given / When /
Then); product-verify is the node that walks them. This gate joins the two: a case nobody walked is
named, a case with an interface is admitted only with frames a person can look at — the state it
started from and the outcome it ended in — and a recording never stands in for frames, because the
reviewer judged stills. It then renders the human report from the same records, so the report cannot
say what the ledger does not. It decides coverage and shape, never whether the product is good: a
walked case that failed is a `gap` entry, reported here and judged by the node's own verdict.

Usage: check_use_case_evidence.py --run .allforai/product-verify [--root .] [--cases <path>] [--partial]
  --partial   a split product-verify node that is not the last one: shape is checked and the report is
              rendered, cases nobody has walked yet do not fail the gate.
Exit 0 admitted, 1 refused (every reason printed).
"""
import argparse
import html
import json
import sys
from pathlib import Path

CASES = ".allforai/use-case/use-case-tree.json"
REPORT = "use-case-report.html"
ENTRIES_DIR = "evidence-entries"
CLAUSES = ("given", "when", "then")
KINDS = ("happy", "exception", "boundary")
VIDEO_SUFFIXES = {".mp4", ".webm", ".mov", ".gif"}
UPSTREAM = "上游缺陷（product-analysis）："
# worst first: a case walked on several clients shows the worst of them
VERDICT_ORDER = ("gap", "drift", "unprovable", "done")
LABELS = {"done": "通过", "gap": "未通过", "drift": "与设计不一致", "unprovable": "无法验证",
          "missing": "未验收", "out_of_scope": "本期不做"}
CLAUSE_LABELS = {"given": "前置 Given", "when": "操作 When", "then": "结果 Then"}


def _text(value):
    """A clause as one string: a string, or a list of strings joined by line."""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list) and all(isinstance(v, str) for v in value):
        return "\n".join(v.strip() for v in value if v.strip())
    return ""


def load_cases(path):
    """(cases, reasons). Every reason is an upstream defect: the gate never repairs or invents a case."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError) as exc:
        return [], [UPSTREAM + "用例文件读不到 %s（%s）" % (path, exc)]
    cases = data.get("cases") if isinstance(data, dict) else None
    if not isinstance(cases, list) or not cases:
        return [], [UPSTREAM + "用例文件缺 cases 列表或为空"]
    reasons, seen = [], set()
    for index, case in enumerate(cases, 1):
        cid = case.get("id") if isinstance(case, dict) else None
        if not isinstance(cid, str) or not cid.strip():
            reasons.append(UPSTREAM + "第 %d 条用例缺 id" % index)
            continue
        if cid in seen:
            reasons.append(UPSTREAM + "用例 id 重复: " + cid)
        seen.add(cid)
        for clause in CLAUSES:
            if not _text(case.get(clause)):
                reasons.append(UPSTREAM + "用例 %s 缺 %s" % (cid, clause))
        if case.get("kind") not in KINDS:
            reasons.append(UPSTREAM + "用例 %s 的 kind 须为 %s" % (cid, " | ".join(KINDS)))
        refs = case.get("screen_refs")
        if not isinstance(refs, list) or any(not isinstance(r, str) or not r.strip() for r in refs):
            reasons.append(UPSTREAM + "用例 %s 缺 screen_refs（无界面写 []）" % cid)
    return [c for c in cases if isinstance(c, dict)], reasons


def load_entries(run_dir):
    """Every case-bound entry under the run, whichever product-verify node wrote it."""
    found = []
    for path in sorted((Path(run_dir) / ENTRIES_DIR).glob("*.json")):
        try:
            entries = json.loads(path.read_text(encoding="utf-8")).get("entries")
        except (OSError, ValueError, UnicodeError, AttributeError):
            continue   # an unreadable entries file is check_evidence.py's refusal, not this gate's
        for entry in entries if isinstance(entries, list) else []:
            if isinstance(entry, dict) and entry.get("case") is not None:
                found.append(entry)
    return found


def _inside(directory, ref):
    """The file `ref` names inside `directory`, or None when it escapes it or is not a file."""
    if not isinstance(ref, str) or not ref.strip():
        return None
    path = (directory / ref).resolve()
    return path if directory.resolve() in path.parents and path.is_file() else None


def entry_reason(entry, case, run_dir):
    """'' when a case-bound entry shows what it claims; otherwise the rule it breaks."""
    cid = entry.get("case")
    if case is None:
        return "条目指向不存在的用例: %s" % cid
    evidence = entry.get("evidence") if isinstance(entry.get("evidence"), dict) else {}
    directory = Path(run_dir) / str(evidence.get("dir") or "")
    verdict = entry.get("verdict")
    video = entry.get("video")
    if video is not None:
        path = _inside(directory, video)
        if path is None or path.suffix.lower() not in VIDEO_SUFFIXES:
            return "用例 %s 的录像不在证据目录内或不是视频文件: %s" % (cid, video)
    if not case.get("screen_refs") or verdict == "unprovable":
        return ""   # no interface to show, or a reason file says why nothing could be shown
    frames = entry.get("frames")
    if not isinstance(frames, list) or not frames:
        if video is not None:
            return "用例 %s 只有录像没有帧：裁决看的是帧，录像不能代替帧" % cid
        return "用例 %s 有界面却没有帧（frames）" % cid
    images = entry.get("images") if isinstance(entry.get("images"), list) else []
    rank = -1
    for index, frame in enumerate(frames, 1):
        if not isinstance(frame, dict) or frame.get("clause") not in CLAUSES:
            return "用例 %s 第 %d 帧的 clause 须为 given | when | then" % (cid, index)
        if not _text(frame.get("caption")):
            return "用例 %s 第 %d 帧缺说明（caption）" % (cid, index)
        if frame.get("image") not in images or _inside(directory, frame.get("image")) is None:
            return "用例 %s 第 %d 帧的图不在本条目的 images 里或文件不存在: %s" % (cid, index, frame.get("image"))
        if CLAUSES.index(frame["clause"]) < rank:
            return "用例 %s 的帧未按 given → when → then 的顺序排列" % cid
        rank = CLAUSES.index(frame["clause"])
    shown = {frame["clause"] for frame in frames}
    if verdict == "done" and not {"given", "then"} <= shown:
        return "用例 %s 判 done 须同时有 given 帧和 then 帧：没有起点，看不出结果是这次操作带来的" % cid
    return ""


def assess(cases, entries, run_dir):
    """(rows, reasons): one row per case in tree order — status, and the entries that walked it."""
    by_id = {c["id"]: c for c in cases if isinstance(c.get("id"), str)}
    walked, reasons = {}, []
    for entry in entries:
        reason = entry_reason(entry, by_id.get(entry.get("case")), run_dir)
        if reason:
            reasons.append(reason)
        elif entry.get("case") in by_id:
            walked.setdefault(entry["case"], []).append(entry)
    rows = []
    for cid, case in by_id.items():
        mine = walked.get(cid, [])
        verdicts = [e.get("verdict") for e in mine]
        if mine:
            status = next((v for v in VERDICT_ORDER if v in verdicts), "unprovable")
        elif _text(case.get("deferred_by")):
            status = "out_of_scope"
        else:
            status = "missing"
        rows.append({"case": case, "status": status, "entries": mine})
    return rows, reasons


# --- the human report ---

CSS = """
:root{--bg:#fafaf8;--fg:#1c1c1a;--muted:#6b6b66;--line:#deded8;--card:#fff;
--done:#1f7a3d;--gap:#b3261e;--drift:#a35a00;--unprovable:#6b4fa0;--missing:#b3261e;--out_of_scope:#6b6b66}
@media (prefers-color-scheme:dark){:root{--bg:#161614;--fg:#ecece6;--muted:#a0a098;--line:#33332f;--card:#1f1f1c;
--done:#6fcf8a;--gap:#ff8a80;--drift:#ffb95c;--unprovable:#b9a3e8;--missing:#ff8a80;--out_of_scope:#a0a098}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);
font:15px/1.6 system-ui,-apple-system,"PingFang SC","Microsoft YaHei",sans-serif}
main{max-width:1080px;margin:0 auto;padding:24px 16px 64px}h1{font-size:22px;margin:0 0 4px}
.sum{display:flex;flex-wrap:wrap;gap:8px;margin:16px 0 24px}.sum span,.badge{border:1px solid currentColor;
border-radius:999px;padding:1px 10px;font-size:13px;white-space:nowrap}
article{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px;margin:0 0 16px}
header{display:flex;flex-wrap:wrap;gap:8px;align-items:baseline}h2{font-size:17px;margin:0;flex:1 1 240px}
.id,.meta{color:var(--muted);font-size:13px}dl{display:grid;grid-template-columns:max-content 1fr;gap:4px 12px;margin:12px 0}
dt{color:var(--muted);white-space:nowrap}dd{margin:0;white-space:pre-wrap}
.frames{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px;margin:12px 0}
figure{margin:0}img,video{width:100%;border:1px solid var(--line);border-radius:6px;background:#0001;display:block}
video{max-width:560px;margin:12px 0}figcaption{font-size:13px;margin-top:4px}figcaption b{color:var(--muted);font-weight:600}
.none{color:var(--muted);font-size:14px}
""" + "".join(".s-%s{color:var(--%s)}" % (s, s) for s in LABELS)


def _esc(value):
    return html.escape(str(value), quote=True)


def _src(entry, name):
    evidence = entry.get("evidence") if isinstance(entry.get("evidence"), dict) else {}
    return _esc((str(evidence.get("dir") or "").rstrip("/") + "/" + str(name)).lstrip("/"))


def _walk(entry):
    """One walk of a case: where it ran, the recording when there is one, then the frames in order."""
    readback = entry.get("readback") if isinstance(entry.get("readback"), dict) else {}
    where = " · ".join("%s=%s" % (k, v) for k, v in readback.items())
    out = ['<p class="meta"><span class="badge s-%s">%s</span> %s</p>'
           % (_esc(entry.get("verdict")), _esc(LABELS.get(entry.get("verdict"), entry.get("verdict"))), _esc(where))]
    if entry.get("video"):
        out.append('<video controls preload="metadata" src="%s"></video>' % _src(entry, entry["video"]))
    frames = entry.get("frames") if isinstance(entry.get("frames"), list) else []
    if frames:
        out.append('<div class="frames">')
        for frame in frames:
            out.append('<figure><a href="{0}"><img loading="lazy" src="{0}" alt="{2}"></a>'
                       '<figcaption><b>{1}</b> {2}</figcaption></figure>'.format(
                           _src(entry, frame.get("image")), _esc(CLAUSE_LABELS.get(frame.get("clause"), "")),
                           _esc(_text(frame.get("caption")))))
        out.append("</div>")
    evidence = entry.get("evidence") if isinstance(entry.get("evidence"), dict) else {}
    if evidence.get("key_observation"):
        out.append('<p class="meta">观察：%s</p>' % _esc(evidence["key_observation"]))
    return "\n".join(out)


def render(rows):
    counts = {status: sum(1 for r in rows if r["status"] == status) for status in LABELS}
    out = ['<!doctype html><html lang="zh"><head><meta charset="utf-8">',
           '<meta name="viewport" content="width=device-width,initial-scale=1">',
           "<title>用例验收报告</title><style>%s</style></head><body><main>" % CSS,
           "<h1>用例验收报告</h1>",
           '<p class="meta">共 %d 条用例。每条用例按 Given / When / Then 展示实际运行时截下的画面。</p>' % len(rows),
           '<div class="sum">']
    out += ['<span class="s-%s">%s %d</span>' % (s, LABELS[s], counts[s]) for s in LABELS if counts[s]]
    out.append("</div>")
    for row in rows:
        case = row["case"]
        out.append('<article id="%s"><header><h2>%s</h2><span class="id">%s · %s</span>'
                   '<span class="badge s-%s">%s</span></header><dl>'
                   % (_esc(case["id"]), _esc(case.get("title") or case["id"]), _esc(case["id"]),
                      _esc(case.get("kind", "")), row["status"], LABELS[row["status"]]))
        out += ["<dt>%s</dt><dd>%s</dd>" % (CLAUSE_LABELS[c], _esc(_text(case.get(c)))) for c in CLAUSES]
        out.append("</dl>")
        if row["status"] == "out_of_scope":
            out.append('<p class="none">由 %s 推迟，本期不验收。</p>' % _esc(_text(case.get("deferred_by"))))
        elif not row["entries"]:
            out.append('<p class="none">没有人走过这条用例。</p>')
        out += [_walk(entry) for entry in row["entries"]]
        out.append("</article>")
    out.append("</main></body></html>")
    return "\n".join(out) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(prog="check_use_case_evidence.py")
    parser.add_argument("--run", required=True, metavar="RUN_DIR")
    parser.add_argument("--root", default=".")
    parser.add_argument("--cases", default=CASES)
    parser.add_argument("--partial", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    run_dir = Path(args.run) if Path(args.run).is_absolute() else root / args.run
    cases_path = Path(args.cases) if Path(args.cases).is_absolute() else root / args.cases
    cases, reasons = load_cases(cases_path)
    if reasons:
        print("\n".join("REFUSED " + r for r in reasons))
        return 1
    rows, reasons = assess(cases, load_entries(run_dir), run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / REPORT).write_text(render(rows), encoding="utf-8")
    missing = [r["case"]["id"] for r in rows if r["status"] == "missing"]
    if missing and not args.partial:
        reasons.append("没有证据条目的用例（%d）：%s" % (len(missing), ", ".join(missing)))
    counts = ", ".join("%s %d" % (LABELS[s], sum(1 for r in rows if r["status"] == s)) for s in LABELS)
    print("%s — %s" % ((run_dir / REPORT).as_posix(), counts))
    if reasons:
        print("\n".join("REFUSED " + r for r in reasons))
        return 1
    print("OK: %d 条用例均已走过或标明推迟" % len(rows) if not args.partial else "OK（partial）：已有条目形状合格")
    return 0


if __name__ == "__main__":
    sys.exit(main())
