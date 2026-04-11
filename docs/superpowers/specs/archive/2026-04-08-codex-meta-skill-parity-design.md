# Codex Meta-Skill Parity Design

> Goal: make `codex/meta-skill` reach Claude-level workflow coverage and artifact compatibility, while accepting platform-specific differences in entry format and tool binding.

## 1. Problem Statement

Current `codex/meta-skill` is not a usable Codex-native counterpart of `claude/meta-skill`.

Observed gaps:

- `codex/meta-skill` has no `SKILL.md`
- `codex/meta-skill` has no `commands/` implementation
- `codex/meta-skill` has no knowledge files at all; the `knowledge/` directory is effectively empty
- `codex/meta-skill` has no `scripts/` runtime helpers
- `codex/meta-skill` has no local `mcp-ai-gateway/` bundle
- `codex/meta-skill` has no MCP registration manifest equivalent to Claude `.mcp.json`
- `codex/meta-skill` has no test coverage
- existing docs still assume Codex can be bootstrapped from `AGENTS.md` alone
- Codex docs still describe `state-machine.json`, while the actual current helper scripts and Claude protocol use `workflow.json`
- parts of the shared test/helper surface still validate `state-machine.json`, so the repository itself has no single bootstrap graph source of truth

As a result, the current Codex version is only a thin placeholder, not a feature-complete migration.

## 2. Target Definition

The requirement "100% experience Claude functions under Codex" must be made precise.

### 2.1 What "100%" means

For this migration, `100%` means:

- the same user goals can be initiated from Codex
- the same bootstrap analysis logic exists
- the same project-local outputs are generated
- the same orchestration model exists
- the same capability knowledge base is available
- the same degradation rules exist when optional tools are absent
- the same validation and smoke-test surface exists

This is called **capability parity**.

### 2.2 What "100%" does not mean

This migration does **not** require:

- identical command frontmatter syntax
- identical environment variable names inside platform wrappers
- identical MCP tool identifiers
- identical plugin install flow
- identical user-facing command transport

This is because Claude and Codex expose different runtime conventions.

### 2.3 Formal Success Metric

Codex parity is achieved only when:

1. every Claude meta-skill workflow has a Codex entry path
2. every Claude bootstrap artifact has a Codex-equivalent producer
3. every Claude runtime helper used by generated workflows exists in Codex form
4. every Claude optional external capability has a Codex detection or downgrade path
5. Codex smoke tests cover the migrated surface with executable evidence
6. Codex and Claude agree on bootstrap artifact names and generated entrypoint locations

## 3. Scope

### In scope

- `codex/meta-skill/SKILL.md`
- `codex/meta-skill/.mcp.json` or a Codex-equivalent MCP registration manifest
- `codex/meta-skill/commands/*`
- `codex/meta-skill/skills/bootstrap.md`
- `codex/meta-skill/knowledge/*`
- `codex/meta-skill/scripts/*`
- `codex/meta-skill/mcp-ai-gateway/*`
- `codex/meta-skill/install.sh`
- `codex/meta-skill/tests/*`
- Codex-facing install and validation docs that currently over-claim compatibility

### Out of scope

- making Codex and Claude use byte-identical command files
- rewriting all other Codex plugins in this phase
- guaranteeing all third-party MCP tools are available in every Codex session
- implementing a universal cross-platform abstraction layer for all future plugins

## 4. Current State Audit

### 4.1 Claude meta-skill surface

`claude/meta-skill` currently includes:

- `.mcp.json`
- `SKILL.md`
- `commands/bootstrap.md`
- `commands/setup.md`
- `commands/journal.md`
- `commands/journal-merge.md`
- `skills/bootstrap.md`
- `knowledge/` with capability references, mappings, domains, protocols, and orchestrator template
- `scripts/` helpers
- `mcp-ai-gateway/`
- `tests/`

### 4.2 Codex meta-skill surface

`codex/meta-skill` currently includes:

- `AGENTS.md`
- `execution-playbook.md`
- an empty `knowledge/` directory
- an empty `skills/` directory

