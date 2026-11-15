"""product-verify's use-case gate: every acceptance case is walked and the walk is shown.

product-analysis declared `use-case-tree.json` a required input of product-verify, and product-verify
never read it — a seam only the producer guarded (ADR-0010). These tests pin the receiver's side:
coverage by case id, frames for a case with an interface, a recording that cannot replace frames, and
a human report rendered from the same records.
"""
import json
from pathlib import Path

import pytest

from .. import module_isolation

SCRIPTS = str(Path(module_isolation.ORCHESTRATOR).parent)
gate = module_isolation._isolation.load(SCRIPTS, "check_use_case_evidence")

RUN = ".allforai/product-verify"
NODE = "product-verify-web"
EVIDENCE = "evidence/%s/q01/" % NODE


def case(cid="UC-01", **extra):
    return {"id": cid, "title": "下单成功", "kind": "happy", "flow_ref": "F1", "screen_refs": ["S-cart"],
            "given": "购物车里有 2 件商品", "when": "点击「提交订单」", "then": "进入订单详情，状态为待支付", **extra}


def entry(cid="UC-01", **extra):
    return {"case": cid, "medium": "runtime", "verdict": "done",
            "evidence": {"dir": EVIDENCE, "key_observation": "订单详情显示待支付"},
            "readback": {"width": "1280", "locale": "zh-CN"},
            "images": ["01-cart.png", "02-submit.png", "03-order.png"],
            "frames": [{"image": "01-cart.png", "clause": "given", "caption": "购物车 2 件商品"},
                       {"image": "02-submit.png", "clause": "when", "caption": "点击提交订单"},
                       {"image": "03-order.png", "clause": "then", "caption": "订单详情：待支付"}], **extra}


@pytest.fixture
def project(tmp_path):
    directory = tmp_path / RUN / EVIDENCE
    directory.mkdir(parents=True)
    for name in ("01-cart.png", "02-submit.png", "03-order.png"):
        (directory / name).write_bytes(b"\x89PNG" + name.encode())
    (directory / "walk.webm").write_bytes(b"webm")
    return tmp_path


def write(project, cases, entries):
    path = project / gate.CASES
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"cases": cases}, ensure_ascii=False))
    ledger = project / RUN / "evidence-entries" / (NODE + ".json")
    ledger.parent.mkdir(parents=True, exist_ok=True)
    ledger.write_text(json.dumps({"schema": "evidence-entries/v1", "entries": entries}, ensure_ascii=False))


def run(project, capsys, *flags):
    code = gate.main(["--run", RUN, "--root", str(project), *flags])
    return code, capsys.readouterr().out


def refusal(project, **changes):
    return gate.entry_reason(entry(**changes), case(), project / RUN)


def test_a_walked_case_is_admitted_and_the_report_shows_it(project, capsys):
    write(project, [case()], [entry(video="walk.webm")])
    code, out = run(project, capsys)
    assert code == 0, out
    report = (project / RUN / gate.REPORT).read_text(encoding="utf-8")
    assert "购物车里有 2 件商品" in report and "进入订单详情，状态为待支付" in report   # the case, in its own words
    assert 'src="%s03-order.png"' % EVIDENCE in report                                # the frame, where it lies
    assert '<video controls preload="metadata" src="%swalk.webm"' % EVIDENCE in report
    assert report.index("01-cart.png") < report.index("02-submit.png") < report.index("03-order.png")


def test_a_case_nobody_walked_refuses_the_gate_and_is_named(project, capsys):
    write(project, [case(), case("UC-02", title="库存不足", kind="exception")], [entry()])
    code, out = run(project, capsys)
    assert code == 1 and "没有证据条目的用例（1）：UC-02" in out
    assert "没有人走过这条用例" in (project / RUN / gate.REPORT).read_text(encoding="utf-8")
    assert run(project, capsys, "--partial")[0] == 0        # an earlier split node does not own coverage


def test_a_deferred_case_is_out_of_scope_not_missing(project, capsys):
    write(project, [case(), case("UC-02", deferred_by="F-coupon（post_launch）")], [entry()])
    code, out = run(project, capsys)
    assert code == 0 and "本期不做 1" in out


def test_a_failed_walk_is_covered_and_reported_as_failed(project, capsys):
    write(project, [case()], [entry(verdict="gap", frames=[
        {"image": "03-order.png", "clause": "then", "caption": "停在购物车，没有跳转"}])])
    code, out = run(project, capsys)
    assert code == 0 and "未通过 1" in out      # coverage is this gate's; the verdict is the node's


def test_an_interface_case_needs_frames_that_show_start_and_outcome(project):
    assert "有界面却没有帧" in refusal(project, frames=[])
    assert "录像不能代替帧" in refusal(project, frames=[], video="walk.webm")
    assert "须同时有 given 帧和 then 帧" in refusal(project, frames=entry()["frames"][1:])
    assert "顺序" in refusal(project, frames=list(reversed(entry()["frames"])))
    assert "缺说明" in refusal(project, frames=[{"image": "01-cart.png", "clause": "given", "caption": " "}])
    assert "不在本条目的 images 里" in refusal(project, images=["01-cart.png"])
    assert "不是视频文件" in refusal(project, video="../../../../../outside.webm")
    assert "不是视频文件" in refusal(project, video="01-cart.png")


def test_a_case_without_an_interface_needs_no_frames(project):
    headless = case(screen_refs=[])
    assert gate.entry_reason(entry(frames=[], images=[]), headless, project / RUN) == ""
    assert gate.entry_reason(entry(verdict="unprovable", frames=[]), case(), project / RUN) == ""


def test_an_entry_for_an_unknown_case_is_refused(project, capsys):
    write(project, [case()], [entry(), entry("UC-99")])
    code, out = run(project, capsys)
    assert code == 1 and "条目指向不存在的用例: UC-99" in out


@pytest.mark.parametrize("broken, said", [
    ({"id": ""}, "缺 id"),
    ({"then": ""}, "缺 then"),
    ({"kind": "smoke"}, "kind 须为"),
    ({"screen_refs": None}, "缺 screen_refs"),
])
def test_a_malformed_case_is_an_upstream_defect_the_gate_does_not_repair(project, capsys, broken, said):
    write(project, [case(**broken)], [entry()])
    code, out = run(project, capsys)
    assert code == 1 and gate.UPSTREAM in out and said in out
    assert not (project / RUN / gate.REPORT).exists()


def test_a_missing_case_file_is_an_upstream_defect(project, capsys):
    code, out = run(project, capsys)
    assert code == 1 and "用例文件读不到" in out


def test_duplicate_case_ids_are_refused(project, capsys):
    write(project, [case(), case()], [entry()])
    assert "用例 id 重复: UC-01" in run(project, capsys)[1]


def test_the_report_escapes_what_cases_and_captions_say(project, capsys):
    write(project, [case(title="<script>alert(1)</script>")], [entry()])
    run(project, capsys)
    report = (project / RUN / gate.REPORT).read_text(encoding="utf-8")
    assert "<script>alert" not in report and "&lt;script&gt;" in report


def test_several_walks_of_one_case_show_the_worst(project, capsys):
    write(project, [case()], [entry(), entry(verdict="gap", readback={"width": "390"})])
    code, out = run(project, capsys)
    assert code == 0 and "未通过 1" in out and "通过 1" not in out.replace("未通过 1", "")
