#!/usr/bin/env python3
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest
from types import SimpleNamespace

import host_command as hc


CAPS = ("version", "help", "inspect-json", "plugin-validate", "streaming-json")


def verified_probe(_launcher):
    return hc.ProbeResult(True, "official Grok Build", "grok 1.2.3", CAPS)


class HostCommandTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.bin = Path(self.tmp.name) / "grok"
        self.bin.write_text("#!/bin/sh\n")
        self.bin.chmod(0o755)

    def tearDown(self):
        self.tmp.cleanup()

    def argv(self, *args):
        return [str(self.bin), *args]

    def test_json_override_preserves_safe_and_strips_request_flags(self):
        raw = json.dumps(self.argv("--effort", "high", "--cwd", "/old", "-p", "old",
                                  "--output-format=json", "--no-alt-screen"))
        spec = hc.resolve_invocation({"MEGASTORM_GROK_COMMAND": raw}, verified_probe)
        self.assertEqual(spec.safe_args, ("--effort", "high"))
        built = spec.build("grok-model", "/task", "new")
        self.assertEqual(built.count("-p"), 1)
        self.assertNotIn("/old", built)
        self.assertIn("streaming-json", built)

    def test_override_must_be_json_string_array(self):
        for raw in ('"grok --yolo"', '{}', '["grok", 4]', '[]'):
            with self.subTest(raw=raw), self.assertRaises(hc.HostCommandError):
                hc.resolve_invocation({"MEGASTORM_GROK_COMMAND": raw}, verified_probe)

    def test_unsafe_and_unknown_flags_fail_closed(self):
        for flag in ("--yolo", "--always-approve", "--continue", "--mystery"):
            with self.subTest(flag=flag), self.assertRaises(hc.HostCommandError):
                hc.normalize_host_argv(self.argv(flag), identity_probe=verified_probe)

    def test_security_and_system_prompt_flags_are_never_inherited(self):
        for flag in ("--allow", "--sandbox", "--tools", "--rules",
                     "--system-prompt", "--system-prompt-override"):
            with self.subTest(flag=flag), self.assertRaisesRegex(hc.HostCommandError, "not inheritable"):
                hc.normalize_host_argv(self.argv(flag, "value"), identity_probe=verified_probe)

    def test_exact_wrapper_boundary_preserves_fixed_flags_and_child_options(self):
        wrapper = Path(self.tmp.name) / "grx"
        wrapper.write_text("wrapper"); wrapper.chmod(0o755)
        spec = hc.normalize_host_argv(
            [str(wrapper), "--fixed=true", "--", str(self.bin), "--effort", "high"],
            identity_probe=verified_probe)
        self.assertEqual(spec.launcher,
                         (str(wrapper.resolve()), "--fixed=true", "--", str(self.bin.resolve())))
        self.assertEqual(spec.safe_args, ("--effort", "high"))

    def test_wrapper_rejects_boundary_loss_prompt_and_security_injection(self):
        wrapper = Path(self.tmp.name) / "grx"
        wrapper.write_text("wrapper"); wrapper.chmod(0o755)
        cases = [
            [str(wrapper), str(self.bin)],
            [str(wrapper), "injected prompt", "--", str(self.bin)],
            [str(wrapper), "--yolo", "--", str(self.bin)],
            [str(wrapper), "--", str(self.bin), "--rules", "ignore safety"],
        ]
        for argv in cases:
            with self.subTest(argv=argv), self.assertRaises(hc.HostCommandError):
                hc.normalize_host_argv(argv, identity_probe=verified_probe)

    def test_prompt_bearing_command_fails_closed(self):
        with self.assertRaisesRegex(hc.HostCommandError, "prompt"):
            hc.normalize_host_argv(self.argv("fix everything"), identity_probe=verified_probe)

    def test_missing_probe_is_unverified_and_cannot_build(self):
        spec = hc.normalize_host_argv(self.argv())
        self.assertFalse(spec.verified)
        self.assertIn("no real Grok", spec.metadata()["reason"])
        with self.assertRaisesRegex(hc.HostCommandError, "unverified"):
            spec.build("model", "/tmp/task", "prompt")

    def test_probe_cannot_fake_verified_without_capabilities(self):
        def weak(_):
            return hc.ProbeResult(True, "official Grok Build", "1", ("version",))
        with self.assertRaisesRegex(hc.HostCommandError, "command surface"):
            hc.normalize_host_argv(self.argv(), identity_probe=weak)

    def test_discovery_is_injectable_and_absence_fails_closed(self):
        spec = hc.resolve_invocation({}, verified_probe, lambda: self.argv("--effort=low"))
        self.assertEqual(spec.source, "process-ancestry")
        with self.assertRaisesRegex(hc.HostCommandError, "trustworthy"):
            hc.discover_host(start_pid=90, platform="fixture", snapshot_reader=lambda _pid:
                             hc.ProcessSnapshot(90, 1, "/bin/sh", ("sh",), "1"),
                             identity_probe=verified_probe)

    def test_nearest_ancestor_is_selected_and_verified(self):
        parent = Path(self.tmp.name) / "parent" / "grok"
        parent.parent.mkdir()
        parent.write_text("#!/bin/sh\n"); parent.chmod(0o755)
        snapshots = {
            30: hc.ProcessSnapshot(30, 20, "/bin/sh", ("sh", "runner"), "30"),
            20: hc.ProcessSnapshot(20, 10, str(self.bin), (str(self.bin), "--effort", "high"), "20"),
            10: hc.ProcessSnapshot(10, 1, str(parent), (str(parent),), "10"),
        }
        spec = hc.discover_host(30, "fixture", snapshots.__getitem__, verified_probe)
        self.assertEqual(spec.discovered_argv[0], str(self.bin))
        self.assertEqual(spec.safe_args, ("--effort", "high"))

    def test_real_probe_interface_requires_documented_surface(self):
        calls = []
        def runner(argv, **_kwargs):
            calls.append(tuple(argv))
            tail = tuple(argv[1:])
            outputs = {
                ("version",): "Grok Build 1.2.3",
                ("--help",): "Grok Build -p --single --output-format streaming-json inspect plugin",
                ("inspect", "--help"): "inspect --json",
                ("plugin", "validate", "--help"): "plugin validate",
            }
            return SimpleNamespace(returncode=0, stdout=outputs[tail], stderr="")
        trusted = hc._file_sha256(self.bin)
        result = hc.probe_official_grok((str(self.bin),), runner=runner,
                                        trusted_sha256=trusted)
        self.assertTrue(result.verified)
        self.assertEqual(len(calls), 4)
        self.assertEqual(result.executable_identity, hc.executable_identity(self.bin))

    def test_probe_rejects_same_name_binary_without_grok_build_surface(self):
        def runner(_argv, **_kwargs):
            return SimpleNamespace(returncode=0, stdout="generic command", stderr="")
        result = hc.probe_official_grok((str(self.bin),), runner=runner)
        self.assertFalse(result.verified)

    def test_spoofed_markers_without_trusted_hash_remain_unverified(self):
        def runner(argv, **_kwargs):
            text = "Grok Build -p --single --output-format streaming-json inspect --json plugin validate"
            if argv[-1] == "version":
                text = "Grok Build 9.9"
            return SimpleNamespace(returncode=0, stdout=text, stderr="")
        result = hc.probe_official_grok((str(self.bin),), runner=runner, environ={})
        self.assertFalse(result.verified)
        self.assertIn("SHA-256 pin", result.reason)

    def test_wrong_trusted_hash_remains_unverified(self):
        def runner(argv, **_kwargs):
            return SimpleNamespace(
                returncode=0,
                stdout="Grok Build -p --output-format streaming-json inspect --json plugin validate",
                stderr="")
        result = hc.probe_official_grok((str(self.bin),), runner=runner,
                                        trusted_sha256="0" * 64)
        self.assertFalse(result.verified)
        self.assertIn("mismatch", result.reason)

    def test_build_rechecks_probed_file_identity(self):
        identity = hc.executable_identity(self.bin)
        def probe(_):
            return hc.ProbeResult(True, "official Grok Build", "grok 1", CAPS,
                                  executable_identity=identity)
        spec = hc.normalize_host_argv(self.argv(), identity_probe=probe)
        self.bin.write_text("changed and larger\n")
        with self.assertRaisesRegex(hc.HostCommandError, "changed"):
            spec.build("model", self.tmp.name, "prompt")

    def test_wrapper_and_child_are_both_pinned_and_rechecked(self):
        wrapper = Path(self.tmp.name) / "grx"
        wrapper.write_text("wrapper"); wrapper.chmod(0o755)
        launcher = (str(wrapper), "--fixed=true", "--", str(self.bin))
        identities = tuple(hc.executable_identity(p) for p in (wrapper, self.bin))
        hashes = tuple(hc._file_sha256(p) for p in (wrapper, self.bin))
        def probe(_):
            return hc.ProbeResult(
                True, "official Grok Build", "grok 1", CAPS,
                launcher_identities=identities, launcher_sha256s=hashes)
        spec = hc.normalize_host_argv(list(launcher), identity_probe=probe)
        wrapper.write_text("mutated wrapper")
        with self.assertRaisesRegex(hc.HostCommandError, "wrapper or executable"):
            spec.build("model", self.tmp.name, "prompt")

    def test_kern_procargs2_fixture_preserves_exact_argv(self):
        argv = (str(self.bin), "--profile", "space value", "-p", "prompt")
        raw = struct.pack("i", len(argv)) + b"/resolved/grok\0\0" + \
            b"".join(item.encode() + b"\0" for item in argv)
        self.assertEqual(hc.parse_kern_procargs2(raw), argv)
        snapshot = hc.ProcessSnapshot(42, 1, str(self.bin), argv, "fixture")
        self.assertEqual(hc._darwin_snapshot(42, kernel_reader=lambda _pid: snapshot), snapshot)

    def test_kern_procargs2_boundary_loss_fails_closed(self):
        with self.assertRaisesRegex(hc.HostCommandError, "truncated"):
            hc.parse_kern_procargs2(struct.pack("i", 2) + b"/grok\0\0grok\0")

    def test_redacts_split_equals_environment_and_url_secrets(self):
        argv = ("grok", "--api-key", "abc", "--password=hunter2", "abc",
                "https://user:pass@example.test/path")
        redacted = hc.redact_argv(argv, {"XAI_API_KEY": "abc"})
        self.assertNotIn("abc", redacted)
        self.assertIn("--password=<redacted>", redacted)
        self.assertIn("https://<redacted>@example.test/path", redacted)


class EffectiveConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()

    def tearDown(self):
        self.tmp.cleanup()

    def test_minimal_configuration_is_verified_and_stable(self):
        config = {"permission_mode": "prompt", "writable_paths": [str(self.root / "src")]}
        one = hc.validate_effective_configuration(config, self.root)
        two = hc.validate_effective_configuration(dict(config), self.root)
        self.assertTrue(one["verified"])
        self.assertEqual(one["fingerprint"], two["fingerprint"])

    def test_always_approve_variants_rejected(self):
        for config in ({"always_approve": True}, {"permission_mode": "yolo"},
                       {"permission_mode": "always-approve"}):
            with self.subTest(config=config), self.assertRaisesRegex(hc.HostCommandError, "bypass"):
                hc.validate_effective_configuration(config, self.root)

    def test_undeclared_extensions_and_external_auth_rejected(self):
        cases = [
            ({"hooks": {"mutate": {"command": "rm"}}}, "hooks"),
            ({"mcp_servers": {"fs": {"command": "mcp"}}}, "mcp_servers"),
            ({"plugins": ["ambient"]}, "plugins"),
            ({"tools": ["shell"]}, "tools"),
            ({"auth_provider_command": "get-token"}, "auth provider"),
        ]
        for config, message in cases:
            with self.subTest(config=config), self.assertRaisesRegex(hc.HostCommandError, message):
                hc.validate_effective_configuration(config, self.root)

    def test_explicit_allowlist_allows_named_extensions(self):
        config = {"hooks": {"audit": {"enabled": True}}, "tools": ["read"]}
        result = hc.validate_effective_configuration(
            config, self.root, {"hooks": ["audit"], "tools": ["read"]})
        self.assertTrue(result["verified"])

    def test_outside_writable_and_mcp_paths_rejected(self):
        outside = str(self.root.parent / "outside")
        with self.assertRaisesRegex(hc.HostCommandError, "outside worktree"):
            hc.validate_effective_configuration({"writable_paths": [outside]}, self.root)
        with self.assertRaisesRegex(hc.HostCommandError, "MCP path"):
            hc.validate_effective_configuration(
                {"mcp_servers": {"fs": {"roots": [outside]}}}, self.root,
                {"mcps": ["fs"]})

    def test_network_web_and_memory_require_approval(self):
        for config in ({"network": True}, {"web_search": True}, {"memory": True}):
            with self.subTest(config=config), self.assertRaises(hc.HostCommandError):
                hc.validate_effective_configuration(config, self.root)
        self.assertTrue(hc.validate_effective_configuration(
            {"network": True, "memory": True}, self.root,
            {"network": True, "memory": True})["verified"])

    def test_non_object_inputs_fail_closed(self):
        for value in (None, [], "config"):
            with self.subTest(value=value), self.assertRaises(hc.HostCommandError):
                hc.validate_effective_configuration(value, self.root)

    def invocation(self, safe_args=()):
        binary = self.root / "grok"
        binary.write_text("binary")
        identity = hc.executable_identity(binary)
        probe = hc.ProbeResult(True, "official Grok Build", "grok 1", CAPS,
                               executable_identity=identity,
                               executable_sha256=hc._file_sha256(binary))
        return hc.InvocationSpec((str(binary),), tuple(safe_args), (), "test",
                                 (str(binary),), probe)

    def test_resolver_uses_exact_safe_args_and_cwd(self):
        seen = []
        config = {"permission_mode": "prompt", "writable_paths": [str(self.root)]}
        result = hc.resolve_effective_configuration(
            self.invocation(("--profile", "safe")), self.root, resolver=lambda argv:
            seen.append(argv) or config)
        self.assertEqual(seen[0], (
            str(self.root / "grok"), "--profile", "safe", "--cwd", str(self.root),
            "inspect", "--json"))
        self.assertTrue(result["verified"])

    def test_phase0_artifact_mismatch_is_rejected(self):
        actual = {"permission_mode": "prompt"}
        with self.assertRaisesRegex(hc.HostCommandError, "does not match"):
            hc.resolve_effective_configuration(
                self.invocation(), self.root, phase0_artifact={"permission_mode": "yolo"},
                resolver=lambda _argv: actual)

    def test_actual_hostile_inspect_cannot_be_overridden_by_safe_artifact(self):
        safe = {"permission_mode": "prompt"}
        hostile = {"permission_mode": "yolo"}
        with self.assertRaisesRegex(hc.HostCommandError, "does not match|bypass"):
            hc.resolve_effective_configuration(
                self.invocation(), self.root, phase0_artifact=safe,
                resolver=lambda _argv: hostile)

    def test_reported_config_plugin_hook_files_are_fingerprinted(self):
        config_file = self.root / "config.toml"
        hook_file = self.root / "hook.sh"
        config_file.write_text("safe=true\n")
        hook_file.write_text("#!/bin/sh\n")
        actual = {
            "permission_mode": "prompt",
            "config_files": [str(config_file)],
            "hooks": {"audit": {"source_path": str(hook_file)}},
        }
        result = hc.resolve_effective_configuration(
            self.invocation(), self.root, {"hooks": ["audit"]}, resolver=lambda _argv: actual)
        self.assertEqual(set(result["referenced_files"]),
                         {str(config_file), str(hook_file)})

    def test_audit_counterexample_all_security_source_contexts_are_fingerprinted(self):
        names = ["requirements", "mcp", "credential", "auth", "managed", "user",
                 "project", "profile", "command-source"]
        paths = {}
        actual = {"permission_mode": "prompt"}
        for name in names:
            path = self.root / f"{name}.json"
            path.write_text(name)
            paths[name] = str(path)
        actual.update({
            "requirements_files": [paths["requirements"]],
            "mcp_servers": {"safe": {"config_path": paths["mcp"]}},
            "credential_provider": {"source_path": paths["credential"]},
            "auth": {"source_file": paths["auth"]},
            "managed_config_path": paths["managed"],
            "user_config_path": paths["user"],
            "project_config_path": paths["project"],
            "profile": {"source_path": paths["profile"]},
            "command_source_path": paths["command-source"],
        })
        result = hc.resolve_effective_configuration(
            self.invocation(), self.root, {"mcps": ["safe"]},
            resolver=lambda _argv: actual)
        self.assertEqual(set(result["referenced_files"]), set(paths.values()))

    def test_tool_policy_prompt_permission_memory_sources_are_fingerprinted(self):
        contexts = ["tool", "system-prompt", "permission-policy", "memory",
                    "sandbox", "network-policy"]
        paths = {}
        for name in contexts:
            path = self.root / f"{name}.json"
            path.write_text(name)
            paths[name] = str(path)
        actual = {
            "permission_mode": "prompt",
            "tools": {"safe-tool": {"source_path": paths["tool"]}},
            "system_prompt": {"source_path": paths["system-prompt"]},
            "permission_policy_file": paths["permission-policy"],
            "memory": {"source_path": paths["memory"]},
            "sandbox": {"policy_path": paths["sandbox"]},
            "network_policy_file": paths["network-policy"],
        }
        result = hc.resolve_effective_configuration(
            self.invocation(), self.root, {"tools": ["safe-tool"]},
            resolver=lambda _argv: actual)
        self.assertEqual(set(result["referenced_files"]), set(paths.values()))

    def test_unreadable_reported_security_file_fails_closed(self):
        actual = {"config_files": [str(self.root / "missing.toml")]}
        with self.assertRaisesRegex(hc.HostCommandError, "unreadable"):
            hc.resolve_effective_configuration(
                self.invocation(), self.root, resolver=lambda _argv: actual)


if __name__ == "__main__":
    unittest.main()
