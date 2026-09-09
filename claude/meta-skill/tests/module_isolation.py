#!/usr/bin/env python3
"""Isolated loading of this plugin's orchestrator modules for the unit suite.

`claude/meta-skill/scripts/orchestrator/` and `shared/scripts/orchestrator/` both ship
`validate_bootstrap`, `check_artifacts`, `check_requires` and `loop_detection` with
deliberately different contracts. Importing them by bare name (after a `sys.path.insert`)
binds whichever host's file was collected first and leaves that binding behind for every
later suite, so a combined pytest run tests one host's module against the other's
expectations.

The loader itself is owned by `shared/scripts/orchestrator/_module_isolation.py`; this
module only binds the plugin's own script directory to it, so there is one implementation
of the isolation rule rather than a copy per host. Tests are only ever run from a repo
checkout, never from the installed plugin cache.
"""
from __future__ import annotations

import contextlib
import importlib.util
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_LOADER = _REPO / "shared/scripts/orchestrator/_module_isolation.py"
ORCHESTRATOR = str(Path(__file__).resolve().parents[1] / "scripts/orchestrator")

if not _LOADER.is_file():
    raise ModuleNotFoundError(
        f"test module loader missing: {_LOADER}. Run the meta-skill unit suite from a "
        "repo checkout, where shared/scripts/orchestrator/ is present."
    )

_spec = importlib.util.spec_from_file_location("_meta_skill_module_isolation", _LOADER)
_isolation = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_isolation)

__all__ = ["bound", "load", "ORCHESTRATOR"]


def load(*names: str):
    """Import `names` from this plugin's orchestrator directory, binding no global name.

    Modules that must agree on shared state have to be requested in one call.
    """
    return _isolation.load(ORCHESTRATOR, *names)


@contextlib.contextmanager
def bound(directory: str = ORCHESTRATOR):
    """Bind `directory`'s bare module names for one scope; see the shared loader."""
    with _isolation.bound(directory):
        yield
