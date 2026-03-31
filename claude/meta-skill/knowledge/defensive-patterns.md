# Defensive Patterns Reference

> Universal defensive patterns for pipeline integrity. Node-specs reference this document in their Defensive Patterns section and add node-specific application details.

---

## Pattern A: JSON Load Validation with .bak Recovery

**Trigger condition**: Loading any `.json` artifact under the `.allforai/` directory.

**Protocol**:

1. Read file contents
2. Validate JSON legality with `python -m json.tool` or equivalent
3. Parse failure ->
   - Check whether a `.bak` backup file exists in the same directory
   - `.bak` exists -> prompt user: "Warning: {filename} JSON parse failed. Backup found: {filename}.bak. Restore?"
   - No `.bak` -> prompt user: "Warning: {filename} JSON parse failed. Please re-run /{corresponding skill} to regenerate"
4. **Never silently skip; must inform the user**

**Example**:

```
Warning: task-inventory.json parse failed (syntax error at line 42)
  Backup found: task-inventory.json.bak (2h ago)
  Options: (a) Restore backup (b) Re-run /product-map
```

### .bak Auto-Backup (Write-Side)

**Trigger condition**: Writing any critical JSON artifact under `.allforai/`.

**Applicable files**: All `*-decisions.json`, `*-report.json`, `*-profile.json`, `*-plan.json`, and other critical artifacts.

**Protocol**:

1. **Before write**: if target file already exists, copy it to `{filename}.bak`
2. **After write**: retain `.bak` (until overwritten by next successful write)
3. **On load**: JSON parse failure -> try reading `.bak` -> success: restore and warn "Restored from backup" -> `.bak` also fails -> error and abort

**Relationship between Load Validation and .bak Auto-Backup**:
- Load validation (above) detects parse failures and checks whether `.bak` exists, prompting the user
- .bak auto-backup ensures `.bak` always exists (auto-backup before every successful write)
- Together they form a complete write-protection + load-recovery chain

**Example**:

```
Writing gap-tasks.json:
  1. Detected existing gap-tasks.json -> copied to gap-tasks.json.bak
  2. Wrote new content to gap-tasks.json
  3. Write succeeded -> retain .bak until next write

Loading gap-tasks.json:
  1. JSON.parse failed -> try gap-tasks.json.bak
  2. .bak parsed successfully -> restored to main file + warning "gap-tasks.json restored from backup, please check if last write was interrupted"
  3. .bak also failed -> error abort "gap-tasks.json and its backup are both unparseable, please re-run /feature-gap"
```

---

## Pattern B: Zero-Result Detection

**Trigger condition**: After every critical generation step completes, check output count.

**Protocol**:

1. After step completion, count output entries
2. count > 0 -> continue normally
3. count == 0 -> **distinguish two cases**:
   - **Genuinely zero** (check logic completed normally, no anomalies, data source sufficient) -> explicitly inform: "Check complete, {checked content} is genuinely zero / no issues"
   - **Possibly anomalous** (upstream data insufficient, load failure, search returned nothing) -> warn: "Output is zero, possibly due to {reason}, recommend {action}"

**Key principles**:

- Never output an empty list without explanation
- "Check passed" marker means "truly nothing"; warning marker means "possibly a problem"
- Show the user an explicit message, not a silent empty array

**Example**:

```
[pass] All checks passed, no feature gaps found (45 tasks checked)

[warn] Extracted 0 tasks. Upstream task-inventory.json contains only 2 roles,
       both in user_removed status. Suggest checking if product-map needs updating.
```

---

## Pattern C: Scale Adaptation (3-tier)

**Trigger condition**: When a skill begins execution, determine scale tier based on the number of objects to process.

**Universal thresholds** (each skill may fine-tune, but the pattern structure is consistent):

| Scale | Condition | Interaction Strategy |
|-------|-----------|---------------------|
| **small** | items <= 30 | Show each item, step-by-step confirmation |
| **medium** | items 31-80 | Summary mode, confirm by module/role groups |
| **large** | items > 80 | Script generates output file + statistical summary + only expand problematic items |

**Unit of measurement varies by skill**:

| Skill | Measured Object |
|-------|----------------|
| product-map | task count |
| experience-map | screen count |
| use-case | task count (determines use case volume) |
| feature-gap | task count |
| ui-design | screen count (thresholds <=15 / 16-40 / >40) |
| design-audit | task count |
| product-concept | N/A (concept layer has no scale tiers) |

**Display rules**:

- **small**: complete list + per-item confirmation
- **medium**: grouped summary + only expand items with flags/issues
- **large**: statistical overview + only expand high-priority / problematic items

