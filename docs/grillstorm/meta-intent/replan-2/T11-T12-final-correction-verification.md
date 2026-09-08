# Root verification of C1 / A1 / C2 corrections

Base: `90257b1504d1c009d6e0f8a920fe0cf389f18463`. Both correction workers
settled through Orca and were released before this combined run. The immutable
90257b15 review reports remain historical findings, not claims of acceptance.

- `python3 -m pytest claude/meta-skill/tests/unit codex/meta-skill/test_flow.py -q`:
  **581 passed in 154.66s**.
- `node --test 'claude/meta-skill/knowledge/run-engine/tests/'*.test.js`:
  **55 passed**.
- `uvx mypy --follow-imports=silent --check-untyped-defs` on `product_intent.py`,
  `evidence_freshness.py`, `check_artifacts.py`: **no issues in 3 source files**.
- `git diff --check`: clean. Shared repository `core.bare` remains `false`.

Root inspected the positive-test adjustments: goal-only legacy records now
require a projection decision; complete recorded intent payloads still reuse.
Historical records are retained. Worker reports record the red/green cycles.
Root also clarified legacy fail-closed behavior in both orchestrator templates,
removed the Codex helper-list whitespace nit, and changed corrupt-read recovery
guidance to restore recorded dependencies rather than delete history.

These are copied-CLI and engine tests, not live Claude/Codex scenario evidence.
All 60 actual-host cells remain unverified. T15 helper preparation was separately
rerun in integration: 16 passed in 25.57s; it does not count as a host scenario.
The Codex evaluator still needs the user to dismiss its model-choice prompt.

Acceptance remains pending independent Standards and Spec rechecks of the new
committed candidate. #13/#16 are not unlocked by these test results alone.
