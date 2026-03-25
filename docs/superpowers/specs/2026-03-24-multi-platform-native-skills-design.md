# Multi-Platform Native Skills Reorganization

> Date: 2026-03-24
> Status: Approved
> Scope: All 6 plugins across 3 platforms (Claude Code, Codex, OpenCode)

## Problem

Current myskills repository has a single canonical implementation (Claude Code plugins) with thin wrapper layers for Codex (`codex-native/`) and OpenCode (`opencode-native/`). The wrappers reference or summarize source files rather than providing complete native implementations. This sacrifices platform-native effectiveness for code reuse.

## Design Principles

1. **Native first** — each platform uses its own tool names, interaction patterns, plugin registration, and attention management. Never sacrifice native effectiveness for cross-platform abstraction.
2. **Attention management is king** — skill effectiveness depends on what gets loaded when. Each platform has different context window sizes, loading mechanisms, and progressive disclosure patterns. Attention layering must be independently optimized per platform.
3. **Prefer duplication over lossy abstraction** — three copies of a skill file, each optimized for its platform, is better than one shared template that compromises all three.
4. **Claude 100% equivalent** — Claude Code plugin content is unchanged (only directory location moves). Existing behavior is preserved exactly.
5. **Functional equivalence** — all three platforms produce identical `.allforai/` output for the same input. Same phases, same schemas, same quality standards.
6. **One-time breaking change** — accept path breakage for Claude/OpenCode users, mitigated by MIGRATION.md and new install scripts.

## Target Directory Structure

```
myskills/
├── claude/                         # Claude Code platform
│   ├── install.sh                  # Claude Code installation script
│   ├── .claude-plugin/             # Root marketplace manifest
│   ├── product-design-skill/       # Moved from root, content unchanged
│   │   ├── .claude-plugin/
│   │   ├── skills/
│   │   ├── commands/
│   │   ├── docs/
│   │   └── SKILL.md
│   ├── dev-forge-skill/
│   ├── demo-forge-skill/
│   ├── code-tuner-skill/
│   ├── code-replicate-skill/
│   └── ui-forge-skill/
│
├── codex/                          # Codex platform (fully native)
│   ├── install.sh
│   ├── product-design-skill/
│   │   ├── AGENTS.md               # Codex native entry point
│   │   ├── skills/                 # Full skill content, Codex attention-optimized
│   │   ├── commands/
│   │   ├── docs/
│   │   └── execution-playbook.md
│   ├── dev-forge-skill/
│   ├── demo-forge-skill/
│   ├── code-tuner-skill/
│   ├── code-replicate-skill/
│   └── ui-forge-skill/
│
├── opencode/                       # OpenCode platform (fully native)
│   ├── install.sh
│   ├── product-design-skill/
│   │   ├── SKILL.md                # OpenCode native entry point
│   │   ├── skills/
│   │   ├── commands/
│   │   ├── docs/
│   │   └── execution-playbook.md
│   ├── dev-forge-skill/
│   ├── demo-forge-skill/
│   ├── code-tuner-skill/
│   ├── code-replicate-skill/
│   └── ui-forge-skill/
│
├── shared/                         # Platform-agnostic assets only
│   ├── scripts/
│   │   ├── product-design/         # From product-design-skill/scripts/
│   │   │   ├── _common.py
│   │   │   ├── gen_aggregate_checkpoint.py
│   │   │   ├── gen_business_flows.py
│   │   │   ├── gen_data_model.py
│   │   │   ├── gen_design_audit.py
│   │   │   ├── gen_experience_map.py
│   │   │   ├── gen_product_map.py
│   │   │   ├── gen_validation_report.py
│   │   │   ├── gen_view_objects.py
│   │   │   ├── review_hub_server.py
│   │   │   ├── stitch_oauth.py
│   │   │   ├── verify_review.py
│   │   │   ├── verify_wireframes.py
│   │   │   └── xv_prompts.py
│   │   └── code-replicate/         # From code-replicate-skill/scripts/
│   │       ├── _common.py
│   │       ├── cr_discover.py
│   │       ├── cr_gen_*.py
│   │       ├── cr_merge_*.py
│   │       ├── cr_validate.py
│   │       └── test_*.py           # Tests co-located with source scripts
│   ├── mcp-ai-gateway/             # Unified MCP gateway (Node service, requires npm build)
│   └── schemas/                    # .allforai/ JSON schema definitions (new work, Phase D)
│
├── CLAUDE.md                       # Project instructions (path refs updated)
└── MIGRATION.md                    # One-time migration guide
```

## Attention Layering Strategy (Per Platform)

### Claude Code (unchanged)

```
Layer 0 — Always loaded: SKILL.md (entry point, ~200 lines, all sub-skill descriptions)
Layer 1 — On-demand: skills/*.md (loaded when user triggers specific skill via description match)
Layer 2 — Deferred: docs/*.md (loaded via "详见 ${CLAUDE_PLUGIN_ROOT}/docs/xxx.md" references)
Layer 3 — Index-first: task-index.json / flow-index.json loaded before full JSON
```

Mechanism: Claude plugin system auto-manages. SKILL.md is resident, skills loaded by description match, docs by reference. No changes.

