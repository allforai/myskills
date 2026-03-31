# Cross-Phase Integrity Protocols

> Five mechanisms that prevent information decay, ensure verification rigor, maintain upstream faithfulness, gate user confirmation, and handle downstream-discovered gaps. Each section is self-contained and can be referenced by a Theory Anchors section in any node-spec (e.g., "See cross-phase-protocols.md **Push-Pull**").

---

## A. Push-Pull Context Protocol

### Problem

In a multi-phase pipeline, each phase only reads its direct upstream artifact. Information decays geometrically:

```
concept -> map -> experience-map -> ui-design -> dev-forge
 100%      70%       50%              30%          10%
```

Key early-phase decisions (governance style, operation frequency, system boundary) nearly vanish after 4 layers. The LLM at the final layer can only do mechanical translation, losing business judgment.

### Principle

**Push + Pull: a concept-distilled baseline is pushed to all phases + each phase pulls specific raw fields on demand.**

Any phase's LLM context = concept-distilled baseline (push) + direct upstream artifact + on-demand cross-level raw fields (pull).

---

### A.1 Push: Concept-Distilled Baseline

#### What It Is

After the concept phase completes, a compact **concept-baseline.json** is automatically extracted from the full concept artifacts. It contains core decisions that all downstream phases need. Properties:

- **Auto-generated**: produced by the orchestrator after concept phase completes (after verify loop passes), no user intervention needed
- **Read-only**: downstream phases read but never modify; concept changes require going back to concept phase
- **Compact**: kept under 2KB so every phase can load it without budget pressure
- **Full push**: every downstream phase's pre-check automatically loads this file

#### Baseline Schema (fixed)

```json
{
  "_meta": {
    "generated_from": "product-concept phase",
    "generated_at": "ISO timestamp",
    "source_files": ["product-concept.json", "role-value-map.json", "product-mechanisms.json"]
  },
  "mission": "one-line product positioning",
  "target_market": "target market summary",
  "roles": [
    {
      "id": "R1",
      "name": "role name",
      "app": "website",
      "client_type": "mobile-ios",
      "screen_granularity": "single_task_focus",
      "high_frequency_tasks": ["task1", "task2", "task3"],
      "design_principle": "single-task focus, minimize page transitions"
    }
  ],
  "governance_styles": [
    {
      "flow_domain": "content publishing",
      "style": "auto_review",
      "system_boundary": {
        "in_scope": ["content editing and submission"],
        "external": ["identity authentication"]
      }
    }
  ],
  "errc_highlights": {
    "must_have": ["core feature list"],
    "differentiators": ["differentiating feature list"],
    "eliminate": ["explicitly excluded features"]
  },
  "pipeline_preferences": {
    "auto_mode": true,
    "ui_style": "..."
  }
}
```

#### Generation Timing and Location

- **When**: Phase 1 concept completes (after verify loop passes), orchestrator auto-executes
- **Where**: `.allforai/product-concept/concept-baseline.json`
- **How**: LLM extracts the above schema fields from `product-concept.json` + `role-value-map.json` + `product-mechanisms.json`
- **Update policy**: re-generated when concept is re-run; downstream phases never modify

#### Downstream Loading

Every skill's pre-check includes as its first step:

```
Concept-distilled baseline (auto-load):
  Read .allforai/product-concept/concept-baseline.json
  -> Use as background knowledge in LLM context, guiding all generation and acceptance decisions in this phase
  -> File not found -> WARNING, non-blocking (backward compatible with old artifacts)
```

---

### A.2 Pull: On-Demand Cross-Level Raw Data

#### When to Pull

The concept-distilled baseline is a compact summary covering general decisions. But some phases need **raw data details** for precise judgment -- that is when pulling is used.

Examples:
- experience-map needs `governance_styles[].downstream_implications` to decide whether a screen needs a review queue component -- the baseline only has `style: "auto_review"`, not detailed enough
- use-case needs `roles[].jobs[].pain_relievers` to generate sad path use cases -- the baseline only has `high_frequency_tasks`
- dev-forge needs `roles[].operation_profile.density` to decide caching strategy -- the baseline only has `screen_granularity`

#### Declaration Format

Each skill's pre-check, after the concept-distilled baseline, declares cross-level raw fields to pull:

