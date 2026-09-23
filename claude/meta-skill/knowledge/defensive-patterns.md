# Defensive Patterns Reference

> Universal defensive patterns for pipeline integrity. Node-specs reference this document in their Defensive Patterns section and add node-specific application details.

---

## Pattern A: JSON Load Validation with .bak Recovery

**Trigger condition**: Loading any `.json` artifact under the `.allforai/` directory.

**Protocol**:

1. Read file contents
2. Validate JSON legality with `python3 -m json.tool` or equivalent
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
| **small** | items <= 30 | Show the full list once; confirm by exception — only items you flagged get a question |
| **medium** | items 31-80 | Summary by module/role group; expand and confirm only flagged items |
| **large** | items > 80 | Script generates output file + statistical summary + only expand problematic items |

At every scale the human confirms exceptions, never each item: the list is shown so nothing is
hidden, the questions go only to what you flagged (a conflict, a guess, a gap). Item-by-item
confirmation was a check on weak generation; it is serial waiting now.

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

---

<a id="pattern-i"></a>

## Pattern I: Specification Gap Escalation

**Trigger condition**: An implementation or UI node needs a user-visible decision — a screen, a setting, an entry point, a copy promise, a permission request, a default value — that is covered by none of: the node's `source_inputs`, the node-spec's `## User-visible decisions` section, or the upstream design artifacts (for an app, the four `.allforai/app-design/...` artifacts; for a game, `.allforai/game-design/game-design-doc.json`).

**Protocol**:

1. **Do not implement the decision** and do not ship a placeholder surface for it. An input box, a stub screen or a "temporary" default is an undesigned product decision made by the implementer.
2. **Append one entry to the node artifact's `contract_gaps[]`**, with all five keys:

   ```json
   {
     "kind": "unspecified_user_visible_decision",
     "where": "<file or screen — what needed the decision>",
     "needed_decision": "<the question a design artifact must answer>",
     "blocking_intent_ids": ["<requirement id from the node's requirement_refs[].id>"],
     "suggested_owner_artifact": "<project-relative path present in some upstream node's exit_artifacts>"
   }
   ```

   `blocking_intent_ids` may be `[]` when no requirement covers the decision at all — say so in `needed_decision`. When no upstream node owns the decision yet, point `suggested_owner_artifact` at the closest upstream design artifact.
3. **Finish and evidence the covered remainder** of the node as usual. A gap on one decision does not excuse the rest of the work.
4. **Let the node fail.** A non-empty `contract_gaps` means the artifact does not pass `check_artifacts.py` and the node is not complete. That is the intended outcome; never empty the field, relabel the entry as `known_gaps`, or soften the `kind` to make the check go green.
5. **Route through the existing diagnosis path.** The node whose `exit_artifacts` contains the `suggested_owner_artifact` is the `suspected_root_node`; diagnosis resets it and its downstream, and this node re-runs once the design node has supplied the decision. Never ask the user inside `/run` — a product decision that genuinely needs the user becomes a preflight blocker for the next `/run` under the existing rules.

**Key principles**:

- Uncovered is not the same as free to invent. Silence in the contract is a gap, not a delegation.
- The cheapest implementation — adding one more input field — is usually the wrong answer, because it moves the burden of the missing decision onto the end user.
- One gap entry describes exactly one decision. Two missing decisions are two entries.
- Purely internal decisions — naming, file organisation, implementation details with no user-visible consequence — do not trigger this pattern. Decide those and move on.

**Example**:

A client node must talk to a backend service. The contract specifies `Authorization: Bearer <token>` and a locally startable server, but no artifact says how the end user obtains the service address or the credential. The node does not build a "Service settings" screen. It implements everything the contract does cover, and writes:

```json
{
  "kind": "unspecified_user_visible_decision",
  "where": "sync client bootstrap — first launch has no service address",
  "needed_decision": "How does the end user obtain the service address and credential: bundled default, operator-provisioned, or user-entered? If user-entered, which surface owns that form and what is its audience?",
  "blocking_intent_ids": ["REQ-031"],
  "suggested_owner_artifact": ".allforai/app-design/spec/permissions-notifications-settings-spec.json"
}
```

---

<a id="pattern-j"></a>

## Pattern J: Audience Isolation

**Trigger condition**: Designing, implementing or verifying any configuration item or setting, and any service endpoint a surface depends on.

**Protocol**:

1. **Exactly one audience per item**: `end-user`, `operator` (the party deploying and running the product), or `developer`. Not two, not none.
2. **Only `end-user` items may appear on an end-user surface.** Operator surfaces — admin console, operator console, CLI — are not end-user surfaces, and putting an operator item behind an "Advanced" disclosure does not change its audience.
3. **These are `operator` or `developer` by default**: service endpoints, access credentials, vendor keys, model selection, feature flags, environment names. They are supplied through `build-time`, `remote-config` or `deploy-env` provisioning, never through an end-user form.
4. **One exception**: a confirmed product requirement states that the end user is expected to connect their own server (self-hosted products). The item is then marked `end-user` and must carry a `requirement_ref` naming that confirmed requirement. Without the reference the exception does not exist.
5. **An item whose audience is not labelled is escalated under Pattern I**, never guessed.

