# check_artifacts read-only measurement surface

Closes the both-host repair-acceptance gap named in msg_3f834fa559da / msg_952ef65013c3:
an independent gate could prove an artifact exists and carries no blocking status, but not
that it was delivered by this attempt, nor what the node is bound to. Root chose option B;
field names and ownership were agreed with the runtime dispatch in msg_abd271fc67ea and
released in msg_e4e2c1dd383e.

Owned and changed: `claude/meta-skill/scripts/orchestrator/check_artifacts.py`
(`codex/meta-skill/scripts` is a symlink to `claude/meta-skill/scripts`, so both hosts copy
the same file). No Node or Codex driver was touched. No commit.

## The contract

Per exit artifact, in `artifacts[]`:

| Field | Value |
|---|---|
| `digest` | lowercase sha256 hex of the file bytes, or `null` |
| `digest_error` | present **only** when `digest` is null: `"missing"`, `"outside project root"`, or `"unreadable: <errno text>"` |

On the node's `freshness` object, beside the existing `readiness_status`:

| Field | Value |
|---|---|
| `binding_identity` | sha256 over canonical JSON of `{kind, inputs}` of the recorded observation, or `null` |
| `binding_kind` | `"contract"`, `"evidence"`, or `null` |

`binding_identity` uses exactly `evidence_freshness.evaluate`'s record precedence
(`contracts[node_id] or nodes[node_id]`) and its canonical `digest`, so the identity and
`readiness_status` always describe the same observation and answer different questions:
what the node is bound to, and whether that binding still holds. The recorded `inputs` is
the full snapshot (files, requirements, contract digest, baseline scope, upstream), which
is why a digest of the delivered bytes cannot substitute for it.

**The record must be the observation `evidence_freshness` actually writes.** The accepted
shape is validated against the existing shared contract, not against a new one:
`snapshot()` builds `files`/`requirements`/`baseline_scope`/`upstream` as maps plus a
non-empty `contract` string, `session()` refuses any kind outside `{contract, evidence}`,
and `evaluate()` reads an absent kind as `evidence`. A record that does not match that
shape can never equal a current snapshot, so it is refused rather than digested into an
identity; an absent kind is not a malformed record and reads as `evidence`, matching what
`readiness_status` was judged against.

**The pair describes one observation.** Readiness is evaluated between two reads of the
same state bytes and the identity is computed from those exact bytes; a rebind landing in
that window fails closed to a null binding rather than reporting a new identity beside an
old `readiness_status`. `freshness_states` is not modified, so the readiness and
reconciliation gates that consume it are unchanged.

How the pair reads across an attempt: identity changed ⇒ the node was re-observed and
re-bound to whatever the inputs now are (the correct signal for a source-changing repair);
identity unchanged and `readiness_status` valid ⇒ still bound to the actual current inputs;
identity unchanged and `readiness_status` stale ⇒ inputs moved and nothing re-bound.

Fail-closed, always as an explicit `null` rather than an omitted field: missing, unreadable
or escaped artifacts; an unparseable or non-object freshness state; a node with no record; a
record without `inputs`; a non-string `kind`.

## Focused tests

`claude/meta-skill/tests/unit/test_check_artifacts_measurement.py` — 48 tests, all green;
**23 of the 24 distinct cases are red** against `HEAD`'s helper (measured in a scratch copy
with only `check_artifacts.py` reverted and a scratch-only import shim so the baseline
reports per test instead of one collection error). The single case that passes at HEAD,
`test_measuring_registers_no_observed_read`, is a no-regression property the old helper
already had.

Digest, content versus existence and mtime:

- `test_the_digest_is_the_sha256_of_the_delivered_bytes` — exact value equality.
- `test_a_content_edit_changes_the_digest`.
- `test_touching_an_artifact_does_not_change_its_digest` — `os.utime` moves mtime, digest
  holds (both hosts). This is the touched-leftover case.
- `test_a_missing_artifact_measures_null_with_its_reason`,
  `test_a_directory_in_place_of_an_artifact_measures_null`,
  `test_an_unreadable_artifact_measures_null` (skips if the user can still read a 0o000 file).
- `test_an_artifact_that_escapes_the_project_is_refused_even_though_it_exists` — a symlink
  out of the project: `exists: true`, `digest: null`, `digest_error: "outside project root"`.
- `test_a_symlink_inside_the_project_is_measured`,
  `test_the_digest_helper_refuses_an_absolute_path_outside_the_root`.

Binding:

- `test_a_published_contract_reports_a_stable_current_binding` — 64-hex, kind `contract`,
  `readiness_status` valid, stable across two measurements.
- `test_the_binding_identity_is_the_recorded_observation_not_the_delivered_bytes`.
- `test_moving_an_input_leaves_the_old_binding_and_turns_readiness_stale` — the stale-binding
  distinction.
- `test_re_observing_the_changed_inputs_rebinds_the_node` — the source-changing repair; the
  identity changes and readiness returns to valid (both hosts).
