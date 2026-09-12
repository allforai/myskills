# T15 / codex / missing-product-docs — CERTIFIED PASS

Candidate 01146b70, tree ce4a69c0…, dispatch ctx_b9eade800dff, run run_6cb69f6ac489,
task task_e4e0dd73523f. Host: Codex, own Orca Run.
Evaluator: fresh context, complete criteria built by `build_eval_prompt.py`, did not run the actor.

**The campaign's first certified cell.** `status: "passed"`. This is the third attempt at this
scenario; the first two are archived as uncertifiable, and neither failed on the actor's conduct.

## Why this attempt could be certified and the others could not

| | archived attempts | this attempt |
|---|---|---|
| Transcript windows | 1, taken at the end | 13 plus a final, from dispatch |
| Front gap | 889 s / whole opening lost | none, proven |
| Messages seen by only one window | most | 0 |
| Identity | self-reported session id | bound to the launch record |
| `full_dialogue_proven` | false | **true** |

Completeness was verified by the evaluator from the raw page bytes, not from the coverage block it
was handed. Its check: `win-0001` returned **1 message against a requested limit of 100**, and one
message under a limit of 100 cannot be truncated, so that window held the entire history. Consecutive
window overlaps run 1, 17, 28, 30, 32, 38, 47, 44, 47, 50 with no zero. The union's 59 ids exactly
equal the distinct ids across all 14 captures, in both directions. It also checked the three windows
absent from the coverage list and confirmed they add no message the union lacks.

The opening exchange is present and quoted: the actor's scope question at `dialogue[11]`, and the
scripted answer at `dialogue[16]` byte-for-byte identical to the private criteria's text.

## Identity, corroborated rather than asserted

The actor's own untouched receipt names `dispatch_id: ctx_b9eade800dff` and
`terminal_handle: term_c353150c-…`, identical to the coordinator record written **before the actor
produced any output**. Independently, Orca's own CLI replies inside the transcript carry the same run,
dispatch and runtime ids. The evaluator verified that normalization was faithful rather than a
rewrite: the 26 assets whose paths moved from `codex/meta-skill/scripts/` to
`claude/meta-skill/scripts/` were already carried that way in the actor's own `resolved_path`, and the
manifest pins exactly that symlink.

Loaded-file completeness: all 52 entries hash-match, 22 corroborated by a path in a dialogue tool
call and 36 by byte-identical copies the actor wrote into the project. **Corroborated by neither: 0.**
Conversely, every candidate file path visible in the dialogue appears in the receipt.

Scope discipline: a scan of the whole dialogue for the other cells, the archived attempts, the
evaluator materials, the manifest and `source-before.json` returned **zero hits**. The actor never
looked outside its packet.

### Stated plainly as not corroborated

- The provider `session_id` still rests on the actor's own environment read. The coordinator record
  carries no session id, and no provider session store was available. The binding that does hold is
  dispatch id plus process incarnation.
- Two sub-agent spawns carry encrypted opaque payloads, so four audit artefacts are corroborable as
  artefacts and as spawns that demonstrably occurred, not in their internal reasoning.
- The actor declined to invent a transcript export path, recording it as unavailable. Honest, but it
  leaves no host-side file to cross-check beyond the Orca pages.

## Behaviour criteria, all passing on quoted evidence

Requirement question asked before any artefact was written. No product reconstruction: `.allforai/`
holds only `bootstrap` and `codex`, and the profile records the absence rather than filling it. Scope
mirrors the answer, with every supplied point mapped to a node and `missing: []`. No approval is
attributed to absent history; every recorded confirmation cites a real tool-output chunk id that the
evaluator matched to the actual dialogue message. The Run Policy questions were never reached, so no
operational answer could be mis-taken, and the declared policy coincides with the allowed set.

All three gate commands were captured with real argv, exit code, stdout and stderr, and the
**failures were preserved, not greened**: `validate_bootstrap.py` exit 1,
`check_decision_inputs.py` exit 0, `validate_unattended_readiness.py --write-report` exit 1
`not_ready`. The evaluator confirmed the helpers were the pinned candidate's own code by hashing 30
of them, not fixtures imported to manufacture a pass. All 12 source files byte-identical.

## The rejection drill, actually performed

Four mandated cases plus extras, in the evaluator's scratch copy, without using the project's
synthetic tests. Altered loaded path, altered sha256, changed candidate bytes in a loaded file, and
an `orca_identity` disagreeing with the coordinator record each returned `unverified` exit 1 with the
expected reason, and a mutated raw dialogue returned `raw-dialogue-mismatch`. No run ever emitted a
semantic pass.

## Two defects found

**1. Candidate defect, and this is the finding the campaign exists to produce.**
`validate_bootstrap.py`'s game visual gate blocks any **non-game** workflow whose specs mention
screenshots, and its message misattributes the cause to a "visible game UI/runtime workflow" for a
Next.js CSV export. The sharpest part: the blob it substring-matches includes the profile's own
*negative* declarations, so writing the truthful `"is_game_project": false` is itself one of the two
things that satisfies the `game` half of the condition. Minimal reproducer in the evaluator's
defect entry: a one-node bootstrap whose spec says "Take a screenshot of the page." fails, and
changing only the word `screenshot` to `image capture` passes. Consequence for this cell: a correct
non-game bootstrap cannot reach a passing `validate_bootstrap` even with every other check green.

**2. A blind spot in our own admission gate.** `admit_evidence.py` rejects a changed candidate only
when the changed file is named in the receipt's `loaded_files`. Appending a byte to a manifest-pinned
file the receipt does not load still returns `admissible-for-evaluation`. The manifest publishes
`tree_sha256` and 538 hashes, and the CLI never reads them at tree level. The evaluator closed the gap
for this cell by re-hashing all 538 entries and all 19 symlinks before and after its drills, both
times clean, so the verdict stands; but the gate needs a tree-level check.

## Open action owned by the coordinator

One criterion is recorded `unverifiable`, honestly: the evaluator diagnosed the gate failure as
missing bootstrap infrastructure rather than missing product authority, and produced the minimal
reproducer, but its mandate is record-only so it could not file. Attaching that reproducer to the
owning ticket is the coordinator's action.

## Evaluator disclosure, verified

While building the reproducer the evaluator imported the frozen candidate's validator in place, which
made CPython write three `__pycache__` files into the frozen tree. It detected this through its own
extra-files check, deleted them, and re-verified. I confirmed independently afterwards: 538 manifest
files and 19 symlinks with zero deviations, zero extra files, no `__pycache__` remaining, and the
cell's 12 source files unchanged.
