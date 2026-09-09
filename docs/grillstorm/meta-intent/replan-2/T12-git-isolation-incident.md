# T12 fixture Git isolation incident

During implementation review, the coordinator observed a test-fixture Git command
escaping its temporary project while running inside a commit hook. This is a
development/test isolation defect, not a successful product or host scenario.

- The T12 branch advanced from `88e7beca` to `6f8bc092b3fe555129f74cfc5b4e79214a4bb3b3`,
  titled `Fixture`, containing the worker's staged implementation and an unintended
  root `orders.py` fixture file. The latter was absent at the accepted base.
- The shared Git configuration also changed to `core.bare=true`. A read-only main
  check failed with `fatal: this operation must be run in a work tree`.
- The coordinator restored only the known non-bare repository setting with
  `git config --local core.bare false` from `/Users/aa/workspace/myskills`.
  Main then reported a clean worktree, `--is-bare-repository=false`, and HEAD
  `d8a84fac` (another actor's newer main commit, left intact).
- No reset, history rewrite, main merge, push, or real product-source deletion was
  performed by the coordinator. The worker subsequently reported a soft reset of
  its own accidental local commit to `88e7beca`, preserving intended changes in
  its index and unstaging the phantom file. The accidental commit hash above is
  recorded for audit; it is no longer claimed to remain on the branch history.
- The implementation worker was instructed to isolate all fixture Git subprocesses
  from inherited `GIT_*` context, disable fixture hooks, add a containment regression,
  and remove only the confirmed synthetic `orders.py` contamination. Acceptance
  remains pending corrected commits and independent verification.

The corrected T12 candidate is `b6357a013415db2012b73d89792955f2afc5d4aa`.
Its regression injects enclosing Git context and compares enclosing HEAD, index
bytes and shared config bytes before/after fixture Git commands. The enabled
commit hook passed. After merging the candidate into the integration worktree,
the coordinator independently ran 382 Python tests and 55 engine tests successfully;
main remained clean and non-bare. The earlier accidental fixture file is absent.

Initial scope reporting was corrected after the shared-configuration effect was
discovered. A clean main status proves the current tracked working tree is clean;
it is not a claim that main has not advanced through other actors' work.
