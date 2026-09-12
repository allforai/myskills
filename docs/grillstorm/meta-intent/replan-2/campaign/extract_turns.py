"""Pull one scenario's scripted user turns out of evaluator-private.md, in order, and nothing else.

The private file mixes turns (quoted strings the coordinator delivers) with observations (what the
evaluator looks for). Only the quoted strings are turns; the observations never leave the evaluator.

Usage: extract_turns.py <T15|T16|T17|T18> <scene>   → writes <packet_root>/<scene>-turns.json
"""
import json
import re
import sys
from pathlib import Path

QUOTED = re.compile(r'"([^"\n]{8,})"')      # a user turn is a quoted sentence; short quoted tokens are not turns


# A scene whose private section defines its answers by reference to another scene's, rather than
# quoting them again. The borrow is the private file's own instruction, quoted in the value, so the
# turns are never invented here.
# A scenario that reuses another's answers. `mode` says how:
#   "all"    - this scene's turns ARE the other scene's turns, in order.
#   "detail" - this scene keeps its own turns and INSERTS the other scene's detail answer in the
#              middle, because the private text says to use those answers for follow-up questions.
#
# deny-inferred-intent was missing from this table, so its script held only the denial and the freeze.
# The freeze says "the group rules we discussed" when no rules had been delivered, and the actor
# correctly refused to invent them and asked. The borrow is not optional: the private text for that
# scene says "For relevant follow-up questions, use the reshape scenario's membership, request
# claim/fulfillment and privacy answers."
BORROWS = {
    ("T15", "new-product"): {"from": "reshape-business-model", "mode": "all",
                             "why": "Answer relevant questions with the reshape scenario's choices, then "
                                    "approve the named directions and release scope as in reshape."},
    ("T15", "deny-inferred-intent"): {"from": "reshape-business-model", "mode": "detail",
                                      "insert_at": 1, "detail_index": 1,
                                      "why": "For relevant follow-up questions, use the reshape "
                                             "scenario's membership, request claim/fulfillment and "
                                             "privacy answers."},
}


def turns_for(private_md, scene, batch=None):
    borrow = BORROWS.get((batch, scene))
    if borrow and borrow["mode"] == "all":
        return turns_for(private_md, borrow["from"], batch=batch)
    if borrow and borrow["mode"] == "detail":
        own = turns_for(private_md, scene, batch=None)
        lender = turns_for(private_md, borrow["from"], batch=None)
        detail = lender[borrow["detail_index"]]
        return own[:borrow["insert_at"]] + [detail] + own[borrow["insert_at"]:]
    section = re.search(r'^### ' + re.escape(scene) + r'\n(.*?)(?=^### |\Z)', private_md, re.S | re.M)
    if not section:
        return []
    return [m.group(1) for m in QUOTED.finditer(section.group(1))]


def main():
    T, scene = sys.argv[1], sys.argv[2]
    R = Path(__file__).resolve().parent.parent
    private = (R / T / "evaluator-private.md").read_text()
    root = Path(json.load(open(R / T / "results.json"))["packet_root"])
    turns = turns_for(private, scene, batch=T)
    (root / f"{scene}-turns.json").write_text(json.dumps({"turns": turns}, ensure_ascii=False, indent=2))
    print(json.dumps({"scene": scene, "turns": len(turns), "file": str(root / f"{scene}-turns.json")}))


if __name__ == "__main__":
    main()
