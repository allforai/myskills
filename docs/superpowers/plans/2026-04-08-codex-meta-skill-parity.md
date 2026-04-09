# Codex Meta-Skill Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `codex/meta-skill` reach Claude-equivalent capability coverage with Codex-native adapters, executable validation, and a single canonical bootstrap contract.

**Architecture:** This implementation must proceed in dependency order. First lock the canonical runtime contract (`workflow.json`, generated `run` shape, MCP registration path). Then define source-of-truth ownership for shared semantic assets. Only after those two decisions are fixed should files be migrated into `codex/meta-skill/`.

**Tech Stack:** Markdown skill files, Python helper scripts, Node-based MCP gateway, shell install scripts, fixture-backed validation.

**Spec:** [`docs/superpowers/specs/2026-04-08-codex-meta-skill-parity-design.md`](/Users/aa/workspace/myskills/docs/superpowers/specs/2026-04-08-codex-meta-skill-parity-design.md)

---

## Task 1: Lock Canonical Contracts

**Files:**
- Update: `docs/superpowers/specs/2026-04-08-codex-meta-skill-parity-design.md` (only if decisions need clarification)
- Update: `codex/meta-skill/AGENTS.md`
- Update: `codex/meta-skill/execution-playbook.md`
- Create or Update: `codex/meta-skill/SKILL.md`

This task defines the contracts that everything else depends on. Do not migrate content before these decisions are explicit.

- [ ] **Step 1: Declare `workflow.json` as the canonical bootstrap graph contract**

Codex currently still documents `state-machine.json`. The live helper stack and Claude bootstrap protocol already use `workflow.json`.

Required outcome:
- `codex/meta-skill/AGENTS.md` stops describing `state-machine.json` as the primary output
- `codex/meta-skill/execution-playbook.md` stops describing `state-machine.json` as the primary output
- `SKILL.md` and Codex docs consistently describe `workflow.json`
- any mention of `state-machine.json` is explicitly labeled backward compatibility only

- [ ] **Step 2: Define the generated `run` entry contract**

Answer all three:
- Where is the generated `run` entry written in the target project?
- What file format does it use under Codex?
- How does the user invoke it from Codex?

Required outcome:
- the answer is written into `SKILL.md` and `execution-playbook.md`
- the answer does not depend on `.claude/commands/run.md`

- [ ] **Step 3: Define the Codex MCP registration strategy**

Claude uses `.mcp.json`. Codex parity needs an equivalent runtime registration path for `mcp-ai-gateway`.

Required outcome:
- create or specify `codex/meta-skill/.mcp.json` or an equivalent install-time generated registration path
- document how environment variables are wired
- make sure this decision is referenced by install docs

- [ ] **Step 4: Define interactive command transport assumptions**

`setup`, `journal`, and `journal-merge` depend on interactive behavior.

Required outcome:
- decide how Codex expresses question/answer flow
- write this as an adapter rule in the implementation notes or command scaffold
- do not rely on Claude-only command frontmatter semantics

- [ ] **Step 5: Commit contract changes**

```bash
git add docs/superpowers/specs/2026-04-08-codex-meta-skill-parity-design.md codex/meta-skill/AGENTS.md codex/meta-skill/execution-playbook.md codex/meta-skill/SKILL.md codex/meta-skill/.mcp.json
git commit -m "design(codex-meta-skill): lock workflow and runtime contracts"
```

---

## Task 2: Define Source-of-Truth Ownership

**Files:**
- Update: `docs/superpowers/specs/2026-04-08-codex-meta-skill-parity-design.md` (if ownership model needs explicit amendment)
- Create or Update: `docs/validation/codex-plugin-audit-summary.md` (later reference)
- Create or Update: helper docs if needed under `docs/validation/`

Three asset classes currently drift or are at risk of drift:
- knowledge files
- helper scripts
- test prompts / expected outputs / fixtures

- [ ] **Step 1: Choose ownership model for knowledge files**

Decide one:
- shared canonical source, then emitted into platform trees
- mirrored copies with automated drift check
- platform-local forks with explicit divergence policy

Required outcome:
- ownership model is written down
- empty Codex `knowledge/` can no longer be treated as "already migrated"

- [ ] **Step 2: Choose ownership model for helper scripts**

Focus on:
- `scripts/orchestrator/*`
- `stitch_oauth.py`
- `mcp-ai-gateway/*`

Required outcome:
- define whether Codex consumes `shared/` scripts directly or gets mirrored copies
- define how drift is detected

- [ ] **Step 3: Choose ownership model for tests and fixtures**

