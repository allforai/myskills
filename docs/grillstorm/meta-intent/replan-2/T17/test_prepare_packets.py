"""Guard T17 packet preparation. No actor behavior is judged here."""
import hashlib
import importlib.util
import json
import shutil
from pathlib import Path
import subprocess
import sys

import pytest

HERE = Path(__file__).resolve().parent


def module():
    spec = importlib.util.spec_from_file_location("t17_prepare_packets", HERE / "prepare_packets.py")
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def test_candidate_export_is_the_shared_t15_utility_not_a_second_framework():
    t17 = module()
    shared = str(t17.shared_path())
    for name in ("candidate", "fingerprint", "put"):
        assert getattr(t17, name).__code__.co_filename == shared, (
            f"T17 {name} must be the shared T15 utility, not a reimplementation")


def test_the_shared_utility_resolves_this_repository_not_its_own_cache_location():
    t17 = module()
    assert t17.SHARED.SOURCE == t17.SOURCE, (
        "the shared exporter must read this checkout's Git objects wherever it was loaded from")
    assert (t17.SOURCE / "claude/meta-skill").is_dir()


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
    assert done.returncode != 0, "the candidate must never be inferred from the current worktree"


MATRIX = json.loads((HERE.parents[1] / "tasks" / "scenario-matrix.json").read_text())
T17_SCENARIOS = [s for s in MATRIX["scenarios"] if s["task"] == "T17"]
CANDIDATE = "1ed30ee5819adf95cf4f2b64c08956ec4c751b1d"


