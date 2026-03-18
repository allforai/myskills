#!/usr/bin/env python3
"""Tests for cr_merge_screens.py."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cr_merge_screens import merge_screens


class TestMergeScreens(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.base_path = os.path.join(self.tmpdir, "project")
        self.fragments_dir = os.path.join(self.tmpdir, "fragments")
        os.makedirs(os.path.join(self.fragments_dir, "screens"), exist_ok=True)

    def _write_fragment(self, name, data):
        path = os.path.join(self.fragments_dir, "screens", name)
        with open(path, "w") as f:
            json.dump(data, f)

    def _read_output(self):
        path = os.path.join(self.base_path, ".allforai", "experience-map", "experience-map.json")
        with open(path) as f:
            return json.load(f)

    def _make_screen(self, page="Login Page", route="/login", route_group="Auth",
                     actions=None, states=None, data_fields=None):
        return {
            "page": page, "route": route, "route_group": route_group,
            "actions": actions or [{"name": "submit_login", "trigger": "form_submit"}],
            "states": states or [{"name": "loading", "condition": "api_call_pending"}],
            "data_fields": data_fields or ["email", "password"],
        }

    def test_basic_merge(self):
        self._write_fragment("mod1.json", {
            "screens": [self._make_screen(page="Login Page", route="/login", route_group="Auth")]
        })
        self._write_fragment("mod2.json", {
            "screens": [self._make_screen(page="Dashboard", route="/dashboard", route_group="Main")]
        })
        merge_screens(self.base_path, self.fragments_dir)
        out = self._read_output()

        self.assertEqual(out["source"], "code-replicate")
        self.assertEqual(out["fidelity"], "stub")
        self.assertIn("generated_at", out)
        self.assertEqual(len(out["operation_lines"]), 2)

    def test_hierarchy_structure(self):
        """Verify 3-layer hierarchy: operation_lines > nodes > screens."""
        self._write_fragment("mod.json", {
            "screens": [
                self._make_screen(page="Login", route="/login", route_group="Auth"),
                self._make_screen(page="Register", route="/register", route_group="Auth"),
                self._make_screen(page="Dashboard", route="/dashboard", route_group="Main"),
            ]
        })
        merge_screens(self.base_path, self.fragments_dir)
        out = self._read_output()

        self.assertEqual(len(out["operation_lines"]), 2)

        auth_ol = out["operation_lines"][0]
        self.assertEqual(auth_ol["name"], "Auth")
        self.assertTrue(auth_ol["id"].startswith("OL"))
        self.assertEqual(len(auth_ol["nodes"]), 2)

        login_node = auth_ol["nodes"][0]
        self.assertEqual(login_node["name"], "Login")
        self.assertEqual(login_node["route"], "/login")
        self.assertTrue(login_node["id"].startswith("N"))
        self.assertEqual(len(login_node["screens"]), 1)
        self.assertTrue(login_node["screens"][0]["id"].startswith("S"))

    def test_id_assignment(self):
        self._write_fragment("mod.json", {
            "screens": [
                self._make_screen(page="A", route="/a", route_group="G1"),
                self._make_screen(page="B", route="/b", route_group="G1"),
                self._make_screen(page="C", route="/c", route_group="G2"),
            ]
        })
        merge_screens(self.base_path, self.fragments_dir)
        out = self._read_output()

        self.assertEqual(out["operation_lines"][0]["id"], "OL001")
        self.assertEqual(out["operation_lines"][1]["id"], "OL002")
        # Screens get global sequential IDs
        all_screens = []
        for ol in out["operation_lines"]:
            for node in ol["nodes"]:
                all_screens.extend(node["screens"])
        ids = [s["id"] for s in all_screens]
        self.assertEqual(ids, ["S001", "S002", "S003"])

    def test_screen_data_preserved(self):
        actions = [{"name": "click_btn", "trigger": "click"}]
        states = [{"name": "idle", "condition": "default"}]
        fields = ["username", "email"]
        self._write_fragment("mod.json", {
            "screens": [self._make_screen(actions=actions, states=states, data_fields=fields)]
        })
        merge_screens(self.base_path, self.fragments_dir)
        out = self._read_output()

        scr = out["operation_lines"][0]["nodes"][0]["screens"][0]
        self.assertEqual(scr["actions"], actions)
        self.assertEqual(scr["states"], states)
        self.assertEqual(scr["data_fields"], fields)

    def test_no_design_fields(self):
        """Stub should NOT contain design-side fields."""
        self._write_fragment("mod.json", {
            "screens": [self._make_screen()]
        })
        merge_screens(self.base_path, self.fragments_dir)
        out = self._read_output()

        scr = out["operation_lines"][0]["nodes"][0]["screens"][0]
        for field in ("emotion_design", "ux_intent", "non_negotiable", "continuity"):
            self.assertNotIn(field, scr)

    def test_empty_fragments_dir(self):
        merge_screens(self.base_path, self.fragments_dir)
        out = self._read_output()
        self.assertEqual(out["operation_lines"], [])

    def test_output_path_correct(self):
        self._write_fragment("mod.json", {"screens": [self._make_screen()]})
        result_path = merge_screens(self.base_path, self.fragments_dir)
        expected = os.path.join(self.base_path, ".allforai", "experience-map", "experience-map.json")
        self.assertEqual(result_path, expected)
        self.assertTrue(os.path.exists(expected))

    def test_default_route_group(self):
        """Screen without route_group should use 'General'."""
        scr = self._make_screen()
        del scr["route_group"]
        self._write_fragment("mod.json", {"screens": [scr]})
        merge_screens(self.base_path, self.fragments_dir)
        out = self._read_output()
        self.assertEqual(out["operation_lines"][0]["name"], "General")

    def test_multiple_screens_same_page(self):
        """Multiple screen entries for the same page should appear as multiple screens under one node."""
        self._write_fragment("mod.json", {
            "screens": [
                self._make_screen(page="Login", route="/login", route_group="Auth",
                                  data_fields=["email"]),
                self._make_screen(page="Login", route="/login", route_group="Auth",
                                  data_fields=["password"]),
            ]
        })
        merge_screens(self.base_path, self.fragments_dir)
        out = self._read_output()

        auth_ol = out["operation_lines"][0]
        self.assertEqual(len(auth_ol["nodes"]), 1)  # single node for "Login"
        self.assertEqual(len(auth_ol["nodes"][0]["screens"]), 2)  # 2 screens

    def test_nonexistent_screens_subdir(self):
        import shutil
        shutil.rmtree(os.path.join(self.fragments_dir, "screens"))
        merge_screens(self.base_path, self.fragments_dir)
        out = self._read_output()
        self.assertEqual(out["operation_lines"], [])


if __name__ == "__main__":
    unittest.main()
