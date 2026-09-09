# Bootstrap audits Protocol

Run after the candidate workflow and node-specs exist, before offering `/run`.
Order: Coverage Self-Check → G0 → A0 → Phase A → three-lens DAG gate → node-spec audit.

### Scope boundary for every audit

Read `bootstrap-profile.json.task_goal`, `task_route` and `task_scope` first.
For `local-change`, audit only the referenced requirements and affected nodes;
use their confirmed goal/rules/acceptance as the coverage basis. Check real
implementation, documentation and verification responsibilities in Node-specs,
including document paths and observable tests, not just responsibility labels.
Do not run the whole-product feature inventory or add unrelated game/art/product
work because a concept or domain file exists. G0/A0/Phase A and reverse critique
have the same boundary. Reuse applicable confirmed decisions and ask only missing
or changed choices. Code observations never authorize product changes.

Before offering `/run`, execute the copied `validate_bootstrap.py`,
`check_decision_inputs.py <project_base>` and `validate_unattended_readiness.py`.
They share `product_intent.py` for scope and requirement validation. A pending,
stale, conflicting or malformed requirement blocks its requested work; file
existence or a code-derived "confirmed" label does not satisfy this gate.

### 3.5 Coverage Self-Check (Concept → Workflow Closure)

> Goal: Verify that all features in product-concept.json are covered by at least one
> workflow node. Auto-fix gaps using Closure Thinking and Reverse Backfill convergence
> rules. Runs silently — no user confirmation needed.

**Trigger**: for product-wide routes after product confirmation, `has_product_concept` is true (from Step 1.0). If false AND `is_game_project` is true, run **Game Design Coverage Check** (§3.5.0) instead. If both false, skip to Step 3.4 (Confirm with User).

#### 3.5.0 Game Design Coverage Check (game projects without product-concept.json)

When `is_game_project = true` AND `has_product_concept = false`, run this abbreviated coverage check instead of the full §3.5 flow. The game-design nodes are themselves the design artifacts (equivalent role to product-concept.json), so coverage is checked against the selected game scenario template.

**Checks to run:**

| System Concern | Trigger Condition | Check |
|---------------|------------------|-------|
| Save/Load | game has progression (levels, stats, unlocks) | Is there a node covering save/load system or persistence design? If not, note as gap — document in bootstrap output as "Save system gap: game has progression but no save/load design node." |
| Audio | game production, launch-prep, unattended run, or any music/SFX reference | Is the full `game-audio` chain covered: audio-registry, audio-style, SFX/BGM spec, source strategy/generation, loudness/loop QA, runtime-audio-import? If not, add those nodes. Only skip audio when `.allforai/scope-lock.json` approved before run removes audio/SFX/BGM from product scope. |
| Input/Control scheme | always applicable for game projects | Is input mapping covered in core-loop-design or a dedicated node? |
| Progression/Meta-loop | game has XP, levels, unlocks, or currency | Is `meta-game-design` or equivalent in selected nodes? |
| Tutorial / Onboarding | game has complex mechanics (action-rpg, strategy-sim, roguelike) | Is tutorial flow mentioned in any node's scope? |
| Platform-specific constraints | platform capability guard applied | Are suppressed monetization/retention nodes documented as "not applicable" in bootstrap output? |

If any gap is found: add a note to bootstrap output (not a blocker). Game projects in pure design mode proceed to game-design nodes regardless.

#### 3.5.1 Extract Feature Inventory

From `.allforai/product-concept/product-concept.json`, extract all declared features.
Source fields vary by schema — LLM uses semantic understanding, not hardcoded paths:

- `features[]` (structured feature list)
- `errc_highlights.must_have[]` + `errc_highlights.differentiators[]`
- `mvp_features[]` + `post_launch_features[]`
- Any other field that declares "the product will do X"

Output: a flat list of feature descriptions, each a natural-language statement.

#### 3.5.2 Closure-Driven Coverage Check

For each feature, two levels of verification:

**Level 1 — Direct Coverage:**
Does at least one node's `goal`, `exit_artifacts`, or node-spec body semantically
cover this feature? This is LLM semantic judgment, not string matching.

**Level 2 — Closure Completeness (6 types from cross-phase-protocols.md §B.3):**

| Closure Type | Check |
|-------------|-------|
| Config Closure | Feature needs configuration → is there a node for config management? |
| Monitoring Closure | Feature needs observability → is there a node for monitoring setup? |
| Exception Closure | Feature has failure modes → are recovery paths covered by a node? |
| Lifecycle Closure | Feature creates entities → is there cleanup/archival in some node? |
| Mapping Closure | Feature has A↔B pair → is B covered? (e.g., create↔delete, buy↔refund) |
| Navigation Closure | Feature is an entry point → is there an exit path in some node? |