@pytest.fixture(scope="module")
def prepared(tmp_path_factory):
    out = tmp_path_factory.mktemp("t17") / "packets"
    done = subprocess.run([sys.executable, str(HERE / "prepare_packets.py"), str(out),
                           "--candidate", CANDIDATE], capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    return out


def test_every_matrix_cell_is_materialized_for_both_hosts(prepared):
    assert len(T17_SCENARIOS) == 8, "the matrix must still declare eight T17 scenarios"
    for scenario in T17_SCENARIOS:
        scene = scenario["id"].split("/", 1)[1]
        assert scenario["hosts"] == ["claude", "codex"]
        for host in scenario["hosts"]:
            cell = prepared / host / scene
            assert (cell / "actor-input.md").is_file(), f"missing prompt for {host}/{scene}"
            assert (cell / "project").is_dir(), f"missing project for {host}/{scene}"
            assert (cell / "source-before.json").is_file()


def test_each_prompt_binds_its_own_host_entry_project_and_receipt(prepared):
    entries = {"claude": "claude/meta-skill/skills/bootstrap/SKILL.md",
               "codex": "codex/meta-skill/SKILL.md"}
    for scenario in T17_SCENARIOS:
        scene = scenario["id"].split("/", 1)[1]
        for host in ("claude", "codex"):
            cell = prepared / host / scene
            text = (cell / "actor-input.md").read_text()
            assert str(prepared / "candidate" / entries[host]) in text
            assert str(cell / "project") in text
            assert str(cell / "receipt.json") in text
            other = entries["codex" if host == "claude" else "claude"]
            assert str(prepared / "candidate" / other) not in text, "a cell must not name the other host entry"


def test_source_before_matches_the_delivered_project_tree(prepared):
    recorded_module = module()
    for scenario in T17_SCENARIOS:
        scene = scenario["id"].split("/", 1)[1]
        for host in ("claude", "codex"):
            cell = prepared / host / scene
            recorded = json.loads((cell / "source-before.json").read_text())
            assert recorded == recorded_module.fingerprint(cell / "project"), (
                "the pre-run fingerprint must describe the tree actually delivered")
            assert recorded, "a scenario project must not be empty"


def test_a_cell_never_carries_another_scenarios_user_turn(prepared):
    scenes = module().SCENES
    for scene, request in scenes.items():
        for host in ("claude", "codex"):
            text = (prepared / host / scene / "actor-input.md").read_text()
            assert request in text
            for other, other_request in scenes.items():
                if other != scene:
                    assert other_request not in text, f"{host}/{scene} leaks the {other} user turn"


FORBIDDEN = ["T17/", "oracle", "expected outcome", "pass criteria", "acceptance criteria",
             "验证", "判据", "scenario-matrix", "issues/17", "evaluator-private", "SG01", "SG02",
             ] + sorted({r for s in T17_SCENARIOS for r in s["requirements"]})


def test_no_packet_file_leaks_criteria_requirements_or_expectations(prepared):
    for scenario in T17_SCENARIOS:
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


def test_repeat_shaped_cells_carry_a_fresh_context_second_phase(prepared):
    phase_two = module().PHASE_TWO
    assert set(phase_two) == {"generated-sync-no-loop", "unchanged-idempotency"}
    for scene in module().SCENES:
        for host in ("claude", "codex"):
            phase2 = prepared / host / scene / "actor-input-phase2.md"
            assert phase2.is_file() == (scene in phase_two), (
                f"{host}/{scene} second-phase prompt presence must match the repeat-shaped scenarios")


def check(project):
    done = subprocess.run([sys.executable, str(project / ".allforai/bootstrap/scripts/evidence_freshness.py"),
                           str(project)], input=json.dumps({"operation": "check"}),
                          text=True, capture_output=True, cwd=project)
    return json.loads(done.stdout)


def statuses(project):
    return {node: entry["status"] for node, entry in check(project)["nodes"].items()}


def test_the_blindness_scan_actually_reads_the_delivered_project_files(prepared):
    text = (prepared / "claude" / "unchanged-idempotency" / "project" / "services/api/requests.py").read_text()
    assert "def visible_requests" in text, "the scanned tree must contain the synthetic product source"


def test_two_dirty_states_cell_holds_one_commit_and_a_second_uncommitted_state(prepared, tmp_path):
    for host in ("claude", "codex"):
        project = prepared / host / "two-dirty-states" / "project"
        log = subprocess.run(["git", "log", "--oneline"], cwd=project, text=True, capture_output=True)
        assert len(log.stdout.split("\n")) == 2, "the scenario needs exactly one commit"
        dirty = subprocess.run(["git", "status", "--porcelain", "services/api/requests.py"],
                               cwd=project, text=True, capture_output=True)
        assert dirty.stdout.startswith(" M "), "the current state must be uncommitted"
        assert statuses(project)["deliver-visibility"] == "stale", (
            "evidence published against the earlier uncommitted state cannot prove the current one")

    seeded = json.loads((prepared / "seeded-state.json").read_text())
    token = seeded["claude/two-dirty-states"]["pending_observation"]
    working = tmp_path / "sg01"
    shutil.copytree(prepared / "claude" / "two-dirty-states" / "project", working, symlinks=True)
    command = ["python3", ".allforai/bootstrap/scripts/validate_bootstrap.py", ".allforai/bootstrap"]

    def freshness(request):
        done = subprocess.run([sys.executable, str(working / ".allforai/bootstrap/scripts/evidence_freshness.py"),
                               str(working)], input=json.dumps(request), text=True, capture_output=True, cwd=working)
        return json.loads(done.stdout)

    rejected = freshness({"operation": "publish", "observation": token, "verification_command": command})
    assert rejected["status"] == "stale", "the observation of the earlier state must not publish"
    fresh = freshness({"operation": "observe", "node_id": "deliver-visibility"})["observation"]
    assert fresh != token
    recovered = freshness({"operation": "publish", "observation": fresh, "verification_command": command})
    assert recovered["status"] == "valid", "a real re-observation of the current state must recover acceptance"


def test_baseline_only_change_cell_changes_the_decision_and_no_source(prepared):
    for host in ("claude", "codex"):
        project = prepared / host / "baseline-only-change" / "project"
        diff = check(project)["nodes"]["deliver-visibility"]["diff"]
        assert "files" not in diff, "no source file may have changed in this scenario"
        assert diff["requirements"], "the revised confirmed decision must be what invalidates the evidence"
        journal = json.loads((project / ".allforai/product-concept/decision-journal.json").read_text())
        assert journal["batches"], "the user's revision must be recorded as a decision"


def test_generated_sync_cell_declares_generated_outputs_and_one_implementation_change(prepared):
    for host in ("claude", "codex"):
        project = prepared / host / "generated-sync-no-loop" / "project"
        workflow = json.loads((project / ".allforai/bootstrap/workflow.json").read_text())
        assert "docs/synchronization-report.md" in workflow["generated_outputs"]
        assert (project / "docs/synchronization-report.md").is_file()
        assert statuses(project) == {"deliver-visibility": "valid", "verify-visibility": "valid",
                                     "publish-digest": "valid", "deliver-directory": "stale"}


def test_tests_pass_docs_stale_cell_pairs_a_passing_build_with_an_unsynchronized_document(prepared):
    for host in ("claude", "codex"):
        project = prepared / host / "tests-pass-docs-stale" / "project"
        report = json.loads((project / ".allforai/bootstrap/visibility-report.json").read_text())
        assert report["status"] == "passed" and report["tests"] == "12 passed"
        verify = json.loads((project / ".allforai/bootstrap/visibility-verify.json").read_text())
        assert verify["status"] == "accepted_with_gaps" and verify["known_gaps"]
        checked = subprocess.run(["python3", "tools/check_requests_doc.py"], cwd=project,
                                 text=True, capture_output=True)
        assert checked.returncode == 1, "the required document must not verify against the current source"


def test_transitive_cell_invalidates_the_chain_and_preserves_the_unrelated_branch(prepared):
    for host in ("claude", "codex"):
        project = prepared / host / "transitive-unrelated-impact" / "project"
        assert statuses(project) == {"deliver-visibility": "stale", "verify-visibility": "stale",
                                     "publish-digest": "stale", "deliver-directory": "valid"}


def test_copied_old_evidence_cell_restores_the_published_report_and_refreshes_its_time(prepared):
    for host in ("claude", "codex"):
        project = prepared / host / "copied-old-evidence" / "project"
        state = json.loads((project / ".allforai/bootstrap/evidence-freshness.json").read_text())
        report = project / ".allforai/bootstrap/visibility-report.json"
        recorded = state["nodes"]["deliver-visibility"]["outputs"][".allforai/bootstrap/visibility-report.json"]
        assert hashlib.sha256(report.read_bytes()).hexdigest() == recorded, (
            "the forged report must be byte-identical to the one that was published")
        assert report.stat().st_mtime > (project / "services/api/requests.py").stat().st_mtime, (
            "the forged report must look newer than the source it claims to cover")
        assert statuses(project)["deliver-visibility"] == "stale"


def test_unchanged_cell_starts_from_a_fully_valid_state(prepared):
    for host in ("claude", "codex"):
        project = prepared / host / "unchanged-idempotency" / "project"
        assert set(statuses(project).values()) == {"valid"}


def test_uncertain_cell_adds_a_module_no_node_declares(prepared):
    for host in ("claude", "codex"):
        project = prepared / host / "uncertain-impact" / "project"
        report = check(project)
        assert report["uncertain_inputs"] == ["services/api/reminders.py"]
        assert report["nodes"]["deliver-visibility"]["status"] == "uncertain"
