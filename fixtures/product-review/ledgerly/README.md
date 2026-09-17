# Ledgerly — product-review discovery fixture

A small Flask invoicing app with planted product defects and traps, used to test whether
`/product-review` can *find* problems on its own (earlier rounds handed the observations to the subject).

- `src/` — the app as committed to the fixture repo (no `.git`; see `build.sh`)
- `build.sh <dir>` — recreates the repo with its three commits (the weather-widget commit message is the
  `decoration` provenance the subject must find)
- `answer-key.md` — what must be found, what must not be written; keep it out of the subject packet
- `subject-prompt.md` — packet template; `{SKILL}` `{APP}` `{OUT}` are substituted per run

Record: `docs/validation/product-review-discovery-tests.md`.