```
Cross-level raw data pull (on-demand):
  product-concept.json:
    - roles[].jobs[].pain_relievers          -> source for generating sad path use cases
  product-mechanisms.json:
    - governance_styles[].downstream_implications -> decides whether to generate review queue components
    - governance_styles[].rationale              -> judges governance design rationality during acceptance
  role-value-map.json:
    - roles[].operation_profile.density          -> decides caching strategy and prefetch behavior
```

#### Pull Principles

- **Only pull details not covered by the baseline**: do not re-pull fields already in the baseline
- **Declare usage**: every pulled field must state how this phase uses it, preventing "pull everything"
- **Control granularity**: use JSONPath to target specific fields, do not load entire files

---

### A.3 Complete Context Model (Push + Pull Combined)

```
Any phase's LLM context:

+-------------------------------------------------+
|  Concept-distilled baseline (push)              |  <- auto-loaded, ~2KB
|  concept-baseline.json                          |
+-------------------------------------------------+
|  Direct upstream artifact                       |  <- normal input
|  e.g., experience-map reads task-inventory      |
+-------------------------------------------------+
|  Cross-level raw data (pull)                    |  <- on-demand declared, only needed fields
|  e.g., governance_styles[].downstream_implications |
+-------------------------------------------------+
        |
   LLM generation + acceptance (4D/6V/Closure)
```

**Token budget reference**:
- Concept-distilled baseline: ~500-800 tokens (fixed overhead, every phase has it)
- Cross-level pull: 0-2000 tokens (on-demand, most phases only pull 2-5 fields)
- Direct upstream: depends on artifact size (existing overhead)

### A.4 Frequently Pulled Fields Reference

Fields frequently used by multiple downstream phases. **Fields already in baseline marked [B]**, others are pull candidates:

| Field | Source | Baseline? | Downstream Users | Usage |
|-------|--------|:---------:|-------------------|-------|
| `mission` | product-concept.json | [B] | all phases | product positioning baseline, prevents feature drift |
| `roles[].app` | role-value-map.json | [B] | all phases | which sub-project code/screens belong to |
| `roles[].screen_granularity` | role-value-map.json | [B] | experience-map, ui-design | screen splitting strategy |
| `governance_styles[].style` | product-mechanisms.json | [B] | experience-map, use-case, dev-forge | presence of review screens/use cases/code |
| `governance_styles[].system_boundary` | product-mechanisms.json | [B] | experience-map, use-case, dev-forge | which features only write integration interfaces |
| `pipeline_preferences` | product-concept.json | [B] | all phases | auto mode, UI style |
| `errc_highlights` | product-concept.json | [B] | all phases | feature priority baseline |
| `governance_styles[].downstream_implications` | product-mechanisms.json | Pull | experience-map, dev-forge | determines specific component requirements |
| `governance_styles[].rationale` | product-mechanisms.json | Pull | use-case | acceptance of governance design rationality |
| `roles[].jobs[].pain_relievers` | product-concept.json | Pull | use-case | generating sad path use cases |
| `roles[].operation_profile.density` | role-value-map.json | Pull | ui-design, dev-forge | caching strategy, prefetch behavior |
| `roles[].operation_profile.high_frequency_tasks` | role-value-map.json | [B] | experience-map | prioritize high-frequency operation entry points |

### A.5 Downstream Contract (Node-Spec Integration)

In workflow v2.0, Push-Pull is operationalized via the **Downstream Contract** section
in each node-spec. Bootstrap generates this section from the `consumers` field in
workflow.json:

```
workflow.json:
  node "design-core-combat-loop":
    consumers: ["design-loot-economy", "implement-combat-system", "design-dungeon-generation"]

Generated node-spec "design-core-combat-loop.md":
  ## Downstream Contract
  → design-loot-economy reads: mechanics[].name (weapon list), meta_loop.currencies
  → implement-combat-system reads: mechanics[].parameters (concrete values needed)
  → design-dungeon-generation reads: core_loop.steps (room encounter structure)
```

This makes Push-Pull concrete: the producing node knows exactly which fields matter
and at what depth, because it knows who will consume them. The subagent can then:
- Ensure those fields are present and detailed enough
- Include concrete values (not placeholders) for fields that implementation nodes need
- Structure the artifact so consumer nodes can parse it reliably

### A.6 Relationship to Upstream Baseline Validation

