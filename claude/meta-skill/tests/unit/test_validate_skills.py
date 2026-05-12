import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../scripts/orchestrator"))
from validate_skills import validate_skill_tree


def _write_skill(root, rel, body):
    path = root / rel / "SKILL.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)
    return path


def test_validate_skill_tree_accepts_layered_skill_path(tmp_path):
    _write_skill(
        tmp_path,
        "app-design/20-spec/data-model-spec",
        """---
name: data-model-spec
description: Test skill.
---

## Invocation Contract

```json
{"skill":"app-design/data-model-spec","mode":"spec_validate","input_paths":{"concept":".allforai/product-concept/concept-baseline.json"},"output_root":".allforai/app-design/spec"}
```
""",
    )

    assert validate_skill_tree(str(tmp_path)) == []


def test_validate_skill_tree_rejects_missing_invocation_target(tmp_path):
    _write_skill(
        tmp_path,
        "app-design/20-spec/data-model-spec",
        """---
name: data-model-spec
description: Test skill.
---

## Invocation Contract

```json
{"skill":"app-design/missing-spec","mode":"spec_validate","output_root":".allforai/app-design/spec"}
```
""",
    )

    errors = validate_skill_tree(str(tmp_path))
    assert any("missing-spec" in error for error in errors)


def test_validate_skill_tree_rejects_broken_canonical_path(tmp_path):
    _write_skill(
        tmp_path,
        "app-design",
        """---
name: app-design
description: Parent.
---

${CLAUDE_PLUGIN_ROOT}/skills/app-design/20-spec/missing/SKILL.md
""",
    )

    errors = validate_skill_tree(str(tmp_path))
    assert any("canonical skill path missing" in error for error in errors)


def test_validate_skill_tree_requires_frontmatter(tmp_path):
    _write_skill(
        tmp_path,
        "app-design/20-spec/data-model-spec",
        """# Data Model Spec

## Invocation Contract

```json
{"skill":"app-design/data-model-spec","mode":"spec_validate","output_root":".allforai/app-design/spec"}
```
""",
    )

    errors = validate_skill_tree(str(tmp_path))
    assert any("missing YAML frontmatter" in error for error in errors)
