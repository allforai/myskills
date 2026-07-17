#!/usr/bin/env python3
"""Discover the current Codex host and build inherited, non-shell child argv."""
from dataclasses import dataclass
import ctypes
import ctypes.util
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import struct
import sys
from urllib.parse import urlsplit, urlunsplit


class HostCommandError(RuntimeError):
    pass


ZERO_INHERIT = {
    "--oss", "--strict-config", "--dangerously-bypass-approvals-and-sandbox",
    "--dangerously-bypass-hook-trust", "--skip-git-repo-check",
    "--ignore-user-config", "--ignore-rules",
}
ROOT_ZERO = {"--search"}
ONE_INHERIT = {
    "-c", "--config", "--enable", "--disable", "-p", "--profile",
    "--local-provider", "-s", "--sandbox", "--add-dir",
}
ROOT_ONE = {"-a", "--ask-for-approval"}
ZERO_DROP = {"--json", "--ephemeral", "--no-alt-screen"}
ONE_DROP = {
    "-m", "--model", "-C", "--cd", "-o", "--output-last-message",
    "--color", "--output-schema",
}
SENSITIVE = re.compile(
    r"(?:^|[._-])(token|secret|password|api[_-]?key|apikey|authorization|credential)(?:$|[._-])",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ProcessSnapshot:
    pid: int
    ppid: int
    executable: str
    argv: tuple
    start_token: str


@dataclass(frozen=True)
class InvocationSpec:
    executable: str
    root_args: tuple
    exec_args: tuple
    source: str
    discovered_argv: tuple
    legacy_template: str = ""

    def build(self, model, cwd, out, prompt):
        if self.legacy_template:
            try:
                rendered = self.legacy_template.format(model=model, cwd=str(cwd), out=str(out))
            except KeyError as exc:
                raise HostCommandError(f"unknown legacy template placeholder: {exc}") from exc
            argv = shlex.split(rendered)
            if not argv:
                raise HostCommandError("legacy template rendered an empty command")
            argv[0] = canonical_executable(argv[0], require_codex=False)
            return argv + [prompt]
        return [self.executable, *self.root_args, "exec", *self.exec_args,
                "--ephemeral", "-m", model, "-C", str(cwd),
                "--output-last-message", str(out), prompt]

    def metadata(self, environ=None):
        env = os.environ if environ is None else environ
        return {
            "source": self.source,
            "executable": self.executable,
            "discovered_argv": redact_argv(self.discovered_argv, env),
            "preserved_root_args": redact_argv(self.root_args, env),
            "preserved_exec_args": redact_argv(self.exec_args, env),
        }


def canonical_executable(value, require_codex=True):
    resolved = value if os.path.isabs(value) else shutil.which(value)
    if not resolved:
        raise HostCommandError(f"executable cannot be resolved: {value}")
    resolved = os.path.abspath(resolved)
    if require_codex and os.path.basename(resolved) != "codex":
        raise HostCommandError("resolved host executable is not codex")
    return resolved


def _split_option(token):
    if token.startswith("--") and "=" in token:
        return token.split("=", 1)
    return token, None


def normalize_host_argv(argv, source, executable=None):
    if not argv or not all(isinstance(v, str) and v for v in argv):
        raise HostCommandError("host argv must be a non-empty string array")
    exe = canonical_executable(executable or argv[0])
    root_args, exec_args = [], []
    args = list(argv[1:])
    in_exec = False
    prompt_seen = False
    i = 0
    while i < len(args):
        token = args[i]
        if token == "exec":
            if in_exec:
                raise HostCommandError("duplicate exec subcommand")
            in_exec = True; i += 1; continue
        if token == "resume" or (in_exec and token == "resume"):
            raise HostCommandError("resume host commands cannot be inherited")
        if token == "--" or token == "-":
            raise HostCommandError(f"unsupported host argument: {token}")
        name, equals_value = _split_option(token)
        if name in ZERO_INHERIT:
            if equals_value is not None:
                raise HostCommandError(f"flag does not take a value: {name}")
            exec_args.append(name); i += 1; continue
        if name in ROOT_ZERO:
            if equals_value is not None:
                raise HostCommandError(f"flag does not take a value: {name}")
            root_args.append(name); i += 1; continue
        if name in ZERO_DROP:
            if equals_value is not None:
                raise HostCommandError(f"flag does not take a value: {name}")
            i += 1; continue
        if name in ONE_INHERIT or name in ROOT_ONE or name in ONE_DROP:
            if equals_value is None:
                if i + 1 >= len(args):
                    raise HostCommandError(f"missing value for host option: {name}")
                value = args[i + 1]; i += 2
            else:
                value = equals_value; i += 1
            if name in ROOT_ONE:
                root_args.extend([name, value])
            elif name in ONE_INHERIT:
                exec_args.extend([name, value])
            continue
        if name == "--image" or name == "-i":
            raise HostCommandError("image-bearing host commands cannot be inherited")
        if token.startswith("-"):
            raise HostCommandError(f"unknown host option: {name}")
        if not in_exec:
            raise HostCommandError("interactive host prompt cannot be inherited")
        if prompt_seen or i != len(args) - 1:
            raise HostCommandError("exec host command has ambiguous positional arguments")
        prompt_seen = True; i += 1
    return InvocationSpec(exe, tuple(root_args), tuple(exec_args), source, tuple(argv))


def _linux_snapshot(pid, proc_root="/proc"):
    base = Path(proc_root) / str(pid)
    def stat_fields():
        raw = (base / "stat").read_text()
        tail = raw[raw.rfind(")") + 2:].split()
        return int(tail[1]), tail[19]
    ppid1, start1 = stat_fields()
    executable = os.path.realpath(os.readlink(base / "exe"))
    argv = tuple(v.decode() for v in (base / "cmdline").read_bytes().split(b"\0") if v)
    ppid2, start2 = stat_fields()
    if (ppid1, start1) != (ppid2, start2) or not argv:
        raise HostCommandError(f"process changed while reading pid {pid}")
    return ProcessSnapshot(pid, ppid1, executable, argv, start1)


class _ProcBSDInfo(ctypes.Structure):
    _fields_ = [
        ("pbi_flags", ctypes.c_uint32), ("pbi_status", ctypes.c_uint32),
        ("pbi_xstatus", ctypes.c_uint32), ("pbi_pid", ctypes.c_uint32),
        ("pbi_ppid", ctypes.c_uint32), ("pbi_uid", ctypes.c_uint32),
        ("pbi_gid", ctypes.c_uint32), ("pbi_ruid", ctypes.c_uint32),
        ("pbi_rgid", ctypes.c_uint32), ("pbi_svuid", ctypes.c_uint32),
        ("pbi_svgid", ctypes.c_uint32), ("rfu_1", ctypes.c_uint32),
        ("pbi_comm", ctypes.c_char * 16), ("pbi_name", ctypes.c_char * 32),
        ("pbi_nfiles", ctypes.c_uint32), ("pbi_pgid", ctypes.c_uint32),
        ("pbi_pjobc", ctypes.c_uint32), ("e_tdev", ctypes.c_uint32),
        ("e_tpgid", ctypes.c_uint32), ("pbi_nice", ctypes.c_int32),
        ("pbi_start_tvsec", ctypes.c_uint64),
        ("pbi_start_tvusec", ctypes.c_uint64),
    ]


def parse_kern_procargs2(raw):
    if len(raw) < 5:
        raise HostCommandError("truncated KERN_PROCARGS2 buffer")
    argc = struct.unpack_from("i", raw)[0]
    if argc <= 0:
        raise HostCommandError("invalid KERN_PROCARGS2 argc")
    pos = raw.find(b"\0", 4)
    if pos < 0:
        raise HostCommandError("KERN_PROCARGS2 missing executable terminator")
    pos += 1
    while pos < len(raw) and raw[pos] == 0:
        pos += 1
    argv = []
    for _ in range(argc):
        end = raw.find(b"\0", pos)
        if end < 0:
            raise HostCommandError("truncated KERN_PROCARGS2 argv")
        argv.append(raw[pos:end].decode()); pos = end + 1
    return tuple(argv)


def _darwin_snapshot(pid):
    libproc = ctypes.CDLL(ctypes.util.find_library("proc"), use_errno=True)
    libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)
    def bsd():
        info = _ProcBSDInfo()
        got = libproc.proc_pidinfo(pid, 3, 0, ctypes.byref(info), ctypes.sizeof(info))
        if got != ctypes.sizeof(info):
            raise HostCommandError(f"proc_pidinfo failed for pid {pid}")
        return info.pbi_ppid, f"{info.pbi_start_tvsec}:{info.pbi_start_tvusec}"
    ppid1, start1 = bsd()
    path_buf = ctypes.create_string_buffer(4096)
    if libproc.proc_pidpath(pid, path_buf, len(path_buf)) <= 0:
        raise HostCommandError(f"proc_pidpath failed for pid {pid}")
    executable = os.path.realpath(path_buf.value.decode())
    mib = (ctypes.c_int * 3)(1, 49, pid)
    size = ctypes.c_size_t(0)
    if libc.sysctl(mib, 3, None, ctypes.byref(size), None, 0) != 0 or not size.value:
        raise HostCommandError(f"KERN_PROCARGS2 size failed for pid {pid}")
    buf = ctypes.create_string_buffer(size.value)
    if libc.sysctl(mib, 3, buf, ctypes.byref(size), None, 0) != 0:
        raise HostCommandError(f"KERN_PROCARGS2 read failed for pid {pid}")
    raw = bytes(buf[:size.value])
    argv = parse_kern_procargs2(raw)
    ppid2, start2 = bsd()
    if (ppid1, start1) != (ppid2, start2) or not argv:
        raise HostCommandError(f"process changed while reading pid {pid}")
    return ProcessSnapshot(pid, ppid1, executable, argv, start1)