Focus on:
- `tests/prompts/*`
- `tests/expected/*`
- `tests/fixtures/*`

Required outcome:
- define whether Codex uses shared fixtures or Codex-local copies
- ensure realistic fixture coverage is not Claude-only

- [ ] **Step 4: Add explicit non-empty directory rule**

Required outcome:
- parity validation rejects empty `knowledge/`, `scripts/`, or `tests/` directories

- [ ] **Step 5: Commit source-of-truth decisions**

```bash
git add docs/superpowers/specs/2026-04-08-codex-meta-skill-parity-design.md docs/validation/
git commit -m "design(codex-meta-skill): define source-of-truth ownership"
```

---

## Task 3: Build the Codex Meta-Skill Skeleton

**Files:**
- Create: `codex/meta-skill/SKILL.md`
- Create: `codex/meta-skill/.mcp.json` or equivalent
- Create: `codex/meta-skill/install.sh`
- Create: `codex/meta-skill/commands/bootstrap.md`
- Create: `codex/meta-skill/commands/setup.md`
- Create: `codex/meta-skill/commands/journal.md`
- Create: `codex/meta-skill/commands/journal-merge.md`
- Create: `codex/meta-skill/skills/bootstrap.md`

At the end of this task, Codex must at least have a complete entry surface and no empty top-level protocol layer.

- [ ] **Step 1: Write `SKILL.md`**

Must include:
- command surface
- generated `run` contract
- bootstrap artifact contract (`workflow.json`)
- capability-parity positioning

- [ ] **Step 2: Add Codex MCP registration manifest**

Must include:
- `mcp-ai-gateway` entry
- env var placeholders
- path resolution that is valid under Codex assumptions

- [ ] **Step 3: Port command shells**

Create Codex-native versions of:
- `bootstrap`
- `setup`
- `journal`
- `journal-merge`

These may initially be thin wrappers, but they must not reference Claude-only runtime variables.

- [ ] **Step 4: Port bootstrap skill**

Create `codex/meta-skill/skills/bootstrap.md` from the Claude protocol, but:
- translate path variables
- translate generated `run` output path
- normalize `workflow.json`
- remove Claude-only assumptions

- [ ] **Step 5: Add install script**

Codex install script must:
- stop over-claiming AGENTS-only discovery
- register or explain MCP setup
- explain how to use the Codex entrypoint

- [ ] **Step 6: Commit skeleton**

```bash
git add codex/meta-skill/
git commit -m "feat(codex-meta-skill): add Codex-native skill skeleton"
```

---

## Task 4: Migrate Knowledge and Runtime Helpers

**Files:**
- Populate: `codex/meta-skill/knowledge/*`
- Populate: `codex/meta-skill/scripts/*`
- Populate: `codex/meta-skill/mcp-ai-gateway/*`

This task turns the skeleton into an actually usable migration.

- [ ] **Step 1: Populate knowledge tree**

Required minimum:
- `knowledge/capabilities/*`
- `knowledge/mappings/*`
- `knowledge/domains/*`
- `knowledge/diagnosis.md`
- `knowledge/learning-protocol.md`
- `knowledge/feedback-protocol.md`
- `knowledge/orchestrator-template.md`
- `knowledge/safety.md`

Rule:
- directories must be populated, not just created

- [ ] **Step 2: Translate knowledge files where needed**

Inspect for:
- Claude-only variable references
- `.claude/commands/run.md` references
- stale `state-machine.json` wording
- tool names that have no Codex meaning

- [ ] **Step 3: Populate helper scripts**

Required minimum:
- `scripts/orchestrator/check_artifacts.py`
- `scripts/orchestrator/check_requires.py`
- `scripts/orchestrator/loop_detection.py`
- `scripts/orchestrator/validate_bootstrap.py`
- `scripts/stitch_oauth.py`

- [ ] **Step 4: Normalize helper scripts to canonical contract**

Rules:
- fresh-output expectation is `workflow.json`
- any `state-machine.json` support is backward compatibility only
- tests and docstrings must say which one is canonical

- [ ] **Step 5: Populate `mcp-ai-gateway/`**

Include the runtime bundle or the declared adapter target selected in Task 2.

- [ ] **Step 6: Commit migrated assets**

```bash
git add codex/meta-skill/
git commit -m "feat(codex-meta-skill): migrate knowledge and runtime helpers"
```

---

## Task 5: Translate the Generated Orchestrator

**Files:**
- Update: `codex/meta-skill/knowledge/orchestrator-template.md`
- Update: `codex/meta-skill/skills/bootstrap.md`
- Create target-project generated run artifact shape in fixtures or examples if needed

