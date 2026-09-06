"""Install one discovery entry and a self-contained bundle outside skill scanning."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


def remove_owned(path):
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)


def install(source, entry, bundle):
    source = source.resolve()
    # Resolve parents, not the old entry symlink: migration must not delete source.
    entry = entry.parent.resolve() / entry.name
    bundle = bundle.parent.resolve() / bundle.name
    for target in (entry, bundle):
        if target.name != 'meta-skill' or target == source or target in source.parents or source in target.parents:
            raise ValueError(f'unsafe installation target: {target}')
    if bundle.parent.name != 'skill-bundles' or 'skills' in bundle.parts or '.agents' in bundle.parts:
        raise ValueError('bundle must live under skill-bundles, outside skills discovery roots')
    if entry == bundle or entry in bundle.parents or bundle in entry.parents:
        raise ValueError('entry and bundle must be separate')
    canonical = source.parent.parent / 'claude/meta-skill'
    if not (canonical / 'skills/bootstrap/SKILL.md').is_file():
        raise ValueError('canonical bootstrap entry missing; install from a complete remote checkout')
    if not (source / 'SKILL.md').is_file():
        raise ValueError('Codex entry missing')
    entry.parent.mkdir(parents=True, exist_ok=True)
    bundle.parent.mkdir(parents=True, exist_ok=True)
    ignore = shutil.ignore_patterns('node_modules', '__pycache__', '.pytest_cache', '.git')
    with tempfile.TemporaryDirectory(prefix='.meta-stage-', dir=bundle.parent) as staging:
        stage = Path(staging)
        payload = stage / 'bundle'
        shutil.copytree(source, payload, ignore=ignore)
        shutil.copytree(canonical / 'skills', payload / 'canonical/skills', ignore=ignore)
        shutil.copytree(canonical / 'knowledge', payload / 'canonical/knowledge', ignore=ignore)
        gateway = payload / 'mcp-ai-gateway'
        if (gateway / 'package.json').is_file():
            subprocess.run(['npm', 'ci', '--ignore-scripts'], cwd=gateway, check=True, timeout=300)
            subprocess.run(['npm', 'run', 'build'], cwd=gateway, check=True, timeout=300)
        compile((payload / 'knowledge/flow-template.py').read_text(), 'flow-template.py', 'exec')
        commit = os.environ.get('SOURCE_COMMIT')
        if not commit:
            commit = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
        (payload / '.install-source').write_text(
            f"source_repo={os.environ.get('SOURCE_REPO', 'https://github.com/allforai/myskills.git')}\n"
            f"source_ref={os.environ.get('SOURCE_REF', 'refs/heads/main')}\nsource_commit={commit}\n")
        # Stage the entry on its own filesystem for rename-based promotion.
        with tempfile.TemporaryDirectory(prefix='.meta-entry-', dir=entry.parent.parent) as entry_staging:
            pending = Path(entry_staging) / 'entry'
            pending.mkdir()
            frontmatter = (source / 'SKILL.md').read_text().split('---', 2)[1]
            (pending / 'SKILL.md').write_text(
                f'---{frontmatter}---\n\n# Meta-Skill entry\n\n'
                f'Read `{bundle}/SKILL.md` and `{bundle}/AGENTS.md` completely before executing a command.\n'
                f'Treat `{bundle}/` as the skill root for all relative protocol paths, '
                'including commands, skills/bootstrap.md, knowledge, scripts and canonical.\n'
                'Load internal capabilities only as needed. Do not copy or symlink the bundle '
                'back into a skills discovery directory. Preserve the bundled invocation policy.\n')
            if (source / 'agents').is_dir():
                shutil.copytree(source / 'agents', pending / 'agents')
            shutil.copyfile(payload / '.install-source', pending / '.install-source')
            old_entry = Path(entry_staging) / 'old-entry'
            old_bundle = stage / 'old-bundle'
            promoted = []
            moved = []
            try:
                for target, old in ((entry, old_entry), (bundle, old_bundle)):
                    if target.exists() or target.is_symlink():
                        target.rename(old)
                        moved.append((target, old))
                payload.rename(bundle)
                promoted.append(bundle)
                pending.rename(entry)
                promoted.append(entry)
            except BaseException:
                for target in reversed(promoted):
                    remove_owned(target)
                for target, old in reversed(moved):
                    old.rename(target)
                raise
            # Previous owned installs are removed only after successful promotion.
    print(f'Installed meta-skill entry: {entry}\nBundle (not scanned): {bundle}\nSource: {commit}')


def main():
    root = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex')))
    entry = Path(os.environ.get('MYSKILLS_CODEX_INSTALL_DIR', str(root / 'skills/meta-skill')))
    bundle = Path(os.environ.get('MYSKILLS_CODEX_BUNDLE_DIR', str(entry.parent.parent / 'skill-bundles/meta-skill')))
    install(Path(__file__).resolve().parent, entry, bundle)


if __name__ == '__main__':
    main()
