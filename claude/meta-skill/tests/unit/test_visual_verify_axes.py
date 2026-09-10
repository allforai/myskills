"""visual-verify captures across the device axis with readback (ADR-0008, #61).

The gate re-expands the node's surface inventory with the shared visual acceptance matrix (the `visual/`
mirror beside `engine/`), owes the reviewer a capture for every case the matrix keeps, refuses a capture
whose in-app readback does not match its declared axis value or width, requires the frozen layout rules
to declare pinned or fluid with both ends, and binds each reviewer report to every original image. The
fixture is the one the protocol names: an 820px centered column, captured at 1920, lands as a finding.
"""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from .. import module_isolation

SCRIPTS = str(Path(module_isolation.ORCHESTRATOR).parent)
_gate, _capture, _check = module_isolation._isolation.load(SCRIPTS, "check_visual_evidence", "capture_evidence",
                                                           "check_evidence")
gate, state = _gate.gate, _gate.state
AXES = _gate.AXES

RUN = ".allforai/visual-verify"
NODE = "visual-verify-web"
WIDE = "1920x1080@1"
INVENTORY = {
    "platform": "web", "form_factor": "desktop",
    "width_range": {"min": 1024, "max": 1920, "basis": "electron/main.ts:12 minWidth 1024; external display"},
    "layout_thresholds": [{"width": 1280, "basis": "src/styles/layout.css:14 @media (min-width: 1280px)"}],
    "axis_support": {"appearance": {"supported": ["light", "dark"], "basis": "src/theme.ts:9 data-theme"}},
    "surfaces": [{"id": "home", "entry": "/", "kind": "page", "scrollable": False,
                  "axes": {"state": ["default", "resize-grow-to-max"], "device": ["1024x768@1", "1280x800@1", WIDE],
                           "os": ["Chromium 131"], "appearance": ["light", "dark"], "dynamic_type": ["zoom 100%"],
                           "locale": ["zh-CN"], "orientation": ["landscape"]}}]}
ENDS = {"1024": {"empty": "两侧各 ≤ 内容宽度 15%"}, "1920": {"empty": "两侧各 ≤ 内容宽度 40%，其余由侧栏与附件栏填充"}}
PINNED = {"rule": "消息列 820px 居中", "pinned": True, "ends": ENDS}
BASELINE = {"categories": {"layout": {"rules": [PINNED], "confirmation": "用户：列宽照设计稿钉 820，宽屏两侧交给侧栏",
                                      "confirmed_at": "2026-09-10T10:00:00+08:00"}}}
PROFILE = {"scroll_width": 1920, "client_width": 1905, "scroll_height": 900, "client_height": 900, "gutter_px": 15,
           "overflow_x": "visible", "overflow_y": "auto", "nested_scrollers": []}
FINDING = {"id": "F1", "severity": "high", "rule": "消息列 820px 居中 — 1920: 两侧各 ≤ 内容宽度 40%",
           "observation": "1920 宽下消息列 820px 居中，右侧空背景约 1100px（内容宽 134%），超出 1920 端允许的 40%"}


def _git(repo, *args):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_AUTHOR_NAME="a", GIT_AUTHOR_EMAIL="a@b", GIT_COMMITTER_NAME="a", GIT_COMMITTER_EMAIL="a@b")
    return subprocess.run(["git", "-C", str(repo), "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null",
                           *args], check=True, capture_output=True, text=True, env=env).stdout.strip()


def _write(root, ref, obj):
    path = root / RUN / ref
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
    return path


def _read(root, ref):
    return json.loads((root / RUN / ref).read_text(encoding="utf-8"))


def _capture_for(case, image, digest):
    width = _gate.visual("matrix").effective_width(case["device"], case["orientation"])
    return {**{a: case[a] for a in AXES}, "case_id": case["id"], "build": "", "captured_at": "2026-09-10T10:30:00+08:00",
            "readback": {"appearance": case["appearance"], "width": width},
            "capture_mode": "viewport", "headless": False, "scrollbars": "native", "scroll_profile": PROFILE,
            "capture_tool": "playwright chromium headed", "images": [image], "image_digests": {image: digest}}


