# Reverse Concept Capability

> Reverse-engineer product concept from existing code. Extracts the "why" and
> "for whom" that the code implicitly encodes but never explicitly states.
> Output is schema-compatible with product-concept, so downstream phases
> (product-analysis, generate-artifacts, product-verify) work identically
> regardless of whether concept came from forward design or reverse extraction.

## Purpose

Existing code embeds product decisions in its structure: entity relationships
reveal the domain model, auth middleware reveals role boundaries, API groupings
reveal feature domains, pricing tables reveal business model, AI prompts reveal
value propositions. This capability extracts those implicit decisions into
explicit, structured concept artifacts.

**Why this matters:**
Without concept artifacts, downstream phases have no independent baseline.
Product-analysis becomes "list what code does" instead of "evaluate whether
code achieves product goals." Product-verify becomes circular — checking code
against code-derived artifacts.

## Input Path

| Input | Source | When |
|-------|--------|------|
| Source code | discovery outputs (source-summary, file-catalog, infrastructure-profile) | goal = analyze |
| README / docs | project documentation | always |
| Existing product-map (if any) | previous analysis artifacts | re-analyze |

## What LLM Must Accomplish

### Required Outputs

| Output | What | Why downstream needs it |
|--------|------|------------------------|
| `product-concept.json` | Mission, target users, core JTBD, value propositions, key differentiators | product-analysis needs to evaluate feature completeness against intended value |
| `role-value-map.json` | Per-role: jobs, pains, gains, operation profile, client type | experience-map needs to judge screen design against role needs |
| `product-mechanisms.json` | Governance styles, system boundaries, content lifecycle | product-analysis needs to know what's in-scope vs external |
| `concept-baseline.json` | Compact (~2KB) distilled baseline pushed to all downstream phases | ALL downstream phases auto-load this for consistency |
| `business-model.json` | Revenue model, pricing tiers, unit economics (if detectable) | product-verify needs to check monetization flows are implemented |
| `concept-conflicts.json` | Contradictions found between code, docs, config, and modules | Human review — conflicts must be resolved before downstream phases proceed |

**concept-conflicts.json field schema:**
```json
{
  "conflicts": [
    {
      "type": "<enum: doc_vs_code | module_vs_module | schema_vs_logic | config_vs_impl | role_vs_permission>",
      "description": "<string — what contradicts what>",
      "evidence_a": "<string — file:line or source A>",
      "evidence_b": "<string — file:line or source B>",
      "severity": "<enum: high | medium | low>",
      "resolution_hint": "<string — which side is likely correct and why>",
      "resolved": false
    }
  ],
  "summary": {
    "total": "<number>",
    "high": "<number>",
    "medium": "<number>",
    "low": "<number>"
  }
}
```

When conflicts are found, reverse-concept MUST present them to the user for resolution
before proceeding. The user decides which side is correct. Unresolved high-severity
conflicts block downstream phases — product-analysis should not proceed on a contradictory baseline.

**concept-baseline.json minimum field schema:**
```json
{
  "product_name": "<string>",
  "mission": "<string — one sentence: Help [user] achieve [outcome] by [mechanism]>",
  "target_users": ["<string — role names>"],
  "core_features": [
    {
      "id": "<string>",
      "name": "<string>",
      "jtbd": "<string — Job-to-be-Done this feature serves>",
      "evidence": ["<string — file:line or module reference>"]
    }
  ],
  "business_flows": [
    {
      "id": "<string>",
      "name": "<string>",
      "steps": ["<string>"]
    }
  ],
  "constraints": ["<string>"],
  "governance_style": "<string — from governance-styles.md>"
}
```
All fields with evidence[] arrays MUST cite code evidence per Evidence-Based Extraction rules.
The full schema reference is in `cross-phase-protocols.md §A.1`.

### Schema Compatibility

All output files MUST use the same schema as forward-designed product-concept outputs.
This ensures downstream phases (product-analysis, experience-map, use-case, etc.) work
identically regardless of whether concept was designed forward or extracted backward.

See `product-concept.md` sub-phases for the canonical schemas of each file.
`concept-baseline.json` schema is defined in `cross-phase-protocols.md §A.1`.

### Downstream Consumers

> Bootstrap reads this table to generate Context Pull sections for downstream node-specs.
> `required` = subagent reports error if file missing; `optional` = warning + continue.

| Artifact | Field Path | Consumer Capability | Required | Reason |
|----------|------------|---------------------|----------|--------|
| `concept-baseline.json` | `jobs`, `mission` | product-analysis | required | product-analysis 用 baseline 做一致性检查，避免循环分析 |
| `concept-baseline.json` | `jobs[].success_criteria` | product-verify | optional | 验收时检查实现是否满足 JTBD 成功条件 |
| `concept-conflicts.json` | `conflicts[]` | product-analysis | required | product-analysis 需要知道哪些概念有冲突，避免基于矛盾信息做分析 |
| `concept-conflicts.json` | `conflicts[].resolved` | concept-acceptance | optional | 验收时检查冲突是否已被解决 |

