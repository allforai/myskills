# Multi-Platform Native Skills Reorganization — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reorganize myskills into three fully native platform directories (claude/, codex/, opencode/) with a minimal shared/ layer, preserving Claude Code 100% backward compatibility.

**Architecture:** Each platform gets a complete, independent copy of all 6 plugins, optimized for that platform's native attention management, tool calls, and interaction patterns. Claude keeps scripts/mcp-ai-gateway in-place (unchanged). shared/ holds a separate copy of scripts and MCP gateway for codex/ and opencode/ to reference.

**Critical note:** `${CLAUDE_PLUGIN_ROOT}` resolves to the plugin **cache** directory at runtime, not the repo source. Therefore Claude plugins must keep scripts co-located — never reference `../../shared/` from Claude skills.

**Spec:** `docs/superpowers/specs/2026-03-24-multi-platform-native-skills-design.md`

**Tech Stack:** Bash (file ops), Markdown (skills/commands), Python (shared scripts), Node (MCP gateway)

---

## File Inventory (current state)

| Plugin | Skills | Commands | Docs | Scripts | CLAUDE_PLUGIN_ROOT refs |
|--------|--------|----------|------|---------|------------------------|
| product-design-skill | 9 | 3 | 22 (nested) | 14 | 24 files |
| dev-forge-skill | 4 | 4 | 35 (nested) | 0 | 12 files |
| demo-forge-skill | 4 | 1 | 1 | 0 | 3 files |
| code-tuner-skill | 0 (SKILL.md only) | 1 | 0 (has references/) | 0 | 4 files |
| code-replicate-skill | 7 | 3 | 17 (nested) | 25 | 19 files |
| ui-forge-skill | 1 | 1 | 4 | 0 | 3 files |

---

## Phase A: Structure Migration

### Task 1: Create rollback tag and directory skeleton

**Files:**
- Create: `claude/` (directory)
- Create: `codex/` (directory)
- Create: `opencode/` (directory)
- Create: `shared/scripts/product-design/` (directory)
- Create: `shared/scripts/code-replicate/` (directory)
- Create: `shared/mcp-ai-gateway/` (directory)

- [ ] **Step 1: Tag current state for rollback**

```bash
git tag pre-restructure
```

- [ ] **Step 2: Create platform directories**

```bash
mkdir -p claude codex opencode shared/scripts/product-design shared/scripts/code-replicate
```

- [ ] **Step 3: Verify directories**

```bash
ls -d claude/ codex/ opencode/ shared/scripts/product-design/ shared/scripts/code-replicate/
```
Expected: all 5 directories listed without error.

- [ ] **Step 4: Add .gitkeep to empty dirs and commit**

```bash
touch claude/.gitkeep codex/.gitkeep opencode/.gitkeep shared/scripts/product-design/.gitkeep shared/scripts/code-replicate/.gitkeep
git add -A && git commit -m "chore: create platform directory skeleton"
```

---

### Task 2: Move Claude plugins into claude/

**Files:**
- Move: `product-design-skill/` → `claude/product-design-skill/`
- Move: `dev-forge-skill/` → `claude/dev-forge-skill/`
- Move: `demo-forge-skill/` → `claude/demo-forge-skill/`
- Move: `code-tuner-skill/` → `claude/code-tuner-skill/`
- Move: `code-replicate-skill/` → `claude/code-replicate-skill/`
- Move: `ui-forge-skill/` → `claude/ui-forge-skill/`
- Move: `.claude-plugin/` → `claude/.claude-plugin/`

- [ ] **Step 1: Move all 6 plugin directories + marketplace manifest**

```bash
git mv product-design-skill/ claude/
git mv dev-forge-skill/ claude/
git mv demo-forge-skill/ claude/
git mv code-tuner-skill/ claude/
git mv code-replicate-skill/ claude/
git mv ui-forge-skill/ claude/
git mv .claude-plugin/ claude/
```

- [ ] **Step 2: Verify structure**

```bash
ls claude/
```
Expected: `code-replicate-skill  code-tuner-skill  demo-forge-skill  dev-forge-skill  product-design-skill  ui-forge-skill  .claude-plugin`

- [ ] **Step 3: Verify no plugin dirs remain at root**

```bash
ls -d *-skill/ 2>/dev/null && echo "ERROR: plugin dirs still at root" || echo "OK: root clean"
```
Expected: `OK: root clean`

- [ ] **Step 4: Commit move**

```bash
git add -A && git commit -m "refactor: move all plugins into claude/ directory"
```

---

### Task 3: Update marketplace.json source paths

**Files:**
- Modify: `claude/.claude-plugin/marketplace.json`

- [ ] **Step 1: Update all source paths from `./xxx-skill/` to `./xxx-skill/` (relative to new location)**

The `source` paths in `marketplace.json` are relative to the marketplace directory. Since both `marketplace.json` and plugin dirs moved into `claude/` together, the relative paths (`./product-design-skill/`, etc.) remain correct.