Missing relative to Claude:

- `.mcp.json` or equivalent MCP registration layer
- `SKILL.md`
- `commands/`
- actual skill implementation files
- `scripts/`
- `mcp-ai-gateway/`
- `install.sh`
- `tests/`

### 4.3 Consequence

Today, `codex/meta-skill` cannot be considered:

- discoverable with normal Codex skill conventions
- runnable end-to-end
- test-backed
- contract-complete
- schema-aligned with the current bootstrap artifact contract
- knowledge-complete

### 4.4 Contract drift already present

There is an existing naming drift inside the repository:

- `codex/meta-skill/AGENTS.md` and `codex/meta-skill/execution-playbook.md` still describe `state-machine.json`
- Claude bootstrap protocol, orchestrator template, and validation helpers use `workflow.json`
- some helper scripts still keep partial backward compatibility for `state-machine.json`

This matters because parity is not only "copy files" but "choose one canonical contract and make both sides align".

### 4.5 Shared asset drift already present

The repository also contains a source-of-truth problem:

- `claude/meta-skill/knowledge/*` is populated
- `codex/meta-skill/knowledge/*` is empty
- current shared orchestrator helpers include both old `state-machine` terminology and newer `workflow` terminology
- some tests still exercise only the old contract

This means parity work must define synchronization ownership, not only file presence.

## 5. Design Principles

### Principle 1: Capability parity over syntax parity

We preserve behavior and outputs first. Platform-native wrappers may differ.

### Principle 2: Project-local generated artifacts remain the ground truth

Generated `.allforai/bootstrap/*` products and project-local run entrypoints remain the interoperability layer. Platform differences must not leak into generated business artifacts.

### Principle 3: No Codex-only silent feature cuts

If Claude supports a capability, Codex must do one of:

- support it directly
- support it through a mapped Codex tool
- document an explicit downgrade path

Removing a capability without a declared downgrade is not allowed.

### Principle 4: Tool bindings are adapters, not business logic

Claude-specific tool detection logic must be isolated so the meta-skill protocol stays portable.

### Principle 5: Validation must be executable

Parity cannot be claimed from docs alone. Each migrated surface needs a local executable check or a fixture-backed smoke run.

### Principle 6: Shared semantic assets need one source of truth

Knowledge files, helper scripts, and fixtures that are platform-agnostic must not diverge silently between Claude and Codex copies.

## 6. Migration Strategy

The migration is split into five layers.

### Layer A: Discovery and entry normalization

Create a real Codex-native entry surface:

- add `codex/meta-skill/SKILL.md`
- keep `AGENTS.md` only as auxiliary human-facing documentation
- define Codex-native command routing inside `SKILL.md`

Outcome:

- Codex can discover and invoke the skill using the same mechanism as other Codex skills in this repo

### Layer B: Protocol migration

Port the workflow protocol from Claude:

- migrate `bootstrap.md`
- migrate `setup`, `journal`, and `journal-merge` command intent
- replace Claude-specific path variables and command wrappers with Codex-native equivalents
- normalize the bootstrap artifact contract so Codex does not keep stale `state-machine.json` wording if `workflow.json` is the canonical schema

Outcome:

- Codex has the same logical command set and phase behavior

### Layer C: Tool binding adapter layer

Separate Claude-specific tool assumptions from meta-skill logic.

Four classes of bindings must be adapted:

1. command transport
2. MCP tool naming and capability detection
3. installation/update flow
4. interactive question semantics and tool availability assumptions

Concrete rule:

- the protocol should say "detect Playwright capability"
- the platform adapter should define how Codex checks for it

Outcome:

- core workflow docs stop hardcoding Claude runtime assumptions

### Layer D: Runtime helper parity

Bring over the missing executable dependencies:

- `scripts/orchestrator/*`
- `mcp-ai-gateway/*`
- MCP registration manifest
- install/bootstrap helpers
- tests and fixtures
- source-of-truth strategy for shared semantic assets

