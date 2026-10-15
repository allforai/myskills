"""Batch judgments with Jev: the same questions for every row, bucketed by confidence.

  run       --sample N first, then the full run (above batch.calibrate_over rows the full run needs an
            approved sample). Resumable: rows already answered under the same question set are skipped,
            failed rows retried.
  approve   record that the sample was reviewed: how many judgments you disagree with, and what.
  rebucket  re-bucket stored answers under the current thresholds — no requests.
  resolve   record final verdicts (review rows, code-scan hits) next to the results.
  save-set  keep an approved question set for reuse; refused while a rule is mostly false positives.
  export    results -> CSV with final answers and who decided them.
  hits      rows where a noul answer is at or above its upper threshold.
"""
import argparse
import csv
import hashlib
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import jev_config as C  # noqa: E402
from jev_client import JevError, make_caller  # noqa: E402

EXIT_REFUSED = 2
EXIT_NOT_ALLOWED = 3
TYPES = ("choice", "score", "noul")
VALUE_KEYS = ("choice", "score", "noul")
FP_MIN_VERIFIED = 4


class Refused(Exception):
    def __init__(self, message, code=EXIT_REFUSED):
        super().__init__(message)
        self.code = code


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _summary_path(out_path):
    return Path(str(out_path) + ".summary.json")


def _resolutions_path(out_path):
    return Path(str(out_path) + ".resolutions.jsonl")


def load_rows(path):
    rows, seen = [], set()
    for n, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except ValueError:
            raise Refused(f"{path}:{n}: 不是合法 JSON") from None
        if not isinstance(row, dict) or "id" not in row or "state" not in row:
            raise Refused(f"{path}:{n}: 每行需要 id 和 state")
        rid = str(row["id"])
        if rid in seen:
            raise Refused(f"{path}:{n}: id 重复：{rid}")
        seen.add(rid)
        rows.append({"id": rid, "state": row["state"]})
    if not rows:
        raise Refused(f"{path}: 没有数据")
    return rows


def load_questions(path):
    try:
        spec = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise Refused(f"{path}: {e}") from None
    questions = spec.get("questions") if isinstance(spec, dict) else None
    if not isinstance(questions, dict) or not questions:
        raise Refused(f"{path}: 需要非空的 questions 对象")
    for qid, q in questions.items():
        if not isinstance(q, dict) or q.get("type") not in TYPES:
            raise Refused(f"{path}: 题目 {qid} 的 type 必须是 {'/'.join(TYPES)}")
    thresholds = spec.get("thresholds") or {}
    if not isinstance(thresholds, dict):
        raise Refused(f"{path}: thresholds 必须是对象")
    for qid, t in thresholds.items():
        number = isinstance(t, (int, float)) and not isinstance(t, bool)
        band = (isinstance(t, dict) and questions.get(qid, {}).get("type") == "noul" and set(t) <= {"hi", "lo"}
                and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in t.values()))
        if qid not in questions or not (number or band):
            raise Refused(f"{path}: thresholds.{qid} 必须对应一道题，值是数字（noul 也可以是 {{\"hi\", \"lo\"}} 数字）")
    return questions, thresholds


def question_hash(questions, model):
    """Identity of a question set. Thresholds are deliberately excluded: retuning them re-buckets
    stored answers and never needs new requests."""
    blob = json.dumps({"q": questions, "m": model}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:12]


def _noul_band(threshold, bc):
    if isinstance(threshold, (int, float)):
        return threshold, 1 - threshold
    threshold = threshold or {}
    return threshold.get("hi", bc["noul_hi"]), threshold.get("lo", bc["noul_lo"])


def _noul_of(row, qid):
    v = ((row.get("answers") or {}).get(qid) or {}).get("noul")
    return v if isinstance(v, (int, float)) else None


