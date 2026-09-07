# Innovation Protocols

> Extracted from product-design-skill: product-concept.md, skill-commons.md

---

## A. Adversarial Multi-Model Generation

A four-role protocol for generating breakthrough innovation concepts. The value is in the
roles and their independence, not in which vendor plays them: each role runs in its own
context, sees only its inputs, and never reads another role's draft. Roles may run on external
models through the ai-gateway `ask_model` routing or on fresh-context sub-agents of the session
model; which model actually ran is recorded in the output's `source_model`, never prescribed
here (model names and temperatures age faster than any protocol).

### Roles

| Role | Mission | Independence requirement |
|------|---------|--------------------------|
| **Disruptor** | Propose the most radical alternatives for each core mechanism. Break all industry conventions. Output: 3 "crazy" concepts | Sees the problem statement only; never the Guardian's boundaries |
| **Guardian** | Find violations of physics/law/human-nature baselines. Draw non-negotiable boundaries. Output: boundary-constraints.json | Sees the problem statement only; never the Disruptor's concepts |
| **Archaeologist** | Search other domains for analogous problem solutions. Fixed 3 cross-domain cases. Output: cross-domain-cases.json | Sees the problem statement only |
| **Pre-Synthesizer** | Initial integration of Disruptor/Guardian/Archaeologist outputs. Output: pre-synthesis.json | A context that produced none of the three inputs |

If only one model is reachable, the roles still run as separate fresh contexts; the protocol
degrades in diversity, never in independence, and the report says so.

### The session model as Alchemist

After receiving all 4 model outputs, Claude:
1. Reads all 4 outputs
2. Re-interprets radical proposals within Guardian's boundaries
3. **Must preserve the Disruptor's core insights** (no compromising into mediocrity)
4. Outputs 3 "unfamiliar but feasible" concepts
5. Writes: `adversarial-concepts.json`

### Archaeologist Examples

The Archaeologist searches for cross-domain analogues based on the problem essence:
- Problem essence = "trust building" -> Gaming industry (guild systems)
- Problem essence = "trust building" -> Finance industry (escrow mechanisms)
- Problem essence = "trust building" -> Biology (symbiotic relationships)

### User Confirmation After Generation

- "Which of these 3 innovation proposals best matches your vision?" (single/multi-select)
- "Protection level for each proposal?" (AI suggests + user confirms):
  - **core** -- differentiating core feature, must retain
  - **defensible** -- has defensive value, negotiable
  - **experimental** -- experimental feature, can defer

### Full JSON Schema: adversarial-concepts.json

```json
{
  "generated_at": "ISO timestamp",
  "multi_model_collaboration": {
    "models_used": [
      { "role": "disruptor", "source_model": "<recorded at run time from the gateway response>", "context": "independent" },
      { "role": "guardian", "source_model": "<recorded at run time>", "context": "independent" },
      { "role": "archaeologist", "source_model": "<recorded at run time>", "context": "independent" },
      { "role": "pre_synthesizer", "source_model": "<recorded at run time>", "context": "independent" }
    ],
    "integration_method": "main_model_synthesis",
    "disagreements": [
      {
        "topic": "Disagreement description",
        "model_a_view": "Model A perspective",
        "model_b_view": "Model B perspective",
        "integration_decision": "Main model's ruling",
        "rationale": "Ruling rationale"
      }
    ]
  },
  "concepts": [
    {
      "id": "IC001",
      "name": "Innovation concept name",
      "description": "Detailed description",
      "source_mechanism": "MEC1",
      "disruptor_input": "Disruptor's original proposal",
      "boundary_constraints": ["Boundary constraint list"],
      "cross_domain_references": ["Cross-domain case IDs"],
      "protection_level": "core | defensible | experimental",
      "feasibility_score": 3,
      "innovation_score": 9,
      "competitor_reference": "none | cross-domain | evolved",
      "state_machine": {
        "description": "Core state flow of the innovation mechanism (generic, not industry-bound)",
        "key_entities": [
          {
            "name": "Core entity name",
            "lifecycle_description": "Entity lifecycle description",
            "critical_states": ["initial_state", "intermediate_state", "terminal_state"],
            "initial_state": "initial_state",
            "terminal_states": ["terminal_state"],
            "critical_transitions": [
              {
                "from": "State A",
                "to": "State B",
                "trigger": "Trigger condition",
                "business_meaning": "Business meaning"
              }
            ]
          }
        ],
        "integrity_requirements": {
          "must_have_initial_state": true,
          "must_have_terminal_state": true,
          "must_have_error_recovery": true,
          "max_unreachable_states": 0,
          "must_have_timeout_transition": true,
          "must_have_compensation_path": true
        }
      }
    }
  ]
}
```

