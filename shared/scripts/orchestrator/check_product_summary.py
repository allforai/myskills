#!/usr/bin/env python3
"""Validate bootstrap product-summary.json outputs.

Checks:
  - parseable JSON
  - required top-level fields exist
  - evidence contains at least 3 entries
  - core_systems contains at least 1 entry
  - confidence is one of high|medium|low
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


ALLOWED_CONFIDENCE = {"high", "medium", "low"}


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: check_product_summary.py <product-summary.json>")
        return 1

    path = Path(sys.argv[1])
    errors: list[str] = []

    if not path.exists():
        print(json.dumps({"passed": False, "errors": [f"missing: {path}"]}, indent=2, ensure_ascii=False))
        return 1

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(json.dumps({"passed": False, "errors": [f"parse error: {exc}"]}, indent=2, ensure_ascii=False))
        return 1

    for field in ["schema_version", "project_name", "product_shape", "platforms", "core_systems", "evidence", "confidence", "open_questions"]:
        if field not in data:
            errors.append(f"missing field: {field}")

    if not isinstance(data.get("platforms"), list) or not data.get("platforms"):
        errors.append("platforms must be a non-empty list")

    if not isinstance(data.get("core_systems"), list) or len(data.get("core_systems", [])) < 1:
        errors.append("core_systems must contain at least 1 entry")

    evidence = data.get("evidence")
    if not isinstance(evidence, list) or len(evidence) < 3:
        errors.append("evidence must contain at least 3 entries")
    else:
        for idx, item in enumerate(evidence):
            if not isinstance(item, dict):
                errors.append(f"evidence[{idx}] must be an object")
                continue
            for field in ["kind", "path", "note"]:
                if field not in item or not item[field]:
                    errors.append(f"evidence[{idx}] missing field: {field}")

    if data.get("confidence") not in ALLOWED_CONFIDENCE:
        errors.append("confidence must be one of: high, medium, low")

    if not isinstance(data.get("open_questions"), list):
        errors.append("open_questions must be a list")

    result = {"passed": not errors, "errors": errors}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
