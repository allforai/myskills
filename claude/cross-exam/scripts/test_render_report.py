# claude/cross-exam/scripts/test_render_report.py
import json
import tempfile
import unittest
from pathlib import Path

from render_report import render


def _mk_run(tmp, facets, entries, baseline="spec", make_evidence=True):
    run = Path(tmp)
    for e in entries:
        d = e.get("evidence", {}).get("dir")
        if d and make_evidence:
            p = run / d
            p.mkdir(parents=True, exist_ok=True)
            (p / "note.txt").write_text("evidence", encoding="utf-8")
    (run / "ledger.json").write_text(json.dumps({
        "target": "demo", "baseline": baseline, "started": "2026-07-09",
        "facets": facets, "entries": entries}, ensure_ascii=False), encoding="utf-8")
    return run


def _entry(q, facet="F1", verdict="done", ev_dir="evidence/q1/", severity=None):
    e = {"q": q, "facet": facet, "leak_point": "lp", "medium": "runtime",
         "evidence": {"dir": ev_dir, "files": [], "key_observation": "obs"},
         "verdict": verdict}
    if severity:
        e["severity"] = severity
    return e


class TestRedLines(unittest.TestCase):
    def test_entry_without_evidence_dir_is_refused(self):
        # 两条 entry：一条有证据、一条 evidence.dir 指向不存在的目录 → 后者被拒渲：
        # 不进计数，出现在"违规裁决"段。
        with tempfile.TemporaryDirectory() as tmp:
            good = _entry("q-good", ev_dir="evidence/q1/")
            bad = _entry("q-oral", ev_dir="evidence/q2/")
            run = _mk_run(tmp, [{"id": "F1", "name": "面一", "status": "examined"}],
                          [good, bad])
            # 只给 q1 建证据目录，q2 的目录不存在
            import shutil
            shutil.rmtree(run / "evidence/q2", ignore_errors=True)
            report = render(run)
            self.assertIn("q-good", report)
            self.assertIn("违规裁决", report)
            self.assertIn("q-oral", report)
            self.assertIn("实证完成：1", report)  # bad 不进计数

    def test_empty_evidence_dir_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            e = _entry("q-empty", ev_dir="evidence/q1/")
            run = _mk_run(tmp, [{"id": "F1", "name": "面一", "status": "examined"}],
                          [e], make_evidence=False)
            (run / "evidence/q1").mkdir(parents=True)  # 存在但为空
            report = render(run)
            self.assertIn("违规裁决", report)
            self.assertIn("实证完成：0", report)

    def test_not_examined_facet_excluded_from_stats(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = _mk_run(tmp, [
                {"id": "F1", "name": "面一", "status": "examined"},
                {"id": "F2", "name": "面二", "status": "not_examined"}],
                [_entry("q1")])
            report = render(run)
            self.assertIn("盘问 1 面", report)      # F2 不计
            self.assertIn("未盘问声明", report)
            self.assertIn("面二", report)


class TestRendering(unittest.TestCase):
    def test_verdict_counts_and_facet_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            entries = [
                _entry("q1", verdict="done", ev_dir="evidence/q1/"),
                _entry("q2", verdict="gap", ev_dir="evidence/q2/", severity="high"),
                _entry("q3", verdict="unprovable", ev_dir="evidence/q3/"),
            ]
            run = _mk_run(tmp, [{"id": "F1", "name": "面一", "status": "examined"}],
                          entries)
            report = render(run)
            self.assertIn("实证完成：1", report)
            self.assertIn("缺口：1", report)
            self.assertIn("无法自证：1", report)
            self.assertIn("3 问中 1 问实证通过", report)

    def test_gap_list_sorted_by_severity(self):
        with tempfile.TemporaryDirectory() as tmp:
            entries = [
                _entry("q-low", verdict="gap", ev_dir="evidence/q1/", severity="low"),
                _entry("q-high", verdict="drift", ev_dir="evidence/q2/", severity="high"),
            ]
            run = _mk_run(tmp, [{"id": "F1", "name": "面一", "status": "examined"}],
                          entries)
            report = render(run)
            self.assertLess(report.index("q-high"), report.index("q-low"))

    def test_baseline_none_declares_closed_lenses(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = _mk_run(tmp, [{"id": "F1", "name": "面一", "status": "examined"}],
                          [_entry("q1")], baseline="none")
            report = render(run)
            self.assertIn("需求覆盖", report)
            self.assertIn("无基准", report)

    def test_missing_required_key_exits(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            (run / "ledger.json").write_text('{"target": "x"}', encoding="utf-8")
            with self.assertRaises(SystemExit):
                render(run)


if __name__ == "__main__":
    unittest.main()
