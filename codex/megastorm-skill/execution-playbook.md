# Execution Playbook — megastorm pipeline (Codex)

**Invariant:** decisions front-loaded → autonomous → self-fix loop, escalate-to-stop.
All human interaction is in Phase 0. After Phase 0, do not stop for the human until an
escalation surfaces. You (the interactive Codex session) are the orchestration brain;
every headless agent below is a fresh `codex exec` process.

Spawning an agent: `codex exec --sandbox workspace-write -m <model> --cd <dir>
--output-last-message <tmpfile> "<prompt>"` — prompt = the relevant `prompts/*.md` file
content + the agent's input JSON appended. The agent's final message must end with
exactly one JSON object per `schemas.md`; parse it, re-ask once on garbage, then escalate.

## Phase -1 — Preflight
Verify `codex`, `git`, `python3` are on PATH and `prompts/`, `scripts/` exist beside this
playbook. If not, STOP and tell the user. Do not proceed.

## Phase 0 — Decisions front-loaded (interactive)
1. Analyze current state: repo structure, recent commits, docs. Summarize.
2. Decompose the goal into M modules + boundaries + inter-module deps, brainstorming
   WITH the human: one question at a time, explore alternatives before settling, YAGNI.
   Write the draft overview to `docs/superpowers/specs/<date>-<goal>-overview.md`
   (module table + dependency graph). **If the goal is too big for one run, cut it
   here:** milestone-1 scope = this run; defer the rest to a `## Roadmap` section.
3. **Granularity review (dedicated step — do not skip):** audit the breakdown itself:
   - **Size:** any module smelling like > 20 tasks gets split or deferred NOW — §1.3
     has a hard size check and an oversized module there is a guaranteed halt.
   - **Cohesion:** one module = one cohesive subsystem; a one-line description that
     needs "and" twice is two modules.
   - **Balance:** don't over-split — two candidate modules sharing most of their
     interfaces should merge.
   Present a table (module → est. size → verdict → action); human approves.
4. For EACH module, brainstorm a standard module spec with the human; all M approved.
5. **Mint the frozen registry (you are the single owner).** Write into the overview,
   wrapped in `<!-- megastorm-registry:start -->` / `<!-- megastorm-registry:end -->`
   markers, a ```json object per `schemas.md`: `requirements` (`R-<module>-NN` for every
   requirement) + `interfaces` (closed vocabulary, grammar `<kind>:<name>`, kind ∈
   api/event/data/ui, lowerCamelCase). Err toward a GENEROUS interface vocabulary — a
   thin registry makes the design fan-out throw escalations. FROZEN before Phase 1.
6. **Resolve the three model tiers WITH the human** — never automatically:
   copy `models.example.json` → `models.json`, fill each tier with a real model name
   available to this codex install (`codex exec -m <name>` must work):
   - `think` (design/closure-critic/plan/reverse-critic): strongest reasoning model.
   - `verify` (supervisor): strong + rigorous; never weaker than `bulk`.
   - `bulk` (executor): cheap/fast coding model.
   Also record the choices in the registry `models` field. NO automatic downgrade —
   ever. A mid-run model failure is retry-then-escalate, never silent substitution.
7. **New-human-decision rule (Phase 1 boundary):** anything changing module boundaries,
   public/cross-module interfaces, or user-visible scope = escalate. Internal-only
   choices = agents decide and log.

## Phase 1 — Autonomous pipeline
For every stage: collect each agent's JSON; ANY `status:"escalate"` → HALT, render
`reason`+`evidence` to the user, get the decision, re-run that stage. `module-too-large`
is an ordinary escalation: stop and ask — no automatic re-decomposition.

### 1.1 Design — fan-out
One `codex exec` (`think` model) per module: `prompts/design-agent.md` + the module spec
+ the frozen registry block. Run them in parallel (shell background jobs) or serially —
collect M design manifests (JSON per `schemas.md`).

### 1.2 Closure check — deterministic then LLM
- Extract the registry: text between the registry markers, strip the ```json fence,
  write `requirements.json` (its `requirements`) + `registry.json` (its `interfaces`),
  and the collected manifests to `manifests.json`.
- `python3 scripts/check_closure.py requirements.json manifests.json registry.json` —
  BLOCK → feed errors to a fix agent (design-agent prompt), re-run, ≤3 rounds.
- Then one `codex exec` (`think`) with `prompts/closure-critic.md` for the prose-level
  judgment, ≤3 rounds. Unresolved → HALT to user.

### 1.3 Plan — fan-out
One `codex exec` (`think`) per design: `prompts/plan-agent.md` → plan-task array
(`implements`/`requires` tags from the registry vocabulary carry cross-module ordering;
`depends_on` is intra-module only).
For each plan: `python3 scripts/validate_plan_tasks.py <tasks.json> registry.json` —
BLOCKED → bounce to the plan agent. Deterministic size check: > 20 validated tasks for
one module = module-too-large → escalate to the human (do NOT bounce — the plan agent
cannot fix scoping).

### 1.4 Reverse review
One `codex exec` (`think`) with `prompts/reverse-critic.md` over all spec/design/plan
docs (≤3 rounds, self-fix or escalate).

### 1.5 Orchestrate — deterministic
Concatenate all plan tasks into `all-tasks.json`, run
`python3 scripts/build_task_dag.py all-tasks.json > orchestration.json`.
Cross-module ordering comes from the derived interface edges (`requires` →
`implements`). BLOCK (cycle / missing dep / required interface nobody implements) →
fix via plan agent. Surface `warnings` in the final report.

### 1.6 Concurrent execute + supervise — deterministic runner (NOT prose)
```
python3 scripts/run_layers.py orchestration.json all-tasks.json \
    --models models.json --prompts prompts --root <repo-root>
```
The runner owns: layer order, in-layer concurrency, worktree isolation + post-confirm
merge for file-colliding groups, the soft-retry ledger (initial + ≤2 retries), vacuous
auto-reinjection, and fresh-context supervision (`verify` model reruns `acceptance_cmd`
itself; it never sees the executor's narrative). Exit 0 = all supervised done.
Exit 1 = escalations in `execution-report.json` → render to the human, apply their
decision, re-run the same command (the state file resumes past completed tasks).

## Phase 2 — Report
Update the overview and write a final report: assumptions agents made, escalations and
their resolutions, every module that ran below its preferred tier (with who approved),
DAG `warnings` and `derived_edges`, and a mandatory **Reality gate** section separating
"autonomously verified" (supervisor-rerun green) from "needs human/hardware
verification" — an all-green run is NEVER claimed as "the feature works".