**Key principles**:

- The test is "who has both the authority and the ability to supply this value", not "where is it cheapest to put the field".
- Copy that reads "provided by your deployment team" or "ask your administrator" on an end-user surface is a symptom of a misplaced audience, not a fix for one.
- `provisioning` is required for every non-`end-user` item and absent on `end-user` items; a value outside `build-time` / `remote-config` / `deploy-env` is a rejection, not a warning.

**Example**:

| Item | Audience | Provisioning / note |
|---|---|---|
| Sync service URL | `operator` | `deploy-env` — never rendered on an end-user surface |
| Daily reminder time | `end-user` | none — genuine end-user preference on the settings screen |
| Self-hosted server URL | `end-user` | exception, `requirement_ref: REQ-012` (confirmed self-hosting requirement) |

## Pattern K: Unhit Defense Deferral

**Trigger condition**: A design or implementation node is about to add a mechanism **for a scenario it imagines** — a rate limit or quota, a retry with backoff, a degradation or fallback path, a cache or batch sized for load, a compatibility branch with no caller, a recovery flow for a "just in case", an abstraction layer that only pays off at a hypothetical scale — and the failure it defends against has **no instance in this system**.

**Not in scope: correctness.** Handling a failure the contract you call says can happen — an error return, a timeout, a cancellation, a reconnect — is not defensive work, it is writing that call correctly. An `if err != nil` branch that has never fired in production is not a candidate here. The test is not "has this branch executed", it is "does the normal path still hold if this is absent". If removing it leaves undefined behaviour on a documented failure mode, this pattern does not apply.

**Protocol**:

1. **Classify the failure it prevents.** If it is abuse, cost, data loss or corruption, money, permissions, or a compliance obligation, this pattern does not apply — build it, and build it before it is hit. Those are not recoverable degradations and frequency does not discount them.
2. **Establish that "no instance" is a finding, not a blind spot.** Say where you looked — incidents, tickets, alerts, metrics, logs — and over what period. If the path has no observability at all, what you have is *not visible*, not *did not happen*; record it as unknown and stop. Absence of evidence counts only where evidence would have been recorded.
3. **Otherwise, do not build it.** A failure that has never occurred and whose consequence is a recoverable degradation does not get defended in advance. Low frequency and low risk together mean the defense costs more than the event.
4. **Record it as deferred**, with the trigger that would bring it back: the real occurrence, not a forecast. "When a call actually saturates the relay" is a trigger; "when we reach 10k users" is a forecast and does not count.
5. **Never size an unhit defense from proxies.** If the threshold cannot be read off an observed measurement or an external contract, deriving one from adjacent constants (participant caps, buffer sizes, capture targets, raw frame arithmetic) produces a number nobody can check. That number does not stay alone: it grows the tests that prove it does not clip normal use, the config keys that carry it, the documentation of where it came from, and later the fixes for how it interacts with the checks around it.
6. **When the defense already exists and does not work** — an always-true limit, a retry that never fires, a switch nothing reads, a default that disables the predicate — there are two repairs, not one. Ask steps 1-3 *before* asking how to make it fire. "Make the guard real" is the reflex answer and it is the expensive one: making an unhit defense real requires inventing the threshold step 5 forbids.

**Key principles**:

- A documented reason is not the same as a justified one. When the commit or comment that introduced the mechanism admits its own premise is unmeasured — "no real sender on this route yet", "a tight value is not derivable", "tighten once we measure" — that is evidence the work was speculative, not evidence it was warranted.
- The effort spent justifying a threshold is a signal about the threshold. Paragraphs of derivation for two constants means the number was not available to be read off anything.
- Deleting unhit defensive work is not a coverage trade-off, because there was no coverage: the branch has never executed on a real input.
- This pattern removes work; it never removes a guard on data, money, security, permissions, or compliance. If unsure which side a mechanism is on, it is on the protected side.
- **Knowing why it exists comes first.** If you cannot establish what a mechanism protects, you cannot establish that it is low-risk, and this pattern does not apply. It requires "investigated, and found to be speculative" — never "could not find a reason, so removed".

**Example**:

| Mechanism | Prevents | Instance found | Verdict |
|---|---|---|---|
| Rate limit on OTP send | Spam, SMS bill, account enumeration | none needed | Build — cost and abuse, step 1 exits |
| Idempotency key on payment callback | Double charge | none in 18 months | Build — money, step 1 exits |
| Per-call media throughput cap | Degraded call quality under a runaway sender | none; route has no client yet | Defer — record "a call actually saturates the relay" as the trigger |
| Auto-resume for a monthly export | Re-running a report | none; re-export is cheap | Defer — recoverable, re-run costs one click |
| `if err != nil` on a network write | Undefined behaviour on a documented failure | branch never fired | Build — correctness, out of scope (see Trigger condition) |
| Retry on a queue whose delivery path has no metrics | Lost job | cannot tell — nothing is recorded | Unknown, not deferred — step 2 stops here |
