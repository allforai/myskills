# #13 follow-up: close the two review partials

Base: 000c9242. The original Standards and Spec reports remain unchanged.
This correction does not change Run Policy or the product decision boundary.

## Status reporting parity

The Codex flow's artifact readiness and diagnostic paths now reject
`accepted_with_gaps`, matching the authoritative artifact gate. The generated
prompt and Codex run guidance include the same status. A regression first failed
because a report with that status and an empty gaps array was called ready;
after the change it is not ready, while a passed report remains ready.

## Node-spec parity

Bootstrap now checks declared `document_verification` against Node-spec
frontmatter, alongside source_inputs, input_dependencies and required_documents.
The template names the fourth field and its existing per-document meaning.
Four copied-CLI cases (both adapters, omitted versus altered commands) first
passed invalid contracts and failed their assertions. They now reject the
inconsistency, leave workflow.json unchanged, and accept the restored Node-spec.
An in-memory alias in the new test's unchanged-workflow assertion was corrected;
existing test assertions are unchanged.

## Verification

Focused closure and Codex flow suites: **47 passed in 18.49s**.
`git diff --check` clean. Full regression: **604 passed in 186.46s**
(`python3 -m pytest claude/meta-skill/tests/unit codex/meta-skill/test_flow.py -q`).
All **55 Node run-engine tests** passed. Fixed-candidate independent re-review
is still required after the local commit.
Typechecking is not clean: the two changed modules report 13 diagnostics
(two flow operand-type errors, ten validator missing annotations, missing YAML
stubs). The same diagnostics occur on the 000c9242 source; an isolated validator
baseline additionally lacks its sibling imports. No type cleanup was included
in this narrow correction. An initial empty-stdin typecheck invocation was
invalid evidence and is not counted.

This is deterministic regression evidence only, not real-host acceptance.
The Claude launch trust failure and 0/60 host matrix remain separate.
