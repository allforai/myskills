"""Whole-tree build identity, as the visual acceptance protocol defines it (platforms/web.md): commit plus a
working-tree snapshot digest plus, when the target ships built artifacts, a digest over them. Two different
uncommitted states on one commit get different builds; "commit plus dirty" cannot tell them apart.

Snapshot digest: SHA-256 over `git diff HEAD --binary` (staged and unstaged edits against the commit) followed
by every untracked, non-ignored file's path and bytes in sorted order. Artifact digest: SHA-256 over the
named files or directories, path and bytes in sorted order; ignored build output (dist/) is invisible to
the snapshot and only enters the identity this way. Every failure is a returned reason, never a traceback."""
import hashlib
import subprocess
from pathlib import Path

SHORT = 16   # hex digits of each digest kept in the build string; the full values stay in the dict


def _git(repo, *args):
    """Raw stdout of a git command in `repo`; raises on any failure so the caller can name it."""
    return subprocess.run(['git', '-C', str(repo), *args], capture_output=True, check=True, timeout=60).stdout


def _files_under(path):
    return sorted(p for p in path.rglob('*') if p.is_file()) if path.is_dir() else [path]


def snapshot_digest(repo):
    """(digest, '') for the working tree of `repo` relative to HEAD, or ('', reason)."""
    repo = Path(repo)
    try:
        commit = _git(repo, 'rev-parse', '--verify', 'HEAD').decode().strip()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return '', '不是 git 仓库或没有提交: %s' % repo
    h = hashlib.sha256()
    try:
        h.update(_git(repo, 'diff', 'HEAD', '--binary', '--no-color', '--no-ext-diff'))
        untracked = _git(repo, 'ls-files', '--others', '--exclude-standard', '-z').split(b'\0')
        for rel in sorted(r for r in untracked if r):
            path = repo / rel.decode('utf-8', 'surrogateescape')
            h.update(b'\0' + rel + b'\0')
            h.update(path.read_bytes())
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as exc:
        return '', '工作树快照不可读: %s' % exc
    return h.hexdigest(), ''


def artifact_digest(artifacts):
    """(digest, '') over the given files/directories, ('', '') when none were named, or ('', reason)."""
    paths = [Path(p) for p in (artifacts or [])]
    if not paths:
        return '', ''
    h = hashlib.sha256()
    for root in paths:
        if not root.exists():
            return '', '构建产物不存在: %s' % root
        try:
            for f in _files_under(root):
                h.update(b'\0' + f.relative_to(root.parent).as_posix().encode() + b'\0')
                h.update(f.read_bytes())
        except OSError as exc:
            return '', '构建产物不可读: %s' % exc
    return h.hexdigest(), ''


def build_identity(repo, artifacts=()):
    """{commit, snapshot, artifact, build, reason}: `build` is the string an entry records; it is '' and
    `reason` names why when the tree cannot be identified."""
    out = {'commit': '', 'snapshot': '', 'artifact': '', 'build': '', 'reason': ''}
    snapshot, reason = snapshot_digest(repo)
    if reason:
        out['reason'] = reason
        return out
    out['commit'] = _git(repo, 'rev-parse', '--verify', 'HEAD').decode().strip()
    out['snapshot'] = snapshot
    digest, reason = artifact_digest(artifacts)
    if reason:
        out['reason'] = reason
        return out
    out['artifact'] = digest
    out['build'] = out['commit'] + '-' + snapshot[:SHORT] + ('-' + digest[:SHORT] if digest else '')
    return out


def build_reason(recorded, repo, artifacts=()):
    """'' when `recorded` is the identity of the tree at `repo` right now, else the refusal reason."""
    if not isinstance(recorded, str) or not recorded.strip():
        return '缺构建标识 build'
    now = build_identity(repo, artifacts)
    if now['reason']:
        return now['reason']
    if now['build'] != recorded:
        return '构建标识不匹配：记录 %s，当前 %s' % (recorded, now['build'])
    return ''
