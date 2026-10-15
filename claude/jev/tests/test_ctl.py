import json
from datetime import datetime, timedelta, timezone

import jev_config as C
import jev_ctl

NOW = datetime(2026, 10, 16, 12, 0, tzinfo=timezone.utc)


def log(**entry):
    C.append_route_log(entry)


def test_on_off_is_per_project(tmp_path):
    a = str(tmp_path / "a")
    msg = jev_ctl.cmd_on(a)
    assert a in msg and "原文" in msg and "第一句" in msg
    assert C.is_route_on(a)
    jev_ctl.cmd_off(a)
    assert not C.is_route_on(a)


def test_status_counts_recent_entries_of_this_project(tmp_path):
    a, b = str(tmp_path / "a"), str(tmp_path / "b")
    C.set_route(a, True)
    ts = (NOW - timedelta(days=1)).isoformat()
    old = (NOW - timedelta(days=8)).isoformat()
    log(ts=ts, event="route", project=a, sent=True, reason="routed", tier="light", target="haiku", latency_ms=200, cost=0.001)
    log(ts=ts, event="delegated", project=a, model="haiku")
    log(ts=ts, event="route", project=a, sent=True, reason="heavy", tier="heavy", latency_ms=400, cost=0.001)
    log(ts=ts, event="route", project=a, sent=True, reason="error", error="network: TimeoutError", latency_ms=3000)
    log(ts=ts, event="route", project=a, sent=False, reason="too_long")
    log(ts=old, event="route", project=a, sent=True, reason="routed", tier="light", target="haiku", latency_ms=1, cost=5.0)
    log(ts=ts, event="route", project=b, sent=True, reason="routed", tier="light", target="haiku", latency_ms=1, cost=5.0)
    out = jev_ctl.cmd_status(a, now=NOW)
    assert "本项目：开" in out
    assert "判断 3 句" in out and "未发送 1 句" in out
    assert "建议降档 1 次，委派 1 次" in out
    assert "超时 1" in out
    assert "$0.0020" in out


def write_jsonl(path, entries):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(e) + "\n" for e in entries))


def reply(model, mid, tin, tout, ts):
    return {"type": "assistant", "timestamp": ts, "message": {
        "id": mid, "model": model, "content": [{"type": "text", "text": "."}],
        "usage": {"input_tokens": tin, "cache_read_input_tokens": 100, "output_tokens": tout}}}


def test_status_reports_tokens_main_vs_subagent(tmp_path):
    a = str(tmp_path / "a")
    d = C.transcript_dir(a)
    ts = (NOW - timedelta(hours=1)).isoformat()
    old = (NOW - timedelta(days=9)).isoformat()
    write_jsonl(d / "s1.jsonl", [{"type": "user", "message": {"content": "hi"}},
                                 reply("claude-opus-5-5", "m1", 10, 5, ts),
                                 reply("claude-opus-5-5", "m1", 10, 5, ts),  # same message id twice: counted once
                                 reply("claude-opus-5-5", "m0", 999, 999, old),  # outside the window
                                 reply("claude-opus-5-5", "m3", 30, 9, ts)])
    write_jsonl(d / "s1" / "subagents" / "agent-x.jsonl", [reply("claude-haiku-5-5", "m2", 20, 7, ts)])
    out = jev_ctl.cmd_status(a, now=NOW)
    assert "主会话：claude-opus-5-5 输入 240 / 输出 14" in out
    assert "子 agent：claude-haiku-5-5 输入 120 / 输出 7" in out


def test_status_without_transcripts_says_none(tmp_path):
    out = jev_ctl.cmd_status(str(tmp_path / "a"), now=NOW)
    assert "主会话：无" in out and "子 agent：无" in out


def test_main_rejects_unknown_action():
    assert jev_ctl.main(["bogus"]) == 2