Outcome:

- generated workflows have the same local helper surface as Claude

### Layer E: Validation parity

Add Codex-specific executable coverage:

- entrypoint existence check
- bootstrap fixture validation
- helper script execution
- command/doc consistency checks
- smoke fixture for generated bootstrap output

Outcome:

- parity status is backed by evidence, not by static inspection

## 7. Required File Set

The minimum viable Codex parity file set is:

```text
codex/meta-skill/
  .mcp.json or equivalent
  SKILL.md
  AGENTS.md
  install.sh
  execution-playbook.md
  commands/
    bootstrap.md
    setup.md
    journal.md
    journal-merge.md
  skills/
    bootstrap.md
    journal.md
    journal-merge.md
  knowledge/
    capabilities/*
    mappings/*
    domains/*
    diagnosis.md
    learning-protocol.md
    feedback-protocol.md
    orchestrator-template.md
    safety.md
  scripts/
    orchestrator/*
    stitch_oauth.py
  mcp-ai-gateway/*
  tests/*
```

If any item above is absent, parity is incomplete.

### 7.1 Required non-empty sets

The following directories must not merely exist; they must contain migrated content:

- `codex/meta-skill/knowledge/`
- `codex/meta-skill/scripts/`
- `codex/meta-skill/tests/`

An empty directory does not count toward parity.

## 8. Source-of-Truth Strategy

Three asset classes are semantically shared across platforms:

1. knowledge files
2. orchestrator helper scripts
3. test prompts / expected outputs / fixtures

The migration must choose one maintenance model for each class:

- shared canonical location with platform wrappers
- generated copy from a canonical source
- mirrored copies with an automated drift check

Rule:

- parity is incomplete until each shared asset class has an explicit ownership model

### 8.0.1 Recommended ownership

Recommended default:

- business and protocol knowledge: canonical under a shared or generator-backed source, then emitted to platform trees
- pure platform wrappers: stay platform-local
- fixtures and expected outputs: shared whenever possible

Reason:

- otherwise Codex and Claude will drift immediately after the first content update

## 8. Adapter Design

### 8.1 Path abstraction

Claude documents currently rely on `${CLAUDE_PLUGIN_ROOT}`.

Codex version must replace this with one of:

- a Codex-native root variable, if available
- relative paths anchored from the skill directory
- explicit repository-relative paths when no dynamic variable exists

Rule:

- no Codex command or skill file may reference `${CLAUDE_PLUGIN_ROOT}`

### 8.1.1 MCP registration layer

Claude currently uses `.mcp.json` to wire `mcp-ai-gateway/dist/index.js` with environment variables.

Codex parity requires one of:

- a Codex-native `.mcp.json` equivalent
- a generated/installed MCP registration path with the same effective capability

Rule:

- Codex parity is incomplete if `mcp-ai-gateway` exists but no runtime registration path is defined

### 8.2 Command abstraction

Claude command markdown contains Claude-specific frontmatter and invocation patterns.

Codex commands must be rewritten so that:

- command intent remains the same
- arguments remain semantically compatible
- file references resolve under Codex conventions

Rule:

- command files are not copied blindly; they are translated

### 8.2.1 Interactive command semantics

Claude command files use platform-specific frontmatter features such as:

- `allowed-tools`
- `AskUserQuestion`
- argument metadata in command headers

Codex migration must define how each of these behaviors is expressed under Codex.

Rule:

- `setup`, `journal`, and `journal-merge` are not complete until their interactive behavior is mapped, not just their prose copied

### 8.2.2 Generated run template translation

Claude's orchestrator template is itself written as a Claude command markdown file.

Codex parity therefore requires not only a target location for generated `run`, but also:

- a Codex-native template format
- a transformation rule from shared orchestrator semantics into that format

Rule:

- copying `knowledge/orchestrator-template.md` as-is is not sufficient if the generated file still uses Claude command frontmatter or invocation semantics

### 8.3 Tool detection abstraction

