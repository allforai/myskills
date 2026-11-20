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


def _plugin_version(name):
    return json.loads((ROOT / "claude" / name / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))["version"]


def test_claude_directory_marketplace_matches_plugin_manifests():
    # claude/.claude-plugin/marketplace.json lists plugins by a path relative to claude/. Nothing
    # read it, so it sat at meta-skill 0.14.2 while the plugin shipped 0.34.x.
    listing = json.loads((ROOT / "claude/.claude-plugin/marketplace.json").read_text(encoding="utf-8"))
    for entry in listing["plugins"]:
        assert entry["version"] == _plugin_version(entry["name"]), entry["name"]


# A Pi package ships the same protocol as a Claude plugin, so its version is that plugin's plus a
# Pi revision. cross-exam has no Claude plugin of its own: it ships inside superstorm.
PI_TRACKS = {"meta-skill": "meta-skill", "cross-exam": "superstorm"}


@pytest.mark.parametrize("package", sorted(path.parent.name for path in ROOT.glob("pi/*/package.json")))
def test_pi_package_version_tracks_its_claude_plugin(package):
    assert package in PI_TRACKS, f"pi/{package}: name the Claude plugin it tracks in PI_TRACKS"
    version = json.loads((ROOT / "pi" / package / "package.json").read_text(encoding="utf-8"))["version"]
    base, sep, revision = version.partition("-pi.")
    assert sep and revision.isdigit() and base == _plugin_version(PI_TRACKS[package]), (
        f"pi/{package} is {version}; expected {_plugin_version(PI_TRACKS[package])}-pi.<n>")