def bucket_for(answers, questions, thresholds, bc):
    reasons = []
    for qid, q in questions.items():
        a = answers.get(qid)
        if not isinstance(a, dict):
            reasons.append(f"{qid}: 没有答案")
        elif q["type"] == "noul":
            hi, lo = _noul_band(thresholds.get(qid), bc)
            v = a.get("noul")
            if not isinstance(v, (int, float)) or lo < v < hi:
                reasons.append(f"{qid}: noul={v} 落在 {lo}–{hi} 之间")
        else:
            t = thresholds.get(qid, bc["default_threshold"])
            c = a.get("confidence")
            if not isinstance(c, (int, float)) or c < t:
                reasons.append(f"{qid}: confidence={c} < {t}")
    return ("review" if reasons else "auto"), reasons


def read_results(out):
    path = Path(out)
    results = {}
    if path.exists():
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
                results[rec["id"]] = rec  # last line per id wins
            except (ValueError, KeyError, TypeError):
                raise Refused(f"{path}:{n}: 不是完整的结果行（多半是上次运行中途被打断）；删掉这一行后重跑") from None
    return results


def read_resolutions(out):
    merged = {}
    path = _resolutions_path(out)
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            d = json.loads(line)
            m = merged.setdefault(d["id"], {"answers": {}, "by": None, "verdicts": {}})
            if d.get("answers"):
                m["answers"].update(d["answers"])
                m["by"] = d["by"]
            if d.get("verdict") and d.get("rule"):
                m["verdicts"][d["rule"]] = d["verdict"]
    return merged


def _state_bytes(state):
    return len((state if isinstance(state, str) else json.dumps(state, ensure_ascii=False)).encode("utf-8"))


def _estimate_usd(rows, questions, bc):
    q_bytes = len(json.dumps(questions, ensure_ascii=False).encode("utf-8"))
    tokens = sum(_state_bytes(r["state"]) + q_bytes for r in rows) / 3  # ~3 UTF-8 bytes per token
    return tokens / 1_000_000 * bc["input_usd_per_mtok"]