Upstream baseline validation (see section C below) checks "does the downstream artifact faithfully reflect upstream intent?" The Push-Pull protocol provides the **data foundation** -- without loading upstream data, baseline validation cannot be performed. The three work together:

```
Push (always):  every phase auto-loads concept-distilled baseline -> used for global consistency checks during acceptance
Pull (on-demand): loads concept-level specific fields -> used for precise judgment during acceptance
Contract (at generation): each node knows who reads its output and what they need
Validation (at output): checks whether generated screens/code conform to baseline + pulled raw data
```

---

## B. 4D+6V+Closure Verification Framework

### Overview

Every generation phase's output quality is ensured by four mutually independent intellectual tools. They are not optional enhancements but acceptance standards for all phases.

---

### B.1 Four-Dimensional Information Card (4D)

Every key output object must withstand four layers of questioning:

| Dimension | Question | Purpose |
|-----------|----------|---------|
| **D1 Conclusion** | Is the conclusion itself correct, complete, and logical? | Verify "what is it" |
| **D2 Evidence** | What is the basis for this conclusion? Is it traceable? | Verify "based on what" |
| **D3 Constraint** | What preconditions and limitations exist? What was missed? | Verify "where are the boundaries" |
| **D4 Decision** | Why this choice and not another? What are the trade-offs? | Verify "why" |

---

### B.2 Six-Perspective Matrix (6V)

Every key output object must be examined from six independent perspectives to prevent single-perspective blind spots:

| Perspective | Focus |
|-------------|-------|
| **user** | Can the user accomplish their goal? How is the experience? |
| **business** | Does it support business objectives? Impact on revenue/conversion? |
| **tech** | Is it technically feasible? Are there uncontrollable dependencies? |
| **ux** | Is the interaction consistent? Is learning cost low? |
| **data** | Is it observable? Can data be collected to verify hypotheses? |
| **risk** | Security/compliance/privacy risks? Are high-risk operations protected? |

#### Product Design vs Development: Same 6V, Different Focus

```
Product Design Phase 6V                  Development Phase 6V
----------------------------             ----------------------------
user:     Can they complete the goal?    user:     Do they know what to do on error?
business: Supports business goals?       business: Won't errors cause financial loss?
tech:     Technically feasible?          tech:     Concurrency/timeout/degradation plans?
ux:       Interaction consistent?        ux:       Error messages friendly?
data:     Can we collect data?           data:     Are exceptions monitored/alerted?
risk:     Are there protections?         risk:     Is attack surface covered?
```

---

### B.3 Closure Thinking (6 Closure Types)

**Principle**: No feature exists in isolation in a product. Every feature exists within cycles. During acceptance, ask for each output: is this cycle complete?

| Closure Type | Questioning Pattern | Product Design (Discovery-level) | Development (Implementation-level) |
|-------------|---------------------|----------------------------------|-------------------------------------|
| **Config Closure** | What does this run on? Who configures it? | Mark "needs configuration" | Config table + defaults + hot-reload mechanism |
| **Monitoring Closure** | How well is it running? Who watches the results? | Mark "needs observability" | Instrumentation events + alert rules + dashboard |
| **Exception Closure** | What happens on failure? Who handles it? Recovery path? | List major exception scenarios | Exhaustive exceptions + retry strategy + degradation plan + user prompts |
| **Lifecycle Closure** | Created things go where? Expiry/cleanup/archival? | Mark "if created, must have cleanup" | TTL + scheduled tasks + archival policy + cascade deletion |
| **Mapping Closure** | A and B are paired; if A exists, B must exist (pain<->reliever, happy<->sad path, action<->feedback) | Mark A<->B relationships | Foreign keys/indexes + consistency checks + orphan cleanup |
| **Navigation Closure** | Can you get in and out? Any dead ends? | Mark reachability | Route guards + 404 handling + fallback strategy + deep linking |

---

### B.4 Verification Loop

**Principle**: One-pass generation is never perfect. Acceptance is not a one-time check but iterative correction until clean.

**Unified loop pattern**:

```
Script collects context + review issues -> stdout JSON
    |
Claude Code reviews using 4D + 6V + Closure thinking
    |
Issues found -> modify source files -> re-run script -> re-review
    |
No issues -> pass, proceed to next phase
```

**Execution entry**: `python3 verify_review.py <BASE> --phase <phase> [--xv]`