### Codex (native redesign)

```
Layer 0 — AGENTS.md: minimal entry (role + workflow list + trigger rules)
Layer 1 — execution-playbook.md: phase-level orchestration (what, order, completion signals)
Layer 2 — skills/*.md: single-phase execution instructions (read only when entering that phase)
Layer 3 — docs/*.md: reference docs (read only when explicitly instructed by skill)
```

Key differences from Claude:
- No plugin system; AGENTS.md is the entry router
- Higher autonomy: assumptions + declarations replace AskUserQuestion
- Skills must be more self-contained (inline key info from docs to reduce cross-file reads)
- No `${CLAUDE_PLUGIN_ROOT}` — use relative paths

### OpenCode (native redesign)

```
Layer 0 — skills.json registration: name + description (runtime does matching)
Layer 1 — SKILL.md: workflow overview + sub-skill index (loaded after match)
Layer 2 — skills/*.md: full execution instructions per skill
Layer 3 — execution-playbook.md: full/resume mode orchestration
Layer 4 — docs/*.md: on-demand reference
```

Key differences from Claude:
- skills.json registration mechanism (similar to Claude's plugin system)
- Natural conversation for interaction (not structured AskUserQuestion)
- `$ARGUMENTS` inferred from natural language
- MCP naming: `mcp__openrouter__*` (not `mcp__plugin_product-design_openrouter__*`)
- execution-playbook must be more explicit about phase transitions (no plugin orchestration semantics)

## Skill Nativization Rules

### Claude → Codex Transformation

| Claude Element | Codex Native Replacement |
|---|---|
| `${CLAUDE_PLUGIN_ROOT}/skills/xxx.md` | `./skills/xxx.md` (relative path) |
| `${CLAUDE_PLUGIN_ROOT}/docs/xxx.md` | `./docs/xxx.md` or `../../shared/docs/xxx.md` |
| `AskUserQuestion` decision gates | Declare assumption + continue; ask only when blocking |
| `allowed-tools: [Read, Edit, ...]` | Remove; Codex selects tools autonomously |
| `Agent` tool parallel dispatch | Describe as "execute in parallel"; Codex decides how |
| `Task` progress tracking | `.allforai/` artifact existence checks |
| `WebSearch` | Describe intent "search for xxx"; Codex chooses method |
| `/command arg` slash commands | Workflow name + mode (natural language) |
| `> 详见 xxx.md` deferred loading | `Read ./xxx.md when needed` explicit instruction |
| YAML frontmatter `name` + `description` | Keep (Codex uses this for trigger matching) |

Additional: Inline critical doc content into skill files to reduce cross-file reads (Codex context is precious).

### Claude → OpenCode Transformation

| Claude Element | OpenCode Native Replacement |
|---|---|
| `${CLAUDE_PLUGIN_ROOT}/skills/xxx.md` | Relative or absolute path |
| `AskUserQuestion` decision gates | Natural language question (only when blocking) |
| `allowed-tools: [...]` | Keep as descriptive metadata, not enforced |
| `Agent` tool parallel dispatch | OpenCode subagent mechanism (if supported), else sequential |
| `Task` progress tracking | `.allforai/` artifact detection + execution logs |
| `WebSearch` | OpenCode native search tool |
| `/command arg` | Keep as workflow label, infer args from natural language |
| YAML frontmatter | Keep; OpenCode skills.json depends on `name` + `description` |
| `mcp__plugin_product-design_openrouter__*` | `mcp__openrouter__*` (OpenCode MCP naming) |

Additional: execution-playbook must be more detailed about phase transition logic (no implicit plugin orchestration).

### Unchanged Across All Platforms

- `.allforai/` output structure and JSON schemas
- Python script invocation: `python3 ../../shared/scripts/product-design/gen_xxx.py <BASE_PATH>` (relative path valid only from `{platform}/{plugin}-skill/` level)
- Domain logic semantics (phase steps, quality standards, completion conditions)
- Pure domain knowledge documents (no platform semantics)

## shared/ Scope

### Included (platform-agnostic, zero-loss sharing)

- `scripts/product-design/` — Python data transform scripts (from product-design-skill/scripts/)
- `scripts/code-replicate/` — Python reverse-engineering scripts (from code-replicate-skill/scripts/)
- `mcp-ai-gateway/` — Node MCP gateway service (from product-design-skill/mcp-ai-gateway/); each platform's install script must handle `npm install && npm run build` at `shared/mcp-ai-gateway/`
- `schemas/` — `.allforai/` JSON schema definitions (new work, deferred to Phase D to keep migration scope bounded)

### Excluded (platform-specific, each platform maintains its own)

- Skill files (`skills/*.md`)
- Command files (`commands/*.md`)
- Plugin manifests (`.claude-plugin/`, `AGENTS.md`, `skills.json`)
- Orchestration logic (`execution-playbook.md`)
- docs/ referenced by skills (copied into each platform to avoid cross-directory attention leaks)

### Reference Method

All platforms use relative paths to shared/:
```
python3 ../../shared/scripts/gen_xxx.py <BASE_PATH>
```

No symlinks. Direct relative path references.

## Migration Plan

### Execution Phases

**Phase A — Structure Migration (mechanical, no content changes)**

1. Create directories: `claude/`, `codex/`, `opencode/`, `shared/`
2. Move Claude plugins: `mv {plugin}-skill/ claude/`
3. Update Claude internal path references (plugin.json, marketplace.json source paths, SKILL.md)
4. **Copy** (not move) shared assets: product-design-skill/scripts/ → `shared/scripts/product-design/`, code-replicate-skill/scripts/ → `shared/scripts/code-replicate/`, product-design-skill/mcp-ai-gateway/ → `shared/mcp-ai-gateway/`. Claude plugins **keep their originals** — `${CLAUDE_PLUGIN_ROOT}` resolves to plugin cache, not repo source, so scripts must stay co-located.
5. Claude skill files remain unchanged (no path updates needed). shared/ is referenced only by codex/ and opencode/.
6. Copy `claude/` to `codex/` and `opencode/`
7. Remove `.claude-plugin/` from codex/ and opencode/

**Rollback**: Tag `pre-restructure` before Step 2. If anything breaks, `git reset --hard pre-restructure`.

**Note**: deadhunt and fieldcheck are subcommands of dev-forge, not separate plugins. Do not create separate directories for them.

**Phase B — Codex Nativization (per-plugin rewrite)**

Order by complexity (low → high):
1. code-tuner-skill (~4 skills, low complexity)
2. code-replicate-skill (~3 skills, low)
3. ui-forge-skill (~3 skills, low)
4. demo-forge-skill (~5 skills, medium)
5. dev-forge-skill (~8 skills, high)
6. product-design-skill (~15 skills, high)

Per plugin:
- Add AGENTS.md entry point
- Rewrite skills/*.md per Codex transformation rules
- Rewrite commands/*.md for Codex command format
- Write execution-playbook.md with phase orchestration
- Optimize attention layering (inline critical docs)

**Phase C — OpenCode Nativization (per-plugin rewrite)**

Same order as Phase B. Can run in parallel with Phase B.

Per plugin:
- Write SKILL.md entry point (OpenCode native)
- Rewrite skills/*.md per OpenCode transformation rules
- Rewrite commands/*.md for OpenCode command format
- Write execution-playbook.md with explicit phase transitions
- Configure skills.json registration

**Phase D — Finalization**

1. Write `claude/install.sh`, `codex/install.sh`, `opencode/install.sh`
2. Write `MIGRATION.md` (path changes, re-install steps per platform)
3. Update `CLAUDE.md` (all path references)
4. Major version bump all plugins (see Version Bump section)
5. Delete old files: `codex-native/`, `opencode-native/`, `install-opencode.sh`, `install-remote.sh`, root `.opencode/`
6. Commit and tag

### Breaking Changes

| Affected | Change | User Action |
|---|---|---|
| Claude Code users | Plugin path: `myskills/{plugin}-skill` → `myskills/claude/{plugin}-skill` | Re-run `claude plugin add` |
| OpenCode users | skills.json paths change | Re-run `opencode/install.sh` |
| Codex users | New directory structure | Run `codex/install.sh` |
| Remote install users | `install-remote.sh` removed | Follow MIGRATION.md |

### Version Bump

All plugins get major version bump (next major above current):
- product-design: 4.17.1 → 5.0.0
- dev-forge: 5.9.1 → 6.0.0
- demo-forge: 1.3.2 → 2.0.0
- code-tuner: 1.1.2 → 2.0.0
- code-replicate: 4.0.0 → 5.0.0
- ui-forge: 0.1.2 → 1.0.0

## Platform Comparison Matrix

| Dimension | Claude Code | Codex | OpenCode |
|---|---|---|---|
| Entry point | SKILL.md (plugin auto-load) | AGENTS.md (manual/auto read) | skills.json → SKILL.md |
| Trigger | description matching | AGENTS.md routing rules | description matching |
| Interaction | AskUserQuestion (structured) | Minimal questions, assume + declare | Natural conversation |
| Orchestration | Phase logic embedded in skills | execution-playbook centralized | execution-playbook centralized |
| Tools | Read/Edit/Bash/Agent/Task | Codex native toolset | OpenCode native toolset |
| Sub-agents | Agent tool (explicit dispatch) | Platform-decided | subagent (explicit dispatch) |
| Variables | `${CLAUDE_PLUGIN_ROOT}` | Relative paths | Relative/absolute paths |
| MCP naming | `mcp__plugin_{name}_{server}__*` | N/A or platform-specific | `mcp__{server}__*` |
| Install | `claude plugin add <path>` | `codex/install.sh` | `opencode/install.sh` |

## Success Criteria

1. Claude Code: `claude plugin add myskills/claude/product-design-skill` works, all existing slash commands function identically
2. Codex: Running product-design workflow produces identical `.allforai/` output to Claude version
3. OpenCode: Same as Codex
4. No skill file in any platform references another platform's directory
5. Each platform's attention layering is independently optimized (verified by manual review)
6. shared/ contains only scripts/, mcp-ai-gateway/, schemas/ — nothing else
