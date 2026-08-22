# AGENTS.md — Cross-exam package (Codex, v0.17.0)

One install. Two explicit commands. Do not mix them.

| Invoke | Protocol | Writes |
|--------|----------|--------|
| `cross-exam` | `SKILL.md` (below the router) | `docs/cross-exam/<run>/` |
| `product-review` | `product-review.md` | `docs/product-review/<run>/` |

`cross-exam` is an evidence-backed completion audit. The main session is the examiner; every probe is a fresh-context sub-agent. Audit-only, interactive-only. Never edits the audited delivery.

`product-review` is a product-thinking critique plus competitor borrow notes. Advice only. No `.allforai/`. After `recommendations.md`, stop and offer `$grill-me` on that file.

Run cross-exam renderer tests with `python3 -m pytest scripts/ -q`.
