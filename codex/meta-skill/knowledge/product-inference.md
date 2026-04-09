# Product Inference (Codex)

Use this guidance when bootstrap can infer the target product from the real codebase.

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
3. Do not invent product claims that are not supported by code or artifacts.
4. If evidence is weak or conflicting, lower confidence and record open questions.

## Good Uses

- reverse engineering an inherited codebase
- reconstructing product scope from partial implementations
- detecting hidden user-facing systems before planning downstream work

## Validation

If `product-summary.json` is emitted, it should:

- name at least one evidence-backed product classification
- include at least 3 evidence entries
- avoid purely architectural restatement with no user-facing interpretation
