#!/usr/bin/env python3
"""Evidence gate — the deterministic keystone of verification honesty.

Derives a node's TRUE state from its recorded `verification` evidence, downgrading
any "verified" claim that lacks real, on-disk, independently-produced proof. This
makes the lazy default path (write a PASS report, no evidence) score `unverified`
rather than inflating completeness — regardless of how the LLM behaves.

  verified    <- status != failed AND verification.method != 'none'
                 AND evidence_path EXISTS on disk
                 AND verifier present AND verifier != generator (no self-grading)
  unverified  <- generated but the above is not satisfied
  failed      <- status failed

Ledger-shaped entries (ADR-0008, #59): the runtime gates — product-verify,
runtime-smoke-verify, test-verify — also write, beside their human reports,
`<run>/evidence-entries/<node_id>.json` in cross-exam's ledger-entry shape. The
shared engine (`engine/`, a sibling of this file) validates the shape; this module
adds what only /run knows: the author marker, the build compared with the tree
now, and the fixture-match refusal `compute_completeness.hollow_reason` uses, so
the two gates cannot drift apart. Every check returns '' or the refusal reason.
A gate whose entries are refused is not passed (`--entries` exits 1).
"""
import importlib.util
import json
import os
import sys
from pathlib import Path

# Methods whose evidence MUST be a structured, reproducible capture record (anti-fabrication
# L1) — not agent-authored free text. 'screenshot' is exempt (an image, checked elsewhere).
COMMAND_METHODS = {"real-run", "real-test", "real-api", "db-query"}

ENTRIES_SCHEMA = "evidence-entries/v1"
ENTRIES_DIR = "evidence-entries"
AUTHOR_PIPELINE = "meta-skill/run"
# The build is the product tree's identity. The host directories are outside it: they are the data bus
# and generated host configuration /run itself writes while a gate runs (the same set evidence_freshness
# keeps out of the source inventory), and an entry records this scope so a later reader recomputes the
# same value. An entry declaring any other scope is refused — a validator cannot let the entry choose
# what it is validated against.
BUILD_EXCLUDES = (".allforai", ".claude", ".codex")
# The literals #55 put in compute_completeness; the ledger gate refuses in the same words.
FIXTURE_REASON = "响应与 fixture 一致（%s）的 runtime 不能判 done"
FIXTURE_UNREADABLE_REASON = "served_by.fixtures 指向的 %s 读不到，响应无法与 fixture 比对"
AUTHOR_REASON = "缺作者标记 author（pipeline / node_id / capability）"


def _is_capture_record(path):
    """True iff path holds a capture_evidence/v1 record of a SUCCESSFUL run (exit 0)."""
    try:
        with open(path) as f:
            r = json.load(f)
    except Exception:
        return False
    return (isinstance(r, dict)
            and r.get("schema") == "capture_evidence/v1"
            and "command" in r
            and r.get("exit_code") == 0
            and "stdout_sha256" in r)


def derive_state(entry, base_dir="."):
    if entry.get("status") == "failed":
        return "failed"
    v = entry.get("verification") or {}
    method = v.get("method", "none")
    if method == "none":
        return "unverified"
    ev = v.get("evidence_path")
    if not ev:
        return "unverified"
    resolved = ev if os.path.isabs(ev) else os.path.join(base_dir, ev)
    if not os.path.exists(resolved):
        return "unverified"  # claimed evidence does not exist -> downgrade
    if not v.get("verifier"):
        return "unverified"
    gen = entry.get("generated_by")
    if gen and gen == v.get("verifier"):
        return "unverified"  # verifier == generator: self-graded homework
    if method in COMMAND_METHODS and not _is_capture_record(resolved):
        return "unverified"  # anti-fabrication L1: command evidence must be a real capture record
    return "verified"


# --- the shared engine ---

_ENGINE = {}


