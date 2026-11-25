"""`human_gate` is retired (bootstrap SKILL.md: "not a runtime concept"). No skill text may
still tell bootstrap to set it: a game project would follow the more specific old rule.
Legacy projects keep their validator and readiness handling; only the teaching goes."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MENTION = re.compile(r'(?<![a-z_])human_gates?(?![a-z_])')
# The paragraph that retires it, and lines that only say it is retired or legacy.
ALLOWED = re.compile(r'not a runtime concept|Do not emit|retired|legacy|former `human_gate`', re.I)


def offending_lines():
    found = []
    for path in sorted(ROOT.rglob('*.md')):
        if {'fixtures', 'tests'} & set(path.relative_to(ROOT).parts):
            continue
        for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
            if MENTION.search(line) and not ALLOWED.search(line):
                found.append(f'{path.relative_to(ROOT)}:{number}: {line.strip()[:120]}')
    return found


def test_no_skill_text_tells_bootstrap_to_set_human_gate():
    assert offending_lines() == []


# The same retired gate, described without its name: a run that waits for an approval, or
# a node that halts unless a record is approved (ADR-0018: /run stops for no one).
RUN_WAITS_FOR_APPROVAL = re.compile(
    r'wait for `?discipline_owner|do not run until it is `?approved|'
    r'gate_status == "approved"`?\. Collect|If any exist → halt|'
    r'Do not produce the contract until all gates pass|gate-driven unblocking|'
    r'`/run` automatically sets `gate_status`|approved → `/run`|must not run until all upstream nodes are approved|requires human approval gate', re.I)


def test_no_run_time_text_waits_for_an_approval():
    found = []
    for path in sorted(ROOT.rglob('*.md')):
        if {'fixtures', 'tests'} & set(path.relative_to(ROOT).parts):
            continue
        for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
            if RUN_WAITS_FOR_APPROVAL.search(line):
                found.append(f'{path.relative_to(ROOT)}:{number}: {line.strip()[:110]}')
    assert found == []
