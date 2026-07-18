#!/usr/bin/env python3
"""Fail-closed Grok host discovery and effective-security validation."""
from dataclasses import dataclass
import ctypes
import ctypes.util
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import struct
import sys
from urllib.parse import urlsplit, urlunsplit


class HostCommandError(RuntimeError):
    pass


SENSITIVE = re.compile(
    r"(?:^|[._-])(token|secret|password|api[_-]?key|apikey|authorization|credential)(?:$|[._-])",
    re.IGNORECASE,
)
ZERO_SAFE = {"--no-auto-update", "--no-alt-screen", "--disable-web-search", "--no-memory"}
ONE_SAFE = {"-m", "--model", "--effort", "--profile", "--config", "--plugin-dir"}
ZERO_DROP = {"--no-auto-update", "--no-alt-screen"}
ONE_DROP = {
    "-p", "--single", "--cwd", "-s", "--session-id", "-r", "--resume",
    "--output-format", "-w", "--worktree", "--ref",
}
ZERO_REJECT = {
    "--always-approve", "--yolo", "--dangerously-skip-permissions",
    "--continue", "-c", "--fork-session",
}
ONE_SECURITY = {
    "--allow", "--deny", "--sandbox", "--tools", "--disallowed-tools",
    "--rules", "--system-prompt-override", "--system-prompt",
    "--append-system-prompt", "--allowedTools", "--disallowedTools",
}
NETWORK_KEYS = {"network", "web", "web_search", "web-search"}


@dataclass(frozen=True)
class ProcessSnapshot:
    pid: int
    ppid: int
    executable: str
    argv: tuple
    start_token: str


@dataclass(frozen=True)
class ProbeResult:
    verified: bool
    identity: str = ""
    version: str = ""
    capabilities: tuple = ()
    reason: str = ""
    executable_identity: tuple = ()
    executable_sha256: str = ""
    launcher_identities: tuple = ()
    launcher_sha256s: tuple = ()


@dataclass(frozen=True)
class InvocationSpec:
    launcher: tuple
    safe_args: tuple
    security_args: tuple
    source: str
    discovered_argv: tuple
    probe: ProbeResult

    @property
    def verified(self):
        return self.probe.verified

    def build(self, model, cwd, prompt, security_args=()):
        if not self.verified:
            raise HostCommandError("Grok host identity/capabilities are unverified")
        if self.probe.executable_identity:
            current = executable_identity(self.launcher[-1])
            if current != self.probe.executable_identity:
                raise HostCommandError("Grok executable changed after capability probe")
        if self.probe.executable_sha256 and _file_sha256(self.launcher[-1]) != self.probe.executable_sha256:
            raise HostCommandError("Grok executable content changed after capability probe")
        executables = launcher_executables(self.launcher)
        if self.probe.launcher_identities:
            current = tuple(executable_identity(path) for path in executables)
            if current != self.probe.launcher_identities:
                raise HostCommandError("Grok wrapper or executable changed after capability probe")
        if self.probe.launcher_sha256s:
            current = tuple(_file_sha256(path) for path in executables)
            if current != self.probe.launcher_sha256s:
                raise HostCommandError("Grok wrapper or executable content changed after capability probe")
        return [
            *self.launcher, *self.safe_args, *self.security_args, *security_args,
            "--no-auto-update", "--cwd", str(cwd), "-m", model,
            "-p", prompt, "--output-format", "streaming-json",
        ]

    def metadata(self, environ=None):
        return {
            "source": self.source,
            "verified": self.verified,
            "identity": self.probe.identity,
            "version": self.probe.version,
            "executable_sha256": self.probe.executable_sha256,
            "reason": self.probe.reason,
            "discovered_argv": redact_argv(self.discovered_argv, environ),
            "safe_args": redact_argv(self.safe_args, environ),
            "security_args": redact_argv(self.security_args, environ),
        }


def _split_option(token):
    if token.startswith("--") and "=" in token:
        return token.split("=", 1)
    return token, None


def canonical_executable(value):
    resolved = value if os.path.isabs(value) else shutil.which(value)
    if not resolved:
        raise HostCommandError(f"executable cannot be resolved: {value}")
    return os.path.realpath(resolved)