Claude `setup.md` currently depends on Claude-specific active/deferred tool inspection language.

Codex version must define a Codex-native capability table:

- required capability
- primary Codex check
- fallback check
- downgrade behavior

Example categories:

- browser automation
- web search
- image generation
- model gateway
- optional visual generation
- question/confirmation transport

### 8.4 Install/update abstraction

Claude install flow and Codex install flow must be documented separately.

Rule:

- README and install scripts must stop claiming that `AGENTS.md` alone is enough for Codex

### 8.4.1 Generated run entry location

Claude bootstrap writes the generated orchestrator entry to `.claude/commands/run.md` in the target project.

Codex parity must explicitly answer:

- where the generated `run` entry lives in a Codex-target project
- how the user invokes it
- whether the generated file is command markdown, a skill file, or another Codex-native entry shape

Rule:

- parity is incomplete until the generated run entry location and invocation contract are defined

## 9. Output Contract

Parity requires generated artifacts to stay compatible with the Claude design.

The following generated outputs are mandatory:

- `.allforai/bootstrap/bootstrap-profile.json`
- `.allforai/bootstrap/workflow.json`
- `.allforai/bootstrap/node-specs/*.md`
- `.allforai/bootstrap/scripts/*`
- `.allforai/bootstrap/protocols/*`
- generated run entry command in the target project

Contract rule:

- generated artifact paths must remain project-local
- generated artifact schema names must not diverge between Claude and Codex without a migration note

### 9.1 Canonical bootstrap graph file

The migration must choose one canonical graph filename:

- `workflow.json`
- or `state-machine.json`

Current repository evidence favors `workflow.json` as the live contract, because:

- bootstrap protocol uses it
- orchestrator template uses it
- artifact checker and validator use it

Decision:

- Codex parity should converge on `workflow.json`
- `state-machine.json` may exist only as backward-compatibility read support during migration, not as the forward contract

### 9.2 Shared helper compatibility

Any helper or test that still treats `state-machine.json` as the primary generated artifact must be either:

- migrated to `workflow.json`
- or explicitly labeled as backward-compatibility coverage only

Rule:

- no newly added Codex validation may use `state-machine.json` as the fresh-output expectation

## 10. Validation Plan

### 10.1 Static checks

- `codex/meta-skill` required file set exists
- Codex MCP registration path exists
- no Codex files reference Claude-only root variables
- command set matches Claude command set
- no Codex docs describe stale bootstrap artifact names as the primary contract
- knowledge and script directories are present

### 10.2 Fixture-backed checks

- bootstrap fixture can generate expected bootstrap directory
- validation scripts can parse and validate generated outputs
- orchestrator helper scripts run against fixture inputs
- journal merge logic has fixture inputs and expected outputs
- specialization prompts and expected outputs exist for Codex, not only Claude
- at least one realistic project fixture exists for Codex bootstrap specialization

### 10.3 Behavior checks

- Codex bootstrap can route goals equivalent to Claude bootstrap
- optional capability absence triggers documented downgrade behavior
- generated run entry references project-local files only
- generated run entry is invocable through a documented Codex-native path
- interactive commands preserve conflict-resolution behavior
- Codex knowledge directory is populated enough to satisfy bootstrap references without falling back to Claude paths

### 10.4 Acceptance threshold

Parity may only be declared when:

- all static checks pass
- all fixture checks pass
- at least one end-to-end Codex local smoke run succeeds on a generic fixture

## 11. Risks

### Risk 1: False parity from file copying

Copying Claude files directly may preserve text but leave runtime bindings broken.

Mitigation:

- adapter pass is mandatory after migration

### Risk 2: Codex runtime lacks direct equivalents for some Claude assumptions

Mitigation:

- encode downgrade behavior explicitly
- keep capability contracts stable even if transport differs

### Risk 2.5: Artifact contract split-brain

If some files keep using `state-machine.json` while others use `workflow.json`, bootstrap output and runtime helpers will silently disagree.

Mitigation:

