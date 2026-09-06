import os
import unittest


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def read(relative_path):
    with open(os.path.join(ROOT, relative_path), encoding="utf-8") as handle:
        return handle.read()


class TestSuperstormContract(unittest.TestCase):
    def test_progressive_disclosure_budget(self):
        router = read("skills/superstorm/SKILL.md")
        playbook = read("knowledge/execution-playbook.md")
        self.assertLessEqual(len(router.split()), 1000)
        self.assertLessEqual(len(playbook.split()), 2000)

    def test_router_references_normative_playbook(self):
        router = read("skills/superstorm/SKILL.md")
        self.assertIn("$ROOT/knowledge/execution-playbook.md", router)
        self.assertIn("follow it exactly", router)

    def test_skill_preserves_new_and_resume_entry_states(self):
        command = read("skills/superstorm/SKILL.md")
        self.assertIn("entry-state selection", command)
        self.assertIn("A new run", command)
        self.assertIn("existing valid run resumes", command)

    def test_failure_and_portability_rules_remain_explicit(self):
        combined = read("skills/superstorm/SKILL.md") + read("knowledge/execution-playbook.md")
        required = (
            "Never silently substitute",
            "vacuous:true",
            "reality_gated:true",
            "Completeness unverified",
            "cross-host recovery",
            "transcript or",
        )
        for phrase in required:
            self.assertIn(phrase, combined)

    def test_decisions_cannot_bypass_durable_gateway(self):
        combined = read("skills/superstorm/SKILL.md") + read("knowledge/execution-playbook.md")
        required = (
            "decision_ledger.py record",
            "decision_ledger.py finalize",
            "Never edit `decision-ledger.json` directly",
            "three",
            "emergency journal",
            "perform no further mutations",
            "degraded",
        )
        for phrase in required:
            self.assertIn(phrase, combined)

    def test_phase1_concurrency_never_requires_a_question(self):
        playbook = read("knowledge/execution-playbook.md")
        self.assertIn("machine-load policy", playbook)
        self.assertIn("continue without asking", playbook)
        self.assertNotIn("user-chosen `max_concurrency`", playbook)


if __name__ == "__main__":
    unittest.main()
