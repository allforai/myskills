"""Bind this directory's orchestrator modules for the duration of each test.

`load()` in `_module_isolation` keeps the bare names out of `sys.modules` between tests, but
the modules under test import their own siblings by bare name at call time. This fixture
opens that resolution only while a test from this directory runs, so a suite that shares a
module basename with another host (`validate_bootstrap`, `check_artifacts`, ...) can never
pick up the other host's file.
"""
import pytest

from _module_isolation import bound, module_dir


@pytest.fixture(autouse=True)
def shared_orchestrator_modules():
    with bound(module_dir()):
        yield
