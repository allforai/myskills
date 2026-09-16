"""Rule-review admission tests, not a benchmark of an LLM's semantic recall."""
import hashlib
import json
from pathlib import Path

import pytest
import render_report


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def fixture(tmp_path, kind="scope_dependency"):
    source = tmp_path / "evidence/rules/sources/spec.md"
    source.parent.mkdir(parents=True)
    source.write_text("本期不做应用深色主题。\n本期应用深色主题下隐藏按钮。\n允许导出数据。\n", encoding="utf-8")
    texts = source.read_text().splitlines()
    rules = [{"id": f"RULE{i}", "source_id": "SRC1", "start_line": i, "end_line": i,
              "quote": text, "subject": "主题" if i < 3 else "导出", "effect": text,
              "scope": {"release": "本期", "platform": "web", "role": "all", "condition": "all"},
              "exceptions": [], "supersedes": [], "requirement_refs": ["R1" if i < 3 else "R2"]}
             for i, text in enumerate(texts, 1)]
    requirements = [{"id": "R1", "text": "主题规则"}, {"id": "R2", "text": "导出数据"}]
    report = {"schema_version": 1, "reviewer": {"session_id": "independent-review-1", "independent": True},
              "source_ids": ["SRC1"], "source_digests": {"SRC1": digest(source)},
              "requirements_digest": render_report._rules.requirements_digest(requirements), "rules": rules,
              "comparison_groups": [{"rule_refs": ["RULE1", "RULE2"], "result": "findings", "basis": "主题范围与依赖"},
                                    {"rule_refs": ["RULE3"], "result": "compatible", "basis": "本组只有一条规则"}],
              "findings": [{"id": "RC1", "kind": kind, "rule_refs": ["RULE1", "RULE2"],
                            "scope_overlap": "本期应用主题", "reason": "排除范围与条件依赖待核对", "question": "以哪条有效规则验收？"}],
              "could_not": []}
    report_path = tmp_path / "evidence/rules/review.json"
    save(report_path, report)
    entries = []
    for i in (1, 2):
        evidence = tmp_path / f"evidence/q{i}"
        evidence.mkdir()
        (evidence / "excerpt.txt").write_text("src/ui.py:1: observed source behavior", encoding="utf-8")
        entries.append({"q": f"q{i}", "facet": f"F{i}", "medium": "code", "verdict": "done",
                        "requirement_refs": [f"R{i}"], "probed_at": "2026-09-16T20:00:00+09:00",
                        "states_to_capture": [], "evidence": {"dir": f"evidence/q{i}", "key_observation": "source excerpt"}})
    ledger = {"ledger_version": 3, "target": "rule review fixture", "baseline": "spec",
              "requirements": requirements,
              "facets": [{"id": "F1", "name": "主题"}, {"id": "F2", "name": "导出"}], "entries": entries,
              "rule_consistency": {"status": "reviewed", "sources": [{"id": "SRC1", "ref": "evidence/rules/sources/spec.md",
                                                                       "sha256": digest(source), "origin": "docs/spec.md:1-3 @ HEAD"}],
                                   "report_ref": "evidence/rules/review.json", "report_digest": digest(report_path),
                                   "agent_task": "fresh-child-1", "agent_model": "session", "decisions": []}}
    return ledger, report


def render(tmp_path, ledger, report=None):
    if report is not None:
        path = tmp_path / "evidence/rules/review.json"
        save(path, report)
        ledger["rule_consistency"]["report_digest"] = digest(path)
    save(tmp_path / "ledger.json", ledger)
    return render_report.render(tmp_path)


def decision(ledger, disposition="clarified"):
    return {"finding_id": "RC1", "disposition": disposition,
            "report_digest": ledger["rule_consistency"]["report_digest"],
            "confirmation": "本期没有应用深色，删除那条本期验收要求，不增加主题。",
            "confirmed_at": "2026-09-16T20:30:00+09:00",
            "effective_rule": "本期应用仅浅色，系统深色不改变按钮可见性。"}


@pytest.mark.parametrize("kind", sorted(render_report._rules.KINDS))
def test_candidate_is_reported_but_not_counted_as_product_bug(tmp_path, kind):
    ledger, report = fixture(tmp_path, kind)
    text = render(tmp_path, ledger)
    assert "RC1" in text and kind in text
    assert "本期不做应用深色主题。" in text
    assert "本期应用深色主题下隐藏按钮。" in text
    assert "SRC1:1-1" in text and "SRC1:2-2" in text
    assert "待用户澄清" in text
    assert "实证完成：1" in text  # unrelated R2 still admissible
    assert "缺口：0" in text
    assert "规则基线未澄清" in text
    assert "[G1]" not in text


@pytest.mark.parametrize("disposition", ["confirmed_conflict", "deferred"])
def test_user_acknowledgment_is_not_resolution(tmp_path, disposition):
    ledger, _ = fixture(tmp_path)
    ledger["rule_consistency"]["decisions"] = [decision(ledger, disposition)]
    text = render(tmp_path, ledger)
    assert "实证完成：1" in text
    assert render_report._rules.DISPOSITIONS[disposition] in text


