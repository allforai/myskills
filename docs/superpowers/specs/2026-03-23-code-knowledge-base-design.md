# Code Knowledge Base Design

## Problem

code-replicate v4.0.0 has two reliability issues:

1. **Phase 2 laziness**: LLM reads source files but may skim/skip (Step 2.3.5 sampling mitigates but doesn't eliminate)
2. **Phase 3 re-reading**: LLM needs source code info again, re-reads unreliably with attention decay

Root cause: every time information is needed, the LLM must re-read raw files, and attention is unreliable.

## Solution

During Phase 2, as the LLM reads each source file, it **immediately generates a structured file card** and **self-verifies** via quiz. The cards are collected into two artifacts that Phase 3 uses instead of raw source, with targeted fallback to source for exact details.

## Artifacts

### file-catalog.json (~30-50KB, loaded per-module slice)

One card per source file:

```json
{
  "version": "1.0.0",
  "generated_at": "2026-03-23T10:00:00Z",
  "files": [
    {
      "path": "internal/service/order_service.go",
      "module": "M002",
      "kind": "service",
      "symbols": [
        {
          "name": "CreateOrder",
          "type": "function",
          "signature": "(ctx, req) (*Order, error)",
          "business_intent": "Create order: validate inventory -> calculate price -> initiate payment"
        }
      ],
      "dependencies": ["M001/user_service.go", "M002/order_repo.go"],
      "business_summary": "Core order service handling create/cancel/query operations"
    }
  ]
}
```

**Card fields:**

| Field | Type | Description |
|-------|------|-------------|
| `path` | string | Relative file path from source root |
| `module` | string | Module ID (M001, M002, ...) from source-summary |
| `kind` | string | LLM-judged file role: controller, service, repository, model, middleware, util, config, test, view, component, hook, store, migration, script, proto, ... |
| `symbols` | array | Public functions/classes/methods with signatures and business intent |
| `symbols[].name` | string | Symbol name |
| `symbols[].type` | string | function, class, method, interface, type, enum, constant |
| `symbols[].signature` | string | Parameter and return type signature |
| `symbols[].business_intent` | string | One-sentence description of what this symbol does in business terms |
| `dependencies` | array | Files this file imports/depends on (module/filename format) |
| `business_summary` | string | One-sentence summary of the file's business purpose |

### code-index.json (~5-10KB, always in context)

Three inverted indexes for cross-module querying:

```json
{
  "version": "1.0.0",
  "generated_at": "2026-03-23T10:00:00Z",
  "concepts": {
    "authentication": ["M001/auth_service.go", "M001/jwt_helper.go", "M003/auth_middleware.go"],
    "order_processing": ["M002/order_service.go", "M002/payment_service.go"],
    "notification": ["M004/email_sender.go", "M004/push_service.go"]
  },
  "entities": {
    "User": {
      "definition": "M001/models/user.go",
      "fields": ["id", "email", "name", "role", "created_at"],
      "used_by": ["M001/user_service.go", "M002/order_service.go"]
    },
    "Order": {
      "definition": "M002/models/order.go",
      "fields": ["id", "user_id", "items", "total", "status", "created_at"],
      "used_by": ["M002/order_service.go", "M002/order_repo.go"]
    }
  },
  "api_surface": {
    "POST /api/orders": {
      "handler": "M002/order_controller.go:CreateHandler",
      "service": "M002/order_service.go:CreateOrder",
      "middleware": ["M003/auth_middleware.go"]
    }
  }
}
```

**Index fields:**

| Index | Key | Value |
|-------|-----|-------|
| `concepts` | Business concept keyword | Array of file paths involved |
| `entities` | Entity/model name | `{definition, fields, used_by}` |
| `api_surface` | API endpoint (method + path) | `{handler, service, middleware}` chain |

## Phase 2 Flow Changes

### Current flow

```
2.3    Read key_files -> output module summaries to source-summary
2.3.5  Sampling read -> discover missed important files, update source-summary
```

### New flow

```
2.3    Read key_files -> for each file:
         a. Read file
         b. Generate file card (JSON)
         c. Quiz verification (3 questions, self-answered)
         d. If quiz inconsistent with card -> re-read file, regenerate card
       -> also output module summaries to source-summary (unchanged)

2.3.5  Sampling read -> for each newly discovered important file:
         a-d. Same card generation + quiz flow
       -> update source-summary (unchanged)

2.3.7  (NEW) Knowledge base assembly:
         a. Collect all file cards -> file-catalog.json
         b. Build inverted indexes from cards -> code-index.json
         c. Store both in .allforai/code-replicate/
```

### Quiz Verification Protocol

After generating a file card, LLM self-answers three questions:

1. **Entry points**: What are the entry functions/exported interfaces of this file?
2. **External dependencies**: What external services/modules does it depend on?
3. **Core scenario**: What is the core business scenario this file handles?

Verification rule:
- Compare quiz answers against the generated card's `symbols`, `dependencies`, and `business_summary`
- If any answer contradicts the card -> re-read the file and regenerate the card
- This is a self-consistency check, not an external validation

### Integration with existing steps

- Steps 2.3 and 2.3.5 behavior is **extended, not replaced**. Module summaries in source-summary.json are still generated as before.
- File cards are an additional output alongside the existing module-level summaries.
- The quiz adds ~3 lines of LLM output per file. For a 50-file project, this is ~150 extra lines — negligible token cost.

## Phase 3 Flow Changes

### Current context loading

```
Per artifact generation:
  source-summary (8KB) + raw source files (10-30KB per module)
  -> LLM may skim/skip parts of source
```

### New context loading

```
Per artifact generation:
  source-summary (8KB)
  + code-index.json (5-10KB, always loaded)
  + file-catalog.json module slice (3-8KB, loaded per extraction-plan module reference)
  -> Information is pre-digested, LLM queries rather than reads

  Fallback for exact details:
  -> Card says "CreateOrder in order_service.go validates inventory"
  -> Need exact validation logic? -> Read only that function (20 lines)
  -> This is targeted reading, not blind file scanning
```

### Fidelity-level behavior

| Fidelity | Primary source | Fallback to raw source |
|----------|---------------|----------------------|
| interface | code-index + card symbols | Rarely needed |
| functional | cards (business_intent + dependencies) | When business rules have edge conditions |
| architecture | cards + code-index (full picture) | When cross-cutting concerns need detail |
| exact | cards as navigation map | Frequently — read specific functions for precise replication |

### extraction-plan integration

The extraction-plan.json already specifies per-artifact source files. Phase 3 changes:

```
Before: extraction-plan says "read M002/order_service.go" -> LLM reads entire file
After:  extraction-plan says "read M002/order_service.go"
        -> LLM first checks file-catalog card for that file
        -> Card has symbols + business_intent -> usually sufficient
        -> If not -> targeted read of specific function from source
```

## Storage

```
.allforai/code-replicate/
├── file-catalog.json      # All file cards
├── code-index.json        # Inverted indexes
├── source-summary.json    # Existing (unchanged)
├── extraction-plan.json   # Existing (unchanged)
└── ...
```

## Implementation Scope

### Files to modify

| File | Change |
|------|--------|
| `docs/phase2/stage-a-structure.md` | Add Step 2.3.7, extend 2.3/2.3.5 with card generation + quiz |
| `skills/code-replicate-core.md` | Add Step 2.3.7 to Phase 2 Stage A table |
| `docs/phase3/standard-artifact-steps.md` | Change context loading to code-index + file-catalog slices + fallback |
| `docs/schema-reference.md` | Add file-catalog.json and code-index.json schemas |

### Files NOT needed

| Originally planned | Why not needed |
|-------------------|---------------|
| `cr_build_knowledge.py` | No script — LLM generates cards directly as it reads |
| `cr_query_knowledge.py` | Optional — Phase 3 loads catalog by module slice, no CLI query needed |
| `test_cr_build_knowledge.py` | No script to test |
| `test_cr_query_knowledge.py` | No script to test |

### What stays the same

- source-summary.json generation (unchanged, cards are additive)
- All merge scripts (unchanged, they consume fragments not cards)
- extraction-plan.json structure (unchanged)
- Phase 3 fragment generation flow (unchanged, only context loading changes)
- All existing iron laws (unchanged, new law added for card generation)

## Token Budget Estimate

For a 50-file project:

| Activity | Extra tokens |
|----------|-------------|
| Card generation (50 files x ~200 tokens/card) | ~10K |
| Quiz verification (50 files x ~100 tokens/quiz) | ~5K |
| Re-reads from failed quizzes (~10% failure rate) | ~3K |
| code-index generation | ~2K |
| **Total extra Phase 2 cost** | **~20K tokens** |
| **Phase 3 savings** (no blind re-reading) | **-15K to -30K tokens** |

Net effect: roughly neutral on tokens, significantly better on reliability.
