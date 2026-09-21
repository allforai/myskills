# Seams are guarded from the receiving side

Most defects in this repository were not inside a part. They were between two parts that were each correct on their own terms. A worker receipt declared twelve reads with paths relative to a different root than the normalizer assumed; eleven vanished and the receipt still admitted on the one that resolved (`cac02bcb`). A decision gate checked that the plan's pointers existed and never opened what they pointed at (`43cb4cfc`). A launcher wrote an identity record that admission does not read (`c0a10b57`). A delegation listing that could not be checked was reported as "no delegations" (`0dcb09f3`). The root marketplace sat two version bumps behind the plugin manifests it lists (`85f12a66`). Three tests that could not all hold stayed red for four days because the suite that held them ran in no hook (`8d1746c5`).

Each time the producing side had done its own checking and was satisfied. What failed was the assumption that a producer's satisfaction carries across the boundary.

One seam here already works the other way. Under ADR-0008, `/run` hands evidence to cross-exam in a fixed ledger shape; cross-exam admits only the media it can re-verify, copies fields verbatim, and recomputes build identity and digests itself. It does not ask `/run` whether the evidence is good. This decision makes that seam the rule rather than the exception.

From this decision:

- **The receiver verifies.** Whoever consumes across a seam establishes for itself that what arrived is what it needs — present, complete in the fields it will read, fresh, and about the thing it thinks it is about. A producer's self-report of success is an input to that check, never a substitute for it.
- **What crosses is checkable.** A seam carries something the receiver can test without trusting the sender's judgement: a digest, a commit, a schema, a command it can rerun. Where only prose can cross, the receiver treats it as a claim and says so in what it passes on.
- **Unchecked is its own outcome.** A receiver that could not complete its check — tool absent, input unreadable, budget spent — returns that, distinctly. It is not a pass, not a fail, and not an empty finding; nothing downstream may read it as "nothing wrong".
- **Every copy has a drift check that runs.** Where the same content lives in two places, one is named authoritative and a check goes red when they differ. A check that no hook or pipeline invokes does not count as existing.

These are acceptance criteria for a seam, not a procedure. How a given receiver verifies is its own business and will differ between a node reading JSON, a supervisor rerunning an acceptance command, and a skill adopting another skill's record.

What this reverses: "the producer validated it" and "the file exists" as sufficient grounds to consume; treating a verification that did not happen as one that found nothing; mirrors maintained by discipline alone.