**Game-specific closure types (added when `is_game_project = true`):**

| Closure Type | Check |
|-------------|-------|
| Save/Load Closure | Game has progression state → is there persistence/save-system implementation coverage? |
| Audio Closure | Game production requires SFX/BGM closure by default → are game-audio specification, generation/acquisition, loudness/loop QA, runtime import, event binding, and actual load/playback verification covered? Scope-lock is the only valid way to exclude audio. |
| Progression Closure | Game has XP/levels/unlocks → is meta-game-design or progression system covered? |
| Input Closure | Game requires player input → is controller/input scheme defined in core-loop or a dedicated node? |

Closure checks are **discovery-level** (as defined in §B.6): identify and mark what
should exist, not exhaustive implementation-level checks.

**Level 3 — Multi-Client Parity (when roles have multiple clients):**

If any role in product-concept.json has `clients[]` (multi-client declaration) with
`feature_parity` = `full`, `partial`, or `explicit`:

For each such role:
1. List all clients declared for this role
2. Determine check strategy based on parity mode:
   - `full`: every client must cover ALL MVP features for this role
   - `partial`: every client must cover all MVP features EXCEPT `parity_exceptions[]`
   - `explicit`: each client only needs to cover its own `supported_features[]`
3. For each feature × client pair that should be covered:
   - Check if that client has a corresponding implementation node
   - A feature that should be covered but has no node = gap

Auto-fix for multi-client gaps:
- If a feature has an implementation node for client A but not client B →
  create or extend a node for client B
- Each client needs its own compile-verify and E2E node (different tech stacks
  require different build/test tools)

**Backward compatibility**: if a role has only `client_type` (single client, legacy format),
skip Level 3 for that role — Level 1 and 2 are sufficient.

Example gap detection:
```
R1 消费者 (feature_parity: full, 3 clients):
  "商品搜索":
    buyer-ios:     implement-buyer-ios ✓
    buyer-android: implement-buyer-android ✓
    buyer-web:     ??? ← GAP: no implementation node for web client
    → auto-fix: create implement-buyer-web node
```

**Level 4 — Adaptive State Machine Coverage (when concept has adaptive_systems):**
> **Scope**: This check applies to WORKFLOW PLANNING — verifying that planned nodes
> cover all state machine implementation needs (storage, transitions, schedulers).
> It complements Step 3.1's check which verifies existing code. For new projects,
> Level 4 is the primary state machine check. For rebuild/translate, both run:
> Step 3.1 checks existing code gaps, Level 4 checks workflow node gaps.

If `product-concept.json` contains `adaptive_systems[]`, check each state machine for
three categories of gaps that Step 3.1's state machine check may have introduced:

1. **Dead state detection**: for each state dimension, verify at least one MVP-scope
   transition updates it. A dimension updated only by post_launch events (e.g.,
   `ai_tutor_session`) is a "dead state" in MVP — either remove it from MVP schema
   or add an alternative MVP-scope transition.

2. **Premature mapping detection**: for each behavior mapping, check if the behavior
   references a post_launch feature. If yes, the mapping cannot be implemented in MVP.
   Either defer the mapping or provide an MVP-scope fallback behavior.

3. **Background job detection**: for each transition or behavior that requires
   scheduled/periodic execution (keywords: "cron", "daily", "weekly", "window",
   "rolling", "periodic", "check every"), verify a scheduler/cron node exists in
   the workflow. Missing scheduler = the state will never be updated.

Auto-fix:
- Dead state → add alternative transition from MVP events, or mark dimension as post_launch
- Premature mapping → split into MVP behavior (simplified) + post_launch behavior (full)
- Missing scheduler → create a `scheduler-{name}` node

#### 3.5.3 Convergence-Controlled Auto-Fix

When uncovered features or broken closures are found, LLM decides:

- **Extend existing node** — if the gap is closely related to an existing node's domain
  (same business area, same tech module). Update that node's `goal`, `exit_artifacts`,
  and node-spec.
- **Create new node** — if the gap is a distinct concern not covered by any existing node.
  Append to `workflow.json` nodes[] and generate new node-spec at
  `.allforai/bootstrap/node-specs/<new-node-id>.md`.

**Convergence rules (from cross-phase-protocols.md §E Reverse Backfill):**

1. **Concept Sets the Boundary** — Only fix gaps derivable from `product-concept.json`.
   Features not in the concept are out of scope.
