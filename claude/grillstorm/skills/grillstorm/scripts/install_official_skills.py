#!/usr/bin/env python3
"""Detect or install the official Matt Pocock skills Grillstorm orchestrates."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


REQUIRED_SKILLS = (
    "grilling",
    "grill-me",
    "grill-with-docs",
    "domain-modeling",
    "setup-matt-pocock-skills",
    "to-spec",
    "to-tickets",
    "tdd",
    "code-review",
    "diagnosing-bugs",
)

OPTIONAL_SKILLS = (
    "research",
    "prototype",
    "codebase-design",
    "resolving-merge-conflicts",
)

INSTALL_SKILLS = REQUIRED_SKILLS + OPTIONAL_SKILLS

HOME = Path.home()

SEARCH_ROOTS = (
    HOME / ".pi" / "agent" / "skills",
    HOME / ".agents" / "skills",
    HOME / ".codex" / "skills",
    HOME / ".claude" / "skills",
    HOME / ".claude" / "plugins" / "cache",
)


def _skill_md(path: Path) -> Path | None:
    if path.is_file() and path.name == "SKILL.md":
        return path
    candidate = path / "SKILL.md"
    return candidate if candidate.is_file() else None


def _name_from_skill_md(skill_md: Path) -> str | None:
    try:
        text = skill_md.read_text(encoding="utf-8")
    except OSError:
        return None
    if not text.startswith("---"):
        return skill_md.parent.name
    parts = text.split("---", 2)
    if len(parts) < 3:
        return skill_md.parent.name
    for line in parts[1].splitlines():
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip().strip('"').strip("'")
    return skill_md.parent.name


def discover_skills() -> dict[str, Path]:
    found: dict[str, Path] = {}
    for root in SEARCH_ROOTS:
        if not root.exists():
            continue
        if root.name == "cache":
            for skill_md in root.glob("**/mattpocock-skills/**/SKILL.md"):
                name = _name_from_skill_md(skill_md)
                if name and name not in found:
                    found[name] = skill_md
            continue
        for child in root.iterdir():
            skill_md = _skill_md(child)
            if skill_md is None:
                continue
            name = _name_from_skill_md(skill_md)
            if name and name not in found:
                found[name] = skill_md
    return found


def missing_required(found: dict[str, Path]) -> list[str]:
    return [name for name in REQUIRED_SKILLS if name not in found]


def detect_host() -> str:
    if os.environ.get("CLAUDE_PLUGIN_ROOT") or os.environ.get("CLAUDECODE"):
        return "claude"
    if os.environ.get("CODEX_HOME") or os.environ.get("CODEX_SESSION_ID"):
        return "codex"
    if os.environ.get("PI_AGENT") or os.environ.get("PI_CODING_AGENT"):
        return "pi"
    if shutil.which("claude") and not shutil.which("pi"):
        return "claude"
    if shutil.which("pi"):
        return "pi"
    return "generic"


def install_command(host: str) -> list[str]:
    skill_csv = ",".join(INSTALL_SKILLS)
    if host == "claude":
        return ["claude", "plugin", "install", "mattpocock-skills", "-s", "user", "-y"]
    agent = {"pi": "pi", "codex": "codex", "claude": "claude-code"}.get(host, "*")
    return [
        "npx",
        "--yes",
        "skills@latest",
        "add",
        "mattpocock/skills",
        "-g",
        "-y",
        "-a",
        agent,
        "-s",
        skill_csv,
    ]


def run_install(host: str, dry_run: bool) -> int:
    command = install_command(host)
    print(json.dumps({"host": host, "command": command}, ensure_ascii=False))
    if dry_run:
        return 0
    completed = subprocess.run(command, check=False)
    return completed.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("status", "install"))
    parser.add_argument("--host", choices=("auto", "claude", "pi", "codex", "generic"), default="auto")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    found = discover_skills()
    missing = missing_required(found)
    host = detect_host() if args.host == "auto" else args.host
    payload = {
        "host": host,
        "found": {name: str(path) for name, path in sorted(found.items()) if name in INSTALL_SKILLS},
        "missing_required": missing,
        "install_command": install_command(host),
    }
    if args.action == "status":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1 if missing else 0
    if missing or args.dry_run:
        code = run_install(host, args.dry_run)
        if code != 0:
            return code
        if args.dry_run:
            return 0
        found = discover_skills()
        missing = missing_required(found)
        print(json.dumps({"missing_required": missing, "found": {n: str(found[n]) for n in REQUIRED_SKILLS if n in found}}, ensure_ascii=False, indent=2))
        return 1 if missing else 0
    print(json.dumps({"already_installed": True, "found": payload["found"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
