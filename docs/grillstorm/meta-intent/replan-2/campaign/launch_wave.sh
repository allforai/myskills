#!/usr/bin/env bash
# Launch several cells concurrently, each with its own Run, and start a driving loop for each.
#
# Safe to run wide ONLY for scenarios whose scripted turns are all replies to actor questions, so the
# loop delivers them from that scenario's own turns.json and the coordinator never picks a line by
# hand. Scenarios needing hand-ordered turns — large-code-local-button's unwired-decision probe, and
# interrupted-confirmation's deliberate context kill — must be driven one at a time instead.
#
# Usage: launch_wave.sh T15 <scene> [<scene> ...]
set -uo pipefail
T=$1; shift
ORCA=${ORCA:-orca}
HERE=/Users/aa/workspace/myskills/docs/grillstorm/meta-intent/replan-2/campaign
ROOT=/private/tmp/meta-intent-host-campaign.pGw3c0/T15
SC=${SC:-/tmp}
for SCENE in "$@"; do
  for HOST in codex claude; do
    CELL=$ROOT/$HOST/$SCENE
    out=$(ORCA=$ORCA bash $HERE/launch_cell.sh "$T" "$HOST" "$SCENE" 2>&1 | tail -1)
    D=$(python3 -c "import json,sys;print(json.loads(sys.argv[1]).get('dispatch_id',''))" "$out" 2>/dev/null)
    RUN=$(python3 -c "import json,sys;print(json.loads(sys.argv[1]).get('run_id',''))" "$out" 2>/dev/null)
    if [ -z "$D" ]; then echo "LAUNCH FAILED $HOST/$SCENE: $out"; continue; fi
    nohup timeout 1700 python3 $HERE/answer_loop.py --dispatch "$D" --run "$RUN" \
      --script $ROOT/$SCENE-turns.json --out $CELL/capture --orca "$ORCA" --timeout-ms 900000 \
      > $SC/wave-$HOST-$SCENE.out 2>&1 &
    echo "$HOST/$SCENE dispatch=$D run=$RUN"
  done
done
