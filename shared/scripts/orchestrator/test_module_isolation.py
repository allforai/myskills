#!/usr/bin/env python3
"""Regression: shared orchestrator tests never load another host's same-named module.

`shared/scripts/orchestrator/` and `claude/meta-skill/scripts/orchestrator/` both ship a
`validate_bootstrap` (and `check_artifacts`, `check_requires`, `loop_detection`) whose
contracts differ on purpose. Before this suite, both trees reached their module through a
bare top-level import, so a combined pytest run bound whichever host was collected first
and then tested it against the other host's expectations — failing in one order and
erroring during collection in the other.

These tests pin the isolation rule itself, the two production contracts that must stay
distinct, and the combined-collection behaviour in both orders.
"""
import os
from pathlib import Path as _Path
import subprocess
import sys
import tempfile
import unittest

from _module_isolation import bound, load, module_dir

SHARED = module_dir()
REPO = os.path.realpath(os.path.join(SHARED, "..", "..", ".."))
CLAUDE = os.path.join(REPO, "claude/meta-skill/scripts/orchestrator")
SHARED_TEST = os.path.join(SHARED, "test_validate_bootstrap.py")
CLAUDE_TEST = os.path.join(REPO, "claude/meta-skill/tests/unit/test_validate_bootstrap.py")

CONTAMINABLE = ("validate_bootstrap", "check_artifacts", "check_requires", "loop_detection")


class TestSharedLoadsItsOwnModule(unittest.TestCase):
    def test_validate_bootstrap_comes_from_the_shared_tree(self):
        module = load(SHARED, "validate_bootstrap")
        self.assertEqual(
            os.path.realpath(module.__file__),
            os.path.join(SHARED, "validate_bootstrap.py"),
        )

    def test_every_bare_name_visible_here_belongs_to_this_directory(self):
        """Inside a shared test, the shared tree owns these names — nothing else may."""
        load(SHARED, "validate_bootstrap")
        for name in CONTAMINABLE:
            module = sys.modules.get(name)
            if module is None:
                continue
            self.assertTrue(
                os.path.realpath(module.__file__).startswith(SHARED + os.sep),
                f"{name} is bound to {module.__file__}, outside {SHARED}",
            )

    def test_a_foreign_binding_scope_leaves_nothing_behind(self):
        """What a later suite inherits: no name, no path entry, no other host's module."""
        if not os.path.isdir(CLAUDE):
            self.skipTest("claude meta-skill tree not present")
        load(CLAUDE, "validate_bootstrap")
        before_path = list(sys.path)
        before_modules = dict(sys.modules)
        with bound(CLAUDE):
            self.assertTrue(
                os.path.realpath(sys.modules["validate_bootstrap"].__file__).startswith(
                    CLAUDE + os.sep
                )
            )
        self.assertEqual(sys.path, before_path, "sys.path was mutated")
        self.assertEqual(
            {n for n in sys.modules if n not in before_modules}, set(),
            "a foreign binding scope leaked module names",
        )
        for name in CONTAMINABLE:
            module = sys.modules.get(name)
            if module is not None:
                self.assertFalse(
                    os.path.realpath(module.__file__).startswith(CLAUDE + os.sep),
                    f"{name} still resolves to the Claude tree after its scope closed",
                )

    def test_a_preloaded_foreign_module_cannot_capture_a_shared_load(self):
        """The exact combined-order failure: the Claude module already bound by name."""
        if not os.path.isdir(CLAUDE):
            self.skipTest("claude meta-skill tree not present")
        foreign = load(CLAUDE, "validate_bootstrap")
        sys.modules["validate_bootstrap"] = foreign
        try:
            module = load(SHARED, "validate_bootstrap")
            self.assertEqual(
                os.path.realpath(module.__file__),
                os.path.join(SHARED, "validate_bootstrap.py"),
            )
            self.assertIs(
                sys.modules["validate_bootstrap"], foreign,
                "an unrelated pre-existing binding must be restored, not rewritten",
            )
        finally:
            del sys.modules["validate_bootstrap"]