**XV Enhancement** (optional): The `--xv` flag triggers cross-model cross-validation, sending output summaries to a second AI model (via OpenRouter API) for independent opinions. XV enhances the Loop; it is not an independent phase.

**Loop round limits**: max 2-3 rounds of generate -> review -> fix -> re-review. If issues persist after 3 rounds, mark as UNRESOLVED and proceed.

---

### B.5 Relationships Between the Four Tools

```
Loop (cycle) is the execution framework -- drives the "generate -> review -> fix" iteration
  +-- 4D (four dimensions) is review depth -- four layers of questioning per object
  +-- 6V (six perspectives) is review breadth -- six angles on the same object
  +-- Closure is review completeness -- checks whether cycles are broken
      +-- XV (cross-validation) is review independence -- cross-check with another model
```

Product design's Loop focuses on "was it discovered?"; development's Loop focuses on "was it implemented?" Same tools, different acceptance standards.

All four are indispensable: without Loop, review is one-shot; without 4D, review stays superficial; without 6V, review has blind spots; without Closure, review cannot find broken cycles.

---

### B.6 Phase Transition Mindset

Product design and development phases have fundamentally different closure concerns:

```
Product Design Phase (from nothing)        Development Phase (fill gaps)
----------------------------------         ----------------------------------
Focus on positive space: what should exist? Focus on negative space: what can go wrong?
Closure granularity: identify + mark        Closure granularity: 100% implementation
Exception handling: list major scenarios    Exception handling: exhaust all paths
State coverage: annotate four states        State coverage: every state has code
```

**Product design closure is "discovery-level"**: identify that a closure should exist (pain<->reliever, happy<->sad path, action<->feedback), mark what is needed. Product design cannot and should not exhaust all exceptions -- its responsibility is to think through normal flows and key exception scenarios.

**Development closure is "implementation-level"**: 100% complete all closures. Product design only marked 3 exceptions; development must derive 15 from those 3 (network timeout, concurrency conflicts, permission changes, data inconsistency, external service degradation...).

**dev-forge's responsibility shift**: design-to-spec should not just "translate" product design's exception list; it should **proactively derive the negative space** -- using product design's normal flows as input, systematically derive all possible exception paths, boundary conditions, race conditions, and degradation strategies.

---

## C. Upstream Baseline Validation

### Principle

Upstream artifacts are not "generate and discard" intermediate files. They are the downstream acceptance **baseline**. Each phase's output simultaneously serves two roles:

```
Phase N's output = Phase N+1's input + Phase N+1's acceptance baseline
```

### Validation Method

After downstream generates its artifact, the LLM simultaneously loads the upstream artifact and the downstream artifact, using **LLM judgment (not mechanical rule matching)** to review whether the downstream faithfully reflects upstream intent. This is the same kind of LLM-driven semantic judgment as other acceptance dimensions in the Loop (4D/6V/Closure).

### Upstream-to-Downstream Verification Chain

| Upstream Artifact | Downstream Artifact | LLM Review Perspective |
|-------------------|---------------------|------------------------|
| product-concept -> roles/mission | product-map -> role-profiles/tasks | Is the role intent from concept faithfully reflected in the map? Do tasks respond to the mission? |
| product-map -> business-flows | journey-emotion -> journey_lines | Is each business flow's semantics reflected in the journey line's emotion arc? Do exception branches have corresponding emotions? |
| journey-emotion -> emotion_nodes | experience-map -> screens | Are emotion intents (design_hint) implemented in screen designs? Do high-risk nodes have protective designs? |
| product-map -> task-inventory | experience-map -> screens.tasks | Do task intents have corresponding interaction entry points in screens? |
| experience-map -> screens | ui-design -> HTML previews | Is screen structure intent preserved in visual design? |
| experience-map -> operation_lines | interaction-gate -> lines | Is the operation line's experience design intent considered in usability scoring? |
| task-inventory -> tasks | use-case -> use_cases | Is each task's business semantics completely covered in use cases? |
| task-inventory -> tasks | feature-gap -> gaps | Is gap analysis based on complete understanding of the task inventory? |

### Implementation

Each skill's verification Loop loads upstream artifacts as review context. Baseline comparison is naturally integrated into existing 4D/6V/Closure review. Baseline validation failure = LLM corrects and re-validates (same as other Loop failures).

