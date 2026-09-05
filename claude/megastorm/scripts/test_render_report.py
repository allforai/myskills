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


def _journey(jid="J1", entry_q="J1 走得通吗？", status="examined", risk=None):
    j = {"id": jid, "who": "回头客", "circumstance": "购物车里已有一件商品",
         "progress": "完成支付并拿到订单号",
         "preconditions": ["已登录测试账号"], "waypoints": ["支付确认页"],
         "oracle": {"done_looks_like": ["URL 含 /orders/"],
                    "stuck_looks_like": ["仍在 /cart"]},
         "step_budget": 15, "status": status, "entry_q": entry_q}
    if risk:
        j["risk"] = risk
    return j


def _jentry(q="J1 走得通吗？", jid="J1", verdict="done", ev_dir="evidence/q5/",
            severity=None, stuck_kind=None, steps=None, missed_waypoints=None):
    e = _entry(q, verdict=verdict, ev_dir=ev_dir, severity=severity)
    e["journey"] = jid
    e["steps"] = steps if steps is not None else [
        {"n": 1, "action": "打开 /cart", "observed": "购物车显示 1 件商品",
         "status": "done", "evidence": "q05-01-cart.png"},
        {"n": 2, "action": "点击 结账", "observed": "跳到 /orders/1001",
         "status": "done", "evidence": "q05-02-order.png"}]
    if stuck_kind:
        e["stuck_kind"] = stuck_kind
    if missed_waypoints is not None:
        e["missed_waypoints"] = missed_waypoints
    return e


def _with_journeys(run, journeys):
    L = json.loads((run / "ledger.json").read_text(encoding="utf-8"))
    L["journeys"] = journeys
    (run / "ledger.json").write_text(json.dumps(L, ensure_ascii=False), encoding="utf-8")
    return run


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


