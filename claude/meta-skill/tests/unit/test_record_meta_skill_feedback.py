import os
import sys

from ..module_isolation import load

_feedback = load("record_meta_skill_feedback")
record_feedback = _feedback.record_feedback


def _write(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def test_record_feedback_prefers_local_myskills_repo(tmp_path, monkeypatch):
    project = tmp_path / "project"
    repo = tmp_path / "myskills"
    project.mkdir()
    repo.mkdir()
    (repo / ".git").mkdir()
    monkeypatch.setenv("META_SKILL_LOCAL_REPO", str(repo))

    def fake_run(args, cwd=None):
        class Result:
            returncode = 0
            stdout = "origin git@github.com:allforai/myskills.git"
            stderr = ""
        return Result()

    monkeypatch.setattr(_feedback, "_run", fake_run)
    result = record_feedback(project, message="workflow expansion gap", category="workflow-gap", mode="draft")

    assert result["status"] == "recorded_local_myskills"
    assert "pending" not in result
    assert (repo / "docs/feedback/inbox").exists()


def test_record_feedback_falls_back_to_pending_issue_when_no_local_repo(tmp_path, monkeypatch):
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.setattr(_feedback, "_candidate_repos", lambda project_root: [])

    result = record_feedback(project, message="workflow expansion gap", category="workflow-gap", mode="draft")

    assert result["status"] == "pending_github_issue"
    assert (project / ".allforai/bootstrap/pending-feedback.md").exists()
    assert (project / ".allforai/bootstrap/pending-feedback.json").exists()


def test_record_feedback_redacts_project_name_and_paths(tmp_path, monkeypatch):
    project = tmp_path / "secret-project"
    project.mkdir()
    monkeypatch.setattr(_feedback, "_candidate_repos", lambda project_root: [])
    message = f"Failure in {project}/src/app.ts for secret-project with api_key=abc"

    result = record_feedback(project, message=message, category="privacy", mode="draft")

    body = (project / ".allforai/bootstrap/pending-feedback.md").read_text()
    assert "secret-project" not in body
    assert str(project) not in body
    assert "api_key=abc" not in body
    assert result["status"] == "pending_github_issue"
