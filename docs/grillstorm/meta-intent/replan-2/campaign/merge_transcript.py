"""Union several bounded transcript captures into one dialogue record, and say what is still missing.

Orca retains only the last 50 messages of a dispatch's transcript and `--limit` does not reach
further back (verified: limit 200 and limit 1000 both return 50 with `limited: true`). A single
capture taken when the actor finishes therefore loses the opening exchange entirely. The only
complete record is the union of windows captured often enough to overlap, which means tailing from
launch. This module builds that union and, crucially, refuses to hide a front gap: it reports the
first known dialogue event so a coordinator can see whether the opening turn was ever captured.

Usage: merge_transcript.py <capture-root> --out <raw-dialogue.json> [--started-at <epoch_ms>]
"""
import argparse
import json
from pathlib import Path


def capture_dirs(root):
    """Every bounded capture under root, in stable order."""
    return sorted({p.parent for p in Path(root).rglob("capture.json")})


def page_messages_of(page_path):
    try:
        obj = json.loads(Path(page_path).read_text())
    except (OSError, ValueError):
        return []
    result = obj.get("result") or {}
    return (result.get("transcript") or {}).get("messages") or result.get("messages") or []


RETENTION_CAP = 50  # Orca returns at most this many messages per read; verified at --limit 1000.


def window_detail(capture_dir, cap=RETENTION_CAP):
    """What one window saw, and whether it was saturated.

    Saturation is the whole question. A window that came back with fewer messages than the cap held
    the transcript's ENTIRE history at that moment, so it starts at message one and nothing can
    predate it. `limited` is useless for this: Orca reports limited:true even on a 1-message read.
    """
    messages = []
    returned = 0
    for page in sorted(Path(capture_dir).glob("page-*.stdout.json")):
        page_messages = page_messages_of(page)
        messages.extend(page_messages)
        returned = max(returned, len(page_messages))
    stamps = [m.get("timestamp") for m in messages if m.get("timestamp")]
    return {"window": Path(capture_dir).name,
            "returned": returned,
            "saturated": returned >= cap,
            "ids": {m["id"] for m in messages if m.get("id")},
            "earliest_ms": min(stamps) if stamps else None}


def union(root):
    """Deduplicate by message id across every window, ordered by timestamp then id.

    A message seen in several windows is kept once, and every window that saw it is recorded, which
    is what lets an evaluator tell a single-window claim from a corroborated one.
    """
    merged = {}
    for d in capture_dirs(root):
        for page in sorted(d.glob("page-*.stdout.json")):
            for m in page_messages_of(page):
                mid = m.get("id")
                if not mid:
                    continue
                entry = merged.setdefault(mid, {"message": m, "seen_in": []})
                if d.name not in entry["seen_in"]:
                    entry["seen_in"].append(d.name)
    ordered = sorted(merged.values(), key=lambda e: (e["message"].get("timestamp") or 0,
                                                     e["message"].get("id") or ""))
    return ordered


def gaps(ordered, threshold_ms=120000):
    """Silences longer than threshold between consecutive captured messages."""
    out = []
    stamps = [e["message"].get("timestamp") for e in ordered if e["message"].get("timestamp")]
    for a, b in zip(stamps, stamps[1:]):
        if b - a > threshold_ms:
            out.append({"after_ms": a, "before_ms": b, "silence_ms": b - a})
    return out


def coverage(ordered, started_at=None, root=None):
    """State plainly whether the record is complete, and on what proof.

    Completeness is not a timestamp tolerance. It is proven when the earliest window was unsaturated,
    because such a window held the whole history at that instant, and when every later window shares
    a message with what came before it, so the windows form an unbroken chain rather than islands.
    """
    stamps = [e["message"].get("timestamp") for e in ordered if e["message"].get("timestamp")]
    cov = {
        "messages": len(ordered),
        "earliest_ms": stamps[0] if stamps else None,
        "latest_ms": stamps[-1] if stamps else None,
        "windows": sorted({w for e in ordered for w in e["seen_in"]}),
        "internal_gaps": gaps(ordered),
        "single_window_messages": sum(1 for e in ordered if len(e["seen_in"]) == 1),
    }
    details = []
    if root is not None:
        details = [window_detail(d) for d in capture_dirs(root)]
        details = [d for d in details if d["returned"]]
        details.sort(key=lambda d: (d["earliest_ms"] or 0, d["window"]))
    cov["window_reads"] = [{k: d[k] for k in ("window", "returned", "saturated")} for d in details]
    cov["starts_at_first_message"] = bool(details) and not details[0]["saturated"]
    cov["first_window"] = details[0]["window"] if details else None
    broken = []
    accumulated = set()
    for index, detail in enumerate(details):
        # An unsaturated window contains message one, so it can never open a gap.
        if index and detail["saturated"] and not (detail["ids"] & accumulated):
            broken.append(detail["window"])
        accumulated |= detail["ids"]
    cov["chain_breaks"] = broken
    if started_at and stamps:
        # Kept as information only. The delay between creating the Run and the agent's first message
        # is launch latency, not lost dialogue, so it must not decide completeness.
        cov["launch_to_first_message_ms"] = stamps[0] - int(started_at)
    cov["full_dialogue_proven"] = bool(
        stamps and not cov["internal_gaps"] and cov["starts_at_first_message"] and not broken)
    return cov


def build(root, started_at=None):
    ordered = union(root)
    return {"dialogue": [e["message"] for e in ordered],
            "provenance": [{"id": e["message"].get("id"), "seen_in": e["seen_in"]} for e in ordered],
            "coverage": coverage(ordered, started_at, root)}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("capture_root")
    ap.add_argument("--out", required=True)
    ap.add_argument("--started-at", type=int, help="dispatch start, epoch ms, to expose a front gap")
    a = ap.parse_args(argv)
    doc = build(a.capture_root, a.started_at)
    Path(a.out).write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(doc["coverage"], indent=2))
    return 0 if doc["coverage"]["full_dialogue_proven"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
