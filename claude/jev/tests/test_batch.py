import csv
import json

import pytest

import jev_batch as B
import jev_config as C
from conftest import default_answers

NOUL_Q = {"questions": {"spam": {"type": "noul", "instructions": "Is this spam?"},
                        "kind": {"type": "choice", "instructions": "What kind?",
                                 "criteria": {"praise": "positive", "complaint": "negative"}}},
          "thresholds": {"kind": 0.8}}


@pytest.fixture
def data(tmp_path, cfg_dir):
    d = tmp_path / "data"
    d.mkdir()
    C.write_json(cfg_dir / "allow.json", {"paths": [str(d)]})
    return d


def write_rows(path, n):
    path.write_text("".join(json.dumps({"id": f"r{i}", "state": f"row {i}"}) + "\n" for i in range(n)))
    return path


def write_q(path, spec=NOUL_Q):
    path.write_text(json.dumps(spec))
    return path


def go(data, n=10, spec=NOUL_Q, **kw):
    rows = write_rows(data / "rows.jsonl", n)
    q = write_q(data / "q.json", spec)
    return B.run(str(rows), str(q), str(data / "out.jsonl"), cfg=C.load_config(), **kw)


def paths(data):
    return str(data / "out.jsonl"), str(data / "q.json")


def summary_of(data):
    return json.loads((data / "out.jsonl.summary.json").read_text())


def kind_conf(conf):
    def responder(body):
        out = default_answers(body)
        out["answers"]["kind"]["confidence"] = conf
        return 200, out
    return responder


def spam_hits(states):
    def responder(body):
        out = default_answers(body)
        if body["state"] in states:
            out["answers"]["spam"]["noul"] = 0.97
        return 200, out
    return responder


def decisions(data, items):
    path = data / "dec.jsonl"
    path.write_text("".join(json.dumps(d) + "\n" for d in items))
    return str(path)


# ---- refusals before any request ----

def test_not_allowed_sends_nothing(fake_jev, tmp_path):
    rows = write_rows(tmp_path / "rows.jsonl", 3)
    with pytest.raises(B.Refused) as err:
        B.run(str(rows), str(write_q(tmp_path / "q.json")), str(tmp_path / "o.jsonl"), cfg=C.load_config())
    assert err.value.code == B.EXIT_NOT_ALLOWED and fake_jev.requests == []


def test_source_is_what_gets_checked(fake_jev, data, tmp_path):
    rows = write_rows(tmp_path / "chunks.jsonl", 3)  # outside the allowlist
    q = write_q(tmp_path / "q.json")
    summary = B.run(str(rows), str(q), str(tmp_path / "o.jsonl"), cfg=C.load_config(), source=str(data))
    assert summary["rows_done"] == 3
    with pytest.raises(B.Refused):
        B.run(str(rows), str(q), str(tmp_path / "o2.jsonl"), cfg=C.load_config(), source=str(tmp_path / "secret"))


@pytest.mark.parametrize("text,needle", [
    ('{"id": 1, "state": "a"}\n{bad\n', ":2:"),
    ('{"id": 1, "state": "a"}\n{"id": 1, "state": "b"}\n', "重复"),
    ('{"id": 1}\n', "state"),
    ("\n\n", "没有数据"),
])
def test_bad_rows_refused_with_line(fake_jev, data, text, needle):
    (data / "rows.jsonl").write_text(text)
    with pytest.raises(B.Refused, match=needle):
        B.run(str(data / "rows.jsonl"), str(write_q(data / "q.json")), str(data / "o.jsonl"), cfg=C.load_config())
    assert fake_jev.requests == []


def test_bad_question_type_refused(fake_jev, data):
    write_rows(data / "rows.jsonl", 2)
    q = write_q(data / "q.json", {"questions": {"x": {"type": "essay"}}})
    with pytest.raises(B.Refused, match="type"):
        B.run(str(data / "rows.jsonl"), str(q), str(data / "o.jsonl"), cfg=C.load_config())


def test_no_key_refused(data):
    with pytest.raises(B.Refused, match="OPENROUTER_API_KEY"):
        go(data)


def test_malformed_config_refused_by_main(fake_jev, data, cfg_dir, capsys):
    (cfg_dir / "config.json").write_text("{broken")
    write_rows(data / "rows.jsonl", 2)
    code = B.main(["run", "--input", str(data / "rows.jsonl"), "--questions", str(write_q(data / "q.json")),
                   "--out", str(data / "o.jsonl")])
    assert code == B.EXIT_REFUSED and "config.json" in capsys.readouterr().err
    assert fake_jev.requests == []


# ---- bucketing ----

BC = C.DEFAULTS["batch"]
QS = NOUL_Q["questions"]


@pytest.mark.parametrize("noul,expected", [(0.95, "auto"), (0.05, "auto"), (0.5, "review"), (0.9, "auto")])
def test_noul_band(noul, expected):
    answers = {"spam": {"noul": noul}, "kind": {"confidence": 0.99}}
    assert B.bucket_for(answers, QS, {}, BC)[0] == expected


