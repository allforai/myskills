"""Generic UI previews survive removal of the retired provider integration."""
import json
from pathlib import Path
import runpy
import sys

import pytest

from ..module_isolation import bound

SCRIPTS = Path(__file__).resolve().parents[4] / "shared/scripts/product-design"


@pytest.fixture
def hub(tmp_path, monkeypatch):
    script = SCRIPTS / "review_hub_server.py"
    monkeypatch.setattr(sys, "argv", [str(script), str(tmp_path)])
    # Load CLI globals against temporary artifacts without starting an HTTP server
    # or leaking the shared tree's _common module into other suites.
    with bound(str(SCRIPTS)):
        yield runpy.run_path(str(script))


def put_ui_file(tmp_path, relative, content):
    path = tmp_path / "ui-design" / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_exact_preview_wins_over_retired_provider_files(hub, tmp_path):
    put_ui_file(tmp_path, "stitch/S001.html", "obsolete provider output")
    put_ui_file(tmp_path, "preview/S001.html", "<h1>Current preview</h1>")
    assert hub["render_ui_screen_html"]("S001") == "<h1>Current preview</h1>"


def test_preview_can_match_screen_id_in_content(hub, tmp_path):
    put_ui_file(tmp_path, "preview/index.html", "S001 index, not a screen")
    html = '<main id="S001">Screen preview</main>'
    put_ui_file(tmp_path, "preview/account.html", html)
    assert hub["render_ui_screen_html"]("S001") == html


def test_missing_preview_uses_spec_skeleton_and_ui_page_still_renders(hub, tmp_path):
    put_ui_file(tmp_path, "stitch/S001.html", "obsolete provider output")
    put_ui_file(tmp_path, "ui-design-spec.json", json.dumps({
        "screens": [{"id": "S001", "name": "Account", "role": "User",
                     "sections": ["Profile"], "states": {"empty": "No profile"}}],
    }))
    html = hub["render_ui_screen_html"]("S001")
    assert "Account" in html
    assert "Profile" in html
    assert "No profile" in html
    assert "obsolete provider output" not in html
    page = hub["render_ui_page"]()
    assert "S001" in page
    assert "Account" in page
    assert "has_stitch" not in page
    assert "ui-tree-badge stitch" not in page


def test_retired_provider_alone_is_not_a_preview(hub, tmp_path):
    put_ui_file(tmp_path, "stitch/S001.html", "obsolete provider output")
    assert hub["render_ui_screen_html"]("S001") == "<h2>No preview available</h2>"