2. **Derivation Radius Decreases** — Bootstrap only fixes Ring 0 (directly missing
   features) and Ring 1 (first-order closure gaps, e.g., "login" exists → "password
   recovery" missing). Ring 2+ is deferred to execution-phase Reverse Backfill.
3. **Layer Cutoff** — Bootstrap = product design phase boundary. Ring 2+ belongs to
   development phase.

**Stop conditions (any one triggers stop):**

| Condition | Meaning |
|-----------|---------|
| Zero output | All features covered, all closures checked, no new gaps found |
| All downgraded | All remaining gaps are Ring 2+ (beyond bootstrap scope) |
| Scale reversal | A "gap" item's scope exceeds its parent feature → not a gap, it's a new feature |

#### 3.5.4 Write Coverage Matrix

Write `.allforai/bootstrap/coverage-matrix.json`:

```json
{
  "source": "product-concept.json",
  "checked_at": "<ISO timestamp>",
  "total_features": 25,
  "covered_before_check": 22,
  "auto_fixed": 3,
  "closure_derived": 2,
  "deferred_ring2_plus": 1,
  "final_coverage_rate": "100%",
  "matrix": [
    {
      "feature": "<feature description>",
      "covered_by": ["<node_id>"],
      "status": "covered"
    },
    {
      "feature": "<feature description>",
      "closure_type": "exception",
      "derived_from": "<parent feature>",
      "ring": 1,
      "status": "auto_added",
      "action": "extended node <node_id>"
    },
    {
      "feature": "<feature description>",
      "ring": 2,
      "status": "deferred",
      "reason": "ring2_cutoff | scale_reversal | all_downgraded"
    }
  ]
}
```


## G0 — Node-Granularity Audit (right-size for single-task attention)

Runs immediately after node generation, BEFORE A0. Granularity quality is U-shaped:
too coarse → attention dilution / context overflow; too fine → coordination cost +
coherence collapse. Target: each node = one coherent, independently-deliverable,
independently-testable responsibility that fits its attention budget. NOT minimal.

**Acts non-interactively** (split/merge), then batches confirmations into Phase A.

For up to 2 passes:
1. For each node, measure against its Attention Contract (Primary outcome / Context
   budget / Non-goals):
   - **Too coarse → split** when: multiple primary outcomes, exceeds context budget,
     or bundles independent concerns. Split into right-sized nodes; regenerate their
     specs, exit_artifacts, and `hard_blocked_by`/`alignment_refs` using the same
     node-generation machinery.
   - **Too fine → merge** when: no standalone deliverable, exists only to feed one
     sibling, or its exit artifact is a fragment. Merge into the coherent parent.
   - Otherwise → keep.
2. Write `.allforai/bootstrap/granularity-audit.json`:
   `{ "split": [{from,into[],rationale}], "merged": [{from[],into,rationale}], "kept": [ids] }`
   then re-run the pass on the restructured graph.
3. Stop after 2 passes (convergence cap); log any residual outliers.

Validate the output:
`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate_audit_outputs.py granularity .allforai/bootstrap/granularity-audit.json`

Queue non-trivial restructures for Phase A confirmation (do not ask now).

---

## A0 — Decision-Coverage Audit (catch every decision before the run)

Runs after G0 (over the right-sized graph), before Phase A. Dual-angle; union results.

- **Agent 1 (concept completeness):** enumerate every direction/intent fork implied by
  the source concept artifacts (art style, monetization model, tech selection, tone,
  scope tradeoffs, …).
- **Agent 2 (node reverse-inference):** scan nodes/node-specs for implicit choices NOT
  marked `decision_mode: "brainstorm"`.

Union the two; write `.allforai/bootstrap/decision-coverage.json`:
`{ "captured": [{id, node_id}], "missing": [{id, rationale, consumer_node}] }`.
**Every `missing` entry MUST name its `consumer_node`** (fix C4 — which node will read this
decision); a decision with no consumer is a planning error, not a decision.

Validate:
`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate_audit_outputs.py decision-coverage .allforai/bootstrap/decision-coverage.json`

Fold every `missing` entry into the Phase A decision queue (and set `decision_mode:
"brainstorm"` + the future `decision_inputs` path on its `consumer_node`).

---

## Phase A — Decision Gathering (interactive bootstrap only)

Resolve any remaining decisions after A0, as the final interactive step of `/bootstrap`. Iterate the decision
queue = (nodes with `decision_mode: "brainstorm"`) ∪ (A0 `missing`) ∪ (G0 restructure
confirmations).

Follow `${CLAUDE_PLUGIN_ROOT}/knowledge/brainstorming-lite.md`: group independent decisions
by topic, one message per topic, each decision with 2–3 options, tradeoffs and a recommended
default; serialize only dependent forks → incremental confirm →
write `.allforai/<domain>/decision-<id>.json` and validate it:
`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate_audit_outputs.py decision .allforai/<domain>/decision-<id>.json`

**Wire it (fix C4):** after writing each decision artifact, set the `consumer_node`'s
`decision_inputs` to include that artifact's path in `workflow.json`. (The final invariant
gate then verifies both directions: no missing, no orphan.)

