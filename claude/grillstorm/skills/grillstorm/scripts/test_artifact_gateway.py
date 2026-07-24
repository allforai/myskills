import hashlib
import os
import subprocess
import tempfile
from pathlib import Path
import unittest

from artifact_gateway import (ArtifactViolation, Change, admit_artifacts,
                              git_changes, normalize_path, validate_contract)


def _contract(cmd="pytest -q"):
    return {
        "schema_version": 1,
        "task_id": "T1",
        "path_rules": [{"pattern": "src/**", "kind": "glob",
                        "operations": ["create", "modify", "delete", "rename"]}],
        "required_outputs": ["src/out.py"],
        "forbidden_paths": ["orchestration.json"],
        "acceptance_cmd_sha256": hashlib.sha256(cmd.encode()).hexdigest(),
        "interface_assertions": [],
        "max_files_changed": 4,
    }


class ContractTests(unittest.TestCase):
    def test_root_and_nested_control_plane_patterns_are_frozen(self):
        from artifact_gateway import _forbidden, CONTROL_PLANE_DEFAULTS
        for path in ("prompts/executor.md", "x/prompts/executor.md",
                     "scripts/run_layers.py", "x/scripts/run_layers.py",
                     "tasks.json", "model-policy.json",
                     "docs/grillstorm/run/specs/module.md",
                     "docs/grillstorm/run/probes/probe-state.json"):
            self.assertTrue(_forbidden(path, CONTROL_PLANE_DEFAULTS), path)

    def test_rejects_legacy_and_operationless_contracts(self):
        for mutation in ({"allowed_paths": ["src"]},
                         {"expected_interfaces": ["api:x"]}):
            contract = _contract(); contract.update(mutation)
            with self.assertRaises(ArtifactViolation):
                validate_contract(contract)
        contract = _contract(); contract["path_rules"] = [{"pattern": "src/**", "kind": "glob"}]
        with self.assertRaises(ArtifactViolation):
            validate_contract(contract)

    def test_posix_normalization_rejects_escape_and_backslash(self):
        for value in ("../x", "/x", "a\\b", "a/../b", ""):
            with self.assertRaises(ArtifactViolation, msg=value):
                normalize_path(value)


class AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "src").mkdir()
        (self.root / "src/out.py").write_text("ok")

    def tearDown(self):
        self.tmp.cleanup()

    def test_admits_exact_artifact_and_rejects_acceptance_drift(self):
        evidence = admit_artifacts(self.root, _contract(),
                                   [Change("create", "src/out.py")], "pytest -q", {})
        self.assertTrue(evidence["admission_sha256"])
        before = evidence["artifact_sha256"]["src/out.py"]
        (self.root / "src/out.py").write_text("supervisor replacement")
        replaced = admit_artifacts(self.root, _contract(),
                                   [Change("create", "src/out.py")], "pytest -q", {})
        self.assertNotEqual(before, replaced["artifact_sha256"]["src/out.py"])
        self.assertNotEqual(evidence["admission_sha256"], replaced["admission_sha256"])
        with self.assertRaisesRegex(ArtifactViolation, "acceptance"):
            admit_artifacts(self.root, _contract(), [Change("create", "src/out.py")],
                            "pytest --changed", {})

    def test_control_plane_undeclared_and_count_are_rejected(self):
        for changes in ([Change("modify", "orchestration.json")],
                        [Change("create", "other.txt")],
                        [Change("create", f"src/{i}.py") for i in range(5)]):
            with self.subTest(changes=changes), self.assertRaises(ArtifactViolation):
                admit_artifacts(self.root, _contract(), changes, "pytest -q", {})

    def test_rename_requires_both_endpoints(self):
        contract = _contract(); contract["path_rules"] = [
            {"pattern": "src/new.py", "kind": "literal", "operations": ["rename"]}]
        (self.root / "src/new.py").write_text("x")
        with self.assertRaisesRegex(ArtifactViolation, "rename source"):
            admit_artifacts(self.root, contract,
                            [Change("rename", "src/new.py", "src/old.py")], "pytest -q", {})

    def test_symlink_escape_hardlink_and_case_collision_rejected(self):
        outside = self.root.parent / "outside-artifact"
        outside.write_text("x")
        (self.root / "src/out.py").unlink()
        (self.root / "src/out.py").symlink_to(outside)
        with self.assertRaisesRegex(ArtifactViolation, "symlink"):
            admit_artifacts(self.root, _contract(), [Change("create", "src/out.py")],
                            "pytest -q", {})
        (self.root / "src/out.py").unlink(); (self.root / "src/out.py").write_text("x")
        os.link(self.root / "src/out.py", self.root / "src/hard.py")
        with self.assertRaisesRegex(ArtifactViolation, "hardlink"):
            admit_artifacts(self.root, _contract(), [Change("create", "src/out.py")],
                            "pytest -q", {})
        (self.root / "src/hard.py").unlink()
        with self.assertRaisesRegex(ArtifactViolation, "case-fold"):
            admit_artifacts(self.root, _contract(),
                            [Change("create", "src/out.py"), Change("create", "src/OUT.py")],
                            "pytest -q", {})

    def test_frozen_hash_and_interface_verifier(self):
        (self.root / "control.txt").write_text("frozen")
        digest = hashlib.sha256(b"frozen").hexdigest()
        contract = _contract(); contract["interface_assertions"] = [{
            "schema_version": 1, "kind": "api", "interface_id": "api:x",
            "artifact_path": "src/out.py", "verifier_id": "v1",
            "verifier_sha256": "a" * 64}]
        result = admit_artifacts(
            self.root, contract, [Change("create", "src/out.py")], "pytest -q",
            {"control.txt": digest}, {"v1": ("a" * 64, lambda *_: True)})
        self.assertEqual(result["interfaces"], ["api:x"])
        (self.root / "control.txt").write_text("changed")
        with self.assertRaisesRegex(ArtifactViolation, "control-plane"):
            admit_artifacts(self.root, contract, [Change("create", "src/out.py")],
                            "pytest -q", {"control.txt": digest},
                            {"v1": ("a" * 64, lambda *_: True)})


class GitChangeTests(unittest.TestCase):
    def test_git_changes_preserves_rename_source_and_destination(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for cmd in (["git", "init", "-q"], ["git", "config", "user.email", "t@t"],
                        ["git", "config", "user.name", "t"]):
                subprocess.run(cmd, cwd=root, check=True)
            (root / "src").mkdir(); (root / "src/old.py").write_text("x")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "base"], cwd=root, check=True)
            base = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root,
                                           text=True).strip()
            (root / "src/old.py").rename(root / "src/new.py")
            changes = git_changes(root, base)
            self.assertEqual(changes, [Change("rename", "src/new.py", "src/old.py")])


if __name__ == "__main__":
    unittest.main()
