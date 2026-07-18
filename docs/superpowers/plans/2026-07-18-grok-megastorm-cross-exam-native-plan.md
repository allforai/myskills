# Grok Build Megastorm and Cross-exam Native Implementation Plan

## Objective

Implement the approved Grok Build design in
`docs/superpowers/specs/2026-07-18-grok-megastorm-cross-exam-native-design.md`
without weakening the existing Codex contracts or claiming real-host
conformance on this machine.

## Execution order

### 1. RED skill-pressure baselines

- Run a Megastorm pressure scenario without the future Grok skill.
- Run a Cross-exam pressure scenario without the future Grok skill.
- Record concrete unsafe shortcuts/rationalizations as test fixtures.
- Do not create either `SKILL.md` until its baseline is captured.

### 2. Package and static contracts

- Add `grok/megastorm/.claude-plugin/plugin.json`, `AGENTS.md`, and README.
- Add structural validators for manifest fields, owned references, and two-skill
  discovery layout.
- Add install tests first, then `install.sh` with `GROK_HOME` and explicit
  destination/dry-run support.

### 3. Host command and effective security

- Write failing fixtures for `grok`, verified `grx`, wrappers, malicious
  same-name binaries, injected protected flags, and secret redaction.
- Implement fail-closed ancestry/override parsing and command construction.
- Implement a runner-owned child environment/policy description and reject
  unsafe resolved configuration fixtures.
- Keep real identity/capability validation explicitly unverified when the CLI is
  absent.

### 4. Streaming protocol adapter

- Add a protocol descriptor format and fake-only descriptor clearly marked
  non-conformant.
- Test chunks, tools, duplicate events, order errors, malformed/truncated input,
  protocol errors, missing/duplicate terminal, post-terminal records, non-zero
  exit, and invalid envelopes.
- Implement strict semantic assembly without terminal-text scraping.

### 5. Megastorm deterministic runner

- Port the proven Codex deterministic gates and runner into the self-contained
  Grok plugin.
- Replace only the host adapter/transport invocation surface.
- Preserve CAS refs, worktrees, touched paths, executor/supervisor independence,
  retry taxonomy, reality gates, state/events, cancellation, and resume.
- Drive end-to-end tests through a fake Grok CLI.

### 6. Megastorm skill GREEN/REFACTOR

- Write the Grok Megastorm `SKILL.md` from the approved protocol and observed RED
  rationalizations.
- Run the same pressure test with the skill supplied.
- Tighten loopholes until the agent respects Phase -1/0, census, native
  subagents, deterministic Phase 1.6, security, and evidence gates.

### 7. Cross-exam implementation and skill GREEN/REFACTOR

- Port deterministic ledger/report behavior into the plugin.
- Add native-subagent identity, evidence-root, refusal, and no-headless-substitute
  contracts and tests.
- Write the Cross-exam `SKILL.md` from its RED baseline.
- Re-run and tighten the pressure scenario until it hard-stops without native
  independent evidence and never fixes audited work.

### 8. Parity, regression, and acceptance

- Add a Claude/Codex/Grok contract matrix with explicit host-conformance status.
- Run all Grok tests plus the existing 126 Codex/Cross-exam regressions.
- Run structural install/inspect simulation and verify the user worktree safety
  fixture.
- Perform thought-test acceptance across happy path, adversarial command/config,
  transport failure, cancellation/resume, evidence fraud, and packaging drift.
- Write an acceptance report with separate `Repository contract verification`
  and `Grok host conformance` statuses.

### 9. Delivery

- Review the final diff and ensure unrelated user work is untouched.
- Commit implementation and acceptance artifacts intentionally.
- Push `main` to `origin` as explicitly authorized by the user.

