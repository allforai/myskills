#!/usr/bin/env python3
"""Crash-safe Cross-exam ledger snapshots and single-examiner run locks."""
import json
import os
import subprocess
import tempfile
import time
import uuid
from pathlib import Path


class ActiveRunError(RuntimeError):
    pass


def _process_start_token(pid):
    """Best-effort PID reuse guard on procfs; None means not verifiable."""
    try:
        return Path(f"/proc/{pid}/stat").read_text().split()[21]
    except (OSError, IndexError):
        try:
            result = subprocess.run(["ps", "-o", "lstart=", "-p", str(pid)],
                                    capture_output=True, text=True, timeout=2)
            token = result.stdout.strip()
            return token or None
        except (OSError, subprocess.SubprocessError):
            return None


def atomic_write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".cross-exam-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, ensure_ascii=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def acquire_lock(run_dir, run_id=None, confirm_stale=False):
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    lock_path = run_dir / ".examiner.lock"
    if lock_path.exists():
        old = json.loads(lock_path.read_text())
        old_pid = old.get("pid")
        live_token = _process_start_token(old_pid) if isinstance(old_pid, int) else None
        live = live_token is not None and live_token == old.get("process_start")
        if live:
            raise ActiveRunError(f"cross-exam run already active (pid={old_pid})")
        if not confirm_stale:
            raise ActiveRunError("stale examiner lock requires explicit takeover confirmation")
        os.replace(lock_path, run_dir / f".examiner.lock.stale-{int(time.time())}")
    rid = run_id or str(uuid.uuid4())
    record = {"schema_version": 1, "run_id": rid, "pid": os.getpid(),
              "process_start": _process_start_token(os.getpid()), "created": time.time()}
    fd = os.open(lock_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(record, handle)
        handle.flush()
        os.fsync(handle.fileno())
    return record


def release_lock(run_dir, run_id):
    path = Path(run_dir) / ".examiner.lock"
    record = json.loads(path.read_text())
    if record.get("run_id") != run_id:
        raise ActiveRunError("refusing to release another run's lock")
    path.unlink()


def save_ledger(run_dir, ledger):
    ledger = dict(ledger)
    ledger.setdefault("schema_version", 1)
    seen = {}
    for collection in (ledger.get("entries", []), ledger.get("open_threads", [])):
        for item in collection:
            item.setdefault("id", str(uuid.uuid4()))
            encoded = json.dumps(item, sort_keys=True, ensure_ascii=False)
            if item["id"] in seen and seen[item["id"]] != encoded:
                raise ValueError(f"conflicting duplicate ledger id: {item['id']}")
            seen[item["id"]] = encoded
    atomic_write(Path(run_dir) / "ledger.json", ledger)
