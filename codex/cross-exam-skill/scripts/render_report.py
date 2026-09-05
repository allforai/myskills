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

Usage: python3 render_report.py <run_dir>    # run_dir 内含 ledger.json
写出 <run_dir>/completion-report.md。exit 0=渲染成功（有拒渲仍为 0，报告内声明）；
exit 1=ledger 不可读或缺必填键。
"""
import json
import sys
from pathlib import Path

VERDICT_LABELS = {"done": "实证完成", "gap": "缺口",
                  "drift": "跑偏", "unprovable": "无法自证"}
SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}
STUCK_KINDS = {"no_entry": "无入口", "not_found": "找不到", "misleading": "误导",
               "no_feedback": "无反馈", "no_recovery": "无恢复路径", "broken": "系统报错"}
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
    if verdict in ("gap", "drift") and e.get("severity") not in SEVERITY_ORDER:
        return f"非法严重度：{e.get('severity')}"
    if e.get("journey") and e["journey"] not in journey_ids:
        return f"旅程引用不存在：{e['journey']}"
    if e.get("journey") and verdict == "gap" and e.get("stuck_kind") not in STUCK_KINDS:
        return f"非法卡死类型：{e.get('stuck_kind')}"
    if e.get("journey") and verdict == "drift" and not e.get("missed_waypoints"):
        return "缺 missed_waypoints"
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
        if not reason and not _has_evidence(e, run_dir):
            reason = "无证据目录"
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

    examined = [f for f in ledger["facets"] if f.get("status") != "not_examined"]
    not_examined = [f for f in ledger["facets"] if f.get("status") == "not_examined"]
    counts = {v: 0 for v in VERDICT_LABELS}
    for e in plain:
        counts[e["verdict"]] += 1
    jcounts = {v: 0 for v in VERDICT_LABELS}
    for _, e in examined_j:
        jcounts[e["verdict"]] += 1

    out = [f"# 完成度报告 — {ledger['target']}", ""]
    head = (f"需求基准：{ledger['baseline']} · 共 {len(ledger['facets'])} 面，"
            f"盘问 {len(examined)} 面 · 实测 {len(plain)} 问")
    if journeys:
        head += f" · 旅程 {len(journeys)} 条，盘问 {len(examined_j)} 条"
    out.append(head)
    out.append("")
    out.append("## 总览")
    out.append("")
    out.append(" · ".join(f"{VERDICT_LABELS[v]}：{counts[v]}" for v in VERDICT_LABELS))
    if journeys:
        out.append("旅程裁决：" + " · ".join(f"{VERDICT_LABELS[v]}：{jcounts[v]}"
                                          for v in VERDICT_LABELS))
    if ledger["baseline"] == "none":
        out.append("")
        out.append(f"> {BASELINE_NONE_NOTE}")
    if ledger.get("examiner_is_author"):
        out.append("")
        out.append(f"> {AUTHOR_NOTE}")

    out.append("")
    out.append("## 逐面完成度")
    for f in examined:
        fe = [e for e in plain if e.get("facet") == f["id"]]
        done = len([e for e in fe if e.get("verdict") == "done"])
        out.append("")
        out.append(f"### {f['name']}（{f['id']}）— {len(fe)} 问中 {done} 问实证通过")
        out.extend(_entry_line(e) for e in fe)

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
