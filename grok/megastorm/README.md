# Megastorm for Grok Build

One Grok Build plugin containing two independent skills:

- `/megastorm` — decomposes and executes large multi-module goals with native
  subagents plus a deterministic, supervised Phase 1.6 runner.
- `/cross-exam` — interactively audits a delivery using fresh-context native
  probers and evidence-backed deterministic reporting. It never fixes findings.

## Install

```bash
./install.sh
grok plugin validate "${GROK_HOME:-$HOME/.grok}/plugins/megastorm"
grok --plugin-dir "${GROK_HOME:-$HOME/.grok}/plugins/megastorm" inspect --json
```

Use `./install.sh --dry-run` to display the destination without writing, or
`./install.sh --dest /absolute/path` for an isolated test installation.

## Conformance boundary

Repository tests use a fake CLI to verify deterministic contracts. They do not
certify the undocumented official streaming event schema. Full host conformance
requires a supported real CLI version, captured protocol fixture, plugin
validation, and inspect discovery. If those checks have not run, report exactly:

`Grok host conformance: unverified`

The production Phase 1.6 runner refuses the bundled fake-only stream descriptor.
Cross-exam report generation also refuses to run without an in-process trusted
native-dispatch verifier; caller-created manifests, keys, or verifier commands
are not accepted. These remain deliberate hard stops until a real Grok
installation supplies the corresponding host fixtures and integration.

## Runner

The Phase 1.6 entry point is `scripts/run_layers.py`. It inherits the actual
verified Grok launcher only after command identity and resolved configuration
pass fail-closed preflight. See `scripts/run_layers.py --help`.
