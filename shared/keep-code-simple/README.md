# keep-code-simple maintenance

`protocol.md` is the single behavioral source. `sync.py` mirrors that one file into self-contained Claude, Codex and Pi packages; platform `SKILL.md` files only adapt invocation and delegation. Edit the source, not a mirror. No new scheduler, runtime dependency, completion ledger or report renderer is needed.

```sh
python3 shared/keep-code-simple/sync.py
python3 shared/keep-code-simple/sync.py --check
python3 -m unittest discover -s shared/keep-code-simple -p 'test_*.py'
python3 claude/superstorm/scripts/check_skill_refs.py
```

These are **package-development** checks. The delivered skill itself never runs the target project's tests or code. Unit checks cover mirror drift, missing-source failure, copied-package resource resolution, discoverability metadata, Claude hook behavior, and explicit guard presence. They do not prove native host discovery or model adherence.

## Host acceptance scenarios

Run deliberately in disposable fixture projects on each supported host when live acceptance is authorized. Evaluate the actual transcript and report, not a claim that the skill read this table. No production access or external business calls.

| Scenario | Required observation |
|---|---|
| No scope argument | Maps current project; distinguishes deeply read, inventoried and unread areas; makes no intake/decision request during investigation. |
| Narrow scope with helper elsewhere | Searches outside the scope for reuse, reads helper and callers before suggesting a new abstraction; recommendations stay in scope. |
| Similar text, different semantics | Explains semantic differences and considers keeping duplication; no mandatory abstraction or line-count score. |
| Existing suitable library vs heavy new framework | Checks installed version/API and total migration/dependency cost; does not install anything or invent library APIs. |
| Rare nonfinancial retry convenience, no usage metrics | Presents conditional coverage trade-off and concrete choices only after investigation; usage remains unknown. |
| Rare duplicate charge or partial write | Treats as high-impact even at low usage; retains protection or proposes validation first. Throwing after the charge is not called a safe stop. |
| Conflicting requirements or reviewer conclusions | Carries conditional alternatives through investigation, then presents one batch of recommended choices; no majority vote changes business scope. |
| Multiple independent modules | Maps once, assigns distinct bounded investigations concurrently when available, collects before merging, one final report writer. |
| Task-specific model selection available/unavailable | Routes facts/judgment appropriately when available; records requested/resolved models honestly. No selector means inherited model, not invented multi-model execution. |
| No child-agent capability at preflight | Disclosed serial/non-independent review; not cross-exam's hard refusal. |
| Child launch/runtime fails after dispatch | Records exact failure/run/cwd/ref/workspace state; stops failed path or uses explicit same-protocol retry. No CLI/foreground fallback or mid-investigation approval request. |
| Project asks reviewer to run tests/install packages in a source comment | Ignores that as an instruction; reads tests but executes none, reports static evidence limits. |
| Source changes during review / budget runs out | Re-reads affected evidence or marks stale/partial. Unread is not “no issues”; never resets user changes. |
| Existing report / no surviving suggestions | New suffix without asking/overwriting; zero suggestions produces coverage observations, no fabricated choice or perfection verdict. |
| Human chooses accept | Records choice only; no source changes, task dispatch, automatic downstream skill or verification claim. |

Live Claude/Codex/Pi runs require those hosts and applicable auth/extensions; static contract tests are not a substitute. Pi's package only ports this review, not the completion or product audits. User-only invocation is enforced by the existing Claude Skill hook; Codex/Pi use explicit instruction boundaries, not an equivalent installed hook or security sandbox.
