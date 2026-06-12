# claude/megastorm/scripts/test_check_closure.py
import unittest
from check_closure import check_closure


def _m(module, covers, exposes=(), consumes=()):
    return {"module": module, "covers_req_ids": list(covers),
            "exposes": list(exposes), "consumes": list(consumes)}


class TestCheckClosure(unittest.TestCase):
    def test_full_closure(self):
        reqs = ["R1", "R2", "R3"]
        manifests = [_m("a", ["R1", "R2"], exposes=["api:x"]),
                     _m("b", ["R3"], consumes=["api:x"])]
        r = check_closure(reqs, manifests)
        self.assertTrue(r["ok"], r["errors"])

    def test_uncovered_requirement(self):
        r = check_closure(["R1", "R2"], [_m("a", ["R1"])])
        self.assertFalse(r["ok"])
        self.assertTrue(any("R2" in e and "uncovered" in e for e in r["errors"]))

    def test_orphan_requirement_id(self):
        r = check_closure(["R1"], [_m("a", ["R1", "R9"])])
        self.assertFalse(r["ok"])
        self.assertTrue(any("R9" in e and "orphan" in e for e in r["errors"]))

    def test_dangling_consume(self):
        r = check_closure(["R1"], [_m("a", ["R1"], consumes=["api:ghost"])])
        self.assertFalse(r["ok"])
        self.assertTrue(any("api:ghost" in e for e in r["errors"]))

    def test_unconsumed_expose_warns(self):
        r = check_closure(["R1"], [_m("a", ["R1"], exposes=["api:unused"])])
        self.assertTrue(r["ok"], r["errors"])
        self.assertTrue(any("api:unused" in w for w in r["warnings"]))

    def test_expose_outside_registry_errors(self):
        # closed-vocabulary: with a frozen interface registry, any exposes/consumes
        # name not in it is a naming-drift error (Finding 2: parallel agents diverge)
        reg = ["api:createOrder"]
        r = check_closure(["R1"], [_m("a", ["R1"], exposes=["api:create_order"])], interface_registry=reg)
        self.assertFalse(r["ok"])
        self.assertTrue(any("api:create_order" in e and "registry" in e for e in r["errors"]))

    def test_registry_names_pass(self):
        reg = ["api:createOrder"]
        manifests = [_m("a", ["R1"], exposes=["api:createOrder"]),
                     _m("b", ["R1"], consumes=["api:createOrder"])]
        r = check_closure(["R1"], manifests, interface_registry=reg)
        self.assertTrue(r["ok"], r["errors"])

    def test_no_registry_skips_vocab_check(self):
        # backward-compatible: no registry => only coverage/interface/orphan run
        r = check_closure(["R1"], [_m("a", ["R1"], exposes=["api:anything"])])
        self.assertTrue(r["ok"], r["errors"])


if __name__ == "__main__":
    unittest.main()
