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


def turns_for(private_md, scene):
    section = re.search(r'^### ' + re.escape(scene) + r'\n(.*?)(?=^### |\Z)', private_md, re.S | re.M)
    if not section:
        return []
    return [m.group(1) for m in QUOTED.finditer(section.group(1))]


def main():
    T, scene = sys.argv[1], sys.argv[2]
    R = Path(__file__).resolve().parent.parent
    private = (R / T / "evaluator-private.md").read_text()
    root = Path(json.load(open(R / T / "results.json"))["packet_root"])
    turns = turns_for(private, scene)
    (root / f"{scene}-turns.json").write_text(json.dumps({"turns": turns}, ensure_ascii=False, indent=2))
    print(json.dumps({"scene": scene, "turns": len(turns), "file": str(root / f"{scene}-turns.json")}))


if __name__ == "__main__":
    main()
