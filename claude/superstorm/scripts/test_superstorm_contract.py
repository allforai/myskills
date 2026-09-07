# claude/superstorm/scripts/test_superstorm_contract.py
"""Contract test for the superstorm router and execution playbook.

This test pins GUARDS, not wording. A guard is a rule that constrains information flow or motive
(who may see what, what counts as evidence, what may never be claimed). Guards hold regardless of
model strength, so removing one is a design change and must break this test. Anything that merely
describes a method (a count, a tier, a template, a rhythm) is scaffolding and is deliberately not
pinned here: rewording or removing scaffolding must not touch CI.

Each guard lists alternative anchors; any one match in the named files satisfies it. The `why`
is for the maintainer who is about to delete the guard.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


ROUTER = "skills/superstorm/SKILL.md"
PLAYBOOK = "knowledge/execution-playbook.md"
SUPERVISOR = "knowledge/prompts/supervisor.md"
EXECUTOR = "knowledge/prompts/executor.md"
DESIGN = "knowledge/prompts/design-agent.md"

# name -> (files, [regex alternatives], why)
GUARDS = {
    "supervisor never sees executor narrative": (
        [SUPERVISOR],
        [r"NOT given the executor'?s narrative", r"not (?:given|shown) .*self-report"],
        "Expectation isolation: a verifier that reads the claim is anchored by it, whatever the model.",
    ),
    "executor self-report is not trusted": (
        [EXECUTOR],
        [r"self-report is NOT trusted", r"self-report .*not trusted"],
        "No self-review: completion is confirmed by an independent rerun, never by the author.",
    ),
    "zero executed tests is not a pass": (
        [SUPERVISOR, PLAYBOOK],
        [r"vacuous:\s*true", r"0 tests ran", r"Executed 0 tests"],
        "Evidence gate: a name-selective test that matched nothing exits 0 and proves nothing.",
    ),
    "proof lives in the committed tree, not in a transcript": (
        [PLAYBOOK],
        [r"transcript .* never portable completion proof", r"never assume executors committed"],
        "Evidence gate: what is not committed cannot be resumed, merged, or verified by another host.",
    ),
    "reality-gated work is neither verified nor failed": (
        [PLAYBOOK, ROUTER],
        [r"neither autonomously verified nor failed", r"Never say the feature works while this list is non-empty"],
        "Honesty gate: an environmental proof failure is not a code defect and not a success.",
    ),
    "class goals need a census or say Completeness unverified": (
        [PLAYBOOK, ROUTER],
        [r"Completeness unverified"],
        "Zero hits are a question, not a conclusion: an audit cannot prove that nothing was missed.",
    ),
    "decisions go through the ledger script": (
        [PLAYBOOK, ROUTER],
        [r"decision_ledger\.py record", r"Never edit `decision-ledger\.json` directly"],
        "Audit gate: an autonomous decision without a durable record is an unaccountable mutation.",
    ),
    "no writable ledger means no further mutations": (
        [PLAYBOOK, ROUTER],
        [r"perform no further mutations", r"stop new mutations", r"never grants permission to continue mutating"],
        "Audit gate: loss of decision state must stop the run, not be worked around.",
    ),
    "phase 1 never asks the user": (
        [PLAYBOOK, ROUTER],
        [r"Never ask the user during Phase 1", r"continue without asking"],
        "Decisions are front-loaded; an unattended pipeline that stops to ask is not unattended.",
    ),
    "skips are reported, never hidden in a percentage": (
        [PLAYBOOK, ROUTER],
        [r"N done / M skipped via K escalations", r"never use a bare completion percentage", r"Never hide skipped"],
        "Honesty gate: a green percentage swallows deferred and skipped work.",
    ),
    "infrastructure failure is not business failure": (
        [PLAYBOOK, ROUTER],
        [r"never consumes business retries", r"Never treat infrastructure failure as business failure"],
        "Attribution gate: a network error spent as a code retry burns budget on the wrong cause.",
    ),
    "no invented fallback output": (
        [ROUTER, EXECUTOR, SUPERVISOR],
        [r"Never invent fallback output", r"unapproved internal fallback", r"swallowed errors"],
        "Motive gate: a default, mock, or swallowed error turns a failure into a fake success.",
    ),
    "touched_paths bound the executor": (
        [EXECUTOR],
        [r"touched_paths"],
        "Concurrency isolation: parallel writers must declare their write set so collisions are detectable.",
    ),
    "design uses the closed interface vocabulary": (
        [DESIGN],
        [r"closed interface vocabulary", r"do NOT invent"],
        "Parallel agents cannot see each other; a closed vocabulary is the join key for closure checks.",
    ),
    "cross-exam is never auto-invoked": (
        [PLAYBOOK, ROUTER],
        [r"Do not invoke, suggest, or invite `/cross-exam`", r"/cross-exam` remains an explicit, separate command"],
        "Motive gate: the delivering pipeline must not start its own audit.",
    ),
    "worktree isolation is real isolation or serialized writes": (
        [PLAYBOOK, ROUTER],
        [r"serialize[d]? .*collision groups", r"Worktree isolation is valid only when"],
        "Concurrency isolation: prompt-level promises of isolation are not isolation.",
    ),
}


class TestSuperstormGuards(unittest.TestCase):
    def test_every_guard_is_present(self):
        missing = []
        for name, (files, anchors, why) in GUARDS.items():
            text = "\n".join(read(f) for f in files)
            if not any(re.search(a, text, flags=re.IGNORECASE | re.DOTALL) for a in anchors):
                missing.append(f"{name}\n    files: {files}\n    why: {why}")
        self.assertFalse(missing, "guards removed from the skill text:\n" + "\n".join(missing))

    def test_guard_table_names_only_existing_files(self):
        for files, _, _ in GUARDS.values():
            for f in files:
                self.assertTrue((ROOT / f).is_file(), f)


class TestSuperstormStructure(unittest.TestCase):
    """Structural facts the router relies on; these are not wording pins."""

    def test_router_points_at_the_playbook(self):
        self.assertIn("$ROOT/knowledge/execution-playbook.md", read(ROUTER))
        self.assertTrue((ROOT / PLAYBOOK).is_file())

    def test_playbook_keeps_its_phase_skeleton(self):
        headings = re.findall(r"^##+ .*$", read(PLAYBOOK), flags=re.MULTILINE)
        joined = "\n".join(headings)
        for phase in ("Phase -1", "Phase 0", "Phase 1", "Phase 2"):
            self.assertIn(phase, joined)

    def test_router_keeps_new_and_resume_entry_states(self):
        router = read(ROUTER)
        self.assertIn("entry-state selection", router)
        self.assertIn("A new run", router)
        self.assertIn("existing valid run resumes", router)

    def test_hard_rules_section_exists(self):
        self.assertIn("## Hard Rules", read(ROUTER))


if __name__ == "__main__":
    unittest.main()
