"""UserPromptSubmit hook: ask Jev how much model a typed prompt needs; when a cheaper tier
will do, suggest that Claude hand the work to a subagent running that tier's model.

A skill's frontmatter `model` does not switch the session model (probe P2), so routing is a
suggestion to delegate, and the main session — on its own model — checks what comes back.

Never in the way: switch off, no key, error, timeout or bad config -> no output, exit 0.
The prompt text is sent to Jev but never written to the log.
"""
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import jev_config as C  # noqa: E402
from jev_client import JevError, make_caller  # noqa: E402

QUESTION_FILE = Path(__file__).resolve().parent / "route_question.json"
SYSTEM_TAG = re.compile(r"^\s*<[A-Za-z][\w-]*[\s>/]")
TAIL_BYTES = 512 * 1024


def is_typed(prompt: str) -> bool:
    return not SYSTEM_TAG.match(prompt)


def model_rank(model, ranks):
    if not model:
        return None
    name = model.lower()
    hits = [rank for key, rank in ranks.items() if key in name]
    return max(hits) if hits else None


def read_tail(path):
    try:
        with open(path, "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - TAIL_BYTES))
            return f.read().decode("utf-8", "replace").splitlines()
    except (OSError, TypeError):
        return []


def real_model(entry):
    model = (entry.get("message") or {}).get("model")
    return model if isinstance(model, str) and model and not model.startswith("<") else None


def iter_assistant(lines):
    for line in lines:
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if isinstance(entry, dict) and entry.get("type") == "assistant":
            yield entry


def session_model(transcript_path):
    """Model of the main session's latest real reply. Subagent replies live in their own
    transcripts (and are marked isSidechain when inlined), so delegation never changes this."""
    base = None
    for entry in iter_assistant(read_tail(transcript_path)):
        if not entry.get("isSidechain") and real_model(entry):
            base = real_model(entry)
    return base


def decide(hook_input, cfg, ask, question):
    rc = cfg["route"]
    ranks = rc["model_rank"]
    prompt = hook_input.get("prompt") or ""
    log = {"prompt_len": len(prompt), "sent": False, "action": "none"}
    if not is_typed(prompt):
        return None, {**log, "reason": "not_typed"}
    if len(prompt) > rc["max_prompt_chars"]:
        return None, {**log, "reason": "too_long"}
    current = session_model(hook_input.get("transcript_path"))
    if current is None and rc.get("assume_model"):
        current, log["assumed_model"] = rc["assume_model"], True
    cur_rank = model_rank(current, ranks)
    if cur_rank is None:
        return None, {**log, "reason": "unknown_model"}
    log["current_model"] = current
    tier_ranks = [r for r in (model_rank(m, ranks) for m in rc["tiers"].values()) if r is not None]
    if not tier_ranks or cur_rank <= min(tier_ranks):
        return None, {**log, "reason": "already_cheapest"}

    started = time.monotonic()
    try:
        result = ask(prompt, question)
    except JevError as e:
        return None, {**log, "sent": True, "reason": "error", "error": str(e),
                      "latency_ms": round((time.monotonic() - started) * 1000)}
    log.update(sent=True, latency_ms=round((time.monotonic() - started) * 1000),
               cost=(result.get("usage") or {}).get("cost"))

    ans = result["answers"].get("tier") or {}
    tier = ans.get("choice")
    prob = (ans.get("probabilities") or {}).get(tier)
    if not isinstance(prob, (int, float)):
        return None, {**log, "reason": "bad_answer"}
    log.update(tier=tier, prob=prob)
    target = rc["tiers"].get(tier)
    if target is None:
        return None, {**log, "reason": "heavy"}
    if prob < rc["threshold"]:
        return None, {**log, "reason": "low_confidence"}
    target_rank = model_rank(target, ranks)
    if target_rank is None or target_rank >= cur_rank:
        return None, {**log, "reason": "not_lower"}

    context = (f"[Jev 路由] Jev 判断这条请求属于 {tier} 档（概率 {prob:.2f}），更便宜的 {target} 就够用。"
               f'如果这件事能独立交出去，用 Agent 工具派一个 model: "{target}" 的子 agent 去做，'
               "你核对它交回的结果后再答复用户；需要你自己的上下文或判断时就自己做。"
               "这只是成本路由，不改变任务内容。")
    out = {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": context},
           "systemMessage": f"Jev → {target} ({prob:.2f})"}
    return out, {**log, "action": "suggest_delegate", "target": target, "reason": "routed"}


def main(stdin=sys.stdin, stdout=sys.stdout):
    try:
        hook_input = json.load(stdin)
        cfg = C.load_config()
        root = C.project_root(hook_input.get("cwd") or ".")
        if not C.is_route_on(root):
            return 0
        prompt = hook_input.get("prompt") or ""
        try:
            ask = make_caller(cfg, timeout=cfg["route"]["timeout_s"], retries=0)
        except JevError:
            out, log = None, {"prompt_len": len(prompt), "sent": False, "action": "none", "reason": "no_key"}
        else:
            question = json.loads(QUESTION_FILE.read_text(encoding="utf-8"))
            out, log = decide(hook_input, cfg, ask, question)
        if out:
            stdout.write(json.dumps(out, ensure_ascii=False))
        try:
            C.append_route_log({"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "event": "route",
                                "session_id": hook_input.get("session_id"), "project": root,
                                "cwd": hook_input.get("cwd"), **log})
        except OSError:
            pass
    except Exception:  # the hook must never get in the user's way
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
