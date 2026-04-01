# Product Concept Capability (Product Design Layer)

> Product design is NOT a single node or a fixed pipeline.
> It is a **state machine layer** — LLM generates project-specific nodes,
> each with entry/exit requires, theory anchors, and validation gates.

## Purpose

From vague idea to structured product concept. Each sub-phase is an independent
node that the orchestrator can include, skip, reorder, or loop.

## Product Design Layer — Sub-Phase Nodes

LLM generates a subset of these based on project type and goals.
Each sub-phase has a **theory anchor** (classical framework that guides the work)
and a **method** (how to execute).

### Sub-Phase 1: Problem Discovery (破题)

**Theory anchors:** First Principles, Opportunity Solution Tree

**What it does:**
1. Decompose user's vague description into the **deepest underlying need**
   (not "I want to build a platform" but "certain people can't do X in scenario Y")
2. WebSearch 2-3 rounds: industry pain points, academic research, market reports
3. Present as selection questions (never open-ended)

**Output:** `problem-domain.json` (problem essence, opportunity tree skeleton)

**Skip when:** User provides a clear, validated problem statement already.

---

### Sub-Phase 2: Assumption Zeroing (假设清零)

**Theory anchors:** First Principles (applied to industry assumptions)

**What it does:**
1. List 5-10 "industry consensus" assumptions in this domain
   (e.g., "learning apps need gamification", "social apps need friend lists")
2. Classify each: physical law (must obey) vs human convention (can challenge)
3. Ask user: which conventions do you want to challenge?
4. Challenging conventions opens new design space

**Method:** Multi-model parallel if available (one model generates assumptions,
another challenges them). Single-model fallback: self-debate with explicit framing.

**Output:** `assumption-zeroing.json`

**Skip when:** Pure replication (no concept change). Keep for rebuild with concept change.

---

### Sub-Phase 3: Market Research (竞品调研)

**Theory anchors:** Blue Ocean ERRC, Porter's Five Forces

**What it does:**
1. WebSearch 3+ rounds: direct competitors, indirect competitors, failed products
2. Per competitor: positioning, features, pricing, user reviews, strengths/weaknesses
3. Map competitive landscape: who does what, where are the gaps
4. ERRC matrix: what to Eliminate, Reduce, Raise, Create vs competitors

**Output:** `competitor-analysis.json`, `errc-matrix.json`

**Skip when:** User already has deep domain expertise and competitive knowledge.

---

### Sub-Phase 4: Innovation Exploration (创新探索)

**Theory anchors:** ERRC (from Blue Ocean), Cross-domain inspiration

**What it does:**
1. Based on assumption-zeroing results: "if we remove constraint X, what's possible?"
2. WebSearch: solutions from adjacent industries, emerging tech, academic research
3. Generate 3-5 innovation proposals, each with rationale and risk assessment
4. Cross-domain inspiration: what patterns from gaming/social/fintech/etc. apply here?

**Method:** Multi-model parallel if available (independent exploration, then merge).

**Output:** `innovation-opportunities.json`

**Depends on:** assumption-zeroing (which conventions to challenge)

---

### Sub-Phase 5: User & Role Definition (角色与价值)

**Theory anchors:** JTBD (Jobs To Be Done), VPC (Value Proposition Canvas), Mom Test

**What it does:**
1. WebSearch: typical user composition for this product category, real user feedback
2. Define roles using JTBD: what job is each role hiring this product to do?
3. VPC per role: Jobs / Pains / Gains → Pain Relievers / Gain Creators
4. Mom Test principle: questions based on behavioral facts, not opinion predictions
5. **Producer-side closure check**: if someone consumes, who produces? who operates?
6. **Multi-client declaration**: for each role, identify ALL client platforms they use.
   A single role may have multiple clients (e.g., consumer: iOS app + Android app + web + H5).
   For each role, declare:
   - `clients[]`: array of client apps, each with `app` name, `client_type`, `platform`
   - `feature_parity`: one of four modes:
     - `full`: all clients implement same features (e.g., iOS vs Android)
     - `partial`: mostly same, with exceptions listed in `parity_exceptions[]` (e.g., App vs Web)
     - `independent`: each client has completely different features (e.g., admin vs user)
     - `explicit`: each client declares its own `supported_features[]` — used for modality-limited
       clients (voice assistant, embedded panel, watch) that can only do a small subset
   - `parity_exceptions[]`: features that differ across clients (only when parity=partial)

   **Backward compatibility**: if a role has only one client, the legacy `app` + `client_type`
   fields are equivalent to a single-element `clients[]` array.

   Example:
   ```json
   {
     "id": "R1", "name": "消费者",
     "clients": [
       { "app": "buyer-ios", "client_type": "swiftui-ios", "platform": "ios" },
       { "app": "buyer-android", "client_type": "kotlin-android", "platform": "android" },
       { "app": "buyer-web", "client_type": "next-js", "platform": "desktop-web" }
     ],
     "feature_parity": "partial",
     "parity_exceptions": ["推送通知仅限移动端", "AR 试穿仅限 iOS"]
   }

   // explicit mode — for modality-limited clients
   {
     "id": "R1", "name": "家庭主人",
     "clients": [
       { "app": "home-ios", "client_type": "swiftui-ios", "platform": "ios" },
       { "app": "home-voice", "client_type": "voice-skill", "platform": "alexa",
         "modality": "voice", "supported_features": ["设备控制", "触发场景", "查看状态"] },
       { "app": "home-panel", "client_type": "flutter-embedded", "platform": "wall-panel",
         "modality": "touch-limited", "supported_features": ["设备控制", "触发场景", "摄像头预览"] }
     ],
     "feature_parity": "explicit"
   }
   ```