def test_choice_below_threshold_is_review():
    bucket, reasons = B.bucket_for({"spam": {"noul": 0.0}, "kind": {"confidence": 0.7}}, QS, {"kind": 0.8}, BC)
    assert bucket == "review" and "kind" in reasons[0]


def test_numeric_threshold_for_noul_is_symmetric():
    assert B.bucket_for({"spam": {"noul": 0.75}, "kind": {"confidence": 1}}, QS, {"spam": 0.7}, BC)[0] == "auto"
    assert B.bucket_for({"spam": {"noul": 0.28}, "kind": {"confidence": 1}}, QS, {"spam": 0.7}, BC)[0] == "auto"
    assert B.bucket_for({"spam": {"noul": 0.5}, "kind": {"confidence": 1}}, QS, {"spam": 0.7}, BC)[0] == "review"


def test_missing_answer_is_review():
    assert B.bucket_for({"kind": {"confidence": 1}}, QS, {}, BC)[0] == "review"


# ---- calibration must leave a review record ----

def test_large_run_requires_a_sample(fake_jev, data):
    with pytest.raises(B.Refused, match="--sample"):
        go(data, n=100)
    assert fake_jev.requests == []


def test_sample_alone_is_not_enough_then_approve_unlocks(fake_jev, data):
    s = go(data, n=100, sample=20)
    assert len(fake_jev.requests) == 20 and s["sample"] is True and s["calibrated"] is False
    with pytest.raises(B.Refused, match="approve"):
        go(data, n=100)
    out, q = paths(data)
    B.approve(out, q, C.load_config(), disagree=0, notes="无")
    full = go(data, n=100)
    assert len(fake_jev.requests) == 100
    assert full["rows_done"] == 100 and full["calibrated"] is True and full["calibration"]["disagree"] == 0


def test_approve_needs_a_sample(fake_jev, data):
    go(data, n=3)
    out, q = paths(data)
    with pytest.raises(B.Refused, match="--sample"):
        B.approve(out, q, C.load_config(), disagree=0, notes="无")


def test_approve_with_disagreement_needs_reason(fake_jev, data):
    go(data, n=60, sample=20)
    out, q = paths(data)
    with pytest.raises(B.Refused, match="--accept-reason"):
        B.approve(out, q, C.load_config(), disagree=2, notes="两条把建议判成了抱怨")
    B.approve(out, q, C.load_config(), disagree=2, notes="两条把建议判成了抱怨", accept_reason="用户说可以接受")
    assert summary_of(data)["calibration"]["disagree"] == 2


def test_approve_needs_notes(fake_jev, data):
    go(data, n=60, sample=20)
    out, q = paths(data)
    with pytest.raises(B.Refused, match="--notes"):
        B.approve(out, q, C.load_config(), disagree=0, notes="  ")


def test_skip_calibration_reason_recorded(fake_jev, data):
    s = go(data, n=60, skip_calibration="用户说：直接跑")
    assert s["skip_calibration"] == "用户说：直接跑" and s["calibrated"] is False


# ---- cost, resume, question-set identity ----

def test_cost_cap(fake_jev, data, cfg_dir):
    C.write_json(cfg_dir / "config.json", {"batch": {"input_usd_per_mtok": 1_000_000}})
    with pytest.raises(B.Refused, match="--confirm-cost"):
        go(data, n=5)
    assert fake_jev.requests == []
    assert go(data, n=5, confirm_cost=True)["rows_done"] == 5


def test_resume_skips_done_and_retries_failed(fake_jev, data):
    fake_jev.responder = lambda body: (400, {}) if body["state"] == "row 3" else (200, default_answers(body))
    s = go(data, n=5)
    assert s["buckets"]["failed"] == 1
    fake_jev.responder = lambda body: (200, default_answers(body))
    s = go(data, n=5)
    assert len(fake_jev.requests) == 6 and s["buckets"].get("failed", 0) == 0


def test_changed_questions_are_a_foreign_set(fake_jev, data):
    go(data, n=3)
    other = json.loads(json.dumps(NOUL_Q))
    other["questions"]["spam"]["instructions"] = "Is this an advertisement?"
    write_q(data / "q.json", other)
    with pytest.raises(B.Refused, match="另一套题目"):
        B.run(str(data / "rows.jsonl"), str(data / "q.json"), str(data / "out.jsonl"), cfg=C.load_config())


def test_rebucket_changes_threshold_without_requests(fake_jev, data):
    fake_jev.responder = kind_conf(0.7)
    assert go(data, n=4)["buckets"] == {"review": 4}
    before = len(fake_jev.requests)
    write_q(data / "q.json", dict(NOUL_Q, thresholds={"kind": 0.6}))
    out, q = paths(data)
    assert B.rebucket(out, q, C.load_config())["buckets"] == {"auto": 4}
    B.run(str(data / "rows.jsonl"), q, out, cfg=C.load_config())  # thresholds alone: same set, nothing to redo
    assert len(fake_jev.requests) == before


