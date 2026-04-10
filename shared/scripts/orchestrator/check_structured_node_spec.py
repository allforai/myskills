#!/usr/bin/env python3
"""Validate Phase 1 structured node-spec sections.

Checks:
  - file exists
  - YAML frontmatter starts with node:
  - contains `## Spec`
  - contains `## Design`
  - contains `## Task`
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


REQUIRED_HEADERS = ["## Spec", "## Design", "## Task"]


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: check_structured_node_spec.py <node-spec.md>")
        return 1

    path = Path(sys.argv[1])
    errors: list[str] = []

    if not path.exists():
        print(json.dumps({"passed": False, "errors": [f"missing: {path}"]}, indent=2, ensure_ascii=False))
        return 1

    text = path.read_text(encoding="utf-8")

    if not text.startswith("---"):
        errors.append("missing YAML frontmatter start")
    if "node:" not in text.split("---", 2)[1] if text.startswith("---") and text.count("---") >= 2 else True:
        errors.append("frontmatter missing node field")

    for header in REQUIRED_HEADERS:
        if header not in text:
            errors.append(f"missing section: {header}")

    result = {"passed": not errors, "errors": errors}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
