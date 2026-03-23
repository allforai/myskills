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
      "business_summary": "Core order service handling create/cancel/query operations",
      "is_abstraction": false
    }
  ]
}
```

**Card fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `path` | string | yes | Relative file path from source root |
| `module` | string\|null | yes | Module ID (M001, M002, ...) from source-summary. `null` for root-level config files (nginx.conf, routes.yaml, etc.) per iron law 18 |
| `kind` | string | yes | LLM-judged file role. Free-form — no controlled vocabulary. Examples: controller, service, repository, model, middleware, util, config, test, view, component, hook, store, migration, script, proto. Phase 3 consumers MUST NOT branch logic on specific `kind` values |
| `symbols` | array | yes | Public functions/classes/methods with signatures and business intent |
| `symbols[].name` | string | yes | Symbol name |
| `symbols[].type` | string | yes | function, class, method, interface, type, enum, constant |
| `symbols[].signature` | string | yes | Parameter and return type signature |
| `symbols[].business_intent` | string | yes | One-sentence description of what this symbol does in business terms |
| `dependencies` | array | yes | Files this file imports/depends on (module/filename format) |
| `business_summary` | string | yes | One-sentence summary of the file's business purpose |
| `is_abstraction` | boolean | no | `true` if this file is a shared abstraction consumed by multiple modules (per iron law 12). Default: `false` |
| `abstraction_consumers` | array | no | Module IDs that consume this abstraction. Only present when `is_abstraction: true` |
| `confidence` | string | no | `"high"` (default) or `"low"` (quiz failed after max retries, card may be incomplete) |

For large projects (200+ files), `file-catalog.json` may exceed 100KB. To support efficient per-module loading, Step 2.3.7 also writes per-module slice files:

```
.allforai/code-replicate/
├── file-catalog.json            # Complete catalog (all files)
├── file-catalog-M001.json       # Module slice (only M001 files)
├── file-catalog-M002.json       # Module slice (only M002 files)
├── file-catalog-root.json       # Root-level files (module: null)
└── ...
```

Phase 3 loads the per-module slice file directly, avoiding the need to parse and filter the full catalog.

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
| `concepts` | Business concept keyword (LLM-generated, advisory — for navigation, not programmatic querying) | Array of file paths involved |
| `entities` | Entity/model name | `{definition, fields, used_by}` — query-optimized view; `source-summary.data_entities` remains source of truth for entity schemas |
| `api_surface` | API endpoint string. Format adapts to project type: `"POST /api/orders"` (HTTP), `"gRPC OrderService.CreateOrder"` (gRPC), `"WS /chat"` (WebSocket), `"GraphQL mutation createOrder"` (GraphQL), `"Event order.created"` (event-driven) | `{handler, service, middleware}` chain |

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
         d. If quiz inconsistent with card -> re-read file, regenerate card (max 2 retries)
         e. If still inconsistent after retries -> mark card confidence: "low", move on
       -> also output module summaries to source-summary (unchanged)
       -> module summaries are synthesized AFTER all file cards for that module are generated
          (cards inform the summary, ensuring consistency)

2.3.5  Sampling read -> for each newly discovered important file:
         a-e. Same card generation + quiz flow
       -> update source-summary (unchanged)

2.3.7  (NEW) Knowledge base assembly:
         a. Collect all file cards -> file-catalog.json + per-module slice files
         b. Build inverted indexes from cards -> code-index.json
         c. Store in .allforai/code-replicate/
         d. Update replicate-config.progress with step "2.3.7"
```

### Quiz Verification Protocol

After generating a file card, LLM self-answers three questions:

1. **Entry points**: What are the entry functions/exported interfaces of this file?
2. **External dependencies**: What external services/modules does it depend on?
3. **Core scenario**: What is the core business scenario this file handles?

**Worked example:**

```
File: order_service.go
Card generated:
  symbols: [CreateOrder, GetOrder]
  dependencies: [user_service.go, order_repo.go]
  business_summary: "Order lifecycle management"

Quiz answers:
  Q1: CreateOrder, CancelOrder, GetOrder     <- CancelOrder not in card symbols!
  Q2: user_service, order_repo, payment_api  <- payment_api not in card dependencies!
  Q3: Order lifecycle management

Mismatch on Q1 and Q2 -> re-read order_service.go -> regenerate card
  (likely missed CancelOrder function and payment_api import on first read)
```

