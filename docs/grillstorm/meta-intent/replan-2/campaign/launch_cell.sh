#!/usr/bin/env bash
# Launch ONE blind host cell as a supervised Orca worker. Usage: launch_cell.sh <T15|T16|T17|T18> <claude|codex> <scene>
# Reads packet_root from the batch's results.json; creates the campaign Run once (campaign-run.json in the packet root).
set -euo pipefail
T=$1; HOST=$2; SCENE=$3; ORCA=${ORCA:-orca}
R=$(cd "$(dirname "$0")/.." && pwd)
ROOT=$(python3 -c "import json;print(json.load(open('$R/$T/results.json'))['packet_root'])")
CELL="$ROOT/$HOST/$SCENE"; test -f "$CELL/actor-input.md" || { echo "no packet at $CELL" >&2; exit 2; }
RUNF="$ROOT/campaign-run.json"
if [ ! -f "$RUNF" ]; then
  $ORCA orchestration run-create --objective "meta-intent host campaign $T on candidate $(python3 -c "import json;print(json.load(open('$R/$T/results.json'))['source_commit'])")" --json > "$RUNF"
fi
RUN_ID=$(python3 -c "import json;d=json.load(open('$RUNF'));print(d.get('run_id') or d.get('run',{}).get('id'))")
# The spec IS the packet, verbatim, plus the working folder. Nothing else is delivered.
SPEC="Work only inside $CELL/project. $(cat "$CELL/actor-input.md")"
$ORCA orchestration worker-start --spec "$SPEC" --worktree current --agent "$HOST" --json | tee "$CELL/dispatch.json"
python3 - <<EOF
import json; d=json.load(open("$CELL/dispatch.json"))
print(json.dumps({"dispatch_id": d.get("dispatch_id") or d.get("dispatch",{}).get("id"), "run_id": "$RUN_ID", "cell": "$T/$HOST/$SCENE"}))
EOF
