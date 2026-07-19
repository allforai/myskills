#!/usr/bin/env python3
"""Discover the current Codex host and build inherited, non-shell child argv."""
from dataclasses import dataclass
import hashlib
import hmac
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


ZERO_INHERIT = {"--oss", "--strict-config"}
DANGEROUS_ZERO = {
    "--dangerously-bypass-approvals-and-sandbox", "--dangerously-bypass-hook-trust",
    "--skip-git-repo-check", "--ignore-user-config", "--ignore-rules",
}
ROOT_ZERO = {"--search"}
ONE_INHERIT = {
    "-c", "--config", "--enable", "--disable", "-p", "--profile",
    "--local-provider", "--add-dir",
}
ROOT_ONE = {"-a", "--ask-for-approval"}
ZERO_DROP = {"--json", "--ephemeral", "--no-alt-screen"}
ONE_DROP = {
    "-m", "--model", "-C", "--cd", "-o", "--output-last-message",
    "--color", "--output-schema", "-s", "--sandbox",
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
    launch_prefix: tuple = ()
    argv_model: str = ""
    executable_pins: tuple = ()
    wrapper_contract_hash: str = ""
    secret_placeholders: tuple = ()
    dangerous_args: tuple = ()
    verified: bool = True
    wrapper_model_ownership: str = ""
    wrapper_model_evidence: str = ""

    def build(self, model, cwd, out, prompt, model_policy="tiered", environ=None,
              integrity_key=None, approved_argv_hmac=None, output_flags=None):
        if self.legacy_template:
            if self.verified:
                raise HostCommandError("legacy templates are not a normal verified path")
            try:
                rendered = self.legacy_template.format(model=model, cwd=str(cwd), out=str(out))
            except KeyError as exc:
                raise HostCommandError(f"unknown legacy template placeholder: {exc}") from exc
            argv = shlex.split(rendered)
            if not argv:
                raise HostCommandError("legacy template rendered an empty command")
            argv[0] = canonical_executable(argv[0], require_codex=False)
            return argv + [prompt]
        self.verify_executables()
        prefix = self._materialize_prefix(environ)
        if integrity_key is not None and approved_argv_hmac is not None:
            actual = argv_hmac(prefix, integrity_key)
            if not hmac.compare_digest(actual, approved_argv_hmac):
                raise HostCommandError("materialized wrapper argv HMAC mismatch")
        if model_policy not in {"tiered", "inherited"}:
            raise HostCommandError("unknown model policy")
        model_args = ["-m", model] if model_policy == "tiered" else []
        if model_policy == "inherited" and self.argv_model:
            model_args = ["-m", self.argv_model]
        channel = (["--output-last-message", str(out)] if output_flags is None
                   else list(output_flags))
        result_dir = str(Path(out).resolve().parent)
        return [*prefix, *self.root_args, "exec", *self.exec_args,
                "--ephemeral", *model_args, "--sandbox", "workspace-write",
                "-c", "sandbox_workspace_write.writable_roots=[]",
                "-c", "sandbox_workspace_write.exclude_tmpdir_env_var=true",
                "-c", "sandbox_workspace_write.exclude_slash_tmp=true",
                "-c", "sandbox_workspace_write.network_access=false",
                "--add-dir", result_dir,
                "-C", str(cwd),
                *channel, prompt]

    def _materialize_prefix(self, environ=None):
        env = os.environ if environ is None else environ
        if not self.launch_prefix:
            return [self.executable]
        out = []
        for token in self.launch_prefix:
            if isinstance(token, dict):
                if token.get("kind") != "env" or token.get("sensitive") is not True:
                    raise HostCommandError("invalid wrapper secret placeholder")
                name = token.get("name")
                value = env.get(name, "")
                if not value:
                    raise HostCommandError(f"missing approved wrapper secret environment: {name}")
                out.append(value)
            else:
                out.append(token)
        return out

    def materialized_discovered_argv(self, environ=None):
        if not self.secret_placeholders:
            return list(self.discovered_argv)
        env = os.environ if environ is None else environ
        values = iter(self.secret_placeholders)
        result = list(self.discovered_argv)
        # Contract validation guarantees placeholder order equals fixed-token order.
        boundary = result.index("--")
        fixed = self.launch_prefix[1:self.launch_prefix.index("--")]
        for index, declared in enumerate(fixed, 1):
            if isinstance(declared, dict):
                name = next(values)
                value = env.get(name, "")
                if not value:
                    raise HostCommandError(f"missing approved wrapper secret environment: {name}")
                result[index] = value
        return result

    def verify_executables(self):
        for path, expected in self.executable_pins:
            if file_sha256(path) != expected:
                raise HostCommandError(f"executable fingerprint drift: {path}")

    def metadata(self, environ=None):
        env = os.environ if environ is None else environ
        return {
            "source": self.source,
            "executable": self.executable,
            "discovered_argv": redact_argv(self.discovered_argv, env),
            "preserved_root_args": redact_argv(self.root_args, env),
            "preserved_exec_args": redact_argv(self.exec_args, env),
            "model_source": "argv" if self.argv_model else "default",
            "wrapper_contract_hash": self.wrapper_contract_hash,
            "verified": self.verified,
        }


def canonical_executable(value, require_codex=True):
    resolved = value if os.path.isabs(value) else shutil.which(value)
    if not resolved:
        raise HostCommandError(f"executable cannot be resolved: {value}")
    if require_codex and os.path.basename(resolved) != "codex":
        raise HostCommandError("resolved host executable is not codex")
    return os.path.realpath(resolved)


def file_sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def argv_hmac(argv, key):
    payload = json.dumps(list(argv), ensure_ascii=False, separators=(",", ":")).encode()
    return hmac.new(key if isinstance(key, bytes) else key.encode(), payload,
                    hashlib.sha256).hexdigest()


def _split_option(token):
    if token.startswith("--") and "=" in token:
        return token.split("=", 1)
    return token, None


def _canonical_contract(contract):
    return json.dumps(contract, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _wrapper_prefix(argv, contract, environ):
    if not isinstance(contract, dict) or contract.get("schema_version") != 1:
        raise HostCommandError("wrapper replay requires a versioned contract")
    if contract.get("replay_safe") is not True:
        raise HostCommandError("wrapper contract is not replay-safe")
    if not contract.get("wrapper_version") or not contract.get("model_evidence"):
        raise HostCommandError("wrapper contract lacks version/model evidence")
    boundary = contract.get("child_boundary_index")
    if not isinstance(boundary, int) or boundary <= 0 or boundary >= len(argv) - 1:
        raise HostCommandError("invalid wrapper child boundary")
    if argv[boundary] != "--":
        raise HostCommandError("wrapper boundary mismatch")
    wrapper = canonical_executable(argv[0], require_codex=False)
    codex = canonical_executable(argv[boundary + 1])
    if wrapper != canonical_executable(contract.get("wrapper_path", ""), require_codex=False):
        raise HostCommandError("wrapper path does not match contract")
    if codex != canonical_executable(contract.get("codex_path", "")):
        raise HostCommandError("Codex path does not match wrapper contract")
    fixed = contract.get("fixed_wrapper_args")
    if not isinstance(fixed, list) or len(fixed) != boundary - 1:
        raise HostCommandError("wrapper fixed-token arity mismatch")
    arities = contract.get("fixed_wrapper_arities")
    if (not isinstance(arities, list) or len(arities) != len(fixed) or
            any(not isinstance(value, int) or value < 0 for value in arities)):
        raise HostCommandError("wrapper option arity contract is invalid")
    materialized, placeholders = [wrapper], []
    env = os.environ if environ is None else environ
    for observed, declared in zip(argv[1:boundary], fixed):
        if isinstance(declared, str):
            if observed != declared:
                raise HostCommandError("wrapper fixed token mismatch")
            materialized.append(declared)
        elif isinstance(declared, dict):
            if declared.get("kind") != "env" or declared.get("sensitive") is not True:
                raise HostCommandError("invalid typed wrapper placeholder")
            name = declared.get("name")
            if not isinstance(name, str) or not env.get(name) or observed != env[name]:
                raise HostCommandError("wrapper secret substitution mismatch")
            materialized.append(dict(declared)); placeholders.append(name)
        else:
            raise HostCommandError("invalid wrapper contract token")
    pins = []
    for path, field in ((wrapper, "wrapper_sha256"), (codex, "codex_sha256")):
        expected = contract.get(field)
        if not isinstance(expected, str) or not hmac.compare_digest(file_sha256(path), expected):
            raise HostCommandError(f"wrapper contract executable pin mismatch: {field}")
        pins.append((path, expected))
    ownership = contract.get("model_ownership")
    if ownership not in {"locked", "unlocked", "unknown"}:
        raise HostCommandError("invalid wrapper model ownership")
    return (tuple([*materialized, "--", codex]), argv[boundary + 2:], codex,
            tuple(pins), hashlib.sha256(_canonical_contract(contract).encode()).hexdigest(),
            tuple(placeholders), ownership, contract["model_evidence"])


def normalize_host_argv(argv, source, executable=None, wrapper_contract=None,
                        environ=None, capability_approvals=()):
    if not argv or not all(isinstance(v, str) and v for v in argv):
        raise HostCommandError("host argv must be a non-empty string array")
    argv = list(argv)
    if "--" in argv or wrapper_contract is not None:
        if executable is not None:
            raise HostCommandError("wrapper discovery cannot override executable identity")
        (prefix, child_args, exe, pins, contract_hash, placeholders,
         wrapper_ownership, wrapper_evidence) = _wrapper_prefix(
            argv, wrapper_contract, environ)
        args = list(child_args)
    else:
        exe = canonical_executable(executable or argv[0])
        prefix, pins, contract_hash, placeholders = (exe,), ((exe, file_sha256(exe)),), "", ()
        wrapper_ownership, wrapper_evidence = "", ""
        args = list(argv[1:])
    root_args, exec_args = [], []
    dangerous_args, argv_model = [], ""
    approvals = set(capability_approvals)
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
        if name in DANGEROUS_ZERO:
            if equals_value is not None:
                raise HostCommandError(f"flag does not take a value: {name}")
            if name not in approvals:
                raise HostCommandError(f"dangerous host capability not approved: {name}")
            dangerous_args.append(name); i += 1; continue
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
            elif name in ("-m", "--model"):
                if argv_model:
                    raise HostCommandError("multiple host model flags")
                argv_model = value
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
    return InvocationSpec(
        exe, tuple(root_args), tuple(exec_args), source, tuple(argv),
        launch_prefix=prefix, argv_model=argv_model, executable_pins=pins,
        wrapper_contract_hash=contract_hash, secret_placeholders=placeholders,
        dangerous_args=tuple(dangerous_args), wrapper_model_ownership=wrapper_ownership,
        wrapper_model_evidence=wrapper_evidence)


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


def discover_host(start_pid=None, platform=None, snapshot_reader=None,
                  wrapper_contract=None, environ=None, capability_approvals=()):
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
            invoked_exe = canonical_executable(snap.argv[0], require_codex=False)
            same_binary = os.path.samefile(invoked_exe, snap.executable)
        except (HostCommandError, OSError):
            same_binary = False
        if same_binary and os.path.basename(snap.argv[0]) == "codex":
            return normalize_host_argv(
                snap.argv, "linux-procfs" if platform.startswith("linux")
                else "macos-kern-procargs2")
        if same_binary and wrapper_contract is not None:
            try:
                return normalize_host_argv(
                    snap.argv, "linux-procfs" if platform.startswith("linux")
                    else "macos-kern-procargs2", wrapper_contract=wrapper_contract,
                    environ=environ, capability_approvals=capability_approvals)
            except HostCommandError:
                pass
        pid = snap.ppid
    raise HostCommandError("no reliable Codex process found in ancestor chain")


def resolve_invocation(template=None, environ=None, start_pid=None,
                       platform=None, snapshot_reader=None, wrapper_contract=None,
                       capability_approvals=(), allow_unsafe_template=False,
                       legacy_model_policy="tiered"):
    env = os.environ if environ is None else environ
    if template is not None:
        # Supplying the separately named template input is the legacy unsafe
        # opt-in. The resulting invocation remains permanently unverified.
        required_fields = ["{cwd}", "{out}"]
        if legacy_model_policy == "tiered":
            required_fields.append("{model}")
        elif legacy_model_policy != "inherited":
            raise HostCommandError("legacy template has invalid model policy")
        for required in required_fields:
            if required not in template:
                raise HostCommandError(f"legacy template missing placeholder: {required}")
        tokens = shlex.split(template)
        if not tokens:
            raise HostCommandError("legacy template is empty")
        exe = canonical_executable(tokens[0], require_codex=False)
        return InvocationSpec(exe, (), (), "legacy-template", tuple(tokens), template,
                              verified=False)
    raw = env.get("MEGASTORM_CODEX_COMMAND")
    if raw is not None:
        try:
            argv = json.loads(raw)
        except ValueError as exc:
            raise HostCommandError("MEGASTORM_CODEX_COMMAND is not valid JSON") from exc
        contract = wrapper_contract
        if contract is None and env.get("MEGASTORM_CODEX_WRAPPER_CONTRACT"):
            try:
                contract = json.loads(env["MEGASTORM_CODEX_WRAPPER_CONTRACT"])
            except ValueError as exc:
                raise HostCommandError("wrapper contract is not valid JSON") from exc
        return normalize_host_argv(argv, "environment", wrapper_contract=contract,
                                   environ=env, capability_approvals=capability_approvals)
    return discover_host(start_pid, platform, snapshot_reader, wrapper_contract,
                         env, capability_approvals)


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