Verify this:
```bash
cat claude/.claude-plugin/marketplace.json | grep '"source"'
```
Expected: all paths still show `./xxx-skill/` — these are correct because they're relative to `claude/.claude-plugin/`.

- [ ] **Step 2: Verify each plugin's plugin.json is intact**

```bash
for p in claude/*/; do
  if [ -f "$p/.claude-plugin/plugin.json" ]; then
    echo "$p: $(grep '"name"' "$p/.claude-plugin/plugin.json" | head -1)"
  fi
done
```
Expected: each plugin shows its correct name.

- [ ] **Step 3: Commit (if any changes needed)**

```bash
git diff --quiet || (git add -A && git commit -m "fix: update marketplace source paths for claude/ move")
```

---

### Task 4: Copy shared assets (Claude keeps originals)

**IMPORTANT:** Claude plugins keep their `scripts/` and `mcp-ai-gateway/` in-place (unchanged).
`shared/` gets a **copy** for codex/ and opencode/ to reference.

**Files:**
- Copy: `claude/product-design-skill/scripts/*` → `shared/scripts/product-design/`
- Copy: `claude/code-replicate-skill/scripts/*` → `shared/scripts/code-replicate/`
- Copy: `claude/product-design-skill/mcp-ai-gateway/` → `shared/mcp-ai-gateway/`

- [ ] **Step 1: Remove __pycache__ before copying**

```bash
rm -rf claude/product-design-skill/scripts/__pycache__
rm -rf claude/code-replicate-skill/scripts/__pycache__
```

- [ ] **Step 2: Copy product-design scripts**

```bash
cp -r claude/product-design-skill/scripts/* shared/scripts/product-design/
```

- [ ] **Step 3: Copy code-replicate scripts**

```bash
cp -r claude/code-replicate-skill/scripts/* shared/scripts/code-replicate/
```

- [ ] **Step 4: Copy mcp-ai-gateway**

```bash
cp -r claude/product-design-skill/mcp-ai-gateway/* shared/mcp-ai-gateway/
```

- [ ] **Step 5: Verify shared structure**

```bash
ls shared/scripts/product-design/
ls shared/scripts/code-replicate/
ls shared/mcp-ai-gateway/
```
Expected: all scripts and gateway files present in shared/.

- [ ] **Step 6: Verify Claude plugins still have their scripts**

```bash
ls claude/product-design-skill/scripts/_common.py
ls claude/code-replicate-skill/scripts/_common.py
ls claude/product-design-skill/mcp-ai-gateway/package.json
```
Expected: all files still in Claude plugins (untouched).

- [ ] **Step 7: Commit**

```bash
git add shared/ && git commit -m "chore: copy scripts and mcp-ai-gateway to shared/ for codex/opencode"
```

---

### Task 5: Verify Claude plugins are intact (no changes needed)

Since Claude plugins keep their `scripts/` and `mcp-ai-gateway/` in-place, no path updates are needed in Claude skill files. `${CLAUDE_PLUGIN_ROOT}/scripts/xxx.py` continues to resolve correctly at runtime.

- [ ] **Step 1: Verify script references still resolve within Claude plugins**

```bash
grep -rn "scripts/" claude/product-design-skill/skills/ claude/product-design-skill/commands/ claude/product-design-skill/SKILL.md 2>/dev/null | head -5
```
Expected: references use `${CLAUDE_PLUGIN_ROOT}/scripts/` which resolves to the plugin's own scripts/ directory. No changes needed.

- [ ] **Step 2: Verify mcp-ai-gateway references**

```bash
grep -rn "mcp-ai-gateway\|mcp-openrouter" claude/product-design-skill/.mcp.json 2>/dev/null
```
Expected: `.mcp.json` references `./mcp-ai-gateway/` (relative to plugin root). This still resolves correctly since mcp-ai-gateway stays in the plugin.

- [ ] **Step 3: Spot-check one CLAUDE_PLUGIN_ROOT reference**

```bash
grep -n "CLAUDE_PLUGIN_ROOT" claude/product-design-skill/SKILL.md | head -3
```
Expected: all use `${CLAUDE_PLUGIN_ROOT}/skills/`, `${CLAUDE_PLUGIN_ROOT}/docs/`, `${CLAUDE_PLUGIN_ROOT}/scripts/` — all resolve within the plugin directory. No changes needed.

---

### Task 6: Copy Claude to Codex and OpenCode platforms

**Files:**
- Create: `codex/*` (full copy from `claude/`)
- Create: `opencode/*` (full copy from `claude/`)

