#!/usr/bin/env python3
"""Mechanical checks for Codex IM specialization guidance.

This validates that the Codex-only IM specialization hook defines the expected
research-first and responsibility-floor behavior for realtime messaging products.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CODEX_META = ROOT / "codex" / "meta-skill"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    hook_path = CODEX_META / "knowledge" / "high-risk-specialization.md"
    im_path = CODEX_META / "knowledge" / "im-specialization.md"
    bootstrap_path = CODEX_META / "skills" / "bootstrap.md"

    for path, label in [
        (hook_path, "high-risk specialization"),
        (im_path, "IM specialization"),
        (bootstrap_path, "Codex bootstrap adapter"),
    ]:
        if not path.exists():
            errors.append(f"missing: {label} ({path})")

    if errors:
        print(json.dumps({"passed": False, "errors": errors, "warnings": warnings}, indent=2, ensure_ascii=False))
        return 1

    hook = read(hook_path).lower()
    im = read(im_path).lower()
    bootstrap = read(bootstrap_path).lower()

    required_hook_terms = [
        "research first",
        "llm",
        "mandatory responsibility",
        "high-risk",
    ]
    for term in required_hook_terms:
        if term not in hook:
            errors.append(f"high-risk hook missing term: {term}")

    required_im_responsibilities = [
        "realtime transport",
        "push delivery path",
        "media storage",
        "search indexing",
        "message state machine",
        "sync engine",
        "session management",
        "moderation controls",
        "message-state verification",
        "multi-device sync verification",
    ]
    for term in required_im_responsibilities:
        if term not in im:
            errors.append(f"IM specialization missing responsibility: {term}")

    bootstrap_terms = [
        "high-risk domain specialization hook",
        "im / realtime messaging specialization",
        "im_realtime",
        "research-first specialization",
    ]
    for term in bootstrap_terms:
        if term not in bootstrap:
            errors.append(f"bootstrap adapter missing IM/hook wiring: {term}")

    if "telegram" not in im and "whatsapp" not in im and "discord" not in im:
        warnings.append("IM specialization guidance does not mention concrete messaging examples")

    result = {"passed": not errors, "errors": errors, "warnings": warnings}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
