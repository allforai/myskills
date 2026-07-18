# Grok Build Megastorm capability matrix

Status date: 2026-07-18

| Contract | Claude | Codex | Grok repository implementation | Grok real host |
|---|---|---|---|---|
| Phase -1 capability probe | v0.14 | verified | verified by skill pressure test | unverified |
| Phase 0 decision freeze/model mapping | v0.14 | verified | verified | unverified |
| Census-backed class completeness | v0.14 | verified | verified | verified | host-independent |
| Native independent design/review agents | workflow agents | multi-agent | native-subagent hard gate | unverified |
| Deterministic Phase 1.6 | workflow runner | `codex exec` runner | Grok headless NDJSON runner | unverified |
| Actual launcher/argument inheritance | host-native | verified | verified discovery/probe logic | unverified |
| Effective configuration security | host policy | verified envelope | resolved-config deny gate | unverified |
| Dirty user worktree isolation | verified | verified | verified by fake-CLI E2E | host-independent |
| CAS integration refs and resume | verified | verified | ported and regression verified | host-independent |
| Business/infrastructure/reality taxonomy | verified | verified | verified | host-independent |
| Streaming semantic transport | host-native | JSONL | strict versioned descriptor | unverified; no real fixture |
| Cross-exam native independence | native agents | hard gate | manifest-correlated native hard gate | unverified |
| Cross-exam evidence containment | verified | verified | strengthened and verified | host-independent |
| One install exposes two skills | N/A | separate skills | structurally verified | unverified by `grok inspect` |

## Status separation

- Repository contract verification: verified (round-3 independent acceptance).
- Grok host conformance: unverified.

The real-host column cannot be upgraded by fake CLI tests. It requires an
installed supported official Grok Build version, successful identity/capability
probes, `grok plugin validate`, `grok inspect --json`, and a captured real
streaming descriptor fixture.