- [ ] **Step 1: Copy to codex/**

```bash
cp -r claude/product-design-skill/ codex/product-design-skill/
cp -r claude/dev-forge-skill/ codex/dev-forge-skill/
cp -r claude/demo-forge-skill/ codex/demo-forge-skill/
cp -r claude/code-tuner-skill/ codex/code-tuner-skill/
cp -r claude/code-replicate-skill/ codex/code-replicate-skill/
cp -r claude/ui-forge-skill/ codex/ui-forge-skill/
```

- [ ] **Step 2: Copy to opencode/**

```bash
cp -r claude/product-design-skill/ opencode/product-design-skill/
cp -r claude/dev-forge-skill/ opencode/dev-forge-skill/
cp -r claude/demo-forge-skill/ opencode/demo-forge-skill/
cp -r claude/code-tuner-skill/ opencode/code-tuner-skill/
cp -r claude/code-replicate-skill/ opencode/code-replicate-skill/
cp -r claude/ui-forge-skill/ opencode/ui-forge-skill/
```

- [ ] **Step 3: Remove .claude-plugin/ from codex and opencode**

```bash
find codex/ -name ".claude-plugin" -type d -exec rm -rf {} + 2>/dev/null
find opencode/ -name ".claude-plugin" -type d -exec rm -rf {} + 2>/dev/null
```

- [ ] **Step 4: Remove .mcp.json from codex and opencode (Claude-specific)**

```bash
find codex/ -name ".mcp.json" -delete 2>/dev/null
find opencode/ -name ".mcp.json" -delete 2>/dev/null
```

- [ ] **Step 5: Verify file counts match**

```bash
echo "Claude skills:" && find claude/ -name "*.md" -path "*/skills/*" | wc -l
echo "Codex skills:" && find codex/ -name "*.md" -path "*/skills/*" | wc -l
echo "OpenCode skills:" && find opencode/ -name "*.md" -path "*/skills/*" | wc -l
```
Expected: all three counts equal.

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "refactor: copy plugins to codex/ and opencode/ platforms"
```

---

### Task 7: Delete old wrapper directories

**Files:**
- Delete: `codex-native/`
- Delete: `opencode-native/`
- Delete: `install-opencode.sh`
- Delete: `install-remote.sh`
- Delete: `update-skills.sh` (if exists)
- Delete: `.opencode/`
- Delete: `OPENCODE_SETUP.md`
- Delete: `OPENCODE_INSTALL.md`
- Delete: `REMOTE_INSTALL.md`
- Delete: `.opencode.template` (if exists)

- [ ] **Step 1: Remove old directories and files**

```bash
git rm -rf codex-native/
git rm -rf opencode-native/
git rm -f install-opencode.sh install-remote.sh update-skills.sh .opencode.template 2>/dev/null
git rm -rf .opencode/ 2>/dev/null
git rm -f OPENCODE_SETUP.md OPENCODE_INSTALL.md REMOTE_INSTALL.md 2>/dev/null
```

- [ ] **Step 2: Verify clean root**

```bash
ls -d */ | grep -v -E "^(claude|codex|opencode|shared|docs|\.)"
```
Expected: no unexpected directories.

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "chore: remove old wrapper directories and install scripts"
```

---

### Task 7.5: Phase A smoke test

Before starting content rewrites, verify the Claude platform works from the new location.

- [ ] **Step 1: Verify a Claude plugin can be added from new path**

```bash
claude plugin add claude/code-tuner-skill 2>&1 | head -5
```
Expected: no path-related errors. If this fails, check marketplace.json source paths.

- [ ] **Step 2: Verify CLAUDE_PLUGIN_ROOT resolves scripts correctly**

Check that a skill referencing `${CLAUDE_PLUGIN_ROOT}/scripts/` would find the scripts:
```bash
ls claude/product-design-skill/scripts/_common.py
```
Expected: file exists (scripts are co-located with the plugin).

---

## Phase B: Codex Nativization

Each plugin follows the same pattern. The agent rewriting each plugin should:
1. Read the Claude version of every skill/command/doc file in the plugin
2. Apply the Codex transformation rules from the spec (Section: Skill Nativization Rules)
3. Write AGENTS.md as the entry point (Layer 0)
4. Write execution-playbook.md (Layer 1)
5. Rewrite each skill file for Codex native attention optimization (Layer 2)
6. Rewrite each command file (remove slash-command semantics)
7. Inline critical doc content into skills where it saves cross-file reads

### Task 8: Codex nativize code-tuner-skill

**Files:**
- Create: `codex/code-tuner-skill/AGENTS.md`
- Create: `codex/code-tuner-skill/execution-playbook.md`
- Modify: `codex/code-tuner-skill/SKILL.md` (rewrite for Codex)
- Modify: `codex/code-tuner-skill/commands/code-tuner.md` (rewrite)
- Modify: `codex/code-tuner-skill/references/phase0-profile.md` (remove CLAUDE_PLUGIN_ROOT)

- [ ] **Step 1: Read all Claude source files for this plugin**

```bash
find claude/code-tuner-skill/ -name "*.md" -type f
```
Read each file to understand the full domain logic.

- [ ] **Step 2: Write AGENTS.md (Layer 0 entry)**

Create `codex/code-tuner-skill/AGENTS.md` with:
- Role description
- Available workflows (code-tuner full / compliance / duplication / abstraction / report)
- Trigger rules
- Link to execution-playbook.md for details
- Keep under 50 lines — this is the attention-minimal entry.

- [ ] **Step 3: Write execution-playbook.md (Layer 1)**

Create `codex/code-tuner-skill/execution-playbook.md` with:
- Phase table (phase → goal → outputs → completion signal)
- Orchestration rules (autonomous mode, minimal asking)
- Script references to `../../shared/` if applicable