## Methodology Guidance

### Extraction Strategy (not steps — principles)

**1. Mission & Target Market**
- README is the primary source (project description, "who is this for")
- If README is vague, infer from: entity names (what domain?), API endpoint groups
  (what operations?), i18n languages (what market?)
- Express as: "Help [target user] achieve [outcome] by [mechanism]"

**2. JTBD Extraction**
- Each major API endpoint group = one Job domain
- Each iOS/Android Feature module = one Job the user is trying to do
- Classify: functional job (what they do), emotional job (how they feel),
  social job (how others perceive them)
- Evidence: code structure IS the evidence — document which files/modules prove each Job

**3. Role-Value Mapping**
- Auth system reveals role boundaries (user types, permission levels)
- Admin middleware reveals admin vs consumer split
- Entity relationships reveal what each role creates/reads/manages
- For each role: extract jobs (from endpoints), pains (from error handling),
  gains (from success flows)

**4. Governance & System Boundaries**
- Content lifecycle: who creates → who reviews → who publishes → who consumes
- Trace from admin CRUD → publish status field → consumer read endpoint
- System boundaries: what's in-scope (built) vs external (integrated via API)
- Auth flow reveals trust boundaries

**5. Business Model**
- Subscription/payment entities reveal pricing structure
- IAP/RevenueCat integration reveals mobile monetization
- Plan/tier fields reveal feature gating
- If no payment code exists: document as "no monetization detected"

**6. Differentiators & ERRC**
- What does this product do that generic alternatives don't? (from unique features)
- What did it eliminate? (from what's NOT in the code despite being common in the domain)
- What did it reduce/raise? (from implementation depth — shallow vs deep features)

### Evidence-Based Extraction

Every claim in the output MUST cite evidence:
```json
{
  "claim": "Primary job: learn vocabulary through AI conversation",
  "evidence": [
    "flydict-api/internal/controller/conversation_controller.go — 9 conversation endpoints",
    "flydict-ios/FlyDict/Features/Conversation/ — 10 views for chat experience",
    "entity.Message has ContentType with 8 variants including voice, grammar, vocabulary"
  ]
}
```

LLM should NOT speculate beyond what code proves. If a README claims a feature
that code doesn't implement, flag it as `"status": "claimed_not_implemented"`.

### Conflict Detection (MANDATORY)

After extraction, systematically scan for contradictions across all evidence sources.
Conflicts are presented to the user for resolution — LLM does NOT resolve them.

**Check dimensions:**

| Conflict Type | How to detect |
|---------------|---------------|
| doc_vs_code | README/docs claim feature X → grep for implementation → not found or partially implemented |
| module_vs_module | Backend defines N enum values / API endpoints → Frontend handles M < N (or different names) |
| schema_vs_logic | DB table/field exists → no code reads or writes it (orphaned schema) |
| config_vs_impl | .env/.config references service X → code integrates service Y instead |
| role_vs_permission | Auth middleware defines role → no API endpoints are restricted to that role (phantom role) |

**Severity rules:**
- **high**: Affects core business flow (e.g., payment module contradicts pricing docs)
- **medium**: Affects secondary feature (e.g., social sharing claimed but not implemented)
- **low**: Cosmetic or naming inconsistency (e.g., `user_name` vs `username`)

**Output:** Write all conflicts to `concept-conflicts.json`. Present high-severity
conflicts to user immediately with resolution options. User must resolve or
acknowledge before reverse-concept marks itself complete.

### Quality Bar

- Every JTBD must have >= 2 code evidence points
- Every role must trace to auth/middleware code
- Governance style must trace to status fields + admin endpoints
- Business model must trace to payment/subscription entities (or explicitly "none detected")
- Concept-baseline must be under 2KB

## Composition Hints

### Single Node (default)
For most projects: one reverse-concept node reads discovery outputs + README + key source files.

### Split by Domain
For large multi-domain products: split concept extraction per business domain
(e.g., reverse-concept-learning, reverse-concept-social, reverse-concept-commerce).

### Merge with Discovery
For very small projects (< 20 files): merge discovery + reverse-concept into one node.

### Skip Entirely
When `has_product_concept` is true AND user is not re-analyzing: concept already exists,
skip reverse extraction. But if user explicitly chose "逆向分析", always run —
they want a fresh extraction.

## Knowledge References

### Phase-Specific:
- cross-phase-protocols.md §A.1: concept-baseline.json schema (MUST follow exactly)
- cross-phase-protocols.md §A.4: frequently pulled fields reference
- product-design-theory.md §Phase-1: JTBD, VPC, Lean Canvas, ERRC theory anchors
- product-concept.md: canonical output schemas for forward-designed concept
