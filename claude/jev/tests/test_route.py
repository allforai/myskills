import io
import json
import time

import pytest

import delegate_seen
import jev_config as C
import route
from jev_client import JevError

QUESTION = json.loads(route.QUESTION_FILE.read_text())


# ---- transcript builders (shapes confirmed by probe P2) ----

def user(text="hi"):
    return {"type": "user", "message": {"role": "user", "content": text}}


def reply(model, sidechain=False):
    entry = {"type": "assistant", "message": {"model": model, "content": [{"type": "text", "text": "..."}]}}
    if sidechain:
        entry["isSidechain"] = True
    return entry


def write_transcript(tmp_path, entries, garbage=False):
    lines = [json.dumps(e) for e in entries]
    if garbage:
        lines.insert(1, "{broken")
    path = tmp_path / "t.jsonl"
    path.write_text("\n".join(lines) + "\n")
    return str(path)


def transcript(tmp_path, *models, garbage=False):
    entries = [user()]
    for m in models:
        entries += [reply(m), user()]
    return write_transcript(tmp_path, entries, garbage)


def answer(tier, p):
    others = {t: (1 - p) / 2 for t in ("light", "standard", "heavy") if t != tier}
    return {"answers": {"tier": {"type": "choice", "choice": tier, "confidence": p,
                                 "probabilities": {tier: p, **others}}},
            "usage": {"cost": 0.00002}, "model": "jev-test"}


class Ask:
    def __init__(self, result=None, error=None):
        self.calls, self.result, self.error = [], result, error

    def __call__(self, state, questions):
        self.calls.append(state)
        if self.error:
            raise self.error
        return self.result


def run(tmp_path, prompt, ask, models=("claude-opus-5-5",), **kw):
    hook = {"prompt": prompt, "transcript_path": transcript(tmp_path, *models, **kw)}
    return route.decide(hook, C.load_config(), ask, QUESTION)


# ---- decide() ----

