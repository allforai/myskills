#!/usr/bin/env python3
"""visual-verify gate — the device axis, in-app readback and reviewer binding (ADR-0008, #61).

visual-verify captures across the axes visual acceptance uses. This gate re-expands the node's
surface inventory with the shared matrix (`visual/`, the visual acceptance mirror beside `engine/`;
`shared/visual-acceptance` in the source tree), so a device axis that does not straddle every layout
threshold and reach both ends of the width range expands nothing; owes the reviewer a capture for
every case the matrix keeps, so a fixed-width column is seen at the wide end; refuses a capture whose
in-app readback does not match its declared axis value or width; requires the frozen layout rules to
declare pinned or fluid with both ends; binds every ledger entry to the captures it judges; and binds
each reviewer report to every original image. Reviewer findings are returned, never judged here
(ADR-0002/0003). Every check returns '' or the refusal reason.

Usage: check_visual_evidence.py --run .allforai/visual-verify --node <node_id> [--root .]
"""
import importlib.util
import json
import sys
from pathlib import Path

from check_evidence import entries_reason as ledger_entries_reason, read_entries

INVENTORY = "surface-inventory.json"
MATRIX = "case-matrix.json"
BASELINE = "visual-baseline.json"
MANIFEST = "screenshot-manifest.json"
REVIEWS = ("visual-review-1.json", "visual-review-2.json")   # reviewer one required; reviewer two when it ran
EVIDENCE = "evidence"
# the shared report shape says high|medium|low; the node's own vocabulary blocker|major|minor is read too
BLOCKING = {"high", "medium", "blocker", "major"}
SEVERITIES = BLOCKING | {"low", "minor"}
AXES = ("state", "device", "os", "appearance", "dynamic_type", "locale", "orientation")

_VISUAL = {}


