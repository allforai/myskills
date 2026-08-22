---
name: product-review
description: Product-thinking critique of a shipped or running product. Names missing jobs, broken journeys, and borrowable competitor positioning. Advice only — never edits product code. Explicitly invoked via /product-review. Same package as cross-exam; different protocol.
disable-model-invocation: true
---

# product-review — 产品思维审视

`$ROOT` = `${CLAUDE_PLUGIN_ROOT}`. This file is the whole protocol.

Not cross-exam. Do not read `skills/cross-exam.md`, do not write a completion ledger, do not use done/gap/drift/unprovable.

## Invariants

- **Interactive only.** Invoked unattended or from an autonomous pipeline: refuse and stop.
- **Advice only.** Do not edit the product's source. The only writes are under `docs/product-review/<date>-<slug>/`.
- **No `.allforai/`.** Do not read or write that tree. Do not call meta-skill capabilities.
- **No 37 interaction types. No UI-spec audit.** Product thinking only.
- **Do not start grilling.** After the report, tell the user they may `$grill-me` / grilling on that file. Wait.

## What you check

For each **user-named job**:

1. **在不在** — is there any entry that does this job?
2. **走不走得完** — can the role start and finish, including the obvious counterpart (place an order → cancel / see status)?
3. **该不该有** — is this a core job or garnish? Use JTBD / Kano only as labels, not as a framework dump.

Default extra pass: **web-search current competitors** for positioning and features that map onto those same named jobs. ERRC is a comparison frame (eliminate / reduce / raise / create vs them), not a file to emit.

Never invent jobs from a competitor catalog. If a competitor feature does not map to a named job, omit it or list it under "seen, not in scope".

## 0. Intake

Completion: target named, jobs named, run directory created, user still present.

1. Confirm a human is in the session.
2. Name the product and how to inspect it (repo, running local app, public site). Production write-actions are forbidden; read-only public marketing pages are allowed.
3. Ask the user to name the jobs this review is about. No jobs → ask once; still none → stop.
4. Create `docs/product-review/<YYYY-MM-DD>-<slug>/`.

## 1. Facts

Completion: every named job has a note on entry / finish / counterpart; competitor notes only for those jobs.

Find facts yourself (repo, running UI, WebSearch). Do not ask the user for anything look-up-able.

- For each named job: where the entry is, whether a path finishes, what counterpart is missing.
- Search live competitors (direct, then indirect). Per hit: positioning one-liner, features that map to a named job, one borrow-or-skip note.

## 2. Recommendations

Completion: `recommendations.md` written in the template below. Every item is one grill-able decision.

Each item:

- `id` stable (`R1`…)
- `job` one named job
- `kind`: `missing_job` | `broken_path` | `borrow_positioning` | `borrow_feature` | `skip`
- `depends_on` other ids or empty
- `recommend`: `adopt` | `defer` | `reject`
- `tradeoff` one sentence
- `evidence` paths, URLs, or UI observations — not vibes

`skip` is for competitor ideas that do not map to a named job.

## 3. Write and stop

Write `docs/product-review/<run>/recommendations.md`:

```markdown
# Product review — <product>

Jobs in scope: …

## Decision tree

### R1 — <title>
- job:
- kind:
- depends_on:
- recommend: adopt | defer | reject
- tradeoff:
- evidence:

## Competitors (named jobs only)
- <name>: positioning. mapped features. borrow or skip.

## Out of scope
- seen elsewhere, not a named job
```

Then stop. One line: this file is upstream for `$grill-me`. Do not grill. Do not implement.
