import json
import tempfile
import unittest
from pathlib import Path

from ledger_store import ActiveRunError, acquire_lock, release_lock, save_ledger


class LedgerStoreTests(unittest.TestCase):
    def test_lock_refuses_concurrent_examiner(self):
        with tempfile.TemporaryDirectory() as td:
            lock = acquire_lock(td)
            with self.assertRaises(ActiveRunError):
                acquire_lock(td)
            release_lock(td, lock["run_id"])

    def test_atomic_ledger_adds_ids_and_version(self):
        with tempfile.TemporaryDirectory() as td:
            ledger = {"target": "x", "baseline": "none", "facets": [],
                      "entries": [{"q": "q"}], "open_threads": [{"q": "t"}]}
            save_ledger(td, ledger)
            loaded = json.loads(Path(td, "ledger.json").read_text())
            self.assertEqual(loaded["schema_version"], 1)
            self.assertTrue(loaded["entries"][0]["id"])
            self.assertTrue(loaded["open_threads"][0]["id"])

    def test_stale_lock_requires_explicit_takeover(self):
        with tempfile.TemporaryDirectory() as td:
            Path(td, ".examiner.lock").write_text(json.dumps(
                {"run_id": "old", "pid": 99999999, "process_start": "gone"}))
            with self.assertRaises(ActiveRunError):
                acquire_lock(td)
            lock = acquire_lock(td, confirm_stale=True)
            self.assertTrue(list(Path(td).glob(".examiner.lock.stale-*")))
            release_lock(td, lock["run_id"])

    def test_conflicting_duplicate_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            ledger = {"entries": [{"id": "same", "q": "a"},
                                   {"id": "same", "q": "b"}]}
            with self.assertRaises(ValueError):
                save_ledger(td, ledger)


if __name__ == "__main__":
    unittest.main()