- [ ] **Step 4: Rewrite SKILL.md for Codex**

Replace Claude-specific SKILL.md with Codex-native version:
- Remove `${CLAUDE_PLUGIN_ROOT}` references
- Remove `allowed-tools` frontmatter
- Use relative paths
- Description field optimized for Codex trigger matching

- [ ] **Step 5: Rewrite commands/code-tuner.md**

- Remove slash-command frontmatter semantics
- Convert to workflow description
- Replace AskUserQuestion with assumption+declaration pattern
- Remove `allowed-tools`

- [ ] **Step 6: Update references/phase0-profile.md**

- Remove `${CLAUDE_PLUGIN_ROOT}` references
- Use relative paths

- [ ] **Step 7: Verify no Claude-specific references remain**

```bash
grep -rn 'CLAUDE_PLUGIN_ROOT\|AskUserQuestion\|allowed-tools\|mcp__plugin_' codex/code-tuner-skill/
```
Expected: no output.

- [ ] **Step 8: Commit**

```bash
git add codex/code-tuner-skill/ && git commit -m "feat(codex): nativize code-tuner-skill"
```

---

### Task 9: Codex nativize code-replicate-skill

**Files:**
- Create: `codex/code-replicate-skill/AGENTS.md`
- Create: `codex/code-replicate-skill/execution-playbook.md`
- Modify: `codex/code-replicate-skill/SKILL.md`
- Modify: `codex/code-replicate-skill/skills/*.md` (7 files)
- Modify: `codex/code-replicate-skill/commands/*.md` (3 files)
- Modify: `codex/code-replicate-skill/docs/**/*.md` (17 files)

- [ ] **Step 1: Read all Claude source files**

Read all 30 files in `claude/code-replicate-skill/` to understand domain logic.

- [ ] **Step 2: Write AGENTS.md (Layer 0)**

Entry point with workflow list: code-replicate (interface/functional/architecture/exact modes), cr-fidelity, cr-visual.

- [ ] **Step 3: Write execution-playbook.md (Layer 1)**

Phase-by-phase orchestration for all workflows. Include:
- Phase 1: Discovery (cr_discover.py)
- Phase 2: Structure analysis (stage-a through stage-d)
- Phase 3: Artifact generation
- Phase 4: Verification/handoff
- Script references: `../../shared/scripts/code-replicate/`

- [ ] **Step 4: Rewrite all 7 skill files per Codex rules**

For each skill in `codex/code-replicate-skill/skills/`:
- `code-replicate-core.md` — main orchestration skill
- `cr-backend.md`, `cr-frontend.md`, `cr-fullstack.md`, `cr-module.md` — variant workflows
- `cr-fidelity.md` — fidelity verification
- `cr-visual.md` — visual comparison

Apply: remove CLAUDE_PLUGIN_ROOT, remove allowed-tools, replace AskUserQuestion with assumptions, inline critical doc content, use relative paths.

- [ ] **Step 5: Rewrite all 3 command files**

`code-replicate.md`, `cr-fidelity.md`, `cr-visual.md` — convert from slash-command to workflow descriptions.

- [ ] **Step 6: Update all 17 doc files**

Remove CLAUDE_PLUGIN_ROOT from docs that reference it (phase2/stage-a-structure.md, phase2/stage-b-runtime.md).

- [ ] **Step 7: Verify no Claude references**

```bash
grep -rn 'CLAUDE_PLUGIN_ROOT\|AskUserQuestion\|allowed-tools\|mcp__plugin_' codex/code-replicate-skill/
```
Expected: no output.

- [ ] **Step 8: Commit**

```bash
git add codex/code-replicate-skill/ && git commit -m "feat(codex): nativize code-replicate-skill"
```

---

### Task 10: Codex nativize ui-forge-skill

**Files:**
- Create: `codex/ui-forge-skill/AGENTS.md`
- Create: `codex/ui-forge-skill/execution-playbook.md`
- Modify: `codex/ui-forge-skill/SKILL.md`
- Modify: `codex/ui-forge-skill/skills/ui-forge.md`
- Modify: `codex/ui-forge-skill/commands/ui-forge.md`
- Modify: `codex/ui-forge-skill/docs/*.md` (4 files)

- [ ] **Step 1: Read all Claude source files**
- [ ] **Step 2: Write AGENTS.md (Layer 0)**
- [ ] **Step 3: Write execution-playbook.md (Layer 1)**
- [ ] **Step 4: Rewrite skill and command files per Codex rules**
- [ ] **Step 5: Update doc files**
- [ ] **Step 6: Verify no Claude references**

```bash
grep -rn 'CLAUDE_PLUGIN_ROOT\|AskUserQuestion\|allowed-tools\|mcp__plugin_' codex/ui-forge-skill/
```

- [ ] **Step 7: Commit**

```bash
git add codex/ui-forge-skill/ && git commit -m "feat(codex): nativize ui-forge-skill"
```

---

### Task 11: Codex nativize demo-forge-skill

