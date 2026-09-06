"""Exercise installation without touching real skills or calling npm."""
import importlib.util
import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('meta_installer', ROOT / 'install_bundle.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


@pytest.fixture
def layout(tmp_path, monkeypatch):
    source = tmp_path / 'repo/codex/meta-skill'
    canonical = tmp_path / 'repo/claude/meta-skill'
    for relative, data in {
        'SKILL.md':'---\nname: meta-skill\ndescription: test\n---\nProtocol',
        'AGENTS.md':'instructions', 'knowledge/flow-template.py':'pass',
        'agents/openai.yaml':'policy:\n  allow_implicit_invocation: false\n',
    }.items():
        path = source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data)
    (canonical / 'skills/bootstrap').mkdir(parents=True)
    (canonical / 'skills/bootstrap/SKILL.md').write_text('canonical bootstrap')
    (canonical / 'knowledge').mkdir()
    monkeypatch.setenv('SOURCE_COMMIT', 'fixture')
    entry = tmp_path / 'home with spaces/skills/meta-skill'
    bundle = tmp_path / 'home with spaces/skill-bundles/meta-skill'
    return source, entry, bundle


def test_update_removes_stale_entries_and_preserves_policy(layout):
    source, entry, bundle = layout
    installer.install(*layout)
    (entry / 'canonical/old').mkdir(parents=True)
    (entry / 'canonical/old/SKILL.md').write_text('obsolete')
    (bundle / 'stale.txt').write_text('obsolete')
    installer.install(*layout)
    assert list(entry.parent.rglob('SKILL.md')) == [entry / 'SKILL.md']
    assert (bundle / 'canonical/skills/bootstrap/SKILL.md').is_file()
    assert not (bundle / 'stale.txt').exists()
    assert (entry / 'agents/openai.yaml').read_bytes() == (source / 'agents/openai.yaml').read_bytes()
    assert not list(bundle.parent.glob('.meta-stage-*'))
    assert not list(entry.parent.parent.glob('.meta-entry-*'))


def test_migrate_source_symlink_without_deleting_source(layout):
    source, entry, bundle = layout
    entry.parent.mkdir(parents=True)
    entry.symlink_to(source, target_is_directory=True)
    installer.install(*layout)
    assert not entry.is_symlink()
    assert (source / 'SKILL.md').is_file()
    assert len(list(entry.rglob('SKILL.md'))) == 1


def test_build_failure_preserves_existing_install(layout):
    source, entry, bundle = layout
    installer.install(*layout)
    previous = (entry / 'SKILL.md').read_bytes()
    (source / 'knowledge/flow-template.py').write_text('invalid python !')
    with pytest.raises(SyntaxError):
        installer.install(*layout)
    assert (entry / 'SKILL.md').read_bytes() == previous
    assert (bundle / 'knowledge/flow-template.py').read_text() == 'pass'


def test_promotion_failure_rolls_back(layout, monkeypatch):
    source, entry, bundle = layout
    installer.install(*layout)
    old_entry = (entry / 'SKILL.md').read_bytes()
    old_bundle = (bundle / 'SKILL.md').read_bytes()
    rename = Path.rename
    def failing_rename(path, target):
        if path.name == 'entry':
            raise OSError('simulated promotion failure')
        return rename(path, target)
    monkeypatch.setattr(Path, 'rename', failing_rename)
    with pytest.raises(OSError):
        installer.install(*layout)
    assert (entry / 'SKILL.md').read_bytes() == old_entry
    assert (bundle / 'SKILL.md').read_bytes() == old_bundle


def test_reject_bundle_in_scan_root(layout):
    source, entry, bundle = layout
    with pytest.raises(ValueError):
        installer.install(source, entry, entry.parent / 'skill-bundles/meta-skill')
    assert not entry.exists()


def test_reject_source_as_target(layout):
    source, entry, bundle = layout
    with pytest.raises(ValueError):
        installer.install(source, source, bundle)
    assert (source / 'SKILL.md').is_file()


def test_aggregate_installer_uses_split_layout(layout):
    source, entry, bundle = layout
    for name in ('install.sh', 'install_bundle.py'):
        (source / name).write_bytes((ROOT / name).read_bytes())
    aggregate = source.parent / 'install.sh'
    aggregate.write_bytes((ROOT.parent / 'install.sh').read_bytes())
    result = subprocess.run(['bash', str(aggregate)], capture_output=True, text=True,
        env={**os.environ, 'CODEX_HOME':str(entry.parent.parent),
             'MYSKILLS_CODEX_BUNDLE_DIR':str(bundle)}, timeout=30)
    assert result.returncode == 0, result.stderr
    assert list(entry.parent.rglob('SKILL.md')) == [entry / 'SKILL.md']
    assert (bundle / 'canonical/skills/bootstrap/SKILL.md').is_file()
