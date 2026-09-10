"""Repository check only: every check the engine owns is defined here and nowhere else.

The contract half of the extraction (#58): cross-exam's renderers, the visual acceptance package and their
mirrors reach these names through the engine, as aliases or thin adapters, never as a second `def`. A
consumer that grows its own copy of `content_reason` or `value_tokens` drifts the moment the engine is fixed;
this grep catches it before the mirrors do."""
import re
from pathlib import Path
import pytest

SOURCE = Path(__file__).resolve().parent
# every consumer tree, with the engine mirror inside it excluded; test files may name helpers as they like
CONSUMERS = ('claude/superstorm/scripts', 'claude/superstorm/knowledge/cross-exam',
             'codex/cross-exam-skill', 'shared/visual-acceptance')
DEF = re.compile(r'^def (_?)(\w+)\(', re.MULTILINE)
CONSTANT = re.compile(r'^(_?)([A-Z][A-Z0-9_]+)\s*=\s*(.*)$', re.MULTILINE)


def _root():
    root = next((p for p in SOURCE.parents if (p / 'shared/evidence-engine/sync.py').is_file()), None)
    if root is None:
        pytest.skip('standalone install')
    return root


def engine_names(source=SOURCE):
    """Public functions and constants of the engine modules: what a consumer must import, not redefine."""
    names = set()
    for path in source.glob('*.py'):
        if path.name.startswith('test_') or path.name == 'sync.py':
            continue
        text = path.read_text(encoding='utf-8')
        names |= {m.group(2) for m in DEF.finditer(text) if not m.group(1)}
        names |= {m.group(2) for m in CONSTANT.finditer(text) if not m.group(1)}
    return names


def consumer_files(root):
    for tree in CONSUMERS:
        for path in (root / tree).rglob('*.py'):
            parts = path.relative_to(root / tree).parts
            if 'engine' in parts or path.name.startswith('test_'):
                continue
            if any(part.startswith('.') or part == '__pycache__' for part in parts):
                continue
            yield path


def double_definitions(root, names):
    """(file, name) for every engine-owned name a consumer defines again, with or without a leading
    underscore. An assignment whose right-hand side reads from the engine module is an import, not a copy."""
    found = []
    for path in consumer_files(root):
        text = path.read_text(encoding='utf-8')
        for m in DEF.finditer(text):
            if m.group(2) in names:
                found.append((path.relative_to(root).as_posix(), m.group(1) + m.group(2)))
        for m in CONSTANT.finditer(text):
            if m.group(2) in names and 'engine' not in m.group(3):
                found.append((path.relative_to(root).as_posix(), m.group(1) + m.group(2)))
    return sorted(found)


def test_engine_names_are_the_ones_the_readme_promises():
    names = engine_names()
    for promised in ('build_identity', 'build_reason', 'ref_digest_reason', 'bindings_reason', 'readback_reason',
                     'served_by_reason', 'content_reason', 'probe_window_reason', 'probe_window',
                     'entry_reason', 'value_tokens', 'parse_time', 'PROBE_WINDOW_TOLERANCE'):
        assert promised in names


def test_no_engine_owned_name_is_defined_twice():
    root = _root()
    assert double_definitions(root, engine_names()) == []


def test_grep_sees_a_private_copy_and_an_aliased_import(tmp_path):
    src = tmp_path / 'shared/evidence-engine'
    src.mkdir(parents=True)
    (src / 'sync.py').write_text('')
    (src / 'evidence.py').write_text('def parse_time(v):\n    return v\n\nPROBE_WINDOW_TOLERANCE = 120\n')
    consumer = tmp_path / 'claude/superstorm/scripts'
    consumer.mkdir(parents=True)
    (consumer / 'render_report.py').write_text(
        '_parse_time = _engine.parse_time\nPROBE_WINDOW_TOLERANCE = _engine.PROBE_WINDOW_TOLERANCE\n'
        'def _parse_time_copy(v):\n    return v\n')
    names = engine_names(src)
    assert double_definitions(tmp_path, names) == []
    (consumer / 'render_report.py').write_text('def _parse_time(v):\n    return v\nPROBE_WINDOW_TOLERANCE = 120\n')
    assert double_definitions(tmp_path, names) == [('claude/superstorm/scripts/render_report.py', 'PROBE_WINDOW_TOLERANCE'),
                                                    ('claude/superstorm/scripts/render_report.py', '_parse_time')]