def test_light_on_opus_suggests_haiku_subagent(tmp_path):
    out, log = run(tmp_path, "where is the deploy script?", Ask(answer("light", 0.93)))
    ctx = out["hookSpecificOutput"]["additionalContext"]
    assert out["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
    assert "Jev" in ctx and 'model: "haiku"' in ctx and "Agent" in ctx
    assert out["systemMessage"] == "Jev → haiku (0.93)"
    assert log["reason"] == "routed" and log["target"] == "haiku"


def test_standard_on_fable_suggests_sonnet(tmp_path):
    out, _ = run(tmp_path, "add a test", Ask(answer("standard", 0.9)), models=("claude-fable-5-1",))
    assert 'model: "sonnet"' in out["hookSpecificOutput"]["additionalContext"]


@pytest.mark.parametrize("tier,p,reason", [("heavy", 0.99, "heavy"), ("light", 0.6, "low_confidence")])
def test_no_route(tmp_path, tier, p, reason):
    out, log = run(tmp_path, "x", Ask(answer(tier, p)))
    assert out is None and log["reason"] == reason


def test_never_routes_up_or_sideways(tmp_path):
    out, log = run(tmp_path, "x", Ask(answer("standard", 0.95)), models=("claude-sonnet-5-5",))
    assert out is None and log["reason"] == "not_lower"


def test_already_cheapest_does_not_call_jev(tmp_path):
    ask = Ask(answer("light", 0.99))
    out, log = run(tmp_path, "x", ask, models=("claude-haiku-5-5",))
    assert out is None and ask.calls == [] and log["reason"] == "already_cheapest"


@pytest.mark.parametrize("models,garbage", [((), False), (("<synthetic>",), True), (("some-other-model",), False)])
def test_unknown_session_model_does_not_call_jev(tmp_path, models, garbage):
    ask = Ask(answer("light", 0.99))
    out, log = run(tmp_path, "x", ask, models=models, garbage=garbage)
    assert out is None and ask.calls == [] and log["reason"] == "unknown_model"


def test_first_prompt_uses_assume_model_when_set(tmp_path, cfg_dir):
    C.write_json(cfg_dir / "config.json", {"route": {"assume_model": "claude-opus-5-5"}})
    out, log = run(tmp_path, "where is x", Ask(answer("light", 0.95)), models=())
    assert out is not None and log["assumed_model"] is True


def test_missing_transcript_is_unknown_model():
    ask = Ask(answer("light", 0.99))
    out, log = route.decide({"prompt": "x", "transcript_path": "/nope/t.jsonl"}, C.load_config(), ask, QUESTION)
    assert out is None and ask.calls == []


def test_transcript_skips_trailing_synthetic(tmp_path):
    assert route.session_model(transcript(tmp_path, "claude-opus-5-5", "<synthetic>")) == "claude-opus-5-5"


def test_sidechain_replies_do_not_count_as_session_model(tmp_path):
    path = write_transcript(tmp_path, [user(), reply("claude-opus-5-5"), reply("claude-haiku-5-5", sidechain=True)])
    assert route.session_model(path) == "claude-opus-5-5"


def test_user_model_switch_is_respected(tmp_path):
    path = write_transcript(tmp_path, [user(), reply("claude-opus-5-5"), user("now on haiku"), reply("claude-haiku-5-5")])
    ask = Ask(answer("standard", 0.99))
    out, log = route.decide({"prompt": "x", "transcript_path": path}, C.load_config(), ask, QUESTION)
    assert out is None and log["reason"] == "already_cheapest" and ask.calls == []


def test_tail_starting_mid_line_is_tolerated(tmp_path, monkeypatch):
    path = transcript(tmp_path, "claude-opus-5-5")
    size = len(open(path, "rb").read())
    monkeypatch.setattr(route, "TAIL_BYTES", size - 5)  # cut inside the first JSON line
    assert route.session_model(path) == "claude-opus-5-5"


# ---- what is never sent ----

@pytest.mark.parametrize("prompt", ["<task-notification>\n<task-id>1</task-id>", "  <system-reminder>hi"])
def test_non_typed_prompts_are_not_sent(tmp_path, prompt):
    ask = Ask(answer("light", 0.99))
    out, log = run(tmp_path, prompt, ask)
    assert out is None and ask.calls == [] and log["reason"] == "not_typed"


def test_long_prompt_is_not_sent(tmp_path):
    ask = Ask(answer("light", 0.99))
    out, log = run(tmp_path, "x" * 8001, ask)
    assert out is None and ask.calls == [] and log["reason"] == "too_long"


def test_jev_error_means_no_output(tmp_path):
    out, log = run(tmp_path, "x", Ask(error=JevError("network: TimeoutError")))
    assert out is None and log["reason"] == "error" and log["sent"] is True


# ---- main(): the hook entry point ----

def hook_main(stdin_obj):
    stdout = io.StringIO()
    raw = stdin_obj if isinstance(stdin_obj, str) else json.dumps(stdin_obj)
    assert route.main(io.StringIO(raw), stdout) == 0
    return stdout.getvalue()


def test_switch_off_sends_nothing_and_logs_nothing(fake_jev, git_repo, tmp_path):
    out = hook_main({"prompt": "where is x", "cwd": str(git_repo), "transcript_path": transcript(tmp_path, "claude-opus-5-5")})
    assert out == "" and fake_jev.requests == [] and not C.log_path().exists()


def test_switch_on_routes_and_log_has_no_prompt_text(fake_jev, git_repo, tmp_path):
    fake_jev.responder = lambda body: (200, answer("light", 0.95))
    C.set_route(C.project_root(str(git_repo)), True)
    sub = git_repo / "src"
    sub.mkdir()
    out = hook_main({"prompt": "where is the SECRET-PHRASE file", "cwd": str(sub), "session_id": "s1",
                     "transcript_path": transcript(tmp_path, "claude-opus-5-5")})
    assert json.loads(out)["systemMessage"].startswith("Jev → haiku")
    assert fake_jev.requests[0]["body"]["state"] == "where is the SECRET-PHRASE file"
    log = C.log_path().read_text()
    assert "SECRET-PHRASE" not in log
    entry = json.loads(log.splitlines()[-1])
    assert entry["event"] == "route" and entry["session_id"] == "s1"
    assert entry["cwd"] == str(sub)
    assert entry["project"] == C.project_root(str(git_repo))


def test_other_project_stays_off(fake_jev, git_repo, tmp_path):
    C.set_route(C.project_root(str(git_repo)), True)
    other = tmp_path / "other"
    other.mkdir()
    assert hook_main({"prompt": "x", "cwd": str(other), "transcript_path": transcript(tmp_path, "claude-opus-5-5")}) == ""
    assert fake_jev.requests == []


def test_no_key_is_silent(git_repo, tmp_path):
    C.set_route(C.project_root(str(git_repo)), True)
    assert hook_main({"prompt": "x", "cwd": str(git_repo), "transcript_path": transcript(tmp_path, "claude-opus-5-5")}) == ""
    assert json.loads(C.log_path().read_text().splitlines()[-1])["reason"] == "no_key"


def test_slow_jev_is_silent(fake_jev, git_repo, tmp_path, cfg_dir):
    def slow(body):
        time.sleep(1.0)
        return 200, answer("light", 0.99)
    fake_jev.responder = slow
    C.write_json(cfg_dir / "config.json", {"route": {"timeout_s": 0.2}})
    C.set_route(C.project_root(str(git_repo)), True)
    assert hook_main({"prompt": "x", "cwd": str(git_repo), "transcript_path": transcript(tmp_path, "claude-opus-5-5")}) == ""


def test_malformed_config_is_silent(fake_jev, git_repo, tmp_path, cfg_dir):
    C.set_route(C.project_root(str(git_repo)), True)
    (cfg_dir / "config.json").write_text("{broken")
    assert hook_main({"prompt": "x", "cwd": str(git_repo), "transcript_path": transcript(tmp_path, "claude-opus-5-5")}) == ""
    assert fake_jev.requests == []


def test_garbage_stdin_is_silent():
    assert hook_main("not json at all") == ""


# ---- delegate_seen: did Claude actually delegate ----

def agent_call(model, cwd, tool="Agent"):
    return io.StringIO(json.dumps({"tool_name": tool, "tool_input": {"prompt": "find x", "model": model},
                                   "session_id": "s1", "cwd": cwd}))


def test_delegate_seen_logs_tier_model_agents_when_on(git_repo):
    root = C.project_root(str(git_repo))
    C.set_route(root, True)
    delegate_seen.main(agent_call("haiku", str(git_repo)))
    delegate_seen.main(agent_call("sonnet", str(git_repo), tool="Task"))
    delegate_seen.main(agent_call("opus", str(git_repo)))      # not a tier model
    delegate_seen.main(agent_call(None, str(git_repo)))        # inherits session model
    assert delegate_seen.main(io.StringIO("garbage")) == 0
    lines = [json.loads(l) for l in C.log_path().read_text().splitlines()]
    assert [{k: v for k, v in e.items() if k != "ts"} for e in lines] == [
        {"event": "delegated", "session_id": "s1", "project": root, "model": "haiku"},
        {"event": "delegated", "session_id": "s1", "project": root, "model": "sonnet"}]


def test_delegate_seen_silent_when_off(git_repo):
    delegate_seen.main(agent_call("haiku", str(git_repo)))
    assert not C.log_path().exists()
