# Codex Plugin Audit Summary

Date: 2026-03-26

This summary consolidates the one-pass thought-experiment audit for all Codex plugins.

Important limitation:
- This is a document-and-prompt consistency audit
- It is not a record of real Codex execution

Validation orientation:
- Project prompts are scenario-level examples
- The preferred long-term validation direction is capability-based and fixture-based, not domain-specific

## Status Table

| Plugin | Scenario | Current Status | Main Confidence | Main Remaining Risk |
|--------|----------|----------------|-----------------|---------------------|
| `product-design` | FreshEats | Usable | High on phase structure | Needs real run to confirm artifact contracts end-to-end |
| `dev-forge` | TeamPulse | Usable with explicit prerequisites and reduced-context fallback | Medium-High | Full-fidelity results still depend on upstream `.allforai/product-map/` correctness |
| `demo-forge` | MarketHub | Usable with clarified runtime reporting | Medium | Runtime/tooling assumptions and iteration routing still unproven in practice |
| `code-tuner` | TeamPulse go-api | Strongest | High | Scenario still uses approximate scoring, not deterministic goldens |
| `code-replicate` | Task API | Strong | High | Discovery-driven outputs may vary more than prompt readers expect |
| `ui-forge` | PulseCRM UI Restore | Clear and bounded | High on positioning | Real restore-vs-polish decisions still need execution evidence |

## Per-Plugin Notes

### product-design

Strengths:
- `AGENTS.md` and `execution-playbook.md` define a coherent Codex-native pipeline
- Prompt now matches current phase structure

Risk:
- Earlier prompt drift shows this plugin is vulnerable to doc/contract drift over time

### dev-forge

Strengths:
- `AGENTS.md` now distinguishes hard upstream prerequisites from reduced-context workflows
- Scenario is aligned with both the full product-map path and the fallback path
- Completion markers remain explicit

Risk:
- Easy for external prompts to omit upstream artifacts and then over-claim certainty
- Reduced-context runs still need to report coverage loss correctly

### demo-forge

Strengths:
- Strong execution playbook with explicit runtime assumptions and iteration loop
- Good degradation-chain design
- Verification language is now less brittle: target threshold plus explicit reporting of untestable scope

Risk:
- Most runtime-sensitive plugin in the set

### code-tuner

Strengths:
- Most self-contained plugin
- Prompt and playbook align well

Risk:
- Simulated score targets should not be mistaken for exact acceptance thresholds

### code-replicate

Strengths:
- Clear phase model
- Good handoff story into downstream `.allforai/`

Risk:
- Output sizes are interpretation-sensitive and should stay range-based

### ui-forge

Strengths:
- Best-defined scope boundary
- Strong guardrails
- Prompt cleanly matches actual intent

Risk:
- Needs real run evidence to show it stops correctly on incomplete screens

## Overall Conclusion

Current Codex support is ready for real smoke execution at the prompt-definition level.

Best readiness:
- `code-tuner`
- `code-replicate`
- `ui-forge`

Good but more runtime-sensitive:
- `demo-forge`
- `dev-forge`

Most likely to drift again if not maintained:
- `product-design`
