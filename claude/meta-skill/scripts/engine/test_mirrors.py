"""Repository check only; installed mirrors do not depend on shared paths."""
import importlib.util
from pathlib import Path
import pytest


def _load_sync():
    root = next((p for p in Path(__file__).resolve().parents if (p / 'shared/evidence-engine/sync.py').is_file()), None)
    if root is None:
        pytest.skip('standalone install')
    spec = importlib.util.spec_from_file_location('evidence_sync', root / 'shared/evidence-engine/sync.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_committed_mirrors_match():
    assert _load_sync().sync(check=True) == []


def test_four_mirrors_sit_beside_their_consumers():
    module = _load_sync()
    root = module.SOURCE.parents[1]
    assert [t.relative_to(root).as_posix() for t in module.TARGETS] == [
        'claude/superstorm/knowledge/cross-exam/engine', 'codex/cross-exam-skill/engine',
        'claude/meta-skill/scripts/engine', 'codex/meta-skill/scripts/engine']
    # cross-exam reaches the engine as a sibling of its visual acceptance mirror
    for target in module.TARGETS[:2]:
        assert (target.parent / 'visual/validation.py').is_file()


def test_divergent_mirror_fails_check(tmp_path):
    module = _load_sync()
    source = tmp_path / 'a/b/src'
    source.mkdir(parents=True)
    (source / 'evidence.py').write_text('x')
    (source / 'requirements.txt').write_text('')
    target = tmp_path / 'a/mirror'
    module.sync(check=False, source=source, targets=[target])
    assert module.sync(check=True, source=source, targets=[target]) == []
    (target / 'evidence.py').write_text('edited in the mirror')
    assert module.sync(check=True, source=source, targets=[target]) == ['mirror/evidence.py']
    (source / 'evidence.py').write_text('fixed in the source')
    module.sync(check=False, source=source, targets=[target])
    assert (target / 'evidence.py').read_text() == 'fixed in the source'


def test_sync_ignores_tool_residue(tmp_path):
    # .pytest_cache/README.md and __pycache__/*.py sit inside the source tree after a test run;
    # they are not package files and must neither fail --check nor be copied into mirrors.
    module = _load_sync()
    source = tmp_path / 'a/b/src'
    source.mkdir(parents=True)
    (source / 'real.md').write_text('x')
    (source / 'requirements.txt').write_text('')
    (source / '.pytest_cache').mkdir()
    (source / '.pytest_cache/README.md').write_text('cache')
    (source / '__pycache__').mkdir()
    (source / '__pycache__/real.cpython-314.pyc').write_text('bin')
    (source / '__pycache__/stray.py').write_text('bin')
    target = tmp_path / 'a/mirror'
    assert sorted(p.relative_to(source).as_posix() for p in module.collect(source)) == ['real.md', 'requirements.txt']
    module.sync(check=False, source=source, targets=[target])
    assert not (target / '.pytest_cache').exists()
    assert not (target / '__pycache__').exists()
    assert module.sync(check=True, source=source, targets=[target]) == []


def test_sync_reports_and_removes_stale_mirror_files(tmp_path):
    module = _load_sync()
    source = tmp_path / 'a/b/src'
    source.mkdir(parents=True)
    (source / 'keep.md').write_text('k')
    (source / 'requirements.txt').write_text('')
    target = tmp_path / 'a/mirror'
    module.sync(check=False, source=source, targets=[target])
    (target / 'retired.py').write_text('old')                  # renamed away in source
    (target / 'notes.txt').write_text('not package-shaped')    # ignored: not a mirrored suffix
    report = module.sync(check=True, source=source, targets=[target])
    assert report == ['mirror/retired.py (stale, not in source)']
    assert (target / 'retired.py').exists()                    # --check never deletes
    module.sync(check=False, source=source, targets=[target])
    assert not (target / 'retired.py').exists()
    assert (target / 'notes.txt').exists()
    assert module.sync(check=True, source=source, targets=[target]) == []
