import hashlib
import unittest

from build_artifact_contracts import build_contract, freeze_tasks
from artifact_gateway import validate_contract


class ArtifactContractTests(unittest.TestCase):
    def test_freezes_paths_and_acceptance(self):
        task = {
            "id": "T-auth-01",
            "touched_paths": ["src/auth.py", "tests/test_auth.py"],
            "acceptance_cmd": "pytest tests/test_auth.py",
        }
        frozen = freeze_tasks([task])[0]
        contract = frozen["artifact_contract"]
        self.assertEqual(contract["schema_version"], 1)
        self.assertEqual(contract["task_id"], "T-auth-01")
        self.assertEqual(len(validate_contract(contract)), 64)
        self.assertEqual(
            contract["acceptance_cmd_sha256"],
            hashlib.sha256(task["acceptance_cmd"].encode()).hexdigest(),
        )
        self.assertEqual(contract["path_rules"][0]["kind"], "literal")

    def test_glob_path_is_declared_as_glob(self):
        contract = build_contract({
            "id": "T-ui-01",
            "touched_paths": ["src/ui/**"],
            "acceptance_cmd": "npm test",
        })
        self.assertEqual(contract["path_rules"][0]["kind"], "glob")

    def test_rejects_absolute_path(self):
        with self.assertRaisesRegex(ValueError, "invalid touched path"):
            build_contract({
                "id": "T-bad",
                "touched_paths": ["/tmp/out"],
                "acceptance_cmd": "true",
            })

    def test_rejects_parent_traversal(self):
        with self.assertRaisesRegex(ValueError, "invalid touched path"):
            build_contract({
                "id": "T-bad",
                "touched_paths": ["../outside"],
                "acceptance_cmd": "true",
            })

    def test_rejects_stale_existing_contract(self):
        with self.assertRaisesRegex(ValueError, "stale artifact_contract"):
            freeze_tasks([{
                "id": "T-stale",
                "touched_paths": ["src/a.py"],
                "acceptance_cmd": "pytest",
                "artifact_contract": {},
            }])


if __name__ == "__main__":
    unittest.main()
