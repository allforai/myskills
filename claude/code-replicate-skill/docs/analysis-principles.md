# Source Analysis Principles

> Generic principles for LLM-driven source code analysis during Phase 2b. Framework-agnostic — applies to any codebase.

---

## 1. Identifying Modules

A module is a cohesive unit of code with a clear responsibility boundary.

**Signals to look for:**
- Directories that group related files (controllers + services + models under one folder)
- Shared naming prefixes (`user.controller`, `user.service`, `user.model`)
- Internal imports that stay within the directory; external imports that cross directories
- A barrel/index file re-exporting public interfaces

**Boundary heuristics:**
- If two directories never import each other, they are likely independent modules
- If directory A imports directory B but not vice versa, B is a dependency of A
- If two directories have circular imports, they may be a single module or need refactoring

**Confidence levels:**
- `high` — clear directory boundary + cohesive naming + limited external surface
- `medium` — directory grouping exists but responsibilities overlap with another module
- `low` — flat file structure, responsibility inferred from naming alone

---

## 2. Identifying Entry Points

Entry points are where external requests first hit the codebase.

**What to look for:**
- Main/bootstrap files (`main.ts`, `app.py`, `main.go`, `index.js`)
- Router/route registration files — where URL paths are bound to handlers
- App configuration files that wire middleware, plugins, and modules together
- CLI entry points (`if __name__ == "__main__"`, cobra commands)
- Event listeners / queue consumers (secondary entry points)

**Prioritization:**
- HTTP route handlers are primary entry points for web applications
- Background workers / cron jobs are secondary entry points
- Internal module initializers are NOT entry points — they are wiring

---

## 3. Tracing Data Flow

Follow the request lifecycle from entry to persistence and back.

**Standard flow pattern:**
```
Entry (route/handler)
  → Input validation / deserialization
    → Business logic (service layer)
      → Data access (repository / ORM / raw query)
        → External calls (APIs, queues, caches)
      ← Response construction
    ← Error handling / exception mapping
  ← Serialization / response formatting
← Response sent
```

**Tracing strategy:**
1. Start at the route handler — identify the service/function it calls
2. Follow the service function — identify data sources it reads/writes
3. Note transformations — where data changes shape (DTO → entity → response)
4. Track side effects — anything that writes outside the main flow (logs, events, queues, emails)
5. Identify the return path — how the result is packaged and sent back

**Watch for:**
- Middleware that modifies request/response before/after the handler
- Decorator/annotation patterns that inject behavior (auth, caching, logging)
- Implicit data flow through shared state (global variables, singletons, context objects)

---

## 4. Extracting Business Rules

Business rules are the domain logic that distinguishes this application from a generic CRUD app.

**Where rules live:**
- Validation logic — constraints beyond type checking (e.g., "quantity must be positive", "email must be unique")
- Conditional branches — `if/else` and `switch` statements in service layers
- Error handling — what triggers specific error codes (409 Conflict, 422 Unprocessable)
- Guard clauses — early returns that enforce preconditions
- Computed fields — derived values (total = price * quantity - discount)

**Extraction approach:**
1. In each service function, list every condition that affects the outcome
2. For each condition, note: trigger, effect, and whether it's enforced in code, DB, or both
3. Distinguish hard rules (always enforced) from soft rules (configurable / feature-flagged)
4. Mark rules without test coverage as `[UNTESTED]`

**Common hiding spots:**
- Database constraints (unique indexes, foreign keys, check constraints)
- ORM model hooks (beforeSave, afterCreate)
- Middleware that silently transforms data (trim whitespace, normalize case)

---

## 5. Identifying Roles and Permissions

Roles define who can do what. They appear as access control checks throughout the codebase.

**Signals to look for:**
- Auth middleware / guards applied to routes or controllers
- Role checks in handlers (`if user.role !== 'admin'`)
- Permission decorators (`@Roles('admin')`, `@RequirePermission('write')`)
- Route-level access control lists (ACL configuration files)
- Frontend route guards that check user roles before rendering

**Extraction approach:**
1. List all distinct role names found in code (admin, user, manager, etc.)
2. Map each route/endpoint to its required role(s)
3. Identify the authorization model: RBAC, ABAC, simple role check, or custom
4. Note routes with NO auth check — they are public endpoints (intentional or oversight)

---

## 6. Inferring Cross-Cutting Concerns

Cross-cutting concerns are behaviors applied across multiple modules without being part of any single module's core logic.

**Common patterns:**
- **Middleware / Interceptors** — request logging, error formatting, CORS, rate limiting
- **Decorators / Annotations** — caching, auth, transaction management
- **Base classes / Mixins** — shared behavior inherited by multiple services or controllers
- **Event systems** — publish/subscribe patterns that decouple modules
- **Aspect-oriented patterns** — before/after hooks, proxy wrappers

