#!/usr/bin/env python3
"""Validate game-design node cross-references across capability and scenario templates."""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent / "claude/meta-skill/knowledge"
CAPABILITY = ROOT / "capabilities/game-design.md"
TEMPLATES_DIR = ROOT / "game-scenario-templates"

VALID_ROLES = {
    "lead-designer", "combat-designer", "systems-designer", "narrative-designer",
    "level-designer", "numeric-designer", "monetization-designer", "ux-designer",
    "gameplay-programmer", "backend-programmer", "ui-programmer", "ai-programmer",
    "graphics-programmer", "tools-programmer",
    "art-director", "concept-artist", "ui-artist", "character-modeler",
    "environment-artist", "animator", "vfx-artist", "technical-artist",
    "audio-director", "producer",
}

errors = []

# 1. Extract canonical node_ids from game-design.md
capability_text = CAPABILITY.read_text()
# Extract the canonical table section (between "## Canonical Node Registry" and next section)
# Table rows start with | `node-id` | role | and contain exactly 5 columns
canonical_ids = set()
in_table = False
for line in capability_text.splitlines():
    if "## Canonical Node Registry" in line:
        in_table = True
        continue
    if in_table:
        if line.startswith("##"):
            # New section, table is over
            break
        # Only match rows with exactly node-id in first column
        m = re.match(r'^\| `([a-z][a-z0-9-]+)` \|', line)
        if m:
            canonical_ids.add(m.group(1))

print(f"Found {len(canonical_ids)} canonical node IDs in game-design.md")

# 2. Validate each scenario template
for tmpl_path in sorted(TEMPLATES_DIR.glob("*.json")):
    with open(tmpl_path) as f:
        tmpl = json.load(f)

    scenario_id = tmpl["scenario_id"]

    for field in ("required_nodes", "optional_nodes", "always_include", "node_order"):
        for node_id in tmpl.get(field, []):
            if node_id not in canonical_ids:
                # Check if it has a bootstrap_note (ad-hoc nodes are expected)
                if "bootstrap_note" not in tmpl:
                    errors.append(
                        f"[{scenario_id}] {field}: '{node_id}' not in canonical registry "
                        f"and no bootstrap_note present"
                    )

    print(f"  {scenario_id}: {len(tmpl['required_nodes'])} required + "
          f"{len(tmpl.get('optional_nodes', []))} optional + "
          f"{len(tmpl['always_include'])} always_include")

if errors:
    print(f"\n❌ {len(errors)} validation error(s):")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
else:
    print("\n✅ All cross-references valid")