def visual(name):
    """The visual acceptance module `name` (matrix, validation) from the mirror beside this file — or, for
    the shared orchestrator copy, from shared/visual-acceptance — loaded by path so no same-named module
    on sys.path can answer for it. None when no mirror is installed; callers turn that into a reason."""
    if name in _VISUAL:
        return _VISUAL[name]
    here = Path(__file__).resolve()
    for base in (here.with_name("visual"), here.parents[2] / "visual-acceptance"):
        path = base / (name + ".py")
        if path.is_file():
            spec = importlib.util.spec_from_file_location("meta_skill_visual_" + name, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            _VISUAL[name] = module
            return module
    _VISUAL[name] = None
    return None


def read_json(path, label):
    """(object, '') or (None, reason) — a missing or malformed frozen input names itself, never a traceback."""
    try:
        return json.loads(Path(path).read_text(encoding="utf-8")), ""
    except (OSError, ValueError, UnicodeError) as exc:
        return None, "%s不可读: %s（%s）" % (label, Path(path).name, exc)


def describe(case):
    """A case as the reviewer would name it: surface, the seven axes, id — so an untested width is visible."""
    return "%s %s (%s)" % (case.get("surface"), " / ".join(str(case.get(a, "?")) for a in AXES), case.get("id"))


# --- the matrix ---

def inventory_cases(inventory):
    """({id: case}, '') from the shared matrix, or ({}, reason). The matrix rules are the engine's: a web
    inventory declares platform, form_factor, width_range and layout_thresholds, and the device axis must
    straddle every threshold and reach both ends, or nothing expands."""
    matrix = visual("matrix")
    if matrix is None:
        return {}, "视觉验收包不可用：scripts/visual 未随插件安装"
    if not isinstance(inventory, dict):
        return {}, "页面清单须是对象"
    try:
        rows = matrix.expand_inventory(inventory)
    except (ValueError, KeyError, TypeError, AttributeError) as exc:
        return {}, "页面清单不展开: %s" % exc
    return {c["id"]: c for c in rows}, ""


def frozen_matrix_reason(rows, cases):
    """The matrix file the reviewer worked from is the expansion row for row; a row may add only the
    not_applicable annotation keys (the same rule cross-exam applies to its ledger rows)."""
    if not isinstance(rows, list):
        return "冻结矩阵须是列表: " + MATRIX
    if not visual("validation").same_matrix(rows, cases):
        return "冻结矩阵与页面清单的展开不一致: " + MATRIX
    return ""


def kept_cases(rows, cases):
    """The cases a capture is owed: not abstracted away, not annotated not_applicable with reason and basis."""
    annotated = {r.get("id"): r for r in rows if isinstance(r, dict)}
    kept = {}
    for cid, case in cases.items():
        row = annotated.get(cid, case)
        if case.get("abstracted_by"):
            continue
        if row.get("applicability") == "not_applicable" and row.get("reason") and row.get("basis"):
            continue
        kept[cid] = case
    return kept


# --- captures ---

def capture_reason(case, capture, inventory, support, rtl_locales, evidence_dir):
    """'' when the capture is the case it claims: same seven axes, a build and a time, the Web capture
    fields, a viewport with native scrollbars for a scroll state, RTL read back for an RTL locale, the
    in-app readback of every axis the code supports and of the width, and images on disk that hash to
    the recorded digests. Setting an axis is not the same as the app rendering it."""
    validation, engine = visual("validation"), visual("matrix").engine
    cid = case.get("id", "?")
    if not isinstance(capture, dict):
        return "截图记录须是对象: " + cid
    if any(capture.get(k) != case.get(k) or not capture.get(k) for k in AXES):
        return "截图环境与用例不匹配: " + cid
    if not capture.get("build") or not capture.get("captured_at"):
        return "缺构建或截图时间: " + cid
    reason = (validation.web_capture_reason(case, capture, inventory.get("platform"))
              or validation.scroll_reason(case, capture)
              or validation.rtl_reason(case, capture, rtl_locales)
              or engine.readback_reason(case, capture, support)
              or validation.width_readback_reason(case, capture, inventory))
    if reason:
        return reason
    refs = capture.get("images")
    if not isinstance(refs, list) or not refs:
        return "缺真实截图: " + cid
    return engine.images_reason(capture, evidence_dir)


def manifest_reason(manifest, cases, kept, inventory, evidence_dir):
    """'' when every kept case has exactly one capture and each capture passes `capture_reason`; the
    first case nobody captured is named with its axes, so the width that went untested is on the record."""
    captures = manifest.get("captures") if isinstance(manifest, dict) else None
    if not isinstance(captures, list):
        return "截图清单缺 captures 列表: " + MANIFEST
    by_case = {}
    for capture in captures:
        cid = capture.get("case_id") if isinstance(capture, dict) else None
        if cid not in cases:
            return "截图引用清单外的用例: %s" % cid
        if cid in by_case:
            return "截图用例 id 重复: " + cid
        by_case[cid] = capture
    matrix = visual("matrix")
    try:
        support = matrix.merged_support(inventory.get("axis_support"), inventory.get("locales"))
    except ValueError as exc:
        return "页面清单不展开: %s" % exc
    rtl_locales = (inventory.get("locales") or {}).get("rtl") or []
    for cid, case in kept.items():
        if cid not in by_case:
            return "用例未拍: " + describe(case)
        reason = capture_reason(case, by_case[cid], inventory, support, rtl_locales, evidence_dir)
        if reason:
            return reason
    return ""


def captures_by_case(manifest):
    return {c.get("case_id"): c for c in manifest.get("captures", []) if isinstance(c, dict)}


# --- ledger entries over the captures ---

def entries_binding_reason(entries, cases, captures, run_dir, evidence_dir):
    """'' when every entry judges cases of the matrix through this manifest, its build is the build every
    capture it judges carries, it lists every image those captures took, and every capture is judged by
    some entry; an entry may not judge a case it never looked at, and a capture nobody judged is not
    evidence of anything."""
    engine = visual("matrix").engine
    claimed = set()
    for index, entry in enumerate(entries, 1):
        ids = entry.get("visual_case_ids") if isinstance(entry, dict) else None
        if not isinstance(ids, list) or not ids or len(ids) != len(set(ids)) or not set(ids) <= cases.keys():
            return "#%d: 视觉用例引用无效" % index
        if entry.get("evidence_manifest") != MANIFEST:
            return "#%d: 条目须指向截图清单 %s" % (index, MANIFEST)
        directory, reason = engine.evidence_dir(entry, run_dir)
        if reason:
            return "#%d: %s" % (index, reason)
        listed = {(directory / ref).resolve() for ref in entry.get("images") or [] if isinstance(ref, str)}
        for cid in ids:
            capture = captures.get(cid)
            if capture is None:
                continue
            if capture.get("build") != entry.get("build"):
                return "#%d: 截图构建与条目不一致: %s" % (index, cid)
            taken = {(Path(evidence_dir) / ref).resolve() for ref in capture.get("images") or []}
            if not taken <= listed:
                return "#%d: 条目未列出用例的截图: %s" % (index, cid)
        claimed |= set(ids)
    for cid, capture in captures.items():
        if cid not in claimed:
            return "截图未被任何条目裁决: " + describe(cases[cid])
    return ""


# --- reviewer reports ---

def review_reason(report, images, name):
    """'' when the report saw every original: inspected_images covers them with matching digests, the
    status is passed|findings, and every finding names a rule, an observation and inspected images with
    a legal severity. What the reviewer concluded is theirs (ADR-0002/0003); this only checks they looked."""
    if not isinstance(report, dict):
        return "reviewer 报告须是对象: " + name
    inspected = report.get("inspected_images")
    if not isinstance(inspected, list):
        return "reviewer 未检查全部原图: %s 缺 inspected_images" % name
    missing = sorted(set(images) - set(inspected))
    if missing:
        return "reviewer 未检查全部原图: %s 缺 %s" % (name, ", ".join(missing))
    digests = report.get("image_digests") if isinstance(report.get("image_digests"), dict) else {}
    if any(digests.get(ref) != digest for ref, digest in images.items()):
        return "reviewer 图片内容绑定不匹配: " + name
    if report.get("status") not in ("passed", "findings"):
        return "reviewer 未完成: " + name
    findings = report.get("findings")
    if not isinstance(findings, list):
        return "reviewer 报告缺 findings 列表: " + name
    seen = set()
    for finding in findings:
        fid = finding.get("id") if isinstance(finding, dict) else None
        if not isinstance(fid, str) or not fid or fid in seen:
            return "发现缺唯一 id: " + name
        seen.add(fid)
        if not finding.get("rule") or not finding.get("observation") or not finding.get("images"):
            return "发现缺规则、观察或图片: %s %s" % (name, fid)
        if not isinstance(finding["images"], list) or not set(finding["images"]) <= set(inspected) \
                or finding.get("severity") not in SEVERITIES:
            return "发现引用或严重度无效: %s %s" % (name, fid)
    return ""


def blocking_findings(report, name):
    return ["%s:%s" % (name, f["id"]) for f in report.get("findings", []) if f.get("severity") in BLOCKING]


# --- the gate ---

def gate(run_dir, root, node_id):
    """{reason, blocking, cases, captured, reviewers}: `reason` names the rule the run breaks ('' when
    every frozen input, capture, entry and report holds); `blocking` is the union of the reviewers'
    high/medium findings, each as `<report>:<finding id>`. The ledger entries are checked first the way
    every /run gate is (`check_evidence.entries_reason`: shape, author marker, build against the tree now)."""
    root = Path(root)
    run_dir = Path(run_dir) if Path(run_dir).is_absolute() else root / run_dir
    result = {"reason": "", "blocking": [], "cases": 0, "captured": 0, "reviewers": 0}

    def refuse(reason):
        result["reason"] = reason
        return result

    inventory, reason = read_json(run_dir / INVENTORY, "页面清单")
    if reason:
        return refuse(reason)
    cases, reason = inventory_cases(inventory)
    if reason:
        return refuse(reason)
    rows, reason = read_json(run_dir / MATRIX, "冻结矩阵")
    if reason:
        return refuse(reason)
    reason = frozen_matrix_reason(rows, cases)
    if reason:
        return refuse(reason)
    kept = kept_cases(rows, cases)
    result["cases"] = len(kept)
    baseline, reason = read_json(run_dir / BASELINE, "冻结规则")
    if reason:
        return refuse(reason)
    if not isinstance(baseline, dict):
        return refuse("冻结规则须是对象: " + BASELINE)
    reason = visual("validation").pinned_layout_reason(baseline, inventory)
    if reason:
        return refuse(reason)
    manifest, reason = read_json(run_dir / MANIFEST, "截图清单")
    if reason:
        return refuse(reason)
    evidence_dir = run_dir / EVIDENCE
    try:
        reason = manifest_reason(manifest, cases, kept, inventory, evidence_dir)
    except (OSError, UnicodeError) as exc:
        reason = "证据文件不可读: %s" % exc
    if reason:
        return refuse(reason)
    captures = captures_by_case(manifest)
    result["captured"] = len(captures)
    reason = ledger_entries_reason(run_dir, root, node_id)
    if reason:
        return refuse(reason)
    entries, reason = read_entries(run_dir, node_id, root)
    if reason:
        return refuse(reason)
    reason = entries_binding_reason(entries, cases, captures, run_dir, evidence_dir)
    if reason:
        return refuse(reason)
    images = {ref: capture["image_digests"][ref] for capture in captures.values() for ref in capture["images"]}
    for name in REVIEWS:
        path = run_dir / name
        if not path.is_file():
            if name == REVIEWS[0]:
                return refuse("缺 reviewer 报告 " + name)
            continue
        report, reason = read_json(path, "reviewer 报告")
        if reason:
            return refuse(reason)
        reason = review_reason(report, images, name)
        if reason:
            return refuse(reason)
        result["reviewers"] += 1
        result["blocking"].extend(blocking_findings(report, name))
    return result


def state(result):
    """The node's state as the capability text names it: refused (a rule broken, named in `reason`),
    failed_visual_review (a reviewer's blocking finding stands), or passed."""
    if result["reason"]:
        return "refused"
    return "failed_visual_review" if result["blocking"] else "passed"


def main(argv):
    import argparse
    parser = argparse.ArgumentParser(prog="check_visual_evidence.py", description=__doc__.split("\n\n")[0])
    parser.add_argument("--run", required=True, metavar="RUN_DIR")
    parser.add_argument("--node", required=True)
    parser.add_argument("--root", default=".")
    args = parser.parse_args(argv[1:])
    result = gate(args.run, Path(args.root).resolve(), args.node)
    verdict = state(result)
    if verdict == "refused":
        print("REFUSED %s: %s" % (args.run, result["reason"]))
        return 1
    if verdict == "failed_visual_review":
        print("FAILED_VISUAL_REVIEW %s: %d blocking finding(s): %s" % (
            args.run, len(result["blocking"]), ", ".join(result["blocking"])))
        return 1
    print("OK: passed — %d cases, %d captures, %d reviewer report(s) for %s" % (
        result["cases"], result["captured"], result["reviewers"], args.node))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