### Core Principle

Upstream artifacts are not "generate and discard" intermediate files; they are the downstream's **living baseline**. Higher upstream quality (more specific fields, clearer intent) means more precise downstream acceptance. Conversely, if upstream output is vague (e.g., all emotions are neutral), baseline validation loses its basis for judgment.

### Relationship to Closure Thinking

Upstream baseline validation is the **cross-phase extension of mapping closure**. Mapping closure checks A<->B correspondence within the same phase; baseline validation checks upstream-A -> downstream-B correspondence across phases.

---

## D. User Confirmation Gate Protocol

### Principle

**All user interaction must complete before execution begins.** The execution phase is pure subagent execution, zero interaction.

### Two-Phase Model

```
Discussion Phase: main flow converses with user -> all decisions written to disk (.allforai/)
Execution Phase:  pure subagent dispatch -> read disk files -> execute -> produce artifacts
```

### Discussion Phase Responsibilities

Before dispatching any subagent, the main flow must:

1. Read all rules files for phases marked `preflight: true`
2. Extract from rules the list of questions requiring user decisions
3. Discuss each with the user until all questions are resolved
4. Write all decisions to corresponding phase output files (e.g., replicate-config.json, project-manifest.json)
5. After user confirms "start execution," enter the execution phase

### Execution Phase: No Interaction Allowed

Execution-phase subagents are **forbidden** from using AskUserQuestion or any user interaction tools. If a subagent discovers missing decision information:
- Information exists in upstream artifact files -> read it
- Information is genuinely missing -> return UPSTREAM_DEFECT (target: the relevant preflight phase); main flow pauses execution, returns to discussion mode to supplement decisions, then resumes execution

### Scale Adaptation for Confirmation

Confirmation interaction adapts to the scale of the project:

| Scale | Condition | Confirmation Strategy |
|-------|-----------|----------------------|
| **small** | items <= 30 | Show each item, confirm step-by-step |
| **medium** | items 31-80 | Summary mode, confirm by module/role groups |
| **large** | items > 80 | Script generates output file + statistical summary + only expand problematic items |

### Closed-Loop Input Audit at Confirmation Points

When collecting user input via AskUserQuestion, not only record what the user said, but check what the user **did not say but should have**:

| Closure Type | Question | Example |
|-------------|----------|---------|
| **Config Closure** | What does the user-described feature run on? Who configures it? | User says "AI auto-reply" -> Who configures which AI model? Who handles model failure? |
| **Exception Closure** | The normal path the user described -- what if it fails? | User says "paid upgrade" -> What if payment fails? Refund flow? Renewal failure? |
| **Lifecycle Closure** | The thing the user described being created -- where does it end up? | User says "post discussions" -> How do completed discussions wrap up? How are expired posts handled? |
| **Role Closure** | User described the consumption side; what about the production side? | User says "users post + AI replies" -> Who manages AI roles? Who reviews content? |

**Execution rules**:
- **No open-ended questions**: when gaps are found, generate multiple-choice questions
- **No flow interruption**: input audit runs after user confirms current step; gaps are addressed in the next round of questions, not by rolling back
- **Gap severity**: MUST (cannot run without it) -> ask immediately; SHOULD (incomplete experience) -> record, ask in later steps; NICE (nice-to-have) -> record, do not ask
- **No over-questioning**: max 1-2 closure supplement questions per user answer, avoiding interrogation fatigue

**Convergence control**:
- **Depth limit**: max 2 layers of closure follow-up (user answer -> follow-up 1 -> user answer -> follow-up 2 -> stop). Layer 3 gaps are recorded in the decision log without further asking
- **SHOULD/NICE deferral**: only MUST-level gaps are asked immediately. SHOULD and NICE are recorded and auto-derived by LLM in later phases (product-map/design-to-spec)
- **Convergence criterion**: if user's consecutive 2 answers produce no new MUST-level gaps -> input audit complete, proceed
- **Total limit**: max 3 closure follow-up questions per Step. Excess MUST gaps are merged into the next Step

---

## E. Reverse Backfill Protocol

### Problem

The pipeline is unidirectional: concept -> map -> experience-map -> ... -> code. When downstream discovers something upstream missed (e.g., "forgot password"), not backfilling upstream creates "design orphans" -- code exists but has no screen design, no use case, no UI spec.