def test_user_clarification_unblocks_but_keeps_original_finding(tmp_path):
    ledger, _ = fixture(tmp_path)
    ledger["rule_consistency"]["decisions"] = [decision(ledger)]
    text = render(tmp_path, ledger)
    assert "实证完成：2" in text
    assert "已澄清" in text and "有效规则：" in text and "RC1" in text
    assert "本期应用深色主题下隐藏按钮。" in text  # source never rewritten


@pytest.mark.parametrize("key,value", [("confirmation", ""), ("effective_rule", ""),
                                       ("confirmed_at", "2026-09-16T20:30:00"), ("finding_id", "unknown")])
def test_invalid_clarification_cannot_close_candidate(tmp_path, key, value):
    ledger, _ = fixture(tmp_path)
    row = decision(ledger)
    row[key] = value
    ledger["rule_consistency"]["decisions"] = [row]
    text = render(tmp_path, ledger)
    assert "实证完成：0" in text
    assert "RC1" in text and "待用户澄清" in text
    assert "本期不做应用深色主题。" in text and "本期应用深色主题下隐藏按钮。" in text
    assert "待确认：以哪条有效规则验收？" in text
    assert "决策不可采信（候选证据保留）" in text


def test_stale_decisions_cannot_apply_to_new_review(tmp_path):
    ledger, report = fixture(tmp_path)
    ledger["rule_consistency"]["decisions"] = [decision(ledger)]
    report["findings"][0]["question"] = "新增约束后请重新确认"
    text = render(tmp_path, ledger, report)
    assert "实证完成：1" in text and "过期确认 1 条未采信" in text


def test_last_user_decision_can_reopen_candidate(tmp_path):
    ledger, _ = fixture(tmp_path)
    ledger["rule_consistency"]["decisions"] = [decision(ledger), decision(ledger, "deferred")]
    assert "实证完成：1" in render(tmp_path, ledger)


@pytest.mark.parametrize("status", ["not_examined", "unavailable"])
def test_unfinished_review_blocks_done_but_preserves_observed_gap(tmp_path, status):
    ledger, _ = fixture(tmp_path)
    ledger["rule_consistency"] = {"status": status, "reason": "没有完成独立规则审查"}
    ledger["entries"][1].update(verdict="gap", severity="high")
    text = render(tmp_path, ledger)
    assert "实证完成：0" in text and "缺口：1" in text and "[G1]" in text


def test_missing_new_run_review_is_not_silent_success(tmp_path):
    ledger, _ = fixture(tmp_path)
    del ledger["rule_consistency"]
    text = render(tmp_path, ledger)
    assert "新 run 缺 rule_consistency" in text and "实证完成：0" in text


@pytest.mark.parametrize("version", [1, 2])
def test_old_run_without_review_stays_compatible_and_discloses_limit(tmp_path, version):
    ledger, _ = fixture(tmp_path)
    ledger["ledger_version"] = version
    del ledger["rule_consistency"]
    text = render(tmp_path, ledger)
    assert "历史台账未做规则对比" in text and "实证完成：2" in text


def test_removing_entry_refs_does_not_evade_pending_conflict(tmp_path):
    ledger, _ = fixture(tmp_path)
    del ledger["entries"][1]["requirement_refs"]
    assert "实证完成：0" in render(tmp_path, ledger)


def test_unknown_impact_blocks_every_done(tmp_path):
    ledger, report = fixture(tmp_path)
    ledger["requirements"] = []
    report["requirements_digest"] = render_report._rules.requirements_digest([])
    for rule in report["rules"]:
        rule["requirement_refs"] = []
    assert "实证完成：0" in render(tmp_path, ledger, report)


def test_no_rule_mode_requires_no_baseline_or_oracles(tmp_path):
    ledger, _ = fixture(tmp_path)
    ledger.update(baseline="none", requirements=[])
    ledger["rule_consistency"] = {"status": "not_applicable", "reason": "用户未声明规则，仅观察契约操作"}
    text = render(tmp_path, ledger)
    assert "无规则可比（不是审查通过）" in text and "实证完成：2" in text
    ledger["baseline"] = "spec"
    assert "实证完成：0" in render(tmp_path, ledger)
    ledger["baseline"] = "none"
    ledger["visual_acceptance"] = {"facet_ids": []}
    assert "实证完成：0" in render(tmp_path, ledger)


def test_partial_review_never_claims_consistency(tmp_path):
    ledger, report = fixture(tmp_path)
    report["could_not"] = ["缺少验收规格，不能完整比较"]
    text = render(tmp_path, ledger, report)
    assert "未能审查：缺少验收规格" in text and "实证完成：0" in text


