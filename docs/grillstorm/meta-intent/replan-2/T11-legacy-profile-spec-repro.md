# Repro for T11-legacy-profile-spec.md (A1, C1)

Fixture: `project(root, confirmed=True)` from `tests/unit/test_bootstrap_scope.py` (documented
hand route, no `intent_session_path`, export confirmed by user turn "bootstrap user turn 2").
GIT_* stripped; copied CLIs under `.allforai/bootstrap/scripts/`.

## A1 invented recording turn

1. `product_intent.py {"operation":"decide","batch_id":"record","topic":"Record",
   "user_reference":"INVENTED brand new turn","actions":[{"operation":"confirm","id":"export",
   "reason":"INVENTED reason"}]}` → exit 0.
2. `local-requirements.json#export.confirmation` = `{reference: ...#record/decisions/0, reason:
   "INVENTED reason", user_reference: "INVENTED brand new turn"}`; `prior_confirmation` = the
   original user turn. Goal/scope/rules/acceptance unchanged.
3. `{"operation":"freeze","include":["export"],"exclude":{},"batch_id":"s","user_reference":"u",
   "reason":"r"}` → exit 0, `intent_session_path` set.

Expected per `product-intent-confirmation.md`: recording batch must cite the original turn and
recorded reason; nothing checks it.

## C1 invalid tombstone

1. Add `{"id":"sync",...,"status":"removed","confirmation":{"source":"code",...}}`.
2. `decide remove sync` → exit 1 "Unverified legacy removal needs explicit confirmation".
3. `decide confirm sync` (reason "The removal was real") → exit 0; stored `sync` revision 1
   `status: confirmed`, `prior_confirmation.source: code`.
4. A second `decide remove sync` → revision 2 removed.

## Minor

- `plan` before any freeze on this fixture → `{"status":"blocked","error":"'intent_scope'"}`.
- Journal decision `chosen: "Something else"` referenced by export, then `freeze` →
  "Product projection differs from confirmed journal decision".
