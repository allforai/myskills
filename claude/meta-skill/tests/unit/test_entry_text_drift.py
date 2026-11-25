"""The meta-skill entry describes what ships, not what used to (expert review 2026-11-26)."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENTRY = ROOT / 'SKILL.md'
BOOTSTRAP = ROOT / 'skills/bootstrap/SKILL.md'


def capability_section():
    text = ENTRY.read_text(encoding='utf-8')
    match = re.search(r'^## Capabilities \((\d+)\)\n(.*?)(?=^## )', text, re.S | re.M)
    assert match, 'SKILL.md has no "## Capabilities (N)" section'
    names = set(re.findall(r'^\| ([a-z0-9-]+) \|', match.group(2), re.M))
    return int(match.group(1)), names


def test_capability_count_matches_files():
    count, names = capability_section()
    files = {path.stem for path in (ROOT / 'knowledge/capabilities').glob('*.md')}
    # `implement` is a goal bootstrap maps without a file of its own; every file is listed.
    assert files <= names, f'file but not listed: {sorted(files - names)}'
    assert count == len(names)


def test_entry_does_not_describe_retired_parts():
    entry = ENTRY.read_text(encoding='utf-8')
    assert 'state machine configurations' not in entry
    assert 'LLM-driven state machine' not in entry
    assert 'MCP tools' not in entry
    heading = next(line for line in BOOTSTRAP.read_text(encoding='utf-8').splitlines() if line.startswith('# '))
    assert not re.search(r'v\d+\.', heading), heading
