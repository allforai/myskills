"""Cut tracked code into jev_batch.py input rows: by file, diff hunk, grep match, or fixed window.

Only files listed by `git ls-files`; binaries and files over --max-bytes are skipped.
Refuses (exit 3) when --root is not in the outbound allowlist.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import jev_config as C  # noqa: E402

HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def tracked_files(root, pathspecs):
    out = subprocess.run(["git", "-C", root, "ls-files", "-z", "--", *pathspecs],
                         capture_output=True, check=True).stdout
    return [p for p in out.decode("utf-8").split("\0") if p]


def read_text(path, max_bytes):
    try:
        raw = Path(path).read_bytes()
    except OSError:
        return None
    if len(raw) > max_bytes or b"\0" in raw[:8000]:
        return None
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return None


def by_file(text):
    n = len(text.splitlines())
    return [(1, n)] if n else []


def by_window(text, lines, overlap):
    n = len(text.splitlines())
    ranges, start = [], 1
    while start <= n:
        end = min(start + lines - 1, n)
        ranges.append((start, end))
        if end == n:
            break
        start = end - overlap + 1
    return ranges


def by_grep(text, pattern, context):
    rx = re.compile(pattern)
    lines = text.splitlines()
    ranges = []
    for i, line in enumerate(lines, 1):
        if rx.search(line):
            s, e = max(1, i - context), min(len(lines), i + context)
            if ranges and s <= ranges[-1][1] + 1:
                ranges[-1] = (ranges[-1][0], max(ranges[-1][1], e))
            else:
                ranges.append((s, e))
    return ranges


def parse_diff(diff_text):
    hunks, path, current = [], None, None
    for line in diff_text.splitlines():
        if line.startswith("+++ "):
            target = line[4:]
            path = None if target == "/dev/null" else target[2:] if target.startswith("b/") else target
            continue
        m = HUNK.match(line)
        if m:
            current = None
            if path is not None:
                start, count = int(m.group(1)), int(m.group(2) if m.group(2) is not None else 1)
                current = [path, start, start + max(count, 1) - 1, [line]]
                hunks.append(current)
            continue
        if line.startswith("diff --git"):
            current = None
        elif current is not None:
            current[3].append(line)
    return [(p, s, e, "\n".join(body)) for p, s, e, body in hunks]


def make_row(rel, start, end, body):
    return {"id": f"{rel}:{start}-{end}", "state": f"# {rel} (lines {start}-{end})\n{body}"}


def main(argv):
    parser = argparse.ArgumentParser(prog="code_chunks.py")
    parser.add_argument("--root", required=True)
    parser.add_argument("--by", required=True, choices=["file", "window", "grep", "hunk"])
    parser.add_argument("--out", required=True)
    parser.add_argument("--lines", type=int, default=80)
    parser.add_argument("--overlap", type=int, default=10)
    parser.add_argument("--pattern")
    parser.add_argument("--context", type=int, default=5)
    parser.add_argument("--base", default="HEAD")
    parser.add_argument("--max-bytes", type=int, default=200_000)
    parser.add_argument("paths", nargs="*")
    args = parser.parse_args(argv)
    if args.by == "grep" and not args.pattern:
        parser.error("--by grep needs --pattern")
    if not C.is_allowed(args.root):
        print(f"{args.root} 不在外发放行清单 {C.config_dir() / 'allow.json'} 里；没有生成切块。", file=sys.stderr)
        return 3
    rows = []
    if args.by == "hunk":
        diff = subprocess.run(["git", "-C", args.root, "diff", f"-U{args.context}", args.base, "--", *args.paths],
                              capture_output=True, text=True, check=True).stdout
        rows = [make_row(p, s, e, body) for p, s, e, body in parse_diff(diff)]
    else:
        for rel in tracked_files(args.root, args.paths):
            text = read_text(Path(args.root) / rel, args.max_bytes)
            if text is None:
                continue
            lines = text.splitlines()
            if args.by == "file":
                ranges = by_file(text)
            elif args.by == "window":
                ranges = by_window(text, args.lines, args.overlap)
            else:
                ranges = by_grep(text, args.pattern, args.context)
            rows += [make_row(rel, s, e, "\n".join(lines[s - 1:e])) for s, e in ranges]
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"{len(rows)} 块 → {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
