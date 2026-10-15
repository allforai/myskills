"""PostToolUse(Agent|Task) hook: when routing is on for this project and Claude starts a subagent
on one of the tier models, record it, so /jev status can tell suggested routes from followed ones.
Silent; always exit 0."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import jev_config as C  # noqa: E402


def main(stdin=sys.stdin):
    try:
        data = json.load(stdin)
        model = (data.get("tool_input") or {}).get("model")
        if data.get("tool_name") not in ("Agent", "Task") or not model:
            return 0
        if model not in C.load_config()["route"]["tiers"].values():
            return 0
        root = C.project_root(data.get("cwd") or ".")
        if C.is_route_on(root):
            C.append_route_log({"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                "event": "delegated", "session_id": data.get("session_id"),
                                "project": root, "model": model})
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
