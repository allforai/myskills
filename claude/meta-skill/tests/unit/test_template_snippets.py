"""The shell a run template hands its driver runs against the helpers it names.

ADR-0010: a template snippet crosses a seam — the driver copies it verbatim, and the helper it
calls changes on its own schedule. Every bash block in a run template is classified: a
`snippet:` block is extracted and run here against a bootstrapped fixture, an `illustrative:`
block says why it is not. Drift on either side goes red here, not in a live run.
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from .test_bootstrap_scope import SCRIPTS
from .test_evidence_freshness import invoke, setup

REPO = Path(__file__).resolve().parents[4]
TEMPLATES = {
    'claude': REPO / 'claude/meta-skill/knowledge/orchestrator-template.md',
    'codex': REPO / 'codex/meta-skill/knowledge/orchestrator-template.md',
    'pi': REPO / 'pi/meta-skill/knowledge/orchestrator-template.md',
}
# Every snippet name a template may use; each is executed by a test below.
EXECUTED = {'preflight-readiness', 'repair-ledger-initialize', 'freshness-publish'}
NODE = 'deliver-export'
PASSING = json.dumps([sys.executable, '-c', 'pass'])
FAILING = json.dumps([sys.executable, '-c', 'raise SystemExit(3)'])
MARKER = re.compile(r'<!-- (snippet:([a-z0-9-]+)|illustrative:(.*?)) -->')


def snippet(template, name):
    """The fenced bash block right after `<!-- snippet:<name> -->`, list indentation removed."""
    text = template.read_text(encoding='utf-8')
    match = re.search(r'<!-- snippet:' + re.escape(name) + r' -->[ \t]*\n([ \t]*)```bash\n(.*?)\n[ \t]*```',
                      text, re.S)
    assert match, f'{template.name} has no snippet:{name} marker followed by a bash block'
    indent = match.group(1)
    return '\n'.join(line[len(indent):] if line.startswith(indent) else line
                     for line in match.group(2).splitlines())


def publish_script(acceptance):
    script = snippet(TEMPLATES['pi'], 'freshness-publish')
    script = script.replace('<node_id>', NODE).replace('<acceptance_argv_json>', acceptance)
    assert not re.search(r'<[a-z_]+>', script), f'unfilled placeholder left in:\n{script}'
    return script


def run(root, script):
    return subprocess.run(['bash', '-c', script], cwd=root, text=True, capture_output=True)


def gate(root):
    result = subprocess.run([sys.executable, str(root / '.allforai/bootstrap/scripts/check_artifacts.py'),
                             str(root / '.allforai/bootstrap/workflow.json'), '--node', NODE, '--json'],
                            text=True, capture_output=True)
    return json.loads(result.stdout)['all_exist']


def test_snippet_extraction_names_a_missing_marker(tmp_path):
    template = tmp_path / 'template.md'
    template.write_text('8. On success:\n\n   ```bash\n   echo hi\n   ```\n', encoding='utf-8')
    with pytest.raises(AssertionError, match='snippet:freshness-publish'):
        snippet(template, 'freshness-publish')


@pytest.mark.parametrize('host', sorted(TEMPLATES))
def test_every_bash_block_in_the_run_templates_is_classified(host):
    lines = TEMPLATES[host].read_text(encoding='utf-8').splitlines()
    problems = []
    for number, line in enumerate(lines):
        if line.strip() != '```bash':
            continue
        previous = next((l.strip() for l in reversed(lines[:number]) if l.strip()), '')
        marker = MARKER.fullmatch(previous)
        if not marker:
            problems.append(f'line {number + 1}: bash block with no snippet:/illustrative: marker')
        elif marker.group(2) and marker.group(2) not in EXECUTED:
            problems.append(f'line {number + 1}: snippet:{marker.group(2)} is executed by no test')
        elif marker.group(3) is not None and not marker.group(3).strip():
            problems.append(f'line {number + 1}: illustrative block with no reason')
    assert problems == [], f'{TEMPLATES[host]}:\n' + '\n'.join(problems)


@pytest.mark.parametrize('host', sorted(TEMPLATES))
def test_preflight_readiness_snippet_writes_the_readiness_report(tmp_path, host):
    setup(tmp_path, 'claude')
    shutil.copy2(SCRIPTS / 'orchestrator' / 'record_run_event.py',
                 tmp_path / '.allforai/bootstrap/scripts/record_run_event.py')
    result = run(tmp_path, snippet(TEMPLATES[host], 'preflight-readiness'))
    report = tmp_path / '.allforai/bootstrap/unattended-run-readiness.json'
    assert report.is_file(), result.stdout + result.stderr
    assert json.loads(report.read_text())['status'] in ('ready', 'not_ready')


@pytest.mark.parametrize('host', ['claude', 'pi'])
def test_repair_ledger_initialize_snippet_records_a_new_run(tmp_path, host):
    setup(tmp_path, 'claude')
    shutil.copy2(SCRIPTS / 'orchestrator' / 'repair_authorization.py',
                 tmp_path / '.allforai/bootstrap/scripts/repair_authorization.py')
    (tmp_path / '.allforai/bootstrap/run-id').write_text('run-1\n', encoding='utf-8')
    script = snippet(TEMPLATES[host], 'repair-ledger-initialize')
    first = run(tmp_path, script)
    assert first.returncode == 0, first.stdout + first.stderr
    answer = json.loads(first.stdout)
    assert answer['status'] == 'ok' and answer['origin'] == 'new_run', answer
    again = json.loads(run(tmp_path, script).stdout)
    assert again['replayed'] is True, again


def test_pi_publish_then_gate_completes_an_accepted_node(tmp_path):
    # The gate reads published freshness: before publication it refuses completion, so the
    # Core Loop must publish first and gate second.
    setup(tmp_path, 'claude')
    assert gate(tmp_path) is False
    result = run(tmp_path, publish_script(PASSING))
    assert result.returncode == 0, result.stdout + result.stderr
    _, checked = invoke(tmp_path, 'check')
    assert checked['nodes'][NODE]['status'] == 'valid', checked
    assert gate(tmp_path) is True


def test_pi_core_loop_publishes_before_the_gate():
    loop = TEMPLATES['pi'].read_text(encoding='utf-8').split('## Core Loop', 1)[1].split('\n## ', 1)[0]
    publish = loop.index('<!-- snippet:freshness-publish -->')
    gate_step = loop.index('--node <node_id> --json')
    assert publish < gate_step, 'Pi Core Loop runs the artifact gate before publishing the freshness it reads'


def test_pi_freshness_publish_snippet_refuses_when_acceptance_fails(tmp_path):
    # check_artifacts.py --json exits 0 whatever it finds; the snippet's verification must be a
    # command that can fail, or a rejected delivery publishes as verified.
    setup(tmp_path, 'claude')
    result = run(tmp_path, publish_script(FAILING))
    assert result.returncode != 0, result.stdout
    assert 'failed_verification' in result.stdout, result.stdout
    _, checked = invoke(tmp_path, 'check')
    assert checked['nodes'].get(NODE, {}).get('status') != 'valid', checked
    assert gate(tmp_path) is False


def test_pi_freshness_publish_snippet_fails_without_killing_the_callers_shell(tmp_path):
    setup(tmp_path, 'claude')
    result = run(tmp_path, publish_script(FAILING) + '\necho "caller survived: $?"')
    assert 'caller survived: 1' in result.stdout, result.stdout + result.stderr
