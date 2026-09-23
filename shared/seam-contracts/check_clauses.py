#!/usr/bin/env python3
"""Every registered copy of a shared rule is revisited when the rule changes.

ADR-0010: where the same content lives in several places, one is named authoritative and a
check goes red when they differ. The authority holds the rule between `clause-begin:<id>` and
`clause-end:<id>`; each copy carries `clause:<id>@<hash>` of that section. Any edit to the
section changes the hash, so every copy is red until someone rereads the rule, brings the copy
in line and restamps it — required phrases alone would let a copy that never heard of the
change keep passing. A copy that cannot be read is unchecked, never passed.

    python3 shared/seam-contracts/check_clauses.py            # check; exit 1 on any violation
    python3 shared/seam-contracts/check_clauses.py --hashes   # print each clause's current stamp
"""
import hashlib
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = Path(__file__).resolve().with_name('clauses.json')
TEXT_SUFFIXES = {'.md', '.py', '.json', '.js', '.mjs', '.sh', '.txt'}
SKIP_DIRS = {'node_modules', '__pycache__', '.git'}


def normalize(text):
    return re.sub(r'\s+', ' ', text).strip()


def load_registry(path=REGISTRY):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def authority_section(root, clause):
    """The marked rule text in the authority file, or None when missing or unmarked."""
    path = Path(root) / clause['authority']['path']
    if not path.is_file():
        return None
    text = path.read_text(encoding='utf-8')
    cid = re.escape(clause['id'])
    match = re.search(rf'clause-begin:{cid}\b.*?\n(.*?)\n[^\n]*clause-end:{cid}\b', text, re.S)
    return match.group(1) if match else None


def stamp(root, clause):
    section = authority_section(root, clause)
    if section is None:
        return None
    digest = hashlib.sha256(normalize(section).encode('utf-8')).hexdigest()[:8]
    return f"clause:{clause['id']}@{digest}"


def scanned_files(root, scan_roots, exclude):
    """Real text files under the scan roots: symlinks, vendored and excluded dirs are skipped."""
    excluded = {Path(p).resolve() for p in exclude}
    for base in scan_roots:
        for dirpath, dirnames, filenames in os.walk(Path(root) / base):
            here = Path(dirpath)
            dirnames[:] = sorted(d for d in dirnames
                                 if d not in SKIP_DIRS and not (here / d).is_symlink()
                                 and (here / d).resolve() not in excluded)
            for name in sorted(filenames):
                path = here / name
                if path.suffix in TEXT_SUFFIXES and not path.is_symlink():
                    yield path


def _check_authority(root, clause, found):
    cid, rel = clause['id'], clause['authority']['path']
    if not (Path(root) / rel).is_file():
        found.append(f'{cid}: {rel} does not exist — unchecked, not passed')
        return None
    section = authority_section(root, clause)
    if section is None:
        found.append(f'{cid}: {rel} has no clause-begin:{cid} … clause-end:{cid} section')
        return None
    text = normalize(section)
    for token in clause['authority'].get('require', []):
        if normalize(token) not in text:
            found.append(f'{cid}: {rel} no longer says {token!r}')
    return stamp(root, clause)


def _check_copy(root, clause, copy, current, found):
    cid, rel = clause['id'], copy['path']
    exempt = 'exempt' in copy
    if exempt and not str(copy['exempt']).strip():
        found.append(f'{cid}: {rel} is exempt with no reason')
        return
    if not exempt and not copy.get('require'):
        found.append(f'{cid}: {rel} has neither a non-empty require list nor an exempt reason')
        return
    path = Path(root) / rel
    if not path.is_file():
        found.append(f'{cid}: {rel} does not exist — unchecked, not passed')
        return
    raw = path.read_text(encoding='utf-8')
    if current is not None and current not in raw:
        stale = re.search(rf'clause:{re.escape(cid)}@([0-9a-f]{{8}})', raw)
        if stale:
            found.append(f"{cid}: {rel} was stamped {stale.group(1)} but the authority is now "
                         f"{current.split('@')[1]}: reread {clause['authority']['path']} "
                         f"clause-begin:{cid}, bring this copy in line, then restamp it")
        else:
            found.append(f'{cid}: {rel} has no {current} stamp')
    if not exempt:
        text = normalize(raw)
        for token in copy['require']:
            if normalize(token) not in text:
                found.append(f'{cid}: {rel} no longer says {token!r}')


def violations(root, registry, exclude=()):
    root = Path(root)
    found = []
    texts = None
    for clause in registry['clauses']:
        current = _check_authority(root, clause, found)
        for copy in clause.get('copies', []):
            _check_copy(root, clause, copy, current, found)
        if clause.get('forbid'):
            if texts is None:
                texts = {path: normalize(path.read_text(encoding='utf-8', errors='ignore'))
                         for path in scanned_files(root, registry['scan_roots'], exclude)}
            for phrase in clause['forbid']:
                for path, text in texts.items():
                    if normalize(phrase) in text:
                        found.append(f"{clause['id']}: {path.relative_to(root).as_posix()} "
                                     f'still says retired {phrase!r}')
    return found


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    registry = load_registry()
    if argv == ['--hashes']:
        for clause in registry['clauses']:
            print(stamp(ROOT, clause) or f"{clause['id']}: unmarked")
        return 0
    found = violations(ROOT, registry, exclude=(REGISTRY.parent,))
    for line in found:
        print(line)
    if found:
        print(f'{len(found)} clause violation(s): fix the copy, or change the rule at its authority '
              f'and revisit every copy {REGISTRY.relative_to(ROOT)} lists', file=sys.stderr)
        return 1
    print(f"ok — {len(registry['clauses'])} clause(s), every copy agrees")
    return 0


if __name__ == '__main__':
    sys.exit(main())
