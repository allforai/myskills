# evidence-engine

The shared evidence engine (ADR-0008): the checks a runtime or code probe must pass before any verdict, gate
or audit can rest on it. One source here, mirrored as `engine/` into four places by `sync.py`:

```
claude/superstorm/knowledge/cross-exam/engine   (beside visual/)
codex/cross-exam-skill/engine                   (beside visual/)
claude/meta-skill/scripts/engine
codex/meta-skill/scripts/engine                 (codex/meta-skill/scripts is a symlink to the Claude scripts dir)
```

`python3 shared/evidence-engine/sync.py` regenerates them; `--check` (and `test_mirrors.py`) fails on any
divergence. A consumer loads the mirror by path as a sibling directory, the way `visual/validation.py`
loads its own siblings; nothing here is on `sys.path`.

## What it owns

- **Build identity** (`identity.py`): commit + working-tree snapshot digest (`git diff HEAD` plus untracked
  file contents) + artifact digest, as `visual-acceptance/platforms/web.md` defines it. Two different
  uncommitted states on one commit get different values. `build_identity(repo, artifacts, exclude)` computes
  it; `build_reason(recorded, repo, artifacts, exclude)` compares a recorded value with the tree now. `exclude`
  names repo-relative paths outside the snapshot whether tracked or not — the run directory and evidence the
  probe itself writes, which must not move the build they record; an entry says what it excluded. Repository
  variables a git hook exports (`GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE`...) are dropped, so a gate run
  from inside another repository's hook still identifies the tree it was asked about.
- **Digest binding of refs** (`ref_digest_reason`, `bindings_reason`, `artifact`, `digest`): a frozen input
  is the file at a ref whose SHA-256 matches the recorded digest, and every capture or report carries the
  run's binding keys verbatim.
- **In-app readback** (`readback`, `readback_reason`, `readback_shape_reason`): an applied axis (theme, locale,
  zoom, width...) is proven by the value the app reports, matched against what the case claims;
  `value_tokens` splits a compound case value ("浏览器 zh-CN + 站点 en") into what a readback may equal.
- **Request destination** (`served_by_reason`): runtime evidence names host, process and the active mock
  layers; through a mock layer a probe can show a gap, never a done.
- **Content gate and probe window** (`content_reason`, `probe_window`, `probe_window_reason`,
  `PROBE_WINDOW_TOLERANCE`): a code excerpt has a `路径:行号`, runtime evidence has screenshots or outputs for
  every requested state, an unprovable has a substantive reason file, and every evidence file was written
  inside `[probed_at, transcript mtime + tolerance]`. `probe_window` returns the facts (window, offenders,
  unreadable times) for a consumer whose report pins its own sentence; `probe_window_reason` is the
  canonical sentence. Both take an optional `read_mtime` reader so a consumer's tests can replace theirs.
- **The ledger-entry shape** (`entry_reason`): medium, verdict, build, `probed_at` with an offset, a real
  evidence directory under the run, served_by, readback and digest-bound images, refused by name. Media are
  a probe's (`MEDIA`: runtime, code, ledger) or a mechanical gate's (`GATE_MEDIA`: build, test, contract —
  whose content is a captured output); which of them an author's entry may gate on is cross-exam's rule (#60),
  the shape is this one.

Every check returns `''` or the refusal reason; none raises on a malformed entry. Reason strings are the ones
cross-exam prints today, so a case moved here keeps its assertion.

## What it deliberately does not own

- **Per-node input freshness.** Whether a node's inputs are newer than its outputs is meta-skill's
  `evidence_freshness`; the engine supplies the build value an entry records, not the staleness decision.
- **Product intent provenance.** Who confirmed a concept item, in which words, at what time, is the concept
  baseline's contract; the engine checks evidence shapes, not what the product was meant to be.
- **Visual matrix expansion, layout rules, reviewer topology.** Those stay in `shared/visual-acceptance`.
- **Verdicts.** Nothing here decides done, gap or drift; it decides whether an entry may be read at all.

## Who reads it

Extracted from cross-exam's renderer and the visual acceptance validator (#54); both cross-exam ports and
`shared/visual-acceptance` now import it and define none of it themselves (#58). Each renderer loads
`engine/evidence.py` by path from its own package and keeps the private names its tests patch (`_mtime`,
`_evidence_files`, `_content_reason`, `_parse_time`) as aliases; the Codex renderer keeps only its own
probe-window sentence over `probe_window`. `visual/matrix.py` finds the engine beside its package
(`engine/` in a mirror, `evidence-engine/` in the source tree) and `validation.py` takes digest binding and
readback from it, raising where `visual_reason` expects a raise. `test_single_definition.py` greps the
consumer trees and fails on any engine-owned name defined a second time, underscore-prefixed or not.
meta-skill's runtime gates consume it too (#59): `scripts/check_evidence.py` loads `engine/evidence.py` and
`engine/identity.py` by path to validate the ledger-shaped entries `scripts/capture_evidence.py entry` writes.
Since #61 the visual acceptance package is mirrored beside the meta-skill engine mirrors as well
(`claude/meta-skill/scripts/visual`), so visual-verify's gate (`scripts/check_visual_evidence.py`) reaches
readback and image binding through the same `visual/matrix.py` → `../engine` path cross-exam uses.

Run the suite from this directory (`python3 -m pytest shared/evidence-engine`); mirrors carry the same
tests and skip the parity and single-definition checks when installed standalone.
