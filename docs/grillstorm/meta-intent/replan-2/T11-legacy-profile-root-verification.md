# Root verification of C1-prime legacy-profile correction

Base: `ed430dfcebed485b913b54d7785f02cc86998303`. Worker
`ctx_8ae581fcb4a6` settled and was released before root took ownership. Its report
is preserved separately; this report records the additional root correction.

Initial root verification of the handed-over candidate: all 577 meta-skill
Python tests passed in 162.19s; 55 Node engine tests passed; typechecking
`product_intent.py`, `evidence_freshness.py`, and `check_artifacts.py` passed.

Root then extended the mixed legacy transition test through an ordinary
`confirm` of a removed, explicitly excluded user-turn item **after freeze**.
Both adapters failed the new assertion: the session-marker change made the
old removal fail canonical provenance validation and `confirm` overwrote its
removed status with confirmed. The existing resume-only assertion missed this.

Minimal correction: before applying a non-restore operation to a removed item,
reuse the verified discussion's current exclusion set and reject attempts to
revive a frozen-excluded removal. Explicit restore remains the entry to revive
it. The test also asserts that the rejected confirmation leaves every file
unchanged. Protocol wording now distinguishes a genuinely confirmed removal
from an unverified legacy tombstone, rather than incorrectly claiming the
existing invalid-provenance recovery has identical semantics.

Red: 2 failed / 18 deselected in 1.17s. Green: all 20 legacy-profile cases passed
in 8.35s. Three core-file typechecks and `git diff --check` passed again.
Final combined regression:
`python3 -m pytest claude/meta-skill/tests/unit codex/meta-skill/test_flow.py -q`
passed **601 tests in 165.89s**. Independent Standards and Spec review of a
fixed committed candidate remains required.

These tests exercise copied public CLIs, not real host conversations. Actual
Claude/Codex scenario evidence remains 0/60. No push, main merge, installation,
or issue closure is part of this verification.
