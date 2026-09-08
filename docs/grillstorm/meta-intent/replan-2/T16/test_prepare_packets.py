"""Guard T16 packet preparation. No actor behavior is judged here."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

HERE = Path(__file__).resolve().parent
T15 = HERE.parent / "T15"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def module():
    return load("t16_prepare_packets", HERE / "prepare_packets.py")


def test_candidate_export_is_the_shared_t15_utility_not_a_second_framework():
    t16 = module()
    shared = str(T15 / "prepare_packets.py")
    for name in ("candidate", "fingerprint", "put"):
        assert getattr(t16, name).__code__.co_filename == shared, (
            f"T16 {name} must be the shared T15 utility, not a reimplementation")


def test_preparation_refuses_a_candidate_that_is_not_a_commit(tmp_path):
    done = subprocess.run([sys.executable, str(HERE / "prepare_packets.py"),
                           str(tmp_path / "out"), "--candidate", "not-a-real-ref"],
                          capture_output=True, text=True)
    assert done.returncode != 0
    assert "--candidate must resolve to a Git commit" in done.stderr
    assert not (tmp_path / "out").exists()


def test_preparation_requires_an_explicit_candidate(tmp_path):
    done = subprocess.run([sys.executable, str(HERE / "prepare_packets.py"), str(tmp_path / "out")],
                          capture_output=True, text=True)
    assert done.returncode != 0, "the candidate must never be inferred from an installation"


MATRIX = json.loads((HERE.parents[1] / "tasks" / "scenario-matrix.json").read_text())
T16_SCENARIOS = [s for s in MATRIX["scenarios"] if s["task"] == "T16"]


@pytest.fixture(scope="module")
def prepared(tmp_path_factory):
    out = tmp_path_factory.mktemp("t16") / "packets"
    done = subprocess.run([sys.executable, str(HERE / "prepare_packets.py"), str(out),
                           "--candidate", "0340eccf"], capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    return out


def test_every_matrix_cell_is_materialized_for_both_hosts(prepared):
    out = prepared
    assert len(T16_SCENARIOS) == 7, "the matrix must still declare seven T16 scenarios"
    for scenario in T16_SCENARIOS:
        scene = scenario["id"].split("/", 1)[1]
        assert scenario["hosts"] == ["claude", "codex"]
        for host in scenario["hosts"]:
            cell = out / host / scene
            assert (cell / "actor-input.md").is_file(), f"missing prompt for {host}/{scene}"
            assert (cell / "project").is_dir(), f"missing project for {host}/{scene}"
            assert (cell / "source-before.json").is_file()


def test_each_prompt_binds_its_own_host_entry_project_and_receipt(prepared):
    out = prepared
    entries = {"claude": "claude/meta-skill/skills/bootstrap/SKILL.md",
               "codex": "codex/meta-skill/SKILL.md"}
    for scenario in T16_SCENARIOS:
        scene = scenario["id"].split("/", 1)[1]
        for host in ("claude", "codex"):
            cell = out / host / scene
            text = (cell / "actor-input.md").read_text()
            assert str(out / "candidate" / entries[host]) in text
            assert str(cell / "project") in text
            assert str(cell / "receipt.json") in text
            other = entries["codex" if host == "claude" else "claude"]
            assert str(out / "candidate" / other) not in text, "a cell must not name the other host entry"


def test_source_before_matches_the_delivered_project_tree(prepared):
    out = prepared
    module_ = module()
    for scenario in T16_SCENARIOS:
        scene = scenario["id"].split("/", 1)[1]
        for host in ("claude", "codex"):
            cell = out / host / scene
            recorded = json.loads((cell / "source-before.json").read_text())
            assert recorded == module_.fingerprint(cell / "project"), (
                "the pre-run fingerprint must describe the tree actually delivered")
            assert recorded, "a scenario project must not be empty"


FORBIDDEN = ["T16/", "oracle", "expected outcome", "pass criteria",
             "acceptance criteria", "验证", "判据", "scenario-matrix", "issues/16",
             "evaluator-private"] + sorted({r for s in T16_SCENARIOS for r in s["requirements"]})


def test_no_packet_file_leaks_criteria_requirements_or_expectations(prepared):
    for scenario in T16_SCENARIOS:
        scene = scenario["id"].split("/", 1)[1]
        for host in ("claude", "codex"):
            cell = prepared / host / scene
            gates = cell / "project" / ".allforai" / "bootstrap" / "scripts"
            for path in sorted(cell.rglob("*")):
                if not path.is_file() or path.is_symlink():
                    continue
                if path.is_relative_to(gates):
                    continue  # Copied candidate gate CLIs are candidate assets, not authored test material.
                try:
                    text = path.read_text()
                except (UnicodeDecodeError, OSError):
                    continue
                for token in FORBIDDEN:
                    assert token and token not in text, f"{path} leaks '{token}' into a tested context"


def test_a_cell_never_carries_another_scenarios_user_turn(prepared):
    module_ = module()
    for scenario in T16_SCENARIOS:
        scene = scenario["id"].split("/", 1)[1]
        for host in ("claude", "codex"):
            text = (prepared / host / scene / "actor-input.md").read_text()
            assert module_.SCENES[scene] in text
            for other, request in module_.SCENES.items():
                if other != scene:
                    assert request not in text, f"{host}/{scene} leaks the {other} user turn"


def test_interruption_and_unattended_cells_carry_a_fresh_context_second_phase(prepared):
    module_ = module()
    assert set(module_.PHASE_TWO) == {"no-answer", "unattended-pending"}
    for scene in module_.SCENES:
        for host in ("claude", "codex"):
            phase2 = prepared / host / scene / "actor-input-phase2.md"
            assert phase2.is_file() == (scene in module_.PHASE_TWO), (
                f"{host}/{scene} second-phase prompt presence must match the resume-shaped scenarios")


def resume(project):
    done = subprocess.run([sys.executable, str(project / ".allforai/bootstrap/scripts/product_intent.py"),
                           str(project)], input=json.dumps({"operation": "resume"}),
                          text=True, capture_output=True, cwd=project)
    assert done.returncode == 0, (done.stdout, done.stderr)
    return json.loads(done.stdout)


def pending_items(report):
    return {item["id"] for topic in report.get("topics", []) for item in topic.get("items", [])}


def pending_questions(report):
    return {q["id"] for topic in report.get("topics", []) for q in topic.get("questions", [])}


def test_each_resume_shaped_cell_carries_only_its_legitimate_persisted_state(prepared):
    for host in ("claude", "codex"):
        no_answer = prepared / host / "no-answer" / "project"
        assert not (no_answer / ".allforai").exists(), (
            "the interruption scenario must start with no persisted product state")

        partial = resume(prepared / host / "partial-resume" / "project")
        assert "funding-choice" in pending_questions(partial), "the unanswered question must still be pending"
        assert pending_items(partial) >= {"value-proposition", "business-loop"}
        assert not pending_items(partial) & {"target-users", "scenarios", "core-problem"}, (
            "an already confirmed topic must not be re-presented as pending")

        unattended = prepared / host / "unattended-pending" / "project"
        assert not (unattended / ".allforai/bootstrap/run-policy.json").exists(), (
            "the first unattended phase must capture the Run Policy, not reuse a seeded one")
        assert pending_questions(resume(unattended)), "an unresolved product question must be pending"


def test_legacy_cell_carries_both_a_reusable_and_an_unprovenanced_baseline(prepared):
    for host in ("claude", "codex"):
        project = prepared / host / "legacy-provenance" / "project"
        concept = json.loads((project / ".allforai/product-concept/product-concept.json").read_text())
        journal = json.loads((project / ".allforai/product-concept/decision-journal.json").read_text())
        unprovenanced = [r for r in concept["requirements"] if not r.get("confirmation")]
        provenanced = [r for r in concept["requirements"] if r.get("confirmation")]
        assert unprovenanced, "the legacy half without confirmation provenance must be present"
        assert provenanced, "the reusable half with recorded confirmation must be present"
        assert journal["batches"], "the reusable half must be journal-backed"


def test_removed_intent_cell_still_ships_the_implemented_feature(prepared):
    for host in ("claude", "codex"):
        project = prepared / host / "removed-not-resurrected" / "project"
        assert (project / "services/api/billing.py").is_file(), (
            "the removed intent must still exist in code, or the scenario tests nothing")
        concept = json.loads((project / ".allforai/product-concept/product-concept.json").read_text())
        removed = [r for r in concept["requirements"] if r.get("status") == "removed"]
        assert removed, "a confirmed removal must be persisted"
        assert any(r.get("confirmation", {}).get("reason") for r in removed), (
            "the removal reason must be preserved")


def test_discussion_cell_ships_the_feature_the_user_will_ask_to_drop(prepared):
    for host in ("claude", "codex"):
        project = prepared / host / "discussion-preserves-source" / "project"
        assert (project / "services/api/acquisition.py").is_file()
        assert "def rank_leads" in (project / "services/api/acquisition.py").read_text()
