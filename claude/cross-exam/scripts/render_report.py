#!/usr/bin/env python3
"""cross-exam 完成度报告渲染器（确定性，禁止口述生成报告）。

诚实性红线在这里、在代码里，不在嘱咐里：
- status=="not_examined" 的面不进任何完成度统计，只进"未盘问声明"；
- 无证据 entry（缺 evidence.dir / 目录不存在 / 目录为空）拒绝渲染进正文与计数，
  在"违规裁决"段点名。合法裁决必有证据（could_not 也要落原因文件），被拒的
  只可能是绕过实测的口头裁决。

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
    return p.is_dir() and any(p.iterdir())


def _entry_line(e):
    label = VERDICT_LABELS.get(e.get("verdict"), e.get("verdict"))
    ref = f" [{e['requirement_ref']}]" if e.get("requirement_ref") else ""
    ev = e.get("evidence", {})
    return (f"- **{label}**{ref} {e['q']} — {ev.get('key_observation', '')}"
            f"（证据：{ev.get('dir', '')}）")


def render(run_dir):
    run_dir = Path(run_dir)
    ledger = _load(run_dir)
    admitted, refused = [], []
    for e in ledger["entries"]:
        (admitted if _has_evidence(e, run_dir) else refused).append(e)

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

    if refused:
        out.append("")
        out.append("## 违规裁决（无证据，已拒渲）")
        out.append(f"以下 {len(refused)} 条 entry 无有效证据目录，"
                   "不计入任何统计：")
        out.extend(f"- {e.get('q', '?')}" for e in refused)

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
