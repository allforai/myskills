"""Parse actual shipping manifests, including releases outside the renderer package."""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
MANIFESTS = sorted({
    *ROOT.glob(".claude-plugin/*.json"),
    *ROOT.glob("claude/*/.claude-plugin/*.json"),
    *ROOT.glob("pi/*/package.json"),
    ROOT / "package.json",
})


@pytest.mark.parametrize("path", MANIFESTS, ids=lambda path: str(path.relative_to(ROOT)))
def test_shipping_manifest_is_valid_json(path):
    assert isinstance(json.loads(path.read_text(encoding="utf-8")), dict)


def test_marketplace_versions_match_plugin_manifests():
    marketplace = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
    for entry in marketplace["plugins"]:
        directory = ROOT / entry["source"] / ".claude-plugin"
        plugin = json.loads((directory / "plugin.json").read_text(encoding="utf-8"))
        local = json.loads((directory / "marketplace.json").read_text(encoding="utf-8"))
        listing = next(row for row in local["plugins"] if row["name"] == plugin["name"])
        assert entry["name"] == plugin["name"]
        assert entry["version"] == plugin["version"] == listing["version"]
