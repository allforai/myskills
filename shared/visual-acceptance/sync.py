"""Synchronize committed, self-contained Claude/Codex visual acceptance mirrors."""
import argparse
from pathlib import Path

SOURCE = Path(__file__).resolve().parent
TARGETS = [SOURCE.parents[1] / 'claude/megastorm/knowledge/cross-exam/visual',
           SOURCE.parents[1] / 'codex/cross-exam-skill/visual']
SUFFIXES = {'.md', '.py', '.swift'}
EXTRA = ('swiftui/LICENSE', 'requirements.txt')


def _is_scratch(path, source):
    """Hidden directories (.pytest_cache, .git) and __pycache__ are tool residue, not package files."""
    return any(part.startswith('.') or part == '__pycache__'
               for part in path.relative_to(source).parts[:-1])


def collect(source):
    files = [p for p in source.rglob('*') if p.is_file() and p.suffix in SUFFIXES
             and p.name != 'sync.py' and not _is_scratch(p, source)]
    files += [source / rel for rel in EXTRA]
    return files


def stray(target, source):
    """Package-shaped files in a mirror that the source no longer has: renamed or retired in shared/."""
    if not target.is_dir():
        return []
    wanted = {p.relative_to(source) for p in collect(source)}
    return [p for p in target.rglob('*') if p.is_file() and not _is_scratch(p, target)
            and (p.suffix in SUFFIXES or p.relative_to(target).as_posix() in EXTRA)
            and p.relative_to(target) not in wanted]


def sync(check=False, source=SOURCE, targets=TARGETS):
    root = source.parents[1]
    mismatches = []
    for target in targets:
        for path in collect(source):
            dest = target / path.relative_to(source)
            if not dest.exists() or dest.read_bytes() != path.read_bytes():
                mismatches.append(str(dest.relative_to(root)))
                if not check:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(path.read_bytes())
        for extra in stray(target, source):
            mismatches.append(str(extra.relative_to(root)) + ' (stale, not in source)')
            if not check:
                extra.unlink()
    return mismatches


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    mismatches = sync(args.check)
    print('\n'.join(mismatches) if mismatches else 'Visual mirrors match')
    raise SystemExit(1 if args.check and mismatches else 0)
