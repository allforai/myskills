"""Bind this plugin's orchestrator modules for the duration of each unit test.

`module_isolation.load()` keeps the bare names out of `sys.modules` between tests, but the
validators import their own siblings by bare name at call time
(`from check_artifacts import freshness_states`). This fixture opens that resolution only
while a test from this suite runs, so the shared orchestrator tree's same-named modules can
never answer a call from this one, in either collection order.
"""
import pytest

from .module_isolation import ORCHESTRATOR, bound


@pytest.fixture(autouse=True)
def meta_skill_orchestrator_modules():
    with bound(ORCHESTRATOR):
        yield
