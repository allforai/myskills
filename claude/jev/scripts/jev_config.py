"""Config defaults, per-project model-routing switch, outbound allowlist, and shared paths.

Everything jev writes lives under ${XDG_CONFIG_HOME:-~/.config}/jev/ — never in CLAUDE_PLUGIN_ROOT,
which is a versioned cache directory.
"""
import copy
import json
import os
import re
import subprocess
from pathlib import Path

DEFAULTS = {
    "model": "~typesafe/jev-latest",
    "base_url": "https://openrouter.ai/api",
    "retries": 3,
    "route": {
        "threshold": 0.8,
        "timeout_s": 3.0,
        "max_prompt_chars": 8000,
        "tiers": {"light": "haiku", "standard": "sonnet"},
        # Substring of a model id -> capability rank. Routing only ever moves to a lower rank.
        "model_rank": {"haiku": 0, "sonnet": 1, "opus": 2, "fable": 3},
        # Session model to assume before the first reply exists; None = never route a session's first prompt.
        "assume_model": None,
    },
    "batch": {
        "concurrency": 8,
        "sample": 20,
        "calibrate_over": 50,
        "cost_cap_usd": 1.0,
        "input_usd_per_mtok": 0.042,
        "default_threshold": 0.8,
        "noul_hi": 0.9,
        "noul_lo": 0.1,
        "long_context_bytes": 32000,
        "request_timeout_s": 30.0,
    },
}


class ConfigError(Exception):
    pass


def config_dir() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "jev"


def read_json(path: Path, default):
    if not path.exists():
        return copy.deepcopy(default)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise ConfigError(f"{path}: {e}") from None


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _merge(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for key, value in over.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = value
    return out


def load_config() -> dict:
    path = config_dir() / "config.json"
    data = read_json(path, {})
    if not isinstance(data, dict):
        raise ConfigError(f"{path}: must be a JSON object")
    return _merge(DEFAULTS, data)


def project_root(cwd: str) -> str:
    try:
        out = subprocess.run(["git", "-C", cwd, "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, timeout=2)
        if out.returncode == 0 and out.stdout.strip():
            return os.path.realpath(out.stdout.strip())
    except (OSError, subprocess.TimeoutExpired):
        pass
    return os.path.realpath(cwd)


def _state_path() -> Path:
    return config_dir() / "state.json"


def route_projects() -> list[str]:
    return list(read_json(_state_path(), {"route_projects": []}).get("route_projects", []))


def is_route_on(root: str) -> bool:
    return root in route_projects()


def set_route(root: str, on: bool) -> None:
    projects = [p for p in route_projects() if p != root]
    if on:
        projects.append(root)
    write_json(_state_path(), {"route_projects": sorted(projects)})


def is_allowed(path: str) -> bool:
    target = Path(os.path.realpath(path))
    for entry in read_json(config_dir() / "allow.json", {"paths": []}).get("paths", []):
        prefix = Path(os.path.realpath(os.path.expanduser(entry)))
        if target.is_relative_to(prefix):
            return True
    return False


def log_path() -> Path:
    return config_dir() / "route-log.jsonl"


def append_route_log(record: dict) -> None:
    path = log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def calibrations_path() -> Path:
    return config_dir() / "calibrations.json"


def question_sets_dir() -> Path:
    return config_dir() / "question-sets"


def transcript_dir(root: str) -> Path:
    base = os.environ.get("CLAUDE_CONFIG_DIR") or str(Path.home() / ".claude")
    return Path(base) / "projects" / re.sub(r"[^A-Za-z0-9]", "-", root)
