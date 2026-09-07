# T10 independent spec recheck

**PASS — both previous blockers fixed; no new bounded spec findings.**

Reviewed only corrective diff `b5c66303ce62618bd587ffa0ec705b8af61a6336...3f66d7acc367cdb39ee12ae10827c8d81298ae0a` (one commit), revised `issues/10.md`, parent `sources/issue-8.json`, and my prior `T10-spec-review.md`. Other-axis reports were not read. Production HEAD remained the requested `3f66d7acc367cdb39ee12ae10827c8d81298ae0a`; production files and coordinator-owned documents were untouched.

1. **Question identity blocker resolved.** Requirement: “未决问题不能通过沉默自动确认，排除范围必须显式决定.” The shared validator rejects question/intent aliases and duplicate question identities before draft/decision persistence, at session entry for persisted inputs, and in the product contract consumed by public gates. Generated gap collisions and newly added intent collisions are covered. Independent temporary-fixture probes additionally injected both an unanswered intent alias and duplicate persisted questions into otherwise valid plans: each adapter's copied session rejected planning without mutation, and all three gates rejected both cases. No unanswered question became approved scope through identity coverage.

2. **Retained-work blocker resolved.** Parent requirement: “preserve unaffected results with their provenance.” Planning now applies the same retained-completion classification as validation, preserves historical node fields and existing Node-spec bytes, and leaves evidence intact. Tests exercise absent, empty and historical references, supplied historical briefs, and native completion formats. New unapproved nodes, reopened nodes, and completed current-scope nodes with invalid acceptance/intent remain rejected. My independent mixed-format failed→completed history probe passed planning and all three gates on both adapters while preserving historical Node-spec, evidence and product-code bytes. This consumes supplied reconciled history; it does not establish future reconciliation correctness.

Validation: **50 passed** across `test_product_question_identity.py`, `test_product_retained_scope.py`, and `test_product_intent_session.py`, plus the independent copied-CLI probes above. Gates exercised: `validate_bootstrap.py`, `check_decision_inputs.py`, and `validate_unattended_readiness.py`. Temporary independent fixtures were removed.

No missing behavior, incorrect behavior, or scope creep found in this correction. Tickets #11–18 and actual-host dialogue/semantic proofs remain outside this review; scripted adapter tests do not claim those proofs.