**Files:**
- Create: `codex/demo-forge-skill/AGENTS.md`
- Create: `codex/demo-forge-skill/execution-playbook.md`
- Modify: `codex/demo-forge-skill/SKILL.md`
- Modify: `codex/demo-forge-skill/skills/*.md` (4 files: demo-design, media-forge, demo-execute, demo-verify)
- Modify: `codex/demo-forge-skill/commands/demo-forge.md`
- Modify: `codex/demo-forge-skill/docs/demo-data-design.md`

Medium complexity: media service degradation chains, Playwright verification, multi-round iteration.

- [ ] **Step 1: Read all Claude source files**
- [ ] **Step 2: Write AGENTS.md with workflow modes (full/design/media/execute/verify/clean)**
- [ ] **Step 3: Write execution-playbook.md with 5-phase pipeline + degradation rules**

Include: Image chain (Imagen 4 → GPT-5 Image → FLUX 2 Pro → skip), Video chain (Veo 3.1 → Kling → skip).

- [ ] **Step 4: Rewrite all 4 skill files per Codex rules**
- [ ] **Step 5: Rewrite command file**
- [ ] **Step 6: Update doc files**
- [ ] **Step 7: Verify no Claude references**

```bash
grep -rn 'CLAUDE_PLUGIN_ROOT\|AskUserQuestion\|allowed-tools\|mcp__plugin_' codex/demo-forge-skill/
```

- [ ] **Step 8: Commit**

```bash
git add codex/demo-forge-skill/ && git commit -m "feat(codex): nativize demo-forge-skill"
```

---

### Task 12: Codex nativize dev-forge-skill

**Files:**
- Create: `codex/dev-forge-skill/AGENTS.md`
- Create: `codex/dev-forge-skill/execution-playbook.md`
- Modify: `codex/dev-forge-skill/SKILL.md`
- Modify: `codex/dev-forge-skill/skills/*.md` (4 files: design-to-spec, task-execute, product-verify, + seed-forge if exists)
- Modify: `codex/dev-forge-skill/commands/*.md` (4 files: project-forge, testforge, deadhunt, fieldcheck)
- Modify: `codex/dev-forge-skill/docs/**/*.md` (35 files across testforge/, deadhunt/, design-to-spec/, field-specs/)

High complexity: multi-phase orchestration, parallel agent dispatch, template system, deadhunt/fieldcheck subcommands.

- [ ] **Step 1: Read all Claude source files (prioritize skills/ and commands/)**
- [ ] **Step 2: Write AGENTS.md with all workflow entries**

Workflows: project-forge (full/resume), design-to-spec, task-execute, testforge, deadhunt (static/deep/full/incremental), fieldcheck (full/frontend/backend/endtoend), seed-forge, product-verify.

- [ ] **Step 3: Write execution-playbook.md with 8-phase pipeline**

Phases 0-8 from the existing orchestration. Include:
- Sub-project routing logic
- Backend-first → frontend-parallel spec generation
- Task batching and progress tracking via build-log.json
- Deadhunt/fieldcheck as sub-workflows

- [ ] **Step 4: Rewrite all skill files per Codex rules**

Special attention to:
- `design-to-spec.md`: has Agent parallel dispatch → convert to "execute in parallel" description
- `task-execute.md`: has Task progress tracking → convert to .allforai/ artifact checks
- `product-verify.md`: has Playwright orchestration → document as optional capability

- [ ] **Step 5: Rewrite all 4 command files**
- [ ] **Step 6: Update all 35 doc files (remove CLAUDE_PLUGIN_ROOT, update paths)**

Focus on files with CLAUDE_PLUGIN_ROOT: testforge/phase4-forge-loop.md, deadhunt/phase3-test.md, deadhunt/fieldcheck/overview.md, execution-batches.md.

- [ ] **Step 7: Verify no Claude references**

```bash
grep -rn 'CLAUDE_PLUGIN_ROOT\|AskUserQuestion\|allowed-tools\|mcp__plugin_' codex/dev-forge-skill/
```

- [ ] **Step 8: Commit**

```bash
git add codex/dev-forge-skill/ && git commit -m "feat(codex): nativize dev-forge-skill"
```

---

### Task 13: Codex nativize product-design-skill

**Files:**
- Create: `codex/product-design-skill/AGENTS.md`
- Create: `codex/product-design-skill/execution-playbook.md`
- Modify: `codex/product-design-skill/SKILL.md`
- Modify: `codex/product-design-skill/skills/*.md` (9 files)
- Modify: `codex/product-design-skill/commands/*.md` (3 files: product-design, review, setup)
- Modify: `codex/product-design-skill/docs/**/*.md` (22 files across schemas/, design-audit/, experience-map/, product-map/, ui-design/)

Highest complexity: 10+ sub-skills, parallel agent execution (phases 4-7), Python script orchestration, MCP XV integration, review hub server.

- [ ] **Step 1: Read all Claude source files (prioritize SKILL.md, skills/, commands/)**

- [ ] **Step 2: Write AGENTS.md with all sub-skill entries**

