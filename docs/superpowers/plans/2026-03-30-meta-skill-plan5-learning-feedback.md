# Meta-Skill Plan 5: Learning + Feedback

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add cross-project experience extraction (knowledge/learned/) and anonymous GitHub Issue feedback to the orchestrator template.

**Architecture:** After `/run` completes, the orchestrator extracts corrections and diagnosis patterns, writes them to the meta-skill's knowledge/learned/ directory. Optionally proposes anonymized GitHub Issues for universally useful findings.

**Tech Stack:** Markdown knowledge files, Bash (gh CLI for Issue creation)

**Spec:** `docs/superpowers/specs/2026-03-29-meta-skill-architecture-design.md` Sections 6 (Learning) + 6 (Feedback)

---

### Task 1: Create learning-protocol.md knowledge file

**Files:**
- Create: `claude/meta-skill/knowledge/learning-protocol.md`

- [ ] **Step 1: Write learning-protocol.md**

```markdown
# Cross-Project Learning Protocol

> After /run completes, the orchestrator extracts reusable experience and
> writes it to knowledge/learned/ in the meta-skill plugin directory.

## When to Trigger

After the orchestrator loop terminates (success or safety stop), if
state-machine.json has any entries in:
- `corrections_applied` (node-spec modifications during execution)
- `diagnosis_history` (full-chain diagnoses performed)

## Extraction Process

1. Read state-machine.json progress section
2. For each correction in corrections_applied:
   - Extract: which node, what was wrong, what was learned
   - Classify: mapping-gap / discovery-blind-spot / convergence / safety / other
3. For each diagnosis in diagnosis_history:
   - Extract: root_cause pattern, gaps_found domains
   - Classify same way
4. Group by tech stack pair (source → target) or by node type

## Output Format

Append to `${CLAUDE_PLUGIN_ROOT}/knowledge/learned/<category>.md`:

```markdown
## [{date}] {project_name or "anonymous"}

### {Classification}
- {What was wrong} → {What was learned}
- {Pattern} → {Fix applied}

### Source
- Correction/Diagnosis from: {node_id}
- Severity: {high/medium/low}
```

## File Naming Convention

- Tech stack specific: `<source>-<target>.md` (e.g., `react-swiftui.md`)
- Node specific: `<node-type>-patterns.md` (e.g., `discovery-patterns.md`)
- General: `general-patterns.md`

## Privacy Rules

- Do NOT include project name, company name, file paths, code snippets
- Do NOT include user identity information
- Only include abstract, tech-stack-level descriptions
- Example: "styled-components → ViewModifier mapping missing" (OK)
- Counter-example: "In /Users/john/acme-shop/src/Button.tsx..." (NOT OK)

## Consumption

Next `/bootstrap` reads `knowledge/learned/` in Step 2.3.
Learned experience takes precedence over preset mappings when they conflict
(learned comes from actual execution, presets are theoretical).
```

- [ ] **Step 2: Commit**

```bash
git add claude/meta-skill/knowledge/learning-protocol.md
git commit -m "feat(knowledge): learning-protocol.md — cross-project experience extraction"
```

---

### Task 2: Create feedback-protocol.md knowledge file

**Files:**
- Create: `claude/meta-skill/knowledge/feedback-protocol.md`

- [ ] **Step 1: Write feedback-protocol.md**

```markdown
# Anonymous Feedback Protocol

> After experience extraction, propose universally useful findings as
> anonymous GitHub Issues on the myskills repository.

## When to Trigger

After learning extraction (learning-protocol.md), if any extracted items
are classified as universally useful (not project-specific):

- Mapping gaps in preset mapping files → useful for all users of that stack pair
- Discovery blind spots → useful for all projects
- Convergence issues → useful for meta-skill improvement
- Safety gaps → critical for all users

Project-specific items (e.g., "this project's auth is unusual") stay local only.

## Privacy Rules (MANDATORY)

Before proposing any Issue, verify the content contains:
- ✅ Tech stack names (React, SwiftUI, Go, Gin)
- ✅ Abstract pattern descriptions ("CRUD completeness check", "handler directory coverage")
- ✅ Threshold/config suggestions ("coverage 50% → 80%")
- ❌ NO project names, company names, domain-specific terms
- ❌ NO file paths from the user's project
- ❌ NO code snippets from the user's project
- ❌ NO user identity (name, email, username)
- ❌ NO business logic descriptions

## User Confirmation Flow

```
Orchestrator presents:

