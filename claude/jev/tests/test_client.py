import time

import pytest

import jev_config as C
from jev_client import JevError, make_caller

Q = {"is_spam": {"type": "noul", "instructions": "Is this spam?"}}


def caller(**kw):
    return make_caller(C.load_config(), timeout=kw.pop("timeout", 2.0), sleep=lambda s: None, **kw)


def test_sends_bearer_model_state_questions(fake_jev):
    out = caller()("hello", Q)
    req = fake_jev.requests[0]
    assert req["path"] == "/v1/systemone"
    assert req["headers"]["Authorization"] == "Bearer sk-test-secret"
    assert req["body"] == {"state": "hello", "model": "~typesafe/jev-latest", "questions": Q}
    assert out["answers"]["is_spam"]["noul"] == 0.0
    assert out["usage"]["cost"] == 0.0001
    assert out["model"] == "jev-test"


def test_retries_5xx_then_succeeds(fake_jev):
    from conftest import default_answers
    replies = [(503, {"error": "busy"}), (429, {"error": "slow down"})]
    fake_jev.responder = lambda body: replies.pop(0) if replies else (200, default_answers(body))
    assert "is_spam" in caller()("x", Q)["answers"]
    assert len(fake_jev.requests) == 3


def test_gives_up_after_retries(fake_jev):
    fake_jev.responder = lambda body: (503, {"error": "busy"})
    with pytest.raises(JevError, match="HTTP 503"):
        caller(retries=3)("x", Q)
    assert len(fake_jev.requests) == 4


def test_does_not_retry_other_4xx(fake_jev):
    fake_jev.responder = lambda body: (400, {"error": "bad"})
    with pytest.raises(JevError, match="HTTP 400"):
        caller()("x", Q)
    assert len(fake_jev.requests) == 1


@pytest.mark.parametrize("payload", [b"not json", {"no_answers": 1}, {"answers": []}])
def test_bad_response_is_error(fake_jev, payload):
    fake_jev.responder = lambda body: (200, payload)
    with pytest.raises(JevError):
        caller(retries=0)("x", Q)


def test_timeout_is_error(fake_jev):
    def slow(body):
        time.sleep(1.0)
        return 200, {"answers": {}}
    fake_jev.responder = slow
    started = time.monotonic()
    with pytest.raises(JevError):
        caller(timeout=0.2, retries=0)("x", Q)
    assert time.monotonic() - started < 0.9


def test_missing_key_raises():
    with pytest.raises(JevError, match="OPENROUTER_API_KEY"):
        caller()


def test_error_never_contains_key(fake_jev):
    fake_jev.responder = lambda body: (401, {"error": "bad key sk-test-secret"})
    with pytest.raises(JevError) as err:
        caller()("x", Q)
    assert "sk-test-secret" not in str(err.value)