def launcher_executables(launcher):
    """Return wrapper and official executable from the approved launcher grammar."""
    if "--" not in launcher:
        return (canonical_executable(launcher[0]),)
    boundary = launcher.index("--")
    if boundary < 1 or boundary + 1 >= len(launcher):
        raise HostCommandError("invalid wrapper child-command boundary")
    return (canonical_executable(launcher[0]), canonical_executable(launcher[boundary + 1]))


def executable_identity(path):
    """Return a stable-enough local file identity for probe/launch TOCTOU checks."""
    try:
        stat = os.stat(path)
    except OSError as exc:
        raise HostCommandError(f"cannot stat Grok executable: {path}") from exc
    return (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns)


def _run_probe(argv, runner, timeout):
    try:
        result = runner(
            argv, stdin=subprocess.DEVNULL, capture_output=True, text=True,
            timeout=timeout, check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise HostCommandError(f"Grok capability probe failed: {argv[-1]}") from exc
    output = f"{result.stdout or ''}\n{result.stderr or ''}"
    if result.returncode != 0:
        raise HostCommandError(f"Grok capability probe returned {result.returncode}: {argv[-1]}")
    return output


def _file_sha256(path):
    digest = hashlib.sha256()
    try:
        with open(path, "rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise HostCommandError(f"cannot hash executable or referenced file: {path}") from exc
    return digest.hexdigest()


def probe_official_grok(launcher, runner=subprocess.run, timeout=5,
                        trusted_sha256=None, trusted_wrapper_sha256=None, environ=None):
    """Probe the unauthenticated documented Grok Build command surface."""
    if not launcher:
        raise HostCommandError("empty launcher for Grok capability probe")
    executables = launcher_executables(launcher)
    executable = executables[-1]
    identity = executable_identity(executable)
    env = os.environ if environ is None else environ
    trusted = trusted_sha256 or env.get("MEGASTORM_GROK_SHA256")
    wrapper_trusted = trusted_wrapper_sha256 or env.get("MEGASTORM_GROK_WRAPPER_SHA256")
    actual_sha256 = _file_sha256(executable)
    launcher_identities = tuple(executable_identity(path) for path in executables)
    launcher_sha256s = tuple(_file_sha256(path) for path in executables)
    commands = {
        "version": [*launcher, "version"],
        "help": [*launcher, "--help"],
        "inspect": [*launcher, "inspect", "--help"],
        "plugin": [*launcher, "plugin", "validate", "--help"],
    }
    outputs = {name: _run_probe(argv, runner, timeout) for name, argv in commands.items()}
    version = outputs["version"].strip()
    combined = "\n".join(outputs.values()).lower()
    required_markers = {
        "single": ("-p", "--single"),
        "stream": ("streaming-json", "--output-format"),
        "inspect": ("inspect", "--json"),
        "plugin": ("plugin", "validate"),
    }
    missing = [label for label, choices in required_markers.items()
               if not any(choice in combined for choice in choices)]
    if "grok" not in combined or "build" not in combined:
        missing.append("Grok Build identity")
    if not trusted:
        missing.append("trusted executable SHA-256 pin")
    elif not re.fullmatch(r"[0-9a-fA-F]{64}", trusted) or actual_sha256 != trusted.lower():
        missing.append("trusted executable SHA-256 mismatch")
    if len(executables) == 2:
        if not wrapper_trusted:
            missing.append("trusted wrapper SHA-256 pin")
        elif (not re.fullmatch(r"[0-9a-fA-F]{64}", wrapper_trusted) or
              launcher_sha256s[0] != wrapper_trusted.lower()):
            missing.append("trusted wrapper SHA-256 mismatch")
    if missing or "grok" not in version.lower():
        return ProbeResult(
            False, reason="capability probe did not identify official Grok Build: " +
            ", ".join(missing or ["version identity"]), executable_identity=identity,
            executable_sha256=actual_sha256,
            launcher_identities=launcher_identities, launcher_sha256s=launcher_sha256s,
        )
    return ProbeResult(
        True, "official Grok Build", version,
        ("version", "help", "inspect-json", "plugin-validate", "streaming-json"),
        executable_identity=identity, executable_sha256=actual_sha256,
        launcher_identities=launcher_identities, launcher_sha256s=launcher_sha256s,
    )


def _take_value(args, index, name, equals_value):
    if equals_value is not None:
        return equals_value, index + 1
    if index + 1 >= len(args):
        raise HostCommandError(f"missing value for host option: {name}")
    return args[index + 1], index + 2


def normalize_host_argv(argv, source="explicit", identity_probe=None):
    """Normalize a direct Grok invocation; verification is exclusively injected."""
    if not isinstance(argv, list) or not argv or not all(isinstance(x, str) and x for x in argv):
        raise HostCommandError("host argv must be a non-empty JSON string array")
    first = canonical_executable(argv[0])
    if "--" in argv:
        boundary = argv.index("--")
        if boundary < 1 or boundary + 1 >= len(argv):
            raise HostCommandError("invalid wrapper child-command boundary")
        wrapper_args = argv[1:boundary]
        for token in wrapper_args:
            name, _ = _split_option(token)
            if (not token.startswith("-") or name in ZERO_REJECT or name in ONE_DROP or
                    name in ONE_SECURITY or name in {"--cwd", "--model", "-m"}):
                raise HostCommandError("wrapper fixed arguments contain prompt/security injection")
        child = canonical_executable(argv[boundary + 1])
        if os.path.basename(child) != "grok":
            raise HostCommandError("wrapper boundary must resolve to the official grok executable")
        launcher = (first, *wrapper_args, "--", child)
        args = argv[boundary + 2:]
    else:
        if os.path.basename(first) != "grok":
            raise HostCommandError("direct launcher must resolve to grok; grx requires a wrapper boundary")
        launcher = (first,)
        args = argv[1:]
    safe, security = [], []
    i = 0
    while i < len(args):
        token = args[i]
        name, equals_value = _split_option(token)
        if name in ZERO_REJECT:
            raise HostCommandError(f"unsafe or session-bearing host option: {name}")
        if name in ZERO_DROP:
            i += 1
            continue
        if name in ONE_DROP:
            _, i = _take_value(args, i, name, equals_value)
            continue
        if name in ZERO_SAFE:
            if equals_value is not None:
                raise HostCommandError(f"flag does not take a value: {name}")
            safe.append(name); i += 1; continue
        if name in ONE_SECURITY:
            raise HostCommandError(f"security/system-prompt host option is not inheritable: {name}")
        if name in ONE_SAFE:
            value, i = _take_value(args, i, name, equals_value)
            safe.extend((name, value))
            continue
        if token == "--" or not token.startswith("-"):
            raise HostCommandError("prompt, subcommand, or wrapper boundary is not inheritable")
        raise HostCommandError(f"unknown host option: {name}")
    if identity_probe is None:
        probe = ProbeResult(False, reason="no real Grok identity/capability probe supplied")
    else:
        probe = identity_probe(launcher)
        if not isinstance(probe, ProbeResult):
            raise HostCommandError("identity probe returned an invalid result")
        required = {"version", "help", "inspect-json", "plugin-validate", "streaming-json"}
        if probe.verified and ("grok" not in probe.identity.lower() or
                               not required.issubset(set(probe.capabilities))):
            raise HostCommandError("identity probe did not prove the official Grok command surface")
    return InvocationSpec(launcher, tuple(safe), tuple(security), source, tuple(argv), probe)


def _linux_snapshot(pid, proc_root="/proc"):
    base = Path(proc_root) / str(pid)

    def stat_fields():
        raw = (base / "stat").read_text()
        tail = raw[raw.rfind(")") + 2:].split()
        return int(tail[1]), tail[19]

    try:
        ppid1, start1 = stat_fields()
        executable = os.path.realpath(os.readlink(base / "exe"))
        argv = tuple(part.decode() for part in (base / "cmdline").read_bytes().split(b"\0") if part)
        ppid2, start2 = stat_fields()
    except (OSError, UnicodeError, ValueError, IndexError) as exc:
        raise HostCommandError(f"cannot inspect process {pid}") from exc
    if (ppid1, start1) != (ppid2, start2) or not argv:
        raise HostCommandError(f"process changed while reading pid {pid}")
    return ProcessSnapshot(pid, ppid1, executable, argv, start1)


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
        try:
            argv.append(raw[pos:end].decode())
        except UnicodeError as exc:
            raise HostCommandError("invalid KERN_PROCARGS2 argv encoding") from exc
        pos = end + 1
    return tuple(argv)


def _darwin_snapshot(pid, kernel_reader=None):
    """Read lossless Darwin argv; callers must explicitly choose ps fallback."""
    if kernel_reader is not None:
        result = kernel_reader(pid)
        if not isinstance(result, ProcessSnapshot):
            raise HostCommandError("invalid injected KERN_PROCARGS2 snapshot")
        return result
    libproc_name, libc_name = ctypes.util.find_library("proc"), ctypes.util.find_library("c")
    if not libproc_name or not libc_name:
        raise HostCommandError("KERN_PROCARGS2 unavailable; explicit ps fallback required")
    libproc, libc = ctypes.CDLL(libproc_name, use_errno=True), ctypes.CDLL(libc_name, use_errno=True)
    # PROC_PIDTBSDINFO starts with flags/status/xstatus/pid/ppid.
    info = (ctypes.c_uint32 * 34)()
    got = libproc.proc_pidinfo(pid, 3, 0, ctypes.byref(info), ctypes.sizeof(info))
    if got < 20:
        raise HostCommandError(f"proc_pidinfo failed for pid {pid}")
    ppid1 = int(info[4])
    path_buf = ctypes.create_string_buffer(4096)
    if libproc.proc_pidpath(pid, path_buf, len(path_buf)) <= 0:
        raise HostCommandError(f"proc_pidpath failed for pid {pid}")
    executable = os.path.realpath(path_buf.value.decode())
    mib = (ctypes.c_int * 3)(1, 49, pid)
    size = ctypes.c_size_t(0)
    if libc.sysctl(mib, 3, None, ctypes.byref(size), None, 0) != 0 or not size.value:
        raise HostCommandError("KERN_PROCARGS2 unavailable; explicit ps fallback required")
    buf = ctypes.create_string_buffer(size.value)
    if libc.sysctl(mib, 3, buf, ctypes.byref(size), None, 0) != 0:
        raise HostCommandError(f"KERN_PROCARGS2 read failed for pid {pid}")
    argv = parse_kern_procargs2(bytes(buf[:size.value]))
    info2 = (ctypes.c_uint32 * 34)()
    if libproc.proc_pidinfo(pid, 3, 0, ctypes.byref(info2), ctypes.sizeof(info2)) < 20:
        raise HostCommandError(f"proc_pidinfo recheck failed for pid {pid}")
    if ppid1 != int(info2[4]):
        raise HostCommandError(f"process changed while reading pid {pid}")
    return ProcessSnapshot(pid, ppid1, executable, argv, "kern-procargs2")


def _ps_snapshot(pid, runner=subprocess.run):
    """Portable fallback for platforms without procfs; deliberately strict."""
    try:
        result = runner(
            ["ps", "-p", str(pid), "-o", "ppid=", "-o", "lstart=", "-o", "command="],
            stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=3, check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise HostCommandError(f"cannot inspect process {pid} with ps") from exc
    if result.returncode != 0 or not result.stdout.strip():
        raise HostCommandError(f"ps could not read process {pid}")
    line = result.stdout.strip()
    match = re.match(r"\s*(\d+)\s+(.{24})\s+(.+)$", line)
    if not match:
        raise HostCommandError(f"unparseable ps record for process {pid}")
    try:
        argv = tuple(shlex.split(match.group(3)))
    except ValueError as exc:
        raise HostCommandError(f"unparseable argv for process {pid}") from exc
    if not argv:
        raise HostCommandError(f"empty argv for process {pid}")
    executable = canonical_executable(argv[0])
    return ProcessSnapshot(pid, int(match.group(1)), executable, argv, match.group(2).strip())


def discover_host(start_pid=None, platform=None, snapshot_reader=None, identity_probe=None):
    """Find the nearest direct Grok/grx ancestor and verify its real command surface."""
    platform = platform or sys.platform
    if snapshot_reader is None:
        if platform.startswith("linux"):
            snapshot_reader = _linux_snapshot
        elif platform == "darwin":
            snapshot_reader = _darwin_snapshot
        else:
            raise HostCommandError(
                f"automatic Grok discovery unsupported on {platform}; explicit ps fallback required")
    pid = os.getppid() if start_pid is None else start_pid
    seen = set()
    while pid > 1 and pid not in seen:
        seen.add(pid)
        snap = snapshot_reader(pid)
        basename = os.path.basename(snap.executable)
        if basename in {"grok", "grx"}:
            try:
                invoked = canonical_executable(snap.argv[0])
                same = os.path.samefile(invoked, snap.executable)
            except (HostCommandError, OSError):
                same = False
            if same:
                return normalize_host_argv(
                    list(snap.argv), "process-ancestry",
                    identity_probe or probe_official_grok,
                )
        pid = snap.ppid
    raise HostCommandError("no trustworthy Grok process found in ancestor chain")


def resolve_invocation(environ=None, identity_probe=None, discoverer=None):
    env = os.environ if environ is None else environ
    probe = identity_probe or (lambda launcher: probe_official_grok(launcher, environ=env))
    raw = env.get("MEGASTORM_GROK_COMMAND")
    if raw is not None:
        try:
            argv = json.loads(raw)
        except (TypeError, ValueError) as exc:
            raise HostCommandError("MEGASTORM_GROK_COMMAND is not valid JSON") from exc
        return normalize_host_argv(argv, "environment", probe)
    if discoverer is not None:
        argv = discoverer()
        if argv is None:
            raise HostCommandError("no trustworthy Grok command found in process ancestry")
        return normalize_host_argv(
            list(argv), "process-ancestry", probe)
    return discover_host(identity_probe=probe)


def validate_effective_configuration(config, worktree, approved=None):
    """Pure validation of resolved ``grok inspect --json``-style security data."""
    if not isinstance(config, dict):
        raise HostCommandError("effective configuration must be an object")
    approved = {} if approved is None else approved
    if not isinstance(approved, dict):
        raise HostCommandError("approved capability envelope must be an object")
    root = Path(worktree).resolve()
    violations = []

    def enabled(value):
        return value not in (None, False, "", [], {})

    def entries(key):
        value = config.get(key, [])
        if isinstance(value, dict):
            return [(str(k), v) for k, v in value.items() if enabled(v)]
        if isinstance(value, list):
            return [(str(v.get("name", i)) if isinstance(v, dict) else str(v), v)
                    for i, v in enumerate(value) if enabled(v)]
        return [(str(value), value)] if enabled(value) else []

    permission = str(config.get("permission_mode", "")).lower()
    if config.get("always_approve") is True or permission in {"always-approve", "yolo", "bypass"}:
        violations.append("approval bypass is enabled")
    for key, approval_key in (("hooks", "hooks"), ("mcp_servers", "mcps"),
                              ("plugins", "plugins"), ("tools", "tools")):
        allowed = set(approved.get(approval_key, []))
        for name, _ in entries(key):
            if name not in allowed:
                violations.append(f"undeclared {key}: {name}")
    if enabled(config.get("auth_provider_command")):
        violations.append("external auth provider command is enabled")
    for key in NETWORK_KEYS:
        if config.get(key) is True and not approved.get("network", False):
            violations.append(f"undeclared network capability: {key}")
    if config.get("memory") is True and not approved.get("memory", False):
        violations.append("undeclared memory capability")
    for raw_path in config.get("writable_paths", []):
        try:
            candidate = Path(raw_path).resolve()
            candidate.relative_to(root)
        except (OSError, ValueError):
            violations.append(f"writable path outside worktree: {raw_path}")
    for _, mcp in entries("mcp_servers"):
        if isinstance(mcp, dict):
            for raw_path in mcp.get("writable_paths", mcp.get("roots", [])):
                try:
                    Path(raw_path).resolve().relative_to(root)
                except (OSError, ValueError):
                    violations.append(f"MCP path outside worktree: {raw_path}")
    if violations:
        raise HostCommandError("unsafe effective Grok configuration: " + "; ".join(sorted(set(violations))))
    canonical = json.dumps(config, sort_keys=True, separators=(",", ":"), default=str)
    return {"verified": True, "fingerprint": hashlib.sha256(canonical.encode()).hexdigest()}


def _default_inspect_resolver(argv):
    try:
        result = subprocess.run(
            argv, stdin=subprocess.DEVNULL, capture_output=True, text=True,
            timeout=10, check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise HostCommandError("Grok inspect --json failed") from exc
    if result.returncode != 0:
        raise HostCommandError(f"Grok inspect --json returned {result.returncode}")
    return result.stdout


def _canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _reported_security_files(config):
    """Collect every reported security/control source path from inspect data."""
    found = set()
    security_contexts = (
        "config", "plugin", "hook", "requirement", "mcp", "credential", "auth",
        "managed", "user", "project", "profile", "command_source", "provider",
        "tool", "policy", "permission", "sandbox", "memory", "system_prompt",
        "instruction", "network", "web", "secret", "certificate", "tls",
    )
    path_contexts = ("path", "file", "source", "root", "manifest")

    def walk(value, context=""):
        if isinstance(value, dict):
            for key, child in value.items():
                lowered = key.lower().replace("-", "_")
                next_context = f"{context}.{lowered}" if context else lowered
                relevant = any(word in next_context for word in security_contexts)
                pathish = any(word in lowered for word in path_contexts)
                if relevant and pathish and isinstance(child, str):
                    found.add(child)
                else:
                    walk(child, next_context)
        elif isinstance(value, list):
            for child in value:
                if (isinstance(child, str) and
                        any(word in context for word in security_contexts) and
                        any(word in context for word in path_contexts)):
                    found.add(child)
                else:
                    walk(child, context)

    walk(config)
    return found


def resolve_effective_configuration(invocation, cwd, approved=None,
                                    phase0_artifact=None, resolver=None):
    """Resolve, bind, fingerprint, then validate the launcher's actual configuration."""
    if not invocation.verified:
        raise HostCommandError("cannot inspect configuration through an unverified Grok launcher")
    inspect_argv = [*invocation.launcher, *invocation.safe_args,
                    "--cwd", str(Path(cwd).resolve()), "inspect", "--json"]
    raw = (resolver or _default_inspect_resolver)(tuple(inspect_argv))
    if hasattr(raw, "returncode"):
        if raw.returncode != 0:
            raise HostCommandError(f"Grok inspect --json returned {raw.returncode}")
        raw = raw.stdout
    try:
        actual = json.loads(raw) if isinstance(raw, str) else raw
    except (TypeError, ValueError) as exc:
        raise HostCommandError("Grok inspect --json returned malformed JSON") from exc
    if not isinstance(actual, dict):
        raise HostCommandError("Grok inspect --json must return an object")
    if phase0_artifact is not None:
        expected = phase0_artifact.get("effective_configuration", phase0_artifact)
        if not isinstance(expected, dict) or _canonical_json(expected) != _canonical_json(actual):
            raise HostCommandError("Phase 0 effective-configuration artifact does not match Grok inspect")
    referenced = {}
    for reported in sorted(_reported_security_files(actual)):
        path = Path(reported).expanduser().resolve()
        if not path.is_file():
            raise HostCommandError(f"reported configuration/plugin/hook file is unreadable: {reported}")
        referenced[str(path)] = _file_sha256(path)
    validated = validate_effective_configuration(actual, cwd, approved)
    binding = _canonical_json({"inspect": actual, "referenced_files": referenced})
    return {
        **validated,
        "inspect_argv": redact_argv(inspect_argv),
        "resolved_fingerprint": hashlib.sha256(binding.encode()).hexdigest(),
        "referenced_files": referenced,
    }


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
        elif token in secret_values:
            out.append("<redacted>")
        else:
            out.append(_redact_url(token))
    return out
