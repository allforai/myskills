import json
import os
from pathlib import Path
import struct
import tempfile
import unittest

from host_command import (HostCommandError, ProcessSnapshot, _linux_snapshot,
                          discover_host, normalize_host_argv, parse_kern_procargs2,
                          redact_argv, resolve_invocation)


class HostCommandTests(unittest.TestCase):
    def _codex_link(self, td):
        target = Path(td, "codex-aarch64-apple-darwin")
        target.write_text("binary"); target.chmod(0o755)
        link = Path(td, "codex"); link.symlink_to(target)
        return link, target

    def test_inherits_permissions_profile_config_and_replaces_task_options(self):
        with tempfile.TemporaryDirectory() as td:
            codex, _ = self._codex_link(td)
            spec = normalize_host_argv([
                str(codex), "-a", "never", "--search", "--profile", "team", "-c", "x=1",
                "--dangerously-bypass-approvals-and-sandbox", "-m", "old",
                "-C", "/old", "--color=always"], "fixture")
            child = spec.build("new", "/new path", "/tmp/out", "do work")
            self.assertEqual(child[:5], [str(codex), "-a", "never", "--search", "exec"])
            self.assertIn("--profile", child); self.assertIn("team", child)
            self.assertIn("--dangerously-bypass-approvals-and-sandbox", child)
            self.assertNotIn("old", child); self.assertNotIn("/old", child)
            self.assertEqual(child.count("-m"), 1); self.assertEqual(child.count("-C"), 1)
            self.assertEqual(child[-1], "do work")

    def test_exec_prompt_removed_and_resume_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            codex, _ = self._codex_link(td)
            spec = normalize_host_argv([str(codex), "exec", "--json", "old prompt"],
                                       "fixture")
            self.assertNotIn("old prompt", spec.build("m", td, "/tmp/o", "new"))
            with self.assertRaises(HostCommandError):
                normalize_host_argv([str(codex), "resume", "latest"], "fixture")

    def test_unknown_ambiguous_and_stdin_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            codex, _ = self._codex_link(td)
            for argv in ([str(codex), "--future-option"],
                         [str(codex), "interactive prompt"],
                         [str(codex), "exec", "-"],
                         [str(codex), "exec", "one", "two"]):
                with self.assertRaises(HostCommandError, msg=argv):
                    normalize_host_argv(argv, "fixture")

    def test_environment_override_requires_json_string_array_and_codex(self):
        with tempfile.TemporaryDirectory() as td:
            codex, _ = self._codex_link(td)
            spec = resolve_invocation(environ={"MEGASTORM_CODEX_COMMAND": json.dumps(
                [str(codex), "--sandbox=read-only"])})
            self.assertEqual(spec.source, "environment")
            for raw in ("not-json", '"codex"', "[]", '["/bin/echo"]'):
                with self.assertRaises(HostCommandError, msg=raw):
                    resolve_invocation(environ={"MEGASTORM_CODEX_COMMAND": raw})

    def test_legacy_template_is_explicit_absolute_non_shell_argv(self):
        spec = resolve_invocation(template="/bin/echo {model} {cwd} {out}", environ={})
        argv = spec.build("m", "/with space", "/tmp/o", "prompt with space")
        self.assertEqual(argv[0], "/bin/echo")
        self.assertEqual(argv[-1], "prompt with space")
        self.assertEqual(spec.source, "legacy-template")

    def test_redaction_covers_config_url_and_environment_secret(self):
        argv = ["codex", "--config=service.api_key=abc", "--endpoint",
                "https://user:pass@example.com/x", "literal-secret"]
        redacted = redact_argv(argv, {"MY_TOKEN": "literal-secret"})
        joined = " ".join(redacted)
        self.assertNotIn("abc", joined); self.assertNotIn("user:pass", joined)
        self.assertNotIn("literal-secret", joined)

    def test_kern_procargs2_parser_preserves_argument_boundaries(self):
        args = [b"codex", b"--profile", b"team name"]
        raw = struct.pack("i", len(args)) + b"/path/codex\0\0" + b"\0".join(args) + b"\0"
        self.assertEqual(parse_kern_procargs2(raw), tuple(a.decode() for a in args))
        with self.assertRaises(HostCommandError):
            parse_kern_procargs2(raw[:-1])

    def test_linux_proc_snapshot_uses_exe_cmdline_and_stable_start(self):
        with tempfile.TemporaryDirectory() as td:
            proc = Path(td, "42"); proc.mkdir()
            _, target = self._codex_link(td)
            (proc / "exe").symlink_to(target)
            tail = ["S", "7"] + ["0"] * 17 + ["123"]
            (proc / "stat").write_text("42 (codex) " + " ".join(tail))
            (proc / "cmdline").write_bytes(b"codex\0--profile\0team\0")
            snap = _linux_snapshot(42, td)
            self.assertEqual(snap.ppid, 7); self.assertEqual(snap.start_token, "123")
            self.assertEqual(snap.argv[-1], "team")

    def test_ancestor_discovery_requires_argv0_and_exe_same_file(self):
        with tempfile.TemporaryDirectory() as td:
            link, target = self._codex_link(td)
            snapshots = {
                30: ProcessSnapshot(30, 20, "/bin/zsh", ("zsh",), "a"),
                20: ProcessSnapshot(20, 1, str(target), (str(link), "--profile", "p"), "b"),
            }
            spec = discover_host(30, "darwin", snapshots.__getitem__)
            self.assertEqual(spec.executable, str(link))
            self.assertEqual(spec.source, "macos-kern-procargs2")


if __name__ == "__main__":
    unittest.main()