class TestHostContractsStayDistinct(unittest.TestCase):
    """Isolation must preserve the divergence, not paper over it.

    The shared validator is the portable minimum used by generated projects on either
    host: a node spec declares `node:`. The Claude plugin's validator additionally owns
    `node_id` and the attention contract. Neither expectation may be relaxed to make a
    combined run green.
    """

    def setUp(self):
        if not os.path.isdir(CLAUDE):
            self.skipTest("claude meta-skill tree not present")
        self.shared = load(SHARED, "validate_bootstrap")
        self.claude = load(CLAUDE, "validate_bootstrap")

    def _spec(self, body):
        handle, path = tempfile.mkstemp(suffix=".md")
        os.close(handle)
        self.addCleanup(os.unlink, path)
        with open(path, "w") as stream:
            stream.write(body)
        return path

    def test_the_two_validators_are_different_modules(self):
        self.assertIsNot(self.shared, self.claude)
        self.assertNotEqual(
            os.path.realpath(self.shared.__file__), os.path.realpath(self.claude.__file__)
        )

    def test_shared_accepts_the_portable_node_spec_the_claude_gate_rejects(self):
        path = self._spec("---\nnode: n1\n---\n\n# Task\nDo it.")
        self.assertEqual(self.shared.validate_node_spec(path), [])
        self.assertNotEqual(
            self.claude.validate_node_spec(path), [],
            "the Claude gate must keep its stricter node-spec contract",
        )

    def test_only_the_claude_validator_owns_the_game_production_contract(self):
        self.assertTrue(hasattr(self.claude, "GAME_2D_PRODUCTION_REQUIRED_NODES"))
        self.assertFalse(hasattr(self.shared, "GAME_2D_PRODUCTION_REQUIRED_NODES"))


class TestDeferredSiblingImports(unittest.TestCase):
    """Isolation has to survive the call, not only the initial import.

    `validate_unattended_readiness` imports `check_artifacts` inside its function body, and
    `check_artifacts` imports `evidence_freshness` inside three of its own. Restoring
    `sys.modules` after the initial import is therefore not enough: a suite that loaded the
    right module can still resolve a sibling out of the other host's tree at call time. The
    shared `check_artifacts` has no `document_verification_errors`, so a wrong binding here
    is an ImportError, not a subtly wrong answer.
    """

    def setUp(self):
        if not os.path.isdir(CLAUDE):
            self.skipTest("claude meta-skill tree not present")

    def test_the_shared_sibling_cannot_answer_a_claude_call(self):
        opposite = load(SHARED, "check_artifacts")
        self.assertFalse(
            hasattr(opposite, "document_verification_errors"),
            "the two check_artifacts modules are no longer distinguishable; "
            "re-point this regression at a name only one of them owns",
        )
        readiness = load(CLAUDE, "validate_unattended_readiness")
        saved = sys.modules.get("check_artifacts")
        sys.modules["check_artifacts"] = opposite
        try:
            with bound(CLAUDE):
                self.assertTrue(
                    os.path.realpath(sys.modules["check_artifacts"].__file__).startswith(
                        CLAUDE + os.sep
                    ),
                    "the scope must own the sibling name for the duration of the call",
                )
                with tempfile.TemporaryDirectory() as project:
                    report = readiness.validate_unattended_readiness(_Path(project))
            self.assertIsInstance(report, dict)
            self.assertIn("blockers", report)
        finally:
            if saved is None:
                sys.modules.pop("check_artifacts", None)
            else:
                sys.modules["check_artifacts"] = saved

    def test_the_scope_is_what_makes_the_deferred_import_resolve(self):
        """Negative control: without the scope the same call fails, so the scope is load-bearing."""
        opposite = load(SHARED, "check_artifacts")
        readiness = load(CLAUDE, "validate_unattended_readiness")
        saved = sys.modules.get("check_artifacts")
        sys.modules["check_artifacts"] = opposite
        try:
            with tempfile.TemporaryDirectory() as project:
                with self.assertRaises(ImportError) as caught:
                    readiness.validate_unattended_readiness(_Path(project))
            self.assertIn("document_verification_errors", str(caught.exception))
            self.assertIn(SHARED, str(caught.exception))
        finally:
            if saved is None:
                sys.modules.pop("check_artifacts", None)
            else:
                sys.modules["check_artifacts"] = saved


class TestCombinedCollectionOrder(unittest.TestCase):
    """Both same-named suites pass together, collected in either order."""

    def _run(self, first, second):
        return subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", first, second],
            cwd=REPO, capture_output=True, text=True,
        )

    def setUp(self):
        if not os.path.isfile(CLAUDE_TEST):
            self.skipTest("claude meta-skill unit suite not present")

    def test_claude_suite_first(self):
        done = self._run(CLAUDE_TEST, SHARED_TEST)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)

    def test_shared_suite_first(self):
        done = self._run(SHARED_TEST, CLAUDE_TEST)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)


if __name__ == "__main__":
    unittest.main()