**Output:** `role-profiles.json`, `vpc-per-role.json`

---

### Sub-Phase 6: Business Model (商业模式)

**Theory anchors:** Lean Canvas, Business Model Canvas

**What it does:**
1. WebSearch: industry pricing models, revenue benchmarks, cost structures
2. Define: revenue streams, cost structure, key metrics, pricing strategy
3. Unit economics: CAC, LTV, payback period (at least rough estimates)
4. Lean Canvas: one-page business model

**Output:** `business-model.json`, `lean-canvas.json`

---

### Sub-Phase 7: Positioning & Differentiation (定位与差异化)

**Theory anchors:** Blue Ocean ERRC, Kano Model

**What it does:**
1. Synthesize insights from market research + innovation exploration
2. Kano classification: which features are must-be, one-dimensional, attractive?
3. Value proposition: one sentence — why this product exists
4. Positioning statement: for [user], who [need], [product] is [category] that [benefit]

**Output:** `positioning.json`

**Depends on:** market-research, innovation-exploration, user-role-definition

---

### Sub-Phase 8: Concept Crystallization (概念结晶)

**Theory anchors:** All above converge here

**What it does:**
1. Synthesize all prior sub-phase outputs into a unified product concept
2. Feature prioritization: MVP (must-have) vs post-launch (nice-to-have)
3. Information architecture: high-level screen/flow structure
4. Interaction principles: core design rules
5. Success metrics: falsifiable, measurable numbers

**Output:** `product-concept.json`, `product-definition.md`

**Depends on:** all prior sub-phases

---

### Sub-Phase 9: Concept Validation (概念验证)

**Theory anchors:** Lean Startup (Build-Measure-Learn), Risk-driven validation

**What it does:**
1. List all assumptions the concept relies on
2. Classify by risk: high (product fails if wrong) / medium / low
3. For each high-risk assumption: how to validate? (MVP test, user interview, prototype)
4. Multi-model cross-validation if available: send concept to another model for adversarial review

**Output:** `assumption-register.json`, `validation-plan.json`

**Can loop back to:** any prior sub-phase if validation reveals a flawed assumption

---

## Node Dependency Graph (Product Design Layer)

```
problem-discovery
  ↓
assumption-zeroing (can run parallel with market-research)
  ↓
market-research (can run parallel with assumption-zeroing)
  ↓
innovation-exploration
  entry: assumption-zeroing + market-research
  ↓
user-role-definition
  entry: problem-discovery + market-research
  ↓
business-model
  entry: user-role-definition
  ↓
positioning
  entry: market-research + innovation-exploration + user-role-definition
  ↓
concept-crystallization
  entry: all above
  ↓
concept-validation
  entry: concept-crystallization
  can loop back → any prior node
```

## Theory Reference

Each node-spec generated by bootstrap MUST include the theory anchors for that sub-phase.
The theory is embedded in the node-spec body under a `## Theory Anchors` section.

Full theory reference: `${CLAUDE_PLUGIN_ROOT}/knowledge/product-design-theory.md`

## Interaction Mode

**Search-driven selection questions (from old product-concept skill):**
- Never ask open-ended questions
- Every question has 2-4 options generated from WebSearch results
- Each option has evidence ("based on XX report...", "XX competitor does...")
- "Other" response → WebSearch with user's input → new selection question

## Knowledge References

### Phase-Specific (load for nodes generated from this capability):
- innovation-protocols.md §Adversarial-Generation: 4-model protocol for concept innovation
- innovation-protocols.md §Search-Protocol: per-step WebSearch strategy, source quality P1-P4
- innovation-protocols.md §XV-Cross-Validation: multi-model concept review
- consumer-maturity-patterns.md: 11 patterns for consumer product maturity evaluation
- governance-styles.md: governance style decisions that cascade downstream
- product-design-theory.md §Phase-1: First Principles, JTBD, VPC, Lean Canvas, Blue Ocean ERRC, Kano, Mom Test

## Composition Hints

### Full Pipeline (new product, no existing concept)
Generate all 9 sub-phase nodes. User confirms each before proceeding.

### Partial Pipeline (rebuild with concept change, like FlyDict v2)
Skip market-research if user already knows the domain.
Start from assumption-zeroing or innovation-exploration.
Always include concept-crystallization + validation.

### Minimal (small tool, clear concept)
Merge problem-discovery + user-role-definition + concept-crystallization into 1 node.
Skip market-research, assumption-zeroing, innovation-exploration.

### Skip Entirely
When replicating an existing product with no concept change.

### Interactive Design Session (what happened with FlyDict)
When user wants to co-design through conversation rather than automated pipeline.
Generate a single `interactive-concept-design` node that facilitates Q&A discussion,
but still applies theory anchors and produces the same structured outputs.