def engine(name):
    """The engine module `name` (evidence, identity) from the mirror beside this file — or, for the
    shared orchestrator copy, from shared/evidence-engine — loaded by path so no same-named module on
    sys.path can answer for it. None when no mirror is installed; callers turn that into a reason."""
    if name in _ENGINE:
        return _ENGINE[name]
    here = Path(__file__).resolve()
    for base in (here.with_name("engine"), here.parents[2] / "evidence-engine"):
        path = base / (name + ".py")
        if path.is_file():
            spec = importlib.util.spec_from_file_location("meta_skill_engine_" + name, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            _ENGINE[name] = module
            return module
    _ENGINE[name] = None
    return None


# --- fixture matching (shared with compute_completeness.hollow_reason) ---

def same_body(a, b):
    """Byte-for-byte after whitespace, or the same JSON document however it was indented."""
    if a.strip() == b.strip():
        return True
    try:
        return json.loads(a) == json.loads(b)
    except ValueError:
        return False


def response_text(path):
    """The body a piece of evidence answered with: a capture record's stdout, else the file as-is;
    None when the file cannot be read."""
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            text = f.read()
    except OSError:
        return None
    try:
        record = json.loads(text)
    except ValueError:
        return text
    if isinstance(record, dict) and record.get("schema") == "capture_evidence/v1":
        return record.get("stdout") if isinstance(record.get("stdout"), str) else ""
    return text


def fixture_match_reason(responses, fixtures, base_dir="."):
    """Why responses that equal a declared canned fixture may not count, in cross-exam's words; "" when
    none does. `fixtures` are project-relative paths (served_by.fixtures); an unreadable one is a reason
    too, because a response nobody can compare is not shown to be real."""
    if not isinstance(fixtures, list) or not fixtures:
        return ""
    for fixture in fixtures:
        path = fixture if os.path.isabs(str(fixture)) else os.path.join(base_dir, str(fixture))
        try:
            with open(path, encoding="utf-8", errors="ignore") as f:
                canned = f.read()
        except OSError:
            return FIXTURE_UNREADABLE_REASON % fixture
        if any(same_body(response, canned) for response in responses if isinstance(response, str)):
            return FIXTURE_REASON % fixture
    return ""


# --- ledger-shaped entries ---

def author_reason(entry, node_id=None):
    """An entry /run wrote says so: author.pipeline is this pipeline, node_id and capability name the gate.
    With `node_id` given, an entry another node wrote is refused — a gate cannot pass on borrowed evidence."""
    author = entry.get("author") if isinstance(entry, dict) else None
    if not isinstance(author, dict) or author.get("pipeline") != AUTHOR_PIPELINE \
            or not all(isinstance(author.get(k), str) and author[k].strip() for k in ("node_id", "capability")):
        return AUTHOR_REASON
    if node_id is not None and author["node_id"] != node_id:
        return "作者标记的节点 %s 不是本门 %s" % (author["node_id"], node_id)
    return ""


def entry_reason(entry, run_dir, root=None, node_id=None, artifacts=()):
    """'' when `entry` may pass a /run gate: the engine's ledger-entry shape, the author marker, a build
    that is the identity of the tree at `root` right now (skipped when `root` is None), and — for a done
    runtime entry — no output equal to a declared fixture. Anything else names the rule."""
    ev = engine("evidence")
    if ev is None:
        return "证据引擎不可用：scripts/engine 未随插件安装"
    reason = ev.entry_reason(entry, run_dir) or author_reason(entry, node_id)
    if reason:
        return reason
    if entry.get("build_excludes") != list(BUILD_EXCLUDES):
        return "构建标识排除范围须为 %s" % ", ".join(BUILD_EXCLUDES)
    if root is not None:
        # The artifacts an entry names only add to its identity; a caller may still name its own.
        named = entry.get("build_artifacts") if isinstance(entry.get("build_artifacts"), list) else []
        paths = [Path(root) / str(a) for a in (artifacts or named)]
        reason = engine("identity").build_reason(entry.get("build"), root, paths, BUILD_EXCLUDES)
        if reason:
            return reason
    if entry.get("medium") == "runtime" and entry.get("verdict") == "done":
        served = entry.get("served_by") if isinstance(entry.get("served_by"), dict) else {}
        outputs = [f for f in ev.evidence_files(entry, run_dir) if f.suffix.lower() in ev.OUTPUT_SUFFIXES]
        try:
            responses = [response_text(f) for f in outputs]
        except (OSError, UnicodeError) as exc:
            return "证据文件不可读: %s" % exc
        return fixture_match_reason(responses, served.get("fixtures"), root if root is not None else run_dir)
    return ""


def entries_path(run_dir, node_id):
    return Path(run_dir) / ENTRIES_DIR / (str(node_id) + ".json")


def read_entries(run_dir, node_id, root=None):
    """(entries, '') from <run>/evidence-entries/<node_id>.json, or ([], reason)."""
    path = entries_path(run_dir, node_id)
    shown = path.relative_to(root).as_posix() if root is not None and Path(root).resolve() in path.resolve().parents \
        else path.as_posix()
    if not path.is_file():
        return [], "无证据条目文件: " + shown
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError) as exc:
        return [], "证据条目文件不可读: %s（%s）" % (shown, exc)
    entries = data.get("entries") if isinstance(data, dict) else None
    if not isinstance(entries, list):
        return [], "证据条目文件缺 entries 列表: " + shown
    if not entries:
        return [], "证据条目为空"
    return entries, ""