Sub-skills: product-concept, product-map, journey-emotion, experience-map, interaction-gate, use-case, feature-gap, feature-prune, ui-design, design-audit.
Orchestration: product-design full / resume / skip.
Setup: setup (OpenRouter/Google/fal.ai configuration).
Review: review hub.

- [ ] **Step 3: Write execution-playbook.md with 10-phase pipeline**

Include:
- Phase 0: Artifact detection + XV status
- Phase 1: product-concept (optional, WebSearch-heavy)
- Phase 2: product-map (6 steps, index generation)
- Phase 3: journey-emotion (human decision point)
- Phase 3.5: design-pattern (pattern recognition)
- Phase 3.6: behavioral-standards (9 behavior types)
- Phase 4-7: parallel execution (experience-map, use-case, feature-gap, feature-prune) — describe as "these 4 phases can execute in parallel"
- Phase 8: ui-design
- Phase 9: design-audit
- Script references: `../../shared/scripts/product-design/gen_xxx.py`
- MCP references: `../../shared/mcp-ai-gateway/`

- [ ] **Step 4: Rewrite all 9 skill files per Codex rules**

Each skill needs:
- CLAUDE_PLUGIN_ROOT → relative paths
- AskUserQuestion → assumption+declaration
- Agent parallel dispatch → "execute in parallel" descriptions
- Inline critical schemas from docs/schemas/ to reduce Layer 3 reads
- Script invocation paths updated to shared/

Special attention:
- `product-concept.md`: heavy WebSearch usage → describe search intent
- `product-map.md`: 6 extraction steps, data model generation
- `experience-map.md`: complex generation + validation steps
- `design-audit.md`: multi-dimensional audit (reverse trace, flood, lateral, innovation, behavioral)

- [ ] **Step 5: Rewrite all 3 command files**

- `product-design.md`: main orchestration command → workflow description
- `review.md`: review hub (review_hub_server.py at shared/) → document as optional
- `setup.md`: MCP/service key configuration → describe setup intent

- [ ] **Step 6: Update all 22 doc files**

