"""Mirror the single review protocol into self-contained install packages."""
import argparse
from pathlib import Path

SOURCE = Path(__file__).resolve().parent / "protocol.md"
ROOT = SOURCE.parents[2]
TARGETS = (
    ROOT / "claude/superstorm/knowledge/keep-code-simple/protocol.md",
    ROOT / "codex/cross-exam-skill/keep-code-simple/protocol.md",
    ROOT / "pi/cross-exam/skills/keep-code-simple/protocol.md",
)


def sync(check=False, source=SOURCE, targets=TARGETS):
    content = source.read_bytes()
    mismatches = []
    for target in targets:
        if not target.is_file() or target.read_bytes() != content:
            mismatches.append(str(target))
            if not check:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
    return mismatches


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    mismatches = sync(check=args.check)
    print("\n".join(mismatches) if mismatches else "Simplicity protocols match")
    raise SystemExit(1 if args.check and mismatches else 0)
