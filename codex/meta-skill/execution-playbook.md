# Meta-Skill Execution Playbook (Codex)

## Bootstrap

1. Read the target project directory.
2. Detect tech stacks, modules, architecture patterns, and any existing `.allforai/` artifacts.
3. Collect or infer the target goals.
4. Load canonical capability references from `./knowledge/capabilities/`.
5. Use research-first specialization:
   - prefer project evidence over hardcoded assumptions
   - for high-risk domains, load Codex-only specialization guidance such as `./knowledge/high-risk-specialization.md`
   - then load the domain-specific guidance file, for example `./knowledge/im-specialization.md`
   - when the project is clearly a fidelity-oriented rewrite, also load `./knowledge/replication-specialization.md`
   - when the product shape can be inferred from code evidence, load `./knowledge/product-inference.md`
6. Follow the canonical bootstrap protocol from `./skills/bootstrap.md`.
7. Generate:
   - `.allforai/bootstrap/bootstrap-profile.json`
   - `.allforai/bootstrap/product-summary.json` when supported by repository evidence
   - `.allforai/bootstrap/workflow.json`
   - `.allforai/bootstrap/node-specs/*.md`
   - `.allforai/bootstrap/scripts/*`
   - `.allforai/bootstrap/protocols/*`
   - `.allforai/codex/flow.py` by materializing `./knowledge/flow-template.py`
   - `.codex/commands/run.md`
8. Validate the bootstrap products.
9. Present a summary and next-step usage instructions.

## Run (Generated)

The generated Codex orchestrator entry is written to `.codex/commands/run.md` in the target project.

It must:

1. Read `.allforai/bootstrap/workflow.json` at every iteration.
2. Use project-local helper scripts under `.allforai/bootstrap/scripts/`.
3. Read node-specs from `.allforai/bootstrap/node-specs/`.
4. Record transitions to `workflow.json`.
5. Resume safely from current project-local artifacts.
6. If the same node fails 3 times, stop retries, read `.allforai/bootstrap/protocols/diagnosis.md`, and record `diagnosis_history`.
7. If 5 consecutive transitions produce no new artifacts, stop and report stagnation instead of looping forever.

`state-machine.json` is not the primary contract. It may only be read for backward compatibility while older bootstrap outputs still exist.
