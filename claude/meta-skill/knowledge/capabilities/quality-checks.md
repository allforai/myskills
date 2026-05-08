# Quality Checks Capability

> Post-implementation quality validation: dead link detection, CRUD gap hunting,
> ghost feature removal, and cross-layer field name consistency.

## Purpose

Catch quality issues that slip through individual node verification:
- Dead links / broken references in code and artifacts
- CRUD operations that exist in API but have no UI (or vice versa)
- Ghost features (code that's unreachable from any user flow)
- Field name drift between UI labels, API params, DB columns

## Protocol

### Deadhunt
1. **Dead links**: Scan routes/navigation for links pointing to non-existent pages
2. **CRUD gaps**: Cross-reference UI operations × API endpoints × DB operations
3. **Ghost features**: Code reachability analysis — functions not called from any route
4. **Seam checks**: Integration points between modules — caller/callee signature match

### Fieldcheck
1. **UI → API**: Form field names match API request parameter names
2. **API → Entity**: API parameter names match ORM/model field names
3. **Entity → DB**: Model field names match database column names
4. **End-to-end**: Trace a field from UI label through API to DB column — consistent?

### Understand-then-Scan Pattern
For both deadhunt and fieldcheck:
1. LLM reads project structure once → builds understanding
2. Derives detection rules from understanding (not hardcoded grep patterns)
3. Batch scans all files using derived rules
4. Reports findings with file:line references

Output: `.allforai/deadhunt/deadhunt-report.json` + `.allforai/deadhunt/fieldcheck-report.json`

**deadhunt-report.json field schema:**
```json
{
  "dead_routes": [
    {
      "route": "<string>",
      "file": "<string — file:line>",
      "reason": "<string>"
    }
  ],
  "field_mismatches": [
    {
      "field": "<string>",
      "expected": "<string>",
      "actual": "<string>",
      "file": "<string — file:line>"
    }
  ],
  "fix_tasks": [
    {
      "id": "<string>",
      "type": "<enum: dead_route | field_mismatch | broken_reference>",
      "description": "<string>",
      "file": "<string — file:line reference>",
      "suggested_fix": "<string>"
    }
  ]
}
```
`fix_tasks[].file` MUST include line number (file:line format). Every finding generates a fix_task.

## Rules (Must Preserve)

1. **Understand-then-scan**: LLM reads code to understand patterns FIRST, then scans. No blind grep.
2. **No false positives on intentional gaps**: Dead code marked with `// deprecated` or `// TODO` is flagged differently from truly orphaned code.
3. **Cross-layer tracing**: Field consistency checked across ALL layers, not just adjacent ones.
4. **Actionable output**: Every finding has file:line reference and suggested fix.

## Knowledge References

### Phase-Specific:
- design-audit-dimensions.md §Reference-Integrity: cross-artifact reference validation
- cross-phase-protocols.md §Upstream-Baseline-Validation: staleness and fidelity checks

## Contract-Parity Check (added 2026-04-14)

Extends deadhunt + fieldcheck with a third scan: **when the same symbol name
is consumed by 2+ sites, do all consumers agree on its shape / semantics?**

Classes of symbol to scan:
- **Env vars** — `ProcessInfo.environment[...]`, `os.Getenv(...)`,
  `process.env.*`, `viper.Get*(...)` — any env name referenced in >1 file
  with different derived usage shapes
- **HTTP request fields** — JSON keys in request bodies, query params, path
  params. If the server handler names field `tier` but the admin UI sends
  `subscription_tier`, that's contract drift, even if both compile
- **Query params declared by the server but never read** — `c.Query("tags")`
  that is parsed into a variable then discarded silently (the value never
  reaches the repo / service). Users who pass `?tags=unknown` get the
  wrong result set. Fails silently unless explicitly tested.
- **Response payload keys** — server returns `free_conv` but iOS decoder
  expects `free_conversation`; decoder gracefully returns nil, UI shows
  blank state, no stacktrace
- **Response-shape decoder mismatch (whole-shape drift)** — server returns
  a wrapper / container containing one or more entities; client
  call-site declares a parametric decoder whose target type is a bare
  entity (or a differently-shaped container). Compile-time the client is
  happy; at runtime the decoder fails and the user sees a broken
  interaction. Distinct from the per-field "payload keys" class above
  because here EVERY field mismatches at once. Common in clients whose
  language enforces static Decodable/Deserializable types at the call
  site — the type system cannot express the actual server shape at the
  API-declaration site, so the drift only appears at runtime.
- **Enum values that N-1 consumers know about** — server produces a value
  in an enum field (e.g., `semantic_type=foo`) but a client-side switch /
  match on that field has no branch for `foo`, falls through to a default
  rendering or action

Detection method:
1. Grep all call sites of the symbol.
2. Extract the expected shape from each surrounding context — what suffix
   is appended, what field is parsed from it, what default is used when
   missing.
3. If any two shapes conflict → `contract_drift_finding`. Include severity
   based on: (a) how many users hit the production path that uses the
   mismatched consumer, (b) whether the mismatch produces a visible error
   or a silent wrong result.

### Response-shape decoder audit (sub-check for typed client decoders)

When the client stack enforces a target type at the decode call-site
(parametric Decodable, generic request helpers, interface-based HTTP
clients), perform this extra audit:

1. Enumerate every client-side call to a request helper that is parametric
   on a decoder target type (generic `request<T>`, typed response
   declarations in interface-based HTTP clients, etc.).
2. For each call, capture the **endpoint identifier** (enum case, URL
   constant, interface method) + the **declared target type**.
3. For each endpoint, locate the server handler. Capture the response
   body shape the handler produces (struct / map / class serialized
   to JSON).
4. Compare the JSON top-level key set the server emits vs the key set
   the client's declared type will accept (exact match required unless
   the decoder explicitly opts into lenient / ignore-unknown handling).