- declare one canonical filename
- add a validation check that rejects fresh Codex docs using the old primary name

### Risk 3.5: Empty-tree false confidence

Directories may exist in `codex/meta-skill` while containing no usable content.

Mitigation:

- validate minimum non-empty file counts for knowledge, scripts, and tests

### Risk 3: Docs drift after migration

Mitigation:

- add parity validation checks that compare Claude and Codex command/file surfaces

### Risk 4: Meta-skill remains unique and untested compared to other Codex skills

Mitigation:

- add dedicated tests instead of relying on cross-plugin confidence

### Risk 5: Interactive features are "ported" only as text

`setup` and `journal-merge` depend on real question/answer mechanics. A text-only port will look complete but fail in use.

Mitigation:

- require adapter mapping for interactive commands
- add behavior tests or manual smoke scripts for conflict resolution flows

### Risk 6: Shared asset ownership remains undefined

If Claude knowledge continues evolving while Codex stores independent copies, parity will decay immediately.

Mitigation:

- declare source-of-truth ownership
- add drift checks across shared assets

## 12. Non-Negotiable Rules

- Do not claim Codex compatibility from `AGENTS.md` presence alone
- Do not mark parity complete without `SKILL.md`
- Do not leave MCP registration unspecified
- Do not leave Claude-only variables in Codex files
- Do not preserve `state-machine.json` as the primary contract if helpers already validate `workflow.json`
- Do not count empty `knowledge/`, `scripts/`, or `tests/` directories as migrated
- Do not leave source-of-truth ownership undefined for shared knowledge and helpers
- Do not cut command surfaces silently
- Do not declare parity without executable validation evidence

## 13. Implementation Order

### Phase 1: Entrypoint completion

- add `SKILL.md`
- add MCP registration manifest or equivalent
- add `commands/*`
- add `skills/bootstrap.md`

### Phase 2: Runtime completion

- populate `knowledge/*`
- add `scripts/*`
- add `mcp-ai-gateway/*`
- add `install.sh`
- define generated `run` entry location and invocation shape

### Phase 3: Adapter pass

- rewrite path bindings
- rewrite command/tool detection logic
- rewrite interactive command semantics
- translate orchestrator template into Codex-native generated `run`
- normalize `workflow.json` as the canonical graph contract
- update install docs

### Phase 4: Validation completion

- add tests
- add fixture smoke checks
- add contract drift checks for graph filename and generated run entry
- add non-empty directory checks for knowledge/scripts/tests
- add drift checks for shared knowledge/helpers/fixtures
- update validation summaries with real Codex execution evidence

## 14. Acceptance Checklist

- [ ] `codex/meta-skill/SKILL.md` exists and is usable
- [ ] Codex MCP registration path exists for `mcp-ai-gateway`
- [ ] Codex command set covers `bootstrap`, `setup`, `journal`, `journal-merge`
- [ ] Codex bootstrap protocol exists as a real skill file
- [ ] Codex knowledge directory is populated, not empty
- [ ] Codex includes helper scripts required by generated workflows
- [ ] Codex includes `mcp-ai-gateway/` or an equivalent declared adapter
- [ ] Codex migration defines where generated `run` lives and how it is invoked
- [ ] Codex migration defines how the generated `run` template is translated from shared orchestrator semantics
- [ ] no Codex files reference Claude-only runtime variables
- [ ] Codex uses `workflow.json` as the canonical bootstrap graph contract
- [ ] no fresh Codex tests expect `state-machine.json` as the primary output
- [ ] install docs no longer overstate `AGENTS.md` discovery
- [ ] shared asset ownership is defined for knowledge, scripts, and fixtures
- [ ] fixture-backed validation exists
- [ ] at least one Codex local smoke run is recorded
- [ ] parity claim is based on executable evidence, not document inspection

## 15. Final Decision

The repository should stop treating `codex/meta-skill` as already compatible.

The correct target is:

**Claude-to-Codex meta-skill capability parity with platform-native adapters.**

Anything weaker is not enough for the user's requirement.