def entries_reason(run_dir, root, node_id, artifacts=()):
    """'' when every entry the gate `node_id` wrote under `run_dir` passes `entry_reason` against the tree at
    `root`; otherwise the first refusal, prefixed with the entry's position. A gate with no entries file, an
    unreadable one or an empty list is not passed either."""
    run_dir = Path(root) / run_dir if not Path(run_dir).is_absolute() else Path(run_dir)
    entries, reason = read_entries(run_dir, node_id, root)
    if reason:
        return reason
    for index, entry in enumerate(entries, 1):
        reason = entry_reason(entry, run_dir, root, node_id, artifacts)
        if reason:
            return "#%d: %s" % (index, reason)
    return ""


def check_entries(argv):
    """check_evidence.py --entries <run_dir> --node <node_id> [--root .] [--artifact <path>...]"""
    import argparse
    parser = argparse.ArgumentParser(prog="check_evidence.py --entries")
    parser.add_argument("--entries", required=True, metavar="RUN_DIR")
    parser.add_argument("--node", required=True)
    parser.add_argument("--root", default=".")
    parser.add_argument("--artifact", action="append", default=[])
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    reason = entries_reason(args.entries, root, args.node, args.artifact)
    if reason:
        print("REFUSED %s: %s" % (entries_path(args.entries, args.node).as_posix(), reason))
        return 1
    print("OK: %s entries admitted for %s" % (len(read_entries(root / args.entries, args.node)[0]), args.node))
    return 0


def main(argv):
    if "--entries" in argv:
        return check_entries(argv[1:])
    base = argv[1] if len(argv) > 1 else "."
    wf_path = os.path.join(base, ".allforai/bootstrap/workflow.json")
    with open(wf_path) as f:
        wf = json.load(f)
    downgraded = []
    for e in wf.get("transition_log", []):
        nid = e.get("node") or e.get("node_id")
        v = e.get("verification") or {}
        if v.get("method", "none") != "none" and derive_state(e, base) != "verified":
            downgraded.append(nid)
    if downgraded:
        print("EVIDENCE-DOWNGRADED (claimed verified but evidence missing/self-graded):")
        for nid in downgraded:
            print(f"  - {nid}")
    else:
        print("OK: no false 'verified' claims (every verified node has real evidence)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
