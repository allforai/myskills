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


def _entry_line(e):
    label = VERDICT_LABELS.get(e.get("verdict"), e.get("verdict"))
    facet_tag = f" [{e.get('facet', '?')}]"
    ref = f" [{e['requirement_ref']}]" if e.get("requirement_ref") else ""
    ev = e.get("evidence", {})
    return (f"- **{label}**{facet_tag}{ref} {e.get('q', '?')} — {ev.get('key_observation', '')}"
            f"（证据：{ev.get('dir', '')}）")


def render(run_dir):
    run_dir = Path(run_dir)
    ledger = _load(run_dir)
    admitted, refused = [], []
    for e in ledger["entries"]:
        if e.get("verdict") not in VERDICT_LABELS:
            refused.append(e)
        elif (e.get("verdict") in ("gap", "drift")
              and e.get("severity") not in SEVERITY_ORDER):
            refused.append(e)
        elif _has_evidence(e, run_dir):
            admitted.append(e)
        else:
            refused.append(e)

    examined = [f for f in ledger["facets"] if f.get("status") != "not_examined"]
    not_examined = [f for f in ledger["facets"] if f.get("status") == "not_examined"]
    counts = {v: 0 for v in VERDICT_LABELS}
    for e in admitted:
        if e.get("verdict") in counts:
            counts[e["verdict"]] += 1

    out = [f"# 完成度报告 — {ledger['target']}", ""]
    out.append(f"需求基准：{ledger['baseline']} · 共 {len(ledger['facets'])} 面，"
               f"盘问 {len(examined)} 面 · 实测 {len(admitted)} 问")
    out.append("")
    out.append("## 总览")
    out.append("")
    out.append(" · ".join(f"{VERDICT_LABELS[v]}：{counts[v]}" for v in VERDICT_LABELS))
    if ledger["baseline"] == "none":
        out.append("")
        out.append(f"> {BASELINE_NONE_NOTE}")

    out.append("")
    out.append("## 逐面完成度")
    for f in examined:
        fe = [e for e in admitted if e.get("facet") == f["id"]]
        done = len([e for e in fe if e.get("verdict") == "done"])
        out.append("")
        out.append(f"### {f['name']}（{f['id']}）— {len(fe)} 问中 {done} 问实证通过")
        out.extend(_entry_line(e) for e in fe)

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
    out.append("## 未盘问声明")
    if not_examined:
        out.extend(f"- {f['name']}（{f['id']}）— 未盘问，不计入任何完成度"
                   for f in not_examined)
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

    if refused:
        out.append("")
        out.append("## 违规裁决（无证据或非法裁决，已拒渲）")
        out.append(f"以下 {len(refused)} 条 entry 不计入任何统计：")
        for e in refused:
            verdict = e.get("verdict")
            if verdict not in VERDICT_LABELS:
                reason = f"非法裁决：{verdict}"
            elif verdict in ("gap", "drift") and e.get("severity") not in SEVERITY_ORDER:
                reason = f"非法严重度：{e.get('severity')}"
            else:
                reason = "无证据目录"
            out.append(f"- {e.get('q', '?')}（{reason}）")

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