**Verification rules:**
- Compare quiz answers against the generated card's `symbols`, `dependencies`, and `business_summary`
- If any answer contains information not captured in the card -> re-read file, regenerate card
- Max 2 re-read retries per file. After 2 failures, mark `"confidence": "low"` and proceed
- This catches attention fragmentation (LLM read the file but didn't fully transfer info to the card). It does NOT catch the case where the LLM failed to read the file at all — that is addressed by the existing Step 2.3.5 coverage mechanism

### Checkpoint and Resume

Step 2.3.7 updates `replicate-config.progress` with step ID `"2.3.7"`.

File cards are generated inline during Steps 2.3 and 2.3.5, accumulated in the LLM context. Step 2.3.7 assembles them into files. If the process crashes:
- **Before 2.3.7**: Cards exist only in LLM context. On resume, re-run from the last completed module in Step 2.3/2.3.5 (existing resume behavior)
- **After 2.3.7 starts**: `file-catalog.json` is written atomically at the end. If it exists, 2.3.7 is considered complete

### Integration with existing steps

- Steps 2.3 and 2.3.5 behavior is **extended, not replaced**. Module summaries in source-summary.json are still generated.
- File cards are an additional output alongside the existing module-level summaries.
- Module summaries are generated AFTER file cards for that module, so the summary can be synthesized from cards (better consistency than independent generation).
- Files identified in `source-summary.abstractions` should have `is_abstraction: true` and `abstraction_consumers` in their cards, preserving iron law 12's abstraction reuse signal.

## Phase 3 Flow Changes

### Current context loading

```
Per artifact generation call:
  - source-summary.json (~4-8KB, always loaded)
  - current module source code (~10-30KB)
  - target schema definition (~2-4KB)
  - replicate-config summary (~1KB)
```

### New context loading

The line "current module source code (~10-30KB)" is **replaced by** code-index + file-catalog module slice:

```
Per artifact generation call:
  - source-summary.json (~4-8KB, always loaded)
  - code-index.json (~5-10KB, always loaded)           <- NEW, replaces raw source
  - file-catalog module slice (~3-8KB, per module)      <- NEW, replaces raw source
  - target schema definition (~2-4KB)
  - replicate-config summary (~1KB)

  Targeted source fallback (when card detail is insufficient):
  -> Card says "CreateOrder in order_service.go validates inventory"
  -> Need exact validation logic? -> Read only CreateOrder function (~20 lines)
  -> This is targeted reading with a specific question, not blind file scanning
```

**New iron law 26**: source-summary AND code-index always in context for every Phase 3 LLM call (extends iron law 2).

### 4D Self-Check Adaptation

The existing D2 (evidence) dimension asks "can each acceptance_criteria trace to source code?" With cards as intermediary:
- D2 now traces to **file card** first (symbol name + business_intent)
- If the card provides sufficient evidence, no source read needed
- If D2 requires exact implementation detail, targeted source read as fallback
- The trace chain becomes: artifact claim -> card symbol -> (optional) source line

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
├── file-catalog.json          # Complete catalog (all files)
├── file-catalog-M001.json     # Per-module slice
├── file-catalog-M002.json     # Per-module slice
├── file-catalog-root.json     # Root-level files (module: null)
├── code-index.json            # Inverted indexes (always in context)
├── source-summary.json        # Existing (unchanged)
├── extraction-plan.json       # Existing (unchanged)
└── ...
```

## Implementation Scope

### Files to modify

| File | Change |
|------|--------|
| `docs/phase2/stage-a-structure.md` | Extend 2.3/2.3.5 with card generation + quiz protocol; add Step 2.3.7 (knowledge base assembly) |
| `skills/code-replicate-core.md` | Add Step 2.3.7 to Phase 2 Stage A table; add iron law 26 (code-index always in context) |
| `docs/phase3/standard-artifact-steps.md` | Replace "current module source code" context line with "code-index + file-catalog module slice + targeted fallback"; update 4D self-check D2 for card-based evidence |
| `docs/schema-reference.md` | Add file-catalog.json and code-index.json schemas |

### Files NOT needed

| Originally planned | Why not needed |
|-------------------|---------------|
| `cr_build_knowledge.py` | No script — LLM generates cards directly as it reads |
| `cr_query_knowledge.py` | Not needed — Phase 3 loads per-module slice files directly |
| `test_cr_build_knowledge.py` | No script to test |
| `test_cr_query_knowledge.py` | No script to test |

### What stays the same

- source-summary.json generation (unchanged, cards are additive; module summaries now synthesized from cards)
- All merge scripts (unchanged, they consume fragments not cards)
- extraction-plan.json structure (unchanged)
- Phase 3 fragment generation flow (unchanged, only context loading changes)
- Iron laws 1-25 (unchanged; new law 26 added)

## Token Budget Estimate

For a 50-file project:

| Activity | Extra tokens |
|----------|-------------|
| Card generation (50 files x ~200 tokens/card, variable for large files) | ~10K |
| Quiz verification (50 files x ~100 tokens/quiz) | ~5K |
| Re-reads from failed quizzes (~10% failure rate, max 2 retries) | ~3K |
| code-index generation | ~2K |
| **Total extra Phase 2 cost** | **~20K tokens** |
| **Phase 3 savings** (no blind re-reading) | **-15K to -30K tokens** |

Net effect: roughly neutral on tokens, significantly better on reliability.

Note: For files with many exports (e.g., utility module with 30 functions), card token count may be 500-1000 tokens. The 200 tokens/card figure is an average; worst case for a 200-file project with complex utility modules could reach 80-100K for file-catalog.json.
