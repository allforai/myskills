# AGENTS.md — Cross-exam package (Codex, v0.19.0)

One install. Two explicit commands. Do not mix them.

| Invoke | Protocol | Writes |
|--------|----------|--------|
| `cross-exam` | `SKILL.md` (below the router) | `docs/cross-exam/<run>/` |
| `product-review` | `product-review.md` | `docs/product-review/<run>/` |

`cross-exam` is an evidence-backed completion audit. The main session is the examiner; every probe is a fresh-context sub-agent. Audit-only, interactive-only. Never edits the audited delivery. Users may declare journeys (who / circumstance / progress with an oracle); each is walked end-to-end by a fresh-context prober and judged against the oracle by the examiner.

`product-review` is a product-thinking critique plus competitor borrow notes. Advice only. No `.allforai/`. After `recommendations.md`, stop and offer `$grill-me` on that file.

Run cross-exam renderer tests with `python3 -m pytest scripts/ -q`.