**G0 overturn → re-audit (fix R1):** Phase A also presents G0's batched restructure
confirmations. If the user OVERTURNS a G0 split/merge, the node set changed, so **re-run A0**
on the corrected graph (decision coverage may have shifted) before finalizing the queue.

**Post-confirmation plan delta → re-confirm (all of it, not only G0):** Step 3.4 confirmed a
specific node list, and every audit from Coverage Self-Check onward may change it. Any change
to the node set or to any node's `hard_blocked_by` made after Step 3.4 — a G0 split/merge, a
node added by Coverage Self-Check or the reverse critic, a new dependency edge, a repair or
closure node added for the loop wiring — enters this Phase A queue and is presented before
the three-lens gate. Present it as the delta against what the user confirmed (added, removed,
re-wired, with the reason), and present it even when the queue is otherwise empty. The user
confirmed a plan, not a licence to grow one: an unconfirmed node set is a planning error, and
`/run` is not offered until the delta has been shown and accepted.

Generation-before: each decision is gathered BEFORE the node that consumes it (the node
references it via `decision_inputs`). When the queue is empty, every decision artifact is
on disk and wired — proceed to the final invariant gate. `/run` asks its Run Policy questions once before the first node and is fully autonomous after that.

---

## Final gate: three-lens DAG validation (节点生成验证)

Before declaring bootstrap complete and offering `/run`, validate the generated node graph
through three lenses. The point is to **shift structural failures LEFT** — catch them here, at
planning time, instead of mid-run as a C3 `deadlock`/`needs_diagnosis` (which would violate the
"autonomous run, zero surprises" promise). Hard errors BLOCK `/run`; warnings are surfaced.

**1. 闭环 — decision closure (deterministic, BLOCK).**
`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check_decision_inputs.py <project_base>`
Both directions (fix C4): every node's `decision_inputs` artifact exists AND every gathered
`decision-*.json` is referenced by ≥1 node (no orphan decisions). BLOCKED → return to Phase A.

**2. 大小循环 — DAG structure (deterministic, BLOCK).**
`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate_dag_structure.py <project_base>`
Detects dependency **cycles** in `hard_blocked_by` and dependencies on **non-existent nodes** —
both are guaranteed runtime deadlocks. BLOCKED → the cycle/missing-dep is a planning bug; fix
the generated graph and re-validate.

**3. 逆向 — reverse critic (LLM judgment, WARN).**
Dispatch one agent that works BACKWARDS from the goal over the node-specs (the node schema has
no `consumes` field, so this needs the specs' prose):
- *artifact closure*: for each node, do the inputs its node-spec reads have an upstream producer?
- *dead nodes*: any node whose outputs no downstream node consumes and that isn't a goal deliverable?
- *goal traceback*: does every goal feature have a producing node, and does every node trace back
  to serving the goal?
- *weakest link*: any single node an unusually large share of others depend on (SPOF)?
Write findings to `.allforai/bootstrap/dag-critique.json`
(`{closure_gaps, dead_nodes, goal_gaps, spofs}`). These are WARNINGS surfaced to the user (avoid
false-positive gating); a genuine `goal_gap` should route back to node generation.

`/run` is offered only when lenses **1 and 2** return OK and the node-spec audit below passes.

## Step 4 — Node-spec audit (每个节点的完成标准)

The three lenses prove the graph; this proves the nodes, reasoning from the
skill's Guiding Philosophy (reverse reasoning, closure loops, acceptance- and
quality-driven completion, attention management, context compression,
dimension elevation) rather than only its blocker list. Run
`${CLAUDE_PLUGIN_ROOT}/skills/meta-orchestration/40-qa/bootstrap-node-expansion-qa/SKILL.md`
over every node-spec. It rejects code-only or existence-only completion, missing
quality acceptance, missing attention contracts, unbounded context pulls, and QA nodes
whose findings have no repair-and-revalidation route or whose closure is not
hard-blocked by that repair. Writes `.allforai/bootstrap/bootstrap-node-expansion-qa-report.json`.
`FAILED_VALIDATION` → regenerate the named node-specs and rerun; do not offer `/run`.

---

