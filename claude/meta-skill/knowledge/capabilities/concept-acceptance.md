# Concept Acceptance Capability

> Final workflow node. A coverage gate, not a verdict (ADR-0008): every behaviour
> mapping the concept declares either has evidence in the delivered product or is
> named as missing. The gate scores nothing, sets no threshold and renders no
> verdict. Whether the product delivers the concept, and how well, is the question
> `/cross-exam` and `/product-review` ask afterwards, as a party that did not write
> the code. This is NOT code-vs-design verification either (that is product-verify).

## Goal

After all build/test/demo/verify nodes complete, answer one machine-decidable
question: for each behaviour mapping the concept declares, does evidence exist
that the delivered product exhibits it? The answer is two lists — covered and
missing. The orchestrator's `on_needs_iteration` trigger fires on a non-empty
missing list and proceeds on an empty one; nothing else in this gate's output
drives the run.

## Prerequisite

`product-concept.json` must exist — OR — for game projects, `game-design-doc.json`
(from game-design-finalize node). Bootstrap auto-appends this node when
`has_product_concept = true` OR `is_game_project = true`.

**What a behaviour mapping is.** The concept states, per adaptive system, the
behaviours that change with state (`adaptive_systems[].behavior_mappings[]`:
`state_read` → `behavior`). Those are the mappings this gate covers, and the concept
is the only source of them: the gate never invents a mapping the concept did not
declare, and never drops one it did.

**Game project fallback** (`is_game_project = true` and `has_product_concept = false`):
the baseline is `.allforai/game-design/game-design-doc.json`; its `systems[]` entries
that describe state-driven behaviour (`core_loop` feedback, `economy` rules, per-role
`player_roles[]` behaviour) are the mappings.

**MVP scope**: mappings that reference only `post_launch` features are listed as
`out_of_scope`, with the feature that defers them, never as covered and never as
missing. Bootstrap Step 3.5 Level 4 flags them as "premature mapping"; this gate does
not re-judge that.

## What LLM Must Accomplish (not how)

### Required Outputs

| Output | What |
|--------|------|
| `.allforai/concept-acceptance/acceptance-report.json` | The coverage gate's machine record: covered, missing and out-of-scope mappings, each bound to the concept it was read from |
| `.allforai/concept-acceptance/acceptance-report.md` | Human-readable summary: the missing list and what evidence each lacks; no scores |
| `.allforai/product-concept/iteration-feedback.json` | The missing list for the next bootstrap cycle, plus `user_decisions[]` (empty until a human records one) |

### Output Shape

`acceptance-report.json` keeps its name; its shape is the gate's and nothing more:

```json
{
  "gate": "concept-acceptance",
  "checked_at": "<ISO timestamp with timezone offset>",
  "attempt_id": "<unique per run of this node>",
  "concept_ref": { "path": ".allforai/product-concept/product-concept.json", "digest": "sha256:<hex>" },
  "covered_mappings": [
    {
      "mapping_id": "<system>/<index or name>",
      "state_read": "<as declared>",
      "behavior": "<as declared>",
      "evidence": [
        { "kind": "runtime-probe | e2e | test | screenshot | log | api-roundtrip",
          "path": "<file under .allforai/ or the project>",
          "claim": "<one line: what this evidence shows>" }
      ]
    }
  ],
  "missing_mappings": [
    {
      "mapping_id": "<system>/<index or name>",
      "state_read": "<as declared>",
      "behavior": "<as declared>",
      "expected_evidence": "<what would have shown it>",
      "searched": ["<where evidence was looked for>"]
    }
  ],
  "out_of_scope_mappings": [
    { "mapping_id": "<...>", "deferred_by": "<post_launch feature>" }
  ]
}
```

The report carries no `verdict`, `overall_score`, `pass_threshold` or
`dimensions[].score`. A report that does is not this gate's output: both
orchestrators refuse it by name rather than read it as either answer, and the
same refusal applies to a report with no `missing_mappings` list at all.

### Required Quality

- Every mapping the concept declares appears in exactly one of the three lists.
  A mapping in none of them, or in two, refuses the report.
- A mapping is covered only by evidence that shows the behaviour **changing with
  the state it reads**: a before/after observation (state, triggering event,
  observed behaviour) or its equivalent. Code that references the state dimension
  is not evidence that the behaviour changes; the mapping stays missing.
- Every `evidence.path` exists and is readable at the time the report is written;
  a path that does not is refused, not skipped.
- `concept_ref.digest` is the digest of the concept as read. A concept edited after
  the report was written invalidates the report; it does not silently age.
- `attempt_id` is unique per run of this node, so the same missing list twice is two
  distinct verdicts and the orchestrator never has to infer a rerun from a timestamp.
- A missing mapping names what evidence would have covered it and where the gate
  looked. That list is the repair request; a bare "not implemented" is not one.
- The gate reads only the concept, the delivered product and the evidence the
  earlier gates left under `.allforai/`. It never runs `/cross-exam` and never
  reads its ledger.

### Evidence the gate may cite

