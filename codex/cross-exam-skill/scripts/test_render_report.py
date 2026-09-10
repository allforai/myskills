# codex/cross-exam-skill/scripts/test_render_report.py
import json
import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

import render_report
from render_report import render


def _mk_run(tmp, facets, entries, baseline="spec", make_evidence=True):
    run = Path(tmp)
    for e in entries:
        d = e.get("evidence", {}).get("dir")
        if d and make_evidence:
            p = run / d
            p.mkdir(parents=True, exist_ok=True)
            (p / "note.txt").write_text("evidence", encoding="utf-8")
            for st in e.get("steps", []):
                if st.get("evidence"):
                    (p / st["evidence"]).write_text("step", encoding="utf-8")
            snap = (e.get("terminal_state") or {}).get("snapshot")
            if snap:
                (p / snap).write_text("a11y", encoding="utf-8")
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

    def test_gap_without_valid_severity_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            e = _entry("q-gap", verdict="gap", ev_dir="evidence/q1/")
            run = _mk_run(tmp, [{"id": "F1", "name": "面一", "status": "examined"}], [e])
            report = render(run)
            self.assertIn("非法严重度", report)
            self.assertIn("缺口：0", report)

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

    def test_model_policy_declared_in_overview(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = _mk_run(tmp, [{"id": "F1", "name": "面一", "status": "examined"}], [_entry("q1")])
            L = json.loads((run / "ledger.json").read_text(encoding="utf-8"))
            L["model_policy"] = {"observation": "sonnet", "judgment": "session",
                                 "confirmed_by_user": "实测官用 sonnet 就行", "confirmed_at": "2026-09-07T15:10:00+08:00"}
            (run / "ledger.json").write_text(json.dumps(L, ensure_ascii=False), encoding="utf-8")
            report = render(run)
            overview = report[:report.index("## 逐面完成度")]
            self.assertIn("取证类子 agent（实测官、枚举官）用 sonnet", overview)
            self.assertIn("实测官用 sonnet 就行", overview)
            self.assertNotIn("非法模型策略", overview)
            L["model_policy"]["recommended"] = {"option": "B", "why": "扫全模式"}
            (run / "ledger.json").write_text(json.dumps(L, ensure_ascii=False), encoding="utf-8")
            self.assertIn("推荐的是选项 B（扫全模式）", render(run))
            L["model_policy"]["history"] = [{"observation": "haiku", "confirmed_by_user": "省", "confirmed_at": "2026-09-01T09:00:00+08:00"}]
            (run / "ledger.json").write_text(json.dumps(L, ensure_ascii=False), encoding="utf-8")
            self.assertIn("此前策略：取证用 haiku，用户于 2026-09-01T09:00:00+08:00 确认", render(run))
            L["model_policy"]["judgment"] = "haiku"
            (run / "ledger.json").write_text(json.dumps(L, ensure_ascii=False), encoding="utf-8")
            self.assertIn("非法模型策略：judgment 只能是 session，ledger 写了 haiku", render(run))
        with tempfile.TemporaryDirectory() as tmp:
            run = _mk_run(tmp, [{"id": "F1", "name": "面一", "status": "examined"}], [_entry("q1")])
            self.assertNotIn("取证类子 agent", render(run))

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
            self.assertIn("— 无法自证\n测试账号无法登录，前置条件造不出（证据：", sec)
            self.assertNotIn("无法自证：测试账号", sec)

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

    def test_journey_gap_without_severity_is_refused_codex(self):
        with tempfile.TemporaryDirectory() as tmp:
            e = _jentry(verdict="gap", stuck_kind="no_feedback")   # 无 severity
            run = _mk_run(tmp, self.FACETS, [e])
            _with_journeys(run, [_journey()])
            report = render(run)
            self.assertIn("非法严重度：None", report)
            self.assertIn("旅程 1 条，盘问 0 条", report)


class TestGapIds(unittest.TestCase):
    FACETS = [{"id": "F1", "name": "面一", "status": "examined"}]

    def test_gap_ids_follow_ledger_order_not_severity(self):
        # 缺口按 ledger 先后编 G 号；缺口清单按严重度排序时编号跟着条目走
        with tempfile.TemporaryDirectory() as tmp:
            entries = [
                _entry("q-low", verdict="gap", ev_dir="evidence/q1/", severity="low"),
                _entry("q-done", verdict="done", ev_dir="evidence/q2/"),
                _entry("q-high", verdict="drift", ev_dir="evidence/q3/", severity="high"),
            ]
            run = _mk_run(tmp, self.FACETS, entries)
            report = render(run)
            gap_sec = report[report.index("## 缺口清单"):report.index("## 无法自证清单")]
            self.assertIn("[G1]", gap_sec)
            self.assertIn("[G2]", gap_sec)
            self.assertLess(gap_sec.index("[G2]"), gap_sec.index("[G1]"))   # high 在前
            self.assertIn("[G2] [F1] q-high", gap_sec)
            self.assertIn("[G1] [F1] q-low", gap_sec)
            facet_sec = report[report.index("## 逐面完成度"):report.index("## 旅程完成度")]
            self.assertIn("[G1] [F1] q-low", facet_sec)     # 逐面里同样带号，便于对照
            self.assertNotIn("[G", facet_sec[facet_sec.index("q-done") - 20:facet_sec.index("q-done")])

    def test_journey_gap_uses_J_not_G_and_does_not_consume_a_number(self):
        with tempfile.TemporaryDirectory() as tmp:
            jgap = _jentry(verdict="gap", severity="high", stuck_kind="no_feedback",
                           ev_dir="evidence/q5/")
            plain = _entry("q-plain", verdict="gap", ev_dir="evidence/q6/", severity="low")
            run = _mk_run(tmp, self.FACETS, [jgap, plain])
            _with_journeys(run, [_journey()])
            report = render(run)
            gap_sec = report[report.index("## 缺口清单"):report.index("## 无法自证清单")]
            self.assertIn("[J1] [F1] J1 走得通吗？", gap_sec)
            self.assertNotIn("[G1] [J1]", gap_sec)
            self.assertIn("[G1] [F1] q-plain", gap_sec)
            self.assertNotIn("[G2]", report)

    def test_refused_gap_does_not_consume_a_number(self):
        with tempfile.TemporaryDirectory() as tmp:
            oral = _entry("q-oral", verdict="gap", ev_dir="evidence/q1/", severity="high")
            real = _entry("q-real", verdict="gap", ev_dir="evidence/q2/", severity="low")
            run = _mk_run(tmp, self.FACETS, [oral, real], make_evidence=False)
            (run / "evidence/q2").mkdir(parents=True)
            (run / "evidence/q2/note.txt").write_text("x", encoding="utf-8")
            report = render(run)
            self.assertIn("违规裁决", report)
            self.assertIn("[G1] [F1] q-real", report)
            self.assertNotIn("[G2]", report)


class TestStepEvidenceFiles(unittest.TestCase):
    FACETS = [{"id": "F1", "name": "面一", "status": "examined"}]

    def test_missing_step_evidence_file_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            e = _jentry()
            run = _mk_run(tmp, self.FACETS, [e])
            _with_journeys(run, [_journey()])
            (run / "evidence/q5/q05-02-order.png").unlink()
            report = render(run)
            self.assertIn("违规裁决", report)
            self.assertIn("步骤证据文件缺失：q05-02-order.png", report)
            self.assertIn("旅程 1 条，盘问 0 条", report)

    def test_missing_terminal_snapshot_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            e = _jentry()
            e["terminal_state"] = {"url": "/orders/1001", "snapshot": "q05-terminal-a11y.txt"}
            run = _mk_run(tmp, self.FACETS, [e])
            _with_journeys(run, [_journey()])
            (run / "evidence/q5/q05-terminal-a11y.txt").unlink()
            report = render(run)
            self.assertIn("步骤证据文件缺失：q05-terminal-a11y.txt", report)

    def test_step_without_evidence_name_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            steps = [{"n": 1, "action": "打开 /cart", "observed": "ok", "status": "done"}]
            e = _jentry(steps=steps)
            run = _mk_run(tmp, self.FACETS, [e])
            _with_journeys(run, [_journey()])
            report = render(run)
            self.assertIn("步骤证据文件缺失：第 1 步未写 evidence", report)

    def test_all_step_files_present_is_admitted(self):
        with tempfile.TemporaryDirectory() as tmp:
            e = _jentry()
            e["terminal_state"] = {"url": "/orders/1001", "snapshot": "q05-terminal-a11y.txt"}
            run = _mk_run(tmp, self.FACETS, [e])
            _with_journeys(run, [_journey()])
            report = render(run)
            self.assertNotIn("违规裁决", report)
            self.assertIn("旅程裁决：实证完成：1", report)


def _with_top(run, **keys):
    ledger = json.loads((run / "ledger.json").read_text(encoding="utf-8"))
    ledger.update(keys)
    (run / "ledger.json").write_text(json.dumps(ledger, ensure_ascii=False), encoding="utf-8")


class TestSurfaceCoverage(unittest.TestCase):
    """覆盖分母：census 的 surfaces 原样入账，facet 的操作面覆盖由渲染器按被采信 entry 算，不许自报。"""
    SURFACES = [{"id": "S1", "name": "创建订单", "entry": "POST /api/orders"},
                {"id": "S2", "name": "订单列表", "entry": "GET /api/orders"},
                {"id": "S3", "name": "退款", "entry": "POST /api/orders/:id/refund"},
                {"id": "S4", "name": "登录", "entry": "POST /api/auth/login"}]
    FACETS = [{"id": "F1", "name": "订单", "status": "examined", "surface_ids": ["S1", "S2", "S3"]},
              {"id": "F2", "name": "账户", "status": "not_examined", "surface_ids": ["S4"],
               "risk": {"level": "high", "why": "全部面的前置"}}]

    def _run(self, tmp, entries, facets=None):
        run = _mk_run(tmp, facets or self.FACETS, entries)
        _with_top(run, surfaces=self.SURFACES)
        return run

    def test_facet_line_names_untouched_surfaces(self):
        with tempfile.TemporaryDirectory() as tmp:
            e = _entry("q-refund"); e["surfaces"] = ["S3"]
            report = render(self._run(tmp, [e]))
            self.assertIn("订单（F1）— 1 问中 1 问实证通过 · 操作面 3 个，裁决触及 1 个", report)
            self.assertIn("未触及：S1 创建订单、S2 订单列表", report)

    def test_overview_counts_surfaces_touched(self):
        with tempfile.TemporaryDirectory() as tmp:
            e = _entry("q-refund"); e["surfaces"] = ["S3", "S1"]
            report = render(self._run(tmp, [e]))
            self.assertIn("操作面 4 个，裁决触及 2 个", report)

    def test_unknown_surface_id_does_not_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            e = _entry("q-x"); e["surfaces"] = ["S3", "S99"]
            report = render(self._run(tmp, [e]))
            self.assertIn("裁决触及 1 个", report)
            self.assertIn("未登记的操作面 id：S99", report)

    def test_refused_entry_touches_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            good = _entry("q-good"); good["surfaces"] = ["S3"]
            oral = _entry("q-oral", ev_dir="evidence/q2/"); oral["surfaces"] = ["S1"]
            run = self._run(tmp, [good, oral])
            import shutil; shutil.rmtree(run / "evidence/q2", ignore_errors=True)
            report = render(run)
            self.assertIn("裁决触及 1 个", report)

    def test_entry_without_surfaces_is_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = render(self._run(tmp, [_entry("q-nosurf")]))
            self.assertIn("未登记触及的操作面", report)
            self.assertIn("裁决触及 0 个", report)

    def test_facet_without_surface_ids_says_coverage_unknown(self):
        with tempfile.TemporaryDirectory() as tmp:
            facets = [{"id": "F1", "name": "横切", "status": "examined"}]
            e = _entry("q-1"); e["surfaces"] = ["S1"]
            report = render(self._run(tmp, [e], facets=facets))
            self.assertIn("横切（F1）— 1 问中 1 问实证通过 · 操作面未登记，覆盖不可算", report)

    def test_facet_status_is_derived_not_self_reported(self):
        # status 写 examined 但零 entry：进未盘问声明，不算盘问过的面
        with tempfile.TemporaryDirectory() as tmp:
            facets = [{"id": "F1", "name": "订单", "status": "examined", "surface_ids": ["S1"]},
                      {"id": "F2", "name": "账户", "status": "examined", "surface_ids": ["S4"]}]
            e = _entry("q-1"); e["surfaces"] = ["S1"]
            report = render(self._run(tmp, [e], facets=facets))
            self.assertIn("盘问 1 面", report)
            unex = report[report.index("## 未盘问声明"):report.index("## 未拉的线")]
            self.assertIn("账户（F2）", unex)
            self.assertIn("未评估风险", unex)

    def test_journey_entry_counts_toward_surface_coverage(self):
        with tempfile.TemporaryDirectory() as tmp:
            je = _jentry(); je["surfaces"] = ["S1", "S3"]
            run = self._run(tmp, [je])
            _with_journeys(run, [_journey()])
            report = render(run)
            self.assertIn("操作面 4 个，裁决触及 2 个", report)

    def test_old_ledger_without_surfaces_renders_as_before(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = _mk_run(tmp, [{"id": "F1", "name": "面一", "status": "examined"}], [_entry("q1")])
            report = render(run)
            self.assertNotIn("操作面", report)
            self.assertIn("面一（F1）— 1 问中 1 问实证通过", report)


class TestDoneByMedium(unittest.TestCase):
    def test_overview_splits_done_by_medium(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = _entry("q-rt", ev_dir="evidence/q1/")
            b = _entry("q-code", ev_dir="evidence/q2/"); b["medium"] = "code"
            c = _entry("q-code2", ev_dir="evidence/q3/"); c["medium"] = "code"
            run = _mk_run(tmp, [{"id": "F1", "name": "面一", "status": "examined"}], [a, b, c])
            report = render(run)
            self.assertIn("实证完成：3（运行时 1 · 代码 2 · 台账 0）", report)


class TestRequirementCoverage(unittest.TestCase):
    REQS = [{"id": "R-01", "text": "提交工单"}, {"id": "R-04", "text": "导出 CSV"},
            {"id": "R-08", "text": "通知邮件"}, {"id": "R-09", "text": "审计日志"}]
    FACETS = [{"id": "F1", "name": "提交", "status": "examined", "requirement_refs": ["R-01"]},
              {"id": "F2", "name": "导出", "status": "not_examined", "requirement_refs": ["R-04"],
               "risk": {"level": "medium", "why": "财务对账"}},
              {"id": "F3", "name": "通知", "status": "examined", "requirement_refs": ["R-08"]}]

    def test_requirement_section_lists_verdicts_and_gaps(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = _entry("q-submit"); a["requirement_refs"] = ["R-01"]
            b = _entry("q-notify", facet="F3", verdict="gap", severity="high", ev_dir="evidence/q2/")
            b["requirement_ref"] = "R-08"
            run = _mk_run(tmp, self.FACETS, [a, b])
            _with_top(run, requirements=self.REQS)
            report = render(run)
            sec = report[report.index("## 需求覆盖"):report.index("## 逐面完成度")]
            self.assertIn("基准 4 条，有裁决 2 条，无裁决 2 条", sec)
            self.assertIn("R-01 提交工单 — 实证完成", sec)
            self.assertIn("R-08 通知邮件 — 缺口", sec)
            self.assertIn("R-04 导出 CSV — 无裁决（面 F2 未盘问）", sec)
            self.assertIn("R-09 审计日志 — 无裁决（未落任何面）", sec)

    def test_requirement_covered_only_by_admitted_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            oral = _entry("q-oral"); oral["requirement_refs"] = ["R-01"]
            run = _mk_run(tmp, self.FACETS, [oral], make_evidence=False)
            _with_top(run, requirements=self.REQS)
            report = render(run)
            self.assertIn("有裁决 0 条", report)

    def test_no_requirements_key_means_no_section(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = _mk_run(tmp, self.FACETS, [_entry("q1")])
            self.assertNotIn("## 需求覆盖", render(run))



class TestLedgerV2ContentGate(unittest.TestCase):
    """ledger_version 2：目录非空不再够，证据内容要像取证。"""
    FACETS = [{"id": "F1", "name": "面一", "status": "examined"}]

    def _run(self, tmp, entry, files):
        run = _mk_run(tmp, self.FACETS, [entry], make_evidence=False)
        d = run / entry["evidence"]["dir"]; d.mkdir(parents=True)
        for name, body in files.items():
            (d / name).write_bytes(body if isinstance(body, bytes) else body.encode("utf-8"))
        ledger = json.loads((run / "ledger.json").read_text(encoding="utf-8"))
        ledger["ledger_version"] = 2
        for x in ledger["entries"]:
            x.setdefault("probed_at", "2026-09-07T10:00:00+08:00")
        (run / "ledger.json").write_text(json.dumps(ledger, ensure_ascii=False), encoding="utf-8")
        return run

    def test_note_saying_looks_fine_is_refused_for_code_medium(self):
        with tempfile.TemporaryDirectory() as tmp:
            e = _entry("q-note"); e["medium"] = "code"
            report = render(self._run(tmp, e, {"note.txt": "看过了，没问题"}))
            self.assertIn("代码摘录无 路径:行号", report)
            self.assertIn("实证完成：0", report)

    def test_code_excerpt_with_path_line_is_admitted(self):
        with tempfile.TemporaryDirectory() as tmp:
            e = _entry("q-code"); e["medium"] = "code"
            report = render(self._run(tmp, e, {"q01-excerpt.md": "src/api/refund.ts:42\n  if (order.refunded) return 409"}))
            self.assertNotIn("违规裁决", report)

    def test_runtime_needs_served_by_and_rejects_mocked_done(self):
        with tempfile.TemporaryDirectory() as tmp:
            e = _entry("q-rt")
            report = render(self._run(tmp, e, {"q01-01.png": b"\x89PNG"}))
            self.assertIn("缺请求去向 served_by", report)
        with tempfile.TemporaryDirectory() as tmp:
            e = _entry("q-rt"); e["served_by"] = {"host": "localhost:3000", "process": "node next dev", "mock_layers": ["msw"]}
            report = render(self._run(tmp, e, {"q01-01.png": b"\x89PNG"}))
            self.assertIn("经 mock 层（msw）的 runtime 不能判 done", report)
        with tempfile.TemporaryDirectory() as tmp:
            e = _entry("q-rt", verdict="gap", severity="high")
            e["served_by"] = {"host": "localhost:3000", "process": "node next dev", "mock_layers": ["msw"]}
            report = render(self._run(tmp, e, {"q01-01.png": b"\x89PNG"}))
            self.assertNotIn("违规裁决", report)   # gap through a mock is still a gap
        with tempfile.TemporaryDirectory() as tmp:
            # layers that were checked and found inactive live in checked_absent, not mock_layers: done stays admissible
            e = _entry("q-rt")
            e["served_by"] = {"host": "localhost:3000", "process": "node next dev", "mock_layers": [],
                              "checked_absent": ["msw 在 devDependencies，service worker 未注册"]}
            report = render(self._run(tmp, e, {"q01-01.png": b"\x89PNG"}))
            self.assertNotIn("违规裁决", report)

    def test_runtime_file_count_must_reach_requested_states(self):
        with tempfile.TemporaryDirectory() as tmp:
            e = _entry("q-rt"); e["states_to_capture"] = ["00", "01", "02"]
            e["served_by"] = {"host": "localhost:3000", "process": "node", "mock_layers": []}
            report = render(self._run(tmp, e, {"q01-00.png": b"\x89PNG", "q01-01.png": b"\x89PNG"}))
            self.assertIn("要求 3 个状态只落了 2 个文件", report)

    def test_unprovable_reason_must_be_substantive(self):
        with tempfile.TemporaryDirectory() as tmp:
            e = _entry("q-u", verdict="unprovable")
            report = render(self._run(tmp, e, {"reason.md": "起不来"}))
            self.assertIn("无法自证缺原因文件", report)

    def test_transcript_linkage(self):
        with tempfile.TemporaryDirectory() as tmp:
            transcript = Path(tmp) / "agent.output"
            transcript.write_text("... wrote evidence/q1/q01-excerpt.md ...", encoding="utf-8")
            e = _entry("q-t"); e["medium"] = "code"; e["agent_task"] = {"output_file": str(transcript)}
            report = render(self._run(tmp, e, {"q01-excerpt.md": "a/b.ts:1 x"}))
            self.assertNotIn("违规裁决", report)
        with tempfile.TemporaryDirectory() as tmp:
            transcript = Path(tmp) / "agent.output"
            transcript.write_text("... wrote docs/other-run/evidence/q9/q01-excerpt.md ...", encoding="utf-8")
            e2 = _entry("q-t2"); e2["medium"] = "code"; e2["agent_task"] = {"output_file": str(transcript)}
            report = render(self._run(tmp, e2, {"q02-other.md": "a/b.ts:1 x"}))
            self.assertIn("证据文件未出现在实测官 transcript，transcript 也未提及证据目录 evidence/q1：q02-other.md", report)
        with tempfile.TemporaryDirectory() as tmp:
            # scripted prober: filenames built in a loop never appear literally, but the directory does
            transcript = Path(tmp) / "agent.output"
            transcript.write_text('for i, s in enumerate(states):\n    page.screenshot(path=f"{evidence_dir}/q01-{s}.png")\n'
                                  "Files written to evidence/q1/.", encoding="utf-8")
            e4 = _entry("q-t4"); e4["agent_task"] = {"output_file": str(transcript)}
            e4["states_to_capture"] = ["00", "01"]
            e4["served_by"] = {"host": "localhost:3000", "process": "node", "mock_layers": []}
            report = render(self._run(tmp, e4, {"q01-00.png": b"\x89PNG", "q01-01.png": b"\x89PNG"}))
            self.assertNotIn("违规裁决", report)
        with tempfile.TemporaryDirectory() as tmp:
            e3 = _entry("q-t3"); e3["medium"] = "code"; e3["agent_task"] = {"output_file": str(Path(tmp) / "gone.output")}
            report = render(self._run(tmp, e3, {"q03.md": "a/b.ts:1 x"}))
            self.assertNotIn("违规裁决", report)

    # 探测窗口：probed_at 起、transcript 写完（mtime）加容差止；mtime 全用 os.utime 设定，不依赖墙钟
    PROBED_AT = "2026-09-07T10:00:00+08:00"
    T0 = datetime.fromisoformat(PROBED_AT).timestamp()
    T_END = T0 + 600          # transcript 落盘时刻
    TOL = render_report.PROBE_WINDOW_TOLERANCE

    def _window_run(self, tmp, files, mtimes, body="Files written to evidence/q1/.", transcript_mtime=None):
        transcript = Path(tmp) / "agent.output"
        transcript.write_text(body, encoding="utf-8")
        e = _entry("q-w"); e["agent_task"] = {"output_file": str(transcript)}
        e["served_by"] = {"host": "localhost:3000", "process": "node", "mock_layers": []}
        run = self._run(tmp, e, files)
        for name, ts in mtimes.items():
            os.utime(run / "evidence/q1" / name, (ts, ts))
        ts = self.T_END if transcript_mtime is None else transcript_mtime
        os.utime(transcript, (ts, ts))
        return run

    def _iso(self, ts):
        return datetime.fromtimestamp(ts, tz=datetime.fromisoformat(self.PROBED_AT).tzinfo).isoformat(timespec="seconds")

    def test_file_written_after_probe_window_is_refused_naming_file_and_window(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = self._window_run(tmp, {"q01-00.png": b"\x89PNG", "q01-01.png": b"\x89PNG"},
                                   {"q01-00.png": self.T0 + 300, "q01-01.png": self.T_END + self.TOL + 1})
            report = render(run)
            self.assertIn("违规裁决", report)
            self.assertIn("证据文件 q01-01.png 写于 %s，不在探测窗口 [%s, %s] 内"
                          % (self._iso(self.T_END + self.TOL + 1), self.PROBED_AT, self._iso(self.T_END + self.TOL)), report)

    def test_naive_probed_at_is_refused_before_the_window_is_computed(self):
        # a probed_at without an offset means a different window on every machine that renders the run
        with tempfile.TemporaryDirectory() as tmp:
            transcript = Path(tmp) / "agent.output"
            transcript.write_text("Files written to evidence/q1/.", encoding="utf-8")
            e = _entry("q-n"); e["agent_task"] = {"output_file": str(transcript)}
            e["served_by"] = {"host": "localhost:3000", "process": "node", "mock_layers": []}
            e["probed_at"] = "2026-09-07T10:00:00"
            run = self._run(tmp, e, {"q01-00.png": b"\x89PNG"})
            report = render(run)
            self.assertIn("probed_at 缺时区偏移", report)

    def test_every_offending_file_is_named(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = self._window_run(tmp, {"a.png": b"\x89PNG", "b.png": b"\x89PNG", "ok.png": b"\x89PNG"},
                                   {"a.png": self.T_END + self.TOL + 5, "b.png": self.T_END + self.TOL + 6,
                                    "ok.png": self.T0 + 5})
            report = render(run)
            self.assertIn("a.png", report); self.assertIn("b.png", report)
            self.assertNotIn("ok.png 写于", report)

    def test_file_written_before_probed_at_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = self._window_run(tmp, {"q01-00.png": b"\x89PNG"}, {"q01-00.png": self.T0 - 10})
            report = render(run)
            self.assertIn("证据文件 q01-00.png 写于 %s，不在探测窗口" % self._iso(self.T0 - 10), report)

    def test_scripted_files_inside_window_pass_on_directory_mention(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = self._window_run(tmp, {"q01-00.png": b"\x89PNG", "q01-01.png": b"\x89PNG"},
                                   {"q01-00.png": self.T0, "q01-01.png": self.T0 + 300})
            self.assertNotIn("违规裁决", render(run))

    def test_file_named_in_transcript_but_outside_window_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = self._window_run(tmp, {"q01-00.png": b"\x89PNG"}, {"q01-00.png": self.T_END + self.TOL + 5},
                                   body="page.screenshot(path='evidence/q1/q01-00.png')")
            report = render(run)
            self.assertIn("证据文件 q01-00.png 写于", report)
            self.assertIn("违规裁决", report)

    def test_file_within_tolerance_after_transcript_mtime_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = self._window_run(tmp, {"q01-00.png": b"\x89PNG"}, {"q01-00.png": self.T_END + self.TOL - 1})
            self.assertNotIn("违规裁决", render(run))

    def test_probed_at_after_transcript_mtime_is_an_empty_window(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = self._window_run(tmp, {"q01-00.png": b"\x89PNG"}, {"q01-00.png": self.T0 - 300},
                                   transcript_mtime=self.T0 - self.TOL - 60)
            self.assertIn("证据文件 q01-00.png 写于", render(run))

    def test_missing_transcript_keeps_note_and_skips_window(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = self._window_run(tmp, {"q01-00.png": b"\x89PNG"}, {"q01-00.png": self.T_END + self.TOL + 999})
            (Path(tmp) / "agent.output").unlink()
            report = render(run)
            self.assertNotIn("违规裁决", report)
            self.assertNotIn("探测窗口", report)
            self.assertIn("transcript 不可核（文件不在）", report)

    def test_unreadable_file_mtime_is_a_note_not_a_refusal(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = self._window_run(tmp, {"q01-00.png": b"\x89PNG"}, {"q01-00.png": self.T0 + 300})
            real = render_report._evidence_files
            ghost = run / "evidence/q1/ghost.png"   # listed but never on disk: stat() fails like a stripped-mtime fs
            with mock.patch.object(render_report, "_evidence_files", lambda e, r: real(e, r) + [ghost]):
                report = render(run)
            self.assertNotIn("违规裁决", report)
            self.assertIn("ghost.png", report)
            self.assertIn("修改时间不可读", report)

    def test_v1_ledger_keeps_old_behaviour(self):
        with tempfile.TemporaryDirectory() as tmp:
            e = _entry("q-old"); e["medium"] = "code"
            run = _mk_run(tmp, self.FACETS, [e], make_evidence=False)
            d = run / "evidence/q1"; d.mkdir(parents=True); (d / "note.txt").write_text("看过了", encoding="utf-8")
            self.assertNotIn("违规裁决", render(run))


class TestSmallHonestyFixes(unittest.TestCase):
    FACETS = [{"id": "F1", "name": "面一", "status": "examined"}, {"id": "F2", "name": "面二", "status": "examined"}]

    def test_header_separates_facets_with_only_unprovable(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = _mk_run(tmp, self.FACETS, [_entry("q1"), _entry("q2", facet="F2", verdict="unprovable", ev_dir="evidence/q2/")])
            self.assertIn("盘问 1 面（另 1 面仅无法自证）", render(run))

    def test_legacy_shorthand_requirement_refs_expand(self):
        from render_report import _requirement_ids
        self.assertEqual(_requirement_ids({"requirement_ref": "R-moment-01/03/07"}),
                         {"R-moment-01", "R-moment-03", "R-moment-07"})
        self.assertEqual(_requirement_ids({"requirement_ref": "R-09, R-10"}), {"R-09", "R-10"})
        self.assertEqual(_requirement_ids({"requirement_ref": "R-09（可选）"}), {"R-09（可选）"})

    def test_git_author_overlap_flags_undeclared_self_review(self):
        import subprocess
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.email", "dev@example.com"], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.name", "dev"], check=True)
            (repo / "a.txt").write_text("x", encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)
            run = _mk_run(str(repo / "docs/cross-exam/run"), self.FACETS[:1], [_entry("q1")])
            report = render(run)
            self.assertIn("检测到当前 git 用户 dev@example.com", report)
            self.assertIn("bias-guard 应生效", report)

    def test_probed_at_required_in_v2_and_fast_runtime_pairs_named(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = _entry("q-a", ev_dir="evidence/q1/"); b = _entry("q-b", ev_dir="evidence/q2/")
            for e, t in ((a, "2026-09-07T10:00:00+08:00"), (b, "2026-09-07T10:00:20+08:00")):
                e["probed_at"] = t; e["served_by"] = {"host": "localhost", "process": "node", "mock_layers": []}
            run = _mk_run(tmp, self.FACETS[:1], [a, b], make_evidence=False)
            for q in ("q1", "q2"):
                (run / "evidence" / q).mkdir(parents=True); (run / "evidence" / q / "shot.png").write_bytes(b"\x89PNG")
            ledger = json.loads((run / "ledger.json").read_text(encoding="utf-8")); ledger["ledger_version"] = 2
            (run / "ledger.json").write_text(json.dumps(ledger, ensure_ascii=False), encoding="utf-8")
            report = render(run)
            self.assertIn("相邻 runtime 问间隔不足 60 秒", report)
            self.assertIn("q-a → q-b（20 秒）", report)
            ledger["entries"][0].pop("probed_at")
            (run / "ledger.json").write_text(json.dumps(ledger, ensure_ascii=False), encoding="utf-8")
            self.assertIn("缺 probed_at", render(run))

    def test_mock_backend_is_declared_in_overview(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = _mk_run(tmp, self.FACETS[:1], [_entry("q1")])
            ledger = json.loads((run / "ledger.json").read_text(encoding="utf-8"))
            ledger["target_backend"] = {"kind": "mock", "how_known": "用户确认 MSW"}
            (run / "ledger.json").write_text(json.dumps(ledger, ensure_ascii=False), encoding="utf-8")
            self.assertIn("开发实例后端为 mock", render(run))


if __name__ == "__main__":
    unittest.main()


class TestFrozenRunRendersByteIdentically(unittest.TestCase):
    """A run frozen before the evidence engine was extracted (#58) renders byte for byte as it did then.
    The golden was captured from the pre-extraction renderer; the fixture walks every seam that moved:
    the v2 content gate per medium, served_by, the probe window inside and outside, and a refused entry."""
    GOLDEN = Path(__file__).with_name("fixtures") / "frozen-run.report.md"
    T0 = datetime.fromisoformat("2026-09-07T10:00:00+08:00").timestamp()

    def _frozen_run(self, tmp):
        served = {"host": "localhost:3000", "process": "node next dev", "mock_layers": []}
        facets = [{"id": "F1", "name": "面一", "status": "examined", "requirement_refs": ["R-01", "R-02"],
                   "surface_ids": ["S1", "S2"], "risk": {"level": "high", "why": "支付主路径"}},
                  {"id": "F2", "name": "面二", "status": "not_examined", "risk": {"level": "low", "why": "静态页"}}]
        done = _entry("登录后能进首页吗？")
        done.update(probed_at="2026-09-07T10:00:00+08:00", served_by=served, surfaces=["S1"], requirement_refs=["R-01"])
        gap = _entry("空购物车能结账吗？", verdict="gap", ev_dir="evidence/q2/", severity="medium")
        gap.update(probed_at="2026-09-07T10:03:00+08:00", served_by=served, surfaces=["S2"], requirement_ref="R-02")
        code = _entry("汇率换算在哪实现？", verdict="drift", ev_dir="evidence/q3/", severity="low")
        code.update(medium="code", probed_at="2026-09-07T10:05:00+08:00", surfaces=["S1"])
        unprovable = _entry("推送到达率能测吗？", verdict="unprovable", ev_dir="evidence/q4/")
        unprovable.update(probed_at="2026-09-07T10:07:00+08:00", surfaces=["S2"])
        journey = _jentry()
        journey.update(probed_at="2026-09-07T10:09:00+08:00", served_by=served, surfaces=["S1"])
        windowed = _entry("订单号真的落库了吗？", ev_dir="evidence/q6/")
        windowed.update(probed_at="2026-09-07T10:20:00+08:00", served_by=served, surfaces=["S1"],
                        agent_task={"output_file": str(Path(tmp) / "prober-ok.output")})
        late = _entry("退款按钮点得动吗？", ev_dir="evidence/q7/")
        late.update(probed_at="2026-09-07T10:30:00+08:00", served_by=served, surfaces=["S2"],
                    agent_task={"output_file": str(Path(tmp) / "prober-late.output")})
        oral = _entry("口头说通过的那条", ev_dir="evidence/q8/")
        run = _mk_run(tmp, facets, [done, gap, code, unprovable, journey, windowed, late, oral], make_evidence=False)
        files = {"q1/note.txt": "evidence", "q1/q01-home.png": b"\x89PNG",
                 "q2/q02-empty-cart.png": b"\x89PNG",
                 "q3/excerpt.md": "src/rates.ts:42 const rate = 1  // 写死的汇率",
                 "q4/reason.md": "尝试用 FCM 沙箱发送三次均无回执；本机拿不到设备 token，推送到达率无法自证，卡在设备注册。",
                 "q5/q05-01-cart.png": "step", "q5/q05-02-order.png": "step",
                 "q6/q06-db.txt": "orders: 1 row", "q7/q07-refund.png": b"\x89PNG"}
        for rel, body in files.items():
            p = run / "evidence" / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(body if isinstance(body, bytes) else body.encode("utf-8"))
        # transcripts and mtimes are pinned with os.utime, never the wall clock
        stamps = {"evidence/q6/q06-db.txt": self.T0 + 1230, "evidence/q7/q07-refund.png": self.T0 + 5000}
        for name, body, ts in (("prober-ok.output", "Files written to evidence/q6/.", self.T0 + 1500),
                               ("prober-late.output", "Files written to evidence/q7/.", self.T0 + 2100)):
            (Path(tmp) / name).write_text(body, encoding="utf-8")
            stamps[name] = ts
        for rel, ts in stamps.items():
            os.utime(Path(tmp) / rel, (ts, ts))
        ledger = json.loads((run / "ledger.json").read_text(encoding="utf-8"))
        ledger.update(ledger_version=2, journeys=[_journey()],
                      surfaces=[{"id": "S1", "name": "首页"}, {"id": "S2", "name": "购物车"}],
                      requirements=[{"id": "R-01", "text": "登录后进首页"}, {"id": "R-02", "text": "空车不能结账"},
                                    {"id": "R-03", "text": "退款原路返回"}],
                      open_threads=[{"facet": "F2", "q": "静态页的 404 呢？", "leak_point": "路由兜底"}],
                      patterns=[{"pattern_id": "P1", "hypothesis": "写死的汇率", "sites": [
                          {"site": "src/rates.ts:42", "facet": "F1", "entry_q": "汇率换算在哪实现？"},
                          {"site": "src/checkout.ts:10", "facet": "F1", "entry_q": "未实测的位点"}]}])
        (run / "ledger.json").write_text(json.dumps(ledger, ensure_ascii=False), encoding="utf-8")
        return run

    def test_frozen_run_matches_golden(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = render(self._frozen_run(tmp))
        self.assertEqual(report, self.GOLDEN.read_text(encoding="utf-8"))


class TestAuthorEvidence(unittest.TestCase):
    """作者证据（交付流水线写的 entry，带 author 标记，#60）：机械介质核过引擎才作门，runtime 只作上下文，
    任何裁决都不能只靠作者——没有独立实测官 entry 的问题按无法自证入账。"""
    FACETS = [{"id": "F1", "name": "面一", "status": "examined"}]
    AUTHOR = {"pipeline": "meta-skill/run", "node_id": "test-verify-1", "capability": "test-verify"}
    HOST_DIRS = [".allforai", ".claude", ".codex"]
    RUN = "docs/cross-exam/2026-09-10-demo"
    SERVED = {"host": "localhost:3000", "process": "node next dev", "mock_layers": []}
    PROBED_AT = "2026-09-07T10:00:00+08:00"

    @staticmethod
    def _git(repo, *args):
        import subprocess
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        env.update(GIT_AUTHOR_NAME="a", GIT_AUTHOR_EMAIL="a@b", GIT_COMMITTER_NAME="a", GIT_COMMITTER_EMAIL="a@b")
        subprocess.run(["git", "-C", str(repo), "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null", *args],
                       check=True, capture_output=True, env=env)

    def _author(self, q, medium="test", verdict="done", **extra):
        e = {"q": q, "facet": "F1", "medium": medium, "verdict": verdict, "probed_at": self.PROBED_AT,
             "author": dict(self.AUTHOR), "build_excludes": list(self.HOST_DIRS),
             "readback": {"runner": "pytest 8.2.0", "selected": "142 tests"},
             "evidence": {"dir": "evidence/author/test-verify-1/", "key_observation": "142 passed"}}
        if medium == "runtime":
            e["served_by"] = dict(self.SERVED)
        if verdict in ("gap", "drift"):
            e["severity"] = "medium"
        e.update(extra)
        return e

    def _prober(self, q, verdict="done"):
        e = _entry(q, verdict=verdict, severity="medium" if verdict in ("gap", "drift") else None)
        e.update(probed_at="2026-09-07T10:05:00+08:00", served_by=dict(self.SERVED))
        return e

    def _run(self, tmp, entries, files=None, dirty=None):
        """A committed target repo with the cross-exam run inside it. Author entries get the build of the tree
        as the pipeline saw it (host dirs excluded, the run dir not yet there); `dirty` edits the tree after."""
        repo = Path(tmp)
        repo.mkdir(parents=True, exist_ok=True)
        (repo / "app.py").write_text("print(1)\n", encoding="utf-8")
        self._git(repo, "init", "-q")
        self._git(repo, "add", ".")
        self._git(repo, "commit", "-q", "-m", "one")
        identity = render_report._identity.build_identity(repo, (), self.HOST_DIRS)["build"]
        run = repo / self.RUN
        files = {"author/test-verify-1/pytest.json": '{"exit_code": 0, "passed": 142}', "q1/note.txt": "evidence",
                 "q1/q01-home.png": b"\x89PNG", **(files or {})}
        for rel, body in files.items():
            if body is None:   # a default file the case does without
                continue
            p = run / "evidence" / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(body if isinstance(body, bytes) else body.encode("utf-8"))
        for e in entries:
            if "author" in e:
                e.setdefault("build", identity)
        if dirty:
            (repo / "app.py").write_text(dirty, encoding="utf-8")
        (run / "ledger.json").write_text(json.dumps({
            "ledger_version": 2, "target": "demo", "baseline": "spec", "started": "2026-09-10",
            "facets": self.FACETS, "entries": entries}, ensure_ascii=False), encoding="utf-8")
        return run

    def test_mechanical_author_entry_is_a_gate_labelled_author_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = self._run(tmp, [self._prober("测试套件在真后端下过吗？"), self._author("测试套件在真后端下过吗？")])
            report = render(run)
            self.assertIn("## 作者证据", report)
            self.assertIn("- **门通过** [F1] 测试套件在真后端下过吗？ — 142 passed（meta-skill/run · test-verify-1 · test-verify · 介质 test", report)
            self.assertIn("· 独立实测：实证完成", report)
            self.assertIn("bias-guard 对每条作者证据生效", report)
            self.assertIn("实证完成：1（运行时 1 · 代码 0 · 台账 0） · 缺口：0 · 跑偏：0 · 无法自证：0", report)
            self.assertNotIn("违规裁决", report)

    def test_author_runtime_evidence_is_context_and_the_question_still_needs_a_prober(self):
        with tempfile.TemporaryDirectory() as tmp:
            screenshot = lambda: self._author("首页在真后端下能渲染吗？", medium="runtime",
                                              evidence={"dir": "evidence/author/product-verify-1/", "key_observation": "首页渲染"})
            run = self._run(tmp, [screenshot()], files={"author/product-verify-1/home.png": b"\x89PNG"})
            report = render(run)
            self.assertIn("- **仅上下文** [F1] 首页在真后端下能渲染吗？ — 首页渲染（meta-skill/run · test-verify-1 · test-verify · 介质 runtime", report)
            self.assertIn("· 待独立实测官取证", report)
            self.assertIn("实测 0 问", report)
            self.assertIn("实证完成：0 · 缺口：0 · 跑偏：0 · 无法自证：0", report)
            self.assertIn("- 面一（F1）— 未盘问，不计入任何完成度", report)
            self.assertNotIn("违规裁决", report)
            # a prober on the same question is the verdict; the author screenshot stays context beside it
            run = self._run(tmp + "/again", [self._prober("首页在真后端下能渲染吗？", verdict="gap"), screenshot()],
                            files={"author/product-verify-1/home.png": b"\x89PNG"})
            report = render(run)
            self.assertIn("· 独立实测：缺口", report)
            self.assertIn("缺口：1", report)
            self.assertIn("[G1]", report)

    def test_author_code_excerpt_is_context_not_a_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = self._run(tmp, [self._author("幂等键在哪？", medium="code")],
                            files={"author/test-verify-1/pytest.json": "src/api/refund.ts:42 if (order.refunded) return 409"})
            report = render(run)
            self.assertIn("- **仅上下文** [F1] 幂等键在哪？", report)
            self.assertNotIn("门通过", report)

    def test_no_verdict_rests_on_author_entries_alone(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = self._run(tmp, [self._author("测试套件在真后端下过吗？")])
            report = render(run)
            self.assertIn("实证完成：0 · 缺口：0 · 跑偏：0 · 无法自证：1", report)
            line = ("- **无法自证** [作者证据] [F1] 测试套件在真后端下过吗？ — 142 passed（证据：evidence/author/test-verify-1/）"
                    " · 作者证据只作门（test 门通过），裁决须独立实测官取证")
            self.assertIn(line, report)
            self.assertIn(line, report.split("## 无法自证清单")[1].split("## ")[0])
            self.assertIn("· 未独立实测，按无法自证入账", report)
            self.assertIn("盘问 0 面（另 1 面仅无法自证）", report)
            # a failed gate cannot close a gap either
            run = self._run(tmp + "/gap", [self._author("测试套件在真后端下过吗？", verdict="gap")])
            report = render(run)
            self.assertIn("缺口：0 · 跑偏：0 · 无法自证：1", report)
            self.assertIn("- **门未通过** [F1]", report)
            self.assertNotIn("[G1]", report)

    def test_readback_is_demanded_of_runtime_author_entries_only(self):
        # a suite run has nothing to read back; a runtime capture without readback proves nothing was applied
        for extra in ({"readback": {}}, {"readback": None}):
            with tempfile.TemporaryDirectory() as tmp:
                report = render(self._run(tmp, [self._author("测试套件在真后端下过吗？", **extra)]))
                self.assertNotIn("作者证据缺读回", report)
                self.assertIn("## 作者证据", report)
            with tempfile.TemporaryDirectory() as tmp:
                report = render(self._run(tmp, [self._author("首页在真后端下渲染吗？", medium="runtime", **extra)]))
                self.assertIn("首页在真后端下渲染吗？（作者证据缺读回 readback", report)
                self.assertNotIn("## 作者证据", report)

    def test_unverifiable_author_evidence_is_refused_by_name(self):
        cases = [
            ({"images": ["pytest.json"], "image_digests": {"pytest.json": "stale"}}, None, None, "截图内容摘要不匹配: pytest.json"),
            ({}, None, "print(2)\n", "构建标识不匹配：记录 "),
            ({"build": "deadbeef-0000000000000000"}, None, None, "构建标识不匹配：记录 deadbeef-0000000000000000，当前 "),
            ({"probed_at": "2026-09-07T10:00:00"}, None, None, "probed_at 缺时区偏移（如 +08:00）"),
            ({"author": {"pipeline": "meta-skill/run"}}, None, None, "作者标记不完整（pipeline / node_id / capability）"),
            ({"build_excludes": [".allforai", "src"]}, None, None, "构建标识排除范围只能是宿主隐藏目录（如 .allforai）: src"),
            ({}, {"author/test-verify-1/pytest.json": None, "author/test-verify-1/green.png": b"\x89PNG"}, None,
             "机械门证据无输出文件（构建 / 测试 / 契约比对的捕获输出）"),
        ]
        for extra, files, dirty, reason in cases:
            with tempfile.TemporaryDirectory() as tmp:
                run = self._run(tmp, [self._author("测试套件在真后端下过吗？", **extra)], files=files, dirty=dirty)
                report = render(run)
                self.assertIn("## 违规裁决", report, reason)
                self.assertIn("测试套件在真后端下过吗？（" + reason, report)
                self.assertIn("无法自证：0", report)
                self.assertNotIn("## 作者证据", report)

    def test_author_build_is_recomputed_without_the_run_directory_the_examiner_writes(self):
        # the run dir did not exist when the pipeline took the identity; the examiner's own ledger and
        # evidence must not turn every author entry stale
        with tempfile.TemporaryDirectory() as tmp:
            run = self._run(tmp, [self._author("测试套件在真后端下过吗？")])
            (run / "notes.md").write_text("盘问官的笔记", encoding="utf-8")
            self.assertIn("- **门通过** [F1]", render(run))

    def test_run_outside_a_repository_refuses_author_evidence_with_the_engine_reason(self):
        with tempfile.TemporaryDirectory() as tmp:
            e = self._author("测试套件在真后端下过吗？", build="abc-clean")
            run = _mk_run(tmp, self.FACETS, [e], make_evidence=False)
            d = run / "evidence/author/test-verify-1"
            d.mkdir(parents=True)
            (d / "pytest.json").write_text('{"exit_code": 0}', encoding="utf-8")
            ledger = json.loads((run / "ledger.json").read_text(encoding="utf-8"))
            ledger["ledger_version"] = 2
            (run / "ledger.json").write_text(json.dumps(ledger, ensure_ascii=False), encoding="utf-8")
            self.assertIn("测试套件在真后端下过吗？（不是 git 仓库或没有提交: ", render(run))