class TestNotExaminedRisk(unittest.TestCase):
    def test_not_examined_sorted_by_risk_with_why(self):
        # 未盘问面按 risk.level 排序并打印 why；缺 risk 的排最后标"未评估风险"
        with tempfile.TemporaryDirectory() as tmp:
            run = _mk_run(tmp, [
                {"id": "F1", "name": "面一", "status": "examined"},
                {"id": "F2", "name": "低风险面", "status": "not_examined",
                 "risk": {"level": "low", "why": "无需求引用"}},
                {"id": "F3", "name": "无风险字段面", "status": "not_examined"},
                {"id": "F4", "name": "高风险面", "status": "not_examined",
                 "risk": {"level": "high", "why": "触碰资金对账"}}],
                [_entry("q1")])
            report = render(run)
            sec = report[report.index("## 未盘问声明"):report.index("## 未拉的线")]
            self.assertLess(sec.index("高风险面"), sec.index("低风险面"))
            self.assertLess(sec.index("低风险面"), sec.index("无风险字段面"))
            self.assertIn("触碰资金对账", sec)
            self.assertIn("未评估风险", sec)
            self.assertIn("盘问 1 面", report)  # 仍不计入

    def test_examiner_is_author_declared_in_overview(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = _mk_run(tmp, [{"id": "F1", "name": "面一", "status": "examined"}],
                          [_entry("q1")])
            L = json.loads((run / "ledger.json").read_text(encoding="utf-8"))
            L["examiner_is_author"] = True
            (run / "ledger.json").write_text(
                json.dumps(L, ensure_ascii=False), encoding="utf-8")
            report = render(run)
            overview = report[:report.index("## 逐面完成度")]
            self.assertIn("examiner_is_author", overview)
            self.assertIn("bias-guard", overview)

    def test_examiner_is_author_absent_is_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = _mk_run(tmp, [{"id": "F1", "name": "面一", "status": "examined"}],
                          [_entry("q1")])
            self.assertNotIn("bias-guard", render(run))


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


class TestPatterns(unittest.TestCase):
    def _run_with_patterns(self, tmp, entries, patterns):
        run = _mk_run(tmp, [{"id": "F1", "name": "面一", "status": "examined"},
                            {"id": "F2", "name": "面二", "status": "partial"}],
                      entries)
        L = json.loads((run / "ledger.json").read_text(encoding="utf-8"))
        L["patterns"] = patterns
        (run / "ledger.json").write_text(
            json.dumps(L, ensure_ascii=False), encoding="utf-8")
        return run

    def test_patterns_section_counts_and_unexamined_sites_listed(self):
        # 3 位点：1 个链到被采信的 gap entry → 实证 1；2 个无 entry → 未查 2，逐个点名
        with tempfile.TemporaryDirectory() as tmp:
            gap = _entry("退款重复提交会双扣吗？", verdict="gap",
                         ev_dir="evidence/q3/", severity="high")
            run = self._run_with_patterns(tmp, [gap], [{
                "pattern_id": "P1", "hypothesis": "写端点普遍缺幂等键",
                "sites": [
                    {"site": "POST /api/refunds", "facet": "F1",
                     "entry_q": "退款重复提交会双扣吗？"},
                    {"site": "POST /api/orders", "facet": "F2"},
                    {"site": "POST /api/coupons/redeem", "facet": "F2"},
                ]}])
            report = render(run)
            self.assertIn("## 缺陷模式", report)
            self.assertIn("写端点普遍缺幂等键", report)
            self.assertIn("共 3 位点", report)
            self.assertIn("实证 1", report)
            self.assertIn("未查 2", report)
            pat = report[report.index("## 缺陷模式"):]
            pat = pat.split("\n## ")[0]
            self.assertIn("POST /api/orders", pat)
            self.assertIn("POST /api/coupons/redeem", pat)

    def test_site_linked_to_refused_entry_counts_as_unexamined(self):
        # entry_q 指向被拒渲（无证据）的 entry → 该位点算未查，不算实证
        with tempfile.TemporaryDirectory() as tmp:
            oral = _entry("下单重复提交会双扣吗？", verdict="gap",
                          ev_dir="evidence/q9/", severity="high")
            run = self._run_with_patterns(tmp, [oral], [{
                "pattern_id": "P1", "hypothesis": "写端点普遍缺幂等键",
                "sites": [{"site": "POST /api/orders", "facet": "F2",
                           "entry_q": "下单重复提交会双扣吗？"}]}])
            import shutil
            shutil.rmtree(Path(tmp) / "evidence/q9", ignore_errors=True)
            report = render(run)
            pat = report[report.index("## 缺陷模式"):].split("\n## ")[0]
            self.assertIn("实证 0", pat)
            self.assertIn("未查 1", pat)

    def test_site_with_unmatched_entry_q_counts_as_unexamined(self):
        # entry_q 对不上任何 entry（口头声称查过）→ 未查
        with tempfile.TemporaryDirectory() as tmp:
            run = self._run_with_patterns(tmp, [_entry("q1")], [{
                "pattern_id": "P1", "hypothesis": "写端点普遍缺幂等键",
                "sites": [{"site": "POST /api/orders", "facet": "F2",
                           "entry_q": "根本没问过的问题"}]}])
            report = render(run)
            pat = report[report.index("## 缺陷模式"):].split("\n## ")[0]
            self.assertIn("实证 0", pat)
            self.assertIn("未查 1", pat)

    def test_patterns_do_not_inflate_overall_counts(self):
        # patterns 引用的 entry 不重复计数；未查位点不进任何裁决计数
        with tempfile.TemporaryDirectory() as tmp:
            gap = _entry("退款重复提交会双扣吗？", verdict="gap",
                         ev_dir="evidence/q3/", severity="high")
            run = self._run_with_patterns(tmp, [gap], [{
                "pattern_id": "P1", "hypothesis": "写端点普遍缺幂等键",
                "sites": [
                    {"site": "POST /api/refunds", "facet": "F1",
                     "entry_q": "退款重复提交会双扣吗？"},
                    {"site": "POST /api/orders", "facet": "F2"},
                ]}])
            report = render(run)
            self.assertIn("缺口：1", report)
            self.assertIn("实证完成：0", report)

    def test_pattern_not_enumerated_is_declared(self):
        # 枚举官无返回：enumerated=false → 标题标"全集未清点"，"未查 0"不被误读为只有一处
        with tempfile.TemporaryDirectory() as tmp:
            gap = _entry("退款重复提交会双扣吗？", verdict="gap",
                         ev_dir="evidence/q3/", severity="high")
            run = self._run_with_patterns(tmp, [gap], [{
                "pattern_id": "P1", "hypothesis": "写端点普遍缺幂等键",
                "enumerated": False,
                "sites": [{"site": "POST /api/refunds", "facet": "F1",
                           "entry_q": "退款重复提交会双扣吗？"}]}])
            report = render(run)
            pat = report[report.index("## 缺陷模式"):].split("\n## ")[0]
            self.assertIn("全集未清点", pat)
            self.assertIn("实证 1", pat)

    def test_patterns_key_absent_renders_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = _mk_run(tmp, [{"id": "F1", "name": "面一", "status": "examined"}],
                          [_entry("q1")])
            report = render(run)
            self.assertIn("## 缺陷模式", report)
            pat = report[report.index("## 缺陷模式"):].split("\n## ")[0]
            self.assertIn("（无）", pat)


class TestJourneys(unittest.TestCase):
    FACETS = [{"id": "F1", "name": "面一", "status": "examined"}]

    def test_journey_done_counted_separately_from_plain(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = _mk_run(tmp, self.FACETS, [_jentry()])
            _with_journeys(run, [_journey()])
            report = render(run)
            overview = report[:report.index("## 逐面完成度")]
            self.assertIn("旅程 1 条，盘问 1 条", overview)
            self.assertIn("旅程裁决：实证完成：1", overview)
            self.assertIn("实证完成：0 · 缺口：0", overview)   # 普通计数不含旅程
            sec = report[report.index("## 旅程完成度"):report.index("## 缺口清单")]
            self.assertIn("J1 回头客 · 购物车里已有一件商品 · 完成支付并拿到订单号", sec)
            self.assertIn("走通，2 步", sec)
            self.assertIn("- 1 done 打开 /cart → 购物车显示 1 件商品", sec)
            facet_sec = report[report.index("## 逐面完成度"):report.index("## 旅程完成度")]
            self.assertNotIn("J1 走得通吗？", facet_sec)

    def test_journey_gap_renders_stuck_step_kind_and_tag(self):
        with tempfile.TemporaryDirectory() as tmp:
            steps = [
                {"n": 1, "action": "打开 /cart", "observed": "购物车显示 1 件商品",
                 "status": "done", "evidence": "q05-01-cart.png"},
                {"n": 7, "action": "点击 确认支付", "observed": "按钮变灰 3 秒后恢复，页面无变化",
                 "status": "stuck", "evidence": "q05-07-pay-noop.png"}]
            e = _jentry(verdict="gap", severity="high", stuck_kind="no_feedback", steps=steps)
            run = _mk_run(tmp, self.FACETS, [e])
            _with_journeys(run, [_journey()])
            report = render(run)
            sec = report[report.index("## 旅程完成度"):report.index("## 缺口清单")]
            self.assertIn("缺口（high，无反馈）", sec)
            self.assertIn("走了 2 步，卡在第 7 步：点击 确认支付 → 按钮变灰 3 秒后恢复，页面无变化", sec)
            gap_sec = report[report.index("## 缺口清单"):report.index("## 无法自证清单")]
            self.assertIn("[J1]", gap_sec)
            self.assertIn("旅程裁决：实证完成：0 · 缺口：1", report)

    def test_journey_gap_with_illegal_stuck_kind_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            e = _jentry(verdict="gap", severity="high", stuck_kind="lost")
            run = _mk_run(tmp, self.FACETS, [e])
            _with_journeys(run, [_journey()])
            report = render(run)
            self.assertIn("违规裁决", report)
            self.assertIn("非法卡死类型：lost", report)
            self.assertIn("旅程 1 条，盘问 0 条", report)
            unex = report[report.index("## 未盘问声明"):report.index("## 未拉的线")]
            self.assertIn("旅程 回头客", unex)
            self.assertIn("（J1）", unex)

    def test_entry_referencing_unknown_journey_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            e = _jentry(jid="J9", q="J9 走得通吗？")
            run = _mk_run(tmp, self.FACETS, [e])
            _with_journeys(run, [_journey()])
            report = render(run)
            self.assertIn("违规裁决", report)
            self.assertIn("旅程引用不存在：J9", report)
            self.assertIn("旅程裁决：实证完成：0", report)

    def test_journey_entry_q_unmatched_is_unexamined_despite_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = _mk_run(tmp, self.FACETS, [_jentry()])
            _with_journeys(run, [_journey(entry_q="nope", status="examined")])
            report = render(run)
            self.assertIn("旅程 1 条，盘问 0 条", report)
            unex = report[report.index("## 未盘问声明"):report.index("## 未拉的线")]
            self.assertIn("旅程 回头客", unex)
            self.assertIn("（J1）", unex)
            self.assertIn("未评估风险", unex)

    def test_journey_linked_to_refused_entry_is_unexamined(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = _mk_run(tmp, self.FACETS, [_jentry()], make_evidence=False)
            _with_journeys(run, [_journey()])
            report = render(run)
            self.assertIn("违规裁决", report)
            self.assertIn("旅程 1 条，盘问 0 条", report)
            unex = report[report.index("## 未盘问声明"):report.index("## 未拉的线")]
            self.assertIn("旅程 回头客", unex)
            self.assertIn("（J1）", unex)

    def test_not_examined_journeys_sorted_by_risk_after_facets(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = _mk_run(tmp, self.FACETS, [_entry("q1")])
            _with_journeys(run, [
                _journey("J1", entry_q="", status="not_examined",
                         risk={"level": "low", "why": "次要路径"}),
                _journey("J2", entry_q="", status="not_examined",
                         risk={"level": "high", "why": "主线收入"}),
                _journey("J3", entry_q="", status="not_examined")])
            report = render(run)
            unex = report[report.index("## 未盘问声明"):report.index("## 未拉的线")]
            self.assertLess(unex.index("（J2）"), unex.index("（J1）"))
            self.assertLess(unex.index("（J1）"), unex.index("（J3）"))
            self.assertIn("主线收入", unex)
            self.assertIn("未评估风险", unex)
            self.assertIn("实证完成：1", report)   # 未盘问旅程不进计数

    def test_journeys_key_absent_renders_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = _mk_run(tmp, self.FACETS, [_entry("q1")])
            report = render(run)
            self.assertIn("## 旅程完成度", report)
            sec = report[report.index("## 旅程完成度"):].split("\n## ")[0]
            self.assertIn("（无旅程声明）", sec)
            self.assertNotIn("旅程裁决", report)
            self.assertNotIn("旅程 0 条", report)

    def test_journey_drift_lists_missed_waypoints(self):
        with tempfile.TemporaryDirectory() as tmp:
            e = _jentry(verdict="drift", severity="medium", missed_waypoints=["支付确认页"])
            run = _mk_run(tmp, self.FACETS, [e])
            _with_journeys(run, [_journey()])
            report = render(run)
            sec = report[report.index("## 旅程完成度"):report.index("## 缺口清单")]
            self.assertIn("跑偏（medium）", sec)
            self.assertIn("走通但绕过 waypoint：支付确认页", sec)

    def test_journey_unprovable_shows_reason(self):
        with tempfile.TemporaryDirectory() as tmp:
            e = _jentry(verdict="unprovable", steps=[])
            e["evidence"]["key_observation"] = "测试账号无法登录，前置条件造不出"
            run = _mk_run(tmp, self.FACETS, [e])
            _with_journeys(run, [_journey()])
            report = render(run)
            sec = report[report.index("## 旅程完成度"):report.index("## 缺口清单")]
            self.assertIn("无法自证：测试账号无法登录，前置条件造不出", sec)

    def test_journey_drift_without_missed_waypoints_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            e = _jentry(verdict="drift", severity="medium", missed_waypoints=[])
            run = _mk_run(tmp, self.FACETS, [e])
            _with_journeys(run, [_journey()])
            report = render(run)
            self.assertIn("违规裁决", report)
            self.assertIn("缺 missed_waypoints", report)
            self.assertIn("旅程 1 条，盘问 0 条", report)
            unex = report[report.index("## 未盘问声明"):report.index("## 未拉的线")]
            self.assertIn("（J1）", unex)

    def test_journey_without_id_does_not_match_plain_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = _mk_run(tmp, self.FACETS, [_entry("q1")])
            j = _journey(entry_q="q1")
            del j["id"]
            _with_journeys(run, [j])
            report = render(run)
            self.assertIn("实证完成：1", report)
            unex = report[report.index("## 未盘问声明"):report.index("## 未拉的线")]
            self.assertIn("（?）", unex)

    def test_journey_entry_with_mismatched_entry_q_is_named_on_unexamined_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            e = _jentry(q="J1 走通了吗？")
            run = _mk_run(tmp, self.FACETS, [e])
            _with_journeys(run, [_journey()])
            report = render(run)
            self.assertIn("旅程 1 条，盘问 0 条", report)
            unex = report[report.index("## 未盘问声明"):report.index("## 未拉的线")]
            self.assertIn("entry_q 对不上：J1 走通了吗？", unex)


if __name__ == "__main__":
    unittest.main()
