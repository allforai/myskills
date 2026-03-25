# Codex Plugin Mind Tests

Date: 2026-03-26

Purpose:
- Define capability-oriented thought-experiment scenarios for each Codex plugin
- Use these scenarios for prompt review, workflow review, artifact-contract review, and guardrail review
- Fix mismatches immediately when found

Note:
- These scenarios are examples, not the long-term regression base by themselves
- Long-term validation should continue to rely on `codex-capability-matrix.md` and `codex-generic-fixtures.md`
- The value of this file is coverage breadth: one plugin should be pressure-tested from several angles, not one branded sample project

## Primary Scenario Matrix

| Plugin | Project | Why This Project | Primary Checks | Status |
|--------|---------|------------------|----------------|--------|
| `product-design` | FreshEats | Multi-role, mobile-first, consumer workflow heavy | concept -> map -> journey -> experience -> gate -> use-case -> gap -> ui -> audit | Prompt aligned |
| `dev-forge` | TeamPulse | Multi-module SaaS, frontend/backend split, strong spec/task needs | project-setup -> design-to-spec -> task-execute -> verify chain | Prompt aligned after product-map bootstrap |
| `demo-forge` | MarketHub | Many entities, media fields, realistic seed/demo needs | design -> media -> execute -> verify -> iteration | Prompt added |
| `code-tuner` | TeamPulse go-api | Clean three-tier example with realistic violations | profile -> compliance -> duplication -> abstraction -> scoring | Prompt aligned |
| `code-replicate` | Task API | Small reverse-engineering target, easy output inspection | discovery -> structure -> artifact generation -> verify | Prompt aligned with range-based assertions |
| `ui-forge` | PulseCRM UI Restore | Functionally complete but visually drifted admin UI | triage -> restore/polish -> guardrails -> verify | Prompt added |

## Expanded Scenario Families

Each plugin should be thought-tested against multiple scenario families. These are not industry-specific goldens. They are capability combinations.

### `product-design`

| Scenario | What It Probes | Expected Pressure Points |
|----------|----------------|--------------------------|
| `Single-path Utility` | minimal viable phase closure | over-asking, unnecessary artifact expectations |
| `Dual-surface Product` | mixed consumer/operator modeling | `experience_priority`, role separation, downstream closure |
| `Constraint-heavy Workflow` | approvals, policy, manual checks | `interaction-gate`, defensive patterns, audit consistency |
| `Ambiguous Discovery Input` | incomplete or fuzzy user input | defaulting policy, blocking-question boundary |

Likely fixes if problems appear:
- phase order correction in playbooks
- artifact naming alignment in prompts
- stop vs continue rules clarified in docs

### `dev-forge`

| Scenario | What It Probes | Expected Pressure Points |
|----------|----------------|--------------------------|
| `Prereq-satisfied Build Path` | happy-path orchestration | setup -> spec -> task -> verify closure |
| `Missing Product Map` | hard prerequisite handling | early stop behavior, user guidance clarity |
| `Spec-first Resume` | partial artifact continuation | resume markers, phase routing |
| `Runtime-optional Verification` | limited runtime access | verify/test degradation path |

Likely fixes if problems appear:
- prerequisite wording in `AGENTS.md`
- completion marker naming
- verify/test/runtime boundary clarification

### `demo-forge`

| Scenario | What It Probes | Expected Pressure Points |
|----------|----------------|--------------------------|
| `Static Demo Packaging` | runtime-free demo creation | asset manifest, plan closure |
| `Runtime-assisted Demo` | optional live environment support | runtime-required step detection |
| `Media-light Demo` | few or no media assets | graceful degradation |
| `Coverage-stressed Demo` | many entities and flows | over-brittle quality gates, scope control |

Likely fixes if problems appear:
- `demo-plan` contract clarification
- runtime assumptions made explicit
- verify thresholds converted to shape-based checks

### `code-tuner`

| Scenario | What It Probes | Expected Pressure Points |
|----------|----------------|--------------------------|
| `Clean Layered Backend` | false-positive control | over-reporting |
| `Mixed-responsibility Backend` | compliance analysis quality | layer detection, responsibility mapping |
| `Duplication-heavy Backend` | duplication vs abstraction boundaries | task recommendation quality |
| `Maintenance-sensitive Backend` | lifecycle-mode separation | pre-launch vs maintenance suggestions |

