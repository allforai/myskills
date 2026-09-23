"""The run entry a driver executes is its template's body, byte for byte.

ADR-0010: the run templates are guarded here (test_template_snippets, seam-contracts), but
bootstrap used to have a model re-type the template into the target project, and nothing
checked the result. render_run_entry.py copies the body instead, and --check proves an
entry on disk still equals it.
"""
import re
import subprocess
import sys
from pathlib import Path

import pytest

from .test_bootstrap_scope import SCRIPTS

REPO = Path(__file__).resolve().parents[4]
RENDER = SCRIPTS / 'orchestrator' / 'render_run_entry.py'
TEMPLATES = {
    'claude': (REPO / 'claude/meta-skill/knowledge/orchestrator-template.md', '.claude/commands/run.md'),
    'codex': (REPO / 'codex/meta-skill/knowledge/orchestrator-template.md', '.codex/commands/run.md'),
    'pi': (REPO / 'pi/meta-skill/knowledge/orchestrator-template.md', '.pi/skills/run/SKILL.md'),
}


def render(*args, cwd):
    return subprocess.run([sys.executable, str(RENDER), *map(str, args)], cwd=cwd,
                          text=True, capture_output=True)


@pytest.mark.parametrize('host', sorted(TEMPLATES))
def test_the_entry_is_the_template_body_with_every_snippet(tmp_path, host):
    template, entry = TEMPLATES[host]
    result = render(template, entry, cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    written = (tmp_path / entry).read_text(encoding='utf-8')
    source = template.read_text(encoding='utf-8')
    assert written == re.search(r'~~~markdown\n(.*)\n~~~', source, re.S).group(1) + '\n'
    snippets = re.findall(r'<!-- snippet:[a-z0-9-]+ -->', source)
    assert snippets and all(marker in written for marker in snippets)
    assert render(template, entry, '--check', cwd=tmp_path).returncode == 0


def test_a_paraphrased_entry_fails_the_check_and_names_the_line(tmp_path):
    template, entry = TEMPLATES['pi']
    render(template, entry, cwd=tmp_path)
    path = tmp_path / entry
    text = path.read_text(encoding='utf-8')
    path.write_text(text.replace("|| exit 1\n", "\n", 1), encoding='utf-8')
    result = render(template, entry, '--check', cwd=tmp_path)
    assert result.returncode == 1
    assert 'differs from' in result.stdout and '|| exit 1' in result.stdout, result.stdout


def test_a_missing_entry_is_unchecked_not_passed(tmp_path):
    template, entry = TEMPLATES['codex']
    result = render(template, entry, '--check', cwd=tmp_path)
    assert result.returncode == 1
    assert 'does not exist — unchecked, not passed' in result.stdout


def test_a_template_without_a_body_is_refused(tmp_path):
    template = tmp_path / 'template.md'
    template.write_text('# no fenced body here\n', encoding='utf-8')
    result = render(template, 'run.md', cwd=tmp_path)
    assert result.returncode == 2
    assert not (tmp_path / 'run.md').exists()