### State Machine Requirements by Protection Level

- `core` -- **must** define complete state machine
- `defensible` -- **should** define state machine
- `experimental` -- optional

### Single-Model Fallback Protocol

When OpenRouter is unavailable:
- Skip multi-model adversarial generation
- Claude alone performs assumption zeroing and innovation exploration
- Output `multi-model XV unavailable` message
- Script-based XV may still be available if OPENROUTER_API_KEY is set

---

## B. Assumption Zeroing Protocol

Before searching competitors, break the constraints of "industry consensus". Uses two models in parallel:

### Phase C Execution

```
Role A (Challenger, independent context)
  -> List 5-10 "industry consensus" statements for the domain
  -> Example: "Collaboration tools must have folders", "Social products must have friend systems"
  -> Output: industry_assumptions[]

Role B (Guardian, independent context)
  -> Challenge each: Is this a law of physics or a human convention?
  -> Physics law -> must obey (e.g., network latency, information entropy)
  -> Human convention -> can challenge (e.g., folders, friend lists)
  -> Output: constraint_classification[]

Session model: Integrator
  -> Weigh both opinions, adjudicate disagreements
  -> Output: assumption-zeroing.json
```

### User Interaction After Zeroing

- "Which of these industry conventions do you want to challenge?" (multi-select, from items classified as "human convention")
- "If you remove these constraints, what new product forms are possible?" (generate 2-4 innovation directions based on challenge selections)

### Innovation Opportunity Exploration (Phase B+)

Based on the assumption-zeroing list, two independent contexts search for unconstrained solutions (different models when the gateway offers them, otherwise two fresh contexts of the session model; the report records which):

```
Role A (Explorer, independent context)
  -> "If constraint X didn't exist, how would the problem be solved?"
  -> 3-4 rounds of deep search per direction
  -> Output: innovation_opportunities_A[]

Role B (Explorer, a second independent context)
  -> Same task, independent search
  -> Output: innovation_opportunities_B[]

Session model: Integrator
  -> Merge, deduplicate, mark disagreement points
  -> Output: innovation-opportunities.json
```

---

## C. Search Protocol

### Per-Step Search Strategy

| Step | What to Search | Keyword Strategy | Min Search Rounds |
|------|---------------|-----------------|-------------------|
| Step 0 Phase A | Problem essence: academic research, industry reports, root cause analysis | `"{problem domain}" industry pain points / "{problem domain}" market size / "{problem domain}" user research` | 2 |
| Step 0 Phase B | Competitor landscape: direct/indirect competitors, failed products | `"{problem domain}" competitor analysis / "{problem domain}" alternatives / "{competitor}" vs / "{problem domain}" startup failed why` | 3 |
| Step 1 | User personas: real user composition, forum complaints, community discussions | `"{product type}" user personas / "{competitor}" user reviews / "{problem domain}" Reddit OR forum / "{competitor}" complaints` | 2 |
| Step 2 | Business models: pricing strategies, success metrics, funding info | `"{product type}" pricing model / "{competitor}" business model / "{industry}" SaaS metrics / "{competitor}" revenue` | 2 |
| Step 3 | Positioning validation: blue/red ocean analysis, differentiation cases, trends | `"{product type}" market positioning / "{industry}" trends 2025 2026 / "{product type}" blue ocean` | 1 |

### Multi-Language Search

Search Chinese once + English once per round. Chinese finds local competitors and user feedback; English finds global perspectives and methodologies.

### Source Quality Hierarchy