def test_long_context_flagged(fake_jev, data):
    (data / "rows.jsonl").write_text(json.dumps({"id": "big", "state": "x" * 33000}) + "\n")
    s = B.run(str(data / "rows.jsonl"), str(write_q(data / "q.json")), str(data / "out.jsonl"), cfg=C.load_config())
    assert s["long_context"] == 1
    assert B.read_results(data / "out.jsonl")["big"]["long_context"] is True


def test_summary_file_written(fake_jev, data):
    go(data, n=4)
    summary = summary_of(data)
    assert summary["buckets"] == {"auto": 4} and summary["cost_usd"] == pytest.approx(0.0004)


# ---- review verdicts land in the deliverable ----

def test_resolve_review_rows_into_final_columns(fake_jev, data):
    fake_jev.responder = kind_conf(0.5)
    go(data, n=2)
    out, q = paths(data)
    dec = decisions(data, [{"id": "r0", "by": "claude", "answers": {"kind": "complaint"}}])
    assert B.resolve(out, dec, q, C.load_config()) == 1
    assert B.export_csv(out, str(data / "out.csv")) == 2
    rows = {r["id"]: r for r in csv.DictReader(open(data / "out.csv", encoding="utf-8"))}  # concurrent writes: any order
    assert rows["r0"]["final_kind"] == "complaint" and rows["r0"]["decided_by"] == "claude"
    assert rows["r1"]["final_kind"] == "" and rows["r1"]["decided_by"] == ""
    assert rows["r0"]["kind"] == "praise" and "kind_confidence" in rows["r0"]
    summary = summary_of(data)
    assert summary["resolved"] == 1 and summary["unresolved_review"] == 1


def test_auto_rows_are_decided_by_jev(fake_jev, data):
    go(data, n=2)
    out, _ = paths(data)
    B.export_csv(out, str(data / "out.csv"))
    rows = {r["id"]: r for r in csv.DictReader(open(data / "out.csv", encoding="utf-8"))}
    assert rows["r0"]["final_kind"] == "praise" and rows["r0"]["decided_by"] == "jev" and rows["r0"]["spam"] == "0.0"


def test_resolve_rejects_bad_lines_and_writes_nothing(fake_jev, data):
    go(data, n=2)
    out, q = paths(data)
    dec = decisions(data, [{"id": "r0", "by": "claude", "answers": {"kind": "praise"}},
                           {"id": "zzz", "by": "user", "answers": {"kind": "praise"}}])
    with pytest.raises(B.Refused, match=":2:"):
        B.resolve(out, dec, q, C.load_config())
    dec = decisions(data, [{"id": "r0", "by": "robot", "answers": {"kind": "praise"}}])
    with pytest.raises(B.Refused, match="by"):
        B.resolve(out, dec, q, C.load_config())
    assert not (data / "out.jsonl.resolutions.jsonl").exists()


# ---- hits, false positives, saving a question set ----

def test_hits_lists_noul_above_hi(fake_jev, data):
    fake_jev.responder = spam_hits({"row 1"})
    go(data, n=3)
    out, q = paths(data)
    assert B.hits(out, q, C.load_config()) == [{"id": "r1", "rules": ["spam"]}]


def test_false_positive_heavy_rule_blocks_save_set(fake_jev, data):
    fake_jev.responder = spam_hits({f"row {i}" for i in range(5)})
    go(data, n=10, sample=10)
    out, q = paths(data)
    cfg = C.load_config()
    B.approve(out, q, cfg, disagree=0, notes="无")
    B.resolve(out, decisions(data, [{"id": f"r{i}", "by": "claude", "rule": "spam", "verdict": "false_positive"} for i in range(4)]
                             + [{"id": "r4", "by": "claude", "rule": "spam", "verdict": "confirmed"}]), q, cfg)
    assert summary_of(data)["rules"]["spam"] == {"hits": 5, "confirmed": 1, "false_positive": 4}
    with pytest.raises(B.Refused, match="spam"):
        B.save_set(q, "spam-check", out, cfg)


def test_save_set_requires_approve_then_writes(fake_jev, data):
    go(data, n=5, sample=5)
    out, q = paths(data)
    cfg = C.load_config()
    with pytest.raises(B.Refused, match="approve"):
        B.save_set(q, "comments", out, cfg)
    B.approve(out, q, cfg, disagree=0, notes="无")
    dest = B.save_set(q, "comments", out, cfg)
    saved = json.loads(dest.read_text())
    assert dest == C.question_sets_dir() / "comments.json"
    assert saved["questions"] == NOUL_Q["questions"] and saved["calibration"]["disagree"] == 0