5. Mismatch → `response_shape_decoder_mismatch` finding. User impact
   is always at least P1 because the runtime error surface is usually
   a raw decode error shown to the user, not a silent wrong result.

Common culprits — language-agnostic:
- Server-side pattern: handler wraps the primary result in a container
  carrying auxiliary context (pagination envelope, relationship data,
  operation metadata). Client call-site declared the target type as
  just the primary entity.
- Backend evolution: an endpoint originally returned a bare entity;
  later wrapped in a container for richer data. One client caller
  updated its decoder target, another didn't. Clients with static
  target types still compile but decode fails.
- Multi-client projects: one client platform adopted the new response
  shape; another platform's decoder target lags. Shape drift invisible
  unless both client declaration files are read side-by-side.

Output goes into `fieldcheck-report.json` under a new key:

```json
{
  "contract_drift_findings": [
    {
      "id": "CD-001",
      "symbol": "<shared env-var name>",
      "kind": "env_var_dual_contract",
      "consumers": [
        {"file": "<consumer A file:line>", "shape": "bare host; caller prepends /api/vN"},
        {"file": "<consumer B file:line>", "shape": "full URL including /api/vN"}
      ],
      "severity": "P1",
      "user_impact": "One consumer path works end-to-end; the other consumer path fails the very first request. Indistinguishable until both paths are exercised.",
      "recommended_fix": "Unify both consumers to a single format, OR have the later-binding consumer detect and normalize the format at use site"
    },
    {
      "id": "CD-002",
      "symbol": "<request-body field name>",
      "kind": "request_body_field_drift",
      "consumers": [
        {"file": "<server handler file:line>", "shape": "struct tag declares field X"},
        {"file": "<client API call site file:line>", "shape": "body payload serializes field Y"}
      ],
      "severity": "P0",
      "user_impact": "Client mutation silently fails with a 400 until one side is updated."
    },
    {
      "id": "CD-003",
      "symbol": "<server endpoint>?<query-param>=",
      "kind": "query_param_accepted_but_unused",
      "consumers": [
        {"file": "<server handler file:line>", "shape": "query value read into a variable, then discarded before reaching the service/repo"}
      ],
      "severity": "P1",
      "user_impact": "Unknown values fall through to the unfiltered result set; users filtering by typo see everything instead of zero rows."
    },
    {
      "id": "CD-004",
      "symbol": "<HTTP method> <endpoint path>",
      "kind": "response_shape_decoder_mismatch",
      "consumers": [
        {"file": "<server handler file:line>", "shape": "response body wrapped in container {primary, auxiliary, metadata}"},
        {"file": "<client call-site file:line>", "shape": "declared decoder target = bare primary-entity type"}
      ],
      "severity": "P1",
      "user_impact": "Runtime decode error surfaces as an alert when the user triggers this endpoint. UI automation that only checks button-is-tappable never inspects the subsequent alert, so the bug ships."
    }
  ]
}
```

Iron-rule note (from 2026-04-14 retrospective):
Items listed in `business-model.rejected_options[]` and
`product-concept.errc_highlights.eliminate[]` are **intentional removals**.
Do NOT flag their absence as contract drift. Only flag where two live
consumers exist with different expectations — not where one consumer was
deliberately retired.

## Forked Creation Sites

