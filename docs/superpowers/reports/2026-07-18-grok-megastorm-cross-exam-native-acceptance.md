# Grok Build Megastorm and Cross-exam acceptance

Date: 2026-07-18

## Status

- Repository contract verification: **verified**
- Grok host conformance: **unverified**

The second status is not hidden by the first. Neither `grok` nor `grx` is
installed on this machine, so real plugin validation, inspect discovery,
authentication, and a real streaming capture were not run.

## Delivered surface

- One Claude-compatible Grok plugin root at `grok/megastorm/`.
- Two independent user-invocable skills: `megastorm` and `cross-exam`.
- Verified current-launcher discovery for direct and bounded wrapper grammar,
  including Linux `/proc`, macOS `KERN_PROCARGS2`, trusted executable SHA pins,
  capability probes, and TOCTOU checks.
- Production binding to the launcher's actual `inspect --json` result, Phase 0
  equality, security-source content fingerprints, and deny-by-default policy.
- Strict versioned streaming parser with a fake-only descriptor; production
  refuses that descriptor until a captured real-version fixture exists.
- Hardened Phase 1.6 scheduling, worktrees, CAS refs, touched paths, independent
  supervision, cancellation, state/events, recovery, census reconciliation,
  failure taxonomy, and reality-gate resolution.
- Cross-exam native-subagent hard gate, dispatch identity correlation, trusted
  in-process verifier requirement, strict evidence files, verdict validation,
  open threads, atomic ledger, and deterministic report rendering.
- `install.sh`, dry-run/destination tests, package checks, and parity matrix.

## Skill TDD

RED baselines were captured before either Grok skill existed.

- Megastorm baseline skipped mandatory capability/census discipline under time
  pressure and accepted task-list green as class-wide completion.
- Cross-exam baseline continued author self-review and considered a headless
  subprocess when native subagents were unavailable.

GREEN/REFACTOR pressure reruns rejected every shortcut. They also exposed stale
playbook references and initially forgeable Cross-exam evidence/identity fields;
those deterministic boundaries were tightened and retested.

## Thought-test rounds

### Round 1: failed, then fixed

The first independent audit found production wiring gaps despite 166 green
tests: caller-asserted config, fake stream default, spoofable launcher identity,
orphanable cancellation, forgeable Git recovery, weak native attestation,
unchecked census claims, incomplete reality resolution, and missing acceptance
artifacts.

Fixes bound real inspect output, required binary pins, rejected fake production
transport, tracked process groups, made events/state authoritative, added census
and reality closure, replaced caller-key attestation with a trusted-verifier hard
gate, and added the missing status artifacts.

### Round 2: failed, then fixed

Five adversarial gaps remained: wrapper/macOS argv fidelity, incomplete security
source fingerprints, census terminal reconciliation, stale reality summary
counts, and caller-mintable HMAC trust. These were fixed with exact wrapper
grammar, `KERN_PROCARGS2`, broader file traversal, terminal outcome reconciliation,
summary recomputation, and production refusal without an in-process host verifier.

### Round 3: approved

The third independent audit found one final fingerprint omission for tool,
prompt, permission, memory, sandbox, network, and TLS policy sources. After the
context traversal and counterexample test were added, the auditor confirmed:

- all seven referenced files were fingerprinted;
- content mutation changed the resolved fingerprint;
- targeted host tests passed 34/34;
- the full Grok suite passed 193/193;
- no repository-contract blocker remained.

## Adversarial scenario verdicts

| Scenario | Verdict |
|---|---|
| Fake CLI Phase 1.6 happy path | pass |
| Real CLI without captured descriptor | fail closed as designed |
| Malicious same-name executable or wrapper injection | rejected |
| Host binary replacement after probe | rejected |
| Host config differs from Phase 0 artifact | rejected |
| Referenced security file changes | resume fingerprint invalidated |
| Malformed, reordered, duplicate, truncated, or post-terminal stream | rejected |
| Dirty user worktree | preserved |
| Mutex/concurrency conflicts | serialized or escalated |
| Timeout, SIGINT, or SIGTERM | process groups terminated; resumable state retained |
| Forged Git completion subject | ignored |
| Rejected reality gate resumed | remains invalidated |
| Incomplete/escalated census task | `Completeness unverified` |
| Forged Cross-exam manifest/evidence | rejected |
| No trusted native verifier | report generation hard-stops |
| One install containing both skills | structurally verified |

## Verification commands

```text
python3 -m pytest -q grok/megastorm/scripts
193 passed

python3 -m pytest -q codex/megastorm-skill/scripts codex/cross-exam-skill/scripts
126 passed

bash -n grok/megastorm/install.sh
python3 -m py_compile grok/megastorm/scripts/*.py
git diff --check
```

Total automated regressions: **319 passed**.

## Remaining reality gate

To upgrade `Grok host conformance` to verified on a machine with official Grok
Build installed:

1. Pin the trusted `grok`/wrapper executable SHA-256.
2. Run `grok plugin validate <plugin-root>`.
3. Run `grok --plugin-dir <plugin-root> inspect --json` and confirm both skills.
4. Capture and redact a real `streaming-json` session for the exact CLI version,
   add its provenance/descriptor, and rerun transport/E2E tests.
5. Integrate a trusted native-subagent dispatch verifier for Cross-exam.

Until then, fake tests or repository parity must not upgrade the real-host field.