| Priority | Source Type | Usage |
|----------|-----------|-------|
| **P1** (cite first) | Official docs, industry reports (Gartner/McKinsey/CB Insights), academic papers, authoritative media | Primary citations |
| **P2** (cross-validate) | Blogs, Medium articles, personal analyses | Cross-validate before citing |
| **P3** (pain evidence) | Reddit, Zhihu, Product Hunt, forums, App Store reviews | Evidence for pain points |
| **P4** (reference only) | Unsigned articles, obvious SEO content, outdated info | Reference only, do not cite |

### Reverse Evidence Searching

Actively search for counter-evidence to avoid confirmation bias:
- "Why did XX fail?"
- "Drawbacks of XX"
- "XX user churn reasons"

### Search Result to Selection Question Conversion

1. Extract common patterns from 5-10 search results -> distill into 2-4 options
2. Each option with brief rationale ("According to XX report..." / "XX competitor's approach is...")
3. If results are highly consistent (industry consensus), mark "industry mainstream approach"
4. If results diverge significantly, mark each option with its supporting evidence

### "Other" Response Handling

When user selects "Other" and provides custom input:
1. **Do not directly adopt** -- user input may be vague or incomplete
2. **WebSearch based on user's new input** -- use keywords as search leads
3. **Generate new selection questions** -- based on new search results, distill 2-4 more precise options
4. **Incorporate user's original input into options** -- ensure user intent is covered
5. Repeat until user confirms from preset options

### Search Failure Handling

- Direction yields no valuable results -> change keywords, search again
- Still no results -> honestly tell user "limited public information in this direction", do not fabricate
- WebSearch tool unavailable -> inform user, mark as `tool_unavailable`, skip that part

---

## D. XV Cross-Validation Protocol

How to use multiple models for independent review at validation points throughout the pipeline.

### Per-Phase Validation Points

Each validation point runs in a context that did not produce the artifact under review; the
gateway's `task_type` routing picks the model, and `source_model` records which one ran.

| Phase | Validation Point | task_type | Content Sent | Target Field |
|-------|-----------------|-----------|-------------|-------------|
| product-concept Step 4 | Assumption challenge | `competitive_analysis` | Concept summary: core problem + value proposition + key assumptions + ERRC matrix | `cross_model_review.assumption_challenges` |
| product-concept Step 4 | Persona blindspot | `user_persona_validation` | Role list + VPC (Jobs/Pains/Gains) + target user personas | `cross_model_review.persona_blindspots` |
| product-map Step 5 | Task completeness | `task_completeness_review` | Role list + high-frequency task list + discovered conflicts | `cross_model_review.missing_tasks` |
| product-map Step 5 | Hidden conflicts | `conflict_detection` | Role list + high-freq tasks + task dependencies + business rules | `cross_model_review.hidden_conflicts` |
| journey-emotion | Intensity distribution | (optional) | second model | Emotion annotation summary | Independent review of intensity distribution |
| experience-map | Architecture review | (optional) | second model | Summary (operation line count, screen count, task coverage, platform distribution) | Information architecture reasonableness |

### What XV Auto-Writes

- Assumption challenges (which assumptions may not hold)
- Blindspot hints (overlooked competitors or alternatives)
- Alternative positioning suggestions
- Missing task hints
- Hidden conflicts (cross-role rule contradictions, state flow deadlock risks)

### Output Schema for cross_model_review

```json
{
  "cross_model_review": {
    "assumption_challenges": [
      {
        "assumption": "The challenged assumption",
        "challenge": "Why it may not hold",
        "source_model": "<recorded from the gateway response>",
        "severity": "high | medium | low"
      }
    ],
    "persona_blindspots": [
      {
        "blindspot": "What was overlooked",
        "suggestion": "Alternative perspective",
        "source_model": "<recorded from the gateway response>"
      }
    ],
    "missing_tasks": [],
    "hidden_conflicts": []
  }
}
```

### XV Availability & Fallback

- If `openrouter_mcp` available: use MCP tool `ask_model` for XV
- If only `openrouter_script` available (API key set): use script-based XV
- If neither available: skip XV silently, output `XV cross-validation unavailable`