@pytest.mark.parametrize("change", ["quote", "source_ids", "requirement_refs", "group", "finding_ref", "independence", "supersedes"])
def test_bad_report_bindings_fail_closed(tmp_path, change):
    ledger, report = fixture(tmp_path)
    if change == "quote":
        report["rules"][0]["quote"] = "本期必须支持深色主题。"
    elif change == "source_ids":
        report["source_ids"] = []
    elif change == "requirement_refs":
        report["rules"][2]["requirement_refs"] = []
    elif change == "group":
        report["comparison_groups"] = []
    elif change == "finding_ref":
        report["findings"][0]["rule_refs"] = ["RULE1", "invented"]
    elif change == "independence":
        report["reviewer"]["independent"] = False
    else:
        report["rules"][0]["supersedes"] = ["invented"]
    text = render(tmp_path, ledger, report)
    assert "规则审查不可采信" in text and "实证完成：0" in text


@pytest.mark.parametrize("field", ["report_digest", "source_digest", "escape"])
def test_evidence_cannot_be_swapped_or_read_outside_run(tmp_path, field):
    ledger, _ = fixture(tmp_path)
    review = ledger["rule_consistency"]
    if field == "report_digest":
        review["report_digest"] = "0" * 64
    elif field == "source_digest":
        review["sources"][0]["sha256"] = "0" * 64
    else:
        review["sources"][0]["ref"] = "../outside.md"
    text = render(tmp_path, ledger)
    assert "规则审查不可采信" in text and "实证完成：0" in text


@pytest.mark.parametrize("scope_basis", ["本期与下期不同版本", "应用浅色与系统深色是不同条件", "管理员与普通用户角色不同", "规则有明确适用例外"])
def test_compatible_assessments_are_not_promoted_to_conflicts(tmp_path, scope_basis):
    # These are reviewer fixtures, not claims that Python understands the sentence.
    ledger, report = fixture(tmp_path)
    report["findings"] = []
    report["comparison_groups"][0].update(result="compatible", basis=scope_basis)
    text = render(tmp_path, ledger, report)
    assert scope_basis in text and "本次材料未发现冲突候选" in text
    assert "实证完成：2" in text and "缺口：0" in text


@pytest.mark.parametrize("change", ["append_source", "requirement_text", "requirement_id", "missing_source_digest", "missing_requirements_digest"])
def test_input_changes_invalidate_old_review_and_clarification(tmp_path, change):
    ledger, report = fixture(tmp_path)
    ledger["rule_consistency"]["decisions"] = [decision(ledger)]
    assert "实证完成：2" in render(tmp_path, ledger)
    if change == "append_source":
        source = tmp_path / "evidence/rules/sources/spec.md"
        source.write_text(source.read_text() + "本期按钮必须始终显示。\n", encoding="utf-8")
        # Old quotations still match and ledger agrees with the NEW file; only the
        # independent report's input binding can detect this stale review.
        ledger["rule_consistency"]["sources"][0]["sha256"] = digest(source)
    elif change == "requirement_text":
        ledger["requirements"][0]["text"] = "本期必须支持深色主题"
    elif change == "requirement_id":
        ledger["requirements"][0]["id"] = "R-new"
    else:
        report.pop("source_digests" if change == "missing_source_digest" else "requirements_digest")
        path = tmp_path / "evidence/rules/review.json"
        save(path, report)
        ledger["rule_consistency"]["report_digest"] = digest(path)
        ledger["rule_consistency"]["decisions"][0]["report_digest"] = digest(path)
    text = render(tmp_path, ledger)
    assert "规则审查不可采信" in text and "实证完成：0" in text
    assert "须重新独立审查" in text


@pytest.mark.parametrize("legacy", [False, True])
@pytest.mark.parametrize("refs", [["R-typo"], ["R2", "R-typo"]])
def test_unknown_requirement_references_cannot_bypass_pending_conflict(tmp_path, legacy, refs):
    ledger, _ = fixture(tmp_path)
    entry = ledger["entries"][0]
    if legacy:
        entry.pop("requirement_refs")
        entry["requirement_ref"] = ", ".join(refs)
    else:
        entry["requirement_refs"] = refs
    text = render(tmp_path, ledger)
    assert "实证完成：1" in text  # R2 only; misspelled references do not count as unrelated
    assert "规则基线未澄清" in text


def test_partly_unmapped_finding_has_unknown_impact(tmp_path):
    ledger, report = fixture(tmp_path)
    report["rules"][1]["requirement_refs"] = []
    text = render(tmp_path, ledger, report)
    assert "实证完成：0" in text
    assert "规则审查不可采信" not in text  # valid report, but impact cannot be bounded


def test_packaged_rule_resources_are_identical():
    root = Path(__file__).resolve().parents[3]
    canonical = root / "claude/superstorm/knowledge/cross-exam"
    codex = root / "codex/cross-exam-skill"
    for path in ("rule_consistency.py", "rule-consistency.md", "prompts/rules.md"):
        assert (canonical / path).read_bytes() == (codex / path).read_bytes()
