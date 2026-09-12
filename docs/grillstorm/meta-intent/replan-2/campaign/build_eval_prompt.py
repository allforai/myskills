"""Assemble ONE blind cell's evaluator prompt from the private file, without losing criteria.

The first hand-assembled prompt truncated the criteria block mid-sentence, which dropped the
evaluator's own corroboration duties and the rule that the synthetic `test_admit_evidence.py`
cases count toward zero host cells. An evaluator missing that rule can excuse the required SG02
rejection drill by pointing at the unit tests. Slicing is therefore done by section boundary and
asserted complete, never by a character budget.

Usage: build_eval_prompt.py <private.md> <template.md> <scene> <transcript-path> <receipt-path>
"""
import argparse
import re
import sys
from pathlib import Path

# Sections carried into the prompt, in this order. "Launch and evidence" and "Raw Orca capture
# recorder" are coordinator mechanics (how to launch, how to record) and are deliberately excluded:
# the evaluator neither launches nor records. "Completion" defines what a cell must contain, so the
# evaluator needs it to know the bar.
SHARED_SECTIONS = ("Run Policy and gates", "Completion")


def sections(private_text):
    """Map every `##`/`###` heading to its body text, keyed by heading title."""
    out = {}
    pattern = re.compile(r"^(#{2,3})\s+(.+?)\s*$", re.MULTILINE)
    marks = list(pattern.finditer(private_text))
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(private_text)
        out[m.group(2)] = private_text[m.end():end].strip("\n")
    return out


def criteria_block(private_text, scene):
    found = sections(private_text)
    if scene not in found:
        raise KeyError(f"no `### {scene}` section in the private file; have {sorted(found)}")
    parts = [found[scene].strip()]
    for name in SHARED_SECTIONS:
        if name not in found:
            raise KeyError(f"shared section `## {name}` missing from the private file")
        parts.append(f"{name}:\n\n{found[name].strip()}")
    return "\n\n".join(parts)


def assert_complete(block, private_text, scene):
    """A criteria block must end at a real boundary and carry every sentence it started."""
    if not block.rstrip().endswith((".", "!", "?", "`", ")", "。")):
        raise ValueError("criteria block ends mid-sentence; it was truncated")
    # Every non-empty paragraph of every carried section must appear verbatim in the block.
    found = sections(private_text)
    for name in (scene,) + SHARED_SECTIONS:
        for para in (p.strip() for p in found[name].split("\n\n")):
            if para and para not in block:
                raise ValueError(f"section `{name}` lost a paragraph: {para[:70]!r}")
    return True


def render(template, criteria, transcript, receipt):
    for key, value in (("{{CRITERIA}}", criteria), ("{{TRANSCRIPT_PATH}}", transcript),
                       ("{{RECEIPT_PATH}}", receipt)):
        if key not in template:
            raise KeyError(f"template has no {key} placeholder")
        template = template.replace(key, value)
    left = re.findall(r"\{\{[A-Z_]+\}\}", template)
    if left:
        raise ValueError(f"unfilled placeholders remain: {left}")
    return template


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("private"); ap.add_argument("template"); ap.add_argument("scene")
    ap.add_argument("transcript"); ap.add_argument("receipt")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    private_text = Path(a.private).read_text()
    block = criteria_block(private_text, a.scene)
    assert_complete(block, private_text, a.scene)
    text = render(Path(a.template).read_text(), block, a.transcript, a.receipt)
    if a.out:
        Path(a.out).write_text(text)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
