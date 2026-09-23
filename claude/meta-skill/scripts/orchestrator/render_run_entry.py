#!/usr/bin/env python3
"""Write a host's run entry from its orchestrator template, byte for byte.

The run entry (`.claude/commands/run.md`, `.codex/commands/run.md`,
`.pi/skills/run/SKILL.md`) is what the /run driver executes. Its template is guarded
in the myskills repository — every shell block is executed by a test, every shared
rule is stamped — but a model re-typing it at bootstrap could paraphrase any of that
away, unseen. So bootstrap copies the body with this script, never by hand, and
`--check` proves an entry on disk still equals its template (ADR-0010).

    render_run_entry.py <template.md> <entry>            write the entry
    render_run_entry.py <template.md> <entry> --check    exit 1 unless <entry> equals the body

An entry is a project file: nothing expands `${CLAUDE_PLUGIN_ROOT}` in it. A body should name
project-local copies instead; one that still names the plugin root is written only with
`--plugin-root <dir>`, which substitutes it (the path then goes stale when the plugin moves),
and refused without it — never left for the driver to trip over.

Exit codes: 0 written / equal; 1 entry missing or different; 2 template has no body, or needs
`--plugin-root`.
"""
import argparse
import difflib
import sys
from pathlib import Path

PLUGIN_ROOT = '${CLAUDE_PLUGIN_ROOT}'
OPEN = '~~~markdown\n'
CLOSE = '\n~~~'
MAX_DIFF_LINES = 20  # enough to locate the drift; the full diff is one --check away


def body(template_text):
    """The run entry: everything between the template's `~~~markdown` fence and its last `~~~`."""
    start = template_text.find(OPEN)
    end = template_text.rfind(CLOSE)
    if start < 0 or end <= start:
        raise ValueError('template has no ~~~markdown … ~~~ body')
    return template_text[start + len(OPEN):end] + '\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('template', type=Path)
    parser.add_argument('entry', type=Path)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--plugin-root', help='substitute ${CLAUDE_PLUGIN_ROOT} in the body with this path')
    args = parser.parse_args(argv)
    try:
        expected = body(args.template.read_text(encoding='utf-8'))
    except (OSError, ValueError) as error:
        print(f'{args.template}: {error}', file=sys.stderr)
        return 2
    if PLUGIN_ROOT in expected:
        if not args.plugin_root:
            print(f'{args.template}: the body names {PLUGIN_ROOT}, which nothing expands in a project '
                  'file; make those references project-local, or pass --plugin-root', file=sys.stderr)
            return 2
        expected = expected.replace(PLUGIN_ROOT, args.plugin_root.rstrip('/'))
    if not args.check:
        args.entry.parent.mkdir(parents=True, exist_ok=True)
        args.entry.write_text(expected, encoding='utf-8')
        print(f'wrote {args.entry} ({expected.count(chr(10))} lines) from {args.template}')
        return 0
    if not args.entry.is_file():
        print(f'{args.entry} does not exist — unchecked, not passed')
        return 1
    actual = args.entry.read_text(encoding='utf-8')
    if actual == expected:
        print(f'ok — {args.entry} equals the body of {args.template}')
        return 0
    diff = list(difflib.unified_diff(expected.splitlines(), actual.splitlines(),
                                     str(args.template), str(args.entry), lineterm=''))
    print(f'{args.entry} differs from the body of {args.template}; re-render it, never edit it by hand:')
    print('\n'.join(diff[:MAX_DIFF_LINES]))
    if len(diff) > MAX_DIFF_LINES:
        print(f'… {len(diff) - MAX_DIFF_LINES} more diff lines')
    return 1


if __name__ == '__main__':
    sys.exit(main())
