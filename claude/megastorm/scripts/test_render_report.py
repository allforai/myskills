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

    def test_evidence_dir_outside_evidence_root_is_refused(self):
        # "." (run 目录本身非空) 与 evidence/ 之外的目录都不算证据
        with tempfile.TemporaryDirectory() as tmp:
            e_dot = _entry("q-dot", ev_dir=".")
            e_out = _entry("q-out", ev_dir="notes/")
            run = _mk_run(tmp, [{"id": "F1", "name": "面一", "status": "examined"}],
                          [e_dot, e_out], make_evidence=False)
            (run / "notes").mkdir()
            (run / "notes" / "x.txt").write_text("x", encoding="utf-8")
            report = render(run)
            self.assertIn("违规裁决", report)
            self.assertIn("q-dot", report)
            self.assertIn("q-out", report)
            self.assertIn("实证完成：0", report)

    def test_unknown_verdict_is_refused_not_silently_rendered(self):
        with tempfile.TemporaryDirectory() as tmp:
            e = _entry("q-weird", verdict="partial", ev_dir="evidence/q1/")
            run = _mk_run(tmp, [{"id": "F1", "name": "面一", "status": "examined"}],
                          [e])
            report = render(run)
            self.assertIn("违规裁决", report)
            self.assertIn("q-weird", report)
            self.assertIn("非法裁决", report)
            facet_section = report[report.index("## 逐面完成度"):report.index("## 缺口清单")]
            self.assertNotIn("q-weird", facet_section)

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
            gap_section = report[report.index("## 缺口清单"):report.index("## 无法自证清单")]
            self.assertIn("q-high", gap_section)
            self.assertIn("q-low", gap_section)
            self.assertLess(gap_section.index("q-high"), gap_section.index("q-low"))

    def test_facet_section_lists_all_verdicts(self):
        with tempfile.TemporaryDirectory() as tmp:
            entries = [
                _entry("q-done", verdict="done", ev_dir="evidence/q1/"),
                _entry("q-gap", verdict="gap", ev_dir="evidence/q2/", severity="high"),
                _entry("q-unprov", verdict="unprovable", ev_dir="evidence/q3/"),
            ]
            run = _mk_run(tmp, [{"id": "F1", "name": "面一", "status": "examined"}],
                          entries)
            report = render(run)
            facet_section = report[report.index("## 逐面完成度"):report.index("## 缺口清单")]
            for q in ("q-done", "q-gap", "q-unprov"):
                self.assertIn(q, facet_section)

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


class TestOpenThreads(unittest.TestCase):
    def test_open_threads_section_rendered_not_counted(self):
        # 弃牌（未拉的线）进报告专节，不进任何裁决计数
        with tempfile.TemporaryDirectory() as tmp:
            run = _mk_run(tmp, [{"id": "F1", "name": "面一", "status": "partial"}],
                          [_entry("q1")])
            L = json.loads((run / "ledger.json").read_text(encoding="utf-8"))
            L["open_threads"] = [
                {"q": "先存后发真的成立吗？", "facet": "F1",
                 "leak_point": "顺序约束单测难测"}]
            (run / "ledger.json").write_text(
                json.dumps(L, ensure_ascii=False), encoding="utf-8")
            report = render(run)
            self.assertIn("## 未拉的线", report)
            threads_section = report[report.index("## 未拉的线"):]
            self.assertIn("先存后发真的成立吗？", threads_section)
            self.assertIn("顺序约束单测难测", threads_section)
            self.assertIn("实证完成：1", report)  # thread 不进计数

    def test_open_threads_key_absent_renders_none(self):
        # 旧 ledger 没有 open_threads 键也能渲染，专节显示（无）
        with tempfile.TemporaryDirectory() as tmp:
            run = _mk_run(tmp, [{"id": "F1", "name": "面一", "status": "examined"}],
                          [_entry("q1")])
            report = render(run)
            self.assertIn("## 未拉的线", report)
            threads_section = report[report.index("## 未拉的线"):]
            self.assertIn("（无）", threads_section.split("\n## ")[0])


if __name__ == "__main__":
    unittest.main()
