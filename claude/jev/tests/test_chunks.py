import json
import subprocess

import pytest

import code_chunks as K
import jev_config as C

TEN = "".join(f"line {i}\n" for i in range(1, 11))


def test_by_file():
    assert K.by_file(TEN) == [(1, 10)]
    assert K.by_file("") == []


def test_by_window_overlaps_and_covers_end():
    assert K.by_window(TEN, lines=4, overlap=1) == [(1, 4), (4, 7), (7, 10)]
    assert K.by_window("a\nb\n", lines=4, overlap=1) == [(1, 2)]


def test_by_grep_merges_overlapping_context():
    text = "".join(("SECRET\n" if i in (3, 5, 10) else "x\n") for i in range(1, 13))
    assert K.by_grep(text, "SECRET", context=1) == [(2, 6), (9, 11)]
    assert K.by_grep(text, "nothing", context=1) == []


DIFF = """diff --git a/src/a.py b/src/a.py
--- a/src/a.py
+++ b/src/a.py
@@ -1,3 +1,4 @@
 one
+two
 three
@@ -10 +11,0 @@
-gone
diff --git a/old.py b/old.py
--- a/old.py
+++ /dev/null
@@ -1 +0,0 @@
-x
"""


def test_parse_diff_new_side_ranges():
    hunks = K.parse_diff(DIFF)
    assert [(p, s, e) for p, s, e, _ in hunks] == [("src/a.py", 1, 4), ("src/a.py", 11, 11)]
    assert "+two" in hunks[0][3]


def test_make_row_id_and_header():
    row = K.make_row("src/a.py", 3, 7, "body")
    assert row["id"] == "src/a.py:3-7" and row["state"].startswith("# src/a.py (lines 3-7)\n")


@pytest.fixture
def repo(git_repo, cfg_dir):
    (git_repo / "a.py").write_text(TEN)
    (git_repo / "bin.dat").write_bytes(b"\x00\x01\x02")
    (git_repo / "big.txt").write_text("x" * 5000)
    subprocess.run(["git", "-C", str(git_repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(git_repo), "commit", "-qm", "init"], check=True)
    (git_repo / "untracked.py").write_text("SECRET\n")
    C.write_json(cfg_dir / "allow.json", {"paths": [str(git_repo)]})
    return git_repo


def rows_of(out):
    return [json.loads(l) for l in out.read_text().splitlines()]


def test_main_by_file_skips_binary_big_and_untracked(repo, tmp_path):
    out = tmp_path / "chunks.jsonl"
    assert K.main(["--root", str(repo), "--by", "file", "--max-bytes", "1000", "--out", str(out)]) == 0
    assert [r["id"] for r in rows_of(out)] == ["a.py:1-10"]


def test_main_by_hunk(repo, tmp_path):
    (repo / "a.py").write_text(TEN.replace("line 5\n", "line 5 changed\n"))
    out = tmp_path / "chunks.jsonl"
    assert K.main(["--root", str(repo), "--by", "hunk", "--base", "HEAD", "--context", "1", "--out", str(out)]) == 0
    assert [r["id"] for r in rows_of(out)] == ["a.py:4-6"]


def test_main_refuses_root_outside_allowlist(git_repo, tmp_path):
    assert K.main(["--root", str(git_repo), "--by", "file", "--out", str(tmp_path / "o.jsonl")]) == 3
    assert not (tmp_path / "o.jsonl").exists()
