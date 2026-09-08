"""Guard T18 packet preparation. No actor behavior is judged here."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

HERE = Path(__file__).resolve().parent
T9_REPLAN = Path("/Users/aa/orca/workspaces/myskills/meta-intent-t9/docs/grillstorm/meta-intent/replan-2")


def t15_root():
    """The T15 utilities this task reuses, wherever this checkout carries them."""
    for root in (HERE.parent / "T15", T9_REPLAN / "T15"):
        if (root / "prepare_packets.py").is_file():
            return root
    pytest.skip("the shared T15 exporter is not reachable from this checkout")


def module():
    spec = importlib.util.spec_from_file_location("t18_prepare_packets", HERE / "prepare_packets.py")
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def test_candidate_export_is_the_shared_t15_utility_not_a_second_framework():
    t18 = module()
    shared = str(t15_root() / "prepare_packets.py")
    for name in ("candidate", "fingerprint", "put"):
        assert getattr(t18, name).__code__.co_filename == shared, (
            f"T18 {name} must be the shared T15 utility, not a reimplementation")


def test_preparation_requires_an_explicit_candidate(tmp_path):
    done = subprocess.run([sys.executable, str(HERE / "prepare_packets.py"), str(tmp_path / "out")],
                          capture_output=True, text=True)
    assert done.returncode != 0, "the candidate must never be inferred from an installation"
    assert not (tmp_path / "out").exists()


def test_preparation_refuses_a_candidate_that_is_not_a_commit(tmp_path):
    done = subprocess.run([sys.executable, str(HERE / "prepare_packets.py"), str(tmp_path / "out"),
                           "--candidate", "not-a-real-ref"], capture_output=True, text=True)
    assert done.returncode != 0
    assert "--candidate must resolve to a Git commit" in done.stderr
    assert not (tmp_path / "out").exists()


MATRIX = json.loads((HERE.parents[1] / "tasks" / "scenario-matrix.json").read_text())
T18_SCENARIOS = [s for s in MATRIX["scenarios"] if s["task"] == "T18"]
REFERENCE = "5c02e24cf993c36591458f87f1c7dcfb66be3a35"


@pytest.fixture(scope="module")
def prepared(tmp_path_factory):
    out = tmp_path_factory.mktemp("t18") / "packets"
    done = subprocess.run([sys.executable, str(HERE / "prepare_packets.py"), str(out),
                           "--candidate", REFERENCE], capture_output=True, text=True)
    assert done.returncode == 0, done.stdout + done.stderr
    return out


def scenes():
    return [s["id"].split("/", 1)[1] for s in T18_SCENARIOS]


def test_every_matrix_cell_is_materialized_for_both_hosts(prepared):
    assert len(T18_SCENARIOS) == 8, "the matrix must still declare eight T18 scenarios"
    for scenario in T18_SCENARIOS:
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
    for scene in scenes():
        for host in ("claude", "codex"):
            cell = prepared / host / scene
            text = (cell / "actor-input.md").read_text()
            assert str(prepared / "candidate" / entries[host]) in text
            assert str(cell / "project") in text
            assert str(cell / "receipt.json") in text
            other = entries["codex" if host == "claude" else "claude"]
            assert str(prepared / "candidate" / other) not in text, "a cell must not name the other host entry"


def test_source_before_matches_the_delivered_project_tree(prepared):
    loaded = module()
    for scene in scenes():
        for host in ("claude", "codex"):
            cell = prepared / host / scene
            recorded = json.loads((cell / "source-before.json").read_text())
            assert recorded == loaded.fingerprint(cell / "project"), (
                "the pre-run fingerprint must describe the tree actually delivered")
            assert recorded, "a scenario project must not be empty"


def test_a_cell_never_carries_another_scenarios_user_turn(prepared):
    loaded = module()
    for scene in scenes():
        for host in ("claude", "codex"):
            text = (prepared / host / scene / "actor-input.md").read_text()
            assert loaded.SCENES[scene] in text
            for other, request in loaded.SCENES.items():
                if other != scene:
                    assert request not in text, f"{host}/{scene} leaks the {other} user turn"


FORBIDDEN = ["T18/", "oracle", "expected outcome", "pass criteria", "acceptance criteria",
             "验证", "判据", "scenario-matrix", "issues/18", "evaluator-private",
             "fact-update", "product-conflict"] + sorted({r for s in T18_SCENARIOS for r in s["requirements"]})


def test_no_packet_file_leaks_criteria_requirements_or_expectations(prepared):
    for scene in scenes():
        for host in ("claude", "codex"):
            cell = prepared / host / scene
            gates = cell / "project" / ".allforai" / "bootstrap" / "scripts"
            store = cell / "project" / ".allforai" / "bootstrap" / "external-changes.json"
            for path in sorted(cell.rglob("*")):
                if not path.is_file() or path.is_symlink():
                    continue
                if path.is_relative_to(gates) or path == store:
                    continue  # Candidate gate CLIs and their own recorded output are candidate assets.
                try:
                    text = path.read_text()
                except (UnicodeDecodeError, OSError):
                    continue
                for token in FORBIDDEN:
                    assert token and token not in text, f"{path} leaks '{token}' into a tested context"


def test_only_the_unattended_cell_carries_a_fresh_context_second_phase(prepared):
    loaded = module()
    assert set(loaded.PHASE_TWO) == {"unattended-conflict"}
    for scene in scenes():
        for host in ("claude", "codex"):
            phase2 = prepared / host / scene / "actor-input-phase2.md"
            assert phase2.is_file() == (scene in loaded.PHASE_TWO), (
                f"{host}/{scene} second-phase prompt presence must match the resume-shaped scenario")


def run(project, name, request):
    done = subprocess.run([sys.executable, str(project / ".allforai/bootstrap/scripts" / name), str(project)],
                          input=json.dumps(request), text=True, capture_output=True, cwd=project)
    return json.loads(done.stdout)


def external(project):
    return run(project, "evidence_freshness.py", {"operation": "external-changes"})


def check(project, node):
    done = subprocess.run([sys.executable, str(project / ".allforai/bootstrap/scripts/check_artifacts.py"),
                           str(project / ".allforai/bootstrap/workflow.json"), "--node", node, "--json"],
                          capture_output=True, text=True, cwd=project)
    return json.loads(done.stdout)


def readiness(project):
    done = subprocess.run([sys.executable,
                           str(project / ".allforai/bootstrap/scripts/validate_unattended_readiness.py"),
                           str(project)], capture_output=True, text=True, cwd=project)
    return json.loads(done.stdout)


def cells(prepared, scene):
    for host in ("claude", "codex"):
        yield host, prepared / host / scene / "project"


def test_the_implementation_only_cell_keeps_the_confirmed_acceptance_passing(prepared):
    for host, project in cells(prepared, "fact-only-vs-behavior"):
        report = external(project)
        assert report["status"] == "fact_update", (host, report)
        assert [c["classification"] for c in report["changes"]] == ["fact-update"]
        assert report["changes"][0]["verification"]["returncode"] == 0
        # The fact document still states the superseded result, so synchronization is real work.
        stale = subprocess.run([sys.executable, "-m", "doctest", "docs/orders-export.md"],
                               cwd=project, capture_output=True, text=True)
        assert stale.returncode != 0, "the fact document must actually be out of date"
        assert not [b for b in readiness(project)["blockers"] if b["code"] == "unresolved_external_change"], (
            "an implementation-only change must not present itself as a product decision")


@pytest.mark.parametrize("scene", ["accept-full-recovery", "reject-repair-full-recovery", "defer",
                                   "unattended-conflict"])
def test_the_undecided_conflict_cells_carry_a_live_unresolved_conflict(prepared, scene):
    for host, project in cells(prepared, scene):
        report = external(project)
        assert report["status"] == "conflict", (host, scene, report)
        change = next(c for c in report["changes"] if c["node_id"] == "deliver-export")
        assert change["classification"] == "product-conflict"
        assert change["resolution"] is None, "no decision may be seeded into an undecided cell"
        journal = json.loads((project / ".allforai/product-concept/decision-journal.json").read_text())
        assert not [b for b in journal["batches"] if b.get("external_change")], (
            "the changed code must not arrive already written into the product record")
        held = [b for b in readiness(project)["blockers"] if b["code"] == "unresolved_external_change"]
        assert [b["node_id"] for b in held] == ["deliver-export"]
        # The unrelated completed branch is valid and must survive the recovery.
        assert check(project, "warehouse")["all_exist"] is True
        assert check(project, "warehouse")["freshness"]["status"] == "valid"


def test_the_unattended_cell_has_no_seeded_run_policy(prepared):
    for host, project in cells(prepared, "unattended-conflict"):
        assert not (project / ".allforai/bootstrap/run-policy.json").exists(), (
            "the unattended phase must capture its own Run Policy, not inherit one")


def test_the_interrupted_cell_carries_one_settled_decision_and_one_open_question(prepared):
    for host, project in cells(prepared, "interrupted-recovery"):
        report = external(project)
        settled = next(c for c in report["changes"] if c["node_id"] == "deliver-export")
        assert settled["resolution"]["resolution"] == "accept"
        assert settled["resolution"]["reason"], "a recorded decision keeps the user's reason"
        open_change = next(c for c in report["changes"] if c["node_id"] is None)
        assert open_change["resolution"] is None, "the undecided change must stay undecided"
        # The accepted intent is recorded but its recovery never finished.
        recorded = json.loads((project / ".allforai/bootstrap/local-requirements.json").read_text())
        confirmed = [r for r in recorded["requirements"] if r["status"] == "confirmed"]
        superseded = [r for r in recorded["requirements"] if r["status"] == "superseded"]
        assert [r["acceptance"] for r in confirmed] == [module().PARTNER_ACCEPTANCE]
        assert superseded, "the decision this one replaced must stay in the record"
        assert check(project, "deliver-export")["all_exist"] is False, "the recovery must still be open"


def test_the_report_only_cell_ships_a_difference_report_and_nothing_synchronized(prepared):
    for host, project in cells(prepared, "report-only-not-done"):
        assert (project / ".allforai/bootstrap/external-change-report.md").is_file()
        assert external(project)["status"] == "fact_update"
        assert check(project, "deliver-export")["all_exist"] is False, (
            "a written-up difference must not already satisfy the delivery gates")
        assert readiness(project)["status"] == "not_ready"


def test_the_repeat_cell_starts_from_a_closed_recovery(prepared):
    for host, project in cells(prepared, "stable-repeat"):
        assert external(project) == {"status": "clear", "changes": []}
        assert readiness(project)["status"] == "ready"
        for node in ("deliver-export", "warehouse"):
            checked = check(project, node)
            assert checked["all_exist"] is True and checked["freshness"]["status"] == "valid"
        journal = json.loads((project / ".allforai/product-concept/decision-journal.json").read_text())
        assert [b["batch_id"] for b in journal["batches"] if b.get("external_change")] == ["external-2"], (
            "exactly the one recorded recovery decision, so a repeat run adding another is visible")
