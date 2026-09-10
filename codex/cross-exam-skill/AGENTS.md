# AGENTS.md — Cross-exam package (Codex, v0.21.0)

Optional visual acceptance uses bundled visual/visual-acceptance.md and SwiftUI references.
User-confirmed baselines, runtime images and independent image review are required.

One install. Three explicit reviews. Do not mix them. Follow only the user-named protocol; none is automatic.

| Invoke | Protocol | Writes |
|--------|----------|--------|
| `cross-exam` | `SKILL.md` (below the router) | `docs/cross-exam/<run>/` |
| `product-review` | `product-review.md` | `docs/product-review/<run>/` |
| `keep-code-simple` | `keep-code-simple/SKILL.md` (also directly discoverable) | `docs/keep-code-simple/<run>/recommendations.md` |

`cross-exam` is an evidence-backed completion audit. The main session is the examiner; every probe is a fresh-context sub-agent. Audit-only, interactive-only. Never edits the audited delivery. Users may declare journeys (who / circumstance / progress with an oracle); each is walked end-to-end by a fresh-context prober and judged against the oracle by the examiner.

`product-review` is a product-thinking critique plus competitor borrow notes. Advice only. No `.allforai/`. After `recommendations.md`, stop and offer `$grill-me` on that file.

`keep-code-simple` investigates implementation simplicity, then presents concrete recommendations as one batch of choices. It reads code and existing tests but never executes the target project or edits its source. Follow its own protocol, not cross-exam's interactive probe loop or mandatory-independent-agent gate.

For package development (not a simplicity review), run cross-exam renderer tests with `python3 -m pytest scripts/ -q`.
