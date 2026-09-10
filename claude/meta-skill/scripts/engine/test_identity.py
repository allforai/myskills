"""Whole-tree build identity: two different uncommitted states on one commit never share a build."""
import os
import subprocess

import pytest
from identity import build_identity, build_reason


def _git(repo, *args):
    env = {**os.environ, 'GIT_AUTHOR_NAME': 'a', 'GIT_AUTHOR_EMAIL': 'a@b',
           'GIT_COMMITTER_NAME': 'a', 'GIT_COMMITTER_EMAIL': 'a@b'}
    return subprocess.run(['git', '-C', str(repo), *args], check=True, capture_output=True, text=True,
                          env=env).stdout.strip()


@pytest.fixture
def repo(tmp_path):
    repo = tmp_path / 'target'
    repo.mkdir()
    (repo / 'app.py').write_text('print(1)\n')
    (repo / '.gitignore').write_text('dist/\n')
    _git(repo, 'init', '-q')
    _git(repo, 'add', '.')
    _git(repo, 'commit', '-q', '-m', 'one')
    return repo


def test_clean_tree_is_stable_and_names_the_commit(repo):
    first, second = build_identity(repo), build_identity(repo)
    assert first['reason'] == '' and first == second
    head = _git(repo, 'rev-parse', 'HEAD')
    assert first['commit'] == head
    assert first['build'].startswith(head + '-') and first['snapshot'] and first['artifact'] == ''


def test_two_uncommitted_states_on_one_commit_differ(repo):
    clean = build_identity(repo)
    (repo / 'app.py').write_text('print(2)\n')
    edited = build_identity(repo)
    (repo / 'app.py').write_text('print(3)\n')
    edited_again = build_identity(repo)
    assert clean['commit'] == edited['commit'] == edited_again['commit']
    assert len({clean['build'], edited['build'], edited_again['build']}) == 3


def test_staged_and_unstaged_edits_both_count(repo):
    clean = build_identity(repo)
    (repo / 'app.py').write_text('print(2)\n')
    _git(repo, 'add', 'app.py')
    assert build_identity(repo)['build'] != clean['build']


def test_untracked_file_content_is_part_of_the_snapshot(repo):
    clean = build_identity(repo)
    (repo / 'new.py').write_text('a')
    with_new = build_identity(repo)
    (repo / 'new.py').write_text('b')
    with_new_edited = build_identity(repo)
    assert len({clean['build'], with_new['build'], with_new_edited['build']}) == 3


def test_ignored_files_are_not_in_the_snapshot_but_named_artifacts_are(repo):
    clean = build_identity(repo)
    dist = repo / 'dist'
    dist.mkdir()
    (dist / 'bundle.js').write_text('v1')
    assert build_identity(repo)['build'] == clean['build']          # dist/ is gitignored
    v1 = build_identity(repo, artifacts=[dist])
    (dist / 'bundle.js').write_text('v2')
    v2 = build_identity(repo, artifacts=[dist])
    assert v1['build'] != clean['build'] and v1['build'] != v2['build']
    assert v1['artifact'] and v1['artifact'] != v2['artifact']
    assert v1['snapshot'] == clean['snapshot']                       # the tree itself did not change


def test_commit_changes_the_identity(repo):
    before = build_identity(repo)
    (repo / 'app.py').write_text('print(2)\n')
    _git(repo, 'commit', '-q', '-am', 'two')
    after = build_identity(repo)
    assert before['commit'] != after['commit'] and before['build'] != after['build']
    assert after['snapshot'] == before['snapshot']                   # both trees are clean


def test_refusals_are_reasons_not_exceptions(tmp_path, repo):
    plain = tmp_path / 'plain'
    plain.mkdir()
    out = build_identity(plain)
    assert out['build'] == '' and '不是 git 仓库' in out['reason']
    missing = build_identity(repo, artifacts=[repo / 'dist'])
    assert missing['build'] == '' and '构建产物不存在' in missing['reason'] and 'dist' in missing['reason']
    assert build_identity(tmp_path / 'nowhere')['build'] == ''


def test_build_reason_compares_a_recorded_value_with_the_tree(repo):
    recorded = build_identity(repo)['build']
    assert build_reason(recorded, repo) == ''
    (repo / 'app.py').write_text('print(2)\n')
    reason = build_reason(recorded, repo)
    assert '构建标识不匹配' in reason and recorded in reason
    assert '缺构建标识' in build_reason('', repo)
    assert '缺构建标识' in build_reason(None, repo)
    assert '不是 git 仓库' in build_reason(recorded, repo / 'nowhere')