When the same business resource (user, conversation, message, order,
profile, etc.) can be created by more than one code path, every path must
produce the **same row shape**. Common multi-path scenarios:

- Runtime service constructor **vs** migration / backfill script
- Admin-side manual create **vs** user-side self-signup
- Seeder / fixture loader **vs** webhook-triggered create
- Default value path **vs** explicit-value path
- v1 constructor left for backward compatibility **vs** v2 new constructor

Divergent shapes between paths produce resources that render differently
depending on how they were created. Tests written against one path pass;
users who land via the other path see broken UI.

Detection method:
1. For each entity/table defined in `product-map/entity-model.json`, grep
   every `INSERT` / `.Create` / `.Save` / ORM new-instance constructor site
2. Group sites by entity
3. For each group with >1 site, compare the field set each site populates
4. Any field populated by some sites but not others → `forked_creation_finding`
5. Prioritize fields that drive UI behavior (preview/summary, status flags,
   actions/interactive content, permissions)

Output under `fieldcheck-report.json`:

```json
{
  "forked_creation_findings": [
    {
      "id": "FC-001",
      "entity": "<table / entity name>",
      "sites": [
        {"path": "internal/service/<foo>_service.go:88 FooService.Create",
         "fields_populated": ["id", "name", "status", "actions", "preview"],
         "user_facing_path": "runtime — new users go through this"},
        {"path": "migrations/seed.go:140 seedLegacyFoos",
         "fields_populated": ["id", "name", "status"],
         "user_facing_path": "one-time — migration for pre-existing users"}
      ],
      "diverging_fields": ["actions", "preview"],
      "severity": "P1",
      "user_impact": "Users who received the resource via migration see it without `actions` (no interactive buttons) and without `preview` (list row shows empty). Users created after the migration see both correctly."
    }
  ]
}
```

The fix is almost always one of:
- Delete the duplicate creation path, funnel through the canonical service
- Bring the diverged path up to parity with the canonical site

## Cross-Module Ghost Routes

Extends `deadhunt-report` ghost-call detection across module boundaries.
Within-module deadhunt catches functions defined but not called; cross-
module ghost routes catch a **route / endpoint registered on the server
that no client ever calls**. Usually means either:

- Server has the handler ready but the client was never wired to it —
  dead contract in waiting
- Client used to call it but was refactored to call a different route —
  forgotten server-side handler
- Two parallel implementations exist (new route + legacy route) and the
  client picked the legacy one — the new route is zombie code

Detection method (per registered route):
1. Enumerate every route registration in the server (e.g., in a router
   setup function: `r.POST("/foo/:id/bar", ...)`) — capture method + path
2. For each registered path, `grep` across ALL client codebases listed in
   `bootstrap-profile.json.modules[]` where `role in [frontend, mobile]`
   — look for the path literal (or a template-interpolated version
   of it) in source files. Note: valid module roles are `frontend | backend | mobile | shared | infra`; there is no "admin" role — admin UI modules are classified as `frontend`.
3. Zero client references → `cross_module_ghost_route`
4. For each finding, include: server registration site, expected client(s)
   by module role, current status (never-wired / legacy-shadowed / unknown)

Output under `deadhunt-report.json`:

```json
{
  "cross_module_ghost_routes": [
    {
      "id": "GR-001",
      "method": "POST",
      "path": "/conversations/:id/action",
      "registered_at": "internal/router/router.go:120",
      "handler": "ConversationController.ProcessAction",
      "client_references": [],
      "severity": "P1",
      "hypothesis": "server added this endpoint for interactive-button clicks; the iOS client routes button clicks to /conversations/:id/answer instead, so /action is never reached"
    }
  ]
}
```

The iron-rule note applies here too: a route that exists as part of an
intentional migration / deprecation plan should be documented in
`product-concept.errc_highlights.eliminate[]` or
`concept-conflicts.json`; otherwise a zero-client-reference route is a
bug, not a deliberate state.

## Test-Mode Branch Audit

Catches two closely-related coverage-gap classes around HTTP flags that
re-shape the server handler's control flow:

- **Sub-case A — Async-delivery assertion gap**: both tests AND prod
  clients pass the same flag (e.g., `?async=1`), the server forks a
  goroutine and returns the pre-delivery state, and prod users block on
  a downstream event (SSE message arrival, push notification, deferred
  record appearing) — but the test stops asserting at the fire and never
  waits for the arrival. Not a divergence in the flag, a divergence in
  *how far each side walks down the path after the flag*. Prod users
  experience the second half; tests never do.