def _pick_sample(rows, n):
    n = min(n, len(rows))
    return [rows[i * len(rows) // n] for i in range(n)]


def _calibration(qhash):
    return C.read_json(C.calibrations_path(), {}).get(qhash) or {}


def _refresh_summary(out_path, questions, thresholds, cfg, **fixed):
    path = _summary_path(out_path)
    prev = C.read_json(path, {})
    qhash = question_hash(questions, cfg["model"])
    calib = _calibration(qhash)
    results = [r for r in read_results(out_path).values() if r.get("qhash") == qhash]
    res = read_resolutions(out_path)
    buckets = {}
    for r in results:
        buckets[r["bucket"]] = buckets.get(r["bucket"], 0) + 1
    rules = {}
    for qid, q in questions.items():
        if q["type"] != "noul":
            continue
        hi = _noul_band(thresholds.get(qid), cfg["batch"])[0]
        verdicts = [m["verdicts"].get(qid) for m in res.values()]
        rules[qid] = {"hits": sum(1 for r in results if (_noul_of(r, qid) is not None and _noul_of(r, qid) >= hi)),
                      "confirmed": verdicts.count("confirmed"),
                      "false_positive": verdicts.count("false_positive")}
    summary = {**prev, **fixed,
               "rows_done": len(results),
               "buckets": buckets,
               "qhash": qhash,
               "thresholds": thresholds,
               "models": sorted({r["model"] for r in results if r.get("model")}),
               "input_tokens": sum((r.get("usage") or {}).get("input_tokens") or 0 for r in results),
               "cost_usd": round(sum((r.get("usage") or {}).get("cost") or 0 for r in results), 6),
               "calibrated": bool(calib.get("approved")),
               "calibration": calib or None,
               "resolved": len(res),
               "unresolved_review": sum(1 for r in results if r["bucket"] == "review" and r["id"] not in res),
               "long_context": sum(1 for r in results if r.get("long_context")),
               "rules": rules}
    C.write_json(path, summary)
    return summary


def run(input_path, questions_path, out_path, *, cfg, source=None, sample=None, skip_calibration=None,
        confirm_cost=False, concurrency=None, ask_factory=make_caller):
    bc = cfg["batch"]
    source = source or input_path
    if not C.is_allowed(source):
        raise Refused(f"{source} 不在外发放行清单 {C.config_dir() / 'allow.json'} 里，没有发送任何数据。",
                      EXIT_NOT_ALLOWED)
    rows = load_rows(input_path)
    questions, thresholds = load_questions(questions_path)
    qhash = question_hash(questions, cfg["model"])
    done = read_results(out_path)
    foreign = sorted({str(r.get("qhash")) for r in done.values()} - {qhash})
    if foreign:
        raise Refused(f"{out_path} 里已有另一套题目（{', '.join(foreign)}）的结果；换一个输出路径。")

    if sample:
        targets = _pick_sample(rows, sample)
    else:
        calib = _calibration(qhash)
        if len(rows) > bc["calibrate_over"] and not calib.get("approved") and not skip_calibration:
            if calib.get("sampled"):
                raise Refused("这套题目已试跑但还没 approve：逐条看样本结果，再运行 approve 记录不同意的条数与要点。")
            raise Refused(f"{len(rows)} 行超过 {bc['calibrate_over']} 行，这套题目还没试跑过。"
                          f"先用 --sample {bc['sample']} 试跑并逐条检查结果，再 approve；"
                          "用户明确同意不校准时才用 --skip-calibration \"理由\"。")
        targets = rows
    todo = [r for r in targets if r["id"] not in done or done[r["id"]]["bucket"] == "failed"]

    estimate = _estimate_usd(todo, questions, bc)
    if estimate > bc["cost_cap_usd"] and not confirm_cost:
        raise Refused(f"本次 {len(todo)} 行预计花费约 ${estimate:.2f}，超过上限 ${bc['cost_cap_usd']:.2f}；"
                      "用户确认后加 --confirm-cost 重跑。")

    if todo:
        try:
            ask = ask_factory(cfg, timeout=bc["request_timeout_s"])
        except JevError as e:
            raise Refused(str(e)) from None
        lock = Lock()
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "a", encoding="utf-8") as f:
            def work(row):
                try:
                    res = ask(row["state"], questions)
                    bucket, reasons = bucket_for(res["answers"], questions, thresholds, bc)
                    rec = {"id": row["id"], "qhash": qhash, "bucket": bucket, "reasons": reasons,
                           "answers": res["answers"], "usage": res["usage"], "model": res["model"]}
                except Exception as e:  # never lose a row silently: anything unexpected is a failed record
                    reason = str(e) if isinstance(e, JevError) else f"{type(e).__name__}: {e}"
                    rec = {"id": row["id"], "qhash": qhash, "bucket": "failed", "reasons": [reason],
                           "answers": {}, "usage": {}, "model": None}
                if _state_bytes(row["state"]) > bc["long_context_bytes"]:
                    rec["long_context"] = True
                with lock:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    f.flush()
            with ThreadPoolExecutor(max_workers=concurrency or bc["concurrency"]) as pool:
                list(pool.map(work, todo))

    if sample:
        calibrations = C.read_json(C.calibrations_path(), {})
        calibrations[qhash] = {"sampled": len(targets), "sampled_at": _now()}  # a new sample voids an old approval
        C.write_json(C.calibrations_path(), calibrations)
    fixed = {"rows_total": len(rows), "sample": bool(sample)}
    if skip_calibration:  # a later run without the flag must not erase the recorded reason
        fixed["skip_calibration"] = skip_calibration
    return _refresh_summary(out_path, questions, thresholds, cfg, **fixed)


def approve(out_path, questions_path, cfg, *, disagree, notes, accept_reason=None):
    questions, thresholds = load_questions(questions_path)
    qhash = question_hash(questions, cfg["model"])
    calibrations = C.read_json(C.calibrations_path(), {})
    entry = calibrations.get(qhash)
    if not entry or not entry.get("sampled"):
        raise Refused("这套题目还没有 --sample 试跑记录，没有可审查的样本。")
    if disagree < 0:
        raise Refused("--disagree 不能是负数")
    if not (notes or "").strip():
        raise Refused("--notes 必填：写下样本里看到的问题；没有就写“无”。")
    if disagree > 0 and not accept_reason:
        raise Refused(f"样本里有 {disagree} 条你不同意：改题目或阈值后重新试跑（改阈值可先 rebucket）；"
                      "确要接受，加 --accept-reason \"理由\"。")
    entry.update(approved=True, approved_at=_now(), disagree=disagree, notes=notes.strip(),
                 accept_reason=accept_reason)
    C.write_json(C.calibrations_path(), calibrations)
    _refresh_summary(out_path, questions, thresholds, cfg)
    return entry


def rebucket(out_path, questions_path, cfg):
    questions, thresholds = load_questions(questions_path)
    qhash = question_hash(questions, cfg["model"])
    results = read_results(out_path)
    if not results:
        raise Refused(f"{out_path}: 没有结果")
    if any(r.get("qhash") != qhash for r in results.values()):
        raise Refused(f"{out_path} 的结果来自另一套题目；rebucket 只能改阈值，不能改题目。")
    tmp = Path(str(out_path) + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        for r in results.values():
            if r["bucket"] != "failed":
                r["bucket"], r["reasons"] = bucket_for(r["answers"], questions, thresholds, cfg["batch"])
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    tmp.replace(out_path)
    return _refresh_summary(out_path, questions, thresholds, cfg)


def _validate_decision(d, questions, where):
    if d.get("by") not in ("claude", "user"):
        raise Refused(f"{where} by 必须是 claude 或 user")
    answers = d.get("answers")
    if answers is not None:
        if not isinstance(answers, dict) or not answers:
            raise Refused(f"{where} answers 必须是非空对象")
        unknown = sorted(set(answers) - set(questions))
        if unknown:
            raise Refused(f"{where} answers 里有不存在的题目 id：{', '.join(unknown)}")
    if "verdict" in d or "rule" in d:
        if d.get("verdict") not in ("confirmed", "false_positive") or d.get("rule") not in questions:
            raise Refused(f"{where} rule（题目 id）与 verdict（confirmed / false_positive）必须成对出现且有效")
    elif answers is None:
        raise Refused(f"{where} 需要 answers，或 rule（题目 id）+ verdict（confirmed / false_positive）")


def resolve(out_path, decisions_path, questions_path, cfg):
    questions, thresholds = load_questions(questions_path)
    results = read_results(out_path)
    if not results:
        raise Refused(f"{out_path}: 没有结果")
    accepted = []
    for n, line in enumerate(Path(decisions_path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        where = f"{decisions_path}:{n}:"
        try:
            d = json.loads(line)
        except ValueError:
            raise Refused(f"{where} 不是合法 JSON") from None
        if not isinstance(d, dict) or str(d.get("id")) not in results:
            raise Refused(f"{where} 结果里没有这个 id")
        _validate_decision(d, questions, where)
        accepted.append({**d, "id": str(d["id"]), "at": _now()})
    with open(_resolutions_path(out_path), "a", encoding="utf-8") as f:
        for d in accepted:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    _refresh_summary(out_path, questions, thresholds, cfg)
    return len(accepted)


def save_set(questions_path, name, out_path, cfg):
    questions, thresholds = load_questions(questions_path)
    calib = _calibration(question_hash(questions, cfg["model"]))
    if not calib.get("approved"):
        raise Refused("这套题目还没 approve，不能存为题目集。")
    if not re.fullmatch(r"[\w.-]+", name):
        raise Refused("名字只能用字母、数字、下划线、点和连字符")
    summary = _refresh_summary(out_path, questions, thresholds, cfg)
    noisy = [qid for qid, s in summary["rules"].items()
             if s["confirmed"] + s["false_positive"] >= FP_MIN_VERIFIED
             and s["false_positive"] * 2 > s["confirmed"] + s["false_positive"]]
    if noisy:
        raise Refused(f"这些规则已核实的命中里误报过半，先改规则再存：{', '.join(noisy)}")
    dest = C.question_sets_dir() / f"{name}.json"
    C.write_json(dest, {"questions": questions, "thresholds": thresholds, "calibration": calib})
    return dest


def export_csv(out_path, csv_path):
    results = list(read_results(out_path).values())
    res = read_resolutions(out_path)
    qids = []
    for r in results:
        for qid in r.get("answers") or {}:
            if qid not in qids:
                qids.append(qid)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        header = ["id", "bucket"]
        for qid in qids:
            header += [qid, f"{qid}_confidence", f"final_{qid}"]
        writer.writerow(header + ["decided_by", "verdicts", "reasons"])
        for r in results:
            m = res.get(r["id"]) or {"answers": {}, "by": None, "verdicts": {}}
            line = [r["id"], r["bucket"]]
            for qid in qids:
                a = (r.get("answers") or {}).get(qid) or {}
                value = next((a[k] for k in VALUE_KEYS if k in a), "")
                final = m["answers"].get(qid, value if r["bucket"] == "auto" else "")
                line += [value, a.get("confidence", ""), final]
            decided_by = m["by"] or ("jev" if r["bucket"] == "auto" else "")
            verdicts = "; ".join(f"{k}:{v}" for k, v in sorted(m["verdicts"].items()))
            writer.writerow(line + [decided_by, verdicts, "; ".join(r.get("reasons") or [])])
    return len(results)


def hits(out_path, questions_path, cfg):
    questions, thresholds = load_questions(questions_path)
    found = []
    for r in read_results(out_path).values():
        rules = []
        for qid, q in questions.items():
            v = _noul_of(r, qid)
            if q["type"] == "noul" and v is not None and v >= _noul_band(thresholds.get(qid), cfg["batch"])[0]:
                rules.append(qid)
        if rules:
            found.append({"id": r["id"], "rules": rules})
    return found


def main(argv):
    parser = argparse.ArgumentParser(prog="jev_batch.py")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("run")
    p.add_argument("--input", required=True)
    p.add_argument("--questions", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--source", help="数据的原始来源（放行清单检查它）；缺省为 --input")
    p.add_argument("--sample", type=int)
    p.add_argument("--skip-calibration")
    p.add_argument("--confirm-cost", action="store_true")
    p.add_argument("--concurrency", type=int)
    p = sub.add_parser("approve")
    p.add_argument("--out", required=True)
    p.add_argument("--questions", required=True)
    p.add_argument("--disagree", type=int, required=True)
    p.add_argument("--notes", required=True)
    p.add_argument("--accept-reason")
    for name in ("rebucket", "hits"):
        p = sub.add_parser(name)
        p.add_argument("--out", required=True)
        p.add_argument("--questions", required=True)
    p = sub.add_parser("resolve")
    p.add_argument("--out", required=True)
    p.add_argument("--questions", required=True)
    p.add_argument("--decisions", required=True)
    p = sub.add_parser("save-set")
    p.add_argument("--out", required=True)
    p.add_argument("--questions", required=True)
    p.add_argument("--name", required=True)
    p = sub.add_parser("export")
    p.add_argument("--out", required=True)
    p.add_argument("--csv", required=True)
    args = parser.parse_args(argv)
    show = lambda obj: print(json.dumps(obj, ensure_ascii=False, indent=2))
    try:
        cfg = C.load_config()
        if args.cmd == "run":
            show(run(args.input, args.questions, args.out, cfg=cfg, source=args.source, sample=args.sample,
                     skip_calibration=args.skip_calibration, confirm_cost=args.confirm_cost,
                     concurrency=args.concurrency))
        elif args.cmd == "approve":
            show(approve(args.out, args.questions, cfg, disagree=args.disagree, notes=args.notes,
                         accept_reason=args.accept_reason))
        elif args.cmd == "rebucket":
            show(rebucket(args.out, args.questions, cfg))
        elif args.cmd == "resolve":
            print(f"记录了 {resolve(args.out, args.decisions, args.questions, cfg)} 条裁决")
        elif args.cmd == "save-set":
            print(f"已存：{save_set(args.questions, args.name, args.out, cfg)}")
        elif args.cmd == "export":
            print(f"{export_csv(args.out, args.csv)} 行 → {args.csv}")
        else:
            for h in hits(args.out, args.questions, cfg):
                print(json.dumps(h, ensure_ascii=False))
    except Refused as e:
        print(str(e), file=sys.stderr)
        return e.code
    except C.ConfigError as e:
        print(f"配置文件有问题：{e}", file=sys.stderr)
        return EXIT_REFUSED
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