**Detection strategy:**
1. Look at the middleware registration chain in the app bootstrap
2. Search for decorators/annotations used across multiple modules
3. Identify base classes that multiple services extend
4. Check for event emitters/listeners and their subscribers
5. Note any "utility" or "common" directories — they often contain cross-cutting logic

**Documentation approach:**
- For each concern, record: what it does, how it's applied, which modules it affects
- Distinguish framework-provided concerns (built-in auth guard) from custom ones (hand-written rate limiter)
- These become `cross_cutting` entries in `source-summary.json`

---

## 7. Identifying User-Perceivable Capabilities

User-perceivable capabilities are features that end users directly interact with or notice. They sit at the boundary between "business intent" (must extract) and "implementation decision" (replaceable).

**The Disappearance Test:**

> "If this capability vanishes from the target application, would an end user notice during normal usage?"
> - Would notice → **user feature** (must extract to task-inventory / experience-map)
> - Would not notice → **implementation detail** (replaceable, record in stack-mapping)

**Reasoning examples:**

| Capability | Disappearance Test | Classification |
|------------|-------------------|---------------|
| Drag file to chat window to send | User could do it before, can't now → notices | User feature |
| Emoji picker popup | User could pick emojis, now can't → notices | User feature |
| Clipboard paste image (Ctrl+V) | Ctrl+V sent screenshots before, doesn't now → notices | User feature |
| Voice recording and playback | User could send/receive voice, now can't → notices | User feature |
| Fullscreen image preview on tap | User could tap to enlarge, now can't → notices | User feature |
| Long-press context menu (6 options) | User had 6 actions, now has 2 → notices 4 missing | Each option = user feature |
| BLoC vs Provider state management | Same UX either way → doesn't notice | Implementation detail |
| GridView vs ListView rendering | Same data and interaction → doesn't notice | Implementation detail |
| flutter_sound vs just_audio library | Same record/play UX → doesn't notice | Implementation detail |

**Three-Layer Model** (reasoning aid, not rigid classification):

1. **User Capability Layer** (What + How user triggers it)
   - Must extract to task-inventory and/or experience-map interaction_triggers
   - Examples: send voice message, fullscreen preview, drag-sort list items, paste image from clipboard

2. **Interaction Implementation Layer** (Which library/component implements it)
   - Record in stack-mapping.json, replaceable in target with equivalent
   - Examples: flutter_sound vs just_audio, Hero animation vs custom transition, native file picker vs web API

3. **Code Structure Layer** (Code patterns and architecture)
   - Do not copy — target ecosystem conventions apply
   - Examples: BLoC vs MVVM, single-file components vs split, mixin vs inheritance, dependency injection style

**Boundary disambiguation — the "apology test":**

> When unsure whether something is a user feature or implementation detail, apply:
> "If this capability disappears from the release, would we need to apologize to users in release notes?"
> - Yes → user feature (extract it)
> - Only developers would notice in code review → implementation detail (skip it)

**Application to extraction-plan:**
- For each screen_source and task_source, LLM should trace not just the main handler but also event bindings (onTap, onClick, onDrag, onPaste, onKeyDown, onLongPress, etc.)
- Each distinct user trigger that produces a user-visible response = one capability to extract
- Enum/switch rendering branches where each case produces distinct user-visible behavior should be extracted individually, not collapsed into a single component

---

## 8. Identifying Embedded Runtimes and Platform Capabilities

Some applications contain sub-platforms that provide a runtime environment for third-party code (mini program engines, plugin systems, script engines, embedded browsers, custom DSL interpreters).

**Detection signals:**
- Sandboxed execution environments with their own lifecycle management
- Bridge/channel APIs between host app and embedded code
- Permission systems governing what embedded code can access
- Independent navigation stacks, storage, or UI frameworks within the host app

**Extraction approach:**
- Record the runtime as a whole in infrastructure-profile with `cannot_substitute: true`
- **Do NOT** extract screens/tasks from the runtime's internal implementation (it is platform infrastructure, not business logic)
- **DO** extract the **host-to-runtime interface** as tasks in task-inventory: "launch embedded app", "embedded app invokes payment", "share from embedded app to chat", etc. — these are user-perceivable capabilities
- In extraction-plan, mark the runtime's internal code as `skip_extraction: true, reason: "embedded_runtime"`
- Record the runtime's capabilities (APIs it exposes to embedded code) in infrastructure-profile for the target to replicate

**The disappearance test still applies** — "if the embedded runtime disappears, users notice" — but the extraction target is the **interface**, not the **internals**.