This is a separate task because it is the highest-risk adapter surface.

- [ ] **Step 1: Rewrite orchestrator template for Codex**

Must answer:
- what the generated file looks like
- how it is invoked
- how it reads `.allforai/bootstrap/workflow.json`
- how it records transitions

- [ ] **Step 2: Remove Claude command frontmatter dependence**

The generated file must not depend on Claude command markdown semantics.

- [ ] **Step 3: Update bootstrap writer instructions**

`skills/bootstrap.md` must describe:
- where to write generated `run`
- how to render it from the Codex-native template
- how to keep references project-local

- [ ] **Step 4: Add one example generated run output**

Use either:
- a fixture snapshot
- or a documented example in validation docs

- [ ] **Step 5: Commit orchestrator translation**

```bash
git add codex/meta-skill/knowledge/orchestrator-template.md codex/meta-skill/skills/bootstrap.md docs/validation/
git commit -m "feat(codex-meta-skill): translate generated orchestrator for Codex"
```

---

## Task 6: Migrate Tests and Fixtures

**Files:**
- Populate: `codex/meta-skill/tests/*` or shared canonical equivalents
- Update: `shared/scripts/orchestrator/test_integration.py`
- Update: any validation docs that still overstate Codex readiness

Current test coverage is Claude-heavy and still partially old-contract.

- [ ] **Step 1: Bring specialization prompts and expected outputs into Codex validation scope**

Required outcome:
- Codex has access to specialization prompts and expected results
- they are not Claude-only assets anymore

- [ ] **Step 2: Bring realistic project fixture into Codex validation scope**

At minimum:
- reuse or mirror the `retail-sphere` fixture

- [ ] **Step 3: Update shared integration tests**

Focus on:
- remove fresh primary dependence on `state-machine.json`
- ensure tests reflect `workflow.json` as canonical output

- [ ] **Step 4: Add non-empty tree tests**

Validate that:
- `codex/meta-skill/knowledge/` contains files
- `codex/meta-skill/scripts/` contains files
- `codex/meta-skill/tests/` contains files

- [ ] **Step 5: Commit tests and fixtures**

```bash
git add codex/meta-skill/tests shared/scripts/orchestrator/ docs/validation/
git commit -m "test(codex-meta-skill): add Codex parity tests and fixtures"
```

---

## Task 7: Add Validation and Drift Checks

**Files:**
- Create or Update: validation scripts under `shared/scripts/` or `codex/meta-skill/tests/`
- Update: `docs/validation/codex-local-run-summary.md`
- Update: `docs/validation/codex-fixture-run-summary.md`
- Update: `docs/validation/codex-plugin-audit-summary.md`

This task turns the migration into a maintained state instead of a one-time copy.

- [ ] **Step 1: Add contract drift check**

Must fail if:
- Codex primary docs still say `state-machine.json`
- Codex generated run contract is undefined
- Codex files reference `${CLAUDE_PLUGIN_ROOT}`

- [ ] **Step 2: Add asset drift check**

Must compare the selected shared asset classes according to the ownership model from Task 2.

- [ ] **Step 3: Add executable smoke run**

Required outcome:
- one real local Codex-oriented smoke run is recorded
- result is written into validation summaries

- [ ] **Step 4: Update validation summaries**

Replace any stale confidence wording with real evidence:
- what was executed
- what passed
- what is still partial

- [ ] **Step 5: Commit validation work**

```bash
git add docs/validation/ shared/scripts/ codex/meta-skill/tests/
git commit -m "test(codex-meta-skill): add drift checks and smoke validation"
```

---

## Final Acceptance Gate

Do not call parity complete until all items below are true:

- [ ] `codex/meta-skill/SKILL.md` exists
- [ ] `codex/meta-skill/.mcp.json` or equivalent registration exists
- [ ] `codex/meta-skill/commands/` contains all four command files
- [ ] `codex/meta-skill/skills/bootstrap.md` exists and is Codex-adapted
- [ ] `codex/meta-skill/knowledge/` is populated
- [ ] `codex/meta-skill/scripts/` is populated
- [ ] `codex/meta-skill/tests/` is populated
- [ ] canonical bootstrap graph file is `workflow.json`
- [ ] generated `run` contract is defined and Codex-invocable
- [ ] no Codex docs rely on `AGENTS.md` alone for compatibility claims
- [ ] no Codex runtime files reference `${CLAUDE_PLUGIN_ROOT}`
- [ ] at least one executable Codex smoke run is recorded
- [ ] drift checks exist for contracts and shared assets

If any box is unchecked, parity is not complete.