- `test_an_unusable_freshness_state_fails_closed_to_a_null_binding` (unparseable, not an
  object, nodes not a map, empty), `test_a_record_without_inputs_or_kind_has_no_binding`,
  `test_a_node_with_no_record_has_no_binding`,
  `test_evidence_and_contract_records_are_distinguished`.

Record shape, kind and pair coherence (the msg_1ca735f1e9fb review findings):

- `test_a_record_that_is_not_the_canonical_snapshot_has_no_binding` — 10 shapes: `inputs`
  null, a string, a list, a number, empty, missing `contract`, `files` not a map, a blank
  or non-string `contract`, a missing container.
- `test_a_kind_outside_the_shared_set_has_no_binding` — unknown, blank, wrong case, number,
  null, list.
- `test_an_absent_kind_reads_as_evidence_exactly_as_evaluate_does` — the one default that is
  shared semantics rather than a malformed record.
- `test_the_binding_reads_the_exact_state_bytes_it_is_given`.
- `test_a_rebind_between_the_two_reads_fails_closed` — a controlled rebind landing inside the
  measurement window: the binding is null, `readiness_status` is not weakened, and the next
  measurement reports the new binding coherently.
- `test_an_absent_state_leaves_the_binding_null_without_failing_the_read`.
- `test_a_target_swapped_after_it_was_opened_is_refused` — a controlled swap between the
  containment check and the read: `digest_error` is `"unreadable: target changed while it
  was being measured"`.

These seven cases are red against the pre-review version of the helper (13 failures across
their parametrizations, measured in a scratch copy with the shape check, the kind set, the
coherent-read window and the descriptor identity recheck relaxed back).

Read-only and additive:

- `test_measuring_writes_nothing` — full byte-level tree snapshot unchanged across a
  measurement.
- `test_measuring_registers_no_observed_read` — the dynamic-read register is untouched.
- `test_the_shipped_json_command_carries_the_measurement_and_stays_additive` — through the
  copied `check_artifacts.py --json` a gate agent actually runs, on both hosts, asserting the
  new fields and that every pre-existing key keeps its meaning.
- `test_a_blocked_artifact_still_blocks_and_is_still_measured`.

Suites after the change: `claude/meta-skill` `tests/unit` **804 passed**; `codex/meta-skill`
`test_flow.py test_install.py` **105 passed**; `node --test` on
`claude/meta-skill/knowledge/run-engine/tests/*.test.js` **95/95** (the consumer, driving the
real helper through `real-gate.js`); `shared/scripts/orchestrator` **122 passed**. Counts on
this tree move between runs because other dispatches are editing it concurrently.

One pre-existing test was touched: `test_freshness_admission_corrections.py` compared the
`freshness` dict by exact equality, so the retained-legacy-node assertion now includes
`binding_identity: None, binding_kind: None` — which is the fail-closed value and states
that no provenance is invented for a legacy node.

## Limitations

0. **Time-of-check/time-of-use.** The bytes are read from the descriptor the containment
   check accepted and the resolved path is re-stat'ed against that descriptor's identity, so
   a swapped target is refused. A swap inside a *parent directory* during the read window is
   still possible; a project that rewrites its own tree mid-measurement is outside what a
   read-only helper can prove, and the consumer's before/after comparison is the backstop.
1. **`exists` and `all_exist` are unchanged.** An exit artifact reached through a symlink out
   of the project still reports `exists: true`; only `digest`/`digest_error` reject it. This
   keeps the output backward compatible, and it means a consumer must assert on a non-null
   digest rather than infer containment from `exists`.
2. **This measures; it never binds.** There is no observation, no dynamic-read registration
   and no publication, so a delivery whose inputs moved without re-observation is visible
   here and refused by the consumer, not repaired here.
3. **`status` versus `readiness_status`.** A node with a published contract and no evidence
   reports `readiness_status: valid` while `status` is stale (`diff: {"evidence":
   "unpublished"}`) and `all_exist` is false. The binding pairs with `readiness_status`.
4. **Shared-state placement.** The binding fields are merged into the `freshness` object
   returned by `check_node_artifacts` only, not into `freshness_states`, so the readiness and
   reconciliation gates that consume that helper are byte-identical to before.
5. **No host proof.** Everything is copied-helper seam evidence in temporary projects. The
   end-to-end acceptance this unblocks belongs to the runtime dispatch's negatives.
6. **A snapshot-shape change in `evidence_freshness` closes bindings rather than corrupting
   them.** The accepted shape is validated against that module's current contract, so if the
   snapshot ever grows or renames a key, `binding_identity` goes null and consumers refuse —
   the safe direction, but it needs coordinating with the freshness owner if that shape moves.
7. **`shared/scripts/orchestrator/check_artifacts.py`** is a much older, already-divergent
   copy (2.7 KB against 30 KB at `2cc347af`) and was left alone — the same pre-existing drift
   already flagged for `check_decision_inputs.py` and `validate_bootstrap.py`.
