"""Packaging/guard regression checks, not proof of live agent behavior."""
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("simplicity_sync", Path(__file__).with_name("sync.py"))
SYNC = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SYNC)
PACKAGES = (
    ("claude/superstorm", "skills/keep-code-simple/SKILL.md"),
    ("codex/cross-exam-skill", "keep-code-simple/SKILL.md"),
    ("pi/cross-exam", "skills/keep-code-simple/SKILL.md"),
)


def protocol_ref(package, entry):
    text = entry.read_text(encoding="utf-8")
    refs = re.findall(r"`([^`\n]*protocol\.md)`", text)
    if len(refs) != 1:
        raise AssertionError(f"Expected one protocol pointer in {entry}: {refs}")
    ref = refs[0]
    if ref.startswith("${CLAUDE_PLUGIN_ROOT}/"):
        return package / ref.removeprefix("${CLAUDE_PLUGIN_ROOT}/")
    return entry.parent / ref


class MirrorTests(unittest.TestCase):
    def test_committed_mirrors_match(self):
        self.assertEqual(SYNC.sync(check=True), [])

    def test_check_reports_missing_and_changed_without_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.md"
            source.write_text("canonical", encoding="utf-8")
            missing = root / "missing/protocol.md"
            changed = root / "changed.md"
            changed.write_text("drift", encoding="utf-8")
            targets = (missing, changed)
            self.assertEqual(SYNC.sync(True, source, targets), [str(p) for p in targets])
            self.assertFalse(missing.parent.exists())
            self.assertEqual(changed.read_text(), "drift")
            SYNC.sync(False, source, targets)
            self.assertEqual(SYNC.sync(True, source, targets), [])
            self.assertEqual(SYNC.sync(False, source, targets), [])

    def test_missing_source_fails_before_any_write(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "target.md"
            target.write_text("keep", encoding="utf-8")
            with self.assertRaises(FileNotFoundError):
                SYNC.sync(False, Path(directory) / "absent.md", [target])
            self.assertEqual(target.read_text(), "keep")


class PackageTests(unittest.TestCase):
    def test_installed_packages_resolve_protocol_without_repository(self):
        for relative, entry_relative in PACKAGES:
            with self.subTest(platform=relative), tempfile.TemporaryDirectory() as directory:
                package = Path(directory) / "installed"
                shutil.copytree(ROOT / relative, package,
                                ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", "node_modules"))
                entry = package / entry_relative
                target = protocol_ref(package, entry).resolve()
                self.assertTrue(target.is_relative_to(package.resolve()))
                self.assertEqual(target.read_bytes(), SYNC.SOURCE.read_bytes())

    def test_entries_are_named_discoverable_and_explicit(self):
        for relative, entry_relative in PACKAGES:
            text = (ROOT / relative / entry_relative).read_text(encoding="utf-8")
            with self.subTest(platform=relative):
                self.assertTrue(text.startswith("---\nname: keep-code-simple\n"))
                self.assertRegex(text, r"(?m)^description: .+")
                self.assertNotIn("disable-model-invocation: true", text)
                self.assertIn("never", text.split("---", 2)[1].lower())

    def test_pi_manifest_loads_only_the_ported_skill(self):
        package = ROOT / "pi/cross-exam"
        manifest = json.loads((package / "package.json").read_text())
        self.assertEqual(manifest["pi"], {"skills": ["./skills/keep-code-simple"]})
        for path in manifest["pi"]["skills"]:
            self.assertTrue((package / path / "SKILL.md").is_file())

    def test_codex_router_points_to_the_discoverable_entry(self):
        package = ROOT / "codex/cross-exam-skill"
        router = (package / "SKILL.md").read_text(encoding="utf-8")
        before_completion = router.split("# cross-exam —", 1)[0]
        self.assertIn("./keep-code-simple/SKILL.md", before_completion)
        self.assertIn("do not continue this file", before_completion)
        self.assertIn("keep-code-simple/SKILL.md", (package / "AGENTS.md").read_text())

    def test_claude_hook_blocks_bare_and_namespaced_entries(self):
        hook = ROOT / "claude/superstorm/hooks/user-only-skills.sh"
        for name in ("keep-code-simple", "superstorm:keep-code-simple",
                     "cross-exam", "product-review", "superstorm"):
            with self.subTest(skill=name):
                result = subprocess.run(["bash", str(hook)], text=True, capture_output=True,
                                        input=json.dumps({"tool_input": {"skill": name}}), timeout=10)
                self.assertEqual(result.returncode, 2)
                self.assertIn("user-invoked only", result.stderr)
        result = subprocess.run(["bash", str(hook)], text=True, capture_output=True,
                                input=json.dumps({"tool_input": {"skill": "ordinary-skill"}}), timeout=10)
        self.assertEqual(result.returncode, 0)

    def test_claude_manifests_advertise_entry_without_version_drift(self):
        plugin = json.loads((ROOT / "claude/superstorm/.claude-plugin/plugin.json").read_text())
        for path in ("claude/superstorm/.claude-plugin/marketplace.json", ".claude-plugin/marketplace.json"):
            listing = json.loads((ROOT / path).read_text())
            entry = next(p for p in listing["plugins"] if p["name"] == "superstorm")
            self.assertEqual(entry["version"], plugin["version"])
            self.assertIn("/keep-code-simple", entry["description"])
        self.assertIn("/keep-code-simple", plugin["description"])


class GuardTests(unittest.TestCase):
    def test_shared_safety_and_decision_guards_remain_explicit(self):
        text = SYNC.SOURCE.read_text(encoding="utf-8")
        # These pin authority/evidence boundaries, not whether a model obeys them.
        guards = (
            "User-invoked only", "Advice only", "No execution",
            "No mid-investigation questions",
            "Data and money are high-impact regardless of frequency",
            "不能把“接受数据/资金风险”做成简化选项",
            "未查", "实现等价", "覆盖取舍", "没有数据就写未知",
            "已启动的派发失败不是自动换模式的许可",
            "不写死品牌或型号", "不上传私有代码",
            "接受建议不代表授权实施", "不自动改代码",
        )
        for guard in guards:
            with self.subTest(guard=guard):
                self.assertIn(guard, text)

    def test_evidence_certainty_and_model_provenance_guards(self):
        text = SYNC.SOURCE.read_text(encoding="utf-8")
        for guard in (
            "区分源码可证明的行为、未知的外部条件和可能后果",
            "外部契约未确认时，不把风险写成必然事故",
            "未查的外部实现能否使该后果不成立",
            "返回注入账本的索引结果不证明返回共享引用",
            "不降低资金/数据风险的优先级",
            "`resolved` 只接受宿主 metadata/receipt，并引用出处",
            "无法取得则写 `unknown`",
            "调查员自报另标 `self-reported`",
        ):
            with self.subTest(guard=guard):
                self.assertIn(guard, text)

    def test_pi_dispatch_uses_async_discovery_and_single_workflow(self):
        text = (ROOT / PACKAGES[2][0] / PACKAGES[2][1]).read_text(encoding="utf-8")
        for boundary in ('action:"list", capabilities:true', "executable", "runner.available === true",
                         "一个顶层", "async:true", "runs.all", "有序数组", "不轮询", "同协议重试"):
            self.assertIn(boundary, text)


if __name__ == "__main__":
    unittest.main()
