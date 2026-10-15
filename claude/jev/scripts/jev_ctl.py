"""/jev on | off | status — the per-project model-routing switch and its evidence:
how often delegation was suggested vs done, and the tokens each model actually used."""
import argparse
import json
import os
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import jev_config as C  # noqa: E402
import route  # noqa: E402

WINDOW_DAYS = 7
INPUT_KEYS = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")


def cmd_on(root):
    C.set_route(root, True)
    lines = [f"已在本项目打开 Jev 选模型：{root}",
             "从现在起，在这个项目里你每句手打的话，原文会经 OpenRouter 发给 Jev 判断难度（日志不记原文）。",
             "判为简单时，会建议 Claude 把这件事交给更便宜模型的子 agent 去做，再由主会话核对。",
             "新会话的第一句不会判断（还读不出会话模型）。关闭：/jev off"]
    if not os.environ.get("OPENROUTER_API_KEY"):
        lines.append("注意：当前没有 OPENROUTER_API_KEY，设置之前不会有任何判断。")
    return "\n".join(lines)


def cmd_off(root):
    C.set_route(root, False)
    return f"已在本项目关闭 Jev 选模型：{root}"


def _parse_ts(value):
    try:
        ts = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)


def _log_entries(root, since):
    path = C.log_path()
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            e = json.loads(line)
        except ValueError:
            continue
        ts = _parse_ts(e.get("ts")) if isinstance(e, dict) else None
        if ts and e.get("project") == root and ts >= since:
            out.append(e)
    return out


def transcript_usage(root, since):
    """{(kind, model): [input incl. cache, output]} with kind "main" or "subagent"."""
    usage, seen = {}, set()
    folder = C.transcript_dir(root)
    if not folder.is_dir():
        return usage
    files = [("main", p) for p in folder.glob("*.jsonl")] + [("subagent", p) for p in folder.glob("*/subagents/*.jsonl")]
    for kind, path in files:
        try:
            if datetime.fromtimestamp(path.stat().st_mtime, timezone.utc) < since:
                continue
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for entry in route.iter_assistant(lines):
            msg = entry.get("message") or {}
            model, u, ts = route.real_model(entry), msg.get("usage"), _parse_ts(entry.get("timestamp"))
            if not model or not isinstance(u, dict) or not ts or ts < since:
                continue
            key = msg.get("id") or f"{path}:{id(entry)}"
            if key in seen:
                continue
            seen.add(key)
            slot = usage.setdefault((kind, model), [0, 0])
            slot[0] += sum(u.get(k) or 0 for k in INPUT_KEYS)
            slot[1] += u.get("output_tokens") or 0
    return usage


def _fmt_usage(usage, kind):
    items = [f"{model} 输入 {v[0]} / 输出 {v[1]}" for (k, model), v in sorted(usage.items()) if k == kind]
    return "；".join(items) or "无"


def cmd_status(root, now=None):
    now = now or datetime.now(timezone.utc)
    since = now - timedelta(days=WINDOW_DAYS)
    entries = _log_entries(root, since)
    decisions = [e for e in entries if e.get("event", "route") == "route"]
    sent = [e for e in decisions if e.get("sent")]
    tiers = Counter(e.get("tier") for e in sent if e.get("tier"))
    suggested = sum(1 for e in sent if e.get("reason") == "routed")
    delegated = sum(1 for e in entries if e.get("event") == "delegated")
    errors = [e for e in sent if e.get("reason") == "error"]
    timeouts = sum(1 for e in errors if "Timeout" in (e.get("error") or ""))
    latencies = [e["latency_ms"] for e in sent if isinstance(e.get("latency_ms"), (int, float))]
    cost = sum(e.get("cost") or 0 for e in sent)
    usage = transcript_usage(root, since)
    enabled = C.route_projects()
    fmt = lambda c: "、".join(f"{k} {v}" for k, v in sorted(c.items())) or "无"
    return "\n".join([
        f"本项目：{'开' if root in enabled else '关'}（{root}）",
        f"已打开的项目：{', '.join(enabled) or '无'}",
        f"最近 {WINDOW_DAYS} 天：判断 {len(sent)} 句，未发送 {len(decisions) - len(sent)} 句",
        f"Jev 判档：{fmt(tiers)}",
        f"建议降档 {suggested} 次，委派 {delegated} 次",
        f"失败 {len(errors) - timeouts}，超时 {timeouts}",
        f"平均延迟：{round(sum(latencies) / len(latencies)) if latencies else '-'} ms",
        f"Jev 花费：${cost:.6f}",
        "实际 token（来自本项目 transcript，输入含缓存）：",
        f"  主会话：{_fmt_usage(usage, 'main')}",
        f"  子 agent：{_fmt_usage(usage, 'subagent')}",
    ])


def main(argv):
    parser = argparse.ArgumentParser(prog="/jev")
    parser.add_argument("action", choices=["on", "off", "status"])
    parser.add_argument("--cwd", default=os.getcwd())
    try:
        args = parser.parse_args(argv)
    except SystemExit:
        return 2
    root = C.project_root(args.cwd)
    try:
        print({"on": cmd_on, "off": cmd_off, "status": cmd_status}[args.action](root))
    except C.ConfigError as e:
        print(f"配置文件有问题：{e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