@pytest.fixture
def project(tmp_path, monkeypatch):
    """A committed target project whose visual-verify run captured every case of the matrix, wrote one
    ledger entry over them, and whose reviewer saw the 820px column fail at the wide end."""
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
        monkeypatch.delenv(key, raising=False)
    (tmp_path / "app.py").write_text("print(1)\n")
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-q", "-m", "one")
    _write(tmp_path, "surface-inventory.json", INVENTORY)
    rows = _gate.visual("matrix").expand_inventory(INVENTORY)
    _write(tmp_path, "case-matrix.json", rows)
    _write(tmp_path, "visual-baseline.json", BASELINE)
    evidence = tmp_path / RUN / "evidence" / NODE
    evidence.mkdir(parents=True)
    captures, digests = [], {}
    for case in rows:
        image = "%s/%s.png" % (NODE, case["id"])
        (tmp_path / RUN / "evidence" / image).write_bytes(b"\x89PNG " + case["id"].encode())
        digests[image] = hashlib.sha256((tmp_path / RUN / "evidence" / image).read_bytes()).hexdigest()
        captures.append(_capture_for(case, image, digests[image]))
    wide = next(c for c in captures if c["device"] == WIDE and c["appearance"] == "light" and c["state"] == "default")
    _write(tmp_path, "screenshot-manifest.json", {"captures": captures})
    draft = {"q": "首页在矩阵每个宽度、每种外观下是否按冻结规则渲染？", "facet": "F1", "medium": "runtime", "verdict": "gap",
             "served_by": {"host": "localhost:5173", "process": "vite dev (pid 4242)", "mock_layers": []},
             "readback": {"appearance": "light + dark", "width": "1024 / 1280 / 1920"},
             "evidence": {"dir": "evidence/%s/" % NODE, "key_observation": "1920 宽下消息列两侧空区超出冻结规则"},
             "images": [Path(c["images"][0]).name for c in captures],
             "visual_case_ids": [c["case_id"] for c in captures], "evidence_manifest": "screenshot-manifest.json"}
    entry, reason = _capture.write_entry(tmp_path / RUN, draft, tmp_path, NODE, "visual-verify")
    assert reason == ""
    manifest = _read(tmp_path, "screenshot-manifest.json")
    for capture in manifest["captures"]:
        capture["build"] = entry["build"]
    _write(tmp_path, "screenshot-manifest.json", manifest)
    _write(tmp_path, "visual-review-1.json", {
        "reviewer": "fresh-context sub-agent", "session_id": "fresh-1", "independent": True, "build": entry["build"],
        "inspected_images": sorted(digests), "image_digests": digests, "status": "findings",
        "findings": [{**FINDING, "images": wide["images"]}]})
    return tmp_path, wide


def _edit(root, ref, mutate):
    obj = _read(root, ref)
    mutate(obj)
    _write(root, ref, obj)


# --- the fixture the protocol names ---

def test_an_820px_column_at_1920_lands_as_a_finding(project):
    root, wide = project
    result = gate(RUN, root, NODE)
    assert result["reason"] == ""
    assert result["blocking"] == ["visual-review-1.json:F1"]
    assert state(result) == "failed_visual_review"
    assert result["captured"] == result["cases"] == 12         # 2 states × 3 widths × 2 appearances
    # the finding cites the pinned rule's wide end against the wide capture: the reviewer had a sentence
    finding = _read(root, "visual-review-1.json")["findings"][0]
    assert "1920" in finding["rule"] and finding["images"] == wide["images"]


def test_a_reviewer_that_did_not_open_the_wide_capture_is_refused(project):
    root, wide = project
    _edit(root, "visual-review-1.json", lambda r: r["inspected_images"].remove(wide["images"][0]))
    reason = gate(RUN, root, NODE)["reason"]
    assert reason.startswith("reviewer 未检查全部原图") and wide["images"][0] in reason

    _edit(root, "visual-review-1.json", lambda r: r["inspected_images"].append(wide["images"][0]))
    _edit(root, "visual-review-1.json", lambda r: r["image_digests"].update({wide["images"][0]: "0" * 64}))
    assert gate(RUN, root, NODE)["reason"] == "reviewer 图片内容绑定不匹配: visual-review-1.json"