Likely fixes if problems appear:
- scoring criteria wording
- phase output boundaries
- read-only guardrail emphasis

### `code-replicate`

| Scenario | What It Probes | Expected Pressure Points |
|----------|----------------|--------------------------|
| `Minimal Source Tree` | lower-bound generation | tiny input acceptance |
| `Role-rich Source` | role/task/flow aggregation | schema closure under sparse code |
| `Flow-gapped Source` | partial inference quality | gap handling, inferred references |
| `Handoff-focused Source` | downstream compatibility | product-map handoff readiness |

Likely fixes if problems appear:
- validator assumptions relaxed or clarified
- hard-coded counts removed from prompts
- generated artifact contract wording updated

### `ui-forge`

| Scenario | What It Probes | Expected Pressure Points |
|----------|----------------|--------------------------|
| `Restore from Strong Baseline` | fidelity-first mode selection | token/spec priority |
| `Polish without Baseline` | no-design-input mode | restore vs polish routing |
| `Drifted Implementation` | design drift detection | non-functional guardrails |
| `Component-consistency Pass` | multi-screen visual coherence | local polish vs system consistency |

Likely fixes if problems appear:
- baseline priority order in docs
- boundary wording against `dev-forge`
- eval criteria alignment

## Baseline Project Definitions

### 1. FreshEats

Type:
- Consumer/mobile delivery platform

Plugins:
- `product-design`
- Optional downstream `dev-forge`
- Optional downstream `demo-forge`

What it stresses:
- Role separation
- Journey continuity
- Experience priority
- UI design and audit chain

### 2. TeamPulse

Type:
- Team management SaaS

Plugins:
- `dev-forge`
- `code-tuner`

What it stresses:
- Modular CRUD + workflow platform
- Backend/frontend split
- Spec quality, endpoint modeling, build-log semantics
- Architecture analysis on a realistic service codebase

### 3. MarketHub

Type:
- Marketplace / ecommerce back office + buyer app

Plugins:
- `demo-forge`

What it stresses:
- Rich entity graph
- Asset/media handling
- Seed data realism
- Iterative verification and deferred-to-dev routing

### 4. Task API

Type:
- Small open-source Go REST API

Plugins:
- `code-replicate`
- Optional downstream `dev-forge`

What it stresses:
- Reverse-engineering from source
- Minimal but complete `.allforai/` handoff
- Discovery-driven counts instead of brittle golden numbers

### 5. PulseCRM UI Restore

Type:
- Existing admin product with working screens but design drift

Plugins:
- `ui-forge`

What it stresses:
- Post-implementation-only positioning
- Restore vs polish mode selection
- Guardrails against accidental business logic changes

## Testing Method

For each plugin:

1. Read `AGENTS.md`
2. Read `execution-playbook.md`
3. Read the dedicated test prompt or scenario definition
4. Check:
   - phases match implementation
   - prerequisites are realistic
   - expected outputs match current artifact contracts
   - quality gates are testable
   - stop behavior is explicit when hard prerequisites are missing
   - degradation behavior is explicit when optional tools/runtime are missing
5. If mismatch exists:
   - fix prompt first
   - then fix user-facing docs if the docs are the source of confusion
   - if the mismatch is contractual, fix the validation docs too

## Fix Priorities When Problems Are Found

1. Entry-point confusion
   - Fix `AGENTS.md` and plugin README
2. Phase-order or resume confusion
   - Fix `execution-playbook.md`
3. Artifact name/path mismatch
   - Fix prompts and validation docs
4. Stop/degrade ambiguity
   - Add explicit prerequisite and fallback wording
5. Overfit assertions
   - Replace exact-count expectations with shape-based assertions

## Current Result

- `product-design`: prompt aligned
- `dev-forge`: prompt aligned after bootstrap prerequisite fix
- `code-tuner`: aligned
- `code-replicate`: aligned after replacing exact counts with lower bounds
- `demo-forge`: prompt added
- `ui-forge`: dedicated prompt added in this round

## Recommended Execution Order

For the next thought-test sweep, use this order:

1. `dev-forge`
2. `demo-forge`
3. `ui-forge`
4. `product-design`
5. `code-tuner`
6. `code-replicate`

Reason:
- `code-replicate` already has the strongest local executable evidence
- `dev-forge`, `demo-forge`, and `ui-forge` still benefit most from additional edge-case thought testing
