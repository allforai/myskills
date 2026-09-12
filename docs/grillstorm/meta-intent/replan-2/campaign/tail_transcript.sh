#!/usr/bin/env bash
# Tail one dispatch's transcript into overlapping windows, from launch until the worker stops.
#
# Orca's worker-read returns at most the LAST 50 messages and there is no backwards read: --limit 200
# and --limit 1000 both return the same 50 with limited:true, and the returned cursor only pages
# forward. A single capture taken when the actor finishes therefore loses everything older than the
# window, which in practice is the whole opening exchange. Both T15 missing-product-docs cells were
# lost exactly this way. The union of overlapping windows is the only complete record, so this must
# run from dispatch, not at the end.
#
# Usage: tail_transcript.sh <dispatch-id> <out-dir> [interval-seconds]
set -u
DISPATCH=$1; OUT=$2; INTERVAL=${3:-60}
ORCA=${ORCA:-orca}
HERE=$(cd "$(dirname "$0")" && pwd)
RECORDER="$HERE/../T15/capture_worker.py"
mkdir -p "$OUT"
i=0
# Observed message rate is roughly one per 9 seconds, so 50 messages is about 450s of history and a
# 60s interval leaves a large overlap. Do not raise the interval past ~200s or windows stop meeting.
while true; do
  i=$((i+1))
  D=$(printf "%s/win-%04d" "$OUT" "$i")
  python3 "$RECORDER" "$DISPATCH" "$D" --orca "$ORCA" >/dev/null 2>&1 || true
  [ -f "$D/capture.json" ] || echo "window $i produced no capture.json"
  if ! $ORCA orchestration worker-show --dispatch "$DISPATCH" --json 2>/dev/null | grep -q '"status": "live"'; then
    # One last window after the worker stops, so the final messages are not lost to the poll gap.
    i=$((i+1))
    python3 "$RECORDER" "$DISPATCH" "$(printf '%s/win-%04d' "$OUT" "$i")" --orca "$ORCA" >/dev/null 2>&1 || true
    echo "worker no longer live; stopped after window $i"
    break
  fi
  sleep "$INTERVAL"
done