def test_a_passing_review_passes_and_a_second_reviewer_adds_to_the_union(project):
    root, wide = project
    _edit(root, "visual-review-1.json", lambda r: r.update(status="passed", findings=[]))
    result = gate(RUN, root, NODE)
    assert result["reason"] == "" and result["blocking"] == [] and state(result) == "passed"
    second = {**_read(root, "visual-review-1.json"), "session_id": "fresh-2", "reviewer": "codex exec", "status": "findings",
              "findings": [{**FINDING, "id": "F7", "severity": "major", "images": wide["images"]}]}
    _write(root, "visual-review-2.json", second)
    result = gate(RUN, root, NODE)
    assert result["blocking"] == ["visual-review-2.json:F7"] and state(result) == "failed_visual_review"
    _edit(root, "visual-review-2.json", lambda r: r["findings"][0].update(images=["not/inspected.png"]))
    assert gate(RUN, root, NODE)["reason"] == "发现引用或严重度无效: visual-review-2.json F7"


# --- the device axis comes from the code, not from the developer's window ---

def test_an_inventory_whose_device_axis_misses_the_wide_end_does_not_expand(project):
    root, _ = project
    _edit(root, "surface-inventory.json", lambda i: i["surfaces"][0]["axes"].update(device=["1024x768@1", "1280x800@1"]))
    reason = gate(RUN, root, NODE)["reason"]
    assert reason == "页面清单不展开: device axis misses width range end 1024..1920: home"

    _edit(root, "surface-inventory.json", lambda i: i.pop("form_factor"))
    assert "form_factor" in gate(RUN, root, NODE)["reason"]

    _edit(root, "surface-inventory.json", lambda i: i.update(form_factor="desktop", width_range={**i["width_range"], "max": 1512}))
    assert "desktop width floor 1920" in gate(RUN, root, NODE)["reason"]

    def mobile_without_a_range(inventory):     # both ends straddle every in-range threshold; without a range they bite
        inventory.pop("width_range")
        inventory.update(form_factor="mobile")
        inventory["surfaces"][0]["axes"].update(device=["1024x768@1"])
    _edit(root, "surface-inventory.json", mobile_without_a_range)
    assert gate(RUN, root, NODE)["reason"] == "页面清单不展开: device axis misses layout threshold 1280: home"


def test_the_wide_case_must_be_captured(project):
    root, wide = project
    _edit(root, "screenshot-manifest.json",
          lambda m: m.update(captures=[c for c in m["captures"] if c["device"] != WIDE]))
    reason = gate(RUN, root, NODE)["reason"]
    assert reason.startswith("用例未拍: home") and WIDE in reason
    _edit(root, "screenshot-manifest.json", lambda m: m["captures"].append({**m["captures"][0], "case_id": "V-ghost"}))
    assert gate(RUN, root, NODE)["reason"] == "截图引用清单外的用例: V-ghost"


def test_the_frozen_matrix_is_the_expansion(project):
    root, _ = project
    _edit(root, "case-matrix.json", lambda rows: rows.pop())
    assert gate(RUN, root, NODE)["reason"] == "冻结矩阵与页面清单的展开不一致: case-matrix.json"
    (root / RUN / "case-matrix.json").unlink()
    assert gate(RUN, root, NODE)["reason"].startswith("冻结矩阵不可读")


# --- readback: setting an axis is not the same as the app rendering it ---

def test_a_wide_capture_taken_in_the_developers_window_is_refused_by_width(project):
    root, wide = project
    _edit(root, "screenshot-manifest.json",
          lambda m: next(c for c in m["captures"] if c["case_id"] == wide["case_id"])["readback"].update(width=1512))
    assert gate(RUN, root, NODE)["reason"] == "width 读回值 1512 与用例设备宽度 1920 不符: " + wide["case_id"]
    _edit(root, "screenshot-manifest.json",
          lambda m: next(c for c in m["captures"] if c["case_id"] == wide["case_id"])["readback"].pop("width"))
    assert gate(RUN, root, NODE)["reason"] == "capture 缺应用内读回的 width: " + wide["case_id"]


def test_an_appearance_the_app_did_not_apply_is_refused_by_name(project):
    root, _ = project
    manifest = _read(root, "screenshot-manifest.json")
    dark = next(c for c in manifest["captures"] if c["appearance"] == "dark")
    dark["readback"]["appearance"] = "light"
    _write(root, "screenshot-manifest.json", manifest)
    assert gate(RUN, root, NODE)["reason"] == "appearance 轴读回值 light 与用例 dark 不符: " + dark["case_id"]
    del dark["readback"]["appearance"]
    _write(root, "screenshot-manifest.json", manifest)
    assert gate(RUN, root, NODE)["reason"] == "appearance 轴缺应用内读回值: " + dark["case_id"]


