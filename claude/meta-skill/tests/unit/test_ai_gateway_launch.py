"""The ai-gateway launcher installs missing runtime dependencies, then starts the server."""
import os
import shutil
import subprocess
from pathlib import Path

import pytest

GATEWAY = Path(__file__).resolve().parents[2] / "mcp-ai-gateway"
pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")

FAKE_NPM = """#!/bin/sh
echo "npm noise on stdout"
[ "$FAKE_NPM_FAILS" = "1" ] && exit 7
mkdir -p node_modules/@modelcontextprotocol/sdk
"""


def _fresh_install(tmp_path):
    """A plugin directory as an upgrade leaves it: launcher and dist, no node_modules."""
    shutil.copy(GATEWAY / "launch.mjs", tmp_path / "launch.mjs")
    (tmp_path / "package.json").write_text('{"type": "module"}')
    (tmp_path / "dist").mkdir()
    (tmp_path / "dist/index.js").write_text('console.error("server started");\n')
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    (fake_bin / "npm").write_text(FAKE_NPM)
    (fake_bin / "npm").chmod(0o755)
    return {**os.environ, "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}"}


def _launch(tmp_path, env):
    return subprocess.run(["node", str(tmp_path / "launch.mjs")], cwd="/", env=env,
                          capture_output=True, text=True, timeout=60)


def test_missing_dependencies_are_installed_and_stdout_stays_clean(tmp_path):
    env = _fresh_install(tmp_path)
    result = _launch(tmp_path, env)
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "node_modules/@modelcontextprotocol/sdk").is_dir()
    assert "server started" in result.stderr
    # stdout is the MCP channel: the installer's output must not reach it.
    assert result.stdout == ""
    assert "npm noise on stdout" in result.stderr

    again = _launch(tmp_path, {**env, "FAKE_NPM_FAILS": "1"})  # present now: npm is not run again
    assert again.returncode == 0 and "installing" not in again.stderr


def test_a_failed_install_says_what_to_run_and_does_not_start_the_server(tmp_path):
    env = _fresh_install(tmp_path)
    result = _launch(tmp_path, {**env, "FAKE_NPM_FAILS": "1"})
    assert result.returncode == 1
    assert "npm exited 7" in result.stderr and "npm install" in result.stderr
    assert "server started" not in result.stderr
    assert result.stdout == ""


def test_plugin_starts_the_gateway_through_the_launcher():
    mcp = (GATEWAY.parent / ".mcp.json").read_text(encoding="utf-8")
    assert "mcp-ai-gateway/launch.mjs" in mcp and "dist/index.js" not in mcp