"本次执行发现了 {N} 条可能对 meta-skill 有改进价值的经验：
{numbered list of deidentified findings}

是否愿意匿名提交到 myskills GitHub Issues？(y/n/选择部分提交)"
```

- User says yes → submit all
- User says no → skip, keep local only
- User selects specific items → submit only those

## Issue Creation

For each approved item:

```bash
gh issue create \
  --repo <myskills-repo> \
  --title "[Auto Feedback] {tech_stack_pair} — {one_line_description}" \
  --body "$(cat <<'EOF'
## [Auto Feedback] {tech_stack_pair} — {description}

**Source**: meta-skill automatic feedback (anonymous)
**Tech Stack**: {source} → {target}
**Category**: {mapping-gap | discovery-blind-spot | convergence | safety}

### Description
{deidentified improvement suggestion}

### Suggested Change
{which knowledge file to modify and what to add/change}
EOF
)" \
  --label "feedback/auto,{tech_stack_label}"
```

## Fallback

If `gh` CLI is not available or not authenticated:
- Log the Issue content to `.allforai/bootstrap/pending-feedback.md`
- Inform user: "gh CLI 不可用，反馈已保存到 pending-feedback.md，您可以稍后手动提交"
```

- [ ] **Step 2: Commit**

```bash
git add claude/meta-skill/knowledge/feedback-protocol.md
git commit -m "feat(knowledge): feedback-protocol.md — anonymous GitHub Issue feedback"
```

---

### Task 3: Add learning + feedback to orchestrator template

**Files:**
- Modify: `claude/meta-skill/knowledge/orchestrator-template.md`

- [ ] **Step 1: Append post-completion section to orchestrator-template.md**

After the "## Termination" section, append:

```markdown

## Post-Completion: Learning + Feedback

After the orchestrator loop terminates (success or safety stop):

### Step 1: Extract Experience

Read `${CLAUDE_PLUGIN_ROOT}/knowledge/learning-protocol.md` and follow its protocol:
- Read state-machine.json corrections_applied + diagnosis_history
- Extract reusable patterns
- Deidentify (remove project-specific details)
- Write to `${CLAUDE_PLUGIN_ROOT}/knowledge/learned/<category>.md`

### Step 2: Propose Feedback (Optional)

Read `${CLAUDE_PLUGIN_ROOT}/knowledge/feedback-protocol.md` and follow its protocol:
- Filter for universally useful findings
- Present to user for confirmation
- Submit approved items as anonymous GitHub Issues
- Save unapproved items locally only
```

- [ ] **Step 2: Commit**

```bash
git add claude/meta-skill/knowledge/orchestrator-template.md
git commit -m "feat(orchestrator): add post-completion learning + feedback protocol"
```

---

### Task 4: Update bootstrap Step 6.2 to copy new files

**Files:**
- Modify: `claude/meta-skill/skills/bootstrap.md`

- [ ] **Step 1: No additional scripts to copy**

learning-protocol.md and feedback-protocol.md are knowledge files read from the plugin directory at runtime via `${CLAUDE_PLUGIN_ROOT}`. They don't need to be copied to the target project.

However, the orchestrator-template.md reference to `${CLAUDE_PLUGIN_ROOT}/knowledge/learning-protocol.md` assumes the meta-skill plugin is still installed when `/run` executes. This is true — the plugin stays installed.

No changes needed. Just verify the reference chain:
- run.md (generated) references learning/feedback protocols
- Those protocols live in the plugin's knowledge/ directory
- Plugin is installed → paths resolve

- [ ] **Step 2: Verify and commit (no-op if nothing changed)**

```bash
# Verify the reference chain
grep -r "learning-protocol\|feedback-protocol" claude/meta-skill/knowledge/orchestrator-template.md
```

If the references are in the orchestrator-template.md (from Task 3), we're good.

No commit needed for this task.
