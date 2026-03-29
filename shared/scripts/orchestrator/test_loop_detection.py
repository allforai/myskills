#!/usr/bin/env python3
"""Tests for loop_detection.py."""

import json
import os
import tempfile
import shutil
import unittest

from loop_detection import check_loop, record_iteration


class TestLoopDetection(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.history_path = os.path.join(self.tmpdir, "loop_history.json")

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_no_loop_on_first(self):
        result = record_iteration(self.history_path, "node-a", [True, False])
        self.assertEqual(result["status"], "ok")

    def test_no_loop_different_nodes(self):
        for node in ["a", "b", "c"]:
            result = record_iteration(self.history_path, node, [True])
        self.assertEqual(result["status"], "ok")

    def test_warn_at_threshold(self):
        for _ in range(3):
            result = record_iteration(self.history_path, "stuck", [False])
        self.assertEqual(result["status"], "warn")

    def test_stop_at_threshold(self):
        for _ in range(5):
            result = record_iteration(self.history_path, "stuck", [False])
        self.assertEqual(result["status"], "stop")

    def test_different_results_no_loop(self):
        record_iteration(self.history_path, "node-a", [True, False])
        record_iteration(self.history_path, "node-a", [True, True])
        result = record_iteration(self.history_path, "node-a", [False, True])
        self.assertEqual(result["status"], "ok")

    def test_custom_thresholds(self):
        for _ in range(2):
            result = record_iteration(
                self.history_path, "node", [False],
                warn_threshold=2, stop_threshold=4
            )
        self.assertEqual(result["status"], "warn")

    def test_sliding_window(self):
        # Fill window with unique entries
        for i in range(10):
            record_iteration(self.history_path, f"node-{i}", [True])
        # Now repeat one — should not trigger warn because old entries fell out
        result = record_iteration(self.history_path, "new-stuck", [False])
        self.assertEqual(result["status"], "ok")

    def test_check_loop_without_recording(self):
        # Pre-fill history
        for _ in range(3):
            record_iteration(self.history_path, "stuck", [False])
        status = check_loop(self.history_path, "stuck", [False])
        self.assertEqual(status, "warn")


if __name__ == "__main__":
    unittest.main()