### Principle

**Downstream exists to fill upstream gaps, not to open new fronts.**

- Upstream-missed supporting features (e.g., credential recovery, operation undo) -> **must backfill upstream**, making the design system complete
- Entirely new domains never discussed upstream (e.g., "should we add social features?") -> **do not backfill**, mark as `unexplored_area`, leave for the next product design iteration
- Distinguishing criterion: **if derivable from an existing core feature's closure = upstream missed it = backfill; if not derivable = new domain = do not backfill**

### Backfill Mechanism

When design-to-spec phase 1.5 discovers Category B gaps, **write back directly to upstream artifacts**:

```
Category B discovery (e.g., "password recovery" -- derived from "login"'s capability-level closure)
  |
Backfill upstream (filling gaps, not opening new fronts):
  1. task-inventory.json      <- append task entry (marked _backfill: true)
  2. experience-map.json      <- append screen entry (marked _backfill: true)
  3. use-case-tree.json       <- append use case entry (marked _backfill: true)
  |
Forward generation (based on already-backfilled upstream):
  4. requirements + design + tasks (normal flow)
  |
Record:
  5. negative-space-supplement.json (audit trail: what was discovered, why judged as gap vs new domain)
```

### Backfill Entry Marker

All backfilled entries are appended to original files using the `_backfill` marker:

```json
{
  "id": "T099",
  "name": "credential recovery",
  "_backfill": {
    "source": "design-to-spec 1.5",
    "ns_ref": "NS-001",
    "derived_from": "T005-authentication (capability-level closure: credential loss recovery)",
    "derivation_ring": 1,
    "backfilled_at": "ISO timestamp"
  },
  "...": "remaining fields follow normal entry schema"
}
```

### Backfill vs New Domain Determination

| Determination | Condition | Behavior |
|---------------|-----------|----------|
| **Backfill** | Derivable from existing task/entity closures | Write back to upstream + forward generate spec |
| **New Domain** | Not derivable, belongs to entirely new business direction | Do not write back, record in `_uncertainty.unexplored_areas` |

Examples:
- "Password recovery" <- derived from "authentication"'s credential-loss closure -> **backfill**
- "Operation undo" <- derived from "submission"'s exception-recovery closure -> **backfill**
- "Social sharing" <- no task can derive this -> **new domain, do not backfill**

### Convergence Rules

Backfilling must converge; it cannot expand indefinitely. Three convergence safeguards:

**1. Concept Sets the Boundary (finite input)**

The concept phase defines a finite set of roles, tasks, and entities. All derivations operate on this finite set. What concept did not mention = nonexistent input = do not derive.

**2. Derivation Radius Decreases (geometric decay)**

```
Core tasks (Ring 0)        -> N tasks
First-order (Ring 1)       -> ~0.3N (direct closure gaps, e.g., authentication -> credential recovery)
Second-order (Ring 2)      -> ~0.1N (backfill item's closure gaps, e.g., credential recovery -> alternative verification when notification unreachable)
Third-order (Ring 3)       -> ~0.03N (approaches zero)
```

Each backfill item is naturally **simpler and narrower** than its parent task. Simpler means fewer closures to check; output naturally decreases -- geometric series naturally converges.

**3. Layer Cutoff (phase relay)**

```
Product Design Phase:  only Ring 0 + Ring 1 (discovery-level)
Development Phase:     continues with Ring 2+ (implementation-level)
```

Each phase has a clear cutoff ring; deeper derivations are not pursued.

**Convergence criteria** (stop derivation when any is met):

| Criterion | Condition | Meaning |
|-----------|-----------|---------|
| Zero output | All dimensions x all tasks = 0 new discoveries | Derivation exhausted |
| All downgraded | All new discoveries are second-order or higher | Beyond current phase's responsibility |
| Scale reversal | A "backfill" item's scope > its parent task | Not a gap; it is a new feature |

**In one sentence**: Backfilling converges toward the center, not expands outward. Concept is the circle's boundary, derivation radius decreases each layer, and phase relay ensures cutoff.

### Post-Backfill Verification

After backfill entries are written to upstream files, subsequent FVL phase 2 normally audits these entries -- they receive the exact same verification standard as original entries. During design-audit final review, `_backfill` entries are separately listed in coverage statistics.
