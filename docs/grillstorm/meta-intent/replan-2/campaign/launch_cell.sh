#!/usr/bin/env bash
# Launch ONE blind host cell as a supervised Orca worker. Usage: launch_cell.sh <T15|T16|T17|T18> <claude|codex> <scene>
# Reads packet_root from the batch's results.json; creates the campaign Run once (campaign-run.json in the packet root).
set -euo pipefail
T=$1; HOST=$2; SCENE=$3; ORCA=${ORCA:-orca}
R=$(cd "$(dirname "$0")/.." && pwd)
ROOT=$(python3 -c "import json;print(json.load(open('$R/$T/results.json'))['packet_root'])")
CELL="$ROOT/$HOST/$SCENE"; test -f "$CELL/actor-input.md" || { echo "no packet at $CELL" >&2; exit 2; }
# One Run PER CELL. Orca's `check` returns the Run's oldest FIFO delivery, so cells that share a Run
# let one coordinator loop consume another's question — that is how a scripted turn once reached the
# wrong actor. A Run per cell keeps every FIFO unambiguous and lets cells run concurrently.
RUNF="$CELL/run.json"
CANDIDATE=$(python3 -c "import json;print(json.load(open('$R/$T/results.json'))['source_commit'])")
$ORCA orchestration run-create --objective "meta-intent $T/$HOST/$SCENE on candidate $CANDIDATE" --json > "$RUNF"
RUN_ID=$(python3 -c "import json;print(json.load(open('$RUNF'))['result']['run']['id'])")
# The spec IS the packet, verbatim, plus the working folder. Nothing else is delivered.
SPEC="Work only inside $CELL/project. $(cat "$CELL/actor-input.md")"
$ORCA orchestration worker-start --run "$RUN_ID" --spec "$SPEC" --worktree current --agent "$HOST" --json > "$CELL/dispatch.json"
python3 - <<EOF
import json; r=json.load(open("$CELL/dispatch.json")).get("result", {})
print(json.dumps({"dispatch_id": r.get("dispatchId"), "run_id": r.get("runId"),
                  "task_id": r.get("taskId"), "cell": "$T/$HOST/$SCENE"}))
EOF
