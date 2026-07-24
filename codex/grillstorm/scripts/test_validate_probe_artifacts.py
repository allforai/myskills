import copy
import unittest

from validate_probe_artifacts import (
    ProbeValidationError,
    validate_gap_manifest,
    validate_plan,
    validate_registry,
    validate_results,
    validate_saturation,
    _hash,
)


class ProbeArtifactTests(unittest.TestCase):
    def setUp(self):
        self.registry = {
            "schema_version": 1,
            "delivery_run_id": "run-1",
            "requirements": [
                {"id": "R1", "source": "spec.md#r1", "states": [
                    {"id": "success", "risk": "high"},
                    {"id": "error", "risk": "medium"},
                ]},
            ],
        }
        self.plan = {
            "schema_version": 1,
            "round": 1,
            "registry_fingerprint": _hash(self.registry),
            "probes": [
                {"id": "P1", "axis": "logic-alignment",
                 "targets": [{"requirement": "R1", "state": "error"}],
                 "observation_channel": "code", "action": "inspect owner",
                 "expected_evidence": "one owner", "falsifier": "duplicated policy"},
                {"id": "P2", "axis": "feature-state-completeness",
                 "targets": [{"requirement": "R1", "state": "success"}],
                 "observation_channel": "api", "action": "start app and request",
                 "expected_evidence": "response and write", "falsifier": "no write"},
            ],
            "unsampled": [],
        }
        sha = "a" * 64
        self.results = [
            {"schema_version": 1, "probe_id": "P1", "status": "pass",
             "evidence": [{"kind": "code", "path": "src/a.py", "sha256": sha}]},
            {"schema_version": 1, "probe_id": "P2", "status": "gap",
             "runtime_attempted": True, "runtime_started": True,
             "exit_code": 1, "gap_ids": ["G1"],
             "evidence": [{"kind": "network", "path": "evidence/api.log",
                           "sha256": sha}]},
        ]

    def test_valid_round(self):
        probes = validate_plan(self.registry, self.plan)
        results = validate_results(probes, self.results)
        validate_gap_manifest(results, {
            "schema_version": 1, "audit_cycle_id": "A1",
            "gaps": [{"id": "G1", "family_fingerprint": "f1",
                      "probe_ids": ["P2"], "affected_requirements": ["R1"],
                      "affected_states": ["success"],
                      "recommended_scope": "repair runtime behavior",
                      "acceptance_probes": ["P2"],
                      "child_delivery_run_id": None, "child_state_path": None}],
        })

    def test_registry_rejects_duplicate_cell(self):
        broken = copy.deepcopy(self.registry)
        broken["requirements"][0]["states"].append(
            {"id": "success", "risk": "low"}
        )
        with self.assertRaisesRegex(ProbeValidationError, "duplicate"):
            validate_registry(broken)

    def test_plan_rejects_static_feature_probe(self):
        broken = copy.deepcopy(self.plan)
        broken["probes"][1]["observation_channel"] = "code"
        with self.assertRaisesRegex(ProbeValidationError, "runtime channel"):
            validate_plan(self.registry, broken)

    def test_plan_rejects_unsampled_high_risk_cell(self):
        broken = copy.deepcopy(self.plan)
        broken["probes"] = broken["probes"][:1]
        broken["unsampled"] = [
            {"requirement": "R1", "state": "success", "reason": "later"}
        ]
        with self.assertRaisesRegex(ProbeValidationError, "high-risk"):
            validate_plan(self.registry, broken)

    def test_feature_result_requires_runtime(self):
        probes = validate_plan(self.registry, self.plan)
        broken = copy.deepcopy(self.results)
        broken[1].pop("runtime_attempted")
        with self.assertRaisesRegex(ProbeValidationError, "runtime attempt"):
            validate_results(probes, broken)

    def test_runtime_start_failure_is_a_gap_not_a_gate(self):
        probes = validate_plan(self.registry, self.plan)
        broken = copy.deepcopy(self.results)
        broken[1].update({
            "runtime_started": False,
            "failure_kind": "runtime_start_failure",
            "exit_code": 127,
        })
        validate_results(probes, broken)
        broken[1]["status"] = "reality_gated"
        with self.assertRaisesRegex(ProbeValidationError, "invalid result status"):
            validate_results(probes, broken)

    def test_feature_result_requires_runtime_evidence(self):
        probes = validate_plan(self.registry, self.plan)
        broken = copy.deepcopy(self.results)
        broken[1]["evidence"][0]["kind"] = "code"
        with self.assertRaisesRegex(ProbeValidationError, "runtime evidence"):
            validate_results(probes, broken)

    def test_evidence_hash_is_verified(self):
        import hashlib
        import pathlib
        import tempfile
        probes = validate_plan(self.registry, self.plan)
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            (root / "src").mkdir()
            (root / "evidence").mkdir()
            (root / "src/a.py").write_text("logic")
            (root / "evidence/api.log").write_text("runtime")
            results = copy.deepcopy(self.results)
            results[0]["evidence"][0]["sha256"] = hashlib.sha256(b"logic").hexdigest()
            results[1]["evidence"][0]["sha256"] = hashlib.sha256(b"runtime").hexdigest()
            validate_results(probes, results, root)
            results[1]["evidence"][0]["sha256"] = "0" * 64
            with self.assertRaisesRegex(ProbeValidationError, "hash mismatch"):
                validate_results(probes, results, root)

    def test_gap_manifest_must_match_results(self):
        probes = validate_plan(self.registry, self.plan)
        results = validate_results(probes, self.results)
        with self.assertRaisesRegex(ProbeValidationError, "does not match"):
            validate_gap_manifest(results, {
                "schema_version": 1, "audit_cycle_id": "A1", "gaps": [],
            })

    def test_gap_manifest_requires_remediation_link_at_launch(self):
        probes = validate_plan(self.registry, self.plan)
        results = validate_results(probes, self.results)
        manifest = {
            "schema_version": 1, "audit_cycle_id": "A1",
            "gaps": [{"id": "G1", "family_fingerprint": "f1",
                      "probe_ids": ["P2"], "affected_requirements": ["R1"],
                      "affected_states": ["success"],
                      "recommended_scope": "repair runtime behavior",
                      "acceptance_probes": ["P2"],
                      "child_delivery_run_id": None, "child_state_path": None}],
        }
        with self.assertRaisesRegex(ProbeValidationError, "child link"):
            validate_gap_manifest(results, manifest, require_child_links=True)
        manifest["gaps"][0]["child_delivery_run_id"] = "run-2"
        manifest["gaps"][0]["child_state_path"] = "docs/grillstorm/run-2/state.json"
        validate_gap_manifest(results, manifest, require_child_links=True)

    def test_saturation_requires_two_clean_rounds(self):
        validate_saturation({
            "schema_version": 1, "status": "saturated",
            "rounds": [
                {"new_gap_families": 0, "new_blocking_members": 0,
                 "unexplored_cells": 0},
                {"new_gap_families": 0, "new_blocking_members": 0,
                 "unexplored_cells": 0},
            ],
        })
        with self.assertRaisesRegex(ProbeValidationError, "last two"):
            validate_saturation({
                "schema_version": 1, "status": "saturated",
                "rounds": [
                    {"new_gap_families": 1, "new_blocking_members": 0,
                     "unexplored_cells": 0},
                    {"new_gap_families": 0, "new_blocking_members": 0,
                     "unexplored_cells": 0},
                ],
            })


if __name__ == "__main__":
    unittest.main()