Runtime evidence produced by earlier nodes (product-verify, runtime-smoke-verify,
test-verify, visual-verify, demo-forge's `verify-report.json`) is admissible when
its `readback`/`build` bindings name the current build; the gate may also gather its
own before/after observations with the project's E2E tool as `bootstrap-profile.json`
selects it (Playwright, `flutter test integration_test/`, XCUITest, Espresso, curl, a
shell script, PlayMode/GUT/Gauntlet, or a manual playthrough checklist for a game with
no runner). Static evidence (a code path, a config value) covers nothing on its own.

For multi-client roles (`clients[]` with `feature_parity`), a mapping is covered
only when it is covered on every client the mapping's feature is declared for;
`parity_exceptions` and `explicit` `supported_features[]` narrow that set, they never
widen it. A mapping covered on one client and not another is missing, and the entry
names the client.

## Downstream Contract (orchestrator)

`on_needs_iteration` fires when `missing_mappings` is non-empty, and proceeds when
it is empty. Under the recorded Run Policy:

- `halt_with_report` writes `acceptance-report.md` and stops; the fix /
  re-bootstrap / accept choice is the human's, afterwards.
- `auto_fix_once` turns the missing list into **one bounded QA repair request** under
  the existing authorization path (ADR-0005, ADR-0006): the gate is a QA node whose
  current report is a positive verdict, its declared `required_repair_loops` entry
  names the repair node, and the dispatch is charged to the ledger before it runs.
  A gate no loop declares a repair for is an unauthorized repair and halts; a spent
  or unknown budget halts; a second missing list after the one recorded repair halts
  with its report. Nothing repairs in-node, and nothing repairs unpaid.
- `accept` records `accepted_with_gaps` as a qualified run outcome, never as
  verified or completed work.

## Iteration Feedback

Write `.allforai/product-concept/iteration-feedback.json` on every run, whatever the
lists hold — it is the audit trail for the iteration:

```json
{
  "iteration": 1,
  "feedback_at": "<ISO timestamp with timezone offset>",
  "source": "concept-acceptance",
  "concept_ref": { "path": "...", "digest": "sha256:<hex>" },
  "missing_mappings": [ "<the report's entries, verbatim>" ],
  "user_decisions": []
}
```

Archive previous feedback to `.allforai/product-concept/iteration-history/iteration-{N}.json`.
`user_decisions[]` is written only by a human at an interactive entry; the gate
leaves it as it found it.

## Rules (Must Preserve)

1. **Concept is the baseline**: not design artifacts, not code structure — the
   declared mappings are the single list this gate covers.
2. **Coverage, not judgement**: the gate says which mappings have evidence and which
   do not. It never says how good the product is, how complete it feels, or whether
   it should ship; those verdicts left `/run` (ADR-0008).
3. **Evidence is bound**: every covered mapping cites evidence that exists and names
   the build it was taken from; the report names the concept digest it was read against.
4. **The missing list is the repair request**: machine-readable, one entry per
   mapping, each naming the evidence that would cover it.
5. **Per-client coverage**: a multi-client mapping is covered per client, never by
   the best client.

## Downstream Consumers

> Bootstrap reads this table to generate Context Pull sections for downstream node-specs.
> `required` = subagent reports error if file missing; `optional` = warning + continue.

| Artifact | Field Path | Consumer Capability | Required | Reason |
|----------|------------|---------------------|----------|--------|
| `.allforai/concept-acceptance/acceptance-report.json` | `missing_mappings[]` | orchestrator (run.md / flow.py) | required | `on_needs_iteration` fires on a non-empty list and proceeds on an empty one; under `auto_fix_once` the list is the bounded repair request |
| `.allforai/concept-acceptance/acceptance-report.json` | `concept_ref`, `attempt_id` | orchestrator (run.md / flow.py) | required | binds the list to the concept it was read from and to the attempt that produced it |
| `.allforai/product-concept/iteration-feedback.json` | full file | bootstrap (re-run) | optional | 下一轮 /bootstrap 读取 missing_mappings 进行增量规划 |

## Knowledge References

### Phase-Specific:
- cross-phase-protocols.md §A: Push-Pull for loading concept baseline
- cross-phase-protocols.md §C: Upstream Baseline Validation (concept = ultimate upstream)
- docs/adr/0008: why the score, threshold and verdict left this gate

## Composition Hints

### Single Node (default)
Run after all build/test/demo/verify nodes complete. Final node in workflow.

### Repair loop for `auto_fix_once`
When the Run Policy may answer `auto_fix_once`, bootstrap declares a
`required_repair_loops` entry whose `qa_node_ids` names this node and whose
`repair_node_id` is a node `hard_blocked_by` it (a distinct node from any loop this
gate closes, or the graph cycles). Without that declaration the trigger halts as an
unauthorized repair — by design, not by accident.

### Split Static vs Dynamic
For large multi-platform projects: evidence gathering per platform as separate
nodes, one gate node reading them all.

### Skip Entirely
When `product-concept.json` does not exist (pure code analysis, tune, quality-checks goals).