def test_a_headless_full_page_capture_and_a_swapped_image_are_refused(project):
    root, wide = project
    manifest = _read(root, "screenshot-manifest.json")
    capture = next(c for c in manifest["captures"] if c["case_id"] == wide["case_id"])
    del capture["scroll_profile"]
    _write(root, "screenshot-manifest.json", manifest)
    assert gate(RUN, root, NODE)["reason"] == "Web capture 缺 scroll_profile: " + wide["case_id"]
    capture["scroll_profile"] = PROFILE
    _write(root, "screenshot-manifest.json", manifest)
    (root / RUN / "evidence" / wide["images"][0]).write_bytes(b"\x89PNG swapped")
    assert gate(RUN, root, NODE)["reason"] == "截图内容摘要不匹配: " + wide["images"][0]


# --- the frozen rule ---

def test_a_pinned_rule_without_its_ends_is_refused(project):
    root, _ = project
    _edit(root, "visual-baseline.json", lambda b: b["categories"]["layout"]["rules"][0].pop("ends"))
    assert gate(RUN, root, NODE)["reason"] == "layout 规则声明钉死（pinned: true）却没写两端空区 ends: 消息列 820px 居中"
    _edit(root, "visual-baseline.json", lambda b: b["categories"]["layout"].update(rules=["消息列 820px 居中"]))
    assert "pinned: true, ends" in gate(RUN, root, NODE)["reason"]
    _edit(root, "visual-baseline.json", lambda b: b["categories"]["layout"].update(rules=[{**PINNED, "pinned": False, "ends": None}]))
    reason = gate(RUN, root, NODE)["reason"]
    assert reason.startswith("layout 规则声明为流式") and "820px" in reason


# --- the ledger entry over the captures ---

def test_entries_bind_the_captures_and_a_stale_tree_is_refused(project):
    root, wide = project
    (root / "app.py").write_text("print(2)\n")
    assert "构建标识不匹配" in gate(RUN, root, NODE)["reason"]
    (root / "app.py").write_text("print(1)\n")
    assert gate(RUN, root, NODE)["reason"] == ""

    entries_file = root / RUN / "evidence-entries" / (NODE + ".json")
    stored = json.loads(entries_file.read_text())
    stored["entries"][0]["visual_case_ids"].remove(wide["case_id"])
    entries_file.write_text(json.dumps(stored))
    assert gate(RUN, root, NODE)["reason"].startswith("截图未被任何条目裁决: home")
    stored["entries"][0]["visual_case_ids"] = ["V-ghost"]
    entries_file.write_text(json.dumps(stored))
    assert gate(RUN, root, NODE)["reason"] == "#1: 视觉用例引用无效"
    entries_file.unlink()
    assert gate(RUN, root, NODE)["reason"].startswith("无证据条目文件")


def test_a_capture_from_another_build_than_its_entry_is_refused(project):
    root, wide = project
    _edit(root, "screenshot-manifest.json",
          lambda m: next(c for c in m["captures"] if c["case_id"] == wide["case_id"]).update(build="older-build"))
    assert gate(RUN, root, NODE)["reason"] == "#1: 截图构建与条目不一致: " + wide["case_id"]


# --- the command ---

def test_the_command_names_the_state_and_exits_nonzero_on_a_finding(project):
    root, _ = project
    cmd = [sys.executable, str(Path(SCRIPTS) / "check_visual_evidence.py"), "--run", RUN, "--node", NODE, "--root", str(root)]
    run = subprocess.run(cmd, capture_output=True, text=True, cwd=root)
    assert run.returncode == 1 and run.stdout.startswith("FAILED_VISUAL_REVIEW") and "visual-review-1.json:F1" in run.stdout
    assert run.stderr == ""
    _edit(root, "visual-review-1.json", lambda r: r.update(status="passed", findings=[]))
    run = subprocess.run(cmd, capture_output=True, text=True, cwd=root)
    assert run.returncode == 0 and run.stdout.startswith("OK: passed")
    (root / RUN / "visual-review-1.json").unlink()
    run = subprocess.run(cmd, capture_output=True, text=True, cwd=root)
    assert run.returncode == 1 and run.stdout.startswith("REFUSED") and "visual-review-1.json" in run.stdout


def test_the_gate_reads_the_visual_mirror_beside_the_engine():
    matrix = _gate.visual("matrix")
    assert Path(matrix.__file__).parent == Path(SCRIPTS) / "visual"
    assert Path(matrix.engine.__file__).parent == Path(SCRIPTS) / "engine"
