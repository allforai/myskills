---
status: accepted
---

# A repair delivery is a measured write, not a standstill

The declared repair loop measured a delivery as: the declared exit artifacts present and
readable, at least one content digest moved, the gate withheld only by the loop's own QA
node — and, in addition, the repair node's own readiness `valid` with its input binding
unchanged across the attempt.

Those last two conditions cannot hold for the repairs the loop exists to perform. A repair
edits the source its QA node checks; that source is also the repair node's own declared
input. Editing it makes the repair node's readiness stale and its binding move, and it makes
the QA node stale as well, so the repair cannot republish either. Every attempt was then
`unmeasured_repair_delivery`, the QA node never reran, and the loop spent its whole budget
on a rule no repair could satisfy. Observed in a real run: three attempts that each landed
the fix in the specs were all settled `failed`.

A delivery therefore drops both conditions. It claims only what the independent gate can
measure across the attempt: this attempt wrote its declared artifacts, and nothing but its
own QA node is withholding it. Whether the repair was *right* is not claimed — the QA rerun
that follows is the proof, `max_attempts` bounds the attempts either way, and the repair node
still commits only on its own merits after that rerun passes (ADR-0006 is unchanged: a
repairer never accepts its own work).

The engine's other refusals stand: an absent or incomplete measurement, a touched or
pre-existing artifact, an unreadable one, and a gate withheld by anything other than the
loop's QA node all remain hard failures rather than quiet advances.
