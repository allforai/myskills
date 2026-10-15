import json
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


@pytest.fixture(autouse=True)
def cfg_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "claude"))
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("JEV_BASE_URL", raising=False)
    return tmp_path / "xdg" / "jev"


def default_answers(body):
    answers = {}
    for qid, q in body["questions"].items():
        if q["type"] == "choice":
            opts = list(q["criteria"])
            answers[qid] = {"type": "choice", "choice": opts[0], "confidence": 1.0,
                            "probabilities": {o: (1.0 if i == 0 else 0.0) for i, o in enumerate(opts)}}
        elif q["type"] == "score":
            answers[qid] = {"type": "score", "score": 0.0, "confidence": 1.0, "probabilities": {"0": 1.0}}
        else:
            answers[qid] = {"type": "noul", "noul": 0.0}
    return {"model": "jev-test", "answers": answers,
            "usage": {"input_tokens": 10, "output_tokens": 1, "cost": 0.0001}}


class FakeJev:
    def __init__(self):
        self.url = ""
        self.requests = []
        self.lock = threading.Lock()
        self.responder = lambda body: (200, default_answers(body))


def _handler(fake):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            with fake.lock:
                fake.requests.append({"path": self.path, "headers": dict(self.headers), "body": body})
            status, payload = fake.responder(body)
            raw = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def log_message(self, *args):
            pass
    return Handler


@pytest.fixture
def fake_jev(monkeypatch):
    fake = FakeJev()
    server = ThreadingHTTPServer(("127.0.0.1", 0), _handler(fake))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    fake.url = f"http://127.0.0.1:{server.server_port}"
    monkeypatch.setenv("JEV_BASE_URL", fake.url)
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test-secret")
    yield fake
    server.shutdown()
    server.server_close()


@pytest.fixture
def git_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "t"], check=True)
    return repo
