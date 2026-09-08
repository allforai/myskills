# #12 implementation acceptance

Accepted producer: `ed430dfcebed485b913b54d7785f02cc86998303`.
Integrated without production differences at `be73f8f18ea12c68e1954f9f0fa3c12c547b025d`.
Pinned main context remains `a37ca40a`; later main changes are not silently mixed in.

Evidence: root 581 Python tests, 55 Node tests, three core-file typechecks; commit
hook 557 unit tests and bundled/protocol validators passed. Independent Standards
final reports no hard/soft breaches or nits. Independent Spec final accepts #12's
freshness fixes, A1 idempotence and C2 structured corrupt-read handling. Reports
are preserved verbatim beside this record; optional smells were not promoted to
requirements.

One non-blocking note remains: an all-legacy workflow without freshness STATE
can short-circuit before inspecting a corrupt dynamic-read register. This is
carried explicitly to #13's completion-gate work, not claimed resolved here.

#11 is **not accepted**: C1-prime remains on the documented hand-projection
route, independently reproduced and assigned to a correction worker in T12.
#13 depends on #12, not #11, so it is dispatched in a separate checkout at this
accepted producer. Its files overlap the #11 correction and will require
coordinator integration and joint regression. Orca initially attached T13 to
main; root corrected only sidebar parent metadata to the integration worktree,
then verified parent, base and HEAD. No process or checkout was replaced.

This decision unlocks implementation only. Actual host scenarios remain 0/60,
and #17 remains mandatory evidence for #12. No issue closed, no push, no main
merge, no installation changes.
