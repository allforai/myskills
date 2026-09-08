"""Fake Orca process boundary for recorder tests; no real actors execute here."""
import json
from pathlib import Path
import subprocess
import sys

CLI = Path(__file__).with_name("capture_worker.py")


def fake_orca(tmp_path, pages):
    source = tmp_path / "fake_orca.py"
    source.write_text("#!" + sys.executable + "\n" + '''import json,sys
from pathlib import Path
root=Path(__file__).parent
calls=root/'calls.json'
history=json.loads(calls.read_text()) if calls.exists() else []
history.append(sys.argv[1:])
calls.write_text(json.dumps(history))
pages=json.loads((root/'pages.json').read_text())
print(json.dumps(pages[min(len(history)-1,len(pages)-1)]))
''')
    source.chmod(0o755)
    (tmp_path / "pages.json").write_text(json.dumps(pages))
    return source


def page(cursor, messages, **extra):
    return {"ok": True, "result": {"dispatchId": "ctx_synthetic", "source": "transcript",
        "sourceIdentity": "synthetic-source", "provider": "codex", "cursor": cursor,
        "warnings": [], "transcript": {"messages": messages, "limited": False}, **extra}}


def test_records_exact_dispatch_and_only_returned_cursor(tmp_path):
    pages = [page("opaque-returned-1", [{"role": "user", "text": "Synthetic test input"}]),
             page("opaque-returned-1", [])]
    fake = fake_orca(tmp_path, pages)
    output = tmp_path / "capture"
    result = subprocess.run([sys.executable, str(CLI), "ctx_synthetic", str(output),
        "--orca", str(fake)], capture_output=True, text=True)
    assert result.returncode == 0, (result.stdout, result.stderr)
    calls = json.loads((tmp_path / "calls.json").read_text())
    assert calls[0] == ["orchestration", "worker-read", "--dispatch", "ctx_synthetic",
                        "--source", "auto", "--limit", "100", "--json"]
    assert calls[1] == calls[0] + ["--cursor", "opaque-returned-1"]
    assert json.loads((output / "page-0001.stdout.json").read_text()) == pages[0]
    assert (output / "page-0001.stderr.txt").read_text() == ""
    report = json.loads((output / "capture.json").read_text())
    assert report["sourceIdentity"] == "synthetic-source"
    assert report["cursor"] == "opaque-returned-1"
    assert report["semantic_verdict"] == "not-evaluated"
    assert report["full_dialogue_proven"] is False


def test_flags_clipped_window_and_stops_on_source_identity_change(tmp_path):
    pages = [page("cursor-1", [], warnings=["oversized block clipped"]),
             page("cursor-2", [], sourceIdentity="different-session")]
    fake = fake_orca(tmp_path, pages)
    output = tmp_path / "capture"
    result = subprocess.run([sys.executable, str(CLI), "ctx_synthetic", str(output),
        "--orca", str(fake)], capture_output=True, text=True)
    assert result.returncode == 1, result.stdout
    report = json.loads((output / "capture.json").read_text())
    assert "runtime-warnings" in report["limitations"]
    assert "source-changed" in report["limitations"]
    assert report["sourceIdentity"] == "synthetic-source"
    assert report["cursor"] == "cursor-1"
    assert len(report["pages"]) == 2
    assert report["pages"][0]["warnings"] == ["oversized block clipped"]


def test_preserves_runtime_source_changed_error_without_guessing_cursor(tmp_path):
    pages = [page("returned-cursor", []),
             {"ok": False, "error": {"code": "source_changed", "message": "Start a fresh read"}}]
    fake = fake_orca(tmp_path, pages)
    output = tmp_path / "capture"
    result = subprocess.run([sys.executable, str(CLI), "ctx_synthetic", str(output),
        "--orca", str(fake)], capture_output=True, text=True)
    assert result.returncode == 1
    assert not result.stderr
    report = json.loads((output / "capture.json").read_text())
    assert report["limitations"] == ["runtime-error", "source-changed"]
    assert report["cursor"] == "returned-cursor"
    assert json.loads((output / "page-0002.stdout.json").read_text()) == pages[1]


def test_continuation_uses_prior_capture_cursor_and_source_identity(tmp_path):
    fake = fake_orca(tmp_path, [page("first", []), page("first", []),
                                page("second", []), page("second", [])])
    first = tmp_path / "first-capture"
    second = tmp_path / "second-capture"
    initial = subprocess.run([sys.executable, str(CLI), "ctx_synthetic", str(first),
        "--orca", str(fake)], capture_output=True, text=True)
    assert initial.returncode == 0, initial.stdout
    resumed = subprocess.run([sys.executable, str(CLI), "ctx_synthetic", str(second),
        "--orca", str(fake), "--after", str(first / "capture.json")], capture_output=True, text=True)
    assert resumed.returncode == 0, (resumed.stdout, resumed.stderr)
    calls = json.loads((tmp_path / "calls.json").read_text())
    assert calls[2][-2:] == ["--cursor", "first"]
    report = json.loads((second / "capture.json").read_text())
    assert report["previous_capture"] == str(first / "capture.json")
    assert report["cursor"] == "second"


def test_missing_cli_preserves_failure_record_without_fallback(tmp_path):
    output = tmp_path / "capture"
    missing = tmp_path / "unavailable-orca"
    result = subprocess.run([sys.executable, str(CLI), "ctx_synthetic", str(output),
        "--orca", str(missing)], capture_output=True, text=True)
    assert result.returncode == 1
    assert not result.stderr
    report = json.loads((output / "capture.json").read_text())
    assert "command-failed" in report["limitations"]
    assert report["pages"][0]["command"][0] == str(missing)
    assert report["pages"][0]["exit_code"] != 0
    assert (output / "page-0001.stderr.txt").read_text()


def test_terminal_fallback_is_preserved_and_explicitly_incomplete(tmp_path):
    returned = page("terminal-cursor", [], source="terminal", transcript=None,
                    provider=None, sourceIdentity="terminal-source", fallbackReason="no_attested_transcript")
    fake = fake_orca(tmp_path, [returned, returned])
    output = tmp_path / "capture"
    result = subprocess.run([sys.executable, str(CLI), "ctx_synthetic", str(output),
        "--orca", str(fake)], capture_output=True, text=True)
    assert result.returncode == 1
    assert not result.stderr
    report = json.loads((output / "capture.json").read_text())
    assert "terminal-fallback" in report["limitations"]
    assert report["pages"][0]["fallbackReason"] == "no_attested_transcript"
