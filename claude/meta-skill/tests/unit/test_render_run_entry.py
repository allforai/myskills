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


BOOTSTRAPS = {
    'claude': REPO / 'claude/meta-skill/skills/bootstrap/SKILL.md',
    'codex': REPO / 'codex/meta-skill/skills/bootstrap.md',
    'pi': REPO / 'pi/meta-skill/skills/bootstrap/SKILL.md',
}
LOCAL_REF = re.compile(r'\.allforai/bootstrap/(?:scripts|protocols|run-engine)/[A-Za-z0-9_./-]+?\.(?:py|md|js)\b')


def template_body(host):
    source = TEMPLATES[host][0].read_text(encoding='utf-8')
    return re.search(r'~~~markdown\n(.*)\n~~~', source, re.S).group(1)


@pytest.mark.parametrize('host', sorted(TEMPLATES))
def test_every_project_local_file_the_entry_runs_is_copied_by_its_bootstrap(host):
    # The entry names project-local helpers; bootstrap is what puts them there. A helper the
    # entry runs and the bootstrap never copies fails only at run time, in the user's project.
    copied = BOOTSTRAPS[host].read_text(encoding='utf-8')
    if host != 'claude':  # Codex and Pi copy "at least the canonical Step 6.2 set" as well
        copied += BOOTSTRAPS['claude'].read_text(encoding='utf-8')
    missing = sorted({ref for ref in LOCAL_REF.findall(template_body(host))
                      if Path(ref).name not in copied})
    assert missing == [], f'{host} entry runs files its bootstrap never copies: {missing}'


def test_the_claude_entry_uses_only_project_local_paths():
    # A project command does not expand ${CLAUDE_PLUGIN_ROOT}; the entry must not need it.
    assert '${CLAUDE_PLUGIN_ROOT}' not in template_body('claude')


def test_an_unresolved_plugin_root_is_refused_without_the_flag(tmp_path):
    template = tmp_path / 'template.md'
    template.write_text('~~~markdown\nrun ${CLAUDE_PLUGIN_ROOT}/x.py\n~~~\n', encoding='utf-8')
    refused = render(template, 'run.md', cwd=tmp_path)
    assert refused.returncode == 2 and 'CLAUDE_PLUGIN_ROOT' in refused.stderr
    assert not (tmp_path / 'run.md').exists()
    written = render(template, 'run.md', '--plugin-root', '/opt/meta-skill', cwd=tmp_path)
    assert written.returncode == 0, written.stderr
    assert (tmp_path / 'run.md').read_text(encoding='utf-8') == 'run /opt/meta-skill/x.py\n'
    assert render(template, 'run.md', '--check', '--plugin-root', '/opt/meta-skill', cwd=tmp_path).returncode == 0
    assert render(template, 'run.md', '--check', cwd=tmp_path).returncode == 2


def test_the_copied_helpers_work_from_the_project(tmp_path):
    # Run the Claude bootstrap's own Step 6.2 copy block, then load what the entry runs from the
    # project copy: a helper that finds its dependencies only beside the plugin fails here.
    skill = BOOTSTRAPS['claude'].read_text(encoding='utf-8')
    block = re.search(r'### 6\.2 Copy Orchestrator Scripts.*?```bash\n(.*?)\n```', skill, re.S).group(1)
    env = {'PATH': '/usr/bin:/bin', 'CLAUDE_PLUGIN_ROOT': str(SCRIPTS.parent)}
    copied = subprocess.run(['bash', '-ec', block], cwd=tmp_path, env=env, text=True, capture_output=True)
    assert copied.returncode == 0, copied.stderr
    for ref in sorted(set(LOCAL_REF.findall(template_body('claude')))):
        assert (tmp_path / ref).is_file(), f'{ref} named by the entry, missing after Step 6.2'
    probe = ("import sys; sys.path.insert(0, '.allforai/bootstrap/scripts'); "
             "import check_evidence, compute_completeness, compute_reset_closure; "
             "assert check_evidence.engine('evidence') and check_evidence.engine('identity')")
    loaded = subprocess.run([sys.executable, '-c', probe], cwd=tmp_path, text=True, capture_output=True)
    assert loaded.returncode == 0, loaded.stderr
