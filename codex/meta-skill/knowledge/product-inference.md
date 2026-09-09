# Product Inference (Codex)

Use this guidance when the user's selected bootstrap goal needs code-based
product evidence. Follow canonical `task_route` and `task_scope`: local work
reads only relevant evidence, even when product documents are missing;
new-product starts from user intent without reverse inference. Do not emit a
whole-product summary merely because code exists.

Observed behavior and inferred intent are provisional evidence. High confidence
is not user confirmation. Existing confirmed decisions retain authority within
their applicable scope, and new/changed requirements need recorded user consent
under the canonical bootstrap planning contract. This summary never replaces
that contract or supplies acceptance criteria from implementation alone.

For reconstruction, supply the six-topic draft, source quotes, uncertainties and
contradiction/gap questions to canonical `product-intent-confirmation.md`. Its
interactive copied CLI owns persistence and resume; inferred summary fields never
substitute for the journal-backed frozen product baseline.

## Goal

Produce a compact, evidence-backed product summary that helps Codex understand:

- what the product is
- who it appears to serve
- which core user-facing systems exist
- which hidden complexity clusters are likely to matter next

## Output

When enough evidence exists, bootstrap should write:

- `.allforai/bootstrap/product-summary.json`

Recommended shape:

```json
{
  "schema_version": "1.0",
  "project_name": "<name>",
  "product_shape": "<one-line classification>",
  "platforms": ["<platform>"],
  "core_systems": ["<system>"],
  "evidence": [
    {
      "kind": "entrypoint | protocol | ui | config | runtime",
      "path": "<project-relative path>",
      "note": "<why this matters>"
    }
  ],
  "confidence": "high | medium | low",
  "open_questions": ["<unknowns>"]
}
```

## Research-First Rules

1. Infer from real repository evidence first:
   - entrypoints
   - protocols
   - UI/page names
   - runtime modules
   - config and deployment surfaces
2. Use LLM synthesis to connect evidence into a product picture.
3. Label code-based product claims as observed or inferred; user-added desired requirements need no code evidence and belong in the confirmed requirement path.
4. If evidence is weak or conflicting, lower confidence and record open questions.

Important:

- product inference explains what the product appears to be
- product inference does not replace UI fidelity evidence for replication work
- if the workflow goal is source-faithful UI reproduction, bootstrap must still capture source UI structure and interaction evidence explicitly
- if repository evidence already makes the product shape obvious, prefer emitting `product-summary.json` directly during bootstrap rather than dedicating a main execution node to it

## Good Uses

- reverse engineering an inherited codebase
- reconstructing product scope from partial implementations
- detecting hidden user-facing systems before planning downstream work

## Validation

If `product-summary.json` is emitted, it should:

- name at least one evidence-backed product classification
- include at least 3 evidence entries
- avoid purely architectural restatement with no user-facing interpretation