def discover_host(start_pid=None, platform=None, snapshot_reader=None):
    platform = platform or sys.platform
    reader = snapshot_reader
    if reader is None:
        if platform.startswith("linux"):
            reader = _linux_snapshot
        elif platform == "darwin":
            reader = _darwin_snapshot
        else:
            raise HostCommandError(f"automatic Codex discovery unsupported on {platform}")
    pid = os.getppid() if start_pid is None else start_pid
    seen = set()
    while pid > 1 and pid not in seen:
        seen.add(pid)
        snap = reader(pid)
        try:
            invoked_exe = canonical_executable(snap.argv[0])
            same_binary = os.path.samefile(invoked_exe, snap.executable)
        except (HostCommandError, OSError):
            same_binary = False
        if same_binary:
            return normalize_host_argv(
                snap.argv, "linux-procfs" if platform.startswith("linux")
                else "macos-kern-procargs2", executable=invoked_exe)
        pid = snap.ppid
    raise HostCommandError("no reliable Codex process found in ancestor chain")


def resolve_invocation(template=None, environ=None, start_pid=None,
                       platform=None, snapshot_reader=None):
    env = os.environ if environ is None else environ
    if template is not None:
        for required in ("{model}", "{cwd}", "{out}"):
            if required not in template:
                raise HostCommandError(f"legacy template missing placeholder: {required}")
        tokens = shlex.split(template)
        if not tokens:
            raise HostCommandError("legacy template is empty")
        exe = canonical_executable(tokens[0], require_codex=False)
        return InvocationSpec(exe, (), (), "legacy-template", tuple(tokens), template)
    raw = env.get("MEGASTORM_CODEX_COMMAND")
    if raw is not None:
        try:
            argv = json.loads(raw)
        except ValueError as exc:
            raise HostCommandError("MEGASTORM_CODEX_COMMAND is not valid JSON") from exc
        return normalize_host_argv(argv, "environment")
    return discover_host(start_pid, platform, snapshot_reader)


def _redact_url(value):
    try:
        parts = urlsplit(value)
    except ValueError:
        return value
    if not parts.scheme or "@" not in parts.netloc:
        return value
    host = parts.netloc.rsplit("@", 1)[1]
    return urlunsplit((parts.scheme, f"<redacted>@{host}", parts.path, parts.query, parts.fragment))


def redact_argv(argv, environ=None):
    env = os.environ if environ is None else environ
    secret_values = {v for k, v in env.items() if v and SENSITIVE.search(k)}
    out, redact_next = [], False
    for token in argv:
        if redact_next:
            out.append("<redacted>"); redact_next = False; continue
        name, value = _split_option(token)
        if token.startswith("-") and SENSITIVE.search(name):
            if value is None:
                out.append(name); redact_next = True
            else:
                out.append(f"{name}=<redacted>")
            continue
        if name in ("-c", "--config"):
            if value is None:
                out.append(name); redact_next = True
            else:
                key = value.split("=", 1)[0]
                out.append(f"{name}=<redacted>" if SENSITIVE.search(key) else token)
            continue
        if token in secret_values:
            out.append("<redacted>")
        else:
            out.append(_redact_url(token))
    return out
