#!/usr/bin/env python3
"""Load production modules from one explicit directory, leaking no top-level names.

Several trees in this repo ship modules with identical basenames — `validate_bootstrap`,
`check_artifacts`, `check_requires`, `loop_detection`, ... — with deliberately different
contracts per host. A bare ``import validate_bootstrap`` therefore resolves to whichever
suite was collected first, so a combined pytest run silently tests one host's module
against another host's expectations.

``load()`` imports the requested modules out of a named directory and then removes every
top-level name that import created, restoring whatever was bound before. Nothing a suite
imports through this helper can be inherited by a later suite, in either collection order.

Modules are memoised per (directory, name) so repeated loads inside one process hand back
the same object — classes and exception types stay comparable across test modules — while
sys.modules stays clean between loads.
"""
from __future__ import annotations

import contextlib
import importlib
import os
import sys

__all__ = ["bound", "load", "module_dir"]

_CACHE: dict[tuple[str, str], object] = {}


def module_dir(*parts: str) -> str:
    """Absolute directory built relative to this file's directory."""
    return os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), *parts))


def _owned_by(directory: str) -> set[str]:
    """Top-level names this directory can bind."""
    names = set()
    for entry in os.listdir(directory):
        full = os.path.join(directory, entry)
        if entry.endswith(".py") and os.path.isfile(full):
            names.add(entry[:-3])
        elif os.path.isfile(os.path.join(full, "__init__.py")):
            names.add(entry)
    names.discard("__init__")
    return names


def _from_directory(name: str, directory: str) -> bool:
    module = sys.modules.get(name)
    origin = getattr(module, "__file__", None)
    if not origin:
        return False
    return os.path.realpath(origin).startswith(directory + os.sep)


def load(directory: str, *names: str):
    """Import `names` from `directory`; return one module, or a tuple for several.

    Callers that need several modules to agree on shared state must request them in a
    single call.
    """
    if not names:
        raise ValueError("load() needs at least one module name")
    directory = os.path.realpath(directory)
    if not os.path.isdir(directory):
        raise FileNotFoundError(directory)

    owned = _owned_by(directory)
    unknown = [n for n in names if n not in owned]
    if unknown:
        raise ModuleNotFoundError(f"{unknown} not found in {directory}")

    # Step aside from whatever the process already bound under these names.
    shadowed = {n: sys.modules.pop(n) for n in owned if n in sys.modules}
    saved_path = list(sys.path)
    sys.path.insert(0, directory)
    # Re-seed this directory's own previously loaded modules so intra-directory
    # imports reuse them instead of building a second copy.
    sys.modules.update({n: m for (d, n), m in _CACHE.items() if d == directory})
    try:
        loaded = tuple(importlib.import_module(n) for n in names)
        _CACHE.update(
            {(directory, n): m for n, m in sys.modules.items() if _from_directory(n, directory)}
        )
    finally:
        sys.path[:] = saved_path
        for name in [n for n in list(sys.modules) if _from_directory(n, directory)]:
            del sys.modules[name]
        sys.modules.update(shadowed)

    return loaded[0] if len(loaded) == 1 else loaded


@contextlib.contextmanager
def bound(directory: str):
    """Make `directory` the only resolution for its bare module names, for one scope.

    Production modules in these trees import siblings by bare name inside functions
    (`from check_artifacts import freshness_states`), so the directory has to be resolvable
    while their code runs, not only while it is first imported. Binding it per test keeps
    that window closed between tests, so no suite can inherit another host's module.
    """
    directory = os.path.realpath(directory)
    bindings = {n: m for (d, n), m in _CACHE.items() if d == directory}
    # A sibling may not have been loaded into our cache yet. Remove every owned
    # name so a deferred import cannot inherit another suite's uncached sibling.
    owned = _owned_by(directory)
    shadowed = {n: sys.modules.pop(n) for n in owned if n in sys.modules}
    saved_path = list(sys.path)
    sys.path.insert(0, directory)
    sys.modules.update(bindings)
    try:
        yield
    finally:
        sys.path[:] = saved_path
        _CACHE.update({(directory, n): m for n, m in sys.modules.items()
                       if _from_directory(n, directory)})
        for name in [n for n in list(sys.modules) if _from_directory(n, directory)]:
            del sys.modules[name]
        sys.modules.update(shadowed)
