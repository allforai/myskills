# Authorized closure refinements

## AD-02: Preserve proof and progress through workflow projection

- Trigger: workflow reverse round1 WG-01/WG-02/WG-03.
- Adopted: hash-bound root Orca task packets; at most one live evaluator with an available subject slot and completion priority; parent-plus-child scenario matrix including new-product on both hosts.
- Alternatives: generic JSON-only prompts can lose criteria; admitting three waiting evaluators can deadlock; child-only case lists omit already-approved R19. Raising concurrency or adding product dependencies is unnecessary.
- Scope: workflow projection revision2, unchanged spec2/task1/product behavior/interfaces/paths. No new testing framework or installed skill change.
- Revalidation: actual packet assembly T9/T15, deterministic role-admission dry-run, unchanged task/DAG/failure validation, independent workflow reverse round2.

## AD-01: Observation and candidate identity

- Trigger: spec reverse round1 SG-01/SG-02.
- Adopted: bind verification to actual consumed manifest and check current input equality; bind cross-host scenarios to actual loaded run-owned candidate paths/hashes, invalidating affected proof after candidate changes.
- Alternative: hash only at stamp time or record only provider version; rejected because that can certify unobserved code or installed old Skill.
- Scope: clarifies #8 R21/R27/R28/R30 and existing #12/#13/#15–#18 proof, no new product decision or new harness.
- Revalidation: full reverse-spec, independent closure/abstraction critics; later public interleaving and candidate-mismatch proof.