---

## Pattern D: WebSearch Failure Handling

**Trigger condition**: Any step invoking WebSearch.

**Protocol**:

1. Attempt WebSearch
2. **Distinguish two failure modes**:

**Case 1: Tool works but no useful results**
- Retry once with adjusted keywords (change search language or search angle)
- Still no useful results -> inform user: "Limited public information on this topic. Searched {N} rounds, no high-quality results found"
- Continue flow, annotate `search_status: "no_useful_results"`

**Case 2: Tool itself errors / unavailable**
- Inform user: "Warning: WebSearch temporarily unavailable ({error message})"
- Provide options (AskUserQuestion):
  - (a) Skip search, continue flow (use AI's existing knowledge + user input)
  - (b) User manually provides reference materials / URLs
- Annotate `search_status: "tool_unavailable"`

**Key principles**:

- Never silently skip a search step
- Must inform the user of search status
- Distinguish "found nothing" from "tool is broken"

---

## Pattern E: Upstream Staleness Detection

**Trigger condition**: Loading an upstream artifact's JSON file.

**Protocol**:

1. Read upstream artifact's `generated_at` field
2. Read this skill's last run decision file (`*-decisions.json`) for the latest `decided_at` timestamp
3. **Comparison logic**:
   - Upstream `generated_at` **is later than** this skill's most recent `decided_at` -> warn: "Upstream {filename} was updated after this skill's last run ({upstream_time} > {this_skill_time}). Current results may be based on stale upstream data. Recommend re-running this skill"
   - Upstream `generated_at` **is earlier than or equal to** this skill's most recent `decided_at` -> normal, no warning
4. **Warning only, does not block flow**

**Example**:

```
Warning: Upstream data has been updated:
  task-inventory.json generated_at: 2026-02-27T14:00:00Z
  This skill's last run:            2026-02-25T10:00:00Z
  Recommendation: Re-run /use-case to get latest data
```

---

## Pattern F: Reference Integrity Assertions

**Trigger condition**: When step N references IDs from step M's output (e.g., task_id, screen_id, flow_id).

**Protocol**:

1. Collect all external IDs referenced in the current step
2. Check each ID exists in the corresponding upstream output
3. **Assertion failure** -> mark `BROKEN_REF`, record:
   - Reference source (current step + artifact item)
   - Referenced ID
   - Expected upstream output file
4. **Do not interrupt flow**, but record in the report
5. Show all `BROKEN_REF` entries to the user

**Example**:

```
Warning: Reference integrity check found 2 broken references
  - Step 3 journey J005 references task_id T999 -> not found in task-inventory
  - Step 2 use case UC042 references screen_ref S088 -> not found in experience-map
  Flow continues, but recommend fixing upstream data.
```

---

## Pattern G: User Interrupt Partial Save

**Trigger condition**: User interrupts mid-flow during a multi-step process (e.g., closes conversation, switches tasks).

**Protocol (principles)**:

- Every confirmed Step is immediately written to disk (existing design; each skill's decisions.json mechanism)
- Unconfirmed Step output exists only in conversation context, not persisted to disk
- Next run resumes from the last confirmed Step
- Content generated but not confirmed during interruption is not guaranteed to be retained

> This pattern defines principles only. Each skill's existing decisions.json incremental-reuse mechanism naturally supports this; no additional implementation is needed.

---

## Pattern H: Full-Auto Mode with Safety Guardrails

**Trigger condition**: When `pipeline_preferences.auto_mode` is set to `true` in the concept baseline.

**Protocol**:

Full-auto mode allows the pipeline to proceed without step-by-step user confirmation, but with safety guardrails:

1. **Automatic progression**: steps proceed without AskUserQuestion at each confirmation point
2. **Exception surfacing**: any UPSTREAM_DEFECT with severity=blocker still pauses and notifies the user
3. **Post-run summary**: at pipeline completion, present a comprehensive summary of all decisions made, flags raised, and items requiring user attention
4. **Opt-out at any point**: if the user sends any message during auto execution, pause and switch to interactive mode
5. **Audit trail**: all auto-decisions are logged with `auto_decided: true` marker in decision files for later review

**Safety guardrails that remain active in auto mode**:

| Guardrail | Behavior |
|-----------|----------|
| Blocker-severity defects | Always pause, always notify |
| Scale adaptation | Still applies (large projects get script output, not inline) |
| JSON .bak backup | Always active |
| Reference integrity | Checked and reported, never skipped |
| Zero-result detection | Warnings still generated and included in summary |
| Upstream staleness | Warnings still generated and included in summary |

**Key principle**: Auto mode skips confirmations, never skips validations.
