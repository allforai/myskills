# T12 selected baseline payload probe

Coordinator-owned deterministic probe, not an actual Claude/Codex dialogue.
The script is retained at `/tmp/meta-intent-t12-root-probe.Z4ynIN/probe.py`.
It imports the worker's public fixture builder, copies each host's CLI into a
separate synthetic project, observes and publishes evidence, then changes only
the selected baseline intent's goal and baseline version.

Before correction, both copied CLI variants returned `deliver-export.status=valid`
and `readiness_status=valid`, despite the changed selected baseline goal. The
minimal probe baseline is synthetic rather than the full #10 journal contract;
the worker was asked to add a regression using the valid #10 producer as well.

After the work-in-progress correction added selected baseline intent content to
the fingerprint, the same probe in new temporary projects returned `status=stale`
and `readiness_status=stale` on both copies. The diagnostic `check` command returns
exit 0 with node statuses; the consuming public gates must interpret the stale
state. This is a pre-candidate recheck, not final acceptance of #12 or host proof.
