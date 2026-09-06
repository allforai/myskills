"""Repository check only; installed mirrors do not depend on shared paths."""
import importlib.util
from pathlib import Path
import pytest


def _load_sync():
    root = next((p for p in Path(__file__).resolve().parents if (p / 'shared/visual-acceptance/sync.py').is_file()), None)
    if root is None:
        pytest.skip('standalone install')
    spec = importlib.util.spec_from_file_location('visual_sync', root / 'shared/visual-acceptance/sync.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_committed_mirrors_match():
    assert _load_sync().sync(check=True) == []


def test_sync_ignores_tool_residue(tmp_path):
    # .pytest_cache/README.md and __pycache__/*.py sit inside the source tree after a test run;
    # they are not package files and must neither fail --check nor be copied into mirrors.
    module = _load_sync()
    source = tmp_path / 'a/b/src'
    (source / 'swiftui').mkdir(parents=True)
    (source / 'real.md').write_text('x')
    (source / 'swiftui/LICENSE').write_text('MIT')
    (source / 'requirements.txt').write_text('Pillow')
    (source / '.pytest_cache').mkdir()
    (source / '.pytest_cache/README.md').write_text('cache')
    (source / '__pycache__').mkdir()
    (source / '__pycache__/real.cpython-314.pyc').write_text('bin')
    (source / '__pycache__/stray.py').write_text('bin')
    target = tmp_path / 'a/mirror'
    assert sorted(p.relative_to(source).as_posix() for p in module.collect(source)) == [
        'real.md', 'requirements.txt', 'swiftui/LICENSE']
    module.sync(check=False, source=source, targets=[target])
    assert not (target / '.pytest_cache').exists()
    assert not (target / '__pycache__').exists()
    assert module.sync(check=True, source=source, targets=[target]) == []


def test_sync_reports_and_removes_stale_mirror_files(tmp_path):
    module = _load_sync()
    source = tmp_path / 'a/b/src'
    (source / 'swiftui').mkdir(parents=True)
    (source / 'keep.md').write_text('k')
    (source / 'swiftui/LICENSE').write_text('MIT')
    (source / 'requirements.txt').write_text('Pillow')
    target = tmp_path / 'a/mirror'
    module.sync(check=False, source=source, targets=[target])
    (target / 'retired-prompt.md').write_text('old')          # renamed away in source
    (target / 'notes.txt').write_text('not package-shaped')    # ignored: not a mirrored suffix
    report = module.sync(check=True, source=source, targets=[target])
    assert report == ['mirror/retired-prompt.md (stale, not in source)']
    assert (target / 'retired-prompt.md').exists()             # --check never deletes
    module.sync(check=False, source=source, targets=[target])
    assert not (target / 'retired-prompt.md').exists()
    assert (target / 'notes.txt').exists()
    assert module.sync(check=True, source=source, targets=[target]) == []
