# Root verification of document-sync closure

Worker candidate: `e79db1e811b07276ffaddeb0a05a2977719bc65f` atop `705ec156`.
Worker `ctx_a8e7d8ab1885` settled and was released before root verification.

Root combined command:
`python3 -m pytest claude/meta-skill/tests/unit codex/meta-skill/test_flow.py -q`
reported **1 failed, 598 passed in 178.85s**. The failing existing test was
`test_resume_runs_real_validation_commands`: a legacy target copies only the
standalone artifact gate, has no freshness state or dynamic-read register, and
must still honor actual exit-artifact validation commands on resume. The new
all-legacy corrupt-register check unconditionally imported `evidence_freshness`,
so this target could never finish even after its real verifier returned success.

Root correction keeps the pre-freshness short circuit when that register does
not exist. A present register still undergoes the new validation; corruption is
not ignored or deleted. No existing test was weakened or supplied extra helpers
to conceal the compatibility regression.

Red: the existing Codex-flow test failed in the combined run. Green after the
four-line correction: all 42 Codex-flow and delivery-closure cases passed in
16.15s, including the corrupt-register negative and substantive document/source
checks. Three core-file typechecks passed again; diff check clean. Node engine
tests on the candidate: 55 passed. The commit hook will rerun the full meta-skill
unit suite; independent Standards/Spec review must use the corrected candidate,
not the superseded `e79db1e8` alone.

Verification substance is still project-specific and host-supplied; these
automated tests do not prove a real Claude/Codex session will select a meaningful
checker. Actual host evidence remains **0/60**. No main merge, push, installation,
or issue closure occurred.
