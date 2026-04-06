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

### Schema Compatibility

All output files MUST use the same schema as forward-designed product-concept outputs.
This ensures downstream phases (product-analysis, experience-map, use-case, etc.) work
identically regardless of whether concept was designed forward or extracted backward.

See `product-concept.md` sub-phases for the canonical schemas of each file.
`concept-baseline.json` schema is defined in `cross-phase-protocols.md §A.1`.

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
