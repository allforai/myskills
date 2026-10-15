import json
import os

import pytest

import jev_config as C


def test_defaults_when_no_config_file():
    cfg = C.load_config()
    assert cfg["model"] == "~typesafe/jev-latest"
    assert cfg["route"]["threshold"] == 0.8
    assert cfg["route"]["assume_model"] is None
    assert cfg["batch"]["cost_cap_usd"] == 1.0


def test_override_keeps_sibling_defaults(cfg_dir):
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "config.json").write_text(json.dumps({"route": {"threshold": 0.5}}))
    cfg = C.load_config()
    assert cfg["route"]["threshold"] == 0.5
    assert cfg["route"]["timeout_s"] == 3.0


def test_malformed_config_raises_with_path(cfg_dir):
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "config.json").write_text("{not json")
    with pytest.raises(C.ConfigError, match="config.json"):
        C.load_config()


def test_project_root_of_subdir_is_repo_root(git_repo):
    sub = git_repo / "a" / "b"
    sub.mkdir(parents=True)
    assert C.project_root(str(sub)) == os.path.realpath(git_repo)


def test_project_root_via_symlink_is_same_project(git_repo, tmp_path):
    link = tmp_path / "link"
    link.symlink_to(git_repo)
    assert C.project_root(str(link)) == os.path.realpath(git_repo)


def test_project_root_outside_git_is_cwd(tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()
    assert C.project_root(str(plain)) == os.path.realpath(plain)


def test_switch_is_per_project(tmp_path):
    a, b = str(tmp_path / "a"), str(tmp_path / "b")
    C.set_route(a, True)
    assert C.is_route_on(a) and not C.is_route_on(b)
    C.set_route(a, False)
    assert not C.is_route_on(a)


def test_allowlist_matches_prefix_not_sibling(cfg_dir, tmp_path):
    data = tmp_path / "data"
    (data / "x").mkdir(parents=True)
    (tmp_path / "data2").mkdir()
    assert not C.is_allowed(str(data / "x"))
    C.write_json(cfg_dir / "allow.json", {"paths": [str(data)]})
    assert C.is_allowed(str(data / "x" / "rows.jsonl"))
    assert C.is_allowed(str(data))
    assert not C.is_allowed(str(tmp_path / "data2" / "rows.jsonl"))


def test_append_route_log_appends_lines():
    C.append_route_log({"a": 1})
    C.append_route_log({"b": "中"})
    assert [json.loads(l) for l in C.log_path().read_text(encoding="utf-8").splitlines()] == [{"a": 1}, {"b": "中"}]


def test_transcript_dir_encodes_project_path(tmp_path):
    assert C.transcript_dir("/Users/aa/workspace/my.skills") == tmp_path / "claude" / "projects" / "-Users-aa-workspace-my-skills"
