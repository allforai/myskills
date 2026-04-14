# Bootstrap Blind Spots — Global Template

This file documents classes of bugs that past bootstrap runs missed across
projects, and the capabilities added to prevent each class. Bootstrap Step
2.4.1 loads this file so every new workflow inherits the lessons.

Entries remain even after the preventing capability ships — `status:
closed` is valuable audit history for "how we learned to check this."

## Schema

```markdown
## <YYYY-MM-DD> — <short bug class name>

- **Class**: short name for the category of bug
- **Missed**: concrete instance (which project, which symbol)
- **Why missed**: which node was expected to catch + what it actually did
- **Minimum prevention**: smallest additional check that would catch it
- **Capability added**: which capability file in `knowledge/capabilities/`
  implements the prevention (may reference a new capability)
- **Status**: `open` (no fix yet) / `scheduled` (capability exists but
  not yet auto-added to workflows) / `closed` (capability ships, auto-
  added to relevant goals)
- **First reported in**: project / session identifier
```

Each entry should be brief — 10-15 lines. For the full story, link out to
the project-local `.allforai/bootstrap/learned/blind-spots.md`.

---

## 2026-04-14 — Env-var dual-contract

- **Class**: runtime contract parity between two consumers of the same
  environment variable
- **Missed**: FlyDict iOS project. `UITEST_API_BASE_URL` was read as a
  bare host by XCUITest (tests prepend `/api/v1/...`) and as a full URL
  including `/api/v1` by `FlyDictApp.swift` via `APIClient.setBaseURL`.
  Manual app launch with `http://localhost:9600` showed 404 login
  screen; all 47 XCUITest cases passed.
- **Why missed**: product-verify-ios runs XCUITest exclusively, so only
  the tests-side contract is exercised. pipeline-closure-verify does
  static cross-layer checks only. quality-checks hunted dead-code /
  ghost-calls, not contract-shape drift.
- **Minimum prevention**: `runtime-smoke-verify` capability — launch
  each artifact outside any test harness with prod-like env, hit the
  first API call, verify 2xx (or expected 4xx for auth).
  Additionally: `quality-checks` contract-parity scan enumerates all
  consumers of any env var and flags shape disagreements.
- **Capability added**: `knowledge/capabilities/runtime-smoke-verify.md`
  + `knowledge/capabilities/quality-checks.md` Contract-Parity section
- **Status**: `closed` — `runtime-smoke-verify` auto-added to all
  goals that include code implementation or launch-prep (see
  `skills/bootstrap.md` Step 1.5 goal mapping). Contract-Parity check
  runs as part of every quality-checks invocation.
- **First reported in**: FlyDict project, 2026-04-14 session

## 2026-04-14 — State-machine transition wired to the wrong event

- **Class**: event-driven state change bound to an event users rarely trigger
- **Missed**: FlyDict `ConversationService.updateStreak` fired from the
  conversation-end path (generateQuiz + extractVocabulary side-effect).
  Messenger-style users don't click "end conversation", so streak never
  advanced in practice. Rule was correct; event binding was wrong.
- **Why missed**: Coverage measured "is rule implemented" rather than
  "does rule fire in the user's real flow." E2E test that sent one
  message and then queried /profile/streak caught this in the first
  reverse-regression round.
- **Minimum prevention**: for every state-machine transition declared
  in product-concept `adaptive_systems[]`, pipeline-closure-verify
  must trace from "user-facing trigger" (send message, complete
  scenario) to "state-change call-site" and fail if the call-site is
  on a path users don't routinely traverse.
- **Capability added**: pipeline-closure-verify extended with "state
  transition trigger-path trace" (TODO — currently `open` status)
- **Status**: `open` — preventing check not yet implemented
- **First reported in**: FlyDict project, 2026-04-14 session

## 2026-04-14 — Path disconnect between rendering surfaces

- **Class**: single entity shown in multiple UI surfaces; mutation refreshes
  surface A but not surface B
- **Missed**: a domain object appears as both an inline item inside a detail
  view and a summary row inside a list view. Tests covered one surface
  (detail looks fine) but not the other (list row shows a stale placeholder
  or empty summary). Manually opening the list was enough to catch it in
  seconds; no automated check noticed.
- **Why missed**: product-verify was scoped per-screen, and the screen that
  renders the detail was green. The list screen's summary field was
  populated by a separate code path that had an ordering bug
  (UPDATE-before-INSERT). That bug was invisible to any single-surface test.
- **Minimum prevention**: `pipeline-closure-verify` Check Dimension 5
  (Multi-Surface Consistency) — for every entity declared in
  product-map entity-model, enumerate all UI surfaces that render any of
  its fields; assert every mutation path refreshes every rendering surface.
- **Capability added**: `knowledge/capabilities/pipeline-closure-verify.md`
  §5. Multi-Surface Consistency
- **Status**: `closed`
- **First reported in**: FlyDict project, 2026-04-14 session

## 2026-04-14 — Forked creation paths produce diverging row shapes

- **Class**: the same business resource can be created by ≥2 code paths and
  those paths populate different field subsets. The resource renders
  correctly for users who arrived via one path and incorrectly for users
  who arrived via the other.
- **Missed**: migration / backfill script and runtime service both
  instantiate the same entity but the migration path omits fields that the
  runtime service always populates. Tests exercise only the runtime path
  (fresh users) and never the migration path (pre-existing users being
  upgraded). Pre-existing users see a silently-broken state.
- **Why missed**: fixture-based test data always uses fresh registrations
  via the canonical service. The migration path exists solely for
  production deploys touching real users and is never exercised by test.
- **Minimum prevention**: `quality-checks` Forked Creation Sites scan —
  for every entity in entity-model, enumerate every INSERT / Create /
  Save call site; flag diverging field sets, especially fields driving UI
  (preview / actions / status / permissions).
- **Capability added**: `knowledge/capabilities/quality-checks.md` §Forked
  Creation Sites
- **Status**: `closed`
- **First reported in**: FlyDict project, 2026-04-14 session

## 2026-04-14 — Server route with zero client callers (cross-module ghost)

- **Class**: HTTP route registered on the backend, intended for a client
  action, but the client routes that action to a different (legacy)
  endpoint — the registered route is dead contract.
- **Missed**: server adds `POST /resource/:id/action` for interactive
  button clicks; iOS codebase has no reference to that path anywhere and
  routes button clicks to an older `POST /resource/:id/answer` endpoint
  that doesn't accept the new semantic type. User taps button → 400 error.
- **Why missed**: within-module deadhunt finds functions-without-callers
  inside one codebase; it doesn't cross repo boundaries. No existing check
  grepped every registered server route against every client codebase for
  at least one caller.
- **Minimum prevention**: `quality-checks` Cross-Module Ghost Routes —
  enumerate every `r.POST/GET/PUT/...` in the router and grep the exact
  path across all client modules; zero matches ≥ P1.
- **Capability added**: `knowledge/capabilities/quality-checks.md` §Cross-
  Module Ghost Routes
- **Status**: `closed`
- **First reported in**: FlyDict project, 2026-04-14 session