Remove CLAUDE_PLUGIN_ROOT from: design-audit/fix-rules.md, design-audit/audit-dimensions.md, experience-map/generation-steps.md, experience-map/validation-steps.md, product-map/*.md, ui-design/design-steps.md.

- [ ] **Step 7: Verify no Claude references**

```bash
grep -rn 'CLAUDE_PLUGIN_ROOT\|AskUserQuestion\|allowed-tools\|mcp__plugin_' codex/product-design-skill/
```

- [ ] **Step 8: Commit**

```bash
git add codex/product-design-skill/ && git commit -m "feat(codex): nativize product-design-skill"
```

---

## Phase C: OpenCode Nativization

Same plugin order as Phase B. Can run in parallel with Phase B. Each plugin follows the same pattern but applies OpenCode transformation rules instead of Codex rules.

Key OpenCode differences from Codex:
- Entry: SKILL.md (not AGENTS.md) — OpenCode has skills.json registration
- Interaction: natural language questions (not assumption+declaration)
- Tools: keep `allowed-tools` as descriptive metadata
- MCP: `mcp__openrouter__*` naming (not Claude's `mcp__plugin_xxx__*`)
- Subagents: OpenCode subagent mechanism where supported

### Task 14: OpenCode nativize code-tuner-skill

**Files:**
- Modify: `opencode/code-tuner-skill/SKILL.md` (rewrite as OpenCode entry)
- Create: `opencode/code-tuner-skill/execution-playbook.md`
- Modify: `opencode/code-tuner-skill/commands/code-tuner.md`
- Modify: `opencode/code-tuner-skill/references/phase0-profile.md`

- [ ] **Step 1: Read Claude source + review Codex version for reference**
- [ ] **Step 2: Write SKILL.md as OpenCode entry (Layer 0+1)**

YAML frontmatter with `name` + `description` (for skills.json matching).
Workflow overview + sub-skill index.

- [ ] **Step 3: Write execution-playbook.md (Layer 3)**

Phase orchestration with explicit transition logic.

- [ ] **Step 4: Rewrite command and reference files per OpenCode rules**
- [ ] **Step 5: Verify no Claude references**

```bash
grep -rn 'CLAUDE_PLUGIN_ROOT\|AskUserQuestion\|allowed-tools\|mcp__plugin_' opencode/code-tuner-skill/
```

- [ ] **Step 6: Commit**

```bash
git add opencode/code-tuner-skill/ && git commit -m "feat(opencode): nativize code-tuner-skill"
```

---

### Task 15: OpenCode nativize code-replicate-skill

**Files:** Same scope as Task 9 but OpenCode rules.

- [ ] **Step 1: Read Claude source + review Codex version**
- [ ] **Step 2: Write SKILL.md as OpenCode entry**
- [ ] **Step 3: Write execution-playbook.md**
- [ ] **Step 4: Rewrite all 7 skill files per OpenCode rules**
- [ ] **Step 5: Rewrite all 3 command files**
- [ ] **Step 6: Update all 17 doc files**
- [ ] **Step 7: Verify no Claude references**

```bash
grep -rn 'CLAUDE_PLUGIN_ROOT\|AskUserQuestion\|allowed-tools\|mcp__plugin_' opencode/code-replicate-skill/
```

- [ ] **Step 8: Commit**

```bash
git add opencode/code-replicate-skill/ && git commit -m "feat(opencode): nativize code-replicate-skill"
```

---

### Task 16: OpenCode nativize ui-forge-skill

- [ ] **Step 1-5: Same pattern as Task 10 but OpenCode rules**
- [ ] **Step 6: Verify + Commit**

```bash
grep -rn 'CLAUDE_PLUGIN_ROOT\|AskUserQuestion\|allowed-tools\|mcp__plugin_' opencode/ui-forge-skill/
git add opencode/ui-forge-skill/ && git commit -m "feat(opencode): nativize ui-forge-skill"
```

---

### Task 17: OpenCode nativize demo-forge-skill

- [ ] **Step 1-6: Same pattern as Task 11 but OpenCode rules**

Special: MCP tool names `mcp__plugin_product-design_openrouter__*` → `mcp__openrouter__*`.

- [ ] **Step 7: Verify + Commit**

```bash
grep -rn 'CLAUDE_PLUGIN_ROOT\|AskUserQuestion\|allowed-tools\|mcp__plugin_' opencode/demo-forge-skill/
git add opencode/demo-forge-skill/ && git commit -m "feat(opencode): nativize demo-forge-skill"
```

---

### Task 18: OpenCode nativize dev-forge-skill

- [ ] **Step 1-7: Same pattern as Task 12 but OpenCode rules**

Special: Agent tool → OpenCode subagent mechanism.

- [ ] **Step 8: Verify + Commit**

```bash
grep -rn 'CLAUDE_PLUGIN_ROOT\|AskUserQuestion\|allowed-tools\|mcp__plugin_' opencode/dev-forge-skill/
git add opencode/dev-forge-skill/ && git commit -m "feat(opencode): nativize dev-forge-skill"
```

---

### Task 19: OpenCode nativize product-design-skill

- [ ] **Step 1-7: Same pattern as Task 13 but OpenCode rules**

Special attention:
- MCP naming: all `mcp__plugin_product-design_openrouter__*` → `mcp__openrouter__*`
- Script paths: `../../shared/scripts/product-design/`
- Review hub: reference `../../shared/scripts/product-design/review_hub_server.py`

- [ ] **Step 8: Verify + Commit**

```bash
grep -rn 'CLAUDE_PLUGIN_ROOT\|AskUserQuestion\|allowed-tools\|mcp__plugin_' opencode/product-design-skill/
git add opencode/product-design-skill/ && git commit -m "feat(opencode): nativize product-design-skill"
```

---

## Phase D: Finalization

### Task 20: Write platform install scripts

**Files:**
- Create: `claude/install.sh`
- Create: `codex/install.sh`
- Create: `opencode/install.sh`

- [ ] **Step 1: Write claude/install.sh**

```bash
#!/usr/bin/env bash
# Install myskills Claude Code plugins
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Installing myskills Claude Code plugins..."
for plugin in product-design-skill dev-forge-skill demo-forge-skill code-tuner-skill code-replicate-skill ui-forge-skill; do
  if [ -d "$SCRIPT_DIR/$plugin" ]; then
    echo "  Adding $plugin..."
    claude plugin add "$SCRIPT_DIR/$plugin" 2>/dev/null || echo "  Warning: could not add $plugin (is claude CLI available?)"
  fi
done

# Build MCP gateway if needed
if [ -d "$SCRIPT_DIR/../shared/mcp-ai-gateway" ]; then
  echo "Building MCP AI Gateway..."
  cd "$SCRIPT_DIR/../shared/mcp-ai-gateway"
  npm install && npm run build
fi

echo "Done. Run 'claude' to start using the plugins."
```

- [ ] **Step 2: Write codex/install.sh**

Codex installation (copy AGENTS.md to project, configure paths).

- [ ] **Step 3: Write opencode/install.sh**

OpenCode installation (write skills.json with correct paths, build MCP gateway).
Based on the old `install-opencode.sh` but with updated paths pointing to `opencode/`.

- [ ] **Step 4: Make all scripts executable**

```bash
chmod +x claude/install.sh codex/install.sh opencode/install.sh
```

- [ ] **Step 5: Commit**

```bash
git add claude/install.sh codex/install.sh opencode/install.sh
git commit -m "feat: add per-platform install scripts"
```

---

### Task 21: Write MIGRATION.md

**Files:**
- Create: `MIGRATION.md`

- [ ] **Step 1: Write migration guide**

Include:
- What changed and why (one paragraph)
- Per-platform re-install steps:
  - Claude Code: `claude plugin remove <name>` then `claude plugin add myskills/claude/<plugin>`
  - OpenCode: re-run `opencode/install.sh`
  - Codex: run `codex/install.sh`
- Remote users: `git pull` then re-run platform install script
- Breaking changes table (from spec)

- [ ] **Step 2: Commit**

```bash
git add MIGRATION.md && git commit -m "docs: add migration guide for restructure"
```

---

### Task 22: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update all path references**

Replace:
- `product-design-skill/` → `claude/product-design-skill/`
- `dev-forge-skill/` → `claude/dev-forge-skill/`
- Same for all other plugins
- `scripts/` references → `shared/scripts/`
- Update directory structure diagram
- Update install commands
- Update version numbers

- [ ] **Step 2: Verify no stale paths**

```bash
grep -n "product-design-skill/" CLAUDE.md | grep -v "claude/"
```
Expected: no output (all paths prefixed with platform).

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md && git commit -m "docs: update CLAUDE.md paths for restructured layout"
```

---

### Task 23: Version bump all plugins

**Files:**
- Modify: `claude/*-skill/.claude-plugin/plugin.json` (6 files)
- Modify: `claude/.claude-plugin/marketplace.json`

Version bumps:
- product-design: 4.17.1 → 5.0.0
- dev-forge: 5.9.1 → 6.0.0
- demo-forge: 1.3.2 → 2.0.0
- code-tuner: 1.1.2 → 2.0.0
- code-replicate: 4.0.0 → 5.0.0
- ui-forge: 0.1.2 → 1.0.0

- [ ] **Step 1: Update each plugin.json version**

```bash
for pair in "product-design-skill:5.0.0" "dev-forge-skill:6.0.0" "demo-forge-skill:2.0.0" "code-tuner-skill:2.0.0" "code-replicate-skill:5.0.0" "ui-forge-skill:1.0.0"; do
  plugin="${pair%%:*}"
  version="${pair##*:}"
  # Update plugin.json
  sed -i "s/\"version\": \"[^\"]*\"/\"version\": \"$version\"/" "claude/$plugin/.claude-plugin/plugin.json"
done
```

- [ ] **Step 2: Update marketplace.json versions**

Update each plugin's version in `claude/.claude-plugin/marketplace.json` to match.

- [ ] **Step 3: Verify versions**

```bash
grep '"version"' claude/*-skill/.claude-plugin/plugin.json
grep '"version"' claude/.claude-plugin/marketplace.json
```

- [ ] **Step 4: Commit**

```bash
git add claude/ && git commit -m "chore: major version bump for restructure (v5/v6/v2/v1)"
```

---

### Task 24: Final verification and tag

- [ ] **Step 1: Verify Claude platform — no broken CLAUDE_PLUGIN_ROOT references**

```bash
grep -rn 'CLAUDE_PLUGIN_ROOT' claude/ | grep -v '${CLAUDE_PLUGIN_ROOT}' | head -5
```
Expected: all references use `${CLAUDE_PLUGIN_ROOT}` variable syntax (valid).

- [ ] **Step 2: Verify Codex platform — zero Claude-specific references**

```bash
grep -rn 'CLAUDE_PLUGIN_ROOT\|AskUserQuestion\|allowed-tools\|mcp__plugin_' codex/
```
Expected: no output.

- [ ] **Step 3: Verify OpenCode platform — zero Claude-specific references**

```bash
grep -rn 'CLAUDE_PLUGIN_ROOT\|AskUserQuestion\|allowed-tools\|mcp__plugin_' opencode/
```
Expected: no output.

- [ ] **Step 4: Verify shared/ contains only scripts and mcp-ai-gateway**

```bash
ls shared/
```
Expected: `mcp-ai-gateway  scripts`

- [ ] **Step 5: Verify no skill files in shared/**

```bash
find shared/ -name "*.md" -path "*/skills/*" | wc -l
```
Expected: 0

- [ ] **Step 6: Count files per platform (sanity check)**

```bash
echo "Claude:" && find claude/ -name "*.md" | wc -l
echo "Codex:" && find codex/ -name "*.md" | wc -l
echo "OpenCode:" && find opencode/ -name "*.md" | wc -l
```
Expected: similar counts (Codex/OpenCode will have extra AGENTS.md/execution-playbook.md files).

- [ ] **Step 7: Tag release**

```bash
git tag v5.0.0-restructure
```

- [ ] **Step 8: Final commit if needed**

```bash
git status
# If clean, done. If not, commit remaining changes.
```

---

## Execution Notes

### Parallelization

- **Phase B tasks (8-13) are independent** — can dispatch 6 parallel agents, one per plugin
- **Phase C tasks (14-19) are independent** — can dispatch 6 parallel agents
- **Phase B and Phase C can run in parallel** — Codex and OpenCode rewrites don't depend on each other
- **Maximum parallelism:** 12 agents (6 Codex + 6 OpenCode plugins) after Phase A completes

### Single-implementer recommendation

If one person does both Phase B and C:
1. Do one plugin fully across both platforms (e.g., code-tuner Codex + OpenCode)
2. Verify the pattern works
3. Then parallelize the remaining 5 plugins

### Risk mitigation

- `pre-restructure` tag allows instant rollback of Phase A
- Each Phase B/C task commits independently — can revert individual plugins
- Claude platform is never modified after Phase A (content-frozen)
