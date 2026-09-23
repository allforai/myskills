"""The clause registry reddens on drift, and only on drift (ADR-0010 criterion 4)."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_clauses  # noqa: E402

AUTHORITY = 'intro\n<!-- clause-begin:demo -->\nthe rule says X\n<!-- clause-end:demo -->\noutro\n'


def write(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')
    return path


def registry(copies=(), forbid=(), require=('the rule says X',)):
    return {'scan_roots': ['src'], 'clauses': [{
        'id': 'demo', 'rule': 'every copy says X',
        'authority': {'path': 'src/authority.md', 'require': list(require)},
        'copies': list(copies), 'forbid': list(forbid)}]}


def stamped(root, reg, body):
    return f"{check_clauses.stamp(root, reg['clauses'][0])}\n{body}"


def test_matching_copies_hold(tmp_path):
    write(tmp_path, 'src/authority.md', AUTHORITY)
    reg = registry(copies=[{'path': 'src/copy.md', 'require': ['the rule says X']}])
    write(tmp_path, 'src/copy.md', stamped(tmp_path, reg, 'the rule says X'))
    assert check_clauses.violations(tmp_path, reg) == []


def test_a_token_rewrapped_across_lines_still_holds(tmp_path):
    write(tmp_path, 'src/authority.md', AUTHORITY.replace('the rule says X', 'the rule\n   says X'))
    assert check_clauses.violations(tmp_path, registry()) == []


def test_an_authority_edit_reddens_every_copy_until_restamped(tmp_path):
    # Replay of 85776b36 / 98aa98e9: the rule moves at its authority, the copies keep every
    # phrase they had. Phrases alone would pass; the stale stamp is what goes red.
    write(tmp_path, 'src/authority.md', AUTHORITY)
    reg = registry(copies=[{'path': 'src/a.md', 'require': ['the rule says X']},
                           {'path': 'src/b.md', 'exempt': 'host does it natively'}])
    old = check_clauses.stamp(tmp_path, reg['clauses'][0])
    write(tmp_path, 'src/a.md', f'{old}\nthe rule says X')
    write(tmp_path, 'src/b.md', old)
    write(tmp_path, 'src/authority.md', AUTHORITY.replace('says X', 'says X, and also Y'))
    new = check_clauses.stamp(tmp_path, reg['clauses'][0])
    assert new != old
    found = check_clauses.violations(tmp_path, reg)
    assert found == [
        f'demo: src/a.md was stamped {old.split("@")[1]} but the authority is now {new.split("@")[1]}: '
        'reread src/authority.md clause-begin:demo, bring this copy in line, then restamp it',
        f'demo: src/b.md was stamped {old.split("@")[1]} but the authority is now {new.split("@")[1]}: '
        'reread src/authority.md clause-begin:demo, bring this copy in line, then restamp it']
    write(tmp_path, 'src/a.md', f'{new}\nthe rule says X, and also Y')
    write(tmp_path, 'src/b.md', new)
    assert check_clauses.violations(tmp_path, reg) == []


def test_a_copy_without_a_stamp_is_named(tmp_path):
    write(tmp_path, 'src/authority.md', AUTHORITY)
    write(tmp_path, 'src/copy.md', 'the rule says X')
    reg = registry(copies=[{'path': 'src/copy.md', 'require': ['the rule says X']}])
    assert check_clauses.violations(tmp_path, reg) == [
        f"demo: src/copy.md has no {check_clauses.stamp(tmp_path, reg['clauses'][0])} stamp"]


def test_an_unmarked_authority_is_named(tmp_path):
    write(tmp_path, 'src/authority.md', 'the rule says X')
    assert check_clauses.violations(tmp_path, registry()) == [
        'demo: src/authority.md has no clause-begin:demo … clause-end:demo section']


def test_an_authority_phrase_must_sit_inside_its_section(tmp_path):
    write(tmp_path, 'src/authority.md', AUTHORITY + 'stray phrase\n')
    assert check_clauses.violations(tmp_path, registry(require=['stray phrase'])) == [
        "demo: src/authority.md no longer says 'stray phrase'"]


def test_a_copy_that_stopped_saying_it_is_named(tmp_path):
    write(tmp_path, 'src/authority.md', AUTHORITY)
    reg = registry(copies=[{'path': 'src/copy.md', 'require': ['the rule says X']}])
    write(tmp_path, 'src/copy.md', stamped(tmp_path, reg, 'the rule says Y'))
    assert check_clauses.violations(tmp_path, reg) == [
        "demo: src/copy.md no longer says 'the rule says X'"]


def test_a_missing_copy_is_unchecked_not_passed(tmp_path):
    write(tmp_path, 'src/authority.md', AUTHORITY)
    reg = registry(copies=[{'path': 'src/moved.md', 'require': ['the rule says X']}])
    assert check_clauses.violations(tmp_path, reg) == [
        'demo: src/moved.md does not exist — unchecked, not passed']


def test_an_exemption_needs_a_reason(tmp_path):
    write(tmp_path, 'src/authority.md', AUTHORITY)
    reg = registry(copies=[{'path': 'src/a.md', 'exempt': 'host does it natively'},
                           {'path': 'src/b.md', 'exempt': '  '}])
    write(tmp_path, 'src/a.md', stamped(tmp_path, reg, ''))
    write(tmp_path, 'src/b.md', stamped(tmp_path, reg, ''))
    assert check_clauses.violations(tmp_path, reg) == [
        'demo: src/b.md is exempt with no reason']


def test_a_copy_with_neither_require_nor_exempt_is_malformed(tmp_path):
    write(tmp_path, 'src/authority.md', AUTHORITY)
    reg = registry(copies=[{'path': 'src/copy.md'}])
    write(tmp_path, 'src/copy.md', stamped(tmp_path, reg, 'anything'))
    assert check_clauses.violations(tmp_path, reg) == [
        'demo: src/copy.md has neither a non-empty require list nor an exempt reason']


def test_a_retired_phrase_is_reported_where_it_survives(tmp_path):
    write(tmp_path, 'src/authority.md', AUTHORITY)
    write(tmp_path, 'src/deep/old.md', 'as before, the old\nwording stays')
    assert check_clauses.violations(tmp_path, registry(forbid=['the old wording'])) == [
        "demo: src/deep/old.md still says retired 'the old wording'"]


def test_forbidden_phrases_skip_symlinks_and_the_excluded_dir(tmp_path):
    write(tmp_path, 'src/authority.md', AUTHORITY)
    real = write(tmp_path, 'src/real/old.md', 'the old wording')
    os.symlink(real, tmp_path / 'src/link.md')
    os.symlink(tmp_path / 'src/real', tmp_path / 'src/linked-dir')
    write(tmp_path, 'src/registry/clauses.json', '"the old wording"')
    write(tmp_path, 'src/node_modules/pkg/readme.md', 'the old wording')
    found = check_clauses.violations(tmp_path, registry(forbid=['the old wording']),
                                     exclude=(tmp_path / 'src/registry',))
    assert found == ["demo: src/real/old.md still says retired 'the old wording'"]


def test_hashes_prints_each_clause_stamp(capsys):
    assert check_clauses.main(['--hashes']) == 0
    printed = capsys.readouterr().out.split()
    assert printed == [check_clauses.stamp(check_clauses.ROOT, c) or f"{c['id']}: unmarked"
                       for c in check_clauses.load_registry()['clauses']]


def test_the_repository_registry_holds():
    found = check_clauses.violations(check_clauses.ROOT, check_clauses.load_registry(),
                                     exclude=(check_clauses.REGISTRY.parent,))
    assert found == [], '\n'.join(found)
    assert check_clauses.main([]) == 0