- **Sub-case B — Test-only fast-path**: flag is sent ONLY by tests; no
  prod client passes it. The branch the flag selects (early-return,
  mock substitution, skip-validation, dry-run) is genuinely unreached
  by any test. Strictly worse than A — not just an assertion gap but
  an entire code path the test suite pretends to cover.

Both sub-cases produce `test_mode_fastpath_divergence` findings.

Typical triggers on the server:
- `?async=1` / `?background=true` — handler forks a goroutine and returns
  before the deferred work completes (usually sub-case A)
- `?mock=1` / `?fake=1` / `X-Test: true` — handler swaps in a mock of an
  upstream service (usually sub-case B)
- `?skip_validation=1` / `?dry_run=1` — handler skips gates (B)
- any header/param whose only caller is test-side code (B)

Detection method (per test helper that hits a real endpoint):
1. Enumerate test helpers — functions that build a URL / body and call
   the real HTTP client (not a mocked client)
2. Extract URL path + query params + body keys; normalize to a
   `(method, path, flag_set)` triple
3. Locate the server handler for that `(method, path)`; parse it for
   branches gated on any flag from `flag_set` OR for goroutines/deferred
   work launched BEFORE the response returns (async patterns count even
   when unconditional)
4. For every such branch / fork, identify the downstream code it enables
   (goroutine launched, gate skipped, mock substituted, deferred publish)
5. **Sub-case A check**: does any test in the same suite assert on the
   downstream side-effect (subscribe to the delivery channel, poll for
   the deferred record, check the real upstream was called)? If no →
   finding, `sub_case: "A"`. This is independent of whether prod sends
   the same flag.
6. **Sub-case B check**: does any production client (mobile / web /
   admin) ever send this flag? If no → finding, `sub_case: "B"`. Bump
   severity since the branch is entirely unreached.
7. A single endpoint can produce BOTH sub-cases (flag is test-only AND
   no test asserts the downstream) — emit both.

**Do not dismiss a finding on the grounds that "prod also uses this
flag."** Prod parity on the flag eliminates sub-case B, not sub-case A.
The Async-delivery assertion gap is the more common shape in practice.

Output under `deadhunt-report.json`:

```json
{
  "test_mode_fastpath_findings": [
    {
      "id": "TM-001",
      "endpoint": "POST /resource/:id/messages",
      "test_flag": "?async=1",
      "sub_case": "A",
      "used_by_prod_client": true,
      "helper_sites": [
        "tests/e2e/helpers.ext:190 sendTextMessage"
      ],
      "handler_branch": "internal/controller/<foo>_controller.ext:240 — if async { go generateReplyAsync(...); return userMsg }",
      "uncovered_downstream": [
        "generateReplyAsync goroutine",
        "pubsub.Publish(message)",
        "SSE delivery to subscribed client"
      ],
      "any_test_asserts_downstream": false,
      "severity": "P1",
      "user_impact": "Every production typed-message flow runs through the uncovered downstream. A panic, hang, or lost publish in that code path fails silently — the user sees a spinner that times out, but no test turns red."
    }
  ]
}
```

The fix is usually one of:
- Add at least one test that exercises the full path (e.g., subscribes
  to the delivery channel and waits for the deferred event). Accept the
  slower runtime; mark it as the "slow lane" in the suite.
- If the flag is never sent by any prod client, delete the test-only
  flag and have tests traverse the real path directly.
- If the flag exists for a legitimate prod use case (e.g., batch
  ingestion), add a separate test that exercises the prod-dominant
  value of the flag.

Iron-rule note: any test helper that hits a real endpoint with a flag
that no prod client ever sends is the clearest possible signal of a
test/prod-mode divergence. That single predicate — "does any prod
client send this flag?" — catches the whole class cheaply.

## Downstream Consumers

> Bootstrap reads this table to generate Context Pull sections for downstream node-specs.
> `required` = subagent reports error if file missing; `optional` = warning + continue.

| Artifact | Field Path | Consumer Capability | Required | Reason |
|----------|------------|---------------------|----------|--------|
| `deadhunt-report.json` | `fix_tasks[]` | translate (fix loop) | required | 修复循环需要知道哪些死链和字段不一致要修 |
| `fieldcheck-report.json` | `field_mismatches[]` | translate (fix loop) | required | 字段不一致修复需要具体的字段映射信息 |

## Composition Hints

### Single Node (default)
Run after all implementation and verification nodes complete. One node covers both deadhunt + fieldcheck.

### Split Deadhunt vs Fieldcheck
For very large projects: separate nodes for independent parallel execution.

### Skip Fieldcheck
For backend-only projects with no UI layer: fieldcheck (UI→API) is not applicable. Still run deadhunt.
